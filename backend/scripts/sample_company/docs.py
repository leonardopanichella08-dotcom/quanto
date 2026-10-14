"""Gli altri documenti dell'azienda: visura camerale, cedolini, F24, bozza di candidatura, DURC, dichiarazione de minimis, business plan e fogli Excel."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict, List

from . import docs_more as DM
from . import docs_ext as EXT
from . import long_docs as L
from . import model as M
from . import people as P
from .pdfkit import Doc, cents, pct, units

CO = M.COMPANY
U = units


def _width(d: Doc) -> float:
    return d.width / 2.8346


# ================================================================================================ visura camerale
def make_registry(path: Path) -> Path:
    d = Doc(path, "Visura ordinaria di società di capitali", f"{CO['cciaa']}", "Registro delle Imprese - Visura ordinaria")
    W = _width(d)
    d.title_block("VISURA ORDINARIA DI SOCIETA' DI CAPITALI", f"{CO['cciaa']} - Registro delle Imprese")
    d.table([["Documento n.", "T 481726395"], ["Data di estrazione", "02/10/2026"], ["Estratto dal Registro Imprese", "in data 02/10/2026 alle ore 11:42:08"], ["Richiedente", f"{CO['name']} (accesso con firma digitale del legale rappresentante)"]],
            [52, W - 52], head=False, align_right_from=9, zebra=True)
    d.H1("INFORMAZIONI SULLA SEDE")
    d.table([["Denominazione", CO["name"]], ["Forma giuridica", CO["legal_form"]], ["Indirizzo sede legale", f"{CO['street']}, {CO['zip']} {CO['city']} ({CO['prov']})"],
             ["Indirizzo PEC", CO["pec"]], ["Numero REA", CO["rea"]], ["Codice fiscale", CO["vat"]], ["Partita IVA", CO["vat"]],
             ["Data atto di costituzione", CO["founded"]], ["Data iscrizione al Registro Imprese", CO["iscr_ri"]], ["Data di inizio attività", "21/03/2016"],
             ["Durata della società", "fino al 31/12/2060"], ["Termine esercizio", "31/12 di ogni anno"], ["Stato attività", "Attiva"],
             ["Procedure concorsuali in corso", "Nessuna"], ["Scioglimento e liquidazione", "Non in corso"]], [58, W - 58], head=False, align_right_from=9, zebra=True)
    d.H1("CAPITALE E STRUMENTI FINANZIARI")
    d.table([["Capitale sociale deliberato", f"euro {cents(CO['capital'])}"], ["Capitale sociale sottoscritto", f"euro {cents(CO['capital'])}"], ["Capitale sociale versato", f"euro {cents(CO['capital'])}"],
             ["Conferimenti", "in denaro"], ["Strumenti finanziari partecipativi", "Nessuno"], ["Titoli di debito", "Nessuno"]], [58, W - 58], head=False, align_right_from=9, zebra=True)
    d.H1("ATTIVITA'")
    d.table([["Codice ATECO attività prevalente", f"{CO['ateco']} - {CO['ateco_desc']}"], ["Codice ATECO attività secondaria", "62.02.00 - Consulenza nel settore delle tecnologie dell'informatica"],
             ["Altra attività secondaria", "63.11.19 - Elaborazione dei dati, hosting e attività connesse"], ["Altra attività secondaria", "85.59.20 - Corsi di formazione e corsi di aggiornamento professionale"],
             ["Data inizio attività prevalente", "21/03/2016"], ["Registro Imprese - Sezione", "Sezione ordinaria. Non iscritta alla sezione speciale delle start-up innovative né delle PMI innovative"],
             ["Dimensione dichiarata", "Piccola impresa ai sensi della raccomandazione 2003/361/CE (dato dichiarato dall'impresa)"]], [58, W - 58], head=False, align_right_from=9, zebra=True)
    d.H2("Oggetto sociale")
    d.P("La società ha per oggetto lo sviluppo, la produzione, la manutenzione e la commercializzazione di software, di piattaforme web e di sistemi di analisi dei dati, anche in modalità di servizio (software as a service); la prestazione di servizi di consulenza informatica, "
        "organizzativa e di progettazione di sistemi informativi per imprese, enti pubblici e privati; la gestione di infrastrutture informatiche, di servizi di hosting e di elaborazione dati; l'organizzazione e l'erogazione di attività di formazione sui temi della trasformazione digitale; "
        "lo svolgimento di attività di ricerca e sviluppo sperimentale nei campi dell'informatica e dell'analisi predittiva. La società può compiere tutte le operazioni mobiliari, immobiliari e finanziarie, "
        "non nei confronti del pubblico, ritenute dall'organo amministrativo necessarie o utili per il conseguimento dell'oggetto sociale.")
    d.H1("UNITA' LOCALI")
    d.table([["Sede", "Indirizzo", "Attività", "Data apertura"], ["Sede legale e operativa", f"{CO['street']}, {CO['zip']} {CO['city'].title()} ({CO['prov']})", "Uffici e sviluppo software", "21/03/2016"],
             ["Unità locale n. 1", "Corso Francia 114, 10143 Torino (TO)", "Laboratorio dati e formazione", "01/09/2021"]], [32, W - 98, 42, 24], align_right_from=9)
    d.H1("SOCI E TITOLARI DI DIRITTI SU QUOTE E AZIONI")
    cf_b = P.fiscal_code("Bertolotti", "Marco", date(1979, 3, 14), True, "L219")
    d.table([["Socio", "Codice fiscale", "Quota", "Valore nominale (euro)", "Diritto"],
             ["FERRARIS GIULIA", P.BY_ID["M001"]["cf"], "60%", "30.000,00", "Proprietà"], ["BERTOLOTTI MARCO", cf_b, "40%", "20.000,00", "Proprietà"]], [48, 42, 18, 34, W - 142], align_right_from=9)
    d.small("Elenco soci e titolari di diritti su azioni e quote sociali alla data del 31/12/2025 (ultimo deposito).")
    d.H1("AMMINISTRATORI E SINDACI")
    d.table([["Carica", "Nominativo", "Data nomina", "Durata", "Poteri"], ["Amministratore unico", f"FERRARIS GIULIA - {P.BY_ID['M001']['cf']}", "21/03/2016 (rinnovata il 29/04/2022)", "Fino a revoca", "Rappresentanza della società con firma singola"]],
            [32, 56, 38, 24, W - 150], align_right_from=9)
    d.P("Non è stato nominato un organo di controllo né un revisore legale: la società non supera i limiti dimensionali previsti dall'art. 2477 del codice civile.")
    d.H1("ADDETTI E DIPENDENTI")
    d.table([["Dato", "Valore", "Fonte e data"], ["Addetti (dipendenti e indipendenti)", "17", "INPS, dato al 30/06/2026"], ["di cui dipendenti", "15", "INPS, dato al 30/06/2026"],
             ["di cui indipendenti (soci lavoratori)", "2", "INPS, dato al 30/06/2026"], ["Numero medio annuo di addetti", "16,5", "INPS, anno 2025"]], [70, 30, W - 100], align_right_from=9)
    d.H1("ALBI, RUOLI, LICENZE, ABILITAZIONI")
    d.P("Non risultano iscrizioni ad albi, ruoli o elenchi, né licenze o autorizzazioni. Certificazioni volontarie dichiarate dall'impresa: ISO 9001:2015 (qualità) e ISO/IEC 27001:2022 (sicurezza delle informazioni), con scadenza 31/05/2027.")
    d.H1("INFORMAZIONI PATRIMONIALI E FINANZIARIE")
    d.table([["Esercizio", "Data deposito", "Ricavi delle vendite e prestazioni (euro)", "Utile/perdita (euro)", "Dipendenti medi"],
             ["2024", "29/05/2025", U(M.REVENUE[2]), U(M.pl(2024)["net"]), "13"], ["2023", "30/05/2024", U(M.REVENUE[1]), U(M.pl(2023)["net"]), "11"], ["2022", "31/05/2023", U(M.REVENUE[0]), U(M.pl(2022)["net"]), "9"]],
            [24, 28, 58, 36, W - 146], align_right_from=2)
    d.small("Il bilancio dell'esercizio 2025, approvato il 28/04/2026, risulta in fase di deposito alla data della visura.")
    d.H1("PROTESTI, PROCEDURE E STORIA DELLA SOCIETA'")
    d.P("Protesti: nessuno risultante. Procedure concorsuali: nessuna. Trasferimenti di sede: dal 01/10/2019 la sede è in Torino, via Giuseppe Garibaldi 28 (precedentemente in via San Quintino 12, Torino).")
    d.table([["Data", "Evento"], ["14/03/2016", "Atto di costituzione con capitale sociale di 10.000,00 euro, notaio in Torino (dati di prova)"], ["21/03/2016", "Iscrizione al Registro delle Imprese di Torino"],
             ["18/12/2019", "Trasferimento della sede legale in via Giuseppe Garibaldi 28"], ["29/04/2021", "Aumento di capitale sociale da 10.000,00 a 50.000,00 euro con utilizzo di riserve e nuovi conferimenti in denaro"],
             ["01/09/2021", "Apertura dell'unità locale di corso Francia 114"], ["29/04/2022", "Rinnovo della nomina dell'amministratore unico"]], [28, W - 28], align_right_from=9)
    d.small("Documento di prova: gli estremi dell'atto, del notaio e dei protocolli sono inventati.")
    L.extend_registry(d)
    DM.registry_more(d)
    EXT.registry_ext(d)
    return d.save()


# ================================================================================================ cedolini
def _irpef(gross: float, months: int):
    inps = round(gross * 0.0919, 2)
    taxable_m = gross - inps
    taxable = taxable_m * months
    tax = min(taxable, 28000) * 0.23 + max(0.0, min(taxable, 50000) - 28000) * 0.35 + max(0.0, taxable - 50000) * 0.43
    if taxable <= 15000:
        detr = 1955.0
    elif taxable <= 28000:
        detr = 1910 + 1190 * (28000 - taxable) / 13000
    elif taxable <= 50000:
        detr = 1910 * (50000 - taxable) / 22000
    else:
        detr = 0.0
    gross_tax_m = round(tax / months, 2)
    detr_m = round(min(detr, tax) / months, 2)
    net_tax = round(gross_tax_m - detr_m, 2)
    reg = round(taxable * 0.0173 / 12, 2)           # addizionale regionale Piemonte (scaglione), trattenuta in rate
    com = round(taxable * 0.0050 / 12, 2)           # addizionale comunale Torino
    return inps, round(taxable_m, 2), gross_tax_m, detr_m, net_tax, reg, com


def make_payslip(path: Path, emp_id: str, gross: float, mansione: str) -> Path:
    e = P.BY_ID[emp_id]
    inps, taxable_m, gross_tax, detr, net_tax, reg, com = _irpef(gross, 14)
    union = round(gross * 0.0045, 2) if e["level"] in ("3", "4") else 0.0
    net = round(gross - inps - net_tax - reg - com - union, 2)
    tfr = round(gross / 13.5, 2)
    d = Doc(path, "Cedolino paga - Libro unico del lavoro", f"{CO['name']}", f"Libro Unico del Lavoro - Cedolino di agosto 2026")
    W = _width(d)
    base = round(gross * 0.58, 2)
    cont = round(gross * 0.2733, 2)
    edr = 10.33
    scatti = round(gross * 0.038, 2)
    super_ = round(gross - base - cont - edr - scatti, 2)
    d.title_block("CEDOLINO PAGA - LIBRO UNICO DEL LAVORO", f"Periodo di competenza: agosto 2026 - cedolino n. 08/2026/{e['id'][-3:]}")
    d.H1("AZIENDA")
    d.table([["Ragione sociale", CO["name"]], ["Sede", f"{CO['street']}, {CO['zip']} {CO['city'].title()} ({CO['prov']})"], ["Codice fiscale / Partita IVA", CO["vat"]],
             ["Matricola INPS", "0123456789 (sede 0100 Torino)"], ["Posizione assicurativa INAIL (PAT)", "9876543/21"], ["CCNL applicato", "Commercio, Terziario Distribuzione e Servizi - Confcommercio"]],
            [62, W - 62], head=False, align_right_from=9, zebra=True)
    d.H1("DATI DEL LAVORATORE")
    d.table([["Cognome e nome", f"{e['surname'].upper()} {e['name'].upper()}"], ["Codice fiscale", e["cf"]], ["Matricola aziendale", e["id"]],
             ["Data di nascita", e["birth"].strftime("%d/%m/%Y")], ["Data di assunzione", date.fromisoformat(e["hired"]).strftime("%d/%m/%Y")],
             ["Tipo di rapporto", f"Tempo indeterminato, orario {e['hours']} ore settimanali"], ["Qualifica", mansione], ["Livello", e["level"]], ["Mensilità", "14"],
             ["Periodo di retribuzione", "08/2026"], ["Modalità di pagamento", "Bonifico bancario - " + P.iban(e["cf"][:12])], ["Giorni retribuiti", "26 su 26"]],
            [62, W - 62], head=False, align_right_from=9, zebra=True)
    d.H1("ELEMENTI DELLA RETRIBUZIONE MENSILE")
    d.table([["Elemento", "Importo mensile (euro)"], ["Paga base conglobata", cents(base)], ["Contingenza", cents(cont)], ["Elemento distinto della retribuzione (EDR)", cents(edr)],
             ["Scatti di anzianità maturati", cents(scatti)], ["Superminimo individuale", cents(super_)]], [W - 40, 40])
    d.H1("COMPETENZE DEL MESE")
    d.table([["Cod.", "Descrizione", "Base", "Ore/giorni", "Importo (euro)"], ["0001", "Retribuzione ordinaria", cents(gross), "26,00 gg", cents(round(gross - 0.0, 2))],
             ["0310", "Ferie godute (già comprese nella retribuzione ordinaria)", "", "0,00 gg", "0,00"], ["0420", "Permessi retribuiti (ROL) goduti", "", "0,00 ore", "0,00"],
             ["0900", "Trasferte e rimborsi spese non imponibili", "", "", "0,00"], ["", f"TOTALE COMPETENZE {cents(gross)}", "", "", cents(gross)]], [14, W - 90, 22, 22, 32], bold_rows=[5], align_right_from=2)
    d.H1("TRATTENUTE DEL MESE")
    rows = [["Cod.", "Descrizione", "Imponibile", "Aliquota", "Importo (euro)"], ["5001", "Contributi INPS a carico del lavoratore", cents(gross), "9,19%", cents(inps)],
            ["5100", "IRPEF lorda del mese", cents(taxable_m), "scaglioni", cents(gross_tax)], ["5110", "Detrazioni per lavoro dipendente", "", "", cents(-detr)],
            ["5120", "IRPEF netta del mese", "", "", cents(net_tax)], ["5200", "Addizionale regionale IRPEF (Piemonte)", cents(taxable_m), "", cents(reg)],
            ["5210", "Addizionale comunale IRPEF (Torino)", cents(taxable_m), "0,50%", cents(com)]]
    if union:
        rows.append(["5400", "Contributo sindacale (quota associativa)", cents(gross), "0,45%", cents(union)])
    rows.append(["", f"TOTALE TRATTENUTE {cents(round(inps + net_tax + reg + com + union, 2))}", "", "", cents(round(inps + net_tax + reg + com + union, 2))])
    d.table(rows, [14, W - 90, 22, 22, 32], bold_rows=[len(rows) - 1], align_right_from=2)
    d.table([["Arrotondamento mese precedente", "0,00"], [f"NETTO IN BUSTA {cents(net)}", cents(net)]], [W - 40, 40], head=False, bold_rows=[1])
    d.H1("RIEPILOGO IMPONIBILI E ONERI DEL MESE")
    d.table([["Imponibile previdenziale INPS", cents(gross)], ["Contributi INPS lavoratore", cents(inps)], ["Imponibile fiscale del mese", cents(taxable_m)],
             ["Contributi a carico dell'azienda (INPS 28,43% circa)", cents(round(gross * 0.2843, 2))], ["Premio INAIL del mese (stima)", cents(round(gross * 0.0089, 2))],
             ["Contributo Fondo Est (assistenza sanitaria) a carico azienda", cents(10.42)]], [W - 40, 40], head=False, zebra=True)
    d.H1("PROGRESSIVI ANNUALI AL 31/08/2026 E TRATTAMENTO DI FINE RAPPORTO")
    d.table([["Imponibile previdenziale progressivo", cents(round(gross * 9.0, 2))], ["Imponibile fiscale progressivo", cents(round(taxable_m * 9.0, 2))], ["IRPEF netta trattenuta nell'anno", cents(round(net_tax * 8.0, 2))],
             [f"QUOTA TFR {cents(tfr)}", cents(tfr)], ["Fondo TFR al 31/12/2025 (rivalutato)", cents(round(tfr * 12 * ((2026 - date.fromisoformat(e['hired']).year) + 0.5), 2))],
             ["Destinazione del TFR", "Mantenuto in azienda (Fondo di Tesoreria INPS per la quota eccedente)"]], [W - 60, 60], head=False, zebra=True)
    d.H1("FERIE, PERMESSI E RATEI")
    d.table([["", "Ferie (giorni)", "Permessi ROL (ore)"], ["Residuo anno precedente", "6,00", "16,00"], ["Maturato nell'anno", "17,33", "49,33"], ["Goduto al 31/08/2026", "11,83", "32,00"], ["Saldo residuo al 31/08/2026", "11,50", "33,33"]],
            [W - 80, 40, 40], bold_rows=[4])
    d.P("Il presente prospetto costituisce estratto del Libro Unico del Lavoro ai sensi del D.L. 112/2008. Eventuali contestazioni vanno comunicate all'ufficio personale entro trenta giorni dalla consegna.", left=True)
    return d.save()


# ================================================================================================ F24
def make_f24(path: Path, pay_date: str, month_ref: str, month_code: str, rows_erario: List[tuple], inps: float, reg: float, com: float) -> Path:
    d = Doc(path, "Modello F24 - ricevuta di pagamento", f"{CO['name']}", f"Delega F24 del {pay_date}")
    W = _width(d)
    d.title_block("MODELLO DI PAGAMENTO UNIFICATO F24", f"Ricevuta di pagamento della delega, versamento del {pay_date}")
    d.H1("CONTRIBUENTE")
    d.table([["Codice fiscale", CO["vat"]], ["Cognome, denominazione o ragione sociale", CO["name"]], ["Domicilio fiscale", f"{CO['street']}, {CO['zip']} {CO['city'].title()} ({CO['prov']})"],
             ["Tipo di delega", "Telematica - home banking, addebito su conto corrente"], ["Esito dell'operazione", "Delega eseguita"], ["Banca di addebito", "Istituto di credito (dati di prova) - ABI 03069 CAB 01000"],
             ["Identificativo operazione", f"F24-{pay_date[-4:]}{pay_date[3:5]}{pay_date[:2]}-0047831"]], [70, W - 70], head=False, align_right_from=9, zebra=True)
    d.H1("SEZIONE ERARIO")
    tab = [["Codice tributo", "Rateazione / mese rif.", "Anno di riferimento", "Importi a debito versati", "Importi a credito compensati"]]
    deb = cred = 0.0
    for code, period, year, debit, credit in rows_erario:
        tab.append([code, period, year, cents(debit) if debit else "", cents(credit) if credit else ""])
        deb += debit
        cred += credit
    d.table(tab, [28, 36, 34, W - 140, 42], align_right_from=3)
    d.small("1001 = ritenute su retribuzioni, pensioni, trasferte; 1040 = ritenute su redditi di lavoro autonomo e provvigioni; 6008 = IVA mensile (versamento di agosto); 6938 = credito d'imposta ricerca e sviluppo (art. 1 c. 198 L. 160/2019).")
    d.table([["Totale A (debito)", cents(deb)], ["Totale B (credito)", cents(cred)]], [W - 40, 40], head=False)
    d.H1("SEZIONE INPS")
    d.table([["Codice sede", "Causale contributo", "Matricola INPS / codice INPS / filiale azienda", "Periodo di riferimento (da - a)", "Importi a debito versati"],
             ["0100", "DM10", "0123456789", f"{month_code} - {month_code}", cents(inps)]], [26, 32, 62, 34, W - 154], align_right_from=4)
    d.small("DM10 = contributi previdenziali e assistenziali per i lavoratori dipendenti, quota a carico del datore di lavoro e del lavoratore.")
    d.H1("SEZIONE REGIONI ED ENTI LOCALI")
    d.table([["Codice tributo", "Codice regione / ente", "Anno di riferimento", "Importi a debito versati"], ["3802", "01", "2026", cents(reg)], ["3848", "L219", "2026", cents(com)]], [34, 50, 38, W - 122], align_right_from=3)
    d.small("3802 = addizionale regionale IRPEF trattenuta dal sostituto d'imposta; 3848 = addizionale comunale IRPEF trattenuta dal sostituto.")
    total_debit = deb + inps + reg + com
    d.H1("SALDO FINALE")
    d.table([["Totale C (debiti sezioni erario, INPS, regioni)", cents(total_debit)], ["Totale D (crediti compensati)", cents(cred)], ["SALDO FINALE (C - D)", cents(total_debit - cred)]], [W - 40, 40], head=False, bold_rows=[2])
    d.P(f"Mese di riferimento dei versamenti: {month_ref}. Il presente documento è la ricevuta telematica della delega e ha valore di quietanza di pagamento.", left=True)
    return d.save()


# ================================================================================================ bozza di candidatura
def make_draft(path: Path) -> Path:
    d = Doc(path, "Progetto Atlas - domanda di contributo (bozza)", f"{CO['name']}", "Progetto Atlas - bozza interna di candidatura")
    W = _width(d)
    d.title_block("PROGETTO ATLAS - DOMANDA DI CONTRIBUTO", "Piattaforma di analisi predittiva dei costi e degli incentivi per le PMI - bozza interna di candidatura, versione 0.7")
    d.H1("1. DATI DEL PROPONENTE")
    d.table([["Denominazione", CO["name"]], ["Forma giuridica", CO["legal_form"]], ["Sede legale", f"{CO['street']}, {CO['zip']} {CO['city'].title()} ({CO['prov']})"], ["Partita IVA", CO["vat"]],
             ["Codice ATECO", f"{CO['ateco']} - {CO['ateco_desc']}"], ["Dimensione d'impresa", "Piccola impresa (17 addetti; fatturato 2025 superiore a 1,5 milioni di euro, inferiore a 10 milioni)"],
             ["Legale rappresentante", "Giulia Ferraris"], ["Referente di progetto", "Matteo Gallo, responsabile sviluppo"], ["Durata del progetto", "12 mesi dalla data di avvio"]], [50, W - 50], head=False, align_right_from=9, zebra=True)
    d.H1("2. SINTESI DEL PROGETTO")
    d.P("Atlas è una piattaforma web che aiuta le piccole e medie imprese a prevedere i propri costi dell'anno successivo e a individuare, tra gli incentivi pubblici aperti, quelli che possono finanziarli. Il progetto sviluppa un prototipo di motore di calcolo "
        "che parte dai bilanci dell'impresa, stima le spese per categoria e le confronta con le regole dei bandi (spese ammissibili, intensità di aiuto, tetti), restituendo per ciascun bando l'importo teorico recuperabile e le voci da adeguare. "
        "L'innovazione sta nel trattare le regole dei bandi come dati strutturati, applicati con un calcolo deterministico e riproducibile, e nel verificare il risultato su un campione di imprese reali.")
    d.H1("3. OBIETTIVI E STATO DELL'ARTE")
    d.B(["Obiettivo 1: realizzare un prototipo funzionante entro il mese 8, con almeno 40 bandi modellati.", "Obiettivo 2: validare il motore su 15 imprese pilota entro il mese 11, confrontando le stime con le spese effettive.",
         "Obiettivo 3: rilasciare la versione commerciale entro il mese 12 con documentazione per studi professionali e associazioni di categoria."])
    d.P("Allo stato dell'arte, la ricerca degli incentivi è affidata a consulenti o a portali di aggregazione che segnalano i bandi senza quantificarne l'effetto sul bilancio dell'impresa. Gli strumenti di pianificazione finanziaria, d'altra parte, non conoscono le regole dei bandi. "
        "Atlas colma la distanza tra i due mondi con un modello di calcolo trasparente: ogni numero è ricondotto alla regola e al documento da cui deriva.")
    d.H1("4. ATTIVITA' E PACCHETTI DI LAVORO")
    d.table([["Pacchetto", "Titolo", "Mesi", "Responsabile", "Descrizione sintetica"],
             ["WP1", "Analisi e progettazione", "1-3", "M. Gallo", "Requisiti, modello dei dati, architettura, scelta dei bandi pilota"],
             ["WP2", "Sviluppo del prototipo", "4-8", "A. Bertone", "Motore di stima, modello delle regole, interfaccia"],
             ["WP3", "Sperimentazione con le imprese pilota", "9-11", "F. Conti", "Test su 15 imprese, confronto stime/spese, correzioni"],
             ["WP4", "Rilascio e diffusione", "12", "V. Rossetti", "Documentazione, formazione, rilascio commerciale"]], [18, 46, 14, 26, W - 104], align_right_from=9)
    d.H1("5. CRONOPROGRAMMA")
    d.table([["Attività"] + [f"M{k}" for k in range(1, 13)], ["WP1"] + ["■" if k <= 3 else "" for k in range(1, 13)], ["WP2"] + ["■" if 4 <= k <= 8 else "" for k in range(1, 13)],
             ["WP3"] + ["■" if 9 <= k <= 11 else "" for k in range(1, 13)], ["WP4"] + ["■" if k == 12 else "" for k in range(1, 13)]], [22] + [(W - 22) / 12] * 12, align_right_from=1)
    d.H1("6. GRUPPO DI LAVORO")
    d.table([["Ruolo nel progetto", "Livello CCNL", "Quota di tempo", "Mesi"], ["Responsabile di progetto", "1", "40%", "12"], ["Sviluppatore senior (2)", "3", "55%", "9"], ["Data scientist", "3", "70%", "9"],
             ["Sviluppatore (2)", "4", "50%", "8"], ["Project manager", "2", "30%", "12"], ["UX designer", "4", "25%", "6"]], [W - 90, 30, 30, 30], align_right_from=1)
    d.H1("7. PIANO DEI COSTI")
    lines = [("Personale di progetto (6 persone, quota di tempo media 45%)", 168000), ("Consulenze specialistiche di data science", 36000),
             ("Licenze software e servizi cloud per lo sviluppo", 24000), ("Attrezzature informatiche e macchinari per il laboratorio dati", 28500),
             ("Spese di formazione del personale sui nuovi strumenti", 9000), ("Spese generali di progetto (affitto e utenze quota progetto)", 22400)]
    d.table([["Voce di spesa", "Importo (euro)"]] + [[a, cents(b)] for a, b in lines] + [[f"TOTALE COSTI PROGETTO", cents(sum(b for _, b in lines))]], [W - 40, 40], bold_rows=[len(lines) + 1])
    d.P("I costi sono stimati sui prezzi di mercato e sui costi del personale dell'ultimo bilancio; le spese generali sono calcolate in modo forfettario sul costo del personale. Le consulenze saranno affidate dopo confronto tra almeno tre preventivi.", left=True)
    d.H1("8. COPERTURA FINANZIARIA")
    d.table([["Fonte", "Importo (euro)", "Quota"], ["Contributo richiesto (intensità 50%)", cents(143950), "50%"], ["Cofinanziamento con risorse proprie", cents(143950), "50%"], ["Totale", cents(287900), "100%"]], [W - 70, 40, 30], bold_rows=[3])
    d.H1("9. RISULTATI ATTESI E INDICATORI")
    d.B(["Almeno 15 imprese pilota coinvolte; riduzione stimata del 20% del tempo dedicato alla ricerca degli incentivi.", "Scostamento tra stima e spesa effettiva inferiore al 10% sulle categorie di costo principali.",
         "Almeno 40 bandi modellati e verificabili alla fonte; 3 accordi con studi professionali per l'uso commerciale."])
    d.H1("10. RISCHI E MITIGAZIONI")
    d.table([["Rischio", "Probabilità", "Mitigazione"], ["Cambio delle regole di un bando durante il progetto", "Media", "Modello dei dati versionato e aggiornamento delle regole a ogni nuova pubblicazione"],
             ["Difficoltà a reclutare imprese pilota", "Bassa", "Accordo preliminare con due associazioni di categoria"], ["Ritardo nello sviluppo del motore di stima", "Media", "Rilascio incrementale per famiglie di bandi"]], [60, 24, W - 84], align_right_from=9)
    d.H1("11. DICHIARAZIONI")
    d.P("Il legale rappresentante dichiara che i dati contenuti nella presente bozza sono veritieri, che l'impresa non è in difficoltà ai sensi della normativa europea sugli aiuti di Stato e che non ha ricevuto altri contributi per le stesse spese. La versione definitiva sarà firmata digitalmente.", left=True)
    L.extend_draft(d)
    L.more_draft(d)
    DM.draft_more(d)
    EXT.draft_ext(d)
    return d.save()


# ================================================================================================ DURC
def make_durc(path: Path) -> Path:
    d = Doc(path, "Documento Unico di Regolarità Contributiva (DURC)", "INPS - INAIL - Casse Edili", "DURC On Line - esito regolare")
    W = _width(d)
    d.title_block("DOCUMENTO UNICO DI REGOLARITA' CONTRIBUTIVA", "DURC On Line - Istituto Nazionale Previdenza Sociale / Istituto Nazionale Assicurazione Infortuni sul Lavoro")
    d.table([["Numero protocollo", "INAIL_48217763"], ["Data richiesta", "01/09/2026"], ["Data emissione", "01/09/2026"], ["Scadenza validità", "29/12/2026 (120 giorni dalla data di emissione)"],
             ["Tipo di richiesta", "Verifica di regolarità contributiva a richiesta dell'impresa (finanziamenti e agevolazioni pubbliche)"]], [58, W - 58], head=False, align_right_from=9, zebra=True)
    d.H1("DATI DELL'IMPRESA")
    d.table([["Denominazione", CO["name"]], ["Codice fiscale", CO["vat"]], ["Sede legale", f"{CO['street']}, {CO['zip']} {CO['city'].title()} ({CO['prov']})"], ["Matricola INPS", "0123456789"],
             ["Codice ditta INAIL / posizioni assicurative", "9876543 - PAT 9876543/21"], ["CCNL applicato", "Commercio, Terziario Distribuzione e Servizi"], ["Dimensione aziendale", "Da 6 a 15 addetti"],
             ["Settore", "Servizi - produzione di software"], ["Lavoratori dipendenti in forza", "15"]], [58, W - 58], head=False, align_right_from=9, zebra=True)
    d.H1("ESITO DELLA VERIFICA")
    d.P("<b>Il documento risulta REGOLARE nei confronti di INPS e INAIL alla data della verifica.</b> Per l'impresa non sussistono inadempienze accertate né versamenti omessi per i periodi contributivi esaminati.", left=True)
    d.table([["Ente", "Esito", "Periodo verificato"], ["INPS", "Regolare", "Ultimi 12 mesi, fino al 31/07/2026"], ["INAIL", "Regolare", "Ultimi 12 mesi, fino al 31/07/2026"], ["Cassa Edile", "Non applicabile", "-"]], [46, 46, W - 92], align_right_from=9)
    d.H1("AVVERTENZE")
    d.B(["Il presente documento ha validità di 120 giorni dalla data di emissione e può essere utilizzato per le finalità indicate nella richiesta.", "L'esito è riferito alla data della verifica; il datore di lavoro è tenuto a comunicare variazioni successive.",
         "La verifica è stata effettuata sulla base dei dati dichiarati e dei versamenti registrati dagli enti previdenziali; non sostituisce i controlli di competenza delle amministrazioni procedenti."])
    L.extend_durc(d)
    DM.durc_more(d)
    EXT.durc_ext(d)
    return d.save()


# ================================================================================================ dichiarazione de minimis
def make_de_minimis(path: Path) -> Path:
    d = Doc(path, "Dichiarazione aiuti de minimis", f"{CO['name']}", "Dichiarazione sostitutiva - aiuti de minimis")
    W = _width(d)
    d.title_block("DICHIARAZIONE SOSTITUTIVA DI ATTO DI NOTORIETA' - AIUTI 'DE MINIMIS'", "Regolamento (UE) 2023/2831 della Commissione del 13 dicembre 2023 - triennio 2024-2026")
    d.P(f"Il sottoscritto Giulia FERRARIS, codice fiscale {P.BY_ID['M001']['cf']}, nato a Torino il 18/02/1981, in qualità di legale rappresentante di {CO['name']}, con sede in {CO['city'].title()}, {CO['street']}, codice fiscale e partita IVA {CO['vat']}, "
        "ai sensi degli articoli 46 e 47 del D.P.R. 28 dicembre 2000, n. 445, consapevole delle sanzioni penali previste dall'art. 76 dello stesso decreto in caso di dichiarazioni mendaci, formazione o uso di atti falsi,")
    d.H1("DICHIARA")
    d.B(["che l'impresa rappresentata <b>non è collegata</b> ad altre imprese, direttamente o indirettamente, ai sensi dell'art. 3, paragrafo 2, del regolamento (UE) 2023/2831, e costituisce pertanto da sola una «impresa unica»;",
         "che, nell'esercizio finanziario in corso e nei due esercizi finanziari precedenti (2024, 2025 e 2026), l'impresa ha ricevuto gli aiuti in regime «de minimis» di seguito elencati, e non altri;",
         "che l'impresa non rientra tra le esclusioni previste dall'art. 1 del regolamento (settori della pesca e dell'acquacoltura, della produzione primaria di prodotti agricoli, attività connesse all'esportazione)."])
    d.H1("AIUTI 'DE MINIMIS' RICEVUTI NEL TRIENNIO")
    d.table([["Ente concedente", "Misura", "Riferimento normativo", "Data concessione", "Importo (euro)", "Codice COR"],
             ["Camera di Commercio di Torino", "Voucher per la digitalizzazione delle PMI", "Reg. UE 2023/2831", "12/04/2024", cents(10000), "COR-0000001"],
             ["Regione Piemonte", "Contributo per la partecipazione a fiere", "Reg. UE 2023/2831", "03/10/2025", cents(6500), "COR-0000002"],
             ["TOTALE AIUTI NEL TRIENNIO", "", "", "", cents(16500), ""]], [38, 44, 28, 24, 24, W - 158], bold_rows=[3], align_right_from=4)
    d.H1("VERIFICA DEL MASSIMALE")
    d.table([["Massimale applicabile a un'impresa unica nell'arco di tre esercizi finanziari", cents(300000)], ["Aiuti già ricevuti nel triennio", cents(16500)], ["Margine residuo dichiarato", cents(283500)]],
            [W - 40, 40], head=False, bold_rows=[2])
    d.P("Il credito d'imposta per attività di ricerca e sviluppo (art. 1, commi 198-206, L. 160/2019) è un aiuto in regime di esenzione generale per categoria e non concorre al massimale de minimis. Il dichiarante si impegna a comunicare tempestivamente "
        "ogni ulteriore aiuto «de minimis» ricevuto fino alla data di concessione dell'agevolazione richiesta, e autorizza il trattamento dei dati personali ai sensi del regolamento (UE) 2016/679 per le finalità del procedimento.", left=True)
    d.P("Luogo e data: Torino, 02/10/2026. Il legale rappresentante: Giulia Ferraris (firma digitale apposta sul file originale).", left=True)
    L.extend_de_minimis(d)
    DM.deminimis_more(d)
    EXT.deminimis_ext(d)
    return d.save()


# ================================================================================================ business plan
def make_business_plan(path: Path) -> Path:
    from . import bp_build
    return bp_build.make_business_plan(path)


# ================================================================================================ fogli Excel
def make_xlsx_aiuti(path: Path) -> Path:
    from . import xlsx_pack
    return xlsx_pack.aiuti(path)


def make_xlsx_organico(path: Path) -> Path:
    from . import xlsx_pack
    return xlsx_pack.organico(path)


def make_xlsx_cespiti(path: Path) -> Path:
    from . import xlsx_pack
    return xlsx_pack.cespiti(path)
