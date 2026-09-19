import React, { useEffect, useMemo, useRef, useState } from 'react'
import { ChevronsRight, Pause, Play, RotateCcw } from 'lucide-react'
import Guide from './Guide'
import { Hint } from './Help'
import { useNav } from '../lib/nav'
import { CRITERIA_BLOCKS, STATUS_LABEL, fmtEur, fmtPct } from '../lib/format'

const ORDER = ['LINE_CRITERIA', 'FTE', 'SHARE_CAPS', 'BUDGET_CHECKS', 'HASH', 'MERKLE', 'EXPLAIN']
const TAIL = ['BUDGET_CHECKS', 'HASH', 'MERKLE', 'EXPLAIN']
const CELL = { PASS: '#10b981', ADJUSTED: '#f59e0b', REJECTED: '#ef4444', SUSPENDED: '#38bdf8' }
const OUTCOME_LABEL = { PASS: 'superato', ADJUSTED: 'ridotto', REJECTED: 'respinto', SUSPENDED: 'in attesa di documento' }
const SPEEDS = { Lento: 450, Normale: 120, Veloce: 25 }
const STATUS_DOT = { APPROVED: '#10b981', CAP_EXCEEDED_ADJUSTED: '#f59e0b', REJECTED: '#ef4444', MISSING_DOCUMENTS: '#38bdf8' }

/** Passi nell'ordine dell'algoritmo: prima i criteri di riga di tutte le voci, poi i massimali sul totale. */
function orderSteps(steps) {
  return [...steps.filter((s) => s.stage !== 'SHARE_CAPS'), ...steps.filter((s) => s.stage === 'SHARE_CAPS')]
}

function stageOf(cursor, ordered) {
  if (cursor <= 0) return null
  if (cursor <= ordered.length) {
    const s = ordered[cursor - 1]
    return s.criterion === 8 && s.outcome !== 'PASS' ? 'FTE' : s.stage
  }
  return TAIL[Math.min(cursor - ordered.length, TAIL.length) - 1]
}

function Pipeline({ stages, active }) {
  const max = Math.max(...stages.map((s) => s.duration_ms), 0.001)
  const activeIdx = ORDER.indexOf(active)
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-7 gap-2">
      {stages.map((s, i) => {
        const idx = ORDER.indexOf(s.key)
        const state = active === s.key ? 'active' : activeIdx > idx ? 'done' : 'todo'
        return (
          <div key={s.key} className={`rounded-xl border p-2.5 space-y-1.5 transition ${state === 'active' ? 'border-[#deffac] bg-[#deffac]/10' : state === 'done' ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-neutral-800 bg-neutral-950'}`}>
            <div className="flex items-center gap-1.5">
              <span className={`w-4 h-4 rounded-full text-[10px] font-bold flex items-center justify-center ${state === 'active' ? 'bg-[#deffac] text-black' : state === 'done' ? 'bg-emerald-500 text-black' : 'bg-neutral-800 text-neutral-400'}`}>{i + 1}</span>
              <span className="text-[11px] font-bold text-neutral-200 leading-tight">{s.label}</span>
            </div>
            <div className="h-1 rounded bg-neutral-800 overflow-hidden"><div className="h-full bg-[#deffac]/70" style={{ width: `${Math.max(4, (s.duration_ms / max) * 100)}%` }} /></div>
            <p className="text-[11px] text-neutral-500 leading-snug">{s.detail}</p>
            <p className="text-[10px] font-mono text-neutral-600">{s.duration_ms.toFixed(2)} ms</p>
          </div>
        )
      })}
    </div>
  )
}

