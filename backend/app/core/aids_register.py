"""Aiuti già ricevuti, impresa unica e verifica sul Registro Nazionale degli Aiuti (RNA).

Il de minimis (Reg. UE 2023/2831: 300.000 € per «impresa unica» in tre esercizi, contati dalla data di concessione) è il rischio che chiude la porta: un aiuto dimenticato, o ricevuto da
un'impresa collegata, e la domanda sfora il tetto. QUANTO non può leggere l'RNA da solo (richiede l'accesso dell'impresa o di un delegato): qui si organizza la verifica perché sia **fatta e
documentata**, non presunta.

Il flusso
1. **Impresa unica**: quattro domande (le relazioni dell'art. 2, par. 2, del regolamento) e l'elenco delle imprese collegate con codice fiscale. Una risposta «non so» non è una risposta: il
   flusso resta incompleto.
2. **Visura aiuti**: per ogni impresa del gruppo (la propria e le collegate) si indica la data in cui si è consultata la visura ufficiale dell'RNA e se ne riportano le concessioni (data, ente,
   misura, regime, importo, codice COR).
3. **Confronto** con ciò che QUANTO sa già (registro degli aiuti caricato, bilanci): ogni differenza è scritta.
4. **Residuo** del triennio sulla data di concessione di ogni aiuto, sommando tutte le imprese del gruppo; se la verifica non è completa e recente (30 giorni) il residuo che si usa nel piano è
   ridotto di un margine di sicurezza (10% del tetto) e lo stato dice «non verificato».
5. **Conferma**: chi ha fatto la verifica la attesta (nome, data); resta nel registro firmato.

Niente viene presunto: finché manca la verifica, il piano che usa il de minimis non è definitivo.
"""
from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core import clients, events

STATE_KEY = "aids-register"
PLAFOND_EUR = 300_000.0
FRESH_DAYS = 30
SAFETY_MARGIN = 0.10
QUESTIONS = {
    "a": "Un'impresa detiene la maggioranza dei diritti di voto degli azionisti o soci di un'altra impresa.",
    "b": "Un'impresa ha il diritto di nominare o revocare la maggioranza dei membri dell'organo di amministrazione, direzione o controllo di un'altra impresa.",
    "c": "Un'impresa ha il diritto di esercitare un'influenza dominante su un'altra in virtù di un contratto o di una clausola dello statuto.",
    "d": "Un'impresa azionista o socia controlla da sola, in base a un accordo con altri soci, la maggioranza dei diritti di voto di un'altra impresa.",
    "e": "Le relazioni a)-d) esistono tra imprese legate fra loro per il tramite di una o più altre imprese (o di una stessa persona fisica).",
}
ANSWERS = ("si", "no", "non_so")


class AidsError(ValueError):
    pass


def _empty() -> Dict[str, Any]:
    return {"group": {"answers": {}, "companies": [], "completed_at": None}, "checks": {}, "entries": [], "confirmations": []}


def load(owner: str) -> Dict[str, Any]:
    st = clients.get_state(owner, STATE_KEY)
    base = _empty()
    if st and isinstance(st.get("value"), dict):
        base.update({k: v for k, v in st["value"].items() if k in base})
    return base


MAX_COMPANIES = 30
MAX_ENTRIES = 300                                           # concessioni per impresa e fonte: una visura ne ha poche decine


def _save(owner: str, reg: Dict[str, Any]) -> None:
    try:
        clients.put_state(owner, STATE_KEY, reg)
    except clients.ClientError as exc:
        raise AidsError(str(exc)) from exc


def _iso(v: Any, what: str) -> str:
    try:
        return date.fromisoformat(str(v)[:10]).isoformat()
    except ValueError:
        raise AidsError(f"{what}: data non valida (AAAA-MM-GG)") from None


def _cf(v: str) -> str:
    c = re.sub(r"\s+", "", str(v or "")).upper()
    if not re.fullmatch(r"\d{11}|[A-Z0-9]{16}", c):
        raise AidsError("Codice fiscale o partita IVA non valido (11 cifre o 16 caratteri)")
    return c


