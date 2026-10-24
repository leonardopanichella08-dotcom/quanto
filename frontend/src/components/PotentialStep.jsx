import React, { useState } from 'react'
import { CheckCircle2, CircleHelp, Loader2, Sparkles } from 'lucide-react'
import { fmtEur, fmtNum, CATEGORY_LABEL } from '../lib/format'
import { Info } from './ui'

const BASIS = {
  DICHIARATI: ['Dato dichiarato', 'tutti e tre gli ultimi esercizi hanno i contributi pubblici dichiarati nel profilo'],
  PARZIALE: ['Dato parziale', 'alcuni esercizi non hanno la voce compilata: per quelli non si sottrae nulla'],
  IPOTESI: ['Ipotesi', 'nessun contributo pubblico dichiarato: si assume che non ne siano stati ricevuti'],
  RNA: ['Verificato sul registro', 'impresa unica e visura aiuti dell’RNA verificate e recenti'],
}

/** Il tetto de minimis (300.000 € in tre anni): quali bandi lo toccano, quanto ne resta all'azienda (stima di QUANTO, con la sua base) e quanto ne usa il piano. */
function DeMinimisBox({ rows, dm, plan }) {
  const [open, setOpen] = useState(false)
  const est = dm?.estimate
  if (!est) return null
  const [basisLabel, basisText] = BASIS[est.basis]
  const needed = plan?.de_minimis_used_eur
  const manual = dm.override !== ''
  const ok = est.basis === 'DICHIARATI' || est.basis === 'RNA'
  return (
    <div className="rounded-xl border border-violet-500/30 bg-violet-500/5 p-3 text-xs space-y-2">
      <button type="button" className="w-full flex flex-wrap items-center gap-x-4 gap-y-1 text-left" aria-expanded={open} onClick={() => setOpen(!open)}>
        <span className="font-medium text-ink">De minimis disponibile: <span className="tabular-nums">{fmtEur(dm.value)}</span></span>
        {needed != null && <span className="text-ink-2">il piano ne usa {fmtEur(needed)}</span>}
        <span className={`px-2 py-0.5 rounded border text-[11px] font-medium ${ok ? 'border-emerald-500/30 text-emerald-700' : 'border-amber-500/30 text-amber-700'}`} title={basisText}>{manual ? 'scritto da te' : basisLabel}</span>
        <span className="ml-auto text-mute">{open ? 'Chiudi' : 'Dettagli'}</span>
      </button>
      {open && (
        <div className="space-y-2 pt-2 border-t border-violet-500/20">
          <p className="text-ink-2 leading-relaxed">Il de minimis è il tetto agli aiuti «piccoli»: 300.000 € in tre anni per impresa. Bandi del piano che ci rientrano: {rows.map((r) => r.name).join('; ')}.</p>
          <p className="text-ink-2 leading-relaxed">{manual ? 'Stai usando un valore scritto da te al posto della stima.' : est.note}</p>
          {est.verification && (
            <div className={`p-2.5 rounded-lg border space-y-1 ${est.verification.status === 'VERIFICATO' ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-amber-500/30 bg-amber-500/5'}`}>
              <p className={`font-medium ${est.verification.status === 'VERIFICATO' ? 'text-emerald-700' : 'text-amber-700'}`}>{est.verification.status === 'VERIFICATO' ? 'Verificato sul registro nazionale degli aiuti' : 'Non verificato sul registro nazionale degli aiuti'}</p>
              <p className="text-ink-2 leading-relaxed">{est.verification.message}</p>
              <button className="underline text-ink-2" onClick={dm.onVerify}>Completa la verifica</button>
            </div>
          )}
          <div className="flex flex-wrap items-center gap-2">
            <button className="btn !py-1" onClick={dm.onDeclare}>Dichiara gli aiuti già ricevuti</button>
            <label className="flex items-center gap-2 text-ink-2">o scrivi il residuo (€)<input type="text" inputMode="decimal" className="field !py-1 !w-32 text-right" value={dm.override} placeholder={String(est.residual_eur)} onChange={(e) => dm.setOverride(e.target.value)} aria-label="Residuo de minimis in euro" /></label>
            {manual && <button className="btn !py-1" onClick={() => dm.setOverride('')}>Torna alla stima</button>}
            {dm.invalid && <span className="text-[11px] text-amber-700">Valore non valido: uso la stima.</span>}
          </div>
        </div>
      )}
    </div>
  )
}

