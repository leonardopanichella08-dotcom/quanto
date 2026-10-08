import React, { useState } from 'react'
import { CheckCircle2, CircleHelp, Loader2, Sparkles } from 'lucide-react'
import { fmtEur, fmtNum, CATEGORY_LABEL } from '../lib/format'


const PALETTE = ['#38bdf8', '#a78bfa', '#f472b6', '#34d399', '#fbbf24', '#fb7185']
const NET = '#f59e0b'

/** Il bilancio dell'anno ricostruito con tutti i bandi insieme: per ogni categoria di spesa, quanto copre ciascun bando e quanto resta a carico. Solo somme dei dati del piano. */
function RebuiltBudget({ plan, nameOf }) {
  const funds = plan.fund_usage.filter((f) => f.used_eur > 0).map((f) => f.fund_id)
  const by = {}
  plan.allocation_plan.forEach((i) => {
    const c = (by[i.category] ||= { gross: 0, net: 0, funds: {} })
    c.gross += i.gross_amount_eur; c.net += i.net_cost_to_entity_eur
    i.coverage.forEach((x) => { c.funds[x.fund_id] = (c.funds[x.fund_id] || 0) + x.covered_amount_eur })
  })
  const rows = Object.entries(by).sort((a, b) => b[1].gross - a[1].gross)
  const total = { gross: plan.total_gross_expense_eur, net: plan.net_cost_to_entity_eur, funds: Object.fromEntries(plan.fund_usage.map((f) => [f.fund_id, f.used_eur])) }
  const max = Math.max(...rows.map(([, c]) => c.gross), 1)
  const color = (id) => PALETTE[funds.indexOf(id) % PALETTE.length]
  const Bar = ({ c, width, label, strong }) => (
    <div className="flex items-center gap-3 text-xs">
      <span className={`w-36 shrink-0 text-ink-2 ${strong ? 'font-semibold text-ink' : ''}`}>{label}</span>
      <div className="flex h-5 rounded overflow-hidden bg-tint-2" style={{ width: `${width}%` }} role="img" aria-label={`${label}: spesa ${fmtEur(c.gross)}, coperta ${fmtEur(c.gross - c.net)}, a carico ${fmtEur(c.net)}`}>
        {funds.map((id) => c.funds[id] > 0 && <div key={id} title={`${nameOf(id)}: ${fmtEur(c.funds[id])}`} style={{ width: `${(c.funds[id] / c.gross) * 100}%`, background: color(id) }} />)}
        {c.net > 0 && <div title={`A carico: ${fmtEur(c.net)}`} style={{ width: `${(c.net / c.gross) * 100}%`, background: NET }} />}
      </div>
      <span className="tabular-nums text-mute whitespace-nowrap">{fmtEur(c.gross)} · {fmtNum(((c.gross - c.net) / c.gross) * 100, 0)}% coperto</span>
    </div>
  )
  return (
    <div className="space-y-3">
      <span className="label">Il bilancio ricostruito: spese dell’anno, coperte dai bandi e a carico</span>
      <Bar c={total} width={100} label="Totale spese" strong />
      <div className="space-y-1.5 pt-1 border-t border-line">
        {rows.map(([cat, c]) => <Bar key={cat} c={c} width={Math.max(8, (c.gross / max) * 100)} label={CATEGORY_LABEL[cat] || cat} />)}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-ink-2">
        {funds.map((id) => <span key={id} className="inline-flex items-center gap-1.5"><i className="w-2.5 h-2.5 rounded-sm" style={{ background: color(id) }} />{nameOf(id)} · {fmtEur(total.funds[id])}</span>)}
        <span className="inline-flex items-center gap-1.5"><i className="w-2.5 h-2.5 rounded-sm" style={{ background: NET }} />A carico · {fmtEur(total.net)}</span>
      </div>
    </div>
  )
}

/** Tutti i bandi a cui l'azienda può partecipare, applicati insieme: quanto potrebbe coprire se li vincesse tutti. Il calcolo è quello del piano (stesse regole di
 *  cumulo, tetti e de minimis): qui si scelgono i bandi e si legge il confronto con la somma dei bandi presi uno per uno. */
