// Tutte le spiegazioni dell'app in un posto solo: parole semplici, un esempio per ogni funzione.
// Gli importi negli esempi servono solo a spiegare come funziona una funzione: non sono dati del sistema.

// ---------------------------------------------------------------- glossario
export const GLOSSARY = {
  bando: { term: 'Bando', text: 'Un avviso pubblico che mette a disposizione dei soldi per certi progetti e dice quali spese si possono finanziare.', example: 'Il bando “Nuova Sabatini” aiuta a comprare macchinari.' },
  regola: { term: 'Regola del bando', text: 'Un numero o un divieto scritto nel bando. QUANTO li usa per controllare le spese.', example: '“Le consulenze possono valere al massimo il 20% del budget”.' },
  budget: { term: 'Budget', text: 'L’elenco di tutte le spese che prevedi per il progetto, con gli importi.', example: '3 stipendi + 1 server + 1 consulenza = 5 voci di budget.' },
  voce: { term: 'Voce di spesa', text: 'Una riga del budget: uno stipendio, un computer, una consulenza…', example: 'Voce “Server GPU” da 12.000 €.' },
  categoria: { term: 'Categoria', text: 'Il tipo di spesa. QUANTO ne usa cinque: personale, beni strumentali (macchinari, computer), consulenze, spese generali, formazione.', example: 'Un notebook è un “bene strumentale”; il commercialista è una “consulenza”.' },
  criterio: { term: 'Controllo (criterio)', text: 'Una verifica che QUANTO fa su una voce o sul budget intero. Sono 60, tutti scritti nel codice e sempre uguali.', example: 'Il controllo #7 verifica che il costo orario non superi il tetto del bando.' },
  richiesto: { term: 'Richiesto', text: 'Quanto hai messo nel budget, prima dei controlli.', example: 'Consulenza inserita a 30.000 € → richiesto 30.000 €.' },
  ammesso: { term: 'Ammesso', text: 'Quanto QUANTO considera finanziabile dopo i controlli. Può essere meno del richiesto.', example: 'Richiesto 30.000 €, ammesso 17.500 € perché supera il limite consulenze.' },
  ridotta: { term: 'Ridotta (decurtata)', text: 'La voce è accettata solo in parte: l’importo è stato abbassato per rispettare un limite.', example: 'Consulenza da 30.000 € ridotta a 17.500 €.' },
  respinta: { term: 'Respinta', text: 'La voce non è finanziabile: un controllo la esclude del tutto.', example: 'Pagamento in contanti → respinta (non è tracciabile).' },
  sospesa: { term: 'In attesa di documento', text: 'Manca il documento che prova la spesa (busta paga, fattura). Finché non lo indichi, la voce non viene ammessa.', example: 'Voce senza “Documento sorgente” → sospesa.' },
  punteggio: { term: 'Punteggio di conformità', text: 'Su 100: la percentuale di controlli superati tra quelli che si sono potuti eseguire.', example: '85/100 = su 100 controlli eseguiti, 85 sono ok.' },
  nonvalutato: { term: 'Non valutato', text: 'Un controllo saltato perché manca un dato sulla riga o il bando non dà la regola. Non conta mai come “superato”: QUANTO non fa finta.', example: 'Non indichi la data della spesa → il controllo sulla data è “non valutato”.' },
  massimale: { term: 'Limite (massimale)', text: 'Un tetto massimo, spesso espresso in percentuale del totale.', example: 'Consulenze max 20% del budget totale.' },
  fte: { term: 'FTE (tempo pieno)', text: 'Quanta parte del tempo di una persona lavora sul progetto. 1 = tempo pieno tutto l’anno, 0,5 = metà tempo.', example: 'Una persona al 50% per 12 mesi = FTE 0,5. La somma dei progetti di una persona non può superare 1.' },
  ral: { term: 'RAL', text: 'Retribuzione annua lorda: lo stipendio di un anno prima delle tasse.', example: 'RAL 38.000 €.' },
  ccnl: { term: 'CCNL', text: 'Il contratto collettivo nazionale: fissa livelli, ore di lavoro all’anno e contributi.', example: 'CCNL Metalmeccanica, livello 5.' },
  tfr: { term: 'TFR', text: 'Trattamento di fine rapporto: una quota di stipendio che l’azienda accantona ogni anno.', example: 'Circa l’8,6% dello stipendio annuo (valore illustrativo).' },
  oneri: { term: 'Oneri sociali', text: 'I contributi che il datore di lavoro versa oltre allo stipendio (pensione, assicurazioni…).', example: 'Su 38.000 € di RAL, 11.400 € di oneri (30%, valore illustrativo).' },
  costoorario: { term: 'Costo orario', text: 'Costo annuo dell’azienda per la persona diviso per le ore annue del contratto.', example: '52.565 € ÷ 1.656 ore ≈ 31,74 €/h.' },
  fontea: { term: 'Fonte A / B / C', text: 'Da dove vengono i dati. A = le regole del bando. B = tabelle ufficiali (contratti, contributi). C = i tuoi documenti (buste paga, fatture).', example: 'Ogni voce ricorda le tre fonti usate, così il calcolo si può rifare.' },
  hash: { term: 'Impronta (hash)', text: 'Una “impronta digitale” di un dato: 64 caratteri. Se cambi anche solo una virgola, l’impronta cambia completamente. Dall’impronta non si ricostruisce il dato.', example: '“Server 12.000” e “Server 12.001” hanno impronte totalmente diverse.' },
  merkle: { term: 'Merkle Root (impronta del budget)', text: 'Un’unica impronta che rappresenta tutte le righe del budget insieme. Si costruisce unendo a coppie le impronte delle righe, fino a restarne una sola.', example: 'Cambi 1 € su una riga → cambia la Merkle Root. Vedi come nella Guida.' },
  registro: { term: 'Registro delle certificazioni', text: 'Un libro mastro in cui si può solo aggiungere. Ogni riga contiene l’impronta della precedente e una firma: cambiare il passato si vede subito.', example: 'Registri la Merkle Root di un budget: oggi c’è, tra un anno puoi provare che non è cambiata.' },
  firma: { term: 'Firma digitale (Ed25519)', text: 'Un sigillo che solo chi ha la chiave segreta può apporre; chiunque può controllarlo con la chiave pubblica.', example: 'Il revisore verifica la firma anche offline.' },
  cep: { term: 'Codice CEP', text: 'Un codice breve (le prime 16 lettere dell’impronta) che identifica il “pacchetto di prove” di un budget.', example: 'CEP-1A2B3C4D5E6F7A8B.' },
  deminimis: { term: 'De minimis', text: 'Aiuti di piccola entità: un’impresa può riceverne fino a un tetto (circa 300.000 € in tre anni, controlla sempre il bando) senza autorizzazione UE.', example: 'Se ne hai già usati 250.000 €, ne restano 50.000.' },
  cumulo: { term: 'Cumulo / doppio finanziamento', text: 'Ricevere più contributi per la stessa spesa. Di solito è vietato.', example: 'Lo stesso macchinario finanziato da due bandi diversi.' },
  intensita: { term: 'Intensità di aiuto', text: 'La percentuale massima di una spesa che i contributi pubblici possono coprire.', example: 'Intensità 50%: su 100.000 € di spesa, al massimo 50.000 € di contributi.' },
  dnsh: { term: 'DNSH', text: '“Non arrecare danno significativo”: la spesa non deve danneggiare l’ambiente.', example: 'Un impianto molto inquinante può non essere ammesso.' },
  ammortamento: { term: 'Ammortamento', text: 'Il costo di un bene si divide sugli anni in cui lo usi. Nel progetto conta solo la parte dei mesi di durata del progetto.', example: 'Macchinario da 12.000 € al 20% annuo, progetto di 6 mesi → contano 1.200 €.' },
  cup: { term: 'CUP e CIG', text: 'Due codici pubblici. Il CUP identifica un progetto finanziato con soldi pubblici; il CIG identifica una gara d’appalto.', example: 'Il CUP va scritto su tutte le fatture del progetto.' },
  durc: { term: 'DURC', text: 'Certificato che dice che un fornitore è in regola con i contributi.', example: 'Fornitore senza DURC regolare → spesa a rischio.' },
  iva: { term: 'IVA recuperabile', text: 'Se l’IVA la puoi recuperare non è un vero costo, quindi non è finanziabile. Lo è solo l’IVA che non recuperi.', example: 'Impresa che detrae l’IVA: l’IVA non entra nel budget.' },
  milp: { term: 'Solutore (MILP)', text: 'Un programma matematico che prova le combinazioni possibili e trova la migliore rispettando tutti i limiti.', example: 'Decide quale fondo paga quale spesa per minimizzare quanto paghi tu.' },
  whatif: { term: 'What-if (“e se…?”)', text: 'Provi a togliere qualcosa e vedi subito come cambia il risultato.', example: 'Escludi un fondo e guardi quanto sale la spesa a tuo carico.' },
  archetipo: { term: 'Archetipo', text: 'Un budget “tipo”, ottenuto dalla media di progetti premiati. Gli archetipi si calcolano dai budget storici importati, con la loro fonte.', example: 'Archetipo: 55% personale, 15% beni, 25% consulenze, 5% generali.' },
  coseno: { term: 'Somiglianza (coseno)', text: 'Un numero da 0 a 1: quanto due ripartizioni si assomigliano. 1 = uguali.', example: '0,98 = quasi identiche; 0,60 = molto diverse.' },
  pp: { term: 'Punti percentuali (pp)', text: 'La differenza tra due percentuali.', example: 'Da 30% a 35% = +5 pp.' },
  traccia: { term: 'Traccia dell’algoritmo', text: 'Il diario di tutto ciò che il motore ha fatto: ogni controllo, su ogni voce, con l’esito e il motivo.', example: '“#31 — consulenze: ridotta di 12.500 €”.' },
  deterministico: { term: 'Deterministico', text: 'Stessi dati, stesso risultato, sempre. Nessuna stima, nessun caso, nessuna intelligenza artificiale che “interpreta” i numeri.', example: 'Rilanci la validazione domani: stessi identici importi.' },
  lacuna: { term: 'Lacuna', text: 'Qualcosa che il bando (o le fonti che abbiamo letto) non dice. QUANTO non lo inventa: quel controllo resta spento e lo vedi dichiarato.', example: '“Il bando non indica il tetto per la formazione”.' },
  confidenza: { term: 'Affidabilità di una regola', text: 'PRIMARIA = letta dal testo ufficiale. SECONDARIA = da una guida o un riassunto affidabile. INTERPRETAZIONE = nostra lettura di un testo ambiguo. PARSING = estratta in automatico da un testo caricato.', example: 'Le regole SECONDARIE e INTERPRETAZIONE vanno controllate sul testo ufficiale.' },
  esecuzione: { term: 'Esecuzione (run)', text: 'Un controllo del budget salvato nella memoria, con la sua traccia. Si può rivedere in seguito.', example: 'Ieri hai validato il progetto X: oggi la rivedi dal Quartier Generale.' },
  evento: { term: 'Evento', text: 'Ogni operazione dell’app lascia una riga di diario: cosa, quando, chi, con quale esito.', example: '“14:32 — Validazione budget — OK — 46 voci”.' },
  timeline: { term: 'Timeline', text: 'Il diario di tutti gli eventi in ordine di tempo.', example: 'Scelta del bando → controllo del budget → registrazione.' },
}

