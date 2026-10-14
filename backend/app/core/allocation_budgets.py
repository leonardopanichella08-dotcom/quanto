"""Dall'allocazione ai budget: un budget per ogni bando che copre una parte delle spese, e che stanno bene insieme.

L'allocazione dice quale fondo copre quale spesa e di quanto. Un commercialista però non presenta «un'allocazione»: presenta un budget a ogni bando. Qui l'allocazione
si trasforma nei budget dei singoli progetti, e si dimostra che sono **ammissibili ciascuno da solo e tutti insieme**.

Come si ricava il budget di un fondo
- la **parte di costo** che il fondo finanzia, per ogni spesa, è ``contributo coperto / intensità del fondo``: se il fondo copre 40.000 € di una spesa al 50%, il suo
  budget contiene 80.000 € di quella spesa;
- le spese pagate da due fondi insieme (cumulo, ammesso solo se i bandi non lo escludono) compaiono in entrambi i budget **dichiarando l'altro** (``funding_ids`` e
  ``other_aid_eur``): è ciò che i controlli 47 e 48 verificano, bando per bando;
- il **personale** si divide tra i progetti senza sovrapporsi: ogni persona ha, in ogni budget, una quota del proprio tempo, e la somma delle quote tra tutti i budget non
  supera il 100% (un'ora di lavoro non si rendiconta a due bandi).

Come si dimostra che stanno bene insieme (``cross_checks``)
1. nessuna spesa è coperta oltre il suo importo;
2. nessuna persona supera il 100% del tempo sommando tutti i budget;
3. due fondi non cumulabili non finanziano mai la stessa spesa;
4. l'aiuto cumulato su una spesa non supera il massimo di nessuno dei fondi che la coprono;
5. il plafond de minimis non è superato;
6. ogni budget, controllato con i 60 criteri del suo bando, ottiene ciò che l'allocazione prevedeva: se il motore ammette meno, la differenza è scritta con la ragione.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from app.core import bandi, budget_basis, company_facts, expense_types, funds as funds_mod
from app.core.deterministic_engine import DeterministicEngine
from app.models.schemas import CostItemInput, GrantRuleSet

_EPS = 0.01


def _rate(fund: Dict[str, Any], category: str) -> float:
    return float((fund.get("category_coverage_pct") or {}).get(category) or fund["coverage_pct"])


def _short(fund_id: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", fund_id.upper())[:14] or "FONDO"


def _item_extras(code: Optional[str], category: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    spec = expense_types.TYPES.get(code or "")
    if spec:
        if spec["subtype"]:
            out["expense_subtype"] = spec["subtype"]
        if spec["asset_nature"] and category == "CAPITAL_ASSETS":
            out["asset_nature"] = spec["asset_nature"]
    return out


def build(owner: str, allocation: Dict[str, Any], fiscal_year: int, validate: bool = True, funding_lines: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """``funding_lines``: le linee di finanziamento usate dall'allocazione (con ``bando_id``); se mancano si usano quelle salvate nel sistema."""
    fund_rows = {f["fund_id"]: f for f in (funding_lines or funds_mod.list_funds())}
    plan_rows: Dict[str, Dict[str, Any]] = {}
    try:
        al = budget_basis.allocation_lines(owner, fiscal_year)
        plan_rows = {f"STIMA-{r['code']}-{r['basis']}": r for r in al["plan"]["types"]}
    except Exception:                                  # l'allocazione può venire da altre spese: il budget si fa lo stesso, solo senza il dettaglio della fonte
        pass
    staff = company_facts.staff(owner)["people"]
    lines = allocation["allocation_plan"]
    used = sorted({c["fund_id"] for ln in lines for c in ln["coverage"] if c["covered_amount_eur"] > 0})
    adjustments: List[str] = []

    # ---- parte di costo di ogni spesa attribuita a ogni fondo
    attributed: Dict[Tuple[str, str], float] = {}                  # (item_id, fund_id) -> costo
    for ln in lines:
        gross = float(ln["gross_amount_eur"])
        cov = [c for c in ln["coverage"] if c["covered_amount_eur"] > 0]
        part: Dict[str, float] = {}
        for c in cov:
            f = fund_rows.get(c["fund_id"])
            r = _rate(f, ln["category"]) if f else 1.0
            part[c["fund_id"]] = min(gross, c["covered_amount_eur"] / r)
        if ln["category"] == "PERSONNEL" and sum(part.values()) > gross + _EPS:       # il tempo di una persona non si rendiconta due volte
            k = gross / sum(part.values())
            adjustments.append(f"Personale: le quote di tempo dei progetti sommavano oltre il 100%; ridotte in proporzione (×{k:.3f}) perché la stessa ora non si rendiconta a due bandi.")
            part = {fid: v * k for fid, v in part.items()}
        for fid, v in part.items():
            attributed[(ln["item_id"], fid)] = v

    budgets: Dict[str, Dict[str, Any]] = {}
    people_share: Dict[str, float] = {}
    for fid in used:
        f = fund_rows.get(fid) or {"fund_id": fid, "name": fid, "bando_id": None, "coverage_pct": 1.0}
        items: List[Dict[str, Any]] = []
        n = 0
        covered_plan = 0.0
        for ln in lines:
            cost = attributed.get((ln["item_id"], fid))
            if not cost or cost <= 0:
                continue
            mine = next(c for c in ln["coverage"] if c["fund_id"] == fid)["covered_amount_eur"]
            covered_plan += mine
            if ln["category"] == "PERSONNEL":
                share = cost / float(ln["gross_amount_eur"])
                people_share[fid] = people_share.get(fid, 0.0) + share
                for k, p in enumerate(staff, 1):
                    ral = p["ral_eur"] if p["ral_eur"] is not None else p.get("payslip_ral_eur")
                    if ral is None:
                        continue
                    it: Dict[str, Any] = {"item_id": f"{_short(fid)}-P{k:02d}", "category": "PERSONNEL", "expense_type": None,
                                          "description": f"{p.get('role') or 'Persona'} ({p.get('ref') or p['token'][:8]}) — quota {share * 100:.1f}% del tempo, {f.get('name') or fid}"[:200],
                                          "source_c_ref": f"DOC-FC-{p['sources'][0]['id']}", "employee_token": p["token"], "ral_eur": ral, "fte_allocation": round(min(1.0, max(0.0001, share)), 4),
                                          "duration_months": 12}
                    if p.get("level"):
                        it["employee_level"] = str(p["level"])
                    if p.get("ccnl_code"):
                        it["ccnl_code"] = p["ccnl_code"]
                    if p.get("payslip_ral_eur") and p["ral_eur"] is not None:
                        it["payslip_ral_eur"] = p["payslip_ral_eur"]
                    items.append(it)
                continue
            others = [c for c in ln["coverage"] if c["fund_id"] != fid and c["covered_amount_eur"] > 0]
            overlap = sum(attributed.get((ln["item_id"], c["fund_id"]), 0.0) for c in ln["coverage"]) > float(ln["gross_amount_eur"]) + _EPS
            n += 1
            row = plan_rows.get(ln["item_id"]) or {}
            src = (row.get("sources") or [{}])[0]
            it = {"item_id": f"{_short(fid)}-{n:02d}", "category": ln["category"], "expense_type": ln.get("expense_type"),
                  "description": f"{ln.get('label') or expense_types.label(ln.get('expense_type')) or ln['item_id']} — parte finanziata da {f.get('name') or fid}"[:200],
                  "amount_eur": round(cost, 2), "source_c_ref": f"DOC-FC-{src['document_id']}" if src.get("document_id") else f"PROFILO-{allocation.get('fiscal_year', fiscal_year)}",
                  **_item_extras(ln.get("expense_type"), ln["category"])}
            if overlap and others:                                   # cumulo: si dichiara l'altro contributo sulla stessa spesa (controlli 47 e 48)
                it["funding_ids"] = [c["fund_id"] for c in others]
                it["other_aid_eur"] = round(sum(c["covered_amount_eur"] for c in others), 2)
            else:
                it["funding_ids"] = []
            items.append(it)
        budgets[fid] = {"fund_id": fid, "name": f.get("name") or fid, "bando_id": f.get("bando_id"), "rate_pct": round(float(f["coverage_pct"]) * 100, 2), "cost_items": items,
                        "contribution_planned_eur": round(covered_plan, 2), "requested_cost_eur": None, "share_personnel": round(people_share.get(fid, 0.0), 4)}

    # ---- il controllo di ogni budget con i 60 criteri del suo bando
    for fid, b in budgets.items():
        if not validate or not b["bando_id"]:
            b["validation"] = None
            continue
        detail = bandi.get_bando_detail(b["bando_id"])
        if not detail or not detail.get("grant_rules"):
            b["validation"] = None
            continue
        try:
            rules = GrantRuleSet.model_validate(detail["grant_rules"])
            res_items, checks, _ = DeterministicEngine.analyze_budget([CostItemInput.model_validate(c) for c in b["cost_items"]], rules)
        except Exception as exc:
            b["validation"] = {"error": f"Non ho potuto controllare il budget: {exc}"}
            continue
        approved = sum(i.computed_cost_eur for i in res_items if i.status.value in ("APPROVED", "CAP_EXCEEDED_ADJUSTED"))       # una voce respinta o in attesa non vale nulla
        requested = sum(i.original_cost_eur for i in res_items)
        rate = float(fund_rows[fid]["coverage_pct"]) if fid in fund_rows else 1.0
        by_status: Dict[str, int] = {}
        for i in res_items:
            by_status[i.status.value] = by_status.get(i.status.value, 0) + 1
        problems = [{"item_id": i.item_id, "description": i.description, "status": i.status.value, "reason": i.rejection_reason, "requested_eur": i.original_cost_eur, "approved_eur": i.computed_cost_eur}
                    for i in res_items if i.status.value != "APPROVED"]
        b["validation"] = {"requested_eur": round(requested, 2), "approved_eur": round(approved, 2), "by_status": by_status, "expected_contribution_eur": round(approved * rate, 2),
                           "problems": problems, "budget_checks": [c.model_dump(mode="json") for c in checks if c.status != "NOT_EVALUATED"]}
        b["requested_cost_eur"] = round(requested, 2)

    cross = _cross_checks(budgets, lines, fund_rows, allocation, adjustments)
    return {"fiscal_year": fiscal_year, "budgets": list(budgets.values()), "cross_checks": cross, "ok": all(c["status"] != "FAIL" for c in cross),
            "summary": {"funds": len(budgets), "total_planned_eur": round(sum(b["contribution_planned_eur"] for b in budgets.values()), 2)}}


