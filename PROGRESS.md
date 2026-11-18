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
- **Homepage** (18/11): mascotte dei 4 agenti senza sfondo (Fiuto, Riparto, Spunta, Duo) con video, sezione «Il gestionale, com'è davvero» con schermate reali della scheda di un bando, prezzi più piccoli, layout da telefono rivisto (agenti scorrevoli di lato). Logo «Q» tolto ovunque, favicon con la scritta.
- **Quartier Generale ricostruito** (17/11): Oggi · Accessi · Marketing · Dati · Sistema; chatbot sui dati (Claude o parole chiave), datacenter con grafici e CSV, Marketing LinkedIn (account, post con approvazione e pubblicazione, campagne con CSV, follower), visite al sito anonime; migrazione 25, 15 test nuovi. **Da fare**: chiavi LinkedIn e ANTHROPIC_API_KEY su Vercel; scheduler per i post programmati; spegnere QUANTO Growth quando il titolare lo decide.
- **Accessi e Quartier Generale** (16/11): registrazione = richiesta in attesa, approvazione con livello e e-mail pronta nel Quartier Generale (5 sezioni: Panoramica, Accessi, Attività, Dati, Manuale, con grafici); migrazione 24, 11 test nuovi in `tests/test_access_requests.py`; corretto il pulsante di registrazione del sito che chiamava il registro firmato. Suite completa non rilanciata.
- **Homepage** (16/11, versione minimale): 7 sezioni (apertura, metodo, processo, agenti e portale ricostruito, principi, prezzi, domande) e chiusura; una sola capsula di vetro liquido. Prima: (15/11, seconda versione dopo la revisione del titolare): colori del marchio senza blu, nessun riquadro, animazioni GSAP (contorni che si riempiono, pratica che si compone, staffetta degli agenti), barra in vetro liquido a scomparsa, video in loop senza controlli, prezzi e token in due colonne, 8 domande + «Chiedi a QUANTO» sulle 200; `public/faq.md`, `llms.txt`, dati strutturati FAQPage. Pagina «La visione» nello stesso stile. Prima versione: fondo bianco, apertura a tutta altezza con lo skyline all'alba, sezione video con i 4 agenti
  (video `quanto-quattro-agenti.mp4`) e il video di lancio, griglie a linee sottili, esempio «frase del bando → regola → calcolo», area Insights (articoli «in arrivo»),
  **newsletter** con consenso (tabella `newsletter_subscribers`, migrazione 23; il modulo ora non è in homepage) e **200 FAQ** dal dossier v4.5.
- Documenti: manuale dei processi (sezioni fino alla 20), dossier (48 pagine), riassunto (7 pagine), `docs/agenti/I_tre_agenti.md`.

## A metà
- Pagina **«La visione»** (`Vision.jsx`) ancora nello stile vecchio: da portare allo stile della nuova homepage.
- Recensioni in homepage tolte: da rimettere solo con recensioni vere e concordate.
- Elenco ISTAT dei comuni per collocare ogni Comune dal nome: proposto, serve l'OK del titolare al download del file.
- Verifica visiva della nuova homepage su telefono e della sezione FAQ dopo l'ultima correzione: non fatta per **disco C: pieno** (78 MB liberi il 15/11).
- Suite completa dei test dopo la migrazione 23: fatti solo `test_agents` e `test_postgres` (33 verdi); la completa non è partita per lo spazio su disco.
- Articoli del blog: da scrivere (oggi «in arrivo»). Invio della newsletter e cancellazione dell'iscrizione: da costruire.

## Prossimi task
- Sentinella sul testo delle circolari INPS (agevolazioni sul lavoro).
- Coda di studio condivisa tra studi (serve l'OK del titolare sui conteggi anonimi).
- Peso di qualità dei template nel Confronto; novità notturne; tabella unica dei budget storici.
- Verificare il Fondo Salvaguardia imprese (probabilmente partecipazioni nel capitale, non fondo perduto).
- Pagamento online delle ricariche di token (oggi le elabora il titolare); `QUANTO_TOKENS_CHARGE` resta spento finché non deciso.
- README: aggiornare numeri e parti superate (conteggio test, codice HQ non più usato).
