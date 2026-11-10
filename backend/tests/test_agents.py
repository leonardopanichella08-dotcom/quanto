"""I tre agenti (Agevolazioni, Allocazione, Confronto): chi si assume persona per persona, bandi regionali collegati, consiglio verificato con le regole del bando, tasso di ammissione, segnali di pertinenza."""
import json
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core import bandi, measures, relevance, template_examples as te, template_learning as tl
from app.core.db import connect
from app.core.ingestion import Ingestion
from main import app

client = TestClient(app)
PROFILE = {"company_type": "CAPITALI", "company_status": "COSTITUITA", "region": "Puglia", "employees": 8, "durc_regular": True}
D = date(2026, 10, 24)
RETAIL = {"region": "Abruzzo", "ateco_code": "47.71.10", "size": {"code": "MICRO", "is_sme": True, "label": "Microimpresa"}}
BANDO = "BANDO-AGENTI"


# ------------------------------------------------------------------------------------------------ Agevolazioni
def test_each_person_gets_the_single_richest_measure_that_fits_the_company_and_the_person():
    r = measures.assign(PROFILE, [{"age": "UNDER35", "gender": "M", "unemployed": "GE24", "year": 2026},       # giovane disoccupato da due anni: Bonus Giovani, 650 € × 24 mesi (sede in ZES)
                                  {"age": "OVER35", "gender": "F", "unemployed": "12_24", "year": 2026}], D)    # donna oltre i 35: solo Bonus Donne, 800 € × 12 mesi
    a, b = r["positions"][0]["best"], r["positions"][1]["best"]
    assert (a["id"], a["months"], a["value_eur"], a["sure"]) == ("BONUS_GIOVANI_2026", 24, 15600, True)
    assert (b["id"], b["months"], b["value_eur"], b["sure"]) == ("BONUS_DONNE_2026", 12, 9600, True)
    assert r["total_eur"] == 25200 and r["counted"] == 2 and {i["id"] for i in r["items"]} == {"BONUS_GIOVANI_2026", "BONUS_DONNE_2026"}
    assert "BONUS_DONNE_2026" in {x["id"] for x in r["positions"][0]["rejected"]}                  # e dice perché le altre non valgono per lei


def test_two_different_exonerations_for_two_different_people_are_both_counted():
    """Prima un solo esonero per gruppo contava sempre: due persone con due esoneri diversi ne perdevano uno."""
    r = measures.assign(PROFILE, [{"age": "UNDER35", "gender": "M", "unemployed": "GE24", "year": 2026}, {"age": "OVER35", "gender": "F", "unemployed": "GE24", "year": 2026}], D)
    sel = measures.selection(PROFILE, [{"id": i["id"], "hires": i["hires"], "months": i["months"], "assigned": True} for i in r["items"]], D)
    assert sel["total_max_eur"] == 15600 + 19200 and sel["counted"] == 2 and all(x["counted"] and x["exact"] for x in sel["items"])
    old = measures.selection(PROFILE, [{"id": "BONUS_GIOVANI_2026", "hires": 1}, {"id": "BONUS_DONNE_2026", "hires": 1}], D)          # senza assegnazione resta la regola prudente
    assert sum(1 for x in old["items"] if x["counted"]) == 1


def test_a_person_with_missing_data_is_shown_but_never_summed():
    r = measures.assign(PROFILE, [{"age": "OVER35"}, {}], D)
    first = r["positions"][0]["best"]
    assert first["sure"] is False and first["to_check"] and r["items"] == [] and r["total_eur"] == 0 and r["uncertain_max_eur"] > 0
    nobody = measures.assign(PROFILE, [{"age": "OVER35", "gender": "M", "unemployed": "LT6", "year": 2026}], D)["positions"][0]
    assert nobody["best"] is None and nobody["message"]                                              # nessuna misura vale: lo dice


def test_assign_respects_company_conditions_and_the_endpoint_validates():
    r = measures.assign({**PROFILE, "durc_regular": False}, [{"age": "UNDER35", "gender": "F", "unemployed": "GE24", "year": 2026}], D)
    assert r["positions"][0]["best"] is None and r["positions"][0]["rejected"]
    ok = client.post("/api/v2/profile/measures/assign", json={"positions": [{"age": "UNDER35", "gender": "F", "unemployed": "GE24", "year": "2026"}, {"year": ""}]})
    assert ok.status_code == 200 and len(ok.json()["positions"]) == 2
    assert client.post("/api/v2/profile/measures/assign", json={"positions": [{} for _ in range(51)]}).status_code == 422


