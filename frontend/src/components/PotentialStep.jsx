import React, { useState } from 'react'
import { CheckCircle2, CircleHelp, Loader2, Sparkles } from 'lucide-react'
import { fmtEur, fmtNum, CATEGORY_LABEL } from '../lib/format'

const BASIS = {
  DICHIARATI: ['Dato dichiarato', 'tutti e tre gli ultimi esercizi hanno i contributi pubblici dichiarati nel profilo'],
  PARZIALE: ['Dato parziale', 'alcuni esercizi non hanno la voce compilata: per quelli non si sottrae nulla'],
  IPOTESI: ['Ipotesi', 'nessun contributo pubblico dichiarato: si assume che non ne siano stati ricevuti'],
}

/** Il tetto de minimis (300.000 € in tre anni): quali bandi lo toccano, quanto ne resta all'azienda (stima di QUANTO, con la sua base) e quanto ne usa il piano. */
function DeMinimisBox({ rows, dm, plan }) {
  const est = dm?.estimate
  if (!est) return null
  const [basisLabel, basisText] = BASIS[est.basis]
  const needed = plan?.de_minimis_used_eur
  const manual = dm.override !== ''
  return (
    <div className="rounded-xl border border-violet-500/30 bg-violet-500/5 p-4 space-y-2 text-xs">
      <p className="font-medium text-ink">De minimis: il tetto agli aiuti «piccoli» (300.000 € in tre anni per impresa)</p>
      <p className="text-ink-2 leading-relaxed">Bandi del piano che ci rientrano: {rows.map((r) => r.name).join('; ')}. Questi aiuti si sommano a quelli già ricevuti dall’azienda, e insieme non possono superare il tetto: il piano lo rispetta.</p>
      <div className="flex flex-wrap items-end gap-x-8 gap-y-2">
        <div><span className="label">Ancora disponibile (stima)</span><div className="text-base font-semibold tabular-nums">{fmtEur(dm.value)}</div></div>
        {needed != null && <div><span className="label">Usato da questo piano</span><div className="text-base font-semibold tabular-nums">{fmtEur(needed)}</div></div>}
        <span className={`px-2 py-0.5 rounded border text-[11px] font-medium ${est.basis === 'DICHIARATI' ? 'border-emerald-500/30 text-emerald-700' : 'border-amber-500/30 text-amber-700'}`} title={basisText}>{manual ? 'Valore scritto da te' : basisLabel}</span>
      </div>
      <p className="text-ink-2 leading-relaxed">{manual ? 'Stai usando un valore scritto da te al posto della stima.' : est.note}{needed != null && !manual && est.basis !== 'DICHIARATI' && dm.value >= needed ? ` Il piano usa solo ${fmtEur(needed)}: resta valido anche se l’azienda ha già ricevuto fino a ${fmtEur(300000 - needed)} di aiuti de minimis negli ultimi tre anni.` : ''}</p>
      <p className="text-mute leading-relaxed">{est.verify}</p>
      <div className="flex flex-wrap items-center gap-2 pt-1">
        <button className="btn !py-1" onClick={dm.onDeclare}>Dichiara gli aiuti già ricevuti</button>
        <label className="flex items-center gap-2 text-ink-2">oppure scrivi il residuo (€)<input type="number" className="field !py-1 !w-32 text-right" value={dm.override} placeholder={String(est.residual_eur)} onChange={(e) => dm.setOverride(e.target.value)} /></label>
        {manual && <button className="btn !py-1" onClick={() => dm.setOverride('')}>Torna alla stima</button>}
      </div>
    </div>
  )
}

