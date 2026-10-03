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
    ("Spese di comunicazione", r"(?:spese|costi|attività|piano|campagn\w+)\s+(?:di|della|per la)\s+(?:comunicazione|promozione|pubblicità)|pubblicit\w+|promozion\w+\s+(?:del|dell|dei|delle)\s+(?:progett\w+|iniziativ\w+|prodott\w+)", [37]),
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
    ("Età e condizione dei richiedenti", r"\b\d{2}\s*(?:e|-|ai|a)\s*\d{2}\s*anni|\b(?:tra|dai|di)\s+\d{2}\s+(?:e|ai|a)\s+\d{2}\s+anni|età\s+(?:compresa|non\s+superiore|inferiore|massima|minima)|under\s?\d{2}|(?:disoccupat\w+|inoccupat\w+|inattiv\w+)|\bNEET\b", []),
    ("Territori ammessi", r"Abruzzo|Basilicata|Calabria|Campania|Molise|Puglia|Sardegna|Sicilia|Mezzogiorno|aree\s+(?:interne|del\s+cratere|sismic\w+)|zone\s+economiche\s+speciali|\bZES\b", []),
    ("Domanda, scadenze e procedura", r"presentazione\s+(?:delle|della)\s+domand\w+|domanda\s+(?:di|deve|va|può)|sportello|click\s+day|scadenz\w+|procedura\s+(?:a\s+sportello|valutativa|negoziale)|piattaforma\s+(?:online|telematica)|a\s+partire\s+dal", []),
    ("Erogazione e rendicontazione", r"erogazion\w+|rendicontazion\w+|saldo\b|stato\s+di\s+avanzamento", []),
    ("Obblighi dopo la concessione", r"revoca|decadenza|restituzion\w+|ispezion\w+|obblighi\s+del\s+beneficiario", []),
    ("Attività e settori", r"settor\w+\s+(?:esclus\w+|ammess\w+)|attività\s+(?:esclus\w+|ammess\w+|non\s+ammess\w+)|impres\w+\s+(?:in\s+difficoltà|di\s+nuova\s+costituzione|costituit\w+)", []),
]
# Documenti europei e programmi (Erasmus+, Horizon, FSE+…) sono spesso in inglese: stessi temi e stessi criteri collegati
TAXONOMY_EN: List[Tuple[str, str, List[int]]] = [
    ("Costo orario del personale", r"staff costs?|personnel costs?|hourly rate|daily rate|per[- ]day|unit costs?", [3, 7]),
    ("Consulenze esterne", r"consultan\w+|external expert\w*|external services", [31, 33]),
    ("Subappalto", r"subcontract\w+", [35]),
    ("Spese generali e costi indiretti", r"indirect costs?|overheads?|flat[- ]rate", [36]),
    ("Viaggi", r"\btravel\b|subsistence", [40]),
    ("IVA", r"\bVAT\b|value added tax", [53, 54]),
    ("Natura del bene", r"equipment|purchase of goods|depreciation", [16]),
    ("Cumulo e doppio finanziamento", r"double funding|cumulat\w+|other (?:EU|public) funding|combin\w+ with other", [47, 48]),
    ("Pagamenti tracciabili", r"bank transfer|cash payment", [52]),
    ("Periodo di ammissibilità", r"eligible period|eligibility period|costs? incurred (?:before|after|between)|start date|end date of the project", [46]),
    ("Rendicontazione per SAL", r"interim report|progress report|milestone", [57]),
    ("Agevolazione: contributo e finanziamento", r"\bgrants?\b|lump[- ]sum|co-?financ\w+|funding rate|EU contribution|maximum (?:amount|contribution|grant)|financial support", []),
    ("Importi massimi e minimi", r"(?:up to|maximum(?: of)?|max\.?|minimum(?: of)?|at least|not exceed(?:ing)?|no more than)[^.\n]{0,40}(?:EUR|€)|(?:EUR|€)\s?\d", []),
    ("Chi può presentare domanda", r"\bapplicants?\b|eligible (?:organisations?|entities|participants|applicants|countries)|who can (?:apply|participate)|legal (?:entit\w+|persons?)|beneficiar\w+|participating organisations?", []),
    ("Età e condizione dei richiedenti", r"aged? (?:between )?\d{2}|between (?:the ages of )?\d{2} and \d{2}|under \d{2}|young people (?:aged|between)|fewer opportunities|\bNEET\b", []),
    ("Territori ammessi", r"programme countries|third countries|member states|eligible countries|partner countries", []),
    ("Domanda, scadenze e procedura", r"deadline|call for proposals|application form|submit(?:ted)? (?:the|an|your)? ?application|closing date|opening date|how to apply|selection procedure|evaluation", []),
    ("Erogazione e rendicontazione", r"pre-?financing|final payment|payment of the (?:grant|balance)|balance|final report|reporting", []),
    ("Obblighi dopo la concessione", r"recover\w+|audits?\b|on-the-spot|termination|irregularit\w+|sanction\w*|monitoring", []),
    ("Durata e tempi", r"duration (?:of|is)|project duration|(?:between|from)\s+\d+\s+(?:and|to)\s+\d+\s+(?:days|months|years)|\d+\s+(?:months|years)\b", []),
    ("Partner e partecipanti", r"at least (?:one|two|three|\d+) (?:partner|organi[sz]ation|participant|country|countries)|minimum (?:number )?of (?:participants|partners)|group leader|participants? (?:per|from) each", []),
]
_TAX = [(t, re.compile(rx, re.I), c) for t, rx, c in TAXONOMY + TAXONOMY_EN]

