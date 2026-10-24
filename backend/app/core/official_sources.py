"""Registro delle fonti ufficiali da cui arrivano i bandi e le agevolazioni, e raccoglitore generico delle loro pagine.

Perché esiste: il catalogo nasceva da due sole mappe del sito (incentivi.gov.it e Invitalia). Qui ogni ente che pubblica bandi (ministeri e agenzie nazionali,
le 20 Regioni e le loro finanziarie, le Camere di commercio, l'Unione europea) ha una riga con indirizzo, tipo e stato di lettura.

Cosa fa il raccoglitore, e cosa NON fa:
- parte dalla pagina dell'ente, trova i collegamenti che nominano un bando / avviso / contributo / incentivo e li iscrive nel catalogo con il testo ESATTO del collegamento
  come nome e l'ente come origine; non scrive date, importi o requisiti (quelli si leggono dopo, dalla pagina o dal documento ufficiale);
- scarta gare d'appalto, concorsi, graduatorie, delibere e simili: non sono agevolazioni per le imprese;
- se un sito non risponde, o carica i contenuti con JavaScript (illeggibili da un server), lo dice: lo stato resta visibile e nessuna voce viene inventata.
"""
from __future__ import annotations

import re
import time
from datetime import date
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Any, Dict, Iterable, List, Optional, Tuple

from app.core import events, research
from app.core.db import connect

NAZ, AGENZIA, REGIONE, UE, CAMERE = "NAZIONALE", "AGENZIA", "REGIONE", "UE", "CAMERE"
LEVEL_LABEL = {NAZ: "Ministeri e istituzioni nazionali", AGENZIA: "Agenzie, enti e fondi nazionali", REGIONE: "Regioni e province autonome (e loro finanziarie)",
               UE: "Unione europea", CAMERE: "Camere di commercio"}


def _s(id_: str, name: str, level: str, home: str, region: Optional[str] = None, hubs: Optional[List[str]] = None, topic: str = "", note: str = "", manual: bool = False) -> Dict[str, Any]:
    return {"id": id_, "name": name, "level": level, "home": home, "region": region, "hubs": hubs or [], "topic": topic, "note": note, "manual": manual}