def test_exonerations_2026_never_count_for_a_hire_in_the_following_year():
    """Il piano è dell'anno dopo: gli esoneri 2026 valgono solo per chi è assunto entro il 31/12/2026. Prima si sommavano comunque."""
    later = measures.assign(PROFILE, [{"age": "UNDER35", "gender": "M", "unemployed": "GE24", "year": 2027}], D)["positions"][0]
    assert later["best"] is None and "31/12/2026" in later["message"] and "31/12/2026" in next(r["why"] for r in later["rejected"] if r["id"] == "BONUS_GIOVANI_2026")
    unknown = measures.assign(PROFILE, [{"age": "UNDER35", "gender": "M", "unemployed": "GE24"}], D)
    assert unknown["positions"][0]["best"]["sure"] is False and "l'anno di assunzione" in unknown["positions"][0]["best"]["to_check"] and unknown["total_eur"] == 0


def test_a_certain_measure_counts_and_a_richer_uncertain_one_is_shown_apart():
    r = measures.assign(PROFILE, [{"age": "UNDER35", "unemployed": "GE24", "year": 2026}], D)          # sesso non indicato: il Bonus Giovani è certo, il Bonus Donne forse
    p = r["positions"][0]
    assert p["best"]["id"] == "BONUS_GIOVANI_2026" and p["best"]["sure"] and r["total_eur"] == 15600
    assert p["better_if"]["id"] == "BONUS_DONNE_2026" and p["better_if"]["missing"] == ["il sesso"]


def test_the_age_of_the_check_is_reported_so_a_stale_one_is_visible():
    assert measures.for_company(PROFILE, date(2026, 11, 9))["verified_age_days"] == 16 and measures.for_company(PROFILE, date(2026, 11, 9))["stale"] is False
    assert measures.for_company(PROFILE, date(2027, 2, 1))["stale"] is True


