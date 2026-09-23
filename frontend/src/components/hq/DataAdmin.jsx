import React, { useCallback, useEffect, useState } from 'react'
import { AlertTriangle, FileUp, Landmark, Loader2, RefreshCw, Trash2 } from 'lucide-react'
import { api, fileToBase64 } from '../../lib/api'
import { SectionTitle } from '../ui'

const Err = ({ e }) => (e ? (
  <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-700 text-xs space-y-1">
    <p className="font-semibold flex items-center gap-1"><AlertTriangle className="w-3.5 h-3.5" />{e.message}</p>
    {e.detail?.errors?.length > 0 && <ul className="list-disc pl-5">{e.detail.errors.slice(0, 15).map((x) => <li key={x.line}>riga {x.line}: {x.error}</li>)}</ul>}
  </div>
) : null)

/** Banca dei pattern: importazione dei budget storici (con la fonte di ogni riga) e archetipi calcolati con k-means. */
export function PatternAdmin() {
  const [cats, setCats] = useState([])
  const [budgets, setBudgets] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [last, setLast] = useState(null)
  const load = useCallback(async () => { try { setCats(await api.patternCategories()); setBudgets(await api.patternBudgets()) } catch (e) { setError(e) } }, [])
  useEffect(() => { load() }, [load])
  const upload = async (f) => {
    if (!f) return
    setBusy(true); setError(null)
    try { setLast(await api.patternImport({ filename: f.name, content_base64: await fileToBase64(f) })); await load() } catch (e) { setError(e) } finally { setBusy(false) }
  }
  return (
    <div className="space-y-5">
      <div className="card p-5 space-y-3">
        <SectionTitle icon={FileUp}>Importa budget storici</SectionTitle>
        <p className="text-xs text-ink-2 leading-relaxed">File CSV con una riga per budget: <code>bando_category</code>, <code>source</code> (obbligatoria: la graduatoria, il dataset o il pilota da cui viene), <code>year</code>, <code>score</code>, poi le quote <code>personnel_pct, assets_pct, consulting_pct, overhead_pct, training_pct, communication_pct</code> (in % o 0,58) oppure gli importi <code>personnel_eur…</code>. Le righe incomplete bloccano l’importazione. Con almeno 6 budget per categoria gli archetipi si calcolano con k-means; con meno c’è una sola media, dichiarata come tale.</p>
        <input type="file" accept=".csv" className="text-xs" disabled={busy} onChange={(e) => { upload(e.target.files?.[0]); e.target.value = '' }} />
        {busy && <Loader2 className="w-4 h-4 animate-spin text-brand-ink" />}
        {last && <p className="text-xs text-emerald-700">Importati {last.imported} budget. {Object.entries(last.categories).map(([c, v]) => `${c}: ${v.archetypes} archetipi (${v.method})`).join(' · ')}</p>}
        <Err e={error} />
      </div>
      <div className="card p-5 space-y-2">
        <SectionTitle>Banca dati ({budgets.length} budget)</SectionTitle>
        {cats.length === 0 && <p className="text-xs text-mute">Vuota: la pagina Confronto lo dice agli utenti e non mostra nessun budget «tipo».</p>}
        {cats.map((c) => <p key={c.bando_category} className="text-xs text-ink-2"><b className="text-ink">{c.bando_category}</b> · {c.budgets} budget · {c.archetypes} archetipi</p>)}
        <div className="max-h-64 overflow-auto"><table className="w-full text-xs"><tbody>
          {budgets.slice(0, 100).map((b) => <tr key={b.id} className="border-t border-line"><td className="py-1 pr-3 text-mute">{b.bando_category}</td><td className="pr-3">{b.source}</td><td className="pr-3 text-mute">{b.year || ''}</td><td className="tabular-nums text-ink-2">{['personnel_pct', 'assets_pct', 'consulting_pct', 'overhead_pct', 'training_pct', 'communication_pct'].map((k) => Math.round(b[k] * 100)).join(' / ')} %</td></tr>)}
        </tbody></table></div>
      </div>
    </div>
  )
}

