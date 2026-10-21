import React, { useCallback, useEffect, useState } from 'react'
import { Loader2, X } from 'lucide-react'
import { api } from '../lib/api'

const KIND = { WELCOME: 'Benvenuto', MONTHLY: 'Token del mese', SPEND: 'Speso', REFUND: 'Restituiti', GRANT: 'Regalo', TOPUP: 'Ricarica' }
const eur = (n) => Number(n).toLocaleString('it-IT', { style: 'currency', currency: 'EUR', minimumFractionDigits: 0 })

/** Il saldo dei token si rilegge quando succede qualcosa che lo cambia (consegna, studio, ricarica) e quando si torna sulla pagina. */
export function useTokens() {
  const [t, setT] = useState(null)
  const load = useCallback(() => api.tokens().then(setT).catch(() => {}), [])
  useEffect(() => {
    load()
    window.addEventListener('quanto-tokens-changed', load)
    window.addEventListener('focus', load)
    return () => { window.removeEventListener('quanto-tokens-changed', load); window.removeEventListener('focus', load) }
  }, [load])
  return [t, load]
}

/** Cosa si può fare coi token, in tre righe: serve a capire subito dove si spende e dove no. */
function Rules({ t }) {
  const c = Object.fromEntries(t.costs.map((x) => [x.op, x.cost]))
  return (
    <ul className="space-y-1.5 text-sm text-ink-2">
      <li><span className="font-medium text-ink">Lavorare è libero.</span> Profilo, documenti, stima, allocazione, controllo del budget mentre lo scrivi, assistente, Confronto e Verifica non costano nulla.</li>
      <li><span className="font-medium text-ink">{c.deliver} token per consegnare un budget</span> (esportarlo o registrarlo). Vale 30 giorni per lo stesso budget: altre esportazioni e modifiche non costano di più.</li>
      <li><span className="font-medium text-ink">{c.study_new} token per studiare un bando nuovo</span>, e 1 torna indietro se la lettura è completa. Un bando già in memoria è gratis.</li>
    </ul>
  )
}

function Packs({ t, onRequested }) {
  const [busy, setBusy] = useState(null)
  const [done, setDone] = useState(null)
  const [error, setError] = useState(null)
  const ask = async (id) => {
    setBusy(id); setError(null)
    try { const r = await api.topupRequest(id); setDone(r.message); onRequested?.() } catch (e) { setError(e.message) } finally { setBusy(null) }
  }
  return (
    <div className="space-y-3">
      <div className="grid sm:grid-cols-3 gap-3">
        {t.packs.map((p) => (
          <div key={p.id} className="rounded-2xl bg-tint p-4 space-y-1">
            <p className="text-2xl font-semibold tabular-nums tracking-tight">{p.tokens}<span className="text-sm font-normal text-mute"> token</span></p>
            <p className="text-sm text-ink">{eur(p.price_eur)}</p>
            <p className="text-[11px] text-mute">{p.note}</p>
            <button className="btn !mt-2" disabled={!!busy} onClick={() => ask(p.id)}>{busy === p.id && <Loader2 className="w-3 h-3 animate-spin" />}Richiedi</button>
          </div>
        ))}
      </div>
      {done && <p className="text-xs text-emerald-700">{done}</p>}
      {error && <p className="text-xs text-red-700">{error}</p>}
      {!t.payments_active && !done && <p className="text-[11px] text-mute">Il pagamento online non è ancora attivo: la richiesta arriva al titolare, che ti accredita i token.</p>}
    </div>
  )
}

