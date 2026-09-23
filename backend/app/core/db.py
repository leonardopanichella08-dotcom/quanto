"""Accesso a PostgreSQL, condiviso da tutti i moduli (registro, catalogo, eventi, tabelle ufficiali, documenti…).

Configurazione: ``QUANTO_DATABASE_URL`` (oppure ``DATABASE_URL`` / ``POSTGRES_URL``, come li impostano Neon, Supabase e
Vercel Postgres). Non esiste alcun database di ripiego: senza URL il server dice chiaramente che manca, invece di
scrivere su un file che si azzera a ogni riavvio.

Scelte per l'hosting serverless:
- pool di connessioni con controllo di validità a ogni prestito (le connessioni inattive vengono chiuse dal provider);
- niente prepared statement (``prepare_threshold=None``): funziona anche dietro PgBouncer in modalità transaction;
- ogni ``connect()`` è una transazione: commit all'uscita, rollback se c'è un'eccezione;
- le migrazioni (schema.py) si applicano una sola volta, sotto un lock consultivo, quindi più istanze che partono
  insieme non si pestano i piedi.
"""
from __future__ import annotations

import atexit
import base64
import json
import os
import threading
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional, Sequence

import psycopg
from psycopg_pool import ConnectionPool

from app.core.schema import MIGRATIONS

MIGRATION_LOCK_KEY = 7_419_001          # lock consultivo per le migrazioni
REGISTRY_LOCK_KEY = 7_419_002           # serializza l'aggiunta di voci alla catena del registro


class DatabaseNotConfigured(RuntimeError):
    """Manca l'URL di PostgreSQL."""


def database_url() -> str:
    url = os.getenv("QUANTO_DATABASE_URL") or os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or ""
    if not url:
        raise DatabaseNotConfigured(
            "Database non configurato: imposta QUANTO_DATABASE_URL (o DATABASE_URL) con l'indirizzo PostgreSQL, "
            "per esempio postgresql://utente:password@host/nome_db?sslmode=require")
    return url


class Row:
    """Riga di risultato: si legge per nome (r["col"]), per posizione (r[0]) e si converte con dict(r)."""
    __slots__ = ("_names", "_values")

    def __init__(self, names: Sequence[str], values: Sequence[Any]):
        self._names = tuple(names)
        self._values = tuple(values)

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self._values[key]
        try:
            return self._values[self._names.index(key)]
        except ValueError:
            raise KeyError(key) from None

    def get(self, key, default=None):
        return self._values[self._names.index(key)] if key in self._names else default

    def keys(self):
        return list(self._names)

    def values(self):
        return list(self._values)

    def items(self):
        return list(zip(self._names, self._values))

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def __contains__(self, key):
        return key in self._names

    def __repr__(self):
        return f"Row({dict(self.items())!r})"


def _row_factory(cursor):
    names = [c.name for c in (cursor.description or [])]
    return lambda values: Row(names, values)


def to_pg(sql: str) -> str:
    """Converte i segnaposto ``?`` in ``%s`` (fuori dai testi tra apici) e protegge i ``%`` letterali."""
    out: List[str] = []
    quoted = False
    for ch in sql:
        if ch == "'":
            quoted = not quoted
            out.append(ch)
        elif ch == "?" and not quoted:
            out.append("%s")
        elif ch == "%":
            out.append("%%")
        else:
            out.append(ch)
    return "".join(out)


class Conn:
    """Connessione con transazione aperta. ``execute`` accetta i segnaposto ``?``."""

    def __init__(self, raw: psycopg.Connection):
        self.raw = raw

    def execute(self, sql: str, params: Optional[Sequence[Any]] = None):
        if params is None:
            return self.raw.execute(sql)
        return self.raw.execute(to_pg(sql), tuple(params))

    def executemany(self, sql: str, seq: Sequence[Sequence[Any]]) -> None:
        with self.raw.cursor() as cur:
            cur.executemany(to_pg(sql), [tuple(p) for p in seq])

    def lock(self, key: int) -> None:
        """Lock consultivo valido fino alla fine della transazione."""
        self.raw.execute("SELECT pg_advisory_xact_lock(%s)", (key,))


_POOLS: Dict[str, ConnectionPool] = {}
_POOL_LOCK = threading.Lock()
_MIGRATED: set = set()
GENERATION = 0        # cresce quando i test svuotano il database: le cache «già inizializzato» si invalidano


def _pool() -> ConnectionPool:
    url = database_url()
    with _POOL_LOCK:
        pool = _POOLS.get(url)
        if pool is None:
            pool = ConnectionPool(url, min_size=0, max_size=int(os.getenv("QUANTO_DB_POOL_MAX", "8")), timeout=20, open=False,
                                  max_idle=60, check=ConnectionPool.check_connection,
                                  kwargs={"row_factory": _row_factory, "prepare_threshold": None, "connect_timeout": 10})
            pool.open()
            _POOLS[url] = pool
        return pool


def close_pools() -> None:
    with _POOL_LOCK:
        for p in _POOLS.values():
            p.close()
        _POOLS.clear()
        _MIGRATED.clear()


atexit.register(close_pools)


def migrate() -> List[int]:
    """Applica le migrazioni mancanti. Restituisce le versioni applicate ora."""
    url = database_url()
    applied: List[int] = []
    with psycopg.connect(url, autocommit=True, prepare_threshold=None, connect_timeout=10) as conn:
        conn.execute("SELECT pg_advisory_lock(%s)", (MIGRATION_LOCK_KEY,))
        try:
            conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())")
            done = {r[0] for r in conn.execute("SELECT version FROM schema_migrations").fetchall()}
            for version, name, sql in sorted(MIGRATIONS):
                if version in done:
                    continue
                with conn.transaction():
                    conn.execute(sql)
                    conn.execute("INSERT INTO schema_migrations (version, name) VALUES (%s,%s)", (version, name))
                applied.append(version)
        finally:
            conn.execute("SELECT pg_advisory_unlock(%s)", (MIGRATION_LOCK_KEY,))
    return applied


def ensure_schema() -> None:
    url = database_url()
    if url not in _MIGRATED:
        migrate()
        _MIGRATED.add(url)


@contextmanager
def connect() -> Iterator[Conn]:
    """Una transazione: commit all'uscita, rollback su eccezione."""
    ensure_schema()
    with _pool().connection() as raw:
        yield Conn(raw)


# ------------------------------------------------------------------ identità delle righe (per l'esplorazione dei dati)
def pk_columns(conn: Conn, table: str) -> List[str]:
    rows = conn.execute(
        "SELECT a.attname AS col FROM pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey) "
        "WHERE i.indrelid = ?::regclass AND i.indisprimary ORDER BY array_position(i.indkey::int2[], a.attnum)", (table,)).fetchall()
    return [r["col"] for r in rows]


def encode_rowid(pk: Sequence[str], row: Row) -> str:
    return base64.urlsafe_b64encode(json.dumps([row[c] for c in pk], default=str).encode()).decode().rstrip("=")


def decode_rowid(token: str) -> List[Any]:
    pad = "=" * (-len(token) % 4)
    values = json.loads(base64.urlsafe_b64decode(token + pad).decode())
    if not isinstance(values, list):
        raise ValueError("Identificativo di riga non valido")
    return values


def table_columns(conn: Conn, table: str) -> List[str]:
    return [r["column_name"] for r in conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = ? ORDER BY ordinal_position", (table,)).fetchall()]


def db_size_bytes(conn: Conn) -> int:
    return int(conn.execute("SELECT pg_database_size(current_database()) AS s").fetchone()["s"])
