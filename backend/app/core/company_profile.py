"""Profilo aziendale: i dati dell'impresa e i suoi bilanci per esercizio, ricavati dai documenti caricati o inseriti a mano.

Tre regole, uguali per ogni dato:
- **di dove viene**: ogni valore ricorda se è letto da un documento (con quale) o inserito dall'utente. Un valore inserito a mano non viene mai
  sovrascritto da una nuova lettura dei documenti;
- **solo ciò che è sicuro**: dai documenti entrano nel profilo i campi letti con sicurezza o confermati da una persona; le righe ancora in verifica
  non entrano, e il totale dell'anno viene segnalato come parziale finché non si verificano;
- **niente valori inventati**: un dato mancante resta mancante e finisce nell'elenco «da completare». La stima dell'anno dopo parte dai dati veri e le
  variazioni le sceglie l'utente (o le accetta dai suoi due ultimi bilanci): non ne esiste una predefinita.
"""
from __future__ import annotations

import json
import re
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from app.core import events
from app.core.db import connect
from app.core.fonte_c import service as fonte_c

CATEGORIES = ("PERSONNEL", "CAPITAL_ASSETS", "CONSULTING", "OVERHEAD", "TRAINING")
CATEGORY_LABEL = {"PERSONNEL": "Personale", "CAPITAL_ASSETS": "Beni strumentali", "CONSULTING": "Consulenze", "OVERHEAD": "Spese generali", "TRAINING": "Formazione"}
FIN_KEY = {"PERSONNEL": "personnel_eur", "CAPITAL_ASSETS": "capital_assets_eur", "CONSULTING": "consulting_eur", "OVERHEAD": "overhead_eur", "TRAINING": "training_eur"}

REGIONS = ["Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia-Romagna", "Friuli Venezia Giulia", "Lazio", "Liguria", "Lombardia", "Marche", "Molise",
           "Piemonte", "Puglia", "Sardegna", "Sicilia", "Toscana", "Trentino-Alto Adige", "Umbria", "Valle d'Aosta", "Veneto"]
_PROVINCES = {
    "Abruzzo": "AQ CH PE TE", "Basilicata": "MT PZ", "Calabria": "CZ CS KR RC VV", "Campania": "AV BN CE NA SA", "Emilia-Romagna": "BO FE FC MO PR PC RA RE RN",
    "Friuli Venezia Giulia": "GO PN TS UD", "Lazio": "FR LT RI RM VT", "Liguria": "GE IM SP SV", "Lombardia": "BG BS CO CR LC LO MN MI MB PV SO VA",
    "Marche": "AN AP FM MC PU", "Molise": "CB IS", "Piemonte": "AL AT BI CN NO TO VB VC", "Puglia": "BA BT BR FG LE TA", "Sardegna": "CA NU OR SS SU CI OG OT VS",
    "Sicilia": "AG CL CT EN ME PA RG SR TP", "Toscana": "AR FI GR LI LU MS PI PT PO SI", "Trentino-Alto Adige": "BZ TN", "Umbria": "PG TR",
    "Valle d'Aosta": "AO", "Veneto": "BL PD RO TV VE VR VI",
}
PROVINCE_REGION = {sigla: region for region, siglas in _PROVINCES.items() for sigla in siglas.split()}

# (etichetta, tipo, serve per la completezza?)
PROFILE_FIELDS: Dict[str, Tuple[str, str, bool]] = {
    "legal_name": ("Ragione sociale", "text", True),
    "vat_number": ("Partita IVA", "vat", True),
    "legal_form": ("Forma giuridica", "text", True),
    "ateco_code": ("Codice ATECO", "ateco", True),
    "region": ("Regione della sede", "region", True),
    "province": ("Provincia della sede", "province", False),
    "founded_year": ("Anno di costituzione", "year", False),
    "employees": ("Numero di dipendenti", "count", True),
    "is_innovative_startup": ("Start-up innovativa iscritta al registro", "bool", True),
}
FIN_FIELDS: Dict[str, Tuple[str, str]] = {
    "revenue_eur": ("Ricavi delle vendite e delle prestazioni", "money"),
    "net_result_eur": ("Utile (perdita) dell'esercizio", "money"),
    "total_costs_eur": ("Totale costi della produzione", "money"),
    "employees_avg": ("Numero medio di dipendenti", "count"),
    **{FIN_KEY[c]: (f"Costi: {CATEGORY_LABEL[c].lower()}", "money") for c in CATEGORIES},
}
FIN_REQUIRED = ["revenue_eur", *FIN_KEY.values()]
REGISTRY_TO_PROFILE = {"company_name": "legal_name", "vat_number": "vat_number", "legal_form": "legal_form", "ateco_code": "ateco_code", "province": "province",
                       "founded_year": "founded_year", "employees": "employees"}