def save_group(owner: str, answers: Dict[str, str], companies: List[Dict[str, Any]], actor: str) -> Dict[str, Any]:
    clean = {}
    for k, v in (answers or {}).items():
        if k not in QUESTIONS:
            raise AidsError(f"Domanda sconosciuta: {k}")
        if v not in ANSWERS:
            raise AidsError("Le risposte possibili sono sì, no, non so")
        clean[k] = v
    if len(companies or []) > MAX_COMPANIES:
        raise AidsError(f"Al massimo {MAX_COMPANIES} imprese collegate")
    comps, seen = [], set()
    for c in companies or []:
        cf = _cf(c.get("cf"))
        if cf in seen:
            continue
        seen.add(cf)
        comps.append({"cf": cf, "name": str(c.get("name") or "")[:120], "relation": str(c.get("relation") or "")[:200]})
    reg = load(owner)
    done = all(clean.get(k) in ("si", "no") for k in QUESTIONS)
    if done and any(v == "si" for v in clean.values()) and not comps:
        raise AidsError("Hai indicato un legame con altre imprese: elenca le imprese collegate con il loro codice fiscale")
    reg["group"] = {"answers": clean, "companies": comps, "completed_at": datetime.utcnow().date().isoformat() if done else None}
    _save(owner, reg)
    events.record("aids.group", f"Impresa unica: {'completata' if done else 'incompleta'}, {len(comps)} imprese collegate", actor=actor)
    return status(owner)


def save_entries(owner: str, company: str, source: str, entries: List[Dict[str, Any]], checked_at: Optional[str], actor: str) -> Dict[str, Any]:
    """Sostituisce le concessioni di (impresa, fonte). Per la fonte RNA serve la data in cui si è consultata la visura ufficiale."""
    if source not in ("RNA", "MANUALE"):
        raise AidsError("La fonte è RNA (visura ufficiale) o MANUALE")
    comp = "SELF" if company == "SELF" else _cf(company)
    if source == "RNA":
        if not checked_at:
            raise AidsError("Indica la data in cui hai consultato la visura aiuti dell'RNA")
        when = _iso(checked_at, "Data della visura")
        if date.fromisoformat(when) > date.today():
            raise AidsError("La data della visura non può essere futura")
    if len(entries or []) > MAX_ENTRIES:
        raise AidsError(f"Al massimo {MAX_ENTRIES} concessioni per volta")
    rows: List[Dict[str, Any]] = []
    for e in entries or []:
        try:
            amount = float(e.get("amount_eur"))
        except (TypeError, ValueError):
            raise AidsError("Importo non valido") from None
        if amount <= 0:
            raise AidsError("L'importo di un aiuto è maggiore di zero")
        rows.append({"id": uuid.uuid4().hex[:10], "company": comp, "source": source, "granted": _iso(e.get("granted"), "Data di concessione"), "entity": str(e.get("entity") or "")[:160],
                     "measure": str(e.get("measure") or "")[:200], "regime": "de minimis" if str(e.get("regime", "de minimis")).lower().startswith("de minimis") else "altro",
                     "amount_eur": round(amount, 2), "cor": (str(e.get("cor") or "")[:40] or None)})
    reg = load(owner)
    reg["entries"] = [x for x in reg["entries"] if not (x["company"] == comp and x["source"] == source)] + rows
    if source == "RNA":
        reg["checks"][comp] = {"checked_at": when, "by": actor}
    _save(owner, reg)
    events.record("aids.entries", f"Aiuti {source} di {comp}: {len(rows)} righe", actor=actor)
    return status(owner)


def confirm(owner: str, actor: str, note: str = "") -> Dict[str, Any]:
    st = status(owner)
    reg = load(owner)
    reg["confirmations"] = (reg.get("confirmations") or [])[-19:] + [{"by": actor, "at": datetime.utcnow().isoformat(timespec="seconds"), "status": st["status"], "residual_eur": st["residual_eur"],
                                                                      "note": note[:300]}]
    _save(owner, reg)
    events.record("aids.confirm", f"Verifica de minimis confermata ({st['status']}, residuo {st['residual_eur']:,.2f} €)", actor=actor)
    return status(owner)


