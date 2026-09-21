"""Utenti, password, blocco, ruoli e protezione degli endpoint (autenticazione attiva per impostazione predefinita)."""
import time

import pytest
from fastapi.testclient import TestClient

from app.core import auth, users
from main import app
from tests.conftest import manager_token

client = TestClient(app)
PW = "Una-Password-Robusta-42"


@pytest.fixture
def secured(monkeypatch):
    monkeypatch.setenv("QUANTO_AUTH_REQUIRED", "1")
    return monkeypatch


def make(email="mario@example.test", role="USER", pw=PW):
    return users.create_user(email, "Mario Rossi", pw, role, actor="test")


def login(email="mario@example.test", pw=PW):
    return client.post("/api/v2/auth/login", json={"email": email, "password": pw})


def bearer(res):
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_auth_is_required_unless_explicitly_switched_off(monkeypatch):
    monkeypatch.delenv("QUANTO_AUTH_REQUIRED", raising=False)
    assert auth.auth_required() is True                                           # sicura per impostazione predefinita
    for off in ("0", "false", "no"):
        monkeypatch.setenv("QUANTO_AUTH_REQUIRED", off)
        assert auth.auth_required() is False


def test_protected_endpoints_reject_anonymous_but_login_health_and_auditor_reads_stay_public(secured):
    for path in ("/api/v2/bandi", "/api/v2/budget/fields", "/api/v2/fonte-b/summary", "/api/v2/allocation/funds", "/api/v2/fonte-c/documents", "/api/v2/hq/overview"):
        assert client.get(path).status_code == 401, path
    assert client.get("/api/v2/health").status_code == 200
    assert client.get("/api/v2/registry/status").status_code == 200
    assert client.get("/api/v2/registry/public-key").status_code == 200
    assert client.post("/api/v2/auth/login", json={"email": "x@example.test", "password": "y"}).status_code == 401


def test_login_gives_a_token_that_opens_the_api_and_wrong_credentials_are_indistinguishable(secured):
    make()
    ok = login()
    assert ok.status_code == 200 and ok.json()["user"]["role"] == "USER" and ok.json()["expires_in"] == 8 * 3600
    assert client.get("/api/v2/bandi", headers=bearer(ok)).status_code == 200
    assert client.get("/api/v2/auth/me", headers=bearer(ok)).json()["email"] == "mario@example.test"
    wrong_pw = login(pw="sbagliata")
    unknown = login(email="nessuno@example.test")
    assert wrong_pw.status_code == unknown.status_code == 401 and wrong_pw.json() == unknown.json()          # nessun elenco degli account


def test_passwords_are_hashed_with_scrypt_and_never_stored_or_returned():
    make()
    from app.core.db import connect
    with connect() as conn:
        stored = conn.execute("SELECT password_hash FROM users").fetchone()["password_hash"]
    assert stored.startswith("scrypt$") and PW not in stored
    assert users.verify_password(PW, stored) and not users.verify_password(PW + "x", stored)
    assert "password" not in str(users.list_users())


@pytest.mark.parametrize("pw,fragment", [("corta1", "almeno 12"), ("aaaaaaaaaaaaaaaa", "semplice"), ("soloLettereLunghe", "numero o un simbolo"), ("mario-example-99", "e-mail")])
def test_password_policy(pw, fragment):
    with pytest.raises(users.UserError, match=fragment):
        users.create_user("mario@example.test", "M", pw, "USER")


def test_lockout_after_repeated_failures_even_with_the_right_password(secured):
    make()
    for _ in range(users.MAX_FAILURES - 1):
        assert login(pw="no").status_code == 401
    assert login(pw="no").status_code == 429                                       # quinto errore: blocco
    locked = login()                                                               # anche la password giusta è bloccata
    assert locked.status_code == 429 and int(locked.headers["retry-after"]) > 0
    users.update_user(users.list_users()[0]["id"], "test", unlock=True)
    assert login().status_code == 200


