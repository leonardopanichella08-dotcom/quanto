import React, { useEffect, useRef, useState } from 'react'
import { ChevronLeft, ChevronRight, ExternalLink, Layers, Loader2, Search, Sparkles } from 'lucide-react'
import { api } from '../lib/api'
import { Hint } from './Help'

const PAGE_SIZE = 20

/** Sfoglia TUTTI i bandi in memoria: i curati (già nell'elenco a sinistra) e le migliaia di voci del catalogo
 * nazionale (solo nome, ente, link ufficiale — non ancora lette). Da qui si sceglie quale far analizzare per intero. */
export default function CatalogBrowser({ onPick, picking }) {
  const [open, setOpen] = useState(false)
  const [q, setQ] = useState('')
  const [issuer, setIssuer] = useState('')
  const [onlyNew, setOnlyNew] = useState(true)
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [issuers, setIssuers] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const debounce = useRef(null)

  useEffect(() => { if (open && !issuers.length) api.bandiCatalogIssuers().then(setIssuers).catch(() => {}) }, [open, issuers.length])

  useEffect(() => {
    if (!open) return
    setLoading(true); setError(null)
    clearTimeout(debounce.current)
    debounce.current = setTimeout(() => {
      api.bandiCatalog({ q, issuer, onlyNew, page, pageSize: PAGE_SIZE })
        .then(setData).catch((e) => setError(e.message)).finally(() => setLoading(false))
    }, q ? 350 : 0)
    return () => clearTimeout(debounce.current)
  }, [open, q, issuer, onlyNew, page])

  if (!open) {
    return (
      <button onClick={() => setOpen(true)} className="btn flex items-center gap-2 w-full justify-center">
        <Layers className="w-4 h-4" />Sfoglia tutti i bandi in memoria (il catalogo nazionale, migliaia di voci)
      </button>
    )
  }

  const items = data?.items || []
  const pages = data?.pages || 1
  const total = data?.total || 0

  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="font-semibold text-base flex items-center gap-2"><Layers className="w-4 h-4 text-brand-ink" />Catalogo nazionale dei bandi <Hint id="bando_catalogo" /></h3>
          <p className="text-xs text-ink-2 leading-relaxed max-w-2xl mt-1">
            Ogni notte QUANTO scarica da solo l'elenco di tutti i bandi nazionali, regionali e comunali (incentivi.gov.it, Invitalia):
            {total > 0 && <> oggi ne ha in memoria <strong className="text-ink">{total.toLocaleString('it-IT')}</strong>.</>} Per la maggior parte
            si conosce solo nome, ente e link ufficiale: non sono ancora stati letti. Cercane uno e chiedi a QUANTO di analizzarlo per intero.
          </p>
        </div>
        <button onClick={() => setOpen(false)} className="text-xs text-ink-2 hover:text-ink shrink-0">Chiudi</button>
      </div>

      <div className="grid md:grid-cols-[1fr,auto,auto] gap-2">
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-mute absolute left-3 top-1/2 -translate-y-1/2" />
          <input value={q} onChange={(e) => { setQ(e.target.value); setPage(1) }} placeholder="Cerca per nome (es. Resto al Sud, voucher digitale, Puglia…)"
            className="field !pl-8" aria-label="Cerca nel catalogo" />
        </div>
        <select value={issuer} onChange={(e) => { setIssuer(e.target.value); setPage(1) }} className="field" aria-label="Filtra per ente">
          <option value="">Tutti gli enti</option>
          {issuers.map((i) => <option key={i} value={i}>{i}</option>)}
        </select>
        <label className="flex items-center gap-1.5 text-xs text-ink-2 whitespace-nowrap px-1">
          <input type="checkbox" className="accent-brand" checked={onlyNew} onChange={(e) => { setOnlyNew(e.target.checked); setPage(1) }} />
          solo non ancora analizzati
        </label>
      </div>

      {error && <div className="p-3 rounded-xl border border-red-500/30 text-red-700 text-xs">{error}</div>}

      <div className="space-y-1.5 min-h-[100px]">
        {loading && <div className="flex items-center justify-center py-8 text-ink-2"><Loader2 className="w-5 h-5 animate-spin" /></div>}
        {!loading && items.length === 0 && <p className="text-xs text-mute text-center py-8">Nessun bando trovato con questi filtri.</p>}
        {!loading && items.map((it) => (
          <div key={it.bando_id} className="flex flex-wrap items-center gap-x-3 gap-y-1 p-2.5 rounded-xl border border-line bg-field text-xs">
            <span className="font-medium text-ink min-w-0 truncate max-w-[38vw] md:max-w-md" title={it.name}>{it.name}</span>
            <span className="text-mute truncate max-w-[20vw]">{it.issuer}</span>
            {it.source_url && <a href={it.source_url} target="_blank" rel="noreferrer" className="text-sky-700 hover:underline inline-flex items-center gap-1 shrink-0"><ExternalLink className="w-3 h-3" /></a>}
            {it.curated ? <span className="px-1.5 py-0.5 rounded border border-emerald-500/30 text-emerald-700 text-[10px] shrink-0">già nella libreria</span>
              : (it.rules || it.sources) ? <span className="px-1.5 py-0.5 rounded border border-sky-500/30 text-sky-700 text-[10px] shrink-0">già cercato: {it.rules} regole</span>
                : <span className="px-1.5 py-0.5 rounded border border-line-strong text-mute text-[10px] shrink-0">da analizzare</span>}
            {!it.curated && !(it.rules || it.sources) && (
              <button onClick={() => onPick({ name: it.name, bando_id: it.bando_id, source_url: it.source_url })} disabled={picking === it.bando_id}
                className="btn-primary !py-1 !px-2.5 ml-auto shrink-0 flex items-center gap-1.5">
                {picking === it.bando_id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />}Analizza questo bando
              </button>
            )}
          </div>
        ))}
      </div>

      {pages > 1 && (
        <div className="flex items-center justify-center gap-3 text-xs text-ink-2 pt-1">
          <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1 || loading} className="btn !p-1.5"><ChevronLeft className="w-3.5 h-3.5" /></button>
          <span>pagina {page} di {pages.toLocaleString('it-IT')} · {total.toLocaleString('it-IT')} bandi</span>
          <button onClick={() => setPage((p) => Math.min(pages, p + 1))} disabled={page >= pages || loading} className="btn !p-1.5"><ChevronRight className="w-3.5 h-3.5" /></button>
        </div>
      )}
    </div>
  )
}
