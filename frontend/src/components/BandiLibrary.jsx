import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { AlertTriangle, CheckCircle2, ExternalLink, Loader2, Scale } from 'lucide-react'
import { api } from '../lib/api'
import { BANDO_STATUS_STYLE, KIND_STYLE, fmtTs } from '../lib/format'
import Guide from './Guide'
import ResearchPanel from './ResearchPanel'
import { Hint, Term } from './Help'

const COV_STYLE = {
  REGOLA_DEL_BANDO: 'bg-[#deffac] text-black', SOLO_DATI: 'bg-sky-500/60 text-white', NON_ATTIVO: 'bg-neutral-800 text-neutral-500 border border-neutral-700',
}
const CONF_STYLE = {
  PRIMARIA: 'text-emerald-300 border-emerald-500/30', SECONDARIA: 'text-amber-300 border-amber-500/30', INTERPRETAZIONE: 'text-sky-300 border-sky-500/30',
  PARSING: 'text-fuchsia-300 border-fuchsia-500/30',
}
const KIND_LABEL = { OBBLIGO: 'obbligo', DIVIETO: 'divieto', LIMITE: 'limite', INFO: 'informazione', DA_REVISIONARE: 'da rivedere' }

function Value({ v }) {
  if (v == null) return <span className="text-amber-300">da decidere</span>
  if (Array.isArray(v)) return <span>{v.join(', ') || '—'}</span>
  if (typeof v === 'boolean') return <span>{v ? 'Sì' : 'No'}</span>
  return <span>{String(v)}</span>
}

function CoverageGrid({ coverage }) {
  return (
    <div className="space-y-3">
      <div className="grid gap-1" style={{ gridTemplateColumns: 'repeat(15, minmax(0, 1fr))' }}>
        {coverage.map((c) => (
          <div key={c.criterion} title={`#${c.criterion} ${c.title}${c.via.length ? ` — regola: ${c.via.join(', ')}` : ''}`}
            className={`aspect-square rounded text-[10px] font-mono flex items-center justify-center ${COV_STYLE[c.status]}`}>{c.criterion}</div>
        ))}
      </div>
      <div className="flex flex-wrap gap-4 text-xs text-neutral-400">
        <span><span className="inline-block w-2.5 h-2.5 rounded bg-[#deffac] mr-1.5" />attivato da una regola del bando</span>
        <span><span className="inline-block w-2.5 h-2.5 rounded bg-sky-500/60 mr-1.5" />si fa solo sui dati della voce</span>
        <span><span className="inline-block w-2.5 h-2.5 rounded bg-neutral-800 border border-neutral-700 mr-1.5" />spento: il bando non dà la regola</span>
      </div>
    </div>
  )
}

const TIER_STYLE = { UFFICIALE: 'text-emerald-300 border-emerald-500/30', SECONDARIA: 'text-amber-300 border-amber-500/30' }
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

