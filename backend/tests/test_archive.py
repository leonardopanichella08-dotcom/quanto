"""Archivio bandi del Quartier Generale, scheda consulente e lettura dei documenti (italiano/inglese, documenti «vuoti»)."""
import io
import zipfile

import pytest
from fastapi.testclient import TestClient
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.core import bandi, research
from main import app

from tests.conftest import manager_token  # noqa: E402

client = TestClient(app)
NAME = "Fondo Archivio Prova"


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
    "Avviso pubblico Fondo Archivio Prova - articolo 5",
    "Le consulenze esterne non possono superare il 15% del totale del progetto approvato dall'ente.",
    "Il costo orario del personale non può essere superiore a 35,00 euro/ora secondo l'avviso.",
    "Il CUP deve essere riportato su tutti i documenti di spesa del progetto finanziato.",
    "Le spese sono ammissibili a partire dal 01/01/2026 secondo quanto previsto dall'avviso.",
])
HTML = (b"<html><body><h1>Fondo Archivio Prova</h1><p>Il costo orario del personale non pu\xc3\xb2 essere superiore a 40,00 euro/ora per tutte le figure professionali.</p>"
        b"<p>Possono presentare domanda i giovani di et\xc3\xa0 compresa tra 18 e 35 anni residenti in Puglia o in Basilicata per progetti presentati all'ente.</p>"
        b"<p>Il subappalto non \xc3\xa8 ammesso per nessuna attivit\xc3\xa0 prevista dal progetto finanziato dall'ente.</p></body></html>")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def deny(url, *a, **k):
        raise research.ResearchError("rete disattivata nei test")

    monkeypatch.setattr(research, "http_get", deny)
    monkeypatch.setattr(research, "_search_one", lambda q, *a, **k: ([], "test"))


@pytest.fixture
def hq():
    return {"X-HQ-Token": manager_token()}


@pytest.fixture
def bando(monkeypatch, hq):
    """Un bando letto dal web con un PDF e una pagina."""
    pages = {"https://www.ente.gov.it/avviso.pdf": (PDF, "application/pdf"), "https://www.ente.gov.it/fondo": (HTML, "text/html")}
    def fake_get(url, max_bytes=0, **kw):
        if url not in pages:
            raise research.ResearchError("Il sito ha risposto 404")
        return pages[url][0], url, pages[url][1]

    monkeypatch.setattr(research, "http_get", fake_get)
    bid = client.post("/api/v2/bandi/research/search", json={"name": NAME}).json()["bando_id"]
    client.post("/api/v2/bandi/research/confirm", json={"name": NAME})
    for u in pages:
        assert client.post("/api/v2/bandi/research/fetch", json={"bando_id": bid, "url": u}).status_code == 200
    a = client.post("/api/v2/bandi/research/analyze", json={"bando_id": bid}).json()
    return {"id": bid, "analyze": a, "pdf_sha": research.hashlib.sha256(PDF).hexdigest()}


def test_archive_requires_manager_code():
    for path in ("/archive", "/archive/X", "/archive/X/consultant", "/db/table/events/export.csv"):
        assert client.get(f"/api/v2/hq{path}").status_code == 401
    assert client.delete("/api/v2/hq/archive/X").status_code == 401
    assert client.put("/api/v2/hq/archive/X/rules/max_hourly_rate_personnel", json={"value": 30}).status_code == 401


def test_list_and_detail_show_sources_files_and_analysis(bando, hq):
    lst = client.get("/api/v2/hq/archive", headers=hq).json()
    row = next(b for b in lst["bandi"] if b["bando_id"] == bando["id"])
    assert row["sources"] == 2 and row["files"] == 2 and row["origin"] == "web" and row["requirements"] >= 4 and row["files_bytes"] > 1000
    d = client.get(f"/api/v2/hq/archive/{bando['id']}", headers=hq).json()
    pdf = next(s for s in d["sources_detail"] if s["name"].endswith("avviso.pdf"))
    assert pdf["file"]["size_bytes"] == len(PDF) and pdf["analysis"]["requirements"] >= 2 and pdf["analysis"]["note"] == "" and pdf["url"].endswith("avviso.pdf")
    assert "text" not in pdf                                                            # l'elenco non porta il testo intero


