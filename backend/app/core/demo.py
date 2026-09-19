"""Scenario demo COMPLETO: 46 voci in tutte le categorie, costruite per esercitare tutti i 60 criteri.

Ogni voce è pensata per un esito preciso (approvata, decurtata, respinta, sospesa) e il nome dice quale criterio
mette alla prova. Lo scenario si applica alle regole del bando selezionato: le voci in categorie non ammesse da
quel bando risulteranno respinte (è proprio ciò che si vuole vedere), e le date si adattano alla finestra del bando.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from app.models.schemas import GrantRuleSet

SANDBOX_ID = "QUANTO-SANDBOX-60"

# Regole del bando di prova: definisce TUTTE le regole, così ogni criterio è eseguibile.
SANDBOX_RULES: Dict[str, Any] = {
    "bando_id": SANDBOX_ID, "bando_name": "QUANTO Sandbox — bando di prova a 60 criteri", "rule_version_hash": "sandbox-rules-v1",
    "max_hourly_rate_personnel": 35.0, "max_consulting_percentage": 0.20, "max_overhead_percentage": 0.07,
    "max_communication_pct": 0.03, "max_immaterial_pct": 0.10, "overhead_flat_rate_pct": 0.15, "overhead_flat_base": "PERSONNEL",
    "requires_new_asset": True, "requires_iot": True, "min_energy_saving_pct": 0.03, "max_price_deviation_pct": 0.10,
    "max_installation_pct": 0.10, "requires_dnsh": True, "appraisal_threshold_eur": 50000.0, "min_durability_months": 36,
    "requires_eu_origin": True, "excluded_asset_natures": ["REAL_ESTATE"], "require_independent_supplier": True,
    "allowed_ateco_prefixes": ["62", "70", "71", "72", "28", "33"], "subcontracting_allowed": False,
    "guarantee_costs_eligible": True, "max_audit_cost_eur": 5000.0, "overtime_allowed": False, "payroll_tolerance_pct": 0.01,
    "eligibility_start": "2026-01-01", "eligibility_end": "2027-12-31", "non_cumulable_funding_ids": ["FSE-PLUS"],
    "max_aid_intensity_pct": 0.80, "contribution_rate_pct": 0.50, "de_minimis_residual_eur": 500000.0, "requires_cup": True,
    "requires_milestones": True, "max_inter_chapter_variation_pct": 0.25, "advance_pct": 0.20, "reimbursement_lag_months": 6,
}

CUP = "J51B26000010001"


def _window(rules: GrantRuleSet) -> tuple[date, date]:
    """(data dentro la finestra del bando, data fuori dalla finestra)."""
    start, end = rules.eligibility_start, rules.eligibility_end
    if start and end:
        return start + (end - start) / 2, start - timedelta(days=60)
    if start:
        return start + timedelta(days=180), start - timedelta(days=60)
    if end:
        return end - timedelta(days=180), end + timedelta(days=60)
    return date(2026, 6, 15), date(2026, 6, 15)


REALISTIC_IDS = ["P-01", "P-02", "P-03", "A-01", "A-02", "A-03", "A-11", "A-16", "C-01", "C-05", "O-01", "O-02", "O-04", "O-05", "T-01"]


def build_demo(rules: Optional[GrantRuleSet] = None, project_id: Optional[str] = None, mode: str = "stress") -> Dict[str, Any]:
    """``mode="stress"``: 46 voci, una per criterio da mettere alla prova. ``mode="realistic"``: 15 voci di un progetto verosimile."""
    rules = rules or GrantRuleSet.model_validate(SANDBOX_RULES)
    inside, outside = _window(rules)
    inside_s, outside_s = inside.isoformat(), outside.isoformat()
    common = {"cup_code": CUP, "milestone_id": "SAL-1", "payment_method": "BANK_TRANSFER", "funding_ids": [], "expense_date": inside_s}

    def line(item_id: str, description: str, category: str, **kw: Any) -> Dict[str, Any]:
        d = {"item_id": item_id, "description": description, "category": category, "source_c_ref": f"DOC-{item_id}", **common}
        d.update(kw)
        return {k: v for k, v in d.items() if v is not None}

    def pers(item_id, description, ral, fte, **kw):
        return line(item_id, description, "PERSONNEL", ral_eur=ral, fte_allocation=fte, duration_months=kw.pop("duration_months", 12),
                    **{"ccnl_code": "TERZO_SETTORE", "employee_level": "3", **kw})

    def asset(item_id, description, amount, **kw):
        base = {"is_new": True, "origin_eu": True, "iot_interconnected": True, "energy_saving_pct": 0.06, "dnsh_compliant": True,
                "exclusive_use": True, "sworn_appraisal_present": True, "post_closure_commitment_months": 48, "asset_nature": "HARDWARE",
                "supplier_durc_valid": True, "cig_required": False}
        base.update(kw)
        return line(item_id, description, "CAPITAL_ASSETS", amount_eur=amount, **base)

    def cons(item_id, description, amount, **kw):
        base = {"supplier_related_party": False, "supplier_ateco": "70.22", "supplier_durc_valid": True, "subcontracted": False}
        base.update(kw)
        return line(item_id, description, "CONSULTING", amount_eur=amount, **base)

    items: List[Dict[str, Any]] = [
        # ---- PERSONALE (criteri 1-15)
        pers("P-01", "Project manager — superminimo, straordinari, trasferte, mansionario, busta paga", 38000, 0.5, employee_token="T-PM",
             contract_type="PERMANENT", superminimo_eur=3000, superminimo_recognized=False, overtime_hours=8, travel_allowance_eur=400,
             travel_documented=True, activity_type="PROJECT", role_min_level="2", role_max_level="4", payslip_ral_eur=38000),
        pers("P-02", "Software architect — supera il tetto orario, tempo determinato, trasferte non documentate", 58000, 0.8,
             ccnl_code="METALMECCANICA", employee_level="5", employee_token="T-ARCH", contract_type="FIXED_TERM",
             travel_allowance_eur=900, travel_documented=False),
        pers("P-03", "Collaboratore occasionale nei limiti di reddito", 6000, 0.2, duration_months=6, ccnl_code="COMMERCIO",
             contract_type="OCCASIONAL", occasional_annual_income_eur=4000, employee_token="T-OCC"),
        pers("P-04", "Analista B2B senza segregazione contabile", 32000, 0.5, activity_type="B2B", activity_segregated=False, employee_token="T-B2B"),
        pers("P-05", "Secondo impegno del PM: FTE cumulato > 100%", 38000, 0.6, employee_token="T-PM"),
        pers("P-06", "Analista di credito — nessuna tabella CCNL in Fonte B", 45000, 0.5, ccnl_code="CREDITO", employee_level="2"),
        pers("P-07", "Ricercatore junior — livello sotto il mansionario", 26000, 0.5, employee_level="1", role_min_level="3", employee_token="T-JR"),
        pers("P-08", "Tecnico — RAL dichiarata diversa dalla busta paga", 30000, 0.5, employee_level="2", payslip_ral_eur=26000, employee_token="T-TEC"),
        # ---- BENI STRUMENTALI (criteri 16-30, 58)
        asset("A-01", "Centro di lavoro CNC 4.0 — ammortamento, installazione, IVA indetraibile, altri aiuti", 180000, depreciation_rate_pct=0.5,
              duration_months=24, market_benchmark_eur=170000, installation_cost_eur=12000, vat_eur=39600, vat_recoverable=False,
              reverse_charge_applied=False, other_aid_eur=20000, energy_saving_pct=0.08),
        asset("A-02", "Macchinario in leasing — interessi, IVA recuperabile, reverse charge", 60000, leasing_interest_eur=3000, vat_eur=13200,
              vat_recoverable=True, reverse_charge_applied=True),
        asset("A-03", "Software gestionale — quota massima di beni immateriali", 45000, asset_nature="SOFTWARE", sworn_appraisal_present=None),
        asset("A-04", "Macchinario usato — non nuovo di fabbrica", 30000, is_new=False),
        asset("A-05", "Impianto non interconnesso", 25000, iot_interconnected=False),
        asset("A-06", "Impianto con risparmio energetico insufficiente", 25000, energy_saving_pct=0.01),
        asset("A-07", "Bene non conforme al principio DNSH", 25000, dnsh_compliant=False),
        asset("A-08", "Attrezzatura ad uso promiscuo", 20000, exclusive_use=False),
        asset("A-09", "Impianto oltre soglia senza perizia asseverata e con impegno breve", 90000, sworn_appraisal_present=False,
              post_closure_commitment_months=12),
        asset("A-10", "Manutenzione ordinaria", 8000, expense_subtype="MAINTENANCE_ORDINARY"),
        asset("A-11", "Revisione straordinaria", 15000, expense_subtype="MAINTENANCE_EXTRAORDINARY"),
        asset("A-12", "Servizio incasellato come bene strumentale", 12000, asset_nature="SERVICE"),
        asset("A-13", "Macchinario pagato sopra il prezzo di mercato", 50000, market_benchmark_eur=30000),
        asset("A-14", "Macchinario prodotto fuori UE/SEE", 40000, origin_eu=False),
        asset("A-15", "Capannone industriale (immobile)", 200000, asset_nature="REAL_ESTATE"),
        asset("A-16", "Attrezzatura con installazione sproporzionata", 20000, installation_cost_eur=10000),
        # ---- CONSULENZE (criteri 31-35, 40, 45)
        cons("C-01", "Energy audit — tariffa oltre il benchmark, ATECO congruo, viaggi inclusi", 40000, daily_rate_eur=900, days=45,
             benchmark_daily_rate_eur=700, travel_cost_eur=1500, travel_included_in_fee=True),
        cons("C-02", "Consulenza da fornitore parte correlata", 15000, supplier_related_party=True),
        cons("C-03", "Consulenza con ATECO incongruo", 12000, supplier_ateco="96.01"),
        cons("C-04", "Consulenza con subappalto non autorizzato", 20000, subcontracted=True, subcontract_authorized=False),
        cons("C-05", "Consulenza strategica — massimale % sul totale", 120000),
        # ---- SPESE GENERALI (criteri 36-44)
        line("O-01", "Locazione sede — quota mq e mesi", "OVERHEAD", amount_eur=24000, expense_subtype="RENT", rent_sqm_project=60,
             rent_sqm_total=240, rent_months_active=12, duration_months=12),
        line("O-02", "Utenze con criterio di ripartizione oggettivo", "OVERHEAD", amount_eur=9000, expense_subtype="UTILITIES", allocation_method="kWh misurati"),
        line("O-03", "Utenze senza criterio di ripartizione", "OVERHEAD", amount_eur=6000, expense_subtype="UTILITIES"),
        line("O-04", "Campagna di comunicazione — massimale %", "OVERHEAD", amount_eur=15000, expense_subtype="COMMUNICATION"),
        line("O-05", "Fideiussione bancaria", "OVERHEAD", amount_eur=3000, expense_subtype="GUARANTEE"),
        line("O-06", "Revisione contabile oltre il limite", "OVERHEAD", amount_eur=9000, expense_subtype="AUDIT"),
        line("O-07", "Sanzione amministrativa", "OVERHEAD", amount_eur=2000, expense_subtype="PENALTY"),
        line("O-08", "Cena di rappresentanza non legata al progetto", "OVERHEAD", amount_eur=1500, expense_subtype="REPRESENTATION", project_related=False),
        line("O-09", "Spese generali forfettarie — tasso e massimale", "OVERHEAD", amount_eur=60000),
        line("O-10", "Interessi passivi", "OVERHEAD", amount_eur=4000, expense_subtype="FINANCIAL_CHARGES"),
        # ---- FORMAZIONE E CUMULO/TRACCIABILITÀ (criteri 46-52, 57, 59)
        line("T-01", "Formazione in dollari con CIG — conversione di valuta", "TRAINING", amount_eur=27000, currency="USD", fx_rate=0.92,
             cig_required=True, cig_code="8123456789", supplier_durc_valid=True),
        line("T-02", "Formazione pagata in contanti", "TRAINING", amount_eur=5000, payment_method="CASH"),
        line("T-03", "Formazione fatturata fuori dalla finestra di ammissibilità", "TRAINING", amount_eur=8000, expense_date=outside_s),
        line("T-04", "Formazione già finanziata da FSE+ (doppio finanziamento)", "TRAINING", amount_eur=7000, funding_ids=["FSE-PLUS"]),
        line("T-05", "Formazione senza CUP", "TRAINING", amount_eur=6000, cup_code=None),
        line("T-06", "Formazione senza milestone/SAL", "TRAINING", amount_eur=6500, milestone_id=None),
        line("T-07", "Formazione con CIG obbligatorio mancante", "TRAINING", amount_eur=4500, cig_required=True),
    ]
    if mode == "realistic":
        items = [i for i in items if i["item_id"] in REALISTIC_IDS]
        if rules.eligible_categories is not None:  # un progetto realistico chiede solo ciò che il bando finanzia
            allowed = {c.value for c in rules.eligible_categories}
            items = [i for i in items if i["category"] in allowed]
            if not items:  # es. bando solo personale: usa le voci di quella categoria dallo scenario completo
                items = [i for i in build_demo(rules, project_id, "stress")["cost_items"] if i["category"] in allowed][:3]
    grant_rules = rules.model_dump(mode="json", exclude_none=True)
    return {
        "project_id": project_id or ("PRJ-DEMO-REALISTICO" if mode == "realistic" else "PRJ-DEMO-COMPLETO"),
        "grant_rules": grant_rules,
        "cost_items": items,
        "entity_liquidity_eur": 1_500_000.0,
        "baseline_totals": {"PERSONNEL": 150000.0, "CAPITAL_ASSETS": 900000.0, "CONSULTING": 150000.0, "OVERHEAD": 80000.0, "TRAINING": 60000.0},
    }
