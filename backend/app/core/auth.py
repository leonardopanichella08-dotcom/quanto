"""Autenticazione per l'integrazione con ERP/gestionali (Zucchetti, TeamSystem): OAuth 2.0 + firma HMAC.

Due modalità, entrambe abilitate quando ``QUANTO_AUTH_REQUIRED=1``:

1. OAuth 2.0 client-credentials: ``POST /api/v2/auth/token`` con client_id/client_secret (registrati in
   ``QUANTO_OAUTH_CLIENTS="id:segreto,id2:segreto2"``) restituisce un bearer token JWT HS256 firmato con
   ``QUANTO_JWT_SECRET`` (scadenza 1 ora).
2. Firma HMAC della richiesta: header ``X-Quanto-Timestamp`` (epoch secondi, tolleranza 5 minuti) e
   ``X-Quanto-Signature: sha256=<hex>`` = HMAC-SHA256(``QUANTO_HMAC_SECRET``, ``"<timestamp>." + corpo``).
   Il timestamp nella firma impedisce il replay oltre la finestra di tolleranza.

Senza ``QUANTO_AUTH_REQUIRED`` l'API è aperta (solo sviluppo locale). Nessuna implementazione crittografica
propria: solo ``hmac``/``hashlib`` della libreria standard.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Dict, Optional

TOKEN_TTL_S = 3600
HMAC_TOLERANCE_S = 300


class AuthConfigError(RuntimeError):
    pass


def auth_required() -> bool:
    """Sicura per impostazione predefinita: si spegne solo scrivendo esplicitamente QUANTO_AUTH_REQUIRED=0 (sviluppo locale)."""
    return os.getenv("QUANTO_AUTH_REQUIRED", "1").strip().lower() not in ("0", "false", "no", "off")


def ensure_configured() -> None:
    """Con l'autenticazione attiva serve almeno un segreto: altrimenti errore di configurazione, mai porta aperta."""
    if not (os.getenv("QUANTO_JWT_SECRET") or os.getenv("QUANTO_HMAC_SECRET")):
        raise AuthConfigError("Nessun segreto di autenticazione configurato")


def _secret(name: str) -> bytes:
    value = os.getenv(name, "")
    if not value:
        raise AuthConfigError(f"{name} non configurata")
    return value.encode("utf-8")


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def oauth_clients() -> Dict[str, str]:
    clients: Dict[str, str] = {}
    for pair in os.getenv("QUANTO_OAUTH_CLIENTS", "").split(","):
        if ":" in pair:
            cid, secret = pair.strip().split(":", 1)
            if cid and secret:
                clients[cid] = secret
    return clients


def authenticate_client(client_id: str, client_secret: str) -> bool:
    expected = oauth_clients().get(client_id)
    return expected is not None and hmac.compare_digest(expected, client_secret)


def issue_token(client_id: str, now: Optional[float] = None) -> Dict[str, object]:
    now = int(now if now is not None else time.time())
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps({"sub": client_id, "iat": now, "exp": now + TOKEN_TTL_S}, separators=(",", ":")).encode())
    sig = hmac.new(_secret("QUANTO_JWT_SECRET"), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    return {"access_token": f"{header}.{payload}.{_b64(sig)}", "token_type": "Bearer", "expires_in": TOKEN_TTL_S}


def verify_token(token: str, now: Optional[float] = None) -> Optional[str]:
    """Restituisce il client_id se il token è valido e non scaduto, altrimenti ``None``."""
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
        header = json.loads(_unb64(header_b64))
        if header.get("alg") != "HS256":  # rifiuta "none" e altri algoritmi
            return None
        expected = hmac.new(_secret("QUANTO_JWT_SECRET"), f"{header_b64}.{payload_b64}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _unb64(sig_b64)):
            return None
        claims = json.loads(_unb64(payload_b64))
        if claims["exp"] < (now if now is not None else time.time()):
            return None
        if claims.get("typ") == "user":          # un token di utente non è un client ERP: si valuta solo in users.user_from_token
            return None
        return str(claims["sub"])
    except (ValueError, KeyError, TypeError):
        return None


def sign_claims(claims: Dict[str, object]) -> str:
    """JWT HS256 con le rivendicazioni indicate (usato per i token degli utenti)."""
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps(claims, separators=(",", ":")).encode())
    sig = hmac.new(_secret("QUANTO_JWT_SECRET"), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    return f"{header}.{payload}.{_b64(sig)}"


def verify_claims(token: str, now: Optional[float] = None) -> Optional[Dict[str, object]]:
    """Rivendicazioni di un JWT valido e non scaduto, altrimenti ``None``."""
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
        if json.loads(_unb64(header_b64)).get("alg") != "HS256":
            return None
        expected = hmac.new(_secret("QUANTO_JWT_SECRET"), f"{header_b64}.{payload_b64}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _unb64(sig_b64)):
            return None
        claims = json.loads(_unb64(payload_b64))
        if claims["exp"] < (now if now is not None else time.time()):
            return None
        return claims
    except (ValueError, KeyError, TypeError):
        return None


def sign_request(timestamp: int, body: bytes, secret: Optional[bytes] = None) -> str:
    key = secret if secret is not None else _secret("QUANTO_HMAC_SECRET")
    return "sha256=" + hmac.new(key, f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()


def verify_signature(timestamp: str, signature: str, body: bytes, now: Optional[float] = None) -> bool:
    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        return False
    if abs((now if now is not None else time.time()) - ts) > HMAC_TOLERANCE_S:
        return False
    return hmac.compare_digest(sign_request(ts, body), signature or "")
