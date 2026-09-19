"""Un test per ciascuno dei 60 criteri: caso che supera, caso che fallisce/decurta, e comportamento 'non valutato'."""
import random
from datetime import date

import pytest

from app.core.criteria_catalog import CRITERIA_TITLES
from app.core.deterministic_engine import DeterministicEngine as E
from app.models.schemas import CostItemInput, GrantRuleSet, ItemValidationStatus as S
from tests.conftest import personnel


def R(**kw) -> GrantRuleSet:
    base = dict(bando_id="B-1", bando_name="Bando di prova", max_hourly_rate_personnel=35.0, max_consulting_percentage=0.20,
                max_overhead_percentage=0.07, rule_version_hash="a8f3b129c9e840134012480a2")
    return GrantRuleSet(**{**base, **kw})


def X(category="CAPITAL_ASSETS", amount=10000.0, item_id="X", ref="DOC-1", **kw) -> CostItemInput:
    return CostItemInput(item_id=item_id, description=category, category=category, source_c_ref=ref, amount_eur=amount, **kw)


def run(item, rules=None):
    return E.validate_personnel_item(item, rules or R())


def failed(r, n):
    return n in r.criteria_failed


def checked(r, n):
    return n in r.criteria_checked


def budget(items, rules=None, **kw):
    return E.evaluate_budget(items, rules or R(), **kw)


P1 = 26282.70  # 38.000 RAL, TERZO_SETTORE lvl 3, 0,5 FTE, 12 mesi


def test_all_60_criteria_are_catalogued():
    assert sorted(CRITERIA_TITLES) == list(range(1, 61))


# ------------------------------------------------------------------ personale 1-15
def test_c06_superminimo_not_recognized_is_excluded():
    r = run(personnel(ral=40000.0, fte=1.0, superminimo_eur=4000.0, superminimo_recognized=False))
    assert (r.original_cost_eur, r.computed_cost_eur, r.status) == (55332.00, 49798.80, S.CAP_EXCEEDED_ADJUSTED) and failed(r, 6)
    ok = run(personnel(ral=40000.0, fte=1.0, superminimo_eur=4000.0, superminimo_recognized=True))
    assert ok.computed_cost_eur == 55332.00 and checked(ok, 6) and not failed(ok, 6)


@pytest.mark.parametrize("documented,expected_cost,status", [(True, 26782.70, S.APPROVED), (False, P1, S.CAP_EXCEEDED_ADJUSTED), (None, 0.0, S.MISSING_DOCUMENTS)])
def test_c09_travel_allowance_traceability(documented, expected_cost, status):
    r = run(personnel(travel_allowance_eur=500.0, travel_documented=documented))
    assert r.computed_cost_eur == expected_cost and r.status == status and checked(r, 9)
    assert r.original_cost_eur == 26782.70 or documented is None


def test_c10_b2b_activity_requires_segregation():
    assert run(personnel(activity_type="B2B", activity_segregated=False)).status == S.REJECTED
    assert run(personnel(activity_type="B2G")).status == S.REJECTED
    assert run(personnel(activity_type="B2B", activity_segregated=True)).status == S.APPROVED
    assert run(personnel(activity_type="PROJECT")).status == S.APPROVED


def test_c11_overtime_blocked_unless_allowed():
    r = run(personnel(overtime_hours=10.0))
    assert r.computed_cost_eur == 25965.28 and failed(r, 11)          # 26.282,70 - 10h x 31,7417 €/h
    assert run(personnel(overtime_hours=10.0), R(overtime_allowed=True)).computed_cost_eur == P1
    assert run(personnel(overtime_hours=0.0)).computed_cost_eur == P1


def test_c12_fixed_term_contribution_surcharge():
    r = run(personnel(contract_type="FIXED_TERM"))
    assert r.computed_cost_eur == 26548.70 and r.breakdown.social_charges_pct == 0.314   # 31,4% oneri
    assert run(personnel(contract_type="PERMANENT")).computed_cost_eur == P1


