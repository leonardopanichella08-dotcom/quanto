"""Schede del catalogo: descrizione e caratteristiche lette dalla pagina, e ordinamento per affinità con l'azienda."""
import json

from fastapi.testclient import TestClient

from app.core import catalog_meta
from app.core.db import connect
from main import app

client = TestClient(app)

PAGE = """<html><head><title>Voucher digitale</title>
<meta name="description" content="Contributo a fondo perduto per la trasformazione digitale delle piccole imprese lombarde, con spese di consulenza e macchinari." />
</head><body><main>
<div>In Arrivo</div><div>Data apertura</div><div>01/01/2099</div><div>Data chiusura</div><div>31/12/2099</div>
<h2>Cos'è</h2><p>Un voucher che copre una parte dei costi di digitalizzazione.</p><p>Altro paragrafo.</p>
<h3>A chi si rivolge</h3><p>Alle piccole imprese.</p>
<h2>Ulteriori Dettagli</h2>
<div>Forma agevolazione</div><div>Contributo/Fondo perduto</div>
<div>Costi ammessi</div><div>Progettazione/studi/consulenze</div><div>Impianti/Macchinari/Attrezzature</div><div>Progettazione/studi/consulenze</div>
<div>Agevolazione concedibile (min-max)</div><div>Fino a 10.000 €</div>
<div>Dimensione</div><div>Microimpresa ,</div><div>Piccola Impresa</div>
<div>ATECO</div><div>Tutti i settori economici ammissibili a ricevere aiuti;</div>
<div>Regioni</div><div>Lombardia</div>
<div>Soggetto gestore</div><div>Regione Lombardia</div>
<div>Base normativa primaria</div><div>Legge regionale qualunque, con un testo lungo che non deve finire nel gestore</div>
</main></body></html>"""

COLON_PAGE = """<html><body><h2>Cos'è</h2><p>Il bando assegna contributi diretti a:</p><p>- sostenere la transizione energetica;</p><p>- ridurre le emissioni</p>
<h3>A chi si rivolge</h3><p>Alle imprese.</p></body></html>"""


def test_page_is_read_without_inventing_anything():
    m = catalog_meta.parse_page(PAGE)
    assert m["summary"].startswith("Contributo a fondo perduto per la trasformazione digitale") and "dichiarata" in m["summary_source"]
    assert m["what_it_is"] == "Un voucher che copre una parte dei costi di digitalizzazione."
    assert m["form"] == ["Contributo/Fondo perduto"] and m["costs"] == ["Progettazione/studi/consulenze", "Impianti/Macchinari/Attrezzature"]   # senza doppioni
    assert m["sizes"] == ["Microimpresa", "Piccola Impresa"] and m["regions"] == ["Lombardia"] and m["benefit_range"] == "Fino a 10.000 €"
    assert m["manager"] == "Regione Lombardia" and m["ateco_all"] is True
    assert m["opens"] == "2099-01-01" and m["closes"] == "2099-12-31" and m["state"] == "IN_ARRIVO"
    assert catalog_meta.cost_categories(m) == ["CONSULTING", "CAPITAL_ASSETS"]
    assert "spend_range" not in m                                                                   # la pagina non lo dice: assente, non riempito


def test_description_falls_back_to_the_what_it_is_paragraph_and_completes_a_list():
    m = catalog_meta.parse_page(COLON_PAGE)
    assert m["summary"] == "Il bando assegna contributi diretti a: sostenere la transizione energetica; ridurre le emissioni"
    assert "Cos'è" in m["summary_source"]
    assert catalog_meta.cost_categories(m) is None                                                  # nessun costo dichiarato: non si deduce


def seed(bando_id, name, meta, deadline="2099-12-31", status="NOT_STARTED"):
    with connect() as conn:
        conn.execute("INSERT INTO bandi (bando_id, name, issuer, source_url, catalog_status, extraction_status, deadline, summary, catalog_meta, meta_at) "
                     "VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT (bando_id) DO NOTHING",
                     (bando_id, name, "Ente", f"https://example.test/{bando_id}", "CATALOGED", status, deadline, meta.get("summary"), json.dumps(meta), "2026-10-03T00:00:00+00:00"))


