"""Accesso SQLite condiviso da registro di asseverazione e catalogo regole (ingestion).

Percorso: ``QUANTO_DB_PATH`` (default: cartella temporanea). Su un runtime serverless (Vercel) il
filesystem è volatile: per la produzione va montato un volume persistente o sostituito questo modulo con
un adattatore PostgreSQL (le query sono poche e isolate in ``registry.py`` / ``ingestion.py``).
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
import threading
from contextlib import contextmanager
from typing import Iterator

LOCK = threading.RLock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS anchors (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    project_key TEXT NOT NULL UNIQUE,
    merkle_root TEXT NOT NULL,
    registered_at TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    entry_hash TEXT NOT NULL,
    key_id TEXT NOT NULL,
    public_key TEXT NOT NULL,
    signature TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS bandi (
    bando_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    issuer TEXT,
    deadline TEXT,
    source_url TEXT,
    catalog_status TEXT NOT NULL DEFAULT 'CATALOGED',
    extraction_status TEXT NOT NULL DEFAULT 'NOT_STARTED',
    requested_by_clients INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS rules (
    bando_id TEXT NOT NULL,
    rule_key TEXT NOT NULL,
    value TEXT,
    origin TEXT NOT NULL,              -- STRUCTURED_PARSING | MULTI_PASS_AGREEMENT | HUMAN_REVIEW
    status TEXT NOT NULL,              -- PUBLISHED | PENDING_REVIEW
    passes TEXT,                       -- JSON: valori dei passaggi indipendenti
    source_ref TEXT,
    PRIMARY KEY (bando_id, rule_key)
);
"""


def db_path() -> str:
    return os.getenv("QUANTO_DB_PATH") or os.path.join(tempfile.gettempdir(), "quanto.sqlite3")


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Connessione con transazione immediata (serializza le scritture della catena di hash)."""
    with LOCK:
        conn = sqlite3.connect(db_path(), isolation_level=None, timeout=15)
        conn.row_factory = sqlite3.Row
        try:
            conn.executescript(SCHEMA)
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
        finally:
            conn.close()
