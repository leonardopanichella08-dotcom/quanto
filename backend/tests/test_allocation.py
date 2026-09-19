from decimal import Decimal

import pytest

from app.core.allocation_engine import AllocationOptimizerEngine as A
from app.models.allocation import AllocationOptimizationRequest as Req


def req(expenses, funds, **kw):
    return Req.model_validate({"historical_expenses": expenses, "available_funding_lines": funds, **kw})


def exp(item_id, cat, amount, month=None):
    return {"item_id": item_id, "category": cat, "amount_eur": amount, **({"month": month} if month else {})}


def fund(fund_id, cats, cov=0.8, **kw):
    return {"fund_id": fund_id, "allowed_categories": cats, "coverage_pct": cov, **kw}


def dec(x):
    return Decimal(str(x))


def test_picks_best_intensity_not_first_match():
    """La bozza greedy avrebbe scelto il primo fondo compatibile (50%); l'ottimo è il fondo all'80%."""
    r = A.optimize_annual_allocation(req([exp("E1", "PERSONNEL", 100000)],
                                         [fund("LOW", ["PERSONNEL"], 0.5, excludes=["HIGH"]), fund("HIGH", ["PERSONNEL"], 0.8)]))
    assert r.covered_by_public_funds_eur == 80000.0 and r.net_cost_to_entity_eur == 20000.0
    assert r.allocation_plan[0].assigned_fund == "HIGH"


def test_fund_cap_is_respected_and_leftover_goes_to_next_fund():
    r = A.optimize_annual_allocation(req(
        [exp("E1", "PERSONNEL", 100000)],
        [fund("BIG", ["PERSONNEL"], 0.8, max_total_eur=30000), fund("SMALL", ["PERSONNEL"], 0.5)]))
    used = {u.fund_id: u.used_eur for u in r.fund_usage}
    assert used["BIG"] == 30000.0
    # totale copribile: 100000 x 80% al massimo per voce = 80000 (BIG 30000 + SMALL 50000 = 80000)
    assert r.covered_by_public_funds_eur == 80000.0
    assert used["SMALL"] == 50000.0


def test_non_cumulable_funds_never_cover_same_item():
    r = A.optimize_annual_allocation(req(
        [exp("E1", "PERSONNEL", 100000), exp("E2", "PERSONNEL", 100000)],
        [fund("A", ["PERSONNEL"], 0.4, excludes=["B"], max_total_eur=60000), fund("B", ["PERSONNEL"], 0.4, max_total_eur=60000)]))
    for line in r.allocation_plan:
        assert len(line.coverage) <= 1, "double funding sulla stessa voce"
    assert r.covered_by_public_funds_eur == 80000.0


def test_exclusion_is_symmetric():
    """Basta che UNO dei due fondi dichiari l'esclusione."""
    r1 = A.optimize_annual_allocation(req([exp("E1", "PERSONNEL", 100000)],
                                          [fund("A", ["PERSONNEL"], 0.4), fund("B", ["PERSONNEL"], 0.4, excludes=["A"])]))
    assert len(r1.allocation_plan[0].coverage) == 1 and r1.covered_by_public_funds_eur == 40000.0


def test_cumulation_without_exclusion_stacks_up_to_100_percent():
    r = A.optimize_annual_allocation(req([exp("E1", "PERSONNEL", 100000)], [fund("A", ["PERSONNEL"], 0.6), fund("B", ["PERSONNEL"], 0.6)]))
    assert r.covered_by_public_funds_eur == 100000.0 and r.net_cost_to_entity_eur == 0.0


def test_de_minimis_plafond_is_a_hard_limit():
    r = A.optimize_annual_allocation(req(
        [exp("E1", "PERSONNEL", 100000)], [fund("DM", ["PERSONNEL"], 0.9, de_minimis=True)], de_minimis_residual_eur=25000))
    assert r.covered_by_public_funds_eur == 25000.0 and r.de_minimis_used_eur == 25000.0 and r.de_minimis_residual_eur == 0.0


def test_de_minimis_required_when_flagged():
    with pytest.raises(ValueError):
        req([exp("E1", "PERSONNEL", 1000)], [fund("DM", ["PERSONNEL"], de_minimis=True)])


def test_category_share_cap_limits_consulting_within_fund():
    r = A.optimize_annual_allocation(req(
        [exp("P", "PERSONNEL", 80000), exp("C", "CONSULTING", 80000)],
        [fund("F", ["PERSONNEL", "CONSULTING"], 1.0, category_max_share={"CONSULTING": 0.20})]))
    cons = next(line for line in r.allocation_plan if line.item_id == "C").covered_amount_eur
    pers = next(line for line in r.allocation_plan if line.item_id == "P").covered_amount_eur
    assert dec(cons) <= dec("0.20") * (dec(cons) + dec(pers))
    assert pers == 80000.0 and cons == 20000.0


