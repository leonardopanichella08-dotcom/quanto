import React, { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import { fmtEur, fmtNum } from '../lib/format'
import { SEED_ALLOCATION } from '../data/mockSeed'
import Guide from './Guide'
import { Hint } from './Help'

const PALETTE = ['#38bdf8', '#a78bfa', '#f472b6', '#34d399', '#fbbf24', '#fb7185']

/** Flusso delle spese verso i fondi: lo spessore è proporzionale all'importo coperto (dati del solver, nessun calcolo qui). */
function Sankey({ plan }) {
  const items = plan.allocation_plan
  const funds = plan.fund_usage.filter((f) => f.used_eur > 0)
  const gross = items.reduce((s, i) => s + i.gross_amount_eur, 0) || 1
  const W = 700, H = Math.max(240, items.length * 46), gap = 10, X0 = 150, X1 = W - 170
  const scale = (H - gap * Math.max(items.length, funds.length + 1)) / gross
  const leftY = {}
  let y = 0
  items.forEach((i) => { leftY[i.item_id] = y; y += i.gross_amount_eur * scale + gap })
  const rightNodes = [...funds.map((f, k) => ({ id: f.fund_id, total: f.used_eur, color: PALETTE[k % PALETTE.length] })),
    { id: 'CARICO ENTE', total: plan.net_cost_to_entity_eur, color: '#f59e0b' }]
  const rightY = {}
  y = 0
  rightNodes.forEach((n) => { rightY[n.id] = y; y += n.total * scale + gap })
  const offL = {}, offR = {}
  const links = []
  items.forEach((i) => {
    const parts = [...i.coverage.map((c) => ({ to: c.fund_id, amount: c.covered_amount_eur })), { to: 'CARICO ENTE', amount: i.net_cost_to_entity_eur }].filter((p) => p.amount > 0)
    parts.forEach((p) => {
      const h = p.amount * scale
      const y0 = leftY[i.item_id] + (offL[i.item_id] || 0), y1 = rightY[p.to] + (offR[p.to] || 0)
      offL[i.item_id] = (offL[i.item_id] || 0) + h; offR[p.to] = (offR[p.to] || 0) + h
      const node = rightNodes.find((n) => n.id === p.to)
      links.push(<path key={`${i.item_id}-${p.to}`} d={`M${X0},${y0 + h / 2} C${(X0 + X1) / 2},${y0 + h / 2} ${(X0 + X1) / 2},${y1 + h / 2} ${X1},${y1 + h / 2}`} stroke={node?.color || '#737373'} strokeOpacity="0.45" strokeWidth={Math.max(1, h)} fill="none"><title>{`${i.item_id} → ${p.to}: ${fmtEur(p.amount)}`}</title></path>)
    })
  })
  return (
    <div className="overflow-x-auto"><svg width={W} height={H + 10} role="img" aria-label="Flusso delle spese verso i fondi">
      {links}
      {items.map((i) => <g key={i.item_id}><rect x={X0 - 6} y={leftY[i.item_id]} width="6" height={Math.max(2, i.gross_amount_eur * scale)} fill="#a3a3a3" /><text x={X0 - 12} y={leftY[i.item_id] + Math.max(2, i.gross_amount_eur * scale) / 2 + 3} fontSize="10" fontFamily="monospace" textAnchor="end" fill="#d4d4d4">{i.item_id}</text></g>)}
      {rightNodes.map((n) => <g key={n.id}><rect x={X1} y={rightY[n.id]} width="6" height={Math.max(2, n.total * scale)} fill={n.color} /><text x={X1 + 12} y={rightY[n.id] + Math.max(2, n.total * scale) / 2 + 3} fontSize="10" fontFamily="monospace" fill="#d4d4d4">{n.id.length > 22 ? `${n.id.slice(0, 21)}…` : n.id}</text></g>)}
    </svg></div>
  )
}

const TARGETS = [
  ['MINIMIZE_NET_COST', 'Pagare il meno possibile di tasca propria'],
  ['MAXIMIZE_COVERED_ITEMS', 'Coprire più spese possibile'],
  ['MINIMIZE_FUNDS_INVOLVED', 'Usare meno fondi possibile'],
]

export default function AllocationView() {
  const [target, setTarget] = useState('MINIMIZE_NET_COST')
  const [excluded, setExcluded] = useState([])
  const [plan, setPlan] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const seq = useRef(0)

  // Ogni cambio di obiettivo o di esclusione (what-if) rilancia il risolutore sul server.
  const run = useCallback(async () => {
    const mine = ++seq.current
    setLoading(true); setError(null)
    try {
      const res = await api.optimizeAllocation({ ...SEED_ALLOCATION, optimization_target: target, excluded_funds: excluded })
      if (mine === seq.current) setPlan(res)
    } catch (e) {
      if (mine === seq.current) { setError(e.message); setPlan(null) }
    } finally {
      if (mine === seq.current) setLoading(false)
    }
  }, [target, excluded])

  useEffect(() => { run() }, [run])

  const toggle = (id) => setExcluded((ex) => (ex.includes(id) ? ex.filter((x) => x !== id) : [...ex, id]))
  const maxMonth = plan ? Math.max(...plan.monthly_plan.map((m) => m.gross_eur), 1) : 1

  return (
    <div className="space-y-6">
      <Guide page="allocation" />
      <div className="card p-6 space-y-4">
        <div className="pb-3 border-b border-neutral-800 flex flex-wrap items-center justify-between gap-3">
          <div className="max-w-xl">
            <h3 className="font-semibold text-lg">Chi paga cosa, nell’anno</h3>
            <p className="text-xs text-neutral-400 mt-0.5 leading-relaxed">Il programma prova le combinazioni possibili e sceglie la migliore, rispettando i tetti dei fondi, i limiti per categoria, i fondi che non si possono cumulare e il limite de minimis.</p>
          </div>
          <label className="flex items-center gap-2 text-xs text-neutral-400 w-full md:w-auto min-w-0">Obiettivo <Hint id="alloc_obiettivo" />
            <select value={target} onChange={(e) => setTarget(e.target.value)} className="field !w-full md:!w-auto min-w-0">
              {TARGETS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </label>
        </div>

        <div className="flex flex-wrap gap-2 items-center">
          <span className="label mr-1 inline-flex items-center gap-1.5">Prova a togliere un fondo <Hint id="alloc_whatif" /></span>
          {SEED_ALLOCATION.available_funding_lines.map((f) => (
            <button key={f.fund_id} onClick={() => toggle(f.fund_id)} aria-pressed={excluded.includes(f.fund_id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${excluded.includes(f.fund_id) ? 'border-red-500/40 text-red-300 line-through' : 'border-neutral-700 text-neutral-300 hover:border-neutral-500'}`}>
              {f.name}
            </button>
          ))}
        </div>
        {error && <div className="p-3 rounded-xl border border-red-500/30 text-red-300 text-xs">{error}</div>}
      </div>

      {plan && (
        <>
          <div className={`grid grid-cols-2 md:grid-cols-4 gap-4 transition ${loading ? 'opacity-50' : ''}`}>
            {[['Spesa totale', fmtEur(plan.total_gross_expense_eur), 'text-neutral-100'],
              ['Coperta dai fondi', fmtEur(plan.covered_by_public_funds_eur), 'text-emerald-400'],
              ['A carico dell’ente', fmtEur(plan.net_cost_to_entity_eur), 'text-amber-400'],
              ['Quota coperta', `${fmtNum(plan.overall_coverage_percentage, 1)}%`, 'text-[#deffac]']].map(([l, v, tone]) => (
              <div key={l} className="card p-5 min-w-0"><span className="label">{l}</span><div className={`text-base sm:text-xl font-semibold font-mono mt-2 break-all ${tone}`}>{v}</div></div>
            ))}
          </div>

          <div className="card p-6 space-y-3"><span className="label inline-flex items-center gap-1.5">Da dove arrivano i soldi, spesa per spesa <Hint id="alloc_flusso" /></span><Sankey plan={plan} /></div>

          <div className="grid lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 card p-6 space-y-3">
              <span className="label">Il piano, voce per voce</span>
              {plan.allocation_plan.map((l) => (
                <div key={l.item_id} className="p-4 bg-neutral-950 border border-neutral-800 rounded-xl text-xs space-y-2">
                  <div className="flex justify-between gap-3 font-mono"><span className="font-medium text-sm font-sans min-w-0 break-words">{l.item_id} <span className="text-neutral-500">· {l.category}</span></span><span>{fmtEur(l.gross_amount_eur)}</span></div>
                  {l.coverage.length ? l.coverage.map((c) => (
                    <div key={c.fund_id} className="flex justify-between gap-3 text-emerald-300 font-mono"><span className="min-w-0 break-words">{c.fund_id}</span><span className="shrink-0">{fmtEur(c.covered_amount_eur)} ({fmtNum(c.coverage_percentage, 1)}%)</span></div>
                  )) : <div className="text-neutral-500">Nessun fondo adatto: la paga direttamente l’ente</div>}
                  <div className="flex justify-between text-amber-300 font-mono border-t border-neutral-800 pt-2"><span>A carico dell’ente</span><span>{fmtEur(l.net_cost_to_entity_eur)}</span></div>
                </div>
              ))}
            </div>

            <div className="space-y-6">
              <div className="card p-6 space-y-3">
                <span className="label inline-flex items-center gap-1.5">Quanto si usa di ogni fondo <Hint id="alloc_uso" /></span>
                {plan.fund_usage.map((u) => (
                  <div key={u.fund_id} className="text-xs font-mono space-y-0.5">
                    <div className="flex justify-between gap-3"><span className="text-neutral-300 min-w-0 break-words">{u.fund_id}</span><span>{fmtEur(u.used_eur)}</span></div>
                    <div className="text-neutral-500">{u.cap_eur != null ? `disponibili ${fmtEur(u.cap_eur)} · margine ${fmtNum(u.safety_margin_pct, 1)}%` : 'nessun limite di importo'}</div>
                  </div>
                ))}
                {plan.de_minimis_residual_eur != null && (
                  <div className="text-xs font-mono pt-2 border-t border-neutral-800 text-neutral-400">De minimis usato {fmtEur(plan.de_minimis_used_eur)} · ancora disponibile {fmtEur(plan.de_minimis_residual_eur)}</div>
                )}
              </div>
              <div className="card p-6 space-y-2">
                <span className="label inline-flex items-center gap-1.5">Mese per mese <Hint id="alloc_mesi" /></span>
                <div className="flex items-end gap-1 h-28">
                  {plan.monthly_plan.map((m) => (
                    <div key={m.month} className="flex-1 flex flex-col justify-end h-full" title={`Mese ${m.month}: totale ${fmtEur(m.gross_eur)}, coperto ${fmtEur(m.covered_eur)}`}>
                      <div className="bg-amber-400/70" style={{ height: `${(m.net_eur / maxMonth) * 100}%` }} />
                      <div className="bg-emerald-400/70" style={{ height: `${(m.covered_eur / maxMonth) * 100}%` }} />
                    </div>
                  ))}
                </div>
                <div className="flex justify-between text-[11px] text-neutral-500 font-mono"><span>Gen</span><span>Dic</span></div>
                <p className="text-[11px] text-neutral-500"><span className="text-emerald-400">■</span> coperto dai fondi <span className="text-amber-400 ml-2">■</span> a carico dell’ente</p>
              </div>
            </div>
          </div>
          <p className="text-[11px] text-neutral-600 font-mono break-words">Dettagli tecnici: {plan.summary} · {plan.solver} · {plan.status}</p>
        </>
      )}
    </div>
  )
}