def _cross_checks(budgets: Dict[str, Dict[str, Any]], lines: List[Dict[str, Any]], fund_rows: Dict[str, Dict[str, Any]], allocation: Dict[str, Any], adjustments: List[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    def add(key: str, label: str, status: str, detail: str) -> None:
        out.append({"key": key, "label": label, "status": status, "detail": detail})

    over = [ln["item_id"] for ln in lines if sum(c["covered_amount_eur"] for c in ln["coverage"]) > float(ln["gross_amount_eur"]) + _EPS]
    add("coverage", "Nessuna spesa coperta oltre il suo importo", "FAIL" if over else "PASS", ("Coperte oltre l'importo: " + ", ".join(over)) if over else "Per ogni spesa la somma dei contributi dei fondi non supera il suo importo.")

    per_person: Dict[str, float] = {}
    for b in budgets.values():
        for it in b["cost_items"]:
            if it.get("employee_token"):
                per_person[it["employee_token"]] = per_person.get(it["employee_token"], 0.0) + float(it["fte_allocation"])
    worst = max(per_person.values(), default=0.0)
    add("fte", "Nessuna persona oltre il 100% del tempo", "FAIL" if worst > 1 + 1e-6 else "PASS",
        f"Sommando tutti i budget la persona più impegnata è al {worst * 100:.1f}% del proprio tempo." if per_person else "Nessuna voce di personale nei budget." + (" " + " ".join(adjustments) if adjustments else ""))
    if adjustments and per_person:
        out[-1]["detail"] += " " + " ".join(adjustments)

    clash: List[str] = []
    cap_viol: List[str] = []
    for ln in lines:
        cov = [c for c in ln["coverage"] if c["covered_amount_eur"] > 0]
        for i, a in enumerate(cov):
            fa = fund_rows.get(a["fund_id"]) or {}
            for b2 in cov[i + 1:]:
                fb = fund_rows.get(b2["fund_id"]) or {}
                if b2["fund_id"] in (fa.get("excludes") or []) or a["fund_id"] in (fb.get("excludes") or []):
                    clash.append(f"{ln['item_id']}: {a['fund_id']} e {b2['fund_id']}")
        tot = sum(c["covered_amount_eur"] for c in cov)
        for c in cov:
            cap = (fund_rows.get(c["fund_id"]) or {}).get("max_cumulated_pct")
            if cap and len(cov) > 1 and tot > cap * float(ln["gross_amount_eur"]) + _EPS:
                cap_viol.append(f"{ln['item_id']} ({c['fund_id']} ammette al massimo il {cap * 100:g}%)")
    add("exclusions", "Fondi non cumulabili mai sulla stessa spesa", "FAIL" if clash else "PASS", ("Cumulo vietato: " + "; ".join(clash)) if clash else "Nessuna spesa è finanziata da due fondi che si escludono a vicenda.")
    add("cumulation", "Aiuto cumulato entro il massimo dei bandi", "FAIL" if cap_viol else "PASS", ("Oltre il massimo: " + "; ".join(cap_viol)) if cap_viol else "Dove due fondi finanziano la stessa spesa, l'aiuto totale resta entro il massimo di entrambi.")

    dm_used, dm_res = allocation.get("de_minimis_used_eur") or 0.0, allocation.get("de_minimis_residual_eur")
    if dm_used and dm_res is not None:
        add("de_minimis", "De minimis entro il plafond", "FAIL" if dm_res < -_EPS else "PASS", f"Usati {dm_used:,.2f} € di de minimis; residuo {dm_res:,.2f} €.".replace(",", "§").replace(".", ",").replace("§", "."))
    else:
        add("de_minimis", "De minimis entro il plafond", "PASS", "Nessun fondo in de minimis usato.")

    problems = []
    for b in budgets.values():
        v = b.get("validation")
        if not v or "error" in v:
            problems.append(f"{b['name']}: {v['error'] if v else 'controllo non eseguito'}")
            continue
        diff = b["contribution_planned_eur"] - v["expected_contribution_eur"]
        if diff > 1.0:
            why = "; ".join(f"{p['description'][:50]}: {p['reason'] or p['status']}" for p in v["problems"][:2])
            problems.append(f"{b['name']}: il motore ammette {v['approved_eur']:,.2f} € su {v['requested_eur']:,.2f} € (contributo atteso {v['expected_contribution_eur']:,.2f} € invece di {b['contribution_planned_eur']:,.2f} €). {why}".replace(",", "§").replace(".", ",").replace("§", "."))
    add("criteria", "Ogni budget supera i 60 criteri del suo bando", "WARN" if problems else "PASS",
        " · ".join(problems) if problems else "Ogni budget, controllato con i criteri del suo bando, ottiene il contributo previsto dall'allocazione.")
    return out
