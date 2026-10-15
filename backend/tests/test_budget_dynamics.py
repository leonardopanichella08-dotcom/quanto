"""Le dinamiche strutturali del budget con un cliente che ha tutti i dati (l'azienda di prova):
1. il budget nasce già con il personale persona per persona (livello, CCNL, RAL, quota di tempo), senza chiedere nulla;
2. dall'allocazione si passa ai budget dei singoli bandi, che stanno bene insieme;
3. il budget si costruisce sulla previsione (budget dell'azienda, piano degli investimenti, previsione dal bilancio), non sull'ammortamento passato;
4. le spese si leggono per voce (affitti, energia, licenze…), da tutti i documenti, non solo per le cinque categorie."""
import base64
import pathlib
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import make_sample_company as sample  # noqa: E402
from app.core import expense_types  # noqa: E402
from app.core.fonte_c import sheets  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)
NEEDED = ("04_Bilancio_2025", "14_Organico", "15_Libro_cespiti", "33_Registro_fatture_ricevute", "34_Controllo_commesse", "35_Business_plan_modello", "13_Registro_aiuti", "_Busta_paga_")


def hq():
    from tests.conftest import manager_token
    return {"Authorization": f"Bearer {manager_token()}"}


@pytest.fixture
def company(tmp_path):
    for kind, path in sample.build(tmp_path):
        if not any(k in path.name for k in NEEDED):
            continue
        r = client.post("/api/v2/fonte-c/documents", json={"doc_type": kind, "filename": path.name, "content_base64": base64.b64encode(path.read_bytes()).decode()})
        assert r.status_code == 201, (path.name, r.text)
    client.post("/api/v2/profile/sync")
    client.get("/api/v2/bandi")                          # semina il catalogo curato


# ------------------------------------------------------------------------------------------------ 4. le voci di spesa
def test_the_expense_taxonomy_is_finer_than_five_categories_and_consistent():
    assert len(expense_types.TYPES) >= 50
    for code, t in expense_types.TYPES.items():
        assert t["category"] in ("PERSONNEL", "CAPITAL_ASSETS", "CONSULTING", "OVERHEAD", "TRAINING", "OTHER"), code
    c = expense_types.classify_type
    assert c("Affitto della sede legale di via Garibaldi") == "OH_AFFITTI" and c("Spese condominiali dell'unità locale") == "OH_CONDOMINIO"
    assert c("Consulenze legali e contrattuali", "CONSULTING") == "CONS_LEGALI" and c("Compensi a professionisti per sviluppo applicativo", "CONSULTING") == "CONS_ALTRE"
    assert c("Licenze software: sicurezza e antivirus", "CAPITAL_ASSETS") == "CAP_SOFTWARE" and c("Servizi cloud: hosting", "CAPITAL_ASSETS") == "CAP_CLOUD"
    assert c("Ammortamento delle immobilizzazioni immateriali") == "CAP_AMMORT" and c("Ammortamento macchine d'ufficio", "CAPITAL_ASSETS") == "CAP_AMMORT"
    assert c("Una voce mai vista", "OVERHEAD") == "OH_GENERALI" and c("Una voce mai vista") is None          # non si inventa una voce
    assert c("Imposta di bollo") == "OTH_IMPOSTE"


def test_a_bando_text_says_which_expense_types_it_excludes_and_admits_with_the_sentence_as_proof():
    text = ("Non sono ammissibili le spese di rappresentanza, le fideiussioni e le spese di locazione. Sono ammissibili le spese per brevetti e per licenze software. "
            "Le spese per IVA non sono ammissibili. Sono ammissibili le spese di viaggio. Non sono ammissibili le spese di viaggio per il personale dipendente.")
    sc = expense_types.type_scope(text)
    assert {"OH_RAPPRES", "OH_AFFITTI", "OH_BANCARIE", "OTH_IMPOSTE"} <= set(sc["excluded"])
    assert {"CONS_PI", "CAP_SOFTWARE"} <= set(sc["eligible"])
    assert "OH_VIAGGI" not in sc["excluded"] and "OH_VIAGGI" not in sc["eligible"]                     # detto nei due sensi: non si decide
    assert "rappresentanza" in sc["excluded"]["OH_RAPPRES"][0].lower()
    assert expense_types.type_scope("x" * 500 + " non sono ammissibili le spese di locazione")["excluded"] == {}            # un impaginato rotto non è un'affermazione


