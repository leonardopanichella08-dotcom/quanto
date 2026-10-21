"""I token dello studio: saldo, consegna di un budget (1 token, 30 giorni), studio dei bandi (3 / 1 / 0), rimborsi, anticipo di cortesia, tetto mensile, esenzioni."""
import pytest
from fastapi.testclient import TestClient

from app.core import tokens, users
from main import app
from tests.conftest import manager_token, tamper_sql

client = TestClient(app)
PW = "Una-Password-Robusta-42"
RULES = {}


@pytest.fixture
def secured(monkeypatch):
    monkeypatch.setenv("QUANTO_AUTH_REQUIRED", "1")
    return monkeypatch


def studio(email="studio@example.test"):
    users.create_user(email, "Studio Rossi", PW, "USER", actor="test")
    r = client.post("/api/v2/auth/login", json={"email": email, "password": PW})
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    RULES["r"] = client.post("/api/v2/bandi/QUANTO-SANDBOX-60/select", headers=h).json()["grant_rules"]
    return h, r.json()["user"]["id"]


def body(project="PRJ-T1", extra=0):
    items = [{"item_id": "I-1", "category": "CONSULTING", "amount_eur": 1000, "description": "test", "source_c_ref": ""}]
    if extra:
        items.append({"item_id": "I-2", "category": "CONSULTING", "amount_eur": extra, "description": "altra", "source_c_ref": ""})
    return {"project_id": project, "grant_rules": RULES["r"], "cost_items": items}


def balance(h):
    return client.get("/api/v2/tokens", headers=h).json()["balance"]


def test_a_new_studio_starts_with_welcome_and_monthly_tokens(secured):
    h, _ = studio()
    o = client.get("/api/v2/tokens", headers=h).json()
    assert o["balance"] == 25 and o["included"] == 15 and o["extra"] == 10 and o["monthly"] == 15 and o["cap"] == 30 and o["payments_active"] is False
    costs = {c["op"]: c["cost"] for c in o["costs"]}
    assert costs["deliver"] == 1 and costs["study_new"] == 3 and costs["study_cached"] == 0 and costs["work"] == 0 and costs["allocate"] == 2.0
    assert [p["tokens"] for p in o["packs"]] == [10] and o["packs"][0]["price_eur"] == 25.0                  # 10 token in più costano 25 euro
    assert o["plan"]["monthly_eur"] == 209.0 and o["plan"]["yearly_eur"] == 1999.0 and o["plan"]["tokens_per_month"] == 15
    assert client.get("/api/v2/tokens").status_code == 401


def test_delivering_a_budget_costs_one_token_for_thirty_days_and_working_is_free(secured):
    h, _ = studio()
    b = body()
    for _ in range(5):
        assert client.post("/api/v2/budget/validate", json=b, headers=h).status_code == 200            # il lavoro quotidiano è libero
    assert balance(h) == 25
    bid = RULES["r"]["bando_id"]
    q = client.get("/api/v2/tokens/quote", params={"op": "deliver", "project_id": "PRJ-T1", "bando_id": bid}, headers=h).json()
    assert q["cost"] == 1 and q["covered"] is False
    assert client.post("/api/v2/budget/export/xlsx", json=b, headers=h).status_code == 200
    assert balance(h) == 24
    assert client.post("/api/v2/budget/export/pdf", json=b, headers=h).status_code == 200                  # stessa consegna: nessun altro token
    assert client.post("/api/v2/budget/export/pdf", json=body(extra=500), headers=h).status_code == 200    # modificato, ma nella stessa consegna
    assert balance(h) == 24
    q2 = client.get("/api/v2/tokens/quote", params={"op": "deliver", "project_id": "PRJ-T1", "bando_id": bid}, headers=h).json()
    assert q2["cost"] == 0 and q2["covered"] is True and "fino al" in q2["reason"]
    assert client.post("/api/v2/budget/export/pdf", json=body("PRJ-T2"), headers=h).status_code == 200     # un altro budget è un'altra consegna
    assert balance(h) == 23