// ---------------------------------------------------------------- aiuti brevi (icona “?”)
export const HINTS = {
  bando_scheda_regole: { title: 'Regole', text: 'I numeri del bando che QUANTO usa nei controlli, ognuno con la sua fonte e un livello di affidabilità.', example: '“Tetto orario personale: 35 €/h” — fonte: art. 5 del bando.' },
  bando_scheda_req: { title: 'Requisiti', text: 'Tutto ciò che il bando obbliga o vieta, anche senza numeri. Ogni requisito è collegato ai controlli che lo verificano.', example: 'OBBLIGO: “il CUP deve comparire sulle fatture” → controllo #50.' },
  bando_scheda_cov: { title: 'Controlli attivati', text: 'I 60 controlli in una griglia. Verde = il bando ha una regola per quel controllo. Azzurro = si fa solo sui dati che inserisci. Grigio = spento perché il bando non dice nulla.', example: 'Se il bando non parla di ore straordinarie, il controllo #11 resta grigio.' },
  bando_scheda_fonti: { title: 'Fonti', text: 'I documenti da cui abbiamo ricavato regole e requisiti, ciascuno con il suo link. Sono la prova di dove viene ogni dato.', example: 'Avviso pubblico, decreto attuativo, circolare dell’ente.' },
  bando_ricerca: { title: 'Cerca un bando sul web', text: 'Scrivi il nome del bando. QUANTO lo cerca su internet, scarica le pagine e i PDF ufficiali (decreti, avvisi, circolari, atti della Gazzetta Ufficiale), li tiene in memoria e li legge tutti. Le fonti ufficiali hanno la precedenza; blog e portali si scaricano solo se li scegli tu.', example: 'Scrivi “Resto al Sud”: trova la pagina di Invitalia, la sua sezione Normativa e i PDF collegati.' },
  bando_upload: { title: 'Aggiungi un documento a mano', text: 'Se hai un PDF o un testo che la ricerca non ha trovato, aggiungilo: viene salvato in memoria e letto insieme agli altri. Un PDF fatto di foto (scansione) non si può leggere.', example: 'Un avviso che ti ha mandato un consulente per email.' },
  bando_controlli_attivi: { title: 'Perché quasi nessun bando arriva a 60/60', text: 'I 60 controlli coprono tutto ciò che QUANTO sa verificare: personale, beni, consulenze, spese generali, regole trasversali. Un singolo bando ne regola solo una parte — una garanzia bancaria non parla di ammortamenti, un fondo per l’export non parla di straordinari. Il numero attivato dipende da cosa il bando dice davvero, mai da quanto è stato letto con attenzione: se un dato manca, il criterio resta “non valutato”, non “sbagliato”.', example: 'Il Fondo di Garanzia PMI attiva 0 criteri sulle voci di costo: è una garanzia sul finanziamento, non regole di spesa ammissibile.' },
  budget_heatmap: { title: 'La mappa dei 60 controlli', text: 'Una riga per voce, una colonna per ciascuno dei 60 controlli. Colorato = eseguito (verde superato, ambra ridotto, rosso respinto, azzurro in attesa di un documento); tratteggiato = non valutato, manca un dato tuo o una regola del bando; grigio chiaro = quel controllo non riguarda proprio quella voce. Clicca una riga per aprirla nell’Ispettore qui a fianco.', example: 'Una voce di personale senza tabella CCNL in Fonte B resta quasi tutta tratteggiata: i controlli 2-15 dipendono da quella tabella.' },
  bando_catalogo: { title: 'Catalogo nazionale dei bandi', text: 'Ogni notte QUANTO scarica da solo l’elenco di tutti i bandi nazionali, regionali e comunali pubblicati sui portali ufficiali. Per la maggior parte si conosce solo nome, ente e link: nessuna regola è ancora stata letta, perché leggere per intero migliaia di bandi che magari nessuno userà mai sarebbe uno spreco. Cerca quello che ti serve e chiedi di analizzarlo: da lì parte la stessa ricerca sul web di “Cerca un bando”.', example: 'Cerchi “voucher digitale” e trovi 40 bandi regionali mai letti: scegli quello della tua regione e QUANTO lo analizza.' },
  bando_fonti_scaricate: { title: 'Documenti di origine', text: 'I documenti scaricati o caricati, con l’indirizzo da cui vengono e il tipo di fonte (ufficiale o secondaria).', example: 'Un PDF di Invitalia è “ufficiale”; un articolo di un blog è “secondaria”.' },
  bando_regole_verifica: { title: 'Regole da verificare', text: 'Quando due documenti danno numeri diversi per la stessa regola, QUANTO non sceglie a caso: la mette da parte e la fa decidere a una persona (Quartier Generale → Caricamento bandi). Finché non è decisa, non diventa un controllo.', example: 'Tetto orario 40 €/h in una pagina e 35 €/h nel PDF dell’avviso → “da controllare a mano”.' },

  budget_toolbar: { title: 'I pulsanti del budget', text: 'Importa: carica un Excel/CSV. Importa da una candidatura: prende le voci da un PDF già scritto. Aggiungi voce: una riga a mano. La bozza dal tuo profilo parte dai bilanci veri dell’azienda.', example: 'Importa il tuo Excel, poi premi “Controlla il budget”.' },
  budget_riepilogo: { title: 'Le quattro caselle', text: 'Punteggio: quanti controlli sono passati. Richiesto: il totale che hai inserito. Ammesso: quanto è finanziabile. Escluso o ridotto: la differenza.', example: 'Richiesto 500.000 €, ammesso 431.000 € → escluso 69.000 €.' },
  budget_lista: { title: 'Elenco delle voci', text: 'Le voci sono raggruppate per categoria. Il colore dice l’esito; se una voce è stata ridotta vedi l’importo originale barrato.', example: '“Consulenza audit 17.500 €” con sopra “30.000 €” barrato.' },
  budget_ispettore: { title: 'Ispettore', text: 'Seleziona una voce: vedi da dove vengono i dati, la formula e ogni controllo, passo per passo, con il motivo.', example: 'Per un dipendente: RAL + oneri + TFR = costo annuo; ÷ ore = costo orario.' },
  budget_editor: { title: 'Modifica voce', text: 'Cambia i campi di una voce. Ogni campo compilato attiva dei controlli (i numeri #). I campi vuoti non vengono valutati. Dopo la modifica il calcolo si rifà da solo.', example: 'Aggiungi “Data della spesa” → si attiva il controllo #46 sulla data.' },
  budget_sintesi: { title: 'Sintesi', text: 'Un riassunto scritto in italiano. Ogni cifra viene confrontata con i risultati veri prima di mostrarla: se un numero non torna, il testo non viene usato.', example: '“Ammessi 431.000 € su 500.000 €”.' },
  budget_controlli: { title: 'Controlli sull’intero budget', text: 'Controlli che guardano tutto il budget insieme, non la singola voce: cumulo con altri contributi, de minimis, liquidità, variazioni.', example: 'Aiuti già ricevuti nel triennio + questo contributo > tetto de minimis → FAIL.' },
  budget_wp: { title: 'Pacchetti di lavoro (WP)', text: 'Dividi il budget ammesso tra i pacchetti di lavoro del bando. Tu indichi i limiti (quota minima, desiderata, massima; categorie ammesse; tetto di una categoria dentro il WP): il programma assegna le voci rispettandoli e ti mostra i controlli. Non inventa nessun limite.', example: 'Voci da 60.000, 20.000, 15.000 e 5.000 € e quote desiderate 50%, 30%, 20%: senza dividere voci lo scostamento minimo è di 20 punti; dividendone una tutto torna esatto.' },
  budget_registra: { title: 'Registra l’impronta', text: 'Scrive nel registro l’impronta del budget (non i dati). Poi chiunque può verificare, nella pagina Verifica, che il budget non sia cambiato.', example: 'Registri oggi; fra sei mesi il revisore ricalcola e l’impronta coincide.' },
  budget_export: { title: 'Esporta', text: 'Scarica il budget validato in Excel o PDF, con il codice CEP e un QR che porta alla pagina di verifica.', example: 'Allega il PDF alla domanda: chi lo riceve scansiona il QR e verifica.' },

  lab_player: { title: 'Riproduzione', text: 'Fa rivedere i controlli uno alla volta, nell’ordine reale. Puoi mettere in pausa o trascinare la barra.', example: 'Velocità “Lento” per seguire ogni passaggio.' },
  lab_fasi: { title: '1 · Le fasi', text: 'Il motore lavora a stadi: controlli sulle righe, tempo dedicato (FTE), limiti percentuali, controlli sul budget intero, impronte, Merkle, sintesi. Sotto ogni fase vedi quanto tempo ha richiesto.', example: 'Di solito tutto dura pochi millisecondi.' },
  lab_mappa: { title: '2 · Mappa dei controlli', text: 'Una riga per voce, una colonna per controllo. Verde = superato, giallo = ridotta, rosso = respinta, azzurro = in attesa di documento, tratteggiato = non valutato, scuro = non pertinente.', example: 'Un quadratino giallo su “Consulenza audit”, colonna 31 = ridotta dal limite consulenze.' },
  lab_cascata: { title: '3 · Cascata degli importi', text: 'Per la voce scelta: parte dall’importo originale, e ogni controllo che lo riduce è una barra. In fondo l’importo ammesso.', example: '30.000 € → −12.500 € (limite consulenze) → 17.500 €.' },
  lab_limiti: { title: '4 · Limiti percentuali', text: 'Alcuni limiti sono “% del totale finale”, ma il totale dipende a sua volta dalle riduzioni. QUANTO risolve il circolo con una formula esatta, senza tentativi.', example: 'Altre spese 70.000 €, limite 20%: consulenze ammesse 17.500 € (che è il 20% di 87.500 €).' },
  lab_merkle: { title: '5 · Impronta del budget', text: 'Ogni riga diventa un’impronta; le impronte si uniscono a coppie fino a una sola: la radice. Cambiare anche 1 € cambia la radice.', example: 'Vuoi vederlo passo passo con numeri veri? Vai alla Guida.' },

  alloc_obiettivo: { title: 'Obiettivo', text: 'Cosa deve ottimizzare il solutore: spendere il meno possibile di tasca propria, coprire più voci possibile, oppure usare meno fondi possibile.', example: '“Minimizzare le fonti” = meno pratiche da gestire.' },
  alloc_whatif: { title: 'Escludi una fonte', text: 'Clicca un fondo per toglierlo e vedere subito il nuovo piano.', example: 'Togli “Transizione 5.0”: i macchinari restano a carico dell’ente.' },
  alloc_flusso: { title: 'Flusso delle spese', text: 'A sinistra le spese, a destra i fondi. Lo spessore di ogni striscia è l’importo. La striscia arancione è ciò che paghi tu.', example: 'Una striscia spessa verso un fondo = quel fondo copre molto.' },
  alloc_uso: { title: 'Utilizzo dei fondi', text: 'Quanto usi di ciascun fondo, quanto ne resta e il residuo de minimis.', example: 'Dotazione 90.000 €, usati 75.000 € → margine 16,7%.' },
  alloc_mesi: { title: 'Timeline 12 mesi', text: 'Come si distribuiscono le spese nell’anno: in verde la parte coperta, in arancione quella a tuo carico.', example: 'Un mese alto = un macchinario acquistato quel mese.' },

  pattern_input: { title: 'La tua ripartizione', text: 'Scrivi che parte del budget va a ciascuna categoria, da 0 a 1 (0,25 = 25%). Le quattro quote dovrebbero fare 1.', example: 'Personale 0,58 · beni 0,12 · consulenze 0,25 · generali 0,05.' },
  pattern_risultato: { title: 'Risultato', text: 'L’archetipo a cui somigli di più, la somiglianza (0–1) e la categoria in cui ti discosti di più, in punti percentuali.', example: '“Scostamento principale: consulenze +10 pp” = spendi 10 punti in più in consulenze del budget tipo.' },

  auditor_verifica: { title: 'Verifica impronta', text: 'Confronta l’impronta che hai in mano (es. dal QR) con quella scritta nel registro per quel progetto.', example: 'Coincidono e la firma è valida → “Budget certificato e non modificato”.' },
  auditor_ricalcola: { title: 'Ricalcola dai dati', text: 'Rifà tutto da zero con i dati originali e confronta con il registro. È la prova più forte: non ti fidi di nessuna impronta ricevuta.', example: 'Se qualcuno ha cambiato una cifra, il ricalcolo dà un’impronta diversa.' },
  auditor_manomissione: { title: 'Simula manomissione', text: 'Aggiunge 1 € alla prima riga prima del ricalcolo, per mostrarti che la verifica se ne accorge.', example: 'Attivalo, premi “Ricalcola”: il risultato diventa rosso.' },

  hq_panoramica: { title: 'Panoramica', text: 'I numeri chiave: validazioni, progetti, bandi, documenti, eventi, registrazioni; stato della memoria e attività recente.', example: 'Se “Registrazioni” è rosso, la catena del registro è stata alterata.' },
  hq_timeline: { title: 'Timeline', text: 'Tutto ciò che è successo, in ordine di tempo. Puoi filtrare per operazione, progetto, bando ed esito. Clicca un evento per i dettagli; le validazioni si rivedono nell’Algoritmo.', example: 'Filtra “progetto PRJ-1” per vedere solo la sua storia.' },
  hq_operazioni: { title: 'Mappa operazioni', text: 'Tutte le cose che l’app sa fare, con i passaggi interni e quante volte sono state eseguite.', example: '“Validare un budget”: 7 fasi, 12 esecuzioni, media 40 ms.' },
  hq_fascicoli: { title: 'Fascicoli', text: 'Una cartella per ogni progetto: esecuzioni, documenti e storia. Il fascicolo di un bando (documenti, regole, utilizzo) è invece nella sezione Bandi.', example: 'Apri il progetto X: vedi le 3 validazioni fatte e la registrazione.' },
  hq_documenti: { title: 'Documenti', text: 'Elenco dei file lavorati (bandi caricati, import, export…) con nome, dimensione e impronta. Il testo intero si conserva solo per i bandi caricati.', example: 'L’impronta prova che il file non è stato sostituito.' },
  hq_database: { title: 'Database', text: 'Le tabelle della memoria, in sola lettura. Serve a controllare cosa c’è salvato; da qui non si può modificare nulla.', example: 'Tabella “events”: una riga per ogni operazione.' },
  hq_archivio: { title: 'Bandi', text: 'Tutto ciò che riguarda i bandi, in un solo posto: la lista a sinistra, il dettaglio a destra con Scheda consulente, Documenti (i PDF scaricati, apribili e cancellabili), Regole (modificabili), Requisiti, Fondo (la linea di finanziamento per l’allocazione) e Utilizzo (progetti e cronologia). “Nuovo bando” lo crea da zero; un bando si elimina dalla scheda Azioni.', example: 'Apri “Resto al Sud”, controlla i PDF scaricati e decidi la regola “75% o 70%”.' },
  hq_scheda: { title: 'Scheda per il consulente', text: 'Per ogni bando: cosa dicono i documenti, cosa NON dicono, cosa cercare e come verificare. Serve a sapere da dove partire quando si controlla un bando.', example: 'La regola “tetto costo orario” manca: la scheda dice le parole da cercare nel decreto e come controllare.' },
}

