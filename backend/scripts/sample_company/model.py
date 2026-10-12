"""Il modello contabile di Meridiana Digital Solutions S.r.l. (azienda COMPLETAMENTE FITTIZIA): tutti i numeri dei documenti vengono da qui.

Quattro esercizi (2022-2025) con stato patrimoniale, conto economico, rendiconto finanziario, movimenti delle immobilizzazioni, fiscalità e dettaglio dei conti.
I valori sono interi in euro (come in un bilancio redatto in unità di euro) e tornano tra loro: attivo = passivo, il rendiconto riconcilia le disponibilità liquide,
i movimenti delle immobilizzazioni portano ai saldi, le imposte discendono dal risultato. Nessun valore corrisponde a persone o imprese reali.
"""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Tuple

YEARS = (2023, 2024, 2025)
ALL_YEARS = (2022, 2023, 2024, 2025)

COMPANY = {
    "name": "MERIDIANA DIGITAL SOLUTIONS S.R.L.", "short": "Meridiana Digital Solutions S.r.l.", "legal_form": "Società a responsabilità limitata", "ateco": "62.01.00",
    "ateco_desc": "Produzione di software non connesso all'edizione", "street": "Via Giuseppe Garibaldi 28", "zip": "10122", "city": "TORINO", "prov": "TO",
    "founded": "14/03/2016", "rea": "TO-1187342", "pec": "meridianadigital@pec-prova.it", "capital": 50000, "addetti": 17,
    "iscr_ri": "21/03/2016", "cciaa": "Camera di Commercio Industria Artigianato e Agricoltura di Torino",
}


def vat_check(first10: str) -> str:
    s = 0
    for i, ch in enumerate(first10):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        s += d
    return str((10 - s % 10) % 10)


COMPANY["vat"] = "0987123001" + vat_check("0987123001")

# ------------------------------------------------------------------------------------------------ conto economico
# (codice voce CEE, sezione, descrizione, importi 2022..2025). Le sezioni sono quelle dell'art. 2425 c.c.
REVENUE = (900200, 1081400, 1327900, 1583200)
REVENUE_SPLIT = [                                           # ricavi per categoria di attività (quote del totale, sommano 100)
    ("Sviluppo software su commessa e personalizzazioni", (46, 45, 44, 43)),
    ("Canoni di licenza e abbonamenti alla piattaforma", (21, 24, 27, 30)),
    ("Consulenza informatica e analisi dei dati", (24, 22, 20, 18)),
    ("Formazione e assistenza tecnica", (9, 9, 9, 9)),
]
WIP = (38000, 46000, 61000, 74000)                           # lavori in corso su ordinazione (rimanenze finali)
GRANTS = (6000, 12000, 31500, 42000)                         # contributi in conto esercizio: credito d'imposta ricerca e sviluppo
OTHER_INCOME = (2100, 2900, 4200, 5800)
INT_INCOME = (210, 420, 980, 1450)
INT_EXPENSE = (11800, 11300, 10200, 8900)
FX_GAIN_LOSS = (0, -180, 240, -310)                           # utili e perdite su cambi (17-bis)
EMPLOYEES = {2022: 9, 2023: 11, 2024: 13, 2025: 15}
HEADCOUNT_SPLIT = {2022: (1, 7, 1), 2023: (1, 9, 1), 2024: (1, 10, 2), 2025: (1, 11, 3)}      # quadri, impiegati, apprendisti (numero medio)

