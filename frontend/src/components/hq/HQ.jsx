import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { api } from '../../lib/api'
import Guide from '../Guide'
import { PageHead } from '../ui'
import { Hint } from '../Help'
import Overview from './Overview'
import Access from './Access'
import Activity from './Activity'
import DataCenter from './DataCenter'
import Manual from './Manual'

/* Quartier Generale: cinque sezioni, ognuna con un compito solo.
   Panoramica (come sta il sistema) · Accessi (chi entra e utenti) · Attività (cosa è successo) · Dati (cosa QUANTO sa) · Manuale. */
const SECTIONS = [['overview', 'Panoramica'], ['access', 'Accessi'], ['activity', 'Attività'], ['data', 'Dati'], ['manual', 'Manuale']]
const SECTION_HINT = { overview: 'hq_panoramica', access: 'hq_accessi', activity: 'hq_timeline', data: 'hq_archivio' }

export default function HQ({ onReplay, user }) {
  const [section, setSection] = useState('overview')
  const [dataView, setDataView] = useState('bandi')
  const [opFilter, setOpFilter] = useState('')
  const [overview, setOverview] = useState(null)
  const [ops, setOps] = useState([])
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    try {
      const [o, list] = await Promise.all([api.hqOverview(), api.hqOperations()])
      setOverview(o); setOps(list); setError(null)
    } catch (e) { setError(e.message) }
  }, [])
  useEffect(() => { load() }, [load, section])

  const opsById = useMemo(() => Object.fromEntries(ops.map((o) => [o.id, o])), [ops])
  const goto = (s, sub) => {
    if (s === 'data' && sub) setDataView(sub)
    if (s === 'activity') setOpFilter(sub || '')
    setSection(s)
  }
  const pending = overview?.access?.PENDING || 0
  const todo = pending + (overview?.access?.mail_to_send || 0)

  return (
    <div className="space-y-6">
      <PageHead title="Quartier Generale" sub="Chi entra, cosa succede e cosa sa il sistema." />
      <Guide page="hq" />
      <div className="flex flex-wrap items-center gap-3 border-b border-line">
        <div className="flex flex-wrap gap-x-6 gap-y-1 flex-1">
          {SECTIONS.map(([id, label]) => (
            <button key={id} onClick={() => goto(id)} className={`pb-2.5 text-sm -mb-px border-b-2 transition inline-flex items-center gap-1.5 ${section === id ? 'border-brand text-ink font-medium' : 'border-transparent text-ink-2 hover:text-ink'}`}>
              {label}
              {id === 'access' && todo > 0 && <span className="min-w-[18px] h-[18px] px-1 rounded-full text-[11px] font-semibold flex items-center justify-center text-ink" style={{ background: '#F1E21B' }}>{todo}</span>}
            </button>
          ))}
        </div>
        {SECTION_HINT[section] && <Hint id={SECTION_HINT[section]} className="pb-2" />}
      </div>
      {error && <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-700 text-xs">{error}</div>}
      {!overview && !error && <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Caricamento…</p>}

      {overview && section === 'overview' && <Overview data={overview} ops={ops} opsById={opsById} goto={goto} />}
      {overview && section === 'access' && <Access me={user} onChanged={load} />}
      {overview && section === 'activity' && <Activity key={opFilter} ops={ops} opsById={opsById} onReplay={onReplay} initialOp={opFilter} />}
      {overview && section === 'data' && <DataCenter view={dataView} setView={setDataView} />}
      {overview && section === 'manual' && <Manual />}
    </div>
  )
}
