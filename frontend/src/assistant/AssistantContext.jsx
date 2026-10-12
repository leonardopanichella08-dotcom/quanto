import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { AlertTriangle, ArrowUp, Check, Loader2, Minus, Sparkles, X } from 'lucide-react'
import { TASKS, TASK_ORDER } from './tasks'

/** L'assistente guidato: una chat. Si scrive cosa si vuole fare (o si sceglie un suggerimento) e l'assistente prende in mano i passaggi in cui l'utente dovrebbe
 *  inserire dati o muoversi nell'app: li esegue lui (cambia pagina, salva, calcola) e, quando gli serve un valore, lo chiede nella chat spiegando in parole semplici
 *  cos'è, cosa scrivere, perché serve e dove si trova. Non è un modello linguistico: capisce le richieste con parole chiave e non inventa mai un dato.
 *  Mentre lavora, l'app resta visibile in una scheda ridotta a sinistra e si vede cosa succede. */
class Cancelled extends Error {}
const Ctx = createContext(null)
export const useAssistant = () => useContext(Ctx) || { start: () => {}, openMenu: () => {}, open: false, busy: false }

const SUGGEST = {
  allocazione: 'Calcola il potenziale massimo',
  budget: 'Prepara la bozza di budget',
  deminimis: 'Dichiara gli aiuti già ricevuti',
  profilo: 'Completa i dati dell’azienda',
}
// parole chiave (senza accenti) per capire cosa si chiede; vince l'attività con più corrispondenze
const INTENTS = {
  allocazione: ['potenziale', 'allocazion', 'massimo', 'bandi adatti', 'quanto copr', 'quanto valgono', 'piano', 'stima', 'quali bandi', 'calcola'],
  budget: ['budget', 'bozza', 'persone', 'personale', 'candidatura', 'spese del progetto', 'controlla'],
  deminimis: ['de minimis', 'minimis', 'aiuti', 'contributi ricevuti', 'plafond', 'tetto'],
  profilo: ['profilo', 'dati', 'visura', 'bilancio', 'azienda', 'mancano', 'partita iva', 'ateco', 'completa'],
}
const plain = (s) => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
function interpret(text) {
  const t = plain(text)
  if (/\b(annulla|interrompi|stop|basta|ferma)\b/.test(t)) return { stop: true }
  let best = null
  let bestScore = 0
  for (const [id, words] of Object.entries(INTENTS)) {
    const score = words.reduce((n, w) => n + (t.includes(w) ? 1 : 0), 0)
    if (score > bestScore) { best = id; bestScore = score }
  }
  return best ? { task: best } : { task: null }
}

let uid = 0
const mid = () => `m${(uid += 1)}`
const GREETING = 'Ciao, sono l’assistente di QUANTO. Faccio io al posto tuo i passaggi in cui servono dati: scrivimi cosa vuoi fare oppure scegli un suggerimento. Quando mi serve un valore te lo chiedo qui, spiegandoti cos’è e dove lo trovi.'