def test_registering_a_delivered_budget_is_free_and_a_new_one_costs_a_token(secured):
    h, _ = studio("reg@example.test")
    b = body("PRJ-REG")
    root = client.post("/api/v2/budget/validate", json=b, headers=h).json()["merkle_root"]
    client.post("/api/v2/budget/export/pdf", json=b, headers=h)
    assert balance(h) == 24
    assert client.post("/api/v2/registry/register", json={"project_id": "PRJ-REG", "merkle_root": root}, headers=h).status_code == 201
    assert balance(h) == 24                                                                                 # la consegna c'era già
    root3 = client.post("/api/v2/budget/validate", json=body("PRJ-REG3"), headers=h).json()["merkle_root"]
    assert client.post("/api/v2/registry/register", json={"project_id": "PRJ-REG3", "merkle_root": root3}, headers=h).status_code == 201
    assert balance(h) == 23                                                                                 # registrare senza aver esportato: 1 token


def test_without_tokens_only_deliveries_stop_with_a_clear_402_after_the_courtesy_advance(secured):
    h, uid = studio("poveri@example.test")
    tamper_sql("INSERT INTO token_ledger (user_id, ts, kind, bucket, amount, op, ref, dedupe, actor, note) VALUES (%s, '2026-01-01T00:00:00Z', 'SPEND', 'EXTRA', -9, 'x', '', 'seed-x', 't', '')", (uid,))
    tamper_sql("INSERT INTO token_ledger (user_id, ts, kind, bucket, amount, op, ref, dedupe, actor, note) VALUES (%s, '2026-01-01T00:00:00Z', 'SPEND', 'INCLUDED', -15, 'x', '', 'seed-y', 't', '')", (uid,))
    assert balance(h) == 1
    assert client.post("/api/v2/budget/export/pdf", json=body("PRJ-A"), headers=h).status_code == 200      # l'ultimo token
    assert balance(h) == 0
    assert client.post("/api/v2/budget/export/pdf", json=body("PRJ-B"), headers=h).status_code == 200      # anticipo di cortesia (fino a -2)
    assert client.post("/api/v2/budget/export/pdf", json=body("PRJ-C"), headers=h).status_code == 200
    assert balance(h) == -2
    r = client.post("/api/v2/budget/export/pdf", json=body("PRJ-D"), headers=h)
    d = r.json()["detail"]
    assert r.status_code == 402 and d["code"] == "TOKENS_NEEDED" and d["needed"] == 1 and "resta libero" in d["message"]
    assert client.post("/api/v2/budget/validate", json=body("PRJ-D"), headers=h).status_code == 200          # controllare resta possibile
    assert client.post("/api/v2/budget/export/pdf", json=body("PRJ-A"), headers=h).status_code == 200      # una consegna già pagata resta valida


def test_monthly_tokens_roll_over_up_to_the_cap_and_welcome_tokens_never_expire(secured):
    h, uid = studio("vecchio@example.test")
    tamper_sql("UPDATE users SET created_at='2026-01-10T00:00:00Z' WHERE id=%s", (uid,))
    o = client.get("/api/v2/tokens", headers=h).json()
    assert o["included"] == 30 and o["extra"] == 10 and o["balance"] == 40                                   # molti mesi non usati: tetto di 30 più il benvenuto
    assert client.get("/api/v2/tokens", headers=h).json()["balance"] == 40                                   # gli accrediti non si ripetono


def test_manager_grants_tokens_and_a_topup_request_is_recorded(secured):
    h, uid = studio("ricarica@example.test")
    r = client.post("/api/v2/tokens/topup-request", json={"pack": "s", "quantity": 3, "note": "ci servono per marzo"}, headers=h)
    assert r.status_code == 201 and r.json()["requested"]["tokens"] == 30 and r.json()["requested"]["price_eur"] == 75.0 and "titolare" in r.json()["message"]
    assert client.post("/api/v2/tokens/topup-request", json={"pack": "zzz"}, headers=h).status_code == 422
    mh = {"X-HQ-Token": manager_token()}
    assert client.post(f"/api/v2/hq/users/{uid}/tokens", json={"tokens": 30, "note": "ricarica pacchetto M"}, headers=mh).status_code == 201
    assert balance(h) == 55
    assert client.post(f"/api/v2/hq/users/{uid}/tokens", json={"tokens": 0}, headers=mh).status_code == 422
    assert client.post(f"/api/v2/hq/users/{uid}/tokens", json={"tokens": 5}, headers=h).status_code in (401, 403)       # solo il titolare


