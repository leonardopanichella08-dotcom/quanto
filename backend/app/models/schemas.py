"""Modelli dati di dominio, enumerazioni e schemi API di QUANTO (Parte 2).

Regole di modellazione:
- il motore lavora in ``decimal.Decimal``; ai bordi API gli importi sono ``float``
  arrotondati ROUND_HALF_UP a 2 cifre (vedi ``money``);
- nessun campo di output espone PII (nomi, codici fiscali, IBAN): i lavoratori
  sono identificati solo da ``employee_token`` opaco (vedi anonymizer);
- i campi opzionali dei criteri: se un dato manca il criterio corrispondente NON viene eseguito e
  finisce in ``criteria_not_evaluated`` (mai un "passato" implicito).
"""
from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def money(value: Any) -> float:
    """Float a 2 cifre con ROUND_HALF_UP, passando da Decimal(str(x)) (mai da float binario)."""
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


# --------------------------------------------------------------------------- enums
class CostCategory(str, Enum):
    PERSONNEL = "PERSONNEL"
    CAPITAL_ASSETS = "CAPITAL_ASSETS"
    CONSULTING = "CONSULTING"
    OVERHEAD = "OVERHEAD"
    TRAINING = "TRAINING"


class CCNLType(str, Enum):
    TERZO_SETTORE = "TERZO_SETTORE"
    METALMECCANICA = "METALMECCANICA"
    COMMERCIO = "COMMERCIO"
    CREDITO = "CREDITO"


class ItemValidationStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CAP_EXCEEDED_ADJUSTED = "CAP_EXCEEDED_ADJUSTED"
    MISSING_DOCUMENTS = "MISSING_DOCUMENTS"


class ContractType(str, Enum):
    PERMANENT = "PERMANENT"
    FIXED_TERM = "FIXED_TERM"
    OCCASIONAL = "OCCASIONAL"


class ExpenseSubtype(str, Enum):
    COMMUNICATION = "COMMUNICATION"
    GUARANTEE = "GUARANTEE"
    AUDIT = "AUDIT"
    PENALTY = "PENALTY"
    LEGAL_DISPUTE = "LEGAL_DISPUTE"
    REPRESENTATION = "REPRESENTATION"
    RENT = "RENT"
    UTILITIES = "UTILITIES"
    MAINTENANCE_ORDINARY = "MAINTENANCE_ORDINARY"
    MAINTENANCE_EXTRAORDINARY = "MAINTENANCE_EXTRAORDINARY"
    FINANCIAL_CHARGES = "FINANCIAL_CHARGES"  # interessi, oneri del debito, perdite di cambio, spese bancarie


class AssetNature(str, Enum):
    HARDWARE = "HARDWARE"
    SOFTWARE = "SOFTWARE"
    SERVICE = "SERVICE"
    IMMATERIAL = "IMMATERIAL"
    REAL_ESTATE = "REAL_ESTATE"  # terreni e fabbricati


class FlatBase(str, Enum):
    """Base di calcolo del tasso forfettario dei costi indiretti."""

    PERSONNEL = "PERSONNEL"
    DIRECT_EXCL_SUBCONTRACTING = "DIRECT_EXCL_SUBCONTRACTING"


class ActivityType(str, Enum):
    PROJECT = "PROJECT"
    B2B = "B2B"
    B2G = "B2G"