def test_ranking_excludes_what_cannot_apply_and_orders_by_spend_coverage():
    seed("CAT-CONSULENZE", "Voucher consulenze", {"summary": "s1", "costs": ["Progettazione/studi/consulenze"], "regions": ["Lombardia"], "sizes": ["Piccola Impresa"], "state": "APERTO"})
    seed("CAT-TUTTO", "Misura generale", {"summary": "s2", "costs": ["Costo del personale", "Impianti/Macchinari/Attrezzature", "Servizi professionali"], "state": "APERTO"})
    seed("CAT-ALTRA-REGIONE", "Bando Sicilia", {"summary": "s3", "costs": ["Costo del personale"], "regions": ["Sicilia"], "state": "APERTO"})
    seed("CAT-GRANDI", "Solo grandi imprese", {"summary": "s4", "costs": ["Costo del personale"], "sizes": ["Grande Impresa"], "state": "APERTO"})
    seed("CAT-SCADUTO", "Bando scaduto", {"summary": "s5", "costs": ["Costo del personale"], "state": "CHIUSO"}, deadline="2020-01-01")
    seed("CAT-ATECO", "Solo manifattura", {"summary": "s6", "costs": ["Costo del personale"], "ateco_codes": ["25", "28"], "state": "APERTO"})
    seed("CAT-SENZA-COSTI", "Scheda povera", {"summary": "s7", "state": "APERTO"})
    profile = {"region": "Lombardia", "ateco_code": "62.01.00", "size": {"code": "SMALL"}, "is_innovative_startup": False}
    by_cat = {"PERSONNEL": 600.0, "CONSULTING": 100.0, "CAPITAL_ASSETS": 300.0}
    out = catalog_meta.rank_for_profile(profile, by_cat)
    ids = [i["bando_id"] for i in out["items"]]
    assert ids[0] == "CAT-TUTTO" and "CAT-CONSULENZE" in ids and ids[-1] == "CAT-SENZA-COSTI"
    assert not {"CAT-ALTRA-REGIONE", "CAT-GRANDI", "CAT-SCADUTO", "CAT-ATECO"} & set(ids)
    top = out["items"][0]
    assert top["score"] == 0.75 and top["affinity"] == "ALTA" and any("personale" in r for r in top["reasons"])
    cons = next(i for i in out["items"] if i["bando_id"] == "CAT-CONSULENZE")
    assert cons["score"] == 0.175 and any("tua regione" in r for r in cons["reasons"])           # consulenze = 100 su 1000 x 0,75 = 0,075, +0,1 per la regione
    assert next(i for i in out["items"] if i["bando_id"] == "CAT-SENZA-COSTI")["to_check"] == ["spese ammesse non dichiarate"]
    assert out["excluded"] == 3                                                                      # il bando scaduto non arriva nemmeno alla selezione


def test_unknown_profile_data_is_flagged_not_assumed():
    seed("CAT-REGIONALE", "Bando regionale", {"summary": "x", "costs": ["Costo del personale"], "regions": ["Lombardia"], "ateco_codes": ["62"], "state": "APERTO"})
    out = catalog_meta.rank_for_profile({}, {"PERSONNEL": 100.0})
    item = next(i for i in out["items"] if i["bando_id"] == "CAT-REGIONALE")
    assert set(item["to_check"]) >= {"regione", "ATECO"}


def test_describe_batch_stores_the_page_and_sets_the_deadline(monkeypatch):
    with connect() as conn:
        conn.execute("INSERT INTO bandi (bando_id, name, issuer, source_url, catalog_status, extraction_status) VALUES (?,?,?,?,?,?)",
                     ("CAT-DA-LEGGERE", "Voucher digitale", "incentivi", "https://www.incentivi.gov.it/it/catalogo/voucher", "CATALOGED", "NOT_STARTED"))
    monkeypatch.setattr(catalog_meta.research, "http_get", lambda url, **kw: (PAGE.encode("utf-8"), url, "text/html; charset=utf-8"))
    rep = catalog_meta.describe_batch(limit=10, budget_s=20.0)
    assert rep["read"] == 1 and rep["remaining"] == 0
    with connect() as conn:
        row = conn.execute("SELECT summary, catalog_meta, meta_at, deadline FROM bandi WHERE bando_id='CAT-DA-LEGGERE'").fetchone()
    assert row["summary"].startswith("Contributo a fondo perduto") and row["meta_at"] and row["deadline"] == "2099-12-31"
    assert json.loads(row["catalog_meta"])["regions"] == ["Lombardia"]
    assert catalog_meta.describe_batch(limit=10, budget_s=20.0)["read"] == 0                    # già letto: non si rilegge


def test_summaries_are_visible_in_the_catalog_browser_and_the_detail():
    seed("CAT-VISIBILE", "Voucher visibile", {"summary": "Descrizione breve.", "form": ["Prestito"], "state": "APERTO"})
    page = client.get("/api/v2/bandi/catalog?q=visibile").json()
    assert page["items"][0]["summary"] == "Descrizione breve."
    detail = client.get("/api/v2/bandi/CAT-VISIBILE").json()
    assert detail["catalog"]["summary"] == "Descrizione breve." and detail["catalog"]["meta"]["form"] == ["Prestito"]