// ---------------------------------------------------------------- guida di pagina (striscia in alto)
export const GUIDE = {
  bandi: {
    title: 'Bandi',
    what: 'Qui scegli il bando su cui lavorare e vedi cosa QUANTO ne ha capito: regole, obblighi e controlli che attiva. Se il bando non c’è, lo cerca lui sul web e ne scarica i documenti ufficiali.',
    steps: ['Clicca un bando nell’elenco a sinistra, oppure scrivine il nome in “Cerca un bando sul web”.', 'La ricerca scarica pagine e PDF ufficiali, li salva in memoria e li legge: guarda l’avanzamento.', 'Apri le schede: Regole, Requisiti (con filtri), Controlli attivati, Fonti.', 'Premi “Usa questo bando nel budget”.'],
    example: 'Scrivi “Resto al Sud”: QUANTO trova la pagina Invitalia e la sezione Normativa, scarica i PDF collegati e nei requisiti trovi, con la fonte accanto, cose come “contributo del 75% a fondo perduto fino a 120.000 euro” e “età 18–35 anni”.',
    terms: ['bando', 'regola', 'criterio', 'confidenza'],
  },
  budget: {
    title: 'Budget',
    what: 'Qui inserisci le spese del progetto e QUANTO le controlla una per una con i 60 controlli del bando scelto.',
    steps: ['Scegli il bando (in alto).', 'Riempi il budget: parti dalla bozza del tuo profilo, importa un Excel o aggiungi voci a mano.', 'Premi “Controlla il budget”.', 'Clicca una voce: capisci perché è stata accettata, ridotta o respinta. Se la modifichi, il controllo si rifà da solo.', 'Se va bene: registra l’impronta o esporta in Excel/PDF.'],
    example: 'Inserisci “Consulenza audit 30.000 €” con le altre spese a 70.000 € e il limite consulenze al 20% del totale: QUANTO ammette 17.500 €, perché 17.500 è il 20% di 87.500 (70.000 + 17.500). L’Ispettore ti mostra il passo esatto.',
    terms: ['voce', 'categoria', 'ammesso', 'punteggio', 'nonvalutato'],
  },
  lab: {
    title: 'Algoritmo',
    what: 'Il “dietro le quinte”: vedi in modo grafico ogni passo che il motore ha fatto sul tuo budget. Non è una simulazione: è la traccia reale.',
    steps: ['Prima controlla un budget dalla pagina Budget.', 'Premi Riproduci per vedere i controlli accendersi uno a uno (o trascina la barra).', 'Nella mappa passa il mouse su un quadratino: leggi il controllo e il motivo.', 'Clicca una riga per vedere come cambia l’importo di quella voce.', 'In fondo vedi come nasce l’impronta del budget.'],
    example: 'Quadratino giallo sulla riga “Consulenza audit”, colonna 31: quel controllo ha ridotto l’importo. La cascata mostra 30.000 € → −12.500 € → 17.500 €.',
    terms: ['traccia', 'deterministico', 'nonvalutato', 'massimale', 'merkle'],
  },
  allocation: {
    title: 'Allocazione',
    what: 'Parte dai bilanci della tua azienda, stima le spese dell’anno successivo, trova i bandi adatti (e come rientrare nei loro tetti) e decide quali spese far coprire da quali bandi, per pagare di tasca propria il meno possibile.',
    steps: ['1 · Controlla i dati: bilanci e documenti si caricano nel Profilo; ciò che manca lo completi tu.', '2 · Stima dell’anno: parte dall’ultimo bilancio, la variazione per categoria la scegli tu.', '3 · Bandi adatti: per ognuno vedi se puoi partecipare, quanto potrebbe coprire e quali voci ridurre per rispettare i tetti. In «Da studiare» trovi i bandi del catalogo non ancora letti, in ordine di affinità: se uno ti interessa, premi «Studia questo bando».', '4 · Spunta i bandi da includere: il programma calcola il piano e il flusso di ogni spesa.'],
    example: 'Le consulenze del bilancio sono 40.000 €, ma il bando le ammette solo fino al 10% delle spese: la scheda ti dice quanto è ammissibile e di quanto ridurre la voce.',
    terms: ['milp', 'whatif', 'deminimis', 'cumulo'],
  },
  pattern: {
    title: 'Confronto',
    what: 'Confronta come hai diviso il budget tra le grandi categorie con i budget di progetti premiati (banca dati con la fonte di ognuno). Ti dice se sei fuori linea, non se vincerai.',
    steps: ['Scegli la categoria di bandi con cui confrontarti.', 'Scrivi le sei quote (0 – 1) oppure usa il budget che hai già controllato: il confronto si aggiorna da solo.', 'Leggi l’archetipo più vicino, lo scostamento maggiore e i budget storici più simili.'],
    example: 'Se metti il 25% in consulenze e i progetti premiati il 15%, leggi “consulenze +10 pp”: è il punto da guardare per primo.',
    terms: ['archetipo', 'coseno', 'pp'],
  },
  documents: {
    title: 'Documenti',
    what: 'Carichi visura, bilanci, buste paga e F24 in PDF: QUANTO legge i campi e ti dice quanto è sicuro di ognuno. Quello che non è sicuro lo controlli tu prima che entri nei calcoli. Gli altri documenti aziendali si archiviano senza essere letti.',
    steps: ['Scegli il tipo di documento e il file.', 'Guarda i campi letti: verde = sicuro, giallo/rosso = da verificare.', 'Conferma o correggi i campi incerti.', 'Usa la busta paga nel Budget; visura e bilanci aggiornano da soli il profilo azienda.'],
    example: 'Dalla busta paga la RAL non si legge: QUANTO la stima (competenze × mensilità) e ti chiede di confermarla.',
    terms: ['fontea', 'hash'],
  },
  auditor: {
    title: 'Verifica',
    what: 'Per chi deve fidarsi: controlla che un budget certificato non sia stato cambiato dopo la registrazione.',
    steps: ['Inserisci progetto e impronta (di solito arriva dal QR del documento).', '“Verifica impronta” la confronta col registro.', '“Ricalcola dai dati” rifà tutto da zero e poi confronta.', 'Attiva “Simula manomissione”: con 1 € in più la verifica diventa rossa.'],
    example: 'Il documento dice CEP-1A2B…: scansioni il QR, arrivi qui con impronta e progetto già compilati, premi Verifica e leggi il verdetto.',
    terms: ['hash', 'merkle', 'registro', 'firma'],
  },
  profilo: {
    title: 'Profilo',
    what: 'Il profilo della tua azienda e i suoi documenti: da visura e bilanci QUANTO ricava i dati dell’impresa e i costi di ogni anno. Serve all’Allocazione e a creare la bozza di budget per i bandi futuri.',
    steps: ['Segui la procedura guidata in alto: trascina insieme visura, bilanci e altri file, poi rispondi alle poche domande che restano.', 'Controlla i dati: ogni valore dice se viene da un documento o l’hai scritto tu (il tuo non viene mai sovrascritto).', 'Completa i campi che mancano e i costi degli anni senza bilancio.', 'Nel Budget, «Bozza di budget dal profilo azienda» parte da questi dati.'],
    example: 'Carichi il bilancio 2025: ricavi, personale e consulenze compaiono nel profilo. Resta da indicare se sei una start-up innovativa: lo scrivi tu.',
    terms: ['fontea'],
  },
  hq: {
    title: 'Quartier Generale',
    what: 'Riservato al titolare dell’account (si apre dal Profilo): vede tutto ciò che è successo nel sistema — operazioni, documenti, bandi, progetti — e la memoria del database.',
    steps: ['Panoramica: numeri chiave e stato.', 'Timeline: ogni operazione in ordine di tempo, con i passaggi.', 'Bandi: ogni documento scaricato (anche il PDF originale), regole, requisiti e la scheda per il consulente; puoi correggere, rileggere, esportare o eliminare.', 'Fascicoli, Documenti, Database: cosa è stato lavorato e salvato; nel Database puoi eliminare righe ed esportare in CSV.'],
    example: 'Apri la Timeline, clicca “Controllare il budget” e poi “Rivedi nell’algoritmo”: rivedi in grafico quella specifica esecuzione.',
    terms: ['evento', 'timeline', 'esecuzione'],
  },
}

