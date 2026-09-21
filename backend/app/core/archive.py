"""Archivio bandi del Quartier Generale: il manager può vedere, correggere ed eliminare tutto ciò che è in memoria.

Nulla di ciò che riguarda il registro di asseverazione (tabella ``anchors``) si può cancellare o modificare: è append-only per costruzione, e cancellarne
una riga romperebbe la catena di firme (è ciò che la rende verificabile da terzi).
"""
from __future__ import annotations

import csv
import io
import json
import zipfile
from typing import Any, Dict, List, Optional

from app.core import bandi, db, events
from app.core.db import connect
from app.core.ingestion import Ingestion, normalize_value

PROTECTED_TABLES = {"anchors"}


def list_archive() -> List[Dict[str, Any]]:
    bandi.ensure_seeded()
    out = []
    with connect() as conn:
        for b in conn.execute("SELECT * FROM bandi ORDER BY CASE catalog_status WHEN 'CURATED' THEN 1 ELSE 0 END, bando_id").fetchall():
            bid = b["bando_id"]
            meta = bandi._meta(conn, bid)
            s = conn.execute("SELECT COUNT(*) n, COALESCE(SUM(LENGTH(text)),0) chars FROM bando_sources WHERE bando_id=?", (bid,)).fetchone()
            f = conn.execute("SELECT COUNT(*) n, COALESCE(SUM(size_bytes),0)::bigint size FROM bando_files WHERE bando_id=?", (bid,)).fetchone()
            r = conn.execute("SELECT COUNT(*) n, COALESCE(SUM((status='PENDING_REVIEW')::int),0) pend FROM rules WHERE bando_id=?", (bid,)).fetchone()
            q = conn.execute("SELECT COUNT(*) n, COALESCE(SUM((kind='DA_REVISIONARE')::int),0) rev FROM requirements WHERE bando_id=?", (bid,)).fetchone()
            runs = conn.execute("SELECT COUNT(*) n FROM runs WHERE bando_id=? AND kind='VALIDATE'", (bid,)).fetchone()["n"]
            out.append({"bando_id": bid, "name": b["name"], "curated": bool(meta.get("curated")), "extraction_status": b["extraction_status"], "sources": s["n"], "chars": s["chars"],
                        "files": f["n"], "files_bytes": f["size"], "rules": r["n"], "rules_pending": int(r["pend"] or 0), "requirements": q["n"],
                        "requirements_to_review": int(q["rev"] or 0), "runs": runs, "origin": "predefinito" if meta.get("curated") else ("web" if bid.startswith("WEB-") else "caricato")})
    return out


def tombstones() -> List[Dict[str, Any]]:
    with connect() as conn:
        return [dict(t) for t in conn.execute("SELECT bando_id, ts FROM bando_tombstones ORDER BY ts DESC").fetchall()]


def bando_archive(bando_id: str) -> Optional[Dict[str, Any]]:
    d = bandi.get_bando_detail(bando_id)
    if d is None:
        return None
    with connect() as conn:
        src = conn.execute("SELECT ts, name, sha256, LENGTH(text) chars, url, tier, pages, origin, content_type, file_sha256, analysis, warnings FROM bando_sources WHERE bando_id=? "
                           "ORDER BY CASE tier WHEN 'UFFICIALE' THEN 0 WHEN 'SECONDARIA' THEN 2 ELSE 1 END, ts", (bando_id,)).fetchall()
        files = {r["sha256"]: dict(r) for r in conn.execute("SELECT sha256, name, content_type, size_bytes FROM bando_files WHERE bando_id=?", (bando_id,)).fetchall()}
    sources = []
    for s in src:
        x = dict(s)
        x["analysis"] = json.loads(x["analysis"]) if x.get("analysis") else None
        x["warnings"] = json.loads(x["warnings"]) if x.get("warnings") else []
        x["file"] = files.get(x.pop("file_sha256") or "")
        sources.append(x)
    d["usage"] = {**d["usage"], "uploaded_sources": sources}
    d["sources_detail"] = sources
    return d


