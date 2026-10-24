import React from 'react'
import { useWords } from '../lib/words'
import { fmtEur, fmtNum, CATEGORY_LABEL } from '../lib/format'

/** Piccoli grafici per le intestazioni dei passi dell'allocazione: usano solo numeri già calcolati (profilo, stima, piano), nessun calcolo nuovo. */

const GREEN = '#10b981', AMBER = '#f59e0b', RED = '#ef4444', VIOLET = '#8b5cf6', GREY = '#a3a39a', SKY = '#38bdf8'

function Legend({ items }) {
  return (
    <div className="flex flex-wrap gap-x-3 gap-y-1 text-[10.5px] text-ink-2">
      {items.map(([c, l]) => <span key={l} className="inline-flex items-center gap-1.5"><i className="w-2.5 h-2.5 rounded-sm" style={{ background: c }} />{l}</span>)}
    </div>
  )
}

function Stack({ parts, height = 14 }) {
  const total = parts.reduce((s, p) => s + Math.max(0, p.v), 0) || 1
  return (
    <div className="flex w-full rounded-md overflow-hidden bg-tint-2" style={{ height }} role="img" aria-label={parts.map((p) => `${p.l}: ${fmtEur(p.v)}`).join(', ')}>
      {parts.map((p) => p.v > 0 && <div key={p.l} title={`${p.l}: ${p.money ? fmtEur(p.v) : p.v}`} style={{ width: `${(p.v / total) * 100}%`, background: p.c }} />)}
    </div>
  )
}

function Hbar({ label, value, max, color, right }) {
  return (
    <div className="flex items-center gap-2 text-[11px]">
      <span className="w-28 shrink-0 truncate text-ink-2" title={label}>{label}</span>
      <div className="flex-1 h-2.5 rounded bg-tint-2 overflow-hidden"><div className="h-full rounded" style={{ width: `${Math.max(1.5, (Math.max(0, value) / (max || 1)) * 100)}%`, background: color }} /></div>
      <span className="w-24 text-right tabular-nums text-mute">{right}</span>
    </div>
  )
}

/** Passo 1 · quanto è completo il profilo. */
export function ProfileChart({ ov }) {
  const w = useWords()
  if (!ov) return null
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-[11px] text-ink-2"><span>Completezza del profilo</span><span className="font-semibold text-ink tabular-nums">{ov.completeness_pct}%</span></div>
      <Stack parts={[{ v: ov.completeness_pct, c: GREEN, l: 'Compilato' }, { v: 100 - ov.completeness_pct, c: 'transparent', l: 'Da inserire' }]} />
      <p className="text-[11px] text-mute">{ov.missing.length ? `${ov.missing.length} ${ov.missing.length === 1 ? 'dato da inserire' : 'dati da inserire'}` : 'Nessun dato mancante'} · {w.last} {ov.last_year ?? '—'}</p>
    </div>
  )
}

/** Passo 2 · spese per categoria: ultimo bilancio contro stima dell'anno. */
export function ForecastChart({ forecast }) {
  const w = useWords()
  if (!forecast) return null
  const rows = [...forecast.categories].sort((a, b) => b.forecast_eur - a.forecast_eur)
  const max = Math.max(...rows.map((r) => Math.max(r.baseline_eur, r.forecast_eur)), 1)
  return (
    <div className="space-y-1.5">
      {rows.map((r) => (
        <div key={r.category} className="flex items-center gap-2 text-[11px]">
          <span className="w-28 shrink-0 truncate text-ink-2" title={r.label}>{r.label}</span>
          <div className="flex-1 space-y-0.5">
            <div className="h-1.5 rounded bg-tint-2 overflow-hidden"><div className="h-full" style={{ width: `${(r.baseline_eur / max) * 100}%`, background: GREY }} /></div>
            <div className="h-1.5 rounded bg-tint-2 overflow-hidden"><div className="h-full" style={{ width: `${(r.forecast_eur / max) * 100}%`, background: AMBER }} /></div>
          </div>
          <span className="w-24 text-right tabular-nums text-mute">{fmtEur(r.forecast_eur)}</span>
        </div>
      ))}
      <Legend items={[[GREY, `${w.cap} ${forecast.base_year}`], [AMBER, `Stima ${forecast.fiscal_year}`]]} />
    </div>
  )
}

