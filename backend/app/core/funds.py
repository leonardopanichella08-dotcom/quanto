"""Linee di finanziamento per l'allocazione annuale (Modulo 12, passo 2): i fondi arrivano dai bandi (Fonte A), non dal codice.

Una linea si ricava dalle regole PUBBLICATE di un bando (categorie ammesse, intensità del contributo, finestra di
ammissibilità, fondi non cumulabili, tetti % di consulenze e spese generali). Ciò che il bando non dice — dotazione massima,
regime de minimis — non si inventa: lo indica una persona, oppure resta vuoto (= nessun tetto dichiarato).
"""
from __future__ import annotations

import hashlib
import json
from datetime import date
from typing import Any, Dict, List, Optional

from app.core import events
from app.core.db import connect
from app.core.ingestion import Ingestion
from app.models.allocation import FundingLine
from app.models.schemas import CostCategory


class FundError(ValueError):
    pass


def _row(r) -> Dict[str, Any]:
    d = dict(r)
    for k in ("allowed_categories", "category_coverage_pct", "category_max_share", "excludes"):
        d[k] = json.loads(d[k]) if d.get(k) else ([] if k in ("allowed_categories", "excludes") else {})
    for k in ("coverage_pct", "max_total_eur"):
        d[k] = float(d[k]) if d.get(k) is not None else None
    return d


def list_funds(active_only: bool = False) -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM funding_lines " + ("WHERE active " if active_only else "") + "ORDER BY fund_id").fetchall()
    return [_row(r) for r in rows]


def upsert_fund(fund: Dict[str, Any], actor: str) -> Dict[str, Any]:
    """Crea o aggiorna una linea. I dati passano dalla stessa validazione che usa il risolutore."""
    try:
        line = FundingLine(**{k: fund[k] for k in fund if k in FundingLine.model_fields})
    except Exception as exc:
        raise FundError(str(exc)) from exc
    if not line.allowed_categories:
        raise FundError("Indica almeno una categoria di spesa ammessa")
    with connect() as conn:
        conn.execute(
            "INSERT INTO funding_lines (fund_id, name, bando_id, allowed_categories, coverage_pct, category_coverage_pct, max_total_eur, category_max_share, de_minimis, "
            "excludes, active_from_month, active_to_month, source_ref, active, updated_by, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT (fund_id) DO UPDATE SET name=excluded.name, bando_id=excluded.bando_id, allowed_categories=excluded.allowed_categories, coverage_pct=excluded.coverage_pct, "
            "category_coverage_pct=excluded.category_coverage_pct, max_total_eur=excluded.max_total_eur, category_max_share=excluded.category_max_share, de_minimis=excluded.de_minimis, "
            "excludes=excluded.excludes, active_from_month=excluded.active_from_month, active_to_month=excluded.active_to_month, source_ref=excluded.source_ref, "
            "active=excluded.active, updated_by=excluded.updated_by, updated_at=excluded.updated_at",
            (line.fund_id, line.name or line.fund_id, fund.get("bando_id"), json.dumps([c.value for c in line.allowed_categories]), line.coverage_pct,
             json.dumps({k.value: v for k, v in line.category_coverage_pct.items()}), line.max_total_eur, json.dumps({k.value: v for k, v in line.category_max_share.items()}),
             line.de_minimis, json.dumps(line.excludes), line.active_from_month, line.active_to_month, fund.get("source_ref"), bool(fund.get("active", True)),
             actor, events.now_iso()))
        out = _row(conn.execute("SELECT * FROM funding_lines WHERE fund_id=?", (line.fund_id,)).fetchone())
    events.record("funds.upsert", f"Linea di finanziamento {line.fund_id} salvata", actor=actor, bando_id=fund.get("bando_id"))
    return out


def delete_fund(fund_id: str, actor: str) -> bool:
    with connect() as conn:
        n = conn.execute("DELETE FROM funding_lines WHERE fund_id=?", (fund_id,)).rowcount
    if n:
        events.record("funds.delete", f"Linea di finanziamento {fund_id} eliminata", actor=actor)
    return bool(n)


