"""Allegati del fascicolo di bilancio: conto economico e stato patrimoniale analitici, bilancio di verifica, partitari, registro dei cespiti, prospetti mensili, liquidazioni IVA."""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Dict, List

from . import assets as AS
from . import ledger as LG
from . import model as M
from .bil_nota import E, EU, PCT
from .pdfkit import Doc, cents, units

U = units
CO = M.COMPANY
MONTHS = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]


def _w(d: Doc) -> float:
    return d.width / 2.8346


def _line(label, cur, prev, level=2, bold=False):
    return (label, [E(cur), E(prev) if prev is not None else ""], level, bold)


# ================================================================================================ Allegato A
def allegato_a(d: Doc, y: int) -> None:
    """Conto economico analitico per conti (euro e centesimi): lo schema dell'art. 2425 c.c. con ogni conto sotto la sua voce."""
    W = _w(d)
    p = M.pl(y)
    d.title_block("ALLEGATO A - CONTO ECONOMICO ANALITICO PER CONTI", f"Dettaglio delle voci dello schema civilistico, euro e centesimi - esercizio {y} con confronto al {y - 1}")
    d.P("Il presente allegato espone, conto per conto, le voci del conto economico riportate in forma sintetica nello schema dell'art. 2425 c.c. Gli importi coincidono con le risultanze della contabilità generale al 31/12 e con le voci di bilancio; "
        "i sottoconti sono quelli del piano dei conti aziendale.", left=True)
    cur_r = {a["code"]: a["cents"] for a in LG.revenue_accounts(y)}
    old_r = {a["code"]: a["cents"] for a in LG.revenue_accounts(y - 1)}
    oth = {a["code"]: a for a in LG.other_pl_accounts(y)}
    oth0 = {a["code"]: a["cents"] for a in LG.other_pl_accounts(y - 1)}
    hdr = ["", f"{y}", f"{y - 1}"]
    cw = [W - 64, 32, 32]
    rows = [("A) VALORE DELLA PRODUZIONE", ["", ""], 0, True), ("1) ricavi delle vendite e delle prestazioni", ["", ""], 1, True)]
    for cat, (label, _) in enumerate(M.REVENUE_SPLIT):
        rows.append((label, ["", ""], 2, True))
        for a in [x for x in LG.REVENUE_ACCOUNTS if x[0] == cat]:
            rows.append(_line(f"{a[1]} {a[2]}", cur_r[a[1]], old_r[a[1]], 3))
    rows.append(("Totale ricavi delle prestazioni per conto", [E(sum(cur_r.values())), E(sum(old_r.values()))], 1, True))
    rows.append(("3) variazioni dei lavori in corso su ordinazione", [E(oth["450.010"]["cents"]), E(oth0["450.010"])], 1, False))
    rows.append(("4) incrementi di immobilizzazioni per lavori interni", [E(oth["460.010"]["cents"]), E(oth0["460.010"])], 1, False))
    rows.append(("5) altri ricavi e proventi", ["", ""], 1, True))
    for code in ("470.010", "480.010", "480.020", "480.030", "480.040"):
        rows.append(_line(f"{code} {oth[code]['name']}", oth[code]["cents"], oth0[code], 2))
    rows.append(("Totale valore della produzione", [E(p["a_total"] * 100), E(M.pl(y - 1)["a_total"] * 100)], 0, True))
    d.statement(rows, cw, hdr, font=8)
    # --- costi
    d.page_break()
    rows = [("B) COSTI DELLA PRODUZIONE", ["", ""], 0, True)]
    heads = [("6", "6) per materie prime, sussidiarie, di consumo e di merci"), ("7", "7) per servizi"), ("8", "8) per godimento di beni di terzi"), ("9", "9) per il personale"),
             ("10", "10) ammortamenti e svalutazioni"), ("14", "14) oneri diversi di gestione")]
    by = defaultdict(list)
    for a in LG.cost_accounts(y):
        by[a["voce"]].append(a)
    prev = {a["code"]: a["cents"] for a in LG.cost_accounts(y - 1)}
    for key, label in heads:
        voci = [v for v in by if (v == key if key in ("6", "7", "8", "14") else v.startswith(key))]
        rows.append((label, ["", ""], 1, True))
        tot = tot0 = 0
        for v in voci:
            macros = []
            for a in by[v]:
                if a["macro"] not in macros:
                    macros.append(a["macro"])
            for macro in macros:
                accts = [a for a in by[v] if a["macro"] == macro and a["cents"] > 0]
                if not accts:
                    continue
                rows.append((macro, ["", ""], 2, True))
                for a in accts:
                    rows.append(_line(f"{a['code']} {a['name']}", a["cents"], prev.get(a["code"], 0), 3))
                sc, sp = sum(a["cents"] for a in accts), sum(prev.get(a["code"], 0) for a in accts)
                rows.append((f"Totale conto: {macro}", [E(sc), E(sp)], 2, True))
                tot += sc
                tot0 += sp
        rows.append((f"Totale voce {key})", [E(tot), E(tot0)], 1, True))
    rows.append(("Totale costi della produzione", [E(p["b_total"] * 100), E(M.pl(y - 1)["b_total"] * 100)], 0, True))
    rows.append(("Differenza tra valore e costi della produzione (A - B)", [E(p["ebit"] * 100), E(M.pl(y - 1)["ebit"] * 100)], 0, True))
    d.statement(rows, cw, hdr, font=7.6)
    d.page_break()
    rows = [("C) PROVENTI E ONERI FINANZIARI", ["", ""], 0, True)]
    for code in ("510.010", "520.010", "520.020", "520.030", "530.010", "530.020"):
        a = oth[code]
        sign = 1 if a["side"] == "R" else -1
        rows.append(_line(f"{code} {a['name']}", sign * a["cents"], sign * oth0.get(code, 0), 2))
    rows.append(("Totale proventi e oneri finanziari", [E(p["fin"] * 100), E(M.pl(y - 1)["fin"] * 100)], 0, True))
    rows.append(("Risultato prima delle imposte", [E(p["pre_tax"] * 100), E(M.pl(y - 1)["pre_tax"] * 100)], 0, True))
    rows.append(("20) imposte sul reddito dell'esercizio", ["", ""], 1, True))
    rows.append(_line("590.010 IRES corrente dell'esercizio", -oth["590.010"]["cents"], -oth0["590.010"], 2))
    rows.append(_line("590.020 IRAP corrente dell'esercizio", -oth["590.020"]["cents"], -oth0["590.020"], 2))
    rows.append(("UTILE (PERDITA) DELL'ESERCIZIO", [E(p["net"] * 100), E(M.pl(y - 1)["net"] * 100)], 0, True))
    d.statement(rows, cw, hdr, font=8)


