"""Le voci di spesa: la classificazione fine che sta sotto le cinque categorie generali.

Le cinque categorie (personale, beni strumentali, consulenze, spese generali, formazione) bastano per un primo quadro, ma un bando non ragiona così:
ammette «i canoni di licenza software» e non «l'affitto», rimborsa la «formazione specialistica» ma non quella obbligatoria, esclude le «spese di rappresentanza»
e le «fideiussioni». E un'azienda non spende «in generale»: spende in affitti, energia, trasferte, consulenze legali, brevetti. Per decidere cosa si può ridurre
e come impostare un budget servono quelle voci, così come stanno scritte nei bilanci, nei registri e nei bandi.

Ogni voce ha un **codice stabile**, un'**etichetta**, la **categoria generale** a cui appartiene e le **parole** con cui compare nei documenti (confronto senza
accenti né maiuscole, sul radicale). La categoria generale resta quella già usata da tutto il sistema (``CostCategory``): la voce la raffina, non la sostituisce.

Le voci sono un elenco aperto: ``classify_type`` non inventa mai una voce, e quando nessuna parola corrisponde restituisce la voce generica della categoria
(«Altre voci di …»), così nulla resta senza una voce e nulla viene classificato per fantasia.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Optional, Tuple

OTHER = "OTHER"      # costi che nessun bando rimborsa (imposte indirette, quote associative, sanzioni…)


def norm(text: str) -> str:
    t = unicodedata.normalize("NFKD", (text or "").replace("’", "'")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t.replace("'", "")).strip().upper()


# codice, etichetta, categoria, parole nei documenti, (sottotipo di spesa per i controlli), (natura del bene)
_T: List[Tuple[str, str, str, List[str], Optional[str], Optional[str]]] = [
    # ---------------------------------------------------------------- personale
    ("PERS_STIPENDI", "Stipendi e salari", "PERSONNEL", ["SALARI", "STIPENDI", "RETRIBUZ", "MENSILITA"], None, None),
    ("PERS_ONERI", "Oneri sociali e contributi previdenziali", "PERSONNEL", ["ONERI SOCIALI", "CONTRIBUTI PREVIDENZIALI", "CONTRIBUTI SOCIALI", "INPS"], None, None),
    ("PERS_TFR", "Trattamento di fine rapporto", "PERSONNEL", ["TRATTAMENTO DI FINE RAPPORTO", "TFR"], None, None),
    ("PERS_INAIL", "Premi INAIL", "PERSONNEL", ["INAIL"], None, None),
    ("PERS_STRAORD", "Lavoro straordinario", "PERSONNEL", ["STRAORDINARI"], None, None),
    ("PERS_FERIE", "Ferie, permessi e festività", "PERSONNEL", ["FERIE", "PERMESSI", "FESTIVITA"], None, None),
    ("PERS_WELFARE", "Welfare, buoni pasto e fondi sanitari", "PERSONNEL", ["BUONI PASTO", "WELFARE", "FONDO EST", "ASSISTENZA SANITARIA", "FONDI SANITARI"], None, None),
    ("PERS_ALTRO", "Altre voci di personale", "PERSONNEL", ["PERSONALE"], None, None),
    # ---------------------------------------------------------------- consulenze e prestazioni professionali
    ("CONS_TECNICHE", "Consulenze tecniche e informatiche", "CONSULTING", ["INFORMATIC", "TECNIC", "INGEGNER", "DATA SCIENCE", "SVILUPPO SOFTWARE", "SICUREZZA INFORMATICA", "PENETRATION", "ARCHITETTUR"], None, None),
    ("CONS_LEGALI", "Consulenze legali e notarili", "CONSULTING", ["AVVOCAT", "LEGAL", "NOTAI", "CONTRATTUAL"], None, None),
    ("CONS_FISCALI", "Consulenze fiscali, contabili e del lavoro", "CONSULTING", ["COMMERCIALIST", "FISCAL", "CONTABIL", "PAGHE", "CONSULENTE DEL LAVORO", "TRIBUTAR"], None, None),
    ("CONS_CERTIF", "Certificazioni, revisione e perizie", "CONSULTING", ["CERTIFICAZ", "REVISIONE", "AUDIT", "PERIZI", "ASSEVERAZ", "COLLAUD", "ISO 9001", "ISO 27001"], "AUDIT", None),
    ("CONS_PI", "Brevetti, marchi e proprietà intellettuale", "CONSULTING", ["BREVETT", "MARCHI", "PROPRIETA INTELLETTUALE", "DEPOSITO MARCHI"], None, None),
    ("CONS_MARKETING", "Consulenze commerciali e di marketing", "CONSULTING", ["MARKETING", "COMMERCIALI", "STRATEGI", "COMUNICAZIONE"], None, None),
    ("CONS_COLLAB", "Collaboratori e lavoro autonomo", "CONSULTING", ["COLLABORATOR", "LAVORO AUTONOMO", "PRESTAZIONI OCCASIONALI", "COLLABORAZIONI"], None, None),
    ("CONS_ALTRE", "Altre consulenze e prestazioni professionali", "CONSULTING", ["CONSULENZ", "PRESTAZIONI PROFESSIONALI", "COMPENSI A PROFESSIONISTI", "SERVIZI PROFESSIONALI", "COMPENSI PROFESSIONALI"], None, None),
    # ---------------------------------------------------------------- formazione
    ("TRN_CORSI", "Corsi di formazione", "TRAINING", ["CORSI DI", "FORMAZIONE", "ADDESTRAMENTO"], None, None),
    ("TRN_SEMINARI", "Seminari, workshop e conferenze", "TRAINING", ["SEMINARI", "WORKSHOP", "CONFERENZE", "CONVEGNI"], None, None),
    ("TRN_AGGIORN", "Aggiornamento professionale", "TRAINING", ["AGGIORNAMENTO PROFESSIONALE", "AGGIORNAMENTO"], None, None),
    # ---------------------------------------------------------------- spese generali
    ("OH_AFFITTI", "Affitti e locazioni", "OVERHEAD", ["AFFITT", "LOCAZION", "CANONI DI LOCAZIONE"], "RENT", None),
    ("OH_CONDOMINIO", "Spese condominiali", "OVERHEAD", ["CONDOMINIAL"], "RENT", None),
    ("OH_ENERGIA", "Energia elettrica, gas e riscaldamento", "OVERHEAD", ["ENERGIA ELETTRICA", "ELETTRIC", "RISCALDAMENTO", "GAS", "ENERGIA"], "UTILITIES", None),
    ("OH_ACQUA", "Acqua e servizi idrici", "OVERHEAD", ["ACQUA", "IDRIC"], "UTILITIES", None),
    ("OH_TELEFONIA", "Telefonia e connettività", "OVERHEAD", ["TELEFON", "CONNETTIVIT", "INTERNET", "FIBRA", "TELECOMUNICAZ"], "UTILITIES", None),
    ("OH_ASSICURAZ", "Assicurazioni", "OVERHEAD", ["ASSICURAZION", "POLIZZ"], None, None),
    ("OH_MANUTENZ", "Manutenzioni e riparazioni", "OVERHEAD", ["MANUTENZION", "RIPARAZION", "ASSISTENZA TECNICA"], "MAINTENANCE_ORDINARY", None),
    ("OH_PULIZIE", "Pulizie e vigilanza", "OVERHEAD", ["PULIZI", "VIGILANZA", "SMALTIMENTO"], None, None),
    ("OH_CANCELLERIA", "Cancelleria e materiali di consumo", "OVERHEAD", ["CANCELLERIA", "MATERIALE DI CONSUMO", "MATERIALI DI CONSUMO", "STAMPATI"], None, None),
    ("OH_POSTALI", "Spese postali e spedizioni", "OVERHEAD", ["POSTAL", "SPEDIZION", "CORRIERE"], None, None),
    ("OH_BANCARIE", "Spese e commissioni bancarie", "OVERHEAD", ["SPESE BANCARIE", "COMMISSIONI BANCARIE", "COMMISSIONI", "INTERESSI PASSIVI", "ONERI FINANZIARI"], "FINANCIAL_CHARGES", None),
    ("OH_VIAGGI", "Viaggi e trasferte", "OVERHEAD", ["TRASFERT", "VIAGGI", "DIARIE", "RIMBORSI SPESE", "ALBERGHI", "VITTO E ALLOGGIO"], None, None),
    ("OH_RAPPRES", "Spese di rappresentanza", "OVERHEAD", ["RAPPRESENTANZA", "OMAGGI"], "REPRESENTATION", None),
    ("OH_PUBBLICITA", "Pubblicità, promozione e fiere", "OVERHEAD", ["PUBBLICIT", "PROMOZION", "FIERE", "MARKETING", "SPONSORIZZ"], "COMMUNICATION", None),
    ("OH_NOLEGGI", "Noleggi e leasing operativo", "OVERHEAD", ["NOLEGGIO", "LEASING"], None, None),
    ("OH_GENERALI", "Altre spese generali", "OVERHEAD", ["SPESE GENERALI"], None, None),
    # ---------------------------------------------------------------- beni strumentali
    ("CAP_HARDWARE", "Computer, server e dispositivi", "CAPITAL_ASSETS", ["HARDWARE", "SERVER", "COMPUTER", "WORKSTATION", "NOTEBOOK", "DISPOSITIVI", "STORAGE"], None, "HARDWARE"),
    ("CAP_SOFTWARE", "Software e licenze d'uso", "CAPITAL_ASSETS", ["SOFTWARE", "LICENZ"], None, "SOFTWARE"),
    ("CAP_CLOUD", "Servizi cloud e hosting", "CAPITAL_ASSETS", ["CLOUD", "HOSTING", "SAAS"], None, None),
    ("CAP_ATTREZZ", "Macchinari e attrezzature", "CAPITAL_ASSETS", ["MACCHINARI", "ATTREZZATUR"], None, "HARDWARE"),
    ("CAP_IMPIANTI", "Impianti", "CAPITAL_ASSETS", ["IMPIANTI", "IMPIANTO"], None, "HARDWARE"),
    ("CAP_ARREDI", "Arredi e mobili d'ufficio", "CAPITAL_ASSETS", ["ARREDI", "MOBILI"], None, "HARDWARE"),
    ("CAP_AUTOMEZZI", "Automezzi", "CAPITAL_ASSETS", ["AUTOMEZZI", "AUTOVETTUR", "VEICOL"], None, "HARDWARE"),
    ("CAP_IMMATERIALI", "Immobilizzazioni immateriali (sviluppo, diritti, marchi)", "CAPITAL_ASSETS", ["IMMATERIAL", "COSTI DI SVILUPPO", "DIRITTI DI UTILIZZ", "AVVIAMENTO", "SVILUPPO PIATTAFORMA", "PIATTAFORMA"], None, "IMMATERIAL"),
    ("CAP_IMMOBILI", "Immobili e fabbricati", "CAPITAL_ASSETS", ["FABBRICAT", "IMMOBILI", "TERRENI"], None, "REAL_ESTATE"),
    ("CAP_AMMORT", "Ammortamenti", "CAPITAL_ASSETS", ["AMMORTAMENT", "IMMOBILIZZAZIONI"], None, None),
    ("CAP_ALTRO", "Altri beni strumentali", "CAPITAL_ASSETS", [], None, None),
    # ---------------------------------------------------------------- non agevolabili
    ("OTH_IMPOSTE", "Imposte, tasse e bolli", "OTHER", ["IMPOSTE E TASSE", "IMPOSTA DI BOLLO", "TASSA", "DIRITTI CAMERALI", "IMU"], None, None),
    ("OTH_QUOTE", "Quote associative e liberalità", "OTHER", ["QUOTE ASSOCIATIV", "LIBERALIT", "EROGAZIONI LIBERALI"], None, None),
    ("OTH_SANZIONI", "Sanzioni, multe e ammende", "OTHER", ["SANZION", "MULTE", "AMMENDE"], "PENALTY", None),
    ("OTH_SVALUT", "Svalutazioni, perdite su crediti e sopravvenienze", "OTHER", ["SVALUTAZION", "PERDITE SU CREDITI", "SOPRAVVENIENZ", "MINUSVALENZ", "ARROTONDAMENT"], None, None),
    ("OTH_CARBURANTI", "Carburanti e lubrificanti", "OTHER", ["CARBURANT"], None, None),
]

#: la voce generica di ogni categoria, usata quando nessuna parola corrisponde
GENERIC: Dict[str, str] = {"PERSONNEL": "PERS_ALTRO", "CONSULTING": "CONS_ALTRE", "TRAINING": "TRN_CORSI", "OVERHEAD": "OH_GENERALI", "CAPITAL_ASSETS": "CAP_ALTRO", OTHER: "OTH_SVALUT"}

TYPES: Dict[str, Dict] = {code: {"code": code, "label": label, "category": cat, "keywords": kws, "subtype": sub, "asset_nature": nat} for code, label, cat, kws, sub, nat in _T}
LABEL: Dict[str, str] = {c: t["label"] for c, t in TYPES.items()}
CATEGORY_OF: Dict[str, str] = {c: t["category"] for c, t in TYPES.items()}
BY_CATEGORY: Dict[str, List[str]] = {}
for _c, _t in TYPES.items():
    BY_CATEGORY.setdefault(_t["category"], []).append(_c)


def classify_type(description: str, category: Optional[str] = None) -> Optional[str]:
    """Il codice della voce di spesa che meglio descrive ``description``. Con ``category`` si cerca solo tra le voci di quella categoria (e se nulla corrisponde
    si restituisce la voce generica); senza, tra tutte (e se nulla corrisponde, ``None``). Vince la parola più lunga e specifica."""
    n = norm(description)
    if "AMMORTAMENT" in n and category in (None, "CAPITAL_ASSETS"):        # l'ammortamento è sempre l'ammortamento, qualunque sia il bene ammortizzato
        return "CAP_AMMORT"
    generic = set(GENERIC.values())
    best: Optional[str] = None
    for pool in (False, True):                                            # prima le voci specifiche; le generiche solo se nessuna specifica corrisponde
        best_len = 0
        for code, t in TYPES.items():
            if (category and t["category"] != category) or ((code in generic) != pool):
                continue
            for kw in t["keywords"]:
                if kw in n and len(kw) > best_len:
                    best, best_len = code, len(kw)
        if best:
            break
    if best is None and category:
        return GENERIC.get(category)
    return best


def label(code: Optional[str]) -> str:
    return LABEL.get(code or "", code or "")


def catalog() -> List[Dict]:
    """Elenco per l'interfaccia: codice, etichetta e categoria."""
    return [{"code": c, "label": t["label"], "category": t["category"]} for c, t in TYPES.items()]


