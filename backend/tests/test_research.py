"""Ricerca web dei bandi: classificazione, protezioni, estrazione del testo, coda dei link e flusso completo (rete simulata)."""
import base64
import io
import zipfile

import httpx
import pytest
from fastapi.testclient import TestClient
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.core import events, research
from main import app

client = TestClient(app)
NAME = "Fondo Test Giovani"

HTML_MAIN = """<html><head><title>Sito ente</title></head><body>
<nav><a href="/menu">Menu principale</a></nav>
<div>Questo sito utilizza cookie tecnici. Cliccando Accetta acconsenti all'uso dei cookie.</div>
<form id="aspnetForm"><h1>Fondo Test Giovani</h1>
<p>Il contributo a fondo perduto è pari al 60% delle spese ammissibili fino a 100.000 euro per ogni progetto presentato.</p>
<p>Le consulenze esterne non possono superare il 15% del totale del progetto approvato dall'ente.</p>
<p>Possono presentare domanda i giovani di età compresa tra 18 e 35 anni residenti in Puglia o in Basilicata.</p>
<p>Il costo orario del personale non può essere superiore a 40,00 euro/ora per tutte le figure professionali.</p>
<a href="/files/avviso-pubblico.pdf">Avviso pubblico</a>
<a href="https://www.gazzettaufficiale.it/eli/id/2024/07/06/24A03521/sg">Decreto Legge n.60 del 07/05/2024</a>
<a href="https://blog.example.com/guida.pdf">Guida di un blog</a>
<a href="/contatti">Contatti</a><a href="mailto:a@b.it">mail</a></form></body></html>"""


def make_pdf(lines):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y = 800
    for ln in lines:
        c.drawString(40, y, ln)
        y -= 18
    c.save()
    return buf.getvalue()


PDF = make_pdf([
    "Avviso pubblico Fondo Test Giovani - articolo 5",
    "Il CUP deve essere riportato su tutti i documenti di spesa del progetto finanziato.",
    "Le spese di comunicazione non possono superare il 3% del totale delle spese ammissibili.",
    "Il costo orario del personale non può essere superiore a 35,00 euro/ora secondo l'avviso.",
    "Decreto Ministeriale n. 55 del 11/07/2025 e Legge n. 95 del 04/07/2024.",
])


@pytest.fixture
def web(monkeypatch):
    """Rete simulata: indirizzo -> (contenuto, content-type)."""
    pages = {
        "https://www.ente.gov.it/fondo": (HTML_MAIN.encode(), "text/html"),
        "https://www.ente.gov.it/files/avviso-pubblico.pdf": (PDF, "application/pdf"),
        "https://www.gazzettaufficiale.it/eli/id/2024/07/06/24A03521/sg": (b"<html><body><h1>Decreto</h1><p>Le domande devono essere presentate entro il 30 giugno.</p></body></html>", "text/html"),
        "https://blog.example.com/guida": (b"<html><body><p>" + b"Guida non ufficiale al Fondo Test Giovani. " * 10 + b"</p></body></html>", "text/html"),
    }

    def fake_get(url, max_bytes=research.MAX_BINARY_BYTES):
        if url not in pages:
            raise research.ResearchError("Il sito ha risposto 404")
        data, ctype = pages[url]
        return data, url, ctype

    def fake_search(query):
        return [
            {"url": "https://www.ente.gov.it/fondo", "title": "Fondo Test Giovani - Ente", "snippet": "bando"},
            {"url": "https://blog.example.com/guida", "title": "Guida al Fondo Test Giovani", "snippet": ""},
            {"url": "https://www.ilrestodelcarlino.it/", "title": "Il Resto del Carlino", "snippet": "notizie"},
        ], None

    monkeypatch.setattr(research, "http_get", fake_get)
    monkeypatch.setattr(research, "_search_one", fake_search)
    return pages


