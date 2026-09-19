import json
import time

import pytest
from fastapi.testclient import TestClient

from app.core import auth
from app.core.ingestion import Ingestion, extract_deterministic, normalize_value
from main import app

client = TestClient(app)

VALIDATE_BODY = {
    "project_id": "PRJ-AUTH", "grant_rules": {"bando_id": "B", "bando_name": "B", "rule_version_hash": "a8f3b129c9e840134012480a2"},
    "cost_items": [{"item_id": "L1", "description": "PM", "category": "PERSONNEL", "source_c_ref": "DOC-1", "ral_eur": 38000, "fte_allocation": 0.5}],
}


@pytest.fixture
def secured(monkeypatch):
    monkeypatch.setenv("QUANTO_AUTH_REQUIRED", "1")
    monkeypatch.setenv("QUANTO_OAUTH_CLIENTS", "zucchetti:s3cret,teamsystem:altro")
    monkeypatch.setenv("QUANTO_JWT_SECRET", "jwt-secret")
    monkeypatch.setenv("QUANTO_HMAC_SECRET", "hmac-secret")


# ------------------------------------------------------------------ autenticazione
def test_auth_disabled_by_default_for_local_dev():
    assert client.post("/api/v2/budget/validate", json=VALIDATE_BODY).status_code == 200


def test_protected_endpoints_reject_anonymous_but_auditor_reads_stay_public(secured):
    assert client.post("/api/v2/budget/validate", json=VALIDATE_BODY).status_code == 401
    assert client.post("/api/v2/registry/register", json={"project_id": "P", "merkle_root": "0x" + "12" * 32}).status_code == 401
    assert client.get("/api/v2/registry/verify/P", params={"merkle_root": "0x" + "12" * 32}).status_code == 200
    assert client.get("/api/v2/registry/status").status_code == 200
    assert client.get("/api/v2/health").status_code == 200


def test_oauth_client_credentials_flow(secured):
    t = client.post("/api/v2/auth/token", data={"grant_type": "client_credentials", "client_id": "zucchetti", "client_secret": "s3cret"})
    assert t.status_code == 200 and t.json()["token_type"] == "Bearer"
    headers = {"Authorization": f"Bearer {t.json()['access_token']}"}
    assert client.post("/api/v2/budget/validate", json=VALIDATE_BODY, headers=headers).status_code == 200
    assert client.post("/api/v2/registry/register", json={"project_id": "PRJ-OAUTH", "merkle_root": "0x" + "12" * 32}, headers=headers).status_code == 201


def test_oauth_rejects_bad_credentials_and_grants(secured):
    assert client.post("/api/v2/auth/token", data={"grant_type": "client_credentials", "client_id": "zucchetti", "client_secret": "wrong"}).status_code == 401
    assert client.post("/api/v2/auth/token", data={"grant_type": "password", "client_id": "zucchetti", "client_secret": "s3cret"}).status_code == 400
    assert client.post("/api/v2/auth/token", json={"grant_type": "client_credentials", "client_id": "teamsystem", "client_secret": "altro"}).status_code == 200


def test_bearer_tampering_expiry_and_alg_none_are_rejected(secured):
    token = auth.issue_token("zucchetti")["access_token"]
    head, payload, sig = token.split(".")
    assert auth.verify_token(token) == "zucchetti"
    assert auth.verify_token(f"{head}.{payload}x.{sig}") is None
    assert auth.verify_token(token, now=time.time() + auth.TOKEN_TTL_S + 5) is None
    none_head = auth._b64(json.dumps({"alg": "none", "typ": "JWT"}).encode())
    assert auth.verify_token(f"{none_head}.{payload}.") is None
    assert client.post("/api/v2/budget/validate", json=VALIDATE_BODY, headers={"Authorization": "Bearer " + token + "x"}).status_code == 401