function Heatmap({ items, byKey, notEval, budgetChecks, cursor, stepsLen, selected, onSelect, titles }) {
  const cols = Array.from({ length: 60 }, (_, i) => i + 1)
  const showBudget = cursor > stepsLen
  const cell = (item, n) => {
    const hit = byKey.get(`${item.item_id}:${n}`)
    if (hit && hit.pos < cursor) return { color: CELL[hit.step.outcome], tip: `${item.item_id} · #${n} ${titles[n] || ''}\n${OUTCOME_LABEL[hit.step.outcome]}${hit.step.delta_eur ? ` (${fmtEur(hit.step.delta_eur)})` : ''}\n${hit.step.note}` }
    if (hit) return { color: '#1f2937', tip: `${item.item_id} · #${n}: non ancora eseguito` }
    if (notEval.get(item.item_id)?.has(n)) return { color: 'transparent', border: '1px dashed #525252', tip: `${item.item_id} · #${n} ${titles[n] || ''}\nNON VALUTATO: manca un dato o la regola del bando` }
    return { color: '#0b0b0b', tip: `#${n}: non pertinente a questa voce` }
  }
  return (
    <div className="overflow-x-auto pb-2">
      <div style={{ minWidth: 60 * 15 + 110 }} className="space-y-0.5">
        <div className="flex" style={{ paddingLeft: 108 }}>
          {CRITERIA_BLOCKS.map((b) => (
            <div key={b.label} className="text-[9px] text-neutral-500 border-l border-neutral-700 pl-1 truncate" style={{ width: (b.to - b.from + 1) * 15 }}>{b.label}</div>
          ))}
        </div>
        <div className="flex" style={{ paddingLeft: 108 }}>
          {cols.map((n) => <div key={n} className="text-[7px] font-mono text-neutral-600 text-center" style={{ width: 15 }}>{n % 5 === 0 || n === 1 ? n : ''}</div>)}
        </div>
        {items.map((it) => (
          <div key={it.item_id} onClick={() => onSelect(it.item_id)} className={`flex items-center cursor-pointer rounded ${selected === it.item_id ? 'bg-[#deffac]/10 ring-1 ring-[#deffac]/50' : 'hover:bg-neutral-900'}`}>
            <div className="w-[108px] shrink-0 pr-2 flex items-center gap-1.5 text-[10px] font-mono text-neutral-300 truncate">
              <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: cursor > stepsLen ? STATUS_DOT[it.status] : '#525252' }} />{it.item_id}
            </div>
            {cols.map((n) => {
              const c = cell(it, n)
              return <div key={n} title={c.tip} className="rounded-[2px] transition-colors" style={{ width: 13, height: 13, margin: 1, background: c.color, border: c.border }} />
            })}
          </div>
        ))}
        <div className="flex items-center rounded bg-neutral-900/60 mt-1">
          <div className="w-[108px] shrink-0 pr-2 text-[10px] font-mono text-fuchsia-300">BUDGET</div>
          {cols.map((n) => {
            const c = budgetChecks.find((x) => x.criterion === n)
            const color = !c ? '#0b0b0b' : !showBudget ? '#1f2937' : c.status === 'PASS' ? '#10b981' : c.status === 'FAIL' ? '#ef4444' : 'transparent'
            return <div key={n} title={c ? `#${n} ${c.title}\n${c.status}\n${c.message}` : `#${n}`} style={{ width: 13, height: 13, margin: 1, background: color, border: c && c.status === 'NOT_EVALUATED' && showBudget ? '1px dashed #525252' : undefined }} className="rounded-[2px]" />
          })}
        </div>
      </div>
    </div>
  )
}

function Waterfall({ item, steps, cursorPos, orderedIndex }) {
  if (!item) return <p className="text-xs text-neutral-500 italic">Clicca una riga della mappa per vedere come cambia l’importo di quella voce.</p>
  const total = Math.max(item.original_cost_eur, 0.01)
  const adj = steps.filter((s) => s.delta_eur !== 0)
  let running = item.original_cost_eur
  const rows = adj.map((s) => { const before = running; running += s.delta_eur; return { s, before, after: running, reached: orderedIndex(s) < cursorPos } })
  return (
    <div className="space-y-1.5 text-xs">
      <div className="flex items-center gap-2"><span className="w-40 shrink-0 text-neutral-300 truncate">Importo richiesto</span>
        <div className="flex-1 h-4 bg-neutral-900 rounded relative"><div className="absolute inset-y-0 left-0 bg-emerald-500/70 rounded" style={{ width: '100%' }} /></div>
        <span className="w-24 text-right font-mono text-neutral-300">{fmtEur(item.original_cost_eur)}</span></div>
      {rows.map(({ s, before, after, reached }) => (
        <div key={s.seq} className={`flex items-center gap-2 transition-opacity ${reached ? 'opacity-100' : 'opacity-25'}`}>
          <span className="w-40 shrink-0 truncate text-neutral-400" title={s.note}><span className="font-mono text-[#deffac]">#{s.criterion}</span> {s.outcome === 'REJECTED' ? 'respinta' : s.outcome === 'SUSPENDED' ? 'in attesa' : 'ridotta'}</span>
          <div className="flex-1 h-4 bg-neutral-900 rounded relative">
            <div className={`absolute inset-y-0 rounded ${s.outcome === 'ADJUSTED' ? 'bg-amber-500/80' : s.outcome === 'SUSPENDED' ? 'bg-sky-500/80' : 'bg-red-500/80'}`}
              style={{ left: `${Math.max(0, after / total) * 100}%`, width: `${Math.max(0.6, (Math.abs(s.delta_eur) / total) * 100)}%` }} />
          </div>
          <span className="w-24 text-right font-mono text-red-300">{fmtEur(s.delta_eur)}</span>
        </div>
      ))}
      <div className="flex items-center gap-2 pt-1 border-t border-neutral-800"><span className="w-40 shrink-0 text-neutral-200 font-semibold">Importo ammesso</span>
        <div className="flex-1 h-4 bg-neutral-900 rounded relative"><div className="absolute inset-y-0 left-0 bg-[#deffac]/80 rounded" style={{ width: `${(item.computed_cost_eur / total) * 100}%` }} /></div>
        <span className="w-24 text-right font-mono text-[#deffac] font-bold">{fmtEur(item.computed_cost_eur)}</span></div>
      {rows.length === 0 && <p className="text-neutral-500 italic">Nessuna riduzione: l’importo è rimasto uguale.</p>}
    </div>
  )
}

