import React, { useState } from 'react'
import { BarChart3 } from 'lucide-react'
import { api } from '../lib/api'
import { SEED_PATTERN } from '../data/mockSeed'

const FIELDS = [
  ['personnel_pct', 'Personale'],
  ['assets_pct', 'Beni strumentali'],
  ['consulting_pct', 'Consulenze'],
  ['overhead_pct', 'Spese generali'],
]

export default function PatternDemo() {
  const [draft, setDraft] = useState(SEED_PATTERN)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const run = async () => {
    setLoading(true); setError(null)
    try { setResult(await api.matchPattern({ bando_category: 'TRANSIZIONE_5.0', draft_budget: draft })) }
    catch (e) { setError(e.message); setResult(null) }
    finally { setLoading(false) }
  }

  return (
    <div className="card p-6 space-y-5">
      <div className="pb-3 border-b border-neutral-800">
        <h3 className="font-bold text-lg flex items-center gap-2"><BarChart3 className="w-5 h-5 text-[#deffac]" />Demo comparativa — Pattern Matching</h3>
        <p className="text-xs text-neutral-400 mt-0.5">Similarità del coseno tra il budget bozza e gli archetipi (illustrativi) di budget premiati. Non stima la probabilità di vincita.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {FIELDS.map(([key, label]) => (
          <label key={key} className="space-y-1"><span className="label">{label} (quota 0-1)</span>
            <input type="number" min="0" max="1" step="0.01" value={draft[key]}
              onChange={(e) => setDraft({ ...draft, [key]: Number(e.target.value) })}
              className="w-full bg-neutral-950 border border-neutral-800 rounded-xl px-3 py-2 font-mono text-xs" /></label>
        ))}
      </div>
      <button onClick={run} disabled={loading} className="btn-primary">{loading ? 'Calcolo similarità…' : 'Confronta con pattern vincenti'}</button>
      {error && <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-xs">{error}</div>}

      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-neutral-950 border border-neutral-800 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <span className="label">Archetipo più vicino</span>
              <span className="text-xs font-mono px-2 py-0.5 bg-[#deffac]/10 text-[#deffac] rounded border border-[#deffac]/20">Coseno: {result.similarity_score.toFixed(2)}</span>
            </div>
            <div className="text-2xl font-black">{result.closest_archetype}</div>
            <p className="text-xs text-neutral-300 leading-relaxed bg-neutral-900 p-3 rounded-lg border border-neutral-800">{result.recommendation}</p>
            <div className="p-3 rounded-lg border border-amber-500/30 bg-amber-500/10 text-amber-300 text-xs">
              Scostamento principale: <strong>{result.main_deviation.category}</strong> ({result.main_deviation.deviation_points > 0 ? '+' : ''}{result.main_deviation.deviation_points} pp)
            </div>
          </div>
          <div className="bg-neutral-950 border border-neutral-800 rounded-xl p-5 space-y-3">
            <span className="label">Archetipo (media vincenti) vs tua bozza</span>
            {FIELDS.map(([key, label]) => (
              <div key={key} className="space-y-1 text-xs">
                <div className="flex justify-between font-mono"><span className="text-neutral-400">{label}</span><span className="text-[#deffac]">{Math.round(result.archetype_averages[key] * 100)}% · tu {Math.round(draft[key] * 100)}%</span></div>
                <div className="h-2 bg-neutral-900 rounded-full overflow-hidden relative">
                  <div className="absolute inset-y-0 left-0 bg-[#deffac]/40" style={{ width: `${result.archetype_averages[key] * 100}%` }} />
                  <div className="absolute inset-y-0 left-0 border-r-2 border-amber-400" style={{ width: `${Math.min(draft[key], 1) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
