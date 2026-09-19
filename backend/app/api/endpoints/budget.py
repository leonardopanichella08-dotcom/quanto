import io
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import StreamingResponse

from app.core import webhooks
from app.core.budget_service import validate_budget
from app.core.criteria_catalog import BUDGET_LEVEL, CRITERIA_TITLES
from app.core.export import build_pdf, build_xlsx
from app.models.schemas import BudgetValidationRequest, BudgetValidationResponse

router = APIRouter()
logger = logging.getLogger("quanto.budget")


def _require_items(request: BudgetValidationRequest) -> None:
    if not request.cost_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Il budget inviato non contiene alcuna riga di costo da validare.")


@router.post("/validate", response_model=BudgetValidationResponse, summary="Valida deterministicamente un budget di progetto (Missione Uno)")
def validate_project_budget(request: BudgetValidationRequest, background: BackgroundTasks) -> BudgetValidationResponse:
    _require_items(request)
    result = validate_budget(request)
    background.add_task(webhooks.emit, "event.budget.validated", {
        "project_id": result.project_id, "bando_id": result.bando_id,
        "conformity_score": result.conformity_score, "merkle_root": result.merkle_root})
    for item in result.items:
        if item.criteria_failed and item.status.value in ("REJECTED", "MISSING_DOCUMENTS"):
            background.add_task(webhooks.emit, "event.criteria.failed", {
                "project_id": result.project_id, "item_id": item.item_id, "criteria_failed": item.criteria_failed})
    return result


@router.post("/export/xlsx", summary="Esporta il budget validato in XLSX con CEP-ID e QR (Layer 1)")
def export_budget_xlsx(request: BudgetValidationRequest) -> StreamingResponse:
    _require_items(request)
    result = validate_budget(request)
    return StreamingResponse(
        io.BytesIO(build_xlsx(result)),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{result.cep_id}.xlsx"'},
    )


@router.post("/export/pdf", summary="Esporta il budget validato in PDF con CEP-ID e QR (Layer 1)")
def export_budget_pdf(request: BudgetValidationRequest) -> StreamingResponse:
    _require_items(request)
    result = validate_budget(request)
    return StreamingResponse(io.BytesIO(build_pdf(result)), media_type="application/pdf",
                             headers={"Content-Disposition": f'attachment; filename="{result.cep_id}.pdf"'})


@router.get("/criteria", summary="I 60 criteri del Deterministic Engine")
def list_criteria() -> dict:
    return {
        "total_criteria": 60, "implemented_count": len(CRITERIA_TITLES),
        "note": "Un criterio si esegue solo se la riga (o le regole del bando) forniscono il dato necessario; altrimenti risulta non valutato.",
        "criteria": [{"number": n, "title": t, "level": "BUDGET" if n in BUDGET_LEVEL else "ITEM"} for n, t in sorted(CRITERIA_TITLES.items())],
    }
