"""LLM Renderer con Strict Grounding (Modulo 7.2).

Flusso: JSON bloccato -> (opzionale) LLM scrive la frase -> Validatore Numerico -> se anche una sola
cifra non coincide, il testo dell'LLM è scartato e si usa il template statico deterministico.

L'LLM riceve SOLO il contesto strutturato (importi, riferimenti, stati), mai documenti grezzi.
Nessun client LLM è configurato di default: ``LLMClient`` è il punto di estensione.
"""
from __future__ import annotations

import json
import logging
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, Optional, Protocol, Tuple

from app.core.numeric_validator import validate_text_against_payload
from app.models.schemas import ItemValidationStatus

logger = logging.getLogger("quanto.renderer")

SYSTEM_PROMPT = (
    "Sei il renderer testuale di QUANTO. Riassumi in italiano, in 2-4 frasi, il JSON fornito. "
    "Usa ESCLUSIVAMENTE i numeri e gli identificativi presenti nel JSON, senza arrotondarli né "
    "calcolarne di nuovi. Non aggiungere valutazioni sulla probabilità di vincita del bando."
)
# costanti ammesse nel testo (scala del punteggio)
EXTRA_ALLOWED = (100,)


class LLMClient(Protocol):
    def complete(self, system: str, context_json: str) -> str: ...


def eur(value: float) -> str:
    """Formato italiano: 26283.5 -> '26.283,50'."""
    q = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    s = f"{q:,.2f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def budget_context(response_like: Dict[str, Any]) -> Dict[str, Any]:
    """Contesto numerico bloccato passato al renderer (e al validatore)."""
    items = response_like["items"]
    adjusted = [i for i in items if i["status"] == ItemValidationStatus.CAP_EXCEEDED_ADJUSTED.value]
    blocked = [i for i in items if i["status"] in (ItemValidationStatus.REJECTED.value, ItemValidationStatus.MISSING_DOCUMENTS.value)]
    return {
        "bando_id": response_like["bando_id"],
        "bando_name": response_like["bando_name"],
        "items_total": len(items),
        "items_adjusted": len(adjusted),
        "items_blocked": len(blocked),
        "total_requested_eur": response_like["total_requested_eur"],
        "total_approved_eur": response_like["total_approved_eur"],
        "total_reduced_eur": response_like["total_rejected_eur"],
        "conformity_score": response_like["conformity_score"],
        "merkle_root": response_like["merkle_root"],
    }


def static_budget_summary(ctx: Dict[str, Any]) -> str:
    parts = [
        f"Controllo completato per il bando '{ctx['bando_name']}' (ID: {ctx['bando_id']}). "
        f"Esaminate {ctx['items_total']} voci: {eur(ctx['total_approved_eur'])} € ammessi su {eur(ctx['total_requested_eur'])} € richiesti "
        f"(ridotti o esclusi: {eur(ctx['total_reduced_eur'])} €).",
        f"Punteggio di conformità: {ctx['conformity_score']}/100.",
    ]
    if ctx["items_adjusted"]:
        parts.append(f"Voci ridotte al limite del bando: {ctx['items_adjusted']}.")
    if ctx["items_blocked"]:
        parts.append(f"Voci respinte o in attesa di documento: {ctx['items_blocked']}.")
    parts.append(f"Impronta del budget (Merkle Root): {ctx['merkle_root'][:18]}…")
    return " ".join(parts)


def render_with_grounding(context: Dict[str, Any], static_text: str, llm: Optional[LLMClient] = None) -> Tuple[str, str]:
    """Restituisce (testo, sorgente) con sorgente 'LLM' solo se il validatore numerico approva."""
    if llm is None:
        return static_text, "TEMPLATE"
    try:
        candidate = llm.complete(SYSTEM_PROMPT, json.dumps(context, ensure_ascii=False))
    except Exception as exc:  # qualunque errore del provider -> fallback deterministico
        logger.warning("LLM renderer non disponibile (%s): uso il template.", type(exc).__name__)
        return static_text, "TEMPLATE"
    result = validate_text_against_payload(candidate, context, EXTRA_ALLOWED)
    if not result.ok:
        logger.warning("Testo LLM rigettato dal validatore numerico: %s", result.problems)
        return static_text, "TEMPLATE"
    return candidate, "LLM"
