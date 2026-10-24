import React, { useCallback, useEffect, useState } from 'react'
import { ExternalLink, Loader2, Radar } from 'lucide-react'
import { api } from '../lib/api'
import { fmtTs } from '../lib/format'
import { Fold, Info } from './ui'

const STATUS = {
  COPERTA: ['Nel catalogo', 'border-emerald-500/30 text-emerald-700'],
  LETTA: ['Letta', 'border-emerald-500/30 text-emerald-700'],
  DA_CONTROLLARE: ['Da controllare', 'border-line-strong text-ink-2'],
  NON_RAGGIUNGIBILE: ['Non raggiungibile', 'border-red-500/30 text-red-700'],
  SOLO_JAVASCRIPT: ['Solo JavaScript', 'border-amber-500/30 text-amber-700'],
  NESSUN_BANDO_TROVATO: ['Nessun bando trovato', 'border-amber-500/30 text-amber-700'],
}
const STATUS_HELP = {
  COPERTA: 'Le voci di questo sito entrano ogni notte dalla sua mappa del sito.',
  LETTA: 'Ho letto la pagina e ne ho ricavato i bandi elencati qui a destra.',
  DA_CONTROLLARE: 'Non l’ho ancora controllata: premi «Cerca nuovi bandi adesso».',
  NON_RAGGIUNGIBILE: 'Il sito non ha risposto da qui (spento, certificato non valido o blocca i programmi). Lo riprovo ad ogni controllo.',
  SOLO_JAVASCRIPT: 'La pagina costruisce l’elenco con JavaScript: un programma che legge solo il testo non lo vede. Serve la sua interfaccia dati o l’inserimento a mano.',
  NESSUN_BANDO_TROVATO: 'Il sito risponde ma in questo momento non elenca collegamenti che sembrino bandi per le imprese.',
}
const LEVEL_ORDER = ['NAZIONALE', 'AGENZIA', 'REGIONE', 'CAMERE', 'UE']