export function AssistantProvider({ bridge, enabled, children }) {
  const [chat, setChat] = useState(null)               // null = chiuso; altrimenti l'elenco dei messaggi
  const token = useRef(0)
  const waiting = useRef(null)

  const addMsg = useCallback((m) => setChat((c) => (c ? [...c, { id: mid(), ...m }] : c)), [])
  const updRun = useCallback((my, fn) => setChat((c) => (c ? c.map((m) => (m.type === 'run' && m.token === my ? fn(m) : m)) : c)), [])

  const makeApi = (my) => {
    const alive = () => { if (my !== token.current) throw new Cancelled() }
    const patch = (id, p) => updRun(my, (r) => ({ ...r, steps: r.steps.map((s) => (s.id === id ? { ...s, ...p } : s)) }))
    return {
      bridge: () => bridge.current,
      begin: (id, detail = null) => { alive(); patch(id, { status: 'doing', detail }); updRun(my, (r) => ({ ...r, busy: true, prompt: null })) },
      done: (id, detail = null) => { alive(); patch(id, { status: 'done', detail }) },
      skip: (id, detail = null) => { alive(); patch(id, { status: 'skipped', detail }) },
      fail: (id, detail = null) => { alive(); patch(id, { status: 'failed', detail }) },
      pause: (ms = 700) => new Promise((res) => setTimeout(res, ms)).then(alive),
      ask: (id, prompt) => new Promise((resolve) => {
        alive()
        patch(id, { status: 'asking' })
        updRun(my, (r) => ({ ...r, busy: false, prompt: { ...prompt, stepId: id, nonce: Math.random() } }))
        waiting.current = { my, resolve, prompt }
      }),
      /** aspetta un evento dell'app (es. il risultato dell'Allocazione); null se non arriva entro il tempo */
      waitFor: (name, ms = 90000) => new Promise((resolve) => {
        let done = false
        const end = (v) => { if (done) return; done = true; window.removeEventListener(name, on); clearTimeout(t); resolve(v) }
        const on = (e) => end(e.detail ?? true)
        const t = setTimeout(() => end(null), ms)
        window.addEventListener(name, on)
      }).then((v) => { alive(); return v }),
      finish: (summary) => { alive(); updRun(my, (r) => ({ ...r, finished: true, busy: false, prompt: null, summary })) },
    }
  }

  const open = !!chat && enabled
  const start = useCallback((taskId, params = {}) => {
    const t = TASKS[taskId]
    if (!t) return
    const my = ++token.current
    waiting.current = null
    const run = { id: mid(), type: 'run', token: my, task: taskId, title: t.title, steps: t.steps.map((s) => ({ ...s, status: 'todo' })), prompt: null, answers: [], busy: true, finished: false, summary: null, error: null, params }
    setChat((c) => [...(c || [{ id: mid(), role: 'assistant', type: 'text', text: GREETING }]),
      { id: mid(), role: 'user', type: 'text', text: params.userText || SUGGEST[taskId] || t.title },
      { id: mid(), role: 'assistant', type: 'text', text: `Va bene: ${t.title.charAt(0).toLowerCase()}${t.title.slice(1)}. Ecco i passaggi.` }, run])
    const a = makeApi(my)
    Promise.resolve().then(() => t.run(a, params)).catch((e) => {
      if (e instanceof Cancelled) return
      updRun(my, (r) => ({ ...r, error: e?.message || String(e), busy: false, prompt: null }))
    })
  }, [])                                                   // eslint-disable-line react-hooks/exhaustive-deps

  const cancelRun = useCallback(() => {                    // ferma l'attività ma lascia aperta la chat: riprende l'utente
    token.current += 1
    waiting.current = null
    setChat((c) => (c ? c.map((m) => (m.type === 'run' && !m.finished ? { ...m, busy: false, prompt: null, cancelled: true } : m)).concat([{ id: mid(), role: 'assistant', type: 'text', text: 'Mi fermo qui. Da questo punto riprendi tu: quello che avevo già fatto resta salvato.' }]) : c))
  }, [])
  const close = useCallback(() => { token.current += 1; waiting.current = null; setChat(null) }, [])
  const openMenu = useCallback(() => { token.current += 1; waiting.current = null; setChat([{ id: mid(), role: 'assistant', type: 'text', text: GREETING }]) }, [])

  const submit = (values) => {
    const w = waiting.current
    if (!w) return
    waiting.current = null
    const fields = w.prompt.fields || []
    const said = values == null ? 'Salto questo passaggio' : fields.length === 0 ? 'Sì' : fields.map((f) => {
      const v = values[f.key]
      if (v === undefined) return null
      const shown = f.kind === 'select' ? (f.options.find((o) => o.value === v)?.label ?? v) : f.kind === 'yesno' ? (v ? 'Sì' : 'No') : f.kind === 'money' ? `${Number(v).toLocaleString('it-IT')} €` : f.kind === 'percent' ? `${v}%` : String(v)
      return `${f.label}: ${shown}`
    }).filter(Boolean).join(' · ') || 'Lascio vuoto'
    updRun(w.my, (r) => ({ ...r, prompt: null, busy: true, answers: [...r.answers, said] }))
    w.resolve(values)
  }

  // un messaggio scritto dall'utente: si capisce con le parole chiave e si parte (o si risponde)
  const say = useCallback((text) => {
    const t = String(text || '').trim()
    if (!t) return
    const intent = interpret(t)
    const running = (chat || []).some((m) => m.type === 'run' && !m.finished && !m.cancelled && !m.error)
    if (intent.stop) {
      if (running) cancelRun()
      else addMsg({ role: 'assistant', type: 'text', text: 'Non c’è nulla in corso. Dimmi pure cosa vuoi fare.' })
      return
    }
    if (running) {
      addMsg({ role: 'user', type: 'text', text: t })
      addMsg({ role: 'assistant', type: 'text', text: waiting.current ? 'Ho bisogno dei dati nel riquadro qui sopra: compilali, oppure scrivi «annulla» per fermarmi.' : 'Sto lavorando: appena finisco ti dico. Scrivi «annulla» se vuoi fermarmi.' })
      return
    }
    if (intent.task) { start(intent.task, { userText: t }); return }
    addMsg({ role: 'user', type: 'text', text: t })
    addMsg({ role: 'assistant', type: 'text', text: 'Non ho capito cosa vuoi che faccia. Posso fare solo queste cose: scegline una dai suggerimenti oppure descrivila con parole come «budget», «potenziale massimo», «aiuti ricevuti» o «dati dell’azienda».' })
  }, [chat, start, addMsg, cancelRun])

  useEffect(() => {
    const on = (e) => start(e.detail?.task, e.detail || {})
    window.addEventListener('quanto-assistant', on)
    const off = () => close()
    window.addEventListener('quanto-logout', off)
    return () => { window.removeEventListener('quanto-assistant', on); window.removeEventListener('quanto-logout', off) }
  }, [start, close])
  useEffect(() => { if (!enabled) close() }, [enabled, close])
  useEffect(() => {
    if (!open) return undefined
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = prev }
  }, [open])

  const lastRun = useMemo(() => [...(chat || [])].reverse().find((m) => m.type === 'run') || null, [chat])
  const busy = !!lastRun && lastRun.busy && !lastRun.finished
  const value = useMemo(() => ({ start, stop: close, openMenu, open, busy }), [start, close, openMenu, open, busy])

  // La struttura è la stessa sia aperta sia chiusa (cambiano solo le classi): l'app non si smonta, quindi non perde nulla di ciò che l'utente aveva fatto.
  return (
    <Ctx.Provider value={value}>
      <div className={open ? 'asst-stage' : 'contents'}>
        <section className={open ? 'asst-left' : 'contents'}>
          <div className={open ? 'asst-card' : 'contents'}>
            <div id="app-scroll" className={open ? 'asst-scroll' : 'contents'}>{children}</div>
            {open && busy && <div className="absolute inset-0 z-40 cursor-progress" aria-hidden="true" />}
          </div>
          {open && <Pills lastRun={lastRun} busy={busy} onStop={cancelRun} onClose={close} />}
        </section>
        {open && <Panel chat={chat} lastRun={lastRun} busy={busy} onClose={close} onSubmit={submit} onSay={say} onSuggest={(id) => start(id, {})} />}
      </div>
    </Ctx.Provider>
  )
}

