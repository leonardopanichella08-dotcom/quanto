"""I token di QUANTO: l'unità di consumo dello studio. Il piano costa 209 € al mese o 1.999 € all'anno e include 15 token al mese; 10 token in più costano 25 € (nessun pagamento reale ancora).

**Principio.** Un token si spende solo dove QUANTO ha un costo vero o dove il lavoro dello studio diventa un consegnabile; tutto il resto, cioè il lavoro quotidiano che crea dipendenza, resta libero.
Dove si spende, il costo segue **quanti dati si analizzano** (da un minimo a un massimo dichiarati), non un prezzo fisso uguale per tutti.

| Cosa | Token | Perché |
|---|---|---|
| Lavorare: profilo, documenti, stima, bandi adatti, controllo del budget mentre si modifica, assistente, Confronto, Verifica | 0 | costo quasi nullo (calcolo deterministico) e porta lo studio a usare QUANTO ogni giorno |
| **Calcolare il piano di allocazione** | da 2 a 4,8 | 2 di base + fino a 1,4 per il bilancio (righe di spesa analizzate) + fino a 1,4 per i bandi nel piano (quanto sono corposi: regole e requisiti letti). Vale 30 giorni per lo stesso lavoro e lo stesso anno: ricalcolare con altre scelte non costa di più, salvo che si analizzino dati più grandi (si paga solo la differenza) |
| **Consegnare un budget**: esportarlo (PDF/Excel) o registrarlo nel registro firmato | da 1 a 2 | 1 fino a 25 voci, 1,5 fino a 60, 2 oltre. Una consegna dura 30 giorni: esportazioni e registrazione dello stesso budget non costano di più (si paga solo la differenza se il budget cresce) |
| **Studiare un bando nuovo** (non ancora in memoria) | 3 | è il costo vero: estrazione con più passaggi, verifica, audit |
| Rifare lo studio di un bando già in memoria | 1 | aggiornare le regole ha un costo più basso |
| Un bando già studiato da chiunque | 0 | la cache è l'asset di QUANTO: più è usata, meno costa e più vale |
| Premio al catalogo | +1 | se lo studio di un bando nuovo si chiude «completo», 1 token torna indietro |
| **Pubblicare un budget per tutti** | **+0,5** | allena il motore collettivo, che è il valore aggiunto di QUANTO. Una volta per cliente e bando, al massimo 10 al mese |

I token possono avere un decimale (0,1). Il saldo è dello studio, non di chi preme il pulsante; i 15 token mensili non usati restano fino a 30; 10 token di benvenuto non scadono; mai addebiti per operazioni fallite o senza esito (rimborso automatico); un anticipo di cortesia di 2 token; il costo si legge prima di premere.

Non c'è nessun incasso: le ricariche sono richieste che il titolare elabora (pagamento reale non ancora attivo). Il titolare (QUANTO_OWNER_EMAIL) non consuma token.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.core import events, users
from app.core.db import Conn, connect

MONTHLY_INCLUDED = 15          # il piano include 15 token al mese
ROLLOVER_CAP = 30              # i token inclusi non usati si portano al mese dopo, fino a questo tetto
WELCOME_BONUS = 10             # una tantum, non scade
OVERDRAFT = 2                  # anticipo di cortesia: si può scendere fino a -2
WINDOW_DAYS = 30               # una consegna o un'analisi di allocazione valgono 30 giorni per lo stesso lavoro
PLAN_MONTHLY_EUR = 209.0       # piano mensile (15 token al mese inclusi)
PLAN_YEARLY_EUR = 1999.0       # piano annuale (gli stessi 15 token al mese)
UNIT_PRICE_EUR = 2.5           # 10 token in più costano 25 €
PUBLISH_BONUS = 0.5            # token regalati a chi pubblica un budget per tutti (motore collettivo)
PUBLISH_BONUS_MONTHLY_CAP = 10  # al massimo 10 premi al mese per studio: il premio è per budget veri, non per riempire il motore

# Allocazione: 2 di base, fino a 1,4 per il bilancio e fino a 1,4 per i bandi → da 2,0 a 4,8
ALLOC_BASE, ALLOC_MAX_PART = 2.0, 1.4
ALLOC_LINES_PER_STEP = 5            # 0,1 token ogni 5 righe di spesa analizzate (tetto a 70 righe)
ALLOC_BANDO_BASE, ALLOC_BANDO_EXTRA_MAX = 0.1, 0.15   # per ogni bando nel piano: 0,1 più fino a 0,15 secondo quanto è corposo
ALLOC_UNITS_PER_STEP = 0.01          # 0,01 token per ogni «unità» (una regola pubblicata o 5 requisiti letti)
# Consegna di un budget: dipende da quante voci ha
DELIVERY_TIERS = ((25, 1.0), (60, 1.5), (10 ** 9, 2.0))

COSTS: Dict[str, Dict[str, Any]] = {
    "allocate": {"label": "Calcolare il piano di allocazione", "cost": 2.0, "max": 4.8, "note": "Da 2 a 4,8 token secondo quanti dati analizza: righe del bilancio e bandi nel piano. Vale 30 giorni per lo stesso lavoro e anno."},
    "deliver": {"label": "Consegnare un budget (esportare o registrare)", "cost": 1.0, "max": 2.0, "note": "1 token fino a 25 voci, 1,5 fino a 60, 2 oltre. Vale 30 giorni per lo stesso budget."},
    "study_new": {"label": "Studiare un bando nuovo", "cost": 3, "note": "Un token torna indietro se la lettura è completa."},
    "study_refresh": {"label": "Rifare lo studio di un bando già in memoria", "cost": 1, "note": ""},
    "study_cached": {"label": "Usare un bando già studiato", "cost": 0, "note": "La memoria comune è gratuita."},
    "publish": {"label": "Pubblicare un budget per tutti", "cost": -PUBLISH_BONUS, "note": "Ti regala 0,5 token: allena il motore collettivo."},
    "work": {"label": "Tutto il resto: profilo, documenti, stima, bandi adatti, controllo del budget, assistente, Confronto, Verifica", "cost": 0, "note": "Sempre incluso."},
}
PACKS: List[Dict[str, Any]] = [
    {"id": "S", "tokens": 10, "price_eur": 25.0, "note": "2,50 € a token"},
]
BONUS_COMPLETE_STUDY = 1


def n1(x: Any) -> float:
    """Token con un decimale."""
    return round(float(x) + 1e-9, 1)


class NotEnoughTokens(Exception):
    def __init__(self, needed: float, balance: float):
        super().__init__(f"Servono {needed} token, ne hai {balance}")
        self.needed, self.balance = needed, balance


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def charging() -> bool:
    """Fase di prova: finché ``QUANTO_TOKENS_CHARGE`` non è 1 nessun token viene scalato e nulla si blocca. Costi e saldo si vedono, ma tutto è gratuito."""
    return os.getenv("QUANTO_TOKENS_CHARGE", "0").strip().lower() in ("1", "true", "yes", "si", "sì")


def exempt(user: Optional[Dict[str, Any]]) -> bool:
    """Chi non consuma token: nessun utente (accesso interno o autenticazione spenta) e il titolare."""
    return user is None or users.is_owner(user.get("email", ""))


# ------------------------------------------------------------------------------------------------ registro dei movimenti
def _insert(conn: Conn, uid: int, kind: str, bucket: str, amount: float, op: str, ref: str, dedupe: Optional[str], actor: str, note: str = "") -> Optional[int]:
    """Scrive un movimento; restituisce il suo id, o None se la stessa ``dedupe`` esiste già."""
    row = conn.execute(
        "INSERT INTO token_ledger (user_id, ts, kind, bucket, amount, op, ref, dedupe, actor, note) VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT (dedupe) DO NOTHING RETURNING id",
        (uid, _iso(_now()), kind, bucket, n1(amount), op, ref, dedupe, actor, note)).fetchone()
    return int(row["id"]) if row else None


def _buckets(conn: Conn, uid: int) -> Dict[str, float]:
    out = {"INCLUDED": 0.0, "EXTRA": 0.0}
    for r in conn.execute("SELECT bucket, COALESCE(SUM(amount), 0) s FROM token_ledger WHERE user_id=? GROUP BY bucket", (uid,)).fetchall():
        out[r["bucket"]] = n1(r["s"])
    return out


def _void(conn: Conn, ids: List[int]) -> None:
    """Annulla dei movimenti di spesa (l'operazione non è andata a buon fine): non contano più come pagati."""
    for i in ids:
        conn.execute("UPDATE token_ledger SET op = op || '#annullato', dedupe = CASE WHEN dedupe IS NULL THEN NULL ELSE dedupe || '#annullato' END WHERE id=?", (i,))


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
        inc = n1(inc)
        _insert(conn, uid, "MONTHLY", "INCLUDED", grant, "monthly", ym, f"monthly:{uid}:{ym}", "system",
                f"{MONTHLY_INCLUDED} token del mese" if grant == MONTHLY_INCLUDED else (f"{grant} token del mese (tetto di {ROLLOVER_CAP} raggiunto)" if grant else f"Tetto di {ROLLOVER_CAP} raggiunto: nessun token aggiunto"))


def _user_row(user_id: int) -> Dict[str, Any]:
    row = users.get(user_id)
    if row is None:
        raise KeyError(user_id)
    return row


def balance(user_id: int) -> float:
    row = _user_row(user_id)
    with connect() as conn:
        conn.lock(8_100_000 + user_id)
        _ensure_grants(conn, user_id, row["created_at"])
        b = _buckets(conn, user_id)
    return n1(b["INCLUDED"] + b["EXTRA"])


# ------------------------------------------------------------------------------------------------ spesa, rimborso, regalo
def spend(user: Optional[Dict[str, Any]], op: str, cost: float, ref: str = "", dedupe: Optional[str] = None, note: str = "") -> Dict[str, Any]:
    """Addebita ``cost`` token. Con la stessa ``dedupe`` non addebita due volte. Solleva ``NotEnoughTokens`` se mancano (oltre l'anticipo di cortesia)."""
    cost = n1(cost)
    if exempt(user) or cost <= 0 or not charging():
        return {"charged": 0, "reason": "esente" if exempt(user) else "gratis" if cost <= 0 else "prova gratuita", "balance": None, "ids": []}
    uid = user["id"]
    row = _user_row(uid)
    ids: List[int] = []
    with connect() as conn:
        conn.lock(8_100_000 + uid)
        _ensure_grants(conn, uid, row["created_at"])
        if dedupe and conn.execute("SELECT 1 FROM token_ledger WHERE dedupe=?", (dedupe,)).fetchone():
            b = _buckets(conn, uid)
            return {"charged": 0, "reason": "già pagato", "balance": n1(b["INCLUDED"] + b["EXTRA"]), "ids": []}
        b = _buckets(conn, uid)
        total = n1(b["INCLUDED"] + b["EXTRA"])
        if total + OVERDRAFT + 1e-9 < cost:
            raise NotEnoughTokens(cost, total)
        take_inc = n1(min(max(b["INCLUDED"], 0), cost))                    # prima i token del mese, che scadono; poi quelli che non scadono
        take_extra = n1(min(max(b["EXTRA"], 0), cost - take_inc))
        rest = n1(cost - take_inc - take_extra)                             # anticipo di cortesia: si registra sui token del mese, il prossimo accredito lo ripiana
        first = True
        for bucket, amount in (("INCLUDED", n1(take_inc + rest)), ("EXTRA", take_extra)):
            if amount > 0:
                i = _insert(conn, uid, "SPEND", bucket, -amount, op, ref, dedupe if first else (f"{dedupe}#2" if dedupe else None), f"user:{user['email']}", note)
                if i:
                    ids.append(i)
                first = False
        left = n1(total - cost)
    events.record("tokens.spend", f"{cost} token per «{COSTS.get(op, {}).get('label', op)}»" + (f" ({ref})" if ref else "") + f": ne restano {left}", actor=f"user:{user['email']}",
                  details={"op": op, "cost": cost, "ref": ref, "balance": left})
    return {"charged": cost, "balance": left, "overdraft": left < 0, "ids": ids}


def refund(user: Optional[Dict[str, Any]], op: str, cost: float, ref: str = "", note: str = "", dedupe: Optional[str] = None, release: Optional[str] = None) -> None:
    """Restituisce token. ``release`` = la chiave dell'addebito annullato: così riprovare lo stesso giorno si paga di nuovo, ma una sola volta."""
    cost = n1(cost)
    if exempt(user) or cost <= 0:
        return
    with connect() as conn:
        conn.lock(8_100_000 + user["id"])
        if release:
            conn.execute("UPDATE token_ledger SET dedupe = dedupe || '#annullato' WHERE dedupe=?", (release,))
        _insert(conn, user["id"], "REFUND", "EXTRA", cost, op, ref, dedupe, "system", note or "Operazione senza esito: token restituiti")
    events.record("tokens.refund", f"{cost} token restituiti ({note or op})", actor=f"user:{user['email']}", details={"op": op, "ref": ref})


def grant(user_id: int, tokens: float, note: str, actor: str, kind: str = "GRANT") -> Dict[str, Any]:
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
    return {"user_id": user_id, "balance": n1(b["INCLUDED"] + b["EXTRA"])}


# ------------------------------------------------------------------------------------------------ cosa costa
def study_cost(bando_id: str) -> Dict[str, Any]:
    """Un bando già in memoria con regole pubblicate si riusa gratis; rifarne lo studio costa poco; uno nuovo costa il costo vero."""
    with connect() as conn:
        n = conn.execute("SELECT COUNT(*) c FROM rules WHERE bando_id=? AND status='PUBLISHED'", (bando_id,)).fetchone()["c"]
    return {"cached": n > 0, "op": "study_refresh" if n > 0 else "study_new", "cost": COSTS["study_refresh" if n > 0 else "study_new"]["cost"]}


def delivery_key(client_id: Any, project_id: str, bando_id: str) -> str:
    return f"{client_id or '-'}|{project_id}|{bando_id or '-'}"


def delivery_cost(items: Optional[int]) -> float:
    """Consegnare un budget costa di più se è grande: 1 fino a 25 voci, 1,5 fino a 60, 2 oltre. Senza sapere le voci (registrazione) vale il minimo."""
    if not items:
        return DELIVERY_TIERS[0][1]
    return next(c for limit, c in DELIVERY_TIERS if items <= limit)


def metered_status(user: Optional[Dict[str, Any]], op: str, ref: str, cost: float) -> Dict[str, Any]:
    """Quanto resta da pagare per ``op`` su ``ref``: il costo dei dati analizzati meno quanto già pagato negli ultimi 30 giorni (mai di più, mai rimborsi per un costo minore)."""
    cost = n1(cost)
    if exempt(user):
        return {"cost": 0.0, "due": 0.0, "paid": 0.0, "covered": True, "reason": "esente"}
    if not charging():
        return {"cost": cost, "due": 0.0, "paid": 0.0, "covered": True, "free": True, "reason": f"fase di prova: gratuito (in futuro {str(cost).replace('.', ',')} token)"}
    since = _iso(_now() - timedelta(days=WINDOW_DAYS))
    with connect() as conn:
        r = conn.execute("SELECT COALESCE(SUM(-amount), 0) s, MIN(ts) first_ts FROM token_ledger WHERE user_id=? AND op=? AND ref=? AND kind='SPEND' AND ts>=?", (user["id"], op, ref, since)).fetchone()
    paid = n1(r["s"])
    due = n1(max(0.0, cost - paid))
    if due <= 0 and paid > 0:
        until = (datetime.fromisoformat(r["first_ts"].replace("Z", "+00:00")) + timedelta(days=WINDOW_DAYS)).date().isoformat()
        return {"cost": cost, "due": 0.0, "paid": paid, "covered": True, "reason": f"già pagato: incluso fino al {until}"}
    if paid > 0:
        return {"cost": cost, "due": due, "paid": paid, "covered": False, "reason": f"i dati sono più grandi di quelli già pagati ({paid}): si paga solo la differenza"}
    return {"cost": cost, "due": due, "paid": 0.0, "covered": False, "reason": "vale 30 giorni per lo stesso lavoro"}


def charge_metered(user: Optional[Dict[str, Any]], op: str, ref: str, cost: float, note: str) -> Dict[str, Any]:
    st = metered_status(user, op, ref, cost)
    if st["covered"]:
        return {"charged": 0, "key": ref, "ids": [], **st}
    return {**spend(user, op, st["due"], ref=ref, note=note), "key": ref, "op": op}


def undo_metered(user: Optional[Dict[str, Any]], paid: Dict[str, Any]) -> None:
    """L'operazione non è riuscita: i token tornano e il pagamento non risulta."""
    if exempt(user) or not paid.get("charged"):
        return
    with connect() as conn:
        conn.lock(8_100_000 + user["id"])
        _void(conn, paid.get("ids") or [])
    refund(user, paid.get("op", "deliver"), paid["charged"], ref=paid["key"], note="Operazione non riuscita: token restituiti")


def delivery_status(user: Optional[Dict[str, Any]], key: str, items: Optional[int] = None) -> Dict[str, Any]:
    """Il budget è già stato consegnato negli ultimi 30 giorni (e quindi esportarlo o registrarlo ora non costa, o costa solo la differenza)?"""
    st = metered_status(user, "deliver", key, delivery_cost(items))
    return {"covered": st["covered"], "cost": st["due"], "total": st["cost"], "paid": st["paid"], "reason": st["reason"], "free": bool(st.get("free"))}


def charge_delivery(user: Optional[Dict[str, Any]], key: str, items: Optional[int] = None) -> Dict[str, Any]:
    return charge_metered(user, "deliver", key, delivery_cost(items), "Consegna di un budget (30 giorni)")


def undo_delivery(user: Optional[Dict[str, Any]], paid: Dict[str, Any]) -> None:
    undo_metered(user, paid)


def allocation_key(client_id: Any, fiscal_year: int) -> str:
    return f"{client_id or '-'}|{fiscal_year}"


def allocation_cost(expense_lines: int, bandi: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Il costo del piano di allocazione, da 2 a 4,8 token, secondo quanto è corposo ciò che analizza.
    ``bandi``: per ogni bando nel piano, ``units`` = regole pubblicate + requisiti letti / 5 (quanto è corposo il bando)."""
    bal = n1(min(ALLOC_MAX_PART, 0.1 * (max(0, expense_lines) // ALLOC_LINES_PER_STEP)))
    parts = []
    for b in bandi:
        extra = min(ALLOC_BANDO_EXTRA_MAX, ALLOC_UNITS_PER_STEP * b.get("units", 0))
        parts.append({"bando_id": b.get("bando_id"), "name": b.get("name"), "rules": b.get("rules", 0), "requirements": b.get("requirements", 0), "tokens": round(ALLOC_BANDO_BASE + extra, 3)})
    ban = n1(min(ALLOC_MAX_PART, sum(p["tokens"] for p in parts)))
    total = n1(min(ALLOC_BASE + ALLOC_MAX_PART * 2, ALLOC_BASE + bal + ban))
    return {"cost": total, "base": ALLOC_BASE, "balance_tokens": bal, "balance_lines": expense_lines, "bandi_tokens": ban, "bandi": parts, "min": ALLOC_BASE, "max": n1(ALLOC_BASE + 2 * ALLOC_MAX_PART)}


def bandi_size(bando_ids: List[str]) -> List[Dict[str, Any]]:
    """Quanto sono corposi i bandi: regole pubblicate e requisiti letti."""
    out = []
    if not bando_ids:
        return out
    with connect() as conn:
        for bid in dict.fromkeys(bando_ids):
            rules = conn.execute("SELECT COUNT(*) c FROM rules WHERE bando_id=? AND status='PUBLISHED'", (bid,)).fetchone()["c"]
            reqs = conn.execute("SELECT COUNT(*) c FROM requirements WHERE bando_id=?", (bid,)).fetchone()["c"]
            name = conn.execute("SELECT name FROM bandi WHERE bando_id=?", (bid,)).fetchone()
            out.append({"bando_id": bid, "name": name["name"] if name else bid, "rules": int(rules), "requirements": int(reqs), "units": int(rules) + int(reqs) // 5})
    return out


def reward_publish(user: Optional[Dict[str, Any]], client_id: Any, bando_id: str, template_id: int) -> Dict[str, Any]:
    """+0,5 token a chi pubblica un budget per tutti: una volta per cliente e bando, al massimo 10 premi al mese."""
    if exempt(user):
        return {"granted": 0, "reason": "esente"}
    if not client_id:
        return {"granted": 0, "reason": "Il premio è per i budget di un lavoro (un cliente): scegli il lavoro."}
    uid = user["id"]
    month = _iso(_now())[:7]
    with connect() as conn:
        conn.lock(8_100_000 + uid)
        done = conn.execute("SELECT COUNT(*) c FROM token_ledger WHERE user_id=? AND op='publish' AND kind='GRANT' AND ts LIKE ?", (uid, month + "%")).fetchone()["c"]
        if done >= PUBLISH_BONUS_MONTHLY_CAP:
            return {"granted": 0, "reason": f"Hai già ricevuto {PUBLISH_BONUS_MONTHLY_CAP} premi questo mese: il budget è pubblicato lo stesso."}
        i = _insert(conn, uid, "GRANT", "EXTRA", PUBLISH_BONUS, "publish", f"{client_id}|{bando_id}|{template_id}", f"publish:{uid}:{client_id}:{bando_id}", "system", "Premio: budget pubblicato per tutti")
    if i is None:
        return {"granted": 0, "reason": "Per questo cliente e questo bando il premio è già stato dato."}
    events.record("tokens.publish_bonus", f"{PUBLISH_BONUS} token per un budget pubblicato per tutti ({bando_id})", actor=f"user:{user['email']}", details={"template_id": template_id, "bando_id": bando_id})
    return {"granted": PUBLISH_BONUS, "reason": "Grazie: il tuo budget allena il motore collettivo."}


def overview(user: Dict[str, Any]) -> Dict[str, Any]:
    uid = user["id"]
    row = _user_row(uid)
    free = exempt(user)
    with connect() as conn:
        conn.lock(8_100_000 + uid)
        _ensure_grants(conn, uid, row["created_at"])
        b = _buckets(conn, uid)
        ledger = [dict(r) for r in conn.execute("SELECT id, ts, kind, bucket, amount, op, ref, note FROM token_ledger WHERE user_id=? ORDER BY id DESC LIMIT 25", (uid,)).fetchall()]
    for r in ledger:
        r["amount"] = n1(r["amount"])
    total = n1(b["INCLUDED"] + b["EXTRA"])
    now = _now()
    nxt = datetime(now.year + (now.month == 12), 1 if now.month == 12 else now.month + 1, 1, tzinfo=timezone.utc)
    since = _iso(now - timedelta(days=30))
    with connect() as conn:
        spent_30 = n1(-conn.execute("SELECT COALESCE(SUM(amount),0) s FROM token_ledger WHERE user_id=? AND kind='SPEND' AND ts>=?", (uid, since)).fetchone()["s"])
    plan = {"monthly_eur": PLAN_MONTHLY_EUR, "yearly_eur": PLAN_YEARLY_EUR, "tokens_per_month": MONTHLY_INCLUDED, "yearly_saving_eur": round(PLAN_MONTHLY_EUR * 12 - PLAN_YEARLY_EUR, 2),
            "yearly_saving_pct": round(100 * (1 - PLAN_YEARLY_EUR / (PLAN_MONTHLY_EUR * 12)), 1)}
    charge = charging()
    return {"charging": charge, "exempt": free, "balance": total, "included": b["INCLUDED"], "extra": b["EXTRA"], "monthly": MONTHLY_INCLUDED, "cap": ROLLOVER_CAP, "overdraft": OVERDRAFT,
            "next_grant": nxt.date().isoformat(), "days_until_grant": max(0, (nxt - now).days), "spent_30_days": spent_30,
            "low": charge and (not free) and total <= 3, "empty": charge and (not free) and total <= 0, "plan": plan, "publish_bonus": PUBLISH_BONUS, "publish_bonus_monthly_cap": PUBLISH_BONUS_MONTHLY_CAP,
            "costs": [{"op": k, **v} for k, v in COSTS.items()], "packs": PACKS, "unit_price_eur": UNIT_PRICE_EUR, "payments_active": False, "ledger": ledger}
