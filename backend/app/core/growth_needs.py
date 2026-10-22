"""Di cosa ha bisogno l'azienda per crescere: persone e strumenti in più, ricavati dal bilancio e dalla previsione.

Si parte da due fatti dell'ultimo bilancio e da una previsione:
- **persone**: ricavi per persona (ricavi ÷ organico medio). Se i ricavi previsti crescono, servono più persone per produrli: ricavi previsti ÷ ricavi per persona, meno chi c'è già e chi è
  già in programma nel piano delle assunzioni;
- **strumenti**: intensità di capitale (costo dei beni nel libro cespiti ÷ ricavi). Se i ricavi crescono servono più beni: ricavi previsti × intensità, meno i beni che ci sono già e gli
  investimenti già nel piano dell'azienda.

È un'ipotesi dichiarata («a parità di produttività e di intensità di capitale»), non una previsione: serve a dire all'imprenditore *cosa si dovrebbe finanziare* se la crescita prevista si
avvera, e a cercare i bandi che lo finanziano. Nessun numero è inventato: ogni passaggio mostra i dati dei documenti da cui viene, e se un dato manca lo dice invece di stimare.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

MIN_ASSET_NEED_EUR = 5_000.0          # sotto questa cifra non è un bisogno da finanziare
MIN_PEOPLE_GAP = 0.5                  # mezza persona o meno non è un'assunzione


def _eur(x: float) -> str:
    return f"{x:,.0f} €".replace(",", ".")


def _dec(x: float, digits: int = 1) -> str:
    """Numero con la virgola decimale (1,5; 28; 30,3)."""
    t = f"{x:.{digits}f}".rstrip("0").rstrip(".") if digits else f"{x:.0f}"
    return t.replace(".", ",")


def growth_needs(owner: str, year: Optional[int] = None) -> Dict[str, Any]:
    from app.core import company_facts, company_profile as cp
    fin = cp._load_financials(owner)
    years = [y for y in sorted(fin) if any(fin[y][0].get(cp.FIN_KEY[c]) is not None for c in cp.CATEGORIES)]
    if not years:
        raise cp.ProfileError("Mancano i dati di bilancio: carica un bilancio nel profilo o inserisci i costi dell'ultimo esercizio")
    year = year or years[-1] + 1
    fc = cp.forecast(owner, year)
    base_year = fc["base_year"]
    base = fin[base_year][0]
    out: Dict[str, Any] = {"year": year, "base_year": base_year, "needs": [], "missing": [], "growth_pct": None, "revenue_base_eur": None, "revenue_forecast_eur": None,
                           "assumption": "A parità di produttività (ricavi per persona) e di intensità di capitale (beni per euro di ricavi): è un'ipotesi da confermare con l'imprenditore, non una previsione."}
    rev = fc.get("revenue")
    if not rev or not rev.get("baseline_eur") or rev["baseline_eur"] <= 0:
        out["missing"].append(f"Mancano i ricavi del bilancio {base_year}: senza non si può dire quanto crescerà l'azienda.")
        return out
    r0, r1 = float(rev["baseline_eur"]), float(rev["forecast_eur"])
    out.update({"revenue_base_eur": r0, "revenue_forecast_eur": r1, "growth_pct": round((r1 / r0 - 1) * 100, 1), "revenue_explanation": rev.get("explanation")})
    if r1 <= r0:
        out["message"] = f"La previsione non vede crescita dei ricavi ({_eur(r0)} nel {base_year}, {_eur(r1)} nel {year}): non servono persone o strumenti in più per sostenerla."
        return out
    f = company_facts.facts(owner)
    staff = company_facts.staff(owner)

    # ---- persone
    employees = base.get("employees_avg") or (len(staff["people"]) or None)
    personnel = base.get("personnel_eur")
    if not employees or employees <= 0:
        out["missing"].append(f"Manca l'organico medio del bilancio {base_year}: senza non so quante persone servono.")
    else:
        per_head = r0 / employees
        required = r1 / per_head
        planned = len([h for h in staff["hiring_plan"] if h["start"][:4] in (str(year), str(year - 1))])
        gap = required - employees - planned
        basis = (f"Nel {base_year} i ricavi sono {_eur(r0)} con {_dec(employees)} persone: {_eur(per_head)} a persona. Nel {year} i ricavi previsti sono {_eur(r1)} (+{_dec(out['growth_pct'])}%): "
                 f"a parità di produttività servono {_dec(required)} persone. Ce ne sono {_dec(employees)}" + (f" e {planned} sono già nel piano delle assunzioni" if planned else "") + ".")
        if gap >= MIN_PEOPLE_GAP and personnel:
            n = max(1, round(gap))
            cost = personnel / employees
            out["needs"].append({"kind": "PERSONE", "label": f"{n} {'persona' if n == 1 else 'persone'} in più", "quantity": n, "unit_cost_eur": round(cost, 2), "amount_eur": round(n * cost, 2), "category": "PERSONNEL",
                                 "basis": basis + f" Ne mancano circa {n}, a un costo medio di {_eur(cost)} l'anno ciascuna (personale {_eur(personnel)} ÷ {_dec(employees)} persone)."})
        elif gap >= MIN_PEOPLE_GAP:
            out["missing"].append(f"Mancano i costi di personale del bilancio {base_year}: non posso dire quanto costerebbero le persone in più.")
        else:
            out["people_message"] = basis + " Non servono persone in più."

    # ---- strumenti
    lines = f.get("asset_line") or []
    gross = sum(float(a["cost_eur"] or 0) for a in lines)
    if not lines or gross <= 0:
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
    needs_total = round(sum(n["amount_eur"] for n in out["needs"]), 2)
    out["total_eur"] = needs_total
    out["message"] = ("Per sostenere la crescita prevista servono: " + "; ".join(n["label"] for n in out["needs"]) + f". In tutto circa {_eur(needs_total)} l'anno.") if out["needs"] else "Con la crescita prevista l'azienda non ha bisogno di persone o strumenti in più."
    return out
