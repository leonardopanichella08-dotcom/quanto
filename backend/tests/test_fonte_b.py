"""Fonte B: tabelle ufficiali versionate nel database. Nessun valore nel codice, nessun ripiego «standard»."""
import base64
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core import fonte_b, fonte_b_admin as admin
from app.core.deterministic_engine import DeterministicEngine as E
from app.models.schemas import CostItemInput, GrantRuleSet
from main import app
from tests.conftest import personnel

client = TestClient(app)


def rules(**kw):
    return GrantRuleSet(bando_id="B", bando_name="B", max_hourly_rate_personnel=35.0, rule_version_hash="hash-di-prova-1", **kw)


def publish(kind, code, csv_text, version, valid_from, valid_to=None):
    d = admin.create_draft(kind, code, f"{kind} {code}", version, valid_from, valid_to, "Documento ufficiale di prova", "https://fonte.example/doc", None,
                           "t.csv", csv_text.encode(), "test")
    return admin.publish(d["id"], "test", attest_official=True)


@pytest.mark.no_fonte_b
def test_without_tables_a_personnel_line_is_rejected_and_no_contract_is_assumed():
    r = E.validate_personnel_item(personnel(), rules())
    assert r.status.value == "REJECTED" and "Fonte B" in r.rejection_reason and r.computed_cost_eur == 0
    no_ccnl = E.validate_personnel_item(CostItemInput(item_id="X", description="x", category="PERSONNEL", source_c_ref="D", employee_level="3",
                                                       ral_eur=30000, fte_allocation=1, duration_months=12), rules())
    assert no_ccnl.status.value == "REJECTED" and "non indicato" in no_ccnl.rejection_reason


def test_versions_are_chosen_by_reference_date_and_change_the_fingerprint():
    old = "level;standard_hours;social_charges_pct;tfr_pct\n9;1650;30%;7,5%\n"
    new = "level;standard_hours;social_charges_pct;tfr_pct\n9;1600;32%;7,5%\n"
    publish("CCNL", "PROVA", old, "2020", date(2020, 1, 1))
    publish("CCNL", "PROVA", new, "2026", date(2026, 1, 1))
    items = [personnel(ccnl="PROVA", level="9")]
    a, _, _ = E.analyze_budget(items, rules(), reference_date=date(2025, 6, 1))
    b, _, _ = E.analyze_budget(items, rules(), reference_date=date(2026, 6, 1))
    assert a[0].breakdown.working_hours == 1650 and b[0].breakdown.working_hours == 1600
    assert a[0].item_hash_sha256 != b[0].item_hash_sha256
    again, _, _ = E.analyze_budget(items, rules(), reference_date=date(2025, 6, 1))
    assert again[0].item_hash_sha256 == a[0].item_hash_sha256                       # stessa data, stessa impronta
    rows = [d for d in admin.list_datasets() if d["code"] == "PROVA"]
    assert {(d["version"], d["valid_to"], d["status"]) for d in rows} == {("2020", "2025-12-31", "SUPERSEDED"), ("2026", None, "PUBLISHED")}


def test_a_draft_is_not_used_until_published_and_needs_an_attestation_and_a_source():
    text = "level;standard_hours;social_charges_pct;tfr_pct\n1;1700;30%;7%\n"
    d = admin.create_draft("CCNL", "BOZZA", "Bozza", "1", date(2020, 1, 1), None, "Doc", "https://x.example", None, "t.csv", text.encode(), "test")
    assert fonte_b.load().ccnl("BOZZA", "1") is None
    with pytest.raises(PermissionError, match="attestare"):
        admin.publish(d["id"], "test", attest_official=False)
    no_src = admin.create_draft("CCNL", "SENZAFONTE", "x", "1", date(2020, 1, 1), None, "Doc", None, None, "t.csv", text.encode(), "test")
    with pytest.raises(PermissionError, match="indirizzo o il riferimento"):
        admin.publish(no_src["id"], "test", attest_official=True)
    admin.publish(d["id"], "test", attest_official=True)
    assert fonte_b.load().ccnl("BOZZA", "1").standard_hours == 1700


def test_overlapping_periods_are_refused():
    text = "level;standard_hours;social_charges_pct;tfr_pct\n1;1700;30%;7%\n"
    publish("CCNL", "OVER", text, "a", date(2020, 1, 1), date(2022, 12, 31))
    d = admin.create_draft("CCNL", "OVER", "x", "b", date(2022, 6, 1), None, "Doc", "https://x.example", None, "t.csv", text.encode(), "test")
    with pytest.raises(PermissionError, match="si sovrappone"):
        admin.publish(d["id"], "test", attest_official=True)


@pytest.mark.parametrize("csv_text,fragment", [
    ("level;standard_hours;social_charges_pct;tfr_pct\n1;1656;30;7%\n", "ambiguo"),
    ("level;standard_hours;social_charges_pct;tfr_pct\n1;abc;30%;7%\n", "non è un numero"),
    ("level;standard_hours;social_charges_pct;tfr_pct\n1;1656;30%;7%\n1;1656;30%;7%\n", "duplicata"),
    ("level;standard_hours;social_charges_pct\n1;1656;30%\n", "Colonne mancanti"),
    ("level;standard_hours;social_charges_pct;tfr_pct\n1;0;30%;7%\n", "maggiore di zero"),
    ("level;standard_hours;social_charges_pct;tfr_pct\n1;1656;130%;7%\n", "fuori intervallo"),
])
def test_import_errors_are_reported_and_nothing_is_saved(csv_text, fragment):
    with pytest.raises(admin.FonteBFileError) as exc:
        admin.create_draft("CCNL", "ERR", "x", "1", date(2020, 1, 1), None, "Doc", "https://x", None, "t.csv", csv_text.encode(), "test")
    assert fragment in str(exc.value) or any(fragment in e["error"] for e in exc.value.errors)
    assert not [d for d in admin.list_datasets() if d["code"] == "ERR"]


