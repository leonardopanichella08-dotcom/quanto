import React, { useCallback, useEffect, useState } from 'react'
import { Briefcase, Building2, Download, KeyRound, Loader2, LogOut, ShieldCheck, Sparkles, Trash2, User } from 'lucide-react'
import { api, download, session } from '../lib/api'
import { fmtTs } from '../lib/format'
import { SectionTitle } from './ui'
import Documents from './Documents'
import CompanyProfile from './CompanyProfile'
import ProfileSetup from './ProfileSetup'
import Guide from './Guide'
import { CreditsRing } from './CreditsBadge'
import { ClientsPanel } from './Clients'

const STATUS_TONE = { OK: 'text-emerald-700', WARN: 'text-amber-700', FAIL: 'text-red-700', DENIED: 'text-red-700', LOCKED: 'text-red-700', CONFLICT: 'text-amber-700', NOT_FOUND: 'text-amber-700' }
const ROLE_LABEL = { MANAGER: 'Manager', USER: 'Utente' }

function Credits() {
  const [c, setC] = useState(null)
  const [error, setError] = useState(null)
  useEffect(() => { api.meCredits().then(setC).catch((e) => setError(e.message)) }, [])
  return (
    <div className="card p-5 space-y-3">
      <SectionTitle icon={Sparkles}>Piano e crediti</SectionTitle>
      {error && <p className="text-xs text-red-700">{error}</p>}
      {!c && !error && <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Carico…</p>}
      {c && (
        <div className="flex flex-wrap items-center gap-5">
          <CreditsRing pct={c.pct_remaining} size={64} />
          <div className="min-w-[14rem] flex-1">
            <p className="text-sm font-semibold text-ink">{c.plan}</p>
            <p className="text-xs text-ink-2 mt-0.5">{c.remaining} crediti disponibili su {c.limit} · {c.used} usati in questo ciclo</p>
            <div className="h-1.5 rounded-full bg-tint-2 overflow-hidden mt-2 max-w-xs">
              <div className="h-full rounded-full bg-brand" style={{ width: `${100 - c.pct_remaining}%` }} />
            </div>
            <p className="text-[11px] text-mute mt-2">Se finiscono, si ricaricano tra {c.days_until_renewal} giorni ({c.renews_at}). Un credito = un controllo del budget.</p>
          </div>
        </div>
      )}
      <p className="text-[11px] text-mute border-t border-line pt-2.5">Oggi QUANTO è gratuito: questa è un'anteprima di come funzionerà un piano annuale a consumo quando arriveranno i piani a pagamento.</p>
    </div>
  )
}

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


const SECTIONS = [['lavori', 'Lavori', Briefcase], ['studio', 'Studio e dati', User], ['sicurezza', 'Sicurezza', ShieldCheck], ['piano', 'Piano e dati', Sparkles]]

function Notice({ tone = 'ok', children }) {
  return <p className={`text-xs ${tone === 'ok' ? 'text-emerald-700' : 'text-red-700'}`} role={tone === 'ok' ? 'status' : 'alert'}>{children}</p>
}

