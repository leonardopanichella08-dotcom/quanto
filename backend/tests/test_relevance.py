"""Pertinenza: un bando che non può riguardare l'azienda non è mai «da verificare» né entra in un progetto o in un piano."""
import json

from app.core import catalog_meta, matching, relevance
from app.core.db import connect

RETAIL = {"region": "Abruzzo", "ateco_code": "47.71.10", "size": {"code": "MICRO", "is_sme": True, "label": "Microimpresa"}}


def ids(fails):
    return [f["id"] for f in fails]


def test_a_retail_clothing_shop_is_never_matched_with_buses_semiconductors_or_research_programmes():
    for name in ("Mobilità sostenibile - Sostegno alla filiera degli autobus elettrici - PNRR", "Contratti di sviluppo - Nuovo sportello semiconduttori",
                 "Progetti di ricerca industriale e sviluppo sperimentale per la transizione ecologica", "Horizon Europe — Model Grant Agreement (azioni a costi reali)",
                 "Bando per la filiera agroalimentare e la pesca"):
        assert "sector" in ids(relevance.text_fails(name, "Ministero", "", RETAIL)), name


def test_the_same_bandi_are_fine_for_the_sector_they_name_and_generic_ones_are_never_excluded():
    transport = {**RETAIL, "ateco_code": "49.31.00"}
    assert relevance.text_fails("Filiera degli autobus elettrici", "MASE", "", transport) == []
    assert relevance.text_fails("Voucher digitalizzazione per le imprese", "Unioncamere", "Imprese di tutti i settori", RETAIL) == []
    assert relevance.text_fails("Fondo di garanzia per le PMI", "MCC", "", RETAIL) == []
    assert relevance.text_fails("Qualsiasi bando", "Ente", "", {"region": "Abruzzo"}) == []                  # ATECO ignoto: non si esclude per un dato che manca


def test_territory_is_read_from_provinces_and_cities_and_bandi_for_public_bodies_are_excluded():
    assert "territory" in ids(relevance.text_fails("Bando Voucher Doppia Transizione - CCIAA Torino", "Camera di commercio", "", RETAIL))
    assert relevance.text_fails("Bando Voucher Doppia Transizione - CCIAA Chieti e Pescara", "", "", RETAIL) == []
    assert relevance.regions_in("Emilia-Romagna, area Romagna") == {"Emilia-Romagna"} and relevance.regions_in("Camera di commercio di Roma") == {"Lazio"}
    assert "applicant" in ids(relevance.text_fails("Bando per la scuola", "Ente", "Possono presentare domanda i Comuni, gli enti locali e le scuole", RETAIL))
    assert relevance.text_fails("Bando", "Ente", "Possono presentare domanda i Comuni e le imprese del territorio", RETAIL) == []


def test_the_catalog_scheda_excludes_other_sectors_and_non_company_applicants():
    assert "applicant" in ids(relevance.meta_fails({"applicant_type": ["Pubblica amministrazione"]}, RETAIL))
    assert "ateco" in ids(relevance.meta_fails({"ateco_codes": ["10", "11"]}, RETAIL))
    assert "sector" in ids(relevance.meta_fails({"sectors": ["Trasporto e magazzinaggio", "Industria"]}, RETAIL))
    assert relevance.meta_fails({"sectors": ["Commercio all'ingrosso e al dettaglio"], "applicant_type": ["Impresa"]}, RETAIL) == []


def test_catalog_candidates_and_project_links_drop_irrelevant_bandi():
    with connect() as conn:
        for bid, name in (("CAT-AUTOBUS", "Filiera degli autobus elettrici"), ("CAT-VOUCHER", "Voucher per la digitalizzazione delle imprese")):
            conn.execute("INSERT INTO bandi (bando_id, name, issuer, source_url, catalog_status, extraction_status, deadline, summary, catalog_meta, meta_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                         (bid, name, "Ente", "https://example.test/" + bid, "CATALOGED", "NOT_STARTED", "2099-12-31", "s",
                          json.dumps({"form": ["Contributo/Fondo perduto"], "costs": ["Spese per impianti e macchinari"], "state": "APERTO"}), "2026-10-24T00:00:00+00:00"))
    out = catalog_meta.rank_for_profile(RETAIL, {"CAPITAL_ASSETS": 100_000.0})
    got = {i["bando_id"] for i in out["items"]}
    assert "CAT-VOUCHER" in got and "CAT-AUTOBUS" not in got and out["excluded"] >= 1


def test_evaluate_marks_an_irrelevant_studied_bando_as_non_adatto(monkeypatch):
    detail = {"name": "Mobilità sostenibile - filiera degli autobus elettrici", "issuer": "MASE", "requirements": [], "rules": [], "status": "APERTO", "funding_modes": {}, "benefit": None}
    monkeypatch.setattr(matching.bandi, "get_bando_detail", lambda bid: detail)
    checks, missing = matching.relevance_checks("X", detail, RETAIL)
    assert [c["result"] for c in checks if c["id"] == "sector"] == ["FAIL"] and missing == []
    assert matching.is_relevant("X", RETAIL) is False
    assert matching.is_relevant("X", {**RETAIL, "ateco_code": "49.31.00"}) is True


