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
    {"label": "agricoltura, pesca e agroalimentare", "rx": r"agricol|agroalimentar|zootecn|allevament|\bpesca\b|acquacoltura|forestal|vitivinicol|\bismea\b|\bmasaf\b|ministero dell.agricoltura|\bpsr\b|\bfeasr\b|filiera del vino",
     "ateco": ["01", "02", "03", "10", "11", "12", "55"]},
    {"label": "semiconduttori ed elettronica", "rx": r"semiconduttor|microelettronic|\bchips?\b", "ateco": ["26", "27", "28", "62"]},
    {"label": "turismo e ricettività", "rx": r"turism|ricettiv|albergh|agenzie di viaggio|tour operator|termal|stabilimenti balneari", "ateco": ["55", "56", "79", "90", "91", "92", "93", "96"]},
    {"label": "cultura, cinema e spettacolo", "rx": r"cinema|audiovisiv|ministero della cultura|ad alta voce|lettura|spettacolo dal vivo|teatr|musei|editoria|culturali e creative|filiera del libro|\blibrerie\b",
     "ateco": ["58", "59", "60", "73", "74", "90", "91", "92", "93", "4761", "4762"]},
    {"label": "sanità e assistenza", "rx": r"sanitari[ao]|socio-?sanitar|ospedal|assistenza sociale|farmacie", "ateco": ["21", "32", "86", "87", "88", "4773", "4774"]},
    {"label": "ricerca industriale e produzione", "rx": r"ricerca industriale|sviluppo sperimentale|\bhorizon\b|\btrl\b|ricerca e sviluppo|ricerca,? sviluppo e innovazione|progetti di ricerca|contratti? di sviluppo|programmi? di sviluppo industriale",
     "ateco": _MANUF + ["35", "36", "37", "38", "39", "58", "59", "60", "61", "62", "63", "69", "70", "71", "72", "73", "74", "85", "86", "87", "88"]},
    {"label": "sport", "rx": r"impianti sportivi|natator|oratori|societ[aà] sportive|palestr|\bsport\b", "ateco": ["93", "85"]},
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


# --- enti locali: un bando di un Comune, di un GAL, di un'Unione dei comuni o di una Camera di commercio vale solo per le imprese di quel territorio.
# Se il nome non si colloca (il Comune non è un capoluogo noto) e la scheda ufficiale non dice la regione, il bando NON si propone: prima serviva una prova
# contraria per escluderlo, ora serve una prova positiva per mostrarlo (un Comune della Basilicata non deve comparire a un'impresa abruzzese).
_LOCAL_ENTITY = re.compile(r"(?<![a-z])(comune|unione dei comuni|unione montana|comunita montana|municipio|gruppo di azione locale|gal|camera di commercio|cciaa)(?![a-z])\s*(?:di |del |della |dei |delle )?([a-z' ]{0,60})")
_PLACE_STOP = {"bando", "bandi", "avviso", "avvisi", "contributi", "contributo", "per", "a", "al", "sostegno", "misure", "misura", "incentivi", "incentivo", "erogazione", "concessione", "e", "ed",
               "il", "la", "le", "lo", "in", "agevolazioni", "fondo", "progetto", "anno", "occupazione", "territorio", "imprese", "attivita", "commerciali", "economiche", "nuove",
               "voucher", "sovvenzioni", "finanziamenti", "economico", "sviluppo", "rilancio", "interventi", "intervento", "programma"}


def local_entity(name: str, issuer: str) -> Optional[str]:
    """«Comune di Corleto Perticara», «GAL Sulcis»…: l'ente locale nominato dal bando (in parole semplici), oppure None."""
    m = _LOCAL_ENTITY.search(_fold(f"{name} {issuer}"))
    if not m:
        return None
    words = []
    for w in m.group(2).split():
        if w in _PLACE_STOP or w.isdigit():
            break
        words.append(w)
    kind = {"cciaa": "Camera di commercio", "gal": "GAL"}.get(m.group(1), m.group(1).capitalize())
    return (kind + (" di " if kind in ("Comune", "Municipio", "Camera di commercio") else " ") + " ".join(words).title()).strip() if words else kind


