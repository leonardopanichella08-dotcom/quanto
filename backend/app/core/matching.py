"""Quali bandi vanno bene per questa azienda, quali voci di costo possono ridurre, di quanto, e come rientrarci.

Tutto si decide sulle regole PUBBLICATE di ciascun bando (le stesse che accendono i controlli del budget) e sui dati del profilo aziendale:
- una verifica è «ok» solo se i dati la dimostrano, «no» solo se la smentiscono, altrimenti «da verificare» (e si dice quale dato manca nel profilo);
- l'importo stimato esiste solo se il bando dichiara un'aliquota di contributo; per garanzie, crediti d'imposta a scaglioni e simili il beneficio si
  descrive ma non si quantifica (non si inventa una percentuale);
- «come rientrarci»: dove un tetto del bando (consulenze, spese generali) è superato, si dice quanta parte della voce è ammissibile e quanta resta a carico.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from app.core import bandi, funds, valuation
from app.core.company_profile import CATEGORIES, CATEGORY_LABEL, REGIONS
from app.core.db import connect
from app.core.ingestion import Ingestion

_EPS = 1e-9


def _rules(detail: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for r in detail.get("rules", []):
        if r["status"] == "PUBLISHED" and r.get("value") is not None:
            out[r["key"]] = r["value"]
    return out


def _as_date(v: Any) -> Optional[date]:
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def availability(detail: Dict[str, Any], rules: Dict[str, Any], deadline: Optional[str], today: date) -> Dict[str, str]:
    """Il bando è aperto, chiuso o non si sa: stato dichiarato, scadenza letta dalla scheda ufficiale, finestra delle regole."""
    status = (detail.get("status") or "").upper()
    if status.startswith("CHIUSO"):
        return {"result": "FAIL", "detail": f"Il bando risulta chiuso ({detail.get('status')})."}
    end = _as_date(rules.get("eligibility_end"))
    if end and end < today:
        return {"result": "FAIL", "detail": f"La finestra di ammissibilità è finita il {end.isoformat()}."}
    close = _as_date(deadline) if deadline and deadline != "non indicata" else None
    if close and close < today:
        return {"result": "FAIL", "detail": f"La scadenza era il {close.isoformat()}."}
    period = detail.get("period") or {}
    pend = _as_date(period.get("to"))
    if pend and pend < today:
        return {"result": "FAIL", "detail": f"Il periodo del bando è finito il {pend.isoformat()}."}
    if close:
        return {"result": "OK", "detail": f"Aperto, scade il {close.isoformat()}."}
    if status.startswith(("APERTO", "PERMANENTE")):
        return {"result": "OK", "detail": detail.get("status") or "Aperto."}
    return {"result": "UNKNOWN", "detail": "Non risulta una scadenza o uno stato di apertura: controlla la pagina ufficiale."}


def _region_in_text(text: str) -> Optional[str]:
    low = text.lower()
    for region in REGIONS:
        if region.lower() in low:
            return region
    return None


def _adjustments(rules: Dict[str, Any], by_cat: Dict[str, float], allowed: List[str]) -> List[Dict[str, Any]]:
    """Dove un tetto percentuale del bando è superato: quanto della voce è ammissibile e quanto resta fuori."""
    base = sum(by_cat.get(c, 0.0) for c in allowed)
    out = []
    for key, cat in (("max_consulting_percentage", "CONSULTING"), ("max_overhead_percentage", "OVERHEAD")):
        cap = rules.get(key)
        amount = by_cat.get(cat, 0.0)
        if cap is None or cat not in allowed or amount <= 0 or base <= 0:
            continue
        cap = float(cap)
        if amount / base > cap + _EPS:
            eligible = round(cap * (base - amount) / (1 - cap), 2) if cap < 1 else amount
            out.append({"category": cat, "label": CATEGORY_LABEL[cat], "forecast_eur": round(amount, 2), "eligible_eur": eligible, "over_cap_eur": round(amount - eligible, 2),
                        "cap_pct": round(cap * 100, 2), "reason": f"{CATEGORY_LABEL[cat]} al massimo il {cap * 100:g}% del totale ammissibile"})
    return out


def _estimate(rules: Dict[str, Any], by_cat: Dict[str, float], rate: float, allowed_override: Optional[List[str]] = None, cap_eur: Optional[float] = None) -> Dict[str, Any]:
    allowed = [c for c in (allowed_override or rules.get("eligible_categories") or list(CATEGORIES)) if c in CATEGORIES]
    adj = {a["category"]: a for a in _adjustments(rules, by_cat, allowed)}
    rows, eligible_total, covered_total = [], 0.0, 0.0
    for c in CATEGORIES:
        amount = by_cat.get(c, 0.0)
        if amount <= 0:
            continue
        if c not in allowed:
            rows.append({"category": c, "label": CATEGORY_LABEL[c], "forecast_eur": round(amount, 2), "eligible_eur": 0.0, "covered_eur": 0.0, "coverage_pct": 0.0, "note": "categoria non ammessa dal bando"})
            continue
        eligible = adj[c]["eligible_eur"] if c in adj else amount
        covered = round(eligible * rate, 2)
        eligible_total += eligible
        covered_total += covered
        rows.append({"category": c, "label": CATEGORY_LABEL[c], "forecast_eur": round(amount, 2), "eligible_eur": round(eligible, 2), "covered_eur": covered,
                     "coverage_pct": round(100 * covered / amount, 1), "note": adj[c]["reason"] if c in adj else None})
    total = sum(by_cat.values())
    capped = False
    if cap_eur is not None and covered_total > cap_eur > 0:                  # tetto in euro del contributo per progetto: si riducono tutte le righe in proporzione
        factor = cap_eur / covered_total
        for r in rows:
            r["covered_eur"] = round(r["covered_eur"] * factor, 2)
            r["coverage_pct"] = round(100 * r["covered_eur"] / r["forecast_eur"], 1) if r["forecast_eur"] else 0.0
        covered_total, capped = cap_eur, True
    return {"rate_pct": round(rate * 100, 2), "capped": capped, "eligible_base_eur": round(eligible_total, 2), "covered_eur": round(covered_total, 2),
            "covered_pct_of_total": round(100 * covered_total / total, 1) if total else 0.0, "by_category": rows, "adjustments": list(adj.values())}


def _applicant_hints(detail: Dict[str, Any]) -> List[str]:
    hints = [r["text"][:200] for r in detail.get("requirements", []) if r["kind"] != "DA_REVISIONARE" and "Chi può presentare" in r["topic"]]
    return hints[:3]


BENEFIT_EXPLANATION = {
    "GARANZIA_PUBBLICA": "È una garanzia pubblica: non rimborsa spese, ma garantisce una parte di un finanziamento bancario. Quanto vale dipende dal prestito che chiedi alla banca, che non è nel bilancio.",
    "FINANZIAMENTO_A_TASSO_ZERO": "È un finanziamento a tasso zero: un prestito senza interessi, non un contributo sulle spese. Il vantaggio è l'interesse risparmiato e dipende dall'importo e dalla durata.",
    "CONTRIBUTO_IN_CONTO_INTERESSI": "Copre una parte degli interessi di un finanziamento: il valore dipende dal prestito che prendi, non dalle spese del bilancio.",
    "IPERAMMORTAMENTO": "È un beneficio fiscale (maggiorazione dell'ammortamento): riduce le imposte, non rimborsa le spese. Dipende dalle tasse che paghi.",
    "FINANZIAMENTO_AGEVOLATO_MISTO": "Combina un finanziamento agevolato e un contributo: la parte a fondo perduto dipende dalle condizioni di ogni sportello.",
}


def _mode_of(detail: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """La modalità di accesso principale del bando (a progetto, credito automatico, garanzia…)."""
    from app.core import funding_modes
    fm = detail.get("funding_modes") or {}
    d = funding_modes.describe(fm.get("primary"))
    if d is not None:
        d["others"] = [m["label"] for m in fm.get("modes", [])[1:3]]
    return d


def _without_excluded_types(rules: Dict[str, Any], by_cat: Dict[str, float], by_type: Optional[Dict[str, Dict[str, Any]]]):
    """Le spese per categoria senza le voci che il bando esclude per nome (affitti, rappresentanza…): non fanno parte della base su cui si calcola il contributo."""
    excluded = [c for c in (rules.get("excluded_expense_types") or []) if by_type and c in by_type]
    if not excluded:
        return by_cat, []
    eff = dict(by_cat)
    out = []
    for code in excluded:
        t = by_type[code]
        eff[t["category"]] = max(0.0, eff.get(t["category"], 0.0) - t["amount_eur"])
        out.append({"code": code, "label": t["label"], "category": t["category"], "amount_eur": round(t["amount_eur"], 2)})
    return eff, out


def evaluate(bando_id: str, profile: Dict[str, Any], by_cat: Dict[str, float], year: int, today: Optional[date] = None, by_type: Optional[Dict[str, Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    today = today or date.today()
    detail = bandi.get_bando_detail(bando_id)
    if detail is None:
        return None
    rules = _rules(detail)
    by_cat, excluded_types = _without_excluded_types(rules, by_cat, by_type)
    row = Ingestion.get_bando(bando_id) or {}
    checks: List[Dict[str, Any]] = []
    missing: List[str] = []

    av = availability(detail, rules, row.get("deadline"), today)
    checks.append({"id": "availability", "label": "Apertura", "decisive": True, **av})

    allowed = [c for c in (rules.get("eligible_categories") or list(CATEGORIES)) if c in CATEGORIES]
    usable = [c for c in allowed if by_cat.get(c, 0) > 0]
    if excluded_types:
        checks.append({"id": "expense_types", "label": "Voci escluse per nome", "decisive": False, "result": "OK",
                       "detail": "Il bando non ammette: " + ", ".join(f"{t['label'].lower()} ({_it_eur(t['amount_eur'])})" for t in excluded_types) + ". Non contano nel contributo."})
    if usable:
        checks.append({"id": "categories", "label": "Spese ammesse", "decisive": True, "result": "OK",
                       "detail": "Ammette: " + ", ".join(CATEGORY_LABEL[c].lower() for c in usable) + "."})
    else:
        checks.append({"id": "categories", "label": "Spese ammesse", "decisive": True, "result": "FAIL", "detail": "Nessuna delle categorie di spesa dell'azienda è tra quelle ammesse dal bando."})

    prefixes = rules.get("allowed_ateco_prefixes")
    if prefixes:
        ateco = profile.get("ateco_code")
        if not ateco:
            missing.append("ateco_code")
            checks.append({"id": "ateco", "label": "Settore (ATECO)", "decisive": True, "result": "UNKNOWN", "detail": "Il bando ammette solo certi settori: indica il tuo codice ATECO nel profilo."})
        elif any(str(ateco).replace(".", "").startswith(str(p).replace(".", "")) for p in prefixes):
            checks.append({"id": "ateco", "label": "Settore (ATECO)", "decisive": True, "result": "OK", "detail": f"Il codice {ateco} rientra tra i settori ammessi."})
        else:
            checks.append({"id": "ateco", "label": "Settore (ATECO)", "decisive": True, "result": "FAIL", "detail": f"Il codice {ateco} non rientra tra i settori ammessi."})

    region_in_name = _region_in_text(f"{detail.get('name', '')} {detail.get('issuer', '')}")
    if region_in_name:
        mine = profile.get("region")
        if not mine:
            missing.append("region")
            checks.append({"id": "territory", "label": "Territorio", "decisive": True, "result": "UNKNOWN", "detail": f"Bando della regione {region_in_name}: indica la regione della tua sede nel profilo."})
        elif mine == region_in_name:
            checks.append({"id": "territory", "label": "Territorio", "decisive": True, "result": "OK", "detail": f"Sede in {mine}, come richiesto."})
        else:
            checks.append({"id": "territory", "label": "Territorio", "decisive": True, "result": "FAIL", "detail": f"Bando riservato a {region_in_name}; la tua sede è in {mine}."})

    name_low = f"{detail.get('name', '')}".lower()
    if "start-up" in name_low or "startup" in name_low:
        flag = profile.get("is_innovative_startup")
        if flag is None:
            missing.append("is_innovative_startup")
            checks.append({"id": "startup", "label": "Start-up innovativa", "decisive": True, "result": "UNKNOWN", "detail": "Il bando è per start-up innovative: indica nel profilo se lo sei."})
        else:
            checks.append({"id": "startup", "label": "Start-up innovativa", "decisive": True, "result": "OK" if flag else "FAIL",
                           "detail": "Risulti start-up innovativa." if flag else "Il bando è riservato alle start-up innovative."})

    size = profile.get("size")
    hints = _applicant_hints(detail)
    applicant_text = " ".join(hints).lower()
    if size and not size["is_sme"] and ("pmi" in applicant_text or "piccole e medie" in applicant_text or "micro" in applicant_text):
        checks.append({"id": "size", "label": "Dimensione", "decisive": False, "result": "UNKNOWN",
                       "detail": f"Il bando sembra rivolto alle PMI e la tua azienda risulta {size['label'].lower()}: controlla i requisiti soggettivi."})
    elif hints:
        checks.append({"id": "applicants", "label": "Chi può presentare domanda", "decisive": False, "result": "UNKNOWN", "detail": " · ".join(hints)})

    benefit = detail.get("benefit")
    fund = None
    estimate = None
    guarantee = None
    val = valuation.value_bando(bando_id, detail, rules, profile, by_cat)
    dm = valuation.de_minimis_info(bando_id, bandi.valuation_model(bando_id))     # in de minimis solo se lo dice una fonte (modello curato o testo ufficiale)
    if val and val["kind"] == "GARANZIA":                    # non è un guadagno: si calcola l'importo garantibile, ma non entra nel piano né nelle somme
        guarantee = {"financed_eur": val["financed_eur"], "guaranteed_low_eur": val["guaranteed_low_eur"], "guaranteed_high_eur": val["guaranteed_high_eur"]}
    elif val:
        from_rule = val["origin"] == "REGOLA"
        try:
            fund = funds.build_fund(bando_id, year, max_total_eur=val.get("cap_low"), de_minimis=bool(val.get("de_minimis")) or dm["applies"],
                                    coverage_pct=None if from_rule else val["rate_low"], categories=None if from_rule else val.get("categories"))
        except funds.FundError as exc:
            if "finestra di ammissibilità" in str(exc):
                checks.append({"id": "window", "label": f"Finestra {year}", "decisive": True, "result": "FAIL", "detail": str(exc)})
        if fund is not None:
            cats = None if from_rule else val.get("categories")
            estimate = _estimate(rules, by_cat, float(fund["coverage_pct"]), cats, val.get("cap_low"))
            hi = _estimate(rules, by_cat, float(val["rate_high"]), cats, val.get("cap_high"))
            estimate.update({"rate_high_pct": hi["rate_pct"], "covered_high_eur": max(hi["covered_eur"], estimate["covered_eur"]), "kind": val["kind"],
                             "kind_label": valuation.KIND_LABEL[val["kind"]], "summable": val["kind"] in valuation.SUMMABLE, "origin": val["origin"],
                             "assumptions": val.get("assumptions", []), "evidence": val.get("evidence", []), "cap_eur": val.get("cap_low"), "cap_high_eur": val.get("cap_high")})
            fund = {**fund, "allowed_categories": [getattr(c, "value", c) for c in fund["allowed_categories"]],
                    "category_max_share": {getattr(k, "value", k): v for k, v in fund["category_max_share"].items()}}

    notes = []
    for key, text in (("requires_cup", "Richiede il CUP su ogni spesa."), ("requires_dnsh", "Richiede il rispetto del principio DNSH (non arrecare danno significativo)."),
                      ("requires_new_asset", "I beni devono essere nuovi di fabbrica."), ("min_durability_months", None)):
        if key in rules:
            notes.append(text if text else f"Vincolo di destinazione: almeno {rules[key]} mesi.")
    if estimate is None and guarantee is None:
        btype = (benefit or {}).get("type") or ""
        notes.append("Il bando non dichiara un'aliquota di contributo (la percentuale delle spese che viene rimborsata): il beneficio non si può quantificare in automatico. "
                     + BENEFIT_EXPLANATION.get(btype, f"Tipo di aiuto: {btype}." if btype else ""))

    fails = [c for c in checks if c["result"] == "FAIL"]
    unknown_decisive = [c for c in checks if c["result"] == "UNKNOWN" and c["decisive"]]
    if fails:
        fit = "NON_ADATTO"
    elif unknown_decisive or (estimate is None and guarantee is None):
        fit = "DA_VERIFICARE"
    else:
        fit = "ADATTO"
    return {"bando_id": bando_id, "name": detail["name"], "issuer": detail.get("issuer"), "status": detail.get("status"), "fit": fit, "checks": checks, "estimate": estimate,
            "fund": fund, "de_minimis": dm, "guarantee": guarantee, "guarantee_info": ({"kind_label": valuation.KIND_LABEL["GARANZIA"], "assumptions": val.get("assumptions", []), "evidence": val.get("evidence", [])} if guarantee else None),
            "excluded_types": excluded_types, "mode": _mode_of(detail), "benefit": benefit, "notes": notes, "missing_profile": sorted(set(missing)), "requirements_count": len(detail.get("requirements", [])),
            "rules_count": len(rules)}


def match_all(profile: Dict[str, Any], by_cat: Dict[str, float], year: int, by_type: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Tutti i bandi studiati (curati o con regole/requisiti letti), dal più utile al meno utile."""
    out = []
    for b in bandi.list_bandi():
        if not (b["curated"] or b["rules_count"] or b["requirements_count"]):
            continue
        r = evaluate(b["bando_id"], profile, by_cat, year, by_type=by_type)
        if r:
            out.append(r)
    order = {"ADATTO": 0, "DA_VERIFICARE": 1, "NON_ADATTO": 2}
    out.sort(key=lambda r: (order[r["fit"]], -((r["estimate"] or {}).get("covered_eur") or 0), r["name"]))
    with connect() as conn:
        unstudied = conn.execute("SELECT COUNT(*) c FROM bandi b WHERE b.bando_id LIKE 'CAT-%' AND b.extraction_status = 'NOT_STARTED' "
                                 "AND (b.deadline IS NULL OR b.deadline = 'non indicata' OR b.deadline >= ?)", (date.today().isoformat(),)).fetchone()["c"]
    from app.core import catalog_meta
    catalog = catalog_meta.rank_for_profile(profile, by_cat)
    return {"fiscal_year": year, "results": out, "catalog": catalog, "summary": {k: sum(1 for r in out if r["fit"] == k) for k in order}, "unstudied_catalog": unstudied,
            "missing_profile": sorted({m for r in out for m in r["missing_profile"]})}