/** Passo 3 · quanti bandi sono adatti e i contributi stimati più alti. */
export function BandiChart({ match }) {
  if (!match) return null
  const s = match.matching.summary
  const top = match.matching.results.filter((r) => r.estimate && r.fit !== 'NON_ADATTO').sort((a, b) => b.estimate.covered_eur - a.estimate.covered_eur).slice(0, 4)
  const max = Math.max(...top.map((r) => r.estimate.covered_eur), 1)
  return (
    <div className="space-y-2">
      <Stack parts={[{ v: s.ADATTO, c: GREEN, l: 'Adatti' }, { v: s.DA_VERIFICARE, c: AMBER, l: 'Da verificare' }, { v: s.NON_ADATTO, c: RED, l: 'Non adatti' }]} />
      <Legend items={[[GREEN, `${s.ADATTO} adatti`], [AMBER, `${s.DA_VERIFICARE} da verificare`], [RED, `${s.NON_ADATTO} non adatti`]]} />
      {top.length > 0 && <div className="space-y-1 pt-1">{top.map((r) => <Hbar key={r.bando_id} label={r.name} value={r.estimate.covered_eur} max={max} color={GREEN} right={fmtEur(r.estimate.covered_eur)} />)}</div>}
    </div>
  )
}

/** Passo 4 · quanto copre il piano, da quali bandi e quanto del tetto de minimis. */
export function PotentialChart({ plan, nameOf, dm }) {
  if (!plan) return null
  const used = plan.fund_usage.filter((u) => u.used_eur > 0).sort((a, b) => b.used_eur - a.used_eur).slice(0, 4)
  const max = Math.max(...used.map((u) => u.used_eur), 1)
  const est = dm?.estimate
  return (
    <div className="space-y-2">
      <Stack parts={[{ v: plan.covered_by_public_funds_eur, c: GREEN, l: 'Coperto dai bandi', money: true }, { v: plan.net_cost_to_entity_eur, c: AMBER, l: 'A carico', money: true }]} />
      <Legend items={[[GREEN, `Coperto ${fmtEur(plan.covered_by_public_funds_eur)} (${fmtNum(plan.overall_coverage_percentage, 1)}%)`], [AMBER, `A carico ${fmtEur(plan.net_cost_to_entity_eur)}`]]} />
      {used.length > 0 && <div className="space-y-1 pt-1">{used.map((u) => <Hbar key={u.fund_id} label={nameOf?.(u.fund_id) || u.fund_id} value={u.used_eur} max={max} color={SKY} right={fmtEur(u.used_eur)} />)}</div>}
      {est && plan.de_minimis_residual_eur != null && (
        <div className="pt-1 space-y-1">
          <div className="text-[11px] text-ink-2">Tetto de minimis (300.000 €)</div>
          <Stack height={10} parts={[{ v: est.received_eur, c: GREY, l: 'Già ricevuto', money: true }, { v: plan.de_minimis_used_eur, c: VIOLET, l: 'Usato dal piano', money: true }, { v: Math.max(0, 300000 - est.received_eur - plan.de_minimis_used_eur), c: 'transparent', l: 'Libero', money: true }]} />
          <Legend items={[[GREY, `già ricevuto ${fmtEur(est.received_eur)}`], [VIOLET, `piano ${fmtEur(plan.de_minimis_used_eur)}`]]} />
        </div>
      )}
    </div>
  )
}

/** Passo 5 · il piano mese per mese e le voci principali. */
export function PlanChart({ plan }) {
  if (!plan) return null
  const maxM = Math.max(...plan.monthly_plan.map((m) => m.gross_eur), 1)
  const cats = {}
  plan.allocation_plan.forEach((i) => { cats[i.category] = (cats[i.category] || 0) + i.gross_amount_eur })
  return (
    <div className="space-y-2">
      <div className="flex items-end gap-1 h-16">
        {plan.monthly_plan.map((m) => (
          <div key={m.month} className="flex-1 flex flex-col justify-end h-full" title={`Mese ${m.month}: ${fmtEur(m.gross_eur)} (coperto ${fmtEur(m.covered_eur)})`}>
            <div style={{ height: `${(m.net_eur / maxM) * 100}%`, background: AMBER, opacity: 0.75 }} />
            <div style={{ height: `${(m.covered_eur / maxM) * 100}%`, background: GREEN, opacity: 0.75 }} />
          </div>
        ))}
      </div>
      <div className="flex justify-between text-[10px] text-mute font-mono"><span>Gen</span><span>Dic</span></div>
      <Legend items={[[GREEN, 'coperto dai bandi'], [AMBER, 'a carico']]} />
      <p className="text-[11px] text-mute">{Object.entries(cats).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([c, v]) => `${CATEGORY_LABEL[c] || c} ${fmtEur(v)}`).join(' · ')}</p>
    </div>
  )
}
