"""Fonti ufficiali dei bandi: registro, raccoglitore generico, scarto di ciò che non è un bando, stato visibile."""
import json
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core import catalog_meta, official_sources as osrc, research
from app.core.db import connect
from main import app

client = TestClient(app)
THIS_YEAR = date.today().year


@pytest.mark.parametrize("title", [
    "Bando voucher servizi IR (V-IR)",
    "Contributo a fondo perduto per gestori impianti natatori",
    f"Voucher digitalizzazione PMI {THIS_YEAR}",
    "PR FESR 21-27 Sostegno alla prima crescita delle start up innovative",
    "Aperto 23 Ott 2026 «TecSTEP» - Fondo Tecnologie STEP per il sostegno alle imprese",
])
def test_real_grants_pass_the_title_filter(title):
    assert osrc.looks_like_grant(title)


@pytest.mark.parametrize("title", [
    "Bandi e avvisi",                                                       # nome di una sezione del sito
    "Fondi e finanziamenti europei",
    "Esplora la sezione Bandi e avvisi",
    "Avviso pubblico per la concessione dell'area verde di proprietà della Regione",
    "Bando di gara per la fornitura di arredi per gli uffici",
    "Avviso di selezione per n. 1 posto di livello dirigenziale",
    "Contributi ai Comuni per la videosorveglianza",
    "Avviso pubblico EPS 2024",                                             # edizione passata
    "POR FESR 14/20 Fondo PMI",                                             # programmazione passata
    "Conclusione 22 Ott 2026 NUOVO AVVISO PUBBLICO per voucher",           # il sito dice che è concluso
    "Webinar - Bando Consulenza Sviluppo Impresa: proroghe e novità",
    "Pensione e previdenza: contributi figurativi",
])
def test_navigation_tenders_old_editions_and_non_grants_are_rejected(title):
    assert not osrc.looks_like_grant(title)


def test_title_is_cleaned_without_inventing_anything():
    assert osrc.clean_title("Per saperne di più su Voucher digitalizzazione PMI 2026") == "Voucher digitalizzazione PMI 2026"
    assert osrc.clean_title("31/07/2026 Veneto Sviluppo/Veneto Innovazione Informa Fondo Veneto Ricerca bando 1.1.3") == "Fondo Veneto Ricerca bando 1.1.3"
    assert osrc.clean_title("Domande online entro le ore 12 del 30 ottobre Contributi per progetti di distretto") == "Contributi per progetti di distretto"


def test_extract_items_separates_grants_from_section_pages_and_ignores_other_sites():
    links = [("/bandi", "Bandi e avvisi"), ("/bandi/voucher-export-2027", "Voucher export per le PMI 2027"), ("https://blog-consulenti.example.com/x", "Bando voucher export spiegato bene"),
             ("/contatti", "Contatti"), ("/files/bando.pdf", "Avviso pubblico per il sostegno alle imprese artigiane"), ("/n/1", "Gara d'appalto per la mensa")]
    items, hubs = osrc.extract_items("https://www.regione.esempio.it/home", links)
    assert [i["title"] for i in items] == ["Voucher export per le PMI 2027", "Avviso pubblico per il sostegno alle imprese artigiane"]
    assert hubs == ["https://www.regione.esempio.it/bandi"]


def _fake_web(monkeypatch, pages):
    def fake_get(url, max_bytes=0, accept_error_body=False, timeout=0, limited=True):
        if url in pages:
            body, ctype = pages[url]
            return body.encode() if isinstance(body, str) else body, url, ctype
        raise research.ResearchError("Il sito ha risposto 404")
    monkeypatch.setattr(research, "http_get", fake_get)


HOME = """<html><body><a href="/bandi">Bandi e avvisi</a><a href="/news">Notizie</a></body></html>"""
HUB = """<html><body>
<a href="/bandi/voucher-digitale-2027">Voucher digitale per le imprese 2027</a>
<a href="/bandi/fondo-startup">Fondo per le startup innovative della Regione</a>
<a href="/gare/mensa">Bando di gara per la mensa</a></body></html>"""
GOOD = """<html><head><meta property="og:title" content="Regione Esempio"><meta name="description" content="Voucher per la digitalizzazione delle imprese del territorio regionale con spese ammissibili ed elenco dei beneficiari."></head><body>
<h1>Voucher digitale</h1><p>Beneficiari: micro e piccole imprese. Spese ammissibili: software e consulenze. Dotazione finanziaria: 2 milioni. Presentazione delle domande entro il 30/11/2099. A fondo perduto fino all'80%.</p></body></html>"""
BAD = """<html><body><h1>Fondo startup</h1><p>Pagina informativa generica sul programma regionale, senza alcun dettaglio.</p></body></html>"""


def _source():
    return {"id": "esempio", "name": "Regione Esempio", "level": osrc.REGIONE, "home": "https://www.regione.esempio.it/", "region": "Umbria", "hubs": [], "topic": "", "note": "", "manual": False}


def test_harvest_registers_new_grants_once_with_source_and_region_and_never_the_tender(monkeypatch):
    _fake_web(monkeypatch, {"https://www.regione.esempio.it/": (HOME, "text/html"), "https://www.regione.esempio.it/bandi": (HUB, "text/html")})
    res = osrc.harvest_source(_source())
    assert res["ok"] and res["pages"] == 2
    titles = {i["title"] for i in res["items"]}
    assert titles == {"Voucher digitale per le imprese 2027", "Fondo per le startup innovative della Regione"}
    assert osrc.register_items(_source(), res["items"]) == 2
    assert osrc.register_items(_source(), res["items"]) == 0                     # rilancio: niente doppioni
    with connect() as conn:
        rows = conn.execute("SELECT bando_id, name, issuer, catalog_status, extraction_status, catalog_meta FROM bandi").fetchall()
    assert len(rows) == 2 and all(r["bando_id"].startswith("CAT-") and r["issuer"] == "Regione Esempio" and r["extraction_status"] == "NOT_STARTED" for r in rows)
    seed = json.loads(rows[0]["catalog_meta"])
    assert seed["harvested"] is True and seed["regions"] == ["Umbria"] and seed["source_id"] == "esempio"


