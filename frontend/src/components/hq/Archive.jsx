import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronRight, Download, ExternalLink, FileText, Loader2, Plus, RefreshCw, Trash2 } from 'lucide-react'
import { api, download } from '../../lib/api'
import { fmtBytes, fmtTs } from '../../lib/format'
import { Hint } from '../Help'

const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
const KINDS = ['OBBLIGO', 'DIVIETO', 'LIMITE', 'INFO', 'DA_REVISIONARE']
const KIND_LABEL = { OBBLIGO: 'obbligo', DIVIETO: 'divieto', LIMITE: 'limite', INFO: 'informazione', DA_REVISIONARE: 'da rivedere' }
const TIER_STYLE = { UFFICIALE: 'text-emerald-700 border-emerald-500/30', SECONDARIA: 'text-amber-700 border-amber-500/30' }
const ORIGIN_LABEL = { predefinito: 'predefinito', web: 'letto dal web', caricato: 'caricato a mano' }

function useAction() {
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)
  const run = async (key, fn) => {
    setBusy(key); setError(null)
    try { return await fn() } catch (e) { setError(e.message); return undefined } finally { setBusy(null) }
  }
  return { busy, error, run, setError }
}

/** Testo estratto di un documento, con ricerca a passaggi. */
function TextViewer({ id, source, onClose }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [q, setQ] = useState('')
  const [shown, setShown] = useState(8000)
  useEffect(() => { api.hqSourceText(id, source.sha256).then(setData).catch((e) => setError(e.message)) }, [id, source.sha256])
  const excerpts = useMemo(() => {
    if (!data || q.trim().length < 2) return null
    const rx = new RegExp(esc(q.trim()), 'gi'); const out = []; let m
    while ((m = rx.exec(data.text)) && out.length < 60) {
      out.push({ at: m.index, text: data.text.slice(Math.max(0, m.index - 200), m.index + q.length + 320).replace(/\s+/g, ' ') })
      rx.lastIndex = m.index + 250
    }
    return out
  }, [data, q])
  const hl = (t) => t.split(new RegExp(`(${esc(q.trim())})`, 'gi')).map((part, i) => (i % 2 ? <mark key={i} className="bg-brand/30 text-ink rounded px-0.5">{part}</mark> : part))
  return (
    <div className="p-3 bg-field border border-line rounded-xl space-y-2">
      <div className="flex items-center gap-2"><span className="text-xs font-medium truncate">{source.name}</span><button onClick={onClose} className="ml-auto text-xs text-ink-2 hover:text-ink">Chiudi</button></div>
      {error && <p className="text-xs text-red-700">{error}</p>}
      {!data && !error && <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3 h-3 animate-spin" />Carico…</p>}
      {data && (<>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={`Cerca nel testo (${data.chars.toLocaleString('it-IT')} caratteri)`} aria-label="Cerca nel testo" className="field" />
        {excerpts ? (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            <p className="text-[11px] text-mute">{excerpts.length} passaggi con “{q.trim()}”</p>
            {excerpts.map((e) => <p key={e.at} className="text-xs text-ink-2 leading-relaxed border-l-2 border-line-strong pl-3">…{hl(e.text)}…</p>)}
          </div>
        ) : (<>
          <pre className="whitespace-pre-wrap text-xs text-ink-2 leading-relaxed max-h-96 overflow-y-auto font-sans">{data.text.slice(0, shown)}</pre>
          {shown < data.text.length && <button onClick={() => setShown(shown + 30000)} className="btn">Mostra altro</button>}
        </>)}
      </>)}
    </div>
  )
}

function Documents({ id, sources, onChanged }) {
  const [open, setOpen] = useState(null)
  const { busy, error, run } = useAction()
  const openFile = (s) => run(`f${s.sha256}`, async () => { const b = await api.hqSourceFile(id, s.sha256, false); window.open(URL.createObjectURL(b), '_blank', 'noopener') })
  const saveFile = (s) => run(`d${s.sha256}`, async () => { const b = await api.hqSourceFile(id, s.sha256, true); download(b, s.file?.name || s.name) })
  const remove = (s) => { if (window.confirm(`Eliminare «${s.name}» dalla memoria del bando? Testo e file originale vengono cancellati.`)) run(`x${s.sha256}`, async () => { await api.hqDeleteSource(id, s.sha256); await onChanged() }) }
  if (!sources.length) return <p className="text-xs text-mute">Nessun documento in memoria per questo bando.</p>
  return (
    <div className="space-y-2">
      {error && <p className="text-xs text-red-700">{error}</p>}
      <p className="text-xs text-mute">{sources.length} documenti · {fmtBytes(sources.reduce((a, s) => a + (s.file?.size_bytes || 0), 0))} di file originali conservati</p>
      {sources.map((s) => {
        const issues = [...(s.warnings || []), ...(s.analysis?.note ? [s.analysis.note] : [])]
        return (
          <div key={s.sha256} className="p-3 bg-field border border-line rounded-xl space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              {s.tier ? <span className={`px-1.5 py-0.5 rounded border text-[11px] ${TIER_STYLE[s.tier]}`}>{s.tier === 'UFFICIALE' ? 'ufficiale' : 'secondaria'}</span> : <span className="px-1.5 py-0.5 rounded border border-line-strong text-[11px] text-ink-2">caricato a mano</span>}
              {s.url ? <a href={s.url} target="_blank" rel="noreferrer" className="text-sky-700 hover:underline inline-flex items-center gap-1 text-xs truncate max-w-full">{s.name}<ExternalLink className="w-3 h-3 shrink-0" /></a> : <span className="text-xs">{s.name}</span>}
            </div>
            <p className="text-[11px] text-mute">{s.content_type || '—'}{s.pages ? ` · ${s.pages} pag.` : ''} · {s.chars.toLocaleString('it-IT')} caratteri{s.analysis?.lang ? ` · lingua ${s.analysis.lang}` : ''} · {s.analysis ? `${s.analysis.requirements} requisiti` : 'non ancora letto'} · {fmtTs(s.ts)}</p>
            {issues.map((w) => <p key={w} className="text-[11px] text-amber-700 flex items-start gap-1"><AlertTriangle className="w-3 h-3 shrink-0 mt-0.5" />{w}</p>)}
            <div className="flex flex-wrap gap-2">
              <button onClick={() => setOpen(open === s.sha256 ? null : s.sha256)} className="btn !py-1"><FileText className="w-3 h-3" />{open === s.sha256 ? 'Chiudi testo' : 'Leggi il testo'}</button>
              <button onClick={() => openFile(s)} disabled={!s.file || busy === `f${s.sha256}`} className="btn !py-1" title={s.file ? 'Apre il file così come è stato scaricato' : 'Il file originale non è conservato'}>{busy === `f${s.sha256}` && <Loader2 className="w-3 h-3 animate-spin" />}Apri originale</button>
              <button onClick={() => saveFile(s)} disabled={!s.file || busy === `d${s.sha256}`} className="btn !py-1"><Download className="w-3 h-3" />Scarica</button>
              <button onClick={() => remove(s)} className="btn !py-1 !text-red-700 !border-red-500/30 ml-auto"><Trash2 className="w-3 h-3" />Elimina</button>
            </div>
            {open === s.sha256 && <TextViewer id={id} source={s} onClose={() => setOpen(null)} />}
          </div>
        )
      })}
    </div>
  )
}

function Rules({ id, detail, sheet, onChanged }) {
  const { busy, error, run } = useAction()
  const [vals, setVals] = useState({})
  const [newKey, setNewKey] = useState('')
  const [newVal, setNewVal] = useState('')
  const labels = useMemo(() => Object.fromEntries([...sheet.says, ...sheet.conflicts, ...sheet.silent].map((x) => [x.key, x.label])), [sheet])
  const save = (key, v) => run(`s${key}`, async () => { await api.hqSetRule(id, key, v); setVals((x) => ({ ...x, [key]: undefined })); await onChanged() })
  const remove = (key) => { if (window.confirm(`Eliminare la regola ${key}?`)) run(`x${key}`, async () => { await api.hqDeleteRule(id, key); await onChanged() }) }
  const fmt = (v) => (v == null ? '' : typeof v === 'object' ? JSON.stringify(v) : String(v))
  return (
    <div className="space-y-3">
      {error && <p className="text-xs text-red-700">{error}</p>}
      <p className="text-xs text-mute">Qui imposti tu il valore: vale come decisione del manager e diventa un controllo attivo. Formati: numero (35), percentuale come 0.15 oppure 15%, true/false, elenco JSON come ["CAPITAL_ASSETS"].</p>
      {detail.rules.map((r) => (
        <div key={r.key} className="p-3 bg-field border border-line rounded-xl space-y-1.5">
          <div className="flex flex-wrap items-center gap-2 text-xs"><span className="font-mono text-ink">{r.key}</span><span className="text-mute">{labels[r.key]}</span>
            <span className={`px-1.5 rounded border text-[10px] ${r.status === 'PUBLISHED' ? 'border-emerald-500/30 text-emerald-700' : 'border-amber-500/30 text-amber-700'}`}>{r.status === 'PUBLISHED' ? 'attiva' : 'da decidere'}</span>
            <span className="text-mute">{r.origin}</span></div>
          {r.status !== 'PUBLISHED' && r.passes && <p className="text-[11px] text-amber-700">Letture diverse: {r.passes.join(' ≠ ')} — scegli quella giusta:{' '}
            {r.passes.map((p) => <button key={p} onClick={() => save(r.key, p)} className="btn !py-0.5 !px-2 mr-1">{p}</button>)}</p>}
          {r.source_ref && <p className="text-[11px] text-mute break-words">Fonte: {r.source_ref}</p>}
          <div className="flex flex-wrap gap-2">
            <input value={vals[r.key] ?? fmt(r.value)} onChange={(e) => setVals({ ...vals, [r.key]: e.target.value })} aria-label={`Valore di ${r.key}`} className="field !w-56 font-mono" />
            <button onClick={() => save(r.key, vals[r.key] ?? fmt(r.value))} disabled={busy === `s${r.key}`} className="btn">Salva</button>
            <button onClick={() => remove(r.key)} className="btn !text-red-700 !border-red-500/30"><Trash2 className="w-3 h-3" />Elimina</button>
          </div>
        </div>
      ))}
      {detail.rules.length === 0 && <p className="text-xs text-mute">Nessuna regola.</p>}
      <div className="p-3 border border-line rounded-xl space-y-2">
        <p className="text-xs font-medium">Aggiungi una regola</p>
        <div className="flex flex-wrap gap-2">
          <select value={newKey} onChange={(e) => setNewKey(e.target.value)} className="field !w-auto max-w-full" aria-label="Regola da aggiungere">
            <option value="">Scegli la regola…</option>
            {sheet.silent.map((x) => <option key={x.key} value={x.key}>{x.label}</option>)}
          </select>
          <input value={newVal} onChange={(e) => setNewVal(e.target.value)} placeholder="valore" aria-label="Valore" className="field !w-40 font-mono" />
          <button onClick={() => save(newKey, newVal).then(() => { setNewKey(''); setNewVal('') })} disabled={!newKey || !newVal} className="btn-primary flex items-center gap-1.5"><Plus className="w-3.5 h-3.5" />Aggiungi</button>
        </div>
      </div>
    </div>
  )
}

function Requirements({ id, items, onChanged }) {
  const { busy, error, run } = useAction()
  const [q, setQ] = useState('')
  const [kind, setKind] = useState('')
  const [limit, setLimit] = useState(30)
  const [form, setForm] = useState({ topic: '', kind: 'OBBLIGO', text: '' })
  const rows = items.filter((r) => (!kind || r.kind === kind) && (!q.trim() || `${r.text} ${r.topic}`.toLowerCase().includes(q.trim().toLowerCase())))
  const reclass = (r, k) => run(`p${r.seq}`, async () => { await api.hqPatchRequirement(id, r.seq, { kind: k }); await onChanged() })
  const remove = (r) => run(`x${r.seq}`, async () => { await api.hqDeleteRequirement(id, r.seq); await onChanged() })
  const add = () => run('add', async () => { await api.hqAddRequirement(id, { ...form, criteria: [] }); setForm({ topic: '', kind: 'OBBLIGO', text: '' }); await onChanged() })
  return (
    <div className="space-y-3">
      {error && <p className="text-xs text-red-700">{error}</p>}
      <div className="flex flex-wrap gap-2">
        <input value={q} onChange={(e) => { setQ(e.target.value); setLimit(30) }} placeholder="Cerca nei requisiti" aria-label="Cerca nei requisiti" className="field !w-64" />
        <select value={kind} onChange={(e) => setKind(e.target.value)} className="field !w-auto" aria-label="Tipo"><option value="">Tutti i tipi</option>{KINDS.map((k) => <option key={k} value={k}>{KIND_LABEL[k]}</option>)}</select>
        <span className="text-xs text-mute self-center">{rows.length} di {items.length}</span>
      </div>
      {rows.slice(0, limit).map((r) => (
        <div key={r.seq} className="p-3 bg-field border border-line rounded-xl space-y-1.5 text-xs">
          <div className="flex flex-wrap items-center gap-2"><span className="font-medium">{r.topic}</span>{r.criteria.map((c) => <span key={c} className="font-mono text-[11px] text-brand-ink">#{c}</span>)}
            <select value={r.kind} onChange={(e) => reclass(r, e.target.value)} disabled={busy === `p${r.seq}`} className="field !w-auto !py-0.5 ml-auto" aria-label="Riclassifica">{KINDS.map((k) => <option key={k} value={k}>{KIND_LABEL[k]}</option>)}</select>
            <button onClick={() => remove(r)} aria-label="Elimina requisito" className="text-mute hover:text-red-700"><Trash2 className="w-3.5 h-3.5" /></button></div>
          <p className="text-ink-2 leading-relaxed">{r.text}</p>
          {r.source_ref && <p className="text-[11px] text-mute break-words">Fonte: {r.source_ref}</p>}
        </div>
      ))}
      {rows.length > limit && <button onClick={() => setLimit(limit + 30)} className="btn">Mostra altri</button>}
      <div className="p-3 border border-line rounded-xl space-y-2">
        <p className="text-xs font-medium">Aggiungi un requisito</p>
        <div className="flex flex-wrap gap-2">
          <input value={form.topic} onChange={(e) => setForm({ ...form, topic: e.target.value })} placeholder="Tema" aria-label="Tema" className="field !w-48" />
          <select value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })} className="field !w-auto" aria-label="Tipo del nuovo requisito">{KINDS.map((k) => <option key={k} value={k}>{KIND_LABEL[k]}</option>)}</select>
        </div>
        <textarea value={form.text} onChange={(e) => setForm({ ...form, text: e.target.value })} rows={2} placeholder="Testo del requisito" aria-label="Testo" className="field" />
        <button onClick={add} disabled={form.topic.trim().length < 2 || form.text.trim().length < 5} className="btn-primary">Aggiungi</button>
      </div>
    </div>
  )
}