def test_original_file_can_be_opened_and_downloaded(bando, hq):
    d = client.get(f"/api/v2/hq/archive/{bando['id']}", headers=hq).json()
    pdf = next(s for s in d["sources_detail"] if s["name"].endswith("avviso.pdf"))
    r = client.get(f"/api/v2/hq/archive/{bando['id']}/sources/{pdf['sha256']}/file", headers=hq)
    assert r.status_code == 200 and r.content == PDF and r.headers["content-type"] == "application/pdf"
    assert r.headers["content-disposition"].startswith("inline") and r.headers["x-content-type-options"] == "nosniff"
    assert client.get(f"/api/v2/hq/archive/{bando['id']}/sources/{pdf['sha256']}/file?download=true", headers=hq).headers["content-disposition"].startswith("attachment")
    html = next(s for s in d["sources_detail"] if s["url"].endswith("/fondo"))
    h = client.get(f"/api/v2/hq/archive/{bando['id']}/sources/{html['sha256']}/file", headers=hq)
    assert h.headers["content-type"].startswith("text/plain")                           # una pagina scaricata non viene eseguita nel browser
    t = client.get(f"/api/v2/hq/archive/{bando['id']}/sources/{pdf['sha256']}/text", headers=hq).json()
    assert "consulenze esterne" in t["text"]
    assert client.get(f"/api/v2/hq/archive/{bando['id']}/sources/{'0' * 64}/file", headers=hq).status_code == 404


def test_delete_source_then_reanalyze_updates_rules(bando, hq):
    d = client.get(f"/api/v2/hq/archive/{bando['id']}", headers=hq).json()
    pdf = next(s for s in d["sources_detail"] if s["name"].endswith("avviso.pdf"))
    assert client.delete(f"/api/v2/hq/archive/{bando['id']}/sources/{pdf['sha256']}", headers=hq).status_code == 200
    assert client.get(f"/api/v2/hq/archive/{bando['id']}/sources/{pdf['sha256']}/file", headers=hq).status_code == 404
    assert client.delete(f"/api/v2/hq/archive/{bando['id']}/sources/{pdf['sha256']}", headers=hq).status_code == 404
    r = client.post(f"/api/v2/hq/archive/{bando['id']}/reanalyze", headers=hq).json()
    assert "max_hourly_rate_personnel" in r["rules_published"] and r["rules_published"]["max_hourly_rate_personnel"] == "40"     # ora resta solo la pagina (40 €/h)


def test_manager_can_set_and_delete_rules_with_validation(bando, hq):
    base = f"/api/v2/hq/archive/{bando['id']}/rules"
    assert client.put(f"{base}/max_hourly_rate_personnel", json={"value": "abc"}, headers=hq).status_code == 422
    assert client.put(f"{base}/regola_inventata", json={"value": 1}, headers=hq).status_code == 422
    assert client.put(f"{base}/max_hourly_rate_personnel", json={"value": 38.5}, headers=hq).json()["value"] == "38.5"
    d = client.get(f"/api/v2/bandi/{bando['id']}").json()
    rule = next(r for r in d["rules"] if r["key"] == "max_hourly_rate_personnel")
    assert rule["value"] == 38.5 and rule["origin"] == "HUMAN_REVIEW" and rule["status"] == "PUBLISHED"
    assert client.put(f"/api/v2/hq/archive/NON-ESISTE/rules/max_hourly_rate_personnel", json={"value": 1}, headers=hq).status_code == 404
    assert client.delete(f"{base}/max_hourly_rate_personnel", headers=hq).status_code == 200
    assert client.delete(f"{base}/max_hourly_rate_personnel", headers=hq).status_code == 404


def test_manager_can_add_reclassify_and_delete_requirements(bando, hq):
    base = f"/api/v2/hq/archive/{bando['id']}/requirements"
    seq = client.post(base, json={"topic": "Nota del consulente", "kind": "OBBLIGO", "text": "Allegare il DURC in corso di validità alla domanda.", "criteria": [45]}, headers=hq).json()["seq"]
    assert client.post(base, json={"topic": "x", "kind": "BOH", "text": "testo lungo abbastanza"}, headers=hq).status_code == 422
    assert client.patch(f"{base}/{seq}", json={"kind": "INFO", "criteria": [45, 46]}, headers=hq).status_code == 200
    r = next(x for x in client.get(f"/api/v2/bandi/{bando['id']}").json()["requirements"] if x["seq"] == seq)
    assert r["kind"] == "INFO" and r["criteria"] == [45, 46] and r["origin"] == "HUMAN_REVIEW"
    assert client.delete(f"{base}/{seq}", headers=hq).status_code == 200 and client.delete(f"{base}/{seq}", headers=hq).status_code == 404