// ------------------------------------------------------------------------------------------------ pillole sotto lo schermo
function Pills({ lastRun, busy, onStop, onClose }) {
  const r = lastRun
  const total = r?.steps.length || 0
  const doneN = r ? r.steps.filter((s) => s.status === 'done' || s.status === 'skipped').length : 0
  const current = r?.steps.find((s) => s.status === 'doing' || s.status === 'asking')
  let label = 'Pronto: scrivimi cosa vuoi fare'
  let tone = 'idle'
  if (r && r.cancelled) { label = 'Interrotto: riprendi tu'; tone = 'idle' }
  else if (r && r.error) { label = 'Mi sono fermato: guarda la chat'; tone = 'error' }
  else if (r && r.finished) { label = `Fatto · ${r.title}`; tone = 'done' }
  else if (r && r.prompt) { label = 'Aspetto un tuo dato nella chat'; tone = 'ask' }
  else if (r && busy) { label = current ? current.title : 'Lavoro…'; tone = 'busy' }
  const active = r && !r.finished && !r.cancelled && !r.error
  return (
    <div className="asst-pillrow">
      <div className="asst-pill asst-pill-wide" data-tone={tone}>
        {tone === 'busy' ? <Loader2 className="w-3.5 h-3.5 animate-spin shrink-0" /> : tone === 'done' ? <Check className="w-3.5 h-3.5 shrink-0" /> : tone === 'error' ? <AlertTriangle className="w-3.5 h-3.5 shrink-0" /> : <i className="asst-dot" />}
        <span className="truncate">{label}</span>
        {r && active && total > 0 && <span className="asst-count">{Math.min(doneN + 1, total)}/{total}</span>}
        {r && active && total > 0 && <span className="asst-bar" style={{ width: `${(doneN / total) * 100}%` }} />}
      </div>
      {active ? <button className="asst-pill asst-pill-btn" onClick={onStop}>Interrompi</button> : <button className="asst-pill asst-pill-btn" onClick={onClose}>Chiudi</button>}
    </div>
  )
}

