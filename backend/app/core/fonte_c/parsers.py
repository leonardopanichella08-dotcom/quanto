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
    t = unicodedata.normalize("NFKD", (text or "").replace("’", "'")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t.replace("'", "")).strip().upper()          # senza apostrofi: «DELL'ESERCIZIO» e «DELL’ESERCIZIO» sono la stessa etichetta


def parse_amount(text: str) -> Optional[Decimal]:
    m = _AMOUNT.search(text or "")
    if not m:
        return None
    try:
        return Decimal(m.group(0).replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


# Un bilancio redatto in unità di euro non ha i centesimi: «1) ricavi delle vendite e delle prestazioni 1.583.200 1.327.900» (esercizio e confronto).
# Si legge come importo il primo dei numeri che chiudono la riga, mai un anno («2025 2024») né un numero dentro il testo.
_UNITS_TAIL = re.compile(r"(?<![\w.,/])(-?\d{1,3}(?:\.\d{3})+|-?\d{1,3})(?=(?:\s+-?\d{1,3}(?:\.\d{3})*)*\s*$)")


def amount_units(text: str) -> Optional[Decimal]:
    """Importo con i centesimi (come ``parse_amount``) oppure, se la riga finisce con numeri interi, il primo di essi."""
    a = parse_amount(text)
    if a is not None:
        return a
    m = _UNITS_TAIL.search((text or "").rstrip())
    if not m:
        return None
    try:
        return Decimal(m.group(1).replace(".", "")).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def strip_amounts(text: str) -> str:
    """La riga senza gli importi (con o senza centesimi): resta la descrizione."""
    if parse_amount(text) is not None:
        return _AMOUNT.sub("", text)
    return re.sub(r"(?<![\w.,/])(?:-?\d{1,3}(?:\.\d{3})*\s*)+$", "", (text or "").rstrip())


def _scrub(text: str) -> str:
    """Riga d'origine da conservare come prova, senza codici fiscali né IBAN."""
    return PrivacyAnonymizer.scrub_free_text(text)[:200]


# ------------------------------------------------------------------------------------------------ etichette → valore
def _at_line_start(prefix: str) -> bool:
    """Prima dell'etichetta c'è solo un codice di voce («IX -», «21)», «B.10»), non altre parole: l'etichetta apre la riga."""
    p = prefix.strip()
    return len(p) <= 12 and not re.search(r"[A-Z]{4,}", p)


def _find(lines: List[dict], labels: List[str], kind: str, key: str, pii: bool = False) -> Optional[Field]:
    """Cerca l'etichetta e ne legge il valore sulla stessa riga (o, se dopo l'etichetta non c'è altro, sulla successiva).

    Se l'etichetta compare più volte conta la più specifica: prima quella che sta più in alto nell'elenco delle etichette, poi quella che apre la riga
    (non «numero medio annuo di addetti» al posto di «addetti»). Un'etichetta seguita da altre parole («totale competenze progressive 23.846,16») non è il valore cercato.
    Tra le occorrenze equivalenti decide la maggioranza; solo se non c'è un vincitore chiaro la lettura è ambigua e la decide una persona."""
    cands: List[tuple] = []
    for i, ln in enumerate(lines):
        n = norm(ln["text"])
        for rank, lab in enumerate(labels):
            pos = n.find(lab)
            if pos < 0:
                continue
            after_norm = n[pos + len(lab):]
            if kind in ("amount", "amountu") and re.match(r"[\s:\-]*[A-Z]", after_norm):         # «TOTALE COMPETENZE PROGRESSIVE …»: è un'altra voce
                break
            value, certainty = _value(kind, after_norm, ln["text"], lab)
            conf_line = ln["conf_min"]
            if value is None and not re.search(r"[A-Z0-9]", after_norm) and i + 1 < len(lines) and lines[i + 1]["page"] == ln["page"]:
                value, _ = _value(kind, norm(lines[i + 1]["text"]), lines[i + 1]["text"], "")
                certainty = 0.90
                conf_line = min(conf_line, lines[i + 1]["conf_min"])
            if value is not None:
                snippet = f"{lab.title()}: [dato personale sostituito da token]" if pii and kind != "cf" else _scrub(ln["text"])
                cands.append(((rank, 0 if _at_line_start(n[:pos]) else 1), Field(key, value, round(certainty * conf_line, 4), ln["page"], snippet, pii)))
            break
    if not cands:
        return None
    top = min(k for k, _ in cands)
    found = [f for k, f in cands if k == top]
    counts: Dict[str, int] = {}
    for f in found:
        counts[f.value] = counts.get(f.value, 0) + 1
    ranked = sorted(counts.values(), reverse=True)
    best = found[0]
    if len(counts) > 1:
        if ranked[0] > ranked[1]:                          # un valore prevale: è quello che il documento ripete (il totale), le altre sono righe di dettaglio
            best = next(f for f in found if counts[f.value] == ranked[0])
        else:                                              # stessa etichetta, valori diversi e nessun vincitore: ambiguo
            best.conf = min(best.conf, 0.55)
            best.snippet = (best.snippet + " | valori diversi nel documento")[:200]
    return best


def _value(kind: str, after_norm: str, raw_line: str, label: str):
    if kind in ("amount", "amountu"):
        a = (amount_units(after_norm) if kind == "amountu" else parse_amount(after_norm)) if after_norm.strip() else None
        return (str(a), 0.98) if a is not None else (None, 0)
    if kind == "int":
        m = re.search(r"\b(\d{1,2})\b", after_norm)
        return (m.group(1), 0.98) if m else (None, 0)
    if kind == "count":
        for m in re.finditer(r"\b(\d{1,5})(?:[,.]\d+)?\b", after_norm):
            if 1900 <= int(m.group(1)) <= 2100:                      # un anno («2025 2024» nell'intestazione di una tabella) non è un numero di persone
                continue
            return m.group(1), 0.98
        return None, 0
    if kind == "vat":
        m = re.search(r"(?:\bIT\s*)?\b(\d{11})\b", after_norm.replace(" ", ""))
        return (m.group(1), 0.98) if m else (None, 0)
    if kind == "ateco":
        m = re.search(r"\b(\d{2}\.\d{2}(?:\.\d{1,2})?)\b", after_norm)
        return (m.group(1), 0.98) if m else (None, 0)
    if kind == "year":
        m = re.search(r"\b(1[89]\d{2}|20\d{2})\b", after_norm)
        return (m.group(1), 0.98) if m else (None, 0)
    if kind == "province":
        m = re.search(r"\(([A-Z]{2})\)", raw_line.upper())
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
    ("ccnl", ["CCNL APPLICATO", "CCNL", "CONTRATTO COLLETTIVO", "CONTRATTO"], "text", False),
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
    # costi che non rientrano in nessuna delle cinque categorie e che i bandi non rimborsano: imposte indirette, quote associative, liberalità, svalutazioni, carburanti…
    "OTHER": ["IMPOSTE E TASSE", "QUOTE ASSOCIATIV", "SOPRAVVENIENZ", "LIBERALIT", "EROGAZIONI LIBERALI", "SVALUTAZION", "CARBURANT", "MINUSVALENZ", "SANZION", "PERDITE SU CREDITI", "ARROTONDAMENT"],
}
_ACCOUNT_CODE = re.compile(r"^\s*(?:(?:[A-Za-z]|\d{1,2})\)|[A-Z]\.\d+|\d+[.\-]\d+(?:[.\-]\d+)*|\d{2,})\s+")
_NUMBERED = re.compile(r"^\s*\d{1,2}\)\s")                    # voce numerata dello schema civilistico: «7) per servizi», «9) per il personale»
_COSTS_START = re.compile(r"COSTI DELLA PRODUZIONE|B\)\s*COSTI")
_YEAR = re.compile(r"\b(?:ESERCIZIO|BILANCIO)\b[^0-9]{0,30}(?:\d{1,2}\s*[/.\-]\s*\d{1,2}\s*[/.\-]\s*)?(20\d{2})\b")


