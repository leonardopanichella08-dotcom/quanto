"""Biblioteca dei bandi: seed del catalogo curato, elenco, dettaglio e copertura dei 60 criteri."""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

from app.core.criteria_catalog import CRITERIA_TITLES
from app.core import db
from app.core.db import connect
from app.core.demo import SANDBOX_RULES
from app.core.ingestion import IDENTITY_FIELDS, Ingestion, normalize_value
from app.core import research
from app.core.requirements_extractor import extract_legal_refs
from app.data.bandi_catalog import BANDI, REFERENCES

# Quali criteri attiva ciascuna regola del bando.
RULE_CRITERIA: Dict[str, List[int]] = {
    "max_hourly_rate_personnel": [7], "max_consulting_percentage": [31], "max_overhead_percentage": [36], "eligible_categories": [16],
    "excluded_asset_natures": [16], "requires_eu_origin": [16], "equipment_depreciation_only": [17, 18], "requires_new_asset": [19],
    "requires_iot": [20], "min_energy_saving_pct": [21], "max_price_deviation_pct": [22], "max_installation_pct": [23],
    "vat_never_eligible": [54], "max_immaterial_pct": [26], "requires_dnsh": [28], "appraisal_threshold_eur": [30],
    "min_durability_months": [58], "require_independent_supplier": [32], "allowed_ateco_prefixes": [34], "subcontracting_allowed": [35],
    "overhead_flat_rate_pct": [36], "overhead_flat_base": [36], "max_communication_pct": [37], "guarantee_costs_eligible": [38],
    "max_audit_cost_eur": [39], "eligibility_start": [46], "eligibility_end": [46], "non_cumulable_funding_ids": [47],
    "max_aid_intensity_pct": [48], "contribution_rate_pct": [48, 49], "de_minimis_residual_eur": [49], "requires_cup": [50],
    "blocked_payment_methods": [52], "requires_milestones": [57], "max_inter_chapter_variation_pct": [56],
    "reimbursement_lag_months": [55], "advance_pct": [55], "overtime_allowed": [11], "payroll_tolerance_pct": [15],
}
# Criteri che NON possono girare senza una regola del bando; gli altri si eseguono sui soli dati della riga.
NEEDS_RULE = {7, 19, 20, 21, 22, 23, 26, 28, 30, 31, 34, 36, 37, 38, 39, 46, 47, 48, 49, 50, 55, 56, 57, 58}

_SEEDED: set = set()


def _typed(raw: Optional[str]) -> Any:
    if raw is None:
        return None
    if raw[:1] in "[{":
        try:
            return json.loads(raw)
        except ValueError:
            return raw
    if raw in ("true", "false"):
        return raw == "true"
    try:
        return int(raw) if raw.lstrip("-").isdigit() else float(raw)
    except ValueError:
        return raw


