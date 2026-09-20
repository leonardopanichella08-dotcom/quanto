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


def name_tokens(name: str) -> List[str]:
    return [t for t in re.findall(r"[a-zà-ù0-9]+", name.lower()) if len(t) > 2 and t not in STOPWORDS] or [t for t in re.findall(r"[a-zà-ù0-9]+", name.lower())][:2]


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


def http_get(url: str, max_bytes: int = MAX_BINARY_BYTES) -> Tuple[bytes, str, str]:
    """Scarica ``url`` seguendo i redirect a mano (ricontrollando ogni destinazione). Ritorna (contenuto, url finale, content-type)."""
    _rate_check()
    headers = {"User-Agent": UA, "Accept": "text/html,application/pdf,application/xhtml+xml,text/plain;q=0.8,*/*;q=0.5", "Accept-Language": "it-IT,it;q=0.9"}
    current = url
    with httpx.Client(timeout=TIMEOUT, follow_redirects=False, headers=headers) as client:
        for _ in range(MAX_REDIRECTS + 1):
            check_public_url(current)
            try:
                with client.stream("GET", current) as r:
                    if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("location"):
                        current = urllib.parse.urljoin(current, r.headers["location"])
                        continue
                    if r.status_code >= 400:
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
    title = re.sub(r"\s+", " ", unescape(p.h1 or p.title)).strip()[:200]
    return "\n".join(lines), title, p.links


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
    words = re.findall(r"[\wà-ù]+", name)
    while words and re.fullmatch(r"\d+", words[-1]):
        words.pop()          # "Resto al Sud 2.0" -> anche le pagine che dicono solo "Resto al Sud"
    if not words:
        return None
    return re.compile(r"[\s\-–]+".join(re.escape(w) for w in words), re.I)


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


def find_links(base_url: str, links: List[Tuple[str, str]], known: Optional[set] = None, limit: int = 25) -> List[Dict[str, Any]]:
    """Collegamenti utili della pagina: PDF, decreti, avvisi, FAQ, atti della Gazzetta. Si seguono solo siti ufficiali."""
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
        score = (50 if is_pdf else 0) + (40 if any(h.endswith(x) for x in ("gazzettaufficiale.it", "normattiva.it", "eur-lex.europa.eu")) else 0) \
            + (30 if _DOC_WORDS.search(text + " " + full) else 0) + (15 if h == base_host else 0)
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


def _search_one(query: str) -> Tuple[List[Dict[str, str]], Optional[str]]:
    _rate_check()
    try:
        r = httpx.get("https://www.bing.com/search", params={"q": query, "setlang": "it", "cc": "IT"},
                      headers={"User-Agent": UA, "Accept-Language": "it-IT,it;q=0.9"}, timeout=TIMEOUT, follow_redirects=True)
        hits = parse_bing(r.text)
        if hits:
            return hits, None
        note = "Bing non ha restituito risultati leggibili (possibile blocco anti-robot)"
    except httpx.HTTPError as exc:
        note = f"Bing non raggiungibile ({type(exc).__name__})"
    try:  # ripiego
        r = httpx.post("https://lite.duckduckgo.com/lite/", data={"q": query}, headers={"User-Agent": UA}, timeout=TIMEOUT, follow_redirects=True)
        hits = parse_ddg_lite(r.text)
        if hits:
            return hits, None
        return [], note + "; anche DuckDuckGo non ha dato risultati"
    except httpx.HTTPError:
        return [], note


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
    tokens = name_tokens(name)
    merged: Dict[str, Dict[str, Any]] = {}
    for hit in raw:
        url = hit["url"]
        if not url.startswith(("http://", "https://")):
            continue
        norm = normalize_url(url)
        hay = f"{hit.get('title', '')} {hit.get('snippet', '')} {url}".lower()
        ratio = sum(1 for t in tokens if t in hay) / max(len(tokens), 1)
        if ratio < 0.6:
            continue  # rumore: il nome del bando non compare (es. "Resto del Carlino" cercando "Resto al Sud")
        tier = classify_url(url)
        is_pdf = bool(re.search(r"\.pdf(\?|$)", url, re.I))
        score = (100 if tier == "UFFICIALE" else 30) + int(ratio * 40) + (15 if is_pdf else 0) + (10 if re.search(r"normativ|decret|avvis|bando|regolament", url, re.I) else 0)
        cur = merged.get(norm)
        if cur is None or score > cur["score"]:
            merged[norm] = {"url": url, "title": hit.get("title") or url, "snippet": hit.get("snippet", ""), "tier": tier, "score": score,
                            "is_pdf": is_pdf, "host": host_of(url), "user_supplied": False, "preselected": False}
    for u in supplied or []:
        norm = normalize_url(u)
        merged[norm] = {"url": u, "title": u, "snippet": "Indicato da te", "tier": classify_url(u), "score": 1000, "is_pdf": bool(re.search(r"\.pdf(\?|$)", u, re.I)),
                        "host": host_of(u), "user_supplied": True, "preselected": True}
    ordered = sorted(merged.values(), key=lambda x: -x["score"])[:max_results]
    picked = 0
    for c in ordered:
        if c["user_supplied"]:
            continue
        if c["tier"] == "UFFICIALE" and picked < 6:
            c["preselected"] = True
            picked += 1
    return ordered


def search_web(name: str, hint: str = "", supplied: Optional[List[str]] = None) -> Dict[str, Any]:
    queries = build_queries(name, hint)
    raw: List[Dict[str, str]] = []
    errors: List[str] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for hits, err in pool.map(_search_one, queries):
            raw.extend(hits)
            if err and err not in errors:
                errors.append(err)
    ranked = rank_results(name, raw, supplied)
    return {"queries": queries, "candidates": ranked, "engine_errors": errors if not raw else []}


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
