"""Marketing del Quartier Generale: LinkedIn (profilo del fondatore e pagina QUANTO), post con approvazione, campagne, statistiche, visite al sito.

Ripreso da QUANTO Growth e portato dentro QUANTO perché il titolare veda tutto in un posto e il chatbot interno possa interrogarlo.
Regole:
- un post si pubblica solo se è stato approvato da una persona (il database rifiuta il contrario);
- i token di LinkedIn sono cifrati con ``QUANTO_FILE_KEY``; senza chiave non si collega nulla;
- ogni risposta delle API di LinkedIn finisce in ``raw_payloads`` per sempre, così si potrà rianalizzare;
- le metriche si aggiungono, non si riscrivono (trigger nel database): lo storico resta;
- le campagne a pagamento si leggono via API solo quando LinkedIn concede l'accesso «Advertising API»: fino ad allora si inseriscono a mano
  (o da CSV di Campaign Manager) e il Quartier Generale lo dice;
- le visite al sito si registrano con una sessione casuale: nessun nome, nessun indirizzo, nessun IP salvato.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import time
import urllib.parse
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.core import access, auth, crypto_store, events
from app.core.db import connect

API = "https://api.linkedin.com/rest"
API_V2 = "https://api.linkedin.com/v2"
AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_VERSION = "202609"
# Permessi oggi concessi all'app (OpenID + Share on LinkedIn). Quando LinkedIn approva la Community Management API o l'Advertising API
# si allargano con LINKEDIN_SCOPES_PROFILE / LINKEDIN_SCOPES_PAGE senza toccare il codice.
DEFAULT_SCOPES = {"profile": "openid profile w_member_social", "page": "openid profile w_member_social"}
POST_STATES = ("BOZZA", "DA_APPROVARE", "APPROVATO", "PROGRAMMATO", "PUBBLICATO", "ERRORE")
CAMPAIGN_STATES = ("BOZZA", "ATTIVA", "IN_PAUSA", "CONCLUSA")
MAX_EVENTS_PER_DAY = 50_000


class MarketingError(ValueError):
    pass


def _now() -> str:
    return events.now_iso()


# ------------------------------------------------------------------------------------------------ account e collegamento
def configured() -> Dict[str, Any]:
    has_app = bool(os.getenv("LINKEDIN_CLIENT_ID", "").strip() and os.getenv("LINKEDIN_CLIENT_SECRET", "").strip())
    has_key = bool(os.getenv("QUANTO_FILE_KEY", "").strip())
    missing = [n for n, ok in (("LINKEDIN_CLIENT_ID e LINKEDIN_CLIENT_SECRET", has_app), ("QUANTO_FILE_KEY", has_key)) if not ok]
    return {"ready": not missing, "missing": missing, "redirect_uri": redirect_uri()}


def redirect_uri() -> str:
    return f"{access.public_url()}/api/v2/marketing/linkedin/callback"


def _public_account(r) -> Dict[str, Any]:
    return {k: r[k] for k in ("id", "kind", "name", "target_urn", "scopes", "expires_at", "status", "last_error", "connected_at", "created_at")}


def accounts() -> List[Dict[str, Any]]:
    """Gli account LinkedIn. Al primo accesso nascono i due previsti: il profilo del fondatore e la pagina QUANTO."""
    with connect() as conn:
        rows = conn.execute("SELECT * FROM li_accounts ORDER BY id").fetchall()
        if not rows:
            now = _now()
            conn.execute("INSERT INTO li_accounts (kind, name, created_at) VALUES ('profile','Profilo del fondatore',?), ('page','Pagina QUANTO',?)", (now, now))
            rows = conn.execute("SELECT * FROM li_accounts ORDER BY id").fetchall()
    return [_public_account(r) for r in rows]


def authorize_url(account_id: int, actor: str) -> str:
    cfg = configured()
    if not cfg["ready"]:
        raise MarketingError("Per collegare LinkedIn mancano: " + ", ".join(cfg["missing"]))
    with connect() as conn:
        acc = conn.execute("SELECT * FROM li_accounts WHERE id=?", (account_id,)).fetchone()
    if acc is None:
        raise KeyError(account_id)
    scopes = os.getenv("LINKEDIN_SCOPES_PROFILE" if acc["kind"] == "profile" else "LINKEDIN_SCOPES_PAGE", "") or DEFAULT_SCOPES[acc["kind"]]
    state = auth.sign_claims({"typ": "li_state", "acc": account_id, "who": actor, "exp": int(time.time()) + 900})
    q = {"response_type": "code", "client_id": os.environ["LINKEDIN_CLIENT_ID"].strip(), "redirect_uri": redirect_uri(), "state": state, "scope": scopes}
    return f"{AUTH_URL}?{urllib.parse.urlencode(q, quote_via=urllib.parse.quote)}"


def _enc(v: Optional[str]) -> Optional[bytes]:
    return crypto_store.encrypt(v.encode()) if v else None


def _dec(v) -> str:
    return crypto_store.decrypt(bytes(v)).decode()


def _raw(endpoint: str, status: Optional[int], payload: Any) -> None:
    with connect() as conn:
        conn.execute("INSERT INTO raw_payloads (ts, source, endpoint, status, payload) VALUES (?, 'linkedin', ?, ?, ?)",
                     (_now(), endpoint, status, json.dumps(payload, ensure_ascii=False, default=str)[:200_000]))


def complete_authorization(code: str, state: str, http: Optional[httpx.Client] = None) -> Dict[str, Any]:
    claims = auth.verify_claims(state or "")
    if not claims or claims.get("typ") != "li_state":
        raise MarketingError("Richiesta di collegamento scaduta o non valida: riprova dal Quartier Generale")
    http = http or httpx.Client(timeout=20)
    r = http.post(TOKEN_URL, data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri(),
                                   "client_id": os.environ["LINKEDIN_CLIENT_ID"].strip(), "client_secret": os.environ["LINKEDIN_CLIENT_SECRET"].strip()})
    _raw("oauth.token", r.status_code, {"ok": r.status_code == 200})                       # mai il token in chiaro
    if r.status_code != 200:
        raise MarketingError(f"LinkedIn ha rifiutato il collegamento ({r.status_code})")
    tok = r.json()
    access_token = tok["access_token"]
    who = http.get(f"{API_V2}/userinfo", headers={"Authorization": f"Bearer {access_token}"})
    info = who.json() if who.status_code == 200 else {}
    _raw("v2/userinfo", who.status_code, {k: info.get(k) for k in ("sub", "name", "locale")})
    urn = f"urn:li:person:{info['sub']}" if info.get("sub") else None
    expires = (datetime.now(timezone.utc) + timedelta(seconds=int(tok.get("expires_in", 0)))).isoformat(timespec="seconds") if tok.get("expires_in") else None
    acc_id = int(claims["acc"])
    with connect() as conn:
        conn.execute("UPDATE li_accounts SET target_urn=COALESCE(?, target_urn), scopes=?, access_token_enc=?, refresh_token_enc=?, expires_at=?, status='collegato', "
                     "last_error=NULL, connected_at=?, name=CASE WHEN kind='profile' AND ? <> '' THEN ? ELSE name END WHERE id=?",
                     (urn, (tok.get("scope") or "").replace(",", " "), _enc(access_token), _enc(tok.get("refresh_token")), expires, _now(),
                      info.get("name") or "", info.get("name") or "", acc_id))
    events.record("marketing.linkedin_connect", f"Account LinkedIn {acc_id} collegato", actor=str(claims.get("who") or "titolare"))
    return {"account_id": acc_id, "target_urn": urn}


def _token(acc) -> str:
    if not acc["access_token_enc"]:
        raise MarketingError("Account LinkedIn non collegato")
    if acc["expires_at"] and acc["expires_at"] < datetime.now(timezone.utc).isoformat(timespec="seconds"):
        with connect() as conn:
            conn.execute("UPDATE li_accounts SET status='scaduto', last_error='Token scaduto: ricollega' WHERE id=?", (acc["id"],))
        raise MarketingError("Il collegamento a LinkedIn è scaduto: ricollega l'account")
    return _dec(acc["access_token_enc"])


_RESERVED = set("\\|{}@[]()<>#*_~")


def to_little_text(text: str) -> str:
    """Testo nel formato dei post di LinkedIn: caratteri riservati protetti, #parola diventa un hashtag vero."""
    out, last = [], 0
    for m in re.finditer(r"#(\w+)", text):
        out.append("".join("\\" + ch if ch in _RESERVED else ch for ch in text[last:m.start()]))
        out.append("{hashtag|\\#|" + m.group(1) + "}")
        last = m.end()
    out.append("".join("\\" + ch if ch in _RESERVED else ch for ch in text[last:]))
    return "".join(out)