/** Testo integrale salvato in memoria: senza ricerca mostra l'inizio, con la ricerca mostra i passaggi che contengono le parole cercate. */
function SourceViewer({ bandoId, source, onClose }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [q, setQ] = useState('')
  const [shown, setShown] = useState(6000)
  useEffect(() => { api.sourceText(bandoId, source.sha256).then(setData).catch((e) => setError(e.message)) }, [bandoId, source.sha256])
  const excerpts = useMemo(() => {
    if (!data || q.trim().length < 2) return null
    const rx = new RegExp(esc(q.trim()), 'gi'); const out = []; let m
    while ((m = rx.exec(data.text)) && out.length < 40) {
      out.push({ at: m.index, text: data.text.slice(Math.max(0, m.index - 160), m.index + q.length + 260).replace(/\s+/g, ' ') })
      rx.lastIndex = m.index + 200
    }
    return out
  }, [data, q])
  const hl = (t) => t.split(new RegExp(`(${esc(q.trim())})`, 'gi')).map((part, i) => (i % 2 ? <mark key={i} className="bg-[#deffac]/30 text-white rounded px-0.5">{part}</mark> : part))
  return (
    <div className="p-3 bg-neutral-950 border border-neutral-800 rounded-xl space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-medium text-neutral-200 truncate max-w-full">{source.name}</span>
        <button onClick={onClose} className="ml-auto text-xs text-neutral-400 hover:text-white">Chiudi</button>
      </div>
      {error && <p className="text-xs text-red-300">{error}</p>}
      {!data && !error && <p className="text-xs text-neutral-500 flex items-center gap-2"><Loader2 className="w-3 h-3 animate-spin" />Carico il testo…</p>}
      {data && (
        <>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={`Cerca nel testo (${data.chars.toLocaleString('it-IT')} caratteri), es. “fondo perduto”, “35 anni”`} aria-label="Cerca nel testo" className="field" />
          {excerpts ? (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              <p className="text-[11px] text-neutral-500">{excerpts.length === 40 ? 'Primi 40 passaggi' : `${excerpts.length} ${excerpts.length === 1 ? 'passaggio' : 'passaggi'}`} con “{q.trim()}”</p>
              {excerpts.map((e) => <p key={e.at} className="text-xs text-neutral-300 leading-relaxed border-l-2 border-neutral-700 pl-3">…{hl(e.text)}…</p>)}
              {excerpts.length === 0 && <p className="text-xs text-neutral-500">Nessun passaggio trovato.</p>}
            </div>
          ) : (
            <div className="space-y-2">
              <pre className="whitespace-pre-wrap text-xs text-neutral-300 leading-relaxed max-h-96 overflow-y-auto font-sans">{data.text.slice(0, shown)}</pre>
              {shown < data.text.length && <button onClick={() => setShown(shown + 20000)} className="btn">Mostra altro testo</button>}
            </div>
          )}
        </>
      )}
    </div>
  )
}

function Sources({ bando }) {
  const [open, setOpen] = useState(null)
  const list = bando.usage.uploaded_sources
  if (!list.length) return <p className="text-xs text-neutral-500">Nessun documento in memoria: cerca il bando sul web oppure aggiungi un documento a mano.</p>
  return (
    <div className="space-y-2">
      <span className="label inline-flex items-center gap-1.5">Documenti in memoria ({list.length}) <Hint id="bando_fonti_scaricate" /></span>
      <ul className="space-y-1.5">
        {list.map((s) => (
          <li key={s.sha256} className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              {s.tier ? <span className={`px-1.5 py-0.5 rounded border text-[11px] font-medium ${TIER_STYLE[s.tier]}`}>{s.tier === 'UFFICIALE' ? 'ufficiale' : 'secondaria'}</span>
                : <span className="px-1.5 py-0.5 rounded border border-neutral-700 text-[11px] text-neutral-400">caricato a mano</span>}
              {s.url ? <a href={s.url} target="_blank" rel="noreferrer" className="text-sky-300 hover:underline inline-flex items-center gap-1 truncate max-w-[60vw] md:max-w-md">{s.name}<ExternalLink className="w-3 h-3 shrink-0" /></a>
                : <span className="text-neutral-200 truncate max-w-[60vw] md:max-w-md">{s.name}</span>}
              <span className="text-neutral-500">{s.pages ? `${s.pages} pag. · ` : ''}{s.chars.toLocaleString('it-IT')} caratteri · {fmtTs(s.ts)}</span>
              <button onClick={() => setOpen(open === s.sha256 ? null : s.sha256)} className="btn !py-1 ml-auto">{open === s.sha256 ? 'Chiudi' : 'Leggi il testo'}</button>
            </div>
            {open === s.sha256 && <SourceViewer bandoId={bando.bando_id} source={s} onClose={() => setOpen(null)} />}
          </li>
        ))}
      </ul>
    </div>
  )
}

