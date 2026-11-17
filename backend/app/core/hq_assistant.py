"""Chatbot interno del Quartier Generale: domande in italiano sui dati di QUANTO.

Come metodos: con la chiave di Claude (``ANTHROPIC_API_KEY``) la domanda diventa una richiesta strutturata per il datacenter; senza chiave
un riconoscitore a parole chiave copre le domande più comuni. In entrambi i casi:
- la richiesta passa dagli stessi controlli del datacenter (solo colonne del catalogo, sola lettura);
- la risposta mostra la richiesta usata, i dati e un grafico;
- la frase di risposta la scrive il codice dai numeri trovati: il modello non scrive mai cifre (regola di QUANTO).
"""
from __future__ import annotations

import json

import psycopg
import re
import unicodedata
from typing import Any, Dict, List, Optional

from app.core import datacenter, llm

SYSTEM = (
    "Sei il traduttore di domande del Quartier Generale di QUANTO. Ricevi il catalogo dei dati e una domanda in italiano. "
    "Rispondi SOLO con un oggetto JSON, senza testo attorno, con questi campi: "
    '{"dataset": id, "filters": [{"column": c, "op": "=|!=|>|<|>=|<=|contains|since_days", "value": v}], '
    '"group_by": colonna o null, "bucket": "day|week|month" o null (solo se group_by è una colonna data), '
    '"measure": "count|sum|avg|min|max" o null, "measure_column": colonna numerica o null, "columns": [colonne da mostrare], '
    '"order_by": colonna o null, "order": "asc|desc", "limit": numero, "title": breve titolo in italiano}. '
    "Usa solo dataset e colonne del catalogo. Per «negli ultimi N giorni» usa op since_days sulla colonna data. "
    'Se la domanda non si può rispondere con il catalogo, rispondi {"unsupported": "motivo breve in italiano"}.'
)


def _fold(t: str) -> str:
    return unicodedata.normalize("NFD", (t or "").lower()).encode("ascii", "ignore").decode()


def _days(q: str) -> Optional[int]:
    m = re.search(r"ultim[io]\s+(\d{1,4})\s+giorn", q)
    if m:
        return int(m.group(1))
    if "ultima settimana" in q or "questa settimana" in q:
        return 7
    if "ultimo mese" in q or "questo mese" in q:
        return 30
    if "oggi" in q:
        return 1
    return None


# parole -> (insieme, raggruppamento, periodo, titolo)
_RULES: List[tuple] = [
    (("richiest",), "access_requests", "status", None, "Richieste di accesso per stato"),
    (("iscritt", "newsletter"), "newsletter_subscribers", None, None, "Iscritti alla newsletter"),
    (("utent", "account", "livell"), "users", "role", None, "Utenti per livello"),
    (("visit", "visitator", "sito", "traffico"), "site_events", "ts", "day", "Visite al sito per giorno"),
    (("campagn",), "li_campaigns", "status", None, "Campagne LinkedIn per stato"),
    (("follower",), "li_followers", "day", "day", "Follower LinkedIn nel tempo"),
    (("post", "linkedin"), "li_posts", "status", None, "Post LinkedIn per stato"),
    (("token",), "token_ledger", "kind", None, "Movimenti dei token per tipo"),
    (("lavor", "client", "aziend"), "clients", "created_at", "month", "Lavori aperti per mese"),
    (("budget", "controll", "validaz", "esecuz"), "runs", "kind", None, "Esecuzioni salvate per tipo"),
    (("regol",), "rules", "status", None, "Regole dei bandi per stato"),
    (("requisit",), "requirements", "kind", None, "Requisiti per tipo"),
    (("bandi", "bando"), "bandi", None, None, "Bandi in memoria"),
    (("document", "file"), "documents", "kind", None, "Documenti lavorati per tipo"),
    (("event", "attivit", "operazion", "succes"), "events", "ts", "day", "Operazioni per giorno"),
]