/** Cosa significa ogni numero di questo riquadro, in parole semplici: resta sempre visibile sotto i risultati. */
function Legend({ multi }) {
  const items = [
    ['Coperto dai bandi', 'Quanto delle spese verrebbe pagato dai bandi se li ottenessi. Due cifre: la prima è lo scenario prudente, la seconda il massimo con tutte le maggiorazioni.'],
    ['Quota coperta', 'Il coperto diviso per la spesa.'],
    ['Resta a tuo carico', 'La parte che nessun bando paga.'],
    ...(multi ? [
      ['Da solo', 'Quanto darebbe quel bando se fosse l’unico.'],
      ['Nel piano insieme', 'Quanto di quel bando serve davvero: la stessa spesa non può essere pagata due volte, quindi riceve un solo fondo perduto (il migliore). «Non serve» = le sue spese sono già coperte da un bando più conveniente o ha raggiunto il suo tetto.'],
    ] : []),
  ]
  return (
    <Info label="Come leggere questi numeri">
      <dl className="space-y-1">{items.map(([k, v]) => <div key={k}><dt className="inline font-semibold text-ink">{k}: </dt><dd className="inline">{v}</dd></div>)}</dl>
      <p className="text-mute">È un massimo teorico: presuppone di presentare domanda a tutti i bandi e di vincerli. Usa solo ciò che ogni bando dichiara; l’esito reale dipende dall’istruttoria e dalle risorse disponibili.</p>
    </Info>
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
    <div className="space-y-3 overflow-x-auto"><div className="space-y-3 min-w-[520px]">
      <span className="label">Il bilancio ricostruito: spese dell’anno, coperte dai bandi e a carico</span>
      <p className="text-xs text-ink-2 leading-relaxed max-w-2xl">Ogni riga è un tipo di spesa: i colori sono i bandi che ne pagano una parte, l’arancio è ciò che resta a tuo carico. La riga in alto è il totale.</p>
      <Bar c={total} width={100} label="Totale spese" strong />
      <div className="space-y-1.5 pt-1 border-t border-line">
        {rows.map(([cat, c]) => <Bar key={cat} c={c} width={Math.max(8, (c.gross / max) * 100)} label={CATEGORY_LABEL[cat] || cat} />)}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-ink-2">
        {funds.map((id) => <span key={id} className={`inline-flex items-center gap-1.5 ${total.funds[id] > 0 ? '' : 'text-mute'}`}><i className="w-2.5 h-2.5 rounded-sm" style={{ background: color(id), opacity: total.funds[id] > 0 ? 1 : 0.35 }} />{nameOf(id)} · {total.funds[id] > 0 ? fmtEur(total.funds[id]) : 'non usato'}</span>)}
        <span className="inline-flex items-center gap-1.5"><i className="w-2.5 h-2.5 rounded-sm" style={{ background: NET }} />A carico · {fmtEur(total.net)}</span>
      </div>
    </div></div>
  )
}

/** Tutti i bandi a cui l'azienda può partecipare, applicati insieme: quanto potrebbe coprire se li vincesse tutti. Il calcolo è quello del piano (stesse regole di
 *  cumulo, tetti e de minimis): qui si scelgono i bandi e si legge il confronto con la somma dei bandi presi uno per uno. */