def test_owner_and_internal_access_never_spend(secured, monkeypatch):
    monkeypatch.setenv("QUANTO_OWNER_EMAIL", "titolare@example.test")
    h, _ = studio("titolare@example.test")
    assert client.get("/api/v2/tokens", headers=h).json()["exempt"] is True
    assert client.post("/api/v2/budget/export/pdf", json=body("PRJ-OWN"), headers=h).status_code == 200
    q = client.get("/api/v2/tokens/quote", params={"op": "deliver", "project_id": "PRJ-OWN", "bando_id": ""}, headers=h).json()
    assert q["cost"] == 0
    assert tokens.exempt(None) is True


def test_studying_costs_by_how_new_the_bando_is_and_failures_are_refunded(secured, monkeypatch):
    h, uid = studio("studia@example.test")
    from app.core import pipeline
    from app.core.ingestion import Ingestion
    Ingestion.catalog("CAT-TOK-AAA111", "Bando di prova token", "Ente", None, None)
    q_new = client.get("/api/v2/tokens/quote", params={"op": "study", "bando_id": "CAT-TOK-AAA111"}, headers=h).json()
    assert q_new["cost"] == 3 and q_new["cached"] is False and q_new["op"] == "study_new"
    assert client.get("/api/v2/tokens/quote", params={"op": "study", "bando_id": "QUANTO-SANDBOX-60"}, headers=h).json()["cached"] is True      # già con regole: costa meno
    monkeypatch.setattr(pipeline, "run", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("rete assente")))
    with pytest.raises(RuntimeError):
        client.post("/api/v2/bandi/research/run", json={"bando_id": "CAT-TOK-AAA111"}, headers=h)
    assert balance(h) == 25                                                                                  # fallito: token restituiti
    monkeypatch.setattr(pipeline, "run", lambda *a, **k: {"status": "COMPLETA"})
    ok = client.post("/api/v2/bandi/research/run", json={"bando_id": "CAT-TOK-AAA111"}, headers=h)
    assert ok.status_code == 200
    assert balance(h) == 23                                                                                  # 3 token meno 1 di premio al catalogo
    assert client.post("/api/v2/bandi/research/run", json={"bando_id": "CAT-TOK-AAA111"}, headers=h).status_code == 200
    led = client.get("/api/v2/tokens", headers=h).json()["ledger"]
    assert any(x["kind"] == "REFUND" and "Premio" in x["note"] for x in led)


def test_a_failed_delivery_gives_the_token_back_and_does_not_count_as_delivered(secured, monkeypatch):
    h, _ = studio("fallita@example.test")
    from app.api.endpoints import budget as budget_api
    b = body("PRJ-FAIL")
    original = budget_api.build_pdf
    monkeypatch.setattr(budget_api, "build_pdf", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("PDF non generato")))
    with pytest.raises(RuntimeError):
        client.post("/api/v2/budget/export/pdf", json=b, headers=h)
    assert balance(h) == 25
    q = client.get("/api/v2/tokens/quote", params={"op": "deliver", "project_id": "PRJ-FAIL", "bando_id": RULES["r"]["bando_id"]}, headers=h).json()
    assert q["covered"] is False and q["cost"] == 1                                                          # non risulta consegnato
    monkeypatch.setattr(budget_api, "build_pdf", original)
    assert client.post("/api/v2/budget/export/pdf", json=b, headers=h).status_code == 200
    assert balance(h) == 24


def test_registering_twice_does_not_cost_a_second_token(secured):
    h, _ = studio("doppia@example.test")
    b = body("PRJ-DUP")
    root = client.post("/api/v2/budget/validate", json=b, headers=h).json()["merkle_root"]
    assert client.post("/api/v2/registry/register", json={"project_id": "PRJ-DUP", "merkle_root": root}, headers=h).status_code == 201
    assert balance(h) == 24
    assert client.post("/api/v2/registry/register", json={"project_id": "PRJ-DUP", "merkle_root": root}, headers=h).status_code == 409
    assert balance(h) == 24


