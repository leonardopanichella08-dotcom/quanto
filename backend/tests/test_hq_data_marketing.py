"""Datacenter, chatbot interno e Marketing del Quartier Generale."""
import pytest
from fastapi.testclient import TestClient

from app.core import datacenter, hq_assistant, llm, marketing, users
from main import app
from tests.conftest import manager_token

client = TestClient(app)
PW = "Una-Password-Robusta-42"


@pytest.fixture
def secured(monkeypatch):
    monkeypatch.setenv("QUANTO_AUTH_REQUIRED", "1")
    monkeypatch.setattr(llm, "get_client", lambda: None)                       # nessuna chiamata esterna nei test
    return monkeypatch


def hq():
    return {"Authorization": f"Bearer {manager_token()}"}


# ------------------------------------------------------------------------------------------------ datacenter
def test_il_catalogo_dei_dati_non_espone_mai_password_token_o_testi_integrali(secured):
    users.create_user("anna@studio.test", "Anna", PW, "USER", actor="test")
    cat = {d["id"]: d for d in client.get("/api/v2/hq/datacenter", headers=hq()).json()}
    assert "users" in cat and "site_events" in cat and "li_posts" in cat
    cols = {c["name"] for c in cat["users"]["columns"]}
    assert "email" in cols and "role" in cols
    assert not cols & {"password_hash", "token_version"}
    assert "access_token_enc" not in {c["name"] for c in cat.get("li_accounts", {"columns": []})["columns"]}
    assert cat["users"]["rows"] >= 2


def test_una_ricerca_su_una_colonna_nascosta_o_un_insieme_sconosciuto_viene_rifiutata(secured):
    bad = client.post("/api/v2/hq/datacenter/query", json={"dataset": "users", "columns": ["password_hash"]}, headers=hq())
    assert bad.status_code == 422 and "Colonna non disponibile" in bad.json()["detail"]
    assert client.post("/api/v2/hq/datacenter/query", json={"dataset": "schema_migrations"}, headers=hq()).status_code == 422
    inj = client.post("/api/v2/hq/datacenter/query", json={"dataset": "users", "group_by": 'role"; DROP TABLE users; --'}, headers=hq())
    assert inj.status_code == 422


def test_raggruppare_contare_e_scaricare_in_csv(secured):
    users.create_user("a1@studio.test", "A", PW, "USER", actor="test")
    users.create_user("a2@studio.test", "B", PW, "USER", actor="test")
    q = {"dataset": "users", "group_by": "role", "measure": "count"}
    res = client.post("/api/v2/hq/datacenter/query", json=q, headers=hq()).json()
    by = {r["gruppo"]: r["valore"] for r in res["rows"]}
    assert by["USER"] == 2 and by["MANAGER"] == 1 and res["chart"] == "bar"
    per_day = client.post("/api/v2/hq/datacenter/query", json={"dataset": "events", "group_by": "ts", "bucket": "day", "measure": "count",
                                                               "filters": [{"column": "ts", "op": "since_days", "value": 7}]}, headers=hq()).json()
    assert per_day["chart"] == "line" and per_day["rows"]
    csv = client.post("/api/v2/hq/datacenter/query.csv", json=q, headers=hq())
    assert csv.status_code == 200 and "gruppo;valore" in csv.text


def test_senza_titolare_il_datacenter_e_il_chatbot_sono_chiusi(secured):
    assert client.get("/api/v2/hq/datacenter").status_code == 401
    assert client.post("/api/v2/hq/ask", json={"question": "quanti utenti?"}).status_code == 401


# ------------------------------------------------------------------------------------------------ chatbot
def test_il_chatbot_senza_chiave_risponde_con_le_parole_chiave_e_i_numeri_veri(secured):
    users.create_user("b1@studio.test", "B", PW, "USER", actor="test")
    out = client.post("/api/v2/hq/ask", json={"question": "Quanti utenti ci sono per livello?"}, headers=hq()).json()
    assert out["engine"] == "parole chiave" and out["result"]["dataset"] == "users"
    assert "Utenti per livello" in out["answer"] and "2 in tutto" in out["answer"]
    visite = client.post("/api/v2/hq/ask", json={"question": "visite al sito negli ultimi 14 giorni"}, headers=hq()).json()
    assert visite["plan"]["filters"][0] == {"column": "ts", "op": "since_days", "value": 14}


