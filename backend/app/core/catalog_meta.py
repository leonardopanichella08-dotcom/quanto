"""Schede del catalogo: descrizione breve e caratteristiche di ogni bando, lette dalla pagina ufficiale (incentivi.gov.it e simili).

Niente è scritto da un modello né dedotto dal nome: la descrizione è la «description» che la pagina stessa dichiara (oppure il primo
paragrafo di «Cos'è», tagliato a fine frase), e le caratteristiche sono i campi della sezione «Ulteriori dettagli» (forma di agevolazione,
costi ammessi, dimensione, regioni, ATECO…). Servono a una cosa: capire quali bandi non ancora studiati somigliano di più a un'azienda,
prima di spendere tempo a leggerne le regole. Le regole numeriche restano compito della pipeline di studio.
"""
from __future__ import annotations

import html as htmllib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import date
from typing import Any, Dict, List, Optional

from app.core import events, lifecycle, research
from app.core.db import connect

# etichetta nella pagina -> chiave
_LABELS = {
    "Obiettivo - Finalità": "purpose", "Forma agevolazione": "form", "Costi ammessi": "costs", "Spesa ammessa (min-max)": "spend_range",
    "Agevolazione concedibile (min-max)": "benefit_range", "Tipologia soggetto": "applicant_type", "Dimensione": "sizes", "Settore attività": "sectors",
    "ATECO": "ateco", "Regioni": "regions", "Comuni": "municipalities", "Ambito territoriale speciale": "special_areas", "Altre caratteristiche": "tags",
    "Soggetto gestore": "manager", "Base normativa primaria": "_skip", "Base normativa secondaria": "_skip", "Provvedimento attuativo": "_skip",
}
_LIST_KEYS = {"sizes", "sectors", "regions", "costs", "form", "special_areas", "tags", "applicant_type", "purpose"}
NL = chr(10)
_COSE = re.compile("(?:^|" + NL + ")Cos'è" + NL + "(.+?)(?:" + NL + "A chi si rivolge" + NL + "|" + NL + "Cosa prevede" + NL + "|" + NL + "Scopri i dettagli" + NL + ")", re.S)
_META_DESC = re.compile(r"<meta[^>]+(?:name|property)=[\"'](?:og:)?description[\"'][^>]+content=[\"']([^\"']+)[\"']", re.I)
_META_DESC_REV = re.compile(r"<meta[^>]+content=[\"']([^\"']+)[\"'][^>]+(?:name|property)=[\"'](?:og:)?description[\"']", re.I)

# costi ammessi nella scheda -> categorie di spesa di QUANTO
COST_CATEGORY = [
    ("personale", "PERSONNEL"), ("immobili", None), ("strumenti e attrezzature", "CAPITAL_ASSETS"), ("impianti", "CAPITAL_ASSETS"), ("macchinari", "CAPITAL_ASSETS"),
    ("attrezzature", "CAPITAL_ASSETS"), ("progettazione", "CONSULTING"), ("studi", "CONSULTING"), ("consulenz", "CONSULTING"), ("servizi professionali", "CONSULTING"),
    ("spese generali", "OVERHEAD"), ("costi generali", "OVERHEAD"), ("formazione", "TRAINING"),
]
SIZE_LABEL = {"MICRO": "microimpresa", "SMALL": "piccola impresa", "MEDIUM": "media impresa", "LARGE": "grande impresa"}


def _mend(s: str) -> str:
    """Alcune schede servono il testo UTF-8 letto come Windows-1252 («â€™» al posto di «’»): lo si rimette a posto."""
    if "â€" in s or "Ã" in s:
        try:
            return s.encode("cp1252").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return s
    return s


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", _mend(htmllib.unescape(s or ""))).strip()


_ABBREVIATIONS = {"n", "nn", "art", "artt", "lett", "comma", "cfr", "es", "ecc", "sig", "dott", "prof", "avv", "pag", "dm", "dl", "dpcm", "dlgs", "reg", "ue", "cd", "spa", "srl", "ss", "sgg"}