class ProfileError(ValueError):
    pass


# ------------------------------------------------------------------------------------------------ validazione
def _clean(kind: str, value: Any) -> Any:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if kind == "text":
        return str(value).strip()[:200]
    if kind == "vat":
        digits = re.sub(r"\s|^IT", "", str(value).upper())
        if not re.fullmatch(r"\d{11}", digits):
            raise ProfileError("La partita IVA ha 11 cifre")
        return digits
    if kind == "ateco":
        v = str(value).strip().replace(",", ".")
        if not re.fullmatch(r"\d{2}(\.\d{2}(\.\d{1,2})?)?", v):
            raise ProfileError("Il codice ATECO ha il formato 62.01 (o 62.01.00)")
        return v
    if kind == "region":
        m = [r for r in REGIONS if r.lower() == str(value).strip().lower()]
        if not m:
            raise ProfileError("Regione non riconosciuta")
        return m[0]
    if kind == "province":
        v = str(value).strip().upper()
        if v not in PROVINCE_REGION:
            raise ProfileError("Sigla di provincia non riconosciuta (es. MI, RM, TO)")
        return v
    if kind == "year":
        try:
            y = int(str(value).strip())
        except ValueError:
            raise ProfileError("Anno non valido") from None
        if not 1800 <= y <= date.today().year:
            raise ProfileError("Anno non valido")
        return y
    if kind == "count":
        try:
            n = int(float(str(value).replace(",", ".").strip()))
        except ValueError:
            raise ProfileError("Numero non valido") from None
        if not 0 <= n <= 1_000_000:
            raise ProfileError("Numero non valido")
        return n
    if kind == "bool":
        if isinstance(value, bool):
            return value
        v = str(value).strip().lower()
        if v in ("true", "si", "sì", "1", "yes"):
            return True
        if v in ("false", "no", "0"):
            return False
        raise ProfileError("Rispondi sì o no")
    if kind == "money":
        try:
            if isinstance(value, (int, float)):
                x = float(value)
            else:
                s = str(value).strip().replace("€", "").replace(" ", "")
                x = float(s.replace(".", "").replace(",", ".") if "," in s else s)
        except ValueError:
            raise ProfileError("Importo non valido") from None
        if abs(x) > 1e12:
            raise ProfileError("Importo non valido")
        return round(x, 2)
    raise ProfileError("Tipo di dato sconosciuto")