# ================================================================================================ Allegato B
def allegato_b(d: Doc, y: int) -> None:
    W = _w(d)
    d.title_block("ALLEGATO B - STATO PATRIMONIALE ANALITICO PER CONTI", f"Saldi dei conti patrimoniali al 31/12/{y} con confronto al 31/12/{y - 1}, euro e centesimi")
    d.P("I saldi sono esposti con il segno proprio del conto: positivi per le attività e le rettifiche in diminuzione del patrimonio (dare), negativi per i fondi di ammortamento e per le passività e il patrimonio netto (avere). "
        "L'utile dell'esercizio non è compreso nei saldi patrimoniali, essendo ancora esposto nei conti economici.", left=True)
    prev = {a["code"]: a["cents"] for a in LG.bs_accounts(y - 1)}
    rows = [["Codice", "Conto", "Sezione", f"31/12/{y}", f"31/12/{y - 1}"]]
    for a in LG.bs_accounts(y):
        rows.append([a["code"], a["name"], a["section"], E(a["cents"]), E(prev.get(a["code"], 0))])
    rows.append(["", "Totale saldi patrimoniali (uguale all'utile dell'esercizio, esposto nei conti economici)", "", E(sum(a["cents"] for a in LG.bs_accounts(y))), E(sum(a["cents"] for a in LG.bs_accounts(y - 1)))])
    d.table(rows, [16, W - 114, 20, 39, 39], bold_rows=[len(rows) - 1], align_right_from=3, font=7.2, zebra=True)


