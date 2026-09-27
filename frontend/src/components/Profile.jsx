import React, { useCallback, useEffect, useState } from 'react'
import { Building2, KeyRound, Loader2, ShieldCheck, User } from 'lucide-react'
import { api } from '../lib/api'
import { fmtTs } from '../lib/format'
import { SectionTitle } from './ui'
import Documents from './Documents'
import Guide from './Guide'

const STATUS_TONE = { OK: 'text-emerald-700', WARN: 'text-amber-700', FAIL: 'text-red-700', DENIED: 'text-red-700', LOCKED: 'text-red-700', CONFLICT: 'text-amber-700', NOT_FOUND: 'text-amber-700' }
const ROLE_LABEL = { MANAGER: 'Manager', USER: 'Utente' }

function Activity() {
  const [list, setList] = useState(null)
  const [error, setError] = useState(null)
  const load = useCallback(() => api.meActivity(30).then(setList).catch((e) => setError(e.message)), [])
  useEffect(() => { load() }, [load])
  return (
    <div className="card p-5 space-y-3">
      <SectionTitle>Le tue operazioni recenti</SectionTitle>
      {error && <p className="text-xs text-red-700">{error}</p>}
      {!list && !error && <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Carico…</p>}
      {list && list.length === 0 && <p className="text-xs text-mute">Ancora nessuna operazione registrata su questo account.</p>}
      {list && list.length > 0 && (
        <div className="space-y-1.5 max-h-96 overflow-y-auto">
          {list.map((e) => (
            <div key={e.id} className="flex gap-3 text-xs border-b border-line pb-1.5 last:border-0">
              <span className="font-mono text-[11px] text-mute w-32 shrink-0">{fmtTs(e.ts)}</span>
              <span className={`shrink-0 font-medium w-20 ${STATUS_TONE[e.status] || 'text-ink-2'}`}>{e.status !== 'OK' ? e.status : ''}</span>
              <span className="text-ink-2 leading-snug">{e.summary}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function Profile({ user, isOwner, onChangePassword, onGoHQ, onUsePayslip, onUseBalance, onUseDraft }) {
  return (
    <div className="space-y-6">
      <Guide page="profilo" />
      <div className="card p-5 flex flex-wrap items-center gap-4">
        <div className="w-12 h-12 rounded-2xl bg-tint-2 flex items-center justify-center shrink-0"><User className="w-6 h-6 text-ink-2" /></div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-ink truncate">{user.name}</p>
          <p className="text-xs text-mute truncate">{user.email} · {ROLE_LABEL[user.role] || user.role}</p>
        </div>
        <button onClick={onChangePassword} className="btn ml-auto"><KeyRound className="w-3.5 h-3.5" />Cambia password</button>
      </div>

      {isOwner && (
        <button onClick={onGoHQ} className="w-full card p-5 flex items-center gap-4 text-left hover:border-line-strong transition">
          <div className="w-12 h-12 rounded-2xl bg-brand/20 flex items-center justify-center shrink-0"><Building2 className="w-6 h-6 text-brand-ink" /></div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-ink">Quartier Generale</p>
            <p className="text-xs text-mute">Riservato a te: memoria del sistema, bandi, tabelle ufficiali, utenti e database.</p>
          </div>
          <ShieldCheck className="w-4 h-4 text-mute shrink-0" />
        </button>
      )}

      <Activity />

      <div className="space-y-3">
        <div className="flex items-center gap-2 px-1"><span className="text-sm font-medium text-ink">I tuoi documenti</span></div>
        <p className="text-xs text-mute px-1 -mt-2">Buste paga, bilanci, F24 e bozze di candidatura che hai caricato: solo tu li vedi.</p>
        <Documents onUsePayslip={onUsePayslip} onUseBalance={onUseBalance} onUseDraft={onUseDraft} />
      </div>
    </div>
  )
}