function Requirements({ items }) {
  const [topic, setTopic] = useState('')
  const [q, setQ] = useState('')
  const [limit, setLimit] = useState(40)
  const topics = useMemo(() => {
    const m = {}
    items.forEach((r) => r.topic.split(' / ').forEach((t) => { m[t] = (m[t] || 0) + 1 }))
    return Object.entries(m).sort((a, b) => b[1] - a[1])
  }, [items])
  const rows = items.filter((r) => (!topic || r.topic.split(' / ').includes(topic)) && (!q.trim() || `${r.text} ${r.topic}`.toLowerCase().includes(q.trim().toLowerCase())))
  const link = (ref) => { const m = ref && ref.match(/^(.*?) — (https?:\/\/\S+)/); return m ? { label: m[1], url: m[2] } : null }
  return (
    <div className="space-y-3">
      <input value={q} onChange={(e) => { setQ(e.target.value); setLimit(40) }} placeholder="Cerca nei requisiti (es. età, fondo perduto, CUP)" aria-label="Cerca nei requisiti" className="field" />
      <div className="flex flex-wrap gap-1.5">
        <button onClick={() => { setTopic(''); setLimit(40) }} className={`px-2 py-1 rounded-lg border text-[11px] ${!topic ? 'border-[#deffac] text-white' : 'border-neutral-700 text-neutral-400 hover:text-white'}`}>Tutti ({items.length})</button>
        {topics.slice(0, 14).map(([t, n]) => (
          <button key={t} onClick={() => { setTopic(t === topic ? '' : t); setLimit(40) }} className={`px-2 py-1 rounded-lg border text-[11px] ${topic === t ? 'border-[#deffac] text-white' : 'border-neutral-700 text-neutral-400 hover:text-white'}`}>{t} ({n})</button>
        ))}
      </div>
      <p className="text-[11px] text-neutral-500">{rows.length} di {items.length} requisiti</p>
      {rows.slice(0, limit).map((r) => {
        const l = link(r.source_ref)
        return (
          <div key={r.seq} className="p-3 bg-neutral-950 border border-neutral-800 rounded-xl text-xs space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`px-1.5 py-0.5 rounded border text-[11px] font-medium ${KIND_STYLE[r.kind]}`}>{KIND_LABEL[r.kind] || r.kind}</span>
              <span className="font-medium text-neutral-100">{r.topic}</span>
              {r.criteria.map((c) => <span key={c} className="font-mono text-[11px] text-[#deffac]">#{c}</span>)}
            </div>
            <p className="text-neutral-300 leading-relaxed">{r.text}</p>
            {l ? <p className="text-[11px] text-neutral-500 truncate">Fonte: <a href={l.url} target="_blank" rel="noreferrer" className="hover:underline text-sky-300/80">{l.label}</a></p>
              : r.source_ref && <p className="text-[11px] text-neutral-500">{r.source_ref}</p>}
          </div>
        )
      })}
      {rows.length > limit && <button onClick={() => setLimit(limit + 40)} className="btn">Mostra altri {Math.min(40, rows.length - limit)}</button>}
      {rows.length === 0 && <p className="text-xs text-neutral-500">Nessun requisito con questi filtri.</p>}
    </div>
  )
}

const TAB_HINT = { rules: 'bando_scheda_regole', reqs: 'bando_scheda_req', cov: 'bando_scheda_cov', src: 'bando_scheda_fonti' }

function Detail({ bando, onUse, using }) {
  const [tab, setTab] = useState('rules')
  const tabs = [['rules', `Regole (${bando.rules.length})`], ['reqs', `Requisiti (${bando.requirements.length})`], ['cov', 'Controlli attivati'], ['src', 'Fonti e testi']]
  const toReview = bando.requirements.filter((r) => r.kind === 'DA_REVISIONARE').length
  return (
    <div className="card p-5 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-semibold text-lg">{bando.name}</h3>
          <p className="text-xs text-neutral-400">{bando.issuer}{bando.period ? ` · dal ${bando.period.from} al ${bando.period.to}` : ''}</p>
          <span className={`inline-block mt-2 px-2 py-0.5 text-[11px] font-medium rounded border ${BANDO_STATUS_STYLE(bando.status || '')}`}>{bando.status || bando.extraction_status}</span>
        </div>
        <button onClick={() => onUse(bando.bando_id)} disabled={using || !bando.grant_rules} className="btn-primary flex items-center gap-2">
          {using && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Usa questo bando nel budget
        </button>
      </div>

      {bando.benefit && (
        <div className="p-3 rounded-xl bg-neutral-950 border border-neutral-800 text-xs text-neutral-300 leading-relaxed">
          <span className="label block mb-1">Che tipo di aiuto è: {bando.benefit.type}</span>{bando.benefit.summary}
        </div>
      )}
      {bando.status?.startsWith('CHIUSO') && <p className="text-xs text-amber-300 flex gap-2"><AlertTriangle className="w-4 h-4 shrink-0" />Bando chiuso: utile per progetti in corso o per fare confronti.</p>}
      {toReview > 0 && <p className="text-xs text-fuchsia-300 flex gap-2"><AlertTriangle className="w-4 h-4 shrink-0" />{toReview} requisiti vanno controllati a mano da un consulente.</p>}

      <div className="flex items-center gap-3">
        <div className="flex flex-wrap gap-x-5 gap-y-1 border-b border-neutral-800 flex-1">
          {tabs.map(([id, label]) => (
            <button key={id} onClick={() => setTab(id)} className={`pb-2 text-xs -mb-px border-b-2 ${tab === id ? 'border-[#deffac] text-white font-medium' : 'border-transparent text-neutral-400 hover:text-white'}`}>{label}</button>
          ))}
        </div>
        <Hint id={TAB_HINT[tab]} />
      </div>

      {tab === 'rules' && (
        <div className="space-y-2">
          {bando.rules.map((r) => (
            <div key={r.key} className="p-3 bg-neutral-950 border border-neutral-800 rounded-xl text-xs space-y-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-mono text-neutral-200">{r.key}</span>
                <span className="font-mono font-semibold text-[#deffac]"><Value v={r.value} /></span>
              </div>
              <div className="flex flex-wrap items-center gap-2 text-xs text-neutral-400">
                <span className={`px-1.5 py-0.5 rounded border font-medium ${CONF_STYLE[r.confidence] || 'text-neutral-400 border-neutral-700'}`}>{r.confidence}</span>
                {r.criteria.length > 0 && <span>controlli: {r.criteria.map((c) => `#${c}`).join(' ')}</span>}
                {r.status === 'PENDING_REVIEW' && <span className="text-fuchsia-300 inline-flex items-center gap-1.5">da controllare a mano{r.passes?.length > 0 && <span className="font-mono">· letture diverse: {r.passes.join(' ≠ ')}</span>}<Hint id="bando_regole_verifica" /></span>}
              </div>
              {r.source_ref && <p className="text-xs text-neutral-500 leading-relaxed">{r.source_ref}</p>}
            </div>
          ))}
          {bando.rules.length === 0 && <p className="text-xs text-neutral-500">Nessuna regola numerica pubblicata.</p>}
          <p className="text-xs text-neutral-500 pt-1">Che cosa significano PRIMARIA, SECONDARIA…? Clicca <Term id="confidenza">affidabilità di una regola</Term>.</p>
        </div>
      )}

      {tab === 'reqs' && <Requirements items={bando.requirements} />}

      {tab === 'cov' && (
        <div className="space-y-3">
          <p className="text-xs text-neutral-400 leading-relaxed">Dei 60 controlli: <strong className="text-[#deffac]">{bando.coverage_summary.REGOLA_DEL_BANDO}</strong> sono attivati da regole di questo bando, <strong className="text-sky-300">{bando.coverage_summary.SOLO_DATI}</strong> si fanno solo sui dati che inserisci nelle voci, <strong className="text-neutral-300">{bando.coverage_summary.NON_ATTIVO}</strong> restano spenti perché il bando non dà la regola. Passa il mouse su un quadratino per leggere il nome del controllo.</p>
          <CoverageGrid coverage={bando.coverage} />
        </div>
      )}

      {tab === 'src' && (
        <div className="space-y-5 text-xs">
          <Sources bando={bando} />
          {bando.legal_refs?.length > 0 && <div><span className="label">Atti di legge citati nei documenti</span><ul className="mt-1 space-y-1 text-neutral-300 list-disc pl-4">{bando.legal_refs.map((l) => <li key={l}>{l}</li>)}</ul></div>}
          {bando.sources?.length > 0 && (
            <div><span className="label">Fonti consultate</span>
              <ul className="mt-1 space-y-1.5">{bando.sources.map((s) => (
                <li key={s.url} className="flex flex-wrap items-center gap-2">
                  <span className={`px-1.5 py-0.5 rounded border text-[11px] font-medium ${CONF_STYLE[s.confidence]}`}>{s.confidence}</span>
                  <a href={s.url} target="_blank" rel="noreferrer" className="text-sky-300 hover:underline inline-flex items-center gap-1">{s.title}<ExternalLink className="w-3 h-3" /></a>
                  <span className="text-neutral-500">letta il {s.accessed}</span>
                </li>))}</ul></div>
          )}
          {bando.not_specified?.length > 0 && (
            <div><span className="label text-amber-300">Cosa le fonti NON dicono (non lo inventiamo)</span>
              <ul className="mt-1 space-y-1 text-amber-200/90 list-disc pl-4">{bando.not_specified.map((n) => <li key={n}>{n}</li>)}</ul></div>
          )}
          {bando.usage.uploaded_sources.length > 0 && (
            <div><span className="label">Testi caricati</span>
              {bando.usage.uploaded_sources.map((s) => <p key={s.sha256} className="font-mono text-[11px] text-neutral-400">{s.name} · {s.chars.toLocaleString('it-IT')} car. · {fmtTs(s.ts)} · {s.sha256.slice(0, 12)}…</p>)}</div>
          )}
          <p className="text-xs text-neutral-500">Queste schede non sostituiscono il bando: fai controllare le regole da un consulente prima di presentare la domanda.</p>
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
      <Guide page="bandi" />
      {error && <div className="p-3 rounded-xl border border-red-500/30 text-red-300 text-xs">{error}</div>}

      <div className="grid lg:grid-cols-3 gap-6 items-start">
        <div className="space-y-3">
          {bandi.map((b) => (
            <button key={b.bando_id} onClick={() => load(b.bando_id)}
              className={`w-full text-left card p-4 space-y-2 transition hover:border-neutral-600 ${openId === b.bando_id ? '!border-[#deffac]' : ''}`}>
              <div className="flex items-start justify-between gap-2">
                <span className="font-semibold text-sm leading-snug">{b.name}</span>
                {selectedId === b.bando_id && <CheckCircle2 className="w-4 h-4 text-[#deffac] shrink-0" aria-label="In uso" />}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <span className={`px-2 py-0.5 text-[11px] font-medium rounded border ${BANDO_STATUS_STYLE(b.status || '')}`}>{(b.status || '').split(' (')[0] || b.extraction_status}</span>
                <span className="text-xs text-neutral-500">{b.issuer}</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-[11px] text-neutral-400 font-mono">
                <span>{b.rules_count} regole</span><span>{b.requirements_count} requisiti</span><span>{b.coverage.REGOLA_DEL_BANDO}/60 controlli</span>
              </div>
              {(b.gaps_count > 0 || b.requirements_to_review > 0) && (
                <p className="text-[11px] text-amber-300/80 flex items-center gap-1"><AlertTriangle className="w-3 h-3" />{b.gaps_count} lacune (cose non dette){b.requirements_to_review ? ` · ${b.requirements_to_review} da rivedere` : ''}</p>
              )}
            </button>
          ))}
          {refs.map((r) => (
            <div key={r.id} className="card p-4 space-y-1.5">
              <div className="flex items-center gap-2"><Scale className="w-4 h-4 text-neutral-400" /><span className="font-semibold text-xs">{r.title}</span></div>
              <p className="text-xs text-neutral-400 leading-relaxed">{r.summary}</p>
              <p className="text-[11px] text-amber-300/80">{r.note}</p>
              <a href={r.url} target="_blank" rel="noreferrer" className="text-xs text-sky-300 hover:underline inline-flex items-center gap-1">EUR-Lex<ExternalLink className="w-3 h-3" /></a>
            </div>
          ))}
        </div>

        <div className="lg:col-span-2 space-y-6">
          {detail ? <Detail bando={detail} onUse={use} using={using} /> : (
            <div className="card p-10 text-center text-sm text-neutral-500">Scegli un bando dall’elenco per vederne regole, requisiti e fonti.</div>
          )}
          <ResearchPanel onDone={async (id) => { await onReload(); await load(id) }} />
        </div>
      </div>
    </div>
  )
}
