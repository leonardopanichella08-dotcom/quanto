import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.models.schemas import CostItemInput, GrantRuleSet  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch, tmp_path):
    """Ogni test parte con database, chiavi e autenticazione isolati."""
    for var in ("QUANTO_SIGNING_KEY", "QUANTO_TRUSTED_PUBLIC_KEYS", "QUANTO_AUTH_REQUIRED", "QUANTO_OAUTH_CLIENTS",
                "QUANTO_JWT_SECRET", "QUANTO_HMAC_SECRET", "QUANTO_WEBHOOK_URLS", "QUANTO_WEBHOOK_SECRET"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("QUANTO_DB_PATH", str(tmp_path / "quanto.sqlite3"))
    monkeypatch.setenv("QUANTO_PII_KEY", "test-key")


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
