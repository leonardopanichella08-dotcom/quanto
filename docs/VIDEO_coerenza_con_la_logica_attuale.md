# Video di QUANTO: coerenza con la logica attuale (19 ottobre 2026)

Dopo la correzione del 16-17 ottobre, la logica dell'allocazione è cambiata in un punto che i video non sapevano:

- **Prima**: «tutti i bandi insieme» sulle spese annuali, compresi i bandi che finanziano progetti (Horizon Europe, Nuova Sabatini, Investimenti Sostenibili…). Risultato gonfiato (nell'azienda di prova: 1,3–1,9 milioni).
- **Ora**: due scenari separati. **Spese dell'anno** = solo i bandi che non chiedono un progetto (nell'azienda di prova: 148.349 € – 177.415 € su 2.100.186 €, 7,1%). **Un progetto** = le spese nuove di un progetto con i bandi che lo finanziano.
- I **60 criteri controllano il budget** (non il bando): il bando fornisce le regole; 36 criteri funzionano sempre, 24 hanno bisogno di una regola del bando.

## Esito per video

| Video | Esito | Dove è nell'app |
|---|---|---|
| Lancio v6 (41,5 s) | Integrale per scelta del titolare; due scene da rifare (vedi sotto) | Homepage, «Guarda QUANTO al lavoro» |
| T00 Percorso in 9 passi | Coerente | Guida → Percorso rapido e Video |
| T01 Studio e lavori | Coerente, con un'incongruenza (vedi sotto) | Profilo |
| T02 Profilo e documenti | Coerente | Profilo, sezione Documenti |
| T03 Catalogo e affinità | Coerente | Bandi |
| T04 Studiare un bando | Coerente | Bandi, accanto alla ricerca sul web |
| T05 Valore in euro | Coerente | Allocazione, passo «Bandi» |
| T06 Stima dell'anno | Coerente | Allocazione, passo «Stima» |
| T07 Bandi adatti | Coerente | Allocazione, passo «Bandi» |
| **T08 Allocazione** | **Racconta la logica vecchia** («Tutti i bandi insieme», «Potenziale massimo 1.307.746 – 1.863.062 €», 8 fondi): in contrasto con T09 e con l'app | Allocazione, passo «Risultato» |
| T09 Spese dell'anno o progetto | **Coerente** (mostra i due scenari, 148.000 € su 2,1 milioni) | Allocazione, passo «Progetti» |
| T10 Valore reale e incassi | Coerente | Allocazione, passo «Valore reale e incassi» |
| T11 De minimis | Coerente | Profilo (aiuti ricevuti) |
| T12 Budget e 60 criteri | Coerente | Budget |
| T13 Budget dei bandi e WP | **Coerente** (usa «Esci dal gruppo») | Allocazione, passo «Budget dei bandi»; Budget |
| T14 Registro e Verifica | Coerente | Verifica |
| T15 Confronto e template | Coerente | Confronto |
| T16 Assistente | Coerente, con un numero da correggere (vedi sotto) | Assistente |

Tutti i 17 tutorial sono nell'app e raccolti in Guida → Video. Per nascondere un video senza cancellarlo: `hidden: true` nella sua riga di `frontend/src/data/tutorials.js` (oggi consigliato per T08 finché non è rifatto, se non vuoi far vedere due messaggi diversi sull'allocazione).

I video sono compressi per il web (tutorial a 1280×720, circa 56 MB in tutto con il lancio).

## Lancio v6: cosa dice e cosa non è più vero

Scene (tempi del file originale):

