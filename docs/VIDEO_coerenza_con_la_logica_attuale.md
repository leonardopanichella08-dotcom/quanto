# Video di QUANTO: coerenza con la logica attuale (19 ottobre 2026)

Dopo la correzione del 16-17 ottobre, la logica dell'allocazione è cambiata in un punto che i video non sapevano:

- **Prima**: «tutti i bandi insieme» sulle spese annuali, compresi i bandi che finanziano progetti (Horizon Europe, Nuova Sabatini, Investimenti Sostenibili…). Risultato gonfiato (nell'azienda di prova: 1,3–1,9 milioni).
- **Ora**: due scenari separati. **Spese dell'anno** = solo i bandi che non chiedono un progetto (nell'azienda di prova: 148.349 € – 177.415 € su 2.100.186 €, 7,1%). **Un progetto** = le spese nuove di un progetto con i bandi che lo finanziano.
- I **60 criteri controllano il budget** (non il bando): il bando fornisce le regole; 36 criteri funzionano sempre, 24 hanno bisogno di una regola del bando.

## Esito per video

| Video | File | Esito | Dove è stato messo nell'app |
|---|---|---|---|
| Lancio v6 (musica) | `public/video/quanto-lancio.mp4` | **Pubblicato accorciato**: 30 s invece di 41,5 s | Pagina iniziale, sezione «Guarda QUANTO al lavoro» |
| T01 · Lo studio e i lavori | `tutorial-t01.mp4` | Coerente, con un'incongruenza da correggere (vedi sotto) | Profilo (sezione Lavori) e Guida → Video |
| T13 · Budget dei bandi e WP | `tutorial-t13.mp4` | **Coerente** (usa già «Esci dal gruppo» e «Spese dell'anno») | Allocazione (passo «Budget dei bandi»), Budget (quando c'è un gruppo di budget), Guida → Video |
| T16 · L'assistente guidato | `tutorial-t16.mp4` | Coerente, con un numero da correggere (vedi sotto) | Assistente («Guarda come funziona») e Guida → Video |
| T00, T02–T12, T14, T15 | — | **Non ancora realizzati come video**: nello zip ci sono solo i sorgenti, senza la pipeline di render (cartella `common`, `v6/kit2`, foto, audio) | Si aggiungono con una riga in `frontend/src/data/tutorials.js` |

I video sono compressi per il web (da 80 MB a circa 23 MB in tutto).

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

**Versione pubblicata (30,5 s)**: scene 0–26 s + chiusura 37–41,5 s, cioè hook → studi → bilancio → previsione → bandi adatti → «Dal bilancio ai bandi giusti». Dice solo cose vere. Il taglio tra 26 s e 37 s è netto (nessuna dissolvenza: il montaggio è su battuta, ma va guardato una volta).

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

## T08 · Allocazione (non ancora renderizzato: va riscritto prima)
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
