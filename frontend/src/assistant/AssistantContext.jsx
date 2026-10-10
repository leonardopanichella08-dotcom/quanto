import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { AlertTriangle, Check, Loader2, Minus, Sparkles, X } from 'lucide-react'
import { TASKS, TASK_ORDER } from './tasks'

/** L'assistente guidato: prende in mano i passaggi in cui l'utente dovrebbe inserire dati o muoversi nell'app, li esegue lui (cambia pagina, salva, calcola),
 *  e quando gli serve un valore lo chiede nel pannello a destra, spiegando in parole semplici che cos'è, cosa scrivere, perché serve e dove si trova.
 *  Non inventa mai un dato: usa solo ciò che scrive l'utente o che è già nel profilo. L'app resta visibile a sinistra, ridotta, e si vede cosa succede. */
class Cancelled extends Error {}
const Ctx = createContext(null)
export const useAssistant = () => useContext(Ctx) || { start: () => {}, openMenu: () => {}, open: false, busy: false }

export function AssistantProvider({ bridge, enabled, children }) {
  const [run, setRun] = useState(null)               // null = chiuso; {id: null} = menu delle attività
  const token = useRef(0)
  const waiting = useRef(null)

  const makeApi = (my) => {
    const alive = () => { if (my !== token.current) throw new Cancelled() }
    const upd = (fn) => setRun((r) => (r && r.token === my ? fn(r) : r))
    const patch = (id, p) => upd((r) => ({ ...r, steps: r.steps.map((s) => (s.id === id ? { ...s, ...p } : s)) }))
    return {
      bridge: () => bridge.current,
      begin: (id, detail = null) => { alive(); patch(id, { status: 'doing', detail }); upd((r) => ({ ...r, busy: true, prompt: null })) },
      done: (id, detail = null) => { alive(); patch(id, { status: 'done', detail }) },
      skip: (id, detail = null) => { alive(); patch(id, { status: 'skipped', detail }) },
      fail: (id, detail = null) => { alive(); patch(id, { status: 'failed', detail }) },
      pause: (ms = 700) => new Promise((res) => setTimeout(res, ms)).then(alive),
      ask: (id, prompt) => new Promise((resolve) => {
        alive()
        patch(id, { status: 'asking' })
        upd((r) => ({ ...r, busy: false, prompt: { ...prompt, stepId: id, nonce: Math.random() } }))
        waiting.current = { my, resolve }
      }),
      /** aspetta un evento dell'app (es. il risultato dell'Allocazione); null se non arriva entro il tempo */
      waitFor: (name, ms = 90000) => new Promise((resolve) => {
        let done = false
        const end = (v) => { if (done) return; done = true; window.removeEventListener(name, on); clearTimeout(t); resolve(v) }
        const on = (e) => end(e.detail ?? true)
        const t = setTimeout(() => end(null), ms)
        window.addEventListener(name, on)
      }).then((v) => { alive(); return v }),
      finish: (summary) => { alive(); upd((r) => ({ ...r, finished: true, busy: false, prompt: null, summary })) },
    }
  }

  const start = useCallback((taskId, params = {}) => {
    const t = TASKS[taskId]
    if (!t) return
    const my = ++token.current
    waiting.current = null
    setRun({ token: my, id: taskId, title: t.title, steps: t.steps.map((s) => ({ ...s, status: 'todo' })), prompt: null, busy: true, finished: false, summary: null, error: null, params })
    const a = makeApi(my)
    Promise.resolve().then(() => t.run(a, params)).catch((e) => {
      if (e instanceof Cancelled) return
      setRun((r) => (r && r.token === my ? { ...r, error: e?.message || String(e), busy: false, prompt: null } : r))
    })
  }, [])                                                   // eslint-disable-line react-hooks/exhaustive-deps
  const stop = useCallback(() => { token.current += 1; waiting.current = null; setRun(null) }, [])
  const openMenu = useCallback(() => { token.current += 1; waiting.current = null; setRun({ token: token.current, id: null }) }, [])
  const submit = (values) => { const w = waiting.current; if (!w) return; waiting.current = null; setRun((r) => (r ? { ...r, prompt: null, busy: true } : r)); w.resolve(values) }

  useEffect(() => {
    const on = (e) => start(e.detail?.task, e.detail || {})
    window.addEventListener('quanto-assistant', on)
    return () => window.removeEventListener('quanto-assistant', on)
  }, [start])
  useEffect(() => { if (!enabled) stop() }, [enabled, stop])

  const open = !!run && enabled
  const value = useMemo(() => ({ start, stop, openMenu, open, busy: !!run?.busy }), [start, stop, openMenu, open, run?.busy])
  return (
    <Ctx.Provider value={value}>
      <div className={open ? 'md:pl-3 md:pr-[412px] md:py-3 max-md:pb-[58vh] min-h-screen bg-tint-2' : ''}>
        <div className={open ? 'relative rounded-xl border border-line-strong bg-page overflow-hidden min-h-[calc(100vh-24px)]' : ''}>
          {children}
          {open && run.busy && <div className="absolute inset-0 z-40 cursor-progress bg-white/20" aria-hidden="true" />}
        </div>
      </div>
      {open && <Panel run={run} onClose={stop} onStart={start} onSubmit={submit} />}
    </Ctx.Provider>
  )
}

