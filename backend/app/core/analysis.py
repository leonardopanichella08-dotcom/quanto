"""Lettura di tutti i documenti in memoria di un bando, con il resoconto per ogni documento.

Regola di questa parte: **nessun documento può risultare «vuoto» senza dire perché**. Per ogni fonte si registra quanti requisiti ha dato, in che lingua è,
quanto testo è stato usato, e — se non ha dato nulla — il motivo (testo non decodificabile, documento lungo che non nomina il bando, testo troppo breve, nessuna frase
con obblighi/limiti/importi). Il resoconto è salvato con la fonte e lo vede il Quartier Generale.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.core import events, llm, research
from app.core.ingestion import Ingestion
from app.core.requirements_extractor import detect_lang, looks_garbled


def is_reference_dataset(s: Dict[str, Any]) -> bool:
    """Un foglio elettronico (es. l'elenco delle imprese finanziate) è un dato di riferimento, non un testo normativo:
    non contiene obblighi né tetti e leggerlo come un bando riempirebbe i requisiti di righe di anagrafica."""
    ctype = (s.get("content_type") or "").lower()
    return "spreadsheetml" in ctype or (s.get("name") or "").lower().endswith((".xlsx", ".xlsm", ".xls"))


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
    srcs: List[tuple] = []
    meta: Dict[str, Dict[str, Any]] = {}
    for s in sources:
        text = s["text"]
        label = _label(s)
        if is_reference_dataset(s):
            meta[s["sha256"]] = {"label": label, "chars": len(text), "used_chars": 0, "lang": "—", "garbled": False, "reference": True}
            continue
        focus = research.focus_text(text, name)
        garbled = looks_garbled(text)
        meta[s["sha256"]] = {"label": label, "chars": len(text), "used_chars": len(focus), "lang": detect_lang(text), "garbled": garbled}
        if focus.strip() and not garbled:
            srcs.append((label, focus))
    Ingestion.confirm(bando_id)
    passes = None
    client = llm.get_client()
    if client is not None and srcs:                               # Stadio 3: solo se c'è un modello collegato; il confronto tra passaggi lo fa il codice
        prose = "\n\n".join(f"[{label}]\n{focus}" for label, focus in srcs)[:llm.MAX_TEXT_CHARS]
        passes = [p for p in llm.extract_passes(client, prose) if p] or None
    outcome = Ingestion.extract(bando_id, sources=srcs, ai_passes=passes)
    reqs = outcome.requirements or []
    by_ref: Dict[str, int] = {}
    for r in reqs:
        by_ref[r["source_ref"]] = by_ref.get(r["source_ref"], 0) + 1
    report: List[Dict[str, Any]] = []
    for s in sources:
        m = meta[s["sha256"]]
        n = by_ref.get(m["label"], 0)
        note = "Elenco di dati di riferimento (non è un testo del bando): conservato, non letto per ricavare regole" if m.get("reference") else source_note(m["chars"], m["used_chars"], m["garbled"], n)
        events.save_source_analysis(bando_id, s["sha256"], {"requirements": n, "lang": m["lang"], "used_chars": m["used_chars"], "chars": m["chars"], "note": note})
        report.append({"sha256": s["sha256"], "name": s["name"], "url": s.get("url"), "requirements": n, "lang": m["lang"], "note": note})
    return {"outcome": outcome, "requirements": reqs, "report": report, "sources": len(sources)}
