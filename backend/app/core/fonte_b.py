"""Fonte B — tabelle di mercato e benchmark ufficiali, versionate per data di validità (Modulo 9.2).

NESSUN valore è scritto nel codice. Le tabelle stanno nel database (``fonte_b_*``), arrivano da fonti ufficiali con
la loro provenienza (documento, indirizzo, impronta del file) e sono pubblicate da un manager. Ogni insieme di dati ha
un periodo di validità: una versione nuova non sovrascrive la precedente, che resta consultabile per i calcoli
retroattivi. Quando una tabella manca, il motore lo dice e la riga non viene calcolata: non esistono valori «standard».

Il motore lavora su una fotografia (``FonteBData``) presa una volta sola all'inizio del calcolo, con una
«data di riferimento» esplicita: così lo stesso budget, ricalcolato con la stessa data, dà sempre la stessa impronta.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Dict, Iterator, List, Optional, Tuple

from app.core.db import connect

# Parametri noti del motore (criteri che li usano). Le chiavi sono fisse, i valori arrivano dai dati caricati.
KNOWN_PARAMS: Dict[str, Tuple[str, str, str]] = {
    "fixed_term_surcharge_pct": ("Maggiorazione contributiva sui contratti a tempo determinato", "frazione (0-1)", "criterio 12"),
    "occasional_income_limit_eur": ("Limite annuo di reddito dei collaboratori occasionali", "euro", "criterio 13"),
}


def allow_unofficial() -> bool:
    """Solo per prove e sviluppo: accetta anche insiemi di dati non attestati come ufficiali."""
    return os.getenv("QUANTO_ALLOW_UNOFFICIAL_TABLES", "").lower() in ("1", "true", "yes")


@dataclass(frozen=True)
class CCNLParameters:
    standard_hours: int
    social_charges_pct: Decimal
    tfr_pct: Decimal
    ref: str                       # es. TERZO_SETTORE:LVL_3:2026.1#12


@dataclass(frozen=True)
class Valued:
    value: Decimal
    ref: str


@dataclass(frozen=True)
class _Versioned:
    valid_from: date
    valid_to: Optional[date]
    payload: object


def _pick(candidates: List[_Versioned], on: date):
    best = None
    for c in candidates:
        if c.valid_from <= on and (c.valid_to is None or on <= c.valid_to):
            if best is None or c.valid_from > best.valid_from:
                best = c
    return best.payload if best else None


class FonteBData:
    """Fotografia delle tabelle pubblicate. ``on`` è la data di riferimento predefinita dei calcoli."""

    def __init__(self, on: date):
        self.on = on
        self._ccnl: Dict[Tuple[str, str], List[_Versioned]] = {}
        self._params: Dict[str, List[_Versioned]] = {}
        self._amort: Dict[str, List[_Versioned]] = {}
        self._bench: Dict[Tuple[str, str], List[_Versioned]] = {}

    # ----------------------------------------------------------------- interrogazioni
    def ccnl(self, code: Optional[str], level: str, on: Optional[date] = None) -> Optional[CCNLParameters]:
        if not code:
            return None
        return _pick(self._ccnl.get((code.upper(), str(level)), []), on or self.on)

    def param(self, key: str, on: Optional[date] = None) -> Optional[Valued]:
        return _pick(self._params.get(key, []), on or self.on)

    def amortization(self, category: Optional[str], on: Optional[date] = None) -> Optional[Valued]:
        return _pick(self._amort.get((category or "").upper(), []), on or self.on)

    def benchmark(self, kind: str, category: Optional[str], on: Optional[date] = None) -> Optional[Valued]:
        return _pick(self._bench.get((kind, (category or "").upper()), []), on or self.on)

    def ccnl_codes(self) -> Dict[str, List[str]]:
        """CCNL con almeno un livello valido alla data di riferimento, e relativi livelli."""
        out: Dict[str, List[str]] = {}
        for (code, level), versions in self._ccnl.items():
            if _pick(versions, self.on) is not None:
                out.setdefault(code, []).append(level)
        return {c: sorted(v, key=lambda x: (len(x), x)) for c, v in sorted(out.items())}

    def amortization_categories(self) -> List[str]:
        return sorted(k for k, v in self._amort.items() if _pick(v, self.on) is not None)

    def benchmark_categories(self, kind: str) -> List[str]:
        return sorted(k[1] for k, v in self._bench.items() if k[0] == kind and _pick(v, self.on) is not None)

    def summary(self) -> Dict[str, int]:
        return {"ccnl": len(self.ccnl_codes()), "params": sum(1 for v in self._params.values() if _pick(v, self.on)),
                "amortization": len(self.amortization_categories()),
                "benchmarks": len(self.benchmark_categories("PRICE")) + len(self.benchmark_categories("DAILY_RATE"))}


def load(on: Optional[date] = None) -> FonteBData:
    """Legge dal database tutti gli insiemi pubblicati (le versioni scadute servono per i calcoli retroattivi)."""
    data = FonteBData(on or date.today())
    official = "" if allow_unofficial() else "AND d.official"
    with connect() as conn:
        heads = {r["id"]: r for r in conn.execute(
            f"SELECT d.id, d.kind, d.code, d.version, d.valid_from, d.valid_to FROM fonte_b_datasets d WHERE d.status IN ('PUBLISHED','SUPERSEDED') {official}").fetchall()}
        if not heads:
            return data
        ids = tuple(heads)

        def ver(r):
            h = heads[r["dataset_id"]]
            return _Versioned(h["valid_from"], h["valid_to"], None), h

        for r in conn.execute("SELECT * FROM fonte_b_ccnl WHERE dataset_id = ANY(?)", (list(ids),)).fetchall():
            v, h = ver(r)
            ref = f'{h["code"]}:LVL_{r["level"]}:{h["version"]}#{h["id"]}'
            data._ccnl.setdefault((h["code"].upper(), str(r["level"])), []).append(
                _Versioned(v.valid_from, v.valid_to, CCNLParameters(int(r["standard_hours"]), Decimal(r["social_charges_pct"]), Decimal(r["tfr_pct"]), ref)))
        for r in conn.execute("SELECT * FROM fonte_b_params WHERE dataset_id = ANY(?)", (list(ids),)).fetchall():
            v, h = ver(r)
            data._params.setdefault(r["param_key"], []).append(_Versioned(v.valid_from, v.valid_to, Valued(Decimal(r["value"]), f'{h["code"]}:{r["param_key"]}:{h["version"]}#{h["id"]}')))
        for r in conn.execute("SELECT * FROM fonte_b_amort WHERE dataset_id = ANY(?)", (list(ids),)).fetchall():
            v, h = ver(r)
            data._amort.setdefault(r["category_code"].upper(), []).append(_Versioned(v.valid_from, v.valid_to, Valued(Decimal(r["rate_pct"]), f'{h["code"]}:{r["category_code"]}:{h["version"]}#{h["id"]}')))
        for r in conn.execute("SELECT * FROM fonte_b_benchmarks WHERE dataset_id = ANY(?)", (list(ids),)).fetchall():
            v, h = ver(r)
            data._bench.setdefault((r["bench_kind"], r["category_code"].upper()), []).append(_Versioned(v.valid_from, v.valid_to, Valued(Decimal(r["reference_eur"]), f'{h["code"]}:{r["category_code"]}:{h["version"]}#{h["id"]}')))
    return data


_CURRENT: ContextVar[Optional[FonteBData]] = ContextVar("fonte_b_current", default=None)


@contextmanager
def scope(on: Optional[date] = None) -> Iterator[FonteBData]:
    """Fotografia unica per tutta la durata di un calcolo."""
    data = load(on)
    token = _CURRENT.set(data)
    try:
        yield data
    finally:
        _CURRENT.reset(token)


def current() -> FonteBData:
    data = _CURRENT.get()
    return data if data is not None else load()
