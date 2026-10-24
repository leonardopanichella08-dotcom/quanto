import React, { useCallback, useEffect, useState } from 'react'
import { Download, ExternalLink, FileText, Loader2, RefreshCw } from 'lucide-react'
import { api, download } from '../lib/api'
import { Fold, Info } from './ui'

const KIND_TONE = { DOMANDA: 'border-emerald-500/30 text-emerald-700', FORMULARIO: 'border-sky-500/30 text-sky-700', ALLEGATO: 'border-line-strong text-ink-2', ISTRUZIONI: 'border-amber-500/30 text-amber-700', AVVISO: 'border-line-strong text-ink-2' }
const ITEM_ORDER = [['ALLEGATO', 'Documenti da presentare'], ['DOMANDA', 'Domande a cui rispondere'], ['CAMPO', 'Dati da inserire'], ['DICHIARAZIONE', 'Dichiarazioni da rendere']]
const fmtSize = (n) => (n == null ? '' : n > 1_000_000 ? `${(n / 1_000_000).toFixed(1).replace('.', ',')} MB` : `${Math.max(1, Math.round(n / 1000))} KB`)

/** I documenti pubblici per fare la domanda (modulo, formulario, allegati) e che cosa chiedono: documenti da presentare, domande, dati, dichiarazioni.
 *  Tutto ciò che compare è il testo dei documenti ufficiali: ogni voce dice da quale documento viene. */
export default function ApplicationDocs({ bandoId, auto = false }) {
  const [data, setData] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [open, setOpen] = useState({})
  const [dl, setDl] = useState(null)

  const collect = useCallback(async () => {
    setBusy(true); setError(null)
    try { const r = await api.bandoApplicationCollect(bandoId); setData(r.application) } catch (e) { setError(e.message) } finally { setBusy(false) }
  }, [bandoId])

  useEffect(() => {
    let alive = true
    setData(null); setError(null)
    api.bandoApplication(bandoId).then((d) => { if (!alive) return; setData(d); if (auto && !d.collected_at) collect() }).catch((e) => alive && setError(e.message))
    return () => { alive = false }
  }, [bandoId]) // eslint-disable-line react-hooks/exhaustive-deps

  const save = async (d) => {
    setDl(d.sha256)
    try { download(await api.bandoApplicationFile(bandoId, d.sha256), (d.url || d.title).split('/').pop().split('?')[0] || 'documento') } catch (e) { setError(e.message) } finally { setDl(null) }
  }

  if (error && !data) return <p className="text-xs text-red-700">{error}</p>
  if (!data) return <p className="text-xs text-mute inline-flex items-center gap-1.5"><Loader2 className="w-3.5 h-3.5 animate-spin" />Carico…</p>
  const t = data.totals || {}
  const total = Object.values(t).reduce((a, b) => a + b, 0)

  return (
    <div className="space-y-4">
      {!data.collected_at && !busy && (
        <div className="space-y-2">
          <p className="text-xs text-ink-2 leading-relaxed">Non ho ancora cercato i documenti per fare la domanda di questo bando. Li cerco sulla pagina ufficiale (modulo di domanda, formulario, allegati, dichiarazioni), li scarico e ti dico che cosa chiedono.</p>
          <button className="btn-primary" onClick={collect}><FileText className="w-3.5 h-3.5" />Cerca i documenti per la domanda</button>
        </div>
      )}
      {busy && <p className="text-xs text-ink-2 inline-flex items-center gap-1.5"><Loader2 className="w-3.5 h-3.5 animate-spin" />Cerco i moduli sul sito ufficiale e li scarico: può richiedere fino a 40 secondi.</p>}
      {error && <p className="text-xs text-red-700">{error}</p>}
      {data.collected_at && (
        <>
          {data.docs.length === 0 && <p className="text-xs text-amber-700 leading-relaxed">{data.note || 'Nessun documento di domanda trovato.'}</p>}
          {data.docs.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs text-ink-2">{data.docs.length} {data.docs.length === 1 ? 'documento ufficiale' : 'documenti ufficiali'} · {total} {total === 1 ? 'voce letta' : 'voci lette'}</p>
              <ul className="space-y-1.5">
                {data.docs.map((d) => (
                  <li key={d.sha256} className="rounded-xl bg-field border border-line px-3 py-2 text-xs space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`px-1.5 py-0.5 rounded border text-[11px] font-medium ${KIND_TONE[d.kind] || KIND_TONE.ALLEGATO}`}>{d.kind_label}</span>
                      <span className="font-medium text-ink break-words min-w-0 flex-1">{d.title}</span>
                      <span className="text-mute">{[d.format && d.format !== 'STUDIO' ? d.format : null, d.pages ? `${d.pages} pag.` : null, fmtSize(d.size_bytes)].filter(Boolean).join(' · ')}</span>
                    </div>
                    <div className="flex flex-wrap items-center gap-3">
                      {d.downloadable && <button className="inline-flex items-center gap-1 text-sky-700 hover:underline" onClick={() => save(d)} disabled={dl === d.sha256}>{dl === d.sha256 ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}Scarica il file</button>}
                      {d.url && <a href={d.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sky-700 hover:underline"><ExternalLink className="w-3 h-3" />Apri sul sito dell’ente</a>}
                    </div>
                    {d.warnings.map((w) => <p key={w} className="text-amber-700">{w}</p>)}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {ITEM_ORDER.map(([k, label]) => {
            const list = data.items[k]?.list || []
            if (!list.length) return null
            return (
              <Fold key={k} id={`appdoc-${bandoId}-${k}`} title={label} badge={String(list.length)} open={!!open[k]} onToggle={() => setOpen({ ...open, [k]: !open[k] })}>
                <ul className="space-y-1.5">
                  {list.map((x, i) => (
                    <li key={`${x.sha256}-${i}`} className="text-xs text-ink-2 leading-relaxed">
                      <span className="text-ink">{x.text}</span>
                      <span className="block text-[11px] text-mute truncate">dal documento: {x.doc}</span>
                    </li>
                  ))}
                </ul>
              </Fold>
            )
          })}
          <div className="flex flex-wrap items-center gap-3">
            <button className="btn" onClick={collect} disabled={busy}><RefreshCw className="w-3.5 h-3.5" />Cerca di nuovo i documenti</button>
            <Info label="Come leggo questi documenti">
              <p>Ogni voce è una riga scritta nel documento ufficiale, non un riassunto: QUANTO riconosce gli elenchi «alla domanda devono essere allegati…», le righe da compilare, i punti che iniziano con «Descrivere…» o «Indicare…» e le dichiarazioni da spuntare.</p>
              <p>I PDF scansionati e i vecchi .doc / .xls non si leggono qui, ma il file resta scaricabile. Molti enti pubblicano la domanda solo sulla piattaforma con accesso: in quel caso non ci sono documenti da scaricare. Prima di presentare controlla sempre il testo ufficiale.</p>
            </Info>
          </div>
        </>
      )}
    </div>
  )
}
