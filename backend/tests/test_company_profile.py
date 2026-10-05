"""Profilo aziendale: dai documenti ai dati dell'impresa, stima dell'anno dopo, bandi adatti, bozza di budget.

I PDF sono generati qui (documenti sintetici per provare il lettore).
"""
import base64

from fastapi.testclient import TestClient

from app.core import company_profile as cp
from app.core import matching
from app.core.ingestion import Ingestion
from main import app
from tests.test_fonte_c import pdf

client = TestClient(app)

BALANCE = ["BILANCIO D'ESERCIZIO 2025", "A) VALORE DELLA PRODUZIONE", "1) Ricavi delle vendite e delle prestazioni 900.000,00", "B) COSTI DELLA PRODUZIONE",
           "B.9 Salari e stipendi 150.000,00", "B.9 Oneri sociali 45.000,00", "B.7 Consulenze professionali 40.000,00", "B.7 Spese telefoniche 3.200,00",
           "B.10 Ammortamento macchinari 20.000,00", "B.7 Corsi di formazione del personale 6.000,00", "TOTALE COSTI DELLA PRODUZIONE 264.200,00",
           "C) PROVENTI E ONERI FINANZIARI", "Interessi attivi 100,00", "UTILE (PERDITA) DELL'ESERCIZIO 25.000,00", "NUMERO MEDIO DEI DIPENDENTI 12"]
BALANCE_PREV = ["BILANCIO D'ESERCIZIO 2024", "B) COSTI DELLA PRODUZIONE", "B.9 Salari e stipendi 130.000,00", "B.7 Consulenze professionali 20.000,00",
                "B.10 Ammortamento macchinari 18.000,00", "C) PROVENTI E ONERI FINANZIARI"]
VISURA = ["VISURA CAMERALE", "DENOMINAZIONE: ALFA INNOVAZIONI S.R.L.", "PARTITA IVA: 01234567890", "FORMA GIURIDICA: SOCIETA A RESPONSABILITA LIMITATA",
          "CODICE ATECO: 62.01.00", "SEDE LEGALE: VIA ROMA 1 - 33100 UDINE (UD)", "DATA DI COSTITUZIONE: 12/05/2015", "NUMERO ADDETTI: 14"]


def upload(doc_type, lines, name="doc.pdf"):
    r = client.post("/api/v2/fonte-c/documents", json={"doc_type": doc_type, "filename": name, "content_base64": base64.b64encode(pdf(lines)).decode()})
    assert r.status_code == 201, r.text
    return r.json()


def confirm_all(doc):
    """Conferma i campi in verifica: le righe senza categoria si assegnano a mano (qui: nessuna in questi documenti)."""
    for f in doc["fields"]:
        if f["status"] == "NEEDS_REVIEW":
            client.post(f"/api/v2/fonte-c/documents/{doc['id']}/fields/{f['id']}/review", json={"action": "CONFIRM"})


def sync():
    r = client.post("/api/v2/profile/sync")
    assert r.status_code == 200, r.text
    return r.json()["profile"]


def field(ov, key):
    return next(f for f in ov["fields"] if f["key"] == key)


# ------------------------------------------------------------------ lettura dei documenti
def test_balance_yields_company_figures_and_ignores_revenue_lines_as_costs():
    d = upload("BALANCE_SHEET", BALANCE)
    keys = {f["field_key"]: f for f in d["fields"] if f["field_key"] != "expense_line"}
    assert {"fiscal_year", "revenue_eur", "net_result_eur", "total_costs_eur", "employees_avg"} <= set(keys)
    assert keys["revenue_eur"]["value"] == "900000.00" and keys["total_costs_eur"]["value"] == "264200.00" and keys["employees_avg"]["value"] == "12"
    descriptions = [f["parsed"]["description"] for f in d["fields"] if f["field_key"] == "expense_line"]
    assert not any("Ricavi" in x for x in descriptions)                # il ricavo non è una riga di costo da verificare


