"""Versioni estese dei documenti lunghi: visura completa, domanda di contributo, business plan, DURC e dichiarazione de minimis (stesso contenuto di ``docs.py``, molto più dettagliato)."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from . import model as M
from . import people as P
from .pdfkit import Doc, cents, pct, units

CO = M.COMPANY
U = units


def _w(d: Doc) -> float:
    return d.width / 2.8346


# ================================================================================================ visura completa
def extend_registry(d: Doc) -> None:
    W = _w(d)
    d.H1("TITOLARI DI CARICHE E QUALIFICHE")
    g = P.BY_ID["M001"]
    d.table([["Dato", "Valore"], ["Cognome e nome", "FERRARIS GIULIA"], ["Codice fiscale", g["cf"]], ["Data e luogo di nascita", "18/02/1981 Torino (TO)"], ["Residenza", "Via Madama Cristina 41, 10125 Torino (TO)"],
             ["Cittadinanza", "Italiana"], ["Carica", "Amministratore unico - legale rappresentante"], ["Data atto di nomina", "29/04/2022"], ["Data presentazione carica", "12/05/2022"],
             ["Durata in carica", "Fino a revoca"], ["Poteri", "Rappresentanza della società di fronte ai terzi e in giudizio; poteri di ordinaria e straordinaria amministrazione con firma singola, esclusa la cessione dell'azienda"]],
            [52, W - 52], align_right_from=9, zebra=True)
    d.H1("PROCURE E POTERI CONFERITI")
    d.table([["Procuratore", "Codice fiscale", "Data conferimento", "Oggetto della procura"],
             ["GALLO MATTEO", P.BY_ID["M002"]["cf"], "15/03/2023", "Sottoscrizione di contratti di sviluppo software e offerte commerciali fino a 150.000 euro per singola operazione"],
             ["FONTANA PAOLA", P.BY_ID["M011"]["cf"], "20/11/2023", "Operazioni bancarie ordinarie e pagamenti fornitori fino a 25.000 euro, firma disgiunta"]], [32, 42, 28, W - 102], align_right_from=9)
    d.H1("SISTEMA DI AMMINISTRAZIONE E CONTROLLO")
    d.table([["Modello di amministrazione", "Amministrazione unipersonale"], ["Organo di controllo", "Non nominato (società al di sotto dei limiti dell'art. 2477 c.c.)"], ["Revisore legale dei conti", "Non nominato"],
             ["Numero amministratori in carica", "1"], ["Collegio sindacale", "Non presente"], ["Organismo di vigilanza (D.Lgs. 231/2001)", "Non nominato"]], [70, W - 70], head=False, align_right_from=9, zebra=True)
    d.H1("PRATICHE E ATTI DEPOSITATI NEL REGISTRO DELLE IMPRESE")
    rows = [["Data deposito", "Protocollo", "Tipo di atto"]]
    rows += [["29/05/2025", "TO-2025-0048213", "Bilancio ordinario d'esercizio al 31/12/2024"], ["12/05/2022", "TO-2022-0036721", "Rinnovo nomina amministratore unico"],
             ["30/05/2024", "TO-2024-0051307", "Bilancio ordinario d'esercizio al 31/12/2023"], ["31/05/2023", "TO-2023-0049880", "Bilancio ordinario d'esercizio al 31/12/2022"],
             ["30/05/2022", "TO-2022-0041095", "Bilancio ordinario d'esercizio al 31/12/2021"], ["03/06/2021", "TO-2021-0044466", "Bilancio ordinario d'esercizio al 31/12/2020"],
             ["07/09/2021", "TO-2021-0071120", "Comunicazione di apertura di unità locale (corso Francia 114)"], ["14/05/2021", "TO-2021-0040732", "Verbale di assemblea straordinaria: aumento di capitale a 50.000 euro"],
             ["14/01/2020", "TO-2020-0003982", "Comunicazione di trasferimento di sede legale"], ["02/06/2020", "TO-2020-0043915", "Bilancio ordinario d'esercizio al 31/12/2019"],
             ["28/05/2019", "TO-2019-0040278", "Bilancio ordinario d'esercizio al 31/12/2018"], ["29/05/2018", "TO-2018-0037120", "Bilancio ordinario d'esercizio al 31/12/2017"],
             ["30/05/2017", "TO-2017-0033841", "Bilancio ordinario d'esercizio al 31/12/2016"], ["21/03/2016", "TO-2016-0022907", "Iscrizione di nuova società al Registro delle Imprese"]]
    d.table(rows, [28, 40, W - 68], align_right_from=9, zebra=True)
    d.H1("INFORMAZIONI DI SINTESI SULL'ATTIVITA'")
    d.table([["Dato", "Valore", "Fonte"], ["Volume d'affari dichiarato (IVA) 2024", U(1318400) + " euro", "Dichiarazione IVA, presentata il 28/04/2025"], ["Numero di unità locali attive", "2", "Registro Imprese"],
             ["Iscrizione all'INPS", "Sì, matricola 0123456789, sede di Torino", "INPS"], ["Iscrizione all'INAIL", "Sì, codice ditta 9876543", "INAIL"], ["Iscrizione alla Camera di Commercio come PMI", "Sì (piccola impresa)", "Dichiarazione dell'impresa"],
             ["Rating di legalità", "Non attribuito", "AGCM"], ["Posta elettronica certificata", CO["pec"], "Indice nazionale PEC (INI-PEC)"]], [64, W - 106, 42], align_right_from=9)
    d.H1("MODIFICHE E VICENDE SOCIETARIE")
    d.P("La società è stata costituita il 14/03/2016 da due soci fondatori con capitale sociale di 10.000 euro interamente versato. Il 29/04/2021 l'assemblea straordinaria ha deliberato l'aumento del capitale sociale a 50.000 euro, mediante utilizzo di riserve di utili per 25.000 euro "
        "e nuovi conferimenti in denaro per 15.000 euro. Non risultano fusioni, scissioni, cessioni di azienda, conferimenti o affitti di azienda. Lo statuto vigente è quello aggiornato in data 29/04/2021, depositato presso il Registro delle Imprese.", left=True)
    d.small("Documento di prova: protocolli, date degli atti e notaio sono inventati. La visura non ha valore di certificato.")


# ================================================================================================ domanda di contributo estesa
def extend_draft(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.H1("12. CONTESTO NORMATIVO E MISURA DI RIFERIMENTO")
    d.P("La presente bozza è predisposta per la candidatura a un bando regionale a sostegno di progetti di ricerca industriale e sviluppo sperimentale delle piccole e medie imprese, che finanzia a fondo perduto una quota delle spese ammissibili. "
        "Il bando richiede un progetto di durata massima di 18 mesi, un investimento ammissibile tra 150.000 e 1.500.000 euro, un'intensità di aiuto fino al 50% per le piccole imprese e la dimostrazione dell'effetto di incentivazione. "
        "Le spese ammissibili comprendono il personale impiegato nel progetto, gli strumenti e le attrezzature per la durata del progetto, le consulenze e i servizi di ricerca contrattuale, le spese generali in misura forfettaria e i costi di formazione specifica.")
    d.H1("13. ARCHITETTURA TECNICA DELLA SOLUZIONE")
    d.P("La piattaforma è composta da quattro moduli. Il <b>modulo di acquisizione</b> legge bilanci e documenti contabili dell'impresa e li trasforma in dati strutturati con indicazione della fonte e del grado di affidabilità; "
        "il <b>modulo delle regole</b> contiene la descrizione strutturata dei bandi (spese ammissibili, intensità, tetti, finestre temporali) con versionamento e tracciabilità del testo da cui ogni regola è ricavata; "
        "il <b>motore di calcolo</b> applica le regole alle spese previste con aritmetica decimale e produce un risultato riproducibile, con una traccia di tutti i passaggi; "
        "il <b>modulo di presentazione</b> espone i risultati agli utenti, con la possibilità di confrontare scenari e di esportare i prospetti.")
    d.table([["Componente", "Tecnologia prevista", "Stato attuale"], ["Acquisizione documenti", "Lettura del testo dei PDF e riconoscimento ottico per le scansioni", "Prototipo interno"], ["Archivio delle regole", "Base dati relazionale con versionamento", "Progettato"],
             ["Motore di calcolo", "Aritmetica decimale, ottimizzazione lineare mista intera per la ripartizione", "Prototipo interno"], ["Interfaccia", "Applicazione web, esportazione in PDF ed Excel", "Da sviluppare"]], [48, W - 98, 50], align_right_from=9)
    d.H1("14. INNOVATIVITA' E STATO DELLA TECNICA")
    d.P("Le soluzioni disponibili sul mercato si dividono in due famiglie: portali che elencano i bandi aperti, senza collegarli ai conti dell'impresa, e software di pianificazione finanziaria, che non conoscono le regole dei bandi. "
        "L'elemento di novità del progetto è la rappresentazione formale delle regole dei bandi, che consente di calcolare in modo ripetibile quanto un bando può finanziare dato un bilancio, e di dimostrare da quale frase del bando discende ogni cifra. "
        "Il rischio tecnico principale è la variabilità del linguaggio dei bandi: il progetto lo affronta con un lavoro di classificazione manuale su un campione di 40 bandi e con la misura dell'accordo tra lettori.")
    d.H1("15. DESCRIZIONE DETTAGLIATA DELLE ATTIVITA'")
    wps = [("WP1 - Analisi e progettazione", "Mesi 1-3", "Raccolta dei requisiti presso cinque imprese e due studi professionali; definizione del modello dei dati delle regole; scelta dei 40 bandi di riferimento; progettazione dell'architettura.", "D1.1 Documento dei requisiti (M2); D1.2 Modello dei dati (M3)"),
           ("WP2 - Sviluppo del prototipo", "Mesi 4-8", "Realizzazione del modulo di acquisizione, dell'archivio delle regole e del motore di calcolo; codifica manuale delle regole dei bandi; test automatici sul motore.", "D2.1 Motore di calcolo (M6); D2.2 Archivio di 40 bandi codificati (M8)"),
           ("WP3 - Sperimentazione con le imprese pilota", "Mesi 9-11", "Prova del prototipo su 15 imprese: confronto tra la stima del sistema e le spese effettivamente ammesse dai bandi; misura dell'errore e correzione delle regole.", "D3.1 Rapporto di sperimentazione (M11)"),
           ("WP4 - Rilascio e diffusione", "Mese 12", "Documentazione per gli utenti, formazione di due studi professionali, rilascio della versione commerciale e comunicazione dei risultati.", "D4.1 Manuale utente (M12); D4.2 Piano di diffusione (M12)")]
    d.table([["Pacchetto", "Durata", "Attività", "Deliverable"]] + [[a, b, c, e] for a, b, c, e in wps], [32, 18, W - 100, 50], align_right_from=9)
    d.H1("16. GRUPPO DI LAVORO")
    d.table([["Ruolo", "Competenze", "Impegno"], ["Responsabile di progetto (M. Gallo)", "Dieci anni di esperienza nella progettazione di sistemi software per enti pubblici e imprese", "40% per 12 mesi"],
             ["Sviluppatore senior (A. Bertone)", "Architetture a servizi, basi dati relazionali, calcolo numerico", "55% per 9 mesi"], ["Sviluppatore senior (E. Marchetti)", "Interfacce web, esportazione di documenti", "55% per 9 mesi"],
             ["Data scientist (F. Greco)", "Elaborazione del testo, classificazione, validazione statistica", "70% per 9 mesi"], ["Project manager (F. Conti)", "Gestione di progetti finanziati, rendicontazione", "30% per 12 mesi"],
             ["UX designer (M. Esposito)", "Progettazione delle interfacce e test di usabilità", "25% per 6 mesi"]], [56, W - 98, 42], align_right_from=9)
    d.H1("17. MILESTONE E INDICATORI DI AVANZAMENTO")
    d.table([["Milestone", "Mese", "Criterio di raggiungimento"], ["MS1 Requisiti approvati", "3", "Documento condiviso con cinque imprese pilota"], ["MS2 Prototipo funzionante", "8", "Calcolo corretto su 40 bandi in 100% dei casi di test"],
             ["MS3 Sperimentazione conclusa", "11", "Scostamento medio stima/spese inferiore al 10% su 15 imprese"], ["MS4 Rilascio", "12", "Versione commerciale pubblicata e manuale consegnato"]], [58, 18, W - 76], align_right_from=9)
    d.H1("18. RIPARTIZIONE DEI COSTI PER PACCHETTO DI LAVORO")
    wp_tot = [62000, 118000, 74000, 33900]
    d.table([["Pacchetto di lavoro", "Costo (euro)"], ["WP1 - Analisi e progettazione", cents(wp_tot[0])], ["WP2 - Sviluppo del prototipo", cents(wp_tot[1])], ["WP3 - Sperimentazione con le imprese pilota", cents(wp_tot[2])],
             ["WP4 - Rilascio e diffusione", cents(wp_tot[3])], ["TOTALE COSTI PER PACCHETTO", cents(sum(wp_tot))]], [W - 40, 40], bold_rows=[5])
    d.H1("19. SOSTENIBILITA', IMPATTO E PROPRIETA' INTELLETTUALE")
    d.P("Al termine del progetto il prodotto sarà commercializzato con canoni annuali e licenze per gli studi professionali. L'impatto occupazionale previsto è di cinque nuove assunzioni a tempo indeterminato entro dodici mesi dalla conclusione. "
        "Il software resterà di proprietà esclusiva della società; i dati delle imprese pilota saranno trattati in forma pseudonimizzata e cancellati al termine della sperimentazione. Il progetto non arreca danno significativo agli obiettivi ambientali (principio DNSH).")
    d.H1("20. ELENCO DEGLI ALLEGATI")
    d.B(["Allegato 1 - Dichiarazione sostitutiva di atto di notorietà sulla dimensione d'impresa", "Allegato 2 - Dichiarazione de minimis", "Allegato 3 - Bilanci degli ultimi due esercizi", "Allegato 4 - Preventivi delle consulenze (tre per voce)",
         "Allegato 5 - Curriculum del gruppo di lavoro", "Allegato 6 - DURC in corso di validità"])


# ================================================================================================ business plan esteso
def extend_business_plan(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.H1("10. ANALISI DEL MERCATO")
    d.P("Il mercato di riferimento è quello dei software e servizi per la pianificazione finanziaria e l'accesso agli incentivi delle piccole e medie imprese italiane. Le imprese tra 10 e 249 addetti sono circa 220.000; "
        "nel segmento di interesse (imprese che investono in digitale e innovazione e che hanno un consulente o un'amministrazione strutturata) si stima un bacino di 60.000 imprese. Il prezzo medio annuo per impresa è ipotizzato in 1.800 euro; "
        "la quota di mercato obiettivo a tre anni è dell'1,2% del bacino, pari a 720 clienti, e a questa si aggiunge la vendita di licenze a 50 studi professionali.")
    d.table([["Segmento", "Imprese (stima)", "Prezzo annuo (euro)", "Quota obiettivo 2028", "Ricavi 2028 (euro)"], ["Imprese manifatturiere", U(26000), U(1900), "1,3%", U(round(26000 * 0.013 * 1900))], ["Imprese di servizi", U(24000), U(1700), "1,1%", U(round(24000 * 0.011 * 1700))],
             ["Imprese commerciali", U(10000), U(1500), "1,0%", U(round(10000 * 0.010 * 1500))], ["Studi professionali (licenze)", U(50), U(9600), "100%", U(480000)]], [46, 34, 36, 34, W - 150], align_right_from=1)
    d.H1("11. CONCORRENZA E POSIZIONAMENTO")
    d.table([["Concorrente (categoria)", "Punti di forza", "Punti deboli", "Posizionamento di Meridiana"], ["Portali di aggregazione dei bandi", "Ampia copertura, notorietà", "Nessun calcolo sul bilancio", "Quantifica l'effetto sul bilancio"],
             ["Software di pianificazione finanziaria", "Funzioni di budgeting complete", "Ignorano le regole dei bandi", "Collega bilancio e regole in un solo calcolo"], ["Consulenti specializzati", "Conoscenza dei bandi", "Costo elevato, tempi lunghi", "Strumento a canone per studi e imprese"]],
            [48, 40, 40, W - 128], align_right_from=9)
    d.H1("12. ANALISI SWOT")
    d.table([["Punti di forza", "Punti di debolezza"], ["Team tecnico stabile e certificazioni ISO 9001 e 27001; prodotto proprietario in sviluppo; ricavi ricorrenti in crescita", "Dimensione ridotta; dipendenza da pochi sviluppatori chiave; ridotta forza commerciale"],
             ["Opportunità", "Minacce"], ["Incentivi alla transizione digitale; domanda di strumenti trasparenti da parte degli studi; accordi con associazioni di categoria", "Ingresso di grandi operatori; variabilità delle regole dei bandi; concorrenza sul prezzo"]],
            [W / 2, W / 2], head=True, align_right_from=9)
    d.H1("13. PIANO DI SVILUPPO DEL PRODOTTO (ROADMAP)")
    d.table([["Trimestre", "Rilascio", "Obiettivo"], ["T4 2026", "Prototipo del motore di calcolo", "40 bandi codificati e verificati"], ["T1 2027", "Versione beta con 15 imprese pilota", "Scostamento medio inferiore al 10%"],
             ["T2 2027", "Versione commerciale 1.0", "Prime 150 imprese clienti"], ["T4 2027", "Modulo di confronto tra scenari", "Licenze a 20 studi professionali"], ["T2 2028", "Estensione ai bandi europei", "720 clienti complessivi"]], [26, 70, W - 96], align_right_from=9)
    d.H1("14. STRATEGIA COMMERCIALE E POLITICA DEI PREZZI")
    d.P("La vendita avviene su due canali: diretto, con una piccola squadra commerciale e webinar formativi, e indiretto, tramite studi professionali e associazioni di categoria che adottano la piattaforma per i propri clienti. "
        "I prezzi sono a canone annuale per impresa (da 900 a 3.000 euro in base al numero di bilanci e di bandi monitorati) e a licenza per gli studi (9.600 euro l'anno per studio, con numero illimitato di clienti). La prova gratuita di trenta giorni riduce l'attrito di acquisto.")
    d.H1("15. STATO PATRIMONIALE E RENDICONTO PREVISIONALI")
    b = M.balance(2025)
    rows = [["Stato patrimoniale previsionale (euro)", "2025 (consuntivo)", "2026", "2027", "2028"], ["Immobilizzazioni", U(b["fixed"]), U(b["fixed"] + 98000), U(b["fixed"] + 172000), U(b["fixed"] + 236000)],
            ["Attivo circolante e ratei", U(b["assets"] - b["fixed"]), U(b["assets"] - b["fixed"] + 142000), U(b["assets"] - b["fixed"] + 276000), U(b["assets"] - b["fixed"] + 410000)],
            ["Patrimonio netto", U(b["pn"]), U(b["pn"] + 130000), U(b["pn"] + 292000), U(b["pn"] + 481000)], ["Debiti finanziari", U(b["loan"]), U(b["loan"] + 105000), U(b["loan"] + 60000), U(b["loan"] + 15000)],
            ["Altre passività e fondi", U(b["liabilities"] - b["pn"] - b["loan"]), U(b["liabilities"] - b["pn"] - b["loan"] + 88000), U(b["liabilities"] - b["pn"] - b["loan"] + 140000), U(b["liabilities"] - b["pn"] - b["loan"] + 190000)]]
    d.table(rows, [W - 120, 30, 30, 30, 30], align_right_from=1)
    d.H1("16. FINANZIAMENTO RICHIESTO E CONDIZIONI")
    d.P("La società richiede un finanziamento chirografario a medio termine di 150.000 euro, durata 60 mesi con 12 di preammortamento, finalizzato a sostenere gli investimenti di sviluppo del 2026; "
        "è prevista la garanzia del Fondo di garanzia per le PMI. Il rapporto tra debiti finanziari e patrimonio netto resterebbe inferiore a 0,5 in tutto il periodo e la copertura degli oneri finanziari, misurata dal rapporto tra risultato operativo e oneri, superiore a 20 volte.")
    d.H1("17. ANALISI DI SENSIBILITA' SULLO SCENARIO")
    d.table([["Scenario", "Ricavi 2028 (euro)", "Risultato operativo 2028 (euro)", "Ipotesi"], ["Prudente", U(round(2480000 * 0.9)), U(round(2480000 * 0.9 * 0.11)), "Ricavi inferiori del 10% e costi invariati"],
             ["Base", U(2480000), U(round(2480000 * 0.158)), "Piano descritto"], ["Ottimistico", U(round(2480000 * 1.12)), U(round(2480000 * 1.12 * 0.185)), "Crescita dei canoni più rapida del 12%"]], [34, 40, 54, W - 128], align_right_from=1)
    d.H1("18. IPOTESI ALLA BASE DEL PIANO")
    d.B(["Crescita annua dei ricavi del 17% nel 2026, 16% nel 2027 e 15% nel 2028, sostenuta dalla quota crescente di canoni ricorrenti.", "Costo medio per dipendente in aumento del 3% annuo per rinnovi contrattuali e scatti.",
         "Ammortamento della piattaforma Atlas in cinque anni dal rilascio commerciale; credito d'imposta ricerca e sviluppo stimato in misura prudenziale.", "Tasso del nuovo finanziamento: Euribor a tre mesi più 2,3 punti.",
         "Nessun dividendo straordinario nel triennio; dividendi ordinari pari al 45% dell'utile."])


# ================================================================================================ DURC, de minimis: pagine aggiuntive
def extend_durc(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.H1("DETTAGLIO DELLE POSIZIONI CONTRIBUTIVE VERIFICATE")
    d.table([["Posizione", "Identificativo", "Periodo verificato", "Esito", "Note"], ["INPS - matricola aziendale", "0123456789", "08/2025 - 07/2026", "Regolare", "Versamenti DM10 tutti presenti e nei termini"],
             ["INAIL - codice ditta", "9876543", "08/2025 - 07/2026", "Regolare", "Autoliquidazione 2025/2026 versata"], ["INPS - gestione separata", "-", "-", "Non applicabile", "Nessun collaboratore con contributo in gestione separata"],
             ["Cassa edile", "-", "-", "Non applicabile", "Settore non edile"]], [40, 30, 34, 24, W - 128], align_right_from=9)
    d.H1("DATI DEL DICHIARANTE E INFORMATIVA")
    d.P("Il documento è stato richiesto ai sensi dell'art. 6 del D.M. 30 gennaio 2015 per la partecipazione a procedure di agevolazione. Il trattamento dei dati personali avviene nel rispetto del regolamento (UE) 2016/679 e dell'informativa pubblicata sui siti degli enti. "
        "La validità del documento può essere verificata inserendo il numero di protocollo nel servizio online dell'INPS o dell'INAIL.", left=True)
    d.table([["Dichiarante", "Giulia Ferraris, legale rappresentante"], ["Modalità di richiesta", "Servizio DURC On Line, accesso con identità digitale"], ["Casella PEC di recapito", CO["pec"]], ["Data stampa del documento", "01/09/2026"]],
            [58, W - 58], head=False, align_right_from=9, zebra=True)


def extend_de_minimis(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.H1("NOTE SULLA NOZIONE DI IMPRESA UNICA")
    d.P("Ai fini del regolamento, per «impresa unica» si intende l'insieme delle imprese fra le quali esiste almeno una delle seguenti relazioni: a) un'impresa detiene la maggioranza dei diritti di voto degli azionisti o soci di un'altra impresa; "
        "b) un'impresa ha il diritto di nominare o revocare la maggioranza dei membri dell'organo di amministrazione, direzione o sorveglianza di un'altra impresa; c) un'impresa ha il diritto di esercitare un'influenza dominante su un'altra impresa in virtù di un contratto o di una clausola dello statuto; "
        "d) un'impresa azionista o socia di un'altra impresa controlla da sola, in virtù di un accordo con altri azionisti o soci, la maggioranza dei diritti di voto di quest'ultima. Le imprese che intrattengono una delle relazioni di cui sopra per il tramite di una o più altre imprese sono anch'esse considerate un'unica impresa.", left=True)
    d.H1("VERIFICA DEI RAPPORTI DI COLLEGAMENTO")
    d.table([["Verifica", "Esito"], ["Soci persone fisiche: Giulia Ferraris (60%) e Marco Bertolotti (40%)", "Nessuno dei due detiene partecipazioni di controllo in altre imprese"],
             ["Partecipazioni della società in altre imprese", "Nessuna"], ["Operazioni straordinarie nel triennio (fusioni, scissioni, acquisizioni)", "Nessuna"], ["Rapporti di controllo per contratto o per statuto", "Nessuno"]], [W / 2, W / 2], align_right_from=9)
    d.H1("ALTRI AIUTI DI STATO PERCEPITI")
    d.P("Nel triennio considerato l'impresa ha fruito del credito d'imposta per attività di ricerca e sviluppo (art. 1, commi 198-206, L. 160/2019), che non è un aiuto in regime «de minimis» ma in esenzione per categoria; non ha ricevuto aiuti dichiarati incompatibili né è destinataria di ordini di recupero. "
        "L'impresa non è in difficoltà ai sensi dell'art. 2, punto 18, del regolamento (UE) n. 651/2014.", left=True)
    d.H1("INFORMATIVA SUL TRATTAMENTO DEI DATI PERSONALI")
    d.P("I dati contenuti nella presente dichiarazione sono trattati dal soggetto che gestisce la procedura di agevolazione per le sole finalità di verifica del rispetto del massimale e di adempimento degli obblighi di registrazione nel Registro Nazionale degli Aiuti di Stato, "
        "e sono conservati per il tempo previsto dalla normativa. Il dichiarante può esercitare i diritti previsti dagli articoli 15-22 del regolamento (UE) 2016/679 scrivendo al titolare del trattamento.", left=True)
    d.H1("ELENCO DEGLI ALLEGATI")
    d.B(["Copia del documento di identità del dichiarante in corso di validità", "Estratto del Registro Nazionale Aiuti (visura de minimis) del 30/09/2026", "Provvedimenti di concessione dei due aiuti dichiarati"])


def more_draft(d: Doc) -> None:
    W = _w(d)
    d.H1("21. DETTAGLIO DEI COSTI DI PERSONALE PER PERSONA")
    team = [("Responsabile di progetto (livello 1)", 40, 12, 5700), ("Sviluppatore senior (livello 3)", 55, 9, 5230), ("Sviluppatore senior (livello 3)", 55, 9, 5230),
            ("Data scientist (livello 3)", 70, 9, 5300), ("Sviluppatore (livello 4)", 50, 8, 4310), ("Sviluppatore (livello 4)", 50, 8, 4310), ("Project manager (livello 2)", 30, 12, 5500), ("UX designer (livello 4)", 25, 6, 4350)]
    rows = [["Persona", "Quota di tempo", "Mesi", "Costo mensile pieno (euro)", "Costo imputato (euro)"]]
    tot = 0
    for name, q, mths, monthly in team:
        amount = round(monthly * q / 100 * mths, 2)
        tot += amount
        rows.append([name, f"{q}%", str(mths), cents(monthly), cents(amount)])
    scale = 168000 / tot
    rows = [rows[0]] + [[r[0], r[1], r[2], r[3], cents(round(float(r[4].replace(".", "").replace(",", ".")) * scale, 2))] for r in rows[1:]]
    d.table(rows, [W - 130, 26, 16, 44, 44], align_right_from=1)
    d.P("I costi imputati sono ottenuti moltiplicando il costo mensile pieno per la quota di tempo dedicata al progetto e per il numero di mesi; il totale è riallineato al costo di personale indicato nel piano dei costi (168.000 euro). "
        "Il costo orario si determina dividendo il costo annuo lordo, comprensivo di oneri e TFR, per le ore produttive annue previste dal contratto collettivo.", left=True)
    d.H1("22. PIANO DEI PAGAMENTI E DELLE SPESE PER TRIMESTRE")
    q = [0.18, 0.31, 0.29, 0.22]
    d.table([["Trimestre", "Spese previste (euro)", "Quota cumulata"]] + [[f"T{k + 1}", cents(round(287900 * q[k], 2)), pct(sum(q[:k + 1]), 0)] for k in range(4)], [40, 50, 40], align_right_from=1)
    d.H1("23. SCHEMA DEI RISCHI DI RENDICONTAZIONE")
    d.B(["Tutte le spese saranno sostenute dopo la data di presentazione della domanda e documentate con fatture quietanzate.", "Le ore del personale saranno registrate in fogli di presenza mensili firmati.",
         "Gli acquisti superiori a 5.000 euro seguiranno una procedura con tre preventivi comparabili.", "Il CUP sarà richiesto dopo la concessione e riportato su ogni documento di spesa."])


def more_business_plan(d: Doc) -> None:
    W = _w(d)
    d.page_break()
    d.H1("19. IL TEAM")
    d.table([["Persona", "Ruolo", "Esperienza"], ["Giulia Ferraris", "Amministratore unico e direttore tecnico", "Fondatrice; venti anni di esperienza in sviluppo software e direzione di team"],
             ["Matteo Gallo", "Responsabile sviluppo", "Dieci anni nella progettazione di sistemi per enti pubblici"], ["Federica Conti", "Project manager", "Gestione di progetti finanziati e rendicontazione"],
             ["Fabio Greco", "Data scientist", "Elaborazione del testo e modelli statistici"], ["Valentina Rossetti", "Responsabile commerciale", "Vendite di servizi digitali a PMI e studi professionali"]], [40, 56, W - 96], align_right_from=9)
    d.H1("20. CONTO ECONOMICO PREVISIONALE DETTAGLIATO")
    rev = (1860000, 2150000, 2480000)
    rows = [["Voce (euro)", "2026", "2027", "2028"]]
    rows += [["Ricavi da canoni e licenze"] + [U(round(r * x)) for r, x in zip(rev, (0.38, 0.45, 0.52))], ["Ricavi da sviluppo su commessa"] + [U(round(r * x)) for r, x in zip(rev, (0.42, 0.36, 0.31))],
             ["Ricavi da consulenza e formazione"] + [U(round(r * x)) for r, x in zip(rev, (0.20, 0.19, 0.17))], ["Totale ricavi"] + [U(x) for x in rev],
             ["Stipendi e salari"] + [U(round(r * 0.57 * 0.74)) for r in rev], ["Oneri sociali e TFR"] + [U(round(r * 0.57 * 0.26)) for r in rev], ["Consulenze e collaborazioni"] + [U(round(r * 0.07)) for r in rev],
             ["Licenze e servizi cloud"] + [U(round(r * 0.055)) for r in rev], ["Affitti e utenze"] + [U(round(r * 0.045)) for r in rev], ["Marketing e vendite"] + [U(round(r * 0.032)) for r in rev],
             ["Altri costi di struttura"] + [U(round(r * 0.031)) for r in rev]]
    d.table(rows, [W - 90, 30, 30, 30], bold_rows=[4])
    d.H1("21. FLUSSO DI CASSA MENSILE 2026")
    months = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
    inflow = [138000, 142000, 150000, 148000, 156000, 162000, 150000, 118000, 160000, 166000, 170000, 178000]
    outflow = [132000, 134000, 141000, 140000, 146000, 151000, 154000, 130000, 148000, 152000, 156000, 188000]
    bal = 205497
    rows = [["Mese", "Incassi", "Pagamenti", "Saldo di cassa"]]
    for m_, i, o in zip(months, inflow, outflow):
        bal += i - o
        rows.append([m_, U(i), U(o), U(bal)])
    d.table(rows, [30, 40, 40, W - 110], align_right_from=1)
    d.H1("22. MATRICE DEI RISCHI")
    d.table([["Rischio", "Probabilità", "Impatto", "Risposta"], ["Perdita di sviluppatori chiave", "Media", "Alto", "Welfare, formazione, piano di successione e documentazione del codice"],
             ["Ritardo di pagamento degli enti pubblici", "Alta", "Medio", "Anticipo di fatture e affidamento bancario di 150.000 euro"], ["Cambiamento delle regole dei bandi", "Media", "Medio", "Versionamento e aggiornamento mensile delle regole"],
             ["Incidente di sicurezza informatica", "Bassa", "Alto", "ISO/IEC 27001, backup cifrati, copertura assicurativa cyber"]], [56, 24, 22, W - 102], align_right_from=9)
    d.H1("23. INDICATORI DI MONITORAGGIO (KPI)")
    d.table([["Indicatore", "2026", "2027", "2028"], ["Clienti con canone attivo", "210", "470", "720"], ["Ricavi ricorrenti su ricavi totali", "38%", "45%", "52%"], ["Abbandono annuo dei clienti (churn)", "9%", "8%", "7%"],
             ["Ricavi per dipendente (euro)", U(round(1860000 / 19)), U(round(2150000 / 22)), U(round(2480000 / 25))], ["Margine operativo sui ricavi", "13,5%", "15,0%", "15,8%"]], [W - 90, 30, 30, 30], align_right_from=1)
