"""Su cosa si costruisce un budget: cosa spenderà l'azienda nell'anno del progetto, voce per voce.

Un budget non si ricava copiando l'ultimo bilancio: quel bilancio dice cosa è stato speso, non cosa serve. L'ammortamento, per esempio, è il costo di beni già
comprati e non ha senso come spesa futura; gli acquisti che l'azienda ha in programma stanno nel suo piano degli investimenti. Qui si mettono insieme, nell'ordine
in cui sono più affidabili:

1. **il budget dell'azienda** per l'anno (se l'ha caricato): conto per conto, è la sua previsione;
2. **il piano degli investimenti** per i beni (acquisti veri, non ammortamenti) e **il piano delle assunzioni**;
3. **la previsione dal bilancio**: l'ultimo esercizio, con la variazione annua di ogni categoria (quella del modello dell'utente o quella che risulta dai suoi due
   ultimi bilanci), ripartita tra le voci di spesa con le stesse proporzioni dell'ultimo bilancio.

Ogni riga dice da quale di queste tre viene, e quando il budget dell'azienda e la previsione dal bilancio differiscono lo dice con i numeri. Ciò che manca
(per esempio gli investimenti previsti) non si inventa: finisce nell'elenco «mancanti».
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core import company_facts, company_profile as cp, expense_types

DEPRECIATION = "CAP_AMMORT"
SPEND_CATEGORIES = ("CONSULTING", "OVERHEAD", "TRAINING", "CAPITAL_ASSETS")          # il personale si costruisce persona per persona


def _eur(x: float) -> str:
    return f"{x:,.2f}".replace(",", "§").replace(".", ",").replace("§", ".") + " €"


def _row(code: Optional[str], category: str, amount: float, basis: str, detail: str, sources: List[Any]) -> Dict[str, Any]:
    code = code or expense_types.GENERIC[category]
    return {"code": code, "label": expense_types.label(code), "category": category, "amount_eur": round(amount, 2), "basis": basis, "detail": detail, "sources": sources}


def plan_for_year(owner: str, year: int, growth: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    fc = cp.forecast(owner, year, growth)                 # solleva ProfileError se mancano i bilanci
    base_year = fc["base_year"]
    bd = cp.expense_breakdown(owner, base_year)
    f = company_facts.facts(owner)
    cat_fc = {r["category"]: r for r in fc["categories"]}
    own = [b for b in f["budget_line"] if b["year"] == year]
    capex = [c for c in f["capex_plan"] if c["year"] == year]
    dep_year = company_facts.assets(owner)["depreciation_by_year"].get(str(year))

    rows: List[Dict[str, Any]] = []
    notes: List[str] = []
    missing: List[str] = []
    compared: List[Dict[str, Any]] = []

    for cat in SPEND_CATEGORIES:
        lines = [b for b in own if b["category"] == cat]
        recurring = [b for b in lines if "AMMORTAMENT" not in expense_types.norm(b["description"])]
        fc_cat = cat_fc.get(cat)
        if lines:                                         # 1. il budget dell'azienda
            by_t: Dict[Optional[str], List[Dict[str, Any]]] = {}
            for b in recurring:
                by_t.setdefault(b["expense_type"], []).append(b)
            for code, group in by_t.items():
                src = group[0]["_doc"]
                rows.append(_row(code, cat, sum(g["amount_eur"] for g in group), "BUDGET", f"Budget {year} dell'azienda: {len(group)} {'conto' if len(group) == 1 else 'conti'}",
                                 [{"document_id": src["id"], "filename": src["filename"], "where": f"{len(group)} righe"}]))
            if fc_cat and cat != "CAPITAL_ASSETS":
                own_total = sum(b["amount_eur"] for b in recurring)
                compared.append({"category": cat, "label": cp.CATEGORY_LABEL[cat], "budget_eur": round(own_total, 2), "forecast_eur": fc_cat["forecast_eur"],
                                 "delta_pct": round(100 * (own_total / fc_cat["forecast_eur"] - 1), 1) if fc_cat["forecast_eur"] else None})
        elif fc_cat and cat != "CAPITAL_ASSETS":          # 3. la previsione dal bilancio, ripartita come nell'ultimo esercizio
            parts = [t for t in bd["types"] if t["category"] == cat]
            base = sum(t["amount_eur"] for t in parts)
            for t in parts:
                share = t["amount_eur"] / base if base else 0
                g = fc_cat["growth_applied"]
                rows.append(_row(t["code"], cat, fc_cat["forecast_eur"] * share, "PREVISIONE",
                                 f"Bilancio {base_year}: {_eur(t['amount_eur'])} ({t['lines']} righe), {g * 100:+.1f}% annuo ({fc_cat['growth_origin_label'].lower()})",
                                 [fc_cat["base_source"]]))
        elif cat != "CAPITAL_ASSETS":
            missing.append(f"Nessuna spesa di {cp.CATEGORY_LABEL[cat].lower()} nei documenti.")

    # beni strumentali: i costi ricorrenti (licenze, cloud…) e gli acquisti previsti; l'ammortamento non è una spesa futura
    cap_recurring = [r for r in rows if r["category"] == "CAPITAL_ASSETS"]
    if not any(b["category"] == "CAPITAL_ASSETS" for b in own) and "CAPITAL_ASSETS" in cat_fc:
        parts = [t for t in bd["types"] if t["category"] == "CAPITAL_ASSETS" and t["code"] != DEPRECIATION]
        g = cat_fc["CAPITAL_ASSETS"]["growth_applied"]
        for t in parts:
            rows.append(_row(t["code"], "CAPITAL_ASSETS", t["amount_eur"] * (1 + g) ** (year - base_year), "PREVISIONE",
                             f"Bilancio {base_year}: {_eur(t['amount_eur'])} ({t['lines']} righe)", [cat_fc["CAPITAL_ASSETS"]["base_source"]]))
    dep_base = sum(t["amount_eur"] for t in bd["types"] if t["code"] == DEPRECIATION)
    if capex:
        by_t = {}
        for c in capex:
            by_t.setdefault(c["expense_type"], []).append(c)
        for code, group in by_t.items():
            src = group[0]["_doc"]
            rows.append(_row(code, "CAPITAL_ASSETS", sum(g["amount_eur"] for g in group), "PIANO_INVESTIMENTI", f"Acquisti previsti nel {year}: {', '.join(sorted({g['description'] for g in group}))}",
                             [{"document_id": src["id"], "filename": src["filename"], "where": f"{len(group)} righe"}]))
    else:
        missing.append(f"Gli investimenti previsti per il {year} (acquisti di beni): nei documenti non c'è un piano degli investimenti. Senza, i beni strumentali del budget sono solo i costi ricorrenti (licenze, cloud).")
    if dep_base:
        notes.append(f"L'ammortamento ({_eur(dep_base)} nel bilancio {base_year}) non è una spesa futura: è il costo di beni già acquistati e non entra nel budget"
                     + (f" (il piano di ammortamento prevede {_eur(dep_year)} nel {year})" if dep_year else "") + ". Un bando che ammette solo l'ammortamento si applica sul libro cespiti.")
    if compared:
        for c in compared:
            if c["delta_pct"] is not None and abs(c["delta_pct"]) >= 5:
                notes.append(f"{c['label']}: il budget {year} dell'azienda ({_eur(c['budget_eur'])}) è {c['delta_pct']:+.1f}% rispetto alla stima dal bilancio ({_eur(c['forecast_eur'])}): uso il budget dell'azienda.")

    # personale: la base dei tetti (budget dell'azienda se c'è, altrimenti previsione)
    pers_lines = [b for b in own if b["category"] == "PERSONNEL"]
    if pers_lines:
        personnel_base = round(sum(b["amount_eur"] for b in pers_lines), 2)
        personnel_basis = "BUDGET"
    elif "PERSONNEL" in cat_fc:
        personnel_base = cat_fc["PERSONNEL"]["forecast_eur"]
        personnel_basis = "PREVISIONE"
    else:
        personnel_base, personnel_basis = 0.0, None
    hires = [h for h in company_facts.staff(owner)["hiring_plan"] if h["start"][:4] <= str(year)]
    if hires:
        notes.append(f"Il piano delle assunzioni prevede {len(hires)} {'ingresso' if len(hires) == 1 else 'ingressi'} entro il {year} ({', '.join(h['role'] for h in hires)}): non sono nel budget perché non hanno ancora RAL né livello contrattuale.")
    rows.sort(key=lambda r: (r["category"], -r["amount_eur"]))
    return {"year": year, "base_year": base_year, "types": rows, "personnel_base_eur": personnel_base, "personnel_basis": personnel_basis, "compared": compared,
            "depreciation_year_eur": dep_year, "notes": notes, "missing": missing, "forecast": {"base_year": base_year, "warnings": fc["warnings"]}}


def allocation_lines(owner: str, year: int, growth: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """Le spese dell'anno nella forma che serve all'allocazione: una riga per voce di spesa (non per categoria), più una riga per il personale.
    Ogni riga porta l'identificativo ``STIMA-<voce>-<base>``: da lì il budget di un bando ritrova da dove viene l'importo."""
    plan = plan_for_year(owner, year, growth)
    lines: List[Dict[str, Any]] = []
    if plan["personnel_base_eur"] > 0:
        lines.append({"item_id": "STIMA-PERSONALE", "category": "PERSONNEL", "expense_type": None, "amount_eur": plan["personnel_base_eur"], "label": "Personale (costo dell'organico)", "basis": plan["personnel_basis"]})
    for r in plan["types"]:
        if r["amount_eur"] > 0:
            lines.append({"item_id": f"STIMA-{r['code']}-{r['basis']}", "category": r["category"], "expense_type": r["code"], "amount_eur": r["amount_eur"], "label": r["label"], "basis": r["basis"]})
    return {"year": year, "base_year": plan["base_year"], "lines": lines, "plan": plan}
