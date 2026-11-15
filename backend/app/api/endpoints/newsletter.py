"""Newsletter: iscrizione pubblica dalla homepage (serve il consenso esplicito)."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core import newsletter

router = APIRouter()


class SubscribeBody(BaseModel):
    email: str = Field(..., max_length=254)
    consent: bool = False
    source: str = Field(default="homepage", max_length=40)


@router.get("/consent", summary="Il testo del consenso che si accetta iscrivendosi")
def consent_text() -> dict:
    return {"version": newsletter.CONSENT_VERSION, "text": newsletter.CONSENT_TEXT}


@router.post("/subscribe", summary="Iscrive un indirizzo alla newsletter di QUANTO (solo con consenso)")
def subscribe(body: SubscribeBody) -> dict:
    try:
        return newsletter.subscribe(body.email, body.consent, body.source)
    except newsletter.NewsletterError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
