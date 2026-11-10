# I tre agenti di QUANTO: Agevolazioni, Allocazione, Confronto

*9 novembre 2026. Scritto dopo aver riletto il codice di ogni passaggio. Le parti marcate **[OGGI]** descrivono ciò che il portale fa adesso (verificato sul codice, con i numeri veri). Le parti marcate **[NUOVO]** sono la proposta: non è ancora costruita.*

---

## 0. In breve

- Oggi Agevolazioni, Allocazione e Confronto sono **tre pagine**: ognuna lavora quando l'utente preme un tasto e poi si ferma.
- Diventano **tre agenti**: ognuno ha **un compito suo**, **una memoria sua** nel datacenter, **un momento in cui lavora da solo** (ogni notte o quando arriva un dato nuovo) e **un contratto chiaro** con gli altri due.
- Restano **deterministici**: nessun numero inventato, nessun modello linguistico che «indovina» cifre, ogni importo con la sua fonte. «Agente» qui vuol dire *chi si occupa di una cosa, la tiene aggiornata e ricorda com'è andata*, non «un'intelligenza che decide da sola».
- Il guadagno è triplo: **più veloci** (si calcola una volta e si riusa), **più chiari per chi lavora** (ogni agente dice «cosa ho fatto, cosa ho trovato, cosa mi serve da te»), **datacenter che cresce con l'uso** (ogni lavoro lascia dati utili a tutti, in forma anonima).

In una riga ciascuno:

| Agente | Domanda a cui risponde | Oggi |
|---|---|---|
| **Agevolazioni** | «Per questa impresa e per le persone che vuole assumere, quali sgravi e incentivi senza bando valgono, e quanto?» | `measures.py` |
| **Allocazione** | «Tra tutti i bandi, quali sono davvero per questa impresa, come li combino sulle sue spese, quanto posso contarci e quando incasso?» | `matching.py`, `allocation_engine.py` e altri 9 file |
| **Confronto** | «Per questo bando e questo settore, com'è fatto un budget che funziona, e il mio quanto se ne discosta?» | `template_learning.py` |

---

## 1. La macchina comune: come funziona il portale, in sette passi

Prima dei tre agenti, la catena che li alimenta tutti. Ogni passo è **un'idea semplice**.

### Passo 1. Raccogliere: da dove arrivano i bandi
**Cosa fa.** Ogni notte il sistema cerca bandi nuovi. Non usa un motore di ricerca: va **direttamente sui siti ufficiali**.
- **90 fonti** (`official_sources.py`): 16 ministeri e dipartimenti, 18 agenzie e fondi (Invitalia, SIMEST, INPS, ISMEA…), 3 sistemi camerali, 7 fonti UE, 46 Regioni e finanziarie regionali.
- **Due mappe di sito** (`discovery.py`): incentivi.gov.it e Invitalia, circa 6.000 voci in tutto.
- Dalla pagina dell'ente prende i collegamenti il cui testo nomina un *bando, avviso, contributo, voucher, incentivo, finanziamento*. Il **nome del bando è il testo esatto del collegamento**: date, importi e requisiti non si scrivono mai dal nome.
- Scarta: gare d'appalto, concorsi, graduatorie, delibere, bandi per i Comuni, edizioni passate, nomi di sezione («Bandi e avvisi»), notizie di servizio.
- Se un sito non risponde o costruisce l'elenco con JavaScript (illeggibile da un server), lo **dice** nello stato della fonte. Nessuna voce inventata.

**Esempio.** Dalla pagina di una Regione il raccoglitore trova «Avviso Voucher Digitalizzazione PMI 2026» → entra nel catalogo con quel nome esatto, ente «Regione X», regione X. «Consulta qui l'Avviso» viene scartato: non è un nome.

### Passo 2. Leggere la scheda
Per ogni voce nuova si legge la pagina ufficiale (`catalog_meta.py`): titolo, descrizione, forma dell'agevolazione, costi ammessi, dimensione, regioni, ATECO, soggetti ammessi, date. Se la pagina **non «parla come un bando»** (meno di 3 espressioni tipiche tra *beneficiari, spese ammissibili, dotazione, presentazione delle domande, a fondo perduto, scadenza…*), la voce è scartata.

### Passo 3. Studiare a fondo
Una scheda non basta per i calcoli. «Studiare» un bando (`pipeline.py`, standard **RICERCA-v2**) dura da pochi secondi a circa mezzo minuto:
1. **Cerca** le pagine e i PDF ufficiali.
2. **Scarica** fino a 8 documenti, 6 alla volta, e fino a 3 giri di collegamenti (allegati, decreti).
3. **Legge** con regole fisse (`requirements_extractor.py`, `benefit_extract.py`): tetti, soglie, percentuali, requisiti. Ogni cifra resta legata alla frase da cui viene.
4. **Valuta**: COMPLETA, PARZIALE o INSUFFICIENTE, con l'elenco delle lacune.

Le percentuali si leggono **solo da testi ufficiali**, mai da blog. Se lo stesso testo dà due valori diversi per la stessa regola, **non se ne pubblica nessuno**: va a una persona.

### Passo 4. Dare un valore in euro
`valuation.py` cerca la percentuale in quest'ordine: **(1)** regola pubblicata («contributo pari al 50%»), **(2)** modello del bando curato (Nuova Sabatini, Iperammortamento, SIMEST…), **(3)** tabella di intensità del testo ufficiale. Il risultato è un **intervallo** (prudente → massimo). Una **garanzia** non è un guadagno e non si somma mai.

### Passo 5. Decidere se un bando è per questa impresa
`matching.py` + `relevance.py`: il giudizio è **ADATTO**, **DA VERIFICARE** o **NON ADATTO**. Un bando che non può riguardare l'impresa (altra regione, altro settore, soggetti che non sono imprese) è **NON ADATTO e non appare mai come possibile**.

### Passo 6. Ottimizzare la combinazione
`allocation_engine.py`: un solutore matematico esatto (HiGHS) sceglie quale fondo copre quale spesa, nel rispetto di tetti, divieti di cumulo e de minimis.

### Passo 7. Controllare e ricordare
- **60 criteri** (`deterministic_engine.py`) controllano ogni budget.
- Il **registro firmato** (hash a catena, firma Ed25519) ricorda ciò che è stato calcolato e quando.
- `events.py` registra ogni operazione.

### Le cinque regole che nessun agente può cambiare
1. Mai inventare un dato: se manca, si dice che manca e **cosa** serve.
2. Ogni numero ha la sua fonte e il suo grado di verifica.
3. Solo i bandi **ADATTI** entrano nei calcoli e nei piani; i «da verificare» non si sommano mai.
4. QUANTO **non aiuta a far passare spese ordinarie o gonfiate come spese di progetto**.
5. Stessi dati → stesso risultato (determinismo).

---

## 2. Agente Agevolazioni

### 2.1 A cosa serve
Le agevolazioni «senza bando» sono sgravi, esoneri e incentivi sul **costo del lavoro** e sull'autoimpiego: non si vince una graduatoria, si **chiedono** (all'INPS, alla Regione) e si **usano in busta paga**. Un commercialista che segue ditte individuali, società di persone e piccole srl le usa ogni giorno: assumere costa, e una parte si recupera.

### 2.2 Come lavora oggi, passo per passo **[OGGI]**

**Esempio che seguiamo.** *Azienda di esempio (numeri di scuola)*: srl con sede in **Puglia**, **8 dipendenti**, **DURC regolare**, negozio di abbigliamento. Ricavi 1.200.000 €, costo del personale 280.000 €, ricavi previsti l'anno dopo 1.440.000 € (+20%).

**Passo 1. Il catalogo delle misure.** Sono **13 misure in 6 famiglie**, scritte a mano in `measures.py`, ognuna con **fonte** e **grado di verifica**:
- **4 «SECONDARIA»** (verificate su circolari INPS riportate dalla stampa specializzata): Bonus Giovani 2026, Bonus Donne 2026, Bonus ZES 2026, Bonus Stabilizzazione 2026. Hanno cifre: tetto mensile e mesi.
- **9 «DA VERIFICARE»**: Bonus Madri, incentivi occupazione della Regione, voucher occupazionali, tirocinio Garanzia Giovani, bonus trasformazione tirocinio, apprendistato, Decontribuzione Sud, maggiorazione del costo deducibile, bandi per nuove imprese. **Nessun importo inventato**: si dice come trovarle nel catalogo e quali condizioni valgono in generale.
- `VERIFIED_ON = 2026-10-24`: la data dell'ultimo controllo editoriale.

