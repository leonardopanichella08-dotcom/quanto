"""Documenti pubblici per FARE la domanda di un bando: modulo di domanda, formulario / scheda progetto, allegati, dichiarazioni, istruzioni.

Per ogni bando si cercano, nella pagina ufficiale e nei documenti già letti, i collegamenti a PDF / Word / Excel e pagine di modulistica; si scaricano (e si
conservano per riaprirli da QUANTO); e se ne ricava, con regole fisse e senza modelli linguistici, che cosa serve davvero per presentare la domanda:

- ALLEGATI      documenti da unire alla domanda (elenchi «alla domanda devono essere allegati…», «Allegato B – …»);
- DOMANDE       punti a cui il formulario chiede di rispondere («Descrivere…», «Indicare…», sezioni numerate, frasi che finiscono con «?»);
- CAMPI         dati da inserire (voci seguite da una riga da compilare «________» o «……»);
- DICHIARAZIONI caselle da spuntare e dichiarazioni sostitutive («DICHIARA di…», «☐ di non essere…»).

Ogni voce riporta il testo ESATTO del documento da cui viene, con il nome del documento: niente è riassunto o inventato. Un documento che non si riesce a leggere
(scansione, vecchio .doc / .xls, sito che blocca) resta scaricabile e porta un avviso: non si fingono contenuti.
"""
from __future__ import annotations

import io
import json
import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Any, Dict, List, Optional, Tuple

from app.core import events, official_sources, research
from app.core.db import connect

MAX_DOCS = 10
MAX_FILE_BYTES = 8_000_000
KINDS = {"DOMANDA": "Modulo di domanda", "FORMULARIO": "Formulario / scheda progetto", "ALLEGATO": "Allegato o dichiarazione", "ISTRUZIONI": "Istruzioni e guide",
         "AVVISO": "Bando / avviso / regolamento"}
ITEM_KINDS = {"ALLEGATO": "Documenti da presentare", "DOMANDA": "Domande a cui rispondere", "CAMPO": "Dati da inserire", "DICHIARAZIONE": "Dichiarazioni da rendere"}
ITEM_CAP = {"ALLEGATO": 40, "DOMANDA": 60, "CAMPO": 60, "DICHIARAZIONE": 40}

_EXT = re.compile(r"\.(pdf|docx?|odt|xlsx?|ods)(\?|$)", re.I)
_FORM_WORDS = re.compile(r"domand|istanz|modul|modulist|allegat|formulari|scheda\s*(?:progett|di\s*progett|tecnic)|business\s*plan|piano\s*(?:di\s*)?(?:spes|investiment|impres)|dichiaraz|autocertific|"
                         r"preventiv|rendicont|istruzion|guida\s*(?:alla\s*)?(?:compilaz|present)|vademecum|manuale|faq|linee\s*guida|modello|mod\.\s*[a-z0-9]|scheda|check\s*list|checklist", re.I)
_AVVISO_WORDS = re.compile(r"\bbando\b|\bavviso\b|disciplinare|regolamento|decreto|\bdd\b|determina", re.I)
_SKIP = re.compile(r"privacy|informativa|trattamento\s*dati|graduatori|elenco\s*(?:dei\s*)?(?:beneficiari|ammess)|beneficiari\s*\d{4}|non\s*ammess|finanziabil|esiti|verbale|nomina|commissione|cookie|newsletter|rassegna|comunicato|calendario|"
                  r"regolamento\s*(?:\(\s*(?:ue|ce|cee)\s*\)|ue|ce|n\.\s*\d+\s*/\s*\d{4})|direttiva|delibera\w*|deliberazione|codici\s*ateco|risultanz\w+|istruttori\w+|elenco|proroga|riapertura|modifica\s*(?:del\s*)?termin\w*", re.I)


def classify(title: str, url: str) -> Optional[str]:
    t = f"{title} {urllib.parse.unquote(url.rsplit('/', 1)[-1])}"
    if _SKIP.search(t):
        return None
    if re.search(r"istruzion|guida\s*(?:alla\s*)?(?:compilaz|present)|vademecum|manuale|faq|linee\s*guida", t, re.I):
        return "ISTRUZIONI"
    if re.search(r"formulari|scheda\s*(?:di\s*)?progett|business\s*plan|piano\s*(?:di\s*)?(?:investiment|impres)|proposta\s*progettuale", t, re.I):
        return "FORMULARIO"
    if re.search(r"domand|istanz|richiesta\s*di\s*(?:contribut|agevolaz|ammission)", t, re.I):
        return "DOMANDA"
    if re.search(r"allegat|dichiaraz|autocertific|modul|modello|mod\.\s*[a-z0-9]|preventiv|piano\s*(?:di\s*)?spes|rendicont|scheda|check\s*list", t, re.I):
        return "ALLEGATO"
    if _AVVISO_WORDS.search(t):
        return "AVVISO"
    return None


