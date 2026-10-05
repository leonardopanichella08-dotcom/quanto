"""Profilo aziendale: dati dell'impresa e bilanci per esercizio, stima dell'anno successivo, bandi adatti, bozza di budget."""
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.deps import actor_of
from app.core import company_profile as cp
from app.core import events, matching

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
    label: str = Field(default="", max_length=80, description="Chi l'ha indicata, per esempio «Commercialista Rossi» o «CFO»")
    note: str = Field(default="", max_length=500)


class TemplateBody(BaseModel):
    bando_id: str = Field(..., max_length=64)
    scale_pct: float = Field(default=100, gt=0, le=100, description="Quota del totale annuale da dedicare al progetto")
    fit: bool = Field(default=True, description="Riduci le voci sopra i tetti del bando alla parte ammissibile")


@router.get("", summary="Il profilo aziendale: dati, bilanci per esercizio, cosa manca e quanto è completo")
def get_profile(request: Request) -> dict:
    return cp.overview(actor_of(request))


@router.put("", summary="Salva i dati dell'impresa inseriti a mano")
def put_profile(body: ProfileBody, request: Request) -> dict:
    owner = actor_of(request)
    _guard(cp.update_profile, owner, body.fields, owner)
    return cp.overview(owner)


@router.put("/financials/{year}", summary="Salva i dati di un esercizio inseriti a mano")
def put_financials(year: int, body: FinancialsBody, request: Request) -> dict:
    owner = actor_of(request)
    _guard(cp.update_financials, owner, year, body.values, owner)
    return cp.overview(owner)


@router.post("/sync", summary="Rileggi i documenti caricati e aggiorna il profilo (i valori inseriti a mano restano)")
def sync(request: Request) -> dict:
    owner = actor_of(request)
    changed = cp.sync_from_documents(owner, owner)
    return {"changed": changed, "profile": cp.overview(owner)}


@router.get("/forecast-template", summary="Il modello di previsione salvato dall'utente (percentuali annue di crescita o calo di costi e ricavi)")
def get_forecast_template(request: Request) -> dict:
    return {"template": cp.get_forecast_template(actor_of(request)), "keys": [{"key": k, "label": cp.GROWTH_LABEL[k]} for k in cp.GROWTH_KEYS]}


@router.put("/forecast-template", summary="Salva il modello di previsione: sostituisce il precedente")
def put_forecast_template(body: ForecastTemplateBody, request: Request) -> dict:
    owner = actor_of(request)
    return {"template": _guard(cp.save_forecast_template, owner, body.growth, body.label, body.note, owner)}


@router.delete("/forecast-template", summary="Elimina il modello di previsione: le percentuali tornano a essere ricavate dai bilanci")
def delete_forecast_template(request: Request) -> dict:
    owner = actor_of(request)
    cp.delete_forecast_template(owner, owner)
    return {"template": None}


@router.post("/forecast", summary="Stima delle spese dell'anno indicato a partire dall'ultimo bilancio")
def forecast(body: ForecastBody, request: Request) -> dict:
    return _guard(cp.forecast, actor_of(request), body.year, body.growth)


@router.post("/match", summary="Quali bandi vanno bene per l'azienda, quali voci riducono, di quanto e come rientrarci")
def match(body: ForecastBody, request: Request) -> dict:
    owner = actor_of(request)
    fc = _guard(cp.forecast, owner, body.year, body.growth)
    by_cat = {r["category"]: r["forecast_eur"] for r in fc["categories"]}
    result = matching.match_all(cp.profile_values(owner), by_cat, body.year)
    events.record("profile.match", f"Bandi per l'esercizio {body.year}: {result['summary']['ADATTO']} adatti, {result['summary']['DA_VERIFICARE']} da verificare, "
                  f"{result['summary']['NON_ADATTO']} non adatti", actor=owner, details={"summary": result["summary"]})
    return {"forecast": fc, "matching": result}


@router.post("/template", summary="Bozza di budget per un bando, ricavata dai bilanci dell'azienda (da modificare)")
def template(body: TemplateBody, request: Request) -> dict:
    owner = actor_of(request)
    try:
        out = _guard(matching.budget_template, owner, body.bando_id, body.scale_pct, body.fit)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bando non trovato") from None
    events.record("profile.template", f"Bozza di budget per {body.bando_id}: {len(out['cost_items'])} voci, {out['total_eur']:,.2f} €", actor=owner, bando_id=body.bando_id)
    return out
