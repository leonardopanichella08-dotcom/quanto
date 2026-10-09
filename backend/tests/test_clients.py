"""Lo studio e i suoi lavori: ogni azienda cliente ha dati propri che non si mescolano con quelli di un'altra."""
import base64

import psycopg
from fastapi.testclient import TestClient

from app.core import db
from app.core.schema import CLIENTS_DATA_MIGRATION
from main import app
from tests.test_company_profile import BALANCE, upload

client = TestClient(app)


def mk(name):
    r = client.post("/api/v2/clients", json={"name": name})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def H(cid):
    return {"X-Client-Id": str(cid)}


def test_each_job_has_its_own_profile_and_they_never_mix():
    a, b = mk("Azienda Alfa S.r.l."), mk("Azienda Beta S.r.l.")
    assert client.put("/api/v2/profile", json={"fields": {"legal_name": "ALFA SRL", "ateco_code": "62.01"}}, headers=H(a)).status_code == 200
    ov_a = client.get("/api/v2/profile", headers=H(a)).json()
    ov_b = client.get("/api/v2/profile", headers=H(b)).json()
    val = lambda ov, k: next(f["value"] for f in ov["fields"] if f["key"] == k)  # noqa: E731
    assert val(ov_a, "ateco_code") == "62.01" and val(ov_b, "ateco_code") is None
    assert client.put("/api/v2/profile/financials/2025", json={"values": {"revenue_eur": 900000, "personnel_eur": 100000}}, headers=H(a)).status_code == 200
    assert client.get("/api/v2/profile", headers=H(b)).json()["financials"] == []
    assert client.post("/api/v2/profile/forecast", json={"year": 2026}, headers=H(b)).status_code == 422          # Beta non ha bilanci
    assert client.post("/api/v2/profile/forecast", json={"year": 2026}, headers=H(a)).status_code == 200


def test_documents_belong_to_the_job_that_uploaded_them():
    a, b = mk("Uno S.r.l."), mk("Due S.r.l.")
    r = client.post("/api/v2/fonte-c/documents", json={"doc_type": "OTHER", "filename": "durc.pdf", "content_base64": base64.b64encode(b"%PDF-1.4 x").decode()}, headers=H(a))
    assert r.status_code == 201
    assert len(client.get("/api/v2/fonte-c/documents", headers=H(a)).json()) == 1
    assert client.get("/api/v2/fonte-c/documents", headers=H(b)).json() == []
    assert client.get(f"/api/v2/fonte-c/documents/{r.json()['id']}", headers=H(b)).status_code == 404


def test_a_job_of_another_studio_cannot_be_used_and_unknown_ids_are_refused():
    a = mk("Mio cliente")
    assert client.get("/api/v2/profile", headers=H(a + 999)).status_code == 404
    assert client.get("/api/v2/profile", headers={"X-Client-Id": "abc"}).status_code == 400
    from app.core import clients
    assert clients.owns("altro-studio", a) is False


def test_job_list_shows_the_state_of_each_company_and_names_are_unique():
    a = mk("Agricola Verdi")
    client.put("/api/v2/profile", json={"fields": {"ateco_code": "01.11", "region": "Puglia"}}, headers=H(a))
    lst = client.get("/api/v2/clients").json()
    row = next(c for c in lst if c["id"] == a)
    assert row["ateco_code"] == "01.11" and row["region"] == "Puglia" and row["completeness_pct"] > 0 and row["documents"] == 0
    assert client.post("/api/v2/clients", json={"name": "agricola verdi"}).status_code == 422


def test_saved_choices_and_results_are_per_job_and_survive():
    a, b = mk("Alfa"), mk("Beta")
    assert client.get("/api/v2/clients/current/state/allocation", headers=H(a)).json()["value"] is None
    assert client.put("/api/v2/clients/current/state/allocation", json={"value": {"year": 2027, "picked": ["X"]}}, headers=H(a)).status_code == 200
    assert client.get("/api/v2/clients/current/state/allocation", headers=H(a)).json()["value"] == {"year": 2027, "picked": ["X"]}
    assert client.get("/api/v2/clients/current/state/allocation", headers=H(b)).json()["value"] is None
    assert client.get("/api/v2/clients/current/state/allocation").status_code == 400                    # serve un lavoro attivo
    assert client.put("/api/v2/clients/current/state/segreti", json={"value": 1}, headers=H(a)).status_code == 422


def test_deleting_a_job_removes_its_data_and_needs_the_name():
    a = mk("Da Eliminare S.r.l.")
    client.put("/api/v2/profile", json={"fields": {"legal_name": "X"}}, headers=H(a))
    assert client.delete(f"/api/v2/clients/{a}", params={"confirm": "sbagliato"}).status_code == 422
    r = client.delete(f"/api/v2/clients/{a}", params={"confirm": "da eliminare s.r.l."})
    assert r.status_code == 200 and r.json()["deleted"]["company_profiles"] == 1
    assert client.get("/api/v2/profile", headers=H(a)).status_code == 404


def test_templates_remember_which_job_they_come_from_and_stay_when_the_job_is_deleted():
    from app.core.ingestion import Ingestion
    Ingestion.catalog("BANDO-X", "Bando X", "Ente", None, None)
    a = mk("Cliente Template")
    sh = {"personnel_pct": 0.3, "assets_pct": 0.4, "consulting_pct": 0.1, "research_pct": 0.1, "overhead_pct": 0.05, "training_pct": 0.03, "communication_pct": 0.02, "other_pct": 0.0}
    t = client.post("/api/v2/templates", json={"ateco_code": "62.01", "bando_id": "BANDO-X", "shares": sh}, headers=H(a))
    assert t.status_code == 201
    assert client.get("/api/v2/templates").json()[0]["client_name"] == "Cliente Template"
    client.delete(f"/api/v2/clients/{a}", params={"confirm": "Cliente Template"})
    kept = client.get("/api/v2/templates").json()
    assert len(kept) == 1 and kept[0]["client_name"] is None


def test_legacy_single_company_data_becomes_the_first_job_after_migration():
    import json
    with db.connect() as conn:
        conn.execute("INSERT INTO company_profiles (owner, data, sources, updated_at) VALUES (?,?,?,?)", ("user:vecchio@studio.test", json.dumps({"legal_name": "VECCHIA SRL"}), "{}", "2026-01-01T00:00:00Z"))
        conn.execute("INSERT INTO company_financials (owner, fiscal_year, data, sources, updated_at) VALUES (?,?,?,?,?)", ("user:vecchio@studio.test", 2025, "{}", "{}", "2026-01-01T00:00:00Z"))
    with psycopg.connect(db.database_url(), autocommit=True) as raw:
        raw.execute(CLIENTS_DATA_MIGRATION)
    with db.connect() as conn:
        c = conn.execute("SELECT * FROM clients WHERE owner=?", ("user:vecchio@studio.test",)).fetchone()
        assert c["name"] == "VECCHIA SRL"
        assert conn.execute("SELECT COUNT(*) n FROM company_profiles WHERE owner=?", (f"user:vecchio@studio.test#{c['id']}",)).fetchone()["n"] == 1
        assert conn.execute("SELECT COUNT(*) n FROM company_financials WHERE owner=?", (f"user:vecchio@studio.test#{c['id']}",)).fetchone()["n"] == 1
        assert conn.execute("SELECT COUNT(*) n FROM company_profiles WHERE owner=?", ("user:vecchio@studio.test",)).fetchone()["n"] == 0