# ------------------------------------------------------------------------------------------------ costo secondo i dati, pubblicazione, decimali
def test_allocation_cost_goes_from_two_to_four_point_eight_with_the_data_it_analyses():
    none = tokens.allocation_cost(0, [])
    assert none["cost"] == 2.0 and none["min"] == 2.0 and none["max"] == 4.8
    small = tokens.allocation_cost(12, [{"bando_id": "A", "rules": 7, "requirements": 0, "units": 7}])
    assert small["balance_tokens"] == 0.2 and small["bandi_tokens"] == 0.2 and small["cost"] == 2.4            # 2 + 0,2 + (0,1 + 0,07 = 0,17 → 0,2)
    big = tokens.allocation_cost(500, [{"bando_id": str(i), "rules": 20, "requirements": 800, "units": 180} for i in range(12)])
    assert big["balance_tokens"] == 1.4 and big["bandi_tokens"] == 1.4 and big["cost"] == 4.8                  # tetto: mai oltre 4,8
    mid = tokens.allocation_cost(40, [{"bando_id": "A", "rules": 10, "requirements": 100, "units": 30}, {"bando_id": "B", "rules": 5, "requirements": 0, "units": 5}])
    assert 2.0 < mid["cost"] < 4.8


def test_delivery_cost_grows_with_the_number_of_voci():
    assert tokens.delivery_cost(10) == 1.0 and tokens.delivery_cost(25) == 1.0 and tokens.delivery_cost(26) == 1.5 and tokens.delivery_cost(61) == 2.0 and tokens.delivery_cost(None) == 1.0


def _plan(h, n, confirm=False):
    exp = [{"item_id": f"E{i}", "category": "PERSONNEL", "amount_eur": 1000} for i in range(n)]
    return client.post("/api/v2/allocation/optimize", headers=h, json={"fiscal_year": 2027, "historical_expenses": exp, **({"confirm_tokens": True} if confirm else {}),
                                                                       "available_funding_lines": [{"fund_id": "F1", "allowed_categories": ["PERSONNEL"], "coverage_pct": 0.5}]})


def test_allocation_asks_confirmation_with_the_cost_then_is_free_for_thirty_days(secured):
    h, _ = studio("alloc@example.test")
    r = _plan(h, 12)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "TOKENS_CONFIRM" and r.json()["detail"]["cost"] == 2.2 and r.json()["detail"]["breakdown"]["balance_lines"] == 12
    assert balance(h) == 25                                                                                      # niente addebitato di nascosto
    assert _plan(h, 12, True).status_code == 200
    assert balance(h) == 22.8
    assert _plan(h, 12).status_code == 200 and balance(h) == 22.8                                                # stesso lavoro e anno: incluso per 30 giorni
    bigger = _plan(h, 60)
    assert bigger.status_code == 409 and bigger.json()["detail"]["due"] == 1.0 and bigger.json()["detail"]["paid"] == 2.2     # dati più grandi: si paga solo la differenza (3,2 - 2,2)
    assert _plan(h, 60, True).status_code == 200 and balance(h) == 21.8
    led = client.get("/api/v2/tokens", headers=h).json()["ledger"]
    assert any(x["op"] == "allocate" and x["amount"] == -2.2 for x in led)


def test_allocation_failure_gives_tokens_back(secured, monkeypatch):
    h, _ = studio("allocko@example.test")
    from app.core.allocation_engine import AllocationOptimizerEngine
    monkeypatch.setattr(AllocationOptimizerEngine, "optimize_annual_allocation", staticmethod(lambda r: (_ for _ in ()).throw(RuntimeError("nessuna soluzione"))))
    r = _plan(h, 1, True)
    assert r.status_code == 500 and balance(h) == 25
    monkeypatch.undo()


