"""Livelli CCNL mancanti: la bozza di completamento nasce solo se i livelli pubblicati sono tutti uguali, e conta solo dopo la pubblicazione di un manager."""
from datetime import date

from fastapi.testclient import TestClient

from app.core import fonte_b, fonte_b_admin as admin
from main import app
from tests.conftest import manager_token

client = TestClient(app)


def hq():
    return {"X-HQ-Token": manager_token()}


def publish(code, csv_text, version="1", valid_from=date(2020, 1, 1)):
    d = admin.create_draft("CCNL", code, f"CCNL {code}", version, valid_from, None, "Contratto di prova", "https://fonte.example/c", None, "t.csv", csv_text.encode(), "test")
    return admin.publish(d["id"], "test", attest_official=True)


def test_completion_is_possible_only_when_all_published_levels_are_identical():
    publish("SOLO34", "level;standard_hours;social_charges_pct;tfr_pct\n3;1700;30%;8,33%\n4;1700;30%;8,33%\n")
    h = hq()
    ok = client.get("/api/v2/fonte-b/ccnl/SOLO34/completion", headers=h).json()
    assert ok["possible"] and ok["levels"] == ["3", "4"] and ok["common"]["standard_hours"] == 1700
    # TERZO_SETTORE (fixture) ha oneri diversi tra i livelli: nulla si deduce
    ts = client.get("/api/v2/fonte-b/ccnl/TERZO_SETTORE/completion", headers=h).json()
    assert ts["possible"] is False and "diversi" in ts["reason"]
    assert client.post("/api/v2/fonte-b/ccnl/TERZO_SETTORE/complete-levels", json={"levels": ["9"]}, headers=h).status_code == 422
    nothing = client.get("/api/v2/fonte-b/ccnl/NON_ESISTE/completion", headers=h).json()
    assert nothing["possible"] is False and "nessuna tabella" in nothing["reason"]
    assert client.get("/api/v2/fonte-b/ccnl/SOLO34/completion").status_code == 401


def test_draft_copies_the_common_parameters_and_counts_only_after_publication():
    publish("SOLO34", "level;standard_hours;social_charges_pct;tfr_pct\n3;1700;30%;8,33%\n4;1700;30%;8,33%\n")
    h = hq()
    assert fonte_b.load().ccnl("SOLO34", "5") is None
    res = client.post("/api/v2/fonte-b/ccnl/SOLO34/complete-levels", json={"levels": ["5", "Quadro"]}, headers=h)
    assert res.status_code == 201
    d = res.json()
    assert d["status"] == "DRAFT" and d["rows"] == 4 and d["official"] is False and "livelli-" in d["version"]
    assert fonte_b.load().ccnl("SOLO34", "5") is None                                   # la bozza non entra nei calcoli
    detail = client.get(f"/api/v2/fonte-b/datasets/{d['id']}", headers=h).json()
    by = {r["level"]: r for r in detail["data"]}
    assert set(by) == {"3", "4", "5", "Quadro"} and by["5"]["standard_hours"] == 1700 and float(by["Quadro"]["social_charges_pct"]) == 0.30
    assert client.post(f"/api/v2/fonte-b/datasets/{d['id']}/publish", json={"attest_official": False}, headers=h).status_code == 409
    pub = client.post(f"/api/v2/fonte-b/datasets/{d['id']}/publish", json={"attest_official": True}, headers=h)
    assert pub.status_code == 200 and pub.json()["official"] is True
    p5 = fonte_b.load().ccnl("SOLO34", "5")
    assert p5 is not None and p5.standard_hours == 1700
    assert "Quadro" in fonte_b.load().ccnl_codes()["SOLO34"]


def test_existing_levels_and_bad_names_are_refused():
    publish("SOLO34", "level;standard_hours;social_charges_pct;tfr_pct\n3;1700;30%;8,33%\n")
    h = hq()
    assert client.post("/api/v2/fonte-b/ccnl/SOLO34/complete-levels", json={"levels": ["3"]}, headers=h).status_code == 422
    assert client.post("/api/v2/fonte-b/ccnl/SOLO34/complete-levels", json={"levels": ["<x>"]}, headers=h).status_code == 422
    assert client.post("/api/v2/fonte-b/ccnl/SOLO34/complete-levels", json={"levels": []}, headers=h).status_code == 422


def test_fixture_commercio_has_every_level():
    lv = fonte_b.load().ccnl_codes()["COMMERCIO"]
    assert set(lv) == {"Quadro", "1", "2", "3", "4", "5", "6", "7"}
