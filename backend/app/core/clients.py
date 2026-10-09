"""Lo studio e i suoi lavori: ogni azienda con cui lo studio lavora su QUANTO è un «lavoro» (cliente) con il proprio profilo, i propri bilanci, documenti e risultati.

L'account è dello studio (i token valgono per lo studio); i dati d'impresa stanno sotto il singolo lavoro. Tecnicamente ogni lavoro è uno «spazio»:
i dati aziendali si leggono e si scrivono con la chiave ``<studio>#<id del lavoro>`` al posto della sola chiave dello studio, così profilo, bilanci,
documenti, modello di previsione e risultati di un cliente non si mescolano mai con quelli di un altro.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.core import events
from app.core.db import connect

MAX_STATE_BYTES = 2_000_000
STATE_KEYS = {"allocation", "budget", "confronto"}


class ClientError(ValueError):
    pass


def scope(owner: str, client_id: int) -> str:
    return f"{owner}#{client_id}"


def owns(owner: str, client_id: int) -> bool:
    with connect() as conn:
        return conn.execute("SELECT 1 FROM clients WHERE id=? AND owner=?", (client_id, owner)).fetchone() is not None


def get(owner: str, client_id: int) -> Optional[Dict[str, Any]]:
    with connect() as conn:
        r = conn.execute("SELECT * FROM clients WHERE id=? AND owner=?", (client_id, owner)).fetchone()
    return dict(r) if r else None


def _summary(owner: str, c: Dict[str, Any]) -> Dict[str, Any]:
    from app.core import company_profile as cp
    from app.core.fonte_c import service as fonte_c
    sc = scope(owner, c["id"])
    ov = cp.overview(sc)
    vals = {f["key"]: f["value"] for f in ov["fields"] if f["value"] is not None}
    with connect() as conn:
        saved = conn.execute("SELECT key, updated_at FROM client_state WHERE scope=? ORDER BY key", (sc,)).fetchall()
    return {"id": c["id"], "name": c["name"], "note": c["note"], "created_at": c["created_at"], "legal_name": vals.get("legal_name"), "ateco_code": vals.get("ateco_code"),
            "region": vals.get("region"), "size": (ov["size"] or {}).get("label"), "completeness_pct": ov["completeness_pct"], "last_year": ov["last_year"],
            "documents": len(fonte_c.list_documents(sc)), "saved": [{"key": s["key"], "updated_at": s["updated_at"]} for s in saved]}


def list_clients(owner: str) -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM clients WHERE owner=? AND archived=FALSE ORDER BY name, id", (owner,)).fetchall()
    return [_summary(owner, dict(r)) for r in rows]


def create_client(owner: str, name: str, note: str = "") -> Dict[str, Any]:
    name = (name or "").strip()
    if len(name) < 2:
        raise ClientError("Scrivi il nome dell'azienda (almeno 2 caratteri)")
    with connect() as conn:
        if conn.execute("SELECT 1 FROM clients WHERE owner=? AND archived=FALSE AND LOWER(name)=LOWER(?)", (owner, name)).fetchone():
            raise ClientError("Hai già un lavoro con questo nome")
        cid = conn.execute("INSERT INTO clients (owner, name, note, created_at) VALUES (?,?,?,?) RETURNING id", (owner, name[:200], (note or "")[:500], events.now_iso())).fetchone()["id"]
    events.record("client.create", f"Nuovo lavoro: {name[:60]}", actor=owner, details={"client_id": cid})
    return _summary(owner, get(owner, cid))  # type: ignore[arg-type]


def update_client(owner: str, client_id: int, name: Optional[str] = None, note: Optional[str] = None) -> Dict[str, Any]:
    c = get(owner, client_id)
    if c is None:
        raise KeyError(client_id)
    new_name = (name if name is not None else c["name"]).strip()
    if len(new_name) < 2:
        raise ClientError("Scrivi il nome dell'azienda (almeno 2 caratteri)")
    with connect() as conn:
        conn.execute("UPDATE clients SET name=?, note=? WHERE id=?", (new_name[:200], (note if note is not None else c["note"])[:500], client_id))
    return _summary(owner, get(owner, client_id))  # type: ignore[arg-type]


def delete_client(owner: str, client_id: int, confirm_name: str) -> Dict[str, int]:
    """Elimina il lavoro e tutto ciò che contiene (profilo, bilanci, documenti, modello di previsione, risultati). Chiede di riscrivere il nome."""
    from app.core.fonte_c import service as fonte_c
    c = get(owner, client_id)
    if c is None:
        raise KeyError(client_id)
    if (confirm_name or "").strip().lower() != c["name"].strip().lower():
        raise ClientError("Per eliminare il lavoro riscrivi il suo nome")
    sc = scope(owner, client_id)
    docs = [d["id"] for d in fonte_c.list_documents(sc)]
    for d in docs:
        fonte_c.delete(d, sc)
    counts = {"documents": len(docs)}
    with connect() as conn:
        for table in ("company_profiles", "company_financials", "forecast_templates"):
            counts[table] = conn.execute(f"DELETE FROM {table} WHERE owner=?", (sc,)).rowcount
        counts["state"] = conn.execute("DELETE FROM client_state WHERE scope=?", (sc,)).rowcount
        conn.execute("UPDATE budget_templates SET client_id=NULL WHERE client_id=? AND owner=?", (client_id, owner))   # i template restano: sono dati dello studio
        conn.execute("DELETE FROM clients WHERE id=?", (client_id,))
    events.record("client.delete", f"Lavoro eliminato: {c['name'][:60]}", actor=owner, details={"client_id": client_id, **counts})
    return counts


# ------------------------------------------------------------------------------------------------ risultati e scelte salvati per lavoro
def get_state(sc: str, key: str) -> Optional[Dict[str, Any]]:
    if key not in STATE_KEYS:
        raise ClientError("Chiave non valida")
    with connect() as conn:
        r = conn.execute("SELECT value, updated_at FROM client_state WHERE scope=? AND key=?", (sc, key)).fetchone()
    return {"value": json.loads(r["value"]), "updated_at": r["updated_at"]} if r else None


def put_state(sc: str, key: str, value: Any) -> Dict[str, Any]:
    if key not in STATE_KEYS:
        raise ClientError("Chiave non valida")
    raw = json.dumps(value, ensure_ascii=False)
    if len(raw.encode("utf-8")) > MAX_STATE_BYTES:
        raise ClientError("Dati troppo grandi da salvare")
    now = events.now_iso()
    with connect() as conn:
        conn.execute("INSERT INTO client_state (scope, key, value, updated_at) VALUES (?,?,?,?) ON CONFLICT (scope, key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                     (sc, key, raw, now))
    return {"updated_at": now}
