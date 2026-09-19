import base64
import binascii
import io
import json
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.deps import actor_of
from app.core import bandi, events, webhooks
from app.core.budget_io import parse_import, template_xlsx
from app.core.budget_service import validate_budget
from app.core.criteria_catalog import BUDGET_LEVEL, CRITERIA_TITLES
from app.core.demo import SANDBOX_ID, build_demo
from app.core.export import build_pdf, build_xlsx
from app.core.field_catalog import CATEGORY_OPTIONS, FIELDS
from app.models.schemas import BudgetValidationRequest, BudgetValidationResponse, GrantRuleSet

router = APIRouter()
logger = logging.getLogger("quanto.budget")


class ImportRequest(BaseModel):
    filename: str = Field(..., max_length=200)
    content_base64: str = Field(..., max_length=3_000_000)


def _require_items(request: BudgetValidationRequest) -> None:
    if not request.cost_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Il budget inviato non contiene alcuna riga di costo da validare.")


def _same_as_last(project_id: str, response: dict) -> Optional[int]:
    """Se l'ultima validazione del progetto ha lo stesso esito (radice, totali e controlli di budget) non crea una nuova esecuzione."""
    with events.connect() as conn:
        row = conn.execute("SELECT id, response_json FROM runs WHERE project_id=? AND kind='VALIDATE' ORDER BY id DESC LIMIT 1", (project_id,)).fetchone()
    if row is None:
        return None
    last = json.loads(row["response_json"])
    keys = ("merkle_root", "total_approved_eur", "total_requested_eur", "conformity_score", "budget_checks", "bando_id")
    return row["id"] if all(last.get(k) == response.get(k) for k in keys) else None


@router.post("/validate", response_model=BudgetValidationResponse, summary="Valida deterministicamente un budget di progetto (Missione Uno)")
def validate_project_budget(request: BudgetValidationRequest, background: BackgroundTasks, http: Request) -> BudgetValidationResponse:
    timer = events.Timer()
    _require_items(request)
    result = validate_budget(request)
    dumped = result.model_dump(mode="json")
    run_id = _same_as_last(request.project_id, dumped)
    if run_id is None:
        run_id = events.save_run("VALIDATE", request.project_id, request.grant_rules.bando_id, request.model_dump(mode="json"), dumped, result.merkle_root)
        by_status = {}
        for i in result.items:
            by_status[i.status.value] = by_status.get(i.status.value, 0) + 1
        events.record(
            "budget.validate",
            f"{len(result.items)} voci · ammesso {result.total_approved_eur:,.2f} € su {result.total_requested_eur:,.2f} € · score {result.conformity_score}/100",
            project_id=request.project_id, bando_id=request.grant_rules.bando_id, actor=actor_of(http), duration_ms=timer.ms, run_id=run_id,
            details={"status": result.status, "conformity_score": result.conformity_score, "total_requested_eur": result.total_requested_eur,
                     "total_approved_eur": result.total_approved_eur, "by_status": by_status, "merkle_root": result.merkle_root, "cep_id": result.cep_id,
                     "stages": [{"key": s.key, "ms": s.duration_ms} for s in (result.trace.stages if result.trace else [])]})
    result.run_id = run_id
    background.add_task(webhooks.emit, "event.budget.validated", {
        "project_id": result.project_id, "bando_id": result.bando_id, "conformity_score": result.conformity_score, "merkle_root": result.merkle_root})
    for item in result.items:
        if item.criteria_failed and item.status.value in ("REJECTED", "MISSING_DOCUMENTS"):
            background.add_task(webhooks.emit, "event.criteria.failed", {
                "project_id": result.project_id, "item_id": item.item_id, "criteria_failed": item.criteria_failed})
    return result


