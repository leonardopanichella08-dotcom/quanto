"""Lavori periodici (Vercel Cron). Accesso: segreto del cron (CRON_SECRET) oppure un manager."""
import hmac
import os

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.api.deps import user_of
from app.core import catalog_job

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
