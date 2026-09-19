"""Motore di asseverazione crittografica per l'Auditor Portal.

Due percorsi, entrambi con lettura REALE del registro append-only:
- ``verify_root``: l'auditor presenta una Merkle Root (es. dal QR del documento) e la si confronta;
- ``verify_from_data``: l'auditor fornisce i dati di costo originali; la radice viene ricalcolata in locale con
  lo stesso motore deterministico e poi confrontata.

Un budget è "valido e inalterato" solo se: il progetto è registrato, la radice coincide, la firma della voce è
valida e l'INTERA catena del registro è integra. Un progetto non registrato non è mai valido.
"""
from __future__ import annotations

import time
from typing import Dict, List, Optional

from app.core.deterministic_engine import DeterministicEngine
from app.core.merkle_tree import MerkleTreeEngine, normalize_root
from app.core.registry import Registry, attestation_dict, verify_attestation
from app.models.schemas import AuditVerificationResponse, CostCategory, CostItemInput, GrantRuleSet


class AuditorVerificationEngine:
    def _compare(self, project_id: str, provided_root: str, recomputed: bool, started: float) -> AuditVerificationResponse:
        provided = normalize_root(provided_root)
        att = Registry.lookup(project_id)
        chain = Registry.verify_chain()
        signature_ok = bool(att and verify_attestation(attestation_dict(att)))
        return AuditVerificationResponse(
            project_id=project_id,
            provided_merkle_root="0x" + provided,
            registered_merkle_root=("0x" + att.merkle_root) if att else "",
            registration_found=att is not None,
            is_valid_and_unaltered=bool(att and att.merkle_root == provided and signature_ok and chain.intact),
            signature_valid=signature_ok,
            chain_intact=chain.intact,
            chain_entries=chain.entries,
            registered_at=att.registered_at if att else None,
            seq=att.seq if att else None,
            entry_hash=att.entry_hash if att else None,
            key_id=att.key_id if att else None,
            recomputed_from_data=recomputed,
            verification_time_seconds=round(time.perf_counter() - started, 3),
        )

    def verify_root(self, project_id: str, merkle_root: str) -> AuditVerificationResponse:
        return self._compare(project_id, merkle_root, recomputed=False, started=time.perf_counter())

    def verify_from_data(self, project_id: str, cost_items: List[CostItemInput], grant_rules: GrantRuleSet,
                         entity_liquidity_eur: Optional[float] = None,
                         baseline_totals: Optional[Dict[CostCategory, float]] = None) -> AuditVerificationResponse:
        started = time.perf_counter()
        validated = DeterministicEngine.validate_budget(cost_items, grant_rules, entity_liquidity_eur=entity_liquidity_eur,
                                                        baseline_totals=baseline_totals)
        root = MerkleTreeEngine.compute_merkle_root([v.item_hash_sha256 for v in validated])
        return self._compare(project_id, root, recomputed=True, started=started)
