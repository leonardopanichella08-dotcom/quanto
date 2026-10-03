"""Ciclo di vita di un bando: APERTO, IN_ARRIVO, CHIUSO o SCONOSCIUTO — letto dalla pagina ufficiale, mai indovinato dal nome.

Le schede di incentivi.gov.it dichiarano «Data apertura» e «Data chiusura». La scadenza letta si salva in ``bandi.deadline`` (ISO);
se la pagina non ha date si salva «non indicata», così la voce non viene riletta ogni notte. Le voci mai toccate e già chiuse le elimina
``catalog_job.cleanup_stale``: qui si fa solo la lettura.
"""
from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import date
from typing import Any, Dict, Optional, Tuple

from app.core import research
from app.core.db import connect

_DATE = r"(\d{1,2})/(\d{1,2})/(\d{4})"
_OPEN = re.compile(r"Data\s+apertura\s+" + _DATE, re.I)
_CLOSE = re.compile(r"Data\s+chiusura\s+" + _DATE, re.I)


def _iso(m: Optional["re.Match[str]"]) -> Optional[str]:
    if not m:
        return None
    day, month, year = (int(x) for x in m.groups())
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def parse_dates(text: str) -> Tuple[Optional[str], Optional[str]]:
    """(apertura, chiusura) in ISO, dalla prima occorrenza nella pagina."""
    return _iso(_OPEN.search(text)), _iso(_CLOSE.search(text))


def classify(opens: Optional[str], closes: Optional[str], today: Optional[str] = None) -> str:
    today = today or date.today().isoformat()
    if closes and closes < today:
        return "CHIUSO"
    if opens and opens > today:
        return "IN_ARRIVO"
    if opens or closes:
        return "APERTO"
    return "SCONOSCIUTO"


def _read(url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    try:
        raw, _, ctype = research.http_get(url, limited=False)
        text, _, _ = research.html_to_text(research._decode(raw, ctype))
    except Exception as exc:  # noqa: BLE001 - una pagina che non risponde non ferma il lotto
        return None, None, type(exc).__name__
    return (*parse_dates(text), None)


def scan_catalog(limit: int = 80, workers: int = 12, budget_s: float = 40.0) -> Dict[str, Any]:
    """Legge le date di un lotto di voci del catalogo mai toccate e senza scadenza nota (prima quelle che citano anni passati)."""
    this_year = str(date.today().year)
    with connect() as conn:
        rows = conn.execute(
            "SELECT bando_id, name, source_url FROM bandi WHERE bando_id LIKE 'CAT-%' AND catalog_status != 'CURATED' AND extraction_status = 'NOT_STARTED' "
            "AND requested_by_clients = 0 AND deadline IS NULL AND source_url LIKE '%incentivi.gov.it%' ORDER BY bando_id"
        ).fetchall()
    rows = sorted(rows, key=lambda r: this_year in (r["name"] or ""))[:limit]      # le voci che non citano l'anno in corso sono le più sospette
    report: Dict[str, Any] = {"scanned": 0, "CHIUSO": 0, "IN_ARRIVO": 0, "APERTO": 0, "SCONOSCIUTO": 0, "errors": 0, "remaining_unscanned": max(0, len(rows))}
    if not rows:
        return report
    t0 = time.monotonic()
    pool = ThreadPoolExecutor(max_workers=workers)
    futures = {pool.submit(_read, r["source_url"]): r["bando_id"] for r in rows}
    done, _ = wait(futures, timeout=budget_s)
    pool.shutdown(wait=False, cancel_futures=True)
    updates = []
    for fut in done:
        opens, closes, err = fut.result()
        if err:
            report["errors"] += 1
            continue
        state = classify(opens, closes)
        report[state] += 1
        updates.append((closes or "non indicata", futures[fut]))
    if updates:
        with connect() as conn:
            conn.executemany("UPDATE bandi SET deadline = ? WHERE bando_id = ? AND deadline IS NULL", updates)
    report["scanned"] = len(updates)
    report["seconds"] = round(time.monotonic() - t0, 1)
    with connect() as conn:
        report["remaining_unscanned"] = conn.execute(
            "SELECT COUNT(*) c FROM bandi WHERE bando_id LIKE 'CAT-%' AND catalog_status != 'CURATED' AND extraction_status = 'NOT_STARTED' "
            "AND requested_by_clients = 0 AND deadline IS NULL AND source_url LIKE '%incentivi.gov.it%'").fetchone()["c"]
    return report
