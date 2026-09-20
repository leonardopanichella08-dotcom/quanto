"""Comprensione deterministica del testo di un bando: regole numeriche, ambito delle categorie e requisiti.

Nessun LLM: solo pattern e una tassonomia collegata ai 60 criteri. Il principio è che NULLA venga ignorato in silenzio:

- ogni frase che tocca un tema noto diventa un *requisito* (tema, tipo, criteri collegati, frase originale);
- ogni frase che esprime un obbligo/divieto ma non rientra in alcun tema finisce in ``DA_REVISIONARE`` per un umano;
- le regole numeriche estratte sono solo quelle che un pattern riconosce senza ambiguità.
"""
from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Set, Tuple

_NUM = r"(\d{1,3}(?:\.\d{3})*(?:,\d+)?|\d+(?:[.,]\d+)?)"

# ------------------------------------------------------------------ tassonomia (tema, regex, criteri collegati)
TAXONOMY: List[Tuple[str, str, List[int]]] = [
    ("Costo orario del personale", r"costo orario|tariffa oraria", [3, 7]),
    ("Retribuzione, oneri e TFR", r"oneri (?:riflessi|sociali|contributivi|previdenziali)|\bTFR\b|retribuzion\w+", [2, 4, 5]),
    ("Superminimi", r"superminim", [6]),
    ("Impegno del personale (FTE)", r"\bFTE\b|tempo pieno|impegno (?:orario|percentuale)|giornate[- ]uomo|ore lavorate", [8]),
    ("Trasferte e diarie", r"trasferte|diarie", [9]),
    ("Segregazione delle attività", r"segregazione|attività commerciali|\bB2B\b|\bB2G\b", [10]),
    ("Ore straordinarie", r"straordinar", [11]),
    ("Contratti a tempo determinato", r"tempo determinato", [12]),
    ("Collaboratori occasionali", r"occasional|gestione separata", [13]),
    ("Inquadramento e mansionario", r"inquadrament\w+|mansionario|livello contrattuale", [14]),
    ("Buste paga e libro unico", r"bust\w+ paga|libro unico", [15]),
    ("Natura del bene", r"beni strumentali|macchinari|attrezzatur\w+|hardware|software|impianti", [16]),
    ("Ammortamento", r"ammortament", [17, 18]),
    ("Bene nuovo di fabbrica", r"nuov\w+ di fabbrica|beni nuovi|beni usati|rigenerat\w+|\busat\w+", [19]),
    ("Interconnessione e Industria 4.0", r"interconness|industria 4\.0|allegat\w+ [AB]\b", [20]),
    ("Risparmio energetico", r"risparmio energetico|riduzione dei consumi", [21]),
    ("Congruità del prezzo", r"congruit\w+|prezzo di mercato|preventiv\w+|benchmark|best value", [22]),
    ("Installazione, trasporto e collaudo", r"installazion\w+|montaggio|collaudo|trasporto", [23]),
    ("Leasing", r"leasing|locazione finanziaria|lease[- ]back|riscatto", [24]),
    ("Reverse charge", r"reverse charge|inversione contabile", [25]),
    ("Beni immateriali", r"immateriali|licenz\w+", [26]),
    ("Manutenzione", r"manutenzion", [27]),
    ("DNSH", r"\bDNSH\b|danno significativo", [28]),
    ("Uso esclusivo nel progetto", r"uso esclusivo|esclusivamente (?:al|per il|nel) progetto", [29]),
    ("Perizia e certificazioni", r"perizia|asseverat|giurata|certificazion\w+ (?:ex|indipendent)|valutatori? indipendent", [30]),
    ("Consulenze esterne", r"consulen\w+", [31, 33]),
    ("Parti correlate e conflitto di interessi", r"parti correlat|conflitto di interess|imprese collegat", [32]),
    ("Codice ATECO", r"\bATECO\b", [34]),
    ("Subappalto", r"subappalt", [35]),
    ("Spese generali e costi indiretti", r"spese generali|costi indiretti|forfett\w+", [36]),
    ("Spese di comunicazione", r"comunicazion\w+|promozion\w+|pubblicit\w+", [37]),
    ("Fideiussioni e assicurazioni", r"fideiussi\w+|polizz\w+|assicurazion\w+", [38]),
    ("Revisione contabile", r"revisione contabile|revisor\w+", [39]),
    ("Viaggi", r"viagg\w+", [40]),
    ("Sanzioni e contenzioso", r"sanzion\w+|penali|contenzios\w+", [41]),
    ("Locazione", r"locazion\w+|canone|affitto", [42]),
    ("Utenze", r"utenz\w+", [43]),
    ("Spese di rappresentanza", r"rappresentanza", [44]),
    ("DURC e regolarità", r"\bDURC\b|regolarità (?:fiscale|contributiva)", [45]),
    ("Periodo di ammissibilità", r"ammissibil\w+ (?:dal|a partire)|data di (?:avvio|inizio|decorrenza)|termine (?:di|per la) (?:conclusione|rendicontazione)|periodo di ammissibilit", [46]),
    ("Cumulo e doppio finanziamento", r"cumul\w+|doppio finanziamento|medesim\w+ (?:spes\w+|cost\w+)", [47, 48]),
    ("De minimis", r"de minimis", [49]),
    ("CUP", r"\bCUP\b", [50]),
    ("CIG", r"\bCIG\b", [51]),
    ("Pagamenti tracciabili", r"tracciabil\w+|bonifico|contant\w+|assegn\w+", [52]),
    ("IVA", r"\bIVA\b", [53, 54]),
    ("Anticipo e liquidità", r"anticip\w+|acconto|liquidità", [55]),
    ("Variazioni di budget", r"variazion\w+ (?:di|del|tra) (?:budget|piano|voci)|rimodulazion\w+", [56]),
    ("Rendicontazione per SAL", r"\bSAL\b|stato di avanzamento|rendicontazione intermedia|milestone", [57]),
    ("Vincolo di destinazione", r"vincolo di destinazione|mantenimento|stabilità delle operazioni|durabilità", [58]),
    ("Valuta estera", r"valuta estera|tasso di cambio|non euro", [59]),
    # temi che non attivano un controllo del motore ma che un bando definisce sempre: si leggono e si mostrano (criteri = [])
    ("Agevolazione: contributo e finanziamento", r"fondo perduto|contributo (?:in conto|pari|del|massimo)|finanziament\w+ agevolat\w+|agevolazion\w+|intensità di aiuto", []),
    ("Importi massimi e minimi", r"(?:fino\s+a|massimo\s+di|non\s+superior\w+\s+a|importo\s+(?:massimo|minimo|complessivo))[^.\n]{0,40}(?:€|euro)|(?:€|euro)\s?\d", []),
    ("Chi può presentare domanda", r"beneficiar\w+|destinatar\w+|possono\s+(?:presentare|accedere|beneficiare)|soggetti\s+(?:ammessi|proponenti|beneficiari)|requisiti\s+(?:soggettivi|di\s+ammissibilità)", []),
    ("Età e condizione dei richiedenti", r"\b\d{2}\s*(?:e|-|ai|a)\s*\d{2}\s*anni|età\s+(?:compresa|non\s+superiore|inferiore|massima)|under\s?\d{2}|giovan\w+|disoccupat\w+|inoccupat\w+|donn\w+", []),
    ("Territori ammessi", r"Abruzzo|Basilicata|Calabria|Campania|Molise|Puglia|Sardegna|Sicilia|Mezzogiorno|aree\s+(?:interne|del\s+cratere|sismic\w+)|zone\s+economiche\s+speciali|\bZES\b", []),
    ("Domanda, scadenze e procedura", r"presentazione\s+(?:delle|della)\s+domand\w+|domanda\s+(?:di|deve|va|può)|sportello|click\s+day|scadenz\w+|procedura\s+(?:a\s+sportello|valutativa|negoziale)|piattaforma\s+(?:online|telematica)|a\s+partire\s+dal", []),
    ("Erogazione e rendicontazione", r"erogazion\w+|rendicontazion\w+|saldo\b|stato\s+di\s+avanzamento", []),
    ("Obblighi dopo la concessione", r"revoca|decadenza|restituzion\w+|ispezion\w+|obblighi\s+del\s+beneficiario", []),
    ("Attività e settori", r"settor\w+\s+(?:esclus\w+|ammess\w+)|attività\s+(?:esclus\w+|ammess\w+|non\s+ammess\w+)|impres\w+\s+(?:in\s+difficoltà|di\s+nuova\s+costituzione|costituit\w+)", []),
]
_TAX = [(t, re.compile(rx, re.I), c) for t, rx, c in TAXONOMY]

