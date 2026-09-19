import React, { useCallback, useEffect, useState } from 'react'
import { AlertTriangle, BookOpen, CheckCircle2, ExternalLink, FileUp, Loader2, Scale } from 'lucide-react'
import { api, fileToBase64 } from '../lib/api'
import { BANDO_STATUS_STYLE, KIND_STYLE, fmtTs } from '../lib/format'
import PageIntro from './PageIntro'

const COV_STYLE = {
  REGOLA_DEL_BANDO: 'bg-[#deffac] text-black', SOLO_DATI: 'bg-sky-500/60 text-white', NON_ATTIVO: 'bg-neutral-800 text-neutral-500 border border-neutral-700',
}
const CONF_STYLE = {
  PRIMARIA: 'text-emerald-300 border-emerald-500/30', SECONDARIA: 'text-amber-300 border-amber-500/30', INTERPRETAZIONE: 'text-sky-300 border-sky-500/30',
  PARSING: 'text-fuchsia-300 border-fuchsia-500/30',
}

function Value({ v }) {
  if (Array.isArray(v)) return <span>{v.join(', ') || '—'}</span>
  if (typeof v === 'boolean') return <span>{v ? 'Sì' : 'No'}</span>
  return <span>{String(v)}</span>
}

function CoverageGrid({ coverage }) {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-10 sm:grid-cols-15 gap-1" style={{ gridTemplateColumns: 'repeat(15, minmax(0, 1fr))' }}>
        {coverage.map((c) => (
          <div key={c.criterion} title={`#${c.criterion} ${c.title}${c.via.length ? ` — regola: ${c.via.join(', ')}` : ''}`}
            className={`aspect-square rounded text-[9px] font-mono flex items-center justify-center ${COV_STYLE[c.status]}`}>{c.criterion}</div>
        ))}
      </div>
      <div className="flex flex-wrap gap-3 text-[11px] text-neutral-400">
        <span><span className="inline-block w-2.5 h-2.5 rounded bg-[#deffac] mr-1" />attivato da una regola del bando</span>
        <span><span className="inline-block w-2.5 h-2.5 rounded bg-sky-500/60 mr-1" />si esegue sui soli dati della riga</span>
        <span><span className="inline-block w-2.5 h-2.5 rounded bg-neutral-800 border border-neutral-700 mr-1" />non attivo: serve una regola che il bando non definisce</span>
      </div>
    </div>
  )
}

