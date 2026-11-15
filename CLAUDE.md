# QUANTO — istruzioni per Claude Code

QUANTO è una piattaforma per studi di commercialisti e boutique di finanza agevolata: trova le agevolazioni adatte a ogni impresa cliente,
ne studia le regole dai testi ufficiali, costruisce progetto e budget del bando e li controlla con 60 criteri deterministici; un piano
(allocazione) dice quale agevolazione paga quale spesa. Produzione: https://quanto-self.vercel.app (Vercel, deploy automatico da `main`).

A inizio sessione leggi anche **PROGRESS.md**, **COLLAB_LOG.md** e **COLLAB_GUIDE.md** (due sessioni lavorano sullo stesso `main`).

## Stack
- **Backend** `backend/`: Python 3.12, FastAPI, PostgreSQL (psycopg + pool; in locale e nei test Postgres incorporato `pixeltable_pgserver`),
  HiGHS (MILP dell'allocazione), Ed25519 + Merkle (registro firmato), pypdf/OCR facoltativo. Entrata `backend/main.py`; su Vercel `backend/api/index.py`.
- **Frontend** `frontend/`: React 18 + Vite 7 + Tailwind 3, icone lucide-react, animazioni GSAP (solo homepage). Nessun calcolo monetario nel client.
- **Deploy**: `vercel.json` (build statico del frontend + funzione Python, regione fra1, maxDuration 60 s, cron notturni `/api/v2/cron/*`).
- **CI**: `.github/workflows/ci.yml` — pytest su Postgres 16, build del frontend, audit delle dipendenze di produzione.

## Struttura
```
backend/app/api/endpoints/   rotte /api/v2/* (bandi, profile, allocation, budget, fonte_c, hq, cron, tokens, clients…)
backend/app/core/            logica: matching (giudizio dei bandi), relevance (territorio/settore/requisiti), funding_modes (bando o agevolazione,
                             budget sì/no), catalog_meta (schede del catalogo), pipeline (studio di un bando), measures (agevolazioni sul lavoro),
                             allocation_engine (MILP), budget_basis + company_profile (spese dell'impresa), valuation, registry/merkle, fonte_c (documenti)
backend/app/data/            catalogo curato, manuale_processi.md, PDF dei documenti
backend/tests/               pytest (676 test), conftest con Postgres incorporato o QUANTO_TEST_DATABASE_URL
frontend/src/App.jsx         navigazione e collegamenti tra pagine
frontend/src/components/     una pagina per file: AllocationView, Agevolazioni, BudgetCanvas, Confronto, BandiLibrary, Landing (homepage)…
frontend/src/lib/            api.js (tutte le chiamate), format.js, nav.js, idleReason.js
docs/                        dossier e riassunto (PDF generati da script Python), agenti/I_tre_agenti.md
```

## Comandi
```bash
# backend
cd backend && python -m venv .venv && .venv/Scripts/activate        # Linux/mac: source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q                                                  # suite completa: ~25 min, va lanciata da sola
python -m pytest tests/test_agents.py -q                             # test mirati: preferirli durante il lavoro
python scripts/run_local.py                                         # backend locale: legge backend/.env, PostgreSQL incorporato in backend/.localdb
                                                                     # (il backend NON legge .env da solo; senza --prod ignora ogni database del file)

# frontend
cd frontend && npm install
npm run dev                                                          # http://localhost:5173, /api inoltrato a :8000
npm run build                                                        # su Windows anche: node node_modules/vite/bin/vite.js build

# documenti (dopo modifiche rilevanti, aggiornare il numero di test in docs/dossier/facts.json e docs/riassunto/build_riassunto.py)
cd docs/dossier && python build_dossier.py
cd docs/riassunto && python build_riassunto.py                       # poi copiare i due PDF in backend/app/data/docs/
```
Variabili d'ambiente: vedi `.env.example` (radice) e `backend/.env.example`. In locale nulla è obbligatorio tranne `QUANTO_PII_KEY` e `QUANTO_FILE_KEY`
per caricare documenti. Utenti di prova locali: solo su localhost, mai in produzione.

## Regole del prodotto (non vanno mai rotte)
- **Mai inventare dati.** Se un dato manca si chiede o si dichiara come lacuna; nessun valore di default inventato.
- I calcoli sono **deterministici**: un LLM non decide cifre (se c'è, scrive solo testo controllato a valle).
- Solo i bandi **ADATTI** entrano nelle somme; «da verificare» non si somma mai e non appare in verde.
- Un bando non pertinente non deve **mai** apparire come possibile (territorio con prova positiva, settore, requisiti dell'impresa).
- Un'**agevolazione senza budget** (credito d'imposta automatico, garanzia, incentivo alle assunzioni, ristoro) non ha pulsanti verso il Budget e non si chiama «bando».
- QUANTO non deve aiutare a far passare costi ordinari o gonfiati come costi di progetto.
- Una ditta individuale non legge mai la parola «bilancio» (dichiarazione dei redditi).
- Tutto gratuito per ora: `QUANTO_TOKENS_CHARGE` resta spento finché il titolare non dice altrimenti.
- Nessun dato personale in URL, log o nomi mostrati (le buste paga si mostrano come «Busta paga (documento N)»).

## Convenzioni
- **Lingua**: interfaccia, testi, commenti e messaggi di commit in **italiano semplice**. Frasi brevi, esempi concreti.
- **UI**: minimale, stile Apple; spiegazioni dietro una «i», sezioni di base chiuse; ogni pulsante dice cosa fa e lo fa davvero; niente scorrimenti o
  riselezioni inutili (ogni azione porta al punto giusto). Homepage e «La visione»: solo i colori del marchio (bianco, nero, grigi neutri,
  giallo **#F1E21B**; **niente blu**), nessun riquadro né griglia di schede, animazioni GSAP che mostrano il lavoro, barra in vetro liquido che sparisce scendendo,
  niente logo «Q» giallo (solo la scritta), poche parole. Il video dei 4 agenti parte da solo, in loop, senza controlli. FAQ: 8 in pagina; tutte le 200 in
  `frontend/src/data/faq.js`, servite come `public/faq.md` (rigenerato a ogni build, non collegato dall'interfaccia, per motori di ricerca e AI) e interrogabili
  da «Chiedi a QUANTO» (`lib/faqSearch.js`: confronto di parole, nessun modello).
- **Codice**: Python con type hint e docstring che spiegano il *perché*; React a funzioni con hook; chiamate solo via `frontend/src/lib/api.js`.
- Ogni correzione di logica porta un **test** in `backend/tests/` (i test raccontano il caso: `test_un_bando_di_un_comune_fuori_regione_non_si_propone…`).
- Documentare i cambi di comportamento in `backend/app/data/manuale_processi.md` (sezione numerata) e, se rilevanti, in `docs/agenti/I_tre_agenti.md`.
- Commit in italiano, frase che dice cosa cambia per l'utente; ultima riga `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Mai committare segreti, `.env`, chiavi, dati di clienti reali. I documenti di prova sono sintetici (`backend/scripts/make_sample_company.py`).

## Trappole note
- La suite completa dura ~25 minuti: non lanciarla insieme al backend locale; spegnere Postgres locale con `pg_ctl ... stop -m fast`.
- Su Windows gli heredoc bash con apostrofi si rompono: per patch lunghe scrivere uno script Python con il tool Write.
- GSAP + React StrictMode: usare `fromTo` con valori finali espliciti, non `from` (in sviluppo l'effetto parte due volte).
- Newsletter: il modulo è stato tolto dalla homepage; `POST /api/v2/newsletter/subscribe` resta (salva solo e-mail e consenso, migrazione 23) per un uso futuro.
- Il backend locale serve il codice vecchio finché non lo si riavvia.
- `index.css` definisce già una classe globale `.glass` (riquadro bianco): nelle pagine pubbliche non usarla come nome di stato (si vedevano due barre sovrapposte); si usa `is-glass`.
