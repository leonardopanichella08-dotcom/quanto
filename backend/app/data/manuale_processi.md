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

## 7. Il profilo dell'azienda e i documenti

**I documenti** (visura, bilanci, buste paga, F24, bozze di candidatura, altri file) si caricano nel Profilo. Il lettore trasforma ogni file in campi e per ogni campo dice quanto è sicuro: AUTO (sicuro), da verificare, confermato, corretto. Entrano nei calcoli solo i campi sicuri o confermati da una persona; i campi incerti restano da controllare e il totale dell'anno viene segnalato come parziale finché non si verificano.

**Da dove viene ogni dato.** Ogni valore ricorda se viene da un documento (con quale), se è stato scritto a mano o se è derivato (per esempio la regione dalla provincia). Un valore scritto a mano non viene mai sovrascritto da una nuova lettura. Se un documento viene eliminato, i valori che ne venivano decadono.

**La dimensione dell'impresa** (micro, piccola, media, grande) si ricava da dipendenti e fatturato con le soglie europee. È indicativa: non guarda il totale di bilancio né le imprese collegate.

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

**Il potenziale massimo** combina tutti i bandi adatti. Regola di prudenza: due contributi a fondo perduto non si sommano sulla stessa spesa, quindi ogni voce riceve un solo contributo, il migliore. Garanzie, interessi e risparmi fiscali invece possono convivere. Il piano si calcola due volte: con le percentuali prudenti e con le percentuali massime, e si mostra l'intervallo.

Esempio (azienda di prova, spesa 1.965.919 euro): da 1.307.746 a 1.863.062 euro coperti (66,5% e oltre), con 8 bandi. Sommando i bandi uno per uno si arriverebbe a 2.394.221 euro: la differenza è la stessa spesa che non si può pagare due volte.

**Il bilancio ricostruito** è un grafico: per ogni categoria di spesa, quanto copre ciascun bando e quanto resta a carico.

Il valore è un massimo teorico: parte dalla spesa prevista come se fosse tutta progetto. Nota professionale da riportare al cliente: l'esito reale dipende dall'istruttoria e dalle risorse disponibili.

## 11. La bozza di budget dal profilo e i pacchetti di lavoro

**La bozza di budget** parte dall'ultimo bilancio: tiene le categorie ammesse dal bando, applica la quota di progetto che scegli (per esempio 50% della spesa annua) e riduce le voci sopra i tetti. Il costo del personale non entra come voce unica: il motore lo vuole persona per persona (livello, contratto, retribuzione annua lorda, quota di tempo).

**I pacchetti di lavoro (WP)**: se il bando divide il lavoro in WP, QUANTO assegna ogni voce ammessa a un WP rispettando le quote minime e massime di ogni WP, le categorie ammesse e i tetti per categoria dentro ogni WP, e si avvicina alle quote desiderate. È un programma lineare misto-intero. Esempio: 100.000 euro di voci con WP al 50/30/20%: a voci intere lo scostamento è di 10, 5 e 5 punti; dividendo una sola voce scende a zero. I vincoli dei WP li dichiara chi sa come il bando divide il lavoro: non si leggono dal testo.

## 12. Il budget e i 60 criteri

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

### 14.5 La mappa nicchie e bandi
Mostra, per ogni nicchia, quali bandi hanno scelto i clienti, con la ripartizione media, quanti sono stati presentati e quanti ammessi. Serve a vedere a colpo d'occhio «che cosa fanno le aziende agricole» o «che cosa fanno le imprese informatiche».

### 14.6 Privacy
I template sono tuoi. Se spunti «condividi in forma anonima», il template entra nel campione di tutti, senza ragione sociale né partita IVA (non vengono nemmeno salvate): contiene solo nicchia, bando, Regione, dimensione, quote ed esito.

### 14.7 Nota professionale
Il consiglio è una statistica sulla struttura della spesa, non una previsione di esito. Non sostituisce la verifica dei requisiti formali con la documentazione del cliente.

## 15. Il Quartier Generale

L'area riservata al titolare dell'account. Contiene: panoramica con i contatori; timeline di ogni operazione; mappa delle operazioni; archivio dei bandi (ogni documento scaricato con testo e file originale, regole e requisiti modificabili, rilettura, esportazione, eliminazione); catalogo; tabelle ufficiali (CCNL e simili, versionate per data); utenti; esplora del database (sola lettura per il registro firmato, che non si può toccare); questo manuale.

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
