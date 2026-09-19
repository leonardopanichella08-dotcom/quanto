"""Registro di asseverazione (catena di hash firmata) e Auditor Portal."""
import logging

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query, status

from app.api.deps import auditor_engine, require_auth
from app.core import webhooks
from app.core.budget_service import cep_id_for
from app.core.registry import (AlreadyRegisteredError, Registry, attestation_dict, current_public_key, project_key,
                               trusted_public_keys, verify_attestation)
from app.models.schemas import (AuditRecomputeRequest, AuditVerificationResponse, ChainStatusResponse, RegistrationRequest,
                                RegistrationResponse)

router = APIRouter()
logger = logging.getLogger("quanto.registry")

ROOT_PATTERN = r"^(0x)?[0-9a-fA-F]{64}$"


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


@router.get("/public-key", summary="Chiave pubblica Ed25519 di firma (radice di fiducia: da fissare fuori banda)")
def public_key() -> dict:
    return current_public_key()


@router.post("/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_auth)], summary="Registra la Merkle Root di un budget nel registro firmato")
def register_merkle_root(request: RegistrationRequest, background: BackgroundTasks) -> RegistrationResponse:
    try:
        att = Registry.register(request.project_id, request.merkle_root)
    except AlreadyRegisteredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
            "message": "Budget già registrato per questo progetto", "already_registered": True,
            "same_root": exc.same_root, "existing_merkle_root": "0x" + exc.existing_root}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    background.add_task(webhooks.emit, "event.budget.registered", {"project_key": att.project_key, "merkle_root": "0x" + att.merkle_root, "seq": att.seq})
    return _response(request.project_id, att)


@router.get("/attestation/{project_id}", response_model=RegistrationResponse, summary="Attestazione firmata di un progetto registrato")
def get_attestation(project_id: str) -> RegistrationResponse:
    att = Registry.lookup(project_id)
    if att is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nessuna registrazione per questo progetto")
    return _response(project_id, att)


@router.get("/verify/{project_id}", response_model=AuditVerificationResponse, summary="Verifica una Merkle Root contro il registro (Auditor Portal)")
def verify_root(project_id: str, merkle_root: str = Query(..., pattern=ROOT_PATTERN)) -> AuditVerificationResponse:
    return auditor_engine.verify_root(project_id, merkle_root)


@router.post("/verify/recompute", response_model=AuditVerificationResponse, summary="Ricalcola la Merkle Root dai dati originali e la verifica")
def verify_from_original_data(request: AuditRecomputeRequest) -> AuditVerificationResponse:
    if not request.cost_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nessuna riga di costo da ricalcolare.")
    return auditor_engine.verify_from_data(request.project_id, request.cost_items, request.grant_rules,
                                           entity_liquidity_eur=request.entity_liquidity_eur, baseline_totals=request.baseline_totals)


@router.post("/verify/attestation", summary="Verifica OFFLINE di un'attestazione con la sola chiave pubblica di fiducia")
def verify_attestation_offline(attestation: dict = Body(...)) -> dict:
    valid = verify_attestation({k: attestation.get(k) for k in ("seq", "project_key", "merkle_root", "registered_at", "prev_hash", "key_id", "entry_hash", "public_key", "signature")}
                               | {"merkle_root": str(attestation.get("merkle_root", "")).removeprefix("0x")}, trusted_public_keys())
    return {"valid": valid, "trusted_key_ids": [current_public_key()["key_id"]]}
