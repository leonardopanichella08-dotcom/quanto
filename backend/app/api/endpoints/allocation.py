import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.core import webhooks
from app.core.allocation_engine import AllocationOptimizerEngine
from app.models.allocation import AllocationOptimizationRequest, AllocationResponse

router = APIRouter()
logger = logging.getLogger("quanto.allocation")


@router.post("/optimize", response_model=AllocationResponse,
             summary="Mappa le spese correnti sulle linee di finanziamento attive (Missione Due)")
def optimize_allocation_plan(request: AllocationOptimizationRequest, background: BackgroundTasks) -> AllocationResponse:
    if not request.historical_expenses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Elenco spese storiche vuoto.")
    try:
        result = AllocationOptimizerEngine.optimize_annual_allocation(request)
    except RuntimeError as exc:
        logger.exception("Risolutore fallito")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Il risolutore non ha prodotto una soluzione") from exc
    background.add_task(webhooks.emit, "event.allocation.optimized", {
        "fiscal_year": result.fiscal_year, "net_cost_to_entity_eur": result.net_cost_to_entity_eur,
        "target": result.optimization_target.value})
    return result
