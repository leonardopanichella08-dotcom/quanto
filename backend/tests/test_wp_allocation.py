"""Ripartizione delle voci tra i pacchetti di lavoro (WP): vincoli rispettati, importi esatti in centesimi, e niente forzature quando non c'è soluzione."""
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core import wp_allocation
from app.models.wp import WPItem, WPRequest, WorkPackage
from main import app

client = TestClient(app)


def req(items, wps, split=False):
    return WPRequest(items=[WPItem(**i) for i in items], work_packages=[WorkPackage(**w) for w in wps], allow_split=split)


ITEMS = [
    {"item_id": "A", "category": "PERSONNEL", "amount_eur": 60000},
    {"item_id": "B", "category": "PERSONNEL", "amount_eur": 20000},
    {"item_id": "C", "category": "CAPITAL_ASSETS", "amount_eur": 15000},
    {"item_id": "D", "category": "CONSULTING", "amount_eur": 5000},
]
WPS = [{"wp_id": "WP1", "name": "Gestione", "target_share_pct": 0.5, "max_share_pct": 0.6}, {"wp_id": "WP2", "name": "Sviluppo", "target_share_pct": 0.3},
       {"wp_id": "WP3", "name": "Diffusione", "target_share_pct": 0.2}]


def cents_of(out, wp_id):
    return sum(round(p["amount_eur"] * 100) for a in out["assignments"] for p in a["parts"] if p["wp_id"] == wp_id)


def test_whole_items_get_as_close_as_possible_to_the_wanted_shares_and_every_euro_is_placed():
    out = wp_allocation.allocate(req(ITEMS, WPS))
    assert out["status"] == "OPTIMAL" and out["all_checks_ok"]
    assert sum(cents_of(out, w["wp_id"]) for w in WPS) == 10000000                        # tutto il budget ammesso, né un centesimo di più né di meno
    assert all(len(a["parts"]) == 1 for a in out["assignments"])                          # nessuna voce divisa
    deviation = sum(abs(w["deviation_pp"]) for w in out["work_packages"])
    assert round(deviation, 2) == 20.0                                                     # con voci intere 20 punti di scostamento è il minimo possibile (60/20/15/5)
    assert next(w for w in out["work_packages"] if w["wp_id"] == "WP1")["share_pct"] <= 60


def test_splitting_one_item_reaches_the_wanted_shares_exactly():
    out = wp_allocation.allocate(req(ITEMS, WPS, split=True))
    assert out["status"] == "OPTIMAL"
    assert [w["deviation_pp"] for w in out["work_packages"]] == [0.0, 0.0, 0.0]
    assert sum(1 for a in out["assignments"] if len(a["parts"]) > 1) == 1                  # una sola voce divisa, e basta
    assert any("divisa" in n for n in out["notes"])


def test_categories_and_in_wp_caps_are_respected():
    wps = [{"wp_id": "GEST", "allowed_categories": ["PERSONNEL", "OVERHEAD"], "max_share_pct": 0.7},
           {"wp_id": "RS", "category_max_share": {"CONSULTING": 0.3}}]
    items = ITEMS + [{"item_id": "E", "category": "CONSULTING", "amount_eur": 8000}]
    out = wp_allocation.allocate(req(items, wps))
    assert out["status"] == "OPTIMAL" and out["all_checks_ok"]
    by = {a["item_id"]: a["parts"][0]["wp_id"] for a in out["assignments"]}
    assert by["C"] == "RS" and by["D"] == "RS" and by["E"] == "RS"                          # beni e consulenze non possono stare in GEST
    rs = next(w for w in out["work_packages"] if w["wp_id"] == "RS")
    assert rs["by_category"]["CONSULTING"]["pct_of_wp"] <= 30.0 + 1e-9, rs                  # tetto delle consulenze dentro il WP (13.000 su 48.000 = 27,08%)
    assert by["A"] == "GEST" and by["B"] == "RS"                                              # GEST non può contenere A e B insieme (74% > 70%)


def test_an_item_pinned_by_the_user_stays_where_it_was_put():
    items = [dict(i) for i in ITEMS]
    items[3]["pinned_wp"] = "WP3"
    out = wp_allocation.allocate(req(items, WPS))
    assert next(a for a in out["assignments"] if a["item_id"] == "D")["parts"] == [{"wp_id": "WP3", "amount_eur": 5000.0, "share": 1.0}]
    assert next(a for a in out["assignments"] if a["item_id"] == "D")["pinned"] is True


