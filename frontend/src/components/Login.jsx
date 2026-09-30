import React, { useState } from 'react'
import { KeyRound, Loader2, X } from 'lucide-react'
import { api, session } from '../lib/api'

export function PasswordModal({ onClose }) {
  const [cur, setCur] = useState('')
  const [next, setNext] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [done, setDone] = useState(false)
  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError(null)
    try { await api.changePassword(cur, next); setDone(true); setTimeout(() => { session.clear(); window.dispatchEvent(new Event('quanto-logout')) }, 1500) }
    catch (err) { setError(err.message) } finally { setBusy(false) }
  }
  return (
    <div className="fixed inset-0 bg-white/40 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <form onSubmit={submit} className="glass-strong rounded-3xl w-full max-w-sm p-6 space-y-4 relative">
        <button type="button" onClick={onClose} aria-label="Chiudi" className="absolute top-4 right-4 text-ink-2 hover:text-ink"><X className="w-5 h-5" /></button>
        <h2 className="font-semibold flex items-center gap-2"><KeyRound className="w-4 h-4" />Cambia la password</h2>
        {done ? <p className="text-sm text-emerald-700">Fatto. Ora rientra con la nuova password.</p> : (
          <>
            <label className="block space-y-1"><span className="label">Password attuale</span><input type="password" autoComplete="current-password" value={cur} onChange={(e) => setCur(e.target.value)} className="field" /></label>
            <label className="block space-y-1"><span className="label">Nuova password (almeno 12 caratteri)</span><input type="password" autoComplete="new-password" value={next} onChange={(e) => setNext(e.target.value)} className="field" /></label>
            {error && <p className="text-xs text-red-700">{error}</p>}
            <button disabled={busy || !cur || next.length < 12} className="btn-primary w-full">{busy && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Cambia password</button>
          </>
        )}
      </form>
    </div>
  )
}
