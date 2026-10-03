import React, { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import { fmtEur, fmtNum, CATEGORY_LABEL } from '../lib/format'
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronRight, CircleHelp, Loader2, XCircle } from 'lucide-react'
import { ChromeCard, SectionTitle } from './ui'
import Guide from './Guide'
import { Hint } from './Help'

const PALETTE = ['#38bdf8', '#a78bfa', '#f472b6', '#34d399', '#fbbf24', '#fb7185']

/** Flusso delle spese verso i fondi: lo spessore è proporzionale all'importo coperto (dati del solver, nessun calcolo qui). */
function Sankey({ plan }) {
  const items = plan.allocation_plan
  const funds = plan.fund_usage.filter((f) => f.used_eur > 0)
  const gross = items.reduce((s, i) => s + i.gross_amount_eur, 0) || 1
  const W = 700, H = Math.max(240, items.length * 46), gap = 10, X0 = 150, X1 = W - 170
  const scale = (H - gap * Math.max(items.length, funds.length + 1)) / gross
  const leftY = {}
  let y = 0
  items.forEach((i) => { leftY[i.item_id] = y; y += i.gross_amount_eur * scale + gap })
  const rightNodes = [...funds.map((f, k) => ({ id: f.fund_id, total: f.used_eur, color: PALETTE[k % PALETTE.length] })),
    { id: 'CARICO ENTE', total: plan.net_cost_to_entity_eur, color: '#f59e0b' }]
  const rightY = {}
  y = 0
  rightNodes.forEach((n) => { rightY[n.id] = y; y += n.total * scale + gap })
  const offL = {}, offR = {}
  const links = []
  items.forEach((i) => {
    const parts = [...i.coverage.map((c) => ({ to: c.fund_id, amount: c.covered_amount_eur })), { to: 'CARICO ENTE', amount: i.net_cost_to_entity_eur }].filter((p) => p.amount > 0)
    parts.forEach((p) => {
      const h = p.amount * scale
      const y0 = leftY[i.item_id] + (offL[i.item_id] || 0), y1 = rightY[p.to] + (offR[p.to] || 0)
      offL[i.item_id] = (offL[i.item_id] || 0) + h; offR[p.to] = (offR[p.to] || 0) + h
      const node = rightNodes.find((n) => n.id === p.to)
      links.push(<path key={`${i.item_id}-${p.to}`} d={`M${X0},${y0 + h / 2} C${(X0 + X1) / 2},${y0 + h / 2} ${(X0 + X1) / 2},${y1 + h / 2} ${X1},${y1 + h / 2}`} stroke={node?.color || '#a3a39a'} strokeOpacity="0.45" strokeWidth={Math.max(1, h)} fill="none"><title>{`${i.item_id} → ${p.to}: ${fmtEur(p.amount)}`}</title></path>)
    })
  })
  return (
    <div className="overflow-x-auto"><svg width={W} height={H + 10} role="img" aria-label="Flusso delle spese verso i fondi">
      {links}
      {items.map((i) => <g key={i.item_id}><rect x={X0 - 6} y={leftY[i.item_id]} width="6" height={Math.max(2, i.gross_amount_eur * scale)} fill="#8a8a80" /><text x={X0 - 12} y={leftY[i.item_id] + Math.max(2, i.gross_amount_eur * scale) / 2 + 3} fontSize="11" fontFamily="Now, Outfit, sans-serif" textAnchor="end" fill="#45453d">{i.item_id}</text></g>)}
      {rightNodes.map((n) => <g key={n.id}><rect x={X1} y={rightY[n.id]} width="6" height={Math.max(2, n.total * scale)} fill={n.color} /><text x={X1 + 12} y={rightY[n.id] + Math.max(2, n.total * scale) / 2 + 3} fontSize="11" fontFamily="Now, Outfit, sans-serif" fill="#45453d">{n.id.length > 22 ? `${n.id.slice(0, 21)}…` : n.id}</text></g>)}
    </svg></div>
  )
}

const TARGETS = [
  ['MINIMIZE_NET_COST', 'Pagare il meno possibile di tasca propria'],
  ['MAXIMIZE_COVERED_ITEMS', 'Coprire più spese possibile'],
  ['MINIMIZE_FUNDS_INVOLVED', 'Usare meno fondi possibile'],
]

