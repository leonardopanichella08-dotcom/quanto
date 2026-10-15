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
from datetime import date
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


_ALL_DOCS = {"rna_visura", "rna_aid", "quote", "tax_return", "rd_credit", "durc", "bank_balance", "de_minimis_declared"}        # più documenti dello stesso tipo valgono tutti (una visura per impresa, un preventivo per fornitore…)


def facts(owner: str) -> Dict[str, List[Dict[str, Any]]]:
    """Fatti letti dai documenti, per tipo. Per i fatti di un anno (bilancio di verifica, fatture, budget, investimenti) vale, per ogni anno, l'ultimo documento caricato; per gli altri l'ultimo documento
    che li contiene (si aggiorna un registro sostituendolo, non si sommano due copie); per quelli di cui servono tutti i documenti (visure, preventivi, dichiarazioni) valgono tutti."""
    out: Dict[str, List[Dict[str, Any]]] = {k: [] for k in FACT_KEYS}
    rows = _rows(owner, list(FACT_KEYS))
    parsed = [(r, json.loads(r["value"])) for r in rows]
    latest: Dict[Any, int] = {}
    for r, d in parsed:
        if r["field_key"] in _ALL_DOCS:
            continue
        k = (r["field_key"], d.get("year")) if "year" in d else (r["field_key"], None)
        latest[k] = max(latest.get(k, 0), r["doc_id"])
    for r, d in parsed:
        key = r["field_key"]
        if key not in _ALL_DOCS:
            k = (key, d.get("year")) if "year" in d else (key, None)
            if r["doc_id"] != latest[k]:
                continue
        d["_doc"] = {"id": r["doc_id"], "filename": r["filename"], "where": r["snippet"]}
        out[key].append(d)
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


# ------------------------------------------------------------------------------------------------ gli altri documenti
def rna_visure(owner: str) -> List[Dict[str, Any]]:
    """Le visure aiuti del registro nazionale caricate: una per impresa, con le sue concessioni."""
    f = facts(owner)
    by_doc: Dict[int, Dict[str, Any]] = {}
    for v in f["rna_visura"]:
        by_doc[v["_doc"]["id"]] = {"cf": v["cf"], "denomination": v.get("denomination"), "checked_at": v["checked_at"], "document": v["_doc"], "entries": []}
    for a in f["rna_aid"]:
        if a["_doc"]["id"] in by_doc:
            by_doc[a["_doc"]["id"]]["entries"].append({k: a[k] for k in ("granted", "measure", "regime", "amount_eur", "cor")})
    return sorted(by_doc.values(), key=lambda x: x["checked_at"])


def quotes(owner: str) -> List[Dict[str, Any]]:
    """I preventivi dei fornitori caricati (validi, cioè con data di validità non passata, per primi)."""
    out = sorted(facts(owner)["quote"], key=lambda q: q.get("date") or "", reverse=True)
    today = date.today().isoformat()
    for q in out:
        q["expired"] = bool(q.get("valid_until") and q["valid_until"] < today)
    return out


def shareholders(owner: str) -> List[Dict[str, Any]]:
    return facts(owner)["shareholder"]


def _vat_digits(v: Any) -> str:
    return "".join(ch for ch in str(v or "") if ch.isdigit())[-11:]


def consistency(owner: str) -> List[Dict[str, Any]]:
    """Controlli di coerenza tra i documenti: servono a vedere subito se due carte dicono cose diverse."""
    from app.core import company_profile as cp
    f = facts(owner)
    fin = cp._load_financials(owner)
    out: List[Dict[str, Any]] = []

    def add(key: str, label: str, status: str, detail: str) -> None:
        out.append({"key": key, "label": label, "status": status, "detail": detail})

    def it(x: float) -> str:
        return f"{x:,.0f}".replace(",", ".") + " €"

    for t in f["tax_return"]:
        if t["kind"] == "IVA" and t.get("tax_year") in fin and fin[t["tax_year"]][0].get("revenue_eur"):
            rev = float(fin[t["tax_year"]][0]["revenue_eur"])
            gap = abs(t["turnover_eur"] - rev) / rev * 100
            add("iva_vs_ricavi", f"Volume d'affari IVA {t['tax_year']} e ricavi del bilancio", "OK" if gap <= 5 else "WARN",
                f"Volume d'affari {it(t['turnover_eur'])}, ricavi del bilancio {it(rev)}: differenza {gap:.1f}%".replace(".", ",") + ("." if gap <= 5 else ": vanno spiegate (anno d'imposta, operazioni fuori campo, reverse charge)."))
    for x in f["xbrl_balance"]:
        if x["year"] in fin and fin[x["year"]][0].get("revenue_eur") and x.get("revenue_eur"):
            rev = float(fin[x["year"]][0]["revenue_eur"])
            gap = abs(x["revenue_eur"] - rev) / rev * 100
            add("xbrl_vs_bilancio", f"Bilancio XBRL {x['year']} e bilancio PDF", "OK" if gap < 1 else "WARN", f"Ricavi XBRL {it(x['revenue_eur'])}, ricavi del PDF {it(rev)}: differenza {gap:.1f}%".replace(".", ","))
    sh = f["shareholder"]
    if sh:
        tot = sum(x["percent"] for x in sh)
        add("soci", "Libro soci", "OK" if tot == 100 else "WARN", f"Le quote dei soci sommano il {tot}%" + ("." if tot == 100 else ": non tornano al 100%."))
        firms = [x for x in sh if x["kind"] == "impresa"]
        if firms:
            add("soci_societa", "Soci che sono società", "WARN", f"{len(firms)} soci sono società ({', '.join(x['name'] for x in firms)}): per l'impresa unica serve verificare il legame e la visura aiuti di ciascuna.")
    durc = sorted(f["durc"], key=lambda d: d.get("issued") or "")
    if durc:
        last = durc[-1]
        left = (date.fromisoformat(last["expires"]) - date.today()).days
        if last["outcome"] != "regolare":
            add("durc", "DURC", "WARN", f"L'ultimo DURC ({last.get('issued')}) non è regolare.")
        elif left < 0:
            add("durc", "DURC", "WARN", f"Il DURC è scaduto il {last['expires']}: per un bando serve uno in corso di validità.")
        elif left <= 30:
            add("durc", "DURC", "WARN", f"Il DURC scade tra {left} giorni ({last['expires']}): rinnovalo prima di presentare una domanda.")
        else:
            add("durc", "DURC", "OK", f"Regolare, valido fino al {last['expires']} ({left} giorni).")
    vis = rna_visure(owner)
    if vis:
        old = (date.today() - date.fromisoformat(vis[-1]["checked_at"])).days
        add("visura_rna", "Visura aiuti dell'RNA", "OK" if old <= 30 else "WARN", f"Ultima visura caricata del {vis[-1]['checked_at']} ({old} giorni fa)" + ("." if old <= 30 else ": rifalla prima di usare il de minimis."))
    for q in f["quote"]:
        if q.get("valid_until") and q["valid_until"] < date.today().isoformat():
            add("preventivo_scaduto", f"Preventivo {q.get('number') or ''}", "WARN", f"Il preventivo di {q['supplier']} è scaduto il {q['valid_until']}: chiedine uno nuovo.")
    bank = sorted(f["bank_balance"], key=lambda b: b["on"])
    if bank:
        add("liquidita", "Liquidità sul conto", "INFO", f"Saldo del conto al {bank[-1]['on']}: {it(bank[-1]['balance_eur'])} (serve per il controllo della liquidità del bando).")
    return out
