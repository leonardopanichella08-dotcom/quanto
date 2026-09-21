import React, { useCallback, useEffect, useState } from 'react'
import { AlertTriangle, CheckCircle2, Download, FileUp, Loader2, Trash2 } from 'lucide-react'
import { api, download, fileToBase64 } from '../../lib/api'
import { SectionTitle } from '../ui'

const STATUS_STYLE = { DRAFT: 'text-amber-700 border-amber-500/30', PUBLISHED: 'text-emerald-700 border-emerald-500/30', SUPERSEDED: 'text-mute border-line-strong' }
const STATUS_LABEL = { DRAFT: 'bozza', PUBLISHED: 'pubblicato', SUPERSEDED: 'sostituito' }

function Upload({ kinds, onDone }) {
  const empty = { kind: 'CCNL', code: '', name: '', version: '', valid_from: '', valid_to: '', source_name: '', source_url: '', source_ref: '', notes: '' }
  const [f, setF] = useState(empty)
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })
  const ok = f.code && f.name && f.version && f.valid_from && f.source_name && (f.source_url || f.source_ref) && file
  const send = async () => {
    setBusy(true); setError(null)
    try {
      await api.fbUpload({ ...f, valid_to: f.valid_to || null, source_url: f.source_url || null, source_ref: f.source_ref || null, notes: f.notes || null,
        filename: file.name, content_base64: await fileToBase64(file) })
      setF(empty); setFile(null); onDone()
    } catch (e) { setError(e) } finally { setBusy(false) }
  }
  const tpl = async () => download(await api.fbTemplate(f.kind), `fonte_b_${f.kind.toLowerCase()}.csv`)
  const errs = error?.detail?.errors
  return (
    <div className="card p-5 space-y-3">
      <SectionTitle icon={FileUp}>Carica una tabella ufficiale</SectionTitle>
      <p className="text-xs text-ink-2">Il file crea una <b>bozza</b>: non entra nei calcoli finché non la pubblichi attestando la fonte. Percentuali come «30%» o «0,30».</p>
      <div className="grid md:grid-cols-3 gap-3 text-xs">
        <label className="space-y-1"><span className="label">Tipo</span>
          <select className="field" value={f.kind} onChange={set('kind')}>{Object.entries(kinds).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}</select></label>
        <label className="space-y-1"><span className="label">Codice {f.kind === 'CCNL' ? '(sigla del contratto, es. TERZO_SETTORE)' : '(nome breve)'}</span><input className="field" value={f.code} onChange={set('code')} /></label>
        <label className="space-y-1"><span className="label">Nome</span><input className="field" value={f.name} onChange={set('name')} /></label>
        <label className="space-y-1"><span className="label">Versione</span><input className="field" value={f.version} onChange={set('version')} placeholder="es. 2026.1" /></label>
        <label className="space-y-1"><span className="label">Valida dal</span><input type="date" className="field" value={f.valid_from} onChange={set('valid_from')} /></label>
        <label className="space-y-1"><span className="label">Valida fino al (facoltativo)</span><input type="date" className="field" value={f.valid_to} onChange={set('valid_to')} /></label>
        <label className="space-y-1 md:col-span-3"><span className="label">Documento ufficiale da cui vengono i valori</span><input className="field" value={f.source_name} onChange={set('source_name')} placeholder="es. CCNL Terzo Settore, tabelle retributive 2026" /></label>
        <label className="space-y-1"><span className="label">Indirizzo del documento</span><input className="field" value={f.source_url} onChange={set('source_url')} placeholder="https://…" /></label>
        <label className="space-y-1"><span className="label">Riferimento (numero, data, articolo)</span><input className="field" value={f.source_ref} onChange={set('source_ref')} /></label>
        <label className="space-y-1"><span className="label">Note</span><input className="field" value={f.notes} onChange={set('notes')} /></label>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <input type="file" accept=".csv,.xlsx" onChange={(e) => setFile(e.target.files?.[0] || null)} className="text-xs" />
        <button type="button" onClick={tpl} className="btn"><Download className="w-3.5 h-3.5" />Intestazione del file</button>
        <button onClick={send} disabled={!ok || busy} className="btn-primary ml-auto">{busy && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Crea bozza</button>
      </div>
      {kinds[f.kind] && <p className="text-[11px] text-mute">Colonne: {kinds[f.kind].columns.join(' · ')}</p>}
      {error && (
        <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-700 text-xs space-y-1">
          <p className="font-semibold flex items-center gap-1"><AlertTriangle className="w-3.5 h-3.5" />{error.message}</p>
          {errs?.length > 0 && <ul className="list-disc pl-5">{errs.slice(0, 20).map((e) => <li key={e.line}>riga {e.line}: {e.error}</li>)}</ul>}
        </div>
      )}
    </div>
  )
}

