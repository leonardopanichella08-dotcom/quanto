import os
import pathlib
import sys

import psycopg
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.models.schemas import CostItemInput, GrantRuleSet  # noqa: E402


@pytest.fixture(scope="session")
def pg_url(tmp_path_factory):
    """PostgreSQL vero per i test: quello di ``QUANTO_TEST_DATABASE_URL`` (CI) oppure uno incorporato in locale."""
    url = os.getenv("QUANTO_TEST_DATABASE_URL")
    if url:
        yield url
        return
    try:
        import pixeltable_pgserver as pgserver
    except ImportError:  # pragma: no cover
        pytest.skip("Serve PostgreSQL: imposta QUANTO_TEST_DATABASE_URL oppure installa requirements-dev.txt (pixeltable-pgserver)")
    server = pgserver.get_server(tmp_path_factory.mktemp("pgdata"), cleanup_mode="delete")
    yield server.get_uri()
    server.cleanup()


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch, pg_url):
    """Ogni test parte con database vuoto (schema ricreato da zero), chiavi e autenticazione isolati."""
    for var in ("QUANTO_SIGNING_KEY", "QUANTO_TRUSTED_PUBLIC_KEYS", "QUANTO_AUTH_REQUIRED", "QUANTO_OAUTH_CLIENTS",
                "QUANTO_JWT_SECRET", "QUANTO_HMAC_SECRET", "QUANTO_WEBHOOK_URLS", "QUANTO_WEBHOOK_SECRET",
                "DATABASE_URL", "POSTGRES_URL"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("QUANTO_DATABASE_URL", pg_url)
    monkeypatch.setenv("QUANTO_PII_KEY", "test-key")
    reset_database(pg_url)
    yield


def reset_database(url: str) -> None:
    """Svuota il database e azzera le cache «già inizializzato»: ogni test vede uno schema nuovo."""
    from app.core import db
    db.close_pools()
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute("DROP SCHEMA IF EXISTS public CASCADE")
        conn.execute("CREATE SCHEMA public")
    db.GENERATION += 1


def tamper_sql(sql: str, params=()) -> None:
    """Modifica diretta del database, come farebbe un attaccante con accesso all'archivio (aggira i trigger)."""
    with psycopg.connect(os.environ["QUANTO_DATABASE_URL"], autocommit=True) as conn:
        conn.execute("SET session_replication_role = replica")
        conn.execute(sql, params)


@pytest.fixture
def rules() -> GrantRuleSet:
    return GrantRuleSet(bando_id="TRANSIZIONE-5.0-2026", bando_name="Piano Transizione 5.0",
                        max_hourly_rate_personnel=35.0, max_consulting_percentage=0.20,
                        max_overhead_percentage=0.07, rule_version_hash="a8f3b129c9e840134012480a2")


def personnel(item_id="LINE-001", ral=38000.0, fte=0.5, months=12, ccnl="TERZO_SETTORE", level="3", **kw) -> CostItemInput:
    return CostItemInput(item_id=item_id, description="Ruolo", category="PERSONNEL", source_c_ref="DOC-PAYROLL-2026-08",
                         ccnl_code=ccnl, employee_level=level, ral_eur=ral, fte_allocation=fte, duration_months=months, **kw)


def other(item_id, category, amount, ref="DOC-1") -> CostItemInput:
    return CostItemInput(item_id=item_id, description=category, category=category, source_c_ref=ref, amount_eur=amount)


@pytest.fixture
def seed_items():
    return [
        personnel("LINE-001"),
        personnel("LINE-002", ral=58000.0, fte=0.8, ccnl="METALMECCANICA", level="5"),
        other("LINE-003", "CONSULTING", 30000.0),
    ]