def publish_to_linkedin(acc, text: str, link: Optional[str], http: Optional[httpx.Client] = None) -> str:
    if not acc["target_urn"] or "w_member_social" not in (acc["scopes"] or "") and "w_organization_social" not in (acc["scopes"] or ""):
        raise MarketingError("Questo account non ha il permesso di pubblicare: ricollegalo")
    body: Dict[str, Any] = {"author": acc["target_urn"], "commentary": to_little_text(text), "visibility": "PUBLIC",
                            "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
                            "lifecycleState": "PUBLISHED", "isReshareDisabledByAuthor": False}
    if link:
        body["content"] = {"article": {"source": link, "title": link}}
    http = http or httpx.Client(timeout=30)
    r = http.post(f"{API}/posts", json=body, headers={"Authorization": f"Bearer {_token(acc)}", "Linkedin-Version": LINKEDIN_VERSION, "X-Restli-Protocol-Version": "2.0.0"})
    try:
        resp = r.json() if r.content else None
    except ValueError:
        resp = {"text": r.text[:2000]}
    _raw("posts.create", r.status_code, resp)
    if r.status_code not in (200, 201):
        raise MarketingError(f"LinkedIn non ha pubblicato il post ({r.status_code})")
    urn = r.headers.get("x-restli-id") or r.headers.get("x-linkedin-id")
    if not urn:
        raise MarketingError("LinkedIn non ha restituito l'identificativo del post")
    return urn