# I siti sono stati provati uno per uno il 24/10/2026 (vedi «checked» nello stato). Gli indirizzi «hubs» sono pagine-elenco dei bandi, se note: senza, si parte dalla home.
SOURCES: List[Dict[str, Any]] = [
    # -------- nazionali
    _s("mimit", "Ministero delle Imprese e del Made in Italy", NAZ, "https://www.mimit.gov.it/it/incentivi", topic="imprese, innovazione, transizione"),
    _s("lavoro", "Ministero del Lavoro e delle Politiche Sociali", NAZ, "https://www.lavoro.gov.it/", topic="lavoro, assunzioni"),
    _s("masaf", "Ministero dell'Agricoltura (MASAF)", NAZ, "https://www.masaf.gov.it/", topic="agricoltura, pesca, filiere"),
    _s("mase", "Ministero dell'Ambiente e della Sicurezza Energetica", NAZ, "https://www.mase.gov.it/", topic="ambiente, energia"),
    _s("cultura", "Ministero della Cultura", NAZ, "https://cultura.gov.it/", topic="cultura, cinema, spettacolo"),
    _s("turismo", "Ministero del Turismo", NAZ, "https://www.ministeroturismo.gov.it/", topic="turismo"),
    _s("mur", "Ministero dell'Università e della Ricerca", NAZ, "https://www.mur.gov.it/it", topic="ricerca, innovazione"),
    _s("innovazione", "Dipartimento per la trasformazione digitale", NAZ, "https://innovazione.gov.it/", topic="digitale"),
    _s("giovani", "Dipartimento per le Politiche Giovanili", NAZ, "https://www.politichegiovanili.gov.it/", topic="giovani"),
    _s("paripp", "Dipartimento per le Pari Opportunità", NAZ, "https://www.pariopportunita.gov.it/", topic="imprenditoria femminile, pari opportunità"),
    _s("sport", "Dipartimento per lo Sport", NAZ, "https://www.sport.governo.it/", topic="sport"),
    _s("italiadomani", "Italia Domani (PNRR) - bandi e avvisi", NAZ, "https://italiadomani.gov.it/it/bandi-e-avvisi.html", topic="PNRR"),
    _s("coesione", "Agenzia per la Coesione Territoriale", NAZ, "https://www.agenziacoesione.gov.it/", topic="fondi di coesione"),
    _s("politichecoesione", "Dipartimento per le Politiche di Coesione", NAZ, "https://politichecoesione.governo.it/", topic="fondi di coesione, Sud"),
    _s("garanziagiovani", "Garanzia Giovani", NAZ, "https://www.garanziagiovani.gov.it/", topic="giovani, lavoro"),
    _s("gazzetta", "Gazzetta Ufficiale", NAZ, "https://www.gazzettaufficiale.it/", topic="norme e decreti", note="elenco dei provvedimenti: le norme si leggono dai documenti di ogni bando"),
    # -------- agenzie, enti e fondi nazionali
    _s("invitalia", "Invitalia", AGENZIA, "https://www.invitalia.it/", hubs=["https://www.invitalia.it/incentivi-e-strumenti"], topic="imprese, startup, Sud",
       note="già raccolta dalla mappa del sito: ogni scheda è nel catalogo"),
    _s("incentivi", "incentivi.gov.it (portale nazionale degli incentivi)", AGENZIA, "https://www.incentivi.gov.it/", topic="tutti: nazionali, regionali, camerali",
       note="già raccolta dalla mappa del sito: contiene anche molte misure regionali e delle Camere di commercio"),
    _s("simest", "SIMEST", AGENZIA, "https://www.simest.it/", hubs=["https://www.simest.it/finanziamenti"], topic="export, internazionalizzazione"),
    _s("mcc", "Fondo di garanzia per le PMI (Mediocredito Centrale)", AGENZIA, "https://www.fondidigaranzia.mcc.it/", topic="garanzia sul credito",
       note="il sito non risponde da tutte le reti: lo riprovo ad ogni controllo"),
    _s("gse", "GSE - Gestore dei Servizi Energetici", AGENZIA, "https://www.gse.it/servizi-per-te", topic="energia, rinnovabili, conto termico"),
    _s("enea", "ENEA - efficienza energetica", AGENZIA, "https://www.efficienzaenergetica.enea.it/", topic="efficienza energetica, detrazioni"),
    _s("ismea", "ISMEA", AGENZIA, "https://www.ismea.it/", topic="agricoltura, credito agricolo"),
    _s("inps", "INPS", AGENZIA, "https://www.inps.it/it/it.html", topic="sgravi contributivi, bonus assunzioni", manual=True,
       note="portale di servizi (pensioni, prestazioni): gli sgravi per le assunzioni sono già inseriti a mano e verificati nelle Agevolazioni"),
    _s("anpal", "ANPAL", AGENZIA, "https://www.anpal.gov.it/", topic="politiche attive del lavoro"),
    _s("inail", "INAIL", AGENZIA, "https://www.inail.it/portale/it.html", topic="sicurezza sul lavoro (bandi ISI)"),
    _s("ice", "ICE - Agenzia per la promozione all'estero", AGENZIA, "https://www.ice.it/it/", topic="export", note="certificato del sito non riconosciuto da tutte le reti"),
    _s("cdp", "Cassa Depositi e Prestiti", AGENZIA, "https://www.cdp.it/sitoCDP/it/home.page", topic="finanza agevolata"),
    _s("agenziaentrate", "Agenzia delle Entrate - crediti d'imposta", AGENZIA, "https://www.agenziaentrate.gov.it/portale/web/guest/agevolazioni", topic="crediti d'imposta"),
    _s("sace", "SACE", AGENZIA, "https://www.sace.it/", topic="garanzie, export"),
    _s("fondimpresa", "Fondimpresa (formazione continua)", AGENZIA, "https://www.fondimpresa.it/", topic="formazione finanziata dei dipendenti"),
    _s("fonter", "Fon.Ter (terziario: commercio, turismo, servizi)", AGENZIA, "https://www.fonter.it/", topic="formazione finanziata dei dipendenti"),
    _s("fondartigianato", "Fondartigianato", AGENZIA, "https://www.fondartigianato.it/", topic="formazione finanziata nell'artigianato"),
    _s("fondoforte", "For.Te. (fondo paritetico del terziario)", AGENZIA, "https://www.fondoforte.it/", topic="formazione finanziata dei dipendenti"),
    _s("unioncamere", "Unioncamere", CAMERE, "https://www.unioncamere.gov.it/", topic="sistema delle Camere di commercio"),
    _s("pid", "Punto Impresa Digitale (Camere di commercio)", CAMERE, "https://www.puntoimpresadigitale.camcom.it/", topic="digitale, voucher I4.0"),
    _s("camcom", "Camere di commercio (portale nazionale)", CAMERE, "https://www.camcom.gov.it/", topic="contributi alle imprese del territorio",
       note="i bandi delle singole Camere sono in buona parte già nel catalogo di incentivi.gov.it"),
    # -------- Unione europea
    _s("ue_ft", "EU Funding & Tenders Portal", UE, "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/home", topic="tutti i programmi europei",
       note="è un'applicazione JavaScript: serve la sua interfaccia dati, non ancora collegata"),
    _s("cordis", "CORDIS", UE, "https://cordis.europa.eu/", topic="ricerca e innovazione (Horizon Europe)"),
    _s("eic", "European Innovation Council", UE, "https://eic.ec.europa.eu/", topic="innovazione, startup"),
    _s("erasmus", "Erasmus+ Italia", UE, "https://www.erasmusplus.it/", topic="giovani, formazione, mobilità"),
    _s("een", "Enterprise Europe Network Italia", UE, "https://een-italia.eu/", topic="PMI, internazionalizzazione"),
    _s("life", "Programma LIFE (CINEA)", UE, "https://cinea.ec.europa.eu/programmes/life_en", topic="ambiente, clima"),
    _s("eif", "Fondo europeo per gli investimenti (EIF)", UE, "https://www.eif.org/", topic="garanzie e capitale di rischio"),
    # -------- Regioni (sito istituzionale, finanziaria regionale, programma europeo regionale)
    _s("abruzzo", "Regione Abruzzo", REGIONE, "https://www.regione.abruzzo.it/", "Abruzzo"),
    _s("abruzzo_fesr", "Abruzzo - Programma FESR", REGIONE, "https://fesr.regione.abruzzo.it/", "Abruzzo", note="non risolto da tutte le reti"),
    _s("basilicata", "Regione Basilicata", REGIONE, "https://www.regione.basilicata.it/", "Basilicata"),
    _s("basilicata_eu", "Basilicata Europa", REGIONE, "https://europa.basilicata.it/", "Basilicata", note="certificato del sito non riconosciuto da tutte le reti"),
    _s("calabria", "Regione Calabria", REGIONE, "https://www.regione.calabria.it/", "Calabria"),
    _s("calabria_eu", "Calabria Europa", REGIONE, "https://calabriaeuropa.regione.calabria.it/", "Calabria"),
    _s("campania", "Regione Campania", REGIONE, "https://www.regione.campania.it/", "Campania"),
    _s("campania_fesr", "Campania - Programma FESR", REGIONE, "https://porfesr.regione.campania.it/", "Campania"),
    _s("emilia", "Emilia-Romagna - Imprese", REGIONE, "https://imprese.regione.emilia-romagna.it/", "Emilia-Romagna"),
    _s("emilia_fesr", "Emilia-Romagna - Fondo europeo FESR", REGIONE, "https://fesr.regione.emilia-romagna.it/", "Emilia-Romagna"),
    _s("fvg", "Regione Friuli Venezia Giulia", REGIONE, "https://www.regione.fvg.it/", "Friuli Venezia Giulia"),
    _s("lazio", "Regione Lazio", REGIONE, "https://www.regione.lazio.it/", "Lazio"),
    _s("lazio_innova", "Lazio Innova", REGIONE, "https://www.lazioinnova.it/", "Lazio", hubs=["https://www.lazioinnova.it/bandi/"]),
    _s("liguria", "Regione Liguria", REGIONE, "https://www.regione.liguria.it/", "Liguria"),
    _s("filse", "FILSE (finanziaria della Liguria)", REGIONE, "https://www.filse.it/", "Liguria"),
    _s("lombardia_bandi", "Lombardia - Bandi online", REGIONE, "https://www.bandi.regione.lombardia.it/", "Lombardia", note="applicazione JavaScript: le voci non sono leggibili da un server"),
    _s("lombardia", "Regione Lombardia", REGIONE, "https://www.regione.lombardia.it/", "Lombardia"),
    _s("marche", "Regione Marche", REGIONE, "https://www.regione.marche.it/", "Marche"),
    _s("marche_bandi", "Marche - Bandi", REGIONE, "https://bandi.regione.marche.it/", "Marche", note="applicazione JavaScript: le voci non sono leggibili da un server"),
    _s("molise", "Regione Molise", REGIONE, "https://www.regione.molise.it/", "Molise", note="certificato del sito non riconosciuto da tutte le reti"),
    _s("piemonte", "Regione Piemonte", REGIONE, "https://www.regione.piemonte.it/", "Piemonte"),
    _s("piemonte_bandi", "Piemonte - Bandi", REGIONE, "https://bandi.regione.piemonte.it/", "Piemonte"),
    _s("finpiemonte", "Finpiemonte", REGIONE, "https://www.finpiemonte.it/", "Piemonte"),
    _s("puglia", "Regione Puglia", REGIONE, "https://www.regione.puglia.it/", "Puglia"),
    _s("puglia_sistema", "Sistema Puglia", REGIONE, "https://www.sistema.puglia.it/", "Puglia", note="certificato del sito non riconosciuto da tutte le reti"),
    _s("sardegna", "Regione Sardegna", REGIONE, "https://www.regione.sardegna.it/", "Sardegna"),
    _s("sardegna_impresa", "Sardegna Impresa", REGIONE, "https://www.sardegnaimpresa.eu/", "Sardegna", hubs=["https://www.sardegnaimpresa.eu/it/bandi"]),
    _s("sicilia", "Regione Siciliana", REGIONE, "https://www.regione.sicilia.it/", "Sicilia"),
    _s("sicilia_eu", "Euro Info Sicilia", REGIONE, "https://www.euroinfosicilia.it/", "Sicilia"),
    _s("toscana", "Regione Toscana", REGIONE, "https://www.regione.toscana.it/", "Toscana"),
    _s("sviluppo_toscana", "Sviluppo Toscana", REGIONE, "https://www.sviluppo.toscana.it/", "Toscana"),
    _s("trento", "Provincia autonoma di Trento", REGIONE, "https://www.provincia.tn.it/", "Trentino-Alto Adige"),
    _s("bolzano", "Provincia autonoma di Bolzano", REGIONE, "https://www.provincia.bz.it/", "Trentino-Alto Adige"),
    _s("umbria", "Regione Umbria", REGIONE, "https://www.regione.umbria.it/", "Umbria"),
    _s("sviluppumbria", "Sviluppumbria", REGIONE, "https://www.sviluppumbria.it/", "Umbria"),
    _s("vda", "Regione Valle d'Aosta", REGIONE, "https://www.regione.vda.it/", "Valle d'Aosta"),
    _s("finaosta", "Finaosta", REGIONE, "https://www.finaosta.com/", "Valle d'Aosta", note="il sito rifiuta le richieste automatiche (403)"),
    _s("sviluppo_campania", "Sviluppo Campania", REGIONE, "https://www.sviluppocampania.it/", "Campania"),
    _s("irfis", "IRFIS FinSicilia", REGIONE, "https://www.irfis.it/", "Sicilia"),
    _s("puglia_sviluppo", "Puglia Sviluppo", REGIONE, "https://www.pugliasviluppo.eu/", "Puglia"),
    _s("finlombarda", "Finlombarda", REGIONE, "https://www.finlombarda.it/", "Lombardia"),
    _s("sfirs", "SFIRS (finanziaria della Sardegna)", REGIONE, "https://www.sfirs.it/", "Sardegna"),
    _s("finmolise", "Finmolise", REGIONE, "https://www.finmolise.it/", "Molise"),
    _s("emilia_bandi", "Emilia-Romagna - Bandi", REGIONE, "https://bandi.regione.emilia-romagna.it/", "Emilia-Romagna"),
    _s("veneto", "Regione Veneto", REGIONE, "https://www.regione.veneto.it/", "Veneto"),
    _s("veneto_sviluppo", "Veneto Sviluppo", REGIONE, "https://www.venetosviluppo.it/", "Veneto"),
]
BY_ID = {s["id"]: s for s in SOURCES}
HARVESTED_BY_OTHER = {"invitalia", "incentivi"}          # le leggono già le mappe del sito (discovery.CATALOGS)
OFFICIAL_HOSTS = tuple(sorted({research.host_of(h) for s in SOURCES for h in [s["home"], *s["hubs"]] if research.host_of(h)}))