def _sentences(text: str, limit: int = 380) -> str:
    """Taglia a fine frase entro ``limit`` caratteri (mai a metà parola)."""
    text = _clean(text)
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for m in reversed(list(re.finditer(r"[.;] ", cut))):
        end = m.start()
        word = re.search(r"(\w+)$", cut[:end])
        if end <= limit * 0.5 or (word and (len(word.group(1)) == 1 or word.group(1).lower() in _ABBREVIATIONS)):
            continue                                        # «n. 59», «art. 4», «D.L.»: non è la fine di una frase
        return cut[:end + 1]
    return cut.rsplit(" ", 1)[0].rstrip(",;:") + "…"


def _split_list(value: str) -> List[str]:
    parts = [_clean(p).strip(",;- ") for p in re.split(r"[\n;,]| - ", value)]
    return [p for p in parts if p and p != "--"]


def _paragraph(block: str) -> str:
    """Primo paragrafo; se finisce con i due punti ci si aggiungono le prime voci dell'elenco che introduce."""
    lines = [ln.strip() for ln in block.split(NL) if ln.strip()]
    if not lines:
        return ""
    first = lines[0]
    if first.endswith(":"):
        items = [ln.lstrip("-•· ").strip() for ln in lines[1:4]]
        first = first[:-1] + ": " + "; ".join(i.rstrip(";.,") for i in items if i)
    return _clean(first)


def parse_page(raw_html: str) -> Dict[str, Any]:
    """Descrizione e caratteristiche dalla pagina di una misura. Ciò che la pagina non dice resta assente (mai riempito)."""
    text, _, _ = research.html_to_text(raw_html)
    out: Dict[str, Any] = {}

    desc, origin = None, None
    for rx in (_META_DESC, _META_DESC_REV):
        m = rx.search(raw_html)
        if m:
            cand = _clean(m.group(1))
            if cand and not cand.lower().startswith("cos'è") and len(cand) > 40:
                desc, origin = cand, "descrizione dichiarata dalla scheda ufficiale"
                break
    section = _COSE.search(text)
    if desc is None and section:
        desc, origin = _paragraph(section.group(1)), "primo paragrafo di «Cos'è» della scheda ufficiale"
    if desc:
        out["summary"] = _sentences(desc)
        out["summary_source"] = origin
    if section:
        out["what_it_is"] = _sentences(_paragraph(section.group(1)), 700)

    # sezione «Ulteriori dettagli»: coppie etichetta / valore su più righe
    start = text.find("Ulteriori Dettagli")
    if start >= 0:
        block = text[start:].split("\n")
        current = None
        buf: Dict[str, List[str]] = {}
        for line in block[1:]:
            ln = line.strip()
            if not ln:
                continue
            if ln in _LABELS:
                current = _LABELS[ln]
                buf.setdefault(current, [])
                continue
            if current and (ln.startswith("Soggetto gestore") and current == "manager" and buf.get("manager")):
                break
            if current:
                buf[current].append(ln)
            if sum(len(v) for v in buf.values()) > 120:
                break
        for key, lines in buf.items():
            if key == "_skip":
                continue
            joined = "\n".join(lines)
            if key in _LIST_KEYS:
                items = _split_list(joined.replace(" -\n", "\n").replace(" ,\n", "\n"))
                items = list(dict.fromkeys(items))
                if items:
                    out[key] = items
            else:
                value = _clean(lines[0] if key == "manager" else " ".join(lines))
                if value and value != "--":
                    out[key] = value[:200]
        if "ateco" in out and isinstance(out["ateco"], str):
            out["ateco_all"] = "tutti i settori" in out["ateco"].lower()
            out["ateco_codes"] = re.findall(r"\b\d{2}(?:\.\d{1,2}){0,2}\b", out["ateco"]) if not out["ateco_all"] else []

    opens, closes = lifecycle.parse_dates(text)
    if opens:
        out["opens"] = opens
    if closes:
        out["closes"] = closes
    out["state"] = lifecycle.classify(opens, closes)
    return out


def cost_categories(meta: Dict[str, Any]) -> Optional[List[str]]:
    """Categorie di spesa di QUANTO coperte dai «costi ammessi» della scheda; ``None`` se la scheda non li dichiara."""
    costs = meta.get("costs")
    if not costs:
        return None
    found = []
    for c in costs:
        low = c.lower()
        for needle, cat in COST_CATEGORY:
            if needle in low and cat and cat not in found:
                found.append(cat)
    return found


# ------------------------------------------------------------------------------------------------ lavoro periodico
def _fetch(url: str):
    try:
        raw, _, ctype = research.http_get(url, limited=False)
        return parse_page(research._decode(raw, ctype)), None
    except Exception as exc:  # noqa: BLE001 - una pagina che non risponde non ferma il lotto
        return None, type(exc).__name__


