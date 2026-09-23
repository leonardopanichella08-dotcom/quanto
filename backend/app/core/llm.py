"""Modello linguistico (Modulo 7, 9.1, 13): collegamento, estrazione a passaggi multipli (Stadio 3) e arricchimento del catalogo (Stadio 1).

Regole che non si aggirano:
- l'LLM non calcola e non decide: per il testo riceve solo il JSON già bloccato dal motore e ogni cifra viene ricontrollata dal
  validatore numerico (renderer.py); se non torna, si usa il testo fisso;
- nell'estrazione di regole ogni valore deve arrivare con la frase del documento da cui lo ricava: se quella frase NON compare
  davvero nel testo, il valore viene scartato. Il codice (non l'LLM) confronta i passaggi: concordanza → regola pubblicata;
  disaccordo → coda di verifica del consulente;
- senza chiave (``ANTHROPIC_API_KEY`` o ``QUANTO_LLM_API_KEY``) non si chiama nulla: tutto resta com'è, deterministico.

Configurazione: ``QUANTO_LLM_PROVIDER`` (per ora ``anthropic``), ``QUANTO_LLM_MODEL`` (default claude-sonnet-5), ``QUANTO_LLM_PASSES`` (default 3).
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("quanto.llm")

DEFAULT_MODEL = "claude-sonnet-5"
DEFAULT_PASSES = 3
MAX_TEXT_CHARS = 24_000


class LLMError(RuntimeError):
    pass


class AnthropicClient:
    """Chiamata diretta all'API Messages di Anthropic (nessuna dipendenza in più)."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, base_url: str = "https://api.anthropic.com", timeout: float = 50.0,
                 transport: Optional[httpx.BaseTransport] = None):
        self.api_key, self.model, self.base_url, self.timeout, self.transport = api_key, model, base_url.rstrip("/"), timeout, transport

    def _post(self, system: str, user: str, max_tokens: int, temperature: float) -> str:
        with httpx.Client(timeout=self.timeout, transport=self.transport) as c:
            r = c.post(f"{self.base_url}/v1/messages", headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                       json={"model": self.model, "max_tokens": max_tokens, "temperature": temperature, "system": system, "messages": [{"role": "user", "content": user}]})
        if r.status_code >= 400:
            raise LLMError(f"Il provider ha risposto {r.status_code}")
        parts = r.json().get("content", [])
        return "".join(p.get("text", "") for p in parts if p.get("type") == "text").strip()

    def complete(self, system: str, context_json: str) -> str:            # interfaccia del renderer (riepiloghi testuali)
        return self._post(system, context_json, 500, 0.0)

    def complete_json(self, system: str, user: str, temperature: float = 0.4) -> str:
        return self._post(system, user, 1800, temperature)


def get_client() -> Optional[AnthropicClient]:
    provider = os.getenv("QUANTO_LLM_PROVIDER", "anthropic").strip().lower()
    key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("QUANTO_LLM_API_KEY") or ""
    if not key:
        return None
    if provider != "anthropic":
        raise LLMError(f"Provider LLM non supportato: {provider}")
    return AnthropicClient(key, os.getenv("QUANTO_LLM_MODEL", DEFAULT_MODEL))


def passes_wanted() -> int:
    try:
        return max(2, min(int(os.getenv("QUANTO_LLM_PASSES", DEFAULT_PASSES)), 7))
    except ValueError:
        return DEFAULT_PASSES


# ------------------------------------------------------------------------------------------------ Stadio 3
def _fold(t: str) -> str:
    return re.sub(r"\s+", " ", (t or "").lower()).strip()


def _rule_catalog() -> str:
    from app.core.consultant import RULE_INFO
    from app.core.ingestion import RULE_KEYS
    lines = []
    for k in sorted(RULE_KEYS):
        info = RULE_INFO.get(k)
        if info:
            lines.append(f'- {k}: {info["label"]}. {info["meaning"]}')
    return "\n".join(lines)


SYSTEM_EXTRACT = (
    "Sei un lettore di testi normativi per un motore di controllo di budget. Leggi il testo e restituisci SOLO un oggetto JSON "
    '{"rules":[{"key":"...","value":"...","quote":"..."}]}. Regole: usa solo le chiavi dell\'elenco; includi una regola SOLO se il testo la dice '
    "esplicitamente (mai dedurre, mai stimare); \"quote\" è la frase ESATTA copiata dal testo da cui ricavi il valore; percentuali come «20%», "
    "importi come numero in euro, date come GG/MM/AAAA, sì/no come true/false. Se il testo non dice nulla, restituisci {\"rules\":[]}.\n\nChiavi ammesse:\n"
)


def extract_pass(client, text: str) -> Dict[str, str]:
    """Un passaggio: {chiave: valore canonico}, solo per i valori con la citazione realmente presente nel testo."""
    from app.core.ingestion import RULE_KEYS, normalize_value
    raw = client.complete_json(SYSTEM_EXTRACT + _rule_catalog(), "TESTO:\n" + text[:MAX_TEXT_CHARS])
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return {}
    try:
        items = json.loads(m.group(0)).get("rules", [])
    except ValueError:
        return {}
    hay = _fold(text)
    out: Dict[str, str] = {}
    for it in items if isinstance(items, list) else []:
        key, value, quote = it.get("key"), it.get("value"), it.get("quote")
        if key not in RULE_KEYS or value is None or not isinstance(quote, str) or len(_fold(quote)) < 12:
            continue
        if _fold(quote) not in hay:                                   # citazione inventata: valore scartato
            logger.warning("Citazione non trovata nel testo per %s: scartata", key)
            continue
        try:
            out[key] = normalize_value(key, value)
        except ValueError:
            continue
    return out


def extract_passes(client, text: str, n: Optional[int] = None) -> List[Dict[str, str]]:
    """N letture indipendenti dello stesso testo. Errori del provider: si registra e si prosegue con quelle riuscite."""
    passes: List[Dict[str, str]] = []
    for _ in range(n or passes_wanted()):
        try:
            passes.append(extract_pass(client, text))
        except Exception as exc:
            logger.warning("Passaggio LLM non riuscito (%s)", type(exc).__name__)
    return passes


# ------------------------------------------------------------------------------------------------ Stadio 1 (arricchimento)
SYSTEM_META = (
    "Dal testo di una pagina di un incentivo restituisci SOLO JSON {\"name\":...,\"issuer\":...,\"deadline\":...} con nome del bando, ente erogatore e scadenza "
    "(formato AAAA-MM-GG oppure null). Ogni campo deve essere scritto nel testo; se non c'è, null. Aggiungi \"quote_issuer\" e \"quote_deadline\": la frase esatta di origine."
)


def extract_metadata(client, page_text: str) -> Dict[str, Optional[str]]:
    raw = client.complete_json(SYSTEM_META, "TESTO:\n" + page_text[:8000], temperature=0.0)
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return {}
    try:
        j = json.loads(m.group(0))
    except ValueError:
        return {}
    hay = _fold(page_text)
    out: Dict[str, Optional[str]] = {"name": (j.get("name") or None)}
    for key, q in (("issuer", "quote_issuer"), ("deadline", "quote_deadline")):
        v, quote = j.get(key), j.get(q)
        out[key] = v if v and isinstance(quote, str) and _fold(quote) in hay else None
    if out["deadline"] and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(out["deadline"])):
        out["deadline"] = None
    return out
