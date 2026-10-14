import React, { useCallback, useEffect, useRef, useState } from 'react'
import { AlertTriangle, CheckCircle2, Download, Eye, FileUp, FlaskConical, Loader2, PackageOpen, Trash2, X } from 'lucide-react'
import { api, download, fileToBase64 } from '../lib/api'
import { createZip, uniqueName } from '../lib/zip'
import { SectionTitle } from './ui'
import Guide from './Guide'

const TYPES = { COMPANY_REGISTRY: 'Visura camerale', BALANCE_SHEET: 'Bilancio', PAYSLIP: 'Busta paga', F24: 'Modello F24', APPLICATION_DRAFT: 'Bozza di candidatura', OTHER: 'Altro documento aziendale' }
const STATUS = {
  PARSED: ['letto', 'text-emerald-700 border-emerald-500/30'], CONFIRMED: ['confermato', 'text-emerald-700 border-emerald-500/30'],
  NEEDS_REVIEW: ['da verificare', 'text-amber-700 border-amber-500/30'], FAILED: ['non letto', 'text-red-700 border-red-500/30'],
  STORED: ['archiviato', 'text-ink-2 border-line-strong'],
}
const FIELD_LABEL = {
  employee_name: 'Nome (token)', tax_code: 'Codice fiscale (token)', ccnl: 'Contratto (CCNL)', level: 'Livello', period: 'Periodo', gross_monthly_eur: 'Totale competenze del mese (€)',
  net_monthly_eur: 'Netto in busta (€)', tfr_accrual_eur: 'Quota TFR del mese (€)', mensilita: 'Mensilità', ral_annual_eur: 'RAL stimata (€)', fiscal_year: 'Anno del bilancio',
  expense_line: 'Riga di costo', f24_row: 'Riga F24', revenue_eur: 'Ricavi (€)', net_result_eur: 'Utile / perdita dell’esercizio (€)', total_costs_eur: 'Totale costi della produzione (€)', de_minimis_aid_eur: 'Aiuti de minimis dell’esercizio (€)',
  employees_avg: 'Dipendenti (media)', company_name: 'Ragione sociale', vat_number: 'Partita IVA', legal_form: 'Forma giuridica', ateco_code: 'Codice ATECO', province: 'Provincia della sede',
  founded_year: 'Anno di costituzione', employees: 'Dipendenti',
}
const CATS = { PERSONNEL: 'Personale', CAPITAL_ASSETS: 'Beni strumentali', CONSULTING: 'Consulenze', OVERHEAD: 'Spese generali', TRAINING: 'Formazione', OTHER: 'Altro (non agevolabile)' }
// Si mostrano nella pagina solo PDF, immagini raster e testo semplice: mai HTML o SVG, che sul nostro dominio potrebbero eseguire codice.
const VIEWABLE = /^(application\/pdf|text\/plain|image\/(png|jpeg|gif|webp))(;|$)/
const BOM = String.fromCharCode(0xfeff)
const CRLF = String.fromCharCode(13, 10)
const csvCell = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`
const pct = (c) => `${Math.round(c * 100)}%`
const tone = (c, min) => (c >= min ? 'bg-emerald-500' : c >= 0.6 ? 'bg-amber-500' : 'bg-red-500')


const FACT_TITLE = {
  staff_member: 'Organico (persona per persona)', asset_line: 'Libro cespiti', dep_plan_line: 'Piano di ammortamento', supplier_spend: 'Spese dalle fatture ricevute (per voce)', aid_received: 'Aiuti ricevuti',
  capex_plan: 'Investimenti previsti', hiring_plan: 'Piano delle assunzioni', budget_line: 'Budget dell’azienda (per conto)',
  durc: 'DURC', lease: 'Contratto di locazione', rd_credit: 'Credito d’imposta ricerca e sviluppo', loan: 'Finanziamento',
}
const eurTxt = (n) => (n == null ? '—' : Number(n).toLocaleString('it-IT', { style: 'currency', currency: 'EUR' }))
const TYPE_LABEL = {}                                    // codice della voce di spesa → etichetta, caricata una volta
function factRow(key, p) {
  const t = (c) => TYPE_LABEL[c] || (c ? c : 'da classificare')
  switch (key) {
    case 'staff_member': return [`${p.role || 'Persona'}${p.ref ? ` (${p.ref})` : ''}`, `livello ${p.level} · ${(p.contract || '').toLowerCase()} · ${p.hours_week || '—'} ore`, eurTxt(p.ral_eur)]
    case 'asset_line': return [`${p.description}`, `${p.class} · acquisto ${p.purchase_year || '—'} · residuo ${eurTxt(p.net_eur)}`, eurTxt(p.cost_eur)]
    case 'dep_plan_line': return [p.description, Object.entries(p.plan || {}).filter(([, v]) => v).map(([y, v]) => `${y}: ${eurTxt(v)}`).join(' · ') || 'già ammortizzato', eurTxt(p.net_eur)]
    case 'supplier_spend': return [`${p.year} · ${t(p.expense_type)}`, `${p.invoices} fatture`, eurTxt(p.amount_eur)]
    case 'aid_received': return [`${p.measure}`, `${p.granted} · ${p.entity} · ${p.regime}`, eurTxt(p.amount_eur)]
    case 'capex_plan': return [p.description, `anno ${p.year} · ${t(p.expense_type)}`, eurTxt(p.amount_eur)]
    case 'hiring_plan': return [`${p.role} (${p.position})`, `ingresso ${p.start} · livello ${p.level} · ${p.area}`, eurTxt(p.annual_cost_eur)]
    case 'durc': return [`DURC ${p.outcome}`, `emesso ${p.issued || '—'} · scade ${p.expires}`, p.protocol || '']
    case 'lease': return ['Canone annuo', `dal ${p.from || '—'} al ${p.to || '—'}`, eurTxt(p.annual_rent_eur)]
    case 'rd_credit': return [`Credito ${p.year || ''} (${p.rate_pct}%)`, `costi ammissibili ${eurTxt(p.eligible_costs_eur)}`, eurTxt(p.credit_eur)]
    case 'loan': return ['Finanziamento', `erogato il ${p.disbursed} · ${p.installments} rate`, eurTxt(p.original_eur)]
    case 'budget_line': return [p.description, `${p.year} · conto ${p.code} · ${t(p.expense_type)}`, eurTxt(p.amount_eur)]
    default: return [key, '', '']
  }
}

/** I dati letti da un foglio Excel, per tipo: ogni riga dice cosa è stato letto e da quale foglio e riga; sono ciò che QUANTO usa per il personale, gli investimenti e le spese per voce. */
function SheetFacts({ fields }) {
  const [more, setMore] = useState({})
  const [, force] = useState(0)
  useEffect(() => { if (!Object.keys(TYPE_LABEL).length) api.expenseTypes().then((r) => { r.types.forEach((t) => { TYPE_LABEL[t.code] = t.label }); force((x) => x + 1) }).catch(() => {}) }, [])
  const groups = {}
  fields.forEach((f) => { if (f.parsed) (groups[f.field_key] = groups[f.field_key] || []).push(f) })
  return (
    <div className="space-y-4">
      {Object.entries(groups).map(([key, list]) => {
        const shown = more[key] ? list : list.slice(0, 10)
        return (
          <div key={key} className="space-y-1.5">
            <p className="text-xs font-medium text-ink">{FACT_TITLE[key] || key} <span className="text-mute font-normal">· {list.length} {list.length === 1 ? 'riga letta' : 'righe lette'} da «{list[0].snippet.split(',')[0]}»</span></p>
            <div className="overflow-x-auto"><table className="w-full text-xs"><tbody>
              {shown.map((f) => { const [a, b, c] = factRow(key, f.parsed); return <tr key={f.id} className="border-t border-line" title={f.snippet}><td className="py-1 pr-3 text-ink-2">{a}</td><td className="pr-3 text-mute">{b}</td><td className="text-right tabular-nums">{c}</td></tr> })}
            </tbody></table></div>
            {list.length > 10 && <button className="text-[11px] underline text-ink-2" onClick={() => setMore({ ...more, [key]: !more[key] })}>{more[key] ? 'Mostra meno' : `Mostra tutte le ${list.length} righe`}</button>}
          </div>
        )
      })}
    </div>
  )
}

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
  const shown = f.parsed ? (f.field_key === 'expense_line' ? `${f.parsed.description} — ${f.parsed.amount_eur} €` : `${f.parsed.codice_tributo}${f.parsed.anno ? ` / ${f.parsed.anno}` : ''} — ${f.parsed.importo_credito_eur ? `credito compensato ${f.parsed.importo_credito_eur}` : f.parsed.importo_debito_eur} €`) : f.value
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

function Detail({ id, onChanged, onUsePayslip, onUseBalance, onUseDraft }) {
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
  const useDraft = async () => {
    setMsg(null)
    try {
      const r = await api.fcDraftItems(id)
      if (!r.cost_items.length) { setMsg('Nessuna voce pronta: conferma prima le righe da verificare qui sopra.'); return }
      onUseDraft(r)
    } catch (e) { setMsg(e.message) }
  }
  return (
    <div className="card p-5 space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <SectionTitle>{TYPES[doc.doc_type]} · {doc.filename}</SectionTitle>
        <span className={`px-1.5 py-0.5 rounded border text-xs ${STATUS[doc.status][1]}`}>{STATUS[doc.status][0]}</span>
        {doc.status === 'STORED'
          ? <span className="text-xs text-mute">Conservato cifrato; QUANTO non lo legge, resta nel tuo archivio aziendale.</span>
          : doc.method === 'xlsx' ? <span className="text-xs text-mute">Foglio Excel letto · {doc.pages} fogli · {doc.fields.length} dati letti</span>
          : doc.doc_type === 'OTHER' ? <span className="text-xs text-mute">Documento letto · {doc.fields.length} dati letti</span>
          : <span className="text-xs text-mute">{doc.method} · {doc.pages} pag. · lettura media {doc.mean_confidence != null ? pct(doc.mean_confidence) : '—'} · soglia {pct(doc.confidence_min)}</span>}
        <button className="btn ml-auto !py-1" onClick={async () => download(await api.fcFile(id), doc.filename)}><Download className="w-3 h-3" />Originale</button>
      </div>
      {doc.error && <p className="text-xs text-red-700 flex gap-2"><AlertTriangle className="w-4 h-4 shrink-0" />{doc.error}</p>}
      {doc.fields.length > 0 && doc.fields.every((f) => f.parsed && FACT_TITLE[f.field_key]) ? <SheetFacts fields={doc.fields} /> : <div className="space-y-2">{doc.fields.map((f) => <FieldRow key={f.id} f={f} doc={doc} min={doc.confidence_min} onDone={done} />)}</div>}
      <div className="flex flex-wrap items-center gap-2 pt-1">
        {doc.doc_type === 'PAYSLIP' && doc.status !== 'FAILED' && <button className="btn-primary" onClick={usePayslip}>Aggiungi al budget come voce di personale</button>}
        {doc.doc_type === 'BALANCE_SHEET' && doc.status !== 'FAILED' && <button className="btn-primary" onClick={() => onUseBalance(id)}>Usa per l’allocazione annuale</button>}
        {doc.doc_type === 'APPLICATION_DRAFT' && doc.status !== 'FAILED' && <button className="btn-primary" onClick={useDraft}>Usa tutte le voci nel Budget</button>}
        {msg && <span className="text-xs text-amber-700">{msg}</span>}
      </div>
    </div>
  )
}

export default function Documents({ onUsePayslip, onUseBalance, onUseDraft, onProfileChanged, refreshKey = 0, defaultType = 'COMPANY_REGISTRY' }) {
  const [list, setList] = useState([])
  const [type, setType] = useState(defaultType)
  const [open, setOpen] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const file = useRef(null)
  const load = useCallback(() => api.fcDocuments().then(setList).catch((e) => setError(e.message)), [])
  useEffect(() => { load() }, [load, refreshKey])          // refreshKey: un documento caricato altrove (procedura guidata) compare anche qui
  // ogni documento letto o confermato aggiorna il profilo aziendale (i valori inseriti a mano restano)
  const refresh = useCallback(async () => {
    await load()
    try { await api.profileSync(); onProfileChanged?.() } catch { /* il profilo si aggiorna comunque alla prossima apertura */ }
  }, [load, onProfileChanged])
  // Aprire o scaricare i file che l'azienda ha allegato: il server li decifra solo per il proprietario.
  const [working, setWorking] = useState(null)
  const [viewer, setViewer] = useState(null)                              // { name, url, type, doc }
  const closeViewer = () => { if (viewer) URL.revokeObjectURL(viewer.url); setViewer(null) }
  useEffect(() => () => { if (viewer) URL.revokeObjectURL(viewer.url) }, [viewer])
  const openFile = async (d) => {
    setError(null); setWorking(`open-${d.id}`)
    try {
      const blob = await api.fcFile(d.id)
      const type = d.content_type || blob.type
      if (!VIEWABLE.test(type)) { download(blob, d.filename); return }       // fogli Excel e simili: nessuna anteprima, si scaricano
      setViewer({ name: d.filename, type, doc: d, url: URL.createObjectURL(new Blob([blob], { type })) })
    } catch (e) { setError(e.message) } finally { setWorking(null) }
  }
  const saveFile = async (d) => {
    setError(null); setWorking(d.id)
    try { download(await api.fcFile(d.id), d.filename) } catch (e) { setError(e.message) } finally { setWorking(null) }
  }
  const saveAll = async () => {
    setError(null); setWorking('all')
    try {
      const used = new Set()
      const files = []
      const rows = [['cartella', 'file', 'tipo', 'stato', 'caricato il', 'dimensione (byte)', 'impronta SHA-256']]
      for (const d of [...list].reverse()) {
        const folder = (TYPES[d.doc_type] || 'Altro').replace(/[\/:*?"<>|]/g, '-')
        const name = uniqueName(`${folder}/${d.filename.replace(/[\/:*?"<>|]/g, '-')}`, used)
        files.push({ name, data: new Uint8Array(await (await api.fcFile(d.id)).arrayBuffer()) })
        rows.push([folder, name.split('/').pop(), TYPES[d.doc_type], STATUS[d.status]?.[0] || d.status, d.created_at.slice(0, 10), d.size_bytes, d.sha256])
      }
      files.push({ name: 'elenco_documenti.csv', data: new TextEncoder().encode(BOM + rows.map((r) => r.map(csvCell).join(';')).join(CRLF) + CRLF) })
      download(createZip(files), `documenti-azienda-${new Date().toISOString().slice(0, 10)}.zip`)
    } catch (e) { setError(e.message) } finally { setWorking(null) }
  }
  const remove = async (d) => {
    if (!window.confirm(`Eliminare «${d.filename}»? I dati che ne derivano escono dal profilo.`)) return
    await api.fcDelete(d.id); if (open === d.id) setOpen(null); refresh()
  }
  // L'azienda di prova (Meridiana): sostituisce i file con lo stesso nome già presenti con l'ultima versione e carica gli altri, uno alla volta.
  const [demo, setDemo] = useState(null)                              // { done, total, name }
  const loadDemo = async () => {
    setError(null); setDemo({ done: 0, total: 0, name: 'elenco dei file' })
    try {
      const man = await (await fetch('/azienda_di_prova/manifest.json', { cache: 'no-store' })).json()
      const total = man.files.length
      let existing = await api.fcDocuments()
      for (let i = 0; i < total; i++) {
        const m = man.files[i]
        setDemo({ done: i, total, name: m.file })
        for (const d of existing.filter((x) => x.filename === m.file)) await api.fcDelete(d.id)
        const blob = await (await fetch(`/azienda_di_prova/${encodeURIComponent(m.file)}`, { cache: 'no-store' })).blob()
        await api.fcUpload({ doc_type: m.doc_type, filename: m.file, content_base64: await fileToBase64(blob) })
      }
      await refresh()
      setDemo({ done: total, total, name: '' })
    } catch (e) { setError(`Caricamento dell'azienda di prova interrotto: ${e.message}`); setDemo(null) }
  }
  const upload = async (f) => {
    if (!f) return
    setBusy(true); setError(null)
    try { const d = await api.fcUpload({ doc_type: type, filename: f.name, content_base64: await fileToBase64(f) }); await refresh(); setOpen(d.id) } catch (e) { setError(e.message) } finally { setBusy(false); if (file.current) file.current.value = '' }
  }
  return (
    <div className="space-y-6">
      <Guide page="documents" />
      <div className="card p-5 space-y-3">
        <SectionTitle icon={FileUp}>Carica un documento</SectionTitle>
        <p className="text-xs text-ink-2 leading-relaxed">Visura camerale, bilanci, buste paga, F24 o una bozza di candidatura già scritta in PDF (anche scansionati, se il server ha il lettore OCR); i fogli Excel che QUANTO riconosce (registro del personale, libro cespiti, registro delle fatture, budget, piano degli investimenti e delle assunzioni, registro degli aiuti) vengono letti e usati; qualunque altro documento aziendale (DURC, contratti…) si archivia senza essere letto. Ogni campo letto ha una percentuale di sicurezza: sotto la soglia lo controlli tu prima di usarlo. Nomi e codici fiscali diventano codici anonimi; il file è conservato cifrato.</p>
        <div className="flex flex-wrap items-center gap-3">
          <select className="field !w-auto" value={type} onChange={(e) => setType(e.target.value)}>{Object.entries(TYPES).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
          <input ref={file} type="file" accept={type === 'OTHER' ? undefined : '.pdf'} className="hidden" onChange={(e) => upload(e.target.files?.[0])} />
          <button className="btn-primary" disabled={busy} onClick={() => file.current?.click()}>{busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FileUp className="w-3.5 h-3.5" />}{type === 'OTHER' ? 'Scegli il file' : 'Scegli il PDF'}</button>
        </div>
        {error && <p className="text-xs text-red-700">{error}</p>}
        <div className="pt-3 border-t border-line flex flex-wrap items-center gap-3">
          <button className="btn" disabled={busy || (demo && demo.done < demo.total) || demo?.total === 0} onClick={loadDemo} title="Carica tutti i documenti di Meridiana Digital Solutions (organico, buste paga, bilanci, fogli Excel…); quelli con lo stesso nome già presenti vengono sostituiti con l'ultima versione">
            {demo && demo.done < demo.total ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FlaskConical className="w-3.5 h-3.5" />}Carica l’azienda di prova
          </button>
          <span className="text-xs text-mute">{demo && demo.total === 0 ? 'Preparo l’elenco…' : demo && demo.done < demo.total ? `Carico ${demo.done + 1} di ${demo.total}: ${demo.name}` : demo ? `Fatto: ${demo.total} documenti aggiornati all’ultima versione.` : 'Meridiana Digital Solutions: visura, bilanci, business plan, fogli Excel… sempre l’ultima versione.'}</span>
        </div>
      </div>
      <div className="card p-5 space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <SectionTitle>I tuoi documenti ({list.length})</SectionTitle>
          {list.length > 0 && <button className="btn !py-1 ml-auto" disabled={working === 'all'} onClick={saveAll} title="Un archivio ZIP con tutti i file allegati, divisi per tipo, e l'elenco in CSV">
            {working === 'all' ? <Loader2 className="w-3 h-3 animate-spin" /> : <PackageOpen className="w-3 h-3" />}Scarica tutti i file (ZIP)</button>}
        </div>
        {list.length === 0 && <p className="text-xs text-mute">Nessun documento ancora.</p>}
        {list.map((d) => (
          <div key={d.id} className="flex flex-wrap items-center gap-2 text-xs p-2 rounded-xl border border-line bg-field">
            <button onClick={() => setOpen(d.id)} className="font-medium text-ink hover:underline">{TYPES[d.doc_type]} · {d.filename}</button>
            <span className={`px-1.5 py-0.5 rounded border ${STATUS[d.status][1]}`}>{STATUS[d.status][0]}</span>
            <span className="text-mute">{d.fields} campi{d.to_review ? ` · ${d.to_review} da verificare` : ''} · {d.created_at.slice(0, 10)}</span>
            <span className="ml-auto flex flex-wrap items-center gap-1.5">
              <button className="btn !py-1" disabled={working === `open-${d.id}`} onClick={() => openFile(d)} title="Guarda il file qui, senza scaricarlo">{working === `open-${d.id}` ? <Loader2 className="w-3 h-3 animate-spin" /> : <Eye className="w-3 h-3" />}Apri</button>
              <button className="btn !py-1" disabled={working === d.id} onClick={() => saveFile(d)} title="Scarica il file originale">{working === d.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}Scarica</button>
              <button className="btn !py-1" onClick={() => remove(d)}><Trash2 className="w-3 h-3" />Elimina</button>
            </span>
          </div>
        ))}
      </div>
      {viewer && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-3 md:p-8" role="dialog" aria-modal="true" aria-label={`Anteprima di ${viewer.name}`} onClick={closeViewer}>
          <div className="bg-white rounded-2xl w-full max-w-5xl h-full max-h-[92vh] flex flex-col overflow-hidden shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-2 px-4 py-2.5 border-b border-line">
              <span className="text-sm font-medium truncate">{viewer.name}</span>
              <button className="btn !py-1 ml-auto" onClick={() => saveFile(viewer.doc)}><Download className="w-3 h-3" />Scarica</button>
              <button className="btn !py-1" onClick={closeViewer} aria-label="Chiudi l'anteprima"><X className="w-3 h-3" />Chiudi</button>
            </div>
            {viewer.type.startsWith('image/') ? <div className="flex-1 overflow-auto bg-tint p-4 flex items-start justify-center"><img src={viewer.url} alt={viewer.name} className="max-w-full" /></div>
              : <iframe title={viewer.name} src={viewer.url} className="flex-1 w-full bg-tint" />}
          </div>
        </div>
      )}
      {open && <Detail key={open} id={open} onChanged={refresh} onUsePayslip={onUsePayslip} onUseBalance={onUseBalance} onUseDraft={onUseDraft} />}
    </div>
  )
}