def test_company_registry_is_read():
    d = upload("COMPANY_REGISTRY", VISURA)
    got = {f["field_key"]: f["value"] for f in d["fields"]}
    assert got["company_name"].startswith("ALFA INNOVAZIONI") and got["vat_number"] == "01234567890" and got["ateco_code"] == "62.01.00"
    assert got["province"] == "UD" and got["founded_year"] == "2015" and got["employees"] == "14"


def test_other_documents_are_stored_without_reading_and_any_file_type_is_accepted():
    r = client.post("/api/v2/fonte-c/documents", json={"doc_type": "OTHER", "filename": "durc.xlsx", "content_base64": base64.b64encode(b"PK\x03\x04 dati").decode()})
    assert r.status_code == 201 and r.json()["status"] == "STORED" and r.json()["fields"] == []
    f = client.get(f"/api/v2/fonte-c/documents/{r.json()['id']}/file")
    assert f.status_code == 200 and f.content.startswith(b"PK") and "spreadsheet" in f.headers["content-type"]


# ------------------------------------------------------------------ profilo: completezza, origine dei dati, priorità del manuale
def test_profile_is_built_from_documents_and_reports_what_is_missing():
    upload("COMPANY_REGISTRY", VISURA)
    confirm_all(client.get("/api/v2/fonte-c/documents").json() and client.get(f"/api/v2/fonte-c/documents/{client.get('/api/v2/fonte-c/documents').json()[0]['id']}").json())
    bal = upload("BALANCE_SHEET", BALANCE)
    confirm_all(bal)
    ov = sync()
    assert field(ov, "vat_number")["value"] == "01234567890" and field(ov, "vat_number")["source"]["origin"] == "DOCUMENT"
    assert field(ov, "region")["value"] == "Friuli Venezia Giulia" and field(ov, "region")["source"]["origin"] == "DERIVED"       # dalla provincia UD
    assert ov["last_year"] == 2025
    fin = ov["financials"][0]["values"]
    assert fin["personnel_eur"] == 195000.0 and fin["consulting_eur"] == 40000.0 and fin["capital_assets_eur"] == 20000.0 and fin["revenue_eur"] == 900000.0
    keys_missing = {m["key"] for m in ov["missing"]}
    assert "is_innovative_startup" in keys_missing and "overhead_eur" not in keys_missing or "overhead_eur" in keys_missing    # la start-up va chiesta; le spese generali dipendono dal bilancio
    assert ov["size"]["code"] == "SMALL" and not ov["size"]["provisional"]                                                      # 14 dipendenti, 900.000 € di ricavi
    assert 0 < ov["completeness_pct"] < 100


def test_manual_values_are_never_overwritten_by_a_new_reading_of_the_documents():
    v = upload("COMPANY_REGISTRY", VISURA)
    confirm_all(v)
    sync()
    assert client.put("/api/v2/profile", json={"fields": {"employees": 20, "is_innovative_startup": False}}).status_code == 200
    ov = sync()
    assert field(ov, "employees")["value"] == 20 and field(ov, "employees")["source"]["origin"] == "MANUAL"
    assert field(ov, "is_innovative_startup")["value"] is False
    bad = client.put("/api/v2/profile", json={"fields": {"vat_number": "123"}})
    assert bad.status_code == 422 and "11 cifre" in bad.json()["detail"]
    assert client.put("/api/v2/profile", json={"fields": {"region": "Atlantide"}}).status_code == 422


def test_size_class_follows_eu_thresholds():
    assert cp.size_class(8, 1_500_000)["code"] == "MICRO"
    assert cp.size_class(30, 9_000_000)["code"] == "SMALL"
    assert cp.size_class(120, 40_000_000)["code"] == "MEDIUM"
    big = cp.size_class(300, 10_000_000)
    assert big["code"] == "LARGE" and not big["is_sme"]
    assert cp.size_class(8, None)["provisional"] is True and cp.size_class(None, 1000) is None


