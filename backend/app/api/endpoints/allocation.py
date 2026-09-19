import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status

from app.api.deps import actor_of
from app.core import events, webhooks
from app.core.allocation_engine import AllocationOptimizerEngine
from app.models.allocation import AllocationOptimizationRequest, AllocationResponse

router = APIRouter()
logger = logging.getLogger("quanto.allocation")


@router.post("/optimize", response_model=AllocationResponse,
             summary="Mappa le spese correnti sulle linee di finanziamento attive (Missione Due)")
def optimize_allocation_plan(request: AllocationOptimizationRequest, background: BackgroundTasks, http: Request) -> AllocationResponse:
    timer = events.Timer()
    if not request.historical_expenses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Elenco spese storiche vuoto.")
    try:
        result = AllocationOptimizerEngine.optimize_annual_allocation(request)
    except RuntimeError as exc:
        logger.exception("Risolutore fallito")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Il risolutore non ha prodotto una soluzione") from exc
    run_id = events.save_run("ALLOCATION", None, None, request.model_dump(mode="json"), result.model_dump(mode="json"))
    events.record("allocation.optimize",
                  f"Piano {result.fiscal_year}: coperto {result.covered_by_public_funds_eur:,.2f} € su {result.total_gross_expense_eur:,.2f} € ({result.optimization_target.value})",
                  actor=actor_of(http), duration_ms=timer.ms, run_id=run_id,
                  details={"target": result.optimization_target.value, "excluded_funds": result.excluded_funds, "funds_involved": result.funds_involved,
                           "net_cost_to_entity_eur": result.net_cost_to_entity_eur, "solver": result.solver, "status": result.status})
    background.add_task(webhooks.emit, "event.allocation.optimized", {
        "fiscal_year": result.fiscal_year, "net_cost_to_entity_eur": result.net_cost_to_entity_eur,
        "target": result.optimization_target.value})
    return result
