"""Quanto vale ogni bando in euro, con un solo criterio: ogni numero viene da una fonte ufficiale o da una formula dichiarata, e le ipotesi si dicono.

Da dove viene la percentuale di un bando, in quest'ordine:
1. **regola pubblicata** (``contribution_rate_pct``): il bando dichiara «contributo pari al N% delle spese»;
2. **modello del bando** (bandi curati): contributo sugli interessi, risparmio fiscale, cofinanziamento a fondo perduto, sovvenzione a tassi di call, garanzia.
   Ogni parametro ha la sua fonte; ciò che dipende da scelte dell'impresa (quanto finanziare, quale call) è un'ipotesi scritta in chiaro;
3. **testo ufficiale letto**: tabelle di intensità per dimensione d'impresa (``benefit_extract``), con la riga di testo da cui vengono.

Il risultato è un intervallo (prudente → massimo) e la natura del valore: contributo vero, equivalente di un finanziamento agevolato, risparmio fiscale
oppure garanzia (che non è un guadagno e non si somma).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core import benefit_extract
from app.core.company_profile import CATEGORIES
from app.core.db import connect

KIND_LABEL = {
    "FONDO_PERDUTO": "Contributo a fondo perduto",
    "CONTO_INTERESSI": "Contributo sugli interessi (valore equivalente)",
    "RISPARMIO_FISCALE": "Risparmio fiscale (stima)",
    "GARANZIA": "Garanzia pubblica (non è un contributo: non si somma)",
}
SUMMABLE = {"FONDO_PERDUTO", "CONTO_INTERESSI", "RISPARMIO_FISCALE"}
IRES_RATE = 0.24            # art. 77 TUIR: aliquota IRES ordinaria

_CACHE: Dict[Any, Dict[str, Any]] = {}


def conventional_interest_share(annual_rate: float, years: int = 5, per_year: int = 2) -> float:
    """Interessi totali di un prestito di 1 € a rate costanti posticipate (tasso periodico composto), come quota del capitale."""
    i = (1 + annual_rate) ** (1 / per_year) - 1
    n = years * per_year
    pmt = i / (1 - (1 + i) ** -n)
    return n * pmt - 1


def _sources_text(bando_id: str) -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT sha256, url, name, tier, text FROM bando_sources WHERE bando_id=? ORDER BY CASE tier WHEN 'UFFICIALE' THEN 0 ELSE 1 END", (bando_id,)).fetchall()
    return [dict(r) for r in rows]


def _from_texts(bando_id: str) -> Dict[str, Any]:
    docs = _sources_text(bando_id)
    key = (bando_id, tuple(d["sha256"] for d in docs))
    if key in _CACHE:
        return _CACHE[key]
    rows: List[Dict[str, Any]] = []
    caps: List[float] = []
    dm: List[Dict[str, Any]] = []
    for d in docs:
        if d["tier"] == "SECONDARIA":                      # le percentuali si leggono solo dal testo ufficiale
            continue
        rows += benefit_extract.intensity_rows(d["text"] or "", d["url"])
        caps += benefit_extract.caps(d["text"] or "")
        dm += benefit_extract.de_minimis_mentions(d["text"] or "", d["url"])
    out = {"rows": rows, "caps": sorted(set(caps)), "dm": dm}
    _CACHE.clear() if len(_CACHE) > 200 else None
    _CACHE[key] = out
    return out


def de_minimis_info(bando_id: str, model: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Il bando è in regime de minimis? Si dice solo se lo dice una fonte: il modello curato del bando o il testo ufficiale letto.
    ``applies`` = conta contro il plafond (per prudenza anche se il testo lo cita solo); ``mentioned`` = il testo lo nomina; ``basis`` = da dove viene."""
    if model and model.get("de_minimis"):
        return {"applies": True, "basis": "MODELLO", "mentioned": True,
                "evidence": [{"text": "Il fondo perduto di questo bando rientra nel regime de minimis (Reg. UE 2023/2831): conta contro il tetto di 300.000 € in tre anni.", "url": None}, *(model.get("evidence") or [])[:1]]}
    hits = _from_texts(bando_id).get("dm", [])
    yes = [h for h in hits if not h["negated"]]
    if yes:
        return {"applies": True, "basis": "TESTO", "mentioned": True, "evidence": [{"text": h["text"], "url": h["url"]} for h in yes[:2]]}
    if hits:
        return {"applies": False, "basis": "TESTO", "mentioned": True, "evidence": [{"text": h["text"], "url": h["url"]} for h in hits[:2]]}
    return {"applies": False, "basis": None, "mentioned": False, "evidence": []}


