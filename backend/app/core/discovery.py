"""Scoperta dei bandi SENZA motore di ricerca (schema FKOS, Ingestion Fonte A, Stadio 1: catalogo continuo delle fonti istituzionali).

Tre canali, tutti su siti ufficiali e tutti leggibili anche da un server cloud (dove i motori gratuiti sono bloccati):

1. **Cataloghi** — le sitemap dei portali che elencano gli incentivi: ``incentivi.gov.it`` (5.900 misure: nazionali, regionali, comunali, CCIAA, GAL) e Invitalia.
   Il nome del bando si confronta, anche in modo approssimativo, con il titolo (ricavato dall'indirizzo) di ogni misura.
2. **Elenchi ufficiali** — le pagine-indice di Invitalia e MIMIT.
3. **Portali per famiglia** — se il nome richiama un programma (Erasmus+, coesione/FSE/FESR/PNRR, PSR/agricoltura, energia, export…) si parte dai portali ufficiali di quel
   programma e si seguono i link che contengono le parole del bando (es. «KA152»), per due salti.

Ogni canale è a tempo: se un sito non risponde si prosegue con gli altri e l'esito resta visibile nella diagnostica.
"""
from __future__ import annotations

import re
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

from app.core import research

CATALOGS: List[Dict[str, Any]] = [
    {"name": "incentivi.gov.it", "site": "https://www.incentivi.gov.it", "sitemap": "https://www.incentivi.gov.it/sitemap.xml", "path": "/it/catalogo/"},
    {"name": "Invitalia", "site": "https://www.invitalia.it", "sitemap": "https://www.invitalia.it/sitemap.xml", "path": "/incentivi-e-strumenti/"},
]
CATALOG_TTL = 6 * 3600
CATALOG_TIMEOUT = 40.0          # le sitemap sono file da ~700 KB ciascuno e da un server cloud possono essere lente
CATALOG_WAIT = 22.0             # oltre questo tempo la ricerca prosegue senza il catalogo (che intanto si completa e resta in cache)
_CACHE: Dict[str, Tuple[float, List[Tuple[str, str]]]] = {}
_LOCK = threading.Lock()

# Portali ufficiali per famiglia di programma: (parole che richiamano la famiglia, pagine di partenza)
PORTALS: List[Tuple[str, List[str]]] = [
    (r"erasmus|\bka\s?\d{3}|eurodesk|scambi giovanili|youth|corpo europeo|solidarietà",
     ["https://www.erasmusplus.it/", "https://www.agenziagiovani.it/", "https://erasmus-plus.ec.europa.eu/it", "https://youth.europa.eu/erasmus-plus_it",
      "https://www.indire.it/erasmus/"]),
    (r"fse|fesr|fsc|coesione|pnrr|pon\b|por\b|next ?generation",
     ["https://www.agenziacoesione.gov.it/", "https://italiadomani.gov.it/", "https://opencoesione.gov.it/", "https://www.mimit.gov.it/it/incentivi"]),
    (r"psr|feasr|pac\b|agricol|rurale|agroaliment|pesca|feampa|ismea",
     ["https://www.reterurale.it/", "https://www.masaf.gov.it/", "https://www.agea.gov.it/", "https://www.ismea.it/"]),
    (r"energia|energetic|conto termico|fotovolta|rinnovabil|transizione|efficientamento|gse",
     ["https://www.gse.it/", "https://www.mase.gov.it/", "https://www.enea.it/"]),
    (r"export|internazional|estero|simest|made in italy|ice\b",
     ["https://www.simest.it/", "https://www.ice.it/", "https://www.esteri.it/it/"]),
    (r"cultur|cinema|film|audiovisiv|teatro|spettacolo|musica|libri|museo",
     ["https://cultura.gov.it/", "https://cinema.cultura.gov.it/"]),
    (r"turismo|turistic",
     ["https://www.ministeroturismo.gov.it/"]),
    (r"lavoro|occupazione|assunzion|apprendistato|formazione|competenze|anpal|inps|decontribuzione",
     ["https://www.lavoro.gov.it/", "https://www.anpal.gov.it/", "https://www.inps.it/it/it.html"]),
    (r"ricerca|innovazione|horizon|cordis|eic|startup|brevett",
     ["https://www.mur.gov.it/it", "https://cordis.europa.eu/", "https://www.mimit.gov.it/it/incentivi"]),
    (r"sport|impianti sportivi",
     ["https://www.sport.governo.it/"]),
    (r"sud|mezzogiorno|autoimpiego|imprenditoria|giovanil|femminil|startup",
     ["https://www.invitalia.it/incentivi-e-strumenti", "https://www.mimit.gov.it/it/incentivi"]),
    (r"sicurezza sul lavoro|inail|infortun",
     ["https://www.inail.it/"]),
    (r"digital|cyber|banda larga|innovazione digitale",
     ["https://innovazione.gov.it/", "https://www.acn.gov.it/"]),
]
# Pagine ufficiali di azioni con sigla (verificate una per una: rispondono 200 e descrivono l'azione)
_PG = "https://erasmus-plus.ec.europa.eu/programme-guide/part-b/"
CODE_PAGES: Dict[str, List[Tuple[str, str]]] = {
    "ka152": [(_PG + "key-action-1/youth-exchanges", "Guida al programma Erasmus+ — KA152 Youth Exchanges (scambi giovanili)")],
    "ka153": [(_PG + "key-action-1/mobility-youth-workers", "Guida al programma Erasmus+ — KA153 Mobility of youth workers")],
    "ka154": [(_PG + "key-action-1/youth-participation-activities", "Guida al programma Erasmus+ — KA154 Youth participation activities")],
    "ka210": [(_PG + "key-action-2/small-scale-partnerships", "Guida al programma Erasmus+ — KA210 Small-scale partnerships")],
    "ka220": [(_PG + "key-action-2/cooperation-partnerships", "Guida al programma Erasmus+ — KA220 Cooperation partnerships")],
}
GENERIC_SEEDS = list(research.DIRECTORIES)
FOCUSED_DEADLINE = 16.0   # secondi per ogni fase della ricerca guidata