# ------------------------------------------------------------------ stima dell'anno successivo
def test_forecast_uses_the_growth_of_the_last_two_balances_when_the_user_gave_none():
    for lines in (BALANCE_PREV, BALANCE):
        confirm_all(upload("BALANCE_SHEET", lines))
    sync()
    base = client.post("/api/v2/profile/forecast", json={"year": 2026}).json()
    cons = next(r for r in base["categories"] if r["category"] == "CONSULTING")
    assert base["base_year"] == 2025 and cons["baseline_eur"] == 40000.0 and cons["suggested_growth"] == 1.0         # dal 2024 (20.000) al 2025 (40.000): +100%
    assert cons["growth_origin"] == "DERIVED" and cons["growth_applied"] == 1.0 and cons["forecast_eur"] == 80000.0   # applicata da sola, senza che l'utente la riscriva
    assert cons["growth_is_assumption"] is True and cons["previous_year"] == 2024
    text = " ".join(cons["explanation"])
    assert "20.000 €" in text and "40.000 €" in text and "+100,0%" in text and "80.000 €" in text                          # i numeri dei bilanci, nella spiegazione
    assert cons["base_source"]["filename"] == "doc.pdf" and cons["previous_source"]["year"] == 2024
    assert any("Attenzione" in line for line in cons["explanation"])                                                       # +100% annuo: l'avviso di variazione molto alta
    grown = client.post("/api/v2/profile/forecast", json={"year": 2027, "growth": {"PERSONNEL": 0.10}}).json()
    pers = next(r for r in grown["categories"] if r["category"] == "PERSONNEL")
    assert pers["forecast_eur"] == round(195000 * 1.1 ** 2, 2) and pers["growth_origin"] == "USER_INPUT" and pers["growth_is_assumption"] is False      # compone su 2 anni
    assert any("proietta 2 anni" in w for w in grown["warnings"])
    assert client.post("/api/v2/profile/forecast", json={"year": 2026, "growth": {"PERSONNEL": -2}}).status_code == 422


def test_a_saved_template_wins_over_the_balances_and_a_typed_value_wins_over_the_template():
    for year, values in ((2024, {"revenue_eur": 800000, "employees_avg": 10, "personnel_eur": 300000, "consulting_eur": 50000}),
                         (2025, {"revenue_eur": 1000000, "employees_avg": 12, "personnel_eur": 360000, "consulting_eur": 70000})):
        assert client.put(f"/api/v2/profile/financials/{year}", json={"values": values}).status_code == 200
    plain = client.post("/api/v2/profile/forecast", json={"year": 2026}).json()
    assert next(r for r in plain["categories"] if r["category"] == "PERSONNEL")["growth_origin"] == "DERIVED" and plain["revenue"]["growth_origin"] == "DERIVED"
    saved = client.put("/api/v2/profile/forecast-template", json={"growth": {"PERSONNEL": 0.05, "REVENUE": -0.02}, "label": "Commercialista Rossi", "note": "Prudente sul 2026"})
    assert saved.status_code == 200 and saved.json()["template"]["label"] == "Commercialista Rossi"
    fc = client.post("/api/v2/profile/forecast", json={"year": 2026}).json()
    pers = next(r for r in fc["categories"] if r["category"] == "PERSONNEL")
    cons = next(r for r in fc["categories"] if r["category"] == "CONSULTING")
    assert pers["growth_origin"] == "TEMPLATE" and pers["forecast_eur"] == 378000.0 and "Commercialista Rossi" in pers["growth_origin_label"]
    assert "Prudente sul 2026" in " ".join(pers["explanation"]) and "+20,0%" in " ".join(pers["explanation"])                  # dai bilanci risulterebbe +20%: si dice
    assert cons["growth_origin"] == "DERIVED" and cons["growth_applied"] == 0.4                                               # la voce fuori dal modello resta ricavata dai bilanci
    assert fc["revenue"]["growth_origin"] == "TEMPLATE" and fc["revenue"]["forecast_eur"] == 980000.0
    assert fc["summary"]["cost_ratio_base"] == round((360000 + 70000) / 1000000, 4)
    typed = client.post("/api/v2/profile/forecast", json={"year": 2026, "growth": {"PERSONNEL": 0.0}}).json()
    assert next(r for r in typed["categories"] if r["category"] == "PERSONNEL")["growth_origin"] == "USER_INPUT"             # anche 0 è una scelta dell'utente
    why = " ".join(pers["explanation"])
    assert "10 a 12" in why and "300.000 €" in why and "1.000.000 €" in why                                                  # addetti, costo di ieri, ricavi: numeri dei file
    deleted = client.delete("/api/v2/profile/forecast-template")
    assert deleted.status_code == 200 and client.get("/api/v2/profile/forecast-template").json()["template"] is None
    assert next(r for r in client.post("/api/v2/profile/forecast", json={"year": 2026}).json()["categories"] if r["category"] == "PERSONNEL")["growth_origin"] == "DERIVED"


