"""Business plan: approfondimenti (storia finanziaria, moduli, mercati, marketing, qualità, formazione, note alle voci, allegati di dettaglio)."""
from __future__ import annotations

from typing import Dict, List

from . import bp
from . import ledger as LG
from . import model as M
from .bp_doc import KPI, MONTHS, pcts, recurring
from .bp_fin import A, annual_pl_rows
from .pdfkit import Doc, pct, units

U = units
YEARS = bp.YEARS


def _w(d: Doc) -> float:
    return d.width / 2.8346


def history(d: Doc) -> None:
    W = _w(d)
    d.H1("2.6 Andamento storico commentato (2022-2025)")
    rows = [["Indicatore", "2022", "2023", "2024", "2025"]]
    for l, f in (("Ricavi (euro)", lambda y: U(M.pl(y)["revenue"])), ("Crescita dei ricavi", lambda y: pcts(M.pl(y)["revenue"] - M.pl(y - 1)["revenue"], M.pl(y - 1)["revenue"]) if y > 2022 else "n.d."),
                 ("EBITDA (euro)", lambda y: U(M.ratio_notes(y)["ebitda"])), ("EBITDA / ricavi", lambda y: pcts(M.ratio_notes(y)["ebitda"], M.pl(y)["revenue"])), ("Utile netto (euro)", lambda y: U(M.pl(y)["net"])),
                 ("Dipendenti medi", lambda y: str(M.EMPLOYEES[y])), ("Ricavi per dipendente (euro)", lambda y: U(round(M.pl(y)["revenue"] / M.EMPLOYEES[y]))), ("Patrimonio netto (euro)", lambda y: U(M.balance(y)["pn"])),
                 ("Disponibilità liquide (euro)", lambda y: U(M.balance(y)["cash"])), ("Debiti verso banche (euro)", lambda y: U(M.balance(y)["loan"])), ("Investimenti dell'anno (euro)", lambda y: U(sum(r["capex"] for r in M.fixed_assets("intang")[y]) + sum(r["capex"] for r in M.fixed_assets("tang")[y])))):
        rows.append([l] + [f(y) for y in M.ALL_YEARS])
    d.table(rows, [W - 120, 30, 30, 30, 30], font=8, zebra=True, align_right_from=1)
    d.P(f"<b>2022.</b> L'azienda ha chiuso con ricavi di {U(M.REVENUE[0])} euro e nove dipendenti, ottenendo la certificazione ISO 9001 e i primi crediti d'imposta per ricerca e sviluppo. Il finanziamento del 2020 pesava ancora per {U(M.balance(2022)['loan'])} euro sul bilancio, riducendo la flessibilità finanziaria.")
    d.P(f"<b>2023.</b> I ricavi sono saliti a {U(M.REVENUE[1])} euro (+{pct(M.REVENUE[1] / M.REVENUE[0] - 1)}) grazie ai primi canoni di Atlas e a due nuovi contratti con enti locali; l'organico è passato a undici persone e l'azienda ha ottenuto la certificazione ISO/IEC 27001. "
        f"L'utile ({U(M.pl(2023)['net'])} euro) è stato in parte distribuito (40.000 euro) e in parte destinato a riserva.")
    d.P(f"<b>2024.</b> I ricavi hanno superato 1,3 milioni di euro ({U(M.REVENUE[2])}); l'assunzione di due sviluppatori e di una persona per l'amministrazione ha portato l'organico a 13 persone. L'azienda ha ottenuto il voucher camerale per la digitalizzazione e ha avviato il programma di licenze agli studi professionali.")
    d.P(f"<b>2025.</b> I ricavi sono stati di {U(M.REVENUE[3])} euro (+{pct(M.REVENUE[3] / M.REVENUE[2] - 1)}), con un utile di {U(M.pl(2025)['net'])} euro e una liquidità di {U(M.balance(2025)['cash'])} euro. Sono entrati un data scientist, un commerciale e un apprendista; è stato avviato lo sviluppo del motore di calcolo deterministico. "
        "Il credito d'imposta per ricerca e sviluppo è salito a 42.000 euro.")


