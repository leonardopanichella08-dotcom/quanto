"""Ricerca di un bando sul web: cerca, scarica pagine e PDF, ne estrae il testo (che poi finisce in memoria).

Cosa fa davvero:
1. ``search_web``: interroga un motore di ricerca (Bing, con DuckDuckGo Lite come ripiego) con più query sul nome del bando;
   ogni risultato è classificato UFFICIALE (Gazzetta Ufficiale, Normattiva, EUR-Lex, ministeri, Invitalia, regioni…) o SECONDARIA (blog, portali).
2. ``fetch_document``: scarica UN indirizzo (pagina HTML, PDF, DOCX o testo) con protezioni contro l'uso improprio e ne estrae il testo;
   restituisce anche i collegamenti utili trovati nella pagina (decreti, avvisi, allegati, FAQ, atti della Gazzetta) per seguirli.

Limiti dichiarati: le pagine costruite interamente in JavaScript restituiscono poco testo; i PDF scansionati (immagini) non si leggono senza OCR;
i motori di ricerca possono bloccare le richieste automatiche (in quel caso si può indicare direttamente il link ufficiale).
"""
from __future__ import annotations

import base64
import hashlib
import io
import ipaddress
import logging
import os
import re
import socket
import threading
import time
import urllib.parse
import zipfile
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from html.parser import HTMLParser
from typing import Any, Deque, Dict, List, Optional, Tuple

import httpx

logging.getLogger("pypdf").setLevel(logging.ERROR)  # avvisi sui font: rumore, non errori

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
MAX_HTML_BYTES = 4_000_000
MAX_BINARY_BYTES = 12_000_000
MAX_PDF_PAGES = 400
PDF_TIME_BUDGET = 18.0            # secondi: una richiesta su serverless ha un limite di tempo
LONG_DOC_CHARS = 60_000         # oltre questa lunghezza si analizzano solo i passaggi che parlano del bando
TIMEOUT = 12.0
MAX_REDIRECTS = 5
RATE_LIMIT = (120, 600)          # richieste in uscita ogni 10 minuti, per processo

OFFICIAL_SUFFIXES = (
    "gazzettaufficiale.it", "normattiva.it", "eur-lex.europa.eu", "europa.eu", "invitalia.it", "governo.it", "gov.it", "inps.it", "camera.it", "senato.it",
    "cdp.it", "mcc.it", "simest.it", "sace.it", "ismea.it", "unioncamere.it", "camcom.it", "anpal.gov.it", "bancaditalia.it", "cortecostituzionale.it",
    # agenzie nazionali e ministeri con dominio proprio
    "erasmusplus.it", "agenziagiovani.it", "indire.it", "eurodesk.it", "gse.it", "enea.it", "inail.it", "esteri.it", "ice.it", "istruzione.it", "difesa.it",
    "giustizia.it", "reterurale.it", "agea.gov.it", "opencoesione.gov.it", "italiadomani.gov.it", "cordis.europa.eu", "eib.org", "eif.org", "acn.gov.it",
    "fondimpresa.it", "fondoforte.it", "for.med.it", "formazienda.it", "sviluppoitalia.it", "confidi.eu", "artigiancassa.it", "bancaditalia.it",
)
_OFFICIAL_RE = re.compile(r"(^|\.)(regione|comune|provincia|cittametropolitana)\.[a-z0-9\-]+\.it$|(^|\.)regione\.[a-z\-]+\.it$")
STOPWORDS = {"il", "lo", "la", "le", "gli", "un", "una", "di", "del", "della", "dei", "delle", "al", "alla", "ai", "alle", "per", "con", "in", "su", "the", "and", "bando", "avviso"}


class ResearchError(Exception):
    """Errore atteso (indirizzo non consentito, file troppo grande, tipo non supportato…): messaggio adatto all'utente."""


# ------------------------------------------------------------------ classificazione
def host_of(url: str) -> str:
    return (urllib.parse.urlparse(url).hostname or "").lower()


def classify_url(url: str) -> str:
    """UFFICIALE = fonte istituzionale; SECONDARIA = blog, portali, consulenti (utili per capire, non per citare)."""
    h = host_of(url)
    if any(h == s or h.endswith("." + s) for s in OFFICIAL_SUFFIXES) or _OFFICIAL_RE.search(h):
        return "UFFICIALE"
    return "SECONDARIA"