def test_unknown_parameter_key_is_refused_and_percentages_accept_comma_and_percent_sign():
    with pytest.raises(admin.FonteBFileError):
        admin.parse_rows("PARAMS", "p.csv", b"param_key;value\ninventato;1\n")
    rows = admin.parse_rows("CCNL", "c.csv", b"level;standard_hours;social_charges_pct;tfr_pct\n1;1656;0,30;8,33%\n")
    assert str(rows[0]["social_charges_pct"]) == "0.30" and str(rows[0]["tfr_pct"]) == "0.0833"


def test_missing_parameter_blocks_the_line_instead_of_using_a_default():
    from app.core.db import connect
    with connect() as conn:
        conn.execute("DELETE FROM fonte_b_params")
    r = E.validate_personnel_item(personnel(contract_type="FIXED_TERM"), rules())
    assert r.status.value == "REJECTED" and "Fonte B" in r.rejection_reason


def test_amortization_table_caps_the_declared_rate_and_unknown_category_suspends():
    def asset(**kw):
        return CostItemInput(item_id="A", description="cnc", category="CAPITAL_ASSETS", source_c_ref="D", amount_eur=100000, duration_months=12, **kw)
    r = rules(equipment_depreciation_only=True)
    capped = E.validate_personnel_item(asset(depreciation_category="MACCHINARI", depreciation_rate_pct=0.5), r)
    assert any("DECLARED_RATE_ABOVE_TABLE" in x for x in capped.applied_rules) and capped.computed_cost_eur == 20000.0
    assert E.validate_personnel_item(asset(depreciation_category="MACCHINARI"), r).computed_cost_eur == 20000.0
    assert E.validate_personnel_item(asset(depreciation_category="INESISTENTE"), r).status.value == "MISSING_DOCUMENTS"


def test_benchmark_from_fonte_b_overrides_the_declared_one():
    it = CostItemInput(item_id="A", description="cnc", category="CAPITAL_ASSETS", source_c_ref="D", amount_eur=300000, benchmark_category="CNC",
                       market_benchmark_eur=999999)
    assert E.validate_personnel_item(it, rules(max_price_deviation_pct=0.1)).computed_cost_eur == 242000.0          # 220.000 di tabella + 10%
    cons = CostItemInput(item_id="C", description="audit", category="CONSULTING", source_c_ref="D", amount_eur=9000, daily_rate_eur=600, days=15,
                         benchmark_category="ENERGY_AUDIT")
    assert E.validate_personnel_item(cons, rules()).computed_cost_eur == 6750.0                                      # 450 €/gg × 15


# ------------------------------------------------------------------ API
def hq_headers():
    tok = client.post("/api/v2/hq/login", json={"code": "QUANTO_1"}).json()["token"]
    return {"X-HQ-Token": tok}


def upload_body(**kw):
    csv_text = "level;standard_hours;social_charges_pct;tfr_pct\n2;1650;30%;8%\n"
    body = {"kind": "CCNL", "code": "API_TEST", "name": "Contratto di prova", "version": "1", "valid_from": "2026-01-01", "source_name": "Circolare di prova n. 1",
            "source_ref": "Circolare 1/2026", "filename": "c.csv", "content_base64": base64.b64encode(csv_text.encode()).decode()}
    return {**body, **kw}


def test_api_flow_upload_publish_and_editor_options_follow_the_data():
    h = hq_headers()
    assert client.post("/api/v2/fonte-b/datasets", json=upload_body()).status_code == 401
    d = client.post("/api/v2/fonte-b/datasets", json=upload_body(), headers=h)
    assert d.status_code == 201 and d.json()["status"] == "DRAFT" and d.json()["rows"] == 1
    did = d.json()["id"]
    assert "API_TEST" not in client.get("/api/v2/budget/fields").json()["ccnl_levels"]
    assert client.post(f"/api/v2/fonte-b/datasets/{did}/publish", json={"attest_official": False}, headers=h).status_code == 409
    ok = client.post(f"/api/v2/fonte-b/datasets/{did}/publish", json={"attest_official": True}, headers=h)
    assert ok.status_code == 200 and ok.json()["status"] == "PUBLISHED" and ok.json()["official"] is True
    fields = client.get("/api/v2/budget/fields").json()
    assert fields["ccnl_levels"]["API_TEST"] == ["2"]
    assert "API_TEST" in next(f for f in fields["fields"] if f["name"] == "ccnl_code")["options"]
    assert client.delete(f"/api/v2/fonte-b/datasets/{did}", headers=h).status_code == 409
    assert client.get(f"/api/v2/fonte-b/datasets/{did}/file", headers=h).content.startswith(b"level;")
    assert client.get("/api/v2/fonte-b/template/CCNL.csv", headers=h).text.strip() == "level;standard_hours;social_charges_pct;tfr_pct"


def test_api_reports_row_errors_with_line_numbers():
    body = upload_body(content_base64=base64.b64encode(b"level;standard_hours;social_charges_pct;tfr_pct\n1;1656;30;7%\n2;x;30%;7%\n").decode())
    res = client.post("/api/v2/fonte-b/datasets", json=body, headers=hq_headers())
    assert res.status_code == 422 and [e["line"] for e in res.json()["detail"]["errors"]] == [2, 3]
