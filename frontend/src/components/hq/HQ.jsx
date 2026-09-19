import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Database, FileText, FolderOpen, Gauge, History, KeyRound, ListTree, Loader2, LogOut, Lock, Network, Play, Wrench } from 'lucide-react'
import { api, hqToken } from '../../lib/api'
import { fmtBytes, fmtTs } from '../../lib/format'
import PageIntro from '../PageIntro'
import IngestionPanel from '../IngestionPanel'
import { DbExplorer, Dossiers, Documents } from './HQSections'

const SECTIONS = [
  ['overview', 'Panoramica', Gauge], ['timeline', 'Timeline', History], ['operations', 'Mappa operazioni', Network],
  ['dossiers', 'Fascicoli', FolderOpen], ['documents', 'Documenti', FileText], ['database', 'Database', Database], ['ingestion', 'Ingestion', Wrench],
]
const STATUS_TONE = { OK: 'text-emerald-300', WARN: 'text-amber-300', FAIL: 'text-red-300', DENIED: 'text-red-300', LOCKED: 'text-red-300', CONFLICT: 'text-amber-300', NOT_FOUND: 'text-amber-300' }

function Gate({ onAuthed }) {
  const [code, setCode] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError(null)
    try {
      const res = await api.hqLogin(code)
      hqToken.set(res.token)
      onAuthed()
    } catch (err) { setError(err.message) } finally { setBusy(false); setCode('') }
  }
  return (
    <div className="max-w-md mx-auto card p-8 space-y-5 mt-6">
      <div className="flex items-center gap-3">
        <div className="p-3 rounded-xl bg-[#deffac]/10 border border-[#deffac]/20 text-[#deffac]"><Lock className="w-6 h-6" /></div>
        <div><h2 className="font-extrabold text-lg">Quartier Generale</h2><p className="text-xs text-neutral-400">Area riservata ai manager</p></div>
      </div>
      <form onSubmit={submit} className="space-y-3">
        <label className="block space-y-1"><span className="label">Codice di accesso</span>
          <input type="password" autoComplete="off" autoFocus value={code} onChange={(e) => setCode(e.target.value)} className="w-full bg-neutral-950 border border-neutral-700 rounded-xl px-3 py-2.5 font-mono text-sm focus:border-[#deffac] outline-none" placeholder="••••••••" /></label>
        <button disabled={busy || !code} className="btn-primary w-full py-2.5 flex items-center justify-center gap-2">{busy && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Entra</button>
        {error && <p className="text-xs text-red-300">{error}</p>}
      </form>
      <p className="text-[11px] text-neutral-500 leading-relaxed">Il codice è verificato dal server (mai nel browser). Dopo 5 tentativi errati l’accesso si blocca per 10 minuti. Ogni tentativo viene registrato nella timeline, senza il codice digitato.</p>
    </div>
  )
}

function Kpi({ label, value, note, tone = 'text-neutral-100' }) {
  return <div className="card p-4"><span className="label">{label}</span><div className={`text-2xl font-bold font-mono mt-1 ${tone}`}>{value}</div>{note && <p className="text-[11px] text-neutral-500 mt-1">{note}</p>}</div>
}

