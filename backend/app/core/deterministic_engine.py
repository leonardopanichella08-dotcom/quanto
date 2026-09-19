"""Motore di calcolo deterministico e validatore di ammissibilità (codice puro, zero LLM).

- Ogni operazione aritmetica usa ``decimal.Decimal``; i ``float`` compaiono solo ai bordi.
- Ogni riga porta la traccia completa delle regole applicate e dei criteri eseguiti / falliti / non valutati.
- Ogni riga validata produce un hash SHA-256 canonico (foglia dell'Albero di Merkle).
- I 60 criteri del Modulo 11 sono tutti implementati. Un criterio si esegue solo se esiste il dato sulla riga
  e (dove serve) la regola nel bando: altrimenti è "non valutato" e NON conta come superato.
- Le rettifiche (decurtazioni) riducono l'importo ammesso senza mai aumentarlo: ``0 <= approvato <= originale``.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from itertools import product
from typing import Dict, List, Optional, Sequence, Tuple

from app.core.criteria_catalog import CRITERIA_TITLES, applicable_criteria
from app.core.fonte_b import FIXED_TERM_SURCHARGE_PCT, OCCASIONAL_INCOME_LIMIT_EUR, lookup_ccnl, table_ref
from app.models.schemas import (
    ActivityType, AssetNature, BudgetCheck, CCNLType, ContractType, CostBreakdown, CostCategory, CostItemInput,
    CostItemValidated, ExpenseSubtype, FlatBase, GrantRuleSet, ItemValidationStatus as S, MerkleView, PipelineStage, TraceStep,
)

ZERO = Decimal("0.00")
CENT = Decimal("0.01")
TWELVE = Decimal(12)
IMPLEMENTED_CRITERIA = CRITERIA_TITLES  # tutti e 60

_CUP_RE = re.compile(r"^[A-Z0-9]{15}$")
_CIG_RE = re.compile(r"^[A-Z0-9]{10}$")
_RANK = {S.APPROVED: 0, S.CAP_EXCEEDED_ADJUSTED: 1, S.MISSING_DOCUMENTS: 2, S.REJECTED: 3}


def q(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def q_down(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_DOWN)


def dec(value) -> Decimal:
    """float/int/str -> Decimal senza passare dalla rappresentazione binaria."""
    return Decimal(str(value))


def fmt(value: Decimal) -> str:
    return format(q(value), "f")


def _f(value: Decimal) -> float:
    return float(q(value))


def _level(text: Optional[str]) -> Optional[int]:
    return int(text) if text is not None and text.strip().isdigit() else None


# --------------------------------------------------------------------------- working record
@dataclass
class _Line:
    item: CostItemInput
    status: S = S.APPROVED
    original: Decimal = ZERO
    approved: Decimal = ZERO
    hourly: Decimal = ZERO
    hourly_cap: Decimal = ZERO
    reasons: List[str] = field(default_factory=list)
    rules: List[str] = field(default_factory=list)
    checked: List[int] = field(default_factory=list)
    failed: List[int] = field(default_factory=list)
    breakdown: Dict = field(default_factory=dict)
    adjustments: List[Dict] = field(default_factory=list)

    @property
    def is_live(self) -> bool:
        return self.status in (S.APPROVED, S.CAP_EXCEEDED_ADJUSTED)

    def check(self, n: int) -> None:
        if n not in self.checked:
            self.checked.append(n)

    def ok(self, n: int, rule: str) -> None:
        self.check(n)
        self.rules.append(rule)

    def _escalate(self, status: S) -> None:
        if _RANK[status] > _RANK[self.status]:
            self.status = status

    def _fail(self, n: int, reason: str, rule: str) -> None:
        self.check(n)
        if n not in self.failed:
            self.failed.append(n)
        self.rules.append(rule)
        self.reasons.append(reason)

    def reject(self, n: int, reason: str, rule: str, status: S = S.REJECTED) -> None:
        """Respinge (o sospende) l'intera riga: l'importo ammesso diventa zero."""
        before = self.approved if self.is_live else ZERO
        self._fail(n, reason, rule)
        self.approved = ZERO
        self._escalate(status)
        self.adjustments.append({"criterion": n, "kind": "SUSPENDED" if status == S.MISSING_DOCUMENTS else "REJECTED",
                                 "delta": -before, "note": reason})

    def cut(self, n: int, excess: Decimal, reason: str, rule: str) -> Decimal:
        """Decurta l'ammesso di ``excess`` (mai sotto zero). Restituisce l'importo effettivamente tolto."""
        self._fail(n, reason, rule)
        taken = min(max(excess, ZERO), self.approved) if self.is_live else ZERO
        self.approved -= taken
        if self.is_live:
            self._escalate(S.CAP_EXCEEDED_ADJUSTED)
        self.adjustments.append({"criterion": n, "kind": "ADJUSTED", "delta": -taken, "note": reason})
        return taken


class DeterministicEngine:
    # ------------------------------------------------------------------ per-line: personnel
    @classmethod
    def _compute_personnel(cls, line: _Line, rules: GrantRuleSet) -> None:
        item = line.item
        ccnl = item.ccnl_code or CCNLType.TERZO_SETTORE

        # Criterio 1 — Fonte B. Nessun fallback su parametri "standard": senza tabella la riga è respinta.
        line.check(1)
        params = lookup_ccnl(ccnl, item.employee_level)
        if params is None:
            line.reject(1, f"Tabella CCNL non disponibile in Fonte B per {ccnl.value} livello {item.employee_level}: "
                           "impossibile calcolare il costo senza una fonte tabellare.",
                        f"CRITERION_01_CCNL_TABLE_NOT_FOUND:{ccnl.value}:LVL_{item.employee_level}")
            return
        line.rules.append(f"CRITERION_01_CCNL_LOOKUP:{ccnl.value}:LVL_{item.employee_level}")
        line.breakdown["ccnl_table_ref"] = table_ref(ccnl, item.employee_level)

        # Criterio 3 — divisore contrattuale. L'override può solo RIDURRE le ore (alzarle gonfierebbe il massimale).
        hours = params.standard_hours
        if item.working_hours_override is not None:
            if item.working_hours_override <= params.standard_hours:
                hours = item.working_hours_override
            else:
                line.rules.append(f"CRITERION_03_HOURS_OVERRIDE_IGNORED:{item.working_hours_override}>CCNL_{params.standard_hours}")

        declared = q(dec(item.ral_eur))
        effective = declared
        superminimo_excluded = ZERO
        if item.superminimo_eur is not None:                                             # criterio 6
            line.check(6)
            if item.superminimo_recognized is False:
                superminimo_excluded = min(q(dec(item.superminimo_eur)), declared)
                effective = declared - superminimo_excluded
            else:
                line.rules.append("CRITERION_06_SUPERMINIMO_RECOGNIZED")

        surcharge = ZERO
        if item.contract_type is not None:                                               # criterio 12
            line.check(12)
            if item.contract_type == ContractType.FIXED_TERM:
                surcharge = FIXED_TERM_SURCHARGE_PCT
                line.rules.append(f"CRITERION_12_FIXED_TERM_SURCHARGE:{q(surcharge * 100)}%")
            else:
                line.rules.append(f"CRITERION_12_CONTRACT_TYPE:{item.contract_type.value}")

        def annual(ral: Decimal) -> Tuple[Decimal, Decimal, Decimal]:
            social = q(ral * (params.social_charges_pct + surcharge))
            tfr = q(ral * params.tfr_pct)
            return social, tfr, ral + social + tfr

        for c in (2, 3, 4, 5):
            line.check(c)
        social_d, tfr_d, annual_decl = annual(declared)
        social, tfr, annual_eff = annual(effective)
        line.rules += ["CRITERION_02_ANNUAL_GROSS_COMPUTATION:(RAL+SOCIAL+TFR)", f"CRITERION_03_HOURLY_DIVISOR:{hours}_HOURS",
                       f"CRITERION_04_TFR_RECOMPUTED:{q(params.tfr_pct * 100)}%", f"CRITERION_05_SOCIAL_CHARGES:{q((params.social_charges_pct + surcharge) * 100)}%"]
        line.hourly = q(annual_eff / Decimal(hours))

        fte, ratio = dec(item.fte_allocation), Decimal(item.duration_months) / TWELVE
        line.check(8)
        line.rules.append(f"CRITERION_08_FTE_PRO_RATA:{item.fte_allocation}_FTE:{item.duration_months}_MONTHS")
        line.original = q(annual_decl * fte * ratio)
        line.approved = line.original

        if superminimo_excluded > 0:
            line.cut(6, line.original - q(annual_eff * fte * ratio),
                     f"Superminimo non assorbibile/unilaterale ({fmt(superminimo_excluded)} €) escluso dalla RAL ammissibile.",
                     f"CRITERION_06_SUPERMINIMO_EXCLUDED:{fmt(superminimo_excluded)}")

        # Criterio 7 — tetto orario (confronto senza divisione: annual/ore > cap  <=>  annual > cap*ore).
        # Se il bando non definisce un tetto orario il criterio NON viene eseguito (nessun default inventato).
        cap: Optional[Decimal] = dec(rules.max_hourly_rate_personnel) if rules.max_hourly_rate_personnel is not None else None
        if cap is not None:
            line.check(7)
            line.hourly_cap = cap
            if annual_eff > cap * Decimal(hours):
                line.cut(7, q(annual_eff * fte * ratio) - q(cap * Decimal(hours) * fte * ratio),
                         f"Costo orario calcolato ({line.hourly} €/h) superiore al tetto ammissibile dal bando "
                         f"({rules.max_hourly_rate_personnel} €/h). Applicata decurtazione automatica al massimale.",
                         f"CRITERION_07_HOURLY_CAP_EXCEEDED:CAP_{rules.max_hourly_rate_personnel}_EUR/H")
            else:
                line.rules.append("CRITERION_07_HOURLY_RATE_COMPLIANT")

        hourly_exact = annual_eff / Decimal(hours)
        line.breakdown.update(
            ral_eur=_f(effective), social_charges_pct=float(params.social_charges_pct + surcharge), social_charges_eur=_f(social),
            tfr_pct=float(params.tfr_pct), tfr_eur=_f(tfr), annual_cost_eur=_f(annual_eff), working_hours=hours,
            fte_allocation=item.fte_allocation, duration_months=item.duration_months, hourly_cap_eur=_f(cap) if cap is not None else None,
        )

        if item.travel_allowance_eur is not None:                                        # criterio 9
            allowance = q(dec(item.travel_allowance_eur))
            line.original += allowance
            line.approved += allowance
            if item.travel_documented is True:
                line.ok(9, "CRITERION_09_TRAVEL_DOCUMENTED")
            elif item.travel_documented is False:
                line.cut(9, allowance, "Trasferte/diarie non tracciate: escluse dall'importo ammesso.", "CRITERION_09_TRAVEL_NOT_DOCUMENTED")
            else:
                line.reject(9, "Tracciabilità di trasferte/diarie non dichiarata: riga sospesa.", "CRITERION_09_TRAVEL_TRACEABILITY_UNKNOWN", S.MISSING_DOCUMENTS)

        if item.activity_type is not None:                                               # criterio 10
            if item.activity_type == ActivityType.PROJECT or item.activity_segregated is True:
                line.ok(10, f"CRITERION_10_ACTIVITY_SEGREGATION_OK:{item.activity_type.value}")
            else:
                line.reject(10, f"Attività {item.activity_type.value} senza segregazione contabile: riga respinta.",
                            f"CRITERION_10_ACTIVITY_NOT_SEGREGATED:{item.activity_type.value}")

        if item.overtime_hours is not None:                                              # criterio 11
            if item.overtime_hours == 0 or rules.overtime_allowed:
                line.ok(11, "CRITERION_11_OVERTIME_ALLOWED_OR_ABSENT")
            else:
                line.cut(11, q(hourly_exact * dec(item.overtime_hours)),
                         f"Ore straordinarie ({item.overtime_hours} h) non previste dal regolamento: escluse.",
                         f"CRITERION_11_OVERTIME_BLOCKED:{item.overtime_hours}_H")

        if item.contract_type == ContractType.OCCASIONAL and item.occasional_annual_income_eur is not None:  # criterio 13
            if dec(item.occasional_annual_income_eur) > OCCASIONAL_INCOME_LIMIT_EUR:
                line.reject(13, f"Reddito del collaboratore occasionale oltre il limite di {fmt(OCCASIONAL_INCOME_LIMIT_EUR)} €.",
                            f"CRITERION_13_OCCASIONAL_INCOME_EXCEEDED:{item.occasional_annual_income_eur}")
            else:
                line.ok(13, "CRITERION_13_OCCASIONAL_INCOME_WITHIN_LIMIT")

        if item.role_min_level is not None or item.role_max_level is not None:           # criterio 14
            lvl, lo, hi = _level(item.employee_level), _level(item.role_min_level), _level(item.role_max_level)
            if lvl is not None:
                if (lo is not None and lvl < lo) or (hi is not None and lvl > hi):
                    line.reject(14, f"Livello {item.employee_level} non congruo con il mansionario ({item.role_min_level or '-'}..{item.role_max_level or '-'}).",
                                f"CRITERION_14_LEVEL_INCONGRUENT:{item.employee_level}")
                else:
                    line.ok(14, "CRITERION_14_LEVEL_CONGRUENT")

        line.check(15)                                                                    # criterio 15
        if not item.source_c_ref.strip():
            line.reject(15, "Riferimento al documento contabile (Fonte C) mancante: riga sospesa.",
                        "CRITERION_15_SOURCE_DOCUMENT_MISSING", S.MISSING_DOCUMENTS)
        else:
            line.rules.append("CRITERION_15_SOURCE_DOCUMENT_PRESENT")
        if item.payslip_ral_eur is not None:
            slip = q(dec(item.payslip_ral_eur))
            if abs(declared - slip) > dec(rules.payroll_tolerance_pct) * slip:
                line.reject(15, f"RAL dichiarata ({fmt(declared)} €) difforme dalla busta paga ({fmt(slip)} €) oltre la tolleranza.",
                            f"CRITERION_15_PAYSLIP_MISMATCH:{fmt(declared)}!={fmt(slip)}")
            else:
                line.rules.append("CRITERION_15_PAYSLIP_MATCH")

    # ------------------------------------------------------------------ per-line: non-personnel
    @classmethod
    def _compute_non_personnel(cls, line: _Line, rules: GrantRuleSet) -> None:
        it = line.item
        net = q(dec(it.amount_eur))
        vat = q(dec(it.vat_eur)) if it.vat_eur is not None else ZERO
        fx_missing = False
        if it.currency.upper() != "EUR":                                                 # criterio 59
            if it.fx_rate is None:
                fx_missing = True
            else:
                fx = dec(it.fx_rate)
                net, vat = q(net * fx), q(vat * fx)
                line.ok(59, f"CRITERION_59_FX_CONVERTED:{it.currency.upper()}@{it.fx_rate}")
        line.original = net + vat
        line.approved = line.original
        if fx_missing:
            line.reject(59, f"Valuta {it.currency.upper()} senza tasso di cambio: riga sospesa.", "CRITERION_59_FX_RATE_MISSING", S.MISSING_DOCUMENTS)

        state = {"net": net}

        def net_cut(n: int, excess: Decimal, reason: str, rule: str) -> None:
            taken = line.cut(n, min(excess, state["net"]), reason, rule)
            state["net"] -= taken

        line.check(16)                                                                    # criterio 16
        line.rules.append(f"CRITERION_16_NATURE_CLASSIFIED:{it.category.value}")
        if it.category == CostCategory.CAPITAL_ASSETS and it.asset_nature == AssetNature.SERVICE:
            line.reject(16, "Un servizio non è classificabile come bene strumentale.", "CRITERION_16_MISCLASSIFIED:SERVICE_AS_CAPITAL_ASSET")
        if it.asset_nature is not None and it.asset_nature in rules.excluded_asset_natures:
            line.reject(16, f"Natura del bene ({it.asset_nature.value}) esclusa dal bando.", f"CRITERION_16_ASSET_NATURE_EXCLUDED:{it.asset_nature.value}")
        if rules.requires_eu_origin and it.category == CostCategory.CAPITAL_ASSETS and it.origin_eu is not None:
            if it.origin_eu:
                line.rules.append("CRITERION_16_EU_ORIGIN_OK")
            else:
                line.reject(16, "Il bando richiede beni prodotti in UE/SEE: origine non ammissibile.", "CRITERION_16_NON_EU_ORIGIN")
        if not it.source_c_ref.strip():
            line.reject(16, "Pezza d'appoggio (Fonte C) mancante: riga sospesa.", "CRITERION_16_SOURCE_DOCUMENT_MISSING", S.MISSING_DOCUMENTS)

        vat_left = vat                                                                    # criteri 53-54, 25
        if rules.vat_never_eligible and vat > 0:
            line.cut(54, vat, "Il bando ammette solo costi al netto di IVA: IVA esclusa.", "CRITERION_54_VAT_EXCLUDED_BY_BANDO")
            vat_left = ZERO
        elif it.vat_eur is not None and it.vat_recoverable is not None:
            if it.vat_recoverable:
                line.cut(54, vat, "IVA recuperabile: esclusa dai costi ammissibili.", f"CRITERION_54_RECOVERABLE_VAT_EXCLUDED:{fmt(vat)}")
                vat_left = ZERO
            else:
                line.ok(53, "CRITERION_53_UNRECOVERABLE_VAT_ELIGIBLE")
        if it.reverse_charge_applied is not None and it.category == CostCategory.CAPITAL_ASSETS:
            if it.reverse_charge_applied and vat_left > 0:
                line.cut(25, vat_left, "Reverse charge: l'IVA non va imputata due volte.", "CRITERION_25_REVERSE_CHARGE_VAT_EXCLUDED")
            else:
                line.ok(25, "CRITERION_25_REVERSE_CHARGE_OK")

        if it.category == CostCategory.CAPITAL_ASSETS:
            cls._assets(line, rules, net_cut, state)
        elif it.category == CostCategory.CONSULTING:
            cls._consulting(line, rules, net_cut, state)
        cls._subtype_rules(line, rules, net_cut, state)

        if it.category != CostCategory.PERSONNEL and it.supplier_durc_valid is not None:  # criterio 45
            if it.supplier_durc_valid:
                line.ok(45, "CRITERION_45_DURC_VALID")
            else:
                line.reject(45, "DURC del fornitore non regolare.", "CRITERION_45_DURC_NOT_VALID")

        if it.cig_required is not None:                                                   # criterio 51
            if not it.cig_required:
                line.ok(51, "CRITERION_51_CIG_NOT_REQUIRED")
            elif it.cig_code and _CIG_RE.match(it.cig_code.upper()):
                line.ok(51, "CRITERION_51_CIG_PRESENT")
            else:
                line.reject(51, "CIG obbligatorio mancante o non valido: riga sospesa.", "CRITERION_51_CIG_MISSING", S.MISSING_DOCUMENTS)

    @classmethod
    def _assets(cls, line: _Line, rules: GrantRuleSet, net_cut, state) -> None:
        it = line.item
        if it.leasing_interest_eur is not None:                                          # criterio 24
            if it.leasing_interest_eur > 0:
                net_cut(24, q(dec(it.leasing_interest_eur)), "Quota interessi del leasing esclusa dai costi rimborsabili.",
                        f"CRITERION_24_LEASING_INTEREST_EXCLUDED:{it.leasing_interest_eur}")
            else:
                line.ok(24, "CRITERION_24_NO_LEASING_INTEREST")
        if it.installation_cost_eur is not None and rules.max_installation_pct is not None:  # criterio 23
            inst = q(dec(it.installation_cost_eur))
            allowed = q((state["net"] - inst) * dec(rules.max_installation_pct))
            if inst > allowed:
                net_cut(23, inst - allowed, "Installazione/collaudo oltre la quota ammessa rispetto al valore capitale.",
                        f"CRITERION_23_INSTALLATION_CAPPED:MAX_{q(dec(rules.max_installation_pct) * 100)}%")
            else:
                line.ok(23, "CRITERION_23_INSTALLATION_WITHIN_LIMIT")
        if it.market_benchmark_eur is not None and rules.max_price_deviation_pct is not None:  # criterio 22
            limit = q(dec(it.market_benchmark_eur) * (1 + dec(rules.max_price_deviation_pct)))
            if state["net"] > limit:
                net_cut(22, state["net"] - limit, "Prezzo oltre il benchmark di mercato (Fonte B) maggiorato della tolleranza.",
                        f"CRITERION_22_PRICE_ABOVE_BENCHMARK:LIMIT_{fmt(limit)}")
            else:
                line.ok(22, "CRITERION_22_PRICE_CONGRUENT")
        if rules.equipment_depreciation_only and it.depreciation_rate_pct is None:
            line.reject(17, "Il bando ammette solo l'ammortamento del bene: indicare l'aliquota d'ammortamento.",
                        "CRITERION_17_DEPRECIATION_RATE_REQUIRED", S.MISSING_DOCUMENTS)
        if it.depreciation_rate_pct is not None:                                          # criteri 17-18
            line.ok(17, f"CRITERION_17_DEPRECIATION_RATE:{q(dec(it.depreciation_rate_pct) * 100)}%")
            eligible = q(state["net"] * dec(it.depreciation_rate_pct) * Decimal(it.duration_months) / TWELVE)
            if eligible < state["net"]:
                net_cut(18, state["net"] - eligible, "Ammortamento pro-rata temporis: ammessa solo la quota dei mesi di progetto.",
                        f"CRITERION_18_PRO_RATA_TEMPORIS:{it.duration_months}_MONTHS")
            else:
                line.ok(18, "CRITERION_18_FULL_PERIOD")
        if it.is_new is not None:                                                         # criterio 19
            if it.is_new or not rules.requires_new_asset:
                line.ok(19, "CRITERION_19_NEW_ASSET_OK")
            else:
                line.reject(19, "Il bando richiede un bene nuovo di fabbrica.", "CRITERION_19_NOT_NEW")
        if rules.requires_iot and it.iot_interconnected is not None:                      # criterio 20
            if it.iot_interconnected:
                line.ok(20, "CRITERION_20_IOT_INTERCONNECTED")
            else:
                line.reject(20, "Requisito di interconnessione IoT non soddisfatto.", "CRITERION_20_IOT_MISSING")
        if rules.min_energy_saving_pct is not None and it.energy_saving_pct is not None:  # criterio 21
            if dec(it.energy_saving_pct) >= dec(rules.min_energy_saving_pct):
                line.ok(21, "CRITERION_21_ENERGY_SAVING_OK")
            else:
                line.reject(21, "Risparmio energetico inferiore al minimo di bando.", f"CRITERION_21_ENERGY_SAVING_BELOW:{it.energy_saving_pct}")
        if rules.requires_dnsh and it.dnsh_compliant is not None:                         # criterio 28
            if it.dnsh_compliant:
                line.ok(28, "CRITERION_28_DNSH_OK")
            else:
                line.reject(28, "Principio DNSH non rispettato.", "CRITERION_28_DNSH_VIOLATED")
        if it.exclusive_use is not None:                                                  # criterio 29
            if it.exclusive_use:
                line.ok(29, "CRITERION_29_EXCLUSIVE_USE")
            else:
                line.reject(29, "Bene non ad uso esclusivo del progetto.", "CRITERION_29_NOT_EXCLUSIVE")
        if rules.appraisal_threshold_eur is not None and it.sworn_appraisal_present is not None:  # criterio 30
            if state["net"] <= dec(rules.appraisal_threshold_eur) or it.sworn_appraisal_present:
                line.ok(30, "CRITERION_30_APPRAISAL_OK_OR_NOT_REQUIRED")
            else:
                line.reject(30, "Perizia tecnica giurata mancante per bene sopra soglia: riga sospesa.", "CRITERION_30_APPRAISAL_MISSING", S.MISSING_DOCUMENTS)
        if rules.min_durability_months is not None and it.post_closure_commitment_months is not None:  # criterio 58
            if it.post_closure_commitment_months >= rules.min_durability_months:
                line.ok(58, "CRITERION_58_DURABILITY_OK")
            else:
                line.reject(58, f"Impegno post-chiusura ({it.post_closure_commitment_months} mesi) inferiore al minimo ({rules.min_durability_months}).",
                            "CRITERION_58_DURABILITY_TOO_SHORT")

    @classmethod
    def _consulting(cls, line: _Line, rules: GrantRuleSet, net_cut, state) -> None:
        it = line.item
        if it.supplier_related_party is not None and rules.require_independent_supplier:  # criterio 32
            if it.supplier_related_party:
                line.reject(32, "Fornitore parte correlata: spesa non ammissibile.", "CRITERION_32_RELATED_PARTY")
            else:
                line.ok(32, "CRITERION_32_SUPPLIER_INDEPENDENT")
        if it.daily_rate_eur is not None and it.days is not None and it.benchmark_daily_rate_eur is not None:  # criterio 33
            limit = q(min(dec(it.daily_rate_eur), dec(it.benchmark_daily_rate_eur)) * dec(it.days))
            if state["net"] > limit:
                net_cut(33, state["net"] - limit, "Tariffa normalizzata al benchmark di mercato (Fonte B).",
                        f"CRITERION_33_RATE_NORMALIZED:BENCHMARK_{it.benchmark_daily_rate_eur}_EUR/DAY")
            else:
                line.ok(33, "CRITERION_33_RATE_WITHIN_BENCHMARK")
        if rules.allowed_ateco_prefixes and it.supplier_ateco is not None:               # criterio 34
            if any(it.supplier_ateco.startswith(p) for p in rules.allowed_ateco_prefixes):
                line.ok(34, f"CRITERION_34_ATECO_CONGRUENT:{it.supplier_ateco}")
            else:
                line.reject(34, f"Codice ATECO {it.supplier_ateco} non congruo con l'attività ammessa.", f"CRITERION_34_ATECO_INCONGRUENT:{it.supplier_ateco}")
        if it.subcontracted is not None:                                                  # criterio 35
            if not it.subcontracted or (rules.subcontracting_allowed and it.subcontract_authorized):
                line.ok(35, "CRITERION_35_SUBCONTRACT_OK_OR_ABSENT")
            else:
                line.reject(35, "Subappalto non autorizzato dal regolamento di gara.", "CRITERION_35_SUBCONTRACT_NOT_AUTHORIZED")
        if it.travel_cost_eur is not None and it.travel_cost_eur > 0:                     # criterio 40
            if it.travel_included_in_fee is None:
                line.reject(40, "Spese di viaggio del consulente non chiarite (incluse o scorporate): riga sospesa.",
                            "CRITERION_40_TRAVEL_UNSPECIFIED", S.MISSING_DOCUMENTS)
            else:
                line.ok(40, f"CRITERION_40_TRAVEL_{'INCLUDED_IN_FEE' if it.travel_included_in_fee else 'ITEMIZED'}")

    @classmethod
    def _subtype_rules(cls, line: _Line, rules: GrantRuleSet, net_cut, state) -> None:
        it = line.item
        sub = it.expense_subtype
        if sub is None:
            return
        if sub == ExpenseSubtype.FINANCIAL_CHARGES:
            line.reject(16, "Interessi, oneri del debito, perdite di cambio e spese bancarie non sono costi ammissibili.",
                        "CRITERION_16_FINANCIAL_CHARGES_EXCLUDED")
        elif sub in (ExpenseSubtype.PENALTY, ExpenseSubtype.LEGAL_DISPUTE):                 # criterio 41
            line.reject(41, "Sanzioni, penali e contenziosi legali non sono ammissibili.", f"CRITERION_41_EXCLUDED:{sub.value}")
        elif sub == ExpenseSubtype.REPRESENTATION:                                        # criterio 44
            if it.project_related:
                line.ok(44, "CRITERION_44_REPRESENTATION_PROJECT_RELATED")
            else:
                line.reject(44, "Spesa di rappresentanza non finalizzata al progetto.", "CRITERION_44_REPRESENTATION_EXCLUDED")
        elif sub == ExpenseSubtype.MAINTENANCE_ORDINARY:                                  # criterio 27
            line.reject(27, "Manutenzione ordinaria: non ammissibile.", "CRITERION_27_ORDINARY_MAINTENANCE_EXCLUDED")
        elif sub == ExpenseSubtype.MAINTENANCE_EXTRAORDINARY:
            line.ok(27, "CRITERION_27_EXTRAORDINARY_MAINTENANCE_ELIGIBLE")
        elif sub == ExpenseSubtype.RENT:                                                  # criterio 42
            if it.rent_sqm_project and it.rent_sqm_total and it.rent_months_active is not None:
                share = min(Decimal(1), dec(it.rent_sqm_project) / dec(it.rent_sqm_total)) * min(Decimal(1), Decimal(it.rent_months_active) / Decimal(it.duration_months))
                eligible = q(state["net"] * share)
                if eligible < state["net"]:
                    net_cut(42, state["net"] - eligible, "Canone ammesso in proporzione a metri quadri e mesi di attività.",
                            f"CRITERION_42_RENT_PRO_RATA:{it.rent_sqm_project}/{it.rent_sqm_total}_SQM")
                else:
                    line.ok(42, "CRITERION_42_RENT_FULLY_ATTRIBUTABLE")
        elif sub == ExpenseSubtype.UTILITIES:                                             # criterio 43
            if it.allocation_method and it.allocation_method.strip():
                line.ok(43, "CRITERION_43_OBJECTIVE_ALLOCATION_KEY")
            else:
                line.reject(43, "Utenze senza criterio di ripartizione oggettivo: riga sospesa.", "CRITERION_43_ALLOCATION_KEY_MISSING", S.MISSING_DOCUMENTS)
        elif sub == ExpenseSubtype.GUARANTEE and rules.guarantee_costs_eligible is not None:  # criterio 38
            if rules.guarantee_costs_eligible:
                line.ok(38, "CRITERION_38_GUARANTEE_ELIGIBLE")
            else:
                line.reject(38, "Costi di fideiussione/assicurazione non ammessi dal bando.", "CRITERION_38_GUARANTEE_NOT_ELIGIBLE")
        elif sub == ExpenseSubtype.AUDIT and rules.max_audit_cost_eur is not None:        # criterio 39
            cap = q(dec(rules.max_audit_cost_eur))
            if state["net"] > cap:
                net_cut(39, state["net"] - cap, "Costo di revisione oltre il limite fissato dal bando.", f"CRITERION_39_AUDIT_CAP:{fmt(cap)}")
            else:
                line.ok(39, "CRITERION_39_AUDIT_WITHIN_LIMIT")

    # ------------------------------------------------------------------ per-line: general (46, 47, 50, 52, 57)
    @classmethod
    def _general(cls, line: _Line, rules: GrantRuleSet) -> None:
        it = line.item
        if rules.eligible_categories is not None:                                         # criterio 16: categoria ammessa dal bando
            if it.category in rules.eligible_categories:
                line.ok(16, f"CRITERION_16_CATEGORY_ELIGIBLE:{it.category.value}")
            else:
                line.reject(16, f"La categoria {it.category.value} non è ammissibile in questo bando "
                                f"(ammesse: {', '.join(c.value for c in rules.eligible_categories)}).",
                            f"CRITERION_16_CATEGORY_NOT_ELIGIBLE:{it.category.value}")
        if it.expense_date is not None and (rules.eligibility_start or rules.eligibility_end):  # criterio 46
            before = rules.eligibility_start and it.expense_date < rules.eligibility_start
            after = rules.eligibility_end and it.expense_date > rules.eligibility_end
            if before or after:
                line.reject(46, f"Spesa del {it.expense_date.isoformat()} fuori dalla finestra di ammissibilità del bando.",
                            f"CRITERION_46_OUT_OF_WINDOW:{it.expense_date.isoformat()}")
            else:
                line.ok(46, "CRITERION_46_DATE_ELIGIBLE")
        if it.funding_ids is not None:                                                    # criterio 47
            clash = sorted(set(it.funding_ids) & set(rules.non_cumulable_funding_ids))
            if clash:
                line.reject(47, f"Double funding: la spesa è già coperta da {', '.join(clash)}, non cumulabile con questo bando.",
                            f"CRITERION_47_DOUBLE_FUNDING:{','.join(clash)}")
            else:
                line.ok(47, "CRITERION_47_NO_DOUBLE_FUNDING")
        if rules.requires_cup:                                                            # criterio 50
            if it.cup_code and _CUP_RE.match(it.cup_code.upper()):
                line.ok(50, "CRITERION_50_CUP_PRESENT")
            else:
                line.reject(50, "CUP obbligatorio mancante o non valido: riga sospesa.", "CRITERION_50_CUP_MISSING", S.MISSING_DOCUMENTS)
        if it.payment_method is not None:                                                 # criterio 52
            blocked = {m.upper() for m in rules.blocked_payment_methods}
            if it.payment_method.upper() in blocked:
                line.reject(52, f"Metodo di pagamento {it.payment_method.upper()} non ammissibile (tracciabilità).",
                            f"CRITERION_52_PAYMENT_BLOCKED:{it.payment_method.upper()}")
            else:
                line.ok(52, f"CRITERION_52_PAYMENT_TRACEABLE:{it.payment_method.upper()}")
        if rules.requires_milestones:                                                     # criterio 57
            if it.milestone_id and it.milestone_id.strip():
                line.ok(57, f"CRITERION_57_MILESTONE_ASSIGNED:{it.milestone_id}")
            else:
                line.reject(57, "Voce non associata a una milestone/SAL di rendicontazione: riga sospesa.", "CRITERION_57_MILESTONE_MISSING", S.MISSING_DOCUMENTS)

    # ------------------------------------------------------------------ hashing
    @staticmethod
    def _seal(line: _Line, rules: GrantRuleSet) -> CostItemValidated:
        """Costruisce la riga finale con l'hash canonico (Fonte C + Fonte B versionata + Fonte A + calcolo)."""
        payload = {
            "item_id": line.item.item_id, "category": line.item.category.value, "source_c_ref": line.item.source_c_ref,
            "rule_version_hash": rules.rule_version_hash, "fonte_b_ref": line.breakdown.get("ccnl_table_ref"),
            "applied_rules": line.rules, "original_cost_eur": fmt(line.original), "computed_cost_eur": fmt(line.approved),
            "status": line.status.value,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        not_evaluated = sorted(n for n in applicable_criteria(line.item) if n not in line.checked)
        return CostItemValidated(
            item_id=line.item.item_id, description=line.item.description, category=line.item.category, status=line.status,
            original_cost_eur=_f(line.original), computed_cost_eur=_f(line.approved),
            hourly_rate_computed=_f(line.hourly), hourly_rate_cap=_f(line.hourly_cap),
            rejection_reason="; ".join(line.reasons) or None, applied_rules=list(line.rules),
            criteria_checked=sorted(line.checked), criteria_failed=sorted(line.failed), criteria_not_evaluated=not_evaluated,
            breakdown=CostBreakdown(**line.breakdown), item_hash_sha256=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        )

    # ------------------------------------------------------------------ share caps (31, 36, 37, 26)
    @staticmethod
    def _apportion(amounts: List[Decimal], target: Decimal) -> List[Decimal]:
        """Riduce ``amounts`` proporzionalmente fino a sommare ``target`` (largest remainder, al centesimo)."""
        total = sum(amounts, ZERO)
        if total == 0:
            return [ZERO for _ in amounts]
        exact = [a * target / total for a in amounts]
        floors = [x.quantize(CENT, rounding=ROUND_DOWN) for x in exact]
        leftover = int(((target - sum(floors, ZERO)) / CENT).to_integral_value(rounding=ROUND_HALF_UP))
        order = sorted(range(len(amounts)), key=lambda i: (-(exact[i] - floors[i]), i))
        for i in order[:leftover]:
            floors[i] += CENT
        return floors

    @staticmethod
    def solve_share_caps(base: Decimal, groups: Sequence[Tuple[Decimal, Decimal]]) -> List[Decimal]:
        """Massimali % sul TOTALE finale: per ogni gruppo k, G'_k <= p_k * T', con T' = base + sum G'.

        T' dipende dai G'_k stessi: si risolve in forma chiusa provando tutti i sottoinsiemi S di gruppi "al tetto"
        (T = (base + sum_{k not in S} G_k) / (1 - sum_{k in S} p_k)) e scegliendo quello coerente. Con arrotondamento
        per difetto + verifica finale i tetti non sono mai superati.
        """
        n = len(groups)
        result = [g for g, _ in groups]
        for flags in product((False, True), repeat=n):
            denom = 1 - sum((groups[k][1] for k in range(n) if flags[k]), Decimal(0))
            if denom <= 0:
                continue
            total = (base + sum((groups[k][0] for k in range(n) if not flags[k]), Decimal(0))) / denom
            if all((groups[k][0] >= groups[k][1] * total) if flags[k] else (groups[k][0] <= groups[k][1] * total) for k in range(n)):
                result = [min(groups[k][0], q_down(groups[k][1] * total)) if flags[k] else groups[k][0] for k in range(n)]
                break
        for k in range(n):  # guardia finale contro residui di arrotondamento sul totale ricalcolato
            while result[k] > groups[k][1] * (base + sum(result, Decimal(0))):
                result[k] -= CENT
        return [max(r, ZERO) for r in result]

    @classmethod
    def solve_caps(cls, base: Decimal, consulting: Decimal, overhead: Decimal, pc: Decimal, po: Decimal) -> Tuple[Decimal, Decimal]:
        c, o = cls.solve_share_caps(base, [(consulting, pc), (overhead, po)])
        return c, o

    @classmethod
    def _apply_share_caps(cls, lines: List[_Line], rules: GrantRuleSet) -> List[Dict]:
        """Tasso forfettario (crit. 36) e massimali % sul totale finale (crit. 26, 31, 36, 37). Restituisce il dettaglio per il trace."""
        spec: Dict[str, Tuple[int, Decimal]] = {}
        if rules.max_consulting_percentage is not None:
            spec["CONSULTING"] = (31, dec(rules.max_consulting_percentage))
        if rules.max_overhead_percentage is not None:
            spec["OVERHEAD"] = (36, dec(rules.max_overhead_percentage))
        if rules.max_communication_pct is not None:
            spec["COMMUNICATION"] = (37, dec(rules.max_communication_pct))
        if rules.max_immaterial_pct is not None:
            spec["IMMATERIAL"] = (26, dec(rules.max_immaterial_pct))

        def group_of(ln: _Line) -> Optional[str]:
            it = ln.item
            if "COMMUNICATION" in spec and it.expense_subtype == ExpenseSubtype.COMMUNICATION:
                return "COMMUNICATION"
            if "IMMATERIAL" in spec and it.category == CostCategory.CAPITAL_ASSETS and it.asset_nature in (AssetNature.SOFTWARE, AssetNature.IMMATERIAL):
                return "IMMATERIAL"
            if "CONSULTING" in spec and it.category == CostCategory.CONSULTING:
                return "CONSULTING"
            if "OVERHEAD" in spec and it.category == CostCategory.OVERHEAD:
                return "OVERHEAD"
            return None

        live = [ln for ln in lines if ln.is_live]

        # Criterio 36 — tasso forfettario: le spese generali non superano una quota di una base di costi diretti.
        flat = rules.overhead_flat_rate_pct
        overhead_lines = [ln for ln in live if ln.item.category == CostCategory.OVERHEAD]
        if flat is not None and overhead_lines:
            if rules.overhead_flat_base == FlatBase.PERSONNEL:
                base_amount = sum((ln.approved for ln in live if ln.item.category == CostCategory.PERSONNEL), ZERO)
                base_label = "dei costi di personale"
            else:
                base_amount = sum((ln.approved for ln in live if ln.item.category != CostCategory.OVERHEAD and not ln.item.subcontracted), ZERO)
                base_label = "dei costi diretti (esclusi i subappalti)"
            limit = q_down(base_amount * dec(flat))
            current = sum((ln.approved for ln in overhead_lines), ZERO)
            for ln in overhead_lines:
                ln.check(36)
            if current > limit:
                for ln, new in zip(overhead_lines, cls._apportion([ln.approved for ln in overhead_lines], limit)):
                    if new != ln.approved:
                        ln.cut(36, ln.approved - new, f"Spese generali forfettarie limitate al {q(dec(flat) * 100)}% {base_label}.",
                               f"CRITERION_36_FLAT_RATE:MAX_{q(dec(flat) * 100)}%_OF_{rules.overhead_flat_base.value}")
            else:
                for ln in overhead_lines:
                    ln.rules.append(f"CRITERION_36_FLAT_RATE_COMPLIANT:MAX_{q(dec(flat) * 100)}%")
            live = [ln for ln in lines if ln.is_live]

        members: Dict[str, List[_Line]] = {k: [] for k in spec}
        base = ZERO
        for ln in live:
            g = group_of(ln)
            if g:
                members[g].append(ln)
            else:
                base += ln.approved

        names = [k for k in spec if members[k]]
        amounts = [(sum((ln.approved for ln in members[k]), ZERO), spec[k][1]) for k in names]
        new_totals = cls.solve_share_caps(base, amounts) if names else []
        info: List[Dict] = []
        total_final = base + sum(new_totals, ZERO)
        for k, (old, pct), new in zip(names, amounts, new_totals):
            criterion = spec[k][0]
            info.append({"group": k, "criterion": criterion, "cap_pct": float(pct), "requested_eur": _f(old), "allowed_eur": _f(new),
                         "base_eur": _f(base), "total_final_eur": _f(total_final)})
            for ln in members[k]:
                ln.check(criterion)
                ln.breakdown["budget_cap_pct"] = float(pct)
            if new == old:
                for ln in members[k]:
                    ln.rules.append(f"CRITERION_{criterion}_{k}_CAP_COMPLIANT:MAX_{q(pct * 100)}%")
                continue
            for ln, amount in zip(members[k], cls._apportion([ln.approved for ln in members[k]], new)):
                if amount != ln.approved:
                    ln.cut(criterion, ln.approved - amount,
                           f"Voce {k} riportata al massimale del {q(pct * 100)}% del budget totale previsto dal bando (importo ammesso {fmt(amount)} €).",
                           f"CRITERION_{criterion}_{k}_CAP_EXCEEDED:MAX_{q(pct * 100)}%_OF_TOTAL_BUDGET")
        return info

    @classmethod
    def _apply_fte_aggregation(cls, lines: List[_Line]) -> None:
        """Criterio 8: la somma degli FTE dello stesso lavoratore non supera il 100% (conservativo: righe concomitanti)."""
        cumulative: Dict[str, Decimal] = {}
        for ln in lines:
            token = ln.item.employee_token
            if not token or ln.item.category != CostCategory.PERSONNEL or not ln.is_live:
                continue
            total = cumulative.get(token, Decimal(0)) + dec(ln.item.fte_allocation)
            if total > 1:
                ln.reject(8, f"FTE cumulato del lavoratore ({total}) superiore al 100% sul budget: riga respinta.",
                          f"CRITERION_08_FTE_SUM_EXCEEDS_100:{total}")
            else:
                cumulative[token] = total

    # ------------------------------------------------------------------ budget-level checks (48, 49, 55, 56, 60)
    @classmethod
    def _budget_checks(cls, lines: List[_Line], rules: GrantRuleSet, liquidity: Optional[float],
                       baseline: Optional[Dict[CostCategory, float]]) -> List[BudgetCheck]:
        def chk(n: int, status: str, msg: str) -> BudgetCheck:
            return BudgetCheck(criterion=n, title=CRITERIA_TITLES[n], status=status, message=msg)

        approved_total = sum((ln.approved for ln in lines), ZERO)
        checks: List[BudgetCheck] = []

        other = [ln.item.other_aid_eur for ln in lines if ln.is_live and ln.item.other_aid_eur is not None]     # 48
        if rules.contribution_rate_pct is not None and rules.max_aid_intensity_pct is not None and other and approved_total > 0:
            other_total = sum((dec(x) for x in other), Decimal(0))
            intensity = dec(rules.contribution_rate_pct) + other_total / approved_total
            limit = dec(rules.max_aid_intensity_pct)
            if intensity > limit:
                max_rate = max(ZERO, limit - other_total / approved_total)
                checks.append(chk(48, "FAIL", f"Intensità di aiuto cumulata {q(intensity * 100)}% oltre il massimo {q(limit * 100)}%: "
                                              f"il contributo richiedibile non supera il {q_down(max_rate * 100)}% dei costi ammessi."))
            else:
                checks.append(chk(48, "PASS", f"Intensità di aiuto cumulata {q(intensity * 100)}% entro il massimo {q(limit * 100)}%."))
        else:
            checks.append(chk(48, "NOT_EVALUATED", "Servono contribution_rate_pct, max_aid_intensity_pct e other_aid_eur sulle righe."))

        if rules.contribution_rate_pct is not None and rules.de_minimis_residual_eur is not None:               # 49
            contribution = q(approved_total * dec(rules.contribution_rate_pct))
            residual = q(dec(rules.de_minimis_residual_eur))
            if contribution > residual:
                base_max = q_down(residual / dec(rules.contribution_rate_pct))
                checks.append(chk(49, "FAIL", f"Contributo richiesto {fmt(contribution)} € oltre il plafond de minimis residuo {fmt(residual)} €: "
                                              f"base di costi ammessi massima {fmt(base_max)} €."))
            else:
                checks.append(chk(49, "PASS", f"Contributo {fmt(contribution)} € entro il plafond de minimis residuo {fmt(residual)} €."))
        else:
            checks.append(chk(49, "NOT_EVALUATED", "Servono contribution_rate_pct e de_minimis_residual_eur."))

        if rules.reimbursement_lag_months is not None and liquidity is not None:                                # 55
            duration = max((ln.item.duration_months for ln in lines), default=12)
            exposure = q(approved_total * (1 - dec(rules.advance_pct)) * min(Decimal(1), Decimal(rules.reimbursement_lag_months) / Decimal(duration)))
            if dec(liquidity) >= exposure:
                checks.append(chk(55, "PASS", f"Liquidità {fmt(dec(liquidity))} € sufficiente a coprire l'esposizione {fmt(exposure)} € fino al rimborso."))
            else:
                checks.append(chk(55, "FAIL", f"Liquidità {fmt(dec(liquidity))} € inferiore all'esposizione {fmt(exposure)} € tra spesa e rimborso."))
        else:
            checks.append(chk(55, "NOT_EVALUATED", "Servono reimbursement_lag_months e entity_liquidity_eur."))

        if baseline and rules.max_inter_chapter_variation_pct is not None:                                      # 56
            tol, breaches = dec(rules.max_inter_chapter_variation_pct), []
            for raw_cat, ref in baseline.items():
                cat = CostCategory(raw_cat)
                now = sum((ln.approved for ln in lines if ln.item.category == cat), ZERO)
                if dec(ref) > 0 and abs(now - dec(ref)) / dec(ref) > tol:
                    breaches.append(f"{cat.value} ({fmt(now)} € vs {fmt(dec(ref))} €)")
            checks.append(chk(56, "FAIL" if breaches else "PASS",
                              ("Variazione oltre " + f"{q(tol * 100)}%: " + "; ".join(breaches)) if breaches else f"Variazioni tra capitoli entro {q(tol * 100)}%."))
        else:
            checks.append(chk(56, "NOT_EVALUATED", "Servono baseline_totals e max_inter_chapter_variation_pct."))

        coherent = all(ZERO <= ln.approved <= ln.original for ln in lines)                                      # 60
        reductions = sum((ln.original - ln.approved for ln in lines), ZERO)
        coherent = coherent and (sum((ln.original for ln in lines), ZERO) - reductions == approved_total)
        checks.append(chk(60, "PASS" if coherent else "FAIL",
                          "Totali coerenti: nessun importo ammesso supera l'originale e ammesso + rettifiche = richiesto." if coherent
                          else "Incoerenza tra importi ammessi, originali e rettifiche."))
        return checks

    # ------------------------------------------------------------------ public API
    @classmethod
    def _compute_line(cls, item: CostItemInput, rules: GrantRuleSet) -> _Line:
        line = _Line(item=item)
        line.breakdown = {"source_c_ref": item.source_c_ref, "rule_version_hash": rules.rule_version_hash}
        if item.category == CostCategory.PERSONNEL:
            cls._compute_personnel(line, rules)
        else:
            cls._compute_non_personnel(line, rules)
            line.breakdown["annual_cost_eur"] = _f(line.original)
        cls._general(line, rules)
        return line

    _SHARE_CAP_CRITERIA = {26, 31, 36, 37}

    @classmethod
    def _build_steps(cls, lines: List[_Line]) -> List[TraceStep]:
        """Ordina i controlli di ogni riga nell'ordine di valutazione e ricostruisce l'importo dopo ciascun passo."""
        steps: List[TraceStep] = []
        for ln in lines:
            by_crit: Dict[int, List[Dict]] = {}
            for a in ln.adjustments:
                by_crit.setdefault(a["criterion"], []).append(a)
            running = ln.original
            sequence: List[Tuple[int, Optional[Dict]]] = []
            for n in ln.checked:
                adjs = by_crit.pop(n, None)
                if adjs:
                    sequence.extend((n, a) for a in adjs)
                else:
                    sequence.append((n, None))
            for n, adjs in by_crit.items():
                sequence.extend((n, a) for a in adjs)
            for n, adj in sequence:
                stage = "SHARE_CAPS" if n in cls._SHARE_CAP_CRITERIA else "LINE_CRITERIA"
                if adj is None:
                    steps.append(TraceStep(seq=0, stage=stage, item_id=ln.item.item_id, criterion=n, outcome="PASS", delta_eur=0.0,
                                           amount_after_eur=_f(running), note=CRITERIA_TITLES.get(n, "")))
                else:
                    running += adj["delta"]
                    steps.append(TraceStep(seq=0, stage=stage, item_id=ln.item.item_id, criterion=n, outcome=adj["kind"],
                                           delta_eur=_f(adj["delta"]), amount_after_eur=_f(running), note=adj["note"]))
        for i, st in enumerate(steps, 1):
            st.seq = i
        return steps

    @classmethod
    def analyze_budget(cls, items: List[CostItemInput], rules: GrantRuleSet, entity_liquidity_eur: Optional[float] = None,
                       baseline_totals: Optional[Dict[CostCategory, float]] = None
                       ) -> Tuple[List[CostItemValidated], List[BudgetCheck], Dict]:
        """Pipeline completa con traccia: criteri di riga -> FTE cumulato -> massimali -> criteri di budget -> sigillo hash.

        Restituisce (righe, controlli di budget, trace parziale con fasi, passi e dettagli dei massimali).
        """
        stages: List[PipelineStage] = []
        last = time.perf_counter()

        def mark(key: str, label: str, detail: str) -> None:
            nonlocal last
            now = time.perf_counter()
            stages.append(PipelineStage(key=key, label=label, duration_ms=round((now - last) * 1000, 3), detail=detail))
            last = now

        lines = [cls._compute_line(item, rules) for item in items]
        mark("LINE_CRITERIA", "Controlli su ogni voce (regole, tabelle, documenti)", f"{len(lines)} voci · {sum(len(ln.checked) for ln in lines)} controlli eseguiti")
        cls._apply_fte_aggregation(lines)
        mark("FTE", "Tempo dedicato per persona (controllo 8)", f"{sum(1 for ln in lines if 8 in ln.failed)} voci respinte")
        caps = cls._apply_share_caps(lines, rules)
        mark("SHARE_CAPS", "Limiti in % sul totale finale (controlli 26, 31, 36, 37)", f"{len(caps)} gruppi di spesa risolti")
        checks = cls._budget_checks(lines, rules, entity_liquidity_eur, baseline_totals)
        mark("BUDGET_CHECKS", "Controlli sull'intero budget (48, 49, 55, 56, 60)", f"{sum(1 for c in checks if c.status != 'NOT_EVALUATED')} su {len(checks)} valutati")
        steps = cls._build_steps(lines)
        sealed = [cls._seal(ln, rules) for ln in lines]
        mark("HASH", "Impronta di ogni voce (SHA-256)", f"{len(sealed)} impronte")
        return sealed, checks, {"stages": stages, "steps": steps, "share_caps": caps}

    @classmethod
    def evaluate_budget(cls, items: List[CostItemInput], rules: GrantRuleSet, entity_liquidity_eur: Optional[float] = None,
                        baseline_totals: Optional[Dict[CostCategory, float]] = None) -> Tuple[List[CostItemValidated], List[BudgetCheck]]:
        sealed, checks, _ = cls.analyze_budget(items, rules, entity_liquidity_eur, baseline_totals)
        return sealed, checks

    @classmethod
    def validate_budget(cls, items: List[CostItemInput], rules: GrantRuleSet, **kwargs) -> List[CostItemValidated]:
        return cls.evaluate_budget(items, rules, **kwargs)[0]

    @classmethod
    def validate_personnel_item(cls, item: CostItemInput, rules: GrantRuleSet) -> CostItemValidated:
        """Validazione di una singola riga (criteri di riga, senza massimali di budget), sigillata."""
        return cls._seal(cls._compute_line(item, rules), rules)

    @staticmethod
    def conformity_score(items: List[CostItemValidated], budget_checks: Sequence[BudgetCheck] = ()) -> int:
        """% (per difetto) di controlli superati sul totale dei controlli realmente eseguiti (righe + budget)."""
        total = sum(len(i.criteria_checked) for i in items)
        failed = sum(len(i.criteria_failed) for i in items)
        for c in budget_checks:
            if c.status != "NOT_EVALUATED":
                total += 1
                failed += 1 if c.status == "FAIL" else 0
        if total == 0:
            return 100
        return max(0, min(100, (100 * (total - failed)) // total))