# ------------------------------------------------------------------------------------------------ post
def _post(conn, post_id: int):
    r = conn.execute("SELECT * FROM li_posts WHERE id=?", (post_id,)).fetchone()
    if r is None:
        raise KeyError(post_id)
    return r


def list_posts() -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT p.*, a.name AS account_name, c.name AS campaign_name, m.impressions, m.reactions, m.comments, m.clicks FROM li_posts p "
            "LEFT JOIN li_accounts a ON a.id=p.account_id LEFT JOIN li_campaigns c ON c.id=p.campaign_id "
            "LEFT JOIN LATERAL (SELECT * FROM li_post_metrics x WHERE x.post_id=p.id ORDER BY x.id DESC LIMIT 1) m ON TRUE "
            "ORDER BY CASE p.status WHEN 'DA_APPROVARE' THEN 0 WHEN 'PROGRAMMATO' THEN 1 WHEN 'APPROVATO' THEN 2 WHEN 'BOZZA' THEN 3 ELSE 4 END, p.updated_at DESC").fetchall()
    return [dict(r) for r in rows]


def save_post(data: Dict[str, Any], actor: str, post_id: Optional[int] = None) -> Dict[str, Any]:
    text = (data.get("text") or "").strip()
    if not text:
        raise MarketingError("Scrivi il testo del post")
    if len(text) > 3000:
        raise MarketingError("LinkedIn accetta al massimo 3.000 caratteri")
    link = (data.get("link") or "").strip() or None
    if link and not re.match(r"^https?://", link):
        raise MarketingError("Il link deve iniziare con https://")
    now = _now()
    with connect() as conn:
        if post_id is None:
            row = conn.execute("INSERT INTO li_posts (account_id, campaign_id, text, link, scheduled_at, status, created_by, created_at, updated_at) "
                               "VALUES (?,?,?,?,?,'BOZZA',?,?,?) RETURNING *", (data.get("account_id"), data.get("campaign_id"), text, link,
                                                                                data.get("scheduled_at") or None, actor, now, now)).fetchone()
        else:
            cur = _post(conn, post_id)
            if cur["status"] in ("PUBBLICATO",):
                raise MarketingError("Un post pubblicato non si modifica")
            # modificare un post approvato lo rimanda all'approvazione: nessuno pubblica un testo che il titolare non ha visto
            row = conn.execute("UPDATE li_posts SET account_id=?, campaign_id=?, text=?, link=?, scheduled_at=?, status='BOZZA', approved_by=NULL, approved_at=NULL, "
                               "updated_at=? WHERE id=? RETURNING *", (data.get("account_id"), data.get("campaign_id"), text, link,
                                                                      data.get("scheduled_at") or None, now, post_id)).fetchone()
    events.record("marketing.post_save", f"Post {row['id']} salvato", actor=actor)
    return dict(row)


