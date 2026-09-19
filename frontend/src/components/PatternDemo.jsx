import React, { useState } from 'react'
import { api } from '../lib/api'
import { SEED_PATTERN } from '../data/mockSeed'
import Guide from './Guide'
import { Hint } from './Help'

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
    <div className="space-y-6">
      <Guide page="pattern" />
      <div className="card p-6 space-y-5">
        <div className="pb-3 border-b border-neutral-800">
          <h3 className="font-semibold text-lg">Il tuo budget somiglia a quelli premiati?</h3>
          <p className="text-xs text-neutral-400 mt-0.5 leading-relaxed">Confronta come ripartisci il budget tra le categorie con budget “tipo” (esempi illustrativi). Non stima la probabilità di vincere.</p>
        </div>

        <div className="space-y-2">
          <span className="label inline-flex items-center gap-1.5">La tua ripartizione (da 0 a 1) <Hint id="pattern_input" /></span>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {FIELDS.map(([key, label]) => (
              <label key={key} className="space-y-1"><span className="text-xs text-neutral-400">{label}</span>
                <input type="number" min="0" max="1" step="0.01" value={draft[key]}
                  onChange={(e) => setDraft({ ...draft, [key]: Number(e.target.value) })}
                  className="field font-mono" /></label>
            ))}
          </div>
          <p className="text-xs text-neutral-500">Somma delle quote: <span className={`font-mono ${Math.abs(FIELDS.reduce((s, [k]) => s + draft[k], 0) - 1) < 0.005 ? 'text-emerald-300' : 'text-amber-300'}`}>{FIELDS.reduce((s, [k]) => s + draft[k], 0).toFixed(2)}</span> (dovrebbe fare 1)</p>
        </div>
        <button onClick={run} disabled={loading} className="btn-primary">{loading ? 'Confronto in corso…' : 'Confronta'}</button>
        {error && <div className="p-3 rounded-xl border border-red-500/30 text-red-300 text-xs">{error}</div>}

        {result && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-neutral-950 border border-neutral-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between gap-3">
                <span className="label inline-flex items-center gap-1.5">Il budget tipo più simile <Hint id="pattern_risultato" /></span>
                <span className="text-xs font-mono px-2 py-0.5 text-[#deffac] rounded border border-[#deffac]/30">somiglianza {result.similarity_score.toFixed(2).replace('.', ',')}</span>
              </div>
              <div className="text-2xl font-semibold">{result.closest_archetype}</div>
              <p className="text-xs text-neutral-300 leading-relaxed p-3 rounded-lg border border-neutral-800">{result.recommendation}</p>
              <div className="p-3 rounded-lg border border-amber-500/30 text-amber-200 text-xs">
                Dove ti discosti di più: <strong>{result.main_deviation.category}</strong> ({result.main_deviation.deviation_points > 0 ? '+' : ''}{result.main_deviation.deviation_points} punti percentuali)
              </div>
            </div>
            <div className="bg-neutral-950 border border-neutral-800 rounded-xl p-5 space-y-3">
              <span className="label">Budget tipo (chiaro) contro il tuo (linea gialla)</span>
              {FIELDS.map(([key, label]) => (
                <div key={key} className="space-y-1 text-xs">
                  <div className="flex justify-between gap-3 font-mono"><span className="text-neutral-400">{label}</span><span className="text-[#deffac]">tipo {Math.round(result.archetype_averages[key] * 100)}% · tu {Math.round(draft[key] * 100)}%</span></div>
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
    </div>
  )
}
