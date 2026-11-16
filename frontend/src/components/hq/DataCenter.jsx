import React from 'react'
import Archive from './Archive'
import CatalogHQ from './CatalogHQ'
import FonteB from './FonteB'
import { PatternAdmin } from './DataAdmin'
import { DbExplorer, Documents } from './HQSections'
import { Pills } from './charts'

/* Dati: tutto ciò che QUANTO sa e conserva, una vista alla volta. Nulla è stato tolto: le sei viste sono le vecchie sezioni
   Bandi, Catalogo, Tabelle ufficiali, Banca pattern, Documenti e Database, ora raccolte qui. */
export const DATA_VIEWS = [['bandi', 'Bandi'], ['catalog', 'Catalogo'], ['tables', 'Tabelle ufficiali'], ['history', 'Storico budget'], ['documents', 'Documenti'], ['database', 'Database']]
const HINT = {
  bandi: 'I bandi in memoria con documenti, regole e requisiti: qui si correggono e si rileggono.',
  catalog: 'Il catalogo nazionale delle agevolazioni, quante schede sono descritte e quali segnali arrivano dagli utenti.',
  tables: 'Contratti collettivi, ammortamenti e parametri di legge che usano i calcoli, con versione e fonte.',
  history: 'I budget storici importati: servono a capire cosa si finanzia di solito.',
  documents: 'I file lavorati (bandi caricati, import, export) con nome, dimensione e impronta.',
  database: 'Le tabelle della memoria, in sola lettura (con esportazione). Per controllare cosa è salvato.',
}

export default function DataCenter({ view, setView }) {
  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <Pills items={DATA_VIEWS} value={view} onChange={setView} />
        <p className="text-xs text-ink-2">{HINT[view]}</p>
      </div>
      {view === 'bandi' && <Archive />}
      {view === 'catalog' && <CatalogHQ />}
      {view === 'tables' && <FonteB />}
      {view === 'history' && <PatternAdmin />}
      {view === 'documents' && <Documents />}
      {view === 'database' && <DbExplorer />}
    </div>
  )
}