_PROHIBIT = re.compile(r"non\s+(?:sono\s+|è\s+|risultano\s+)?(?:ammissibil\w+|finanziabil\w+|ammess\w+|consentit\w+|rimborsabil\w+)|vietat\w+|esclus\w+|non\s+possono|divieto"
                       r"|not\s+(?:be\s+)?(?:eligible|allowed|permitted|accepted|funded|financed)|ineligible|cannot\b|can not\b|may not\b|must not\b|shall not\b|prohibited|excluded?\b", re.I)
_OBLIGE = re.compile(r"\bdev\w+\b|obbligator\w+|è\s+richiest\w+|sono\s+richiest\w+|occorre|è\s+necessari\w+|a\s+pena\s+di|obbligo"
                     r"|\bmust\b|\bshall\b|(?:is|are)\s+required|mandatory|need(?:s)? to|have to|obligat\w+|are expected to|has to", re.I)
_LIMIT_STRONG = re.compile(r"(?:superior\w+|superare|eccedere|massim\w+|almeno|minim\w+)[^.\n]{0,40}\d|\d[^.\n]{0,40}(?:massim\w+|minim\w+)"
                           r"|(?:maximum|minimum|at least|at most|up to|no more than|not exceed\w*|not more than|not less than)[^.\n]{0,40}\d|\d[^.\n]{0,40}(?:maximum|minimum)", re.I)
_LIMIT = re.compile(r"\d+\s*%|\d[\d.,]*\s*(?:€|euro|EUR)|massim\w+|non\s+superior\w+|entro\s+(?:il|i|\d)|fino\s+a|almeno|minim\w+"
                    r"|maximum|minimum|at least|up to|\d+\s+(?:days|months|years|giorni|mesi|anni)\b", re.I)

CATEGORY_WORDS: Dict[str, str] = {
    r"consulen\w+": "CONSULTING", r"personale|dipendent\w+|lavorator\w+": "PERSONNEL", r"formazione|corsi": "TRAINING",
    r"spese generali|costi indiretti|overhead": "OVERHEAD", r"beni strumentali|macchinari|attrezzatur\w+|impianti|hardware|software": "CAPITAL_ASSETS",
}


