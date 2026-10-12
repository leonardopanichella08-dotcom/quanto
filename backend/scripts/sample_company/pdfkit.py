"""Piccola cassetta degli attrezzi per scrivere PDF lunghi e ordinati (intestazione, piè di pagina «pagina X di Y», tabelle di importi)."""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle)

INK = colors.HexColor("#1a1a17")
MUTE = colors.HexColor("#5b5b52")
LINE = colors.HexColor("#b9b9ad")
FOOTER = "Documento di prova - dati fittizi generati per provare QUANTO. Nessun valore corrisponde a persone o imprese reali."


def units(x: int) -> str:
    """Importo in unità di euro, come in un bilancio redatto senza decimali: 1.583.200 (negativi con il segno meno)."""
    return ("-" if x < 0 else "") + f"{abs(int(x)):,}".replace(",", ".")


def cents(x) -> str:
    q = Decimal(str(x)).quantize(Decimal("0.01"))
    s = f"{abs(q):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if q < 0 else "") + s


def pct(x: float, digits: int = 1) -> str:
    return f"{x * 100:.{digits}f}".replace(".", ",") + "%"


S = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=INK, spaceAfter=4),
    "sub": ParagraphStyle("sub", fontName="Helvetica", fontSize=10, leading=13, textColor=MUTE, spaceAfter=10),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=INK, spaceBefore=16, spaceAfter=7, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=INK, spaceBefore=8, spaceAfter=3, keepWithNext=1),
    "p": ParagraphStyle("p", fontName="Helvetica", fontSize=10, leading=14.2, textColor=INK, spaceAfter=7, alignment=TA_JUSTIFY),
    "pl": ParagraphStyle("pl", fontName="Helvetica", fontSize=10, leading=14.2, textColor=INK, spaceAfter=6, alignment=TA_LEFT),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=7.6, leading=10, textColor=MUTE, spaceAfter=3),
    "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=9, leading=11.6, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=9, leading=11.6, textColor=INK),
    "num": ParagraphStyle("num", fontName="Helvetica", fontSize=9, leading=11.6, textColor=INK, alignment=TA_RIGHT),
    "numb": ParagraphStyle("numb", fontName="Helvetica-Bold", fontSize=9, leading=11.6, textColor=INK, alignment=TA_RIGHT),
    "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=10, leading=13.8, textColor=INK, leftIndent=12, bulletIndent=2, spaceAfter=2.5),
}