# conti di costo: (voce CEE, descrizione, importi 2022..2025). Il dettaglio analitico è l'allegato del bilancio.
COSTS: List[Tuple[str, str, Tuple[int, int, int, int]]] = [
    ("6", "Cancelleria e materiale di consumo", (6100, 7120, 8450, 9800)),
    ("6", "Hardware di piccolo valore e materiale informatico di consumo", (3200, 4100, 5300, 6400)),
    ("6", "Materiale di pulizia e igiene", (1200, 1350, 1500, 1650)),
    ("6", "Carburanti e lubrificanti autovetture aziendali", (2400, 3600, 5100, 6200)),
    ("7", "Consulenze professionali informatiche e tecniche", (27900, 38400, 61200, 86500)),
    ("7", "Consulenze legali, fiscali e del lavoro", (17100, 18200, 19600, 21800)),
    ("7", "Compensi a professionisti e collaboratori esterni", (33200, 41000, 52300, 64200)),
    ("7", "Licenze software e servizi cloud", (28800, 36500, 47900, 58600)),
    ("7", "Energia elettrica e riscaldamento", (13900, 14800, 13900, 14300)),
    ("7", "Spese telefoniche e connettività", (8200, 8700, 9100, 9600)),
    ("7", "Assicurazioni", (9100, 9900, 10800, 11900)),
    ("7", "Pubblicità e marketing", (12300, 18600, 29400, 38700)),
    ("7", "Corsi di formazione e aggiornamento professionale", (6900, 9300, 14700, 18400)),
    ("7", "Manutenzione e pulizia uffici", (10600, 11200, 11900, 12800)),
    ("7", "Spese di rappresentanza e trasferte", (6400, 8900, 12300, 15600)),
    ("7", "Spese bancarie e commissioni", (3800, 4300, 4900, 5600)),
    ("7", "Spese postali e di corriere", (1500, 1700, 1900, 2100)),
    ("8", "Affitto uffici e spese condominiali", (42000, 48000, 54000, 54000)),
    ("8", "Canoni di locazione operativa autovetture", (4800, 7200, 10800, 13200)),
    ("8", "Canoni di locazione operativa apparecchiature informatiche", (3600, 4200, 4800, 5400)),
    ("9a", "Salari e stipendi", (371000, 449000, 538000, 640000)),
    ("9b", "Oneri sociali", (110400, 133600, 160100, 190400)),
    ("9c", "Trattamento di fine rapporto", (26900, 32500, 38900, 46200)),
    ("9e", "Altri costi del personale (buoni pasto e welfare aziendale)", (7100, 9400, 11700, 14100)),
    ("10a", "Ammortamento delle immobilizzazioni immateriali", (11900, 15200, 19800, 22400)),
    ("10b", "Ammortamento delle immobilizzazioni materiali", (17800, 21900, 27600, 31700)),
    ("10d", "Svalutazione dei crediti compresi nell'attivo circolante", (0, 0, 2500, 3000)),
    ("14", "Imposte e tasse indirette (imposta di bollo, tassa rifiuti, diritti camerali)", (3100, 3400, 3700, 4100)),
    ("14", "Quote associative e contributi a organismi di categoria", (1500, 1500, 1800, 1800)),
    ("14", "Sopravvenienze passive ordinarie", (0, 1200, 0, 2400)),
    ("14", "Erogazioni liberali", (0, 0, 1000, 1500)),
]
COST_HEAD = {"6": "6) per materie prime, sussidiarie, di consumo e di merci", "7": "7) per servizi", "8": "8) per godimento di beni di terzi", "14": "14) oneri diversi di gestione"}


def _i(y: int) -> int:
    return y - 2022


def acct(start: str, y: int) -> int:
    """Importo di un conto di costo, individuato dall'inizio della descrizione."""
    return next(v[_i(y)] for _, d, v in COSTS if d.startswith(start))


def cost_total(y: int, prefix: str = "") -> int:
    return sum(v[_i(y)] for code, _, v in COSTS if code.startswith(prefix))


def dep_intang(y: int) -> int:
    return cost_total(y, "10a")


def dep_tang(y: int) -> int:
    return cost_total(y, "10b")


def pl(y: int) -> Dict[str, int]:
    """Conto economico dell'esercizio ``y`` (voci dello schema civilistico, in euro)."""
    i = _i(y)
    wip_delta = WIP[i] - (WIP[i - 1] if i > 0 else 31000)
    capitalized = fixed_assets("intang")[y][0]["capex"]                 # i costi di sviluppo sono costruiti in casa: si capitalizzano
    a_total = REVENUE[i] + wip_delta + capitalized + GRANTS[i] + OTHER_INCOME[i]
    b = {k: cost_total(y, k) for k in ("6", "7", "8", "9a", "9b", "9c", "9e", "10a", "10b", "10d", "14")}
    b_total = sum(b.values())
    ebit = a_total - b_total
    fin = INT_INCOME[i] - INT_EXPENSE[i] + FX_GAIN_LOSS[i]
    pre_tax = ebit + fin
    tx = tax(y, ebit, pre_tax)
    net = pre_tax - tx["ires"] - tx["irap"]
    return {"revenue": REVENUE[i], "wip_delta": wip_delta, "capitalized": capitalized, "grants": GRANTS[i], "other_income": OTHER_INCOME[i], "a_total": a_total,
            **{f"b{k}": v for k, v in b.items()}, "b_total": b_total, "ebit": ebit, "int_income": INT_INCOME[i], "int_expense": INT_EXPENSE[i], "fx": FX_GAIN_LOSS[i],
            "fin": fin, "pre_tax": pre_tax, "ires": tx["ires"], "irap": tx["irap"], "taxes": tx["ires"] + tx["irap"], "net": net, "tax": tx}