def test_regional_measures_are_linked_to_the_open_bandi_of_the_catalog_that_concern_the_company():
    with connect() as conn:
        for bid, name, issuer, dl in (("CAT-TIR-PUG", "Avviso tirocini extracurriculari Regione Puglia", "Regione Puglia", "2099-12-31"),
                                      ("CAT-TIR-LOM", "Avviso tirocini Regione Lombardia", "Regione Lombardia", "2099-12-31"),
                                      ("CAT-TIR-OLD", "Avviso tirocini Regione Puglia 2019", "Regione Puglia", "2019-12-31")):
            conn.execute("INSERT INTO bandi (bando_id, name, issuer, source_url, catalog_status, extraction_status, deadline, summary, catalog_meta, meta_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                         (bid, name, issuer, "https://example.test/" + bid, "CATALOGED", "NOT_STARTED", dl, "s", json.dumps({}), "2026-11-07T00:00:00+00:00"))
    found = bandi.open_by_terms(["tirocini", "garanzia giovani"], PROFILE)
    assert [f["bando_id"] for f in found] == ["CAT-TIR-PUG"]                          # solo aperti e della sua regione
    assert bandi.open_by_terms([], PROFILE) == [] and bandi.open_by_terms(["ab"], PROFILE) == []


def test_names_with_punctuation_are_found_and_regional_links_need_the_region():
    with connect() as conn:
        for bid, name in (("CAT-OCC-PUG", "Incentivi all'occupazione Regione Puglia 2026"), ("CAT-SS", "Smart&Start Italia")):
            conn.execute("INSERT INTO bandi (bando_id, name, issuer, source_url, catalog_status, extraction_status, deadline, summary, catalog_meta, meta_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                         (bid, name, "Ente", "https://example.test/" + bid, "CATALOGED", "NOT_STARTED", "2099-12-31", "s", json.dumps({}), "2026-11-07T00:00:00+00:00"))
    assert [f["bando_id"] for f in bandi.open_by_terms(["incentivi all'occupazione"], PROFILE)] == ["CAT-OCC-PUG"]
    assert "CAT-SS" in [f["bando_id"] for f in bandi.open_by_terms(["smart&start"], PROFILE)]              # trovato anche lo Smart&Start curato: giusto
    body = client.get("/api/v2/profile/measures").json()                 # nessun profilo: la regione manca, i bandi regionali non si mostrano
    tir = next(i for f in body["families"] for i in f["items"] if i["id"] == "TIROCINIO_GARANZIA_GIOVANI")
    assert tir["linked"] == [] and "regione" in tir["linked_note"]


def test_regional_links_do_not_match_unrelated_bandi_that_share_a_word():
    """«Voucher occupazionali» non è il «Voucher Doppia Transizione»; il bonus per trasformare un tirocinio non è la «trasformazione digitale»."""
    with connect() as conn:
        for bid, name in (("CAT-VDT", "Bando Voucher Doppia Transizione 2026 Puglia"), ("CAT-TD", "Avviso trasformazione digitale delle PMI pugliesi"),
                          ("CAT-VOC", "Voucher occupazionali Regione Puglia"), ("CAT-TT", "Bonus per la trasformazione dei tirocini in contratti Puglia")):
            conn.execute("INSERT INTO bandi (bando_id, name, issuer, source_url, catalog_status, extraction_status, deadline, summary, catalog_meta, meta_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                         (bid, name, "Regione Puglia", "https://example.test/" + bid, "CATALOGED", "NOT_STARTED", "2099-12-31", "s", json.dumps({}), "2026-11-07T00:00:00+00:00"))
    voucher = [f["bando_id"] for f in bandi.open_by_terms(measures.BY_ID["VOUCHER_OCCUPAZIONALI"]["search"], PROFILE)]
    transf = [f["bando_id"] for f in bandi.open_by_terms(measures.BY_ID["BONUS_TRASFORMAZIONE_TIROCINIO"]["search"], PROFILE)]
    assert voucher == ["CAT-VOC"] and transf == ["CAT-TT"]


# ------------------------------------------------------------------------------------------------ Confronto
def _shares(**kw):
    base = {k: 0.0 for k in tl.SHARES}
    base.update({"personnel_pct": 0.40, "assets_pct": 0.35, "consulting_pct": 0.20, "training_pct": 0.05})
    base.update(kw)
    return base


def test_the_recommendation_is_checked_against_the_rules_of_the_bando_and_brought_inside_the_caps():
    rules = {"eligible_categories": ["PERSONNEL", "CAPITAL_ASSETS", "CONSULTING"], "max_consulting_percentage": 0.15}
    sh = _shares()
    assert te.verify_shares(rules, sh)["outcome"] == "NON_CONFORME"
    fitted = tl._fit(rules, sh)
    assert te.verify_shares(rules, fitted)["outcome"] == "CONFORME" and abs(sum(fitted.values()) - 1) < 1e-4
    assert fitted["consulting_pct"] <= 0.15 + 1e-6 and fitted["training_pct"] == 0          # la voce non ammessa esce, le consulenze scendono al tetto
    assert tl.rules_check(None, sh)["available"] is False and "regole" in tl.rules_check("NON-ESISTE", sh)["message"]


def _seed_templates(n=3, outcomes=None):
    Ingestion.catalog(BANDO, "Bando per i test degli agenti", "Regione", None, None)
    for i in range(n):
        client.post("/api/v2/templates", json={"ateco_code": "01.11", "bando_id": BANDO, "shares": {"personnel_pct": 0.1, "assets_pct": 0.5, "consulting_pct": 0.2, "research_pct": 0.1, "overhead_pct": 0.1},
                                               "outcome": (outcomes or ["BOZZA"] * n)[i], "shared": True})


def test_recommend_and_draft_carry_a_rules_check(monkeypatch):
    _seed_templates(3)
    monkeypatch.setattr(tl, "_rules_of", lambda b: {"eligible_categories": ["PERSONNEL", "CAPITAL_ASSETS"], "max_consulting_percentage": 0.05})
    r = tl.recommend("anonymous", "01.11", BANDO, draft={"personnel_pct": 0.5, "assets_pct": 0.5})
    assert r["rules_check"]["available"] and r["rules_check"]["outcome"] != "CONFORME"
    assert r["comparison"]["rules_check"]["available"] and r["comparison"]["rules_check"]["outcome"] == "CONFORME"
    monkeypatch.setattr(tl, "_rules_of", lambda b: None)
    assert tl.recommend("anonymous", "01.11", BANDO)["rules_check"]["available"] is False


def test_win_rate_needs_three_decided_outcomes_and_never_counts_examples():
    _seed_templates(4, ["AMMESSO", "PRESENTATO", "AMMESSO", "NON_AMMESSO"])
    w = tl.win_rate("anonymous", BANDO, "01.11")
    assert w["wins"] == 2 and w["decided"] == 3 and w["rate_pct"] == 67 and "ammessi su 3" in w["text"]
    assert tl.win_rate("anonymous", "NON-ESISTE", "01.11") is None
    r = client.get(f"/api/v2/templates/win-rate?bando_id={BANDO}&ateco_code=01.11")
    assert r.status_code == 200 and r.json()["win_rate"]["decided"] == 3


def test_win_rate_is_absent_with_fewer_than_three_decided_outcomes():
    _seed_templates(3, ["AMMESSO", "PRESENTATO", "BOZZA"])
    assert tl.win_rate("anonymous", BANDO, "01.11") is None


# ------------------------------------------------------------------------------------------------ Allocazione
def test_studios_can_signal_a_wrong_relevance_verdict_anonymously_and_hq_sees_the_summary():
    with connect() as conn:
        conn.execute("INSERT INTO bandi (bando_id, name, issuer, source_url, catalog_status, extraction_status, deadline, summary, catalog_meta, meta_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                     ("CAT-SEGNALE", "Avviso generico 2026", "Ente", "https://example.test/x", "CATALOGED", "NOT_STARTED", "2099-12-31", "s", "{}", "2026-11-07T00:00:00+00:00"))
    assert relevance.record_signal("studio@example.test", "CAT-SEGNALE", "NOT_FOR_ME", "DA_VERIFICARE", RETAIL) == {"ok": True}
    relevance.record_signal("studio@example.test", "CAT-SEGNALE", "NOT_FOR_ME", "DA_VERIFICARE", RETAIL)           # lo stesso studio conta una volta sola
    relevance.record_signal("altro@example.test", "CAT-SEGNALE", "NOT_FOR_ME", "ADATTO", RETAIL)
    s = relevance.signal_summary()
    assert s[0]["bando_id"] == "CAT-SEGNALE" and s[0]["studios"] == 2 and s[0]["signal"] == "NOT_FOR_ME"
    with pytest.raises(ValueError):
        relevance.record_signal("studio@example.test", "CAT-SEGNALE", "BOH", None, RETAIL)
    with pytest.raises(KeyError):
        relevance.record_signal("studio@example.test", "NON-ESISTE", "FOR_ME", None, RETAIL)
    assert client.post("/api/v2/bandi/CAT-SEGNALE/signal", json={"signal": "FOR_ME"}).status_code == 200


def test_the_agent_states_are_accepted_per_work():
    job = client.post("/api/v2/clients", json={"name": "Lavoro agenti"}).json()["id"]
    h = {"X-Client-Id": str(job)}
    for key, value in (("measure_positions", {"positions": [{"age": "UNDER35"}]}), ("agent_seen", {"allocation": {"fit": ["A"], "at": "2026-11-09"}})):
        assert client.put(f"/api/v2/clients/current/state/{key}", json={"value": value}, headers=h).status_code == 200
        assert client.get(f"/api/v2/clients/current/state/{key}", headers=h).json()["value"] == value


# ------------------------------------------------------------------------------------------------ verifica del 10 novembre (seconda): budget solo dove serve, territorio provato, studio che dice cosa fare
def test_an_automatic_tax_credit_or_a_guarantee_never_has_a_budget_and_is_called_agevolazione():
    from app.core import funding_modes as fm
    assert fm.from_forms(["Credito d'imposta"]) == {"budget": False, "noun": "agevolazione", "form": "Credito d'imposta"}
    assert fm.from_forms(["Garanzia"])["budget"] is False and fm.from_forms(["Contributo/Fondo perduto"])["budget"] is True
    assert fm.from_forms([], "Agevolazioni fiscali finalizzate all'assunzione di dipendenti detenuti")["noun"] == "agevolazione"
    assert fm.from_forms([], "Avviso per le imprese")["budget"] is None                      # non si sa: si saprà con lo studio
    assert fm.describe("CREDITO_AUTOMATICO")["budget"] is False and fm.describe("PROGETTO_INVESTIMENTO")["budget"] is True and fm.describe("SPESE_CORRENTI")["budget"] is True


def test_the_draft_budget_is_refused_for_an_agevolazione_without_budget():
    from app.core import bandi as b, company_profile as cp, matching
    b.ensure_seeded()
    d = b.get_bando_detail("IPERAMMORTAMENTO-2026")
    assert d["access"]["budget"] is False and d["access"]["noun"] == "agevolazione"
    with pytest.raises(cp.ProfileError) as e:
        matching.budget_template("chiunque", "IPERAMMORTAMENTO-2026", 100)
    assert "non chiede un budget" in str(e.value)
    r = client.get("/api/v2/bandi/IPERAMMORTAMENTO-2026").json()
    assert r["access"]["budget"] is False and r["study"]["budget"] is False and r["study"]["budget_ready"] is False


def test_a_bando_of_a_municipality_outside_the_company_region_is_never_proposed():
    """Un'impresa abruzzese non deve vedere il bando del Comune di Corleto Perticara (Basilicata), anche se il Comune non è un capoluogo noto."""
    abruzzo = {"region": "Abruzzo", "ateco_code": "47.71"}
    name = "Comune Di Corleto Pertica Bando Occupazione E Territorio Lassunzione Da Parte Di Imprese"
    assert relevance.local_entity(name, "") == "Comune di Corleto Pertica"
    assert [f["id"] for f in relevance.text_fails(name, "incentivi.gov.it", "", abruzzo)] == ["territory"]
    assert relevance.text_fails("Comune di Pescara: contributi alle imprese", "", "", abruzzo) == []                 # capoluogo noto, nella sua regione
    assert relevance.text_fails("Comune di Lanciano contributi commercio", "", "", abruzzo, {"regions": ["Abruzzo"]}) == []   # la scheda ufficiale lo colloca
    assert relevance.text_fails("Comune di Matera contributi", "", "", abruzzo)[0]["id"] == "territory"
    assert relevance.text_fails("Contributi CCIAA Irpinia Sannio", "", "", abruzzo)[0]["id"] == "territory"
    assert relevance.in_region("Voucher Regione Abruzzo", "", None, "Abruzzo") and not relevance.in_region("Agevolazioni fiscali nazionali", "", None, "Abruzzo")
    with connect() as conn:
        conn.execute("INSERT INTO bandi (bando_id, name, issuer, source_url, catalog_status, extraction_status, deadline, summary, catalog_meta, meta_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                     ("CAT-CORLETO", name, "incentivi.gov.it", "https://example.test/c", "CATALOGED", "NOT_STARTED", "2099-12-31", "s", "{}", "2026-11-07T00:00:00+00:00"))
        conn.execute("INSERT INTO bandi (bando_id, name, issuer, source_url, catalog_status, extraction_status, deadline, summary, catalog_meta, meta_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                     ("CAT-DETENUTI", "Agevolazioni fiscali finalizzate all'assunzione di dipendenti detenuti o internati", "incentivi.gov.it", "https://example.test/d", "CATALOGED", "NOT_STARTED", "2099-12-31", "s", "{}", "2026-11-07T00:00:00+00:00"))
    terms = measures.BY_ID["INCENTIVI_OCCUPAZIONE_FSE"]["search"]
    assert bandi.open_by_terms(terms, abruzzo, 10, regional=True) == []                      # né il Comune lucano né la misura nazionale: per una misura regionale serve la prova della regione
    detenuti = [x for x in bandi.open_by_terms(terms, abruzzo, 10) if x["bando_id"] == "CAT-DETENUTI"]
    assert detenuti and detenuti[0]["noun"] == "agevolazione" and detenuti[0]["budget"] is False


def test_the_study_state_says_what_can_be_done_and_proposes_a_retry_only_when_it_helps():
    from app.core import pipeline
    with connect() as conn:
        conn.execute("INSERT INTO bandi (bando_id, name, issuer, source_url, catalog_status, extraction_status, deadline, summary, catalog_meta, meta_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                     ("CAT-MAI", "Avviso mai studiato", "Ente", "https://example.test/m", "CATALOGED", "NOT_STARTED", "2099-12-31", "s", "{}", "2026-11-07T00:00:00+00:00"))
    never = pipeline.study_state("CAT-MAI")
    assert never["studied"] is False and never["budget_ready"] is False and never["retry"] is False and "Non ancora studiato" in never["verdict"]
    cur = pipeline.study_state("IPERAMMORTAMENTO-2026")                                     # curato: studiato, niente da rifare, niente budget
    assert cur["studied"] and cur["retry"] is False and "non chiede un budget" in cur["verdict"]
