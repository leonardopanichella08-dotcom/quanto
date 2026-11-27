# Diario di staffetta

Due sessioni di Claude Code lavorano su `main`. Prima di toccare qualcosa, scrivi qui sotto in «In corso ora» chi sei e su cosa lavori;
quando hai finito sposta la riga nel «Diario» (in cima, la più recente prima) e svuota la tua voce.

## In corso ora
| Sessione | Da quando | Su cosa (file o area) | Note |
|---|---|---|---|
| QUANTO (chat principale) | 27/11 | homepage: `Landing.css` | tutto più piccolo e più lontano dai bordi |

## Diario
### 2026-11-27 · homepage: verbi compatti, pratica come carta 3D, via l'anteprima del portale
- Verbi: al posto della scritta enorme «QUANTO trova.», una riga con i quattro verbi e una capsula gialla che scivola da uno all'altro ogni 3,2 s (`Verbs`, misura con `useLayoutEffect`); sotto la frase e un filo che si riempie. Su telefono 2×2.
- Processo: tolta la linea temporale con i cinque cerchi; resta il titolo e una carta (`PracticeCard`) che entra inclinata e si raddrizza scorrendo, segue il mouse in 3D con un riflesso giallo, ondeggia piano; il passo corrente sta in testa alla carta, la barra di avanzamento sul bordo in basso.
- Tolta la sezione «quanto · impresa di prova» (ricostruzione del portale): eliminati `PortalPreview.jsx` e `PortalPreview.css`, usati solo lì.
- Build ok; provato nel browser a 1280 e 390 px, nessuno scorrimento laterale.
### 2026-11-24 · homepage: apertura bianca, meno testi, riquadri con immagini
- Tolta la foto dell'apertura: fondo bianco, titolo nero, barra con scritte nere. Sotto il titolo sette riquadri (`Bento`, `TILES`): squadra dei 4 agenti, due schermate vere, «60 controlli per voce» che conta, Fiuto e Spunta che ondeggiano, registro firmato che si scrive. Entrano a scaglioni, le schermate scorrono piano dentro la cornice.
- Tolti i paragrafi grigi descrittivi (metodo, gestionale, agenti, video, prezzi, didascalie delle schermate, fumetti degli agenti); passi del processo, verbi e liste dei prezzi accorciati a una riga.
- Build ok; provato nel browser a 1024 e 390 px, nessuno scorrimento laterale, console pulita.
### 2026-11-24 · homepage: immagine al posto del video, tutto centrato, verbi uno alla volta
- Tolto il video di sfondo (`public/landing/sfondo.mp4`, 4,8 MB) e `skyline-alba.jpg`: al loro posto `apertura.webp` (1920×1080, fotogramma del video) e `apertura-1080.webp` per il telefono, componente `BgImage`.
- Tutto centrato: apertura, titoli e testi, gestionale, processo (5 tappe in fila con il passo corrente sotto, su telefono tutte in colonna), agenti, principi, prezzi, domande con la chat sotto, piè di pagina.
- Sezione «Trova / Studia / Costruisce / Controlla» rifatta: «QUANTO trova.» al centro, la parola cambia da sola ogni 3,6 s (solo quando è in vista), quattro schede sotto con la barra gialla.
- Build ok; provato nel browser a 1024, 1440 e 390 px, nessuno scorrimento laterale.
### 2026-11-23 · homepage: si apre sul titolo, menu da telefono, iPhone
- La pagina si apriva sulle domande: «Chiedi a QUANTO» usava `scrollIntoView` all'avvio. Ora scorre solo dentro la chat e solo dopo una domanda; la homepage parte sempre dall'alto (anche con `#sezione` nell'indirizzo, che viene tolto).
- Tolta la pillola grigia «Per studi di commercialisti e consulenti». Menu a tendina sotto 1080 px, voce della sezione in lettura accesa, tre domande pronte nella chat, Esc chiude modulo e menu.
- iPhone: `viewport-fit=cover` e margini per tacca e barra, campi a 16 px (niente zoom), modulo di accesso come foglio dal basso, pagina ferma dietro il modulo, video forzati muti per l'avvio automatico, `ignoreMobileResize` di ScrollTrigger, effetti al passaggio spenti sugli schermi a tocco.
- Build ok; provato nel browser a 1440 e 390 px. Nessun test backend toccato.
### 2026-11-18 · homepage: agenti con pagine dedicate, prezzi, apertura
- `AgentPage.jsx/.css` nuovi (tab `agente-<id>`), `Landing.jsx/.css`, `App.jsx`, video `public/landing/sfondo.mp4` sostituito (1920×1080). Build ok, controllato da computer e telefono.

### 2026-11-18 · assistente a tutto schermo con le mascotte
- `assistant/AssistantContext.jsx` riscritto nella parte visiva (Screen, Msg, Peek, RunCard con la mascotte), `assistant/tasks.js` + agevolazioni e confronto, `App.jsx` bridge.isOwner, stili `.asst-*` sostituiti in `index.css`.
- Provato in locale nel browser (computer e telefono). Nessun test backend toccato.

### 2026-11-17 · Quartier Generale ricostruito, chatbot, Marketing
- Nuovi: `core/datacenter.py`, `core/hq_assistant.py`, `core/marketing.py`, `endpoints/marketing.py`, migrazione 25; frontend `hq/HQ.jsx` + Today, Ask, Marketing, Data, System.
- Test: `tests/test_hq_data_marketing.py` (15) e i test di accessi/HQ/utenti verdi (79). Suite completa non rilanciata.

### 2026-11-16 · richieste di accesso e Quartier Generale
- Registrazione come richiesta, approvazione con livello e e-mail pronta (`core/access.py`, `endpoints/hq.py`, migrazione 24); Quartier Generale in 5 sezioni con grafici (`frontend/src/components/hq/*`).
- Test: `tests/test_access_requests.py` (11), `test_users_auth.py`, `test_hq_bandi.py` verdi (64). Suite completa non rilanciata.

### 2026-11-15 · homepage editoriale, newsletter e 200 FAQ
- Homepage rifatta su fondo bianco con apertura fotografica, video dei 4 agenti, Insights «in arrivo», newsletter con consenso, 200 FAQ dal dossier.
- Backend: `app/core/newsletter.py`, `POST /api/v2/newsletter/subscribe`, migrazione 23; test in `tests/test_agents.py` (33 verdi con `test_postgres`).
- Resta: controllo visivo su telefono e suite completa, entrambi bloccati dal disco C: pieno.

### 2026-11-15 · setup della collaborazione
- Creati `CLAUDE.md`, `PROGRESS.md`, `COLLAB_LOG.md`, `COLLAB_GUIDE.md`, `.env.example` (radice) e completato `backend/.env.example` (tutte le variabili, senza valori).
- `.gitignore`: chiavi e file di ambiente esclusi, esempi e file di collaborazione inclusi.
- Stato di partenza: commit `69f1770`, 676 test verdi, produzione allineata a `main`.