def describe_batch(limit: int = 120, workers: int = 16, budget_s: float = 40.0, actor: str = "cron") -> Dict[str, Any]:
    """Legge la scheda di un lotto di voci del catalogo senza descrizione (prima le aperte o senza data) e salva descrizione e caratteristiche."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT bando_id, source_url, deadline FROM bandi WHERE bando_id LIKE 'CAT-%' AND meta_at IS NULL AND source_url IS NOT NULL "
            "AND (deadline IS NULL OR deadline = 'non indicata' OR deadline >= ?) ORDER BY bando_id LIMIT ?", (date.today().isoformat(), limit)).fetchall()
        remaining = conn.execute("SELECT COUNT(*) c FROM bandi WHERE bando_id LIKE 'CAT-%' AND meta_at IS NULL AND source_url IS NOT NULL "
                                 "AND (deadline IS NULL OR deadline = 'non indicata' OR deadline >= ?)", (date.today().isoformat(),)).fetchone()["c"]
    report: Dict[str, Any] = {"read": 0, "errors": 0, "closed": 0, "remaining": remaining}
    if not rows:
        return report
    t0 = time.monotonic()
    pool = ThreadPoolExecutor(max_workers=workers)
    futures = {pool.submit(_fetch, r["source_url"]): r for r in rows}
    done, _ = wait(futures, timeout=budget_s)
    pool.shutdown(wait=False, cancel_futures=True)
    now = events.now_iso()
    with connect() as conn:
        for fut in done:
            meta, err = fut.result()
            r = futures[fut]
            if err or meta is None:
                report["errors"] += 1
                continue
            summary = meta.pop("summary", None)
            if meta.get("state") == "CHIUSO":
                report["closed"] += 1
            conn.execute("UPDATE bandi SET summary=?, catalog_meta=?, meta_at=?, "
                         "deadline=CASE WHEN deadline IS NULL OR deadline='non indicata' THEN ? ELSE deadline END WHERE bando_id=?",
                         (summary, json.dumps(meta, ensure_ascii=False), now, meta.get("closes") or "non indicata", r["bando_id"]))
            report["read"] += 1
    report["remaining"] = max(0, remaining - report["read"])
    report["seconds"] = round(time.monotonic() - t0, 1)
    if report["read"]:
        events.record("catalog.describe", f"Lette le schede di {report['read']} bandi del catalogo ({report['remaining']} ancora da leggere)", actor=actor, details=report)
    return report


# ------------------------------------------------------------------------------------------------ affinità con un'azienda
def _size_ok(sizes: List[str], code: Optional[str]) -> Optional[bool]:
    if not sizes or not code:
        return None
    low = " ".join(sizes).lower()
    if "non classificabile" in low and len(sizes) == 1:
        return None
    return SIZE_LABEL[code] in low


def rank_for_profile(profile: Dict[str, Any], by_cat: Dict[str, float], limit: int = 40) -> Dict[str, Any]:
    """Voci del catalogo non ancora studiate, ordinate per affinità con l'azienda. Nessun importo: solo i motivi, uno per uno.

    Esclusi: scadute, riservate a un'altra regione o a un'altra dimensione d'impresa, o a ATECO diversi dal suo. Punteggio = quota delle
    spese previste dell'azienda che le «spese ammesse» dichiarate dalla scheda coprono (0–1); +0,1 se il bando nomina esplicitamente la sua regione,
    +0,05 se tratta il suo tipo di impresa (start-up innovativa)."""
    today = date.today().isoformat()
    total = sum(by_cat.values()) or 0.0
    region, size_code, ateco, startup = profile.get("region"), (profile.get("size") or {}).get("code"), profile.get("ateco_code"), profile.get("is_innovative_startup")
    with connect() as conn:
        rows = conn.execute(
            "SELECT b.bando_id, b.name, b.issuer, b.source_url, b.deadline, b.summary, b.catalog_meta, b.extraction_status FROM bandi b "
            "WHERE b.bando_id LIKE 'CAT-%' AND b.extraction_status = 'NOT_STARTED' AND b.meta_at IS NOT NULL "
            "AND (b.deadline IS NULL OR b.deadline = 'non indicata' OR b.deadline >= ?)", (today,)).fetchall()
        without = conn.execute("SELECT COUNT(*) c FROM bandi WHERE bando_id LIKE 'CAT-%' AND extraction_status = 'NOT_STARTED' AND meta_at IS NULL "
                               "AND (deadline IS NULL OR deadline = 'non indicata' OR deadline >= ?)", (today,)).fetchone()["c"]
    scored, excluded = [], 0
    for r in rows:
        meta = json.loads(r["catalog_meta"] or "{}")
        if meta.get("state") == "CHIUSO":
            excluded += 1
            continue
        reasons: List[str] = []
        flags: List[str] = []
        regions = meta.get("regions") or []
        if regions and region and region not in regions and not any(region.lower() == x.lower() for x in regions):
            excluded += 1
            continue
        local = bool(regions) and len(regions) <= 3                 # una misura che elenca quasi tutte le regioni è nazionale: la regione non la distingue
        if regions and region:
            reasons.append(f"Riservato alla tua regione ({region})" if len(regions) == 1 else f"Ammette la tua regione ({region})")
        elif regions and not region:
            flags.append("regione")
        if meta.get("municipalities"):
            flags.append("valido solo in certi comuni")
        ok = _size_ok(meta.get("sizes") or [], size_code)
        if ok is False:
            excluded += 1
            continue
        if ok:
            reasons.append(f"Ammette la tua dimensione ({SIZE_LABEL[size_code]})")
        elif meta.get("sizes") and not size_code:
            flags.append("dimensione")
        codes = meta.get("ateco_codes") or []
        if codes:
            if not ateco:
                flags.append("ATECO")
            elif any(str(ateco).replace(".", "").startswith(c.replace(".", "")) for c in codes):
                reasons.append(f"Il tuo ATECO {ateco} è tra quelli ammessi")
            else:
                excluded += 1
                continue
        text_all = f"{r['name']} {' '.join(meta.get('tags') or [])} {' '.join(meta.get('purpose') or [])}".lower()
        startup_only = "startup" in text_all.replace("-", "").replace(" ", "") and "innovativ" in text_all
        if startup_only and startup is False:
            excluded += 1
            continue
        compact = f"{r['name']} {' '.join(meta.get('tags') or [])}".lower().replace("-", "").replace(" ", "")
        young_only = "startup" in compact and not startup_only          # «start-up» senza «innovativa»: in genere imprese appena nate
        penalty = 0.0
        if young_only and profile.get("founded_year") and date.today().year - int(profile["founded_year"]) >= 5:
            penalty = 0.4
            flags.append(f"rivolto alle start-up: la tua impresa è del {profile['founded_year']}")
        cats = cost_categories(meta)
        if cats is None:
            score, covered = 0.0, None
            flags.append("spese ammesse non dichiarate")
        else:
            covered = sum(by_cat.get(c, 0.0) for c in cats)
            score = (covered / total) if total else 0.0
            if cats:
                reasons.append("Spese ammesse che ti riguardano: " + ", ".join(sorted({{"PERSONNEL": "personale", "CAPITAL_ASSETS": "beni strumentali", "CONSULTING": "consulenze",
                                                                                        "OVERHEAD": "spese generali", "TRAINING": "formazione"}[c] for c in cats if by_cat.get(c, 0) > 0})))
        if local and region:
            score += 0.1
        score = max(0.0, score - penalty)
        if startup_only and startup:
            score += 0.05
            reasons.append("Rivolto alle start-up innovative, come te")
        scored.append({"bando_id": r["bando_id"], "name": r["name"], "issuer": meta.get("manager") or r["issuer"], "source_url": r["source_url"], "deadline": r["deadline"],
                       "summary": r["summary"], "form": meta.get("form"), "benefit_range": meta.get("benefit_range"), "costs": meta.get("costs"), "regions": regions,
                       "sizes": meta.get("sizes"), "state": meta.get("state"), "opens": meta.get("opens"), "score": round(min(score, 1.0), 3),
                       "affinity": "ALTA" if score >= 0.6 else "MEDIA" if score >= 0.25 else "BASSA", "reasons": reasons, "to_check": flags})
    scored.sort(key=lambda x: (-x["score"], x["name"]))
    return {"items": scored[:limit], "total_candidates": len(scored), "excluded": excluded, "without_description": without}
