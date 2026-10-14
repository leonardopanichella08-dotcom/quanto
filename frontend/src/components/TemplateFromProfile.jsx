import React, { useState } from 'react'
import { AlertTriangle, ChevronDown, ChevronRight, Loader2, Sparkles, Users } from 'lucide-react'
import { api } from '../lib/api'
import { CATEGORY_LABEL, fmtEur } from '../lib/format'

const BASIS = {
  BUDGET: ['Budget dell’azienda', 'bg-emerald-500/15 text-emerald-700 border-emerald-500/30'],
  PIANO_INVESTIMENTI: ['Piano investimenti', 'bg-sky-500/15 text-sky-700 border-sky-500/30'],
  PREVISIONE: ['Previsione dal bilancio', 'bg-amber-500/15 text-amber-700 border-amber-500/30'],
}

/** Bozza di budget per il bando scelto: il personale persona per persona e le altre spese voce per voce, con la fonte di ogni numero. Una base da modificare, poi la controlla la pagina Budget. */
export default function TemplateFromProfile({ bando, onApply, onGoProfile, startOpen = false }) {
  const [open, setOpen] = useState(startOpen)
  const [scale, setScale] = useState(100)
  const [fit, setFit] = useState(true)
  const [year, setYear] = useState('')
  const [busy, setBusy] = useState(false)
  const [res, setRes] = useState(null)
  const [error, setError] = useState(null)
  const [showAll, setShowAll] = useState(false)

  const generate = async () => {
    setBusy(true); setError(null)
    try {
      const r = await api.profileTemplate(bando.bando_id, Number(scale), fit, year ? Number(year) : undefined)
      setRes(r)
      onApply(r)
    } catch (e) { setError(e.message); setRes(null) } finally { setBusy(false) }
  }
  const people = res?.personnel || []
  const rows = res?.basis || []
  const shown = showAll ? rows : rows.slice(0, 8)

  return (
    <div className="card">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center gap-2 px-4 py-3 text-left text-sm font-medium">
        {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        <Sparkles className="w-4 h-4 text-brand-ink" />Bozza di budget dall’azienda
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3">
          <p className="text-xs text-ink-2 leading-relaxed">Parte da tutto ciò che hai caricato nel Profilo: l’organico persona per persona (livello, contratto, RAL), il budget e il piano degli investimenti dell’azienda se ci sono, altrimenti la previsione dall’ultimo bilancio. Le spese sono voci precise (affitti, energia, licenze…), non solo categorie; quelle che «{bando.name}» esclude per nome non entrano e le voci sopra i tetti si riducono. È solo una base: modificala come vuoi, poi controllala qui sotto.</p>
          <div className="flex flex-wrap items-end gap-3">
            <label className="space-y-1 text-xs text-ink-2"><span className="label">Quota del progetto (% di spese e di tempo di lavoro)</span>
              <input type="number" min="1" max="100" className="field !w-28" value={scale} onChange={(e) => setScale(e.target.value)} /></label>
            <label className="space-y-1 text-xs text-ink-2"><span className="label">Anno (vuoto = il prossimo)</span>
              <input type="number" min="2020" max="2100" placeholder="auto" className="field !w-24" value={year} onChange={(e) => setYear(e.target.value)} /></label>
            <label className="inline-flex items-center gap-2 text-xs text-ink-2 pb-2"><input type="checkbox" checked={fit} onChange={(e) => setFit(e.target.checked)} />Riduci le voci sopra i tetti del bando</label>
            <button className="btn-primary" disabled={busy || !(Number(scale) > 0)} onClick={generate}>{busy && <Loader2 className="w-3.5 h-3.5 animate-spin" />}{res ? 'Rigenera la bozza' : 'Crea la bozza'}</button>
            <button className="btn" onClick={() => window.dispatchEvent(new CustomEvent('quanto-assistant', { detail: { task: 'budget', bandoId: bando.bando_id, scale: Number(scale) > 0 ? Number(scale) : undefined } }))}><Sparkles className="w-3.5 h-3.5" />Fallo fare all’assistente</button>
          </div>
          {error && (
            <p className="text-xs text-red-700">{error} {error.startsWith('Mancano i dati') && <button className="underline font-medium" onClick={onGoProfile}>Vai al profilo</button>}</p>
          )}
          {res && (
            <div className="text-xs space-y-3 p-3 rounded-xl border border-line bg-field">
              <p className="text-ink"><span className="font-semibold">{res.cost_items.length} voci</span> aggiunte al budget{people.length ? ` (${people.length} persone e ${res.cost_items.length - people.length} voci di spesa)` : ''}, anno {res.year}. Quelle con codice <span className="font-mono">TPL-</span> sostituiscono la bozza precedente.</p>

              {people.length > 0 && (
                <div className="space-y-1.5">
                  <p className="font-medium text-ink inline-flex items-center gap-1.5"><Users className="w-3.5 h-3.5" />Personale persona per persona</p>
                  <div className="overflow-x-auto"><table className="w-full"><thead><tr className="text-left text-mute"><th className="font-medium py-1">Persona</th><th className="font-medium">Livello</th><th className="font-medium">Contratto</th><th className="font-medium text-right">RAL</th><th className="font-medium text-right">Tempo sul progetto</th></tr></thead>
                    <tbody>{people.map((p) => (
                      <tr key={p.item_id} className="border-t border-line"><td className="py-1 text-ink-2">{p.role || 'Persona'} <span className="text-mute">{p.ref}</span>{p.has_payslip && <span className="ml-1 text-emerald-700" title="C’è la busta paga: la RAL si confronta con quella dichiarata (criterio 15)">· busta paga</span>}</td>
                        <td>{p.level || '—'}</td><td>{p.ccnl_code ? p.ccnl_code.replace(/_/g, ' ').toLowerCase() : <span className="text-amber-700">da indicare</span>}</td>
                        <td className="text-right tabular-nums">{fmtEur(p.ral_eur)}</td><td className="text-right tabular-nums">{Math.round(p.fte_allocation * 100)}%</td></tr>))}</tbody></table></div>
                </div>
              )}

              <div className="space-y-1.5">
                <p className="font-medium text-ink">Le spese, voce per voce, e da dove viene ogni numero</p>
                <div className="overflow-x-auto"><table className="w-full"><thead><tr className="text-left text-mute"><th className="font-medium py-1">Voce di spesa</th><th className="font-medium">Categoria</th><th className="font-medium text-right">Importo</th><th className="font-medium pl-3">Fonte</th></tr></thead>
                  <tbody>{shown.map((b) => { const [label, tone] = BASIS[b.basis] || [b.basis, 'border-line text-ink-2']; return (
                    <tr key={b.item_id} className="border-t border-line align-top"><td className="py-1 text-ink-2">{b.label}<span className="block text-[10px] text-mute">{b.detail}</span></td>
                      <td className="text-ink-2">{CATEGORY_LABEL[b.category]}</td><td className="text-right tabular-nums">{fmtEur(b.amount_eur)}</td>
                      <td className="pl-3"><span className={`px-1.5 py-0.5 rounded border text-[10px] ${tone}`}>{label}</span>{b.sources?.[0]?.filename && <span className="block text-[10px] text-mute truncate max-w-[16rem]" title={b.sources[0].filename}>{b.sources[0].filename}</span>}</td></tr>) })}</tbody></table></div>
                {rows.length > 8 && <button className="underline text-ink-2" onClick={() => setShowAll(!showAll)}>{showAll ? 'Mostra meno' : `Mostra tutte le ${rows.length} voci`}</button>}
              </div>

              {res.adjustments.map((a) => <p key={a.category} className="text-amber-700">{a.reason}: {a.label.toLowerCase()} ridotte da {fmtEur(a.forecast_eur)} a {fmtEur(a.eligible_eur)}.</p>)}
              {res.excluded_types?.length > 0 && <p className="text-amber-700">Il bando le esclude per nome e non sono nel budget: {res.excluded_types.map((t) => `${t.label.toLowerCase()} (${fmtEur(t.amount_eur)})`).join(', ')}.</p>}
              {res.excluded_categories.length > 0 && <p className="text-mute">Categorie non incluse perché il bando non le ammette: {res.excluded_categories.map((c) => c.label.toLowerCase()).join(', ')}.</p>}
              {res.needs_personnel && <p className="text-amber-700">Personale ({fmtEur(res.needs_personnel.amount_eur)}): {res.needs_personnel.message} <button className="underline font-medium" onClick={onGoProfile}>Vai al profilo</button></p>}
              {res.needs_input?.length > 0 && (
                <div className="p-2.5 rounded-lg border border-amber-500/30 bg-amber-500/5 space-y-1">
                  <p className="font-medium text-amber-700 inline-flex items-center gap-1.5"><AlertTriangle className="w-3.5 h-3.5" />Cosa manca per completarlo</p>
                  {res.needs_input.map((n) => <p key={n} className="text-ink-2">• {n}</p>)}
                </div>
              )}
              {res.notes.map((n) => <p key={n} className="text-mute">• {n}</p>)}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
