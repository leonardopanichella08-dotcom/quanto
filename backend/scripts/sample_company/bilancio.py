"""Il bilancio d'esercizio in forma ordinaria (art. 2423 e seguenti c.c.): stato patrimoniale, conto economico, rendiconto finanziario, nota integrativa,
relazione sulla gestione, verbale dell'assemblea e allegato con il conto economico analitico. Come lo consegna uno studio, per ogni esercizio."""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from . import bil_all, bil_nota, bil_rel
from . import model as M
from .pdfkit import Doc, cents, pct, units

U = units


def _pair(y: int, key: str, src) -> Tuple[str, str]:
    cur = src(y)[key]
    prev = src(y - 1)[key] if y > 2022 else None
    return U(cur), (U(prev) if prev is not None else "")


def _bs(y: int):
    return M.balance(y)


def make_balance(path: Path, y: int) -> Path:
    co = M.COMPANY
    b, p = M.balance(y), M.pl(y)
    b0 = M.balance(y - 1) if y > 2022 else None
    p0 = M.pl(y - 1) if y > 2022 else None
    cf = M.cash_flow(y) if y > 2022 else None
    ia, ta = M.fixed_assets("intang")[y], M.fixed_assets("tang")[y]
    ia0 = M.fixed_assets("intang")[y - 1] if y > 2022 else None
    ta0 = M.fixed_assets("tang")[y - 1] if y > 2022 else None
    approved = f"28/04/{y + 1}"
    d = Doc(path, f"Bilancio d'esercizio al 31/12/{y} - {co['short']}", f"{co['name']} - Partita IVA {co['vat']}", f"Bilancio d'esercizio al 31/12/{y}")
    W = d.width / 2.8346                                                   # larghezza utile in mm

    def v(cur: int, prev) -> List[str]:
        return [U(cur), U(prev) if prev is not None else ""]

    # ------------------------------------------------------------------ frontespizio
    d.title_block(f"BILANCIO DI ESERCIZIO AL 31/12/{y}", f"{co['name']}")
    d.table([["Denominazione", co["name"]], ["Forma giuridica", co["legal_form"]], ["Sede legale", f"{co['street']}, {co['zip']} {co['city'].title()} ({co['prov']})"],
             ["Codice fiscale e partita IVA", co["vat"]], ["Numero REA", co["rea"]], ["Capitale sociale", f"euro {U(co['capital'])} interamente versato"],
             ["Codice ATECO prevalente", f"{co['ateco']} - {co['ateco_desc']}"], ["Esercizio", f"dal 01/01/{y} al 31/12/{y}"],
             ["Forma del bilancio", "Ordinaria, ai sensi degli artt. 2423 e seguenti del codice civile (non si applica l'art. 2435-bis)"],
             ["Unità di misura", "Euro, senza cifre decimali; il conto economico analitico (Allegato A) è espresso in euro e centesimi"],
             ["Organo amministrativo", "Amministratore unico: Giulia Ferraris"], ["Approvazione", f"Assemblea ordinaria dei soci del {approved}"]], [52, W - 52], head=False, align_right_from=9, zebra=True)
    d.H1("Indice del fascicolo")
    d.B(["Stato patrimoniale (attivo e passivo)", "Conto economico", "Rendiconto finanziario (metodo indiretto)", "Nota integrativa (criteri, movimenti, composizione delle voci, imposte, personale)", "Relazione sulla gestione (riclassificazioni, indicatori, rischi)",
         f"Verbale di approvazione dell'assemblea del {approved}", "Allegato A - Conto economico analitico per conti", "Allegato B - Stato patrimoniale analitico per conti", "Allegato C - Bilancio di verifica", "Allegato D - Partitario clienti",
         "Allegato E - Partitario fornitori", "Allegato F - Registro dei cespiti e piano di ammortamento", "Allegato G - Andamento mensile dell'esercizio", "Allegato H - Liquidazioni IVA periodiche", "Ricevuta di deposito e dichiarazione di conformità"])
    d.P(f"Il presente fascicolo è stato predisposto dall'organo amministrativo sulla base delle scritture contabili al 31/12/{y}, regolarmente tenute, e verrà depositato presso il Registro delle Imprese di Torino nei termini di legge, "
        "in formato elettronico secondo la tassonomia XBRL in vigore.")
    d.page_break()

    # ------------------------------------------------------------------ stato patrimoniale
    d.title_block("STATO PATRIMONIALE", f"Situazione al 31/12/{y} con confronto al 31/12/{y - 1}")
    hdr = ["ATTIVO", f"31/12/{y}", f"31/12/{y - 1}"]
    cw = [W - 64, 32, 32]

    def val(key):
        return [U(b[key]), U(b0[key]) if b0 else ""]

    def cls(rows, idx):
        return [U(rows[idx]["net_close"]), U(ia0[idx]["net_close"]) if ia0 else ""]

    def clt(rows, rows0, idxs):
        return [U(sum(rows[i]["net_close"] for i in idxs)), U(sum(rows0[i]["net_close"] for i in idxs)) if rows0 else ""]

    d.statement([
        ("A) CREDITI VERSO SOCI PER VERSAMENTI ANCORA DOVUTI", ["-", "-"], 0, True),
        ("B) IMMOBILIZZAZIONI", ["", ""], 0, True),
        ("I - Immobilizzazioni immateriali", ["", ""], 1, True),
        ("1) costi di impianto e di ampliamento", ["-", "-"], 2, False),
        ("2) costi di sviluppo", cls(ia, 0), 2, False),
        ("3) diritti di brevetto industriale e diritti di utilizzazione delle opere dell'ingegno", cls(ia, 1), 2, False),
        ("4) concessioni, licenze, marchi e diritti simili", cls(ia, 2), 2, False),
        ("7) altre", cls(ia, 3), 2, False),
        ("Totale immobilizzazioni immateriali", val("intang"), 1, True),
        ("II - Immobilizzazioni materiali", ["", ""], 1, True),
        ("2) impianti e macchinario", clt(ta, ta0, [0]), 2, False),
        ("3) attrezzature industriali e commerciali", clt(ta, ta0, [1]), 2, False),
        ("4) altri beni", clt(ta, ta0, [2, 3, 4]), 2, False),
        ("Totale immobilizzazioni materiali", val("tang"), 1, True),
        ("III - Immobilizzazioni finanziarie", ["", ""], 1, True),
        ("2) crediti - d-bis) verso altri (esigibili oltre l'esercizio successivo)", val("deposits"), 2, False),
        ("Totale immobilizzazioni finanziarie", val("deposits"), 1, True),
        ("Totale immobilizzazioni (B)", val("fixed"), 0, True),
        ("C) ATTIVO CIRCOLANTE", ["", ""], 0, True),
        ("I - Rimanenze", ["", ""], 1, True),
        ("3) lavori in corso su ordinazione", val("wip"), 2, False),
        ("Totale rimanenze", val("wip"), 1, True),
        ("II - Crediti", ["", ""], 1, True),
        ("1) verso clienti (esigibili entro l'esercizio successivo)", val("trade"), 2, False),
        ("5-bis) crediti tributari (esigibili entro l'esercizio successivo)", val("tax_cr"), 2, False),
        ("5-quater) verso altri (esigibili entro l'esercizio successivo)", val("other_cr"), 2, False),
        ("Totale crediti", val("receivables"), 1, True),
        ("IV - Disponibilità liquide", ["", ""], 1, True),
        ("1) depositi bancari e postali", val("cash_bank"), 2, False),
        ("3) danaro e valori in cassa", val("cash_cash"), 2, False),
        ("Totale disponibilità liquide", val("cash"), 1, True),
        ("Totale attivo circolante (C)", val("current"), 0, True),
        ("D) RATEI E RISCONTI", val("prepaid"), 0, True),
        ("TOTALE ATTIVO", val("assets"), 0, True),
    ], cw, hdr)
    d.page_break()
    d.statement([
        ("A) PATRIMONIO NETTO", val("pn"), 0, True),
        ("I - Capitale", val("pn_capital"), 1, False),
        ("IV - Riserva legale", val("pn_legal"), 1, False),
        ("VI - Altre riserve, distintamente indicate", ["", ""], 1, False),
        ("Riserva straordinaria", val("pn_extra"), 2, False),
        ("VIII - Utili (perdite) portati a nuovo", ["-", "-"], 1, False),
        ("IX - Utile (perdita) dell'esercizio", val("pn_net"), 1, False),
        ("Totale patrimonio netto", val("pn"), 0, True),
        ("B) FONDI PER RISCHI E ONERI", ["-", "-"], 0, True),
        ("C) TRATTAMENTO DI FINE RAPPORTO DI LAVORO SUBORDINATO", val("tfr"), 0, True),
        ("D) DEBITI", ["", ""], 0, True),
        ("4) debiti verso banche", ["", ""], 1, False),
        ("esigibili entro l'esercizio successivo", val("loan_short"), 2, False),
        ("esigibili oltre l'esercizio successivo", val("loan_long"), 2, False),
        ("7) debiti verso fornitori (esigibili entro l'esercizio successivo)", val("suppliers"), 1, False),
        ("12) debiti tributari (esigibili entro l'esercizio successivo)", val("tax_debt"), 1, False),
        ("13) debiti verso istituti di previdenza e di sicurezza sociale (esigibili entro l'esercizio successivo)", val("social"), 1, False),
        ("14) altri debiti (esigibili entro l'esercizio successivo)", val("other_debt"), 1, False),
        ("Totale debiti (D)", val("debts"), 0, True),
        ("E) RATEI E RISCONTI", val("accrued"), 0, True),
        ("TOTALE PASSIVO", val("liabilities"), 0, True),
    ], cw, ["PASSIVO", f"31/12/{y}", f"31/12/{y - 1}"])
    d.page_break()

    # ------------------------------------------------------------------ conto economico
    d.title_block("CONTO ECONOMICO", f"Esercizio {y} con confronto all'esercizio {y - 1}")

    def pv(key):
        return [U(p[key]), U(p0[key]) if p0 else ""]

    d.statement([
        ("A) VALORE DELLA PRODUZIONE", ["", ""], 0, True),
        ("1) ricavi delle vendite e delle prestazioni", pv("revenue"), 1, False),
        ("3) variazioni dei lavori in corso su ordinazione", pv("wip_delta"), 1, False),
        ("4) incrementi di immobilizzazioni per lavori interni", pv("capitalized"), 1, False),
        ("5) altri ricavi e proventi", ["", ""], 1, False),
        ("contributi in conto esercizio", pv("grants"), 2, False),
        ("altri", pv("other_income"), 2, False),
        ("Totale altri ricavi e proventi", [U(p["grants"] + p["other_income"]), U(p0["grants"] + p0["other_income"]) if p0 else ""], 2, True),
        ("Totale valore della produzione", pv("a_total"), 0, True),
        ("B) COSTI DELLA PRODUZIONE", ["", ""], 0, True),
        ("6) per materie prime, sussidiarie, di consumo e di merci", pv("b6"), 1, False),
        ("7) per servizi", pv("b7"), 1, False),
        ("8) per godimento di beni di terzi", pv("b8"), 1, False),
        ("9) per il personale", [U(p["b9a"] + p["b9b"] + p["b9c"] + p["b9e"]), U(p0["b9a"] + p0["b9b"] + p0["b9c"] + p0["b9e"]) if p0 else ""], 1, False),
        ("a) salari e stipendi", pv("b9a"), 2, False),
        ("b) oneri sociali", pv("b9b"), 2, False),
        ("c) trattamento di fine rapporto", pv("b9c"), 2, False),
        ("e) altri costi", pv("b9e"), 2, False),
        ("10) ammortamenti e svalutazioni", [U(p["b10a"] + p["b10b"] + p["b10d"]), U(p0["b10a"] + p0["b10b"] + p0["b10d"]) if p0 else ""], 1, False),
        ("a) ammortamento delle immobilizzazioni immateriali", pv("b10a"), 2, False),
        ("b) ammortamento delle immobilizzazioni materiali", pv("b10b"), 2, False),
        ("d) svalutazioni dei crediti compresi nell'attivo circolante e delle disponibilità liquide", pv("b10d"), 2, False),
        ("14) oneri diversi di gestione", pv("b14"), 1, False),
        ("Totale costi della produzione", pv("b_total"), 0, True),
        ("Differenza tra valore e costi della produzione (A - B)", pv("ebit"), 0, True),
        ("C) PROVENTI E ONERI FINANZIARI", ["", ""], 0, True),
        ("16) altri proventi finanziari - d) proventi diversi dai precedenti", pv("int_income"), 1, False),
        ("17) interessi e altri oneri finanziari - altri", [U(-p["int_expense"]), U(-p0["int_expense"]) if p0 else ""], 1, False),
        ("17-bis) utili e perdite su cambi", pv("fx"), 1, False),
        ("Totale proventi e oneri finanziari (15 + 16 - 17 +/- 17-bis)", pv("fin"), 0, True),
        ("D) RETTIFICHE DI VALORE DI ATTIVITA' E PASSIVITA' FINANZIARIE", ["-", "-"], 0, True),
        ("Risultato prima delle imposte (A - B +/- C +/- D)", pv("pre_tax"), 0, True),
        ("20) imposte sul reddito dell'esercizio, correnti, differite e anticipate", [U(-p["taxes"]), U(-p0["taxes"]) if p0 else ""], 1, False),
        ("imposte correnti (IRES e IRAP)", [U(-p["taxes"]), U(-p0["taxes"]) if p0 else ""], 2, False),
        ("21) UTILE (PERDITA) DELL'ESERCIZIO", pv("net"), 0, True),
    ], cw, ["", f"{y}", f"{y - 1}"])
    d.page_break()

    # ------------------------------------------------------------------ rendiconto finanziario
    if cf:
        cf0 = M.cash_flow(y - 1) if y > 2023 else None

        def c2(key, sign=1):
            return [U(sign * cf[key]), U(sign * cf0[key]) if cf0 else ""]
        d.title_block("RENDICONTO FINANZIARIO", f"Metodo indiretto - esercizio {y}" + (f" con confronto all'esercizio {y - 1}" if cf0 else ""))
        d.statement([
            ("A) Flussi finanziari derivanti dall'attività operativa (metodo indiretto)", ["", ""], 0, True),
            ("Utile (perdita) dell'esercizio", c2("net"), 1, False),
            ("Imposte sul reddito", c2("taxes"), 1, False),
            ("Interessi passivi/(attivi) e differenze cambio", c2("interest"), 1, False),
            ("1. Utile (perdita) dell'esercizio prima di imposte sul reddito, interessi, dividendi e plus/minusvalenze", c2("pre"), 1, True),
            ("Rettifiche per elementi non monetari che non hanno avuto contropartita nel capitale circolante netto", ["", ""], 1, False),
            ("Accantonamenti al TFR e svalutazione dei crediti", c2("provisions"), 2, False),
            ("Ammortamenti delle immobilizzazioni", c2("dep"), 2, False),
            ("2. Flusso finanziario prima delle variazioni del capitale circolante netto", c2("before_wc"), 1, True),
            ("Variazioni del capitale circolante netto", ["", ""], 1, False),
            ("Decremento/(incremento) delle rimanenze (lavori in corso)", c2("d_wip"), 2, False),
            ("Decremento/(incremento) dei crediti verso clienti", c2("d_trade"), 2, False),
            ("Incremento/(decremento) dei debiti verso fornitori", c2("d_suppliers"), 2, False),
            ("Decremento/(incremento) dei ratei e risconti attivi", c2("d_prepaid"), 2, False),
            ("Incremento/(decremento) dei ratei e risconti passivi", c2("d_accrued"), 2, False),
            ("Altre variazioni del capitale circolante netto", c2("d_other"), 2, False),
            ("3. Flusso finanziario dopo le variazioni del capitale circolante netto", c2("after_wc"), 1, True),
            ("Altre rettifiche", ["", ""], 1, False),
            ("Interessi incassati/(pagati)", c2("interest_paid"), 2, False),
            ("(Imposte sul reddito pagate)", c2("taxes_paid"), 2, False),
            ("(Utilizzo del TFR)", c2("tfr_used"), 2, False),
            ("Flusso finanziario dell'attività operativa (A)", c2("operating"), 0, True),
            ("B) Flussi finanziari derivanti dall'attività di investimento", ["", ""], 0, True),
            ("(Investimenti) in immobilizzazioni immateriali", c2("capex_intang"), 1, False),
            ("(Investimenti) in immobilizzazioni materiali", c2("capex_tang"), 1, False),
            ("(Investimenti) in immobilizzazioni finanziarie", c2("deposits"), 1, False),
            ("Flusso finanziario dell'attività di investimento (B)", c2("investing"), 0, True),
            ("C) Flussi finanziari derivanti dall'attività di finanziamento", ["", ""], 0, True),
            ("Accensione/(rimborso) finanziamenti a medio/lungo termine", c2("loan"), 1, False),
            ("(Dividendi e acconti su dividendi pagati)", c2("dividends"), 1, False),
            ("Flusso finanziario dell'attività di finanziamento (C)", c2("financing"), 0, True),
            ("Incremento (decremento) delle disponibilità liquide (A + B + C)", c2("change"), 0, True),
            ("Disponibilità liquide all'inizio dell'esercizio", c2("open"), 1, False),
            ("Disponibilità liquide alla fine dell'esercizio", c2("close"), 1, False),
        ], cw, ["", f"{y}", f"{y - 1}" if cf0 else ""])
    else:
        d.title_block("RENDICONTO FINANZIARIO", "Per il primo esercizio presentato il rendiconto non si redige: manca il bilancio comparativo di apertura nel presente fascicolo.")
    d.page_break()

    # ------------------------------------------------------------------ nota integrativa e relazione sulla gestione (moduli estesi)
    bil_nota.nota(d, y)
    d.page_break()
    bil_rel.relazione(d, y)
    d.page_break()
    prop = {2022: 40000, 2023: 60000, 2024: 80000, 2025: 90000}[y]

    # ------------------------------------------------------------------ verbale di assemblea
    d.title_block("VERBALE DI ASSEMBLEA ORDINARIA DEI SOCI", f"{co['name']} - approvazione del bilancio al 31/12/{y}")
    d.P(f"L'anno {y + 1}, il giorno 28 del mese di aprile, alle ore 10:30, presso la sede sociale in {co['city'].title()}, {co['street']}, si è riunita l'assemblea ordinaria dei soci della {co['short']}, con sede legale in {co['city'].title()} e capitale sociale di euro {U(co['capital'])}, "
        "per discutere e deliberare sul seguente ordine del giorno: 1) approvazione del bilancio dell'esercizio chiuso al 31/12 e relative relazioni; 2) destinazione del risultato dell'esercizio; 3) varie ed eventuali.")
    d.P("Assume la presidenza, a norma di statuto, l'amministratore unico Giulia Ferraris, la quale constata e fa constatare che: sono presenti i soci Giulia Ferraris, titolare di una quota pari al 60% del capitale sociale, e Marco Bertolotti, titolare di una quota pari al 40%, "
        "e quindi l'intero capitale sociale; l'assemblea è regolarmente costituita e atta a deliberare su quanto posto all'ordine del giorno. Funge da segretario, con il consenso degli intervenuti, il socio Marco Bertolotti.")
    d.P(f"Sul primo punto, il presidente illustra il bilancio al 31/12/{y}, composto da stato patrimoniale, conto economico, rendiconto finanziario e nota integrativa, e la relazione sulla gestione, evidenziando un utile di euro {U(p['net'])}. "
        "Dopo breve discussione, l'assemblea, all'unanimità, <b>delibera</b> di approvare il bilancio dell'esercizio nelle risultanze esposte dall'organo amministrativo.")
    d.P(f"Sul secondo punto, l'assemblea, all'unanimità, <b>delibera</b> di destinare l'utile dell'esercizio di euro {U(p['net'])} quanto a euro {U(prop)} a distribuzione di dividendi ai soci in proporzione alle rispettive quote e quanto a euro {U(p['net'] - prop)} a riserva straordinaria.")
    d.P("Null'altro essendovi da deliberare e nessuno chiedendo la parola, la riunione è sciolta alle ore 11:20, previa lettura e approvazione del presente verbale.")
    d.table([["Il Presidente", "Il Segretario"], ["Giulia Ferraris", "Marco Bertolotti"]], [W / 2, W / 2], align_right_from=9)
    d.page_break()

    # ------------------------------------------------------------------ allegati
    prop = {2022: 40000, 2023: 60000, 2024: 80000, 2025: 90000}[y]
    d.page_break()
    bil_all.allegato_a(d, y)
    d.page_break()
    bil_all.allegato_b(d, y)
    d.page_break()
    bil_all.allegato_c(d, y)
    d.page_break()
    bil_all.allegato_clienti(d, y)
    d.page_break()
    bil_all.allegato_fornitori(d, y)
    d.page_break()
    bil_all.allegato_cespiti(d, y)
    d.page_break()
    bil_all.allegato_mensili(d, y)
    d.page_break()
    bil_all.allegato_iva(d, y)
    d.page_break()
    deposito(d, y, W)
    return d.save()


