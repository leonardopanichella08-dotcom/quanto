"""Il processo standard di studio di un bando, uguale per ogni bando e ripetibile: CERCA → SCARICA → LEGGI → VALUTA.

1. Cerca: le pagine e i PDF ufficiali del bando (i link già noti restano, quelli indicati a mano passano per primi).
2. Scarica: in parallelo, con un secondo giro sui PDF ufficiali collegati dalle pagine scaricate. Ogni documento si salva intero (testo e file).
3. Leggi: ``analysis.run_analysis`` — requisiti su tutto il documento, regole numeriche dai passaggi che nominano il bando, cifre (tetti e soglie) strutturate.
4. Valuta: un rapporto di completezza con soglie fisse e i motivi di ogni lacuna, così nessun bando resta «a metà» senza che si sappia perché.

Le soglie sono costanti qui sotto: cambiarle cambia il criterio per tutti i bandi insieme.
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from app.core import analysis, bandi, events, research, valuation
from app.core.analysis import distinctive_tokens, is_about  # noqa: F401 - la stessa regola vale al download e all'analisi
from app.core.ingestion import Ingestion

STANDARD_VERSION = "RICERCA-v2"   # lo standard di ricerca e raccolta dati descritto nel manuale (Quartier Generale)
MAX_DOCS = 8                 # documenti scaricati per esecuzione
SECOND_ROUND_DOCS = 4        # PDF ufficiali collegati dalle pagine già scaricate
MAX_ROUNDS = 3               # al massimo tre giri di link da seguire
SECOND_ROUND_FROM_S = 26.0   # il secondo giro parte solo se il primo è stato abbastanza veloce (limite di 60 s della funzione)
INTENSITY_ROUND_DOCS = 4     # documenti in più cercati apposta per la percentuale di agevolazione
INTENSITY_ROUND_BEFORE_S = 30.0
WORKERS = 6

# soglie del rapporto di completezza
COMPLETE_MIN_OFFICIAL_CHARS = 20_000
COMPLETE_MIN_REQUIREMENTS = 40
COMPLETE_MIN_CLASSIFIED = 0.5
PARTIAL_MIN_REQUIREMENTS = 10


def store_fetched(bando_id: str, doc: Dict[str, Any], actor: str = "pipeline") -> str:
    """Salva un documento scaricato: file originale, testo letto, voce nei documenti. Restituisce l'impronta della fonte."""
    warns = list(doc["warnings"])
    if doc["chars"] > events.MAX_SOURCE_TEXT:
        warns.append(f"Testo salvato solo per i primi {events.MAX_SOURCE_TEXT:,} caratteri su {doc['chars']:,} (il file originale è conservato per intero)".replace(",", "."))
    file_sha = events.save_bando_file(bando_id, doc["title"], doc["raw"], doc["content_type"])
    digest = events.save_bando_source(bando_id, doc["title"], doc["text"], url=doc["url"], tier=doc["tier"], content_type=doc["content_type"],
                                      pages=doc["pages"], origin="WEB", file_sha256=file_sha, warnings=warns)
    events.add_document("BANDO_PDF" if doc["kind"] == "PDF" else "BANDO_WEB", doc["url"], doc["raw"], bando_id=bando_id,
                        meta={"url": doc["url"], "kind": doc["kind"], "chars": doc["chars"], "pages": doc["pages"], "tier": doc["tier"]})
    return digest


def _fetch(url: str) -> Dict[str, Any]:
    try:
        return {"url": url, "doc": research.fetch_document(url), "error": None}
    except research.ResearchError as exc:
        return {"url": url, "doc": None, "error": str(exc)}
    except Exception as exc:  # noqa: BLE001 - un documento illeggibile non ferma gli altri
        return {"url": url, "doc": None, "error": f"{type(exc).__name__}"}


def _pick(candidates: List[Dict[str, Any]], known: set, limit: int) -> List[str]:
    """Prima gli indirizzi indicati a mano, poi le fonti ufficiali preselezionate, poi gli altri PDF ufficiali."""
    ranked = sorted(candidates, key=lambda c: (not c.get("user_supplied"), not c.get("preselected"), not (c["tier"] == "UFFICIALE" and c.get("is_pdf")), -c["score"]))
    out: List[str] = []
    for c in ranked:
        if research.normalize_url(c["url"]) in known or c["tier"] != "UFFICIALE" and not c.get("user_supplied"):
            continue
        out.append(c["url"])
        if len(out) >= limit:
            break
    return out


