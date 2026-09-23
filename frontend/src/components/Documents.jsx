import React, { useCallback, useEffect, useRef, useState } from 'react'
import { AlertTriangle, CheckCircle2, Download, FileUp, Loader2, Trash2 } from 'lucide-react'
import { api, download, fileToBase64 } from '../lib/api'
import { SectionTitle } from './ui'
import Guide from './Guide'

const TYPES = { PAYSLIP: 'Busta paga', BALANCE_SHEET: 'Bilancio', F24: 'Modello F24' }
const STATUS = {
  PARSED: ['letto', 'text-emerald-700 border-emerald-500/30'], CONFIRMED: ['confermato', 'text-emerald-700 border-emerald-500/30'],
  NEEDS_REVIEW: ['da verificare', 'text-amber-700 border-amber-500/30'], FAILED: ['non letto', 'text-red-700 border-red-500/30'],
}
const FIELD_LABEL = {
  employee_name: 'Nome (token)', tax_code: 'Codice fiscale (token)', ccnl: 'Contratto (CCNL)', level: 'Livello', period: 'Periodo', gross_monthly_eur: 'Totale competenze del mese (€)',
  net_monthly_eur: 'Netto in busta (€)', tfr_accrual_eur: 'Quota TFR del mese (€)', mensilita: 'Mensilità', ral_annual_eur: 'RAL stimata (€)', fiscal_year: 'Anno del bilancio',
  expense_line: 'Riga di costo', f24_row: 'Riga F24',
}
const CATS = { PERSONNEL: 'Personale', CAPITAL_ASSETS: 'Beni strumentali', CONSULTING: 'Consulenze', OVERHEAD: 'Spese generali', TRAINING: 'Formazione' }
const pct = (c) => `${Math.round(c * 100)}%`
const tone = (c, min) => (c >= min ? 'bg-emerald-500' : c >= 0.6 ? 'bg-amber-500' : 'bg-red-500')

function FieldRow({ f, doc, min, onDone }) {
  const [val, setVal] = useState(f.parsed ? f.parsed.category || '' : f.value || '')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)
  const review = async (action) => {
    setBusy(true); setErr(null)
    try {
      const value = f.field_key === 'expense_line' ? JSON.stringify({ ...f.parsed, category: val || null }) : val
      onDone(await api.fcReview(doc.id, f.id, action, action === 'CORRECT' ? value : undefined))
    } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }
  const shown = f.parsed ? (f.field_key === 'expense_line' ? `${f.parsed.description} — ${f.parsed.amount_eur} €` : `${f.parsed.codice_tributo}${f.parsed.anno ? ` / ${f.parsed.anno}` : ''} — ${f.parsed.importo_debito_eur} €`) : f.value
  return (
    <div className="p-3 rounded-xl border border-line bg-field text-xs space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium text-ink">{FIELD_LABEL[f.field_key] || f.field_key}</span>
        <span className="font-mono text-ink-2 break-all">{shown}</span>
        {f.field_key === 'expense_line' && f.parsed.category && <span className="text-mute">→ {CATS[f.parsed.category]}</span>}
        <span className="ml-auto flex items-center gap-2" title="Sicurezza della lettura">
          <span className="w-16 h-1.5 rounded-full bg-tint-2 overflow-hidden"><span className={`block h-full ${tone(f.confidence, min)}`} style={{ width: pct(f.confidence) }} /></span>
          <span className="tabular-nums text-mute w-8">{pct(f.confidence)}</span>
        </span>
        {f.status === 'CONFIRMED' && <span className="text-emerald-700 inline-flex items-center gap-1"><CheckCircle2 className="w-3 h-3" />confermato</span>}
        {f.status === 'CORRECTED' && <span className="text-emerald-700 inline-flex items-center gap-1"><CheckCircle2 className="w-3 h-3" />corretto</span>}
      </div>
      {f.snippet && <p className="text-[11px] text-mute">Letto da: «{f.snippet}»</p>}
      {f.status === 'NEEDS_REVIEW' && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-amber-700 inline-flex items-center gap-1"><AlertTriangle className="w-3 h-3" />Lettura poco sicura: non entra nei calcoli finché non la verifichi.</span>
          {f.field_key === 'expense_line'
            ? <select className="field !w-auto !py-1" value={val} onChange={(e) => setVal(e.target.value)}><option value="">— categoria —</option>{Object.entries(CATS).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
            : !f.pii && f.field_key !== 'f24_row' && <input className="field !w-40 !py-1" value={val} onChange={(e) => setVal(e.target.value)} aria-label="Valore corretto" />}
          {!f.pii && f.field_key !== 'f24_row' && <button className="btn !py-1" disabled={busy || !val} onClick={() => review('CORRECT')}>{f.field_key === 'expense_line' ? 'Assegna categoria' : 'Correggi'}</button>}
          {(f.field_key !== 'expense_line' || f.parsed.category) && <button className="btn-primary !py-1" disabled={busy} onClick={() => review('CONFIRM')}>{busy && <Loader2 className="w-3 h-3 animate-spin" />}È giusto</button>}
        </div>
      )}
      {err && <p className="text-red-700">{err}</p>}
    </div>
  )
}

