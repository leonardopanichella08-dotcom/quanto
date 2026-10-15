"""Fatture elettroniche (FatturaPA, XML) e bilanci in formato XBRL: dati strutturati, niente lettura ottica.

- **Fatture**: ogni file XML (o un archivio ZIP di file XML, come lo scarica il gestionale o il cassetto fiscale) è una fattura. Si sommano le righe per anno e per voce di spesa, con lo stesso criterio
  dei bilanci e dei fogli Excel (``supplier_spend``). Una nota di credito (TD04, TD08) sottrae. Non si conserva il nome del fornitore: servono solo le somme.
- **Bilancio XBRL** (il formato in cui un bilancio si deposita al Registro delle Imprese): si leggono i totali del conto economico (ricavi, costi della produzione, personale, utile). Un bilancio XBRL non
  divide i servizi tra consulenze, affitti e utenze: quel dettaglio sta nella nota integrativa o nel bilancio di verifica del gestionale; i totali, qui, arrivano senza OCR.
  I nomi degli elementi si riconoscono dalle parole del loro nome (tassonomia italiana «itcc-ci»): se un elemento non si riconosce non si legge, non si indovina. Il lettore è provato su file
  costruiti seguendo quei nomi, non ancora su un bilancio depositato vero.

Sicurezza: un file con una DOCTYPE (definizioni di entità) si rifiuta; dimensione e numero dei file sono limitati.
"""
from __future__ import annotations

import io
import re
import zipfile
from typing import Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

from app.core.fonte_c import parsers, sheets

Field = parsers.Field
MAX_FILES = 6000
MAX_XML_BYTES = 2_000_000
MAX_UNCOMPRESSED = 200_000_000
CREDIT_NOTES = {"TD04", "TD08"}


def _safe_root(data: bytes) -> Optional[ET.Element]:
    head = data[:8192].upper()
    if len(data) > MAX_XML_BYTES or b"<!DOCTYPE" in head or b"<!ENTITY" in head:
        return None
    try:
        return ET.fromstring(data)
    except ET.ParseError:
        return None


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _find_all(el: ET.Element, name: str) -> List[ET.Element]:
    return [e for e in el.iter() if _local(e.tag) == name]


def _first(el: ET.Element, name: str) -> str:
    for e in el.iter():
        if _local(e.tag) == name and (e.text or "").strip():
            return e.text.strip()
    return ""


def _num(v: str) -> Optional[float]:
    try:
        return float(v.replace(",", "."))
    except ValueError:
        return None


def is_invoice(root: ET.Element) -> bool:
    return _local(root.tag).lower().startswith("fatturaelettronica")


def read_invoices(files: List[Tuple[str, bytes]]) -> Tuple[str, List[Field], List[str]]:
    agg: Dict[Tuple[int, Optional[str], Optional[str]], List[float]] = {}
    n_ok = 0
    for _name, data in files[:MAX_FILES]:
        root = _safe_root(data)
        if root is None or not is_invoice(root):
            continue
        when = sheets._date(_first(root, "Data"))                                    # DatiGeneraliDocumento/Data
        if not when:
            continue
        year = int(when[:4])
        sign = -1.0 if _first(root, "TipoDocumento") in CREDIT_NOTES else 1.0
        n_ok += 1
        for line in _find_all(root, "DettaglioLinee"):
            desc = _first(line, "Descrizione")
            amount = _num(_first(line, "PrezzoTotale"))
            if amount is None:
                continue
            cat, typ = sheets._cost_class(desc)
            a = agg.setdefault((year, typ, cat), [0.0, 0])
            a[0] += sign * amount
            a[1] += 1
    fields = [sheets._fact("supplier_spend", {"year": y, "expense_type": t, "category": c, "amount_eur": round(a[0], 2), "invoices": a[1]}, 1, f"{n_ok} fatture elettroniche, {a[1]} righe")
              for (y, t, c), a in sorted(agg.items(), key=lambda kv: (kv[0][0], -kv[1][0]))]
    return (f"Fatture elettroniche lette: {n_ok}" if fields else ""), fields, ([f"{n_ok} fatture"] if fields else [])


def read_zip(data: bytes) -> Tuple[str, List[Field], List[str]]:
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        return "", [], []
    infos = [i for i in z.infolist() if i.filename.lower().endswith(".xml") and i.file_size <= MAX_XML_BYTES][:MAX_FILES]
    if sum(i.file_size for i in infos) > MAX_UNCOMPRESSED:                              # un archivio che si espande oltre ogni misura non è un elenco di fatture
        return "", [], []
    return read_invoices([(i.filename, z.read(i)) for i in infos])


# ------------------------------------------------------------------------------------------------ XBRL
_PATTERNS: List[Tuple[str, List[str]]] = [          # chiave, [parole che l'elemento deve contenere]
    ("revenue_eur", ["RICAVI", "VENDITE", "PRESTAZIONI"]),
    ("total_costs_eur", ["TOTALE", "COSTI", "PRODUZIONE"]),
    ("personnel_eur", ["TOTALE", "COSTI", "PERSONALE"]),
    ("net_result_eur", ["UTILE", "ESERCIZIO"]),
]


def read_xbrl(data: bytes) -> Tuple[str, List[Field], List[str]]:
    root = _safe_root(data)
    if root is None or "xbrl" not in _local(root.tag).lower():
        return "", [], []
    periods: Dict[str, int] = {}
    for ctx in _find_all(root, "context"):
        end = _first(ctx, "endDate") or _first(ctx, "instant")
        if end[:4].isdigit() and not _find_all(ctx, "explicitMember"):                  # solo il contesto «generale» dell'esercizio, senza dimensioni
            periods[ctx.attrib.get("id", "")] = int(end[:4])
    by_year: Dict[int, Dict[str, Any]] = {}
    for el in root.iter():
        ref = el.attrib.get("contextRef")
        if ref not in periods or not (el.text or "").strip():
            continue
        v = _num(el.text.strip())
        if v is None:
            continue
        name = re.sub(r"[^A-Z]", "", _local(el.tag).upper())
        for key, words in _PATTERNS:
            if all(w in name for w in words):
                cur = by_year.setdefault(periods[ref], {})
                if key not in cur or len(name) < cur.get("_len_" + key, 10 ** 6):           # il nome più corto è il totale, non una sua voce
                    cur[key], cur["_len_" + key] = v, len(name)
    fields = []
    for y, vals in sorted(by_year.items()):
        payload = {"year": y, **{k: round(v, 2) for k, v in vals.items() if not k.startswith("_")}}
        if len(payload) > 2:
            fields.append(sheets._fact("xbrl_balance", payload, 1, f"bilancio XBRL {y}"))
    return (f"Bilancio XBRL letto: esercizi {', '.join(str(f.page) for f in fields)}" if fields else ""), fields, ([str(y) for y in sorted(by_year)] if fields else [])
