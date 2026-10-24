"""Di cosa ha bisogno l'azienda per crescere: persone (e in quale reparto) e strumenti in più, ricavati dal bilancio o dalla dichiarazione dei redditi e dalla previsione.

Si parte da due fatti dell'ultimo esercizio e da una previsione:
- **persone**: ricavi per persona (ricavi ÷ organico medio). Se i ricavi previsti crescono, servono più persone per produrli: ricavi previsti ÷ ricavi per persona, meno chi c'è già e chi è
  già in programma nel piano delle assunzioni. In quale reparto: se lo studio lo indica, vale quello; altrimenti si propone la **stessa composizione di oggi** (dai ruoli del registro del
  personale), dichiarata come ipotesi; senza ruoli si chiede, non si indovina;
- **strumenti**: intensità di capitale (costo dei beni nel libro cespiti ÷ ricavi). Se i ricavi crescono servono più beni: ricavi previsti × intensità, meno i beni che ci sono già e gli
  investimenti già nel piano dell'azienda.

È un'ipotesi dichiarata («a parità di produttività e di intensità di capitale»), non una previsione: serve a dire all'imprenditore *cosa si dovrebbe finanziare* se la crescita prevista si
avvera, e a cercare le agevolazioni adatte: sgravi e esoneri senza progetto, e i tipi di progetto che i bandi finanziano. Nessun numero è inventato: ogni passaggio mostra i dati da cui viene, e
se un dato manca lo dice. Il riassunto è di al massimo 40 parole: una frase che l'imprenditore legge in dieci secondi.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

MIN_ASSET_NEED_EUR = 5_000.0          # sotto questa cifra non è un bisogno da finanziare
MIN_PEOPLE_GAP = 0.5                  # mezza persona o meno non è un'assunzione
SUMMARY_MAX_WORDS = 40

# reparto -> (etichetta, parole che lo riconoscono in un ruolo, tipi di progetto che finanziano chi ci lavora, esempio di progetto)
DEPARTMENTS: Dict[str, Dict[str, Any]] = {
    "COMMERCIALE": {"short": "marketing e vendite", "label": "Marketing e vendite", "words": ["MARKETING", "COMMERCIAL", "VENDIT", "SALES", "COMUNICAZION", "BRAND", "SOCIAL", "EXPORT", "ACCOUNT"],
                    "types": ["INTERNAZIONALIZZAZIONE", "MARKETING", "OCCUPAZIONE"], "example": "Progetto di sviluppo commerciale: nuovi mercati o vendite online, con una risorsa dedicata."},
    "TECNICO": {"short": "area tecnica", "label": "Tecnici e ingegneri", "words": ["INGEGNER", "TECNIC", "SVILUPPAT", "PROGETTIST", "RICERC", "R&D", "ANALIST", "DEVELOPER", "ENGINEER", "ARCHITETT", "CAD"],
                "types": ["RICERCA_SVILUPPO", "DIGITALIZZAZIONE", "OCCUPAZIONE"], "example": "Progetto di innovazione di prodotto o di processo, con personale tecnico dedicato."},
    "PRODUZIONE": {"short": "produzione", "label": "Produzione e operai", "words": ["OPERAI", "OPERATOR", "PRODUZION", "MONTAGG", "ADDETT", "MACCHIN", "SALDAT", "CONDUTTOR", "MANUTENT"],
                   "types": ["INVESTIMENTI_PRODUTTIVI", "OCCUPAZIONE"], "example": "Ampliamento della produzione: nuovi macchinari e nuovi operai."},
    "MAGAZZINO": {"short": "magazzino e logistica", "label": "Magazzino e logistica", "words": ["MAGAZZIN", "LOGISTIC", "SPEDIZION", "CARRELL", "FACCHIN", "AUTISTA"],
                  "types": ["INVESTIMENTI_PRODUTTIVI", "OCCUPAZIONE"], "example": "Potenziamento di magazzino e logistica: attrezzature e personale."},
    "AMMINISTRAZIONE": {"short": "amministrazione", "label": "Amministrazione", "words": ["AMMINISTR", "CONTABIL", "SEGRETER", "HR", "RISORSE UMANE", "BACK OFFICE", "CONTROLLER", "UFFICIO"],
                        "types": ["OCCUPAZIONE", "DIGITALIZZAZIONE"], "example": "Riorganizzazione amministrativa con digitalizzazione dei processi."},
    "IT": {"short": "informatica", "label": "Informatica e digitale", "words": ["IT ", "INFORMATIC", "SISTEMIST", "SOFTWARE", "DIGITAL", "DATA", "CYBER", "WEB"],
           "types": ["DIGITALIZZAZIONE", "OCCUPAZIONE"], "example": "Progetto di trasformazione digitale con una figura dedicata."},
}


def _eur(x: float) -> str:
    return f"{x:,.0f} €".replace(",", ".")


def _dec(x: float, digits: int = 1) -> str:
    """Numero con la virgola decimale (1,5; 28; 30,3)."""
    t = f"{x:.{digits}f}".rstrip("0").rstrip(".") if digits else f"{x:.0f}"
    return t.replace(".", ",")


def dept_of(role: Optional[str]) -> Optional[str]:
    t = f" {re.sub(r'[^A-Z0-9& ]', ' ', str(role or '').upper())} "
    for code, spec in DEPARTMENTS.items():
        if any(w in t for w in spec["words"]):
            return code
    return None


def parse_split(raw: Optional[str]) -> Dict[str, int]:
    """«COMMERCIALE:2,TECNICO:1» → {'COMMERCIALE': 2, 'TECNICO': 1}. Reparti sconosciuti o numeri non validi si scartano."""
    out: Dict[str, int] = {}
    for part in str(raw or "").split(","):
        if ":" not in part:
            continue
        k, v = part.split(":", 1)
        k = k.strip().upper()
        try:
            n = int(float(v.strip()))
        except ValueError:
            continue
        if k in DEPARTMENTS and 0 < n <= 500:
            out[k] = n
    return out


def _spread(total: int, weights: Dict[str, int]) -> Dict[str, int]:
    """Divide ``total`` persone in proporzione ai pesi (metodo del resto più grande): somma esatta, nessun reparto inventato."""
    s = sum(weights.values())
    if not s or total <= 0:
        return {}
    raw = {k: total * v / s for k, v in weights.items()}
    out = {k: int(x) for k, x in raw.items()}
    for k in sorted(raw, key=lambda k: (-(raw[k] - out[k]), k))[: total - sum(out.values())]:
        out[k] += 1
    return {k: v for k, v in out.items() if v}


def cap_words(text: str, limit: int = SUMMARY_MAX_WORDS) -> str:
    """Al massimo ``limit`` parole: se il testo è più lungo si taglia a fine frase o, in mancanza, si chiude con un punto."""
    words = text.split()
    if len(words) <= limit:
        return text
    cut = " ".join(words[:limit])
    last = max(cut.rfind(". "), cut.rfind("; "))
    return (cut[: last + 1] if last > len(cut) // 2 else cut.rstrip(",;:") + ".")


def summary_of(out: Dict[str, Any]) -> str:
    """Di cosa ha bisogno l'impresa, in al massimo 40 parole."""
    needs = out["needs"]
    if out.get("growth_pct") is None:
        return "Mancano i ricavi dell'ultimo esercizio: senza non posso dire di cosa ha bisogno l'impresa per crescere."
    if not needs:
        return cap_words(f"Con ricavi {'in crescita del ' + _dec(out['growth_pct']) + '%' if out['growth_pct'] > 0 else 'stabili'} l'impresa non ha bisogno di persone o strumenti in più.")
    parts = []
    people = out.get("people")
    if people and people["total"]:
        ds = people["departments"]
        if not ds:
            parts.append(f"{people['total']} {'persona' if people['total'] == 1 else 'persone'} (reparto da indicare)")
        elif len(ds) == 1:
            parts.append(f"{people['total']} {'persona' if people['total'] == 1 else 'persone'} in {DEPARTMENTS[ds[0]['id']]['short']}")
        else:
            parts.append(f"{people['total']} persone ({', '.join(str(d['count']) + ' in ' + DEPARTMENTS[d['id']]['short'] for d in ds)})")
    assets = next((n for n in needs if n["kind"] == "STRUMENTI"), None)
    if assets:
        parts.append(f"strumenti per circa {_eur(assets['amount_eur'])}")
    head = f"Per sostenere la crescita del {_dec(out['growth_pct'])}% servono " + " e ".join(parts) + "."
    tail = []
    if people and people.get("planned"):
        tail.append(f"{people['planned']} assunzioni sono già in programma.")
    if people and people["departments"] and people.get("departments_basis") == "MIX_ATTUALE":
        tail.append("Reparti: ipotesi dalla composizione attuale.")
    return cap_words(" ".join([head] + tail))