def seed() -> None:
    """Carica (o aggiorna) il catalogo curato. Le regole con origine diversa da CURATED_SOURCE (es. revisione umana) non si toccano."""
    with connect() as conn:
        tomb = {r["bando_id"] for r in conn.execute("SELECT bando_id FROM bando_tombstones").fetchall()}
        for b in BANDI:
            if b["bando_id"] in tomb:
                continue  # eliminato dal manager
            rules = dict(b["rules"])
            if b["bando_id"] == "QUANTO-SANDBOX-60":
                rules = {k: v for k, v in SANDBOX_RULES.items() if k not in IDENTITY_FIELDS}
            partial = b["bando_id"] == "FNC3-2024"
            period = b.get("period") or {}
            conn.execute(
                "INSERT INTO bandi (bando_id, name, issuer, deadline, source_url, catalog_status, extraction_status) VALUES (?,?,?,?,?,?,?) "
                "ON CONFLICT(bando_id) DO UPDATE SET name=excluded.name, issuer=excluded.issuer, deadline=excluded.deadline, "
                "source_url=excluded.source_url, catalog_status='CURATED', extraction_status=excluded.extraction_status",
                (b["bando_id"], b["name"], b["issuer"], period.get("to"), (b["sources"][0]["url"] if b["sources"] else None),
                 "CURATED", "PARTIAL" if partial else "COMPLETED"))
            meta = {k: b[k] for k in ("status", "period", "legal_refs", "benefit", "sources", "not_specified", "rule_notes")}
            meta["curated"] = True
            conn.execute("INSERT INTO bando_meta (bando_id, meta) VALUES (?,?) ON CONFLICT(bando_id) DO UPDATE SET meta=excluded.meta",
                         (b["bando_id"], json.dumps(meta, ensure_ascii=False)))
            conn.execute("DELETE FROM rules WHERE bando_id=? AND origin='CURATED_SOURCE'", (b["bando_id"],))
            for key, value in rules.items():
                note = b["rule_notes"].get(key, {})
                conn.execute(
                    "INSERT INTO rules (bando_id, rule_key, value, origin, status, passes, source_ref) VALUES (?,?,?,?,?,?,?) "
                    "ON CONFLICT(bando_id, rule_key) DO NOTHING",
                    (b["bando_id"], key, normalize_value(key, value), "CURATED_SOURCE", "PUBLISHED", None, note.get("source")))
            conn.execute("DELETE FROM requirements WHERE bando_id=? AND origin='CURATED_SOURCE'", (b["bando_id"],))
            for i, r in enumerate(b["requirements"], 1):
                conn.execute("INSERT INTO requirements (bando_id, seq, topic, kind, text, criteria, source_ref, origin) VALUES (?,?,?,?,?,?,?,?) "
                             "ON CONFLICT (bando_id, seq) DO UPDATE SET topic=excluded.topic, kind=excluded.kind, text=excluded.text, criteria=excluded.criteria, source_ref=excluded.source_ref, origin=excluded.origin",
                             (b["bando_id"], i, r["topic"], r["kind"], r["text"], json.dumps(r["criteria"]),
                              f'{r["source_ref"]} [{r["confidence"]}]', "CURATED_SOURCE"))


def ensure_seeded() -> None:
    key = (db.database_url(), db.GENERATION)
    if key in _SEEDED:
        return
    seed()
    _SEEDED.add(key)


def coverage(rule_keys: List[str]) -> List[Dict[str, Any]]:
    """Per ciascuno dei 60 criteri: attivato da una regola del bando, eseguibile sui soli dati, oppure non attivo."""
    active: Dict[int, List[str]] = {}
    for key in rule_keys:
        for n in RULE_CRITERIA.get(key, []):
            active.setdefault(n, []).append(key)
    out = []
    for n, title in sorted(CRITERIA_TITLES.items()):
        if n in active:
            status = "REGOLA_DEL_BANDO"
        elif n in NEEDS_RULE:
            status = "NON_ATTIVO"
        else:
            status = "SOLO_DATI"
        out.append({"criterion": n, "title": title, "status": status, "via": active.get(n, [])})
    return out


def _summary(cov: List[Dict[str, Any]]) -> Dict[str, int]:
    return {s: sum(1 for c in cov if c["status"] == s) for s in ("REGOLA_DEL_BANDO", "SOLO_DATI", "NON_ATTIVO")}


def _meta(conn, bando_id: str) -> Dict[str, Any]:
    row = conn.execute("SELECT meta FROM bando_meta WHERE bando_id=?", (bando_id,)).fetchone()
    return json.loads(row["meta"]) if row else {}


