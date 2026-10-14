"""Tutto ciò che si sa dell'azienda dai documenti caricati, in forma di fatti con la loro fonte.

I documenti (bilanci, buste paga, fogli Excel…) producono campi; qui li si rimette insieme per ciò che servono a fare:
- **l'organico**: persona per persona con livello, contratto, RAL, ore e (se c'è) la RAL letta dalla busta paga;
- **i beni** del libro cespiti e il loro piano di ammortamento;
- **le spese previste**: il budget dell'azienda, il piano degli investimenti, il piano delle assunzioni;
- **le spese per voce** ricavate dalle fatture ricevute;
- **gli aiuti** già ricevuti.

Si usa solo ciò che è sicuro o confermato. Se lo stesso tipo di fatto sta in più documenti si prende l'ultimo caricato (è la versione aggiornata): non si
sommano due copie dello stesso registro. Niente viene inventato: ciò che manca resta nell'elenco «mancanti».
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from app.core import fonte_b
from app.core.db import connect
from app.core.fonte_c import parsers, service as fonte_c
from app.core.fonte_c.sheets import FACT_KEYS


def _rows(owner: str, keys: List[str]) -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT f.id, f.field_key, f.value, f.status, f.page, f.snippet, d.id AS doc_id, d.filename, d.doc_type FROM client_document_fields f "
            "JOIN client_documents d ON d.id=f.document_id WHERE d.owner=? AND d.status <> 'FAILED' AND f.field_key = ANY(?) ORDER BY d.id, f.id", (owner, keys)).fetchall()
    return [dict(r) for r in rows if r["status"] in fonte_c.USABLE]


def facts(owner: str) -> Dict[str, List[Dict[str, Any]]]:
    """Fatti letti dai fogli: per ogni tipo, quelli dell'ultimo documento caricato che lo contiene."""
    out: Dict[str, List[Dict[str, Any]]] = {k: [] for k in FACT_KEYS}
    latest: Dict[str, int] = {}
    rows = _rows(owner, list(FACT_KEYS))
    for r in rows:
        latest[r["field_key"]] = max(latest.get(r["field_key"], 0), r["doc_id"])
    for r in rows:
        if r["doc_id"] != latest[r["field_key"]]:
            continue
        d = json.loads(r["value"])
        d["_doc"] = {"id": r["doc_id"], "filename": r["filename"], "where": r["snippet"]}
        out[r["field_key"]].append(d)
    return out


def _codes() -> List[str]:
    try:
        return list(fonte_b.load().ccnl_codes())
    except Exception:
        return []


def ccnl_code(text: Optional[str], codes: Optional[List[str]] = None) -> Optional[str]:
    """Il codice del contratto collettivo di Fonte B che il testo nomina (uno solo, altrimenti nessuno: non si sceglie al posto di chi legge)."""
    if not text:
        return None
    codes = _codes() if codes is None else codes
    n = parsers.norm(text)
    hits = [c for c in codes if c in n.replace(" ", "_") or c.replace("_", " ") in n]
    return hits[0] if len(hits) == 1 else None


def _payslips(owner: str) -> Dict[str, Dict[str, Any]]:
    """Per ogni lavoratore (token) la busta paga più recente: livello, contratto, competenze e RAL stimata (se utilizzabile)."""
    out: Dict[str, Dict[str, Any]] = {}
    by_doc: Dict[int, Dict[str, Any]] = {}
    for r in _rows(owner, ["tax_code", "ccnl", "level", "period", "gross_monthly_eur", "mensilita", "ral_annual_eur"]):
        by_doc.setdefault(r["doc_id"], {"doc_id": r["doc_id"], "filename": r["filename"]})[r["field_key"]] = r["value"]
    for did in sorted(by_doc):
        d = by_doc[did]
        if "tax_code" in d:
            out[d["tax_code"]] = d                                  # l'ultima (id più alto) sovrascrive
    return out