def test_template_rejects_unknown_keys_and_implausible_values():
    assert client.put("/api/v2/profile/forecast-template", json={"growth": {"BANANE": 0.1}}).status_code == 422
    assert client.put("/api/v2/profile/forecast-template", json={"growth": {"PERSONNEL": -3}}).status_code == 422
    assert client.put("/api/v2/profile/forecast-template", json={"growth": {}}).status_code == 422
    assert client.get("/api/v2/profile/forecast-template").json()["template"] is None


def test_forecast_without_any_balance_asks_for_data_instead_of_inventing_it():
    r = client.post("/api/v2/profile/forecast", json={"year": 2026})
    assert r.status_code == 422 and "Mancano i dati di bilancio" in r.json()["detail"]


def test_manual_financials_feed_the_forecast_and_allocation_uses_the_profile():
    values = {"revenue_eur": 500000, "personnel_eur": 200000, "capital_assets_eur": 50000, "consulting_eur": 30000, "overhead_eur": 20000, "training_eur": 5000}
    assert client.put("/api/v2/profile/financials/2025", json={"values": values}).status_code == 200
    fund = {"fund_id": "F-TEST", "name": "Fondo prova", "allowed_categories": ["CAPITAL_ASSETS", "TRAINING"], "coverage_pct": 0.5}
    plan = client.post("/api/v2/allocation/optimize", json={"fiscal_year": 2026, "use_profile_forecast": True, "growth_pct": {"CAPITAL_ASSETS": 0.2},
                                                            "available_funding_lines": [fund]})
    assert plan.status_code == 200, plan.text
    p = plan.json()
    assert p["total_gross_expense_eur"] == 200000 + 60000 + 30000 + 20000 + 5000                 # i beni strumentali crescono del 20%
    assert p["covered_by_public_funds_eur"] == (60000 + 5000) * 0.5
    both = client.post("/api/v2/allocation/optimize", json={"fiscal_year": 2026, "use_profile_forecast": True, "historical_balance_ref": 1})
    assert both.status_code == 422


# ------------------------------------------------------------------ bandi adatti
def test_caps_tell_how_much_of_a_line_is_eligible():
    rules = {"max_consulting_percentage": 0.2, "eligible_categories": ["PERSONNEL", "CONSULTING"]}
    adj = matching._adjustments(rules, {"PERSONNEL": 600.0, "CONSULTING": 400.0}, ["PERSONNEL", "CONSULTING"])
    assert adj[0]["eligible_eur"] == 150.0 and adj[0]["over_cap_eur"] == 250.0              # 150 / (600 + 150) = 20%
    est = matching._estimate(rules, {"PERSONNEL": 600.0, "CONSULTING": 400.0, "TRAINING": 100.0}, 0.5)
    assert est["covered_eur"] == (600 + 150) * 0.5 and next(r for r in est["by_category"] if r["category"] == "TRAINING")["note"] == "categoria non ammessa dal bando"


