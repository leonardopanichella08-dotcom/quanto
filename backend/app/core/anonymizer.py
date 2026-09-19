"""Pseudonimizzazione lato server dei dati personali (GDPR Art. 9 / privacy by design).

Differenze rispetto a un semplice SHA-256 con sale costante: codici fiscali e IBAN hanno
spazi di ricerca enumerabili, quindi un hash non chiavato è invertibile con un attacco a
dizionario. Qui il token è un HMAC-SHA256 con chiave segreta ``QUANTO_PII_KEY`` (mai nel
repository). La ricomposizione dei dati reali avviene solo lato client.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
from typing import Any, Dict

logger = logging.getLogger("quanto.anonymizer")

_DEV_KEY = "INSECURE-DEV-KEY-SET-QUANTO_PII_KEY"
_IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")
_CF_RE = re.compile(r"\b[A-Z]{6}\d{2}[A-EHLMPR-T]\d{2}[A-Z]\d{3}[A-Z]\b")
PII_FIELDS = ("employee_name", "tax_code", "fiscal_code", "iban", "home_address")


class PrivacyAnonymizer:
    @staticmethod
    def _key() -> bytes:
        key = os.getenv("QUANTO_PII_KEY", "")
        if not key:
            logger.warning("QUANTO_PII_KEY non impostata: uso la chiave di sviluppo (NON usare in produzione).")
            key = _DEV_KEY
        return key.encode("utf-8")

    @classmethod
    def generate_opaque_token(cls, raw_value: str) -> str:
        """Token opaco e deterministico (stesso dato -> stesso token) non invertibile senza la chiave."""
        normalized = re.sub(r"\s+", " ", raw_value.strip().upper())
        digest = hmac.new(cls._key(), normalized.encode("utf-8"), hashlib.sha256).hexdigest()
        return "TOK-" + digest[:16]

    @classmethod
    def sanitize_payroll_record(cls, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Tokenizza i campi PII di un record di Fonte C lasciando intatti i soli parametri numerici."""
        sanitized = dict(record_data)
        for field in PII_FIELDS:
            if sanitized.get(field):
                sanitized[field] = cls.generate_opaque_token(str(sanitized[field]))
        return sanitized

    @classmethod
    def scrub_free_text(cls, text: str) -> str:
        """Sostituisce IBAN e codici fiscali eventualmente presenti in testo libero (es. causali)."""
        text = _IBAN_RE.sub(lambda m: cls.generate_opaque_token(m.group(0)), text)
        return _CF_RE.sub(lambda m: cls.generate_opaque_token(m.group(0)), text)