def test_a_big_budget_costs_one_and_a_half_and_growing_it_later_costs_only_the_difference(secured):
    h, _ = studio("grande@example.test")
    items = [{"item_id": f"I-{i}", "category": "CONSULTING", "amount_eur": 100, "description": "voce", "source_c_ref": ""} for i in range(30)]
    b = {"project_id": "PRJ-BIG", "grant_rules": RULES["r"], "cost_items": items}
    assert client.post("/api/v2/budget/export/pdf", json=b, headers=h).status_code == 200
    assert balance(h) == 23.5                                                                                    # 30 voci: 1,5 token
    assert client.post("/api/v2/budget/export/xlsx", json=b, headers=h).status_code == 200 and balance(h) == 23.5
    b["cost_items"] = items + [{"item_id": f"J-{i}", "category": "CONSULTING", "amount_eur": 100, "description": "altra", "source_c_ref": ""} for i in range(40)]
    assert client.post("/api/v2/budget/export/pdf", json=b, headers=h).status_code == 200
    assert balance(h) == 23.0                                                                                    # 70 voci: 2 in tutto, 0,5 in più


def test_publishing_for_everyone_gives_half_a_token_once_per_client_and_bando_and_private_stays_private(secured):
    h, uid = studio("pubblica@example.test")
    c = client.post("/api/v2/clients", json={"name": "Cliente A"}, headers=h).json()
    hc = {**h, "X-Client-Id": str(c["id"])}
    body_t = {"ateco_code": "62.01", "bando_id": "SMART-START-ITALIA", "shares": {"assets_pct": 0.5, "personnel_pct": 0.25, "consulting_pct": 0.25}, "outcome": "BOZZA"}
    r = client.post("/api/v2/templates", json=body_t, headers=hc)
    assert r.status_code == 201 and r.json()["shared"] is True and r.json()["bonus"]["granted"] == 0.5
    assert balance(h) == 25.5
    again = client.post("/api/v2/templates", json=body_t, headers=hc)
    assert again.json()["bonus"]["granted"] == 0 and "già" in again.json()["bonus"]["reason"] and balance(h) == 25.5     # una volta per cliente e bando
    c2 = client.post("/api/v2/clients", json={"name": "Cliente B"}, headers=h).json()
    hc2 = {**h, "X-Client-Id": str(c2["id"])}
    priv = client.post("/api/v2/templates", json={**body_t, "shared": False}, headers=hc2)
    assert priv.json()["shared"] is False and priv.json()["bonus"]["granted"] == 0 and balance(h) == 25.5
    coll = client.post("/api/v2/templates/recommend", json={"ateco_code": "62.01", "bando_id": "SMART-START-ITALIA", "engine": "COLLETTIVO"}, headers=h).json()
    assert coll["status"] == "NO_DATA"                                                                              # 2 pubblicati: sotto il minimo di 3; il privato non conta nel collettivo
    internal = client.post("/api/v2/templates/recommend", json={"ateco_code": "62.01", "bando_id": "SMART-START-ITALIA", "engine": "INTERNO"}, headers=h).json()
    assert internal["status"] == "OK" and internal["templates_used"] == 3                                  # l'interno li vede tutti e tre, anche il privato
    pub = client.patch(f"/api/v2/templates/{priv.json()['id']}", json={"shared": True}, headers=hc2)              # pubblicarlo dopo: il premio arriva (cliente diverso)
    assert pub.status_code == 200 and pub.json()["shared"] is True and pub.json()["bonus"]["granted"] == 0.5 and balance(h) == 26.0


def test_publish_bonus_is_capped_per_month(secured):
    h, uid = studio("tetto@example.test")
    got = 0.0
    for i in range(12):
        c = client.post("/api/v2/clients", json={"name": f"Cliente {i}"}, headers=h).json()
        r = client.post("/api/v2/templates", json={"ateco_code": "62.01", "bando_id": "SMART-START-ITALIA", "shares": {"assets_pct": 0.5, "personnel_pct": 0.5}}, headers={**h, "X-Client-Id": str(c["id"])})
        got += r.json()["bonus"]["granted"]
    assert got == 5.0 and balance(h) == 30.0                                                                        # 10 premi da 0,5
