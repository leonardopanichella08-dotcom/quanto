// I video di QUANTO. I file stanno in public/video: per aggiungerne uno basta copiare il .mp4 (e una locandina .jpg) e scrivere qui una riga.
// `page` dice dove compare il video nell'app; i numeri nei video sono esempi con l'azienda di prova fittizia.
export const TUTORIALS = {
  T01: { title: 'Lo studio e i lavori', page: 'Profilo', seconds: 45, src: '/video/tutorial-t01.mp4', poster: '/video/tutorial-t01.jpg', about: 'Un account per lo studio, un lavoro per ogni azienda cliente, dati che non si mescolano.' },
  T13: { title: 'Budget dei bandi e pacchetti di lavoro', page: 'Allocazione · Budget', seconds: 55, src: '/video/tutorial-t13.mp4', poster: '/video/tutorial-t13.jpg', about: 'Un budget per ogni bando del piano, verificati insieme, e la ripartizione nei pacchetti di lavoro.' },
  T16: { title: 'L’assistente guidato', page: 'Assistente', seconds: 45, src: '/video/tutorial-t16.mp4', poster: '/video/tutorial-t16.jpg', about: 'L’assistente esegue i passaggi al posto tuo e ti chiede solo i dati che mancano.' },
}

export const LAUNCH = { title: 'QUANTO in 40 secondi', seconds: 42, src: '/video/quanto-lancio.mp4', poster: '/video/quanto-lancio.jpg' }
