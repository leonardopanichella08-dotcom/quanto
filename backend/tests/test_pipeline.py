"""Il processo standard di studio di un bando: ciclo di vita, cifre strutturate, pipeline cerca→scarica→leggi→valuta."""
from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.core import catalog_job, lifecycle, pipeline, research
from app.core.db import connect
from app.core.ingestion import Ingestion
from app.core.requirements_extractor import extract_figures
from main import app

client = TestClient(app)


# ------------------------------------------------------------------ cifre: tetti e soglie
def figs(sentence):
    return [(f["kind"], f["value"], f["bound"]) for f in extract_figures(sentence)]


def test_figures_tell_a_cap_from_a_floor_and_ignore_dates_and_act_numbers():
    assert figs("Le consulenze non possono superare il 20% del totale delle spese ammissibili.") == [("PERCENT", 20.0, "MAX")]
    assert figs("L'importo minimo del progetto è pari ad almeno 100.000 euro.") == [("EUR", 100000.0, "MIN")]
    assert ("EUR", 2000000.0, "MAX") in figs("Il finanziamento è concesso fino a € 2.000.000 per un periodo non superiore a 60 mesi.")
    assert ("DURATION", 60, "MAX") in figs("Il finanziamento è concesso fino a € 2.000.000 per un periodo non superiore a 60 mesi.")
    assert ("EUR", 3000000.0, "MAX") in figs("Contributo del 75 per cento e importo massimo di 3 milioni di euro; vincolo di 5 anni.")
    assert ("DURATION", 5, "RIF") in figs("Contributo del 75 per cento e importo massimo di 3 milioni di euro; vincolo di 5 anni.")   # il «massimo» è dell'altra clausola
    assert figs("La domanda va presentata entro il 30 giugno 2026 ai sensi del Regolamento (UE) 1407/2013.") == []


# ------------------------------------------------------------------ ciclo di vita
PAGE = "Stato INCENTIVO Attivo Chiuso In Arrivo Data apertura 12/02/2026 Data chiusura 31/12/2026 Note Le domande"


def test_dates_are_read_from_the_official_page_and_classified():
    assert lifecycle.parse_dates(PAGE) == ("2026-02-12", "2026-12-31")
    assert lifecycle.classify("2026-02-12", "2026-12-31", today="2026-10-03") == "APERTO"
    assert lifecycle.classify("2026-01-14", "2026-02-18", today="2026-10-03") == "CHIUSO"
    assert lifecycle.classify("2027-01-10", "2027-03-01", today="2026-10-03") == "IN_ARRIVO"
    assert lifecycle.classify(None, None, today="2026-10-03") == "SCONOSCIUTO"
    assert lifecycle.parse_dates("Data apertura 31/02/2026") == (None, None)                # data impossibile: non si inventa


def test_scan_stores_the_closing_date_and_cleanup_removes_what_is_closed_or_undated_and_old(monkeypatch):
    today = date.today()
    pages = {
        "https://www.incentivi.gov.it/it/catalogo/chiuso": ("2025-01-10", "2025-02-10"),
        "https://www.incentivi.gov.it/it/catalogo/aperto": ("2026-01-10", (today + timedelta(days=90)).isoformat()),
        "https://www.incentivi.gov.it/it/catalogo/senza-date-vecchio-2024": (None, None),
        "https://www.incentivi.gov.it/it/catalogo/senza-date-attuale": (None, None),
    }
    Ingestion.catalog("CAT-CLOSED-AAA111", "Misura Chiusa", "incentivi.gov.it", None, "https://www.incentivi.gov.it/it/catalogo/chiuso")
    Ingestion.catalog("CAT-OPEN-BBB222", "Misura Aperta", "incentivi.gov.it", None, "https://www.incentivi.gov.it/it/catalogo/aperto")
    Ingestion.catalog("CAT-OLD-CCC333", "Voucher Digitale 2024", "incentivi.gov.it", None, "https://www.incentivi.gov.it/it/catalogo/senza-date-vecchio-2024")
    Ingestion.catalog("CAT-NODATE-DDD444", "Sostegno Alle Imprese", "incentivi.gov.it", None, "https://www.incentivi.gov.it/it/catalogo/senza-date-attuale")
    monkeypatch.setattr(lifecycle, "_read", lambda url: (*pages[url], None))

    report = lifecycle.scan_catalog(limit=50, workers=2, budget_s=10)
    assert report["scanned"] == 4 and report["CHIUSO"] == 1 and report["APERTO"] == 1 and report["SCONOSCIUTO"] == 2
    removed = catalog_job.cleanup_stale(actor="test")["deleted"]
    with connect() as conn:
        left = {r["bando_id"]: r["deadline"] for r in conn.execute("SELECT bando_id, deadline FROM bandi").fetchall()}
    assert removed == 2
    assert "CAT-CLOSED-AAA111" not in left and "CAT-OLD-CCC333" not in left        # chiusa per data; senza date e con solo anni passati nel nome
    assert left["CAT-OPEN-BBB222"] == (today + timedelta(days=90)).isoformat()
    assert left["CAT-NODATE-DDD444"] == "non indicata"                              # nessuna prova che sia chiusa: resta, ma non viene riletta ogni notte


