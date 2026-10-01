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
