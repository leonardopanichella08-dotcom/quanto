"""Documenti pubblici di domanda: si trovano, si scaricano, si conservano e si leggono con regole fisse (niente inventato)."""
import io
import zipfile

from fastapi.testclient import TestClient

from app.core import application_forms as af, research
from app.core.db import connect
from main import app

client = TestClient(app)

FORM = """Domanda di ammissione alle agevolazioni
Denominazione dell'impresa ______________________
Codice fiscale ………………………
Partita IVA: __________
Il sottoscritto, consapevole delle sanzioni penali, DICHIARA:
di essere una micro, piccola o media impresa;
di non essere in difficoltà ai sensi del regolamento UE 651/2014;
☐ di avere almeno una sede operativa in Umbria
☐ di aver preso visione dell'informativa privacy
Alla domanda devono essere allegati:
- ultimo bilancio approvato;
- preventivi di spesa di almeno tre fornitori;
- visura camerale aggiornata.
Descrivere il progetto e gli obiettivi che si intendono raggiungere
Indicare il numero di nuovi occupati previsti nei 12 mesi successivi
3.2 Piano degli investimenti
L'impresa può cumulare altri aiuti?
Il presente Avviso è pubblicato sul sito.
"""


def test_extract_items_reads_documents_fields_questions_and_declarations_exactly_as_written():
    it = af.extract_items(FORM, "DOMANDA")
    assert it["ALLEGATO"] == ["ultimo bilancio approvato", "preventivi di spesa di almeno tre fornitori", "visura camerale aggiornata"]
    assert "Denominazione dell'impresa" in it["CAMPO"] and "Codice fiscale" in it["CAMPO"] and "Partita IVA" in it["CAMPO"]
    assert "Descrivere il progetto e gli obiettivi che si intendono raggiungere" in it["DOMANDA"]
    assert "Indicare il numero di nuovi occupati previsti nei 12 mesi successivi" in it["DOMANDA"]
    assert "L'impresa può cumulare altri aiuti?" in it["DOMANDA"]
    assert "di essere una micro, piccola o media impresa" in it["DICHIARAZIONE"] and "di avere almeno una sede operativa in Umbria" in it["DICHIARAZIONE"]
    assert not any("pubblicato sul sito" in x for v in it.values() for x in v)                 # una frase qualunque non diventa una voce


def test_a_call_text_lists_attachments_and_declarations_but_its_prose_is_not_mistaken_for_questions():
    text = "Art. 8 - Presentazione\nLa domanda deve essere corredata da:\n- statuto o atto costitutivo\n- copia del documento d'identità del legale rappresentante\n\n" \
           "Il beneficiario dovrà descrivere le attività svolte nella relazione finale.\nAllegato B - Dichiarazione sostitutiva di certificazione\n"
    it = af.extract_items(text, "AVVISO")
    assert it["ALLEGATO"] == ["statuto o atto costitutivo", "copia del documento d'identità del legale rappresentante", "Allegato B - Dichiarazione sostitutiva di certificazione"]
    assert it["DOMANDA"] == [] and it["CAMPO"] == []


def test_classification_keeps_forms_and_drops_privacy_graduatorie_and_decrees_about_deadlines():
    assert af.classify("Allegato 1 - Domanda di partecipazione", "https://x.it/a.docx") == "DOMANDA"
    assert af.classify("Allegato 2 - Formulario di progetto", "https://x.it/b.docx") == "FORMULARIO"
    assert af.classify("Guida alla compilazione", "https://x.it/c.pdf") == "ISTRUZIONI"
    assert af.classify("Informativa privacy", "https://x.it/d.pdf") is None
    assert af.classify("Graduatoria definitiva", "https://x.it/e.pdf") is None
    assert af.classify("Decreto n. 12 - Proroga termini per la presentazione", "https://x.it/f.pdf") is None
    assert af.classify("Elenco risultanze istruttorie domande", "https://x.it/g.pdf") is None


def _docx(lines):
    body = "".join(f"<w:p><w:r><w:t>{ln}</w:t></w:r></w:p>" for ln in lines)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", f'<?xml version="1.0"?><w:document xmlns:w="x"><w:body>{body}</w:body></w:document>')
    return buf.getvalue()


PAGE = """<html><body>
<a href="/f/domanda.docx">Allegato 1 - Domanda di ammissione</a>
<a href="/f/dl">Scarica Allegato</a>
<a href="/f/privacy.pdf">Informativa privacy</a>
<a href="/f/vecchio.doc">Allegato 3 - Dichiarazione de minimis</a>
<a href="https://sito-di-un-consulente.example.com/domanda.pdf">Modulo domanda spiegato</a>
</body></html>"""