class _Numbered(canvas.Canvas):
    """Canvas che conosce il numero totale di pagine: «Pagina 3 di 15»."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._saved: List[dict] = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            self._footer(total)
            super().showPage()
        super().save()

    def _footer(self, total: int):
        self.setFont("Helvetica", 7)
        self.setFillColor(MUTE)
        self.drawString(18 * mm, 10 * mm, FOOTER)
        self.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Pagina {self._pageNumber} di {total}")


class Doc:
    """Documento A4 a flusso: ``H1/H2/P/B/table/statement`` aggiungono blocchi, ``save`` scrive il PDF."""

    def __init__(self, path: Path, title: str, header_left: str, header_right: str = "", margins: Tuple[float, float, float, float] = (18, 18, 20, 18)):
        self.path, self.title = Path(path), title
        self.header_left, self.header_right = header_left, header_right
        self.story: list = []
        l, r, t, b = margins
        self.doc = BaseDocTemplate(str(path), pagesize=A4, leftMargin=l * mm, rightMargin=r * mm, topMargin=t * mm, bottomMargin=b * mm, title=title, author="Documento di prova")
        self.width = A4[0] - (l + r) * mm
        self.doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(self.doc.leftMargin, self.doc.bottomMargin, self.doc.width, self.doc.height, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)],
                                                 onPage=self._decor)])

    def _decor(self, c, doc):
        c.saveState()
        c.setFont("Helvetica-Bold", 7.6)
        c.setFillColor(INK)
        c.drawString(doc.leftMargin, A4[1] - 12 * mm, self.header_left)
        c.setFont("Helvetica", 7.6)
        c.setFillColor(MUTE)
        c.drawRightString(A4[0] - doc.rightMargin, A4[1] - 12 * mm, self.header_right)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.4)
        c.line(doc.leftMargin, A4[1] - 14 * mm, A4[0] - doc.rightMargin, A4[1] - 14 * mm)
        c.restoreState()

    # blocchi di testo
    def title_block(self, title: str, sub: str = "") -> None:
        self.story.append(Paragraph(title, S["title"]))
        if sub:
            self.story.append(Paragraph(sub, S["sub"]))

    def H1(self, t: str) -> None:
        self.story.append(Paragraph(t, S["h1"]))

    def H2(self, t: str) -> None:
        self.story.append(Paragraph(t, S["h2"]))

    def P(self, t: str, left: bool = False) -> None:
        self.story.append(Paragraph(t, S["pl" if left else "p"]))

    def small(self, t: str) -> None:
        self.story.append(Paragraph(t, S["small"]))

    def B(self, items: Sequence[str]) -> None:
        for i in items:
            self.story.append(Paragraph(i, S["bullet"], bulletText="•"))

    def space(self, h: float = 6) -> None:
        self.story.append(Spacer(1, h))

    def page_break(self) -> None:
        self.story.append(PageBreak())

    # tabelle
    def table(self, rows: List[List[str]], widths: Sequence[float], head: bool = True, align_right_from: int = 1, zebra: bool = False, bold_rows: Sequence[int] = (), font: float = 8.4,
              line_below: bool = True, keep: bool = False) -> None:
        """Tabella di testo: la prima colonna a sinistra, le altre (da ``align_right_from``) allineate a destra come gli importi."""
        data = []
        for r, row in enumerate(rows):
            bold = (head and r == 0) or r in bold_rows
            cells = []
            for c, v in enumerate(row):
                st = S["numb" if bold else "num"] if c >= align_right_from else S["cellb" if bold else "cell"]
                cells.append(Paragraph(str(v), st))
            data.append(cells)
        t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1 if head else 0)
        style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 2.5), ("RIGHTPADDING", (0, 0), (-1, -1), 2.5), ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6)]
        if line_below:
            style.append(("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#d6d6cc")))
        if head:
            style += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ecece4")), ("LINEBELOW", (0, 0), (-1, 0), 0.6, LINE)]
        if zebra:
            style += [("BACKGROUND", (0, k), (-1, k), colors.HexColor("#f7f7f2")) for k in range(2 if head else 1, len(rows), 2)]
        t.setStyle(TableStyle(style))
        self.story.append(KeepTogether(t) if keep else t)
        self.story.append(Spacer(1, 6))

    def statement(self, rows: List[Tuple[str, List[str], int, bool]], widths: Sequence[float], header: Optional[List[str]] = None) -> None:
        """Prospetto di bilancio: righe (etichetta, importi, livello di rientro 0-3, grassetto). Le etichette rientrano come nello schema civilistico."""
        data = []
        if header:
            data.append([Paragraph(h, S["numb"] if i else S["cellb"]) for i, h in enumerate(header)])
        for label, vals, level, bold in rows:
            st_l = ParagraphStyle("l", parent=S["cellb" if bold else "cell"], leftIndent=level * 9)
            data.append([Paragraph(label, st_l)] + [Paragraph(v, S["numb" if bold else "num"]) for v in vals])
        t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1 if header else 0)
        style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2.5), ("TOPPADDING", (0, 0), (-1, -1), 2.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2)]
        if header:
            style += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ecece4")), ("LINEBELOW", (0, 0), (-1, 0), 0.6, LINE)]
        for k, (_, _, level, bold) in enumerate(rows, 1 if header else 0):
            if bold and level == 0:
                style.append(("LINEABOVE", (0, k), (-1, k), 0.4, LINE))
        t.setStyle(TableStyle(style))
        self.story.append(t)
        self.story.append(Spacer(1, 6))

    def save(self) -> Path:
        self.doc.build(self.story, canvasmaker=_Numbered)
        return self.path
