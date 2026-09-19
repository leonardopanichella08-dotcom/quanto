from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.core import webhooks
from app.core.pattern_engine import PatternMatchingEngine
from app.models.schemas import PatternMatchRequest, PatternMatchResponse

router = APIRouter()


@router.post("/match", response_model=PatternMatchResponse, summary="Confronta un budget bozza con gli archetipi vincenti")
def match_budget_pattern(request: PatternMatchRequest, background: BackgroundTasks) -> PatternMatchResponse:
    try:
        result = PatternMatchingEngine.analyze_budget_pattern(request.draft_budget)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    background.add_task(webhooks.emit, "event.pattern.matched", {
        "bando_category": request.bando_category, "closest_archetype": result.closest_archetype,
        "similarity_score": result.similarity_score})
    return result