def assess(bando_id: str, fetched_ok: int, failed: List[Dict[str, str]]) -> Dict[str, Any]:
    """Rapporto di completezza: COMPLETA / PARZIALE / INSUFFICIENTE, con le lacune dette una per una."""
    detail = bandi.get_bando_detail(bando_id) or {}
    reqs = detail.get("requirements", [])
    kinds: Dict[str, int] = {}
    for r in reqs:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    classified = sum(1 for r in reqs if r["kind"] != "DA_REVISIONARE")
    figures = sum(len(r.get("figures") or []) for r in reqs)
    sources = events.list_bando_sources(bando_id)
    official = [s for s in sources if s.get("tier") == "UFFICIALE" and not analysis.is_reference_dataset(s)]
    official_chars = sum(len(s["text"]) for s in official)
    rules = [r for r in detail.get("rules", []) if r["status"] == "PUBLISHED"]
    share = (classified / len(reqs)) if reqs else 0.0

    gaps: List[str] = []
    if not official:
        gaps.append("Nessun documento ufficiale letto: servono il decreto, l'avviso o il regolamento dell'ente.")
    elif official_chars < COMPLETE_MIN_OFFICIAL_CHARS:
        gaps.append(f"I documenti ufficiali letti sono brevi ({official_chars:,} caratteri): probabilmente solo una pagina informativa, non il regolamento.".replace(",", "."))
    if reqs and share < COMPLETE_MIN_CLASSIFIED:
        gaps.append(f"Solo il {round(share * 100)}% dei requisiti è collegato a un tema noto: il resto va rivisto da una persona.")
    if not rules:
        gaps.append("Nessuna regola numerica pubblicata: i tetti compaiono solo come requisiti di tipo «limite» e non accendono controlli.")
    for f in failed[:5]:
        gaps.append(f"Non scaricato: {f['url'][:90]} ({f['error']})")

    if official and official_chars >= COMPLETE_MIN_OFFICIAL_CHARS and len(reqs) >= COMPLETE_MIN_REQUIREMENTS and share >= COMPLETE_MIN_CLASSIFIED:
        status = "COMPLETA"
    elif official and len(reqs) >= PARTIAL_MIN_REQUIREMENTS:
        status = "PARZIALE"
    else:
        status = "INSUFFICIENTE"
    return {"status": status, "documents_official": len(official), "documents_total": len(sources), "official_chars": official_chars,
            "requirements": len(reqs), "requirements_by_kind": kinds, "classified_share": round(share, 2), "figures": figures,
            "rules_published": len(rules), "fetched_now": fetched_ok, "gaps": gaps}


def run(bando_id: str, urls: Optional[List[str]] = None, max_docs: int = MAX_DOCS, actor: str = "pipeline") -> Dict[str, Any]:
    t0 = time.monotonic()
    b = Ingestion.get_bando(bando_id)
    if b is None:
        raise KeyError(bando_id)
    name = b["name"]
    supplied = [u for u in (urls or []) if u.startswith(("http://", "https://"))]
    if b.get("source_url") and b["source_url"] not in supplied:
        supplied.append(b["source_url"])
    known = {research.normalize_url(s["url"]) for s in events.list_bando_sources(bando_id) if s.get("url")}

    try:
        found = research.search_web(name, "", supplied)
    except research.ResearchError as exc:           # ricerca non disponibile: si lavora comunque sugli indirizzi già noti
        found = {"candidates": [{"url": u, "title": u, "tier": research.classify_url(u), "score": 1000, "is_pdf": u.lower().endswith(".pdf"),
                                 "user_supplied": True, "preselected": True} for u in supplied], "engine_errors": [str(exc)]}
    chosen = _pick(found["candidates"], known, max_docs)
    failed: List[Dict[str, str]] = []
    fetched_ok = 0
    htmls: List[Dict[str, Any]] = []

    def fetch_and_store(batch: List[str]) -> None:
        nonlocal fetched_ok
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            results = list(pool.map(_fetch, batch))
        for r in results:
            if r["doc"] is None:
                failed.append({"url": r["url"], "error": r["error"]})
                continue
            if r["url"] not in supplied and not is_about(name, r["doc"]):
                failed.append({"url": r["url"], "error": "scartato: non parla di questo bando"})
                continue
            store_fetched(bando_id, r["doc"], actor)
            known.add(research.normalize_url(r["doc"]["url"]))
            fetched_ok += 1
            if r["doc"]["kind"] == "HTML":
                htmls.append(r["doc"])

    fetch_and_store(chosen)
    rounds = 0                                         # giri successivi: dalla scheda del catalogo alla pagina dell'ente, e da questa agli allegati (bando, decreto)
    while htmls and rounds < MAX_ROUNDS and time.monotonic() - t0 < SECOND_ROUND_FROM_S:
        rounds += 1
        current, htmls = htmls, []
        links: List[Dict[str, Any]] = []
        for d in current:
            links += research.find_links(d["url"], d["links"], known, focus=name)
        second: List[str] = []
        for link in sorted(links, key=lambda x: (not x["is_pdf"], -x["score"])):
            if link["url"] not in second and research.normalize_url(link["url"]) not in known:
                second.append(link["url"])
            if len(second) >= SECOND_ROUND_DOCS:
                break
        if not second:
            break
        fetch_and_store(second)

    analysed = analysis.run_analysis(bando_id) if events.list_bando_sources(bando_id) else None
    if analysed is not None and not valuation.has_intensity(bando_id) and time.monotonic() - t0 < INTENSITY_ROUND_BEFORE_S:
        try:                                                   # terzo giro: nei documenti non c'è ancora la percentuale di agevolazione, la si cerca apposta
            more = research.search_web(name, "intensità contributo percentuale spese ammissibili beneficiari", supplied)
        except research.ResearchError:
            more = {"candidates": []}
        extra = _pick(more["candidates"], known, INTENSITY_ROUND_DOCS)
        if extra:
            fetch_and_store(extra)
            analysed = analysis.run_analysis(bando_id)
    report = assess(bando_id, fetched_ok, failed)
    if not valuation.has_intensity(bando_id):
        report["gaps"].append("Nei documenti ufficiali letti non compare una percentuale di agevolazione (contributo, intensità di aiuto): il valore in euro non si può ancora calcolare.")
    report["standard"] = STANDARD_VERSION
    report["engine_errors"] = found.get("engine_errors", [])
    report["seconds"] = round(time.monotonic() - t0, 1)
    report["rules_new"] = sorted(analysed["outcome"].published) if analysed else []
    events.record("bando.pipeline", f"Studio del bando «{name[:60]}»: {report['status']} — {report['documents_official']} documenti ufficiali, {report['requirements']} requisiti, "
                  f"{report['figures']} cifre, {report['rules_published']} regole", bando_id=bando_id, actor=actor, status="OK" if report["status"] != "INSUFFICIENTE" else "WARN",
                  details=report)
    return report
