"""Biblioteca dei bandi: elenco, dettaglio, selezione e caricamento di un nuovo bando (testo o PDF)."""
import base64
import binascii
import io
import re
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from pydantic import BaseModel, Field, model_validator

from app.api.deps import actor_of
from app.core import bandi, events, webhooks
from app.core.ingestion import Ingestion

router = APIRouter()
MAX_UPLOAD_BYTES = 3_000_000
MAX_PDF_PAGES = 250


class UploadRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=200, description="Denominazione del bando")
    bando_id: Optional[str] = Field(default=None, max_length=64, pattern=r"^[A-Za-z0-9._\-]+$")
    filename: str = Field(default="bando.txt", max_length=200)
    text: Optional[str] = Field(default=None, max_length=500_000)
    content_base64: Optional[str] = Field(default=None, description="Contenuto del file (PDF o testo) in base64")
    issuer: Optional[str] = Field(default=None, max_length=120)
    source_url: Optional[str] = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def _one_source(self) -> "UploadRequest":
        if not self.text and not self.content_base64:
            raise ValueError("Fornire text oppure content_base64")
        return self


def _slug(name: str) -> str:
    return "CUSTOM-" + re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").upper()[:40]


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    if len(reader.pages) > MAX_PDF_PAGES:
        raise ValueError(f"PDF troppo lungo ({len(reader.pages)} pagine, max {MAX_PDF_PAGES})")
    return "\n".join((p.extract_text() or "") for p in reader.pages)


@router.get("", summary="Elenco dei bandi con copertura dei 60 criteri")
def list_all() -> list:
    return bandi.list_bandi()


@router.get("/references", summary="Quadri normativi di riferimento (es. de minimis)")
def references() -> list:
    return bandi.references()


@router.get("/{bando_id}", summary="Dettaglio del bando: regole con fonte, requisiti, copertura dei criteri, lacune")
def detail(bando_id: str) -> dict:
    d = bandi.get_bando_detail(bando_id)
    if d is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bando non trovato")
    return d


@router.post("/{bando_id}/select", summary="Seleziona il bando: restituisce le regole pronte per la validazione")
def select(bando_id: str, request: Request) -> dict:
    timer = events.Timer()
    d = bandi.get_bando_detail(bando_id)
    if d is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bando non trovato")
    if d["grant_rules"] is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nessuna regola pubblicata per questo bando")
    events.record("bandi.select", f"Selezionato {d['name']} ({len(d['rules'])} regole, {d['coverage_summary']['REGOLA_DEL_BANDO']} criteri attivati)",
                  bando_id=bando_id, actor=actor_of(request), duration_ms=timer.ms,
                  details={"rules": len(d["rules"]), "coverage": d["coverage_summary"], "rule_version_hash": d["grant_rules"]["rule_version_hash"]})
    return {"bando_id": bando_id, "name": d["name"], "status": d["status"], "grant_rules": d["grant_rules"], "coverage_summary": d["coverage_summary"],
            "not_specified": d["not_specified"]}


@router.post("/upload", summary="Carica il testo o il PDF di un bando: estrae regole, ambito e requisiti")
def upload(body: UploadRequest, request: Request, background: BackgroundTasks) -> dict:
    timer = events.Timer()
    bandi.ensure_seeded()
    raw = b""
    try:
        if body.content_base64:
            raw = base64.b64decode(body.content_base64, validate=True)
            if len(raw) > MAX_UPLOAD_BYTES:
                raise ValueError("File troppo grande (max 3 MB)")
            text = _pdf_text(raw) if (raw[:4] == b"%PDF" or body.filename.lower().endswith(".pdf")) else raw.decode("utf-8", errors="replace")
        else:
            text = body.text or ""
            raw = text.encode("utf-8")
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc) if isinstance(exc, ValueError) and not isinstance(exc, binascii.Error) else "Contenuto non valido") from exc
    except Exception as exc:  # PDF corrotto o cifrato
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Impossibile leggere il file (PDF corrotto o protetto?)") from exc
    if len(text.strip()) < 100:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Testo insufficiente: un PDF scansionato richiede un OCR (non incluso)")

    bando_id = body.bando_id or _slug(body.name)
    kind = "BANDO_PDF" if raw[:4] == b"%PDF" else "BANDO_TEXT"
    Ingestion.catalog(bando_id, body.name, body.issuer, None, body.source_url)
    digest = events.save_bando_source(bando_id, body.filename, text)
    events.add_document(kind, body.filename, raw, bando_id=bando_id, meta={"chars": len(text)})
    Ingestion.confirm(bando_id)
    outcome = Ingestion.extract(bando_id, source_text=text, source_ref=body.filename)
    detail = bandi.get_bando_detail(bando_id)
    to_review = [r for r in (outcome.requirements or []) if r["kind"] == "DA_REVISIONARE"]
    events.record("bando.upload", f"Analizzato «{body.name}»: {len(outcome.published)} regole, {len(outcome.requirements or [])} requisiti, {len(to_review)} da rivedere",
                  bando_id=bando_id, actor=actor_of(request), duration_ms=timer.ms,
                  details={"sha256": digest, "chars": len(text), "rules_published": sorted(outcome.published), "requirements": len(outcome.requirements or []),
                           "to_review": len(to_review), "kind": kind})
    if outcome.coverage_activated:
        background.add_task(webhooks.emit, "event.bando.coverage_activated", {"bando_id": bando_id})
    return {"bando_id": bando_id, "sha256": digest, "characters_read": len(text), "rules_published": outcome.published,
            "requirements_total": len(outcome.requirements or []), "requirements_to_review": len(to_review), "detail": detail}
