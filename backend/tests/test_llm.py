"""Modello linguistico: Stadio 3 a passaggi multipli, riepiloghi con validatore numerico, catalogo continuo (Stadio 1).

Le chiamate al provider sono simulate con un trasporto HTTP finto (nessuna rete, nessuna chiave): si prova la nostra logica di
controllo — citazioni verificate, confronto fatto dal codice, validatore numerico — non il modello.
"""
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core import analysis, catalog_job, discovery, events, llm
from app.core.ingestion import Ingestion
from main import app
from tests.conftest import manager_token

client = TestClient(app)

DOC = ("Art. 4 - Contributo. Il contributo a fondo perduto è pari al 65 per cento delle spese ammissibili sostenute dal beneficiario. "
       "Art. 6 - Il beneficiario deve mantenere l'investimento per almeno 36 mesi dalla conclusione del progetto.")


def fake_provider(replies):
    """Trasporto che risponde in ordine con i testi indicati (formato Messages API)."""
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        text = replies[min(len(seen) - 1, len(replies) - 1)]
        return httpx.Response(200, json={"content": [{"type": "text", "text": text}]})
    return httpx.MockTransport(handler), seen


def reply(rules):
    return json.dumps({"rules": rules})


def anthropic(replies):
    transport, seen = fake_provider(replies)
    return llm.AnthropicClient("chiave-di-prova", transport=transport), seen


GOOD = {"key": "contribution_rate_pct", "value": "65%", "quote": "Il contributo a fondo perduto è pari al 65 per cento delle spese ammissibili"}