_ART_HEAD = re.compile(r"^(?:Art(?:icolo|\.)?|Article)\s*\d+", re.I)
_HEAD_BLOCK = re.compile(r"^(?:PARTE|TITOLO|CAPO|SEZIONE|ALLEGATO|PART|CHAPTER|SECTION|ANNEX)\s+(?:[IVXLC]+|\d+|[A-Z])\b", re.I)
_HEAD_NUM = re.compile(r"^(?:\d{1,2}(?:\.\d{1,2}){0,2}|[A-Z](?:\.\d{1,2})?)\.?\s+[A-ZÀ-Ý]")
_CITATION = re.compile(r"^\d{1,4}/\d{2,4}\s+del\s", re.I)       # «1407/2013 del 18 dicembre 2013: …»: un atto citato, non un limite


def _mark_sections(text: str) -> str:
    """Le intestazioni (Art. 5, PARTE II, 5.1 Spese ammissibili, D.2 …) diventano righe-segnaposto così ogni requisito sa in che sezione sta.
    Una riga con un obbligo, un divieto o un limite non è mai un'intestazione, anche se corta: è un requisito."""
    out = []
    for line in text.split("\n"):
        t = line.strip()
        is_head = (3 <= len(t) <= 110 and not t.endswith((":", ";", ",")) and not (_OBLIGE.search(t) or _PROHIBIT.search(t) or _LIMIT.search(t))
                   and (_ART_HEAD.match(t) or _HEAD_BLOCK.match(t) or (_HEAD_NUM.match(t) and not t.endswith("."))))
        label = re.sub(r"[§\s]+", " ", t)[:70]
        out.append(f"\n\n§§{label}§§\n\n" if is_head else line)
    return "\n".join(out)


def reflow(text: str) -> str:
    """Ricompone le frasi spezzate dall'estrazione dei PDF: «…dei\ngiovani con esigenze» → una riga; le divisioni con trattino tornano parole intere."""
    text = text.replace("\r", "\n")
    text = re.sub(r"(?<=[a-zà-ù])-\n(?=[a-zà-ù])", "", text)                      # parola spezzata col trattino
    return re.sub(r"(?<![.;:!?\n])[ \t]*\n(?!\n)(?=[a-zà-ù(«\"0-9])", " ", text)      # riga che continua la precedente


def split_sentences(text: str) -> List[str]:
    text = re.sub(r"[ \t]+", " ", reflow(text))
    parts = re.split(r"(?<=[.;!?])\s+(?=[A-ZÀ-Ý0-9«\"(•-])|\n{1,}", text)
    return [p.strip(" •-\t") for p in parts if len(p.strip()) >= 25]


_IT_WORDS = re.compile(r"\b(?:il|la|di|che|per|con|non|sono|del|delle|dei|della|nel|alla|gli|una|come)\b", re.I)
_EN_WORDS = re.compile(r"\b(?:the|of|and|to|for|with|shall|must|is|are|will|be|by|from|that|this)\b", re.I)


def detect_lang(text: str) -> str:
    sample = text[:20000]
    it, en = len(_IT_WORDS.findall(sample)), len(_EN_WORDS.findall(sample))
    return "en" if en > it * 1.3 else "it"


def looks_garbled(text: str) -> bool:
    """Testo estratto male (font non decodificabili: «(cid:12)», simboli, poche lettere)."""
    sample = text[:20000]
    if not sample.strip():
        return True
    letters = sum(c.isalpha() for c in sample)
    return sample.count("(cid:") > 20 or letters / max(len(sample), 1) < 0.45


