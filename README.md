# QUANTO — Financial Knowledge Operating System (ex FKOS)

Motore deterministico di budgeting per bandi pubblici, allocazione annuale multi-fonte e asseverazione crittografica
(Merkle Root in un registro append-only firmato). Nessun collegamento a blockchain. L'LLM, se presente, è solo un
renderer a valle di un Validatore Numerico: **nessuna cifra nel testo che non sia nel JSON bloccato**.

```
backend/   FastAPI · Decimal engine (60 criteri) · Merkle · registro firmato Ed25519 · MILP (HiGHS) · ingestion Fonte A
frontend/  React + Vite + Tailwind (nessun calcolo monetario lato client)
            Grafica: bianco come colore principale, vetro liquido stile Apple (`.glass`, `.card`, `.glass-strong`) e i gialli del marchio
            (`#f1e21b`, `#fffb96`) in gradiente (`.bg-liquid`); icone Lucide a tratto sottile. Token in `tailwind.config.js` e `src/index.css`.
            Font "Now": non è su Google Fonts, quindi finché i file non sono in `frontend/public/fonts` (e nei `@font-face` di `index.css`)
            si usa Outfit. Loghi in `frontend/public/brand`.
```

## Avvio locale

```bash
cd backend && python -m venv .venv && .venv/Scripts/activate   # Linux/mac: source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest                                               # 298 test
uvicorn main:app --reload --port 8000                          # http://localhost:8000/docs