def set_status(post_id: int, action: str, actor: str) -> Dict[str, Any]:
    """Passi del post: invia → approva → programma o pubblica. Ogni passo controlla da dove parte."""
    now = _now()
    with connect() as conn:
        p = _post(conn, post_id)
        st = p["status"]
        if action == "submit" and st in ("BOZZA", "ERRORE"):
            row = conn.execute("UPDATE li_posts SET status='DA_APPROVARE', error=NULL, updated_at=? WHERE id=? RETURNING *", (now, post_id)).fetchone()
        elif action == "approve" and st in ("BOZZA", "DA_APPROVARE"):
            new = "PROGRAMMATO" if p["scheduled_at"] else "APPROVATO"
            row = conn.execute("UPDATE li_posts SET status=?, approved_by=?, approved_at=?, updated_at=? WHERE id=? RETURNING *", (new, actor, now, now, post_id)).fetchone()
        elif action == "back" and st in ("DA_APPROVARE", "APPROVATO", "PROGRAMMATO", "ERRORE"):
            row = conn.execute("UPDATE li_posts SET status='BOZZA', approved_by=NULL, approved_at=NULL, updated_at=? WHERE id=? RETURNING *", (now, post_id)).fetchone()
        elif action == "mark_published" and st in ("APPROVATO", "PROGRAMMATO"):
            row = conn.execute("UPDATE li_posts SET status='PUBBLICATO', published_at=?, updated_at=? WHERE id=? RETURNING *", (now, now, post_id)).fetchone()
        else:
            raise MarketingError("Questo passaggio non è possibile per lo stato attuale del post")
    events.record(f"marketing.post_{action}", f"Post {post_id}: {action}", actor=actor)
    return dict(row)


def publish_now(post_id: int, actor: str, http: Optional[httpx.Client] = None) -> Dict[str, Any]:
    with connect() as conn:
        p = _post(conn, post_id)
        if p["status"] not in ("APPROVATO", "PROGRAMMATO"):
            raise MarketingError("Si pubblica solo un post approvato")
        acc = conn.execute("SELECT * FROM li_accounts WHERE id=?", (p["account_id"],)).fetchone() if p["account_id"] else None
    if acc is None:
        raise MarketingError("Scegli l'account LinkedIn su cui pubblicare")
    try:
        urn = publish_to_linkedin(acc, p["text"], p["link"], http=http)
    except MarketingError as exc:
        with connect() as conn:
            conn.execute("UPDATE li_posts SET status='ERRORE', error=?, updated_at=? WHERE id=?", (str(exc)[:500], _now(), post_id))
        events.record("marketing.post_publish", f"Post {post_id} non pubblicato: {exc}", status="FAIL", actor=actor)
        raise
    now = _now()
    with connect() as conn:
        row = conn.execute("UPDATE li_posts SET status='PUBBLICATO', urn=?, published_at=?, error=NULL, updated_at=? WHERE id=? RETURNING *", (urn, now, now, post_id)).fetchone()
    events.record("marketing.post_publish", f"Post {post_id} pubblicato su LinkedIn", actor=actor)
    return dict(row)


def publish_due(actor: str = "cron", http: Optional[httpx.Client] = None) -> Dict[str, int]:
    """Pubblica i post programmati la cui ora è passata (lo chiama il lavoro periodico)."""
    with connect() as conn:
        due = [r["id"] for r in conn.execute("SELECT id FROM li_posts WHERE status='PROGRAMMATO' AND scheduled_at <= ? ORDER BY scheduled_at", (_now(),)).fetchall()]
    ok = ko = 0
    for pid in due:
        try:
            publish_now(pid, actor, http=http); ok += 1
        except MarketingError:
            ko += 1
    return {"published": ok, "failed": ko}