def delete_source(bando_id: str, sha256: str) -> bool:
    with connect() as conn:
        row = conn.execute("SELECT file_sha256, name FROM bando_sources WHERE bando_id=? AND sha256=?", (bando_id, sha256)).fetchone()
        if row is None:
            return False
        conn.execute("DELETE FROM bando_sources WHERE bando_id=? AND sha256=?", (bando_id, sha256))
        if row["file_sha256"]:
            left = conn.execute("SELECT 1 FROM bando_sources WHERE bando_id=? AND file_sha256=?", (bando_id, row["file_sha256"])).fetchone()
            if not left:
                conn.execute("DELETE FROM bando_files WHERE bando_id=? AND sha256=?", (bando_id, row["file_sha256"]))
    return True


def delete_bando(bando_id: str) -> Optional[Dict[str, int]]:
    """Elimina il bando e tutto ciò che ne discende (fonti, file, regole, requisiti, documenti). La cronologia degli eventi e le validazioni già fatte restano."""
    with connect() as conn:
        if not conn.execute("SELECT 1 FROM bandi WHERE bando_id=?", (bando_id,)).fetchone():
            return None
        meta = bandi._meta(conn, bando_id)
        counts = {}
        for table in ("bando_files", "bando_sources", "requirements", "rules", "documents"):
            counts[table] = conn.execute(f"SELECT COUNT(*) c FROM {table} WHERE bando_id=?", (bando_id,)).fetchone()["c"]
            conn.execute(f"DELETE FROM {table} WHERE bando_id=?", (bando_id,))
        conn.execute("DELETE FROM bando_meta WHERE bando_id=?", (bando_id,))
        conn.execute("DELETE FROM bandi WHERE bando_id=?", (bando_id,))
        if meta.get("curated"):  # il catalogo predefinito non deve ricrearlo al prossimo avvio
            conn.execute("INSERT INTO bando_tombstones (bando_id, ts) VALUES (?,?) ON CONFLICT (bando_id) DO UPDATE SET ts=excluded.ts", (bando_id, events.now_iso()))
    return counts


def restore_defaults() -> int:
    with connect() as conn:
        n = conn.execute("SELECT COUNT(*) c FROM bando_tombstones").fetchone()["c"]
        conn.execute("DELETE FROM bando_tombstones")
    bandi.seed()
    return n


def rename_bando(bando_id: str, name: str) -> bool:
    with connect() as conn:
        cur = conn.execute("UPDATE bandi SET name=? WHERE bando_id=?", (name.strip(), bando_id))
        return cur.rowcount > 0


def _refresh_status(conn, bando_id: str) -> None:
    rows = conn.execute("SELECT status FROM rules WHERE bando_id=?", (bando_id,)).fetchall()
    ok = any(r["status"] == "PUBLISHED" for r in rows)
    pend = any(r["status"] == "PENDING_REVIEW" for r in rows)
    conn.execute("UPDATE bandi SET extraction_status=? WHERE bando_id=?", ("COMPLETED" if ok and not pend else "PARTIAL", bando_id))


def set_rule(bando_id: str, key: str, value: Any) -> str:
    """Il manager imposta (o corregge) il valore di una regola: vale come decisione umana. Solleva ValueError se il valore non è valido."""
    if Ingestion.get_bando(bando_id) is None:
        raise KeyError(bando_id)
    normalized = normalize_value(key, value)
    with connect() as conn:
        conn.execute(
            "INSERT INTO rules (bando_id, rule_key, value, origin, status, passes, source_ref) VALUES (?,?,?,?,?,?,?) "
            "ON CONFLICT(bando_id, rule_key) DO UPDATE SET value=excluded.value, origin='HUMAN_REVIEW', status='PUBLISHED', source_ref=excluded.source_ref",
            (bando_id, key, normalized, "HUMAN_REVIEW", "PUBLISHED", None, "Impostata dal manager"))
        _refresh_status(conn, bando_id)
    return normalized


def delete_rule(bando_id: str, key: str) -> bool:
    with connect() as conn:
        cur = conn.execute("DELETE FROM rules WHERE bando_id=? AND rule_key=?", (bando_id, key))
        _refresh_status(conn, bando_id)
        return cur.rowcount > 0


