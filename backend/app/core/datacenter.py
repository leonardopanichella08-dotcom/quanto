"""Datacenter del Quartier Generale: ogni tabella utile è un «insieme di dati» con le sue colonne, interrogabile in sola lettura.

Perché così: il titolare (e il chatbot interno) deve poter chiedere qualunque cosa ai dati di QUANTO senza scrivere SQL e senza poter
rompere nulla. Una richiesta è un piccolo oggetto (insieme, filtri, raggruppamento, misura); il codice la controlla colonna per colonna
contro il catalogo e costruisce la query con nomi verificati e valori come parametri. Non si leggono mai password, token, chiavi,
testi integrali o file: quelle colonne non entrano nel catalogo, qualunque cosa chieda la richiesta.
"""
from __future__ import annotations

import csv
import io
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.core.db import connect

# insieme -> (gruppo, nome, colonna data principale, descrizione)
DATASETS: Dict[str, tuple] = {
    "users": ("Persone", "Utenti", "created_at", "Chi ha un account: livello, studio, quando è entrato l'ultima volta."),
    "access_requests": ("Persone", "Richieste di accesso", "requested_at", "Chi ha chiesto di entrare, con stato, livello e invio dell'e-mail."),
    "newsletter_subscribers": ("Persone", "Iscritti alla newsletter", "consent_at", "Indirizzo e momento del consenso."),
    "clients": ("Lavoro degli studi", "Lavori (aziende clienti)", "created_at", "Le aziende clienti aperte dagli studi."),
    "runs": ("Lavoro degli studi", "Esecuzioni salvate", "ts", "Controlli dei budget e allocazioni eseguiti."),
    "token_ledger": ("Lavoro degli studi", "Movimenti dei token", "ts", "Token accreditati e usati, per utente."),
    "events": ("Lavoro degli studi", "Cronologia delle operazioni", "ts", "Ogni operazione fatta nel sistema, con esito e durata."),
    "documents": ("Lavoro degli studi", "Documenti lavorati", "ts", "File caricati, importati ed esportati."),
    "bandi": ("Bandi e regole", "Bandi in memoria", None, "I bandi studiati con le loro regole."),
    "rules": ("Bandi e regole", "Regole dei bandi", None, "Le regole numeriche lette dai testi ufficiali."),
    "requirements": ("Bandi e regole", "Requisiti dei bandi", None, "Obblighi e requisiti estratti dai bandi."),
    "li_posts": ("Marketing", "Post LinkedIn", "created_at", "Post scritti, approvati, programmati e pubblicati."),
    "li_post_metrics": ("Marketing", "Statistiche dei post", "ts", "Impressioni, reazioni, commenti e clic dei post nel tempo."),
    "li_campaigns": ("Marketing", "Campagne LinkedIn", "created_at", "Campagne con obiettivo, budget e date."),
    "li_campaign_metrics": ("Marketing", "Statistiche delle campagne", "day", "Impressioni, clic, spesa e contatti giorno per giorno."),
    "li_followers": ("Marketing", "Follower LinkedIn", "day", "Follower di profilo e pagina nel tempo."),
    "site_events": ("Marketing", "Visite al sito", "ts", "Pagine viste e clic sul sito pubblico (sessione anonima)."),
}
# colonne mai esposte, in qualunque tabella
_HIDDEN = re.compile(r"(password|token|secret|hash|_enc$|^data$|^text$|request_json|response_json|^meta$|payload|mail_body|^note$|^notes$|figures)", re.I)
_DATE_HINT = re.compile(r"(_at$|^ts$|^day$|_day$|^date$)")
OPS = {"=": "=", "!=": "<>", ">": ">", "<": "<", ">=": ">=", "<=": "<=", "contains": "ILIKE", "since_days": ">="}
MEASURES = ("count", "sum", "avg", "min", "max")
BUCKETS = ("day", "week", "month")
MAX_ROWS = 500


class QueryError(ValueError):
    pass


def _columns(conn, table: str) -> List[Dict[str, str]]:
    rows = conn.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema=current_schema() AND table_name=? ORDER BY ordinal_position",
                        (table,)).fetchall()
    out = []
    for r in rows:
        if _HIDDEN.search(r["column_name"]):
            continue
        kind = "number" if r["data_type"] in ("integer", "bigint", "numeric", "double precision", "real", "smallint") else \
               "boolean" if r["data_type"] == "boolean" else "date" if _DATE_HINT.search(r["column_name"]) else "text"
        out.append({"name": r["column_name"], "kind": kind})
    return out


