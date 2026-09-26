"""Ricerca nell'elenco interno e conferma prima dell'estrazione (schema FKOS, Fonte A Stadio 1: «Cliente cerca il bando»)."""
from fastapi.testclient import TestClient

from app.core import events
from app.core.ingestion import Ingestion
from main import app

client = TestClient(app)


def search(q):
    return client.get("/api/v2/bandi/search", params={"q": q}).json()["matches"]


def test_exact_and_approximate_names_find_the_curated_bando():
    assert search("Nuova Sabatini")[0]["bando_id"] == "NUOVA-SABATINI"
    assert search("sabatini")[0]["bando_id"] == "NUOVA-SABATINI"                       # parola sola
    assert search("Nuva Sabatinni")[0]["bando_id"] == "NUOVA-SABATINI"                 # con errori di battitura
    assert search("transizione 5.0")[0]["curated"] is True
    assert search("zzzz qqqq") == []


def test_matches_report_cache_state_and_hide_empty_web_entries():
    Ingestion.catalog("WEB-VUOTO", "Bando Vuoto Che Non Ha Nulla", None, None, None)
    assert not [m for m in search("Bando Vuoto") if m["bando_id"] == "WEB-VUOTO"]     # senza regole né documenti non si propone
    Ingestion.catalog("WEB-CON-REGOLE", "Fondo Con Regole", None, None, None)
    Ingestion.extract("WEB-CON-REGOLE", source_text="Il contributo è pari al 60% delle spese ammissibili.")
    m = [x for x in search("Fondo Con Regole") if x["bando_id"] == "WEB-CON-REGOLE"][0]
    assert m["cache_hit"] is True and m["rules"] >= 1


def test_confirm_creates_the_catalog_entry_only_now_and_reports_cache():
    assert client.get("/api/v2/ingestion/catalog").json() == [] or "WEB-NUOVO-FONDO" not in [b["bando_id"] for b in client.get("/api/v2/ingestion/catalog").json()]
    first = client.post("/api/v2/bandi/research/confirm", json={"name": "Nuovo Fondo"}).json()
    assert first["bando_id"] == "WEB-NUOVO-FONDO" and first["cache_hit"] is False and first["requested_by_clients_count"] == 1
    Ingestion.extract("WEB-NUOVO-FONDO", source_text="Il contributo è pari al 40% delle spese ammissibili.")
    events.save_bando_source("WEB-NUOVO-FONDO", "doc", "testo del documento ufficiale", url="https://x.gov.it/a", tier="UFFICIALE")
    second = client.post("/api/v2/bandi/research/confirm", json={"name": "Nuovo Fondo"}).json()
    assert second["cache_hit"] is True and second["complete"] is True and second["requested_by_clients_count"] == 2       # riuso tra clienti


# ------------------------------------------------------------------ sfoglia il catalogo (bandi non ancora analizzati, non solo per nome esatto)
def browse(**params):
    return client.get("/api/v2/bandi/catalog", params=params).json()


def test_browse_paginates_and_finds_by_name_without_knowing_the_exact_title():
    Ingestion.catalog("CAT-VOUCHER-DIGITALE-LOMBARDIA-1", "Voucher digitale Lombardia", "Regione Lombardia", None, "https://x.it/a")
    Ingestion.catalog("CAT-VOUCHER-DIGITALE-PIEMONTE-2", "Voucher digitale Piemonte", "Regione Piemonte", None, "https://x.it/b")
    r = browse(q="voucher digitale", page=1, page_size=1)
    assert r["total"] == 2 and r["pages"] == 2 and len(r["items"]) == 1
    ids = {browse(q="voucher digitale", page=1, page_size=1)["items"][0]["bando_id"], browse(q="voucher digitale", page=2, page_size=1)["items"][0]["bando_id"]}
    assert ids == {"CAT-VOUCHER-DIGITALE-LOMBARDIA-1", "CAT-VOUCHER-DIGITALE-PIEMONTE-2"}


def test_browse_marks_catalog_only_entries_and_only_new_hides_the_rest():
    Ingestion.catalog("CAT-DA-ANALIZZARE-X", "Bando tutto da analizzare", "Comune di Test", None, "https://x.it/c")
    only_this = browse(q="tutto da analizzare")["items"][0]
    assert only_this["catalog_only"] is True and only_this["curated"] is False
    assert any(x["bando_id"] == "NUOVA-SABATINI" for x in browse(q="sabatini", only_new=False)["items"])
    assert not any(x["bando_id"] == "NUOVA-SABATINI" for x in browse(q="sabatini", only_new=True)["items"])   # già curato: non e' "da analizzare"


def test_catalog_issuers_lists_distinct_non_empty_values():
    Ingestion.catalog("CAT-ENTE-PROVA", "Bando dell'ente di prova", "Ente Prova Unico XYZ", None, "https://x.it/d")
    issuers = client.get("/api/v2/bandi/catalog/issuers").json()
    assert "Ente Prova Unico XYZ" in issuers and len(issuers) == len(set(issuers)) and None not in issuers and "" not in issuers
