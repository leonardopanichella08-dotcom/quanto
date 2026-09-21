"""Estrazione dei campi dai documenti contabili del cliente (Modulo 9.3): buste paga, bilanci, modelli F24.

Ogni campo estratto ha una confidenza (0-1) = certezza del riconoscimento × confidenza di lettura delle parole:
- 0,98 etichetta e valore sulla stessa riga, valore del tipo atteso;
- 0,90 valore sulla riga sotto l'etichetta;
- 0,55 la stessa etichetta compare con valori diversi (ambiguo: lo decide una persona).
I campi sotto la soglia (``CONFIDENCE_MIN``) vanno in verifica: non entrano nei calcoli finché non vengono confermati o
corretti (fail-safe del Modulo 15.3). I dati personali diventano token opachi già qui: il valore vero non esce da questo modulo.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Callable, Dict, List, Optional

from app.core.anonymizer import PrivacyAnonymizer

DEFAULT_CONFIDENCE_MIN = 0.90


def confidence_min() -> float:
    try:
        return float(os.getenv("QUANTO_FIELD_CONFIDENCE_MIN", DEFAULT_CONFIDENCE_MIN))
    except ValueError:
        return DEFAULT_CONFIDENCE_MIN


@dataclass
class Field:
    key: str
    value: str
    conf: float
    page: int = 1
    snippet: str = ""
    pii: bool = False
    derived: bool = False

    @property
    def status(self) -> str:
        return "AUTO" if self.conf >= confidence_min() else "NEEDS_REVIEW"


_CF = re.compile(r"\b[A-Z]{6}\d{2}[A-EHLMPR-T]\d{2}[A-Z]\d{3}[A-Z]\b")
_AMOUNT = re.compile(r"(?<![\w.,])-?\d{1,3}(?:\.\d{3})*,\d{2}(?![\d])|(?<![\w.,])-?\d+,\d{2}(?![\d])")
_IBAN = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")


def norm(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t).strip().upper()


def parse_amount(text: str) -> Optional[Decimal]:
    m = _AMOUNT.search(text or "")
    if not m:
        return None
    try:
        return Decimal(m.group(0).replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


def _scrub(text: str) -> str:
    """Riga d'origine da conservare come prova, senza codici fiscali né IBAN."""
    return PrivacyAnonymizer.scrub_free_text(text)[:200]


# ------------------------------------------------------------------------------------------------ etichette → valore
def _find(lines: List[dict], labels: List[str], kind: str, key: str, pii: bool = False) -> Optional[Field]:
    """Cerca la prima etichetta nota e ne legge il valore sulla stessa riga o sulla successiva."""
    found: List[Field] = []
    for i, ln in enumerate(lines):
        n = norm(ln["text"])
        for lab in labels:
            pos = n.find(lab)
            if pos < 0:
                continue
            same = ln["text"] if pos == 0 else ln["text"]
            after_norm = n[pos + len(lab):]
            value, certainty = _value(kind, after_norm, ln["text"], lab)
            conf_line = ln["conf_min"]
            if value is None and i + 1 < len(lines) and lines[i + 1]["page"] == ln["page"]:
                value, _ = _value(kind, norm(lines[i + 1]["text"]), lines[i + 1]["text"], "")
                certainty = 0.90
                conf_line = min(conf_line, lines[i + 1]["conf_min"])
            if value is not None:
                found.append(Field(key, value, round(certainty * conf_line, 4), ln["page"],
                                    (f"{lab.title()}: [dato personale sostituito da token]" if pii and kind != "cf" else _scrub(ln["text"])), pii))
            break
    if not found:
        return None
    values = {f.value for f in found}
    best = found[0]
    if len(values) > 1:                                   # stessa etichetta, valori diversi: ambiguo
        best.conf = min(best.conf, 0.55)
        best.snippet = (best.snippet + " | valori diversi nel documento")[:200]
    return best