def modules(d: Doc) -> None:
    W = _w(d)
    d.H1("3.5 Descrizione dei moduli di Atlas")
    mods = [("Acquisizione documenti", "Legge i PDF testuali e le scansioni dei bilanci, dei modelli F24 e delle buste paga. Ogni dato estratto riceve un grado di affidabilità; i dati incerti vengono sottoposti all'utente, che li conferma o li corregge. Nessun dato incerto entra nei calcoli senza conferma."),
            ("Profilo dell'azienda", "Raccoglie i dati dell'impresa (sede, ATECO, dimensione, dipendenti, bilanci) con l'indicazione del documento da cui ciascuno proviene. Quando un dato manca lo dichiara, senza inventarlo."),
            ("Previsione di bilancio", "Parte dall'ultimo bilancio e stima costi e ricavi dell'anno successivo: per ogni categoria applica la variazione indicata dall'utente, quella del suo modello di previsione o quella che risulta dai due ultimi bilanci, con la spiegazione dei numeri."),
            ("Biblioteca dei bandi", "Contiene le regole di bandi e agevolazioni (spese ammissibili, aliquote, tetti, finestre temporali) come dati strutturati e versionati, ognuna con il passaggio del testo ufficiale da cui deriva."),
            ("Allocazione ottimale", "Decide quale bando paga quale spesa, rispettando i tetti dei fondi, il cumulo e il de minimis, e restituisce il massimo recuperabile. Il risultato è sempre lo stesso a parità di dati."),
            ("De minimis automatico", "Stima il tetto residuo dagli aiuti dichiarati nei bilanci degli ultimi tre esercizi e lo usa nel calcolo, dichiarando la base della stima."),
            ("Dossier e registro firmato", "Produce il documento per il cliente e registra ogni esecuzione in una catena di impronte firmate, verificabile da un revisore."),
            ("Assistente di inserimento", "Guida l'utente passo per passo, chiede solo i valori che mancano e li spiega in parole semplici.")]
    for t, txt in mods:
        d.P(f"<b>{t}.</b> {txt}")
    d.H1("3.6 Casi d'uso (clienti di esempio)")
    d.table([["Cliente tipo", "Esigenza", "Risultato con Atlas", "Tempo risparmiato"], ["Studio commerciale con 60 clienti", "Individuare i bandi adatti a ciascun cliente ogni trimestre", "Elenco dei bandi adatti con importo stimato per cliente e dossier pronti", "Da 3 ore a 20 minuti per cliente"],
             ["Boutique di finanza agevolata", "Costruire il budget del bando e prevedere cosa verrebbe ridotto", "Budget per bando con le voci da adeguare e i tetti rispettati", "Da 2 giorni a mezza giornata per pratica"],
             ["PMI manifatturiera con CFO esterno", "Capire quanto potrebbe recuperare nell'anno", "Potenziale massimo con tutti i bandi insieme e quota a carico", "Immediato, con scenario prudente e massimo"],
             ["Ente pubblico con consulente", "Verificare la coerenza del budget presentato con le regole del bando", "Controllo dei criteri con la fonte di ogni regola", "Da 1 giorno a 2 ore"]], [38, 44, W - 134, 52], align_right_from=9, font=7.6, zebra=True)
    d.H1("3.7 Proprietà intellettuale e dati")
    d.P("Il codice di Atlas è di proprietà esclusiva della società; i marchi ATLAS e Meridiana sono registrati presso l'UIBM. I dati dei clienti restano di proprietà dei clienti e sono trattati come responsabile del trattamento; non sono usati per addestrare modelli né ceduti a terzi. "
        "I contratti con i collaboratori prevedono la cessione dei diritti sulle opere dell'ingegno realizzate per la società e clausole di riservatezza.")


