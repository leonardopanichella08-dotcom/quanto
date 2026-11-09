import React from 'react'
import { ArrowRight } from 'lucide-react'
import { useNav } from '../lib/nav'

/** L'ordine in cui si lavora: prima le agevolazioni, poi tutti i bandi e il piano, poi il budget di ogni bando, infine il confronto con chi ha già vinto. */
export const AGENTS = [['agevolazioni', 'Agevolazioni'], ['allocation', 'Allocazione'], ['canvas', 'Budget'], ['pattern', 'Confronto']]

/** In cima a ogni pagina-agente: in quale passo si è e, in tre righe, cosa ha fatto l'agente, cosa ha trovato e cosa gli serve. Un solo pulsante per andare avanti. */
export default function AgentBar({ current, did, found, need, next, busy }) {
  const nav = useNav()
  const rows = [['Ho fatto', did, ''], ['Ho trovato', found, ''], ['Mi serve da te', need, 'text-amber-700']].filter((r) => r[1])
  return (
    <section aria-label="L’agente di questa pagina" className="space-y-3">
      <ol className="flex flex-wrap items-center gap-x-1 gap-y-1 text-xs">
        {AGENTS.map(([id, label], i) => (
          <li key={id} className="flex items-center gap-1">
            {i > 0 && <span className="text-mute" aria-hidden="true">›</span>}
            <button type="button" onClick={() => nav.go(id)} aria-current={id === current ? 'step' : undefined}
              className={`px-2.5 py-1 rounded-full inline-flex items-center gap-1.5 transition ${id === current ? 'bg-ink text-white' : 'text-ink-2 hover:text-ink hover:bg-tint'}`}>
              <span className="tabular-nums opacity-70">{i + 1}</span>{label}
            </button>
          </li>
        ))}
      </ol>
      {(rows.length > 0 || next) && (
        <div className="card p-4 flex flex-wrap items-end gap-x-6 gap-y-3">
          <dl className="min-w-0 flex-1 basis-72 space-y-1.5">
            {rows.map(([label, text, tone]) => (
              <div key={label} className="flex flex-col sm:flex-row gap-0.5 sm:gap-3 text-sm leading-snug">
                <dt className="sm:w-28 shrink-0 text-xs text-mute sm:pt-0.5">{label}</dt>
                <dd className={`min-w-0 text-ink-2 ${tone}`}>{text}</dd>
              </div>
            ))}
          </dl>
          {next && <button type="button" className="btn-primary" disabled={busy} onClick={next.onClick}>{next.label}<ArrowRight className="w-3.5 h-3.5" /></button>}
        </div>
      )}
    </section>
  )
}
