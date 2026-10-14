"""Approfondimenti dei documenti PDF dell'azienda e documenti aggiuntivi: visura, domanda di contributo, DURC, de minimis, dichiarazioni fiscali, estratto conto, contratto di locazione, relazione tecnica."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import List

from . import ledger as LG
from . import model as M
from . import people as P
from .bil_nota import E
from .pdfkit import Doc, cents, pct, units

CO = M.COMPANY
U = units


def _w(d: Doc) -> float:
    return d.width / 2.8346


# ================================================================================================ visura: sezioni aggiuntive
def registry_more(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.H1("STORICO DELLE MODIFICHE DEL REGISTRO DELLE IMPRESE")
    ev = [("14/03/2016", "Atto costitutivo", "Società a responsabilità limitata, capitale 10.000,00 euro; amministratore unico Giulia Ferraris"), ("21/03/2016", "Iscrizione", "Iscrizione al Registro delle Imprese di Torino, inizio attività"),
          ("12/09/2016", "Variazione attività", "Aggiunta dell'attività secondaria 62.02.00 (consulenza informatica)"), ("18/05/2017", "Variazione oggetto sociale", "Ampliamento dell'oggetto sociale alle attività di formazione"),
          ("04/12/2018", "Nomina procuratore", "Procura speciale per contratti di sviluppo software a favore di un dipendente"), ("18/12/2019", "Trasferimento sede", "Dalla via San Quintino 12 alla via Giuseppe Garibaldi 28, Torino"),
          ("30/09/2020", "Finanziamento", "Iscrizione dell'operazione di finanziamento con garanzia del Fondo centrale (non iscritta ipoteca)"), ("29/04/2021", "Aumento di capitale", "Da 10.000,00 a 50.000,00 euro, con riserve di utili per 25.000,00 euro e conferimenti in denaro per 15.000,00 euro"),
          ("01/09/2021", "Apertura unità locale", "Corso Francia 114, Torino: laboratorio dati e formazione"), ("15/03/2023", "Procura", "Procura a Matteo Gallo per contratti fino a 150.000 euro"), ("20/11/2023", "Procura", "Procura a Paola Fontana per operazioni bancarie ordinarie fino a 25.000 euro"),
          ("29/04/2022", "Rinnovo nomina", "Conferma dell'amministratore unico a tempo indeterminato"), ("11/03/2024", "Variazione attività", "Aggiunta dell'attività 63.11.19 (elaborazione dei dati, hosting)"), ("22/07/2025", "Brevetti e marchi", "Deposito del marchio ATLAS per le classi 9, 35 e 42")]
    d.table([["Data", "Evento", "Descrizione"]] + [list(x) for x in ev], [24, 40, W - 64], align_right_from=9, font=8, zebra=True)
    d.H1("MARCHI, BREVETTI E DIRITTI DI PROPRIETA' INTELLETTUALE")
    d.table([["Titolo", "Numero di deposito", "Data", "Classi", "Stato"], ["Marchio denominativo ATLAS", "UIBM 302019000051234", "04/04/2019", "9, 35, 42", "Registrato, rinnovo 2029"], ["Marchio figurativo Meridiana", "UIBM 302020000087612", "06/06/2020", "9, 42", "Registrato, rinnovo 2030"],
             ["Marchio dell'Unione europea ATLAS", "EUIPO 018912345", "22/07/2025", "9, 35, 42", "In esame"], ["Brevetti", "-", "-", "-", "Nessuno"]], [52, 40, 22, 22, W - 136], align_right_from=9, font=8)
    d.H1("DATI ECONOMICI DEGLI ULTIMI ESERCIZI (SINTESI)")
    rows = [["Esercizio", "Ricavi", "Utile", "Patrimonio netto", "Totale attivo", "Organico medio", "Debiti verso banche"]]
    for y in (2025, 2024, 2023, 2022):
        b = M.balance(y)
        rows.append([str(y), U(M.pl(y)["revenue"]), U(M.pl(y)["net"]), U(b["pn"]), U(b["assets"]), str(M.EMPLOYEES[y]), U(b["loan"])])
    d.table(rows, [20, 26, 24, 28, 26, 26, W - 150], align_right_from=1, font=8, zebra=True)
    d.small("Dati tratti dai bilanci depositati. Per l'esercizio 2025 il bilancio è stato approvato il 28/04/2026.")
    d.H1("CODICI ATECO E ATTIVITA' ESERCITATE")
    d.table([["Codice", "Descrizione", "Tipo", "Dal"], ["62.01.00", "Produzione di software non connesso all'edizione", "Prevalente", "21/03/2016"], ["62.02.00", "Consulenza nel settore delle tecnologie dell'informatica", "Secondaria", "12/09/2016"],
             ["63.11.19", "Elaborazione dei dati, hosting e attività connesse", "Secondaria", "11/03/2024"], ["85.59.20", "Corsi di formazione e corsi di aggiornamento professionale", "Secondaria", "18/05/2017"]], [24, W - 88, 36, 28], align_right_from=9, font=8)
    d.H1("UNITA' LOCALI: DETTAGLIO")
    d.table([["Dato", "Sede legale e operativa", "Unità locale n. 1"], ["Indirizzo", "Via Giuseppe Garibaldi 28, 10122 Torino", "Corso Francia 114, 10143 Torino"], ["Data apertura", "21/03/2016", "01/09/2021"], ["Attività", "Uffici, sviluppo software, commerciale", "Laboratorio dati, formazione"],
             ["Persone presenti in sede", "14", "3"], ["Titolo di possesso", "Locazione (scadenza 31/12/2028)", "Locazione (scadenza 31/08/2027)"], ["Superficie", "420 mq", "180 mq"], ["Codice ATECO dell'unità", "62.01.00", "63.11.19 / 85.59.20"]], [40, 70, W - 110], align_right_from=9, font=8, zebra=True)
    d.H1("ALTRE INFORMAZIONI")
    d.table([["Informazione", "Valore"], ["Procedure concorsuali negli ultimi cinque anni", "Nessuna"], ["Protesti e pregiudizievoli", "Nessuno"], ["Ipoteche e gravami iscritti sul patrimonio sociale", "Nessuno"], ["Sede secondaria all'estero", "Nessuna"], ["Appartenenza a gruppo societario", "No"],
             ["Contratti di rete", "Nessuno"], ["Iscrizione ad albi professionali o camerali ulteriori", "Nessuna"], ["Atto di nomina del DPO", "Esterno, nominato il 25/05/2018 (non soggetto a iscrizione)"], ["Data ultimo aggiornamento della posizione", "02/10/2026"]], [80, W - 80], align_right_from=9, font=8, zebra=True)
    d.small("Documento di prova: tutti i dati sono fittizi.")


# ================================================================================================ DURC e de minimis
def durc_more(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.H1("VERSAMENTI CONTRIBUTIVI DEGLI ULTIMI DODICI MESI (INPS, DM10)")
    rows = [["Periodo", "Data di versamento", "Importo versato (euro)", "Dipendenti in forza", "Esito"]]
    base = round(M.acct("Oneri sociali", 2025) / 12 * 1.04)
    r = LG.rng("durc")
    for k in range(12):
        yy, mm = (2025, 8 + k) if 8 + k <= 12 else (2026, 8 + k - 12)
        pay = date(yy + (1 if mm == 12 else 0), (mm % 12) + 1, 16)
        rows.append([f"{mm:02d}/{yy}", pay.strftime("%d/%m/%Y"), cents(round(base * r.uniform(0.94, 1.1), 2)), str(15 + (k >= 5)), "Regolare"])
    d.table(rows, [28, 40, 40, 36, W - 144], align_right_from=2, font=8, zebra=True)
    d.H1("AUTOLIQUIDAZIONE INAIL")
    d.table([["Annualità", "Retribuzioni imponibili (euro)", "Premio dovuto (euro)", "Data di pagamento", "Esito"], ["2024/2025", cents(M.acct("Salari e stipendi", 2024) * 0.97), cents(round(M.acct("Salari e stipendi", 2024) * 0.0089, 2)), "16/02/2025", "Regolare"],
             ["2025/2026", cents(M.acct("Salari e stipendi", 2025) * 0.97), cents(round(M.acct("Salari e stipendi", 2025) * 0.0089, 2)), "16/02/2026", "Regolare"]], [28, 50, 42, 36, W - 156], align_right_from=1, font=8)
    d.H1("STORICO DEI DURC EMESSI")
    d.table([["Protocollo", "Data emissione", "Scadenza", "Finalità", "Esito"], ["INAIL_41203311", "03/05/2025", "31/08/2025", "Bando regionale", "Regolare"], ["INAIL_38820004", "17/12/2024", "16/04/2025", "Voucher camerale", "Regolare"], ["INAIL_35417702", "05/09/2024", "03/01/2025", "Verifica a richiesta", "Regolare"],
             ["INAIL_48217763", "01/09/2026", "29/12/2026", "Agevolazioni pubbliche", "Regolare"]], [34, 30, 28, W - 124, 32], align_right_from=9, font=8, zebra=True)


def deminimis_more(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.H1("ESTRATTO DEL REGISTRO NAZIONALE DEGLI AIUTI (VISURA AIUTI)")
    d.table([["Data concessione", "Ente", "Misura", "Regime", "Importo (euro)", "COR"], ["14/09/2023", "Fondimpresa", "Avviso formazione continua", "De minimis", cents(5200), "COR-0000003"], ["12/04/2024", "Camera di Commercio di Torino", "Voucher digitalizzazione PMI", "De minimis", cents(10000), "COR-0000001"],
             ["03/10/2025", "Regione Piemonte", "Contributo partecipazione fiere", "De minimis", cents(6500), "COR-0000002"]], [28, 42, 46, 24, 26, W - 166], align_right_from=4, font=8)
    d.H1("CALCOLO DEL MASSIMALE NEL TRIENNIO MOBILE ALLA DATA DI OGNI CONCESSIONE")
    d.table([["Data di concessione", "Aiuti nei tre anni precedenti (euro)", "Nuovo aiuto (euro)", "Totale nel triennio (euro)", "Margine residuo (euro)"], ["14/09/2023", cents(0), cents(5200), cents(5200), cents(294800)], ["12/04/2024", cents(5200), cents(10000), cents(15200), cents(284800)],
             ["03/10/2025", cents(15200), cents(6500), cents(21700), cents(278300)], ["02/10/2026 (data della dichiarazione, triennio 2024-2026)", cents(16500), cents(0), cents(16500), cents(283500)]], [62, 38, 28, 30, W - 158], align_right_from=1, font=8, zebra=True)
    d.small("Nel triennio 2024-2026 dell'attuale dichiarazione rientrano gli aiuti del 12/04/2024 e del 03/10/2025; l'aiuto del 14/09/2023 è uscito dalla finestra mobile.")
    d.H1("DICHIARAZIONI PRECEDENTI")
    d.table([["Data", "Destinatario", "Procedura", "Importo totale dichiarato (euro)"], ["15/02/2024", "Camera di Commercio di Torino", "Voucher digitalizzazione 2024", cents(5200)], ["14/05/2025", "Regione Piemonte", "Contributo partecipazione fiere", cents(15200)],
             ["10/03/2026", "Camera di Commercio di Torino", "Voucher digitalizzazione 2026", cents(21700)]], [26, 56, 56, W - 138], align_right_from=3, font=8)


# ================================================================================================ domanda di contributo: sezioni aggiuntive
def draft_more(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.title_block("PARTE SECONDA - DESCRIZIONE ESECUTIVA DEL PROGETTO")
    d.H1("24. ANALISI DEL FABBISOGNO E DEL CONTESTO")
    d.P("Le piccole e medie imprese italiane affrontano ogni anno la scelta di quali spese pianificare e quali agevolazioni pubbliche richiedere. L'analisi condotta presso quindici studi professionali e venti imprese ha evidenziato che la ricerca dei bandi e la verifica della loro coerenza con il bilancio assorbono in media tre ore per cliente a trimestre, "
        "con un margine di errore significativo: nel 24% delle pratiche esaminate l'importo atteso differiva di oltre il 10% da quello ammesso. Le cause principali sono la lettura incompleta delle regole (tetti per categoria, cumulo, de minimis) e l'uso di stime non riproducibili.")
    d.table([["Evidenza dell'indagine preliminare", "Valore"], ["Studi professionali intervistati", "15"], ["Imprese intervistate", "20"], ["Tempo medio per cliente per ricerca e verifica dei bandi", "3 ore a trimestre"], ["Pratiche con scostamento oltre il 10% tra stima e importo ammesso", "24%"],
             ["Studi interessati a uno strumento a canone", "11 su 15"], ["Disponibilità a partecipare alla sperimentazione", "9 studi e 12 imprese"]], [W - 50, 50], align_right_from=1, font=8, zebra=True)
    d.H1("25. OBIETTIVI REALIZZATIVI, ATTIVITA' E RISULTATI ATTESI")
    tasks = [("T1.1", "Raccolta dei requisiti presso studi e imprese pilota", "WP1", 1, 2), ("T1.2", "Modello dei dati delle regole dei bandi", "WP1", 2, 3), ("T1.3", "Scelta dei 40 bandi di riferimento e delle fonti ufficiali", "WP1", 2, 3), ("T1.4", "Progettazione dell'architettura e della sicurezza", "WP1", 2, 3),
             ("T2.1", "Modulo di acquisizione dei documenti contabili", "WP2", 4, 6), ("T2.2", "Archivio delle regole e versionamento", "WP2", 4, 7), ("T2.3", "Motore di calcolo deterministico e ripartizione ottimale", "WP2", 5, 8), ("T2.4", "Codifica manuale dei 40 bandi", "WP2", 4, 8),
             ("T2.5", "Interfaccia web e prospetti", "WP2", 6, 8), ("T3.1", "Selezione e formazione delle imprese pilota", "WP3", 9, 9), ("T3.2", "Sperimentazione su 15 imprese", "WP3", 9, 11), ("T3.3", "Misura dello scostamento tra stima e spese effettive", "WP3", 10, 11),
             ("T3.4", "Correzione delle regole e del motore", "WP3", 10, 11), ("T4.1", "Documentazione per gli utenti e manuale", "WP4", 11, 12), ("T4.2", "Formazione di due studi professionali", "WP4", 12, 12), ("T4.3", "Rilascio della versione commerciale e comunicazione dei risultati", "WP4", 12, 12)]
    d.table([["Attività", "Descrizione", "Pacchetto", "Dal mese", "Al mese"]] + [[a, b, c, str(e), str(f)] for a, b, c, e, f in tasks], [20, W - 90, 24, 22, 24], align_right_from=2, font=8, zebra=True)
    d.H1("26. DIAGRAMMA DI GANTT DETTAGLIATO")
    rows = [["Attività"] + [f"M{k}" for k in range(1, 13)]]
    for a, b, c, s, e in tasks:
        rows.append([f"{a} {b[:34]}"] + ["■" if s <= k <= e else "" for k in range(1, 13)])
    d.table(rows, [64] + [(W - 64) / 12] * 12, align_right_from=1, font=7.2, zebra=True)
    d.H1("27. DESCRIZIONE DEI PACCHETTI DI LAVORO")
    for wp, desc in (("WP1 - Analisi e progettazione", "Il pacchetto definisce i requisiti del sistema attraverso interviste e prove di compilazione con cinque imprese e due studi; progetta il modello dei dati delle regole (spese ammissibili, aliquote, tetti, cumulo, finestre temporali) e sceglie i 40 bandi di riferimento in base a diffusione e varietà di regole. "
                                                          "Il risultato è un documento dei requisiti approvato dagli utenti pilota e un modello dei dati verificato su dieci bandi."),
                     ("WP2 - Sviluppo del prototipo", "Il pacchetto realizza il modulo di acquisizione dei documenti, l'archivio delle regole con versionamento, il motore di calcolo e l'interfaccia. Le regole dei 40 bandi sono codificate manualmente da due analisti con doppia lettura e misura dell'accordo; il motore è verificato con test automatici sull'intero insieme di casi."),
                     ("WP3 - Sperimentazione con le imprese pilota", "Il prototipo è usato da quindici imprese per stimare i recuperi dell'anno; le stime sono confrontate con le spese effettivamente ammesse dai bandi, misurando lo scostamento per categoria. Le cause di scostamento sono analizzate e le regole corrette."),
                     ("WP4 - Rilascio e diffusione", "Il pacchetto produce il manuale utente, forma due studi professionali, rilascia la versione commerciale e comunica i risultati attraverso un convegno e un rapporto pubblico di sintesi.")):
        d.H2(wp)
        d.P(desc)
    d.H1("28. SPESE PER IL PERSONALE: PROSPETTO MENSILE")
    team = [("Responsabile di progetto (livello 1)", 40, 5700), ("Sviluppatore senior (livello 3) A", 55, 5230), ("Sviluppatore senior (livello 3) B", 55, 5230), ("Data scientist (livello 3)", 70, 5300), ("Sviluppatore (livello 4) A", 50, 4310), ("Sviluppatore (livello 4) B", 50, 4310),
            ("Project manager (livello 2)", 30, 5500), ("UX designer (livello 4)", 25, 4350)]
    rows = [["Persona", "Quota"] + [f"M{k}" for k in range(1, 13)] + ["Totale"]]
    tot = [0] * 12
    grand = 0
    for name, q, m_ in team:
        cells = []
        for k in range(1, 13):
            on = 1 if (k >= 4 or "Responsabile" in name or "Project" in name) and not ("UX" in name and k > 6) else 0
            if "Data scientist" in name and k < 4:
                on = 0
            v = round(m_ * q / 100 * on)
            cells.append(v)
        for k, v in enumerate(cells):
            tot[k] += v
        grand += sum(cells)
        rows.append([name, f"{q}%"] + [U(v) if v else "" for v in cells] + [U(sum(cells))])
    rows.append(["Totale mese", ""] + [U(v) for v in tot] + [U(grand)])
    d.table(rows, [50, 12] + [(W - 50 - 12 - 18) / 12] * 12 + [18], bold_rows=[len(rows) - 1], align_right_from=2, font=6.6, zebra=True)
    d.small("Il prospetto è indicativo: il costo imputato definitivo è quello del piano dei costi (168.000 euro), riallineato in sede di rendicontazione sulla base dei fogli di presenza.")
    d.H1("29. PREVENTIVI E CONFRONTO TRA OFFERTE")
    d.table([["Voce", "Fornitore A (euro)", "Fornitore B (euro)", "Fornitore C (euro)", "Scelto", "Motivazione"], ["Consulenza di data science", cents(38400), cents(36000), cents(41200), "B", "Miglior rapporto qualità/prezzo, referenze su progetti simili"],
             ["Licenze e servizi cloud per lo sviluppo (12 mesi)", cents(25800), cents(24000), cents(24900), "B", "Prezzo più basso, regione europea"], ["Attrezzature del laboratorio dati", cents(30100), cents(28500), cents(29200), "B", "Garanzia estesa a 36 mesi"],
             ["Formazione specialistica", cents(9800), cents(9000), cents(9400), "B", "Docenti certificati e sede vicina"]], [48, 26, 26, 26, 14, W - 140], align_right_from=1, font=7.6, zebra=True)
    d.H1("30. ATTREZZATURE E LICENZE DEL PROGETTO")
    rows = [["Bene", "Q.tà", "Costo unitario (euro)", "Totale (euro)", "Quota imputata al progetto", "Importo imputato (euro)"]]
    items = [("Workstation per elaborazione dati", 2, 4200, 0.6), ("Server di calcolo e storage dedicato", 1, 9800, 0.5), ("Dispositivi di test mobile", 6, 450, 1.0), ("Apparati di rete del laboratorio", 1, 3400, 0.5), ("Monitor 27 pollici", 4, 380, 1.0), ("Licenze di sviluppo e test (12 mesi)", 1, 24000, 1.0)]
    tot = 0
    for n, q, c, sh in items:
        rows.append([n, str(q), cents(c), cents(q * c), f"{int(sh * 100)}%", cents(round(q * c * sh))])
        tot += round(q * c * sh)
    rows.append(["Totale attrezzature e licenze", "", "", "", "", cents(tot)])
    d.table(rows, [W - 134, 12, 28, 28, 30, 36], bold_rows=[len(rows) - 1], align_right_from=1, font=7.8, zebra=True)
    d.H1("31. CRONOPROGRAMMA DELLA SPESA PER TRIMESTRE E PER VOCE")
    q = [0.18, 0.31, 0.29, 0.22]
    cats = [("Personale", 168000), ("Consulenze specialistiche", 36000), ("Licenze e cloud", 24000), ("Attrezzature", 28500), ("Formazione", 9000), ("Spese generali", 22400)]
    rows = [["Voce", "T1", "T2", "T3", "T4", "Totale"]]
    for n, v in cats:
        rows.append([n] + [cents(round(v * x, 2)) for x in q] + [cents(v)])
    rows.append(["Totale"] + [cents(round(sum(v for _, v in cats) * x, 2)) for x in q] + [cents(sum(v for _, v in cats))])
    d.table(rows, [W - 130, 26, 26, 26, 26, 26], bold_rows=[7], align_right_from=1, font=8, zebra=True)
    d.H1("32. ANALISI DEI RISCHI DI PROGETTO")
    d.table([["Rischio", "Prob.", "Impatto", "Mitigazione", "Responsabile"], ["Cambio delle regole di un bando durante il progetto", "Media", "Medio", "Archivio versionato; aggiornamento entro 5 giorni", "M. Gallo"], ["Difficoltà a reclutare imprese pilota", "Bassa", "Alto", "Accordo preliminare con due associazioni", "V. Rossetti"],
             ["Ritardo nello sviluppo del motore di calcolo", "Media", "Alto", "Rilascio incrementale per famiglie di bandi", "A. Bertone"], ["Scarsa qualità dei documenti dei pilota", "Media", "Medio", "Verifica manuale dei dati incerti", "F. Greco"], ["Uscita di una persona chiave", "Bassa", "Medio", "Affiancamento e documentazione", "G. Ferraris"],
             ["Incidente di sicurezza informatica", "Bassa", "Alto", "ISO/IEC 27001, backup cifrati", "Resp. sicurezza"], ["Aumento dei costi del personale", "Bassa", "Basso", "Riserva del 3% nel piano dei costi", "F. Conti"], ["Ritardi nei pagamenti del contributo", "Media", "Medio", "Anticipo di liquidità con la cassa disponibile", "G. Ferraris"]],
            [62, 14, 16, W - 130, 38], align_right_from=9, font=7.6, zebra=True)
    d.H1("33. IMPATTO OCCUPAZIONALE, AMBIENTALE E DI GENERE")
    d.table([["Area", "Misura", "Valore atteso"], ["Occupazione", "Nuove assunzioni a tempo indeterminato entro 12 mesi dalla conclusione", "5"], ["Occupazione giovanile", "Quota di under 35 tra i nuovi assunti", "60%"], ["Parità di genere", "Quota femminile nel gruppo di lavoro", "38%"],
             ["Ambiente", "Energia elettrica da fonti rinnovabili per il laboratorio dati", "100%"], ["DNSH", "Verifica dell'assenza di danno significativo ai sei obiettivi ambientali", "Rispettato"], ["Territorio", "Imprese pilota in Piemonte e Lombardia", "15"]], [40, W - 80, 40], align_right_from=2, font=8, zebra=True)
    d.H1("34. CAPACITA' ECONOMICA E FINANZIARIA DEL PROPONENTE")
    rows = [["Indicatore", "2023", "2024", "2025"]]
    for l, f in (("Ricavi (euro)", lambda y: U(M.pl(y)["revenue"])), ("Utile (euro)", lambda y: U(M.pl(y)["net"])), ("Patrimonio netto (euro)", lambda y: U(M.balance(y)["pn"])), ("Disponibilità liquide (euro)", lambda y: U(M.balance(y)["cash"])),
                 ("Indice di liquidità corrente", lambda y: f"{M.ratio_notes(y)['current_ratio']:.2f}".replace(".", ",")), ("Debiti / patrimonio netto", lambda y: f"{M.ratio_notes(y)['debt_equity']:.2f}".replace(".", ","))):
        rows.append([l] + [f(y) for y in (2023, 2024, 2025)])
    d.table(rows, [W - 90, 30, 30, 30], align_right_from=1, font=8, zebra=True)
    d.P("Il cofinanziamento di 143.950 euro è coperto dalla liquidità disponibile (oltre 280.000 euro al 31/12/2025) e dal flusso operativo dell'esercizio: l'impresa non richiede anticipazioni e non prevede ricorso a nuovo debito per il progetto.")
    d.H1("35. DICHIARAZIONI E IMPEGNI")
    d.B(["Dichiarazione sostitutiva sulla dimensione d'impresa (piccola impresa, 17 addetti, ricavi superiori a 1,5 milioni e inferiori a 10 milioni di euro).", "Dichiarazione de minimis e verifica nel Registro nazionale degli aiuti (margine residuo 283.500 euro).",
         "Dichiarazione di assenza di condizioni ostative (art. 80 D.Lgs. 50/2016 per quanto applicabile) e di conflitto di interessi.", "Impegno a conservare la documentazione di spesa per dieci anni e a consentire verifiche in loco.",
         "Impegno a non delocalizzare le attività finanziate per cinque anni dalla conclusione.", "Dichiarazione di regolarità contributiva (DURC regolare, protocollo INAIL_48217763)."])
    d.H1("36. CHECK-LIST DEGLI ALLEGATI")
    d.table([["N.", "Allegato", "Stato"], ["1", "Dichiarazione sulla dimensione d'impresa", "Pronto"], ["2", "Dichiarazione de minimis", "Pronto"], ["3", "Bilanci degli ultimi due esercizi (2024 e 2025)", "Pronto"], ["4", "Preventivi per consulenze, attrezzature e licenze (tre per voce)", "Pronto"],
             ["5", "Curriculum del gruppo di lavoro", "Pronto"], ["6", "DURC in corso di validità", "Pronto"], ["7", "Visura camerale aggiornata", "Pronto"], ["8", "Lettere di adesione delle imprese pilota", "In raccolta (9 su 15)"], ["9", "Piano economico-finanziario dell'impresa", "Pronto"],
             ["10", "Relazione tecnica sugli aspetti innovativi", "In revisione"], ["11", "Documento di identità del legale rappresentante", "Pronto"], ["12", "Certificazioni ISO 9001 e ISO/IEC 27001", "Pronto"]], [14, W - 64, 50], align_right_from=9, font=8, zebra=True)
    d.small("Bozza interna: i contenuti sono indicativi e soggetti a revisione prima della presentazione. Dati fittizi di prova.")


# ================================================================================================ documenti aggiuntivi
def redditi(path: Path) -> Path:
    y = 2024
    p, b = M.pl(y), M.balance(y)
    t = p["tax"]
    d = Doc(path, f"Modello REDDITI SC {y + 1}", CO["name"], f"REDDITI SC {y + 1} - anno d'imposta {y}")
    W = _w(d)
    d.title_block(f"MODELLO REDDITI SC {y + 1} - ESTRATTO DEI QUADRI", f"Società di capitali - periodo d'imposta {y} - presentata telematicamente il 30/10/{y + 1}")
    d.table([["Dato", "Valore"], ["Contribuente", CO["name"]], ["Codice fiscale", CO["vat"]], ["Periodo d'imposta", f"01/01/{y} - 31/12/{y}"], ["Tipo di dichiarazione", "Ordinaria"], ["Intermediario", "Studio commercialista incaricato (dati di prova)"], ["Protocollo telematico", f"25103012345678-{y}"],
             ["Codice attività", "62.01.00"], ["Regime", "Ordinario"]], [58, W - 58], align_right_from=9, zebra=True, head=False)
    d.H1("QUADRO RF - VARIAZIONI IN AUMENTO E IN DIMINUZIONE")
    rows = [["Rigo", "Descrizione", "Importo (euro)"], ["RF5", "Utile dell'esercizio risultante dal conto economico", U(p["net"] + 0)]]
    k = 6
    for label, amount in t["up"].items():
        rows.append([f"RF{k}", f"Variazione in aumento: {label}", U(amount)])
        k += 1
    for label, amount in t["down"].items():
        rows.append([f"RF{k}", f"Variazione in diminuzione: {label}", U(-amount)])
        k += 1
    rows.append(["RF61", "Reddito imponibile (somma algebrica)", U(t["taxable"] + t["ires"] * 0)])
    d.table(rows, [20, W - 56, 36], align_right_from=2, font=8, zebra=True)
    d.H1("QUADRO RN - DETERMINAZIONE DELL'IRES")
    d.table([["Rigo", "Descrizione", "Importo (euro)"], ["RN1", "Reddito complessivo", U(t["taxable"])], ["RN4", "Deduzione ACE", U(round(p["pre_tax"] * 0.03))], ["RN6", "Reddito imponibile", U(t["taxable"])], ["RN17", "IRES lorda (aliquota 24%)", U(t["ires"])],
             ["RN22", "Crediti d'imposta utilizzati", U(0)], ["RN26", "Acconti versati", U(round(t["ires"] * 0.9))], ["RN30", "IRES a debito / credito", U(t["ires"] - round(t["ires"] * 0.9))]], [20, W - 56, 36], align_right_from=2, font=8, zebra=True)
    d.H1("QUADRO RS - PROSPETTI")
    d.table([["Prospetto", "Contenuto"], ["Prospetto dei dati di bilancio (RS)", f"Ricavi {U(p['revenue'])}; valore della produzione {U(p['a_total'])}; costi della produzione {U(p['b_total'])}; utile {U(p['net'])}; totale attivo {U(b['assets'])}"],
             ["Prospetto aiuti di Stato (RS401)", "Credito d'imposta R&S e aiuti de minimis dichiarati nel registro aiuti"], ["Prospetto dei crediti d'imposta (RU)", f"Credito ricerca e sviluppo {y}: costi ammissibili {U(M.GRANTS[2] * 10)} euro, credito {U(M.GRANTS[2])} euro"],
             ["Prospetto dei beni ammortizzabili", "Quote di ammortamento fiscale pari a quelle civilistiche"], ["Prospetto delle perdite", "Nessuna perdita pregressa"]], [60, W - 60], align_right_from=9, font=8, zebra=True)
    d.small("Estratto di prova a fini dimostrativi: i valori derivano dal bilancio di prova dell'esercizio.")
    return d.save()


def irap(path: Path) -> Path:
    y = 2024
    p = M.pl(y)
    d = Doc(path, f"Dichiarazione IRAP {y + 1}", CO["name"], f"IRAP {y + 1} - periodo d'imposta {y}")
    W = _w(d)
    d.title_block(f"DICHIARAZIONE IRAP {y + 1}", f"Periodo d'imposta {y} - presentata il 30/10/{y + 1}")
    d.H1("QUADRO IQ - DETERMINAZIONE DEL VALORE DELLA PRODUZIONE NETTA")
    d.table([["Rigo", "Descrizione", "Importo (euro)"], ["IQ1", "Ricavi delle vendite e delle prestazioni", U(p["revenue"])], ["IQ4", "Variazione dei lavori in corso", U(p["wip_delta"])], ["IQ5", "Incrementi per lavori interni", U(p["capitalized"])], ["IQ6", "Altri ricavi e proventi", U(p["grants"] + p["other_income"])],
             ["IQ7", "Totale valore della produzione", U(p["a_total"])], ["IQ8", "Costi per materie e merci", U(p["b6"])], ["IQ9", "Costi per servizi", U(p["b7"])], ["IQ10", "Costi per godimento di beni di terzi", U(p["b8"])], ["IQ11", "Ammortamenti e svalutazioni", U(p["b10a"] + p["b10b"] + p["b10d"])],
             ["IQ12", "Oneri diversi di gestione", U(p["b14"])], ["IQ21", "Costo del lavoro non deducibile (variazioni in aumento)", U(0)], ["IQ52", "Valore della produzione netta", U(p["tax"]["irap_base"])], ["IQ53", "Deduzioni del costo del lavoro a tempo indeterminato", U(p["b9a"] + p["b9b"] + p["b9c"] + p["b9e"])],
             ["IQ55", "Base imponibile", U(p["tax"]["irap_base"])]], [20, W - 56, 36], align_right_from=2, font=8, zebra=True)
    d.H1("QUADRO IR - DETERMINAZIONE DELL'IMPOSTA")
    d.table([["Rigo", "Descrizione", "Importo (euro)"], ["IR1", "Base imponibile", U(p["tax"]["irap_base"])], ["IR2", "Aliquota regionale (Piemonte)", "3,90%"], ["IR3", "Imposta lorda", U(p["irap"])], ["IR20", "Acconti versati", U(round(p["irap"] * 0.92))], ["IR21", "Saldo a debito", U(p["irap"] - round(p["irap"] * 0.92))]],
            [20, W - 56, 36], align_right_from=2, font=8, zebra=True)
    d.small("Documento di prova: i valori derivano dal bilancio di prova dell'esercizio.")
    return d.save()


def iva_annuale(path: Path) -> Path:
    y = 2025
    d = Doc(path, f"Dichiarazione IVA {y + 1}", CO["name"], f"Dichiarazione annuale IVA - anno {y}")
    W = _w(d)
    d.title_block(f"DICHIARAZIONE ANNUALE IVA {y + 1}", f"Anno d'imposta {y} - presentata il 30/04/{y + 1}")
    em = sum(i["taxable"] for i in LG.invoices_issued(y))
    vat_e = sum(i["vat"] for i in LG.invoices_issued(y))
    rc = sum(i["taxable"] for i in LG.invoices_received(y))
    vat_r = sum(i["vat"] for i in LG.invoices_received(y))
    d.H1("QUADRO VE - OPERAZIONI ATTIVE")
    d.table([["Rigo", "Descrizione", "Imponibile (euro)", "Imposta (euro)"], ["VE23", "Operazioni imponibili al 22%", E(sum(i["taxable"] for i in LG.invoices_issued(y) if i["vat"])), E(vat_e)], ["VE30", "Operazioni non imponibili (art. 7-ter, clienti esteri)", E(sum(i["taxable"] for i in LG.invoices_issued(y) if not i["vat"])), ""],
             ["VE38", "Totale delle operazioni attive", E(em), E(vat_e)]], [20, W - 100, 40, 40], align_right_from=2, font=8, zebra=True)
    d.H1("QUADRO VF - OPERAZIONI PASSIVE")
    d.table([["Rigo", "Descrizione", "Imponibile (euro)", "Imposta (euro)"], ["VF13", "Acquisti di beni e servizi nazionali al 22%", E(rc), E(vat_r)], ["VF25", "Totale degli acquisti", E(rc), E(vat_r)]], [20, W - 100, 40, 40], align_right_from=2, font=8, zebra=True)
    d.H1("QUADRO VL - LIQUIDAZIONI E SALDO")
    rows = [["Mese", "IVA a debito (euro)", "IVA a credito (euro)", "Saldo (euro)", "Versato il"]]
    for m in range(1, 13):
        dv = sum(i["vat"] for i in LG.invoices_issued(y) if i["date"].month == m)
        cr = sum(i["vat"] for i in LG.invoices_received(y) if i["date"].month == m)
        rows.append([["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"][m - 1], E(dv), E(cr), E(dv - cr), f"16/{(m % 12) + 1:02d}/{y + (1 if m == 12 else 0)}"])
    rows.append(["Totale", E(vat_e), E(vat_r), E(vat_e - vat_r), ""])
    d.table(rows, [30, 40, 40, 36, W - 146], bold_rows=[13], align_right_from=1, font=8, zebra=True)
    d.small("Documento di prova: gli importi derivano dai registri IVA di prova; le operazioni con pubbliche amministrazioni sono in scissione dei pagamenti.")
    return d.save()


def piano_ammortamento_finanziamento(path: Path) -> Path:
    d = Doc(path, "Piano di ammortamento del finanziamento", CO["name"], "Finanziamento chirografario - piano di ammortamento")
    W = _w(d)
    d.title_block("PIANO DI AMMORTAMENTO DEL FINANZIAMENTO CHIROGRAFARIO", "Importo originario euro 300.000,00 - erogato il 30/09/2020 - 28 rate trimestrali - tasso variabile Euribor 3 mesi + 2,10 punti")
    rows = [["N.", "Data", "Debito iniziale", "Quota capitale", "Interessi", "Rata totale", "Debito residuo", "Tasso applicato"]]
    left = 300000.0
    cap = 300000 / 28
    from datetime import date as D
    eur_path = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    for k in range(1, 29):
        mm = 12 + 3 * k - 12
        y = 2020 + (9 + 3 * k - 1) // 12
        m = (9 + 3 * k - 1) % 12 + 1
        day = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
        rate = 0.0210 + (0.0 if y <= 2021 else (0.012 if y == 2022 else (0.036 if y == 2023 else (0.033 if y == 2024 else 0.022)))) + (0.0 if y > 2022 else 0.0)
        interest = round(left * rate / 4, 2)
        q = round(cap, 2) if k < 28 else round(left, 2)
        rows.append([str(k), f"{day:02d}/{m:02d}/{y}", cents(left), cents(q), cents(interest), cents(q + interest), cents(left - q), f"{rate * 100:.2f}%".replace(".", ",")])
        left = round(left - q, 2)
    d.table(rows, [8, 22, 28, 26, 22, 26, 28, W - 160], align_right_from=2, font=7.6, zebra=True)
    d.small("Le rate in scadenza dopo il 31/12/2025 sono quelle ricomprese nel piano del bilancio; il residuo al 31/12/2025 è di 75.000 euro. Il piano è un prospetto di prova: i tassi storici sono indicativi.")
    return d.save()


def estratto_conto(path: Path) -> Path:
    d = Doc(path, "Estratto conto bancario - agosto 2026", CO["name"], "Estratto conto - agosto 2026")
    W = _w(d)
    d.title_block("ESTRATTO CONTO BANCARIO - AGOSTO 2026", "Conto corrente ordinario n. 000123456789 - Banca prima (istituto di prova)")
    r = LG.rng("ec-2026-08")
    bal = 311842.17
    rows = [["Data", "Valuta", "Descrizione", "Dare", "Avere", "Saldo"]]
    ops: List[tuple] = []
    for c in LG.customers()[:14]:
        ops.append((r.randint(1, 28), f"Bonifico ricevuto {c['name'][:36]} - saldo fattura", 0, round(r.uniform(1800, 21000), 2)))
    for s in LG.suppliers()[:18]:
        ops.append((r.randint(1, 28), f"Bonifico a {s['name'][:36]} - pagamento fattura", round(r.uniform(300, 9800), 2), 0))
    ops += [(1, "Addebito canone di locazione sede di via Garibaldi", 4500.0, 0), (1, "Addebito canone di locazione unità locale di corso Francia", 1450.0, 0), (5, "Addebito SDD canone leasing autovetture", 1100.0, 0), (10, "Commissioni e spese di tenuta conto", 48.2, 0),
            (16, "Pagamento F24 - ritenute, IVA e contributi (luglio)", 52432.0, 0), (21, "Accredito POS e incassi carte", 0, 2430.5), (26, "Bonifico stipendi agosto (cumulativo)", 41230.6, 0), (28, "Addebito carta di credito aziendale", 3120.4, 0), (31, "Competenze di liquidazione interessi", 0, 31.7)]
    ops.sort()
    for day, desc, dare, avere in ops:
        bal = round(bal - dare + avere, 2)
        rows.append([f"{day:02d}/08/2026", f"{day:02d}/08/2026", desc, cents(dare) if dare else "", cents(avere) if avere else "", cents(bal)])
    d.table(rows, [20, 20, W - 114, 22, 22, 30], align_right_from=3, font=7.4, zebra=True)
    d.table([["Riepilogo", "Importo (euro)"], ["Saldo iniziale al 01/08/2026", cents(311842.17)], ["Totale movimenti in dare", cents(round(sum(o[2] for o in ops), 2))], ["Totale movimenti in avere", cents(round(sum(o[3] for o in ops), 2))], ["Saldo finale al 31/08/2026", cents(bal)]], [W - 40, 40], bold_rows=[4], font=8)
    d.small("Estratto di prova: soggetti e importi sono fittizi.")
    return d.save()


def contratto_locazione(path: Path) -> Path:
    d = Doc(path, "Contratto di locazione ad uso diverso", CO["name"], "Contratto di locazione - sede legale")
    W = _w(d)
    d.title_block("CONTRATTO DI LOCAZIONE DI IMMOBILE AD USO NON ABITATIVO", "Estratto - sede legale di via Giuseppe Garibaldi 28, Torino")
    arts = [("Art. 1 - Parti", f"Locatore: Immobiliare Garibaldi 28 S.r.l. (società di prova). Conduttore: {CO['name']}, in persona dell'amministratore unico Giulia Ferraris."), ("Art. 2 - Oggetto", "Unità immobiliare al piano secondo e terzo, di 420 mq calpestabili, con otto posti auto interrati, identificata al catasto fabbricati di Torino (dati di prova)."),
            ("Art. 3 - Destinazione d'uso", "Uffici e studi professionali; è vietata ogni diversa destinazione senza il consenso scritto del locatore."), ("Art. 4 - Durata", "Sei anni dal 01/01/2023 al 31/12/2028, con rinnovo tacito per ulteriori sei anni salvo disdetta con preavviso di dodici mesi (formula 6+6)."),
            ("Art. 5 - Canone", "Euro 54.000,00 annui, pagabili in rate mensili anticipate di 4.500,00 euro entro il giorno 5, aggiornati annualmente nella misura del 75% della variazione ISTAT dell'indice dei prezzi al consumo."), ("Art. 6 - Spese condominiali", "Le spese di riscaldamento, pulizia delle parti comuni e portierato sono a carico del conduttore in base ai millesimi, con acconti trimestrali."),
            ("Art. 7 - Deposito cauzionale e garanzie", "Deposito cauzionale di 5.850,00 euro, pari a poco più di una mensilità; fidejussione bancaria a prima richiesta di 27.000,00 euro per l'intera durata."), ("Art. 8 - Migliorie", "Le migliorie eseguite dal conduttore (pareti, impianti, area ristoro) restano acquisite al locatore alla scadenza, senza indennità, salvo diverso accordo scritto."),
            ("Art. 9 - Recesso", "Il conduttore può recedere in qualsiasi momento con preavviso di sei mesi per gravi motivi; il recesso anticipato senza gravi motivi comporta il pagamento di tre mensilità."), ("Art. 10 - Registrazione e imposte", "Il contratto è registrato telematicamente; l'imposta di registro è ripartita a metà tra le parti."),
            ("Art. 11 - Foro competente", "Per ogni controversia è competente in via esclusiva il Foro di Torino.")]
    for t, tx in arts:
        d.H2(t)
        d.P(tx)
    d.table([["Dato economico", "Valore"], ["Canone annuo", "54.000,00 euro"], ["Rata mensile", "4.500,00 euro"], ["Deposito cauzionale", "5.850,00 euro"], ["Fidejussione bancaria", "27.000,00 euro"], ["Canone residuo fino al 31/12/2028 (dal 01/01/2026)", "162.000,00 euro"]], [W - 50, 50], align_right_from=1, font=8, zebra=True)
    d.small("Estratto di prova: soggetti, dati catastali e importi sono fittizi.")
    return d.save()


def libro_soci(path: Path) -> Path:
    d = Doc(path, "Libro dei soci", CO["name"], "Libro dei soci - estratto")
    W = _w(d)
    d.title_block("LIBRO DEI SOCI", f"{CO['name']} - estratto aggiornato al 31/12/2025")
    d.table([["Socio", "Codice fiscale", "Quota", "Valore nominale (euro)", "Data iscrizione", "Titolo"], ["FERRARIS GIULIA", P.BY_ID["M001"]["cf"], "60%", "30.000,00", "14/03/2016", "Sottoscrizione all'atto costitutivo e aumento di capitale"],
             ["BERTOLOTTI MARCO", P.fiscal_code("Bertolotti", "Marco", date(1979, 3, 14), True, "L219"), "40%", "20.000,00", "14/03/2016", "Sottoscrizione all'atto costitutivo e aumento di capitale"]], [34, 40, 14, 30, 24, W - 142], align_right_from=9, font=8)
    d.H1("MOVIMENTI DEL CAPITALE")
    d.table([["Data", "Operazione", "Capitale prima", "Capitale dopo", "Delibera"], ["14/03/2016", "Costituzione", "-", "10.000,00", "Atto costitutivo"], ["29/04/2021", "Aumento a pagamento e con riserve", "10.000,00", "50.000,00", "Assemblea straordinaria, verbale notarile"]], [24, 66, 30, 30, W - 150], align_right_from=2, font=8)
    d.H1("DIVIDENDI DISTRIBUITI")
    rows = [["Esercizio", "Delibera", "Dividendo totale (euro)", "A G. Ferraris (60%)", "A M. Bertolotti (40%)"]]
    for y, div in ((2022, 40000), (2023, 60000), (2024, 80000), (2025, 90000)):
        rows.append([str(y), f"Assemblea del 28/04/{y + 1}", cents(div), cents(div * 0.6), cents(div * 0.4)])
    d.table(rows, [24, 50, 40, 38, W - 152], align_right_from=2, font=8, zebra=True)
    d.small("Estratto di prova.")
    return d.save()


def relazione_rs(path: Path) -> Path:
    y = 2025
    d = Doc(path, "Relazione tecnica sul credito d'imposta ricerca e sviluppo", CO["name"], f"Relazione tecnica R&S {y}")
    W = _w(d)
    base = M.GRANTS[3] * 10
    d.title_block(f"RELAZIONE TECNICA - CREDITO D'IMPOSTA RICERCA E SVILUPPO {y}", "Art. 1, commi 198-206, legge 160/2019 - progetto «Atlas: motore di calcolo deterministico per la previsione dei costi e il recupero delle agevolazioni»")
    d.H1("1. Descrizione del progetto")
    d.P("Il progetto ha l'obiettivo di sviluppare un motore di calcolo che stimi, a partire dal bilancio di un'impresa, i costi dell'anno successivo e il recupero ottenibile da bandi e agevolazioni, rispettando tetti, cumulo e limiti di aiuto, con un risultato riproducibile e verificabile. "
        "La novità rispetto allo stato dell'arte è la rappresentazione formale delle regole dei bandi come dati strutturati e la loro applicazione con aritmetica decimale e ottimizzazione lineare mista intera.")
    d.H1("2. Incertezza tecnico-scientifica")
    d.B(["Possibilità di rappresentare in modo uniforme regole eterogenee (percentuali, tetti per categoria, soglie, cumulo) senza perdere informazioni rilevanti.", "Garanzia di riproducibilità e di assenza di arrotondamenti in un problema di ripartizione tra più fondi con vincoli di cumulo.",
         "Estrazione affidabile delle voci contabili da documenti reali eterogenei (testo e scansioni) con misura dell'incertezza.", "Validità statistica della stima rispetto agli importi effettivamente ammessi."])
    d.H1("3. Attività svolte nell'esercizio")
    d.table([["Attività", "Natura", "Mesi", "Risultato"], ["Modello formale delle regole dei bandi", "Ricerca industriale", "Gen-Giu", "Schema dei dati con 18 tipi di regola"], ["Motore di ripartizione ottimale", "Sviluppo sperimentale", "Mar-Set", "Algoritmo con risultato deterministico e traccia"],
             ["Lettura dei documenti contabili", "Sviluppo sperimentale", "Apr-Nov", "Riconoscimento di bilanci, F24 e cedolini con affidabilità"], ["Validazione su casi reali", "Sviluppo sperimentale", "Set-Dic", "Scostamento medio del 7,8% su 15 imprese"]], [60, 34, 20, W - 114], align_right_from=9, font=8, zebra=True)
    d.H1("4. Costi ammissibili")
    cp = LG.alloc(base, [70, 18, 7, 5])
    d.table([["Voce di costo", "Importo (euro)"], ["Personale impiegato in attività di ricerca e sviluppo", cents(cp[0])], ["Ricerca contrattuale e consulenze tecniche", cents(cp[1])], ["Quote di ammortamento di attrezzature di laboratorio", cents(cp[2])], ["Materiali e forniture per i prototipi", cents(cp[3])],
             ["Totale costi ammissibili", cents(base)], ["Credito d'imposta (10%)", cents(M.GRANTS[3])]], [W - 40, 40], bold_rows=[5, 6], align_right_from=1, font=8)
    d.H1("5. Personale impiegato")
    rows = [["Matricola", "Ruolo", "Ore dedicate", "Costo orario (euro)", "Costo imputato (euro)"]]
    team = [("M002", "Responsabile sviluppo", 560), ("M003", "Sviluppatore senior", 820), ("M004", "Sviluppatore senior", 780), ("M014", "Data scientist", 940), ("M005", "Sviluppatore", 720), ("M007", "Sviluppatore", 640), ("M008", "Project manager", 380), ("M012", "UX designer", 420)]
    tot = 0
    for eid, role, hours in team:
        e = P.BY_ID[eid]
        rate = round(e["cost"] / 1720, 2)
        rows.append([eid, role, str(hours), cents(rate), cents(round(rate * hours, 2))])
        tot += round(rate * hours, 2)
    rows.append(["Totale", "", str(sum(h for _, _, h in team)), "", cents(tot)])
    d.table(rows, [20, W - 130, 26, 40, 44], bold_rows=[len(rows) - 1], align_right_from=2, font=8, zebra=True)
    d.small("I fogli di presenza mensili firmati sono conservati agli atti. Il costo del personale della relazione è quello del libro unico del lavoro.")
    d.H1("6. Conclusioni")
    d.P("Le attività descritte rispettano i criteri di novità, creatività, incertezza, sistematicità e riproducibilità previsti dal Manuale di Frascati e dalla normativa. La relazione è predisposta dal responsabile di progetto e sottoscritta dal legale rappresentante; la certificazione contabile è affidata a un revisore esterno.")
    return d.save()