# --------------------------------------------------------------------------- input
class CostItemInput(BaseModel):
    """Riga di spesa grezza da sottoporre a validazione deterministica."""

    model_config = ConfigDict(extra="forbid")  # un refuso nel nome di un campo deve dare errore, non essere ignorato

    item_id: str = Field(..., min_length=1, max_length=64, examples=["LINE-001"])
    description: str = Field(..., max_length=200, examples=["Project Manager Junior"])
    category: CostCategory = Field(..., examples=[CostCategory.PERSONNEL])
    source_c_ref: str = Field(..., description="Riferimento al documento contabile (Fonte C)", examples=["DOC-PAYROLL-2026-08"])

    # --- PERSONNEL (CCNL)
    ccnl_code: Optional[str] = Field(default=None, max_length=40, description="Sigla del CCNL (deve esistere in Fonte B: nessun contratto è assunto per default)")
    employee_level: str = Field(default="3", examples=["3"])
    ral_eur: Optional[float] = Field(default=None, gt=0, description="RAL dichiarata (solo PERSONNEL)", examples=[38000.0])
    fte_allocation: float = Field(default=1.0, gt=0, le=1.0, description="Quota di impegno sul progetto (FTE)")
    duration_months: int = Field(default=12, gt=0, le=36)
    working_hours_override: Optional[int] = Field(default=None, gt=0, le=2400)
    employee_token: Optional[str] = Field(default=None, max_length=64, description="Token opaco del lavoratore (mai il nome): criterio 8")
    contract_type: Optional[ContractType] = Field(default=None, description="Criteri 12-13")
    superminimo_eur: Optional[float] = Field(default=None, ge=0, description="Quota di RAL costituita da superminimo (criterio 6)")
    superminimo_recognized: Optional[bool] = Field(default=None, description="False = superminimo non assorbibile/unilaterale: escluso")
    overtime_hours: Optional[float] = Field(default=None, ge=0, description="Ore straordinarie imputate (criterio 11)")
    travel_allowance_eur: Optional[float] = Field(default=None, ge=0, description="Trasferte/diarie imputate (criterio 9)")
    travel_documented: Optional[bool] = None
    occasional_annual_income_eur: Optional[float] = Field(default=None, ge=0, description="Reddito annuo del collaboratore occasionale (criterio 13)")
    role_min_level: Optional[str] = Field(default=None, description="Livello minimo richiesto dal mansionario (criterio 14)")
    role_max_level: Optional[str] = None
    payslip_ral_eur: Optional[float] = Field(default=None, gt=0, description="RAL letta dalla busta paga reale (criterio 15)")
    activity_type: Optional[ActivityType] = Field(default=None, description="Criterio 10")
    activity_segregated: Optional[bool] = None

    # --- NON-PERSONNEL
    amount_eur: Optional[float] = Field(default=None, gt=0, description="Imponibile della voce (categorie diverse da PERSONNEL)")
    expense_subtype: Optional[ExpenseSubtype] = None
    vat_eur: Optional[float] = Field(default=None, ge=0, description="IVA sulla voce (criteri 25, 53, 54)")
    vat_recoverable: Optional[bool] = None
    reverse_charge_applied: Optional[bool] = None
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    fx_rate: Optional[float] = Field(default=None, gt=0, description="Cambio verso EUR (criterio 59)")

    # beni strumentali (16-30, 58)
    asset_nature: Optional[AssetNature] = None
    depreciation_rate_pct: Optional[float] = Field(default=None, gt=0, le=1, description="Aliquota d'ammortamento annua (criteri 17-18)")
    depreciation_category: Optional[str] = Field(default=None, max_length=40, description="Categoria di bene della tabella d'ammortamento di Fonte B: l'aliquota di tabella è il tetto")
    benchmark_category: Optional[str] = Field(default=None, max_length=40, description="Categoria di prezzo/tariffa di Fonte B per i criteri 22 e 33")
    is_new: Optional[bool] = None
    origin_eu: Optional[bool] = Field(default=None, description="Bene prodotto in UE/SEE (requisito di origine)")
    iot_interconnected: Optional[bool] = None
    energy_saving_pct: Optional[float] = Field(default=None, ge=0, le=1)
    market_benchmark_eur: Optional[float] = Field(default=None, gt=0, description="Prezzo di mercato di riferimento (Fonte B, criterio 22)")
    installation_cost_eur: Optional[float] = Field(default=None, ge=0)
    leasing_interest_eur: Optional[float] = Field(default=None, ge=0)
    dnsh_compliant: Optional[bool] = None
    exclusive_use: Optional[bool] = None
    sworn_appraisal_present: Optional[bool] = None
    post_closure_commitment_months: Optional[int] = Field(default=None, ge=0)

    # consulenze (32-35, 40, 45)
    supplier_related_party: Optional[bool] = None
    supplier_ateco: Optional[str] = Field(default=None, max_length=10)
    supplier_durc_valid: Optional[bool] = None
    subcontracted: Optional[bool] = None
    subcontract_authorized: Optional[bool] = None
    daily_rate_eur: Optional[float] = Field(default=None, gt=0)
    days: Optional[float] = Field(default=None, gt=0)
    benchmark_daily_rate_eur: Optional[float] = Field(default=None, gt=0)
    travel_cost_eur: Optional[float] = Field(default=None, ge=0)
    travel_included_in_fee: Optional[bool] = None

    # spese generali (41-44)
    rent_sqm_project: Optional[float] = Field(default=None, gt=0)
    rent_sqm_total: Optional[float] = Field(default=None, gt=0)
    rent_months_active: Optional[int] = Field(default=None, ge=0)
    allocation_method: Optional[str] = Field(default=None, max_length=120, description="Criterio di ripartizione delle utenze (criterio 43)")
    project_related: Optional[bool] = None

    # generali (46-52, 57)
    expense_date: Optional[date] = None
    funding_ids: Optional[List[str]] = Field(default=None, description="Altri contributi sulla stessa spesa (criterio 47); [] = nessuno")
    other_aid_eur: Optional[float] = Field(default=None, ge=0, description="Altri aiuti/crediti d'imposta sulla voce (criterio 48)")
    cup_code: Optional[str] = Field(default=None, max_length=15)
    cig_required: Optional[bool] = None
    cig_code: Optional[str] = Field(default=None, max_length=10)
    payment_method: Optional[str] = Field(default=None, max_length=20)
    milestone_id: Optional[str] = Field(default=None, max_length=32)

    @field_validator("ral_eur", "amount_eur")
    @classmethod
    def _round_money(cls, v: Optional[float]) -> Optional[float]:
        return None if v is None else money(v)

    @model_validator(mode="after")
    def _amount_required_by_category(self) -> "CostItemInput":
        if self.category == CostCategory.PERSONNEL:
            if self.ral_eur is None:
                raise ValueError("ral_eur obbligatoria per le voci PERSONNEL")
        elif self.amount_eur is None:
            raise ValueError(f"amount_eur obbligatorio per le voci {self.category.value}")
        return self