def is_official_host(host: str) -> bool:
    return any(host == h or host.endswith("." + h.removeprefix("www.")) or h.removeprefix("www.") == host for h in OFFICIAL_HOSTS)


# ------------------------------------------------------------------------------------------------ che cosa è un bando
_POSITIVE = re.compile(r"\b(bando|bandi|avviso pubblico|avviso|contribut\w*|incentiv\w*|voucher|finanziament\w*|agevolazion\w*|sovvenzion\w*|sostegno|sostegni|bonus|"
                       r"credito d.imposta|crediti d.imposta|call for|invito a presentare|misura|fondo|fondi|sgravi\w*|esonero|decontribuzione)\b", re.I)
# non sono agevolazioni per le imprese: gare, concorsi, elenchi, immobili, atti di procedura, enti pubblici, famiglie
_NEGATIVE = re.compile(r"\b(gara|gare|appalt\w*|fornitur\w*|affidament\w*|concors\w*|selezione (?:del|di|pubblica)|assunzion\w* (?:di|a tempo)|graduatori\w*|aggiudica\w*|esit[oi]|"
                       r"determin\w*|delibera\w*|verbale|nomina|incaric\w*|trasparenza|privacy|cookie|albo|elenco (?:fornitori|operatori|professionisti)|rettifica|sorteggio|"
                       r"borsa di studio|borse di studio|tirocini\w*|alloggi\w*|edilizia residenziale|servizio civile|calendario|comunicato|newsletter|rassegna|"
                       r"manifestazione di interesse (?:per|a partecipare)|procedura negoziata|lavori pubblici|nucleo di valutazione|commissione|seduta|ordine del giorno|statuto|"
                       r"bilancio (?:di|del) (?:previsione|esercizio)|avviso d.asta|asta|concessione d.uso|comodato|immobil\w*|elenco regionale|iscrizione all.elenco|mediator\w*|"
                       r"piano strutturale|consultazion\w*|circolar\w*|liquidazione|rendicontazione|faq|chiusura sportello|prorogat\w*|report|dismissione|ammessi|ammesse|"
                       r"aggiornamento|ai comuni|agli enti locali|enti locali|amministrazioni|pro loco|scuole|famiglie|cittadini|pensione|pensionati|previdenz\w*|tributi|"
                       r"tariffar\w*|canone|assistenza|disabilit\w*|sanit\w*|ufficio|uffici|direzione generale|organigramma|convenzione|protocollo d.intesa|decret[oi]|d\.d\.|"
                       r"reclutamento|candidature|profilo|webinar|truffe|evento|eventi|convegno|seminario|selezionat[oie]|autorizzazion\w*|variante|connessione|procedimento|eolico|guida|"
                       r"domande nel primo giorno|avviso di ricerca|fondi di mutualit\w*|riassicurazione|autorizzazioni ad agire|patrocinio|area verde|terren\w+|demanio|concessione dell\w*|avviso di selezione|posto di|dirigenzial\w*|personale)\b", re.I)