function ShareCaps({ caps, active }) {
  if (!caps.length) return <p className="text-xs text-neutral-500 italic">Il bando non pone limiti in percentuale sul totale per questo budget.</p>
  const max = Math.max(...caps.map((c) => c.requested_eur), 1)
  return (
    <div className={`space-y-3 transition-opacity ${active ? 'opacity-100' : 'opacity-40'}`}>
      {caps.map((c) => (
        <div key={c.group} className="space-y-1 text-xs">
          <div className="flex justify-between"><span className="text-neutral-300 font-semibold">{c.group} <span className="font-mono text-[#deffac]">#{c.criterion}</span></span><span className="text-neutral-500">limite {fmtPct(c.cap_pct)} del totale finale ({fmtEur(c.total_final_eur)})</span></div>
          <div className="h-3 bg-neutral-900 rounded relative"><div className="absolute inset-y-0 left-0 bg-neutral-500/60 rounded" style={{ width: `${(c.requested_eur / max) * 100}%` }} /></div>
          <div className="h-3 bg-neutral-900 rounded relative"><div className="absolute inset-y-0 left-0 bg-[#deffac]/80 rounded" style={{ width: `${(c.allowed_eur / max) * 100}%` }} /></div>
          <div className="flex justify-between font-mono text-[11px]"><span className="text-neutral-400">richiesto {fmtEur(c.requested_eur)}</span><span className="text-[#deffac]">ammesso {fmtEur(c.allowed_eur)}</span></div>
        </div>
      ))}
      <p className="text-[11px] text-neutral-500">Questi limiti sono percentuali del totale FINALE, che a sua volta dipende dalle riduzioni: il motore risolve il circolo con una formula esatta, senza tentativi.</p>
    </div>
  )
}

function MerkleTree({ merkle, visible }) {
  if (!merkle) return null
  const { levels, leaf_item_ids: ids } = merkle
  const n = levels[0].length
  const gap = 26, top = 24, lvH = 46, W = Math.max(560, n * gap + 40), H = top + levels.length * lvH + 44
  const xs = [levels[0].map((_, i) => 24 + i * gap)]
  for (let k = 1; k < levels.length; k += 1) {
    xs.push(levels[k].map((_, j) => {
      const a = xs[k - 1][2 * j], b = xs[k - 1][2 * j + 1]
      return b === undefined ? a : (a + b) / 2
    }))
  }
  const y = (k) => H - 40 - k * lvH
  const lines = []
  for (let k = 1; k < levels.length; k += 1) {
    levels[k].forEach((_, j) => {
      [2 * j, 2 * j + 1].forEach((c) => { if (xs[k - 1][c] !== undefined) lines.push(<line key={`${k}-${j}-${c}`} x1={xs[k - 1][c]} y1={y(k - 1)} x2={xs[k][j]} y2={y(k)} stroke="#525252" strokeWidth="1" />) })
    })
  }
  return (
    <div className={`overflow-x-auto transition-opacity duration-700 ${visible ? 'opacity-100' : 'opacity-15'}`}>
      <svg width={W} height={H} role="img" aria-label="Albero di Merkle del budget">
        {lines}
        {levels.map((lvl, k) => lvl.map((h, j) => (
          <g key={`${k}-${j}`}>
            <circle cx={xs[k][j]} cy={y(k)} r={k === levels.length - 1 ? 7 : k === 0 ? 4 : 5} fill={k === levels.length - 1 ? '#deffac' : k === 0 ? '#38bdf8' : '#737373'} />
            {k === 0 && <text x={xs[k][j]} y={y(0) + 10} fontSize="7" fill="#a3a3a3" transform={`rotate(60 ${xs[k][j]} ${y(0) + 10})`}>{ids[j]}</text>}
            {k === levels.length - 1 && <text x={xs[k][j]} y={y(k) - 12} fontSize="9" fontFamily="monospace" textAnchor="middle" fill="#deffac">{h}…</text>}
          </g>
        )))}
      </svg>
      <p className="text-[11px] text-neutral-500">In basso le voci (ognuna con la sua impronta SHA-256); ogni punto sopra è l’impronta dei due punti sotto di lui; uno senza compagno sale così com’è. In cima c’è la Merkle Root: l’impronta di tutto il budget. Cambiare anche 1 € cambia tutto il percorso fino alla radice.</p>
    </div>
  )
}