# ------------------------------------------------------------------ cifre: tetti, soglie, importi, durate
_FIG_PERCENT = re.compile(r"(?<![\d.,])(\d{1,3}(?:[.,]\d{1,4})?)\s*(?:%|per\s*cento\b)", re.I)       # «3,575%» ha tre decimali: con due si leggeva 575
_FIG_EUR = re.compile(r"(?:€|euro|EUR)\s*(\d[\d.,]*)(?:\s*(milioni|mln|mila|miliardi))?|(\d[\d.,]*)\s*(milioni|mln|mila|miliardi)?\s*(?:di\s+)?(?:€|euro|EUR)\b", re.I)
_FIG_DURATION = re.compile(r"(\d{1,3})\s*(giorni|mesi|anni|days|months|years)\b", re.I)
_BOUND_MAX = re.compile(r"non\s+(?:pu[oò]\s+|possono\s+|deve\s+|devono\s+)?(?:essere\s+)?(?:superior\w+|superare|eccedere|oltre)|massim\w+|fino\s+(?:a|al|ad)|al\s+più|entro|non\s+oltre|up\s+to|no\s+more\s+than|not\s+exceed\w*|maximum|at\s+most|limite\s+di", re.I)
_BOUND_MIN = re.compile(r"almeno|minim\w+|non\s+inferior\w+|pari\s+o\s+superior\w+|a\s+partire\s+da|at\s+least|minimum|no\s+less\s+than|not\s+less\s+than", re.I)
_MULT = {"mila": 1_000, "milioni": 1_000_000, "mln": 1_000_000, "miliardi": 1_000_000_000}
_UNIT = {"giorni": "giorni", "days": "giorni", "mesi": "mesi", "months": "mesi", "anni": "anni", "years": "anni"}


def _bound(before: str) -> str:
    """Il verbo che precede la cifra dice se è un tetto o una soglia minima; senza indicazione è un valore di riferimento."""
    window = re.split(r"[;:]", before[-55:])[-1]      # il verbo vale solo per la cifra della sua stessa clausola
    mx, mn = list(_BOUND_MAX.finditer(window)), list(_BOUND_MIN.finditer(window))
    if mx and (not mn or mx[-1].start() > mn[-1].start()):
        return "MAX"
    if mn:
        return "MIN"
    return "RIF"


def extract_figures(sentence: str) -> List[Dict]:
    """Cifre di una frase come dati strutturati: {kind: PERCENT|EUR|DURATION, value, unit, bound: MAX|MIN|RIF}. Le date e i numeri di atto non sono cifre."""
    out: List[Dict] = []
    for m in _FIG_PERCENT.finditer(sentence):
        try:
            out.append({"kind": "PERCENT", "value": _num(m.group(1)), "unit": "%", "bound": _bound(sentence[:m.start()])})
        except ValueError:
            continue
    for m in _FIG_EUR.finditer(sentence):
        raw, mult = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        try:
            value = _num(raw.strip(".,")) * _MULT.get((mult or "").lower(), 1)
        except ValueError:
            continue
        out.append({"kind": "EUR", "value": value, "unit": "€", "bound": _bound(sentence[:m.start()])})
    for m in _FIG_DURATION.finditer(sentence):
        out.append({"kind": "DURATION", "value": int(m.group(1)), "unit": _UNIT[m.group(2).lower()], "bound": _bound(sentence[:m.start()])})
    seen, uniq = set(), []
    for f in out:
        k = (f["kind"], f["value"], f["bound"])
        if k not in seen:
            seen.add(k)
            uniq.append(f)
    return uniq[:6]


def extract_requirements(text: str, max_items: int = 3000, source_ref: str = "testo caricato") -> List[Dict]:
    """Ogni frase con un tema noto o con un obbligo/divieto diventa un requisito tracciato, in tutto il documento
    (non solo le prime pagine), con l'articolo in cui si trova quando il testo ne ha."""
    out: List[Dict] = []
    seen: Set[str] = set()
    article = ""
    for sentence in split_sentences(_mark_sections(text)):
        if sentence.startswith("§§"):
            article = sentence.strip("§ ")
            continue
        if _CITATION.match(sentence):
            continue
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
            out.append({"topic": " / ".join(t for t, _ in topics[:3]), "kind": kind, "text": (f"[{article}] " if article else "") + sentence[:600], "criteria": criteria,
                        "source_ref": source_ref, "confidence": "PARSING", "figures": extract_figures(sentence)})
        elif kind in ("DIVIETO", "OBBLIGO"):
            out.append({"topic": "Non classificato", "kind": "DA_REVISIONARE", "text": (f"[{article}] " if article else "") + sentence[:600], "criteria": [],
                        "source_ref": source_ref, "confidence": "PARSING", "figures": extract_figures(sentence)})
        if len(out) >= max_items:
            break
    if len(out) < 8 and len(text) > 1500:
        out += _salient(text, {r["text"] for r in out}, source_ref, limit=40)
    return out