def classify_cost(description: str) -> (Optional[str], float):
    n = norm(description)
    hits = {cat for cat, kws in COST_KEYWORDS.items() if any(k in n for k in kws)}
    if hits == {"TRAINING", "PERSONNEL"}:
        hits = {"TRAINING"}                                # «formazione del personale»: la parola «personale» è solo il complemento
    if len(hits) == 1:
        return next(iter(hits)), 0.95
    if len(hits) > 1:
        return None, 0.0                                   # riga ambigua: la assegna una persona
    return None, 0.0


_PAGE_MARK = re.compile(r"\bPAGINA\s+\d+\s*(?:DI|/)\s*\d+\b|\bPAG\.?\s*\d+\s*(?:DI|/)\s*\d+\b")


def _total_costs(lines: List[dict]) -> Optional[Decimal]:
    """Il «Totale costi della produzione» dichiarato dal documento (il valore che si ripete di più, esercizio corrente)."""
    counts: Dict[Decimal, int] = {}
    for ln in lines:
        if "TOTALE COSTI DELLA PRODUZIONE" in norm(ln["text"]):
            a = amount_units(ln["text"])
            if a is not None:
                counts[a] = counts.get(a, 0) + 1
    return max(counts, key=counts.get) if counts else None


def _block_sum(block: List["Field"]) -> Decimal:
    return sum((Decimal(json.loads(f.value)["amount_eur"]) for f in block), Decimal(0))


