"""Idee di progetto per l'azienda, costruite sui suoi documenti.

Un bando finanzia un progetto, e un buon progetto nasce da ciò che all'azienda serve davvero: beni da rinnovare, investimenti già in programma, assunzioni previste, formazione,
presenza sui mercati. Qui si propongono idee a partire da ciò che i documenti dicono, ognuna con:
- **le spese che la compongono**, con importo, fonte e natura: *nuova* (un acquisto o un'assunzione che il progetto causa: è ciò che un bando finanzia) oppure *ordinaria* (una spesa che l'azienda
  sostiene comunque: entra in un progetto solo se il bando la ammette per quel progetto, per esempio spese generali a forfait o personale realmente dedicato con timesheet, e solo per la parte dedicata);
- **cosa manca** per trasformarla in un budget presentabile (un preventivo, la RAL di chi si assume, la diagnosi energetica);
- **i bandi che finanziano quel tipo di progetto**, dalle frasi dei loro testi.

Regole che non si cambiano:
- le idee sono **ipotesi** da validare con l'imprenditore, non progetti decisi;
- un importo che non si ricava da un documento non si inventa: la riga resta «da quantificare» e dice con cosa (un preventivo);
- le spese ordinarie non si trasformano in spese di progetto: restano separate e dichiarate tali.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core import bandi, budget_basis, company_facts, expense_types, funding_modes, project_types

NEW, ORDINARY, TO_QUANTIFY = "NUOVA", "ORDINARIA", "DA_QUANTIFICARE"
_PHYSICAL = ("ATTREZZ", "MACCHIN", "ELETTRONIC", "ARREDI", "MOBILI", "IMPIANT", "HARDWARE", "AUTOMEZZ", "COMPUTER")


def _line(label: str, category: str, code: Optional[str], amount: Optional[float], nature: str, detail: str, sources: List[Any]) -> Dict[str, Any]:
    return {"label": label, "category": category, "expense_type": code, "amount_eur": None if amount is None else round(amount, 2), "nature": nature, "detail": detail, "sources": sources}


def _idea(key: str, title: str, types: List[str], why: List[str], lines: List[Dict[str, Any]], missing: List[str], cautions: Optional[List[str]] = None) -> Dict[str, Any]:
    return {"id": key, "title": title, "project_types": types, "project_type_labels": [project_types.label(t) for t in types], "why": why, "lines": lines, "missing": missing, "cautions": cautions or [],
            "new_eur": round(sum(ln["amount_eur"] or 0 for ln in lines if ln["nature"] == NEW), 2), "ordinary_eur": round(sum(ln["amount_eur"] or 0 for ln in lines if ln["nature"] == ORDINARY), 2),
            "to_quantify": [ln["label"] for ln in lines if ln["nature"] == TO_QUANTIFY]}


def _src(f: Dict[str, Any]) -> List[Dict[str, Any]]:
    d = f.get("_doc") or {}
    return [{"document_id": d.get("id"), "filename": d.get("filename"), "where": d.get("where")}]


def _bando_types() -> Dict[str, Dict[str, Any]]:
    """Le tipologie di progetto di ogni bando studiato (una lettura sola per chiamata)."""
    out: Dict[str, Dict[str, Any]] = {}
    for b in bandi.list_bandi():
        if not (b["curated"] or b["rules_count"] or b["requirements_count"]):
            continue
        d = bandi.get_bando_detail(b["bando_id"])
        if d:
            out[b["bando_id"]] = {"name": d["name"], "issuer": d.get("issuer"), "status": d.get("status"), "types": {t["code"]: t for t in d["project_types"]},
                                  "mode": funding_modes.describe((d.get("funding_modes") or {}).get("primary"))}
    return out


def generate(owner: str, year: Optional[int] = None) -> Dict[str, Any]:
    from app.core import company_profile as cp
    fin = cp._load_financials(owner)
    years = [y for y in sorted(fin) if any(fin[y][0].get(cp.FIN_KEY[c]) is not None for c in cp.CATEGORIES)]
    if not years:
        raise cp.ProfileError("Mancano i dati di bilancio: carica un bilancio nel profilo o inserisci i costi dell'ultimo esercizio")
    year = year or years[-1] + 1
    plan = budget_basis.plan_for_year(owner, year)
    f = company_facts.facts(owner)
    staff = company_facts.staff(owner)
    assets = company_facts.assets(owner)
    ideas: List[Dict[str, Any]] = []
    notes: List[str] = []

    # 1. gli investimenti già nel piano dell'azienda
    capex = [c for c in f["capex_plan"] if c["year"] == year]
    themes = {"RICERCA_SVILUPPO": ("Sviluppo e innovazione di prodotto", ["CAP_IMMATERIALI"]), "DIGITALIZZAZIONE": ("Infrastruttura digitale e software", ["CAP_CLOUD", "CAP_SOFTWARE"]),
              "INVESTIMENTI_PRODUTTIVI": ("Dotazioni, attrezzature e arredi", ["CAP_HARDWARE", "CAP_ATTREZZ", "CAP_ARREDI", "CAP_IMPIANTI", "CAP_AUTOMEZZI", "CAP_ALTRO"])}
    for ptype, (title, codes) in themes.items():
        rows = [c for c in capex if c["expense_type"] in codes]
        if not rows:
            continue
        types = [ptype] + (["DIGITALIZZAZIONE"] if ptype == "INVESTIMENTI_PRODUTTIVI" and any(c["expense_type"] == "CAP_HARDWARE" for c in rows) else [])
        lines = [_line(r["description"], "CAPITAL_ASSETS", r["expense_type"], r["amount_eur"], NEW, f"Previsto nel piano degli investimenti {year}", _src(r)) for r in rows]
        cautions = []
        rd = f.get("rd_credit") or []
        if ptype == "RICERCA_SVILUPPO" and rd:
            cautions.append(f"L'azienda ha già un credito d'imposta ricerca e sviluppo ({rd[0]['year']}: {rd[0]['credit_eur']:,.2f} €): sulle stesse spese un contributo non è cumulabile liberamente, va verificato.".replace(",", "§").replace(".", ",").replace("§", "."))
        ideas.append(_idea(f"piano-{ptype.lower()}", title, types, [f"È già nel piano degli investimenti {year} dell'azienda: il bando può finanziarne una parte se il progetto parte dopo la domanda."], lines,
                           ["Un preventivo per ogni acquisto (il piano ha un importo, non un fornitore)", "La data di avvio prevista: un acquisto già fatto prima della domanda non è finanziabile"], cautions))

    # 2. i beni a fine vita: da rinnovare (il costo di sostituzione non si conosce: si parte dal costo storico, dichiarato)
    old = [a for a in assets["assets"] if a["cost_eur"] and a["net_eur"] <= 0.1 * a["cost_eur"] and any(k in parsers_norm(a["class"]) for k in _PHYSICAL)]
    if old:
        by_class: Dict[str, List[Dict[str, Any]]] = {}
        for a in old:
            by_class.setdefault(a["class"], []).append(a)
        lines = [_line(f"Rinnovo: {cls} ({len(v)} beni)", "CAPITAL_ASSETS", v[0].get("expense_type") or expense_types.GENERIC["CAPITAL_ASSETS"], sum(a["cost_eur"] for a in v), NEW,
                       "Costo storico dei beni quasi o del tutto ammortizzati: è una stima, il prezzo di oggi si conosce solo con un preventivo", _src(v[0])) for cls, v in by_class.items()]
        ideas.append(_idea("rinnovo-beni", "Rinnovo dei beni a fine vita", ["INVESTIMENTI_PRODUTTIVI", "DIGITALIZZAZIONE"],
                           [f"{len(old)} beni del libro cespiti sono ammortizzati per oltre il 90% del costo storico: sono candidati al rinnovo."], lines,
                           ["Quali beni si rinnovano davvero, con un preventivo per ognuno", "L'importo di oggi: quello indicato è il costo storico"]))

    # 3. le assunzioni previste
    hires = [h for h in staff["hiring_plan"] if h["start"][:4] in (str(year), str(year + 1))]
    if hires:
        lines = [_line(f"{h['role']} ({h['position']}), ingresso {h['start']}", "PERSONNEL", "PERS_STIPENDI", h["annual_cost_eur"], NEW, "Costo azienda annuo dal piano delle assunzioni", [{"filename": "Piano delle assunzioni"}]) for h in hires]
        ideas.append(_idea("assunzioni", "Nuove assunzioni previste", ["OCCUPAZIONE"] + (["FORMAZIONE"] if len(hires) > 1 else []),
                           [f"Il piano delle assunzioni prevede {len(hires)} {'ingresso' if len(hires) == 1 else 'ingressi'} tra il {year} e il {year + 1}: i bandi per l'occupazione finanziano proprio assunzioni nuove."], lines,
                           ["RAL, livello e tipo di contratto di ogni persona (il controllo vuole persona per persona)", "La data di assunzione: se precede la domanda o il periodo del bando, non è finanziabile"]))

    # 4-5-7. le spese che l'azienda sostiene già (ORDINARIE): si mostrano come tali
    by_code = {}
    for r in plan["types"]:
        by_code.setdefault(r["code"], []).append(r)

    def ordinary(codes: List[str], label_prefix: str) -> List[Dict[str, Any]]:
        out = []
        for c in codes:
            for r in by_code.get(c, []):
                out.append(_line(r["label"], r["category"], r["code"], r["amount_eur"], ORDINARY, f"{label_prefix}: {r['detail']}", r["sources"]))
        return out

    train = ordinary(["TRN_CORSI", "TRN_SEMINARI", "TRN_AGGIORN"], "L'azienda spende già")
    if train:
        ideas.append(_idea("formazione", "Piano di formazione", ["FORMAZIONE"], ["L'azienda sostiene già costi di formazione: un piano organico può essere finanziato da bandi e fondi interprofessionali."], train,
                           ["Il piano formativo: corsi, ore, partecipanti, ente formatore (un preventivo per corso)", "Quali di queste spese sarebbero comunque sostenute: restano ordinarie e non finanziabili come tali"]))
    promo = ordinary(["OH_PUBBLICITA"], "L'azienda spende già")
    if promo:
        ideas.append(_idea("promozione", "Promozione e presenza su nuovi mercati", ["INTERNAZIONALIZZAZIONE", "MARKETING"], ["L'azienda sostiene già spese di promozione e fiere: un progetto di export ha una parte finanziabile se i mercati sono nuovi."], promo,
                           ["Quali mercati esteri e quali fiere, con un preventivo", "Le spese ordinarie di pubblicità non sono finanziabili come tali: contano solo quelle del nuovo progetto"]))
    cert = ordinary(["CONS_CERTIF"], "L'azienda spende già")
    ideas.append(_idea("certificazioni", "Certificazioni (qualità, sicurezza delle informazioni)", ["CERTIFICAZIONI"], ["Le certificazioni sono finanziate da diversi bandi e danno vantaggi nelle gare."], cert or
                       [_line("Certificazione da definire", "CONSULTING", "CONS_CERTIF", None, TO_QUANTIFY, "Nei documenti non c'è una spesa per certificazioni", [])],
                       ["Quale certificazione serve ai clienti dell'azienda e il preventivo dell'ente certificatore"]))

    # 6. l'efficientamento: l'importo non si ricava dai documenti
    energy = sum(r["amount_eur"] for r in by_code.get("OH_ENERGIA", []))
    if energy >= 5000:
        ideas.append(_idea("energia", "Efficientamento energetico delle sedi", ["EFFICIENZA_ENERGETICA"], [f"L'azienda spende circa {energy:,.0f} € l'anno di energia e riscaldamento".replace(",", ".") + ": un intervento di efficientamento o un impianto fotovoltaico è un progetto classico dei bandi."],
                           [_line("Intervento di efficientamento (da dimensionare)", "CAPITAL_ASSETS", "CAP_IMPIANTI", None, TO_QUANTIFY, "Serve una diagnosi energetica o un preventivo: dai documenti non si ricava", [])],
                           ["Diagnosi energetica o preventivo dell'impianto", "Se le sedi sono in affitto: l'accordo del proprietario"]))

    # i preventivi dei fornitori: dove c'è un preventivo valido per quel tipo di spesa, l'importo è quello del preventivo (il più basso se sono più d'uno, e si dice)
    qs = [q for q in company_facts.quotes(owner) if not q["expired"] and q.get("expense_type")]
    for idea in ideas:
        if not idea["id"].startswith("piano-"):
            continue
        for ln in idea["lines"]:
            mine = sorted((q for q in qs if q["expense_type"] == ln["expense_type"]), key=lambda q: q["net_eur"])
            if not mine or ln["nature"] == ORDINARY:
                continue
            best = mine[0]
            plan_amount = ln["amount_eur"]
            ln["quotes"] = [{"supplier": q["supplier"], "number": q.get("number"), "date": q.get("date"), "valid_until": q.get("valid_until"), "net_eur": q["net_eur"], "document": q["_doc"]["filename"]} for q in mine]
            ln["amount_eur"] = best["net_eur"]
            ln["nature"] = NEW
            ln["plan_amount_eur"] = plan_amount
            ln["detail"] = (f"Preventivo n. {best.get('number') or '—'} di {best['supplier']} del {best.get('date') or '—'}" + (f", il più basso di {len(mine)}" if len(mine) > 1 else "")
                            + (f" (il piano degli investimenti indicava {plan_amount:,.2f} €)".replace(",", "§").replace(".", ",").replace("§", ".") if plan_amount else ""))
            ln["sources"] = [{"document_id": best["_doc"]["id"], "filename": best["_doc"]["filename"], "where": f"preventivo {best.get('number') or ''}"}]
        idea["new_eur"] = round(sum(ln["amount_eur"] or 0 for ln in idea["lines"] if ln["nature"] == NEW), 2)
        left = [ln for ln in idea["lines"] if ln["nature"] == NEW and not ln.get("quotes")]
        idea["missing"] = [m for m in idea["missing"] if not m.startswith("Un preventivo per ogni acquisto")]
        if left:
            idea["missing"].insert(0, f"Un preventivo per {len(left)} {'acquisto' if len(left) == 1 else 'acquisti'}: " + ", ".join(ln["label"] for ln in left))
        else:
            idea["quoted"] = True
    # le idee con spese nuove per prime
    ideas.sort(key=lambda i: (-i["new_eur"], -i["ordinary_eur"], i["id"]))

    # i bandi che finanziano quel tipo di progetto
    bt = _bando_types()
    for idea in ideas:
        idea["bandi"] = [{"bando_id": bid, "name": b["name"], "issuer": b["issuer"], "status": b["status"], "types": [b["types"][t]["label"] for t in idea["project_types"] if t in b["types"]],
                          "evidence": next((b["types"][t]["evidence"][0] for t in idea["project_types"] if t in b["types"] and b["types"][t]["evidence"]), None),
                          "mode": b["mode"]["label"] if b["mode"] else None, "needs_project": b["mode"]["needs_project"] if b["mode"] else None, "ordinary_costs_ok": b["mode"]["ordinary_costs_ok"] if b["mode"] else None}
                         for bid, b in bt.items() if any(t in b["types"] for t in idea["project_types"])]
        for n, ln in enumerate(idea["lines"], 1):
            ln["item_id"] = f"IDEA-{idea['id']}-{n:02d}"
    # le misure che non chiedono un progetto: la loro base è un'altra (acquisti, finanziamento, persone assunte, spese commerciali, dati storici)
    no_project = [{"bando_id": bid, "name": b["name"], "issuer": b["issuer"], "status": b["status"], "mode": b["mode"]["label"], "base": b["mode"]["base"], "example": b["mode"]["example"],
                   "ordinary_costs_ok": b["mode"]["ordinary_costs_ok"]} for bid, b in bt.items() if b["mode"] and not b["mode"]["needs_project"]]
    notes.append("Le idee sono ipotesi costruite sui tuoi documenti: vanno validate con l'imprenditore. Un importo che non viene da un documento non è inventato: la riga resta «da quantificare».")
    notes.append("Le spese «ordinarie» sono costi che l'azienda sostiene comunque: non diventano spese di progetto. Un bando può ammetterne alcune per forma (spese generali a forfait, personale realmente dedicato con timesheet).")
    return {"year": year, "ideas": ideas, "no_project": no_project, "notes": notes}


def parsers_norm(s: str) -> str:
    return expense_types.norm(s)
