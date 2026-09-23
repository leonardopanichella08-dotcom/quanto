"""Documenti del cliente (Fonte C): caricamento, lettura, verifica dei campi incerti, uso nei calcoli.

Flusso: file → controlli (PDF, peso) → cifratura a riposo → lettura (testo del PDF o OCR) → campi con confidenza →
i campi sotto soglia restano «da verificare» → una persona li conferma o li corregge → solo allora si usano nel budget.
"""
from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from app.core import crypto_store, events, fonte_b
from app.core.db import connect
from app.core.fonte_c import ocr, parsers

DOC_TYPES = {"PAYSLIP": "Busta paga", "BALANCE_SHEET": "Bilancio", "F24": "Modello F24"}
MAX_BYTES = 15 * 1024 * 1024
USABLE = ("AUTO", "CONFIRMED", "CORRECTED")
COST_CATEGORIES = ("PERSONNEL", "CAPITAL_ASSETS", "CONSULTING", "OVERHEAD", "TRAINING")


class DocumentError(ValueError):
    pass


def _public_doc(r) -> Dict[str, Any]:
    d = {k: r[k] for k in r.keys() if k != "data_enc"}
    d["mean_confidence"] = float(d["mean_confidence"]) if d.get("mean_confidence") is not None else None
    d["type_label"] = DOC_TYPES.get(d["doc_type"])
    return d


def _public_field(r) -> Dict[str, Any]:
    d = dict(r)
    d["confidence"] = float(d["confidence"])
    if d["field_key"] in ("expense_line", "f24_row") and d["value"]:
        d["parsed"] = json.loads(d["value"])
    return d


def upload(doc_type: str, filename: str, data: bytes, owner: str) -> Dict[str, Any]:
    if doc_type not in DOC_TYPES:
        raise DocumentError(f"Tipo di documento sconosciuto: {doc_type}")
    if len(data) > MAX_BYTES:
        raise DocumentError("File troppo grande (massimo 15 MB)")
    if not data.startswith(b"%PDF"):
        raise DocumentError("Per ora si leggono solo i PDF (anche scansionati)")
    enc = crypto_store.encrypt(data, aad=hashlib.sha256(data).digest())        # FileKeyError se manca la chiave: nulla viene salvato
    error: Optional[str] = None
    read = None
    fields: List[parsers.Field] = []
    try:
        read = ocr.read_pdf(data)
        fields = parsers.PARSERS[doc_type](ocr.group_lines(read.words))
        if not fields:
            error = "Non ho riconosciuto nessun campo: il documento non sembra del tipo indicato o il testo non è leggibile"
    except ocr.OcrUnavailable as exc:
        error = str(exc)
    except ValueError as exc:
        error = str(exc)
    except Exception as exc:  # PDF corrotto o protetto
        error = f"Il PDF non si legge ({type(exc).__name__})"
    status = "FAILED" if error else ("NEEDS_REVIEW" if any(f.status == "NEEDS_REVIEW" for f in fields) else "PARSED")
    with connect() as conn:
        did = conn.execute(
            "INSERT INTO client_documents (doc_type, filename, content_type, size_bytes, sha256, data_enc, status, method, pages, mean_confidence, error, owner, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?) RETURNING id",
            (doc_type, filename[:200], "application/pdf", len(data), hashlib.sha256(data).hexdigest(), enc, status, read.method if read else None,
             read.pages if read else None, round(read.mean_confidence, 4) if read else None, error, owner, events.now_iso())).fetchone()["id"]
        conn.executemany(
            "INSERT INTO client_document_fields (document_id, field_key, value, confidence, status, pii, page, snippet) VALUES (?,?,?,?,?,?,?,?)",
            [(did, f.key, f.value, f.conf, f.status, f.pii, f.page, f.snippet) for f in fields])
    events.record("fonte_c.upload", f"{DOC_TYPES[doc_type]} «{filename[:60]}»: {status}, {len(fields)} campi" + (f" — {error}" if error else ""),
                  status="WARN" if error else "OK", actor=owner, details={"document_id": did, "method": read.method if read else None})
    return get(did)


