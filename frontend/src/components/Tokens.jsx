import React, { useCallback, useEffect, useState } from 'react'
import { Loader2, Minus, Plus, X } from 'lucide-react'
import { api } from '../lib/api'

const KIND = { WELCOME: 'Benvenuto', MONTHLY: 'Token del mese', SPEND: 'Speso', REFUND: 'Restituiti', GRANT: 'Regalo', TOPUP: 'Ricarica' }
const eur = (n) => Number(n).toLocaleString('it-IT', { style: 'currency', currency: 'EUR', minimumFractionDigits: 0, useGrouping: 'always' })
/** I token hanno al massimo un decimale: 2,4 · 25 · 0,5 */
export const fmtTok = (n) => Number(n).toLocaleString('it-IT', { maximumFractionDigits: 1 })

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

/** Cosa si può fare coi token, in poche righe: serve a capire subito dove si spende, dove no e dove si guadagna. */
function Rules({ t }) {
  const c = Object.fromEntries(t.costs.map((x) => [x.op, x]))
  return (
    <ul className="space-y-1.5 text-sm text-ink-2">
      <li><span className="font-medium text-ink">Lavorare è libero.</span> Profilo, documenti, stima, bandi adatti, controllo del budget mentre lo scrivi, assistente, Confronto e Verifica non costano nulla.</li>
      <li><span className="font-medium text-ink">Piano di allocazione: da {fmtTok(c.allocate.cost)} a {fmtTok(c.allocate.max)} token</span>, secondo quanti dati analizza (righe del bilancio e bandi nel piano). Vale 30 giorni per lo stesso lavoro e anno.</li>
      <li><span className="font-medium text-ink">Consegnare un budget: da {fmtTok(c.deliver.cost)} a {fmtTok(c.deliver.max)} token</span> (1 fino a 25 voci, 1,5 fino a 60, 2 oltre). Vale 30 giorni per lo stesso budget.</li>
      <li><span className="font-medium text-ink">Studiare un bando nuovo: {fmtTok(c.study_new.cost)} token</span>, e 1 torna indietro se la lettura è completa. Un bando già in memoria è gratis.</li>
      <li><span className="font-medium text-emerald-700">Pubblicare un budget per tutti: +{fmtTok(t.publish_bonus)} token.</span> Allena il motore collettivo; una volta per cliente e bando, al massimo {t.publish_bonus_monthly_cap} al mese.</li>
    </ul>
  )
}

function PlanLine({ t }) {
  const p = t.plan
  return (
    <p className="text-sm text-ink-2">
      <span className="font-medium text-ink">Il piano: {eur(p.monthly_eur)} al mese</span> oppure <span className="font-medium text-ink">{eur(p.yearly_eur)} all’anno</span> (risparmi {eur(p.yearly_saving_eur)}), con {p.tokens_per_month} token al mese inclusi.
      Quando finiscono, <span className="font-medium text-ink">10 token in più costano {eur(t.packs[0].price_eur)}</span>.
    </p>
  )
}