_PROHIBIT = re.compile(r"non\s+(?:sono\s+|è\s+|risultano\s+)?(?:ammissibil\w+|finanziabil\w+|ammess\w+|consentit\w+|rimborsabil\w+)|vietat\w+|esclus\w+|non\s+possono|divieto", re.I)
_OBLIGE = re.compile(r"\bdev\w+\b|obbligator\w+|è\s+richiest\w+|sono\s+richiest\w+|occorre|è\s+necessari\w+|a\s+pena\s+di|obbligo", re.I)
_LIMIT_STRONG = re.compile(r"(?:superior\w+|superare|eccedere|massim\w+|almeno|minim\w+)[^.\n]{0,40}\d|\d[^.\n]{0,40}(?:massim\w+|minim\w+)", re.I)
_LIMIT = re.compile(r"\d+\s*%|\d[\d.,]*\s*(?:€|euro)|massim\w+|non\s+superior\w+|entro\s+(?:il|i|\d)|fino\s+a|almeno|minim\w+", re.I)

CATEGORY_WORDS: Dict[str, str] = {
    r"consulen\w+": "CONSULTING", r"personale|dipendent\w+|lavorator\w+": "PERSONNEL", r"formazione|corsi": "TRAINING",
    r"spese generali|costi indiretti|overhead": "OVERHEAD", r"beni strumentali|macchinari|attrezzatur\w+|impianti|hardware|software": "CAPITAL_ASSETS",
}


