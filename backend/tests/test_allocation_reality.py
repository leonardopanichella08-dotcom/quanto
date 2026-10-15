"""Allocazione e realtà: valore atteso, costo dell'istruttoria, tempi di incasso, cumulo. Niente numeri inventati: ciò che manca si dice."""
from fastapi.testclient import TestClient

from app.core import allocation_reality as R
from app.core.allocation_engine import AllocationOptimizerEngine as A
from app.models.allocation import AllocationOptimizationRequest as Req
from main import app

client = TestClient(app)


def allocation():
    r = A.optimize_annual_allocation(Req.model_validate({
        "historical_expenses": [{"item_id": "E1", "category": "PERSONNEL", "amount_eur": 120000, "month": 1}, {"item_id": "E2", "category": "CAPITAL_ASSETS", "amount_eur": 60000, "month": 4}],
        "available_funding_lines": [{"fund_id": "A", "allowed_categories": ["PERSONNEL"], "coverage_pct": 0.5}, {"fund_id": "B", "allowed_categories": ["CAPITAL_ASSETS"], "coverage_pct": 0.5}]}))
    return r.model_dump(mode="json")


def test_without_assumptions_nothing_is_invented():
    out = R.assess("u", allocation(), {}, 2027, funding_lines=[{"fund_id": "A", "name": "A"}, {"fund_id": "B", "name": "B"}])
    assert out["totals"]["nominal_eur"] == 90000.0 and out["totals"]["expected_eur"] is None and out["totals"]["complete"] is False
    assert all("probabilità" in " ".join(f["missing"]) for f in out["funds"])
    assert out["cash"]["funds_not_in_timeline"] == ["A", "B"] and "non è noto" in out["cash"]["message"]


def test_expected_value_fee_admin_and_break_even():
    a = {"A": {"probability_pct": 50, "admin_cost_eur": 3000, "fee_pct": 10, "reimbursement_lag_months": 3, "advance_pct": 0},
         "B": {"probability_pct": 20, "admin_cost_eur": 8000, "fee_pct": 0, "reimbursement_lag_months": 6}}
    out = R.assess("u", allocation(), a, 2027, funding_lines=[{"fund_id": "A", "name": "A"}, {"fund_id": "B", "name": "B"}])
    fa, fb = out["funds"]
    assert fa["covered_eur"] == 60000.0 and fa["expected_eur"] == 30000.0 and fa["fee_eur"] == 3000.0 and fa["net_expected_eur"] == 24000.0 and fa["worth_it"]
    assert fb["expected_eur"] == 6000.0 and fb["net_expected_eur"] == -2000.0 and fb["worth_it"] is False and fb["break_even_probability_pct"] == 26.7
    assert out["totals"]["complete"] and out["totals"]["net_expected_eur"] == 22000.0


def test_cash_timeline_waits_for_the_reimbursement():
    a = {"A": {"probability_pct": 100, "admin_cost_eur": 0, "fee_pct": 0, "reimbursement_lag_months": 3, "advance_pct": 0},
         "B": {"probability_pct": 100, "admin_cost_eur": 0, "fee_pct": 0, "reimbursement_lag_months": 6, "advance_pct": 50}}
    out = R.assess("u", allocation(), a, 2027, funding_lines=[{"fund_id": "A"}, {"fund_id": "B"}])
    cash = out["cash"]
    assert cash["peak_need_without_funds_eur"] == 180000.0 and 0 < cash["peak_need_eur"] < 180000.0
    assert round(sum(r["received_eur"] for r in cash["rows"]), 2) == 90000.0                      # alla fine entra tutto il contributo
    first = cash["rows"][0]
    assert first["received_eur"] == 0 and first["spent_eur"] == 120000.0                           # spesa pagata dall'azienda, nulla ancora incassato
    assert cash["rows"][3]["received_eur"] > 0                                                    # a 3 mesi dalla prima spesa arriva il rimborso di A, e per B l'anticipo del 50% di aprile
    assert len(cash["rows"]) == 18


def test_bad_assumptions_are_rejected_and_the_endpoint_works():
    body = {"allocation": allocation(), "fiscal_year": 2027, "assumptions": {"A": {"probability_pct": 150}}}
    assert client.post("/api/v2/allocation/reality", json=body).status_code == 422
    body["assumptions"] = {"A": {"probability_pct": 60, "admin_cost_eur": 1000, "fee_pct": 5, "reimbursement_lag_months": 40}}
    assert client.post("/api/v2/allocation/reality", json=body).status_code == 422
    body["assumptions"] = {"A": {"probability_pct": 60, "admin_cost_eur": 1000, "fee_pct": 5, "reimbursement_lag_months": 4}}
    ok = client.post("/api/v2/allocation/reality", json=body)
    assert ok.status_code == 200 and ok.json()["funds"][0]["expected_eur"] == 36000.0
    assert client.post("/api/v2/allocation/reality", json={"allocation": {}, "fiscal_year": 2027}).status_code == 422


def test_other_aids_are_listed_as_cumulation_notes(monkeypatch):
    doc = {"filename": "f.xlsx"}
    monkeypatch.setattr(R.company_facts, "facts", lambda owner: {"rd_credit": [{"year": 2026, "credit_eur": 50000.0, "_doc": doc}, {"year": 2019, "credit_eur": 9.0, "_doc": doc}]})
    monkeypatch.setattr(R.company_facts, "aids", lambda owner: [{"granted": "2026-03-01", "regime": "Credito d'imposta", "measure": "Transizione 4.0", "amount_eur": 20000.0, "_doc": doc},
                                                                 {"granted": "2026-05-01", "regime": "de minimis", "measure": "x", "amount_eur": 5.0, "_doc": doc},
                                                                 {"granted": "2020-05-01", "regime": "GBER", "measure": "vecchio", "amount_eur": 5.0, "_doc": doc}])
    notes = R.cumulation("u", 2027)
    assert [n["amount_eur"] for n in notes] == [50000.0, 20000.0]                  # l'anno 2019 e il de minimis (ha il suo registro) non compaiono
    assert "altri aiuti" in notes[0]["text"]