const FIT = {
  ADATTO: ['Adatto', 'bg-emerald-500/15 text-emerald-700 border-emerald-500/30'],
  DA_VERIFICARE: ['Da verificare', 'bg-amber-500/15 text-amber-700 border-amber-500/30'],
  NON_ADATTO: ['Non adatto', 'bg-red-500/10 text-red-700 border-red-500/30'],
}
const CHECK_ICON = { OK: [CheckCircle2, 'text-emerald-700'], FAIL: [XCircle, 'text-red-700'], UNKNOWN: [CircleHelp, 'text-amber-700'] }
const MISSING_LABEL = { region: 'la regione della sede', ateco_code: 'il codice ATECO', is_innovative_startup: 'se sei una start-up innovativa' }

function Step({ n, title, sub, children, done }) {
  return (
    <ChromeCard label={`quanto.app/allocazione/${n}`} bodyClassName="p-6 space-y-4">
      <div className="pb-3 border-b border-line flex items-start gap-3">
        <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 ${done ? 'bg-emerald-500/20 text-emerald-700' : 'bg-tint-2 text-ink-2'}`}>{done ? <CheckCircle2 className="w-4 h-4" /> : n}</span>
        <div className="min-w-0"><SectionTitle className="!text-lg">{title}</SectionTitle>{sub && <p className="text-xs text-ink-2 mt-0.5 leading-relaxed max-w-2xl">{sub}</p>}</div>
      </div>
      {children}
    </ChromeCard>
  )
}

function BandoCard({ r, picked, onToggle, onBudget }) {
  const [open, setOpen] = useState(false)
  const [fit, tone] = FIT[r.fit]
  const e = r.estimate
  return (
    <div className={`rounded-2xl border p-4 space-y-3 ${picked ? 'border-brand/60 bg-brand/5' : 'border-line bg-field'}`}>
      <div className="flex flex-wrap items-start gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-ink break-words">{r.name}</p>
          <p className="text-[11px] text-mute">{r.issuer || 'Ente non indicato'} · {r.bando_id}</p>
        </div>
        <span className={`px-2 py-0.5 text-[11px] font-medium rounded border ${tone}`}>{fit}</span>
      </div>

      {e ? (
        <div className="flex flex-wrap items-end gap-x-6 gap-y-2">
          <div><span className="label">Contributo stimato</span><div className="text-lg font-display font-semibold text-emerald-700 tabular-nums">{fmtEur(e.covered_eur)}</div></div>
          <div><span className="label">Aliquota del bando</span><div className="text-sm font-semibold tabular-nums">{fmtNum(e.rate_pct, 1)}%</div></div>
          <div><span className="label">Sul totale delle tue spese</span><div className="text-sm font-semibold tabular-nums">{fmtNum(e.covered_pct_of_total, 1)}%</div></div>
        </div>
      ) : <p className="text-xs text-amber-700">{r.notes.find((n) => n.startsWith('Il bando non dichiara')) || 'Il beneficio non si può quantificare in automatico.'}</p>}

      {e && e.adjustments.length > 0 && (
        <div className="p-3 rounded-xl border border-amber-500/30 bg-amber-500/5 text-xs space-y-1">
          <p className="font-medium text-amber-700 inline-flex items-center gap-1.5"><AlertTriangle className="w-3.5 h-3.5" />Per rientrare nei tetti del bando</p>
          {e.adjustments.map((a) => (
            <p key={a.category} className="text-ink-2 leading-relaxed">{a.reason}: dei tuoi {fmtEur(a.forecast_eur)} di {a.label.toLowerCase()} ne sono ammissibili {fmtEur(a.eligible_eur)}. Porta la voce a {fmtEur(a.eligible_eur)} (−{fmtEur(a.over_cap_eur)}) e rientra nel tetto.</p>
          ))}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2">
        {r.fund && r.fit !== 'NON_ADATTO' && <label className="inline-flex items-center gap-2 text-xs font-medium cursor-pointer"><input type="checkbox" checked={picked} onChange={onToggle} />Includi nel piano</label>}
        <button className="btn !py-1" onClick={() => onBudget(r.bando_id)}>Bozza di budget per questo bando</button>
        <button className="btn !py-1 ml-auto" onClick={() => setOpen(!open)}>{open ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}Dettagli</button>
      </div>

      {open && (
        <div className="space-y-3 text-xs pt-2 border-t border-line">
          <ul className="space-y-1.5">
            {r.checks.map((c) => { const [Icon, color] = CHECK_ICON[c.result]; return <li key={c.id} className="flex gap-2"><Icon className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${color}`} /><span className="text-ink-2"><span className="font-medium text-ink">{c.label}:</span> {c.detail}</span></li> })}
          </ul>
          {e && (
            <table className="w-full"><thead><tr className="text-left text-mute"><th className="font-medium py-1">Spesa</th><th className="font-medium text-right">Prevista</th><th className="font-medium text-right">Ammissibile</th><th className="font-medium text-right">Contributo</th></tr></thead>
              <tbody>{e.by_category.map((c) => (
                <tr key={c.category} className="border-t border-line"><td className="py-1 text-ink-2">{c.label}{c.note ? <span className="block text-[10px] text-mute">{c.note}</span> : null}</td>
                  <td className="text-right tabular-nums">{fmtEur(c.forecast_eur)}</td><td className="text-right tabular-nums">{fmtEur(c.eligible_eur)}</td><td className="text-right tabular-nums text-emerald-700">{fmtEur(c.covered_eur)}</td></tr>))}</tbody></table>
          )}
          {r.notes.filter((n) => !n.startsWith('Il bando non dichiara')).map((n) => <p key={n} className="text-mute">• {n}</p>)}
          {r.missing_profile.length > 0 && <p className="text-amber-700">Per decidere servono ancora: {r.missing_profile.map((m) => MISSING_LABEL[m] || m).join(', ')}.</p>}
          <p className="text-[11px] text-mute">{r.rules_count} regole e {r.requirements_count} requisiti letti dal bando. Stima basata solo su ciò che il bando dichiara: l’esito dipende dall’istruttoria.</p>
        </div>
      )}
    </div>
  )
}