def split_sentences(text: str) -> List[str]:
    text = re.sub(r"[ \t]+", " ", text.replace("\r", "\n"))
    parts = re.split(r"(?<=[.;!?])\s+(?=[A-ZÀ-Ý0-9«\"(•-])|\n{1,}", text)
    return [p.strip(" •-\t") for p in parts if len(p.strip()) >= 25]


def extract_requirements(text: str, max_items: int = 150, source_ref: str = "testo caricato") -> List[Dict]:
    """Ogni frase con un tema noto o con un obbligo/divieto diventa un requisito tracciato."""
    out: List[Dict] = []
    seen: Set[str] = set()
    for sentence in split_sentences(text):
        key = sentence.lower()
        if key in seen:
            continue
        seen.add(key)
        topics = [(t, c) for t, rx, c in _TAX if rx.search(sentence)]
        if len(sentence) < 60 and not (_PROHIBIT.search(sentence) or _OBLIGE.search(sentence)):
            continue  # titoli e voci di menu ("Il Mezzogiorno bello e buono"): non sono requisiti
        if _LIMIT_STRONG.search(sentence) and not re.search(r"non\s+(?:sono\s+)?ammissibil", sentence, re.I):
            kind = "LIMITE"          # «non possono superare il 3%» è un limite, non un divieto
        elif _PROHIBIT.search(sentence):
            kind = "DIVIETO"
        elif _OBLIGE.search(sentence):
            kind = "OBBLIGO"
        elif _LIMIT.search(sentence):
            kind = "LIMITE"
        else:
            kind = "INFO"
        if topics:
            criteria = sorted({n for _, cs in topics for n in cs})
            out.append({"topic": " / ".join(t for t, _ in topics[:3]), "kind": kind, "text": sentence[:600], "criteria": criteria,
                        "source_ref": source_ref, "confidence": "PARSING"})
        elif kind in ("DIVIETO", "OBBLIGO"):
            out.append({"topic": "Non classificato", "kind": "DA_REVISIONARE", "text": sentence[:600], "criteria": [],
                        "source_ref": source_ref, "confidence": "PARSING"})
        if len(out) >= max_items:
            break
    return out


# ------------------------------------------------------------------ regole numeriche/strutturali aggiuntive
def _num(text: str) -> float:
    t = text.strip()
    t = t.replace(".", "").replace(",", ".") if "," in t else (t.replace(".", "") if re.fullmatch(r"\d{1,3}(\.\d{3})+", t) else t)
    return float(t)


