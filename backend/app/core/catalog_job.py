"""Stadio 1 — catalogazione continua (schema FKOS): il catalogo dei bandi si aggiorna da solo, senza che nessuno lo chieda.

Solo metadati (nome, ente, scadenza, link): nessuna regola e nessun numero vengono toccati qui. Le voci arrivano dai cataloghi
istituzionali (incentivi.gov.it, Invitalia) tramite le loro mappe del sito; se c'è un modello linguistico collegato, per alcune pagine
per volta legge ente e scadenza, e ogni dato è accettato solo se la frase di origine compare davvero nella pagina.
Il lavoro periodico è lanciato da Vercel Cron (vedi vercel.json) su ``/api/v2/cron/catalog-refresh``.
"""
from __future__ import annotations

import hashlib
import logging
import re
import urllib.parse
from datetime import date
from typing import Any, Dict, List

from app.core import discovery, events, lifecycle, llm, research
from app.core.db import connect

logger = logging.getLogger("quanto.catalog")

_LEADING_YEAR = re.compile(r"^(19|20)\d{2}\b")


def _bando_id(url: str, title: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", title).strip("-").upper()[:36] or "VOCE"
    return f"CAT-{slug}-{hashlib.sha1(url.encode()).hexdigest()[:6].upper()}"


def cleanup_stale(actor: str = "cron") -> Dict[str, Any]:
    """Elimina dal catalogo nazionale (mai dai bandi curati) le voci ormai certamente chiuse:
    misure locali «una tantum» il cui nome inizia con un anno passato (es. «2021 Bando...»),
    o con una scadenza passata — e solo se nessuno le ha mai toccate (nessuna ricerca avviata,
    nessun cliente le ha richieste): un bando su cui è già stato fatto del lavoro non si cancella mai in automatico."""
    this_year = date.today().year
    today_iso = date.today().isoformat()
    with connect() as conn:
        rows = conn.execute(
            "SELECT bando_id, name, deadline, source_url FROM bandi WHERE bando_id LIKE 'CAT-%' AND catalog_status != 'CURATED' "
            "AND extraction_status = 'NOT_STARTED' AND requested_by_clients = 0"
        ).fetchall()
        stale = []
        for r in rows:
            name, deadline = r["name"] or "", r["deadline"]
            m = _LEADING_YEAR.match(name)
            by_name = bool(m) and int(m.group(0)[:4]) < this_year
            by_deadline = bool(deadline) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", deadline) is not None and deadline < today_iso
            # Nessuna data dichiarata dalla pagina e il nome cita solo anni passati: nessuna prova che sia aperto, quindi chiuso.
            years = [int(y) for y in re.findall(r"\b(20[0-3]\d)\b", name)]
            undated = deadline in (None, "non indicata")
            by_old_year = undated and bool(years) and max(years) < this_year and (deadline == "non indicata" or "incentivi.gov.it" not in (r["source_url"] or ""))
            if by_name or by_deadline or by_old_year:
                stale.append(r["bando_id"])
        if stale:
            placeholders = ",".join("?" * len(stale))
            for table in ("rules", "requirements", "bando_sources", "bandi"):
                conn.execute(f"DELETE FROM {table} WHERE bando_id IN ({placeholders})", stale)
    if stale:
        events.record("catalog.cleanup", f"Eliminate {len(stale)} voci del catalogo ormai chiuse (misure passate, mai toccate)", actor=actor,
                      details={"deleted": len(stale)})
    return {"deleted": len(stale)}


def refresh(enrich: int = 15, actor: str = "cron") -> Dict[str, Any]:
    report: Dict[str, Any] = {"catalogs": {}, "inserted": 0, "enriched": 0, "errors": []}
    for cat in discovery.CATALOGS:
        try:
            items = discovery.load_catalog(cat, force=True)
        except research.ResearchError as exc:
            report["errors"].append(f"{cat['name']}: {exc}")
            continue
        rows: List[tuple] = [(_bando_id(u, t), t.title()[:200], cat["name"], u, "CATALOGED", "NOT_STARTED") for u, t in items]
        with connect() as conn:
            before = conn.execute("SELECT COUNT(*) c FROM bandi WHERE catalog_status='CATALOGED' AND bando_id LIKE 'CAT-%'").fetchone()["c"]
            conn.executemany("INSERT INTO bandi (bando_id, name, issuer, source_url, catalog_status, extraction_status) VALUES (?,?,?,?,?,?) ON CONFLICT (bando_id) DO NOTHING", rows)
            after = conn.execute("SELECT COUNT(*) c FROM bandi WHERE catalog_status='CATALOGED' AND bando_id LIKE 'CAT-%'").fetchone()["c"]
        report["catalogs"][cat["name"]] = {"listed": len(items), "new": after - before}
        report["inserted"] += after - before
    client = llm.get_client()
    if client is not None and enrich > 0:
        with connect() as conn:
            todo = conn.execute("SELECT bando_id, source_url, issuer FROM bandi WHERE bando_id LIKE 'CAT-%' AND deadline IS NULL AND issuer IN (?,?) ORDER BY bando_id LIMIT ?",
                                (discovery.CATALOGS[0]["name"], discovery.CATALOGS[1]["name"], enrich)).fetchall()
        for r in todo:
            try:
                doc = research.fetch_document(r["source_url"])
                meta = llm.extract_metadata(client, doc["text"])
            except Exception as exc:
                report["errors"].append(f"{r['bando_id']}: {type(exc).__name__}")
                continue
            with connect() as conn:
                conn.execute("UPDATE bandi SET name=COALESCE(?, name), issuer=COALESCE(?, issuer), deadline=COALESCE(?, deadline) WHERE bando_id=?",
                             (meta.get("name"), meta.get("issuer"), meta.get("deadline") or "non indicata", r["bando_id"]))
            report["enriched"] += 1
    report["lifecycle"] = lifecycle.scan_catalog(limit=60, budget_s=25.0)            # prima si leggono le date, poi si eliminano le voci chiuse
    report["deleted"] = cleanup_stale(actor)["deleted"]
    events.record("catalog.refresh", f"Catalogo aggiornato: {report['inserted']} voci nuove, {report['enriched']} arricchite, {report['deleted']} eliminate perché ormai chiuse"
                  + (f", {len(report['errors'])} errori" if report["errors"] else ""),
                  status="WARN" if report["errors"] and not report["inserted"] else "OK", actor=actor, details=report)
    return report