class GrantRuleSet(BaseModel):
    """Regole normativo-finanziarie del bando (Fonte A). Le regole ``None`` non sono definite dal bando."""

    model_config = ConfigDict(extra="forbid")

    bando_id: str = Field(..., examples=["TRANSIZIONE-5.0-2026"])
    bando_name: str = Field(..., examples=["Piano Transizione 5.0 - Efficienza Energetica"])
    # None = il bando non definisce la regola: il criterio corrispondente risulta "non valutato" (nessun default inventato)
    max_hourly_rate_personnel: Optional[float] = Field(default=None, gt=0, description="Tetto costo orario (€/ora)")
    max_consulting_percentage: Optional[float] = Field(default=None, ge=0, le=1)
    max_overhead_percentage: Optional[float] = Field(default=None, ge=0, le=1)
    eligible_categories: Optional[List[CostCategory]] = Field(default=None, description="Categorie di spesa ammesse dal bando (None = tutte)")
    rule_version_hash: str = Field(..., min_length=8, examples=["a8f3b129c9e840134012480a2"])

    # personale
    overtime_allowed: bool = False
    payroll_tolerance_pct: float = Field(default=0.01, ge=0, le=1)
    # beni
    requires_new_asset: bool = False
    vat_never_eligible: bool = Field(default=False, description="Il bando ammette solo costi al netto di IVA")
    requires_iot: bool = False
    min_energy_saving_pct: Optional[float] = Field(default=None, ge=0, le=1)
    max_price_deviation_pct: Optional[float] = Field(default=None, ge=0)
    max_installation_pct: Optional[float] = Field(default=None, ge=0)
    requires_dnsh: bool = False
    appraisal_threshold_eur: Optional[float] = Field(default=None, ge=0, description="Soglia oltre cui serve la perizia asseverata (0 = sempre)")
    excluded_asset_natures: List[AssetNature] = Field(default_factory=list)
    equipment_depreciation_only: bool = Field(default=False, description="Ammesso solo l'ammortamento dei beni (es. Horizon Europe)")
    requires_eu_origin: bool = False
    max_immaterial_pct: Optional[float] = Field(default=None, ge=0, le=1)
    min_durability_months: Optional[int] = Field(default=None, ge=0)
    # consulenze / spese generali
    require_independent_supplier: bool = True
    allowed_ateco_prefixes: List[str] = Field(default_factory=list)
    subcontracting_allowed: bool = False
    overhead_flat_rate_pct: Optional[float] = Field(default=None, ge=0, le=1, description="Tasso forfettario massimo dei costi indiretti")
    overhead_flat_base: FlatBase = FlatBase.PERSONNEL
    max_communication_pct: Optional[float] = Field(default=None, ge=0, le=1)
    guarantee_costs_eligible: Optional[bool] = None
    max_audit_cost_eur: Optional[float] = Field(default=None, gt=0)
    # tempo, cumulo, tracciabilità
    eligibility_start: Optional[date] = None
    eligibility_end: Optional[date] = None
    non_cumulable_funding_ids: List[str] = Field(default_factory=list)
    max_aid_intensity_pct: Optional[float] = Field(default=None, gt=0, le=1)
    contribution_rate_pct: Optional[float] = Field(default=None, gt=0, le=1)
    de_minimis_residual_eur: Optional[float] = Field(default=None, ge=0)
    requires_cup: bool = False
    blocked_payment_methods: List[str] = Field(default_factory=lambda: ["CASH", "CHECK"])
    requires_milestones: bool = False
    max_inter_chapter_variation_pct: Optional[float] = Field(default=None, ge=0)
    advance_pct: float = Field(default=0.0, ge=0, le=1)
    reimbursement_lag_months: Optional[int] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _caps_feasible(self) -> "GrantRuleSet":
        shares = (self.max_consulting_percentage or 0) + (self.max_overhead_percentage or 0)
        shares += self.max_communication_pct or 0
        shares += self.max_immaterial_pct or 0
        if shares >= 1:
            raise ValueError("La somma dei massimali percentuali (consulenze, spese generali, comunicazione, immateriali) deve essere < 100%")
        if self.eligibility_start and self.eligibility_end and self.eligibility_start > self.eligibility_end:
            raise ValueError("eligibility_start successiva a eligibility_end")
        return self


