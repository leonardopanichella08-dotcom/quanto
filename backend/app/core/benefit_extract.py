"""Quanto vale un bando: l'intensità dell'agevolazione letta dal testo ufficiale, anche quando sta in una tabella per dimensione d'impresa.

Il lettore delle regole (ingestion) trova la frase «contributo pari al 50% delle spese». Molti bandi però scrivono l'intensità in una tabella:

    TIPOLOGIA BENEFICIARIO      BASE   MAGGIORAZIONI         MAX
    Micro-piccole imprese       25%    20%   15%             60%
    Medie imprese               25%    10%   15%             50%

Qui si legge ogni riga con la sua dimensione: la percentuale base (la prima) e quella massima (la più alta, con tutte le maggiorazioni). Di ogni riga si
conserva la frase da cui viene, così chi controlla vede il testo ufficiale. Niente viene dedotto: se il testo non ha una percentuale accanto alla dimensione,
la riga non c'è.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

SIZE_PATTERNS = [
    ("MICRO_SMALL", re.compile(r"micro[\s,\-]*(?:e\s+)?piccol[ae]\s+impres[ae]|micro[\s\-]?piccol[ae]", re.I)),
    ("SMALL", re.compile(r"\bpiccol[ae]\s+impres[ae]|\bpiccole\b", re.I)),
    ("MEDIUM", re.compile(r"\bmedi[ae]\s+impres[ae]|\bmedie\b", re.I)),
    ("LARGE", re.compile(r"\bgrand[ie]\s+impres[ae]|\bGI\b(?!\w)|\bmid[\s\-]?caps?\b", re.I)),
    ("PMI", re.compile(r"\bM?PMI\b|piccole\s+e\s+medie\s+impres[ae]|micro,\s*piccole\s+e\s+medie", re.I)),
]
_PCT = re.compile(r"(?<![\d.,])(\d{1,3}(?:[.,]\d+)?)\s?%")
_CONTEXT = re.compile(r"intensit|contribut|agevolazion|aiuto|aiuti|fondo perduto|sovvenzion", re.I)
_NOT_AID = re.compile(r"anticipazion|cauzion|fideiussor|IVA\b|saldo|premialit[àa] dei criteri|punteggio", re.I)
_FLAT = re.compile(
    r"(?:contribut[oi]|agevolazion[ei]|intensit[àa](?: di aiuto| dell.agevolazione)?|sovvenzion[ei])[^.\n%]{0,90}?"
    r"(?:pari al|fino al|nella misura (?:massima )?(?:del|pari al)|del|al)\s*(\d{1,3}(?:[.,]\d+)?)\s?%\s*(?:\(?[a-z]*\)?\s*)?(?:delle|dei|della|degli|sulle|sui)?\s*(?:spese|costi|investiment)",
    re.I)
_MONEY = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d{3}){1,2})(?:,\d{2})?\s*$")


def _pct(x: str) -> float:
    return float(x.replace(",", ".")) / 100.0


def _line_with_tail(lines: List[str], i: int) -> str:
    """La riga e, se la successiva è fatta solo di numeri e simboli (cella andata a capo), anche quella."""
    out = lines[i]
    if i + 1 < len(lines) and re.fullmatch(r"[\d\s%.,*/o\-–()]+", lines[i + 1].strip() or "x") and "%" in lines[i + 1]:
        out += " " + lines[i + 1]
    return out


def intensity_rows(text: str, url: Optional[str] = None) -> List[Dict[str, Any]]:
    """Righe «dimensione → % base / % massima» e frasi «contributo pari al N% delle spese». Ognuna con il testo da cui viene."""
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in (text or "").splitlines()]
    rows: List[Dict[str, Any]] = []
    for i, ln in enumerate(lines):
        if not ln:
            continue
        for code, pat in SIZE_PATTERNS:
            m = pat.search(ln)
            if not m or m.start() > 3:                       # è una riga di tabella solo se la dimensione apre la riga
                continue
            seg = _line_with_tail(lines, i)[m.start():]
            nxt = min((p.search(seg, m.end() - m.start()).start() for _, p in SIZE_PATTERNS if p.search(seg, m.end() - m.start())), default=len(seg))
            seg = seg[:nxt]
            pcts = [_pct(x) for x in _PCT.findall(seg)]
            pcts = [p for p in pcts if 0.05 <= p <= 1.0]
            if not pcts or _NOT_AID.search(seg):
                continue
            context = " ".join(lines[max(0, i - 12): i + 1])
            if not _CONTEXT.search(context):
                continue
            rows.append({"size": code, "base": pcts[0], "max": max(pcts), "text": seg[:220], "url": url})
            break
    for m in _FLAT.finditer(re.sub(r"\s+", " ", text or "")):
        p = _pct(m.group(1))
        if 0.05 <= p <= 1.0:
            rows.append({"size": "ALL", "base": p, "max": p, "text": m.group(0)[:220], "url": url})
    seen, out = set(), []
    for r in rows:
        k = (r["size"], r["base"], r["max"])
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def caps(text: str) -> List[float]:
    """Importi massimi di contributo (€) dopo un'intestazione «importo massimo / massimale»: le righe di tabella che finiscono con un importo."""
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in (text or "").splitlines()]
    found: List[float] = []
    for i, ln in enumerate(lines):
        if re.search(r"importo massimo|massimale|contributo massimo", ln, re.I):
            for k in range(i, min(i + 10, len(lines))):
                m = _MONEY.search(lines[k])
                if m:
                    v = float(m.group(1).replace(".", ""))
                    if 10_000 <= v <= 100_000_000:
                        found.append(v)
    return sorted(set(found))


