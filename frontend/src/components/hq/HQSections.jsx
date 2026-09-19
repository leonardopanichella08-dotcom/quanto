import React, { useCallback, useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight, FileText, FolderOpen, Loader2, Play, ShieldCheck } from 'lucide-react'
import { api } from '../../lib/api'
import { BANDO_STATUS_STYLE, fmtBytes, fmtEur, fmtTs } from '../../lib/format'

const KIND_LABEL = {
  BANDO_TEXT: 'Bando (testo)', BANDO_PDF: 'Bando (PDF)', EXPORT_XLSX: 'Export Excel', EXPORT_PDF: 'Export PDF', IMPORT_XLSX: 'Import voci', ATTESTATION: 'Attestazione',
}

function useLoad(fn, deps) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const reload = useCallback(async () => {
    setBusy(true); setError(null)
    try { setData(await fn()) } catch (e) { setError(e.message) } finally { setBusy(false) }
  }, deps) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { reload() }, [reload])
  return { data, error, busy, reload }
}

function ProjectDossier({ id, onReplay, opsById }) {
  const { data, error, busy } = useLoad(() => api.hqProject(id), [id])
  const replay = async (runId) => onReplay((await api.hqRun(runId)).response)
  if (busy && !data) return <p className="text-xs text-neutral-500 flex gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Caricamento…</p>
  if (error) return <p className="text-xs text-red-300">{error}</p>
  if (!data) return null
  return (
    <div className="space-y-4">
      <div className="card p-4 space-y-2">
        <h4 className="font-bold text-sm font-mono">{data.project_id}</h4>
        {data.registration ? (
          <p className="text-xs text-emerald-300 flex items-center gap-1.5 flex-wrap"><ShieldCheck className="w-3.5 h-3.5" />Registrato il {fmtTs(data.registration.registered_at)} (voce n. {data.registration.seq}) · <span className="font-mono text-[10px] text-neutral-400">{data.registration.merkle_root.slice(0, 22)}…</span></p>
        ) : <p className="text-xs text-neutral-500">Non ancora registrato nel registro di asseverazione.</p>}
      </div>

      <div className="card p-4 space-y-2">
        <span className="label">Esecuzioni salvate ({data.runs.length})</span>
        {data.runs.map((r) => (
          <div key={r.id} className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs border-b border-neutral-900 py-1.5 last:border-0">
            <span className="font-mono text-[10px] text-neutral-500">{fmtTs(r.ts)}</span>
            <span className="font-mono">{r.items} voci</span><span className="text-emerald-300 font-mono">{fmtEur(r.total_approved_eur)}</span>
            <span className="text-neutral-400">score {r.conformity_score}/100</span><span className="text-neutral-500 text-[10px]">{r.bando_id}</span>
            <button onClick={() => replay(r.id)} className="ml-auto text-[#deffac] hover:underline flex items-center gap-1"><Play className="w-3 h-3" />rivedi nell’algoritmo</button>
          </div>
        ))}
        {data.runs.length === 0 && <p className="text-xs text-neutral-500 italic">Nessuna validazione.</p>}
      </div>

      <div className="card p-4 space-y-2">
        <span className="label">Documenti ({data.documents.length})</span>
        {data.documents.map((d) => <p key={d.id} className="text-[11px] font-mono text-neutral-300">{fmtTs(d.ts)} · {KIND_LABEL[d.kind] || d.kind} · {d.name} · {fmtBytes(d.size_bytes)} · {d.sha256.slice(0, 12)}…</p>)}
        {data.documents.length === 0 && <p className="text-xs text-neutral-500 italic">Nessun documento.</p>}
      </div>

      <div className="card p-4 space-y-2">
        <span className="label">Timeline del progetto</span>
        <div className="space-y-1.5">
          {data.timeline.map((e) => (
            <div key={e.id} className="flex gap-3 text-xs"><span className="font-mono text-[10px] text-neutral-500 w-32 shrink-0">{fmtTs(e.ts)}</span>
              <span className="text-[#deffac] shrink-0 w-44 truncate">{opsById[e.op]?.title || e.op}</span><span className="text-neutral-400">{e.summary}</span></div>
          ))}
        </div>
      </div>
    </div>
  )
}

