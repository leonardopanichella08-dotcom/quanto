import json

from app.core import catalog_meta
from app.core.db import connect


def seed(bando_id, name, meta):
    with connect() as conn:
        conn.execute("INSERT INTO bandi (bando_id, name, issuer, source_url, catalog_status, extraction_status, deadline, summary, catalog_meta, meta_at) "
                     "VALUES (?,?,?,?,?,?,?,?,?,?)", (bando_id, name, "Ente", "https://example.test/x", "CATALOGED", "NOT_STARTED", "2099-12-31", "s", json.dumps(meta), "2026-10-03T00:00:00+00:00"))


def test_summary_is_not_cut_after_an_abbreviation():
    text = ("Avviso pubblico per progetti di ricerca industriale, nell'ambito del Piano complementare istituito con il decreto-legge 6 maggio 2021, n. 59, "
            "convertito dalla legge n. 101 del 2021. Le domande si presentano online entro la scadenza prevista dal bando e saranno valutate da una commissione di esperti.")
    out = catalog_meta._sentences(text, 190)
    assert out.endswith("2021.") and "n." not in out[-8:], out


def test_a_measure_open_to_many_regions_is_not_called_reserved_and_young_company_bandi_are_flagged():
    many = ["Piemonte", "Lombardia", "Veneto", "Lazio", "Toscana", "Sicilia"]
    seed("CAT-NAZIONALE", "Misura nazionale", {"costs": ["Costo del personale"], "regions": many, "state": "APERTO"})
    seed("CAT-GIOVANE", "Call Startup 2026", {"costs": ["Costo del personale"], "state": "APERTO"})
    seed("CAT-SOLO-PIEMONTE", "Voucher piemontese", {"costs": ["Costo del personale"], "regions": ["Piemonte"], "state": "APERTO"})
    out = catalog_meta.rank_for_profile({"region": "Piemonte", "founded_year": 2016, "is_innovative_startup": False}, {"PERSONNEL": 100.0})
    by_id = {i["bando_id"]: i for i in out["items"]}
    assert by_id["CAT-NAZIONALE"]["reasons"][0] == "Ammette la tua regione (Piemonte)" and by_id["CAT-NAZIONALE"]["score"] == 0.75          # nessun bonus: non distingue
    assert by_id["CAT-SOLO-PIEMONTE"]["reasons"][0] == "Riservato alla tua regione (Piemonte)" and by_id["CAT-SOLO-PIEMONTE"]["score"] == 0.85
    assert by_id["CAT-GIOVANE"]["score"] == 0.35 and "2016" in by_id["CAT-GIOVANE"]["to_check"][0]