def _salient(text: str, taken: Set[str], source_ref: str, limit: int = 40) -> List[Dict]:
    """Rete di sicurezza: un documento lungo non deve mai risultare «vuoto». Si tengono le frasi con numeri e unità (importi, %, durate) o con un obbligo/divieto,
    anche se non rientrano in un tema noto, segnalate come DA CLASSIFICARE (le vede il consulente)."""
    out: List[Dict] = []
    for sentence in split_sentences(text):
        if sentence in taken or len(sentence) < 50:
            continue
        if _PROHIBIT.search(sentence):
            kind = "DIVIETO"
        elif _OBLIGE.search(sentence):
            kind = "OBBLIGO"
        elif _LIMIT.search(sentence) and re.search(r"\d", sentence):
            kind = "LIMITE"
        else:
            continue
        out.append({"topic": "Da classificare", "kind": "DA_REVISIONARE" if kind in ("DIVIETO", "OBBLIGO") else kind, "text": sentence[:600], "criteria": [],
                    "source_ref": source_ref, "confidence": "PARSING"})
        if len(out) >= limit:
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


# ------------------------------------------------------------------ regole numeriche dalle cifre (tabella dichiarativa)
# (chiave della regola, parola chiave nella frase, tipo di cifra, versi ammessi, conversione). Una frase conta solo se ha UNA cifra di quel tipo e verso:
# con due cifre non si sa a quale riferirla, e una regola sbagliata altera le validazioni.
FIGURE_RULES = [
    ("max_installation_pct", re.compile(r"installazion\w+|trasport\w+|collaud\w+", re.I), "PERCENT", ("MAX",), "fraction"),
    # un tetto esplicito («intensità massima», «l'intensità non può superare»): non basta la parola «intensità», che compare anche nelle statistiche di una relazione
    ("max_aid_intensity_pct", re.compile(r"intensit[àa]\s+(?:di\s+aiut\w+\s+)?massima|massima\s+intensit[àa]|intensit[àa][^.;]{0,70}non\s+(?:pu[oò]|possono)\s+(?:essere\s+)?(?:superior\w+|superare)", re.I), "PERCENT", ("MAX", "RIF"), "fraction"),
    # l'anticipo del contributo, non l'acconto dell'impresa al fornitore: la frase deve legare l'anticipo all'agevolazione
    ("advance_pct", re.compile(r"anticip\w+[^.;]{0,90}(?:agevolazion\w+|contribut\w+|finanziament\w+|intervento)|(?:agevolazion\w+|contribut\w+|intervento)[^.;]{0,90}anticip\w+|a\s+titolo\s+di\s+anticip\w+", re.I), "PERCENT", ("MAX", "RIF"), "fraction"),
    ("max_inter_chapter_variation_pct", re.compile(r"(?:variazion\w+|compensazion\w+|scostament\w+)[^.;]{0,80}(?:voci|capitol\w+|categori\w+)", re.I), "PERCENT", ("MAX", "RIF"), "fraction"),
    ("reimbursement_lag_months", re.compile(r"(?:rimbors\w+|liquidazion\w+|erogazion\w+|saldo)[^.;]{0,70}entro", re.I), "DURATION", ("MAX",), "months"),
]


def extract_figure_rules(text: str) -> Dict[str, List[str]]:
    """{chiave: [valori distinti]} dalle frasi che hanno la parola chiave della regola e una sola cifra del tipo giusto.
    Più valori diversi per la stessa chiave restano tutti: sarà ingestion a trattarli come ambigui (revisione umana)."""
    found: Dict[str, List[str]] = {}
    for sentence in split_sentences(text):
        figs = None
        for key, cue, kind, bounds, conv in FIGURE_RULES:
            if not cue.search(sentence):
                continue
            figs = extract_figures(sentence) if figs is None else figs
            same = [f for f in figs if f["kind"] == kind and f["bound"] in bounds]
            if len(same) != 1:
                continue
            f = same[0]
            if conv == "fraction":
                if not 0 < f["value"] <= 100:
                    continue
                value = _fmt(f["value"] / 100)
            else:                                   # durata in mesi: i giorni non si arrotondano a mesi, si lasciano fuori
                if f["unit"] == "mesi":
                    value = str(int(f["value"]))
                elif f["unit"] == "anni":
                    value = str(int(f["value"]) * 12)
                else:
                    continue
            if value not in found.setdefault(key, []):
                found[key].append(value)
    return found


