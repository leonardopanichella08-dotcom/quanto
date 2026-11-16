import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Check, ChevronDown, ChevronRight, Copy, Loader2, Mail, MailCheck, X } from 'lucide-react'
import { api } from '../../lib/api'
import { fmtTs } from '../../lib/format'
import Users from './Users'
import { Big, ChartTitle, Donut } from './charts'

/* Accessi: chi ha chiesto di entrare, a che livello, e l'e-mail di conferma già pronta.
   Percorso in tre passi, sempre uguale: 1) scegli il livello  2) approva (o rifiuta)  3) apri l'e-mail preparata e segnala che è partita. */

const copy = async (text) => { try { await navigator.clipboard.writeText(text); return true } catch { return false } }
const mailto = (to, subject, body) => `mailto:${encodeURIComponent(to)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`

function Pending({ r, levels, busy, onApprove, onReject }) {
  const [level, setLevel] = useState('USER')
  const [rejecting, setRejecting] = useState(false)
  const [reason, setReason] = useState('')
  const lv = levels.find((l) => l.id === level)
  return (
    <div className="py-4 border-t border-line first:border-0 space-y-3">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5">
        <span className="font-semibold text-sm">{r.name}</span>
        <span className="text-xs text-ink-2">{r.email}</span>
        {r.studio_name && <span className="text-xs text-ink-2">· {r.studio_name}</span>}
        <span className="text-[11px] text-mute font-mono ml-auto">{fmtTs(r.requested_at)}</span>
      </div>
      {!rejecting ? (
        <div className="flex flex-wrap items-center gap-3">
          <div className="inline-flex rounded-full bg-black/[0.05] p-0.5" role="radiogroup" aria-label="Livello da assegnare">
            {levels.map((l) => (
              <button key={l.id} role="radio" aria-checked={level === l.id} onClick={() => setLevel(l.id)} className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition ${level === l.id ? 'bg-brand text-white' : 'text-ink-2 hover:text-ink'}`}>{l.label}</button>
            ))}
          </div>
          <button className="btn-primary" disabled={busy} onClick={() => onApprove(r.id, level)}>{busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}Approva come {lv?.label}</button>
          <button className="btn" disabled={busy} onClick={() => setRejecting(true)}>Rifiuta</button>
          <p className="text-xs text-mute basis-full">{lv?.help}</p>
        </div>
      ) : (
        <div className="flex flex-wrap items-center gap-2">
          <input className="field !w-72" autoFocus placeholder="Motivo (facoltativo, finisce nell’e-mail)" value={reason} onChange={(e) => setReason(e.target.value)} />
          <button className="btn-primary" disabled={busy} onClick={() => onReject(r.id, reason)}>{busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <X className="w-3.5 h-3.5" />}Conferma il rifiuto</button>
          <button className="btn" onClick={() => setRejecting(false)}>Annulla</button>
        </div>
      )}
    </div>
  )
}

function MailToSend({ r, busy, onSent }) {
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState(false)
  const approved = r.status === 'APPROVED'
  return (
    <div className="py-3.5 border-t border-line first:border-0 space-y-2">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <span className="font-medium text-sm">{r.name}</span>
        <span className="text-xs text-ink-2">{r.email}</span>
        <span className={`text-[11px] px-2 py-0.5 rounded-full ${approved ? 'bg-brand text-white' : 'bg-black/[0.06] text-ink-2'}`}>{approved ? `approvato · ${r.level_label}` : 'rifiutato'}</span>
        <span className="ml-auto flex flex-wrap items-center gap-2">
          <a className="btn-primary" href={mailto(r.email, r.mail_subject, r.mail_body)}><Mail className="w-3.5 h-3.5" />Apri nella posta</a>
          <button className="btn" onClick={async () => { setCopied(await copy(`${r.mail_subject}\n\n${r.mail_body}`)); setTimeout(() => setCopied(false), 1800) }}>{copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}{copied ? 'Copiata' : 'Copia'}</button>
          <button className="btn" disabled={busy} onClick={() => onSent(r.id)}>{busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <MailCheck className="w-3.5 h-3.5" />}Segna inviata</button>
        </span>
      </div>
      <button onClick={() => setOpen(!open)} className="text-xs text-ink-2 hover:text-ink inline-flex items-center gap-1">{open ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}Leggi l’e-mail già pronta</button>
      {open && <div className="rounded-xl bg-black/[0.04] p-3 text-xs space-y-2"><p className="font-semibold">{r.mail_subject}</p><pre className="whitespace-pre-wrap font-sans text-ink-2 leading-relaxed">{r.mail_body}</pre></div>}
    </div>
  )
}

export default function Access({ me, onChanged }) {
  const [data, setData] = useState(null)
  const [users, setUsers] = useState([])
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(null)
  const [showDone, setShowDone] = useState(false)
  const load = useCallback(async () => {
    try { const [d, u] = await Promise.all([api.accessRequests(), api.users()]); setData(d); setUsers(u); setError(null); onChanged?.() } catch (e) { setError(e.message) }
  }, [onChanged])
  useEffect(() => { load() }, [load])
  const act = async (id, fn) => { setBusy(id); setError(null); try { await fn(); await load() } catch (e) { setError(e.message) } finally { setBusy(null) } }

  const pending = useMemo(() => (data?.requests || []).filter((r) => r.status === 'PENDING'), [data])
  const toSend = useMemo(() => (data?.requests || []).filter((r) => r.status !== 'PENDING' && !r.mail_sent_at), [data])
  const done = useMemo(() => (data?.requests || []).filter((r) => r.status !== 'PENDING' && r.mail_sent_at), [data])
  const hidden = useMemo(() => new Set((data?.requests || []).filter((r) => r.status !== 'APPROVED').map((r) => r.user_id)), [data])
  const active = users.filter((u) => u.active)
  if (!data) return error ? <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-700 text-xs">{error}</div> : <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Caricamento…</p>

  return (
    <div className="space-y-8">
      {error && <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-700 text-xs">{error}</div>}

      <div className="grid sm:grid-cols-3 gap-6 items-center">
        <Big label="Da decidere" value={pending.length} tone={pending.length ? 'text-ink' : 'text-mute'} note={pending.length ? 'scegli il livello e approva' : 'nessuna richiesta in attesa'} />
        <Big label="E-mail da inviare" value={toSend.length} tone={toSend.length ? 'text-ink' : 'text-mute'} note={toSend.length ? 'già scritte, mancano solo da spedire' : 'tutto inviato'} />
        <div><span className="label block mb-1.5">Utenti attivi per livello</span><Donut size={64} center={active.length} parts={[{ label: 'Utenti', value: active.filter((u) => u.role === 'USER').length }, { label: 'Manager', value: active.filter((u) => u.role === 'MANAGER').length }]} /></div>
      </div>

      <section className="card p-5">
        <ChartTitle>1 · Richieste di accesso</ChartTitle>
        {pending.length === 0
          ? <p className="text-sm text-ink-2">Nessuna richiesta da decidere. Quando qualcuno preme «Richiedi accesso» sul sito, la trovi qui.</p>
          : pending.map((r) => <Pending key={r.id} r={r} levels={data.levels} busy={busy === r.id} onApprove={(id, level) => act(id, () => api.approveAccess(id, level))} onReject={(id, reason) => act(id, () => api.rejectAccess(id, reason))} />)}
      </section>

      {toSend.length > 0 && (
        <section className="card p-5">
          <ChartTitle>2 · E-mail pronte da inviare</ChartTitle>
          <p className="text-xs text-ink-2 mb-1">QUANTO non spedisce da solo: «Apri nella posta» compila il messaggio nel tuo programma di posta, tu lo controlli e premi invio. Poi segna «inviata».</p>
          {toSend.map((r) => <MailToSend key={r.id} r={r} busy={busy === r.id} onSent={(id) => act(id, () => api.accessMailSent(id))} />)}
        </section>
      )}

      {done.length > 0 && (
        <section>
          <button onClick={() => setShowDone(!showDone)} className="text-xs text-ink-2 hover:text-ink inline-flex items-center gap-1">{showDone ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}Richieste già chiuse ({done.length})</button>
          {showDone && (
            <ul className="mt-2 divide-y divide-line text-xs">
              {done.map((r) => <li key={r.id} className="py-2 flex flex-wrap gap-x-3"><span className="font-medium">{r.name}</span><span className="text-ink-2">{r.email}</span><span>{r.status === 'APPROVED' ? `approvato · ${r.level_label}` : 'rifiutato'}</span><span className="text-mute font-mono ml-auto">{fmtTs(r.decided_at)}</span></li>)}
            </ul>
          )}
        </section>
      )}

      <section>
        <ChartTitle>Utenti</ChartTitle>
        <Users me={me} list={users} hideIds={hidden} reload={load} />
      </section>
    </div>
  )
}