/** Linee di finanziamento dell'allocazione: ricavate dalle regole pubblicate dei bandi. */
export function FundsAdmin({ bandi }) {
  const [funds, setFunds] = useState([])
  const [form, setForm] = useState({ bando_id: '', fiscal_year: new Date().getFullYear() + 1, max_total_eur: '', de_minimis: false })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const load = useCallback(() => api.funds().then(setFunds).catch(setError), [])
  useEffect(() => { load() }, [load])
  const derive = async () => {
    setBusy(true); setError(null)
    try { await api.deriveFund({ bando_id: form.bando_id, fiscal_year: Number(form.fiscal_year), max_total_eur: form.max_total_eur ? Number(form.max_total_eur) : null, de_minimis: form.de_minimis }); await load() } catch (e) { setError(e) } finally { setBusy(false) }
  }
  return (
    <div className="space-y-5">
      <div className="card p-5 space-y-3">
        <SectionTitle icon={Landmark}>Nuova linea di finanziamento da un bando</SectionTitle>
        <p className="text-xs text-ink-2 leading-relaxed">Si ricava dalle regole <b>pubblicate</b> del bando: categorie ammesse, percentuale di contributo, finestra di ammissibilità, fondi non cumulabili, tetti di consulenze e spese generali. Quello che il bando non dice — la <b>dotazione massima</b> per l’ente e il regime <b>de minimis</b> — lo indichi tu; se lasci vuoto non c’è tetto.</p>
        <div className="grid md:grid-cols-4 gap-3 text-xs">
          <label className="space-y-1 md:col-span-2"><span className="label">Bando</span>
            <select className="field" value={form.bando_id} onChange={(e) => setForm({ ...form, bando_id: e.target.value })}><option value="">Scegli…</option>{bandi.map((b) => <option key={b.bando_id} value={b.bando_id}>{b.name}</option>)}</select></label>
          <label className="space-y-1"><span className="label">Anno fiscale</span><input type="number" className="field" value={form.fiscal_year} onChange={(e) => setForm({ ...form, fiscal_year: e.target.value })} /></label>
          <label className="space-y-1"><span className="label">Dotazione massima (€)</span><input type="number" className="field" value={form.max_total_eur} onChange={(e) => setForm({ ...form, max_total_eur: e.target.value })} /></label>
          <label className="flex items-center gap-2 md:col-span-4"><input type="checkbox" className="accent-brand" checked={form.de_minimis} onChange={(e) => setForm({ ...form, de_minimis: e.target.checked })} />Aiuto in regime de minimis</label>
        </div>
        <button className="btn-primary" disabled={!form.bando_id || busy} onClick={derive}>{busy && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Crea la linea</button>
        <Err e={error} />
      </div>
      <div className="card p-5 space-y-2">
        <SectionTitle>Linee attive ({funds.length})</SectionTitle>
        {funds.length === 0 && <p className="text-xs text-mute">Nessuna: la pagina Allocazione non può pianificare finché non ce n’è almeno una.</p>}
        {funds.map((f) => (
          <div key={f.fund_id} className="p-3 rounded-xl border border-line bg-field text-xs flex flex-wrap items-center gap-2">
            <span className="font-medium text-ink">{f.name}</span>
            <span className="text-ink-2">copertura {Math.round(f.coverage_pct * 100)}% · mesi {f.active_from_month}-{f.active_to_month}{f.max_total_eur ? ` · dotazione ${f.max_total_eur.toLocaleString('it-IT')} €` : ' · nessun tetto'}{f.de_minimis ? ' · de minimis' : ''}</span>
            <span className="text-mute">{f.allowed_categories.join(', ')}</span>
            <button className="btn !py-1 ml-auto" onClick={async () => { await api.deleteFund(f.fund_id); load() }}><Trash2 className="w-3 h-3" />Elimina</button>
          </div>
        ))}
      </div>
    </div>
  )
}

/** Stadio 1: aggiornamento del catalogo nazionale (metadati). Parte ogni notte da solo; qui lo si lancia a mano. */
export function CatalogRefresh() {
  const [busy, setBusy] = useState(false)
  const [res, setRes] = useState(null)
  const [error, setError] = useState(null)
  const run = async () => { setBusy(true); setError(null); try { setRes(await api.catalogRefresh()) } catch (e) { setError(e) } finally { setBusy(false) } }
  return (
    <div className="card p-5 space-y-2">
      <SectionTitle icon={RefreshCw}>Catalogo nazionale dei bandi</SectionTitle>
      <p className="text-xs text-ink-2">Ogni notte QUANTO aggiorna da solo l’elenco dei bandi (solo nome, ente, scadenza, link) dai cataloghi ufficiali: nessuna regola viene letta finché un cliente non conferma il bando. Puoi lanciarlo anche ora.</p>
      <button className="btn" disabled={busy} onClick={run}>{busy && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Aggiorna adesso</button>
      {res && <p className="text-xs text-emerald-700">{res.inserted} voci nuove · {res.enriched} arricchite{Object.entries(res.catalogs).map(([c, v]) => ` · ${c}: ${v.listed} misure`).join('')}{res.errors.length ? ` · errori: ${res.errors.join('; ')}` : ''}</p>}
      <Err e={error} />
    </div>
  )
}
