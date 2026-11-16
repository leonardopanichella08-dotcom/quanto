import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Loader2, Play } from 'lucide-react'
import { api } from '../../lib/api'
import { fmtTs } from '../../lib/format'
import { Dossiers } from './HQSections'
import { BarList, ChartTitle, Donut, Pills } from './charts'

/* Attività: tutto ciò che il sistema ha fatto. In alto il grafico delle operazioni (cliccando se ne sceglie una e si vedono i suoi passaggi),
   sotto la cronologia filtrabile e, a parte, il fascicolo di ogni progetto. Sostituisce «Timeline», «Mappa operazioni» e «Fascicoli». */
const STATUS_LABEL = { OK: 'OK', WARN: 'Attenzione', FAIL: 'Non superato', DENIED: 'Negato', LOCKED: 'Bloccato', CONFLICT: 'Conflitto', NOT_FOUND: 'Non trovato' }
const STATUS_TONE = { OK: 'text-emerald-700', WARN: 'text-amber-700', FAIL: 'text-red-700', DENIED: 'text-red-700', LOCKED: 'text-red-700', CONFLICT: 'text-amber-700', NOT_FOUND: 'text-amber-700' }

function Timeline({ ops, opsById, initialOp, onReplay }) {
  const [filters, setFilters] = useState({ op: initialOp || '', project: '', bando: '', status: '' })
  const [events, setEvents] = useState([])
  const [open, setOpen] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setBusy(true); setError(null)
    try { setEvents(await api.hqTimeline({ ...filters, limit: 200 })) } catch (e) { setError(e.message) } finally { setBusy(false) }
  }, [filters])
  useEffect(() => { load() }, [load])

  const replay = async (runId) => {
    try { onReplay((await api.hqRun(runId)).response) } catch (e) { setError(e.message) }
  }
  const input = 'bg-field border border-line rounded-lg px-2 py-1.5 text-xs'
  return (
    <div className="space-y-4">
      <div className="card p-3 flex flex-wrap items-center gap-2">
        <select value={filters.op} onChange={(e) => setFilters({ ...filters, op: e.target.value })} className={`${input} w-full sm:w-auto max-w-full`}>
          <option value="">Tutte le operazioni</option>{ops.map((o) => <option key={o.id} value={o.id}>{o.area} · {o.title}</option>)}
        </select>
        <input placeholder="nome progetto" value={filters.project} onChange={(e) => setFilters({ ...filters, project: e.target.value })} className={`${input} w-[46%] sm:w-40 font-mono`} />
        <input placeholder="codice bando" value={filters.bando} onChange={(e) => setFilters({ ...filters, bando: e.target.value })} className={`${input} w-[46%] sm:w-40 font-mono`} />
        <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })} className={input}>
          <option value="">Ogni esito</option>{Object.entries(STATUS_LABEL).map(([s, l]) => <option key={s} value={s}>{l}</option>)}
        </select>
        <button onClick={load} className="btn-primary flex items-center gap-1.5">{busy && <Loader2 className="w-3 h-3 animate-spin" />}Aggiorna</button>
        <span className="text-xs text-mute ml-auto">{events.length} eventi</span>
      </div>
      {error && <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-700 text-xs">{error}</div>}
      <div className="relative pl-5 space-y-2 before:absolute before:left-[7px] before:top-1 before:bottom-1 before:w-px before:bg-tint-2">
        {events.map((e) => {
          const op = opsById[e.op]
          return (
            <div key={e.id} className="relative">
              <span className={`absolute -left-[18px] top-3 w-2.5 h-2.5 rounded-full border-2 border-[#0e0e0e] ${e.status === 'OK' ? 'bg-emerald-400' : 'bg-amber-400'}`} />
              <button onClick={() => setOpen(open === e.id ? null : e.id)} className="w-full text-left card p-3 hover:border-line-strong transition">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5">
                  <span className="text-[11px] font-mono text-mute">{fmtTs(e.ts)}</span>
                  <span className="text-xs font-bold text-brand-ink">{op?.title || e.op}</span>
                  <span className="text-[11px] text-mute">{op?.area}</span>
                  <span className={`text-[11px] font-medium ${STATUS_TONE[e.status] || 'text-ink-2'}`}>{STATUS_LABEL[e.status] || e.status}</span>
                  {e.duration_ms != null && <span className="text-[11px] font-mono text-mute">{e.duration_ms} ms</span>}
                  <span className="text-[11px] font-mono text-mute ml-auto">{e.actor}</span>
                </div>
                <p className="text-xs text-ink-2 mt-1">{e.summary}</p>
                {(e.project_id || e.bando_id) && <p className="text-[11px] font-mono text-mute mt-0.5">{e.project_id && `progetto ${e.project_id}`}{e.project_id && e.bando_id && ' · '}{e.bando_id && `bando ${e.bando_id}`}</p>}
              </button>
              {open === e.id && (
                <div className="card p-3 mt-1 space-y-2 !bg-field">
                  {op?.stages?.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-ink-2">{op.stages.map((s, i) => <span key={s} className="flex items-center gap-1.5"><span className="px-1.5 py-0.5 rounded bg-tint border border-line">{i + 1}. {s}</span></span>)}</div>
                  )}
                  {e.details && <pre className="text-[11px] font-mono text-ink-2 overflow-x-auto max-h-64">{JSON.stringify(e.details, null, 2)}</pre>}
                  {e.run_id && e.op === 'budget.validate' && <button onClick={() => replay(e.run_id)} className="btn-primary flex items-center gap-1.5"><Play className="w-3 h-3" />Rivedi nell’algoritmo</button>}
                </div>
              )}
            </div>
          )
        })}
        {events.length === 0 && !busy && <p className="text-xs text-mute italic">Nessun evento con questi filtri.</p>}
      </div>
    </div>
  )
}


