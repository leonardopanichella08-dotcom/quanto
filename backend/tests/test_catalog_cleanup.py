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


def test_a_document_is_strict_only_if_titled_like_the_bando_or_it_mentions_it_often():
    from app.core import analysis
    name = "Fondo Test Innovazione"
    assert analysis.is_strict_source({"name": "disposizioni_fondo_test_innovazione.pdf", "url": None}, name, "testo")          # il titolo lo dice
    assert analysis.is_strict_source({"name": "circolare.pdf", "url": "https://x.it/c.pdf"}, name, ("Il Fondo Test Innovazione concede. " * 9))      # citato spesso
    assert analysis.is_strict_source({"name": "scheda.pdf", "url": "https://x.it/s.pdf"}, name, "Il Fondo Test Innovazione. " * 3 + "x" * 2000)        # breve e denso
    assert not analysis.is_strict_source({"name": "bilancio-consolidato.pdf", "url": "https://x.it/b.pdf"}, name, "Il Fondo Test Innovazione. " * 2 + "x" * 500_000)   # citato di passaggio


def test_only_the_latest_edition_of_the_same_document_is_read():
    from app.core import analysis
    mk = lambda sha, url, ts: {"sha256": sha, "name": url.rsplit("/", 1)[-1], "url": url, "ts": ts, "content_type": "application/pdf"}
    old = mk("a", "https://www.simest.it/app/uploads/2025/04/Circolare-4-394-2023-DE-17.04.2025_clean.pdf", "1")
    mid = mk("b", "https://www.simest.it/app/uploads/2025/11/Circolare-4-394-2023-DE-3.11.2025.pdf", "2")
    new = mk("c", "https://www.simest.it/app/uploads/2026/08/Circolare-4-394-2023-DE-30.07.2026.pdf", "3")
    other = mk("d", "https://www.simest.it/app/uploads/2024/07/Circolare-modifica-art-3.6-v-25.07.2024.pdf", "4")
    out = analysis.superseded_shas([old, mid, new, other])
    assert set(out) == {"a", "b"} and out["a"].startswith("Circolare-4-394-2023-DE-30.07.2026")


def test_a_rule_read_by_one_regex_hit_from_a_non_strict_source_waits_for_review_unless_two_sources_agree():
    from app.core import events
    from app.core.ingestion import Ingestion
    Ingestion.catalog("CAT-RULES-HHH888", "Fondo Regole Prova", "Ente", None, None)
    text = "Il contributo a fondo perduto è pari al 50% delle spese ammissibili del progetto presentato dall'impresa beneficiaria."
    one = Ingestion.extract("CAT-RULES-HHH888", sources=[("Bilancio generale", text)], strict_refs=set())
    assert "contribution_rate_pct" not in one.published
    two = Ingestion.extract("CAT-RULES-HHH888", sources=[("Bilancio generale", text), ("Altro documento", text)], strict_refs=set())
    assert two.published.get("contribution_rate_pct") == "0.5"
    Ingestion.catalog("CAT-RULES-III999", "Fondo Regole Seconda", "Ente", None, None)
    assert Ingestion.extract("CAT-RULES-III999", sources=[("Regolamento del Fondo", text)], strict_refs={"Regolamento del Fondo"}).published.get("contribution_rate_pct") == "0.5"