cd ../frontend && npm install && npm run dev                   # http://localhost:5173 (proxy /api -> :8000)
```

Configurazione: `backend/.env.example`. **In produzione impostare almeno `QUANTO_SIGNING_KEY`, `QUANTO_PII_KEY`,
`QUANTO_DB_PATH` (volume persistente) e `QUANTO_AUTH_REQUIRED=1`.** Senza `QUANTO_SIGNING_KEY` il server usa una chiave di
sviluppo e la UI lo segnala: le attestazioni non hanno valore probatorio.

## Le pagine dell'app

| Pagina | A cosa serve |
|---|---|
| **Bandi** | Libreria dei bandi con regole, fonti e lacune per ciascuno, e **ricerca sul web**: scrivi il nome di un bando (es. "Resto al Sud") e QUANTO lo cerca, scarica le pagine e i PDF ufficiali, li salva in memoria (testo integrale, ricercabile) e li legge tutti. Da qui si "usa" un bando nel Budget. |
| **Budget** | Elenco voci di costo (tutte le categorie: personale, beni, consulenze, spese generali, formazione). Demo *realistica* (15 voci) o *stress* (46 voci che attivano tutti i 60 criteri), import/template Excel, editor di riga guidato dal catalogo campi; ogni modifica ri-valida. Registrazione della Merkle Root. |
| **Algoritmo** (non è nella barra) | Si apre solo dal pulsante **«Guarda come ha lavorato»** della pagina Budget ("Torna al Budget" per uscire). Vista grafica di ogni passo del motore: fasi, mappa criteri×voci, cascata degli importi, limiti, albero di Merkle. |
| **Allocazione** | MILP (HiGHS) che distribuisce il budget sui fondi rispettando tetti, quote, non cumulabilità, de minimis e finestre mensili; what-if e tre obiettivi. |
| **Confronto** (ex Pattern) | Confronto della ripartizione tra macro-categorie con archetipi di budget premiati (coseno + scostamento in pp). Non stima la probabilità di vincita. |
| **Verifica** (ex Auditor) | Verifica che un budget non sia stato alterato: confronto radice presentata/ricalcolata con il registro firmato; simula manomissione. |
| **Guida** | Spiegazioni in parole semplici: percorso rapido, **Merkle Root passo passo** (demo interattiva con l'algoritmo vero, `POST /registry/merkle-lab`), ogni funzione con un esempio, glossario. In ogni pagina: striscia "come si usa" e icone `?` / parole sottolineate con spiegazione ed esempio (testi in `frontend/src/data/help.js`). |
| **Quartier Generale** | Area manager con codice (`QUANTO_HQ_CODE`, default `QUANTO_1`): panoramica KPI, timeline di ogni operazione, mappa delle operazioni, **Archivio bandi** (ogni documento scaricato con testo e file originale, regole e requisiti modificabili, scheda di controllo per il consulente, rilettura, esportazione ZIP, eliminazione con ripristino dei predefiniti), fascicoli per progetto, documenti, database (lettura, CSV, eliminazione di righe; il registro firmato `anchors` è protetto), ripresa di una run nell'Algoritmo. Lacune, regole in disaccordo e requisiti "da rivedere" sono visibili **solo qui**, non agli utenti. |

### Quartier Generale e memoria
Ogni operazione (validazione, registrazione, ingestion, allocazione, import…) viene scritta in `events`; ogni validazione
salva la *traccia completa* dell'algoritmo in `runs` (rivedibile dall'HQ; run identiche non sono duplicate). Le descrizioni sono
ripulite da IBAN/CF prima del salvataggio. Il codice HQ è verificato **lato server** (confronto a tempo costante, blocco dopo
5 tentativi/10 min, token HMAC in `X-HQ-Token`); il database è esposto solo in lettura e solo per tabelle in whitelist.
**Il default `QUANTO_1` è un segreto debole e pubblico in questo README: impostare `QUANTO_HQ_CODE` in produzione.**

### Bandi: cosa è (e cosa non è) la "comprensione" del bando
Il catalogo (`app/data/bandi_catalog.py`) contiene 6 bandi con regole compilate a mano da **fonti secondarie/ufficiali
consultate**, ognuna con fonte e confidenza. Non è una lettura automatica garantita del testo: l'estrattore sui bandi caricati
è deterministico (tassonomia → criteri) e segnala come *da revisionare* ciò che non sa classificare. FNC3-2024 è **parziale**.
Un caso reale: un riepilogo automatico dava Horizon al 15% di indiretti, il documento ufficiale dice 25% — per questo le regole
vanno verificate sul testo ufficiale prima dell'uso operativo. Se un bando non definisce una regola, il criterio è "non
valutato": nessun default inventato.

### Ricerca dei bandi sul web (`/bandi/research/*`)
1. **Cerca** (`search`): 3 vie insieme — **elenchi ufficiali** (Invitalia, MIMIT: funzionano anche da cloud), **Brave Search API** se imposti `QUANTO_BRAVE_API_KEY` (piano gratuito; la via affidabile in produzione) e 6 ricerche su Bing/DuckDuckGo Lite (gratuite ma spesso bloccate dai server cloud: da Vercel Bing risponde con risultati senza alcun legame, che vengono scartati). Scarto dei risultati che non nominano il bando, classificazione
   **UFFICIALE** (Gazzetta Ufficiale, Normattiva, EUR-Lex, ministeri, Invitalia, INPS, regioni…) o **SECONDARIA** (blog, portali). Si preselezionano solo le ufficiali.
2. **Scarica** (`fetch`, un indirizzo alla volta): pagina HTML, PDF o Word, con protezioni (solo http/https verso IP pubblici, redirect ricontrollati,
   niente porte strane, limiti di dimensione e tempo, tetto di richieste). Il testo integrale va in memoria (`bando_sources`) con indirizzo, tipo di fonte e impronta.
   L'interfaccia segue i collegamenti trovati (PDF, decreti, allegati, atti della Gazzetta) fino a 2 livelli, con priorità ai PDF e agli atti di legge.
3. **Analizza** (`analyze`): legge tutte le fonti in memoria. Per i documenti lunghi (leggi, manuali) usa solo i passaggi che nominano il bando.
   Requisiti collegati ai 60 controlli e temi come agevolazione, importi, chi può presentare domanda, età, territori, scadenze; atti di legge citati.
   **Se documenti diversi — o lo stesso documento — danno valori diversi per la stessa regola (es. contributo 75% e 70%) la regola non si pubblica:
   va in "da verificare a mano"** e diventa un controllo solo dopo la decisione di una persona.

**Scoperta senza motore di ricerca** (`app/core/discovery.py`, schema FKOS Fonte A Stadio 1). Da Vercel Bing risponde con risultati senza legame, quindi la ricerca non dipende da lui:
- **cataloghi**: `incentivi.gov.it` (≈5.900 misure nazionali, regionali, comunali, CCIAA, GAL, dalla sitemap) e Invitalia, confrontati per nome anche approssimativo;
- **portali per famiglia** (Erasmus+, coesione/FSE/FESR/PNRR, PSR, energia, export, cultura, lavoro…): si parte dai portali ufficiali e si seguono i link che nominano il bando, per due salti;
- **sigle di azione** (KA152, KA153, KA154, KA210, KA220): collegate alla loro pagina della Guida al Programma e ai loro nomi estesi («Youth Exchanges», «scambi giovanili»);
- **motori** in catena, il primo con risultati *pertinenti* vince: Brave / Serper / Tavily se imposti `QUANTO_BRAVE_API_KEY` / `QUANTO_SERPER_API_KEY` / `QUANTO_TAVILY_API_KEY` (piani gratuiti; la via affidabile in produzione), poi Bing e DuckDuckGo Lite.
La pertinenza è sul percorso dell'indirizzo, mai sul dominio, e una sigla presente basta da sola (una pagina «KA152 – Scambi giovanili» non dice «Erasmus»).

**Lettura dei documenti** (`requirements_extractor.py`, `analysis.py`): italiano **e inglese**, testo dei PDF ricomposto (le righe spezzate tornano frasi), tassonomia estesa (agevolazione, importi, chi può presentare domanda, età, territori, scadenze, durata, partner), documenti lunghi ridotti ai passaggi che nominano il bando, rete di sicurezza di «frasi salienti» da classificare. **Un documento non risulta mai vuoto senza dire perché**: testo non decodificabile, troppo breve, lungo e non pertinente, o senza frasi con obblighi/limiti/importi. Il resoconto per documento è salvato e visibile.

**Limiti dichiarati.** Le pagine costruite in JavaScript restituiscono poco testo; i PDF scansionati (immagini) non si leggono (nessun OCR); i motori di ricerca possono
bloccare le richieste automatiche (da Vercel non è garantito: in quel caso si incolla il link ufficiale); PDF oltre 12 MB o oltre il tempo disponibile si leggono in parte o
non si leggono (l'interfaccia lo segnala); la lettura è deterministica (pattern e tassonomia), non un LLM: i requisiti non classificati vanno in "da rivedere" e le regole
lette in automatico hanno affidabilità `PARSING` e vanno verificate sul testo ufficiale. Su Vercel la memoria è volatile (vedi sotto).

## Come funziona l'asseverazione (senza blockchain)

1. Ogni riga validata ha un hash SHA-256 canonico (Fonte C + tabella Fonte B versionata + regola Fonte A + calcolo).
2. Gli hash formano un Albero di Merkle (domain separation, nodi dispari promossi): la Merkle Root è l'impronta del budget.
3. `POST /registry/register` la scrive in un registro **append-only a catena di hash**: ogni voce include l'hash della
   precedente ed è **firmata Ed25519**. Nel registro c'è solo la radice e un identificativo di progetto opaco.
4. L'Auditor Portal ricalcola la radice dai dati (o riceve quella del QR), la confronta con il registro e verifica firma e
   integrità dell'intera catena. Modificare o cancellare una voce passata rompe la catena; un progetto non registrato non è
   mai "valido". Un'attestazione si verifica anche **offline** con la sola chiave pubblica (`/registry/public-key`).

**Limite dichiarato:** il registro è gestito da QUANTO, non da un testimone terzo indipendente. Chi controlla la chiave privata
e il database può riscrivere l'intera catena; la difesa è che la chiave *pubblica* venga fissata dall'auditor fuori banda e
che `head_hash` (`/registry/status`) sia pubblicato periodicamente (PEC, repository pubblico, marca temporale qualificata).

## Stato di implementazione

| Area | Stato |
|---|---|
| Missione Uno: validazione budget con **tutti i 60 criteri** (`GET /budget/criteria`) | ✅ |
| Criteri: un criterio si esegue solo se la riga/il bando forniscono il dato; altrimenti è **"non valutato"** (mai "superato") e il Conformity Score conta solo i controlli eseguiti | ✅ |
| Massimali % (consulenze, spese generali, comunicazione, immateriali) risolti in forma chiusa sul totale finale | ✅ |
| Merkle + registro firmato + Auditor Portal + verifica offline | ✅ |
| Missione Due: MILP (tetti fondo, quote per categoria, non cumulabilità, de minimis, finestre mensili, what-if, 3 obiettivi) | ✅ |
| Ingestion Fonte A: catalogo, cache, Stadio 2 deterministico, Stadio 3 (confronto passaggi fatto dal codice), coda di verifica umana | ✅ — non chiama alcun LLM: i passaggi AI arrivano dal client (`ai_passes`) |
| Export XLSX e PDF con CEP-ID + QR; webhook firmati HMAC | ✅ |
| Autenticazione ERP: OAuth 2.0 client-credentials (JWT HS256) o firma HMAC delle richieste | ✅ — attiva con `QUANTO_AUTH_REQUIRED=1` |
| Validatore Numerico + LLM Renderer | ✅ — nessun client LLM di default (`LLMClient` è il punto di estensione) |
| **Dati illustrativi**: tabelle CCNL/oneri/TFR (Fonte B), maggiorazione tempo determinato, limite occasionali, archetipi del pattern matching | ⚠️ da sostituire con fonti ufficiali |
| Quartier Generale, timeline, memoria (eventi/run/documenti/bandi), Algoritmo grafico, libreria Bandi, demo a 46 voci su tutte le categorie, import/template Excel | ✅ |
| Persistenza | ⚠️ SQLite (`QUANTO_DB_PATH`). PostgreSQL/pgvector non implementati; su Vercel il filesystem è volatile: **la memoria dell'HQ si azzera ai cold start** finché non si collega un DB esterno |
| Ingestione Fonte B da portali istituzionali, parser OCR di buste paga/F24 (Fonte C), Reparto consulenza, assicurazione | ❌ non implementati |

## Scelte che divergono dalla specifica (e perché)

- **Nessuna blockchain** (richiesta esplicita): al suo posto registro a catena di hash firmato; vedi limite sopra.
- **Merkle**: la bozza duplicava l'ultima foglia dispari (`[a,b,c]` ≡ `[a,b,c,c]`) e non separava foglie/nodi.
- **Verifica auditor**: la bozza confrontava la radice con se stessa (sempre valida). Ora legge il registro.
- **CCNL mancante**: la riga è respinta, non calcolata su parametri "standard" inventati.
- **Override ore**: può solo ridurre le ore CCNL (alzarle gonfiava il massimale orario).
- **Score/totali**: `richiesto` include oneri e TFR (la bozza li escludeva → approvato > richiesto → score > 100 → errore 500).
- **Allocazione**: MILP esatto al posto del "primo fondo compatibile"; importi in centesimi interi ri-verificati.
- **Anonimizzazione**: HMAC con chiave segreta invece di SHA-256 con sale costante (CF/IBAN sono enumerabili).
- **API**: CORS con origini esplicite (mai `*` + credenziali), nessun dettaglio interno nelle risposte d'errore.
- **PDF FKOS v2, Modulo 10**: l'esempio (31,58 €/h → 26.148 €) non coincide con le sue tabelle:
  `(38.000 + 11.400 + 3.165,40) / 1.656 = 31,74 €/h` → **26.282,70 €** (valore usato nei test).
- **Criterio 48** (intensità di aiuto) e **49** (de minimis) sono controlli sul budget, non rettifiche di riga: segnalano il
  superamento e indicano il contributo/base massimi, non riducono i costi.

## Deploy (Vercel + GitHub)

`vercel.json` in root espone il frontend statico e le API FastAPI come funzione Python. Repository, remote e variabili
(`vercel env add …`) vanno creati/collegati manualmente: chiavi e segreti solo in Vercel/GitHub Secrets, mai nel codice.
La CI (`.github/workflows/ci.yml`) presuppone che `quanto/` sia la root del repository. Poiché il registro deve persistere, su Vercel serve un database esterno (l'adattatore SQLite
in `app/core/db.py` va sostituito) — con SQLite in `/tmp` le registrazioni si perdono a ogni cold start.


## Dati veri, memoria persistente, accesso (ramo `feat/postgres-dati-veri`)
Vedi **`docs/DEPLOY.md`** per le variabili e i passi di messa in produzione.
- **PostgreSQL** al posto di SQLite (`db.py`, `schema.py`): memoria persistente; registro firmato append-only anche a livello di database.
- **Fonte B nel database** (`fonte_b.py`, `fonte_b_admin.py`): nessuna tabella nel codice; bozza → attestazione della fonte → pubblicazione, versioni per data di validità, `reference_date` per ricalcoli identici.
- **Fonte C** (`fonte_c/`): PDF di buste paga, bilanci, F24, cifrati a riposo; testo del PDF o OCR; ogni campo ha una confidenza e sotto soglia resta in verifica; dati personali solo come token.
- **Missione Due** su bilancio caricato e fondi ricavati dai bandi (`funds.py`); nessun dato d'esempio nell'app.
- **Ricerca come da schema**: ricerca nell'elenco interno (`GET /bandi/search`) → conferma (`POST /bandi/research/confirm`) → controllo cache → estrazione.
- **Utenti** (`users.py`): scrypt, blocco, ruoli USER/MANAGER, revoca dei token; `QUANTO_AUTH_REQUIRED` acceso di default.
- **Banca pattern e k-means** (`pattern_bank.py`); **LLM** (`llm.py`) per Stadio 3, catalogo continuo (`catalog_job.py`) e riepiloghi verificati.
- I test girano su PostgreSQL vero (incorporato in locale con `pixeltable-pgserver`, servizio in CI).