function Overview({ data, opsById, goto }) {
  const c = data.counts
  const maxDay = Math.max(...data.events_by_day.map((d) => d.n), 1)
  const docsTotal = Object.values(data.documents_by_kind).reduce((a, b) => a + b, 0)
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        <Kpi label="Validazioni" value={data.validations} note={data.last_validation_ts ? `ultima ${fmtTs(data.last_validation_ts)}` : 'nessuna ancora'} tone="text-[#deffac]" />
        <Kpi label="Progetti" value={data.projects} />
        <Kpi label="Bandi" value={c.bandi} note={`${c.rules} regole · ${c.requirements} requisiti`} />
        <Kpi label="Documenti" value={docsTotal} note={Object.entries(data.documents_by_kind).map(([k, v]) => `${v} ${k.replace('_', ' ').toLowerCase()}`).join(' · ') || '—'} />
        <Kpi label="Eventi" value={c.events} note="ogni operazione è registrata" />
        <Kpi label="Registrazioni" value={data.registry.entries} note={data.registry.intact ? 'catena integra' : 'CATENA NON INTEGRA'} tone={data.registry.intact ? 'text-emerald-300' : 'text-red-300'} />
      </div>

      <div className="grid lg:grid-cols-3 gap-4">
        <div className={`card p-4 space-y-2 ${data.storage.volatile ? '!border-amber-500/40' : ''}`}>
          <span className="label flex items-center gap-1.5"><Database className="w-3.5 h-3.5" />Memoria e database</span>
          <p className="text-sm font-mono">{data.storage.engine} · {fmtBytes(data.storage.size_bytes)}</p>
          <p className={`text-[11px] leading-relaxed ${data.storage.volatile ? 'text-amber-300' : 'text-neutral-400'}`}>{data.storage.volatile && <AlertTriangle className="w-3 h-3 inline mr-1" />}{data.storage.note}</p>
        </div>
        <div className={`card p-4 space-y-2 ${data.hq_code_is_default ? '!border-amber-500/40' : ''}`}>
          <span className="label flex items-center gap-1.5"><KeyRound className="w-3.5 h-3.5" />Sicurezza dell’accesso</span>
          <p className={`text-[11px] leading-relaxed ${data.hq_code_is_default ? 'text-amber-300' : 'text-emerald-300'}`}>{data.hq_code_is_default ? 'Il codice manager è ancora quello predefinito (QUANTO_1), presente nella documentazione del progetto. Cambialo impostando QUANTO_HQ_CODE sul server.' : 'Codice manager personalizzato.'}</p>
          <p className={`text-[11px] ${data.registry.is_dev_key ? 'text-amber-300' : 'text-neutral-400'}`}>Firma del registro: chiave {data.registry.key_id}{data.registry.is_dev_key ? ' (sviluppo)' : ''}</p>
        </div>
        <div className="card p-4 space-y-2">
          <span className="label">Attività degli ultimi giorni</span>
          <div className="flex items-end gap-1 h-16">
            {data.events_by_day.map((d) => <div key={d.day} title={`${d.day}: ${d.n}`} className="flex-1 max-w-[36px] bg-[#deffac]/60 rounded-t" style={{ height: `${Math.max(6, (d.n / maxDay) * 100)}%` }} />)}
            {data.events_by_day.length === 0 && <p className="text-[11px] text-neutral-500 italic">Nessun evento.</p>}
          </div>
        </div>
      </div>

      <div className="card p-4 space-y-2">
        <div className="flex items-center justify-between"><span className="label">Ultimi eventi</span><button onClick={() => goto('timeline')} className="text-[11px] text-[#deffac] hover:underline">Timeline completa →</button></div>
        {data.recent_events.map((e) => (
          <div key={e.id} className="flex flex-wrap items-center gap-x-3 text-xs border-b border-neutral-900 py-1.5 last:border-0">
            <span className="font-mono text-[10px] text-neutral-500 w-32 shrink-0">{fmtTs(e.ts)}</span>
            <span className="text-[#deffac] font-semibold shrink-0">{opsById[e.op]?.title || e.op}</span>
            <span className="text-neutral-400 truncate">{e.summary}</span>
          </div>
        ))}
        {data.recent_events.length === 0 && <p className="text-xs text-neutral-500 italic">Ancora nessuna operazione registrata.</p>}
      </div>
    </div>
  )
}

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
  const input = 'bg-neutral-950 border border-neutral-800 rounded-lg px-2 py-1.5 text-xs'
  return (
    <div className="space-y-4">
      <div className="card p-3 flex flex-wrap items-center gap-2">
        <select value={filters.op} onChange={(e) => setFilters({ ...filters, op: e.target.value })} className={`${input} w-full sm:w-auto max-w-full`}>
          <option value="">Tutte le operazioni</option>{ops.map((o) => <option key={o.id} value={o.id}>{o.area} · {o.title}</option>)}
        </select>
        <input placeholder="progetto" value={filters.project} onChange={(e) => setFilters({ ...filters, project: e.target.value })} className={`${input} w-[46%] sm:w-40 font-mono`} />
        <input placeholder="bando" value={filters.bando} onChange={(e) => setFilters({ ...filters, bando: e.target.value })} className={`${input} w-[46%] sm:w-40 font-mono`} />
        <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })} className={input}>
          <option value="">Ogni esito</option>{['OK', 'WARN', 'FAIL', 'CONFLICT', 'NOT_FOUND', 'DENIED', 'LOCKED'].map((s) => <option key={s}>{s}</option>)}
        </select>
        <button onClick={load} className="btn-primary flex items-center gap-1.5">{busy && <Loader2 className="w-3 h-3 animate-spin" />}Aggiorna</button>
        <span className="text-[11px] text-neutral-500 ml-auto">{events.length} eventi</span>
      </div>
      {error && <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-xs">{error}</div>}
      <div className="relative pl-5 space-y-2 before:absolute before:left-[7px] before:top-1 before:bottom-1 before:w-px before:bg-neutral-800">
        {events.map((e) => {
          const op = opsById[e.op]
          return (
            <div key={e.id} className="relative">
              <span className={`absolute -left-[18px] top-3 w-2.5 h-2.5 rounded-full border-2 border-[#0e0e0e] ${e.status === 'OK' ? 'bg-emerald-400' : 'bg-amber-400'}`} />
              <button onClick={() => setOpen(open === e.id ? null : e.id)} className="w-full text-left card p-3 hover:border-neutral-600 transition">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5">
                  <span className="text-[10px] font-mono text-neutral-500">{fmtTs(e.ts)}</span>
                  <span className="text-xs font-bold text-[#deffac]">{op?.title || e.op}</span>
                  <span className="text-[10px] text-neutral-500">{op?.area}</span>
                  <span className={`text-[10px] font-bold ${STATUS_TONE[e.status] || 'text-neutral-300'}`}>{e.status}</span>
                  {e.duration_ms != null && <span className="text-[10px] font-mono text-neutral-600">{e.duration_ms} ms</span>}
                  <span className="text-[10px] font-mono text-neutral-600 ml-auto">{e.actor}</span>
                </div>
                <p className="text-xs text-neutral-300 mt-1">{e.summary}</p>
                {(e.project_id || e.bando_id) && <p className="text-[10px] font-mono text-neutral-500 mt-0.5">{e.project_id && `progetto ${e.project_id}`}{e.project_id && e.bando_id && ' · '}{e.bando_id && `bando ${e.bando_id}`}</p>}
              </button>
              {open === e.id && (
                <div className="card p-3 mt-1 space-y-2 !bg-neutral-950">
                  {op?.stages?.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5 text-[10px] text-neutral-400">{op.stages.map((s, i) => <span key={s} className="flex items-center gap-1.5"><span className="px-1.5 py-0.5 rounded bg-neutral-900 border border-neutral-800">{i + 1}. {s}</span></span>)}</div>
                  )}
                  {e.details && <pre className="text-[10px] font-mono text-neutral-300 overflow-x-auto max-h-64">{JSON.stringify(e.details, null, 2)}</pre>}
                  {e.run_id && e.op === 'budget.validate' && <button onClick={() => replay(e.run_id)} className="btn-primary flex items-center gap-1.5"><Play className="w-3 h-3" />Rivedi nell’algoritmo</button>}
                </div>
              )}
            </div>
          )
        })}
        {events.length === 0 && !busy && <p className="text-xs text-neutral-500 italic">Nessun evento con questi filtri.</p>}
      </div>
    </div>
  )
}

