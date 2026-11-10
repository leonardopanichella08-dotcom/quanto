import React, { useRef, useState } from 'react'
import { Info } from './ui'
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronRight, Loader2, Sparkles, Upload, Users } from 'lucide-react'
import { api, fileToBase64 } from '../lib/api'
import { CATEGORY_LABEL, fmtEur, su } from '../lib/format'

const BASIS = {
  BUDGET: ['Budget dell’azienda', 'bg-emerald-500/15 text-emerald-700 border-emerald-500/30'],
  PIANO_INVESTIMENTI: ['Piano investimenti', 'bg-sky-500/15 text-sky-700 border-sky-500/30'],
  PREVISIONE: ['Previsione dal bilancio', 'bg-amber-500/15 text-amber-700 border-amber-500/30'],
}

/** Un dato che manca alla bozza: che cosa, quali documenti ho già letto, quale serve. «Carica adesso» lo carica qui e la bozza si rifà da sola. */
function MissingItem({ m, onUploaded }) {
  const [busy, setBusy] = useState(null)
  const [done, setDone] = useState(null)
  const [err, setErr] = useState(null)
  const inputs = useRef({})
  const send = async (u, files) => {
    if (!files?.length) return
    setBusy(u.doc_type); setErr(null)
    try {
      for (const f of files) await api.fcUpload({ doc_type: u.doc_type, filename: f.name, content_base64: await fileToBase64(f) })
      setDone(`${files.length === 1 ? files[0].name : `${files.length} documenti`} letto. Rifaccio la bozza…`)
      await onUploaded()
    } catch (e) { setErr(e.message) } finally { setBusy(null) }
  }
  return (
    <li className="rounded-xl bg-white border border-line p-3 space-y-1.5">
      <p className="text-ink">{m.what}</p>
      {m.read?.length > 0 && <p className="text-[11px] text-mute">Ho letto: {m.read.slice(0, 4).join(', ')}{m.read.length > 4 ? ` e altri ${m.read.length - 4}` : ''}. Lì non c’è.</p>}
      <p className="text-[11px] text-ink-2"><span className="font-medium text-ink">Serve:</span> {m.need}</p>
      <div className="flex flex-wrap items-center gap-2">
        {(m.upload || []).map((u) => (
          <span key={u.doc_type + u.label}>
            <input type="file" multiple className="hidden" accept=".pdf,.xlsx,.xls,.csv,.xml,.p7m,image/*" ref={(el) => { inputs.current[u.label] = el }} onChange={(e) => { send(u, [...e.target.files]); e.target.value = '' }} />
            <button className="btn !py-1 !text-xs" disabled={!!busy} onClick={() => inputs.current[u.label]?.click()}>{busy === u.doc_type ? <Loader2 className="w-3 h-3 animate-spin" /> : <Upload className="w-3 h-3" />}{u.label}</button>
          </span>
        ))}
      </div>
      {done && <p className="text-[11px] text-emerald-700 inline-flex items-center gap-1"><CheckCircle2 className="w-3 h-3" />{done}</p>}
      {err && <p className="text-[11px] text-red-700">{err}</p>}
    </li>
  )
}