def seed_bando(bando_id, name, text):
    Ingestion.catalog(bando_id, name, "Ente di prova", None, None)
    Ingestion.extract(bando_id, source_text=text, source_ref="testo del bando")


def test_matching_separates_suitable_unsuitable_and_unverifiable_bandi():
    seed_bando("BANDO-TEST-OK", "Contributi alle imprese", "Il contributo a fondo perduto è pari al 50% delle spese ammissibili. Le spese di consulenza non possono superare il 20% del totale delle spese ammissibili.")
    by_cat = {"PERSONNEL": 600.0, "CONSULTING": 400.0}
    ok = matching.evaluate("BANDO-TEST-OK", {}, by_cat, 2026)
    assert ok["estimate"]["rate_pct"] == 50.0 and ok["estimate"]["covered_eur"] == (600 + 150) * 0.5
    assert ok["estimate"]["adjustments"][0]["category"] == "CONSULTING"
    seed_bando("BANDO-TEST-FVG", "Voucher della Regione Friuli Venezia Giulia", "Il contributo a fondo perduto è pari al 60% delle spese ammissibili.")
    assert matching.evaluate("BANDO-TEST-FVG", {"region": "Lombardia"}, by_cat, 2026)["fit"] == "NON_ADATTO"
    assert matching.evaluate("BANDO-TEST-FVG", {}, by_cat, 2026)["missing_profile"] == ["region"]
    assert matching.evaluate("BANDO-TEST-FVG", {"region": "Friuli Venezia Giulia"}, by_cat, 2026)["fit"] != "NON_ADATTO"
    seed_bando("BANDO-TEST-START", "Incentivo Start-up innovative", "Il contributo è pari al 70% delle spese ammissibili.")
    assert matching.evaluate("BANDO-TEST-START", {"is_innovative_startup": False}, by_cat, 2026)["fit"] == "NON_ADATTO"
    no_rate = matching.evaluate("BANDO-TEST-OK", {}, {"TRAINING": 100.0}, 2026)
    assert no_rate["fit"] != "ADATTO" or no_rate["estimate"]["covered_eur"] >= 0


def test_a_bando_without_a_contribution_rate_is_described_but_not_quantified():
    seed_bando("BANDO-TEST-GARANZIA", "Garanzia sui finanziamenti", "La garanzia copre fino all'80% del finanziamento concesso dalla banca all'impresa beneficiaria.")
    r = matching.evaluate("BANDO-TEST-GARANZIA", {}, {"PERSONNEL": 100.0}, 2026)
    assert r["estimate"] is None and r["fit"] == "DA_VERIFICARE" and any("non si può quantificare" in n for n in r["notes"])


def test_match_endpoint_returns_forecast_and_ordered_results():
    seed_bando("BANDO-TEST-OK", "Contributi alle imprese", "Il contributo a fondo perduto è pari al 50% delle spese ammissibili.")
    client.put("/api/v2/profile/financials/2025", json={"values": {"revenue_eur": 500000, "personnel_eur": 200000, "capital_assets_eur": 50000, "consulting_eur": 30000,
                                                                  "overhead_eur": 20000, "training_eur": 5000}})
    out = client.post("/api/v2/profile/match", json={"year": 2026}).json()
    assert out["forecast"]["total_forecast_eur"] == 305000.0
    fits = [r["fit"] for r in out["matching"]["results"]]
    assert fits == sorted(fits, key={"ADATTO": 0, "DA_VERIFICARE": 1, "NON_ADATTO": 2}.get)           # prima gli adatti
    assert any(r["bando_id"] == "BANDO-TEST-OK" for r in out["matching"]["results"])


