import random
from decimal import Decimal

import pytest

from app.core.deterministic_engine import DeterministicEngine as E
from app.models.schemas import ItemValidationStatus as S
from tests.conftest import other, personnel


def test_golden_pm_junior_terzo_settore(rules):
    # (38000 + 11400 + 3165.40) / 1656 = 31.74 €/h ; x 0.5 FTE, 12 mesi = 26.282,70 €
    r = E.validate_personnel_item(personnel(), rules)
    assert r.status == S.APPROVED
    assert r.computed_cost_eur == 26282.70 and r.original_cost_eur == 26282.70
    assert r.hourly_rate_computed == 31.74
    assert r.criteria_failed == []
    assert r.breakdown.annual_cost_eur == 52565.40 and r.breakdown.ccnl_table_ref.startswith("TERZO_SETTORE:LVL_3")


def test_hourly_cap_decurtazione(rules):
    r = E.validate_personnel_item(personnel(ral=58000.0, fte=0.8, ccnl="METALMECCANICA", level="5"), rules)
    assert r.status == S.CAP_EXCEEDED_ADJUSTED
    assert r.computed_cost_eur == 44800.00          # 35 x 1600 x 0.8
    assert r.original_cost_eur == 65113.12          # 81391.40 x 0.8
    assert r.criteria_failed == [7] and "CRITERION_07_HOURLY_CAP_EXCEEDED:CAP_35.0_EUR/H" in r.applied_rules


def test_duration_pro_rata(rules):
    r = E.validate_personnel_item(personnel(months=6), rules)
    assert r.computed_cost_eur == 13141.35


def test_hours_override_can_only_lower_hours(rules):
    base = E.validate_personnel_item(personnel(ral=58000.0, fte=1.0, ccnl="METALMECCANICA", level="5"), rules)
    gamed = E.validate_personnel_item(personnel(ral=58000.0, fte=1.0, ccnl="METALMECCANICA", level="5", working_hours_override=2400), rules)
    assert gamed.computed_cost_eur == base.computed_cost_eur          # override oltre lo standard ignorato
    assert any("HOURS_OVERRIDE_IGNORED" in x for x in gamed.applied_rules)


def test_unknown_ccnl_table_is_rejected_not_guessed(rules):
    r = E.validate_personnel_item(personnel(ccnl="CREDITO", level="3"), rules)
    assert r.status == S.REJECTED and r.computed_cost_eur == 0.0 and r.criteria_failed == [1]


def test_missing_source_document_suspends_line(rules):
    item = personnel()
    item.source_c_ref = "  "
    r = E.validate_personnel_item(item, rules)
    assert r.status == S.MISSING_DOCUMENTS and r.computed_cost_eur == 0.0


def test_fte_sum_over_100_percent_rejects_last_line(rules):
    items = [personnel("A", fte=0.7, employee_token="TOK-1"), personnel("B", fte=0.5, employee_token="TOK-1"),
             personnel("C", fte=0.5, employee_token="TOK-2")]
    res = {r.item_id: r for r in E.validate_budget(items, rules)}
    assert res["A"].status == S.APPROVED and res["C"].status == S.APPROVED
    assert res["B"].status == S.REJECTED and 8 in res["B"].criteria_failed


def test_consulting_cap_is_share_of_final_total(rules):
    items = [personnel("P", ral=30000.0, fte=1.0), other("C", "CONSULTING", 50000.0)]
    res = E.validate_budget(items, rules)
    p, c = res[0].computed_cost_eur, res[1].computed_cost_eur
    assert c / (p + c) <= 0.20 and c > 0
    assert res[1].status == S.CAP_EXCEEDED_ADJUSTED and 31 in res[1].criteria_failed


def test_consulting_under_cap_untouched(rules):
    res = E.validate_budget([personnel("P", ral=30000.0, fte=1.0), other("C", "CONSULTING", 1000.0)], rules)
    assert res[1].status == S.APPROVED and res[1].computed_cost_eur == 1000.0


def test_cap_solver_invariants_randomized(rules):
    """Proprietà: tetti mai superati, nessuna riduzione inutile (massimalità), nessun importo aumentato."""
    rng = random.Random(42)
    pc, po = Decimal("0.20"), Decimal("0.07")
    for _ in range(300):
        base = Decimal(rng.randint(0, 900_000)) / 100 * 100
        c = Decimal(rng.randint(0, 5_000_000)) / 100
        o = Decimal(rng.randint(0, 3_000_000)) / 100
        c2, o2 = E.solve_caps(base, c, o, pc, po)
        total = base + c2 + o2
        assert c2 <= c and o2 <= o and c2 >= 0 and o2 >= 0
        assert c2 <= pc * total and o2 <= po * total
        if c2 < c:  # se ridotta, deve essere al massimale (entro 1-2 centesimi di arrotondamento)
            assert pc * total - c2 <= Decimal("0.02")
        if o2 < o:
            assert po * total - o2 <= Decimal("0.02")


def test_apportion_sums_exactly():
    parts = E._apportion([Decimal("100.00"), Decimal("200.00"), Decimal("300.01")], Decimal("400.00"))
    assert sum(parts) == Decimal("400.00")


def test_hash_deterministic_and_sensitive(rules):
    a = E.validate_personnel_item(personnel(), rules)
    b = E.validate_personnel_item(personnel(), rules)
    c = E.validate_personnel_item(personnel(ral=38000.01), rules)
    assert a.item_hash_sha256 == b.item_hash_sha256 != c.item_hash_sha256
    other_rules = rules.model_copy(update={"rule_version_hash": "ffffffffffffffff"})
    assert E.validate_personnel_item(personnel(), other_rules).item_hash_sha256 != a.item_hash_sha256


def test_conformity_score_counts_only_executed_checks(rules, seed_items):
    res = E.validate_budget(seed_items, rules)
    total = sum(len(i.criteria_checked) for i in res)
    failed = sum(len(i.criteria_failed) for i in res)
    assert E.conformity_score(res) == (100 * (total - failed)) // total < 100
    assert E.conformity_score([]) == 100


def test_non_personnel_requires_amount():
    with pytest.raises(ValueError):
        from app.models.schemas import CostItemInput
        CostItemInput(item_id="X", description="d", category="CONSULTING", source_c_ref="D")

