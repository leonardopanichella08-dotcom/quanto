import React, { useEffect, useState } from 'react'
import { AlertTriangle, CheckCircle2, Loader2, Radar } from 'lucide-react'
import { api } from '../lib/api'

const KIND = { OBBLIGO: 'obblighi', DIVIETO: 'divieti', LIMITE: 'limiti', INFO: 'informazioni', DA_REVISIONARE: 'da rivedere' }

/** L'esito dello studio detto come serve a chi lavora: cosa si può fare ora (budget, valore in euro) e, se manca qualcosa, perché. I numeri della lettura restano sotto, a richiesta. */
export function StudyResult({ study, report }) {
  const [more, setMore] = useState(false)
  if (!study) return null
  const good = study.budget_ready || study.has_rate || study.budget === false
  return (
    <div className={`p-3 rounded-xl border text-xs space-y-1.5 ${good ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-amber-500/30 bg-amber-500/5'}`}>
      <p className="text-ink leading-relaxed flex gap-1.5">{good ? <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" /> : <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600" />}<span>{study.verdict}</span></p>
      {report && (
        <>
          <button type="button" className="text-[11px] text-mute underline" onClick={() => setMore(!more)}>{more ? 'Nascondi i dettagli della lettura' : 'Dettagli della lettura'}</button>
          {more && (
            <div className="text-ink-2 space-y-1">
              <p>{report.documents_official} document{report.documents_official === 1 ? 'o ufficiale' : 'i ufficiali'} ({report.official_chars.toLocaleString('it-IT')} caratteri) · {report.requirements} requisiti ({Object.entries(report.requirements_by_kind).map(([k, n]) => `${n} ${KIND[k] || k}`).join(', ') || 'nessuno'}) · {report.figures} cifre · {report.rules_published} regole numeriche · {report.seconds} s</p>
              {report.gaps.length > 0 && <ul className="list-disc pl-5 space-y-0.5">{report.gaps.map((g) => <li key={g}>{g}</li>)}</ul>}
            </div>
          )}
        </>
      )}
    </div>
  )
}

/** Il processo standard di studio di un bando: cerca, scarica, legge, valuta. Stesso percorso per ogni bando; alla fine dice in una frase cosa si può fare. */
export default function PipelineButton({ bandoId, onDone, label = 'Studia il bando', hint }) {
  const [busy, setBusy] = useState(false)
  const [quote, setQuote] = useState(null)
  useEffect(() => { api.tokenQuote({ op: 'study', bando_id: bandoId }).then(setQuote).catch(() => {}) }, [bandoId])          // il costo lo dice il server: in fase di prova non c'è nulla da pagare
  const price = quote && !quote.free ? quote.cost : null
  const [res, setRes] = useState(null)
  const [error, setError] = useState(null)

  const go = async () => {
    setBusy(true); setError(null)
    try {
      const r = await api.researchRun({ bando_id: bandoId })
      setRes(r)
      if (onDone) await onDone(r)
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  return (
    <div className="space-y-3">
      {!res && (
        <div className="flex flex-wrap items-center gap-3">
          <button onClick={go} disabled={busy} className="btn-primary flex items-center gap-1.5">
            {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Radar className="w-3.5 h-3.5" />}{busy ? 'Studio in corso…' : label}{!busy && price != null && <span className="opacity-70 font-normal">· {price === 0 ? 'gratis' : `${price} token`}</span>}
          </button>
          {!busy && hint && <span className="text-xs text-mute max-w-sm leading-snug">{hint}</span>}
          {busy && <span className="text-xs text-mute">Cerco le fonti ufficiali, le scarico e le leggo: può richiedere fino a un minuto.</span>}
        </div>
      )}
      {error && <p className="text-xs text-red-700">{error}</p>}
      {res && <StudyResult study={res.study} report={res.report} />}
      {res?.study?.retry && !busy && <button type="button" className="btn !py-1" onClick={go}>Riprova la lettura</button>}
    </div>
  )
}