_DM = re.compile(r"de[\s\-]*minimis|2023/2831|1407/2013", re.I)
_DM_NEG = re.compile(r"\bnon\s+(?:rientra|è\s+soggett\w+|è\s+concess\w+|è\s+in\s+regime|costituisce|si\s+configura)[^.;]{0,60}$", re.I)   # solo la negazione esplicita: nel dubbio il bando conta


def de_minimis_mentions(text: str, url: Optional[str] = None) -> List[Dict[str, Any]]:
    """I passaggi del testo ufficiale che citano il regime de minimis (o i suoi regolamenti), ognuno con le parole da cui viene.
    ``negated`` = il passaggio dice il contrario («non rientra nel de minimis»): quello non conta come aiuto in de minimis."""
    flat = re.sub(r"\s+", " ", text or "")
    out: List[Dict[str, Any]] = []
    last_end = -1
    for m in _DM.finditer(flat):
        if m.start() < last_end:                           # lo stesso passaggio citato due volte di seguito (regime + regolamento)
            continue
        lo, hi = max(0, m.start() - 170), min(len(flat), m.end() + 170)
        if lo > 0 and " " in flat[lo:m.start()]:
            lo += flat[lo:].index(" ") + 1
        if hi < len(flat) and " " in flat[m.end():hi]:
            hi = flat.rfind(" ", m.end(), hi)
        last_end = hi
        out.append({"text": flat[lo:hi].strip(), "url": url, "negated": bool(_DM_NEG.search(flat[max(0, m.start() - 90):m.start()]))})
        if len(out) >= 4:
            break
    return out


def applicable(rows: List[Dict[str, Any]], size_code: Optional[str]) -> List[Dict[str, Any]]:
    """Le righe che valgono per la dimensione dell'impresa (microimpresa, piccola, media, grande); quelle senza dimensione valgono per tutti."""
    if size_code is None:
        return [r for r in rows if r["size"] in ("ALL", "PMI")]
    ok = {"MICRO": {"MICRO_SMALL", "SMALL", "PMI", "ALL"}, "SMALL": {"MICRO_SMALL", "SMALL", "PMI", "ALL"}, "MEDIUM": {"MEDIUM", "PMI", "ALL"}, "LARGE": {"LARGE", "ALL"}}[size_code]
    return [r for r in rows if r["size"] in ok]


def range_for(rows: List[Dict[str, Any]], size_code: Optional[str]) -> Optional[Dict[str, Any]]:
    """Da quale percentuale a quale: la più bassa tra le basi applicabili e la più alta tra i massimi. None se il testo non dice nulla per quella dimensione."""
    app = applicable(rows, size_code)
    if not app:
        return None
    return {"low": min(r["base"] for r in app), "high": max(r["max"] for r in app), "rows": app}
