"""Il bilancio d'esercizio in forma ordinaria (art. 2423 e seguenti c.c.): stato patrimoniale, conto economico, rendiconto finanziario, nota integrativa,
relazione sulla gestione, verbale dell'assemblea e allegato con il conto economico analitico. Come lo consegna uno studio, per ogni esercizio."""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

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
    d.B(["Stato patrimoniale (attivo e passivo)", "Conto economico", "Rendiconto finanziario (metodo indiretto)", "Nota integrativa", "Relazione sulla gestione",
         f"Verbale di approvazione dell'assemblea del {approved}", "Allegato A - Conto economico analitico per conti"])
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

    # ------------------------------------------------------------------ nota integrativa
    d.title_block("NOTA INTEGRATIVA", f"al bilancio chiuso il 31/12/{y}")
    d.H1("1. Premessa e struttura del bilancio")
    d.P(f"Il bilancio dell'esercizio chiuso al 31/12/{y}, di cui la presente nota integrativa costituisce parte integrante ai sensi dell'art. 2423 c.c., è stato redatto in conformità alle disposizioni degli articoli 2423 e seguenti del codice civile, "
        "interpretate e integrate dai principi contabili nazionali emanati dall'Organismo Italiano di Contabilità (OIC) nella versione vigente. Lo stato patrimoniale e il conto economico sono redatti secondo gli schemi degli artt. 2424 e 2425 c.c. "
        "e il rendiconto finanziario secondo l'art. 2425-ter c.c. e l'OIC 10. La società, pur avendo i requisiti dimensionali per redigere il bilancio in forma abbreviata ai sensi dell'art. 2435-bis c.c., ha scelto di redigerlo in forma ordinaria "
        "per fornire un'informativa più completa ai soci e agli istituti di credito.")
    d.P("Il bilancio è espresso in unità di euro, senza cifre decimali, ai sensi dell'art. 2423 c.c.; le differenze di arrotondamento sono state riportate nella voce di patrimonio netto «Riserva straordinaria» e, ove necessario, tra gli altri ricavi o costi. "
        "Per ogni voce dello stato patrimoniale e del conto economico è indicato l'importo dell'esercizio precedente, perfettamente comparabile: nell'esercizio non si sono verificati casi eccezionali che abbiano reso necessaria una deroga ai sensi dell'art. 2423, comma 5, c.c.")
    d.H1("2. Criteri di valutazione")
    d.P("I criteri di valutazione sono ispirati ai principi generali di prudenza, competenza economica e prospettiva della continuazione dell'attività, tenendo conto della funzione economica dell'elemento dell'attivo o del passivo considerato (art. 2423-bis c.c.). "
        "I criteri applicati non sono variati rispetto all'esercizio precedente. Si illustrano di seguito i principali.")
    d.P("<b>Immobilizzazioni immateriali.</b> Sono iscritte al costo di acquisto o di produzione, comprensivo degli oneri accessori, e ammortizzate in quote costanti in relazione alla residua possibilità di utilizzazione. "
        "I costi di sviluppo, relativi alla piattaforma software prodotta internamente, sono capitalizzati quando il progetto è chiaramente definito, i costi sono identificabili e misurabili, il prodotto è tecnicamente realizzabile e vi è la prospettiva di ricavi futuri; "
        "sono ammortizzati in cinque anni a partire dal momento in cui il prodotto è commercializzabile. Il software applicativo acquistato è ammortizzato in tre anni, le licenze e i marchi in cinque anni, le migliorie su beni di terzi in base alla minore tra la durata residua del contratto di locazione e la vita utile.")
    d.P("<b>Immobilizzazioni materiali.</b> Sono iscritte al costo di acquisto, comprensivo degli oneri accessori di diretta imputazione, e sono sistematicamente ammortizzate in ogni esercizio sulla base di aliquote economico-tecniche determinate in relazione alla residua possibilità di utilizzazione dei beni. "
        "Le aliquote applicate sono: impianti e macchinario 15%; attrezzature industriali e commerciali (server e apparati di test) 20%; macchine d'ufficio elettroniche 20%; mobili e arredi 12%; autovetture e mezzi di trasporto interni 25%. "
        "Nell'esercizio di entrata in funzione dei beni l'aliquota è ridotta alla metà, ritenendo che ciò approssimi adeguatamente l'utilizzo effettivo. I costi di manutenzione ordinaria sono imputati integralmente al conto economico.")
    d.P("<b>Immobilizzazioni finanziarie.</b> Sono costituite da depositi cauzionali versati a fronte del contratto di locazione della sede, iscritti al valore nominale che coincide con il presumibile valore di realizzo.")
    d.P("<b>Rimanenze.</b> I lavori in corso su ordinazione si riferiscono a commesse di sviluppo software di durata infrannuale non ancora ultimate alla data di bilancio e sono valutati al costo di produzione sostenuto (personale diretto, costi di terzi direttamente imputabili e quota di costi generali di produzione), "
        "senza rilevazione di margini, in quanto le commesse hanno durata inferiore a dodici mesi.")
    d.P("<b>Crediti.</b> Sono iscritti al presumibile valore di realizzo, ottenuto rettificando il valore nominale con un fondo svalutazione stimato sulla base dell'anzianità dei crediti e delle perdite attese. Data la scadenza inferiore a dodici mesi e l'irrilevanza degli effetti, non si è applicato il criterio del costo ammortizzato né l'attualizzazione.")
    d.P("<b>Disponibilità liquide, ratei e risconti.</b> Le disponibilità liquide sono iscritte al valore nominale. I ratei e i risconti sono determinati secondo il principio della competenza economica e temporale, mediante la ripartizione di costi e proventi comuni a due o più esercizi.")
    d.P("<b>Trattamento di fine rapporto.</b> Rappresenta l'effettivo debito maturato verso i dipendenti in conformità alla legge e ai contratti di lavoro vigenti, al netto degli acconti erogati e delle quote destinate alla previdenza complementare e al Fondo di Tesoreria dell'INPS.")
    d.P("<b>Debiti.</b> Sono rilevati al valore nominale, che coincide con il valore di estinzione; i debiti scadenti oltre i dodici mesi, derivanti da un finanziamento a tasso di mercato, non sono stati attualizzati per l'irrilevanza degli effetti.")
    d.P("<b>Ricavi e costi.</b> I ricavi per servizi e per canoni sono rilevati secondo il principio di competenza, in base al periodo di effettiva fruizione da parte del cliente; i ricavi per sviluppi su commessa sono rilevati alla consegna e accettazione del lavoro. Costi e ricavi sono esposti al netto di resi, sconti, abbuoni e premi.")
    d.P("<b>Imposte sul reddito.</b> Sono stanziate in base alla previsione dell'onere fiscale corrente (IRES e IRAP) applicando le aliquote vigenti, tenendo conto delle esenzioni e delle agevolazioni applicabili. Non sono state rilevate imposte differite o anticipate in quanto le differenze temporanee sono irrilevanti.")

    d.H1("3. Movimenti delle immobilizzazioni")
    d.H2(f"Immobilizzazioni immateriali (esercizio {y})")
    rows = [["Classe", "Costo storico 1/1", "Fondo amm.to 1/1", "Valore netto 1/1", "Acquisizioni", "Ammortamento", "Valore netto 31/12"]]
    for k, r in enumerate(ia):
        rows.append([M.INTANG_CLASSES[k][0], U(r["cost_open"]), U(r["fund_open"]), U(r["net_open"]), U(r["capex"]), U(-r["dep"]), U(r["net_close"])])
    rows.append(["Totale", U(sum(r["cost_open"] for r in ia)), U(sum(r["fund_open"] for r in ia)), U(sum(r["net_open"] for r in ia)), U(sum(r["capex"] for r in ia)), U(-sum(r["dep"] for r in ia)), U(sum(r["net_close"] for r in ia))])
    d.table(rows, [W - 96, 16, 16, 16, 16, 16, 16], bold_rows=[len(rows) - 1], font=7.6)
    d.small(f"Le acquisizioni di «Costi di sviluppo» ({U(ia[0]['capex'])} euro) sono i costi sostenuti per lo sviluppo interno della piattaforma Atlas (personale dedicato e consulenze tecniche), capitalizzati con contropartita la voce A.4 del conto economico.")
    d.H2(f"Immobilizzazioni materiali (esercizio {y})")
    rows = [["Classe", "Costo storico 1/1", "Fondo amm.to 1/1", "Valore netto 1/1", "Acquisizioni", "Ammortamento", "Valore netto 31/12"]]
    for k, r in enumerate(ta):
        rows.append([M.TANG_CLASSES[k][0], U(r["cost_open"]), U(r["fund_open"]), U(r["net_open"]), U(r["capex"]), U(-r["dep"]), U(r["net_close"])])
    rows.append(["Totale", U(sum(r["cost_open"] for r in ta)), U(sum(r["fund_open"] for r in ta)), U(sum(r["net_open"] for r in ta)), U(sum(r["capex"] for r in ta)), U(-sum(r["dep"] for r in ta)), U(sum(r["net_close"] for r in ta))])
    d.table(rows, [W - 96, 16, 16, 16, 16, 16, 16], bold_rows=[len(rows) - 1], font=7.6)
    d.P(f"Nell'esercizio non sono state effettuate cessioni né rivalutazioni di immobilizzazioni, né svalutazioni per perdite durevoli di valore. Le immobilizzazioni finanziarie ({U(b['deposits'])} euro) sono invariate: depositi cauzionali versati al locatore della sede di via Garibaldi.")

    d.H1("4. Attivo circolante, ratei e risconti")
    d.P(f"<b>Lavori in corso su ordinazione.</b> Ammontano a {U(b['wip'])} euro (esercizio precedente: {U(b0['wip']) if b0 else U(M.WIP[0])}) e si riferiscono a {3 + y % 3} commesse in corso di esecuzione al 31/12/{y}, tutte con consegna prevista entro il primo semestre dell'esercizio successivo.")
    d.H2("Crediti dell'attivo circolante")
    rows = [["Voce", f"31/12/{y}", f"31/12/{y - 1}", "Variazione", "Entro 12 mesi", "Oltre 12 mesi"]]
    for label, key in [("Crediti verso clienti", "trade"), ("Crediti tributari", "tax_cr"), ("Crediti verso altri", "other_cr")]:
        rows.append([label, U(b[key]), U(b0[key]) if b0 else "", U(b[key] - b0[key]) if b0 else "", U(b[key]), "-"])
    rows.append(["Totale crediti", U(b["receivables"]), U(b0["receivables"]) if b0 else "", U(b["receivables"] - b0["receivables"]) if b0 else "", U(b["receivables"]), "-"])
    d.table(rows, [W - 100, 20, 20, 20, 20, 20], bold_rows=[len(rows) - 1])
    invoiced = b["trade"] - b["trade_invoices_to_issue"]
    d.P(f"I crediti verso clienti ({U(b['trade'])} euro) sono composti da fatture emesse per {U(invoiced + round(b['trade'] * 0.0125))} euro, da fatture da emettere per {U(b['trade_invoices_to_issue'])} euro "
        f"e sono esposti al netto di un fondo svalutazione crediti di {U(round(b['trade'] * 0.0125))} euro, movimentato nell'esercizio per l'accantonamento di {U(p['b10d'])} euro iscritto alla voce B.10.d del conto economico. "
        "La ripartizione geografica dei crediti verso clienti è la seguente: Italia 86%, altri Paesi dell'Unione Europea 10%, extra Unione Europea 4%.")
    d.P(f"I crediti tributari ({U(b['tax_cr'])} euro) comprendono il credito d'imposta per attività di ricerca e sviluppo maturato sugli investimenti dell'esercizio, da utilizzare in compensazione orizzontale in F24, e il credito IVA. "
        "I crediti verso altri sono costituiti da anticipi a fornitori e da anticipi ai dipendenti per trasferte.")
    d.P(f"<b>Disponibilità liquide.</b> Ammontano a {U(b['cash'])} euro (esercizio precedente: {U(b0['cash']) if b0 else '-'}) e sono costituite da saldi attivi di conto corrente presso due istituti di credito per {U(b['cash_bank'])} euro e da denaro in cassa per {U(b['cash_cash'])} euro. "
        "Non vi sono vincoli sulle disponibilità liquide.")
    d.P(f"<b>Ratei e risconti attivi.</b> Ammontano a {U(b['prepaid'])} euro e si riferiscono per il 58% a risconti su licenze software e servizi cloud con competenza dell'esercizio successivo, per il 24% a premi assicurativi e per il restante 18% a canoni di locazione operativa anticipati. "
        "Non vi sono ratei e risconti con durata superiore a cinque anni.")

    d.H1("5. Patrimonio netto")
    prev_net = p0["net"] if p0 else None
    div = M.DIVIDENDS.get(y, 0)
    rows = [["", "Capitale", "Riserva legale", "Riserva straordinaria", "Utile dell'esercizio", "Totale"]]
    if b0:
        rows.append([f"Saldo al 31/12/{y - 1}", U(b0["pn_capital"]), U(b0["pn_legal"]), U(b0["pn_extra"]), U(b0["pn_net"]), U(b0["pn"])])
        rows.append([f"Destinazione dell'utile {y - 1}: dividendi distribuiti", "-", "-", "-", U(-div), U(-div)])
        rows.append([f"Destinazione dell'utile {y - 1}: a riserva straordinaria", "-", "-", U(prev_net - div), U(-(prev_net - div)), "-"])
        rows.append([f"Utile dell'esercizio {y}", "-", "-", "-", U(p["net"]), U(p["net"])])
    else:
        rows.append(["Saldo al 31/12/2022", U(b["pn_capital"]), U(b["pn_legal"]), U(b["pn_extra"]), U(b["pn_net"]), U(b["pn"])])
    rows.append([f"Saldo al 31/12/{y}", U(b["pn_capital"]), U(b["pn_legal"]), U(b["pn_extra"]), U(b["pn_net"]), U(b["pn"])])
    d.table(rows, [W - 100, 20, 20, 20, 20, 20], bold_rows=[len(rows) - 1])
    d.P(f"Il capitale sociale, pari a {U(b['pn_capital'])} euro, è suddiviso in due quote: Giulia Ferraris, 60% (30.000 euro), e Marco Bertolotti, 40% (20.000 euro). La riserva legale ha raggiunto il quinto del capitale sociale (art. 2430 c.c.) e non è più alimentata. "
        "La riserva straordinaria è libera e disponibile per ogni utilizzo, inclusi aumenti di capitale e distribuzione ai soci; non sono presenti riserve di rivalutazione né riserve in sospensione d'imposta.")

    d.H1("6. Trattamento di fine rapporto e debiti")
    tfr_used = (b0["tfr"] if b0 else 0) + p["b9c"] - b["tfr"]
    if b0:
        d.table([["Movimentazione del fondo TFR", "Importo"], [f"Saldo al 31/12/{y - 1}", U(b0["tfr"])], ["Accantonamento dell'esercizio (B.9.c)", U(p["b9c"])],
                 ["Utilizzi per dimissioni, anticipazioni, imposta sostitutiva e previdenza complementare", U(-tfr_used)], [f"Saldo al 31/12/{y}", U(b["tfr"])]], [W - 30, 30], bold_rows=[4])
    d.H2("Debiti")
    rows = [["Voce", f"31/12/{y}", f"31/12/{y - 1}", "Variazione", "Entro 12 mesi", "Oltre 12 mesi"]]
    for label, key, short, long_ in [("Debiti verso banche", "loan", "loan_short", "loan_long"), ("Debiti verso fornitori", "suppliers", "suppliers", None), ("Debiti tributari", "tax_debt", "tax_debt", None),
                                     ("Debiti verso istituti di previdenza", "social", "social", None), ("Altri debiti", "other_debt", "other_debt", None)]:
        rows.append([label, U(b[key]), U(b0[key]) if b0 else "", U(b[key] - b0[key]) if b0 else "", U(b[short]), U(b[long_]) if long_ else "-"])
    rows.append(["Totale debiti", U(b["debts"]), U(b0["debts"]) if b0 else "", U(b["debts"] - b0["debts"]) if b0 else "", U(b["debts"] - b["loan_long"]), U(b["loan_long"])])
    d.table(rows, [W - 100, 20, 20, 20, 20, 20], bold_rows=[len(rows) - 1])
    d.P(f"I debiti verso banche ({U(b['loan'])} euro) sono rappresentati dal residuo di un finanziamento chirografario, originariamente di 300.000 euro, concesso da un primario istituto di credito con piano di ammortamento a rate trimestrali, tasso variabile (Euribor a tre mesi più 2,10 punti) e scadenza il 31/12/2027; "
        f"la quota esigibile entro l'esercizio successivo è di {U(b['loan_short'])} euro. Non sono presenti debiti assistiti da garanzie reali né debiti in valuta rilevanti.")
    d.P(f"I debiti tributari ({U(b['tax_debt'])} euro) comprendono ritenute IRPEF su redditi di lavoro dipendente e autonomo per {U(b['withheld'])} euro, IVA a debito di dicembre per {U(b['vat_due'])} euro, saldo IRES per {U(b['ires_due'])} euro e saldo IRAP per {U(b['irap_due'])} euro, al netto degli acconti versati. "
        f"I debiti verso istituti di previdenza ({U(b['social'])} euro) sono i contributi INPS e INAIL di dicembre, versati nei termini di legge. Gli altri debiti ({U(b['other_debt'])} euro) sono i debiti verso dipendenti per retribuzioni di dicembre ({U(b['employees_debt'])} euro) "
        f"e per ferie, permessi e ratei di mensilità aggiuntive maturati e non goduti ({U(b['holidays'])} euro). I ratei passivi ({U(b['accrued'])} euro) si riferiscono a interessi passivi e utenze di competenza dell'esercizio.")
    d.P("<b>Impegni, garanzie e passività potenziali.</b> Non vi sono impegni, garanzie o passività potenziali non risultanti dallo stato patrimoniale, salvo i canoni residui dei contratti di locazione operativa di autovetture e apparecchiature informatiche, "
        f"pari a {U(round((M.acct('Canoni di locazione operativa autovetture', y) + M.acct('Canoni di locazione operativa apparecchiature', y)) * 2.1))} euro complessivi, di cui entro i dodici mesi successivi {U(M.acct('Canoni di locazione operativa autovetture', y) + M.acct('Canoni di locazione operativa apparecchiature', y))} euro.")

    d.H1("7. Conto economico")
    d.H2("Ricavi delle vendite e delle prestazioni per categoria di attività")
    i = M._i(y)
    rows = [["Categoria di attività", f"{y}", f"{y - 1}" if p0 else "", "Variazione"]]
    tot_cur = tot_prev = 0
    parts_cur = M._alloc(p["revenue"], [s[1][i] / 100 for s in M.REVENUE_SPLIT])
    parts_prev = M._alloc(p0["revenue"], [s[1][i - 1] / 100 for s in M.REVENUE_SPLIT]) if p0 else [0] * len(M.REVENUE_SPLIT)
    for k, (label, _) in enumerate(M.REVENUE_SPLIT):
        rows.append([label, U(parts_cur[k]), U(parts_prev[k]) if p0 else "", U(parts_cur[k] - parts_prev[k]) if p0 else ""])
    rows.append(["Totale ricavi delle vendite e delle prestazioni", U(p["revenue"]), U(p0["revenue"]) if p0 else "", U(p["revenue"] - p0["revenue"]) if p0 else ""])
    d.table(rows, [W - 90, 30, 30, 30], bold_rows=[len(rows) - 1])
    d.P("Per area geografica, i ricavi dell'esercizio sono realizzati per l'88% in Italia (Piemonte 54%, Lombardia 21%, altre regioni 13%), per il 9% in altri Paesi dell'Unione Europea e per il 3% extra Unione Europea. "
        "Nessun cliente ha superato il 12% dei ricavi complessivi; i primi cinque clienti rappresentano il 31% del fatturato.")
    d.H2("Altri ricavi e proventi e aiuti di Stato ricevuti")
    d.P(f"Gli altri ricavi e proventi comprendono contributi in conto esercizio per {U(p['grants'])} euro, rappresentati dal credito d'imposta per attività di ricerca e sviluppo (art. 1, commi 198-206, L. 160/2019) maturato sulle spese di sviluppo della piattaforma, "
        f"e altri proventi per {U(p['other_income'])} euro (rimborsi assicurativi, recuperi di spese e sopravvenienze attive ordinarie).")
    aid_rows = [["Soggetto erogante", "Misura", "Data", "Importo (euro)", "Regime"], ["Agenzia delle Entrate", "Credito d'imposta ricerca e sviluppo", f"31/12/{y}", U(p["grants"]), "Credito d'imposta"]]
    if y == 2024:
        aid_rows.append(["Camera di Commercio di Torino", "Voucher digitalizzazione PMI", "12/04/2024", U(10000), "De minimis"])
    if y == 2025:
        aid_rows.append(["Regione Piemonte", "Contributo partecipazione a fiere", "03/10/2025", U(6500), "De minimis"])
    d.P("Ai sensi dell'art. 1, commi 125-129, della legge 124/2017, si espongono i contributi e gli aiuti pubblici incassati o concessi nell'esercizio:")
    d.table(aid_rows, [48, 56, 22, 24, W - 150], align_right_from=3)
    d.H2("Costi della produzione")
    d.P(f"I costi per servizi ({U(p['b7'])} euro) comprendono consulenze tecniche, legali e fiscali, compensi a collaboratori esterni, licenze e servizi cloud, utenze, assicurazioni, pubblicità, formazione e spese di rappresentanza; il dettaglio per conto è nell'Allegato A. "
        f"I costi per godimento di beni di terzi ({U(p['b8'])} euro) sono costituiti dal canone di locazione della sede e dai canoni di locazione operativa di autovetture e apparecchiature. "
        f"Il costo del personale ({U(p['b9a'] + p['b9b'] + p['b9c'] + p['b9e'])} euro) comprende retribuzioni, contributi previdenziali e assistenziali, TFR e ferie maturate, e include i costi del personale dedicato allo sviluppo interno, "
        f"capitalizzati per {U(p['capitalized'])} euro tra le immobilizzazioni immateriali mediante la voce A.4. Gli oneri diversi di gestione ({U(p['b14'])} euro) sono costituiti da imposte indirette, quote associative, liberalità e sopravvenienze passive ordinarie.")
    d.H2("Proventi e oneri finanziari")
    d.P(f"Gli interessi e altri oneri finanziari ({U(p['int_expense'])} euro) sono quasi interamente relativi agli interessi sul finanziamento chirografario ({U(round(p['int_expense'] * 0.86))} euro) e, per il resto, a commissioni su affidamenti e interessi di mora fornitori. "
        f"I proventi finanziari ({U(p['int_income'])} euro) sono interessi attivi di conto corrente. Le differenze di cambio nette sono di {U(p['fx'])} euro e si riferiscono a fatture in dollari e sterline non rilevanti.")

    d.H1("8. Imposte sul reddito")
    t = p["tax"]
    rows = [["Riconciliazione tra onere fiscale teorico ed effettivo (IRES)", "Imponibile", "Imposta"], ["Risultato prima delle imposte", U(p["pre_tax"]), ""], ["Onere fiscale teorico (aliquota 24%)", "", U(t["theoretical"])]]
    for label, amount in t["up"].items():
        rows.append([f"Variazioni in aumento: {label}", U(amount), ""])
    for label, amount in t["down"].items():
        rows.append([f"Variazioni in diminuzione: {label}", U(-amount), ""])
    rows.append(["Imponibile IRES", U(t["taxable"]), ""])
    rows.append(["IRES corrente dell'esercizio (aliquota 24%)", "", U(t["ires"])])
    rows.append([f"IRAP: base imponibile e imposta (aliquota 3,90%, Regione Piemonte)", U(t["irap_base"]), U(t["irap"])])
    rows.append(["Totale imposte correnti a conto economico", "", U(p["taxes"])])
    d.table(rows, [W - 56, 28, 28], bold_rows=[len(rows) - 1])
    d.P("Ai fini IRAP, per effetto della deduzione integrale del costo del personale a tempo indeterminato, la base imponibile coincide con la differenza tra valore e costi della produzione. Non sono state rilevate imposte anticipate o differite per irrilevanza delle differenze temporanee.")

    d.H1("9. Altre informazioni")
    q, imp, app = M.HEADCOUNT_SPLIT[y]
    d.table([["Numero medio dei dipendenti per categoria", f"{y}", f"{y - 1}" if y > 2022 else ""],
             ["Quadri", str(q), str(M.HEADCOUNT_SPLIT[y - 1][0]) if y > 2022 else ""], ["Impiegati", str(imp), str(M.HEADCOUNT_SPLIT[y - 1][1]) if y > 2022 else ""],
             ["Apprendisti", str(app), str(M.HEADCOUNT_SPLIT[y - 1][2]) if y > 2022 else ""], ["Totale dipendenti", str(M.EMPLOYEES[y]), str(M.EMPLOYEES[y - 1]) if y > 2022 else ""]], [W - 60, 30, 30], bold_rows=[4])
    d.P(f"Numero medio dei dipendenti {M.EMPLOYEES[y]}. Ai dipendenti è applicato il CCNL Commercio, Terziario Distribuzione e Servizi. L'organo amministrativo è composto dall'amministratore unico, che non percepisce compensi in tale qualità ed è retribuito come quadro dirigente; "
        "la società non è soggetta a revisione legale né è tenuta alla nomina di un organo di controllo, e nessun compenso è stato corrisposto a revisori o sindaci. Non sono stati concessi anticipazioni o crediti agli amministratori né sono state prestate garanzie a loro favore.")
    d.P("<b>Operazioni con parti correlate.</b> Non sono state poste in essere operazioni con parti correlate a condizioni diverse da quelle di mercato. <b>Accordi non risultanti dallo stato patrimoniale</b>: non ve ne sono. "
        "<b>Strumenti finanziari derivati</b>: la società non ha sottoscritto strumenti derivati. <b>Patrimoni e finanziamenti destinati a uno specifico affare</b>: non ve ne sono.")
    nxt = {2023: "nel mese di febbraio 2024 sono stati sottoscritti due nuovi contratti di sviluppo con enti pubblici locali per complessivi 180.000 euro; ", 2024: "nei primi mesi del 2025 è stata completata l'assunzione di due sviluppatori e di un data scientist; ",
           2025: "nei primi mesi del 2026 sono stati assunti due apprendisti e avviato il progetto di analisi predittiva dei costi per le PMI; "}.get(y, "")
    d.P(f"<b>Fatti di rilievo avvenuti dopo la chiusura dell'esercizio.</b> Dopo il 31/12/{y} {nxt or 'non si sono verificati fatti '}che non abbiano modificato la situazione patrimoniale e finanziaria della società né il risultato economico dell'esercizio.")
    d.H1("10. Proposta di destinazione dell'utile")
    prop = {2022: 40000, 2023: 60000, 2024: 80000, 2025: 90000}[y]
    d.P(f"L'organo amministrativo propone di destinare l'utile dell'esercizio, pari a euro {U(p['net'])}, quanto a euro {U(prop)} a dividendo ai soci in proporzione alle quote possedute e quanto a euro {U(p['net'] - prop)} a riserva straordinaria, "
        "la riserva legale avendo già raggiunto il limite previsto dall'art. 2430 c.c.")
    d.P(f"Torino, {approved.replace(str(y + 1), str(y + 1))}. L'Amministratore unico: Giulia Ferraris.", left=True)
    d.page_break()

    # ------------------------------------------------------------------ relazione sulla gestione
    d.title_block("RELAZIONE SULLA GESTIONE", f"dell'organo amministrativo al bilancio chiuso il 31/12/{y}")
    growth = (p["revenue"] / p0["revenue"] - 1) if p0 else None
    r = M.ratio_notes(y)
    d.H1("Condizioni operative e sviluppo dell'attività")
    d.P(f"Signori soci, l'esercizio {y} si chiude con un utile di {U(p['net'])} euro, dopo aver rilevato ammortamenti per {U(p['b10a'] + p['b10b'])} euro e imposte per {U(p['taxes'])} euro. "
        f"I ricavi delle vendite e delle prestazioni sono stati pari a {U(p['revenue'])} euro" + (f", in crescita del {pct(growth)} rispetto ai {U(p0['revenue'])} euro del {y - 1}" if growth is not None else "") +
        ". La società opera nello sviluppo di software e di piattaforme di analisi dei dati per piccole e medie imprese e per enti pubblici locali, con sede a Torino, e nell'esercizio ha proseguito il percorso di crescita sia dei ricavi ricorrenti da licenze e abbonamenti sia dell'attività di sviluppo su commessa.")
    d.P("Il mercato di riferimento ha confermato una domanda sostenuta di digitalizzazione dei processi e di analisi dei dati da parte delle imprese di piccola dimensione, sostenuta anche dagli incentivi pubblici alla transizione digitale. "
        "La concorrenza resta frammentata e si sta spostando verso piattaforme verticali; la società ha risposto investendo nello sviluppo di un prodotto proprietario e nella formazione del personale.")
    d.H1("Andamento della gestione e principali indicatori")
    d.table([["Indicatore", f"{y}", f"{y - 1}" if y > 2022 else ""],
             ["Valore della produzione", U(p["a_total"]), U(p0["a_total"]) if p0 else ""], ["Margine operativo lordo (EBITDA)", U(r["ebitda"]), U(M.ratio_notes(y - 1)["ebitda"]) if p0 else ""],
             ["Risultato operativo (EBIT)", U(p["ebit"]), U(p0["ebit"]) if p0 else ""], ["Utile dell'esercizio", U(p["net"]), U(p0["net"]) if p0 else ""],
             ["ROS (EBIT / ricavi)", pct(r["ros"]), pct(M.ratio_notes(y - 1)["ros"]) if p0 else ""], ["ROE (utile / patrimonio netto iniziale)", pct(r["roe"]), pct(M.ratio_notes(y - 1)["roe"]) if p0 else ""],
             ["ROI (EBIT / totale attivo)", pct(r["roi"]), pct(M.ratio_notes(y - 1)["roi"]) if p0 else ""],
             ["Indice di liquidità (attivo corrente / debiti a breve)", f"{r['current_ratio']:.2f}".replace(".", ","), f"{M.ratio_notes(y - 1)['current_ratio']:.2f}".replace(".", ",") if p0 else ""],
             ["Debiti / patrimonio netto", f"{r['debt_equity']:.2f}".replace(".", ","), f"{M.ratio_notes(y - 1)['debt_equity']:.2f}".replace(".", ",") if p0 else ""]], [W - 60, 30, 30])
    d.H1("Investimenti, personale e attività di ricerca e sviluppo")
    d.P(f"Nell'esercizio sono stati effettuati investimenti in immobilizzazioni immateriali per {U(sum(x['capex'] for x in ia))} euro e in immobilizzazioni materiali per {U(sum(x['capex'] for x in ta))} euro, in prevalenza macchine d'ufficio elettroniche, server e apparati di test. "
        f"L'organico medio è passato a {M.EMPLOYEES[y]} unità" + (f" dalle {M.EMPLOYEES[y - 1]} dell'esercizio precedente" if y > 2022 else "") + ", con un costo complessivo del personale di "
        f"{U(p['b9a'] + p['b9b'] + p['b9c'] + p['b9e'])} euro. L'attività di ricerca e sviluppo ha riguardato la piattaforma Atlas per l'analisi predittiva dei costi delle PMI; i costi sostenuti sono stati in parte capitalizzati ({U(p['capitalized'])} euro) e hanno dato diritto al credito d'imposta per ricerca e sviluppo "
        f"di {U(p['grants'])} euro. La società non possiede azioni proprie né quote di società controllanti e non ha filiali o sedi secondarie.")
    d.H1("Principali rischi e incertezze")
    d.B(["<b>Rischio di credito:</b> i clienti sono prevalentemente imprese e pubbliche amministrazioni italiane; l'esposizione è frazionata e monitorata con un fondo svalutazione prudenziale.",
         f"<b>Rischio di liquidità:</b> la società dispone di disponibilità liquide per {U(b['cash'])} euro e di un finanziamento a medio termine in ammortamento; la copertura degli impegni a breve è adeguata.",
         "<b>Rischio di mercato e di tasso:</b> il finanziamento è a tasso variabile; una variazione di un punto percentuale del tasso inciderebbe per circa 1.000 euro sugli oneri finanziari annui. Il rischio di cambio è marginale.",
         "<b>Rischio operativo e di dipendenza dal personale chiave:</b> la crescita è legata alla capacità di assumere e trattenere sviluppatori e analisti; la società investe in formazione e welfare aziendale."])
    d.H1("Evoluzione prevedibile della gestione")
    d.P("Per l'esercizio successivo si prevede una prosecuzione della crescita dei ricavi, trainata dai canoni della piattaforma e dai nuovi contratti già acquisiti, con ulteriori assunzioni nell'area sviluppo e nell'area commerciale e il completamento del progetto Atlas. "
        "Sono allo studio la partecipazione a bandi per la ricerca e l'innovazione e un investimento in infrastruttura cloud. Non si prevedono eventi in grado di compromettere la continuità aziendale.")
    d.P(f"Torino, {approved}. L'Amministratore unico: Giulia Ferraris.", left=True)
    d.page_break()

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

    # ------------------------------------------------------------------ allegato A: conto economico analitico
    d.title_block("ALLEGATO A - CONTO ECONOMICO ANALITICO PER CONTI", f"Dettaglio delle voci dello schema civilistico, euro e centesimi - esercizio {y} con confronto al {y - 1}")
    d.P("Il presente allegato espone, conto per conto, le voci del conto economico riportate in forma sintetica nello schema dell'art. 2425 c.c. Gli importi coincidono con le risultanze della contabilità generale al 31/12 e con le voci di bilancio.", left=True)

    def line(label, cur, prev, level=1, bold=False):
        return (label, [cents(cur), cents(prev) if prev is not None else ""], level, bold)

    rows = [("A) VALORE DELLA PRODUZIONE", ["", ""], 0, True)]
    parts_cur = M._alloc(p["revenue"], [s[1][i] / 100 for s in M.REVENUE_SPLIT])
    parts_prev = M._alloc(p0["revenue"], [s[1][i - 1] / 100 for s in M.REVENUE_SPLIT]) if p0 else None
    for k, (label, _) in enumerate(M.REVENUE_SPLIT):
        rows.append(line(f"Ricavi - {label.lower()}", parts_cur[k], parts_prev[k] if parts_prev else None))
    rows.append(line("Totale ricavi delle vendite e delle prestazioni", p["revenue"], p0["revenue"] if p0 else None, 0, True))
    rows.append(line("Variazione dei lavori in corso su ordinazione", p["wip_delta"], p0["wip_delta"] if p0 else None))
    rows.append(line("Incrementi di immobilizzazioni per lavori interni (sviluppo piattaforma)", p["capitalized"], p0["capitalized"] if p0 else None))
    rows.append(line("Contributi in conto esercizio (credito d'imposta ricerca e sviluppo)", p["grants"], p0["grants"] if p0 else None))
    rows.append(line("Altri ricavi e proventi", p["other_income"], p0["other_income"] if p0 else None))
    rows.append(line("Totale valore della produzione", p["a_total"], p0["a_total"] if p0 else None, 0, True))
    d.statement(rows, [W - 60, 30, 30], ["", f"{y}", f"{y - 1}" if p0 else ""])
    rows = [("B) COSTI DELLA PRODUZIONE", ["", ""], 0, True)]
    for code, label in (("6", "6) per materie prime, sussidiarie, di consumo e di merci"), ("7", "7) per servizi"), ("8", "8) per godimento di beni di terzi"), ("9", "9) per il personale"),
                        ("10", "10) ammortamenti e svalutazioni"), ("14", "14) oneri diversi di gestione")):
        accts = [(dsc, vals) for c, dsc, vals in M.COSTS if (c == code if len(code) == 1 and code in "678" or code == "14" else c.startswith(code))]
        rows.append((label, ["", ""], 1, True))
        for dsc, vals in accts:
            rows.append((dsc, [cents(vals[i]), cents(vals[i - 1]) if p0 else ""], 2, False))
        rows.append((f"Totale voce {code})", [cents(sum(vv[i] for _, vv in accts)), cents(sum(vv[i - 1] for _, vv in accts)) if p0 else ""], 1, True))
    rows.append(("Totale costi della produzione", [cents(p["b_total"]), cents(p0["b_total"]) if p0 else ""], 0, True))
    rows.append(("Differenza tra valore e costi della produzione (A - B)", [cents(p["ebit"]), cents(p0["ebit"]) if p0 else ""], 0, True))
    d.statement(rows, [W - 60, 30, 30], ["", f"{y}", f"{y - 1}" if p0 else ""])
    rows = [("C) PROVENTI E ONERI FINANZIARI", ["", ""], 0, True), ("Interessi attivi su conti correnti", [cents(p["int_income"]), cents(p0["int_income"]) if p0 else ""], 1, False),
            ("Interessi passivi su finanziamento chirografario", [cents(-round(p["int_expense"] * 0.86)), cents(-round(p0["int_expense"] * 0.86)) if p0 else ""], 1, False),
            ("Altri interessi e commissioni su affidamenti", [cents(-(p["int_expense"] - round(p["int_expense"] * 0.86))), cents(-(p0["int_expense"] - round(p0["int_expense"] * 0.86))) if p0 else ""], 1, False),
            ("Utili e perdite su cambi", [cents(p["fx"]), cents(p0["fx"]) if p0 else ""], 1, False),
            ("Risultato prima delle imposte", [cents(p["pre_tax"]), cents(p0["pre_tax"]) if p0 else ""], 0, True),
            ("Imposte correnti sul reddito (IRES e IRAP)", [cents(-p["taxes"]), cents(-p0["taxes"]) if p0 else ""], 1, False),
            ("UTILE (PERDITA) DELL'ESERCIZIO", [cents(p["net"]), cents(p0["net"]) if p0 else ""], 0, True)]
    d.statement(rows, [W - 60, 30, 30], ["", f"{y}", f"{y - 1}" if p0 else ""])
    return d.save()
