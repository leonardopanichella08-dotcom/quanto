import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Building2, CheckCircle2, Loader2, Plus, RefreshCw, Save } from 'lucide-react'
import { api } from '../lib/api'
import { fmtEur } from '../lib/format'
import { ChromeCard, SectionTitle } from './ui'

const ORIGIN = {
  DOCUMENT: ['da documento', 'text-emerald-700 border-emerald-500/30'],
  MANUAL: ['inserito da te', 'text-sky-700 border-sky-500/30'],
  DERIVED: ['ricavato', 'text-ink-2 border-line-strong'],
}

function Origin({ source }) {
  if (!source) return <span className="text-[11px] text-amber-700">manca</span>
  const [label, tone] = ORIGIN[source.origin] || [source.origin, 'text-ink-2 border-line-strong']
  return <span className={`px-1.5 py-0.5 rounded border text-[11px] ${tone}`} title={source.from || (source.document_id ? `Documento n. ${source.document_id}` : '')}>{label}{source.from ? ` · ${source.from}` : ''}</span>
}

export function FieldInput({ f, regions, value, onChange }) {
  const common = { 'aria-label': f.label, value: value ?? '', onChange: (e) => onChange(e.target.value) }
  if (f.kind === 'region') return <select className="field" {...common}><option value="">— scegli —</option>{regions.map((r) => <option key={r}>{r}</option>)}</select>
  if (f.kind === 'bool') {
    const v = value === true ? 'yes' : value === false ? 'no' : ''
    return <select className="field" aria-label={f.label} value={v} onChange={(e) => onChange(e.target.value === 'yes' ? true : e.target.value === 'no' ? false : '')}>
      <option value="">— indica —</option><option value="no">No</option><option value="yes">Sì</option></select>
  }
  const props = f.kind === 'count' || f.kind === 'year' ? { type: 'number', min: 0 } : f.kind === 'province' ? { maxLength: 2, className: 'field uppercase' } : {}
  return <input className="field" {...props} {...common} />
}