def _declared(owner: str, company_self: str = "SELF") -> List[Dict[str, Any]]:
    """Gli aiuti de minimis che l'azienda ha già dichiarato nei documenti: registro degli aiuti in Excel e dichiarazioni sostitutive firmate."""
    from app.core import company_facts
    out: List[Dict[str, Any]] = []
    for a in company_facts.aids(owner):
        if str(a.get("regime", "")).lower().startswith("de minimis"):
            out.append({"id": a.get("cor") or a["granted"], "company": company_self, "source": "FOGLIO", "granted": a["granted"], "entity": a.get("entity"), "measure": a.get("measure"),
                        "regime": "de minimis", "amount_eur": float(a["amount_eur"]), "cor": a.get("cor")})
    for d in company_facts.facts(owner)["de_minimis_declared"]:
        for a in d["aids"]:
            e = {"id": a.get("cor") or a["granted"], "company": company_self, "source": "DICHIARAZIONE", "granted": a["granted"], "entity": "", "measure": a.get("measure"), "regime": "de minimis",
                 "amount_eur": float(a["amount_eur"]), "cor": a.get("cor")}
            if not any(_same(e, x) for x in out):
                out.append(e)
    return out


def _visure(owner: str, reg: Dict[str, Any]) -> Dict[str, Any]:
    """Le visure aiuti caricate come documenti: valgono come la visura consultata, per l'impresa a cui appartengono (la propria o una collegata)."""
    from app.core import company_facts, company_profile as cp
    try:
        mine = company_facts._vat_digits(cp.profile_values(owner).get("vat_number"))
    except Exception:
        mine = ""
    related = {company_facts._vat_digits(c["cf"]): c["cf"] for c in reg["group"]["companies"]}
    checks: Dict[str, Dict[str, Any]] = {}
    entries: List[Dict[str, Any]] = []
    for v in company_facts.rna_visure(owner):
        cf = company_facts._vat_digits(v["cf"])
        comp = "SELF" if cf and cf == mine else related.get(cf)
        if comp is None:
            continue
        if comp not in checks or v["checked_at"] > checks[comp]["checked_at"]:
            checks[comp] = {"checked_at": v["checked_at"], "by": "documento caricato", "document": v["document"]["filename"]}
        for a in v["entries"]:
            entries.append({"id": a.get("cor") or a["granted"], "company": comp, "source": "RNA", "granted": a["granted"], "entity": "", "measure": a.get("measure"), "regime": a["regime"],
                            "amount_eur": float(a["amount_eur"]), "cor": a.get("cor")})
    return {"checks": checks, "entries": entries}