function BandoDossier({ id }) {
  const { data, error, busy } = useLoad(() => api.hqBando(id), [id])
  if (busy && !data) return <p className="text-xs text-neutral-500 flex gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Caricamento…</p>
  if (error) return <p className="text-xs text-red-300">{error}</p>
  if (!data) return null
  const bySource = data.rules.reduce((a, r) => ({ ...a, [r.origin]: (a[r.origin] || 0) + 1 }), {})
  return (
    <div className="space-y-4">
      <div className="card p-4 space-y-2">
        <h4 className="font-bold text-sm">{data.name}</h4>
        <span className={`inline-block px-2 py-0.5 text-[10px] font-bold rounded border ${BANDO_STATUS_STYLE(data.status || '')}`}>{data.status || data.extraction_status}</span>
        <p className="text-[11px] text-neutral-400">{data.rules.length} regole ({Object.entries(bySource).map(([k, v]) => `${v} ${k.toLowerCase().replace('_', ' ')}`).join(', ')}) · {data.requirements.length} requisiti · {data.coverage_summary.REGOLA_DEL_BANDO}/60 criteri attivati · {data.not_specified.length} lacune dichiarate</p>
        {data.grant_rules && <p className="text-[10px] font-mono text-neutral-500">versione delle regole: {data.grant_rules.rule_version_hash}</p>}
      </div>
      <div className="card p-4 space-y-2">
        <span className="label">Progetti che hanno usato il bando ({data.projects.length})</span>
        {data.projects.map((p) => <p key={p.project_id} className="text-xs font-mono text-neutral-300">{p.project_id} · {p.n} validazioni · ultima {fmtTs(p.last_ts)}</p>)}
        {data.projects.length === 0 && <p className="text-xs text-neutral-500 italic">Nessuna validazione con questo bando.</p>}
      </div>
      <div className="card p-4 space-y-2">
        <span className="label">Fonti</span>
        {data.sources.map((s) => <p key={s.url} className="text-[11px] text-neutral-300">{s.confidence} · {s.title}</p>)}
        {data.usage.uploaded_sources.map((s) => <p key={s.sha256} className="text-[11px] font-mono text-neutral-300">testo caricato: {s.name} · {s.chars.toLocaleString('it-IT')} car. · {s.sha256.slice(0, 12)}…</p>)}
        {data.sources.length === 0 && data.usage.uploaded_sources.length === 0 && <p className="text-xs text-neutral-500 italic">Nessuna fonte registrata.</p>}
      </div>
      <div className="card p-4 space-y-2">
        <span className="label">Timeline del bando</span>
        {data.timeline.map((e) => <div key={e.id} className="flex gap-3 text-xs"><span className="font-mono text-[10px] text-neutral-500 w-32 shrink-0">{fmtTs(e.ts)}</span><span className="text-neutral-400">{e.summary}</span></div>)}
        {data.timeline.length === 0 && <p className="text-xs text-neutral-500 italic">Nessun evento.</p>}
      </div>
    </div>
  )
}

export function Dossiers({ bandi, onReplay, opsById }) {
  const [mode, setMode] = useState('projects')
  const [selected, setSelected] = useState(null)
  const projects = useLoad(() => api.hqProjects(), [])
  const list = mode === 'projects' ? (projects.data || []).map((p) => ({ id: p.project_id, title: p.project_id, sub: `${p.events} eventi · ${fmtTs(p.last_ts)}` }))
    : bandi.map((b) => ({ id: b.bando_id, title: b.name, sub: `${b.runs_count} validazioni · ${b.rules_count} regole` }))
  return (
    <div className="grid lg:grid-cols-3 gap-6 items-start">
      <div className="space-y-3">
        <div className="flex gap-1 bg-neutral-950 border border-neutral-800 p-1 rounded-xl w-fit">
          {[['projects', 'Progetti'], ['bandi', 'Bandi']].map(([id, l]) => <button key={id} onClick={() => { setMode(id); setSelected(null) }} className={`px-3 py-1.5 text-xs font-bold rounded-lg ${mode === id ? 'bg-[#deffac] text-black' : 'text-neutral-400'}`}>{l}</button>)}
        </div>
        {list.map((it) => (
          <button key={it.id} onClick={() => setSelected(it.id)} className={`w-full text-left card p-3 hover:border-neutral-600 ${selected === it.id ? '!border-[#deffac]' : ''}`}>
            <p className="text-xs font-bold truncate flex items-center gap-1.5"><FolderOpen className="w-3.5 h-3.5 text-neutral-500 shrink-0" />{it.title}</p><p className="text-[10px] text-neutral-500 mt-0.5">{it.sub}</p>
          </button>
        ))}
        {list.length === 0 && <p className="text-xs text-neutral-500 italic">Ancora niente da mostrare.</p>}
      </div>
      <div className="lg:col-span-2">
        {!selected ? <div className="card p-10 text-center text-sm text-neutral-500 italic">Scegli un {mode === 'projects' ? 'progetto' : 'bando'} per aprirne il fascicolo.</div>
          : mode === 'projects' ? <ProjectDossier id={selected} onReplay={onReplay} opsById={opsById} /> : <BandoDossier id={selected} />}
      </div>
    </div>
  )
}