def locality_fails(name: str, issuer: str, meta: Optional[Dict[str, Any]], profile: Dict[str, Any]) -> List[Dict[str, str]]:
    """Un bando di un ente locale si propone solo se il suo territorio è la regione dell'impresa: dal nome (capoluoghi e province) o dalla scheda ufficiale."""
    if regions_in(f"{name} {issuer}"):
        return []                                                     # il territorio si legge dal nome: decide il controllo «Territorio»
    entity = local_entity(name, issuer)
    if not entity:
        return []
    listed = [str(x).lower() for x in ((meta or {}).get("regions") or [])]
    region = profile.get("region")
    if listed:
        return []                                                     # la scheda ufficiale dice la regione: decide meta_fails (esclude se non è la tua)
    where = f" ({region})" if region else ""
    return [{"id": "territory", "label": "Territorio",
             "detail": f"È un bando di un ente locale ({entity}) e non risulta nella tua regione{where}: vale solo per le imprese di quel territorio, per questo non lo propongo."}]


def in_region(name: str, issuer: str, meta: Optional[Dict[str, Any]], region: Optional[str]) -> bool:
    """Prova POSITIVA che il bando riguarda la regione dell'impresa: la regione (o una sua provincia o capoluogo) nel nome o nell'ente, oppure nella scheda ufficiale."""
    if not region:
        return False
    if region in regions_in(f"{name} {issuer}"):
        return True
    return region.lower() in [str(x).lower() for x in ((meta or {}).get("regions") or [])]