function Detail({ id, onChanged, onUsePayslip, onUseBalance }) {
  const [doc, setDoc] = useState(null)
  const [msg, setMsg] = useState(null)
  const load = useCallback(() => api.fcDocument(id).then(setDoc), [id])
  useEffect(() => { load() }, [load])
  if (!doc) return <Loader2 className="w-4 h-4 animate-spin text-brand-ink" />
  const done = (d) => { setDoc(d); onChanged() }
  const usePayslip = async () => {
    setMsg(null)
    try { const r = await api.fcCostLine(id); onUsePayslip(r) } catch (e) { setMsg(e.message) }
  }
  return (
    <div className="card p-5 space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <SectionTitle>{TYPES[doc.doc_type]} · {doc.filename}</SectionTitle>
        <span className={`px-1.5 py-0.5 rounded border text-xs ${STATUS[doc.status][1]}`}>{STATUS[doc.status][0]}</span>
        <span className="text-xs text-mute">{doc.method} · {doc.pages} pag. · lettura media {doc.mean_confidence != null ? pct(doc.mean_confidence) : '—'} · soglia {pct(doc.confidence_min)}</span>
        <button className="btn ml-auto !py-1" onClick={async () => download(await api.fcFile(id), doc.filename)}><Download className="w-3 h-3" />Originale</button>
      </div>
      {doc.error && <p className="text-xs text-red-700 flex gap-2"><AlertTriangle className="w-4 h-4 shrink-0" />{doc.error}</p>}
      <div className="space-y-2">{doc.fields.map((f) => <FieldRow key={f.id} f={f} doc={doc} min={doc.confidence_min} onDone={done} />)}</div>
      <div className="flex flex-wrap items-center gap-2 pt-1">
        {doc.doc_type === 'PAYSLIP' && doc.status !== 'FAILED' && <button className="btn-primary" onClick={usePayslip}>Aggiungi al budget come voce di personale</button>}
        {doc.doc_type === 'BALANCE_SHEET' && doc.status !== 'FAILED' && <button className="btn-primary" onClick={() => onUseBalance(id)}>Usa per l’allocazione annuale</button>}
        {msg && <span className="text-xs text-amber-700">{msg}</span>}
      </div>
    </div>
  )
}

export default function Documents({ onUsePayslip, onUseBalance }) {
  const [list, setList] = useState([])
  const [type, setType] = useState('PAYSLIP')
  const [open, setOpen] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const file = useRef(null)
  const load = useCallback(() => api.fcDocuments().then(setList).catch((e) => setError(e.message)), [])
  useEffect(() => { load() }, [load])
  const upload = async (f) => {
    if (!f) return
    setBusy(true); setError(null)
    try { const d = await api.fcUpload({ doc_type: type, filename: f.name, content_base64: await fileToBase64(f) }); await load(); setOpen(d.id) } catch (e) { setError(e.message) } finally { setBusy(false); if (file.current) file.current.value = '' }
  }
  return (
    <div className="space-y-6">
      <Guide page="documents" />
      <div className="card p-5 space-y-3">
        <SectionTitle icon={FileUp}>Carica un documento</SectionTitle>
        <p className="text-xs text-ink-2 leading-relaxed">PDF di buste paga, bilanci o F24 (anche scansionati, se il server ha il lettore OCR). Ogni campo letto ha una percentuale di sicurezza: sotto la soglia lo controlli tu prima di usarlo. Nomi e codici fiscali diventano codici anonimi; il file è conservato cifrato.</p>
        <div className="flex flex-wrap items-center gap-3">
          <select className="field !w-auto" value={type} onChange={(e) => setType(e.target.value)}>{Object.entries(TYPES).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
          <input ref={file} type="file" accept=".pdf" className="hidden" onChange={(e) => upload(e.target.files?.[0])} />
          <button className="btn-primary" disabled={busy} onClick={() => file.current?.click()}>{busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FileUp className="w-3.5 h-3.5" />}Scegli il PDF</button>
        </div>
        {error && <p className="text-xs text-red-700">{error}</p>}
      </div>
      <div className="card p-5 space-y-2">
        <SectionTitle>I tuoi documenti ({list.length})</SectionTitle>
        {list.length === 0 && <p className="text-xs text-mute">Nessun documento ancora.</p>}
        {list.map((d) => (
          <div key={d.id} className="flex flex-wrap items-center gap-2 text-xs p-2 rounded-xl border border-line bg-field">
            <button onClick={() => setOpen(d.id)} className="font-medium text-ink hover:underline">{TYPES[d.doc_type]} · {d.filename}</button>
            <span className={`px-1.5 py-0.5 rounded border ${STATUS[d.status][1]}`}>{STATUS[d.status][0]}</span>
            <span className="text-mute">{d.fields} campi{d.to_review ? ` · ${d.to_review} da verificare` : ''} · {d.created_at.slice(0, 10)}</span>
            <button className="btn !py-1 ml-auto" onClick={async () => { await api.fcDelete(d.id); if (open === d.id) setOpen(null); load() }}><Trash2 className="w-3 h-3" />Elimina</button>
          </div>
        ))}
      </div>
      {open && <Detail key={open} id={open} onChanged={load} onUsePayslip={onUsePayslip} onUseBalance={onUseBalance} />}
    </div>
  )
}
