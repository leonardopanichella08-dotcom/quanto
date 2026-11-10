import React, { useState } from 'react'
import { AlertTriangle, CheckCircle2, ChevronDown, CircleHelp, ExternalLink } from 'lucide-react'
import { fmtEur, fmtNum, su } from '../lib/format'
import { Note } from './ui'
import { idleReason } from '../lib/idleReason'

const ORIGIN = {
  ANNUAL: ['Bando · spese dell’anno', 'bg-sky-500/15 text-sky-700', '#38bdf8'],
  PROJECT: ['Bando a progetto', 'bg-violet-500/15 text-violet-700', '#a78bfa'],
  MISURA: ['Agevolazione sul lavoro', 'bg-emerald-500/15 text-emerald-700', '#34d399'],
}
const HEAD = { ANNUAL: 'Sulle spese dell’anno', PROJECT: 'Sul progetto', MISURA: 'Agevolazioni sul lavoro' }          // titoli dei totali: un credito d'imposta sulle spese dell'anno non è un «bando»
const VERIFIED = { SECONDARIA: 'letta su fonte secondaria: conferma sul sito INPS', PRIMARIA: 'letta su fonte ufficiale', DA_VERIFICARE: 'parametri da leggere nel bando' }
const CHECK = { OK: [CheckCircle2, 'text-emerald-700'], UNKNOWN: [CircleHelp, 'text-amber-700'], FAIL: [AlertTriangle, 'text-red-700'] }