def test_roles_hq_needs_a_manager_and_managers_manage_users(secured):
    make("utente@example.test")
    assert client.get("/api/v2/hq/overview", headers=bearer(login("utente@example.test"))).status_code == 403
    assert client.get("/api/v2/hq/users", headers={"Authorization": f"Bearer {manager_token()}"}).status_code == 200
    h = {"Authorization": f"Bearer {manager_token()}"}
    created = client.post("/api/v2/hq/users", headers=h, json={"email": "nuovo@example.test", "name": "Nuovo", "password": "Altra-Password-Solida-7", "role": "USER"})
    assert created.status_code == 201 and "password" not in created.text
    assert client.post("/api/v2/hq/users", headers=h, json={"email": "nuovo@example.test", "name": "X", "password": "Altra-Password-Solida-7"}).status_code == 422       # doppione
    assert client.post("/api/v2/hq/users", headers=h, json={"email": "debole@example.test", "name": "X", "password": "corta"}).status_code == 422
    assert client.post("/api/v2/hq/users", headers=bearer(login("utente@example.test")), json={"email": "a@example.test", "name": "A", "password": PW}).status_code == 403


def test_disabling_or_changing_password_invalidates_existing_tokens(secured):
    u = make()
    tok = login()
    assert client.get("/api/v2/bandi", headers=bearer(tok)).status_code == 200
    changed = client.post("/api/v2/auth/change-password", headers=bearer(tok), json={"current_password": PW, "new_password": "Nuova-Password-Robusta-9"})
    assert changed.status_code == 200
    assert client.get("/api/v2/bandi", headers=bearer(tok)).status_code == 401                         # il vecchio token non vale più
    assert login().status_code == 401 and login(pw="Nuova-Password-Robusta-9").status_code == 200
    tok2 = login(pw="Nuova-Password-Robusta-9")
    users.update_user(u["id"], "test", active=False)
    assert client.get("/api/v2/bandi", headers=bearer(tok2)).status_code == 401 and login(pw="Nuova-Password-Robusta-9").status_code == 401
    bad = client.post("/api/v2/auth/change-password", headers=bearer(tok2), json={"current_password": "x", "new_password": "Y"})
    assert bad.status_code == 401


def test_at_least_one_manager_must_remain():
    m = make("solo@example.test", "MANAGER")
    with pytest.raises(users.UserError, match="almeno un manager"):
        users.update_user(m["id"], "test", active=False)
    with pytest.raises(users.UserError, match="almeno un manager"):
        users.update_user(m["id"], "test", role="USER")


def test_tokens_cannot_be_forged_altered_or_used_after_expiry(secured):
    u = make()
    good = users.issue_token({**users.get(u["id"]), "role": "USER"})["access_token"]
    assert users.user_from_token(good)
    head, payload, sig = good.split(".")
    assert not users.user_from_token(f"{head}.{payload}.{sig[:-3]}AAA") and not users.user_from_token("") and not users.user_from_token(None)
    assert not users.user_from_token(good, now=time.time() + users.TOKEN_TTL_S + 5)
    manager_claim = auth.sign_claims({"sub": str(u["id"]), "typ": "user", "role": "MANAGER", "tv": 1, "exp": int(time.time()) + 999})
    assert users.user_from_token(manager_claim)["role"] == "USER"                    # il ruolo non si legge dal token ma dal database
    erp = auth.issue_token("zucchetti")["access_token"]
    assert users.user_from_token(erp) is None                                        # un token ERP non è un utente


def test_bootstrap_admin_is_created_once_from_the_environment(monkeypatch):
    monkeypatch.setenv("QUANTO_BOOTSTRAP_ADMIN_EMAIL", "admin@example.test")
    monkeypatch.setenv("QUANTO_BOOTSTRAP_ADMIN_PASSWORD", "Amministratore-Robusto-31")
    assert users.count_users() == 0
    assert users.authenticate("admin@example.test", "Amministratore-Robusto-31")["role"] == "MANAGER"
    users.update_user(users.list_users()[0]["id"], "t", name="Cambiato")
    monkeypatch.setenv("QUANTO_BOOTSTRAP_ADMIN_EMAIL", "altro@example.test")
    users.bootstrap_admin()
    assert users.count_users() == 1                                                  # una sola volta, quando non c'è nessun utente


def test_the_old_shared_hq_code_no_longer_exists(secured):
    assert client.post("/api/v2/hq/login", json={"code": "QUANTO_1"}).status_code in (404, 405)