/** Da dove arrivano i bandi: la strada dal sito ufficiale al piano, i numeri veri e lo stato di ogni fonte. Chiuso di base. */
export default function SourcesPanel() {
  const [open, setOpen] = useState(false)
  const [data, setData] = useState(null)
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback(() => api.sources().then(setData).catch((e) => setError(e.message)), [])
  useEffect(() => { load() }, [load])

  const refresh = async () => {
    setBusy(true); setError(null); setNote(null)
    try {
      const r = await api.sourcesRefresh()
      setNote(`Controllate ${r.checked} fonti ufficiali: ${r.reachable} rispondono, ${r.found} voci trovate, ${r.new} nuove nel catalogo.${r.skipped ? ` Altre ${r.skipped} al prossimo controllo.` : ''} Le schede nuove si leggono nelle prossime ore.`)
      await load()
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  const t = data?.totals
  const summary = t ? `${t.sources} fonti ufficiali · ${t.catalog.toLocaleString('it-IT')} bandi in memoria · ${t.read.toLocaleString('it-IT')} con scheda letta · ${t.studied} studiati a fondo` : 'Fonti ufficiali, numeri e stato di lettura'
  const groups = LEVEL_ORDER.map((lv) => [lv, (data?.sources || []).filter((s) => s.level === lv)]).filter(([, l]) => l.length)

  return (
    <Fold id="fold-fonti" title="Da dove arrivano i bandi" summary={summary} open={open} onToggle={() => setOpen(!open)}>
      {error && <p className="text-xs text-red-700">{error}</p>}
      {!data && !error && <p className="text-xs text-mute inline-flex items-center gap-1.5"><Loader2 className="w-3.5 h-3.5 animate-spin" />Carico…</p>}
      {data && (
        <div className="space-y-5">
          <ol className="grid md:grid-cols-3 gap-3 text-xs text-ink-2 leading-relaxed">
            <li className="rounded-xl bg-field border border-line p-3 space-y-1"><p className="font-semibold text-ink text-sm">1 · Elenco</p><p><strong className="text-ink tabular-nums">{t.catalog.toLocaleString('it-IT')}</strong> bandi di cui conosco nome, ente e indirizzo ufficiale. Arrivano ogni notte dalle mappe di incentivi.gov.it e Invitalia e dalle pagine di ministeri, Regioni e agenzie.</p></li>
            <li className="rounded-xl bg-field border border-line p-3 space-y-1"><p className="font-semibold text-ink text-sm">2 · Scheda letta in breve</p><p><strong className="text-ink tabular-nums">{t.read.toLocaleString('it-IT')}</strong> con la scheda letta (chi può partecipare, spese ammesse, regione, date); {t.unread.toLocaleString('it-IT')} da leggere: se ne leggono alcune centinaia a notte.</p></li>
            <li className="rounded-xl bg-field border border-line p-3 space-y-1"><p className="font-semibold text-ink text-sm">3 · Studio a fondo</p><p><strong className="text-ink tabular-nums">{t.studied}</strong> studiati: regole, requisiti, importi e documenti di domanda. Si studia un bando quando serve a un cliente; dall’Allocazione si studiano in fila tutti i più affini.</p></li>
          </ol>
          <Info label="Perché gli studiati sono pochi">
            <p>Studiare un bando significa scaricare e leggere per intero i suoi documenti ufficiali (bando, allegati, FAQ): dura circa un minuto e dà regole e importi veri. Leggere la scheda è molto più veloce ma dice solo se il bando somiglia all’azienda.</p>
            <p>Per questo l’Allocazione parte da tutti i bandi letti, mostra un tetto provvisorio ricavato dalle cifre della scheda e li studia a fondo in fila: solo allora entrano nel piano con importi veri.</p>
          </Info>
          <div className="flex flex-wrap items-center gap-3">
            <button className="btn-primary" onClick={refresh} disabled={busy}>{busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Radar className="w-3.5 h-3.5" />}{busy ? 'Controllo le fonti…' : 'Cerca nuovi bandi adesso'}</button>
            <span className="text-xs text-mute">{t.checked} di {t.sources} fonti controllate almeno una volta · {t.reading} leggibili</span>
          </div>
          {note && <p className="text-xs text-emerald-700 leading-relaxed">{note}</p>}
          <div className="space-y-2">
            {groups.map(([lv, list]) => (
              <details key={lv} className="rounded-xl border border-line bg-white">
                <summary className="cursor-pointer select-none px-4 py-2.5 text-sm font-medium text-ink flex flex-wrap items-center gap-2">
                  {data.levels[lv]}
                  <span className="text-xs font-normal text-mute">{list.length} {list.length === 1 ? 'fonte' : 'fonti'} · {list.reduce((a, s) => a + s.in_catalog, 0).toLocaleString('it-IT')} bandi</span>
                </summary>
                <ul className="divide-y divide-line">
                  {list.map((s) => {
                    const [label, tone] = STATUS[s.status] || STATUS.DA_CONTROLLARE
                    return (
                      <li key={s.id} className="px-4 py-2.5 text-xs space-y-0.5">
                        <div className="flex flex-wrap items-center gap-2">
                          <a href={s.home} target="_blank" rel="noreferrer" className="font-medium text-ink hover:underline inline-flex items-center gap-1 min-w-0">{s.name}<ExternalLink className="w-3 h-3 shrink-0 text-mute" /></a>
                          <span title={STATUS_HELP[s.status]} className={`px-1.5 py-0.5 rounded border text-[11px] ${tone}`}>{label}</span>
                          <span className="text-mute ml-auto">{s.in_catalog > 0 ? `${s.in_catalog.toLocaleString('it-IT')} in catalogo` : ''}{s.studied ? ` · ${s.studied} studiati` : ''}{s.checked_at ? ` · controllata ${fmtTs(s.checked_at)}` : ''}</span>
                        </div>
                        {(s.topic || s.note) && <p className="text-mute">{[s.topic, s.note].filter(Boolean).join(' · ')}</p>}
                        {s.status !== 'COPERTA' && s.status !== 'LETTA' && s.status !== 'DA_CONTROLLARE' && <p className="text-amber-700">{STATUS_HELP[s.status]}</p>}
                      </li>
                    )
                  })}
                </ul>
              </details>
            ))}
          </div>
          <p className="text-[11px] text-mute leading-relaxed">Le fonti sono siti istituzionali; di ogni voce QUANTO tiene il nome esatto del collegamento e l’indirizzo ufficiale. Date, importi e requisiti si leggono solo dalla pagina o dal documento del bando, mai dal nome.</p>
        </div>
      )}
    </Fold>
  )
}
