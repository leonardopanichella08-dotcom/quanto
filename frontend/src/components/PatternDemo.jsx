import React, { useEffect, useMemo, useRef, useState } from 'react'
import { AlertTriangle, GitCompare } from 'lucide-react'
import { api } from '../lib/api'
import { SectionTitle } from './ui'
import Guide from './Guide'
import { Hint } from './Help'

const FIELDS = [
  ['personnel_pct', 'Personale'], ['assets_pct', 'Beni strumentali'], ['consulting_pct', 'Consulenze'],
  ['overhead_pct', 'Spese generali'], ['training_pct', 'Formazione'], ['communication_pct', 'Comunicazione'],
]
const BY_CATEGORY = { PERSONNEL: 'personnel_pct', CAPITAL_ASSETS: 'assets_pct', CONSULTING: 'consulting_pct', OVERHEAD: 'overhead_pct', TRAINING: 'training_pct' }
const EMPTY = Object.fromEntries(FIELDS.map(([k]) => [k, 0]))

/** Quote del budget corrente (importi ammessi dal server, ripartiti per categoria): sono rapporti tra importi già calcolati, non un calcolo economico. */
function sharesOf(validation) {
  if (!validation?.items?.length) return null
  const tot = {}
  validation.items.forEach((i) => { const k = BY_CATEGORY[i.category]; if (k) tot[k] = (tot[k] || 0) + i.computed_cost_eur })
  const sum = Object.values(tot).reduce((a, b) => a + b, 0)
  if (!sum) return null
  return Object.fromEntries(FIELDS.map(([k]) => [k, Math.round(((tot[k] || 0) / sum) * 1000) / 1000]))
}