def market_more(d: Doc) -> None:
    W = _w(d)
    d.H1("4.4 Analisi dei segmenti")
    segs = [("Imprese manifatturiere", "Bisogno prevalente: stimare quanto recuperare da incentivi sugli investimenti (beni strumentali, transizione digitale) e dal credito d'imposta ricerca e sviluppo. Il processo d'acquisto coinvolge il CFO o il consulente esterno; il ciclo di vendita dura 4-8 settimane; la sensibilità al prezzo è media."),
            ("Imprese di servizi", "Bisogno prevalente: finanziare formazione, assunzioni e digitalizzazione. Il decisore è spesso l'imprenditore; il ciclo di vendita è breve (2-4 settimane); la sensibilità al prezzo è alta, quindi il piano Base è il canale d'ingresso."),
            ("Studi professionali e società di consulenza", "Bisogno prevalente: seguire più clienti con lo stesso organico. Acquistano licenze per l'intero studio; il ciclo di vendita è di 6-10 settimane e richiede una dimostrazione; sono i clienti con il valore più alto e il churn più basso."),
            ("Enti pubblici locali", "Bisogno prevalente: sviluppare servizi digitali per i cittadini e gestire dati. Acquistano tramite procedure di affidamento; i tempi di pagamento sono più lunghi; il rischio di credito è minimo.")]
    for t, txt in segs:
        d.P(f"<b>{t}.</b> {txt}")
    d.H1("4.5 Benchmark dei prezzi")
    d.table([["Soluzione (categoria)", "Modello di prezzo", "Prezzo indicativo annuo (euro)", "Cosa include"], ["Portale di segnalazione dei bandi", "Abbonamento", "300 - 900", "Elenco dei bandi aperti e avvisi"], ["Software di budgeting per PMI", "Abbonamento per utente", "1.200 - 4.800", "Budget, scenari, report"],
             ["Consulenza di finanza agevolata", "Percentuale sul contributo (3-8%) più quota fissa", "5.000 - 30.000 a pratica", "Analisi, domanda e rendicontazione"], ["Atlas piano Base", "Abbonamento", "1.200", "Profilo, previsione, bandi adatti"], ["Atlas piano Professional", "Abbonamento", "2.400", "Più allocazione, de minimis, dossier"],
             ["Atlas piano Studio", "Licenza per studio", "9.600", "Clienti illimitati, registro firmato"]], [58, 50, 36, W - 144], align_right_from=9, font=7.6, zebra=True)
    d.P("Il prezzo di Atlas è collocato nella parte bassa della fascia dei software di budgeting e ben al di sotto della consulenza, a parità di risultato sul calcolo del recupero; il valore per lo studio è nella riduzione del tempo di analisi per cliente.")


def marketing_more(d: Doc) -> None:
    W = _w(d)
    d.H1("6.6 Piano di marketing per trimestre")
    plan = {2026: ["Rinnovo del sito e delle pagine di prodotto; avvio campagne a risposta diretta", "Ciclo di webinar con associazioni di categoria; partecipazione a una fiera regionale", "Pubblicazione di casi d'uso; campagne per gli studi", "Evento di presentazione dell'assistente di inserimento; offerta di fine anno"],
            2027: ["Lancio della versione 2.0 della lettura dei documenti; campagna stampa di settore", "Programma partner con 20 studi; webinar mensili", "Partecipazione a due fiere nazionali; contenuti sui bandi europei", "Eventi con i clienti; offerte di rinnovo pluriennale"],
            2028: ["Estensione ai bandi europei: campagna dedicata", "Programma di referral tra studi; ricerca sulla produttività degli studi", "Partecipazione a fiere nazionali; nuovi connettori", "Evento annuale degli utenti di Atlas"]}
    rows = [["Anno", "Primo trimestre", "Secondo trimestre", "Terzo trimestre", "Quarto trimestre"]]
    for y in YEARS:
        rows.append([str(y)] + plan[y])
    d.table(rows, [14, (W - 14) / 4, (W - 14) / 4, (W - 14) / 4, (W - 14) / 4], align_right_from=9, font=7.4, zebra=True)
    d.H1("6.7 Partnership e canale indiretto")
    d.table([["Tipo di partner", "Numero obiettivo 2028", "Accordo", "Beneficio per Meridiana"], ["Studi commerciali e di consulenza", "48 (licenze)", "Licenza annuale per studio", "Ricavi ricorrenti e prescrizione verso i clienti"], ["Associazioni di categoria", "6", "Convenzione per gli associati con sconto del 15%", "Accesso a migliaia di imprese"],
             ["Camere di Commercio e agenzie di sviluppo", "3", "Progetti pilota e webinar congiunti", "Credibilità e lead qualificati"], ["Produttori di software gestionali", "5", "Connettori e referral", "Integrazione e nuova base clienti"], ["Università e centri di ricerca", "2", "Accordi di ricerca contrattuale", "Credito d'imposta e competenze"]],
            [48, 28, 52, W - 128], align_right_from=9, font=7.6, zebra=True)


