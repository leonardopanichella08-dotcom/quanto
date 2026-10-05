import React, { useState } from 'react'
import { ChevronDown, ChevronRight, Loader2, RotateCcw, Trash2 } from 'lucide-react'
import { api } from '../lib/api'
import { fmtEur, fmtNum } from '../lib/format'

const ORIGIN_TONE = {
  USER_INPUT: 'border-brand/60 bg-brand/10 text-brand-ink',
  TEMPLATE: 'border-sky-500/30 bg-sky-500/10 text-sky-700',
  DERIVED: 'border-line-strong text-ink-2',
  NONE: 'border-amber-500/30 bg-amber-500/10 text-amber-700',
}
const KEYS = [['REVENUE', 'Ricavi'], ['PERSONNEL', 'Personale'], ['CAPITAL_ASSETS', 'Beni strumentali'], ['CONSULTING', 'Consulenze'], ['OVERHEAD', 'Spese generali'], ['TRAINING', 'Formazione']]

const pctStr = (g) => String(Math.round(g * 1000) / 10)
const signed = (g) => `${g > 0 ? '+' : ''}${fmtNum(g * 100, 1)}%`
const sourceText = (s) => (!s ? null : s.filename ? `«${s.filename}»` : s.origin === 'MANUAL' ? 'inserito a mano' : 'dato del profilo')

