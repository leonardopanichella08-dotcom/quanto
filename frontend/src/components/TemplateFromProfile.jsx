import React, { useState } from 'react'
import { ChevronDown, ChevronRight, Loader2, Sparkles } from 'lucide-react'
import { api } from '../lib/api'
import { fmtEur } from '../lib/format'

/** Bozza di budget per il bando scelto, ricavata dai bilanci del profilo azienda: una base da modificare, poi la controlla la pagina Budget. */
export default function TemplateFromProfile({ bando, onApply, onGoProfile, startOpen = false }) {
  const [open, setOpen] = useState(startOpen)
  const [scale, setScale] = useState(100)
  const [fit, setFit] = useState(true)
  const [busy, setBusy] = useState(false)
  const [res, setRes] = useState(null)
  const [error, setError] = useState(null)

  const generate = async () => {
    setBusy(true); setError(null)
    try {
      const r = await api.profileTemplate(bando.bando_id, Number(scale), fit)
      setRes(r)
      onApply(r)
    } catch (e) { setError(e.message); setRes(null) } finally { setBusy(false) }
  }

  return (
    <div className="card">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center gap-2 px-4 py-3 text-left text-sm font-medium">
        {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        <Sparkles className="w-4 h-4 text-brand-ink" />Bozza di budget dal profilo azienda
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3">
          <p className="text-xs text-ink-2 leading-relaxed">Parte dai bilanci che hai caricato nel Profilo: prende le voci di costo delle categorie che «{bando.name}» ammette, per la quota di progetto che indichi, e riduce quelle che superano i tetti del bando. È solo una base: modificala come vuoi, poi controllala qui sotto.</p>
          <div className="flex flex-wrap items-end gap-3">
            <label className="space-y-1 text-xs text-ink-2"><span className="label">Quota del progetto sui costi annui (%)</span>
              <input type="number" min="1" max="100" className="field !w-28" value={scale} onChange={(e) => setScale(e.target.value)} /></label>
            <label className="inline-flex items-center gap-2 text-xs text-ink-2 pb-2"><input type="checkbox" checked={fit} onChange={(e) => setFit(e.target.checked)} />Riduci le voci sopra i tetti del bando</label>
            <button className="btn-primary" disabled={busy || !(Number(scale) > 0)} onClick={generate}>{busy && <Loader2 className="w-3.5 h-3.5 animate-spin" />}{res ? 'Rigenera la bozza' : 'Crea la bozza'}</button>
          </div>
          {error && (
            <p className="text-xs text-red-700">{error} {error.startsWith('Mancano i dati') && <button className="underline font-medium" onClick={onGoProfile}>Vai al profilo</button>}</p>
          )}
          {res && (
            <div className="text-xs space-y-1.5 p-3 rounded-xl border border-line bg-field">
              <p className="text-ink"><span className="font-semibold">{res.cost_items.length} voci</span> aggiunte al budget, per {fmtEur(res.total_eur)} (base: bilancio {res.base_year}). Quelle con codice <span className="font-mono">TPL-</span> sostituiscono la bozza precedente.</p>
              {res.adjustments.map((a) => <p key={a.category} className="text-amber-700">{a.reason}: {a.label.toLowerCase()} ridotte da {fmtEur(a.forecast_eur)} a {fmtEur(a.eligible_eur)}.</p>)}
              {res.excluded_categories.length > 0 && <p className="text-mute">Non incluse perché il bando non le ammette: {res.excluded_categories.map((c) => c.label.toLowerCase()).join(', ')}.</p>}
              {res.notes.map((n) => <p key={n} className="text-mute">• {n}</p>)}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
