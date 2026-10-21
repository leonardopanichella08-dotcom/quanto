"""I token di QUANTO: l'unità di consumo dello studio, come nel piano economico (15 «credit» al mese inclusi, extra a 8 € l'uno, nessun pagamento reale ancora).

**Principio.** Un token si spende solo dove QUANTO ha un costo vero o dove il lavoro dello studio diventa un consegnabile; tutto il resto, cioè il lavoro quotidiano che crea dipendenza, resta libero.

| Cosa | Token | Perché |
|---|---|---|
| Lavorare: profilo, documenti, stima, allocazione, bandi, controllo del budget mentre si modifica, assistente, Confronto, Verifica | 0 | costo quasi nullo (calcolo deterministico) e porta lo studio a usare QUANTO ogni giorno |
| **Consegnare un budget**: esportarlo (PDF/Excel) o registrarlo nel registro firmato | 1 | è il «credito di validazione» del piano: il momento in cui il lavoro vale. Una consegna dura 30 giorni: esportazioni e registrazione dello stesso budget, dopo modifiche comprese, non costano di più |
| **Studiare un bando nuovo** (non ancora in memoria) | 3 | è il costo vero del piano: estrazione con più passaggi, verifica, audit |
| Rifare lo studio di un bando già in memoria | 1 | aggiornare le regole ha un costo più basso |
| Un bando già studiato da chiunque | 0 | la cache è l'asset di QUANTO: più è usata, meno costa e più vale (nel piano la cache passa dal 10% al 65%) |
| Premio al catalogo | +1 | se lo studio di un bando nuovo si chiude «completo», 1 token torna indietro: chi arricchisce la memoria comune paga meno |

**Comodità per lo studio.** Il saldo è dello studio, non di chi preme il pulsante; i 15 token mensili non usati restano fino a 30; 10 token di benvenuto non scadono; mai addebiti per operazioni fallite o senza esito (rimborso automatico); un anticipo di cortesia di 2 token evita di restare bloccati a metà lavoro; il costo si legge prima di premere; i controlli del budget mentre si scrive non costano mai.

**Rendimento per QUANTO.** Il consumo segue il costo: chi studia bandi nuovi paga, chi usa la memoria condivisa no; la consegna è il punto di conversione; i premi al catalogo fanno crescere l'asset; i pacchetti hanno prezzi dal piano (8 € a token) con sconto volume.

Non c'è nessun incasso: le ricariche sono richieste che il titolare elabora (pagamento reale non ancora attivo). Il titolare (QUANTO_OWNER_EMAIL) non consuma token.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.core import events, users
from app.core.db import Conn, connect

MONTHLY_INCLUDED = 15          # piano economico: credit inclusi al mese
ROLLOVER_CAP = 30              # i token inclusi non usati si portano al mese dopo, fino a questo tetto
WELCOME_BONUS = 10             # una tantum, non scade
OVERDRAFT = 2                  # anticipo di cortesia: si può scendere fino a -2
DELIVERY_DAYS = 30             # una consegna copre esportazioni e registrazione dello stesso budget per 30 giorni
UNIT_PRICE_EUR = 8.0           # piano economico: prezzo del credito aggiuntivo

COSTS: Dict[str, Dict[str, Any]] = {
    "deliver": {"label": "Consegnare un budget (esportare o registrare)", "cost": 1, "note": "Vale 30 giorni per lo stesso budget, modifiche comprese."},
    "study_new": {"label": "Studiare un bando nuovo", "cost": 3, "note": "Un token torna indietro se la lettura è completa."},
    "study_refresh": {"label": "Rifare lo studio di un bando già in memoria", "cost": 1, "note": ""},
    "study_cached": {"label": "Usare un bando già studiato", "cost": 0, "note": "La memoria comune è gratuita."},
    "work": {"label": "Tutto il resto: profilo, documenti, stima, allocazione, controllo del budget, assistente, Confronto, Verifica", "cost": 0, "note": "Sempre incluso."},
}
PACKS: List[Dict[str, Any]] = [
    {"id": "S", "tokens": 10, "price_eur": 80.0, "note": "8 € a token, come nel piano"},
    {"id": "M", "tokens": 30, "price_eur": 216.0, "note": "7,20 € a token (−10%)"},
    {"id": "L", "tokens": 100, "price_eur": 680.0, "note": "6,80 € a token (−15%, come lo sconto del piano annuale)"},
]
BONUS_COMPLETE_STUDY = 1


class NotEnoughTokens(Exception):
    def __init__(self, needed: int, balance: int):
        super().__init__(f"Servono {needed} token, ne hai {balance}")
        self.needed, self.balance = needed, balance


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def exempt(user: Optional[Dict[str, Any]]) -> bool:
    """Chi non consuma token: nessun utente (accesso interno o autenticazione spenta) e il titolare."""
    return user is None or users.is_owner(user.get("email", ""))


# ------------------------------------------------------------------------------------------------ registro dei movimenti
def _insert(conn: Conn, uid: int, kind: str, bucket: str, amount: int, op: str, ref: str, dedupe: Optional[str], actor: str, note: str = "") -> bool:
    row = conn.execute(
        "INSERT INTO token_ledger (user_id, ts, kind, bucket, amount, op, ref, dedupe, actor, note) VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT (dedupe) DO NOTHING RETURNING id",
        (uid, _iso(_now()), kind, bucket, amount, op, ref, dedupe, actor, note)).fetchone()
    return row is not None


def _buckets(conn: Conn, uid: int) -> Dict[str, int]:
    out = {"INCLUDED": 0, "EXTRA": 0}
    for r in conn.execute("SELECT bucket, COALESCE(SUM(amount), 0) s FROM token_ledger WHERE user_id=? GROUP BY bucket", (uid,)).fetchall():
        out[r["bucket"]] = int(r["s"])
    return out


def _ensure_grants(conn: Conn, uid: int, created_at: str) -> None:
    """Token di benvenuto e uno stock mensile per ogni mese dalla registrazione (idempotente: ogni mese una volta sola)."""
    _insert(conn, uid, "WELCOME", "EXTRA", WELCOME_BONUS, "welcome", "", f"welcome:{uid}", "system", "Benvenuto: token che non scadono")
    start = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    y, m = start.year, start.month
    now = _now()
    months = []
    while (y, m) <= (now.year, now.month) and len(months) < 36:
        months.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    for ym in months[-36:]:
        if conn.execute("SELECT 1 FROM token_ledger WHERE dedupe=?", (f"monthly:{uid}:{ym}",)).fetchone():
            continue
        inc = _buckets(conn, uid)["INCLUDED"]
        grant = max(0, min(MONTHLY_INCLUDED, ROLLOVER_CAP - inc))
        _insert(conn, uid, "MONTHLY", "INCLUDED", grant, "monthly", ym, f"monthly:{uid}:{ym}", "system",
                f"{MONTHLY_INCLUDED} token del mese" if grant == MONTHLY_INCLUDED else (f"{grant} token del mese (tetto di {ROLLOVER_CAP} raggiunto)" if grant else f"Tetto di {ROLLOVER_CAP} raggiunto: nessun token aggiunto"))


def _user_row(user_id: int) -> Dict[str, Any]:
    row = users.get(user_id)
    if row is None:
        raise KeyError(user_id)
    return row


def balance(user_id: int) -> int:
    row = _user_row(user_id)
    with connect() as conn:
        conn.lock(8_100_000 + user_id)
        _ensure_grants(conn, user_id, row["created_at"])
        b = _buckets(conn, user_id)
    return b["INCLUDED"] + b["EXTRA"]


# ------------------------------------------------------------------------------------------------ spesa, rimborso, regalo
def spend(user: Optional[Dict[str, Any]], op: str, cost: int, ref: str = "", dedupe: Optional[str] = None, note: str = "") -> Dict[str, Any]:
    """Addebita ``cost`` token. Con la stessa ``dedupe`` non addebita due volte. Solleva ``NotEnoughTokens`` se mancano (oltre l'anticipo di cortesia)."""
    if exempt(user) or cost <= 0:
        return {"charged": 0, "reason": "esente" if exempt(user) else "gratis", "balance": None}
    uid = user["id"]
    row = _user_row(uid)
    with connect() as conn:
        conn.lock(8_100_000 + uid)
        _ensure_grants(conn, uid, row["created_at"])
        if dedupe and conn.execute("SELECT 1 FROM token_ledger WHERE dedupe=?", (dedupe,)).fetchone():
            b = _buckets(conn, uid)
            return {"charged": 0, "reason": "già pagato", "balance": b["INCLUDED"] + b["EXTRA"]}
        b = _buckets(conn, uid)
        total = b["INCLUDED"] + b["EXTRA"]
        if total + OVERDRAFT < cost:
            raise NotEnoughTokens(cost, total)
        take_inc = min(max(b["INCLUDED"], 0), cost)                        # prima i token del mese, che scadono; poi quelli che non scadono
        take_extra = min(max(b["EXTRA"], 0), cost - take_inc)
        rest = cost - take_inc - take_extra                                 # anticipo di cortesia: si registra sui token del mese, il prossimo accredito lo ripiana
        first = True
        for bucket, amount in (("INCLUDED", take_inc + rest), ("EXTRA", take_extra)):
            if amount:
                _insert(conn, uid, "SPEND", bucket, -amount, op, ref, dedupe if first else (f"{dedupe}#2" if dedupe else None), f"user:{user['email']}", note)
                first = False
        left = total - cost
    events.record("tokens.spend", f"{cost} token per «{COSTS.get(op, {}).get('label', op)}»" + (f" ({ref})" if ref else "") + f": ne restano {left}", actor=f"user:{user['email']}",
                  details={"op": op, "cost": cost, "ref": ref, "balance": left})
    return {"charged": cost, "balance": left, "overdraft": left < 0}


def refund(user: Optional[Dict[str, Any]], op: str, cost: int, ref: str = "", note: str = "", dedupe: Optional[str] = None, release: Optional[str] = None) -> None:
    """Restituisce token. ``release`` = la chiave dell'addebito annullato: così riprovare lo stesso giorno si paga di nuovo, ma una sola volta."""
    if exempt(user) or cost <= 0:
        return
    with connect() as conn:
        conn.lock(8_100_000 + user["id"])
        if release:
            conn.execute("UPDATE token_ledger SET dedupe = dedupe || '#annullato' WHERE dedupe=?", (release,))
        _insert(conn, user["id"], "REFUND", "EXTRA", cost, op, ref, dedupe, "system", note or "Operazione senza esito: token restituiti")
    events.record("tokens.refund", f"{cost} token restituiti ({note or op})", actor=f"user:{user['email']}", details={"op": op, "ref": ref})


def grant(user_id: int, tokens: int, note: str, actor: str, kind: str = "GRANT") -> Dict[str, Any]:
    """Token regalati o ricaricati dal titolare (non scadono)."""
    if tokens <= 0 or tokens > 100_000:
        raise ValueError("Il numero di token deve essere tra 1 e 100000")
    row = _user_row(user_id)
    with connect() as conn:
        conn.lock(8_100_000 + user_id)
        _ensure_grants(conn, user_id, row["created_at"])
        _insert(conn, user_id, kind, "EXTRA", tokens, "grant", "", None, actor, note[:300])
        b = _buckets(conn, user_id)
    events.record("tokens.grant", f"{tokens} token a {row['email']}" + (f": {note}" if note else ""), actor=actor, details={"user_id": user_id, "tokens": tokens})
    return {"user_id": user_id, "balance": b["INCLUDED"] + b["EXTRA"]}


# ------------------------------------------------------------------------------------------------ cosa costa
def study_cost(bando_id: str) -> Dict[str, Any]:
    """Un bando già in memoria con regole pubblicate si riusa gratis; rifarne lo studio costa poco; uno nuovo costa il costo vero."""
    with connect() as conn:
        n = conn.execute("SELECT COUNT(*) c FROM rules WHERE bando_id=? AND status='PUBLISHED'", (bando_id,)).fetchone()["c"]
    return {"cached": n > 0, "op": "study_refresh" if n > 0 else "study_new", "cost": COSTS["study_refresh" if n > 0 else "study_new"]["cost"]}


def delivery_key(client_id: Any, project_id: str, bando_id: str) -> str:
    return f"{client_id or '-'}|{project_id}|{bando_id or '-'}"


def delivery_status(user: Optional[Dict[str, Any]], key: str) -> Dict[str, Any]:
    """Il budget è già stato consegnato negli ultimi 30 giorni (e quindi esportarlo o registrarlo ora non costa)?"""
    if exempt(user):
        return {"covered": True, "cost": 0, "reason": "esente"}
    since = _iso(_now() - timedelta(days=DELIVERY_DAYS))
    with connect() as conn:
        r = conn.execute("SELECT ts FROM token_ledger WHERE user_id=? AND op='deliver' AND ref=? AND kind='SPEND' AND ts>=? ORDER BY id DESC LIMIT 1", (user["id"], key, since)).fetchone()
    if r:
        until = (datetime.fromisoformat(r["ts"].replace("Z", "+00:00")) + timedelta(days=DELIVERY_DAYS)).date().isoformat()
        return {"covered": True, "cost": 0, "reason": f"già consegnato: esportazioni e registrazione incluse fino al {until}"}
    return {"covered": False, "cost": COSTS["deliver"]["cost"], "reason": "una consegna vale 30 giorni per lo stesso budget"}


def charge_delivery(user: Optional[Dict[str, Any]], key: str) -> Dict[str, Any]:
    st = delivery_status(user, key)
    if st["covered"]:
        return {"charged": 0, "key": key, **st}
    return {**spend(user, "deliver", COSTS["deliver"]["cost"], ref=key, note="Consegna di un budget (30 giorni)"), "key": key}


def undo_delivery(user: Optional[Dict[str, Any]], paid: Dict[str, Any]) -> None:
    """La consegna non è riuscita (esportazione o registrazione in errore): il token torna e la consegna non risulta pagata."""
    if exempt(user) or not paid.get("charged"):
        return
    with connect() as conn:
        conn.lock(8_100_000 + user["id"])
        conn.execute("UPDATE token_ledger SET op='deliver#annullato' WHERE id=(SELECT id FROM token_ledger WHERE user_id=? AND op='deliver' AND ref=? AND kind='SPEND' ORDER BY id DESC LIMIT 1)", (user["id"], paid["key"]))
    refund(user, "deliver", paid["charged"], ref=paid["key"], note="Consegna non riuscita: token restituiti")


def overview(user: Dict[str, Any]) -> Dict[str, Any]:
    uid = user["id"]
    row = _user_row(uid)
    free = exempt(user)
    with connect() as conn:
        conn.lock(8_100_000 + uid)
        _ensure_grants(conn, uid, row["created_at"])
        b = _buckets(conn, uid)
        ledger = [dict(r) for r in conn.execute("SELECT id, ts, kind, bucket, amount, op, ref, note FROM token_ledger WHERE user_id=? ORDER BY id DESC LIMIT 25", (uid,)).fetchall()]
    total = b["INCLUDED"] + b["EXTRA"]
    now = _now()
    nxt = datetime(now.year + (now.month == 12), 1 if now.month == 12 else now.month + 1, 1, tzinfo=timezone.utc)
    spent_30 = 0
    since = _iso(now - timedelta(days=30))
    with connect() as conn:
        spent_30 = -int(conn.execute("SELECT COALESCE(SUM(amount),0) s FROM token_ledger WHERE user_id=? AND kind='SPEND' AND ts>=?", (uid, since)).fetchone()["s"])
    return {"exempt": free, "balance": total, "included": b["INCLUDED"], "extra": b["EXTRA"], "monthly": MONTHLY_INCLUDED, "cap": ROLLOVER_CAP, "overdraft": OVERDRAFT,
            "next_grant": nxt.date().isoformat(), "days_until_grant": max(0, (nxt - now).days), "spent_30_days": spent_30,
            "low": (not free) and total <= 3, "empty": (not free) and total <= 0,
            "costs": [{"op": k, **v} for k, v in COSTS.items()], "packs": PACKS, "unit_price_eur": UNIT_PRICE_EUR, "payments_active": False, "ledger": ledger}