function Fold({ title, count, tone = '', defaultOpen = false, children }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="border border-line rounded-xl">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center gap-2 px-3 py-2.5 text-left text-sm font-medium">{open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}<span className={tone}>{title}</span><span className="ml-auto text-xs text-mute font-mono">{count}</span></button>
      {open && <div className="px-3 pb-3 space-y-2">{children}</div>}
    </div>
  )
}

/** Scheda di controllo: cosa dicono i documenti, cosa non dicono, cosa cercare e come verificare. */
function Sheet({ id, sheet, onChanged }) {
  const { busy, error, run } = useAction()
  const [vals, setVals] = useState({})
  const set = (key, v) => run(`s${key}`, async () => { await api.hqSetRule(id, key, v); await onChanged() })
  const reclass = (r, k) => run(`p${r.seq}`, async () => { await api.hqPatchRequirement(id, r.seq, { kind: k }); await onChanged() })
  const s = sheet.summary
  return (
    <div className="space-y-3">
      {error && <p className="text-xs text-red-700">{error}</p>}
      <div className="p-3 bg-field border border-line rounded-xl space-y-2">
        <p className="text-sm font-medium">Da dove partire</p>
        <ol className="space-y-1.5 text-xs text-ink-2 list-decimal pl-5">{sheet.checklist.map((c) => <li key={c} className="leading-relaxed">{c}</li>)}</ol>
        <p className="text-[11px] text-mute">{s.rules_published} regole attive · {s.conflicts} da decidere · {s.silent} non trovate · {s.review} requisiti da rivedere · {s.document_issues} documenti con problemi</p>
      </div>

      <Fold title="Da decidere: documenti in disaccordo" count={sheet.conflicts.length} tone="text-amber-700" defaultOpen={sheet.conflicts.length > 0}>
        {sheet.conflicts.length === 0 && <p className="text-xs text-mute">Nessuna regola in disaccordo.</p>}
        {sheet.conflicts.map((c) => (
          <div key={c.key} className="p-3 bg-field border border-line rounded-xl space-y-1.5 text-xs">
            <p className="font-medium">{c.label} <span className="font-mono text-mute">{c.key}</span></p>
            <p className="text-ink-2 leading-relaxed">{c.what_to_do}</p>
            <p className="text-mute break-words">Fonti: {c.source}</p>
            <div className="flex flex-wrap gap-1.5 items-center">Imposta: {(c.values || []).map((v) => <button key={v} onClick={() => set(c.key, v)} disabled={busy === `s${c.key}`} className="btn !py-0.5 !px-2 font-mono">{v}</button>)}</div>
          </div>
        ))}
      </Fold>

      <Fold title="Cosa dice il bando (regole attive con la fonte)" count={sheet.says.length}>
        {sheet.says.map((x) => (
          <div key={x.key} className="p-3 bg-field border border-line rounded-xl text-xs space-y-1">
            <p className="font-medium">{x.label}: <span className="font-mono text-brand-ink">{JSON.stringify(x.value)}</span> <span className="text-mute">· controlli {x.criteria.map((n) => `#${n}`).join(' ')}</span></p>
            <p className="text-mute break-words">Fonte: {x.source || '—'} · affidabilità {x.confidence}</p>
            <p className="text-ink-2">{x.check}</p>
          </div>
        ))}
        {sheet.says.length === 0 && <p className="text-xs text-mute">Nessuna regola attiva.</p>}
      </Fold>

      <Fold title="Cosa NON dice: regole non trovate, cosa cercare e come verificare" count={sheet.silent.length} defaultOpen>
        <p className="text-xs text-mute leading-relaxed">Ogni riga è una regola che il motore sa usare ma che non ho trovato nei documenti. Finché non c’è, i controlli collegati restano spenti (mai “superati”). Per ognuna trovi cosa fa, quali parole cercare, dove compare di solito e come verificare.</p>
        {sheet.silent.map((x) => (
          <details key={x.key} className="border border-line rounded-xl group">
            <summary className="cursor-pointer list-none px-3 py-2 flex flex-wrap items-center gap-2 text-xs">
              <span className="font-medium">{x.label}</span>
              <span className={`px-1.5 rounded border text-[10px] ${x.mentions ? 'border-amber-500/30 text-amber-700' : 'border-line-strong text-mute'}`}>{x.mentions ? `${x.mentions} citazioni nei documenti` : 'mai citata'}</span>
              <span className="ml-auto font-mono text-[10px] text-mute">{x.criteria.map((c) => `#${c.n}`).join(' ')}</span>
            </summary>
            <div className="px-3 pb-3 space-y-2 text-xs text-ink-2">
              <p><span className="text-mute">Cosa significa · </span>{x.meaning}</p>
              {x.criteria.length > 0 && <p><span className="text-mute">Controlli spenti · </span>{x.criteria.map((c) => `#${c.n} ${c.title}`).join(' · ')}</p>}
              <p><span className="text-mute">Stato · </span>{x.state}</p>
              <p className="break-words leading-7"><span className="text-mute">Cerca · </span>{x.search.map((w) => <code key={w} className="mr-1.5 px-1 rounded bg-tint-2 whitespace-normal break-all">{w}</code>)}</p>
              <p><span className="text-mute">Dove · </span>{x.where}</p>
              <p><span className="text-mute">Come verificare · </span>{x.verify}</p>
              {x.snippets.map((sn) => <p key={sn} className="border-l-2 border-line-strong pl-3 text-ink-2">{sn}</p>)}
              <div className="flex flex-wrap gap-2 pt-1">
                <input value={vals[x.key] || ''} onChange={(e) => setVals({ ...vals, [x.key]: e.target.value })} placeholder="valore da impostare" aria-label={`Valore per ${x.label}`} className="field !w-48 font-mono" />
                <button onClick={() => set(x.key, vals[x.key])} disabled={!vals[x.key] || busy === `s${x.key}`} className="btn">Imposta</button>
              </div>
            </div>
          </details>
        ))}
      </Fold>

      <Fold title="Requisiti da rivedere (obblighi e divieti non classificati)" count={sheet.review.length}>
        {sheet.review.map((r) => (
          <div key={r.seq} className="p-3 bg-field border border-line rounded-xl text-xs space-y-1.5">
            <p className="text-ink-2 leading-relaxed">{r.text}</p>
            <p className="text-[11px] text-mute break-words">Fonte: {r.source_ref}</p>
            <div className="flex flex-wrap gap-1.5 items-center">Classifica come: {['OBBLIGO', 'DIVIETO', 'LIMITE', 'INFO'].map((k) => <button key={k} onClick={() => reclass(r, k)} disabled={busy === `p${r.seq}`} className="btn !py-0.5 !px-2">{KIND_LABEL[k]}</button>)}</div>
          </div>
        ))}
        {sheet.review.length === 0 && <p className="text-xs text-mute">Nessun requisito da rivedere.</p>}
      </Fold>

      <Fold title="Documenti letti" count={sheet.documents.length}>
        {sheet.documents.map((d) => (
          <p key={d.sha256} className="text-xs flex flex-wrap items-center gap-2">
            {d.issues.length ? <AlertTriangle className="w-3.5 h-3.5 text-amber-700 shrink-0" /> : <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700 shrink-0" />}
            <span className="text-ink">{d.name}</span><span className="text-mute">{d.requirements ?? '—'} requisiti{d.lang ? ` · ${d.lang}` : ''}</span>
            {d.issues.map((w) => <span key={w} className="text-amber-700 w-full pl-5">{w}</span>)}
          </p>
        ))}
      </Fold>
    </div>
  )
}

function BandoManager({ id, deletedDefaults, onList }) {
  const [detail, setDetail] = useState(null)
  const [sheet, setSheet] = useState(null)
  const [tab, setTab] = useState('sheet')
  const [error, setError] = useState(null)
  const [name, setName] = useState('')
  const { busy, error: actErr, run } = useAction()

  const load = useCallback(async () => {
    try {
      const [d, s] = await Promise.all([api.hqArchiveDetail(id), api.hqConsultant(id)])
      setDetail(d); setSheet(s); setName(d.name); setError(null)
    } catch (e) { setError(e.message) }
  }, [id])
  useEffect(() => { setDetail(null); setSheet(null); load() }, [load])
  const changed = async () => { await load(); await onList() }

  const reanalyze = () => run('re', async () => { await api.hqReanalyze(id); await changed() })
  const rename = () => run('rn', async () => { await api.hqRenameBando(id, name); await changed() })
  const exportZip = () => run('zip', async () => { download(await api.hqExportBando(id), `${id}.zip`) })
  const remove = () => { if (window.confirm(`Eliminare DEFINITIVAMENTE «${detail.name}» con tutti i suoi documenti, file originali, regole e requisiti?\nLa cronologia degli eventi resta.`)) run('del', async () => { await api.hqDeleteBando(id); await onList(true) }) }
  const restore = () => run('rest', async () => { await api.hqRestoreDefaults(); await onList() })

  if (error) return <p className="text-xs text-red-700">{error}</p>
  if (!detail || !sheet) return <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Carico…</p>
  const tabs = [['sheet', 'Scheda consulente'], ['docs', `Documenti (${detail.sources_detail.length})`], ['rules', `Regole (${detail.rules.length})`], ['reqs', `Requisiti (${detail.requirements.length})`], ['actions', 'Azioni']]
  return (
    <div className="card p-5 space-y-4">
      <div><h3 className="font-semibold text-lg break-words">{detail.name}</h3><p className="text-xs font-mono text-mute">{detail.bando_id} · {detail.extraction_status}</p></div>
      <div className="flex items-center gap-3"><div className="flex flex-wrap gap-x-5 gap-y-1 border-b border-line flex-1">
        {tabs.map(([k, l]) => <button key={k} onClick={() => setTab(k)} className={`pb-2 text-xs -mb-px border-b-2 ${tab === k ? 'border-brand text-ink font-medium' : 'border-transparent text-ink-2 hover:text-ink'}`}>{l}</button>)}</div>
        <Hint id="hq_scheda" /></div>
      {tab === 'sheet' && <Sheet id={id} sheet={sheet} onChanged={changed} />}
      {tab === 'docs' && <Documents id={id} sources={detail.sources_detail} onChanged={changed} />}
      {tab === 'rules' && <Rules id={id} detail={detail} sheet={sheet} onChanged={changed} />}
      {tab === 'reqs' && <Requirements id={id} items={detail.requirements} onChanged={changed} />}
      {tab === 'actions' && (
        <div className="space-y-4">
          {actErr && <p className="text-xs text-red-700">{actErr}</p>}
          <div className="flex flex-wrap gap-2"><button onClick={reanalyze} disabled={busy === 're' || !detail.sources_detail.length} className="btn-primary flex items-center gap-1.5">{busy === 're' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}Rileggi tutto</button>
            <button onClick={exportZip} disabled={busy === 'zip'} className="btn"><Download className="w-3.5 h-3.5" />Esporta tutto (ZIP)</button></div>
          <p className="text-xs text-mute">“Rileggi tutto” ricalcola regole automatiche e requisiti da tutti i documenti in memoria (le decisioni che hai preso a mano restano). L’esportazione contiene la scheda JSON, i testi estratti e i file originali.</p>
          <div className="flex flex-wrap gap-2"><input value={name} onChange={(e) => setName(e.target.value)} aria-label="Nome del bando" className="field !w-72" /><button onClick={rename} disabled={busy === 'rn' || name.trim().length < 3 || name === detail.name} className="btn">Rinomina</button></div>
          <div className="pt-3 border-t border-line space-y-2">
            <button onClick={remove} disabled={busy === 'del'} className="btn !text-red-700 !border-red-500/30"><Trash2 className="w-3.5 h-3.5" />Elimina il bando</button>
            <p className="text-xs text-mute">Cancella documenti, file originali, regole e requisiti. La cronologia degli eventi resta. I bandi predefiniti si possono ripristinare.</p>
            {deletedDefaults.length > 0 && <button onClick={restore} className="btn">Ripristina i {deletedDefaults.length} bandi predefiniti eliminati</button>}
          </div>
        </div>
      )}
    </div>
  )
}

export default function Archive() {
  const [data, setData] = useState({ bandi: [], deleted_defaults: [] })
  const [selected, setSelected] = useState(null)
  const [error, setError] = useState(null)
  const [q, setQ] = useState('')
  const load = useCallback(async (clear) => {
    try { setData(await api.hqArchive()); setError(null); if (clear) setSelected(null) } catch (e) { setError(e.message) }
  }, [])
  useEffect(() => { load() }, [load])
  const list = data.bandi.filter((b) => !q.trim() || `${b.name} ${b.bando_id}`.toLowerCase().includes(q.trim().toLowerCase()))
  return (
    <div className="grid lg:grid-cols-3 gap-6 items-start">
      <div className="space-y-3">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cerca un bando" aria-label="Cerca un bando" className="field" />
        {error && <p className="text-xs text-red-700">{error}</p>}
        {list.map((b) => (
          <button key={b.bando_id} onClick={() => setSelected(b.bando_id)} className={`w-full text-left card p-3 space-y-1 hover:border-line-strong ${selected === b.bando_id ? '!border-brand' : ''}`}>
            <p className="text-sm font-medium leading-snug">{b.name}</p>
            <p className="text-[11px] text-mute">{ORIGIN_LABEL[b.origin]} · {b.sources} documenti{b.files_bytes ? ` (${fmtBytes(b.files_bytes)})` : ''} · {b.rules} regole · {b.requirements} requisiti</p>
            {(b.rules_pending > 0 || b.requirements_to_review > 0) && <p className="text-[11px] text-amber-700 flex items-center gap-1"><AlertTriangle className="w-3 h-3" />{b.rules_pending ? `${b.rules_pending} da decidere` : ''}{b.rules_pending && b.requirements_to_review ? ' · ' : ''}{b.requirements_to_review ? `${b.requirements_to_review} da rivedere` : ''}</p>}
          </button>
        ))}
        {list.length === 0 && <p className="text-xs text-mute">Nessun bando.</p>}
        {data.deleted_defaults.length > 0 && !selected && <button onClick={async () => { await api.hqRestoreDefaults(); load() }} className="btn">Ripristina i {data.deleted_defaults.length} bandi predefiniti eliminati</button>}
      </div>
      <div className="lg:col-span-2 min-w-0">
        {selected ? <BandoManager id={selected} deletedDefaults={data.deleted_defaults} onList={load} />
          : <div className="card p-10 text-center text-sm text-mute">Scegli un bando per vedere tutto ciò che è in memoria, correggerlo o eliminarlo.</div>}
      </div>
    </div>
  )
}