# parole che da sole formano solo il nome di una sezione del sito («Fondi e finanziamenti europei», «Esplora la sezione Bandi e avvisi»), non di un bando
_NAV_WORDS = set("""bandi bando avvisi avviso incentivi incentivo agevolazioni agevolazione contributi contributo finanziamenti finanziamento fondi fondo europei europa ue opportunita imprese impresa
    sezione esplora altre altri amministrazioni da e di per le i la il lo alla al ai delle dei degli del in evidenza tutti tutte vai vedi leggi scopri archivio aperti chiusi scaduti attivi attivo
    programmazione regionali regionale nazionali nazionale pubblici pubblico strumenti strumento sostegno sostegni misure misura bonus voucher news notizie home cerca altro piu informazioni
    saperne su sul sulla della dello nuovi nuove nuova gli un una d l""".split())
_HUB_TEXT = re.compile(r"^(?:bandi(?: e avvisi| aperti| in corso| per le imprese)?|avvisi e bandi|bandi e finanziamenti|finanziamenti(?: e bandi)?|incentivi(?: e agevolazioni)?|"
                       r"contributi(?: e finanziamenti)?|agevolazioni|bandi di finanziamento|finanza agevolata|per le imprese|imprese|opportunità(?: per le imprese)?|"
                       r"bandi attivi|elenco bandi|tutti i bandi)$", re.I)
