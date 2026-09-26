import React from 'react'
import { CRITERIA_BLOCKS, fmtEur } from '../lib/format'

export const HEATMAP_CELL = { PASS: '#10b981', ADJUSTED: '#f59e0b', REJECTED: '#ef4444', SUSPENDED: '#38bdf8' }
export const HEATMAP_OUTCOME_LABEL = { PASS: 'superato', ADJUSTED: 'ridotto', REJECTED: 'respinto', SUSPENDED: 'in attesa di documento' }

/** Costruisce da una validazione i dati che il grafico si aspetta: una voce dei passi per (voce, criterio),
 * i criteri non valutati per voce, e i titoli (60 criteri + quelli sull'intero budget). Usata sia dalla vista
 * statica (Budget) sia da quella animata passo-passo (Algoritmo). */
export function heatmapData(validation, criteriaTitles = {}) {
  const steps = validation?.trace?.steps || []
  const items = validation?.items || []
  const byKey = new Map()
  steps.forEach((s, pos) => byKey.set(`${s.item_id}:${s.criterion}`, { step: s, pos }))
  const notEval = new Map(items.map((i) => [i.item_id, new Set(i.criteria_not_evaluated)]))
  const titles = { ...criteriaTitles }
  ;(validation?.budget_checks || []).forEach((c) => { titles[c.criterion] = c.title })
  return { byKey, notEval, titles, stepsLen: steps.length }
}

/** Griglia dei 60 controlli, una riga per voce: verde/ambra/rosso/azzurro se il controllo è stato eseguito,
 * tratteggiato se non valutato (manca un dato o una regola del bando), grigio chiaro se non pertinente alla
 * voce. `cursor` governa fino a che passo mostrare (Infinity = tutto, a validazione conclusa). */
export default function CriteriaHeatmap({ items, byKey, notEval, budgetChecks = [], cursor = Infinity, stepsLen = 0, selected, onSelect, titles = {}, cellSize = 13, statusDot }) {
  const cols = Array.from({ length: 60 }, (_, i) => i + 1)
  const showBudget = cursor > stepsLen
  const cell = (item, n) => {
    const hit = byKey.get(`${item.item_id}:${n}`)
    if (hit && hit.pos < cursor) {
      return { color: HEATMAP_CELL[hit.step.outcome], tip: `${item.item_id} · #${n} ${titles[n] || ''}\n${HEATMAP_OUTCOME_LABEL[hit.step.outcome]}${hit.step.delta_eur ? ` (${fmtEur(hit.step.delta_eur)})` : ''}\n${hit.step.note}` }
    }
    if (hit) return { color: 'rgba(21,21,15,0.13)', tip: `${item.item_id} · #${n}: non ancora eseguito` }
    if (notEval.get(item.item_id)?.has(n)) return { color: 'transparent', border: '1px dashed rgba(21,21,15,0.4)', tip: `${item.item_id} · #${n} ${titles[n] || ''}\nNON VALUTATO: manca un dato o la regola del bando` }
    return { color: 'rgba(21,21,15,0.04)', tip: `#${n}: non pertinente a questa voce` }
  }
  return (
    <div className="overflow-x-auto pb-2">
      <div style={{ minWidth: 60 * (cellSize + 2) + 110 }} className="space-y-0.5">
        <div className="flex" style={{ paddingLeft: 108 }}>
          {CRITERIA_BLOCKS.map((b) => (
            <div key={b.label} className="text-[9px] text-mute border-l border-line-strong pl-1 truncate" style={{ width: (b.to - b.from + 1) * (cellSize + 2) }}>{b.label}</div>
          ))}
        </div>
        <div className="flex" style={{ paddingLeft: 108 }}>
          {cols.map((n) => <div key={n} className="text-[7px] font-mono text-mute text-center" style={{ width: cellSize + 2 }}>{n % 5 === 0 || n === 1 ? n : ''}</div>)}
        </div>
        {items.map((it) => (
          <div key={it.item_id} onClick={() => onSelect?.(it.item_id)} className={`flex items-center ${onSelect ? 'cursor-pointer' : ''} rounded ${selected === it.item_id ? 'bg-brand/10 ring-1 ring-brand/50' : onSelect ? 'hover:bg-tint' : ''}`}>
            <div className="w-[108px] shrink-0 pr-2 flex items-center gap-1.5 text-[10px] font-mono text-ink-2 truncate" title={it.description}>
              {statusDot && <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: showBudget ? (statusDot[it.status] || '#9ca3af') : 'rgba(21,21,15,0.35)' }} />}
              {it.item_id}
            </div>
            {cols.map((n) => {
              const c = cell(it, n)
              return <div key={n} title={c.tip} className="rounded-[2px] transition-colors" style={{ width: cellSize, height: cellSize, margin: 1, background: c.color, border: c.border }} />
            })}
          </div>
        ))}
        <div className="flex items-center rounded bg-white/45 mt-1">
          <div className="w-[108px] shrink-0 pr-2 text-[10px] font-mono text-fuchsia-700">BUDGET</div>
          {cols.map((n) => {
            const c = budgetChecks.find((x) => x.criterion === n)
            const color = !c ? 'rgba(21,21,15,0.04)' : !showBudget ? 'rgba(21,21,15,0.13)' : c.status === 'PASS' ? '#10b981' : c.status === 'FAIL' ? '#ef4444' : 'transparent'
            return <div key={n} title={c ? `#${n} ${c.title}\n${c.status}\n${c.message}` : `#${n}`} style={{ width: cellSize, height: cellSize, margin: 1, background: color, border: c && c.status === 'NOT_EVALUATED' && showBudget ? '1px dashed rgba(21,21,15,0.4)' : undefined }} className="rounded-[2px]" />
          })}
        </div>
      </div>
    </div>
  )
}
