"""Lettura dei documenti (Modulo 9.3, 15.3): testo del PDF quando c'è, OCR quando il documento è una scansione.

Ogni parola letta porta la sua ``confidenza`` (0-1). Per il testo del PDF è 1.0 (il testo è lì, non è stato «riconosciuto»);
per l'OCR è quella del motore. La confidenza delle parole si propaga ai campi estratti (parsers.py): un campo letto male
non entra nei calcoli finché una persona non lo conferma.

Motori OCR: l'interfaccia ``OcrEngine`` è unica. ``TesseractEngine`` è il motore open source (serve il programma Tesseract
sul server, quindi non gira su hosting serverless come Vercel). Senza motore configurato le scansioni vengono rifiutate
con un messaggio chiaro: non si inventa mai un testo.
"""
from __future__ import annotations

import io
import os
import shutil
from dataclasses import dataclass
from typing import List, Optional, Protocol

MIN_CHARS_PER_PAGE = 40          # sotto questa soglia la pagina è considerata una scansione
MAX_PAGES = 60


@dataclass
class Word:
    text: str
    conf: float
    page: int
    x0: float
    top: float
    x1: float
    bottom: float


@dataclass
class ReadResult:
    words: List[Word]
    pages: int
    method: str                  # TEXT_LAYER | OCR:<motore> | MIXED:<motore>

    @property
    def mean_confidence(self) -> float:
        return sum(w.conf for w in self.words) / len(self.words) if self.words else 0.0


class OcrUnavailable(RuntimeError):
    """Il documento è una scansione e non c'è un motore OCR configurato (o non funziona)."""


class OcrEngine(Protocol):
    name: str

    def read_image(self, png: bytes, page: int) -> List[Word]: ...


class TesseractEngine:
    """Motore open source. Richiede il programma ``tesseract`` (con i dati della lingua italiana) e il pacchetto pytesseract."""
    name = "tesseract"

    def __init__(self, lang: str = "ita+eng"):
        self.lang = lang
        if shutil.which(os.getenv("QUANTO_TESSERACT_CMD", "tesseract")) is None:
            raise OcrUnavailable("Tesseract non è installato su questo server")
        try:
            import pytesseract  # noqa: F401
        except ImportError:
            raise OcrUnavailable("Manca il pacchetto pytesseract") from None

    def read_image(self, png: bytes, page: int) -> List[Word]:
        import pytesseract
        from PIL import Image
        cmd = os.getenv("QUANTO_TESSERACT_CMD")
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd
        img = Image.open(io.BytesIO(png))
        d = pytesseract.image_to_data(img, lang=self.lang, output_type=pytesseract.Output.DICT)
        out: List[Word] = []
        for i, t in enumerate(d["text"]):
            t = (t or "").strip()
            conf = float(d["conf"][i])
            if t and conf >= 0:
                out.append(Word(t, conf / 100.0, page, d["left"][i], d["top"][i], d["left"][i] + d["width"][i], d["top"][i] + d["height"][i]))
        return out


def get_engine() -> Optional[OcrEngine]:
    name = os.getenv("QUANTO_OCR_ENGINE", "").strip().lower()
    if not name or name == "none":
        return None
    if name == "tesseract":
        return TesseractEngine()
    raise OcrUnavailable(f"Motore OCR sconosciuto: {name}")


def _render_page_png(pdf_bytes: bytes, index: int, scale: float = 3.0) -> bytes:
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(pdf_bytes)
    img = pdf[index].render(scale=scale).to_pil()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def read_pdf(data: bytes, engine: Optional[OcrEngine] = None) -> ReadResult:
    """Legge un PDF: pagine con testo → parole del PDF; pagine-immagine → OCR (se c'è un motore, altrimenti errore)."""
    import pdfplumber
    words: List[Word] = []
    used_ocr = False
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        n = len(pdf.pages)
        if n == 0:
            raise ValueError("Il PDF non ha pagine")
        if n > MAX_PAGES:
            raise ValueError(f"PDF troppo lungo ({n} pagine, massimo {MAX_PAGES})")
        for i, page in enumerate(pdf.pages, 1):
            ws = page.extract_words(keep_blank_chars=False, use_text_flow=False, x_tolerance=1.5)
            chars = sum(len(w["text"]) for w in ws)
            if chars >= MIN_CHARS_PER_PAGE:
                words += [Word(w["text"], 1.0, i, float(w["x0"]), float(w["top"]), float(w["x1"]), float(w["bottom"])) for w in ws]
                continue
            eng = engine if engine is not None else get_engine()
            if eng is None:
                raise OcrUnavailable(f"La pagina {i} è una scansione (nessun testo selezionabile) e non c'è un motore OCR configurato (QUANTO_OCR_ENGINE)")
            words += eng.read_image(_render_page_png(data, i - 1), i)
            used_ocr = True
            engine = eng
    method = "TEXT_LAYER" if not used_ocr else f"OCR:{engine.name}"
    return ReadResult(words, n, method)


def group_lines(words: List[Word], y_tol: float = 3.0) -> List[dict]:
    """Raggruppa le parole in righe (stessa altezza), da sinistra a destra. Ogni riga: testo, pagina, confidenza minima e media."""
    lines: List[dict] = []
    for page in sorted({w.page for w in words}):
        ws = sorted((w for w in words if w.page == page), key=lambda w: (round(w.top), w.x0))
        cur: List[Word] = []
        for w in ws:
            if cur and abs(w.top - cur[0].top) > y_tol:
                lines.append(_line(cur))
                cur = []
            cur.append(w)
        if cur:
            lines.append(_line(cur))
    return lines


def _line(ws: List[Word]) -> dict:
    ws = sorted(ws, key=lambda w: w.x0)
    return {"text": " ".join(w.text for w in ws), "page": ws[0].page, "conf_min": min(w.conf for w in ws),
            "conf_mean": sum(w.conf for w in ws) / len(ws), "top": ws[0].top}