/** Cosa significa ogni numero di questo riquadro, in parole semplici: resta sempre visibile sotto i risultati. */
function Legend({ multi }) {
  const items = [
    ['Coperto dai bandi', 'Quanto delle spese dell’anno verrebbe pagato dai bandi se l’azienda li ottenesse. Se vedi due cifre: la prima è lo scenario prudente (percentuale base di ogni bando), la seconda il massimo con tutte le maggiorazioni.'],
    ['Su una spesa di', 'Le spese previste per l’anno: la stima partita dall’ultimo bilancio, con le variazioni del punto 2.'],
    ['Quota coperta', 'Il «coperto dai bandi» diviso per la spesa: la percentuale delle spese pagata da fondi pubblici.'],
    ['Resta a tuo carico', 'La parte di spesa che nessun bando paga: la mette l’azienda.'],
    ...(multi ? [
      ['Da solo', 'Quanto darebbe quel bando se fosse l’unico. Due cifre = dal prudente al massimo.'],
      ['Nel piano insieme', 'Quanto di quel bando serve davvero quando i bandi lavorano insieme: la stessa spesa non si può far pagare due volte, quindi ogni spesa riceve un solo fondo perduto (il migliore). «Non serve» = le sue spese sono già coperte da un bando più conveniente, oppure ha raggiunto il suo tetto.'],
      ['Totale', 'La colonna «Da solo» somma i bandi come se fossero separati; la colonna «Nel piano insieme» è il vero massimo. I pochi centesimi di scarto tra le due cifre di un bando sono arrotondamenti: il piano lavora in centesimi interi, sempre per difetto.'],
    ] : []),
  ]
  return (
    <div className="rounded-xl border border-line bg-field p-4 space-y-1.5 text-[11px] leading-relaxed">
      <p className="text-xs font-medium text-ink">Come leggere questi numeri</p>
      <dl className="grid md:grid-cols-2 gap-x-8 gap-y-1.5">{items.map(([k, v]) => <div key={k}><dt className="inline font-semibold text-ink">{k}: </dt><dd className="inline text-ink-2">{v}</dd></div>)}</dl>
    </div>
  )
}


const PALETTE = ['#38bdf8', '#a78bfa', '#f472b6', '#34d399', '#fbbf24', '#fb7185', '#2dd4bf', '#818cf8', '#f97316', '#84cc16', '#e879f9', '#94a3b8']
const NET = '#f59e0b'

/** Il bilancio dell'anno ricostruito con tutti i bandi insieme: per ogni categoria di spesa, quanto copre ciascun bando e quanto resta a carico. Solo somme dei dati del piano. */
function RebuiltBudget({ plan, nameOf }) {
  const funds = plan.fund_usage.map((f) => f.fund_id)                        // tutti i bandi del piano, anche quelli che alla fine non servono
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
        {funds.map((id) => <span key={id} className={`inline-flex items-center gap-1.5 ${total.funds[id] > 0 ? '' : 'text-mute'}`}><i className="w-2.5 h-2.5 rounded-sm" style={{ background: color(id), opacity: total.funds[id] > 0 ? 1 : 0.35 }} />{nameOf(id)} · {total.funds[id] > 0 ? fmtEur(total.funds[id]) : 'non usato'}</span>)}
        <span className="inline-flex items-center gap-1.5"><i className="w-2.5 h-2.5 rounded-sm" style={{ background: NET }} />A carico · {fmtEur(total.net)}</span>
      </div>
    </div>
  )
}

/** Tutti i bandi a cui l'azienda può partecipare, applicati insieme: quanto potrebbe coprire se li vincesse tutti. Il calcolo è quello del piano (stesse regole di
 *  cumulo, tetti e de minimis): qui si scelgono i bandi e si legge il confronto con la somma dei bandi presi uno per uno. */