def list_bandi() -> List[Dict[str, Any]]:
    """Elenco pubblico: solo i bandi curati o con una ricerca che ha prodotto qualcosa (regole, requisiti, fonti, run).

    Il catalogo nazionale (Fonte A, aggiornato ogni notte da ``catalog_job``) può contenere migliaia di voci di sole
    metadati (``CAT-*``): filtrarle qui in SQL — invece di leggerle tutte e scartarle in Python con 4-5 interrogazioni
    a testa — evita che l'elenco pubblico faccia decine di migliaia di andate e ritorni al database a ogni apertura
    della pagina Bandi.
    """
    ensure_seeded()
    out = []
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM bandi b WHERE b.catalog_status='CURATED' "
            "OR EXISTS (SELECT 1 FROM rules r WHERE r.bando_id=b.bando_id) "
            "OR EXISTS (SELECT 1 FROM requirements q WHERE q.bando_id=b.bando_id) "
            "OR EXISTS (SELECT 1 FROM bando_sources s WHERE s.bando_id=b.bando_id) "
            "OR EXISTS (SELECT 1 FROM runs ru WHERE ru.bando_id=b.bando_id AND ru.kind='VALIDATE') "
            "ORDER BY CASE b.catalog_status WHEN 'CURATED' THEN 0 ELSE 1 END, b.bando_id"
        ).fetchall()
        for b in rows:
            bid = b["bando_id"]
            meta = _meta(conn, bid)
            rules = conn.execute("SELECT rule_key, status FROM rules WHERE bando_id=?", (bid,)).fetchall()
            published = [r["rule_key"] for r in rules if r["status"] == "PUBLISHED"]
            reqs = conn.execute("SELECT COUNT(*) c, COALESCE(SUM((kind='DA_REVISIONARE')::int),0) r FROM requirements WHERE bando_id=?", (bid,)).fetchone()
            runs = conn.execute("SELECT COUNT(*) c, MAX(ts) t FROM runs WHERE bando_id=? AND kind='VALIDATE'", (bid,)).fetchone()
            out.append({
                "bando_id": bid, "name": b["name"], "issuer": b["issuer"], "status": meta.get("status") or ("IN LAVORAZIONE" if b["extraction_status"] != "COMPLETED" else "ESTRATTO"),
                "period": meta.get("period"), "curated": bool(meta.get("curated")), "extraction_status": b["extraction_status"],
                "benefit_type": (meta.get("benefit") or {}).get("type"), "rules_count": len(published),
                "rules_pending": sum(1 for r in rules if r["status"] == "PENDING_REVIEW"),
                "requirements_count": reqs["c"] or 0, "requirements_to_review": int(reqs["r"] or 0),
                "sources_count": len(meta.get("sources", [])), "gaps_count": len(meta.get("not_specified", [])),
                "coverage": _summary(coverage(published)), "runs_count": runs["c"], "last_run_ts": runs["t"],
            })
    return out