// ------------------------------------------------------------------------------------------------ pannello a destra: la chat
function Panel({ chat, lastRun, busy, onClose, onSubmit, onSay, onSuggest }) {
  const [text, setText] = useState('')
  const endRef = useRef(null)
  const scroller = useRef(null)
  useEffect(() => { scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: 'smooth' }) }, [chat, lastRun?.prompt])
  const idle = !busy && !lastRun?.prompt
  const send = (e) => { e?.preventDefault(); if (!text.trim()) return; onSay(text); setText('') }
  return (
    <aside className="asst-panel" aria-label="Assistente QUANTO">
      <header className="asst-head">
        <span className="asst-avatar"><Sparkles className="w-4 h-4" /></span>
        <div className="min-w-0 flex-1"><p className="text-[14px] font-semibold leading-tight">Assistente</p><p className="text-[11px] text-ink-2/80 truncate">{busy ? 'Sto lavorando per te' : lastRun?.prompt ? 'Ho bisogno di un dato' : 'Pronto ad aiutarti'}</p></div>
        <button className="asst-icon" onClick={onClose} aria-label="Chiudi l’assistente" title="Chiudi"><X className="w-4 h-4" /></button>
      </header>
      <div ref={scroller} className="asst-chat">
        {chat.map((m) => (m.type === 'run'
          ? <RunCard key={m.id} run={m} onSubmit={onSubmit} onRetry={() => onSuggest(m.task)} />
          : <Bubble key={m.id} role={m.role}>{m.text}</Bubble>))}
        <div ref={endRef} />
      </div>
      <div className="asst-composer">
        <p className="asst-note">Non invento mai nessun dato: uso solo ciò che scrivi tu o che è già nel profilo.</p>
        {idle && (
          <div className="asst-suggest" aria-label="Suggerimenti">
            {TASK_ORDER.map((id) => <button key={id} type="button" className="asst-chip" onClick={() => onSuggest(id)}>{SUGGEST[id]}</button>)}
          </div>
        )}
        <form className="asst-input" onSubmit={send}>
          <input id="asst-input" value={text} onChange={(e) => setText(e.target.value)} placeholder={busy ? 'Sto lavorando… scrivi «annulla» per fermarmi' : lastRun?.prompt ? 'Compila il riquadro, o scrivi «annulla»' : 'Scrivi cosa vuoi che faccia…'} autoComplete="off" aria-label="Scrivi all’assistente" />
          <button type="submit" className="asst-send" disabled={!text.trim()} aria-label="Invia"><ArrowUp className="w-4 h-4" /></button>
        </form>
      </div>
    </aside>
  )
}

function Bubble({ role, children }) {
  return <div className={`asst-row ${role === 'user' ? 'asst-row-user' : ''}`}><div className={role === 'user' ? 'asst-bubble asst-bubble-user' : 'asst-bubble'}>{children}</div></div>
}

const ICON = {
  done: <span className="asst-st asst-st-done"><Check className="w-3 h-3" /></span>,
  doing: <span className="asst-st"><Loader2 className="w-3 h-3 animate-spin" /></span>,
  asking: <span className="asst-st asst-st-ask"><i /></span>,
  skipped: <span className="asst-st asst-st-skip"><Minus className="w-3 h-3" /></span>,
  failed: <span className="asst-st asst-st-fail"><X className="w-3 h-3" /></span>,
  todo: <span className="asst-st asst-st-todo" />,
}

function RunCard({ run, onSubmit, onRetry }) {
  return (
    <div className="space-y-2.5">
      <div className="asst-steps">
        <p className="asst-steps-title">{run.title}</p>
        <ol className="space-y-2.5">
          {run.steps.map((s) => (
            <li key={s.id} className="flex gap-2.5">
              <span className="mt-0.5 shrink-0">{ICON[s.status]}</span>
              <div className="min-w-0">
                <p className={`text-[13px] leading-snug ${s.status === 'todo' || s.status === 'skipped' ? 'text-ink-2/60' : 'text-ink font-medium'}`}>{s.title}</p>
                {s.detail && <p className="text-[11px] text-ink-2 leading-relaxed mt-0.5">{s.detail}</p>}
              </div>
            </li>
          ))}
        </ol>
      </div>
      {run.answers.map((a, i) => <Bubble key={i} role="user">{a}</Bubble>)}
      {run.prompt && <Prompt key={run.prompt.nonce} prompt={run.prompt} onSubmit={onSubmit} />}
      {run.error && (
        <div className="asst-alert">
          <p className="font-medium inline-flex items-center gap-1.5"><AlertTriangle className="w-3.5 h-3.5" />Mi sono fermato</p>
          <p className="leading-relaxed">{run.error}</p>
          <button className="asst-chip" onClick={onRetry}>Riprova</button>
        </div>
      )}
      {run.finished && (
        <div className="asst-done">
          <p className="text-[13px] font-semibold inline-flex items-center gap-1.5"><Check className="w-4 h-4" />Fatto</p>
          {run.summary && <p className="text-[12px] leading-relaxed whitespace-pre-line">{run.summary}</p>}
        </div>
      )}
    </div>
  )
}

