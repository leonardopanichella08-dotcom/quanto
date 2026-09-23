import React, { useState } from 'react'
import { KeyRound, Loader2, LogIn, ShieldCheck, X } from 'lucide-react'
import { api, session } from '../lib/api'
import { Mark, Wordmark } from './ui'

export function LoginScreen({ onLogin, onAuditor }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError(null)
    try {
      const res = await api.login(email.trim(), password)
      session.set(res.access_token, res.user)
      onLogin(res.user)
    } catch (err) { setError(err.message) } finally { setBusy(false); setPassword('') }
  }
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="liquid-bg" aria-hidden="true"><span /><span /><span /></div>
      <form onSubmit={submit} className="glass-strong rounded-3xl w-full max-w-sm p-8 space-y-5">
        <div className="flex items-center gap-3"><Mark size={40} /><Wordmark height={22} className="text-ink" /></div>
        <div>
          <h1 className="text-lg font-semibold">Accedi</h1>
          <p className="text-xs text-ink-2 mt-0.5">Controllo dei budget per i bandi. Usa l’account che ti ha dato il tuo referente.</p>
        </div>
        <label className="block space-y-1"><span className="label">E-mail</span>
          <input type="email" autoComplete="username" autoFocus required value={email} onChange={(e) => setEmail(e.target.value)} className="field !py-2.5 text-sm" /></label>
        <label className="block space-y-1"><span className="label">Password</span>
          <input type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} className="field !py-2.5 text-sm" /></label>
        <button disabled={busy || !email || !password} className="btn-primary w-full !py-2.5">{busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <LogIn className="w-3.5 h-3.5" />}Entra</button>
        {error && <p className="text-xs text-red-700" role="alert">{error}</p>}
        <p className="text-[11px] text-mute leading-relaxed">Dopo 5 tentativi sbagliati l’account si blocca per 15 minuti. Ogni accesso viene registrato.</p>
        <button type="button" onClick={onAuditor} className="text-xs text-brand-ink hover:underline inline-flex items-center gap-1.5"><ShieldCheck className="w-3.5 h-3.5" />Sei un revisore? Verifica un budget certificato</button>
      </form>
    </div>
  )
}

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
