// I video di QUANTO. I file stanno in public/video (tutorial-tNN.mp4 + locandina tutorial-tNN.jpg): per aggiungerne uno basta copiare i file e scrivere qui una riga.
// `page` dice dove compare il video nell'app; `hidden: true` lo nasconde da tutte le pagine senza cancellarlo. I numeri nei video sono esempi con l'azienda di prova fittizia.
const v = (n, title, page, seconds, about, extra = {}) => ({ title, page, seconds, about, src: `/video/tutorial-t${n}.mp4`, poster: `/video/tutorial-t${n}.jpg`, ...extra })

export const TUTORIALS = {
  T00: v('00', 'Il percorso di QUANTO in 9 passi', 'Guida', 60, 'Dal catalogo dei bandi al registro firmato, in un minuto.'),
  T01: v('01', 'Lo studio e i lavori', 'Profilo', 45, 'Un account per lo studio, un lavoro per ogni azienda cliente, dati che non si mescolano.'),
  T02: v('02', 'Il profilo: i documenti diventano dati', 'Profilo', 60, 'QUANTO legge i documenti, dice quanto è sicuro ogni dato e li confronta tra loro.'),
  T03: v('03', 'Il catalogo dei bandi e l’affinità', 'Bandi', 50, 'Come si ordinano i bandi per un’azienda, e perché.'),
  T04: v('04', 'Studiare un bando', 'Bandi', 60, 'Dalla scheda del catalogo alle fonti ufficiali, fino alla percentuale.'),
  T05: v('05', 'Quanto vale un bando in euro', 'Allocazione · Bandi', 50, 'Da dove viene la percentuale e perché il valore è un intervallo.'),
  T06: v('06', 'La stima dell’anno dopo', 'Allocazione', 50, 'Come nasce la previsione e da dove viene ogni percentuale.'),
  T07: v('07', 'I bandi adatti', 'Allocazione', 45, 'I controlli di idoneità e i tre esiti: adatto, da verificare, non adatto.'),
  T08: v('08', 'Allocazione: chi paga cosa', 'Allocazione', 70, 'Come QUANTO assegna le spese ai bandi senza pagare due volte la stessa spesa.'),
  T09: v('09', 'Spese dell’anno o un progetto', 'Allocazione', 60, 'I due scenari, le idee di progetto nate dai documenti e i preventivi.'),
  T10: v('10', 'Valore reale e incassi', 'Allocazione', 55, 'Un contributo non è un incasso: probabilità, costi e tempi di cassa.'),
  T11: v('11', 'De minimis e impresa unica', 'Profilo · Allocazione', 55, 'Il tetto agli aiuti piccoli e come si verifica sul registro nazionale.'),
  T12: v('12', 'Il budget e i 60 criteri', 'Budget', 70, 'La bozza nata dall’azienda e il controllo voce per voce.'),
  T13: v('13', 'Budget dei bandi e pacchetti di lavoro', 'Allocazione · Budget', 55, 'Un budget per ogni bando del piano, verificati insieme, e la ripartizione nei pacchetti di lavoro.'),
  T14: v('14', 'Il registro firmato e la Verifica', 'Verifica', 50, 'Come si firma un budget e come chiunque può controllarlo.'),
  T15: v('15', 'Il Confronto: i template', 'Confronto', 70, 'Il consiglio che impara dai budget salvati dallo studio.'),
  T16: v('16', 'L’assistente guidato', 'Assistente', 45, 'L’assistente esegue i passaggi al posto tuo e ti chiede solo i dati che mancano.'),
}

export const LAUNCH = { title: 'QUANTO in 40 secondi', seconds: 42, src: '/video/quanto-lancio.mp4', poster: '/video/quanto-lancio.jpg' }
