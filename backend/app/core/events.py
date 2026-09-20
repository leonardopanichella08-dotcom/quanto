"""Memoria del sistema: registro di ogni operazione (timeline), esecuzioni salvate e documenti lavorati.

Regole:
- registrare non deve MAI far fallire l'operazione principale: ogni errore di scrittura è loggato e ignorato;
- nessun dato personale: le descrizioni delle righe di costo passano dallo scrubber (IBAN/codici fiscali -> token);
- i documenti (export, import, bandi) si tracciano con nome, hash SHA-256 e dimensione; il testo integrale si conserva
  solo per le fonti dei bandi (serve a rielaborarle).
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional

from app.core.anonymizer import PrivacyAnonymizer
from app.core.db import connect

logger = logging.getLogger("quanto.events")
MAX_DETAILS = 20_000
MAX_SOURCE_TEXT = 500_000


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _dump(obj: Any, limit: int = MAX_DETAILS) -> Optional[str]:
    if obj is None:
        return None
    text = json.dumps(obj, default=str, ensure_ascii=False)
    return text if len(text) <= limit else json.dumps({"truncated": True, "size": len(text)})


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Timer:
    def __init__(self) -> None:
        self.start = time.perf_counter()

    @property
    def ms(self) -> float:
        return round((time.perf_counter() - self.start) * 1000, 2)


@contextmanager
def timed() -> Iterator[Timer]:
    yield Timer()


def record(op: str, summary: str, status: str = "OK", project_id: Optional[str] = None, bando_id: Optional[str] = None,
           actor: str = "api", duration_ms: Optional[float] = None, details: Optional[Dict[str, Any]] = None,
           run_id: Optional[int] = None) -> Optional[int]:
    try:
        with connect() as conn:
            cur = conn.execute(
                "INSERT INTO events (ts, op, status, actor, project_id, bando_id, duration_ms, summary, details, run_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (now_iso(), op, status, actor, project_id, bando_id, duration_ms, summary[:400], _dump(details), run_id))
            return int(cur.lastrowid)
    except Exception:  # la memoria non deve mai rompere l'operazione
        logger.exception("Impossibile registrare l'evento %s", op)
        return None


def save_run(kind: str, project_id: Optional[str], bando_id: Optional[str], request: Dict[str, Any], response: Dict[str, Any],
             merkle_root: Optional[str] = None) -> Optional[int]:
    try:
        req = json.loads(json.dumps(request, default=str))
        for item in req.get("cost_items", []) or []:
            if isinstance(item.get("description"), str):
                item["description"] = PrivacyAnonymizer.scrub_free_text(item["description"])
        with connect() as conn:
            cur = conn.execute(
                "INSERT INTO runs (ts, kind, project_id, bando_id, merkle_root, request_json, response_json) VALUES (?,?,?,?,?,?,?)",
                (now_iso(), kind, project_id, bando_id, merkle_root, _dump(req, 400_000), _dump(response, 1_500_000)))
            return int(cur.lastrowid)
    except Exception:
        logger.exception("Impossibile salvare l'esecuzione %s", kind)
        return None


def add_document(kind: str, name: str, data: bytes, bando_id: Optional[str] = None, project_id: Optional[str] = None,
                 meta: Optional[Dict[str, Any]] = None) -> Optional[int]:
    try:
        with connect() as conn:
            cur = conn.execute(
                "INSERT INTO documents (ts, kind, name, sha256, size_bytes, bando_id, project_id, meta) VALUES (?,?,?,?,?,?,?,?)",
                (now_iso(), kind, name[:200], sha256_hex(data), len(data), bando_id, project_id, _dump(meta, 4000)))
            return int(cur.lastrowid)
    except Exception:
        logger.exception("Impossibile registrare il documento %s", name)
        return None


def save_bando_source(bando_id: str, name: str, text: str, url: Optional[str] = None, tier: Optional[str] = None,
                      content_type: Optional[str] = None, pages: Optional[int] = None, origin: str = "UPLOAD") -> str:
    """Salva il testo integrale di una fonte del bando (caricata a mano o scaricata dal web) nella memoria."""
    digest = sha256_hex(text.encode("utf-8"))
    with connect() as conn:
        conn.execute("INSERT OR REPLACE INTO bando_sources (bando_id, ts, name, sha256, text, url, tier, content_type, pages, origin) VALUES (?,?,?,?,?,?,?,?,?,?)",
                     (bando_id, now_iso(), name[:200], digest, text[:MAX_SOURCE_TEXT], url, tier, content_type, pages, origin))
    return digest


def list_bando_sources(bando_id: str) -> List[dict]:
    """Fonti in memoria: prima le ufficiali, poi le altre (con il testo)."""
    with connect() as conn:
        rows = conn.execute("SELECT * FROM bando_sources WHERE bando_id=? ORDER BY CASE tier WHEN 'UFFICIALE' THEN 0 WHEN 'SECONDARIA' THEN 2 ELSE 1 END, ts", (bando_id,)).fetchall()
    return [dict(r) for r in rows]


def list_events(op: Optional[str] = None, project_id: Optional[str] = None, bando_id: Optional[str] = None,
                status: Optional[str] = None, limit: int = 100, before_id: Optional[int] = None) -> List[dict]:
    clauses, args = [], []
    for col, val in (("op", op), ("project_id", project_id), ("bando_id", bando_id), ("status", status)):
        if val:
            clauses.append(f"{col} = ?")
            args.append(val)
    if before_id:
        clauses.append("id < ?")
        args.append(before_id)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM events {where} ORDER BY id DESC LIMIT ?", (*args, max(1, min(limit, 500)))).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["details"] = json.loads(d["details"]) if d.get("details") else None
        out.append(d)
    return out
