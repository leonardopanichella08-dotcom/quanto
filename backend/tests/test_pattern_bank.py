"""Banca dati dei pattern e clustering k-means: nessun archetipo nel codice, tutto viene dai budget importati.

I budget di questi test sono generati qui con un seme fisso (tre gruppi sintetici ben separati) per verificare che l'algoritmo li
ritrovi: non sono dati del prodotto.
"""
import base64

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.core import pattern_bank
from main import app
from tests.conftest import manager_token

client = TestClient(app)
HEAD = "bando_category;source;year;score;personnel_pct;assets_pct;consulting_pct;overhead_pct;training_pct;communication_pct\n"


def synthetic_csv(category="TEST_CAT", per_group=8):
    rng = np.random.default_rng(7)
    centers = {"occ": [0.62, 0.12, 0.14, 0.06, 0.04, 0.02], "tec": [0.20, 0.58, 0.12, 0.05, 0.03, 0.02], "con": [0.25, 0.10, 0.50, 0.08, 0.04, 0.03]}
    lines = []
    for name, c in centers.items():
        for i in range(per_group):
            v = np.abs(np.array(c) + rng.normal(0, 0.012, 6))
            v = v / v.sum()
            lines.append(f"{category};Graduatoria {name} {i};2025;{70 + i};" + ";".join(f"{x * 100:.2f}".replace(".", ",") for x in v))
    return HEAD + "\n".join(lines) + "\n"


def hq():
    return {"Authorization": f"Bearer {manager_token()}"}


def upload(text, name="b.csv"):
    return client.post("/api/v2/pattern/import", json={"filename": name, "content_base64": base64.b64encode(text.encode()).decode()}, headers=hq())


def test_empty_bank_refuses_to_compare_and_says_so():
    r = client.post("/api/v2/pattern/match", json={"bando_category": "QUALUNQUE", "draft_budget": {"personnel_pct": 0.5, "assets_pct": 0.5}})
    assert r.status_code == 409 and "banca dati" in r.json()["detail"] and "importa" in r.json()["detail"]
    assert client.get("/api/v2/pattern/categories").json() == []


def test_kmeans_recovers_three_groups_deterministically():
    res = upload(synthetic_csv())
    assert res.status_code == 201 and res.json()["imported"] == 24
    info = res.json()["categories"]["TEST_CAT"]
    assert info["archetypes"] == 3 and "k-means k=3" in info["method"]
    labels = sorted(a for a in [x["label"] for x in _archetypes()])
    assert labels == ["TRAZIONE_CONSULENZIALE", "TRAZIONE_OCCUPAZIONALE", "TRAZIONE_TECNOLOGICA"]
    again = pattern_bank.refresh_archetypes("TEST_CAT")
    assert again["archetypes"] == 3 and sorted(x["label"] for x in _archetypes()) == labels               # stesso dataset, stessi archetipi


def _archetypes():
    from app.core.db import connect
    with connect() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM pattern_archetypes ORDER BY label").fetchall()]


def test_match_returns_closest_archetype_deviation_nearest_budgets_and_score_range():
    upload(synthetic_csv())
    draft = {"personnel_pct": 0.22, "assets_pct": 0.10, "consulting_pct": 0.50, "overhead_pct": 0.10, "training_pct": 0.04, "communication_pct": 0.04}
    r = client.post("/api/v2/pattern/match", json={"bando_category": "test_cat", "draft_budget": draft}).json()
    assert r["closest_archetype"] == "TRAZIONE_CONSULENZIALE" and r["similarity_score"] >= 0.95
    assert 5 <= len(r["nearest_budgets"]) <= 10 and all(b["source"].startswith("Graduatoria con") for b in r["nearest_budgets"][:5])
    assert r["archetype"]["members"] == 8 and r["archetype"]["score_min"] == 70.0 and r["archetype"]["score_max"] == 77.0
    assert r["data_points"] == 24 and set(r["deviations_pp"]) == set(pattern_bank.SHARES)
    assert abs(r["main_deviation"]["deviation_points"]) < 0.06                                            # è già vicino all'archetipo: frazione, come nello schema


def test_main_deviation_note_uses_the_bando_cap_from_published_rules():
    from app.core.ingestion import Ingestion
    Ingestion.catalog("B-CAP", "Bando con tetto", None, None, None)
    Ingestion.extract("B-CAP", source_text="Le consulenze non possono superare il 20% del totale del progetto.")
    upload(synthetic_csv())
    draft = {"personnel_pct": 0.30, "assets_pct": 0.12, "consulting_pct": 0.45, "overhead_pct": 0.05, "training_pct": 0.04, "communication_pct": 0.04}
    r = client.post("/api/v2/pattern/match", json={"bando_category": "TEST_CAT", "bando_id": "B-CAP", "draft_budget": draft}).json()
    assert r["main_deviation"]["category"] == "consulting_pct" and r["main_deviation"]["note"] == "Sopra il tetto di bando del 20%"


def test_few_budgets_give_a_single_declared_average_not_a_fake_clustering():
    upload(synthetic_csv(per_group=1))                                       # 3 budget: meno del minimo per fare cluster
    a = _archetypes()
    assert len(a) == 1 and "servono almeno" in a[0]["method"]


@pytest.mark.parametrize("row,fragment", [
    ("TEST_CAT;;2025;70;60;10;15;5;5;5", "fonte"),
    ("TEST_CAT;Fonte;2025;70;60;10;15;5;5;10", "sommano"),
    (";Fonte;2025;70;60;10;15;5;5;5", "categoria"),
    ("TEST_CAT;Fonte;2025;70;;;;;;", "mancano le quote"),
])
def test_incomplete_records_are_rejected_with_line_numbers_and_nothing_is_saved(row, fragment):
    res = upload(HEAD + row + "\n")
    assert res.status_code == 422 and fragment in str(res.json()["detail"]["errors"][0]["error"]).lower() + str(res.json()["detail"]["message"]).lower() or fragment in res.text
    assert res.json()["detail"]["errors"][0]["line"] == 2
    assert client.get("/api/v2/pattern/categories").json() == []


def test_amounts_are_converted_to_shares_and_import_needs_a_manager():
    csv_text = "bando_category;source;personnel_eur;assets_eur;consulting_eur;overhead_eur;training_eur;communication_eur\nX;Fonte;60000;10000;20000;5000;3000;2000\n"
    assert client.post("/api/v2/pattern/import", json={"filename": "a.csv", "content_base64": base64.b64encode(csv_text.encode()).decode()}).status_code == 401
    assert upload(csv_text).status_code == 201
    b = client.get("/api/v2/pattern/budgets", headers=hq()).json()[0]
    assert b["personnel_pct"] == 0.6 and b["assets_pct"] == 0.1
