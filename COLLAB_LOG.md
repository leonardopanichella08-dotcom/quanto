# Diario di staffetta

Due sessioni di Claude Code lavorano su `main`. Prima di toccare qualcosa, scrivi qui sotto in «In corso ora» chi sei e su cosa lavori;
quando hai finito sposta la riga nel «Diario» (in cima, la più recente prima) e svuota la tua voce.

## In corso ora
| Sessione | Da quando | Su cosa (file o area) | Note |
|---|---|---|---|
| — | — | — | — |

## Diario
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