/** Perché un bando è stato scelto: i controlli superati con il loro motivo, che spese paga nel piano, in che percentuale, e il testo ufficiale da cui viene. */
export function BandoWhy({ r, plan }) {
  const e = r.estimate
  const lines = (plan?.allocation_plan || []).map((l) => ({ l, c: l.coverage.find((x) => x.fund_id === r.fund?.fund_id) })).filter((x) => x.c && x.c.covered_amount_eur > 0)
  return (
    <div className="space-y-3 text-xs text-ink-2 leading-relaxed">
      <div>
        <p className="label">Le caratteristiche per cui è stato scelto</p>
        <ul className="space-y-1">
          {r.checks.filter((c) => c.result !== 'FAIL').map((c) => { const [Icon, color] = CHECK[c.result]; return <li key={c.id} className="flex gap-1.5"><Icon className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${color}`} /><span><span className="font-medium text-ink">{c.label}:</span> {c.detail}</span></li> })}
        </ul>
      </div>
      <div className="grid sm:grid-cols-2 gap-x-6 gap-y-1">
        {e?.kind_label && <p><span className="font-medium text-ink">Tipo di aiuto:</span> {e.kind_label}</p>}
        {r.mode && <p><span className="font-medium text-ink">Come si accede:</span> {r.mode.needs_project ? 'a progetto' : r.mode.label} · si calcola {su(r.mode.base)}</p>}
        {e && <p><span className="font-medium text-ink">Percentuale applicata:</span> {fmtNum(e.rate_pct, 0)}%{e.rate_high_pct > e.rate_pct ? ` (fino al ${fmtNum(e.rate_high_pct, 0)}% con le maggiorazioni)` : ''} delle spese ammissibili{e.cap_eur ? `, tetto ${fmtEur(e.cap_eur)}` : ''}</p>}
        {r.de_minimis?.applies && <p><span className="font-medium text-ink">De minimis:</span> conta contro il tetto di 300.000 € in tre anni.</p>}
      </div>
      {lines.length > 0 && (
        <div className="overflow-x-auto">
          <p className="label">Che cosa paga nel piano</p>
          <table className="w-full min-w-[360px]"><thead><tr className="text-left text-mute"><th className="font-medium py-1">Spesa</th><th className="font-medium text-right">Importo</th><th className="font-medium text-right">Coperto</th><th className="font-medium text-right">%</th></tr></thead>
            <tbody>{lines.slice(0, 8).map(({ l, c }) => <tr key={l.item_id} className="border-t border-line"><td className="py-1 pr-2">{l.label || l.category}</td><td className="text-right tabular-nums">{fmtEur(l.gross_amount_eur)}</td><td className="text-right tabular-nums text-emerald-700">{fmtEur(c.covered_amount_eur)}</td><td className="text-right tabular-nums">{fmtNum(c.coverage_percentage, 0)}%</td></tr>)}</tbody></table>
          {lines.length > 8 && <p className="text-[11px] text-mute mt-1">…e altre {lines.length - 8} voci.</p>}
        </div>
      )}
      {e?.assumptions?.length > 0 && <div>{e.assumptions.map((a, i) => <p key={i}>• {a}</p>)}</div>}
      {e?.evidence?.length > 0 && (
        <div><p className="label">Dal testo ufficiale</p>{e.evidence.slice(0, 3).map((x, i) => <p key={i} className="text-mute">«{x.text}»{x.url && <> · <a href={x.url} target="_blank" rel="noreferrer" className="underline inline-flex items-center gap-0.5">fonte<ExternalLink className="w-3 h-3" /></a></>}</p>)}</div>
      )}
      {r.notes?.filter((n) => !n.startsWith('Il bando non dichiara')).map((n) => <p key={n} className="text-mute">• {n}</p>)}
    </div>
  )
}

/** Tutto ciò che serve per decidere e fare domanda di un'agevolazione sul lavoro: condizioni rispettate, chi assumere, dichiarazioni, cumulo, procedura, legge e fonte. */
export function MeasureDetails({ m }) {
  return (
    <div className="space-y-3 text-xs text-ink-2 leading-relaxed">
      <div>
        <p className="label">Le caratteristiche per cui vale per questa impresa</p>
        {m.ok.length === 0 && m.to_check.length === 0 && <p>Nessuna condizione sull’impresa da verificare.</p>}
        {m.ok.map((w) => <p key={w} className="text-emerald-700 flex gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 mt-0.5 shrink-0" />{w}</p>)}
        {m.to_check.map((c) => <p key={c.label} className="text-amber-700 flex gap-1.5"><CircleHelp className="w-3.5 h-3.5 mt-0.5 shrink-0" />Da chiarire: {c.label}</p>)}
        {m.why_not.map((w) => <p key={w} className="text-red-700 flex gap-1.5"><AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />{w}</p>)}
      </div>
      <div><p className="label">Chi assumere</p><ul className="list-disc pl-4 space-y-0.5">{m.worker.map((w) => <li key={w}>{w}</li>)}</ul><p className="mt-1"><span className="font-medium text-ink">Contratto:</span> {m.contract} <span className="font-medium text-ink">Periodo:</span> {m.period}</p></div>
      <div><p className="label">Dichiarazioni e condizioni sull’impresa</p><ul className="list-disc pl-4 space-y-0.5">{m.company.map((w) => <li key={w}>{w}</li>)}</ul></div>
      <div><p className="label">Cumulo e aiuti di Stato</p><p>{m.cumulation} {m.aid}</p></div>
      <div><p className="label">Come si ottiene</p><p>{m.how}</p></div>
      <p className="text-[11px] text-mute">Fonte e norma: {m.source.label} · {VERIFIED[m.verified] || m.verified}</p>
    </div>
  )
}

function Expand({ label, children }) {
  const [open, setOpen] = useState(false)
  return (
    <div>
      <button type="button" onClick={() => setOpen(!open)} aria-expanded={open} className="inline-flex items-center gap-1 text-xs text-sky-700 hover:underline"><ChevronDown className={`w-3.5 h-3.5 transition ${open ? 'rotate-180' : ''}`} />{open ? 'Nascondi' : label}</button>
      {open && <div className="mt-2 rounded-xl bg-white border border-line p-3">{children}</div>}
    </div>
  )
}

/** Le agevolazioni sul lavoro scelte: quante assunzioni le usano, quanto valgono al massimo, se entrano nel totale e perché sì o no. */
export function MeasuresPanel({ sel, onHires, onRemove, onGoAgevolazioni, suggestions = [], onAdd, defaultHires }) {
  const items = sel?.items || []
  return (
    <div className="space-y-3">
      <Note>Sono le agevolazioni scelte dalla pagina Agevolazioni (o da qui sotto). Non sono bandi e non hanno un budget: si applicano in busta paga. Valgono per ogni nuova assunzione e si sommano al totale solo se non manca nessun dato decisivo; per ogni persona conta un solo esonero, il più ricco (persone diverse possono usarne di diversi).</Note>
      {items.length === 0 && <p className="text-sm text-ink-2">Nessuna agevolazione scelta. Indica nella pagina Agevolazioni chi assume l’impresa{suggestions.length ? ' oppure scegline una da qui sotto' : ''}.</p>}
      <ul className="space-y-3">
        {items.map((m) => (
          <li key={m.id} className="rounded-2xl bg-tint p-4 space-y-2.5">
            <div className="flex flex-wrap items-start gap-2">
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-ink">{m.name}</p>
                <p className="text-xs text-ink-2 leading-snug">{m.tagline}</p>
              </div>
              <span className={`px-2 py-0.5 rounded-full text-[11px] font-medium ${m.counted ? 'bg-emerald-500/15 text-emerald-700' : 'bg-amber-500/15 text-amber-700'}`}>{m.counted ? 'Nel totale' : 'Non nel totale'}</span>
            </div>
            <div className="flex flex-wrap items-end gap-x-6 gap-y-2">
              {m.assigned
                ? <div><span className="label">Persone</span><div className="text-sm font-medium text-ink">{m.hires} {m.hires === 1 ? 'persona' : 'persone'}<span className="block text-[11px] font-normal text-mute">scelte nella pagina Agevolazioni</span></div></div>
                : <div><span className="label">Assunzioni</span>
                  <div className="flex items-center gap-2"><button className="btn !px-2 !py-0.5" aria-label="Meno assunzioni" disabled={m.hires <= 1} onClick={() => onHires(m.id, m.hires - 1)}>−</button><span className="w-5 text-center text-sm tabular-nums">{m.hires}</span><button className="btn !px-2 !py-0.5" aria-label="Più assunzioni" onClick={() => onHires(m.id, m.hires + 1)}>+</button></div></div>}
              <div><span className="label">Valore massimo</span><div className="text-lg font-display font-semibold text-emerald-700 tabular-nums">{m.max_eur == null ? '—' : fmtEur(m.max_eur)}</div></div>
              {m.value?.text && <div className="text-xs text-ink-2 max-w-xs"><span className="label">Come si calcola</span><br />{m.exact ? `tetto mensile × i mesi di ogni persona (${m.value.cap_month_eur} € al mese)` : `${m.value.text} per ogni assunzione × ${m.hires}`}</div>}
              <button className="btn !py-1 ml-auto" onClick={() => onRemove(m.id)}>Togli</button>
            </div>
            {!m.counted && m.reason && <p className="text-xs text-amber-700 leading-snug">{m.reason}</p>}
            <Expand label="Condizioni, dichiarazioni, norma e come si ottiene"><MeasureDetails m={m} /></Expand>
          </li>
        ))}
      </ul>
      {items.length > 0 && <p className="text-[11px] text-mute">{sel.warning}</p>}
      {suggestions.length > 0 && (
        <div className="space-y-1.5 pt-1">
          <p className="text-xs font-medium text-ink">Altre agevolazioni adatte alle assunzioni previste{defaultHires ? ` (${defaultHires})` : ''}</p>
          <ul className="space-y-1.5">{suggestions.map((s) => (
            <li key={s.id} className="flex flex-wrap items-center gap-2 text-xs text-ink-2"><span className="font-medium text-ink">{s.name}</span><span className="text-emerald-700">fino a {fmtEur(s.value.max_eur)} a persona</span>{s.status === 'DA_VERIFICARE' && <span className="text-amber-700">da verificare</span>}<button className="btn !py-0.5 ml-auto" onClick={() => onAdd(s.id)}>Usa questa</button></li>
          ))}</ul>
        </div>
      )}
      <button className="text-xs underline text-ink-2" onClick={onGoAgevolazioni}>Tutte le agevolazioni</button>
    </div>
  )
}

/** Il totale e da dove viene: bandi dell'anno, bandi a progetto e agevolazioni sul lavoro, ognuno con importo, quota del totale, percentuale applicata e il perché della scelta. */
export function TotalPanel({ annual, project, sel, year, projectSummable = true }) {
  const rows = []
  const fundRows = (kind, side) => {
    if (!side?.plan) return
    const gross = side.plan.total_gross_expense_eur || 0
    side.plan.fund_usage.filter((u) => u.used_eur > 0).forEach((u) => {
      const r = (side.rows || []).find((x) => x.fund?.fund_id === u.fund_id)
      if (!r) return
      rows.push({ key: `${kind}-${u.fund_id}`, kind, noun: r.mode?.noun, name: r.name, issuer: r.issuer, amount: u.used_eur, pctSpese: gross ? (u.used_eur / gross) * 100 : null, rate: r.estimate ? `${fmtNum(r.estimate.rate_pct, 0)}%${r.estimate.rate_high_pct > r.estimate.rate_pct ? `–${fmtNum(r.estimate.rate_high_pct, 0)}%` : ''} delle spese ammissibili` : 'tetto del bando', base: kind === 'PROJECT' ? `spese nuove di «${side.title}»` : `spese del ${year}`, why: <BandoWhy r={r} plan={side.plan} />, summable: kind !== 'PROJECT' || projectSummable })
    })
  }
  fundRows('ANNUAL', annual)
  fundRows('PROJECT', project)
  const counted = (sel?.items || []).filter((m) => m.counted)
  counted.forEach((m) => rows.push({ key: `M-${m.id}`, kind: 'MISURA', name: m.name, issuer: m.source.label, amount: m.max_eur, pctSpese: null, rate: m.exact ? `${m.tagline} (${m.value.cap_month_eur} € al mese per i mesi di ogni persona)` : (m.value?.text ? `${m.tagline} (${m.value.text} per assunzione)` : m.tagline), base: `costo del lavoro di ${m.hires} ${m.hires === 1 ? 'assunzione' : 'assunzioni'}`, why: <MeasureDetails m={m} />, summable: true }))
  const total = rows.filter((r) => r.summable).reduce((s, r) => s + r.amount, 0)
  const byKind = Object.fromEntries(['ANNUAL', 'PROJECT', 'MISURA'].map((k) => [k, rows.filter((r) => r.kind === k && r.summable).reduce((s, r) => s + r.amount, 0)]))
  const usedA = Object.fromEntries((annual?.plan?.fund_usage || []).map((u) => [u.fund_id, u.used_eur]))
  const idle = (annual?.plan?.fund_usage || []).filter((u) => !(u.used_eur > 0)).map((u) => (annual.rows || []).find((x) => x.fund?.fund_id === u.fund_id)).filter(Boolean).map((r) => ({ name: r.name, ...idleReason(r, annual.rows || [], usedA) }))
  const skipped = (sel?.items || []).filter((m) => !m.counted)
  if (rows.length === 0) return <p className="text-sm text-ink-2">Il totale compare quando c’è almeno un bando adatto incluso nel piano o un’agevolazione scelta.</p>
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-x-8 gap-y-2">
        <div><span className="label">Totale agevolato (massimo)</span><div className="text-3xl font-display font-semibold text-emerald-700 tabular-nums">{fmtEur(total)}</div></div>
        {Object.entries(byKind).filter(([, v]) => v > 0).map(([k, v]) => <div key={k}><span className="label">{HEAD[k]}</span><div className="text-sm font-semibold tabular-nums">{fmtEur(v)} <span className="text-mute font-normal">· {fmtNum((v / total) * 100, 0)}%</span></div></div>)}
      </div>
      <div className="flex w-full h-3 rounded-md overflow-hidden bg-tint-2" role="img" aria-label="Quota del totale per origine">
        {Object.entries(byKind).filter(([, v]) => v > 0).map(([k, v]) => <div key={k} title={`${HEAD[k]}: ${fmtEur(v)}`} style={{ width: `${(v / total) * 100}%`, background: ORIGIN[k][2] }} />)}
      </div>
      <Note>Ogni riga è una fonte di contributo e il colore dice di che tipo è: sulle spese dell’anno (un bando o un’agevolazione senza budget), un bando a progetto o un’agevolazione sul lavoro. «Quota» è la parte del totale; «percentuale» è quanto copre sulle spese su cui si calcola. Apri una riga per vedere perché è stata scelta e quali criteri soddisfa.</Note>
      <div className="space-y-2">
        {rows.map((r) => (
          <div key={r.key} className={`rounded-2xl bg-tint p-3.5 space-y-2 ${r.summable ? '' : 'opacity-70'}`}>
            <div className="flex flex-wrap items-start gap-2">
              <div className="min-w-0 flex-1"><p className="text-sm font-semibold text-ink break-words">{r.name}</p><p className="text-[11px] text-mute">{r.issuer}</p></div>
              <span className={`px-2 py-0.5 rounded-full text-[11px] font-medium ${ORIGIN[r.kind][1]}`}>{r.noun === 'agevolazione' ? 'Agevolazione · senza budget' : ORIGIN[r.kind][0]}</span>
            </div>
            <div className="flex flex-wrap items-end gap-x-6 gap-y-1 text-xs text-ink-2">
              <div><span className="label">{r.noun === 'agevolazione' ? 'Valore' : 'Contributo'}</span><div className="text-base font-semibold text-emerald-700 tabular-nums">{fmtEur(r.amount)}</div></div>
              <div><span className="label">Quota del totale</span><div className="text-sm font-semibold tabular-nums text-ink">{r.summable && total ? `${fmtNum((r.amount / total) * 100, 1)}%` : 'non sommato'}</div></div>
              {r.pctSpese != null && <div><span className="label">Sulle spese del piano</span><div className="text-sm font-semibold tabular-nums text-ink">{fmtNum(r.pctSpese, 1)}%</div></div>}
              <div className="min-w-0 max-w-sm"><span className="label">Percentuale applicata</span><div className="text-ink">{r.rate}</div></div>
              <div className="min-w-0 max-w-xs"><span className="label">Si calcola su</span><div className="text-ink">{r.base}</div></div>
            </div>
            {!r.summable && <p className="text-[11px] text-amber-700">Non sommato al totale: il progetto include anche le spese correnti, già contate nelle spese dell’anno.</p>}
            <Expand label="Perché è stato scelto e quali criteri soddisfa">{r.why}</Expand>
          </div>
        ))}
      </div>
      {idle.length > 0 && (
        <div className="space-y-1.5 text-xs text-ink-2 leading-relaxed">
          <p className="font-medium text-ink">Inclusi nel piano ma non necessari (valgono 0 € nel totale)</p>
          {idle.map((x) => <p key={x.name}><span className="font-medium text-ink">{x.name}.</span> {x.why}{x.when ? ` ${x.when}` : ''}</p>)}
        </div>
      )}
      {skipped.length > 0 && <p className="text-xs text-amber-700 leading-relaxed"><span className="font-medium">Agevolazioni scelte ma non sommate:</span> {skipped.map((m) => `${m.name} (${m.reason})`).join(' · ')}</p>}
    </div>
  )
}