def _fmt(x: float) -> str:
    return format(x, "f").rstrip("0").rstrip(".") if "." in format(x, "f") else format(x, "f")


def _cap_rules(text: str) -> Dict[str, str]:
    found: Dict[str, str] = {}
    cap = r"(?:non\s+(?:(?:pu[oò]|poss\w+|dev\w+)\s+)?(?:essere\s+)?(?:superior\w+|superare|eccedere|oltre)|massim\w+|max|fino\s+al)"
    m = re.search(r"comunicazion\w*[^.\n\d]{0,60}?" + cap + r"[^.\n\d]{0,30}?" + _NUM + r"\s*%", text, re.I)
    if m:
        found["max_communication_pct"] = _fmt(_num(m.group(1)) / 100)
    m = re.search(r"immateriali\w*[^.\n\d]{0,60}?" + cap + r"[^.\n\d]{0,30}?" + _NUM + r"\s*%", text, re.I)
    if m:
        found["max_immaterial_pct"] = _fmt(_num(m.group(1)) / 100)
    m = re.search(r"revisione\w*[^.\n\d]{0,60}?" + cap + r"[^.\n\d]{0,30}?" + _NUM + r"\s*(?:€|euro)", text, re.I)
    if m:
        found["max_audit_cost_eur"] = _fmt(_num(m.group(1)))
    m = re.search(r"riduzione\s+dei\s+consumi\s+energetici[^.\n\d]{0,30}?almeno\s+(?:il\s+)?" + _NUM + r"\s*%", text, re.I)
    if m:
        found["min_energy_saving_pct"] = _fmt(_num(m.group(1)) / 100)
    m = re.search(r"(?:tasso\s+forfettario|forfait\w*)[^.\n\d]{0,60}?" + _NUM + r"\s*%[^.\n]{0,60}?(costi\s+(?:diretti|di\s+personale)[^.\n]{0,40})", text, re.I)
    if m:
        found["overhead_flat_rate_pct"] = _fmt(_num(m.group(1)) / 100)
        found["overhead_flat_base"] = "PERSONNEL" if "personale" in m.group(2).lower() else "DIRECT_EXCL_SUBCONTRACTING"
    m = re.search(r"(?:vincolo|mantenimento|destinazione)[^.\n]{0,80}?(?:per|di)\s+(\d+)\s+(anni|mesi)", text, re.I)
    if m:
        found["min_durability_months"] = str(int(m.group(1)) * (12 if m.group(2).lower() == "anni" else 1))
    return found


def _flag_rules(text: str) -> Dict[str, str]:
    found: Dict[str, str] = {}
    if re.search(r"nuov\w+\s+di\s+fabbrica|beni\s+(?:strumentali\s+)?nuov\w+", text, re.I):
        found["requires_new_asset"] = "true"
    if re.search(r"interconness", text, re.I):
        found["requires_iot"] = "true"
    if re.search(r"\bDNSH\b|non\s+arrecare(?:\s+un)?\s+danno\s+significativo", text, re.I):
        found["requires_dnsh"] = "true"
    if re.search(r"perizia\s+(?:tecnica\s+)?(?:asseverata|giurata)", text, re.I):
        found["appraisal_threshold_eur"] = "0"
    if re.search(r"prodott\w+\s+(?:in|negli?)\s+(?:Stati\s+membri\s+dell['’])?(?:Unione\s+europea|UE|SEE)", text, re.I):
        found["requires_eu_origin"] = "true"
    if re.search(r"al\s+netto\s+dell['’]?\s*IVA|IVA[^.\n]{0,60}?(?:non\s+(?:è\s+)?ammissibil\w+|esclusa)", text, re.I):
        found["vat_never_eligible"] = "true"
    if re.search(r"\bSAL\b|stato\s+di\s+avanzamento|rendicontazione\s+intermedia", text, re.I):
        found["requires_milestones"] = "true"
    if re.search(r"subappalt\w+[^.\n]{0,60}?(?:non\s+(?:è\s+)?ammess\w+|vietat\w+|non\s+ammissibil\w+)", text, re.I):
        found["subcontracting_allowed"] = "false"
    elif re.search(r"subappalt\w+[^.\n]{0,60}?(?:ammess\w+|ammissibil\w+|consentit\w+)", text, re.I):
        found["subcontracting_allowed"] = "true"
    if re.search(r"fideiussi\w+[^.\n]{0,80}?non\s+ammissibil\w+", text, re.I):
        found["guarantee_costs_eligible"] = "false"
    elif re.search(r"fideiussi\w+[^.\n]{0,80}?(?:ammissibil\w+|ammess\w+)", text, re.I):
        found["guarantee_costs_eligible"] = "true"
    if re.search(r"terren\w+|fabbricat\w+|immobil\w+", text, re.I) and re.search(r"(?:terren\w+|fabbricat\w+|immobil\w+)[^.\n]{0,80}?(?:non\s+ammissibil\w+|esclus\w+)|(?:non\s+ammissibil\w+|esclus\w+)[^.\n]{0,80}?(?:terren\w+|fabbricat\w+|immobil\w+)", text, re.I):
        found["excluded_asset_natures"] = json.dumps(["REAL_ESTATE"])
    return found