def test_c13_occasional_income_limit():
    assert run(personnel(contract_type="OCCASIONAL", occasional_annual_income_eur=6000.0)).status == S.REJECTED
    r = run(personnel(contract_type="OCCASIONAL", occasional_annual_income_eur=4000.0))
    assert r.status == S.APPROVED and checked(r, 13)


def test_c14_level_congruent_with_role():
    assert run(personnel(role_min_level="4")).status == S.REJECTED
    assert run(personnel(role_max_level="2")).status == S.REJECTED
    assert run(personnel(role_min_level="2", role_max_level="3")).status == S.APPROVED


def test_c15_payslip_cross_check_with_tolerance():
    assert run(personnel(payslip_ral_eur=36000.0)).status == S.REJECTED
    assert run(personnel(payslip_ral_eur=38200.0)).status == S.APPROVED       # 0,52% < 1%
    assert run(personnel(payslip_ral_eur=38200.0), R(payroll_tolerance_pct=0.001)).status == S.REJECTED


# ------------------------------------------------------------------ beni 16-30 e 58
def test_c16_service_is_not_a_capital_asset_and_missing_document():
    assert run(X(asset_nature="SERVICE")).status == S.REJECTED
    assert run(X(asset_nature="HARDWARE")).status == S.APPROVED
    assert run(X(ref=" ")).status == S.MISSING_DOCUMENTS


def test_c17_c18_pro_rata_temporis_depreciation():
    r = run(X(depreciation_rate_pct=0.2, duration_months=6))
    assert r.computed_cost_eur == 1000.0 and checked(r, 17) and failed(r, 18) and r.status == S.CAP_EXCEEDED_ADJUSTED
    assert run(X(depreciation_rate_pct=1.0, duration_months=12)).computed_cost_eur == 10000.0


def test_c19_new_asset_requirement():
    assert run(X(is_new=False), R(requires_new_asset=True)).status == S.REJECTED
    assert run(X(is_new=True), R(requires_new_asset=True)).status == S.APPROVED
    assert run(X(is_new=False)).status == S.APPROVED     # regola assente nel bando: non valutata


def test_c20_iot_interconnection():
    assert run(X(iot_interconnected=False), R(requires_iot=True)).status == S.REJECTED
    assert run(X(iot_interconnected=True), R(requires_iot=True)).status == S.APPROVED
    assert not checked(run(X(iot_interconnected=False)), 20)             # regola assente nel bando: non valutato


def test_c21_energy_saving_minimum():
    assert run(X(energy_saving_pct=0.05), R(min_energy_saving_pct=0.10)).status == S.REJECTED
    assert run(X(energy_saving_pct=0.20), R(min_energy_saving_pct=0.10)).status == S.APPROVED


def test_c22_price_capped_at_benchmark_plus_tolerance():
    r = run(X(market_benchmark_eur=8000.0), R(max_price_deviation_pct=0.10))
    assert r.computed_cost_eur == 8800.0 and failed(r, 22)
    assert run(X(market_benchmark_eur=9500.0), R(max_price_deviation_pct=0.10)).computed_cost_eur == 10000.0


def test_c23_installation_share_capped():
    r = run(X(installation_cost_eur=2000.0), R(max_installation_pct=0.10))
    assert r.computed_cost_eur == 8800.0 and failed(r, 23)             # ammessi 10% di 8.000 = 800 su 2.000


def test_c24_leasing_interest_excluded():
    r = run(X(leasing_interest_eur=500.0))
    assert r.computed_cost_eur == 9500.0 and failed(r, 24)
    assert checked(run(X(leasing_interest_eur=0.0)), 24)


def test_c25_reverse_charge_vat_not_counted_twice():
    r = run(X(vat_eur=2200.0, reverse_charge_applied=True))
    assert (r.original_cost_eur, r.computed_cost_eur) == (12200.0, 10000.0) and failed(r, 25)
    assert run(X(vat_eur=2200.0, reverse_charge_applied=False)).computed_cost_eur == 12200.0