def test_an_excluded_expense_type_is_rejected_by_name_even_inside_an_admitted_category(company):
    det = client.get("/api/v2/bandi/FVG-VALIDAZIONE-TRL-2026").json()
    rules = {**det["grant_rules"], "excluded_expense_types": ["CONS_LEGALI"], "eligible_categories": ["CONSULTING"]}
    items = [{"item_id": "A", "description": "Consulenza legale", "category": "CONSULTING", "amount_eur": 1000, "source_c_ref": "DOC-1", "expense_type": "CONS_LEGALI"},
             {"item_id": "B", "description": "Consulenza tecnica", "category": "CONSULTING", "amount_eur": 1000, "source_c_ref": "DOC-1", "expense_type": "CONS_TECNICHE"}]
    r = client.post("/api/v2/budget/validate", json={"project_id": "PRJ-X", "grant_rules": rules, "cost_items": items})
    assert r.status_code == 200, r.text
    by = {i["item_id"]: i for i in r.json()["items"]}
    assert by["A"]["status"] == "REJECTED" and 16 in by["A"]["criteria_failed"] and "esclusa" in by["A"]["rejection_reason"]
    assert by["B"]["status"] != "REJECTED"


# ------------------------------------------------------------------------------------------------ 4. tutti i documenti, anche gli Excel
def test_every_spreadsheet_of_the_company_is_read_and_personal_data_never_enters(tmp_path):
    out = {}
    for kind, path in sample.build(tmp_path):
        if path.suffix == ".xlsx":
            summary, fields, seen = sheets.read_workbook(path.read_bytes())
            out[path.name] = (fields, seen)
    kinds = {f.key for fields, _ in out.values() for f in fields}
    assert {"staff_member", "asset_line", "dep_plan_line", "supplier_spend", "aid_received", "capex_plan", "hiring_plan", "budget_line"} <= kinds
    staff = out["14_Organico_e_livelli_CCNL.xlsx"][0]
    assert sum(1 for f in staff if f.key == "staff_member") == 17
    blob = " ".join(f.value + f.snippet for fields, _ in out.values() for f in fields)
    for private in ("Ferraris", "FRRGLI", "Bertone", "Giulia", "BRTNDR"):
        assert private not in blob, private                           # nome, cognome e codice fiscale restano fuori: c'è solo il token
    budget = [f for f in out["34_Controllo_commesse_e_budget_2026.xlsx"][0] if f.key == "budget_line"]
    assert len(budget) >= 100 and all('"expense_type"' in f.value for f in budget)


def test_the_company_profile_exposes_staff_assets_and_expenses_by_type(company):
    st = client.get("/api/v2/profile/staff").json()
    assert len(st["people"]) == 17 and len({p["token"] for p in st["people"]}) == 17
    assert all(p["ccnl_code"] == "COMMERCIO" and p["level"] and p["ral_eur"] and p["hours_week"] for p in st["people"])
    assert all(p["payslip_document_id"] for p in st["people"])                       # la busta paga di ogni persona è stata letta e collegata
    assert all(abs(p["payslip_ral_eur"] / p["ral_eur"] - 1) < 0.01 for p in st["people"] if p.get("payslip_ral_eur"))      # RAL del cedolino e del registro dicono la stessa cosa
    assert "Ferraris" not in str(st) and "FRRGLI" not in str(st)
    assert {h["role"] for h in st["hiring_plan"]} >= {"Data engineer", "Commerciale junior"}
    a = client.get("/api/v2/profile/assets").json()
    assert len(a["assets"]) == 66 and a["depreciation_by_year"]["2026"] > 50000
    ex = client.get("/api/v2/profile/expenses").json()
    assert ex["year"] == 2025 and len(ex["types"]) >= 25
    fin = next(f for f in client.get("/api/v2/profile").json()["financials"] if f["fiscal_year"] == 2025)["values"]
    for cat, key in (("CONSULTING", "consulting_eur"), ("OVERHEAD", "overhead_eur"), ("TRAINING", "training_eur"), ("PERSONNEL", "personnel_eur")):
        assert abs(ex["by_category"][cat] - float(fin[key])) < 1.0, cat                # la somma delle voci è il totale della categoria
    facts = client.get("/api/v2/profile/facts").json()
    assert facts["counts"]["staff_member"] == 17 and facts["counts"]["budget_line"] >= 100