def operations_more(d: Doc) -> None:
    W = _w(d)
    d.H1("7.4 Processo di sviluppo e qualità")
    d.P("Il processo di sviluppo è iterativo, con cicli di due settimane. Ogni modifica passa da una richiesta tracciata, una revisione tra pari, test automatici e un rilascio controllato; le regole dei bandi sono modificate solo tramite una procedura che conserva il testo di origine e la data di verifica. "
        "Le non conformità, i reclami e gli incidenti sono registrati e analizzati ogni trimestre dal responsabile qualità, nell'ambito del riesame della direzione previsto dalla ISO 9001.")
    d.table([["Processo", "Responsabile", "Frequenza", "Evidenza"], ["Pianificazione dello sviluppo", "Responsabile sviluppo", "Ogni 2 settimane", "Backlog e verbale di pianificazione"], ["Revisione del codice", "Sviluppatori senior", "Ad ogni modifica", "Richiesta di modifica approvata"],
             ["Test automatici e di regressione", "Quality assurance", "Ad ogni rilascio", "Rapporto dei test"], ["Aggiornamento delle regole dei bandi", "Analista dei bandi", "Entro 5 giorni dalla pubblicazione", "Versione della regola con fonte"],
             ["Gestione degli incidenti", "Responsabile sicurezza", "A evento", "Registro degli incidenti"], ["Riesame della direzione", "Amministratore unico", "Annuale", "Verbale del riesame"], ["Audit interni", "Responsabile qualità", "Annuale", "Rapporti di audit"]], [58, 38, 38, W - 134], align_right_from=9, font=7.6, zebra=True)
    d.H1("7.5 Continuità operativa")
    d.table([["Scenario", "Impatto", "Misura", "Obiettivo di ripristino"], ["Indisponibilità di una regione cloud", "Servizio degradato", "Spostamento automatico sulla seconda regione", "30 minuti"], ["Perdita della base dati", "Perdita di dati", "Backup cifrati giornalieri e log continui", "4 ore; perdita massima 15 minuti"],
             ["Indisponibilità della sede", "Lavoro non in sede", "Lavoro agile già predisposto, postazioni portatili", "Immediato"], ["Assenza prolungata di una persona chiave", "Ritardo di attività", "Affiancamento e documentazione", "Sostituzione operativa in 10 giorni"], ["Attacco informatico", "Compromissione dei dati", "Procedura di incident response e polizza cyber", "Contenimento in 2 ore"]],
            [52, 34, W - 126, 40], align_right_from=9, font=7.6, zebra=True)


