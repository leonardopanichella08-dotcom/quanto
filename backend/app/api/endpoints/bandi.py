"""Biblioteca dei bandi: elenco, dettaglio, selezione e caricamento di un nuovo bando (testo o PDF)."""
import base64
import binascii
import io
import re
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, model_validator

from app.api.deps import actor_of, require_auth, require_hq
from app.core import analysis, bandi, discovery, events, research, webhooks
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


def _web_slug(name: str) -> str:
    return "WEB-" + re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").upper()[:40]


# ------------------------------------------------------------------ ricerca sul web
class ResearchSearch(BaseModel):
    name: str = Field(..., min_length=3, max_length=120, description="Nome del bando da cercare")
    hint: str = Field(default="", max_length=120, description="Parole in più per restringere la ricerca (ente, anno…)")
    urls: List[str] = Field(default_factory=list, max_length=5, description="Link ufficiali che conosci già")


class ResearchFetch(BaseModel):
    bando_id: str = Field(..., max_length=64, pattern=r"^[A-Za-z0-9._\-]+$")
    url: str = Field(..., min_length=8, max_length=800)


class ResearchAnalyze(BaseModel):
    bando_id: str = Field(..., max_length=64, pattern=r"^[A-Za-z0-9._\-]+$")


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    if len(reader.pages) > MAX_PDF_PAGES:
        raise ValueError(f"PDF troppo lungo ({len(reader.pages)} pagine, max {MAX_PDF_PAGES})")
    return "\n".join((p.extract_text() or "") for p in reader.pages)


@router.post("/research/search", dependencies=[Depends(require_auth)], summary="Cerca il bando sul web: pagine e documenti, ufficiali per primi")
def research_search(body: ResearchSearch, request: Request) -> dict:
    timer = events.Timer()
    bandi.ensure_seeded()
    bando_id = _web_slug(body.name)
    try:
        result = research.search_web(body.name, body.hint, body.urls, discover=discovery.discover)
    except research.ResearchError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    Ingestion.catalog(bando_id, body.name.strip(), None, None, None)
    cands = result["candidates"]
    official = sum(1 for c in cands if c["tier"] == "UFFICIALE")
    events.record("bando.research.search", f"Ricerca web «{body.name}»: {len(cands)} risultati pertinenti ({official} ufficiali)", bando_id=bando_id,
                  status="OK" if cands else "WARN", actor=actor_of(request), duration_ms=timer.ms,
                  details={"queries": result["queries"], "engine_errors": result["engine_errors"], "top": [c["url"] for c in cands[:8]]})
    return {"bando_id": bando_id, "name": body.name.strip(), **result}


