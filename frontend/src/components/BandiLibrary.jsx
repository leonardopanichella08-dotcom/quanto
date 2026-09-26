import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { AlertTriangle, CheckCircle2, ExternalLink, Loader2, Scale } from 'lucide-react'
import { api } from '../lib/api'
import { BANDO_STATUS_STYLE, KIND_STYLE, fmtTs } from '../lib/format'
import { ruleLabel } from '../data/ruleLabels'
import Guide from './Guide'
import ResearchPanel from './ResearchPanel'
import CatalogBrowser from './CatalogBrowser'
import { Hint, Term } from './Help'

const COV_STYLE = {
  REGOLA_DEL_BANDO: 'bg-liquid text-ink', SOLO_DATI: 'bg-sky-500/60 text-ink', NON_ATTIVO: 'bg-tint-2 text-mute border border-line-strong',
}
const CONF_STYLE = {
  PRIMARIA: 'text-emerald-700 border-emerald-500/30', SECONDARIA: 'text-amber-700 border-amber-500/30', INTERPRETAZIONE: 'text-sky-700 border-sky-500/30',
  PARSING: 'text-fuchsia-700 border-fuchsia-500/30',
}
const KIND_LABEL = { OBBLIGO: 'obbligo', DIVIETO: 'divieto', LIMITE: 'limite', INFO: 'informazione', DA_REVISIONARE: 'da rivedere' }

function Value({ v }) {
  if (v == null) return <span className="text-amber-700">da decidere</span>
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
      <div className="flex flex-wrap gap-4 text-xs text-ink-2">
        <span><span className="inline-block w-2.5 h-2.5 rounded bg-liquid mr-1.5" />attivato da una regola del bando</span>
        <span><span className="inline-block w-2.5 h-2.5 rounded bg-sky-500/60 mr-1.5" />si fa solo sui dati della voce</span>
        <span><span className="inline-block w-2.5 h-2.5 rounded bg-tint-2 border border-line-strong mr-1.5" />spento: il bando non dà la regola</span>
      </div>
    </div>
  )
}

const TIER_STYLE = { UFFICIALE: 'text-emerald-700 border-emerald-500/30', SECONDARIA: 'text-amber-700 border-amber-500/30' }