def people_more(d: Doc) -> None:
    W = _w(d)
    d.H1("8.5 Piano di formazione 2026-2028")
    rows = [["Area di formazione", "2026 (ore)", "2027 (ore)", "2028 (ore)", "Destinatari"]]
    heads = {y: bp.staff()["heads"][[m for m in range(bp.N) if bp.MONTHS[m] == (y, 12)][0]] for y in YEARS}
    for l, k, who in (("Tecnica (linguaggi, architetture, cloud)", 11, "Sviluppo e dati"), ("Sicurezza informatica e protezione dei dati", 4, "Tutti"), ("Sicurezza sul lavoro (D.Lgs. 81/2008)", 3, "Tutti"), ("Competenze commerciali e relazionali", 2, "Commerciale e clienti"), ("Gestione dei progetti e metodologie agili", 1.5, "Progetto e sviluppo")):
        rows.append([l] + [U(round(heads[y] * k)) for y in YEARS] + [who])
    rows.append(["Totale ore di formazione"] + [U(round(heads[y] * 21.5)) for y in YEARS] + [""])
    d.table(rows, [W - 120, 22, 22, 22, 54], align_right_from=1, font=7.8, zebra=True, bold_rows=[6])
    d.H1("8.6 Matrice delle competenze")
    d.table([["Competenza", "Sviluppo piattaforma", "Sviluppo commesse", "Dati e analisi", "Progetto e design", "Commerciale"], ["Architetture a servizi e cloud", "Alta", "Media", "Media", "Bassa", "-"], ["Basi dati e calcolo numerico", "Alta", "Media", "Alta", "-", "-"],
             ["Lettura e classificazione di documenti", "Media", "-", "Alta", "-", "-"], ["Interfacce e usabilità", "Media", "Alta", "-", "Alta", "-"], ["Conoscenza dei bandi e degli incentivi", "Media", "-", "Media", "Media", "Alta"], ["Gestione di progetti finanziati", "-", "Media", "-", "Alta", "Media"],
             ["Sicurezza delle informazioni", "Alta", "Media", "Media", "-", "-"]], [58, 28, 28, 24, 24, W - 162], align_right_from=1, font=7.6, zebra=True)


def rd_more(d: Doc) -> None:
    W = _w(d)
    d.H1("9.4 Pacchetti di lavoro del progetto Atlas 2026-2028")
    d.table([["Pacchetto", "Periodo", "Contenuto", "Costo previsto (euro)", "Risultato atteso"], ["WP-A Motore di calcolo e regole", "2026-2027", "Ampliamento a 100 bandi, regole per i bandi europei, verifica statistica", U(round(sum(bp.RD_INVEST.values()) * 0.34)), "Scostamento tra stima e spesa effettiva < 10%"],
             ["WP-B Lettura dei documenti", "2026-2027", "Versione 2.0, riconoscimento delle scansioni, 5 nuove tipologie di documento", U(round(sum(bp.RD_INVEST.values()) * 0.24)), "Voci riconosciute > 95%"],
             ["WP-C Interfaccia e assistente", "2026-2028", "Assistente di inserimento, dossier, scenari", U(round(sum(bp.RD_INVEST.values()) * 0.22)), "Completamento del profilo senza supporto per il 70%"], ["WP-D Sicurezza e registro firmato", "2027-2028", "Registro verificabile da terzi, controllo accessi avanzato", U(round(sum(bp.RD_INVEST.values()) * 0.12)), "Verifica indipendente del registro"],
             ["WP-E Connettori", "2027-2028", "Integrazione con 5 gestionali contabili", U(round(sum(bp.RD_INVEST.values()) * 0.08)), "60 imprese collegate"]], [38, 20, W - 140, 30, 52], align_right_from=9, font=7.4, zebra=True)


