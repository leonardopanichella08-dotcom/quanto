# QUANTO — messa in produzione

Il codice sta sul ramo `feat/postgres-dati-veri`. **Non si fonde in `main` (e quindi non va in produzione) finché non sono impostate le variabili qui sotto:** senza database il server risponde 503 con un messaggio chiaro.

## 1. Database PostgreSQL (obbligatorio)
Serve un PostgreSQL esterno (Neon, Supabase, Vercel Postgres, RDS…). Imposta **una** di queste, con l'indirizzo completo:

```
QUANTO_DATABASE_URL=postgresql://utente:password@host/nome_db?sslmode=require
```
Le tabelle si creano da sole al primo avvio (migrazioni numerate in `backend/app/core/schema.py`, sotto lock: più istanze insieme non si pestano i piedi). Con un pooler tipo PgBouncer/Neon pooled funziona: non usa prepared statement.
Per copiare un vecchio archivio SQLite: `python -m app.tools.sqlite_to_postgres percorso/quanto.sqlite3`.

## 2. Segreti (obbligatori)
| Variabile | A cosa serve | Come crearla |
|---|---|---|
| `QUANTO_JWT_SECRET` | firma dei token di accesso | `python -c "import secrets;print(secrets.token_urlsafe(48))"` |
| `QUANTO_FILE_KEY` | cifratura a riposo dei documenti dei clienti (AES-256-GCM) | `python -c "import secrets;print(secrets.token_hex(32))"` — **non perderla**: senza, i file non si aprono più |
| `QUANTO_PII_KEY` | token anonimi di nomi, codici fiscali, IBAN | già impostata su Vercel |
| `QUANTO_SIGNING_KEY` | firma Ed25519 del registro | già impostata su Vercel |
| `QUANTO_BOOTSTRAP_ADMIN_EMAIL` / `_PASSWORD` | primo manager, creato **una sola volta** se non esiste nessun utente (poi togli le due variabili) | password di almeno 12 caratteri |
| `CRON_SECRET` | il lavoro notturno che aggiorna il catalogo dei bandi (Vercel Cron) | una stringa lunga a caso |

`QUANTO_AUTH_REQUIRED` è **acceso per impostazione predefinita**: si spegne solo scrivendo `0` (sviluppo locale). Il vecchio codice `QUANTO_1` non esiste più: si entra con e-mail e password (scrypt, blocco dopo 5 errori per 15 minuti, token da 8 ore, revoca immediata al cambio password o alla disattivazione).

## 3. Intelligenza artificiale (facoltativa, ma serve per Stadio 1 arricchito, Stadio 3 e riepiloghi)
```
ANTHROPIC_API_KEY=...            # senza chiave non si chiama nulla: tutto resta deterministico
QUANTO_LLM_MODEL=claude-sonnet-5 # facoltativo
QUANTO_LLM_PASSES=3              # letture indipendenti dello Stadio 3 (2-7)
```
Garanzie: ogni valore estratto deve arrivare con la frase esatta del documento (se la frase non c'è, il valore è scartato); il confronto tra le letture lo fa il codice (concordanza → pubblicata, disaccordo → coda del consulente); ogni cifra dei riepiloghi è ricontrollata dal validatore numerico e, se non torna, si usa il testo fisso.

## 4. OCR per i PDF scansionati (decisione da prendere)
Il lettore usa il testo del PDF quando c'è. Per le **scansioni** serve un motore OCR: l'interfaccia è pronta (`app/core/fonte_c/ocr.py`) ed è collegato Tesseract (`QUANTO_OCR_ENGINE=tesseract`), ma Tesseract è un programma da installare sul server e **non gira su Vercel**. Senza motore le scansioni vengono rifiutate con un messaggio chiaro (mai un testo inventato). Opzioni: un servizio OCR in cloud (da collegare: serve la tua scelta e la chiave) oppure ospitare il backend su un contenitore con Tesseract.
Soglia di confidenza dei campi: `QUANTO_FIELD_CONFIDENCE_MIN` (default 0,90).

## 5. Dati che il codice NON contiene (vanno caricati da un manager)
- **Fonte B** — Quartier Generale → *Tabelle ufficiali*: CCNL (ore, oneri, TFR per livello), parametri (tempo determinato, occasionali), aliquote d'ammortamento, benchmark. Ogni file va con il documento ufficiale di origine e l'attestazione. **Finché non ne carichi almeno una, le voci di personale vengono respinte** («tabella CCNL non disponibile»).
- **Fondi dell'allocazione** — Quartier Generale → *Fondi*: si ricavano dalle regole pubblicate di un bando (dotazione massima e de minimis li indica una persona).
- **Banca pattern** — Quartier Generale → *Banca pattern*: CSV di budget storici con la fonte di ogni riga; gli archetipi si calcolano con k-means (serve un minimo di 6 budget per categoria).

## 6. Verifiche dopo il primo deploy
`GET /api/v2/health/ready` deve rispondere `READY`; il pannello «Memoria e database» del Quartier Generale deve dire *PostgreSQL*. Controlla anche la dimensione dell'ambiente Python (limite di Vercel: 250 MB decompressi): sono state aggiunte `psycopg`, `psycopg-pool`, `pdfplumber`.