class BudgetValidationRequest(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=64, examples=["PRJ-2026-NEXUS"])
    grant_rules: GrantRuleSet
    cost_items: List[CostItemInput]
    entity_liquidity_eur: Optional[float] = Field(default=None, ge=0, description="Liquidità dell'ente per il criterio 55")
    baseline_totals: Optional[Dict[CostCategory, float]] = Field(default=None, description="Totali per capitolo del budget di riferimento (criterio 56)")
    reference_date: Optional[date] = Field(default=None, description="Data a cui si leggono le tabelle di Fonte B (default: oggi). Serve a ricalcolare lo stesso budget con le stesse tabelle")

    @model_validator(mode="after")
    def _unique_item_ids(self) -> "BudgetValidationRequest":
        ids = [i.item_id for i in self.cost_items]
        if len(ids) != len(set(ids)):
            raise ValueError("item_id duplicati: ogni riga deve avere un identificativo univoco")
        return self


class RegistrationRequest(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=64, examples=["PRJ-2026-NEXUS"])
    merkle_root: str = Field(..., pattern=r"^(0x)?[0-9a-fA-F]{64}$")


class PatternMatchRequest(BaseModel):
    bando_category: str = Field(..., examples=["FONDO_SPORT_PERIFERIE"])
    draft_budget: Dict[str, float] = Field(
        ..., examples=[{"personnel_pct": 0.58, "assets_pct": 0.12, "consulting_pct": 0.25, "overhead_pct": 0.05}]
    )

    @field_validator("draft_budget")
    @classmethod
    def _valid_shares(cls, v: Dict[str, float]) -> Dict[str, float]:
        allowed = {"personnel_pct", "assets_pct", "consulting_pct", "overhead_pct"}
        unknown = set(v) - allowed
        if unknown:
            raise ValueError(f"Categorie sconosciute: {sorted(unknown)}")
        if any(x < 0 for x in v.values()):
            raise ValueError("Le quote non possono essere negative")
        return v


# --------------------------------------------------------------------------- output
class CostBreakdown(BaseModel):
    """Scomposizione del calcolo, mostrata dall'Ispettore di Riga (nessun numero opaco)."""

    source_c_ref: str
    ccnl_table_ref: Optional[str] = Field(default=None, description="Tabella Fonte B usata (CCNL:livello:versione)")
    ral_eur: Optional[float] = None
    social_charges_pct: Optional[float] = None
    social_charges_eur: Optional[float] = None
    tfr_pct: Optional[float] = None
    tfr_eur: Optional[float] = None
    annual_cost_eur: Optional[float] = None
    working_hours: Optional[int] = None
    fte_allocation: Optional[float] = None
    duration_months: Optional[int] = None
    rule_version_hash: str
    hourly_cap_eur: Optional[float] = Field(default=None, description="Tetto di bando applicato (Fonte A)")
    budget_cap_pct: Optional[float] = Field(default=None, description="Massimale % di bando applicato alla categoria")


class CostItemValidated(BaseModel):
    item_id: str
    description: str
    category: CostCategory
    status: ItemValidationStatus
    original_cost_eur: float
    computed_cost_eur: float
    hourly_rate_computed: float = Field(..., description="Costo orario derivato dalle tabelle CCNL (€/ora); 0 se non applicabile")
    hourly_rate_cap: float = Field(..., description="Tetto orario del bando (€/ora); 0 se non applicabile")
    rejection_reason: Optional[str] = None
    applied_rules: List[str]
    criteria_checked: List[int] = Field(default_factory=list, description="Criteri (1-60) realmente eseguiti sulla riga")
    criteria_failed: List[int] = Field(default_factory=list)
    criteria_not_evaluated: List[int] = Field(default_factory=list, description="Criteri applicabili ma non eseguiti per dati o regole di bando mancanti")
    breakdown: CostBreakdown
    item_hash_sha256: str = Field(..., description="Foglia dell'Albero di Merkle")


