"""Catalogo dei campi di una voce di costo: alimenta l'editor del frontend, il template Excel e l'import.

Ogni campo di ``CostItemInput`` deve comparire qui (un test lo verifica): così UI e Excel non possono restare
indietro rispetto al modello quando si aggiunge un criterio.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.models.schemas import CostItemInput

ALL = None  # tutte le categorie
PERS = ["PERSONNEL"]
NONPERS = ["CAPITAL_ASSETS", "CONSULTING", "OVERHEAD", "TRAINING"]
ASSET = ["CAPITAL_ASSETS"]
CONS = ["CONSULTING"]
OVER = ["OVERHEAD"]

CATEGORY_OPTIONS = ["PERSONNEL", "CAPITAL_ASSETS", "CONSULTING", "OVERHEAD", "TRAINING"]


def _f(name: str, label: str, type_: str, group: str, cats: Optional[List[str]] = ALL, crit: Tuple[int, ...] = (),
       help_: str = "", options: Optional[List[str]] = None, step: Optional[str] = None) -> Dict[str, Any]:
    d: Dict[str, Any] = {"name": name, "label": label, "type": type_, "group": group, "categories": cats, "criteria": list(crit), "help": help_}
    if options:
        d["options"] = options
    if step:
        d["step"] = step
    return d


FIELDS: List[Dict[str, Any]] = [
    # --- identificazione
    _f("item_id", "ID voce", "text", "Identificazione", crit=(), help_="Identificativo univoco nel budget"),
    _f("description", "Descrizione", "text", "Identificazione"),
    _f("category", "Categoria", "select", "Identificazione", options=CATEGORY_OPTIONS, crit=(16,), help_="Deve essere ammessa dal bando"),
    _f("source_c_ref", "Documento sorgente (Fonte C)", "text", "Identificazione", crit=(15, 16), help_="Busta paga, fattura, contratto: se vuoto la riga è sospesa"),
    # --- personale
    _f("ccnl_code", "CCNL", "select", "Personale", PERS, (1,), "Le opzioni sono i contratti presenti in Fonte B (tabelle ufficiali caricate dal manager)", options=[]),
    _f("employee_level", "Livello contrattuale", "text", "Personale", PERS, (1, 14)),
    _f("ral_eur", "RAL dichiarata (€)", "number", "Personale", PERS, (2, 4, 5), step="0.01"),
    _f("fte_allocation", "Quota FTE sul progetto", "number", "Personale", PERS, (8,), step="0.05"),
    _f("duration_months", "Durata (mesi)", "number", "Identificazione", ALL, (8, 18, 42), step="1"),
    _f("working_hours_override", "Ore annue (solo riduzione)", "number", "Personale", PERS, (3,), "Non può superare le ore del CCNL", step="1"),
    _f("employee_token", "Token lavoratore (opaco)", "text", "Personale", PERS, (8,), "Mai il nome: somma FTE per lavoratore"),
    _f("contract_type", "Tipo di contratto", "select", "Personale", PERS, (12, 13), options=["PERMANENT", "FIXED_TERM", "OCCASIONAL"]),
    _f("superminimo_eur", "Superminimo incluso nella RAL (€)", "number", "Personale", PERS, (6,), step="0.01"),
    _f("superminimo_recognized", "Superminimo riconosciuto", "bool", "Personale", PERS, (6,)),
    _f("overtime_hours", "Ore straordinarie imputate", "number", "Personale", PERS, (11,), step="0.5"),
    _f("travel_allowance_eur", "Trasferte/diarie (€)", "number", "Personale", PERS, (9,), step="0.01"),
    _f("travel_documented", "Trasferte documentate", "bool", "Personale", PERS, (9,)),
    _f("occasional_annual_income_eur", "Reddito annuo occasionale (€)", "number", "Personale", PERS, (13,), step="0.01"),
    _f("role_min_level", "Livello minimo del mansionario", "text", "Personale", PERS, (14,)),
    _f("role_max_level", "Livello massimo del mansionario", "text", "Personale", PERS, (14,)),
    _f("payslip_ral_eur", "RAL da busta paga reale (€)", "number", "Personale", PERS, (15,), step="0.01"),
    _f("activity_type", "Tipo di attività", "select", "Personale", PERS, (10,), options=["PROJECT", "B2B", "B2G"]),
    _f("activity_segregated", "Attività segregata contabilmente", "bool", "Personale", PERS, (10,)),
    # --- importo e IVA
    _f("amount_eur", "Imponibile (€)", "number", "Importo, IVA e valuta", NONPERS, (16,), step="0.01"),
    _f("expense_subtype", "Sotto-tipo di spesa", "select", "Importo, IVA e valuta", NONPERS, (27, 37, 38, 39, 41, 42, 43, 44),
       options=["COMMUNICATION", "GUARANTEE", "AUDIT", "PENALTY", "LEGAL_DISPUTE", "REPRESENTATION", "RENT", "UTILITIES",
                "MAINTENANCE_ORDINARY", "MAINTENANCE_EXTRAORDINARY", "FINANCIAL_CHARGES"]),
    _f("vat_eur", "IVA (€)", "number", "Importo, IVA e valuta", NONPERS, (25, 53, 54), step="0.01"),
    _f("vat_recoverable", "IVA recuperabile", "bool", "Importo, IVA e valuta", NONPERS, (53, 54)),
    _f("reverse_charge_applied", "Reverse charge", "bool", "Importo, IVA e valuta", ASSET, (25,)),
    _f("currency", "Valuta", "text", "Importo, IVA e valuta", NONPERS, (59,), "Codice ISO a 3 lettere (default EUR)"),
    _f("fx_rate", "Cambio verso EUR", "number", "Importo, IVA e valuta", NONPERS, (59,), step="0.0001"),
    # --- beni strumentali
    _f("asset_nature", "Natura del bene", "select", "Beni strumentali", ASSET, (16, 26), options=["HARDWARE", "SOFTWARE", "SERVICE", "IMMATERIAL", "REAL_ESTATE"]),
    _f("depreciation_rate_pct", "Aliquota d'ammortamento annua", "number", "Beni strumentali", ASSET, (17, 18), "0-1 (es. 0,2 = 20%)", step="0.01"),
    _f("is_new", "Nuovo di fabbrica", "bool", "Beni strumentali", ASSET, (19,)),
    _f("origin_eu", "Prodotto in UE/SEE", "bool", "Beni strumentali", ASSET, (16,)),
    _f("iot_interconnected", "Interconnesso (IoT/4.0)", "bool", "Beni strumentali", ASSET, (20,)),
    _f("energy_saving_pct", "Risparmio energetico atteso", "number", "Beni strumentali", ASSET, (21,), "0-1", step="0.01"),
    _f("market_benchmark_eur", "Prezzo di mercato di riferimento (€)", "number", "Beni strumentali", ASSET, (22,), step="0.01"),
    _f("depreciation_category", "Categoria d'ammortamento (Fonte B)", "select", "Beni strumentali", ASSET, (17,), "L'aliquota di tabella è il tetto", options=[]),
    _f("benchmark_category", "Categoria di prezzo o tariffa (Fonte B)", "select", "Beni strumentali", list(ASSET) + list(CONS), (22, 33), "Se scelta, il riferimento è quello della tabella di Fonte B", options=[]),
    _f("installation_cost_eur", "Costi di installazione/collaudo (€)", "number", "Beni strumentali", ASSET, (23,), step="0.01"),
    _f("leasing_interest_eur", "Interessi del leasing (€)", "number", "Beni strumentali", ASSET, (24,), step="0.01"),
    _f("dnsh_compliant", "Conforme DNSH", "bool", "Beni strumentali", ASSET, (28,)),
    _f("exclusive_use", "Uso esclusivo nel progetto", "bool", "Beni strumentali", ASSET, (29,)),
    _f("sworn_appraisal_present", "Perizia asseverata presente", "bool", "Beni strumentali", ASSET, (30,)),
    _f("post_closure_commitment_months", "Impegno post-chiusura (mesi)", "number", "Beni strumentali", ASSET, (58,), step="1"),
    # --- consulenze
    _f("supplier_related_party", "Fornitore parte correlata", "bool", "Consulenze e fornitori", NONPERS, (32,)),
    _f("supplier_ateco", "ATECO del fornitore", "text", "Consulenze e fornitori", NONPERS, (34,)),
    _f("supplier_durc_valid", "DURC regolare", "bool", "Consulenze e fornitori", NONPERS, (45,)),
    _f("subcontracted", "Subappalto", "bool", "Consulenze e fornitori", NONPERS, (35,)),
    _f("subcontract_authorized", "Subappalto autorizzato", "bool", "Consulenze e fornitori", NONPERS, (35,)),
    _f("daily_rate_eur", "Tariffa giornaliera (€)", "number", "Consulenze e fornitori", CONS, (33,), step="0.01"),
    _f("days", "Giornate", "number", "Consulenze e fornitori", CONS, (33,), step="0.5"),
    _f("benchmark_daily_rate_eur", "Tariffa di mercato (€/gg)", "number", "Consulenze e fornitori", CONS, (33,), step="0.01"),
    _f("travel_cost_eur", "Spese di viaggio del consulente (€)", "number", "Consulenze e fornitori", CONS, (40,), step="0.01"),
    _f("travel_included_in_fee", "Viaggi inclusi nell'onorario", "bool", "Consulenze e fornitori", CONS, (40,)),
    # --- spese generali
    _f("rent_sqm_project", "Locazione: mq del progetto", "number", "Spese generali", OVER, (42,), step="0.1"),
    _f("rent_sqm_total", "Locazione: mq totali", "number", "Spese generali", OVER, (42,), step="0.1"),
    _f("rent_months_active", "Locazione: mesi di attività", "number", "Spese generali", OVER, (42,), step="1"),
    _f("allocation_method", "Criterio di ripartizione utenze", "text", "Spese generali", OVER, (43,)),
    _f("project_related", "Finalizzata al progetto", "bool", "Spese generali", OVER, (44,)),
    # --- tracciabilità e cumulo
    _f("expense_date", "Data della spesa", "date", "Tracciabilità e cumulo", ALL, (46,)),
    _f("funding_ids", "Altri contributi (separati da virgola)", "list", "Tracciabilità e cumulo", ALL, (47,), "Vuoto = nessuno"),
    _f("other_aid_eur", "Altri aiuti/crediti d'imposta (€)", "number", "Tracciabilità e cumulo", ALL, (48,), step="0.01"),
    _f("cup_code", "Codice CUP", "text", "Tracciabilità e cumulo", ALL, (50,), "15 caratteri alfanumerici"),
    _f("cig_required", "CIG obbligatorio", "bool", "Tracciabilità e cumulo", NONPERS, (51,)),
    _f("cig_code", "Codice CIG", "text", "Tracciabilità e cumulo", NONPERS, (51,), "10 caratteri alfanumerici"),
    _f("payment_method", "Metodo di pagamento", "select", "Tracciabilità e cumulo", ALL, (52,), options=["BANK_TRANSFER", "CARD", "CASH", "CHECK"]),
    _f("milestone_id", "Milestone/SAL", "text", "Tracciabilità e cumulo", ALL, (57,)),
]


def field_names() -> List[str]:
    return [f["name"] for f in FIELDS]


def coerce_value(field: Dict[str, Any], raw: Any) -> Any:
    """Converte una cella Excel/CSV nel tipo del campo. ``None`` per celle vuote."""
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    t = field["type"]
    if t == "bool":
        if isinstance(raw, bool):
            return raw
        return str(raw).strip().lower() in ("1", "true", "vero", "si", "sì", "yes", "y", "x")
    if t == "number":
        if isinstance(raw, (int, float)):
            return raw
        return float(str(raw).strip().replace(".", "").replace(",", ".")) if "," in str(raw) else float(str(raw).strip())
    if t == "list":
        return [p.strip() for p in str(raw).split(",") if p.strip()]
    if t == "date":
        return raw.date().isoformat() if hasattr(raw, "date") else str(raw).strip()
    return str(raw).strip()


def assert_complete() -> None:
    missing = set(CostItemInput.model_fields) - set(field_names())
    extra = set(field_names()) - set(CostItemInput.model_fields)
    if missing or extra:
        raise AssertionError(f"field_catalog non allineato: mancanti={sorted(missing)} extra={sorted(extra)}")