**Passo 2. Quali dati dell'impresa servono.** Solo quelli che il profilo ha già: tipo di impresa, stato (costituita o da costituire), regione, **numero di dipendenti**, **DURC**. Se mancano, la domanda viene posta («In che regione ha sede l'impresa?») e **non si indovina**.

**Passo 3. La verifica, una misura alla volta** (`evaluate`). Le regole si applicano in quest'ordine:
1. Impresa **ancora da costituire** → «DOPO LA COSTITUZIONE» (si usa dopo, prima della prima assunzione).
2. Misura **scaduta** (`valid_to`) → «SCADUTA».
3. DURC (per gli esoneri INPS verificati): se `falso` → NON APPLICABILE; se sconosciuto → DA VERIFICARE; se vero → «DURC regolare» spuntato.
4. Bonus ZES: la sede deve essere in una delle 10 regioni della ZES unica; e **al massimo 10 dipendenti**.
5. Le misure «DA VERIFICARE» non diventano mai APPLICABILI: restano da verificare perché i parametri vanno letti nella circolare.

Stati finali: **APPLICABILE · DA VERIFICARE · NON APPLICABILE · SCADUTA · DOPO LA COSTITUZIONE**.

*Sull'esempio:* Bonus Giovani → DURC ok → **APPLICABILE**. Bonus ZES → Puglia è ZES, ma l'impresa ha 8 dipendenti (≤ 10) → APPLICABILE. Tirocinio Garanzia Giovani → **DA VERIFICARE** (i parametri sono della Regione).

**Passo 4. Quanto vale** (`value_per_hire`). Tetto mensile × mesi, **per una assunzione, al massimo**. Il tetto cresce se la sede è in ZES.
- Bonus Giovani in **Puglia** (ZES): 650 € al mese × 12 mesi = **7.800 €**, × 24 mesi = **15.600 €** (24 mesi se il giovane è «molto svantaggiato»).
- Bonus Giovani **in Lombardia** (non ZES): 500 € × 12–24 = 6.000–12.000 €.
- Bonus Donne in Puglia: 800 € × 12–24 = 9.600–19.200 €.

È un **massimo, non un incasso**: l'esonero non supera i contributi che il datore deve davvero.

**Passo 5. Non si sommano.** Gli esoneri 2026 sono **alternativi tra loro**, con la Decontribuzione Sud e con altri incentivi (testo delle circolari). Per ogni assunzione conta **un solo** esonero: il migliore. Sono invece compatibili con la maggiorazione del costo deducibile.

**Passo 6. Cosa succede quando scegli** (`selection`, `POST /profile/measures/selection`). Quando premi «Usa nell'Allocazione» la scelta si salva nel lavoro (chiave `allocation_measures`). Il motore calcola per ogni scelta:
- **entra nel totale solo se APPLICABILE** e con un importo quantificabile;
- se due esoneri sono nello stesso gruppo, **conta solo il più ricco**;
- altrimenti scrive il **motivo** («Manca un dato: DURC… Non si somma finché non è chiarito»).

Il valore è sempre indicato come intervallo minimo-massimo e dice che non è un incasso.