# ------------------------------------------------------------------------------------------------ 1 e 3. il budget dall'azienda
def test_the_template_has_every_person_with_level_ccnl_ral_and_time_and_typed_expenses_from_the_forecast(company):
    # una versione del contratto con soli i livelli 3 e 4 (stessi parametri): chi sta a un altro livello resta senza tabella, e il budget lo dice
    from app.core import fonte_b_admin as admin
    d = admin.create_draft("CCNL", "COMMERCIO", "CCNL COMMERCIO", "ridotta", __import__("datetime").date(2001, 1, 1), None, "Fonte di prova", "https://esempio.test/c", None, "t.csv",
                           b"level;standard_hours;social_charges_pct;tfr_pct" + bytes([10]) + b"3;1680;29,5%;8,33%" + bytes([10]) + b"4;1680;29,5%;8,33%" + bytes([10]), "test")
    admin.publish(d["id"], "test", attest_official=True)
    r = client.post("/api/v2/profile/template", json={"bando_id": "FVG-VALIDAZIONE-TRL-2026", "scale_pct": 40, "fit": True})
    assert r.status_code == 200, r.text
    t = r.json()
    people = [i for i in t["cost_items"] if i["category"] == "PERSONNEL"]
    assert len(people) == 17 and t["needs_personnel"] is None                         # il personale c'è già: niente da chiedere
    assert all(p["ccnl_code"] == "COMMERCIO" and p["employee_level"] and p["ral_eur"] > 0 and p["fte_allocation"] == 0.4 and p["employee_token"].startswith("TOK-") for p in people)
    part_time = next(p for p in t["personnel"] if p["hours_week"] == 30)
    assert part_time["fte_allocation"] == 0.4                                         # quota del PROPRIO tempo: la RAL del part-time è già ridotta
    others = [i for i in t["cost_items"] if i["category"] != "PERSONNEL"]
    assert others and all(i["expense_type"] for i in others)
    assert not any(i["expense_type"] == "CAP_AMMORT" for i in others)                  # l'ammortamento non è una spesa futura
    bases = {b["basis"] for b in t["basis"]}
    assert {"BUDGET", "PIANO_INVESTIMENTI"} <= bases and t["year"] == 2026
    assert any("ammortamento" in n.lower() and "non è una spesa futura" in n for n in t["notes"])
    assert any("budget 2026 dell'azienda" in n for n in t["notes"])                    # il budget del cliente e la previsione dal bilancio si confrontano, con i numeri
    assert any(b["code"] == "CAP_IMMATERIALI" and b["basis"] == "PIANO_INVESTIMENTI" for b in t["basis"])
    assert all(b["sources"] and b["sources"][0].get("filename") for b in t["basis"])    # ogni numero dice da quale documento viene
    missing = [n for n in t["needs_input"] if "livello" in n]
    assert missing and all("bozza che aggiunge anche questo livello" in n for n in missing)      # manca il livello: lo si dice e si indica come completarlo, senza inventare nulla


def test_the_forecast_base_is_used_when_the_company_has_no_own_budget(tmp_path):
    for kind, path in sample.build(tmp_path):
        if "04_Bilancio_2025" in path.name:
            assert client.post("/api/v2/fonte-c/documents", json={"doc_type": kind, "filename": path.name, "content_base64": base64.b64encode(path.read_bytes()).decode()}).status_code == 201
    client.post("/api/v2/profile/sync")
    client.get("/api/v2/bandi")
    t = client.post("/api/v2/profile/template", json={"bando_id": "FVG-VALIDAZIONE-TRL-2026", "scale_pct": 100, "fit": False}).json()
    assert {b["basis"] for b in t["basis"]} == {"PREVISIONE"} and t["needs_personnel"] is not None          # senza organico lo si chiede; senza budget si parte dalla previsione
    assert any("investimenti previsti" in m for m in t["needs_input"])                                    # e si dice che mancano gli investimenti, senza trasformare l'ammortamento in acquisti
    assert not any(i.get("expense_type") == "CAP_AMMORT" for i in t["cost_items"])


# ------------------------------------------------------------------------------------------------ 2. dall'allocazione ai budget
FUNDS = ({"fund_id": "F-FVG", "name": "FVG validazione TRL", "bando_id": "FVG-VALIDAZIONE-TRL-2026", "allowed_categories": ["PERSONNEL", "CAPITAL_ASSETS", "CONSULTING"], "coverage_pct": 0.5,
          "category_max_share": {"CONSULTING": 0.45}},
         {"fund_id": "F-SOST", "name": "Investimenti sostenibili 4.0", "bando_id": "INVESTIMENTI-SOSTENIBILI-4.0-2026", "allowed_categories": ["CAPITAL_ASSETS"], "coverage_pct": 0.75})


def _plan(lines):
    r = client.post("/api/v2/allocation/optimize", json={"fiscal_year": 2026, "use_profile_forecast": True, "available_funding_lines": lines})
    assert r.status_code == 200, r.text
    return r.json()


