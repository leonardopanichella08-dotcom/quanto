import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ArrowLeft, ArrowRight, Building2, CheckCircle2, ClipboardCheck, FileText, FolderOpen, HelpCircle, Landmark, Loader2, PartyPopper, Receipt, Upload, X } from 'lucide-react'
import { api, fileToBase64 } from '../lib/api'
import { fmtEur } from '../lib/format'
import { FieldInput } from './CompanyProfile'

const TYPE_LABEL = { COMPANY_REGISTRY: 'Visura camerale', BALANCE_SHEET: 'Bilancio', PAYSLIP: 'Busta paga', F24: 'Modello F24', APPLICATION_DRAFT: 'Bozza di candidatura', OTHER: 'Altro documento' }
const STATUS = { PARSED: 'letto', CONFIRMED: 'confermato', NEEDS_REVIEW: 'da verificare', FAILED: 'non letto', STORED: 'archiviato' }

/** Il tipo di documento si propone dal nome del file; l'utente lo può cambiare prima di caricare. Solo i PDF vengono letti. */
export function detectType(name) {
  const n = name.toLowerCase()
  if (!n.endsWith('.pdf')) return 'OTHER'
  if (/visura|camerale|registro[ _-]imprese/.test(n)) return 'COMPANY_REGISTRY'
  if (/bilancio|balance/.test(n)) return 'BALANCE_SHEET'
  if (/f24/.test(n)) return 'F24'
  if (/busta|cedolino|payslip|paga_|_paga/.test(n)) return 'PAYSLIP'
  if (/bozza|candidatura|domanda/.test(n)) return 'APPLICATION_DRAFT'
  return 'OTHER'
}