# ------------------------------------------------------------------------------------------------ bozza di budget dal profilo
def _project_year(rules: Dict[str, Any], base_year: int) -> int:
    """L'anno su cui si costruisce il budget: quello dopo l'ultimo bilancio, riportato dentro la finestra di ammissibilità del bando se questa lo esclude."""
    year = base_year + 1
    start, end = _as_date(rules.get("eligibility_start")), _as_date(rules.get("eligibility_end"))
    if start and start.year > year:
        year = start.year
    if end and base_year < end.year < year:
        year = end.year
    return year


_CONTRACT = (("INDETERMINATO", "PERMANENT"), ("DETERMINATO", "FIXED_TERM"), ("APPRENDIST", "FIXED_TERM"), ("OCCASIONAL", "OCCASIONAL"))


def _contract_type(text: Optional[str]) -> Optional[str]:
    from app.core.expense_types import norm
    n = norm(text or "")
    for key, val in _CONTRACT:
        if key in n:
            return val
    return None


def _it_eur(x: float) -> str:
    return f"{x:,.2f}".replace(",", "§").replace(".", ",").replace("§", ".") + " €"


def _can_complete(code: str) -> bool:
    from app.core import fonte_b_admin
    try:
        return bool(fonte_b_admin.completion_info(code)["possible"])
    except Exception:
        return False