export default function CompanyProfile({ version = 0, onChanged }) {
  const [ov, setOv] = useState(null)
  const [error, setError] = useState(null)
  const [draft, setDraft] = useState({})                 // campi modificati e non ancora salvati
  const [finDraft, setFinDraft] = useState({})           // {anno: {chiave: valore}}
  const [busy, setBusy] = useState(null)
  const [newYear, setNewYear] = useState('')
  const [extraYears, setExtraYears] = useState([])

  const load = useCallback(() => api.profile().then((o) => { setOv(o); setError(null) }).catch((e) => setError(e.message)), [])
  useEffect(() => { load() }, [load, version])

  const years = useMemo(() => {
    const ys = new Set([...(ov?.financials || []).map((f) => f.fiscal_year), ...extraYears])
    return [...ys].sort((a, b) => a - b)
  }, [ov, extraYears])

  if (error && !ov) return <p className="text-xs text-red-700">{error}</p>
  if (!ov) return <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Carico il profilo…</p>

  const saved = (o) => { setOv(o); setError(null); onChanged?.() }
  const saveProfile = async () => {
    setBusy('profile'); setError(null)
    try { saved(await api.saveProfile(draft)); setDraft({}) } catch (e) { setError(e.message) } finally { setBusy(null) }
  }
  const saveYear = async (y) => {
    setBusy(`fin-${y}`); setError(null)
    try { saved(await api.saveFinancials(y, finDraft[y] || {})); setFinDraft((d) => { const n = { ...d }; delete n[y]; return n }) } catch (e) { setError(e.message) } finally { setBusy(null) }
  }
  const reread = async () => {
    setBusy('sync'); setError(null)
    try { saved((await api.profileSync()).profile) } catch (e) { setError(e.message) } finally { setBusy(null) }
  }
  const finValue = (y, k) => {
    if (finDraft[y] && k in finDraft[y]) return finDraft[y][k]
    return ov.financials.find((f) => f.fiscal_year === y)?.values[k] ?? ''
  }
  const finSource = (y, k) => ov.financials.find((f) => f.fiscal_year === y)?.sources[k]
  const addYear = () => {
    const y = Number(newYear)
    if (y >= 2000 && y <= 2100 && !years.includes(y)) { setExtraYears((e) => [...e, y]); setNewYear('') }
  }
  const dirtyProfile = Object.keys(draft).length > 0
  const missingProfile = ov.missing.filter((m) => m.scope === 'profile')
  const missingFin = ov.missing.filter((m) => m.scope === 'financial')

  return (
    <ChromeCard label="quanto.app/profilo/azienda" bodyClassName="p-6 space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4 pb-4 border-b border-line">
        <div className="max-w-xl">
          <SectionTitle icon={Building2} className="!text-lg">Il profilo dell’azienda</SectionTitle>
          <p className="text-xs text-ink-2 mt-0.5 leading-relaxed">Carica visura, bilanci e documenti qui sotto: QUANTO ne ricava i dati dell’impresa e i costi di ogni anno. Il profilo serve all’Allocazione (stima dell’anno dopo e bandi adatti) e al Budget (bozza di partenza per un bando). Quello che scrivi tu non viene mai sovrascritto dai documenti.</p>
        </div>
        <div className="min-w-[12rem]">
          <span className="label">Completezza</span>
          <div className="text-2xl font-display font-semibold tabular-nums text-ink">{ov.completeness_pct}%</div>
          <div className="h-1.5 rounded-full bg-tint-2 overflow-hidden mt-1"><div className="h-full rounded-full bg-brand" style={{ width: `${ov.completeness_pct}%` }} /></div>
          {ov.size && <p className="text-[11px] text-mute mt-2">{ov.size.label}{ov.size.provisional ? ' (indicativo: manca un dato)' : ''}</p>}
        </div>
      </div>

      {error && <p className="text-xs text-red-700 p-3 rounded-xl border border-red-500/30">{error}</p>}

      {(missingProfile.length > 0 || missingFin.length > 0) && (
        <div className="p-3 rounded-xl border border-amber-500/30 bg-amber-500/5 text-xs text-ink-2 space-y-1">
          <p className="font-medium text-amber-700">Da completare</p>
          <ul className="list-disc pl-5">
            {missingProfile.map((m) => <li key={m.key}>{m.label}</li>)}
            {missingFin.map((m) => <li key={`${m.key}-${m.year}`}>{m.year ? `${m.label} (esercizio ${m.year})` : m.label}</li>)}
          </ul>
        </div>
      )}

      <div>
        <div className="flex items-center gap-2 mb-3"><span className="label">Dati dell’impresa</span>
          <button className="btn !py-1 ml-auto" onClick={reread} disabled={busy === 'sync'} title="Rilegge tutti i documenti caricati e aggiorna i dati">
            {busy === 'sync' ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}Rileggi i documenti</button></div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {ov.fields.map((f) => (
            <label key={f.key} className="space-y-1 text-xs text-ink-2 block">
              <span className="flex items-center justify-between gap-2"><span className="label">{f.label}{f.required ? ' *' : ''}</span><Origin source={f.key in draft ? { origin: 'MANUAL', from: 'da salvare' } : f.source} /></span>
              <FieldInput f={f} regions={ov.regions} value={f.key in draft ? draft[f.key] : f.value} onChange={(v) => setDraft((d) => ({ ...d, [f.key]: v }))} />
            </label>
          ))}
        </div>
        <div className="flex items-center gap-3 mt-3">
          <button className="btn-primary" disabled={!dirtyProfile || busy === 'profile'} onClick={saveProfile}>{busy === 'profile' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}Salva i dati</button>
          <span className="text-[11px] text-mute">* serve per la completezza. Un campo svuotato e salvato viene cancellato.</span>
        </div>
      </div>

      <div>
        <div className="flex flex-wrap items-center gap-2 mb-1"><span className="label">Bilanci per esercizio</span>
          <span className="ml-auto flex items-center gap-2"><input type="number" className="field !w-24 !py-1" placeholder="Anno" value={newYear} onChange={(e) => setNewYear(e.target.value)} aria-label="Nuovo esercizio" />
            <button className="btn !py-1" onClick={addYear}><Plus className="w-3 h-3" />Aggiungi esercizio</button></span></div>
        <p className="text-[11px] text-mute mb-3">I costi per categoria arrivano dalle righe del bilancio già assegnate o confermate; puoi completare o correggere a mano. L’ultimo esercizio è la base per la stima dell’anno successivo.</p>
        {years.length === 0 && <p className="text-xs text-mute">Nessun esercizio ancora: carica un bilancio oppure aggiungi un anno e scrivi i dati a mano.</p>}
        {years.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead><tr className="text-left text-mute"><th className="py-1.5 pr-3 font-medium">Voce</th>{years.map((y) => <th key={y} className="py-1.5 px-2 font-medium text-center">{y}</th>)}</tr></thead>
              <tbody>
                {ov.fin_fields.map((k) => (
                  <tr key={k.key} className="border-t border-line">
                    <td className="py-1.5 pr-3 text-ink-2">{k.label}{k.required ? ' *' : ''}</td>
                    {years.map((y) => (
                      <td key={y} className="py-1 px-1">
                        <input type="number" step={k.kind === 'count' ? 1 : 0.01} className="field !py-1 !w-32 text-right tabular-nums" aria-label={`${k.label} ${y}`}
                          value={finValue(y, k.key)} onChange={(e) => setFinDraft((d) => ({ ...d, [y]: { ...(d[y] || {}), [k.key]: e.target.value } }))} />
                        <div className="text-[10px] text-mute text-right mt-0.5 h-3">{finDraft[y] && k.key in finDraft[y] ? 'da salvare' : finSource(y, k.key) ? ORIGIN[finSource(y, k.key).origin]?.[0] : ''}</div>
                      </td>
                    ))}
                  </tr>
                ))}
                <tr className="border-t border-line">
                  <td />{years.map((y) => (
                    <td key={y} className="py-2 px-1 text-center">
                      <button className="btn !py-1" disabled={!finDraft[y] || busy === `fin-${y}`} onClick={() => saveYear(y)}>{busy === `fin-${y}` ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCircle2 className="w-3 h-3" />}Salva {y}</button>
                      {ov.financials.find((f) => f.fiscal_year === y)?.partial && <div className="text-[10px] text-amber-700 mt-1">{ov.financials.find((f) => f.fiscal_year === y).partial.pending_lines} righe da verificare</div>}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        )}
        {ov.last_year && <p className="text-[11px] text-mute mt-2">Ultimo esercizio: {ov.last_year}. Costi complessivi per categoria: {fmtEur(ov.financials.find((f) => f.fiscal_year === ov.last_year)?.values && Object.entries(ov.financials.find((f) => f.fiscal_year === ov.last_year).values).filter(([k]) => /^(personnel|capital_assets|consulting|overhead|training)_eur$/.test(k)).reduce((s, [, v]) => s + Number(v || 0), 0))}.</p>}
      </div>
    </ChromeCard>
  )
}