def _value(kind: str, after_norm: str, raw_line: str, label: str):
    if kind == "amount":
        a = parse_amount(after_norm) if after_norm.strip() else None
        return (str(a), 0.98) if a is not None else (None, 0)
    if kind == "int":
        m = re.search(r"\b(\d{1,2})\b", after_norm)
        return (m.group(1), 0.98) if m else (None, 0)
    if kind == "cf":
        m = _CF.search(raw_line.upper())
        return (m.group(0), 0.98) if m else (None, 0)
    if kind == "period":
        m = re.search(r"\b(0?[1-9]|1[0-2])\s*[/\-]\s*(20\d{2})\b", after_norm)
        return (f"{int(m.group(1)):02d}/{m.group(2)}", 0.98) if m else (None, 0)
    if kind in ("text", "short"):
        v = re.sub(r"^[\s:.\-]+", "", after_norm).strip()
        return (v, 0.98) if len(v) >= (1 if kind == "short" else 2) else (None, 0)
    return (None, 0)


def _tokenize(f: Optional[Field]) -> Optional[Field]:
    if f is not None and f.pii:
        f.value = PrivacyAnonymizer.generate_opaque_token(f.value)
    return f


# ------------------------------------------------------------------------------------------------ busta paga
PAYSLIP_SPECS = [
    ("employee_name", ["COGNOME E NOME", "COGNOME NOME", "NOMINATIVO", "DIPENDENTE"], "text", True),
    ("tax_code", ["CODICE FISCALE", "COD. FISC", "C.F."], "cf", True),
    ("ccnl", ["CCNL", "CONTRATTO COLLETTIVO", "CONTRATTO"], "text", False),
    ("level", ["LIVELLO", "INQUADRAMENTO", "QUALIFICA"], "short", False),
    ("period", ["PERIODO DI RETRIBUZIONE", "PERIODO", "MESE DI RIFERIMENTO"], "period", False),
    ("gross_monthly_eur", ["TOTALE COMPETENZE", "TOTALE LORDO", "RETRIBUZIONE LORDA"], "amount", False),
    ("net_monthly_eur", ["NETTO IN BUSTA", "NETTO DEL MESE", "NETTO A PAGARE"], "amount", False),
    ("tfr_accrual_eur", ["QUOTA TFR", "TFR DEL MESE", "TFR MATURATO"], "amount", False),
    ("mensilita", ["MENSILITA", "N. MENSILITA", "NUMERO MENSILITA"], "int", False),
]


def parse_payslip(lines: List[dict]) -> List[Field]:
    out: List[Field] = []
    for key, labels, kind, pii in PAYSLIP_SPECS:
        f = _find(lines, labels, kind, key, pii)
        if f is None and kind == "cf":                    # il codice fiscale si riconosce anche senza etichetta
            for ln in lines:
                m = _CF.search(ln["text"].upper())
                if m:
                    f = Field(key, m.group(0), round(0.85 * ln["conf_min"], 4), ln["page"], _scrub(ln["text"]), True)
                    break
        if f is not None:
            out.append(_tokenize(f))
    by = {f.key: f for f in out}
    g, m = by.get("gross_monthly_eur"), by.get("mensilita")
    if g and m:                                           # la RAL non è sul cedolino: è una stima, e come tale va confermata da una persona
        ral = (Decimal(g.value) * int(m.value)).quantize(Decimal("0.01"))
        out.append(Field("ral_annual_eur", str(ral), round(min(g.conf, m.conf) * 0.80, 4), g.page,
                         f"stima: totale competenze mensili × {m.value} mensilità (la RAL non è indicata sul cedolino)", derived=True))
    return out


