"""Traccia dell'algoritmo, copertura dei 60 criteri dallo scenario demo e nuove regole di bando."""
import pytest
from pydantic import ValidationError

from app.core.budget_service import validate_budget
from app.core.demo import SANDBOX_ID, SANDBOX_RULES, build_demo
from app.core.deterministic_engine import DeterministicEngine as E
from app.core.field_catalog import FIELDS, assert_complete, coerce_value
from app.core.merkle_tree import MerkleTreeEngine as M
from app.models.schemas import BudgetValidationRequest, CostItemInput, GrantRuleSet, ItemValidationStatus as S
from tests.conftest import personnel
from tests.test_criteria import R, X, budget, run


def demo_result(mode="stress", rules=None):
    return validate_budget(BudgetValidationRequest.model_validate(build_demo(rules, mode=mode)))


# ------------------------------------------------------------------ scenario demo
def test_stress_demo_exercises_all_60_criteria_with_46_lines():
    res = demo_result()
    assert len(res.items) == 46
    evaluated = set()
    for i in res.items:
        evaluated |= set(i.criteria_checked)
    evaluated |= {c.criterion for c in res.budget_checks if c.status != "NOT_EVALUATED"}
    assert evaluated == set(range(1, 61)), f"criteri non esercitati: {sorted(set(range(1, 61)) - evaluated)}"


def test_stress_demo_covers_every_category_and_every_outcome():
    res = demo_result()
    assert {i.category.value for i in res.items} == {"PERSONNEL", "CAPITAL_ASSETS", "CONSULTING", "OVERHEAD", "TRAINING"}
    assert {i.status for i in res.items} == {S.APPROVED, S.CAP_EXCEEDED_ADJUSTED, S.REJECTED, S.MISSING_DOCUMENTS}


def test_realistic_demo_is_mostly_valid_and_respects_bando_categories():
    res = demo_result("realistic")
    assert len(res.items) == 15 and sum(1 for i in res.items if i.status == S.REJECTED) <= 1
    only_assets = GrantRuleSet(bando_id="B", bando_name="B", rule_version_hash="abcdefgh", eligible_categories=["CAPITAL_ASSETS"])
    assets_res = demo_result("realistic", only_assets)
    assert {i.category.value for i in assets_res.items} == {"CAPITAL_ASSETS"}


def test_demo_dates_follow_the_bando_window():
    window = GrantRuleSet(bando_id="B", bando_name="B", rule_version_hash="abcdefgh", eligibility_start="2030-01-01", eligibility_end="2030-12-31", requires_cup=False)
    res = demo_result("stress", window)
    t03 = next(i for i in res.items if i.item_id == "T-03")
    assert t03.status == S.REJECTED and 46 in t03.criteria_failed          # la data «fuori finestra» è fuori dalla finestra DEL BANDO
    assert 46 in next(i for i in res.items if i.item_id == "P-01").criteria_checked and 46 not in next(i for i in res.items if i.item_id == "P-01").criteria_failed


def test_field_catalog_matches_the_model_exactly():
    assert_complete()
    assert {f["name"] for f in FIELDS} == set(CostItemInput.model_fields)
    assert coerce_value({"type": "bool"}, "sì") is True and coerce_value({"type": "number"}, "1.234,50") == 1234.5
    assert coerce_value({"type": "list"}, "A, B") == ["A", "B"] and coerce_value({"type": "text"}, "  ") is None


# ------------------------------------------------------------------ traccia
def test_trace_steps_reconstruct_every_amount():
    res = demo_result()
    by_item = {}
    for st in res.trace.steps:
        by_item.setdefault(st.item_id, []).append(st)
    for item in res.items:
        steps = by_item[item.item_id]
        deltas = round(sum(s.delta_eur for s in steps), 2)
        assert round(item.original_cost_eur + deltas, 2) == item.computed_cost_eur, item.item_id     # originale + delta = ammesso
        assert steps[-1].amount_after_eur == item.computed_cost_eur
        assert {s.criterion for s in steps} >= set(item.criteria_checked)
    assert [s.seq for s in res.trace.steps] == list(range(1, len(res.trace.steps) + 1))


def test_trace_outcomes_match_item_status():
    res = demo_result()
    steps = [s for s in res.trace.steps if s.item_id == "P-04"]
    assert any(s.outcome == "REJECTED" and s.criterion == 10 for s in steps)
    a09 = [s for s in res.trace.steps if s.item_id == "A-09"]
    assert any(s.outcome == "SUSPENDED" for s in a09) or any(s.outcome == "REJECTED" for s in a09)
    assert all(s.outcome in ("PASS", "ADJUSTED", "REJECTED", "SUSPENDED") for s in res.trace.steps)


def test_pipeline_stages_are_reported_in_order():
    res = demo_result()
    assert [s.key for s in res.trace.stages] == ["LINE_CRITERIA", "FTE", "SHARE_CAPS", "BUDGET_CHECKS", "HASH", "MERKLE", "EXPLAIN"]
    assert all(s.duration_ms >= 0 and s.detail for s in res.trace.stages)


def test_share_cap_info_is_consistent_with_the_solution():
    res = demo_result()
    caps = {c.group: c for c in res.trace.share_caps}
    assert set(caps) >= {"CONSULTING", "OVERHEAD", "COMMUNICATION", "IMMATERIAL"}
    for c in caps.values():
        assert c.allowed_eur <= c.requested_eur and c.allowed_eur <= c.cap_pct * c.total_final_eur + 0.01


def test_merkle_view_matches_the_root():
    res = demo_result("realistic")
    levels = res.trace.merkle.levels
    assert len(levels[0]) == len(res.items) == len(res.trace.merkle.leaf_item_ids)
    assert len(levels[-1]) == 1 and res.merkle_root.removeprefix("0x").startswith(levels[-1][0])
    full = M.build_levels([i.item_hash_sha256 for i in res.items])
    assert full[-1][0] == res.merkle_root.removeprefix("0x")