def normalize_url(url: str) -> str:
    p = urllib.parse.urlparse(url.strip())
    host = (p.hostname or "").lower().removeprefix("www.")
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query) if not k.lower().startswith(("utm_", "fbclid", "gclid"))]
    return urllib.parse.urlunparse((p.scheme.lower(), host + (f":{p.port}" if p.port and p.port not in (80, 443) else ""), p.path.rstrip("/") or "/", "", urllib.parse.urlencode(q), ""))


def norm_hay(s: str) -> str:
    """Testo confrontabile: minuscolo, «+» come spazio, «KA 152» e «KA-152» come «ka152»."""
    s = s.lower().replace("+", " ")
    s = re.sub(r"(?<=[a-zà-ù])[\s\-_/]+(?=\d)", "", s)
    return re.sub(r"[\s\-_/]+", " ", s)


def split_tokens(name: str) -> Tuple[List[str], List[str]]:
    """(parole, sigle). Le sigle (KA152, 5.0→50, D.L. 34…) identificano un'azione DENTRO un programma: Erasmus KA152 = parola «erasmus» + sigla «ka152»."""
    toks = re.findall(r"[a-zà-ù0-9]+", norm_hay(name))
    codes = [t for t in toks if re.search(r"[a-z]", t) and re.search(r"\d", t)]
    words = [t for t in toks if t not in codes and len(t) > 2 and t not in STOPWORDS and not t.isdigit()]
    return words, codes


def url_text(url: str) -> str:
    """Percorso e parametri dell'indirizzo, senza dominio: «erasmusplus.it» non deve far passare qualunque pagina per «Erasmus»."""
    p = urllib.parse.urlparse(url)
    return urllib.parse.unquote(f"{p.path} {p.query}")


def name_tokens(name: str) -> List[str]:
    words, codes = split_tokens(name)
    return words + codes or [t for t in re.findall(r"[a-zà-ù0-9]+", name.lower())][:2]


# Le sigle dei programmi europei portano al loro settore: sui portali ufficiali l'azione sta dentro una sezione (es. KA152 → «Gioventù»)
_SECTOR_HINTS = [
    (r"^ka15\d$|^you$", ["gioventù", "gioventu", "giovani", "youth", "scambi giovanili", "scambi di giovani"]),
    (r"^ka13\d$|^ka17\d$|^hed$", ["istruzione superiore", "higher education", "università", "universita"]),
    (r"^sch$", ["scuola", "istruzione scolastica", "school"]),
    (r"^vet$", ["formazione professionale", "vocational"]),
    (r"^adu$|^eda$", ["educazione degli adulti", "adult education"]),
]


# Come i documenti ufficiali chiamano le azioni con sigla: «KA152» compare quasi solo nei bandi, il testo della Guida dice «Youth Exchanges»
CODE_SYNONYMS: Dict[str, List[str]] = {
    "ka152": ["youth exchange", "scambi giovanili", "scambi di giovani"],
    "ka153": ["mobility of youth workers", "youth workers mobility", "mobilità degli animatori giovanili"],
    "ka154": ["youth participation activities", "attività di partecipazione giovanile"],
    "ka210": ["small-scale partnership", "partenariati su piccola scala"],
    "ka220": ["cooperation partnership", "partenariati di cooperazione"],
}


def hint_phrases(name: str) -> List[str]:
    toks = re.findall(r"[a-zà-ù0-9]+", norm_hay(name))
    out: List[str] = []
    for rx, phrases in _SECTOR_HINTS:
        if any(re.search(rx, t) for t in toks):
            out += phrases
    return out


