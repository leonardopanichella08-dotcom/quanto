"""Endpoint OAuth 2.0 (client credentials) per l'integrazione con ERP/gestionali."""
import json
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.deps import require_auth, user_of
from app.core import auth, events, users

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
        token = auth.issue_token(str(data["client_id"]))
        events.record("auth.token", f"Token emesso a {data['client_id']}", actor=f"client:{data['client_id']}")
        return token
    except auth.AuthConfigError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OAuth non configurato sul server") from None


class LoginBody(BaseModel):
    email: str = Field(..., max_length=200)
    password: str = Field(..., min_length=1, max_length=200)


class PasswordBody(BaseModel):
    current_password: str = Field(..., max_length=200)
    new_password: str = Field(..., max_length=200)


@router.post("/login", summary="Accesso con e-mail e password: restituisce il token dell'utente (8 ore)")
def login(body: LoginBody, request: Request) -> dict:
    client = request.client.host if request.client else "unknown"
    try:
        user = users.authenticate(body.email, body.password, client)
        token = users.issue_token(user)
    except users.AuthFailed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail o password non corrette") from None
    except users.AccountLocked as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"Troppi tentativi: account bloccato, riprova tra {exc.retry_after // 60 + 1} minuti",
                            headers={"Retry-After": str(exc.retry_after)}) from exc
    except users.UserError as exc:                       # bootstrap con password debole
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except auth.AuthConfigError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Autenticazione non configurata sul server (QUANTO_JWT_SECRET)") from None
    return {**token, "user": {k: user[k] for k in ("id", "email", "name", "role")}}


@router.get("/me", dependencies=[Depends(require_auth)], summary="Chi sono")
def me(request: Request) -> dict:
    u = user_of(request)
    if u is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Accesso richiesto")
    return u


@router.post("/change-password", dependencies=[Depends(require_auth)], summary="Cambia la tua password (tutti i token già emessi decadono)")
def change_password(body: PasswordBody, request: Request) -> dict:
    u = user_of(request)
    if u is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Accesso richiesto")
    try:
        users.change_password(u["id"], body.current_password, body.new_password)
    except users.AuthFailed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password attuale non corretta") from None
    except users.UserError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return {"changed": True}
