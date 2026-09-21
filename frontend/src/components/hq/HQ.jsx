import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Archive as Archive2, Scale, Building2, Database, FileText, FolderOpen, Gauge, History, KeyRound, ListTree, Loader2, LogOut, Lock, Network, Play, Wrench } from 'lucide-react'
import { api } from '../../lib/api'
import { fmtBytes, fmtTs } from '../../lib/format'
import Guide from '../Guide'
import { PageHead } from '../ui'
import { Hint } from '../Help'
import IngestionPanel from '../IngestionPanel'
import { DbExplorer, Dossiers, Documents } from './HQSections'
import Archive from './Archive'
import FonteB from './FonteB'
import Users from './Users'

const SECTIONS = [
  ['overview', 'Panoramica', Gauge], ['timeline', 'Timeline', History], ['operations', 'Mappa operazioni', Network],
  ['archive', 'Archivio bandi', Archive2], ['fonteb', 'Tabelle ufficiali', Scale], ['users', 'Utenti', KeyRound], ['dossiers', 'Fascicoli', FolderOpen], ['documents', 'Documenti', FileText], ['database', 'Database', Database], ['ingestion', 'Caricamento bandi', Wrench],
]
const STATUS_LABEL = { OK: 'OK', WARN: 'Attenzione', FAIL: 'Non superato', DENIED: 'Negato', LOCKED: 'Bloccato', CONFLICT: 'Conflitto', NOT_FOUND: 'Non trovato' }
const SECTION_HINT = { overview: 'hq_panoramica', timeline: 'hq_timeline', operations: 'hq_operazioni', archive: 'hq_archivio', fonteb: 'hq_archivio', users: 'hq_archivio', dossiers: 'hq_fascicoli', documents: 'hq_documenti', database: 'hq_database', ingestion: 'hq_caricamento' }
const STATUS_TONE = { OK: 'text-emerald-700', WARN: 'text-amber-700', FAIL: 'text-red-700', DENIED: 'text-red-700', LOCKED: 'text-red-700', CONFLICT: 'text-amber-700', NOT_FOUND: 'text-amber-700' }

function Kpi({ label, value, note, tone = 'text-ink' }) {
  return <div className="card p-4"><span className="label">{label}</span><div className={`text-2xl font-bold font-mono mt-1 ${tone}`}>{value}</div>{note && <p className="text-xs text-mute mt-1">{note}</p>}</div>
}

