"""Tabelle di Fonte B SOLO PER I TEST, caricate attraverso lo stesso percorso di importazione usato in produzione.

I valori sono quelli usati dai test storici del motore: NON sono tabelle ufficiali e nel codice dell'applicazione non esistono.
"""
from datetime import date

from app.core import fonte_b_admin as admin

SOURCE = "FIXTURE DI TEST (valori non ufficiali)"

CCNL = {
    "TERZO_SETTORE": "level;standard_hours;social_charges_pct;tfr_pct\n1;1656;31%;8,33%\n2;1656;30%;8,33%\n3;1656;30%;8,33%\n",
    "METALMECCANICA": "level;standard_hours;social_charges_pct;tfr_pct\n3;1600;32%;8,33%\n5;1600;32%;8,33%\n",
    "COMMERCIO": "level;standard_hours;social_charges_pct;tfr_pct\n3;1680;29,5%;8,33%\n4;1680;29,5%;8,33%\n",
}
PARAMS = "param_key;value;unit\nfixed_term_surcharge_pct;1,4%;frazione\noccasional_income_limit_eur;5000;euro\n"
AMORT = "category_code;description;rate_pct\nMACCHINARI;Macchinari e impianti;20%\nINFORMATICA;Hardware e software;20%\n"
BENCH = "bench_kind;category_code;description;reference_eur\nPRICE;CNC;Centro di lavoro;220000\nDAILY_RATE;ENERGY_AUDIT;Consulenza energetica;450\n"


def load(valid_from: date = date(2000, 1, 1)) -> None:
    def put(kind, code, csv_text, version="test-1"):
        d = admin.create_draft(kind, code, f"{kind} {code}", version, valid_from, None, SOURCE, "https://esempio.test/fixture", None, "fixture.csv",
                               csv_text.encode(), actor="test")
        admin.publish(d["id"], "test", attest_official=True)

    for code, text in CCNL.items():
        put("CCNL", code, text)
    put("PARAMS", "PARAMETRI", PARAMS)
    put("AMORTIZATION", "TABELLA-AMM", AMORT)
    put("BENCHMARK", "BENCHMARK", BENCH)
