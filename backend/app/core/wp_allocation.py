"""Ripartizione delle voci di budget tra i pacchetti di lavoro (WP) del bando (Modulo 2.1 della v2.1).

Le voci sono quelle AMMESSE dal motore (importo approvato, non richiesto). I vincoli dei WP li dichiara chi conosce il bando; qui non ne esiste nessuno
«di default». Il problema è un programma lineare misto-intero, risolto con HiGHS (come l'allocazione annuale):

- x_iw ∈ {0,1} (o [0,1] se si ammette di dividere una voce): la voce i sta nel WP w; Σ_w x_iw = 1 (ogni euro ammesso ha un WP);
- categorie ammesse per WP: x_iw = 0 dove la categoria non è consentita; voce già assegnata a mano: x_i,w* = 1;
- quota del WP sul totale ammesso: min·T ≤ Σ_i a_i x_iw ≤ max·T;
- tetto per categoria dentro il WP: Σ_(i∈c) a_i x_iw ≤ cap_cw · Σ_i a_i x_iw;
- obiettivo: avvicinarsi alle quote desiderate (scostamento assoluto Σ_w |S_w − target_w·T|); a parità, riempire i WP nell'ordine indicato;
  se si ammettono le divisioni, ognuna costa poco (si divide solo se serve davvero).

Il solver lavora in quote (importo / totale) per tenere i numeri piccoli; gli importi finali sono interi in centesimi e il risultato è RI-VERIFICATO in
aritmetica esatta contro tutti i vincoli. Se non esiste una ripartizione si dice perché e quali voci restano fuori: non si forza nulla.
"""
from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

from app.models.schemas import CostCategory
from app.models.wp import WPRequest

CATEGORY_LABEL = {"PERSONNEL": "personale", "CAPITAL_ASSETS": "beni strumentali", "CONSULTING": "consulenze", "OVERHEAD": "spese generali", "TRAINING": "formazione"}
TIME_LIMIT_S = 20.0


