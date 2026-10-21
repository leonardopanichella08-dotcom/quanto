"""I token dello studio: saldo, cosa costa ogni cosa, preventivo prima di spendere, richiesta di ricarica."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.deps import client_of, user_of
from app.core import events, tokens

router = APIRouter()


def _me(request: Request) -> dict:
    u = user_of(request)
    if u is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Accesso richiesto")
    return u


def not_enough(exc: tokens.NotEnoughTokens) -> HTTPException:
    """Risposta 402: dice quanti token servono, quanti ce ne sono e che si può ricaricare."""
    return HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail={
        "code": "TOKENS_NEEDED", "needed": exc.needed, "balance": exc.balance,
        "message": f"Servono {exc.needed} token e ne hai {exc.balance}. Il lavoro quotidiano (profilo, documenti, allocazione, controllo del budget) resta libero: puoi ricaricare per consegnare o studiare bandi nuovi."})


def charge_delivery(request: Request, project_id: str, bando_id: Optional[str]) -> dict:  # restituisce l'addebito (da annullare con undo_delivery se la consegna fallisce)
    """Consegna di un budget (esportazione o registrazione): 1 token, valido 30 giorni per lo stesso budget."""
    u = user_of(request)
    try:
        return tokens.charge_delivery(u, tokens.delivery_key(client_of(request), project_id, bando_id or ""))
    except tokens.NotEnoughTokens as exc:
        raise not_enough(exc) from exc


def undo_delivery(request: Request, paid: dict) -> None:
    tokens.undo_delivery(user_of(request), paid)


@router.get("", summary="Saldo dei token, costi, pacchetti e ultimi movimenti dello studio")
def overview(request: Request) -> dict:
    return tokens.overview(_me(request))


@router.get("/quote", summary="Quanto costa un'operazione, prima di farla (deliver con project_id e bando_id; study con bando_id)")
def quote(request: Request, op: str, project_id: Optional[str] = None, bando_id: Optional[str] = None) -> dict:
    u = _me(request)
    if op == "deliver":
        if not project_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Indica project_id")
        st = tokens.delivery_status(u, tokens.delivery_key(client_of(request), project_id, bando_id or ""))
        return {"op": op, "cost": st["cost"], "covered": st["covered"], "reason": st["reason"]}
    if op == "study":
        if not bando_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Indica bando_id")
        s = tokens.study_cost(bando_id)
        return {"op": s["op"], "cost": 0 if tokens.exempt(u) else s["cost"], "cached": s["cached"],
                "reason": "già in memoria: rifare lo studio costa meno" if s["cached"] else "bando nuovo: se la lettura è completa 1 token torna indietro"}
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Operazione sconosciuta: deliver o study")


class TopUp(BaseModel):
    pack: str = Field(..., max_length=4)
    note: str = Field(default="", max_length=300)


@router.post("/topup-request", status_code=status.HTTP_201_CREATED, summary="Chiede una ricarica (il pagamento reale non è ancora attivo: la elabora il titolare)")
def topup_request(body: TopUp, request: Request) -> dict:
    u = _me(request)
    pack = next((p for p in tokens.PACKS if p["id"] == body.pack.upper()), None)
    if pack is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Pacchetto sconosciuto")
    events.record("tokens.topup_request", f"{u['email']} chiede il pacchetto {pack['id']}: {pack['tokens']} token, {pack['price_eur']:.2f} €" + (f" — {body.note}" if body.note else ""),
                  actor=f"user:{u['email']}", details={"pack": pack["id"], "tokens": pack["tokens"], "price_eur": pack["price_eur"], "user_id": u["id"]})
    return {"requested": pack, "message": "Richiesta registrata. Il pagamento online non è ancora attivo: il titolare la elabora e ti accredita i token."}