def notes_to_plan(d: Doc) -> None:
    W = _w(d)
    pl = bp.pl()
    d.page_break()
    d.title_block("NOTE ALLE VOCI DEL PIANO ECONOMICO")
    d.H1("Ricavi")
    d.P("I ricavi 2026-2028 sono ottenuti applicando al totale dichiarato la ripartizione per linea di attività e distribuendo ciascuna linea sui mesi con una curva di crescita e un profilo stagionale (agosto debole, dicembre forte per la chiusura dei progetti). "
        "Per i canoni la curva cresce al 40% annuo; per le commesse al 10%; per la consulenza all'8%; per la formazione al 6%. Il piano non assume ricavi da clienti non ancora identificati oltre il 22% dei canoni del 2028.")
    rc = {y: recurring(y) for y in YEARS}
    d.table([["Composizione dei ricavi da canoni (euro)", "2026", "2027", "2028"], ["Imprese clienti (ricavo medio per impresa × media dei clienti)"] + [U(rc[y]["companies"]) for y in YEARS], ["Studi professionali (9.600 euro × media delle licenze)"] + [U(rc[y]["studios"]) for y in YEARS],
             ["Hosting e manutenzione applicativa ricorrente"] + [U(rc[y]["hosting"]) for y in YEARS], ["Totale canoni e licenze"] + [U(rc[y]["total"]) for y in YEARS]], [W - 90, 30, 30, 30], font=8, bold_rows=[4], align_right_from=1)
    d.H1("Costi esterni")
    d.P("Ogni voce dei costi esterni è determinata come percentuale dei ricavi, con profilo mensile coerente con la natura del costo: gli affitti sono costanti, il marketing segue il calendario di campagne e fiere, le licenze cloud seguono i ricavi in modo meno che proporzionale, consulenze e altri costi seguono i ricavi. "
        "Le percentuali partono da quelle del 2025 (28,8% dei ricavi) e scendono al 27,0% nel 2028 per effetto delle economie di scala.")
    d.H1("Costo del personale")
    d.P("Il costo del personale è costruito persona per persona: ciascuna ha un costo azienda annuo di partenza (retribuzione lorda, oneri, TFR), rivalutato del 2,5% ogni gennaio; sono considerate 14 mensilità (giugno e dicembre doppie). "
        "A questo costo si aggiunge il 13% per premi di risultato, straordinari, buoni pasto e welfare. Le otto assunzioni previste entrano nei mesi indicati nell'allegato C.")
    d.H1("Ammortamenti")
    dep = bp.depreciation()
    d.table([["Ammortamenti (euro)", "2026", "2027", "2028"], ["Immobilizzazioni immateriali"] + [U(A(dep["immateriali"], y)) for y in YEARS], ["Immobilizzazioni materiali"] + [U(A(dep["materiali"], y)) for y in YEARS], ["Totale ammortamenti"] + [U(A(pl["ammortamenti"], y)) for y in YEARS]],
            [W - 90, 30, 30, 30], font=8, bold_rows=[3], align_right_from=1)
    d.P("Gli ammortamenti dei beni in essere seguono il piano del registro dei cespiti al 31/12/2025; i nuovi investimenti sono ammortizzati dal mese successivo all'acquisto, con le aliquote di bilancio (20% sviluppo, apparati e macchine d'ufficio; 33% software).")
    d.H1("Oneri finanziari e imposte")
    d.P("Gli oneri finanziari comprendono gli interessi sul finanziamento esistente (5,05%) e sul nuovo (5,35%) calcolati sul debito medio mensile e 1.200 euro l'anno di commissioni su affidamenti e fidejussioni. "
        "L'IRES è calcolata al 24% sul risultato prima delle imposte al netto del credito d'imposta non imponibile, con le variazioni in aumento per i costi indeducibili (0,6% dei ricavi) e la deduzione ACE; l'IRAP al 3,90% sul risultato operativo.")
    d.H1("Riconciliazione con il bilancio 2025")
    p5 = M.pl(2025)
    rev26 = bp.REV_TARGET[2026]
    d.table([["Passaggio dal 2025 al 2026 (euro)", "Importo"], ["Utile netto 2025", U(p5["net"])], ["Crescita dei ricavi", U(rev26 - p5["revenue"])], ["Maggiori costi esterni", U(-(A(pl["costi_esterni"], 2026) - (p5["b6"] + p5["b7"] + p5["b8"])))],
             ["Maggior costo del personale", U(-(A(pl["personale"], 2026) - (p5["b9a"] + p5["b9b"] + p5["b9c"] + p5["b9e"])))], ["Variazione degli altri ricavi (capitalizzazioni e credito d'imposta)", U(A(pl["lavori_interni"], 2026) + A(pl["contributi"], 2026) + A(pl["altri_ricavi"], 2026) - (p5["capitalized"] + p5["grants"] + p5["other_income"] + p5["wip_delta"]))],
             ["Variazione degli ammortamenti e altre voci", U(-(A(pl["ammortamenti"], 2026) + A(pl["svalutazione_crediti"], 2026) + A(pl["oneri_diversi"], 2026) - (p5["b10a"] + p5["b10b"] + p5["b10d"] + p5["b14"])))], ["Variazione di oneri finanziari e imposte", U(-(A(pl["oneri_finanziari"], 2026) - A(pl["proventi_finanziari"], 2026) + A(pl["imposte"], 2026)) + (p5["int_expense"] - p5["int_income"] - p5["fx"] + p5["taxes"]))],
             ["Utile netto 2026", U(A(pl["utile"], 2026))]], [W - 40, 40], font=8, bold_rows=[1, 8], align_right_from=1)