def extract_more_rules(text: str) -> Dict[str, str]:
    rules = {**_flag_rules(text), **_cap_rules(text)}
    scope = category_scope(text)
    if scope is not None:
        rules["eligible_categories"] = json.dumps(scope)
    return rules


# ------------------------------------------------------------------ riferimenti normativi citati nel testo
_MONTHS = r"gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre"
_DATE = rf"\d{{1,2}}[/.\-]\d{{1,2}}[/.\-]\d{{2,4}}|\d{{1,2}}\s+(?:{_MONTHS})\s+\d{{4}}"
_KIND = (r"Decreto[- ]Legge|Decreto\s+Legislativo|Decreto\s+del\s+Presidente\s+della\s+Repubblica|Decreto\s+Interministeriale|"
         r"Decreto\s+Direttoriale|Decreto\s+Ministeriale|Decreto\s+del\s+Ministro|DPCM|D\.\s?P\.\s?R\.|D\.\s?L\.|D\.\s?Lgs\.|"
         r"Legge\s+[Rr]egionale|Legge|Regolamento\s+delegato\s+\((?:UE|CE)\)|Regolamento\s+\((?:UE|CE)\)|Regolamento\s+(?:UE|CE)|"
         r"Direttiva\s+\((?:UE|CE)\)|Direttiva\s+(?:UE|CE)|Deliberazione|Delibera|Circolare|Determinazione|Determina")
# Ordine «numero poi data»: «Legge n. 207/2024» oppure «Legge n. 207 del 30 dicembre 2024».
_LEGAL_NUM_FIRST = re.compile(rf"({_KIND})\s+(?:n\.?\s*)?(\d{{1,4}}(?:/\d{{2,4}})?)(?:\s*(?:del|dell['’]|,)\s*({_DATE}))?", re.I)
# Ordine «data poi numero», il più frequente nei testi ufficiali italiani: «Legge 30 dicembre 2024, n. 207».
_LEGAL_DATE_FIRST = re.compile(rf"({_KIND})\s+({_DATE})\s*,?\s*n\.?\s*(\d{{1,4}}(?:/\d{{2,4}})?)", re.I)


def extract_legal_refs(text: str, limit: int = 40) -> List[str]:
    """Atti citati nel testo (decreti, leggi, regolamenti UE…), i più citati per primi.

    Riconosce entrambi gli ordini di citazione usati nei testi ufficiali italiani: «Legge n. 207 del
    30/12/2024» (meno comune) e «Legge 30 dicembre 2024, n. 207» (il più frequente in assoluto — la forma
    che la versione precedente di questa funzione non riconosceva affatto).
    """
    counts: Dict[str, int] = {}
    for m in _LEGAL_NUM_FIRST.finditer(text):
        kind, number, when = m.group(1), m.group(2), m.group(3)
        if not when and "/" not in number:
            continue  # "legge n. 27" senza data né anno: ambiguo, non è un riferimento utilizzabile
        kind = re.sub(r"\s+", " ", kind).strip()
        ref = f"{kind[:1].upper() + kind[1:]} n. {number}" + (f" del {when}" if when else "")
        counts[ref] = counts.get(ref, 0) + 1
    for m in _LEGAL_DATE_FIRST.finditer(text):
        kind, when, number = m.group(1), m.group(2), m.group(3)
        kind = re.sub(r"\s+", " ", kind).strip()
        ref = f"{kind[:1].upper() + kind[1:]} n. {number} del {when}"
        counts[ref] = counts.get(ref, 0) + 1
    return [r for r, _ in sorted(counts.items(), key=lambda kv: -kv[1])][:limit]