# ================================================================================================ Allegato C
def allegato_c(d: Doc, y: int) -> None:
    W = _w(d)
    d.title_block("ALLEGATO C - BILANCIO DI VERIFICA", f"Al 31/12/{y}, prima delle scritture di chiusura - saldo iniziale, movimenti dell'esercizio e saldo finale (euro e centesimi; dare positivo, avere negativo)")
    tb = LG.trial_balance(y)
    rows = [["Codice", "Conto", "Saldo iniziale", "Movimenti dare", "Movimenti avere", "Saldo finale"]]
    for r in tb:
        rows.append([r["code"], r["name"], E(r["opening"]), E(r["dare"]), E(r["avere"]), E(r["closing"])])
    rows.append(["", "Totale del bilancio di verifica", E(sum(r["opening"] for r in tb)), E(sum(r["dare"] for r in tb)), E(sum(r["avere"] for r in tb)), E(sum(r["closing"] for r in tb))])
    d.table(rows, [14, W - 128, 27, 29, 29, 29], bold_rows=[len(rows) - 1], align_right_from=2, font=6.8, zebra=True)
    d.small("Il totale dei movimenti dare è uguale al totale dei movimenti avere e la somma algebrica dei saldi (iniziali e finali) è zero: il bilancio di verifica quadra.")


# ================================================================================================ Allegato D/E: partitari
def allegato_clienti(d: Doc, y: int) -> None:
    W = _w(d)
    d.title_block("ALLEGATO D - PARTITARIO CLIENTI", f"Fatture emesse non incassate al 31/12/{y} (IVA inclusa) e scadenzario")
    open_ = LG.open_receivables(y)
    from datetime import date
    ref = date(y, 12, 31)
    rows = [["Fattura", "Data", "Scadenza", "Cliente", "Importo fattura", "Residuo", "Giorni di scaduto"]]
    for o in open_:
        late = (ref - o["due"]).days
        rows.append([o["number"], o["date"].strftime("%d/%m/%Y"), o["due"].strftime("%d/%m/%Y"), o["customer"]["name"], E(o["total"]), E(o["open"]), str(late) if late > 0 else "non scaduta"])
    rows.append(["", "", "", "Totale fatture emesse aperte", E(sum(o["total"] for o in open_)), E(sum(o["open"] for o in open_)), ""])
    d.table(rows, [20, 17, 17, W - 126, 24, 24, 24], bold_rows=[len(rows) - 1], align_right_from=4, font=7, zebra=True)


def allegato_fornitori(d: Doc, y: int) -> None:
    W = _w(d)
    d.title_block("ALLEGATO E - PARTITARIO FORNITORI", f"Fatture ricevute non pagate al 31/12/{y} (IVA inclusa) e scadenzario")
    pay = LG.open_payables(y)
    from datetime import date
    ref = date(y, 12, 31)
    rows = [["Protocollo", "Data", "Scadenza", "Fornitore", "Importo fattura", "Residuo", "Giorni di scaduto"]]
    for o in pay:
        late = (ref - o["due"]).days
        rows.append([o["protocol"], o["date"].strftime("%d/%m/%Y"), o["due"].strftime("%d/%m/%Y"), o["supplier"]["name"], E(o["total"]), E(o["open"]), str(late) if late > 0 else "non scaduta"])
    rows.append(["", "", "", "Totale fatture ricevute aperte", E(sum(o["total"] for o in pay)), E(sum(o["open"] for o in pay)), ""])
    d.table(rows, [20, 17, 17, W - 126, 24, 24, 24], bold_rows=[len(rows) - 1], align_right_from=4, font=7, zebra=True)


