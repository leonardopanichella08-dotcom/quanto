"""Fonte C: documenti del cliente — lettura con confidenza, verifica dei campi incerti, cifratura, uso nei calcoli.

I PDF di questi test sono generati qui (documenti sintetici per provare il lettore): non sono dati del prodotto.
"""
import base64
import io

import pytest
from fastapi.testclient import TestClient
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.core import crypto_store
from app.core.fonte_c import ocr
from main import app

client = TestClient(app)


def pdf(lines):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y = 800
    for t in lines:
        c.drawString(50, y, t)
        y -= 16
    c.save()
    return buf.getvalue()


def image_only_pdf():
    from PIL import Image
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    from reportlab.lib.utils import ImageReader
    c.drawImage(ImageReader(Image.new("RGB", (300, 100), "white")), 50, 700)
    c.save()
    return buf.getvalue()


PAYSLIP = ["COGNOME E NOME: ROSSI MARIO", "CODICE FISCALE: RSSMRA80A01H501U", "CCNL: Terzo Settore", "LIVELLO: 3", "PERIODO DI RETRIBUZIONE: 08/2026",
           "MENSILITA: 13", "TOTALE COMPETENZE 2.923,08", "QUOTA TFR 216,45", "NETTO IN BUSTA 2.150,00"]
BALANCE = ["BILANCIO D'ESERCIZIO 2025", "B) COSTI DELLA PRODUZIONE", "B.9 Salari e stipendi 150.000,00", "B.9 Oneri sociali 45.000,00",
           "B.7 Consulenze professionali 40.000,00", "B.7 Spese telefoniche 3.200,00", "B.10 Ammortamento macchinari 20.000,00", "B.7 Costi vari 1.500,00",
           "TOTALE COSTI DELLA PRODUZIONE 259.700,00", "C) PROVENTI E ONERI FINANZIARI", "Interessi attivi 100,00"]
F24 = ["MODELLO F24 - SEZIONE ERARIO", "1001 2026 1.234,56", "6099 2025 500,00", "testo qualunque senza importi"]


def upload(doc_type, data, name="doc.pdf"):
    return client.post("/api/v2/fonte-c/documents", json={"doc_type": doc_type, "filename": name, "content_base64": base64.b64encode(data).decode()})


def fields(doc):
    out = {}
    for f in doc["fields"]:
        out.setdefault(f["field_key"], []).append(f)
    return out


def test_payslip_is_read_with_confidence_pii_is_tokenized_and_derived_ral_needs_review():
    r = upload("PAYSLIP", pdf(PAYSLIP))
    assert r.status_code == 201
    d = r.json()
    f = fields(d)
    assert d["method"] == "TEXT_LAYER" and d["status"] == "NEEDS_REVIEW"
    assert f["gross_monthly_eur"][0]["value"] == "2923.08" and f["gross_monthly_eur"][0]["status"] == "AUTO"
    assert f["level"][0]["value"] == "3" and f["mensilita"][0]["value"] == "13"
    # nome e codice fiscale: solo token, mai il valore vero, nemmeno nella riga d'origine
    assert f["employee_name"][0]["value"].startswith("TOK-") and f["tax_code"][0]["value"].startswith("TOK-")
    assert "RSSMRA80A01H501U" not in str(d) and "ROSSI" not in str(d) and "TOK-" in f["tax_code"][0]["snippet"]
    # la RAL non è sul cedolino: è una stima e non entra nei calcoli finché non la conferma una persona
    ral = f["ral_annual_eur"][0]
    assert ral["value"] == "38000.04" and ral["status"] == "NEEDS_REVIEW" and ral["confidence"] < d["confidence_min"]


def test_low_confidence_field_blocks_the_cost_line_until_confirmed_or_corrected():
    d = upload("PAYSLIP", pdf(PAYSLIP)).json()
    line = client.get(f"/api/v2/fonte-c/documents/{d['id']}/cost-line").json()
    assert "payslip_ral_eur" not in line["cost_item"] and "ral_annual_eur" in line["missing"] and "ral_annual_eur" in line["needs_review"]
    assert line["cost_item"]["source_c_ref"] == f"DOC-FC-{d['id']}" and line["cost_item"]["employee_token"].startswith("TOK-")
    ral_id = fields(d)["ral_annual_eur"][0]["id"]
    fixed = client.post(f"/api/v2/fonte-c/documents/{d['id']}/fields/{ral_id}/review", json={"action": "CORRECT", "value": "38.000,00"}).json()
    assert fields(fixed)["ral_annual_eur"][0]["status"] == "CORRECTED" and fields(fixed)["ral_annual_eur"][0]["value"] == "38000.00"
    line = client.get(f"/api/v2/fonte-c/documents/{d['id']}/cost-line").json()
    assert line["cost_item"]["payslip_ral_eur"] == 38000.0 and not line["missing"]
    assert client.post(f"/api/v2/fonte-c/documents/{d['id']}/fields/{fields(d)['tax_code'][0]['id']}/review", json={"action": "CORRECT", "value": "X"}).status_code == 422   # i token non si correggono


def test_ccnl_is_matched_to_a_code_present_in_fonte_b_only():
    d = upload("PAYSLIP", pdf(PAYSLIP)).json()
    ral_id = fields(d)["ral_annual_eur"][0]["id"]
    client.post(f"/api/v2/fonte-c/documents/{d['id']}/fields/{ral_id}/review", json={"action": "CONFIRM"})
    ccnl = fields(d)["ccnl"][0]
    assert client.get(f"/api/v2/fonte-c/documents/{d['id']}/cost-line").json()["cost_item"]["ccnl_code"] == "TERZO_SETTORE"      # esiste in Fonte B (fixture)
    assert ccnl["value"] == "TERZO SETTORE"


