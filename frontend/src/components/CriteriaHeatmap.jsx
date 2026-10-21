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
  const count = (o) => steps.filter((x) => x.outcome === o).length
  return { byKey, notEval, titles, stepsLen: steps.length, passed: count('PASS'), adjusted: count('ADJUSTED'), rejected: count('REJECTED') }
}

/** Griglia dei 60 controlli, una riga per voce: verde/ambra/rosso/azzurro se il controllo è stato eseguito,
 * tratteggiato se non valutato (manca un dato o una regola del bando), grigio chiaro se non pertinente alla
 * voce. `cursor` governa fino a che passo mostrare (Infinity = tutto, a validazione conclusa). */
export default function CriteriaHeatmap({ items, byKey, notEval, budgetChecks = [], cursor = Infinity, stepsLen = 0, selected, onSelect, titles = {}, statusDot }) {
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
  const LABEL = '6.5rem'
  const grid = { display: 'grid', gridTemplateColumns: `${LABEL} repeat(60, minmax(0, 1fr))`, columnGap: 2, alignItems: 'center' }
  const sq = (color, border, tip, key) => <div key={key} title={tip} className="rounded-[2px] aspect-square transition-colors" style={{ background: color, border }} />
  return (
    <div className="overflow-x-auto -mx-1 px-1 pb-1">
      <div style={{ minWidth: 440 }} className="space-y-[3px]">
        <div style={grid} className="mb-1">
          <span />
          {CRITERIA_BLOCKS.map((b) => (
            <div key={b.label} className="text-[10px] text-mute border-l border-line-strong pl-1.5 truncate leading-tight" style={{ gridColumn: `${b.from + 1} / span ${b.to - b.from + 1}` }} title={b.label}>{b.label}</div>
          ))}
        </div>
        {items.map((it) => (
          <div key={it.item_id} style={grid} onClick={() => onSelect?.(it.item_id)} className={`rounded-md py-[1px] ${onSelect ? 'cursor-pointer' : ''} ${selected === it.item_id ? 'bg-brand/10 ring-1 ring-brand/50' : onSelect ? 'hover:bg-tint' : ''}`}>
            <div className="pr-2 flex items-center gap-1.5 text-[11px] font-mono text-ink-2 min-w-0" title={`${it.item_id} · ${it.description || ''}`}>
              {statusDot && <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: showBudget ? (statusDot[it.status] || '#9ca3af') : 'rgba(21,21,15,0.35)' }} />}
              <span className="truncate">{it.item_id}</span>
            </div>
            {cols.map((n) => { const c = cell(it, n); return sq(c.color, c.border, c.tip, n) })}
          </div>
        ))}
        <div style={grid} className="pt-1 mt-1 border-t border-line">
          <div className="text-[11px] font-mono text-fuchsia-700">Intero budget</div>
          {cols.map((n) => {
            const c = budgetChecks.find((x) => x.criterion === n)
            const color = !c ? 'rgba(21,21,15,0.04)' : !showBudget ? 'rgba(21,21,15,0.13)' : c.status === 'PASS' ? '#10b981' : c.status === 'FAIL' ? '#ef4444' : 'transparent'
            return sq(color, c && c.status === 'NOT_EVALUATED' && showBudget ? '1px dashed rgba(21,21,15,0.4)' : undefined, c ? `#${n} ${c.title}
${c.status}
${c.message}` : `#${n}`, n)
          })}
        </div>
      </div>
    </div>
  )
}
