# Come lavorano insieme due sessioni di Claude Code

## Regole
1. **Si lavora direttamente su `main`.** Niente rami lunghi. Ogni push su `main` va in produzione (Vercel): solo codice che funziona.
2. **Inizio sessione**
   - `git pull --rebase`
   - leggere `CLAUDE.md`, `PROGRESS.md`, `COLLAB_LOG.md`
   - scrivere la propria riga in «In corso ora» di `COLLAB_LOG.md` (area e file su cui si lavora), commit e push subito, così l'altra sessione lo vede.
3. **Durante**
   - Non toccare file che l'altra sessione ha dichiarato in «In corso ora»; se serve, scriverlo nella sua riga e aspettare.
   - Commit piccoli e frequenti, messaggio in italiano che dice cosa cambia per l'utente.
4. **Prima di ogni push**
   - `git pull --rebase` (risolvere i conflitti tenendo il lavoro di entrambe le sessioni; mai `--force`).
   - **Test verdi**: i test mirati dell'area toccata (`python -m pytest tests/<file> -q`) e `npm run build` se si è toccato il frontend.
     La suite completa (~25 min) prima di un cambio di logica ampio o a fine giornata; la CI la rifà su ogni push.
   - Mai committare `.env`, chiavi o dati di clienti reali (controllare `git status` e `git diff --cached`).
5. **Fine sessione**
   - Aggiornare `PROGRESS.md` (fatto, a metà, prossimi task) e `COLLAB_LOG.md` (spostare la riga «In corso ora» nel «Diario» con cosa è stato fatto e cosa resta).
   - Se è cambiato il modo di lavorare o una regola del prodotto, aggiornare `CLAUDE.md`.
   - Commit e push (con `git pull --rebase` prima).

## Se qualcosa va storto
- Conflitto che non si capisce: fermarsi e scriverlo nel «Diario», non sovrascrivere il lavoro dell'altra sessione.
- Test rossi dopo il pull: non è detto che sia colpa propria; controllare il «Diario», correggere o avvisare.
- Produzione rotta dopo un push: `git revert` del commit (mai riscrivere la storia di `main`).