_SKIP_URL = re.compile(r"\.(jpe?g|png|gif|svg|webp|zip|rar|mp[34]|css|js|ico|xlsx?|pptx?)(\?|$)|^(mailto|tel|javascript):|facebook\.com|twitter\.com|x\.com/|linkedin\.com|youtube\.com|instagram\.com|"
                       r"/(login|accedi|area-riservata|newsletter|cookie|privacy|sitemap|accessibilit|rss|contatti|search|ricerca|amministrazione-trasparente|bandi-di-gara|bandi-gara|gare)(/|\?|$)|"
                       r"[?&](lang|language)=|cittadini", re.I)


def _words(t: str) -> List[str]:
    return re.findall(r"[a-z]+", research.norm_hay(t))


def _only_section_name(t: str) -> bool:
    w = _words(t)
    return bool(w) and all(x in _NAV_WORDS for x in w)


def clean_title(text: str) -> str:
    """Il testo del collegamento senza gli orpelli della pagina («Per saperne di più su…», data e nome dell'ente davanti, «Scopri di più» in coda)."""
    t = re.sub(r"\s+", " ", text or "").strip(" -–—|:·•")
    t = re.sub(r"^(?:aperto|apertura|conclusione|chiuso|chiusura|scaduto|in arrivo|prossima apertura)\s+\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\s*", "", t, flags=re.I)
    t = re.sub(r"^\d{1,2}/\d{1,2}/\d{4}\s+(?:[\w' ]+/[\w' ]+\s+Informa\s+)?", "", t)
    t = re.sub(r"^(?:per saperne di più su|leggi tutto su|scopri di più su|leggi|scarica|vai a|apri)(?: tutto| il bando| la scheda)?\s*[:\-–]?\s*", "", t, flags=re.I)
    t = re.sub(r"^(?:[Pp]resentazione )?[Dd]omande[^A-Z]{0,90}?(?=(?:Contribut|Bando|Avviso|Voucher|Incentiv|Finanziament|Sostegn|Bonus|Credito|Misura))", "", t)
    t = re.sub(r"\s*(?:scopri (?:di più|qui[\w ]*)|leggi tutto|maggiori informazioni)\s*$", "", t, flags=re.I)
    return t.strip(" -–—|:·•")[:200]