/** I dati dello studio: chi sei, come ti chiami in fattura, come ti raggiungono. L'e-mail è l'accesso e non si cambia da qui. */
function StudioData({ me, onSaved }) {
  const [f, setF] = useState(null)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState(null)
  useEffect(() => { if (me) setF({ name: me.name || '', studio_name: me.studio_name || '', studio_vat: me.studio_vat || '', phone: me.phone || '', job_title: me.job_title || '' }) }, [me])
  if (!f) return <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Carico…</p>
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })
  const save = async (e) => {
    e.preventDefault(); setBusy(true); setMsg(null)
    try { const u = await api.updateMe(f); setMsg({ ok: true, text: 'Dati salvati.' }); onSaved(u) } catch (err) { setMsg({ ok: false, text: err.message }) } finally { setBusy(false) }
  }
  return (
    <form onSubmit={save} className="card p-6 space-y-5 max-w-3xl">
      <div><SectionTitle>Dati dello studio</SectionTitle><p className="text-xs text-mute mt-1">Compaiono nei documenti e nelle esportazioni dello studio.</p></div>
      <div className="grid sm:grid-cols-2 gap-4">
        <label className="space-y-1"><span className="label">Nome e cognome</span><input className="field" value={f.name} onChange={set('name')} maxLength={120} required autoComplete="name" /></label>
        <label className="space-y-1"><span className="label">Ruolo</span><input className="field" value={f.job_title} onChange={set('job_title')} maxLength={80} placeholder="Dottore commercialista, consulente…" /></label>
        <label className="space-y-1 sm:col-span-2"><span className="label">Ragione sociale dello studio</span><input className="field" value={f.studio_name} onChange={set('studio_name')} maxLength={160} autoComplete="organization" /></label>
        <label className="space-y-1"><span className="label">Partita IVA dello studio</span><input className="field" value={f.studio_vat} onChange={set('studio_vat')} inputMode="numeric" placeholder="11 cifre" /></label>
        <label className="space-y-1"><span className="label">Telefono</span><input className="field" value={f.phone} onChange={set('phone')} autoComplete="tel" placeholder="+39 …" /></label>
        <label className="space-y-1 sm:col-span-2"><span className="label">E-mail di accesso</span><input className="field bg-field text-mute" value={me.email} readOnly aria-readonly="true" /><span className="text-[11px] text-mute">È il tuo identificativo di accesso: non si modifica da qui.</span></label>
      </div>
      <div className="flex items-center gap-3"><button className="btn-primary" disabled={busy}>{busy && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Salva i dati</button>{msg && <Notice tone={msg.ok ? 'ok' : 'err'}>{msg.text}</Notice>}</div>
    </form>
  )
}

const RULES = [['Almeno 12 caratteri', (p) => p.length >= 12], ['Contiene lettere e numeri', (p) => /[A-Za-z]/.test(p) && /\d/.test(p)]]

function PasswordForm({ email }) {
  const [cur, setCur] = useState('')
  const [next, setNext] = useState('')
  const [again, setAgain] = useState('')
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState(null)
  const ok = RULES.every(([, t]) => t(next)) && next === again && cur && !next.toLowerCase().includes((email || '').split('@')[0].toLowerCase())
  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setMsg(null)
    try {
      await api.changePassword(cur, next)
      setMsg({ ok: true, text: 'Password cambiata. Per sicurezza ora si esce da tutti i dispositivi: rientra con la nuova password.' })
      setTimeout(() => { session.clear(); window.dispatchEvent(new Event('quanto-logout')) }, 2200)
    } catch (err) { setMsg({ ok: false, text: err.message }) } finally { setBusy(false) }
  }
  return (
    <form onSubmit={submit} className="card p-6 space-y-4 max-w-xl">
      <div><SectionTitle icon={KeyRound}>Cambia la password</SectionTitle><p className="text-xs text-mute mt-1">Dopo il cambio tutti i dispositivi collegati vengono scollegati.</p></div>
      <label className="block space-y-1"><span className="label">Password attuale</span><input className="field" type="password" autoComplete="current-password" value={cur} onChange={(e) => setCur(e.target.value)} /></label>
      <label className="block space-y-1"><span className="label">Nuova password</span><input className="field" type="password" autoComplete="new-password" value={next} onChange={(e) => setNext(e.target.value)} /></label>
      <label className="block space-y-1"><span className="label">Ripeti la nuova password</span><input className="field" type="password" autoComplete="new-password" value={again} onChange={(e) => setAgain(e.target.value)} /></label>
      <ul className="text-[11px] space-y-0.5">
        {RULES.map(([t, test]) => <li key={t} className={test(next) ? 'text-emerald-700' : 'text-mute'}>{test(next) ? '✓' : '○'} {t}</li>)}
        <li className={next && next === again ? 'text-emerald-700' : 'text-mute'}>{next && next === again ? '✓' : '○'} Le due password coincidono</li>
        <li className="text-mute">○ Non deve contenere la parte iniziale della tua e-mail</li>
      </ul>
      <div className="flex items-center gap-3"><button className="btn-primary" disabled={busy || !ok}>{busy && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Cambia password</button>{msg && <Notice tone={msg.ok ? 'ok' : 'err'}>{msg.text}</Notice>}</div>
    </form>
  )
}