def _cents(x: float) -> int:
    return int((Decimal(str(x)) * 100).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


def _cat(c) -> str:
    return getattr(c, "value", c)


def _label(c) -> str:
    return CATEGORY_LABEL.get(_cat(c), str(_cat(c)))


def _reasons(req: WPRequest, allowed: List[List[bool]]) -> List[str]:
    """Motivi evidenti per cui non esiste una ripartizione, prima ancora di chiamare il solver."""
    out: List[str] = []
    wps = req.work_packages
    for i, it in enumerate(req.items):
        if not any(allowed[i]):
            out.append(f"La voce «{it.description or it.item_id}» ({_label(it.category)}) non è ammessa in nessun WP.")
        if it.pinned_wp is not None:
            w = next(k for k, wp in enumerate(wps) if wp.wp_id == it.pinned_wp)
            if not allowed[i][w]:
                out.append(f"La voce «{it.description or it.item_id}» è assegnata a {it.pinned_wp}, che non ammette {_label(it.category)}.")
    maxes = [wp.max_share_pct for wp in wps]
    if all(m is not None for m in maxes) and sum(maxes) < 1 - 1e-9:
        out.append(f"I tetti dei WP sommano al {sum(maxes) * 100:.1f}%: non bastano a contenere il 100% del budget ammesso.")
    mins = [wp.min_share_pct or 0.0 for wp in wps]
    if sum(mins) > 1 + 1e-9:
        out.append(f"Le quote minime dei WP sommano al {sum(mins) * 100:.1f}%: superano il 100% del budget ammesso.")
    return out


def _build(req: WPRequest, allowed, relax: bool) -> Tuple[Any, Dict[str, Any]]:
    items, wps = req.items, req.work_packages
    n, m = len(items), len(wps)
    cents = [_cents(i.amount_eur) for i in items]
    total = sum(cents)
    sh = [c / total for c in cents]
    split = req.allow_split
    nx = n * m
    iu = nx if split else None
    nu = nx if split else 0
    targets = [w for w, wp in enumerate(wps) if wp.target_share_pct is not None]
    id0 = nx + nu
    ns = n if relax else 0
    is0 = id0 + len(targets)
    N = is0 + ns
    x = lambda i, w: i * m + w  # noqa: E731

    lb, ub = np.zeros(N), np.ones(N)
    integrality = np.zeros(N)
    for i, it in enumerate(items):
        for w, wp in enumerate(wps):
            if not allowed[i][w]:
                ub[x(i, w)] = 0
            if it.pinned_wp is not None:
                if wp.wp_id == it.pinned_wp:
                    lb[x(i, w)] = 1 if allowed[i][w] else 0
                else:
                    ub[x(i, w)] = 0
    if not split:
        integrality[:nx] = 1
    else:
        integrality[nx:nx + nu] = 1
    ub[id0:is0] = np.inf
    if relax:
        ub[is0:] = 1

    c = np.zeros(N)
    for i in range(n):
        for w in range(m):
            c[x(i, w)] = 1e-5 * (w / max(1, m)) * sh[i]                    # a parità: i WP si riempiono nell'ordine indicato
    if split:
        c[nx:nx + nu] = 1e-4 / max(1, n)                                      # ogni divisione di una voce costa poco
    c[id0:is0] = 1.0                                                          # scostamento dalle quote desiderate (in quote del totale)
    if relax:
        for i in range(n):
            c[is0 + i] = 10.0 * sh[i]                                         # nella versione rilassata ogni euro lasciato fuori costa molto

    rows: List[Tuple[Dict[int, float], float, float]] = []
    for i in range(n):                                                        # ogni voce sta in un WP
        coef = {x(i, w): 1.0 for w in range(m)}
        if relax:
            coef[is0 + i] = 1.0
        rows.append((coef, 1.0, 1.0))
    if split:
        for i in range(n):
            for w in range(m):
                rows.append(({x(i, w): 1.0, iu + x(i, w): -1.0}, -np.inf, 0.0))
    for w, wp in enumerate(wps):
        s_w = {x(i, w): sh[i] for i in range(n)}
        if wp.min_share_pct:
            rows.append((dict(s_w), wp.min_share_pct, np.inf))
        if wp.max_share_pct is not None:
            rows.append((dict(s_w), -np.inf, wp.max_share_pct))
        for cat, cap in wp.category_max_share.items():                        # Σ_(i∈cat) a_i x_iw − cap · Σ_i a_i x_iw ≤ 0
            coef = {x(i, w): (sh[i] if _cat(items[i].category) == _cat(cat) else 0.0) - cap * sh[i] for i in range(n)}
            rows.append((coef, -np.inf, 0.0))
    for k, w in enumerate(targets):                                           # d_w ≥ |S_w − t_w|
        t = wps[w].target_share_pct
        s_w = {x(i, w): sh[i] for i in range(n)}
        rows.append(({**s_w, id0 + k: 1.0}, t, np.inf))
        rows.append(({**{j: -v for j, v in s_w.items()}, id0 + k: 1.0}, -t, np.inf))

    A = lil_matrix((len(rows), N))
    lo, hi = np.zeros(len(rows)), np.zeros(len(rows))
    for r, (coef, a, b) in enumerate(rows):
        for j, v in coef.items():
            A[r, j] = v
        lo[r], hi[r] = a, b
    return dict(c=c, A=A.tocsr(), lo=lo, hi=hi, lb=lb, ub=ub, integrality=integrality, n=n, m=m, cents=cents, total=total, nx=nx, is0=is0, relax=relax), {}


def _solve(p) -> Optional[Any]:
    res = milp(p["c"], constraints=LinearConstraint(p["A"], p["lo"], p["hi"]), bounds=Bounds(p["lb"], p["ub"]), integrality=p["integrality"],
               options={"time_limit": TIME_LIMIT_S, "presolve": True, "mip_rel_gap": 0.0})
    return res if res.x is not None and res.status in (0, 1) else None


def _to_parts(p, xv, split: bool) -> List[List[int]]:
    """Centesimi di ogni voce in ogni WP: tutta la voce nel WP scelto, oppure divisione per resti maggiori (somma esatta)."""
    n, m, cents = p["n"], p["m"], p["cents"]
    parts: List[List[int]] = []
    for i in range(n):
        frac = [max(0.0, float(xv[i * m + w])) for w in range(m)]
        if not split:
            w = int(np.argmax(frac))
            row = [0] * m
            row[w] = cents[i]
            parts.append(row)
            continue
        tot = sum(frac) or 1.0
        raw = [cents[i] * f / tot for f in frac]
        base = [int(r) for r in raw]
        for k in sorted(range(m), key=lambda k: raw[k] - base[k], reverse=True)[: cents[i] - sum(base)]:
            base[k] += 1
        parts.append(base)
    return parts


def _report(req: WPRequest, parts: List[List[int]], split_used: int) -> Dict[str, Any]:
    items, wps = req.items, req.work_packages
    m = len(wps)
    total = sum(sum(r) for r in parts)
    eur = lambda c: round(c / 100, 2)  # noqa: E731
    tol = split_used  # un centesimo di tolleranza per ogni voce divisa (arrotondamento)
    assignments, summary, checks = [], [], []
    for i, it in enumerate(items):
        ps = [{"wp_id": wps[w].wp_id, "amount_eur": eur(parts[i][w]), "share": round(parts[i][w] / sum(parts[i]), 4)} for w in range(m) if parts[i][w]]
        assignments.append({"item_id": it.item_id, "description": it.description, "category": _cat(it.category), "amount_eur": eur(sum(parts[i])), "parts": ps,
                            "pinned": it.pinned_wp is not None})
    for w, wp in enumerate(wps):
        s_c = sum(parts[i][w] for i in range(len(items)))
        by_cat: Dict[str, int] = {}
        for i, it in enumerate(items):
            if parts[i][w]:
                by_cat[_cat(it.category)] = by_cat.get(_cat(it.category), 0) + parts[i][w]
        share = s_c / total if total else 0.0
        summary.append({"wp_id": wp.wp_id, "name": wp.name, "total_eur": eur(s_c), "share_pct": round(share * 100, 2), "items": sum(1 for i in range(len(items)) if parts[i][w]),
                        "by_category": {k: {"eur": eur(v), "pct_of_wp": round(100 * v / s_c, 2) if s_c else 0.0} for k, v in by_cat.items()},
                        "target_share_pct": wp.target_share_pct, "deviation_pp": None if wp.target_share_pct is None else round(100 * (share - wp.target_share_pct), 2)})
        if wp.min_share_pct:
            ok = s_c + tol >= wp.min_share_pct * total
            checks.append({"wp_id": wp.wp_id, "rule": "quota minima", "ok": ok, "detail": f"{share * 100:.2f}% contro un minimo del {wp.min_share_pct * 100:g}%"})
        if wp.max_share_pct is not None:
            ok = s_c <= wp.max_share_pct * total + tol
            checks.append({"wp_id": wp.wp_id, "rule": "quota massima", "ok": ok, "detail": f"{share * 100:.2f}% contro un massimo del {wp.max_share_pct * 100:g}%"})
        for cat, cap in wp.category_max_share.items():
            v = by_cat.get(_cat(cat), 0)
            ok = v <= cap * s_c + tol
            checks.append({"wp_id": wp.wp_id, "rule": f"tetto {_label(cat)} nel WP", "ok": ok,
                           "detail": f"{(100 * v / s_c) if s_c else 0:.2f}% del WP contro un massimo del {cap * 100:g}%"})
        if wp.allowed_categories is not None:
            bad = [k for k in by_cat if k not in {_cat(c) for c in wp.allowed_categories}]
            checks.append({"wp_id": wp.wp_id, "rule": "categorie ammesse", "ok": not bad, "detail": "solo categorie ammesse" if not bad else "contiene " + ", ".join(_label(b) for b in bad)})
    checks.append({"wp_id": None, "rule": "ogni euro ammesso ha un WP", "ok": sum(sum(r) for r in parts) == sum(_cents(i.amount_eur) for i in items),
                   "detail": f"{eur(total):,.2f} € ripartiti su {len(items)} voci".replace(",", "X").replace(".", ",").replace("X", ".")})
    return {"assignments": assignments, "work_packages": summary, "checks": checks, "total_eur": eur(total), "all_checks_ok": all(c["ok"] for c in checks)}


def allocate(req: WPRequest) -> Dict[str, Any]:
    items, wps = req.items, req.work_packages
    allowed = [[(wp.allowed_categories is None or _cat(it.category) in {_cat(c) for c in wp.allowed_categories}) for wp in wps] for it in items]
    reasons = _reasons(req, allowed)
    if reasons:
        return {"status": "INFEASIBLE", "message": "Non esiste una ripartizione che rispetti i vincoli indicati.", "reasons": reasons, "unplaced": [], "notes": []}
    p, _ = _build(req, allowed, relax=False)
    res = _solve(p)
    if res is None:
        pr, _ = _build(req, allowed, relax=True)
        rr = _solve(pr)
        unplaced = []
        if rr is not None:
            for i, it in enumerate(items):
                s = float(rr.x[pr["is0"] + i])
                if s > 1e-6:
                    unplaced.append({"item_id": it.item_id, "description": it.description, "unplaced_eur": round(s * p["cents"][i] / 100, 2)})
        return {"status": "INFEASIBLE", "message": "I vincoli dei WP non lasciano posto a tutto il budget ammesso: allarga un tetto o una quota, o consenti la divisione delle voci.",
                "reasons": reasons or ["Le quote massime, le categorie ammesse e i tetti per categoria, insieme, non contengono tutte le voci."], "unplaced": unplaced, "notes": []}
    parts = _to_parts(p, res.x, req.allow_split)
    split_used = sum(1 for r in parts if sum(1 for v in r if v) > 1)
    out = _report(req, parts, split_used)
    notes = []
    if not any(wp.target_share_pct is not None for wp in wps):
        notes.append("Nessuna quota desiderata: i WP si riempiono nell'ordine indicato, nei limiti dei tetti.")
    if split_used:
        notes.append(f"{split_used} {'voce è stata divisa' if split_used == 1 else 'voci sono state divise'} tra più WP per rispettare le quote.")
    out.update({"status": "OPTIMAL" if res.status == 0 else "BEST_FOUND", "message": "Ripartizione verificata su tutti i vincoli." if out["all_checks_ok"] else "Ripartizione trovata ma un controllo non torna: vedi i controlli.",
                "reasons": [], "unplaced": [], "notes": notes + ([] if res.status == 0 else ["Il tempo massimo del calcolo è scaduto: questa è la migliore ripartizione trovata."]),
                "solver": "HiGHS (scipy.optimize.milp)", "project_id": req.project_id})
    return out