_CLOSED_PREFIX = re.compile(r"^(?:conclusione|chiuso|chiusura|scaduto)\s+\d{1,2}\s+[A-Za-z]{3}\s+\d{4}", re.I)
_PERIOD = re.compile(r"(?<![\d/.-])(?:20)?(\d{2})\s?[-/]\s?(?:20)?(\d{2})(?![\d/.-])")          # «14-20», «2021/2027»; non le date «10/12/2026»


def looks_like_grant(text: str) -> bool:
    if _CLOSED_PREFIX.match((text or "").strip()):
        return False                                                       # il sito stesso dice che è concluso
    t = clean_title(text)
    if not (20 <= len(t) <= 240) or len(t.split()) < 3:
        return False
    if _NEGATIVE.search(t) or not _POSITIVE.search(t) or _only_section_name(t):
        return False
    years = [int(y) for y in re.findall(r"\b(20[0-3]\d)\b", t)] + [2000 + int(b) for a, b in _PERIOD.findall(t) if int(b) >= int(a) >= 10]
    return not (years and max(years) < date.today().year)                  # «Avviso pubblico 2024», «PSC 14-20»: edizione o programmazione passata


def extract_items(page_url: str, links: Iterable[Tuple[str, str]]) -> Tuple[List[Dict[str, str]], List[str]]:
    """Dai collegamenti di una pagina: (voci che sembrano bandi, pagine-elenco da aprire). Solo collegamenti a pagine/documenti dello stesso ente o di un sito ufficiale."""
    items: Dict[str, Dict[str, str]] = {}
    hubs: Dict[str, str] = {}
    page_host = research.host_of(page_url)
    for href, text in links:
        if not href or href.startswith("#"):
            continue
        full = urllib.parse.urljoin(page_url, href.split("#")[0])
        if not full.startswith(("http://", "https://")) or _SKIP_URL.search(full):
            continue
        host = research.host_of(full)
        same = host == page_host or host.removeprefix("www.") == page_host.removeprefix("www.")
        if not (same or research.classify_url(full) == "UFFICIALE" or is_official_host(host)):
            continue
        norm = research.normalize_url(full)
        t = re.sub(r"\s+", " ", text or "").strip()
        is_hub_text = bool(_HUB_TEXT.match(t)) or (len(t) < 60 and not re.search(r"\d", t) and _only_section_name(t) and re.search(r"band|avvis|incentiv|agevolaz|finanziament|contribut", t, re.I) is not None)
        if same and is_hub_text and norm != research.normalize_url(page_url):
            hubs.setdefault(norm, full)
            continue
        if looks_like_grant(t):
            items.setdefault(norm, {"url": full, "title": clean_title(t)})
    return list(items.values()), list(hubs.values())


def _page_links(url: str, timeout: float = 14.0) -> Tuple[Optional[str], List[Tuple[str, str]], Optional[str], int]:
    """(indirizzo finale, collegamenti, errore, byte letti). Un sito che serve solo JavaScript dà zero collegamenti: lo si dice."""
    try:
        raw, final, ctype = research.http_get(url, timeout=timeout, limited=False, accept_error_body=True)
    except research.ResearchError as exc:
        return None, [], str(exc), 0
    if raw[:4] == b"%PDF" or "html" not in ctype and ctype not in ("", "text/plain", "application/xhtml+xml", "text/xml", "application/xml"):
        return final, [], None, len(raw)
    _, _, links = research.html_to_text(research._decode(raw, ctype))
    return final, links, None, len(raw)