| Tempo | Scena | Giudizio |
|---|---|---|
| 0–4 s | «Ogni cliente ha un bilancio.» | Corretta |
| 4–10 s | «Per studi di commercialisti. Un account, tutti i tuoi clienti.» | Corretta (l'URL mostrato `quanto.app/clienti` oggi è `/profilo`) |
| 10–14 s | «Carichi il bilancio. QUANTO lo legge voce per voce.» | Corretta (oggi legge anche fatture XML, XBRL, visura RNA, preventivi…) |
| 14–20 s | «Prevede l'anno successivo.» | Corretta (URL `/previsione` oggi è nel passo «Stima» di `/allocazione`) |
| 20–26 s | «Dalla previsione ai bandi adatti.» | Corretta: è l'abbinamento bandi–azienda, che non è cambiato |
| **26–30,5 s** | **«Calcola il massimo. Tutti i bandi insieme, senza contare due volte la stessa spesa. € 524.894 su € 2.151.206, quota coperta 24,4%.»** | **Non più vera**: applica alle spese annuali anche i bandi a progetto (Horizon Europe, Nuova Sabatini) con barre per categoria. Messaggio sbagliato |
| **30,5–34 s** | **«60 controlli per ogni bando.»** | **Ambigua**: i 60 controlli sono sul **budget**, non sul bando. Da dire «60 controlli su ogni voce del budget» |
| 34–37 s | Riepilogo Bilancio → Previsione → Bandi adatti → Budget | Corretto nella forma, ma l'ultima finestra mostra ancora un «massimo» (€ 523.378) |
| 37–41,5 s | «Dal bilancio ai bandi giusti. Per studi di commercialisti e consulenti d'impresa. Inizia gratis» | Corretta; verificare se «consulenti d'impresa» vale ancora come target (la linea di prodotto è studi di commercialisti e boutique di finanza agevolata) |

**Versione pubblicata**: integrale, come da scelta del titolare (19 ottobre). Le scene «Calcola il massimo» (26–30,5 s) e «60 controlli per ogni bando» (30,5–34 s) dicono cose non più allineate: se il video si usa anche fuori dall'app (LinkedIn, presentazioni), meglio rifarle prima. Una versione accorciata a 30,5 s (0–26 s + chiusura 37–41,5 s) è facile da ricavare con ffmpeg.

**Da rifare nel sorgente (`Lancio6`, non presente nello zip)**:
1. Scena «Calcola il massimo» → «Assegna le spese ai bandi», con l'interruttore **Spese dell'anno / Un progetto**: a sinistra 2 bandi senza progetto che coprono 148.349 € di 2,1 milioni; a destra un progetto («Rinnovo dei beni a fine vita») con i bandi che lo finanziano. Testo: «Le spese dell'anno e i progetti hanno bandi diversi.»
2. «60 controlli per ogni bando» → «60 controlli su ogni voce del budget», con sotto: «Se il bando non dà una regola, il controllo resta “non valutato”.»
3. Ultima finestra del riepilogo: togliere il numero grande e scrivere «Budget» con la griglia.
4. URL nelle finestre: `quanto.app/clienti` → `quanto.app/profilo`; `quanto.app/previsione` → `quanto.app/allocazione`.

## T01 · Lo studio e i lavori (da correggere nel sorgente `T01.tsx`)
- Scena 14–22 s («tutto si allinea»): la scheda Allocazione mostra «potenziale massimo 1.307.746 €» (`T01.tsx` riga 11 e 49). Con la logica attuale: «Spese dell'anno 148.349 €».
- Scena 34–42 s («Si salva tutto da solo»): la finestra mostra «Scenario: Spese dell'anno · Bandi scelti 8 · Potenziale massimo 1.863.062 €» (`T01.tsx` riga 128). Con la logica attuale: «Bandi scelti 2 · Coperti 148.349 €» (le spese dell'anno non includono i bandi a progetto).

## T16 · L'assistente guidato (da correggere nel sorgente `T16.tsx`)
- Scena finale del compito: «Potenziale massimo 1.863.062 €» (`T16.tsx` righe 41–42, nel file renderizzato appare 1.630.179 €). Con la logica attuale il risultato dell'assistente è sul piano delle spese dell'anno: 148.349 € – 177.415 €.
- La richiesta «Calcola il potenziale massimo» (riga 46) coincide con il suggerimento attuale dell'assistente nell'app. Se si cambia il testo nel video, cambiarlo anche in `frontend/src/assistant/AssistantContext.jsx` (`SUGGEST.allocazione`): oggi nell'app si chiama ancora «Calcola il potenziale massimo».

## T08 · Allocazione (renderizzato con il sorgente vecchio: da rifare)
Il sorgente `T08.tsx` racconta la logica vecchia: «Tutti i bandi insieme», «8 fondi collegati», «Potenziale massimo · tutti i bandi insieme», prudente 1.307.746 €, massimo 1.863.062 €, somma uno per uno 2.394.221 € (righe 9, 18, 70, 188–190, 203). Va riscritto con i due scenari come già fa lo script T09: spese dell'anno con i bandi senza progetto (cifre: 148.349 € – 177.415 € su 2.100.186 €, 7,1%) e il passaggio a un progetto. Titolo suggerito: «Chi paga cosa, senza doppi conteggi».

## Altri video del programma
Dallo script (`SCRIPT_TUTORIAL_QUANTO.md`) T00, T02–T07, T09–T12, T14, T15 sono coerenti con la logica attuale. Due precisazioni:
- T07 («Sei controlli per ogni bando») riguarda i **controlli di idoneità** del bando (apertura, spese, settore, territorio…), non i 60 criteri del budget: tenere separati i due nomi.
- T12 va benissimo («60 criteri, voce per voce»); aggiungere se possibile la riga «36 sempre attivi, 24 dipendono da una regola del bando».

## Come aggiungere un video
1. Copiare `nome.mp4` e `nome.jpg` (locandina) in `frontend/public/video/`.
2. Aggiungere una riga in `frontend/src/data/tutorials.js` (titolo, pagina, durata, percorsi).
3. Inserire `<TutorialVideo id="Txx" />` nella pagina giusta (e comparirà in automatico in Guida → Video).

Compressione consigliata (ffmpeg): `-c:v libx264 -crf 25 -preset slow -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart`.