export default function AllocationView({ onGoProfile, onBudgetFrom }) {
  const [ov, setOv] = useState(null)
  const [year, setYear] = useState(new Date().getFullYear() + 1)
  const [growth, setGrowth] = useState({})                 // % per categoria, scelta dall'utente
  const [match, setMatch] = useState(null)                 // {forecast, matching}
  const [matching, setMatching] = useState(false)
  const [tab, setTab] = useState('ADATTO')
  const [picked, setPicked] = useState([])
  const [target, setTarget] = useState('MINIMIZE_NET_COST')
  const [deMinimis, setDeMinimis] = useState('')
  const [plan, setPlan] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [planError, setPlanError] = useState(null)
  const seq = useRef(0)

  useEffect(() => { api.profile().then(setOv).catch((e) => setError(e.message)) }, [])

  const growthBody = useCallback(() => Object.fromEntries(Object.entries(growth).filter(([, v]) => v !== '' && !Number.isNaN(Number(v))).map(([k, v]) => [k, Number(v) / 100])), [growth])

  const estimate = async () => {
    setMatching(true); setError(null); setPlan(null); setPicked([])
    try {
      const sent = growthBody()
      const res = await api.profileMatch(Number(year), sent)
      setMatch({ ...res, growthSent: sent })
      setTab(res.matching.summary.ADATTO ? 'ADATTO' : res.matching.summary.DA_VERIFICARE ? 'DA_VERIFICARE' : 'NON_ADATTO')
    } catch (e) { setError(e.message); setMatch(null) } finally { setMatching(false) }
  }

  const pickedRows = (match?.matching.results || []).filter((r) => picked.includes(r.bando_id) && r.fund)
  const needsDeMinimis = pickedRows.some((r) => r.fund.de_minimis)

  // Il piano si ricalcola da solo a ogni scelta (bandi inclusi, obiettivo, de minimis): il calcolo è sul server.
  const run = useCallback(async () => {
    if (!match || pickedRows.length === 0) { setPlan(null); setPlanError(null); return }
    if (needsDeMinimis && deMinimis === '') { setPlan(null); setPlanError('Uno dei bandi scelti è in de minimis: indica quanto plafond ti resta nel triennio.'); return }
    const mine = ++seq.current
    setLoading(true); setPlanError(null)
    try {
      const res = await api.optimizeAllocation({ fiscal_year: match.forecast.fiscal_year, use_profile_forecast: true, growth_pct: match.growthSent, optimization_target: target,
        available_funding_lines: pickedRows.map((r) => r.fund), ...(needsDeMinimis ? { de_minimis_residual_eur: Number(deMinimis) } : {}) })
      if (mine === seq.current) setPlan(res)
    } catch (e) { if (mine === seq.current) { setPlanError(e.message); setPlan(null) } } finally { if (mine === seq.current) setLoading(false) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [match, picked, target, deMinimis])
  useEffect(() => { run() }, [run])

  const toggle = (id) => setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]))
  const maxMonth = plan ? Math.max(...plan.monthly_plan.map((m) => m.gross_eur), 1) : 1
  const hasData = ov && ov.last_year != null
  const results = match?.matching.results || []
  const shown = results.filter((r) => r.fit === tab)

  return (
    <div className="space-y-6">
      <Guide page="allocation" />

      <Step n={1} title="I dati della tua azienda" done={!!hasData && ov.missing.length === 0}
        sub="Il punto di partenza sono i bilanci e i documenti che hai caricato nel Profilo. Quello che manca lo completi lì: QUANTO non inventa nessun dato.">
        {!ov && !error && <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Carico il profilo…</p>}
        {ov && (
          <div className="flex flex-wrap items-center gap-x-8 gap-y-3">
            <div><span className="label">Completezza del profilo</span><div className="text-2xl font-display font-semibold tabular-nums">{ov.completeness_pct}%</div></div>
            <div><span className="label">Ultimo bilancio</span><div className="text-sm font-semibold">{ov.last_year ?? 'nessuno'}</div></div>
            <div><span className="label">Dimensione</span><div className="text-sm font-semibold">{ov.size ? ov.size.label : 'da indicare'}</div></div>
            <div><span className="label">Documenti</span><div className="text-sm font-semibold">{ov.documents.total}{ov.documents.to_review ? ` · ${ov.documents.to_review} campi da verificare` : ''}</div></div>
            <button className="btn-primary ml-auto" onClick={onGoProfile}>{ov.missing.length ? 'Completa il profilo' : 'Apri il profilo'}</button>
          </div>
        )}
        {ov && ov.missing.length > 0 && (
          <div className="p-3 rounded-xl border border-amber-500/30 bg-amber-500/5 text-xs text-ink-2">
            <p className="font-medium text-amber-700 mb-1">Ancora da inserire</p>
            <ul className="list-disc pl-5">{ov.missing.map((m) => <li key={`${m.scope}-${m.key}`}>{m.year ? `${m.label} (esercizio ${m.year})` : m.label}</li>)}</ul>
          </div>
        )}
        {ov && !hasData && <p className="text-xs text-ink-2">Senza un bilancio non si può stimare l’anno successivo: caricalo nel Profilo (o scrivi a mano i costi dell’ultimo esercizio).</p>}
      </Step>

      {hasData && (
        <Step n={2} title="Stima dell’anno successivo" done={!!match}
          sub="Parte dall’ultimo bilancio: le spese di ogni categoria, aumentate o diminuite della variazione che scegli tu. Se non scrivi niente, la stima è uguale all’ultimo bilancio.">
          <div className="flex flex-wrap items-end gap-3">
            <label className="space-y-1 text-xs text-ink-2"><span className="label">Anno da pianificare</span><input type="number" className="field !w-24" value={year} onChange={(e) => setYear(e.target.value)} /></label>
            <button className="btn-primary" disabled={matching || !Number(year)} onClick={estimate}>{matching && <Loader2 className="w-3.5 h-3.5 animate-spin" />}{match ? 'Ricalcola stima e bandi' : 'Calcola la stima e cerca i bandi'}</button>
          </div>
          {match && (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead><tr className="text-left text-mute"><th className="py-1.5 font-medium">Categoria</th><th className="font-medium text-right">Esercizio {match.forecast.base_year}</th><th className="font-medium text-right">Variazione suggerita</th>
                  <th className="font-medium text-right pl-3">Tua variazione annua %</th><th className="font-medium text-right">Stima {match.forecast.fiscal_year}</th></tr></thead>
                <tbody>
                  {match.forecast.categories.map((c) => (
                    <tr key={c.category} className="border-t border-line">
                      <td className="py-2 text-ink-2">{c.label}</td>
                      <td className="text-right tabular-nums">{fmtEur(c.baseline_eur)}</td>
                      <td className="text-right text-mute tabular-nums">{c.suggested_growth != null
                        ? <button className="underline decoration-dotted" title="Dai tuoi due ultimi bilanci: è solo un suggerimento, lo applichi tu" onClick={() => setGrowth((g) => ({ ...g, [c.category]: String(Math.round(c.suggested_growth * 1000) / 10) }))}>{c.suggested_growth > 0 ? '+' : ''}{fmtNum(c.suggested_growth * 100, 1)}%</button> : '—'}</td>
                      <td className="text-right pl-3"><input type="number" step="0.5" className="field !w-24 !py-1 text-right" placeholder="0" aria-label={`Variazione ${c.label}`} value={growth[c.category] ?? ''} onChange={(e) => setGrowth((g) => ({ ...g, [c.category]: e.target.value }))} /></td>
                      <td className="text-right font-semibold tabular-nums">{fmtEur(c.forecast_eur)}</td>
                    </tr>
                  ))}
                  <tr className="border-t border-line-strong font-semibold"><td className="py-2">Totale</td><td className="text-right tabular-nums">{fmtEur(match.forecast.total_baseline_eur)}</td><td /><td /><td className="text-right tabular-nums">{fmtEur(match.forecast.total_forecast_eur)}</td></tr>
                </tbody>
              </table>
              {match.forecast.missing.length > 0 && <p className="text-xs text-amber-700 mt-2">Senza dato nel bilancio {match.forecast.base_year}: {match.forecast.missing.map((m) => m.label.toLowerCase()).join(', ')} (non entrano nella stima).</p>}
              {match.forecast.warnings.map((w) => <p key={w} className="text-xs text-amber-700 mt-1">{w}</p>)}
              <p className="text-[11px] text-mute mt-2">La variazione suggerita è quella tra i tuoi due ultimi bilanci: non viene applicata da sola. Cambia i numeri e premi «Ricalcola».</p>
            </div>
          )}
        </Step>
      )}
      {error && <div className="p-3 rounded-xl border border-red-500/30 text-red-700 text-xs">{error}</div>}

      {match && (
        <Step n={3} title="Bandi adatti alla tua azienda" done={picked.length > 0}
          sub="Per ogni bando studiato da QUANTO: se puoi partecipare, quanto potrebbe coprire sulle tue spese, quali voci vanno ridotte per rispettare i tetti e come rientrarci.">
          <div className="flex flex-wrap items-center gap-2">
            {Object.entries(FIT).map(([k, [label, tone]]) => (
              <button key={k} onClick={() => setTab(k)} aria-pressed={tab === k} className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${tab === k ? tone : 'border-line text-ink-2 hover:border-line-strong'}`}>{label} · {match.matching.summary[k]}</button>
            ))}
          </div>
          {match.matching.unstudied_catalog > 0 && <p className="text-[11px] text-mute">Nel catalogo ci sono altri {match.matching.unstudied_catalog} bandi aperti non ancora studiati: finché QUANTO non ne legge le regole non si possono valutare. Si studiano dalla pagina Bandi.</p>}
          {match.matching.missing_profile.length > 0 && <p className="text-xs text-amber-700">Per valutare meglio alcuni bandi indica nel profilo: {match.matching.missing_profile.map((m) => MISSING_LABEL[m] || m).join(', ')}.</p>}
          {shown.length === 0 && <p className="text-xs text-mute">Nessun bando in questa categoria.</p>}
          <div className="grid lg:grid-cols-2 gap-4">{shown.map((r) => <BandoCard key={r.bando_id} r={r} picked={picked.includes(r.bando_id)} onToggle={() => toggle(r.bando_id)} onBudget={onBudgetFrom} />)}</div>
        </Step>
      )}

      {match && picked.length > 0 && (
        <Step n={4} title="Il piano dell’anno" done={!!plan}
          sub="Con i bandi che hai incluso, il programma prova le combinazioni possibili e sceglie la migliore, rispettando i tetti dei fondi, i limiti per categoria, i fondi non cumulabili e il de minimis.">
          <div className="flex flex-wrap items-end gap-3">
            <label className="flex items-center gap-2 text-xs text-ink-2">Obiettivo <Hint id="alloc_obiettivo" />
              <select value={target} onChange={(e) => setTarget(e.target.value)} className="field !w-full md:!w-auto min-w-0">{TARGETS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>
            {needsDeMinimis && <label className="space-y-1 text-xs text-ink-2"><span className="label">De minimis residuo (€)</span><input type="number" className="field !w-32" value={deMinimis} onChange={(e) => setDeMinimis(e.target.value)} /></label>}
            <span className="text-xs text-mute">{pickedRows.length} {pickedRows.length === 1 ? 'bando incluso' : 'bandi inclusi'}</span>
          </div>
          {planError && <div className="p-3 rounded-xl border border-red-500/30 text-red-700 text-xs">{planError}</div>}
        </Step>
      )}

      {plan && (
        <>
          <div className={`grid grid-cols-2 md:grid-cols-4 gap-4 transition ${loading ? 'opacity-50' : ''}`}>
            {[['Spesa totale', fmtEur(plan.total_gross_expense_eur), 'text-ink'],
              ['Coperta dai fondi', fmtEur(plan.covered_by_public_funds_eur), 'text-emerald-700'],
              ['A carico dell’ente', fmtEur(plan.net_cost_to_entity_eur), 'text-amber-700'],
              ['Quota coperta', `${fmtNum(plan.overall_coverage_percentage, 1)}%`, 'text-brand-ink']].map(([l, v, tone]) => (
              <div key={l} className="card p-5 min-w-0"><span className="label">{l}</span><div className={`text-lg sm:text-xl font-semibold mt-2 whitespace-nowrap tabular-nums tracking-tight ${tone}`}>{v}</div></div>
            ))}
          </div>

          <div className="card p-6 space-y-3"><span className="label inline-flex items-center gap-1.5">Da dove arrivano i soldi, spesa per spesa <Hint id="alloc_flusso" /></span><Sankey plan={plan} /></div>

          <div className="grid lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 card p-6 space-y-3">
              <span className="label">Il piano, voce per voce</span>
              {plan.allocation_plan.map((l) => (
                <div key={l.item_id} className="p-4 bg-field border border-line rounded-xl text-xs space-y-2">
                  <div className="flex justify-between gap-3 font-mono"><span className="font-medium text-sm font-sans min-w-0 break-words">{CATEGORY_LABEL[l.category] || l.category} <span className="text-mute">· {l.item_id}</span></span><span>{fmtEur(l.gross_amount_eur)}</span></div>
                  {l.coverage.length ? l.coverage.map((c) => (
                    <div key={c.fund_id} className="flex justify-between gap-3 text-emerald-700 font-mono"><span className="min-w-0 break-words">{c.fund_id}</span><span className="shrink-0">{fmtEur(c.covered_amount_eur)} ({fmtNum(c.coverage_percentage, 1)}%)</span></div>
                  )) : <div className="text-mute">Nessun bando adatto: la paga direttamente l’ente</div>}
                  <div className="flex justify-between text-amber-700 font-mono border-t border-line pt-2"><span>A carico dell’ente</span><span>{fmtEur(l.net_cost_to_entity_eur)}</span></div>
                </div>
              ))}
            </div>

            <div className="space-y-6">
              <div className="card p-6 space-y-3">
                <span className="label inline-flex items-center gap-1.5">Quanto si usa di ogni bando <Hint id="alloc_uso" /></span>
                {plan.fund_usage.map((u) => (
                  <div key={u.fund_id} className="text-xs font-mono space-y-0.5">
                    <div className="flex justify-between gap-3"><span className="text-ink-2 min-w-0 break-words">{u.fund_id}</span><span>{fmtEur(u.used_eur)}</span></div>
                    <div className="text-mute">{u.cap_eur != null ? `disponibili ${fmtEur(u.cap_eur)} · margine ${fmtNum(u.safety_margin_pct, 1)}%` : 'nessun limite di importo'}</div>
                  </div>
                ))}
                {plan.de_minimis_residual_eur != null && (
                  <div className="text-xs font-mono pt-2 border-t border-line text-ink-2">De minimis usato {fmtEur(plan.de_minimis_used_eur)} · ancora disponibile {fmtEur(plan.de_minimis_residual_eur)}</div>
                )}
              </div>
              <div className="card p-6 space-y-2">
                <span className="label inline-flex items-center gap-1.5">Mese per mese <Hint id="alloc_mesi" /></span>
                <div className="flex items-end gap-1 h-28">
                  {plan.monthly_plan.map((m) => (
                    <div key={m.month} className="flex-1 flex flex-col justify-end h-full" title={`Mese ${m.month}: totale ${fmtEur(m.gross_eur)}, coperto ${fmtEur(m.covered_eur)}`}>
                      <div className="bg-amber-400/70" style={{ height: `${(m.net_eur / maxMonth) * 100}%` }} />
                      <div className="bg-emerald-400/70" style={{ height: `${(m.covered_eur / maxMonth) * 100}%` }} />
                    </div>
                  ))}
                </div>
                <div className="flex justify-between text-[11px] text-mute font-mono"><span>Gen</span><span>Dic</span></div>
                <p className="text-[11px] text-mute"><span className="text-emerald-700">■</span> coperto dai fondi <span className="text-amber-700 ml-2">■</span> a carico dell’ente</p>
              </div>
            </div>
          </div>
          <p className="text-[11px] text-mute font-mono break-words">Dettagli tecnici: {plan.summary} · {plan.solver} · {plan.status}</p>
        </>
      )}
    </div>
  )
}