# ------------------------------------------------------------------ cataloghi (sitemap)
def _rewrite(loc: str, site: str) -> str:
    """Le sitemap di alcuni portali riportano l'host interno (es. http://incentivi:8080/...): si rimette quello pubblico."""
    p, s = urllib.parse.urlparse(loc), urllib.parse.urlparse(site)
    return urllib.parse.urlunparse((s.scheme, s.netloc, p.path, "", p.query, ""))


def _locs(xml: str) -> List[str]:
    return re.findall(r"<loc>\s*([^<]+?)\s*</loc>", xml)


def _title_from_url(url: str) -> str:
    slug = urllib.parse.unquote(urllib.parse.urlparse(url).path.rstrip("/").rsplit("/", 1)[-1])
    return re.sub(r"[-_]+", " ", slug).strip()


def load_catalog(cat: Dict[str, Any], force: bool = False) -> List[Tuple[str, str]]:
    """[(indirizzo, titolo ricavato dall'indirizzo)] di tutte le misure del catalogo, con cache di alcune ore."""
    with _LOCK:
        hit = _CACHE.get(cat["name"])
        if hit and not force and time.monotonic() - hit[0] < CATALOG_TTL:
            return hit[1]
    raw, _, _ = research.http_get(cat["sitemap"], max_bytes=8_000_000, timeout=CATALOG_TIMEOUT)
    top = _locs(raw.decode("utf-8", errors="replace"))
    children = [c for c in top if c.endswith(".xml") or "sitemap" in c.lower()]
    pages = [top] if not children else []

    def one(child: str) -> List[str]:
        try:
            r2, _, _ = research.http_get(_rewrite(child, cat["site"]), max_bytes=8_000_000, timeout=CATALOG_TIMEOUT)
            return _locs(r2.decode("utf-8", errors="replace"))
        except research.ResearchError:
            return []

    with ThreadPoolExecutor(max_workers=4) as pool:          # le sitemap figlie si scaricano insieme
        pages += [x for x in pool.map(one, children[:8]) if x]
    out: List[Tuple[str, str]] = []
    for locs in pages:
        for loc in locs:
            u = _rewrite(loc, cat["site"])
            if cat["path"] in urllib.parse.urlparse(u).path and not u.endswith(".xml"):
                out.append((u, _title_from_url(u)))
    out = list(dict.fromkeys(out))
    with _LOCK:
        _CACHE[cat["name"]] = (time.monotonic(), out)
    return out


def search_catalogs(name: str, limit: int = 15) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    hits: List[Dict[str, str]] = []
    info: List[Dict[str, Any]] = []
    for cat in CATALOGS:
        entry: Dict[str, Any] = {"channel": f"catalogo {cat['name']}", "items": 0, "matched": 0, "error": None}
        try:
            items = load_catalog(cat)
        except research.ResearchError as exc:
            entry["error"] = str(exc)
            info.append(entry)
            continue
        entry["items"] = len(items)
        scored = []
        for url, title in items:
            s = research.match_score(name, title)
            if s is not None:
                scored.append((s, url, title))
        scored.sort(key=lambda x: (-x[0], len(x[2])))
        entry["matched"] = len(scored)
        info.append(entry)
        hits += [{"url": u, "title": t[:1].upper() + t[1:], "snippet": f"Catalogo ufficiale: {cat['name']}"} for _, u, t in scored[:limit]]
    return hits, info


# ------------------------------------------------------------------ portali per famiglia: ricerca guidata
def seeds_for(name: str) -> List[str]:
    seeds: List[str] = []
    for rx, urls in PORTALS:
        if re.search(rx, name, re.I):
            seeds += urls
    return list(dict.fromkeys(seeds + GENERIC_SEEDS))