def test_delete_bando_removes_everything_and_curated_ones_can_be_restored(bando, hq):
    r = client.delete(f"/api/v2/hq/archive/{bando['id']}", headers=hq).json()
    assert r["removed"]["bando_sources"] == 2 and r["removed"]["bando_files"] == 2 and r["removed"]["requirements"] >= 4
    assert client.get(f"/api/v2/bandi/{bando['id']}").status_code == 404
    assert bando["id"] not in [b["bando_id"] for b in client.get("/api/v2/bandi").json()]
    assert client.delete(f"/api/v2/hq/archive/{bando['id']}", headers=hq).status_code == 404
    # bando predefinito: eliminato e NON ricreato dal catalogo al riavvio
    assert client.delete("/api/v2/hq/archive/IPERAMMORTAMENTO-2026", headers=hq).status_code == 200
    bandi._SEEDED.clear()
    assert "IPERAMMORTAMENTO-2026" not in [b["bando_id"] for b in client.get("/api/v2/bandi").json()]
    assert [t["bando_id"] for t in client.get("/api/v2/hq/archive", headers=hq).json()["deleted_defaults"]] == ["IPERAMMORTAMENTO-2026"]
    assert client.post("/api/v2/hq/archive/restore-defaults", headers=hq).json()["restored"] == 1
    assert "IPERAMMORTAMENTO-2026" in [b["bando_id"] for b in client.get("/api/v2/bandi").json()]


def test_rename_and_export_zip(bando, hq):
    assert client.patch(f"/api/v2/hq/archive/{bando['id']}", json={"name": "Nuovo nome del fondo"}, headers=hq).status_code == 200
    assert client.get(f"/api/v2/bandi/{bando['id']}").json()["name"] == "Nuovo nome del fondo"
    z = client.get(f"/api/v2/hq/archive/{bando['id']}/export.zip", headers=hq)
    assert z.status_code == 200 and z.headers["content-type"] == "application/zip"
    names = zipfile.ZipFile(io.BytesIO(z.content)).namelist()
    assert "bando.json" in names and any(n.startswith("testi/") for n in names) and any(n.startswith("originali/") and n.endswith(".pdf") for n in names)
    assert zipfile.ZipFile(io.BytesIO(z.content)).read([n for n in names if n.endswith(".pdf")][0]) == PDF          # il PDF originale è identico byte per byte


def test_database_rows_can_be_deleted_but_the_signed_registry_cannot(bando, hq):
    rows = client.get("/api/v2/hq/db/table/requirements?limit=5", headers=hq).json()["rows"]
    assert rows and "_rowid" in rows[0]
    rid = rows[0]["_rowid"]
    before = client.get("/api/v2/hq/db/table/requirements", headers=hq).json()["total"]
    assert client.delete(f"/api/v2/hq/db/table/requirements/row/{rid}", headers=hq).status_code == 200
    assert client.get("/api/v2/hq/db/table/requirements", headers=hq).json()["total"] == before - 1
    assert client.delete(f"/api/v2/hq/db/table/requirements/row/{rid}", headers=hq).status_code == 404
    # registro firmato: intoccabile
    client.post("/api/v2/registry/register", json={"project_id": "PRJ-ARCH", "merkle_root": "0x" + "ab" * 32})
    assert client.delete("/api/v2/hq/db/table/anchors/row/1", headers=hq).status_code == 403
    assert client.delete("/api/v2/hq/db/table/anchors?confirm=anchors", headers=hq).status_code == 403
    assert client.get("/api/v2/registry/status").json()["intact"] is True
    # svuotare una tabella richiede la conferma esplicita
    assert client.delete("/api/v2/hq/db/table/bando_files", headers=hq).status_code == 400
    assert client.delete("/api/v2/hq/db/table/bando_files?confirm=bando_files", headers=hq).json()["deleted_rows"] == 2
    assert client.delete("/api/v2/hq/db/table/inesistente/row/1", headers=hq).status_code == 404
    csv_text = client.get("/api/v2/hq/db/table/bando_sources/export.csv", headers=hq).content.decode("utf-8-sig")
    assert csv_text.splitlines()[0].startswith("_rowid,") and "consulenze esterne" in csv_text                 # testi completi nell'esportazione


def test_consultant_sheet_explains_what_is_said_and_not_said(bando, hq):
    s = client.get(f"/api/v2/hq/archive/{bando['id']}/consultant", headers=hq).json()
    says = {x["key"]: x for x in s["says"]}
    assert says["max_consulting_percentage"]["value"] == 0.15 and "avviso.pdf" in says["max_consulting_percentage"]["source"] and says["max_consulting_percentage"]["criteria"] == [31]
    conflict = next(x for x in s["conflicts"] if x["key"] == "max_hourly_rate_personnel")
    assert set(conflict["values"]) == {"35", "40"} and "Documenti" in conflict["what_to_do"]                    # 35 nel PDF, 40 nella pagina
    silent = {x["key"]: x for x in s["silent"]}
    assert "max_hourly_rate_personnel" not in silent and "max_consulting_percentage" not in silent
    dnsh = silent["requires_dnsh"]
    assert dnsh["mentions"] == 0 and "Non compare" in dnsh["state"] and dnsh["search"] and dnsh["where"] and dnsh["verify"] and dnsh["criteria"][0]["n"] == 28
    sub = silent.get("subcontracting_allowed") or says["subcontracting_allowed"]
    assert sub                                                                                                # «il subappalto non è ammesso» nella pagina
    assert [d["name"] for d in s["documents"]] and all("issues" in d for d in s["documents"]) and any(d["has_file"] for d in s["documents"])
    assert len(s["checklist"]) == 7 and s["summary"]["conflicts"] == 1
    assert client.get("/api/v2/hq/archive/NON-ESISTE/consultant", headers=hq).status_code == 404
    # anche i bandi predefiniti hanno la scheda
    ip = client.get("/api/v2/hq/archive/IPERAMMORTAMENTO-2026/consultant", headers=hq).json()
    assert ip["says"] and ip["curated_gaps"] is not None


