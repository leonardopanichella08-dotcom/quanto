import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Check, ExternalLink, Linkedin, Loader2, Plus, Send, Trash2, Upload } from 'lucide-react'
import { api } from '../../lib/api'
import { fmtTs } from '../../lib/format'
import { BarList, Big, ChartTitle, LineChart, Pills } from './charts'

/* Marketing: come arrivano le persone al sito, cosa si pubblica su LinkedIn, quanto rendono le campagne.
   Quattro viste: Panoramica · Post · Campagne · Account LinkedIn. */
const VIEWS = [['overview', 'Panoramica'], ['posts', 'Post'], ['campaigns', 'Campagne'], ['accounts', 'Account LinkedIn']]
const STATE = { BOZZA: 'Bozza', DA_APPROVARE: 'Da approvare', APPROVATO: 'Approvato', PROGRAMMATO: 'Programmato', PUBBLICATO: 'Pubblicato', ERRORE: 'Errore' }
const CSTATE = { BOZZA: 'Bozza', ATTIVA: 'Attiva', IN_PAUSA: 'In pausa', CONCLUSA: 'Conclusa' }
const eur = (n) => (n == null ? '—' : `${Number(n).toLocaleString('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`)
const num = (n) => (n == null ? '—' : Number(n).toLocaleString('it-IT'))
const Err = ({ e }) => (e ? <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-700 text-xs">{e}</div> : null)

function Overview({ days, setDays }) {
  const [d, setD] = useState(null)
  const [e, setE] = useState(null)
  useEffect(() => { setD(null); api.mkOverview(days).then(setD).catch((x) => setE(x.message)) }, [days])
  if (!d) return e ? <Err e={e} /> : <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Caricamento…</p>
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between gap-3"><Pills items={[[7, '7 giorni'], [30, '30 giorni'], [90, '90 giorni'], [365, '12 mesi']]} value={days} onChange={setDays} />
        {d.just_published?.published > 0 && <span className="text-xs">Pubblicati ora {d.just_published.published} post programmati</span>}</div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        <Big label="Visitatori del sito" value={num(d.visitors)} note={`${num(d.cta)} clic su «Richiedi accesso»`} />
        <Big label="Richieste di accesso" value={num(d.signups)} note={d.conversion_pct != null ? `${d.conversion_pct}% dei visitatori` : 'nel periodo'} />
        <Big label="Impressioni dei post" value={num(d.post_totals.impressions)} note={`${num(d.post_totals.reactions)} reazioni · ${num(d.post_totals.comments)} commenti`} />
        <Big label="Spesa in campagne" value={eur(d.ads.spend_eur)} note={`${num(d.ads.leads)} contatti · ${num(d.ads.clicks)} clic`} />
      </div>
      <div className="grid lg:grid-cols-[2fr_1fr] gap-6">
        <div className="card p-5"><ChartTitle>Visitatori e azioni sul sito</ChartTitle><LineChart points={d.visits_by_day.map((v) => ({ x: v.day, a: v.visitors, b: v.actions }))} labels={['visitatori', 'clic su richiedi accesso']} /></div>
        <div className="card p-5"><ChartTitle>Da dove arrivano</ChartTitle><BarList rows={d.sources.map((s) => ({ label: s.fonte, value: s.visitors }))} empty="Nessuna visita registrata ancora." /></div>
      </div>
      <div className="grid lg:grid-cols-2 gap-6">
        <div className="card p-5"><ChartTitle>Post per stato</ChartTitle><BarList rows={Object.entries(STATE).map(([k, l]) => ({ label: l, value: d.posts[k] || 0, alert: k === 'DA_APPROVARE' && d.posts[k] > 0 }))} /></div>
        <div className="card p-5"><ChartTitle>Follower</ChartTitle>
          {d.followers.length ? <BarList rows={d.followers.map((f) => ({ label: `${f.name} · ${f.day}`, value: f.followers }))} /> : <p className="text-xs text-mute">Nessun dato: aggiungilo in «Account LinkedIn».</p>}</div>
      </div>
      {!d.linkedin.ready && <p className="text-xs text-amber-800 bg-amber-500/10 border border-amber-500/30 rounded-xl p-3">LinkedIn non è ancora collegabile: mancano {d.linkedin.missing.join(' e ')} nelle variabili di Vercel. Le visite al sito si registrano comunque.</p>}
    </div>
  )
}

