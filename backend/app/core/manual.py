"""Il manuale dei processi di QUANTO: un solo testo (``app/data/manuale_processi.md``), letto dal Quartier Generale e trasformato in PDF.

Il PDF si costruisce da quel testo con un convertitore minimo di Markdown (titoli, paragrafi, elenchi, tabelle, citazioni): nessun altro contenuto,
così il manuale che si legge a schermo e quello che si scarica non possono divergere. Il carattere è Vera, che reportlab porta con sé: funziona anche su server
senza font di sistema.
"""
from __future__ import annotations

import io
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

SOURCE = Path(__file__).resolve().parent.parent / "data" / "manuale_processi.md"
_REPLACE = {"→": "->", "≥": ">=", "≤": "<=", "≈": "~", "’": "'", "‘": "'", "“": '"', "”": '"', "…": "...", " ": " "}


def load() -> Dict[str, Any]:
    text = SOURCE.read_text(encoding="utf-8")
    title = next((ln[2:].strip() for ln in text.splitlines() if ln.startswith("# ")), "Manuale dei processi di QUANTO")
    version = re.search(r"Versione\s+([\d.]+)", text)
    return {"title": title, "version": version.group(1) if version else None, "markdown": text, "characters": len(text),
            "sections": [ln[3:].strip() for ln in text.splitlines() if ln.startswith("## ")]}


# ------------------------------------------------------------------------------------------------ PDF
def _fonts() -> None:
    from reportlab.lib.fonts import addMapping
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import reportlab

    if "Vera" in pdfmetrics.getRegisteredFontNames():
        return
    d = Path(reportlab.__file__).resolve().parent / "fonts"
    for name, file in (("Vera", "Vera.ttf"), ("Vera-B", "VeraBd.ttf"), ("Vera-I", "VeraIt.ttf"), ("Vera-BI", "VeraBI.ttf")):
        pdfmetrics.registerFont(TTFont(name, str(d / file)))
    addMapping("Vera", 0, 0, "Vera"); addMapping("Vera", 1, 0, "Vera-B"); addMapping("Vera", 0, 1, "Vera-I"); addMapping("Vera", 1, 1, "Vera-BI")


def _inline(s: str) -> str:
    for a, b in _REPLACE.items():
        s = s.replace(a, b)
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<i>\1</i>", s)
    return s


