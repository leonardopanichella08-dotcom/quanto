"""Dall'allocazione alla realtà: quanto vale davvero un contributo, e quando i soldi entrano.

L'allocazione dice «questo fondo copre 40.000 €». Non dice tre cose che a un'azienda servono per decidere:

1. **quanto si può davvero contare** — un bando si vince o non si vince, istruire la domanda costa lavoro (e spesso una percentuale al consulente);
2. **quando entrano i soldi** — il contributo si incassa dopo, a rimborso; nel frattempo le spese le paga l'azienda;
3. **cosa si è già preso** — un credito d'imposta o un altro aiuto sulle stesse spese si somma al nuovo, e il bando ha un tetto.

Nulla qui viene inventato. La probabilità di successo, il costo di istruttoria e la percentuale del consulente li indica una persona (dipendono dall'azienda e dal bando):
dove mancano, il calcolo «realistico» di quel fondo non si fa e si dice cosa manca. Anticipo e tempi di rimborso si leggono dal bando, se le sue regole sono pubblicate,
e una persona può correggerli; l'origine di ogni numero è scritta nel risultato.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core import bandi, company_facts, funds as funds_mod

MAX_MONTHS = 36
ASSUMPTION_KEYS = ("probability_pct", "admin_cost_eur", "fee_pct", "reimbursement_lag_months", "advance_pct")


def _num(v: Any) -> Optional[float]:
    try:
        return None if v is None or v == "" else float(v)
    except (TypeError, ValueError):
        return None


def _from_bando(bando_id: Optional[str]) -> Dict[str, Optional[float]]:
    """Anticipo e mesi di rimborso, se le regole del bando sono pubblicate (mai un valore «tipico»)."""
    if not bando_id:
        return {}
    detail = bandi.get_bando_detail(bando_id)
    rules = (detail or {}).get("grant_rules") or {}
    adv = _num(rules.get("advance_pct"))
    return {"reimbursement_lag_months": _num(rules.get("reimbursement_lag_months")), "advance_pct": adv if adv else None}      # 0 = il bando non parla di anticipo


def _clean(a: Dict[str, Any]) -> Dict[str, Optional[float]]:
    out: Dict[str, Optional[float]] = {k: _num(a.get(k)) for k in ASSUMPTION_KEYS}
    for k in ("probability_pct", "fee_pct", "advance_pct"):
        if out[k] is not None and not 0 <= out[k] <= 100:
            raise ValueError(f"{k}: serve un valore tra 0 e 100")
    for k in ("admin_cost_eur", "reimbursement_lag_months"):
        if out[k] is not None and out[k] < 0:
            raise ValueError(f"{k}: non può essere negativo")
    if out["reimbursement_lag_months"] is not None and out["reimbursement_lag_months"] > 24:
        raise ValueError("reimbursement_lag_months: oltre 24 mesi non è un tempo di rimborso plausibile, controlla il valore")
    return out


def _covered_by_fund(allocation: Dict[str, Any]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for u in allocation.get("fund_usage") or []:
        out[u["fund_id"]] = float(u["used_eur"])
    if not out:
        for ln in allocation.get("allocation_plan") or []:
            for c in ln.get("coverage") or []:
                out[c["fund_id"]] = out.get(c["fund_id"], 0.0) + float(c["covered_amount_eur"])
    return {k: round(v, 2) for k, v in out.items() if v > 0}


def _money(x: float) -> str:
    return f"{x:,.2f}".replace(",", "§").replace(".", ",").replace("§", ".") + " €"


def cumulation(owner: str, fiscal_year: int) -> List[Dict[str, Any]]:
    """Gli aiuti già presi o previsti che si sommano a un nuovo contributo sulle stesse spese (il de minimis ha il suo registro)."""
    out: List[Dict[str, Any]] = []
    f = company_facts.facts(owner)
    for rd in f.get("rd_credit") or []:
        if rd.get("year") is None or rd["year"] >= fiscal_year - 1:
            out.append({"kind": "credito d'imposta ricerca e sviluppo", "year": rd.get("year"), "amount_eur": rd["credit_eur"], "document": rd["_doc"]["filename"],
                        "text": f"Credito d'imposta ricerca e sviluppo {rd.get('year') or ''}: {_money(rd['credit_eur'])}. Se riguarda le stesse spese di un progetto, si somma al nuovo contributo "
                                "e il bando ha un tetto all'aiuto totale: indicalo come «altri aiuti» sulle voci interessate."})
    for a in company_facts.aids(owner):
        if str(a.get("regime", "")).lower().startswith("de minimis"):
            continue
        if int(str(a["granted"])[:4]) >= fiscal_year - 2:
            out.append({"kind": a.get("regime") or "altro aiuto", "year": int(str(a["granted"])[:4]), "amount_eur": a["amount_eur"], "document": a["_doc"]["filename"],
                        "text": f"{a.get('measure') or 'Aiuto'} ({a.get('regime') or 'regime non indicato'}), concesso il {a['granted']}: {_money(a['amount_eur'])}. "
                                "Se copre le stesse spese di un nuovo progetto va sommato: indicalo come «altri aiuti» sulle voci interessate."})
    return out


def assess(owner: str, allocation: Dict[str, Any], assumptions: Dict[str, Dict[str, Any]], fiscal_year: int, funding_lines: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    fund_rows = {f["fund_id"]: f for f in (funding_lines or funds_mod.list_funds())}
    covered = _covered_by_fund(allocation)
    funds_out: List[Dict[str, Any]] = []
    resolved: Dict[str, Dict[str, Any]] = {}
    for fid, amount in sorted(covered.items()):
        mine = _clean(assumptions.get(fid) or {})
        default = _from_bando((fund_rows.get(fid) or {}).get("bando_id"))
        origin: Dict[str, str] = {}
        for k in ("reimbursement_lag_months", "advance_pct"):
            if mine[k] is None and default.get(k) is not None:
                mine[k] = default[k] * 100 if k == "advance_pct" else default[k]       # nelle regole l'anticipo è una frazione (0,25)
                origin[k] = "dal bando"
            elif mine[k] is not None:
                origin[k] = "inserito"
        for k in ("probability_pct", "admin_cost_eur", "fee_pct"):
            if mine[k] is not None:
                origin[k] = "inserito"
        resolved[fid] = mine
        missing = [m for k, m in (("probability_pct", "probabilità di successo"), ("admin_cost_eur", "costo di istruttoria"), ("fee_pct", "percentuale del consulente (anche 0)")) if mine[k] is None]
        row: Dict[str, Any] = {"fund_id": fid, "name": (fund_rows.get(fid) or {}).get("name") or fid, "covered_eur": amount, "assumptions": mine, "origin": origin, "missing": missing}
        fee = (mine["fee_pct"] or 0) / 100
        admin = mine["admin_cost_eur"] or 0.0
        if not missing:
            p = mine["probability_pct"] / 100
            expected = round(amount * p, 2)
            row.update({"expected_eur": expected, "fee_eur": round(expected * fee, 2), "admin_cost_eur": admin, "net_expected_eur": round(expected * (1 - fee) - admin, 2),
                        "break_even_probability_pct": round(min(100.0, admin / (amount * (1 - fee)) * 100), 1) if amount * (1 - fee) > 0 else None})
            row["worth_it"] = row["net_expected_eur"] > 0
            row["message"] = (f"Contributo di {_money(amount)} con probabilità {mine['probability_pct']:g}%: ci si può contare per {_money(expected)}. Tolti consulente e istruttoria restano "
                              f"{_money(row['net_expected_eur'])}" + (" — conviene." if row["worth_it"] else " — non conviene alle ipotesi indicate."))
        else:
            row["message"] = f"Contributo nominale di {_money(amount)}. Per valutare quanto conviene mancano: " + ", ".join(missing) + "."
        funds_out.append(row)

    rated = [r for r in funds_out if "net_expected_eur" in r]
    totals = {"nominal_eur": round(sum(covered.values()), 2), "funds": len(funds_out), "funds_rated": len(rated),
              "expected_eur": round(sum(r["expected_eur"] for r in rated), 2) if rated else None,
              "net_expected_eur": round(sum(r["net_expected_eur"] for r in rated), 2) if rated else None,
              "complete": len(rated) == len(funds_out) and bool(funds_out)}

    # ---- i tempi: spese pagate subito dall'azienda, contributi che entrano dopo
    plan = allocation.get("monthly_plan") or []
    timeline_missing = [fid for fid in covered if resolved[fid]["reimbursement_lag_months"] is None]
    horizon = 12 + int(max([resolved[f]["reimbursement_lag_months"] or 0 for f in covered] or [0]))
    horizon = min(MAX_MONTHS, horizon)
    out_m = [0.0] * (horizon + 1)
    in_m = [0.0] * (horizon + 1)
    for m in plan:
        out_m[int(m["month"])] += float(m["gross_eur"])
    for fid in covered:
        lag = resolved[fid]["reimbursement_lag_months"]
        if lag is None:
            continue
        adv = (resolved[fid]["advance_pct"] or 0.0) / 100
        first = next((int(m["month"]) for m in plan if (m.get("by_fund") or {}).get(fid, 0) > 0), None)
        if first is not None and adv > 0:
            in_m[first] += covered[fid] * adv
        for m in plan:
            c = (m.get("by_fund") or {}).get(fid, 0.0)
            at = min(horizon, int(m["month"]) + int(lag))
            in_m[at] += c * (1 - adv)
    rows: List[Dict[str, Any]] = []
    cum = 0.0
    cum_without = 0.0
    peak = (0.0, None)
    peak_without = 0.0
    for mth in range(1, horizon + 1):
        cum += in_m[mth] - out_m[mth]
        cum_without -= out_m[mth]
        peak_without = max(peak_without, -cum_without)
        if -cum > peak[0]:
            peak = (-cum, mth)
        rows.append({"month": mth, "spent_eur": round(out_m[mth], 2), "received_eur": round(in_m[mth], 2), "cumulative_eur": round(cum, 2)})
    cash = {"rows": rows, "peak_need_eur": round(peak[0], 2), "peak_month": peak[1], "peak_need_without_funds_eur": round(peak_without, 2),
            "funds_not_in_timeline": timeline_missing,
            "message": (f"L'azienda deve anticipare al massimo {_money(peak[0])}" + (f" (al mese {peak[1]})" if peak[1] else "") + f", contro {_money(peak_without)} senza contributi." if rows else "Nessuna spesa nel piano.")
                       + (" Il tempo di rimborso non è noto per: " + ", ".join(timeline_missing) + " — quei contributi non sono nel conto." if timeline_missing else ""),
            "assumption": "Le entrate si contano come se tutti i contributi fossero concessi (la probabilità riguarda il valore atteso, non i tempi)."}
    return {"fiscal_year": fiscal_year, "funds": funds_out, "totals": totals, "cash": cash, "cumulation": cumulation(owner, fiscal_year)}
