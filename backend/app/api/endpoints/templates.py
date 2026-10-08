"""Template di budget: le nicchie, i bandi che scelgono e come ripartiscono il budget. Il consiglio si ricalcola a ogni template salvato."""
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import actor_of
from app.core import template_learning as tl

router = APIRouter()


class TemplateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ateco_code: str = Field(..., max_length=12, description="Codice ATECO dell'azienda: la nicchia")
    bando_id: str = Field(..., max_length=80, description="Il bando scelto")
    shares: Dict[str, float] = Field(..., description="Ripartizione del budget del progetto (quote da 0 a 1 o in %, somma 100%)")
    outcome: str = Field(default="BOZZA", description="BOZZA, PRESENTATO, AMMESSO, NON_AMMESSO")
    score: Optional[float] = Field(default=None, ge=0, le=1000)
    total_eur: Optional[float] = Field(default=None, gt=0)
    company_size: Optional[str] = Field(default=None, max_length=20)
    region: Optional[str] = Field(default=None, max_length=40)
    note: str = Field(default="", max_length=500)
    shared: bool = Field(default=False, description="Condividi il template in forma anonima per allenare l'algoritmo di tutti")


class TemplatePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: Optional[str] = None
    score: Optional[float] = Field(default=None, ge=0, le=1000)
    total_eur: Optional[float] = Field(default=None, gt=0)
    note: Optional[str] = Field(default=None, max_length=500)
    shared: Optional[bool] = None
    shares: Optional[Dict[str, float]] = None


class RecommendBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ateco_code: Optional[str] = Field(default=None, max_length=12)
    bando_id: Optional[str] = Field(default=None, max_length=80)
    draft: Optional[Dict[str, float]] = Field(default=None, description="Il tuo budget bozza da confrontare con il consiglio")


def _guard(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except tl.TemplateError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/meta", summary="Voci del budget, esiti e livelli usati dai template")
def meta() -> dict:
    return {"shares": [{"key": k, "label": tl.SHARE_LABEL[k]} for k in tl.SHARES], "outcomes": [{"key": k, "label": tl.OUTCOME_LABEL[k], "weight": tl.OUTCOME_WEIGHT[k]} for k in tl.OUTCOMES],
            "min_templates": tl.MIN_TEMPLATES, "tiers": [{"key": k, "label": v} for k, v in tl.TIERS]}


@router.get("", summary="I miei template di budget")
def mine(request: Request) -> list:
    return tl.list_templates(actor_of(request))


@router.post("", status_code=status.HTTP_201_CREATED, summary="Salva un template: nicchia, bando scelto, ripartizione del budget ed esito")
def create(body: TemplateBody, request: Request) -> dict:
    owner = actor_of(request)
    return _guard(tl.save_template, owner, body.model_dump(), owner)


@router.patch("/{template_id}", summary="Aggiorna l'esito, il punteggio o le quote di un mio template: l'algoritmo si riallena da solo")
def patch(template_id: int, body: TemplatePatch, request: Request) -> dict:
    owner = actor_of(request)
    try:
        return _guard(tl.update_template, owner, template_id, {k: v for k, v in body.model_dump().items() if v is not None}, owner)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template non trovato") from None


@router.delete("/{template_id}", summary="Elimina un mio template")
def remove(template_id: int, request: Request) -> dict:
    owner = actor_of(request)
    if not tl.delete_template(owner, template_id, owner):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template non trovato")
    return {"deleted": template_id}


@router.post("/recommend", summary="Il budget consigliato per una nicchia e un bando (e il confronto con un budget bozza)")
def recommend(body: RecommendBody, request: Request) -> dict:
    return _guard(tl.recommend, actor_of(request), body.ateco_code, body.bando_id, body.draft)


@router.get("/niches", summary="Mappa: quali nicchie partecipano a quali bandi, con quale ripartizione e quanti ammessi")
def niches(request: Request) -> list:
    return tl.niche_map(actor_of(request))


@router.get("/learning", summary="Come sta imparando l'algoritmo: template, esiti e se seguire il consiglio conviene")
def learning(request: Request) -> dict:
    return tl.learning_status(actor_of(request))
