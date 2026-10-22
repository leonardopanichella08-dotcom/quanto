import React, { useEffect, useMemo, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { api } from '../lib/api'
import { fmtNum } from '../lib/format'
import { Fold, Info } from './ui'
import { publishGo, useNav } from '../lib/nav'

const BY_CATEGORY = { PERSONNEL: 'personnel_pct', CAPITAL_ASSETS: 'assets_pct', CONSULTING: 'consulting_pct', OVERHEAD: 'overhead_pct', TRAINING: 'training_pct' }
const LABEL = { personnel_pct: 'Personale', assets_pct: 'Beni strumentali', consulting_pct: 'Consulenze', research_pct: 'Ricerca e sviluppo', overhead_pct: 'Spese generali', training_pct: 'Formazione', communication_pct: 'Comunicazione', other_pct: 'Altro' }
const pct = (v) => `${fmtNum((v || 0) * 100, 1)}%`

/** Il budget controllato messo accanto a come lo hanno composto le aziende simili per lo stesso bando (motore collettivo): dove si scosta e di quanto. Si carica solo se lo apri. */
export default function PatternCompare({ validation, bando }) {
  const nav = useNav()
  const [open, setOpen] = useState(false)
  const [rec, setRec] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const shares = useMemo(() => {
    const tot = {}
    ;(validation?.items || []).forEach((i) => { const k = BY_CATEGORY[i.category]; if (k) tot[k] = (tot[k] || 0) + (i.computed_cost_eur || 0) })
    const sum = Object.values(tot).reduce((a, b) => a + b, 0)
    return sum ? Object.fromEntries(Object.entries(tot).map(([k, v]) => [k, v / sum])) : null
  }, [validation])
  useEffect(() => { setRec(null); setError(null) }, [validation?.merkle_root, bando?.bando_id])
  useEffect(() => {
    if (!open || rec || busy || !shares || !bando) return
    setBusy(true); setError(null)
    api.profile().catch(() => null).then((ov) => {
      const ateco = (ov?.fields || []).find((f) => f.key === 'ateco_code')?.value
      return api.templateRecommend({ ateco_code: ateco ? String(ateco) : undefined, bando_id: bando.bando_id, engine: 'COLLETTIVO', draft: shares })
    }).then(setRec).catch((e) => setError(e.message)).finally(() => setBusy(false))
  }, [open, rec, busy, shares, bando])
  if (!shares || !bando) return null
  const ok = rec?.status === 'OK'
  const summary = ok ? `${rec.comparison?.message?.split('.')[0] || 'Confronto pronto'}` : rec?.status === 'NO_DATA' ? 'Ancora pochi budget simili' : 'Il tuo budget accanto a quelli di aziende simili'
  return (
    <Fold id="fold-pattern" title="Come lo fanno aziende simili" summary={summary} open={open} onToggle={() => setOpen(!open)}>
      <div className="space-y-4 pt-3">
        {busy && <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Confronto…</p>}
        {error && <p className="text-xs text-red-700">{error}</p>}
        {rec?.status === 'NO_DATA' && <p className="text-sm text-ink-2 leading-relaxed">{rec.message}</p>}
        {ok && (
          <>
            <p className="text-sm text-ink-2 leading-relaxed">{rec.comparison?.message}</p>
            <table className="w-full text-xs">
              <thead><tr className="text-left text-mute"><th className="py-1 font-medium">Voce</th><th className="font-medium text-right">Il tuo</th><th className="font-medium text-right">Consigliato</th><th className="font-medium text-right">Scarto</th></tr></thead>
              <tbody>{Object.keys(LABEL).filter((k) => (shares[k] || 0) > 0 || (rec.recommended[k] || 0) > 0.005).map((k) => {
                const d = ((shares[k] || 0) - (rec.recommended[k] || 0)) * 100
                return <tr key={k} className="border-t border-line"><td className="py-1.5 text-ink-2">{LABEL[k]}</td><td className="text-right tabular-nums">{pct(shares[k])}</td><td className="text-right tabular-nums">{pct(rec.recommended[k])}</td>
                  <td className={`text-right tabular-nums ${Math.abs(d) >= 10 ? 'text-amber-700 font-medium' : 'text-mute'}`}>{d > 0 ? '+' : ''}{fmtNum(d, 1)}</td></tr>
              })}</tbody>
            </table>
            <p className="text-[11px] text-mute">Fiducia {rec.confidence.toLowerCase()} · {rec.real_templates} budget reali{rec.example_templates ? ` + ${rec.example_templates} esempi` : ''} · {rec.basis_label}. È una statistica sulla struttura della spesa, non una previsione di esito.</p>
          </>
        )}
        <div className="flex flex-wrap items-center gap-3">
          <button className="btn" onClick={() => { publishGo(); nav.go('pattern') }}>Pubblica il tuo budget per migliorare il consiglio</button>
          <Info label="Come funziona">Il confronto usa i budget pubblicati per tutti da altri studi (e gli esempi di partenza), per lo stesso bando e la stessa nicchia se ci sono, altrimenti per il settore. Più budget si pubblicano, più il consiglio è preciso.</Info>
        </div>
      </div>
    </Fold>
  )
}
