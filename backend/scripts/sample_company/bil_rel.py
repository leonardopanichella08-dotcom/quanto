"""Relazione sulla gestione estesa (art. 2428 c.c.): andamento, riclassificazioni, indicatori, ricerca e sviluppo, personale, rischi, evoluzione prevedibile."""
from __future__ import annotations

from typing import List

from . import ledger as LG
from . import model as M
from .bil_nota import E, EU, PCT
from .pdfkit import Doc, pct, units

U = units
CO = M.COMPANY


def _w(d: Doc) -> float:
    return d.width / 2.8346


def f2(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def reclass(y: int) -> dict:
    """Riclassificazione del conto economico a valore aggiunto e dello stato patrimoniale finanziario."""
    p, b = M.pl(y), M.balance(y)
    ext = p["b6"] + p["b7"] + p["b8"] - 0
    vp = p["revenue"] + p["wip_delta"] + p["capitalized"] + p["grants"] + p["other_income"]
    va = vp - ext - p["b14"]
    staff = p["b9a"] + p["b9b"] + p["b9c"] + p["b9e"]
    ebitda = va - staff
    dep = p["b10a"] + p["b10b"] + p["b10d"]
    ebit = ebitda - dep
    assert ebit == p["ebit"], (y, ebit, p["ebit"])
    fixed = b["fixed"]
    ccn_assets = b["wip"] + b["trade"] + b["tax_cr"] + b["other_cr"] + b["prepaid"]
    ccn_liab = b["suppliers"] + b["tax_debt"] + b["social"] + b["other_debt"] + b["accrued"]
    ccn = ccn_assets - ccn_liab
    invested = fixed + ccn - b["tfr"]
    pfn = b["loan"] - b["cash"]
    return {"vp": vp, "ext": ext, "va": va, "staff": staff, "ebitda": ebitda, "dep": dep, "ebit": ebit, "fixed": fixed, "ccn_assets": ccn_assets, "ccn_liab": ccn_liab, "ccn": ccn, "invested": invested, "pfn": pfn}


def relazione(d: Doc, y: int) -> None:
    W = _w(d)
    p, b = M.pl(y), M.balance(y)
    p0, b0 = M.pl(y - 1), M.balance(y - 1)
    rc, rc0 = reclass(y), reclass(y - 1)
    r, r0 = M.ratio_notes(y), M.ratio_notes(y - 1)
    growth = p["revenue"] / p0["revenue"] - 1
    ia, ta = M.fixed_assets("intang")[y], M.fixed_assets("tang")[y]
    approved = f"28/04/{y + 1}"
    d.title_block("RELAZIONE SULLA GESTIONE", f"dell'organo amministrativo al bilancio chiuso il 31/12/{y} - art. 2428 del codice civile")

    d.H1("1. Condizioni operative e sviluppo dell'attività")
    d.P(f"Signori soci, l'esercizio {y} si chiude con un utile di {U(p['net'])} euro, dopo aver rilevato ammortamenti per {U(p['b10a'] + p['b10b'])} euro e imposte per {U(p['taxes'])} euro. "
        f"I ricavi delle vendite e delle prestazioni sono stati pari a {U(p['revenue'])} euro, in crescita del {pct(growth)} rispetto ai {U(p0['revenue'])} euro del {y - 1}. "
        "La società opera nello sviluppo di software e di piattaforme di analisi dei dati per piccole e medie imprese e per enti pubblici locali, con sede a Torino e un'unità locale dedicata al laboratorio dati e alla formazione, e nell'esercizio ha proseguito il percorso di crescita "
        "sia dei ricavi ricorrenti da licenze e abbonamenti sia dell'attività di sviluppo su commessa.")
    d.P("Il mercato di riferimento ha confermato una domanda sostenuta di digitalizzazione dei processi e di analisi dei dati da parte delle imprese di piccola dimensione, sostenuta anche dagli incentivi pubblici alla transizione digitale e dalla maggiore attenzione alla sicurezza delle informazioni. "
        "La concorrenza resta frammentata e si sta spostando verso piattaforme verticali; la società ha risposto investendo nello sviluppo di un prodotto proprietario, nella certificazione dei propri processi (ISO 9001 e ISO/IEC 27001) e nella formazione del personale.")
    d.P("<b>Scenario macroeconomico.</b> Il contesto è stato caratterizzato da una crescita moderata dell'economia italiana, da un'inflazione in progressivo rientro e da tassi di interesse che si sono stabilizzati su livelli inferiori ai picchi del biennio precedente. "
        "Per la società, che opera in larga parte con clienti italiani e con costi prevalentemente in euro, gli effetti diretti sono stati limitati; l'inflazione ha inciso soprattutto sul costo del lavoro (rinnovi contrattuali) e sulle utenze.")

    d.H1("2. Andamento della gestione: conto economico riclassificato")
    rows = [["Conto economico a valore aggiunto (euro)", f"{y}", "% ricavi", f"{y - 1}", "% ricavi", "Variazione"]]

    def line(label, a, a0, rev=True):
        return [label, U(a), PCT(a, p["revenue"]) if rev else "", U(a0), PCT(a0, p0["revenue"]) if rev else "", U(a - a0)]
    rows += [line("Ricavi delle prestazioni e dei canoni", p["revenue"], p0["revenue"]), line("Variazione dei lavori in corso e incrementi per lavori interni", p["wip_delta"] + p["capitalized"], p0["wip_delta"] + p0["capitalized"]),
             line("Altri ricavi e proventi", p["grants"] + p["other_income"], p0["grants"] + p0["other_income"]), line("Valore della produzione", rc["vp"], rc0["vp"]),
             line("Costi esterni: materie, servizi e godimento di beni di terzi", -rc["ext"], -rc0["ext"]), line("Oneri diversi di gestione", -p["b14"], -p0["b14"]), line("Valore aggiunto", rc["va"], rc0["va"]),
             line("Costo del personale", -rc["staff"], -rc0["staff"]), line("Margine operativo lordo (EBITDA)", rc["ebitda"], rc0["ebitda"]), line("Ammortamenti e svalutazioni", -rc["dep"], -rc0["dep"]),
             line("Risultato operativo (EBIT)", rc["ebit"], rc0["ebit"]), line("Proventi e oneri finanziari", p["fin"], p0["fin"]), line("Risultato prima delle imposte", p["pre_tax"], p0["pre_tax"]),
             line("Imposte sul reddito", -p["taxes"], -p0["taxes"]), line("Utile dell'esercizio", p["net"], p0["net"])]
    d.table(rows, [W - 120, 24, 18, 24, 18, 24, ][:6], bold_rows=[4, 7, 9, 11, 13, 15], font=7.6)
    d.P(f"Il valore aggiunto è cresciuto del {pct(rc['va'] / rc0['va'] - 1)}, a fronte di una crescita dei ricavi del {pct(growth)}: i costi esterni sono aumentati meno dei ricavi grazie al maggior peso dei canoni ricorrenti, che richiedono meno consulenze esterne. "
        f"Il costo del personale è passato dal {PCT(rc0['staff'], p0['revenue'])} al {PCT(rc['staff'], p['revenue'])} dei ricavi per l'aumento dell'organico da {M.EMPLOYEES[y - 1]} a {M.EMPLOYEES[y]} unità e per gli adeguamenti contrattuali. "
        f"L'EBITDA si attesta a {U(rc['ebitda'])} euro ({PCT(rc['ebitda'], p['revenue'])} dei ricavi) rispetto a {U(rc0['ebitda'])} euro del {y - 1}.")

    d.H2("Analisi dei ricavi per linea di attività")
    i = M._i(y)
    cur = M._alloc(p["revenue"], [s[1][i] / 100 for s in M.REVENUE_SPLIT])
    old = M._alloc(p0["revenue"], [s[1][i - 1] / 100 for s in M.REVENUE_SPLIT])
    rows = [["Linea di attività", f"{y}", "Quota", f"{y - 1}", "Quota", "Var. %"]]
    for k, (label, _) in enumerate(M.REVENUE_SPLIT):
        rows.append([label, U(cur[k]), PCT(cur[k], p["revenue"]), U(old[k]), PCT(old[k], p0["revenue"]), PCT(cur[k] - old[k], old[k])])
    rows.append(["Totale", U(p["revenue"]), "100,0%", U(p0["revenue"]), "100,0%", PCT(p["revenue"] - p0["revenue"], p0["revenue"])])
    d.table(rows, [W - 124, 24, 18, 24, 18, 18], bold_rows=[5], font=7.8)
    d.P("I canoni della piattaforma Atlas e le licenze agli studi professionali continuano a crescere a ritmo sostenuto e raggiungono una quota sempre maggiore dei ricavi; lo sviluppo su commessa resta la linea più ampia ma con peso decrescente. "
        "La consulenza sui dati beneficia della domanda di cruscotti e di analisi predittive; formazione e assistenza tecnica restano stabili in rapporto ai ricavi.")

    d.H1("3. Situazione patrimoniale e finanziaria")
    rows = [["Stato patrimoniale riclassificato (euro)", f"31/12/{y}", f"31/12/{y - 1}", "Variazione"]]
    rows += [["Immobilizzazioni nette", U(rc["fixed"]), U(rc0["fixed"]), U(rc["fixed"] - rc0["fixed"])], ["Crediti verso clienti, rimanenze e altre attività correnti", U(rc["ccn_assets"]), U(rc0["ccn_assets"]), U(rc["ccn_assets"] - rc0["ccn_assets"])],
             ["Debiti verso fornitori, tributari, previdenziali e altri", U(-rc["ccn_liab"]), U(-rc0["ccn_liab"]), U(-rc["ccn_liab"] + rc0["ccn_liab"])], ["Capitale circolante netto", U(rc["ccn"]), U(rc0["ccn"]), U(rc["ccn"] - rc0["ccn"])],
             ["Trattamento di fine rapporto", U(-b["tfr"]), U(-b0["tfr"]), U(-b["tfr"] + b0["tfr"])], ["Capitale investito netto", U(rc["invested"]), U(rc0["invested"]), U(rc["invested"] - rc0["invested"])],
             ["Patrimonio netto", U(b["pn"]), U(b0["pn"]), U(b["pn"] - b0["pn"])], ["Debiti finanziari a medio termine", U(b["loan"]), U(b0["loan"]), U(b["loan"] - b0["loan"])],
             ["Disponibilità liquide", U(-b["cash"]), U(-b0["cash"]), U(-b["cash"] + b0["cash"])], ["Posizione finanziaria netta (negativa = liquidità netta)", U(rc["pfn"]), U(rc0["pfn"]), U(rc["pfn"] - rc0["pfn"])],
             ["Totale fonti di finanziamento", U(b["pn"] + rc["pfn"]), U(b0["pn"] + rc0["pfn"]), U(b["pn"] + rc["pfn"] - b0["pn"] - rc0["pfn"])]]
    assert b["pn"] + rc["pfn"] == rc["invested"], (y, b["pn"] + rc["pfn"], rc["invested"])
    d.table(rows, [W - 90, 30, 30, 30], bold_rows=[4, 6, 10, 11], font=7.8)
    d.P(f"La posizione finanziaria netta è negativa per {U(-rc['pfn'])} euro, cioè la società dispone di liquidità superiore al debito bancario residuo. La liquidità è aumentata di {U(b['cash'] - b0['cash'])} euro; il debito finanziario si è ridotto di {U(b0['loan'] - b['loan'])} euro per il rimborso delle rate del finanziamento chirografario. "
        f"Il capitale circolante netto è {'aumentato' if rc['ccn'] > rc0['ccn'] else 'diminuito'} di {U(abs(rc['ccn'] - rc0['ccn']))} euro, soprattutto per l'andamento dei crediti verso clienti, cresciuti con i ricavi.")

    d.H2("Indicatori di bilancio")
    dso = b["trade"] / p["revenue"] * 365
    dso0 = b0["trade"] / p0["revenue"] * 365
    dpo = b["suppliers"] / (p["b6"] + p["b7"] + p["b8"]) * 365
    dpo0 = b0["suppliers"] / (p0["b6"] + p0["b7"] + p0["b8"]) * 365
    quick = (b["cash"] + b["trade"] + b["tax_cr"] + b["other_cr"]) / max(1, b["debts"] - b["loan_long"] + b["accrued"])
    quick0 = (b0["cash"] + b0["trade"] + b0["tax_cr"] + b0["other_cr"]) / max(1, b0["debts"] - b0["loan_long"] + b0["accrued"])
    rows = [["Indicatore", "Formula", f"{y}", f"{y - 1}"],
            ["ROE", "Utile / patrimonio netto iniziale", pct(r["roe"]), pct(r0["roe"])], ["ROI", "EBIT / totale attivo", pct(r["roi"]), pct(r0["roi"])], ["ROS", "EBIT / ricavi", pct(r["ros"]), pct(r0["ros"])],
            ["EBITDA margin", "EBITDA / ricavi", PCT(rc["ebitda"], p["revenue"]), PCT(rc0["ebitda"], p0["revenue"])], ["Incidenza del personale", "Costo del personale / ricavi", PCT(rc["staff"], p["revenue"]), PCT(rc0["staff"], p0["revenue"])],
            ["Indice di liquidità corrente", "Attivo corrente / debiti a breve", f2(r["current_ratio"]), f2(r0["current_ratio"])], ["Indice di liquidità secondaria (quick ratio)", "(Liquidità + crediti) / passività a breve", f2(quick), f2(quick0)],
            ["Indice di indebitamento", "Debiti / patrimonio netto", f2(r["debt_equity"]), f2(r0["debt_equity"])], ["Indice di autonomia finanziaria", "Patrimonio netto / totale attivo", PCT(b["pn"], b["assets"]), PCT(b0["pn"], b0["assets"])],
            ["Copertura delle immobilizzazioni", "Patrimonio netto / immobilizzazioni", f2(b["pn"] / b["fixed"]), f2(b0["pn"] / b0["fixed"])],
            ["Giorni medi di incasso (DSO)", "Crediti clienti / ricavi × 365", f"{dso:.0f} giorni", f"{dso0:.0f} giorni"], ["Giorni medi di pagamento (DPO)", "Fornitori / costi esterni × 365", f"{dpo:.0f} giorni", f"{dpo0:.0f} giorni"],
            ["Ricavi per dipendente", "Ricavi / numero medio dipendenti", U(round(p["revenue"] / M.EMPLOYEES[y])), U(round(p0["revenue"] / M.EMPLOYEES[y - 1]))]]
    d.table(rows, [58, W - 134, 38, 38], align_right_from=2, font=7.8, zebra=True)

    d.H1("4. Investimenti, ricerca e sviluppo")
    d.P(f"Nell'esercizio sono stati effettuati investimenti in immobilizzazioni immateriali per {U(sum(x['capex'] for x in ia))} euro e in immobilizzazioni materiali per {U(sum(x['capex'] for x in ta))} euro, in prevalenza macchine d'ufficio elettroniche, server e apparati di test. "
        f"L'attività di ricerca e sviluppo ha riguardato la piattaforma Atlas per l'analisi predittiva dei costi delle PMI; i costi sostenuti sono stati in parte capitalizzati ({U(p['capitalized'])} euro) e hanno dato diritto al credito d'imposta per ricerca e sviluppo di {U(p['grants'])} euro.")
    d.table([["Progetto di ricerca e sviluppo", "Obiettivo", "Stato al 31/12"], ["Motore di calcolo deterministico", "Calcolare in modo riproducibile i contributi recuperabili da un bilancio, con traccia di ogni passaggio", "Completato, in manutenzione evolutiva"],
             ["Lettura dei documenti contabili", "Estrarre automaticamente le voci di bilancio, F24 e cedolini con indicazione dell'affidabilità", "Rilascio della versione 2"], ["Archivio delle regole dei bandi", "Rappresentare le regole di bandi e agevolazioni come dati strutturati e versionati", "40 bandi codificati"],
             ["Assistente di inserimento dati", "Guidare l'utente nella compilazione dei dati mancanti con spiegazioni in linguaggio semplice", "Prototipo in sperimentazione"]], [48, W - 98, 50], align_right_from=9, font=8)
    d.P("La società non possiede azioni proprie né quote di società controllanti, non ha filiali o sedi secondarie e non ha effettuato nell'esercizio acquisti o alienazioni di tali titoli, né direttamente né tramite società fiduciarie o interposta persona.")

    d.H1("5. Personale, sicurezza, ambiente e protezione dei dati")
    q, imp, app = M.HEADCOUNT_SPLIT[y]
    d.P(f"L'organico medio è passato a {M.EMPLOYEES[y]} unità (di cui {q} quadro, {imp} impiegati e {app} apprendisti) dalle {M.EMPLOYEES[y - 1]} dell'esercizio precedente, con un costo complessivo del personale di {U(rc['staff'])} euro. "
        f"Sono state erogate {M.EMPLOYEES[y] * 21} ore di formazione (in media 21 ore per dipendente), comprese le ore obbligatorie sulla sicurezza sul lavoro (D.Lgs. 81/2008). Nell'esercizio non si sono verificati infortuni sul lavoro né contenziosi con il personale; non vi sono addebiti in materia di mobbing.")
    d.table([["Area", "Misura adottata", "Esito dell'esercizio"], ["Salute e sicurezza", "Documento di valutazione dei rischi, visite mediche, formazione obbligatoria, medico competente", "Nessun infortunio; visite effettuate al 100% del personale"],
             ["Welfare", "Buoni pasto, assistenza sanitaria integrativa, flessibilità oraria e lavoro agile", "Adesione del 100% dei dipendenti"], ["Pari opportunità", "Politica di selezione basata sul merito, monitoraggio dei livelli retributivi", "Quota femminile 47% dell'organico"],
             ["Ambiente", "Raccolta differenziata, riduzione del consumo di carta, energia da fonti rinnovabili per la sede", "Consumi energetici in linea con l'anno precedente"],
             ["Sicurezza delle informazioni", "Sistema di gestione ISO/IEC 27001, controllo degli accessi, backup cifrati, test di penetrazione periodici", "Nessun incidente di sicurezza rilevante"],
             ["Protezione dei dati personali", "Registro dei trattamenti, nomine a responsabile, valutazioni d'impatto per i nuovi servizi (GDPR)", "Nessuna violazione notificata al Garante"]], [32, W - 98, 66], align_right_from=9, font=7.8)

    d.H1("6. Principali rischi e incertezze")
    rows = [["Rischio", "Descrizione ed esposizione", "Presidio"],
            ["Rischio di credito", f"Clienti prevalentemente imprese e pubbliche amministrazioni italiane; crediti verso clienti {U(b['trade'])} euro, il {PCT(b['trade'], b['assets'])} dell'attivo; esposizione frazionata", "Fondo svalutazione prudenziale, solleciti sistematici, fidi per cliente"],
            ["Rischio di liquidità", f"Disponibilità liquide per {U(b['cash'])} euro e finanziamento a medio termine in ammortamento; la copertura degli impegni a breve è {f2(r['current_ratio'])} volte", "Pianificazione di tesoreria mensile, linee di credito non utilizzate"],
            ["Rischio di tasso", f"Il finanziamento ({U(b['loan'])} euro residui) è a tasso variabile: un punto percentuale incide per circa {U(round(b['loan'] * 0.01 * 0.6))} euro sugli oneri annui", "Rimborso anticipato possibile senza penali"],
            ["Rischio di cambio", "Operazioni in valuta marginali (meno del 2% dei ricavi)", "Fatturazione in euro per i nuovi contratti esteri"],
            ["Rischio operativo e di personale chiave", "La crescita dipende dalla capacità di assumere e trattenere sviluppatori e analisti", "Welfare, formazione, piano di successione, documentazione del codice"],
            ["Rischio normativo", "Le regole di bandi e agevolazioni su cui si basa parte dei ricavi e degli investimenti possono cambiare", "Monitoraggio mensile e archivio delle regole versionato"],
            ["Rischio informatico", "Attacchi alla piattaforma o ai dati dei clienti", "ISO/IEC 27001, backup, polizza cyber, test di penetrazione"]]
    d.table(rows, [34, W - 106, 72], align_right_from=9, font=7.8, zebra=True)
    d.H2("Analisi di sensibilità")
    base = p["ebit"]
    d.table([["Variazione ipotizzata", "Effetto sul risultato operativo (euro)", "Risultato operativo risultante"], ["Ricavi -10% con costi invariati", U(-round(p["revenue"] * 0.10)), U(base - round(p["revenue"] * 0.10))],
             ["Ricavi -5% con costi invariati", U(-round(p["revenue"] * 0.05)), U(base - round(p["revenue"] * 0.05))], ["Costo del lavoro +3%", U(-round(rc["staff"] * 0.03)), U(base - round(rc["staff"] * 0.03))],
             ["Costi esterni +5%", U(-round(rc["ext"] * 0.05)), U(base - round(rc["ext"] * 0.05))], ["Tassi di interesse +200 punti base (effetto sugli oneri)", U(-round(b["loan"] * 0.02 * 0.6)), U(base - round(b["loan"] * 0.02 * 0.6))]],
            [W - 96, 52, 44], font=8)
    d.H2("Continuità aziendale")
    d.table([["Verifica della continuità (12 mesi successivi alla data di bilancio)", "Importo (euro)"], ["Disponibilità liquide al 31/12", U(b["cash"])], ["Rate del finanziamento in scadenza entro 12 mesi", U(-b["loan_short"])], ["Imposte e contributi del primo trimestre (stima)", U(-round((b["tax_debt"] + b["social"]) * 0.85))],
             ["Costo mensile del personale (stima)", U(-round(rc["staff"] / 12))], ["Mesi di costo del personale coperti dalla sola liquidità residua", f2((b["cash"] - b["loan_short"]) / (rc["staff"] / 12))]], [W - 40, 40], font=8)
    d.P("Sulla base delle verifiche sopra esposte e del portafoglio ordini acquisito, gli amministratori hanno concluso che non sussistono incertezze significative sulla capacità della società di continuare a operare come entità in funzionamento per almeno dodici mesi dalla data di riferimento del bilancio.")

    d.H1("7. Fatti di rilievo successivi e evoluzione prevedibile della gestione")
    nxt_rev = round(p["revenue"] * (1 + {2023: 0.22, 2024: 0.19, 2025: 0.17}[y]))
    d.P(f"Per l'esercizio successivo si prevede una prosecuzione della crescita dei ricavi, trainata dai canoni della piattaforma e dai nuovi contratti già acquisiti, con ricavi attesi intorno a {U(nxt_rev)} euro, ulteriori assunzioni nell'area sviluppo e nell'area commerciale e il completamento del progetto Atlas. "
        "Sono allo studio la partecipazione a bandi per la ricerca e l'innovazione e un investimento in infrastruttura cloud. Non si prevedono eventi in grado di compromettere la continuità aziendale.")
    d.table([["Budget dell'esercizio successivo (indicativo)", "Importo (euro)", "Variazione"], ["Ricavi delle vendite e delle prestazioni", U(nxt_rev), PCT(nxt_rev - p["revenue"], p["revenue"])], ["Costo del personale", U(round(rc["staff"] * 1.2)), "20,0%"],
             ["EBITDA atteso", U(round(rc["ebitda"] * 1.28)), "28,0%"], ["Investimenti in immobilizzazioni", U(round((sum(x["capex"] for x in ia) + sum(x["capex"] for x in ta)) * 1.35)), "35,0%"]], [W - 80, 40, 40], font=8)
    d.H1("8. Proposta di destinazione dell'utile")
    prop = {2022: 40000, 2023: 60000, 2024: 80000, 2025: 90000}[y]
    d.P(f"Vi proponiamo di approvare il bilancio così come presentato e di destinare l'utile dell'esercizio di euro {U(p['net'])} quanto a euro {U(prop)} a distribuzione di dividendi ai soci e quanto a euro {U(p['net'] - prop)} a riserva straordinaria.")
    d.P(f"Torino, {approved}. L'Amministratore unico: Giulia Ferraris.", left=True)
