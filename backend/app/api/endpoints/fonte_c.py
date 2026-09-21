"""Fonte C — documenti contabili del cliente: buste paga, bilanci, F24 (Modulo 9.3, 16)."""
import base64
import binascii
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.api.deps import actor_of
from app.core import crypto_store
from app.core.fonte_c import service

router = APIRouter()


class UploadBody(BaseModel):
    doc_type: str = Field(..., description="PAYSLIP | BALANCE_SHEET | F24")
    filename: str = Field(..., max_length=200)
    content_base64: str


class ReviewBody(BaseModel):
    action: str = Field(..., description="CONFIRM | CORRECT")
    value: Optional[str] = Field(default=None, max_length=2000)


def _owner(request: Request) -> str:
    return actor_of(request)


def _guard(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except service.DocumentError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except crypto_store.FileKeyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.post("/documents", status_code=status.HTTP_201_CREATED, summary="Carica un documento (PDF, anche scansionato): lettura con confidenza per campo")
def upload(body: UploadBody, request: Request) -> dict:
    try:
        data = base64.b64decode(body.content_base64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File non valido (base64)") from None
    return _guard(service.upload, body.doc_type, body.filename, data, _owner(request))


@router.get("/documents", summary="I tuoi documenti")
def documents(request: Request) -> list:
    return service.list_documents(_owner(request))


@router.get("/documents/{document_id}", summary="Un documento con tutti i campi letti, la confidenza e lo stato")
def document(document_id: int, request: Request) -> dict:
    d = service.get(document_id, _owner(request))
    if d is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento non trovato")
    return d


@router.get("/documents/{document_id}/file", summary="Il file originale (decifrato solo per te)")
def file(document_id: int, request: Request) -> Response:
    f = _guard(service.original, document_id, _owner(request))
    if f is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento non trovato")
    return Response(f["data"], media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{f["name"]}"'})


@router.delete("/documents/{document_id}", summary="Elimina il documento e i suoi campi")
def delete(document_id: int, request: Request) -> dict:
    if not service.delete(document_id, _owner(request)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento non trovato")
    return {"deleted": document_id}


@router.post("/documents/{document_id}/fields/{field_id}/review", summary="Conferma o correggi un campo letto con poca sicurezza")
def review(document_id: int, field_id: int, body: ReviewBody, request: Request) -> dict:
    try:
        return _guard(service.review_field, field_id, body.action, body.value, _owner(request), _owner(request))
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campo non trovato") from None


@router.get("/documents/{document_id}/cost-line", summary="Voce di personale precompilata da una busta paga (solo campi sicuri o confermati)")
def cost_line(document_id: int, request: Request) -> dict:
    try:
        return _guard(service.payslip_cost_line, document_id, _owner(request))
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Busta paga non trovata") from None


@router.get("/documents/{document_id}/expenses", summary="Spese storiche di un bilancio, pronte per l'allocazione annuale")
def expenses(document_id: int, request: Request) -> dict:
    try:
        return _guard(service.balance_expenses, document_id, _owner(request))
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bilancio non trovato") from None