def test_c26_immaterial_assets_share_cap():
    items = [personnel("P", ral=30000.0, fte=1.0), X(item_id="SW", amount=20000.0, asset_nature="SOFTWARE")]
    res, _ = budget(items, R(max_immaterial_pct=0.10))
    p, sw = res[0].computed_cost_eur, res[1].computed_cost_eur
    assert sw / (p + sw) <= 0.10 and sw > 0 and failed(res[1], 26)


def test_c27_ordinary_vs_extraordinary_maintenance():
    assert run(X(expense_subtype="MAINTENANCE_ORDINARY")).status == S.REJECTED
    r = run(X(expense_subtype="MAINTENANCE_EXTRAORDINARY"))
    assert r.status == S.APPROVED and checked(r, 27)


def test_c28_dnsh():
    assert run(X(dnsh_compliant=False), R(requires_dnsh=True)).status == S.REJECTED
    assert run(X(dnsh_compliant=True), R(requires_dnsh=True)).status == S.APPROVED


def test_c29_exclusive_use():
    assert run(X(exclusive_use=False)).status == S.REJECTED
    assert run(X(exclusive_use=True)).status == S.APPROVED


def test_c30_sworn_appraisal_above_threshold():
    assert run(X(sworn_appraisal_present=False), R(appraisal_threshold_eur=5000.0)).status == S.MISSING_DOCUMENTS
    assert run(X(sworn_appraisal_present=True), R(appraisal_threshold_eur=5000.0)).status == S.APPROVED
    assert run(X(amount=4000.0, sworn_appraisal_present=False), R(appraisal_threshold_eur=5000.0)).status == S.APPROVED


def test_c58_durability_after_closure():
    assert run(X(post_closure_commitment_months=12), R(min_durability_months=24)).status == S.REJECTED
    assert run(X(post_closure_commitment_months=36), R(min_durability_months=24)).status == S.APPROVED


# ------------------------------------------------------------------ consulenze e spese generali 31-45
def test_c31_consulting_share_cap():
    res, _ = budget([personnel("P", ral=30000.0, fte=1.0), X("CONSULTING", 50000.0, "C")])
    assert res[1].computed_cost_eur / (res[0].computed_cost_eur + res[1].computed_cost_eur) <= 0.20 and failed(res[1], 31)


def test_c32_related_party_supplier():
    assert run(X("CONSULTING", supplier_related_party=True)).status == S.REJECTED
    assert run(X("CONSULTING", supplier_related_party=False)).status == S.APPROVED
    assert run(X("CONSULTING", supplier_related_party=True), R(require_independent_supplier=False)).status == S.APPROVED


def test_c33_daily_rate_normalized_to_benchmark():
    r = run(X("CONSULTING", daily_rate_eur=1000.0, days=10.0, benchmark_daily_rate_eur=800.0))
    assert r.computed_cost_eur == 8000.0 and failed(r, 33)


def test_c34_ateco_congruence():
    rules = R(allowed_ateco_prefixes=["62"])
    assert run(X("CONSULTING", supplier_ateco="70.22"), rules).status == S.REJECTED
    assert run(X("CONSULTING", supplier_ateco="62.01"), rules).status == S.APPROVED


def test_c35_unauthorized_subcontracting():
    assert run(X("CONSULTING", subcontracted=True, subcontract_authorized=True)).status == S.REJECTED   # bando non lo consente
    assert run(X("CONSULTING", subcontracted=True, subcontract_authorized=True), R(subcontracting_allowed=True)).status == S.APPROVED
    assert run(X("CONSULTING", subcontracted=True, subcontract_authorized=False), R(subcontracting_allowed=True)).status == S.REJECTED
    assert run(X("CONSULTING", subcontracted=False)).status == S.APPROVED


