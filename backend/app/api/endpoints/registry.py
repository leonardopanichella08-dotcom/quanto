"""Registro di asseverazione (catena di hash firmata) e Auditor Portal."""
import logging
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.deps import actor_of, auditor_engine, require_auth
from app.core import events, merkle_lab, webhooks
from app.core.budget_service import cep_id_for
from app.core.registry import (AlreadyRegisteredError, Registry, attestation_dict, current_public_key, project_key,
                               trusted_public_keys, verify_attestation)
from app.models.schemas import (AuditRecomputeRequest, AuditVerificationResponse, ChainStatusResponse, RegistrationRequest,
                                RegistrationResponse)

router = APIRouter()
logger = logging.getLogger("quanto.registry")

ROOT_PATTERN = r"^(0x)?[0-9a-fA-F]{64}$"


def _log_verify(op: str, res: AuditVerificationResponse, http: Request, timer) -> None:
    verdict = "VALIDO e inalterato" if res.is_valid_and_unaltered else ("NON registrato" if not res.registration_found else "NON valido")
    events.record(op, f"Verifica: {verdict}" + (" (ricalcolo dai dati)" if res.recomputed_from_data else ""),
                  status="OK" if res.is_valid_and_unaltered else ("NOT_FOUND" if not res.registration_found else "FAIL"),
                  project_id=res.project_id, actor=actor_of(http), duration_ms=timer.ms,
                  details={"valid": res.is_valid_and_unaltered, "signature_valid": res.signature_valid, "chain_intact": res.chain_intact,
                           "recomputed": res.recomputed_from_data, "provided_root": res.provided_merkle_root, "registered_root": res.registered_merkle_root})


def _response(project_id: str, att) -> RegistrationResponse:
    return RegistrationResponse(
        project_id=project_id, cep_id=cep_id_for(att.merkle_root), merkle_root="0x" + att.merkle_root, seq=att.seq,
        registered_at=att.registered_at, prev_hash=att.prev_hash, entry_hash=att.entry_hash, key_id=att.key_id,
        public_key=att.public_key, signature=att.signature, project_key=att.project_key)


@router.get("/status", response_model=ChainStatusResponse, summary="Integrità della catena del registro e chiave di firma attiva")
def registry_status() -> ChainStatusResponse:
    chain, key = Registry.verify_chain(), current_public_key()
    return ChainStatusResponse(intact=chain.intact, entries=chain.entries, head_hash=chain.head_hash, broken_at_seq=chain.broken_at_seq,
                               reason=chain.reason, key_id=key["key_id"], public_key=key["public_key"], is_dev_key=key["is_dev_key"])


class MerkleLabRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rows: List[str] = Field(..., min_length=1, max_length=merkle_lab.MAX_ROWS, description="Testi delle righe (l'impronta di riga è lo SHA-256 del testo)")
    prove_index: Optional[int] = Field(None, ge=0, description="Riga di cui mostrare la prova di inclusione")

    @field_validator("rows")
    @classmethod
    def _rows_ok(cls, v: List[str]) -> List[str]:
        if any(not r.strip() or len(r) > 200 for r in v):
            raise ValueError("ogni riga deve avere da 1 a 200 caratteri")
        return v


@router.post("/merkle-lab", summary="Didattica: calcola la Merkle Root passo passo su righe di esempio (stesso algoritmo del sistema)")
def merkle_lab_endpoint(request: MerkleLabRequest) -> dict:
    try:
        return merkle_lab.explain(request.rows, request.prove_index)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.get("/public-key",summary="Chiave pubblica Ed25519 di firma (radice di fiducia: da fissare fuori banda)")
def public_key() -> dict:
    return current_public_key()


@router.post("/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_auth)], summary="Registra la Merkle Root di un budget nel registro firmato")
def register_merkle_root(request: RegistrationRequest, background: BackgroundTasks, http: Request) -> RegistrationResponse:
    timer = events.Timer()
    try:
        att = Registry.register(request.project_id, request.merkle_root)
    except AlreadyRegisteredError as exc:
        events.record("registry.register", "Registrazione respinta: progetto già registrato" + (" (stessa radice)" if exc.same_root else " con radice diversa"),
                      status="CONFLICT", project_id=request.project_id, actor=actor_of(http), duration_ms=timer.ms, details={"same_root": exc.same_root})
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
            "message": "Budget già registrato per questo progetto", "already_registered": True,
            "same_root": exc.same_root, "existing_merkle_root": "0x" + exc.existing_root}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    events.record("registry.register", f"Registrata la radice {att.merkle_root[:14]}… come voce n. {att.seq}", project_id=request.project_id,
                  actor=actor_of(http), duration_ms=timer.ms,
                  details={"seq": att.seq, "merkle_root": "0x" + att.merkle_root, "entry_hash": att.entry_hash, "prev_hash": att.prev_hash, "key_id": att.key_id})
    background.add_task(webhooks.emit, "event.budget.registered", {"project_key": att.project_key, "merkle_root": "0x" + att.merkle_root, "seq": att.seq})
    return _response(request.project_id, att)


@router.get("/attestation/{project_id}", response_model=RegistrationResponse, summary="Attestazione firmata di un progetto registrato")
def get_attestation(project_id: str) -> RegistrationResponse:
    att = Registry.lookup(project_id)
    if att is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nessuna registrazione per questo progetto")
    return _response(project_id, att)


@router.get("/verify/{project_id}", response_model=AuditVerificationResponse, summary="Verifica una Merkle Root contro il registro (Auditor Portal)")
def verify_root(project_id: str, http: Request, merkle_root: str = Query(..., pattern=ROOT_PATTERN)) -> AuditVerificationResponse:
    timer = events.Timer()
    res = auditor_engine.verify_root(project_id, merkle_root)
    _log_verify("registry.verify_root", res, http, timer)
    return res


@router.post("/verify/recompute", response_model=AuditVerificationResponse, summary="Ricalcola la Merkle Root dai dati originali e la verifica")
def verify_from_original_data(request: AuditRecomputeRequest, http: Request) -> AuditVerificationResponse:
    timer = events.Timer()
    if not request.cost_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nessuna riga di costo da ricalcolare.")
    res = auditor_engine.verify_from_data(request.project_id, request.cost_items, request.grant_rules,
                                          entity_liquidity_eur=request.entity_liquidity_eur, baseline_totals=request.baseline_totals,
                                          reference_date=request.reference_date)
    _log_verify("registry.verify_recompute", res, http, timer)
    return res


@router.post("/verify/attestation", summary="Verifica OFFLINE di un'attestazione con la sola chiave pubblica di fiducia")
def verify_attestation_offline(http: Request, attestation: dict = Body(...)) -> dict:
    timer = events.Timer()
    valid = verify_attestation({k: attestation.get(k) for k in ("seq", "project_key", "merkle_root", "registered_at", "prev_hash", "key_id", "entry_hash", "public_key", "signature")}
                               | {"merkle_root": str(attestation.get("merkle_root", "")).removeprefix("0x")}, trusted_public_keys())
    events.record("registry.verify_attestation", "Attestazione " + ("valida" if valid else "NON valida"), status="OK" if valid else "FAIL",
                  actor=actor_of(http), duration_ms=timer.ms, details={"valid": valid})
    return {"valid": valid, "trusted_key_ids": [current_public_key()["key_id"]]}
