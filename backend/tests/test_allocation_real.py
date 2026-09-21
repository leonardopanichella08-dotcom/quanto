"""Missione Due su dati veri: le spese vengono dal bilancio caricato (Fonte C), i fondi dai bandi (Fonte A)."""
import base64
import json

from fastapi.testclient import TestClient

from app.core.ingestion import Ingestion
from main import app
from tests.test_fonte_c import BALANCE, pdf

client = TestClient(app)


def hq():
    tok = client.post("/api/v2/hq/login", json={"code": "QUANTO_1"}).json()["token"]
    return {"X-HQ-Token": tok}


def upload_balance(lines=BALANCE):
    return client.post("/api/v2/fonte-c/documents", json={"doc_type": "BALANCE_SHEET", "filename": "b.pdf", "content_base64": base64.b64encode(pdf(lines)).decode()}).json()


def make_bando(bando_id="BANDO-FONDO", text="Il contributo è pari al 60% delle spese ammissibili.\nLe consulenze non possono superare il 20% del totale."):
    Ingestion.catalog(bando_id, "Fondo di prova", "Ente", None, None)
    Ingestion.extract(bando_id, source_text=text)


def resolve_all_lines(doc):
    for f in doc["fields"]:
        if f["field_key"] == "expense_line" and f["status"] == "NEEDS_REVIEW":
            body = {"description": f["parsed"]["description"], "amount_eur": f["parsed"]["amount_eur"], "category": "OVERHEAD"}
            client.post(f"/api/v2/fonte-c/documents/{doc['id']}/fields/{f['id']}/review", json={"action": "CORRECT", "value": json.dumps(body)})


def test_no_active_fund_means_no_plan_and_a_clear_message():
    doc = upload_balance()
    resolve_all_lines(doc)
    r = client.post("/api/v2/allocation/optimize", json={"fiscal_year": 2027, "historical_balance_ref": doc["id"]})
    assert r.status_code == 409 and "linea di finanziamento" in r.json()["detail"]


def test_fund_is_derived_from_published_rules_and_missing_contribution_rate_is_refused():
    make_bando("SENZA-CONTRIBUTO", "Le consulenze non possono superare il 20% del totale.")
    assert client.post("/api/v2/allocation/funds/from-bando", json={"bando_id": "SENZA-CONTRIBUTO", "fiscal_year": 2027}, headers=hq()).status_code == 422
    make_bando()
    r = client.post("/api/v2/allocation/funds/from-bando", json={"bando_id": "BANDO-FONDO", "fiscal_year": 2027, "max_total_eur": 50000}, headers=hq())
    assert r.status_code == 200
    f = r.json()
    assert f["coverage_pct"] == 0.6 and f["category_max_share"] == {"CONSULTING": 0.2} and f["max_total_eur"] == 50000.0
    assert f["active_from_month"] == 1 and f["active_to_month"] == 12 and "BANDO-FONDO" in f["source_ref"]
    assert client.post("/api/v2/allocation/funds/from-bando", json={"bando_id": "BANDO-FONDO", "fiscal_year": 2027}).status_code == 401


def test_plan_is_computed_from_the_uploaded_balance_and_lines_needing_review_block_it():
    make_bando()
    client.post("/api/v2/allocation/funds/from-bando", json={"bando_id": "BANDO-FONDO", "fiscal_year": 2027, "max_total_eur": 50000}, headers=hq())
    doc = upload_balance()
    blocked = client.post("/api/v2/allocation/optimize", json={"fiscal_year": 2027, "historical_balance_ref": doc["id"]})
    assert blocked.status_code == 409 and blocked.json()["detail"]["lines"][0]["description"] == "Costi vari"
    resolve_all_lines(doc)
    r = client.post("/api/v2/allocation/optimize", json={"fiscal_year": 2027, "historical_balance_ref": doc["id"], "excluded_funds": []})
    assert r.status_code == 200
    plan = r.json()
    total = 150000 + 45000 + 40000 + 3200 + 20000 + 1500
    assert plan["total_gross_expense_eur"] == plan["total_cost_eur"] == total and plan["status"] == "OPTIMIZED"
    assert plan["covered_by_funds_eur"] == plan["covered_by_public_funds_eur"] <= 50000
    assert plan["allocation_plan"][0]["cost_category"] and plan["allocation_plan"][0]["covered_by"]
    assert {ln["item_id"][:4] for ln in plan["allocation_plan"]} == {"EXP-"}


def test_excluding_the_only_fund_leaves_everything_to_the_entity():
    make_bando()
    client.post("/api/v2/allocation/funds/from-bando", json={"bando_id": "BANDO-FONDO", "fiscal_year": 2027}, headers=hq())
    doc = upload_balance()
    resolve_all_lines(doc)
    r = client.post("/api/v2/allocation/optimize", json={"fiscal_year": 2027, "historical_balance_ref": doc["id"], "excluded_funds": ["BANDO-FONDO"]}).json()
    assert r["covered_by_funds_eur"] == 0 and r["net_cost_to_entity_eur"] == r["total_cost_eur"]


def test_balance_and_inline_expenses_are_mutually_exclusive_and_unknown_balance_is_404():
    inline = {"item_id": "E1", "category": "PERSONNEL", "amount_eur": 1000}
    assert client.post("/api/v2/allocation/optimize", json={"historical_balance_ref": 1, "historical_expenses": [inline]}).status_code == 422
    assert client.post("/api/v2/allocation/optimize", json={"historical_balance_ref": 9999}).status_code == 404
