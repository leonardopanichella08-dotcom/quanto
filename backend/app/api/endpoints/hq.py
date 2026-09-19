"""Quartier Generale: accesso con codice manager e consultazione (sola lettura) di timeline, dossier, documenti e database."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.api.deps import require_hq
from app.core import events, hq

router = APIRouter()


class LoginRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=64)


@router.post("/login", summary="Accesso al Quartier Generale con il codice manager")
def hq_login(body: LoginRequest, request: Request) -> dict:
    client = request.client.host if request.client else "unknown"
    try:
        token = hq.login(body.code, client)
    except hq.HQLocked as exc:
        events.record("hq.login", "Accesso HQ bloccato: troppi tentativi", status="LOCKED", actor=f"ip:{client}")
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"Troppi tentativi: riprova tra {exc.retry_after} secondi",
                            headers={"Retry-After": str(exc.retry_after)}) from exc
    except hq.HQAuthError:
        events.record("hq.login", "Tentativo di accesso HQ con codice errato", status="DENIED", actor=f"ip:{client}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Codice non valido") from None
    events.record("hq.login", "Accesso al Quartier Generale", actor=f"ip:{client}")
    return {"token": token, "expires_in": hq.TOKEN_TTL_S}


deps = [Depends(require_hq)]


@router.get("/overview", dependencies=deps, summary="Panoramica: contatori, storage, registro, operazioni, ultimi eventi")
def hq_overview() -> dict:
    return hq.overview()


@router.get("/operations", dependencies=deps, summary="Mappa di tutte le operazioni fattibili con le loro fasi e le statistiche")
def hq_operations() -> list:
    return hq.operations_catalog()


@router.get("/timeline", dependencies=deps, summary="Timeline degli eventi (filtrabile)")
def hq_timeline(op: Optional[str] = None, project: Optional[str] = None, bando: Optional[str] = None, event_status: Optional[str] = Query(default=None, alias="status"),
                limit: int = Query(default=100, ge=1, le=500), before_id: Optional[int] = None) -> list:
    return events.list_events(op=op, project_id=project, bando_id=bando, status=event_status, limit=limit, before_id=before_id)


@router.get("/runs/{run_id}", dependencies=deps, summary="Esecuzione salvata (richiesta e risposta complete, con la traccia dell'algoritmo)")
def hq_run(run_id: int) -> dict:
    run = hq.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Esecuzione non trovata")
    return run


@router.get("/projects", dependencies=deps, summary="Elenco dei progetti lavorati")
def hq_projects() -> list:
    return hq.projects_index()


@router.get("/projects/{project_id}", dependencies=deps, summary="Fascicolo di un progetto: timeline, esecuzioni, documenti, registrazione")
def hq_project(project_id: str) -> dict:
    return hq.project_dossier(project_id)


@router.get("/bandi/{bando_id}", dependencies=deps, summary="Fascicolo di un bando: regole, requisiti, fonti, progetti che lo hanno usato")
def hq_bando(bando_id: str) -> dict:
    dossier = hq.bando_dossier(bando_id)
    if dossier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bando non trovato")
    return dossier


@router.get("/documents", dependencies=deps, summary="Documenti lavorati (bandi caricati, import, export)")
def hq_documents(kind: Optional[str] = None, limit: int = Query(default=200, ge=1, le=500)) -> list:
    return hq.documents_index(kind, limit)


@router.get("/db/tables", dependencies=deps, summary="Tabelle del database (sola lettura)")
def hq_db_tables() -> list:
    return hq.db_tables()


@router.get("/db/table/{table}", dependencies=deps, summary="Righe di una tabella (sola lettura, paginate)")
def hq_db_rows(table: str, limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)) -> dict:
    try:
        return hq.db_rows(table, limit, offset)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tabella non consultabile") from None