def test_hmac_signed_requests(secured):
    raw = json.dumps(VALIDATE_BODY).encode()
    ts = int(time.time())
    good = {"X-Quanto-Timestamp": str(ts), "X-Quanto-Signature": auth.sign_request(ts, raw), "Content-Type": "application/json"}
    assert client.post("/api/v2/budget/validate", content=raw, headers=good).status_code == 200
    tampered = json.dumps({**VALIDATE_BODY, "project_id": "ALTRO"}).encode()
    assert client.post("/api/v2/budget/validate", content=tampered, headers=good).status_code == 401
    old = ts - auth.HMAC_TOLERANCE_S - 10
    stale = {"X-Quanto-Timestamp": str(old), "X-Quanto-Signature": auth.sign_request(old, raw), "Content-Type": "application/json"}
    assert client.post("/api/v2/budget/validate", content=raw, headers=stale).status_code == 401
    assert client.post("/api/v2/budget/validate", content=raw, headers={**good, "X-Quanto-Signature": "sha256=" + "0" * 64}).status_code == 401


def test_auth_required_without_secrets_is_a_503_not_an_open_door(monkeypatch):
    monkeypatch.setenv("QUANTO_AUTH_REQUIRED", "1")
    r = client.post("/api/v2/budget/validate", json=VALIDATE_BODY, headers={"Authorization": "Bearer abc.def.ghi"})
    assert r.status_code == 503


# ------------------------------------------------------------------ ingestion: parsing deterministico
TEXT = """
Art. 5 - Spese ammissibili
Il costo orario del personale non può essere superiore a 35,00 euro/ora.
Le consulenze esterne non possono superare il 20% del totale del progetto, massimo 20%.
Le spese generali forfettarie sono ammesse fino al 7% dei costi diretti, massimo 7%.
Il contributo è pari al 60% delle spese ammissibili.
Sono ammissibili le spese sostenute dal 01/01/2026 fino al 31/12/2027.
Il CUP deve essere riportato su tutti i documenti di spesa.
"""


def test_deterministic_extraction_from_prose_and_tables():
    found = extract_deterministic(TEXT)
    assert found["max_hourly_rate_personnel"] == "35"
    assert found["max_consulting_percentage"] == "0.2" and found["max_overhead_percentage"] == "0.07"
    assert found["contribution_rate_pct"] == "0.6"
    assert found["eligibility_start"] == "2026-01-01" and found["eligibility_end"] == "2027-12-31"
    assert found["requires_cup"] == "true"


def test_table_format_and_rejection_of_unparseable_values():
    found = extract_deterministic("max_hourly_rate_personnel: 42,5\nmax_consulting_percentage | abc\nunknown_rule: 5\nrequires_dnsh = true")
    assert found == {"max_hourly_rate_personnel": "42.5", "requires_dnsh": "true"}   # 'abc' e chiavi ignote scartati, mai indovinati


def test_normalize_value_typing():
    assert normalize_value("max_consulting_percentage", "0,20") == "0.2"
    assert normalize_value("max_consulting_percentage", "20%") == "0.2" and normalize_value("max_overhead_percentage", "7,5 %") == "0.075"
    assert normalize_value("overtime_allowed", "sì") == "true"
    assert normalize_value("blocked_payment_methods", '["CASH"]') == '["CASH"]'
    with pytest.raises(ValueError):
        normalize_value("max_consulting_percentage", "tanto")
    with pytest.raises(ValueError):
        normalize_value("bando_id", "x")


# ------------------------------------------------------------------ ingestion: flusso via API
def _catalog(bando="TR5"):
    assert client.post("/api/v2/ingestion/catalog", json={"bando_id": bando, "name": "Transizione 5.0", "issuer": "MIMIT"}).status_code == 201


def test_full_pipeline_cache_and_grant_rules():
    _catalog()
    assert client.get("/api/v2/ingestion/grant-rules/TR5").status_code == 409                  # nessuna regola ancora
    assert client.post("/api/v2/ingestion/confirm/TR5").json()["cache_hit"] is False
    first = client.post("/api/v2/ingestion/extract", json={"bando_id": "TR5", "source_text": TEXT}).json()
    assert first["cache_hit"] is False and first["coverage_activated"] is True and not first["pending_human_review"]

    assert client.post("/api/v2/ingestion/confirm/TR5").json()["cache_hit"] is True            # secondo cliente: cache
    st = client.get("/api/v2/ingestion/status/TR5").json()
    assert st["extraction_status"] == "COMPLETED" and st["cache_hit"] is True and st["requested_by_clients_count"] == 2
    assert st["rules_from_structured_parsing"] == st["rules_extracted_total"] == 7

    rules = client.get("/api/v2/ingestion/grant-rules/TR5").json()
    assert rules["max_hourly_rate_personnel"] == 35.0 and rules["requires_cup"] is True and rules["eligibility_start"] == "2026-01-01"
    # le regole estratte alimentano direttamente la validazione
    body = {**VALIDATE_BODY, "grant_rules": rules}
    assert client.post("/api/v2/budget/validate", json=body).status_code == 200


