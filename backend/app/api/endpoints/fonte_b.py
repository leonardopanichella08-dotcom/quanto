"""Fonte B — tabelle ufficiali versionate (Modulo 9.2): consultazione per gli utenti, caricamento e pubblicazione per il manager."""
import base64
import binascii
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.api.deps import actor_of, require_hq
from app.core import events, fonte_b, fonte_b_admin as admin

router = APIRouter()
hq_only = [Depends(require_hq)]


class DatasetUpload(BaseModel):
    kind: str = Field(..., description="CCNL | PARAMS | AMORTIZATION | BENCHMARK")
    code: str = Field(..., min_length=2, max_length=40, description="CCNL: sigla del contratto; altri tipi: nome breve dell'insieme")
    name: str = Field(..., min_length=3, max_length=160)
    version: str = Field(..., min_length=1, max_length=40)
    valid_from: date
    valid_to: Optional[date] = None
    source_name: str = Field(..., min_length=3, max_length=200, description="Documento ufficiale da cui vengono i valori")
    source_url: Optional[str] = Field(default=None, max_length=500)
    source_ref: Optional[str] = Field(default=None, max_length=300, description="Numero, data, articolo del documento")
    filename: str = Field(..., max_length=200)
    content_base64: str
    notes: Optional[str] = Field(default=None, max_length=1000)


class PublishRequest(BaseModel):
    attest_official: bool = Field(..., description="Attesto che i valori corrispondono alla fonte ufficiale indicata")


@router.get("/summary", summary="Cosa c'è oggi in Fonte B: contratti, parametri, categorie (per l'editor delle voci)")
def summary(on: Optional[date] = None) -> dict:
    data = fonte_b.load(on)
    return {"on": data.on.isoformat(), "counts": data.summary(), "ccnl": data.ccnl_codes(), "amortization": data.amortization_categories(),
            "benchmarks": {"PRICE": data.benchmark_categories("PRICE"), "DAILY_RATE": data.benchmark_categories("DAILY_RATE")},
            "known_params": {k: {"label": v[0], "unit": v[1], "criterion": v[2]} for k, v in fonte_b.KNOWN_PARAMS.items()}}


@router.get("/kinds", dependencies=hq_only, summary="Tipi di tabella e colonne attese dal file")
def kinds() -> dict:
    return {k: {"label": admin.KIND_LABEL[k], "columns": list(admin.COLUMNS[k]), "required": admin.REQUIRED[k]} for k in admin.KINDS}


@router.get("/template/{kind}.csv", dependencies=hq_only, summary="Intestazione del file da compilare (senza valori d'esempio)")
def template(kind: str) -> Response:
    try:
        text = admin.template_csv(kind.upper())
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo sconosciuto") from None
    return Response(text, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="fonte_b_{kind.lower()}.csv"'})


@router.get("/datasets", dependencies=hq_only, summary="Tutti gli insiemi di dati: bozze, pubblicati, sostituiti")
def datasets() -> list:
    return admin.list_datasets()


@router.get("/datasets/{dataset_id}", dependencies=hq_only, summary="Un insieme con tutte le sue righe")
def dataset(dataset_id: int) -> dict:
    d = admin.dataset_detail(dataset_id)
    if d is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insieme non trovato")
    return d


@router.get("/datasets/{dataset_id}/file", dependencies=hq_only, summary="File originale caricato")
def dataset_file(dataset_id: int) -> Response:
    f = admin.original_file(dataset_id)
    if f is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File non disponibile")
    return Response(f["data"], media_type="application/octet-stream", headers={"Content-Disposition": f'attachment; filename="{f["name"]}"'})


@router.post("/datasets", dependencies=hq_only, status_code=status.HTTP_201_CREATED, summary="Carica un file: crea una BOZZA (non ancora usata nei calcoli)")
def upload(body: DatasetUpload, request: Request) -> dict:
    try:
        data = base64.b64decode(body.content_base64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File non valido (base64)") from None
    if len(data) > 5_000_000:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File troppo grande (massimo 5 MB)")
    try:
        d = admin.create_draft(body.kind.upper(), body.code, body.name, body.version, body.valid_from, body.valid_to, body.source_name,
                               body.source_url, body.source_ref, body.filename, data, actor_of(request), body.notes)
    except admin.FonteBFileError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"message": str(exc), "errors": exc.errors}) from exc
    events.record("fonte_b.upload", f"Bozza Fonte B {d['kind']} {d['code']} v{d['version']}: {d['rows']} righe", actor=actor_of(request), details={"id": d["id"]})
    return d


@router.post("/datasets/{dataset_id}/publish", dependencies=hq_only, summary="Pubblica una bozza: da ora i calcoli la usano (alla sua data di validità)")
def publish(dataset_id: int, body: PublishRequest, request: Request) -> dict:
    try:
        d = admin.publish(dataset_id, actor_of(request), body.attest_official)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insieme non trovato") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    events.record("fonte_b.publish", f"Pubblicato Fonte B {d['kind']} {d['code']} v{d['version']} dal {d['valid_from']}", actor=actor_of(request), details={"id": dataset_id})
    return d


@router.delete("/datasets/{dataset_id}", dependencies=hq_only, summary="Elimina una bozza")
def delete(dataset_id: int, request: Request) -> dict:
    try:
        ok = admin.delete_draft(dataset_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insieme non trovato")
    events.record("fonte_b.delete", f"Bozza Fonte B {dataset_id} eliminata", actor=actor_of(request))
    return {"deleted": dataset_id}