def keyword_plan(question: str) -> Optional[Dict[str, Any]]:
    q = _fold(question)
    for words, ds, group, bucket, title in _RULES:
        if any(w in q for w in words):
            plan: Dict[str, Any] = {"dataset": ds, "measure": "count", "title": title, "limit": 60}
            if group:
                plan["group_by"] = group
                if bucket:
                    plan["bucket"] = bucket
            days = _days(q)
            date_col = datacenter.DATASETS[ds][2]
            if days and date_col:
                plan["filters"] = [{"column": date_col, "op": "since_days", "value": days}]
                plan["title"] += f", ultimi {days} giorni"
            if any(w in q for w in ("elenco", "lista", "mostra", "quali", "chi ")) and not bucket:
                plan = {"dataset": ds, "title": title.split(" per ")[0], "limit": 50, "filters": plan.get("filters", []),
                        "order_by": date_col, "order": "desc"} if date_col else {"dataset": ds, "title": title.split(" per ")[0], "limit": 50}
            return plan
    return None


def _llm_plan(client, question: str, cat: List[Dict[str, Any]]) -> Dict[str, Any]:
    compact = [{"id": d["id"], "nome": d["label"], "data": d["date_column"], "colonne": [f'{c["name"]}:{c["kind"]}' for c in d["columns"]]} for d in cat]
    raw = client.complete_json(SYSTEM, json.dumps({"catalogo": compact, "domanda": question}, ensure_ascii=False))
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m:
        raise llm.LLMError("Risposta non leggibile")
    return json.loads(m.group(0))


def _sentence(res: Dict[str, Any], title: str) -> str:
    rows = res["rows"]
    if not rows:
        return f"{title}: nessun dato trovato."
    if res["columns"] == ["valore"]:
        return f"{title}: {rows[0]['valore']}."
    if res["columns"] == ["gruppo", "valore"]:
        tot = sum(r["valore"] or 0 for r in rows)
        top = max(rows, key=lambda r: r["valore"] or 0)
        if res.get("chart") == "line":
            return f"{title}: {tot} in tutto su {len(rows)} periodi; il più alto è {top['gruppo']} con {top['valore']}."
        return f"{title}: {tot} in tutto; il gruppo più grande è «{top['gruppo']}» con {top['valore']}."
    return f"{title}: {len(rows)} righe."


def ask(question: str) -> Dict[str, Any]:
    question = (question or "").strip()[:500]
    if not question:
        return {"answer": "Scrivi una domanda.", "result": None, "engine": None}
    cat = datacenter.catalog()
    client = llm.get_client()
    engine, plan, note = "parole chiave", None, None
    if client is not None:
        try:
            plan = _llm_plan(client, question, cat)
            engine = "Claude"
        except Exception:                                                   # rete, quota, JSON: si ripiega sulle parole chiave
            note = "Claude non ha risposto: uso il riconoscitore a parole chiave."
            plan = None
    if plan and plan.get("unsupported"):
        return {"answer": f"Non posso rispondere con i dati che ho: {plan['unsupported']}", "result": None, "engine": engine, "plan": plan}
    if plan is None:
        plan = keyword_plan(question)
        if plan is None:
            return {"answer": "Non ho capito su quali dati cercare. Prova con parole come «richieste», «utenti», «visite al sito», «post», «campagne», «bandi» o «operazioni», "
                              "anche con un periodo («negli ultimi 30 giorni»).", "result": None, "engine": "parole chiave", "note": note}
    title = str(plan.pop("title", "") or datacenter.DATASETS.get(plan.get("dataset"), ("", "Risultato"))[1])[:120]
    try:
        res = datacenter.run(plan)
    except (datacenter.QueryError, ValueError, TypeError, psycopg.Error) as exc:
        return {"answer": f"La ricerca non è valida: {exc}", "result": None, "engine": engine, "plan": plan}
    return {"answer": _sentence(res, title), "title": title, "result": res, "engine": engine, "plan": plan, "note": note}