def _parse_balance_costs(lines: List[dict]) -> List[Field]:
    """Righe di costo del bilancio: descrizione + importo. Il fiscal year e i totali vengono letti a parte.

    Un bilancio vero espone i costi più volte: nello schema civilistico (voci 6, 7, 8, 9…) e nell'allegato analitico (conto per conto). Ogni tabella è un blocco;
    si usa un solo blocco, quello la cui somma torna con il «Totale costi della produzione» del documento e che ha più righe (il più dettagliato): così nessun costo si conta due volte."""
    year = None
    def starts_costs(n: str) -> bool:                       # intestazione «B) Costi della produzione», non i totali né la «Differenza tra valore e costi della produzione»
        return bool(_COSTS_START.search(n)) and not re.search(r"\b(?:TOTALE|DIFFERENZA)\b", n)

    has_section = any(starts_costs(norm(ln["text"])) for ln in lines)
    in_costs: Optional[bool] = False if has_section else None       # con la sezione dei costi presente si leggono solo le sue righe (non l'attivo né i ricavi)
    blocks: List[List[Field]] = []
    cur: Optional[List[Field]] = [] if not has_section else None
    agg: Optional[dict] = None                                      # voce numerata in corso: se le sottovoci ne danno la somma, la voce è un sottototale e non va contata due volte

    def close_agg() -> None:
        nonlocal agg
        if agg and agg["n"] and cur is not None and abs(agg["sum"] - agg["amount"]) <= Decimal("1.00"):
            cur.remove(agg["field"])
        agg = None

    def close_block() -> None:
        nonlocal cur
        close_agg()
        if cur is not None:
            blocks.append(cur)
        cur = None

    year_field: Optional[Field] = None
    for ln in lines:
        n = norm(ln["text"])
        if _PAGE_MARK.search(n):                              # piè di pagina o intestazione ripetuta su ogni pagina («Pagina 13 di 14»): non è una riga del bilancio
            continue
        if year is None:
            m = _YEAR.search(n)
            if m:
                year = year_field = Field("fiscal_year", m.group(1), round(0.98 * ln["conf_min"], 4), ln["page"], _scrub(ln["text"]))
        if starts_costs(n):
            close_block()
            cur = []
            in_costs = True
            continue
        # «C) Proventi e oneri finanziari» chiude i costi; «c) trattamento di fine rapporto» è solo la terza sottovoce del personale (la lettera minuscola, normalizzata, è uguale)
        if re.search(r"^C\)\s*(?:PROVENTI|$)|PROVENTI E ONERI FINANZIARI|VALORE DELLA PRODUZIONE|DIFFERENZA TRA|TOTALE COSTI DELLA PRODUZIONE", n) and in_costs:
            close_block()
            in_costs = False
        amt = amount_units(ln["text"])
        if amt is None or in_costs is False:
            if in_costs is not False and _NUMBERED.match(ln["text"]):
                close_agg()
            continue
        desc = strip_amounts(ln["text"])
        numbered = bool(_NUMBERED.match(ln["text"]))
        desc = _ACCOUNT_CODE.sub("", desc).strip(" .:-")
        if len(desc) < 4 or re.search(r"\bTOTALE\b", norm(desc)):
            close_agg()
            continue
        cat, cat_conf = classify_cost(desc)
        if in_costs is None and cat is None:
            continue                                        # senza sezione dei costi riconoscibile: una riga senza categoria di costo non è da verificare
        pattern = 0.98 if in_costs else 0.80               # fuori da una sezione «Costi della produzione» la riga potrebbe non essere un costo
        conf = round(pattern * (cat_conf if cat else 0.0) * ln["conf_min"], 4)
        f = Field("expense_line", json.dumps({"description": desc, "amount_eur": str(abs(amt)), "category": cat}, ensure_ascii=False), conf, ln["page"], _scrub(ln["text"]))
        cur.append(f)
        if numbered:
            close_agg()
            agg = {"field": f, "amount": abs(amt), "sum": Decimal(0), "n": 0}
        elif agg is not None:
            agg["sum"] += abs(amt)
            agg["n"] += 1
    close_block()
    chosen: List[Field] = []
    if blocks:
        total = _total_costs(lines)
        matching = [b for b in blocks if total is not None and abs(_block_sum(b) - total) <= Decimal("1.00")]
        chosen = max(matching or blocks, key=len)
    return ([year_field] if year_field else []) + chosen


