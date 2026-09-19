"""Quartier Generale (HQ): accesso con codice, memoria del sistema, timeline, dossier e database.

Sicurezza: il codice si verifica SEMPRE sul server (mai nel frontend), a tempo costante, con blocco temporaneo dopo
tentativi errati. Il codice predefinito è ``QUANTO_1`` e si sostituisce con ``QUANTO_HQ_CODE``: un codice breve e
pubblicato nella documentazione è una barriera di comodità, non un segreto forte — in produzione va cambiato.
Tutto ciò che l'HQ espone è di sola lettura.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import tempfile
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

from app.core import bandi, events
from app.core.db import connect, db_path
from app.core.operations import OPERATIONS
from app.core.registry import Registry, current_public_key

DEFAULT_CODE = "QUANTO_1"
TOKEN_TTL_S = 2 * 3600
MAX_FAILURES = 5
LOCK_WINDOW_S = 600

_FAILURES: Dict[str, List[float]] = defaultdict(list)

# tabelle consultabili (whitelist) e colonne pesanti da riassumere
TABLES = ["anchors", "bandi", "bando_meta", "rules", "requirements", "bando_sources", "events", "runs", "documents"]
HEAVY = {"runs": ("request_json", "response_json"), "bando_sources": ("text",), "bando_meta": ("meta",)}


class HQAuthError(Exception):
    pass


class HQLocked(Exception):
    def __init__(self, retry_after: int):
        super().__init__("Troppi tentativi")
        self.retry_after = retry_after


def _secret() -> bytes:
    raw = os.getenv("QUANTO_HQ_SECRET") or os.getenv("QUANTO_JWT_SECRET") or os.getenv("QUANTO_SIGNING_KEY") or "dev-hq-secret"
    return hashlib.sha256(b"quanto-hq|" + raw.encode()).digest()


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def issue_token(now: Optional[float] = None) -> str:
    payload = _b64(json.dumps({"sub": "hq", "exp": int((now or time.time()) + TOKEN_TTL_S)}, separators=(",", ":")).encode())
    return f"{payload}.{_b64(hmac.new(_secret(), payload.encode(), hashlib.sha256).digest())}"


def verify_token(token: Optional[str], now: Optional[float] = None) -> bool:
    try:
        payload, sig = (token or "").split(".")
        if not hmac.compare_digest(hmac.new(_secret(), payload.encode(), hashlib.sha256).digest(), _unb64(sig)):
            return False
        claims = json.loads(_unb64(payload))
        return claims.get("sub") == "hq" and claims["exp"] >= (now or time.time())
    except (ValueError, KeyError, TypeError):
        return False


def login(code: str, client: str, now: Optional[float] = None) -> str:
    """Restituisce un token HQ se il codice è corretto; ``HQLocked`` dopo troppi errori; ``HQAuthError`` se errato."""
    t = now or time.time()
    recent = [x for x in _FAILURES[client] if t - x < LOCK_WINDOW_S]
    _FAILURES[client] = recent
    if len(recent) >= MAX_FAILURES:
        raise HQLocked(int(LOCK_WINDOW_S - (t - recent[0])) + 1)
    expected = os.getenv("QUANTO_HQ_CODE", DEFAULT_CODE)
    if not hmac.compare_digest(code.encode("utf-8"), expected.encode("utf-8")):
        _FAILURES[client].append(t)
        raise HQAuthError("Codice non valido")
    _FAILURES[client] = []
    return issue_token(now)


def reset_lockouts() -> None:
    _FAILURES.clear()


# ------------------------------------------------------------------ panoramica
def _count(conn, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) c FROM {table}").fetchone()["c"])  # nome tabella dalla whitelist


def operation_stats() -> Dict[str, Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT op, COUNT(*) n, SUM(status!='OK') errs, AVG(duration_ms) avg_ms, MAX(ts) last_ts FROM events GROUP BY op").fetchall()
    return {r["op"]: {"count": r["n"], "errors": int(r["errs"] or 0), "avg_ms": round(r["avg_ms"], 1) if r["avg_ms"] is not None else None, "last_ts": r["last_ts"]} for r in rows}


def operations_catalog() -> List[Dict[str, Any]]:
    stats = operation_stats()
    return [{**o, "stats": stats.get(o["id"], {"count": 0, "errors": 0, "avg_ms": None, "last_ts": None})} for o in OPERATIONS]


def overview() -> Dict[str, Any]:
    bandi.ensure_seeded()
    path = db_path()
    with connect() as conn:
        counts = {t: _count(conn, t) for t in TABLES}
        projects = conn.execute("SELECT COUNT(DISTINCT project_id) c FROM events WHERE project_id IS NOT NULL").fetchone()["c"]
        validations = conn.execute("SELECT COUNT(*) c FROM runs WHERE kind='VALIDATE'").fetchone()["c"]
        last_validation = conn.execute("SELECT ts FROM runs WHERE kind='VALIDATE' ORDER BY id DESC LIMIT 1").fetchone()
        docs_by_kind = {r["kind"]: r["n"] for r in conn.execute("SELECT kind, COUNT(*) n FROM documents GROUP BY kind").fetchall()}
        events_by_day = [dict(r) for r in conn.execute("SELECT substr(ts,1,10) day, COUNT(*) n FROM events GROUP BY day ORDER BY day DESC LIMIT 14").fetchall()]
    chain = Registry.verify_chain()
    key = current_public_key()
    size = os.path.getsize(path) if os.path.exists(path) else 0
    return {
        "counts": counts, "projects": projects, "validations": validations, "last_validation_ts": last_validation["ts"] if last_validation else None,
        "documents_by_kind": docs_by_kind, "events_by_day": list(reversed(events_by_day)),
        "storage": {"engine": "SQLite", "size_bytes": size, "volatile": os.path.abspath(path).startswith(os.path.abspath(tempfile.gettempdir())),
                    "note": "File nella cartella temporanea: su hosting serverless (es. Vercel) si azzera ai cold start. Per una memoria duratura serve un database esterno."},
        "registry": {"intact": chain.intact, "entries": chain.entries, "head_hash": chain.head_hash, "key_id": key["key_id"], "is_dev_key": key["is_dev_key"]},
        "hq_code_is_default": os.getenv("QUANTO_HQ_CODE", DEFAULT_CODE) == DEFAULT_CODE,
        "operations": operations_catalog(),
        "recent_events": events.list_events(limit=12),
    }


# ------------------------------------------------------------------ dossier
def projects_index() -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT project_id, COUNT(*) n, MIN(ts) first_ts, MAX(ts) last_ts, GROUP_CONCAT(DISTINCT bando_id) bandi "
            "FROM events WHERE project_id IS NOT NULL GROUP BY project_id ORDER BY last_ts DESC").fetchall()
    return [{"project_id": r["project_id"], "events": r["n"], "first_ts": r["first_ts"], "last_ts": r["last_ts"],
             "bandi": [b for b in (r["bandi"] or "").split(",") if b]} for r in rows]


def _run_summary(row) -> Dict[str, Any]:
    resp = json.loads(row["response_json"])
    return {"id": row["id"], "ts": row["ts"], "kind": row["kind"], "bando_id": row["bando_id"], "merkle_root": row["merkle_root"],
            "status": resp.get("status"), "conformity_score": resp.get("conformity_score"), "total_requested_eur": resp.get("total_requested_eur"),
            "total_approved_eur": resp.get("total_approved_eur"), "net_cost_to_entity_eur": resp.get("net_cost_to_entity_eur"),
            "items": len(resp.get("items", []) or resp.get("allocation_plan", []) or [])}


def project_dossier(project_id: str) -> Dict[str, Any]:
    with connect() as conn:
        runs = conn.execute("SELECT * FROM runs WHERE project_id=? ORDER BY id", (project_id,)).fetchall()
        docs = conn.execute("SELECT * FROM documents WHERE project_id=? ORDER BY id", (project_id,)).fetchall()
    att = Registry.lookup(project_id)
    return {
        "project_id": project_id,
        "timeline": list(reversed(events.list_events(project_id=project_id, limit=500))),
        "runs": [_run_summary(r) for r in runs],
        "documents": [{k: d[k] for k in ("id", "ts", "kind", "name", "sha256", "size_bytes", "bando_id")} for d in docs],
        "registration": ({"seq": att.seq, "registered_at": att.registered_at, "merkle_root": "0x" + att.merkle_root, "entry_hash": att.entry_hash,
                          "key_id": att.key_id} if att else None),
    }


def bando_dossier(bando_id: str) -> Optional[Dict[str, Any]]:
    detail = bandi.get_bando_detail(bando_id)
    if detail is None:
        return None
    with connect() as conn:
        projects = conn.execute("SELECT project_id, COUNT(*) n, MAX(ts) last_ts FROM runs WHERE bando_id=? AND project_id IS NOT NULL GROUP BY project_id ORDER BY last_ts DESC", (bando_id,)).fetchall()
    return {**detail, "timeline": list(reversed(events.list_events(bando_id=bando_id, limit=300))), "projects": [dict(p) for p in projects]}


def documents_index(kind: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
    with connect() as conn:
        if kind:
            rows = conn.execute("SELECT * FROM documents WHERE kind=? ORDER BY id DESC LIMIT ?", (kind, limit)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM documents ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["meta"] = json.loads(d["meta"]) if d.get("meta") else None
        out.append(d)
    return out


def get_run(run_id: int) -> Optional[Dict[str, Any]]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
    if row is None:
        return None
    return {"id": row["id"], "ts": row["ts"], "kind": row["kind"], "project_id": row["project_id"], "bando_id": row["bando_id"],
            "merkle_root": row["merkle_root"], "request": json.loads(row["request_json"]), "response": json.loads(row["response_json"])}


# ------------------------------------------------------------------ database (sola lettura)
def db_tables() -> List[Dict[str, Any]]:
    bandi.ensure_seeded()
    out = []
    with connect() as conn:
        for t in TABLES:
            cols = [r["name"] for r in conn.execute(f"PRAGMA table_info({t})").fetchall()]
            out.append({"name": t, "rows": _count(conn, t), "columns": cols})
    return out


def db_rows(table: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    if table not in TABLES:
        raise KeyError(table)
    limit = max(1, min(limit, 200))
    with connect() as conn:
        total = _count(conn, table)
        order = "seq" if table == "anchors" else "id" if table in ("events", "runs", "documents") else "rowid"
        rows = conn.execute(f"SELECT * FROM {table} ORDER BY {order} DESC LIMIT ? OFFSET ?", (limit, max(0, offset))).fetchall()
    heavy = HEAVY.get(table, ())
    out = []
    for r in rows:
        d = dict(r)
        for col in heavy:
            if col in d and d[col] is not None:
                text = str(d[col])
                d[col] = f"[{len(text)} caratteri] {text[:120]}…" if len(text) > 120 else text
        out.append(d)
    return {"table": table, "total": total, "limit": limit, "offset": offset, "rows": out}
