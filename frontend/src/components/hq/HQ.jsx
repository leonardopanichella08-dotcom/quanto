import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Database, Loader2, Megaphone, Settings2, Sun, Users as UsersIcon } from 'lucide-react'
import { api } from '../../lib/api'
import Today from './Today'
import Access from './Access'
import Marketing from './Marketing'
import Data from './Data'
import System from './System'

/* Quartier Generale, ricostruito per capirsi al primo sguardo: un menu a sinistra con cinque voci, ognuna con una riga che dice a cosa serve.
   Oggi (cosa fare e domande ai dati) · Accessi (chi entra) · Marketing (sito e LinkedIn) · Dati (tutto ciò che QUANTO sa) · Sistema (cronologia e salute). */
const SECTIONS = [
  ['today', 'Oggi', 'Cosa fare e domande ai dati', Sun],
  ['access', 'Accessi', 'Richieste, livelli, utenti', UsersIcon],
  ['marketing', 'Marketing', 'Sito, post e campagne LinkedIn', Megaphone],
  ['data', 'Dati', 'Esplora, scarica, correggi', Database],
  ['system', 'Sistema', 'Cronologia, salute, manuale', Settings2],
]
const DEFAULT_SUB = { marketing: 'overview', data: 'explore', system: 'activity' }

export default function HQ({ onReplay, user }) {
  const url = new URLSearchParams(window.location.search)
  const start = SECTIONS.some(([id]) => id === url.get('hq')) ? url.get('hq') : 'today'
  const [section, setSection] = useState(start)
  const [sub, setSub] = useState({ ...DEFAULT_SUB, ...(start === 'marketing' && url.get('linkedin') ? { marketing: 'accounts' } : {}) })
  const [overview, setOverview] = useState(null)
  const [ops, setOps] = useState([])
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    try { const [o, list] = await Promise.all([api.hqOverview(), api.hqOperations()]); setOverview(o); setOps(list); setError(null) } catch (e) { setError(e.message) }
  }, [])
  useEffect(() => { load() }, [load, section])
  const opsById = useMemo(() => Object.fromEntries(ops.map((o) => [o.id, o])), [ops])
  const goto = (s, v) => { if (v) setSub((x) => ({ ...x, [s]: v })); setSection(s); window.scrollTo({ top: 0 }) }
  const setView = (s) => (v) => setSub((x) => ({ ...x, [s]: v }))
  const badge = { access: (overview?.access?.PENDING || 0) + (overview?.access?.mail_to_send || 0) }
  const current = SECTIONS.find(([id]) => id === section)

  return (
    <div className="grid lg:grid-cols-[220px_1fr] gap-8 pt-2">
      <aside className="lg:sticky lg:top-6 self-start space-y-4">
        <div><h2 className="text-[22px] font-semibold tracking-tight">Quartier Generale</h2><p className="text-xs text-mute">Solo per il titolare</p></div>
        <nav className="flex lg:flex-col gap-1 overflow-x-auto">
          {SECTIONS.map(([id, label, hint, Icon]) => (
            <button key={id} onClick={() => goto(id)} className={`text-left flex items-start gap-3 rounded-xl px-3 py-2.5 shrink-0 transition ${section === id ? 'bg-brand text-white' : 'hover:bg-black/[0.05]'}`}>
              <Icon className="w-4 h-4 mt-0.5 shrink-0" />
              <span className="min-w-0"><span className="flex items-center gap-2 text-sm font-medium">{label}
                {badge[id] > 0 && <span className="min-w-[18px] h-[18px] px-1 rounded-full text-[11px] font-semibold flex items-center justify-center text-ink" style={{ background: '#F1E21B' }}>{badge[id]}</span>}</span>
                <span className={`hidden lg:block text-[11px] ${section === id ? 'text-white/70' : 'text-mute'}`}>{hint}</span></span>
            </button>
          ))}
        </nav>
      </aside>

      <main className="min-w-0 space-y-6">
        <div className="flex items-baseline gap-2"><h3 className="text-[26px] font-semibold tracking-tight">{current[1]}</h3><span className="text-sm text-mute ml-2 hidden sm:inline">{current[2]}</span></div>
        {error && <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-700 text-xs">{error}</div>}
        {!overview && !error && <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Caricamento…</p>}
        {overview && section === 'today' && <Today data={overview} goto={goto} />}
        {overview && section === 'access' && <Access me={user} onChanged={load} />}
        {overview && section === 'marketing' && <Marketing view={sub.marketing} setView={setView('marketing')} />}
        {overview && section === 'data' && <Data view={sub.data} setView={setView('data')} />}
        {overview && section === 'system' && <System view={sub.system} setView={setView('system')} data={overview} ops={ops} opsById={opsById} onReplay={onReplay} />}
      </main>
    </div>
  )
}