# ------------------------------------------------------------------------------------------------ che cosa chiede il documento
_BULLET = re.compile(r"^\s*(?:[-•▪●■◦·–—]|\(?[a-z]\)|\(?\d{1,2}[.)]|[ivx]{1,4}[.)])\s+(.{6,})$", re.I)
_ATTACH_INTRO = re.compile(r"(?:alla\s+domanda\s+(?:devono|dovranno|deve|dovrà)\s+essere\s+(?:allegat\w+|corredat\w+)|alla\s+domanda\s+vanno\s+allegat\w+|da\s+allegare|documentazione\s+(?:da\s+)?(?:presentare|allegare)|"
                           r"allegare\s+obbligatoriamente|deve\s+essere\s+corredata\s+(?:da|dai|dalla)|devono\s+essere\s+allegat\w+|allegati\s+obbligatori|documenti\s+(?:da\s+)?(?:presentare|allegare)|"
                           r"la\s+domanda\s+(?:deve|dovrà)\s+(?:essere\s+)?(?:corredata|accompagnata)|si\s+allegano?\s*:)", re.I)
_ATTACH_TITLE = re.compile(r"^\s*(allegato\s*[“\"]?\s*(?:[A-Z]|\d{1,2}[A-Z]?)\b[^\n]{0,180})$", re.I)
_PROMPT_VERBS = (r"descri(?:vere|vi)|illustra(?:re|ri)|indica(?:re|ri)|specifica(?:re|ri)|elenca(?:re|ri)|motiva(?:re|ri)|quantifica(?:re|ri)|spiega(?:re|ri)|fornire|fornisci|riporta(?:re|ri)|"
                 r"precisa(?:re|ri)|dettaglia(?:re|ri)|argomenta(?:re|ri)|evidenzia(?:re|ri)|documenta(?:re|ri)|inserire|inserisci|compila(?:re|ri)|dimostra(?:re|ri)|"
                 r"presenta(?:re|ri)|identifica(?:re|ri)|definire|definisci|stima(?:re|ri)|valuta(?:re|ri)")
_PROMPT = re.compile(r"^\s*(?:\d+(?:\.\d+)*[.)]?\s*|[a-z][.)]\s*)?((?:" + _PROMPT_VERBS + r")\b.{12,300})$", re.I)
_SECTION = re.compile(r"^\s*((?:\d{1,2}(?:\.\d{1,2}){0,2}|[A-Z])[.)]?\s+[A-ZÀ-Ú][^\n.:;]{8,140})$")
_FIELD = re.compile(r"^\s*([A-ZÀ-Úa-zà-ú][A-ZÀ-Úa-zà-ú0-9'’ /()\-,.]{2,70}?)\s*[:：]?\s*(?:_{3,}|\.{4,}|…{2,}|…+|\[\s*\]|\(\s*\))\s*(?:[A-Za-zÀ-Úà-ú'’ /()\-]{0,40})?\s*(?:_{3,}|\.{4,}|…+)?\s*$")
_BOX = re.compile(r"^\s*(?:☐|□|☑|☒|\[\s?[xX]?\s?\]|\(\s?[xX]?\s?\))\s*(.{8,400})$")
_DECL_INTRO = re.compile(r"\b(?:dichiara|dichiarano|consapevole\s+delle\s+sanzioni|sotto\s+la\s+propria\s+responsabilit\w+|ai\s+sensi\s+degli?\s+art\w*\.?\s*(?:46|47)\s+del\s+d\.?p\.?r\.?)", re.I)
_DECL_ITEM = re.compile(r"^\s*(?:[-•▪●■◦·–—]|\(?[a-z0-9]{1,2}[.)])?\s*((?:di|che|a)\s+(?:essere|non\s+essere|avere|non\s+avere|aver|non\s+aver|possedere|non\s+possedere|impegnarsi|rispettare|"
                        r"trovarsi|non\s+trovarsi|aver\s+preso|conoscere|accettare|autorizzare|manifestare)\b.{8,420})$", re.I)


