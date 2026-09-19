"""Fonte B — tabelle di mercato / benchmark ufficiali, versionate per data di validità.

ATTENZIONE: i valori sotto sono i PARAMETRI ILLUSTRATIVI della specifica QUANTO, non le
tabelle ministeriali ufficiali. Prima di qualsiasi uso reale vanno sostituiti da un
connettore verso le fonti istituzionali (Modulo 9.2). Ogni versione è identificata da
``TABLE_VERSION`` e finisce nell'hash di riga, così un ricalcolo retroattivo con tabelle
diverse produce una Merkle Root diversa (e quindi è rilevabile).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional, Tuple

from app.models.schemas import CCNLType

TABLE_VERSION = "2026.1-ILLUSTRATIVE"

# Parametri illustrativi (da sostituire con fonti ufficiali)
FIXED_TERM_SURCHARGE_PCT = Decimal("0.0140")      # criterio 12: maggiorazione contributiva tempo determinato
OCCASIONAL_INCOME_LIMIT_EUR = Decimal("5000.00")  # criterio 13: limite annuo collaboratori occasionali


@dataclass(frozen=True)
class CCNLParameters:
    standard_hours: int
    social_charges_pct: Decimal
    tfr_pct: Decimal


_TBL: Dict[Tuple[CCNLType, str], CCNLParameters] = {
    (CCNLType.TERZO_SETTORE, "1"): CCNLParameters(1656, Decimal("0.3100"), Decimal("0.0833")),
    (CCNLType.TERZO_SETTORE, "2"): CCNLParameters(1656, Decimal("0.3000"), Decimal("0.0833")),
    (CCNLType.TERZO_SETTORE, "3"): CCNLParameters(1656, Decimal("0.3000"), Decimal("0.0833")),
    (CCNLType.METALMECCANICA, "3"): CCNLParameters(1600, Decimal("0.3200"), Decimal("0.0833")),
    (CCNLType.METALMECCANICA, "5"): CCNLParameters(1600, Decimal("0.3200"), Decimal("0.0833")),
    (CCNLType.COMMERCIO, "3"): CCNLParameters(1680, Decimal("0.2950"), Decimal("0.0833")),
    (CCNLType.COMMERCIO, "4"): CCNLParameters(1680, Decimal("0.2950"), Decimal("0.0833")),
}


def lookup_ccnl(ccnl: CCNLType, level: str) -> Optional[CCNLParameters]:
    """Restituisce i parametri o ``None`` se la coppia CCNL/livello non è coperta."""
    return _TBL.get((ccnl, level))


def table_ref(ccnl: CCNLType, level: str) -> str:
    return f"{ccnl.value}:LVL_{level}:v{TABLE_VERSION}"