@router.post("/research/fetch", dependencies=[Depends(require_auth)], summary="Scarica una pagina o un PDF, ne salva il testo in memoria e restituisce i link utili")
def research_fetch(body: ResearchFetch, request: Request) -> dict:
    timer = events.Timer()
    if Ingestion.get_bando(body.bando_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bando non trovato: avvia prima la ricerca")
    try:
        doc = research.fetch_document(body.url)
    except research.ResearchError as exc:
        events.record("bando.research.fetch", f"Download non riuscito: {body.url[:120]} — {exc}", bando_id=body.bando_id, status="WARN",
                      actor=actor_of(request), duration_ms=timer.ms, details={"url": body.url, "error": str(exc)})
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    warns = list(doc["warnings"])
    if doc["chars"] > events.MAX_SOURCE_TEXT:
        warns.append(f"Testo salvato solo per i primi {events.MAX_SOURCE_TEXT:,} caratteri su {doc['chars']:,} (il file originale è conservato per intero)".replace(",", "."))
    file_sha = events.save_bando_file(body.bando_id, doc["title"], doc["raw"], doc["content_type"])
    digest = events.save_bando_source(body.bando_id, doc["title"], doc["text"], url=doc["url"], tier=doc["tier"], content_type=doc["content_type"],
                                      pages=doc["pages"], origin="WEB", file_sha256=file_sha, warnings=warns)
    events.add_document("BANDO_PDF" if doc["kind"] == "PDF" else "BANDO_WEB", doc["url"], doc["raw"], bando_id=body.bando_id,
                        meta={"url": doc["url"], "kind": doc["kind"], "chars": doc["chars"], "pages": doc["pages"], "tier": doc["tier"]})
    known = {research.normalize_url(s["url"]) for s in events.list_bando_sources(body.bando_id) if s.get("url")}
    links = research.find_links(doc["url"], doc["links"], known, focus=(Ingestion.get_bando(body.bando_id) or {}).get("name", ""))
    events.record("bando.research.fetch", f"Scaricato {doc['kind']} ({doc['tier'].lower()}): {doc['title'][:80]}, {doc['chars']} caratteri",
                  bando_id=body.bando_id, actor=actor_of(request), duration_ms=timer.ms,
                  details={"url": doc["url"], "sha256": digest, "size_bytes": doc["size_bytes"], "pages": doc["pages"], "links_found": len(links), "warnings": doc["warnings"]})
    return {"source": {"name": doc["title"], "url": doc["url"], "tier": doc["tier"], "kind": doc["kind"], "chars": doc["chars"], "pages": doc["pages"],
                       "size_bytes": doc["size_bytes"], "sha256": digest, "warnings": warns}, "links": links}


@router.post("/research/analyze", dependencies=[Depends(require_auth)], summary="Legge tutti i documenti in memoria: regole, requisiti, dati chiave, riferimenti di legge")
def research_analyze(body: ResearchAnalyze, request: Request, background: BackgroundTasks) -> dict:
    timer = events.Timer()
    if Ingestion.get_bando(body.bando_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bando non trovato")
    if not events.list_bando_sources(body.bando_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nessun documento in memoria da analizzare")
    res = analysis.run_analysis(body.bando_id)
    outcome, reqs = res["outcome"], res["requirements"]
    detail = bandi.get_bando_detail(body.bando_id)
    to_review = [r for r in reqs if r["kind"] == "DA_REVISIONARE"]
    topics = {}
    for r in reqs:
        topics[r["topic"]] = topics.get(r["topic"], 0) + 1
    empty = [x for x in res["report"] if not x["requirements"]]
    events.record("bando.research.analyze", f"Analizzate {res['sources']} fonti: {len(outcome.published)} regole, {len(reqs)} requisiti ({len(to_review)} da rivedere), "
                  f"{len(detail['legal_refs'])} atti citati" + (f"; {len(empty)} documenti senza requisiti" if empty else ""),
                  bando_id=body.bando_id, actor=actor_of(request), duration_ms=timer.ms, status="OK" if reqs else "WARN",
                  details={"sources": res["sources"], "rules_published": sorted(outcome.published), "requirements": len(reqs), "to_review": len(to_review), "topics": topics,
                           "report": res["report"]})
    if outcome.coverage_activated:
        background.add_task(webhooks.emit, "event.bando.coverage_activated", {"bando_id": body.bando_id})
    return {"bando_id": body.bando_id, "sources": res["sources"], "rules_published": outcome.published, "requirements_total": len(reqs),
            "requirements_to_review": len(to_review), "topics": topics, "legal_refs": detail["legal_refs"], "sources_report": res["report"],
            "warning": None if reqs else "Non sono riuscito a ricavare requisiti da nessun documento: vedi il motivo per ciascuno e aggiungi il testo ufficiale a mano.", "detail": detail}


@router.get("/{bando_id}/sources/{sha256}", dependencies=[Depends(require_hq)], summary="Testo integrale di una fonte salvata in memoria (solo Quartier Generale)")
def source_text(bando_id: str, sha256: str) -> dict:
    for s in events.list_bando_sources(bando_id):
        if s["sha256"] == sha256:
            return {"name": s["name"], "url": s.get("url"), "tier": s.get("tier"), "pages": s.get("pages"), "chars": len(s["text"]), "ts": s["ts"], "text": s["text"][:400_000]}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fonte non trovata")


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
    file_sha = events.save_bando_file(bando_id, body.filename, raw, "application/pdf" if raw[:4] == b"%PDF" else "text/plain")
    digest = events.save_bando_source(bando_id, body.filename, text, url=body.source_url, origin="UPLOAD", file_sha256=file_sha,
                                      content_type="application/pdf" if raw[:4] == b"%PDF" else "text/plain")
    events.add_document(kind, body.filename, raw, bando_id=bando_id, meta={"chars": len(text)})
    Ingestion.confirm(bando_id)
    res = analysis.run_analysis(bando_id)
    outcome = res["outcome"]
    outcome.requirements = res["requirements"]
    detail = bandi.get_bando_detail(bando_id)
    to_review = [r for r in (outcome.requirements or []) if r["kind"] == "DA_REVISIONARE"]
    events.record("bando.upload", f"Analizzato «{body.name}»: {len(outcome.published)} regole, {len(outcome.requirements or [])} requisiti, {len(to_review)} da rivedere",
                  bando_id=bando_id, actor=actor_of(request), duration_ms=timer.ms,
                  details={"sha256": digest, "chars": len(text), "rules_published": sorted(outcome.published), "requirements": len(outcome.requirements or []),
                           "to_review": len(to_review), "kind": kind})
    if outcome.coverage_activated:
        background.add_task(webhooks.emit, "event.bando.coverage_activated", {"bando_id": bando_id})
    mine = next((x for x in res["report"] if x["sha256"] == digest), None)
    return {"bando_id": bando_id, "sha256": digest, "characters_read": len(text), "rules_published": outcome.published,
            "requirements_total": len(outcome.requirements or []), "requirements_to_review": len(to_review), "sources_report": res["report"],
            "this_document": mine, "warning": (mine["note"] if mine and not mine["requirements"] else None), "detail": detail}