def annex_customers(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.title_block("ALLEGATO F - CLIENTI E RICAVI RICORRENTI PER MESE")
    rev = bp.revenue()[bp.REV_LINES[0]]
    for y in YEARS:
        idx = [m for m in range(bp.N) if bp.MONTHS[m][0] == y]
        ce0, ce1 = KPI["companies_end"][y - 1], KPI["companies_end"][y]
        se0, se1 = KPI["studios_end"][y - 1], KPI["studios_end"][y]
        comp = [round(ce0 + (ce1 - ce0) * (k + 1) / 12) for k in range(12)]
        stu = [round(se0 + (se1 - se0) * (k + 1) / 12) for k in range(12)]
        d.H2(f"Anno {y}")
        for half, label in ((0, "Gennaio-giugno"), (1, "Luglio-dicembre")):
            ii = list(range(half * 6, half * 6 + 6))
            rows = [[f"{label} {y}"] + [MONTHS[k] for k in ii] + ["Fine periodo"]]
            rows.append(["Imprese clienti a fine mese"] + [str(comp[k]) for k in ii] + [str(comp[ii[-1]])])
            rows.append(["Studi con licenza a fine mese"] + [str(stu[k]) for k in ii] + [str(stu[ii[-1]])])
            rows.append(["Ricavi da canoni e licenze del mese (euro)"] + [U(rev[idx[k]]) for k in ii] + [U(sum(rev[idx[k]] for k in ii))])
            d.table(rows, [W - 119] + [17] * 7, font=7, align_right_from=1, zebra=True)


def annex_depreciation(d: Doc) -> None:
    W = _w(d)
    d.H1("ALLEGATO G - PIANO DEGLI AMMORTAMENTI PER CLASSE (euro)")
    cx = bp.capex()
    dep = bp.depreciation()
    rows = [["Classe", "Valore netto al 31/12/2025", "Investimenti 2026-28", "Ammortamenti 2026-28", "Valore netto al 31/12/2028"]]
    ni = M.balance(2025)["intang"]
    nt = M.balance(2025)["tang"]
    ci = sum(sum(cx[k]) for k in ("Sviluppo piattaforma Atlas (costi capitalizzati)", "Software e licenze perpetue"))
    ct = sum(sum(cx[k]) for k in ("Infrastruttura cloud e apparati di test", "Macchine d'ufficio e arredi"))
    rows.append(["Immobilizzazioni immateriali", U(ni), U(ci), U(sum(dep["immateriali"])), U(ni + ci - sum(dep["immateriali"]))])
    rows.append(["Immobilizzazioni materiali", U(nt), U(ct), U(sum(dep["materiali"])), U(nt + ct - sum(dep["materiali"]))])
    d.table(rows, [W - 134, 34, 32, 32, 36], font=8, align_right_from=1)
    d.H1("ALLEGATO H - CALENDARIO DELLE SCADENZE FISCALI E FINANZIARIE")
    d.table([["Scadenza", "Adempimento", "Importo stimato 2026 (euro)"], ["16 di ogni mese", "Versamento ritenute, contributi INPS, IVA mensile (F24)", "Secondo piano mensile"], ["31/03, 30/06, 30/09, 31/12", "Rata trimestrale del finanziamento esistente", U(11250)], ["30/04", "Approvazione del bilancio e dividendi", "-"],
             ["30/06", "Saldo imposte dell'anno precedente e primo acconto", "Secondo piano di tesoreria"], ["16/11", "Secondo acconto IRES e IRAP", "Secondo piano di tesoreria"], ["31/05", "Rinnovo certificazioni ISO", "-"], ["Trimestrale", "Comunicazioni delle liquidazioni IVA", "-"],
             ["Annuale", "Comunicazione per il credito d'imposta ricerca e sviluppo", "-"]], [48, W - 108, 60], align_right_from=9, font=7.8, zebra=True)
