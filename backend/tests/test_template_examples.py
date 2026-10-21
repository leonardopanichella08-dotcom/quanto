"""Gli esempi del motore collettivo: 48 budget costruiti sulle regole dei bandi e verificati con esse; pesano la metà, non contano come ammessi, escono con i template reali."""
import pytest
from fastapi.testclient import TestClient

from app.core import template_examples as te, template_learning as tl
from main import app
from tests.conftest import manager_token

client = TestClient(app)
HQ = lambda: {"X-HQ-Token": manager_token()}  # noqa: E731


@pytest.fixture
def examples(monkeypatch):
    monkeypatch.setenv("QUANTO_SEED_TEMPLATES", "1")
    te._DONE["generation"] = None
    return te


def listing():
    return client.get("/api/v2/hq/template-examples", headers=HQ()).json()


def test_there_are_at_least_forty_examples_across_the_curated_bandi(examples):
    d = listing()
    assert d["count"] >= 40
    assert {t["bando_id"] for t in d["items"]} >= {"HORIZON-EUROPE-MGA", "FVG-VALIDAZIONE-TRL-2026", "SMART-START-ITALIA", "SIMEST-FONDO-394-PNRR"}
    assert len({t["ateco_division"] for t in d["items"]}) >= 8
    assert all(t["origin"] == "ESEMPIO" and t["verification"]["checks"] and t["verification"]["rule_version_hash"] for t in d["items"])
    assert all(abs(sum(t["shares"].values()) - 1) < 0.001 for t in d["items"])
    results = {t["verification"]["result"] for t in d["items"]}
    assert results == {"CONFORME", "RIDUZIONI", "NON_CONFORME"}                      # anche i casi che il motore taglierebbe o respingerebbe


def test_seeding_is_idempotent_and_deterministic(examples):
    first = listing()
    again = client.post("/api/v2/hq/template-examples", headers=HQ())
    assert again.status_code == 201 and again.json()["created"] == 0 and again.json()["refreshed"] == 0
    second = listing()
    assert [(t["id"], t["shares"]) for t in first["items"]] == [(t["id"], t["shares"]) for t in second["items"]]


def test_verification_follows_the_real_rules():
    caps = {"eligible_categories": ["CAPITAL_ASSETS"], "max_consulting_percentage": None}
    ok = te.verify_shares(caps, {"assets_pct": 1.0})
    assert ok["outcome"] == "CONFORME"
    bad = te.verify_shares(caps, {"assets_pct": 0.9, "personnel_pct": 0.1})
    assert bad["outcome"] == "NON_CONFORME" and "categorie non ammesse" in bad["checks"][0]["detail"]
    cut = te.verify_shares({"eligible_categories": ["CAPITAL_ASSETS", "CONSULTING"], "max_consulting_percentage": 0.05}, {"assets_pct": 0.9, "consulting_pct": 0.1})
    assert cut["outcome"] == "RIDUZIONI"
    flat = {"overhead_flat_rate_pct": 0.25}
    assert te.verify_shares(flat, {"personnel_pct": 0.8, "overhead_pct": 0.2})["outcome"] == "CONFORME"
    assert te.verify_shares(flat, {"personnel_pct": 0.7, "overhead_pct": 0.3})["outcome"] == "RIDUZIONI"
    pers = {"overhead_flat_rate_pct": 0.10, "overhead_flat_base": "PERSONNEL"}
    assert te.verify_shares(pers, {"personnel_pct": 0.5, "assets_pct": 0.45, "overhead_pct": 0.05})["outcome"] == "CONFORME"


def test_examples_give_a_cold_start_advice_but_never_count_as_wins_or_high_confidence(examples):
    rec = client.post("/api/v2/templates/recommend", json={"ateco_code": "62.01", "bando_id": "SMART-START-ITALIA"}).json()
    assert rec["status"] == "OK" and rec["example_templates"] >= 3 and rec["real_templates"] == 0
    assert rec["wins"] == 0 and rec["confidence"] == "BASSA" and rec["basis"] == "NICCHIA_E_BANDO"
    assert any("esempi costruiti sulle regole" in line for line in rec["explanation"])
    assert rec["outcomes"]["AMMESSO"] == 0


def test_examples_weigh_half_and_leave_when_real_templates_reach_the_threshold(examples):
    ex = {"origin": "ESEMPIO", "outcome": "AMMESSO"}
    real = {"origin": "REALE", "outcome": "AMMESSO"}
    assert tl._weight(ex) == tl._weight(real) / 2
    for i in range(tl.EXAMPLES_FADE):
        r = client.post("/api/v2/templates", json={"ateco_code": "62.01", "bando_id": "SMART-START-ITALIA", "shares": {"assets_pct": 0.5, "personnel_pct": 0.25, "consulting_pct": 0.25},
                                                   "outcome": "AMMESSO"})
        assert r.status_code == 201
    rec = client.post("/api/v2/templates/recommend", json={"ateco_code": "62.01", "bando_id": "SMART-START-ITALIA"}).json()
    assert rec["example_templates"] == 0 and rec["real_templates"] == tl.EXAMPLES_FADE and rec["wins"] == tl.EXAMPLES_FADE and rec["confidence"] == "ALTA"
    other = client.post("/api/v2/templates/recommend", json={"ateco_code": "26.20", "bando_id": "SMART-START-ITALIA"}).json()
    assert other["example_templates"] >= 3                                            # un'altra nicchia non ha ancora reali: gli esempi servono ancora


def test_examples_do_not_pollute_my_templates_the_internal_engine_or_the_feedback_loop(examples):
    assert client.get("/api/v2/templates").json() == []
    internal = client.post("/api/v2/templates/recommend", json={"ateco_code": "62.01", "bando_id": "SMART-START-ITALIA", "engine": "INTERNO"}).json()
    assert internal["status"] == "NO_DATA"
    learning = client.get("/api/v2/templates/learning").json()
    assert learning["templates_pool"] == 0 and learning["outcomes"]["AMMESSO"] == 0 and learning["examples"]["count"] >= 40 and learning["feedback"]["judged"] == 0
    niches = client.get("/api/v2/templates/niches").json()
    assert sum(n["examples"] for n in niches) >= 40 and all(n["templates"] == 0 and n["wins"] == 0 for n in niches)


def test_the_owner_can_remove_the_examples_and_they_do_not_come_back_alone(examples):
    assert listing()["count"] >= 40
    assert client.delete("/api/v2/hq/template-examples", headers=HQ()).json()["deleted"] >= 40
    te._DONE["generation"] = None
    client.post("/api/v2/templates/recommend", json={"ateco_code": "62.01", "bando_id": "SMART-START-ITALIA"})
    assert te.ensure() is None
    assert listing()["count"] == 0
    assert client.post("/api/v2/hq/template-examples", headers=HQ()).json()["created"] >= 40         # rimessi a mano


def test_a_changed_rule_remakes_only_the_examples_of_that_bando(examples):
    listing()
    from tests.conftest import tamper_sql
    tamper_sql("UPDATE budget_templates SET verification = replace(verification, 'rule_version_hash', 'rule_version_vecchio') WHERE bando_id='SIMEST-FONDO-394-PNRR'")
    out = client.post("/api/v2/hq/template-examples", headers=HQ()).json()
    assert out["created"] == 0 and out["refreshed"] == 9
