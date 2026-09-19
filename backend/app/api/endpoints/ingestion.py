"""Pannello di ingestion della Fonte A (uso interno del team): catalogo, estrazione, coda di verifica."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.deps import actor_of
from app.core import events, webhooks
from app.core.ingestion import Ingestion
from app.models.schemas import GrantRuleSet

router = APIRouter()


class CatalogEntry(BaseModel):
    bando_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=200)
    issuer: Optional[str] = Field(default=None, max_length=120)
    deadline: Optional[str] = Field(default=None, max_length=32)
    source_url: Optional[str] = Field(default=None, max_length=300)


class ExtractionRequest(BaseModel):
    bando_id: str
    source_text: Optional[str] = Field(default=None, max_length=200_000, description="Testo del bando: parsing deterministico (Stadio 2)")
    ai_passes: Optional[List[Dict[str, Any]]] = Field(default=None, max_length=10, description="Passaggi indipendenti (Stadio 3): il confronto è fatto dal codice")
    source_ref: Optional[str] = Field(default=None, max_length=200)


class ReviewDecision(BaseModel):
    bando_id: str
    rule_key: str
    value: Any


def _not_found(bando_id: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bando {bando_id} non presente nel catalogo")


@router.post("/catalog", status_code=status.HTTP_201_CREATED, summary="Stadio 1: censisce un bando nel catalogo (solo metadati)")
def add_to_catalog(entry: CatalogEntry, http: Request) -> dict:
    Ingestion.catalog(entry.bando_id, entry.name, entry.issuer, entry.deadline, entry.source_url)
    events.record("ingestion.catalog", f"Censito {entry.name}", bando_id=entry.bando_id, actor=actor_of(http))
    return {"bando_id": entry.bando_id, "catalog_status": "CATALOGED"}


@router.get("/catalog", summary="Catalogo dei bandi")
def list_catalog() -> List[dict]:
    return Ingestion.list_catalog()


@router.post("/confirm/{bando_id}", summary="Il cliente conferma il bando: trigger dell'estrazione (o cache hit)")
def confirm_bando(bando_id: str, http: Request) -> dict:
    if Ingestion.get_bando(bando_id) is None:
        raise _not_found(bando_id)
    hit = Ingestion.confirm(bando_id)
    events.record("ingestion.confirm", "Bando confermato: " + ("regole già in cache" if hit else "estrazione necessaria"), bando_id=bando_id, actor=actor_of(http), details={"cache_hit": hit})
    return {"bando_id": bando_id, "cache_hit": hit}


@router.post("/extract", summary="Stadi 2 e 3: estrazione deterministica + riconciliazione dei passaggi multipli")
def extract_rules(request: ExtractionRequest, background: BackgroundTasks, http: Request) -> dict:
    timer = events.Timer()
    if not request.source_text and not request.ai_passes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fornire source_text e/o ai_passes")
    try:
        outcome = Ingestion.extract(request.bando_id, request.source_text, request.ai_passes, request.source_ref)
    except KeyError:
        raise _not_found(request.bando_id) from None
    events.record("ingestion.extract", f"Estrazione: {len(outcome.published)} regole pubblicate, {len(outcome.pending_review)} in revisione" + (" (cache)" if outcome.cache_hit else ""),
                  bando_id=request.bando_id, actor=actor_of(http), duration_ms=timer.ms,
                  details={"published": outcome.published, "pending": outcome.pending_review, "cache_hit": outcome.cache_hit, "coverage_activated": outcome.coverage_activated})
    for key in outcome.pending_review:
        background.add_task(webhooks.emit, "event.rule.disagreement_detected", {"bando_id": request.bando_id, "rule_key": key})
    if outcome.coverage_activated:
        background.add_task(webhooks.emit, "event.bando.coverage_activated", {"bando_id": request.bando_id})
    return {"bando_id": request.bando_id, "cache_hit": outcome.cache_hit, "published": outcome.published,
            "pending_human_review": outcome.pending_review, "coverage_activated": outcome.coverage_activated}


@router.get("/status/{bando_id}", summary="Stato dell'ingestion normativa per un bando (Pannello Interno)")
def get_ingestion_pipeline_status(bando_id: str) -> Dict[str, Any]:
    result = Ingestion.status(bando_id)
    if result is None:
        raise _not_found(bando_id)
    return result


@router.get("/review-queue", summary="Coda di verifica umana: solo i casi di reale disaccordo tra i passaggi")
def review_queue() -> List[dict]:
    return Ingestion.review_queue()


@router.post("/review", summary="Il consulente risolve un disaccordo: la regola viene pubblicata")
def resolve_review(decision: ReviewDecision, http: Request) -> dict:
    try:
        value = Ingestion.resolve_review(decision.bando_id, decision.rule_key, decision.value)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regola non presente per questo bando") from None
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    events.record("ingestion.review", f"Regola {decision.rule_key} risolta a mano: {value}", bando_id=decision.bando_id, actor=actor_of(http),
                  details={"rule_key": decision.rule_key, "value": value})
    return {"bando_id": decision.bando_id, "rule_key": decision.rule_key, "value": value, "status": "PUBLISHED", "origin": "HUMAN_REVIEW"}


@router.get("/grant-rules/{bando_id}", summary="GrantRuleSet composto dalle sole regole pubblicate (pronto per /budget/validate)")
def grant_rules(bando_id: str) -> dict:
    try:
        rule_set, missing = Ingestion.build_rule_set(bando_id)
    except KeyError:
        raise _not_found(bando_id) from None
    if rule_set is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"message": "Regole di base non ancora pubblicate", "missing": missing})
    return GrantRuleSet.model_dump(rule_set, mode="json")