def test_public_bando_detail_does_not_leak_manager_only_material(bando):
    d = client.get(f"/api/v2/bandi/{bando['id']}").json()
    assert all("text" not in s for s in d["usage"]["uploaded_sources"])


# ------------------------------------------------------------------ lettura: inglese, documenti «vuoti» e spiegazione del motivo
ENGLISH = ("Youth Exchanges allow groups of young people from different countries to meet. Applicants must be non-profit organisations established in a Programme Country. "
           "The following activities are not eligible for grants under Youth Exchanges: academic study trips and tourist activities. "
           "The grant shall not exceed EUR 30 000 per project. Participants must be aged between 13 and 30 years. "
           "Each project must involve at least two organisations from two different countries. The application form must be submitted by the deadline of the call. "
           "The duration of a Youth Exchange is between 5 and 21 days, excluding travel days. Additional fees cannot be collected from participants with fewer opportunities. ") * 3


def _upload(name, text, bid="CUSTOM-PROVA-LETTURA"):
    return client.post("/api/v2/bandi/upload", json={"name": name, "bando_id": bid, "text": text, "filename": "doc.txt"}).json()


def test_english_document_is_understood():
    r = _upload("Erasmus KA152 prova", ENGLISH)
    assert r["requirements_total"] >= 8
    topics = " ".join(t["topic"] for t in r["detail"]["requirements"])
    for expected in ("Chi può presentare domanda", "Importi massimi e minimi", "Età e condizione dei richiedenti", "Partner e partecipanti", "Durata e tempi"):
        assert expected in topics
    kinds = {t["kind"] for t in r["detail"]["requirements"]}
    assert "DIVIETO" in kinds and "OBBLIGO" in kinds and "LIMITE" in kinds
    assert r["warning"] is None


def test_broken_pdf_lines_are_rejoined_before_reading():
    from app.core.requirements_extractor import extract_requirements, reflow
    broken = "Le consulenze esterne non possono superare il\n15% del totale del progetto approvato\ndall'ente finanziatore.\n\nIl beneficiario deve conservare la docu-\nmentazione di spesa per cinque anni."
    assert "superare il 15% del totale" in reflow(broken) and "documentazione" in reflow(broken)
    reqs = extract_requirements(broken)
    assert any(r["kind"] == "LIMITE" and "15% del totale" in r["text"] for r in reqs)


def test_empty_documents_explain_why():
    garbled = "(cid:12)(cid:45)" * 400
    r = _upload("Prova illeggibile", garbled, "CUSTOM-PROVA-CID")
    assert r["requirements_total"] == 0 and "non decodificabile" in r["warning"]
    short = _upload("Prova breve", "Pagina indice con pochi contenuti e nessuna condizione. " * 3, "CUSTOM-PROVA-BREVE")
    assert short["requirements_total"] == 0 and "troppo breve" in short["warning"]
    descriptive = _upload("Prova descrittiva", "Il paesaggio della valle è molto bello in primavera quando fioriscono i prati. " * 60, "CUSTOM-PROVA-DESCR")
    assert descriptive["requirements_total"] == 0 and "leggilo a mano" in descriptive["warning"]
    long_unrelated = _upload("Bando Molto Specifico", ("Disposizioni generali sulla contabilità. Il ministro deve presentare la relazione annuale entro il 30 giugno. " * 900), "CUSTOM-PROVA-LUNGO")
    assert long_unrelated["requirements_total"] == 0 and "non nomina mai il bando" in long_unrelated["warning"]


def test_document_without_known_topics_still_yields_salient_sentences():
    text = ("Il gestore assicura la presenza di un referente per almeno 12 mesi consecutivi dalla data di avvio delle attività previste. "
            "La quota del 25% sarà trattenuta fino alla verifica finale dell'organismo competente per territorio. ") * 20
    r = _upload("Prova frasi salienti", text, "CUSTOM-PROVA-SAL")
    assert r["requirements_total"] >= 2 and any(x["topic"] == "Da classificare" for x in r["detail"]["requirements"])