def harvest_source(src: Dict[str, Any], max_hubs: int = 4, deadline: Optional[float] = None) -> Dict[str, Any]:
    """Scansiona la pagina dell'ente (e al massimo ``max_hubs`` pagine-elenco collegate) e ne ricava le voci che sembrano bandi. Non scrive nel database."""
    out: Dict[str, Any] = {"source_id": src["id"], "ok": False, "http_error": None, "pages": 0, "links": 0, "items": [], "hubs": []}
    starts = list(dict.fromkeys([*src["hubs"], src["home"]]))
    seen: set = set()
    found: Dict[str, Dict[str, str]] = {}
    queue: List[Tuple[str, int]] = [(u, 0) for u in starts]
    while queue and len(seen) < len(starts) + max_hubs:
        if deadline and time.monotonic() > deadline:
            break
        url, depth = queue.pop(0)
        norm = research.normalize_url(url)
        if norm in seen:
            continue
        seen.add(norm)
        final, links, err, _size = _page_links(url)
        if err:
            if not out["pages"]:
                out["http_error"] = err
            continue
        out["ok"] = True
        out["pages"] += 1
        out["links"] += len(links)
        items, hubs = extract_items(final or url, links)
        for it in items:
            found.setdefault(research.normalize_url(it["url"]), it)
        if depth == 0:
            for h in hubs[:max_hubs]:
                queue.append((h, 1))
                out["hubs"].append(h)
    out["items"] = list(found.values())
    return out