# ------------------------------------------------------------------ classificazione e ranking
def test_classify_and_normalize():
    assert research.classify_url("https://www.invitalia.it/incentivi/resto-al-sud") == "UFFICIALE"
    assert research.classify_url("https://www.gazzettaufficiale.it/eli/id/2024/x") == "UFFICIALE"
    assert research.classify_url("https://eur-lex.europa.eu/legal-content/IT/TXT/") == "UFFICIALE"
    assert research.classify_url("https://lavoro.regione.campania.it/x") == "UFFICIALE"
    assert research.classify_url("https://www.business-plan.it/blog/resto-al-sud") == "SECONDARIA"
    assert research.classify_url("https://fake-gov.it.evil.com/x") == "SECONDARIA"      # non basta contenere "gov.it"
    assert research.normalize_url("https://WWW.Sito.it/a/b/?utm_source=x&id=3#top") == "https://sito.it/a/b?id=3"


def test_rank_drops_noise_and_preselects_official():
    raw = [
        {"url": "https://www.invitalia.it/incentivi-e-strumenti/resto-al-sud", "title": "Resto al Sud - Invitalia", "snippet": ""},
        {"url": "https://www.ilrestodelcarlino.it/", "title": "Il Resto del Carlino", "snippet": ""},
        {"url": "https://www.business-plan.it/resto-al-sud", "title": "Resto al Sud guida", "snippet": ""},
    ]
    out = research.rank_results("Resto al Sud", raw, supplied=["https://www.mimit.gov.it/atto.pdf"])
    urls = [c["url"] for c in out]
    assert not any("carlino" in u for u in urls)
    assert out[0]["user_supplied"] and out[0]["preselected"]
    inv = next(c for c in out if "invitalia" in c["url"])
    blog = next(c for c in out if "business-plan" in c["url"])
    assert inv["preselected"] and inv["tier"] == "UFFICIALE" and not blog["preselected"] and inv["score"] > blog["score"]


def test_parse_bing_decodes_redirects():
    target = "https://www.invitalia.it/x"
    u = "a1" + base64.urlsafe_b64encode(target.encode()).decode().rstrip("=")
    html = f'<ol><li class="b_algo"><h2><a href="https://www.bing.com/ck/a?!&amp;u={u}&amp;ntb=1">Titolo &amp; test</a></h2><p>Descrizione</p></li></ol>'
    hits = research.parse_bing(html)
    assert hits == [{"url": target, "title": "Titolo & test", "snippet": "Descrizione"}]


# ------------------------------------------------------------------ protezioni
@pytest.mark.parametrize("url", ["http://127.0.0.1/", "http://localhost/admin", "http://169.254.169.254/latest/meta-data", "http://10.0.0.5/x", "http://[::1]/",
                                 "ftp://example.org/x", "http://8.8.8.8:8080/", "http://user:pw@8.8.8.8/", "file:///etc/passwd"])
def test_internal_or_odd_addresses_are_refused(url):
    with pytest.raises(research.ResearchError):
        research.check_public_url(url)


def test_public_address_is_accepted():
    research.check_public_url("https://8.8.8.8/")


def test_redirect_to_internal_address_is_blocked(monkeypatch):
    def handler(request):
        return httpx.Response(302, headers={"location": "http://127.0.0.1/segreto"})

    real = httpx.Client
    monkeypatch.setattr(research.httpx, "Client", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))
    with pytest.raises(research.ResearchError, match="rete interna"):
        research.http_get("https://8.8.8.8/")


def test_size_and_status_limits(monkeypatch):
    real = httpx.Client
    state = {}

    def handler(request):
        return state["resp"]

    monkeypatch.setattr(research.httpx, "Client", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))
    state["resp"] = httpx.Response(404)
    with pytest.raises(research.ResearchError, match="404"):
        research.http_get("https://8.8.8.8/x")
    state["resp"] = httpx.Response(200, headers={"content-type": "application/pdf", "content-length": str(50_000_000)}, content=b"%PDF")
    with pytest.raises(research.ResearchError, match="troppo grande"):
        research.http_get("https://8.8.8.8/x")
    state["resp"] = httpx.Response(200, headers={"content-type": "text/html"}, content=b"x" * (research.MAX_HTML_BYTES + 10))
    with pytest.raises(research.ResearchError, match="troppo grande"):
        research.http_get("https://8.8.8.8/x")