export default function PotentialStep({ results, picked, setPicked, plan, loading, planError, onStudyMore, studyingMore }) {
  const [withMaybe, setWithMaybe] = useState(false)
  const sure = results.filter((r) => r.fit === 'ADATTO' && r.fund)
  const maybe = results.filter((r) => r.fit === 'DA_VERIFICARE' && r.fund)
  const noAmount = results.filter((r) => r.fit !== 'NON_ADATTO' && !r.fund)
  const wanted = [...sure, ...(withMaybe ? maybe : [])]
  const wantedIds = wanted.map((r) => r.bando_id)
  const isAll = wantedIds.length > 0 && wantedIds.length === picked.length && wantedIds.every((id) => picked.includes(id))
  const pickedRows = results.filter((r) => picked.includes(r.bando_id) && r.fund)
  const alone = pickedRows.reduce((s, r) => s + (r.estimate?.covered_eur || 0), 0)
  const used = Object.fromEntries((plan?.fund_usage || []).map((u) => [u.fund_id, u.used_eur]))

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <button className="btn-primary" disabled={wanted.length === 0} onClick={() => setPicked(wantedIds)}>
          <Sparkles className="w-3.5 h-3.5" />{isAll ? 'Bandi già combinati' : `Combina tutti i bandi adatti (${sure.length}${withMaybe ? ` + ${maybe.length} da verificare` : ''})`}
        </button>
        {maybe.length > 0 && (
          <label className="inline-flex items-center gap-2 text-xs text-ink-2 cursor-pointer">
            <input type="checkbox" checked={withMaybe} onChange={(e) => setWithMaybe(e.target.checked)} />Includi anche {maybe.length === 1 ? 'il bando da verificare' : `i ${maybe.length} bandi da verificare`} con un importo stimabile (scenario ottimistico)
          </label>
        )}
        {picked.length > 0 && <button className="btn" onClick={() => setPicked([])}>Deseleziona tutti</button>}
      </div>
      {sure.length === 0 && <p className="text-xs text-amber-700">Nessun bando risulta già adatto con un importo stimabile. Studia altri bandi del catalogo{maybe.length ? ' oppure includi quelli da verificare' : ''}.</p>}
      {sure.length === 1 && maybe.length === 0 && <p className="text-xs text-ink-2">Per ora un solo bando adatto ha un contributo calcolabile sulle tue spese. Per trovarne altri puoi farne studiare di nuovi al programma dal catalogo.</p>}
      {onStudyMore && (
        <div className="flex flex-wrap items-center gap-3">
          <button className="btn" disabled={studyingMore} onClick={onStudyMore}>{studyingMore && <Loader2 className="w-3.5 h-3.5 animate-spin" />}{studyingMore ? 'Studio in corso…' : 'Studia i 5 bandi del catalogo più affini'}</button>
          <span className="text-[11px] text-mute">Cerca, scarica e legge le fonti ufficiali di ciascuno, uno dopo l’altro. A lettura finita rifaccio la stima e i bandi.</span>
        </div>
      )}

      {picked.length > 0 && (
        <div className={`rounded-2xl border border-brand/50 bg-brand/5 p-5 space-y-4 transition ${loading ? 'opacity-60' : ''}`}>
          {planError && <p className="text-xs text-red-700">{planError}</p>}
          {plan ? (
            <>
              <div>
                <p className="text-xs text-ink-2">{isAll ? 'Potenziale massimo' : 'Con i bandi che hai scelto'}: se l’azienda ottenesse {pickedRows.length === 1 ? 'il bando scelto' : `tutti i ${pickedRows.length} bandi insieme`}, nell’anno {plan.fiscal_year}</p>
                <div className="flex flex-wrap items-end gap-x-8 gap-y-2 mt-1">
                  <div><span className="label">Coperto dai bandi</span><div className="text-2xl font-display font-semibold text-emerald-700 tabular-nums">{fmtEur(plan.covered_by_public_funds_eur)}</div></div>
                  <div><span className="label">Su una spesa di</span><div className="text-sm font-semibold tabular-nums">{fmtEur(plan.total_gross_expense_eur)}</div></div>
                  <div><span className="label">Quota coperta</span><div className="text-sm font-semibold tabular-nums">{fmtNum(plan.overall_coverage_percentage, 1)}%</div></div>
                  <div><span className="label">Resta a tuo carico</span><div className="text-sm font-semibold tabular-nums text-amber-700">{fmtEur(plan.net_cost_to_entity_eur)}</div></div>
                </div>
              </div>
              {pickedRows.length > 1 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead><tr className="text-left text-mute"><th className="py-1 font-medium">Bando</th><th className="font-medium text-right">Da solo</th><th className="font-medium text-right">Nel piano insieme</th></tr></thead>
                    <tbody>
                      {pickedRows.map((r) => (
                        <tr key={r.bando_id} className="border-t border-line"><td className="py-1.5 text-ink-2 pr-3">{r.name}{r.fit === 'DA_VERIFICARE' && <span className="ml-1.5 text-[10px] text-amber-700">(da verificare)</span>}</td>
                          <td className="text-right tabular-nums">{fmtEur(r.estimate?.covered_eur)}</td><td className="text-right tabular-nums text-emerald-700">{fmtEur(used[r.fund.fund_id] ?? 0)}</td></tr>
                      ))}
                      <tr className="border-t border-line-strong font-semibold"><td className="py-1.5">Totale</td><td className="text-right tabular-nums">{fmtEur(alone)}</td><td className="text-right tabular-nums">{fmtEur(plan.covered_by_public_funds_eur)}</td></tr>
                    </tbody>
                  </table>
                  <p className="text-[11px] text-mute mt-2 leading-relaxed">
                    {alone - plan.covered_by_public_funds_eur > 0.5
                      ? `Sommando i bandi uno per uno si arriverebbe a ${fmtEur(alone)}, ma la stessa spesa non può essere pagata due volte: insieme il massimo è ${fmtEur(plan.covered_by_public_funds_eur)} (${fmtEur(alone - plan.covered_by_public_funds_eur)} in meno per spese contese, tetti dei fondi o fondi non cumulabili).`
                      : 'I bandi scelti coprono spese diverse o compatibili: insieme non si tolgono nulla a vicenda.'}
                  </p>
                </div>
              )}
              <RebuiltBudget plan={plan} nameOf={(id) => (results.find((r) => r.fund?.fund_id === id)?.name || id)} />
            </>
          ) : !planError && <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Calcolo il piano con tutti i bandi insieme…</p>}
          <p className="text-[11px] text-mute leading-relaxed">Nota professionale da includere nel report per il cliente: è un massimo teorico, presuppone di presentare domanda a tutti i bandi e di vincerli tutti. Usa solo ciò che ogni bando dichiara (aliquote, categorie, tetti, cumulo); l’esito reale dipende dall’istruttoria e dalle risorse disponibili.</p>
        </div>
      )}

      {noAmount.length > 0 && (
        <div className="rounded-2xl border border-line bg-field p-4 space-y-2 text-xs">
          <p className="font-medium text-ink inline-flex items-center gap-1.5"><CircleHelp className="w-3.5 h-3.5 text-amber-700" />Altri bandi a cui puoi partecipare, senza un importo sulle spese ({noAmount.length})</p>
          <p className="text-ink-2 leading-relaxed">Il loro beneficio non è una percentuale delle spese (garanzie, finanziamenti agevolati, benefici fiscali…): vale ma dipende da dati che non sono nel bilancio, quindi non lo sommo al potenziale.</p>
          <ul className="space-y-1">
            {noAmount.map((r) => (
              <li key={r.bando_id} className="flex gap-1.5 text-ink-2"><CheckCircle2 className="w-3.5 h-3.5 mt-0.5 shrink-0 text-emerald-600" /><span><span className="font-medium text-ink">{r.name}</span>{r.benefit?.summary ? ` — ${r.benefit.summary}` : ''}</span></li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
