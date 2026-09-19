"""Notifiche webhook event-driven (budget.validated, allocation.optimized, criteria.failed, pattern.matched).

Sicurezza: URL e segreto provengono solo dall'ambiente (``QUANTO_WEBHOOK_URLS`` separati da virgola,
``QUANTO_WEBHOOK_SECRET``): nessun URL è accettato da richieste esterne (no SSRF). Il corpo è firmato
HMAC-SHA256 (header ``X-Quanto-Signature``). Senza segreto non si invia nulla. I payload contengono solo
identificativi opachi e totali, mai dati personali o contabili di dettaglio.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

import httpx

logger = logging.getLogger("quanto.webhooks")


def emit(event: str, data: Dict[str, Any]) -> None:
    urls = [u.strip() for u in os.getenv("QUANTO_WEBHOOK_URLS", "").split(",") if u.strip()]
    secret = os.getenv("QUANTO_WEBHOOK_SECRET", "")
    if not urls:
        return
    if not secret:
        logger.warning("Webhook configurati ma QUANTO_WEBHOOK_SECRET assente: invio annullato.")
        return
    body = json.dumps({"event": event, "emitted_at": datetime.now(timezone.utc).isoformat(), "data": data}, sort_keys=True)
    signature = "sha256=" + hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    for url in urls:
        try:
            httpx.post(url, content=body, timeout=5.0, headers={"Content-Type": "application/json", "X-Quanto-Event": event, "X-Quanto-Signature": signature})
        except httpx.HTTPError as exc:
            logger.warning("Webhook %s verso %s fallito: %s", event, url.split("?")[0], type(exc).__name__)