def get_bando_detail(bando_id: str) -> Optional[Dict[str, Any]]:
    ensure_seeded()
    with connect() as conn:
        b = conn.execute("SELECT * FROM bandi WHERE bando_id=?", (bando_id,)).fetchone()
        if b is None:
            return None
        meta = _meta(conn, bando_id)
        notes = meta.get("rule_notes", {})
        rule_rows = conn.execute("SELECT * FROM rules WHERE bando_id=? ORDER BY rule_key", (bando_id,)).fetchall()
        req_rows = conn.execute("SELECT * FROM requirements WHERE bando_id=? ORDER BY seq", (bando_id,)).fetchall()
        runs = conn.execute("SELECT id, ts, project_id, merkle_root FROM runs WHERE bando_id=? AND kind='VALIDATE' ORDER BY id DESC LIMIT 15", (bando_id,)).fetchall()
        docs = conn.execute("SELECT id, ts, kind, name, sha256, size_bytes FROM documents WHERE bando_id=? ORDER BY id DESC LIMIT 15", (bando_id,)).fetchall()
        sources = conn.execute("SELECT ts, name, sha256, LENGTH(text) AS chars, url, tier, pages, origin, content_type, text FROM bando_sources WHERE bando_id=? "
                               "ORDER BY CASE tier WHEN 'UFFICIALE' THEN 0 WHEN 'SECONDARIA' THEN 2 ELSE 1 END, ts DESC", (bando_id,)).fetchall()
    rules = [{
        "key": r["rule_key"], "value": _typed(r["value"]), "status": r["status"], "origin": r["origin"], "source_ref": r["source_ref"],
        "confidence": notes.get(r["rule_key"], {}).get("confidence") or ("PARSING" if r["origin"] == "STRUCTURED_PARSING" else r["origin"]),
        "criteria": RULE_CRITERIA.get(r["rule_key"], []), "passes": json.loads(r["passes"]) if r["passes"] else None,
    } for r in rule_rows]
    source_rows = [dict(s) for s in sources]
    found_refs = extract_legal_refs("\n".join(research.focus_text(s.pop("text") or "", b["name"]) for s in source_rows)) if source_rows else []
    legal_refs = list(dict.fromkeys([*meta.get("legal_refs", []), *found_refs]))
    published_keys = [r["key"] for r in rules if r["status"] == "PUBLISHED"]
    cov = coverage(published_keys)
    rule_set, _ = Ingestion.build_rule_set(bando_id)
    return {
        "bando_id": bando_id, "name": b["name"], "issuer": b["issuer"], "status": meta.get("status"), "period": meta.get("period"),
        "curated": bool(meta.get("curated")), "extraction_status": b["extraction_status"], "legal_refs": legal_refs,
        "benefit": meta.get("benefit"), "sources": meta.get("sources", []), "not_specified": meta.get("not_specified", []),
        "rules": rules,
        "requirements": [{"seq": r["seq"], "topic": r["topic"], "kind": r["kind"], "text": r["text"], "criteria": json.loads(r["criteria"]),
                          "source_ref": r["source_ref"], "origin": r["origin"]} for r in req_rows],
        "coverage": cov, "coverage_summary": _summary(cov),
        "grant_rules": rule_set.model_dump(mode="json") if rule_set else None,
        "usage": {"runs": [dict(r) for r in runs], "documents": [dict(d) for d in docs], "uploaded_sources": source_rows},
    }


def references() -> List[Dict[str, Any]]:
    return REFERENCES