def test_without_wanted_shares_wps_fill_in_the_order_given_within_their_caps():
    wps = [{"wp_id": "WP1", "max_share_pct": 0.65}, {"wp_id": "WP2"}]
    out = wp_allocation.allocate(req(ITEMS, wps))
    assert out["status"] == "OPTIMAL"
    assert next(w for w in out["work_packages"] if w["wp_id"] == "WP1")["total_eur"] == 65000.0      # il più possibile in WP1 senza superare il 65% (voce da 60.000 + voce da 5.000)
    assert any("nell'ordine indicato" in n for n in out["notes"])


def test_no_solution_is_reported_with_the_reason_and_nothing_is_forced():
    only_staff = [{"wp_id": "WP1", "allowed_categories": ["PERSONNEL"]}]
    out = wp_allocation.allocate(req(ITEMS, only_staff))
    assert out["status"] == "INFEASIBLE" and "assignments" not in out
    assert any("beni strumentali" in r and "nessun WP" in r for r in out["reasons"])

    too_small = [{"wp_id": "WP1", "max_share_pct": 0.3}, {"wp_id": "WP2", "max_share_pct": 0.3}]
    out = wp_allocation.allocate(req(ITEMS, too_small))
    assert out["status"] == "INFEASIBLE" and any("60.0%" in r for r in out["reasons"])


def test_the_solver_explains_which_items_do_not_fit_when_caps_clash():
    # quote massime del 70% ciascuno bastano in teoria, ma la voce da 60.000 € in WP1 + il tetto delle consulenze dentro WP2 lasciano fuori qualcosa
    wps = [{"wp_id": "WP1", "max_share_pct": 0.5}, {"wp_id": "WP2", "max_share_pct": 0.5, "category_max_share": {"PERSONNEL": 0.0}}]
    out = wp_allocation.allocate(req(ITEMS, wps))
    assert out["status"] == "INFEASIBLE"
    assert out["unplaced"] and out["unplaced"][0]["unplaced_eur"] > 0
    assert out["message"].startswith("I vincoli dei WP")


def test_cents_always_add_up_even_when_items_are_split():
    items = [{"item_id": f"V{i}", "category": "OVERHEAD", "amount_eur": 100.01 + i * 0.07} for i in range(9)]
    wps = [{"wp_id": "A", "target_share_pct": 1 / 3}, {"wp_id": "B", "target_share_pct": 1 / 3}, {"wp_id": "C", "target_share_pct": 1 / 3}]
    out = wp_allocation.allocate(req(items, wps, split=True))
    assert out["status"] == "OPTIMAL" and out["all_checks_ok"]
    for it in items:
        parts = next(a for a in out["assignments"] if a["item_id"] == it["item_id"])["parts"]
        assert sum(Decimal(str(p["amount_eur"])) for p in parts) == Decimal(str(round(it["amount_eur"], 2)))      # nessun centesimo perso o creato


def test_inconsistent_requests_are_rejected_before_any_calculation():
    with pytest.raises(ValidationError):
        req(ITEMS, [{"wp_id": "A", "min_share_pct": 0.6, "max_share_pct": 0.4}])
    with pytest.raises(ValidationError):
        req(ITEMS, [{"wp_id": "A", "target_share_pct": 0.9, "max_share_pct": 0.5}])
    with pytest.raises(ValidationError):
        req(ITEMS, [{"wp_id": "A"}, {"wp_id": "A"}])
    with pytest.raises(ValidationError):
        req([{**ITEMS[0], "pinned_wp": "ZZ"}], [{"wp_id": "A"}])
    with pytest.raises(ValidationError):
        req([ITEMS[0], ITEMS[0]], [{"wp_id": "A"}])


def test_endpoint_returns_the_plan_and_records_the_operation():
    body = {"project_id": "PRJ-WP", "items": ITEMS, "work_packages": WPS, "allow_split": True}
    r = client.post("/api/v2/budget/wp-plan", json=body)
    assert r.status_code == 200 and r.json()["status"] == "OPTIMAL" and r.json()["project_id"] == "PRJ-WP"
    assert client.post("/api/v2/budget/wp-plan", json={**body, "work_packages": []}).status_code == 422
    from app.core import events
    assert any("Ripartizione in 3 WP" in e["summary"] for e in events.list_events(limit=20))