def match_score(name: str, text: str) -> Optional[int]:
    """None = il testo non parla di questo bando; altrimenti un punteggio 60..100.

    Le parole del nome devono esserci tutte (se sono 3 o più basta il 60%); la sigla (es. KA152) non è obbligatoria — la pagina può descrivere il programma
    che la contiene — ma vale di più. Così «Resto del Carlino» non passa per «Resto al Sud», mentre la pagina Erasmus+ passa per «Erasmus KA152»."""
    words, codes = split_tokens(name)
    hay = norm_hay(text)
    got_w = sum(1 for w in words if w in hay)
    got_c = sum(1 for c in codes if c in hay)
    if codes and got_c == len(codes):
        return 90 + (10 if words and got_w == len(words) else 0)       # la sigla (es. KA152) è specifica: da sola identifica l'azione
    if codes and any(s in hay for c in codes for s in CODE_SYNONYMS.get(c, [])):
        return 88 + (10 if words and got_w == len(words) else 0)        # la pagina descrive l'azione con il suo nome esteso
    hinted = any(h in hay for h in hint_phrases(name))
    if hinted and not words:
        return 65                                                      # solo il settore: pagina da cui si arriva all'azione
    if words:
        need = len(words) if len(words) <= 2 else max(1, int(len(words) * 0.6 + 0.999))
        if got_w < need:
            return None
    else:
        return None
    score = 60 + (20 * got_w // max(len(words), 1) if words else 0) + (20 * got_c // len(codes) if codes else 0) + (10 if hinted else 0)
    return min(100, score)


# ------------------------------------------------------------------ protezioni e download
_HITS: Deque[float] = deque()
_HITS_LOCK = threading.Lock()


def _rate_check() -> None:
    limit, window = RATE_LIMIT
    now = time.monotonic()
    with _HITS_LOCK:
        while _HITS and now - _HITS[0] > window:
            _HITS.popleft()
        if len(_HITS) >= limit:
            raise ResearchError("Troppe richieste di ricerca in poco tempo: riprova tra qualche minuto")
        _HITS.append(now)


def check_public_url(url: str) -> None:
    """Solo http/https verso indirizzi pubblici: niente rete interna, localhost o metadati cloud (SSRF)."""
    p = urllib.parse.urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        raise ResearchError("Sono ammessi solo indirizzi http/https")
    if p.username or p.password:
        raise ResearchError("Indirizzo con credenziali non consentito")
    if p.port not in (None, 80, 443):
        raise ResearchError("Porta non consentita")
    try:
        infos = socket.getaddrinfo(p.hostname, p.port or (443 if p.scheme == "https" else 80), proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise ResearchError(f"Indirizzo non raggiungibile ({p.hostname})") from exc
    for info in infos:
        if not ipaddress.ip_address(info[4][0]).is_global:
            raise ResearchError("Indirizzo non consentito (rete interna)")


def http_get(url: str, max_bytes: int = MAX_BINARY_BYTES, accept_error_body: bool = False, timeout: float = TIMEOUT) -> Tuple[bytes, str, str]:
    """Scarica ``url`` seguendo i redirect a mano (ricontrollando ogni destinazione). Ritorna (contenuto, url finale, content-type)."""
    _rate_check()
    headers = {"User-Agent": UA, "Accept": "text/html,application/pdf,application/xhtml+xml,text/plain;q=0.8,*/*;q=0.5", "Accept-Language": "it-IT,it;q=0.9"}
    current = url
    with httpx.Client(timeout=timeout, follow_redirects=False, headers=headers) as client:
        for _ in range(MAX_REDIRECTS + 1):
            check_public_url(current)
            try:
                with client.stream("GET", current) as r:
                    if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("location"):
                        current = urllib.parse.urljoin(current, r.headers["location"])
                        continue
                    if r.status_code >= 400 and not (accept_error_body and r.status_code == 404):
                        raise ResearchError(f"Il sito ha risposto {r.status_code}")
                    ctype = r.headers.get("content-type", "").split(";")[0].strip().lower()
                    declared = int(r.headers.get("content-length") or 0)
                    limit = MAX_HTML_BYTES if ctype.startswith("text/") else max_bytes
                    if declared and declared > limit:
                        raise ResearchError(f"File troppo grande ({declared // 1_000_000} MB)")
                    buf = bytearray()
                    for chunk in r.iter_bytes():
                        buf += chunk
                        if len(buf) > limit:
                            raise ResearchError("File troppo grande")
                    return bytes(buf), current, ctype
            except httpx.TimeoutException as exc:
                raise ResearchError("Il sito non risponde in tempo") from exc
            except httpx.HTTPError as exc:
                raise ResearchError(f"Errore di rete: {type(exc).__name__}") from exc
    raise ResearchError("Troppi reindirizzamenti")


# ------------------------------------------------------------------ estrazione del testo
class _Page(HTMLParser):
    # niente "form": molte pagine ASP.NET avvolgono tutto il contenuto in un unico <form>
    SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "aside", "iframe", "template", "head"}
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "table", "ul", "ol", "dt", "dd", "blockquote", "hr", "pre"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: List[str] = []
        self.skip = 0
        self.title = ""
        self.h1 = ""
        self._in: Optional[str] = None
        self.links: List[Tuple[str, str]] = []
        self._href: Optional[str] = None
        self._ltxt: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag == "title":
            self._in = "title"
        elif tag == "h1" and not self.h1:
            self._in = "h1"
        if tag == "body":
            self.skip = 0  # un <head> o <nav> lasciato aperto non deve inghiottire tutta la pagina
        elif tag in self.SKIP:
            self.skip += 1
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._ltxt = []
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("title", "h1"):
            self._in = None
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        if tag == "a" and self._href:
            self.links.append((self._href, re.sub(r"\s+", " ", "".join(self._ltxt)).strip()))
            self._href = None
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in == "title":
            self.title += data
        elif self._in == "h1":
            self.h1 += data
        if self._href is not None:
            self._ltxt.append(data)
        if not self.skip:
            self.parts.append(data)


def _decode(raw: bytes, ctype_header: str = "") -> str:
    m = re.search(rb"charset=[\"']?([\w\-]+)", raw[:3000], re.I)
    for enc in ([m.group(1).decode()] if m else []) + ["utf-8", "cp1252"]:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


_JUNK = re.compile(r"cookie|accetta|rifiuta|privacy policy|javascript|salta al contenuto|torna su|seguici su", re.I)


_GENERIC_TITLE = re.compile(r"^(?:select your language|choose your language|cookie|menu|home|homepage|skip to|accedi|login|sign in|search|cerca|benvenut)", re.I)


def _best_title(title: str, h1: str) -> str:
    """<title> senza il nome del sito («Pagina | Sito»); il primo <h1> solo se il titolo manca o è generico («Select your language»)."""
    t = re.sub(r"\s+", " ", unescape(title)).strip()
    t = re.split(r"\s+[|–—]\s+", t)[0].strip()
    h = re.sub(r"\s+", " ", unescape(h1)).strip()
    for cand in (h, t):
        if len(cand) >= 4 and not _GENERIC_TITLE.match(cand):
            return cand[:200]
    return (h or t)[:200]


def html_to_text(html: str) -> Tuple[str, str, List[Tuple[str, str]]]:
    """(testo pulito, titolo, collegamenti). Senza menu, piè di pagina, script e avvisi sui cookie."""
    p = _Page()
    try:
        p.feed(html)
    except Exception:  # HTML malformato: teniamo quello che abbiamo letto
        pass
    lines: List[str] = []
    for ln in "".join(p.parts).split("\n"):
        ln = re.sub(r"\s+", " ", unescape(ln)).strip()
        if not ln or (len(ln) < 300 and _JUNK.search(ln)) or (lines and lines[-1] == ln):
            continue
        lines.append(ln)
    return "\n".join(lines), _best_title(p.title, p.h1), p.links


def pdf_to_text(data: bytes, budget: float = PDF_TIME_BUDGET) -> Tuple[str, int, int]:
    """(testo, pagine totali, pagine lette): si ferma se finisce il tempo o si superano le pagine massime."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    n = len(reader.pages)
    out = []
    t0 = time.monotonic()
    for page in reader.pages[:MAX_PDF_PAGES]:
        if time.monotonic() - t0 > budget:
            break
        try:
            out.append(page.extract_text() or "")
        except Exception:  # pagina con font/codifica non leggibile
            out.append("")
    return "\n".join(out), n, len(out)


def _phrase_regex(name: str) -> Optional["re.Pattern[str]"]:
    """Le espressioni che identificano il bando nel testo: il nome intero e le sigle (KA152 anche come «KA 152» o «KA-152»)."""
    words = re.findall(r"[\wà-ù]+", name)
    while words and re.fullmatch(r"\d+", words[-1]):
        words.pop()          # "Resto al Sud 2.0" -> anche le pagine che dicono solo "Resto al Sud"
    alts: List[str] = []
    if words:
        alts.append(r"[\s\-–]+".join(re.escape(w) for w in words))
    for code in split_tokens(name)[1]:
        m = re.fullmatch(r"([a-zà-ù]+)(\d+)", code)
        if m:
            alts.append(re.escape(m.group(1)) + r"[\s\-–]?" + re.escape(m.group(2)))
        alts += [re.escape(s).replace(r"\ ", r"[\s\-]+") for s in CODE_SYNONYMS.get(code, [])]
    return re.compile("|".join(f"(?:{a})" for a in alts), re.I) if alts else None


def focus_text(text: str, name: str, window_before: int = 1500, window_after: int = 3000) -> str:
    """Per i documenti lunghi (leggi, manuali) tiene solo i passaggi che citano il bando. I documenti brevi restano interi."""
    if len(text) <= LONG_DOC_CHARS:
        return text
    rx = _phrase_regex(name)
    if rx is None:
        return text
    spans: List[List[int]] = []
    for m in rx.finditer(text):
        a, b = max(0, m.start() - window_before), min(len(text), m.end() + window_after)
        if spans and a <= spans[-1][1]:
            spans[-1][1] = max(spans[-1][1], b)
        else:
            spans.append([a, b])
    if not spans:
        return ""            # documento lungo che non nomina mai il bando: non pertinente
    return "\n[…]\n".join(text[a:b] for a, b in spans)


def docx_to_text(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    xml = re.sub(r"</w:p>", "\n", xml)
    return re.sub(r"[ \t]+", " ", unescape(re.sub(r"<[^>]+>", "", xml))).strip()


# ------------------------------------------------------------------ collegamenti da seguire
_DOC_WORDS = re.compile(r"normativ|decret|avvis|bando|circolar|regolament|allegat|faq|dpcm|legge|linee guida|modulistic|domanda|istruzion|vademecum|gazzetta|eur-lex|normattiva|disposizion|direttiv", re.I)
_BAD_LINK = re.compile(r"^(mailto|tel|javascript):|\.(jpe?g|png|gif|svg|webp|zip|rar|mp4|mp3|xlsx?|pptx?|css|js|ico)(\?|$)|/(login|accedi|area-riservata|newsletter|cookie|privacy|sitemap|accessibilit|rss|contatti|search|ricerca)(/|\?|$)|[?&](lang|language)=", re.I)


def find_links(base_url: str, links: List[Tuple[str, str]], known: Optional[set] = None, limit: int = 25, focus: str = "") -> List[Dict[str, Any]]:
    """Collegamenti utili della pagina: PDF, decreti, avvisi, FAQ, atti della Gazzetta. Si seguono solo siti ufficiali.
    ``focus`` = nome del bando: i link che lo nominano (o nominano la sua sigla, es. KA152) passano avanti."""
    known = known or set()
    seen: Dict[str, Dict[str, Any]] = {}
    base_host = host_of(base_url)
    for href, text in links:
        if not href or href.startswith("#"):
            continue
        full = urllib.parse.urljoin(base_url, href.split("#")[0])
        if not full.startswith(("http://", "https://")) or _BAD_LINK.search(full):
            continue
        norm = normalize_url(full)
        if norm in known or norm in seen or norm == normalize_url(base_url):
            continue
        if classify_url(full) != "UFFICIALE":
            continue
        h = host_of(full)
        is_pdf = bool(re.search(r"\.pdf(\?|$)", full, re.I))
        about = focus and match_score(focus, f"{text} {url_text(full)}") is not None
        score = (50 if is_pdf else 0) + (40 if any(h.endswith(x) for x in ("gazzettaufficiale.it", "normattiva.it", "eur-lex.europa.eu")) else 0) \
            + (30 if _DOC_WORDS.search(text + " " + full) else 0) + (15 if h == base_host else 0) + (45 if about else 0)
        if score < 45:
            continue
        seen[norm] = {"url": full, "title": (text or full)[:140], "score": score, "is_pdf": is_pdf, "host": h}
    return sorted(seen.values(), key=lambda x: -x["score"])[:limit]


# ------------------------------------------------------------------ ricerca
def _decode_bing(href: str) -> str:
    if "bing.com/ck/a" in href:
        u = (urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("u") or [""])[0]
        if u.startswith("a1"):
            b = u[2:] + "=" * (-len(u[2:]) % 4)
            try:
                return base64.urlsafe_b64decode(b).decode()
            except Exception:
                return href
    return href


def _strip(html: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", html))).strip()


def parse_bing(html: str) -> List[Dict[str, str]]:
    out = []
    for m in re.finditer(r'<li class="b_algo".*?</li>', html, re.S):
        blk = m.group(0)
        a = re.search(r'<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', blk, re.S)
        if not a:
            continue
        cap = re.search(r"<p[^>]*>(.*?)</p>", blk, re.S)
        out.append({"url": _decode_bing(unescape(a.group(1))), "title": _strip(a.group(2)), "snippet": _strip(cap.group(1))[:220] if cap else ""})
    return out


def parse_ddg_lite(html: str) -> List[Dict[str, str]]:
    out = []
    for m in re.finditer(r'<a[^>]+class=[\'"]result-link[\'"][^>]*href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', html, re.S):
        href = unescape(m.group(1))
        q = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
        real = (q.get("uddg") or [href])[0]
        out.append({"url": real, "title": _strip(m.group(2)), "snippet": ""})
    return out


BRAVE_URL = "https://api.search.brave.com/res/v1/web/search"


def parse_brave(data: Dict[str, Any]) -> List[Dict[str, str]]:
    return [{"url": r.get("url", ""), "title": _strip(r.get("title", "")), "snippet": _strip(r.get("description", ""))[:220]}
            for r in (data.get("web") or {}).get("results", []) if r.get("url")]


def _engine_brave(query: str, key: str) -> Tuple[List[Dict[str, str]], Optional[str]]:
    try:
        r = httpx.get(BRAVE_URL, params={"q": query, "country": "IT", "search_lang": "it", "count": 20},
                      headers={"X-Subscription-Token": key, "Accept": "application/json"}, timeout=TIMEOUT)
        return (parse_brave(r.json()), None) if r.status_code == 200 else ([], f"risposta {r.status_code}")
    except (httpx.HTTPError, ValueError) as exc:
        return [], f"non raggiungibile ({type(exc).__name__})"


def _engine_serper(query: str, key: str) -> Tuple[List[Dict[str, str]], Optional[str]]:
    try:
        r = httpx.post("https://google.serper.dev/search", json={"q": query, "gl": "it", "hl": "it", "num": 20}, headers={"X-API-KEY": key}, timeout=TIMEOUT)
        if r.status_code != 200:
            return [], f"risposta {r.status_code}"
        return [{"url": x.get("link", ""), "title": x.get("title", ""), "snippet": x.get("snippet", "")[:220]} for x in r.json().get("organic", []) if x.get("link")], None
    except (httpx.HTTPError, ValueError) as exc:
        return [], f"non raggiungibile ({type(exc).__name__})"


def _engine_tavily(query: str, key: str) -> Tuple[List[Dict[str, str]], Optional[str]]:
    try:
        r = httpx.post("https://api.tavily.com/search", json={"api_key": key, "query": query, "max_results": 15, "search_depth": "basic"}, timeout=TIMEOUT)
        if r.status_code != 200:
            return [], f"risposta {r.status_code}"
        return [{"url": x.get("url", ""), "title": x.get("title", ""), "snippet": (x.get("content") or "")[:220]} for x in r.json().get("results", []) if x.get("url")], None
    except (httpx.HTTPError, ValueError) as exc:
        return [], f"non raggiungibile ({type(exc).__name__})"


def _engine_bing(query: str) -> Tuple[List[Dict[str, str]], Optional[str]]:
    try:
        r = httpx.get("https://www.bing.com/search", params={"q": query, "setlang": "it", "cc": "IT"},
                      headers={"User-Agent": UA, "Accept-Language": "it-IT,it;q=0.9"}, timeout=TIMEOUT, follow_redirects=True)
        hits = parse_bing(r.text)
        return (hits, None) if hits else ([], "nessun risultato leggibile (possibile blocco anti-robot)")
    except httpx.HTTPError as exc:
        return [], f"non raggiungibile ({type(exc).__name__})"


def _engine_ddg(query: str) -> Tuple[List[Dict[str, str]], Optional[str]]:
    try:
        r = httpx.post("https://lite.duckduckgo.com/lite/", data={"q": query}, headers={"User-Agent": UA}, timeout=TIMEOUT, follow_redirects=True)
        hits = parse_ddg_lite(r.text)
        return (hits, None) if hits else ([], f"nessun risultato (risposta {r.status_code})")
    except httpx.HTTPError as exc:
        return [], f"non raggiungibile ({type(exc).__name__})"


def _engines() -> List[Tuple[str, Any]]:
    """Prima i motori con chiave (affidabili anche da server cloud), poi quelli gratuiti (spesso bloccati)."""
    out: List[Tuple[str, Any]] = []
    for env, name, fn in (("QUANTO_BRAVE_API_KEY", "brave", _engine_brave), ("QUANTO_SERPER_API_KEY", "serper", _engine_serper), ("QUANTO_TAVILY_API_KEY", "tavily", _engine_tavily)):
        key = os.getenv(env, "").strip()
        if key:
            out.append((name, lambda q, fn=fn, key=key: fn(q, key)))
    return out + [("bing", _engine_bing), ("duckduckgo", _engine_ddg)]


def _relevant(name: Optional[str], hits: List[Dict[str, str]]) -> bool:
    return name is None or any(match_score(name, f"{h.get('title', '')} {h.get('snippet', '')} {url_text(h['url'])}") is not None for h in hits)


def _search_one(query: str, name: Optional[str] = None) -> Tuple[List[Dict[str, str]], Optional[str]]:
    """Prova i motori in ordine e si ferma al primo che dà risultati PERTINENTI (da un server cloud Bing risponde spesso con risultati senza alcun legame)."""
    notes: List[str] = []
    for engine, fn in _engines():
        _rate_check()
        hits, err = fn(query)
        if hits and _relevant(name, hits):
            return [{**h, "engine": engine} for h in hits], None
        notes.append(f"{engine}: {err or 'risultati non pertinenti'}")
    return [], "; ".join(notes)


# elenchi ufficiali di incentivi: non dipendono da un motore di ricerca e funzionano anche da server cloud
DIRECTORIES = (
    "https://www.invitalia.it/incentivi-e-strumenti",
    "https://www.mimit.gov.it/it/incentivi-mise",
    "https://www.mimit.gov.it/it/incentivi",
    "https://www.mimit.gov.it/it/incentivi-mise/incentivi-in-evidenza",
)


def _scan_directory(args: Tuple[str, str]) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    url, name = args
    info: Dict[str, Any] = {"url": url, "matched": 0, "error": None}
    try:
        raw, final, ctype = http_get(url, accept_error_body=True)
        _, _, links = html_to_text(_decode(raw, ctype))
    except ResearchError as exc:
        info["error"] = str(exc)
        return [], info
    found: List[Dict[str, str]] = []
    for href, text in links:
        full = urllib.parse.urljoin(final, href.split("#")[0])
        if full.startswith("http") and len(text) < 160 and match_score(name, f"{text} {url_text(full)}") is not None:
            found.append({"url": full, "title": text or full, "snippet": f"Elenco ufficiale: {host_of(final)}"})
    info["matched"] = len(found)
    return found, info


def official_directory(name: str) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
    """Cerca il nome nei link degli elenchi ufficiali (Invitalia, MIMIT): affidabile anche quando i motori di ricerca bloccano il server."""
    hits: List[Dict[str, str]] = []
    infos: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for found, info in pool.map(_scan_directory, [(d, name) for d in DIRECTORIES]):
            hits.extend(found)
            infos.append(info)
    return hits, infos


def build_queries(name: str, hint: str = "") -> List[str]:
    n = f'"{name.strip()}"' + (f" {hint.strip()}" if hint.strip() else "")
    return [
        f"{n} bando",
        f"{n} normativa decreto avviso",
        f"{n} site:invitalia.it",
        f"{n} site:gov.it",
        f"{n} site:gazzettaufficiale.it",
        f"{n} filetype:pdf avviso decreto",
    ]


def rank_results(name: str, raw: List[Dict[str, str]], supplied: Optional[List[str]] = None, max_results: int = 30) -> List[Dict[str, Any]]:
    """Unisce e ordina i risultati: prima le fonti ufficiali pertinenti al nome, poi le altre."""
    merged: Dict[str, Dict[str, Any]] = {}
    for hit in raw:
        url = hit["url"]
        if not url.startswith(("http://", "https://")):
            continue
        norm = normalize_url(url)
        rel = match_score(name, f"{hit.get('title', '')} {hit.get('snippet', '')} {url_text(url)}")
        if rel is None:
            continue  # rumore: il nome del bando non compare (es. "Resto del Carlino" cercando "Resto al Sud")
        tier = classify_url(url)
        is_pdf = bool(re.search(r"\.pdf(\?|$)", url, re.I))
        score = (100 if tier == "UFFICIALE" else 30) + rel // 2 + (15 if is_pdf else 0) + (10 if re.search(r"normativ|decret|avvis|bando|regolament", url, re.I) else 0)
        cur = merged.get(norm)
        if cur is None or score > cur["score"]:
            merged[norm] = {"url": url, "title": hit.get("title") or url, "snippet": hit.get("snippet", ""), "tier": tier, "score": score,
                            "is_pdf": is_pdf, "host": host_of(url), "user_supplied": False, "preselected": False, "engine": hit.get("engine")}
    for u in supplied or []:
        norm = normalize_url(u)
        merged[norm] = {"url": u, "title": u, "snippet": "Indicato da te", "tier": classify_url(u), "score": 1000, "is_pdf": bool(re.search(r"\.pdf(\?|$)", u, re.I)),
                        "host": host_of(u), "user_supplied": True, "preselected": True, "engine": None}
    ordered = sorted(merged.values(), key=lambda x: -x["score"])[:max_results]
    picked = 0
    for c in ordered:
        if c["user_supplied"]:
            continue
        if c["tier"] == "UFFICIALE" and picked < 6:
            c["preselected"] = True
            picked += 1
    return ordered


def search_web(name: str, hint: str = "", supplied: Optional[List[str]] = None, discover: Any = None) -> Dict[str, Any]:
    queries = build_queries(name, hint)
    raw: List[Dict[str, str]] = []
    errors: List[str] = []
    per_query: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for q, (hits, err) in zip(queries, pool.map(lambda q: _search_one(q, name), queries)):
            raw.extend(hits)
            per_query.append({"query": q, "hits": len(hits), "engine": hits[0].get("engine") if hits else None, "error": err})
            if err and err not in errors:
                errors.append(err)
    dir_hits, dir_info = (discover or official_directory)(name)
    ranked = rank_results(name, [*dir_hits, *raw], supplied)
    # diagnostica: se il motore risponde ma nulla è pertinente (o risponde con altro), si vede perché
    diagnostics = {"raw_hits": len(raw), "kept": len(ranked), "per_query": per_query, "directories": dir_info,
                   "keyed_engines": [n for n, _ in _engines() if n not in ("bing", "duckduckgo")], "sample": [f"{h.get('title', '')[:70]} — {h['url'][:80]}" for h in raw[:5]]}
    if not ranked:
        if raw:
            errors.append("Il motore ha risposto ma nessun risultato nomina il bando")
        if not any(os.getenv(k, "").strip() for k in ("QUANTO_BRAVE_API_KEY", "QUANTO_SERPER_API_KEY", "QUANTO_TAVILY_API_KEY")):
            errors.append("Da un server cloud i motori di ricerca gratuiti sono spesso bloccati: con una chiave (QUANTO_BRAVE_API_KEY, QUANTO_SERPER_API_KEY o QUANTO_TAVILY_API_KEY, tutte con piano gratuito) la ricerca è affidabile")
    return {"queries": queries, "candidates": ranked, "engine_errors": errors if not ranked else [], "diagnostics": diagnostics}


# ------------------------------------------------------------------ download di un documento
def fetch_document(url: str) -> Dict[str, Any]:
    """Scarica e legge un indirizzo. Solleva ResearchError con un messaggio comprensibile se non è possibile."""
    raw, final, ctype = http_get(url)
    warnings: List[str] = []
    links: List[Tuple[str, str]] = []
    title = ""
    is_pdf = raw[:4] == b"%PDF" or ctype == "application/pdf" or final.lower().split("?")[0].endswith(".pdf")
    pages: Optional[int] = None
    if is_pdf:
        kind = "PDF"
        try:
            text, pages, read = pdf_to_text(raw)
        except Exception as exc:
            raise ResearchError("PDF non leggibile (danneggiato o protetto)") from exc
        if pages and len(text.strip()) < 150 * min(read or 1, 3):
            warnings.append("Il PDF contiene quasi solo immagini (scansione): serve un OCR, che qui non c'è")
        if pages and read < pages:
            warnings.append(f"Lette solo le prime {read} pagine su {pages} (limite di tempo o di lunghezza)")
        title = final.rsplit("/", 1)[-1].split("?")[0] or "documento.pdf"
        title = urllib.parse.unquote(title)
    elif raw[:2] == b"PK" and (final.lower().endswith(".docx") or "wordprocessingml" in ctype):
        kind = "DOCX"
        try:
            text = docx_to_text(raw)
        except Exception as exc:
            raise ResearchError("File Word non leggibile") from exc
        title = urllib.parse.unquote(final.rsplit("/", 1)[-1].split("?")[0])
    elif ctype.startswith("text/") or "xml" in ctype or ctype in ("", "application/octet-stream"):
        html = _decode(raw, ctype)
        if ctype == "text/plain":
            kind, text, title = "TXT", html, final.rsplit("/", 1)[-1]
        else:
            kind = "HTML"
            text, title, links = html_to_text(html)
            if len(text) < 800:
                warnings.append("Poco testo nella pagina: il contenuto potrebbe essere caricato dinamicamente (JavaScript) e non leggibile qui")
    else:
        raise ResearchError(f"Tipo di file non supportato ({ctype or 'sconosciuto'})")
    if len(text.strip()) < 40:
        raise ResearchError("Nessun testo leggibile in questo documento")
    return {"url": final, "title": title or final, "text": text, "chars": len(text), "pages": pages, "kind": kind, "content_type": ctype,
            "tier": classify_url(final), "size_bytes": len(raw), "sha256_raw": hashlib.sha256(raw).hexdigest(), "raw": raw, "links": links, "warnings": warnings}
