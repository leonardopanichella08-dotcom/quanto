"""Endpoint OAuth 2.0 (client credentials) per l'integrazione con ERP/gestionali."""
import json
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request, status

from app.core import auth

router = APIRouter()


@router.post("/token", summary="OAuth 2.0 client-credentials: restituisce un bearer token (1 ora)")
async def token(request: Request) -> dict:
    raw = (await request.body()).decode("utf-8", errors="replace")
    try:
        if "json" in request.headers.get("content-type", ""):
            data = json.loads(raw or "{}")
        else:  # application/x-www-form-urlencoded, come da RFC 6749
            data = {k: v[0] for k, v in parse_qs(raw).items()}
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Corpo della richiesta non valido") from None
    if data.get("grant_type") != "client_credentials":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "unsupported_grant_type"})
    try:
        if not auth.authenticate_client(str(data.get("client_id", "")), str(data.get("client_secret", ""))):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "invalid_client"})
        return auth.issue_token(str(data["client_id"]))
    except auth.AuthConfigError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OAuth non configurato sul server") from None