/** Bozza di budget per il bando scelto: il personale persona per persona e le altre spese voce per voce, con la fonte di ogni numero. Una base da modificare, poi la controlla la pagina Budget. */
export default function TemplateFromProfile({ bando, onApply, onGoProfile, startOpen = false }) {
  const [open, setOpen] = useState(startOpen)
  const [scale, setScale] = useState(100)
  const [fit, setFit] = useState(true)
  const [year, setYear] = useState('')
  const [start, setStart] = useState('')
  const [busy, setBusy] = useState(false)
  const [res, setRes] = useState(null)
  const [error, setError] = useState(null)
  const [showAll, setShowAll] = useState(false)

  const generate = async () => {
    setBusy(true); setError(null)
    try {
      const r = await api.profileTemplate(bando.bando_id, Number(scale), fit, year ? Number(year) : undefined, start || undefined)
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
          {(() => { const m = bando.funding_modes?.modes?.[0]; return m && !m.needs_project ? (
            <p className="text-xs p-2.5 rounded-lg border border-emerald-500/30 bg-emerald-500/5 text-ink-2 leading-relaxed"><strong className="text-ink">Questo bando non chiede un progetto nuovo</strong> ({m.label.toLowerCase()}). Si calcola {su(m.base)}. {m.ordinary_costs_ok ? 'Le spese che l’azienda sostiene già sono una base valida per questa bozza.' : 'Le spese di bilancio non sono la base: guarda gli acquisti e le persone dei piani dell’azienda.'}</p>
          ) : (
            <p className="text-xs p-2.5 rounded-lg border border-amber-500/30 bg-amber-500/5 text-ink-2 leading-relaxed"><strong className="text-ink">Questo bando finanzia un progetto.</strong> La bozza parte dalle spese che l’azienda sostiene già: serve a capire l’ordine di grandezza e cosa il bando ammetterebbe. Un budget da presentare si costruisce sul progetto: dalle «Idee di progetto» nell’Allocazione, oppure inserendo a mano le spese nuove. Le spese correnti entrano solo se il bando le ammette per forma (spese generali a forfait, personale realmente dedicato).</p>
          ) })()}
          <Info label="Come funziona">Parte da tutto ciò che hai caricato nel Profilo: l’organico persona per persona (livello, contratto, RAL), il budget e il piano degli investimenti dell’azienda se ci sono, altrimenti la previsione dall’ultimo bilancio. Le spese sono voci precise (affitti, energia, licenze…), non solo categorie; quelle che «{bando.name}» esclude per nome non entrano e le voci sopra i tetti si riducono. È solo una base: modificala come vuoi, poi controllala qui sotto.</Info>
          <div className="flex flex-wrap items-end gap-3">
            <label className="space-y-1 text-xs text-ink-2"><span className="label">Quota del progetto (% di spese e di tempo di lavoro)</span>
              <input type="number" min="1" max="100" className="field !w-28" value={scale} onChange={(e) => setScale(e.target.value)} /></label>
            <label className="space-y-1 text-xs text-ink-2"><span className="label">Anno (vuoto = il prossimo)</span>
              <input type="number" min="2020" max="2100" placeholder="auto" className="field !w-24" value={year} onChange={(e) => setYear(e.target.value)} /></label>
            <label className="space-y-1 text-xs text-ink-2"><span className="label">Avvio del progetto (facoltativo)</span>
              <input type="date" className="field !w-40" value={start} onChange={(e) => setStart(e.target.value)} title="Se la indichi, il controllo 46 verifica su ogni voce che la spesa sia dentro la finestra del bando" /></label>
            <label className="inline-flex items-center gap-2 text-xs text-ink-2 pb-2"><input type="checkbox" checked={fit} onChange={(e) => setFit(e.target.checked)} />Riduci le voci sopra i tetti del bando</label>
            <button className="btn-primary" disabled={busy || !(Number(scale) > 0)} onClick={generate}>{busy && <Loader2 className="w-3.5 h-3.5 animate-spin" />}{res ? 'Rigenera la bozza' : 'Crea la bozza'}</button>
            <button className="btn" onClick={() => window.dispatchEvent(new CustomEvent('quanto-assistant', { detail: { task: 'budget', bandoId: bando.bando_id, scale: Number(scale) > 0 ? Number(scale) : undefined } }))}><Sparkles className="w-3.5 h-3.5" />Fallo fare all’assistente</button>
          </div>
          {error && (
            error.startsWith('Mancano i dati')
              ? <ul className="text-xs"><MissingItem m={{ id: 'bilancio', what: 'Mancano i costi dell’ultimo anno: senza, la bozza non ha da dove partire.', need: 'L’ultimo bilancio (società di capitali) o l’ultima dichiarazione dei redditi (società di persone e ditte individuali).', upload: [{ doc_type: 'BALANCE_SHEET', label: 'Carica il bilancio' }] }} onUploaded={generate} /><li className="pt-1.5"><button className="underline text-ink-2" onClick={() => onGoProfile({ to: 'azienda' })}>Con la dichiarazione dei redditi bastano due numeri: scrivili nel profilo</button></li></ul>
              : <p className="text-xs text-red-700">{error}</p>
          )}
          {res && (
            <div className="text-xs space-y-3 p-3 rounded-xl border border-line bg-field">
              <p className="text-ink">{res.cost_items.length === 0 && (res.missing || []).some((m) => m.required) ? <span className="font-semibold">Nessuna voce ancora: manca un documento (qui sotto). </span> : null}<span className="font-semibold">{res.cost_items.length} voci</span> aggiunte al budget{people.length ? ` (${people.length} persone e ${res.cost_items.length - people.length} voci di spesa)` : ''}, anno {res.year}. Quelle con codice <span className="font-mono">TPL-</span> sostituiscono la bozza precedente.</p>

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
                <div className="overflow-x-auto"><table className="w-full"><thead><tr className="text-left text-mute"><th className="font-medium py-1">Voce di spesa</th><th className="font-medium">Categoria</th><th className="font-medium text-right">Importo</th><th className="font-medium pl-3">Natura e fonte</th></tr></thead>
                  <tbody>{shown.map((b) => { const [label, tone] = BASIS[b.basis] || [b.basis, 'border-line text-ink-2']; return (
                    <tr key={b.item_id} className="border-t border-line align-top"><td className="py-1 text-ink-2">{b.label}<span className="block text-[10px] text-mute">{b.detail}</span></td>
                      <td className="text-ink-2">{CATEGORY_LABEL[b.category]}</td><td className="text-right tabular-nums">{fmtEur(b.amount_eur)}</td>
                      <td className="pl-3"><span className={`mr-1 px-1.5 py-0.5 rounded border text-[10px] ${b.nature === 'NUOVA' || b.nature === 'CORRENTE' ? 'border-emerald-500/30 text-emerald-700' : 'border-amber-500/30 text-amber-700'}`} title={b.nature === 'NUOVA' ? 'Un acquisto in programma: una spesa che il progetto causa' : b.nature === 'CORRENTE' ? 'Una spesa che l’azienda sostiene già: per questo bando è una base valida' : 'Una spesa che l’azienda sostiene comunque: per questo bando non è una spesa di progetto'}>{b.nature === 'NUOVA' ? 'nuova' : b.nature === 'CORRENTE' ? 'corrente' : 'ordinaria'}</span><span className={`px-1.5 py-0.5 rounded border text-[10px] ${tone}`}>{label}</span>{b.sources?.[0]?.filename && <span className="block text-[10px] text-mute truncate max-w-[16rem]" title={b.sources[0].filename}>{b.sources[0].filename}</span>}</td></tr>) })}</tbody></table></div>
                {rows.length > 8 && <button className="underline text-ink-2" onClick={() => setShowAll(!showAll)}>{showAll ? 'Mostra meno' : `Mostra tutte le ${rows.length} voci`}</button>}
              </div>

              {res.adjustments.map((a) => <p key={a.category} className="text-amber-700">{a.reason}: {a.label.toLowerCase()} ridotte da {fmtEur(a.forecast_eur)} a {fmtEur(a.eligible_eur)}.</p>)}
              {res.excluded_types?.length > 0 && <p className="text-amber-700">Il bando le esclude per nome e non sono nel budget: {res.excluded_types.map((t) => `${t.label.toLowerCase()} (${fmtEur(t.amount_eur)})`).join(', ')}.</p>}
              {res.excluded_categories.length > 0 && <p className="text-mute">Categorie non incluse perché il bando non le ammette: {res.excluded_categories.map((c) => c.label.toLowerCase()).join(', ')}.</p>}
              {(() => {
                const all = res.missing || []
                const must = all.filter((m) => m.required)
                const maybe = all.filter((m) => !m.required)
                if (!all.length) return null
                return (
                  <div className="space-y-2">
                    {must.length > 0 && (
                      <div className="p-2.5 rounded-lg border border-amber-500/30 bg-amber-500/5 space-y-2">
                        <p className="font-medium text-amber-700 inline-flex items-center gap-1.5"><AlertTriangle className="w-3.5 h-3.5" />Per completarlo serve {must.length === 1 ? 'un documento' : `${must.length} documenti`}: caricalo qui, la bozza si rifà da sola</p>
                        <ul className="space-y-2">{must.map((m) => <MissingItem key={m.id} m={m} onUploaded={generate} />)}</ul>
                      </div>
                    )}
                    {maybe.length > 0 && (
                      <details className="rounded-lg border border-line">
                        <summary className="cursor-pointer select-none px-2.5 py-2 text-ink-2">Facoltativo · {maybe.length} {maybe.length === 1 ? 'dato in più' : 'dati in più'} che il bando ammetterebbe (la bozza va bene anche senza)</summary>
                        <ul className="space-y-2 p-2.5 pt-0">{maybe.map((m) => <MissingItem key={m.id} m={m} onUploaded={generate} />)}</ul>
                      </details>
                    )}
                  </div>
                )
              })()}
              {res.notes.length > 0 && (
                <details>
                  <summary className="cursor-pointer select-none text-mute">Come è stata costruita</summary>
                  <div className="space-y-1 pt-1">{res.notes.map((n) => <p key={n} className="text-mute">• {n}</p>)}</div>
                </details>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