def tax(y: int, ebit: int, pre_tax: int) -> Dict[str, int]:
    """Riconciliazione fiscale: onere teorico IRES, variazioni, imponibile, IRES e IRAP correnti."""
    i = _i(y)
    car_lease = acct("Canoni di locazione operativa autovetture", y)
    phone = acct("Spese telefoniche", y)
    repr_ = acct("Spese di rappresentanza", y)
    up = {"Costi di autovetture e canoni di locazione operativa indeducibili (quota 30%)": round(car_lease * 0.30),
          "Spese telefoniche indeducibili (quota 20%)": round(phone * 0.20),
          "Spese di rappresentanza e ospitalità oltre i limiti": round(repr_ * 0.25),
          "Imposte e tasse non deducibili e sopravvenienze passive indeducibili": round((acct("Imposte e tasse indirette", y) + acct("Sopravvenienze", y)) * 0.35)}
    down = {"Deduzione IRAP riferita al costo del lavoro": round(pre_tax * 0.04),
            "Deduzione per aiuto alla crescita economica (ACE)": round(pre_tax * 0.03),
            "Contributi in conto esercizio non imponibili (credito d'imposta ricerca e sviluppo)": GRANTS[i]}
    taxable = pre_tax + sum(up.values()) - sum(down.values())
    ires = max(0, round(taxable * 0.24))
    irap = round(max(0, ebit) * 0.039)
    return {"theoretical": round(pre_tax * 0.24), "up": up, "down": down, "taxable": taxable, "ires": ires, "irap": irap, "irap_base": max(0, ebit)}


# ------------------------------------------------------------------------------------------------ immobilizzazioni
# classe → (quota di capex, quota di ammortamento, costo storico 31/12/2021, fondo ammortamento 31/12/2021, aliquota di riferimento)
INTANG_CLASSES = [
    ("Costi di sviluppo", 0.72, 0.70, 98000, 54000, "20%"),
    ("Diritti di utilizzazione di opere dell'ingegno (software applicativo)", 0.18, 0.20, 22000, 14000, "33%"),
    ("Concessioni, licenze, marchi e diritti simili", 0.04, 0.04, 6200, 3600, "20%"),
    ("Altre immobilizzazioni immateriali (migliorie su beni di terzi)", 0.06, 0.06, 15000, 8000, "20%"),
]
TANG_CLASSES = [
    ("Impianti e macchinario (impianti di rete e cablaggio)", 0.12, 0.13, 28000, 15500, "15%"),
    ("Attrezzature industriali e commerciali (server e apparati di test)", 0.26, 0.27, 61000, 36000, "20%"),
    ("Altri beni: macchine d'ufficio elettroniche", 0.44, 0.42, 84000, 60000, "20%"),
    ("Altri beni: mobili e arredi", 0.12, 0.12, 31500, 14500, "12%"),
    ("Altri beni: autovetture e mezzi di trasporto interni", 0.06, 0.06, 18000, 10000, "25%"),
]
NET_INTANG = (64000, 78000, 92000, 106000)
NET_TANG = (92000, 101000, 110000, 119000)


def _alloc(total: int, shares: List[float]) -> List[int]:
    parts = [round(total * s) for s in shares]
    parts[0] += total - sum(parts)
    return parts


def fixed_assets(kind: str) -> Dict[int, List[Dict[str, int]]]:
    """Movimenti per classe e per esercizio: costo e fondo a inizio anno, acquisti, ammortamento, costo e fondo a fine anno, valore netto."""
    classes = INTANG_CLASSES if kind == "intang" else TANG_CLASSES
    nets = NET_INTANG if kind == "intang" else NET_TANG
    out: Dict[int, List[Dict[str, int]]] = {}
    cost = [c[3] for c in classes]
    fund = [c[4] for c in classes]
    # 2022: dato di partenza (costo e fondo a fine 2022 = quelli del 2021 più il movimento del 2022, calcolato come per gli altri anni)
    for y in ALL_YEARS:
        i = _i(y)
        dep_total = dep_intang(y) if kind == "intang" else dep_tang(y)
        prev_net = nets[i - 1] if i > 0 else sum(c[3] - c[4] for c in classes)
        capex_total = nets[i] - prev_net + dep_total
        capex = _alloc(capex_total, [c[1] for c in classes])
        dep = _alloc(dep_total, [c[2] for c in classes])
        rows = []
        for k in range(len(classes)):
            rows.append({"cost_open": cost[k], "fund_open": fund[k], "capex": capex[k], "dep": dep[k], "cost_close": cost[k] + capex[k], "fund_close": fund[k] + dep[k],
                         "net_open": cost[k] - fund[k], "net_close": cost[k] + capex[k] - fund[k] - dep[k]})
            cost[k] += capex[k]
            fund[k] += dep[k]
        out[y] = rows
        assert sum(r["net_close"] for r in rows) == nets[i], (kind, y)
    return out


