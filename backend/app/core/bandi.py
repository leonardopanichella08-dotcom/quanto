"""Biblioteca dei bandi: seed del catalogo curato, elenco, dettaglio e copertura dei 60 criteri."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from app.core.criteria_catalog import CRITERIA_TITLES
from app.core.db import connect, db_path
from app.core.demo import SANDBOX_RULES
from app.core.ingestion import IDENTITY_FIELDS, Ingestion, normalize_value
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
        for b in BANDI:
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
                conn.execute("INSERT OR REPLACE INTO requirements (bando_id, seq, topic, kind, text, criteria, source_ref, origin) VALUES (?,?,?,?,?,?,?,?)",
                             (b["bando_id"], i, r["topic"], r["kind"], r["text"], json.dumps(r["criteria"]),
                              f'{r["source_ref"]} [{r["confidence"]}]', "CURATED_SOURCE"))


def ensure_seeded() -> None:
    key = db_path()
    if key in _SEEDED and os.path.exists(key):
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
    ensure_seeded()
    out = []
    with connect() as conn:
        for b in conn.execute("SELECT * FROM bandi ORDER BY CASE catalog_status WHEN 'CURATED' THEN 0 ELSE 1 END, bando_id").fetchall():
            bid = b["bando_id"]
            meta = _meta(conn, bid)
            rules = conn.execute("SELECT rule_key, status FROM rules WHERE bando_id=?", (bid,)).fetchall()
            published = [r["rule_key"] for r in rules if r["status"] == "PUBLISHED"]
            reqs = conn.execute("SELECT COUNT(*) c, SUM(kind='DA_REVISIONARE') r FROM requirements WHERE bando_id=?", (bid,)).fetchone()
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
        sources = conn.execute("SELECT ts, name, sha256, LENGTH(text) AS chars FROM bando_sources WHERE bando_id=? ORDER BY ts DESC", (bando_id,)).fetchall()
    rules = [{
        "key": r["rule_key"], "value": _typed(r["value"]), "status": r["status"], "origin": r["origin"], "source_ref": r["source_ref"],
        "confidence": notes.get(r["rule_key"], {}).get("confidence") or ("PARSING" if r["origin"] == "STRUCTURED_PARSING" else r["origin"]),
        "criteria": RULE_CRITERIA.get(r["rule_key"], []), "passes": json.loads(r["passes"]) if r["passes"] else None,
    } for r in rule_rows]
    published_keys = [r["key"] for r in rules if r["status"] == "PUBLISHED"]
    cov = coverage(published_keys)
    rule_set, _ = Ingestion.build_rule_set(bando_id)
    return {
        "bando_id": bando_id, "name": b["name"], "issuer": b["issuer"], "status": meta.get("status"), "period": meta.get("period"),
        "curated": bool(meta.get("curated")), "extraction_status": b["extraction_status"], "legal_refs": meta.get("legal_refs", []),
        "benefit": meta.get("benefit"), "sources": meta.get("sources", []), "not_specified": meta.get("not_specified", []),
        "rules": rules,
        "requirements": [{"seq": r["seq"], "topic": r["topic"], "kind": r["kind"], "text": r["text"], "criteria": json.loads(r["criteria"]),
                          "source_ref": r["source_ref"], "origin": r["origin"]} for r in req_rows],
        "coverage": cov, "coverage_summary": _summary(cov),
        "grant_rules": rule_set.model_dump(mode="json") if rule_set else None,
        "usage": {"runs": [dict(r) for r in runs], "documents": [dict(d) for d in docs], "uploaded_sources": [dict(s) for s in sources]},
    }


def references() -> List[Dict[str, Any]]:
    return REFERENCES
