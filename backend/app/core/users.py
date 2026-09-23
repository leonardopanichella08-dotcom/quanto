"""Utenti e autenticazione: password con scrypt, blocco dopo errori ripetuti, token firmati con scadenza e revoca.

- Le password non si conservano mai: solo un hash scrypt con sale casuale (``scrypt$N$r$p$sale$hash``).
- 5 errori di fila bloccano l'account per 15 minuti (il blocco sta nel database: vale su tutte le istanze del server).
  Un utente inesistente costa lo stesso tempo di uno esistente e dà lo stesso messaggio (niente elenco degli account).
- Il token (JWT HS256) contiene utente, ruolo e ``tv`` (versione): cambiare password o disattivare l'utente lo invalida subito.
- Ruoli: USER (usa l'app) e MANAGER (Quartier Generale, tabelle ufficiali, gestione utenti).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.core import auth, events
from app.core.db import connect

ROLES = ("USER", "MANAGER")
MAX_FAILURES = 5
LOCK_MINUTES = 15
TOKEN_TTL_S = 8 * 3600
SCRYPT_N, SCRYPT_R, SCRYPT_P = 2 ** 14, 8, 1
MIN_PASSWORD = 12
_EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s]{2,}$")
_COMMON = {"password1234", "123456789012", "qwertyuiop12", "quanto123456", "administrator", "passwordpassword"}


class AuthFailed(Exception):
    """Credenziali non valide (messaggio volutamente generico)."""


class AccountLocked(Exception):
    def __init__(self, retry_after: int):
        super().__init__("Account bloccato")
        self.retry_after = retry_after


class UserError(ValueError):
    pass


# ------------------------------------------------------------------------------------------------ password
def check_password_policy(password: str, email: str = "") -> None:
    if len(password) < MIN_PASSWORD:
        raise UserError(f"La password deve avere almeno {MIN_PASSWORD} caratteri")
    if password.lower() in _COMMON or len(set(password)) < 5:
        raise UserError("Password troppo semplice: scegline una meno prevedibile")
    local = email.split("@")[0].lower()
    if local and len(local) >= 4 and local in password.lower():
        raise UserError("La password non deve contenere il nome dell'indirizzo e-mail")
    if not (re.search(r"[A-Za-z]", password) and re.search(r"[^A-Za-z]", password)):
        raise UserError("Usa lettere e almeno un numero o un simbolo")


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    h = hashlib.scrypt(password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=32, maxmem=64 * 1024 * 1024)
    b = lambda x: base64.b64encode(x).decode()
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${b(salt)}${b(h)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, n, r, p, salt, h = stored.split("$")
        got = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt), n=int(n), r=int(r), p=int(p), dklen=32, maxmem=64 * 1024 * 1024)
        return hmac.compare_digest(got, base64.b64decode(h))
    except (ValueError, TypeError):
        return False


_DUMMY = None


def _dummy_hash() -> str:
    global _DUMMY
    if _DUMMY is None:
        _DUMMY = hash_password(secrets.token_urlsafe(16))
    return _DUMMY


# ------------------------------------------------------------------------------------------------ archivio utenti
def _public(r) -> Dict[str, Any]:
    return {"id": r["id"], "email": r["email"], "name": r["name"], "role": r["role"], "active": r["active"], "created_at": r["created_at"],
            "last_login_at": r["last_login_at"], "locked": bool(r["locked_until"] and r["locked_until"] > events.now_iso())}


def _norm_email(email: str) -> str:
    e = (email or "").strip().lower()
    if not _EMAIL.match(e):
        raise UserError("Indirizzo e-mail non valido")
    return e


def create_user(email: str, name: str, password: str, role: str = "USER", actor: str = "system") -> Dict[str, Any]:
    email = _norm_email(email)
    if role not in ROLES:
        raise UserError("Ruolo sconosciuto")
    if not (name or "").strip():
        raise UserError("Indica il nome")
    check_password_policy(password, email)
    with connect() as conn:
        if conn.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
            raise UserError("Esiste già un utente con questo indirizzo")
        row = conn.execute("INSERT INTO users (email, name, password_hash, role, active, token_version, failed_logins, created_at) VALUES (?,?,?,?,TRUE,1,0,?) RETURNING *",
                           (email, name.strip()[:120], hash_password(password), role, events.now_iso())).fetchone()
    events.record("users.create", f"Utente {email} creato ({role})", actor=actor)
    return _public(row)


def list_users() -> List[Dict[str, Any]]:
    with connect() as conn:
        return [_public(r) for r in conn.execute("SELECT * FROM users ORDER BY email").fetchall()]


def get(user_id: int) -> Optional[Dict[str, Any]]:
    with connect() as conn:
        r = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return dict(r) if r else None


def count_users(role: Optional[str] = None) -> int:
    with connect() as conn:
        if role:
            return conn.execute("SELECT COUNT(*) n FROM users WHERE role=? AND active", (role,)).fetchone()["n"]
        return conn.execute("SELECT COUNT(*) n FROM users").fetchone()["n"]


def _managers_left(conn, excluding: int) -> int:
    return conn.execute("SELECT COUNT(*) n FROM users WHERE role='MANAGER' AND active AND id<>?", (excluding,)).fetchone()["n"]


def update_user(user_id: int, actor: str, role: Optional[str] = None, active: Optional[bool] = None, name: Optional[str] = None,
                new_password: Optional[str] = None, unlock: bool = False) -> Dict[str, Any]:
    with connect() as conn:
        r = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if r is None:
            raise KeyError(user_id)
        if (role and role != "MANAGER" or active is False) and r["role"] == "MANAGER" and r["active"] and _managers_left(conn, user_id) == 0:
            raise UserError("Deve restare almeno un manager attivo")
        sets, params = [], []
        if role is not None:
            if role not in ROLES:
                raise UserError("Ruolo sconosciuto")
            sets.append("role=?"); params.append(role)
        if active is not None:
            sets.append("active=?"); params.append(active)
        if name is not None:
            sets.append("name=?"); params.append(name.strip()[:120])
        if new_password is not None:
            check_password_policy(new_password, r["email"])
            sets += ["password_hash=?", "failed_logins=0", "locked_until=NULL"]; params.append(hash_password(new_password))
        if unlock:
            sets += ["failed_logins=0", "locked_until=NULL"]
        if role is not None or active is not None or new_password is not None:
            sets.append("token_version=token_version+1")             # i token già emessi non valgono più
        if sets:
            conn.execute(f"UPDATE users SET {', '.join(sets)} WHERE id=?", (*params, user_id))
        out = _public(conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone())
    events.record("users.update", f"Utente {out['email']} aggiornato", actor=actor, details={"role": role, "active": active, "password_reset": new_password is not None})
    return out


def change_password(user_id: int, current: str, new: str) -> None:
    with connect() as conn:
        r = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if r is None or not verify_password(current, r["password_hash"]):
            raise AuthFailed()
        check_password_policy(new, r["email"])
        conn.execute("UPDATE users SET password_hash=?, token_version=token_version+1 WHERE id=?", (hash_password(new), user_id))
    events.record("users.password", f"Password cambiata da {r['email']}", actor=f"user:{r['email']}")


# ------------------------------------------------------------------------------------------------ accesso
def bootstrap_admin() -> Optional[Dict[str, Any]]:
    """Primo manager, solo se non esiste nessun utente, da QUANTO_BOOTSTRAP_ADMIN_EMAIL / _PASSWORD (poi vanno tolte)."""
    email, pw = os.getenv("QUANTO_BOOTSTRAP_ADMIN_EMAIL", "").strip(), os.getenv("QUANTO_BOOTSTRAP_ADMIN_PASSWORD", "")
    if not email or not pw:
        return None
    with connect() as conn:
        if conn.execute("SELECT 1 FROM users LIMIT 1").fetchone():
            return None
    return create_user(email, "Amministratore", pw, "MANAGER", actor="bootstrap")


def authenticate(email: str, password: str, client: str = "unknown") -> Dict[str, Any]:
    bootstrap_admin()
    email = (email or "").strip().lower()
    now = events.now_iso()
    with connect() as conn:
        r = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if r is None:
            verify_password(password, _dummy_hash())                   # stesso tempo di un utente vero
            events.record("auth.login", "Accesso negato: utente sconosciuto", status="DENIED", actor=f"ip:{client}")
            raise AuthFailed()
        if r["locked_until"] and r["locked_until"] > now:
            left = int((datetime.fromisoformat(r["locked_until"]) - datetime.fromisoformat(now)).total_seconds())
            raise AccountLocked(max(1, left))
        ok = verify_password(password, r["password_hash"]) and r["active"]
        if not ok:
            failed = r["failed_logins"] + 1
            locked = (datetime.now(timezone.utc) + timedelta(minutes=LOCK_MINUTES)).isoformat(timespec="seconds") if failed >= MAX_FAILURES else None
            conn.execute("UPDATE users SET failed_logins=?, locked_until=? WHERE id=?", (0 if locked else failed, locked, r["id"]))
    if not ok:
        events.record("auth.login", f"Accesso negato per {email}", status="DENIED", actor=f"ip:{client}")
        if failed >= MAX_FAILURES:
            raise AccountLocked(LOCK_MINUTES * 60)
        raise AuthFailed()
    with connect() as conn:
        conn.execute("UPDATE users SET failed_logins=0, locked_until=NULL, last_login_at=? WHERE id=?", (now, r["id"]))
    events.record("auth.login", f"Accesso di {email}", actor=f"user:{email}")
    return _public(r) | {"token_version": r["token_version"]}


# ------------------------------------------------------------------------------------------------ token
def issue_token(user: Dict[str, Any], now: Optional[float] = None) -> Dict[str, Any]:
    exp = int((now if now is not None else time.time()) + TOKEN_TTL_S)
    tok = auth.sign_claims({"sub": str(user["id"]), "typ": "user", "role": user["role"], "tv": user["token_version"], "exp": exp})
    return {"access_token": tok, "token_type": "Bearer", "expires_in": TOKEN_TTL_S}


def user_from_token(token: Optional[str], now: Optional[float] = None) -> Optional[Dict[str, Any]]:
    """L'utente del token se valido, non scaduto, attivo e con la versione giusta; altrimenti None."""
    claims = auth.verify_claims(token or "", now)
    if not claims or claims.get("typ") != "user":
        return None
    row = get(int(claims["sub"]))
    if row is None or not row["active"] or row["token_version"] != claims.get("tv"):
        return None
    return {"id": row["id"], "email": row["email"], "name": row["name"], "role": row["role"]}
