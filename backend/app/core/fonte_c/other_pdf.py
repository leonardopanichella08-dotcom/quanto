"""Lettura dei PDF «altri documenti» dell'azienda che dicono qualcosa di preciso: DURC, contratto di locazione, relazione sul credito d'imposta ricerca e sviluppo, finanziamento.

Un documento si riconosce dal titolo e dalle espressioni che lo definiscono; i dati si leggono solo se compaiono con la loro etichetta («Scadenza validità», «Il canone annuo è convenuto in…»).
Se un dato non c'è o non è chiaro non si legge: il documento resta archiviato. Nessun valore è dedotto.
"""
from __future__ import annotations

import json
import re
from datetime import date
from typing import Any, Dict, List, Optional

from app.core.fonte_c import parsers

Field = parsers.Field
CONF = 0.92                                                  # testo di un PDF nativo con etichetta esplicita: letto bene, ma meno di una cella di foglio
_MONTHS = {"GENNAIO": 1, "FEBBRAIO": 2, "MARZO": 3, "APRILE": 4, "MAGGIO": 5, "GIUGNO": 6, "LUGLIO": 7, "AGOSTO": 8, "SETTEMBRE": 9, "OTTOBRE": 10, "NOVEMBRE": 11, "DICEMBRE": 12}
_EUR = r"(\d{1,3}(?:\.\d{3})*,\d{2})"


def _money(s: str) -> float:
    return float(s.replace(".", "").replace(",", "."))


def _dmy(s: str) -> Optional[str]:
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    return date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat() if m else None


def _long_date(day: str, month: str, year: str) -> Optional[str]:
    mth = _MONTHS.get(parsers.norm(month))
    return date(int(year), mth, int(day)).isoformat() if mth else None


def _fact(key: str, payload: Dict[str, Any], page: int, snippet: str) -> Field:
    return Field(key, json.dumps(payload, ensure_ascii=False, sort_keys=True), CONF, page, snippet[:200], False)


def read(text: str) -> List[Field]:
    out: List[Field] = []
    n = parsers.norm(text)
    flat = re.sub(r"\s+", " ", text)
    if "DURC" in n and "REGOLARITA CONTRIBUTIVA" in n:
        outcome = "regolare" if "ESITO REGOLARE" in n else ("irregolare" if "ESITO IRREGOLARE" in n else None)
        issued = re.search(r"Data emissione\s+(\d{2}/\d{2}/\d{4})", text)
        expires = re.search(r"Scadenza validit\S*\s+(\d{2}/\d{2}/\d{4})", text)
        proto = re.search(r"Numero protocollo\s+(\S+)", text)
        if outcome and expires:
            out.append(_fact("durc", {"outcome": outcome, "issued": _dmy(issued.group(1)) if issued else None, "expires": _dmy(expires.group(1)), "protocol": proto.group(1) if proto else None}, 1,
                             f"DURC {outcome}, scade il {expires.group(1)}"))
    if "CONTRATTO DI LOCAZIONE" in n:
        rent = re.search(r"canone annuo\D{0,60}?" + _EUR + r"\s*euro", flat, re.I)
        span = re.search(r"dal\s+(\d{1,2})\S*\s+([a-zà-ù]+)\s+(\d{4})\s+al\s+(\d{1,2})\S*\s+([a-zà-ù]+)\s+(\d{4})", flat, re.I)
        if rent:
            out.append(_fact("lease", {"annual_rent_eur": _money(rent.group(1)), "from": _long_date(*span.groups()[:3]) if span else None, "to": _long_date(*span.groups()[3:]) if span else None},
                             1, f"canone annuo {rent.group(1)} euro"))
    if "CREDITO DIMPOSTA RICERCA" in n:                      # norm() toglie gli apostrofi
        base = re.search(r"Totale costi ammissibili\s*" + _EUR, flat, re.I)
        credit = re.search(r"Credito d.imposta \(aliquota del (\d+)%\)\s*" + _EUR, flat, re.I)
        year = re.search(r"01/01/(20\d{2})", n)
        if base and credit:
            out.append(_fact("rd_credit", {"year": int(year.group(1)) if year else None, "eligible_costs_eur": _money(base.group(1)), "rate_pct": int(credit.group(1)), "credit_eur": _money(credit.group(2))}, 1,
                             f"costi ammissibili {base.group(1)}, credito {credit.group(2)}"))
    if "PIANO DI AMMORTAMENTO DEL FINANZIAMENTO" in n:
        loan = re.search(r"Importo originario euro\s+" + _EUR + r"\s*-\s*erogato il\s+(\d{2}/\d{2}/\d{4})\s*-\s*(\d+)\s+rate", flat, re.I)
        if loan:
            out.append(_fact("loan", {"original_eur": _money(loan.group(1)), "disbursed": _dmy(loan.group(2)), "installments": int(loan.group(3))}, 1, f"finanziamento di {loan.group(1)} euro"))
    return out