def test_c36_overhead_share_and_flat_rate_of_personnel():
    p = personnel("P", ral=30000.0, fte=1.0)                                   # costo pieno 41.499,00
    flat, _ = budget([p, X("OVERHEAD", 10000.0, "O")], R(max_overhead_percentage=0.5, overhead_flat_rate_pct=0.15))
    assert flat[1].computed_cost_eur == 6224.85 and failed(flat[1], 36)        # 15% x 41.499
    share, _ = budget([p, X("OVERHEAD", 10000.0, "O")])
    assert share[1].computed_cost_eur / (share[0].computed_cost_eur + share[1].computed_cost_eur) <= 0.07


def test_c37_communication_cap():
    items = [personnel("P", ral=30000.0, fte=1.0), X("OVERHEAD", 5000.0, "COM", expense_subtype="COMMUNICATION")]
    res, _ = budget(items, R(max_communication_pct=0.05))
    assert res[1].computed_cost_eur / (res[0].computed_cost_eur + res[1].computed_cost_eur) <= 0.05 and failed(res[1], 37)


def test_c38_guarantee_costs():
    assert run(X("OVERHEAD", expense_subtype="GUARANTEE"), R(guarantee_costs_eligible=False)).status == S.REJECTED
    assert run(X("OVERHEAD", expense_subtype="GUARANTEE"), R(guarantee_costs_eligible=True)).status == S.APPROVED
    assert not checked(run(X("OVERHEAD", expense_subtype="GUARANTEE")), 38)


def test_c39_audit_cost_cap():
    r = run(X("OVERHEAD", 5000.0, expense_subtype="AUDIT"), R(max_audit_cost_eur=3000.0))
    assert r.computed_cost_eur == 3000.0 and failed(r, 39)


def test_c40_consultant_travel_included_or_itemized():
    assert run(X("CONSULTING", travel_cost_eur=200.0)).status == S.MISSING_DOCUMENTS
    assert run(X("CONSULTING", travel_cost_eur=200.0, travel_included_in_fee=True)).status == S.APPROVED


@pytest.mark.parametrize("subtype", ["PENALTY", "LEGAL_DISPUTE"])
def test_c41_penalties_and_disputes_excluded(subtype):
    r = run(X("OVERHEAD", expense_subtype=subtype))
    assert r.status == S.REJECTED and failed(r, 41)


def test_c42_rent_pro_rata_on_area_and_months():
    r = run(X("OVERHEAD", 12000.0, expense_subtype="RENT", rent_sqm_project=50.0, rent_sqm_total=200.0, rent_months_active=12))
    assert r.computed_cost_eur == 3000.0 and failed(r, 42)
    half = run(X("OVERHEAD", 12000.0, expense_subtype="RENT", rent_sqm_project=200.0, rent_sqm_total=200.0, rent_months_active=6))
    assert half.computed_cost_eur == 6000.0


def test_c43_utilities_need_objective_allocation_key():
    assert run(X("OVERHEAD", expense_subtype="UTILITIES")).status == S.MISSING_DOCUMENTS
    assert run(X("OVERHEAD", expense_subtype="UTILITIES", allocation_method="metri quadri")).status == S.APPROVED


def test_c44_representation_only_if_project_related():
    assert run(X("OVERHEAD", expense_subtype="REPRESENTATION", project_related=False)).status == S.REJECTED
    assert run(X("OVERHEAD", expense_subtype="REPRESENTATION", project_related=True)).status == S.APPROVED


def test_c45_durc():
    assert run(X("CONSULTING", supplier_durc_valid=False)).status == S.REJECTED
    assert checked(run(X("CONSULTING", supplier_durc_valid=True)), 45)