def build_pdf(markdown: str) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import HRFlowable, KeepTogether, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    _fonts()
    ink, mute, line = colors.HexColor("#15130a"), colors.HexColor("#6b6755"), colors.HexColor("#d9d4bd")
    st = {
        "title": ParagraphStyle("t", fontName="Vera-B", fontSize=24, leading=29, textColor=ink, spaceAfter=6),
        "meta": ParagraphStyle("m", fontName="Vera", fontSize=9, leading=13, textColor=mute, spaceAfter=14),
        "h1": ParagraphStyle("h1", fontName="Vera-B", fontSize=15.5, leading=20, textColor=ink, spaceBefore=16, spaceAfter=6, keepWithNext=1),
        "h2": ParagraphStyle("h2", fontName="Vera-B", fontSize=11.5, leading=15, textColor=ink, spaceBefore=11, spaceAfter=4, keepWithNext=1),
        "h3": ParagraphStyle("h3", fontName="Vera-B", fontSize=10, leading=13.5, textColor=mute, spaceBefore=8, spaceAfter=3, keepWithNext=1),
        "p": ParagraphStyle("p", fontName="Vera", fontSize=9.4, leading=14, textColor=ink, spaceAfter=5),
        "q": ParagraphStyle("q", fontName="Vera-I", fontSize=9.2, leading=13.5, textColor=mute, leftIndent=10, spaceAfter=5),
        "cell": ParagraphStyle("c", fontName="Vera", fontSize=8, leading=10.8, textColor=ink),
        "cellh": ParagraphStyle("ch", fontName="Vera-B", fontSize=8, leading=10.8, textColor=ink),
        "code": ParagraphStyle("k", fontName="Courier", fontSize=8, leading=10.5, textColor=ink, backColor=colors.HexColor("#f4f1e2"), leftIndent=6, rightIndent=6, spaceAfter=6),
    }
    story: List[Any] = []
    lines = markdown.splitlines()
    i = 0
    para: List[str] = []

    def flush() -> None:
        if para:
            story.append(Paragraph(_inline(" ".join(x.strip() for x in para)), st["p"]))
            para.clear()

    def table(rows: List[List[str]]) -> None:
        data = [[Paragraph(_inline(c), st["cellh" if r == 0 else "cell"]) for c in row] for r, row in enumerate(rows)]
        cols = len(rows[0])
        width = 174 * mm
        t = Table(data, colWidths=[width / cols] * cols, repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1e21b")), ("GRID", (0, 0), (-1, -1), 0.4, line), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        story.append(t)
        story.append(Spacer(1, 6))

    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if s.startswith("```"):
            flush()
            j = i + 1
            block = []
            while j < len(lines) and not lines[j].strip().startswith("```"):
                block.append(lines[j])
                j += 1
            from reportlab.platypus import Preformatted
            story.append(Preformatted("\n".join(block), st["code"]))
            i = j + 1
            continue
        if not s:
            flush(); i += 1; continue
        if s.startswith("# "):
            flush(); story.append(Paragraph(_inline(s[2:]), st["title"])); i += 1; continue
        if s.startswith("## "):
            flush(); story.append(Paragraph(_inline(s[3:]), st["h1"])); story.append(HRFlowable(width="100%", thickness=0.6, color=line, spaceAfter=3)); i += 1; continue
        if s.startswith("### "):
            flush(); story.append(Paragraph(_inline(s[4:]), st["h2"])); i += 1; continue
        if s.startswith("#### "):
            flush(); story.append(Paragraph(_inline(s[5:]), st["h3"])); i += 1; continue
        if s.startswith("|"):
            flush()
            rows: List[List[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            if rows:
                table(rows)
            continue
        if re.match(r"^(-|\*|\d+\.)\s+", s):
            flush()
            ordered = bool(re.match(r"^\d+\.", s))
            items: List[Any] = []
            while i < len(lines) and re.match(r"^\s*(-|\*|\d+\.)\s+", lines[i]):
                body = re.sub(r"^\s*(-|\*|\d+\.)\s+", "", lines[i])
                i += 1
                while i < len(lines) and lines[i].startswith("  ") and lines[i].strip() and not re.match(r"^\s*(-|\*|\d+\.)\s+", lines[i]):
                    body += " " + lines[i].strip(); i += 1
                items.append(ListItem(Paragraph(_inline(body), st["p"]), leftIndent=12))
            story.append(ListFlowable(items, bulletType="1" if ordered else "bullet", start=1 if ordered else "•", leftIndent=14, bulletFontName="Vera", bulletFontSize=8.5))
            story.append(Spacer(1, 3))
            continue
        if s.startswith(">"):
            flush(); story.append(Paragraph(_inline(s.lstrip("> ")), st["q"])); i += 1; continue
        if s == "---":
            flush(); story.append(HRFlowable(width="100%", thickness=0.6, color=line)); i += 1; continue
        if i == 2 and story and story[0].style.name == "t":                # riga di versione sotto il titolo
            story.append(Paragraph(_inline(s), st["meta"])); i += 1; continue
        para.append(s); i += 1
    flush()

    def footer(c, doc):
        c.saveState()
        c.setFont("Vera", 7.5)
        c.setFillColor(mute)
        c.drawString(18 * mm, 10 * mm, "QUANTO — Manuale dei processi")
        c.drawRightString(A4[0] - 18 * mm, 10 * mm, f"pagina {doc.page}")
        c.restoreState()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm, title="QUANTO — Manuale dei processi",
                            author="QUANTO", subject=f"Generato il {datetime.now().date().isoformat()}")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()


def to_pdf() -> bytes:
    return build_pdf(load()["markdown"])


if __name__ == "__main__":                      # python -m app.core.manual <file.pdf>
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "manuale_processi.pdf"
    Path(out).write_bytes(to_pdf())
    print(out, os.path.getsize(out))