# ------------------------------------------------------------------------------------------------ stato patrimoniale
DIVIDENDS = {2023: 40000, 2024: 60000, 2025: 80000}      # utili dell'esercizio precedente distribuiti nell'anno
EXTRA_RESERVE_2022 = 122000
TFR_FUND = {y: round(cost_total(y, "9c") * 3.4) for y in ALL_YEARS}
LOAN_BALANCE = {2022: 210000, 2023: 165000, 2024: 120000, 2025: 75000}
LOAN_REPAYMENT = {2023: 45000, 2024: 45000, 2025: 45000}
PREPAID = (5200, 6800, 8400, 9900)
ACCRUED = (3900, 4200, 4800, 5300)
TAX_CREDITS = {y: 24000 + (y - 2022) * 6000 for y in ALL_YEARS}
DEPOSITS = 8500
OTHER_RECEIVABLES = (2600, 3100, 3500, 4200)


def balance(y: int) -> Dict[str, int]:
    """Stato patrimoniale al 31/12 dell'esercizio ``y``; le disponibilità liquide chiudono il bilancio e sono controllate dal rendiconto."""
    i = _i(y)
    p = pl(y)
    intang, tang = NET_INTANG[i], NET_TANG[i]
    trade = round(REVENUE[i] * 0.27)
    wip = WIP[i]
    tax_cr, other_cr, prepaid = TAX_CREDITS[y], OTHER_RECEIVABLES[i], PREPAID[i]
    # patrimonio netto
    reserve = EXTRA_RESERVE_2022
    for yy in range(2023, y + 1):
        reserve = reserve + pl(yy - 1)["net"] - DIVIDENDS[yy]
    pn_parts = {"capital": COMPANY["capital"], "legal": 10000, "extra": reserve, "net": p["net"]}
    pn = sum(pn_parts.values())
    tfr = TFR_FUND[y]
    loan = LOAN_BALANCE[y]
    loan_short = 45000 if loan >= 45000 else loan
    suppliers = round(cost_total(y, "7") * 0.16)
    withheld = round(cost_total(y, "9a") * 0.0455)                  # ritenute su redditi di lavoro dipendente e autonomo versate a gennaio
    vat_due = round(REVENUE[i] * 0.011)
    ires_due = round(p["ires"] * 0.32)
    irap_due = round(p["irap"] * 0.28)
    tax_debt = withheld + vat_due + ires_due + irap_due
    social = round(cost_total(y, "9b") / 11)
    employees_debt = round(cost_total(y, "9a") / 13)
    holidays = round(cost_total(y, "9a") * 0.03)
    other_debt = employees_debt + holidays
    accrued = ACCRUED[i]
    liabilities = pn + tfr + loan + suppliers + tax_debt + social + other_debt + accrued
    non_cash = intang + tang + DEPOSITS + trade + wip + tax_cr + other_cr + prepaid
    cash = liabilities - non_cash
    cash_bank = cash - round(cash * 0.0009)
    cash_cash = cash - cash_bank
    return {"intang": intang, "tang": tang, "deposits": DEPOSITS, "fixed": intang + tang + DEPOSITS, "wip": wip, "trade": trade, "tax_cr": tax_cr, "other_cr": other_cr,
            "receivables": trade + tax_cr + other_cr, "cash_bank": cash_bank, "cash_cash": cash_cash, "cash": cash, "current": wip + trade + tax_cr + other_cr + cash, "prepaid": prepaid,
            "assets": non_cash + cash, **{f"pn_{k}": v for k, v in pn_parts.items()}, "pn": pn, "tfr": tfr, "loan": loan, "loan_short": loan_short, "loan_long": loan - loan_short,
            "suppliers": suppliers, "withheld": withheld, "vat_due": vat_due, "ires_due": ires_due, "irap_due": irap_due, "tax_debt": tax_debt, "social": social,
            "employees_debt": employees_debt, "holidays": holidays, "other_debt": other_debt, "debts": loan + suppliers + tax_debt + social + other_debt, "accrued": accrued,
            "liabilities": liabilities, "trade_invoices_to_issue": round(trade * 0.06)}