def test_rate_limit(monkeypatch):
    monkeypatch.setattr(research, "RATE_LIMIT", (2, 600))
    research._HITS.clear()
    research._rate_check(); research._rate_check()
    with pytest.raises(research.ResearchError, match="Troppe richieste"):
        research._rate_check()
    research._HITS.clear()


# ------------------------------------------------------------------ estrazione del testo
def test_html_to_text_removes_noise_and_keeps_form_wrapped_content():
    text, title, links = research.html_to_text(HTML_MAIN)
    assert title == "Fondo Test Giovani"
    assert "contributo a fondo perduto" in text and "18 e 35 anni" in text          # contenuto dentro <form> conservato
    assert "cookie" not in text.lower() and "Menu principale" not in text          # avviso cookie e menu tolti
    assert ("/files/avviso-pubblico.pdf", "Avviso pubblico") in links


def test_unclosed_head_does_not_swallow_page():
    text, _, _ = research.html_to_text("<html><head><title>T</title><body><p>Testo del bando che deve restare leggibile nella pagina.</p></body></html>")
    assert "deve restare leggibile" in text


def test_focus_text_keeps_only_passages_about_the_bando():
    filler = "Disposizioni generali sulla contabilità dello Stato. " * 2000
    long_doc = filler + " Il fondo Resto al Sud finanzia i giovani fino a 35 anni. " + filler
    focused = research.focus_text(long_doc, "Resto al Sud 2.0")
    assert "Resto al Sud" in focused and len(focused) < len(long_doc) / 5
    assert research.focus_text(filler + filler, "Resto al Sud") == ""                 # lungo e mai nominato: non pertinente
    assert research.focus_text("breve testo", "Resto al Sud") == "breve testo"        # breve: intero


def test_find_links_prioritises_documents_and_official_hosts():
    _, _, links = research.html_to_text(HTML_MAIN)
    found = research.find_links("https://www.ente.gov.it/fondo", links)
    urls = [x["url"] for x in found]
    assert urls[0].endswith("avviso-pubblico.pdf") or "gazzettaufficiale" in urls[0]
    assert "https://www.ente.gov.it/files/avviso-pubblico.pdf" in urls
    assert any("gazzettaufficiale" in u for u in urls)
    assert not any("blog.example.com" in u or "contatti" in u or u.startswith("mailto") for u in urls)   # blog e pagine di servizio esclusi
    known = {research.normalize_url("https://www.ente.gov.it/files/avviso-pubblico.pdf")}
    assert "https://www.ente.gov.it/files/avviso-pubblico.pdf" not in [x["url"] for x in research.find_links("https://www.ente.gov.it/fondo", links, known)]


def test_pdf_and_docx_and_errors(monkeypatch):
    text, pages, read = research.pdf_to_text(PDF)
    assert pages == read == 1 and "CUP" in text
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", "<w:document><w:p><w:t>Le consulenze non possono superare il 10%.</w:t></w:p></w:document>")
    assert "consulenze" in research.docx_to_text(buf.getvalue())

    def fake_get(url, max_bytes=0):
        d, c = {"https://a": (b"\x89PNG....", "image/png"), "https://b": (b"<html><body>x</body></html>", "text/html")}[url]
        return d, url, c

    monkeypatch.setattr(research, "http_get", fake_get)
    with pytest.raises(research.ResearchError, match="non supportato"):
        research.fetch_document("https://a")
    with pytest.raises(research.ResearchError, match="Nessun testo"):
        research.fetch_document("https://b")


def test_scanned_pdf_is_flagged(monkeypatch):
    blank = make_pdf([])
    monkeypatch.setattr(research, "http_get", lambda url, max_bytes=0: (blank, url, "application/pdf"))
    with pytest.raises(research.ResearchError):      # nessun testo: errore chiaro invece di un documento vuoto in memoria
        research.fetch_document("https://x.gov.it/scan.pdf")