def _fetch_links(url: str) -> Tuple[str, List[Tuple[str, str]], Optional[str]]:
    try:
        raw, final, ctype = research.http_get(url, accept_error_body=True)
    except research.ResearchError as exc:
        return url, [], str(exc)
    if not (ctype.startswith("text/") or "html" in ctype or "xml" in ctype or ctype == ""):
        return final, [], None
    _, _, links = research.html_to_text(research._decode(raw, ctype))
    return final, [(urllib.parse.urljoin(final, h.split("#")[0]), t) for h, t in links if h and not h.startswith(("#", "mailto:", "tel:", "javascript:"))], None


def _score_links(name: str, links: List[Tuple[str, str]], skip: set) -> List[Tuple[int, str, str]]:
    out = {}
    for url, text in links:
        if not url.startswith("http") or len(text) > 200 or research._BAD_LINK.search(url):
            continue
        s = research.match_score(name, f"{text} {research.url_text(url)}")
        if s is None:
            continue
        norm = research.normalize_url(url)
        if norm in skip:
            continue
        if norm not in out or s > out[norm][0]:
            out[norm] = (s, url, text or url)
    return sorted(out.values(), key=lambda x: -x[0])


def focused_crawl(name: str, seeds: List[str]) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    """Dai portali di partenza, due salti sui link che nominano il bando (parole e sigle come «KA152»)."""
    deadline = time.monotonic() + FOCUSED_DEADLINE
    info: List[Dict[str, Any]] = []
    found: Dict[str, Tuple[int, str, str, str]] = {}      # norm -> (score, url, title, via)
    seen = {research.normalize_url(s) for s in seeds}

    def hop(urls: List[str], level: int) -> List[Tuple[int, str, str]]:
        cands: List[Tuple[int, str, str]] = []
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = [pool.submit(_fetch_links, u) for u in urls]
            for u, f in zip(urls, futures):
                remaining = max(0.5, deadline - time.monotonic())
                try:
                    final, links, err = f.result(timeout=remaining)
                except Exception:
                    info.append({"channel": f"portale (salto {level})", "url": u, "matched": 0, "error": "tempo scaduto"})
                    continue
                scored = _score_links(name, links, seen)
                info.append({"channel": f"portale (salto {level})", "url": u, "matched": len(scored), "error": err})
                for s, url, title in scored[:12]:
                    norm = research.normalize_url(url)
                    if norm not in found or s > found[norm][0]:
                        found[norm] = (s, url, title, u)
                    cands.append((s, url, title))
        return sorted(cands, key=lambda x: -x[0])

    first = hop(seeds, 1)
    # secondo salto: dalle pagine più promettenti del primo (le sigle come KA152 stanno spesso una pagina più in là)
    nxt: List[str] = []
    for _, url, _t in first:
        if research.classify_url(url) == "UFFICIALE" and not re.search(r"\.pdf(\?|$)", url, re.I) and url not in nxt:
            nxt.append(url)
        if len(nxt) >= 8:
            break
    for u in nxt:
        seen.add(research.normalize_url(u))
    if nxt and time.monotonic() < deadline:
        hop(nxt, 2)
    hits = [{"url": url, "title": title[:1].upper() + title[1:], "snippet": f"Trovato seguendo i link di {urllib.parse.urlparse(via).netloc}"}
            for s, url, title, via in sorted(found.values(), key=lambda x: -x[0])[:25]]
    return hits, info


def code_pages(name: str) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    hits: List[Dict[str, str]] = []
    for code in research.split_tokens(name)[1]:
        for url, title in CODE_PAGES.get(code, []):
            hits.append({"url": url, "title": title, "snippet": "Pagina ufficiale dell'azione"})
    return hits, ([{"channel": "pagine delle azioni con sigla", "matched": len(hits), "error": None}] if hits else [])


def discover(name: str) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    """Cataloghi + portali di famiglia + elenchi ufficiali. Ritorna (risultati grezzi, diagnostica per canale)."""
    pool = ThreadPoolExecutor(max_workers=2)
    f_cat = pool.submit(search_catalogs, name)
    f_crawl = pool.submit(focused_crawl, name, seeds_for(name))
    crawl_hits, crawl_info = f_crawl.result()
    try:
        cat_hits, cat_info = f_cat.result(timeout=CATALOG_WAIT)
    except Exception:  # catalogo lento: si prosegue senza; il caricamento continua in background e alla prossima ricerca è in cache
        cat_hits, cat_info = [], [{"channel": "catalogo (in caricamento)", "items": 0, "matched": 0,
                                   "error": "Il catalogo nazionale è lento a rispondere: lo uso alla prossima ricerca (resta in memoria per alcune ore)"}]
    pool.shutdown(wait=False)
    code_hits, code_info = code_pages(name)
    return [*code_hits, *cat_hits, *crawl_hits], [*code_info, *cat_info, *crawl_info]