const NUMERIC = new Set(['money', 'number', 'percent'])
const initial = (f) => (f.default !== undefined && f.default !== null ? String(f.default) : '')

function Prompt({ prompt, onSubmit }) {
  const [vals, setVals] = useState(() => Object.fromEntries(prompt.fields.map((f) => [f.key, initial(f)])))
  const [err, setErr] = useState(null)
  const set = (k, v) => { setVals((x) => ({ ...x, [k]: v })); setErr(null) }
  const go = () => {
    const out = {}
    for (const f of prompt.fields) {
      const raw = vals[f.key]
      const empty = raw === '' || raw === undefined
      if (empty) { if (!f.optional) { setErr(`Manca: ${f.label}.`); return } continue }
      if (NUMERIC.has(f.kind)) {
        const n = Number(String(raw).replace(',', '.'))
        if (!Number.isFinite(n) || n < (f.min ?? 0)) { setErr(`${f.label}: scrivi un numero${f.min != null ? ` da ${f.min} in su` : ' non negativo'}.`); return }
        if (f.max != null && n > f.max) { setErr(`${f.label}: al massimo ${f.max}.`); return }
        out[f.key] = n
      } else if (f.kind === 'yesno') out[f.key] = raw === 'yes'
      else out[f.key] = String(raw).trim()
    }
    const bad = prompt.validate?.(out)
    if (bad) { setErr(bad); return }
    onSubmit(out)
  }
  return (
    <form className="asst-prompt" onSubmit={(e) => { e.preventDefault(); go() }}>
      <div className="space-y-1">
        <p className="text-[13px] font-semibold">{prompt.title}</p>
        {prompt.intro && <p className="text-[12px] text-ink-2 leading-relaxed">{prompt.intro}</p>}
      </div>
      {prompt.fields.map((f) => (
        <div key={f.key} className="space-y-1.5">
          <label className="text-[12px] font-semibold text-ink" htmlFor={`as-${f.key}`}>{f.label}{f.optional ? ' (facoltativo)' : ''}</label>
          {f.what && <p className="text-[11px] text-ink-2 leading-relaxed">{f.what}</p>}
          <div className="flex items-center gap-2">
            {f.kind === 'select' || f.kind === 'yesno' ? (
              <select id={`as-${f.key}`} className="asst-field" value={vals[f.key]} onChange={(e) => set(f.key, e.target.value)}>
                <option value="">— scegli —</option>
                {(f.kind === 'yesno' ? [{ value: 'yes', label: 'Sì' }, { value: 'no', label: 'No' }] : f.options).map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            ) : (
              <input id={`as-${f.key}`} className="asst-field text-right tabular-nums" type={NUMERIC.has(f.kind) ? 'number' : 'text'} step={f.step || (f.kind === 'money' ? 0.01 : 'any')} inputMode={NUMERIC.has(f.kind) ? 'decimal' : undefined}
                value={vals[f.key]} placeholder={f.placeholder || ''} onChange={(e) => set(f.key, e.target.value)} />
            )}
            {f.kind === 'money' && <span className="text-xs text-ink-2">€</span>}
            {f.kind === 'percent' && <span className="text-xs text-ink-2">%</span>}
            {f.suffix && <span className="text-xs text-ink-2 whitespace-nowrap">{f.suffix}</span>}
            {f.zeroLabel && <button type="button" className="asst-chip whitespace-nowrap" onClick={() => set(f.key, '0')}>{f.zeroLabel}</button>}
          </div>
          {(f.why || f.where || f.example) && (
            <ul className="text-[11px] text-ink-2/80 leading-relaxed space-y-0.5">
              {f.why && <li><span className="font-semibold text-ink-2">Perché serve:</span> {f.why}</li>}
              {f.where && <li><span className="font-semibold text-ink-2">Dove lo trovi:</span> {f.where}</li>}
              {f.example && <li><span className="font-semibold text-ink-2">Esempio:</span> {f.example}</li>}
            </ul>
          )}
        </div>
      ))}
      {err && <p className="text-xs text-red-700">{err}</p>}
      <div className="flex flex-wrap items-center gap-2">
        <button type="submit" className="asst-go">{prompt.submitLabel || 'Conferma e continua'}</button>
        {prompt.skipLabel && <button type="button" className="asst-chip" onClick={() => onSubmit(null)}>{prompt.skipLabel}</button>}
      </div>
    </form>
  )
}
