"""Il de minimis dell'azienda: quanto del tetto di 300.000 € in tre anni è ancora disponibile.

QUANTO non può leggere il Registro Nazionale degli Aiuti. La stima parte quindi da ciò che i bilanci degli ultimi tre esercizi dichiarano. Per ogni esercizio vale, in ordine:
gli «Aiuti de minimis» letti dalla tabella della nota integrativa (art. 1, commi 125-129, L. 124/2017: soggetto, misura, data, importo, regime), oppure, se manca,
la voce «Contributi pubblici ricevuti» scritta a mano. La stima dice con chiarezza su cosa si regge:

* ``DICHIARATI``: tutti e tre gli esercizi hanno la voce compilata → residuo = 300.000 − somma;
* ``PARZIALE``: solo alcuni esercizi hanno la voce → si sottrae quanto dichiarato, per gli altri non c'è alcun dato;
* ``IPOTESI``: nessun esercizio ha la voce → 300.000 € nell'ipotesi, dichiarata, che non ci siano aiuti.

Quando si parte dalla voce scritta a mano («anche de minimis») ogni contributo conta per prudenza come de minimis: il residuo vero può essere solo maggiore, mai minore.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

PLAFOND_EUR = 300_000.0
YEARS = 3


def estimate(owner: str, year: int, used_by_plan_eur: Optional[float] = None) -> Dict[str, Any]:
    from app.core import company_profile as cp
    fin = cp._load_financials(owner)
    window = [year - k for k in range(YEARS, 0, -1)]            # i tre esercizi che precedono l'anno del piano
    def declared_for(y: int) -> Optional[float]:
        if y not in fin:
            return None
        data, src = fin[y]
        manual = data.get("public_aid_eur") if (src.get("public_aid_eur") or {}).get("origin") == "MANUAL" else None
        v = manual if manual is not None else data.get("de_minimis_aid_eur")       # quello che l'utente ha scritto vale più di ciò che si è letto dal bilancio
        if v is None:
            v = data.get("public_aid_eur")
        return None if v is None else max(0.0, float(v))
    declared = {y: v for y in window if (v := declared_for(y)) is not None}
    missing = [y for y in window if y not in declared]
    received = round(sum(declared.values()), 2)
    residual = round(max(0.0, PLAFOND_EUR - received), 2)
    basis = "DICHIARATI" if not missing else ("PARZIALE" if declared else "IPOTESI")
    def it(x: float) -> str:                                        # 16.500 (punto delle migliaia all'italiana)
        return f"{x:,.0f}".replace(",", ".")
    if basis == "DICHIARATI":
        note = f"Aiuti de minimis dichiarati nei bilanci {window[0]}–{window[-1]}: {it(received)} €. Residuo = 300.000 € − {it(received)} €."
    elif basis == "PARZIALE":
        note = (f"Aiuti de minimis dichiarati nei bilanci {' e '.join(map(str, sorted(declared)))}: {it(received)} €. Per {' e '.join(map(str, missing))} non c'è ancora un bilancio con il dato, "
                "quindi non si sottrae nulla.")
    else:
        note = "Nessun aiuto de minimis dichiarato nei bilanci degli ultimi tre esercizi: il residuo è 300.000 € nell'ipotesi che l'azienda non abbia ricevuto altri aiuti. Non è un dato verificato."
    out = {"plafond_eur": PLAFOND_EUR, "received_eur": received, "residual_eur": residual, "basis": basis, "years_declared": sorted(declared), "years_missing": missing,
           "window": [window[0], window[-1]], "note": note,
           "verify": "Per verificarlo: visura aiuti sul Registro Nazionale degli Aiuti (RNA), provvedimenti di concessione già ricevuti, dichiarazioni de minimis firmate per le domande precedenti; "
                     "per un gruppo di società collegate si sommano gli aiuti di tutte."}
    if used_by_plan_eur is not None:
        out["needed_eur"] = round(used_by_plan_eur, 2)
        out["margin_eur"] = round(residual - used_by_plan_eur, 2)
    return out