export default function PotentialStep({ results, picked, onPick, dm, plan, planHigh, loading, planError, onStudyMore, studyingMore, studyQueue = 0, onStudyStop, scenario = 'ANNUAL', isCandidate = () => true, projectOnly = 0, onGoProjects }) {
  const sure = results.filter((r) => r.fit === 'ADATTO' && r.fund && isCandidate(r))
  const noAmount = results.filter((r) => r.fit !== 'NON_ADATTO' && !r.fund && !r.guarantee)
  const guarantees = results.filter((r) => r.fit !== 'NON_ADATTO' && r.guarantee)
  const wanted = sure                                  // nel piano entrano solo i bandi ADATTI: quelli da verificare non si sommano mai
  const wantedIds = wanted.map((r) => r.bando_id)
  const isAll = wantedIds.length > 0 && wantedIds.length === picked.length && wantedIds.every((id) => picked.includes(id))
  const pickedRows = results.filter((r) => picked.includes(r.bando_id) && r.fund)
  const alone = pickedRows.reduce((s, r) => s + (r.estimate?.covered_eur || 0), 0)
  const used = Object.fromEntries((plan?.fund_usage || []).map((u) => [u.fund_id, u.used_eur]))

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <button className="btn-primary" disabled={wanted.length === 0} onClick={() => onPick(wantedIds, true)}>
          <Sparkles className="w-3.5 h-3.5" />{isAll ? (scenario === 'PROJECT' ? 'Tutti i bandi del progetto inclusi' : 'Tutti i bandi inclusi') : `${scenario === 'PROJECT' ? 'Includi i bandi del progetto' : 'Includi tutti'} (${sure.length})`}
        </button>
        {picked.length > 0 && <button className="btn" onClick={() => onPick([], false)}>Nessuno</button>}
      </div>
      {sure.length === 0 && <p className="text-xs text-amber-700">{scenario === 'PROJECT' ? 'Nessun bando adatto cita questo tipo di progetto: puoi includere tu i bandi dalla lista «Bandi».' : 'Nessun bando adatto per le spese annuali con un importo stimabile: studia altri bandi del catalogo.'}</p>}
      {scenario === 'ANNUAL' && projectOnly > 0 && (
        <p className="text-xs text-ink-2">{projectOnly} {projectOnly === 1 ? 'bando finanzia' : 'bandi finanziano'} solo progetti, non le spese annuali: non {projectOnly === 1 ? 'è' : 'sono'} in questo piano. {onGoProjects && <button className="underline text-ink" onClick={onGoProjects}>Scegli un progetto</button>}</p>
      )}
      {onStudyMore && (
        <div className="flex flex-wrap items-center gap-3">
          <button className="btn" disabled={studyingMore} onClick={() => onStudyMore(false)}>{studyingMore && <Loader2 className="w-3.5 h-3.5 animate-spin" />}{studyingMore ? 'Studio in corso…' : 'Studia a fondo i 5 più affini'}</button>
          {!studyingMore && studyQueue > 5 && <button className="btn-primary" onClick={() => onStudyMore(true)}>Studia a fondo tutti i bandi affini ({studyQueue})</button>}
          {studyingMore && onStudyStop && <button className="btn" onClick={onStudyStop}>Ferma dopo questo bando</button>}
          <Info label="Cosa fa">Tutti i bandi del catalogo sono già letti in breve (scheda ufficiale) e ordinati per affinità. Qui studi a fondo i più affini: cerca, scarica e legge le fonti ufficiali di ciascuno, uno dopo l’altro (circa un minuto ciascuno: lascia aperta la pagina), poi rifà la stima. Solo un bando studiato a fondo ha importi veri e può avere un budget; fino ad allora la scheda mostra un tetto provvisorio ricavato dalle sue cifre.</Info>
        </div>
      )}

      {picked.length > 0 && (
        <div className={`rounded-2xl border border-brand/50 bg-brand/5 p-5 space-y-4 transition ${loading ? 'opacity-60' : ''}`}>
          {pickedRows.some((r) => r.fund.de_minimis) && <DeMinimisBox rows={pickedRows.filter((r) => r.fund.de_minimis)} dm={dm} plan={plan} />}
          {plan ? (
            <>
              <div>
                <p className="text-xs text-ink-2">{scenario === 'PROJECT' ? 'Progetto' : 'Piano dell’anno'} · {pickedRows.length === 1 ? '1 bando' : `${pickedRows.length} bandi insieme`} · {plan.fiscal_year}</p>
                <div className="flex flex-wrap items-end gap-x-8 gap-y-2 mt-1">
                  <div><span className="label">Coperto dai bandi</span><div className="text-2xl font-display font-semibold text-emerald-700 tabular-nums">{fmtEur(plan.covered_by_public_funds_eur)}{planHigh && planHigh.covered_by_public_funds_eur > plan.covered_by_public_funds_eur + 0.5 && <span className="text-base text-emerald-700/80"> – {fmtEur(planHigh.covered_by_public_funds_eur)}</span>}</div>
                    {planHigh && planHigh.covered_by_public_funds_eur > plan.covered_by_public_funds_eur + 0.5 && <span className="text-[11px] text-mute">prudente – con maggiorazioni</span>}</div>
                  <div><span className="label">Su spese di</span><div className="text-sm font-semibold tabular-nums">{fmtEur(plan.total_gross_expense_eur)}</div></div>
                  <div><span className="label">Quota coperta</span><div className="text-sm font-semibold tabular-nums">{fmtNum(plan.overall_coverage_percentage, 1)}%</div></div>
                  <div><span className="label">A tuo carico</span><div className="text-sm font-semibold tabular-nums text-amber-700">{fmtEur(plan.net_cost_to_entity_eur)}</div></div>
                </div>
              </div>
              {plan.covered_by_public_funds_eur <= 0 && <p className="text-xs text-amber-700 leading-relaxed">I bandi inclusi non coprono nessuna di queste spese: le categorie che ammettono (o la finestra di spesa, o i tetti) non coincidono con quelle {scenario === 'PROJECT' ? 'del progetto' : 'dell’anno'}. Apri «Dettagli» di ciascun bando per vedere cosa ammette.</p>}
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
                  {alone - plan.covered_by_public_funds_eur > 0.5 && <p className="text-[11px] text-mute mt-2">Sommati uno per uno farebbero {fmtEur(alone)}: la stessa spesa non si paga due volte, quindi insieme il massimo è {fmtEur(plan.covered_by_public_funds_eur)}.</p>}
                </div>
              )}
              <RebuiltBudget plan={plan} nameOf={(id) => (results.find((r) => r.fund?.fund_id === id)?.name || id)} />
              <Legend multi={pickedRows.length > 1} />
            </>
          ) : !planError && <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Calcolo il piano con tutti i bandi insieme…</p>}
        </div>
      )}

      {guarantees.length > 0 && (
        <div className="rounded-2xl border border-line bg-field p-4 space-y-2 text-xs">
          <div className="font-medium text-ink space-y-1"><p>Garanzie pubbliche ({guarantees.length})</p><Info label="Perché sono a parte">Non sono un contributo: coprono una parte di un finanziamento bancario. Per questo non si sommano al piano.</Info></div>
                    <ul className="space-y-1">{guarantees.map((r) => <li key={r.bando_id} className="text-ink-2"><span className="font-medium text-ink">{r.name}</span> — garantiti {fmtEur(r.guarantee.guaranteed_low_eur)} – {fmtEur(r.guarantee.guaranteed_high_eur)} su un finanziamento di {fmtEur(r.guarantee.financed_eur)}.</li>)}</ul>
        </div>
      )}

      {noAmount.length > 0 && (
        <div className="rounded-2xl border border-line bg-field p-4 space-y-2 text-xs">
          <p className="font-medium text-ink inline-flex items-center gap-1.5"><CircleHelp className="w-3.5 h-3.5 text-amber-700" />Senza percentuale nei documenti letti ({noAmount.length}): non li sommo</p>
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
