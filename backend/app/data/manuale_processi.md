# Manuale dei processi di QUANTO

Versione 4.0 · aggiornato l'8 ottobre 2026 · Standard di ricerca e raccolta dati RICERCA-v2

Questo manuale spiega come lavora QUANTO, passo per passo, con parole semplici e con esempi. È scritto per chi usa lo strumento (commercialisti, consulenti) e per chi lo gestisce dal Quartier Generale. Ogni numero che trovi qui (limiti, soglie, pesi) è quello che il programma usa davvero: se cambia nel codice, cambia anche qui.

## 1. Le regole d'oro

Tutto quello che QUANTO fa rispetta cinque regole. Se un processo le violasse, sarebbe un errore da correggere.

1. **Non inventare mai un dato.** Se un numero non c'è, QUANTO scrive «manca» e dice cosa serve per averlo. Non lo stima a occhio e non lo chiede a un'intelligenza artificiale.
2. **Ogni numero ha una fonte.** Un tetto, una percentuale, una data: accanto c'è il documento da cui viene (con il link) e quanto è affidabile quella lettura.
3. **Stesso input, stesso risultato.** Il calcolo non usa il caso e non scrive testo: stesso budget, stesse regole, stesso risultato, oggi e tra un anno. Per questo ogni calcolo lascia un'impronta che si può verificare.
4. **Le ipotesi si dicono.** Quando per dare un importo serve una scelta dell'azienda (per esempio «finanzia tutto l'investimento con un prestito»), l'ipotesi è scritta accanto al numero.
5. **Nel dubbio decide una persona.** Se due documenti dicono cose diverse sulla stessa regola, QUANTO non sceglie: la mette da parte e la fa decidere al Quartier Generale.

## 2. La mappa: da dove si parte e dove si arriva

Il percorso di un cliente, in ordine:

1. **Catalogo**: QUANTO tiene una lista di tutti i bandi italiani aperti (circa 780 voci, aggiornate ogni notte).
2. **Studio del bando**: per un bando scelto, cerca i documenti ufficiali, li scarica, li legge e ne ricava regole, requisiti e la percentuale di agevolazione.
3. **Profilo dell'azienda**: si caricano visura e bilanci; QUANTO legge i dati e dice quanto è sicuro di ognuno.
4. **Stima dell'anno dopo**: partendo dall'ultimo bilancio si stimano spese e ricavi dell'anno da pianificare.
5. **Bandi adatti**: per ogni bando studiato si controlla se l'azienda può partecipare e quanto varrebbe in euro.
6. **Piano**: un programma matematico combina i bandi scelti e decide quale fondo paga quale spesa. Da qui nasce il «potenziale massimo».
7. **Budget**: si costruisce il budget del progetto e i 60 criteri lo controllano voce per voce.
8. **Registro**: il budget controllato lascia un'impronta firmata che chiunque può verificare.
9. **Confronto**: i budget dei clienti diventano template, per nicchia e per bando, e insegnano al sistema come si compone un budget vincente.

Il resto del manuale spiega ogni passaggio.

## 3. Il processo standard di ricerca e raccolta dati (RICERCA-v2)

Questo è il modo unico, uguale per ogni bando, in cui QUANTO cerca e legge le fonti. Si chiama «studiare un bando». Dura da pochi secondi a circa mezzo minuto.

### 3.1 In una frase
QUANTO parte dalla scheda del catalogo, trova la pagina dell'ente che gestisce il bando, da lì arriva agli allegati (il bando vero, il decreto), li legge tutti e, se ancora non ha trovato la percentuale di contributo, la cerca apposta.

### 3.2 I passi, in ordine

**Passo 1: cercare.** Si parte dal nome del bando e dall'indirizzo della scheda ufficiale. Se il motore di ricerca è disponibile si aggiungono i risultati più pertinenti; in ogni caso la scheda del catalogo è il punto di partenza sicuro. Ogni indirizzo viene classificato:
- **UFFICIALE**: Gazzetta Ufficiale, Normattiva, EUR-Lex, ministeri, Invitalia, SIMEST, Mediocredito Centrale, siti delle Regioni, delle Camere di commercio, dei comuni e simili. Solo da qui si leggono regole e percentuali.
- **SECONDARIA**: blog, portali di consulenza. Si conservano come lettura di contorno ma **mai** per ricavarne una percentuale.

**Passo 2: scaricare (primo giro).** Fino a 8 documenti, 6 alla volta in parallelo. Ogni documento viene scaricato per intero (testo e file originale) e si accettano pagine web, PDF (fino a 12 MB e 400 pagine), documenti Word e fogli Excel. Prima di accettare un documento si controlla che parli davvero di quel bando (nome o parole distintive): altrimenti viene scartato, così il bando di un'altra Regione con un nome simile non inquina le regole.

**Passo 3: seguire i link (fino a tre giri).** È la parte che rende il metodo diverso da una semplice ricerca. Dalle pagine scaricate si prendono i collegamenti utili e si scelgono fino a 4 documenti per giro, con questo ordine:
- prima i PDF, poi le pagine;
- punteggio in più per parole come «bando», «avviso», «decreto», «regolamento», «allegato 1»;
- punteggio in meno per «privacy», «trattamento dei dati», «graduatoria», «report», «griglia», «CUP», «sospensione»: documenti che non contengono le regole.
Si fanno al massimo 3 giri, e solo se il tempo trascorso è sotto i 26 secondi (la funzione ha un limite di 60 secondi). Ogni giro parte dalle pagine nuove trovate nel giro precedente: scheda del catalogo, pagina dell'ente, allegati.

**Passo 4: leggere.** Tutti i documenti in memoria passano dal lettore. Un documento che «cita spesso» il bando si legge intero; gli altri solo nei passaggi che nominano il bando; i fogli elettronici si conservano come dati e non si leggono come testo normativo. Per ogni documento si scrive quanti requisiti ha dato; se non ne ha dati, si scrive il motivo (testo illeggibile, documento che non nomina il bando, testo troppo corto).

**Passo 5: cercare la percentuale, apposta.** Se dopo la lettura non c'è né una regola «contributo pari al N%» né una tabella di intensità, parte un ultimo giro (solo se sono passati meno di 30 secondi): si cercano fino a 4 documenti in più con parole come «intensità contributo percentuale spese ammissibili beneficiari». Si rilegge tutto.

**Passo 6: valutare e riferire.** Si produce un rapporto: COMPLETA, PARZIALE o INSUFFICIENTE.
- COMPLETA: almeno 20.000 caratteri di testo ufficiale, almeno 40 requisiti, almeno metà dei requisiti riconosciuti.
- PARZIALE: almeno un documento ufficiale e almeno 10 requisiti.
- INSUFFICIENTE: tutto il resto.
Il rapporto elenca una per una le lacune (per esempio «nessuna percentuale di agevolazione trovata») così nessun bando resta «a metà» senza che si sappia perché.

### 3.3 Un esempio vero: il bando SWIch 2026 della Regione Piemonte
- La scheda del catalogo (8.754 caratteri) rimandava alla pagina della Regione. Prima il sistema si fermava lì.
- Con la ricerca a più giri: scheda del catalogo, pagina della Regione (22.281 caratteri), poi gli allegati: il bando completo (177.687 caratteri), le definizioni, la normativa, le regole di compilazione. Totale: 6 documenti ufficiali, 293.206 caratteri, 158 requisiti.
- Dalla tabella del bando QUANTO ha letto: «Micro-piccole imprese: base 25%, maggiorazioni, massimo 60%» e i massimali per progetto (da 1.000.000 a 5.000.000 euro).