# ------------------------------------------------------------------------------------------------ lettura e scrittura
def _load_profile(owner: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    with connect() as conn:
        r = conn.execute("SELECT data, sources FROM company_profiles WHERE owner=?", (owner,)).fetchone()
    return (json.loads(r["data"]), json.loads(r["sources"])) if r else ({}, {})


def _save_profile(owner: str, data: Dict[str, Any], sources: Dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute("INSERT INTO company_profiles (owner, data, sources, updated_at) VALUES (?,?,?,?) ON CONFLICT (owner) DO UPDATE SET data=excluded.data, sources=excluded.sources, "
                     "updated_at=excluded.updated_at", (owner, json.dumps(data, ensure_ascii=False), json.dumps(sources, ensure_ascii=False), events.now_iso()))


def _load_financials(owner: str) -> Dict[int, Tuple[Dict[str, Any], Dict[str, Any]]]:
    with connect() as conn:
        rows = conn.execute("SELECT fiscal_year, data, sources FROM company_financials WHERE owner=? ORDER BY fiscal_year", (owner,)).fetchall()
    return {r["fiscal_year"]: (json.loads(r["data"]), json.loads(r["sources"])) for r in rows}


def _save_financials(owner: str, year: int, data: Dict[str, Any], sources: Dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute("INSERT INTO company_financials (owner, fiscal_year, data, sources, updated_at) VALUES (?,?,?,?,?) ON CONFLICT (owner, fiscal_year) DO UPDATE SET "
                     "data=excluded.data, sources=excluded.sources, updated_at=excluded.updated_at",
                     (owner, year, json.dumps(data), json.dumps(sources), events.now_iso()))


def update_profile(owner: str, updates: Dict[str, Any], actor: Optional[str] = None) -> None:
    """Valori inseriti dall'utente. Vuoto = cancella il valore. La provincia, se la regione non c'è, ne ricava la regione."""
    data, sources = _load_profile(owner)
    for key, raw in updates.items():
        if key not in PROFILE_FIELDS:
            raise ProfileError(f"Campo sconosciuto: {key}")
        value = _clean(PROFILE_FIELDS[key][1], raw)
        if value is None:
            data.pop(key, None); sources.pop(key, None)
        else:
            data[key] = value; sources[key] = {"origin": "MANUAL"}
    if "province" in updates and data.get("province") and "region" not in updates and sources.get("region", {}).get("origin") != "MANUAL":
        data["region"] = PROVINCE_REGION[data["province"]]; sources["region"] = {"origin": "DERIVED", "from": "province"}
    _save_profile(owner, data, sources)
    events.record("profile.update", f"Profilo aziendale aggiornato ({', '.join(sorted(updates))})", actor=actor or owner)


def update_financials(owner: str, year: int, updates: Dict[str, Any], actor: Optional[str] = None) -> None:
    if not 1990 <= year <= date.today().year + 1:
        raise ProfileError("Esercizio non valido")
    all_fin = _load_financials(owner)
    data, sources = all_fin.get(year, ({}, {}))
    for key, raw in updates.items():
        if key not in FIN_FIELDS:
            raise ProfileError(f"Campo sconosciuto: {key}")
        value = _clean(FIN_FIELDS[key][1], raw)
        if value is None:
            data.pop(key, None); sources.pop(key, None)
        else:
            data[key] = value; sources[key] = {"origin": "MANUAL"}
    _save_financials(owner, year, data, sources)
    events.record("profile.financials", f"Dati dell'esercizio {year} aggiornati ({', '.join(sorted(updates))})", actor=actor or owner)


# ------------------------------------------------------------------------------------------------ lettura dai documenti
def _usable(doc: Dict[str, Any], key: str) -> Optional[Dict[str, Any]]:
    for f in doc["fields"]:
        if f["field_key"] == key and f["status"] in fonte_c.USABLE:
            return f
    return None


def sync_from_documents(owner: str, actor: Optional[str] = None) -> Dict[str, Any]:
    """Rilegge i documenti dell'utente e aggiorna profilo e bilanci. I valori inseriti a mano restano."""
    docs = [fonte_c.get(d["id"], owner) for d in fonte_c.list_documents(owner)]
    docs = [d for d in docs if d and d["status"] != "FAILED"]
    data, sources = _load_profile(owner)
    changed = {"profile": [], "years": {}}
    live = {d["id"] for d in docs}

    def orphan(src: Dict[str, Any]) -> bool:               # valore letto da un documento che l'utente ha poi eliminato
        return src.get("origin") in ("DOCUMENT", "DERIVED") and src.get("document_id") is not None and src["document_id"] not in live

    for key in [k for k, v in sources.items() if orphan(v)]:
        data.pop(key, None); sources.pop(key, None)
        changed["profile"].append(key)
    for year, (fdata, fsrc) in _load_financials(owner).items():
        gone = [k for k, v in fsrc.items() if not k.startswith("_") and orphan(v)]
        for k in gone:
            fdata.pop(k, None); fsrc.pop(k, None)
        if fsrc.get("_partial", {}).get("document_id") not in live:
            fsrc.pop("_partial", None)
        if gone:
            if fdata:
                _save_financials(owner, year, fdata, fsrc)
            else:
                with connect() as conn:
                    conn.execute("DELETE FROM company_financials WHERE owner=? AND fiscal_year=?", (owner, year))

    def put(store: Dict[str, Any], src: Dict[str, Any], key: str, value: Any, doc_id: int, bucket: List[str]) -> None:
        if src.get(key, {}).get("origin") == "MANUAL":
            return
        if store.get(key) != value:
            bucket.append(key)
        store[key] = value; src[key] = {"origin": "DOCUMENT", "document_id": doc_id}

    for d in sorted((x for x in docs if x["doc_type"] == "COMPANY_REGISTRY"), key=lambda x: x["id"]):
        for fkey, pkey in REGISTRY_TO_PROFILE.items():
            f = _usable(d, fkey)
            if not f:
                continue
            try:
                value = _clean(PROFILE_FIELDS[pkey][1], f["value"])
            except ProfileError:
                continue                                   # un valore letto in modo non valido non entra nel profilo: resta da compilare
            if value is not None:
                put(data, sources, pkey, value, d["id"], changed["profile"])
        if data.get("province") and sources.get("region", {}).get("origin") != "MANUAL" and data["province"] in PROVINCE_REGION:
            put(data, sources, "region", PROVINCE_REGION[data["province"]], d["id"], changed["profile"])
            sources["region"] = {"origin": "DERIVED", "from": "province", "document_id": d["id"]}
    _save_profile(owner, data, sources)

    latest: Dict[int, Dict[str, Any]] = {}          # per esercizio vale il bilancio caricato per ultimo
    for d in docs:
        if d["doc_type"] != "BALANCE_SHEET":
            continue
        fy = _usable(d, "fiscal_year")
        if fy:
            y = int(fy["value"])
            if y not in latest or d["id"] > latest[y]["id"]:
                latest[y] = d
    fin_all = _load_financials(owner)
    for year, d in sorted(latest.items()):
        fdata, fsrc = fin_all.get(year, ({}, {}))
        bucket: List[str] = []
        sums: Dict[str, float] = {}
        pending = 0
        for f in d["fields"]:
            if f["field_key"] != "expense_line":
                continue
            p = f["parsed"]
            if f["status"] in fonte_c.USABLE and p.get("category"):
                sums[p["category"]] = round(sums.get(p["category"], 0.0) + float(p["amount_eur"]), 2)
            else:
                pending += 1
        for cat, amount in sums.items():
            put(fdata, fsrc, FIN_KEY[cat], amount, d["id"], bucket)
        for fkey in ("revenue_eur", "net_result_eur", "total_costs_eur", "employees_avg"):
            f = _usable(d, fkey)
            if f:
                try:
                    put(fdata, fsrc, fkey, _clean(FIN_FIELDS[fkey][1], f["value"]), d["id"], bucket)
                except ProfileError:
                    continue
        if pending:
            fsrc["_partial"] = {"document_id": d["id"], "pending_lines": pending}
        else:
            fsrc.pop("_partial", None)
        _save_financials(owner, year, fdata, fsrc)
        changed["years"][year] = bucket
    events.record("profile.sync", f"Profilo riletto da {len(docs)} documenti: {len(changed['profile'])} dati aziendali, {len(changed['years'])} esercizi", actor=actor or owner)
    return changed


# ------------------------------------------------------------------------------------------------ dimensione dell'impresa
def size_class(employees: Optional[int], revenue_eur: Optional[float]) -> Optional[Dict[str, Any]]:
    """Micro / piccola / media / grande secondo la raccomandazione UE 2003/361 (soglie di dipendenti e fatturato). Senza il totale di bilancio e senza
    guardare le imprese collegate: per questo è una classificazione indicativa."""
    if employees is None:
        return None
    tiers = [("MICRO", "Microimpresa", 10, 2_000_000), ("SMALL", "Piccola impresa", 50, 10_000_000), ("MEDIUM", "Media impresa", 250, 50_000_000)]
    for code, label, max_emp, max_rev in tiers:
        if employees < max_emp and (revenue_eur is None or revenue_eur <= max_rev):
            return {"code": code, "label": label, "is_sme": True, "provisional": revenue_eur is None,
                    "note": "Indicativa: soglie UE su dipendenti e fatturato, senza il totale di bilancio e senza le imprese collegate." + ("" if revenue_eur is not None else " Manca il fatturato.")}
    return {"code": "LARGE", "label": "Grande impresa", "is_sme": False, "provisional": False, "note": "Oltre le soglie UE delle PMI."}


# ------------------------------------------------------------------------------------------------ panoramica e completezza
def overview(owner: str) -> Dict[str, Any]:
    data, sources = _load_profile(owner)
    fin = _load_financials(owner)
    years = sorted(fin)
    last_year = years[-1] if years else None
    last = fin[last_year][0] if last_year else {}

    effective = dict(data)
    eff_src = dict(sources)
    if effective.get("employees") is None and last.get("employees_avg") is not None:       # dipendenti dall'ultimo bilancio se la visura non li dice
        effective["employees"] = last["employees_avg"]; eff_src["employees"] = {"origin": "DOCUMENT", "document_id": fin[last_year][1].get("employees_avg", {}).get("document_id"), "from": f"bilancio {last_year}"}

    fields = []
    missing: List[Dict[str, Any]] = []
    for key, (label, kind, required) in PROFILE_FIELDS.items():
        filled = key in effective and effective[key] is not None
        fields.append({"key": key, "label": label, "kind": kind, "required": required, "value": effective.get(key), "source": eff_src.get(key)})
        if required and not filled:
            missing.append({"scope": "profile", "key": key, "label": label})
    financials = []
    for y in years:
        fdata, fsrc = fin[y]
        financials.append({"fiscal_year": y, "values": fdata, "sources": {k: v for k, v in fsrc.items() if not k.startswith("_")}, "partial": fsrc.get("_partial")})
    if last_year is not None:
        for key in FIN_REQUIRED:
            if last.get(key) is None:
                missing.append({"scope": "financial", "key": key, "year": last_year, "label": FIN_FIELDS[key][0]})
    else:
        missing.append({"scope": "financial", "key": "balance", "year": None, "label": "Nessun bilancio: carica un bilancio o inserisci i dati dell'ultimo esercizio"})
    total = sum(1 for f in fields if f["required"]) + len(FIN_REQUIRED)
    done = sum(1 for f in fields if f["required"] and f["value"] is not None) + (sum(1 for k in FIN_REQUIRED if last.get(k) is not None) if last_year is not None else 0)
    docs = fonte_c.list_documents(owner)
    return {"fields": fields, "financials": financials, "last_year": last_year, "missing": missing, "completeness_pct": round(100 * done / total),
            "size": size_class(effective.get("employees"), last.get("revenue_eur")), "documents": {"total": len(docs), "to_review": sum(d["to_review"] for d in docs)},
            "fin_fields": [{"key": k, "label": v[0], "kind": v[1], "required": k in FIN_REQUIRED} for k, v in FIN_FIELDS.items()], "regions": REGIONS}


def profile_values(owner: str) -> Dict[str, Any]:
    """Il profilo come semplice dizionario (con i dipendenti dall'ultimo bilancio se mancano), per l'abbinamento ai bandi."""
    ov = overview(owner)
    out = {f["key"]: f["value"] for f in ov["fields"] if f["value"] is not None}
    out["size"] = ov["size"]
    return out


# ------------------------------------------------------------------------------------------------ stima dell'anno successivo
def forecast(owner: str, year: int, growth: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """Spese per categoria dell'esercizio ``year``: ultimo bilancio disponibile (≤ year-1) × (1 + variazione annua)^anni.
    La variazione la sceglie l'utente; dai suoi due ultimi bilanci si ricava solo un suggerimento, mai applicato da solo."""
    growth = growth or {}
    fin = _load_financials(owner)
    candidates = [y for y in sorted(fin) if y < year and any(fin[y][0].get(FIN_KEY[c]) is not None for c in CATEGORIES)]
    if not candidates:
        raise ProfileError("Mancano i dati di bilancio: carica un bilancio nel profilo o inserisci i costi dell'ultimo esercizio")
    base_year = candidates[-1]
    base, prev = fin[base_year][0], fin.get(base_year - 1, ({}, {}))[0]
    rows, missing, warnings = [], [], []
    for cat in CATEGORIES:
        b = base.get(FIN_KEY[cat])
        if b is None:
            missing.append({"category": cat, "label": CATEGORY_LABEL[cat], "year": base_year})
            continue
        p = prev.get(FIN_KEY[cat])
        suggested = round(b / p - 1, 4) if p and p > 0 and b >= 0 else None
        g = growth.get(cat)
        if g is not None and not -0.95 <= g <= 5:
            raise ProfileError(f"Variazione non plausibile per {CATEGORY_LABEL[cat]}")
        applied = g if g is not None else 0.0
        amount = round(b * (1 + applied) ** (year - base_year), 2)
        rows.append({"category": cat, "label": CATEGORY_LABEL[cat], "baseline_eur": b, "previous_eur": p, "suggested_growth": suggested, "growth_applied": applied,
                     "growth_is_assumption": g is None, "forecast_eur": amount})
    partial = fin[base_year][1].get("_partial")
    if partial:
        warnings.append(f"Nel bilancio {base_year} ci sono {partial['pending_lines']} righe ancora da verificare: i totali per categoria sono parziali.")
    if year - base_year > 1:
        warnings.append(f"L'ultimo bilancio disponibile è del {base_year}: la stima del {year} proietta {year - base_year} anni.")
    return {"fiscal_year": year, "base_year": base_year, "categories": rows, "missing": missing, "warnings": warnings,
            "total_baseline_eur": round(sum(r["baseline_eur"] for r in rows), 2), "total_forecast_eur": round(sum(r["forecast_eur"] for r in rows), 2)}
