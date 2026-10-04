"""Difetti trovati provando l'app come un utente vero (profilo, catalogo, documenti): ognuno ha qui la sua prova."""
import base64
import json

from fastapi.testclient import TestClient

from app.core import bandi, catalog_meta
from app.core.db import connect
from main import app

client = TestClient(app)

PAGE = ('<html><head><meta property="og:title" content="Voucher digitale per le PMI piemontesi | Incentivi"/>'
        '<meta name="description" content="Contributo per la trasformazione digitale delle imprese piemontesi."/></head><body>'
        "<h2>Ulteriori Dettagli</h2><div>Settore attività</div><div>ICT</div><div>Meccanica</div></body></html>")


def seed(bando_id, name, meta=None, deadline="2099-12-31", status="NOT_STARTED", meta_at="2026-10-03T00:00:00+00:00"):
    with connect() as conn:
        conn.execute("INSERT INTO bandi (bando_id, name, issuer, source_url, catalog_status, extraction_status, deadline, summary, catalog_meta, meta_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                     (bando_id, name, "Ente", "https://example.test/x", "CATALOGED", status, deadline, "s", json.dumps(meta) if meta is not None else None, meta_at))


def test_official_title_replaces_the_shortened_name_taken_from_the_address(monkeypatch):
    assert catalog_meta.parse_page(PAGE)["title"] == "Voucher digitale per le PMI piemontesi"
    seed("CAT-VECCHIA-LETTURA", "Voucher Digitale Pmi", {"summary": "s", "state": "APERTO"})          # letta prima che esistesse il titolo: va riletta
    monkeypatch.setattr(catalog_meta.research, "http_get", lambda url, **kw: (PAGE.encode("utf-8"), url, "text/html; charset=utf-8"))
    rep = catalog_meta.describe_batch(limit=5, budget_s=10.0)
    assert rep["read"] == 1
    with connect() as conn:
        assert conn.execute("SELECT name FROM bandi WHERE bando_id='CAT-VECCHIA-LETTURA'").fetchone()["name"] == "Voucher digitale per le PMI piemontesi"
    assert catalog_meta.describe_batch(limit=5, budget_s=10.0)["read"] == 0                           # con il titolo salvato non si rilegge


def test_ranking_uses_the_sector_and_breaks_ties_by_the_closing_date():
    seed("CAT-ICT", "Misura per l'ICT", {"costs": ["Costo del personale"], "sectors": ["ICT", "Elettronica"], "state": "APERTO"}, deadline="2030-01-01")
    seed("CAT-MECCANICA", "Misura per la meccanica", {"costs": ["Costo del personale"], "sectors": ["Meccanica", "Metallurgia"], "state": "APERTO"}, deadline="2030-01-01")
    seed("CAT-PRIMA", "Misura che scade prima", {"costs": ["Costo del personale"], "state": "APERTO"}, deadline="2027-03-01")
    seed("CAT-DOPO", "Misura che scade dopo", {"costs": ["Costo del personale"], "state": "APERTO"}, deadline="2029-03-01")
    out = catalog_meta.rank_for_profile({"ateco_code": "62.01.00"}, {"PERSONNEL": 100.0})
    by = {i["bando_id"]: i for i in out["items"]}
    assert by["CAT-ICT"]["score"] == 0.9 and any("ICT" in r for r in by["CAT-ICT"]["reasons"])
    assert by["CAT-MECCANICA"]["score"] == 0.45 and by["CAT-MECCANICA"]["to_check"][0].startswith("settore: il bando indica Meccanica")
    ids = [i["bando_id"] for i in out["items"]]
    assert ids.index("CAT-ICT") < ids.index("CAT-PRIMA") < ids.index("CAT-DOPO") < ids.index("CAT-MECCANICA")   # a pari affinità, prima chi scade prima


def test_studied_catalog_bandi_show_open_or_closed_from_the_official_deadline():
    class Row(dict):
        pass
    assert bandi._catalog_status(Row(deadline="2020-05-01", extraction_status="PARTIAL")).startswith("CHIUSO (scaduto il 01/05/2020")
    assert bandi._catalog_status(Row(deadline="2099-12-31", extraction_status="PARTIAL")) == "APERTO (fino al 31/12/2099)"
    assert bandi._catalog_status(Row(deadline="non indicata", extraction_status="PARTIAL")) == "IN LAVORAZIONE"


def test_empty_files_are_refused_and_file_names_lose_their_path():
    empty = client.post("/api/v2/fonte-c/documents", json={"doc_type": "OTHER", "filename": "vuoto.xlsx", "content_base64": ""})
    assert empty.status_code == 422 and "vuoto" in empty.json()["detail"]
    ok = client.post("/api/v2/fonte-c/documents", json={"doc_type": "OTHER", "filename": "../../etc/passwd\\..\\durc.pdf", "content_base64": base64.b64encode(b"%PDF-1.4 x").decode()})
    assert ok.status_code == 201 and ok.json()["filename"] == "durc.pdf"


def test_a_growth_for_an_unknown_category_is_an_error_not_silently_ignored():
    client.put("/api/v2/profile/financials/2025", json={"values": {"personnel_eur": 100000}})
    r = client.post("/api/v2/profile/forecast", json={"year": 2026, "growth": {"BANANE": 0.1}})
    assert r.status_code == 422 and "Categoria sconosciuta: BANANE" in r.json()["detail"]


def test_template_leaves_personnel_out_and_warns_about_cup_milestones_and_amortization():
    from app.core.ingestion import Ingestion
    Ingestion.catalog("BANDO-TPL", "Bando di prova", "Ente", None, None)
    Ingestion.extract("BANDO-TPL", source_text="Il contributo a fondo perduto è pari al 50% delle spese ammissibili. Ogni spesa deve riportare il CUP.", source_ref="testo")
    client.put("/api/v2/profile/financials/2025", json={"values": {"personnel_eur": 200000, "capital_assets_eur": 40000}})
    t = client.post("/api/v2/profile/template", json={"bando_id": "BANDO-TPL", "scale_pct": 50}).json()
    assert [i["category"] for i in t["cost_items"]] == ["CAPITAL_ASSETS"] and t["needs_personnel"]["amount_eur"] == 100000.0
    assert "persona per persona" in t["needs_personnel"]["message"]