const ICON = {
  done: <span className="w-5 h-5 rounded-full bg-emerald-500/15 text-emerald-700 flex items-center justify-center"><Check className="w-3 h-3" /></span>,
  doing: <span className="w-5 h-5 rounded-full bg-tint-2 flex items-center justify-center"><Loader2 className="w-3 h-3 animate-spin text-ink" /></span>,
  asking: <span className="w-5 h-5 rounded-full border-2 border-ink flex items-center justify-center"><i className="w-1.5 h-1.5 rounded-full bg-ink" /></span>,
  skipped: <span className="w-5 h-5 rounded-full bg-tint-2 text-mute flex items-center justify-center"><Minus className="w-3 h-3" /></span>,
  failed: <span className="w-5 h-5 rounded-full bg-red-500/15 text-red-700 flex items-center justify-center"><X className="w-3 h-3" /></span>,
  todo: <span className="w-5 h-5 rounded-full border border-line-strong" />,
}

function Panel({ run, onClose, onStart, onSubmit }) {
  return (
    <aside className="fixed z-50 bg-white border-line md:border-l max-md:border-t md:right-0 md:top-0 md:h-screen md:w-[400px] max-md:left-0 max-md:right-0 max-md:bottom-0 max-md:h-[55vh] flex flex-col" aria-label="Assistente QUANTO">
      <header className="flex items-center gap-2.5 px-4 py-3 border-b border-line">
        <span className="w-7 h-7 rounded-lg bg-ink text-white flex items-center justify-center shrink-0"><Sparkles className="w-3.5 h-3.5" /></span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold leading-tight">Assistente</p>
          <p className="text-[11px] text-mute truncate">{run.id ? run.title : 'Dimmi cosa vuoi fare'}</p>
        </div>
        <button className="btn !px-2 !py-1.5" onClick={onClose} title={run.id && !run.finished ? 'Interrompi e riprendi tu' : 'Chiudi'} aria-label="Chiudi l’assistente"><X className="w-3.5 h-3.5" /></button>
      </header>
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-5">
        {!run.id ? <Menu onStart={onStart} /> : <Running run={run} onSubmit={onSubmit} onClose={onClose} onStart={onStart} />}
      </div>
      <footer className="px-4 py-2.5 border-t border-line text-[11px] text-mute leading-relaxed">
        {run.busy ? 'Sto lavorando: l’app a sinistra si muove da sola. ' : ''}Non invento mai nessun dato: uso solo quello che scrivi tu o che è già nel profilo. Puoi interrompere quando vuoi con la X.
      </footer>
    </aside>
  )
}

function Menu({ onStart }) {
  return (
    <div className="space-y-3">
      <p className="text-xs text-ink-2 leading-relaxed">Scegli un’attività: la faccio io al posto tuo, passo per passo. Quando mi serve un dato te lo chiedo qui, spiegandoti cos’è e dove lo trovi.</p>
      {TASK_ORDER.map((id) => (
        <button key={id} className="w-full text-left rounded-xl border border-line hover:border-line-strong p-3.5 space-y-1" onClick={() => onStart(id, {})}>
          <p className="text-sm font-semibold text-ink">{TASKS[id].title}</p>
          <p className="text-xs text-ink-2 leading-relaxed">{TASKS[id].blurb}</p>
        </button>
      ))}
    </div>
  )
}