def delete_post(post_id: int, actor: str) -> None:
    with connect() as conn:
        p = _post(conn, post_id)
        if p["status"] == "PUBBLICATO":
            raise MarketingError("Un post pubblicato resta nello storico")
        conn.execute("DELETE FROM li_posts WHERE id=?", (post_id,))
    events.record("marketing.post_delete", f"Post {post_id} eliminato", actor=actor)


def add_post_metrics(post_id: int, m: Dict[str, Any], actor: str) -> Dict[str, Any]:
    vals = {k: _int(m.get(k)) for k in ("impressions", "reach", "reactions", "comments", "reshares", "clicks")}
    if all(v is None for v in vals.values()):
        raise MarketingError("Inserisci almeno un numero")
    with connect() as conn:
        _post(conn, post_id)
        row = conn.execute("INSERT INTO li_post_metrics (post_id, ts, impressions, reach, reactions, comments, reshares, clicks, source) VALUES (?,?,?,?,?,?,?,?,'manuale') RETURNING *",
                           (post_id, _now(), *vals.values())).fetchone()
    events.record("marketing.metrics", f"Statistiche del post {post_id} aggiornate", actor=actor)
    return dict(row)


def _int(v: Any) -> Optional[int]:
    if v in (None, ""):
        return None
    n = int(float(str(v).replace(".", "").replace(",", ".")) if isinstance(v, str) else v)
    if n < 0:
        raise MarketingError("I numeri non possono essere negativi")
    return n


def _eur(v: Any) -> Optional[float]:
    if v in (None, ""):
        return None
    s = str(v).strip().replace("€", "").replace(" ", "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    n = float(s)
    if n < 0:
        raise MarketingError("Gli importi non possono essere negativi")
    return round(n, 2)


# ------------------------------------------------------------------------------------------------ campagne
def list_campaigns() -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT c.*, COALESCE(SUM(m.impressions),0) impressions, COALESCE(SUM(m.clicks),0) clicks, COALESCE(SUM(m.spend_eur),0) spend_eur, "
            "COALESCE(SUM(m.leads),0) leads, COALESCE(SUM(m.conversions),0) conversions, (SELECT COUNT(*) FROM li_posts p WHERE p.campaign_id=c.id) posts "
            "FROM li_campaigns c LEFT JOIN li_campaign_metrics m ON m.campaign_id=c.id GROUP BY c.id ORDER BY c.created_at DESC").fetchall()
    out = []
    for r in rows:
        d = {k: (float(v) if hasattr(v, "as_tuple") else v) for k, v in dict(r).items()}
        d["ctr_pct"] = round(d["clicks"] / d["impressions"] * 100, 2) if d["impressions"] else None
        d["cpc_eur"] = round(d["spend_eur"] / d["clicks"], 2) if d["clicks"] else None
        d["cpl_eur"] = round(d["spend_eur"] / d["leads"], 2) if d["leads"] else None
        out.append(d)
    return out


def save_campaign(data: Dict[str, Any], actor: str, campaign_id: Optional[int] = None) -> Dict[str, Any]:
    name = (data.get("name") or "").strip()
    if not name:
        raise MarketingError("Dai un nome alla campagna")
    status = data.get("status") or "BOZZA"
    if status not in CAMPAIGN_STATES:
        raise MarketingError("Stato della campagna non valido")
    vals = (name[:160], (data.get("objective") or "")[:160], data.get("account_id"), _eur(data.get("budget_eur")), data.get("start_day") or None,
            data.get("end_day") or None, status, (data.get("notes") or "")[:2000])
    with connect() as conn:
        if campaign_id is None:
            row = conn.execute("INSERT INTO li_campaigns (name, objective, account_id, budget_eur, start_day, end_day, status, notes, created_by, created_at) "
                               "VALUES (?,?,?,?,?,?,?,?,?,?) RETURNING *", (*vals, actor, _now())).fetchone()
        else:
            row = conn.execute("UPDATE li_campaigns SET name=?, objective=?, account_id=?, budget_eur=?, start_day=?, end_day=?, status=?, notes=? WHERE id=? RETURNING *",
                               (*vals, campaign_id)).fetchone()
            if row is None:
                raise KeyError(campaign_id)
    events.record("marketing.campaign_save", f"Campagna «{name}» salvata", actor=actor)
    return {k: (float(v) if hasattr(v, "as_tuple") else v) for k, v in dict(row).items()}


