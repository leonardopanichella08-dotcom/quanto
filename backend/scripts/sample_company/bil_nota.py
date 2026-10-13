"""Nota integrativa estesa al bilancio d'esercizio (artt. 2427 e 2427-bis c.c.): ogni voce di stato patrimoniale e conto economico con le sue tabelle di dettaglio."""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Dict, List

from . import assets as AS
from . import ledger as LG
from . import model as M
from .pdfkit import Doc, cents, pct, units

U = units
CO = M.COMPANY


def E(c: int) -> str:
    """Centesimi interi → importo in euro con due decimali (1.234,56)."""
    return cents(Decimal(int(c)) / Decimal(100))


def EU(c: int) -> str:
    """Centesimi interi → importo in unità di euro arrotondate (1.235)."""
    return U(int(round(c / 100)))


def PCT(a: float, b: float, digits: int = 1) -> str:
    return pct(a / b, digits) if b else "-"


def _w(d: Doc) -> float:
    return d.width / 2.8346


def _acc_by_voce(y: int) -> Dict[str, List[dict]]:
    out: Dict[str, List[dict]] = defaultdict(list)
    for a in LG.cost_accounts(y):
        out[a["voce"]].append(a)
    return out


def _prev(y: int, code: str) -> int:
    for a in LG.cost_accounts(y - 1):
        if a["code"] == code:
            return a["cents"]
    return 0