# ------------------------------------------------------------------------------------------------ cosa dice un bando
# Le parole con cui un TESTO UFFICIALE nomina una voce di spesa possono differire da quelle di un bilancio («locazione di immobili», «canoni», «costi di fideiussione»).
_TEXT_EXTRA: Dict[str, List[str]] = {
    "OH_AFFITTI": ["CANONI", "LOCAZIONE DI IMMOBILI", "AFFITTO DI LOCALI"], "OH_RAPPRES": ["SPESE DI RAPPRESENTANZA", "RAPPRESENTANZA"], "OH_BANCARIE": ["FIDEIUSSION", "INTERESSI", "ONERI FINANZIARI", "SPESE BANCARIE", "COSTI DI GARANZIA"],
    "OH_VIAGGI": ["SPESE DI VIAGGIO", "MISSIONI", "TRASFERTE"], "OH_PUBBLICITA": ["SPESE DI PUBBLICITA", "COMUNICAZIONE E PROMOZIONE", "ATTIVITA PROMOZIONALI"], "OH_MANUTENZ": ["MANUTENZIONE ORDINARIA"],
    "OH_NOLEGGI": ["NOLEGGIO", "LEASING"], "CAP_AUTOMEZZI": ["AUTOVEICOLI", "MEZZI DI TRASPORTO"], "CAP_IMMOBILI": ["ACQUISTO DI IMMOBILI", "ACQUISTO DI TERRENI", "OPERE MURARIE"], "OTH_IMPOSTE": ["IVA", "IMPOSTE", "TASSE", "ONERI FISCALI"],
    "OTH_SANZIONI": ["PENALI", "SANZIONI", "AMMENDE"], "CAP_SOFTWARE": ["LICENZE SOFTWARE", "LICENZE D USO", "PROGRAMMI INFORMATICI"], "CONS_PI": ["BREVETTI", "BREVETTAZIONE", "REGISTRAZIONE DI MARCHI", "DIRITTI DI PROPRIETA INDUSTRIALE"],
    "TRN_CORSI": ["FORMAZIONE DEL PERSONALE", "CORSI DI FORMAZIONE"], "PERS_STRAORD": ["LAVORO STRAORDINARIO"], "CAP_ATTREZZ": ["ATTREZZATURE", "MACCHINARI"], "CONS_CERTIF": ["CERTIFICAZIONI", "REVISIONE CONTABILE"],
}
_NEGATIVE = re.compile(r"NON\s+(?:SONO\s+|E\s+|RISULTANO\s+)?(?:AMMISSIBIL\w+|FINANZIABIL\w+|AMMESS\w+|RIMBORSABIL\w+|AGEVOLABIL\w+|CONSENTIT\w+)|\bESCLUS[EAIO]\b|\bESCLUDE\b|\bESCLUDONO\b|\bVIETAT\w+|\bDIVIETO\b|NON\s+RIENTRAN\w+")
_POSITIVE = re.compile(r"(?:SONO|RISULTANO|SARANNO)\s+AMMISSIBIL\w+|(?:SONO|RISULTANO)\s+FINANZIABIL\w+|SONO\s+AMMESS\w+|RIENTRAN\w+\s+TRA\s+LE\s+SPESE|AMMISSIBIL\w+\s+LE\s+SPESE|SPESE\s+AMMISSIBIL\w+")


