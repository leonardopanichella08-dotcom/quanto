"""Quartier Generale: accesso con codice manager, consultazione di timeline/dossier/documenti/database e gestione dei dati (archivio bandi, file originali,
regole, requisiti, eliminazioni). Tutto tranne il registro firmato, che è append-only."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import actor_of, require_hq
from app.core import analysis, archive, consultant, events, hq
from app.core.ingestion import Ingestion

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


# ------------------------------------------------------------------ archivio bandi: vedere, correggere, eliminare
class RuleValue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: object


class RequirementIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic: str = Field(..., min_length=2, max_length=120)
    kind: str = Field(..., pattern=r"^(OBBLIGO|DIVIETO|LIMITE|INFO|DA_REVISIONARE)$")
    text: str = Field(..., min_length=5, max_length=2000)
    criteria: List[int] = Field(default_factory=list, max_length=60)


class RequirementPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Optional[str] = Field(default=None, pattern=r"^(OBBLIGO|DIVIETO|LIMITE|INFO|DA_REVISIONARE)$")
    topic: Optional[str] = Field(default=None, max_length=120)
    criteria: Optional[List[int]] = Field(default=None, max_length=60)


class RenameIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=3, max_length=200)


def _log(op: str, summary: str, request: Request, bando_id: Optional[str] = None, details: Optional[dict] = None) -> None:
    events.record(op, summary, bando_id=bando_id, actor=actor_of(request), details=details)


@router.get("/archive", dependencies=deps, summary="Tutti i bandi in memoria (predefiniti, dal web, caricati) con contatori")
def archive_list() -> dict:
    return {"bandi": archive.list_archive(), "deleted_defaults": archive.tombstones()}


@router.get("/archive/{bando_id}", dependencies=deps, summary="Tutto di un bando: regole (anche in disaccordo), requisiti, fonti e file originali")
def archive_detail(bando_id: str) -> dict:
    d = archive.bando_archive(bando_id)
    if d is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bando non trovato")
    return d


@router.get("/archive/{bando_id}/consultant", dependencies=deps, summary="Scheda per il consulente: cosa dicono i documenti, cosa non dicono, cosa cercare e come verificare")
def archive_consultant(bando_id: str) -> dict:
    s = consultant.consultant_sheet(bando_id)
    if s is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bando non trovato")
    return s


@router.get("/archive/{bando_id}/sources/{sha256}/text", dependencies=deps, summary="Testo estratto di un documento")
def archive_source_text(bando_id: str, sha256: str) -> dict:
    for s in events.list_bando_sources(bando_id):
        if s["sha256"] == sha256:
            return {"name": s["name"], "url": s.get("url"), "tier": s.get("tier"), "pages": s.get("pages"), "chars": len(s["text"]), "ts": s["ts"], "text": s["text"]}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fonte non trovata")


@router.get("/archive/{bando_id}/sources/{sha256}/file", dependencies=deps, summary="File originale del documento (PDF, pagina, Word) così come è stato scaricato")
def archive_source_file(bando_id: str, sha256: str, download: bool = False) -> Response:
    src = next((s for s in events.list_bando_sources(bando_id) if s["sha256"] == sha256), None)
    f = events.get_bando_file(bando_id, src["file_sha256"]) if src and src.get("file_sha256") else None
    if f is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File originale non conservato per questo documento")
    name = "".join(c if c.isalnum() or c in "._- " else "_" for c in f["name"])[:100] or "documento"
    ctype = f.get("content_type") or "application/octet-stream"
    if ctype.startswith("text/html"):
        ctype = "text/plain; charset=utf-8"   # una pagina scaricata si mostra come testo: non si esegue nel browser del manager
    disp = "attachment" if download else "inline"
    return Response(content=f["data"], media_type=ctype, headers={"Content-Disposition": f'{disp}; filename="{name}"', "X-Content-Type-Options": "nosniff"})


@router.delete("/archive/{bando_id}/sources/{sha256}", dependencies=deps, summary="Elimina un documento (testo e file originale) dalla memoria del bando")
def archive_delete_source(bando_id: str, sha256: str, request: Request) -> dict:
    if not archive.delete_source(bando_id, sha256):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fonte non trovata")
    _log("hq.bando.source.delete", f"Documento eliminato dal bando {bando_id}", request, bando_id, {"sha256": sha256})
    return {"deleted": True}


@router.post("/archive/{bando_id}/reanalyze", dependencies=deps, summary="Rilegge tutti i documenti in memoria (ricalcola regole automatiche e requisiti)")
def archive_reanalyze(bando_id: str, request: Request) -> dict:
    if Ingestion.get_bando(bando_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bando non trovato")
    if not events.list_bando_sources(bando_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nessun documento in memoria da analizzare")
    res = analysis.run_analysis(bando_id)
    _log("bando.research.analyze", f"Rilettura del manager: {len(res['requirements'])} requisiti da {res['sources']} fonti", request, bando_id,
         {"requirements": len(res["requirements"]), "report": res["report"]})
    return {"requirements": len(res["requirements"]), "rules_published": res["outcome"].published, "sources_report": res["report"]}


@router.put("/archive/{bando_id}/rules/{key}", dependencies=deps, summary="Imposta o corregge una regola (decisione del manager)")
def archive_set_rule(bando_id: str, key: str, body: RuleValue, request: Request) -> dict:
    try:
        v = archive.set_rule(bando_id, key, body.value)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bando non trovato") from None
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    _log("hq.bando.rule.set", f"Regola {key} = {v} nel bando {bando_id}", request, bando_id, {"rule": key, "value": v})
    return {"rule": key, "value": v}


@router.delete("/archive/{bando_id}/rules/{key}", dependencies=deps, summary="Elimina una regola")
def archive_delete_rule(bando_id: str, key: str, request: Request) -> dict:
    if not archive.delete_rule(bando_id, key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regola non trovata")
    _log("hq.bando.rule.delete", f"Regola {key} eliminata dal bando {bando_id}", request, bando_id)
    return {"deleted": True}


@router.post("/archive/{bando_id}/requirements", dependencies=deps, status_code=status.HTTP_201_CREATED, summary="Aggiunge un requisito a mano")
def archive_add_requirement(bando_id: str, body: RequirementIn, request: Request) -> dict:
    if Ingestion.get_bando(bando_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bando non trovato")
    seq = archive.add_requirement(bando_id, body.topic, body.kind, body.text, body.criteria)
    _log("hq.bando.requirement.add", f"Requisito aggiunto al bando {bando_id}", request, bando_id, {"seq": seq})
    return {"seq": seq}


@router.patch("/archive/{bando_id}/requirements/{seq}", dependencies=deps, summary="Riclassifica un requisito (tipo, tema, controlli collegati)")
def archive_patch_requirement(bando_id: str, seq: int, body: RequirementPatch, request: Request) -> dict:
    if not archive.update_requirement(bando_id, seq, body.kind, body.topic, body.criteria):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requisito non trovato")
    _log("hq.bando.requirement.update", f"Requisito {seq} riclassificato nel bando {bando_id}", request, bando_id)
    return {"updated": True}


@router.delete("/archive/{bando_id}/requirements/{seq}", dependencies=deps, summary="Elimina un requisito")
def archive_delete_requirement(bando_id: str, seq: int, request: Request) -> dict:
    if not archive.delete_requirement(bando_id, seq):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requisito non trovato")
    _log("hq.bando.requirement.delete", f"Requisito {seq} eliminato dal bando {bando_id}", request, bando_id)
    return {"deleted": True}


@router.patch("/archive/{bando_id}", dependencies=deps, summary="Rinomina il bando")
def archive_rename(bando_id: str, body: RenameIn, request: Request) -> dict:
    if not archive.rename_bando(bando_id, body.name):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bando non trovato")
    _log("hq.bando.rename", f"Bando {bando_id} rinominato «{body.name}»", request, bando_id)
    return {"renamed": True}


@router.delete("/archive/{bando_id}", dependencies=deps, summary="Elimina il bando con tutti i suoi documenti, file, regole e requisiti")
def archive_delete(bando_id: str, request: Request) -> dict:
    counts = archive.delete_bando(bando_id)
    if counts is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bando non trovato")
    _log("hq.bando.delete", f"Bando {bando_id} eliminato ({counts['bando_sources']} documenti, {counts['rules']} regole, {counts['requirements']} requisiti)", request, bando_id, counts)
    return {"deleted": True, "removed": counts}


@router.post("/archive/restore-defaults", dependencies=deps, summary="Ripristina i bandi predefiniti eliminati")
def archive_restore(request: Request) -> dict:
    n = archive.restore_defaults()
    _log("hq.bando.restore", f"Ripristinati {n} bandi predefiniti", request)
    return {"restored": n}


@router.get("/archive/{bando_id}/export.zip", dependencies=deps, summary="Scarica tutto il bando: scheda JSON, testi e file originali")
def archive_export(bando_id: str) -> Response:
    data = archive.export_zip(bando_id)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bando non trovato")
    return Response(content=data, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{bando_id}.zip"'})


# ------------------------------------------------------------------ database: correzione dei dati (non del registro firmato)
@router.delete("/db/table/{table}/row/{rowid}", dependencies=deps, summary="Elimina una riga (tranne il registro firmato)")
def db_delete_row(table: str, rowid: int, request: Request) -> dict:
    try:
        ok = archive.db_delete_row(table, rowid)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tabella non consultabile") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Riga non trovata")
    _log("hq.db.delete_row", f"Riga {rowid} eliminata dalla tabella {table}", request, None, {"table": table, "rowid": rowid})
    return {"deleted": True}


@router.delete("/db/table/{table}", dependencies=deps, summary="Svuota una tabella (serve confirm=<nome tabella>); il registro firmato è escluso")
def db_clear(table: str, request: Request, confirm: str = Query(default="")) -> dict:
    if confirm != table:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Per svuotare la tabella passa confirm=<nome della tabella>")
    try:
        n = archive.db_clear_table(table)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tabella non consultabile") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    _log("hq.db.clear", f"Tabella {table} svuotata ({n} righe)", request, None, {"table": table, "rows": n})
    return {"deleted_rows": n}


@router.get("/db/table/{table}/export.csv", dependencies=deps, summary="Esporta una tabella in CSV (testi completi, file come dimensione)")
def db_export(table: str) -> Response:
    try:
        data = archive.db_export_csv(table)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tabella non consultabile") from None
    return Response(content=data.encode("utf-8-sig"), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{table}.csv"'})
