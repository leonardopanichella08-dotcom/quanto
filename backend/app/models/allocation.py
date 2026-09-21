"""Schemi tipizzati della Missione Due (allocazione annuale multi-fonte, Modulo 12)."""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.schemas import CostCategory


class OptimizationTarget(str, Enum):
    MINIMIZE_NET_COST = "MINIMIZE_NET_COST"
    MAXIMIZE_COVERED_ITEMS = "MAXIMIZE_COVERED_ITEMS"
    MINIMIZE_FUNDS_INVOLVED = "MINIMIZE_FUNDS_INVOLVED"


class ExpenseLine(BaseModel):
    item_id: str = Field(..., min_length=1, max_length=64)
    category: CostCategory
    amount_eur: float = Field(..., gt=0)
    month: Optional[int] = Field(default=None, ge=1, le=12, description="Mese di competenza; se assente la spesa è ripartita su 12 mesi")


class FundingLine(BaseModel):
    fund_id: str = Field(..., min_length=1, max_length=64)
    name: Optional[str] = None
    allowed_categories: List[CostCategory]
    coverage_pct: float = Field(default=0.80, gt=0, le=1, description="Intensità massima di copertura per voce")
    category_coverage_pct: Dict[CostCategory, float] = Field(default_factory=dict, description="Intensità per categoria (sovrascrive coverage_pct)")
    max_total_eur: Optional[float] = Field(default=None, gt=0, description="Dotazione massima erogabile dal fondo all'ente")
    category_max_share: Dict[CostCategory, float] = Field(default_factory=dict, description="Quota massima per categoria sul totale coperto dal fondo (criteri 31/36)")
    de_minimis: bool = Field(default=False, description="Se true, il fondo consuma il plafond de minimis (criterio 49)")
    excludes: List[str] = Field(default_factory=list, description="Fondi non cumulabili sulla stessa voce (criterio 47)")
    active_from_month: int = Field(default=1, ge=1, le=12)
    active_to_month: int = Field(default=12, ge=1, le=12)

    @field_validator("category_coverage_pct", "category_max_share")
    @classmethod
    def _unit_interval(cls, v: Dict[CostCategory, float]) -> Dict[CostCategory, float]:
        if any(not 0 < x <= 1 for x in v.values()):
            raise ValueError("Le percentuali devono essere in (0, 1]")
        return v

    @model_validator(mode="after")
    def _window(self) -> "FundingLine":
        if self.active_from_month > self.active_to_month:
            raise ValueError("active_from_month deve essere <= active_to_month")
        return self


class AllocationOptimizationRequest(BaseModel):
    fiscal_year: int = Field(default=2027, ge=2020, le=2100)
    historical_balance_ref: Optional[int] = Field(default=None, description="Identificativo del bilancio caricato (Fonte C): le spese si leggono da lì")
    historical_expenses: List[ExpenseLine] = Field(default_factory=list, description="In alternativa al bilancio: spese fornite dal chiamante (es. gestionale)")
    available_funding_lines: List[FundingLine] = Field(default_factory=list, description="Se vuoto si usano le linee di finanziamento attive (ricavate dai bandi)")
    optimization_target: OptimizationTarget = OptimizationTarget.MINIMIZE_NET_COST
    excluded_funds: List[str] = Field(default_factory=list, description="What-if: fondi che l'utente esclude manualmente")
    de_minimis_residual_eur: Optional[float] = Field(default=None, ge=0, description="Plafond de minimis residuo nel triennio mobile")
    min_saving_ratio: float = Field(default=0.90, gt=0, le=1, description="Solo MINIMIZE_FUNDS_INVOLVED: quota minima del risparmio massimo da preservare")

    @model_validator(mode="after")
    def _unique(self) -> "AllocationOptimizationRequest":
        if self.historical_balance_ref is not None and self.historical_expenses:
            raise ValueError("Indica il bilancio (historical_balance_ref) oppure le spese (historical_expenses), non entrambi")
        for label, ids in (("item_id", [e.item_id for e in self.historical_expenses]), ("fund_id", [f.fund_id for f in self.available_funding_lines])):
            if len(ids) != len(set(ids)):
                raise ValueError(f"{label} duplicati")
        if self.de_minimis_residual_eur is None and any(f.de_minimis for f in self.available_funding_lines):
            raise ValueError("de_minimis_residual_eur è obbligatorio se almeno un fondo è in regime de minimis")
        return self


class FundCoverage(BaseModel):
    fund_id: str
    covered_amount_eur: float
    coverage_percentage: float


class AllocationLine(BaseModel):
    item_id: str
    category: CostCategory
    cost_category: Optional[str] = Field(default=None, description="Nome dello schema API: come category")
    amount_eur: Optional[float] = Field(default=None, description="Nome dello schema API: come gross_amount_eur")
    covered_by: Optional[str] = Field(default=None, description="Nome dello schema API: come assigned_fund")
    gross_amount_eur: float
    covered_amount_eur: float
    net_cost_to_entity_eur: float
    coverage_percentage: float
    assigned_fund: str
    coverage: List[FundCoverage]


class FundUsage(BaseModel):
    fund_id: str
    used_eur: float
    cap_eur: Optional[float]
    remaining_eur: Optional[float]
    safety_margin_pct: Optional[float]


class MonthlyPlanEntry(BaseModel):
    month: int
    gross_eur: float
    covered_eur: float
    net_eur: float
    by_fund: Dict[str, float]


class AllocationResponse(BaseModel):
    status: str
    total_cost_eur: Optional[float] = Field(default=None, description="Nome dello schema API: come total_gross_expense_eur")
    covered_by_funds_eur: Optional[float] = Field(default=None, description="Nome dello schema API: come covered_by_public_funds_eur")
    fiscal_year: int
    optimization_target: OptimizationTarget
    excluded_funds: List[str]
    total_gross_expense_eur: float
    covered_by_public_funds_eur: float
    net_cost_to_entity_eur: float
    overall_coverage_percentage: float
    items_covered: int
    funds_involved: int
    de_minimis_used_eur: float
    de_minimis_residual_eur: Optional[float]
    allocation_plan: List[AllocationLine]
    fund_usage: List[FundUsage]
    monthly_plan: List[MonthlyPlanEntry]
    solver: str
    summary: str