function Overview({ data, opsById, goto }) {
  const c = data.counts
  const maxDay = Math.max(...data.events_by_day.map((d) => d.n), 1)
  const docsTotal = Object.values(data.documents_by_kind).reduce((a, b) => a + b, 0)
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        <Kpi label="Budget controllati" value={data.validations} note={data.last_validation_ts ? `ultima ${fmtTs(data.last_validation_ts)}` : 'nessuna ancora'} tone="text-brand-ink" />
        <Kpi label="Progetti" value={data.projects} />
        <Kpi label="Bandi" value={c.bandi} note={`${c.rules} regole · ${c.requirements} requisiti`} />
        <Kpi label="Documenti" value={docsTotal} note={Object.entries(data.documents_by_kind).map(([k, v]) => `${v} ${k.replace('_', ' ').toLowerCase()}`).join(' · ') || '—'} />
        <Kpi label="Eventi" value={c.events} note="ogni operazione lascia una traccia" />
        <Kpi label="Registrazioni" value={data.registry.entries} note={data.registry.intact ? 'registro integro' : 'REGISTRO ALTERATO'} tone={data.registry.intact ? 'text-emerald-700' : 'text-red-700'} />
      </div>

      <div className="grid lg:grid-cols-3 gap-4">
        <div className={`card p-4 space-y-2 ${data.storage.volatile ? '!border-amber-500/40' : ''}`}>
          <span className="label flex items-center gap-1.5"><Database className="w-3.5 h-3.5" />Memoria e database</span>
          <p className="text-sm font-mono">{data.storage.engine} · {fmtBytes(data.storage.size_bytes)}</p>
          <p className={`text-xs leading-relaxed ${data.storage.volatile ? 'text-amber-700' : 'text-ink-2'}`}>{data.storage.volatile && <AlertTriangle className="w-3 h-3 inline mr-1" />}{data.storage.note}</p>
        </div>
        <div className={`card p-4 space-y-2 ${!data.auth.required ? '!border-amber-500/40' : ''}`}>
          <span className="label flex items-center gap-1.5"><KeyRound className="w-3.5 h-3.5" />Sicurezza dell’accesso</span>
          <p className={`text-xs leading-relaxed ${data.auth.required ? 'text-emerald-700' : 'text-amber-700'}`}>{data.auth.required ? `Accesso protetto: ${data.auth.users} utenti, ${data.auth.managers} manager. Password con scrypt, blocco dopo 5 errori, token da 8 ore.` : 'ATTENZIONE: l’autenticazione è spenta (QUANTO_AUTH_REQUIRED=0). Va tenuta spenta solo in sviluppo.'}</p>
          <p className={`text-xs ${data.registry.is_dev_key ? 'text-amber-700' : 'text-ink-2'}`}>Firma del registro: chiave {data.registry.key_id}{data.registry.is_dev_key ? ' (di prova)' : ''}</p>
        </div>
        <div className="card p-4 space-y-2">
          <span className="label">Attività negli ultimi giorni</span>
          <div className="flex items-end gap-1 h-16">
            {data.events_by_day.map((d) => <div key={d.day} title={`${d.day}: ${d.n}`} className="flex-1 max-w-[36px] bg-brand rounded-t" style={{ height: `${Math.max(6, (d.n / maxDay) * 100)}%` }} />)}
            {data.events_by_day.length === 0 && <p className="text-xs text-mute italic">Nessun evento.</p>}
          </div>
        </div>
      </div>

      <div className="card p-4 space-y-2">
        <div className="flex items-center justify-between"><span className="label">Ultimi eventi</span><button onClick={() => goto('timeline')} className="text-xs text-brand-ink hover:underline">Timeline completa →</button></div>
        {data.recent_events.map((e) => (
          <div key={e.id} className="flex flex-wrap items-center gap-x-3 text-xs border-b border-line py-1.5 last:border-0">
            <span className="font-mono text-[11px] text-mute w-32 shrink-0">{fmtTs(e.ts)}</span>
            <span className="text-brand-ink font-semibold shrink-0">{opsById[e.op]?.title || e.op}</span>
            <span className="text-ink-2 truncate">{e.summary}</span>
          </div>
        ))}
        {data.recent_events.length === 0 && <p className="text-xs text-mute">Ancora nessuna operazione registrata.</p>}
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

function Operations({ ops, onShow }) {
  const areas = useMemo(() => { const m = {}; ops.forEach((o) => { (m[o.area] ||= []).push(o) }); return Object.entries(m) }, [ops])
  return (
    <div className="space-y-6">
      <p className="text-xs text-ink-2">Tutto ciò che l’app sa fare, con i passaggi interni nell’ordine reale e quante volte è stato eseguito.</p>
      {areas.map(([area, list]) => (
        <div key={area} className="space-y-3">
          <h3 className="label">{area}</h3>
          <div className="grid lg:grid-cols-2 gap-3">
            {list.map((o) => (
              <div key={o.id} className="card p-4 space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div><p className="font-bold text-sm">{o.title}</p><p className="text-[11px] font-mono text-mute">{o.endpoint}</p></div>
                  <div className="text-right shrink-0"><p className="font-mono text-lg font-bold text-brand-ink">{o.stats.count}</p><p className="text-[11px] text-mute">esecuzioni</p></div>
                </div>
                <p className="text-xs text-ink-2 leading-relaxed">{o.description}</p>
                <ol className="space-y-1">{o.stages.map((s, i) => (
                  <li key={s} className="flex items-center gap-2 text-xs text-ink-2"><span className="w-4 h-4 rounded-full bg-tint-2 text-[10px] font-bold flex items-center justify-center text-ink-2 shrink-0">{i + 1}</span>{s}</li>))}</ol>
                <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono text-mute">
                  {o.criteria.length > 0 && <span className="text-sky-700">{o.criteria.length === 60 ? 'tutti i 60 controlli' : `controlli ${o.criteria.map((c) => `#${c}`).join(' ')}`}</span>}
                  {o.stats.avg_ms != null && <span>media {o.stats.avg_ms} ms</span>}
                  {o.stats.errors > 0 && <span className="text-amber-700">{o.stats.errors} con esito non riuscito</span>}
                  {o.stats.last_ts && <span>ultima {fmtTs(o.stats.last_ts)}</span>}
                  {o.stats.count > 0 && <button onClick={() => onShow(o.id)} className="ml-auto text-brand-ink hover:underline">vedi eventi →</button>}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

export default function HQ({ bandi, onReplay, user }) {
  const [section, setSection] = useState('overview')
  const [overview, setOverview] = useState(null)
  const [ops, setOps] = useState([])
  const [opFilter, setOpFilter] = useState('')
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    try {
      const [o, list] = await Promise.all([api.hqOverview(), api.hqOperations()])
      setOverview(o); setOps(list); setError(null)
    } catch (e) { setError(e.message) }
  }, [])
  useEffect(() => { load() }, [load, section])

  const opsById = useMemo(() => Object.fromEntries(ops.map((o) => [o.id, o])), [ops])
  const goto = (s, op) => { if (op !== undefined) setOpFilter(op); setSection(s) }

  return (
    <div className="space-y-6">
      <PageHead icon={Building2} title="Quartier Generale" sub="Tutto ciò che è successo nel sistema, e i dati per intervenire." />
      <Guide page="hq" />
      <div className="flex flex-wrap items-center gap-3 border-b border-line">
        <div className="flex flex-wrap gap-x-5 gap-y-1 flex-1">
          {SECTIONS.map(([id, label, Icon]) => (
            <button key={id} onClick={() => goto(id, '')} className={`pb-2.5 text-sm -mb-px border-b-2 transition inline-flex items-center gap-1.5 ${section === id ? 'border-brand text-ink font-medium' : 'border-transparent text-ink-2 hover:text-ink'}`}><Icon className="w-3.5 h-3.5" />{label}</button>
          ))}
        </div>
        <Hint id={SECTION_HINT[section]} className="pb-2" />
      </div>
      {error && <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-700 text-xs">{error}</div>}
      {!overview && !error && <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Caricamento…</p>}

      {overview && section === 'overview' && <Overview data={overview} opsById={opsById} goto={goto} />}
      {overview && section === 'timeline' && <Timeline key={opFilter} ops={ops} opsById={opsById} initialOp={opFilter} onReplay={onReplay} />}
      {overview && section === 'operations' && <Operations ops={ops} onShow={(id) => goto('timeline', id)} />}
      {overview && section === 'archive' && <Archive />}
      {overview && section === 'fonteb' && <FonteB />}
      {overview && section === 'users' && <Users me={user} />}
      {overview && section === 'dossiers' && <Dossiers bandi={bandi} onReplay={onReplay} opsById={opsById} />}
      {overview && section === 'documents' && <Documents />}
      {overview && section === 'database' && <DbExplorer />}
      {overview && section === 'ingestion' && <IngestionPanel />}
    </div>
  )
}
