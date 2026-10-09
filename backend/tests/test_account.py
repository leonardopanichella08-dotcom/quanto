"""Profilo dello studio: dati, sicurezza (password, uscita da tutti i dispositivi), esportazione ed eliminazione dell'account."""
import pytest
from fastapi.testclient import TestClient

from app.core import users
from main import app
from tests.test_users_auth import PW, bearer, login, make, secured  # noqa: F401

client = TestClient(app)


def session(email="studio@example.test"):
    make(email=email)
    return bearer(login(email=email))


def test_studio_data_can_be_completed_and_is_validated(secured):
    h = session()
    r = client.patch("/api/v2/auth/me", json={"studio_name": "Studio Rossi & Associati", "studio_vat": "IT01234567890", "phone": "+39 011 123456", "job_title": "Dottore commercialista"}, headers=h)
    assert r.status_code == 200 and r.json()["studio_vat"] == "01234567890" and r.json()["studio_name"].startswith("Studio Rossi")
    prof = client.get("/api/v2/auth/me/profile", headers=h).json()
    assert prof["profile"]["phone"] == "+39 011 123456" and prof["logins"] and "12 caratteri" in prof["password_policy"]
    assert client.patch("/api/v2/auth/me", json={"studio_vat": "123"}, headers=h).status_code == 422
    assert client.patch("/api/v2/auth/me", json={"phone": "abc"}, headers=h).status_code == 422
    assert client.patch("/api/v2/auth/me", json={"name": "  "}, headers=h).status_code == 422
    assert client.patch("/api/v2/auth/me", json={"studio_name": "x"}).status_code == 401


def test_sign_out_everywhere_invalidates_the_tokens_already_issued(secured):
    h = session()
    assert client.get("/api/v2/auth/me", headers=h).status_code == 200
    assert client.post("/api/v2/auth/me/sign-out-everywhere", headers=h).status_code == 200
    assert client.get("/api/v2/auth/me", headers=h).status_code == 401
    assert login(email="studio@example.test").status_code == 200                  # con la password si rientra


def test_password_change_needs_the_current_one_and_ends_the_old_sessions(secured):
    h = session()
    assert client.post("/api/v2/auth/change-password", json={"current_password": "sbagliata", "new_password": "Nuova-Password-Robusta-77"}, headers=h).status_code == 401
    assert client.post("/api/v2/auth/change-password", json={"current_password": PW, "new_password": "corta"}, headers=h).status_code == 422
    assert client.post("/api/v2/auth/change-password", json={"current_password": PW, "new_password": "Nuova-Password-Robusta-77"}, headers=h).status_code == 200
    assert client.get("/api/v2/auth/me", headers=h).status_code == 401


def test_export_contains_the_studio_data_jobs_and_templates(secured):
    from app.core.ingestion import Ingestion
    h = session()
    Ingestion.catalog("BANDO-EXP", "Bando", "Ente", None, None)
    job = client.post("/api/v2/clients", json={"name": "Cliente Esporta"}, headers=h).json()["id"]
    client.put("/api/v2/profile", json={"fields": {"legal_name": "ESPORTA SRL"}}, headers={**h, "X-Client-Id": str(job)})
    sh = {"personnel_pct": 0.3, "assets_pct": 0.4, "consulting_pct": 0.1, "research_pct": 0.1, "overhead_pct": 0.05, "training_pct": 0.03, "communication_pct": 0.02, "other_pct": 0.0}
    assert client.post("/api/v2/templates", json={"ateco_code": "62.01", "bando_id": "BANDO-EXP", "shares": sh}, headers={**h, "X-Client-Id": str(job)}).status_code == 201
    data = client.get("/api/v2/auth/me/export", headers=h).json()
    assert data["account"]["email"] == "studio@example.test" and "password_hash" not in str(data)
    assert data["jobs"][0]["name"] == "Cliente Esporta" and data["jobs"][0]["profile"]["legal_name"] == "ESPORTA SRL"
    assert len(data["budget_templates"]) == 1 and data["recent_operations"]


def test_account_deletion_needs_password_and_email_and_removes_everything(secured):
    from app.core.db import connect
    h = session()
    job = client.post("/api/v2/clients", json={"name": "Da Cancellare"}, headers=h).json()["id"]
    client.put("/api/v2/profile", json={"fields": {"legal_name": "X"}}, headers={**h, "X-Client-Id": str(job)})
    assert client.request("DELETE", "/api/v2/auth/me", json={"password": "sbagliata", "confirm_email": "studio@example.test"}, headers=h).status_code == 401
    assert client.request("DELETE", "/api/v2/auth/me", json={"password": PW, "confirm_email": "altro@example.test"}, headers=h).status_code == 422
    r = client.request("DELETE", "/api/v2/auth/me", json={"password": PW, "confirm_email": "studio@example.test"}, headers=h)
    assert r.status_code == 200 and r.json()["deleted"]["jobs"] == 1
    with connect() as conn:
        assert conn.execute("SELECT COUNT(*) n FROM users WHERE email=?", ("studio@example.test",)).fetchone()["n"] == 0
        assert conn.execute("SELECT COUNT(*) n FROM company_profiles").fetchone()["n"] == 0
    assert client.get("/api/v2/auth/me", headers=h).status_code == 401


def test_the_last_manager_cannot_delete_the_account(secured):
    make(email="capo@example.test", role="MANAGER")
    with pytest.raises(users.UserError):
        users.delete_account(users.authenticate("capo@example.test", PW)["id"], PW, "capo@example.test")
