"""Orchestrazione della Missione Uno: motore deterministico -> Merkle -> renderer con strict grounding."""
from __future__ import annotations

import time
from decimal import Decimal
from typing import Optional

from app.core.deterministic_engine import DeterministicEngine
from app.core.merkle_tree import MerkleTreeEngine
from app.core.renderer import LLMClient, budget_context, render_with_grounding, static_budget_summary
from app.models.schemas import (
    AlgorithmTrace, BudgetValidationRequest, BudgetValidationResponse, ItemValidationStatus, MerkleView, PipelineStage,
    ShareCapInfo,
)


def cep_id_for(merkle_root: str) -> str:
    return "CEP-" + merkle_root.removeprefix("0x")[:16].upper()


def _sum(values) -> Decimal:
    return sum((Decimal(str(v)) for v in values), Decimal("0"))


def validate_budget(request: BudgetValidationRequest, llm: Optional[LLMClient] = None) -> BudgetValidationResponse:
    items, checks, partial = DeterministicEngine.analyze_budget(
        request.cost_items, request.grant_rules, entity_liquidity_eur=request.entity_liquidity_eur, baseline_totals=request.baseline_totals)
    stages = list(partial["stages"])

    t = time.perf_counter()
    leaf_hashes = [i.item_hash_sha256 for i in items]
    levels = MerkleTreeEngine.build_levels(leaf_hashes)
    root = "0x" + MerkleTreeEngine.compute_merkle_root(leaf_hashes)
    stages.append(PipelineStage(key="MERKLE", label="Albero di Merkle e radice", duration_ms=round((time.perf_counter() - t) * 1000, 3),
                                detail=f"{len(leaf_hashes)} foglie · {len(levels)} livelli · radice {root[:14]}…"))

    requested = _sum(i.original_cost_eur for i in items)
    approved = _sum(i.computed_cost_eur for i in items)
    blocked = any(i.status in (ItemValidationStatus.REJECTED, ItemValidationStatus.MISSING_DOCUMENTS) for i in items)
    score = DeterministicEngine.conformity_score(items, checks)

    t = time.perf_counter()
    totals = {
        "bando_id": request.grant_rules.bando_id, "bando_name": request.grant_rules.bando_name,
        "total_requested_eur": float(requested), "total_approved_eur": float(approved),
        "total_rejected_eur": float(requested - approved), "conformity_score": score, "merkle_root": root,
        "items": [{"status": i.status.value} for i in items],
    }
    ctx = budget_context(totals)
    text, source = render_with_grounding(ctx, static_budget_summary(ctx), llm)
    stages.append(PipelineStage(key="EXPLAIN", label="Sintesi testuale con validazione numerica", duration_ms=round((time.perf_counter() - t) * 1000, 3),
                                detail=f"sorgente: {source} (ogni cifra confrontata con il JSON bloccato)"))

    trace = AlgorithmTrace(
        stages=stages, steps=partial["steps"], share_caps=[ShareCapInfo(**c) for c in partial["share_caps"]],
        merkle=MerkleView(leaf_item_ids=[i.item_id for i in items], levels=[[h[:12] for h in lvl] for lvl in levels]),
    )
    return BudgetValidationResponse(
        project_id=request.project_id, bando_id=request.grant_rules.bando_id,
        status="REJECTED_WITH_ERRORS" if blocked else "VALIDATED", conformity_score=score,
        total_requested_eur=float(requested), total_approved_eur=float(approved), total_rejected_eur=float(requested - approved),
        items=items, budget_checks=checks, trace=trace, merkle_root=root, cep_id=cep_id_for(root),
        llm_explanation_summary=text, explanation_source=source,
    )