def cash_flow(y: int) -> Dict[str, int]:
    """Rendiconto finanziario, metodo indiretto: parte dall'utile e riconcilia la variazione delle disponibilità liquide."""
    b, b0, p = balance(y), balance(y - 1), pl(y)
    dep = p["b10a"] + p["b10b"]
    net_interest = p["int_expense"] - p["int_income"] - p["fx"]
    a = {"net": p["net"], "taxes": p["taxes"], "interest": net_interest}
    a["pre"] = a["net"] + a["taxes"] + a["interest"]
    a["provisions"] = p["b9c"] + p["b10d"]
    a["dep"] = dep
    a["before_wc"] = a["pre"] + a["provisions"] + a["dep"]
    a["d_wip"] = -(b["wip"] - b0["wip"])
    a["d_trade"] = -(b["trade"] - b0["trade"]) - p["b10d"]                  # il credito è esposto al netto della svalutazione: la perdita non è un incasso mancato
    a["d_suppliers"] = b["suppliers"] - b0["suppliers"]
    a["d_prepaid"] = -(b["prepaid"] - b0["prepaid"])
    a["d_accrued"] = b["accrued"] - b0["accrued"]
    a["d_other"] = ((b["withheld"] + b["vat_due"]) - (b0["withheld"] + b0["vat_due"])) + (b["social"] - b0["social"]) + (b["other_debt"] - b0["other_debt"])         - (b["tax_cr"] - b0["tax_cr"]) - (b["other_cr"] - b0["other_cr"])
    a["wc"] = a["d_wip"] + a["d_trade"] + a["d_suppliers"] + a["d_prepaid"] + a["d_accrued"] + a["d_other"]
    a["after_wc"] = a["before_wc"] + a["wc"]
    a["interest_paid"] = -net_interest
    a["taxes_paid"] = -p["taxes"] + ((b["ires_due"] + b["irap_due"]) - (b0["ires_due"] + b0["irap_due"]))
    tfr_used = b0["tfr"] + p["b9c"] - b["tfr"]
    a["tfr_used"] = -tfr_used
    a["operating"] = a["after_wc"] + a["interest_paid"] + a["taxes_paid"] + a["tfr_used"]
    a["capex_intang"] = -sum(r["capex"] for r in fixed_assets("intang")[y])
    a["capex_tang"] = -sum(r["capex"] for r in fixed_assets("tang")[y])
    a["deposits"] = -(b["deposits"] - b0["deposits"])
    a["investing"] = a["capex_intang"] + a["capex_tang"] + a["deposits"]
    a["loan"] = b["loan"] - b0["loan"]
    a["dividends"] = -DIVIDENDS.get(y, 0)
    a["financing"] = a["loan"] + a["dividends"]
    a["change"] = a["operating"] + a["investing"] + a["financing"]
    a["open"], a["close"] = b0["cash"], b["cash"]
    return a


# ------------------------------------------------------------------------------------------------ elementi per i documenti
def ratio_notes(y: int) -> Dict[str, float]:
    p, b = pl(y), balance(y)
    return {"ebitda": p["ebit"] + p["b10a"] + p["b10b"] + p["b10d"], "roe": p["net"] / max(1, b["pn"] - p["net"]), "roi": p["ebit"] / b["assets"], "ros": p["ebit"] / p["revenue"],
            "current_ratio": b["current"] / max(1, b["debts"] - b["loan_long"]), "debt_equity": b["debts"] / b["pn"]}


def check() -> None:
    """Controlli di coerenza del modello: si eseguono prima di scrivere qualunque documento."""
    for y in ALL_YEARS:
        b, p = balance(y), pl(y)
        assert b["assets"] == b["liabilities"], y
        assert b["cash"] > 50000, (y, b["cash"])
        assert sum(REVENUE_SPLIT[k][1][_i(y)] for k in range(len(REVENUE_SPLIT))) == 100
        assert p["a_total"] - p["b_total"] == p["ebit"]
        assert sum(HEADCOUNT_SPLIT[y]) == EMPLOYEES[y]
    for y in YEARS:
        cf = cash_flow(y)
        assert cf["close"] - cf["open"] == cf["change"], (y, cf["close"] - cf["open"], cf["change"])


check()