def _months(start: Optional[date], end: Optional[date], year: int) -> tuple:
    """Mesi in cui la finestra di ammissibilità cade nell'anno fiscale (1-12 se non c'è finestra)."""
    first = 1 if start is None or start.year < year else (start.month if start.year == year else 13)
    last = 12 if end is None or end.year > year else (end.month if end.year == year else 0)
    return first, last


def _typed(key: str, value: str):
    """Valore di una regola pubblicata, con il tipo del campo di GrantRuleSet."""
    from pydantic import TypeAdapter
    from app.models.schemas import GrantRuleSet
    raw: Any = value
    if isinstance(raw, str) and raw[:1] in "[{":
        raw = json.loads(raw)
    return TypeAdapter(GrantRuleSet.model_fields[key].annotation).validate_python(raw)


def derive_from_bando(bando_id: str, fiscal_year: int, actor: str, max_total_eur: Optional[float] = None, de_minimis: bool = False,
                      fund_id: Optional[str] = None) -> Dict[str, Any]:
    """Crea la linea dalle regole PUBBLICATE del bando. Errore chiaro se mancano le regole necessarie."""
    bando = Ingestion.get_bando(bando_id)
    if bando is None:
        raise FundError("Bando non trovato")
    with connect() as conn:
        rows = conn.execute("SELECT rule_key, value FROM rules WHERE bando_id=? AND status='PUBLISHED'", (bando_id,)).fetchall()
    vals = {r["rule_key"]: _typed(r["rule_key"], r["value"]) for r in rows if r["value"] is not None}
    if not vals:
        raise FundError("Il bando non ha regole pubblicate")
    if vals.get("contribution_rate_pct") is None:
        raise FundError("Il bando non indica la percentuale di contributo (contribution_rate_pct): non si può ricavare un'intensità di copertura. Aggiungila nell'archivio del bando.")
    rule_set = type("Rules", (), {"bando_name": bando["name"], "contribution_rate_pct": float(vals["contribution_rate_pct"]),
                                  "eligible_categories": vals.get("eligible_categories"), "eligibility_start": vals.get("eligibility_start"),
                                  "eligibility_end": vals.get("eligibility_end"), "max_consulting_percentage": vals.get("max_consulting_percentage"),
                                  "max_overhead_percentage": vals.get("max_overhead_percentage"), "non_cumulable_funding_ids": vals.get("non_cumulable_funding_ids") or [],
                                  "rule_version_hash": hashlib.sha256(json.dumps({r["rule_key"]: r["value"] for r in rows}, sort_keys=True).encode()).hexdigest()})()
    cats = [CostCategory(c) for c in rule_set.eligible_categories] if rule_set.eligible_categories else list(CostCategory)
    first, last = _months(rule_set.eligibility_start, rule_set.eligibility_end, fiscal_year)
    if first > last:
        raise FundError(f"La finestra di ammissibilità del bando non cade nell'anno {fiscal_year}")
    share = {}
    if rule_set.max_consulting_percentage is not None:
        share[CostCategory.CONSULTING] = rule_set.max_consulting_percentage
    if rule_set.max_overhead_percentage is not None:
        share[CostCategory.OVERHEAD] = rule_set.max_overhead_percentage
    fund = {"fund_id": fund_id or bando_id, "name": rule_set.bando_name, "bando_id": bando_id, "allowed_categories": cats, "coverage_pct": rule_set.contribution_rate_pct,
            "category_max_share": share, "excludes": list(rule_set.non_cumulable_funding_ids), "active_from_month": first, "active_to_month": last,
            "max_total_eur": max_total_eur, "de_minimis": de_minimis, "source_ref": f"regole pubblicate del bando {bando_id} (versione {rule_set.rule_version_hash[:12]})"}
    return upsert_fund(fund, actor)


def funding_lines_for_allocation() -> List[FundingLine]:
    """Linee attive, nel formato del risolutore."""
    out = []
    for d in list_funds(active_only=True):
        out.append(FundingLine(fund_id=d["fund_id"], name=d["name"], allowed_categories=d["allowed_categories"], coverage_pct=d["coverage_pct"],
                               category_coverage_pct=d["category_coverage_pct"], max_total_eur=d["max_total_eur"], category_max_share=d["category_max_share"],
                               de_minimis=d["de_minimis"], excludes=d["excludes"], active_from_month=d["active_from_month"], active_to_month=d["active_to_month"]))
    return out