def test_no_key_means_no_model_and_nothing_is_called(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("QUANTO_LLM_API_KEY", raising=False)
    assert llm.get_client() is None
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    assert llm.get_client().model == llm.DEFAULT_MODEL
    monkeypatch.setenv("QUANTO_LLM_PROVIDER", "altro")
    with pytest.raises(llm.LLMError):
        llm.get_client()


def test_client_sends_the_messages_api_request_and_reads_text():
    c, seen = anthropic(["ciao"])
    assert c.complete("sistema", "{}") == "ciao"
    assert seen[0]["model"] == llm.DEFAULT_MODEL and seen[0]["system"] == "sistema" and seen[0]["messages"][0]["role"] == "user"
    bad = llm.AnthropicClient("k", transport=httpx.MockTransport(lambda r: httpx.Response(529)))
    with pytest.raises(llm.LLMError):
        bad.complete("s", "{}")


def test_a_value_whose_quote_is_not_in_the_text_is_discarded_and_values_are_normalized():
    invented = {"key": "max_consulting_percentage", "value": "20%", "quote": "Le consulenze non possono superare il 20% del progetto complessivo"}
    c, _ = anthropic([reply([GOOD, invented, {"key": "chiave_inventata", "value": "1", "quote": "Il beneficiario deve mantenere l'investimento per almeno"}])])
    out = llm.extract_pass(c, DOC)
    assert out == {"contribution_rate_pct": "0.65"}                         # citazione inventata e chiave sconosciuta: scartate; 65% → 0.65


def test_garbage_replies_give_no_rules():
    c, _ = anthropic(["non è JSON", reply("non è una lista"), "{}"])
    assert llm.extract_pass(c, DOC) == {} and llm.extract_pass(c, DOC) == {} and llm.extract_pass(c, DOC) == {}


def test_agreeing_passes_publish_and_disagreeing_ones_go_to_human_review():
    Ingestion.catalog("B-AI", "Bando AI", None, None, None)
    other = {**GOOD, "value": "60%", "quote": "Il contributo a fondo perduto è pari al 65 per cento delle spese ammissibili"}
    c, _ = anthropic([reply([GOOD]), reply([GOOD]), reply([other])])
    passes = llm.extract_passes(c, DOC, n=3)
    out = Ingestion.extract("B-AI", ai_passes=passes)
    assert "contribution_rate_pct" in out.pending_review and not out.published            # 0.65, 0.65, 0.60: disaccordo → coda del consulente
    Ingestion.catalog("B-AI2", "Bando AI 2", None, None, None)
    c2, _ = anthropic([reply([GOOD])])
    out2 = Ingestion.extract("B-AI2", ai_passes=llm.extract_passes(c2, DOC, n=3))
    assert out2.published == {"contribution_rate_pct": "0.65"}                            # 3 letture uguali → pubblicata, origine tracciata
    with_origin = Ingestion.status("B-AI2")
    assert with_origin["rules_from_multi_pass_ai"] == 1 and with_origin["rules_with_pass_agreement"] == 1


def test_a_rule_missing_from_one_pass_is_not_published():
    Ingestion.catalog("B-AI3", "Bando AI 3", None, None, None)
    c, _ = anthropic([reply([GOOD]), reply([]), reply([GOOD])])
    out = Ingestion.extract("B-AI3", ai_passes=llm.extract_passes(c, DOC, n=3))
    assert "contribution_rate_pct" in out.pending_review and not out.published


def test_analysis_uses_the_model_only_when_configured_and_never_overwrites_deterministic_rules(monkeypatch):
    Ingestion.catalog("B-AN", "Bando Analisi", None, None, None)
    events.save_bando_source("B-AN", "avviso", DOC + " Il CUP deve essere riportato su tutte le fatture.", url="https://x.gov.it/a", tier="UFFICIALE")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("QUANTO_LLM_API_KEY", raising=False)
    res = analysis.run_analysis("B-AN")
    assert "requires_cup" in res["outcome"].published                                     # senza modello: solo lettura deterministica
    c, seen = anthropic([reply([GOOD])])
    monkeypatch.setattr(llm, "get_client", lambda: c)
    res2 = analysis.run_analysis("B-AN")
    assert len(seen) == llm.passes_wanted()                                              # N letture indipendenti
    st = Ingestion.status("B-AN")
    assert st["rules_from_structured_parsing"] >= 1                                       # le regole deterministiche restano dov'erano


def test_budget_summary_from_the_model_is_accepted_only_if_every_number_matches(monkeypatch):
    from app.core.renderer import budget_context, render_with_grounding, static_budget_summary
    ctx = {"bando_id": "B", "bando_name": "Bando", "items_total": 3, "items_adjusted": 1, "items_blocked": 0, "total_requested_eur": 1000.0, "total_approved_eur": 900.0,
           "total_reduced_eur": 100.0, "conformity_score": 90, "merkle_root": "0x" + "ab" * 32}
    static = static_budget_summary(ctx)
    honest, _ = anthropic(["Ammessi 900,00 € su 1.000,00 € richiesti; punteggio 90."])
    assert render_with_grounding(ctx, static, honest)[1] == "LLM"
    liar, _ = anthropic(["Ammessi 950,00 € su 1.000,00 € richiesti."])
    assert render_with_grounding(ctx, static, liar) == (static, "TEMPLATE")             # cifra alterata: testo scartato


def test_allocation_summary_is_grounded_too(monkeypatch):
    c, _ = anthropic(["Il piano copre 999.999,00 € delle spese."])                      # cifra che non esiste nel piano
    monkeypatch.setattr(llm, "get_client", lambda: c)
    body = {"fiscal_year": 2027, "historical_expenses": [{"item_id": "E1", "category": "PERSONNEL", "amount_eur": 10000}],
            "available_funding_lines": [{"fund_id": "F1", "allowed_categories": ["PERSONNEL"], "coverage_pct": 0.5}]}
    r = client.post("/api/v2/allocation/optimize", json=body).json()
    assert r["summary_source"] == "TEMPLATE" and "999.999" not in r["summary"]


# ------------------------------------------------------------------ Stadio 1: catalogo continuo
def test_catalog_refresh_lists_entries_as_metadata_only_and_they_become_searchable(monkeypatch):
    monkeypatch.setattr(discovery, "load_catalog", lambda cat, force=False: [(f"{cat['site']}{cat['path']}fondo-per-le-imprese-culturali", "fondo per le imprese culturali")])
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("QUANTO_LLM_API_KEY", raising=False)
    rep = catalog_job.refresh()
    assert rep["inserted"] == 2 and rep["enriched"] == 0
    assert catalog_job.refresh()["inserted"] == 0                                        # una seconda volta non duplica
    m = client.get("/api/v2/bandi/search", params={"q": "imprese culturali"}).json()["matches"]
    assert m and m[0]["catalog_only"] is True and m[0]["rules"] == 0 and m[0]["source_url"].startswith("https://www.")
    assert "CAT-" not in str([b["bando_id"] for b in client.get("/api/v2/bandi").json()])   # non intasa l'elenco pubblico dei bandi lavorati


def test_catalog_enrichment_accepts_metadata_only_with_a_real_quote(monkeypatch):
    page = "Fondo Cultura 2026. Ente erogatore: Ministero della Cultura. Le domande si presentano entro il 30/09/2026."
    monkeypatch.setattr(discovery, "load_catalog", lambda cat, force=False: [(f"{cat['site']}{cat['path']}fondo-cultura", "fondo cultura")] if cat["name"] == "incentivi.gov.it" else [])
    monkeypatch.setattr(catalog_job.research, "fetch_document", lambda url: {"text": page})
    good = json.dumps({"name": "Fondo Cultura 2026", "issuer": "Ministero della Cultura", "quote_issuer": "Ente erogatore: Ministero della Cultura",
                       "deadline": "2026-09-30", "quote_deadline": "entro il 30/09/2026"})
    c, _ = anthropic([good])
    monkeypatch.setattr(llm, "get_client", lambda: c)
    rep = catalog_job.refresh()
    assert rep["enriched"] == 1
    row = client.get("/api/v2/bandi/search", params={"q": "fondo cultura"}).json()["matches"][0]
    assert row["issuer"] == "Ministero della Cultura" and row["deadline"] == "2026-09-30"


def test_cron_endpoint_needs_the_cron_secret_or_a_manager(monkeypatch):
    monkeypatch.setattr(discovery, "load_catalog", lambda cat, force=False: [])
    monkeypatch.setenv("CRON_SECRET", "segreto-del-cron-lungo")
    assert client.get("/api/v2/cron/catalog-refresh").status_code == 401
    assert client.get("/api/v2/cron/catalog-refresh", headers={"Authorization": "Bearer sbagliato"}).status_code == 401
    assert client.get("/api/v2/cron/catalog-refresh", headers={"Authorization": "Bearer segreto-del-cron-lungo"}).status_code == 200      # come lo chiama Vercel
    assert client.post("/api/v2/cron/catalog-refresh", headers={"Authorization": f"Bearer {manager_token()}"}).status_code == 200
