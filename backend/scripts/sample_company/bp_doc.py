"""Business plan 2026-2028 (documento PDF): parte descrittiva, mercato, strategia, organizzazione, investimenti, ipotesi."""
from __future__ import annotations

from typing import Dict, List

from . import bp
from . import ledger as LG
from . import model as M
from . import people as P
from .pdfkit import Doc, pct, units

U = units
CO = M.COMPANY
MONTHS = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]

# indicatori commerciali del piano (clienti con canone attivo a fine anno)
KPI = {"companies_end": {2025: 150, 2026: 270, 2027: 330, 2028: 390}, "studios_end": {2025: 12, 2026: 20, 2027: 34, 2028: 48}, "arpa": {2026: 2300, 2027: 2300, 2028: 2400}, "churn": {2026: 0.09, 2027: 0.08, 2028: 0.07}}
STUDIO_PRICE = 9600


def _w(d: Doc) -> float:
    return d.width / 2.8346


def pcts(a: float, b: float, digits: int = 1) -> str:
    return pct(a / b, digits) if b else "-"


def recurring(y: int) -> Dict[str, int]:
    """Ricavi ricorrenti dell'anno scomposti in canoni delle imprese, licenze agli studi e hosting e manutenzione (residuo)."""
    total = bp.annual(bp.revenue()[bp.REV_LINES[0]], y)
    ce = (KPI["companies_end"][y - 1] + KPI["companies_end"][y]) / 2
    se = (KPI["studios_end"][y - 1] + KPI["studios_end"][y]) / 2
    comp = round(ce * KPI["arpa"][y])
    stu = round(se * STUDIO_PRICE)
    host = total - comp - stu
    assert host > 0, (y, host)
    return {"total": total, "companies": comp, "studios": stu, "hosting": host, "avg_companies": ce, "avg_studios": se}


def cover_and_summary(d: Doc) -> None:
    W = _w(d)
    p5, b5 = M.pl(2025), M.balance(2025)
    d.title_block("BUSINESS PLAN 2026-2028", f"{CO['name']} - documento per finanziatori, bandi e partner (versione di settembre 2026)")
    d.table([["Società", CO["name"]], ["Sede", f"{CO['street']}, {CO['zip']} {CO['city'].title()} ({CO['prov']})"], ["Partita IVA", CO["vat"]], ["Forma giuridica", CO["legal_form"]], ["Capitale sociale", f"euro {U(CO['capital'])}"],
             ["Settore", f"{CO['ateco']} - {CO['ateco_desc']}"], ["Orizzonte del piano", "Gennaio 2026 - dicembre 2028, con dettaglio mensile"], ["Base dei dati storici", "Bilanci d'esercizio 2022-2025 e situazione contabile al 31/08/2026"],
             ["Responsabile del piano", "Giulia Ferraris, amministratore unico, con il supporto di Federica Conti (controllo di gestione)"], ["Versione", "3.1 - settembre 2026"]], [52, W - 52], head=False, align_right_from=9, zebra=True)
    d.H1("Indice")
    d.B(["1. Sintesi del piano", "2. L'azienda: storia, governo e organizzazione", "3. Prodotti e servizi", "4. Il mercato", "5. Concorrenza e analisi SWOT", "6. Strategia commerciale e di marketing",
         "7. Operazioni, tecnologia e qualità", "8. Persone e organizzazione", "9. Investimenti, ricerca e sviluppo", "10. Ipotesi alla base del piano", "11. Piano economico, patrimoniale e finanziario annuale",
         "12. Piano trimestrale", "13. Fabbisogno finanziario, finanziamenti e sostenibilità del debito", "14. Indicatori chiave (KPI)", "15. Scenari e analisi di sensibilità", "16. Rischi e piani di contingenza",
         "17. Governance, sostenibilità e adempimenti", "Allegato A - Piano mensile del conto economico", "Allegato B - Piano mensile della tesoreria e dello stato patrimoniale", "Allegato C - Organico e costo del personale per mese",
         "Allegato D - Dati storici di riferimento", "Allegato E - Glossario"])
    d.small("Documento di prova: l'azienda, le persone e i dati sono completamente fittizi e generati per provare QUANTO. Nessun valore corrisponde a persone o imprese reali.")
    d.page_break()
    d.title_block("1. SINTESI DEL PIANO")
    rev = {y: bp.REV_TARGET[y] for y in bp.YEARS}
    pl = bp.pl()
    d.P("Meridiana Digital Solutions sviluppa software e piattaforme di analisi dei dati per le piccole e medie imprese e per gli enti pubblici locali. Fondata a Torino nel 2016 da due soci, chiude il 2025 con ricavi di "
        f"{U(p5['revenue'])} euro, un utile di {U(p5['net'])} euro e {M.EMPLOYEES[2025]} dipendenti medi (17 persone in organico a settembre 2026). Il piano 2026-2028 prevede una crescita dei ricavi a {U(rev[2028])} euro nel 2028 "
        "(+16% annuo composto), trainata dai canoni della piattaforma Atlas e dalle licenze agli studi professionali, che passano dal 30% al 52% dei ricavi.")
    d.P(f"Il piano finanzia la crescita con l'autofinanziamento, con un nuovo finanziamento chirografario di {U(bp.NEW_LOAN)} euro (erogazione a marzo 2026) e con la cassa esistente ({U(b5['cash'])} euro al 31/12/2025); "
        "non prevede aumenti di capitale. Gli investimenti in ricerca e sviluppo del progetto Atlas sono di 770.000 euro nel triennio, di cui il 35% capitalizzato; l'organico passa da 17 a 25 persone.")
    rows = [["Dati principali (euro)", "2025 (consuntivo)", "2026", "2027", "2028"]]
    rows.append(["Ricavi delle vendite e delle prestazioni", U(p5["revenue"])] + [U(rev[y]) for y in bp.YEARS])
    rows.append(["Crescita dei ricavi", pcts(p5["revenue"] - M.pl(2024)["revenue"], M.pl(2024)["revenue"])] + [pcts(rev[y] - (rev[y - 1] if y > 2026 else p5["revenue"]), rev[y - 1] if y > 2026 else p5["revenue"]) for y in bp.YEARS])
    rows.append(["Ricavi ricorrenti (canoni e licenze) sui ricavi totali", pcts(M.REVENUE[3] * 0.30, M.REVENUE[3])] + [pcts(bp.annual(bp.revenue()[bp.REV_LINES[0]], y), rev[y]) for y in bp.YEARS])
    ebitda25 = M.ratio_notes(2025)["ebitda"]
    rows.append(["Margine operativo lordo (EBITDA)", U(ebitda25)] + [U(bp.annual(pl["ebitda"], y)) for y in bp.YEARS])
    rows.append(["EBITDA sui ricavi", pcts(ebitda25, p5["revenue"])] + [pcts(bp.annual(pl["ebitda"], y), rev[y]) for y in bp.YEARS])
    rows.append(["Risultato operativo (EBIT)", U(p5["ebit"])] + [U(bp.annual(pl["ebit"], y)) for y in bp.YEARS])
    rows.append(["Utile netto", U(p5["net"])] + [U(bp.annual(pl["utile"], y)) for y in bp.YEARS])
    rows.append(["Persone in organico a fine anno", "16"] + [str(bp.staff()["heads"][[m for m in range(bp.N) if bp.MONTHS[m] == (y, 12)][0]]) for y in bp.YEARS])
    bs = bp.balance_sheet()
    rows.append(["Disponibilità liquide a fine anno", U(b5["cash"])] + [U(bp.year_end(bs["cash"], y)) for y in bp.YEARS])
    rows.append(["Posizione finanziaria netta (negativa = liquidità netta)", U(b5["loan"] - b5["cash"])] + [U(bp.year_end(bs["loan"], y) - bp.year_end(bs["cash"], y)) for y in bp.YEARS])
    rows.append(["Patrimonio netto", U(b5["pn"])] + [U(bp.year_end(bs["pn"], y)) for y in bp.YEARS])
    d.table(rows, [W - 124, 34, 30, 30, 30], font=8, zebra=True, bold_rows=[1, 4, 7])
    d.H2("Punti di forza della proposta")
    d.B(["<b>Ricavi ricorrenti in crescita.</b> Canoni e licenze valgono già il 30% dei ricavi e sono pianificati al 52% nel 2028: aumentano la prevedibilità dei flussi e il margine.",
         "<b>Prodotto proprietario e certificato.</b> La piattaforma Atlas è sviluppata internamente; l'azienda ha le certificazioni ISO 9001 e ISO/IEC 27001, richieste da clienti pubblici e finanziatori.",
         "<b>Situazione finanziaria solida.</b> Liquidità superiore al debito bancario, patrimonio netto in crescita, nessun covenant e nessuna garanzia reale sui beni sociali.",
         "<b>Crescita sostenibile.</b> L'organico cresce meno dei ricavi (+47% di persone contro +60% di ricavi sul triennio); il margine operativo resta intorno al 16-17%.",
         "<b>Rischio ripartito.</b> Il primo cliente pesa meno del 10% dei ricavi e i primi cinque circa il 31%; le linee di attività sono quattro, con stagionalità diverse."])
    d.H2("Uso delle risorse e richiesta")
    d.table([["Fonti e impieghi del triennio (euro)", "Importo"], ["Autofinanziamento (flusso operativo dopo imposte)", U(sum(bp.annual(bp.cash_flow()["operating"], y) for y in bp.YEARS))], ["Nuovo finanziamento chirografario (marzo 2026)", U(bp.NEW_LOAN)],
             ["Rimborso dei finanziamenti esistenti e nuovi (capitale)", U(-(sum(bp.debt()["old_pay"]) + sum(max(0, x) for x in bp.debt()["new_flow"])))], ["Investimenti in immobilizzazioni", U(-sum(bp.annual(bp.cash_flow()["investing"], y) for y in bp.YEARS))],
             ["Dividendi ai soci", U(-sum(bp.annual(bp.cash_flow()["dividends"], y) for y in bp.YEARS))], ["Variazione delle disponibilità liquide", U(bp.year_end(bs["cash"], 2028) - b5["cash"])]], [W - 40, 40], font=8, bold_rows=[6])


