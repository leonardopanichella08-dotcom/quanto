"""Profilo aziendale: dati dell'impresa e bilanci per esercizio, stima dell'anno successivo, bandi adatti, bozza di budget."""
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.deps import actor_of, scope_of
from app.core import company_profile as cp
from app.core import aids_register, budget_basis, company_facts, de_minimis, events, expense_types, growth_needs, matching, measures, project_ideas, project_types

router = APIRouter()


def _guard(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except cp.ProfileError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


class ProfileBody(BaseModel):
    fields: Dict[str, Any] = Field(..., description="Campi del profilo da salvare; un valore vuoto lo cancella")


class FinancialsBody(BaseModel):
    values: Dict[str, Any]


class ForecastBody(BaseModel):
    year: int = Field(..., ge=2020, le=2100)
    growth: Dict[str, float] = Field(default_factory=dict, description="Variazione annua per categoria o per i ricavi (REVENUE) (0,05 = +5%); ha la precedenza sul modello salvato")


class ForecastTemplateBody(BaseModel):
    growth: Dict[str, float] = Field(..., description="Variazione annua per categoria di spesa e per i ricavi (REVENUE): 0,05 = +5%, -0,03 = -3%")
    label: str = Field(default="", max_length=80, description="Chi l'ha indicata, per esempio «Cliente», «CFO» o «Studio»")
    note: str = Field(default="", max_length=500)


class TemplateBody(BaseModel):
    bando_id: str = Field(..., max_length=64)
    scale_pct: float = Field(default=100, gt=0, le=100, description="Quota del totale annuale da dedicare al progetto")
    fit: bool = Field(default=True, description="Riduci le voci sopra i tetti del bando alla parte ammissibile")
    year: Optional[int] = Field(default=None, ge=2020, le=2100, description="Anno del progetto (default: quello dopo l'ultimo bilancio, dentro la finestra del bando)")
    project_start: Optional[str] = Field(default=None, description="Data di avvio del progetto (AAAA-MM-GG): su ogni voce il controllo 46 verifica la finestra di ammissibilità del bando")


@router.get("", summary="Il profilo aziendale: dati, bilanci per esercizio, cosa manca e quanto è completo")
def get_profile(request: Request) -> dict:
    return cp.overview(scope_of(request))


@router.put("", summary="Salva i dati dell'impresa inseriti a mano")
def put_profile(body: ProfileBody, request: Request) -> dict:
    owner = scope_of(request)
    _guard(cp.update_profile, owner, body.fields, owner)
    return cp.overview(owner)


@router.put("/financials/{year}", summary="Salva i dati di un esercizio inseriti a mano")
def put_financials(year: int, body: FinancialsBody, request: Request) -> dict:
    owner = scope_of(request)
    _guard(cp.update_financials, owner, year, body.values, owner)
    return cp.overview(owner)


@router.post("/sync", summary="Rileggi i documenti caricati e aggiorna il profilo (i valori inseriti a mano restano)")
def sync(request: Request) -> dict:
    owner = scope_of(request)
    changed = cp.sync_from_documents(owner, owner)
    return {"changed": changed, "profile": cp.overview(owner)}


@router.get("/forecast-template", summary="Il modello di previsione salvato dall'utente (percentuali annue di crescita o calo di costi e ricavi)")
def get_forecast_template(request: Request) -> dict:
    return {"template": cp.get_forecast_template(scope_of(request)), "keys": [{"key": k, "label": cp.GROWTH_LABEL[k]} for k in cp.GROWTH_KEYS]}


@router.put("/forecast-template", summary="Salva il modello di previsione: sostituisce il precedente")
def put_forecast_template(body: ForecastTemplateBody, request: Request) -> dict:
    owner = scope_of(request)
    return {"template": _guard(cp.save_forecast_template, owner, body.growth, body.label, body.note, owner)}


@router.delete("/forecast-template", summary="Elimina il modello di previsione: le percentuali tornano a essere ricavate dai bilanci")
def delete_forecast_template(request: Request) -> dict:
    owner = scope_of(request)
    cp.delete_forecast_template(owner, owner)
    return {"template": None}


@router.post("/forecast", summary="Stima delle spese dell'anno indicato a partire dall'ultimo bilancio")
def forecast(body: ForecastBody, request: Request) -> dict:
    return _guard(cp.forecast, scope_of(request), body.year, body.growth)


@router.post("/match", summary="Quali bandi vanno bene per l'azienda, quali voci riducono, di quanto e come rientrarci")
def match(body: ForecastBody, request: Request) -> dict:
    owner = scope_of(request)
    fc = _guard(cp.forecast, owner, body.year, body.growth)
    by_cat = {r["category"]: r["forecast_eur"] for r in fc["categories"]}
    try:                                                       # le spese per voce (affitti, energia…) servono a togliere ciò che un bando esclude per nome
        plan = budget_basis.plan_for_year(owner, body.year, body.growth)
        by_type: Dict[str, Dict[str, Any]] = {}
        for r in plan["types"]:
            t = by_type.setdefault(r["code"], {"category": r["category"], "label": r["label"], "amount_eur": 0.0})
            t["amount_eur"] += r["amount_eur"]
    except cp.ProfileError:
        by_type = {}
    result = matching.match_all(cp.profile_values(owner), by_cat, body.year, by_type)
    events.record("profile.match", f"Bandi per l'esercizio {body.year}: {result['summary']['ADATTO']} adatti, {result['summary']['DA_VERIFICARE']} da verificare, "
                  f"{result['summary']['NON_ADATTO']} non adatti", actor=owner, details={"summary": result["summary"]})
    return {"forecast": fc, "matching": result, "de_minimis": de_minimis.estimate(owner, body.year)}


@router.post("/template", summary="Bozza di budget per un bando, ricavata dai bilanci dell'azienda (da modificare)")
def template(body: TemplateBody, request: Request) -> dict:
    owner = scope_of(request)
    try:
        out = _guard(matching.budget_template, owner, body.bando_id, body.scale_pct, body.fit, body.year, body.project_start)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bando non trovato") from None
    events.record("profile.template", f"Bozza di budget per {body.bando_id}: {len(out['cost_items'])} voci, {out['total_eur']:,.2f} €", actor=owner, bando_id=body.bando_id)
    return out


# ------------------------------------------------------------------------------------------------ cosa si è letto dai documenti
@router.get("/expenses", summary="Le spese dell'ultimo esercizio per voce di spesa (affitti, energia, licenze…), con la categoria generale")
def expenses(request: Request, year: Optional[int] = None) -> dict:
    return _guard(cp.expense_breakdown, scope_of(request), year)


@router.get("/staff", summary="L'organico persona per persona, dal registro del personale e dalle buste paga")
def staff(request: Request) -> dict:
    return company_facts.staff(scope_of(request))


@router.get("/assets", summary="Il libro cespiti e il piano di ammortamento")
def assets(request: Request) -> dict:
    return company_facts.assets(scope_of(request))


@router.get("/facts", summary="Quanti fatti sono stati letti dai documenti, per tipo")
def facts_overview(request: Request) -> dict:
    return company_facts.overview(scope_of(request))


@router.get("/expense-types", summary="L'elenco delle voci di spesa riconosciute")
def expense_type_list() -> dict:
    return {"types": expense_types.catalog()}


# ------------------------------------------------------------------------------------------------ idee di progetto
@router.get("/project-ideas", summary="Idee di progetto per l'azienda, dai suoi documenti, con le spese (nuove o ordinarie), cosa manca e i bandi che le finanziano")
def ideas(request: Request, year: Optional[int] = None, split: Optional[str] = None) -> dict:
    return _guard(project_ideas.generate, scope_of(request), year, growth_needs.parse_split(split))


@router.get("/needs", summary="Di cosa ha bisogno l'impresa per crescere: persone per reparto e strumenti, in al massimo 40 parole, e come farli finanziare")
def needs(request: Request, year: Optional[int] = None, split: Optional[str] = None) -> dict:
    return _guard(growth_needs.growth_needs, scope_of(request), year, growth_needs.parse_split(split))


@router.get("/measures", summary="Le agevolazioni che non sono bandi (esoneri INPS, tirocini, apprendistato, incentivi regionali, nuove imprese) e come valgono per questa impresa")
def measures_list(request: Request) -> dict:
    return measures.for_company(cp.profile_values(scope_of(request)))


@router.get("/project-types", summary="Le tipologie di progetto che un bando può finanziare")
def project_type_list() -> dict:
    return {"types": project_types.catalog()}


# ------------------------------------------------------------------------------------------------ aiuti ricevuti, impresa unica, registro nazionale
def _aids_guard(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except aids_register.AidsError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


class GroupBody(BaseModel):
    answers: Dict[str, str] = Field(default_factory=dict)
    companies: list = Field(default_factory=list)


class AidEntriesBody(BaseModel):
    company: str = Field(default="SELF", description="SELF = l'azienda; altrimenti il codice fiscale dell'impresa collegata")
    source: str = Field(default="RNA", description="RNA (visura ufficiale) o MANUALE")
    checked_at: Optional[str] = Field(default=None, description="Data in cui si è consultata la visura aiuti dell'RNA (solo per la fonte RNA)")
    entries: list = Field(default_factory=list)


class ConfirmBody(BaseModel):
    note: str = Field(default="", max_length=300)


@router.get("/aids", summary="Aiuti già ricevuti, impresa unica e verifica sul Registro Nazionale degli Aiuti: stato e residuo de minimis")
def aids(request: Request, on: Optional[str] = None) -> dict:
    day = None
    if on:
        try:
            from datetime import date as _d
            day = _d.fromisoformat(on)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Data non valida") from None
    return aids_register.status(scope_of(request), day)


@router.put("/aids/group", summary="Impresa unica: le risposte alle cinque domande e l'elenco delle imprese collegate")
def aids_group(body: GroupBody, request: Request) -> dict:
    return _aids_guard(aids_register.save_group, scope_of(request), body.answers, body.companies, actor_of(request))


@router.put("/aids/entries", summary="Le concessioni di un'impresa dalla visura aiuti dell'RNA (o inserite a mano): sostituiscono quelle precedenti della stessa fonte")
def aids_entries(body: AidEntriesBody, request: Request) -> dict:
    return _aids_guard(aids_register.save_entries, scope_of(request), body.company, body.source, body.entries, body.checked_at, actor_of(request))


@router.post("/aids/confirm", summary="Chi ha fatto la verifica la attesta: resta nel registro delle operazioni")
def aids_confirm(body: ConfirmBody, request: Request) -> dict:
    return _aids_guard(aids_register.confirm, scope_of(request), actor_of(request), body.note)


# ------------------------------------------------------------------------------------------------ coerenza tra i documenti, preventivi, soci
@router.get("/consistency", summary="Controlli di coerenza tra i documenti (IVA e bilancio, libro soci, DURC, visura aiuti, preventivi…)")
def consistency(request: Request) -> dict:
    return {"checks": company_facts.consistency(scope_of(request))}


@router.get("/quotes", summary="I preventivi dei fornitori caricati")
def quotes(request: Request) -> dict:
    return {"quotes": company_facts.quotes(scope_of(request))}


@router.get("/shareholders", summary="I soci dal libro soci (le persone fisiche solo come codice anonimo)")
def shareholders(request: Request) -> dict:
    return {"shareholders": company_facts.shareholders(scope_of(request))}
