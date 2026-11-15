"""Iscrizioni alla newsletter di QUANTO (aggiornamenti di finanza agevolata per gli studi).

Si salva solo ciò che serve: l'indirizzo e-mail, il momento del consenso e la versione del testo di consenso accettato.
Senza consenso esplicito non si salva nulla. Una seconda iscrizione con lo stesso indirizzo non crea un doppione.
L'indirizzo non compare mai nei log né nella timeline: l'evento registra solo che c'è stata un'iscrizione.
"""
from __future__ import annotations

import re
from typing import Any, Dict

from app.core import events
from app.core.db import connect

CONSENT_VERSION = "2026-11-15"
CONSENT_TEXT = ("Acconsento a ricevere la newsletter di QUANTO sulla finanza agevolata. Il mio indirizzo serve solo a questo invio, "
                "non viene ceduto a terzi e posso cancellarmi in qualunque momento.")
_EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[a-z]{2,24}$", re.I)


class NewsletterError(ValueError):
    pass


def subscribe(email: str, consent: bool, source: str = "homepage") -> Dict[str, Any]:
    email = (email or "").strip().lower()
    if not _EMAIL.match(email) or len(email) > 254:
        raise NewsletterError("Indirizzo e-mail non valido")
    if consent is not True:
        raise NewsletterError("Serve il consenso per iscriversi alla newsletter")
    now = events.now_iso()
    with connect() as conn:
        found = conn.execute("SELECT 1 FROM newsletter_subscribers WHERE email=?", (email,)).fetchone()
        if found is None:
            conn.execute("INSERT INTO newsletter_subscribers (email, consent_at, consent_version, source) VALUES (?,?,?,?)",
                         (email, now, CONSENT_VERSION, (source or "homepage")[:40]))
    if found is None:
        events.record("newsletter.subscribe", "Nuova iscrizione alla newsletter", actor="pubblico")
    return {"ok": True, "already": found is not None}


def count() -> int:
    with connect() as conn:
        return int(conn.execute("SELECT COUNT(*) c FROM newsletter_subscribers").fetchone()["c"])
