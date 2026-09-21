import React, { useRef, useState } from 'react'
import { AlertTriangle, CheckCircle2, ExternalLink, FileUp, Loader2, Plus, Search, XCircle } from 'lucide-react'
import { api, fileToBase64 } from '../lib/api'
import { Hint } from './Help'

const MAX_DOCS = 16          // documenti scaricati per ricerca
const MAX_DEPTH = 2          // pagina → sue pagine/PDF → loro allegati
const norm = (u) => u.replace(/^https?:\/\/(www\.)?/, '').replace(/[#?].*$/, '').replace(/\/$/, '').toLowerCase()
const TIER_LABEL = { UFFICIALE: 'ufficiale', SECONDARIA: 'secondaria' }
const TIER_STYLE = { UFFICIALE: 'text-emerald-700 border-emerald-500/30', SECONDARIA: 'text-amber-700 border-amber-500/30' }

function Step({ n, state, title, children }) {
  const icon = state === 'run' ? <Loader2 className="w-4 h-4 animate-spin text-brand-ink" /> : state === 'done' ? <CheckCircle2 className="w-4 h-4 text-emerald-700" />
    : state === 'fail' ? <XCircle className="w-4 h-4 text-red-700" /> : <span className="w-4 h-4 rounded-full border border-line-strong text-[10px] text-mute flex items-center justify-center">{n}</span>
  return (
    <div className={`space-y-1.5 ${state === 'todo' ? 'opacity-50' : ''}`}>
      <div className="flex items-center gap-2 text-sm font-medium">{icon}{title}</div>
      {children && <div className="pl-6 text-xs text-ink-2 space-y-1">{children}</div>}
    </div>
  )
}

export default function ResearchPanel({ onDone }) {
  const [name, setName] = useState('')
  const [hint, setHint] = useState('')
  const [urls, setUrls] = useState('')
  const [phase, setPhase] = useState('idle')          // idle | search | fetch | analyze | done | error
  const [error, setError] = useState(null)
  const [search, setSearch] = useState(null)
  const [matches, setMatches] = useState(null)         // bandi già in memoria che assomigliano al nome
  const [picked, setPicked] = useState(new Set())      // pagine scelte dall'utente
  const [confirmInfo, setConfirmInfo] = useState(null)
  const [force, setForce] = useState(false)
  const [docs, setDocs] = useState([])                // {key,url,title,status,tier,kind,chars,pages,message,warnings}
  const [result, setResult] = useState(null)
  const [busyExtra, setBusyExtra] = useState(null)
  const [manual, setManual] = useState({ text: '', file: null, open: false })
  const bandoRef = useRef(null)
  const internalRef = useRef(null)                  // bando scelto dall'elenco interno (anche solo del catalogo nazionale)

  const patchDoc = (key, patch) => setDocs((d) => d.map((x) => (x.key === key ? { ...x, ...patch } : x)))

  const analyze = async (bandoId) => {
    setPhase('analyze')
    const res = await api.researchAnalyze({ bando_id: bandoId })
    setResult(res)
    setPhase('done')
    await onDone(bandoId)
    return res
  }

  // 1) cerco nell'elenco interno (nome esatto o approssimato) — nessuna rete
  const lookup = async () => {
    setError(null); setResult(null); setDocs([]); setSearch(null); setMatches(null); setPicked(new Set()); setConfirmInfo(null); setForce(false); internalRef.current = null; setPhase('lookup')
    try {
      const r = await api.bandiSearch(name.trim())
      setMatches(r.matches)
      if (r.matches.length) setPhase('matches'); else await webSearch()
    } catch (e) { setPhase('error'); setError(e.message) }
  }

  // 2) se non c'è (o l'utente vuole aggiornarlo) cerco sul web: si scelgono le pagine, ancora niente viene scaricato
  const webSearch = async (nameOverride) => {
    setError(null); setPhase('search')
    try {
      const supplied = urls.split('\n').map((u) => u.trim()).filter(Boolean)
      const s = await api.researchSearch({ name: (nameOverride || name).trim(), hint: hint.trim(), urls: supplied })
      setSearch(s); bandoRef.current = s.bando_id
      if (!s.candidates.length) {
        setPhase('error')
        setError(s.engine_errors?.length ? `Non sono riuscito a usare il motore di ricerca (${s.engine_errors[0]}). Incolla qui sotto il link della pagina ufficiale del bando e riprova.`
          : 'Non ho trovato pagine ufficiali per questo nome. Prova con altre parole, oppure incolla il link della pagina ufficiale.')
        return
      }
      const pre = s.candidates.filter((c) => c.preselected)
      setPicked(new Set((pre.length ? pre : s.candidates.slice(0, 4)).map((c) => c.url)))
      setPhase('pick')
    } catch (e) { setPhase('error'); setError(e.message) }
  }

  // 3) l'utente conferma che è il bando giusto: si registra la richiesta e si controlla la cache
  const confirmBando = async (payload, viaWeb) => {
    setError(null)
    try {
      const c = await api.researchConfirm(payload)
      bandoRef.current = c.bando_id; setConfirmInfo(c)
      if (c.complete && !force) { setPhase('cached'); await onDone(c.bando_id); return }      // cache: niente da riscaricare
      if (viaWeb) await downloadPicked(c.bando_id)
      else { setName(payload.name); await webSearch(payload.name) }                             // bando interno ma incompleto: si cercano le fonti
    } catch (e) { setPhase('error'); setError(e.message) }
  }

  // 4) scarico le pagine scelte (e i PDF che citano), poi leggo tutto
  const downloadPicked = async (bandoId) => {
    try {
      const queue = (search?.candidates || []).filter((c) => picked.has(c.url)).map((c) => ({ url: c.url, title: c.title, tier: c.tier, score: c.user_supplied ? 500 : 200, depth: 0 }))
      setPhase('fetch')
      const seen = new Set(); let ok = 0; let attempts = 0
      while (queue.length && ok < MAX_DOCS && attempts < MAX_DOCS + 8) {
        queue.sort((a, b) => b.score - a.score)         // prima i risultati della ricerca, poi PDF e atti di legge trovati nelle pagine
        const item = queue.shift()
        if (seen.has(norm(item.url))) continue
        seen.add(norm(item.url)); attempts += 1
        const key = norm(item.url)
        setDocs((d) => [...d, { key, url: item.url, title: item.title, tier: item.tier, status: 'run', depth: item.depth }])
        try {
          const r = await api.researchFetch({ bando_id: bandoId, url: item.url })
          ok += 1
          patchDoc(key, { status: 'ok', title: r.source.name, tier: r.source.tier, kind: r.source.kind, chars: r.source.chars, pages: r.source.pages, warnings: r.source.warnings, url: r.source.url })
          seen.add(norm(r.source.url))
          if (item.depth < MAX_DEPTH) r.links.slice(0, 8).forEach((l) => queue.push({ url: l.url, title: l.title, tier: 'UFFICIALE', score: l.score - 20 * item.depth, depth: item.depth + 1 }))
        } catch (e) {
          patchDoc(key, { status: 'error', message: e.message })
        }
      }
      if (!ok) { setPhase('error'); setError('Non sono riuscito a scaricare nessun documento. Puoi aggiungerne uno a mano qui sotto.'); return }
      await analyze(bandoId)
    } catch (e) {
      setPhase('error'); setError(e.message)
    }
  }

  // aggiunge una fonte tra quelle trovate ma non scaricate (di solito secondarie), poi rilegge tutto
  const addCandidate = async (c) => {
    setBusyExtra(c.url); setError(null)
    try {
      const key = norm(c.url)
      setDocs((d) => [...d, { key, url: c.url, title: c.title, tier: c.tier, status: 'run', depth: 0 }])
      try {
        const r = await api.researchFetch({ bando_id: bandoRef.current, url: c.url })
        patchDoc(key, { status: 'ok', title: r.source.name, tier: r.source.tier, kind: r.source.kind, chars: r.source.chars, pages: r.source.pages, warnings: r.source.warnings })
      } catch (e) { patchDoc(key, { status: 'error', message: e.message }); return }
      await analyze(bandoRef.current)
    } catch (e) { setError(e.message) } finally { setBusyExtra(null) }
  }

  const addManual = async () => {
    setBusyExtra('manual'); setError(null)
    try {
      const body = { name: name.trim(), bando_id: bandoRef.current || undefined, filename: manual.file?.name || 'testo-incollato.txt' }
      if (manual.file) body.content_base64 = await fileToBase64(manual.file)
      else body.text = manual.text
      const res = await api.bandoUpload(body)
      bandoRef.current = res.bando_id
      setManual({ text: '', file: null, open: false })
      setResult(await analyze(res.bando_id))
    } catch (e) { setError(e.message) } finally { setBusyExtra(null) }
  }

  const running = ['lookup', 'search', 'fetch', 'analyze'].includes(phase)
  const okDocs = docs.filter((d) => d.status === 'ok')
  const notFetched = (search?.candidates || []).filter((c) => !docs.some((d) => d.key === norm(c.url)))

  return (
    <div className="card p-5 space-y-4">
      <h3 className="font-semibold text-base flex items-center gap-2"><Search className="w-4 h-4 text-brand-ink" />Cerca un bando sul web <Hint id="bando_ricerca" /></h3>
      <p className="text-xs text-ink-2 leading-relaxed max-w-3xl">Scrivi il nome del bando. QUANTO lo cerca su internet, scarica le pagine e i PDF ufficiali (decreti, avvisi, circolari, atti della Gazzetta Ufficiale), li salva in memoria e li legge tutti. Le fonti ufficiali hanno la precedenza.</p>

      <div className="grid md:grid-cols-2 gap-3">
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Nome del bando (es. Resto al Sud)" aria-label="Nome del bando" className="field" disabled={running} />
        <input value={hint} onChange={(e) => setHint(e.target.value)} placeholder="Parole in più, facoltative (es. 2025, Invitalia)" aria-label="Parole in più" className="field" disabled={running} />
      </div>
      <textarea value={urls} onChange={(e) => setUrls(e.target.value)} rows={2} disabled={running} aria-label="Link ufficiali"
        placeholder="Facoltativo: link ufficiali che conosci già (uno per riga). Se la ricerca non trova nulla, incollali qui." className="field font-mono" />
      <div className="flex flex-wrap items-center gap-3">
        <button onClick={lookup} disabled={running || name.trim().length < 3} className="btn-primary flex items-center gap-2">
          {running && <Loader2 className="w-3.5 h-3.5 animate-spin" />}{running ? 'Ricerca in corso…' : 'Cerca'}
        </button>
        {phase === 'done' && <span className="text-xs text-emerald-700">Fatto: il bando è in memoria.</span>}
      </div>
      {error && <div className="p-3 rounded-xl border border-red-500/30 text-red-700 text-xs leading-relaxed">{error}</div>}

      {phase === 'matches' && matches?.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-line">
          <p className="label">Ho trovato questi bandi già in memoria. È uno di questi?</p>
          <ul className="space-y-1.5">
            {matches.map((m) => (
              <li key={m.bando_id} className="flex flex-wrap items-center gap-2 text-xs p-2 rounded-xl border border-line bg-field">
                <span className="font-medium text-ink">{m.name}</span>
                {m.issuer && <span className="text-mute">{m.issuer}</span>}
                <span className="text-mute">{m.rules} regole · {m.requirements} requisiti · {m.sources} documenti</span>
                {m.cache_hit && <span className="px-1.5 rounded border text-[10px] text-emerald-700 border-emerald-500/30">regole già in memoria</span>}
                {m.catalog_only && <span className="px-1.5 rounded border text-[10px] text-sky-700 border-sky-500/30">nel catalogo nazionale: regole da leggere</span>}
                {m.deadline && m.deadline !== 'non indicata' && <span className="text-mute">scadenza {m.deadline}</span>}
                <button onClick={() => { internalRef.current = m.bando_id; if (m.source_url) setUrls((u) => u || m.source_url); confirmBando({ name: m.name, bando_id: m.bando_id }, false) }} className="btn-primary !py-1 ml-auto">Sì, è questo</button>
              </li>
            ))}
          </ul>
          <button onClick={() => webSearch()} className="btn">Nessuno di questi: cerca sul web</button>
        </div>
      )}

      {phase === 'cached' && confirmInfo && (
        <div className="p-3 rounded-xl border border-emerald-500/30 bg-emerald-500/5 text-xs text-ink-2 space-y-2">
          <p className="flex items-center gap-1.5 text-emerald-700 font-medium"><CheckCircle2 className="w-4 h-4" />Le regole di questo bando sono già in memoria: le uso senza riscaricare nulla.</p>
          <p>{confirmInfo.sources} documenti · già richiesto da {confirmInfo.requested_by_clients_count} {confirmInfo.requested_by_clients_count === 1 ? 'cliente' : 'clienti'}.</p>
          <button onClick={() => { setForce(true); webSearch() }} className="btn">Aggiorna dal web</button>
        </div>
      )}

      {phase === 'pick' && search && (
        <div className="space-y-2 pt-2 border-t border-line">
          <p className="label">Ho trovato queste pagine sul web. Scegli quelle giuste e conferma che è il bando che cerchi.</p>
          <ul className="space-y-1.5">
            {search.candidates.slice(0, 12).map((c) => (
              <li key={c.url} className="flex flex-wrap items-center gap-2 text-xs">
                <input type="checkbox" className="accent-brand" checked={picked.has(c.url)} onChange={() => setPicked((p) => { const n = new Set(p); if (n.has(c.url)) n.delete(c.url); else n.add(c.url); return n })} aria-label={c.title} />
                <span className={`px-1.5 rounded border text-[10px] ${TIER_STYLE[c.tier]}`}>{TIER_LABEL[c.tier]}</span>
                <a href={c.url} target="_blank" rel="noreferrer" className="text-ink hover:underline truncate max-w-[60vw] md:max-w-lg inline-flex items-center gap-1">{c.title}<ExternalLink className="w-3 h-3 shrink-0" /></a>
              </li>
            ))}
          </ul>
          <button onClick={() => confirmBando({ name: name.trim(), bando_id: internalRef.current || undefined }, true)} disabled={!picked.size} className="btn-primary">Sì, è questo bando: scarica e leggi</button>
        </div>
      )}

      {['fetch', 'analyze', 'done'].includes(phase) && (
        <div className="space-y-4 pt-2 border-t border-line">
          <Step n={1} state={search ? 'done' : 'todo'} title="Ho cercato sul web e confermato il bando">
            {search && <p>{search.candidates.length} risultati pertinenti ({search.candidates.filter((c) => c.tier === 'UFFICIALE').length} ufficiali) da {search.queries.length} ricerche.</p>}
          </Step>

          <Step n={2} state={phase === 'fetch' ? 'run' : ['analyze', 'done'].includes(phase) ? 'done' : phase === 'error' && docs.length ? 'fail' : 'todo'} title={`Scarico i documenti${docs.length ? ` (${okDocs.length} salvati)` : ''}`}>
            <ul className="space-y-1">
              {docs.map((d) => (
                <li key={d.key} className="flex flex-wrap items-center gap-x-2 gap-y-0.5" style={{ paddingLeft: d.depth * 12 }}>
                  {d.status === 'run' ? <Loader2 className="w-3 h-3 animate-spin text-brand-ink shrink-0" /> : d.status === 'ok' ? <CheckCircle2 className="w-3 h-3 text-emerald-700 shrink-0" /> : <XCircle className="w-3 h-3 text-red-700 shrink-0" />}
                  <a href={d.url} target="_blank" rel="noreferrer" className="text-ink hover:underline truncate max-w-[60vw] md:max-w-md inline-flex items-center gap-1">{d.title || d.url}<ExternalLink className="w-3 h-3 shrink-0" /></a>
                  {d.tier && <span className={`px-1.5 rounded border text-[10px] ${TIER_STYLE[d.tier]}`}>{TIER_LABEL[d.tier]}</span>}
                  {d.status === 'ok' && <span className="text-mute">{d.kind}{d.pages ? ` · ${d.pages} pag.` : ''} · {d.chars.toLocaleString('it-IT')} caratteri</span>}
                  {d.status === 'error' && <span className="text-red-700">{d.message}</span>}
                  {d.warnings?.map((w) => <span key={w} className="text-amber-700 flex items-center gap-1"><AlertTriangle className="w-3 h-3" />{w}</span>)}
                </li>
              ))}
            </ul>
          </Step>

          <Step n={3} state={phase === 'analyze' ? 'run' : phase === 'done' ? 'done' : 'todo'} title="Leggo tutto e capisco cosa chiede il bando">
            {result && (
              <p><strong className="text-ink">{result.requirements_total}</strong> requisiti letti, <strong className="text-ink">{Object.keys(result.rules_published).length}</strong> regole numeriche
                pubblicate, <strong className="text-ink">{result.legal_refs.length}</strong> atti di legge citati, da {result.sources} documenti.</p>
            )}
            {result?.warning && <p className="text-amber-700 flex items-start gap-1.5"><AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />{result.warning}</p>}
            {result?.sources_report?.filter((x) => !x.requirements).map((x) => (
              <p key={x.sha256} className="text-amber-700">Da «{x.name.slice(0, 60)}» non ho ricavato requisiti: {x.note}.</p>
            ))}
          </Step>
        </div>
      )}

      {phase === 'done' && notFetched.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-line">
          <p className="label">Altre pagine trovate ma non scaricate <span className="text-mute">(di solito blog e portali: utili per capire, ma non sono la fonte ufficiale)</span></p>
          <ul className="space-y-1.5">
            {notFetched.slice(0, 8).map((c) => (
              <li key={c.url} className="flex flex-wrap items-center gap-2 text-xs">
                <span className={`px-1.5 rounded border text-[10px] ${TIER_STYLE[c.tier]}`}>{TIER_LABEL[c.tier]}</span>
                <a href={c.url} target="_blank" rel="noreferrer" className="text-ink-2 hover:underline truncate max-w-[55vw] md:max-w-lg">{c.title}</a>
                <button onClick={() => addCandidate(c)} disabled={busyExtra !== null} className="btn !py-1 ml-auto">{busyExtra === c.url ? <Loader2 className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}Aggiungi</button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="pt-2 border-t border-line space-y-3">
        <div className="flex items-center gap-2">
        <button type="button" onClick={() => setManual({ ...manual, open: !manual.open })} className="text-xs text-ink-2 hover:text-ink inline-flex items-center gap-1.5"><FileUp className="w-3.5 h-3.5" />Aggiungi un documento a mano (PDF o testo)</button>
          <Hint id="bando_upload" />
        </div>
        {manual.open && (
          <div className="space-y-3">
            <input type="file" accept=".pdf,.txt,.md" onChange={(e) => setManual({ ...manual, file: e.target.files?.[0] || null })} className="text-xs text-ink-2 file:mr-3 file:rounded-lg file:border-0 file:bg-tint-2 file:px-3 file:py-2 file:text-xs file:text-ink" />
            {!manual.file && <textarea value={manual.text} onChange={(e) => setManual({ ...manual, text: e.target.value })} rows={4} placeholder="…oppure incolla qui un testo (almeno 100 caratteri)" className="field font-mono" />}
            <button onClick={addManual} disabled={busyExtra !== null || name.trim().length < 3 || (!manual.file && manual.text.trim().length < 100)} className="btn-primary flex items-center gap-2">
              {busyExtra === 'manual' && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Aggiungi e rileggi tutto
            </button>
            {name.trim().length < 3 && <p className="text-xs text-mute">Scrivi prima il nome del bando in alto.</p>}
          </div>
        )}
      </div>
    </div>
  )
}