function Running({ run, onSubmit, onClose, onStart }) {
  return (
    <>
      <ol className="space-y-3">
        {run.steps.map((s) => (
          <li key={s.id} className="flex gap-3">
            <span className="mt-0.5 shrink-0">{ICON[s.status]}</span>
            <div className="min-w-0">
              <p className={`text-[13px] leading-snug ${s.status === 'todo' || s.status === 'skipped' ? 'text-mute' : 'text-ink font-medium'}`}>{s.title}</p>
              {s.detail && <p className="text-[11px] text-ink-2 leading-relaxed mt-0.5">{s.detail}</p>}
            </div>
          </li>
        ))}
      </ol>
      {run.prompt && <Prompt key={run.prompt.nonce} prompt={run.prompt} onSubmit={onSubmit} />}
      {run.error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-3 text-xs text-red-700 space-y-2">
          <p className="font-medium inline-flex items-center gap-1.5"><AlertTriangle className="w-3.5 h-3.5" />Mi sono fermato</p>
          <p className="leading-relaxed">{run.error}</p>
          <div className="flex gap-2"><button className="btn !py-1" onClick={() => onStart(run.id, run.params)}>Riprova</button><button className="btn !py-1" onClick={onClose}>Chiudi</button></div>
        </div>
      )}
      {run.finished && (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-3.5 space-y-2">
          <p className="text-sm font-semibold text-emerald-700 inline-flex items-center gap-1.5"><Check className="w-4 h-4" />Fatto</p>
          {run.summary && <p className="text-xs text-ink-2 leading-relaxed whitespace-pre-line">{run.summary}</p>}
          <button className="btn-primary !py-1.5" onClick={onClose}>Chiudi e continua da solo</button>
        </div>
      )}
    </>
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
    <form className="rounded-xl border border-ink/80 p-3.5 space-y-4" onSubmit={(e) => { e.preventDefault(); go() }}>
      <div className="space-y-1">
        <p className="text-sm font-semibold">{prompt.title}</p>
        {prompt.intro && <p className="text-xs text-ink-2 leading-relaxed">{prompt.intro}</p>}
      </div>
      {prompt.fields.map((f) => (
        <div key={f.key} className="space-y-1.5">
          <label className="text-xs font-semibold text-ink" htmlFor={`as-${f.key}`}>{f.label}{f.optional ? ' (facoltativo)' : ''}</label>
          {f.what && <p className="text-[11px] text-ink-2 leading-relaxed">{f.what}</p>}
          <div className="flex items-center gap-2">
            {f.kind === 'select' || f.kind === 'yesno' ? (
              <select id={`as-${f.key}`} className="field" value={vals[f.key]} onChange={(e) => set(f.key, e.target.value)}>
                <option value="">— scegli —</option>
                {(f.kind === 'yesno' ? [{ value: 'yes', label: 'Sì' }, { value: 'no', label: 'No' }] : f.options).map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            ) : (
              <input id={`as-${f.key}`} className="field text-right tabular-nums" type={NUMERIC.has(f.kind) ? 'number' : 'text'} step={f.step || (f.kind === 'money' ? 0.01 : 'any')} inputMode={NUMERIC.has(f.kind) ? 'decimal' : undefined}
                value={vals[f.key]} placeholder={f.placeholder || ''} onChange={(e) => set(f.key, e.target.value)} />
            )}
            {f.kind === 'money' && <span className="text-xs text-mute">€</span>}
            {f.kind === 'percent' && <span className="text-xs text-mute">%</span>}
            {f.suffix && <span className="text-xs text-mute whitespace-nowrap">{f.suffix}</span>}
            {f.zeroLabel && <button type="button" className="btn !py-1 whitespace-nowrap" onClick={() => set(f.key, '0')}>{f.zeroLabel}</button>}
          </div>
          {(f.why || f.where || f.example) && (
            <ul className="text-[11px] text-mute leading-relaxed space-y-0.5">
              {f.why && <li><span className="font-semibold text-ink-2">Perché serve:</span> {f.why}</li>}
              {f.where && <li><span className="font-semibold text-ink-2">Dove lo trovi:</span> {f.where}</li>}
              {f.example && <li><span className="font-semibold text-ink-2">Esempio:</span> {f.example}</li>}
            </ul>
          )}
        </div>
      ))}
      {err && <p className="text-xs text-red-700">{err}</p>}
      <div className="flex flex-wrap items-center gap-2">
        <button type="submit" className="btn-primary">{prompt.submitLabel || 'Conferma e continua'}</button>
        {prompt.skipLabel && <button type="button" className="btn" onClick={() => onSubmit(null)}>{prompt.skipLabel}</button>}
      </div>
    </form>
  )
}