def add_campaign_day(campaign_id: int, m: Dict[str, Any], actor: str, source: str = "manuale") -> None:
    day = (m.get("day") or "").strip()[:10]
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", day):
        raise MarketingError("Indica il giorno (AAAA-MM-GG)")
    with connect() as conn:
        if conn.execute("SELECT 1 FROM li_campaigns WHERE id=?", (campaign_id,)).fetchone() is None:
            raise KeyError(campaign_id)
        conn.execute("INSERT INTO li_campaign_metrics (campaign_id, day, impressions, clicks, spend_eur, leads, conversions, source, ts) VALUES (?,?,?,?,?,?,?,?,?)",
                     (campaign_id, day, _int(m.get("impressions")), _int(m.get("clicks")), _eur(m.get("spend_eur")), _int(m.get("leads")),
                      _int(m.get("conversions")), source, _now()))
    events.record("marketing.metrics", f"Campagna {campaign_id}: dati del {day}", actor=actor)


_CSV_COLS = {"day": ("data", "giorno", "start date", "date", "day"), "impressions": ("impressioni", "impressions"), "clicks": ("clic", "clicks"),
             "spend_eur": ("spesa", "total spent", "spend", "importo speso"), "leads": ("lead", "leads", "contatti"), "conversions": ("conversioni", "conversions")}


def import_campaign_csv(campaign_id: int, content: str, actor: str) -> Dict[str, int]:
    """Importa le righe giornaliere esportate da Campaign Manager (o un CSV con le stesse colonne, in italiano o in inglese)."""
    sample = content[:2000]
    delim = ";" if sample.count(";") > sample.count(",") else ","
    reader = csv.DictReader(io.StringIO(content), delimiter=delim)
    heads = {h: (h or "").strip().lower() for h in (reader.fieldnames or [])}
    pick = {k: next((h for h, low in heads.items() if any(low == a or low.startswith(a) for a in alts)), None) for k, alts in _CSV_COLS.items()}
    if not pick["day"]:
        raise MarketingError("Nel file manca la colonna della data (data, giorno o date)")
    ok = skipped = 0
    for row in reader:
        raw_day = (row.get(pick["day"]) or "").strip()
        day = raw_day
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
            try:
                day = datetime.strptime(raw_day[:10], fmt).date().isoformat(); break
            except ValueError:
                continue
        try:
            add_campaign_day(campaign_id, {k: row.get(c) if c else None for k, c in pick.items()} | {"day": day}, actor, source="csv")
            ok += 1
        except (MarketingError, ValueError):
            skipped += 1
    return {"imported": ok, "skipped": skipped}


def add_followers(account_id: int, day: str, followers: Any, actor: str) -> None:
    n = _int(followers)
    if n is None:
        raise MarketingError("Indica il numero di follower")
    with connect() as conn:
        conn.execute("INSERT INTO li_followers (account_id, day, followers, source, ts) VALUES (?,?,?,'manuale',?)", (account_id, (day or date.today().isoformat())[:10], n, _now()))
    events.record("marketing.metrics", f"Follower dell'account {account_id}: {n}", actor=actor)


# ------------------------------------------------------------------------------------------------ visite al sito
_KINDS = {"view", "click", "cta", "video", "form"}