// ---------------------------------------------------------------- percorso rapido
export const QUICKSTART = [
  { t: 'Configura la tua azienda', d: 'Pagina Profilo: la procedura guidata ti fa caricare visura e bilanci e rispondere a due domande. Serve per stimare l’anno dopo, trovare i bandi adatti e avere una bozza di budget.' },
  { t: 'Scegli il bando', d: 'Pagina Bandi: cerca o apri un bando, leggi regole e requisiti, premi “Usa questo bando”.' },
  { t: 'Carica il budget', d: 'Pagina Budget: bozza dal profilo, Excel o voci a mano.' },
  { t: 'Controlla il budget', d: 'Ogni voce viene controllata con i 60 controlli. Vedi ammesso, ridotto, respinto.' },
  { t: 'Capisci perché', d: 'Ispettore per una voce; il pulsante «Guarda come ha lavorato» per il film di tutti i passaggi.' },
  { t: 'Certifica e verifica', d: 'Registra l’impronta del budget. Chiunque può poi verificare che non sia cambiato.' },
]

// ---------------------------------------------------------------- ogni funzione, con un esempio
export const FUNCTIONS = [
  { page: 'Bandi', items: [
    { name: 'Elenco dei bandi', what: 'Sei bandi già preparati, con stato (aperto/chiuso), ente, numero di regole, requisiti e controlli attivati.', example: 'Clicca “Nuova Sabatini” per aprirne la scheda.' },
    { name: 'Regole', what: 'I numeri del bando con la fonte e l’affidabilità di ciascuno.', example: '“Tetto costo orario 35 €/h — SECONDARIA”: da confermare sul testo ufficiale.' },
    { name: 'Requisiti', what: 'Obblighi, divieti e limiti letti nel testo, collegati ai controlli.', example: 'DIVIETO: “non sono ammesse spese in contanti” → controllo #52.' },
    { name: 'Controlli attivati', what: 'La griglia dei 60 controlli: quali il bando attiva, quali girano solo sui dati, quali sono spenti.', example: '5/60 attivati dal bando: gli altri controlli usano solo ciò che scrivi nelle voci.' },
    { name: 'Fonti', what: 'I documenti da cui derivano regole e requisiti, con il link alla fonte.', example: 'Decreto direttoriale dell’8 ottobre 2025 (Invitalia).' },
    { name: 'Cerca un bando sul web', what: 'Cerca il nome su internet, scarica le pagine e i PDF ufficiali (anche seguendo i link a decreti e Gazzetta), li salva in memoria e li legge tutti.', example: 'Scrivi “Resto al Sud” e guarda i documenti arrivare uno a uno.' },
    
    { name: 'Aggiungi un documento a mano', what: 'Se la ricerca non ha trovato un documento, lo aggiungi tu (PDF o testo) e viene letto insieme agli altri.', example: 'Un avviso ricevuto per email.' },
    { name: 'Usa questo bando', what: 'Passa le regole al Budget e registra la scelta nella timeline.', example: 'Premi il pulsante e sei già nel Budget con il bando attivo.' },
  ] },
  { page: 'Budget', items: [
    { name: 'Importa Excel/CSV', what: 'Legge le voci da un file e ti dice gli errori riga per riga.', example: 'Riga 7: “importo non valido” — correggi e reimporta.' },
    { name: 'Aggiungi voce', what: 'Crea una riga nella categoria scelta con valori di partenza da modificare.', example: 'Aggiungi “Formazione” e apri “Modifica voce”.' },
    { name: 'Controlla il budget', what: 'Fa girare i 60 controlli sul server e mostra il risultato.', example: 'Punteggio 85/100, ammesso 431.000 € su 500.000 €.' },
    { name: 'Ispettore', what: 'Per una voce: fonti, formula e ogni controllo con il motivo.', example: '“#7 — ridotta di 4.000 €: costo orario 40 € > tetto 35 €”.' },
    { name: 'Modifica voce', what: 'Cambia i campi (organizzati per gruppo). Ogni campo mostra i controlli che attiva.', example: 'Metti “Pagamento: contanti” → la voce viene respinta (#52).' },
    { name: 'Controlli sul budget intero', what: 'Cumulo, de minimis, liquidità, variazioni tra capitoli.', example: '“#49 de minimis: residuo insufficiente”.' },
    { name: 'Registra l’impronta', what: 'Scrive nel registro l’impronta del budget con firma digitale.', example: 'Fatto: voce n. 12 del registro, con data e firma.' },
    { name: 'Pacchetti di lavoro (WP)', what: 'Dopo il controllo, dividi il budget ammesso tra i WP del bando: indichi quote e categorie ammesse, QUANTO assegna le voci rispettandole e ti mostra ogni controllo.', example: '4 voci e 3 WP con quote desiderate 50/30/20: se una voce può essere divisa, lo scostamento è zero.' },
    { name: 'Esporta Excel / PDF', what: 'Scarica il budget validato con codice CEP e QR di verifica.', example: 'Il QR apre la pagina Verifica già compilata.' },
  ] },
  { page: 'Guarda come ha lavorato', items: [
    { name: 'Riproduzione', what: 'Rivede i controlli nell’ordine reale, con pausa, velocità e barra.', example: '“Voce LINE-003 · controllo #31 → ridotto (−12.500 €)”.' },
    { name: 'Le fasi', what: 'Sette fasi con il tempo di ciascuna.', example: 'Merkle: 0,3 ms.' },
    { name: 'Mappa dei controlli', what: 'Griglia voci × controlli con i colori dell’esito.', example: 'Passa il mouse su una cella per leggere il motivo.' },
    { name: 'Cascata degli importi', what: 'Come l’importo di una voce scende controllo dopo controllo.', example: '30.000 € → 17.500 €.' },
    { name: 'Limiti percentuali', what: 'Risolve i limiti “% del totale finale” con una formula esatta.', example: 'Vedi richiesto contro ammesso per ogni gruppo.' },
    { name: 'Albero dell’impronta', what: 'Le foglie sono le righe, la cima è la Merkle Root.', example: 'Per la spiegazione passo passo vai alla sezione Merkle di questa Guida.' },
  ] },
  { page: 'Allocazione', items: [
    { name: '1 · I dati della tua azienda', what: 'Riepilogo del profilo: completezza, ultimo bilancio, dimensione e cosa manca.', example: 'Profilo al 92%: manca solo se sei una start-up innovativa.' },
    { name: '2 · Stima dell’anno successivo', what: 'Parte dall’ultimo bilancio; la variazione per categoria la scegli tu (le tue due ultime annate ti danno solo un suggerimento).', example: 'Consulenze +10%: da 172.500 € a 189.750 €.' },
    { name: '3 · Bandi adatti', what: 'Per ogni bando studiato: se puoi partecipare, quanto copre, quali voci ridurre per i tetti. «Da studiare» elenca i bandi del catalogo per affinità.', example: 'Consulenze al massimo il 10% del totale: con 40.000 € di consulenze e 224.200 € di altre spese, ne sono ammissibili 24.911 €.' },
    { name: 'Studia questo bando', what: 'Cerca, scarica e legge i documenti ufficiali di un bando del catalogo; poi lo trovi tra quelli valutati, con il contributo stimato se dichiara un’aliquota.', example: 'Lettura completa: 8 documenti, 165 requisiti, 2 regole numeriche.' },
    { name: 'Bozza di budget per questo bando', what: 'Apre il Budget con la bozza costruita sui tuoi bilanci e ridotta ai tetti del bando.', example: 'Beni strumentali al 25% del bilancio: 28.175 €.' },
    { name: '4 · Obiettivo', what: 'Tre modi di scegliere il “migliore” piano.', example: 'Minimizzare la spesa netta.' },
    { name: 'Flusso e piano per voce', what: 'Da quale fondo è coperta ogni spesa e quanto resta a tuo carico.', example: 'EXP-ASSET: 62% Transizione 5.0, 38% ente.' },
    { name: 'Utilizzo fondi e de minimis', what: 'Quanto usi di ogni dotazione e del plafond de minimis.', example: 'Residuo de minimis 30.000 €.' },
    { name: 'Timeline 12 mesi', what: 'Spese per mese, coperte e a carico.', example: 'Aprile alto: acquisto del macchinario.' },
  ] },
  { page: 'Confronto', items: [
    { name: 'Confronto con archetipi', what: 'Somiglianza (0–1) tra la tua ripartizione e quella dei budget tipo.', example: '0,98 con “Tecnologico”.' },
    { name: 'Scostamento principale', what: 'La categoria dove ti allontani di più, in punti percentuali.', example: 'Consulenze +10 pp.' },
  ] },
  { page: 'Verifica', items: [
    { name: 'Verifica impronta', what: 'Confronta un’impronta con quella registrata; controlla anche firma e integrità della catena.', example: 'Tre segni verdi: impronta, firma, catena.' },
    { name: 'Ricalcola dai dati', what: 'Rifà l’intero calcolo dai dati originali e poi confronta.', example: 'Impronta uguale → nulla è cambiato.' },
    { name: 'Simula manomissione', what: 'Cambia di 1 € la prima riga per mostrare che la verifica se ne accorge.', example: 'Risultato rosso: “impronta diversa”.' },
  ] },
  { page: 'Profilo', items: [
    { name: 'Procedura guidata', what: 'Otto passi come le storie dei social: carichi i documenti insieme (il tipo si riconosce dal nome), rispondi alle domande e controlli le letture incerte. In alto la percentuale di completezza.', example: 'Trascini 14 file: il profilo passa dallo 0% al 92%; resta da dire se sei una start-up innovativa.' },
    { name: 'Dati e bilanci dell’azienda', what: 'Ogni valore dice se viene da un documento o l’hai scritto tu; il tuo non viene mai sovrascritto. Puoi aggiungere anni e correggere i costi per categoria.', example: 'Esercizio 2025: personale 890.700 €, consulenze 172.500 € (da documento).' },
    { name: 'Operazioni recenti', what: 'Le tue ultime azioni nell’app, in ordine di tempo.', example: '“Accesso di te@email.it”, “Bando confermato: Resto al Sud”.' },
    { name: 'I tuoi documenti', what: 'Visura, bilanci, buste paga, F24, bozze di candidatura e ogni altro documento aziendale (archiviato cifrato, anche Excel): li vedi solo tu.', example: 'Carichi una busta paga e la usi come voce di personale nel Budget.' },
    { name: 'Cambia password', what: 'Aggiorna la password: tutti gli accessi già aperti altrove decadono subito.', example: 'Cambi password dal telefono: il computer in ufficio chiede di rientrare.' },
  ] },
  { page: 'Quartier Generale', items: [
    { name: 'Accesso riservato', what: 'Si apre solo dal Profilo, ed è visibile solo al titolare dell’account: nessun altro utente vede questo pulsante.', example: 'Un collega con accesso all’app non trova da nessuna parte il Quartier Generale.' },
    { name: 'Panoramica', what: 'Numeri chiave, stato di memoria e sicurezza, attività recente.', example: 'Registro non integro: la voce compromessa è indicata.' },
    { name: 'Timeline', what: 'Ogni operazione in ordine di tempo, con filtri e dettagli.', example: 'Filtra per esito “FAIL”.' },
    { name: 'Mappa operazioni', what: 'Tutte le operazioni possibili con i passaggi interni e le statistiche.', example: '“Registrare l’impronta”: 4 passaggi, 3 esecuzioni.' },
    { name: 'Catalogo', what: 'Tutte le voci del catalogo nazionale con la descrizione e le caratteristiche lette dalla scheda ufficiale (forma di agevolazione, costi ammessi, regioni, ATECO). Il pulsante legge le schede mancanti.', example: 'Cerca “voucher”: vedi per ogni misura descrizione, scadenza e a chi si rivolge.' },
    { name: 'Bandi', what: 'Ogni bando in memoria: documenti (testo estratto e file originale), regole, requisiti, la linea di finanziamento per l’allocazione e chi lo ha usato. Si corregge, rilegge, esporta in ZIP o elimina da qui.', example: 'Apri “Resto al Sud”, scarica il decreto originale e decidi la regola “75% o 70%”.' },
    { name: 'Scheda per il consulente', what: 'Per ogni bando: cosa dicono i documenti, cosa non dicono, quali parole cercare, dove compaiono di solito e come verificare.', example: 'Regola “tetto costo orario” non trovata: la scheda dice di cercare “costo orario” nell’articolo sulle spese di personale.' },
    { name: 'Fascicoli', what: 'Cartella di un progetto: le sue validazioni, i documenti, la cronologia.', example: 'Progetto X: 3 validazioni, 1 registrazione.' },
    { name: 'Documenti', what: 'File lavorati, con dimensione e impronta.', example: 'Export PDF del progetto X.' },
    { name: 'Database', what: 'Le tabelle della memoria: le leggi, le esporti in CSV e puoi eliminare righe. Il registro delle certificazioni è protetto (append-only).', example: 'Elimini una riga di “events”; non puoi eliminarla da “anchors”.' },
  ] },
]

export function lookup(id) {
  const g = GLOSSARY[id]
  if (g) return { title: g.term, text: g.text, example: g.example }
  return HINTS[id] || null
}
