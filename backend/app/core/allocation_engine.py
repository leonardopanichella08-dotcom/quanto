"""Allocazione annuale multi-fonte (Missione Due, Modulo 12) con ottimizzazione vincolata esatta.

Formulazione (MILP, risolto con HiGHS tramite ``scipy.optimize.milp``):

- x_pj in [0, cov_pj]: quota della (sotto)voce p coperta dal fondo j; z_pj binaria di utilizzo;
- sum_j x_pj <= 1                                        (una voce non è coperta oltre il 100%);
- sum_p a_p x_pj <= dotazione_j                          (tetto del fondo);
- sum_{p in cat c} a_p x_pj <= share_cj * sum_p a_p x_pj  (massimali % per categoria, criteri 31/36);
- z_pj + z_pk <= 1 per fondi non cumulabili j,k           (double funding, criterio 47);
- sum_{p, j in DM} a_p x_pj <= plafond de minimis residuo (criterio 49);
- finestre di attività mensili dei fondi (criterio 46).

Le spese senza mese sono espanse in 12 mensilità solo se un fondo ha una finestra di attività ridotta
(così la finestra si applica a ogni mensilità); altrimenti restano annuali e il piano mensile è ripartito
a posteriori, senza artefatti di arrotondamento.

Il solver lavora in euro (float) solo per trovare la struttura ottima; gli importi finali sono interi
in centesimi, arrotondati per difetto e RI-VERIFICATI in aritmetica esatta contro tutti i vincoli
(con riparazione deterministica dei residui di arrotondamento).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal
from fractions import Fraction
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

from app.models.allocation import (
    AllocationLine, AllocationOptimizationRequest, AllocationResponse, FundCoverage, FundingLine,
    FundUsage, MonthlyPlanEntry, OptimizationTarget,
)
from app.models.schemas import CostCategory

TIME_LIMIT_S = 20.0
TIE_WEIGHT = 1e-3  # a parità di risparmio preferisce meno coppie voce-fondo


def _cents(value: float) -> int:
    return int((Decimal(str(value)) * 100).to_integral_value(rounding=ROUND_DOWN))


def _eur(cents: int) -> float:
    return float(Decimal(cents) / 100)


def _spread(cents: int) -> List[int]:
    """Ripartisce un importo su 12 mesi in centesimi interi (il resto va ai primi mesi)."""
    base, rem = divmod(cents, 12)
    return [base + (1 if m < rem else 0) for m in range(12)]


@dataclass
class _SubLine:
    item_id: str
    category: CostCategory
    month: int
    cents: int


@dataclass
class _Pair:
    s: int
    j: int
    cap_cents: int  # copertura massima consentita dall'intensità del fondo
    intensity: float


class _MILP:
    def __init__(self) -> None:
        self.lb: List[float] = []
        self.ub: List[float] = []
        self.integer: List[int] = []
        self.rows: List[Tuple[Dict[int, float], float, float]] = []

    def var(self, lb: float, ub: float, integer: bool = False) -> int:
        self.lb.append(lb)
        self.ub.append(ub)
        self.integer.append(1 if integer else 0)
        return len(self.lb) - 1

    def con(self, coeffs: Dict[int, float], lo: float = -np.inf, hi: float = np.inf) -> None:
        self.rows.append((coeffs, lo, hi))

    def solve(self, objective: Dict[int, float], extra: Optional[List[Tuple[Dict[int, float], float, float]]] = None) -> Tuple[np.ndarray, bool]:
        rows = self.rows + (extra or [])
        n = len(self.lb)
        c = np.zeros(n)
        for k, v in objective.items():
            c[k] = v
        r_idx, c_idx, data = [], [], []
        for i, (coeffs, _, _) in enumerate(rows):
            for k, v in coeffs.items():
                r_idx.append(i); c_idx.append(k); data.append(v)
        constraints = []
        if rows:
            a = coo_matrix((data, (r_idx, c_idx)), shape=(len(rows), n)).tocsr()
            constraints = [LinearConstraint(a, [r[1] for r in rows], [r[2] for r in rows])]
        res = milp(c, constraints=constraints, integrality=np.array(self.integer),
                   bounds=Bounds(self.lb, self.ub), options={"time_limit": TIME_LIMIT_S, "mip_rel_gap": 0.0})
        if res.x is None:
            raise RuntimeError(f"Risolutore senza soluzione ammissibile: {res.message}")
        return res.x, res.status == 0


class AllocationOptimizerEngine:
    @classmethod
    def optimize_annual_allocation(cls, req: AllocationOptimizationRequest) -> AllocationResponse:
        excluded = set(req.excluded_funds)
        funds = [f for f in req.available_funding_lines if f.fund_id not in excluded]

        # ---- sotto-voci (interi in centesimi). Le spese senza mese si espandono in 12 mensilità solo se
        # qualche fondo ha una finestra di attività ridotta; altrimenti restano annuali (month=0, nessun
        # artefatto di arrotondamento) e il piano mensile è ripartito a posteriori.
        windowed = any(f.active_from_month != 1 or f.active_to_month != 12 for f in funds)
        subs: List[_SubLine] = []
        for e in req.historical_expenses:
            total = _cents(e.amount_eur)
            if e.month is not None:
                subs.append(_SubLine(e.item_id, e.category, e.month, total))
            elif windowed:
                subs.extend(_SubLine(e.item_id, e.category, m, c) for m, c in enumerate(_spread(total), 1))
            else:
                subs.append(_SubLine(e.item_id, e.category, 0, total))

        # ---- coppie ammissibili (voce, fondo)
        pairs: List[_Pair] = []
        for s, sub in enumerate(subs):
            if sub.cents == 0:
                continue
            for j, f in enumerate(funds):
                if sub.category not in f.allowed_categories or (sub.month and not f.active_from_month <= sub.month <= f.active_to_month):
                    continue
                cov = f.category_coverage_pct.get(sub.category, f.coverage_pct)
                pairs.append(_Pair(s, j, int((Decimal(str(cov)) * sub.cents).to_integral_value(rounding=ROUND_DOWN)), cov))

        stages = 0
        covered: Dict[int, int] = {}
        solved_optimal = True
        if pairs:
            covered, solved_optimal, stages = cls._solve(req, subs, funds, pairs)
            covered = cls._repair(covered, subs, funds, pairs, req.de_minimis_residual_eur)
        return cls._build_response(req, subs, funds, pairs, covered, excluded, stages, solved_optimal)

    # ------------------------------------------------------------------ MILP
    @classmethod
    def _solve(cls, req, subs, funds, pairs) -> Tuple[Dict[int, int], bool, int]:
        m = _MILP()
        amt = [subs[p.s].cents / 100 for p in pairs]  # euro
        x = [m.var(0.0, p.intensity) for p in pairs]
        z = [m.var(0.0, 1.0, integer=True) for _ in pairs]
        by_sub: Dict[int, List[int]] = {}
        by_fund: Dict[int, List[int]] = {}
        for i, p in enumerate(pairs):
            by_sub.setdefault(p.s, []).append(i)
            by_fund.setdefault(p.j, []).append(i)
            m.con({x[i]: 1.0, z[i]: -p.intensity}, hi=0.0)            # x <= intensità * z
        for idxs in by_sub.values():
            m.con({x[i]: 1.0 for i in idxs}, hi=1.0)                  # copertura totale voce <= 100%
        for j, idxs in by_fund.items():
            f = funds[j]
            if f.max_total_eur is not None:
                m.con({x[i]: amt[i] for i in idxs}, hi=f.max_total_eur)
            for cat, share in f.category_max_share.items():
                if share >= 1:
                    continue
                coeffs = {x[i]: amt[i] * ((1.0 if subs[pairs[i].s].category == cat else 0.0) - share) for i in idxs}
                m.con(coeffs, hi=0.0)
        # non cumulabilità a livello di voce
        idx_of = {(p.s, p.j): i for i, p in enumerate(pairs)}
        position = {f.fund_id: j for j, f in enumerate(funds)}
        exclusive_pairs = set()
        for j, f in enumerate(funds):
            for other in f.excludes:
                k = position.get(other)
                if k is not None and k != j:
                    exclusive_pairs.add((min(j, k), max(j, k)))  # l'esclusione vale in entrambe le direzioni
        for j, k in sorted(exclusive_pairs):
            for s in by_sub:
                a, b = idx_of.get((s, j)), idx_of.get((s, k))
                if a is not None and b is not None:
                    m.con({z[a]: 1.0, z[b]: 1.0}, hi=1.0)
        # de minimis
        dm_idx = [i for i, p in enumerate(pairs) if funds[p.j].de_minimis]
        if dm_idx:
            m.con({x[i]: amt[i] for i in dm_idx}, hi=req.de_minimis_residual_eur or 0.0)

        covered_expr = {x[i]: amt[i] for i in range(len(pairs))}
        neg_covered = {k: -v for k, v in covered_expr.items()}
        tie = {z[i]: TIE_WEIGHT for i in range(len(pairs))}
        stages = 0
        optimal = True

        def run(obj, extra=None):
            nonlocal stages, optimal
            stages += 1
            sol, ok = m.solve(obj, extra)
            optimal = optimal and ok
            return sol

        target = req.optimization_target
        sol = run({**neg_covered, **tie})                                     # stadio 1: massimo risparmio
        best_cov = sum(covered_expr[k] * sol[k] for k in covered_expr)
        if target == OptimizationTarget.MAXIMIZE_COVERED_ITEMS:
            w = {s: m.var(0.0, 1.0, integer=True) for s in by_sub}
            for s, idxs in by_sub.items():
                m.con({**{x[i]: -1.0 for i in idxs}, w[s]: 0.01}, hi=0.0)     # w=1 => >= 1% coperto
            sol = run({w[s]: -1.0 for s in by_sub})
            n_items = round(sum(sol[w[s]] for s in by_sub))
            sol = run({**neg_covered, **tie}, [({w[s]: 1.0 for s in by_sub}, n_items - 0.5, np.inf)])
        elif target == OptimizationTarget.MINIMIZE_FUNDS_INVOLVED:
            y = {j: m.var(0.0, 1.0, integer=True) for j in by_fund}
            for i, p in enumerate(pairs):
                m.con({z[i]: 1.0, y[p.j]: -1.0}, hi=0.0)
            floor_cov = req.min_saving_ratio * best_cov - 1e-6 * max(1.0, best_cov)
            keep = ({**covered_expr}, floor_cov, np.inf)
            sol = run({y[j]: 1.0 for j in by_fund}, [keep])
            n_funds = round(sum(sol[y[j]] for j in by_fund))
            sol = run({**neg_covered, **tie}, [keep, ({y[j]: 1.0 for j in by_fund}, -np.inf, n_funds + 0.5)])

        result: Dict[int, int] = {}
        for i, p in enumerate(pairs):
            v = float(min(max(sol[x[i]], 0.0), p.intensity))
            if v < 1e-9:
                continue
            c = min(int(math.floor(subs[p.s].cents * v + 1e-3)), p.cap_cents)
            if c > 0:
                result[i] = c
        return result, optimal, stages

    # ------------------------------------------------------------------ exact repair
    @staticmethod
    def _repair(covered: Dict[int, int], subs, funds, pairs, dm_residual: Optional[float]) -> Dict[int, int]:
        """Riporta i residui di arrotondamento entro i vincoli, in interi (solo decrementi)."""

        def trim(indices: List[int], excess: int) -> None:
            for i in sorted(indices, key=lambda k: (-covered.get(k, 0), k)):
                if excess <= 0:
                    return
                take = min(covered.get(i, 0), excess)
                if take:
                    covered[i] -= take
                    excess -= take

        by_sub: Dict[int, List[int]] = {}
        by_fund: Dict[int, List[int]] = {}
        for i, p in enumerate(pairs):
            by_sub.setdefault(p.s, []).append(i)
            by_fund.setdefault(p.j, []).append(i)

        for s, idxs in by_sub.items():
            trim(idxs, sum(covered.get(i, 0) for i in idxs) - subs[s].cents)
        for j, idxs in by_fund.items():
            cap = funds[j].max_total_eur
            if cap is not None:
                trim(idxs, sum(covered.get(i, 0) for i in idxs) - _cents(cap))
        dm = [i for i, p in enumerate(pairs) if funds[p.j].de_minimis]
        if dm:
            trim(dm, sum(covered.get(i, 0) for i in dm) - _cents(dm_residual or 0.0))

        changed = True
        while changed:  # i massimali % si influenzano a vicenda: iterare fino a stabilità
            changed = False
            for j, idxs in by_fund.items():
                for cat, share in funds[j].category_max_share.items():
                    if share >= 1:
                        continue
                    frac = Fraction(str(share))
                    cat_idx = [i for i in idxs if subs[pairs[i].s].category == cat]
                    cat_sum = sum(covered.get(i, 0) for i in cat_idx)
                    total = sum(covered.get(i, 0) for i in idxs)
                    if cat_sum > frac * total:
                        trim(cat_idx, 1)
                        changed = True
        return {i: c for i, c in covered.items() if c > 0}

    # ------------------------------------------------------------------ output
    @classmethod
    def _build_response(cls, req, subs, funds, pairs, covered, excluded, stages, optimal) -> AllocationResponse:
        gross_cents = sum(s.cents for s in subs)
        cov_cents = sum(covered.values())

        item_cov: Dict[str, Dict[str, int]] = {}
        month_cov: Dict[int, Dict[str, int]] = {}
        for i, c in covered.items():
            p = pairs[i]
            fid = funds[p.j].fund_id
            item_cov.setdefault(subs[p.s].item_id, {}).setdefault(fid, 0)
            item_cov[subs[p.s].item_id][fid] += c
            months = _spread(c) if subs[p.s].month == 0 else None
            for m in range(1, 13):
                amount = months[m - 1] if months else (c if subs[p.s].month == m else 0)
                if amount:
                    month_cov.setdefault(m, {}).setdefault(fid, 0)
                    month_cov[m][fid] += amount

        def pct(part: int, whole: int) -> float:
            return float((Decimal(part) * 100 / Decimal(whole)).quantize(Decimal("0.01"))) if whole else 0.0

        plan: List[AllocationLine] = []
        for e in req.historical_expenses:
            gross = sum(s.cents for s in subs if s.item_id == e.item_id)
            per_fund = item_cov.get(e.item_id, {})
            total_cov = sum(per_fund.values())
            main = max(per_fund, key=lambda k: (per_fund[k], k)) if per_fund else "CARICO_ENTE_DIRETTO"
            plan.append(AllocationLine(
                item_id=e.item_id, category=e.category, cost_category=e.category.value, amount_eur=_eur(gross), covered_by=main, gross_amount_eur=_eur(gross), covered_amount_eur=_eur(total_cov),
                net_cost_to_entity_eur=_eur(gross - total_cov), coverage_percentage=pct(total_cov, gross), assigned_fund=main,
                coverage=[FundCoverage(fund_id=k, covered_amount_eur=_eur(v), coverage_percentage=pct(v, gross)) for k, v in sorted(per_fund.items())],
            ))

        usage: List[FundUsage] = []
        for f in funds:
            used = sum(c for i, c in covered.items() if funds[pairs[i].j].fund_id == f.fund_id)
            cap = _cents(f.max_total_eur) if f.max_total_eur is not None else None
            usage.append(FundUsage(
                fund_id=f.fund_id, used_eur=_eur(used), cap_eur=_eur(cap) if cap is not None else None,
                remaining_eur=_eur(cap - used) if cap is not None else None,
                safety_margin_pct=pct(cap - used, cap) if cap else None,
            ))

        monthly: List[MonthlyPlanEntry] = []
        for month in range(1, 13):
            g = sum(_spread(s.cents)[month - 1] if s.month == 0 else (s.cents if s.month == month else 0) for s in subs)
            per = month_cov.get(month, {})
            monthly.append(MonthlyPlanEntry(month=month, gross_eur=_eur(g), covered_eur=_eur(sum(per.values())),
                                            net_eur=_eur(g - sum(per.values())), by_fund={k: _eur(v) for k, v in sorted(per.items())}))

        dm_used = sum(c for i, c in covered.items() if funds[pairs[i].j].de_minimis)
        involved = {funds[pairs[i].j].fund_id for i in covered}
        items_covered = sum(1 for line in plan if line.covered_amount_eur > 0)
        resid = None if req.de_minimis_residual_eur is None else _eur(_cents(req.de_minimis_residual_eur) - dm_used)
        summary = (
            f"Esercizio {req.fiscal_year}: spesa lorda {_eur(gross_cents)} €, coperta da fondi pubblici {_eur(cov_cents)} € "
            f"({pct(cov_cents, gross_cents)}%), spesa netta a carico dell'ente {_eur(gross_cents - cov_cents)} €. "
            f"Fondi coinvolti: {len(involved)}; voci con copertura: {items_covered} su {len(plan)}."
        )
        return AllocationResponse(
            status="OPTIMIZED" if optimal else "BEST_FOUND_TIME_LIMIT", fiscal_year=req.fiscal_year,
            total_cost_eur=_eur(gross_cents), covered_by_funds_eur=_eur(cov_cents),
            optimization_target=req.optimization_target, excluded_funds=sorted(excluded),
            total_gross_expense_eur=_eur(gross_cents), covered_by_public_funds_eur=_eur(cov_cents),
            net_cost_to_entity_eur=_eur(gross_cents - cov_cents), overall_coverage_percentage=pct(cov_cents, gross_cents),
            items_covered=items_covered, funds_involved=len(involved), de_minimis_used_eur=_eur(dm_used),
            de_minimis_residual_eur=resid, allocation_plan=plan, fund_usage=usage, monthly_plan=monthly,
            solver=f"HiGHS (scipy.optimize.milp), {stages} stadi", summary=summary,
        )