function Detail({ id, onClose }) {
  const [d, setD] = useState(null)
  useEffect(() => { api.fbDataset(id).then(setD).catch(() => setD(null)) }, [id])
  if (!d) return null
  const cols = d.data[0] ? Object.keys(d.data[0]).filter((c) => c !== 'dataset_id') : []
  return (
    <div className="card p-5 space-y-3">
      <div className="flex items-center gap-2"><SectionTitle>{d.name} · v{d.version}</SectionTitle><button onClick={onClose} className="btn ml-auto">Chiudi</button></div>
      <p className="text-xs text-ink-2">Fonte: {d.source_name}{d.source_url ? ` · ${d.source_url}` : ''}{d.source_ref ? ` · ${d.source_ref}` : ''} · file {d.file_sha256?.slice(0, 12)}…</p>
      <div className="overflow-x-auto"><table className="w-full text-xs"><thead><tr>{cols.map((c) => <th key={c} className="text-left text-mute font-medium pr-4 pb-1">{c}</th>)}</tr></thead>
        <tbody>{d.data.map((r, i) => <tr key={i} className="border-t border-line">{cols.map((c) => <td key={c} className="py-1 pr-4 tabular-nums">{String(r[c] ?? '')}</td>)}</tr>)}</tbody></table></div>
    </div>
  )
}

export default function FonteB() {
  const [kinds, setKinds] = useState({})
  const [list, setList] = useState([])
  const [summary, setSummary] = useState(null)
  const [open, setOpen] = useState(null)
  const [attest, setAttest] = useState({})
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(null)
  const load = useCallback(async () => {
    try { const [k, l, s] = await Promise.all([api.fbKinds(), api.fbDatasets(), api.fonteBSummary()]); setKinds(k); setList(l); setSummary(s) } catch (e) { setError(e.message) }
  }, [])
  useEffect(() => { load() }, [load])
  const act = async (id, fn) => { setBusy(id); setError(null); try { await fn(); await load() } catch (e) { setError(e.message) } finally { setBusy(null) } }
  const empty = summary && summary.counts.ccnl + summary.counts.params + summary.counts.amortization + summary.counts.benchmarks === 0
  return (
    <div className="space-y-5">
      <div className="card p-5 space-y-2">
        <SectionTitle>Cosa usano i calcoli oggi</SectionTitle>
        {summary && (empty
          ? <p className="text-xs text-red-700 flex gap-2"><AlertTriangle className="w-4 h-4 shrink-0" />Nessuna tabella pubblicata: le voci di personale vengono respinte («tabella CCNL non disponibile») finché non ne carichi una. QUANTO non usa valori di ripiego.</p>
          : <p className="text-xs text-ink-2">{summary.counts.ccnl} contratti · {summary.counts.params} parametri · {summary.counts.amortization} categorie d’ammortamento · {summary.counts.benchmarks} benchmark (alla data {summary.on}).</p>)}
        {summary && Object.keys(summary.ccnl).length > 0 && <p className="text-xs text-ink-2">CCNL: {Object.entries(summary.ccnl).map(([c, l]) => `${c} (livelli ${l.join(', ')})`).join(' · ')}</p>}
      </div>
      {error && <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-700 text-xs">{error}</div>}
      <Upload kinds={kinds} onDone={load} />
      {open && <Detail id={open} onClose={() => setOpen(null)} />}
      <div className="card p-5 space-y-3">
        <SectionTitle>Insiemi di dati ({list.length})</SectionTitle>
        {list.length === 0 && <p className="text-xs text-mute">Nessun insieme caricato.</p>}
        {list.map((d) => (
          <div key={d.id} className="p-3 rounded-xl border border-line bg-field text-xs space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`px-1.5 py-0.5 rounded border font-medium ${STATUS_STYLE[d.status]}`}>{STATUS_LABEL[d.status]}</span>
              <button onClick={() => setOpen(d.id)} className="font-medium text-ink hover:underline">{kinds[d.kind]?.label || d.kind} · {d.code} · v{d.version}</button>
              <span className="text-mute">dal {d.valid_from}{d.valid_to ? ` al ${d.valid_to}` : ''} · {d.rows} righe</span>
              {d.official && <span className="text-emerald-700 inline-flex items-center gap-1"><CheckCircle2 className="w-3.5 h-3.5" />attestato ufficiale da {d.published_by}</span>}
              <span className="ml-auto flex items-center gap-2">
                {d.has_file && <button className="btn !py-1" onClick={async () => download(await api.fbFile(d.id), d.file_name)}><Download className="w-3 h-3" />File</button>}
                {d.status === 'DRAFT' && <button className="btn !py-1" disabled={busy === d.id} onClick={() => act(d.id, () => api.fbDelete(d.id))}><Trash2 className="w-3 h-3" />Elimina</button>}
              </span>
            </div>
            <p className="text-ink-2">Fonte: {d.source_name}{d.source_url ? ` · ${d.source_url}` : ''}{d.source_ref ? ` · ${d.source_ref}` : ''}</p>
            {d.status === 'DRAFT' && (
              <label className="flex items-start gap-2 text-ink-2"><input type="checkbox" className="mt-0.5 accent-brand" checked={!!attest[d.id]} onChange={(e) => setAttest({ ...attest, [d.id]: e.target.checked })} />
                <span>Attesto che questi valori corrispondono al documento ufficiale indicato.</span>
                <button className="btn-primary ml-auto" disabled={!attest[d.id] || busy === d.id} onClick={() => act(d.id, () => api.fbPublish(d.id, true))}>Pubblica</button></label>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
