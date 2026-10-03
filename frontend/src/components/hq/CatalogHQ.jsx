import React, { useCallback, useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight, ExternalLink, Loader2, RefreshCw, Search } from 'lucide-react'
import { api } from '../../lib/api'
import { fmtTs } from '../../lib/format'

const PAGE = 20
const FIELDS = [['purpose', 'Obiettivo'], ['form', 'Forma di agevolazione'], ['costs', 'Costi ammessi'], ['spend_range', 'Spesa ammessa'], ['benefit_range', 'Agevolazione concedibile'],
  ['applicant_type', 'Chi può chiederlo'], ['sizes', 'Dimensione'], ['sectors', 'Settori'], ['ateco', 'ATECO'], ['regions', 'Regioni'], ['municipalities', 'Comuni'],
  ['special_areas', 'Aree speciali'], ['tags', 'Altre caratteristiche'], ['manager', 'Soggetto gestore'], ['opens', 'Apertura'], ['closes', 'Chiusura']]

function Stat({ label, value, note }) {
  return <div className="card p-4"><span className="label">{label}</span><div className="text-2xl font-bold font-mono mt-1">{value}</div>{note && <p className="text-xs text-mute mt-1">{note}</p>}</div>
}

/** Quartier Generale: tutte le voci del catalogo nazionale con la descrizione e le caratteristiche lette dalla scheda ufficiale. */
export default function CatalogHQ() {
  const [stats, setStats] = useState(null)
  const [q, setQ] = useState('')
  const [described, setDescribed] = useState('')          // '' tutte · 'yes' lette · 'no' da leggere
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [open, setOpen] = useState(null)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState(null)
  const [error, setError] = useState(null)

  const loadStats = useCallback(() => api.bandiCatalogStats().then(setStats).catch((e) => setError(e.message)), [])
  const load = useCallback(() => {
    setData(null)
    api.bandiCatalog({ q, page, pageSize: PAGE, described: described === '' ? null : described === 'yes', withMeta: true }).then(setData).catch((e) => setError(e.message))
  }, [q, page, described])
  useEffect(() => { loadStats() }, [loadStats])
  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t) }, [load])

  const describe = async () => {
    setBusy(true); setError(null); setMsg(null)
    try {
      let read = 0, deleted = 0, errors = 0, remaining = 1
      for (let round = 0; round < 40 && remaining > 0; round += 1) {      // un gruppo alla volta, finché non resta nulla da leggere
        const r = await api.catalogDescribe(400)
        read += r.read; deleted += r.deleted || 0; errors += r.errors; remaining = r.remaining
        setMsg(`Lette ${read} schede · ancora da leggere: ${remaining}${errors ? ` · ${errors} non raggiungibili` : ''}${deleted ? ` · ${deleted} voci chiuse eliminate` : ''}`)
        if (r.read === 0) break
      }
      loadStats(); load()
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <Stat label="Voci del catalogo" value={stats ? stats.total.toLocaleString('it-IT') : '…'} note="bandi e incentivi nazionali e locali" />
        <Stat label="Schede lette" value={stats ? stats.described.toLocaleString('it-IT') : '…'} note={stats?.last_read_at ? `ultima lettura ${fmtTs(stats.last_read_at)}` : 'nessuna ancora'} />
        <Stat label="Da leggere" value={stats ? stats.to_describe.toLocaleString('it-IT') : '…'} note="le legge il lavoro notturno, o il pulsante qui sotto" />
        <Stat label="Con scadenza futura" value={stats ? stats.open_dated.toLocaleString('it-IT') : '…'} note={stats ? `${stats.undated} senza data` : ''} />
        <Stat label="Già studiati" value={stats ? stats.studied : '…'} note="regole e requisiti letti" />
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button className="btn-primary" disabled={busy} onClick={describe}>{busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}Leggi le schede da leggere</button>
        {msg && <span className="text-xs text-emerald-700">{msg}</span>}
        {error && <span className="text-xs text-red-700">{error}</span>}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <label className="relative flex-1 min-w-[14rem]"><Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-mute" />
          <input className="field !pl-9" placeholder="Cerca per nome o ente…" value={q} onChange={(e) => { setQ(e.target.value); setPage(1) }} aria-label="Cerca nel catalogo" /></label>
        <select className="field !w-auto" value={described} onChange={(e) => { setDescribed(e.target.value); setPage(1) }} aria-label="Filtra per scheda letta">
          <option value="">Tutte le voci</option><option value="yes">Con scheda letta</option><option value="no">Da leggere</option></select>
      </div>

      <div className="space-y-2 min-h-[8rem]">
        {!data && <div className="flex justify-center py-8"><Loader2 className="w-5 h-5 animate-spin text-ink-2" /></div>}
        {data && data.items.length === 0 && <p className="text-xs text-mute text-center py-8">Nessuna voce con questi filtri.</p>}
        {data && data.items.map((it) => {
          const meta = it.meta || {}
          const isOpen = open === it.bando_id
          return (
            <div key={it.bando_id} className="card p-3 text-xs space-y-2">
              <button className="w-full text-left flex flex-wrap items-center gap-x-3 gap-y-1" onClick={() => setOpen(isOpen ? null : it.bando_id)} aria-expanded={isOpen}>
                <span className="font-medium text-ink text-sm min-w-0 flex-1 break-words">{it.name}</span>
                {meta.state && <span className="px-1.5 py-0.5 rounded border border-line-strong text-ink-2">{{ APERTO: 'aperto', CHIUSO: 'chiuso', IN_ARRIVO: 'in arrivo', SCONOSCIUTO: 'senza data' }[meta.state] || meta.state}</span>}
                {it.curated
                  ? <span className="px-1.5 py-0.5 rounded border border-emerald-500/30 text-emerald-700">bando della libreria</span>
                  : <span className={`px-1.5 py-0.5 rounded border ${it.read_at ? 'border-emerald-500/30 text-emerald-700' : 'border-amber-500/30 text-amber-700'}`}>{it.read_at ? 'scheda letta' : 'da leggere'}</span>}
                {it.rules > 0 && <span className="px-1.5 py-0.5 rounded border border-sky-500/30 text-sky-700">studiato · {it.rules} regole</span>}
              </button>
              {it.summary ? <p className="text-ink-2 leading-relaxed">{it.summary}</p>
                : <p className="text-mute">{it.curated ? 'Bando preparato a mano: regole, requisiti e fonti sono nella sezione Bandi.' : 'Descrizione non ancora letta dalla scheda ufficiale.'}</p>}
              {isOpen && (
                <div className="border-t border-line pt-2 space-y-1.5">
                  <p className="text-mute">Ente: {it.issuer || '—'} · scadenza {it.deadline || '—'} · id <span className="font-mono">{it.bando_id}</span>{it.read_at ? ` · letta il ${fmtTs(it.read_at)}` : ''}</p>
                  {FIELDS.map(([k, label]) => meta[k] && (
                    <p key={k} className="leading-relaxed"><span className="text-mute">{label} · </span>{Array.isArray(meta[k]) ? meta[k].join(' · ') : String(meta[k])}</p>))}
                  {meta.summary_source && <p className="text-mute">Origine della descrizione: {meta.summary_source}.</p>}
                  {it.source_url && <a href={it.source_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sky-700 hover:underline"><ExternalLink className="w-3 h-3" />Scheda ufficiale</a>}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {data && data.pages > 1 && (
        <div className="flex items-center justify-center gap-3 text-xs text-ink-2">
          <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1} className="btn !p-1.5" aria-label="Pagina precedente"><ChevronLeft className="w-3.5 h-3.5" /></button>
          <span>pagina {page} di {data.pages.toLocaleString('it-IT')} · {data.total.toLocaleString('it-IT')} voci</span>
          <button onClick={() => setPage((p) => Math.min(data.pages, p + 1))} disabled={page >= data.pages} className="btn !p-1.5" aria-label="Pagina successiva"><ChevronRight className="w-3.5 h-3.5" /></button>
        </div>
      )}
    </div>
  )
}