# ------------------------------------------------------------------ tempo, cumulo, tracciabilità 46-59
def test_c46_expense_date_window():
    rules = R(eligibility_start=date(2026, 1, 1), eligibility_end=date(2026, 12, 31))
    assert run(X(expense_date=date(2025, 12, 31)), rules).status == S.REJECTED
    assert run(X(expense_date=date(2027, 1, 1)), rules).status == S.REJECTED
    assert run(X(expense_date=date(2026, 6, 1)), rules).status == S.APPROVED
    assert not checked(run(X(expense_date=date(2020, 1, 1))), 46)


def test_c47_double_funding():
    rules = R(non_cumulable_funding_ids=["FSE-PLUS"])
    assert run(X(funding_ids=["FSE-PLUS"]), rules).status == S.REJECTED
    assert run(X(funding_ids=[]), rules).status == S.APPROVED
    assert run(X(funding_ids=["ALTRO"]), rules).status == S.APPROVED


def test_c48_aid_intensity_cumulation_budget_check():
    items = [personnel("P", ral=30000.0, fte=1.0, )]
    items[0].other_aid_eur = 30000.0
    _, checks = budget(items, R(contribution_rate_pct=0.6, max_aid_intensity_pct=0.8))
    c48 = next(c for c in checks if c.criterion == 48)
    assert c48.status == "FAIL"
    items[0].other_aid_eur = 1000.0
    assert next(c for c in budget(items, R(contribution_rate_pct=0.6, max_aid_intensity_pct=0.8))[1] if c.criterion == 48).status == "PASS"
    assert next(c for c in budget(items)[1] if c.criterion == 48).status == "NOT_EVALUATED"


def test_c49_de_minimis_residual_budget_check():
    items = [personnel("P", ral=30000.0, fte=1.0)]                              # ammesso 41.499 -> contributo 50% = 20.749,50
    fail = next(c for c in budget(items, R(contribution_rate_pct=0.5, de_minimis_residual_eur=20000.0))[1] if c.criterion == 49)
    assert fail.status == "FAIL" and "40000.00" in fail.message           # base massima = 20.000 / 50%
    assert next(c for c in budget(items, R(contribution_rate_pct=0.5, de_minimis_residual_eur=30000.0))[1] if c.criterion == 49).status == "PASS"


def test_c50_cup_required_and_format():
    rules = R(requires_cup=True)
    assert run(X(), rules).status == S.MISSING_DOCUMENTS
    assert run(X(cup_code="ABC"), rules).status == S.MISSING_DOCUMENTS
    assert run(X(cup_code="J51B21005710006"), rules).status == S.APPROVED


def test_c51_cig_when_required():
    assert run(X(cig_required=True)).status == S.MISSING_DOCUMENTS
    assert run(X(cig_required=True, cig_code="ABCDE12345")).status == S.APPROVED
    assert run(X(cig_required=False)).status == S.APPROVED


def test_c52_blocked_payment_methods():
    assert run(X(payment_method="cash")).status == S.REJECTED
    assert run(X(payment_method="CHECK")).status == S.REJECTED
    assert run(X(payment_method="BANK_TRANSFER")).status == S.APPROVED
    assert run(personnel(payment_method="CASH")).status == S.REJECTED


def test_c53_c54_vat_recoverable_excluded_unrecoverable_eligible():
    rec = run(X(vat_eur=2200.0, vat_recoverable=True))
    assert (rec.original_cost_eur, rec.computed_cost_eur) == (12200.0, 10000.0) and failed(rec, 54)
    non = run(X(vat_eur=2200.0, vat_recoverable=False))
    assert non.computed_cost_eur == 12200.0 and checked(non, 53)


def test_c55_cash_flow_sustainability():
    items = [personnel("P", ral=30000.0, fte=1.0)]
    rules = R(reimbursement_lag_months=6, advance_pct=0.2)                     # esposizione 41.499 x 0,8 x 6/12 = 16.599,60
    get = lambda liq: next(c for c in budget(items, rules, entity_liquidity_eur=liq)[1] if c.criterion == 55)
    assert get(10000.0).status == "FAIL" and get(20000.0).status == "PASS"
    assert next(c for c in budget(items, rules)[1] if c.criterion == 55).status == "NOT_EVALUATED"


