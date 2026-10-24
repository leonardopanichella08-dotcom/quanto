"""Un bando è PERTINENTE per un'azienda solo se può davvero riguardarla: territorio, settore e tipo di soggetto.

Prima il giudizio «da verificare» bastava che non ci fosse una percentuale o che mancasse un dato: così un bando sugli autobus elettrici del PNRR finiva tra i
possibili per un negozio di abbigliamento. Qui si decide con segni scritti nel bando (il nome, chi può presentare domanda, la scheda del catalogo), mai per
somiglianza: se il bando nomina un settore e l'ATECO dell'azienda non ci rientra, o se è riservato a enti pubblici, famiglie o associazioni, NON è adatto, e il
motivo si legge in chiaro. Se il bando non nomina nessun settore, non si esclude nulla.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set

from app.core.company_profile import REGIONS

# --- territorio: province e capoluoghi che compaiono nei nomi («Camera di commercio di Chieti e Pescara», «Comune di Bari»…)
_PLACES: Dict[str, List[str]] = {
    "Abruzzo": ["l'aquila", "teramo", "pescara", "chieti", "abruzzo"],
    "Basilicata": ["matera", "basilicata"],
    "Calabria": ["catanzaro", "cosenza", "crotone", "reggio calabria", "vibo valentia", "calabria"],
    "Campania": ["napoli", "salerno", "caserta", "avellino", "benevento", "campania"],
    "Emilia-Romagna": ["bologna", "modena", "parma", "reggio emilia", "ravenna", "forli", "cesena", "rimini", "ferrara", "piacenza", "romagna"],
    "Friuli Venezia Giulia": ["trieste", "udine", "gorizia", "pordenone", "friuli", "fvg"],
    "Lazio": ["roma", "latina", "frosinone", "viterbo", "rieti", "lazio"],
    "Liguria": ["genova", "savona", "la spezia", "imperia", "liguria"],
    "Lombardia": ["milano", "bergamo", "brescia", "cremona", "lecco", "mantova", "monza", "pavia", "sondrio", "varese", "lombardia"],
    "Marche": ["ancona", "pesaro", "urbino", "macerata", "ascoli piceno", "marche"],
    "Molise": ["campobasso", "isernia", "molise"],
    "Piemonte": ["torino", "alessandria", "asti", "biella", "cuneo", "novara", "verbania", "vercelli", "ossola", "piemonte"],
    "Puglia": ["bari", "taranto", "brindisi", "lecce", "foggia", "barletta", "puglia"],
    "Sardegna": ["cagliari", "sassari", "nuoro", "oristano", "sud sardegna", "gallura", "sardegna"],
    "Sicilia": ["palermo", "catania", "messina", "agrigento", "caltanissetta", "ragusa", "siracusa", "trapani", "sicilia"],
    "Toscana": ["firenze", "pisa", "livorno", "lucca", "arezzo", "siena", "grosseto", "pistoia", "prato", "massa carrara", "toscana"],
    "Trentino-Alto Adige": ["trento", "bolzano", "trentino", "alto adige", "sudtirol"],
    "Umbria": ["perugia", "terni", "umbria"],
    "Valle d'Aosta": ["aosta", "valle d'aosta", "vallee d'aoste"],
    "Veneto": ["venezia", "verona", "padova", "vicenza", "treviso", "belluno", "rovigo", "veneto"],
}
_PLACE_RX = [(region, re.compile(r"(?<![a-z])(?:" + "|".join(re.escape(p) for p in names) + r")(?![a-z])")) for region, names in _PLACES.items()]


def _fold(text: str) -> str:
    import unicodedata
    return unicodedata.normalize("NFKD", (text or "").lower().replace("’", "'")).encode("ascii", "ignore").decode()


def regions_in(text: str) -> Set[str]:
    """Regioni nominate nel testo, direttamente o con una loro provincia o capoluogo."""
    t = _fold(text).replace("friuli venezia giulia", " fvg ")           # «Venezia» dentro il nome della regione non è la provincia veneta
    return {region for region, rx in _PLACE_RX if rx.search(t)}


# --- settore: parole che dicono a quale attività è rivolto il bando -> prefissi ATECO ammessi (senza punti)
_MANUF = [f"{d:02d}" for d in range(1, 34)]
SECTOR_LEXICON: List[Dict[str, Any]] = [
    {"label": "trasporti e mezzi di trasporto", "rx": r"autobus|trasporto pubblico|trasporto passeggeri|\btpl\b|ferrovi|trasporto marittimo|armator|aeroport|autotrasport|trasporto merci|trasporto stradale",
     "ateco": ["29", "30", "49", "50", "51", "52", "53"]},
    {"label": "agricoltura, pesca e agroalimentare", "rx": r"agricol|agroalimentar|zootecn|allevament|\bpesca\b|acquacoltura|forestal|vitivinicol|\bpsr\b|\bfeasr\b|filiera del vino",
     "ateco": ["01", "02", "03", "10", "11", "12", "55"]},
    {"label": "semiconduttori ed elettronica", "rx": r"semiconduttor|microelettronic|\bchips?\b", "ateco": ["26", "27", "28", "62"]},
    {"label": "turismo e ricettività", "rx": r"turism|ricettiv|albergh|agenzie di viaggio|tour operator|termal|stabilimenti balneari", "ateco": ["55", "56", "79", "90", "91", "92", "93", "96"]},
    {"label": "cultura, cinema e spettacolo", "rx": r"cinema|audiovisiv|spettacolo dal vivo|teatr|musei|editoria|culturali e creative|filiera del libro|\blibrerie\b",
     "ateco": ["58", "59", "60", "73", "74", "90", "91", "92", "93", "4761", "4762"]},
    {"label": "sanità e assistenza", "rx": r"sanitari[ao]|socio-?sanitar|ospedal|assistenza sociale|farmacie", "ateco": ["21", "32", "86", "87", "88", "4773", "4774"]},
    {"label": "ricerca industriale e produzione", "rx": r"ricerca industriale|sviluppo sperimentale|\bhorizon\b|\btrl\b|ricerca e sviluppo|ricerca,? sviluppo e innovazione|progetti di ricerca|contratti? di sviluppo|programmi? di sviluppo industriale",
     "ateco": _MANUF + ["35", "36", "37", "38", "39", "58", "59", "60", "61", "62", "63", "69", "70", "71", "72", "73", "74", "85", "86", "87", "88"]},
    {"label": "sport", "rx": r"impianti sportivi|societ[aà] sportive|palestr|\bsport\b", "ateco": ["93", "85"]},
    {"label": "commercio e servizi alla persona", "rx": r"distrett[oi] del commercio|centri commerciali naturali|esercizi commerciali|negozi di vicinato|commercio al dettaglio|botteghe",
     "ateco": ["45", "46", "47", "55", "56", "79", "82", "95", "96", "68", "73"]},
]
for _e in SECTOR_LEXICON:
    _e["_rx"] = re.compile(_e["rx"], re.I)

_APPLICANT_ONLY_PUBLIC = re.compile(r"\b(pubblich[ae] amministrazion\w*|enti locali|comuni|unioni di comuni|scuole|universit[aà]|enti del terzo settore|associazioni|parrocchie|oratori|persone fisiche|"
                                    r"cittadini|famiglie|studenti|enti pubblici|gestori del servizio|aziende di trasporto|istituti scolastici|enti di ricerca)\b", re.I)
_APPLICANT_BUSINESS = re.compile(r"\b(impres\w*|pmi|societ[aà]|ditt\w*|professionist\w*|lavorator\w* autonom\w*|start-?up|microimpres\w*|aziend\w*|liberi professionisti|cooperative|artigian\w*)\b", re.I)


def _digits(ateco: Optional[str]) -> str:
    return re.sub(r"\D", "", str(ateco or ""))


def sector_fails(text: str, ateco: Optional[str]) -> List[str]:
    """Settori nominati dal bando ai quali l'ATECO dell'azienda non appartiene. Vuoto se il bando non nomina settori o se l'ATECO è ignoto."""
    d = _digits(ateco)
    if not d:
        return []
    named = [e for e in SECTOR_LEXICON if e["_rx"].search(_fold(text))]
    if not named:
        return []
    if any(d.startswith(p) for e in named for p in e["ateco"]):
        return []
    return [e["label"] for e in named]