# ------------------------------------------------------------------ pipeline
def long_official_text(n=300):
    return "\n".join(f"Art. {i}. Le spese per consulenze non possono superare il {i % 30 + 1}% del totale delle spese ammissibili del progetto numero {i}." for i in range(n))


def fake_doc(url, text, kind="PDF"):
    return {"url": url, "title": url.rsplit("/", 1)[-1], "text": text, "chars": len(text), "pages": 40, "kind": kind, "content_type": "application/pdf",
            "tier": "UFFICIALE", "size_bytes": len(text), "sha256_raw": "x", "raw": text.encode(), "links": [], "warnings": []}


def test_pipeline_searches_downloads_reads_and_reports_completeness(monkeypatch):
    Ingestion.catalog("CAT-PIPE-EEE555", "Fondo Prova Pipeline", "Ente", None, "https://www.incentivi.gov.it/it/catalogo/fondo-prova")
    url = "https://www.ente.gov.it/avviso/regolamento.pdf"
    def fake_search(name, hint="", supplied=None, discover=None):
        mine = [{"url": u, "title": u, "tier": "UFFICIALE", "score": 1000, "is_pdf": False, "user_supplied": True, "preselected": True} for u in supplied or []]
        return {"candidates": mine + [{"url": url, "title": "Regolamento", "tier": "UFFICIALE", "score": 200, "is_pdf": True, "user_supplied": False, "preselected": True}],
                "engine_errors": []}
    monkeypatch.setattr(research, "search_web", fake_search)
    monkeypatch.setattr(research, "fetch_document", lambda u: fake_doc(u, "Regolamento del Fondo Prova Pipeline.\n" + long_official_text()) if u == url else (_ for _ in ()).throw(research.ResearchError("non raggiungibile")))

    report = pipeline.run("CAT-PIPE-EEE555", actor="test")
    assert report["status"] == "COMPLETA"
    assert report["documents_official"] == 1 and report["official_chars"] >= pipeline.COMPLETE_MIN_OFFICIAL_CHARS
    assert report["requirements"] >= pipeline.COMPLETE_MIN_REQUIREMENTS and report["figures"] > 0
    assert any("non raggiungibile" in g for g in report["gaps"])                    # la fonte catalogo non scaricata è dichiarata, non taciuta
    detail = client.get("/api/v2/bandi/CAT-PIPE-EEE555").json()
    assert any(f["bound"] == "MAX" and f["kind"] == "PERCENT" for r in detail["requirements"] for f in r["figures"])


def test_pipeline_with_nothing_found_is_declared_insufficient_with_the_reason(monkeypatch):
    Ingestion.catalog("CAT-PIPE-FFF666", "Misura Locale Sconosciuta", "Ente", None, None)
    monkeypatch.setattr(research, "search_web", lambda name, hint="", supplied=None, discover=None: {"candidates": [], "engine_errors": ["brave: risposta 429"]})
    report = pipeline.run("CAT-PIPE-FFF666", actor="test")
    assert report["status"] == "INSUFFICIENTE" and report["requirements"] == 0
    assert any("Nessun documento ufficiale" in g for g in report["gaps"])
    assert report["engine_errors"] == ["brave: risposta 429"]


def test_run_endpoint_rejects_unknown_bando():
    assert client.post("/api/v2/bandi/research/run", json={"bando_id": "NON-ESISTE"}).status_code == 404