export default function AlgorithmLab({ validation, title, criteriaTitles = {} }) {
  const nav = useNav()
  const trace = validation?.trace
  const [cursor, setCursor] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState('Normale')
  const [selected, setSelected] = useState(null)
  const timer = useRef(null)

  const ordered = useMemo(() => (trace ? orderSteps(trace.steps) : []), [trace])
  const total = ordered.length + TAIL.length
  const items = validation?.items || []

  const { byKey, posOf, notEval, titles } = useMemo(() => {
    const byKey = new Map(); const posOf = new Map()
    ordered.forEach((s, pos) => { byKey.set(`${s.item_id}:${s.criterion}`, { step: s, pos }); posOf.set(s.seq, pos) })
    const notEval = new Map(items.map((i) => [i.item_id, new Set(i.criteria_not_evaluated)]))
    const titles = { ...criteriaTitles }
    ;(validation?.budget_checks || []).forEach((c) => { titles[c.criterion] = c.title })
    return { byKey, posOf, notEval, titles }
  }, [ordered, items, validation, criteriaTitles])

  useEffect(() => { setCursor(0); setPlaying(false); setSelected(null) }, [validation])
  useEffect(() => {
    if (!playing) return undefined
    timer.current = setInterval(() => {
      setCursor((c) => { if (c >= total) { setPlaying(false); return c } return c + 1 })
    }, SPEEDS[speed])
    return () => clearInterval(timer.current)
  }, [playing, speed, total])

  if (!trace) {
    return (
      <div className="space-y-6">
        <Guide page="lab" />
        <div className="card p-10 text-center space-y-3">
          <p className="text-sm text-neutral-300">Non c’è ancora nulla da mostrare.</p>
          <p className="text-xs text-neutral-500">Vai al Budget, scegli un bando, prova un esempio e premi “Controlla il budget”. Poi torna qui.</p>
          <button onClick={() => nav.go('canvas')} className="btn-primary">Vai al Budget</button>
        </div>
      </div>
    )
  }

  const active = stageOf(cursor, ordered)
  const current = cursor > 0 && cursor <= ordered.length ? ordered[cursor - 1] : null
  const seen = ordered.slice(0, cursor)
  const counts = seen.reduce((a, s) => ({ ...a, [s.outcome]: (a[s.outcome] || 0) + 1 }), {})
  const selItem = items.find((i) => i.item_id === selected) || null
  const selSteps = trace.steps.filter((s) => s.item_id === selected)
  const caption = cursor === 0 ? 'Premi Riproduci per vedere i controlli uno alla volta, nell’ordine reale.'
    : current ? `Voce ${current.item_id} · criterio #${current.criterion} → ${OUTCOME_LABEL[current.outcome]}${current.delta_eur ? ` (${fmtEur(current.delta_eur)})` : ''}. ${current.note}`
      : ['Controlli su tutto il budget: altri contributi, de minimis, liquidità, variazioni tra capitoli.', 'Ogni voce riceve la sua impronta (SHA-256).', 'Le impronte si uniscono a coppie fino a una sola: la Merkle Root.', 'Riassunto scritto: ogni cifra è confrontata con i risultati veri.'][cursor - ordered.length - 1]

  return (
    <div className="space-y-6">
      <Guide page="lab" />

      <div className="card p-4 space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <button onClick={() => { if (cursor >= total) setCursor(0); setPlaying(!playing) }} className="btn-primary flex items-center gap-1.5">{playing ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}{playing ? 'Pausa' : cursor >= total ? 'Riavvia' : 'Riproduci'}</button>
          <button onClick={() => { setPlaying(false); setCursor(0) }} title="Da capo" aria-label="Da capo" className="btn !px-2"><RotateCcw className="w-3.5 h-3.5" /></button>
          <button onClick={() => { setPlaying(false); setCursor(total) }} title="Vai alla fine" aria-label="Vai alla fine" className="btn !px-2"><ChevronsRight className="w-3.5 h-3.5" /></button>
          <select value={speed} onChange={(e) => setSpeed(e.target.value)} aria-label="Velocità" className="field !w-auto">{Object.keys(SPEEDS).map((s) => <option key={s}>{s}</option>)}</select>
          <input type="range" min="0" max={total} value={cursor} onChange={(e) => { setPlaying(false); setCursor(Number(e.target.value)) }} className="flex-1 min-w-[140px] accent-[#deffac]" />
          <span className="font-mono text-xs text-neutral-400">{cursor}/{total}</span>
          <Hint id="lab_player" />
        </div>
        <p className="text-xs text-neutral-300 min-h-[2.5rem] leading-relaxed">{caption}</p>
        <div className="flex flex-wrap gap-4 text-xs font-mono">
          <span className="text-emerald-300">{counts.PASS || 0} superati</span><span className="text-amber-300">{counts.ADJUSTED || 0} ridotti</span>
          <span className="text-red-300">{counts.REJECTED || 0} respinti</span><span className="text-sky-300">{counts.SUSPENDED || 0} in attesa di documento</span>
          <span className="text-neutral-500">{ordered.length} controlli in totale</span>
        </div>
      </div>

      <div className="card p-4 space-y-3">
        <span className="label inline-flex items-center gap-1.5">1 · Le fasi <Hint id="lab_fasi" /></span>
        <Pipeline stages={trace.stages} active={active} />
      </div>

      <div className="card p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2"><span className="label inline-flex items-center gap-1.5">2 · Mappa dei 60 controlli (una riga per voce) <Hint id="lab_mappa" /></span>
          <span className="text-xs text-neutral-500">{items.length} voci · 60 controlli</span></div>
        <Heatmap items={items} byKey={byKey} notEval={notEval} budgetChecks={validation.budget_checks || []} cursor={cursor} stepsLen={ordered.length} selected={selected} onSelect={setSelected} titles={titles} />
        <div className="flex flex-wrap gap-3 text-[11px] text-neutral-400">
          {Object.entries(CELL).map(([k, c]) => <span key={k}><span className="inline-block w-2.5 h-2.5 rounded-sm mr-1" style={{ background: c }} />{OUTCOME_LABEL[k]}</span>)}
          <span><span className="inline-block w-2.5 h-2.5 rounded-sm mr-1 border border-dashed border-neutral-500" />non valutato</span>
          <span><span className="inline-block w-2.5 h-2.5 rounded-sm mr-1 bg-[#0b0b0b] border border-neutral-800" />non pertinente</span>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="card p-4 space-y-3">
          <span className="label inline-flex items-center gap-1.5">3 · Come scende l’importo {selItem ? `— ${selItem.item_id}` : ''} <Hint id="lab_cascata" /></span>
          {selItem && <p className="text-xs text-neutral-400">{selItem.description}</p>}
          <Waterfall item={selItem} steps={selSteps} cursorPos={cursor} orderedIndex={(s) => posOf.get(s.seq) ?? 0} />
        </div>
        <div className="card p-4 space-y-3">
          <span className="label inline-flex items-center gap-1.5">4 · Limiti in percentuale sul totale <Hint id="lab_limiti" /></span>
          <ShareCaps caps={trace.share_caps} active={cursor > ordered.length - trace.steps.filter((s) => s.stage === 'SHARE_CAPS').length} />
        </div>
      </div>

      <div className="card p-4 space-y-3">
        <span className="label inline-flex items-center gap-1.5">5 · L’impronta del budget (Merkle Root) <Hint id="lab_merkle" /></span>
        <MerkleTree merkle={trace.merkle} visible={cursor >= ordered.length + 3} />
        <p className="font-mono text-xs text-[#deffac] break-all">{validation.merkle_root} · {validation.cep_id}</p>
        <button type="button" onClick={() => nav.go('guida', 'merkle')} className="text-xs text-[#deffac] hover:underline">Come nasce questa impronta? Guarda la spiegazione passo passo →</button>
      </div>
    </div>
  )
}
