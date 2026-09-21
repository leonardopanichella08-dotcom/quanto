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
