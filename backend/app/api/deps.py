"""Dipendenze condivise dell'API: servizi e autenticazione."""
from __future__ import annotations

import logging

from typing import Optional

from fastapi import Header, HTTPException, Request, status

from app.core import auth, hq
from app.core.auditor_engine import AuditorVerificationEngine

logger = logging.getLogger("quanto.api")

auditor_engine = AuditorVerificationEngine()


async def require_auth(request: Request) -> None:
    """Bearer OAuth2 oppure firma HMAC della richiesta. Aperta se QUANTO_AUTH_REQUIRED non è attivo (sviluppo)."""
    if not auth.auth_required():
        return
    try:
        auth.ensure_configured()
        header = request.headers.get("authorization", "")
        if header.lower().startswith("bearer "):
            if auth.verify_token(header[7:].strip()):
                return
        elif request.headers.get("x-quanto-signature"):
            body = await request.body()
            if auth.verify_signature(request.headers.get("x-quanto-timestamp", ""), request.headers["x-quanto-signature"], body):
                return
    except auth.AuthConfigError:
        logger.error("Autenticazione richiesta ma segreti non configurati")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Autenticazione non configurata sul server") from None
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenziali mancanti o non valide",
                        headers={"WWW-Authenticate": "Bearer"})


def actor_of(request: Request) -> str:
    """Chi ha eseguito l'operazione, per la timeline: il client OAuth se c'è un bearer valido, altrimenti anonimo."""
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        try:
            sub = auth.verify_token(header[7:].strip())
            if sub:
                return f"client:{sub}"
        except auth.AuthConfigError:
            pass
    return "anonymous"


def require_hq(x_hq_token: Optional[str] = Header(default=None)) -> None:
    """Accesso al Quartier Generale: token emesso da POST /hq/login dopo la verifica del codice manager."""
    if not hq.verify_token(x_hq_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Accesso al Quartier Generale richiesto")