def has_intensity(bando_id: str) -> bool:
    """Il bando ha una percentuale (o un modello di calcolo) da cui ricavare un valore? Serve alla ricerca per decidere se cercare ancora."""
    from app.core import bandi
    with connect() as conn:
        r = conn.execute("SELECT 1 FROM rules WHERE bando_id=? AND rule_key='contribution_rate_pct' AND status='PUBLISHED'", (bando_id,)).fetchone()
    return bool(r or bandi.valuation_model(bando_id) or _from_texts(bando_id)["rows"])


def _model_value(model: Dict[str, Any], by_cat: Dict[str, float], profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    kind = model["kind"]
    cats = model.get("categories")
    base = sum(by_cat.get(c, 0.0) for c in (cats or CATEGORIES))
    assumptions = list(model.get("assumptions", []))
    if kind == "CONTO_INTERESSI":
        years, share = model.get("years", 5), model.get("financed_share", 1.0)
        lo = conventional_interest_share(model["annual_rate_low"], years) * share
        hi = conventional_interest_share(model["annual_rate_high"], years) * share
        return {"kind": kind, "rate_low": lo, "rate_high": hi, "categories": cats, "assumptions": assumptions, "cap_low": None, "cap_high": None}
    if kind == "RISPARMIO_FISCALE":
        legal = str(profile.get("legal_form") or "").upper()
        if legal and not any(x in legal for x in ("RESPONSABILITA", "S.R.L", "SRL", "AZIONI", "S.P.A", "SPA", "ACCOMANDITA")):
            assumptions = assumptions + [f"Forma giuridica «{profile.get('legal_form')}»: l'aliquota IRES del 24% vale per le società di capitali; per altre forme il risparmio cambia."]
        saving = 0.0
        left = base
        prev = 0.0
        for t in model["tiers"]:
            slice_ = max(0.0, min(left, t["up_to_eur"] - prev))
            saving += slice_ * t["rate"] * IRES_RATE
            left -= slice_
            prev = t["up_to_eur"]
            if left <= 0:
                break
        rate = saving / base if base else 0.0
        return {"kind": kind, "rate_low": rate, "rate_high": rate, "categories": cats, "assumptions": assumptions, "cap_low": None, "cap_high": None}
    if kind == "FONDO_PERDUTO":
        return {"kind": kind, "rate_low": model["rate_low"], "rate_high": model["rate_high"], "categories": cats, "assumptions": assumptions,
                "cap_low": model.get("cap_low"), "cap_high": model.get("cap_high"), "de_minimis": bool(model.get("de_minimis"))}
    if kind == "GARANZIA":
        financed = base * model.get("financed_share", 1.0)
        return {"kind": kind, "guaranteed_low_eur": round(financed * model["rate_low"], 2), "guaranteed_high_eur": round(financed * model["rate_high"], 2),
                "financed_eur": round(financed, 2), "categories": cats, "assumptions": assumptions}
    return None


def value_bando(bando_id: str, detail: Dict[str, Any], rules: Dict[str, Any], profile: Dict[str, Any], by_cat: Dict[str, float]) -> Optional[Dict[str, Any]]:
    """None solo se né le regole, né il modello, né il testo ufficiale danno una percentuale."""
    from app.core import bandi
    size = (profile.get("size") or {}).get("code")
    if rules.get("contribution_rate_pct") is not None:
        r = float(rules["contribution_rate_pct"])
        return {"kind": "FONDO_PERDUTO", "origin": "REGOLA", "rate_low": r, "rate_high": r, "categories": None, "cap_low": None, "cap_high": None,
                "assumptions": [], "evidence": [{"text": "Percentuale dichiarata dal bando tra le regole pubblicate.", "url": None}]}
    model = (bandi.valuation_model(bando_id) or None)
    if model:
        v = _model_value(model, by_cat, profile)
        if v:
            v.update({"origin": "MODELLO", "evidence": model.get("evidence", []), "model_note": model.get("note")})
            return v
    t = _from_texts(bando_id)
    rg = benefit_extract.range_for(t["rows"], size)
    if rg:
        caps = t["caps"]
        return {"kind": "FONDO_PERDUTO", "origin": "TESTO", "rate_low": rg["low"], "rate_high": rg["high"], "categories": None,
                "cap_low": caps[0] if caps else None, "cap_high": caps[-1] if caps else None,
                "assumptions": ["Percentuali lette dalla tabella di intensità del testo ufficiale, per la dimensione dell'impresa: la prima è la base, la seconda include tutte le maggiorazioni (collaborazione, dimensione, diffusione dei risultati).",
                                *(["Il contributo ha un massimo per progetto (da {:,.0f} a {:,.0f} €, secondo la categoria di progetto).".format(caps[0], caps[-1]).replace(",", ".")] if caps else [])],
                "evidence": [{"text": r["text"], "url": r.get("url")} for r in rg["rows"][:4]]}
    return None
