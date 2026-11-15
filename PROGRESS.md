# Avanzamento di QUANTO

Aggiornato: 15 novembre 2026 · ultimo commit di riferimento `69f1770` · 676 test verdi · produzione https://quanto-self.vercel.app

## Fatto
- **Motore**: 60 criteri deterministici sul budget, registro firmato (Ed25519 + Merkle), allocazione MILP con tetti, cumulo, de minimis.
- **Documenti dell'impresa** (Fonte C): bilanci, dichiarazioni, visure, buste paga, F24, registro del personale, budget e piano investimenti; profilo con fonte di ogni dato.
- **Catalogo** su tutto il catalogo aperto: lettura breve di ogni scheda, schede non lette lette subito a lotti (`POST /bandi/catalog/read-more`), affini contati e ordinati.
- **Giudizio dei bandi**: territorio con prova positiva (enti locali), settore, soggetti, età dell'impresa e compagine (`relevance.founding_checks`).
- **Bando o agevolazione**: `funding_modes` con budget sì/no, riconciliato con la forma della scheda ufficiale e il nome.
- **Quattro agenti** (Agevolazioni → Allocazione → Budget → Confronto) con barra «Ho fatto · Ho trovato · Mi serve da te».
- **Allocazione**: «Fuori da questa somma, e perché»; bandi «non serve» con perché e quando servirebbero; stessa base di spese tra «da solo» e piano.
- **Bozza di budget**: chiede solo i documenti necessari al bando e li fa caricare sul posto.
- **Homepage** editoriale su fondo quasi nero, animazioni GSAP che mostrano il lavoro (regola → calcolo, pratica che si compone, staffetta degli agenti).
- Documenti: manuale dei processi (sezioni fino alla 20), dossier (48 pagine), riassunto (7 pagine), `docs/agenti/I_tre_agenti.md`.

## A metà
- Pagina **«La visione»** (`Vision.jsx`) ancora nello stile vecchio: da portare allo stile della nuova homepage.
- Recensioni in homepage tolte: da rimettere solo con recensioni vere e concordate.
- Elenco ISTAT dei comuni per collocare ogni Comune dal nome: proposto, serve l'OK del titolare al download del file.
- Verifica visiva della homepage in un browser visibile (fluidità delle animazioni).

## Prossimi task
- Sentinella sul testo delle circolari INPS (agevolazioni sul lavoro).
- Coda di studio condivisa tra studi (serve l'OK del titolare sui conteggi anonimi).
- Peso di qualità dei template nel Confronto; novità notturne; tabella unica dei budget storici.
- Verificare il Fondo Salvaguardia imprese (probabilmente partecipazioni nel capitale, non fondo perduto).
- Pagamento online delle ricariche di token (oggi le elabora il titolare); `QUANTO_TOKENS_CHARGE` resta spento finché non deciso.
- README: aggiornare numeri e parti superate (conteggio test, codice HQ non più usato).