### 3.4 Cosa QUANTO non fa durante la ricerca
- Non usa un modello linguistico per «capire» cifre: i numeri si leggono con regole fisse e ogni cifra è legata alla frase da cui viene.
- Non legge percentuali da blog o riassunti.
- Non apre indirizzi non pubblici (reti interne, indirizzi locali) e non supera 400 richieste ogni 10 minuti.
- Non contorna i blocchi dei siti: se un sito non risponde, lo dice nel rapporto.

### 3.5 Limiti dichiarati
Le pagine costruite interamente con JavaScript danno poco testo; i PDF scansionati (immagini) non si leggono senza riconoscimento ottico; i motori di ricerca gratuiti possono bloccare un server cloud (per questo la scheda del catalogo e i suoi link sono il percorso principale).

## 4. Il catalogo nazionale

**Da dove viene.** Dalle mappe del sito dei cataloghi ufficiali (incentivi.gov.it e Invitalia). Ogni voce ha nome, ente e link. Una volta, in totale, erano circa 6.000 voci; la maggior parte è chiusa.

**Cosa succede ogni notte** (orari Vercel, ora UTC):
1. **03:00, aggiornamento.** Si scarica l'elenco e si aggiungono le voci nuove.
2. **03:30, lettura delle schede.** Per ogni voce si legge la pagina ufficiale: titolo, descrizione breve, forma di agevolazione, costi ammessi, dimensione, regioni, ATECO, date di apertura e chiusura. I dati si salvano nella scheda.
3. **Pulizia.** Le voci chiuse (data di chiusura passata, o nome che cita solo anni passati e nessuna data) vengono eliminate. Per questo il catalogo «utile» resta di circa 780 voci.

**Come QUANTO sceglie quali bandi proporti (affinità).** Per le voci che non sono state ancora studiate, si calcola un punteggio da 0 a 1:
- 75% è la quota delle tue spese (dall'ultimo bilancio) che le «costi ammessi» della scheda coprono;
- più 10% se il bando è della tua Regione, più 15% se il settore indicato coincide con il tuo (ATECO), più 5% se è per start-up e tu lo sei;
- meno 30% se il settore indicato è un altro, meno 40% se è riservato a start-up e la tua impresa ha 5 anni o più.
Si escludono: bandi chiusi, di un'altra Regione, di altra dimensione o ATECO, per soggetti che non sono imprese. Affinità ALTA da 0,6, MEDIA da 0,25.

Esempio: un'azienda informatica di Torino. «Voucher per la digitalizzazione» di una Regione del Sud viene esclusa (Regione); «Bando SWIch Piemonte» sale in alto perché è piemontese e copre personale e consulenze, che sono le sue spese principali.

## 5. La lettura delle regole di un bando

Dopo aver scaricato i documenti QUANTO ricava tre cose diverse.

**a) Le regole numeriche** (le uniche che «accendono» i controlli del budget): per esempio «le consulenze non possono superare il 20% del totale», «tetto del costo orario 35 euro», «il contributo è pari al 50% delle spese». Si leggono con formule fisse. Se lo stesso testo dà due valori diversi per la stessa regola (75% e 70%), QUANTO non ne pubblica nessuno e li manda alla persona del Quartier Generale. Una regola già pubblicata non viene mai sovrascritta da una lettura successiva: solo una persona può correggerla. Ogni regola pubblicata ha un livello di affidabilità: PRIMARIA (letta dal testo ufficiale), SECONDARIA (da una guida), INTERPRETAZIONE (lettura di un testo ambiguo) o PARSING (estratta in automatico).

**b) I requisiti**: le frasi del bando che sono obblighi, divieti, limiti o informazioni, ognuna collegata al tema («chi può presentare domanda», «spese ammissibili», ecc.) e ai controlli del budget che riguardano.

**c) Le cifre**: tetti, soglie e importi presenti nel testo, strutturati.

Le regole pubblicate compongono un «insieme di regole» con un'impronta (hash): cambiare una regola cambia l'impronta e quindi anche l'impronta di ogni budget calcolato con quella regola.

## 6. Quanto vale un bando in euro

Per ogni bando adatto a un'azienda, QUANTO calcola un valore con un intervallo: dal valore prudente al valore con tutte le maggiorazioni. La percentuale viene da qui, in questo ordine:

1. **Regola pubblicata**: il bando dichiara «contributo pari al N% delle spese». Valore unico.
2. **Modello del bando** (per i bandi curati): per ogni bando dove l'aiuto non è una semplice percentuale, c'è una formula con le sue fonti e le sue ipotesi.
3. **Tabella del testo ufficiale**: la tabella delle intensità per dimensione d'impresa.

Il valore si calcola sulla spesa prevista dell'anno nelle categorie ammesse dal bando. Se il bando ha un tetto per progetto, il valore non lo supera.

### 6.1 Le tabelle di intensità
Molti bandi regionali scrivono le percentuali in una tabella per dimensione. QUANTO legge ogni riga dove la dimensione apre la riga («Micro-piccole imprese», «Medie imprese», «Grandi imprese») e prende la prima percentuale come **base** e la più alta come **massimo** (base più tutte le maggiorazioni). Per un'azienda piccola si usano solo le righe che la riguardano. Esempio: «Micro-piccole imprese 25% 20% 15% 60%» diventa base 25%, massimo 60%. Con 1.965.919 euro di spesa prevista: da 491.480 a 1.179.552 euro. Di ogni riga si conserva il testo da cui viene e il documento in cui sta.

### 6.2 I modelli dei bandi curati

| Bando | Natura del valore | Come si calcola | Ipotesi dichiarata |
|---|---|---|---|
| Nuova Sabatini | Contributo sugli interessi | Interessi convenzionali di un finanziamento a 5 anni al 2,75% (3,575% per 4.0 e green), rate semestrali costanti: 7,66% (10,0%) dell'investimento | Si finanzia l'intero investimento. Il metodo ufficiale è nella circolare MIMIT: verificarlo prima di indicare l'importo al cliente |
| Iperammortamento | Risparmio fiscale | Maggiorazione (180% fino a 2,5 milioni) per l'aliquota IRES del 24%: 43,2% dei beni | Serve reddito imponibile capiente e beni 4.0 |
| Fondo 394/81 (SIMEST) | Fondo perduto | 10% (con almeno un requisito) o 20% (imprese energivore) | Il finanziamento copre le spese; il fondo perduto rientra nel de minimis |
| Horizon Europe | Fondo perduto | Dal 70% (innovazione, imprese a scopo di lucro) al 100% (ricerca) | È un massimo teorico: solo la parte di spesa che entra in un progetto è finanziata |
| Fondo di Garanzia PMI | Garanzia (non è un guadagno) | 50% (liquidità) o 80% (investimenti) del finanziamento bancario | L'investimento è finanziato per intero con un prestito |

La **garanzia** non si somma ai contributi: si calcola solo l'importo garantibile (per esempio 78.861-126.178 euro su un finanziamento di 157.722 euro).

### 6.3 Quando manca la percentuale
QUANTO non inventa nulla. Il bando resta nella lista «Bandi senza una percentuale nei documenti letti» con il motivo, e si può rilanciare lo studio: la ricerca cerca apposta la percentuale.

## 7. Lo studio, i lavori e il profilo dell'azienda

