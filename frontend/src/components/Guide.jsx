import React, { useState } from 'react'
import { BookOpen, HelpCircle, X } from 'lucide-react'
import { GUIDE } from '../data/help'
import { useNav } from '../lib/nav'
import { Term } from './Help'

const KEY = (page) => `quanto.guide.${page}`
const read = (page) => { try { return localStorage.getItem(KEY(page)) === '1' } catch { return false } }
const write = (page, v) => { try { localStorage.setItem(KEY(page), v ? '1' : '0') } catch { /* storage non disponibile */ } }

/** Chiusa per difetto (un bottone piccolo, non sporca la pagina): a richiesta mostra cosa fa la pagina,
 * come si usa, un esempio e le parole difficili. Lo stato aperto/chiuso si ricorda per pagina. */
export default function Guide({ page, extra }) {
  const g = GUIDE[page]
  const nav = useNav()
  const [open, setOpen] = useState(() => read(page))
  if (!g) return null
  const toggle = () => { write(page, !open); setOpen(!open) }
  if (!open) {
    return (
      <button type="button" onClick={toggle} className="text-xs text-ink-2 hover:text-ink inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-line hover:border-line-strong">
        <HelpCircle className="w-3.5 h-3.5" />Guida: a cosa serve questa pagina
      </button>
    )
  }
  return (
    <section className="border-l-2 border-brand/40 pl-4 space-y-2">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm text-ink leading-relaxed">{g.what}</p>
        <button type="button" onClick={toggle} className="text-xs text-ink-2 hover:text-ink inline-flex items-center gap-1 shrink-0 mt-0.5"><X className="w-3.5 h-3.5" />Chiudi</button>
      </div>
      <div className="grid md:grid-cols-2 gap-x-8 gap-y-4 pt-1">
        <div className="space-y-2">
          <p className="text-xs font-semibold text-ink-2">Come si usa</p>
          <ol className="space-y-1.5 text-xs text-ink-2">
            {g.steps.map((s, i) => (
              <li key={s} className="flex gap-2"><span className="w-4 h-4 rounded-full bg-tint-2 text-[10px] font-semibold flex items-center justify-center text-ink-2 shrink-0 mt-0.5">{i + 1}</span><span className="leading-relaxed">{s}</span></li>
            ))}
          </ol>
        </div>
        <div className="space-y-3">
          <div className="space-y-1">
            <p className="text-xs font-semibold text-ink-2">Un esempio</p>
            <p className="text-xs text-ink-2 leading-relaxed">{g.example}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs font-semibold text-ink-2">Parole difficili <span className="font-normal text-mute">(clicca)</span></p>
            <p className="text-xs text-ink-2 flex flex-wrap gap-x-4 gap-y-1">{g.terms.map((t) => <Term key={t} id={t} />)}</p>
          </div>
          {extra}
          <button type="button" onClick={() => nav.go('guida')} className="text-xs text-ink-2 hover:text-ink inline-flex items-center gap-1.5"><BookOpen className="w-3.5 h-3.5" />Apri la Guida completa</button>
        </div>
      </div>
    </section>
  )
}