def _clip(s: str, n: int = 260) -> str:
    s = re.sub(r"\s+", " ", s).strip(" \t-–—•▪●·;")
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def extract_items(text: str, kind: str = "") -> Dict[str, List[str]]:
    """Voci {tipo: [testo, …]} del documento. Solo ciò che è scritto nel testo, senza duplicati."""
    out: Dict[str, List[str]] = {k: [] for k in ITEM_KINDS}
    seen: Dict[str, set] = {k: set() for k in ITEM_KINDS}

    def add(k: str, value: str) -> None:
        v = _clip(value)
        if k == "ALLEGATO":
            v = v.rstrip(".,;")
            if re.match(r"^(?:sezione|divisione|divisioni|codice|codici)\s+[A-Za-z0-9]", v, re.I):          # elenchi di settori ATECO, non documenti da presentare
                return
        key = re.sub(r"\W+", " ", v.lower()).strip()
        if len(v) >= 6 and key not in seen[k] and len(out[k]) < ITEM_CAP[k]:
            seen[k].add(key)
            out[k].append(v)

    lines = [ln.rstrip() for ln in (text or "").splitlines()]
    n = len(lines)
    in_decl = 0
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s:
            continue
        # allegati: titolo «Allegato B – Dichiarazione…» oppure elenco introdotto da «alla domanda devono essere allegati»
        m = _ATTACH_TITLE.match(s)
        if m and len(s) > 12 and kind in ("AVVISO", "ISTRUZIONI", ""):          # nei moduli «Allegato 1A» è il titolo del modulo stesso, non un altro documento da presentare
            add("ALLEGATO", m.group(1))
        if _ATTACH_INTRO.search(s) and len(s) < 400:
            tail = s.split(":", 1)[1].strip() if ":" in s and len(s.split(":", 1)[1].strip()) > 8 else ""
            if tail:
                add("ALLEGATO", tail)
            taken = 0
            for j in range(i + 1, min(n, i + 16)):
                b = _BULLET.match(lines[j])
                if b:
                    if len(b.group(1)) <= 260 and not re.match(r"^\d{1,2}\s+\w+\s+\d{4}$", b.group(1).strip()):
                        add("ALLEGATO", b.group(1))
                    taken += 1
                elif lines[j].strip() == "" and taken:
                    break
                elif taken and not lines[j].startswith((" ", "\t")) and len(lines[j].strip()) > 120:
                    break
        if kind == "AVVISO":                      # un bando / decreto elenca gli allegati; domande, campi e dichiarazioni da rendere stanno nei moduli
            continue
        # dichiarazioni: caselle e «dichiara di…»
        b = _BOX.match(s)
        if b:
            add("DICHIARAZIONE", b.group(1))
        if _DECL_INTRO.search(s):
            in_decl = 18
        elif in_decl:
            in_decl -= 1
            d = _DECL_ITEM.match(s)
            if d:
                add("DICHIARAZIONE", d.group(1))
        # campi da compilare
        f = _FIELD.match(s)
        if f and not _BOX.match(s):
            label = f.group(1).strip(" :.-")
            if 4 <= len(label) <= 70 and not re.fullmatch(r"[_.\s…]+", label) and label.count("(") == label.count(")"):
                add("CAMPO", label)
        # domande / punti a cui rispondere
        p = _PROMPT.match(s)
        if p and not _FIELD.match(s):
            add("DOMANDA", p.group(1))
        elif s.endswith("?") and 18 <= len(s) <= 300:
            add("DOMANDA", s)
        elif kind == "FORMULARIO" and _SECTION.match(s) and not s.isupper():
            add("DOMANDA", _SECTION.match(s).group(1))
    return out


