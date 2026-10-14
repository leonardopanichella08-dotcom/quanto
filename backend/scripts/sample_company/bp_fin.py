"""Business plan 2026-2028: parte finanziaria (conto economico, stato patrimoniale, rendiconto, trimestri, finanziamenti, scenari) e allegati mensili."""
from __future__ import annotations

from typing import Dict, List

from . import bp
from . import model as M
from .bp_doc import KPI, MONTHS, pcts, recurring
from .pdfkit import Doc, pct, units

U = units
YEARS = bp.YEARS


def _w(d: Doc) -> float:
    return d.width / 2.8346


def A(series: List[int], y: int) -> int:
    return bp.annual(series, y)


def Q(series: List[int], y: int, q: int) -> int:
    return sum(series[m] for m in range(bp.N) if bp.MONTHS[m][0] == y and (bp.MONTHS[m][1] - 1) // 3 == q)


def QE(series: List[int], y: int, q: int) -> int:
    return series[[m for m in range(bp.N) if bp.MONTHS[m] == (y, q * 3 + 3)][0]]


def annual_pl_rows() -> List[tuple]:
    """Righe del conto economico previsionale annuale: (etichetta, serie mensile con segno, grassetto)."""
    pl = bp.pl()
    rev = bp.revenue()
    ext = bp.external_costs()
    pers = bp.personnel_lines()
    rows: List[tuple] = []
    for n in bp.REV_LINES:
        rows.append((n, rev[n], False))
    rows.append(("Ricavi delle vendite e delle prestazioni", pl["ricavi"], True))
    rows.append(("Incrementi di immobilizzazioni per lavori interni", pl["lavori_interni"], False))
    rows.append(("Contributi in conto esercizio (credito d'imposta ricerca e sviluppo)", pl["contributi"], False))
    rows.append(("Altri ricavi e proventi", pl["altri_ricavi"], False))
    rows.append(("Valore della produzione", pl["valore_produzione"], True))
    for n, s in ext.items():
        rows.append((n, [-x for x in s], False))
    rows.append(("Oneri diversi di gestione", [-x for x in pl["oneri_diversi"]], False))
    rows.append(("Svalutazione dei crediti", [-x for x in pl["svalutazione_crediti"]], False))
    for n, s in pers.items():
        rows.append((n, [-x for x in s], False))
    rows.append(("Margine operativo lordo (EBITDA)", pl["ebitda"], True))
    rows.append(("Ammortamenti", [-x for x in pl["ammortamenti"]], False))
    rows.append(("Risultato operativo (EBIT)", pl["ebit"], True))
    rows.append(("Proventi finanziari", pl["proventi_finanziari"], False))
    rows.append(("Oneri finanziari", [-x for x in pl["oneri_finanziari"]], False))
    rows.append(("Risultato prima delle imposte", pl["ante_imposte"], True))
    rows.append(("IRES", [-x for x in pl["ires"]], False))
    rows.append(("IRAP", [-x for x in pl["irap"]], False))
    rows.append(("Utile netto", pl["utile"], True))
    return rows


def annual_financials(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.title_block("11. PIANO ECONOMICO, PATRIMONIALE E FINANZIARIO ANNUALE")
    d.H1("11.1 Conto economico previsionale")
    rows = [["Voce (euro)", "2023", "2024", "2025", "2026", "2027", "2028"]]
    hist = {y: M.pl(y) for y in (2023, 2024, 2025)}
    rws = annual_pl_rows()
    hist_map = {
        "Ricavi delle vendite e delle prestazioni": lambda p: p["revenue"], "Incrementi di immobilizzazioni per lavori interni": lambda p: p["capitalized"],
        "Contributi in conto esercizio (credito d'imposta ricerca e sviluppo)": lambda p: p["grants"], "Altri ricavi e proventi": lambda p: p["other_income"],
        "Valore della produzione": lambda p: p["a_total"], "Oneri diversi di gestione": lambda p: -p["b14"], "Svalutazione dei crediti": lambda p: -p["b10d"],
        "Margine operativo lordo (EBITDA)": lambda p: p["ebit"] + p["b10a"] + p["b10b"] + p["b10d"], "Ammortamenti": lambda p: -(p["b10a"] + p["b10b"]), "Risultato operativo (EBIT)": lambda p: p["ebit"],
        "Proventi finanziari": lambda p: p["int_income"] + max(0, p["fx"]), "Oneri finanziari": lambda p: -p["int_expense"] + min(0, p["fx"]), "Risultato prima delle imposte": lambda p: p["pre_tax"],
        "IRES": lambda p: -p["ires"], "IRAP": lambda p: -p["irap"], "Utile netto": lambda p: p["net"],
        "Salari e stipendi": lambda p: -p["b9a"], "Oneri sociali": lambda p: -p["b9b"], "Trattamento di fine rapporto": lambda p: -p["b9c"], "Altri costi del personale (premi, welfare, buoni pasto)": lambda p: -p["b9e"]}
    bold = []
    for k, (label, series, b) in enumerate(rws, 1):
        h = [U(hist_map[label](hist[y])) if label in hist_map else "" for y in (2023, 2024, 2025)]
        rows.append([label] + h + [U(A(series, y)) for y in YEARS])
        if b:
            bold.append(k)
    d.table(rows, [W - 132, 22, 22, 22, 22, 22, 22], bold_rows=bold, font=7.2, zebra=True)
    d.small("Per gli anni storici le voci di costo esterne sono esposte nel dettaglio per natura nelle note del bilancio; qui compaiono solo quelle confrontabili. Il costo del personale 2023-2025 comprende anche la quota capitalizzata (voce A.4).")
    d.P("Il conto economico mostra la crescita del valore della produzione del 18,5% nel 2026 e del 16% in media nei due anni successivi, con margini operativi stabili: i costi esterni si riducono in percentuale dei ricavi, mentre il costo del personale cresce con l'organico e con gli adeguamenti contrattuali. "
        "Gli ammortamenti aumentano per la capitalizzazione dei costi di sviluppo di Atlas e per gli investimenti in infrastruttura.")
    bs = bp.balance_sheet()
    b5 = M.balance(2025)
    d.H1("11.2 Stato patrimoniale previsionale")
    rows = [["Voce (euro)", "31/12/2025", "31/12/2026", "31/12/2027", "31/12/2028"]]

    def row(label, key, sign=1):
        return [label, U(sign * b5[key] if key in b5 else 0)] + [U(sign * bp.year_end(bs[key], y)) for y in YEARS]
    items = [("Immobilizzazioni immateriali", "intang"), ("Immobilizzazioni materiali", "tang"), ("Immobilizzazioni finanziarie", "deposits"), ("Lavori in corso su ordinazione", "wip"), ("Crediti verso clienti", "trade"),
             ("Crediti tributari", "tax_cr"), ("Crediti verso altri", "other_cr"), ("Disponibilità liquide", "cash"), ("Ratei e risconti attivi", "prepaid")]
    for l, k in items:
        rows.append(row(l, k))
    rows.append(["Totale attivo", U(b5["assets"])] + [U(bp.year_end(bs["assets"], y)) for y in YEARS])
    rows.append(row("Patrimonio netto", "pn"))
    rows.append(row("Trattamento di fine rapporto", "tfr"))
    rows.append(row("Debiti verso banche", "loan"))
    rows.append(row("Debiti verso fornitori", "suppliers"))
    rows.append(row("Debiti tributari", "tax_debt"))
    rows.append(row("Debiti verso istituti di previdenza", "social"))
    rows.append(row("Altri debiti", "other_debt"))
    rows.append(row("Ratei e risconti passivi", "accrued"))
    rows.append(["Totale passivo e patrimonio netto", U(b5["liabilities"])] + [U(bp.year_end(bs["liabilities"], y)) for y in YEARS])
    d.table(rows, [W - 124, 31, 31, 31, 31], bold_rows=[10, 19], font=8, zebra=True)
    cf = bp.cash_flow()
    d.H1("11.3 Rendiconto finanziario previsionale (metodo indiretto)")
    rows = [["Voce (euro)", "2026", "2027", "2028"]]
    lines = [("Utile netto", "utile"), ("Ammortamenti", "ammortamenti"), ("Variazione del TFR", "d_tfr"), ("Variazione dei lavori in corso", "d_wip"), ("Variazione dei crediti verso clienti", "d_trade"), ("Variazione di altri crediti e risconti attivi", "d_other_assets"),
             ("Variazione dei debiti verso fornitori", "d_suppliers"), ("Variazione di debiti tributari, previdenziali, altri e ratei", "d_tax_social_other"), ("Flusso finanziario dell'attività operativa (A)", "operating"),
             ("Investimenti in immobilizzazioni (B)", "investing"), ("Accensione e rimborso di finanziamenti", "loan"), ("Dividendi pagati", "dividends"), ("Flusso finanziario dell'attività di finanziamento (C)", "financing"),
             ("Variazione delle disponibilità liquide (A+B+C)", "change")]
    for l, k in lines:
        rows.append([l] + [U(A(cf[k], y)) for y in YEARS])
    rows.append(["Disponibilità liquide a inizio anno"] + [U(cf["open"][[m for m in range(bp.N) if bp.MONTHS[m] == (y, 1)][0]]) for y in YEARS])
    rows.append(["Disponibilità liquide a fine anno"] + [U(bp.year_end(cf["close"], y)) for y in YEARS])
    d.table(rows, [W - 90, 30, 30, 30], bold_rows=[9, 10, 13, 14, 16], font=8, zebra=True)
    d.H1("11.4 Indicatori del piano")
    pl = bp.pl()
    rows = [["Indicatore", "2025", "2026", "2027", "2028"]]
    r5 = M.ratio_notes(2025)
    ratios = {"ROE": [pcts(M.pl(2025)["net"], M.balance(2024)["pn"])] + [pcts(A(pl["utile"], y), (b5["pn"] if y == 2026 else bp.year_end(bs["pn"], y - 1))) for y in YEARS],
              "ROI": [pcts(M.pl(2025)["ebit"], b5["assets"])] + [pcts(A(pl["ebit"], y), bp.year_end(bs["assets"], y)) for y in YEARS],
              "EBITDA / ricavi": [pcts(r5["ebitda"], M.REVENUE[3])] + [pcts(A(pl["ebitda"], y), bp.REV_TARGET[y]) for y in YEARS],
              "Costo del personale / ricavi": [pcts(M.pl(2025)["b9a"] + M.pl(2025)["b9b"] + M.pl(2025)["b9c"] + M.pl(2025)["b9e"], M.REVENUE[3])] + [pcts(A(bp.personnel_total(), y), bp.REV_TARGET[y]) for y in YEARS],
              "Posizione finanziaria netta / EBITDA": [f"{(b5['loan'] - b5['cash']) / r5['ebitda']:.2f}".replace(".", ",")] + [f"{(bp.year_end(bs['loan'], y) - bp.year_end(bs['cash'], y)) / A(pl['ebitda'], y):.2f}".replace(".", ",") for y in YEARS],
              "Patrimonio netto / totale attivo": [pcts(b5["pn"], b5["assets"])] + [pcts(bp.year_end(bs["pn"], y), bp.year_end(bs["assets"], y)) for y in YEARS],
              "Ricavi per persona (euro)": [U(round(M.REVENUE[3] / M.EMPLOYEES[2025]))] + [U(round(bp.REV_TARGET[y] / (sum(bp.staff()["heads"][m] for m in range(bp.N) if bp.MONTHS[m][0] == y) / 12))) for y in YEARS]}
    for k, v in ratios.items():
        rows.append([k] + v)
    d.table(rows, [W - 130, 26, 26, 26, 26], align_right_from=1, font=8, zebra=True)


def quarterly(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.title_block("12. PIANO TRIMESTRALE")
    pl = bp.pl()
    bs = bp.balance_sheet()
    cf = bp.cash_flow()
    for y in YEARS:
        d.H1(f"12.{YEARS.index(y) + 1} Anno {y}")
        rows = [["Conto economico (euro)", "T1", "T2", "T3", "T4", "Anno"]]
        items = [("Ricavi", pl["ricavi"]), ("Valore della produzione", pl["valore_produzione"]), ("Costi esterni", pl["costi_esterni"]), ("Costo del personale", pl["personale"]), ("EBITDA", pl["ebitda"]), ("Ammortamenti", pl["ammortamenti"]),
                 ("EBIT", pl["ebit"]), ("Oneri finanziari netti", [pl["oneri_finanziari"][m] - pl["proventi_finanziari"][m] for m in range(bp.N)]), ("Imposte", pl["imposte"]), ("Utile netto", pl["utile"])]
        for l, s in items:
            rows.append([l] + [U(Q(s, y, q)) for q in range(4)] + [U(A(s, y))])
        d.table(rows, [W - 130, 26, 26, 26, 26, 26], bold_rows=[1, 5, 7, 10], font=8, zebra=True)
        rows = [["Stato patrimoniale e cassa a fine trimestre (euro)", "T1", "T2", "T3", "T4"]]
        for l, k in (("Crediti verso clienti", "trade"), ("Disponibilità liquide", "cash"), ("Debiti bancari", "loan"), ("Debiti verso fornitori", "suppliers"), ("Patrimonio netto", "pn"), ("Totale attivo", "assets")):
            rows.append([l] + [U(QE(bs[k], y, q)) for q in range(4)])
        rows.append(["Flusso operativo del trimestre"] + [U(Q(cf["operating"], y, q)) for q in range(4)])
        rows.append(["Investimenti del trimestre"] + [U(Q(cf["investing"], y, q)) for q in range(4)])
        d.table(rows, [W - 104, 26, 26, 26, 26], font=8, zebra=True)


def financing(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.title_block("13. FABBISOGNO FINANZIARIO, FINANZIAMENTI E SOSTENIBILITA' DEL DEBITO")
    d.P(f"Il piano non presenta un fabbisogno finanziario strutturale: il flusso operativo copre gli investimenti, il rimborso dei finanziamenti e i dividendi. Il nuovo finanziamento chirografario di {U(bp.NEW_LOAN)} euro serve a rafforzare la liquidità durante la fase di maggiore investimento "
        "(sviluppo della versione commerciale di Atlas e assunzioni) e a mantenere un presidio di liquidità superiore a tre mesi di costi fissi. È richiesta la garanzia del Fondo centrale di garanzia per le PMI nella misura dell'80%.")
    d.table([["Condizioni del nuovo finanziamento", "Dato"], ["Importo", f"euro {U(bp.NEW_LOAN)}"], ["Forma tecnica", "Finanziamento chirografario a medio termine"], ["Durata", "60 mesi, di cui 12 di preammortamento"], ["Erogazione prevista", "Marzo 2026"],
             ["Rimborso", "16 rate trimestrali di capitale costanti dal 31/03/2027, più interessi trimestrali"], ["Tasso", "Euribor a tre mesi più 2,40 punti (ipotesi 5,35% nel piano)"], ["Garanzie", "Fondo centrale di garanzia PMI 80%; nessuna garanzia reale"],
             ["Covenant", "Nessuno richiesto; indicatore interno: PFN / EBITDA non superiore a 1,5"], ["Spese di istruttoria", "0,50% dell'importo"]], [60, W - 60], align_right_from=9, font=8, zebra=True)
    d.H1("13.1 Piano di rimborso dei finanziamenti")
    d_ = bp.debt()
    rows = [["Data", "Finanziamento esistente: rata capitale", "Debito residuo", "Nuovo finanziamento: movimento", "Debito residuo", "Debito bancario totale"]]
    for m in range(bp.N):
        yy, mm = bp.MONTHS[m]
        if mm in (3, 6, 9, 12):
            rows.append([f"{[31, 30, 30, 31][(mm // 3) - 1]:02d}/{mm:02d}/{yy}", U(d_["old_pay"][m]), U(d_["old"][m]), U(d_["new_flow"][m]), U(d_["new"][m]), U(d_["old"][m] + d_["new"][m])])
    d.table(rows, [24, 34, 28, 36, 28, W - 150], align_right_from=1, font=7.6, zebra=True)
    d.small("Nel movimento del nuovo finanziamento il valore negativo è l'erogazione (entrata di cassa); i valori positivi sono rimborsi di capitale.")
    d.H1("13.2 Sostenibilità del debito")
    pl = bp.pl()
    cf = bp.cash_flow()
    rows = [["Indicatore", "2026", "2027", "2028"]]
    svc = {}
    for y in YEARS:
        cap_rep = sum(max(0, d_["old_pay"][m]) + max(0, d_["new_flow"][m]) for m in range(bp.N) if bp.MONTHS[m][0] == y)
        svc[y] = cap_rep + A(pl["oneri_finanziari"], y)
    rows.append(["Flusso di cassa operativo (euro)"] + [U(A(cf["operating"], y)) for y in YEARS])
    rows.append(["Servizio del debito: capitale e interessi (euro)"] + [U(svc[y]) for y in YEARS])
    rows.append(["Indice di copertura del servizio del debito (DSCR)"] + [f"{A(cf['operating'], y) / svc[y]:.1f}".replace(".", ",") for y in YEARS])
    rows.append(["Copertura degli oneri finanziari (EBIT / oneri)"] + [f"{A(pl['ebit'], y) / A(pl['oneri_finanziari'], y):.0f}".replace(".", ",") + " volte" for y in YEARS])
    bs = bp.balance_sheet()
    rows.append(["PFN / EBITDA (negativa = liquidità netta)"] + [f"{(bp.year_end(bs['loan'], y) - bp.year_end(bs['cash'], y)) / A(pl['ebitda'], y):.2f}".replace(".", ",") for y in YEARS])
    rows.append(["Debiti bancari / patrimonio netto"] + [f"{bp.year_end(bs['loan'], y) / bp.year_end(bs['pn'], y):.2f}".replace(".", ",") for y in YEARS])
    rows.append(["Liquidità minima mensile nell'anno (euro)"] + [U(min(bs["cash"][m] for m in range(bp.N) if bp.MONTHS[m][0] == y)) for y in YEARS])
    d.table(rows, [W - 90, 30, 30, 30], font=8, zebra=True, align_right_from=1)


def kpi(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.title_block("14. INDICATORI CHIAVE (KPI)")
    rev = bp.revenue()
    rows = [["KPI", "2025", "2026", "2027", "2028"]]
    rc = {y: recurring(y) for y in YEARS}
    rows.append(["Imprese clienti con canone a fine anno"] + [str(KPI["companies_end"][y]) for y in (2025, 2026, 2027, 2028)])
    rows.append(["Studi professionali con licenza a fine anno"] + [str(KPI["studios_end"][y]) for y in (2025, 2026, 2027, 2028)])
    rows.append(["Ricavi ricorrenti annui - ARR (euro)"] + [U(round(M.REVENUE[3] * 0.30))] + [U(rc[y]["total"]) for y in YEARS])
    rows.append(["Ricavi ricorrenti su ricavi totali"] + [pcts(M.REVENUE[3] * 0.30, M.REVENUE[3])] + [pcts(rc[y]["total"], bp.REV_TARGET[y]) for y in YEARS])
    rows.append(["Abbandono annuo dei clienti (churn)", "9%"] + [pcts(KPI["churn"][y], 1, 0) for y in YEARS])
    rows.append(["Ricavo medio annuo per impresa (euro)", U(2300)] + [U(KPI["arpa"][y]) for y in YEARS])
    pl = bp.pl()
    rows.append(["Margine operativo lordo / ricavi", pcts(M.ratio_notes(2025)["ebitda"], M.REVENUE[3])] + [pcts(A(pl["ebitda"], y), bp.REV_TARGET[y]) for y in YEARS])
    rows.append(["Margine operativo / ricavi", pcts(M.pl(2025)["ebit"], M.REVENUE[3])] + [pcts(A(pl["ebit"], y), bp.REV_TARGET[y]) for y in YEARS])
    rows.append(["Ricavi per persona (euro)", U(round(M.REVENUE[3] / M.EMPLOYEES[2025]))] + [U(round(bp.REV_TARGET[y] / (sum(bp.staff()["heads"][m] for m in range(bp.N) if bp.MONTHS[m][0] == y) / 12))) for y in YEARS])
    rows.append(["Persone in organico a fine anno", "16"] + [str(bp.staff()["heads"][[m for m in range(bp.N) if bp.MONTHS[m] == (y, 12)][0]]) for y in YEARS])
    rows.append(["Giorni medi di incasso (DSO)", "99"] + [str(bp.DSO[y]) for y in YEARS])
    d.table(rows, [W - 130, 26, 26, 26, 26], font=8, zebra=True, align_right_from=1)
    d.H1("Soglie di attenzione e azioni")
    d.table([["KPI", "Soglia di attenzione", "Azione prevista"], ["Churn annuo", "Superiore al 11%", "Revisione del piano di customer success e del prezzo"], ["DSO", "Superiore a 100 giorni", "Solleciti anticipati, scontistica per pagamento anticipato dei canoni"],
             ["Liquidità minima mensile", "Inferiore a 120.000 euro", "Rinvio degli investimenti discrezionali; utilizzo di affidamenti"], ["Costo del personale / ricavi", "Superiore al 60%", "Rallentamento delle assunzioni non commerciali"],
             ["Costo di acquisizione / LTV", "CAC oltre un terzo dell'LTV", "Riduzione delle campagne meno efficaci"]], [50, 44, W - 94], align_right_from=9, font=8, zebra=True)


def scenarios(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.title_block("15. SCENARI E ANALISI DI SENSIBILITA'")
    pl = bp.pl()
    d.P("Gli scenari sono costruiti a partire dal piano di base modificando i ricavi e le voci di costo che ne dipendono. Nello scenario prudente i ricavi sono inferiori del 10% e le due assunzioni più lontane sono rinviate; nello scenario ottimistico "
        "si assume una crescita dei canoni più rapida del 12% e la concessione di contributi per 60.000 euro nel 2027 e 70.000 euro nel 2028.")
    def scen(y: int, rev_k: float, ext_k: float, pers_add: int, grants: int) -> Dict[str, int]:
        rev_ = round(bp.REV_TARGET[y] * rev_k)
        ext_ = round(A(pl["costi_esterni"], y) * ext_k)
        pers_ = A(pl["personale"], y) + pers_add
        oth = A(pl["lavori_interni"], y) + A(pl["contributi"], y) + A(pl["altri_ricavi"], y) + grants
        var = A(pl["svalutazione_crediti"], y) + A(pl["oneri_diversi"], y)
        ebitda = rev_ + oth - ext_ - pers_ - round(var * rev_k)
        ebit = ebitda - A(pl["ammortamenti"], y)
        pre = ebit - A(pl["oneri_finanziari"], y) + A(pl["proventi_finanziari"], y)
        tax = round(max(0, pre - A(pl["contributi"], y)) * 0.24 + max(0, ebit) * 0.039)
        return {"rev": rev_, "ebitda": ebitda, "ebit": ebit, "net": pre - tax}
    sets = {"Prudente": (0.90, 0.92, {2026: -17000, 2027: -63000, 2028: -118000}, {y: 0 for y in YEARS}), "Base": (1.0, 1.0, {y: 0 for y in YEARS}, {y: 0 for y in YEARS}),
            "Ottimistico": (1.12, 1.07, {2026: 12000, 2027: 40000, 2028: 70000}, {2026: 0, 2027: 60000, 2028: 70000})}
    rows = [["Scenario", "Ricavi 2028", "EBITDA 2028", "EBIT 2028", "Utile 2028", "EBIT / ricavi", "Ricavi cumulati 2026-28"]]
    for name, (rk, ek, pa, gr) in sets.items():
        res = {y: scen(y, rk, ek, pa[y], gr[y]) for y in YEARS}
        rows.append([name, U(res[2028]["rev"]), U(res[2028]["ebitda"]), U(res[2028]["ebit"]), U(res[2028]["net"]), pcts(res[2028]["ebit"], res[2028]["rev"]), U(sum(res[y]["rev"] for y in YEARS))])
    d.table(rows, [28, 26, 26, 26, 26, 22, W - 154], align_right_from=1, font=7.8, bold_rows=[2])
    for name, (rk, ek, pa, gr) in sets.items():
        d.H2(f"Scenario {name.lower()}: conto economico sintetico (euro)")
        res = {y: scen(y, rk, ek, pa[y], gr[y]) for y in YEARS}
        d.table([["Voce", "2026", "2027", "2028"], ["Ricavi"] + [U(res[y]["rev"]) for y in YEARS], ["EBITDA"] + [U(res[y]["ebitda"]) for y in YEARS], ["EBIT"] + [U(res[y]["ebit"]) for y in YEARS], ["Utile netto"] + [U(res[y]["net"]) for y in YEARS]],
                [W - 90, 30, 30, 30], font=8, align_right_from=1, bold_rows=[4])
    d.H1("15.1 Sensibilità del risultato operativo 2028 ai singoli fattori")
    base = A(pl["ebit"], 2028)
    rows = [["Fattore (variazione)", "Effetto sull'EBIT 2028 (euro)", "EBIT risultante", "EBIT / ricavi"]]
    effects = [("Ricavi -10% (costi esterni variabili)", -round(bp.REV_TARGET[2028] * 0.10) + round(A(pl["costi_esterni"], 2028) * 0.10)), ("Ricavi +10% (costi esterni variabili)", round(bp.REV_TARGET[2028] * 0.10) - round(A(pl["costi_esterni"], 2028) * 0.10)),
               ("Costo del personale +5%", -round(A(pl["personale"], 2028) * 0.05)), ("Costo del personale -5%", round(A(pl["personale"], 2028) * 0.05)), ("Costi esterni +10%", -round(A(pl["costi_esterni"], 2028) * 0.10)),
               ("Costi esterni -10%", round(A(pl["costi_esterni"], 2028) * 0.10)), ("Prezzi dei canoni -5%", -round(A(bp.revenue()[bp.REV_LINES[0]], 2028) * 0.05)), ("Prezzi dei canoni +5%", round(A(bp.revenue()[bp.REV_LINES[0]], 2028) * 0.05)),
               ("Ritardo di due assunzioni di sviluppo (6 mesi)", round(2 * 50000 * 0.5 * 1.13)), ("Abbandono dei clienti +3 punti", -round(recurring(2028)["companies"] * 0.03))]
    for l, e in effects:
        rows.append([l, U(e), U(base + e), pcts(base + e, bp.REV_TARGET[2028])])
    d.table(rows, [W - 100, 36, 34, 30], font=8, zebra=True, align_right_from=1)
    d.H1("15.2 Prova di stress sulla liquidità")
    bs = bp.balance_sheet()
    d.table([["Evento di stress", "Effetto sulla cassa (euro)", "Cassa minima risultante (euro)", "Valutazione"], ["Ritardo di incasso di 30 giorni su tutti i clienti (2027)", U(-round(bp.REV_TARGET[2027] / 12)), U(min(bs["cash"][m] for m in range(bp.N) if bp.MONTHS[m][0] == 2027) - round(bp.REV_TARGET[2027] / 12)), "Sostenibile"],
             ["Perdita del cliente più grande (10% dei ricavi) da giugno 2027", U(-round(bp.REV_TARGET[2027] * 0.10 * 0.5)), U(min(bs["cash"][m] for m in range(bp.N) if bp.MONTHS[m][0] == 2027) - round(bp.REV_TARGET[2027] * 0.10 * 0.5)), "Sostenibile"],
             ["Mancato utilizzo del finanziamento e dividendi invariati (2026)", U(-bp.NEW_LOAN), U(min(bs["cash"][m] for m in range(bp.N) if bp.MONTHS[m][0] == 2026) - bp.NEW_LOAN), "Sostenibile con riduzione degli investimenti"],
             ["Aumento dei tassi di 200 punti base su tutto il debito", U(-round(100000 * 0.02)), U(min(bs["cash"][m] for m in range(bp.N) if bp.MONTHS[m][0] == 2027) - 2000), "Sostenibile"]], [72, 34, 38, W - 144], font=7.6, align_right_from=1)


def risks(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.title_block("16. RISCHI E PIANI DI CONTINGENZA")
    d.table([["Rischio", "Probabilità", "Impatto", "Indicatore di allerta", "Risposta"],
             ["Perdita di sviluppatori chiave", "Media", "Alto", "Dimissioni; rotazione > 10%", "Welfare, formazione, documentazione del codice, piano di successione"],
             ["Ritardo di pagamento degli enti pubblici", "Alta", "Medio", "DSO > 100 giorni", "Anticipo fatture e affidamento bancario; sollecito anticipato"],
             ["Cambiamento delle regole dei bandi", "Media", "Medio", "Nuove circolari non recepite entro 5 giorni", "Archivio versionato, analista dedicata, comunicazione agli utenti"],
             ["Incidente di sicurezza informatica", "Bassa", "Alto", "Vulnerabilità critiche aperte", "ISO/IEC 27001, backup cifrati, polizza cyber, test di penetrazione"],
             ["Rallentamento delle vendite", "Media", "Alto", "Lead e prove gratuite sotto il 15% del piano", "Rimodulazione del marketing, partnership con associazioni, rinvio delle assunzioni"],
             ["Aumento dell'abbandono dei clienti", "Media", "Medio", "Churn > 11%", "Customer success, revisione del prodotto, offerte di rinnovo pluriennale"],
             ["Concorrenza di grandi operatori", "Media", "Medio", "Perdita di gare o clienti per prezzo", "Differenziazione su trasparenza e tracciabilità; accordi con gli studi"],
             ["Aumento dei tassi di interesse", "Bassa", "Basso", "Euribor > 4%", "Rimborso anticipato; debito contenuto rispetto alla liquidità"],
             ["Dipendenza dai fornitori cloud", "Bassa", "Medio", "Interruzioni > 4 ore", "Doppia regione, fornitore alternativo testato"],
             ["Rischio normativo sul trattamento dei dati", "Bassa", "Alto", "Rilievi del Garante o dei clienti", "DPO esterno, valutazioni d'impatto, registro dei trattamenti"],
             ["Ritardo nel completamento di Atlas", "Media", "Medio", "Scostamento > 2 mesi sulla roadmap", "Rilascio incrementale; priorità ai moduli con ricavi"],
             ["Mancata concessione di contributi", "Media", "Basso", "Esito negativo delle istruttorie", "Il piano di base non li include"]], [44, 18, 16, 42, W - 120], align_right_from=9, font=7.4, zebra=True)
    d.H1("Piano di contingenza")
    d.P("Se almeno due indicatori di allerta si attivano per due trimestri consecutivi, la direzione convoca un comitato straordinario che decide, entro trenta giorni, tra: rinvio delle assunzioni non commerciali, riduzione degli investimenti discrezionali (fino a 80.000 euro l'anno), "
        "utilizzo delle linee di credito non impegnate, rinegoziazione dei canoni di locazione, rimodulazione dei dividendi. Con ricavi inferiori del 10% il risultato operativo resterebbe positivo in tutto il triennio.")


def governance(d: Doc) -> None:
    W = _w(d)
    d.H1("17. GOVERNANCE, SOSTENIBILITA' E ADEMPIMENTI")
    d.B(["<b>Monitoraggio del piano:</b> consuntivo mensile entro il decimo giorno lavorativo, scostamenti commentati in comitato di direzione, revisione trimestrale delle ipotesi e aggiornamento del piano due volte l'anno.",
         "<b>Reporting ai finanziatori:</b> bilancio e situazione semestrale entro 60 giorni, indicatori di sostenibilità del debito su richiesta.",
         "<b>Sostenibilità:</b> energia da fonti rinnovabili per la sede, riduzione del consumo di carta, politica di trasferte a minore impatto, selezione di fornitori cloud con data center a basse emissioni.",
         "<b>Conformità:</b> GDPR, ISO/IEC 27001, D.Lgs. 81/2008, antiriciclaggio (non applicabile), trasparenza sugli aiuti di Stato (registro aiuti aggiornato a ogni agevolazione)."])
    d.table([["Adempimento", "Scadenza", "Responsabile"], ["Approvazione del bilancio e deposito", "Entro 30 giorni dall'approvazione", "Amministratore unico"], ["Comunicazione del credito d'imposta ricerca e sviluppo", "Entro il termine annuale del MIMIT", "Controllo di gestione"],
             ["Rinnovo certificazioni ISO", "31/05/2027", "Responsabile qualità"], ["Rinnovo DURC", "Ogni 120 giorni", "Amministrazione"], ["Aggiornamento registro aiuti de minimis", "A ogni concessione", "Amministrazione"]], [W - 100, 56, 44], align_right_from=9, font=8, zebra=True)


# ------------------------------------------------------------------------------------------------ allegati
def _semesters(d: Doc, title: str, rows_: List[tuple], y: int, bold: set, font: float = 6.9) -> None:
    W = _w(d)
    d.H2(title)
    for half, label in ((0, "Gennaio-giugno"), (1, "Luglio-dicembre")):
        idx = [m for m in range(bp.N) if bp.MONTHS[m][0] == y][half * 6:half * 6 + 6]
        rows = [[f"{label} {y}"] + [MONTHS[bp.MONTHS[m][1] - 1] for m in idx] + ["Totale"]]
        b_idx = []
        for k, (l, s) in enumerate(rows_, 1):
            rows.append([l] + [U(s[m]) for m in idx] + [U(sum(s[m] for m in idx))])
            if l in bold:
                b_idx.append(k)
        d.table(rows, [W - 119] + [17] * 6 + [17], bold_rows=b_idx, align_right_from=1, font=font, zebra=True)


def annex_monthly_pl(d: Doc) -> None:
    d.page_break()
    d.title_block("ALLEGATO A - PIANO MENSILE DEL CONTO ECONOMICO", "Importi in euro; i costi sono con il segno meno")
    rows = [(l, s) for l, s, _ in annual_pl_rows()]
    bold = {l for l, _, b in annual_pl_rows() if b}
    for y in YEARS:
        _semesters(d, f"Conto economico mensile {y}", rows, y, bold)
        d.page_break() if y != YEARS[-1] else None


def annex_monthly_cash(d: Doc) -> None:
    d.page_break()
    d.title_block("ALLEGATO B - PIANO MENSILE DELLA TESORERIA E DELLO STATO PATRIMONIALE", "Importi in euro")
    cf = bp.cash_flow()
    bs = bp.balance_sheet()
    flows = [("Disponibilità liquide a inizio mese", cf["open"]), ("Flusso operativo", cf["operating"]), ("Investimenti", cf["investing"]), ("Accensione e rimborso finanziamenti", cf["loan"]), ("Dividendi", cf["dividends"]),
             ("Disponibilità liquide a fine mese", cf["close"])]
    for y in YEARS:
        _semesters(d, f"Tesoreria mensile {y}", flows, y, {"Disponibilità liquide a fine mese"})
        items = [("Crediti verso clienti", bs["trade"]), ("Lavori in corso", bs["wip"]), ("Immobilizzazioni nette", [bs["intang"][m] + bs["tang"][m] + bs["deposits"][m] for m in range(bp.N)]), ("Totale attivo", bs["assets"]),
                 ("Patrimonio netto", bs["pn"]), ("Debiti bancari", bs["loan"]), ("Debiti verso fornitori", bs["suppliers"]), ("Debiti tributari e previdenziali", [bs["tax_debt"][m] + bs["social"][m] for m in range(bp.N)])]
        _semesters(d, f"Stato patrimoniale mensile {y} (saldi a fine mese)", items, y, {"Totale attivo", "Patrimonio netto"})
        d.page_break() if y != YEARS[-1] else None


def annex_staff(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.title_block("ALLEGATO C - ORGANICO E COSTO DEL PERSONALE PER MESE")
    st = bp.staff()
    pl = bp.personnel_lines()
    for y in YEARS:
        rows_ = [("Persone in organico a fine mese", st["heads"])] + [(k, v) for k, v in pl.items()] + [("Costo totale del personale", bp.personnel_total())]
        d.H2(f"Anno {y}")
        for half, label in ((0, "Gennaio-giugno"), (1, "Luglio-dicembre")):
            idx = [m for m in range(bp.N) if bp.MONTHS[m][0] == y][half * 6:half * 6 + 6]
            rows = [[f"{label} {y}"] + [MONTHS[bp.MONTHS[m][1] - 1] for m in idx] + ["Totale"]]
            for l, s in rows_:
                tot = "" if l.startswith("Persone") else U(sum(s[m] for m in idx))
                rows.append([l] + [U(s[m]) for m in idx] + [tot])
            d.table(rows, [W - 119] + [17] * 6 + [17], bold_rows=[len(rows) - 1], align_right_from=1, font=7, zebra=True)
    d.H2("Costo annuo del personale per persona (euro)")
    rows = [["Matricola", "Ruolo", "2026", "2027", "2028"]]
    for pr in st["people"]:
        ser = st["per_person"][pr["id"]]
        rows.append([pr["id"], pr["role"]] + [U(round(sum(ser[m] for m in range(bp.N) if bp.MONTHS[m][0] == y) * (1 + bp.PERSONNEL_EXTRA))) for y in YEARS])
    d.table(rows, [20, W - 110, 30, 30, 30], align_right_from=2, font=7.4, zebra=True)


def annex_history(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.title_block("ALLEGATO D - DATI STORICI DI RIFERIMENTO", "Bilanci d'esercizio 2022-2025 in forma sintetica (euro)")
    rows = [["Conto economico", "2022", "2023", "2024", "2025"]]
    for l, k in (("Ricavi delle vendite e delle prestazioni", "revenue"), ("Valore della produzione", "a_total"), ("Costi della produzione", "b_total"), ("Risultato operativo (EBIT)", "ebit"), ("Proventi e oneri finanziari", "fin"),
                 ("Imposte sul reddito", "taxes"), ("Utile dell'esercizio", "net")):
        rows.append([l] + [U(M.pl(y)[k]) for y in M.ALL_YEARS])
    rows.append(["Margine operativo lordo (EBITDA)"] + [U(M.ratio_notes(y)["ebitda"]) for y in M.ALL_YEARS])
    rows.append(["Dipendenti medi"] + [str(M.EMPLOYEES[y]) for y in M.ALL_YEARS])
    d.table(rows, [W - 120, 30, 30, 30, 30], font=8, zebra=True, align_right_from=1)
    rows = [["Stato patrimoniale", "2022", "2023", "2024", "2025"]]
    for l, k in (("Immobilizzazioni", "fixed"), ("Rimanenze", "wip"), ("Crediti", "receivables"), ("Disponibilità liquide", "cash"), ("Totale attivo", "assets"), ("Patrimonio netto", "pn"), ("TFR", "tfr"), ("Debiti verso banche", "loan"),
                 ("Altri debiti", "debts")):
        rows.append([l] + [U(M.balance(y)[k]) for y in M.ALL_YEARS])
    d.table(rows, [W - 120, 30, 30, 30, 30], font=8, zebra=True, align_right_from=1)
    d.P("Il piano parte dai saldi di bilancio al 31/12/2025 e dall'organico di settembre 2026. I dati storici sono quelli dei bilanci d'esercizio depositati; per l'esercizio 2025 il bilancio è stato approvato il 28/04/2026.")


def annex_glossary(d: Doc) -> None:
    W = _w(d)
    d.H1("ALLEGATO E - GLOSSARIO")
    d.table([["Termine", "Significato"], ["EBITDA", "Margine operativo lordo: risultato operativo prima di ammortamenti e svalutazioni"], ["EBIT", "Risultato operativo: valore della produzione meno costi della produzione"],
             ["PFN", "Posizione finanziaria netta: debiti finanziari meno disponibilità liquide"], ["DSCR", "Indice di copertura del servizio del debito: flusso operativo / (capitale + interessi)"], ["DSO", "Giorni medi di incasso dei crediti verso clienti"],
             ["DPO", "Giorni medi di pagamento dei debiti verso fornitori"], ["ARR", "Ricavi ricorrenti annui da canoni e licenze"], ["Churn", "Percentuale di clienti con canone che non rinnovano nell'anno"],
             ["CAC", "Costo di acquisizione di un nuovo cliente"], ["LTV", "Valore attuale del margine generato da un cliente nel tempo"], ["De minimis", "Aiuti di importo limitato (300.000 euro in tre anni) esentati dalla notifica"],
             ["SAM/TAM/SOM", "Mercato totale, mercato raggiungibile e quota ottenibile"]], [34, W - 34], align_right_from=9, font=8, zebra=True)
    d.small("Documento di prova: tutti i dati sono fittizi e generati per provare QUANTO.")