def text_fails(name: str, issuer: str, applicants: str, profile: Dict[str, Any], meta: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
    """Esclusioni dai testi del bando: territorio (anche da provincia o da un ente locale), settore nominato, soggetti ammessi."""
    out: List[Dict[str, str]] = []
    region, ateco = profile.get("region"), profile.get("ateco_code")
    named = regions_in(f"{name} {issuer}")
    if named and region and region not in named:
        out.append({"id": "territory", "label": "Territorio", "detail": f"Bando di {' / '.join(sorted(named))}; la tua sede è in {region}."})
    out += locality_fails(name, issuer, meta, profile)
    bad = sector_fails(f"{name} {issuer} {applicants}", ateco)
    if bad:
        out.append({"id": "sector", "label": "Settore", "detail": f"Il bando è rivolto a: {', '.join(bad)}. Il tuo codice ATECO {ateco} non rientra."})
    who = applicant_fails(f"{name} {applicants}")
    if who:
        out.append({"id": "applicant", "label": "Chi può presentare domanda", "detail": f"Il bando è riservato a «{who}»: non a un'impresa come la tua."})
    return out


# --- impresa giovane: «costituite da non più di 60 mesi», «compagine a prevalenza giovanile o femminile» (ON Tasso Zero, Smart&Start, autoimpiego…)
_AGE_LIMIT = re.compile(r"(?:costituit[ea]|iscritt[ea] al registro delle imprese|attiv[ea])\s+da\s+(?:non\s+pi[uù]\s+di|meno\s+di|al\s+massimo|massimo|non\s+oltre)\s+(\d{1,3})\s+(mesi|anni)", re.I)
_AGE_LIMIT_2 = re.compile(r"entro\s+(?:i\s+)?(\d{1,3})\s+(mesi|anni)\s+dalla\s+(?:data\s+di\s+)?costituzione", re.I)
_NEW_COMPANY_NAME = re.compile(r"(?<![a-z])(nuove imprese|nuova impresa|neo-?impres\w*|imprese neocostituite|neocostituit\w*|autoimpiego|autoimprenditorialit\w*)(?![a-z])")
_TEAM = re.compile(r"(compagine|soci|composte|costituite|partecipat\w*|titolar\w*)[^.;]{0,160}?(prevalen\w*|maggioranza|oltre la met[aà]|totalmente|interamente)", re.I)
_TEAM_BONUS = re.compile(r"premial|punteggi|priorit|maggiorazion|\briserva\b|quota riservata|incremento", re.I)
_TEAM_RULE = re.compile(r"compagine|compost[ae]|riservat|esclusivamente|soltanto|devono essere|deve essere", re.I)
_TEAM_ALSO = re.compile(r"\b(comprese|incluse|inclusi|compresi)\b", re.I)


def founding_checks(texts: List[str], profile: Dict[str, Any], today=None) -> List[Dict[str, Any]]:
    """Requisiti sull'impresa stessa, letti nel testo: da quanto è costituita e chi sono i soci. Ogni controllo dice la frase da cui viene.

    FAIL solo se il dato del profilo smentisce il requisito scritto (un'impresa del 2010 e un bando «costituite da non più di 60 mesi»).
    Se il dato manca, il controllo è da chiarire (e il bando resta «da verificare», mai sommato). Se il testo non lo dice, non si inventa un limite."""
    from datetime import date as _date
    today = today or _date.today()
    out: List[Dict[str, Any]] = []
    status = profile.get("company_status") or "COSTITUITA"
    joined = " ".join(t for t in texts if t)
    m = _AGE_LIMIT.search(joined) or _AGE_LIMIT_2.search(joined)
    founded = profile.get("founded_year")
    if m and status != "DA_COSTITUIRE":
        n, unit = int(m.group(1)), m.group(2).lower()
        limit_m = n * 12 if unit.startswith("ann") else n
        said = f"«{_sentence_around(joined, m.start())}»"
        if not founded:
            out.append({"id": "company_age", "label": "Età dell'impresa", "decisive": True, "result": "UNKNOWN", "missing": "founded_year",
                        "detail": f"Il bando è per imprese costituite da non più di {n} {unit}: indica l'anno di costituzione nel profilo. {said}"})
        else:
            youngest = (today.year - int(founded) - 1) * 12 + today.month        # costituita il 31 dicembre di quell'anno: l'età più bassa possibile
            oldest = (today.year - int(founded)) * 12 + today.month              # costituita il 1° gennaio
            if youngest > limit_m:
                out.append({"id": "company_age", "label": "Età dell'impresa", "decisive": True, "result": "FAIL",
                            "detail": f"Il bando è per imprese costituite da non più di {n} {unit}; la tua è del {founded}. {said}"})
            elif oldest <= limit_m:
                out.append({"id": "company_age", "label": "Età dell'impresa", "decisive": True, "result": "OK", "detail": f"Costituita nel {founded}: entro i {n} {unit} richiesti."})
            else:
                out.append({"id": "company_age", "label": "Età dell'impresa", "decisive": True, "result": "UNKNOWN",
                            "detail": f"Il bando chiede al massimo {n} {unit} dalla costituzione e la tua impresa è del {founded}: conta la data esatta di costituzione."})
    elif not m and status != "DA_COSTITUIRE" and _NEW_COMPANY_NAME.search(_fold(" ".join(texts[:2]))):
        old = f" La tua è del {founded}." if founded else ""
        out.append({"id": "company_age", "label": "Età dell'impresa", "decisive": True, "result": "UNKNOWN", **({} if founded else {"missing": "founded_year"}),
                    "detail": f"Il bando è per nuove imprese ma il testo letto non dice entro quanti anni dalla costituzione.{old} Va letto nel bando prima di contarlo."})
    for sent in re.split(r"(?<=[.;])\s+", joined):
        if not _TEAM.search(sent) or _TEAM_BONUS.search(sent) or not _TEAM_RULE.search(sent) or _TEAM_ALSO.search(sent):
            continue                                        # «comprese le imprese femminili» o un punteggio in più non sono un requisito
        low = sent.lower()
        young = bool(re.search(r"giovan|under\s*35|35 anni|36 anni", low))
        women = bool(re.search(r"donne|femminil", low))
        if not (young or women):
            continue
        age, fem = profile.get("founders_age"), profile.get("women_majority")
        ok_young = None if age is None else age == "U35"
        ok_women = None if fem is None else bool(fem)
        need = [x for x, on in ((ok_young, young), (ok_women, women)) if on]
        said = f"«{sent.strip()[:220]}»"
        who = " o ".join(w for w, on in (("giovani", young), ("donne", women)) if on)
        if any(x is True for x in need):
            out.append({"id": "team", "label": "Soci", "decisive": True, "result": "OK", "detail": f"La compagine richiesta ({who}) corrisponde al profilo."})
        elif all(x is False for x in need):
            out.append({"id": "team", "label": "Soci", "decisive": True, "result": "FAIL", "detail": f"Il bando chiede una compagine in prevalenza di {who}: il profilo dice di no. {said}"})
        else:
            missing = [k for k, on, v in (("founders_age", young, ok_young), ("women_majority", women, ok_women)) if on and v is None]
            out.append({"id": "team", "label": "Soci", "decisive": True, "result": "UNKNOWN", "missing": missing[0] if missing else None,
                        "detail": f"Il bando chiede una compagine in prevalenza di {who}: indicalo nel profilo. {said}"})
        break
    return out


def _sentence_around(text: str, pos: int) -> str:
    start = max(text.rfind(".", 0, pos), text.rfind(";", 0, pos)) + 1
    end_candidates = [i for i in (text.find(".", pos), text.find(";", pos)) if i != -1]
    end = min(end_candidates) if end_candidates else len(text)
    return text[start:end].strip()[:220]


# --- segnali degli studi: il giudizio sbaglia? Si registra, un manager decide se aggiungere una parola al dizionario
def record_signal(owner: str, bando_id: str, signal: str, engine_fit: Optional[str], profile: Dict[str, Any]) -> Dict[str, Any]:
    """«Non è per questa azienda» o «invece è per lei», in forma anonima (l'utente è un codice, l'azienda solo ATECO a due cifre e regione). Una volta per utente e bando."""
    import hashlib
    from app.core import events
    from app.core.db import connect
    if signal not in ("NOT_FOR_ME", "FOR_ME"):
        raise ValueError("Segnale non valido")
    who = hashlib.sha256(f"quanto-signal|{owner.split('#')[0]}".encode()).hexdigest()[:12]
    division = _digits(profile.get("ateco_code"))[:2] or None
    with connect() as conn:
        if conn.execute("SELECT 1 FROM bandi WHERE bando_id=?", (bando_id,)).fetchone() is None:
            raise KeyError(bando_id)
        conn.execute("INSERT INTO relevance_signals (bando_id, owner_hash, signal, engine_fit, ateco_division, region, created_at) VALUES (?,?,?,?,?,?,?) "
                     "ON CONFLICT (bando_id, owner_hash, signal) DO UPDATE SET engine_fit=excluded.engine_fit, ateco_division=excluded.ateco_division, region=excluded.region, created_at=excluded.created_at",
                     (bando_id, who, signal, engine_fit, division, profile.get("region"), events.now_iso()))
    events.record("relevance.signal", f"Segnale di pertinenza {signal} su {bando_id}", actor="studio", bando_id=bando_id)
    return {"ok": True}


def withdraw_signal(owner: str, bando_id: str) -> Dict[str, Any]:
    """Annulla la segnalazione di questo utente su questo bando (qualunque fosse): il conteggio anonimo torna come prima."""
    import hashlib
    from app.core import events
    from app.core.db import connect
    who = hashlib.sha256(f"quanto-signal|{owner.split('#')[0]}".encode()).hexdigest()[:12]
    with connect() as conn:
        n = conn.execute("DELETE FROM relevance_signals WHERE bando_id=? AND owner_hash=?", (bando_id, who)).rowcount
    if n:
        events.record("relevance.signal", f"Segnalazione di pertinenza annullata su {bando_id}", actor="studio", bando_id=bando_id)
    return {"ok": True, "removed": int(n or 0)}


def signal_summary(min_studios: int = 1) -> List[Dict[str, Any]]:
    """Per il Quartier Generale: i bandi su cui gli studi non sono d'accordo con il giudizio, con quanti studi e per quali settori."""
    from app.core.db import connect
    with connect() as conn:
        rows = conn.execute("SELECT s.bando_id, b.name, s.signal, COUNT(*) AS studios, MAX(s.engine_fit) AS engine_fit FROM relevance_signals s LEFT JOIN bandi b ON b.bando_id=s.bando_id "
                            "GROUP BY s.bando_id, b.name, s.signal HAVING COUNT(*) >= ? ORDER BY COUNT(*) DESC, s.bando_id LIMIT 100", (min_studios,)).fetchall()
    return [{"bando_id": r["bando_id"], "name": r["name"], "signal": r["signal"], "studios": int(r["studios"]), "engine_fit": r["engine_fit"]} for r in rows]
