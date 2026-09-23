import React, { useCallback, useEffect, useState } from 'react'
import { Loader2, Unlock, UserPlus } from 'lucide-react'
import { api } from '../../lib/api'
import { SectionTitle } from '../ui'

export default function Users({ me }) {
  const [list, setList] = useState([])
  const [form, setForm] = useState({ email: '', name: '', password: '', role: 'USER' })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(null)
  const [reset, setReset] = useState({})
  const load = useCallback(() => api.users().then(setList).catch((e) => setError(e.message)), [])
  useEffect(() => { load() }, [load])
  const act = async (id, fn) => { setBusy(id); setError(null); try { await fn(); await load() } catch (e) { setError(e.message) } finally { setBusy(null) } }
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })
  return (
    <div className="space-y-5">
      {error && <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-700 text-xs">{error}</div>}
      <div className="card p-5 space-y-3">
        <SectionTitle icon={UserPlus}>Nuovo utente</SectionTitle>
        <p className="text-xs text-ink-2">Comunica tu la password iniziale (almeno 12 caratteri, lettere e numeri). L’utente può cambiarla dal suo profilo.</p>
        <div className="grid md:grid-cols-4 gap-3 text-xs">
          <label className="space-y-1"><span className="label">E-mail</span><input className="field" type="email" value={form.email} onChange={set('email')} /></label>
          <label className="space-y-1"><span className="label">Nome</span><input className="field" value={form.name} onChange={set('name')} /></label>
          <label className="space-y-1"><span className="label">Password iniziale</span><input className="field" type="password" autoComplete="new-password" value={form.password} onChange={set('password')} /></label>
          <label className="space-y-1"><span className="label">Ruolo</span><select className="field" value={form.role} onChange={set('role')}><option value="USER">Utente</option><option value="MANAGER">Manager</option></select></label>
        </div>
        <button className="btn-primary" disabled={!form.email || !form.name || form.password.length < 12 || busy === 'new'}
          onClick={() => act('new', async () => { await api.createUser(form); setForm({ email: '', name: '', password: '', role: 'USER' }) })}>Crea utente</button>
      </div>
      <div className="card p-5 space-y-3">
        <SectionTitle>Utenti ({list.length})</SectionTitle>
        {list.map((u) => (
          <div key={u.id} className="p-3 rounded-xl border border-line bg-field text-xs flex flex-wrap items-center gap-3">
            <span className="font-medium text-ink">{u.name}</span><span className="text-ink-2">{u.email}</span>
            <span className={`px-1.5 py-0.5 rounded border ${u.role === 'MANAGER' ? 'text-brand-ink border-brand/60' : 'text-ink-2 border-line-strong'}`}>{u.role === 'MANAGER' ? 'manager' : 'utente'}</span>
            {!u.active && <span className="text-red-700">disattivato</span>}
            {u.locked && <span className="text-amber-700">bloccato</span>}
            <span className="text-mute">{u.last_login_at ? `ultimo accesso ${u.last_login_at.slice(0, 16).replace('T', ' ')}` : 'mai entrato'}</span>
            <span className="ml-auto flex flex-wrap items-center gap-2">
              {u.locked && <button className="btn !py-1" onClick={() => act(u.id, () => api.patchUser(u.id, { unlock: true }))}><Unlock className="w-3 h-3" />Sblocca</button>}
              <input className="field !w-40 !py-1" type="password" autoComplete="new-password" placeholder="nuova password" value={reset[u.id] || ''} onChange={(e) => setReset({ ...reset, [u.id]: e.target.value })} />
              <button className="btn !py-1" disabled={(reset[u.id] || '').length < 12 || busy === u.id} onClick={() => act(u.id, async () => { await api.patchUser(u.id, { new_password: reset[u.id] }); setReset({ ...reset, [u.id]: '' }) })}>Reimposta</button>
              <button className="btn !py-1" disabled={busy === u.id || u.id === me?.id} onClick={() => act(u.id, () => api.patchUser(u.id, { active: !u.active }))}>{busy === u.id ? <Loader2 className="w-3 h-3 animate-spin" /> : null}{u.active ? 'Disattiva' : 'Riattiva'}</button>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
