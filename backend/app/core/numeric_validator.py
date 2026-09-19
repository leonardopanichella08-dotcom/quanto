"""Validatore Numerico post-generazione (Strict Grounding, Modulo 7.2).

Ogni numero presente nel testo prodotto dal renderer deve corrispondere ESATTAMENTE (parsing
``Decimal``, nessuna tolleranza) a un numero del JSON bloccato da cui il testo deriva. Qualsiasi
cifra inventata, arrotondata diversamente o non tracciabile fa rigettare l'intero testo.

Gli identificativi alfanumerici (LINE-001, TRANSIZIONE-5.0-2026, 0x7f83...) non sono "numeri":
vengono estratti a parte e devono comparire testualmente nel JSON sorgente.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, List, Set

# token che mescolano lettere e cifre: id, hash, versioni ("LINE-001", "0x7f83", "PRJ-2026-T50")
_IDENT_RE = re.compile(r"(?<![\w.])(?=[\w.\-]*[A-Za-z])(?=[\w.\-]*\d)[\w][\w.\-]*[\w]|(?<![\w.])0x[0-9a-fA-F]+")
_NUM_RE = re.compile(r"(?<![\w.,])\d{1,3}(?:\.\d{3})+(?:,\d+)?(?![\w])|(?<![\w.,])\d+(?:[.,]\d+)?(?![\w])")
_THOUSANDS_RE = re.compile(r"^\d{1,3}(\.\d{3})+$")


def _interpretations(token: str) -> Set[Decimal]:
    """Letture possibili di un token numerico (formato italiano o inglese)."""
    out: Set[Decimal] = set()
    candidates: List[str] = []
    if "." in token and "," in token:
        candidates.append(token.replace(".", "").replace(",", "."))
    elif "," in token:
        candidates.append(token.replace(",", "."))
    elif _THOUSANDS_RE.match(token):
        candidates += [token.replace(".", ""), token]  # "26.283": migliaia oppure decimale
    else:
        candidates.append(token)
    for c in candidates:
        try:
            out.add(Decimal(c).normalize())
        except InvalidOperation:
            pass
    return out


def extract_numbers(text: str) -> tuple[List[Set[Decimal]], List[str]]:
    """Restituisce (letture per ciascun numero, identificativi) trovati nel testo."""
    idents = [m.group(0) for m in _IDENT_RE.finditer(text)]
    stripped = _IDENT_RE.sub(" ", text)
    return [_interpretations(m.group(0)) for m in _NUM_RE.finditer(stripped)], idents


def _leaves(obj: Any) -> Iterable[Any]:
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _leaves(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _leaves(v)
    else:
        yield obj


def numbers_in_payload(payload: Any) -> Set[Decimal]:
    allowed: Set[Decimal] = set()
    for leaf in _leaves(payload):
        if isinstance(leaf, bool) or leaf is None:
            continue
        if isinstance(leaf, (int, float, Decimal)):
            allowed.add(Decimal(str(leaf)).normalize())
        elif isinstance(leaf, str):
            readings, _ = extract_numbers(leaf)
            for r in readings:
                allowed |= r
    return allowed


@dataclass
class ValidationResult:
    ok: bool
    problems: List[str] = field(default_factory=list)


def validate_text_against_payload(text: str, payload: Any, extra_allowed: Iterable[int] = ()) -> ValidationResult:
    """True solo se OGNI numero e OGNI identificativo del testo è riconducibile al JSON bloccato."""
    allowed = numbers_in_payload(payload) | {Decimal(x).normalize() for x in extra_allowed}
    haystack = json.dumps(payload, default=str, ensure_ascii=False)
    readings, idents = extract_numbers(text)
    problems: List[str] = []
    for r in readings:
        if not r & allowed:
            problems.append("numero non presente nel JSON: " + "/".join(sorted(str(x) for x in r)))
    for ident in idents:
        if ident not in haystack:
            problems.append(f"identificativo non presente nel JSON: {ident}")
    return ValidationResult(ok=not problems, problems=problems)
