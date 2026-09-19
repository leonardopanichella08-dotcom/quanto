"""Catalogo dei 60 criteri del Deterministic Engine (Modulo 11 del documento FKOS v2) e loro applicabilità.

Ogni criterio è implementato come funzione autonoma in ``deterministic_engine.py``. Se il dato necessario
(sulla riga o nelle regole del bando) manca, il criterio non viene eseguito e risulta "non valutato": non è mai
contato come superato.
"""
from __future__ import annotations

from typing import Dict, Set

from app.models.schemas import AssetNature, CostCategory, CostItemInput, ExpenseSubtype

CRITERIA_TITLES: Dict[int, str] = {
    1: "Inquadramento CCNL e verifica della tabella ministeriale aggiornata",
    2: "Calcolo della Retribuzione Annua Lorda, esclusa ogni stima probabilistica",
    3: "Costo orario effettivo secondo il divisore contrattuale",
    4: "Isolamento e ricalcolo del TFR sul montante retributivo",
    5: "Oneri riflessi e previdenziali puntuali per inquadramento",
    6: "Esclusione dei superminimi non assorbibili unilaterali",
    7: "Tetto massimo di costo orario previsto dal bando",
    8: "Pro-rata FTE/durata e somma FTE <= 100% per lavoratore",
    9: "Tracciabilità di trasferte e diarie",
    10: "Segregazione contabile delle attività B2B e B2G",
    11: "Blocco delle ore straordinarie non previste dal regolamento",
    12: "Contratti a tempo determinato con maggiorazione contributiva",
    13: "Ammissibilità dei collaboratori occasionali (limite di reddito)",
    14: "Congruenza tra livello contrattuale e complessità dell'attività",
    15: "Cross-check tra busta paga reale e retribuzione dichiarata",
    16: "Natura della voce e corretto incasellamento contabile",
    17: "Aliquota d'ammortamento fiscale tabellare",
    18: "Ammortamento pro-rata temporis sui mesi di durata del progetto",
    19: "Requisito di \"nuovo di fabbrica\"",
    20: "Requisiti di interconnessione IoT (4.0/5.0)",
    21: "Risparmio energetico target rispetto alla baseline",
    22: "Congruenza del prezzo di acquisto rispetto ai benchmark (Fonte B)",
    23: "Separazione dei costi di installazione dal valore capitale del bene",
    24: "Leasing: esclusione della quota interessi",
    25: "Cumulo delle inversioni contabili (reverse charge)",
    26: "Beni immateriali e quota massima",
    27: "Manutenzione ordinaria vs straordinaria",
    28: "Principio DNSH (Do No Significant Harm)",
    29: "Uso esclusivo del bene nel progetto",
    30: "Perizia tecnica giurata per beni sopra soglia",
    31: "Massimale percentuale sulle consulenze rispetto al budget totale",
    32: "Indipendenza del fornitore (anti-parti correlate)",
    33: "Normalizzazione della tariffa di consulenza sui benchmark",
    34: "Congruenza del codice ATECO del fornitore",
    35: "Esclusione dei subappalti non autorizzati",
    36: "Spese generali e indirette forfettarie",
    37: "Spese di comunicazione entro i tetti previsti",
    38: "Costi di fideiussione e assicurazione se obbligatori",
    39: "Costi di revisione contabile indipendente entro i limiti",
    40: "Spese di viaggio dei consulenti, incluse o scorporate dall'onorario",
    41: "Esclusione di sanzioni, penali e contenziosi legali",
    42: "Canoni di locazione in proporzione a metri quadri e mesi di attività",
    43: "Utenze imputate con criteri di ripartizione oggettivi",
    44: "Esclusione delle spese di rappresentanza non finalizzate al progetto",
    45: "Regolarità fiscale e contributiva del fornitore (DURC)",
    46: "Data di decorrenza dell'ammissibilità della spesa",
    47: "Non cumulabilità dei contributi (double funding)",
    48: "Cumulo con crediti d'imposta e intensità di aiuto massima (GBER)",
    49: "Plafond de minimis residuo nel triennio mobile",
    50: "Presenza e tracciabilità del codice CUP",
    51: "Presenza e tracciabilità del codice CIG",
    52: "Metodi di pagamento ammissibili (blocco contanti/assegni)",
    53: "Indetraibilità IVA come costo ammissibile",
    54: "Esclusione dell'IVA recuperabile",
    55: "Sostenibilità del cash-flow tra spesa e rimborso",
    56: "Variazione di budget tollerabile tra capitoli",
    57: "Vincoli di rendicontazione intermedia per milestone/SAL",
    58: "Clausola di durabilità post-chiusura del progetto",
    59: "Discrepanze di cambio per bandi internazionali",
    60: "Coerenza globale del budget rispetto ai criteri precedenti",
}

BUDGET_LEVEL: Set[int] = {48, 49, 55, 56, 60}

_PERSONNEL = set(range(1, 16))
_GENERAL = {46, 47, 50, 52, 57}
_NON_PERSONNEL_COMMON = {16, 45, 51, 53, 54, 59}


def applicable_criteria(item: CostItemInput) -> Set[int]:
    """Criteri item-level pertinenti alla riga (per calcolare i \"non valutati\")."""
    cat, sub = item.category, item.expense_subtype
    crit = set(_GENERAL)
    if cat == CostCategory.PERSONNEL:
        return crit | _PERSONNEL
    crit |= _NON_PERSONNEL_COMMON
    if cat == CostCategory.CAPITAL_ASSETS:
        crit |= {17, 18, 19, 20, 21, 22, 23, 24, 25, 28, 29, 30, 58}
        if item.asset_nature in (AssetNature.SOFTWARE, AssetNature.IMMATERIAL):
            crit.add(26)
    elif cat == CostCategory.CONSULTING:
        crit |= {31, 32, 33, 34, 35, 40}
    elif cat == CostCategory.OVERHEAD:
        crit.add(36)
    subtype_map = {
        ExpenseSubtype.COMMUNICATION: {37}, ExpenseSubtype.GUARANTEE: {38}, ExpenseSubtype.AUDIT: {39},
        ExpenseSubtype.PENALTY: {41}, ExpenseSubtype.LEGAL_DISPUTE: {41}, ExpenseSubtype.RENT: {42},
        ExpenseSubtype.UTILITIES: {43}, ExpenseSubtype.REPRESENTATION: {44},
        ExpenseSubtype.MAINTENANCE_ORDINARY: {27}, ExpenseSubtype.MAINTENANCE_EXTRAORDINARY: {27},
    }
    if sub:
        crit |= subtype_map.get(sub, set())
    return crit
