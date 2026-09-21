import logging

from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.deps import actor_of, require_hq
from app.core import events, funds, webhooks
from app.core.fonte_c import service as fonte_c
from app.core.allocation_engine import AllocationOptimizerEngine
from app.models.allocation import AllocationOptimizationRequest, AllocationResponse, ExpenseLine

router = APIRouter()
logger = logging.getLogger("quanto.allocation")


@router.post("/optimize", response_model=AllocationResponse,
             summary="Mappa le spese correnti sulle linee di finanziamento attive (Missione Due)")
def optimize_allocation_plan(request: AllocationOptimizationRequest, background: BackgroundTasks, http: Request) -> AllocationResponse:
    timer = events.Timer()
    source = "spese fornite"
    if request.historical_balance_ref is not None:          # spese lette dal bilancio caricato (Fonte C): solo righe sicure o confermate
        try:
            ex = fonte_c.balance_expenses(request.historical_balance_ref)
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bilancio non trovato") from None
        except fonte_c.DocumentError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        pending = ex["needs_review"] + ex["needs_category"]
        if pending:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
                "message": f"{len(pending)} righe del bilancio vanno verificate (lettura incerta o categoria mancante) prima di pianificare", "lines": pending})
        request.historical_expenses = [ExpenseLine(item_id=f"EXP-{ln['field_id']}", category=ln["category"], amount_eur=float(ln["amount_eur"])) for ln in ex["lines"]]
        source = f"bilancio {request.historical_balance_ref}"
    if not request.historical_expenses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Elenco spese storiche vuoto.")
    if not request.available_funding_lines:                # fondi dalle linee attive (ricavate dai bandi), mai dal codice
        request.available_funding_lines = funds.funding_lines_for_allocation()
        if not request.available_funding_lines:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nessuna linea di finanziamento attiva: creala dai bandi (Quartier Generale → Fondi) prima di pianificare")
    if request.de_minimis_residual_eur is None and any(f.de_minimis for f in request.available_funding_lines):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="de_minimis_residual_eur è obbligatorio se almeno un fondo è in regime de minimis")
    try:
        result = AllocationOptimizerEngine.optimize_annual_allocation(request)
    except RuntimeError as exc:
        logger.exception("Risolutore fallito")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Il risolutore non ha prodotto una soluzione") from exc
    run_id = events.save_run("ALLOCATION", None, None, request.model_dump(mode="json"), result.model_dump(mode="json"))
    events.record("allocation.optimize",
                  f"Piano {result.fiscal_year} da {source}: coperto {result.covered_by_public_funds_eur:,.2f} € su {result.total_gross_expense_eur:,.2f} € ({result.optimization_target.value})",
                  actor=actor_of(http), duration_ms=timer.ms, run_id=run_id,
                  details={"target": result.optimization_target.value, "excluded_funds": result.excluded_funds, "funds_involved": result.funds_involved,
                           "net_cost_to_entity_eur": result.net_cost_to_entity_eur, "solver": result.solver, "status": result.status})
    background.add_task(webhooks.emit, "event.allocation.optimized", {
        "fiscal_year": result.fiscal_year, "net_cost_to_entity_eur": result.net_cost_to_entity_eur,
        "target": result.optimization_target.value})
    return result


# ------------------------------------------------------------------ linee di finanziamento (Fonte A → fondi dell'allocazione)
class FundBody(BaseModel):
    fund_id: str = Field(..., min_length=2, max_length=64)
    name: Optional[str] = None
    bando_id: Optional[str] = None
    allowed_categories: List[str]
    coverage_pct: float
    category_coverage_pct: dict = Field(default_factory=dict)
    max_total_eur: Optional[float] = None
    category_max_share: dict = Field(default_factory=dict)
    de_minimis: bool = False
    excludes: List[str] = Field(default_factory=list)
    active_from_month: int = 1
    active_to_month: int = 12
    source_ref: Optional[str] = None
    active: bool = True


class DeriveBody(BaseModel):
    bando_id: str
    fiscal_year: int = Field(..., ge=2020, le=2100)
    max_total_eur: Optional[float] = Field(default=None, gt=0, description="Dotazione massima erogabile all'ente: il bando non la dice, la indica una persona (vuoto = nessun tetto dichiarato)")
    de_minimis: bool = False
    fund_id: Optional[str] = None


def _fund_guard(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except funds.FundError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/funds", summary="Linee di finanziamento usate dall'allocazione (ricavate dai bandi)")
def list_funds() -> list:
    return funds.list_funds()


@router.post("/funds", dependencies=[Depends(require_hq)], summary="Crea o modifica una linea di finanziamento")
def upsert_fund(body: FundBody, request: Request) -> dict:
    return _fund_guard(funds.upsert_fund, body.model_dump(), actor_of(request))


@router.post("/funds/from-bando", dependencies=[Depends(require_hq)], summary="Ricava la linea dalle regole pubblicate di un bando")
def derive_fund(body: DeriveBody, request: Request) -> dict:
    return _fund_guard(funds.derive_from_bando, body.bando_id, body.fiscal_year, actor_of(request), body.max_total_eur, body.de_minimis, body.fund_id)


@router.delete("/funds/{fund_id}", dependencies=[Depends(require_hq)], summary="Elimina una linea di finanziamento")
def delete_fund(fund_id: str, request: Request) -> dict:
    if not funds.delete_fund(fund_id, actor_of(request)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linea non trovata")
    return {"deleted": fund_id}