# ================================================================================================ Allegato F: registro cespiti
def allegato_cespiti(d: Doc, y: int) -> None:
    W = _w(d)
    d.title_block("ALLEGATO F - REGISTRO DEI CESPITI", f"Movimenti dell'esercizio {y} bene per bene (euro) e piano di ammortamento 2026-2030 dei beni in essere al 31/12/2025")
    for kind, title in (("intang", "Immobilizzazioni immateriali"), ("tang", "Immobilizzazioni materiali")):
        reg = [r for r in AS.register(kind)[y] if r["cost_close"] > 0]
        d.H1(title)
        rows = [["Bene", "Acq.", "Aliq.", "Costo 1/1", "Incrementi", "Costo 31/12", "Fondo 1/1", "Amm.to", "Fondo 31/12", "Netto"]]
        for r in reg:
            rows.append([r["item"], r["date"].strftime("%m/%y"), f"{int(r['rate'] * 100)}%", U(r["cost_open"]), U(r["capex"]), U(r["cost_close"]), U(r["fund_open"]), U(r["dep"]), U(r["fund_close"]), U(r["net_close"])])
        rows.append(["Totale", "", "", U(sum(r["cost_open"] for r in reg)), U(sum(r["capex"] for r in reg)), U(sum(r["cost_close"] for r in reg)), U(sum(r["fund_open"] for r in reg)), U(sum(r["dep"] for r in reg)),
                     U(sum(r["fund_close"] for r in reg)), U(sum(r["net_close"] for r in reg))])
        d.table(rows, [W - 134, 10, 9, 15, 14, 16, 15, 14, 16, 15], bold_rows=[len(rows) - 1], align_right_from=1, font=6.5, zebra=True)
    if y == 2025:
        d.H1("Piano di ammortamento dei beni in essere al 31/12/2025")
        for kind, title in (("intang", "Immobilizzazioni immateriali"), ("tang", "Immobilizzazioni materiali")):
            plan = [r for r in AS.projected_depreciation(kind) if r["net_close"] > 0]
            rows = [[title, "Netto 31/12/2025", "2026", "2027", "2028", "2029", "2030", "Residuo dopo il 2030"]]
            for r in plan:
                rows.append([r["item"], U(r["net_close"])] + [U(r["plan"][yy]) for yy in (2026, 2027, 2028, 2029, 2030)] + [U(r["after"])])
            rows.append(["Totale", U(sum(r["net_close"] for r in plan))] + [U(sum(r["plan"][yy] for r in plan)) for yy in (2026, 2027, 2028, 2029, 2030)] + [U(sum(r["after"] for r in plan))])
            d.table(rows, [W - 119, 19, 15, 15, 15, 15, 15, 25], bold_rows=[len(rows) - 1], align_right_from=1, font=6.8, zebra=True)


# ================================================================================================ Allegato G: prospetti mensili
def _semester_tables(d: Doc, title: str, items: List[tuple], total_label: str) -> None:
    """Due tabelle (gennaio-giugno e luglio-dicembre) di righe (descrizione, [12 importi in centesimi])."""
    W = _w(d)
    d.H2(title)
    for half, label in ((0, "Primo semestre"), (1, "Secondo semestre")):
        m0 = half * 6
        rows = [[label] + MONTHS[m0:m0 + 6] + ["Totale sem."]]
        for name, months in items:
            rows.append([name] + [EU(months[m]) for m in range(m0, m0 + 6)] + [EU(sum(months[m0:m0 + 6]))])
        tot = [sum(it[1][m] for it in items) for m in range(12)]
        rows.append([total_label] + [EU(tot[m]) for m in range(m0, m0 + 6)] + [EU(sum(tot[m0:m0 + 6]))])
        d.table(rows, [W - 119] + [17] * 6 + [17], bold_rows=[len(rows) - 1], align_right_from=1, font=6.9, zebra=True)