function Operations({ ops, onShow }) {
  const areas = useMemo(() => { const m = {}; ops.forEach((o) => { (m[o.area] ||= []).push(o) }); return Object.entries(m) }, [ops])
  return (
    <div className="space-y-6">
      <p className="text-xs text-neutral-400">Tutte le operazioni fattibili nell’app, con le fasi che il motore attraversa nell’ordine reale e quante volte sono state eseguite.</p>
      {areas.map(([area, list]) => (
        <div key={area} className="space-y-3">
          <h3 className="label">{area}</h3>
          <div className="grid lg:grid-cols-2 gap-3">
            {list.map((o) => (
              <div key={o.id} className="card p-4 space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div><p className="font-bold text-sm">{o.title}</p><p className="text-[10px] font-mono text-neutral-500">{o.endpoint}</p></div>
                  <div className="text-right shrink-0"><p className="font-mono text-lg font-bold text-[#deffac]">{o.stats.count}</p><p className="text-[9px] text-neutral-500">esecuzioni</p></div>
                </div>
                <p className="text-[11px] text-neutral-400 leading-relaxed">{o.description}</p>
                <ol className="space-y-1">{o.stages.map((s, i) => (
                  <li key={s} className="flex items-center gap-2 text-[11px] text-neutral-300"><span className="w-4 h-4 rounded-full bg-neutral-800 text-[9px] font-bold flex items-center justify-center text-neutral-400 shrink-0">{i + 1}</span>{s}</li>))}</ol>
                <div className="flex flex-wrap items-center gap-3 text-[10px] font-mono text-neutral-500">
                  {o.criteria.length > 0 && <span className="text-sky-300">{o.criteria.length === 60 ? 'tutti i 60 criteri' : `criteri ${o.criteria.map((c) => `#${c}`).join(' ')}`}</span>}
                  {o.stats.avg_ms != null && <span>media {o.stats.avg_ms} ms</span>}
                  {o.stats.errors > 0 && <span className="text-amber-300">{o.stats.errors} con esito non OK</span>}
                  {o.stats.last_ts && <span>ultima {fmtTs(o.stats.last_ts)}</span>}
                  {o.stats.count > 0 && <button onClick={() => onShow(o.id)} className="ml-auto text-[#deffac] hover:underline">vedi eventi →</button>}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

export default function HQ({ bandi, onReplay }) {
  const [authed, setAuthed] = useState(Boolean(hqToken.get()))
  const [section, setSection] = useState('overview')
  const [overview, setOverview] = useState(null)
  const [ops, setOps] = useState([])
  const [opFilter, setOpFilter] = useState('')
  const [error, setError] = useState(null)

  const logout = useCallback(() => { hqToken.clear(); setAuthed(false); setOverview(null) }, [])
  const load = useCallback(async () => {
    try {
      const [o, list] = await Promise.all([api.hqOverview(), api.hqOperations()])
      setOverview(o); setOps(list); setError(null)
    } catch (e) { if (e.status === 401) logout(); else setError(e.message) }
  }, [logout])
  useEffect(() => { if (authed) load() }, [authed, load, section])

  const opsById = useMemo(() => Object.fromEntries(ops.map((o) => [o.id, o])), [ops])
  const goto = (s, op) => { if (op !== undefined) setOpFilter(op); setSection(s) }

  if (!authed) return <div className="space-y-6"><PageIntro title="Quartier Generale">Area riservata ai manager: timeline di tutti i processi, documenti e bandi lavorati, database e memoria del sistema. Inserisci il codice di accesso.</PageIntro><Gate onAuthed={() => setAuthed(true)} /></div>

  return (
    <div className="space-y-6">
      <PageIntro title="Quartier Generale" tips={['Ogni operazione dell’app lascia una traccia: qui la rivedi in ordine cronologico, con le sue fasi.', 'Le validazioni si possono riprodurre nel laboratorio dell’algoritmo.', 'Il database è consultabile in sola lettura; nulla si può modificare da qui.']}>
        Il posto da cui un manager vede tutto ciò che è successo nel sistema: processi, documenti, bandi, progetti e memoria.
      </PageIntro>
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex flex-wrap gap-1 bg-neutral-950 border border-neutral-800 p-1 rounded-xl">
          {SECTIONS.map(([id, label, Icon]) => (
            <button key={id} onClick={() => goto(id, '')} className={`px-3 py-2 text-xs font-bold rounded-lg flex items-center gap-1.5 ${section === id ? 'bg-[#deffac] text-black' : 'text-neutral-400 hover:text-white'}`}><Icon className="w-3.5 h-3.5" />{label}</button>
          ))}
        </div>
        <button onClick={logout} className="ml-auto px-3 py-2 rounded-xl border border-neutral-700 text-neutral-300 hover:border-neutral-500 text-xs font-bold flex items-center gap-1.5"><LogOut className="w-3.5 h-3.5" />Esci</button>
      </div>
      {error && <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-xs">{error}</div>}
      {!overview && !error && <p className="text-xs text-neutral-500 flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Caricamento…</p>}

      {overview && section === 'overview' && <Overview data={overview} opsById={opsById} goto={goto} />}
      {overview && section === 'timeline' && <Timeline key={opFilter} ops={ops} opsById={opsById} initialOp={opFilter} onReplay={onReplay} />}
      {overview && section === 'operations' && <Operations ops={ops} onShow={(id) => goto('timeline', id)} />}
      {overview && section === 'dossiers' && <Dossiers bandi={bandi} onReplay={onReplay} opsById={opsById} />}
      {overview && section === 'documents' && <Documents />}
      {overview && section === 'database' && <DbExplorer />}
      {overview && section === 'ingestion' && <IngestionPanel />}
    </div>
  )
}