/** La scheda completa: saldo, da dove vengono i token, regole, ricariche e ultimi movimenti. Sta in Profilo → Piano e dati. */
export function TokenCard() {
  const [t, load] = useTokens()
  const [log, setLog] = useState(false)
  if (!t) return <div className="card p-6 text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Carico i token…</div>
  return (
    <div className="card p-6 space-y-6">
      <div className="flex flex-wrap items-end gap-x-10 gap-y-3">
        <div>
          <p className="label">Token dello studio</p>
          <p className={`text-5xl font-semibold tracking-tight tabular-nums ${t.empty ? 'text-red-700' : t.low ? 'text-amber-700' : 'text-ink'}`}>{t.exempt ? '∞' : t.balance}</p>
        </div>
        {!t.exempt && (
          <div className="text-sm text-ink-2 space-y-0.5 pb-1">
            <p>{t.included} del mese (se ne usi meno, ne restano fino a {t.cap}) · {t.extra} che non scadono</p>
            <p className="text-mute">Prossimi {t.monthly} il {new Date(t.next_grant).toLocaleDateString('it-IT', { day: 'numeric', month: 'long' })} · spesi negli ultimi 30 giorni: {t.spent_30_days}</p>
          </div>
        )}
        {t.exempt && <p className="text-sm text-ink-2 pb-1">Account del titolare: non consuma token.</p>}
      </div>
      {t.balance < 0 && <p className="text-sm text-amber-700">Stai usando l’anticipo di cortesia ({t.balance}): il prossimo accredito lo ripiana.</p>}
      <Rules t={t} />
      {!t.exempt && <div className="space-y-2"><p className="text-sm font-medium text-ink">Ricarica</p><Packs t={t} onRequested={load} /></div>}
      <div>
        <button className="text-xs underline text-ink-2" onClick={() => setLog(!log)}>{log ? 'Nascondi i movimenti' : 'Mostra gli ultimi movimenti'}</button>
        {log && (
          <ul className="mt-2 space-y-1 text-xs">
            {t.ledger.length === 0 && <li className="text-mute">Nessun movimento.</li>}
            {t.ledger.map((r) => (
              <li key={r.id} className="flex gap-3 border-b border-line pb-1 last:border-0"><span className="text-mute w-28 shrink-0">{r.ts.slice(0, 10).split('-').reverse().join('/')}</span>
                <span className="text-ink-2 flex-1">{KIND[r.kind] || r.kind}{r.note ? ` · ${r.note}` : ''}{r.ref && r.kind === 'SPEND' ? ` · ${r.ref.split('|').slice(1).join(' · ')}` : ''}</span>
                <span className={`tabular-nums font-medium ${r.amount < 0 ? 'text-ink' : 'text-emerald-700'}`}>{r.amount > 0 ? '+' : ''}{r.amount}</span></li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

/** Compare quando serve un'operazione che i token non coprono: dice cosa manca e permette di ricaricare, senza perdere il lavoro. */
export function TokensModal() {
  const [info, setInfo] = useState(null)
  const [t, load] = useTokens()
  useEffect(() => {
    const on = (e) => { setInfo(e.detail || {}); load() }
    window.addEventListener('quanto-tokens-needed', on)
    return () => window.removeEventListener('quanto-tokens-needed', on)
  }, [load])
  if (!info) return null
  return (
    <div className="fixed inset-0 z-[90] bg-black/40 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label="Token esauriti" onClick={() => setInfo(null)}>
      <div className="bg-white rounded-3xl w-full max-w-xl p-6 md:p-8 space-y-5 shadow-2xl max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start gap-3">
          <div className="min-w-0 flex-1"><h3 className="text-xl font-semibold tracking-tight">Servono più token</h3><p className="text-sm text-ink-2 mt-1">{info.message || `Servono ${info.needed} token e ne hai ${info.balance}.`}</p></div>
          <button className="rounded-full bg-tint hover:bg-tint-2 p-1.5" onClick={() => setInfo(null)} aria-label="Chiudi"><X className="w-4 h-4" /></button>
        </div>
        {t && <Rules t={t} />}
        {t && <Packs t={t} onRequested={load} />}
        <button className="btn-primary" onClick={() => setInfo(null)}>Ho capito</button>
      </div>
    </div>
  )
}