/** Testo integrale salvato in memoria: senza ricerca mostra l'inizio, con la ricerca mostra i passaggi che contengono le parole cercate. */
function Sources({ bando }) {
  const list = bando.usage.uploaded_sources
  if (!list.length) return <p className="text-xs text-mute">Nessun documento in memoria: cerca il bando sul web oppure aggiungi un documento a mano.</p>
  return (
    <div className="space-y-2">
      <span className="label inline-flex items-center gap-1.5">Documenti da cui derivano le regole ({list.length}) <Hint id="bando_fonti_scaricate" /></span>
      <ul className="space-y-1.5">
        {list.map((s) => (
          <li key={s.sha256} className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              {s.tier ? <span className={`px-1.5 py-0.5 rounded border text-[11px] font-medium ${TIER_STYLE[s.tier]}`}>{s.tier === 'UFFICIALE' ? 'ufficiale' : 'secondaria'}</span>
                : <span className="px-1.5 py-0.5 rounded border border-line-strong text-[11px] text-ink-2">caricato a mano</span>}
              {s.url ? <a href={s.url} target="_blank" rel="noreferrer" className="text-sky-700 hover:underline inline-flex items-center gap-1 truncate max-w-[60vw] md:max-w-md">{s.name}<ExternalLink className="w-3 h-3 shrink-0" /></a>
                : <span className="text-ink truncate max-w-[60vw] md:max-w-md">{s.name}</span>}
              <span className="text-mute">{s.pages ? `${s.pages} pag. · ` : ''}{s.chars.toLocaleString('it-IT')} caratteri · {fmtTs(s.ts)}</span>
            </div>
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
        <button onClick={() => { setTopic(''); setLimit(40) }} className={`px-2 py-1 rounded-lg border text-[11px] ${!topic ? 'border-brand text-ink' : 'border-line-strong text-ink-2 hover:text-ink'}`}>Tutti ({items.length})</button>
        {topics.slice(0, 14).map(([t, n]) => (
          <button key={t} onClick={() => { setTopic(t === topic ? '' : t); setLimit(40) }} className={`px-2 py-1 rounded-lg border text-[11px] ${topic === t ? 'border-brand text-ink' : 'border-line-strong text-ink-2 hover:text-ink'}`}>{t} ({n})</button>
        ))}
      </div>
      <p className="text-[11px] text-mute">{rows.length} di {items.length} requisiti</p>
      {rows.slice(0, limit).map((r) => {
        const l = link(r.source_ref)
        return (
          <div key={r.seq} className="p-3 bg-field border border-line rounded-xl text-xs space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`px-1.5 py-0.5 rounded border text-[11px] font-medium ${KIND_STYLE[r.kind]}`}>{KIND_LABEL[r.kind] || r.kind}</span>
              <span className="font-medium text-ink">{r.topic}</span>
              {r.criteria.map((c) => <span key={c} className="font-mono text-[11px] text-brand-ink">#{c}</span>)}
            </div>
            <p className="text-ink-2 leading-relaxed">{r.text}</p>
            {l ? <p className="text-[11px] text-mute truncate">Fonte: <a href={l.url} target="_blank" rel="noreferrer" className="hover:underline text-sky-700">{l.label}</a></p>
              : r.source_ref && <p className="text-[11px] text-mute">{r.source_ref}</p>}
          </div>
        )
      })}
      {rows.length > limit && <button onClick={() => setLimit(limit + 40)} className="btn">Mostra altri {Math.min(40, rows.length - limit)}</button>}
      {rows.length === 0 && <p className="text-xs text-mute">Nessun requisito con questi filtri.</p>}
    </div>
  )
}

const TAB_HINT = { rules: 'bando_scheda_regole', reqs: 'bando_scheda_req', cov: 'bando_scheda_cov', src: 'bando_scheda_fonti' }

function Detail({ bando, onUse, using }) {
  const [tab, setTab] = useState('rules')
  const rules = bando.rules.filter((r) => r.status === 'PUBLISHED')        // le regole in disaccordo le vede solo il Quartier Generale
  const requirements = bando.requirements.filter((r) => r.kind !== 'DA_REVISIONARE')
  const tabs = [['rules', `Regole (${rules.length})`], ['reqs', `Requisiti (${requirements.length})`], ['cov', 'Controlli attivati'], ['src', 'Fonti']]
  return (
    <div className="card p-5 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-semibold text-lg">{bando.name}</h3>
          <p className="text-xs text-ink-2">{bando.issuer}{bando.period ? ` · dal ${bando.period.from} al ${bando.period.to}` : ''}</p>
          <span className={`inline-block mt-2 px-2 py-0.5 text-[11px] font-medium rounded border ${BANDO_STATUS_STYLE(bando.status || '')}`}>{bando.status || bando.extraction_status}</span>
        </div>
        <button onClick={() => onUse(bando.bando_id)} disabled={using || !bando.grant_rules} className="btn-primary flex items-center gap-2">
          {using && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Usa questo bando nel budget
        </button>
      </div>

      {bando.benefit && (
        <div className="p-3 rounded-xl bg-field border border-line text-xs text-ink-2 leading-relaxed">
          <span className="label block mb-1">Che tipo di aiuto è: {bando.benefit.type}</span>{bando.benefit.summary}
        </div>
      )}
      {bando.status?.startsWith('CHIUSO') && <p className="text-xs text-amber-700 flex gap-2"><AlertTriangle className="w-4 h-4 shrink-0" />Bando chiuso: utile per progetti in corso o per fare confronti.</p>}

      <div className="flex items-center gap-3">
        <div className="flex flex-wrap gap-x-5 gap-y-1 border-b border-line flex-1">
          {tabs.map(([id, label]) => (
            <button key={id} onClick={() => setTab(id)} className={`pb-2 text-xs -mb-px border-b-2 ${tab === id ? 'border-brand text-ink font-medium' : 'border-transparent text-ink-2 hover:text-ink'}`}>{label}</button>
          ))}
        </div>
        <Hint id={TAB_HINT[tab]} />
      </div>

      {tab === 'rules' && (
        <div className="space-y-2">
          {rules.map((r) => (
            <div key={r.key} className="p-3 bg-field border border-line rounded-xl text-xs space-y-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-medium text-ink" title={r.key}>{ruleLabel(r.key)}</span>
                <span className="font-mono font-semibold text-brand-ink"><Value v={r.value} /></span>
              </div>
              <div className="flex flex-wrap items-center gap-2 text-xs text-ink-2">
                <span className={`px-1.5 py-0.5 rounded border font-medium ${CONF_STYLE[r.confidence] || 'text-ink-2 border-line-strong'}`}>{r.confidence}</span>
                {r.criteria.length > 0 && <span>controlli: {r.criteria.map((c) => `#${c}`).join(' ')}</span>}
              </div>
              {r.source_ref && <p className="text-xs text-mute leading-relaxed">{r.source_ref}</p>}
            </div>
          ))}
          {rules.length === 0 && <p className="text-xs text-mute">Nessuna regola numerica pubblicata.</p>}
          <p className="text-xs text-mute pt-1">Che cosa significano PRIMARIA, SECONDARIA…? Clicca <Term id="confidenza">affidabilità di una regola</Term>.</p>
        </div>
      )}

      {tab === 'reqs' && <Requirements items={requirements} />}

      {tab === 'cov' && (
        <div className="space-y-3">
          <p className="text-xs text-ink-2 leading-relaxed">Dei 60 controlli: <strong className="text-brand-ink">{bando.coverage_summary.REGOLA_DEL_BANDO}</strong> sono attivati da regole di questo bando, <strong className="text-sky-700">{bando.coverage_summary.SOLO_DATI}</strong> si fanno solo sui dati che inserisci nelle voci, <strong className="text-ink-2">{bando.coverage_summary.NON_ATTIVO}</strong> restano spenti perché il bando non dà la regola. Passa il mouse su un quadratino per leggere il nome del controllo.</p>
          <CoverageGrid coverage={bando.coverage} />
        </div>
      )}

      {tab === 'src' && (
        <div className="space-y-5 text-xs">
          <Sources bando={bando} />
          {bando.legal_refs?.length > 0 && <div><span className="label">Atti di legge citati nei documenti</span><ul className="mt-1 space-y-1 text-ink-2 list-disc pl-4">{bando.legal_refs.map((l) => <li key={l}>{l}</li>)}</ul></div>}
          {bando.sources?.length > 0 && (
            <div><span className="label">Fonti consultate</span>
              <ul className="mt-1 space-y-1.5">{bando.sources.map((s) => (
                <li key={s.url} className="flex flex-wrap items-center gap-2">
                  <span className={`px-1.5 py-0.5 rounded border text-[11px] font-medium ${CONF_STYLE[s.confidence]}`}>{s.confidence}</span>
                  <a href={s.url} target="_blank" rel="noreferrer" className="text-sky-700 hover:underline inline-flex items-center gap-1">{s.title}<ExternalLink className="w-3 h-3" /></a>
                  <span className="text-mute">letta il {s.accessed}</span>
                </li>))}</ul></div>
          )}
          {bando.usage.uploaded_sources.length > 0 && (
            <div><span className="label">Testi caricati</span>
              {bando.usage.uploaded_sources.map((s) => <p key={s.sha256} className="font-mono text-[11px] text-ink-2">{s.name} · {s.chars.toLocaleString('it-IT')} car. · {fmtTs(s.ts)} · {s.sha256.slice(0, 12)}…</p>)}</div>
          )}
          <p className="text-xs text-mute">Queste schede non sostituiscono il bando: fai controllare le regole da un consulente prima di presentare la domanda.</p>
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
  const [catalogPick, setCatalogPick] = useState(null)
  const [picking, setPicking] = useState(null)
  const researchRef = useRef(null)

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
      {error && <div className="p-3 rounded-xl border border-red-500/30 text-red-700 text-xs">{error}</div>}

      <div className="grid lg:grid-cols-3 gap-6 items-start">
        <div className="space-y-3">
          <p className="text-[11px] text-mute leading-relaxed px-1">
            «N/60 controlli» è quanti dei 60 criteri <em>questo</em> bando attiva con le sue regole — non un punteggio di
            completezza. Un bando che finanzia solo attrezzature non parlerà mai di ore di lavoro straordinario: restare
            sotto 60 è la norma, non un'analisi a metà. <Hint id="bando_controlli_attivi" />
          </p>
          {bandi.map((b) => (
            <button key={b.bando_id} onClick={() => load(b.bando_id)}
              className={`w-full text-left card p-4 space-y-2 transition hover:border-line-strong ${openId === b.bando_id ? '!border-brand' : ''}`}>
              <div className="flex items-start justify-between gap-2">
                <span className="font-semibold text-sm leading-snug">{b.name}</span>
                {selectedId === b.bando_id && <CheckCircle2 className="w-4 h-4 text-brand-ink shrink-0" aria-label="In uso" />}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <span className={`px-2 py-0.5 text-[11px] font-medium rounded border ${BANDO_STATUS_STYLE(b.status || '')}`}>{(b.status || '').split(' (')[0] || b.extraction_status}</span>
                <span className="text-xs text-mute">{b.issuer}</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-[11px] text-ink-2 font-mono">
                <span>{b.rules_count} regole</span><span>{b.requirements_count} requisiti</span><span>{b.coverage.REGOLA_DEL_BANDO}/60 controlli</span>
              </div>
            </button>
          ))}
          {refs.map((r) => (
            <div key={r.id} className="card p-4 space-y-1.5">
              <div className="flex items-center gap-2"><Scale className="w-4 h-4 text-ink-2" /><span className="font-semibold text-xs">{r.title}</span></div>
              <p className="text-xs text-ink-2 leading-relaxed">{r.summary}</p>
              <p className="text-[11px] text-amber-700">{r.note}</p>
              <a href={r.url} target="_blank" rel="noreferrer" className="text-xs text-sky-700 hover:underline inline-flex items-center gap-1">EUR-Lex<ExternalLink className="w-3 h-3" /></a>
            </div>
          ))}
        </div>

        <div className="lg:col-span-2 space-y-6">
          {detail ? <Detail bando={detail} onUse={use} using={using} /> : (
            <div className="card p-10 text-center text-sm text-mute">Scegli un bando dall’elenco per vederne regole, requisiti e fonti.</div>
          )}
          <CatalogBrowser picking={picking} onPick={(item) => {
            setPicking(item.bando_id); setCatalogPick(item)
            researchRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
            setTimeout(() => setPicking((p) => (p === item.bando_id ? null : p)), 20000)   // rete di sicurezza: non resta bloccato se qualcosa fallisce prima di "onDone"
          }} />
          <div ref={researchRef}>
            <ResearchPanel pick={catalogPick} onDone={async (id) => { setPicking(null); await onReload(); await load(id) }} />
          </div>
        </div>
      </div>
    </div>
  )
}