# ------------------------------------------------------------------ flusso completo
def test_full_research_flow(web):
    s = client.post("/api/v2/bandi/research/search", json={"name": NAME}).json()
    bid = s["bando_id"]
    assert bid == "WEB-FONDO-TEST-GIOVANI"
    urls = [c["url"] for c in s["candidates"]]
    assert "https://www.ente.gov.it/fondo" in urls and not any("carlino" in u for u in urls)
    assert next(c for c in s["candidates"] if "ente.gov.it" in c["url"])["preselected"]
    assert not next(c for c in s["candidates"] if "blog" in c["url"])["preselected"]

    f = client.post("/api/v2/bandi/research/fetch", json={"bando_id": bid, "url": "https://www.ente.gov.it/fondo"}).json()
    assert f["source"]["kind"] == "HTML" and f["source"]["tier"] == "UFFICIALE" and f["source"]["chars"] > 300
    link_urls = [x["url"] for x in f["links"]]
    pdf_url = "https://www.ente.gov.it/files/avviso-pubblico.pdf"
    assert pdf_url in link_urls
    p = client.post("/api/v2/bandi/research/fetch", json={"bando_id": bid, "url": pdf_url}).json()
    assert p["source"]["kind"] == "PDF" and p["source"]["pages"] == 1

    a = client.post("/api/v2/bandi/research/analyze", json={"bando_id": bid}).json()
    assert a["sources"] == 2 and a["requirements_total"] >= 6
    topics = " ".join(a["topics"])
    assert "Agevolazione" in topics and "Età" in topics and "CUP" in topics
    # regole lette dal testo: il tetto orario è in DISACCORDO tra pagina (40) e PDF (35) -> non diventa un controllo, va a verifica manuale
    assert "max_hourly_rate_personnel" not in a["rules_published"]
    assert any(q["rule_key"] == "max_hourly_rate_personnel" for q in client.get("/api/v2/ingestion/review-queue").json())
    assert a["rules_published"].get("max_consulting_percentage") == "0.15"
    assert a["rules_published"].get("max_communication_pct") == "0.03"
    assert any("Decreto Ministeriale n. 55 del 11/07/2025" == r for r in a["legal_refs"])

    d = client.get(f"/api/v2/bandi/{bid}").json()
    origins = {s["origin"] for s in d["usage"]["uploaded_sources"]}
    assert origins == {"WEB"} and all(s["url"] for s in d["usage"]["uploaded_sources"])
    assert d["usage"]["uploaded_sources"][0]["tier"] == "UFFICIALE"
    assert all("text" not in s for s in d["usage"]["uploaded_sources"])     # l'elenco non porta il testo intero
    assert any(r["source_ref"] and "avviso-pubblico.pdf" in r["source_ref"] for r in d["requirements"])   # ogni requisito cita la sua fonte

    sha = d["usage"]["uploaded_sources"][0]["sha256"]
    t = client.get(f"/api/v2/bandi/{bid}/sources/{sha}").json()
    assert t["chars"] == len(t["text"]) and t["url"]
    assert client.get(f"/api/v2/bandi/{bid}/sources/{'0' * 64}").status_code == 404

    ev = [e["op"] for e in events.list_events(bando_id=bid, limit=50)]
    assert {"bando.research.search", "bando.research.fetch", "bando.research.analyze"} <= set(ev)


def test_manual_upload_adds_to_web_sources_without_losing_requirements(web):
    bid = client.post("/api/v2/bandi/research/search", json={"name": NAME}).json()["bando_id"]
    client.post("/api/v2/bandi/research/fetch", json={"bando_id": bid, "url": "https://www.ente.gov.it/fondo"})
    n1 = client.post("/api/v2/bandi/research/analyze", json={"bando_id": bid}).json()["requirements_total"]
    text = "Le spese di formazione non possono superare il 7% del totale del progetto. " * 3 + "Il beneficiario deve conservare la documentazione per cinque anni."
    r = client.post("/api/v2/bandi/upload", json={"name": NAME, "bando_id": bid, "text": text * 2, "filename": "integrazione.txt"}).json()
    assert r["requirements_total"] >= n1                      # prima l'upload cancellava i requisiti letti dalle altre fonti
    assert len(r["detail"]["usage"]["uploaded_sources"]) == 2