**Lo studio e i lavori.** L'account è dello studio: nome, password e token valgono per tutto lo studio. Ogni azienda cliente è un **lavoro**: sotto il Profilo dello studio si aprono tanti lavori quanti sono i clienti, e ognuno ha il suo profilo, i suoi bilanci, i suoi documenti, il suo modello di previsione e i suoi risultati salvati. Il lavoro attivo si sceglie dal selettore in alto: tutte le pagine (Allocazione, Budget, Confronto) mostrano allora i dati di quell'azienda e di nessun'altra. Per questo non si mescolano mai: ogni dato aziendale vive con la chiave «studio + lavoro». Eliminare un lavoro cancella i suoi dati (si riscrive il nome per confermare), ma i template di budget restano allo studio.

**Cosa si salva da solo, per ogni lavoro.** Le scelte e i risultati restano: anno e percentuali dell'Allocazione, bandi inclusi nel piano, obiettivo e de minimis; il budget con il bando scelto e il risultato del controllo; il motore, il bando e i dati inseriti nel Confronto. Cambiando pagina si ritrova tutto com'era, e anche chiudendo e riaprendo QUANTO. I calcoli si rifanno da soli sugli stessi dati, con lo stesso risultato.

**Il profilo dello studio.** La pagina Profilo ha quattro sezioni: **Lavori** (le aziende clienti e il lavoro attivo), **Studio e dati** (nome, ruolo, ragione sociale e partita IVA dello studio, telefono), **Sicurezza** (cambio password con le regole in vista, uscita da tutti i dispositivi, ultimi accessi) e **Piano e dati** (crediti, operazioni recenti, esportazione di tutti i dati dello studio in un file, eliminazione dell'account con password e e-mail). L'e-mail è l'identificativo di accesso e non si cambia da qui.

**I token.** Il lavoro con QUANTO è libero: profilo, documenti, stima, bandi adatti, controllo del budget (anche cento volte mentre lo scrivi), assistente, Confronto e Verifica non costano nulla. I token servono dove c'è un calcolo grande o un consegnabile, e il costo segue **quanti dati si analizzano**:
- **Piano di allocazione: da 2 a 4,8 token.** 2 di base, più fino a 1,4 secondo il bilancio (quante righe di spesa analizza) e fino a 1,4 secondo i bandi nel piano (quanto sono corposi). Prima di calcolare, l'app mostra il costo con il suo perché e aspetta la tua conferma. Vale 30 giorni per lo stesso lavoro e anno: ricalcolare con altre scelte non costa di più; se i dati diventano più grandi si paga solo la differenza.
- **Consegnare un budget: da 1 a 2 token** (esportarlo o registrarlo): 1 fino a 25 voci, 1,5 fino a 60, 2 oltre. Una consegna vale 30 giorni per lo stesso budget.
- **Studiare un bando nuovo: 3 token** (1 per rifare lo studio di uno in memoria, 0 per uno già studiato); se la lettura è completa 1 torna indietro. I bandi vanno studiati prima dell'allocazione: solo quelli con regole pubblicate entrano nel piano, gli altri sono in «Da studiare».
- **Pubblicare un budget per tutti: +0,5 token** (Confronto → «Pubblica il tuo budget», o il tasto in fondo al Budget). Una volta per cliente e bando, al massimo 10 al mese. Allena il motore collettivo, che è ciò che rende QUANTO più preciso per tutti.

Il piano costa **209 € al mese o 1.999 € all'anno** e include **15 token al mese** (quelli non usati restano fino a 30), più **10 di benvenuto che non scadono**. Quando finiscono, **10 token in più costano 25 €**. Si spendono prima quelli del mese, poi gli altri. Se un'operazione fallisce i token tornano da soli. Se finiscono, il lavoro continua e si fermano solo piano, consegne e studi nuovi, con un messaggio chiaro; un anticipo di cortesia di 2 token evita di restare bloccati. Dove si vede: in basso nel menu a sinistra e in Profilo → Piano e dati. Le ricariche sono richieste: il pagamento online non è ancora attivo e le elabora il titolare dal Quartier Generale (Utenti → Accredita). Esempio: uno studio con 12 clienti in un mese fa 4 piani (15,6 token), 10 consegne (13), studia 2 bandi nuovi (4 con i premi) e pubblica 6 budget (+3): consuma 29,6 token, 15 inclusi e 14,6 in più, cioè 2 pacchetti da 25 €.

### 7.1 Il profilo dell'azienda e i documenti

**I documenti** (visura, bilanci, buste paga, F24, bozze di candidatura, altri file) si caricano nel Profilo. Il lettore trasforma ogni file in campi e per ogni campo dice quanto è sicuro: AUTO (sicuro), da verificare, confermato, corretto. Entrano nei calcoli solo i campi sicuri o confermati da una persona; i campi incerti restano da controllare e il totale dell'anno viene segnalato come parziale finché non si verificano.

**Da dove viene ogni dato.** Ogni valore ricorda se viene da un documento (con quale), se è stato scritto a mano o se è derivato (per esempio la regione dalla provincia). Un valore scritto a mano non viene mai sovrascritto da una nuova lettura. Se un documento viene eliminato, i valori che ne venivano decadono.

**La dimensione dell'impresa** (micro, piccola, media, grande) si ricava da dipendenti e fatturato con le soglie europee. È indicativa: non guarda il totale di bilancio né le imprese collegate.

**Documenti fatti come quelli veri.** Un bilancio vero è lungo (stato patrimoniale, conto economico, rendiconto, nota integrativa, relazione, spesso un allegato con il dettaglio conto per conto) e ripete gli stessi costi in più tabelle. QUANTO legge gli importi anche senza centesimi, ignora i piè di pagina, e quando i costi compaiono più volte usa **una sola tabella**: quella che torna con il «Totale costi della produzione» del documento e ha più righe riconosciute, così nessun costo si conta due volte. Lo stesso vale per la domanda di contributo (costi per voce, per pacchetto di lavoro, per persona). Dove un'etichetta compare più volte conta la più specifica («Addetti» e non «numero medio annuo di addetti»; ATECO prevalente e non secondario). Nei modelli F24 si leggono le sole sezioni con codice tributo e un importo nella colonna «a credito compensati» è un credito, non un debito. I costi che nessun bando rimborsa (imposte indirette, quote associative, liberalità, svalutazioni, carburanti) vanno nella categoria **«Altro (non agevolabile)»**: sono nel totale dei costi ma non nelle cinque categorie di spesa.

**Cosa QUANTO legge, oltre a visura e bilanci.** Ogni file riconosciuto diventa dati, con il foglio e la riga (o la pagina) da cui vengono:

| File | Cosa ne ricava | A cosa serve |
|---|---|---|
| Excel dell'organico | persona per persona: livello, contratto, ore, RAL | il budget del personale, il controllo del costo orario |
| Libro cespiti (Excel) | i beni, il costo storico, l'ammortamento | beni a fine vita da rinnovare, ammortamento da non contare |
| Registro delle fatture ricevute (Excel) e fatture elettroniche (XML, anche in un archivio ZIP) | spese per voce e per anno | le spese per voce del budget |
| Bilancio di verifica del gestionale (Excel o CSV) | i costi conto per conto | il bilancio di un anno senza PDF |
| Bilancio in formato XBRL | ricavi, costi, personale, utile per esercizio | confronto con il bilancio PDF |
| Budget dell'azienda, piano degli investimenti, piano delle assunzioni (Excel) | gli importi dell'anno del progetto | il budget dal piano, non dalla previsione |
| Registro degli aiuti (Excel), dichiarazione de minimis, visura aiuti dell'RNA | le concessioni con data, regime, importo, COR | il residuo de minimis e la verifica |
| Libro soci | quote dei soci; le società socie si nominano, le persone restano un codice | impresa unica |
| Dichiarazioni IVA, IRAP, REDDITI | volume d'affari, valore della produzione, reddito | coerenza con il bilancio |
| Estratto conto | il saldo alla data | controllo di liquidità |
| Preventivi dei fornitori | fornitore, numero, validità, importo, voce | l'importo vero di un acquisto previsto |
| DURC, contratto di locazione, credito ricerca e sviluppo, piano di ammortamento di un finanziamento | scadenze e importi | requisiti e cumulo |

Un file che non si riconosce resta archiviato, senza inventare nulla. I tracciati della visura RNA e dell'XBRL che QUANTO legge oggi sono quelli dei file di prova: sul primo file vero potrebbe servire un adattamento.

**Coerenza tra i documenti.** Nella pagina «Cosa ho letto dai documenti» la scheda «Coerenza tra i documenti» confronta carte che parlano della stessa cosa. Esempio: il volume d'affari IVA 2025 è 1.579.064 € e i ricavi del bilancio 1.583.200 €: differenza 0,3%, torna. Se la differenza supera il 5% viene segnalata da spiegare. Controlla anche che le quote dei soci sommino il 100%, la scadenza del DURC, l'età della visura aiuti e i preventivi scaduti.

**Come si lavora nel Profilo di un cliente.** La pagina è fatta di sezioni che si aprono e si chiudono, ognuna con il suo riassunto già in testa: «Configurazione guidata» (aperta finché il profilo non è completo), «Il profilo dell'azienda» (chiusa: dice solo quanti dati mancano), «I documenti» (aperta solo se c'è qualcosa da fare), «Cosa ho letto dai documenti» e «Aiuti ricevuti». In cima c'è sempre **un solo «Prossimo passo»**, con il pulsante che porta esattamente al punto giusto: carica la visura, rispondi alla domanda, completa il dato mancante, verifica le letture incerte. Esempio: con 17 buste paga la cui RAL è solo stimata, il pulsante «Verifica ora» apre la verifica rapida, una tabella con valore letto e frase di origine di tutte le letture; togli il segno a quelle che non tornano e confermi le altre con un clic. Un pulsante in un'altra pagina (per esempio «Completa il profilo» nell'Allocazione, o «Carica il registro del personale» nel Budget) apre il Profilo già sulla sezione giusta, con un anello che evidenzia il punto. Il dettaglio di un documento si apre subito sotto di lui; se le letture incerte sono tutte giuste, «Sono tutte giuste» le conferma insieme, e «Vai al prossimo» passa al documento successivo.

**Tutti i file dell'azienda** si possono aprire, scaricare uno per uno o tutti insieme in un archivio ZIP con l'elenco.

## 8. La stima dell'anno dopo

La stima parte dall'ultimo bilancio disponibile e applica a ogni voce (personale, beni strumentali, consulenze, spese generali, formazione, e anche ricavi) una variazione annua per gli anni che mancano.

**Da dove viene la percentuale di ogni voce, in ordine:**
1. quella scritta da te in questo calcolo;
2. quella del tuo modello di previsione (indicata dal cliente, dal suo CFO o stimata dal tuo studio);
3. quella che risulta dai due ultimi bilanci (già inserita, senza che tu debba riscriverla).

**La spiegazione di ogni riga** usa i numeri dei documenti. Esempio: «Nel bilancio 2024 il personale era 748.700 euro, nel 2025 890.700: +19,0%. I ricavi sono passati da 1.327.900 a 1.583.200 (+19,2%): la voce pesa il 56,4% e poi il 56,3% dei ricavi, in linea. Gli addetti medi sono passati da 13 a 15». Sotto la riga si indicano i nomi dei file da cui vengono i dati. Se la variazione supera il 25% l'anno, compare un punto di attenzione.

La formula è: stima = ultimo bilancio × (1 + variazione) elevato al numero di anni.

## 9. I bandi adatti

Per ogni bando studiato QUANTO fa questi controlli sull'azienda:
- **Apertura**: stato dichiarato, scadenza letta, finestra delle regole.
- **Spese ammesse**: almeno una categoria di spesa dell'azienda è ammessa?
- **Settore**: se il bando ammette solo certi codici ATECO.
- **Territorio**: se il bando è riservato a una Regione.
- **Start-up**: se è riservato alle start-up innovative.
- **Chi può presentare domanda**: dimensione, forma giuridica (controllo informativo).

Ogni controllo vale OK (dimostrato dai dati), NO (smentito dai dati) o DA VERIFICARE (manca un dato, e si dice quale). Il risultato:
- **Adatto**: nessun NO, nessun controllo decisivo da verificare, e c'è un valore in euro;
- **Da verificare**: manca un dato decisivo o manca il valore;
- **Non adatto**: almeno un NO.

Quando una voce supera un tetto del bando (consulenze, spese generali), QUANTO dice quanto è ammissibile e quanto resta a carico.

## 10. Il piano, il potenziale massimo e il bilancio ricostruito

**Il piano** è un problema di ottimizzazione risolto con un programma matematico esatto (HiGHS). Per ogni spesa decide quale fondo la paga e in che quota, rispettando:
- ogni spesa non è coperta oltre il 100%;
- il tetto di ogni fondo;
- i massimali per categoria (consulenze, spese generali);
- i fondi non cumulabili sulla stessa spesa;
- il plafond de minimis (300.000 euro in tre anni per impresa unica);
- le finestre di attività del bando.
Il solver lavora in euro per trovare la struttura migliore; gli importi finali sono interi in centesimi, arrotondati per difetto e **ri-verificati in aritmetica esatta** contro tutti i vincoli.

Tre obiettivi: pagare il meno possibile di tasca propria (quello di default), coprire più spese possibile, usare meno fondi possibile.

**Il de minimis, in parole semplici.** È il tetto europeo agli aiuti «piccoli» (Reg. UE 2023/2831): un'impresa unica può ricevere al massimo 300.000 euro in tre anni mobili. Conta solo per i bandi che lo dichiarano; gli altri non lo toccano.

**Quali bandi sono in de minimis.** Lo dice solo una fonte: la scheda curata del bando (per esempio il fondo perduto SIMEST) oppure il testo ufficiale letto, che cita il regime o i suoi regolamenti (2023/2831, 1407/2013). Se il testo lo cita ma lo nega («non rientra nel regime de minimis»), il bando non conta e la frase si mostra. Le fonti secondarie non servono a questo. Ogni bando in de minimis porta un'etichetta con la frase da cui viene.

**Quanto ne resta all'azienda: la stima automatica.** QUANTO non legge il Registro Nazionale degli Aiuti, quindi non inserisce un numero inventato: lo calcola da ciò che l'azienda ha dichiarato nel profilo, voce «Contributi pubblici ricevuti nell'esercizio» dei tre esercizi che precedono l'anno del piano. Per prudenza ogni contributo dichiarato conta come de minimis. Il residuo è 300.000 − somma, mai sotto zero, e porta sempre la sua base: **dato dichiarato** (tutti e tre gli anni compilati), **dato parziale** (alcuni anni; per gli altri non si sottrae nulla) o **ipotesi** (nessun anno compilato: si assume che non ci siano aiuti; non è un dato verificato). Il campo si può correggere a mano; l'assistente raccoglie i dati spiegando dove trovarli (visura aiuti RNA, provvedimenti di concessione, dichiarazioni firmate; per un gruppo si sommano le società collegate). In più il piano dice quanto de minimis usa davvero: se ne usa 17.000 euro, resta valido anche se l'azienda ne ha già ricevuti fino a 283.000. Il piano non si blocca mai in attesa di questo dato.

**Il piano è sempre lo stesso e sempre il massimo.** Stessi dati, stessi bandi nel catalogo, stesso risultato, in euro e in centesimi. Quando due fondi valgono uguale su una spesa, la scelta non dipende dall'ordine in cui arrivano ma da una regola fissa: prima il valore più alto, poi (a parità) il fondo senza de minimis, poi il fondo con il tetto più alto, poi il nome. Il piano considera di default **tutti i bandi adatti** e include da solo quelli che entrano nel catalogo; cambia solo se cambiano i dati dell'azienda o il catalogo (per esempio Invitalia pubblica un bando nuovo). Se togli dei bandi a mano, il piano è un sottoinsieme e lo dice.

**Come leggere i numeri del riquadro.** «Coperto dai bandi» è quanto delle spese dell'anno pagano i bandi (due cifre: scenario prudente e massimo con tutte le maggiorazioni); «Su una spesa di» è la spesa prevista; «Quota coperta» è il rapporto tra le due; «Resta a tuo carico» è il resto. Nella tabella «Da solo» è ciò che darebbe ogni bando se fosse l'unico, «Nel piano insieme» ciò che serve davvero quando lavorano insieme. Gli scarti di pochi centesimi sono arrotondamenti: il piano lavora in centesimi interi, sempre per difetto. La legenda è sempre visibile sotto i risultati.

**Cosa mostrano i grafici.** Tutti i bandi del piano compaiono in legenda e in tabella, ognuno con il suo colore (12 colori). Un bando che non porta euro in più è indicato «non serve»: la sua spesa è già coperta da un bando più conveniente (una spesa riceve un solo fondo perduto) o ha raggiunto il suo tetto. Non è scartato e rientra da solo se i dati cambiano.

**Il potenziale massimo** combina tutti i bandi adatti. Regola di prudenza: due contributi a fondo perduto non si sommano sulla stessa spesa, quindi ogni voce riceve un solo contributo, il migliore. Garanzie, interessi e risparmi fiscali invece possono convivere. Il piano si calcola due volte: con le percentuali prudenti e con le percentuali massime, e si mostra l'intervallo.

Esempio (azienda di prova, spesa 1.965.919 euro): da 1.307.746 a 1.863.062 euro coperti (66,5% e oltre), con 8 bandi. Sommando i bandi uno per uno si arriverebbe a 2.394.221 euro: la differenza è la stessa spesa che non si può pagare due volte.

**Il bilancio ricostruito** è un grafico: per ogni categoria di spesa, quanto copre ciascun bando e quanto resta a carico.

Il valore è un massimo teorico: parte dalla spesa prevista come se fosse tutta progetto. Nota professionale da riportare al cliente: l'esito reale dipende dall'istruttoria e dalle risorse disponibili.

## 11. La bozza di budget dal profilo e i pacchetti di lavoro

**La bozza di budget** si costruisce sull'azienda, non copiando l'ultimo bilancio. Il **personale è persona per persona**: dall'organico letto nei documenti (registro del personale in Excel e buste paga) ogni dipendente diventa una voce con livello, contratto, retribuzione annua lorda e quota di tempo sul progetto. Le **altre spese sono voci precise** (affitti, energia, licenze software, trasferte…), ognuna con la sua fonte: il budget dell'azienda per l'anno del progetto se è stato caricato, il piano degli investimenti per gli acquisti di beni, altrimenti la previsione dal bilancio. L'**ammortamento non entra**: è il costo di beni già acquistati. Tiene le voci che il bando ammette (quelle che esclude per nome restano fuori), applica la quota di progetto che scegli (per esempio 50% della spesa annua e del tempo di ogni persona) e riduce le voci sopra i tetti. Ciò che manca (investimenti previsti, tabella di un contratto) è scritto nell'elenco «cosa manca».

**Dall'allocazione ai budget dei bandi**: dopo l'allocazione su più bandi, «Crea i budget dei bandi» ricava il budget di ognuno, controllato con i suoi 60 criteri e verificato insieme agli altri (nessuna persona oltre il 100% del tempo, nessun cumulo vietato, de minimis rispettato). Si aprono nella pagina Budget uno alla volta.

**Come si accede a un bando (non tutti chiedono un progetto)**: nella scheda di ogni bando, «Progetti e voci di spesa», QUANTO dice con quale modalità si accede, con un esempio e la frase del testo che lo prova.

| Modalità | Esempio | Su cosa si calcola | Le spese correnti sono una base valida? |
|---|---|---|---|
| Progetto o investimento | ricerca e sviluppo, Smart&Start | le spese nuove del progetto | solo per forma (spese generali a forfait, personale realmente dedicato) |
| Credito d'imposta automatico | iperammortamento, Transizione 5.0 | gli acquisti qualificati dell'anno | no: contano i beni acquistati |
| Garanzia e liquidità | Fondo di garanzia PMI | il finanziamento bancario da garantire | sì: serve il fabbisogno di cassa |
| Occupazione | incentivi alle assunzioni | le persone assunte e i loro requisiti | no: contano le assunzioni |
| Spese commerciali | SIMEST: fiere, e-commerce, export | le spese commerciali del programma | sì, se sostenute per il programma e dopo la domanda |
| Ristoro | caro energia, crisi | i dati storici di bilancio | sì: si calcola sui bilanci |

Esempio semplice: un'azienda spende ogni anno 20.000 € di fiere. Con SIMEST sono una base valida; con un bando di ricerca no (serve un progetto nuovo); con il Fondo di garanzia non conta nessuna delle due.

**Spese dell'anno e Un progetto: i due scenari dell'Allocazione.** La pagina mostra un solo **Risultato**, con un interruttore a due posizioni, perché i bandi sono di due famiglie diverse e non vanno mescolati. **Spese dell'anno**: le spese che l'azienda sostiene comunque (personale, affitti, licenze…), coperte dai bandi che **non chiedono un progetto**: crediti d'imposta automatici, spese commerciali, incentivi alle assunzioni. **Un progetto**: spese nuove e straordinarie (un investimento, una ricerca), coperte dai bandi che **finanziano progetti**. Un bando a progetto non paga le spese correnti, quindi non entra nelle spese dell'anno: nella sua scheda c'è scritto «Finanzia le spese nuove di un progetto» e, al posto dell'importo, i progetti possibili. «Includi nel piano» e «Includi nel progetto» sono la stessa spunta: decide quali bandi entrano nel calcolo dello scenario che stai guardando, e le due scelte restano separate (passare da uno scenario all'altro non cancella nulla). Esempio: con le sole spese dell'anno, 2 bandi coprono 148.000 € su 2,1 milioni (7%); il progetto «Rinnovo dei beni a fine vita» ha un suo calcolo, con i bandi che finanziano progetti come questo.

**Da dove nascono i progetti, e cosa succede se per un bando non ce n'è.** Le idee di progetto nascono dai documenti dell'azienda (piano degli investimenti, beni a fine vita, piano delle assunzioni, formazione, promozione, energia). Ogni idea elenca i bandi che finanziano quel tipo di progetto, e ogni bando a progetto mostra le idee collegate. Se per un bando a progetto i tuoi documenti non suggeriscono nessuna idea adatta, QUANTO non ne inventa: lo scrive («nessun progetto tra quelli proposti») ed elenca quei bandi nella sezione Progetti; serve un progetto scritto dal cliente.

**Idee di progetto**: nell'Allocazione, il passo «Idee di progetto e misure senza progetto» è facoltativo (senza, il piano parte dalle spese annuali dell'azienda). Propone progetti ricavati dai documenti: investimenti già in programma, beni a fine vita, assunzioni previste, formazione, promozione. Ogni spesa è **nuova** (la causa il progetto), **corrente** (l'azienda la sostiene già: valida o no a seconda del bando) o **da quantificare** (serve un preventivo). Sono ipotesi da validare con l'imprenditore. Esempio: il piano delle assunzioni prevede un data engineer a settembre: l'idea dice che mancano RAL e livello e propone i bandi per l'occupazione, che chiedono contratto e DURC, non un progetto. Il costo del personale si rendiconta sulle ore realmente dedicate e alla retribuzione vera: il controllo 15 la confronta con la busta paga.

**Preventivi**: se hai caricato il preventivo di un fornitore per un acquisto previsto, l'idea di progetto usa l'importo del preventivo (il più basso se sono più d'uno) al posto di quello del piano, e lo scrive con il fornitore e la validità. Un preventivo scaduto non si usa e viene segnalato. Esempio: il piano prevede 45.000 € di infrastruttura cloud; il preventivo di Nuvola Datacenter è di 48.600 €: l'idea mostra 48.600 € e ricorda che il piano diceva 45.000 €.

**Quanto vale davvero, e quando incassi** (passo 8 dell'Allocazione): un contributo nominale non è un incasso. Per ogni bando del piano scrivi la probabilità di successo, il costo di istruttoria e la percentuale del consulente (anche zero): QUANTO non li inventa, e senza mostra solo il nominale. Con le ipotesi calcola il valore atteso e il netto, e la probabilità sopra la quale conviene. Anticipo e mesi di rimborso si leggono dal bando se le sue regole sono pubblicate; li puoi correggere. Poi mostra mese per mese quanto l'azienda deve anticipare (le spese si pagano subito, i contributi arrivano dopo) e quali altri aiuti già presi (credito d'imposta ricerca e sviluppo, altri aiuti del registro) si sommano. Esempio: contributo di 60.000 €, probabilità 50%, consulente 10%, istruttoria 3.000 €: ci si può contare per 30.000 €, tolti 3.000 € di consulente e 3.000 € di istruttoria restano 24.000 €. Un secondo bando da 30.000 € con probabilità 20% e istruttoria 8.000 € vale 6.000 € e costa 8.000 €: non conviene alle ipotesi indicate.

**Livelli di contratto mancanti** (area riservata, Fonte B): se una persona ha un livello che non è in tabella, il controllo del suo costo orario resta in attesa e la bozza di budget lo scrive. Se tutti i livelli già pubblicati di quel contratto hanno gli stessi parametri (ore, oneri, TFR), il manager può preparare una **bozza** che aggiunge i livelli mancanti con gli stessi valori. La bozza non conta nei calcoli finché il manager non la controlla sul testo del contratto e la pubblica attestandolo. Se i livelli pubblicati hanno parametri diversi non si deduce nulla: la tabella va caricata dal contratto. Esempio: COMMERCIO ha i livelli 3 e 4 con 1.680 ore, 29,5% e 8,33%; manca il 5: si prepara la bozza con 1.680 ore, 29,5% e 8,33% anche per il 5, il manager verifica sul contratto e pubblica.

**Voci escluse lette dal testo**: se il testo di un bando dice che una voce non è ammissibile, QUANTO propone l'esclusione ma **non la attiva da sola**: va in revisione e la conferma una persona nel Quartier Generale. Una voce letta male toglierebbe soldi ammessi.

**L'azienda di prova si aggiorna da sola**: chi ha già caricato l'azienda di prova la trova all'ultima versione aprendo la pagina dei documenti (i file nuovi o cambiati si caricano da soli, quelli tolti dal set di prova si eliminano). A chi non l'ha mai caricata non viene caricato nulla.

**De minimis e impresa unica**: nel Profilo, «Aiuti ricevuti, impresa unica e registro nazionale». Si rispondono cinque domande sui legami con altre imprese, si elencano le imprese collegate, e per ognuna (la tua azienda e le collegate) si riportano le concessioni della visura aiuti ufficiale dell'RNA con la data di consultazione. QUANTO le confronta con i documenti, calcola il residuo del triennio sommando tutte le imprese e, finché la verifica non è completa e recente (30 giorni), usa nel piano un residuo ridotto del 10% del tetto. La visura aiuti, se la carichi come documento, viene letta da sola (data, misura, regime, importo, COR) e confrontata con il registro e con la dichiarazione de minimis; se la dichiarazione dice che l'impresa non è collegata ad altre, QUANTO propone «No» a tutte e cinque le domande, ma la risposta resta tua. La verifica si attesta; non sostituisce la dichiarazione firmata dal legale rappresentante. Esempio: l'azienda risulta aver ricevuto 16.500 €, ma la visura mostra anche 40.000 € di una controllata: l'impresa unica ne ha già usati 56.500, e finché la visura non è caricata e recente il piano usa 270.000 € invece di 283.500.


**I pacchetti di lavoro (WP)**: se il bando divide il lavoro in WP, QUANTO assegna ogni voce ammessa a un WP rispettando le quote minime e massime di ogni WP, le categorie ammesse e i tetti per categoria dentro ogni WP, e si avvicina alle quote desiderate. È un programma lineare misto-intero. Esempio: 100.000 euro di voci con WP al 50/30/20%: a voci intere lo scostamento è di 10, 5 e 5 punti; dividendo una sola voce scende a zero. I vincoli dei WP li dichiara chi sa come il bando divide il lavoro: non si leggono dal testo.

**I video.** Il video di presentazione (circa 40 secondi) è nella pagina iniziale. I 17 video tutorial stanno nella pagina del loro strumento, come una scheda con la locandina che si apre al clic: nel Profilo «Lo studio e i lavori» e «I documenti diventano dati»; in Bandi «Il catalogo» e «Studiare un bando»; nell'Allocazione, dentro ogni passo, la stima, i bandi adatti, il valore in euro, il risultato, i progetti, il valore reale e gli incassi, i budget dei bandi; nel Budget «Il budget e i 60 criteri»; in Verifica «Il registro firmato»; nel Confronto «I template»; accanto all'assistente «L'assistente guidato». Tutti sono raccolti in Guida → Video, e il percorso completo in 9 passi è in Guida → Percorso rapido. I numeri nei video sono esempi con l'azienda di prova fittizia.

## 12. Il budget e i 60 criteri

**Come nasce un budget, in quattro passi.** (1) **Leggo il bando**: dai testi ufficiali ricavo le regole (percentuali, tetti, voci escluse, date). I 60 criteri sono una lista fissa, uguale per tutti i bandi; **36 funzionano sempre** perché guardano solo i dati della voce (per esempio il calcolo del costo orario di una persona, l'IVA, l'ammortamento, i metodi di pagamento), **24 dipendono da una regola del bando** (per esempio il tetto sul costo orario, il tetto percentuale sulle consulenze, la data da cui le spese sono ammesse, il plafond de minimis, la non cumulabilità). Ogni regola letta accende i suoi criteri; se il bando non dà una regola, quei criteri restano spenti e sulle voci risultano **«non valutato»**, mai «superato». Nella pagina Bandi, scheda «Controlli attivati», una griglia di 60 quadratini mostra per ogni bando quali sono accesi dalle sue regole, quali girano solo sui dati e quali sono spenti. Esempio: un bando che dichiara «le consulenze non superano il 20% del totale» accende il criterio 31; un bando che non dice nulla sulle consulenze lo lascia spento, e la sua riga di consulenza risulta «non valutata» su quel punto. (2) **Preparo la bozza** dai documenti dell'azienda: ogni persona con livello e RAL, le spese una per una; lascio fuori ciò che il bando non ammette e riduco ciò che supera i tetti. (3) **Controllo con i 60 criteri**: i criteri guardano il **budget**, non il bando (il bando fornisce le regole, il budget è ciò che si controlla); ogni voce risulta ammessa, ridotta, respinta o in attesa di un documento, con il motivo, e il controllo si ripete da solo a ogni modifica. (4) **Correggi e registra**: sistemi le voci segnalate, poi esporti e registri il budget con un'impronta firmata. Se per quel bando e quella nicchia esistono template (pagina Confronto), il consiglio suggerisce come ripartire il budget; se non ce ne sono, la bozza parte solo dai dati dell'azienda e QUANTO lo dice. **QUANTO non promette un budget «vincente»**: lo rende ammissibile e coerente con le regole; se il bando sarà vinto dipende dal progetto e dagli altri candidati, e la graduatoria non è prevedibile.

**Allocazione e budget.** L'allocazione decide quale bando paga quale spesa; non è un budget. Dopo l'allocazione, «Budget dei bandi» ricava **un budget per ogni bando** del piano (ognuno ha le sue regole e si presenta a parte, quindi non esiste un budget unico) e li verifica anche insieme: nessuna persona oltre il 100% del tempo, nessun cumulo vietato, de minimis rispettato. Nella pagina Budget i budget del piano compaiono come una barra di schede, una per bando. **«Esci dal gruppo»** (prima «Chiudi il gruppo») non unisce né calcola nulla: toglie la barra e ti lascia a lavorare su **un solo budget**, quello che hai aperto; gli altri escono dalla barra e le modifiche non salvate si perdono (con una conferma). Per riaverli: Allocazione → «Budget dei bandi». Esempio: tre bandi del piano annuale danno tre budget; salvi o esporti ognuno per il suo bando; «Esci dal gruppo» serve solo se vuoi lavorare su uno di essi senza la barra.

Quando premi «Controlla il budget», il motore applica i 60 criteri a ogni voce e poi guarda il budget intero. Un criterio gira solo se il bando dichiara la regola e la voce ha il dato: altrimenti risulta «non valutato», mai «superato». Per ogni voce l'esito è ammessa, ridotta, respinta, in attesa di documento o non valutata, con il motivo e la fonte della regola. Il file «I 60 criteri spiegati» descrive ogni criterio con un esempio.

Esempio: tetto consulenze 20% del totale ammissibile. Inserisci 30.000 euro di consulenze con altre spese per 70.000: ne vengono ammessi 17.500, perché 17.500 è il 20% di 87.500 (70.000 più 17.500).

## 13. Il registro firmato

Ogni budget controllato può lasciare un'impronta (radice di Merkle: una sola impronta che riassume tutte le righe). L'impronta entra in un registro dove si può solo aggiungere: ogni riga contiene l'impronta della precedente e una firma. Cambiare il passato rompe la catena. La voce n. 1 del registro non si può cancellare, per costruzione. Un revisore può verificare un budget con la chiave pubblica, anche senza accedere ad altro.

## 14. Il Confronto: i template e come l'algoritmo impara

### 14.1 A cosa serve
Il Confronto risponde a una domanda da commercialista: «Per un'azienda di questa nicchia, che sceglie questo bando, com'è fatto di solito il budget che vince?». La risposta nasce dai template che salvi tu (e, se condivisi, da quelli degli altri).

### 14.2 Cos'è un template
Un template è una scheda con:
- la **nicchia**: il codice ATECO dell'azienda (per esempio 01.11 = coltivazione di cereali; la nicchia è identificata dalle prime due cifre e dal settore: Agricoltura, Manifattura, Informazione e comunicazione...);
- il **bando** scelto;
- la **ripartizione del budget** in otto voci: personale, beni strumentali, consulenze, ricerca e sviluppo, spese generali, formazione, comunicazione, altro. Devono sommare 100%;
- l'**esito**: bozza, presentato, ammesso, non ammesso (e, se vuoi, il punteggio);
- dimensione, Regione, importo del budget e una nota.

Esempio: un'azienda agricola sceglie un bando e costruisce un budget con il 13% in consulenze, il 16,1% in ricerca e sviluppo, il 45% in beni strumentali, il resto in personale, spese generali, formazione e comunicazione. Il commercialista lo salva come template con esito «presentato».

### 14.3 Come nasce il consiglio
Quando chiedi il budget consigliato per una nicchia e un bando, QUANTO cerca i template simili su sei livelli, dal più preciso al più generale:
1. stessa nicchia e stesso bando;
2. stesso settore e stesso bando;
3. stesso bando;
4. stessa nicchia;
5. stesso settore;
6. tutti i template.
Usa il **primo livello che ha almeno 3 template**. Se nessuno ne ha 3, dice «ancora pochi dati» e non inventa nulla.

Poi fa una **media pesata**: ogni template pesa secondo l'esito.

| Esito | Peso |
|---|---|
| Ammesso | 3 |
| Presentato | 1,5 |
| Bozza | 1 |
| Non ammesso | 0,25 |

Esempio numerico: tre template della stessa nicchia e dello stesso bando, quota consulenze 20% (ammesso), 5% (non ammesso), 13% (bozza). Media pesata = (3 × 20% + 0,25 × 5% + 1 × 13%) / (3 + 0,25 + 1) = 17,5%. Senza pesi sarebbe il 12,7%: il budget che ha vinto trascina il consiglio.

Il consiglio comprende anche:
- l'**intervallo tipico** per ogni voce (media più o meno la dispersione dei template): dove c'è più libertà e dove no;
- il **livello di fiducia**: ALTA se si usa il livello 1 con almeno 8 template; MEDIA se si usa il livello 1, 2 o 3 (c'è un bando preciso); BASSA se si usano solo livelli generici;
- gli **stili di budget**: con almeno 6 template, un raggruppamento automatico (k-means con seme fisso, quindi ripetibile) trova gruppi di budget simili e dice quanti di ciascun gruppo hanno vinto; se i gruppi non sono ben separati, non si inventano stili;
- una **spiegazione** in frasi: quanti template, quanti ammessi, quali voci pesano di più.

### 14.4 Come l'algoritmo si auto-migliora
Non c'è un addestramento notturno né una «scatola nera»: il consiglio si ricalcola ogni volta, da tutti i template, quindi **migliora da solo a ogni dato nuovo**. In concreto:
1. **Più template, livello più preciso.** Con 2 template della stessa nicchia e dello stesso bando QUANTO scende a un livello più generale (stesso settore, o tutti) e la fiducia è bassa; con 3 template arriva il consiglio preciso (fiducia media); con 8 diventa alta.
2. **Gli esiti spostano il consiglio.** Quando il bando risponde, aggiorni l'esito del template. Se un budget passa da «presentato» ad «ammesso», il suo peso sale da 1,5 a 3 e il consiglio si sposta verso quel budget. Se passa a «non ammesso», il peso scende a 0,25.
3. **Misura onesta.** Ogni volta che salvi un template, QUANTO registra a quanta distanza era dal consiglio che c'era in quel momento (metà della somma degli scarti, da 0 a 100%). Quando ci sono almeno 5 esiti noti tra i budget vicini al consiglio (scarto fino al 10%) e almeno 5 tra gli altri, QUANTO mostra se i budget vicini vincono più spesso. Finché i dati non bastano, lo dice.
4. **Riproducibile.** Ogni consiglio porta l'impronta dei template usati: stessi template, stesso consiglio.

Esempio: un commercialista lavora con aziende agricole. Mese 1: salva 3 template: fiducia media. Mese 6: ne ha 9, 4 ammessi: fiducia alta, intervalli più stretti, e due stili («beni strumentali» e «consulenze»), con 4 ammessi sul primo. Un nuovo cliente agricolo sceglie lo stesso bando: il consiglio mostra una ripartizione di partenza basata su 9 casi reali.

### 14.4 bis Gli esempi di partenza nel motore collettivo
All'inizio i budget reali sono pochi, quindi il motore collettivo contiene **48 template di esempio**: per ogni bando con regole pubblicate (Horizon Europe, FVG, Smart&Start, SIMEST, Iperammortamento, Sabatini, Investimenti sostenibili 4.0) ci sono ripartizioni del budget per nicchie ATECO plausibili, **controllate con le regole di quota di quel bando**: categorie ammesse, tetto sulle consulenze, forfait sulle spese generali. Il risultato è «conforme», «conforme con riduzioni» (il motore taglierebbe una parte) o «non conforme» (una voce non è ammessa). Ci sono anche casi non conformi: servono per imparare cosa evitare.

Non sono budget di aziende reali e non hanno un esito di bando: «conforme» non vuol dire «ammesso». Per questo nel Confronto compaiono come «esempi» (per esempio «3 reali + 5 esempi»), non contano come ammessi, pesano la metà e, quando in un gruppo ci sono 8 template reali, non contano più. Con soli esempi la fiducia è sempre bassa. Il motore interno non li usa. Il titolare può vederli, ricrearli o toglierli dal Quartier Generale.

Esempio: scegli Smart&Start e la nicchia software. Prima, senza dati, il Confronto diceva «ancora pochi dati». Ora mostra un consiglio di partenza (beni poco sotto la metà, personale circa un quarto, consulenze circa un quinto) basato su 3 esempi, con fiducia bassa. Man mano che salvi budget veri, il consiglio si sposta verso di loro.

### 14.5 La mappa nicchie e bandi
Mostra, per ogni nicchia, quali bandi hanno scelto i clienti, con la ripartizione media, quanti sono stati presentati e quanti ammessi. Serve a vedere a colpo d'occhio «che cosa fanno le aziende agricole» o «che cosa fanno le imprese informatiche».

### 14.6 I due motori e la privacy
Lo studio sceglie con quale motore confrontarsi:
- **Motore collettivo**: lavora sui template **pubblicati per tutti**, in forma anonima: così l'algoritmo si auto-migliora con i dati di tutti. Pubblicare è la scelta predefinita e regala 0,5 token (una volta per cliente e bando, al massimo 10 al mese); chi preferisce può tenere un template «solo nello studio»: allena soltanto il motore interno, e lo si può pubblicare dopo dall'elenco.
- **Motore interno**: lavora solo sui template del tuo studio. Serve a vedere come lavora il tuo studio, senza influenze esterne.
L'elenco dei template dello studio è sempre visibile (con il cliente da cui vengono) e lì si aggiorna l'esito. I template contengono solo nicchia, bando, Regione, dimensione, quote ed esito: ragione sociale e partita IVA non vengono nemmeno salvate. La nota libera resta dello studio e l'algoritmo non la usa. Dei template degli altri studi si usano solo gruppi di almeno 3: sotto questa soglia non entrano, così nessuno può risalire a un singolo cliente. Nel Confronto compaiono solo i bandi affini al lavoro attivo (stesso criterio dell'Allocazione); chi ha partecipato a un bando diverso lo cerca per nome.

### 14.7 Nota professionale
Il consiglio è una statistica sulla struttura della spesa, non una previsione di esito. Non sostituisce la verifica dei requisiti formali con la documentazione del cliente.

## 15. Il Quartier Generale

L'area riservata al titolare dell'account. Contiene: panoramica con i contatori; timeline di ogni operazione; mappa delle operazioni; archivio dei bandi (ogni documento scaricato con testo e file originale, regole e requisiti modificabili, rilettura, esportazione, eliminazione); catalogo; tabelle ufficiali (CCNL e simili, versionate per data); utenti; esplora del database (sola lettura per il registro firmato, che non si può toccare); questo manuale.

### 15.1 L'assistente guidato

Dove l'utente dovrebbe inserire dati o muoversi nell'app, può affidare il lavoro all'assistente (pulsante «Assistente» nel menu, oppure «Fallo fare all'assistente» nei punti in cui serve). È una **chat**: si scrive cosa si vuole fare (per esempio «prepara la bozza di budget», «calcola il potenziale massimo», «dichiara gli aiuti ricevuti») oppure si sceglie uno dei suggerimenti sopra la barra di scrittura. L'assistente capisce la richiesta con parole chiave, non è un modello linguistico, e se non capisce lo dice. L'app si riduce a sinistra, in una scheda con gli angoli arrotondati, con sotto due pillole (il passo in corso e «Interrompi»); a destra, sullo sfondo giallo sfumato, compare la chat con l'elenco di **tutti i passaggi**, che si spuntano man mano. Mentre l'assistente lavora l'app si muove da sola (cambia pagina, salva, calcola) e non si può toccare. Quando manca un dato lo chiede nella chat, e per ogni campo spiega in parole semplici **cos'è, cosa scrivere, perché serve, dove si trova e un esempio**. Si può interrompere in qualsiasi momento con «Interrompi», scrivendo «annulla» o chiudendo, e riprendere da soli.

Le attività: **calcolare il potenziale massimo** (controlla i dati, chiede quelli che mancano, stima l'anno, cerca i bandi adatti, verifica il de minimis, mostra il risultato); **preparare la bozza di budget** (sceglie il bando, la quota di progetto, crea la bozza dall'azienda con le persone già dentro, chiede le persone una per una con ruolo, CCNL, livello, RAL, quota di tempo e mesi solo se nei documenti non ci sono, e controlla il budget con i 60 criteri); **dichiarare gli aiuti già ricevuti**; **completare i dati dell'azienda**. L'assistente esegue solo le azioni che farebbe l'utente e non inventa mai un dato: usa ciò che l'utente scrive o che è già nel profilo. Se una tabella necessaria non esiste (per esempio nessun CCNL pubblicato) lo dice e salta il passaggio, senza scegliere al posto dell'utente.

## 16. Quello che QUANTO non fa

- Non scrive il progetto né il testo di una candidatura.
- Non prevede l'esito di un bando: il Confronto è una statistica, il potenziale è un massimo teorico.
- Non somma garanzie e contributi.
- Non usa percentuali da fonti non ufficiali.
- Non carica bandi da testo libero: i bandi si studiano dal catalogo con il processo standard (il caricamento manuale di documenti è riservato all'operatore nel Quartier Generale).

## 17. Glossario in parole semplici

- **Aliquota / intensità**: la percentuale delle spese che il bando rimborsa.
- **Fondo perduto**: soldi che non si restituiscono.
- **ATECO**: il codice che dice di che settore è l'azienda.
- **Nicchia**: un gruppo di aziende dello stesso settore (stesse prime due cifre ATECO).
- **De minimis**: un tetto agli aiuti piccoli: 300.000 euro in tre anni per impresa unica.
- **CUP**: il codice che identifica un progetto finanziato con soldi pubblici.
- **Impronta (hash)**: un codice che cambia se cambia anche una sola cifra.
- **Template**: la scheda di un budget con nicchia, bando ed esito.
- **Fiducia**: quanto è solido un consiglio, in base a quanti template lo sostengono.