export function Documents() {
  const [kind, setKind] = useState('')
  const { data, error, busy } = useLoad(() => api.hqDocuments(kind), [kind])
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <select value={kind} onChange={(e) => setKind(e.target.value)} className="bg-neutral-950 border border-neutral-800 rounded-lg px-2 py-1.5 text-xs">
          <option value="">Tutti i documenti</option>{Object.entries(KIND_LABEL).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
        </select>
        {busy && <Loader2 className="w-3.5 h-3.5 animate-spin text-neutral-500" />}
        <span className="text-[11px] text-neutral-500">Nome, hash SHA-256 e dimensione. Il testo integrale si conserva solo per i bandi caricati.</span>
      </div>
      {error && <p className="text-xs text-red-300">{error}</p>}
      <div className="card overflow-x-auto">
        <table className="w-full text-xs">
          <thead><tr className="text-left text-[10px] uppercase tracking-wider text-neutral-500 border-b border-neutral-800">{['Quando', 'Tipo', 'Nome', 'Progetto', 'Bando', 'Dim.', 'SHA-256'].map((h) => <th key={h} className="p-2.5 font-semibold">{h}</th>)}</tr></thead>
          <tbody>
            {(data || []).map((d) => (
              <tr key={d.id} className="border-b border-neutral-900 last:border-0">
                <td className="p-2.5 font-mono text-[10px] text-neutral-400 whitespace-nowrap">{fmtTs(d.ts)}</td>
                <td className="p-2.5"><span className="inline-flex items-center gap-1"><FileText className="w-3 h-3 text-neutral-500" />{KIND_LABEL[d.kind] || d.kind}</span></td>
                <td className="p-2.5 font-mono">{d.name}</td><td className="p-2.5 font-mono text-neutral-400">{d.project_id || '—'}</td><td className="p-2.5 font-mono text-neutral-400">{d.bando_id || '—'}</td>
                <td className="p-2.5 font-mono text-neutral-400">{fmtBytes(d.size_bytes)}</td><td className="p-2.5 font-mono text-[10px] text-neutral-500" title={d.sha256}>{d.sha256.slice(0, 16)}…</td>
              </tr>
            ))}
            {data && data.length === 0 && <tr><td colSpan={7} className="p-6 text-center text-neutral-500 italic">Nessun documento ancora.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export function DbExplorer() {
  const tables = useLoad(() => api.hqTables(), [])
  const [table, setTable] = useState('events')
  const [offset, setOffset] = useState(0)
  const PAGE = 25
  const rows = useLoad(() => api.hqRows(table, PAGE, offset), [table, offset])
  const cols = rows.data?.rows?.[0] ? Object.keys(rows.data.rows[0]) : (tables.data?.find((t) => t.name === table)?.columns || [])
  return (
    <div className="grid lg:grid-cols-4 gap-6 items-start">
      <div className="space-y-2">
        <p className="text-[11px] text-neutral-400">Database in sola lettura. I payload pesanti (richieste e risposte salvate, testi dei bandi) sono riassunti.</p>
        {(tables.data || []).map((t) => (
          <button key={t.name} onClick={() => { setTable(t.name); setOffset(0) }} className={`w-full text-left card p-2.5 flex items-center justify-between hover:border-neutral-600 ${table === t.name ? '!border-[#deffac]' : ''}`}>
            <span className="font-mono text-xs">{t.name}</span><span className="font-mono text-[11px] text-[#deffac]">{t.rows}</span>
          </button>
        ))}
      </div>
      <div className="lg:col-span-3 space-y-3 min-w-0">
        <div className="flex items-center gap-3">
          <span className="font-mono text-sm font-bold">{table}</span>
          <span className="text-[11px] text-neutral-500">{rows.data ? `${rows.data.total} righe · ${offset + 1}–${Math.min(offset + PAGE, rows.data.total)}` : ''}</span>
          <div className="ml-auto flex gap-1">
            <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))} className="p-1.5 rounded-lg border border-neutral-700 disabled:opacity-30"><ChevronLeft className="w-3.5 h-3.5" /></button>
            <button disabled={!rows.data || offset + PAGE >= rows.data.total} onClick={() => setOffset(offset + PAGE)} className="p-1.5 rounded-lg border border-neutral-700 disabled:opacity-30"><ChevronRight className="w-3.5 h-3.5" /></button>
          </div>
        </div>
        {rows.error && <p className="text-xs text-red-300">{rows.error}</p>}
        <div className="card overflow-x-auto">
          <table className="w-full text-[11px]">
            <thead><tr className="text-left text-[10px] uppercase tracking-wider text-neutral-500 border-b border-neutral-800">{cols.map((c) => <th key={c} className="p-2 font-semibold whitespace-nowrap">{c}</th>)}</tr></thead>
            <tbody>
              {(rows.data?.rows || []).map((r, i) => (
                <tr key={i} className="border-b border-neutral-900 last:border-0 align-top">
                  {cols.map((c) => <td key={c} className="p-2 font-mono text-neutral-300 max-w-[260px] truncate" title={r[c] == null ? '' : String(r[c])}>{r[c] == null ? <span className="text-neutral-600">null</span> : String(r[c])}</td>)}
                </tr>
              ))}
              {rows.data && rows.data.rows.length === 0 && <tr><td colSpan={Math.max(cols.length, 1)} className="p-6 text-center text-neutral-500 italic">Tabella vuota.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
