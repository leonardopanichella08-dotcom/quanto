"""Pulizia del catalogo nazionale: le misure locali «una tantum» di anni passati, mai toccate da nessuno, si eliminano da sole."""
from app.core import catalog_job
from app.core.db import connect
from app.core.ingestion import Ingestion


def test_old_untouched_catalog_entries_are_deleted_but_curated_and_touched_ones_are_never_removed():
    Ingestion.catalog("CAT-OLD-UNA-TANTUM-AAA111", "2021 Bando Contributi Fondo Perduto Comune Di Prova", "Comune di Prova", None,
                       "https://example.test/2021")
    Ingestion.catalog("CAT-CURRENT-2026-BBB222", "Agevolazioni Servizi Campo Ambientale 2026 Camera Di Commercio", "incentivi.gov.it", None,
                       "https://example.test/2026")
    Ingestion.catalog("CAT-OLD-BUT-REQUESTED-CCC333", "2021 Bando Richiesto Da Un Cliente", "Comune di Prova", None, "https://example.test/req")
    Ingestion.catalog("CAT-OLD-PAST-DEADLINE-DDD444", "Bando Con Scadenza Passata", "Comune di Prova", "2024-01-01", "https://example.test/deadline")
    with connect() as conn:
        conn.execute("UPDATE bandi SET requested_by_clients = 1 WHERE bando_id = 'CAT-OLD-BUT-REQUESTED-CCC333'")
        conn.execute(
            "INSERT INTO bandi (bando_id, name, issuer, catalog_status, extraction_status) VALUES ('CURATED-2020-SAMPLE', '2020 Misura Storica Curata', 'Test', 'CURATED', 'COMPLETED')")

    report = catalog_job.cleanup_stale(actor="test")

    with connect() as conn:
        remaining = {r["bando_id"] for r in conn.execute("SELECT bando_id FROM bandi").fetchall()}
    assert report["deleted"] == 2
    assert "CAT-OLD-UNA-TANTUM-AAA111" not in remaining
    assert "CAT-OLD-PAST-DEADLINE-DDD444" not in remaining
    assert "CAT-CURRENT-2026-BBB222" in remaining                 # anno corrente: resta
    assert "CAT-OLD-BUT-REQUESTED-CCC333" in remaining            # un cliente l'ha richiesto: non si tocca
    assert "CURATED-2020-SAMPLE" in remaining                     # curato: mai toccato dalla pulizia automatica


def test_refresh_runs_cleanup_too_and_reports_how_many_were_deleted(monkeypatch):
    Ingestion.catalog("CAT-STALE-FOR-REFRESH-EEE555", "2019 Bando Da Eliminare", "Comune di Prova", None, "https://example.test/2019")
    monkeypatch.setattr(catalog_job.discovery, "CATALOGS", [])        # non serve raggiungere davvero i cataloghi istituzionali in questo test
    report = catalog_job.refresh(enrich=0, actor="test")
    assert report["deleted"] == 1
    with connect() as conn:
        assert not conn.execute("SELECT 1 FROM bandi WHERE bando_id = 'CAT-STALE-FOR-REFRESH-EEE555'").fetchone()


def test_a_spreadsheet_source_is_kept_but_never_read_as_if_it_were_the_bando_text():
    from app.core import analysis, events
    Ingestion.catalog("CAT-WITH-DATASET-FFF666", "Bando Con Elenco Beneficiari", "Ente", None, "https://example.test/x")
    sheet = "### Foglio: Foglio1\n" + "\n".join(f"AZIENDA {i} SRL | 1234567890{i} | Lazio | RM | ROMA | 100000 | Life sciences | 2023-01-01" for i in range(40))
    events.save_bando_source("CAT-WITH-DATASET-FFF666", "elenco.xlsx", sheet, url="https://example.test/elenco.xlsx", tier="UFFICIALE",
                             content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", pages=None, origin="WEB", file_sha256=None, warnings=[])
    out = analysis.run_analysis("CAT-WITH-DATASET-FFF666")
    assert out["requirements"] == []
    assert "dati di riferimento" in out["report"][0]["note"]


def test_a_long_document_titled_like_the_bando_is_read_whole_not_only_where_the_exact_name_appears():
    from app.core import analysis, events
    Ingestion.catalog("CAT-OWN-DOC-GGG777", "Fondo Test Innovazione", "Ente", None, "https://example.test/f")
    filler = "Il Fondo concede un contributo alle imprese ammissibili secondo le condizioni stabilite. " * 700
    body = filler + "\n\nLe consulenze non possono superare il 20% del totale delle spese ammissibili del progetto presentato. " + filler
    events.save_bando_source("CAT-OWN-DOC-GGG777", "disposizioni_fondo_test_innovazione.pdf", body, url="https://example.test/disposizioni_fondo_test_innovazione.pdf",
                             tier="UFFICIALE", content_type="application/pdf", pages=90, origin="WEB", file_sha256=None, warnings=[])
    assert len(body) > 60_000
    out = analysis.run_analysis("CAT-OWN-DOC-GGG777")
    assert any("20%" in r["text"] for r in out["requirements"])


def test_issuer_documents_are_read_whole_but_general_law_collections_stay_filtered():
    from app.core import analysis
    name = "Fondo Test Innovazione"
    assert analysis.is_own_document({"name": "Circolare 4-2026.pdf", "url": "https://www.simest.it/app/uploads/circolare.pdf"}, name)
    assert analysis.is_own_document({"name": "testo-incollato.txt", "url": None}, name)
    assert not analysis.is_own_document({"name": "Regolamento UE 1407", "url": "https://eur-lex.europa.eu/legal-content/IT/TXT/?uri=CELEX:32013R1407"}, name)
    assert not analysis.is_own_document({"name": "DL 179", "url": "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.legge:2012-10-18;179"}, name)
