import base64
import binascii

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.deps import actor_of, require_hq
from app.core import events, pattern_bank, webhooks
from app.core.ingestion import Ingestion
from app.models.schemas import PatternMatchRequest, PatternMatchResponse

router = APIRouter()


class ImportBody(BaseModel):
    filename: str = Field(..., max_length=200)
    content_base64: str


def _caps(bando_id):
    """Tetti del bando per il commento sullo scostamento (dalle regole pubblicate, mai inventati)."""
    if not bando_id:
        return None
    rule_set, _ = Ingestion.build_rule_set(bando_id) if Ingestion.get_bando(bando_id) else (None, [])
    if rule_set is None:
        return None
    caps = {}
    if rule_set.max_consulting_percentage is not None:
        caps["consulting_pct"] = rule_set.max_consulting_percentage
    if rule_set.max_overhead_percentage is not None:
        caps["overhead_pct"] = rule_set.max_overhead_percentage
    return caps


@router.post("/match", response_model=PatternMatchResponse, summary="Confronta un budget bozza con gli archetipi vincenti (banca dati + k-means)")
def match_budget_pattern(request: PatternMatchRequest, background: BackgroundTasks, http: Request) -> PatternMatchResponse:
    timer = events.Timer()
    try:
        result = pattern_bank.match(request.bando_category, request.draft_budget, cap_notes=_caps(request.bando_id))
    except pattern_bank.PatternError as exc:
        code = status.HTTP_409_CONFLICT if "banca dati" in str(exc) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=str(exc)) from exc
    events.record("pattern.match", f"Archetipo più vicino: {result['closest_archetype']} (coseno {result['similarity_score']:.2f}, {result['data_points']} budget storici)",
                  actor=actor_of(http), duration_ms=timer.ms, details={"draft": request.draft_budget, "archetype": result["closest_archetype"],
                                                                         "similarity": result["similarity_score"], "main_deviation": result["main_deviation"]})
    background.add_task(webhooks.emit, "event.pattern.matched", {
        "bando_category": request.bando_category, "closest_archetype": result["closest_archetype"], "similarity_score": result["similarity_score"]})
    return PatternMatchResponse(**result)


@router.get("/categories", summary="Categorie di bandi presenti nella banca dati dei pattern, con il numero di budget e di archetipi")
def categories() -> list:
    return pattern_bank.categories()


@router.get("/budgets", dependencies=[Depends(require_hq)], summary="Budget storici in banca dati")
def budgets(category: str = "", limit: int = 200) -> list:
    return pattern_bank.list_budgets(category.upper() or None, max(1, min(limit, 500)))


@router.post("/import", dependencies=[Depends(require_hq)], status_code=status.HTTP_201_CREATED,
             summary="Importa budget storici da un file CSV (con la fonte di ogni riga) e ricalcola gli archetipi")
def import_budgets(body: ImportBody, request: Request) -> dict:
    try:
        data = base64.b64decode(body.content_base64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File non valido (base64)") from None
    try:
        return pattern_bank.import_budgets(pattern_bank.parse_budgets(body.filename, data), actor_of(request))
    except pattern_bank.PatternError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"message": str(exc), "errors": exc.errors}) from exc