def list_documents(owner: Optional[str] = None) -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM client_documents " + ("WHERE owner=? " if owner else "") + "ORDER BY id DESC", (owner,) if owner else None).fetchall()
        out = []
        for r in rows:
            d = _public_doc(r)
            c = conn.execute("SELECT COUNT(*) n, COALESCE(SUM((status='NEEDS_REVIEW')::int),0) rev FROM client_document_fields WHERE document_id=?", (r["id"],)).fetchone()
            d["fields"], d["to_review"] = c["n"], int(c["rev"])
            out.append(d)
    return out


def get(document_id: int, owner: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with connect() as conn:
        r = conn.execute("SELECT * FROM client_documents WHERE id=?", (document_id,)).fetchone()
        if r is None or (owner and r["owner"] != owner):
            return None
        fields = [_public_field(x) for x in conn.execute("SELECT * FROM client_document_fields WHERE document_id=? ORDER BY id", (document_id,)).fetchall()]
    d = _public_doc(r)
    d["fields"] = fields
    d["confidence_min"] = parsers.confidence_min()
    d["to_review"] = sum(1 for f in fields if f["status"] == "NEEDS_REVIEW")
    return d


def original(document_id: int, owner: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with connect() as conn:
        r = conn.execute("SELECT * FROM client_documents WHERE id=?", (document_id,)).fetchone()
    if r is None or (owner and r["owner"] != owner):
        return None
    return {"name": r["filename"], "data": crypto_store.decrypt(r["data_enc"], aad=bytes.fromhex(r["sha256"]))}


def delete(document_id: int, owner: Optional[str] = None) -> bool:
    with connect() as conn:
        r = conn.execute("SELECT owner FROM client_documents WHERE id=?", (document_id,)).fetchone()
        if r is None or (owner and r["owner"] != owner):
            return False
        conn.execute("DELETE FROM client_documents WHERE id=?", (document_id,))
    return True


# ------------------------------------------------------------------------------------------------ verifica dei campi
def _validate_correction(key: str, value: str) -> str:
    value = (value or "").strip()
    if not value:
        raise DocumentError("Valore vuoto")
    if key.endswith("_eur"):
        try:
            return str(Decimal(value.replace(".", "").replace(",", ".") if "," in value else value).quantize(Decimal("0.01")))
        except InvalidOperation:
            raise DocumentError("Importo non valido") from None
    if key in ("mensilita",):
        if not re.fullmatch(r"\d{1,2}", value):
            raise DocumentError("Numero di mensilità non valido")
        return value
    if key == "period":
        m = re.fullmatch(r"(\d{1,2})/(20\d{2})", value)
        if not m or not 1 <= int(m.group(1)) <= 12:
            raise DocumentError("Periodo non valido (MM/AAAA)")
        return f"{int(m.group(1)):02d}/{m.group(2)}"
    if key == "fiscal_year":
        if not re.fullmatch(r"20\d{2}", value):
            raise DocumentError("Anno non valido")
        return value
    if key == "expense_line":
        try:
            j = json.loads(value)
            amount = Decimal(str(j["amount_eur"]))
        except (ValueError, KeyError, InvalidOperation):
            raise DocumentError("Riga di costo non valida") from None
        if j.get("category") not in COST_CATEGORIES + (None,):
            raise DocumentError("Categoria di costo non valida")
        return json.dumps({"description": str(j.get("description", ""))[:200], "amount_eur": str(abs(amount)), "category": j.get("category")}, ensure_ascii=False)
    return value[:200]


def review_field(field_id: int, action: str, value: Optional[str], user: str, owner: Optional[str] = None) -> Dict[str, Any]:
    """CONFIRM = il valore letto è giusto; CORRECT = lo sostituisco con il mio. I dati personali (token) non si correggono."""
    if action not in ("CONFIRM", "CORRECT"):
        raise DocumentError("Azione sconosciuta")
    with connect() as conn:
        f = conn.execute("SELECT f.*, d.owner FROM client_document_fields f JOIN client_documents d ON d.id=f.document_id WHERE f.id=?", (field_id,)).fetchone()
        if f is None or (owner and f["owner"] != owner):
            raise KeyError(field_id)
        if action == "CORRECT":
            if f["pii"]:
                raise DocumentError("I dati personali non si correggono: sono conservati solo come token")
            new = _validate_correction(f["field_key"], value or "")
            conn.execute("UPDATE client_document_fields SET value=?, status='CORRECTED', reviewed_by=?, reviewed_at=?, confidence=1 WHERE id=?", (new, user, events.now_iso(), field_id))
        else:
            if f["field_key"] == "expense_line" and not json.loads(f["value"]).get("category"):
                raise DocumentError("Assegna una categoria di costo (usa «correggi»): una riga senza categoria non si può confermare")
            conn.execute("UPDATE client_document_fields SET status='CONFIRMED', reviewed_by=?, reviewed_at=?, confidence=1 WHERE id=?", (user, events.now_iso(), field_id))
        left = conn.execute("SELECT COUNT(*) n FROM client_document_fields WHERE document_id=? AND status='NEEDS_REVIEW'", (f["document_id"],)).fetchone()["n"]
        conn.execute("UPDATE client_documents SET status=? WHERE id=? AND status<>'FAILED'", ("NEEDS_REVIEW" if left else "CONFIRMED", f["document_id"]))
    events.record("fonte_c.review", f"Campo {f['field_key']} del documento {f['document_id']}: {action}", actor=user, details={"field_id": field_id})
    return get(f["document_id"])


# ------------------------------------------------------------------------------------------------ uso nei calcoli
def _usable(doc: Dict[str, Any], key: str) -> Optional[Dict[str, Any]]:
    for f in doc["fields"]:
        if f["field_key"] == key and f["status"] in USABLE:
            return f
    return None


def payslip_cost_line(document_id: int, owner: Optional[str] = None) -> Dict[str, Any]:
    """Voce di personale precompilata dai campi UTILIZZABILI di una busta paga. I campi in verifica non si usano: si elencano."""
    doc = get(document_id, owner)
    if doc is None or doc["doc_type"] != "PAYSLIP":
        raise KeyError(document_id)
    if doc["status"] == "FAILED":
        raise DocumentError(doc["error"] or "Documento non leggibile")
    line: Dict[str, Any] = {"category": "PERSONNEL", "source_c_ref": f"DOC-FC-{document_id}", "description": f"Personale da busta paga (documento {document_id})"}
    missing: List[str] = []
    tok = _usable(doc, "tax_code")
    if tok:
        line["employee_token"] = tok["value"]
    ral = _usable(doc, "ral_annual_eur")
    if ral:
        line["payslip_ral_eur"] = float(ral["value"])
    else:
        missing.append("ral_annual_eur")
    lvl = _usable(doc, "level")
    if lvl and (m := re.search(r"\b(\d{1,2})\b", lvl["value"])):
        line["employee_level"] = m.group(1)
    ccnl = _usable(doc, "ccnl")
    if ccnl:
        codes = fonte_b.load().ccnl_codes()
        n = parsers.norm(ccnl["value"]).replace(" ", "_")
        hits = [c for c in codes if c in n or c.replace("_", " ") in parsers.norm(ccnl["value"])]
        if len(hits) == 1:
            line["ccnl_code"] = hits[0]
    pending = [f["field_key"] for f in doc["fields"] if f["status"] == "NEEDS_REVIEW"]
    return {"document_id": document_id, "cost_item": line, "missing": missing, "needs_review": pending,
            "note": "Compila a mano RAL dichiarata, quota FTE e durata: la busta paga non li contiene."}


def balance_expenses(document_id: int, owner: Optional[str] = None) -> Dict[str, Any]:
    """Spese storiche di un bilancio, pronte per l'allocazione annuale: solo righe utilizzabili e con categoria."""
    doc = get(document_id, owner)
    if doc is None or doc["doc_type"] != "BALANCE_SHEET":
        raise KeyError(document_id)
    lines, unassigned, review = [], [], []
    for f in doc["fields"]:
        if f["field_key"] != "expense_line":
            continue
        p = f["parsed"]
        if f["status"] == "NEEDS_REVIEW":
            review.append({"field_id": f["id"], **p})
        elif not p.get("category"):
            unassigned.append({"field_id": f["id"], **p})
        else:
            lines.append({"field_id": f["id"], **p})
    year = _usable(doc, "fiscal_year")
    return {"document_id": document_id, "fiscal_year": int(year["value"]) if year else None, "lines": lines, "needs_category": unassigned, "needs_review": review}
