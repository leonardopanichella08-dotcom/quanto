"""Orchestrazione della Missione Uno: motore deterministico -> Merkle -> renderer con strict grounding."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.core.deterministic_engine import DeterministicEngine
from app.core.merkle_tree import MerkleTreeEngine
from app.core.renderer import LLMClient, budget_context, render_with_grounding, static_budget_summary
from app.models.schemas import BudgetValidationRequest, BudgetValidationResponse, ItemValidationStatus


def cep_id_for(merkle_root: str) -> str:
    return "CEP-" + merkle_root.removeprefix("0x")[:16].upper()


def _sum(values) -> Decimal:
    return sum((Decimal(str(v)) for v in values), Decimal("0"))


def validate_budget(request: BudgetValidationRequest, llm: Optional[LLMClient] = None) -> BudgetValidationResponse:
    items, checks = DeterministicEngine.evaluate_budget(
        request.cost_items, request.grant_rules, entity_liquidity_eur=request.entity_liquidity_eur, baseline_totals=request.baseline_totals)
    requested = _sum(i.original_cost_eur for i in items)
    approved = _sum(i.computed_cost_eur for i in items)
    root = "0x" + MerkleTreeEngine.compute_merkle_root([i.item_hash_sha256 for i in items])
    blocked = any(i.status in (ItemValidationStatus.REJECTED, ItemValidationStatus.MISSING_DOCUMENTS) for i in items)
    score = DeterministicEngine.conformity_score(items, checks)

    totals = {
        "bando_id": request.grant_rules.bando_id, "bando_name": request.grant_rules.bando_name,
        "total_requested_eur": float(requested), "total_approved_eur": float(approved),
        "total_rejected_eur": float(requested - approved), "conformity_score": score, "merkle_root": root,
        "items": [{"status": i.status.value} for i in items],
    }
    ctx = budget_context(totals)
    text, source = render_with_grounding(ctx, static_budget_summary(ctx), llm)
    return BudgetValidationResponse(
        project_id=request.project_id, bando_id=request.grant_rules.bando_id,
        status="REJECTED_WITH_ERRORS" if blocked else "VALIDATED", conformity_score=score,
        total_requested_eur=float(requested), total_approved_eur=float(approved), total_rejected_eur=float(requested - approved),
        items=items, budget_checks=checks, merkle_root=root, cep_id=cep_id_for(root),
        llm_explanation_summary=text, explanation_source=source,
    )