def _same(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    if a.get("cor") and a.get("cor") == b.get("cor"):
        return True
    return a["granted"] == b["granted"] and abs(a["amount_eur"] - b["amount_eur"]) < 0.5


def status(owner: str, on: Optional[date] = None) -> Dict[str, Any]:
    today = date.today()
    on = on or today
    reg = load(owner)
    group = reg["group"]
    comps = [{"cf": "SELF", "name": "L'azienda", "relation": ""}] + group["companies"]
    answered = all(group["answers"].get(k) in ("si", "no") for k in QUESTIONS)
    unsure = [k for k in QUESTIONS if group["answers"].get(k) == "non_so"]
    declared = _declared(owner)
    doc = _visure(owner, reg)
    checks = dict(reg["checks"])
    for comp, c in doc["checks"].items():                       # vale la visura più recente, caricata o inserita
        if comp not in checks or c["checked_at"] >= checks[comp]["checked_at"]:
            checks[comp] = c
    rna = [e for e in reg["entries"] if e["source"] == "RNA"]
    for e in doc["entries"]:
        if not any(_same(e, x) and x["company"] == e["company"] for x in rna):
            rna.append(e)
    manual = [e for e in reg["entries"] if e["source"] == "MANUALE"]
    window_start = date(on.year - 3, on.month, min(on.day, 28)) if not (on.month == 2 and on.day == 29) else date(on.year - 3, 2, 28)

    def in_window(e: Dict[str, Any]) -> bool:
        return window_start < date.fromisoformat(e["granted"]) <= on

    # confronto: ciò che è dichiarato nei documenti contro la visura
    diff: List[str] = []
    checked_self = "SELF" in checks
    if checked_self:
        rna_self = [e for e in rna if e["company"] == "SELF" and e["regime"] == "de minimis"]            # i documenti dichiarano solo il de minimis: gli altri aiuti della visura non sono una differenza
        for d in declared:
            if not any(_same(d, r) for r in rna_self):
                diff.append(f"Dichiarato nei documenti ma non nella visura: {d['granted']} · {d.get('measure') or d.get('entity')} · {d['amount_eur']:,.2f} €".replace(",", "§").replace(".", ",").replace("§", "."))
        for r in rna_self:
            if declared and not any(_same(d, r) for d in declared):
                diff.append(f"Nella visura ma non nei documenti: {r['granted']} · {r.get('measure') or r.get('entity')} · {r['amount_eur']:,.2f} €".replace(",", "§").replace(".", ",").replace("§", "."))
    # l'insieme che conta, prudente: unione di visura, documenti e inserimenti a mano (un aiuto presente in due fonti vale una volta)
    counted: List[Dict[str, Any]] = []
    for e in rna + declared + manual:
        if e["regime"] != "de minimis" or not in_window(e):
            continue
        if not any(_same(e, c) and (c["company"] == e["company"]) for c in counted):
            counted.append(e)
    received = round(sum(e["amount_eur"] for e in counted), 2)
    residual = round(max(0.0, PLAFOND_EUR - received), 2)

    missing_checks = [c for c in comps if c["cf"] not in checks]
    stale = [c for c in comps if c["cf"] in checks and (today - date.fromisoformat(checks[c["cf"]]["checked_at"])).days > FRESH_DAYS]
    problems: List[str] = []
    if not answered:
        problems.append("L'impresa unica non è completata" + (f" (risposte «non so»: {', '.join(unsure)})" if unsure else "") + ": non si sa se ci sono imprese collegate.")
    if missing_checks:
        problems.append("Manca la visura aiuti dell'RNA per: " + ", ".join("la tua azienda" if c["cf"] == "SELF" else (c["name"] or c["cf"]) for c in missing_checks) + ".")
    if stale:
        problems.append(f"La visura ha più di {FRESH_DAYS} giorni per: " + ", ".join("la tua azienda" if c["cf"] == "SELF" else (c["name"] or c["cf"]) for c in stale) + ": rifalla.")
    if diff:
        problems.append(f"{len(diff)} differenze tra la visura e i documenti: vanno spiegate.")
    if not checked_self and not rna and not declared:
        state = "NON_VERIFICATO"
    elif problems and diff and not missing_checks and not stale and answered:
        state = "DISCORDANZA"
    elif problems:
        state = "NON_VERIFICATO" if (missing_checks or not answered) else "SCADUTO"
    else:
        state = "VERIFICATO"
    usable = residual if state == "VERIFICATO" else round(max(0.0, residual - PLAFOND_EUR * SAFETY_MARGIN), 2)
    from app.core import company_facts
    alone = [d for d in company_facts.facts(owner)["de_minimis_declared"] if d.get("unique_enterprise_alone")]
    suggested = ({k: "no" for k in QUESTIONS} if alone and not answered else None)          # la dichiarazione firmata dice che l'impresa non è collegata: è un suggerimento, la risposta resta di chi verifica
    return {"state_key": STATE_KEY, "status": state, "on": on.isoformat(), "window": [window_start.isoformat(), on.isoformat()], "plafond_eur": PLAFOND_EUR, "received_eur": received, "residual_eur": residual,
            "usable_residual_eur": usable, "safety_margin_eur": round(residual - usable, 2), "problems": problems, "differences": diff, "group": group, "questions": QUESTIONS, "companies": comps,
            "checks": checks, "entries": rna + manual, "declared_in_documents": declared, "suggested_answers": suggested, "counted": counted, "confirmations": reg["confirmations"][-5:],
            "message": ("Verificato sul registro ufficiale: il residuo è quello della visura." if state == "VERIFICATO" else
                        "Non verificato: il piano usa il residuo ridotto del margine di sicurezza e non è definitivo finché la verifica non è completa.")}