def nota(d: Doc, y: int) -> None:
    W = _w(d)
    co = CO
    b, p = M.balance(y), M.pl(y)
    b0, p0 = M.balance(y - 1), M.pl(y - 1)
    ia, ta = M.fixed_assets("intang")[y], M.fixed_assets("tang")[y]
    reg_i = [r for r in AS.register("intang")[y] if r["cost_close"] > 0]
    reg_t = [r for r in AS.register("tang")[y] if r["cost_close"] > 0]
    approved = f"28/04/{y + 1}"
    cust = LG.customer_revenue(y)
    cust0 = LG.customer_revenue(y - 1)
    cust_tot = sum(v for _, v in cust)
    cust_tot0 = sum(v for _, v in cust0)

    d.title_block("NOTA INTEGRATIVA", f"al bilancio chiuso il 31/12/{y} - artt. 2427 e 2427-bis del codice civile")

    # ================================================================== 1. premessa
    d.H1("1. Premessa e struttura del bilancio")
    d.P(f"Il bilancio dell'esercizio chiuso al 31/12/{y}, di cui la presente nota integrativa costituisce parte integrante ai sensi dell'art. 2423 c.c., è stato redatto in conformità alle disposizioni degli articoli 2423 e seguenti del codice civile, "
        "interpretate e integrate dai principi contabili nazionali emanati dall'Organismo Italiano di Contabilità (OIC) nella versione vigente. Lo stato patrimoniale e il conto economico sono redatti secondo gli schemi degli artt. 2424 e 2425 c.c., "
        "il rendiconto finanziario secondo l'art. 2425-ter c.c. e l'OIC 10. La società, pur avendo i requisiti dimensionali per redigere il bilancio in forma abbreviata ai sensi dell'art. 2435-bis c.c., "
        "ha scelto di redigerlo in forma ordinaria per fornire un'informativa più completa ai soci, agli istituti di credito e agli enti che valutano le richieste di agevolazione.")
    d.P("Il bilancio è espresso in unità di euro, senza cifre decimali, ai sensi dell'art. 2423 c.c.; le differenze di arrotondamento sono state riportate nella voce di patrimonio netto «Riserva straordinaria» e, ove necessario, tra gli altri ricavi o costi. "
        "Per ogni voce dello stato patrimoniale e del conto economico è indicato l'importo dell'esercizio precedente, perfettamente comparabile: nell'esercizio non si sono verificati casi eccezionali che abbiano reso necessaria una deroga ai sensi dell'art. 2423, comma 5, c.c. "
        "Gli importi dell'allegato A (conto economico analitico), dell'allegato B (stato patrimoniale analitico) e dell'allegato C (bilancio di verifica) sono invece esposti in euro e centesimi e coincidono con le risultanze della contabilità generale.")
    d.table([["Informazione generale", "Dato"], ["Principi contabili di riferimento", "Codice civile e principi OIC (OIC 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 23, 24, 25, 28, 29, 31, 32, 34)"],
             ["Continuità aziendale", "Il bilancio è redatto nella prospettiva della continuazione dell'attività (OIC 11)"], ["Comparabilità con l'esercizio precedente", "Piena: nessuna riclassifica di importi dell'esercizio precedente"],
             ["Casi eccezionali ex art. 2423, comma 5", "Nessuno"], ["Cambiamenti di principi contabili e correzioni di errori rilevanti", "Nessuno (OIC 29)"],
             ["Operazioni in valuta estera", "Rilevate al cambio del giorno dell'operazione; poste monetarie adeguate al cambio di fine esercizio"], ["Data di approvazione prevista", f"Assemblea ordinaria del {approved}"]],
            [66, W - 66], align_right_from=9, zebra=True)

    # ================================================================== 2. criteri di valutazione
    d.H1("2. Criteri di valutazione")
    d.P("I criteri di valutazione sono ispirati ai principi generali di prudenza, competenza economica e prospettiva della continuazione dell'attività, tenendo conto della funzione economica dell'elemento dell'attivo o del passivo considerato (art. 2423-bis c.c.). "
        "I criteri applicati non sono variati rispetto all'esercizio precedente. Si illustrano di seguito i principali, voce per voce.")
    d.P("<b>Immobilizzazioni immateriali (OIC 24).</b> Sono iscritte al costo di acquisto o di produzione, comprensivo degli oneri accessori, e ammortizzate in quote costanti in relazione alla residua possibilità di utilizzazione. "
        "I costi di sviluppo, relativi alla piattaforma software prodotta internamente, sono capitalizzati quando il progetto è chiaramente definito, i costi sono identificabili e misurabili, il prodotto è tecnicamente realizzabile e vi è la prospettiva di ricavi futuri; "
        "sono ammortizzati in cinque anni a partire dal momento in cui il prodotto è commercializzabile. Il software applicativo acquistato è ammortizzato in tre anni, le licenze e i marchi in cinque anni, le migliorie su beni di terzi in base alla minore tra la durata residua del contratto di locazione e la vita utile. "
        "Alla fine di ogni esercizio si verifica l'esistenza di indicatori di perdite durevoli di valore; in assenza di indicatori non si procede alla stima del valore recuperabile.")
    d.P("<b>Immobilizzazioni materiali (OIC 16).</b> Sono iscritte al costo di acquisto, comprensivo degli oneri accessori di diretta imputazione, e sono sistematicamente ammortizzate in ogni esercizio sulla base di aliquote economico-tecniche determinate in relazione alla residua possibilità di utilizzazione dei beni. "
        "Nell'esercizio di entrata in funzione dei beni l'aliquota è ridotta alla metà, ritenendo che ciò approssimi adeguatamente l'utilizzo effettivo. I costi di manutenzione ordinaria sono imputati integralmente al conto economico; quelli di manutenzione straordinaria che incrementano la vita utile o la produttività sono capitalizzati.")
    rows = [["Classe di cespiti", "Aliquota di ammortamento", "Vita utile stimata"]]
    for c in list(M.INTANG_CLASSES) + list(M.TANG_CLASSES):
        r = int(c[5].rstrip("%"))
        rows.append([c[0], c[5], f"{100 / r:.1f} anni".replace(".", ",")])
    d.table(rows, [W - 70, 36, 34], align_right_from=1, zebra=True)
    d.P("<b>Immobilizzazioni finanziarie.</b> Sono costituite da depositi cauzionali versati a fronte dei contratti di locazione della sede legale e dell'unità locale, iscritti al valore nominale che coincide con il presumibile valore di realizzo; "
        "non sono state attualizzate per l'irrilevanza degli effetti (OIC 15).")
    d.P("<b>Rimanenze (OIC 23).</b> I lavori in corso su ordinazione si riferiscono a commesse di sviluppo software di durata infrannuale non ancora ultimate alla data di bilancio e sono valutati al costo di produzione sostenuto (personale diretto, costi di terzi direttamente imputabili e quota di costi generali di produzione), "
        "senza rilevazione di margini, in quanto le commesse hanno durata inferiore a dodici mesi.")
    d.P("<b>Crediti (OIC 15).</b> Sono iscritti al presumibile valore di realizzo, ottenuto rettificando il valore nominale con un fondo svalutazione stimato sulla base dell'anzianità dei crediti, della solvibilità dei debitori e delle perdite attese. "
        "Data la scadenza inferiore a dodici mesi e l'irrilevanza degli effetti, non si è applicato il criterio del costo ammortizzato né l'attualizzazione. I crediti d'imposta per ricerca e sviluppo sono rilevati nell'esercizio di maturazione, tra gli altri ricavi, con contropartita i crediti tributari.")
    d.P("<b>Disponibilità liquide, ratei e risconti (OIC 14, OIC 18).</b> Le disponibilità liquide sono iscritte al valore nominale. I ratei e i risconti sono determinati secondo il principio della competenza economica e temporale, mediante la ripartizione di costi e proventi comuni a due o più esercizi.")
    d.P("<b>Trattamento di fine rapporto (OIC 31).</b> Rappresenta l'effettivo debito maturato verso i dipendenti in conformità alla legge e ai contratti di lavoro vigenti, al netto degli acconti erogati e delle quote destinate alla previdenza complementare e al Fondo di Tesoreria dell'INPS.")
    d.P("<b>Debiti (OIC 19).</b> Sono rilevati al valore nominale, che coincide con il valore di estinzione; i debiti scadenti oltre i dodici mesi, derivanti da un finanziamento a tasso di mercato, non sono stati attualizzati per l'irrilevanza degli effetti.")
    d.P("<b>Ricavi e costi (OIC 34).</b> I ricavi per servizi e per canoni sono rilevati secondo il principio di competenza, in base al periodo di effettiva fruizione da parte del cliente; i canoni fatturati in anticipo sono rinviati con i risconti passivi. "
        "I ricavi per sviluppi su commessa sono rilevati alla consegna e accettazione del lavoro. Costi e ricavi sono esposti al netto di resi, sconti, abbuoni e premi.")
    d.P("<b>Imposte sul reddito (OIC 25).</b> Sono stanziate in base alla previsione dell'onere fiscale corrente (IRES e IRAP) applicando le aliquote vigenti, tenendo conto delle esenzioni e delle agevolazioni applicabili. Non sono state rilevate imposte differite o anticipate in quanto le differenze temporanee sono irrilevanti.")
    d.P("<b>Conversione delle poste in valuta (OIC 26).</b> Le operazioni in valuta estera (sterline e dollari, di importo marginale) sono rilevate al cambio del giorno; i crediti e i debiti monetari in valuta sono adeguati al cambio di fine esercizio e le differenze sono imputate al conto economico alla voce 17-bis.")

    # ================================================================== 3. immobilizzazioni immateriali
    d.H1("3. Immobilizzazioni immateriali")
    rows = [["Classe", "Costo storico 1/1", "Fondo amm.to 1/1", "Valore netto 1/1", "Acquisizioni", "Ammortamento", "Valore netto 31/12"]]
    for k, r in enumerate(ia):
        rows.append([M.INTANG_CLASSES[k][0], U(r["cost_open"]), U(r["fund_open"]), U(r["net_open"]), U(r["capex"]), U(-r["dep"]), U(r["net_close"])])
    rows.append(["Totale", U(sum(r["cost_open"] for r in ia)), U(sum(r["fund_open"] for r in ia)), U(sum(r["net_open"] for r in ia)), U(sum(r["capex"] for r in ia)), U(-sum(r["dep"] for r in ia)), U(sum(r["net_close"] for r in ia))])
    d.table(rows, [W - 98, 16, 16, 16, 16, 16, 18], bold_rows=[len(rows) - 1], font=7.4)
    d.small(f"Le acquisizioni di «Costi di sviluppo» ({U(ia[0]['capex'])} euro) sono i costi sostenuti per lo sviluppo interno della piattaforma Atlas (personale dedicato e consulenze tecniche), capitalizzati con contropartita la voce A.4 del conto economico.")
    d.H2("Dettaglio per singolo bene")
    d.table([["Bene", "Anno", "Costo storico", "Fondo 1/1", "Ammortamento", "Valore netto"]] +
            [[f"{r['item']}", str(r["year"]), U(r["cost_close"]), U(r["fund_open"]), U(-r["dep"]), U(r["net_close"])] for r in reg_i] +
            [["Totale", "", U(sum(r["cost_close"] for r in reg_i)), U(sum(r["fund_open"] for r in reg_i)), U(-sum(r["dep"] for r in reg_i)), U(sum(r["net_close"] for r in reg_i))]],
            [W - 100, 12, 22, 22, 22, 22], bold_rows=[len(reg_i) + 1], font=7.2, zebra=True)
    d.H2("Costi di sviluppo capitalizzati nell'esercizio")
    cap = p["capitalized"]
    parts = LG.alloc(cap, [34, 28, 24, 14])
    d.table([["Progetto di sviluppo", "Personale interno", "Consulenze tecniche", "Totale capitalizzato"],
             ["Motore di calcolo deterministico e archivio delle regole", U(round(parts[0] * 0.78)), U(parts[0] - round(parts[0] * 0.78)), U(parts[0])],
             ["Modulo di acquisizione e lettura dei documenti", U(round(parts[1] * 0.74)), U(parts[1] - round(parts[1] * 0.74)), U(parts[1])],
             ["Interfaccia web, reportistica e dossier", U(round(parts[2] * 0.7)), U(parts[2] - round(parts[2] * 0.7)), U(parts[2])],
             ["Test, sicurezza e documentazione tecnica", U(round(parts[3] * 0.82)), U(parts[3] - round(parts[3] * 0.82)), U(parts[3])],
             ["Totale costi di sviluppo capitalizzati", U(sum(round(x * k) for x, k in zip(parts, (0.78, 0.74, 0.7, 0.82)))), U(cap - sum(round(x * k) for x, k in zip(parts, (0.78, 0.74, 0.7, 0.82)))), U(cap)]],
            [W - 96, 32, 32, 32], bold_rows=[5])
    d.P("I costi di sviluppo sono capitalizzati solo per la parte riferita a progetti con prospettiva di utilità pluriennale; i costi di ricerca e quelli di sviluppo per commesse specifiche dei clienti sono imputati integralmente a conto economico nell'esercizio. "
        "Non sono stati effettuati oneri finanziari capitalizzati, rivalutazioni, svalutazioni per perdite durevoli o cessioni di immobilizzazioni immateriali. Non esistono immobilizzazioni immateriali con vita utile indefinita o avviamento iscritto.")

    # ================================================================== 4. immobilizzazioni materiali
    d.H1("4. Immobilizzazioni materiali")
    rows = [["Classe", "Costo storico 1/1", "Fondo amm.to 1/1", "Valore netto 1/1", "Acquisizioni", "Ammortamento", "Valore netto 31/12"]]
    for k, r in enumerate(ta):
        rows.append([M.TANG_CLASSES[k][0], U(r["cost_open"]), U(r["fund_open"]), U(r["net_open"]), U(r["capex"]), U(-r["dep"]), U(r["net_close"])])
    rows.append(["Totale", U(sum(r["cost_open"] for r in ta)), U(sum(r["fund_open"] for r in ta)), U(sum(r["net_open"] for r in ta)), U(sum(r["capex"] for r in ta)), U(-sum(r["dep"] for r in ta)), U(sum(r["net_close"] for r in ta))])
    d.table(rows, [W - 98, 16, 16, 16, 16, 16, 18], bold_rows=[len(rows) - 1], font=7.4)
    d.H2("Dettaglio per singolo bene")
    d.table([["Bene", "Acquisto", "Costo storico", "Fondo 1/1", "Ammortamento", "Valore netto"]] +
            [[f"{r['item']}", r["date"].strftime("%m/%Y"), U(r["cost_close"]), U(r["fund_open"]), U(-r["dep"]), U(r["net_close"])] for r in reg_t] +
            [["Totale", "", U(sum(r["cost_close"] for r in reg_t)), U(sum(r["fund_open"] for r in reg_t)), U(-sum(r["dep"] for r in reg_t)), U(sum(r["net_close"] for r in reg_t))]],
            [W - 100, 16, 21, 21, 21, 21], bold_rows=[len(reg_t) + 1], font=7.2, zebra=True)
    d.P(f"Nell'esercizio non sono state effettuate cessioni né rivalutazioni di immobilizzazioni, né svalutazioni per perdite durevoli di valore. Le immobilizzazioni materiali non sono gravate da ipoteche, privilegi o vincoli. "
        f"Gli acquisti dell'esercizio ({U(sum(r['capex'] for r in ta))} euro) riguardano in prevalenza macchine d'ufficio elettroniche e apparati per il laboratorio dati. I beni completamente ammortizzati ancora in uso hanno un costo storico di "
        f"{U(sum(r['cost_close'] for r in reg_t if r['net_close'] == 0) + sum(r['cost_close'] for r in reg_i if r['net_close'] == 0))} euro.")
    d.H2("Immobilizzazioni finanziarie")
    dep = [a for a in LG.bs_accounts(y) if a["group"] == "fin"]
    d.table([["Depositi cauzionali", f"31/12/{y}", f"31/12/{y - 1}", "Variazione"]] + [[a["name"], E(a["cents"]), E(next(x["cents"] for x in LG.bs_accounts(y - 1) if x["code"] == a["code"])), E(0)] for a in dep] +
            [["Totale immobilizzazioni finanziarie", E(sum(a["cents"] for a in dep)), E(sum(a["cents"] for a in dep)), E(0)]], [W - 96, 32, 32, 32], bold_rows=[len(dep) + 1])
    d.P("I depositi cauzionali sono esigibili alla scadenza dei contratti di locazione (31/12/2028 per la sede legale, 31/08/2027 per l'unità locale) e sono infruttiferi.")

    # ================================================================== 5. attivo circolante
    d.H1("5. Attivo circolante")
    d.H2("Lavori in corso su ordinazione")
    wip = [a for a in LG.bs_accounts(y) if a["group"] == "wip"]
    r_ = LG.rng("wipdetail", y)
    rows = [["Commessa", "Avanzamento", "Consegna prevista", "Valore a bilancio"]]
    for a in wip:
        rows.append([a["name"].replace("Lavori in corso su ordinazione: ", ""), f"{r_.randint(35, 88)}%", f"{r_.randint(1, 28):02d}/{r_.randint(1, 6):02d}/{y + 1}", E(a["cents"])])
    rows.append(["Totale lavori in corso su ordinazione", "", "", E(sum(a["cents"] for a in wip))])
    d.table(rows, [W - 94, 24, 34, 36], bold_rows=[len(rows) - 1])
    d.P(f"I lavori in corso ammontano a {U(b['wip'])} euro (esercizio precedente: {U(b0['wip'])}) e si riferiscono a {len(wip)} commesse in corso di esecuzione al 31/12/{y}, tutte con consegna prevista entro il primo semestre dell'esercizio successivo. "
        "Poiché le commesse hanno durata inferiore a dodici mesi, sono valutate al costo senza rilevazione di margine; non sono presenti perdite attese su commesse che richiedano accantonamenti.")

    d.H2("Crediti")
    rows = [["Voce", f"31/12/{y}", f"31/12/{y - 1}", "Variazione", "Entro 12 mesi", "Oltre 12 mesi"]]
    for label, key in [("Crediti verso clienti", "trade"), ("Crediti tributari", "tax_cr"), ("Crediti verso altri", "other_cr")]:
        rows.append([label, U(b[key]), U(b0[key]), U(b[key] - b0[key]), U(b[key]), "-"])
    rows.append(["Totale crediti", U(b["receivables"]), U(b0["receivables"]), U(b["receivables"] - b0["receivables"]), U(b["receivables"]), "-"])
    d.table(rows, [W - 100, 20, 20, 20, 20, 20], bold_rows=[len(rows) - 1])
    open_ = LG.open_receivables(y)
    gross_open = sum(o["open"] for o in open_)
    toissue = b["trade_invoices_to_issue"]
    fund_y = LG.credit_fund(y)
    d.table([["Composizione dei crediti verso clienti", "Importo"], ["Fatture emesse ancora aperte (IVA inclusa)", E(gross_open)], ["Fatture da emettere (ricavi di competenza non ancora fatturati)", E(toissue * 100)],
             ["Fondo svalutazione crediti", E(-fund_y * 100)], ["Crediti verso clienti iscritti in bilancio", E(gross_open + toissue * 100 - fund_y * 100)]], [W - 40, 40], bold_rows=[4])
    d.H2("Anzianità dei crediti verso clienti")
    ref = date(y, 12, 31)
    buckets = [("Non ancora scaduti", None, 0), ("Scaduti da 1 a 30 giorni", 1, 30), ("Scaduti da 31 a 60 giorni", 31, 60), ("Scaduti da 61 a 90 giorni", 61, 90), ("Scaduti da 91 a 180 giorni", 91, 180), ("Scaduti da oltre 180 giorni", 181, 10000)]
    sums = [0] * len(buckets)
    for o in open_:
        late = (ref - o["due"]).days
        for k, (_, lo, hi) in enumerate(buckets):
            if (lo is None and late <= 0) or (lo is not None and lo <= late <= hi):
                sums[k] += o["open"]
                break
    d.table([["Fascia di scaduto", "Importo (euro)", "% sul totale"]] + [[b_[0], E(s), PCT(s, gross_open)] for b_, s in zip(buckets, sums)] + [["Totale fatture emesse aperte", E(gross_open), "100,0%"]], [W - 70, 40, 30], bold_rows=[len(buckets) + 1])
    uses = LG.FUND_USES[y]
    d.H2("Movimentazione del fondo svalutazione crediti")
    d.table([["Fondo svalutazione crediti", "Importo"], [f"Saldo al 31/12/{y - 1}", U(LG.credit_fund(y - 1))], ["Accantonamento dell'esercizio (B.10.d)", U(p["b10d"])], ["Utilizzi per perdite su crediti stralciati", U(-uses)], [f"Saldo al 31/12/{y}", U(fund_y)]],
            [W - 40, 40], bold_rows=[4])
    agg: Dict[str, int] = defaultdict(int)
    names: Dict[str, str] = {}
    for o in open_:
        agg[o["customer"]["id"]] += o["open"]
        names[o["customer"]["id"]] = o["customer"]["name"]
    top = sorted(agg.items(), key=lambda t: -t[1])[:10]
    d.H2("Principali debitori")
    d.table([["Cliente", "Credito aperto (euro)", "% sul totale"]] + [[names[k], E(v), PCT(v, gross_open)] for k, v in top] + [["Primi dieci debitori", E(sum(v for _, v in top)), PCT(sum(v for _, v in top), gross_open)]],
            [W - 70, 40, 30], bold_rows=[len(top) + 1], font=8)
    area = defaultdict(int)
    for o in open_:
        area["Italia" if o["customer"]["kind"] != "Estero" else ("Unione Europea" if o["customer"]["region"] in ("Germania", "Svezia", "Spagna") else "Extra Unione Europea")] += o["open"]
    d.table([["Area geografica dei crediti verso clienti", "Importo (euro)", "%"]] + [[k, E(area.get(k, 0)), PCT(area.get(k, 0), gross_open)] for k in ("Italia", "Unione Europea", "Extra Unione Europea")], [W - 70, 40, 30])
    d.P(f"I crediti verso clienti sono esposti al netto del fondo svalutazione, determinato sulla base dell'anzianità delle singole posizioni e di una percentuale di perdita attesa del 12% sui crediti scaduti da oltre 90 giorni e dello 0,3% sugli altri crediti; "
        f"nessun credito è stato ceduto pro soluto. Le posizioni verso pubbliche amministrazioni ({PCT(sum(o['open'] for o in open_ if o['customer']['kind'] == 'PA'), gross_open, 0)} del totale) hanno tempi di pagamento mediamente più lunghi ma rischio di insolvenza trascurabile.")
    d.H2("Crediti tributari e crediti verso altri")
    tc = [a for a in LG.bs_accounts(y) if a["group"] in ("taxcr", "othercr")]
    d.table([["Conto", f"31/12/{y}", f"31/12/{y - 1}", "Variazione"]] + [[a["name"], E(a["cents"]), E(next((x["cents"] for x in LG.bs_accounts(y - 1) if x["code"] == a["code"]), 0)),
                                                                   E(a["cents"] - next((x["cents"] for x in LG.bs_accounts(y - 1) if x["code"] == a["code"]), 0))] for a in tc], [W - 96, 32, 32, 32], font=8)
    d.P(f"Il credito d'imposta per ricerca e sviluppo ({U(M.GRANTS[M._i(y)])} euro) è maturato sulle spese ammissibili dell'esercizio ai sensi dell'art. 1, commi 198-206, L. 160/2019 e sarà utilizzato in compensazione in F24 con codice tributo 6938 in tre quote annuali di pari importo, "
        "dopo l'invio della comunicazione al Ministero delle Imprese e del Made in Italy e l'ottenimento della certificazione della relazione tecnica; non è soggetto a limiti di compensazione annuali.")
    d.H2("Disponibilità liquide")
    cash = [a for a in LG.bs_accounts(y) if a["group"] == "cash"]
    d.table([["Conto", f"31/12/{y}", f"31/12/{y - 1}", "Variazione"]] + [[a["name"], E(a["cents"]), E(next((x["cents"] for x in LG.bs_accounts(y - 1) if x["code"] == a["code"]), 0)),
                                                                   E(a["cents"] - next((x["cents"] for x in LG.bs_accounts(y - 1) if x["code"] == a["code"]), 0))] for a in cash] +
            [["Totale disponibilità liquide", E(sum(a["cents"] for a in cash)), E(sum(x["cents"] for x in LG.bs_accounts(y - 1) if x["group"] == "cash")), E(sum(a["cents"] for a in cash) - sum(x["cents"] for x in LG.bs_accounts(y - 1) if x["group"] == "cash"))]],
            [W - 96, 32, 32, 32], bold_rows=[len(cash) + 1])
    transit = round(b["cash_bank"] * 0.004)
    d.table([["Riconciliazione dei saldi bancari al 31/12", "Importo"], ["Saldo contabile dei conti correnti", U(b["cash_bank"])], ["Accrediti in corso di valuta (bonifici di fine anno)", U(transit)], ["Addebiti in corso di valuta (disposizioni non ancora eseguite)", U(-round(transit * 0.62))],
             ["Saldo degli estratti conto bancari al 31/12", U(b["cash_bank"] + transit - round(transit * 0.62))]], [W - 40, 40], bold_rows=[4])
    d.P("Non vi sono vincoli sulle disponibilità liquide né depositi a garanzia. Le disponibilità liquide in valuta estera sono irrilevanti.")
    d.H2("Ratei e risconti attivi")
    pre = [a for a in LG.bs_accounts(y) if a["group"] == "prepaid"]
    d.table([["Natura", f"31/12/{y}", f"31/12/{y - 1}"]] + [[a["name"], E(a["cents"]), E(next(x["cents"] for x in LG.bs_accounts(y - 1) if x["code"] == a["code"]))] for a in pre] + [["Totale ratei e risconti attivi", E(sum(a["cents"] for a in pre)), E(sum(x["cents"] for x in LG.bs_accounts(y - 1) if x["group"] == "prepaid"))]],
            [W - 64, 32, 32], bold_rows=[len(pre) + 1])
    d.P("Non vi sono ratei e risconti con durata superiore a cinque anni.")

    # ================================================================== 6. patrimonio netto
    d.H1("6. Patrimonio netto")
    div = M.DIVIDENDS.get(y, 0)
    prev_net = p0["net"]
    rows = [["", "Capitale", "Riserva legale", "Riserva straordinaria", "Utile dell'esercizio", "Totale"]]
    for yy in (y - 2, y - 1, y):
        if yy < 2022:
            continue
        bb, bp = M.balance(yy), M.pl(yy)
        if yy > 2022:
            b_prev = M.balance(yy - 1)
            rows.append([f"Saldo al 31/12/{yy - 1}", U(b_prev["pn_capital"]), U(b_prev["pn_legal"]), U(b_prev["pn_extra"]), U(b_prev["pn_net"]), U(b_prev["pn"])])
            dv = M.DIVIDENDS.get(yy, 0)
            rows.append([f"Dividendi deliberati nel {yy}", "-", "-", "-", U(-dv), U(-dv)])
            rows.append([f"Destinazione a riserva straordinaria nel {yy}", "-", "-", U(M.pl(yy - 1)["net"] - dv), U(-(M.pl(yy - 1)["net"] - dv)), "-"])
            rows.append([f"Utile dell'esercizio {yy}", "-", "-", "-", U(bp["net"]), U(bp["net"])])
        rows.append([f"Saldo al 31/12/{yy}", U(bb["pn_capital"]), U(bb["pn_legal"]), U(bb["pn_extra"]), U(bb["pn_net"]), U(bb["pn"])])
    rows = [rows[0]] + [r for k, r in enumerate(rows[1:], 1) if not (k > 1 and r[0].startswith("Saldo al 31/12/") and rows[k - 1][0].startswith("Saldo al 31/12/"))]
    bold_idx = [k for k, r in enumerate(rows) if r[0].startswith("Saldo al")]
    d.table(rows, [W - 100, 20, 20, 20, 20, 20], bold_rows=bold_idx, font=7.6)
    d.H2("Origine, possibilità di utilizzazione e distribuibilità delle poste di patrimonio netto")
    d.table([["Natura", "Importo", "Origine", "Possibilità di utilizzazione", "Quota disponibile"],
             ["Capitale sociale", U(b["pn_capital"]), "Conferimenti dei soci", "-", "-"], ["Riserva legale", U(b["pn_legal"]), "Utili", "B", U(0)],
             ["Riserva straordinaria", U(b["pn_extra"]), "Utili", "A, B, C", U(b["pn_extra"])], ["Utile dell'esercizio", U(b["pn_net"]), "Utili", "A, B, C", U(b["pn_net"])],
             ["Totale", U(b["pn"]), "", "", U(b["pn_extra"] + b["pn_net"])]], [42, 26, 36, W - 140, 36], bold_rows=[5], align_right_from=1)
    d.small("Legenda: A = per aumento di capitale; B = per copertura di perdite; C = per distribuzione ai soci. La riserva legale, avendo raggiunto il quinto del capitale sociale, non è più alimentata.")
    d.P(f"Il capitale sociale, pari a {U(b['pn_capital'])} euro, è suddiviso in due quote: Giulia Ferraris, 60% (30.000 euro), e Marco Bertolotti, 40% (20.000 euro). "
        "La riserva straordinaria è libera e disponibile per ogni utilizzo, inclusi aumenti di capitale e distribuzione ai soci; non sono presenti riserve di rivalutazione, riserve in sospensione d'imposta, riserve per operazioni di copertura di flussi finanziari attesi né azioni proprie.")

    # ================================================================== 7. TFR
    d.H1("7. Trattamento di fine rapporto e fondi per rischi e oneri")
    tfr_used = b0["tfr"] + p["b9c"] - b["tfr"]
    d.table([["Movimentazione del fondo TFR", "Importo"], [f"Saldo al 31/12/{y - 1}", U(b0["tfr"])], ["Accantonamento dell'esercizio (B.9.c)", U(p["b9c"])],
             ["di cui destinato a previdenza complementare e Fondo di Tesoreria INPS (non incrementa il fondo)", U(round(p["b9c"] * 0.42))], ["Utilizzi per dimissioni, anticipazioni, imposta sostitutiva e previdenza complementare", U(-tfr_used)],
             [f"Saldo al 31/12/{y}", U(b["tfr"])]], [W - 40, 40], bold_rows=[5])
    d.P(f"Il fondo rappresenta l'impegno nei confronti dei {M.EMPLOYEES[y]} dipendenti in forza (media dell'esercizio) per il trattamento di fine rapporto maturato fino al 31/12/{y} per la quota non versata a forme di previdenza complementare o al Fondo di Tesoreria dell'INPS. "
        "Nell'esercizio sono state liquidate anticipazioni e liquidazioni per cessazione di rapporto di importo non significativo; l'imposta sostitutiva sulla rivalutazione del fondo è stata versata nei termini.")
    d.P("<b>Fondi per rischi e oneri.</b> Non sono stati iscritti fondi per rischi e oneri: non sussistono controversie legali, fiscali o con il personale, né garanzie prestate, per le quali sia stata valutata una passività probabile o possibile di importo rilevante (OIC 31). "
        "Il processo verbale di constatazione della Guardia di Finanza ricevuto nel 2019 si è concluso senza rilievi.")

    # ================================================================== 8. debiti
    d.H1("8. Debiti")
    rows = [["Voce", f"31/12/{y}", f"31/12/{y - 1}", "Variazione", "Entro 12 mesi", "Oltre 12 mesi"]]
    for label, key, short, long_ in [("Debiti verso banche", "loan", "loan_short", "loan_long"), ("Debiti verso fornitori", "suppliers", "suppliers", None), ("Debiti tributari", "tax_debt", "tax_debt", None),
                                     ("Debiti verso istituti di previdenza", "social", "social", None), ("Altri debiti", "other_debt", "other_debt", None)]:
        rows.append([label, U(b[key]), U(b0[key]), U(b[key] - b0[key]), U(b[short]), U(b[long_]) if long_ else "-"])
    rows.append(["Totale debiti", U(b["debts"]), U(b0["debts"]), U(b["debts"] - b0["debts"]), U(b["debts"] - b["loan_long"]), U(b["loan_long"])])
    d.table(rows, [W - 100, 20, 20, 20, 20, 20], bold_rows=[len(rows) - 1])
    d.H2("Debiti verso banche: finanziamento chirografario")
    d.table([["Caratteristica", "Dato"], ["Importo originario", "euro 300.000,00"], ["Data di erogazione", "30/09/2020"], ["Durata e scadenza finale", "84 mesi, ultima rata il 30/09/2027"], ["Rimborso", "Rate trimestrali costanti di capitale più interessi"],
             ["Tasso", "Variabile: Euribor a tre mesi più 2,10 punti percentuali (non coperto da strumenti derivati)"], ["Garanzie", "Chirografario; garanzia del Fondo centrale di garanzia per le PMI nella misura dell'80%"],
             [f"Debito residuo al 31/12/{y}", f"euro {U(b['loan'])}"], ["di cui entro 12 mesi", f"euro {U(b['loan_short'])}"], ["di cui oltre 12 mesi", f"euro {U(b['loan_long'])}"], ["Covenant finanziari", "Nessuno"]], [60, W - 60], align_right_from=9, zebra=True)
    d.H2("Piano di rimborso del debito residuo")
    sched = []
    left = b["loan"]
    start_y = y + 1
    inst = 11250
    for k in range(8):
        yy = start_y + k // 4
        mm = [3, 6, 9, 12][k % 4]
        if left <= 0:
            break
        q = min(inst, left)
        left -= q
        sched.append([f"{[31, 30, 30, 31][k % 4]:02d}/{mm:02d}/{yy}", U(q), U(left)])
    d.table([["Data della rata", "Quota capitale (euro)", "Debito residuo dopo la rata (euro)"]] + sched, [60, 50, W - 110], align_right_from=1, font=8)
    d.H2("Debiti tributari e previdenziali")
    tx = [a for a in LG.bs_accounts(y) if a["group"] in ("tax", "social")]
    d.table([["Conto", f"31/12/{y}", f"31/12/{y - 1}", "Variazione"]] + [[a["name"], E(-a["cents"]), E(-next((x["cents"] for x in LG.bs_accounts(y - 1) if x["code"] == a["code"]), 0)),
                                                                   E(-a["cents"] + next((x["cents"] for x in LG.bs_accounts(y - 1) if x["code"] == a["code"]), 0))] for a in tx] +
            [["Totale debiti tributari e previdenziali", E(-sum(a["cents"] for a in tx)), E(-sum(x["cents"] for x in LG.bs_accounts(y - 1) if x["group"] in ("tax", "social"))),
              E(-sum(a["cents"] for a in tx) + sum(x["cents"] for x in LG.bs_accounts(y - 1) if x["group"] in ("tax", "social")))]], [W - 96, 32, 32, 32], bold_rows=[len(tx) + 1], font=8)
    d.P(f"I debiti tributari ({U(b['tax_debt'])} euro) comprendono le ritenute IRPEF su redditi di lavoro dipendente e autonomo di dicembre, versate con F24 del 16 gennaio, l'IVA a debito di dicembre, il saldo IRES ({U(b['ires_due'])} euro) e il saldo IRAP ({U(b['irap_due'])} euro), al netto degli acconti versati. "
        f"I debiti verso istituti di previdenza ({U(b['social'])} euro) sono i contributi INPS e INAIL di dicembre, versati nei termini di legge. Tutti i debiti tributari e previdenziali sono regolarmente corrisposti: non esistono rateazioni o cartelle esattoriali.")
    d.H2("Debiti verso fornitori")
    pay = LG.open_payables(y)
    agg2: Dict[str, int] = defaultdict(int)
    for o in pay:
        agg2[o["supplier"]["name"]] += o["open"]
    toprec = sorted(agg2.items(), key=lambda t: -t[1])[:10]
    gp = sum(o["open"] for o in pay)
    d.table([["Fornitore", "Debito aperto (euro)", "%"]] + [[k, E(v), PCT(v, gp)] for k, v in toprec] + [["Fatture da ricevere", E(round(b["suppliers"] * 0.12) * 100), ""], ["Totale debiti verso fornitori", E(gp + round(b["suppliers"] * 0.12) * 100), ""]],
            [W - 70, 40, 30], bold_rows=[len(toprec) + 2], font=8)
    d.P("I debiti verso fornitori sono esigibili entro l'esercizio successivo e sono relativi a forniture di servizi, licenze, consulenze e utenze; i tempi medi di pagamento sono di 47 giorni. Non vi sono debiti assistiti da garanzie reali su beni sociali né debiti con obbligo di retrocessione a termine.")
    d.H2("Altri debiti e ratei e risconti passivi")
    od = [a for a in LG.bs_accounts(y) if a["group"] in ("other", "accrued")]
    d.table([["Conto", f"31/12/{y}", f"31/12/{y - 1}"]] + [[a["name"], E(-a["cents"]), E(-next((x["cents"] for x in LG.bs_accounts(y - 1) if x["code"] == a["code"]), 0))] for a in od], [W - 64, 32, 32], font=8)
    d.P("<b>Impegni, garanzie e passività potenziali.</b> Non vi sono impegni, garanzie o passività potenziali non risultanti dallo stato patrimoniale, salvo i canoni residui dei contratti di locazione operativa di autovetture e apparecchiature informatiche e le fidejussioni rilasciate dal sistema bancario a favore dei locatori degli immobili:")
    car = M.acct("Canoni di locazione operativa autovetture", y)
    ap = M.acct("Canoni di locazione operativa apparecchiature", y)
    d.table([["Impegno", "Entro 12 mesi", "Da 1 a 5 anni", "Totale"], ["Canoni di locazione operativa di autovetture", U(car), U(round(car * 1.6)), U(car + round(car * 1.6))], ["Canoni di locazione operativa di apparecchiature informatiche", U(ap), U(round(ap * 1.4)), U(ap + round(ap * 1.4))],
             ["Canoni di locazione degli immobili (contratti 6+6)", U(M.acct("Affitto uffici", y)), U(M.acct("Affitto uffici", y) * 3), U(M.acct("Affitto uffici", y) * 4)], ["Fidejussioni bancarie a favore dei locatori", U(27000), "-", U(27000)]],
            [W - 90, 30, 30, 30], font=8)

    # ================================================================== 9. conto economico: valore della produzione
    d.H1("9. Valore della produzione")
    i = M._i(y)
    cur = {a["code"]: a["cents"] for a in LG.revenue_accounts(y)}
    old = {a["code"]: a["cents"] for a in LG.revenue_accounts(y - 1)}
    rows = [["Conto", f"{y}", f"{y - 1}", "Variazione", "Var. %"]]
    for cat, (label, _) in enumerate(M.REVENUE_SPLIT):
        accts = [a for a in LG.REVENUE_ACCOUNTS if a[0] == cat]
        rows.append([f"<b>{label}</b>", "", "", "", ""])
        for a in accts:
            rows.append([f"{a[2]}", E(cur[a[1]]), E(old[a[1]]), E(cur[a[1]] - old[a[1]]), PCT(cur[a[1]] - old[a[1]], old[a[1]])])
        sc, so = sum(cur[a[1]] for a in accts), sum(old[a[1]] for a in accts)
        rows.append([f"Totale {label.lower()}", E(sc), E(so), E(sc - so), PCT(sc - so, so)])
    rows.append(["Totale ricavi delle prestazioni per conto", E(sum(cur.values())), E(sum(old.values())), E(sum(cur.values()) - sum(old.values())), PCT(sum(cur.values()) - sum(old.values()), sum(old.values()))])
    bold = [k for k, r in enumerate(rows) if r[0].startswith("Totale")]
    d.table(rows, [W - 100, 26, 26, 26, 22], bold_rows=bold, font=7.4)
    reg = defaultdict(int)
    kind = defaultdict(int)
    for c, v in cust:
        rg = c["region"]
        reg["Piemonte" if rg == "Piemonte" else ("Lombardia" if rg == "Lombardia" else ("Altre regioni italiane" if c["kind"] != "Estero" else ("Unione Europea" if rg in ("Germania", "Svezia", "Spagna") else "Extra Unione Europea")))] += v
        kind[{"PMI": "Imprese (PMI)", "PA": "Enti pubblici e del terzo settore", "Studio": "Studi professionali e associazioni", "Estero": "Clienti esteri"}[c["kind"]]] += v
    d.H2("Ricavi per area geografica e per tipologia di cliente")
    d.table([["Area geografica", f"{y}", "%"]] + [[k, E(v), PCT(v, cust_tot)] for k, v in sorted(reg.items(), key=lambda t: -t[1])] + [["Totale", E(cust_tot), "100,0%"]], [W - 70, 40, 30], bold_rows=[len(reg) + 1])
    d.table([["Tipologia di cliente", f"{y}", "%"]] + [[k, E(v), PCT(v, cust_tot)] for k, v in sorted(kind.items(), key=lambda t: -t[1])] + [["Totale", E(cust_tot), "100,0%"]], [W - 70, 40, 30], bold_rows=[len(kind) + 1])
    d.H2("Principali clienti")
    d.table([["Cliente", "Settore", f"Ricavi {y} (euro)", "%", f"Ricavi {y - 1}"]] + [[c["name"], c["sector"], E(v), PCT(v, cust_tot), E(dict((x["id"], vv) for x, vv in cust0).get(c["id"], 0))] for c, v in cust[:10]] +
            [["Primi dieci clienti", "", E(sum(v for _, v in cust[:10])), PCT(sum(v for _, v in cust[:10]), cust_tot), ""], [f"Totale clienti attivi ({len(cust)})", "", E(cust_tot), "100,0%", E(cust_tot0)]], [W - 114, 40, 30, 16, 28], bold_rows=[11, 12], font=7.4)
    d.P(f"Il cliente più rilevante rappresenta il {PCT(cust[0][1], cust_tot)} dei ricavi e i primi cinque clienti il {PCT(sum(v for _, v in cust[:5]), cust_tot)} del fatturato; la società non dipende da un singolo committente. "
        f"I ricavi ricorrenti da canoni e licenze ammontano a {U(round(sum(v for k_, v in cur.items() if k_.startswith('420')) / 100))} euro ({PCT(sum(v for k_, v in cur.items() if k_.startswith('420')), sum(cur.values()))} dei ricavi) rispetto a "
        f"{U(round(sum(v for k_, v in old.items() if k_.startswith('420')) / 100))} euro nel {y - 1}.")
    d.H2("Altri ricavi e proventi e aiuti di Stato ricevuti")
    other = [a for a in LG.other_pl_accounts(y) if a["section"] in ("A.3", "A.4", "A.5")]
    other0 = {a["code"]: a["cents"] for a in LG.other_pl_accounts(y - 1)}
    d.table([["Conto", f"{y}", f"{y - 1}"]] + [[a["name"], E(a["cents"]), E(other0.get(a["code"], 0))] for a in other], [W - 64, 32, 32], font=8)
    d.P(f"Gli altri ricavi e proventi comprendono contributi in conto esercizio per {U(p['grants'])} euro, rappresentati dal credito d'imposta per attività di ricerca e sviluppo (art. 1, commi 198-206, L. 160/2019) maturato sulle spese di sviluppo della piattaforma, "
        f"e altri proventi per {U(p['other_income'])} euro (rimborsi assicurativi, recuperi di spese e sopravvenienze attive ordinarie).")
    aid_rows = [["Soggetto erogante", "Misura", "Data", "Importo (euro)", "Regime"], ["Agenzia delle Entrate", "Credito d'imposta ricerca e sviluppo", f"31/12/{y}", U(p["grants"]), "Credito d'imposta"]]
    if y == 2024:
        aid_rows.append(["Camera di Commercio di Torino", "Voucher digitalizzazione PMI", "12/04/2024", U(10000), "De minimis"])
    if y == 2025:
        aid_rows.append(["Regione Piemonte", "Contributo partecipazione a fiere", "03/10/2025", U(6500), "De minimis"])
    d.P("Ai sensi dell'art. 1, commi 125-129, della legge 124/2017, si espongono i contributi e gli aiuti pubblici incassati o concessi nell'esercizio:")
    d.table(aid_rows, [48, 56, 22, 24, W - 150], align_right_from=3)
    d.small("Gli aiuti in regime de minimis sono assegnati ai sensi del regolamento (UE) 2023/2831 e registrati nel Registro nazionale degli aiuti di Stato con il codice COR indicato nel registro aiuti dell'impresa.")

    # ================================================================== 10. costi della produzione
    d.H1("10. Dettaglio degli oneri e dei costi dell'esercizio")
    by = _acc_by_voce(y)
    voci = [("6", "Costi per materie prime, sussidiarie, di consumo e di merci (B.6)"), ("7", "Costi per servizi (B.7)"), ("8", "Costi per godimento di beni di terzi (B.8)"), ("9a", "Costi del personale: salari e stipendi (B.9.a)"),
            ("9b", "Costi del personale: oneri sociali (B.9.b)"), ("9c", "Costi del personale: trattamento di fine rapporto (B.9.c)"), ("9e", "Costi del personale: altri costi (B.9.e)"),
            ("10a", "Ammortamento delle immobilizzazioni immateriali (B.10.a)"), ("10b", "Ammortamento delle immobilizzazioni materiali (B.10.b)"), ("10d", "Svalutazione dei crediti (B.10.d)"), ("14", "Oneri diversi di gestione (B.14)")]
    for code, label in voci:
        accts = by[code]
        rows = [[label, f"{y}", f"{y - 1}", "Var. %"]]
        for a in accts:
            if a["cents"] == 0 and _prev(y, a["code"]) == 0:
                continue
            pv = _prev(y, a["code"])
            rows.append([a["name"], E(a["cents"]), E(pv), PCT(a["cents"] - pv, pv) if pv else "n.s."])
        tot, tot0 = sum(a["cents"] for a in accts), sum(_prev(y, a["code"]) for a in accts)
        rows.append([f"Totale {label.split('(')[0].strip().lower()}", E(tot), E(tot0), PCT(tot - tot0, tot0) if tot0 else "n.s."])
        d.table(rows, [W - 94, 32, 32, 30], bold_rows=[len(rows) - 1], font=7.4)
    d.P(f"I costi per servizi ({U(p['b7'])} euro) comprendono consulenze tecniche, legali e fiscali, compensi a collaboratori esterni, licenze e servizi cloud, utenze, assicurazioni, pubblicità, formazione e spese di rappresentanza. "
        f"I costi per godimento di beni di terzi ({U(p['b8'])} euro) sono costituiti dai canoni di locazione della sede e dell'unità locale e dai canoni di locazione operativa di autovetture e apparecchiature. "
        f"Il costo del personale ({U(p['b9a'] + p['b9b'] + p['b9c'] + p['b9e'])} euro) comprende retribuzioni, contributi previdenziali e assistenziali, TFR e ferie maturate, e include i costi del personale dedicato allo sviluppo interno, "
        f"capitalizzati per {U(p['capitalized'])} euro tra le immobilizzazioni immateriali mediante la voce A.4. Gli oneri diversi di gestione ({U(p['b14'])} euro) sono costituiti da imposte indirette, quote associative, liberalità e sopravvenienze passive ordinarie.")

    d.H1("11. Proventi e oneri finanziari")
    fin = [a for a in LG.other_pl_accounts(y) if a["section"] in ("C.16", "C.17", "C.17-bis")]
    fin0 = {a["code"]: a["cents"] for a in LG.other_pl_accounts(y - 1)}
    d.table([["Conto", f"{y}", f"{y - 1}"]] + [[a["name"], E(a["cents"] if a["side"] == "R" else -a["cents"]), E(fin0.get(a["code"], 0) if a["side"] == "R" else -fin0.get(a["code"], 0))] for a in fin] +
            [["Totale proventi e oneri finanziari", E(p["fin"] * 100), E(p0["fin"] * 100)]], [W - 64, 32, 32], bold_rows=[len(fin) + 1], font=8)
    d.P(f"Gli interessi e altri oneri finanziari ({U(p['int_expense'])} euro) sono quasi interamente relativi agli interessi sul finanziamento chirografario ({U(round(p['int_expense'] * 0.86))} euro) e, per il resto, a commissioni su affidamenti e interessi di mora fornitori. "
        f"I proventi finanziari ({U(p['int_income'])} euro) sono interessi attivi di conto corrente. Le differenze di cambio nette sono di {U(p['fx'])} euro e si riferiscono a fatture in dollari e sterline non rilevanti. "
        "Non vi sono proventi da partecipazioni, rettifiche di valore di attività finanziarie né elementi di ricavo o di costo di entità o incidenza eccezionali.")

    # ================================================================== 12. imposte
    d.H1("12. Imposte sul reddito dell'esercizio")
    t = p["tax"]
    rows = [["Riconciliazione tra onere fiscale teorico ed effettivo (IRES)", "Imponibile", "Imposta"], ["Risultato prima delle imposte", U(p["pre_tax"]), ""], ["Onere fiscale teorico (aliquota 24%)", "", U(t["theoretical"])]]
    for label, amount in t["up"].items():
        rows.append([f"Variazioni in aumento: {label}", U(amount), ""])
    for label, amount in t["down"].items():
        rows.append([f"Variazioni in diminuzione: {label}", U(-amount), ""])
    rows.append(["Imponibile IRES", U(t["taxable"]), ""])
    rows.append(["IRES corrente dell'esercizio (aliquota 24%)", "", U(t["ires"])])
    rows.append(["IRAP: base imponibile e imposta (aliquota 3,90%, Regione Piemonte)", U(t["irap_base"]), U(t["irap"])])
    rows.append(["Totale imposte correnti a conto economico", "", U(p["taxes"])])
    d.table(rows, [W - 56, 28, 28], bold_rows=[len(rows) - 1])
    d.H2("Determinazione dell'IRAP")
    irap_base = t["irap_base"]
    d.table([["Calcolo IRAP (metodo del valore della produzione netta)", "Importo (euro)"], ["Differenza tra valore e costi della produzione (A - B)", U(p["ebit"])], ["Variazioni in aumento: costi per collaboratori e lavoro autonomo occasionale", U(round(M.acct("Compensi a professionisti", y) * 0.0))],
             ["Variazioni in diminuzione: deduzione del costo del lavoro a tempo indeterminato (art. 11 D.Lgs. 446/1997)", U(0)], ["Valore della produzione netta", U(irap_base)], ["Imposta IRAP (aliquota 3,90%)", U(t["irap"])]], [W - 40, 40], bold_rows=[4, 5])
    d.H2("Credito d'imposta per ricerca e sviluppo: calcolo")
    base = M.GRANTS[i] * (10 if y >= 2023 else 5)
    cp = LG.alloc(base, [70, 18, 7, 5])
    d.table([["Costi ammissibili alla base di calcolo", "Importo (euro)"], ["Personale impiegato in attività di ricerca e sviluppo", U(cp[0])], ["Ricerca contrattuale e consulenze tecniche con università e centri di ricerca", U(cp[1])],
             ["Quota di ammortamento di attrezzature di laboratorio", U(cp[2])], ["Materiali e forniture per i prototipi", U(cp[3])], ["Totale costi ammissibili", U(base)], [f"Credito d'imposta maturato (aliquota {'10%' if y >= 2023 else '20%'})", U(M.GRANTS[i])]], [W - 40, 40], bold_rows=[5, 6])
    d.P("Ai fini della determinazione dell'IRES sono state applicate le agevolazioni vigenti (deduzione ACE e deduzione dell'IRAP riferita al costo del lavoro). Non sono state rilevate imposte anticipate o differite per irrilevanza delle differenze temporanee; "
        "non esistono perdite fiscali riportabili. Gli accertamenti degli esercizi dal 2020 in avanti non sono ancora definiti; non risultano contenziosi tributari in corso.")

    # ================================================================== 13. personale e organi
    d.H1("13. Dati sull'occupazione, compensi agli organi e altre informazioni")
    q, imp, app = M.HEADCOUNT_SPLIT[y]
    q0, imp0, app0 = M.HEADCOUNT_SPLIT[y - 1]
    d.table([["Numero medio dei dipendenti per categoria", f"{y}", f"{y - 1}"], ["Dirigenti", "-", "-"], ["Quadri", str(q), str(q0)], ["Impiegati", str(imp), str(imp0)], ["Operai", "-", "-"], ["Apprendisti", str(app), str(app0)],
             ["Totale dipendenti", str(M.EMPLOYEES[y]), str(M.EMPLOYEES[y - 1])]], [W - 60, 30, 30], bold_rows=[6])
    wages = p["b9a"] + p["b9b"] + p["b9c"] + p["b9e"]
    d.table([["Indicatore", f"{y}", f"{y - 1}"], ["Costo del personale (euro)", U(wages), U(p0["b9a"] + p0["b9b"] + p0["b9c"] + p0["b9e"])], ["Costo medio per dipendente (euro)", U(round(wages / M.EMPLOYEES[y])), U(round((p0["b9a"] + p0["b9b"] + p0["b9c"] + p0["b9e"]) / M.EMPLOYEES[y - 1]))],
             ["Ricavi per dipendente (euro)", U(round(p["revenue"] / M.EMPLOYEES[y])), U(round(p0["revenue"] / M.EMPLOYEES[y - 1]))], ["Incidenza del costo del personale sui ricavi", PCT(wages, p["revenue"]), PCT(p0["b9a"] + p0["b9b"] + p0["b9c"] + p0["b9e"], p0["revenue"])],
             ["Età media del personale (anni)", "35,4" if y == 2025 else ("35,9" if y == 2024 else "36,2"), "35,9" if y == 2025 else ("36,2" if y == 2024 else "36,8")], ["Assunzioni dell'esercizio", str(M.EMPLOYEES[y] - M.EMPLOYEES[y - 1] + 1), str(M.EMPLOYEES[y - 1] - M.EMPLOYEES[y - 2] + 1) if y > 2023 else "2"],
             ["Cessazioni dell'esercizio", "1", "1"]], [W - 60, 30, 30], font=8)
    d.P(f"Numero medio dei dipendenti {M.EMPLOYEES[y]}. Ai dipendenti è applicato il CCNL Commercio, Terziario Distribuzione e Servizi. L'organo amministrativo è composto dall'amministratore unico, che non percepisce compensi in tale qualità ed è retribuito come quadro dirigente; "
        "la società non è soggetta a revisione legale né è tenuta alla nomina di un organo di controllo, e nessun compenso è stato corrisposto a revisori o sindaci. Non sono stati concessi anticipazioni o crediti agli amministratori né sono state prestate garanzie a loro favore.")
    d.table([["Compensi, anticipazioni e crediti concessi agli organi sociali", "Importo (euro)"], ["Compensi all'amministratore unico per la carica", "-"], ["Retribuzione dell'amministratore unico come quadro dipendente (inclusa nel costo del personale)", U(78000)],
             ["Compensi a sindaci e revisori", "-"], ["Compensi alla società di revisione per verifiche volontarie", "-"], ["Anticipazioni e crediti concessi ad amministratori", "-"], ["Garanzie prestate a favore di amministratori", "-"]], [W - 40, 40], font=8)
    d.H2("Operazioni con parti correlate, accordi fuori bilancio e strumenti finanziari")
    d.P("<b>Operazioni con parti correlate.</b> Non sono state poste in essere operazioni con parti correlate a condizioni diverse da quelle di mercato; non risultano rapporti commerciali o finanziari con i soci o con società a essi riconducibili, salvo il rimborso di spese documentate. "
        "<b>Accordi non risultanti dallo stato patrimoniale</b>: non ve ne sono. <b>Strumenti finanziari derivati</b>: la società non ha sottoscritto strumenti derivati e non detiene strumenti finanziari rilevanti ai sensi dell'art. 2427-bis c.c. "
        "<b>Patrimoni e finanziamenti destinati a uno specifico affare</b>: non ve ne sono. <b>Attività di direzione e coordinamento</b>: la società non è soggetta a direzione e coordinamento di altre società o enti.")
    nxt = {2023: "nel mese di febbraio 2024 sono stati sottoscritti due nuovi contratti di sviluppo con enti pubblici locali per complessivi 180.000 euro; ", 2024: "nei primi mesi del 2025 è stata completata l'assunzione di due sviluppatori e di un data scientist; ",
           2025: "nei primi mesi del 2026 sono stati assunti due apprendisti e avviato il progetto di analisi predittiva dei costi per le PMI; "}.get(y, "")
    d.P(f"<b>Fatti di rilievo avvenuti dopo la chiusura dell'esercizio.</b> Dopo il 31/12/{y} {nxt or 'non si sono verificati fatti '}che non abbiano modificato la situazione patrimoniale e finanziaria della società né il risultato economico dell'esercizio.")
    d.H1("14. Proposta di destinazione dell'utile")
    prop = {2022: 40000, 2023: 60000, 2024: 80000, 2025: 90000}[y]
    d.table([["Destinazione proposta", "Importo (euro)"], ["Utile dell'esercizio", U(p["net"])], ["a dividendo ai soci in proporzione alle quote (60% e 40%)", U(prop)], ["di cui a Giulia Ferraris (60%)", U(round(prop * 0.6))], ["di cui a Marco Bertolotti (40%)", U(prop - round(prop * 0.6))],
             ["a riserva straordinaria", U(p["net"] - prop)], ["a riserva legale (limite del quinto del capitale già raggiunto)", "-"]], [W - 40, 40], bold_rows=[1])
    d.P(f"L'organo amministrativo propone di destinare l'utile dell'esercizio, pari a euro {U(p['net'])}, quanto a euro {U(prop)} a dividendo ai soci in proporzione alle quote possedute e quanto a euro {U(p['net'] - prop)} a riserva straordinaria, "
        "la riserva legale avendo già raggiunto il limite previsto dall'art. 2430 c.c.")
    d.P(f"Torino, {approved}. L'Amministratore unico: Giulia Ferraris.", left=True)
