"""Che tipo di progetto finanzia un bando.

Un bando non finanzia «costi»: finanzia progetti di un certo tipo (digitalizzazione, ricerca e sviluppo, efficienza energetica, export, assunzioni…). Per proporre a un'azienda il
progetto giusto bisogna prima sapere cosa ogni bando finanzia. Qui il testo del bando (nome, scheda, requisiti letti) viene confrontato con un elenco di tipologie di progetto: una
tipologia è attribuita a un bando solo se una frase del suo testo la nomina, e quella frase è la prova che si mostra. Un bando senza testo letto non ha tipologie: non si indovinano.

Nessun giudizio sull'azienda: è la descrizione del bando. Le idee di progetto per l'azienda stanno in ``project_ideas``.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from app.core.expense_types import norm

# codice -> (etichetta, parole che nel testo di un bando la nominano)
TYPES: Dict[str, Dict[str, Any]] = {
    "DIGITALIZZAZIONE": {"label": "Digitalizzazione e trasformazione digitale", "words": ["DIGITALIZZAZION", "TRASFORMAZIONE DIGITALE", "TRANSIZIONE DIGITALE", "INDUSTRIA 4.0", "INDUSTRIA 4", "CYBERSECURITY",
                                                                                         "SICUREZZA INFORMATICA", "E-COMMERCE", "COMMERCIO ELETTRONICO", "SERVIZI CLOUD", "SOFTWARE GESTIONALE", "INTELLIGENZA ARTIFICIALE"]},
    "RICERCA_SVILUPPO": {"label": "Ricerca, sviluppo e innovazione", "words": ["RICERCA INDUSTRIALE", "SVILUPPO SPERIMENTALE", "RICERCA E SVILUPPO", "R&S", "INNOVAZIONE DI PRODOTTO", "INNOVAZIONE DI PROCESSO",
                                                                             "PROTOTIP", "BREVETT", "TRASFERIMENTO TECNOLOGICO", "PROGETTI DI INNOVAZIONE", "VALIDAZIONE TECNOLOGICA"]},
    "EFFICIENZA_ENERGETICA": {"label": "Efficienza energetica e rinnovabili", "words": ["EFFICIENZA ENERGETICA", "EFFICIENTAMENTO ENERGETICO", "FOTOVOLTAIC", "ENERGIE RINNOVABILI", "FONTI RINNOVABILI", "AUTOCONSUMO",
                                                                                         "TRANSIZIONE ECOLOGICA", "TRANSIZIONE ENERGETICA", "DECARBONIZZAZIONE", "RISPARMIO ENERGETICO", "TRANSIZIONE 5.0"]},
    "INTERNAZIONALIZZAZIONE": {"label": "Internazionalizzazione ed export", "words": ["INTERNAZIONALIZZAZION", "EXPORT", "MERCATI ESTERI", "PAESI ESTERI", "FIERE INTERNAZIONALI", "TEMPORARY EXPORT", "COMMERCIO ESTERO",
                                                                                      "PROMOZIONE ALL ESTERO", "ESPORTAZION"]},
    "OCCUPAZIONE": {"label": "Occupazione e assunzioni", "words": ["ASSUNZION", "NUOVA OCCUPAZIONE", "INCENTIVI ALL OCCUPAZIONE", "APPRENDISTATO", "INSERIMENTO LAVORATIV", "STABILIZZAZION", "OCCUPAZIONE GIOVANILE"]},
    "FORMAZIONE": {"label": "Formazione e competenze", "words": ["FORMAZIONE", "COMPETENZE", "RESKILLING", "UPSKILLING", "PERCORSI FORMATIVI", "PIANI FORMATIVI"]},
    "INVESTIMENTI_PRODUTTIVI": {"label": "Macchinari, impianti e beni strumentali", "words": ["MACCHINARI", "IMPIANTI PRODUTTIVI", "ATTREZZATURE", "BENI STRUMENTALI", "INVESTIMENTI PRODUTTIVI", "NUOVI IMPIANTI",
                                                                                                "BENI MATERIALI", "BENI IMMATERIALI"]},
    "NUOVE_IMPRESE": {"label": "Nuove imprese e start-up", "words": ["START-UP", "STARTUP", "NUOVE IMPRESE", "AUTOIMPRENDITORIALIT", "NEOCOSTITUIT", "IMPRESA GIOVANILE", "IMPRENDITORIA FEMMINILE"]},
    "CERTIFICAZIONI": {"label": "Certificazioni e qualità", "words": ["CERTIFICAZION", "ISO 9001", "ISO 14001", "ISO 27001", "SISTEMI DI GESTIONE DELLA QUALITA", "MARCHIO DI QUALITA"]},
    "MARKETING": {"label": "Marketing, comunicazione e promozione", "words": ["MARKETING", "COMUNICAZIONE", "PROMOZIONE COMMERCIALE", "BRAND", "CAMPAGNE PUBBLICITARIE", "SITO WEB"]},
    "AMBIENTE_SICUREZZA": {"label": "Ambiente, economia circolare e sicurezza", "words": ["ECONOMIA CIRCOLARE", "GESTIONE DEI RIFIUTI", "SICUREZZA SUL LAVORO", "SOSTENIBILITA AMBIENTALE", "RIDUZIONE DELL IMPATTO AMBIENTALE", "RICICLO"]},
    "ACCESSO_CREDITO": {"label": "Accesso al credito (garanzie e finanziamenti agevolati)", "words": ["GARANZIA PUBBLICA", "GARANZIA SUI FINANZIAMENTI", "FINANZIAMENTO AGEVOLATO", "TASSO ZERO", "CONTRIBUTO IN CONTO INTERESSI",
                                                                                                          "ACCESSO AL CREDITO", "MICROCREDITO"]},
    "RADICAMENTO_TERRITORIO": {"label": "Sviluppo del territorio e riqualificazione", "words": ["RIQUALIFICAZIONE", "SVILUPPO LOCALE", "ZONE ECONOMICHE SPECIALI", "AREE DI CRISI", "COESIONE TERRITORIALE", "RIGENERAZIONE URBANA"]},
}
_MAX_SENTENCE = 400
_PATTERNS = {c: [re.compile(r"(?<![A-Z0-9])" + re.escape(w)) for w in spec["words"]] for c, spec in TYPES.items()}       # «formazione» non si trova dentro «trasformazione»


def _sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.;:])\s+|\n+", text or "") if s.strip()]


def for_texts(texts: List[str], limit: int = 2) -> List[Dict[str, Any]]:
    """Le tipologie di progetto nominate nei testi, dalla più citata, con le frasi che le nominano come prova (al massimo ``limit``)."""
    found: Dict[str, List[str]] = {}
    for t in texts:
        for raw in _sentences(t):
            if len(raw) > _MAX_SENTENCE:                      # un elenco o un impaginato rotto non dice di cosa si parla
                continue
            n = norm(raw)
            for code, spec in TYPES.items():
                if any(p.search(n) for p in _PATTERNS[code]):
                    found.setdefault(code, []).append(raw)
    out = [{"code": c, "label": TYPES[c]["label"], "mentions": len(ev), "evidence": list(dict.fromkeys(ev))[:limit]} for c, ev in found.items()]
    return sorted(out, key=lambda x: (-x["mentions"], x["code"]))


def label(code: str) -> str:
    return TYPES.get(code, {}).get("label", code)


def catalog() -> List[Dict[str, str]]:
    return [{"code": c, "label": s["label"]} for c, s in TYPES.items()]
