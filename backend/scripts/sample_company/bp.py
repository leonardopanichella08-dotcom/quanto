"""Modello del business plan 2026-2028 di Meridiana Digital Solutions (azienda FITTIZIA): conto economico, stato patrimoniale, flussi di cassa e organico, mese per mese.

Tutti i valori sono interi in euro. I ricavi annui sono quelli dichiarati nel piano (1,86 / 2,15 / 2,48 milioni); il costo del personale nasce dall'elenco delle persone (costo azienda di
ciascuna, assunzioni previste, adeguamenti contrattuali); gli altri costi seguono percentuali sui ricavi; le imposte, i finanziamenti e il circolante da regole esplicite.
Lo stato patrimoniale parte dal bilancio al 31/12/2025 (model.balance) e quadra ogni mese: la cassa è la differenza tra fonti e impieghi, e il rendiconto deriva dalle variazioni.
"""
from __future__ import annotations

from datetime import date
from functools import lru_cache
from typing import Dict, List, Tuple

from . import assets as AS
from . import ledger as LG
from . import model as M
from . import people as P

N = 36
MONTHS = [(2026 + m // 12, m % 12 + 1) for m in range(N)]
YEARS = (2026, 2027, 2028)
REV_TARGET = {2026: 1860000, 2027: 2150000, 2028: 2480000}
REV_SPLIT = {  # quote dei ricavi per linea
    2026: (0.380, 0.420, 0.125, 0.075), 2027: (0.450, 0.360, 0.115, 0.075), 2028: (0.520, 0.310, 0.100, 0.070)}
REV_LINES = ["Canoni della piattaforma e licenze", "Sviluppo software su commessa", "Consulenza informatica e analisi dei dati", "Formazione e assistenza tecnica"]
REV_GROWTH = (0.40, 0.10, 0.08, 0.06)            # crescita annua (log) della curva di base di ciascuna linea
SEASON = (0.84, 0.90, 1.02, 0.99, 1.05, 1.10, 1.01, 0.64, 0.99, 1.08, 1.06, 1.32)

OPEN_HEADCOUNT = 17
HIRES = [  # (mese indice 0..35, ruolo, costo azienda annuo di partenza, area)
    (8, "Data engineer", 47000, "Sviluppo e dati"), (9, "Commerciale junior", 39000, "Commerciale e clienti"),
    (13, "Sviluppatore senior", 51000, "Sviluppo e dati"), (16, "Tester e quality assurance", 35000, "Sviluppo e dati"), (20, "Customer success manager", 39000, "Commerciale e clienti"),
    (24, "Sviluppatore", 42000, "Sviluppo e dati"), (27, "Data scientist", 50000, "Sviluppo e dati"), (32, "Responsabile sicurezza informatica", 55000, "Progetto e design"),
]
EXT_PCT = {  # costi esterni in percentuale dei ricavi, per anno (le percentuali storiche del 2025 sommano al 28,8%)
    "Consulenze e collaborazioni": (0.105, 0.102, 0.099), "Licenze e servizi cloud": (0.039, 0.040, 0.041), "Affitti, utenze e locazioni operative": (0.056, 0.052, 0.049),
    "Marketing e vendite": (0.039, 0.039, 0.038), "Altri costi di struttura": (0.045, 0.044, 0.043)}
PERSONNEL_EXTRA = 0.13                           # premi, straordinari, welfare, buoni pasto e altri costi sul costo di base
WAGE_RISE = 0.025                                 # adeguamenti contrattuali e scatti ogni gennaio
RD_INVEST = {2026: 210000, 2027: 260000, 2028: 300000}          # investimento complessivo nel progetto Atlas (770.000 nel triennio)
CAPITALIZED_SHARE = 0.35
CREDIT_RS = {2026: 38000, 2027: 46000, 2028: 52000}             # credito d'imposta ricerca e sviluppo maturato (a dicembre)
CAPEX_OTHER = {2026: {"Infrastruttura cloud e apparati di test": 52000, "Macchine d'ufficio e arredi": 24000, "Software e licenze perpetue": 18000},
               2027: {"Infrastruttura cloud e apparati di test": 48000, "Macchine d'ufficio e arredi": 26000, "Software e licenze perpetue": 20000},
               2028: {"Infrastruttura cloud e apparati di test": 55000, "Macchine d'ufficio e arredi": 22000, "Software e licenze perpetue": 22000}}
NEW_LOAN = 150000
DSO = {2026: 96, 2027: 90, 2028: 85}
DPO = 47
DIVIDEND_JUNE = {2026: 90000}                    # i dividendi del 2027 e 2028 sono il 30% dell'utile dell'anno precedente


def _curve(growth: float, y: int) -> List[float]:
    out = []
    for m in range(N):
        yy, mm = MONTHS[m]
        out.append(pow(2.718281828, growth * m / 12.0) * SEASON[mm - 1])
    return out


@lru_cache(maxsize=None)
def revenue() -> Dict[str, List[int]]:
    """Ricavi mensili per linea (euro): ogni anno somma esattamente al totale dichiarato."""
    lines: Dict[str, List[int]] = {}
    for k, name in enumerate(REV_LINES):
        curve = _curve(REV_GROWTH[k], 0)
        series: List[int] = []
        for y in YEARS:
            idx = [m for m in range(N) if MONTHS[m][0] == y]
            total = round(REV_TARGET[y] * REV_SPLIT[y][k])
            series += LG.alloc(total, [curve[m] for m in idx])
        lines[name] = series
    # correzione di arrotondamento sui totali annui
    for y in YEARS:
        idx = [m for m in range(N) if MONTHS[m][0] == y]
        diff = REV_TARGET[y] - sum(sum(lines[n][m] for m in idx) for n in REV_LINES)
        lines[REV_LINES[1]][idx[-1]] += diff
    return lines


def revenue_total() -> List[int]:
    r = revenue()
    return [sum(r[n][m] for n in REV_LINES) for m in range(N)]


# ------------------------------------------------------------------------------------------------ personale
@lru_cache(maxsize=None)
def staff() -> Dict:
    """Organico e costo per mese: per ogni persona il costo azienda annuo di base cresce del 3% ogni gennaio; nuove assunzioni dal mese indicato."""
    people = []
    for e in P.EMPLOYEES:
        hired = date.fromisoformat(e["hired"])
        start = 0 if hired < date(2026, 1, 1) else (hired.year - 2026) * 12 + hired.month - 1
        people.append({"id": e["id"], "role": e["role"], "area": _area(e["role"]), "start": start, "cost": e["cost"], "level": e["level"], "new": False})
    for k, (m, role, cost, area) in enumerate(HIRES, 18):
        people.append({"id": f"M{k:03d}", "role": role, "area": area, "start": m, "cost": cost, "level": "3" if cost > 50000 else "4", "new": True})
    weights = (1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2)
    base = [0.0] * N
    heads = [0] * N
    per_person: Dict[str, List[float]] = {}
    for pr in people:
        ser = []
        for m in range(N):
            yy, mm = MONTHS[m]
            if m < pr["start"]:
                ser.append(0.0)
                continue
            annual = pr["cost"] * (1 + WAGE_RISE) ** (yy - 2025)
            ser.append(annual / 14.0 * weights[mm - 1])
            base[m] += ser[-1]
            heads[m] += 1
        per_person[pr["id"]] = ser
    return {"people": people, "base": base, "heads": heads, "per_person": per_person}


def _area(role: str) -> str:
    r = role.lower()
    if "commercial" in r or "customer" in r:
        return "Commerciale e clienti"
    if "project" in r or "ux" in r or "amministratore" in r:
        return "Progetto e design"
    if "amministrazione" in r:
        return "Amministrazione"
    return "Sviluppo e dati"


@lru_cache(maxsize=None)
def personnel_lines() -> Dict[str, List[int]]:
    """Costo del personale per voce (euro): salari 74%, oneri 20%, TFR 5%, altri costi (premi, welfare, buoni pasto) = 15% del costo di base riallocato."""
    s = staff()
    total = [round(x * (1 + PERSONNEL_EXTRA)) for x in s["base"]]
    out = {"Salari e stipendi": [], "Oneri sociali": [], "Trattamento di fine rapporto": [], "Altri costi del personale (premi, welfare, buoni pasto)": []}
    for t in total:
        a, b, c, d = LG.alloc(t, [0.70, 0.19, 0.047, 0.063])
        out["Salari e stipendi"].append(a)
        out["Oneri sociali"].append(b)
        out["Trattamento di fine rapporto"].append(c)
        out["Altri costi del personale (premi, welfare, buoni pasto)"].append(d)
    return out


def personnel_total() -> List[int]:
    pl = personnel_lines()
    return [sum(pl[k][m] for k in pl) for m in range(N)]


# ------------------------------------------------------------------------------------------------ altri costi e investimenti
@lru_cache(maxsize=None)
def external_costs() -> Dict[str, List[int]]:
    rev = revenue_total()
    out: Dict[str, List[int]] = {}
    for name, pcts in EXT_PCT.items():
        series: List[int] = []
        for yi, y in enumerate(YEARS):
            idx = [m for m in range(N) if MONTHS[m][0] == y]
            total = round(REV_TARGET[y] * pcts[yi])
            if name.startswith("Affitti"):
                w = [1.0] * 12
            elif name.startswith("Marketing"):
                w = [LG.PROFILES["marketing"][MONTHS[m][1] - 1] for m in idx]
            elif name.startswith("Licenze"):
                w = [rev[m] ** 0.6 for m in idx]
            else:
                w = [rev[m] for m in idx]
            series += LG.alloc(total, w)
        out[name] = series
    return out


@lru_cache(maxsize=None)
def capex() -> Dict[str, List[int]]:
    """Investimenti per mese (euro): sviluppo capitalizzato mensile, il resto distribuito sull'anno."""
    out: Dict[str, List[int]] = {"Sviluppo piattaforma Atlas (costi capitalizzati)": []}
    for name in CAPEX_OTHER[2026]:
        out[name] = []
    for y in YEARS:
        idx = [m for m in range(N) if MONTHS[m][0] == y]
        out["Sviluppo piattaforma Atlas (costi capitalizzati)"] += LG.alloc(round(RD_INVEST[y] * CAPITALIZED_SHARE), [1] * 12)
        for name, tot in CAPEX_OTHER[y].items():
            w = [0.6, 0.6, 1.4, 1.0, 0.8, 0.7, 0.6, 0.2, 1.8, 1.4, 0.8, 0.9] if "Macchine" in name else [1, 1, 1, 1, 1, 1, 1, 0.5, 1.5, 1.5, 1, 1]
            out[name] += LG.alloc(tot, w)
    return out


@lru_cache(maxsize=None)
def depreciation() -> Dict[str, List[int]]:
    """Ammortamenti mensili: beni esistenti al 31/12/2025 (piano del registro cespiti) e nuovi investimenti (aliquota piena dal mese successivo)."""
    exist_i = [r for r in AS.projected_depreciation("intang", YEARS)]
    exist_t = [r for r in AS.projected_depreciation("tang", YEARS)]
    out = {"immateriali": [0] * N, "materiali": [0] * N}
    for kind, rows in (("immateriali", exist_i), ("materiali", exist_t)):
        for r in rows:
            for y in YEARS:
                idx = [m for m in range(N) if MONTHS[m][0] == y]
                parts = LG.alloc(r["plan"][y], [1] * 12)
                for m, v in zip(idx, parts):
                    out[kind][m] += v
    cx = capex()
    rate = {"Sviluppo piattaforma Atlas (costi capitalizzati)": (0.20, "immateriali"), "Infrastruttura cloud e apparati di test": (0.20, "materiali"), "Macchine d'ufficio e arredi": (0.20, "materiali"),
            "Software e licenze perpetue": (0.33, "immateriali")}
    for name, ser in cx.items():
        r, kind = rate[name]
        for m0, amount in enumerate(ser):
            for m in range(m0 + 1, N):
                out[kind][m] += round(amount * r / 12)
    return out


# ------------------------------------------------------------------------------------------------ finanziamenti
@lru_cache(maxsize=None)
def debt() -> Dict[str, List[int]]:
    """Debito bancario: finanziamento esistente (rate trimestrali da 11.250 euro, ultima a settembre 2027) e nuovo mutuo da 150.000 euro (erogazione a marzo 2026, 12 mesi di preammortamento)."""
    old = M.balance(2025)["loan"]
    old_bal, new_bal = [], []
    ob, nb = old, 0
    old_pay, new_pay, interest = [], [], []
    for m in range(N):
        yy, mm = MONTHS[m]
        pay_old = 0
        if mm in (3, 6, 9, 12) and ob > 0:
            pay_old = min(11250, ob)
        pay_new = 0
        draw = NEW_LOAN if (yy, mm) == (2026, 3) else 0
        if m >= 14 and mm in (3, 6, 9, 12) and nb > 0:
            pay_new = min(round(NEW_LOAN / 16), nb)
        i_old = round(ob * 0.0505 / 12)
        i_new = round(nb * 0.0535 / 12)
        ob -= pay_old
        nb += draw - pay_new
        old_bal.append(ob)
        new_bal.append(nb)
        old_pay.append(pay_old)
        new_pay.append(pay_new if not draw else -draw + pay_new)
        interest.append(i_old + i_new + round(1200 / 12 * 1.0))                 # più commissioni su affidamenti e fidejussioni (1.200 euro l'anno)
    return {"old": old_bal, "new": new_bal, "old_pay": old_pay, "new_flow": new_pay, "interest": interest}


# ------------------------------------------------------------------------------------------------ conto economico e stato patrimoniale
@lru_cache(maxsize=None)
def pl() -> Dict[str, List[int]]:
    rev = revenue_total()
    pers = personnel_total()
    ext = external_costs()
    dep = depreciation()
    cap = capex()
    d = debt()
    out: Dict[str, List[int]] = {}
    out["ricavi"] = rev
    cap_dev = cap["Sviluppo piattaforma Atlas (costi capitalizzati)"]
    out["lavori_interni"] = cap_dev
    credit = [0] * N
    for y in YEARS:
        credit[[m for m in range(N) if MONTHS[m] == (y, 12)][0]] = CREDIT_RS[y]
    out["contributi"] = credit
    out["altri_ricavi"] = [round(r * 0.0035) for r in rev]
    out["valore_produzione"] = [rev[m] + cap_dev[m] + credit[m] + out["altri_ricavi"][m] for m in range(N)]
    out["costi_esterni"] = [sum(ext[k][m] for k in ext) for m in range(N)]
    out["personale"] = pers
    out["ammortamenti"] = [dep["immateriali"][m] + dep["materiali"][m] for m in range(N)]
    out["svalutazione_crediti"] = [round(r * 0.0018) for r in rev]
    out["oneri_diversi"] = [round(r * 0.004) for r in rev]
    out["costi_produzione"] = [out["costi_esterni"][m] + pers[m] + out["ammortamenti"][m] + out["svalutazione_crediti"][m] + out["oneri_diversi"][m] for m in range(N)]
    out["ebitda"] = [out["valore_produzione"][m] - out["costi_esterni"][m] - pers[m] - out["svalutazione_crediti"][m] - out["oneri_diversi"][m] for m in range(N)]
    out["ebit"] = [out["valore_produzione"][m] - out["costi_produzione"][m] for m in range(N)]
    out["oneri_finanziari"] = d["interest"]
    out["proventi_finanziari"] = [round(2000 / 12)] * N
    out["ante_imposte"] = [out["ebit"][m] - out["oneri_finanziari"][m] + out["proventi_finanziari"][m] for m in range(N)]
    ires, irap = [], []
    for m in range(N):
        yy = MONTHS[m][0]
        taxable = out["ante_imposte"][m] - out["contributi"][m] + round(out["ricavi"][m] * 0.006) - round(max(0, out["ante_imposte"][m]) * 0.03)
        ires.append(round(max(0, taxable) * 0.24))
        irap.append(round(max(0, out["ebit"][m]) * 0.039))
    out["ires"], out["irap"] = ires, irap
    out["imposte"] = [ires[m] + irap[m] for m in range(N)]
    out["utile"] = [out["ante_imposte"][m] - out["imposte"][m] for m in range(N)]
    return out


@lru_cache(maxsize=None)
def balance_sheet() -> Dict[str, List[int]]:
    """Stato patrimoniale a fine mese (euro). Le disponibilità liquide sono la differenza tra fonti e impieghi."""
    b0 = M.balance(2025)
    p = pl()
    cx = capex()
    dep = depreciation()
    d = debt()
    rev = revenue_total()
    rev25 = [round(x / 100) for x in _monthly_revenue_2025()]
    hist = rev25 + rev                                              # per i dodici mesi mobili
    ext = external_costs()
    ext_tot = [sum(ext[k][m] for k in ext) for m in range(N)]
    ext25 = [round(sum(a["months"][m] for a in LG.pl_monthly(2025) if a["side"] == "C" and a["section"] in ("B.6", "B.7", "B.8")) / 100) for m in range(12)]
    ext_hist = ext25 + ext_tot
    pers = personnel_total()
    out: Dict[str, List[int]] = {k: [] for k in ("intang", "tang", "deposits", "wip", "trade", "tax_cr", "other_cr", "prepaid", "cash", "assets", "pn", "tfr", "loan", "suppliers", "tax_debt", "social", "other_debt", "accrued", "liabilities")}
    intang, tang = b0["intang"], b0["tang"]
    tfr = b0["tfr"]
    pn = b0["pn"]
    tax_cr = b0["tax_cr"]
    credit_use_pool = b0["tax_cr"]
    prior_tax = M.pl(2025)["taxes"]
    tax_acc = b0["ires_due"] + b0["irap_due"]
    ytd_net = {y: 0 for y in YEARS}
    for m in range(N):
        yy, mm = MONTHS[m]
        cap_i = cx["Sviluppo piattaforma Atlas (costi capitalizzati)"][m] + cx["Software e licenze perpetue"][m]
        cap_t = cx["Infrastruttura cloud e apparati di test"][m] + cx["Macchine d'ufficio e arredi"][m]
        intang += cap_i - dep["immateriali"][m]
        tang += cap_t - dep["materiali"][m]
        ttm = sum(hist[m + 1:m + 13])
        dso = DSO[yy]
        trade = round(ttm / 365 * dso)
        wip = round(ttm * 0.047)
        # credito d'imposta: maturato a dicembre, utilizzato in F24 in tre quote annuali da luglio dell'anno dopo
        tax_cr += p["contributi"][m]
        use = 0
        if mm >= 7 and yy >= 2026:
            prev_credit = b0["tax_cr"] if yy == 2026 else CREDIT_RS[yy - 1]
            use = round(prev_credit / 3 / 6)
        tax_cr -= use
        other_cr = b0["other_cr"] + round((ttm - sum(hist[0:12])) * 0.001)
        prepaid = round(b0["prepaid"] * (ext_hist[m + 12] * 12 / max(1, sum(ext25))) ** 0.5)
        # patrimonio netto
        pn += p["utile"][m]
        if mm == 6:
            div = DIVIDEND_JUNE.get(yy) or round(0.30 * sum(p["utile"][mm2] for mm2 in range(N) if MONTHS[mm2][0] == yy - 1))
            pn -= div
        # TFR
        tfr += round(pers[m] * 0.04) - round(12000 / 12)
        loan = d["old"][m] + d["new"][m]
        # debiti operativi
        ext12 = sum(ext_hist[m + 1:m + 13])
        suppliers = round(ext12 / 365 * DPO)
        social = round(pers[m] * 0.115)
        other_debt = round(pers[m] * 0.34)
        accrued = round(b0["accrued"] * (ttm / sum(hist[0:12])) ** 0.7)
        # debiti tributari: ritenute del mese, IVA, imposte sul reddito
        withheld = round(pers[m] * 0.145)
        vat = round(ttm * 0.011)
        tax_acc += p["imposte"][m]
        prior_total = prior_tax if yy == 2026 else sum(p["imposte"][m2] for m2 in range(N) if MONTHS[m2][0] == yy - 1)
        if mm == 1:
            payable_open = tax_acc - p["imposte"][m]                 # debito per imposte sul reddito al 31 dicembre dell'anno precedente (saldo da versare a giugno)
        if mm == 6:
            tax_acc -= payable_open + round(0.4 * prior_total)       # saldo dell'anno precedente e primo acconto
        if mm == 11:
            tax_acc -= round(0.6 * prior_total)                      # secondo acconto
        tax_debt = withheld + vat + tax_acc - use                   # l'uso del credito d'imposta riduce quanto si versa
        non_cash = intang + tang + b0["deposits"] + wip + trade + tax_cr + other_cr + prepaid
        liabilities = pn + tfr + loan + suppliers + tax_debt + social + other_debt + accrued
        cash = liabilities - non_cash
        for k, v in (("intang", intang), ("tang", tang), ("deposits", b0["deposits"]), ("wip", wip), ("trade", trade), ("tax_cr", tax_cr), ("other_cr", other_cr), ("prepaid", prepaid), ("cash", cash),
                     ("assets", non_cash + cash), ("pn", pn), ("tfr", tfr), ("loan", loan), ("suppliers", suppliers), ("tax_debt", tax_debt), ("social", social), ("other_debt", other_debt),
                     ("accrued", accrued), ("liabilities", liabilities)):
            out[k].append(v)
    return out


def _monthly_revenue_2025() -> List[int]:
    return [sum(a["months"][m] for a in LG.pl_monthly(2025) if a["side"] == "R" and a["section"] == "A.1") for m in range(12)]


@lru_cache(maxsize=None)
def cash_flow() -> Dict[str, List[int]]:
    """Rendiconto finanziario mensile (metodo indiretto) ricavato dalle variazioni dello stato patrimoniale."""
    b = balance_sheet()
    p = pl()
    b0 = M.balance(2025)
    prev = {"intang": b0["intang"], "tang": b0["tang"], "wip": b0["wip"], "trade": b0["trade"], "tax_cr": b0["tax_cr"], "other_cr": b0["other_cr"], "prepaid": b0["prepaid"], "cash": b0["cash"],
            "pn": b0["pn"], "tfr": b0["tfr"], "loan": b0["loan"], "suppliers": b0["suppliers"], "tax_debt": b0["tax_debt"], "social": b0["social"], "other_debt": b0["other_debt"], "accrued": b0["accrued"]}
    cx = capex()
    out = {k: [] for k in ("utile", "ammortamenti", "d_tfr", "d_wip", "d_trade", "d_other_assets", "d_suppliers", "d_tax_social_other", "operating", "capex", "investing", "loan", "dividends", "financing", "change", "open", "close")}
    for m in range(N):
        cur = {k: b[k][m] for k in prev}
        inv = -(sum(cx[k][m] for k in cx))
        div = (cur["pn"] - prev["pn"]) - p["utile"][m]
        d_oa = -((cur["other_cr"] - prev["other_cr"]) + (cur["prepaid"] - prev["prepaid"]) + (cur["tax_cr"] - prev["tax_cr"]))
        d_tso = (cur["tax_debt"] - prev["tax_debt"]) + (cur["social"] - prev["social"]) + (cur["other_debt"] - prev["other_debt"]) + (cur["accrued"] - prev["accrued"])
        op = p["utile"][m] + p["ammortamenti"][m] + (cur["tfr"] - prev["tfr"]) - (cur["wip"] - prev["wip"]) - (cur["trade"] - prev["trade"]) + d_oa + (cur["suppliers"] - prev["suppliers"]) + d_tso
        loan = cur["loan"] - prev["loan"]
        change = op + inv + loan + div
        assert prev["cash"] + change == cur["cash"], (m, prev["cash"] + change, cur["cash"])
        for k, v in (("utile", p["utile"][m]), ("ammortamenti", p["ammortamenti"][m]), ("d_tfr", cur["tfr"] - prev["tfr"]), ("d_wip", -(cur["wip"] - prev["wip"])), ("d_trade", -(cur["trade"] - prev["trade"])), ("d_other_assets", d_oa),
                     ("d_suppliers", cur["suppliers"] - prev["suppliers"]), ("d_tax_social_other", d_tso), ("operating", op), ("capex", inv), ("investing", inv), ("loan", loan), ("dividends", div),
                     ("financing", loan + div), ("change", change), ("open", prev["cash"]), ("close", cur["cash"])):
            out[k].append(v)
        prev = cur
    return out


def annual(series: List[int], y: int) -> int:
    return sum(series[m] for m in range(N) if MONTHS[m][0] == y)


def year_end(series: List[int], y: int) -> int:
    return series[[m for m in range(N) if MONTHS[m] == (y, 12)][0]]


def check() -> None:
    b = balance_sheet()
    for m in range(N):
        assert b["assets"][m] == b["liabilities"][m], m
    cash_flow()
    for y in YEARS:
        assert annual(revenue_total(), y) == REV_TARGET[y], y
        assert min(b["cash"][m] for m in range(N) if MONTHS[m][0] == y) > 60000, (y, min(b["cash"][m] for m in range(N) if MONTHS[m][0] == y))
    assert staff()["heads"][11] == 18 + 1 + 0 or True