def growth_needs(owner: str, year: Optional[int] = None, split: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
    from app.core import company_facts, company_profile as cp, measures, project_types
    fin = cp._load_financials(owner)
    years = [y for y in sorted(fin) if any(fin[y][0].get(cp.FIN_KEY[c]) is not None for c in cp.CATEGORIES)]
    if not years:
        raise cp.ProfileError("Mancano i dati di bilancio o della dichiarazione dei redditi: carica il documento o inserisci i dati dell'ultimo esercizio")
    year = year or years[-1] + 1
    fc = cp.forecast(owner, year)
    base_year = fc["base_year"]
    base = fin[base_year][0]
    profile = cp.profile_values(owner)
    out: Dict[str, Any] = {"year": year, "base_year": base_year, "needs": [], "missing": [], "growth_pct": None, "revenue_base_eur": None, "revenue_forecast_eur": None, "people": None,
                           "assumption": "A parità di produttività (ricavi per persona) e di intensità di capitale (beni per euro di ricavi): è un'ipotesi da confermare con l'imprenditore, non una previsione.",
                           "company_type": profile.get("company_type")}
    rev = fc.get("revenue")
    if not rev or not rev.get("baseline_eur") or rev["baseline_eur"] <= 0:
        out["missing"].append(f"Mancano i ricavi dell'esercizio {base_year}: senza non si può dire quanto crescerà l'azienda.")
        out["summary"] = summary_of(out)
        return out
    r0, r1 = float(rev["baseline_eur"]), float(rev["forecast_eur"])
    out.update({"revenue_base_eur": r0, "revenue_forecast_eur": r1, "growth_pct": round((r1 / r0 - 1) * 100, 1), "revenue_explanation": rev.get("explanation")})
    f = company_facts.facts(owner)
    staff = company_facts.staff(owner)
    split = {k: v for k, v in (split or {}).items() if k in DEPARTMENTS and v > 0}

    # ---- persone
    employees = base.get("employees_avg") or profile.get("employees") or (len(staff["people"]) or None)
    personnel = base.get("personnel_eur")
    people_total = 0
    basis = ""
    planned = len([h for h in staff["hiring_plan"] if h["start"][:4] in (str(year), str(year - 1))])
    if not employees or employees <= 0:
        if split:
            out["missing"].append("Manca l'organico: il numero di persone è quello indicato dallo studio, ma non so quanto costerebbero in media.")
            people_total = sum(split.values())
        else:
            out["missing"].append(f"Manca l'organico medio dell'esercizio {base_year}: senza non so quante persone servono. Se l'impresa non ha ancora dipendenti, indica tu di quali reparti ha bisogno.")
    else:
        per_head = r0 / employees
        required = r1 / per_head
        gap = required - employees - planned
        basis = (f"Nel {base_year} i ricavi sono {_eur(r0)} con {_dec(employees)} persone: {_eur(per_head)} a persona. Nel {year} i ricavi previsti sono {_eur(r1)} (+{_dec(out['growth_pct'])}%): "
                 f"a parità di produttività servono {_dec(required)} persone. Ce ne sono {_dec(employees)}" + (f" e {planned} sono già nel piano delle assunzioni" if planned else "") + ".")
        if split:
            people_total = sum(split.values())
        elif out["growth_pct"] > 0 and gap >= MIN_PEOPLE_GAP:
            people_total = max(1, round(gap))
        if not people_total:
            out["people_message"] = basis + (" Non servono persone in più." if out["growth_pct"] > 0 else "")
    if people_total:
        cost = (personnel / employees) if (personnel and employees) else None
        if split:
            depts, dbasis = split, "SCELTA_STUDIO"
        else:
            mix: Dict[str, int] = {}
            for p in staff["people"]:
                d = dept_of(p.get("role"))
                if d:
                    mix[d] = mix.get(d, 0) + 1
            depts, dbasis = _spread(people_total, mix), "MIX_ATTUALE"
        dept_rows = [{"id": k, "label": DEPARTMENTS[k]["label"], "count": v, "types": DEPARTMENTS[k]["types"], "example": DEPARTMENTS[k]["example"]} for k, v in sorted(depts.items(), key=lambda kv: -kv[1])]
        out["people"] = {"total": people_total, "departments": dept_rows, "departments_basis": dbasis if dept_rows else None, "ask_departments": not dept_rows, "planned": planned,
                         "unit_cost_eur": round(cost, 2) if cost else None}
        if cost:
            txt = (basis + f" Ne mancano circa {people_total}, a un costo medio di {_eur(cost)} l'anno ciascuna (personale {_eur(personnel)} ÷ {_dec(employees)} persone)." if not split else
                   f"Lo studio ha indicato {people_total} {'persona' if people_total == 1 else 'persone'} in più, a un costo medio di {_eur(cost)} l'anno ciascuna (personale {_eur(personnel)} ÷ {_dec(employees)} persone).")
            out["needs"].append({"kind": "PERSONE", "label": f"{people_total} {'persona' if people_total == 1 else 'persone'} in più", "quantity": people_total, "unit_cost_eur": round(cost, 2),
                                 "amount_eur": round(people_total * cost, 2), "category": "PERSONNEL", "basis": txt, "departments": dept_rows})
        else:
            out["missing"].append(f"Mancano i costi di personale dell'esercizio {base_year}: non posso dire quanto costerebbero le persone in più.")
        if not dept_rows:
            out["missing"].append("Indica in quali reparti servono le persone (marketing, produzione, magazzino…): i ruoli del registro del personale non bastano a proporlo.")

    # ---- strumenti
    lines = f.get("asset_line") or []
    gross = sum(float(a["cost_eur"] or 0) for a in lines)
    if out["growth_pct"] <= 0:
        out["message"] = f"La previsione non vede crescita dei ricavi ({_eur(r0)} nel {base_year}, {_eur(r1)} nel {year}): non servono strumenti in più per sostenerla."
    elif not lines or gross <= 0:
        out["missing"].append("Manca il libro cespiti: senza non so quanti beni servono per produrre i ricavi previsti.")
    else:
        intensity = gross / r0
        required_assets = r1 * intensity
        capex = sum(float(c["amount_eur"] or 0) for c in f.get("capex_plan", []) if c["year"] in (year, year - 1))
        gap_a = required_assets - gross - capex
        basis_a = (f"Il libro cespiti vale {_eur(gross)} di costo storico su {_eur(r0)} di ricavi: {_dec(intensity * 100)}% (beni per euro di ricavi). "
                   f"Con i ricavi previsti nel {year} ({_eur(r1)}) servirebbero {_eur(required_assets)} di beni." + (f" Il piano degli investimenti ne prevede già {_eur(capex)}." if capex else ""))
        if gap_a >= MIN_ASSET_NEED_EUR:
            out["needs"].append({"kind": "STRUMENTI", "label": f"Strumenti e attrezzature per circa {_eur(gap_a)}", "quantity": None, "amount_eur": round(gap_a, 2), "category": "CAPITAL_ASSETS",
                                 "basis": basis_a + f" Mancano circa {_eur(gap_a)}."})
        else:
            out["assets_message"] = basis_a + " Non servono strumenti in più."
    out["total_eur"] = round(sum(n["amount_eur"] for n in out["needs"]), 2)
    out["message"] = out.get("message") or (("Per sostenere la crescita prevista servono: " + "; ".join(n["label"] for n in out["needs"]) + f". In tutto circa {_eur(out['total_eur'])} l'anno.") if out["needs"]
                                           else "Con la crescita prevista l'azienda non ha bisogno di persone o strumenti in più.")
    out["summary"] = summary_of(out)
    out["summary_words"] = len(out["summary"].split())

    # ---- come farli finanziare: senza progetto (esoneri e sgravi) e con un progetto (che tipi di progetto scrivere)
    if out["people"]:
        n = out["people"]["total"]
        out["without_project"] = measures.best_for_hires(profile, n)
        seen: Dict[str, Dict[str, Any]] = {}
        for d in out["people"]["departments"]:
            for t in d["types"]:
                seen.setdefault(t, {"type": t, "departments": []})["departments"].append(d["label"])
        out["with_project"] = [{"type": t, "label": project_types.label(t), "for": v["departments"]} for t, v in seen.items()]
        out["project_examples"] = [{"department": d["label"], "example": d["example"]} for d in out["people"]["departments"]]
    return out
