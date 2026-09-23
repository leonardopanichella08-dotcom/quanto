"""Infrastruttura PostgreSQL: migrazioni, registro append-only a livello di database, concorrenza, identità delle righe."""
import threading

import psycopg
import pytest

from app.core import db
from app.core.registry import Registry
from app.core.schema import MIGRATIONS


def test_placeholders_are_translated_outside_quotes_and_percent_is_escaped():
    assert db.to_pg("SELECT * FROM t WHERE a=? AND b LIKE '100%?' AND c=?") == "SELECT * FROM t WHERE a=%s AND b LIKE '100%%?' AND c=%s"


@pytest.mark.no_fonte_b
def test_migrations_apply_once_and_are_idempotent():
    assert db.migrate() == [m[0] for m in MIGRATIONS]      # database appena ricreato: si applicano tutte, in ordine
    assert db.migrate() == []                              # la seconda volta non fa nulla
    with db.connect() as conn:
        assert conn.execute("SELECT MAX(version) v FROM schema_migrations").fetchone()["v"] == MIGRATIONS[-1][0]


def test_missing_database_url_is_a_clear_error(monkeypatch):
    monkeypatch.delenv("QUANTO_DATABASE_URL", raising=False)
    with pytest.raises(db.DatabaseNotConfigured, match="QUANTO_DATABASE_URL"):
        db.database_url()


def test_registry_is_append_only_in_the_database_itself():
    Registry.register("PRJ-DB-1", "0x" + "ab" * 32)
    with db.connect() as conn:
        with pytest.raises(psycopg.errors.RestrictViolation):
            conn.execute("UPDATE anchors SET merkle_root = ?", ("cd" * 32,))
    with db.connect() as conn:
        with pytest.raises(psycopg.errors.RestrictViolation):
            conn.execute("DELETE FROM anchors")
    with db.connect() as conn:
        with pytest.raises(psycopg.errors.RestrictViolation):
            conn.execute("TRUNCATE anchors")
    assert Registry.verify_chain().intact and Registry.verify_chain().entries == 1


def test_concurrent_registrations_keep_a_linear_chain():
    errors = []

    def go(i):
        try:
            Registry.register(f"PRJ-CONC-{i}", "0x" + f"{i + 1:02x}" * 32)
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    threads = [threading.Thread(target=go, args=(i,)) for i in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert not errors
    chain = Registry.verify_chain()
    assert chain.intact and chain.entries == 8
    assert [e.seq for e in Registry.entries()] == list(range(1, 9))


def test_row_identity_round_trips_and_a_row_can_be_deleted_by_it():
    from app.core import archive, bandi
    bandi.ensure_seeded()
    rows = archive_rows = None
    from app.core import hq
    data = hq.db_rows("rules", limit=3)
    rid = data["rows"][0]["_rowid"]
    assert isinstance(rid, str) and db.decode_rowid(rid)
    assert archive.db_delete_row("rules", rid) is True
    assert archive.db_delete_row("rules", rid) is False


def test_rollback_on_error_leaves_no_partial_writes():
    with pytest.raises(RuntimeError):
        with db.connect() as conn:
            conn.execute("INSERT INTO bando_tombstones (bando_id, ts) VALUES (?,?)", ("X", "2026-01-01"))
            raise RuntimeError("boom")
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) c FROM bando_tombstones").fetchone()["c"] == 0