def test_fetch_failures_and_unknown_bando(web):
    assert client.post("/api/v2/bandi/research/fetch", json={"bando_id": "WEB-NON-ESISTE", "url": "https://www.ente.gov.it/fondo"}).status_code == 404
    bid = client.post("/api/v2/bandi/research/search", json={"name": NAME}).json()["bando_id"]
    r = client.post("/api/v2/bandi/research/fetch", json={"bando_id": bid, "url": "https://www.ente.gov.it/non-esiste"})
    assert r.status_code == 422 and "404" in r.json()["detail"]
    assert client.post("/api/v2/bandi/research/fetch", json={"bando_id": bid, "url": "http://127.0.0.1/x"}).status_code == 422
    assert client.post("/api/v2/bandi/research/analyze", json={"bando_id": bid}).status_code == 409        # nulla in memoria
    warn = [e for e in events.list_events(bando_id=bid, limit=20) if e["op"] == "bando.research.fetch"]
    assert warn and all(e["status"] == "WARN" for e in warn)


def test_search_without_results_and_supplied_urls(monkeypatch):
    monkeypatch.setattr(research, "_search_one", lambda q: ([], "Bing non ha restituito risultati leggibili"))
    r = client.post("/api/v2/bandi/research/search", json={"name": "Bando Inesistente Xyz", "urls": ["https://www.mimit.gov.it/it/atto.pdf"]}).json()
    assert len(r["candidates"]) == 1                              # con un link indicato dall'utente si può comunque procedere
    assert r["candidates"][0]["user_supplied"] and r["candidates"][0]["preselected"] and r["candidates"][0]["tier"] == "UFFICIALE"
    r2 = client.post("/api/v2/bandi/research/search", json={"name": "Bando Inesistente Xyz"}).json()
    assert r2["candidates"] == [] and r2["engine_errors"]        # l'errore del motore è visibile, non nascosto


def test_research_endpoints_require_auth_when_enabled(web, monkeypatch):
    monkeypatch.setenv("QUANTO_AUTH_REQUIRED", "1")
    assert client.post("/api/v2/bandi/research/search", json={"name": NAME}).status_code in (401, 503)
    assert client.post("/api/v2/bandi/research/fetch", json={"bando_id": "WEB-X", "url": "https://a.gov.it/x"}).status_code in (401, 503)


def test_web_bando_without_numeric_rules_can_still_be_used(web, monkeypatch):
    monkeypatch.setitem(web, "https://www.ente.gov.it/fondo", (b"<html><body><h1>Bando Solo Testo</h1><p>" + b"Il bando sostiene la nascita di nuove imprese giovanili nel territorio regionale con un percorso di accompagnamento. " * 6 + b"</p></body></html>", "text/html"))
    bid = client.post("/api/v2/bandi/research/search", json={"name": NAME}).json()["bando_id"]
    client.post("/api/v2/bandi/research/fetch", json={"bando_id": bid, "url": "https://www.ente.gov.it/fondo"})
    a = client.post("/api/v2/bandi/research/analyze", json={"bando_id": bid}).json()
    assert a["rules_published"] == {}
    assert a["detail"]["grant_rules"] and a["detail"]["grant_rules"]["max_hourly_rate_personnel"] is None      # nessun default inventato
    assert client.post(f"/api/v2/bandi/{bid}/select").status_code == 200