def test_merkle_levels_edge_cases():
    assert len(M.build_levels(["ab" * 32])) == 1
    assert [len(l) for l in M.build_levels(["cd" * 32] * 5)] == [5, 3, 2, 1]        # nodo dispari promosso


# ------------------------------------------------------------------ regole assenti = criteri non valutati
def test_absent_bando_rules_are_not_invented():
    bare = GrantRuleSet(bando_id="B", bando_name="B", rule_version_hash="abcdefgh")
    assert bare.max_hourly_rate_personnel is None and bare.max_consulting_percentage is None and bare.max_overhead_percentage is None
    r = run(personnel(ral=58000.0, fte=0.8, ccnl="METALMECCANICA", level="5"), bare)
    assert r.status == S.APPROVED and r.hourly_rate_cap == 0.0 and 7 not in r.criteria_checked and 7 in r.criteria_not_evaluated
    res, _ = budget([personnel("P", ral=30000.0, fte=1.0), X("CONSULTING", 500000.0, "C")], bare)
    assert res[1].status == S.APPROVED and res[1].computed_cost_eur == 500000.0     # nessun massimale consulenze nel bando


def test_unknown_fields_are_rejected_not_ignored():
    with pytest.raises(ValidationError):
        GrantRuleSet(bando_id="B", bando_name="B", rule_version_hash="abcdefgh", max_hourly_rate="35")      # refuso
    with pytest.raises(ValidationError):
        CostItemInput(item_id="X", description="d", category="CONSULTING", source_c_ref="D", amount_eur=1, importo=2)


# ------------------------------------------------------------------ nuove regole
def test_category_not_eligible_is_rejected_with_reason():
    rules = R(eligible_categories=["CAPITAL_ASSETS"])
    r = run(personnel(), rules)
    assert r.status == S.REJECTED and 16 in r.criteria_failed and "non è ammissibile" in r.rejection_reason
    assert run(X(), rules).status == S.APPROVED


def test_excluded_asset_nature_and_financial_charges():
    assert run(X(asset_nature="REAL_ESTATE"), R(excluded_asset_natures=["REAL_ESTATE"])).status == S.REJECTED
    assert run(X(asset_nature="REAL_ESTATE")).status == S.APPROVED
    assert run(X("OVERHEAD", expense_subtype="FINANCIAL_CHARGES")).status == S.REJECTED


def test_depreciation_only_requires_a_rate():
    rules = R(equipment_depreciation_only=True)
    assert run(X(), rules).status == S.MISSING_DOCUMENTS
    ok = run(X(depreciation_rate_pct=0.2, duration_months=12), rules)
    assert ok.status == S.CAP_EXCEEDED_ADJUSTED and ok.computed_cost_eur == 2000.0          # 20% x 12/12


def test_eu_origin_requirement():
    rules = R(requires_eu_origin=True)
    assert run(X(origin_eu=False), rules).status == S.REJECTED
    assert run(X(origin_eu=True), rules).status == S.APPROVED
    assert run(X(origin_eu=False)).status == S.APPROVED


def test_vat_never_eligible_by_bando():
    r = run(X(vat_eur=2200.0, vat_recoverable=False), R(vat_never_eligible=True))
    assert (r.original_cost_eur, r.computed_cost_eur) == (12200.0, 10000.0) and 54 in r.criteria_failed


def test_appraisal_threshold_zero_means_always_required():
    rules = R(appraisal_threshold_eur=0)
    assert run(X(amount=10.0, sworn_appraisal_present=False), rules).status == S.MISSING_DOCUMENTS
    assert run(X(amount=10.0, sworn_appraisal_present=True), rules).status == S.APPROVED


def test_flat_rate_on_direct_costs_excludes_subcontracting():
    """Horizon Europe: 25% dei costi diretti, esclusi i subappalti."""
    rules = GrantRuleSet(bando_id="HE", bando_name="HE", rule_version_hash="abcdefgh", overhead_flat_rate_pct=0.25,
                         overhead_flat_base="DIRECT_EXCL_SUBCONTRACTING", subcontracting_allowed=True)
    items = [personnel("P", ral=30000.0, fte=1.0),                                   # 41.499,00
             X("CONSULTING", 20000.0, "SUB", subcontracted=True, subcontract_authorized=True),
             X("OVERHEAD", 50000.0, "O")]
    res, _ = budget(items, rules)
    assert res[2].computed_cost_eur == 10374.75 and 36 in res[2].criteria_failed     # 25% x 41.499 (il subappalto non fa base)
    assert res[1].computed_cost_eur == 20000.0


def test_flat_rate_base_personnel_vs_direct():
    p = personnel("P", ral=30000.0, fte=1.0)
    asset = X("CAPITAL_ASSETS", 100000.0, "A")
    over = X("OVERHEAD", 90000.0, "O")
    def rules(base):
        return GrantRuleSet(bando_id="B", bando_name="B", rule_version_hash="abcdefgh", overhead_flat_rate_pct=0.15, overhead_flat_base=base)

    only_pers, _ = budget([p, asset, over], rules("PERSONNEL"))
    direct, _ = budget([p, asset, over], rules("DIRECT_EXCL_SUBCONTRACTING"))
    assert only_pers[2].computed_cost_eur == 6224.85 and direct[2].computed_cost_eur == 21224.85      # 15% di 41.499 / di 141.499


def test_sandbox_rules_are_a_valid_rule_set():
    assert GrantRuleSet.model_validate(SANDBOX_RULES).bando_id == SANDBOX_ID