# I valori che descrivono l'impresa (non le singole righe di costo): servono a costruire il profilo aziendale.
BALANCE_SPECS = [
    ("revenue_eur", ["RICAVI DELLE VENDITE E DELLE PRESTAZIONI", "RICAVI DELLE VENDITE E PRESTAZIONI", "RICAVI DELLE VENDITE"], "amountu"),
    ("net_result_eur", ["UTILE (PERDITA) DELLESERCIZIO", "UTILE/PERDITA DELLESERCIZIO", "UTILE (PERDITA) DELL ESERCIZIO", "UTILE DELLESERCIZIO", "PERDITA DELLESERCIZIO", "RISULTATO DELLESERCIZIO"], "amountu"),
    ("total_costs_eur", ["TOTALE COSTI DELLA PRODUZIONE"], "amountu"),
    ("employees_avg", ["NUMERO MEDIO DEI DIPENDENTI", "NUMERO MEDIO DI DIPENDENTI", "NUMERO MEDIO DIPENDENTI", "ORGANICO MEDIO", "OCCUPATI MEDI"], "count"),
]


def parse_balance(lines: List[dict]) -> List[Field]:
    out = _parse_balance_costs(lines)
    for key, labels, kind in BALANCE_SPECS:
        f = _find(lines, labels, kind, key)
        if f is not None:
            out.append(f)
    return out


# ------------------------------------------------------------------------------------------------ visura camerale
REGISTRY_SPECS = [
    ("company_name", ["DENOMINAZIONE", "RAGIONE SOCIALE"], "text"),
    ("vat_number", ["PARTITA IVA", "P. IVA", "P.IVA", "PARTITA I.V.A."], "vat"),
    ("legal_form", ["FORMA GIURIDICA", "NATURA GIURIDICA"], "text"),
    ("ateco_code", ["CODICE ATECO ATTIVITA PREVALENTE", "ATTIVITA PREVALENTE", "CODICE ATECO", "CODICE ATTIVITA", "ATECO"], "ateco"),
    ("province", ["SEDE LEGALE", "INDIRIZZO SEDE", "SEDE"], "province"),
    ("founded_year", ["DATA DI COSTITUZIONE", "DATA ATTO DI COSTITUZIONE", "DATA COSTITUZIONE", "DATA DI ISCRIZIONE"], "year"),
    ("employees", ["NUMERO ADDETTI", "ADDETTI", "NUMERO DIPENDENTI", "DIPENDENTI"], "count"),
]