def test_il_chatbot_dice_quando_non_capisce_invece_di_inventare(secured):
    out = client.post("/api/v2/hq/ask", json={"question": "che tempo fa a Roma?"}, headers=hq()).json()
    assert out["result"] is None and "Non ho capito" in out["answer"]


def test_con_claude_la_ricerca_passa_comunque_dai_controlli(secured):
    class Fake:
        def __init__(self, plan): self.plan = plan
        def complete_json(self, system, user): return self.plan
    users.create_user("c1@studio.test", "C", PW, "USER", actor="test")
    secured.setattr(llm, "get_client", lambda: Fake('{"dataset":"users","group_by":"role","measure":"count","title":"Utenti per ruolo"}'))
    ok = hq_assistant.ask("dimmi gli utenti per ruolo")
    assert ok["engine"] == "Claude" and ok["result"]["rows"]
    secured.setattr(llm, "get_client", lambda: Fake('{"dataset":"users","columns":["password_hash"]}'))
    assert hq_assistant.ask("password")["result"] is None                         # il modello non apre colonne nascoste
    secured.setattr(llm, "get_client", lambda: Fake('{"unsupported":"non ho dati meteo"}'))
    assert "non ho dati meteo" in hq_assistant.ask("meteo")["answer"]


# ------------------------------------------------------------------------------------------------ marketing
def test_un_post_passa_da_bozza_ad_approvato_e_modificarlo_lo_rimanda_all_approvazione(secured):
    acc = client.get("/api/v2/marketing/accounts", headers=hq()).json()
    assert [a["kind"] for a in acc] == ["profile", "page"]
    p = client.post("/api/v2/marketing/posts", json={"text": "Un bando si legge, non si indovina. #finanzaagevolata", "account_id": acc[0]["id"]}, headers=hq()).json()
    assert p["status"] == "BOZZA"
    assert client.post(f"/api/v2/marketing/posts/{p['id']}/publish", headers=hq()).status_code == 422          # non approvato
    assert client.post(f"/api/v2/marketing/posts/{p['id']}/submit", headers=hq()).json()["status"] == "DA_APPROVARE"
    ok = client.post(f"/api/v2/marketing/posts/{p['id']}/approve", headers=hq()).json()
    assert ok["status"] == "APPROVATO" and ok["approved_by"] and ok["approved_at"]
    edited = client.put(f"/api/v2/marketing/posts/{p['id']}", json={"text": "Testo cambiato", "account_id": acc[0]["id"]}, headers=hq()).json()
    assert edited["status"] == "BOZZA" and edited["approved_by"] is None


def test_il_database_rifiuta_un_post_pubblicato_senza_approvazione(secured):
    import psycopg
    from app.core.db import connect
    marketing.accounts()
    with pytest.raises(psycopg.errors.CheckViolation):
        with connect() as conn:
            conn.execute("INSERT INTO li_posts (text, status, created_by, created_at, updated_at) VALUES ('x','PUBBLICATO','test','2026-01-01','2026-01-01')")


def test_pubblicare_senza_linkedin_collegato_lascia_il_post_in_errore_con_il_motivo(secured):
    acc = marketing.accounts()[0]
    p = marketing.save_post({"text": "Prova", "account_id": acc["id"]}, "test")
    marketing.set_status(p["id"], "approve", "titolare")
    r = client.post(f"/api/v2/marketing/posts/{p['id']}/publish", headers=hq())
    assert r.status_code == 422 and "permesso" in r.json()["detail"]
    assert [x for x in marketing.list_posts() if x["id"] == p["id"]][0]["status"] == "ERRORE"