function Security({ me, logins }) {
  const [busy, setBusy] = useState(false)
  const out = async () => {
    if (!window.confirm('Uscire da tutti i dispositivi, compreso questo? Per rientrare servirà la password.')) return
    setBusy(true)
    try { await api.signOutEverywhere() } finally { session.clear(); window.dispatchEvent(new Event('quanto-logout')) }
  }
  return (
    <div className="space-y-6">
      <PasswordForm email={me.email} />
      <div className="card p-6 space-y-4 max-w-xl">
        <div><SectionTitle icon={LogOut}>Sessioni</SectionTitle><p className="text-xs text-mute mt-1">L’accesso dura 8 ore. Se hai usato un computer non tuo, scollega tutti i dispositivi.</p></div>
        <button className="btn" onClick={out} disabled={busy}>{busy && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Esci da tutti i dispositivi</button>
      </div>
      <div className="card p-6 space-y-3 max-w-xl">
        <SectionTitle>Ultimi accessi</SectionTitle>
        <dl className="grid grid-cols-2 gap-y-1 text-xs"><dt className="text-mute">Account creato</dt><dd className="text-ink-2">{fmtTs(me.created_at)}</dd><dt className="text-mute">Ultimo accesso</dt><dd className="text-ink-2">{me.last_login_at ? fmtTs(me.last_login_at) : '—'}</dd></dl>
        <div className="border-t border-line pt-2 space-y-1">
          {(logins || []).length === 0 && <p className="text-xs text-mute">Nessun accesso registrato.</p>}
          {(logins || []).map((l, i) => <div key={i} className="flex gap-3 text-xs"><span className="font-mono text-[11px] text-mute w-32 shrink-0">{fmtTs(l.ts)}</span><span className={l.status === 'OK' ? 'text-ink-2' : 'text-red-700'}>{l.status === 'OK' ? 'Accesso riuscito' : 'Accesso negato'}</span></div>)}
        </div>
      </div>
    </div>
  )
}

function DataAndPlan({ me }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [del, setDel] = useState({ open: false, password: '', email: '' })
  const exportAll = async () => {
    setBusy(true); setError(null)
    try { download(await api.exportMe(), `quanto-dati-${new Date().toISOString().slice(0, 10)}.json`) } catch (e) { setError(e.message) } finally { setBusy(false) }
  }
  const remove = async (e) => {
    e.preventDefault(); setBusy(true); setError(null)
    try { await api.deleteMe(del.password, del.email); session.clear(); window.dispatchEvent(new Event('quanto-logout')) } catch (err) { setError(err.message) } finally { setBusy(false) }
  }
  return (
    <div className="space-y-6">
      <Credits />
      <div className="card p-6 space-y-3 max-w-xl">
        <div><SectionTitle icon={Download}>I tuoi dati</SectionTitle><p className="text-xs text-mute mt-1">Un unico file con i dati dello studio, i lavori con profilo e bilanci, i template di budget e le operazioni recenti. I documenti caricati si scaricano da ogni lavoro.</p></div>
        <button className="btn" onClick={exportAll} disabled={busy}>{busy && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Scarica tutti i dati (JSON)</button>
      </div>
      <Activity />
      {!me.is_owner && (
        <div className="card p-6 space-y-3 max-w-xl border-red-500/30">
          <div><SectionTitle icon={Trash2} className="text-red-700">Elimina l’account</SectionTitle><p className="text-xs text-mute mt-1">Cancella lo studio con tutti i lavori, i documenti, i risultati salvati e i template. Non si può annullare: scarica prima i dati.</p></div>
          {!del.open ? <button className="btn text-red-700" onClick={() => setDel({ ...del, open: true })}>Elimina l’account…</button> : (
            <form onSubmit={remove} className="space-y-3">
              <label className="block space-y-1"><span className="label">Password</span><input className="field" type="password" autoComplete="current-password" value={del.password} onChange={(e) => setDel({ ...del, password: e.target.value })} /></label>
              <label className="block space-y-1"><span className="label">Riscrivi la tua e-mail ({me.email})</span><input className="field" value={del.email} onChange={(e) => setDel({ ...del, email: e.target.value })} autoComplete="off" /></label>
              <div className="flex gap-2"><button className="btn-primary !bg-red-700" disabled={busy || !del.password || del.email.trim().toLowerCase() !== me.email}>{busy && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Elimina definitivamente</button><button type="button" className="btn" onClick={() => setDel({ open: false, password: '', email: '' })}>Annulla</button></div>
            </form>
          )}
        </div>
      )}
      {error && <Notice tone="err">{error}</Notice>}
    </div>
  )
}

export default function Profile({ user, isOwner, clients, clientId, onSelectClient, onClientsChanged, onChangePassword, onGoHQ, onGoAllocation, onUsePayslip, onUseBalance, onUseDraft }) {
  const [version, setVersion] = useState(0)          // si alza quando un documento cambia: il profilo azienda si ricarica
  const [section, setSection] = useState('lavori')
  const [me, setMe] = useState(null)
  const [logins, setLogins] = useState([])
  const bump = useCallback(() => { setVersion((v) => v + 1); onClientsChanged?.(clientId) }, [onClientsChanged, clientId])
  useEffect(() => { api.meProfile().then((r) => { setMe(r.profile); setLogins(r.logins) }).catch(() => {}) }, [])
  const active = (clients || []).find((c) => c.id === clientId)
  return (
    <div className="space-y-6">
      <Guide page="profilo" />
      <div className="flex items-center gap-4">
        <span className="w-12 h-12 rounded-full bg-tint-2 flex items-center justify-center text-base font-semibold text-ink-2 shrink-0">{(user.name || user.email).slice(0, 1).toUpperCase()}</span>
        <div className="min-w-0">
          <p className="text-base font-semibold text-ink truncate">{me?.studio_name || user.name}</p>
          <p className="text-xs text-mute truncate">{[me?.studio_name ? user.name : null, user.email, ROLE_LABEL[user.role] || user.role].filter(Boolean).join(' · ')}</p>
        </div>
      </div>
      <div className="flex gap-1 border-b border-line overflow-x-auto" role="tablist" aria-label="Sezioni del profilo">
        {SECTIONS.map(([id, label, Icon]) => (
          <button key={id} role="tab" aria-selected={section === id} onClick={() => setSection(id)}
            className={`inline-flex items-center gap-1.5 px-4 py-2.5 text-[13px] whitespace-nowrap -mb-px border-b-2 transition ${section === id ? 'border-ink text-ink font-medium' : 'border-transparent text-ink-2 hover:text-ink'}`}>
            <Icon className="w-4 h-4" />{label}
          </button>
        ))}
      </div>

      {section === 'lavori' && (
        <div className="space-y-6">
          <div className="card p-6"><ClientsPanel clients={clients} clientId={clientId} onSelect={onSelectClient} onChanged={onClientsChanged} /></div>
          {active && (
            <div className="space-y-6" key={active.id}>
              <div className="flex items-center gap-2"><Briefcase className="w-4 h-4 text-ink-2" /><h3 className="text-[15px] font-semibold text-ink">Lavoro attivo: {active.name}</h3></div>
              <ProfileSetup version={version} onChanged={bump} onGoAllocation={onGoAllocation}
                onGoDocuments={() => document.getElementById('documenti-azienda')?.scrollIntoView({ behavior: 'smooth', block: 'start' })} />
              <CompanyProfile version={version} />
              <div id="documenti-azienda" className="space-y-3 scroll-mt-20">
                <span className="text-sm font-medium text-ink">I documenti di {active.name}</span>
                <p className="text-xs text-mute -mt-1">Visura, bilanci, buste paga, F24, bozze di candidatura e ogni altro documento aziendale: restano dentro questo lavoro e li vede solo il tuo studio. Da visura e bilanci si compila il profilo qui sopra.</p>
                <Documents onUsePayslip={onUsePayslip} onUseBalance={onUseBalance} onUseDraft={onUseDraft} onProfileChanged={bump} refreshKey={version} />
              </div>
            </div>
          )}
        </div>
      )}
      {section === 'studio' && me && <StudioData me={me} onSaved={(u) => { setMe(u); try { const cur = session.user(); if (cur) session.set(session.token(), { ...cur, name: u.name }) } catch { /* sessione non disponibile */ } }} />}
      {section === 'sicurezza' && me && <Security me={me} logins={logins} />}
      {section === 'piano' && me && <DataAndPlan me={me} />}
      {isOwner && section === 'studio' && (
        <button onClick={onGoHQ} className="w-full max-w-3xl card p-5 flex items-center gap-4 text-left hover:border-line-strong transition">
          <Building2 className="w-5 h-5 text-ink-2 shrink-0" />
          <div className="min-w-0 flex-1"><p className="text-sm font-semibold text-ink">Quartier Generale</p><p className="text-xs text-mute">Riservato al titolare: memoria del sistema, bandi, tabelle ufficiali, utenti e database.</p></div>
        </button>
      )}
    </div>
  )
}