# ------------------------------------------------------------------------------------------------ bilancio
COST_KEYWORDS = {
    "PERSONNEL": ["SALARI", "STIPENDI", "ONERI SOCIALI", "TRATTAMENTO DI FINE RAPPORTO", "TFR", "PERSONALE", "RETRIBUZIONI", "CONTRIBUTI PREVIDENZIALI"],
    "CAPITAL_ASSETS": ["AMMORTAMENT", "IMMOBILIZZAZIONI", "MACCHINARI", "ATTREZZATURE", "IMPIANTI", "HARDWARE", "SOFTWARE", "AUTOMEZZI", "ARREDI"],
    "CONSULTING": ["CONSULENZ", "PRESTAZIONI PROFESSIONALI", "COMPENSI A PROFESSIONISTI", "SERVIZI PROFESSIONALI", "COMPENSI PROFESSIONALI"],
    "TRAINING": ["FORMAZIONE", "CORSI DI", "AGGIORNAMENTO PROFESSIONALE"],
    "OVERHEAD": ["AFFITT", "LOCAZION", "UTENZE", "ENERGIA ELETTRICA", "TELEFON", "ASSICURAZION", "SPESE GENERALI", "CANCELLERIA", "MANUTENZION", "PULIZI",
                 "SPESE DI RAPPRESENTANZA", "SPESE POSTALI", "SPESE BANCARIE", "PUBBLICITA"],
}
_ACCOUNT_CODE = re.compile(r"^\s*(?:[A-Z]\)|[A-Z]\.\d+|\d+[.\-]\d+(?:[.\-]\d+)*|\d{2,})\s+")


def classify_cost(description: str) -> (Optional[str], float):
    n = norm(description)
    hits = {cat for cat, kws in COST_KEYWORDS.items() if any(k in n for k in kws)}
    if len(hits) == 1:
        return next(iter(hits)), 0.95
    if len(hits) > 1:
        return None, 0.0                                   # riga ambigua: la assegna una persona
    return None, 0.0


def parse_balance(lines: List[dict]) -> List[Field]:
    """Righe di costo del bilancio: descrizione + importo. Il fiscal year e i totali vengono letti a parte."""
    out: List[Field] = []
    year = None
    in_costs: Optional[bool] = None
    for ln in lines:
        n = norm(ln["text"])
        if year is None:
            m = re.search(r"\b(?:ESERCIZIO|BILANCIO)\D{0,20}(20\d{2})\b", n)
            if m:
                year = Field("fiscal_year", m.group(1), round(0.98 * ln["conf_min"], 4), ln["page"], _scrub(ln["text"]))
                out.append(year)
        if re.search(r"COSTI DELLA PRODUZIONE|B\)\s*COSTI", n):
            in_costs = True
            continue
        if re.search(r"^C\)|PROVENTI E ONERI FINANZIARI|VALORE DELLA PRODUZIONE", n) and in_costs:
            in_costs = False
        amt = parse_amount(ln["text"])
        if amt is None or in_costs is False:
            continue
        desc = _AMOUNT.sub("", ln["text"])
        desc = _ACCOUNT_CODE.sub("", desc).strip(" .:-")
        if len(desc) < 4 or re.search(r"\bTOTALE\b", norm(desc)):
            continue
        cat, cat_conf = classify_cost(desc)
        pattern = 0.98 if in_costs else 0.80               # fuori da una sezione «Costi della produzione» la riga potrebbe non essere un costo
        conf = round(pattern * (cat_conf if cat else 0.0) * ln["conf_min"], 4)
        out.append(Field("expense_line", json.dumps({"description": desc, "amount_eur": str(abs(amt)), "category": cat}, ensure_ascii=False), conf, ln["page"], _scrub(ln["text"])))
    return out


# ------------------------------------------------------------------------------------------------ F24
_F24_ROW = re.compile(r"\b(\d{4})\b\s+(?:(?!\d{4}\s)[A-Z0-9/\-]{1,12}\s+)?(?:(\d{4})\s+)?(\d{1,3}(?:\.\d{3})*,\d{2})")


def parse_f24(lines: List[dict]) -> List[Field]:
    out: List[Field] = []
    for ln in lines:
        text = ln["text"]
        m = _F24_ROW.search(text)
        if not m:
            continue
        code, year, amount = m.group(1), m.group(2), m.group(3)
        if not (1000 <= int(code) <= 9999):
            continue
        strict = bool(year and 2000 <= int(year) <= 2100)
        row = {"codice_tributo": code, "anno": year if strict else None, "importo_debito_eur": str(parse_amount(amount))}
        out.append(Field("f24_row", json.dumps(row), round((0.96 if strict else 0.70) * ln["conf_min"], 4), ln["page"], _scrub(text)))
    return out


PARSERS: Dict[str, Callable[[List[dict]], List[Field]]] = {"PAYSLIP": parse_payslip, "BALANCE_SHEET": parse_balance, "F24": parse_f24}
