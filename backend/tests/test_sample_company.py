"""I documenti dell'azienda di prova (scripts/make_sample_company.py) devono essere letti per intero dal profilo, senza righe ambigue."""
import base64
import pathlib
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import make_sample_company as sample  # noqa: E402
from app.core.fonte_c.parsers import classify_cost  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)


def upload_all(tmp_path):
    docs = {}
    for kind, path in sample.build(tmp_path):
        r = client.post("/api/v2/fonte-c/documents", json={"doc_type": kind, "filename": path.name, "content_base64": base64.b64encode(path.read_bytes()).decode()})
        assert r.status_code == 201, (path.name, r.text)
        docs[path.name] = r.json()
    return docs


def test_sample_documents_fill_the_profile_without_manual_review(tmp_path):
    docs = upload_all(tmp_path)
    # nessuna riga ambigua nei documenti letti: il profilo si compila senza interventi
    for name, d in docs.items():
        if d["doc_type"] == "OTHER":
            assert d["status"] == "STORED"
            continue
        review = [f for f in d["fields"] if f["status"] == "NEEDS_REVIEW" and f["field_key"] not in ("ral_annual_eur",)]
        assert not review, (name, [(f["field_key"], f["value"], f.get("parsed"), f["confidence"], f.get("snippet")) for f in review])

    ov = client.post("/api/v2/profile/sync").json()["profile"]
    val = {f["key"]: f["value"] for f in ov["fields"]}
    assert val["legal_name"].startswith("MERIDIANA DIGITAL SOLUTIONS") and val["vat_number"] == sample.COMPANY["vat"]
    assert val["ateco_code"] == "62.01.00" and val["province"] == "TO" and val["region"] == "Piemonte" and val["founded_year"] == 2016 and val["employees"] == 17
    assert [f["fiscal_year"] for f in ov["financials"]] == [2023, 2024, 2025]
    for f in ov["financials"]:
        y = f["fiscal_year"]
        fig = sample.balance_figures(y)
        v = f["values"]
        assert v["revenue_eur"] == sample.REVENUE[sample._idx(y)] and v["total_costs_eur"] == fig["costs"] and v["net_result_eur"] == fig["net"]
        assert v["employees_avg"] == sample.EMPLOYEES[y] and f["partial"] is None
        by = {k: sum(x[2][sample._idx(y)] for x in sample.COST_LINES if classify_cost(x[0])[0] == k) for k in ("PERSONNEL", "CAPITAL_ASSETS", "CONSULTING", "OVERHEAD", "TRAINING")}
        assert v["personnel_eur"] == by["PERSONNEL"] and v["consulting_eur"] == by["CONSULTING"] and v["training_eur"] == by["TRAINING"]
        assert v["overhead_eur"] == by["OVERHEAD"] and v["capital_assets_eur"] == by["CAPITAL_ASSETS"]
        # le cinque categorie sommano il totale dei costi: nessuna riga persa né contata due volte
        assert round(sum(by.values()), 2) == fig["costs"], y
    # resta da rispondere solo alla domanda che nessun documento può dire
    assert [m["key"] for m in ov["missing"]] == ["is_innovative_startup"]
    assert ov["size"]["code"] == "SMALL"
    client.put("/api/v2/profile", json={"fields": {"is_innovative_startup": False}})
    assert client.get("/api/v2/profile").json()["completeness_pct"] == 100


def test_payslips_f24_and_draft_are_read(tmp_path):
    docs = upload_all(tmp_path)
    pay = docs["05_Busta_paga_agosto_2026_Bertone_Andrea.pdf"]
    f = {x["field_key"]: x for x in pay["fields"]}
    assert f["gross_monthly_eur"]["value"] == "2980.77" and f["mensilita"]["value"] == "14" and f["level"]["value"] == "3" and f["period"]["value"] == "08/2026"
    assert f["employee_name"]["value"].startswith("TOK-") and "BERTONE" not in str(pay)
    f24 = docs["07_F24_pagamento_16-09-2026.pdf"]
    rows = [x["parsed"] for x in f24["fields"] if x["field_key"] == "f24_row"]
    assert [(r["codice_tributo"], r["anno"], r["importo_debito_eur"]) for r in rows] == [("1001", "2026", "21486.30"), ("1040", "2026", "3120.00"), ("6008", "2026", "15284.55")]
    assert all(x["status"] == "AUTO" for x in f24["fields"] if x["field_key"] == "f24_row")
    draft = docs["09_Bozza_candidatura_Progetto_Atlas.pdf"]
    lines = [x["parsed"] for x in draft["fields"] if x["field_key"] == "expense_line"]
    assert len(lines) == 6 and all(x["category"] for x in lines) and sum(float(x["amount_eur"]) for x in lines) == 287900.0