def track(ev: Dict[str, Any]) -> bool:
    """Registra una visita o un clic sul sito pubblico. Nessun dato personale: sessione casuale generata dal browser, niente IP."""
    kind = str(ev.get("kind") or "view")[:20]
    session = re.sub(r"[^A-Za-z0-9-]", "", str(ev.get("session") or ""))[:40]
    if kind not in _KINDS or len(session) < 8:
        return False
    today = date.today().isoformat()
    with connect() as conn:
        n = conn.execute("SELECT COUNT(*) n FROM site_events WHERE ts >= ?", (today,)).fetchone()["n"]
        if n >= MAX_EVENTS_PER_DAY:
            return False
        clip = lambda k, m=200: str(ev.get(k) or "")[:m]                                    # noqa: E731
        ref = clip("referrer", 300)
        ref = re.sub(r"[?#].*$", "", ref)                                                   # mai parametri altrui nel database
        conn.execute("INSERT INTO site_events (ts, session, kind, path, label, referrer, utm_source, utm_medium, utm_campaign, device) VALUES (?,?,?,?,?,?,?,?,?,?)",
                     (_now(), session, kind, re.sub(r"[?#].*$", "", clip("path")), clip("label", 120), ref, clip("utm_source", 80),
                      clip("utm_medium", 80), clip("utm_campaign", 120), clip("device", 20)))
    return True


# ------------------------------------------------------------------------------------------------ panoramica
def overview(days: int = 30) -> Dict[str, Any]:
    since = (date.today() - timedelta(days=days - 1)).isoformat()
    with connect() as conn:
        visits_by_day = [dict(r) for r in conn.execute(
            "SELECT substr(ts,1,10) AS day, COUNT(DISTINCT session) AS visitors, COUNT(*) FILTER (WHERE kind='view') AS views, COUNT(*) FILTER (WHERE kind IN ('cta','form')) AS actions "
            "FROM site_events WHERE ts >= ? GROUP BY 1 ORDER BY 1", (since,)).fetchall()]
        sources = [dict(r) for r in conn.execute(
            "SELECT CASE WHEN utm_source<>'' THEN utm_source WHEN referrer ILIKE '%linkedin%' THEN 'linkedin' WHEN referrer ILIKE '%google%' THEN 'google' "
            "WHEN referrer='' THEN 'diretto' ELSE 'altri siti' END fonte, COUNT(DISTINCT session) visitors FROM site_events WHERE ts >= ? GROUP BY 1 ORDER BY 2 DESC LIMIT 8",
            (since,)).fetchall()]
        posts = {r["status"]: r["n"] for r in conn.execute("SELECT status, COUNT(*) n FROM li_posts GROUP BY status").fetchall()}
        reach = conn.execute("SELECT COALESCE(SUM(impressions),0) imp, COALESCE(SUM(reactions),0) re, COALESCE(SUM(comments),0) co, COALESCE(SUM(clicks),0) cl FROM "
                             "(SELECT DISTINCT ON (post_id) * FROM li_post_metrics ORDER BY post_id, id DESC) last").fetchone()
        spend = conn.execute("SELECT COALESCE(SUM(spend_eur),0) s, COALESCE(SUM(leads),0) l, COALESCE(SUM(clicks),0) c FROM li_campaign_metrics WHERE day >= ?", (since,)).fetchone()
        followers = [dict(r) for r in conn.execute(
            "SELECT DISTINCT ON (f.account_id) f.account_id, a.name, f.followers, f.day FROM li_followers f JOIN li_accounts a ON a.id=f.account_id ORDER BY f.account_id, f.day DESC, f.id DESC").fetchall()]
        signups = conn.execute("SELECT COUNT(*) n FROM access_requests WHERE requested_at >= ?", (since,)).fetchone()["n"]
    visitors = sum(d["visitors"] for d in visits_by_day)
    return {
        "days": days, "visits_by_day": visits_by_day, "sources": sources, "visitors": visitors,
        "cta": sum(d["actions"] for d in visits_by_day), "signups": signups,
        "conversion_pct": round(signups / visitors * 100, 1) if visitors and signups <= visitors else None,      # le richieste di prima della misura non hanno visite: niente percentuali oltre il 100
        "posts": posts, "post_totals": {"impressions": reach["imp"], "reactions": reach["re"], "comments": reach["co"], "clicks": reach["cl"]},
        "ads": {"spend_eur": float(spend["s"]), "leads": spend["l"], "clicks": spend["c"]}, "followers": followers,
        "linkedin": configured(),
    }