def budget_template(owner: str, bando_id: str, scale_pct: float, fit: bool = True, year: Optional[int] = None, project_start: Optional[str] = None) -> Dict[str, Any]:
    """Una bozza di budget per il bando, costruita sui dati dell'azienda e sulle regole del bando.

    - **Il personale è persona per persona**, dall'organico dei documenti (registro del personale, buste paga): livello, contratto, RAL, ore e quota di tempo sul progetto.
    - **Le altre spese sono voci di spesa** (affitti, energia, licenze, trasferte…), non categorie: ognuna con l'importo previsto per l'anno del progetto, da dove viene
      (budget dell'azienda, piano degli investimenti o previsione dal bilancio) e il documento che lo giustifica.
    - **Le voci che il bando esclude per nome** non entrano, e quelle sopra i tetti del bando si riducono alla parte ammissibile.
    È una base da modificare, non un budget pronto: la controlla poi la pagina Budget con i 60 criteri."""
    from app.core import budget_basis, company_facts, company_profile as cp, expense_types

    if not 0 < scale_pct <= 100:
        raise cp.ProfileError("La quota del progetto sul totale annuale va da 0 a 100%")
    detail = bandi.get_bando_detail(bando_id)
    if detail is None:
        raise KeyError(bando_id)
    rules = _rules(detail)
    fin = cp._load_financials(owner)
    years = [y for y in sorted(fin) if any(fin[y][0].get(cp.FIN_KEY[c]) is not None for c in CATEGORIES)]
    if not years:
        raise cp.ProfileError("Mancano i dati di bilancio: carica un bilancio nel profilo o inserisci i costi dell'ultimo esercizio")
    base_year = years[-1]
    target = year or _project_year(rules, base_year)
    plan = budget_basis.plan_for_year(owner, target)
    factor = scale_pct / 100.0
    allowed = [c for c in (rules.get("eligible_categories") or list(CATEGORIES)) if c in CATEGORIES]
    excluded_types = set(rules.get("excluded_expense_types") or [])

    usable = [r for r in plan["types"] if r["category"] in allowed]
    dropped_cat = sorted({r["category"] for r in plan["types"] if r["category"] not in allowed})
    dropped_types = [r for r in usable if r["code"] in excluded_types]
    kept = [r for r in usable if r["code"] not in excluded_types]

    by_cat: Dict[str, float] = {}
    for r in kept:
        by_cat[r["category"]] = by_cat.get(r["category"], 0.0) + r["amount_eur"] * factor
    if "PERSONNEL" in allowed:
        by_cat["PERSONNEL"] = plan["personnel_base_eur"] * factor            # il personale conta nei tetti; le voci le fanno le persone
    adjustments = _adjustments(rules, by_cat, allowed) if fit else []
    reduce = {a["category"]: a["eligible_eur"] / a["forecast_eur"] for a in adjustments}

    items: List[Dict[str, Any]] = []
    basis_rows: List[Dict[str, Any]] = []
    for n, r in enumerate(kept, 1):
        ratio = reduce.get(r["category"], 1.0)
        amount = round(r["amount_eur"] * factor * ratio, 2)
        if amount <= 0:
            continue
        spec = expense_types.TYPES[r["code"]]
        src = (r["sources"] or [{}])[0]
        ref = f"DOC-FC-{src['document_id']}" if src.get("document_id") else f"PROFILO-{plan['base_year']}"
        note = f" · ridotta al {ratio * 100:.0f}% per il tetto del bando" if ratio < 1 else ""
        item = {"item_id": f"TPL-{n:02d}", "description": f"{r['label']} — {r['detail']}, quota progetto {scale_pct:g}%{note}"[:200], "category": r["category"], "expense_type": r["code"],
                "amount_eur": amount, "source_c_ref": ref}
        if spec["subtype"]:
            item["expense_subtype"] = spec["subtype"]
        if spec["asset_nature"] and r["category"] == "CAPITAL_ASSETS":
            item["asset_nature"] = spec["asset_nature"]
        items.append(item)
        nature = "NUOVA" if r["basis"] == "PIANO_INVESTIMENTI" else "ORDINARIA"            # un acquisto in programma è nuovo; una spesa di budget o di bilancio l'azienda la sostiene comunque
        if project_start:
            item["expense_date"] = project_start                                           # il controllo 46 verifica la finestra di ammissibilità del bando su questa data
        basis_rows.append({"item_id": item["item_id"], "code": r["code"], "label": r["label"], "category": r["category"], "basis": r["basis"], "nature": nature, "forecast_eur": round(r["amount_eur"] * factor, 2),
                           "amount_eur": amount, "detail": r["detail"], "sources": r["sources"]})

    people_info: List[Dict[str, Any]] = []
    needs_personnel = None
    needs_input: List[str] = list(plan["missing"])
    if "PERSONNEL" in allowed:
        from app.core import fonte_b
        staff = company_facts.staff(owner)
        fb = fonte_b.load()
        no_table: Dict[Any, int] = {}
        for k, p in enumerate(staff["people"], 1):
            if p["ral_eur"] is None and p.get("payslip_ral_eur") is None:
                needs_input.append(f"La RAL di {p.get('role') or 'una persona'} ({p.get('ref') or p['token'][:8]}) non è nei documenti: la persona non è nel budget.")
                continue
            hours = p.get("hours_week") or 40.0
            fte = round(min(1.0, max(0.01, factor)), 4)                      # quota del PROPRIO tempo: la RAL di chi è part-time è già quella del part-time
            src = p["sources"][0]
            ral = p["ral_eur"] if p["ral_eur"] is not None else p["payslip_ral_eur"]
            item = {"item_id": f"TPL-P{k:02d}", "description": f"{p.get('role') or 'Persona'} ({p.get('ref') or p['token'][:8]}) — quota progetto {scale_pct:g}% del tempo di lavoro"[:200], "category": "PERSONNEL",
                    "source_c_ref": f"DOC-FC-{src['id']}", "employee_token": p["token"], "ral_eur": ral, "fte_allocation": fte, "duration_months": 12}
            if p.get("level"):
                item["employee_level"] = str(p["level"])
            if p.get("ccnl_code"):
                item["ccnl_code"] = p["ccnl_code"]
                if p.get("level") and fb.ccnl(p["ccnl_code"], str(p["level"])) is None:
                    no_table[(p["ccnl_code"], str(p["level"]))] = no_table.get((p["ccnl_code"], str(p["level"])), 0) + 1
            else:
                needs_input.append(f"Il contratto collettivo di {p.get('role') or 'una persona'} ({p.get('ref') or p['token'][:8]}) non è tra quelli di Fonte B: il controllo del costo orario resta in attesa.")
            ct = _contract_type(p.get("contract"))
            if ct:
                item["contract_type"] = ct
            if p.get("payslip_ral_eur") and p["ral_eur"] is not None:
                item["payslip_ral_eur"] = p["payslip_ral_eur"]
            if project_start:
                item["expense_date"] = project_start
            items.append(item)
            people_info.append({"item_id": item["item_id"], "ref": p.get("ref"), "role": p.get("role"), "level": p.get("level"), "ccnl_code": p.get("ccnl_code"), "ral_eur": ral, "hours_week": hours,
                                "fte_allocation": fte, "has_payslip": bool(p.get("payslip_document_id")), "contract": p.get("contract")})
        for (code, level), n in sorted(no_table.items()):
            needs_input.append(f"In Fonte B manca la tabella del contratto {code} per il livello {level} ({n} {'persona' if n == 1 else 'persone'}): il costo orario di chi è a quel livello non si può controllare "
                               "finché un manager non la pubblica (Quartier Generale → Fonte B)."
                               + (" I livelli già pubblicati hanno parametri identici: dal Quartier Generale si può preparare una bozza che aggiunge anche questo livello, da controllare sul contratto e pubblicare."
                                  if _can_complete(code) else ""))
        if not staff["people"] and plan["personnel_base_eur"] > 0:
            needs_personnel = {"amount_eur": round(plan["personnel_base_eur"] * factor, 2),
                               "message": "Nei documenti non ci sono persone: carica il registro del personale (Excel) o le buste paga. Il controllo vuole persona per persona livello, CCNL, RAL e quota di tempo."}

    if project_start:
        try:
            date.fromisoformat(project_start)
        except ValueError:
            raise cp.ProfileError("La data di avvio del progetto non è valida (AAAA-MM-GG)") from None
    mode = _mode_of(detail)
    current_ok = bool(mode and mode["ordinary_costs_ok"])
    for b in basis_rows:                                                                  # dove il bando parte dalle spese correnti (spese commerciali, liquidità, ristoro) non sono «ordinarie» da guardare con sospetto
        if current_ok and b["nature"] == "ORDINARIA":
            b["nature"] = "CORRENTE"
    new_eur = round(sum(b["amount_eur"] for b in basis_rows if b["nature"] == "NUOVA"), 2)
    ordinary_eur = round(sum(b["amount_eur"] for b in basis_rows if b["nature"] in ("ORDINARIA", "CORRENTE")), 2)
    if mode and not mode["needs_project"]:
        message = (f"Questo bando non chiede un progetto nuovo: la modalità è «{mode['label'].lower()}». Si calcola su {mode['base']}. "
                   + ("Le spese che l'azienda sostiene già sono quindi una base valida per questa stima." if mode["ordinary_costs_ok"] else
                      "Per questa modalità le spese di bilancio non sono la base: la bozza mostra gli acquisti e le persone dei piani dell'azienda dove ci sono."))
    else:
        message = ("Questa bozza parte dalle spese che l'azienda sostiene già: serve a capire l'ordine di grandezza e cosa il bando ammetterebbe, non è ancora un progetto. Un budget da presentare "
                   "si costruisce sul progetto: solo le spese nuove (acquisti, assunzioni) e quelle che il bando ammette per forma (spese generali a forfait, personale realmente dedicato con timesheet), "
                   "per la parte dedicata al progetto.")
    reality = {"new_eur": new_eur, "ordinary_eur": ordinary_eur, "personnel_eur": round(plan["personnel_base_eur"] * factor, 2) if "PERSONNEL" in allowed else 0.0, "mode": mode, "message": message}
    notes = list(plan["notes"])
    notes.insert(0, reality["message"])
    if "PERSONNEL" in allowed and people_info:
        notes.append("La quota di tempo di ogni persona deve essere quella realmente dedicata al progetto e dimostrata con un timesheet: il costo si rendiconta sulle ore vere, alla retribuzione vera (il controllo 15 la confronta con la busta paga).")
    if project_start:
        notes.append(f"Data di avvio del progetto: {project_start}. Il controllo della finestra del bando (46) la usa su ogni voce: una spesa anteriore alla domanda o al periodo ammesso non si finanzia.")
    notes.append(f"Anno del progetto: {target}. Le spese vengono dal budget dell'azienda, dal piano degli investimenti o dalla previsione del bilancio {plan['base_year']} (la fonte è scritta su ogni voce); sono una base da adattare al progetto.")
    if scale_pct < 100:
        notes.append(f"Quota di progetto: {scale_pct:g}% delle spese annue e del tempo di lavoro di ogni persona.")
    if dropped_types:
        notes.append("Escluse perché il bando le dichiara non ammissibili: " + ", ".join(f"{r['label'].lower()} ({_it_eur(r['amount_eur'] * factor)})" for r in dropped_types) + ".")
    if rules.get("requires_cup"):
        notes.append("Il bando richiede il CUP su ogni spesa: finché manca il controllo #50 mette la voce «in attesa». Inseriscilo in «Modifica voce».")
    if rules.get("requires_milestones"):
        notes.append("Il bando chiede di assegnare ogni voce a una milestone/SAL di rendicontazione (controllo #57): indicala in «Modifica voce».")
    return {"bando_id": bando_id, "base_year": plan["base_year"], "year": target, "scale_pct": scale_pct, "fit": fit, "cost_items": items, "needs_personnel": needs_personnel, "needs_category": [], "needs_review": [],
            "adjustments": adjustments, "excluded_categories": [{"category": c, "label": CATEGORY_LABEL[c]} for c in dropped_cat],
            "excluded_types": [{"code": r["code"], "label": r["label"], "amount_eur": round(r["amount_eur"] * factor, 2)} for r in dropped_types],
            "basis": basis_rows, "personnel": people_info, "needs_input": needs_input, "notes": notes, "reality": reality,
            "total_eur": round(sum(i.get("amount_eur") or 0 for i in items), 2), "personnel_base_eur": round(plan["personnel_base_eur"] * factor, 2)}
