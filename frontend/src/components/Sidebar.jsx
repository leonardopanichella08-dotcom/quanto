import React, { useEffect, useState } from 'react'
import { Briefcase, Building2, ChevronDown, LogOut, Menu, Plus, X } from 'lucide-react'
import { Mark, Wordmark } from './ui'
import { api } from '../lib/api'
import { CreditsRing } from './CreditsBadge'

const Item = ({ id, label, Icon, tab, onGo, extra }) => (
  <button className="nav-item" aria-current={tab === id ? 'page' : undefined} onClick={() => onGo(id)}>
    <Icon className="w-4 h-4 shrink-0" /><span className="truncate">{label}</span>{extra}
  </button>
)

function Group({ title, children }) {
  return (
    <div className="space-y-0.5">
      {title && <p className="px-3 pb-1 text-[10px] font-semibold uppercase tracking-[0.08em] text-mute">{title}</p>}
      {children}
    </div>
  )
}

/** Il lavoro attivo: l'azienda cliente su cui lavora lo studio. Tutte le pagine di lavoro mostrano i dati di quest'azienda. */
function Workspace({ clients, clientId, onChange, onNew }) {
  if (!clients) return <div className="h-14 rounded-lg bg-field animate-pulse" aria-hidden="true" />
  if (clients.length === 0) {
    return <button className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg border border-dashed border-line-strong text-[13px] text-ink-2 hover:bg-field" onClick={onNew}><Plus className="w-4 h-4" />Apri il primo lavoro</button>
  }
  const current = clients.find((c) => c.id === clientId)
  return (
    <label className="block relative">
      <span className="px-1 pb-1 block text-[10px] font-semibold uppercase tracking-[0.08em] text-mute">Lavoro attivo</span>
      <div className="relative">
        <Briefcase className="w-4 h-4 text-mute absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        <select aria-label="Lavoro attivo" value={clientId || ''} onChange={(e) => (e.target.value === '__new' ? onNew() : onChange(Number(e.target.value)))}
          className="field !pl-9 !pr-8 appearance-none font-medium truncate">
          {clients.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          <option value="__new">+ Nuovo lavoro…</option>
        </select>
        <ChevronDown className="w-3.5 h-3.5 text-mute absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
      </div>
      {current && <p className="px-1 pt-1 text-[11px] text-mute truncate">{[current.ateco_code && `ATECO ${current.ateco_code}`, current.region].filter(Boolean).join(' · ') || 'Profilo da completare'}</p>}
    </label>
  )
}

function Credits({ onClick }) {
  const [c, setC] = useState(null)
  useEffect(() => { api.meCredits().then(setC).catch(() => {}) }, [])
  if (!c) return null
  return (
    <button onClick={onClick} className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg hover:bg-field text-left" title={`${c.remaining} crediti su ${c.limit} · si rinnovano tra ${c.days_until_renewal} giorni`}>
      <CreditsRing pct={c.pct_remaining} size={22} />
      <span className="min-w-0"><span className="block text-[12px] font-medium text-ink tabular-nums">{c.remaining} crediti</span><span className="block text-[11px] text-mute">dello studio · su {c.limit}</span></span>
    </button>
  )
}

/** Menu di gestione a sinistra: lavoro attivo, pagine di lavoro, archivio, profilo e crediti dello studio. */
export default function Sidebar({ user, isOwner, tab, onGo, clients, clientId, onClient, onNewClient, onLogout, groups, footer, open, onClose }) {
  const body = (
    <div className="h-full flex flex-col gap-5 px-3 py-4 overflow-y-auto">
      <div className="flex items-center gap-2.5 px-1">
        <Mark size={28} />
        <Wordmark height={17} className="text-ink" />
        <button className="md:hidden ml-auto btn !px-2 !py-1.5" onClick={onClose} aria-label="Chiudi il menu"><X className="w-4 h-4" /></button>
      </div>
      <Workspace clients={clients} clientId={clientId} onChange={onClient} onNew={onNewClient} />
      <nav className="flex-1 space-y-5" aria-label="Pagine">
        {groups.map((g) => (
          <Group key={g.title} title={g.title}>
            {g.items.map(([id, label, Icon]) => <Item key={id} id={id} label={label} Icon={Icon} tab={tab} onGo={onGo} />)}
          </Group>
        ))}
      </nav>
      <div className="space-y-0.5 border-t border-line pt-3">
        {footer.map(([id, label, Icon]) => <Item key={id} id={id} label={label} Icon={Icon} tab={tab} onGo={onGo} />)}
        {isOwner && <Item id="hq" label="Quartier Generale" Icon={Building2} tab={tab} onGo={onGo} />}
        <Credits onClick={() => onGo('profilo')} />
        <div className="flex items-center gap-2.5 px-3 pt-2">
          <span className="w-7 h-7 rounded-full bg-tint-2 flex items-center justify-center text-[11px] font-semibold text-ink-2 shrink-0">{(user.name || user.email).slice(0, 1).toUpperCase()}</span>
          <span className="min-w-0 flex-1"><span className="block text-[12px] font-medium text-ink truncate">{user.name}</span><span className="block text-[11px] text-mute truncate">{user.email}</span></span>
          <button onClick={onLogout} className="btn !px-2 !py-1.5" title="Esci" aria-label="Esci"><LogOut className="w-3.5 h-3.5" /></button>
        </div>
      </div>
    </div>
  )
  return (
    <>
      <aside className="hidden md:block w-64 shrink-0 bg-white border-r border-line sticky top-0 h-screen">{body}</aside>
      {open && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div className="absolute inset-0 bg-ink/30" onClick={onClose} aria-hidden="true" />
          <aside className="relative w-72 max-w-[85vw] bg-white h-full shadow-xl">{body}</aside>
        </div>
      )}
    </>
  )
}

export function MobileBar({ onOpen }) {
  return (
    <div className="md:hidden sticky top-0 z-40 flex items-center gap-3 bg-white border-b border-line px-4 py-2.5">
      <button className="btn !px-2 !py-1.5" onClick={onOpen} aria-label="Apri il menu"><Menu className="w-4 h-4" /></button>
      <Mark size={24} /><Wordmark height={15} className="text-ink" />
    </div>
  )
}