def _sentences(text: str) -> List[str]:
    return [s for s in re.split(r"(?<=[.;:])\s+|\n+", text or "") if s.strip()]


def type_scope(text: str) -> Dict[str, Dict[str, List[str]]]:
    """Quali voci di spesa un testo ufficiale esclude e quali nomina come ammesse, con la frase che lo dice (la prova).
    Una voce è «esclusa» solo se una frase la nomina e dice (nella stessa frase) che non è ammissibile; è «ammessa» se una frase la nomina e la dice ammissibile,
    senza negazioni. Una frase con entrambi i segni non conta (ambigua): non si decide al posto di chi legge."""
    out: Dict[str, Dict[str, List[str]]] = {"excluded": {}, "eligible": {}}
    for raw in _sentences(text):
        if len(raw) > 350:                                      # una «frase» così lunga è un elenco o un impaginato rotto, non un'affermazione su una voce
            continue
        s = norm(raw)
        neg, pos = bool(_NEGATIVE.search(s)), bool(_POSITIVE.search(_NEGATIVE.sub(" ", s)))      # «non sono ammissibili le spese…» non è anche una frase positiva
        if neg == pos:
            continue
        hit = []
        for code, t in TYPES.items():
            if t["category"] == OTHER and not neg:
                continue
            words = set(_TEXT_EXTRA.get(code, [])) | {k for k in t["keywords"] if len(k) >= 7}
            if any(re.search(r"(?<![A-Z])" + re.escape(w) + r"(?![A-Z]{4,})", s) for w in words):
                hit.append(code)
        if len(hit) > 8:                                        # una frase che nomina quasi tutto non parla di una voce in particolare
            continue
        for code in hit:
            out["excluded" if neg else "eligible"].setdefault(code, []).append(raw.strip()[:240])
    for code in set(out["excluded"]) & set(out["eligible"]):      # detto in un senso e nell'altro: non si decide
        out["eligible"].pop(code)
        out["excluded"].pop(code)
    return out