def test_friuli_venezia_giulia_is_not_read_as_the_veneto_province_of_venezia():
    assert relevance.regions_in("Regione Autonoma Friuli Venezia Giulia") == {"Friuli Venezia Giulia"}
    assert relevance.regions_in("Camera di commercio di Venezia") == {"Veneto"}


def test_research_development_and_innovation_projects_are_for_research_and_production_activities():
    assert "sector" in ids(relevance.text_fails("Progetti di ricerca, sviluppo e innovazione per la transizione ecologica", "MASE", "", RETAIL))
    assert relevance.text_fails("Progetti di ricerca, sviluppo e innovazione per la transizione ecologica", "MASE", "", {**RETAIL, "ateco_code": "62.01.00"}) == []


def _seed_catalog(items):
    with connect() as conn:
        for bid, name, issuer, meta in items:
            conn.execute("INSERT INTO bandi (bando_id, name, issuer, source_url, catalog_status, extraction_status, deadline, summary, catalog_meta, meta_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                         (bid, name, issuer, "https://example.test/" + bid, "CATALOGED", "NOT_STARTED", "2099-12-31", "s", json.dumps(meta), "2026-11-07T00:00:00+00:00"))


def test_searching_and_browsing_for_a_company_flags_or_hides_bandi_that_do_not_concern_it():
    from app.core import bandi
    _seed_catalog([("CAT-VOUCHER-ABR", "Voucher digitalizzazione imprese Abruzzo", "Regione Abruzzo", {}),
                   ("CAT-VOUCHER-PIE", "Voucher digitalizzazione imprese Piemonte", "Regione Piemonte", {}),
                   ("CAT-VOUCHER-AUTOBUS", "Voucher per il rinnovo degli autobus", "Ministero", {})])
    names = [m["name"] for m in bandi.search_catalog("voucher", profile=RETAIL)]
    assert names == ["Voucher digitalizzazione imprese Abruzzo"]                       # niente altra regione, niente autobus
    assert len(bandi.search_catalog("voucher")) == 3                                    # senza profilo la ricerca resta quella di sempre
    page = bandi.browse_catalog("voucher", profile=RETAIL, page_size=10)["items"]
    why = {i["bando_id"]: i["not_for_you"] for i in page}
    assert why["CAT-VOUCHER-ABR"] is None and "Piemonte" in why["CAT-VOUCHER-PIE"] and "ATECO" in why["CAT-VOUCHER-AUTOBUS"]
    assert all(i["not_for_you"] is None for i in bandi.browse_catalog("voucher", page_size=10)["items"])         # senza profilo nessun giudizio


def test_issuer_names_the_sector_when_the_title_does_not():
    ids_ = lambda name, issuer: ids(relevance.text_fails(name, issuer, "", RETAIL))
    assert "sector" in ids_("Cambiale Azzurra: aperto il portale", "ISMEA")
    assert "sector" in ids_("Avviso per progetti oratoriali", "Dipartimento per lo Sport")
    assert "sector" in ids_("Educare alla lettura: la 9ª edizione", "Ministero della Cultura")
    assert ids_("Bando Voucher Doppia Transizione 2026", "Punto Impresa Digitale (Camere di commercio)") == []


def test_harvested_titles_without_a_name_or_that_are_news_are_not_grants():
    from app.core import official_sources as osrc
    for t in ("Consulta qui l'Avviso", "Il testo dell'avviso", "Avviso pubblico e allegato", "37° ciclo - Bando e modalità di presentazione domande",
              "Avviate le procedure di erogazione del contributo in favore dei gestori di impianti natatori per l'anno 2026", "Puglia Moltiplica. Boom di domande per Finanziamento Taranto JTF",
              "Bandi e Avvisi dei Soggetti Attuatori", "Bonus colonnine domestiche"):
        assert not osrc.looks_like_grant(t), t
    assert osrc.clean_title("Al via il Voucher Internazionalizzazione 2027: 15 milioni di euro per le PMI") == "Voucher Internazionalizzazione 2027: 15 milioni di euro per le PMI"
    assert osrc.looks_like_grant("Al via il Voucher Internazionalizzazione 2027: 15 milioni di euro per le PMI")


def test_old_harvested_entries_with_a_bad_title_are_discarded_but_studied_ones_never():
    from app.core import official_sources as osrc
    seed = {"harvested": True, "source_id": "x"}
    _seed_catalog([("CAT-BAD-1", "Consulta qui l'Avviso", "Ente", seed), ("CAT-GOOD-1", "Voucher digitalizzazione delle imprese 2099", "Ente", seed), ("CAT-OLD-1", "Il testo dell'avviso", "Ente", {})])
    with connect() as conn:
        conn.execute("INSERT INTO bandi (bando_id, name, issuer, catalog_status, extraction_status, catalog_meta) VALUES ('CAT-STUDIED-1','Consulta qui l''Avviso','Ente','CATALOGED','COMPLETED',?)", (json.dumps(seed),))
    assert osrc.purge_bad_titles() == 1
    with connect() as conn:
        st = {r["bando_id"]: r["extraction_status"] for r in conn.execute("SELECT bando_id, extraction_status FROM bandi").fetchall()}
    assert st == {"CAT-BAD-1": "REJECTED", "CAT-GOOD-1": "NOT_STARTED", "CAT-OLD-1": "NOT_STARTED", "CAT-STUDIED-1": "COMPLETED"}