def read_text(raw: bytes, url: str, ctype: str) -> Tuple[str, Optional[int], List[str], str]:
    """(testo, pagine, avvisi, formato). Non solleva: un file non leggibile dà testo vuoto e un avviso."""
    low = url.lower().split("?")[0]
    warnings: List[str] = []
    try:
        if raw[:4] == b"%PDF" or ctype == "application/pdf" or low.endswith(".pdf"):
            text, pages, read = research.pdf_to_text(raw, budget=9.0)
            if pages and len(text.strip()) < 150 * min(read or 1, 3):
                warnings.append("Il PDF è una scansione (solo immagini): serve l'OCR, qui non c'è. Scaricalo e compilalo a mano.")
            if pages and read < pages:
                warnings.append(f"Lette solo le prime {read} pagine su {pages}")
            return text, pages, warnings, "PDF"
        if raw[:2] == b"PK":                         # Word / Excel moderni sono archivi zip: dal contenuto si capisce quale, anche se l'indirizzo non ha l'estensione
            import zipfile
            names = set(zipfile.ZipFile(io.BytesIO(raw)).namelist())
            if "word/document.xml" in names:
                return research.docx_to_text(raw), None, warnings, "DOCX"
            if "xl/workbook.xml" in names:
                return research.xlsx_to_text(raw), None, warnings, "XLSX"
            warnings.append("Archivio non riconosciuto come documento Word o Excel")
            return "", None, warnings, "ZIP"
        if low.endswith((".doc", ".xls", ".odt", ".ods")) or ctype in ("application/msword", "application/vnd.ms-excel"):
            warnings.append("Formato vecchio (.doc / .xls / OpenDocument): QUANTO non lo legge, ma puoi scaricarlo e compilarlo.")
            return "", None, warnings, low.rsplit(".", 1)[-1].upper()
        text, _, _ = research.html_to_text(research._decode(raw, ctype))
        return text, None, warnings, "HTML"
    except Exception as exc:  # noqa: BLE001 - un documento rotto non ferma la raccolta
        return "", None, [f"Documento non leggibile ({type(exc).__name__})"], "ALTRO"


