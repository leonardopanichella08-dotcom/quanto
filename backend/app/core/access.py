"""Richieste di accesso: chi si registra non entra subito, il titolare decide dal Quartier Generale e assegna il livello.

Percorso:
  1. L'utente compila il modulo (nome, e-mail, password, studio facoltativo): nasce un account **non attivo** e una richiesta IN ATTESA.
  2. Il Quartier Generale la vede subito (contatore e sezione «Accessi»). Il titolare sceglie il livello e approva, oppure rifiuta.
  3. All'approvazione l'account diventa attivo con il livello scelto e QUANTO prepara già il testo dell'e-mail da inviare all'utente
     (oggetto e corpo pronti, con il collegamento per entrare). QUANTO non invia e-mail da solo: il titolare la apre nella propria posta con un clic
     e poi segna «inviata». Così nessuno riceve un messaggio che il titolare non ha visto.

Livelli: «Utente» (lavora sui propri clienti) e «Manager» (come Utente, in più avvia a mano gli aggiornamenti automatici). Sono i due ruoli già esistenti;
il Quartier Generale resta riservato al titolare (QUANTO_OWNER_EMAIL) e nessun livello lo apre.
L'utente in attesa non entra e, se prova ad accedere con la password giusta, legge un messaggio chiaro invece di «credenziali errate».
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from app.core import events, users
from app.core.db import connect

LEVELS = {"USER": "Utente", "MANAGER": "Manager"}
LEVEL_HELP = {"USER": "Lavora sui propri clienti: profilo, agevolazioni, allocazione, budget e confronto.",
              "MANAGER": "Come l'Utente, in più può avviare a mano gli aggiornamenti automatici dei dati. Il Quartier Generale resta riservato al titolare."}
MAX_PENDING = 200                       # tetto alle richieste in attesa: il modulo è pubblico e non deve poter riempire il database


class AccessError(ValueError):
    pass


def public_url() -> str:
    return (os.getenv("QUANTO_PUBLIC_URL") or "https://quanto-self.vercel.app").rstrip("/")


# ------------------------------------------------------------------------------------------------ l'e-mail già pronta
def build_mail(kind: str, name: str, level: Optional[str] = None, reason: str = "") -> Dict[str, str]:
    """Oggetto e corpo dell'e-mail per l'utente. ``kind``: «approved» o «rejected»."""
    first = (name or "").strip().split(" ")[0] or "buongiorno"
    url = public_url()
    if kind == "approved":
        lvl = LEVELS.get(level or "USER", "Utente")
        extra = ("\nCon il livello Manager puoi anche avviare a mano gli aggiornamenti automatici dei dati.\n" if level == "MANAGER" else "")
        return {"subject": "La tua richiesta di accesso a QUANTO è stata approvata",
                "body": (f"Ciao {first},\n\n"
                         f"la tua richiesta di accesso a QUANTO è stata approvata: il tuo livello è «{lvl}».\n\n"
                         f"Per entrare:\n"
                         f"1. vai su {url}\n"
                         f"2. premi «Accedi»\n"
                         f"3. usa questa e-mail e la password che hai scelto quando hai fatto la richiesta.\n"
                         f"{extra}\n"
                         f"In questa fase l'uso è gratuito. Se hai dubbi o qualcosa non funziona, rispondi a questo messaggio.\n\n"
                         f"A presto,\nil team di QUANTO\n")}
    why = f"\n{reason.strip()}\n" if reason.strip() else ""
    return {"subject": "Sulla tua richiesta di accesso a QUANTO",
            "body": (f"Ciao {first},\n\n"
                     f"grazie per aver richiesto l'accesso a QUANTO. Per ora non possiamo attivare il tuo account.\n{why}\n"
                     f"Se pensi sia un errore o vuoi darci più informazioni sul tuo studio, rispondi a questo messaggio.\n\n"
                     f"Il team di QUANTO\n")}


# ------------------------------------------------------------------------------------------------ la richiesta
def _row(r) -> Dict[str, Any]:
    d = dict(r)
    d["level_label"] = LEVELS.get(d.get("level") or "", None)
    return d


def request_access(email: str, name: str, password: str, studio_name: str = "") -> Dict[str, Any]:
    """Crea l'account non attivo e la richiesta in attesa. Gli errori (e-mail già usata, password debole) arrivano come ``users.UserError``."""
    with connect() as conn:
        if conn.execute("SELECT COUNT(*) n FROM access_requests WHERE status='PENDING'").fetchone()["n"] >= MAX_PENDING:
            raise AccessError("Ci sono troppe richieste in attesa: riprova tra qualche giorno")
    user = users.create_user(email, name, password, role="USER", actor="self-signup", active=False)
    studio = (studio_name or "").strip()[:160]
    with connect() as conn:
        if studio:
            conn.execute("UPDATE users SET studio_name=? WHERE id=?", (studio, user["id"]))
        row = conn.execute("INSERT INTO access_requests (user_id, email, name, status, requested_at) VALUES (?,?,?,'PENDING',?) RETURNING *",
                           (user["id"], user["email"], user["name"], events.now_iso())).fetchone()
    events.record("access.request", f"Richiesta di accesso da {user['email']}", actor="self-signup", details={"request_id": row["id"], "studio": bool(studio)})
    return _row(row)