def test_c56_inter_chapter_variation():
    items = [personnel("P", ral=30000.0, fte=1.0)]
    rules = R(max_inter_chapter_variation_pct=0.10)
    get = lambda ref: next(c for c in budget(items, rules, baseline_totals={"PERSONNEL": ref})[1] if c.criterion == 56)
    assert get(30000.0).status == "FAIL" and get(40000.0).status == "PASS"


def test_c57_milestone_assignment():
    rules = R(requires_milestones=True)
    assert run(X(), rules).status == S.MISSING_DOCUMENTS
    assert run(X(milestone_id="SAL-1"), rules).status == S.APPROVED


def test_c59_foreign_currency_needs_fx_rate():
    assert run(X(currency="USD")).status == S.MISSING_DOCUMENTS
    r = run(X(currency="USD", fx_rate=0.9))
    assert r.original_cost_eur == r.computed_cost_eur == 9000.0 and checked(r, 59)


def test_c60_global_coherence_check_present_and_passing():
    _, checks = budget([personnel("P"), X("CONSULTING", 30000.0, "C")])
    c60 = next(c for c in checks if c.criterion == 60)
    assert c60.status == "PASS"
    assert {c.criterion for c in checks} == {48, 49, 55, 56, 60}


# ------------------------------------------------------------------ non valutati e invarianti
def test_missing_data_is_reported_as_not_evaluated_never_as_passed():
    r = run(personnel())
    assert r.criteria_not_evaluated == [6, 9, 10, 11, 12, 13, 14, 46, 47, 50, 52, 57]
    assert set(r.criteria_checked) == {1, 2, 3, 4, 5, 7, 8, 15}
    assert not set(r.criteria_checked) & set(r.criteria_not_evaluated)


def test_conformity_score_includes_budget_checks():
    items, checks = budget([personnel()])
    assert E.conformity_score(items, checks) == 100
    items2, checks2 = budget([personnel(ral=58000.0, ccnl="METALMECCANICA", level="5")])
    assert E.conformity_score(items2, checks2) < 100


def test_random_budgets_keep_invariants():
    rng = random.Random(7)
    subtypes = [None, "COMMUNICATION", "AUDIT", "RENT", "UTILITIES", "GUARANTEE"]
    for n in range(150):
        items = []
        for i in range(rng.randint(1, 6)):
            cat = rng.choice(["PERSONNEL", "CAPITAL_ASSETS", "CONSULTING", "OVERHEAD", "TRAINING"])
            if cat == "PERSONNEL":
                items.append(personnel(f"I{i}", ral=float(rng.randint(15000, 80000)), fte=rng.choice([0.25, 0.5, 1.0]),
                                       months=rng.choice([6, 12, 24]), superminimo_eur=rng.choice([None, 2000.0]),
                                       superminimo_recognized=rng.choice([None, False, True]), overtime_hours=rng.choice([None, 0.0, 12.0])))
            else:
                items.append(X(cat, float(rng.randint(500, 90000)), f"I{i}", expense_subtype=rng.choice(subtypes) if cat == "OVERHEAD" else None,
                               vat_eur=rng.choice([None, 220.0]), vat_recoverable=rng.choice([None, True, False])))
        rules = R(max_communication_pct=rng.choice([None, 0.05]), max_immaterial_pct=rng.choice([None, 0.1]), max_audit_cost_eur=rng.choice([None, 2000.0]))
        res, checks = budget(items, rules)
        for it in res:
            assert 0 <= it.computed_cost_eur <= it.original_cost_eur
        assert next(c for c in checks if c.criterion == 60).status == "PASS"
        again, _ = budget(items, rules)
        assert [a.item_hash_sha256 for a in again] == [b.item_hash_sha256 for b in res]
