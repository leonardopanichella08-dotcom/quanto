"""I lavori dello studio: un'azienda cliente per lavoro, con profilo, bilanci, documenti e risultati salvati."""
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import actor_of, scope_of
from app.core import clients

router = APIRouter()


class ClientBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=200)
    note: str = Field(default="", max_length=500)


class ClientPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, max_length=200)
    note: Optional[str] = Field(default=None, max_length=500)


class StateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: Any


def _guard(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except clients.ClientError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lavoro non trovato") from None


@router.get("", summary="I lavori dello studio, con lo stato di ciascuno")
def list_all(request: Request) -> list:
    return clients.list_clients(actor_of(request))


@router.post("", status_code=status.HTTP_201_CREATED, summary="Apre un nuovo lavoro (un'azienda cliente)")
def create(body: ClientBody, request: Request) -> dict:
    return _guard(clients.create_client, actor_of(request), body.name, body.note)


@router.patch("/{client_id}", summary="Rinomina un lavoro o cambia la nota")
def patch(client_id: int, body: ClientPatch, request: Request) -> dict:
    return _guard(clients.update_client, actor_of(request), client_id, body.name, body.note)


@router.delete("/{client_id}", summary="Elimina un lavoro con tutti i suoi dati (si riscrive il nome per confermare)")
def delete(client_id: int, confirm: str, request: Request) -> dict:
    return {"deleted": _guard(clients.delete_client, actor_of(request), client_id, confirm)}


@router.get("/current/state/{key}", summary="Scelte e risultati salvati per il lavoro attivo (allocazione, budget, confronto)")
def get_state(key: str, request: Request) -> dict:
    sc = scope_of(request)
    if "#" not in sc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Scegli prima un lavoro")
    return _guard(clients.get_state, sc, key) or {"value": None, "updated_at": None}


@router.put("/current/state/{key}", summary="Salva scelte e risultati per il lavoro attivo")
def put_state(key: str, body: StateBody, request: Request) -> dict:
    sc = scope_of(request)
    if "#" not in sc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Scegli prima un lavoro")
    return _guard(clients.put_state, sc, key, body.value)