def catalog() -> List[Dict[str, Any]]:
    """Gli insiemi di dati presenti, con colonne visibili e numero di righe."""
    out = []
    with connect() as conn:
        for key, (group, label, date_col, help_) in DATASETS.items():
            cols = _columns(conn, key)
            if not cols:
                continue
            n = conn.execute(f'SELECT COUNT(*) n FROM "{key}"').fetchone()["n"]
            out.append({"id": key, "group": group, "label": label, "date_column": date_col, "help": help_, "rows": n, "columns": cols})
    return out


def _plain(v: Any) -> Any:
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, (bytes, memoryview)):
        return None
    return v


def _date_expr(col: str) -> str:
    return f'("{col}")::timestamptz'


def build(req: Dict[str, Any], cols: Dict[str, Dict[str, str]]) -> tuple:
    """Costruisce la query controllata. Restituisce (sql, parametri, colonne del risultato)."""
    table = req.get("dataset")
    if table not in DATASETS:
        raise QueryError("Insieme di dati sconosciuto")

    def col(name: Optional[str]) -> str:
        if not name or name not in cols:
            raise QueryError(f"Colonna non disponibile: {name}")
        return name

    where, params = [], []
    for f in req.get("filters") or []:
        c, op, v = col(f.get("column")), f.get("op", "="), f.get("value")
        if op not in OPS:
            raise QueryError(f"Condizione non ammessa: {op}")
        if op == "contains":
            where.append(f'CAST("{c}" AS TEXT) ILIKE ?'); params.append(f"%{str(v)[:100]}%")
        elif op == "since_days":
            days = int(v)
            if not 0 < days <= 3650:
                raise QueryError("Il periodo va da 1 a 3650 giorni")
            where.append(f"{_date_expr(c)} >= now() - (? || ' days')::interval"); params.append(str(days))
        else:
            where.append(f'"{c}" {OPS[op]} ?'); params.append(v)
    measure = req.get("measure") or ("count" if req.get("group_by") else None)
    group = req.get("group_by")
    bucket = req.get("bucket")
    limit = max(1, min(int(req.get("limit") or 100), MAX_ROWS))
    sql_where = f" WHERE {' AND '.join(where)}" if where else ""
    if measure:
        if measure not in MEASURES:
            raise QueryError("Misura non ammessa")
        target = req.get("measure_column")
        if measure == "count":
            agg = "COUNT(*)"
        else:
            t = col(target)
            if cols[t]["kind"] != "number":
                raise QueryError("Somma e media si fanno solo su colonne di numeri")
            agg = f'{measure.upper()}("{t}")'
        if group:
            g = col(group)
            if bucket:
                if bucket not in BUCKETS:
                    raise QueryError("Raggruppamento per periodo non ammesso")
                fmt = {"day": "YYYY-MM-DD", "week": "IYYY-\"W\"IW", "month": "YYYY-MM"}[bucket]
                key = f"to_char({_date_expr(g)}, '{fmt}')"
                order = "1"
            else:
                key = f'"{g}"'
                order = "2 DESC"
            sql = f"SELECT {key} AS gruppo, {agg} AS valore FROM \"{table}\"{sql_where} GROUP BY 1 ORDER BY {order} LIMIT {limit}"
            return sql, params, ["gruppo", "valore"]
        return f'SELECT {agg} AS valore FROM "{table}"{sql_where}', params, ["valore"]
    show = [col(c) for c in (req.get("columns") or [])] or list(cols)[:8]
    order_col = req.get("order_by")
    order = f' ORDER BY "{col(order_col)}" {"ASC" if req.get("order") == "asc" else "DESC"}' if order_col else ""
    sel = ", ".join(f'"{c}"' for c in show)
    return f'SELECT {sel} FROM "{table}"{sql_where}{order} LIMIT {limit}', params, show


def run(req: Dict[str, Any]) -> Dict[str, Any]:
    """Esegue una richiesta controllata in sola lettura."""
    table = req.get("dataset")
    if table not in DATASETS:
        raise QueryError("Insieme di dati sconosciuto")
    with connect() as conn:
        cols = {c["name"]: c for c in _columns(conn, table)}
        if not cols:
            raise QueryError("Insieme di dati non disponibile")
    sql, params, out_cols = build(req, cols)
    with connect() as conn:
        conn.execute("SET TRANSACTION READ ONLY")                       # primo comando della transazione: niente scritture possibili
        rows = conn.execute(sql, tuple(params)).fetchall()
    data = [{k: _plain(r[k]) for k in out_cols} for r in rows]
    chart = None
    if out_cols == ["gruppo", "valore"]:
        chart = "line" if req.get("bucket") else "bar"
    return {"dataset": table, "label": DATASETS[table][1], "columns": out_cols, "rows": data, "chart": chart, "request": req}


def to_csv(result: Dict[str, Any]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(result["columns"])
    for r in result["rows"]:
        w.writerow([r.get(c, "") for c in result["columns"]])
    return buf.getvalue()