def test_documents_about_another_bando_are_discarded_and_the_search_limit_does_not_crash_the_run(monkeypatch):
    name = "Investimenti Sostenibili 4.0 — Bando 2026 (PN RIC 2021-2027)"
    assert pipeline.distinctive_tokens(name) == ["investimenti", "sostenibili"]
    assert not pipeline.is_about(name, {"title": "Bando investimenti campagna 2026", "url": "https://regione.sicilia.it/x", "text": "Contributi agricoli per la campagna"})
    assert pipeline.is_about(name, {"title": "FAQ", "url": "https://pnric.gov.it/faq.pdf", "text": "Investimenti sostenibili 4.0: domande frequenti"})

    Ingestion.catalog("CAT-PIPE-GGG777", "Investimenti Sostenibili 4.0", "Ente", None, None)
    good, other = "https://www.pnric.gov.it/faq.pdf", "https://www.regione.sicilia.it/bando-campagna.pdf"
    monkeypatch.setattr(research, "search_web", lambda *a, **k: (_ for _ in ()).throw(research.ResearchError("Troppe richieste di ricerca in poco tempo")))
    texts = {good: long_official_text() + " Investimenti sostenibili 4.0.", other: long_official_text().replace("consulenze", "trattori")}
    monkeypatch.setattr(research, "fetch_document", lambda u: fake_doc(u, texts[u]))
    report = pipeline.run("CAT-PIPE-GGG777", urls=[good], actor="test")                 # la ricerca è limitata ma l'indirizzo già noto viene studiato lo stesso
    assert report["documents_official"] == 1 and "Troppe richieste" in report["engine_errors"][0]
    assert research.normalize_url(other) not in {research.normalize_url(s["url"]) for s in __import__("app.core.events", fromlist=["x"]).list_bando_sources("CAT-PIPE-GGG777")}


def test_a_sibling_bando_of_the_same_issuer_is_not_mistaken_for_this_one():
    from app.core import analysis
    name = "Agevolazioni Servizi Campo Ambientale 2026 Camera Di Commercio Di Torino"
    sibling = {"title": "Voucher transizione ecologica 2024", "url": "https://www.to.camcom.it/bando-transizione-ecologica-2024",
               "text": "La Camera di commercio di Torino concede voucher alle imprese per servizi di consulenza sulla transizione ecologica."}
    own = {"title": "Servizi in campo ambientale", "url": "https://www.to.camcom.it/campo-ambientale",
           "text": "Servizi di analisi in campo ambientale del Laboratorio Chimico della Camera di commercio di Torino."}
    assert not analysis.is_about(name, sibling)
    assert analysis.is_about(name, own)


def test_percentages_with_three_decimals_are_read_whole():
    assert figs("2,75% per gli investimenti ordinari, 3,575% per gli investimenti 4.0") == [("PERCENT", 2.75, "RIF"), ("PERCENT", 3.575, "RIF")]
    assert figs("contributo maggiorato al 3,575% annuo") == [("PERCENT", 3.575, "RIF")]


# ------------------------------------------------------------------ regole numeriche dalle cifre
def test_figure_rules_need_the_cue_words_and_exactly_one_matching_figure():
    from app.core.requirements_extractor import extract_figure_rules as fr
    assert fr("Le spese di installazione, trasporto e collaudo non possono superare il 5% del costo del bene.") == {"max_installation_pct": ["0.05"]}
    assert fr("L'intensità massima comprensiva di tutte le maggiorazioni non può superare l'80%.") == {"max_aid_intensity_pct": ["0.8"]}
    assert fr("La prima tranche, a titolo di anticipo, è pari al 25% dell'agevolazione concessa.") == {"advance_pct": ["0.25"]}
    assert fr("Il saldo del contributo è erogato entro 6 mesi dalla rendicontazione.") == {"reimbursement_lag_months": ["6"]}
    # nessuna parola chiave del contributo: l'acconto dell'impresa al fornitore e le statistiche di una relazione non sono regole
    assert fr("È sufficiente l'emissione di una fattura di acconto di almeno il 20% a favore del fornitore.") == {}
    assert fr("Una parte delle aziende ha dichiarato che a fronte di una maggiore intensità dell'aiuto avrebbe investito di più, per il 33,8%.") == {}
    # due cifre della stessa famiglia nella frase: non si sa a quale riferirsi
    assert fr("L'anticipo del contributo è del 25% oppure del 50% se l'impresa è energivora.") == {}
    # i giorni non si arrotondano a mesi
    assert fr("Il saldo è erogato entro 30 giorni dalla richiesta.") == {}


def test_conflicting_figure_rules_wait_for_review_with_their_candidates():
    Ingestion.catalog("CAT-FIG-JJJ000", "Fondo Cifre Prova", "Ente", None, None)
    text = ("Prima tranche, a titolo di anticipo, pari al 25% dell'agevolazione concessa per le imprese ordinarie. "
            "Prima tranche, a titolo di anticipo, pari al 50% dell'agevolazione concessa per le imprese energivore.")
    out = Ingestion.extract("CAT-FIG-JJJ000", sources=[("Regolamento del Fondo", text)], strict_refs={"Regolamento del Fondo"})
    assert "advance_pct" not in out.published and "advance_pct" in out.pending_review
    ok = Ingestion.extract("CAT-FIG-JJJ000", sources=[("Regolamento del Fondo", text.split(". ")[0] + ".")], strict_refs={"Regolamento del Fondo"})
    assert ok.published.get("advance_pct") == "0.25"