def company(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.title_block("2. L'AZIENDA")
    d.H1("2.1 Storia")
    d.P("Meridiana Digital Solutions S.r.l. è stata costituita il 14 marzo 2016 a Torino da Giulia Ferraris, ingegnere informatico con esperienza ventennale nella direzione di team di sviluppo, e da Marco Bertolotti, consulente di organizzazione aziendale. "
        "Nei primi due anni l'azienda ha realizzato siti e applicazioni su commessa per piccole imprese del Piemonte; dal 2018 ha affiancato allo sviluppo su commessa un'attività di analisi dei dati per i clienti e, dal 2019, ha avviato lo sviluppo del prodotto proprietario che oggi si chiama Atlas.")
    d.table([["Anno", "Evento"], ["2016", "Costituzione e avvio dell'attività in via San Quintino; primi tre clienti"], ["2018", "Prima assunzione stabile di un team di sviluppo (5 persone); primo contratto con un ente pubblico locale"],
             ["2019", "Trasferimento in via Garibaldi 28; avvio dello sviluppo del motore di stima dei costi (primo prototipo di Atlas)"], ["2020", "Finanziamento chirografario di 300.000 euro con garanzia del Fondo centrale; emergenza sanitaria gestita con il lavoro agile"],
             ["2021", "Aumento di capitale a 50.000 euro; apertura dell'unità locale di corso Francia per laboratorio dati e formazione"], ["2022", "Certificazione ISO 9001; organico a 9 persone; primo credito d'imposta ricerca e sviluppo"],
             ["2023", "Certificazione ISO/IEC 27001; lancio dei primi canoni di Atlas; organico a 11 persone"], ["2024", "Voucher della Camera di Commercio per la digitalizzazione; organico a 13 persone; ricavi oltre 1,3 milioni"],
             ["2025", "Ricavi di 1,58 milioni e utile di 190 mila euro; 12 studi professionali con licenza; organico medio a 15 persone"], ["2026", "Nuovo finanziamento e piano di crescita; assunzione di apprendisti; avvio del progetto di candidatura Atlas a bandi per la ricerca"]],
            [16, W - 16], align_right_from=9, font=8, zebra=True)
    d.H1("2.2 Compagine sociale e governo")
    d.table([["Socio", "Quota", "Valore nominale (euro)", "Ruolo"], ["Giulia Ferraris", "60%", "30.000", "Amministratore unico e direttore tecnico"], ["Marco Bertolotti", "40%", "20.000", "Socio lavoratore, sviluppo commerciale e rapporti con gli enti"]], [40, 18, 40, W - 98], align_right_from=9)
    d.P("La società è amministrata da un amministratore unico. Non è obbligata alla nomina di un organo di controllo (art. 2477 c.c.); ha tuttavia adottato prassi di governo volontarie: un comitato di direzione mensile con i responsabili di area, un budget annuale approvato dai soci, la revisione trimestrale degli scostamenti "
        "e il monitoraggio degli indicatori del presente piano. Le decisioni sulle operazioni straordinarie sono assunte dall'assemblea dei soci.")
    d.H1("2.3 Sedi e infrastrutture")
    d.table([["Sede", "Superficie", "Utilizzo", "Contratto"], ["Via Giuseppe Garibaldi 28, Torino", "420 mq", "Direzione, sviluppo, commerciale, amministrazione", "Locazione 6+6, scadenza 31/12/2028"],
             ["Corso Francia 114, Torino", "180 mq", "Laboratorio dati, formazione, sala server di test", "Locazione 6+6, scadenza 31/08/2027"]], [58, 22, W - 130, 50], align_right_from=9, font=8)
    d.P("L'infrastruttura di produzione della piattaforma Atlas è ospitata presso fornitori cloud europei, con ridondanza tra due regioni e backup cifrati giornalieri; i server fisici dell'azienda sono usati solo per test e sviluppo.")
    d.H1("2.4 Struttura organizzativa")
    st = bp.staff()
    areas: Dict[str, List[str]] = {}
    for pr in st["people"]:
        areas.setdefault(pr["area"], []).append(pr["role"])
    rows = [["Area", "Funzioni presenti (organico a settembre 2026)", "Persone"]]
    for area, roles in sorted(areas.items()):
        present = [r for r, pr in zip(roles, [x for x in st["people"] if x["area"] == area]) if pr["start"] <= 8]
        rows.append([area, "; ".join(sorted(set(present))), str(len(present))])
    rows.append(["Totale", "", str(sum(int(r[2]) for r in rows[1:]))])
    d.table(rows, [38, W - 56, 18], bold_rows=[len(rows) - 1], align_right_from=2, font=8)
    d.P("L'organizzazione è per area funzionale con responsabili di prodotto. Lo sviluppo è organizzato in due squadre (piattaforma e commesse), con un responsabile e riunioni di pianificazione quindicinali; il commerciale e il servizio clienti rispondono a un unico responsabile. "
        "Le funzioni amministrative, di controllo di gestione e di gestione del personale sono centralizzate.")
    d.H1("2.5 Certificazioni e conformità")
    d.table([["Certificazione o requisito", "Stato", "Scadenza"], ["UNI EN ISO 9001:2015 (sistema di gestione per la qualità)", "Certificata", "31/05/2027"], ["ISO/IEC 27001:2022 (sicurezza delle informazioni)", "Certificata", "31/05/2027"],
             ["Regolamento (UE) 2016/679 (GDPR)", "Conforme: registro dei trattamenti, DPO esterno", "-"], ["D.Lgs. 81/2008 (salute e sicurezza sul lavoro)", "Conforme: DVR aggiornato, medico competente", "Revisione annuale"], ["DURC", "Regolare", "29/12/2026"],
             ["Rating di legalità", "Non richiesto", "-"], ["Modello organizzativo D.Lgs. 231/2001", "Non adottato (valutazione prevista nel 2027)", "-"]], [W - 90, 56, 34], align_right_from=9, font=8, zebra=True)


def products(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.title_block("3. PRODOTTI E SERVIZI")
    d.H1("3.1 La piattaforma Atlas")
    d.P("Atlas è una piattaforma web per le piccole e medie imprese e per i loro consulenti: legge i bilanci e i documenti contabili dell'impresa, stima i costi dell'anno successivo per categoria di spesa e li confronta con le regole dei bandi e delle agevolazioni, "
        "restituendo per ciascuna misura l'importo teorico recuperabile, le voci da adeguare e le cautele da osservare. Il calcolo è deterministico: a parità di dati produce sempre lo stesso risultato e ogni cifra è ricondotta alla regola e al documento da cui deriva.")
    d.table([["Modulo", "Funzione", "Stato", "Utenti principali"], ["Acquisizione documenti", "Lettura di bilanci, F24, buste paga, visure; indicazione dell'affidabilità di ogni dato", "In produzione", "Imprese e studi"],
             ["Profilo dell'azienda", "Dati e bilanci in un posto solo, con la fonte di ogni valore", "In produzione", "Imprese e studi"], ["Previsione di bilancio", "Stima dei costi dell'anno successivo, con la spiegazione di ogni percentuale", "In produzione", "Imprese e studi"],
             ["Biblioteca dei bandi", "Regole di 40 bandi codificate e versionate, con il testo da cui derivano", "In produzione", "Studi"], ["Allocazione ottimale", "Quale bando paga quale spesa: ripartizione che rispetta tetti, cumulo e de minimis", "In produzione", "Studi"],
             ["Dossier e registro firmato", "Documento per il cliente e registro delle esecuzioni a prova di manomissione", "In produzione", "Studi e revisori"], ["Assistente di inserimento", "Guida l'utente nei dati mancanti spiegandoli in parole semplici", "Sperimentazione", "Imprese"],
             ["Connettori ai gestionali", "Importazione automatica da software contabili", "Roadmap 2027", "Imprese"]], [38, W - 100, 30, 32], align_right_from=9, font=7.8, zebra=True)
    d.H1("3.2 Piani commerciali e prezzi")
    d.table([["Piano", "Destinatari", "Prezzo annuo (euro)", "Contenuto"], ["Base", "Piccole imprese con un solo bilancio da monitorare", "1.200", "Profilo, previsione di bilancio, elenco bandi adatti"],
             ["Professional", "Imprese con più esercizi e consulente esterno", "2.400", "Tutto il piano Base più allocazione ottimale, de minimis e dossier"], ["Studio", "Studi professionali e boutique di finanza agevolata", "9.600", "Clienti illimitati, registro firmato, assistente, supporto dedicato"],
             ["Servizi professionali", "Tutti", "a progetto", "Configurazione, formazione, integrazioni e assistenza"]], [24, 66, 30, W - 120], align_right_from=9, font=8)
    d.H1("3.3 Servizi di sviluppo, consulenza e formazione")
    d.P("<b>Sviluppo su commessa.</b> Applicativi web e mobile, integrazioni con sistemi gestionali e personalizzazioni per imprese e enti pubblici locali, con metodologia agile e contratti a corpo o a tempo e materiali. Le commesse alimentano il prodotto: i componenti sviluppati più volte diventano moduli di Atlas.")
    d.P("<b>Consulenza informatica e analisi dei dati.</b> Analisi dei requisiti, cruscotti di business intelligence, valutazioni di sicurezza informatica e protezione dei dati. È la linea con il margine più alto per giornata ed è la porta d'ingresso per i clienti di Atlas.")
    d.P("<b>Formazione e assistenza tecnica.</b> Corsi per i clienti, help desk e interventi presso la sede del cliente; sono la linea più stabile e quella con il maggiore tasso di rinnovo.")
    d.H1("3.4 Roadmap di prodotto")
    d.table([["Trimestre", "Rilascio", "Obiettivo misurabile"], ["T4 2026", "Assistente di inserimento dati in produzione", "70% degli utenti nuovi completa il profilo senza supporto"], ["T1 2027", "Versione 2.0 della lettura dei documenti", "Riconoscimento automatico di almeno il 95% delle voci di costo"],
             ["T2 2027", "Connettori ai principali gestionali contabili", "5 connettori rilasciati; 60 imprese collegate"], ["T4 2027", "Confronto tra scenari e budget per bando", "Licenze a 34 studi professionali"], ["T2 2028", "Estensione ai bandi europei e a nuove regioni", "100 bandi codificati; 390 imprese clienti"],
             ["T4 2028", "Modulo di rendicontazione delle spese agevolate", "48 studi con licenza; churn inferiore al 7%"]], [24, 70, W - 94], align_right_from=9, font=8, zebra=True)


def market(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.title_block("4. IL MERCATO")
    d.H1("4.1 Dimensione e segmenti")
    d.P("Il mercato di riferimento è quello dei software e dei servizi per la pianificazione finanziaria e per l'accesso agli incentivi delle piccole e medie imprese italiane. Le imprese tra 10 e 249 addetti sono circa 220.000; "
        "nel segmento di interesse (imprese che investono in digitale e innovazione e che si avvalgono di un'amministrazione strutturata o di un consulente) si stima un bacino di 60.000 imprese. A queste si aggiungono circa 7.000 studi professionali e società di consulenza che seguono la finanza agevolata.")
    seg = [("Imprese manifatturiere", 26000, 1900), ("Imprese di servizi", 24000, 1700), ("Imprese commerciali", 10000, 1500)]
    d.table([["Segmento", "Imprese nel bacino", "Prezzo medio (euro)", "Valore teorico annuo (euro)"]] + [[a, U(b_), U(c), U(b_ * c)] for a, b_, c in seg] + [["Studi professionali e consulenti", U(7000), U(STUDIO_PRICE), U(7000 * STUDIO_PRICE)],
             ["Totale mercato indirizzabile (TAM)", U(60000 + 7000), "", U(sum(b_ * c for _, b_, c in seg) + 7000 * STUDIO_PRICE)]], [60, 36, 36, W - 132], bold_rows=[4], align_right_from=1, font=8)
    tam = sum(b_ * c for _, b_, c in seg) + 7000 * STUDIO_PRICE
    sam = round(tam * 0.38)
    d.table([["Livello", "Definizione", "Valore (euro)"], ["TAM", "Tutte le imprese e gli studi del bacino, a prezzo di listino", U(tam)], ["SAM", "Piemonte, Lombardia, Liguria, Emilia-Romagna e Veneto (38% del bacino)", U(sam)],
             ["SOM 2028", "Quota ottenibile a tre anni con la capacità commerciale pianificata", U(bp.annual(bp.revenue()[bp.REV_LINES[0]], 2028))], ["Quota sul SAM", "Ricavi ricorrenti 2028 / SAM", pcts(bp.annual(bp.revenue()[bp.REV_LINES[0]], 2028), sam)]],
            [26, W - 76, 50], align_right_from=2, font=8)
    d.H1("4.2 Tendenze")
    d.B(["<b>Digitalizzazione delle PMI:</b> la spesa in software gestionali e in analisi dei dati cresce a doppia cifra nelle imprese sotto i 50 addetti, sostenuta da agevolazioni come il credito d'imposta per i beni strumentali e i voucher camerali.",
         "<b>Complessità degli incentivi:</b> il numero di bandi attivi e la frequenza con cui cambiano le regole rendono la ricerca manuale costosa; gli studi cercano strumenti che riducano le ore di analisi.",
         "<b>Attenzione alla sicurezza e alla tracciabilità:</b> enti e finanziatori chiedono evidenze verificabili; le certificazioni e i registri a prova di manomissione diventano un criterio di scelta.",
         "<b>Consolidamento degli studi professionali:</b> gli studi più strutturati acquistano piattaforme per seguire più clienti senza aumentare l'organico."])
    d.H1("4.3 Clienti attuali")
    cust = LG.customer_revenue(2025)
    tot = sum(v for _, v in cust)
    kinds: Dict[str, int] = {}
    for c, v in cust:
        kinds[c["kind"]] = kinds.get(c["kind"], 0) + v
    names = {"PMI": "Imprese (PMI)", "PA": "Enti pubblici e del terzo settore", "Studio": "Studi professionali e associazioni", "Estero": "Clienti esteri"}
    d.table([["Tipologia di cliente (ricavi 2025)", "Ricavi (euro)", "Quota", "Clienti attivi"]] + [[names[k], U(round(v / 100)), pcts(v, tot), str(sum(1 for c, _ in cust if c["kind"] == k))] for k, v in sorted(kinds.items(), key=lambda t: -t[1])] +
            [["Totale", U(round(tot / 100)), "100,0%", str(len(cust))]], [W - 100, 36, 30, 34], bold_rows=[len(kinds) + 1], align_right_from=1, font=8)
    d.P(f"Il cliente più grande pesa il {pcts(cust[0][1], tot)} dei ricavi 2025 e i primi cinque il {pcts(sum(v for _, v in cust[:5]), tot)}. Il tasso di rinnovo annuale dei canoni è dell'91% (churn del 9%); i clienti che hanno provato la piattaforma gratuitamente per trenta giorni si convertono in abbonamento nel 22% dei casi.")


def competition(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.title_block("5. CONCORRENZA E ANALISI SWOT")
    d.table([["Categoria di concorrente", "Esempi (generici)", "Punti di forza", "Punti deboli", "Posizionamento di Meridiana"],
             ["Portali di aggregazione dei bandi", "Siti e newsletter di segnalazione", "Ampia copertura, notorietà", "Nessun calcolo sul bilancio dell'impresa", "Quantifica l'effetto sul bilancio e sulle spese"],
             ["Software di pianificazione finanziaria", "Strumenti di budgeting e controllo di gestione", "Funzioni di budget complete", "Ignorano le regole dei bandi", "Collega bilancio e regole in un solo calcolo"],
             ["Consulenti di finanza agevolata", "Boutique e studi specializzati", "Conoscenza dei bandi, relazione", "Costo elevato, tempi lunghi, poco scalabili", "Diventano clienti: strumento a canone per lo studio"],
             ["Software house generaliste", "Società di sviluppo su commessa", "Capacità di sviluppo", "Nessuna conoscenza dei bandi", "Prodotto verticale già pronto"],
             ["Grandi piattaforme gestionali", "Suite ERP e contabili", "Base clienti ampia", "Moduli di incentivi superficiali", "Connettori: complementari, non sostitutivi"]], [34, 34, 34, 36, W - 138], align_right_from=9, font=7.4, zebra=True)
    d.H1("Analisi SWOT")
    d.table([["Punti di forza", "Punti di debolezza"], ["Team tecnico stabile; certificazioni ISO 9001 e 27001; prodotto proprietario con calcolo trasparente; ricavi ricorrenti in crescita; assenza di debiti rilevanti",
                                                       "Dimensione ridotta; dipendenza da pochi sviluppatori chiave; ridotta forza commerciale; copertura commerciale concentrata nel Nord Ovest"],
             ["Opportunità", "Minacce"], ["Incentivi alla transizione digitale; domanda di strumenti trasparenti da parte degli studi; accordi con associazioni di categoria; estensione ai bandi europei",
                                          "Ingresso di grandi operatori; variabilità delle regole dei bandi; concorrenza sul prezzo; ritardi di pagamento della pubblica amministrazione"]], [W / 2, W / 2], align_right_from=9, font=8)
    d.H1("Fattori critici di successo e risposta")
    d.table([["Fattore critico", "Come lo presidia Meridiana"], ["Accuratezza del calcolo", "Motore deterministico, test automatici su 40 bandi, confronto tra stime e spese effettive su imprese pilota"],
             ["Aggiornamento delle regole", "Archivio versionato; un'analista dedicata; aggiornamento entro cinque giorni da ogni nuova pubblicazione"], ["Fiducia degli studi", "Fonti dichiarate, dossier verificabile, registro firmato, certificazione ISO 27001"],
             ["Costo di acquisizione dei clienti", "Canale indiretto tramite studi e associazioni, prova gratuita, contenuti formativi"]], [50, W - 50], align_right_from=9, font=8, zebra=True)


def go_to_market(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.title_block("6. STRATEGIA COMMERCIALE E DI MARKETING")
    d.H1("6.1 Canali")
    d.P("La vendita avviene su due canali. Il <b>canale diretto</b> (due commerciali e un customer success manager dal 2027) segue imprese di dimensione medio-grande e enti pubblici; il <b>canale indiretto</b> si basa su studi professionali e associazioni di categoria che adottano la piattaforma per i propri clienti "
        "e riconoscono una commissione di segnalazione del 10% sul primo anno. Le attività di marketing sono webinar formativi, contenuti sul sito, partecipazione a fiere di settore e campagne online mirate.")
    d.H1("6.2 Imbuto commerciale")
    rows = [["Fase", "2025", "2026", "2027", "2028"]]
    lead = {2025: 1900, 2026: 3100, 2027: 3600, 2028: 4100}
    conv = [1.0, 0.31, 0.22, 0.19]
    names = ["Visitatori unici del sito (migliaia)", "Contatti qualificati (lead)", "Prove gratuite avviate", "Nuovi clienti con canone (lordi)"]
    vals = {y: [lead[y] / 1000, round(lead[y] * 0.31 / 10) * 1.0, round(lead[y] * 0.31 * 0.22), round(lead[y] * 0.31 * 0.22 * 0.19 * 1.9)] for y in lead}
    rows = [["Fase"] + [str(y) for y in (2025, 2026, 2027, 2028)]]
    for k, nm in enumerate(names):
        rows.append([nm] + [(f"{vals[y][k]:.1f}".replace(".", ",") if k == 0 else U(round(vals[y][k]))) for y in (2025, 2026, 2027, 2028)])
    d.table(rows, [W - 120, 30, 30, 30, 30], align_right_from=1, font=8, zebra=True)
    d.H1("6.3 Clienti, ricavi unitari e costi di acquisizione")
    pl = bp.pl()
    rows = [["Indicatore", "2026", "2027", "2028"]]
    k_end = KPI["companies_end"]
    new_c = {y: k_end[y] - k_end[y - 1] + round(k_end[y - 1] * KPI["churn"][y]) for y in bp.YEARS}
    sales_cost = {y: round(bp.REV_TARGET[y] * bp.EXT_PCT["Marketing e vendite"][bp.YEARS.index(y)]) + 118000 + (45000 if y >= 2027 else 0) for y in bp.YEARS}
    cac = {y: round(sales_cost[y] / (new_c[y] + (KPI["studios_end"][y] - KPI["studios_end"][y - 1]))) for y in bp.YEARS}
    ltv = {y: round(KPI["arpa"][y] * 0.78 / KPI["churn"][y]) for y in bp.YEARS}
    rows += [["Imprese clienti a fine anno"] + [str(k_end[y]) for y in bp.YEARS], ["Studi con licenza a fine anno"] + [str(KPI["studios_end"][y]) for y in bp.YEARS], ["Nuove imprese clienti (al lordo degli abbandoni)"] + [str(new_c[y]) for y in bp.YEARS],
             ["Ricavo annuo medio per impresa cliente (euro)"] + [U(KPI["arpa"][y]) for y in bp.YEARS], ["Abbandono annuo (churn)"] + [pcts(KPI["churn"][y], 1, 0) for y in bp.YEARS],
             ["Costo commerciale e di marketing (euro)"] + [U(sales_cost[y]) for y in bp.YEARS], ["Costo di acquisizione per cliente - CAC (euro)"] + [U(cac[y]) for y in bp.YEARS],
             ["Valore del cliente nel tempo - LTV (margine lordo 78%) (euro)"] + [U(ltv[y]) for y in bp.YEARS], ["Rapporto LTV / CAC"] + [f"{ltv[y] / cac[y]:.1f}".replace(".", ",") for y in bp.YEARS],
             ["Recupero del CAC (mesi)"] + [f"{cac[y] / (KPI['arpa'][y] * 0.78 / 12):.1f}".replace(".", ",") for y in bp.YEARS]]
    d.table(rows, [W - 90, 30, 30, 30], align_right_from=1, font=8, zebra=True)
    d.H1("6.4 Composizione dei ricavi ricorrenti")
    rows = [["Ricavi ricorrenti (euro)", "2025 (stima)", "2026", "2027", "2028"]]
    rc = {y: recurring(y) for y in bp.YEARS}
    rows.append(["Canoni delle imprese clienti", U(round(M.REVENUE[3] * 0.30 * 0.62))] + [U(rc[y]["companies"]) for y in bp.YEARS])
    rows.append(["Licenze agli studi professionali", U(round(M.REVENUE[3] * 0.30 * 0.24))] + [U(rc[y]["studios"]) for y in bp.YEARS])
    rows.append(["Hosting e manutenzione applicativa ricorrente", U(round(M.REVENUE[3] * 0.30 * 0.14))] + [U(rc[y]["hosting"]) for y in bp.YEARS])
    rows.append(["Totale ricavi ricorrenti", U(round(M.REVENUE[3] * 0.30))] + [U(rc[y]["total"]) for y in bp.YEARS])
    d.table(rows, [W - 144, 34, 30, 30, 30], bold_rows=[4], align_right_from=1, font=8)
    d.H1("6.5 Budget di marketing e vendite")
    mk = bp.external_costs()["Marketing e vendite"]
    rows = [["Voce (euro)", "2026", "2027", "2028"]]
    parts = (0.34, 0.18, 0.14, 0.20, 0.14)
    labels = ["Pubblicità online: motori di ricerca e social", "Webinar ed eventi", "Materiale promozionale", "Sito web e contenuti", "Fiere di settore"]
    for lbl, w_ in zip(labels, parts):
        rows.append([lbl] + [U(round(bp.annual(mk, y) * w_)) for y in bp.YEARS])
    rows.append(["Totale marketing e vendite"] + [U(bp.annual(mk, y)) for y in bp.YEARS])
    d.table(rows, [W - 90, 30, 30, 30], bold_rows=[6], align_right_from=1, font=8)
    d.P("Le commissioni ai segnalatori sono comprese nel costo commerciale ma non nel budget di marketing. La prova gratuita di trenta giorni riduce l'attrito di acquisto; il customer success manager seguirà i clienti nei primi 90 giorni per ridurre l'abbandono.")


def operations(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.title_block("7. OPERAZIONI, TECNOLOGIA E QUALITA'")
    d.H1("7.1 Architettura e sicurezza")
    d.P("La piattaforma è composta da un'applicazione web, da servizi di calcolo e lettura dei documenti e da una base dati relazionale. I dati dei clienti sono separati logicamente per studio e per cliente; l'accesso avviene con credenziali individuali; i documenti sono cifrati a riposo. "
        "Il sistema registra ogni esecuzione di calcolo in un registro firmato che permette di dimostrare a posteriori che un risultato non è stato modificato. I processi di sviluppo seguono le prassi della norma ISO/IEC 27001: revisione del codice, test automatici, ambienti separati, gestione delle vulnerabilità.")
    d.table([["Area", "Misura", "Indicatore", "Obiettivo"], ["Disponibilità", "Due regioni cloud, bilanciamento e ripristino automatico", "Disponibilità mensile del servizio", "99,5%"], ["Sicurezza", "Test di penetrazione semestrali, scansione delle dipendenze", "Vulnerabilità critiche aperte", "0"],
             ["Qualità del codice", "Revisione tra pari, copertura dei test", "Copertura dei test automatici", ">= 85%"], ["Continuità", "Backup cifrati giornalieri, prova di ripristino trimestrale", "Tempo di ripristino", "<= 4 ore"],
             ["Assistenza", "Help desk con ticket e priorità", "Tempo di prima risposta", "<= 4 ore lavorative"]], [34, W - 108, 40, 34], align_right_from=9, font=7.8, zebra=True)
    d.H1("7.2 Fornitori principali")
    sup = [s for s in LG.suppliers() if s["category"] in ("Servizi cloud e licenze", "Consulenze informatiche", "Locazioni")][:9]
    d.table([["Fornitore", "Categoria", "Natura della fornitura"], *[[s["name"], s["category"], "Servizio continuativo" if s["category"] != "Consulenze informatiche" else "Prestazioni a richiesta"] for s in sup]], [70, 54, W - 124], align_right_from=9, font=8)
    d.P("Nessun fornitore pesa più del 12% dei costi esterni; per i servizi cloud sono stati identificati fornitori alternativi e testate le procedure di migrazione. I contratti con i fornitori critici prevedono livelli di servizio e clausole di uscita.")
    d.H1("7.3 Capacità produttiva")
    st = bp.staff()
    rev = bp.revenue()
    rows = [["Capacità di sviluppo", "2026", "2027", "2028"]]
    dev = {y: sum(1 for pr in st["people"] if pr["area"] == "Sviluppo e dati" and pr["start"] <= [m for m in range(bp.N) if bp.MONTHS[m] == (y, 6)][0]) for y in bp.YEARS}
    days = 17 * 12
    rows.append(["Persone nell'area sviluppo e dati a metà anno"] + [str(dev[y]) for y in bp.YEARS])
    rows.append(["Giornate-persona disponibili (17 giorni fatturabili al mese)"] + [U(dev[y] * days) for y in bp.YEARS])
    rows.append(["Ricavi da sviluppo su commessa e consulenza (euro)"] + [U(bp.annual(rev[bp.REV_LINES[1]], y) + bp.annual(rev[bp.REV_LINES[2]], y)) for y in bp.YEARS])
    rows.append(["Ricavo per giornata disponibile (euro)"] + [U(round((bp.annual(rev[bp.REV_LINES[1]], y) + bp.annual(rev[bp.REV_LINES[2]], y)) / (dev[y] * days))) for y in bp.YEARS])
    d.table(rows, [W - 90, 30, 30, 30], align_right_from=1, font=8)
    d.P("La capacità è dimensionata sul tasso di occupazione degli sviluppatori: una parte crescente del tempo è destinata al prodotto Atlas (capitalizzato e a ricerca e sviluppo) e quindi non genera ricavi su commessa; il piano tiene conto di questa riallocazione.")


def people(d: Doc) -> None:
    W = _w(d)
    st = bp.staff()
    d.page_break()
    d.title_block("8. PERSONE E ORGANIZZAZIONE")
    d.H1("8.1 Organico e piano delle assunzioni")
    rows = [["Matricola", "Ruolo", "Area", "Ingresso", "Livello", "Costo azienda annuo 2026 (euro)"]]
    for pr in st["people"]:
        yy, mm = (2026 + pr["start"] // 12, pr["start"] % 12 + 1) if pr["new"] or pr["start"] > 0 else (None, None)
        from datetime import date
        hired = {e["id"]: e["hired"] for e in P.EMPLOYEES}.get(pr["id"])
        entry = f"{hired[8:10]}/{hired[5:7]}/{hired[:4]}" if hired else f"{mm:02d}/{yy}"
        rows.append([pr["id"], pr["role"], pr["area"], entry, pr["level"], U(round(pr["cost"] * (1 + bp.WAGE_RISE)))])
    d.table(rows, [18, 56, 42, 22, 14, W - 152], font=7.4, zebra=True, align_right_from=5)
    d.small("Le persone da M018 in poi sono assunzioni previste dal piano; i costi sono quelli di un'assunzione a tempo indeterminato al livello indicato, comprensivi di oneri e TFR.")
    d.H1("8.2 Organico per area a fine anno")
    rows = [["Area", "2025", "2026", "2027", "2028"]]
    areas = sorted({pr["area"] for pr in st["people"]})

    def count(area: str, y: int) -> int:
        if y == 2025:
            return sum(1 for pr in st["people"] if pr["area"] == area and not pr["new"] and pr["id"] <= "M016")
        dec = [m for m in range(bp.N) if bp.MONTHS[m] == (y, 12)][0]
        return sum(1 for pr in st["people"] if pr["area"] == area and pr["start"] <= dec)
    for a in areas:
        rows.append([a] + [str(count(a, y)) for y in (2025, 2026, 2027, 2028)])
    rows.append(["Totale"] + [str(sum(int(r[k]) for r in rows[1:])) for k in range(1, 5)])
    d.table(rows, [W - 120, 30, 30, 30, 30], bold_rows=[len(rows) - 1], align_right_from=1, font=8)
    d.H1("8.3 Costo del personale")
    pl = bp.personnel_lines()
    rows = [["Voce (euro)", "2026", "2027", "2028"]]
    for k in pl:
        rows.append([k] + [U(bp.annual(pl[k], y)) for y in bp.YEARS])
    rows.append(["Totale costo del personale"] + [U(bp.annual(bp.personnel_total(), y)) for y in bp.YEARS])
    rows.append(["Incidenza sui ricavi"] + [pcts(bp.annual(bp.personnel_total(), y), bp.REV_TARGET[y]) for y in bp.YEARS])
    rows.append(["Costo medio per dipendente (euro)"] + [U(round(bp.annual(bp.personnel_total(), y) / (sum(st["heads"][m] for m in range(bp.N) if bp.MONTHS[m][0] == y) / 12))) for y in bp.YEARS])
    d.table(rows, [W - 90, 30, 30, 30], bold_rows=[5], align_right_from=1, font=8)
    d.H1("8.4 Politiche per le persone")
    d.B(["<b>Retribuzione:</b> CCNL Commercio, Terziario Distribuzione e Servizi, con superminimi individuali e premio di risultato legato a ricavi e qualità; revisione annuale a gennaio (+2,5% nel piano).",
         "<b>Formazione:</b> budget di 21 ore pro capite l'anno, certificazioni tecniche e di sicurezza; percorsi per gli apprendisti con tutor dedicato.", "<b>Welfare:</b> buoni pasto, assistenza sanitaria integrativa, flessibilità oraria e lavoro agile fino a due giorni la settimana.",
         "<b>Selezione:</b> collaborazione con università e ITS del territorio; contratti di apprendistato professionalizzante per i profili junior.", "<b>Dipendenza da persone chiave:</b> documentazione del codice, affiancamento dei profili senior, piano di successione per la direzione tecnica."])


def investments(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.title_block("9. INVESTIMENTI, RICERCA E SVILUPPO")
    d.H1("9.1 Piano degli investimenti")
    cx = bp.capex()
    rows = [["Investimento (euro)", "2026", "2027", "2028", "Totale"]]
    for k in cx:
        rows.append([k] + [U(bp.annual(cx[k], y)) for y in bp.YEARS] + [U(sum(cx[k]))])
    rows.append(["Totale investimenti in immobilizzazioni"] + [U(sum(bp.annual(cx[k], y) for k in cx)) for y in bp.YEARS] + [U(sum(sum(cx[k]) for k in cx))])
    d.table(rows, [W - 120, 30, 30, 30, 30], bold_rows=[len(rows) - 1], align_right_from=1, font=8)
    d.H1("9.2 Ricerca e sviluppo del progetto Atlas")
    rows = [["Progetto Atlas (euro)", "2026", "2027", "2028", "Totale"]]
    rd = bp.RD_INVEST
    rows.append(["Investimento complessivo in ricerca e sviluppo"] + [U(rd[y]) for y in bp.YEARS] + [U(sum(rd.values()))])
    rows.append(["di cui capitalizzato tra le immobilizzazioni (35%)"] + [U(round(rd[y] * bp.CAPITALIZED_SHARE)) for y in bp.YEARS] + [U(sum(round(rd[y] * bp.CAPITALIZED_SHARE) for y in bp.YEARS))])
    rows.append(["di cui a conto economico (ricerca e sviluppo non capitalizzabile)"] + [U(rd[y] - round(rd[y] * bp.CAPITALIZED_SHARE)) for y in bp.YEARS] + [U(sum(rd.values()) - sum(round(rd[y] * bp.CAPITALIZED_SHARE) for y in bp.YEARS))])
    rows.append(["Credito d'imposta ricerca e sviluppo maturato (10% dei costi ammissibili)"] + [U(bp.CREDIT_RS[y]) for y in bp.YEARS] + [U(sum(bp.CREDIT_RS.values()))])
    d.table(rows, [W - 120, 30, 30, 30, 30], align_right_from=1, font=8, zebra=True)
    d.P("Dalla versione commerciale di Atlas i costi di sviluppo che soddisfano i criteri dell'OIC 24 (fattibilità tecnica, intenzione di completamento, capacità di generare benefici economici futuri, misurabilità dei costi) sono capitalizzati e ammortizzati in cinque anni; "
        "i costi di ricerca e quelli di sviluppo che non rispettano tali criteri sono imputati a conto economico e concorrono alla base del credito d'imposta.")
    d.H1("9.3 Contributi pubblici richiesti")
    d.table([["Misura (esempi)", "Ente", "Importo richiesto (euro)", "Stato", "Trattamento nel piano"], ["Voucher per la digitalizzazione 2026", "Camera di Commercio di Torino", U(12000), "In istruttoria", "Non incluso (prudenza)"],
             ["Bando regionale per progetti di ricerca e sviluppo", "Regione Piemonte", U(140000), "In preparazione", "Non incluso; scenario ottimistico"], ["Progetto Atlas - bando nazionale per l'innovazione", "Ministero (bando in corso di selezione)", U(143950), "Bozza di candidatura", "Non incluso; scenario ottimistico"]],
            [60, 40, 30, 28, W - 158], align_right_from=2, font=7.6, zebra=True)
    d.P("Il piano di base non assume alcun contributo a fondo perduto, ad eccezione del credito d'imposta per ricerca e sviluppo, già maturato negli anni precedenti con percentuali di legge. I contributi eventualmente concessi migliorerebbero il risultato e la liquidità (scenario ottimistico).")


def assumptions(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.title_block("10. IPOTESI ALLA BASE DEL PIANO")
    d.table([["Ipotesi", "2026", "2027", "2028", "Fondamento"], ["Crescita dei ricavi", "17,5%", "15,6%", "15,3%", "Portafoglio ordini, crescita dei canoni e capacità commerciale"],
             ["Quota di ricavi da canoni e licenze", "38%", "45%", "52%", "Passaggio da commesse a ricavi ricorrenti"], ["Adeguamento delle retribuzioni (gennaio)", "2,5%", "2,5%", "2,5%", "Rinnovi contrattuali e scatti"],
             ["Premi, welfare e altri costi sul costo di base", "13%", "13%", "13%", "Dato storico 2025"], ["Giorni medi di incasso (DSO)", str(bp.DSO[2026]), str(bp.DSO[2027]), str(bp.DSO[2028]), "Maggiore peso dei canoni con incasso anticipato"],
             ["Giorni medi di pagamento (DPO)", "47", "47", "47", "Dato storico"], ["Aliquota IRES", "24%", "24%", "24%", "Normativa vigente"], ["Aliquota IRAP (Piemonte)", "3,90%", "3,90%", "3,90%", "Normativa vigente"],
             ["Tasso del finanziamento esistente", "5,05%", "5,05%", "5,05%", "Euribor a tre mesi più 2,10 punti"], ["Tasso del nuovo finanziamento", "5,35%", "5,35%", "5,35%", "Euribor a tre mesi più 2,40 punti"],
             ["Dividendi ai soci", "90.000", "30% utile 2026", "30% utile 2027", "Politica di distribuzione prudente"], ["Aliquote di ammortamento", "Come bilancio", "Come bilancio", "Come bilancio", "Sviluppo software 20%, apparati 20%"]], [54, 20, 24, 24, W - 122], align_right_from=1, font=7.6, zebra=True)
    d.H1("Ipotesi sui costi esterni (percentuale dei ricavi)")
    rows = [["Voce", "2025 (storico)", "2026", "2027", "2028"]]
    hist = {"Consulenze e collaborazioni": 0.110, "Licenze e servizi cloud": 0.037, "Affitti, utenze e locazioni operative": 0.061, "Marketing e vendite": 0.039, "Altri costi di struttura": 0.046}
    for k, v in bp.EXT_PCT.items():
        rows.append([k, pcts(hist[k], 1)] + [pcts(x, 1) for x in v])
    rows.append(["Totale costi esterni", pcts(sum(hist.values()), 1)] + [pcts(sum(v[i] for v in bp.EXT_PCT.values()), 1) for i in range(3)])
    d.table(rows, [W - 120, 30, 30, 30, 30], bold_rows=[6], align_right_from=1, font=8)
    d.P("Le percentuali dei costi esterni si riducono gradualmente per effetto di economie di scala sugli affitti e sulle consulenze, a fronte di un aumento dei costi per licenze e servizi cloud, che crescono con il numero di clienti. "
        "Le imposte sul reddito sono calcolate con le regole fiscali vigenti: il credito d'imposta per ricerca e sviluppo non concorre alla base imponibile; i costi di autovetture e telefonia sono deducibili in misura parziale.")
    d.H1("Ipotesi sul capitale circolante e sulla tesoreria")
    d.B(["I ricavi da canoni sono fatturati in anticipo per il 60% dei clienti (annuali) e per il resto trimestralmente; i risconti passivi crescono con il peso dei canoni.", "I clienti pubblici pagano mediamente a 75 giorni; i clienti privati a 55 giorni; i clienti esteri a 40 giorni.",
         "I fornitori sono pagati a 47 giorni in media; le utenze e gli affitti con addebito diretto.", "Le imposte sul reddito sono versate a giugno (saldo e primo acconto) e a novembre (secondo acconto); il credito d'imposta per ricerca e sviluppo è usato in compensazione da luglio, in tre quote annuali.",
         "Non sono previsti aumenti di capitale, cessioni di cespiti o operazioni straordinarie."])