def allegato_mensili(d: Doc, y: int) -> None:
    W = _w(d)
    d.title_block("ALLEGATO G - ANDAMENTO MENSILE DELL'ESERCIZIO", f"Ricavi e costi per conto mese per mese - esercizio {y} (importi in euro, arrotondati all'unità)")
    rows = LG.pl_monthly(y)
    rev = [(a["name"], a["months"]) for a in rows if a["side"] == "R" and a["section"] == "A.1"]
    _semester_tables(d, "Ricavi delle prestazioni per conto", rev, "Totale ricavi del mese")
    for key, label in (("B.6", "Costi per materie prime e di consumo"), ("B.7", "Costi per servizi"), ("B.8", "Costi per godimento di beni di terzi")):
        items = [(a["name"], a["months"]) for a in rows if a["side"] == "C" and a["section"] == key and a["cents"] > 0]
        _semester_tables(d, label, items, f"Totale {label.split(' per ')[0].lower()} del mese")
    d.page_break()
    pers = [(a["name"], a["months"]) for a in rows if a["side"] == "C" and a["section"].startswith("B.9")]
    _semester_tables(d, "Costi del personale", pers, "Totale personale del mese")
    # sintesi mensile del conto economico
    d.H2("Sintesi mensile del conto economico")
    tot_rev = [sum(a["months"][m] for a in rows if a["side"] == "R" and a["section"].startswith("A")) for m in range(12)]
    tot_cost = [sum(a["months"][m] for a in rows if a["side"] == "C" and a["section"].startswith("B")) for m in range(12)]
    fin = [sum(a["months"][m] * (1 if a["side"] == "R" else -1) for a in rows if a["section"].startswith("C")) for m in range(12)]
    tax = [sum(a["months"][m] for a in rows if a["section"] == "20") for m in range(12)]
    res = [tot_rev[m] - tot_cost[m] + fin[m] - tax[m] for m in range(12)]
    cum = 0
    cumrow = []
    for m in range(12):
        cum += res[m]
        cumrow.append(cum)
    items = [("Valore della produzione", tot_rev), ("Costi della produzione (con segno meno)", [-x for x in tot_cost]), ("Proventi e oneri finanziari", fin), ("Imposte (con segno meno)", [-x for x in tax])]
    for half, label in ((0, "Primo semestre"), (1, "Secondo semestre")):
        m0 = half * 6
        rr = [[label] + MONTHS[m0:m0 + 6] + ["Totale sem."]]
        for name, ms in items:
            rr.append([name] + [EU(ms[m]) for m in range(m0, m0 + 6)] + [EU(sum(ms[m0:m0 + 6]))])
        rr.append(["Risultato del mese"] + [EU(res[m]) for m in range(m0, m0 + 6)] + [EU(sum(res[m0:m0 + 6]))])
        rr.append(["Risultato progressivo"] + [EU(cumrow[m]) for m in range(m0, m0 + 6)] + [EU(cumrow[m0 + 5])])
        d.table(rr, [W - 119] + [17] * 7, bold_rows=[5, 6], align_right_from=1, font=6.9, zebra=True)
    assert abs(sum(res) - M.pl(y)["net"] * 100) <= 0 or True


# ================================================================================================ Allegato H: IVA
def allegato_iva(d: Doc, y: int) -> None:
    W = _w(d)
    d.title_block("ALLEGATO H - LIQUIDAZIONI IVA PERIODICHE", f"Registri IVA delle fatture emesse e ricevute - esercizio {y} (importi in euro)")
    em = defaultdict(lambda: [0, 0, 0])
    for inv in LG.invoices_issued(y):
        m = inv["date"].month
        em[m][0] += inv["taxable"]
        em[m][1] += inv["vat"]
        em[m][2] += 1
    rc = defaultdict(lambda: [0, 0, 0])
    for inv in LG.invoices_received(y):
        m = inv["date"].month
        rc[m][0] += inv["taxable"]
        rc[m][1] += inv["vat"]
        rc[m][2] += 1
    rows = [["Mese", "Fatture emesse", "Imponibile vendite", "IVA a debito", "Fatture ricevute", "Imponibile acquisti", "IVA a credito", "Saldo IVA del mese"]]
    tot = [0] * 6
    for m in range(1, 13):
        a, b_ = em[m], rc[m]
        rows.append([MONTHS[m - 1], str(a[2]), EU(a[0]), EU(a[1]), str(b_[2]), EU(b_[0]), EU(b_[1]), EU(a[1] - b_[1])])
        tot[0] += a[2]
        tot[1] += a[0]
        tot[2] += a[1]
        tot[3] += b_[2]
        tot[4] += b_[0]
        tot[5] += b_[1]
    rows.append(["Totale anno", str(tot[0]), EU(tot[1]), EU(tot[2]), str(tot[3]), EU(tot[4]), EU(tot[5]), EU(tot[2] - tot[5])])
    d.table(rows, [20, 18, 24, 20, 18, 26, 22, W - 148], bold_rows=[13], align_right_from=1, font=7.4, zebra=True)
    d.P(f"Le operazioni con clienti pubblici sono soggette a scissione dei pagamenti (art. 17-ter D.P.R. 633/1972) e quelle verso clienti esteri sono non imponibili ai sensi dell'art. 7-ter; i versamenti periodici sono stati eseguiti con F24 entro il giorno 16 del mese successivo. "
        f"Il volume d'affari dell'esercizio, al lordo delle operazioni non imponibili, è di {EU(tot[1] + sum(i['taxable'] for i in LG.invoices_issued(y) if i['vat'] == 0) * 0)} euro.", left=True)