/** Una riga della stima: percentuale già compilata (modello dell'utente o ricavata dai bilanci), modificabile, con la spiegazione sotto. */
function ForecastRow({ r, overrides, setOverride, showWhy, base }) {
  const mine = overrides[r.category]
  const value = mine !== undefined ? mine : pctStr(r.growth_applied)
  const changed = mine !== undefined && mine !== '' && Number(mine) !== Math.round(r.growth_applied * 1000) / 10
  return (
    <>
      <tr className="border-t border-line align-top">
        <td className="py-2 text-ink-2">
          <span className="font-medium text-ink">{r.label}</span>
          <span className={`ml-2 px-1.5 py-0.5 rounded border text-[10px] font-medium ${ORIGIN_TONE[r.growth_origin]}`}>{r.growth_origin_label}</span>
        </td>
        <td className="text-right tabular-nums">{fmtEur(r.baseline_eur)}</td>
        <td className="text-right pl-3">
          <span className="inline-flex items-center gap-1">
            <input type="number" step="0.5" className="field !w-24 !py-1 text-right" aria-label={`Variazione annua ${r.label}`} value={value} onChange={(e) => setOverride(r.category, e.target.value)} />
            <span className="text-mute">%</span>
            {mine !== undefined && <button className="text-mute hover:text-ink" title="Torna alla percentuale proposta" aria-label="Annulla la modifica" onClick={() => setOverride(r.category, undefined)}><RotateCcw className="w-3 h-3" /></button>}
          </span>
          {changed && <span className="block text-[10px] text-brand-ink">da ricalcolare</span>}
        </td>
        <td className="text-right font-semibold tabular-nums">{fmtEur(r.forecast_eur)}</td>
      </tr>
      {showWhy && (
        <tr>
          <td colSpan={4} className="pb-3 pt-0">
            <div className="rounded-xl bg-field border border-line px-3 py-2 text-[11px] text-ink-2 leading-relaxed space-y-1">
              {r.explanation.map((t, i) => <p key={i} className={t.startsWith('Attenzione') ? 'text-amber-700' : ''}>{t}</p>)}
              <p className="text-mute">
                Dati da: bilancio {base} · {sourceText(r.base_source)}
                {r.previous_source && <> · bilancio {r.previous_year} · {sourceText(r.previous_source)}</>}
              </p>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

/** Il modello di previsione dell'utente (per esempio del commercialista o del CFO): percentuali annue per ogni voce, salvate e usate al posto di quelle ricavate dai bilanci. */
function TemplateEditor({ forecast, onSaved }) {
  const tpl = forecast.template
  const rows = [forecast.revenue, ...forecast.categories].filter(Boolean)
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState({})
  const [label, setLabel] = useState(tpl?.label || '')
  const [note, setNote] = useState(tpl?.note || '')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const start = () => {
    setDraft(Object.fromEntries(KEYS.map(([k]) => [k, tpl?.growth[k] != null ? pctStr(tpl.growth[k]) : ''])))
    setLabel(tpl?.label || ''); setNote(tpl?.note || ''); setError(null); setOpen(true)
  }
  const fromCurrent = () => setDraft(Object.fromEntries(rows.map((r) => [r.category, pctStr(r.growth_applied)])))
  const save = async () => {
    const growth = Object.fromEntries(Object.entries(draft).filter(([, v]) => v !== '' && !Number.isNaN(Number(v))).map(([k, v]) => [k, Number(v) / 100]))
    if (!Object.keys(growth).length) { setError('Scrivi almeno una percentuale.'); return }
    setBusy(true); setError(null)
    try { await api.saveForecastTemplate(growth, label, note); setOpen(false); await onSaved() } catch (e) { setError(e.message) } finally { setBusy(false) }
  }
  const remove = async () => {
    if (!window.confirm('Eliminare il modello? Le percentuali torneranno a essere ricavate dai tuoi bilanci.')) return
    setBusy(true); setError(null)
    try { await api.deleteForecastTemplate(); setOpen(false); await onSaved() } catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  return (
    <div className="rounded-2xl border border-line bg-field p-4 space-y-3 text-xs">
      <div className="flex flex-wrap items-start gap-3">
        <div className="min-w-0 flex-1 space-y-0.5">
          <p className="text-sm font-semibold text-ink">Il tuo modello di previsione</p>
          {tpl ? (
            <p className="text-ink-2 leading-relaxed">Sto usando il modello{tpl.label ? <> «<strong>{tpl.label}</strong>»</> : ''} per {Object.keys(tpl.growth).length} {Object.keys(tpl.growth).length === 1 ? 'voce' : 'voci'}; le altre hanno la percentuale ricavata dai tuoi bilanci. Salvato il {String(tpl.updated_at).slice(0, 10).split('-').reverse().join('/')}.</p>
          ) : (
            <p className="text-ink-2 leading-relaxed">Non hai un modello: per ogni voce uso la variazione che risulta dai tuoi due ultimi bilanci, già inserita qui sotto e spiegata. Se il commercialista o il CFO ti ha dato delle percentuali di crescita o di calo di costi e ricavi, salvale come modello: sostituiranno quelle automatiche.</p>
          )}
        </div>
        {!open && <button className="btn !py-1" onClick={start}>{tpl ? 'Modifica il modello' : 'Inserisci il mio modello'}</button>}
      </div>
      {open && (
        <div className="space-y-3 pt-2 border-t border-line">
          <div className="grid sm:grid-cols-3 gap-3">
            {KEYS.map(([k, l]) => (
              <label key={k} className="space-y-1"><span className="label">{l} · % annua</span>
                <input type="number" step="0.5" className="field" placeholder="vuoto = dai bilanci" value={draft[k] ?? ''} onChange={(e) => setDraft((d) => ({ ...d, [k]: e.target.value }))} /></label>
            ))}
          </div>
          <div className="grid sm:grid-cols-2 gap-3">
            <label className="space-y-1"><span className="label">Chi l’ha indicato (facoltativo)</span><input className="field" maxLength={80} placeholder="Per esempio: commercialista, CFO" value={label} onChange={(e) => setLabel(e.target.value)} /></label>
            <label className="space-y-1"><span className="label">Nota (facoltativa)</span><input className="field" maxLength={500} placeholder="Il motivo, in una riga" value={note} onChange={(e) => setNote(e.target.value)} /></label>
          </div>
          <p className="text-mute">Numeri positivi = crescita, negativi = calo (per esempio −3 per un calo del 3% l’anno). Le caselle vuote restano ricavate dai bilanci.</p>
          <div className="flex flex-wrap items-center gap-2">
            <button className="btn-primary" disabled={busy} onClick={save}>{busy && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Salva il modello</button>
            <button className="btn" onClick={fromCurrent} disabled={busy}>Parti dalle percentuali attuali</button>
            <button className="btn" onClick={() => setOpen(false)} disabled={busy}>Annulla</button>
            {tpl && <button className="btn ml-auto text-red-700" onClick={remove} disabled={busy}><Trash2 className="w-3 h-3" />Elimina il modello</button>}
          </div>
        </div>
      )}
      {error && <p className="text-red-700">{error}</p>}
    </div>
  )
}

export default function ForecastStep({ forecast, overrides, setOverride, year, setYear, matching, onEstimate, onTemplateChanged }) {
  const [showWhy, setShowWhy] = useState(true)
  const rows = forecast ? [forecast.revenue, ...forecast.categories].filter(Boolean) : []
  const dirty = rows.some((r) => overrides[r.category] !== undefined && overrides[r.category] !== '' && Number(overrides[r.category]) !== Math.round(r.growth_applied * 1000) / 10)
  return (
    <>
      <div className="flex flex-wrap items-end gap-3">
        <label className="space-y-1 text-xs text-ink-2"><span className="label">Anno da pianificare</span><input type="number" className="field !w-24" value={year} onChange={(e) => setYear(e.target.value)} /></label>
        <button className="btn-primary" disabled={matching || !Number(year)} onClick={onEstimate}>{matching && <Loader2 className="w-3.5 h-3.5 animate-spin" />}{forecast ? 'Ricalcola stima e bandi' : 'Calcola la stima e cerca i bandi'}</button>
        {dirty && <span className="text-xs text-brand-ink">Hai cambiato delle percentuali: premi «Ricalcola».</span>}
      </div>
      {!forecast && matching && <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Calcolo la stima e cerco i bandi…</p>}
      {forecast && (
        <div className="space-y-4">
          <TemplateEditor key={forecast.template?.updated_at || 'none'} forecast={forecast} onSaved={onTemplateChanged} />
          <div className="overflow-x-auto">
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs text-ink-2">Le percentuali sono già compilate: puoi lasciarle così o cambiarle. Sotto ogni voce c’è il perché, con i numeri dei tuoi file.</p>
              <button className="btn !py-0.5 shrink-0 ml-3" onClick={() => setShowWhy(!showWhy)}>{showWhy ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}{showWhy ? 'Nascondi i perché' : 'Mostra i perché'}</button>
            </div>
            <table className="w-full text-xs">
              <thead><tr className="text-left text-mute"><th className="py-1.5 font-medium">Voce</th><th className="font-medium text-right">Esercizio {forecast.base_year}</th>
                <th className="font-medium text-right pl-3">Variazione annua</th><th className="font-medium text-right">Stima {forecast.fiscal_year}</th></tr></thead>
              <tbody>
                {forecast.revenue && (
                  <>
                    <tr><td colSpan={4} className="pt-2 pb-1 text-[11px] font-semibold uppercase tracking-wide text-mute">Guadagni</td></tr>
                    <ForecastRow r={forecast.revenue} overrides={overrides} setOverride={setOverride} showWhy={showWhy} base={forecast.base_year} />
                  </>
                )}
                <tr><td colSpan={4} className="pt-3 pb-1 text-[11px] font-semibold uppercase tracking-wide text-mute">Costi</td></tr>
                {forecast.categories.map((r) => <ForecastRow key={r.category} r={r} overrides={overrides} setOverride={setOverride} showWhy={showWhy} base={forecast.base_year} />)}
                <tr className="border-t border-line-strong font-semibold"><td className="py-2">Totale costi</td><td className="text-right tabular-nums">{fmtEur(forecast.total_baseline_eur)}</td><td /><td className="text-right tabular-nums">{fmtEur(forecast.total_forecast_eur)}</td></tr>
                {forecast.summary && (
                  <tr className="text-mute"><td className="py-1">Costi sui ricavi</td><td className="text-right tabular-nums">{fmtNum(forecast.summary.cost_ratio_base * 100, 1)}%</td><td /><td className="text-right tabular-nums">{fmtNum(forecast.summary.cost_ratio_forecast * 100, 1)}%</td></tr>
                )}
              </tbody>
            </table>
            {forecast.missing.length > 0 && <p className="text-xs text-amber-700 mt-2">Senza dato nel bilancio {forecast.base_year}: {forecast.missing.map((m) => m.label.toLowerCase()).join(', ')} (non entrano nella stima).</p>}
            {forecast.warnings.map((w) => <p key={w} className="text-xs text-amber-700 mt-1">{w}</p>)}
            <p className="text-[11px] text-mute mt-2">Le percentuali ricavate dai bilanci sono la variazione tra i tuoi due ultimi esercizi e valgono per ogni anno fino a quello pianificato. «Costi sui ricavi» considera solo le cinque categorie di spesa qui sopra.</p>
          </div>
        </div>
      )}
    </>
  )
}