def category_scope(text: str) -> Optional[List[str]]:
    """Categorie ammesse dedotte dal testo: 'solo/esclusivamente ...' -> elenco positivo; 'non ammissibili ...' -> tutte meno le escluse."""
    positives: Set[str] = set()
    negatives: Set[str] = set()
    for sentence in split_sentences(text):
        cats = {c for rx, c in CATEGORY_WORDS.items() if re.search(rx, sentence, re.I)}
        if not cats:
            continue
        if re.search(r"(?:ammissibil\w+|ammess\w+|finanziabil\w+)\s+(?:esclusivamente|solo|unicamente)|(?:esclusivamente|solo|unicamente)\s+(?:le\s+)?spese", sentence, re.I):
            positives |= cats
        elif re.search(r"non\s+(?:sono\s+)?(?:ammissibil\w+|finanziabil\w+|ammess\w+)|escluse?\b", sentence, re.I):
            negatives |= cats
    universe = {"PERSONNEL", "CAPITAL_ASSETS", "CONSULTING", "OVERHEAD", "TRAINING"}
    if positives:
        result = positives - negatives
    elif negatives:
        result = universe - negatives
    else:
        return None
    return sorted(result) if result and result != universe else None


def extract_more_rules(text: str) -> Dict[str, str]:
    rules = {**_flag_rules(text), **_cap_rules(text)}
    scope = category_scope(text)
    if scope is not None:
        rules["eligible_categories"] = json.dumps(scope)
    return rules


# ------------------------------------------------------------------ riferimenti normativi citati nel testo
_LEGAL = re.compile(
    r"(Decreto[- ]Legge|Decreto\s+Legislativo|Decreto\s+Ministeriale|Decreto\s+Direttoriale|Decreto\s+Interministeriale|DPCM|D\.\s?L\.|D\.\s?Lgs\.|Legge|Regolamento\s+\((?:UE|CE)\)|Circolare|Delibera)"
    r"\s+(?:n\.?\s*)?(\d{1,4}(?:/\d{2,4})?)(?:\s*(?:del|dell['’]|,)\s*(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}|\d{1,2}\s+[a-zà-ù]+\s+\d{4}))?", re.I)


def extract_legal_refs(text: str, limit: int = 40) -> List[str]:
    """Atti citati nel testo (decreti, leggi, regolamenti UE…), i più citati per primi."""
    counts: Dict[str, int] = {}
    for m in _LEGAL.finditer(text):
        kind = re.sub(r"\s+", " ", m.group(1)).strip()
        if not m.group(3) and "/" not in m.group(2):
            continue  # "legge n. 27" senza data né anno: ambiguo, non è un riferimento utilizzabile
        ref = f"{kind[:1].upper() + kind[1:]} n. {m.group(2)}" + (f" del {m.group(3)}" if m.group(3) else "")
        counts[ref] = counts.get(ref, 0) + 1
    return [r for r, _ in sorted(counts.items(), key=lambda kv: -kv[1])][:limit]