export default function PotentialStep({ results, picked, onPick, dm, plan, planHigh, loading, planError, onStudyMore, studyingMore }) {
  const [withMaybe, setWithMaybe] = useState(false)
  const sure = results.filter((r) => r.fit === 'ADATTO' && r.fund)
  const maybe = results.filter((r) => r.fit === 'DA_VERIFICARE' && r.fund)
  const noAmount = results.filter((r) => r.fit !== 'NON_ADATTO' && !r.fund && !r.guarantee)
  const guarantees = results.filter((r) => r.fit !== 'NON_ADATTO' && r.guarantee)
  const wanted = [...sure, ...(withMaybe ? maybe : [])]
  const wantedIds = wanted.map((r) => r.bando_id)
  const isAll = wantedIds.length > 0 && wantedIds.length === picked.length && wantedIds.every((id) => picked.includes(id))
  const pickedRows = results.filter((r) => picked.includes(r.bando_id) && r.fund)
  const alone = pickedRows.reduce((s, r) => s + (r.estimate?.covered_eur || 0), 0)
  const used = Object.fromEntries((plan?.fund_usage || []).map((u) => [u.fund_id, u.used_eur]))

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <button className="btn-primary" disabled={wanted.length === 0} onClick={() => onPick(wantedIds, !withMaybe)}>
          <Sparkles className="w-3.5 h-3.5" />{isAll ? 'Bandi già combinati' : `Combina tutti i bandi adatti (${sure.length}${withMaybe ? ` + ${maybe.length} da verificare` : ''})`}
        </button>
        {maybe.length > 0 && (
          <label className="inline-flex items-center gap-2 text-xs text-ink-2 cursor-pointer">
            <input type="checkbox" checked={withMaybe} onChange={(e) => setWithMaybe(e.target.checked)} />Includi anche {maybe.length === 1 ? 'il bando da verificare' : `i ${maybe.length} bandi da verificare`} con un importo stimabile (scenario ottimistico)
          </label>
        )}
        {picked.length > 0 && <button className="btn" onClick={() => onPick([], false)}>Deseleziona tutti</button>}
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
                  <div><span className="label">Coperto dai bandi</span><div className="text-2xl font-display font-semibold text-emerald-700 tabular-nums">{fmtEur(plan.covered_by_public_funds_eur)}{planHigh && planHigh.covered_by_public_funds_eur > plan.covered_by_public_funds_eur + 0.5 && <span className="text-base text-emerald-700/80"> – {fmtEur(planHigh.covered_by_public_funds_eur)}</span>}</div>
                    {planHigh && planHigh.covered_by_public_funds_eur > plan.covered_by_public_funds_eur + 0.5 && <span className="text-[11px] text-mute">dalla stima prudente a quella con tutte le maggiorazioni</span>}</div>
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
                        <tr key={r.bando_id} className="border-t border-line"><td className="py-1.5 text-ink-2 pr-3">{r.name}{r.de_minimis?.applies && <span className="ml-1.5 px-1.5 py-px rounded border border-violet-500/30 bg-violet-500/10 text-[10px] font-medium text-violet-700" title={r.de_minimis.evidence[0]?.text}>de minimis</span>}{r.estimate?.kind_label && <span className="block text-[10px] text-mute">{r.estimate.kind_label}</span>}{r.fit === 'DA_VERIFICARE' && <span className="ml-1.5 text-[10px] text-amber-700">(da verificare)</span>}</td>
                          <td className="text-right tabular-nums">{fmtEur(r.estimate?.covered_eur)}{r.estimate?.covered_high_eur > r.estimate?.covered_eur + 0.5 && <span className="text-mute"> – {fmtEur(r.estimate.covered_high_eur)}</span>}</td><td className={`text-right tabular-nums ${(used[r.fund.fund_id] ?? 0) > 0 ? 'text-emerald-700' : 'text-mute'}`}>{(used[r.fund.fund_id] ?? 0) > 0 ? fmtEur(used[r.fund.fund_id]) : 'non serve'}</td></tr>
                      ))}
                      <tr className="border-t border-line-strong font-semibold"><td className="py-1.5">Totale</td><td className="text-right tabular-nums">{fmtEur(alone)}</td><td className="text-right tabular-nums">{fmtEur(plan.covered_by_public_funds_eur)}</td></tr>
                    </tbody>
                  </table>
                  {pickedRows.some((r) => (used[r.fund.fund_id] ?? 0) === 0) && (
                    <p className="text-[11px] text-ink-2 mt-2 leading-relaxed"><strong className="text-ink">Perché alcuni bandi risultano «non serve»?</strong> Non sono scartati: in questo piano le loro spese sono già coperte da un bando più conveniente (ogni spesa riceve un solo contributo a fondo perduto, il migliore) oppure il bando ha raggiunto il suo tetto. Restano nel calcolo e rientrano da soli se cambiano i dati.</p>
                  )}
                  {wanted.length > 0 && picked.length < sure.length && <p className="text-[11px] text-amber-700 mt-1">Hai incluso {picked.length} bandi adatti su {sure.length}: il potenziale massimo li comprende tutti.</p>}
                  <p className="text-[11px] text-mute mt-2 leading-relaxed">
                    {alone - plan.covered_by_public_funds_eur > 0.5
                      ? `Sommando i bandi uno per uno si arriverebbe a ${fmtEur(alone)}, ma la stessa spesa non può essere pagata due volte: insieme il massimo è ${fmtEur(plan.covered_by_public_funds_eur)} (${fmtEur(alone - plan.covered_by_public_funds_eur)} in meno per spese contese, tetti dei fondi o fondi non cumulabili).`
                      : 'I bandi scelti coprono spese diverse o compatibili: insieme non si tolgono nulla a vicenda.'}
                  </p>
                </div>
              )}
              <RebuiltBudget plan={plan} nameOf={(id) => (results.find((r) => r.fund?.fund_id === id)?.name || id)} />
              {pickedRows.some((r) => r.fund.de_minimis) && <DeMinimisBox rows={pickedRows.filter((r) => r.fund.de_minimis)} dm={dm} plan={plan} />}
              <Legend multi={pickedRows.length > 1} />
            </>
          ) : !planError && <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Calcolo il piano con tutti i bandi insieme…</p>}
          <p className="text-[11px] text-mute leading-relaxed">Nota professionale da includere nel report per il cliente: è un massimo teorico, presuppone di presentare domanda a tutti i bandi e di vincerli tutti. Usa solo ciò che ogni bando dichiara (aliquote, categorie, tetti) e, per prudenza, ogni spesa riceve un solo contributo a fondo perduto (il migliore): i contributi a fondo perduto non si sommano sulla stessa spesa, mentre garanzie, interessi e risparmi fiscali sì; l’esito reale dipende dall’istruttoria e dalle risorse disponibili.</p>
        </div>
      )}

      {guarantees.length > 0 && (
        <div className="rounded-2xl border border-line bg-field p-4 space-y-2 text-xs">
          <p className="font-medium text-ink">Garanzie pubbliche ({guarantees.length}): valgono, ma non si sommano</p>
          <p className="text-ink-2 leading-relaxed">Non sono un contributo: coprono una parte di un finanziamento bancario e spesso permettono di ottenerlo. Per questo l’importo garantibile sta fuori dal potenziale.</p>
          <ul className="space-y-1">{guarantees.map((r) => <li key={r.bando_id} className="text-ink-2"><span className="font-medium text-ink">{r.name}</span> — fino a {fmtEur(r.guarantee.guaranteed_low_eur)} – {fmtEur(r.guarantee.guaranteed_high_eur)} garantiti su un finanziamento di {fmtEur(r.guarantee.financed_eur)} (ipotesi: finanzi i beni strumentali previsti).</li>)}</ul>
        </div>
      )}

      {noAmount.length > 0 && (
        <div className="rounded-2xl border border-line bg-field p-4 space-y-2 text-xs">
          <p className="font-medium text-ink inline-flex items-center gap-1.5"><CircleHelp className="w-3.5 h-3.5 text-amber-700" />Bandi senza una percentuale nei documenti letti ({noAmount.length})</p>
          <p className="text-ink-2 leading-relaxed">Nei documenti ufficiali letti non compare una percentuale di agevolazione. Studiali di nuovo: la ricerca ora cerca apposta la percentuale. Finché manca, non li sommo.</p>
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