def test_ambiguous_rule_inside_one_document_goes_to_manual_review(monkeypatch):
    page = ("<html><body><h1>Fondo Test Giovani</h1><p>Il contributo è pari al 75% a fondo perduto per programmi di investimento fino a 120.000 euro.</p>"
            "<p>Il contributo è pari al 70% a fondo perduto per programmi di investimento tra 120.000 e 200.000 euro.</p>"
            "<p>Le consulenze esterne non possono superare il 15% del totale del progetto approvato dall'ente.</p></body></html>").encode()
    monkeypatch.setattr(research, "_search_one", lambda q: ([{"url": "https://www.ente.gov.it/f", "title": "Fondo Test Giovani", "snippet": ""}], None))
    monkeypatch.setattr(research, "http_get", lambda url, max_bytes=0: (page, url, "text/html"))
    bid = client.post("/api/v2/bandi/research/search", json={"name": NAME}).json()["bando_id"]
    client.post("/api/v2/bandi/research/fetch", json={"bando_id": bid, "url": "https://www.ente.gov.it/f"})
    a = client.post("/api/v2/bandi/research/analyze", json={"bando_id": bid}).json()
    assert "contribution_rate_pct" not in a["rules_published"]                       # 75% e 70%: non si sceglie a caso
    assert a["rules_published"]["max_consulting_percentage"] == "0.15"               # il valore univoco si pubblica
    rule = next(r for r in a["detail"]["rules"] if r["key"] == "contribution_rate_pct")
    assert rule["status"] == "PENDING_REVIEW" and set(rule["passes"]) == {"0.75", "0.7"}
    # una persona decide: solo allora diventa un controllo attivo
    assert client.post("/api/v2/ingestion/review", json={"bando_id": bid, "rule_key": "contribution_rate_pct", "value": "0.75"}).status_code == 200
    d = client.get(f"/api/v2/bandi/{bid}").json()
    assert next(r for r in d["rules"] if r["key"] == "contribution_rate_pct")["status"] == "PUBLISHED"


def test_reanalysis_recomputes_parsed_rules_but_keeps_human_decisions(monkeypatch):
    text1 = "<html><body><h1>Fondo Test Giovani</h1><p>Il contributo è pari al 60% delle spese ammissibili per ogni progetto presentato all'ente.</p><p>Le consulenze esterne non possono superare il 15% del totale del progetto approvato.</p></body></html>"
    text2 = "<html><body><h1>Fondo Test Giovani</h1><p>Il contributo è pari al 45% delle spese ammissibili per ogni progetto presentato all'ente.</p><p>Il costo orario del personale non può essere superiore a 40,00 euro/ora per tutte le figure.</p></body></html>"
    page = {"cur": text1}
    monkeypatch.setattr(research, "_search_one", lambda q: ([{"url": "https://www.ente.gov.it/a", "title": "Fondo Test Giovani", "snippet": ""}], None))
    monkeypatch.setattr(research, "http_get", lambda url, max_bytes=0: (page["cur"].encode(), url, "text/html"))
    bid = client.post("/api/v2/bandi/research/search", json={"name": NAME}).json()["bando_id"]
    client.post("/api/v2/bandi/research/fetch", json={"bando_id": bid, "url": "https://www.ente.gov.it/a"})
    a1 = client.post("/api/v2/bandi/research/analyze", json={"bando_id": bid}).json()
    assert a1["rules_published"] == {"contribution_rate_pct": "0.6", "max_consulting_percentage": "0.15"}
    # una persona corregge il contributo
    client.post("/api/v2/ingestion/review", json={"bando_id": bid, "rule_key": "contribution_rate_pct", "value": "0.5"})
    # nuovo documento con altre cifre: i parser rifanno le regole, la decisione umana resta
    page["cur"] = text2
    client.post("/api/v2/bandi/research/fetch", json={"bando_id": bid, "url": "https://www.ente.gov.it/b"})
    a2 = client.post("/api/v2/bandi/research/analyze", json={"bando_id": bid}).json()
    rules = {r["key"]: r for r in a2["detail"]["rules"]}
    assert rules["contribution_rate_pct"]["value"] == 0.5 and rules["contribution_rate_pct"]["origin"] == "HUMAN_REVIEW"
    assert rules["max_hourly_rate_personnel"]["value"] == 40
    assert rules["max_consulting_percentage"]["value"] == 0.15            # ancora presente nella prima fonte