# ------------------------------------------------------------------------------------------------ stato e iscrizione nel catalogo
def _norm_name(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", research.norm_hay(s)).strip()


def save_state(source_id: str, res: Dict[str, Any], inserted: int) -> None:
    now = events.now_iso()
    with connect() as conn:
        conn.execute("INSERT INTO source_checks (source_id, checked_at, ok, http_error, pages, links, found, inserted) VALUES (?,?,?,?,?,?,?,?) "
                     "ON CONFLICT (source_id) DO UPDATE SET checked_at=excluded.checked_at, ok=excluded.ok, http_error=excluded.http_error, pages=excluded.pages, "
                     "links=excluded.links, found=excluded.found, inserted=source_checks.inserted + excluded.inserted",
                     (source_id, now, bool(res["ok"]), res.get("http_error"), res["pages"], res["links"], len(res["items"]), inserted))


def register_items(src: Dict[str, Any], items: List[Dict[str, str]]) -> int:
    """Iscrive nel catalogo le voci nuove (mai quelle già presenti: stesso indirizzo o stesso nome). Ritorna quante sono nuove."""
    from app.core import catalog_job
    if not items:
        return 0
    with connect() as conn:
        existing_names = {_norm_name(r["name"]) for r in conn.execute("SELECT name FROM bandi").fetchall()}
        existing_urls = {research.normalize_url(r["source_url"]) for r in conn.execute("SELECT source_url FROM bandi WHERE source_url IS NOT NULL").fetchall()}
    seed = '{"harvested": true, "source_id": "%s"%s}' % (src["id"], (', "regions": ["%s"]' % src["region"]) if src.get("region") else "")
    rows = []
    for it in items:
        if research.normalize_url(it["url"]) in existing_urls or _norm_name(it["title"]) in existing_names:
            continue
        existing_names.add(_norm_name(it["title"]))
        rows.append((catalog_job._bando_id(it["url"], it["title"]), it["title"], src["name"], it["url"], "CATALOGED", "NOT_STARTED", seed))
    if rows:
        with connect() as conn:
            conn.executemany("INSERT INTO bandi (bando_id, name, issuer, source_url, catalog_status, extraction_status, catalog_meta) VALUES (?,?,?,?,?,?,?) "
                             "ON CONFLICT (bando_id) DO NOTHING", rows)
    return len(rows)


def run(source_ids: Optional[List[str]] = None, budget_s: float = 40.0, workers: int = 8, actor: str = "cron", write: bool = True) -> Dict[str, Any]:
    """Raccoglie dalle fonti indicate (o da tutte quelle non già coperte dalle mappe del sito, le meno recenti per prime) entro il tempo dato."""
    states = {r["source_id"]: r for r in _states()}
    todo = [BY_ID[i] for i in source_ids if i in BY_ID] if source_ids else sorted(
        (s for s in SOURCES if s["id"] not in HARVESTED_BY_OTHER and not s["manual"]), key=lambda s: states.get(s["id"], {}).get("checked_at") or "")
    t0 = time.monotonic()
    deadline = t0 + budget_s
    pool = ThreadPoolExecutor(max_workers=workers)
    futures = {pool.submit(harvest_source, s, 4, deadline): s for s in todo}
    done, pending = wait(futures, timeout=budget_s)
    pool.shutdown(wait=False, cancel_futures=True)
    report: Dict[str, Any] = {"checked": 0, "reachable": 0, "found": 0, "new": 0, "skipped": len(pending), "sources": []}
    for fut in done:
        src = futures[fut]
        try:
            res = fut.result()
        except Exception as exc:  # noqa: BLE001 - una fonte che si rompe non ferma le altre
            res = {"source_id": src["id"], "ok": False, "http_error": type(exc).__name__, "pages": 0, "links": 0, "items": [], "hubs": []}
        new = register_items(src, res["items"]) if write and res["ok"] else 0
        if write:
            save_state(src["id"], res, new)
        report["checked"] += 1
        report["reachable"] += 1 if res["ok"] else 0
        report["found"] += len(res["items"])
        report["new"] += new
        report["sources"].append({"id": src["id"], "ok": res["ok"], "found": len(res["items"]), "new": new, "error": res["http_error"]})
    report["seconds"] = round(time.monotonic() - t0, 1)
    if write and report["checked"]:
        events.record("sources.harvest", f"Controllate {report['checked']} fonti ufficiali: {report['reachable']} rispondono, {report['new']} bandi nuovi nel catalogo", actor=actor,
                      details={k: v for k, v in report.items() if k != "sources"})
    return report


def _states() -> List[Dict[str, Any]]:
    with connect() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM source_checks").fetchall()]


def registry() -> Dict[str, Any]:
    """Il registro con lo stato dell'ultimo controllo e quante voci del catalogo vengono da ciascun ente."""
    states = {r["source_id"]: r for r in _states()}
    with connect() as conn:
        by_issuer = {r["issuer"]: r["n"] for r in conn.execute("SELECT issuer, COUNT(*) n FROM bandi WHERE bando_id LIKE 'CAT-%' AND extraction_status <> 'REJECTED' GROUP BY issuer").fetchall()}
        studied = {r["issuer"]: r["n"] for r in conn.execute("SELECT issuer, COUNT(*) n FROM bandi WHERE bando_id LIKE 'CAT-%' AND extraction_status NOT IN ('NOT_STARTED','REJECTED') GROUP BY issuer").fetchall()}
        total = conn.execute("SELECT COUNT(*) n FROM bandi WHERE bando_id LIKE 'CAT-%' AND extraction_status <> 'REJECTED'").fetchone()["n"]
        read = conn.execute("SELECT COUNT(*) n FROM bandi WHERE bando_id LIKE 'CAT-%' AND meta_at IS NOT NULL AND extraction_status <> 'REJECTED'").fetchone()["n"]
        studied_total = conn.execute("SELECT COUNT(*) n FROM bandi WHERE extraction_status NOT IN ('NOT_STARTED','REJECTED')").fetchone()["n"]
    out = []
    for s in SOURCES:
        st = states.get(s["id"])
        aggregated = s["id"] in HARVESTED_BY_OTHER
        count = by_issuer.get(s["name"], 0) if not aggregated else by_issuer.get("incentivi.gov.it" if s["id"] == "incentivi" else "Invitalia", 0)
        if st is None:
            status = "COPERTA" if aggregated else "DA_CONTROLLARE"
        elif aggregated:
            status = "COPERTA"
        elif not st["ok"]:
            status = "NON_RAGGIUNGIBILE"
        elif st["links"] == 0:
            status = "SOLO_JAVASCRIPT"
        elif st["found"] == 0:
            status = "NESSUN_BANDO_TROVATO"
        else:
            status = "LETTA"
        out.append({**s, "status": status, "checked_at": (st or {}).get("checked_at"), "error": (st or {}).get("http_error"), "found": (st or {}).get("found"),
                    "in_catalog": int(count), "studied": int(studied.get(s["name"], 0))})
    return {"sources": out, "levels": LEVEL_LABEL,
            "totals": {"catalog": int(total), "read": int(read), "unread": int(total - read), "studied": int(studied_total),
                       "sources": len(SOURCES), "checked": sum(1 for s in out if s["checked_at"]), "reading": sum(1 for s in out if s["status"] in ("LETTA", "COPERTA"))}}
