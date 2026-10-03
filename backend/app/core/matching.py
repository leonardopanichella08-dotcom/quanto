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

from app.core import bandi, funds
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


def _estimate(rules: Dict[str, Any], by_cat: Dict[str, float], rate: float) -> Dict[str, Any]:
    allowed = [c for c in (rules.get("eligible_categories") or list(CATEGORIES)) if c in CATEGORIES]
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
    return {"rate_pct": round(rate * 100, 2), "eligible_base_eur": round(eligible_total, 2), "covered_eur": round(covered_total, 2),
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


def evaluate(bando_id: str, profile: Dict[str, Any], by_cat: Dict[str, float], year: int, today: Optional[date] = None) -> Optional[Dict[str, Any]]:
    today = today or date.today()
    detail = bandi.get_bando_detail(bando_id)
    if detail is None:
        return None
    rules = _rules(detail)
    row = Ingestion.get_bando(bando_id) or {}
    checks: List[Dict[str, Any]] = []
    missing: List[str] = []

    av = availability(detail, rules, row.get("deadline"), today)
    checks.append({"id": "availability", "label": "Apertura", "decisive": True, **av})

    allowed = [c for c in (rules.get("eligible_categories") or list(CATEGORIES)) if c in CATEGORIES]
    usable = [c for c in allowed if by_cat.get(c, 0) > 0]
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
    try:
        fund = funds.build_fund(bando_id, year)
    except funds.FundError as exc:
        if "finestra di ammissibilità" in str(exc):
            checks.append({"id": "window", "label": f"Finestra {year}", "decisive": True, "result": "FAIL", "detail": str(exc)})
    if fund is not None:
        estimate = _estimate(rules, by_cat, float(fund["coverage_pct"]))
        fund = {**fund, "allowed_categories": [getattr(c, "value", c) for c in fund["allowed_categories"]],
                "category_max_share": {getattr(k, "value", k): v for k, v in fund["category_max_share"].items()}}

    notes = []
    for key, text in (("requires_cup", "Richiede il CUP su ogni spesa."), ("requires_dnsh", "Richiede il rispetto del principio DNSH (non arrecare danno significativo)."),
                      ("requires_new_asset", "I beni devono essere nuovi di fabbrica."), ("min_durability_months", None)):
        if key in rules:
            notes.append(text if text else f"Vincolo di destinazione: almeno {rules[key]} mesi.")
    if estimate is None:
        btype = (benefit or {}).get("type") or ""
        notes.append("Il bando non dichiara un'aliquota di contributo (la percentuale delle spese che viene rimborsata): il beneficio non si può quantificare in automatico. "
                     + BENEFIT_EXPLANATION.get(btype, f"Tipo di aiuto: {btype}." if btype else ""))

    fails = [c for c in checks if c["result"] == "FAIL"]
    unknown_decisive = [c for c in checks if c["result"] == "UNKNOWN" and c["decisive"]]
    if fails:
        fit = "NON_ADATTO"
    elif unknown_decisive or estimate is None:
        fit = "DA_VERIFICARE"
    else:
        fit = "ADATTO"
    return {"bando_id": bando_id, "name": detail["name"], "issuer": detail.get("issuer"), "status": detail.get("status"), "fit": fit, "checks": checks, "estimate": estimate,
            "fund": fund, "benefit": benefit, "notes": notes, "missing_profile": sorted(set(missing)), "requirements_count": len(detail.get("requirements", [])),
            "rules_count": len(rules)}


def match_all(profile: Dict[str, Any], by_cat: Dict[str, float], year: int) -> Dict[str, Any]:
    """Tutti i bandi studiati (curati o con regole/requisiti letti), dal più utile al meno utile."""
    out = []
    for b in bandi.list_bandi():
        if b["bando_id"] == "QUANTO-SANDBOX-60" or not (b["curated"] or b["rules_count"] or b["requirements_count"]):
            continue
        r = evaluate(b["bando_id"], profile, by_cat, year)
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
def budget_template(owner: str, bando_id: str, scale_pct: float, fit: bool = True) -> Dict[str, Any]:
    """Voci di costo di partenza, prese dall'ultimo bilancio dell'azienda: solo le categorie ammesse dal bando, per la quota di progetto indicata
    e (se ``fit``) con le voci sopra i tetti del bando ridotte alla parte ammissibile. È una base da modificare, non un budget pronto."""
    from app.core import company_profile as cp
    from app.core.fonte_c import service as fonte_c

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
    year = years[-1]
    fdata, fsrc = fin[year]
    factor = scale_pct / 100.0
    allowed = [c for c in (rules.get("eligible_categories") or list(CATEGORIES)) if c in CATEGORIES]

    lines: List[Dict[str, Any]] = []
    doc_ids = {s.get("document_id") for k, s in fsrc.items() if not k.startswith("_") and s.get("origin") == "DOCUMENT"}
    pending = 0
    for did in sorted(d for d in doc_ids if d):
        try:
            ex = fonte_c.balance_expenses(did, owner)
        except (KeyError, fonte_c.DocumentError):
            continue
        if ex["fiscal_year"] == year:
            lines += [{"description": ln["description"], "category": ln["category"], "amount": float(ln["amount_eur"]), "ref": f"DOC-FC-{did}"} for ln in ex["lines"]]
            pending += len(ex["needs_review"]) + len(ex["needs_category"])
    covered_cats = {ln["category"] for ln in lines}
    for c in CATEGORIES:                                    # categorie inserite a mano o senza righe di dettaglio: una voce sola con il totale
        if c not in covered_cats and fdata.get(cp.FIN_KEY[c]):
            lines.append({"description": f"{CATEGORY_LABEL[c]} (totale annuo)", "category": c, "amount": float(fdata[cp.FIN_KEY[c]]), "ref": f"PROFILO-{year}"})

    excluded = sorted({ln["category"] for ln in lines if ln["category"] not in allowed})
    kept = sorted((ln for ln in lines if ln["category"] in allowed), key=lambda ln: -ln["amount"])
    head, tail = kept[:15], kept[15:]
    for c in sorted({ln["category"] for ln in tail}):       # le voci più piccole si raggruppano per categoria
        rest = [ln for ln in tail if ln["category"] == c]
        head.append({"description": f"Altre voci di {CATEGORY_LABEL[c].lower()} ({len(rest)} righe)", "category": c, "amount": sum(ln["amount"] for ln in rest), "ref": rest[0]["ref"]})

    by_cat: Dict[str, float] = {}
    for ln in head:
        by_cat[ln["category"]] = by_cat.get(ln["category"], 0.0) + ln["amount"] * factor
    adjustments = _adjustments(rules, by_cat, allowed) if fit else []
    reduce = {a["category"]: a["eligible_eur"] / a["forecast_eur"] for a in adjustments}

    items = []
    for n, ln in enumerate(head, 1):
        ratio = reduce.get(ln["category"], 1.0)
        amount = round(ln["amount"] * factor * ratio, 2)
        if amount <= 0:
            continue
        note = f" · ridotta al {ratio * 100:.0f}% per il tetto del bando" if ratio < 1 else ""
        items.append({"item_id": f"TPL-{n:02d}", "description": f"{ln['description']} — da bilancio {year}, quota progetto {scale_pct:g}%{note}"[:200], "category": ln["category"],
                      "amount_eur": amount, "source_c_ref": ln["ref"]})
    notes = [f"Importi del bilancio {year} moltiplicati per la quota di progetto ({scale_pct:g}%): sono una base da adattare al tuo progetto, non un budget pronto."]
    if pending:
        notes.append(f"{pending} righe del bilancio non sono ancora verificate e non sono incluse.")
    if any(i["source_c_ref"].startswith("PROFILO-") for i in items):
        notes.append("Alcune voci vengono da totali inseriti a mano nel profilo: allega il documento che le giustifica prima di controllare il budget.")
    if any(i["category"] == "PERSONNEL" for i in items):
        notes.append("Per il personale servono livello, CCNL, RAL e quota di tempo di ciascuna persona: completali nel Budget.")
    return {"bando_id": bando_id, "base_year": year, "scale_pct": scale_pct, "fit": fit, "cost_items": items, "needs_category": [], "needs_review": [],
            "adjustments": adjustments, "excluded_categories": [{"category": c, "label": CATEGORY_LABEL[c]} for c in excluded], "notes": notes,
            "total_eur": round(sum(i["amount_eur"] for i in items), 2)}