function Uploader({ fixedType, onUploaded, hint }) {
  const input = useRef(null)
  const [items, setItems] = useState([])          // {file, type, state, message}
  const [busy, setBusy] = useState(false)
  const [drag, setDrag] = useState(false)

  const add = (files) => setItems((cur) => [...cur, ...[...files].map((f) => ({ file: f, type: fixedType || detectType(f.name), state: 'ready' }))])
  const upload = async () => {
    setBusy(true)
    const next = [...items]
    for (let i = 0; i < next.length; i += 1) {
      if (next[i].state !== 'ready') continue
      next[i] = { ...next[i], state: 'busy' }; setItems([...next])
      try {
        const d = await api.fcUpload({ doc_type: next[i].type, filename: next[i].file.name, content_base64: await fileToBase64(next[i].file) })
        next[i] = { ...next[i], state: 'done', message: `${STATUS[d.status] || d.status}${d.fields?.length ? ` · ${d.fields.length} campi` : ''}` }
      } catch (e) { next[i] = { ...next[i], state: 'error', message: e.message } }
      setItems([...next])
    }
    try { await api.profileSync() } catch { /* il profilo si aggiorna comunque alla prossima apertura */ }
    setBusy(false)
    onUploaded?.()
  }
  const pending = items.filter((i) => i.state === 'ready').length

  return (
    <div className="space-y-3">
      <div onDragOver={(e) => { e.preventDefault(); setDrag(true) }} onDragLeave={() => setDrag(false)} onDrop={(e) => { e.preventDefault(); setDrag(false); add(e.dataTransfer.files) }}
        onClick={() => input.current?.click()} role="button" tabIndex={0} onKeyDown={(e) => { if (e.key === 'Enter') input.current?.click() }}
        className={`cursor-pointer rounded-2xl border-2 border-dashed p-6 text-center transition ${drag ? 'border-brand bg-brand/10' : 'border-line-strong hover:border-brand/60 bg-field'}`}>
        <Upload className="w-6 h-6 mx-auto text-ink-2" />
        <p className="text-sm font-medium mt-2">Trascina qui i file o clicca per scegliere</p>
        <p className="text-xs text-mute mt-1">{hint || 'PDF e fogli Excel; puoi sceglierne più di uno insieme'}</p>
        <input ref={input} type="file" multiple className="hidden" accept={fixedType && fixedType !== 'OTHER' ? '.pdf' : undefined} onChange={(e) => { add(e.target.files); e.target.value = '' }} />
      </div>
      {items.length > 0 && (
        <ul className="space-y-1.5">
          {items.map((it, i) => (
            <li key={`${it.file.name}-${i}`} className="flex flex-wrap items-center gap-2 text-xs p-2 rounded-xl border border-line bg-field">
              <FileText className="w-3.5 h-3.5 text-mute shrink-0" />
              <span className="font-medium truncate max-w-[16rem]" title={it.file.name}>{it.file.name}</span>
              {it.state === 'ready' && !fixedType
                ? <select className="field !w-auto !py-0.5 text-xs" value={it.type} aria-label={`Tipo di ${it.file.name}`} onChange={(e) => setItems((cur) => cur.map((c, k) => (k === i ? { ...c, type: e.target.value } : c)))}>
                  {Object.entries(TYPE_LABEL).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
                : <span className="text-mute">{TYPE_LABEL[it.type]}</span>}
              <span className="ml-auto flex items-center gap-1.5">
                {it.state === 'busy' && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                {it.state === 'done' && <span className="text-emerald-700 inline-flex items-center gap-1"><CheckCircle2 className="w-3.5 h-3.5" />{it.message}</span>}
                {it.state === 'error' && <span className="text-red-700">{it.message}</span>}
                {it.state === 'ready' && <button className="text-mute hover:text-ink" aria-label="Togli" onClick={() => setItems((cur) => cur.filter((_, k) => k !== i))}><X className="w-3.5 h-3.5" /></button>}
              </span>
            </li>
          ))}
        </ul>
      )}
      {pending > 0 && <button className="btn-primary" disabled={busy} onClick={upload}>{busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}Carica {pending} {pending === 1 ? 'file' : 'file'}</button>}
    </div>
  )
}

/** Passo «domande»: i dati che nessun documento può dire. */
function Questions({ ov, onSaved }) {
  const missing = ov.fields.filter((f) => f.required && (f.value === null || f.value === undefined))
  const [vals, setVals] = useState({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const save = async (extra) => {
    setBusy(true); setError(null)
    try { await api.saveProfile({ ...vals, ...(extra || {}) }); setVals({}); onSaved() } catch (e) { setError(e.message) } finally { setBusy(false) }
  }
  if (missing.length === 0) return <p className="text-sm text-emerald-700 inline-flex items-center gap-2"><CheckCircle2 className="w-4 h-4" />Hai risposto a tutto.</p>
  return (
    <div className="space-y-4">
      {missing.map((f) => (
        <div key={f.key} className="space-y-1.5">
          <span className="label">{f.label}</span>
          {f.kind === 'bool'
            ? <div className="flex gap-2">
              <button className="btn-primary" disabled={busy} onClick={() => save({ [f.key]: true })}>Sì</button>
              <button className="btn" disabled={busy} onClick={() => save({ [f.key]: false })}>No</button></div>
            : <FieldInput f={f} regions={ov.regions} value={vals[f.key]} onChange={(v) => setVals((d) => ({ ...d, [f.key]: v }))} />}
          {f.key === 'is_innovative_startup' && <p className="text-[11px] text-mute">Rispondi «Sì» solo se sei iscritta alla sezione speciale del Registro delle Imprese: la visura lo riporta. Alcuni bandi sono riservati a chi lo è.</p>}
        </div>
      ))}
      {missing.some((f) => f.kind !== 'bool') && <button className="btn-primary" disabled={busy || Object.values(vals).every((v) => v === undefined || v === '')} onClick={() => save()}>Salva le risposte</button>}
      {error && <p className="text-xs text-red-700">{error}</p>}
    </div>
  )
}

export default function ProfileSetup({ version = 0, onChanged, onGoAllocation, onGoDocuments }) {
  const [ov, setOv] = useState(null)
  const [docs, setDocs] = useState([])
  const [step, setStep] = useState(null)
  const [error, setError] = useState(null)
  const touched = useRef(false)

  const load = useCallback(async () => {
    try { const [o, d] = await Promise.all([api.profile(), api.fcDocuments()]); setOv(o); setDocs(d); setError(null) } catch (e) { setError(e.message) }
  }, [])
  useEffect(() => { load() }, [load, version])
  const changed = useCallback(async () => { await load(); onChanged?.() }, [load, onChanged])

  const has = (type) => docs.some((d) => d.doc_type === type)
  const filled = (k) => ov?.fields.find((f) => f.key === k)?.value != null
  const finYears = ov?.financials.filter((f) => f.values.revenue_eur != null) || []
  const lastComplete = ov && ov.last_year != null && !ov.missing.some((m) => m.scope === 'financial')

  const steps = useMemo(() => {
    if (!ov) return []
    return [
      { id: 'all', icon: FolderOpen, title: 'Carica i documenti dell’azienda', optional: false, done: docs.length > 0,
        text: 'Trascina insieme tutto quello che hai: visura camerale, bilanci, buste paga, F24, bozze di candidatura e ogni altro documento. QUANTO riconosce il tipo dal nome del file (lo puoi correggere) e legge quello che può.' },
      { id: 'registry', icon: Building2, title: 'Visura camerale', done: filled('legal_name') && filled('vat_number') && filled('ateco_code'),
        text: 'Dalla visura ricavo ragione sociale, partita IVA, forma giuridica, codice ATECO, sede e anno di costituzione.' },
      { id: 'balance', icon: Landmark, title: 'Bilancio dell’ultimo esercizio', done: !!lastComplete,
        text: 'È la base della stima dell’anno successivo: ricavi, utile, dipendenti e i costi per categoria (personale, beni strumentali, consulenze, spese generali, formazione).' },
      { id: 'history', icon: Receipt, title: 'Bilanci degli anni precedenti', optional: true, done: finYears.length >= 2,
        text: 'Con due o più bilanci posso suggerirti di quanto sono cresciuti i tuoi costi. Non è obbligatorio: la variazione la scegli sempre tu.' },
      { id: 'questions', icon: HelpCircle, title: 'Due domande che nessun documento può dire', done: ov.missing.filter((m) => m.scope === 'profile').length === 0,
        text: 'Servono per capire a quali bandi puoi partecipare.' },
      { id: 'review', icon: ClipboardCheck, title: 'Controllo delle righe incerte', done: ov.documents.to_review === 0,
        text: 'Quando una lettura non è abbastanza sicura non entra nei calcoli finché non la confermi tu.' },
      { id: 'extra', icon: FileText, title: 'Altri documenti (facoltativo)', optional: true, done: has('PAYSLIP') || has('F24') || has('OTHER') || has('APPLICATION_DRAFT'),
        text: 'Buste paga, F24, DURC, dichiarazioni de minimis, business plan: vengono archiviati cifrati e le buste paga e le bozze si possono usare nel Budget.' },
      { id: 'end', icon: PartyPopper, title: 'Profilo completo', done: ov.completeness_pct === 100, text: '' },
    ]
  }, [ov, docs]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {          // si parte dal primo passo obbligatorio non ancora fatto, finché l'utente non sceglie da sé
    if (steps.length && !touched.current) {
      const first = steps.findIndex((s) => !s.done && !s.optional)
      setStep(first === -1 ? steps.length - 1 : first)
    }
  }, [steps])

  if (error && !ov) return <p className="text-xs text-red-700">{error}</p>
  if (!ov || step === null) return <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Carico la configurazione…</p>

  const s = steps[step]
  const Icon = s.icon
  const go = (n) => { touched.current = true; setStep(Math.max(0, Math.min(steps.length - 1, n))) }
  const pct = ov.completeness_pct
  const doneAll = pct === 100 && ov.documents.to_review === 0

  return (
    <div className="card overflow-hidden" aria-label="Configurazione guidata del profilo">
      <div className="px-5 pt-4 pb-3 border-b border-line bg-tint space-y-3">
        <div className="flex gap-1.5" role="tablist" aria-label="Passi">
          {steps.map((x, i) => (
            <button key={x.id} role="tab" aria-selected={i === step} aria-label={x.title} onClick={() => go(i)} className="flex-1 h-6 flex items-center group">
              <span className={`block w-full h-1.5 rounded-full transition ${x.done ? 'bg-emerald-500' : i === step ? 'bg-brand' : 'bg-tint-2 group-hover:bg-line-strong'}`} />
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3 text-xs text-ink-2">
          <span className="font-medium text-ink">Configura l’azienda del lavoro</span>
          <span>passo {step + 1} di {steps.length}</span>
          <span className="ml-auto tabular-nums font-semibold text-ink">{pct}% completo</span>
        </div>
      </div>

      <div key={s.id} className="story-in p-6 md:p-8 space-y-5 min-h-[18rem]">
        <div className="flex items-start gap-4">
          <span className="icon-tile w-14 h-14 rounded-3xl shrink-0"><Icon className="w-7 h-7" /></span>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-2xl md:text-3xl font-display font-bold tracking-tight leading-tight">{s.title}</h3>
              {s.done && s.id !== 'end' && <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500/15 text-emerald-700 border border-emerald-500/30 inline-flex items-center gap-1"><CheckCircle2 className="w-3 h-3" />fatto</span>}
              {s.optional && <span className="px-2 py-0.5 rounded-full text-[11px] text-mute border border-line-strong">facoltativo</span>}
            </div>
            {s.text && <p className="text-sm text-ink-2 mt-1.5 leading-relaxed max-w-2xl">{s.text}</p>}
          </div>
        </div>

        {s.id === 'all' && <Uploader onUploaded={changed} />}
        {s.id === 'registry' && (
          <div className="space-y-3">
            {s.done
              ? <ul className="grid sm:grid-cols-2 gap-x-6 gap-y-1.5 text-sm">{ov.fields.filter((f) => ['legal_name', 'vat_number', 'legal_form', 'ateco_code', 'region', 'founded_year', 'employees'].includes(f.key) && f.value != null).map((f) => (
                <li key={f.key} className="flex gap-2"><CheckCircle2 className="w-4 h-4 mt-0.5 text-emerald-600 shrink-0" /><span><span className="text-mute">{f.label}: </span><span className="font-medium">{String(f.value)}</span></span></li>))}</ul>
              : <Uploader fixedType="COMPANY_REGISTRY" hint="La visura in PDF, anche scansionata" onUploaded={changed} />}
          </div>
        )}
        {s.id === 'balance' && (
          <div className="space-y-3">
            {s.done && (() => { const f = ov.financials[ov.financials.length - 1]; return (
              <ul className="grid sm:grid-cols-2 gap-x-6 gap-y-1.5 text-sm">
                {[['Esercizio', f.fiscal_year], ['Ricavi', fmtEur(f.values.revenue_eur)], ['Utile (perdita)', f.values.net_result_eur != null ? fmtEur(f.values.net_result_eur) : '—'], ['Costi del personale', fmtEur(f.values.personnel_eur)],
                  ['Consulenze', fmtEur(f.values.consulting_eur)], ['Beni strumentali', fmtEur(f.values.capital_assets_eur)]].map(([l, v]) => (
                  <li key={l} className="flex gap-2"><CheckCircle2 className="w-4 h-4 mt-0.5 text-emerald-600 shrink-0" /><span><span className="text-mute">{l}: </span><span className="font-medium">{v}</span></span></li>))}</ul>) })()}
            {!s.done && <p className="text-xs text-amber-700">{ov.missing.filter((m) => m.scope === 'financial').map((m) => m.label).slice(0, 4).join(' · ') || 'Nessun bilancio ancora.'}</p>}
            {!s.done && <Uploader fixedType="BALANCE_SHEET" hint="Il bilancio in PDF (schema civilistico): carica quello dell’ultimo esercizio chiuso" onUploaded={changed} />}
          </div>
        )}
        {s.id === 'history' && (
          <div className="space-y-3">
            <p className="text-sm">Esercizi presenti: <span className="font-semibold">{finYears.map((f) => f.fiscal_year).join(', ') || 'nessuno'}</span></p>
            <Uploader fixedType="BALANCE_SHEET" hint="Bilanci degli esercizi precedenti, in PDF" onUploaded={changed} />
          </div>
        )}
        {s.id === 'questions' && <Questions ov={ov} onSaved={changed} />}
        {s.id === 'review' && (
          <div className="space-y-3">
            {ov.documents.to_review === 0
              ? <p className="text-sm text-emerald-700 inline-flex items-center gap-2"><CheckCircle2 className="w-4 h-4" />Tutte le letture sono sicure o confermate.</p>
              : <><p className="text-sm">{ov.documents.to_review} {ov.documents.to_review === 1 ? 'campo è' : 'campi sono'} da verificare. Aprili nei documenti: «È giusto» o correggi.</p>
                <button className="btn-primary" onClick={onGoDocuments}>Vai ai documenti da verificare</button></>}
          </div>
        )}
        {s.id === 'extra' && <Uploader hint="Buste paga, F24, bozze di candidatura, DURC, de minimis, business plan, Excel…" onUploaded={changed} />}
        {s.id === 'end' && (
          <div className="space-y-4">
            {doneAll
              ? <p className="text-sm text-ink-2 max-w-xl">Il profilo è completo al 100%: ora puoi stimare l’anno successivo e vedere quali bandi fanno per te, oppure partire da una bozza di budget costruita sui tuoi bilanci.</p>
              : <p className="text-sm text-ink-2 max-w-xl">Manca ancora qualcosa: {ov.missing.map((m) => m.label).join(' · ') || 'verifica le righe incerte'}.</p>}
            <div className="flex flex-wrap gap-2">
              <button className="btn-primary" onClick={onGoAllocation}>Stima l’anno e cerca i bandi<ArrowRight className="w-3.5 h-3.5" /></button>
            </div>
          </div>
        )}
      </div>

      <div className="px-5 py-3 border-t border-line bg-tint flex items-center gap-2">
        <button className="btn" disabled={step === 0} onClick={() => go(step - 1)}><ArrowLeft className="w-3.5 h-3.5" />Indietro</button>
        <button className="btn-primary ml-auto" disabled={step === steps.length - 1} onClick={() => go(step + 1)}>{s.done || s.optional ? 'Avanti' : 'Salta per ora'}<ArrowRight className="w-3.5 h-3.5" /></button>
      </div>
    </div>
  )
}