**Passo 7. Il collegamento con la crescita** (`growth_needs.py`). Da dove arriva «quante assunzioni»? Dal bilancio:
- ricavi per persona = 1.200.000 ÷ 8 = **150.000 €**;
- con ricavi previsti 1.440.000 € servirebbero 1.440.000 ÷ 150.000 = **9,6 persone**; ce ne sono 8 → ne mancano **1,6**, cioè **2 assunzioni** (sotto 0,5 non è un'assunzione);
- costo medio per persona: 280.000 ÷ 8 = **35.000 €** → 70.000 € l'anno;
- in quale reparto: se lo studio non lo indica, si propone **la stessa composizione di oggi** (dai ruoli del registro del personale), **dichiarata come ipotesi**; senza ruoli si chiede.
Per queste 2 persone `best_for_hires` elenca gli esoneri che valgono e quanto: Bonus Giovani in Puglia, 2 × 15.600 = **31.200 €** al massimo (15.600 € in prudenza).

**Passo 8. Le misure regionali.** Per tirocini, voucher e incentivi regionali non c'è un importo: c'è un pulsante «Cerca nel catalogo», con parole chiave (`tirocini`, `garanzia giovani`…), e i risultati passano dal **filtro di pertinenza** sull'impresa (altra regione = escluso).

### 2.3 Cosa ho trovato studiandolo: i limiti veri **[OGGI]**

1. **Due esoneri per due persone diverse oggi non si sommano.** Esempio: scegli Bonus Giovani per un under 35 (15.600 €) e Bonus Donne per una donna di 40 anni (19.200 €). Il codice conta **solo il più ricco (19.200 €)** perché i due esoneri sono nello stesso gruppo, **senza chiedersi se sono per persone diverse**. Sono due persone, quindi valgono entrambi: 34.800 € al massimo. Oggi il totale è **sottostimato** (è prudente, ma non è giusto).
2. **Il lavoratore non entra nel calcolo.** Età, sesso, mesi senza lavoro, tipo di contratto sono «chi assumere»: l'utente li legge e decide, ma il motore non li conosce. Quindi il valore è sempre un massimo e non si sa quale tra 12 e 24 mesi vale.
3. **Le misure sono scritte a mano e non c'è nessuno che guardi le circolari.** Le circolari INPS cambiano ogni anno: se cambia una cifra, il portale la mostra vecchia finché qualcuno non la corregge a mano. C'è la data `VERIFIED_ON` ma nessun controllo che dica «attenzione, la fonte è cambiata».
4. **Nove misure su tredici non hanno cifre.** È onesto, ma significa che un'impresa del Sud vede *Decontribuzione Sud* senza sapere quanto vale.
5. **Le misure regionali sono già collegate al catalogo, ma la ricerca non partiva da sola.** *(Rettifica del 9 novembre: nella prima stesura avevo scritto che non erano collegate. Non è esatto.)* Ogni misura regionale aveva già il pulsante «Cerca nel catalogo · regione», con il filtro di pertinenza sull'impresa e, per ogni bando trovato, i tasti «Fai il budget» e «Vedi nell'Allocazione» (che studiano il bando a fondo se serve). Mancava solo che la ricerca partisse da sola e dicesse quanti bandi aperti ci sono. Ora lo fa: sulla misura compare «3 bandi aperti · Puglia» e, aprendola, l'elenco.
6. **Nessuno ricorda come è andata.** Se la domanda INPS è stata accolta o respinta non resta da nessuna parte.

### 2.4 Come diventa un agente **[NUOVO]**

**Missione.** *Per ogni persona che l'impresa assumerà, trovare la combinazione di agevolazioni che vale di più, dire quando fare domanda e cosa dichiarare, e tenerla aggiornata.*

**Cosa guarda da solo (i suoi «sensori»)**
- Il **profilo** (dipendenti, DURC, regione) e il **piano delle assunzioni** dei documenti.
- Il **bisogno di crescita** calcolato dall'Allocazione («servono 2 persone in marketing e vendite»).
- Le **scadenze** delle misure (31/12/2026) e le finestre (Stabilizzazione: dal 1° agosto al 31 dicembre 2026).
- Le **fonti normative**: le pagine INPS delle circolari presenti nel registro delle fonti. Ogni notte l'agente **confronta l'impronta del testo** con quella dell'ultima verifica: se è cambiata, la misura diventa «**da riverificare**» e l'agente avvisa il Quartier Generale. **Non modifica mai da solo le cifre**: le cifre le aggiorna una persona dopo aver letto la circolare (regola 2).

**Cosa decide**
- Per ogni **posizione da assumere** (età, sesso, mesi senza lavoro, contratto) assegna **una sola misura**, la migliore tra quelle ammesse. Per ogni persona la scelta migliore è semplicemente la più ricca, quindi il calcolo è esatto e leggero.
- Conta ogni persona **una volta sola**: Bonus Giovani per l'under 35, Bonus Donne per la donna di 40 anni → 15.600 + 19.200 = **34.800 €** al massimo (oggi: 19.200).
- Distingue **massimo** e **valore del caso concreto**: con «disoccupato da 14 mesi» sa che valgono i 12 mesi, non i 24.

**Cosa fa**
- Compila per ogni assunzione una **scheda pratica**: misura, importo massimo, condizioni sull'impresa e sul lavoratore, **dichiarazioni da rendere**, norma, **«fai la domanda PRIMA dell'assunzione»** con la data limite.
- Per le misure regionali **cerca da solo nel catalogo** i bandi aperti della regione dell'impresa e li mostra sulla misura (es. «tirocini Regione Puglia: 2 bandi aperti»), con gli stessi tasti di prima. Se non ci sono, lo dice. *(Il collegamento al catalogo esisteva già dietro un pulsante: ora è automatico.)*
- Passa all'Allocazione **un elenco chiaro** di ciò che entra nel totale e ciò che no, con il perché.

**Cosa chiede all'utente (solo quando serve)**
- Un dato mancante dell'impresa: «L'impresa è regolare con DURC?».
- Per ogni assunzione prevista: età, sesso, da quanto è senza lavoro. Se non lo sa, vale il massimo e lo dice.

**Cosa ricorda nel datacenter**
- **Versioni delle misure**: per ogni misura, data della verifica, fonte, impronta del testo, **chi l'ha verificata**.
- **Esiti anonimi**: «domanda presentata → accolta / respinta» per misura e regione (solo conteggi, gruppi di almeno 3).
- **Cosa è stato scelto** e poi usato davvero.

**Cosa NON fa**
- Non scrive cifre prese da una lettura automatica: le cifre sono sempre verificate da una persona.
- Non presenta la domanda all'INPS per conto dell'utente.
- Non consiglia di assumere: calcola cosa succede *se* si assume.

### 2.5 Esempio completo dell'agente **[NUOVO]**
> **Lunedì mattina.** L'agente nota che nel profilo dell'azienda di esempio ci sono 8 dipendenti e DURC regolare. Dal bilancio sa che mancheranno 2 persone nel 2027.
> **Cosa mostra:** «2 assunzioni previste. Se assumi 1 under 35 e 1 donna disoccupata da oltre 12 mesi, in Puglia puoi recuperare **fino a 34.800 €** (15.600 + 19.200). Fai la domanda sul portale INPS **prima** di firmare il contratto; la misura vale per assunzioni entro il 31/12/2026.» *(Se la sentinella trovasse il testo della circolare cambiato, aggiungerebbe: «Il testo della fonte è cambiato dall'ultima verifica: **da riverificare**».)*
> **Cosa ti chiede:** «L'under 35 è disoccupato da quanto? (12 o 24 mesi)».

### 2.6 Cosa migliora il datacenter
| Cosa si registra | A cosa serve |
|---|---|
| Versione di ogni misura con data, fonte, impronta e verificatore | Nessuna cifra «vecchia» senza che si sappia |
| Misure regionali collegate ai bandi aperti del catalogo | Ogni studio vede subito cosa c'è nella sua regione |
| Esito delle domande (anonimo, ≥ 3) | Dire quanto sono «facili» le misure con dati veri |

---

## 3. Agente Allocazione

### 3.1 A cosa serve
È il cuore del portale: partendo dall'impresa dice **quali bandi sono davvero per lei**, **come combinarli** sulle sue spese e quanto contarci **realisticamente**.

### 3.2 Come lavora oggi, passo per passo **[OGGI]**

**Esempio:** la stessa azienda di esempio (Puglia, ATECO 47.71 negozio di abbigliamento, 8 dipendenti, spese previste per l'anno: personale 280.000 €, beni strumentali 60.000 €, consulenze 20.000 €, altre 40.000 € → **400.000 €**).

**Passo A. Il catalogo si riempie da solo.** Due lavori notturni (Vercel ne permette solo due): alle 03:00 l'aggiornamento dell'elenco; alle 03:30 la raccolta dalle 90 fonti (15 secondi) e poi la lettura delle schede. È il lavoro del §1.

**Passo B. Il profilo e le spese** (`company_profile.py`, `budget_basis.py`).
Il budget dell'anno non è il vecchio bilancio copiato: dice cosa è stato speso, non cosa servirà. Si compone nell'ordine più affidabile:
1. **budget dell'azienda** per l'anno, se l'ha caricato, conto per conto;
2. **piano degli investimenti** (acquisti veri, non ammortamenti) e **piano delle assunzioni**;
3. **previsione dal bilancio**: ultimo esercizio × variazione annua di ogni categoria (scelta dall'utente o ricavata dai suoi due ultimi bilanci).
Ogni riga dice **da quale delle tre viene**. Il personale si costruisce **persona per persona**.

**Passo C. Quali bandi sono per lei** (`matching.evaluate`).
Per ogni bando studiato si fanno queste verifiche, ognuna «ok», «no» o «da verificare»:
1. **Apertura**: chiuso, scaduto, finestra finita?
2. **Spese ammesse**: almeno una categoria dell'impresa è ammessa?
3. **Settore**: se il bando dichiara codici ATECO ammessi, il suo ci rientra?
4. **Pertinenza** (`relevance.py`): territorio (anche da una provincia: «Camera di commercio di Chieti e Pescara» = Abruzzo), settore nominato nel nome o nell'ente, soggetti ammessi, scheda del catalogo.
5. **Start-up innovativa**, **dimensione**.
6. **Valore** (`valuation.py`): percentuale da regola, modello o testo; tetti; massimo per progetto.
Se **una** verifica è «no» → **NON ADATTO**. Se una verifica decisiva è «da verificare» o non c'è una percentuale → **DA VERIFICARE**. Altrimenti **ADATTO**.

*Esempio pertinenza:* il «bando sugli autobus elettrici del PNRR». Il dizionario dei settori riconosce *autobus* → trasporti, ammessi solo ATECO 29, 30, 49–53. L'impresa è 47.71 → **NON ADATTO: «Il bando è rivolto a: trasporti e mezzi di trasporto. Il tuo codice ATECO 47.71 non rientra.»** Non appare mai tra i possibili.

**Passo D. Il catalogo non ancora studiato** (`catalog_meta.rank_for_profile`).
Le voci lette ma non studiate si ordinano per **affinità** da 0 a 1:
- **0,75 × quota delle spese dell'impresa** coperta dai «costi ammessi» della scheda;
- **+0,10** se il bando è locale e include la sua regione, **+0,15** se tra i settori indicati c'è il suo, **+0,05** se è per start-up innovative e lo è;
- **−0,30** se i settori indicati non includono il suo; **−0,40** se è per start-up e l'impresa ha 5 anni o più.
- Esclusi: chiusi, di altra regione, altra dimensione, altro ATECO, per chi non è un'impresa.
Affinità **ALTA da 0,6**, **MEDIA da 0,25**.

*Esempio:* «Contributo macchinari e consulenze Puglia»: i costi ammessi coprono beni (60.000) + consulenze (20.000) = 80.000 su 400.000 = 20% → 0,75 × 0,20 = **0,15**; + 0,10 (bando solo pugliese) = **0,25** → **MEDIA**, per un soffio.
Per i contributi la scheda dà anche un **tetto provvisorio**: «agevolazione massima ÷ spesa massima» applicata alle spese dell'azienda, mai oltre l'agevolazione massima. È un tetto, non una stima.

**Passo E. Lo studio a fondo, in fila.** «Studia a fondo tutti i bandi affini» li studia uno dopo l'altro (≈ 1 minuto ciascuno) e il tetto provvisorio diventa un importo vero. Solo i bandi **studiati** entrano nel piano.

**Passo F. Cosa serve all'impresa** (`growth_needs.py`, `project_ideas.py`).
- Dalla crescita prevista si ricavano **persone** (per reparto) e **strumenti** (intensità di capitale = costo dei beni ÷ ricavi), come al §2.2 passo 7.
- Si propongono **idee di progetto** dai documenti: investimenti già in piano, beni a fine vita (ammortizzati oltre il 90%), assunzioni previste, formazione, promozione, certificazioni, efficientamento energetico.
- Ogni spesa è **NUOVA** (un acquisto o un'assunzione che il progetto causa: è ciò che un bando finanzia), **ORDINARIA** (l'azienda la sostiene comunque: **non diventa spesa di progetto**; entra solo dove il bando la ammette per forma, per esempio spese generali a forfait) o **DA QUANTIFICARE** (manca un preventivo: **non si inventa**).
- Per ogni idea si elencano i **bandi che finanziano quel tipo di progetto**, ma solo quelli **pertinenti** all'impresa.

**Passo G. Il piano: l'ottimizzatore** (`allocation_engine.py`). È un problema di programmazione lineare mista, risolto in modo **esatto** (HiGHS):
- per ogni spesa e ogni fondo, quanta parte copre il fondo (mai oltre la sua intensità);
- una spesa non è coperta oltre il 100%;
- ogni fondo ha il suo **tetto**;
- **non cumulabilità** (due fondi che si escludono non coprono mai la stessa spesa);
- **massimale per categoria** (es. consulenze al massimo 20% del totale);
- **de minimis**: la somma dei fondi in de minimis non supera il residuo;
- **finestre mensili** dei fondi.
Funziona in stadi: prima il risparmio massimo, poi (se scelto) il numero di voci coperte o di fondi coinvolti, e infine una **scelta canonica** tra soluzioni equivalenti (così gli stessi dati danno **sempre** lo stesso piano). Gli importi finali sono **interi in centesimi, arrotondati per difetto e ricontrollati in aritmetica esatta**.

*Esempio verificato col motore vero:* macchinario 100.000 € e consulenza 30.000 €.
- **Fondo A**: copre il 40% di beni e consulenze, tetto del fondo 30.000 €.
- **Fondo B**: copre il 50% dei soli beni, in de minimis, residuo 20.000 €.
- A e B **non cumulabili** sulla stessa spesa.
Risultato: **B copre 20.000 € del macchinario** (il massimo del residuo de minimis) e **A copre 12.000 € della consulenza** → **32.000 €**, cioè **più** di quanto otterrebbe usando solo A (il suo tetto di 30.000 €). La soluzione «ovvia» (A sul macchinario) rende meno: per questo serve un solutore e non una regola a occhio.

**Passo H. Dalla somma alla realtà** (`allocation_reality.py`).
Il piano dice «32.000 €». Non dice tre cose:
1. **Quanto ci si può contare**: un bando si vince o no, istruire la domanda costa, spesso c'è una percentuale al consulente. **La probabilità, il costo di istruttoria e la percentuale del consulente li indica una persona**: se mancano, il valore atteso di quel fondo **non si calcola** e si dice cosa manca.
   *Esempio:* contributo 32.000 €, probabilità 60%, istruttoria 1.500 €, consulente 10% → ci si può contare per 19.200 €; tolti consulente (1.920 €) e istruttoria restano **15.780 €**. **Soglia di convenienza**: con probabilità sopra il **5,2%** conviene comunque.
2. **Quando entrano i soldi**: il contributo si incassa dopo; nel frattempo le spese le paga l'azienda. Anticipo e mesi di rimborso si leggono dal bando se le regole sono pubblicate. Risultato: «l'azienda deve anticipare al massimo X € al mese Y, contro Z € senza contributi».
3. **Cosa ha già preso**: credito d'imposta ricerca e sviluppo, altri aiuti sulle stesse spese: si sommano e il bando ha un tetto. Il **de minimis** ha il suo registro (`aids_register.py`): 300.000 € in tre esercizi **per impresa unica**; se la verifica sul Registro Nazionale Aiuti non è completa e recente (30 giorni), il piano usa il residuo **ridotto di un margine di sicurezza pari al 10% del tetto** (30.000 €) e dice «non verificato».

**Passo I. Un budget per ogni bando** (`allocation_budgets.py`). Un commercialista non presenta «un'allocazione»: presenta un budget a ogni bando.
- La parte di costo di un fondo = **contributo coperto ÷ intensità del fondo** (se il fondo copre 40.000 € al 50%, il suo budget contiene 80.000 € di spesa);
- il **personale si divide tra i bandi senza sovrapporsi**: ogni persona ha, in ogni budget, una quota del proprio tempo e la somma tra tutti i budget **non supera il 100%** (un'ora non si rendiconta a due bandi);
- **sei controlli incrociati**: nessuna spesa coperta oltre il suo importo; nessuna persona oltre il 100%; fondi non cumulabili mai insieme; aiuto cumulato entro il massimo di ogni bando; de minimis nel limite; **ogni budget supera i 60 criteri del suo bando** (se il motore ammette meno, la differenza è scritta con la ragione).

**Passo J. Cosa entra nel totale.** Solo i bandi **ADATTI** (con importo vero) e le agevolazioni **applicabili**. I «da verificare» si mostrano, ma **non si sommano mai**. La pagina è divisa in quattro parti: **azienda · bandi · insieme · progetti**, ciascuna con la barra di navigazione fissa e con la spiegazione dietro la «i».

### 3.3 Cosa ho trovato studiandolo: i limiti veri **[OGGI]**

1. **Si ricalcola tutto a ogni richiesta.** `match_all` rilegge dal database il dettaglio di ogni bando studiato, rifà tutte le verifiche e valuta; `rank_for_profile` rilegge **tutto il catalogo**; `project_ideas` ricarica di nuovo il dettaglio di ogni bando. Non l'ho misurato (da fare prima di toccare nulla), ma è lavoro ripetuto: stesso bando, stessa regola, stesso risultato, rifatto per ogni lavoro e per ogni apertura della pagina.
2. **La pertinenza si basa su parole.** Il dizionario dei settori (`SECTOR_LEXICON`) funziona dove il nome o l'ente dicono il settore. Se il bando ha un nome generico («Avviso 2026»), passa tra i «da verificare». Dopo l'errore degli autobus l'abbiamo allargato a mano; **non impara dai tuoi segnali** («questo non fa per me»).
3. **Chi studia cosa non è coordinato.** Un bando studiato **vale per tutti gli studi** (la tabella `bandi` non ha un proprietario), ma la coda di studio è «i più affini a questo lavoro». Nessuno ordina lo studio per **quanti studi lo vogliono**. Esiste un contatore (`requested_by_clients`) ma serve solo a proteggere dalla pulizia, non a dare la priorità.
4. **I numeri chiave li scrive una persona.** Probabilità di successo, costo di istruttoria, percentuale del consulente: oggi sono vuoti finché qualcuno non li inserisce, anche se per un bando con tanti budget presentati nel Confronto un dato di partenza esisterebbe.
5. **Il piano non ricorda.** Nessuno storico dei piani calcolati: non si può dire «cosa è cambiato dall'ultima volta» e non si sa cosa è successo ai bandi presentati.
6. **Pochi bandi hanno un importo vero.** Il limite principale non è il solutore: è **quanti bandi sono stati studiati** e dichiarano una percentuale.

### 3.4 Come diventa un agente **[NUOVO]**

**Missione.** *Tenere per ogni lavoro un piano sempre aggiornato dei bandi davvero adatti, combinati bene sulle sue spese, con importi vincolati a fonti e la prudenza di cosa c'è da verificare.*

L'agente è composto da **sei mansioni**, ognuna già in parte presente nel codice:

| Mansione | Compito | Oggi |
|---|---|---|
| **Esploratore** | Trova bandi nuovi nelle fonti ufficiali e li iscrive | `official_sources`, `discovery` |
| **Lettore** | Legge schede e studia a fondo | `catalog_meta`, `pipeline` |
| **Giudice** | Dice ADATTO / DA VERIFICARE / NON ADATTO e **perché** | `matching`, `relevance` |
| **Pianificatore** | Combina i bandi sulle spese | `allocation_engine` |
| **Realista** | Valore atteso, anticipi, cumulo, de minimis | `allocation_reality`, `aids_register` |
| **Costruttore di budget** | Un budget per bando, controllato e coerente con gli altri | `allocation_budgets` |

**Cosa guarda da solo**
- **Ogni notte, dopo la raccolta**: i bandi nuovi o cambiati. Per ogni lavoro con un piano aperto ricalcola solo ciò che è cambiato e produce una lista **Novità** («2 bandi nuovi adatti; 1 scade tra 7 giorni; 1 non è più adatto: spiegazione»).
- **Quando arriva un documento** o cambia il profilo: ricalcola solo le parti toccate.
- **Quando un bando cambia regole** (l'impronta delle regole cambia): invalida solo le schede e i piani che lo usano.

**Cosa decide**
- La **priorità di studio** condivisa: ogni notte mette in coda per lo studio a fondo i bandi con **affinità ALTA o MEDIA per più lavori**, partendo da quelli richiesti da più studi (solo conteggi, nessun nome).
- Cosa entra nel piano: sempre e solo i bandi ADATTI (regola 3).

**Cosa fa di nuovo**
1. **Scheda precalcolata del bando** (`bando_cards`): per ogni bando studiato salva **una volta sola** ciò che oggi si rifà ogni volta (regole pubblicate, tipi di progetto, modalità, modello di valore, segnali di pertinenza), con l'impronta delle regole. Si ricalcola **solo** se l'impronta cambia. Il confronto con l'impresa diventa un calcolo leggero su dati già pronti.
2. **Registro dei segnali di pertinenza**: quando un utente segna un bando «non è per la mia azienda» (o «sì, è per me») la scelta si registra con il motivo. Se lo stesso segnale arriva da più lavori, l'agente **propone al Quartier Generale una parola in più per il dizionario**. **Non la applica da solo**: la applica una persona (regola 2).
3. **Valori di partenza dal Confronto**: se per quel bando e quel settore esistono almeno 3 budget con esito noto, propone la **percentuale di bandi ammessi** come probabilità di partenza, scrivendo da dove viene («dal tuo studio: 4 ammessi su 7»). L'utente **accetta o corregge**. Mai applicata in silenzio.
4. **Storico dei piani**: ogni piano calcolato è salvato con la sua impronta e si può confrontare con il precedente («prima 32.000 €, ora 38.000 €: è entrato il bando X; è uscito il bando Y perché chiuso il 31/10»).
5. **Esiti**: quando il bando risponde, l'utente segna «presentato / ammesso / non ammesso». L'agente passa il dato al Confronto (con consenso) e al proprio registro.

**Cosa chiede all'utente (solo quando serve)**
Il dato che manca, con la ragione («regione della sede: serve a escludere i bandi di altre regioni»).

**Cosa NON fa**
- Non sposta una spesa ordinaria in un progetto.
- Non somma un bando «da verificare».
- Non cambia le regole di un bando: le legge e le propone, le pubblica una persona.

### 3.5 Esempio completo dell'agente **[NUOVO]**
*(Il bando «Voucher Digitale Puglia 2026» è di fantasia, solo per spiegare.)*
> **Notte del 12 novembre.** La raccolta aggiunge «Voucher Digitale Puglia 2026». L'agente lo legge: *Regione Puglia, PMI, costi ammessi: consulenze e software, scadenza 20/12*.
> **Mattina.** Per l'azienda di esempio il bando è **MEDIA** (0,25: copre il 20% delle spese + bando regionale). L'agente lo mette in coda di studio, **davanti agli altri** perché altri 3 lavori della stessa regione lo avrebbero.
> **Dopo lo studio** (un minuto): intensità 50%, tetto 40.000 € → **ADATTO**. Il piano si ricalcola solo con i dati nuovi: **da 32.000 € a 41.000 €**.
> **Novità:** «Nuovo bando adatto: Voucher Digitale Puglia 2026, scade fra 38 giorni. +9.000 € nel piano. Probabilità di partenza 60% (dai budget del Confronto: 4 ammessi su 7): accetta o correggi.»

### 3.6 Cosa migliora il datacenter
| Cosa si registra | A cosa serve |
|---|---|
| `bando_cards` (scheda precalcolata + impronta delle regole) | Piani più veloci, stessi numeri |
| Segnali di pertinenza («non è per me», «sì») | Il dizionario dei settori cresce dai casi veri, con approvazione |
| Domanda di studio per bando (conteggi anonimi) | Lo studio coordinato: ogni studio beneficia degli studi degli altri |
| Storico dei piani con impronta | Si vede cosa è cambiato e perché |
| Esiti dei bandi | Alimentano Confronto e probabilità di partenza |

---

## 3 bis. Agente Budget (il quarto passo del percorso, tra Allocazione e Confronto)

**L'analisi dell'ordine.** Cronologicamente il lavoro va così: **1 Agevolazioni** (chi assumo e cosa recupero) → **2 Allocazione** (quali bandi, quale fondo paga cosa) → **3 Budget** (il budget di ogni bando, controllato) → **4 Confronto** (il budget finito si confronta con chi ha già partecipato e si pubblica). Il Budget **deve** stare prima del Confronto: il Confronto lavora su un budget già composto e controllato (la sua «Pubblica questo budget» parte proprio dalle quote del budget controllato), e l'Allocazione consegna al Budget i budget per bando. Nel menu il Budget stava prima dell'Allocazione: era l'ordine sbagliato. Lo è anche il suo posto di «strumento»: è il passo in cui l'Allocazione diventa qualcosa che si può presentare.

**Come lavora oggi [OGGI].**
1. **La bozza dal profilo** (`matching.budget_template`): personale **persona per persona** (RAL, livello, contratto, quota di tempo), le altre spese come **voci di spesa** con importo, fonte (budget dell'azienda, piano degli investimenti o previsione) e documento; le voci che il bando esclude per nome non entrano; quelle sopra i tetti si riducono alla parte ammissibile.
2. **Un budget per ogni bando** dal piano dell'Allocazione (`allocation_budgets.py`): la parte di costo di ogni fondo, il personale diviso senza superare il 100% del tempo, sei controlli incrociati.
3. **I 60 criteri** (`deterministic_engine.py`) su ogni voce: ammessa, ridotta, respinta, in attesa di un documento.
4. **Pacchetti di lavoro** (`wp_allocation.py`), registro firmato ed esportazione.

**Cosa ho trovato.** La pagina non diceva da sola dove si era arrivati né quale fosse il passo dopo; per sapere cosa mancava bisognava scorrerla. Il passo successivo (portare il budget al Confronto) esisteva ma in fondo alla pagina.

**Come diventa un agente [FATTO].** In cima ha la striscia a tre righe: **ho fatto** («ho preparato 5 budget dal piano»), **ho trovato** («12 voci ammesse su 14, 2 ridotte; verificati insieme: nessun conflitto»), **mi serve da te** («1 voce aspetta il CUP»), e un solo pulsante che cambia col momento: *Vai ai bandi* → *Controlla il budget* → *Confronta con chi ha già vinto*. Non cambia nessuna regola di calcolo.

---

## 4. Agente Confronto

### 4.1 A cosa serve
Un commercialista che prepara il budget di un bando si chiede: *«come l'hanno composto gli altri che hanno vinto? Il mio è troppo pesante su consulenze o beni?»* Il Confronto risponde con una **statistica spiegabile**, non con un'opinione.

### 4.2 Come lavora oggi, passo per passo **[OGGI]**

**Passo 1. Cos'è un template.** Una riga con: **nicchia** (ATECO a 2 cifre, es. 47 = commercio al dettaglio), **bando**, **ripartizione del budget** in 8 voci (personale, beni strumentali, consulenze, ricerca e sviluppo, spese generali, formazione, comunicazione, altro, che sommano 100%) ed **esito** (bozza, presentato, ammesso, non ammesso). Si possono salvare **solo per lo studio** o **pubblicare per tutti** (in forma anonima: niente ragione sociale né partita IVA).

**Passo 2. Chi somiglia a chi: sei livelli**, dal più preciso al più generale:
1. stessa nicchia e stesso bando
2. stesso settore e stesso bando
3. stesso bando
4. stessa nicchia
5. stesso settore
6. tutti
Si usa il **primo livello con almeno 3 template** (`MIN_TEMPLATES`).

**Passo 3. Chi conta di più.** Ogni template pesa secondo l'esito: **ammesso 3 · presentato 1,5 · bozza 1 · non ammesso 0,25**. Così i budget che hanno vinto guidano il consiglio.

**Passo 4. Il consiglio = media pesata.** Per ogni voce: somma dei (quota × peso) ÷ somma dei pesi; la **dispersione** (quanto i template sono diversi) dà l'intervallo «di solito tra».

*Esempio (numeri di scuola):* tre template per lo stesso bando e la stessa nicchia, con quote **personale / beni / consulenze**:
- ammesso: 60 / 30 / 10 (peso 3);
- bozza: 50 / 30 / 20 (peso 1);
- non ammesso: 20 / 70 / 10 (peso 0,25).
Somma dei pesi 4,25. Consiglio: personale (180 + 50 + 5) ÷ 4,25 ≈ **55,3%**, beni (90 + 30 + 17,5) ÷ 4,25 ≈ **32,4%**, consulenze (30 + 20 + 2,5) ÷ 4,25 ≈ **12,4%**.

**Passo 5. Quanta fiducia.** **ALTA** solo se il livello è «stessa nicchia e stesso bando» con **almeno 8 template reali**; **MEDIA** per i livelli che includono lo stesso bando; **BASSA** per gli altri. Con **meno di 3 template reali** la fiducia è sempre BASSA. Il testo dice quanti template reali mancano per salire.

**Passo 6. Gli stili.** Con almeno 6 template si cercano gruppi di budget simili (**k-means** con seme fisso, scelta di k con l'indice «silhouette»; sotto 0,2 i gruppi non si inventano). Per ogni gruppo: nome dalla voce dominante («Stile “consulenze”»), quanti template, quanti ammessi.

**Passo 7. Il confronto con il tuo budget.** Distanza = **metà della somma degli scarti assoluti**. *Esempio:* il tuo budget è 50 / 35 / 15 → scarti 5,3 + 2,6 + 2,6 = 10,6 → **dista il 5,3%** dal consiglio; scostamento maggiore sul personale (−5,3 punti). Entro il **10%** si dice «vicino».

**Passo 8. Auto-miglioramento.** Alla creazione di ogni template si registra **quanto distava dal consiglio di quel momento**. Con almeno **5 esiti noti tra i vicini e 5 tra i lontani** il sistema dice: «i budget vicini al consiglio sono stati ammessi nel X% dei casi, gli altri nel Y%». Sotto la soglia dice quanti ne mancano. Non si dichiara mai che «seguire il consiglio conviene» senza dati.

**Passo 9. Privacy e due motori.** Il **motore collettivo** lavora sui template pubblicati; l'**interno** solo su quelli dello studio. Dei template **altrui** si usa un gruppo solo se ha **almeno 3** template: sotto, nessuno può risalire a un cliente. Si condivide solo: nicchia, bando, regione, dimensione, percentuali, esito. **Mai** ragione sociale, partita IVA, importi personali, note.

**Passo 10. L'avvio a freddo.** 48 **esempi** costruiti sulle regole vere di 7 bandi (Horizon Europe, FVG Validazione TRL, Smart&Start, SIMEST 394, Iperammortamento, Nuova Sabatini, Investimenti Sostenibili 4.0) e **verificati con quelle regole** (categorie ammesse, tetto sulle consulenze, forfait sulle spese generali): «conforme», «conforme con riduzioni», «non conforme». **Non sono budget reali e non hanno un esito di bando**: pesano la metà ed escono dal calcolo appena il gruppo ha 8 template reali. Si possono eliminare dal Quartier Generale.

**Passo 11. Un secondo sistema.** Esiste anche la **banca dei pattern** (`pattern_bank.py`): budget storici importati da file (graduatorie pubbliche, dataset UE) **con la fonte**, 6 voci, gruppi con k-means. Funziona in parallelo al Confronto e vive solo nel Quartier Generale (importazione e laboratorio). La pagina Budget, invece, mostra già il confronto con il **motore dei template** (`PatternCompare` usa la stessa raccomandazione del Confronto).

### 4.3 Cosa ho trovato studiandolo: i limiti veri **[OGGI]**

1. **Il consiglio non viene controllato con le regole del bando.** È una media di budget degli altri: se la media sfora un tetto (es. consulenze al 14% con un tetto del 12%), il consiglio lo propone lo stesso. Il controllo con le regole esiste (`verify_shares`), ma si usa solo per costruire gli esempi, **non per verificare il consiglio**.
2. **Due motori che si sovrappongono** (template e banca dei pattern) con voci diverse (8 contro 6): lo stesso concetto «budget storico» è in due tabelle.
3. **Nessun legame con l'Allocazione.** L'Allocazione costruisce già un budget per bando, ma il Confronto riceve le quote solo se l'utente preme «Pubblica questo budget» dal Budget controllato (e lì le 5 categorie del motore diventano 8 voci con tre a zero). Né l'esito né il budget tornano all'Allocazione.
4. **Gli esiti si inseriscono a mano e non si controllano.** Un template «ammesso» che in realtà non passava i 60 criteri pesa 3 lo stesso.
5. **Si usano pochi segnali per «chi somiglia».** Regione, dimensione dell'impresa e importo totale sono salvati ma **non entrano** nel giudizio di somiglianza.
6. **L'avvio a freddo copre 7 bandi.** Per tutti gli altri, finché lo studio non salva budget reali, il consiglio dice «ancora pochi dati» (onesto, ma poco utile).

### 4.4 Come diventa un agente **[NUOVO]**

**Missione.** *Dire come si compone un budget che funziona per quel bando e quel settore, verificarlo con le regole del bando e imparare da ogni budget e da ogni esito.*

**Cosa guarda da solo**
- I **budget controllati** nella pagina Budget (che superano i 60 criteri) e i **budget per bando** costruiti dall'Allocazione.
- I **cambi di esito** («presentato» → «ammesso»).
- Le **regole dei bandi** (se l'impronta cambia, gli esempi si rifanno da soli: esiste già; si estende al controllo del consiglio).

**Cosa decide**
- **Il consiglio è sempre verificato.** Dopo la media pesata l'agente controlla il risultato con le regole di quota del bando (categorie ammesse, tetto consulenze, forfait spese generali). Se sfora, lo **dice** («la media degli altri è 14% di consulenze ma questo bando ammette al massimo il 12%: la parte oltre il tetto non si finanzia») e propone la versione **già dentro i tetti**, mostrando le due.
- **Peso di qualità.** Un template pesa di più se il budget ha superato i 60 criteri e meno se non li passava, **oltre** al peso dell'esito.
- **Somiglianza più ricca.** Oltre a nicchia e bando, un peso minore per regione, dimensione dell'impresa e ordine di grandezza dell'importo.

**Cosa fa**
- **Quando l'Allocazione ha costruito il budget di un bando**, l'agente lo confronta **da solo** («il tuo budget per il Voucher dista il 4% dal consiglio: bene; sulle consulenze sei 3 punti sopra») e lascia un pulsante «Salva per l'apprendimento».
- Passa all'Allocazione un **dato di partenza per la probabilità** (ammessi ÷ presentati, con quanti e da dove) per **bando e nicchia**, solo se i template sono almeno 3.
- **Unifica i budget storici** in un'unica tabella con **origine**: `REALE` (di uno studio), `STORICO` (importato da fonte pubblica con indirizzo), `ESEMPIO` (costruito sulle regole). Le tre origini pesano diversamente e il testo dice quali ha usato.

**Cosa chiede all'utente (solo quando serve)**
Nicchia, bando e esito. E, quando salva, la scelta chiara **«Per tutti» o «Solo nello studio»**.

**Cosa NON fa**
- Non promette un esito di bando. Dice sempre: *«È un'indicazione statistica sulla struttura della spesa, non una previsione di esito.»*
- Non mostra mai gruppi con meno di 3 budget di altri studi.
- Non aiuta a **gonfiare** un budget per somigliare ai vincenti: il consiglio è già dentro i tetti.

### 4.5 Esempio completo dell'agente **[NUOVO]**
*(Stesso bando di fantasia; i numeri sono di scuola.)*
> L'Allocazione ha costruito il budget del «Voucher Digitale Puglia»: personale 15%, software 55%, consulenze 20%, altro 10%.
> **Confronto:** «Per il commercio al dettaglio e questo bando ho 5 budget reali (3 ammessi): fiducia media. Consiglio: software 50%, consulenze 14%, personale 22%… Il tuo budget dista il 7%. **Attenzione:** il bando ammette al massimo il 15% di consulenze: il tuo 20% ne lascerebbe fuori 5 punti. Versione dentro il tetto: …»
> Un mese dopo l'utente segna «ammesso». Il template sale di peso, il consiglio si ricalcola, e la probabilità di partenza per quel bando passa da «dato non disponibile» a «4 ammessi su 6».

### 4.6 Cosa migliora il datacenter
| Cosa si registra | A cosa serve |
|---|---|
| Tabella unica dei budget storici con origine | Un solo motore, un solo conteggio |
| Qualità del template (superato i 60 criteri sì/no) | Il consiglio non si fida di budget che non passavano |
| Calibrazione (distanza dal consiglio ↔ esito) | Si può dire con i numeri se seguirlo conviene |
| Probabilità di partenza per bando e nicchia | Si usa nell'Allocazione, con la sua origine scritta |

---

## 5. Il datacenter cumulativo di QUANTO

### 5.1 Cosa c'è oggi **[OGGI]**
| Cosa | Dove | Condiviso tra studi? |
|---|---|---|
| Bandi, regole, requisiti, documenti originali, fonti | `bandi`, `rules`, `requirements`, `bando_sources`, `bando_files` | **Sì**: un bando studiato vale per tutti |
| Schede del catalogo | `bandi.catalog_meta`, `bandi.summary` | Sì |
| Stato delle 90 fonti | `source_checks` | Sì |
| Documenti di domanda estratti | `application_docs`, `application_runs` | Sì |
| Budget dei template | `budget_templates` | **Solo se pubblicati**, in forma anonima, gruppi ≥ 3 |
| Budget storici importati | `pattern_budgets`, `pattern_archetypes` | Sì (importati dal Quartier Generale) |
| Dati dell'impresa e documenti | `company_profiles`, `company_financials`, `client_documents` | **No**: per studio e per lavoro |
| Scelte nel lavoro | `client_state` (allocazione, budget, confronto, agevolazioni…) | No |
| Operazioni | `events`, registro firmato `anchors` | Registro firmato verificabile |

### 5.2 Cosa manca, e quale agente lo porta **[NUOVO]**
| Nuovo | Chi lo scrive | Contenuto | Condivisione |
|---|---|---|---|
| `measure_versions` | Agevolazioni | misura, versione, data, fonte, impronta del testo, verificatore | Sì |
| `measure_outcomes` | Agevolazioni | misura, regione, esito della domanda | Solo conteggi, gruppi ≥ 3 |
| `bando_cards` | Allocazione | regole, tipi di progetto, modello di valore, segnali, impronta | Sì |
| `relevance_signals` | Allocazione | bando, segnale, motivo (senza dati dell'impresa; ATECO a 2 cifre e regione) | Conteggi |
| `study_demand` | Allocazione | bando, numero di lavori che lo vogliono ALTO/MEDIO | Conteggi |
| `plan_history` | Allocazione | impronta degli ingressi, uscita, data | No (dello studio) |
| `budget_bank` (unica) | Confronto | quote, origine, esito, qualità, nicchia, regione, dimensione | Anonimo, gruppi ≥ 3 |
| `calibration` | Confronto | distanza dal consiglio ↔ esito | Aggregato |

### 5.3 Le regole del datacenter (valgono per tutti e tre)
1. **Ogni record dice da dove viene** (fonte, data, grado, chi l'ha verificato).
2. **Il privato resta privato**: ragione sociale, partita IVA, importi di una persona, note non escono mai. Dei dati altrui si usano **solo aggregati di almeno 3**.
3. **Gli agenti propongono, le persone pubblicano**: cifre di una misura, regole di un bando e parole del dizionario si cambiano solo con una conferma (con nome e data, nel registro firmato).
4. **Nessun dato inventato**: dove un dato manca, la voce resta vuota e dice cosa serve.
5. **Tutto resta gratuito per ora** (`QUANTO_TOKENS_CHARGE` spento); i token si vedono, non si scalano.

### 5.4 Come si misura che migliora
| Domanda | Numero |
|---|---|
| Quanto sono pronti i bandi? | % di bandi ALTA/MEDIA già studiati |
| Quanto è veloce? | secondi per aprire un piano (prima/dopo la scheda precalcolata) |
| Quanto sono giusti i giudizi? | % di bandi segnati «non per me» sul totale mostrato (deve scendere) |
| Quanto vale il Confronto? | n. di gruppi con fiducia ALTA; ammessi tra «vicini» e «lontani» |
| Quanto sono fresche le misure? | giorni dall'ultima verifica; n. di misure «da riverificare» |

---

## 6. Come si parlano i tre agenti

```
        Agevolazioni                  Allocazione                    Confronto
  ┌───────────────────┐        ┌───────────────────────┐       ┌───────────────────┐
  │ per ogni persona  │ scelte │ giudica i bandi,      │ budget│ confronta con chi │
  │ da assumere trova │ ─────► │ combina i fondi,      │ ────► │ ha già vinto,     │
  │ l'esonero migliore│        │ valore atteso, cassa  │       │ verifica i tetti  │
  └───────────────────┘        └───────────────────────┘       └───────────────────┘
          ▲   assunzioni previste        ▲   probabilità di partenza      │
          └──────── dal bisogno di crescita ◄──────────── esiti ◄─────────┘
                                     │
                         ┌───────────▼───────────┐
                         │  DATACENTER QUANTO    │
                         └───────────────────────┘
```
- **Agevolazioni → Allocazione**: l'elenco delle scelte con cosa entra nel totale e perché.
- **Allocazione → Confronto**: il budget di ogni bando.
- **Confronto → Allocazione**: la probabilità di partenza (ammessi ÷ presentati) con origine e numerosità.
- **Allocazione → Agevolazioni**: il bisogno di crescita («servono 2 persone»).
- **Tutti → datacenter**: ciò che hanno imparato, in forma anonima dove serve.

---

## 7. Cosa cambia per chi usa il portale **[NUOVO]**

Rimane l'impostazione minima di sempre (sezioni di base chiuse, spiegazioni dietro la «i», pulsanti che fanno ciò che dicono). Ogni agente apre con **una striscia di tre righe**:

| Riga | Esempio per l'Allocazione |
|---|---|
| **Ho fatto** | «Stanotte ho letto 14 bandi nuovi e ricalcolato il piano.» |
| **Ho trovato** | «2 nuovi adatti (+9.000 €), 1 non è più adatto.» |
| **Mi serve da te** | «La probabilità di successo del Voucher Digitale Puglia.» |

E sotto, le tre parti già note (Novità, Dettaglio, Storia). I pulsanti hanno nomi che dicono cosa succede: **«Studia ora i 5 bandi più richiesti»**, **«Segna: non è per la mia azienda»**, **«Salva per l'apprendimento (per tutti)»**.

---

## 8. In che ordine costruirli

Il più semplice e con il maggior effetto prima.

| Fase | Cosa | Perché prima |
|---|---|---|
| **1. Agevolazioni corretto** | Posizioni da assumere (età, sesso, mesi) e assegnazione per persona (corregge il limite 1 del §2.3) | È un **errore di conteggio vero** e serve poco lavoro |
| **2. Scheda precalcolata (Allocazione)** | `bando_cards` con impronta delle regole; misurare prima/dopo i tempi | Rende veloci tutti gli altri passi; **prima si misura**, poi si ottimizza |
| **3. Confronto verificato** | Il consiglio controllato con le regole del bando + peso di qualità | Evita di consigliare un budget che sfora un tetto |
| **4. Allocazione: Novità e coda condivisa** | Notte → novità per lavoro; priorità di studio per domanda aggregata | Dà il «lavoro da solo» promesso |
| **5. Il ponte Allocazione ↔ Confronto** | Budget per bando → confronto automatico; esiti → probabilità di partenza | È ciò che chiude il cerchio del datacenter |
| **6. Agevolazioni: sentinella delle circolari** | Impronta del testo, «da riverificare», avviso al Quartier Generale | Serve sapere **quali pagine** INPS sono leggibili da un server: si prova prima |
| **7. Datacenter: tabelle e misure** | Tabelle del §5.2, metriche del §5.4, tabella unica dei budget | Raccoglie quanto costruito sopra |

Ogni fase si chiude con **test automatici**, **prova su dati di esempio**, **aggiornamento del manuale, del dossier e del riassunto** e solo dopo pubblicazione.

---

## 9. Cosa non cambia, e cosa non prometto

- **Nessun modello linguistico decide cifre**: i testi di sintesi, dove ci sono, si limitano a *dire* numeri già calcolati.
- **Le pagine costruite solo con JavaScript restano illeggibili** da un server: la sentinella delle circolari funziona dove l'INPS pubblica testo o PDF; **dove non si può leggere, l'agente lo dice**.
- **L'avvio a freddo del Confronto dipende dai budget veri**: gli esempi coprono 7 bandi e il resto parte quando gli studi salvano budget.
- **I tempi non sono ancora misurati**: l'idea della scheda precalcolata è un'ipotesi ragionevole, da verificare con una misura prima di costruirla.
- **Un'agevolazione è sempre un massimo finché non si conosce il lavoratore**: lo dico anche dopo il miglioramento.

---

## 10. Decisioni che mi servono da te

1. **Un solo via libera per partire dalla Fase 1** (la correzione del conteggio delle agevolazioni)? È la più piccola e non cambia l'aspetto del portale.
2. **Le «Novità» notturne** possono comparire solo dentro il portale, oppure vuoi anche un avviso fuori (es. e-mail allo studio)? Oggi non esiste nessun invio.
3. **Conteggi anonimi tra gli studi** (quanti lavori vogliono un bando, quanti «non è per me»): va bene usarli per dare la priorità allo studio? Non escono nomi né importi.

---

## 11. Stato dei lavori (10 novembre 2026)

Costruito e provato nel portale (backend + schermate), **in quest'ordine di percorso: Agevolazioni → Allocazione → Budget → Confronto** (il menu lo rispecchia, con la barra «1 › 2 › 3 › 4» in cima a ogni pagina).

| Limite trovato | Cosa è stato fatto |
|---|---|
| Due esoneri per persone diverse non si sommavano | «Chi assume l'impresa»: una riga per persona (sesso, età, da quanto è senza lavoro); l'agente assegna **una sola** misura per persona (la più ricca) e persone diverse si sommano. Mesi veri della fascia (12 o 24), non più un intervallo, quando i dati ci sono. Una persona con dati mancanti si mostra ma **non entra nel totale** |
| Il lavoratore non entrava nel calcolo | Entra: età, sesso, mesi senza lavoro (`worker_fit`, `assign`). Se una misura è certa e una più ricca dipende da un dato mancante, conta la certa e l'altra si mostra a parte |
| **Trovato nella verifica del 10 novembre:** gli esoneri 2026 si sommavano anche nel piano del 2027 | Valgono solo per chi è assunto entro il 31/12/2026: ora per ogni persona si indica l'anno di assunzione; chi entra nel 2027 non li ha (serve una nuova norma, che non si inventa) |
| **Trovato nella verifica del 10 novembre:** la ricerca dei bandi regionali non trovava i nomi con apostrofo o «&» («all'occupazione», «Smart&Start») e senza regione mostrava i bandi di tutte le regioni | La punteggiatura del nome si confronta come uno spazio; senza la regione della sede i bandi regionali non si mostrano e si chiede la regione |
| Le circolari cambiano e nessuno guarda | Parziale: ogni pagina dice **quanti giorni fa** sono state controllate le regole e, oltre 45 giorni, lo scrive tra le cose che servono. **La sentinella sul testo delle circolari non c'è ancora** (va prima verificato quali pagine INPS si leggono da un server) |
| Misure regionali senza collegamento automatico | Rettificato (vedi §2.3, punto 5): ora la ricerca parte da sola e la misura mostra «N bandi aperti · regione» |
| Allocazione: si ricalcola tutto | **Misurato prima di toccarlo**: 0,7 secondi sul database di prova. Non ottimizzato: la scheda precalcolata non serve ancora (si rimisura sul database vero quando ci saranno più bandi studiati) |
| Il giudizio di pertinenza non impara | «Il giudizio sbaglia» su ogni bando: segnale **anonimo** (un codice per studio, ATECO a 2 cifre e regione) nella tabella `relevance_signals`; l'elenco dei bandi su cui gli studi dissentono è nel Quartier Generale → Catalogo («Giudizi di pertinenza segnalati dagli studi»). Nessuna parola entra nel dizionario da sola |
| Probabilità di successo sempre a mano | Nel «Valore reale e incassi» compare «Dal Confronto: 2 ammessi su 3 budget con esito noto. Usa 67%» (solo con almeno 3 esiti decisi, mai applicato da solo) |
| Nessuna novità dall'ultima volta | L'Allocazione mostra **cosa è cambiato dall'ultima apertura** (bandi diventati adatti o non più adatti) con «Ho visto». *Non è notturna*: si calcola all'apertura della pagina |
| Coda di studio coordinata tra gli studi | **Non fatta**: serve la tua decisione sui conteggi anonimi tra studi |
| **Trovato nella verifica del 10 novembre:** «Voucher occupazionali» si collegava al «Voucher Doppia Transizione» (stessa parola, altro scopo) | Le misure regionali cercano parole precise («voucher occupazion…», «trasformazione dei tiroc…») |
| **Trovato nella verifica del 10 novembre:** dal Budget il Confronto si apriva con il bando e le quote salvate prima, non con quelli del budget appena controllato | Il Confronto prende bando, ATECO e quote del budget; le scelte salvate non li sovrascrivono |
| Il consiglio del Confronto non rispettava le regole del bando | Ora **ogni consiglio e ogni tuo budget sono verificati** con le regole di quota del bando; se non le rispettano, la versione che le rispetta e il tasto «Parti da questa versione» |
| Due motori, nessun legame con l'Allocazione | Il legame passa dal Budget (passo 3): «Confronta con chi ha già vinto». La tabella unica dei budget storici **non è fatta** |
| Peso di qualità dei template (60 criteri sì/no) | **Non fatto**: cambierebbe i numeri del consiglio e va deciso insieme |

### 11 bis. Seconda verifica dell'utente (10 novembre 2026)

| Problema segnalato | Correzione |
|---|---|
| Una misura che non chiede un progetto (credito d'imposta automatico) portava comunque al Budget («Bozza di budget dall'azienda») e veniva chiamata «bando» | Ogni modalità dice se ha un budget e se è un bando o un'**agevolazione**. Le agevolazioni senza budget (crediti d'imposta automatici, garanzie, incentivi alle assunzioni, ristori) non hanno nessun pulsante verso il Budget, in nessuna pagina; nel menu del Budget non si scelgono; i budget dall'Allocazione le saltano e le elencano a parte; la bozza dal profilo le rifiuta. Etichetta «Agevolazione · niente budget» |
| A un'impresa abruzzese compariva il bando del Comune di Corleto Perticara (Basilicata) | Nuovo strato di verifica: un bando di un ente locale (Comune, GAL, Unione dei comuni, Camera di commercio) si propone solo con una **prova positiva** che sia nella regione dell'impresa (capoluogo o provincia nel nome, oppure la regione nella scheda ufficiale). Sotto una misura regionale compaiono solo voci provate nella regione |
| «Studia» seguito da «nessuna regola», poi «Completa la ricerca» → pagina Bandi → «analisi parziale» → «Rifai lo studio» → di nuovo parziale | Lo studio si fa dove si clicca e dice in una frase cosa si può fare (budget sì/no, valore sì/no, e perché). Nessun rimando ad altre pagine; «Riprova la lettura» solo se non si è letto nessun documento ufficiale o se la lettura è vecchia. «Studia e fai il budget» apre il Budget solo se il budget si può fare |
| Troppi clic e scorrimenti | «Prepara e apri i budget dei bandi» in un clic; dopo uno studio la scheda del bando si apre ed è evidenziata; dalle Agevolazioni l'Allocazione apre direttamente il bando studiato |

### 11 ter. Terza verifica dell'utente (10 novembre 2026)

- **ON compariva in «Bandi adatti» e spariva in «Tutti insieme».** Era un bando da verificare mostrato in verde nel grafico. Ora il grafico mostra solo gli adatti (verde: si sommano; viola: a progetto) e sotto il totale c'è «Fuori da questa somma, e perché», con il pulsante che risolve ogni caso. Nuovo controllo sui requisiti dell'impresa: «costituite da non più di 60 mesi» e compagine giovanile o femminile, dalla frase del bando e dal profilo (anno di costituzione, età dei soci, prevalenza femminile).
- **Cifre uguali tra le due pagine.** Il valore «da solo» si calcola sulle spese del piano (budget, acquisti previsti, previsione).
- **Bando o agevolazione.** La forma della scheda ufficiale e il nome correggono la modalità letta dalle parole: un finanziamento per investimenti è un bando a progetto, con budget.
- **Ricerca su tutto il catalogo.** Le schede non ancora lette restano candidate («Scheda da leggere») e l'Allocazione le legge subito a lotti (`POST /bandi/catalog/read-more`); una pagina che non risponde non blocca la fila.
- **Caricamento visibile.** Il riquadro «L'azienda» si riempie di nero mentre si carica; poi si passa da soli ai bandi adatti.

