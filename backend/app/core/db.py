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
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    op TEXT NOT NULL,
    status TEXT NOT NULL,
    actor TEXT NOT NULL,
    project_id TEXT,
    bando_id TEXT,
    duration_ms REAL,
    summary TEXT NOT NULL,
    details TEXT,
    run_id INTEGER
);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events (id DESC);
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    kind TEXT NOT NULL,                -- VALIDATE | ALLOCATION
    project_id TEXT,
    bando_id TEXT,
    merkle_root TEXT,
    request_json TEXT NOT NULL,
    response_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    kind TEXT NOT NULL,                -- BANDO_TEXT | BANDO_PDF | EXPORT_XLSX | EXPORT_PDF | IMPORT_XLSX | ATTESTATION
    name TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    bando_id TEXT,
    project_id TEXT,
    meta TEXT
);
CREATE TABLE IF NOT EXISTS bando_meta (
    bando_id TEXT PRIMARY KEY,
    meta TEXT NOT NULL                 -- JSON: stato, riferimenti normativi, fonti, beneficio, note
);
CREATE TABLE IF NOT EXISTS requirements (
    bando_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    topic TEXT NOT NULL,
    kind TEXT NOT NULL,                -- OBBLIGO | DIVIETO | LIMITE | INFO | DA_REVISIONARE
    text TEXT NOT NULL,
    criteria TEXT NOT NULL,            -- JSON: numeri dei criteri collegati
    source_ref TEXT,
    origin TEXT NOT NULL,              -- CURATED_SOURCE | STRUCTURED_PARSING
    PRIMARY KEY (bando_id, seq)
);
CREATE TABLE IF NOT EXISTS bando_sources (
    bando_id TEXT NOT NULL,
    ts TEXT NOT NULL,
    name TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    text TEXT NOT NULL,
    PRIMARY KEY (bando_id, sha256)
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


# colonne aggiunte dopo la prima versione (le tabelle esistenti vengono estese senza perdere dati)
MIGRATIONS = {
    "bando_sources": [("url", "TEXT"), ("tier", "TEXT"), ("content_type", "TEXT"), ("pages", "INTEGER"), ("origin", "TEXT")],
}


def _migrate(conn: sqlite3.Connection) -> None:
    for table, cols in MIGRATIONS.items():
        have = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        for name, typ in cols:
            if name not in have:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {typ}")


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Connessione con transazione immediata (serializza le scritture della catena di hash)."""
    with LOCK:
        conn = sqlite3.connect(db_path(), isolation_level=None, timeout=15)
        conn.row_factory = sqlite3.Row
        try:
            conn.executescript(SCHEMA)
            _migrate(conn)
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
        finally:
            conn.close()
