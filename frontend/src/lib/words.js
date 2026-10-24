import { createContext, useContext } from 'react'

// Le parole giuste per questa impresa: le società di capitali hanno il bilancio, le società di persone e le ditte individuali la dichiarazione dei redditi.
// Un commercialista che ha scelto «ditta individuale» non deve mai leggere «bilancio».
export const docWords = (ov) => (ov?.document?.kind === 'DICHIARAZIONE_REDDITI'
  ? { tax: true, doc: 'dichiarazione dei redditi', docs: 'dichiarazioni dei redditi', the: 'la dichiarazione dei redditi', last: 'ultima dichiarazione dei redditi', period: 'periodo d’imposta', inThe: 'nella dichiarazione dei redditi', cap: 'Dichiarazione dei redditi', fromThe: 'dalla dichiarazione dei redditi' }
  : { tax: false, doc: 'bilancio', docs: 'bilanci', the: 'il bilancio', last: 'ultimo bilancio', period: 'esercizio', inThe: 'nel bilancio', cap: 'Bilancio', fromThe: 'dal bilancio' })

// Chi è il «socio» di questa impresa: in una ditta individuale c'è solo il titolare.
export const personWords = (type) => (type === 'DITTA'
  ? { age: 'Quanti anni ha il titolare?', woman: 'Il titolare è una donna', unemployed: 'Il titolare è disoccupato o inoccupato', header: 'Titolare e regolarità', founded: 'Anno di apertura' }
  : { age: 'Quanti anni ha il socio più giovane?', woman: 'L’impresa è a prevalenza femminile', unemployed: 'Un socio o promotore è disoccupato o inoccupato', header: 'Soci e regolarità', founded: 'Anno di costituzione' })

// Le pagine che dipendono dal tipo di impresa mettono qui le loro parole: chi sta sotto le legge con useWords() senza passarle di mano in mano.
export const WordsContext = createContext(docWords(null))
export const useWords = () => useContext(WordsContext)
