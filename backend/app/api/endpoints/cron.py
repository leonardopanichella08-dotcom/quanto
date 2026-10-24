"""Lavori periodici (Vercel Cron). Accesso: segreto del cron (CRON_SECRET) oppure un manager."""
import hmac
import os

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.api.deps import user_of
from app.core import catalog_job, catalog_meta, lifecycle, official_sources

router = APIRouter()


def _allowed(request: Request) -> bool:
    header = request.headers.get("authorization", "")
    secret = os.getenv("CRON_SECRET", "")
    if secret and header.lower().startswith("bearer ") and hmac.compare_digest(header[7:].strip().encode(), secret.encode()):
        return True
    u = user_of(request)
    return bool(u and u["role"] == "MANAGER")


@router.api_route("/catalog-refresh", methods=["GET", "POST"], summary="Stadio 1: aggiorna il catalogo dei bandi (solo metadati)")
def catalog_refresh(request: Request, enrich: int = Query(default=15, ge=0, le=50)) -> dict:
    if not _allowed(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Accesso non consentito")
    return catalog_job.refresh(enrich=enrich, actor="cron")


@router.api_route("/catalog-describe", methods=["GET", "POST"], summary="Legge la scheda ufficiale di un lotto di bandi del catalogo: descrizione breve e caratteristiche")
def catalog_describe(request: Request, limit: int = Query(default=400, ge=1, le=800)) -> dict:
    if not _allowed(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Accesso non consentito")
    harvest = official_sources.run(budget_s=15.0, workers=12, actor="cron")          # prima le fonti ufficiali (ministeri, Regioni, agenzie): le voci nuove si leggono subito dopo
    out = catalog_meta.describe_batch(limit=limit, workers=24, budget_s=32.0)
    return {**out, "harvest": {k: v for k, v in harvest.items() if k != "sources"}, "deleted": catalog_job.cleanup_stale(actor="cron")["deleted"]}


@router.api_route("/catalog-lifecycle", methods=["GET", "POST"], summary="Legge le date di apertura/chiusura di un lotto di voci del catalogo ed elimina quelle chiuse")
def catalog_lifecycle(request: Request, limit: int = Query(default=120, ge=1, le=300)) -> dict:
    if not _allowed(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Accesso non consentito")
    scan = lifecycle.scan_catalog(limit=limit, workers=16, budget_s=40.0)
    return {**scan, "deleted": catalog_job.cleanup_stale(actor="cron")["deleted"]}


@router.api_route("/sources-harvest", methods=["GET", "POST"], summary="Cerca nuovi bandi nelle fonti ufficiali (ministeri, Regioni, agenzie, UE) e li iscrive nel catalogo")
def sources_harvest(request: Request) -> dict:
    if not _allowed(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Accesso non consentito")
    out = official_sources.run(budget_s=45.0, workers=10, actor="cron")
    return {k: v for k, v in out.items() if k != "sources"}
