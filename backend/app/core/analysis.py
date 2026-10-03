"""Lettura di tutti i documenti in memoria di un bando, con il resoconto per ogni documento.

Regola di questa parte: **nessun documento può risultare «vuoto» senza dire perché**. Per ogni fonte si registra quanti requisiti ha dato, in che lingua è,
quanto testo è stato usato, e — se non ha dato nulla — il motivo (testo non decodificabile, documento lungo che non nomina il bando, testo troppo breve, nessuna frase
con obblighi/limiti/importi). Il resoconto è salvato con la fonte e lo vede il Quartier Generale.

Tre decisioni uguali per ogni bando:
- un foglio elettronico è un dato di riferimento, non un testo normativo: si conserva e non si legge;
- tra le edizioni dello stesso documento (circolare del 2025, del 2026…) conta solo l'ultima;
- un documento «severo» (si intitola come il bando o lo cita spesso) si legge intero; gli altri solo nei passaggi che nominano il bando, e le regole
  numeriche che ne ricavo si pubblicano solo se confermate da due fonti.
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Set

from app.core import events, llm, research
from app.core.ingestion import Ingestion
from app.core.requirements_extractor import detect_lang, looks_garbled

# un documento che cita il bando almeno STRICT_MIN_MENTIONS volte, o almeno STRICT_SHORT_MENTIONS volte con alta densità, parla di lui
STRICT_MIN_MENTIONS = 8
STRICT_SHORT_MENTIONS = 3
STRICT_DENSITY_PER_1K = 0.5


def is_reference_dataset(s: Dict[str, Any]) -> bool:
    """Un foglio elettronico (es. l'elenco delle imprese finanziate) è un dato di riferimento, non un testo normativo:
    non contiene obblighi né tetti e leggerlo come un bando riempirebbe i requisiti di righe di anagrafica."""
    ctype = (s.get("content_type") or "").lower()
    return "spreadsheetml" in ctype or (s.get("name") or "").lower().endswith((".xlsx", ".xlsm", ".xls"))


def name_parts(bando_name: str) -> List[List[str]]:
    """Le espressioni che nominano il bando: ogni parte del nome (prima e dopo il trattino lungo), senza la parentesi."""
    base = re.sub(r"\([^)]*\)", " ", bando_name)
    parts: List[List[str]] = []
    for p in re.split(r"\s[—–-]\s", base):
        words = re.findall(r"[\wà-ù/.&]+", p)
        meaningful = [w for w in words if w.lower() not in _STOP and not re.fullmatch(r"(19|20)\d\d", w)]      # «Bando 2026» non identifica nulla
        if len(meaningful) >= 2:
            parts.append(words)
    return parts


def mentions(text: str, bando_name: str) -> int:
    """Quante volte il testo nomina il bando (la parte del nome più citata)."""
    best = 0
    for words in name_parts(bando_name):
        best = max(best, len(re.findall(r"[\s\W]*".join(re.escape(w) for w in words), text, re.I)))
    return best


def is_strict_source(s: Dict[str, Any], bando_name: str, text: str) -> bool:
    """Parla senza dubbio di questo bando: lo dice il titolo o l'indirizzo, oppure lo cita spesso. Un bilancio che lo nomina due volte in 500 pagine no."""
    if research.match_score(bando_name, f"{s.get('name') or ''} {research.url_text(s.get('url') or '')}") is not None:
        return True
    n = mentions(text, bando_name)
    return n >= STRICT_MIN_MENTIONS or (n >= STRICT_SHORT_MENTIONS and n * 1000 / max(len(text), 1) >= STRICT_DENSITY_PER_1K)


_DATE_IN_NAME = re.compile(r"(\d{1,2})[.\-_](\d{1,2})[.\-_](\d{2,4})")


def _stem(s: Dict[str, Any]) -> str:
    raw = (s.get("url") or s.get("name") or "").split("?")[0].rsplit("/", 1)[-1].rsplit(".", 1)[0].lower()
    raw = _DATE_IN_NAME.sub("", raw)
    raw = re.sub(r"v[.\-_ ]?\d+(?:[.\-_]\d+)*|clean|sito|def\b|firmato|testo[ -]coordinato", "", raw)
    return re.sub(r"[^a-z0-9]", "", raw)


def _version_key(s: Dict[str, Any]) -> tuple:
    m = re.search(r"/(20\d\d)/(\d{1,2})/", s.get("url") or "")
    d = _DATE_IN_NAME.search((s.get("url") or s.get("name") or "").rsplit("/", 1)[-1])
    year, month = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    day = 0
    if d:
        day, month2, yy = int(d.group(1)), int(d.group(2)), int(d.group(3))
        year = year or (yy + 2000 if yy < 100 else yy if yy >= 1000 else 0)
        month = month or month2
    return (year, month, day, s.get("ts") or "")


def superseded_shas(sources: List[Dict[str, Any]]) -> Dict[str, str]:
    """{impronta della fonte superata: nome di quella che la sostituisce}: edizioni diverse dello stesso documento, vale la più recente."""
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for s in sources:
        stem = _stem(s)
        if len(stem) >= 8 and not is_reference_dataset(s):
            groups.setdefault(stem, []).append(s)
    out: Dict[str, str] = {}
    for members in groups.values():
        if len(members) < 2:
            continue
        newest = max(members, key=_version_key)
        for s in members:
            if s["sha256"] != newest["sha256"] and _version_key(s) < _version_key(newest):
                out[s["sha256"]] = newest["name"]
    return out


_STOP = {"bando", "avviso", "agevolazioni", "agevolazione", "incentivo", "incentivi", "contributi", "contributo", "delle", "della", "dello", "dei", "degli", "per", "con", "anno",
         # parole che identificano l'ente e non il bando: un altro bando della stessa Camera di Commercio le condivide
         "camera", "commercio", "regione", "provincia", "comune", "metropolitana", "ministero", "cciaa", "ente", "citta"}


def distinctive_tokens(name: str) -> List[str]:
    """Le parole che identificano il bando: tutto il nome tranne la parentesi, gli anni e le parole generiche (un anno non distingue un bando da quello di un'altra regione)."""
    base = re.sub(r"\([^)]*\)", " ", name).lower()
    return [w for w in re.findall(r"[a-zà-ù0-9]+(?:\.[0-9]+)?", base) if len(w) >= 4 and w not in _STOP and not re.fullmatch(r"(19|20)\d\d", w)]


def is_about(name: str, doc: Dict[str, Any]) -> bool:
    """Un documento entra solo se parla davvero di questo bando: ne cita il nome, oppure almeno il 60% delle parole che lo identificano compare nel titolo, nell'indirizzo o nel testo.
    Evita che il bando di un'altra regione con un nome simile riempia i requisiti di regole non sue."""
    text = doc.get("text", "")[:400_000]
    if mentions(text, name) >= 1:
        return True
    tokens = distinctive_tokens(name)
    if not tokens:
        return True
    hay = f"{doc.get('title', '')} {doc.get('url', '')} {text}".lower()
    return sum(1 for t in tokens if t in hay) >= math.ceil(0.6 * len(tokens))


def _label(s: Dict[str, Any]) -> str:
    return (s["name"] + (f" — {s['url']}" if s.get("url") else "") + (" (fonte secondaria)" if s.get("tier") == "SECONDARIA" else ""))[:300]


def source_note(chars: int, used: int, garbled: bool, reqs: int, rules_hint: bool = False) -> str:
    if reqs:
        return ""
    if garbled:
        return "Testo non decodificabile (font particolari o scansione): serve il file originale con testo selezionabile o un OCR"
    if chars < 300:
        return "Testo troppo breve per contenere condizioni: probabilmente la pagina è costruita in JavaScript o è solo un indice"
    if used == 0:
        return "Documento lungo che non nomina mai il bando: ignorato perché non pertinente"
    return "Nessuna frase con obblighi, limiti o importi riconosciuta: leggilo a mano (potrebbe essere un documento solo descrittivo)"


def run_analysis(bando_id: str) -> Dict[str, Any]:
    b = Ingestion.get_bando(bando_id)
    name = b["name"] if b else ""
    sources = events.list_bando_sources(bando_id)
    old = superseded_shas(sources)
    srcs: List[tuple] = []
    strict: Set[str] = set()
    meta: Dict[str, Dict[str, Any]] = {}
    for s in sources:
        text = s["text"]
        label = _label(s)
        if is_reference_dataset(s):
            meta[s["sha256"]] = {"label": label, "chars": len(text), "used_chars": 0, "lang": "—", "garbled": False, "special": "Elenco di dati di riferimento (non è un testo del bando): conservato, non letto per ricavare regole"}
            continue
        if s.get("origin") != "UPLOAD" and not is_about(name, {"title": s.get("name"), "url": s.get("url"), "text": text}):
            meta[s["sha256"]] = {"label": label, "chars": len(text), "used_chars": 0, "lang": detect_lang(text), "garbled": False,
                                 "special": "Non parla di questo bando (pagina o documento generico): conservato, non letto per ricavare regole"}
            continue
        if s["sha256"] in old:
            meta[s["sha256"]] = {"label": label, "chars": len(text), "used_chars": 0, "lang": detect_lang(text), "garbled": False,
                                 "special": f"Edizione precedente dello stesso documento: vale la più recente ({old[s['sha256']][:70]}). Conservata, non letta"}
            continue
        # Il filtro «solo i passaggi che nominano il bando» serve per le leggi e i manuali che lo citano di passaggio.
        # Un documento che parla senza dubbio del bando va letto per intero, altrimenti di un decreto di 200 pagine che dice sempre «il Fondo» resterebbe il 3%.
        is_strict = is_strict_source(s, name, text)
        focus = text if is_strict else research.focus_text(text, name)
        garbled = looks_garbled(text)
        meta[s["sha256"]] = {"label": label, "chars": len(text), "used_chars": len(focus), "lang": detect_lang(text), "garbled": garbled}
        if focus.strip() and not garbled:
            srcs.append((label, focus))
            # Affidabile per le regole: un documento severo, un testo caricato apposta da una persona, o un documento breve (che si legge intero e
            # difficilmente è un bilancio). Il rischio sono i documenti lunghi e generici, dove una frase sparsa basta a far scattare una regola.
            if is_strict or s.get("origin") == "UPLOAD" or len(text) <= research.LONG_DOC_CHARS:
                strict.add(label)
    Ingestion.confirm(bando_id)
    passes = None
    client = llm.get_client()
    if client is not None and srcs:                               # Stadio 3: solo se c'è un modello collegato; il confronto tra passaggi lo fa il codice
        prose = "\n\n".join(f"[{label}]\n{focus}" for label, focus in srcs)[:llm.MAX_TEXT_CHARS]
        passes = [p for p in llm.extract_passes(client, prose) if p] or None
    outcome = Ingestion.extract(bando_id, sources=srcs, ai_passes=passes, strict_refs=strict)
    reqs = outcome.requirements or []
    by_ref: Dict[str, int] = {}
    for r in reqs:
        by_ref[r["source_ref"]] = by_ref.get(r["source_ref"], 0) + 1
    report: List[Dict[str, Any]] = []
    for s in sources:
        m = meta[s["sha256"]]
        n = by_ref.get(m["label"], 0)
        note = m.get("special") or source_note(m["chars"], m["used_chars"], m["garbled"], n)
        events.save_source_analysis(bando_id, s["sha256"], {"requirements": n, "lang": m["lang"], "used_chars": m["used_chars"], "chars": m["chars"], "note": note})
        report.append({"sha256": s["sha256"], "name": s["name"], "url": s.get("url"), "requirements": n, "lang": m["lang"], "note": note})
    return {"outcome": outcome, "requirements": reqs, "report": report, "sources": len(sources)}
