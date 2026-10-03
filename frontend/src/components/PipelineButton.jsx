import React, { useState } from 'react'
import { AlertTriangle, CheckCircle2, Loader2, Radar } from 'lucide-react'
import { api } from '../lib/api'

const STATUS = {
  COMPLETA: ['Analisi completa', 'text-emerald-700 border-emerald-500/30 bg-emerald-500/5'],
  PARZIALE: ['Analisi parziale', 'text-amber-700 border-amber-500/30 bg-amber-500/5'],
  INSUFFICIENTE: ['Analisi insufficiente', 'text-red-700 border-red-500/30 bg-red-500/5'],
}
const KIND = { OBBLIGO: 'obblighi', DIVIETO: 'divieti', LIMITE: 'limiti', INFO: 'informazioni', DA_REVISIONARE: 'da rivedere' }

/** Il processo standard di studio di un bando: cerca, scarica, legge, valuta. Stesso percorso per ogni bando, con il rapporto di completezza. */
export default function PipelineButton({ bandoId, onDone, label = 'Studia il bando (cerca, scarica, leggi)' }) {
  const [busy, setBusy] = useState(false)
  const [report, setReport] = useState(null)
  const [error, setError] = useState(null)

  const go = async () => {
    setBusy(true); setError(null)
    try {
      const r = await api.researchRun({ bando_id: bandoId })
      setReport(r.report)
      if (onDone) await onDone(r)
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  const st = report && STATUS[report.status]
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        <button onClick={go} disabled={busy} className="btn-primary flex items-center gap-1.5">
          {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Radar className="w-3.5 h-3.5" />}{busy ? 'Studio in corso…' : label}
        </button>
        {busy && <span className="text-xs text-mute">Cerca le fonti ufficiali, le scarica e le legge: può richiedere fino a un minuto.</span>}
      </div>
      {error && <p className="text-xs text-red-700">{error}</p>}
      {report && (
        <div className={`p-3 rounded-xl border text-xs space-y-2 ${st[1]}`}>
          <p className="font-semibold flex items-center gap-1.5">
            {report.status === 'COMPLETA' ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}{st[0]}
          </p>
          <p className="text-ink-2 leading-relaxed">
            {report.documents_official} document{report.documents_official === 1 ? 'o ufficiale' : 'i ufficiali'} letti ({report.official_chars.toLocaleString('it-IT')} caratteri) ·{' '}
            <strong className="text-ink">{report.requirements}</strong> requisiti ({Object.entries(report.requirements_by_kind).map(([k, n]) => `${n} ${KIND[k] || k}`).join(', ') || 'nessuno'}) ·{' '}
            <strong className="text-ink">{report.figures}</strong> cifre (tetti, soglie, importi) · {report.rules_published} regole numeriche · {report.seconds} s
          </p>
          {report.gaps.length > 0 && (
            <ul className="list-disc pl-5 space-y-0.5 text-ink-2">{report.gaps.map((g) => <li key={g}>{g}</li>)}</ul>
          )}
        </div>
      )}
    </div>
  )
}