class BudgetCheck(BaseModel):
    """Esito di un criterio valutato sull'intero budget (48, 49, 55, 56, 60)."""

    criterion: int
    title: str
    status: str = Field(..., description="PASS | FAIL | NOT_EVALUATED")
    message: str


class TraceStep(BaseModel):
    """Un passo dell'algoritmo: un criterio valutato su una riga, con effetto sull'importo."""

    seq: int
    stage: str
    item_id: Optional[str] = None
    criterion: Optional[int] = None
    outcome: str = Field(..., description="PASS | ADJUSTED | REJECTED | SUSPENDED")
    delta_eur: float = 0.0
    amount_after_eur: Optional[float] = None
    note: str = ""


class PipelineStage(BaseModel):
    key: str
    label: str
    duration_ms: float
    detail: str


class ShareCapInfo(BaseModel):
    group: str
    criterion: int
    cap_pct: float
    requested_eur: float
    allowed_eur: float
    base_eur: float
    total_final_eur: float


class MerkleView(BaseModel):
    leaf_item_ids: List[str]
    levels: List[List[str]] = Field(..., description="Hash troncati (12 caratteri): livello 0 = foglie, ultimo = radice")


class AlgorithmTrace(BaseModel):
    stages: List[PipelineStage]
    steps: List[TraceStep]
    share_caps: List[ShareCapInfo] = Field(default_factory=list)
    merkle: Optional[MerkleView] = None


class BudgetValidationResponse(BaseModel):
    project_id: str
    bando_id: str
    status: str = Field(..., description="VALIDATED o REJECTED_WITH_ERRORS")
    conformity_score: int = Field(..., ge=0, le=100)
    total_requested_eur: float
    total_approved_eur: float
    total_rejected_eur: float
    items: List[CostItemValidated]
    budget_checks: List[BudgetCheck] = Field(default_factory=list)
    trace: Optional[AlgorithmTrace] = None
    run_id: Optional[int] = Field(default=None, description="Identificativo dell'esecuzione nella memoria (HQ)")
    reference_date: Optional[date] = Field(default=None, description="Data di riferimento usata per leggere Fonte B: da ripassare nel ricalcolo")
    merkle_root: str
    cep_id: str = Field(..., description="Identificativo del Cryptographic Evidence Package")
    llm_explanation_summary: str
    explanation_source: str = Field(default="TEMPLATE", description="TEMPLATE | LLM (solo se il validatore numerico ha approvato)")


class RegistrationResponse(BaseModel):
    """Attestazione firmata di registrazione della Merkle Root nel registro append-only."""

    project_id: str
    cep_id: str
    merkle_root: str
    seq: int
    registered_at: str
    prev_hash: str
    entry_hash: str
    key_id: str
    public_key: str
    signature: str
    project_key: str


class ChainStatusResponse(BaseModel):
    intact: bool
    entries: int
    head_hash: str
    broken_at_seq: Optional[int] = None
    reason: Optional[str] = None
    key_id: str
    public_key: str
    is_dev_key: bool


class MainDeviation(BaseModel):
    category: str
    deviation_points: float = Field(..., description="Scostamento in punti percentuali (bozza - archetipo)")


class PatternMatchResponse(BaseModel):
    closest_archetype: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    archetype_averages: Dict[str, float]
    main_deviation: MainDeviation
    recommendation: str


class AuditVerificationResponse(BaseModel):
    """Report di asseverazione crittografica dell'Auditor Portal."""

    project_id: str
    provided_merkle_root: str = Field(..., description="Merkle Root presentata all'auditor / ricalcolata dai dati")
    registered_merkle_root: str = Field(..., description="Merkle Root nel registro (vuota se il progetto non è registrato)")
    registration_found: bool
    is_valid_and_unaltered: bool
    signature_valid: bool
    chain_intact: bool
    chain_entries: int
    registered_at: Optional[str] = None
    seq: Optional[int] = None
    entry_hash: Optional[str] = None
    key_id: Optional[str] = None
    recomputed_from_data: bool = False
    verification_time_seconds: float


class AuditRecomputeRequest(BaseModel):
    """Ricalcolo dell'albero da dati originali (Auditor Portal)."""

    project_id: str
    grant_rules: GrantRuleSet
    cost_items: List[CostItemInput]
    entity_liquidity_eur: Optional[float] = None
    baseline_totals: Optional[Dict[CostCategory, float]] = None
    reference_date: Optional[date] = Field(default=None, description="Data di riferimento di Fonte B usata nel calcolo originale (è nella risposta di /budget/validate)")
