import React, { useState } from 'react'
import { BookOpen, ChevronDown, ChevronUp } from 'lucide-react'
import { GUIDE } from '../data/help'
import { useNav } from '../lib/nav'
import { Term } from './Help'

const KEY = (page) => `quanto.guide.${page}`
const read = (page) => { try { return localStorage.getItem(KEY(page)) === '1' } catch { return false } }
const write = (page, v) => { try { localStorage.setItem(KEY(page), v ? '1' : '0') } catch { /* storage non disponibile */ } }

/** In cima a ogni pagina: cosa fa (sempre visibile) e, a richiesta, come si usa, un esempio e le parole difficili. */
export default function Guide({ page, extra }) {
  const g = GUIDE[page]
  const nav = useNav()
  const [open, setOpen] = useState(() => read(page))
  if (!g) return null
  const toggle = () => { write(page, !open); setOpen(!open) }
  return (
    <section className="border-l-2 border-[#deffac]/40 pl-4 space-y-2">
      <p className="text-sm text-neutral-200 leading-relaxed">{g.what}</p>
      <button type="button" onClick={toggle} className="text-xs text-[#deffac] hover:underline inline-flex items-center gap-1">
        {open ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}{open ? 'Nascondi la spiegazione' : 'Come si usa, un esempio e le parole difficili'}
      </button>
      {open && (
        <div className="grid md:grid-cols-2 gap-x-8 gap-y-4 pt-1">
          <div className="space-y-2">
            <p className="text-xs font-semibold text-neutral-400">Come si usa</p>
            <ol className="space-y-1.5 text-xs text-neutral-300">
              {g.steps.map((s, i) => (
                <li key={s} className="flex gap-2"><span className="w-4 h-4 rounded-full bg-neutral-800 text-[10px] font-semibold flex items-center justify-center text-neutral-300 shrink-0 mt-0.5">{i + 1}</span><span className="leading-relaxed">{s}</span></li>
              ))}
            </ol>
          </div>
          <div className="space-y-3">
            <div className="space-y-1">
              <p className="text-xs font-semibold text-neutral-400">Un esempio</p>
              <p className="text-xs text-neutral-300 leading-relaxed">{g.example}</p>
            </div>
            <div className="space-y-1">
              <p className="text-xs font-semibold text-neutral-400">Parole difficili <span className="font-normal text-neutral-500">(clicca)</span></p>
              <p className="text-xs text-neutral-300 flex flex-wrap gap-x-4 gap-y-1">{g.terms.map((t) => <Term key={t} id={t} />)}</p>
            </div>
            {extra}
            <button type="button" onClick={() => nav.go('guida')} className="text-xs text-neutral-400 hover:text-white inline-flex items-center gap-1.5"><BookOpen className="w-3.5 h-3.5" />Apri la Guida completa</button>
          </div>
        </div>
      )}
    </section>
  )
}
