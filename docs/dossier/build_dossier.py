"""Genera il dossier completo di QUANTO (ex FKOS) in PDF: stessa struttura del documento v2.1, aggiornata allo stato reale.

Uso:  python docs/dossier/build_dossier.py  (dalla radice del repository, con il venv del backend)
Ogni affermazione sullo stato (FATTO / PARZIALE / DA FARE) è verificata sul codice o sul sistema online alla data indicata.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, PageBreak, PageTemplate, Paragraph, Preformatted, Spacer, Table, TableStyle)

from app.core.criteria_catalog import CRITERIA_TITLES  # noqa: E402

WIN = Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("Body", str(WIN / "segoeui.ttf")))
pdfmetrics.registerFont(TTFont("Body-B", str(WIN / "segoeuib.ttf")))
pdfmetrics.registerFont(TTFont("Body-I", str(WIN / "segoeuii.ttf")))
pdfmetrics.registerFont(TTFont("Mono", str(WIN / "consola.ttf")))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-B", italic="Body-I", boldItalic="Body-B")

INK, MUTE, BRAND, LINE = colors.HexColor("#15150f"), colors.HexColor("#5d5d52"), colors.HexColor("#8a7d00"), colors.HexColor("#d9d9cf")
OK, WARN, TODO = colors.HexColor("#1b7a45"), colors.HexColor("#b36b00"), colors.HexColor("#a32a2a")

S = {
    "title": ParagraphStyle("title", fontName="Body-B", fontSize=24, leading=28, textColor=INK, spaceAfter=6),
    "sub": ParagraphStyle("sub", fontName="Body", fontSize=12.5, leading=17, textColor=MUTE, spaceAfter=10),
    "h1": ParagraphStyle("h1", fontName="Body-B", fontSize=16, leading=20, textColor=INK, spaceBefore=14, spaceAfter=6, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="Body-B", fontSize=12, leading=15, textColor=BRAND, spaceBefore=10, spaceAfter=3, keepWithNext=1),
    "h3": ParagraphStyle("h3", fontName="Body-B", fontSize=10, leading=13, textColor=INK, spaceBefore=6, spaceAfter=2, keepWithNext=1),
    "p": ParagraphStyle("p", fontName="Body", fontSize=9.4, leading=13.2, textColor=INK, spaceAfter=4.5, alignment=TA_LEFT),
    "b": ParagraphStyle("b", fontName="Body", fontSize=9.4, leading=13, textColor=INK, leftIndent=12, bulletIndent=2, spaceAfter=2.2),
    "cell": ParagraphStyle("cell", fontName="Body", fontSize=8.2, leading=10.6, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="Body-B", fontSize=8.2, leading=10.6, textColor=INK),
    "code": ParagraphStyle("code", fontName="Mono", fontSize=7.6, leading=9.4, textColor=INK),
    "note": ParagraphStyle("note", fontName="Body-I", fontSize=8.8, leading=12, textColor=MUTE, spaceAfter=4),
}
BADGE = {"FATTO": OK, "PARZIALE": WARN, "DA FARE": TODO, "FASE 3": MUTE, "FASE 4": MUTE, "DECISIONE": BRAND}

story: list = []


def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rich(t: str) -> str:
    """Testo con marcatori semplici: **grassetto**, [[STATO]]."""
    import re
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r'<font name="Mono" size="8">\1</font>', t)
    t = re.sub(r"\[\[([A-Z0-9 ]+)\]\]", lambda m: f'<font name="Body-B" color="{BADGE.get(m.group(1), INK).hexval().replace("0x", "#")}">[{m.group(1)}]</font>', t)
    return t


def H1(t): story.append(Paragraph(rich(t), S["h1"]))
def H2(t): story.append(Paragraph(rich(t), S["h2"]))
def H3(t): story.append(Paragraph(rich(t), S["h3"]))
def P(t): story.append(Paragraph(rich(t), S["p"]))
def NOTE(t): story.append(Paragraph(rich(t), S["note"]))
def B(items): [story.append(Paragraph(rich(i), S["b"], bulletText="•")) for i in items]
def SP(h=4): story.append(Spacer(1, h))
def CODE(t): story.append(Preformatted(t, S["code"], maxLineLength=120)); SP(4)


def T(rows, widths, head=True, zebra=True):
    data = [[Paragraph(rich(str(c)), S["cellb"] if (head and i == 0) else S["cell"]) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1 if head else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.3, LINE), ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
          ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
    if head:
        st += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#efeee4"))]
    if zebra:
        st += [("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fafaf5")) for i in range(2, len(rows), 2)]
    t.setStyle(TableStyle(st))
    story.append(t)
    SP(6)


def page_decor(canv, doc):
    canv.saveState()
    canv.setFont("Body", 7.5)
    canv.setFillColor(MUTE)
    canv.drawString(18 * mm, 10 * mm, "QUANTO v3.0 — Documento completo · stato reale al 4 ottobre 2026")
    canv.drawRightString(A4[0] - 18 * mm, 10 * mm, f"pag. {doc.page}")
    canv.restoreState()


from content import build  # noqa: E402  (il testo vive in content.py)

if __name__ == "__main__":
    out = ROOT / "docs" / "dossier" / "QUANTO_v3_documento_completo.pdf"
    build(sys.modules[__name__])
    doc = BaseDocTemplate(str(out), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=18 * mm, title="QUANTO v3.0 — Documento completo",
                          author="QUANTO", subject="Motore di budgeting, allocazione e profilo aziendale")
    doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")], onPage=page_decor)])
    doc.build(story)
    print(out)
