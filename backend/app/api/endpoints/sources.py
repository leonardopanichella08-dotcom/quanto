"""Da dove vengono i bandi: registro delle fonti ufficiali, stato di lettura e raccolta di nuovi bandi."""
import threading
import time
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.deps import actor_of
from app.core import official_sources

router = APIRouter()
_LAST_RUN = 0.0
_LOCK = threading.Lock()
MIN_SECONDS_BETWEEN_RUNS = 90          # la raccolta interroga decine di siti ufficiali: non la si lancia a raffica


@router.get("", summary="Registro delle fonti ufficiali dei bandi con stato di lettura e quante voci del catalogo arrivano da ciascuna")
def list_sources() -> dict:
    return official_sources.registry()


class RefreshBody(BaseModel):
    source_ids: Optional[List[str]] = Field(default=None, max_length=80, description="Solo queste fonti; senza, quelle controllate meno di recente")


@router.post("/refresh", summary="Cerca nuovi bandi nelle fonti ufficiali (le meno recenti per prime) e li iscrive nel catalogo")
def refresh(body: RefreshBody, request: Request) -> dict:
    global _LAST_RUN
    with _LOCK:
        wait = MIN_SECONDS_BETWEEN_RUNS - (time.monotonic() - _LAST_RUN)
        if wait > 0:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"Ricerca appena eseguita: riprova tra {int(wait) + 1} secondi")
        _LAST_RUN = time.monotonic()
    ids = [i for i in (body.source_ids or []) if i in official_sources.BY_ID] or None
    return official_sources.run(ids, budget_s=40.0, actor=actor_of(request))
