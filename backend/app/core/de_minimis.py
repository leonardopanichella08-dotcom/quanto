"""Il de minimis dell'azienda: quanto del tetto di 300.000 € in tre anni è ancora disponibile.

QUANTO non può leggere il Registro Nazionale degli Aiuti. La stima parte quindi da ciò che l'azienda ha dichiarato (voce «Contributi pubblici ricevuti» dei bilanci
degli ultimi tre esercizi) e dice con chiarezza su cosa si regge:

* ``DICHIARATI``: tutti e tre gli esercizi hanno la voce compilata → residuo = 300.000 − somma;
* ``PARZIALE``: solo alcuni esercizi hanno la voce → si sottrae quanto dichiarato, per gli altri non c'è alcun dato;
* ``IPOTESI``: nessun esercizio ha la voce → 300.000 € nell'ipotesi, dichiarata, che non ci siano aiuti.

Per prudenza ogni contributo pubblico dichiarato conta come de minimis (può non esserlo: allora il residuo vero è maggiore, mai minore).
"""
from __future__ import annotations

from typing import Any, Dict, Optional

PLAFOND_EUR = 300_000.0
YEARS = 3


def estimate(owner: str, year: int, used_by_plan_eur: Optional[float] = None) -> Dict[str, Any]:
    from app.core import company_profile as cp
    fin = cp._load_financials(owner)
    window = [year - k for k in range(YEARS, 0, -1)]            # i tre esercizi che precedono l'anno del piano
    declared = {y: float(fin[y][0]["public_aid_eur"]) for y in window if y in fin and fin[y][0].get("public_aid_eur") is not None}
    missing = [y for y in window if y not in declared]
    received = round(sum(declared.values()), 2)
    residual = round(max(0.0, PLAFOND_EUR - received), 2)
    basis = "DICHIARATI" if not missing else ("PARZIALE" if declared else "IPOTESI")
    if basis == "DICHIARATI":
        note = f"Contributi pubblici dichiarati negli esercizi {window[0]}–{window[-1]}: {received:,.0f} €. Residuo = 300.000 € − {received:,.0f} €.".replace(",", ".")
    elif basis == "PARZIALE":
        note = (f"Dichiarati {received:,.0f} € di contributi pubblici per gli esercizi {', '.join(map(str, sorted(declared)))}; per {', '.join(map(str, missing))} non c'è nessun dato, "
                "quindi non si sottrae nulla.").replace(",", ".")
    else:
        note = "Nessun contributo pubblico dichiarato negli ultimi tre esercizi: il residuo è 300.000 € nell'ipotesi che l'azienda non abbia ricevuto altri aiuti. Non è un dato verificato."
    out = {"plafond_eur": PLAFOND_EUR, "received_eur": received, "residual_eur": residual, "basis": basis, "years_declared": sorted(declared), "years_missing": missing,
           "window": [window[0], window[-1]], "note": note,
           "verify": "Per verificarlo: visura aiuti sul Registro Nazionale degli Aiuti (RNA), provvedimenti di concessione già ricevuti, dichiarazioni de minimis firmate per le domande precedenti; "
                     "per un gruppo di società collegate si sommano gli aiuti di tutte."}
    if used_by_plan_eur is not None:
        out["needed_eur"] = round(used_by_plan_eur, 2)
        out["margin_eur"] = round(residual - used_by_plan_eur, 2)
    return out
