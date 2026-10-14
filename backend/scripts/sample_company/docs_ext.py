"""Ultimo strato di approfondimento: domanda di contributo (stato dell'arte, architettura, KPI, giustificazione di spesa, curricula), visura (cariche, soci, atti depositati, bilanci), DURC e de minimis."""
from __future__ import annotations

from datetime import date

from . import ledger as LG
from . import model as M
from . import people as P
from .pdfkit import Doc, cents, pct, units

U = units


def _w(d: Doc) -> float:
    return d.width / 2.8346


# ================================================================================================ domanda di contributo
def draft_ext(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.title_block("PARTE TERZA - APPROFONDIMENTI TECNICI, ECONOMICI E ORGANIZZATIVI")
    d.H1("37. STATO DELL'ARTE E POSIZIONAMENTO RISPETTO ALLE SOLUZIONI ESISTENTI")
    d.P("Sono state analizzate venti soluzioni disponibili sul mercato italiano ed europeo, in quattro categorie: portali di segnalazione dei bandi, software di pianificazione finanziaria, strumenti di consulenza assistita e motori di regole generici. "
        "Per ciascuna sono stati verificati la capacità di leggere il bilancio dell'impresa, di applicare le regole di ogni bando, di dimostrare la fonte di ogni numero, di garantire un risultato identico a parità di dati e di gestire cumulo e limiti di aiuto.")
    d.table([["Categoria", "Prodotti", "Legge il bilancio", "Applica le regole", "Fonte di ogni regola", "Risultato riproducibile", "Cumulo e limiti"], ["Portali di segnalazione bandi", "7", "No", "No", "In parte", "-", "No"], ["Pianificazione finanziaria per PMI", "6", "Sì", "No", "No", "Sì", "No"],
             ["Consulenza assistita", "4", "Parziale", "Manuale", "No", "No", "Manuale"], ["Motori di regole generici", "3", "No", "Sì", "No", "Sì", "Sì, da configurare"], ["Piattaforma proposta (Atlas)", "1", "Sì", "Sì", "Sì", "Sì", "Sì"]],
            [46, 14, 24, 24, 26, 28, W - 162], align_right_from=9, font=7.4, zebra=True)
    d.P("Il vantaggio competitivo non è l'elenco dei bandi, già disponibile altrove, ma la combinazione di tre elementi mai riuniti in un unico strumento: la lettura dei documenti contabili dell'impresa, la rappresentazione formale delle regole e la prova della provenienza di ogni numero.", left=True)
    d.H1("38. ARCHITETTURA TECNICA DELLA PIATTAFORMA")
    d.table([["Livello", "Componente", "Tecnologia", "Funzione", "Requisito di sicurezza"], ["Presentazione", "Interfaccia web", "Applicazione a pagina singola con rendering lato client", "Prospetti, grafici e conferme guidate dell'utente", "Sessioni con scadenza e protezione dagli attacchi sui moduli"],
             ["Applicazione", "Servizio di calcolo", "Servizio web asincrono in linguaggio Python", "Ripartizione ottimale dei costi tra bandi e controllo del cumulo", "Aritmetica decimale, nessun numero a virgola mobile"], ["Acquisizione", "Lettura documenti", "Estrazione del testo con riconoscimento ottico dei caratteri", "Bilanci, F24, buste paga, visure", "Isolamento dei file caricati, limite di dimensione e di pagine"],
             ["Dati", "Archivio relazionale", "Database relazionale gestito, regione europea", "Pratiche, regole versionate, esecuzioni", "Cifratura a riposo, backup giornalieri, accesso per ruolo"], ["Tracciabilità", "Registro firmato", "Catena di impronte con firma", "Prova delle esecuzioni e delle fonti", "Verifica indipendente dell'integrità"], ["Monitoraggio", "Controlli e avvisi", "Registri strutturati e avvisi automatici", "Errori di lettura, scostamenti, scadenze dei bandi", "Nessun dato personale nei registri"]],
            [24, 26, 38, W - 150, 62], align_right_from=9, font=7.4, zebra=True)
    d.H2("Flusso dei dati")
    d.B(["<b>1. Caricamento.</b> Lo studio carica i documenti dell'impresa cliente (bilanci, F24, buste paga, visura, registro degli aiuti).", "<b>2. Lettura.</b> Il modulo di acquisizione estrae le voci e assegna a ciascuna un livello di affidabilità; le voci incerte sono mostrate all'utente per la conferma.",
         "<b>3. Profilo.</b> Le voci confermate costruiscono il profilo dell'impresa: dimensione, settore, dipendenti, costi per categoria, aiuti già ricevuti.", "<b>4. Previsione.</b> Il modello stima i costi dell'anno successivo con ipotesi esplicite e intervalli.",
         "<b>5. Abbinamento.</b> Il motore confronta il profilo con le regole dei bandi e calcola l'ammissibilità di ogni spesa.", "<b>6. Ripartizione.</b> Un solutore ottimizza l'uso dei fondi nel rispetto di tetti, cumulo e divieto di doppio finanziamento.",
         "<b>7. Prospetto.</b> L'utente ottiene il prospetto con la fonte di ogni numero e lo scarica come PDF o foglio di calcolo."])
    d.H1("39. INDICATORI DI RISULTATO DEL PROGETTO (KPI)")
    kp = [("Scostamento medio tra stima e importo ammesso", "Differenza percentuale media su 15 imprese", "24%", "< 10%", "Fine WP3"), ("Tempo di analisi per cliente", "Ore dall'upload alla mappa dei bandi", "3 ore a trimestre", "< 20 minuti", "Fine WP3"), ("Voci contabili lette senza intervento", "Quota di voci con affidabilità alta", "-", ">= 85%", "Fine WP2"),
          ("Bandi codificati e verificati", "Numero di bandi con regole complete e fonte", "0", "40", "Fine WP2"), ("Riproducibilità dei calcoli", "Esecuzioni ripetute con risultato identico", "-", "100%", "Fine WP2"), ("Studi professionali formati", "Numero di studi con utenti abilitati", "0", "2", "Fine WP4"),
          ("Imprese pilota coinvolte", "Imprese che completano la sperimentazione", "0", "15", "Fine WP3"), ("Soddisfazione degli utenti", "Punteggio medio da 1 a 5", "-", ">= 4,2", "Fine WP4")]
    d.table([["Indicatore", "Definizione", "Situazione di partenza", "Obiettivo", "Verifica"]] + [list(k) for k in kp], [50, W - 130, 30, 22, 28], align_right_from=9, font=7.6, zebra=True)
    d.H1("40. GIUSTIFICAZIONE DELLE SPESE PER VOCE")
    d.table([["Voce", "Importo (euro)", "Giustificazione", "Criterio di congruità"], ["Personale", cents(168000), "Otto persone con competenze di sviluppo, dati e gestione di progetto, impiegate dal quarto mese per tre quarti del tempo", "Costo orario da busta paga e libro unico, fogli di presenza mensili"],
             ["Consulenze specialistiche", cents(36000), "Validazione statistica del modello, revisione dell'architettura di sicurezza e test di penetrazione", "Tre preventivi per voce, scelta del migliore rapporto qualità/prezzo"], ["Licenze e cloud", cents(24000), "Strumenti di sviluppo, ambienti di test e servizi in regione europea per dodici mesi", "Offerte comparate, contratti annuali"],
             ["Attrezzature", cents(28500), "Server di calcolo, dispositivi di test, apparati di rete del laboratorio per la quota di utilizzo nel progetto", "Ammortamento ordinario sulla quota di utilizzo"], ["Formazione", cents(9000), "Corsi specialistici sull'ottimizzazione e sulla sicurezza per il gruppo di lavoro", "Docenti certificati, preventivi comparati"],
             ["Spese generali", cents(22400), "Forfait del 10% sul totale delle spese dirette ammissibili, come previsto dall'avviso", "Forfait da bando"], ["Totale", cents(287900), "", ""]], [34, 30, W - 128, 64], bold_rows=[7], align_right_from=1, font=7.4, zebra=True)
    d.H1("41. GRUPPO DI LAVORO: SCHEDE DI SINTESI")
    team = [("M001", "Responsabile scientifico e legale rappresentante", "Direzione, rapporti con gli studi pilota", 10), ("M002", "Responsabile di progetto", "Coordinamento tecnico e architettura", 40), ("M003", "Sviluppatore senior", "Motore di calcolo e solutore", 55), ("M004", "Sviluppatore senior", "Modulo di acquisizione dei documenti", 55),
            ("M014", "Data scientist", "Modello di previsione dei costi e validazione", 70), ("M005", "Sviluppatore", "Interfaccia e prospetti", 50), ("M007", "Sviluppatore", "Archivio delle regole e test automatici", 50), ("M008", "Project manager", "Pianificazione, rendicontazione e rapporti con le pilota", 30), ("M012", "UX designer", "Progettazione dell'esperienza utente", 25)]
    rows = [["Matricola", "Nome", "Ruolo nel progetto", "Attività", "Impegno", "Assunzione"]]
    for eid, role, act, q in team:
        e = P.BY_ID[eid]
        rows.append([eid, f"{e['name']} {e['surname']}", role, act, f"{q}%", e["hired"][8:] + "/" + e["hired"][5:7] + "/" + e["hired"][:4]])
    d.table(rows, [18, 34, 42, W - 156, 16, 26], align_right_from=9, font=7.4, zebra=True)
    d.H2("Esperienze del gruppo")
    for eid, role, act, q in team[:6]:
        e = P.BY_ID[eid]
        d.P(f"<b>{e['name']} {e['surname']}</b> ({role}, livello {e['level']}). Assunto il {e['hired'][8:]}/{e['hired'][5:7]}/{e['hired'][:4]}, ha contribuito ai progetti di sviluppo di Meridiana Digital Solutions nell'ambito dell'analisi dei dati e dell'ingegneria del software, "
            f"con responsabilità su {act.lower()}. Nel progetto sarà impegnato per il {q}% del proprio tempo secondo il cronoprogramma di cui al paragrafo 26.")
    d.H1("42. PROPRIETA' INTELLETTUALE E CONDIZIONI DI UTILIZZO DEI RISULTATI")
    d.B(["I risultati del progetto sono di proprietà esclusiva del beneficiario e non sono ceduti a terzi per almeno cinque anni.", "Il codice sorgente non è reso pubblico; i risultati della sperimentazione sono diffusi in forma aggregata e anonima.",
         "Le regole dei bandi, tratte da fonti pubbliche, sono conservate con l'indicazione della fonte e della data di consultazione.", "Il marchio ATLAS è depositato in Italia e in corso di esame presso l'Ufficio dell'Unione europea.",
         "Nessun dipendente o collaboratore ha diritti sul codice sviluppato: i contratti prevedono la cessione dei diritti di utilizzazione economica."])
    d.H1("43. SOSTENIBILITA' DEL PROGETTO DOPO IL FINANZIAMENTO")
    rows = [["Anno", "Studi attivi", "Canone medio annuo per studio (euro)", "Ricavi del prodotto (euro)", "Costi diretti (euro)", "Margine (euro)"]]
    for k, (n, c, cost) in enumerate(((6, 4800, 64000), (14, 5200, 96000), (28, 5600, 140000), (46, 5900, 188000)), 1):
        rows.append([str(2027 + k - 1), str(n), U(c), U(n * c), U(cost), U(n * c - cost)])
    d.table(rows, [16, 22, 46, 34, 32, W - 150], align_right_from=1, font=8, zebra=True)
    d.P("Le ipotesi di diffusione sono prudenziali e sono sostenute dalla disponibilità dichiarata di undici studi su quindici a sottoscrivere un canone; il progetto resta in equilibrio anche con la metà degli studi indicati.", left=True)
    d.H1("44. QUADRO FINANZIARIO COMPLESSIVO DEL PROGETTO")
    d.table([["Fonte di copertura", "Importo (euro)", "Quota"], ["Contributo richiesto a fondo perduto", cents(143950), "50,0%"], ["Risorse proprie (liquidità disponibile)", cents(143950), "50,0%"], ["Totale dei costi di progetto", cents(287900), "100,0%"]], [W - 80, 44, 36], bold_rows=[3], align_right_from=1, font=8)
    d.H1("45. CRONOLOGIA DELLE VERIFICHE E DEI RAPPORTI INTERMEDI")
    d.table([["Data prevista", "Verifica", "Evidenza", "Responsabile"], ["Mese 3", "Chiusura WP1", "Documento dei requisiti approvato", "M. Gallo"], ["Mese 6", "Stato di avanzamento", "Rapporto intermedio e primi 20 bandi codificati", "F. Conti"], ["Mese 8", "Chiusura WP2", "Prototipo rilasciato agli utenti pilota", "M. Gallo"],
             ["Mese 11", "Chiusura WP3", "Rapporto di validazione sulle 15 imprese", "F. Greco"], ["Mese 12", "Rendicontazione finale", "Fogli di presenza, fatture, rapporto tecnico", "F. Conti"]], [28, 40, W - 106, 38], align_right_from=9, font=8, zebra=True)
    d.small("Bozza interna: dati fittizi di prova.")


# ================================================================================================ visura
def registry_ext(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.title_block("SEZIONE INTEGRATIVA - SOCI, CARICHE, ATTI E BILANCI DEPOSITATI")
    d.H1("ELENCO SOCI E TITOLARI DI DIRITTI SULLE QUOTE")
    d.table([["Socio", "Codice fiscale", "Quota nominale (euro)", "Percentuale", "Diritti reali", "Data di iscrizione"], ["FERRARIS GIULIA", P.BY_ID["M001"]["cf"], "30.000,00", "60%", "Piena proprietà", "14/03/2016"],
             ["BERTOLOTTI MARCO", P.fiscal_code("Bertolotti", "Marco", date(1979, 3, 14), True, "L219"), "20.000,00", "40%", "Piena proprietà", "14/03/2016"]], [34, 40, 26, 18, 28, W - 146], align_right_from=9, font=8)
    d.H1("CARICHE ATTUALMENTE VIGENTI")
    d.table([["Persona", "Carica", "Data nomina", "Durata", "Poteri"], ["FERRARIS GIULIA", "Amministratore unico e legale rappresentante", "14/03/2016", "A tempo indeterminato", "Ordinaria e straordinaria amministrazione, firma singola"], ["GALLO MATTEO", "Procuratore", "15/03/2023", "Fino a revoca", "Contratti di sviluppo software fino a 150.000 euro"],
             ["FONTANA PAOLA", "Procuratore", "20/11/2023", "Fino a revoca", "Operazioni bancarie ordinarie fino a 25.000 euro"]], [30, 46, 22, 28, W - 126], align_right_from=9, font=7.8, zebra=True)
    d.H1("CARICHE CESSATE")
    d.table([["Persona", "Carica", "Dal", "Al", "Motivo"], ["Procuratore dipendente (2018)", "Procuratore per contratti di sviluppo", "04/12/2018", "15/03/2023", "Sostituzione con nuova procura"], ["Consulente DPO esterno", "Responsabile della protezione dei dati", "25/05/2018", "in corso", "Non soggetto a iscrizione"]], [40, 50, 22, 22, W - 134], align_right_from=9, font=7.8)
    d.H1("ATTI E BILANCI DEPOSITATI PRESSO IL REGISTRO DELLE IMPRESE")
    rows = [["Anno", "Tipo di atto", "Data di deposito", "Protocollo", "Stato"]]
    for y in (2021, 2022, 2023, 2024, 2025):
        rows.append([str(y), "Bilancio d'esercizio con nota integrativa e relazione sulla gestione", f"{15 + (y % 4):02d}/05/{y + 1}", f"TO-{y + 1}-00{4410 + y % 100}", "Depositato"])
    rows += [["2021", "Verbale di assemblea straordinaria (aumento di capitale)", "07/05/2021", "TO-2021-0031558", "Iscritto"], ["2019", "Variazione della sede legale", "08/01/2020", "TO-2020-0002214", "Iscritto"], ["2021", "Comunicazione di apertura dell'unità locale", "06/09/2021", "TO-2021-0049870", "Iscritto"]]
    d.table(rows, [14, W - 100, 26, 34, 26], align_right_from=9, font=7.6, zebra=True)
    d.H1("DIMENSIONE DELL'IMPRESA E INDICATORI DI MERCATO")
    b = M.balance(2025)
    p = M.pl(2025)
    d.table([["Parametro", "Valore", "Soglia PMI (Racc. 2003/361/CE)", "Esito"], ["Organico medio dell'esercizio 2025", str(M.EMPLOYEES[2025]), "< 50 (piccola impresa)", "Piccola impresa"], ["Fatturato annuo 2025 (euro)", U(p["revenue"]), "<= 10.000.000", "Rispettata"], ["Totale di bilancio 2025 (euro)", U(b["assets"]), "<= 10.000.000", "Rispettata"],
             ["Indipendenza", "Nessuna partecipazione di imprese superiori al 25%", "Autonoma", "Impresa autonoma"]], [50, 40, 50, W - 140], align_right_from=9, font=7.8, zebra=True)
    d.H1("ESTRATTO DEGLI AGGIORNAMENTI RECENTI")
    d.table([["Data", "Tipo di pratica", "Esito"], ["02/10/2026", "Verifica periodica della posizione (a richiesta)", "Positiva"], ["18/09/2026", "Comunicazione dell'indirizzo di posta elettronica certificata", "Registrata"], ["22/07/2025", "Deposito di marchio dell'Unione europea (informazione camerale)", "Registrata"],
             ["11/03/2024", "Aggiunta dell'attività 63.11.19", "Iscritta"]], [30, W - 70, 40], align_right_from=9, font=8, zebra=True)
    d.small("Estratto di prova: tutti i dati sono fittizi.")


# ================================================================================================ DURC
def durc_ext(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.H1("POSIZIONI CONTRIBUTIVE ATTIVE")
    d.table([["Ente", "Posizione", "Matricola / codice ditta", "Stato", "Ultimo controllo"], ["INPS", "Contribuente aziende con dipendenti", "5412398760", "Attiva e regolare", "01/09/2026"], ["INAIL", "Codice ditta, voce di tariffa 0722 (programmazione e consulenza informatica)", "42318796", "Attiva e regolare", "01/09/2026"],
             ["Cassa edile", "Non applicabile", "-", "-", "-"], ["Fondimpresa", "Fondo interprofessionale", "FIM-0097415", "Adesione attiva", "14/09/2023"]], [24, W - 120, 32, 34, 30], align_right_from=9, font=7.8, zebra=True)
    d.H1("RETRIBUZIONI IMPONIBILI E CONTRIBUTI PER CATEGORIA (ANNO 2025)")
    sal = M.acct("Salari e stipendi", 2025)
    ons = M.acct("Oneri sociali", 2025)
    parts = LG.alloc(ons, [60.5, 15.3, 8.0, 7.6, 4.8, 3.8])
    rows = [["Contribuzione", "Aliquota media", "Imponibile (euro)", "Importo (euro)"]]
    for (n, a), v in zip((("Fondo pensioni lavoratori dipendenti", "23,81%"), ("Assegni familiari e prestazioni temporanee", "5,91%"), ("Maternità e disoccupazione", "3,10%"), ("Tutela infortuni (INAIL)", "0,89%"), ("Contributo di solidarietà e fondi bilaterali", "1,86%"), ("Altri contributi e fondi", "1,47%")), parts):
        rows.append([n, a, U(sal), U(v)])
    rows.append(["Totale", "", "", U(ons)])
    d.table(rows, [W - 108, 28, 40, 40], bold_rows=[7], align_right_from=1, font=8, zebra=True)
    d.H1("DICHIARAZIONI DEL DATORE DI LAVORO")
    d.B(["Il datore di lavoro applica il contratto collettivo nazionale del commercio, dei servizi e del terziario avanzato e rispetta gli obblighi retributivi e contributivi.", "Non sono in corso rateizzazioni dei debiti contributivi né contenziosi amministrativi.",
         "Le assunzioni con apprendistato sono comunicate al centro per l'impiego nei termini e registrate nel libro unico del lavoro.", "I tirocini e le collaborazioni sono assenti nel periodo considerato."])
    d.small("Documento di prova.")


# ================================================================================================ de minimis
def deminimis_ext(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.H1("VERIFICA DELL'IMPRESA UNICA (ART. 2, PAR. 2, REG. UE 2023/2831)")
    d.table([["Criterio", "Verifica", "Esito"], ["Un'impresa detiene la maggioranza dei diritti di voto di un'altra", "Nessuna partecipazione societaria", "Non ricorre"], ["Un'impresa ha il diritto di nominare o revocare la maggioranza dell'organo amministrativo di un'altra", "Nessun accordo", "Non ricorre"],
             ["Un'impresa ha il diritto di esercitare un'influenza dominante in virtù di un contratto o di una clausola statutaria", "Nessun contratto o clausola", "Non ricorre"], ["Un'impresa controlla da sola la maggioranza dei diritti di voto in base a un accordo con altri soci", "Nessun patto parasociale", "Non ricorre"],
             ["Operazioni di fusione, scissione o acquisizione negli ultimi tre esercizi", "Nessuna", "Non ricorre"]], [W - 100, 66, 34], align_right_from=9, font=7.8, zebra=True)
    d.P("Le due persone fisiche socie (60% e 40%) non detengono partecipazioni di controllo in altre imprese con attività nello stesso mercato o in mercati contigui; l'impresa dichiarante costituisce pertanto da sola una «impresa unica» ai fini del massimale.", left=True)
    d.H1("MASSIMALE APPLICABILE E TRIENNIO MOBILE")
    d.table([["Parametro", "Valore"], ["Regolamento", "Reg. (UE) 2023/2831 della Commissione del 13 dicembre 2023"], ["Massimale per impresa unica", cents(300000)], ["Periodo di riferimento", "Tre esercizi finanziari consecutivi mobili"], ["Aiuti ricevuti nel triennio 2024-2026", cents(16500)],
             ["Margine residuo", cents(283500)], ["Registro di controllo", "Registro nazionale degli aiuti di Stato (RNA), visura del 02/10/2026"], ["Esito", "Massimale rispettato"]], [58, W - 58], align_right_from=9, font=8, zebra=True, head=False)
    d.H1("IMPEGNI DEL DICHIARANTE")
    d.B(["Informare l'ente concedente di ogni aiuto de minimis concesso successivamente alla presente dichiarazione e prima della concessione dell'agevolazione richiesta.", "Conservare per dieci anni la documentazione degli aiuti ricevuti.", "Consentire controlli a campione dell'ente e dell'Unione europea.",
         "Restituire gli importi indebitamente percepiti, maggiorati degli interessi, in caso di dichiarazioni non veritiere."])
    d.small("Documento di prova.")