def add_requirement(bando_id: str, topic: str, kind: str, text: str, criteria: List[int], source_ref: str = "Aggiunto dal manager") -> int:
    with connect() as conn:
        seq = conn.execute("SELECT COALESCE(MAX(seq),0)+1 s FROM requirements WHERE bando_id=?", (bando_id,)).fetchone()["s"]
        conn.execute("INSERT INTO requirements (bando_id, seq, topic, kind, text, criteria, source_ref, origin) VALUES (?,?,?,?,?,?,?,?)",
                     (bando_id, seq, topic[:120], kind, text[:2000], json.dumps(sorted(set(criteria))), source_ref, "HUMAN_REVIEW"))
    return int(seq)


def update_requirement(bando_id: str, seq: int, kind: Optional[str] = None, topic: Optional[str] = None, criteria: Optional[List[int]] = None) -> bool:
    with connect() as conn:
        row = conn.execute("SELECT * FROM requirements WHERE bando_id=? AND seq=?", (bando_id, seq)).fetchone()
        if row is None:
            return False
        conn.execute("UPDATE requirements SET kind=?, topic=?, criteria=?, origin='HUMAN_REVIEW' WHERE bando_id=? AND seq=?",
                     (kind or row["kind"], (topic or row["topic"])[:120], json.dumps(sorted(set(criteria))) if criteria is not None else row["criteria"], bando_id, seq))
    return True


def delete_requirement(bando_id: str, seq: int) -> bool:
    with connect() as conn:
        return conn.execute("DELETE FROM requirements WHERE bando_id=? AND seq=?", (bando_id, seq)).rowcount > 0


def export_zip(bando_id: str) -> Optional[bytes]:
    """Tutto il bando in un file: scheda JSON, testi estratti e file originali."""
    d = bando_archive(bando_id)
    if d is None:
        return None
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("bando.json", json.dumps({k: v for k, v in d.items() if k not in ("usage",)}, ensure_ascii=False, indent=2, default=str))
        for i, s in enumerate(events.list_bando_sources(bando_id), 1):
            safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in s["name"])[:60]
            z.writestr(f"testi/{i:02d}_{safe}.txt", s["text"])
            if s.get("file_sha256"):
                f = events.get_bando_file(bando_id, s["file_sha256"])
                if f:
                    ext = ".pdf" if (f.get("content_type") or "").endswith("pdf") else ".html" if "html" in (f.get("content_type") or "") else ""
                    z.writestr(f"originali/{i:02d}_{safe}{ext if not safe.lower().endswith(ext) else ''}", f["data"])
    return buf.getvalue()


# ------------------------------------------------------------------ database: modifica dei dati (tranne il registro firmato)
def db_delete_row(table: str, rowid: str) -> bool:
    from app.core import hq
    if table not in hq.TABLES:
        raise KeyError(table)
    if table in PROTECTED_TABLES:
        raise PermissionError("Il registro delle certificazioni è append-only: le righe non si cancellano")
    with connect() as conn:
        pk = db.pk_columns(conn, table)
        values = db.decode_rowid(rowid)
        if not pk or len(values) != len(pk):
            raise ValueError("Identificativo di riga non valido")
        where = " AND ".join(f"{c}=?" for c in pk)
        return conn.execute(f"DELETE FROM {table} WHERE {where}", tuple(values)).rowcount > 0


def db_clear_table(table: str) -> int:
    from app.core import hq
    if table not in hq.TABLES:
        raise KeyError(table)
    if table in PROTECTED_TABLES:
        raise PermissionError("Il registro delle certificazioni è append-only: non si svuota")
    with connect() as conn:
        return conn.execute(f"DELETE FROM {table}").rowcount


def db_export_csv(table: str, full: bool = True) -> str:
    from app.core import hq
    if table not in hq.TABLES:
        raise KeyError(table)
    with connect() as conn:
        pk = db.pk_columns(conn, table)
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
    out = io.StringIO()
    if not rows:
        return ""
    w = csv.writer(out)
    w.writerow(["_rowid"] + list(rows[0].keys()))
    for r in rows:
        w.writerow([db.encode_rowid(pk, r)] + [f"[{len(v)} byte]" if isinstance(v, (bytes, bytearray, memoryview)) else v for v in r.values()])
    return out.getvalue()