function PostEditor({ post, accounts, campaigns, onSaved, onCancel }) {
  const [f, setF] = useState({ text: post?.text || '', link: post?.link || '', account_id: post?.account_id || accounts[0]?.id || null, campaign_id: post?.campaign_id || null, scheduled_at: post?.scheduled_at?.slice(0, 16) || '' })
  const [busy, setBusy] = useState(false)
  const [e, setE] = useState(null)
  const save = async () => {
    setBusy(true); setE(null)
    try { await api.mkSavePost({ ...f, link: f.link || null, scheduled_at: f.scheduled_at ? new Date(f.scheduled_at).toISOString() : null, campaign_id: f.campaign_id || null }, post?.id); onSaved() } catch (x) { setE(x.message) } finally { setBusy(false) }
  }
  return (
    <div className="card p-5 space-y-3">
      <textarea className="field min-h-[140px] text-sm" maxLength={3000} placeholder="Testo del post. #hashtag diventano veri hashtag." value={f.text} onChange={(e) => setF({ ...f, text: e.target.value })} />
      <p className="text-[11px] text-mute text-right">{f.text.length}/3000</p>
      <div className="grid md:grid-cols-4 gap-3 text-xs">
        <label className="space-y-1"><span className="label">Pubblica come</span><select className="field" value={f.account_id || ''} onChange={(e) => setF({ ...f, account_id: Number(e.target.value) || null })}>{accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}</select></label>
        <label className="space-y-1"><span className="label">Campagna (facoltativa)</span><select className="field" value={f.campaign_id || ''} onChange={(e) => setF({ ...f, campaign_id: Number(e.target.value) || null })}><option value="">Nessuna</option>{campaigns.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
        <label className="space-y-1"><span className="label">Link (facoltativo)</span><input className="field" placeholder="https://" value={f.link} onChange={(e) => setF({ ...f, link: e.target.value })} /></label>
        <label className="space-y-1"><span className="label">Programma per (facoltativo)</span><input className="field" type="datetime-local" value={f.scheduled_at} onChange={(e) => setF({ ...f, scheduled_at: e.target.value })} /></label>
      </div>
      <Err e={e} />
      <div className="flex gap-2"><button className="btn-primary" disabled={busy || !f.text.trim()} onClick={save}>{busy && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Salva bozza</button><button className="btn" onClick={onCancel}>Annulla</button></div>
      {post?.approved_by && <p className="text-[11px] text-amber-700">Salvando le modifiche il post torna in bozza e va riapprovato.</p>}
    </div>
  )
}

function Posts() {
  const [posts, setPosts] = useState(null)
  const [accounts, setAccounts] = useState([])
  const [campaigns, setCampaigns] = useState([])
  const [edit, setEdit] = useState(null)
  const [busy, setBusy] = useState(null)
  const [e, setE] = useState(null)
  const [stats, setStats] = useState({})
  const [filter, setFilter] = useState('all')
  const load = useCallback(async () => {
    try { const [p, a, c] = await Promise.all([api.mkPosts(), api.mkAccounts(), api.mkCampaigns()]); setPosts(p); setAccounts(a); setCampaigns(c) } catch (x) { setE(x.message) }
  }, [])
  useEffect(() => { load() }, [load])
  const act = async (id, fn) => { setBusy(id); setE(null); try { await fn(); await load() } catch (x) { setE(x.message); await load() } finally { setBusy(null) } }
  const shown = useMemo(() => (posts || []).filter((p) => filter === 'all' || p.status === filter), [posts, filter])
  if (!posts) return e ? <Err e={e} /> : <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Caricamento…</p>
  const counts = posts.reduce((m, p) => ({ ...m, [p.status]: (m[p.status] || 0) + 1 }), {})
  return (
    <div className="space-y-5">
      <p className="text-xs text-ink-2">Il percorso di un post: <b>bozza</b> → <b>da approvare</b> → <b>approvato</b> (o <b>programmato</b> se ha una data) → <b>pubblicato</b>. Nessun post parte senza la tua approvazione; se lo modifichi dopo, va riapprovato.</p>
      <div className="flex flex-wrap items-center gap-3">
        <Pills items={[['all', `Tutti (${posts.length})`], ...Object.entries(STATE).filter(([k]) => counts[k]).map(([k, l]) => [k, `${l} (${counts[k]})`])]} value={filter} onChange={setFilter} />
        {!edit && <button className="btn-primary ml-auto" onClick={() => setEdit('new')}><Plus className="w-3.5 h-3.5" />Nuovo post</button>}
      </div>
      {edit && <PostEditor post={edit === 'new' ? null : edit} accounts={accounts} campaigns={campaigns} onSaved={() => { setEdit(null); load() }} onCancel={() => setEdit(null)} />}
      <Err e={e} />
      {shown.length === 0 && <p className="text-sm text-ink-2">Nessun post. Scrivine uno con «Nuovo post».</p>}
      <ul className="space-y-3">
        {shown.map((p) => (
          <li key={p.id} className="card p-4 space-y-3">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
              <span className={`px-2 py-0.5 rounded-full font-medium ${p.status === 'DA_APPROVARE' ? 'text-ink' : p.status === 'PUBBLICATO' ? 'bg-brand text-white' : p.status === 'ERRORE' ? 'bg-red-500/10 text-red-700' : 'bg-black/[0.06] text-ink-2'}`} style={p.status === 'DA_APPROVARE' ? { background: '#F1E21B' } : undefined}>{STATE[p.status]}</span>
              <span className="text-ink-2">{p.account_name || 'nessun account'}</span>
              {p.campaign_name && <span className="text-ink-2">· {p.campaign_name}</span>}
              {p.scheduled_at && p.status !== 'PUBBLICATO' && <span className="text-ink-2">· programmato {fmtTs(p.scheduled_at)}</span>}
              {p.published_at && <span className="text-ink-2">· pubblicato {fmtTs(p.published_at)}</span>}
              {p.approved_by && <span className="text-mute">· approvato da {p.approved_by.replace('user:', '')}</span>}
            </div>
            <p className="text-sm whitespace-pre-wrap leading-relaxed">{p.text}</p>
            {p.error && <p className="text-xs text-red-700">{p.error}</p>}
            {p.status === 'PUBBLICATO' && <p className="text-xs text-ink-2 font-mono">{num(p.impressions)} impressioni · {num(p.reactions)} reazioni · {num(p.comments)} commenti · {num(p.clicks)} clic</p>}
            <div className="flex flex-wrap items-center gap-2">
              {['BOZZA', 'ERRORE'].includes(p.status) && <button className="btn" disabled={busy === p.id} onClick={() => act(p.id, () => api.mkPostAction(p.id, 'submit'))}>Invia in approvazione</button>}
              {['BOZZA', 'DA_APPROVARE'].includes(p.status) && <button className="btn-primary" disabled={busy === p.id} onClick={() => act(p.id, () => api.mkPostAction(p.id, 'approve'))}><Check className="w-3.5 h-3.5" />Approva</button>}
              {['APPROVATO', 'PROGRAMMATO'].includes(p.status) && <button className="btn-primary" disabled={busy === p.id} onClick={() => act(p.id, () => api.mkPostAction(p.id, 'publish'))}>{busy === p.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}Pubblica ora su LinkedIn</button>}
              {['APPROVATO', 'PROGRAMMATO'].includes(p.status) && <button className="btn" disabled={busy === p.id} onClick={() => act(p.id, () => api.mkPostAction(p.id, 'mark_published'))}>L’ho pubblicato a mano</button>}
              {p.status !== 'PUBBLICATO' && <button className="btn" onClick={() => setEdit(p)}>Modifica</button>}
              {['DA_APPROVARE', 'APPROVATO', 'PROGRAMMATO'].includes(p.status) && <button className="btn" disabled={busy === p.id} onClick={() => act(p.id, () => api.mkPostAction(p.id, 'back'))}>Torna in bozza</button>}
              {p.status !== 'PUBBLICATO' && <button className="btn ml-auto" aria-label="Elimina il post" disabled={busy === p.id} onClick={() => { if (window.confirm('Eliminare questo post?')) act(p.id, () => api.mkDeletePost(p.id)) }}><Trash2 className="w-3.5 h-3.5" /></button>}
              {p.urn && <a className="btn ml-auto" href={`https://www.linkedin.com/feed/update/${p.urn}`} target="_blank" rel="noreferrer"><ExternalLink className="w-3.5 h-3.5" />Apri su LinkedIn</a>}
            </div>
            {p.status === 'PUBBLICATO' && (
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="text-mute">Aggiorna i numeri:</span>
                {['impressions', 'reactions', 'comments', 'clicks'].map((k) => <input key={k} className="field !w-28 !py-1" inputMode="numeric" placeholder={{ impressions: 'impressioni', reactions: 'reazioni', comments: 'commenti', clicks: 'clic' }[k]}
                  value={stats[p.id]?.[k] || ''} onChange={(ev) => setStats({ ...stats, [p.id]: { ...stats[p.id], [k]: ev.target.value } })} />)}
                <button className="btn !py-1" disabled={!stats[p.id] || busy === p.id} onClick={() => act(p.id, async () => { await api.mkPostMetrics(p.id, stats[p.id]); setStats({ ...stats, [p.id]: undefined }) })}>Salva</button>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

function Campaigns() {
  const [list, setList] = useState(null)
  const [form, setForm] = useState(null)
  const [day, setDay] = useState({})
  const [busy, setBusy] = useState(null)
  const [e, setE] = useState(null)
  const [msg, setMsg] = useState(null)
  const load = useCallback(() => api.mkCampaigns().then(setList).catch((x) => setE(x.message)), [])
  useEffect(() => { load() }, [load])
  const act = async (id, fn) => { setBusy(id); setE(null); setMsg(null); try { await fn(); await load() } catch (x) { setE(x.message) } finally { setBusy(null) } }
  const upload = (id) => (ev) => {
    const file = ev.target.files?.[0]
    if (!file) return
    const r = new FileReader()
    r.onload = () => act(id, async () => { const out = await api.mkCampaignCsv(id, String(r.result)); setMsg(`Importate ${out.imported} righe${out.skipped ? `, ${out.skipped} saltate (data non leggibile)` : ''}.`) })
    r.readAsText(file)
    ev.target.value = ''
  }
  if (!list) return e ? <Err e={e} /> : <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Caricamento…</p>
  const set = (k) => (ev) => setForm({ ...form, [k]: ev.target.value })
  return (
    <div className="space-y-5">
      <p className="text-xs text-ink-2">Le statistiche delle campagne a pagamento arrivano in automatico solo quando LinkedIn concede l’accesso «Advertising API». Fino ad allora: inserisci i numeri del giorno oppure carica il CSV esportato da Campaign Manager. Lo storico non si sovrascrive.</p>
      <div className="flex"><button className="btn-primary ml-auto" onClick={() => setForm({ name: '', objective: '', budget_eur: '', start_day: '', end_day: '', status: 'BOZZA', notes: '' })}><Plus className="w-3.5 h-3.5" />Nuova campagna</button></div>
      {form && (
        <div className="card p-5 space-y-3">
          <div className="grid md:grid-cols-3 gap-3 text-xs">
            <label className="space-y-1"><span className="label">Nome</span><input className="field" value={form.name} onChange={set('name')} /></label>
            <label className="space-y-1"><span className="label">Obiettivo</span><input className="field" placeholder="es. richieste di accesso" value={form.objective} onChange={set('objective')} /></label>
            <label className="space-y-1"><span className="label">Budget (€)</span><input className="field" inputMode="decimal" value={form.budget_eur ?? ''} onChange={set('budget_eur')} /></label>
            <label className="space-y-1"><span className="label">Inizio</span><input className="field" type="date" value={form.start_day || ''} onChange={set('start_day')} /></label>
            <label className="space-y-1"><span className="label">Fine</span><input className="field" type="date" value={form.end_day || ''} onChange={set('end_day')} /></label>
            <label className="space-y-1"><span className="label">Stato</span><select className="field" value={form.status} onChange={set('status')}>{Object.entries(CSTATE).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select></label>
          </div>
          <div className="flex gap-2"><button className="btn-primary" disabled={!form.name || busy === 'form'} onClick={() => act('form', async () => { await api.mkSaveCampaign({ ...form, budget_eur: form.budget_eur === '' ? null : String(form.budget_eur) }, form.id); setForm(null) })}>Salva</button><button className="btn" onClick={() => setForm(null)}>Annulla</button></div>
        </div>
      )}
      <Err e={e} />{msg && <p className="text-xs">{msg}</p>}
      {list.length === 0 && !form && <p className="text-sm text-ink-2">Nessuna campagna. Creane una con «Nuova campagna».</p>}
      {list.length > 0 && <div className="card p-5"><ChartTitle>Spesa per campagna</ChartTitle><BarList rows={list.map((c) => ({ label: c.name, value: c.spend_eur, display: eur(c.spend_eur) }))} /></div>}
      <ul className="space-y-3">
        {list.map((c) => (
          <li key={c.id} className="card p-4 space-y-3">
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <span className="font-semibold text-sm">{c.name}</span><span className="text-xs text-ink-2">{CSTATE[c.status]}{c.objective ? ` · ${c.objective}` : ''}{c.start_day ? ` · dal ${c.start_day}` : ''}{c.end_day ? ` al ${c.end_day}` : ''}</span>
              <button className="btn !py-1 ml-auto" onClick={() => setForm({ ...c, budget_eur: c.budget_eur ?? '' })}>Modifica</button>
            </div>
            <div className="grid grid-cols-3 md:grid-cols-6 gap-4 text-xs">
              {[['Budget', eur(c.budget_eur)], ['Spesa', eur(c.spend_eur)], ['Impressioni', num(c.impressions)], ['Clic', `${num(c.clicks)}${c.ctr_pct != null ? ` · ${c.ctr_pct}%` : ''}`], ['Costo per clic', eur(c.cpc_eur)], ['Contatti', `${num(c.leads)}${c.cpl_eur != null ? ` · ${eur(c.cpl_eur)} l’uno` : ''}`]].map(([l, v]) =>
                <div key={l}><span className="label block">{l}</span><span className="font-mono">{v}</span></div>)}
            </div>
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <input className="field !w-36 !py-1" type="date" value={day[c.id]?.day || ''} onChange={(ev) => setDay({ ...day, [c.id]: { ...day[c.id], day: ev.target.value } })} />
              {[['impressions', 'impressioni'], ['clicks', 'clic'], ['spend_eur', 'spesa €'], ['leads', 'contatti']].map(([k, ph]) =>
                <input key={k} className="field !w-24 !py-1" inputMode="decimal" placeholder={ph} value={day[c.id]?.[k] || ''} onChange={(ev) => setDay({ ...day, [c.id]: { ...day[c.id], [k]: ev.target.value } })} />)}
              <button className="btn !py-1" disabled={!day[c.id]?.day || busy === c.id} onClick={() => act(c.id, async () => { await api.mkCampaignDay(c.id, day[c.id]); setDay({ ...day, [c.id]: undefined }) })}>Aggiungi il giorno</button>
              <label className="btn !py-1 cursor-pointer ml-auto"><Upload className="w-3.5 h-3.5" />Importa CSV<input type="file" accept=".csv,text/csv" className="hidden" onChange={upload(c.id)} /></label>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

function Accounts() {
  const [list, setList] = useState(null)
  const [cfg, setCfg] = useState(null)
  const [f, setF] = useState({})
  const [busy, setBusy] = useState(null)
  const [e, setE] = useState(null)
  const result = new URLSearchParams(window.location.search).get('linkedin')
  const load = useCallback(async () => { try { const [a, o] = await Promise.all([api.mkAccounts(), api.mkOverview(30)]); setList(a); setCfg(o.linkedin) } catch (x) { setE(x.message) } }, [])
  useEffect(() => { load() }, [load])
  const connect = async (id) => { setBusy(id); setE(null); try { window.location.href = (await api.mkConnect(id)).url } catch (x) { setE(x.message); setBusy(null) } }
  if (!list) return e ? <Err e={e} /> : <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Caricamento…</p>
  return (
    <div className="space-y-5">
      {result === 'collegato' && <p className="text-sm">LinkedIn collegato.</p>}
      {result === 'errore' && <Err e="Il collegamento con LinkedIn non è riuscito: riprova." />}
      {cfg && !cfg.ready && (
        <div className="rounded-2xl border border-amber-500/40 bg-amber-500/10 p-4 text-xs text-amber-900 space-y-1.5">
          <p className="font-semibold">Per collegare LinkedIn manca la configurazione su Vercel: {cfg.missing.join(' e ')}.</p>
          <p>Nell’app LinkedIn per sviluppatori aggiungi questo indirizzo di ritorno: <code className="font-mono">{cfg.redirect_uri}</code></p>
        </div>
      )}
      <Err e={e} />
      <ul className="space-y-3">
        {list.map((a) => (
          <li key={a.id} className="card p-4 space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <Linkedin className="w-4 h-4" /><span className="font-semibold text-sm">{a.name}</span><span className="text-xs text-ink-2">{a.kind === 'page' ? 'pagina aziendale' : 'profilo personale'}</span>
              <span className={`text-xs px-2 py-0.5 rounded-full ${a.status === 'collegato' ? 'bg-brand text-white' : 'bg-black/[0.06] text-ink-2'}`}>{a.status}</span>
              {a.connected_at && <span className="text-[11px] text-mute">dal {fmtTs(a.connected_at)}{a.expires_at ? ` · scade ${fmtTs(a.expires_at)}` : ''}</span>}
              <button className="btn-primary ml-auto" disabled={!cfg?.ready || busy === a.id} onClick={() => connect(a.id)}>{busy === a.id && <Loader2 className="w-3.5 h-3.5 animate-spin" />}{a.status === 'collegato' ? 'Ricollega' : 'Collega con LinkedIn'}</button>
            </div>
            {a.last_error && <p className="text-xs text-red-700">{a.last_error}</p>}
            {a.kind === 'page' && <p className="text-[11px] text-mute">Per pubblicare a nome della pagina e leggere le sue statistiche LinkedIn deve concedere la «Community Management API». Finché non c’è, i post si pubblicano dal profilo.</p>}
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="text-mute">Follower di oggi:</span>
              <input className="field !w-28 !py-1" inputMode="numeric" placeholder="numero" value={f[a.id] || ''} onChange={(ev) => setF({ ...f, [a.id]: ev.target.value })} />
              <button className="btn !py-1" disabled={!f[a.id] || busy === `f${a.id}`} onClick={async () => { setBusy(`f${a.id}`); try { await api.mkFollowers(a.id, { followers: f[a.id] }); setF({ ...f, [a.id]: '' }) } catch (x) { setE(x.message) } finally { setBusy(null) } }}>Salva</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function Marketing({ view, setView }) {
  const [days, setDays] = useState(30)
  return (
    <div className="space-y-6">
      <Pills items={VIEWS} value={view} onChange={setView} />
      {view === 'overview' && <Overview days={days} setDays={setDays} />}
      {view === 'posts' && <Posts />}
      {view === 'campaigns' && <Campaigns />}
      {view === 'accounts' && <Accounts />}
    </div>
  )
}