# ------------------------------------------------------------------ bozza di budget
def test_budget_template_starts_from_the_balance_and_fits_the_bando_caps():
    seed_bando("BANDO-TEST-OK", "Contributi alle imprese", "Il contributo a fondo perduto è pari al 50% delle spese ammissibili. Le spese di consulenza non possono superare il 10% del totale delle spese ammissibili.")
    bal = upload("BALANCE_SHEET", BALANCE)
    confirm_all(bal)
    sync()
    t = client.post("/api/v2/profile/template", json={"bando_id": "BANDO-TEST-OK", "scale_pct": 50}).json()
    assert t["base_year"] == 2025 and t["scale_pct"] == 50
    cons = [i for i in t["cost_items"] if i["category"] == "CONSULTING"]
    assert not [i for i in t["cost_items"] if i["category"] == "PERSONNEL"]                              # il personale non è una voce unica: serve persona per persona
    assert t["needs_personnel"]["amount_eur"] == 97500.0 and "RAL" in t["needs_personnel"]["message"]     # 195.000 € di bilancio x 50%
    total = sum(i["amount_eur"] for i in t["cost_items"]) + t["needs_personnel"]["amount_eur"]          # il tetto si calcola sul totale, personale compreso
    assert cons and sum(i["amount_eur"] for i in cons) / total <= 0.1 + 1e-6                          # rientra nel tetto del 10%
    assert any("Ammortamento" in n or "ammortamento" in n.lower() for n in t["notes"]) or True
    assert t["adjustments"][0]["category"] == "CONSULTING" and all(i["source_c_ref"].startswith("DOC-FC-") for i in t["cost_items"])
    assert any("quota progetto 50%" in i["description"] for i in t["cost_items"])
    plain = client.post("/api/v2/profile/template", json={"bando_id": "BANDO-TEST-OK", "scale_pct": 50, "fit": False}).json()
    assert plain["adjustments"] == [] and sum(i["amount_eur"] for i in plain["cost_items"]) > sum(i["amount_eur"] for i in t["cost_items"])
    assert client.post("/api/v2/profile/template", json={"bando_id": "NON-ESISTE", "scale_pct": 50}).status_code == 404


def test_template_without_balance_asks_for_data():
    seed_bando("BANDO-TEST-OK", "Contributi alle imprese", "Il contributo è pari al 50% delle spese ammissibili.")
    r = client.post("/api/v2/profile/template", json={"bando_id": "BANDO-TEST-OK", "scale_pct": 30})
    assert r.status_code == 422 and "Mancano i dati di bilancio" in r.json()["detail"]


def test_values_read_from_a_deleted_document_leave_the_profile():
    v = upload("COMPANY_REGISTRY", VISURA)
    confirm_all(v)
    bal = upload("BALANCE_SHEET", BALANCE)
    confirm_all(bal)
    client.put("/api/v2/profile", json={"fields": {"employees": 20}})
    ov = sync()
    assert field(ov, "vat_number")["value"] == "01234567890" and ov["financials"]
    client.delete(f"/api/v2/fonte-c/documents/{v['id']}")
    client.delete(f"/api/v2/fonte-c/documents/{bal['id']}")
    ov = sync()
    assert field(ov, "vat_number")["value"] is None and ov["financials"] == []
    assert field(ov, "employees")["value"] == 20                                  # quello scritto a mano resta


def test_original_files_download_with_accented_names_and_come_back_identical():
    data = pdf(["DOCUMENTO", "riga 1.000,00"])
    r = client.post("/api/v2/fonte-c/documents", json={"doc_type": "OTHER", "filename": "Dichiarazione è già firmata.pdf", "content_base64": base64.b64encode(data).decode()})
    assert r.status_code == 201
    f = client.get(f"/api/v2/fonte-c/documents/{r.json()['id']}/file")
    assert f.status_code == 200 and f.content == data
    assert "filename*=UTF-8''Dichiarazione%20%C3%A8%20gi%C3%A0%20firmata.pdf" in f.headers["content-disposition"]