def test_an_entry_whose_page_does_not_read_like_a_grant_is_rejected_and_hidden_but_a_real_one_keeps_its_name_and_region(monkeypatch):
    pages = {"https://www.regione.esempio.it/": (HOME, "text/html"), "https://www.regione.esempio.it/bandi": (HUB, "text/html"),
             "https://www.regione.esempio.it/bandi/voucher-digitale-2027": (GOOD, "text/html"), "https://www.regione.esempio.it/bandi/fondo-startup": (BAD, "text/html")}
    _fake_web(monkeypatch, pages)
    osrc.register_items(_source(), osrc.harvest_source(_source())["items"])
    out = catalog_meta.describe_batch(limit=10, workers=2, budget_s=20, actor="test")
    assert out["read"] == 2 and out["rejected"] == 1
    with connect() as conn:
        good = conn.execute("SELECT * FROM bandi WHERE name LIKE 'Voucher digitale%'").fetchone()
        bad = conn.execute("SELECT * FROM bandi WHERE name LIKE 'Fondo per le startup%'").fetchone()
    assert good["extraction_status"] == "NOT_STARTED" and good["name"] == "Voucher digitale per le imprese 2027"        # l'og:title «Regione Esempio» non sostituisce il nome
    meta = json.loads(good["catalog_meta"])
    assert meta["regions"] == ["Umbria"] and meta["grant_signals"] >= 3 and "title" not in meta
    assert bad["extraction_status"] == "REJECTED" and json.loads(bad["catalog_meta"])["not_a_grant"] is True
    reg = osrc.registry()
    assert reg["totals"]["catalog"] == 1 and reg["totals"]["read"] == 1                # la voce scartata non conta né si mostra
    with connect() as conn:
        assert catalog_meta.describe_batch(limit=10, workers=2, budget_s=10)["read"] == 0   # non si rilegge ogni giorno
    names = [i["name"] for i in client.get("/api/v2/bandi/catalog?q=startup").json()["items"]]
    assert "Fondo per le startup innovative della Regione" not in names
    assert osrc.register_items(_source(), [{"url": "https://www.regione.esempio.it/bandi/fondo-startup", "title": "Fondo per le startup innovative della Regione"}]) == 0   # e non torna


def test_registry_tells_the_truth_about_each_source(monkeypatch):
    sources = [
        {**_source(), "id": "ok", "name": "Ente ok", "home": "https://www.regione.ok.it/"},
        {**_source(), "id": "js", "name": "Ente js", "home": "https://www.regione.js.it/"},
        {**_source(), "id": "down", "name": "Ente giù", "home": "https://www.regione.down.it/"},
        {**_source(), "id": "empty", "name": "Ente vuoto", "home": "https://www.regione.vuoto.it/"},
    ]
    monkeypatch.setattr(osrc, "SOURCES", sources)
    monkeypatch.setattr(osrc, "BY_ID", {s["id"]: s for s in sources})
    _fake_web(monkeypatch, {"https://www.regione.ok.it/": ('<a href="/b/voucher-export-2027">Voucher export per le PMI 2027</a>', "text/html"),
                            "https://www.regione.js.it/": ("<html><body><div id='app'></div></body></html>", "text/html"),
                            "https://www.regione.vuoto.it/": ('<a href="/chi-siamo">Chi siamo</a>', "text/html")})
    rep = osrc.run(budget_s=20, workers=4, actor="test")
    assert rep["checked"] == 4 and rep["reachable"] == 3 and rep["new"] == 1
    status = {s["id"]: s["status"] for s in osrc.registry()["sources"]}
    assert status == {"ok": "LETTA", "js": "SOLO_JAVASCRIPT", "down": "NON_RAGGIUNGIBILE", "empty": "NESSUN_BANDO_TROVATO"}


def test_registry_covers_ministries_agencies_all_regions_and_the_eu():
    by_level = {}
    for s in osrc.SOURCES:
        by_level.setdefault(s["level"], []).append(s)
    assert {osrc.NAZ, osrc.AGENZIA, osrc.REGIONE, osrc.UE, osrc.CAMERE} <= set(by_level)
    from app.core.company_profile import REGIONS
    covered = {s["region"] for s in by_level[osrc.REGIONE]}
    assert set(REGIONS) <= covered                                          # tutte le 20 Regioni e province autonome
    assert len({s["id"] for s in osrc.SOURCES}) == len(osrc.SOURCES)
    assert {"incentivi", "invitalia"} <= osrc.HARVESTED_BY_OTHER
    assert all(s["home"].startswith("https://") for s in osrc.SOURCES)


def test_sources_api_lists_the_registry_and_throttles_refresh(monkeypatch):
    r = client.get("/api/v2/sources")
    assert r.status_code == 200 and r.json()["totals"]["sources"] == len(osrc.SOURCES)
    monkeypatch.setattr(osrc, "run", lambda ids=None, **kw: {"checked": 1, "reachable": 1, "found": 0, "new": 0, "skipped": 0, "sources": [], "seconds": 0.1})
    from app.api.endpoints import sources as ep
    ep._LAST_RUN = 0.0
    assert client.post("/api/v2/sources/refresh", json={}).status_code == 200
    assert client.post("/api/v2/sources/refresh", json={}).status_code == 429          # a raffica no: interroga decine di siti ufficiali