def list_requests(status: Optional[str] = None) -> List[Dict[str, Any]]:
    sql = ("SELECT r.*, u.studio_name, u.last_login_at FROM access_requests r JOIN users u ON u.id = r.user_id"
           + (" WHERE r.status=?" if status else "") + " ORDER BY CASE r.status WHEN 'PENDING' THEN 0 ELSE 1 END, r.requested_at DESC")
    with connect() as conn:
        return [_row(r) for r in conn.execute(sql, (status,) if status else ()).fetchall()]


def pending_count() -> int:
    with connect() as conn:
        return conn.execute("SELECT COUNT(*) n FROM access_requests WHERE status='PENDING'").fetchone()["n"]


def counts() -> Dict[str, int]:
    with connect() as conn:
        out = {s: 0 for s in ("PENDING", "APPROVED", "REJECTED")}
        for r in conn.execute("SELECT status, COUNT(*) n FROM access_requests GROUP BY status").fetchall():
            out[r["status"]] = r["n"]
        out["mail_to_send"] = conn.execute("SELECT COUNT(*) n FROM access_requests WHERE status<>'PENDING' AND mail_sent_at IS NULL").fetchone()["n"]
    return out


def _pending(conn, request_id: int):
    r = conn.execute("SELECT * FROM access_requests WHERE id=?", (request_id,)).fetchone()
    if r is None:
        raise KeyError(request_id)
    if r["status"] != "PENDING":
        raise AccessError("Questa richiesta è già stata decisa")
    return r


def approve(request_id: int, level: str, actor: str) -> Dict[str, Any]:
    """Attiva l'account con il livello scelto e prepara l'e-mail di conferma."""
    if level not in LEVELS:
        raise AccessError("Scegli il livello: Utente o Manager")
    with connect() as conn:
        r = _pending(conn, request_id)
        mail = build_mail("approved", r["name"], level)
        now = events.now_iso()
        conn.execute("UPDATE users SET role=?, active=TRUE, token_version=token_version+1 WHERE id=?", (level, r["user_id"]))
        row = conn.execute("UPDATE access_requests SET status='APPROVED', level=?, decided_at=?, decided_by=?, mail_subject=?, mail_body=? WHERE id=? RETURNING *",
                           (level, now, actor, mail["subject"], mail["body"], request_id)).fetchone()
    events.record("access.approve", f"Accesso di {r['email']} approvato come {LEVELS[level]}", actor=actor, details={"request_id": request_id, "level": level})
    return _row(row)


def reject(request_id: int, reason: str, actor: str) -> Dict[str, Any]:
    """Rifiuta la richiesta: l'account resta non attivo. Prepara comunque una risposta cortese (il motivo è facoltativo)."""
    with connect() as conn:
        r = _pending(conn, request_id)
        mail = build_mail("rejected", r["name"], reason=reason or "")
        row = conn.execute("UPDATE access_requests SET status='REJECTED', decided_at=?, decided_by=?, note=?, mail_subject=?, mail_body=? WHERE id=? RETURNING *",
                           (events.now_iso(), actor, (reason or "").strip()[:500] or None, mail["subject"], mail["body"], request_id)).fetchone()
    events.record("access.reject", f"Richiesta di {r['email']} rifiutata", actor=actor, details={"request_id": request_id})
    return _row(row)


def mark_mail_sent(request_id: int, actor: str) -> Dict[str, Any]:
    with connect() as conn:
        r = conn.execute("SELECT * FROM access_requests WHERE id=?", (request_id,)).fetchone()
        if r is None:
            raise KeyError(request_id)
        if r["status"] == "PENDING":
            raise AccessError("L'e-mail si prepara quando decidi la richiesta")
        row = conn.execute("UPDATE access_requests SET mail_sent_at=? WHERE id=? RETURNING *", (events.now_iso(), request_id)).fetchone()
    events.record("access.mail", f"E-mail a {r['email']} segnata come inviata", actor=actor, details={"request_id": request_id})
    return _row(row)


def status_of_user(user_id: int) -> Optional[str]:
    with connect() as conn:
        r = conn.execute("SELECT status FROM access_requests WHERE user_id=?", (user_id,)).fetchone()
    return r["status"] if r else None