# ------------------------------------------------------------------------------------------------ ricerca dei collegamenti
def _candidate_links(page_url: str, links: List[Tuple[str, str]], known: set) -> List[Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    base = research.host_of(page_url)
    for href, text in links:
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        full = urllib.parse.urljoin(page_url, href.split("#")[0])
        if not full.startswith(("http://", "https://")):
            continue
        host = research.host_of(full)
        same = host == base or host.removeprefix("www.") == base.removeprefix("www.")
        if not (same or research.classify_url(full) == "UFFICIALE" or official_sources.is_official_host(host)):
            continue
        is_file = bool(_EXT.search(full))
        title = re.sub(r"\s+", " ", text or "").strip()
        kind = classify(title, full) if title else None
        if not title or re.match(r"^(?:pdf\s+)?(?:scarica|download|clicca|vai|apri|leggi)\b[\w\s]{0,25}$|^(?:allegato|documento|file|pdf|doc|docx|xls|xlsx|odt)$|^formato\s+\w+$", title, re.I):
            title = urllib.parse.unquote(full.rsplit("/", 1)[-1].split("?")[0])             # «Scarica Allegato»: meglio il nome del file
        kind = kind or classify(title, full)                      # «Scarica Allegato» dice già che è un allegato; se no, vale il nome del file
        if kind is None or not (is_file or (kind in ("DOMANDA", "FORMULARIO", "ALLEGATO") and same and re.search(r"scarica|download|allegat|modul|domanda|formulari", text or "", re.I))):
            continue
        norm = research.normalize_url(full)
        if norm in known or norm in out or norm == research.normalize_url(page_url):
            continue
        rank = {"DOMANDA": 0, "FORMULARIO": 1, "ALLEGATO": 2, "ISTRUZIONI": 3, "AVVISO": 4}[kind] + (0 if is_file else 0.5)
        out[norm] = {"url": full, "title": title[:160], "kind": kind, "rank": rank, "is_file": is_file}
    return sorted(out.values(), key=lambda x: (x["rank"], x["title"]))


def _page_links(url: str) -> Tuple[Optional[str], List[Tuple[str, str]]]:
    try:
        raw, final, ctype = research.http_get(url, limited=False, timeout=14.0)
    except research.ResearchError:
        return None, []
    if raw[:4] == b"%PDF" or "html" not in ctype and ctype not in ("", "text/plain"):
        return final, []
    _, _, links = research.html_to_text(research._decode(raw, ctype))
    return final, links


def _download(c: Dict[str, Any]) -> Dict[str, Any]:
    try:
        raw, final, ctype = research.http_get(c["url"], max_bytes=MAX_FILE_BYTES, limited=False, timeout=20.0)
    except research.ResearchError as exc:
        return {**c, "error": str(exc)}
    text, pages, warnings, fmt = read_text(raw, final, ctype)
    return {**c, "raw": raw, "final": final, "ctype": ctype, "text": text, "pages": pages, "warnings": warnings, "format": fmt}


# ------------------------------------------------------------------------------------------------ raccolta per un bando
def _save_doc(bando_id: str, d: Dict[str, Any]) -> Dict[str, Any]:
    items = extract_items(d.get("text") or "", d["kind"]) if d.get("text") else {k: [] for k in ITEM_KINDS}
    name = urllib.parse.unquote(d["final"].rsplit("/", 1)[-1].split("?")[0]) or d["title"]
    sha = events.save_bando_file(bando_id, name, d["raw"], d.get("ctype"))
    row = {"sha256": sha, "url": d["final"], "title": d["title"], "kind": d["kind"], "format": d["format"], "size_bytes": len(d["raw"]), "pages": d.get("pages"),
           "warnings": d.get("warnings") or [], "items": items}
    with connect() as conn:
        conn.execute("INSERT INTO application_docs (bando_id, sha256, url, title, kind, content_type, size_bytes, pages, fetched_at, items, warnings) VALUES (?,?,?,?,?,?,?,?,?,?,?) "
                     "ON CONFLICT (bando_id, sha256) DO UPDATE SET url=excluded.url, title=excluded.title, kind=excluded.kind, size_bytes=excluded.size_bytes, pages=excluded.pages, "
                     "fetched_at=excluded.fetched_at, items=excluded.items, warnings=excluded.warnings",
                     (bando_id, sha, d["final"], d["title"][:200], d["kind"], d.get("ctype"), len(d["raw"]), d.get("pages"), events.now_iso(),
                      json.dumps({"format": d["format"], **items}, ensure_ascii=False), json.dumps(row["warnings"], ensure_ascii=False)))
    return row


def collect(bando_id: str, budget_s: float = 40.0, actor: str = "sistema") -> Dict[str, Any]:
    """Cerca e scarica i documenti di domanda del bando; ritorna cosa è stato trovato. Rilancio sicuro: i documenti già presi si aggiornano, non si duplicano."""
    t0 = time.monotonic()
    with connect() as conn:
        b = conn.execute("SELECT bando_id, name, source_url FROM bandi WHERE bando_id=?", (bando_id,)).fetchone()
        if not b:
            raise LookupError(bando_id)
        stored = conn.execute("SELECT sha256, name, url, text FROM bando_sources WHERE bando_id=?", (bando_id,)).fetchall()
    known = {research.normalize_url(s["url"]) for s in stored if s["url"]}
    pages = [u for u in dict.fromkeys([b["source_url"], *[s["url"] for s in stored if s["url"] and not _EXT.search(s["url"])]]) if u][:4]
    cands: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for final, links in pool.map(_page_links, pages):
            if final:
                cands += _candidate_links(final, links, known)
    # una pagina «Modulistica» non è il modulo: si apre (un solo salto) per prendere i file che elenca; se non ne elenca, resta la pagina stessa
    hubs = [c for c in cands if not c["is_file"]][:4]
    if hubs:
        expanded: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=4) as pool:
            for final, links in pool.map(_page_links, [h["url"] for h in hubs]):
                if final:
                    expanded += [c for c in _candidate_links(final, links, known) if c["is_file"]]
        if expanded:
            cands = [c for c in cands if c["is_file"]] + expanded
    seen, uniq = set(), []
    for c in sorted(cands, key=lambda x: (x["rank"], x["title"])):
        key = research.normalize_url(c["url"])
        if key not in seen:
            seen.add(key)
            uniq.append(c)
    uniq = uniq[:MAX_DOCS]
    # i documenti già letti per lo studio (bando, avviso…) non si riscaricano: se ne usano testo e file già salvati
    docs: List[Dict[str, Any]] = []
    pool = ThreadPoolExecutor(max_workers=6)
    futures = [pool.submit(_download, c) for c in uniq]
    done, _ = wait(futures, timeout=max(5.0, budget_s - (time.monotonic() - t0)))
    pool.shutdown(wait=False, cancel_futures=True)
    errors = []
    for f in futures:
        if f not in done:
            continue
        d = f.result()
        if d.get("error"):
            errors.append({"title": d["title"], "url": d["url"], "error": d["error"]})
            continue
        docs.append(_save_doc(bando_id, d))
    # documenti principali già in memoria dallo studio: si rileggono per elencare allegati e dichiarazioni
    for s in stored:
        name = s["name"] or ""
        kind = classify(name, s["url"] or name) or "AVVISO"
        items = extract_items(s["text"] or "", "FORMULARIO" if kind == "FORMULARIO" else "")
        if not any(items.values()):
            continue
        with connect() as conn:
            conn.execute("INSERT INTO application_docs (bando_id, sha256, url, title, kind, content_type, size_bytes, pages, fetched_at, items, warnings) VALUES (?,?,?,?,?,?,?,?,?,?,?) "
                         "ON CONFLICT (bando_id, sha256) DO UPDATE SET items=excluded.items, fetched_at=excluded.fetched_at",
                         (bando_id, s["sha256"], s["url"] or "", name[:200], kind if kind in KINDS else "AVVISO", None, None, None, events.now_iso(),
                          json.dumps({"format": "STUDIO", **items}, ensure_ascii=False), "[]"))
        docs.append({"sha256": s["sha256"], "url": s["url"], "title": name, "kind": kind, "format": "STUDIO", "size_bytes": None, "pages": None, "warnings": [], "items": items})
    note = None if docs else ("Nessun documento di domanda pubblicato trovato sulla pagina del bando: molti enti li pubblicano solo sulla piattaforma di presentazione (con accesso)." if not errors
                              else "I documenti trovati non si sono potuti scaricare.")
    with connect() as conn:
        conn.execute("INSERT INTO application_runs (bando_id, ts, docs, note) VALUES (?,?,?,?) ON CONFLICT (bando_id) DO UPDATE SET ts=excluded.ts, docs=excluded.docs, note=excluded.note",
                     (bando_id, events.now_iso(), len(docs), note))
    events.record("bando.application", f"Documenti di domanda di «{(b['name'] or bando_id)[:70]}»: {len(docs)} trovati" + (f", {len(errors)} non scaricabili" if errors else ""),
                  bando_id=bando_id, actor=actor, status="OK" if docs else "WARN", details={"candidates": len(uniq), "errors": errors[:5], "pages": pages})
    return {"bando_id": bando_id, "found": len(docs), "errors": errors, "note": note, "seconds": round(time.monotonic() - t0, 1)}