def test_month_window_and_monthly_plan():
    r = A.optimize_annual_allocation(req(
        [exp("E1", "PERSONNEL", 120000)], [fund("H2", ["PERSONNEL"], 1.0, active_from_month=7, active_to_month=12)]))
    assert r.covered_by_public_funds_eur == 60000.0
    first, last = r.monthly_plan[0], r.monthly_plan[-1]
    assert first.covered_eur == 0.0 and first.net_eur == 10000.0
    assert last.covered_eur == 10000.0 and sum(m.gross_eur for m in r.monthly_plan) == 120000.0


def test_what_if_excluding_fund_recomputes_alternative():
    base = req([exp("E1", "PERSONNEL", 100000)], [fund("A", ["PERSONNEL"], 0.8, excludes=["B"]), fund("B", ["PERSONNEL"], 0.5)])
    assert A.optimize_annual_allocation(base).allocation_plan[0].assigned_fund == "A"
    alt = A.optimize_annual_allocation(base.model_copy(update={"excluded_funds": ["A"]}))
    assert alt.allocation_plan[0].assigned_fund == "B" and alt.covered_by_public_funds_eur == 50000.0
    assert alt.excluded_funds == ["A"]


def test_no_compatible_fund_means_full_cost_to_entity():
    r = A.optimize_annual_allocation(req([exp("E1", "TRAINING", 5000)], [fund("A", ["PERSONNEL"])]))
    assert r.net_cost_to_entity_eur == 5000.0 and r.allocation_plan[0].assigned_fund == "CARICO_ENTE_DIRETTO"


def test_maximize_covered_items_prefers_breadth():
    """Un fondo con dotazione 30k: MINIMIZE copre solo la voce grande; MAXIMIZE_ITEMS copre entrambe."""
    expenses = [exp("BIG", "PERSONNEL", 100000), exp("SMALL", "PERSONNEL", 10000)]
    funds = [fund("F", ["PERSONNEL"], 1.0, max_total_eur=30000)]
    by_cost = A.optimize_annual_allocation(req(expenses, funds))
    by_items = A.optimize_annual_allocation(req(expenses, funds, optimization_target="MAXIMIZE_COVERED_ITEMS"))
    assert by_cost.covered_by_public_funds_eur == by_items.covered_by_public_funds_eur == 30000.0
    assert by_items.items_covered == 2 >= by_cost.items_covered


def test_minimize_funds_involved_trades_saving_for_simplicity():
    expenses = [exp("E1", "PERSONNEL", 100000)]
    funds = [fund("MAIN", ["PERSONNEL"], 0.6), fund("TOP_UP", ["PERSONNEL"], 0.05)]
    best = A.optimize_annual_allocation(req(expenses, funds))
    lean = A.optimize_annual_allocation(req(expenses, funds, optimization_target="MINIMIZE_FUNDS_INVOLVED", min_saving_ratio=0.9))
    assert best.funds_involved == 2 and lean.funds_involved == 1
    assert lean.covered_by_public_funds_eur >= 0.9 * best.covered_by_public_funds_eur


def test_exact_cent_accounting_and_invariants_on_realistic_case():
    expenses = [exp("STIP", "PERSONNEL", 123456.78), exp("CONS", "CONSULTING", 45678.9), exp("HW", "CAPITAL_ASSETS", 99999.99, month=3)]
    funds = [
        fund("F1", ["PERSONNEL", "CONSULTING"], 0.62, max_total_eur=70000, category_max_share={"CONSULTING": 0.2}, excludes=["F3"]),
        fund("F2", ["CAPITAL_ASSETS", "PERSONNEL"], 0.5, max_total_eur=60000, de_minimis=True),
        fund("F3", ["PERSONNEL", "CONSULTING", "CAPITAL_ASSETS"], 0.3),
    ]
    r = A.optimize_annual_allocation(req(expenses, funds, de_minimis_residual_eur=40000))
    assert dec(r.total_gross_expense_eur) == dec("123456.78") + dec("45678.90") + dec("99999.99")
    assert dec(r.covered_by_public_funds_eur) + dec(r.net_cost_to_entity_eur) == dec(r.total_gross_expense_eur)
    usage = {u.fund_id: u for u in r.fund_usage}
    assert usage["F1"].used_eur <= 70000 and usage["F2"].used_eur <= 60000 and r.de_minimis_used_eur <= 40000
    for line in r.allocation_plan:
        assert dec(line.covered_amount_eur) <= dec(line.gross_amount_eur)
        assert not ({"F1", "F3"} <= {c.fund_id for c in line.coverage})
    assert sum(dec(m.covered_eur) for m in r.monthly_plan) == dec(r.covered_by_public_funds_eur)
