// Recensioni mostrate nella homepage. QUANTO non è ancora in uso presso studi veri: finché non ci sono recensioni reali, i testi qui sotto sono SEGNAPOSTO
// (real: false) e la pagina lo dichiara con un'etichetta visibile. Per pubblicarne una vera: sostituire testo, autore e ruolo con quelli concordati
// con la persona e mettere real: true, l'etichetta sparisce da sola.
export const REVIEWS = [
  { id: 'r1', stars: 5, real: false, text: 'La fonte di ogni regola è pronta da mostrare al cliente: non devo più andare a cercare in quale pagina del bando c’è il tetto.', author: 'Nome Cognome', role: 'Studio di commercialisti' },
  { id: 'r2', stars: 5, real: false, text: 'Carico i bilanci e vedo subito quali spese verrebbero ridotte o respinte, prima di consegnare il budget.', author: 'Nome Cognome', role: 'Boutique di finanza agevolata' },
  { id: 'r3', stars: 5, real: false, text: 'Stesso dato, stesso risultato: posso rifare il calcolo davanti al cliente e ottengo sempre lo stesso numero.', author: 'Nome Cognome', role: 'Studio associato' },
]
