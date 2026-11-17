"""Marketing (Quartier Generale): LinkedIn, post con approvazione, campagne, statistiche; più le due porte pubbliche necessarie:
il ritorno da LinkedIn dopo il collegamento e la registrazione delle visite al sito."""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.api.deps import actor_of, require_hq
from app.core import access, marketing

router = APIRouter()
deps = [Depends(require_hq)]


def _guard(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except marketing.MarketingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Elemento non trovato") from None
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Valore non valido") from exc


class PostIn(BaseModel):
    text: str = Field(..., max_length=3000)
    link: Optional[str] = Field(default=None, max_length=500)
    account_id: Optional[int] = None
    campaign_id: Optional[int] = None
    scheduled_at: Optional[str] = Field(default=None, max_length=40)


class CampaignIn(BaseModel):
    name: str = Field(..., max_length=160)
    objective: str = Field(default="", max_length=160)
    account_id: Optional[int] = None
    budget_eur: Optional[str] = Field(default=None, max_length=30)
    start_day: Optional[str] = Field(default=None, max_length=10)
    end_day: Optional[str] = Field(default=None, max_length=10)
    status: str = Field(default="BOZZA", max_length=20)
    notes: str = Field(default="", max_length=2000)


class Numbers(BaseModel):
    day: Optional[str] = Field(default=None, max_length=10)
    impressions: Optional[str] = Field(default=None, max_length=20)
    reach: Optional[str] = Field(default=None, max_length=20)
    reactions: Optional[str] = Field(default=None, max_length=20)
    comments: Optional[str] = Field(default=None, max_length=20)
    reshares: Optional[str] = Field(default=None, max_length=20)
    clicks: Optional[str] = Field(default=None, max_length=20)
    spend_eur: Optional[str] = Field(default=None, max_length=20)
    leads: Optional[str] = Field(default=None, max_length=20)
    conversions: Optional[str] = Field(default=None, max_length=20)
    followers: Optional[str] = Field(default=None, max_length=20)


class CsvIn(BaseModel):
    content: str = Field(..., max_length=2_000_000)


class TrackIn(BaseModel):
    kind: str = Field(default="view", max_length=20)
    session: str = Field(..., max_length=60)
    path: str = Field(default="", max_length=300)
    label: str = Field(default="", max_length=200)
    referrer: str = Field(default="", max_length=500)
    utm_source: str = Field(default="", max_length=120)
    utm_medium: str = Field(default="", max_length=120)
    utm_campaign: str = Field(default="", max_length=200)
    device: str = Field(default="", max_length=20)


# ------------------------------------------------------------------------------------------------ porte pubbliche
@router.post("/track", summary="Pubblica: registra una visita o un clic sul sito (sessione casuale, nessun dato personale)")
def track(body: TrackIn) -> Dict[str, bool]:
    return {"ok": marketing.track(body.model_dump())}


@router.get("/linkedin/callback", summary="Ritorno da LinkedIn dopo il collegamento (verificato con il codice firmato della richiesta)")
def linkedin_callback(code: str = "", state: str = "", error: str = "") -> RedirectResponse:
    base = access.public_url()
    if error or not code:
        return RedirectResponse(f"{base}/?tab=hq&hq=marketing&linkedin=annullato", status_code=303)
    try:
        marketing.complete_authorization(code, state)
    except (marketing.MarketingError, KeyError):
        return RedirectResponse(f"{base}/?tab=hq&hq=marketing&linkedin=errore", status_code=303)
    return RedirectResponse(f"{base}/?tab=hq&hq=marketing&linkedin=collegato", status_code=303)


# ------------------------------------------------------------------------------------------------ Quartier Generale
@router.get("/overview", dependencies=deps, summary="Panoramica: visite, fonti, post, campagne, follower; pubblica anche i post programmati già scaduti")
def overview(days: int = Query(default=30, ge=7, le=365)) -> dict:
    due = marketing.publish_due(actor="quartier-generale")
    return marketing.overview(days) | {"just_published": due}


@router.get("/accounts", dependencies=deps)
def accounts() -> list:
    return marketing.accounts()


@router.post("/accounts/{account_id}/connect", dependencies=deps, summary="Indirizzo di LinkedIn per collegare l'account")
def connect_account(account_id: int, request: Request) -> dict:
    return {"url": _guard(marketing.authorize_url, account_id, actor_of(request))}


@router.post("/accounts/{account_id}/followers", dependencies=deps)
def followers(account_id: int, body: Numbers, request: Request) -> dict:
    _guard(marketing.add_followers, account_id, body.day or "", body.followers, actor_of(request))
    return {"ok": True}


@router.get("/posts", dependencies=deps)
def posts() -> list:
    return marketing.list_posts()


@router.post("/posts", dependencies=deps, status_code=status.HTTP_201_CREATED)
def create_post(body: PostIn, request: Request) -> dict:
    return _guard(marketing.save_post, body.model_dump(), actor_of(request))


@router.put("/posts/{post_id}", dependencies=deps)
def update_post(post_id: int, body: PostIn, request: Request) -> dict:
    return _guard(marketing.save_post, body.model_dump(), actor_of(request), post_id)


@router.post("/posts/{post_id}/{action}", dependencies=deps, summary="submit · approve · back · mark_published · publish")
def post_action(post_id: int, action: str, request: Request) -> dict:
    if action == "publish":
        return _guard(marketing.publish_now, post_id, actor_of(request))
    if action not in ("submit", "approve", "back", "mark_published"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Azione sconosciuta")
    return _guard(marketing.set_status, post_id, action, actor_of(request))


@router.post("/posts/{post_id}/metrics/add", dependencies=deps)
def post_metrics(post_id: int, body: Numbers, request: Request) -> dict:
    return _guard(marketing.add_post_metrics, post_id, body.model_dump(), actor_of(request))


@router.delete("/posts/{post_id}", dependencies=deps)
def delete_post(post_id: int, request: Request) -> dict:
    _guard(marketing.delete_post, post_id, actor_of(request))
    return {"deleted": True}


@router.get("/campaigns", dependencies=deps)
def campaigns() -> list:
    return marketing.list_campaigns()


@router.post("/campaigns", dependencies=deps, status_code=status.HTTP_201_CREATED)
def create_campaign(body: CampaignIn, request: Request) -> dict:
    return _guard(marketing.save_campaign, body.model_dump(), actor_of(request))


@router.put("/campaigns/{campaign_id}", dependencies=deps)
def update_campaign(campaign_id: int, body: CampaignIn, request: Request) -> dict:
    return _guard(marketing.save_campaign, body.model_dump(), actor_of(request), campaign_id)


@router.post("/campaigns/{campaign_id}/day", dependencies=deps, summary="Dati di un giorno della campagna (inseriti a mano)")
def campaign_day(campaign_id: int, body: Numbers, request: Request) -> dict:
    _guard(marketing.add_campaign_day, campaign_id, body.model_dump(), actor_of(request))
    return {"ok": True}


@router.post("/campaigns/{campaign_id}/import", dependencies=deps, summary="Importa un CSV giornaliero esportato da Campaign Manager")
def campaign_import(campaign_id: int, body: CsvIn, request: Request) -> dict:
    return _guard(marketing.import_campaign_csv, campaign_id, body.content, actor_of(request))