def test_pubblicazione_su_linkedin_con_risposta_simulata(secured, monkeypatch):
    monkeypatch.setenv("QUANTO_FILE_KEY", "00" * 32)
    from app.core.db import connect
    acc = marketing.accounts()[0]
    with connect() as conn:
        conn.execute("UPDATE li_accounts SET target_urn='urn:li:person:abc', scopes='openid profile w_member_social', access_token_enc=?, status='collegato' WHERE id=?",
                     (marketing._enc("tok-finto"), acc["id"]))
    import httpx
    seen = {}

    def handler(req):
        seen["auth"] = req.headers["authorization"]; seen["body"] = req.content.decode()
        return httpx.Response(201, headers={"x-restli-id": "urn:li:share:999"})
    p = marketing.save_post({"text": "Ciao #QUANTO", "account_id": acc["id"]}, "test")
    marketing.set_status(p["id"], "approve", "titolare")
    out = marketing.publish_now(p["id"], "titolare", http=httpx.Client(transport=httpx.MockTransport(handler)))
    assert out["status"] == "PUBBLICATO" and out["urn"] == "urn:li:share:999"
    assert seen["auth"] == "Bearer tok-finto" and "{hashtag|\\\\#|QUANTO}" in seen["body"]


def test_campagne_con_dati_giornalieri_e_csv_di_campaign_manager(secured):
    c = client.post("/api/v2/marketing/campaigns", json={"name": "Lancio studi", "objective": "Contatti", "budget_eur": "500,00"}, headers=hq()).json()
    assert c["budget_eur"] == 500.0
    assert client.post(f"/api/v2/marketing/campaigns/{c['id']}/day", json={"day": "2026-11-10", "impressions": "1000", "clicks": "20", "spend_eur": "40,00", "leads": "2"}, headers=hq()).status_code == 200
    csv = "Start Date;Impressions;Clicks;Total Spent;Leads\n11/11/2026;2000;30;60,00;1\nnon-una-data;1;1;1;1\n"
    imp = client.post(f"/api/v2/marketing/campaigns/{c['id']}/import", json={"content": csv}, headers=hq()).json()
    assert imp == {"imported": 1, "skipped": 1}
    row = [x for x in client.get("/api/v2/marketing/campaigns", headers=hq()).json() if x["id"] == c["id"]][0]
    assert row["impressions"] == 3000 and row["clicks"] == 50 and row["spend_eur"] == 100.0 and row["leads"] == 3
    assert row["cpc_eur"] == 2.0 and row["cpl_eur"] == 33.33 and row["ctr_pct"] == 1.67


def test_le_statistiche_si_aggiungono_e_non_si_riscrivono(secured):
    import psycopg
    from app.core.db import connect
    acc = marketing.accounts()[0]
    marketing.add_followers(acc["id"], "2026-11-01", "1.200", "test")
    with pytest.raises(psycopg.Error):
        with connect() as conn:
            conn.execute("UPDATE li_followers SET followers=1")


def test_le_visite_al_sito_si_registrano_senza_dati_personali_e_finiscono_nella_panoramica(secured):
    ok = client.post("/api/v2/marketing/track", json={"kind": "view", "session": "abcd1234efgh", "path": "/?email=mario@x.it",
                                                     "referrer": "https://www.linkedin.com/feed/?trk=abc", "utm_source": "linkedin"})
    assert ok.status_code == 200 and ok.json()["ok"] is True
    assert client.post("/api/v2/marketing/track", json={"kind": "virus", "session": "abcd1234efgh"}).json()["ok"] is False
    assert client.post("/api/v2/marketing/track", json={"kind": "view", "session": "x"}).json()["ok"] is False
    from app.core.db import connect
    with connect() as conn:
        r = conn.execute("SELECT path, referrer FROM site_events").fetchone()
    assert r["path"] == "/" and r["referrer"] == "https://www.linkedin.com/feed/"                  # niente parametri salvati
    ov = client.get("/api/v2/marketing/overview", headers=hq()).json()
    assert ov["visitors"] == 1 and ov["sources"][0]["fonte"] == "linkedin" and ov["linkedin"]["ready"] is False


def test_il_ritorno_da_linkedin_con_richiesta_falsa_non_collega_nulla(secured):
    r = client.get("/api/v2/marketing/linkedin/callback?code=abc&state=falso", follow_redirects=False)
    assert r.status_code == 303 and "linkedin=errore" in r.headers["location"]