def parse_registry(lines: List[dict]) -> List[Field]:
    """Visura camerale: denominazione, partita IVA, forma giuridica, ATECO, provincia, anno di costituzione, addetti."""
    out: List[Field] = []
    for key, labels, kind in REGISTRY_SPECS:
        f = _find(lines, labels, kind, key)
        if f is not None:
            out.append(f)
    return out


# ------------------------------------------------------------------------------------------------ F24
# codice tributo, poi (facoltativo) rateazione / mese di riferimento, poi (facoltativo) anno di riferimento, poi l'importo a debito
_F24_ROW = re.compile(r"\b(\d{4})\b\s+(?:(?!20\d{2}\s)(?:\d{4}|[A-Z0-9/\-]{1,12})\s+)?(?:(20\d{2})\s+)?(\d{1,3}(?:\.\d{3})*,\d{2})")


_F24_SECTION = re.compile(r"^SEZIONE\s+(ERARIO|INPS|INAIL|REGIONI|IMU|ACCISE|ALTRI)")
_F24_TAX_SECTIONS = ("ERARIO", "REGIONI", "IMU")                # righe con «codice tributo»: le sezioni INPS e INAIL hanno colonne diverse (causale, matricola, periodo)


def _centers(lines: List[dict], start: int, word: str) -> Optional[float]:
    """Centro orizzontale della colonna la cui intestazione contiene ``word`` («debito», «credito»), cercata nelle righe subito dopo l'intestazione di sezione."""
    for ln in lines[start:start + 6]:
        for text, x0, x1 in ln.get("words", []):
            if word in norm(text):
                return (x0 + x1) / 2
    return None


def parse_f24(lines: List[dict]) -> List[Field]:
    """Righe di un modello F24: codice tributo, anno e importo. Si leggono solo le sezioni con codice tributo (erario, regioni ed enti locali, IMU), non la sezione INPS;
    un importo nella colonna «a credito compensati» non è un debito: si registra come credito."""
    out: List[Field] = []
    has_sections = any(_F24_SECTION.match(norm(ln["text"])) for ln in lines)
    section: Optional[str] = None if has_sections else "ERARIO"
    cx_debit = cx_credit = None
    for i, ln in enumerate(lines):
        text = ln["text"]
        n = norm(text)
        m_sec = _F24_SECTION.match(n)
        if m_sec:
            section = m_sec.group(1)
            cx_debit, cx_credit = _centers(lines, i, "DEBITO"), _centers(lines, i, "CREDITO")
            continue
        if re.match(r"^(SALDO FINALE|TOTALE [A-D]\b)", n):
            if n.startswith("SALDO FINALE"):
                section = None
            continue
        if section not in _F24_TAX_SECTIONS:
            continue
        m = _F24_ROW.search(text)
        if not m:
            continue
        code, year, amount = m.group(1), m.group(2), m.group(3)
        if not (1000 <= int(code) <= 9999):
            continue
        strict = bool(year and 2000 <= int(year) <= 2100)
        value = str(parse_amount(amount))
        credit = False
        if cx_debit is not None and cx_credit is not None:
            for wt, x0, x1 in ln.get("words", []):
                if wt.strip() == amount:
                    ax = (x0 + x1) / 2
                    credit = abs(ax - cx_credit) < abs(ax - cx_debit)
        row = {"codice_tributo": code, "anno": year if strict else None, "importo_debito_eur": "0.00" if credit else value}
        if credit:
            row["importo_credito_eur"] = value
        out.append(Field("f24_row", json.dumps(row), round((0.96 if strict else 0.70) * ln["conf_min"], 4), ln["page"], _scrub(text)))
    return out