def _export(request: BudgetValidationRequest, http: Request, kind: str):
    timer = events.Timer()
    _require_items(request)
    result = validate_budget(request)
    data = build_xlsx(result) if kind == "xlsx" else build_pdf(result)
    name = f"{result.cep_id}.{kind}"
    events.add_document("EXPORT_XLSX" if kind == "xlsx" else "EXPORT_PDF", name, data, project_id=request.project_id, bando_id=request.grant_rules.bando_id,
                        meta={"cep_id": result.cep_id, "merkle_root": result.merkle_root})
    events.record(f"budget.export_{kind}", f"Esportato {name} ({len(data):,} byte)", project_id=request.project_id, bando_id=request.grant_rules.bando_id,
                  actor=actor_of(http), duration_ms=timer.ms, details={"cep_id": result.cep_id, "sha256": events.sha256_hex(data)})
    media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if kind == "xlsx" else "application/pdf"
    return StreamingResponse(io.BytesIO(data), media_type=media, headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.post("/export/xlsx", summary="Esporta il budget validato in XLSX con CEP-ID e QR (Layer 1)")
def export_budget_xlsx(request: BudgetValidationRequest, http: Request) -> StreamingResponse:
    return _export(request, http, "xlsx")


@router.post("/export/pdf", summary="Esporta il budget validato in PDF con CEP-ID e QR (Layer 1)")
def export_budget_pdf(request: BudgetValidationRequest, http: Request) -> StreamingResponse:
    return _export(request, http, "pdf")


@router.get("/fields", summary="Catalogo dei campi di una voce di costo (per l'editor e il template)")
def fields() -> dict:
    return {"categories": CATEGORY_OPTIONS, "fields": FIELDS}


@router.get("/template.xlsx", summary="Template Excel con tutte le colonne, esempi e guida ai campi")
def template(http: Request) -> StreamingResponse:
    timer = events.Timer()
    data = template_xlsx()
    events.record("budget.template", "Scaricato il template Excel delle voci", actor=actor_of(http), duration_ms=timer.ms)
    return StreamingResponse(io.BytesIO(data), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": 'attachment; filename="quanto_template_voci.xlsx"'})


@router.post("/import", summary="Importa le voci da un file .xlsx o .csv (errori riga per riga)")
def import_items(body: ImportRequest, http: Request) -> dict:
    timer = events.Timer()
    try:
        data = base64.b64decode(body.content_base64, validate=True)
    except binascii.Error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contenuto base64 non valido") from None
    try:
        parsed = parse_import(body.filename, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Import fallito")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="File illeggibile") from exc
    events.add_document("IMPORT_XLSX", body.filename, data, meta={"rows_read": parsed["rows_read"], "imported": len(parsed["items"]), "errors": len(parsed["errors"])})
    events.record("budget.import", f"Import di {body.filename}: {len(parsed['items'])} voci valide, {len(parsed['errors'])} righe con errori",
                  status="OK" if not parsed["errors"] else "WARN", actor=actor_of(http), duration_ms=timer.ms,
                  details={"rows_read": parsed["rows_read"], "imported": len(parsed["items"]), "errors": parsed["errors"][:20], "ignored_columns": parsed["ignored_columns"]})
    return parsed


@router.get("/demo", summary="Scenario demo adattato alle regole del bando (stress-test 46 voci o progetto realistico)")
def demo(http: Request, bando_id: str = Query(default=SANDBOX_ID), mode: str = Query(default="stress", pattern="^(stress|realistic)$")) -> dict:
    timer = events.Timer()
    detail = bandi.get_bando_detail(bando_id)
    if detail is None or detail["grant_rules"] is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bando non trovato o senza regole pubblicate")
    scenario = build_demo(GrantRuleSet.model_validate(detail["grant_rules"]), mode=mode)
    events.record("budget.demo", f"Scenario {mode} per {detail['name']}: {len(scenario['cost_items'])} voci", bando_id=bando_id, actor=actor_of(http), duration_ms=timer.ms)
    return scenario


@router.get("/criteria", summary="I 60 criteri del Deterministic Engine")
def list_criteria() -> dict:
    return {
        "total_criteria": 60, "implemented_count": len(CRITERIA_TITLES),
        "note": "Un criterio si esegue solo se la riga (o le regole del bando) forniscono il dato necessario; altrimenti risulta non valutato.",
        "criteria": [{"number": n, "title": t, "level": "BUDGET" if n in BUDGET_LEVEL else "ITEM"} for n, t in sorted(CRITERIA_TITLES.items())],
    }