def deposito(d: Doc, y: int, W: float) -> None:
    co = M.COMPANY
    d.title_block("RICEVUTA DI DEPOSITO E DICHIARAZIONE DI CONFORMITA'", f"Bilancio d'esercizio al 31/12/{y} - deposito presso il Registro delle Imprese di Torino")
    d.table([["Dato", "Valore"], ["Società", co["name"]], ["Esercizio", f"01/01/{y} - 31/12/{y}"], ["Formato di deposito", "XBRL con tassonomia vigente, firmato digitalmente dal legale rappresentante"],
             ["Protocollo di deposito", f"TO-{y + 1}-00{40000 + y * 3 % 9999}"], ["Data di approvazione", f"28/04/{y + 1}"], ["Data di deposito", f"{(29 if y % 2 else 30)}/05/{y + 1}"], ["Diritti di segreteria e imposta di bollo", "Assolti con addebito sul conto Telemaco"],
             ["Esito del controllo formale", "Accettato"]], [58, W - 58], head=False, align_right_from=9, zebra=True)
    d.P("<b>Dichiarazione di conformità.</b> Il sottoscritto Giulia Ferraris, in qualità di amministratore unico, dichiara che il presente documento informatico è conforme ai documenti originali depositati presso la società. "
        "Il fascicolo comprende lo stato patrimoniale, il conto economico, il rendiconto finanziario, la nota integrativa, la relazione sulla gestione, il verbale di approvazione e gli allegati analitici di supporto (non soggetti a deposito).", left=True)
    d.small("Documento di prova: protocolli, date e importi sono inventati; nessun valore corrisponde a persone o imprese reali.")