# ------------------------------------------------------------------ ricerca per nome nel catalogo interno (schema FKOS, «Cliente cerca il bando»)
def _fold(text: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def search_catalog(query: str, limit: int = 8) -> List[Dict[str, Any]]:
    """Bandi già in memoria che assomigliano al nome cercato (esatto o approssimato). Non tocca la rete."""
    import difflib
    ensure_seeded()
    q = _fold(query)
    if len(q) < 2:
        return []
    q_tokens = q.split()
    with connect() as conn:
        rows = conn.execute("SELECT b.bando_id, b.name, b.issuer, b.source_url, b.deadline, b.catalog_status, b.extraction_status, "
                            "(SELECT COUNT(*) FROM rules r WHERE r.bando_id=b.bando_id AND r.status='PUBLISHED') AS rules, "
                            "(SELECT COUNT(*) FROM bando_sources s WHERE s.bando_id=b.bando_id) AS sources, "
                            "(SELECT COUNT(*) FROM requirements q2 WHERE q2.bando_id=b.bando_id) AS reqs FROM bandi b").fetchall()
    out = []
    for r in rows:
        catalogued = r["bando_id"].startswith("CAT-") and r["source_url"]          # voce del catalogo nazionale: solo metadati, ma è un bando vero
        if r["catalog_status"] != "CURATED" and not catalogued and not (r["rules"] or r["sources"] or r["reqs"]):
            continue                                      # ricerche senza esito: non sono bandi da proporre
        name = _fold(r["name"] + " " + (r["issuer"] or ""))
        tokens = name.split()
        hit = sum(1 for t in q_tokens if any(n == t or n.startswith(t) or (len(t) >= 4 and t in n) or (len(t) >= 4 and difflib.SequenceMatcher(None, t, n).ratio() >= 0.8) for n in tokens)) / len(q_tokens)
        ratio = difflib.SequenceMatcher(None, q, _fold(r["name"])).ratio()
        score = round(0.65 * hit + 0.35 * ratio, 3)
        if q in name:
            score = max(score, 0.95)
        if score >= 0.4:
            out.append({"bando_id": r["bando_id"], "name": r["name"], "issuer": r["issuer"], "extraction_status": r["extraction_status"], "curated": r["catalog_status"] == "CURATED",
                        "rules": r["rules"], "sources": r["sources"], "requirements": r["reqs"], "cache_hit": r["rules"] > 0, "score": score,
                        "catalog_only": bool(catalogued and not (r["rules"] or r["sources"])), "source_url": r["source_url"], "deadline": r["deadline"]})
    out.sort(key=lambda x: (-x["score"], x["name"]))
    return out[:limit]


# ------------------------------------------------------------------ sfoglia tutto il catalogo (curati + migliaia di voci nazionali)
def catalog_issuers() -> List[str]:
    """Elenco degli enti presenti nel catalogo, per il filtro della sfoglia (poche decine di valori: veloce anche su migliaia di righe)."""
    ensure_seeded()
    with connect() as conn:
        rows = conn.execute("SELECT DISTINCT issuer FROM bandi WHERE issuer IS NOT NULL AND issuer <> '' ORDER BY 1").fetchall()
    return [r["issuer"] for r in rows]


def browse_catalog(query: str = "", issuer: Optional[str] = None, only_new: bool = False, page: int = 1, page_size: int = 30) -> Dict[str, Any]:
    """Elenco paginato di TUTTI i bandi in memoria (i curati e le voci del catalogo nazionale), con ricerca libera ed
    eventuale filtro per ente. ``only_new`` mostra solo le voci non ancora analizzate (né curate né con regole/requisiti/
    fonti già estratti): quelle da cui partire per allargare la libreria. Il filtro sta nella query SQL, non in Python:
    con migliaia di righe è l'unico modo per restare veloci (vedi il commento su ``list_bandi``)."""
    ensure_seeded()
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    where, params = [], []
    q = query.strip()
    if q:
        where.append("(b.name ILIKE ? OR b.issuer ILIKE ?)")
        params += [f"%{q}%", f"%{q}%"]
    if issuer:
        where.append("b.issuer = ?")
        params.append(issuer)
    if only_new:
        where.append("b.catalog_status <> 'CURATED' AND NOT EXISTS (SELECT 1 FROM rules r WHERE r.bando_id=b.bando_id) "
                      "AND NOT EXISTS (SELECT 1 FROM bando_sources s WHERE s.bando_id=b.bando_id)")
    clause = ("WHERE " + " AND ".join(where)) if where else ""
    with connect() as conn:
        total = conn.execute(f"SELECT COUNT(*) c FROM bandi b {clause}", params).fetchone()["c"]
        rows = conn.execute(
            f"SELECT b.bando_id, b.name, b.issuer, b.source_url, b.deadline, b.catalog_status, b.extraction_status, "
            "(SELECT COUNT(*) FROM rules r WHERE r.bando_id=b.bando_id AND r.status='PUBLISHED') AS rules, "
            "(SELECT COUNT(*) FROM bando_sources s WHERE s.bando_id=b.bando_id) AS sources, "
            "(SELECT COUNT(*) FROM requirements q2 WHERE q2.bando_id=b.bando_id) AS reqs "
            f"FROM bandi b {clause} ORDER BY CASE b.catalog_status WHEN 'CURATED' THEN 0 ELSE 1 END, b.name "
            "LIMIT ? OFFSET ?", params + [page_size, (page - 1) * page_size]).fetchall()
    items = [{
        "bando_id": r["bando_id"], "name": r["name"], "issuer": r["issuer"], "source_url": r["source_url"], "deadline": r["deadline"],
        "curated": r["catalog_status"] == "CURATED", "extraction_status": r["extraction_status"],
        "rules": r["rules"], "sources": r["sources"], "requirements": r["reqs"],
        "catalog_only": r["catalog_status"] != "CURATED" and not (r["rules"] or r["sources"]),
    } for r in rows]
    return {"total": total, "page": page, "page_size": page_size, "pages": max(1, -(-total // page_size)), "items": items}