function UploadPanel({ onDone }) {
  const [name, setName] = useState('')
  const [text, setText] = useState('')
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const run = async () => {
    setBusy(true); setError(null); setResult(null)
    try {
      const body = { name, filename: file?.name || 'bando.txt' }
      if (file) body.content_base64 = await fileToBase64(file)
      else body.text = text
      const res = await api.bandoUpload(body)
      setResult(res)
      onDone(res.bando_id)
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  return (
    <div className="card p-5 space-y-3">
      <h3 className="font-bold text-sm flex items-center gap-2"><FileUp className="w-4 h-4 text-[#deffac]" />Carica un bando nuovo (testo o PDF)</h3>
      <p className="text-[11px] text-neutral-400">QUANTO legge il documento, estrae le regole numeriche, l’ambito delle categorie e <strong>ogni requisito</strong>, collegandoli ai criteri. Le frasi con un obbligo o un divieto che non riconosce finiscono in “da rivedere”: nulla viene ignorato in silenzio. Un PDF scansionato richiede un OCR (non incluso).</p>
      <div className="grid md:grid-cols-2 gap-3">
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Denominazione del bando" className="bg-neutral-950 border border-neutral-800 rounded-xl px-3 py-2 text-xs" />
        <input type="file" accept=".pdf,.txt,.md" onChange={(e) => setFile(e.target.files?.[0] || null)} className="text-xs text-neutral-400 file:mr-3 file:rounded-lg file:border-0 file:bg-neutral-800 file:px-3 file:py-2 file:text-xs file:text-neutral-200" />
      </div>
      {!file && <textarea value={text} onChange={(e) => setText(e.target.value)} rows={5} placeholder="…oppure incolla qui il testo del bando" className="w-full bg-neutral-950 border border-neutral-800 rounded-xl px-3 py-2 font-mono text-[11px]" />}
      <div className="flex items-center gap-3">
        <button onClick={run} disabled={busy || name.trim().length < 3 || (!file && text.trim().length < 100)} className="btn-primary flex items-center gap-2">
          {busy && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Analizza il bando
        </button>
        {error && <span className="text-xs text-red-300">{error}</span>}
        {result && <span className="text-xs text-emerald-300">Letti {result.characters_read.toLocaleString('it-IT')} caratteri · {Object.keys(result.rules_published).length} regole · {result.requirements_total} requisiti ({result.requirements_to_review} da rivedere)</span>}
      </div>
    </div>
  )
}

function Detail({ bando, onUse, using }) {
  const [tab, setTab] = useState('rules')
  const tabs = [['rules', `Regole (${bando.rules.length})`], ['reqs', `Requisiti (${bando.requirements.length})`], ['cov', 'Criteri attivati'], ['src', 'Fonti e lacune']]
  const toReview = bando.requirements.filter((r) => r.kind === 'DA_REVISIONARE').length
  return (
    <div className="card p-5 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-bold text-lg">{bando.name}</h3>
          <p className="text-xs text-neutral-400">{bando.issuer}{bando.period ? ` · ${bando.period.from} → ${bando.period.to}` : ''}</p>
          <span className={`inline-block mt-2 px-2 py-0.5 text-[10px] font-bold rounded border ${BANDO_STATUS_STYLE(bando.status || '')}`}>{bando.status || bando.extraction_status}</span>
        </div>
        <button onClick={() => onUse(bando.bando_id)} disabled={using || !bando.grant_rules} className="btn-primary flex items-center gap-2">
          {using && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Usa questo bando nel budget
        </button>
      </div>

      {bando.benefit && (
        <div className="p-3 rounded-xl bg-neutral-950 border border-neutral-800 text-xs text-neutral-300">
          <span className="label block mb-1">Tipo di agevolazione: {bando.benefit.type}</span>{bando.benefit.summary}
        </div>
      )}
      {bando.status?.startsWith('CHIUSO') && <p className="text-xs text-amber-300 flex gap-2"><AlertTriangle className="w-4 h-4 shrink-0" />Bando chiuso: utile per progetti in corso o come confronto.</p>}
      {toReview > 0 && <p className="text-xs text-fuchsia-300 flex gap-2"><AlertTriangle className="w-4 h-4 shrink-0" />{toReview} requisiti richiedono la revisione di un consulente.</p>}

      <div className="flex flex-wrap gap-1 bg-neutral-950 border border-neutral-800 p-1 rounded-xl w-fit">
        {tabs.map(([id, label]) => (
          <button key={id} onClick={() => setTab(id)} className={`px-3 py-1.5 text-xs font-bold rounded-lg ${tab === id ? 'bg-[#deffac] text-black' : 'text-neutral-400 hover:text-white'}`}>{label}</button>
        ))}
      </div>

      {tab === 'rules' && (
        <div className="space-y-2">
          {bando.rules.map((r) => (
            <div key={r.key} className="p-3 bg-neutral-950 border border-neutral-800 rounded-xl text-xs space-y-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-mono text-neutral-200">{r.key}</span>
                <span className="font-mono font-bold text-[#deffac]"><Value v={r.value} /></span>
              </div>
              <div className="flex flex-wrap items-center gap-2 text-[11px] text-neutral-400">
                <span className={`px-1.5 py-0.5 rounded border font-bold ${CONF_STYLE[r.confidence] || 'text-neutral-400 border-neutral-700'}`}>{r.confidence}</span>
                {r.criteria.length > 0 && <span>criteri: {r.criteria.map((c) => `#${c}`).join(' ')}</span>}
                {r.status === 'PENDING_REVIEW' && <span className="text-fuchsia-300">in attesa di revisione</span>}
              </div>
              {r.source_ref && <p className="text-[11px] text-neutral-500 leading-relaxed">{r.source_ref}</p>}
            </div>
          ))}
          {bando.rules.length === 0 && <p className="text-xs text-neutral-500 italic">Nessuna regola numerica pubblicata.</p>}
        </div>
      )}

      {tab === 'reqs' && (
        <div className="space-y-2">
          {bando.requirements.map((r) => (
            <div key={r.seq} className="p-3 bg-neutral-950 border border-neutral-800 rounded-xl text-xs space-y-1.5">
              <div className="flex flex-wrap items-center gap-2">
                <span className={`px-1.5 py-0.5 rounded border text-[10px] font-bold ${KIND_STYLE[r.kind]}`}>{r.kind.replace('_', ' ')}</span>
                <span className="font-semibold text-neutral-200">{r.topic}</span>
                {r.criteria.map((c) => <span key={c} className="font-mono text-[10px] text-[#deffac]">#{c}</span>)}
              </div>
              <p className="text-neutral-300 leading-relaxed">{r.text}</p>
              {r.source_ref && <p className="text-[10px] text-neutral-500">{r.source_ref}</p>}
            </div>
          ))}
        </div>
      )}

      {tab === 'cov' && (
        <div className="space-y-3">
          <p className="text-xs text-neutral-400">Quali dei 60 criteri questo bando attiva con le proprie regole ({bando.coverage_summary.REGOLA_DEL_BANDO}), quali girano sui soli dati della riga ({bando.coverage_summary.SOLO_DATI}) e quali restano spenti perché il bando non definisce la regola ({bando.coverage_summary.NON_ATTIVO}).</p>
          <CoverageGrid coverage={bando.coverage} />
        </div>
      )}

      {tab === 'src' && (
        <div className="space-y-4 text-xs">
          {bando.legal_refs?.length > 0 && <div><span className="label">Riferimenti normativi</span><ul className="mt-1 space-y-1 text-neutral-300 list-disc pl-4">{bando.legal_refs.map((l) => <li key={l}>{l}</li>)}</ul></div>}
          {bando.sources?.length > 0 && (
            <div><span className="label">Fonti consultate</span>
              <ul className="mt-1 space-y-1.5">{bando.sources.map((s) => (
                <li key={s.url} className="flex flex-wrap items-center gap-2">
                  <span className={`px-1.5 py-0.5 rounded border text-[10px] font-bold ${CONF_STYLE[s.confidence]}`}>{s.confidence}</span>
                  <a href={s.url} target="_blank" rel="noreferrer" className="text-sky-300 hover:underline inline-flex items-center gap-1">{s.title}<ExternalLink className="w-3 h-3" /></a>
                  <span className="text-neutral-500">consultata il {s.accessed}</span>
                </li>))}</ul></div>
          )}
          {bando.not_specified?.length > 0 && (
            <div><span className="label text-amber-300">Cosa le fonti NON dicono (non compilato con valori plausibili)</span>
              <ul className="mt-1 space-y-1 text-amber-200/90 list-disc pl-4">{bando.not_specified.map((n) => <li key={n}>{n}</li>)}</ul></div>
          )}
          {bando.usage.uploaded_sources.length > 0 && (
            <div><span className="label">Testi caricati</span>
              {bando.usage.uploaded_sources.map((s) => <p key={s.sha256} className="font-mono text-[11px] text-neutral-400">{s.name} · {s.chars.toLocaleString('it-IT')} car. · {fmtTs(s.ts)} · {s.sha256.slice(0, 12)}…</p>)}</div>
          )}
          <p className="text-[11px] text-neutral-500">Le schede non sostituiscono il bando: vanno riviste da un consulente prima di presentare una candidatura.</p>
        </div>
      )}
    </div>
  )
}

export default function BandiLibrary({ bandi, selectedId, onSelect, onReload }) {
  const [detail, setDetail] = useState(null)
  const [openId, setOpenId] = useState(selectedId || null)
  const [using, setUsing] = useState(false)
  const [error, setError] = useState(null)
  const [refs, setRefs] = useState([])

  const load = useCallback(async (id) => {
    setOpenId(id); setError(null)
    try { setDetail(await api.bandoDetail(id)) } catch (e) { setError(e.message) }
  }, [])

  useEffect(() => { if (openId) load(openId) }, []) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { api.bandoReferences().then(setRefs).catch(() => {}) }, [])

  const use = async (id) => {
    setUsing(true); setError(null)
    try { await onSelect(id) } catch (e) { setError(e.message) } finally { setUsing(false) }
  }

  return (
    <div className="space-y-6">
      <PageIntro title="Biblioteca dei bandi" tips={['Scegli un bando: le sue regole diventano quelle della validazione.', 'Ogni regola riporta la fonte e un livello di confidenza; ciò che le fonti non dicono è dichiarato, non inventato.', 'Puoi caricare il testo o il PDF di un bando nuovo: viene analizzato in profondità.']}>
        Qui scegli il bando su cui lavorare e vedi cosa QUANTO ne ha capito: regole numeriche, requisiti, criteri attivati, fonti e lacune.
      </PageIntro>
      {error && <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-xs">{error}</div>}

      <div className="grid lg:grid-cols-3 gap-6 items-start">
        <div className="space-y-3">
          {bandi.map((b) => (
            <button key={b.bando_id} onClick={() => load(b.bando_id)}
              className={`w-full text-left card p-4 space-y-2 transition hover:border-neutral-600 ${openId === b.bando_id ? '!border-[#deffac]' : ''}`}>
              <div className="flex items-start justify-between gap-2">
                <span className="font-bold text-sm leading-snug">{b.name}</span>
                {selectedId === b.bando_id && <CheckCircle2 className="w-4 h-4 text-[#deffac] shrink-0" />}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <span className={`px-2 py-0.5 text-[10px] font-bold rounded border ${BANDO_STATUS_STYLE(b.status || '')}`}>{(b.status || '').split(' (')[0] || b.extraction_status}</span>
                <span className="text-[11px] text-neutral-500">{b.issuer}</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-[10px] text-neutral-400 font-mono">
                <span>{b.rules_count} regole</span><span>{b.requirements_count} requisiti</span><span>{b.coverage.REGOLA_DEL_BANDO}/60 criteri</span>
              </div>
              {(b.gaps_count > 0 || b.requirements_to_review > 0) && (
                <p className="text-[10px] text-amber-300/80 flex items-center gap-1"><AlertTriangle className="w-3 h-3" />{b.gaps_count} lacune dichiarate{b.requirements_to_review ? ` · ${b.requirements_to_review} da rivedere` : ''}</p>
              )}
            </button>
          ))}
          {refs.map((r) => (
            <div key={r.id} className="card p-4 space-y-1.5">
              <div className="flex items-center gap-2"><Scale className="w-4 h-4 text-[#deffac]" /><span className="font-bold text-xs">{r.title}</span></div>
              <p className="text-[11px] text-neutral-400 leading-relaxed">{r.summary}</p>
              <p className="text-[10px] text-amber-300/80">{r.note}</p>
              <a href={r.url} target="_blank" rel="noreferrer" className="text-[11px] text-sky-300 hover:underline inline-flex items-center gap-1">EUR-Lex<ExternalLink className="w-3 h-3" /></a>
            </div>
          ))}
        </div>

        <div className="lg:col-span-2 space-y-6">
          {detail ? <Detail bando={detail} onUse={use} using={using} /> : (
            <div className="card p-10 text-center text-sm text-neutral-500 italic flex flex-col items-center gap-3"><BookOpen className="w-8 h-8 text-neutral-600" />Seleziona un bando dall’elenco per vederne regole, requisiti e fonti.</div>
          )}
          <UploadPanel onDone={async (id) => { await onReload(); await load(id) }} />
        </div>
      </div>
    </div>
  )
}