function OpDetail({ op, onClear }) {
  return (
    <div className="rounded-2xl bg-black/[0.04] p-4 space-y-2.5">
      <div className="flex items-start justify-between gap-3">
        <div><p className="font-semibold text-sm">{op.title}</p><p className="text-[11px] font-mono text-mute">{op.area} · {op.endpoint}</p></div>
        <button className="btn !py-1" onClick={onClear}>Mostra tutte</button>
      </div>
      <p className="text-xs text-ink-2 leading-relaxed">{op.description}</p>
      <ol className="flex flex-wrap gap-x-4 gap-y-1">{op.stages.map((s, i) => <li key={s} className="flex items-center gap-1.5 text-xs text-ink-2"><span className="w-4 h-4 rounded-full bg-black/[0.08] text-[10px] font-bold flex items-center justify-center shrink-0">{i + 1}</span>{s}</li>)}</ol>
      <p className="text-[11px] font-mono text-mute flex flex-wrap gap-x-4">
        <span>{op.stats.count} esecuzioni</span>
        {op.stats.avg_ms != null && <span>media {op.stats.avg_ms} ms</span>}
        {op.stats.errors > 0 && <span className="text-amber-700">{op.stats.errors} non riuscite</span>}
        {op.criteria.length > 0 && <span>{op.criteria.length === 60 ? 'tutti i 60 controlli' : `controlli ${op.criteria.map((c) => `#${c}`).join(' ')}`}</span>}
        {op.stats.last_ts && <span>ultima {fmtTs(op.stats.last_ts)}</span>}
      </p>
    </div>
  )
}

export default function Activity({ ops, opsById, onReplay, initialOp = '' }) {
  const [view, setView] = useState('log')
  const [op, setOp] = useState(initialOp)
  const used = useMemo(() => ops.filter((o) => o.stats.count > 0).sort((a, b) => b.stats.count - a.stats.count), [ops])
  const unused = useMemo(() => ops.filter((o) => o.stats.count === 0), [ops])
  const total = used.reduce((a, o) => a + o.stats.count, 0)
  const errors = used.reduce((a, o) => a + o.stats.errors, 0)
  const pick = (id) => { setOp(op === id ? '' : id); setView('log') }
  return (
    <div className="space-y-7">
      <div className="grid lg:grid-cols-[1fr_auto] gap-8 items-start">
        <div>
          <ChartTitle right={<span className="text-xs text-mute">clicca una operazione per filtrare</span>}>Cosa è stato fatto</ChartTitle>
          <BarList rows={used.slice(0, 8).map((o) => ({ id: o.id, label: o.title, value: o.stats.count, alert: o.stats.errors > 0 }))} selected={op || undefined} onSelect={pick} empty="Ancora nessuna operazione eseguita." />
          {unused.length > 0 && <details className="mt-3 text-[11px] text-mute"><summary className="cursor-pointer hover:text-ink">Altre {unused.length} operazioni mai eseguite</summary><p className="mt-1.5 leading-relaxed">{unused.map((o) => o.title).join(' · ')}</p></details>}
        </div>
        <div><ChartTitle>Esiti</ChartTitle><Donut size={84} center={total} parts={[{ label: 'Riuscite', value: total - errors }, { label: 'Non riuscite', value: errors }]} /></div>
      </div>
      {op && opsById[op] && <OpDetail op={opsById[op]} onClear={() => setOp('')} />}
      <div className="flex items-center justify-between gap-3">
        <Pills items={[['log', 'Cronologia'], ['projects', 'Per progetto']]} value={view} onChange={setView} />
      </div>
      {view === 'log' && <Timeline key={op} ops={ops} opsById={opsById} initialOp={op} onReplay={onReplay} />}
      {view === 'projects' && <Dossiers onReplay={onReplay} opsById={opsById} />}
    </div>
  )
}