# ------------------------------------------------------------------------------------------------ lettura
def get(bando_id: str) -> Dict[str, Any]:
    with connect() as conn:
        docs = conn.execute("SELECT sha256, url, title, kind, content_type, size_bytes, pages, fetched_at, items, warnings FROM application_docs WHERE bando_id=? ORDER BY fetched_at DESC, title", (bando_id,)).fetchall()
        run = conn.execute("SELECT ts, docs, note FROM application_runs WHERE bando_id=?", (bando_id,)).fetchone()
        has_file = {r["sha256"] for r in conn.execute("SELECT sha256 FROM bando_files WHERE bando_id=?", (bando_id,)).fetchall()}
    out_docs, grouped = [], {k: [] for k in ITEM_KINDS}
    order = {"DOMANDA": 0, "FORMULARIO": 1, "ALLEGATO": 2, "ISTRUZIONI": 3, "AVVISO": 4}
    for r in sorted(docs, key=lambda r: (order.get(r["kind"], 9), r["title"])):
        data = json.loads(r["items"] or "{}")
        counts = {k: len(data.get(k) or []) for k in ITEM_KINDS}
        out_docs.append({"sha256": r["sha256"], "url": r["url"], "title": r["title"], "kind": r["kind"], "kind_label": KINDS.get(r["kind"], r["kind"]), "format": data.get("format"),
                         "size_bytes": r["size_bytes"], "pages": r["pages"], "fetched_at": r["fetched_at"], "warnings": json.loads(r["warnings"] or "[]"), "counts": counts,
                         "downloadable": r["sha256"] in has_file})
        for k in ITEM_KINDS:
            for text in data.get(k) or []:
                grouped[k].append({"text": text, "doc": r["title"], "sha256": r["sha256"]})
    return {"bando_id": bando_id, "collected_at": (run or {}).get("ts"), "note": (run or {}).get("note"), "docs": out_docs,
            "items": {k: {"label": ITEM_KINDS[k], "list": grouped[k]} for k in ITEM_KINDS}, "totals": {k: len(grouped[k]) for k in ITEM_KINDS}}