# ------------------------------------------------------------------------------------------------ bozza di candidatura
# Un cliente che ha già scritto la propria domanda (o solo il piano dei costi/quadro economico) in un PDF: le stesse
# etichette di spesa del bilancio, ma sotto intestazioni tipiche di un progetto, non di un bilancio civilistico.
_DRAFT_SECTION_START = re.compile(r"PIANO DEI COSTI|QUADRO ECONOMICO|BUDGET DI PROGETTO|COSTI DI PROGETTO|COSTI AMMISSIBILI|"
                                   r"SPESE (?:PREVISTE|AMMISSIBILI)|VOCI DI SPESA|DETTAGLIO (?:DEI )?COSTI|RIPARTIZIONE (?:DEI )?COSTI|PIANO FINANZIARIO")
_DRAFT_SECTION_END = re.compile(r"\bTOTALE\s+(?:COSTI|SPESE|GENERALE|PROGETTO)\b|CRONOPROGRAMMA|ALLEGAT\w+|DICHIARAZION\w+")


def parse_application_draft(lines: List[dict]) -> List[Field]:
    """Righe di costo da una bozza di candidatura scritta dal cliente (non un bilancio civilistico): stessa idea di
    ``parse_balance`` ma con intestazioni di sezione più ampie. Se il documento non usa nessuna delle intestazioni
    note, si leggono comunque tutte le righe con un importo e una descrizione riconoscibile, con una confidenza più
    bassa (il documento non dichiara esplicitamente «qui inizia il piano dei costi»: la verifica umana decide di più).

    Una domanda vera espone gli stessi costi più volte (per voce di spesa, per pacchetto di lavoro, per persona): ogni tabella è un blocco con il suo totale dichiarato.
    Si usa un solo blocco: quello la cui somma torna con il proprio totale e che ha più righe già riconosciute (le altre sono lo stesso costo diviso in un altro modo)."""
    has_section_markers = any(_DRAFT_SECTION_START.search(norm(ln["text"])) for ln in lines)
    base = 0.95 if has_section_markers else 0.75            # nessuna intestazione riconosciuta: più prudenza
    blocks: List[tuple] = []                                 # (righe, totale dichiarato)
    cur: Optional[List[Field]] = [] if not has_section_markers else None
    for ln in lines:
        n = norm(ln["text"])
        if _PAGE_MARK.search(n):
            continue
        if has_section_markers:
            if _DRAFT_SECTION_START.search(n):
                if cur is not None:
                    blocks.append((cur, None))
                cur = []
                continue
            if cur is not None and _DRAFT_SECTION_END.search(n):
                blocks.append((cur, amount_units(ln["text"]) if re.search(r"\bTOTALE\b", n) else None))
                cur = None
        amt = parse_amount(ln["text"])
        if amt is None or cur is None:
            continue
        desc = _ACCOUNT_CODE.sub("", _AMOUNT.sub("", ln["text"])).strip(" .:-")
        if len(desc) < 4 or re.search(r"\bTOTALE\b", norm(desc)):
            continue
        cat, cat_conf = classify_cost(desc)
        conf = round(base * (cat_conf if cat else 0.0) * ln["conf_min"], 4)
        cur.append(Field("expense_line", json.dumps({"description": desc, "amount_eur": str(abs(amt)), "category": cat}, ensure_ascii=False), conf, ln["page"], _scrub(ln["text"])))
    if cur:
        blocks.append((cur, None))
    if not blocks:
        return []
    ok = [bl for bl, total in blocks if total is not None and abs(_block_sum(bl) - total) <= Decimal("1.00")]
    pool = ok or [bl for bl, _ in blocks]
    return max(pool, key=lambda bl: (sum(1 for f in bl if json.loads(f.value)["category"]), len(bl)))


PARSERS: Dict[str, Callable[[List[dict]], List[Field]]] = {
    "PAYSLIP": parse_payslip, "BALANCE_SHEET": parse_balance, "F24": parse_f24, "APPLICATION_DRAFT": parse_application_draft, "COMPANY_REGISTRY": parse_registry,
}
