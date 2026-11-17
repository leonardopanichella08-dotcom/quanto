import React, { useEffect, useRef, useState } from 'react'
import { ArrowUp, ChevronDown, ChevronRight, Loader2, Sparkles } from 'lucide-react'
import { api } from '../../lib/api'
import { ResultView } from './charts'

/* Chatbot interno: una domanda in italiano, una risposta con numeri veri, grafico e la ricerca usata (per controllare cosa ha letto). */
const EXAMPLES = ['Quante richieste di accesso per stato?', 'Visite al sito negli ultimi 30 giorni', 'Utenti per livello', 'Post LinkedIn per stato', 'Operazioni negli ultimi 7 giorni']

function Turn({ t }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="space-y-3">
      <p className="ml-auto w-fit max-w-[85%] bg-brand text-white text-sm px-4 py-2 rounded-2xl rounded-br-md">{t.q}</p>
      {t.busy ? <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Cerco nei dati…</p> : (
        <div className="space-y-3">
          <p className="text-sm leading-relaxed pl-3 border-l-2" style={{ borderColor: '#F1E21B' }}>{t.error || t.r.answer}</p>
          {t.r?.result && <ResultView result={t.r.result} />}
          {t.r?.plan && (
            <div className="text-[11px] text-mute">
              <button onClick={() => setOpen(!open)} className="inline-flex items-center gap-1 hover:text-ink">{open ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}Come ho cercato · {t.r.engine}</button>
              {open && <pre className="mt-1.5 p-2 rounded-lg bg-black/[0.04] overflow-x-auto font-mono">{JSON.stringify(t.r.plan, null, 2)}</pre>}
            </div>
          )}
          {t.r?.note && <p className="text-[11px] text-amber-700">{t.r.note}</p>}
        </div>
      )}
    </div>
  )
}

export default function Ask({ compact = false }) {
  const [q, setQ] = useState('')
  const [turns, setTurns] = useState([])
  const end = useRef(null)
  useEffect(() => { if (turns.length) end.current?.scrollIntoView({ block: 'nearest', behavior: 'smooth' }) }, [turns])
  const ask = async (text) => {
    const question = (text ?? q).trim()
    if (!question) return
    setQ('')
    const id = Date.now()
    setTurns((t) => [...t, { id, q: question, busy: true }])
    try {
      const r = await api.hqAsk(question)
      setTurns((t) => t.map((x) => (x.id === id ? { ...x, busy: false, r } : x)))
    } catch (e) {
      setTurns((t) => t.map((x) => (x.id === id ? { ...x, busy: false, error: e.message } : x)))
    }
  }
  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-center gap-2"><Sparkles className="w-4 h-4" /><h3 className="font-semibold text-[15px] tracking-tight">Chiedi ai dati di QUANTO</h3></div>
      {turns.length === 0 && !compact && (
        <div className="flex flex-wrap gap-1.5">{EXAMPLES.map((e) => <button key={e} onClick={() => ask(e)} className="text-xs px-3 py-1.5 rounded-full bg-black/[0.05] text-ink-2 hover:bg-black/[0.09]">{e}</button>)}</div>
      )}
      {turns.length > 0 && <div className="space-y-6 max-h-[560px] overflow-y-auto pr-1">{turns.map((t) => <Turn key={t.id} t={t} />)}<span ref={end} /></div>}
      <form onSubmit={(e) => { e.preventDefault(); ask() }} className="flex items-center gap-2 rounded-full bg-black/[0.04] pl-4 pr-1.5 py-1.5 focus-within:bg-white focus-within:ring-1 focus-within:ring-ink">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Per esempio: quante persone hanno chiesto l’accesso questo mese?" className="flex-1 bg-transparent text-sm outline-none py-1.5 min-w-0" aria-label="Domanda sui dati" />
        <button type="submit" disabled={!q.trim()} aria-label="Chiedi" className="w-9 h-9 rounded-full bg-brand text-white grid place-items-center disabled:opacity-25"><ArrowUp className="w-4 h-4" /></button>
      </form>
    </div>
  )
}
