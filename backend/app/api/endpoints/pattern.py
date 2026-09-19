from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status

from app.api.deps import actor_of
from app.core import events, webhooks
from app.core.pattern_engine import PatternMatchingEngine
from app.models.schemas import PatternMatchRequest, PatternMatchResponse

router = APIRouter()


@router.post("/match", response_model=PatternMatchResponse, summary="Confronta un budget bozza con gli archetipi vincenti")
def match_budget_pattern(request: PatternMatchRequest, background: BackgroundTasks, http: Request) -> PatternMatchResponse:
    timer = events.Timer()
    try:
        result = PatternMatchingEngine.analyze_budget_pattern(request.draft_budget)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    events.record("pattern.match", f"Archetipo più vicino: {result.closest_archetype} (coseno {result.similarity_score:.2f})", actor=actor_of(http),
                  duration_ms=timer.ms, details={"draft": request.draft_budget, "archetype": result.closest_archetype,
                                                 "similarity": result.similarity_score, "main_deviation": result.main_deviation.model_dump()})
    background.add_task(webhooks.emit, "event.pattern.matched", {
        "bando_category": request.bando_category, "closest_archetype": result.closest_archetype,
        "similarity_score": result.similarity_score})
    return result