def applicant_fails(text: str) -> Optional[str]:
    """Il testo su chi può presentare domanda nomina solo enti pubblici, famiglie, scuole, associazioni e nessuna impresa: non è per un'azienda."""
    m = _APPLICANT_ONLY_PUBLIC.search(text or "")
    if m and not _APPLICANT_BUSINESS.search(text or ""):
        return m.group(1)
    return None


def meta_fails(meta: Dict[str, Any], profile: Dict[str, Any]) -> List[Dict[str, str]]:
    """Esclusioni dalla scheda del catalogo (regioni, soggetti, dimensione, ATECO, settori elencati)."""
    from app.core import catalog_meta
    out: List[Dict[str, str]] = []
    region, size_code, ateco = profile.get("region"), (profile.get("size") or {}).get("code"), profile.get("ateco_code")
    regions = meta.get("regions") or []
    if regions and region and region.lower() not in [x.lower() for x in regions]:
        out.append({"id": "territory", "label": "Territorio", "detail": f"La scheda ufficiale lo riserva a {', '.join(regions[:3])}; la tua sede è in {region}."})
    kinds = [str(x).lower() for x in (meta.get("applicant_type") or [])]
    if kinds and not [k for k in kinds if "impresa" in k and "da costituire" not in k]:
        out.append({"id": "applicant", "label": "Chi può presentare domanda", "detail": f"La scheda ufficiale lo riserva a: {', '.join(meta['applicant_type'][:3])}. Non a un'impresa già costituita."})
    if catalog_meta._size_ok(meta.get("sizes") or [], size_code) is False:
        out.append({"id": "size", "label": "Dimensione", "detail": f"La scheda ammette solo: {', '.join(meta['sizes'][:3])}."})
    codes = meta.get("ateco_codes") or []
    if codes and ateco and not any(_digits(ateco).startswith(_digits(c)) for c in codes):
        out.append({"id": "ateco", "label": "Settore (ATECO)", "detail": f"La scheda ammette solo i codici {', '.join(codes[:6])}; il tuo è {ateco}."})
    listed = [s for s in (meta.get("sectors") or [])]
    d = _digits(ateco)
    if listed and 0 < len(listed) <= 10 and d[:2].isdigit():
        word = catalog_meta.SECTOR_OF_DIVISION.get(int(d[:2]))
        if word and not any(word in s.lower() for s in listed):
            out.append({"id": "sector", "label": "Settore", "detail": f"La scheda indica i settori: {', '.join(listed[:4])}. La tua attività è «{word}»."})
    return out


def text_fails(name: str, issuer: str, applicants: str, profile: Dict[str, Any]) -> List[Dict[str, str]]:
    """Esclusioni dai soli testi del bando: territorio (anche da provincia), settore nominato, soggetti ammessi."""
    out: List[Dict[str, str]] = []
    region, ateco = profile.get("region"), profile.get("ateco_code")
    named = regions_in(f"{name} {issuer}")
    if named and region and region not in named:
        out.append({"id": "territory", "label": "Territorio", "detail": f"Bando di {' / '.join(sorted(named))}; la tua sede è in {region}."})
    bad = sector_fails(f"{name} {applicants}", ateco)
    if bad:
        out.append({"id": "sector", "label": "Settore", "detail": f"Il bando è rivolto a: {', '.join(bad)}. Il tuo codice ATECO {ateco} non rientra."})
    who = applicant_fails(f"{name} {applicants}")
    if who:
        out.append({"id": "applicant", "label": "Chi può presentare domanda", "detail": f"Il bando è riservato a «{who}»: non a un'impresa come la tua."})
    return out