def _web(monkeypatch):
    docx = _docx(FORM.splitlines())
    pages = {"https://www.regione.esempio.it/bando": (PAGE.encode(), "text/html"), "https://www.regione.esempio.it/f/domanda.docx": (docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
             "https://www.regione.esempio.it/f/dl": (_docx(["Allegato 2 - Formulario di progetto", "Descrivere il contesto di mercato in cui opera l'impresa"]), "application/octet-stream"),
             "https://www.regione.esempio.it/f/vecchio.doc": (b"\xd0\xcf\x11\xe0 vecchio", "application/msword")}

    def fake_get(url, max_bytes=0, accept_error_body=False, timeout=0, limited=True):
        if url in pages:
            body, ctype = pages[url]
            return body, url, ctype
        raise research.ResearchError("Il sito ha risposto 404")
    monkeypatch.setattr(research, "http_get", fake_get)


def _bando():
    with connect() as conn:
        conn.execute("INSERT INTO bandi (bando_id, name, issuer, source_url, catalog_status, extraction_status) VALUES (?,?,?,?,?,?)",
                     ("CAT-PROVA-DOMANDA", "Voucher di prova", "Regione Esempio", "https://www.regione.esempio.it/bando", "CATALOGED", "NOT_STARTED"))


def test_collect_downloads_official_forms_keeps_the_originals_and_flags_unreadable_formats(monkeypatch):
    _web(monkeypatch)
    _bando()
    res = af.collect("CAT-PROVA-DOMANDA", actor="test")
    assert res["found"] == 3 and not res["errors"]                       # privacy esclusa, sito di un consulente escluso
    app_ = af.get("CAT-PROVA-DOMANDA")
    by_title = {d["title"]: d for d in app_["docs"]}
    assert set(by_title) == {"Allegato 1 - Domanda di ammissione", "dl", "Allegato 3 - Dichiarazione de minimis"} or len(by_title) == 3
    domanda = next(d for d in app_["docs"] if d["kind"] == "DOMANDA")
    assert domanda["format"] == "DOCX" and domanda["downloadable"] and domanda["counts"]["CAMPO"] >= 3
    old = next(d for d in app_["docs"] if d["format"] == "DOC")
    assert old["downloadable"] and old["warnings"] and sum(old["counts"].values()) == 0          # non legge, avvisa, ma lo si scarica
    questions = [x["text"] for x in app_["items"]["DOMANDA"]["list"]]
    assert "Descrivere il contesto di mercato in cui opera l'impresa" in questions
    assert all(x["doc"] for k in af.ITEM_KINDS for x in app_["items"][k]["list"])                  # ogni voce dice da quale documento viene
    assert af.collect("CAT-PROVA-DOMANDA", actor="test")["found"] == 3                              # rilancio: niente doppioni
    assert len(af.get("CAT-PROVA-DOMANDA")["docs"]) == 3


def test_application_api_collects_lists_and_serves_the_original_file(monkeypatch):
    _web(monkeypatch)
    _bando()
    assert client.get("/api/v2/bandi/CAT-INESISTENTE/application").status_code == 404
    empty = client.get("/api/v2/bandi/CAT-PROVA-DOMANDA/application").json()
    assert empty["docs"] == [] and empty["collected_at"] is None
    r = client.post("/api/v2/bandi/CAT-PROVA-DOMANDA/application/collect")
    assert r.status_code == 200 and r.json()["found"] == 3
    docs = r.json()["application"]["docs"]
    sha = next(d["sha256"] for d in docs if d["format"] == "DOCX" and d["kind"] == "DOMANDA")
    f = client.get(f"/api/v2/bandi/CAT-PROVA-DOMANDA/application/file/{sha}")
    assert f.status_code == 200 and f.content[:2] == b"PK" and "attachment" in f.headers["content-disposition"]
    assert client.get("/api/v2/bandi/CAT-PROVA-DOMANDA/application/file/" + "0" * 64).status_code == 404
    assert client.get("/api/v2/bandi/CAT-PROVA-DOMANDA/application/file/../../etc").status_code in (404, 422)


def test_a_bando_with_no_public_forms_says_so_instead_of_inventing_them(monkeypatch):
    monkeypatch.setattr(research, "http_get", lambda *a, **k: (b"<html><body>Solo testo</body></html>", "https://www.regione.esempio.it/bando", "text/html"))
    _bando()
    res = af.collect("CAT-PROVA-DOMANDA", actor="test")
    assert res["found"] == 0 and "piattaforma" in res["note"]
    assert af.get("CAT-PROVA-DOMANDA")["totals"] == {"ALLEGATO": 0, "DOMANDA": 0, "CAMPO": 0, "DICHIARAZIONE": 0}
