import React, { useEffect, useMemo, useState } from 'react'
import { Download, Loader2 } from 'lucide-react'
import { api, download } from '../../lib/api'
import Archive from './Archive'
import CatalogHQ from './CatalogHQ'
import FonteB from './FonteB'
import { PatternAdmin } from './DataAdmin'
import { DbExplorer, Documents } from './HQSections'
import Ask from './Ask'
import { Pills, ResultView } from './charts'

/* Dati: «Esplora» (ogni dato di QUANTO, scegli cosa vedere e come raggrupparlo, scarichi in CSV) e «Modifica i contenuti»
   (bandi, catalogo, tabelle ufficiali, storico dei budget, documenti, tabelle grezze). */
const EDIT = [['bandi', 'Bandi'], ['catalog', 'Catalogo'], ['tables', 'Tabelle ufficiali'], ['history', 'Storico budget'], ['documents', 'Documenti'], ['database', 'Tabelle grezze']]

function Explore() {
  const [cat, setCat] = useState(null)
  const [ds, setDs] = useState(null)
  const [q, setQ] = useState({ group_by: '', bucket: '', measure: 'count', measure_column: '', since: '' })
  const [res, setRes] = useState(null)
  const [busy, setBusy] = useState(false)
  const [e, setE] = useState(null)
  useEffect(() => { api.hqDatasets().then((c) => { setCat(c); setDs(c[0]?.id) }).catch((x) => setE(x.message)) }, [])
  const d = useMemo(() => cat?.find((x) => x.id === ds), [cat, ds])
  const groups = useMemo(() => (cat || []).reduce((m, x) => ({ ...m, [x.group]: [...(m[x.group] || []), x] }), {}), [cat])
  const request = useMemo(() => {
    if (!d) return null
    const filters = q.since && d.date_column ? [{ column: d.date_column, op: 'since_days', value: Number(q.since) }] : []
    if (!q.group_by) return { dataset: d.id, filters, limit: 200, ...(d.date_column ? { order_by: d.date_column, order: 'desc' } : {}) }
    const isDate = d.columns.find((c) => c.name === q.group_by)?.kind === 'date'
    return { dataset: d.id, filters, group_by: q.group_by, bucket: isDate ? (q.bucket || 'day') : null, measure: q.measure, measure_column: q.measure === 'count' ? null : q.measure_column || null, limit: 200 }
  }, [d, q])
  useEffect(() => {
    if (!request) return
    setBusy(true); setE(null)
    api.hqQuery(request).then(setRes).catch((x) => { setE(x.message); setRes(null) }).finally(() => setBusy(false))
  }, [request])
  if (!cat) return e ? <p className="text-xs text-red-700">{e}</p> : <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Caricamento…</p>
  const numbers = d?.columns.filter((c) => c.kind === 'number') || []
  const set = (k) => (ev) => setQ({ ...q, [k]: ev.target.value })
  return (
    <div className="grid lg:grid-cols-[240px_1fr] gap-6">
      <nav className="space-y-4">
        {Object.entries(groups).map(([g, items]) => (
          <div key={g}><p className="label mb-1">{g}</p>
            {items.map((x) => <button key={x.id} onClick={() => { setDs(x.id); setQ({ group_by: '', bucket: '', measure: 'count', measure_column: '', since: '' }) }}
              className={`w-full text-left flex justify-between gap-2 px-2.5 py-1.5 rounded-lg text-[13px] ${ds === x.id ? 'bg-brand text-white' : 'text-ink-2 hover:bg-black/[0.05]'}`}><span className="truncate">{x.label}</span><span className="font-mono text-[11px] opacity-70">{x.rows}</span></button>)}
          </div>
        ))}
      </nav>
      {d && (
        <div className="space-y-4 min-w-0">
          <div><h3 className="font-semibold">{d.label}</h3><p className="text-xs text-ink-2">{d.help} · {d.rows} righe</p></div>
          <div className="flex flex-wrap items-end gap-3 text-xs">
            <label className="space-y-1"><span className="label">Raggruppa per</span><select className="field !w-44" value={q.group_by} onChange={set('group_by')}><option value="">— mostra le righe —</option>{d.columns.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}</select></label>
            {q.group_by && d.columns.find((c) => c.name === q.group_by)?.kind === 'date' && <label className="space-y-1"><span className="label">Periodo</span><select className="field !w-32" value={q.bucket || 'day'} onChange={set('bucket')}><option value="day">giorno</option><option value="week">settimana</option><option value="month">mese</option></select></label>}
            {q.group_by && <label className="space-y-1"><span className="label">Misura</span><select className="field !w-40" value={q.measure} onChange={set('measure')}><option value="count">quante righe</option>{numbers.length > 0 && <><option value="sum">somma</option><option value="avg">media</option><option value="max">massimo</option></>}</select></label>}
            {q.group_by && q.measure !== 'count' && <label className="space-y-1"><span className="label">di</span><select className="field !w-40" value={q.measure_column} onChange={set('measure_column')}><option value="">scegli</option>{numbers.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}</select></label>}
            {d.date_column && <label className="space-y-1"><span className="label">Quando</span><select className="field !w-36" value={q.since} onChange={set('since')}><option value="">da sempre</option><option value="7">ultimi 7 giorni</option><option value="30">ultimi 30 giorni</option><option value="90">ultimi 90 giorni</option><option value="365">ultimo anno</option></select></label>}
            <button className="btn ml-auto" disabled={!request} onClick={async () => download(await api.hqQueryCsv(request), `quanto_${d.id}.csv`)}><Download className="w-3.5 h-3.5" />Scarica CSV</button>
          </div>
          {e && <p className="text-xs text-red-700">{e}</p>}
          {busy ? <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Cerco…</p> : <ResultView result={res} />}
        </div>
      )}
    </div>
  )
}

export default function Data({ view, setView }) {
  const [edit, setEdit] = useState('bandi')
  return (
    <div className="space-y-6">
      <Pills items={[['explore', 'Esplora i dati'], ['ask', 'Chiedi'], ['edit', 'Modifica i contenuti']]} value={view} onChange={setView} />
      {view === 'explore' && <Explore />}
      {view === 'ask' && <Ask />}
      {view === 'edit' && (
        <div className="space-y-5">
          <Pills items={EDIT} value={edit} onChange={setEdit} />
          {edit === 'bandi' && <Archive />}
          {edit === 'catalog' && <CatalogHQ />}
          {edit === 'tables' && <FonteB />}
          {edit === 'history' && <PatternAdmin />}
          {edit === 'documents' && <Documents />}
          {edit === 'database' && <DbExplorer />}
        </div>
      )}
    </div>
  )
}