def test_balance_sheet_lines_are_classified_and_unknown_ones_wait_for_a_person():
    d = upload("BALANCE_SHEET", pdf(BALANCE)).json()
    lines = [f for f in d["fields"] if f["field_key"] == "expense_line"]
    by_desc = {f["parsed"]["description"]: f for f in lines}
    assert "Interessi attivi" not in by_desc and not any("TOTALE" in k.upper() for k in by_desc)      # fuori dai costi e i totali non contano
    assert by_desc["Salari e stipendi"]["parsed"]["category"] == "PERSONNEL" and by_desc["Salari e stipendi"]["status"] == "AUTO"
    assert by_desc["Spese telefoniche"]["parsed"]["category"] == "OVERHEAD"
    assert by_desc["Ammortamento macchinari"]["parsed"]["category"] == "CAPITAL_ASSETS"
    assert by_desc["Costi vari"]["parsed"]["category"] is None and by_desc["Costi vari"]["status"] == "NEEDS_REVIEW"
    ex = client.get(f"/api/v2/fonte-c/documents/{d['id']}/expenses").json()
    assert ex["fiscal_year"] == 2025 and len(ex["lines"]) == 5 and [x["description"] for x in ex["needs_review"]] == ["Costi vari"]
    # una riga senza categoria non si conferma: si corregge assegnandola
    fid = by_desc["Costi vari"]["id"]
    assert client.post(f"/api/v2/fonte-c/documents/{d['id']}/fields/{fid}/review", json={"action": "CONFIRM"}).status_code == 422
    body = '{"description": "Costi vari", "amount_eur": "1500.00", "category": "OVERHEAD"}'
    assert client.post(f"/api/v2/fonte-c/documents/{d['id']}/fields/{fid}/review", json={"action": "CORRECT", "value": body}).status_code == 200
    assert len(client.get(f"/api/v2/fonte-c/documents/{d['id']}/expenses").json()["lines"]) == 6


def test_f24_rows_are_read():
    d = upload("F24", pdf(F24)).json()
    rows = [f["parsed"] for f in d["fields"] if f["field_key"] == "f24_row"]
    assert rows == [{"codice_tributo": "1001", "anno": "2026", "importo_debito_eur": "1234.56"}, {"codice_tributo": "6099", "anno": "2025", "importo_debito_eur": "500.00"}]


def test_a_scan_without_an_ocr_engine_is_rejected_clearly_and_never_invented():
    d = upload("PAYSLIP", image_only_pdf()).json()
    assert d["status"] == "FAILED" and "OCR" in d["error"] and d["fields"] == []
    assert client.get(f"/api/v2/fonte-c/documents/{d['id']}/cost-line").status_code == 422


def test_ocr_words_carry_their_confidence_into_the_fields(monkeypatch):
    class Fake:
        name = "fake"

        def read_image(self, png, page):
            return [ocr.Word(t, c, page, x, 10, x + 20, 20) for t, c, x in
                    [("TOTALE", 0.62, 1), ("COMPETENZE", 0.60, 30), ("1.000,00", 0.58, 80)]] + \
                   [ocr.Word(t, 0.99, page, x, 40, x + 20, 50) for t, x in [("MENSILITA:", 1), ("14", 40)]]
    monkeypatch.setattr(ocr, "get_engine", lambda: Fake())
    d = upload("PAYSLIP", image_only_pdf()).json()
    assert d["method"] == "OCR:fake" and d["status"] == "NEEDS_REVIEW"
    g = fields(d)["gross_monthly_eur"][0]
    assert g["value"] == "1000.00" and g["status"] == "NEEDS_REVIEW" and g["confidence"] < 0.6          # 0,98 × 0,58
    assert fields(d)["mensilita"][0]["status"] == "AUTO"


def test_ambiguous_label_is_flagged():
    d = upload("PAYSLIP", pdf(PAYSLIP + ["TOTALE COMPETENZE 3.000,00"])).json()
    g = fields(d)["gross_monthly_eur"][0]
    assert g["confidence"] <= 0.55 and g["status"] == "NEEDS_REVIEW" and "valori diversi" in g["snippet"]


def test_original_file_is_encrypted_at_rest_and_round_trips():
    data = pdf(PAYSLIP)
    d = upload("PAYSLIP", data).json()
    from app.core.db import connect
    with connect() as conn:
        stored = bytes(conn.execute("SELECT data_enc FROM client_documents WHERE id=?", (d["id"],)).fetchone()["data_enc"])
    assert b"RSSMRA80A01H501U" not in stored and b"%PDF" not in stored and stored[:1] == b"\x01"
    assert client.get(f"/api/v2/fonte-c/documents/{d['id']}/file").content == data


def test_without_the_file_key_nothing_is_stored(monkeypatch):
    monkeypatch.delenv("QUANTO_FILE_KEY")
    assert upload("PAYSLIP", pdf(PAYSLIP)).status_code == 503
    assert client.get("/api/v2/fonte-c/documents").json() == []


def test_upload_validation():
    assert upload("PAYSLIP", b"non e un pdf").status_code == 422
    assert upload("ALTRO", pdf(PAYSLIP)).status_code == 422
    assert upload("PAYSLIP", pdf(["pagina senza campi noti, solo testo generico ma lungo abbastanza per non sembrare una scansione"])).json()["status"] == "FAILED"


def test_key_validation():
    with pytest.raises(crypto_store.FileKeyError):
        import os
        os.environ["QUANTO_FILE_KEY"] = "troppo-corta"
        try:
            crypto_store.encrypt(b"x")
        finally:
            os.environ["QUANTO_FILE_KEY"] = "11" * 32
