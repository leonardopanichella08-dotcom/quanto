"""Assembla il PDF del business plan 2026-2028."""
from __future__ import annotations

from pathlib import Path

from . import bp, bp_doc, bp_fin, bp_more, model as M
from .pdfkit import Doc


def make_business_plan(path: Path) -> Path:
    bp.check()
    d = Doc(path, "Business plan 2026-2028", M.COMPANY["name"], "Business plan 2026-2028")
    bp_doc.cover_and_summary(d)
    bp_doc.company(d)
    bp_more.history(d)
    bp_doc.products(d)
    bp_more.modules(d)
    bp_doc.market(d)
    bp_more.market_more(d)
    bp_doc.competition(d)
    bp_doc.go_to_market(d)
    bp_more.marketing_more(d)
    bp_doc.operations(d)
    bp_more.operations_more(d)
    bp_doc.people(d)
    bp_more.people_more(d)
    bp_doc.investments(d)
    bp_more.rd_more(d)
    bp_doc.assumptions(d)
    bp_fin.annual_financials(d)
    bp_more.notes_to_plan(d)
    bp_fin.quarterly(d)
    bp_fin.financing(d)
    bp_fin.kpi(d)
    bp_fin.scenarios(d)
    bp_fin.risks(d)
    bp_fin.governance(d)
    bp_fin.annex_monthly_pl(d)
    bp_fin.annex_monthly_cash(d)
    bp_fin.annex_staff(d)
    bp_fin.annex_history(d)
    bp_more.annex_customers(d)
    bp_more.annex_depreciation(d)
    bp_fin.annex_glossary(d)
    return d.save()