def test_rule_version_hash_changes_when_a_rule_changes():
    _catalog()
    client.post("/api/v2/ingestion/extract", json={"bando_id": "TR5", "source_text": TEXT})
    h1 = client.get("/api/v2/ingestion/grant-rules/TR5").json()["rule_version_hash"]
    Ingestion.resolve_review("TR5", "max_hourly_rate_personnel", "40")
    h2 = client.get("/api/v2/ingestion/grant-rules/TR5").json()["rule_version_hash"]
    assert h1 != h2 and len(h1) == 32


def test_published_rules_are_not_overwritten_by_later_extractions():
    _catalog()
    client.post("/api/v2/ingestion/extract", json={"bando_id": "TR5", "source_text": "max_hourly_rate_personnel: 35"})
    again = client.post("/api/v2/ingestion/extract", json={"bando_id": "TR5", "source_text": "max_hourly_rate_personnel: 99"}).json()
    assert again["published"] == {} and again["cache_hit"] is True
    Ingestion.build_rule_set("TR5")
    assert Ingestion.status("TR5")["rules_extracted_total"] == 1


def test_multi_pass_agreement_publishes_and_disagreement_goes_to_human_review():
    _catalog()
    passes = [{"max_hourly_rate_personnel": "35", "max_consulting_percentage": "20%", "max_overhead_percentage": 0.07},
              {"max_hourly_rate_personnel": 35.0, "max_consulting_percentage": 0.25, "max_overhead_percentage": "0,07"}]
    out = client.post("/api/v2/ingestion/extract", json={"bando_id": "TR5", "ai_passes": passes}).json()
    assert out["published"] == {"max_hourly_rate_personnel": "35", "max_overhead_percentage": "0.07"}
    assert out["pending_human_review"] == ["max_consulting_percentage"] and out["coverage_activated"] is False

    queue = client.get("/api/v2/ingestion/review-queue").json()
    assert [q["rule_key"] for q in queue] == ["max_consulting_percentage"] and queue[0]["passes"] == ["0.2", "0.25"]
    st = client.get("/api/v2/ingestion/status/TR5").json()
    assert st["extraction_status"] == "PARTIAL" and st["rules_pending_human_review"] == 1 and st["rules_with_pass_agreement"] == 2

    done = client.post("/api/v2/ingestion/review", json={"bando_id": "TR5", "rule_key": "max_consulting_percentage", "value": "0,20"}).json()
    assert done["value"] == "0.2" and done["origin"] == "HUMAN_REVIEW"
    assert client.get("/api/v2/ingestion/review-queue").json() == []
    assert client.get("/api/v2/ingestion/status/TR5").json()["extraction_status"] == "COMPLETED"
    assert client.get("/api/v2/ingestion/grant-rules/TR5").json()["max_consulting_percentage"] == 0.2


def test_single_pass_is_never_enough_for_publication():
    _catalog()
    out = client.post("/api/v2/ingestion/extract", json={"bando_id": "TR5", "ai_passes": [{"max_hourly_rate_personnel": "35"}]}).json()
    assert out["published"] == {} and out["pending_human_review"] == ["max_hourly_rate_personnel"]


def test_ingestion_errors():
    assert client.get("/api/v2/ingestion/status/NOPE").status_code == 404
    assert client.post("/api/v2/ingestion/confirm/NOPE").status_code == 404
    assert client.post("/api/v2/ingestion/extract", json={"bando_id": "NOPE", "source_text": "x"}).status_code == 404
    _catalog()
    assert client.post("/api/v2/ingestion/extract", json={"bando_id": "TR5"}).status_code == 400
    assert client.post("/api/v2/ingestion/review", json={"bando_id": "TR5", "rule_key": "max_hourly_rate_personnel", "value": "35"}).status_code == 404
    client.post("/api/v2/ingestion/extract", json={"bando_id": "TR5", "source_text": "max_hourly_rate_personnel: 35"})
    assert client.post("/api/v2/ingestion/review", json={"bando_id": "TR5", "rule_key": "max_hourly_rate_personnel", "value": "molto"}).status_code == 422