def test_allocation_lines_are_expense_types_not_categories(company):
    plan = _plan(list(FUNDS))
    ids = [ln["item_id"] for ln in plan["allocation_plan"]]
    assert "STIMA-PERSONALE" in ids and any(i.startswith("STIMA-OH_AFFITTI") for i in ids) and any(i.startswith("STIMA-CONS_TECNICHE") for i in ids)
    assert all(ln["label"] for ln in plan["allocation_plan"])
    assert not any("AMMORT" in i for i in ids)


def test_a_fund_that_excludes_a_type_by_name_never_covers_it(company):
    plan = _plan([{**FUNDS[0], "allowed_categories": ["PERSONNEL", "CAPITAL_ASSETS", "CONSULTING", "OVERHEAD"], "excluded_expense_types": ["OH_AFFITTI", "OH_RAPPRES"]}])
    by = {ln["item_id"]: ln for ln in plan["allocation_plan"]}
    rent = next(v for k, v in by.items() if k.startswith("STIMA-OH_AFFITTI"))
    other = next(v for k, v in by.items() if k.startswith("STIMA-OH_ENERGIA"))
    assert rent["covered_amount_eur"] == 0 and other["covered_amount_eur"] > 0


def test_the_allocation_becomes_one_budget_per_bando_and_they_are_admissible_together(company):
    lines = list(FUNDS)
    plan = _plan(lines)
    r = client.post("/api/v2/allocation/budgets", json={"allocation": plan, "fiscal_year": 2026, "funding_lines": lines})
    assert r.status_code == 200, r.text
    out = r.json()
    assert {b["fund_id"] for b in out["budgets"]} == {"F-FVG", "F-SOST"} and out["ok"]
    checks = {c["key"]: c for c in out["cross_checks"]}
    assert all(checks[k]["status"] == "PASS" for k in ("coverage", "fte", "exclusions", "cumulation", "de_minimis"))
    assert checks["criteria"]["status"] in ("PASS", "WARN")
    # nessuna persona oltre il 100% del tempo sommando tutti i budget
    per_person = {}
    for b in out["budgets"]:
        for it in b["cost_items"]:
            if it.get("employee_token"):
                per_person[it["employee_token"]] = per_person.get(it["employee_token"], 0) + it["fte_allocation"]
    assert per_person and max(per_person.values()) <= 1.0 + 1e-9
    # il contributo previsto di ogni budget torna con l'allocazione
    cov = {}
    for ln in plan["allocation_plan"]:
        for c in ln["coverage"]:
            cov[c["fund_id"]] = cov.get(c["fund_id"], 0) + c["covered_amount_eur"]
    for b in out["budgets"]:
        assert abs(b["contribution_planned_eur"] - cov[b["fund_id"]]) < 0.05
        assert b["bando_id"] and b["cost_items"] and b["validation"] is not None
    # le spese pagate da due bandi insieme compaiono in entrambi e dichiarano l'altro contributo (controlli 47-48)
    shared = [it for it in next(b for b in out["budgets"] if b["fund_id"] == "F-SOST")["cost_items"] if it.get("funding_ids")]
    assert shared and all(it["funding_ids"] == ["F-FVG"] and it["other_aid_eur"] > 0 for it in shared)
    # ogni voce è controllabile dal motore con le regole del suo bando
    for b in out["budgets"]:
        det = client.get(f"/api/v2/bandi/{b['bando_id']}").json()
        v = client.post("/api/v2/budget/validate", json={"project_id": f"PRJ-{b['fund_id']}", "grant_rules": det["grant_rules"], "cost_items": b["cost_items"]})
        assert v.status_code == 200, v.text


def test_budgets_never_double_count_a_cost_when_funds_split_it(company):
    """Se due fondi non sono cumulabili, ogni spesa va a uno solo e i costi attribuiti non superano la spesa (nessun doppio conteggio)."""
    lines = [{**FUNDS[0], "max_total_eur": 100000, "excludes": ["F-SOST"]}, FUNDS[1]]
    plan = _plan(lines)
    out = client.post("/api/v2/allocation/budgets", json={"allocation": plan, "fiscal_year": 2026, "funding_lines": lines}).json()
    assert out["ok"]
    rate = {"F-FVG": 0.5, "F-SOST": 0.75}
    for ln in plan["allocation_plan"]:
        parts = [c for c in ln["coverage"] if c["covered_amount_eur"] > 0]
        assert len(parts) <= 1                                                         # fondi non cumulabili: mai la stessa spesa
        assert sum(c["covered_amount_eur"] / rate[c["fund_id"]] for c in parts) <= ln["gross_amount_eur"] + 0.05
    assert all(not it.get("funding_ids") for b in out["budgets"] for it in b["cost_items"])