export default function PatternDemo({ bando, validation }) {
  const [cats, setCats] = useState(null)
  const [category, setCategory] = useState('')
  const [draft, setDraft] = useState(EMPTY)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const seq = useRef(0)
  const mine = useMemo(() => sharesOf(validation), [validation])
  const sum = FIELDS.reduce((s, [k]) => s + (Number(draft[k]) || 0), 0)

  useEffect(() => { api.patternCategories().then((c) => { setCats(c); if (c.length) setCategory((x) => x || c[0].bando_category) }).catch((e) => setError(e.message)) }, [])

  // Ogni modifica (anche di un solo importo) rilancia il confronto sul server dopo una breve pausa: simulazione di correzione in tempo reale.
  useEffect(() => {
    if (!category || sum <= 0) { setResult(null); return undefined }
    const t = setTimeout(async () => {
      const id = ++seq.current
      setLoading(true); setError(null)
      try {
        const r = await api.matchPattern({ bando_category: category, bando_id: bando?.bando_id, draft_budget: draft })
        if (id === seq.current) setResult(r)
      } catch (e) { if (id === seq.current) { setError(e.message); setResult(null) } } finally { if (id === seq.current) setLoading(false) }
    }, 450)
    return () => clearTimeout(t)
  }, [category, draft, sum, bando])

  const empty = cats && cats.length === 0
  return (
    <div className="space-y-6">
      <Guide page="pattern" />
      <div className="card p-6 space-y-5">
        <div className="pb-3 border-b border-line">
          <SectionTitle icon={GitCompare} className="!text-lg">Il tuo budget somiglia a quelli premiati?</SectionTitle>
          <p className="text-xs text-ink-2 mt-0.5 leading-relaxed">Confronta come ripartisci la spesa con i budget storici di bandi comparabili (graduatorie pubbliche e dati del pilota, con la fonte di ciascuno). Non stima la probabilità di vincere: misura una distanza.</p>
        </div>

        {empty && (
          <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/5 text-xs text-amber-800 flex gap-2"><AlertTriangle className="w-4 h-4 shrink-0" />
            <span>La banca dati dei budget storici è ancora vuota, quindi non ho nulla con cui confrontarti. Un manager può importarla dal Quartier Generale (sezione «Banca pattern»). Non mostro budget «tipo» inventati.</span></div>
        )}

        {cats && cats.length > 0 && (
          <>
            <div className="flex flex-wrap items-end gap-4">
              <label className="space-y-1 text-xs text-ink-2"><span className="label">Categoria di bandi con cui confrontarti <Hint id="pattern_input" /></span>
                <select className="field !w-auto" value={category} onChange={(e) => setCategory(e.target.value)}>
                  {cats.map((c) => <option key={c.bando_category} value={c.bando_category}>{c.bando_category} — {c.budgets} budget, {c.archetypes} archetipi</option>)}</select></label>
              {mine && <button className="btn" onClick={() => setDraft(mine)}>Usa il budget che ho controllato</button>}
              {bando && <span className="text-xs text-mute">Tetti letti dal bando in uso: {bando.name}</span>}
            </div>
            <div className="space-y-2">
              <span className="label">La tua ripartizione (quote da 0 a 1: cambiale e il confronto si aggiorna da solo)</span>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {FIELDS.map(([key, label]) => (
                  <label key={key} className="space-y-1"><span className="text-xs text-ink-2">{label}</span>
                    <input type="number" min="0" max="1" step="0.01" value={draft[key]} onChange={(e) => setDraft({ ...draft, [key]: Number(e.target.value) })} className="field tabular-nums" /></label>
                ))}
              </div>
              <p className="text-xs text-mute">Somma delle quote: <span className={`tabular-nums ${Math.abs(sum - 1) < 0.005 ? 'text-emerald-700' : 'text-amber-700'}`}>{sum.toFixed(2).replace('.', ',')}</span> (il server le riporta comunque a 1).</p>
            </div>
          </>
        )}
        {error && <div className="p-3 rounded-xl border border-red-500/30 text-red-700 text-xs">{error}</div>}

        {result && (
          <div className={`grid grid-cols-1 lg:grid-cols-2 gap-6 transition ${loading ? 'opacity-60' : ''}`}>
            <div className="bg-field border border-line rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between gap-3">
                <span className="label inline-flex items-center gap-1.5">Il budget tipo più simile <Hint id="pattern_risultato" /></span>
                <span className="text-xs tabular-nums px-2 py-0.5 text-brand-ink rounded border border-brand/40">somiglianza {result.similarity_score.toFixed(2).replace('.', ',')}</span>
              </div>
              <div className="text-2xl font-semibold">{result.closest_archetype}</div>
              <p className="text-xs text-ink-2 leading-relaxed p-3 rounded-lg border border-line">{result.recommendation}</p>
              <div className="p-3 rounded-lg border border-amber-500/30 text-amber-800 text-xs">
                Dove ti discosti di più: <strong>{result.main_deviation.category}</strong> ({result.deviations_pp[result.main_deviation.category] > 0 ? '+' : ''}{result.deviations_pp[result.main_deviation.category]} punti percentuali){result.main_deviation.note ? ` — ${result.main_deviation.note}` : ''}.
              </div>
              <p className="text-[11px] text-mute">Archetipo da {result.archetype.members} budget · {result.archetype.method}{result.archetype.score_min != null ? ` · punteggi storici da ${result.archetype.score_min} a ${result.archetype.score_max} (indicazione statistica)` : ''}.</p>
              {validation && <p className="text-[11px] text-mute">Il tuo Conformity Score sul budget controllato: <strong className="text-ink">{validation.conformity_score}/100</strong>.</p>}
            </div>
            <div className="bg-field border border-line rounded-xl p-5 space-y-3">
              <span className="label">Budget tipo (chiaro) contro il tuo (linea gialla)</span>
              {FIELDS.map(([key, label]) => (
                <div key={key} className="space-y-1 text-xs">
                  <div className="flex justify-between gap-3 tabular-nums"><span className="text-ink-2">{label}</span><span className="text-brand-ink">tipo {(result.archetype_averages[key] * 100).toFixed(1)}% · tu {(sum ? (draft[key] / sum) * 100 : 0).toFixed(1)}%</span></div>
                  <div className="h-2 bg-tint rounded-full overflow-hidden relative">
                    <div className="absolute inset-y-0 left-0 bg-brand/40" style={{ width: `${result.archetype_averages[key] * 100}%` }} />
                    <div className="absolute inset-y-0 left-0 border-r-2 border-amber-400" style={{ width: `${sum ? Math.min(draft[key] / sum, 1) * 100 : 0}%` }} />
                  </div>
                </div>
              ))}
            </div>
            <div className="lg:col-span-2 space-y-2">
              <span className="label">I {result.nearest_budgets.length} budget storici più simili al tuo</span>
              <ul className="space-y-1 text-xs">
                {result.nearest_budgets.map((b, i) => (
                  <li key={i} className="flex flex-wrap items-center gap-2 p-2 rounded-lg border border-line">
                    <span className="tabular-nums text-brand-ink w-12">{(b.similarity * 100).toFixed(1)}%</span>
                    <span className="text-ink">{b.source_url ? <a href={b.source_url} target="_blank" rel="noreferrer" className="hover:underline">{b.source}</a> : b.source}</span>
                    <span className="text-mute">{b.year || ''}{b.score != null ? ` · punteggio ${b.score}` : ''}</span>
                    <span className="ml-auto text-mute tabular-nums">{FIELDS.map(([k]) => `${Math.round(b.shares[k] * 100)}`).join(' / ')} %</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
