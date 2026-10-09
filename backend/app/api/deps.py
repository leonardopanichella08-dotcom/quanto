"""Dipendenze condivise dell'API: servizi e autenticazione."""
from __future__ import annotations

import logging

from typing import Optional

from fastapi import HTTPException, Request, status

from app.core import auth, clients, users
from app.core.auditor_engine import AuditorVerificationEngine

logger = logging.getLogger("quanto.api")

auditor_engine = AuditorVerificationEngine()


def _bearer(request: Request) -> Optional[str]:
    header = request.headers.get("authorization", "")
    return header[7:].strip() if header.lower().startswith("bearer ") else None


def user_of(request: Request) -> Optional[dict]:
    """L'utente autenticato dal bearer (o dall'intestazione X-HQ-Token, che porta lo stesso token), altrimenti None."""
    token = _bearer(request) or request.headers.get("x-hq-token")
    if not token:
        return None
    try:
        return users.user_from_token(token)
    except auth.AuthConfigError:
        return None


async def require_auth(request: Request) -> None:
    """Utente con token, client ERP (OAuth 2.0) oppure firma HMAC. Si spegne solo con QUANTO_AUTH_REQUIRED=0."""
    if not auth.auth_required():
        return
    try:
        auth.ensure_configured()
        if user_of(request):
            return
        token = _bearer(request)
        if token:
            if auth.verify_token(token):
                return
        elif request.headers.get("x-quanto-signature"):
            body = await request.body()
            if auth.verify_signature(request.headers.get("x-quanto-timestamp", ""), request.headers["x-quanto-signature"], body):
                return
    except auth.AuthConfigError:
        logger.error("Autenticazione richiesta ma segreti non configurati")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Autenticazione non configurata sul server") from None
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Accesso richiesto: effettua il login",
                        headers={"WWW-Authenticate": "Bearer"})


def actor_of(request: Request) -> str:
    """Chi ha eseguito l'operazione, per la timeline: l'utente, il client OAuth oppure anonimo."""
    u = user_of(request)
    if u:
        return f"user:{u['email']}"
    token = _bearer(request)
    if token:
        try:
            sub = auth.verify_token(token)
            if sub:
                return f"client:{sub}"
        except auth.AuthConfigError:
            pass
    return "anonymous"


def require_hq(request: Request) -> None:
    """Quartier Generale, tabelle ufficiali, utenti: riservato al titolare (QUANTO_OWNER_EMAIL) quando configurato,
    altrimenti a chi ha ruolo MANAGER (sviluppo locale, senza quella variabile)."""
    u = user_of(request)
    if u is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Accesso richiesto: effettua il login")
    if users.owner_email():
        if not users.is_owner(u["email"]):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Il Quartier Generale è riservato al titolare dell'account")
        return
    if u["role"] != "MANAGER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Serve il ruolo di manager")


def client_of(request: Request) -> Optional[int]:
    """Il lavoro (azienda cliente) attivo, dall'intestazione X-Client-Id; deve appartenere allo studio che fa la richiesta."""
    raw = request.headers.get("x-client-id")
    if not raw:
        return None
    if not raw.isdigit():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lavoro non valido")
    cid = int(raw)
    if not clients.owns(actor_of(request), cid):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lavoro non trovato")
    return cid


def scope_of(request: Request) -> str:
    """La chiave dei dati d'impresa: studio + lavoro attivo. Senza lavoro (uso diretto dell'API) resta la sola chiave dello studio."""
    base = actor_of(request)
    cid = client_of(request)
    return clients.scope(base, cid) if cid else base