function Packs({ t, onRequested }) {
  const pack = t.packs[0]
  const [q, setQ] = useState(1)
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(null)
  const [error, setError] = useState(null)
  const ask = async () => {
    setBusy(true); setError(null)
    try { const r = await api.topupRequest(pack.id, q); setDone(r.message); onRequested?.() } catch (e) { setError(e.message) } finally { setBusy(false) }
  }
  return (
    <div className="space-y-3">
      <div className="rounded-2xl bg-tint p-4 flex flex-wrap items-center gap-x-6 gap-y-3">
        <div>
          <p className="text-2xl font-semibold tabular-nums tracking-tight">{pack.tokens * q}<span className="text-sm font-normal text-mute"> token</span></p>
          <p className="text-sm text-ink">{eur(pack.price_eur * q)} <span className="text-[11px] text-mute">· {pack.note}</span></p>
        </div>
        <div className="inline-flex items-center gap-1 ml-auto" role="group" aria-label="Quanti pacchetti da 10 token">
          <button className="btn !px-2" disabled={q <= 1} onClick={() => setQ(q - 1)} aria-label="Meno"><Minus className="w-3.5 h-3.5" /></button>
          <span className="w-8 text-center text-sm tabular-nums">{q}</span>
          <button className="btn !px-2" disabled={q >= 20} onClick={() => setQ(q + 1)} aria-label="Più"><Plus className="w-3.5 h-3.5" /></button>
        </div>
        <button className="btn-primary" disabled={busy} onClick={ask}>{busy && <Loader2 className="w-3 h-3 animate-spin" />}Richiedi</button>
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
          <p className={`text-5xl font-semibold tracking-tight tabular-nums ${t.empty ? 'text-red-700' : t.low ? 'text-amber-700' : 'text-ink'}`}>{t.exempt ? '∞' : fmtTok(t.balance)}</p>
        </div>
        {!t.exempt && (
          <div className="text-sm text-ink-2 space-y-0.5 pb-1">
            <p>{fmtTok(t.included)} del mese (se ne usi meno, ne restano fino a {t.cap}) · {fmtTok(t.extra)} che non scadono</p>
            <p className="text-mute">Prossimi {t.monthly} il {new Date(t.next_grant).toLocaleDateString('it-IT', { day: 'numeric', month: 'long' })} · spesi negli ultimi 30 giorni: {fmtTok(t.spent_30_days)}</p>
          </div>
        )}
        {t.exempt && <p className="text-sm text-ink-2 pb-1">Account del titolare: non consuma token.</p>}
      </div>
      {!t.charging && !t.exempt && <p className="text-sm rounded-2xl bg-tint px-4 py-3 text-ink-2"><span className="font-medium text-ink">Fase di prova: tutto è gratuito.</span> I costi qui sotto sono quelli previsti per il futuro: per ora nessun token viene scalato e nulla si blocca.</p>}
      {t.charging && t.balance < 0 && <p className="text-sm text-amber-700">Stai usando l’anticipo di cortesia ({fmtTok(t.balance)}): il prossimo accredito lo ripiana.</p>}
      <Rules t={t} />
      <PlanLine t={t} />
      {!t.exempt && t.charging && <div className="space-y-2"><p className="text-sm font-medium text-ink">Ricarica</p><Packs t={t} onRequested={load} /></div>}
      <div>
        <button className="text-xs underline text-ink-2" onClick={() => setLog(!log)}>{log ? 'Nascondi i movimenti' : 'Mostra gli ultimi movimenti'}</button>
        {log && (
          <ul className="mt-2 space-y-1 text-xs">
            {t.ledger.length === 0 && <li className="text-mute">Nessun movimento.</li>}
            {t.ledger.map((r) => (
              <li key={r.id} className="flex gap-3 border-b border-line pb-1 last:border-0"><span className="text-mute w-28 shrink-0">{r.ts.slice(0, 10).split('-').reverse().join('/')}</span>
                <span className="text-ink-2 flex-1">{KIND[r.kind] || r.kind}{r.note ? ` · ${r.note}` : ''}{r.ref && r.kind === 'SPEND' ? ` · ${r.ref.split('|').slice(1).join(' · ')}` : ''}</span>
                <span className={`tabular-nums font-medium ${r.amount < 0 ? 'text-ink' : 'text-emerald-700'}`}>{r.amount > 0 ? '+' : ''}{fmtTok(r.amount)}</span></li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

/** Prima di calcolare il piano di allocazione: quanto costa e perché (bilancio e bandi), con un tocco per confermare. Vale 30 giorni. */
export function CostConfirm({ c, onConfirm, busy }) {
  const b = c.breakdown
  return (
    <div className="rounded-2xl bg-tint p-5 space-y-4">
      <div className="flex flex-wrap items-end gap-x-8 gap-y-2">
        <div><p className="label">Calcolare il piano costa</p><p className="text-3xl font-semibold tabular-nums tracking-tight">{fmtTok(c.due)}<span className="text-sm font-normal text-mute"> token</span></p></div>
        <p className="text-xs text-ink-2 max-w-md leading-relaxed pb-1">{c.paid > 0 ? `Hai già pagato ${fmtTok(c.paid)} per questo lavoro e questo anno: i dati ora sono più grandi, si paga solo la differenza. ` : ''}Vale 30 giorni: ricalcolare con altre scelte non costa di più.</p>
      </div>
      <ul className="text-xs text-ink-2 space-y-1">
        <li className="flex justify-between gap-4"><span>Base</span><span className="tabular-nums">{fmtTok(b.base)}</span></li>
        <li className="flex justify-between gap-4"><span>Bilancio: {b.balance_lines} righe di spesa analizzate</span><span className="tabular-nums">+ {fmtTok(b.balance_tokens)}</span></li>
        <li className="flex justify-between gap-4"><span>Bandi nel piano: {b.bandi.length} {b.bandi.length === 1 ? 'bando' : 'bandi'}, secondo quanto sono corposi</span><span className="tabular-nums">+ {fmtTok(b.bandi_tokens)}</span></li>
        <li className="flex justify-between gap-4 pt-1.5 border-t border-line font-medium text-ink"><span>Totale (da {fmtTok(b.min)} a {fmtTok(b.max)})</span><span className="tabular-nums">{fmtTok(c.cost)}</span></li>
      </ul>
      <button className="btn-primary" disabled={busy} onClick={onConfirm}>{busy && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Calcola il piano · {fmtTok(c.due)} token</button>
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
          <div className="min-w-0 flex-1"><h3 className="text-xl font-semibold tracking-tight">Servono più token</h3><p className="text-sm text-ink-2 mt-1">{info.message || `Servono ${fmtTok(info.needed)} token e ne hai ${fmtTok(info.balance)}.`}</p></div>
          <button className="rounded-full bg-tint hover:bg-tint-2 p-1.5" onClick={() => setInfo(null)} aria-label="Chiudi"><X className="w-4 h-4" /></button>
        </div>
        {t && <Rules t={t} />}
        {t && <Packs t={t} onRequested={load} />}
        <button className="btn-primary" onClick={() => setInfo(null)}>Ho capito</button>
      </div>
    </div>
  )
}
