"""Come si accede a un'agevolazione: non tutti i bandi chiedono un progetto.

Un bando di ricerca o di investimento finanzia un progetto nuovo e i suoi costi incrementali. Ma molte misure funzionano in altro modo, e il budget che serve è diverso:

| modalità | esempio | su cosa si calcola | le spese correnti dell'azienda sono una base valida? |
| progetto o investimento | ricerca e sviluppo, Smart&Start, bandi regionali per l'innovazione | le spese nuove del progetto | solo in parte (spese generali a forfait, personale realmente dedicato) |
| credito d'imposta automatico | Transizione 5.0, iperammortamento | gli acquisti qualificati dell'anno, senza domanda né graduatoria | no: contano i beni acquistati |
| garanzia e liquidità | Fondo di garanzia PMI | il finanziamento bancario da garantire | sì: serve il fabbisogno di cassa, non un piano |
| occupazione | incentivi alle assunzioni | le persone assunte e i loro requisiti | no: contano le assunzioni |
| spese commerciali e internazionalizzazione | SIMEST: fiere, e-commerce, export | le spese commerciali del programma, anche ricorrenti | sì, se sostenute per il programma e dopo la domanda |
| ristoro | contributi per crisi, caro energia | i dati storici (ricavi, costi) | sì: si calcola sui bilanci |

La modalità si ricava dal tipo di aiuto del bando e dalle frasi del suo testo; ogni modalità porta le frasi come prova. Senza testo e senza tipo di aiuto non si indovina.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.core.expense_types import norm

MODES: Dict[str, Dict[str, Any]] = {
    "CREDITO_AUTOMATICO": {"label": "Credito d'imposta o beneficio fiscale automatico", "needs_project": False, "ordinary_costs_ok": False,
                           "base": "gli acquisti qualificati dell'anno (beni, investimenti): non c'è una domanda da approvare né un budget, serve la documentazione dei beni",
                           "example": "Un'azienda compra un macchinario interconnesso: il credito spetta per quell'acquisto, senza scrivere un progetto.",
                           "benefit_types": ["IPERAMMORTAMENTO", "CREDITO_D_IMPOSTA"],
                           "words": ["CREDITO D IMPOSTA", "CREDITO DIMPOSTA", "IPERAMMORTAMENTO", "CASSETTO FISCALE", "COMPENSAZIONE IN F24", "COMPENSAZIONE TRAMITE F24", "SENZA GRADUATORIA", "NON E PREVISTA ALCUNA GRADUATORIA",
                                     "NON E NECESSARIA LA PRESENTAZIONE DI DOMANDA"]},
    "GARANZIA_LIQUIDITA": {"label": "Garanzia pubblica e liquidità", "needs_project": False, "ordinary_costs_ok": True,
                           "base": "il finanziamento bancario da garantire (importo, durata): serve il fabbisogno di cassa, non un elenco di spese",
                           "example": "Un'azienda chiede 200.000 € di fido per il capitale circolante: la garanzia copre una parte, senza progetto.",
                           "benefit_types": ["GARANZIA_PUBBLICA"],
                           "words": ["GARANZIA PUBBLICA", "GARANZIA SUI FINANZIAMENTI", "LIQUIDITA", "CAPITALE CIRCOLANTE", "FABBISOGNO DI CASSA", "CIRCOLANTE"]},
    "OCCUPAZIONE": {"label": "Incentivi all'occupazione", "needs_project": False, "ordinary_costs_ok": False,
                    "base": "le persone assunte, con contratto e requisiti del lavoratore (età, sesso, condizione), e la regolarità contributiva (DURC)",
                    "example": "Un'azienda assume una persona under 30 a tempo indeterminato: il contributo dipende dal contratto, non da un progetto.",
                    "benefit_types": [],
                    "words": ["ASSUNZION", "ESONERO CONTRIBUTIVO", "SGRAVIO CONTRIBUTIVO", "INCENTIVO ALL OCCUPAZIONE", "INCENTIVI ALL OCCUPAZIONE", "NUOVA OCCUPAZIONE", "BONUS ASSUNZION"]},
    "SPESE_CORRENTI": {"label": "Spese commerciali e di internazionalizzazione", "needs_project": False, "ordinary_costs_ok": True,
                       "base": "le spese commerciali e di sviluppo del programma, anche ricorrenti (fiere, e-commerce, consulenze per l'export), se sostenute per il programma e dopo la domanda",
                       "example": "Un'azienda partecipa a due fiere all'estero e apre un negozio online: sono costi operativi, e il bando ne rimborsa una parte.",
                       "benefit_types": [],
                       "words": ["FIERE", "E-COMMERCE", "COMMERCIO ELETTRONICO", "TEMPORARY EXPORT", "INTERNAZIONALIZZAZION", "MERCATI ESTERI", "PAESI ESTERI", "SPESE COMMERCIALI", "PROMOZIONE ALL ESTERO"]},
    "RISTORO": {"label": "Ristoro e resilienza (calcolato sui dati storici)", "needs_project": False, "ordinary_costs_ok": True,
                "base": "i dati storici di bilancio (ricavi, costi) o il calo di fatturato: nessun piano di investimenti",
                "example": "Un contributo per il caro energia si calcola sulla differenza tra i costi dell'energia di due anni.",
                "benefit_types": [],
                "words": ["RISTORO", "CALO DEL FATTURATO", "PERDITA DI FATTURATO", "CARO ENERGIA", "CARO-ENERGIA", "EMERGENZA", "RESILIENZA DELLE IMPRESE", "CONTINUITA AZIENDALE"]},
    "PROGETTO_INVESTIMENTO": {"label": "Progetto o investimento", "needs_project": True, "ordinary_costs_ok": False,
                              "base": "le spese nuove del progetto (acquisti, assunzioni, sviluppo); le spese correnti entrano solo per forma (spese generali a forfait, personale realmente dedicato con timesheet)",
                              "example": "Un'azienda sviluppa un nuovo prodotto in 12 mesi: i costi del progetto sono finanziati, non quelli dell'attività di sempre.",
                              "benefit_types": ["SOVVENZIONE", "CONTRIBUTO_IN_CONTO_CAPITALE", "CONTRIBUTO_E_FINANZIAMENTO_MISTO", "CONTRIBUTO_IN_CONTO_INTERESSI", "FINANZIAMENTO_A_TASSO_ZERO"],
                              "words": ["PROGETTO", "PIANO DI INVESTIMENT", "PROGRAMMA DI INVESTIMENT", "SVILUPPO SPERIMENTALE", "RICERCA INDUSTRIALE", "MILESTONE", "WORK PACKAGE", "ACQUISTO DI BENI STRUMENTALI", "INVESTIMENTI PRODUTTIVI"]},
}
_PATTERNS = {c: [re.compile(r"(?<![A-Z0-9])" + re.escape(w)) for w in spec["words"]] for c, spec in MODES.items()}
_MAX_SENTENCE = 400
_PRIORITY = ["CREDITO_AUTOMATICO", "GARANZIA_LIQUIDITA", "OCCUPAZIONE", "SPESE_CORRENTI", "RISTORO", "PROGETTO_INVESTIMENTO"]       # a parità di prove, la modalità più specifica


def _sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.;:])\s+|\n+", text or "") if s.strip()]


def classify(benefit_type: Optional[str], texts: List[str]) -> Dict[str, Any]:
    """Le modalità di accesso di un bando: la principale, e tutte quelle che il tipo di aiuto o il testo sostengono, ognuna con le frasi come prova."""
    found: Dict[str, List[str]] = {}
    for t in texts:
        for raw in _sentences(t):
            if len(raw) > _MAX_SENTENCE:
                continue
            n = norm(raw)
            for code, pats in _PATTERNS.items():
                if any(p.search(n) for p in pats):
                    found.setdefault(code, []).append(raw)
    typed = {c for c, spec in MODES.items() if benefit_type in spec["benefit_types"]}
    scores: Dict[str, float] = {}
    for code in MODES:
        mentions = len(found.get(code, []))
        score = mentions + (5 if code in typed else 0)           # il tipo di aiuto dichiarato pesa più di qualche menzione
        if code == "PROGETTO_INVESTIMENTO":
            score *= 0.6                                         # «progetto» è una parola comune: non deve battere una modalità specifica con prove simili
        if score > 0:
            scores[code] = score
    ordered = sorted(scores, key=lambda c: (-scores[c], _PRIORITY.index(c)))
    modes = [{"code": c, "label": MODES[c]["label"], "needs_project": MODES[c]["needs_project"], "ordinary_costs_ok": MODES[c]["ordinary_costs_ok"], "base": MODES[c]["base"], "example": MODES[c]["example"],
              "by_benefit_type": c in typed, "mentions": len(found.get(c, [])), "evidence": list(dict.fromkeys(found.get(c, [])))[:2]} for c in ordered]
    return {"primary": modes[0]["code"] if modes else None, "modes": modes}


def describe(code: Optional[str]) -> Optional[Dict[str, Any]]:
    spec = MODES.get(code or "")
    return None if not spec else {"code": code, "label": spec["label"], "needs_project": spec["needs_project"], "ordinary_costs_ok": spec["ordinary_costs_ok"], "base": spec["base"], "example": spec["example"]}