def staff(owner: str) -> Dict[str, Any]:
    """L'organico persona per persona: dal registro del personale (Excel) e dalle buste paga, unite dal token della persona."""
    f = facts(owner)
    slips = _payslips(owner)
    codes = _codes()                                                # le tabelle dei contratti si leggono una volta sola
    people: List[Dict[str, Any]] = []
    used = set()
    for s in f["staff_member"]:
        p = {"token": s["token"], "ref": s.get("ref"), "role": s.get("role"), "level": s.get("level"), "contract": s.get("contract"), "hours_week": s.get("hours_week"),
             "payments": s.get("payments"), "ral_eur": s.get("ral_eur"), "hired": s.get("hired"), "ccnl_text": s.get("ccnl"), "ccnl_code": ccnl_code(s.get("ccnl"), codes),
             "sources": [s["_doc"]]}
        sl = slips.get(s["token"])
        if sl:
            used.add(s["token"])
            p["payslip_document_id"] = sl["doc_id"]
            if sl.get("ral_annual_eur"):
                p["payslip_ral_eur"] = float(sl["ral_annual_eur"])
            if not p["ccnl_code"]:
                p["ccnl_text"] = p["ccnl_text"] or sl.get("ccnl")
                p["ccnl_code"] = ccnl_code(sl.get("ccnl"), codes)
            p["sources"].append({"id": sl["doc_id"], "filename": f"Busta paga (documento {sl['doc_id']})", "where": "busta paga"})          # il nome del file può contenere il nome della persona: non si mostra
        people.append(p)
    for tok, sl in slips.items():                                   # lavoratori che hanno solo la busta paga
        if tok in used:
            continue
        lvl = re.search(r"\b(\d{1,2})\b", sl.get("level", "") or "")
        people.append({"token": tok, "ref": None, "role": None, "level": lvl.group(1) if lvl else (sl.get("level") or None), "contract": None, "hours_week": None,
                       "payments": float(sl["mensilita"]) if sl.get("mensilita") else None, "ral_eur": None, "payslip_ral_eur": float(sl["ral_annual_eur"]) if sl.get("ral_annual_eur") else None,
                       "hired": None, "ccnl_text": sl.get("ccnl"), "ccnl_code": ccnl_code(sl.get("ccnl"), codes), "payslip_document_id": sl["doc_id"],
                       "sources": [{"id": sl["doc_id"], "filename": f"Busta paga (documento {sl['doc_id']})", "where": "busta paga"}]})
    missing: List[str] = []
    if people:
        if any(p["ral_eur"] is None and p.get("payslip_ral_eur") is None for p in people):
            missing.append("La RAL di alcune persone non è nei documenti.")
        if any(not p["ccnl_code"] for p in people):
            missing.append("Per alcune persone il contratto collettivo non corrisponde a nessuno di quelli presenti in Fonte B.")
    return {"people": people, "hiring_plan": f["hiring_plan"], "missing": missing}


def assets(owner: str) -> Dict[str, Any]:
    f = facts(owner)
    lines, plan = f["asset_line"], f["dep_plan_line"]
    by_class: Dict[str, Dict[str, float]] = {}
    for a in lines:
        c = by_class.setdefault(a["class"] or "Altro", {"cost_eur": 0.0, "net_eur": 0.0, "assets": 0})
        c["cost_eur"] = round(c["cost_eur"] + a["cost_eur"], 2)
        c["net_eur"] = round(c["net_eur"] + a["net_eur"], 2)
        c["assets"] += 1
    dep_by_year: Dict[str, float] = {}
    for p in plan:
        for y, v in p["plan"].items():
            dep_by_year[y] = round(dep_by_year.get(y, 0.0) + (v or 0.0), 2)
    return {"assets": lines, "by_class": by_class, "depreciation_plan": plan, "depreciation_by_year": dep_by_year}


def aids(owner: str) -> List[Dict[str, Any]]:
    return sorted(facts(owner)["aid_received"], key=lambda a: a["granted"])


def overview(owner: str) -> Dict[str, Any]:
    """Cosa ho letto, in una riga per tipo: serve a far vedere all'utente che ogni documento è stato davvero usato."""
    f = facts(owner)
    docs = {k: sorted({d["_doc"]["filename"] for d in v}) for k, v in f.items() if v}
    return {"counts": {k: len(v) for k, v in f.items() if v}, "documents": docs}
