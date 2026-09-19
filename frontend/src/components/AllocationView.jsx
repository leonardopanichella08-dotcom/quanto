import React, { useCallback, useEffect, useRef, useState } from 'react'
import { CalendarRange } from 'lucide-react'
import { api } from '../lib/api'
import { fmtEur, fmtNum } from '../lib/format'
import { SEED_ALLOCATION } from '../data/mockSeed'

const TARGETS = [
  ['MINIMIZE_NET_COST', 'Minimizzare la spesa netta'],
  ['MAXIMIZE_COVERED_ITEMS', 'Massimizzare le voci coperte'],
  ['MINIMIZE_FUNDS_INVOLVED', 'Minimizzare il numero di fonti'],
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
      <div className="card p-6 space-y-4">
        <div className="pb-3 border-b border-neutral-800 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="font-bold text-lg flex items-center gap-2"><CalendarRange className="w-5 h-5 text-[#deffac]" />Allocazione annuale multi-fonte (Missione Due)</h3>
            <p className="text-xs text-neutral-400 mt-0.5">Ottimizzazione vincolata (MILP) su tetti di fondo, massimali per categoria, non cumulabilità e plafond de minimis.</p>
          </div>
          <select value={target} onChange={(e) => setTarget(e.target.value)} className="bg-neutral-950 border border-neutral-700 rounded-xl px-3 py-2 text-xs">
            {TARGETS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </div>

        <div className="flex flex-wrap gap-2 items-center">
          <span className="label mr-2">What-if: escludi fonte</span>
          {SEED_ALLOCATION.available_funding_lines.map((f) => (
            <button key={f.fund_id} onClick={() => toggle(f.fund_id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${excluded.includes(f.fund_id) ? 'border-red-500/40 bg-red-500/10 text-red-300 line-through' : 'border-neutral-700 text-neutral-300 hover:border-neutral-500'}`}>
              {f.name}
            </button>
          ))}
        </div>
        {error && <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-xs">{error}</div>}
      </div>

      {plan && (
        <>
          <div className={`grid grid-cols-2 md:grid-cols-4 gap-4 transition ${loading ? 'opacity-50' : ''}`}>
            {[['Spesa lorda', fmtEur(plan.total_gross_expense_eur), 'text-neutral-100'],
              ['Coperta da fondi', fmtEur(plan.covered_by_public_funds_eur), 'text-emerald-400'],
              ['Netto a carico ente', fmtEur(plan.net_cost_to_entity_eur), 'text-amber-400'],
              ['Copertura', `${fmtNum(plan.overall_coverage_percentage, 1)}%`, 'text-[#deffac]']].map(([l, v, tone]) => (
              <div key={l} className="card p-5"><span className="label">{l}</span><div className={`text-xl font-bold font-mono mt-2 ${tone}`}>{v}</div></div>
            ))}
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 card p-6 space-y-3">
              <span className="label">Piano per voce</span>
              {plan.allocation_plan.map((l) => (
                <div key={l.item_id} className="p-4 bg-neutral-950 border border-neutral-800 rounded-xl text-xs space-y-2">
                  <div className="flex justify-between font-mono"><span className="font-semibold text-sm font-sans">{l.item_id} <span className="text-neutral-500">· {l.category}</span></span><span>{fmtEur(l.gross_amount_eur)}</span></div>
                  {l.coverage.length ? l.coverage.map((c) => (
                    <div key={c.fund_id} className="flex justify-between text-emerald-300 font-mono"><span>{c.fund_id}</span><span>{fmtEur(c.covered_amount_eur)} ({fmtNum(c.coverage_percentage, 1)}%)</span></div>
                  )) : <div className="text-neutral-500">Nessuna fonte compatibile: a carico diretto dell’ente</div>}
                  <div className="flex justify-between text-amber-300 font-mono border-t border-neutral-800 pt-2"><span>Netto ente</span><span>{fmtEur(l.net_cost_to_entity_eur)}</span></div>
                </div>
              ))}
            </div>

            <div className="space-y-6">
              <div className="card p-6 space-y-3">
                <span className="label">Utilizzo fondi</span>
                {plan.fund_usage.map((u) => (
                  <div key={u.fund_id} className="text-xs font-mono space-y-0.5">
                    <div className="flex justify-between"><span className="text-neutral-300">{u.fund_id}</span><span>{fmtEur(u.used_eur)}</span></div>
                    <div className="text-neutral-500">{u.cap_eur != null ? `dotazione ${fmtEur(u.cap_eur)} · margine ${fmtNum(u.safety_margin_pct, 1)}%` : 'nessun tetto di dotazione'}</div>
                  </div>
                ))}
                {plan.de_minimis_residual_eur != null && (
                  <div className="text-xs font-mono pt-2 border-t border-neutral-800 text-neutral-400">De minimis usato {fmtEur(plan.de_minimis_used_eur)} · residuo {fmtEur(plan.de_minimis_residual_eur)}</div>
                )}
              </div>
              <div className="card p-6 space-y-2">
                <span className="label">Timeline 12 mesi</span>
                <div className="flex items-end gap-1 h-28">
                  {plan.monthly_plan.map((m) => (
                    <div key={m.month} className="flex-1 flex flex-col justify-end h-full" title={`Mese ${m.month}: lordo ${fmtEur(m.gross_eur)}, coperto ${fmtEur(m.covered_eur)}`}>
                      <div className="bg-amber-400/70" style={{ height: `${(m.net_eur / maxMonth) * 100}%` }} />
                      <div className="bg-emerald-400/70" style={{ height: `${(m.covered_eur / maxMonth) * 100}%` }} />
                    </div>
                  ))}
                </div>
                <div className="flex justify-between text-[10px] text-neutral-500 font-mono"><span>Gen</span><span>Dic</span></div>
                <p className="text-[10px] text-neutral-500"><span className="text-emerald-400">■</span> coperto <span className="text-amber-400 ml-2">■</span> netto ente</p>
              </div>
            </div>
          </div>
          <p className="text-[11px] text-neutral-500 font-mono">{plan.summary} · {plan.solver} · {plan.status}</p>
        </>
      )}
    </div>
  )
}
