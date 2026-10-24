import React, { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import { fmtEur, fmtNum, CATEGORY_LABEL, STATUS_LABEL, STATUS_STYLE } from '../lib/format'
import { nextStep } from '../lib/profileSteps'
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronRight, CircleHelp, ExternalLink, FolderOpen, Loader2, Sparkles, XCircle } from 'lucide-react'
import { CostConfirm, fmtTok } from './Tokens'
import { Info } from './ui'
import HowItWorks from './HowItWorks'
import TutorialVideo from './TutorialVideo'
import { flashTo, useNav } from '../lib/nav'
import Guide from './Guide'
import PipelineButton from './PipelineButton'
import { Hint } from './Help'
import ForecastStep from './ForecastStep'
import PotentialStep from './PotentialStep'
import ProjectIdeas from './ProjectIdeas'
import { BandiChart, ForecastChart, PlanChart, PotentialChart, ProfileChart } from './StepCharts'

const PALETTE = ['#38bdf8', '#a78bfa', '#f472b6', '#34d399', '#fbbf24', '#fb7185', '#2dd4bf', '#818cf8', '#f97316', '#84cc16', '#e879f9', '#94a3b8']

/** Flusso delle spese verso i fondi: lo spessore è proporzionale all'importo coperto (dati del solver, nessun calcolo qui). */
function Sankey({ plan }) {
  const items = plan.allocation_plan
  const allFunds = plan.fund_usage.map((f) => f.fund_id)
  const funds = plan.fund_usage.filter((f) => f.used_eur > 0)
  const gross = items.reduce((s, i) => s + i.gross_amount_eur, 0) || 1
  const W = 760, H = Math.max(240, items.length * 30), gap = 6, X0 = 200, X1 = W - 170
  const scale = (H - gap * Math.max(items.length, funds.length + 1)) / gross
  const leftY = {}
  let y = 0
  items.forEach((i) => { leftY[i.item_id] = y; y += i.gross_amount_eur * scale + gap })
  const rightNodes = [...funds.map((f) => ({ id: f.fund_id, total: f.used_eur, color: PALETTE[allFunds.indexOf(f.fund_id) % PALETTE.length] })),
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
      links.push(<path key={`${i.item_id}-${p.to}`} d={`M${X0},${y0 + h / 2} C${(X0 + X1) / 2},${y0 + h / 2} ${(X0 + X1) / 2},${y1 + h / 2} ${X1},${y1 + h / 2}`} stroke={node?.color || '#a3a39a'} strokeOpacity="0.45" strokeWidth={Math.max(1, h)} fill="none"><title>{`${i.label || i.item_id} → ${p.to}: ${fmtEur(p.amount)}`}</title></path>)
    })
  })
  return (
    <div className="overflow-x-auto"><svg width={W} height={H + 10} role="img" aria-label="Flusso delle spese verso i fondi">
      {links}
      {items.map((i) => <g key={i.item_id}><rect x={X0 - 6} y={leftY[i.item_id]} width="6" height={Math.max(2, i.gross_amount_eur * scale)} fill="#8a8a80" /><text x={X0 - 12} y={leftY[i.item_id] + Math.max(2, i.gross_amount_eur * scale) / 2 + 3} fontSize="11" fontFamily="Now, Outfit, sans-serif" textAnchor="end" fill="#45453d">{(i.label || i.item_id).length > 24 ? `${(i.label || i.item_id).slice(0, 23)}…` : (i.label || i.item_id)}</text></g>)}
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

const AFFINITY = { ALTA: ['Molto affine', 'bg-emerald-500/15 text-emerald-700 border-emerald-500/30'], MEDIA: ['Affine', 'bg-sky-500/15 text-sky-700 border-sky-500/30'], BASSA: ['Poco affine', 'bg-ink/10 text-ink-2 border-line-strong'] }

/** Voce del catalogo non ancora studiata: descrizione ufficiale e motivi dell'affinità; se serve, la si studia con il processo standard. */
function CatalogCard({ it, onStudied }) {
  const [label, tone] = AFFINITY[it.affinity]
  return (
    <div className="rounded-2xl border border-line bg-field p-4 space-y-2.5">
      <div className="flex flex-wrap items-start gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-ink break-words">{it.name}</p>
          <p className="text-[11px] text-mute">{it.issuer || 'Ente non indicato'}{it.deadline && it.deadline !== 'non indicata' ? ` · scade il ${it.deadline.split('-').reverse().join('/')}` : ''}{it.state === 'IN_ARRIVO' && it.opens ? ` · apre il ${it.opens.split('-').reverse().join('/')}` : ''}</p>
        </div>
        <span className={`px-2 py-0.5 text-[11px] font-medium rounded border ${tone}`}>{label}</span>
      </div>
      {it.summary && <p className="text-xs text-ink-2 leading-relaxed">{it.summary}</p>}
      <div className="flex flex-wrap gap-1.5 text-[11px]">
        {(it.form || []).map((f) => <span key={f} className="px-1.5 py-0.5 rounded border border-line-strong text-ink-2">{f}</span>)}
        {it.benefit_range && <span className="px-1.5 py-0.5 rounded border border-emerald-500/30 text-emerald-700">Agevolazione: {it.benefit_range}</span>}
      </div>
      {it.reasons.length > 0 && <ul className="text-xs text-ink-2 space-y-0.5">{it.reasons.map((r) => <li key={r} className="flex gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 mt-0.5 text-emerald-600 shrink-0" />{r}</li>)}</ul>}
      {it.to_check.length > 0 && <p className="text-[11px] text-amber-700">Da verificare: {it.to_check.join(', ')}.</p>}
      <div className="flex flex-wrap items-start gap-3 pt-1">
        <PipelineButton bandoId={it.bando_id} label="Studia a fondo questo bando" onDone={(r) => onStudied(it, r)} />
        {it.source_url && <a href={it.source_url} target="_blank" rel="noreferrer" className="text-xs text-sky-700 hover:underline inline-flex items-center gap-1 pt-2"><ExternalLink className="w-3 h-3" />Scheda ufficiale</a>}
      </div>
    </div>
  )
}

/** Bandi del catalogo (letti in breve) la cui scheda ammette le spese del progetto scelto: non hanno ancora un importo, si studiano a fondo per portarli nel piano. */
function ProjectCandidates({ items, onStudied }) {
  if (!items.length) return null
  return (
    <div className="rounded-2xl bg-tint p-4 space-y-3">
      <div>
        <p className="text-sm font-semibold text-ink">Altri bandi che potrebbero finanziarlo</p>
        <p className="text-xs text-ink-2 mt-0.5 leading-relaxed">Dal catalogo: la scheda ufficiale ammette le spese di questo progetto. Non sono ancora studiati a fondo, quindi non hanno un importo: studiali per portarli nel piano.</p>
      </div>
      <ul className="space-y-2">
        {items.map((it) => (
          <li key={it.bando_id} className="rounded-xl bg-white p-3 space-y-2">
            <div className="flex flex-wrap items-start gap-2"><p className="text-sm font-medium text-ink flex-1 min-w-0 break-words">{it.name}</p><span className={`px-2 py-0.5 text-[11px] font-medium rounded-full border ${AFFINITY[it.affinity][1]}`}>{AFFINITY[it.affinity][0]}</span></div>
            {it.benefit_range && <p className="text-[11px] text-emerald-700">Agevolazione: {it.benefit_range}</p>}
            <PipelineButton bandoId={it.bando_id} label="Studia a fondo" onDone={(r) => onStudied(it, r)} />
          </li>
        ))}
      </ul>
    </div>
  )
}

/** Un passo dell'allocazione: titolo e una riga di riassunto; il resto si apre a richiesta. La spiegazione sta dietro la «i». */
function Step({ id, title, info, summary, chart, alert, children, done, open, onToggle }) {
  return (
    <section id={id} className="card overflow-hidden scroll-mt-20">
      <button type="button" onClick={onToggle} aria-expanded={!!open} className="w-full flex items-center gap-3 px-6 py-4 text-left">
        <span className={`w-2 h-2 rounded-full shrink-0 ${done ? 'bg-emerald-500' : 'bg-line-strong'}`} aria-hidden="true" />
        <span className="min-w-0 flex-1">
          <span className="block text-[15px] font-semibold tracking-tight text-ink">{title}</span>
          {summary && <span className="block text-sm text-ink-2 mt-0.5 leading-snug">{summary}</span>}
        </span>
        <ChevronDown className={`w-4 h-4 text-mute shrink-0 transition ${open ? 'rotate-180' : ''}`} />
      </button>
      <div className={open ? 'px-6 pb-6 pt-4 space-y-4 border-t border-line' : 'hidden'}>
        {alert && <div className="p-3 rounded-xl border border-red-500/30 text-red-700 text-xs">{alert}</div>}
        {info && <Info>{info}</Info>}
        {chart && <div className="max-w-xl">{chart}</div>}
        {children}
      </div>
    </section>
  )
}


/** Il percorso dall'azienda al budget, in una riga: dove sei, cosa viene dopo e un tasto per andarci. Ogni passo si apre solo se serve. */
const DEPT_ORDER = [['COMMERCIALE', 'Marketing e vendite'], ['TECNICO', 'Tecnici e ingegneri'], ['PRODUZIONE', 'Produzione e operai'], ['MAGAZZINO', 'Magazzino e logistica'], ['AMMINISTRAZIONE', 'Amministrazione'], ['IT', 'Informatica e digitale']]

function Journey({ stages, onGo }) {
  const next = stages.find((x) => !x.done && !x.off)
  return (
    <div className="card p-5 space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-[15px] font-semibold tracking-tight">Dall’azienda al budget, passo dopo passo</p>
          <p className="text-sm text-ink-2 mt-0.5">QUANTO parte dai bisogni dell’azienda, legge tutti i bandi, sceglie quelli che li finanziano e ne ricava un budget per ognuno. Tocca un passo per aprirlo.</p>
        </div>
        {next && <button className="btn-primary" onClick={() => onGo(next.go)}>{next.cta}</button>}
      </div>
      <ol className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
        {stages.map((x, i) => (
          <li key={x.id}>
            <button onClick={() => onGo(x.go)} className={`w-full h-full text-left rounded-2xl px-3 py-2.5 transition ${x === next ? 'bg-ink text-white' : x.off ? 'bg-tint/60 text-mute' : 'bg-tint hover:bg-tint-2'}`}>
              <span className="flex items-center gap-1.5 text-[12px] font-medium">
                <span className={`w-4 h-4 rounded-full inline-flex items-center justify-center text-[10px] font-semibold shrink-0 ${x.done ? 'bg-emerald-500 text-white' : x === next ? 'bg-white text-ink' : 'bg-white text-mute'}`}>{x.done ? '✓' : i + 1}</span>{x.title}
              </span>
              <span className={`block text-[11px] mt-1 leading-snug ${x === next ? 'text-white/80' : 'text-ink-2'}`}>{x.line}</span>
            </button>
          </li>
        ))}
      </ol>
    </div>
  )
}

const CROSS = { PASS: [CheckCircle2, 'text-emerald-700'], FAIL: [XCircle, 'text-red-700'], WARN: [AlertTriangle, 'text-amber-700'] }

/** Dall'allocazione ai budget: un budget per ogni bando che copre una parte delle spese, controllato con i 60 criteri del suo bando e verificato insieme agli altri. */
function BudgetsFromPlan({ plan, lines, onOpen }) {
  const [res, setRes] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  useEffect(() => { setRes(null); setError(null) }, [plan])
  const build = async () => {
    setBusy(true); setError(null)
    try { setRes(await api.allocationBudgets({ allocation: plan, fiscal_year: plan.fiscal_year, funding_lines: lines })) } catch (e) { setError(e.message); setRes(null) } finally { setBusy(false) }
  }
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <button className="btn-primary" disabled={busy} onClick={build}>{busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FolderOpen className="w-3.5 h-3.5" />}{res ? 'Ricrea i budget' : 'Crea i budget dei bandi'}</button>
        {res && res.budgets.length > 0 && <button className="btn" onClick={() => onOpen(res, res.budgets[0].fund_id)}>Apri i budget nella pagina Budget</button>}
      </div>
      {error && <p className="text-xs text-red-700">{error}</p>}
      {res && (
        <>
          <div className="space-y-2">
            <p className="text-sm font-medium text-ink">{res.ok ? 'I budget stanno bene insieme.' : 'Attenzione: ci sono incompatibilità tra i budget.'}</p>
            <ul className="space-y-1.5">
              {res.cross_checks.map((c) => { const [Icon, color] = CROSS[c.status] || CROSS.WARN; return <li key={c.key} className="flex gap-2 text-xs"><Icon className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${color}`} /><span className="text-ink-2"><span className="font-medium text-ink">{c.label}.</span> {c.detail}</span></li> })}
            </ul>
          </div>
          <div className="grid lg:grid-cols-2 gap-4">
            {res.budgets.map((b) => {
              const v = b.validation
              const people = b.cost_items.filter((i) => i.category === 'PERSONNEL').length
              return (
                <div key={b.fund_id} className="rounded-2xl border border-line bg-field p-4 space-y-2.5 text-xs">
                  <div className="flex items-start gap-2"><div className="min-w-0 flex-1"><p className="text-sm font-semibold text-ink break-words">{b.name}</p><p className="text-[11px] text-mute">{b.bando_id} · intensità {fmtNum(b.rate_pct, 1)}%</p></div></div>
                  <div className="flex flex-wrap gap-x-6 gap-y-1.5">
                    <div><span className="label">Contributo previsto</span><div className="text-base font-semibold text-emerald-700 tabular-nums">{fmtEur(b.contribution_planned_eur)}</div></div>
                    <div><span className="label">Costi nel budget</span><div className="text-sm font-semibold tabular-nums">{fmtEur(v?.requested_eur ?? b.cost_items.reduce((s, i) => s + (i.amount_eur || 0), 0))}</div></div>
                    {v && !v.error && <div><span className="label">Ammessi dal motore</span><div className="text-sm font-semibold tabular-nums">{fmtEur(v.approved_eur)}</div></div>}
                  </div>
                  <p className="text-ink-2">{b.cost_items.length} voci{people ? `, di cui ${people} persone con il loro tempo` : ''}.</p>
                  {v?.error && <p className="text-amber-700">{v.error}</p>}
                  {v && !v.error && <div className="flex flex-wrap gap-1.5">{Object.entries(v.by_status).map(([k, n]) => <span key={k} className={`px-1.5 py-0.5 rounded border ${STATUS_STYLE[k]}`}>{n} {STATUS_LABEL[k]?.toLowerCase()}</span>)}</div>}
                  {v && !v.error && v.problems.length > 0 && (
                    <ul className="text-[11px] text-amber-700 space-y-0.5">{v.problems.slice(0, 3).map((p) => <li key={p.item_id}>• {p.description.slice(0, 60)}: {p.reason || STATUS_LABEL[p.status]}</li>)}{v.problems.length > 3 && <li className="text-mute">…e altre {v.problems.length - 3}: aprile nella pagina Budget.</li>}</ul>
                  )}
                  <button className="btn !py-1" onClick={() => onOpen(res, b.fund_id)}><FolderOpen className="w-3 h-3" />Apri questo budget</button>
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}

const REALITY_FIELDS = [['probability_pct', 'Probabilità di successo (%)', 'es. 60'], ['admin_cost_eur', 'Costo di istruttoria (€)', 'ore interne e spese'], ['fee_pct', 'Consulente: % sul concesso', 'anche 0'],
  ['reimbursement_lag_months', 'Mesi per il rimborso', 'dal bando'], ['advance_pct', 'Anticipo (%)', 'dal bando']]

/** Dall'allocazione alla realtà: quanto si può contare sul contributo, quanto costa ottenerlo, quando entrano i soldi e cosa si somma ad altri aiuti. Le ipotesi le scrive chi conosce il caso: nulla è inventato. */
function RealityPanel({ plan, lines }) {
  const [assume, setAssume] = useState({})
  const [res, setRes] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const run = useCallback(async (a) => {
    setBusy(true); setError(null)
    try {
      const clean = {}
      Object.entries(a).forEach(([f, v]) => { clean[f] = {}; Object.entries(v).forEach(([k, x]) => { if (x !== '' && x != null) clean[f][k] = Number(x) }) })
      setRes(await api.allocationReality({ allocation: plan, fiscal_year: plan.fiscal_year, assumptions: clean, funding_lines: lines }))
    } catch (e) { setError(e.message); setRes(null) } finally { setBusy(false) }
  }, [plan, lines])
  useEffect(() => { setAssume({}); setRes(null); run({}) }, [plan, run])
  useEffect(() => {      // i valori che arrivano dal bando riempiono i campi, senza sovrascrivere ciò che l'utente ha scritto
    if (!res) return
    setAssume((cur) => { const n = { ...cur }; res.funds.forEach((f) => { n[f.fund_id] = { ...Object.fromEntries(Object.entries(f.assumptions).filter(([k, v]) => v != null && f.origin[k] === 'dal bando')), ...(cur[f.fund_id] || {}) } }); return n })
  }, [res])
  const set = (fid, k, v) => setAssume((a) => ({ ...a, [fid]: { ...(a[fid] || {}), [k]: v } }))
  const t = res?.totals
  const cash = res?.cash
  const maxCum = cash ? Math.max(1, ...cash.rows.map((r) => Math.abs(r.cumulative_eur))) : 1
  return (
    <div className="space-y-4">
      {error && <p className="text-xs text-red-700">{error}</p>}
      {res && (
        <>
          <div className="space-y-3">
            {res.funds.map((f) => (
              <div key={f.fund_id} className="rounded-2xl border border-line bg-field p-4 space-y-2.5 text-xs">
                <div className="flex flex-wrap items-baseline gap-2"><p className="text-sm font-semibold text-ink">{f.name}</p><span className="text-mute">contributo previsto {fmtEur(f.covered_eur)}</span></div>
                <div className="grid sm:grid-cols-3 lg:grid-cols-5 gap-2">
                  {REALITY_FIELDS.map(([k, label, ph]) => (
                    <label key={k} className="space-y-1"><span className="label">{label}</span>
                      <input className="field !py-1" inputMode="decimal" placeholder={ph} value={assume[f.fund_id]?.[k] ?? ''} onChange={(e) => set(f.fund_id, k, e.target.value)} />
                      {f.origin[k] === 'dal bando' && String(assume[f.fund_id]?.[k]) === String(f.assumptions[k]) && <span className="text-[10px] text-mute">letto dal bando</span>}</label>
                  ))}
                </div>
                <p className={f.worth_it === false ? 'text-amber-700' : 'text-ink-2'}>{f.message}</p>
                {f.break_even_probability_pct != null && <p className="text-[11px] text-mute">Conviene se la probabilità di successo supera il {fmtNum(f.break_even_probability_pct, 1)}%.</p>}
              </div>
            ))}
            <button className="btn-primary" disabled={busy} onClick={() => run(assume)}>{busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}Calcola con queste ipotesi</button>
          </div>
          {t && (
            <div className="flex flex-wrap gap-x-8 gap-y-2">
              <div><span className="label">Contributi nominali</span><div className="text-base font-semibold tabular-nums">{fmtEur(t.nominal_eur)}</div></div>
              <div><span className="label">Valore atteso</span><div className="text-base font-semibold tabular-nums text-emerald-700">{t.expected_eur == null ? '—' : fmtEur(t.expected_eur)}</div></div>
              <div><span className="label">Netto di consulente e istruttoria</span><div className="text-base font-semibold tabular-nums">{t.net_expected_eur == null ? '—' : fmtEur(t.net_expected_eur)}</div></div>
              {!t.complete && <p className="text-[11px] text-mute max-w-sm">I totali realistici compaiono quando tutte le ipotesi di tutti i bandi sono compilate: {t.funds_rated} su {t.funds} pronti.</p>}
            </div>
          )}
          {cash && cash.rows.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-ink">Quando entrano i soldi</p>
              <p className="text-xs text-ink-2 leading-relaxed">{cash.message} <span className="text-mute">{cash.assumption}</span></p>
              <div className="flex items-end gap-1 h-24" role="img" aria-label="Cassa cumulata mese per mese">
                {cash.rows.map((r) => (
                  <div key={r.month} className="flex-1 flex flex-col justify-end h-full min-w-0" title={`Mese ${r.month}: speso ${fmtEur(r.spent_eur)}, incassato ${fmtEur(r.received_eur)}, posizione ${fmtEur(r.cumulative_eur)}`}>
                    <div className={`${r.cumulative_eur < 0 ? 'bg-amber-500/70' : 'bg-emerald-500/70'} rounded-sm`} style={{ height: `${Math.max(2, Math.abs(r.cumulative_eur) / maxCum * 100)}%` }} />
                  </div>
                ))}
              </div>
              <div className="flex justify-between text-[10px] text-mute"><span>mese 1</span><span>mese {cash.rows.length}</span></div>
            </div>
          )}
          {res.cumulation.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-sm font-medium text-ink">Altri aiuti da sommare</p>
              {res.cumulation.map((c, i) => <p key={i} className="text-xs text-ink-2 flex gap-1.5"><AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0 text-amber-600" />{c.text}</p>)}
            </div>
          )}
        </>
      )}
      {!res && !error && <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Calcolo…</p>}
    </div>
  )
}

function BandoCard({ r, picked, onToggle, onBudget, includeLabel = 'Includi', scenario = 'ANNUAL', linked = [], onPickProject }) {
  const [open, setOpen] = useState(false)
  const [fit, tone] = FIT[r.fit]
  const e = r.estimate
  const projectOnly = !!r.mode?.needs_project
  const blocked = projectOnly && scenario === 'ANNUAL'                            // un bando a progetto non finanzia le spese annuali: nel piano dell'anno non entra
  return (
    <div className={`rounded-2xl p-4 space-y-3 ${picked ? 'bg-brand/5 ring-1 ring-brand/40' : 'bg-tint'} ${blocked ? 'opacity-95' : ''}`}>
      <div className="space-y-1.5">
        <div className="flex flex-wrap gap-1.5">
          {r.mode && <span title={`Si calcola su ${r.mode.base}`} className="px-2 py-0.5 text-[11px] font-medium rounded-full bg-white text-ink-2">{projectOnly ? 'Per un progetto' : r.mode.label}</span>}
          {r.de_minimis?.applies && <span title={r.de_minimis.evidence[0]?.text} className="px-2 py-0.5 text-[11px] font-medium rounded-full bg-violet-500/10 text-violet-700">De minimis</span>}
          <span className={`px-2 py-0.5 text-[11px] font-medium rounded-full ${tone}`}>{fit}</span>
        </div>
        <p className="text-sm font-semibold text-ink break-words leading-snug">{r.name}</p>
        <p className="text-[11px] text-mute">{r.issuer || 'Ente non indicato'}</p>
      </div>

      {blocked ? (
        <div className="space-y-2">
          <p className="text-sm text-ink-2 leading-snug">Finanzia le spese nuove di un progetto{e ? <>, fino al <span className="font-semibold text-ink tabular-nums">{fmtNum(e.rate_pct, 0)}%</span></> : ''}: non le spese annuali. L’importo si calcola quando scegli un progetto.</p>
          {linked.length > 0
            ? <div className="flex flex-wrap items-center gap-1.5"><span className="text-[11px] text-mute">Progetti possibili:</span>{linked.map((i) => <button key={i.id} className="btn !py-0.5 !text-[11px]" onClick={() => onPickProject(i)}>{i.title}</button>)}</div>
            : <p className="text-[11px] text-mute">Nessuno dei tuoi documenti suggerisce un progetto adatto a questo bando.</p>}
        </div>
      ) : projectOnly && scenario === 'PROJECT' ? (
        <p className="text-sm text-ink-2 leading-snug">{e ? <>Contributo fino al <span className="font-semibold text-ink tabular-nums">{fmtNum(e.rate_pct, 0)}%</span> delle spese del progetto.</> : 'Contributo sulle spese del progetto.'}</p>
      ) : e ? (
        <div className="flex flex-wrap items-end gap-x-6 gap-y-1">
          <div><span className="label">{e.kind_label || 'Contributo stimato'}</span><div className="text-lg font-display font-semibold text-emerald-700 tabular-nums">{fmtEur(e.covered_eur)}{e.covered_high_eur > e.covered_eur + 0.5 && <span className="text-sm text-emerald-700/80"> – {fmtEur(e.covered_high_eur)}</span>}</div></div>
          <div><span className="label">Sulle tue spese</span><div className="text-sm font-semibold tabular-nums">{fmtNum(e.covered_pct_of_total, 1)}%</div></div>
        </div>
      ) : r.guarantee ? (
        <div><span className="label">Importo garantibile</span><div className="text-lg font-display font-semibold text-sky-700 tabular-nums">{fmtEur(r.guarantee.guaranteed_low_eur)} – {fmtEur(r.guarantee.guaranteed_high_eur)}</div></div>
      ) : <p className="text-xs text-amber-700">Nessuna percentuale nei documenti letti: puoi farlo studiare di nuovo.</p>}
      {e && !projectOnly && e.adjustments.length > 0 && <p className="text-[11px] text-amber-700 inline-flex items-center gap-1.5"><AlertTriangle className="w-3.5 h-3.5" />Alcune voci vanno ridotte per rientrare nei tetti (dettagli)</p>}

      <div className="flex flex-wrap items-center gap-2">
        {r.fund && r.fit !== 'NON_ADATTO' && !blocked && <label className="inline-flex items-center gap-2 text-xs font-medium cursor-pointer"><input type="checkbox" checked={picked} onChange={onToggle} />{includeLabel}</label>}
        <button className="btn !py-1 ml-auto" onClick={() => setOpen(!open)}>{open ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}Dettagli</button>
      </div>

      {open && (
        <div className="space-y-3 text-xs pt-2 border-t border-line">
          {e && (e.assumptions?.length > 0 || e.evidence?.length > 0) && (
            <div className="text-[11px] text-ink-2 space-y-1 leading-relaxed">
              {e.assumptions.map((a, i) => <p key={i}>• {a}</p>)}
              {e.evidence.slice(0, 2).map((x, i) => <p key={`ev${i}`} className="text-mute">Dal testo ufficiale: «{x.text}»{x.url && <> · <a href={x.url} target="_blank" rel="noreferrer" className="underline">fonte</a></>}</p>)}
            </div>
          )}
          {!e && r.guarantee && r.guarantee_info && <div className="text-[11px] text-ink-2 space-y-1">{r.guarantee_info.assumptions.map((a, i) => <p key={i}>• {a}</p>)}</div>}
          {e && e.adjustments.length > 0 && (
            <div className="p-3 rounded-xl border border-amber-500/30 bg-amber-500/5 space-y-1">
              <p className="font-medium text-amber-700">Per rientrare nei tetti del bando</p>
              {e.adjustments.map((a) => <p key={a.category} className="text-ink-2 leading-relaxed">{a.reason}: dei tuoi {fmtEur(a.forecast_eur)} di {a.label.toLowerCase()} ne sono ammissibili {fmtEur(a.eligible_eur)}.</p>)}
            </div>
          )}
          <ul className="space-y-1.5">
            {r.checks.map((c) => { const [Icon, color] = CHECK_ICON[c.result]; return <li key={c.id} className="flex gap-2"><Icon className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${color}`} /><span className="text-ink-2"><span className="font-medium text-ink">{c.label}:</span> {c.detail}</span></li> })}
          </ul>
          {e && (
            <table className="w-full"><thead><tr className="text-left text-mute"><th className="font-medium py-1">Spesa</th><th className="font-medium text-right">Prevista</th><th className="font-medium text-right">Ammissibile</th><th className="font-medium text-right">Contributo</th></tr></thead>
              <tbody>{e.by_category.map((c) => (
                <tr key={c.category} className="border-t border-line"><td className="py-1 text-ink-2">{c.label}{c.note ? <span className="block text-[10px] text-mute">{c.note}</span> : null}</td>
                  <td className="text-right tabular-nums">{fmtEur(c.forecast_eur)}</td><td className="text-right tabular-nums">{fmtEur(c.eligible_eur)}</td><td className="text-right tabular-nums text-emerald-700">{fmtEur(c.covered_eur)}</td></tr>))}</tbody></table>
          )}
          {r.de_minimis?.applies && <p className="text-ink-2"><span className="font-medium text-ink">De minimis:</span> conta contro il tetto di 300.000 € in tre anni.</p>}
          {!r.de_minimis?.applies && r.de_minimis?.mentioned && <p className="text-mute">Il testo cita il de minimis ma dice che questo aiuto non rientra: «{r.de_minimis.evidence[0]?.text}»</p>}
          {r.notes.filter((n) => !n.startsWith('Il bando non dichiara')).map((n) => <p key={n} className="text-mute">• {n}</p>)}
          {r.missing_profile.length > 0 && <p className="text-amber-700">Per decidere servono ancora: {r.missing_profile.map((m) => MISSING_LABEL[m] || m).join(', ')}.</p>}
          <div className="flex items-center gap-3 pt-1"><button className="btn !py-1" onClick={() => onBudget(r.bando_id)}>Prepara la bozza di budget per questo bando</button><span className="text-[11px] text-mute">{r.rules_count} regole · {r.requirements_count} requisiti</span></div>
        </div>
      )}
    </div>
  )
}

export default function AllocationView({ onGoProfile, onBudgetFrom, onOpenBudgets }) {
  const goTab = useNav().go
  const [ov, setOv] = useState(null)
  const [year, setYear] = useState(new Date().getFullYear() + 1)
  const [growth, setGrowth] = useState({})                 // percentuali che l'utente ha scritto a mano in questa schermata (le altre arrivano dal modello o dai bilanci)
  const [match, setMatch] = useState(null)                 // {forecast, matching}
  const [matching, setMatching] = useState(false)
  const [tab, setTab] = useState('ADATTO')
  const [picked, setPicked] = useState([])                         // bandi del «Piano dell'anno»
  const [projectPicked, setProjectPicked] = useState([])             // bandi del «Progetto»: le due scelte restano separate
  const [mode, setMode] = useState('ANNUAL')                         // ANNUAL = tutte le spese dell'anno; PROJECT = solo le spese nuove del progetto scelto
  const [openSteps, setOpenSteps] = useState({})
  const [studied, setStudied] = useState(null)
  const [studyingMore, setStudyingMore] = useState(false)
  const [studyNote, setStudyNote] = useState(null)
  const auto = useRef(false)
  const pending = useRef(null)                           // bandi inclusi nel piano al momento dell'ultimo salvataggio
  const allMode = useRef(true)                           // vero finché il piano include TUTTI i bandi adatti: quelli nuovi entrano da soli
  const [restored, setRestored] = useState(false)
  const [target, setTarget] = useState('MINIMIZE_NET_COST')
  const [dmOverride, setDmOverride] = useState('')                    // vuoto = vale la stima di QUANTO (dagli aiuti dichiarati nei bilanci); pieno = il valore scritto dall'utente
  const [plan, setPlan] = useState(null)
  const [planHigh, setPlanHigh] = useState(null)
  const [ideas, setIdeas] = useState(null)                       // le idee di progetto: servono sia alla sezione «Progetti» sia alle schede dei bandi a progetto
  const [ideasError, setIdeasError] = useState(null)
  const [ideasLoading, setIdeasLoading] = useState(false)
  const [deptSplit, setDeptSplit] = useState({})                // reparti dove servono persone, se lo studio li ha scelti (altrimenti si propone la composizione di oggi)
  const [ideasTick, setIdeasTick] = useState(0)
  const splitKey = Object.entries(deptSplit).filter(([, v]) => v > 0).map(([k, v]) => `${k}:${v}`).join(',') || undefined                   // cresce dopo lo studio di un bando: le idee e i bandi che le finanziano si rifanno
  const [includeCurrent, setIncludeCurrent] = useState(false)       // nel progetto scelto: includere anche le spese correnti (dove i bandi scelti le ammettono)
  const [project, setProject] = useState(null)                    // il progetto scelto: nello scenario «Progetto» il piano si calcola sulle sue spese nuove
  const [planLines, setPlanLines] = useState([])                      // le linee di finanziamento con cui è stato calcolato il piano (servono per i budget)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [planError, setPlanError] = useState(null)
  const [confirm, setConfirm] = useState(null)                         // il piano costa token: si mostra il costo e si aspetta la conferma
  const confirmRef = useRef(false)
  const seq = useRef(0)

  useEffect(() => { api.profile().then(setOv).catch((e) => setError(e.message)) }, [])
  // scelte salvate per questo lavoro: anno, percentuali scritte a mano, bandi inclusi, obiettivo, de minimis
  useEffect(() => {
    api.clientState('allocation').then((st) => {
      const v = st.value
      if (v) { if (v.year) setYear(v.year); setGrowth(v.growth || {}); if (v.target) setTarget(v.target); setDmOverride(Number(v.dmOverride) >= 0 ? String(v.dmOverride) : ''); allMode.current = v.allMode ?? false; pending.current = v.allMode ? null : (v.picked || []); if (v.deptSplit) setDeptSplit(v.deptSplit) }
    }).catch(() => {}).finally(() => setRestored(true))
  }, [])
  useEffect(() => {
    if (!restored) return undefined
    const t = setTimeout(() => { api.saveClientState('allocation', { year, growth, picked, target, dmOverride, allMode: allMode.current, deptSplit }).catch(() => {}) }, 800)
    return () => clearTimeout(t)
  }, [restored, year, growth, picked, target, dmOverride, deptSplit])

  const growthBody = useCallback(() => Object.fromEntries(Object.entries(growth).filter(([, v]) => v !== undefined && v !== '' && !Number.isNaN(Number(v))).map(([k, v]) => [k, Number(v) / 100])), [growth])
  const setOverride = (key, v) => setGrowth((g) => { const n = { ...g }; if (v === undefined) delete n[key]; else n[key] = v; return n })

  const runMatch = async () => {
    const sent = growthBody()
    const res = await api.profileMatch(Number(year), sent)
    const full = { ...res, growthSent: sent }
    setMatch(full)
    return full
  }
  const estimate = async () => {
    setMatching(true); setError(null); setPlan(null); setStudied(null)
    try {
      const res = await runMatch()
      const valid = new Set(res.matching.results.filter((r) => r.fund).map((r) => r.bando_id))
      const annualOk = (r) => !r.mode?.needs_project                                       // un bando a progetto non finanzia le spese annuali
      const sure = res.matching.results.filter((r) => r.fit === 'ADATTO' && r.fund && annualOk(r)).map((r) => r.bando_id)
      const annualIds = new Set(res.matching.results.filter((r) => r.fund && annualOk(r)).map((r) => r.bando_id))
      const keep = (allMode.current ? sure : (pending.current ?? picked)).filter((id) => annualIds.has(id))   // piano «tutti i bandi adatti»: segue i bandi nuovi; altrimenti le scelte restano (se ancora valide)
      pending.current = null
      setPicked(keep.filter((id) => valid.has(id)))
      setTab(res.matching.summary.ADATTO ? 'ADATTO' : res.matching.summary.DA_VERIFICARE ? 'DA_VERIFICARE' : 'NON_ADATTO')
    } catch (e) { setError(e.message); setMatch(null) } finally { setMatching(false) }
  }
  // Il modello è cambiato (salvato o eliminato): le percentuali scritte a mano prima non valgono più, si riparte dal modello.
  const templateChanged = async () => { setGrowth({}); setMatching(true); setError(null); setPlan(null); setPicked([]); try { const res = await api.profileMatch(Number(year), {}); setMatch({ ...res, growthSent: {} }) } catch (e) { setError(e.message) } finally { setMatching(false) } }
  // La stima parte da sola appena c'è un bilancio: le percentuali arrivano già compilate, l'utente non deve rifarle.
  useEffect(() => {
    if (ov && ov.last_year != null && restored && !auto.current) { auto.current = true; estimate() }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ov, restored])
  // Dopo lo studio di un bando del catalogo: si ricalcola, si porta l'utente alla scheda dove il bando è finito e si mostra com'è andata la lettura.
  const afterStudy = async (it, r) => {
    try {
      const res = await runMatch()
      setIdeasTick((t) => t + 1)
      const found = res.matching.results.find((x) => x.bando_id === it.bando_id)
      setStudied({ id: it.bando_id, name: found?.name || it.name, report: r?.report, fit: found?.fit, estimate: found?.estimate })
      if (found) setTab(found.fit)
    } catch (e) { setError(e.message) }
  }

  const studyMore = async () => {
    const todo = (match?.matching.catalog.items || []).slice(0, 5)
    if (!todo.length) { setStudyNote('Nessuna scheda del catalogo da studiare ora.'); return }
    setStudyingMore(true); setStudyNote(null)
    const done = []
    try {
      for (let i = 0; i < todo.length; i += 1) {
        setStudyNote(`Studio ${i + 1} di ${todo.length}: ${todo[i].name}`)
        try { const r = await api.researchRun({ bando_id: todo[i].bando_id }); done.push(`${todo[i].name} (${r.report?.status === 'COMPLETA' ? 'lettura completa' : r.report?.status === 'PARZIALE' ? 'lettura parziale' : 'lettura insufficiente'})`) } catch (e) { done.push(`${todo[i].name} (non riuscito: ${e.message})`) }
      }
      await runMatch()
      setIdeasTick((t) => t + 1)
      setStudyNote(`Ho studiato ${done.length} bandi: ${done.join('; ')}. Stima e bandi aggiornati.`)
    } catch (e) { setError(e.message) } finally { setStudyingMore(false) }
  }

  const inProject = mode === 'PROJECT' && !!project
  const active = inProject ? projectPicked : picked
  const pickedRows = (match?.matching.results || []).filter((r) => active.includes(r.bando_id) && r.fund)
  const needsDeMinimis = pickedRows.some((r) => r.fund.de_minimis)
  const dmEstimate = match?.de_minimis || null
  const overrideOk = dmOverride !== '' && Number.isFinite(Number(dmOverride)) && Number(dmOverride) >= 0         // un valore scritto non valido (vuoto, negativo, non numerico) non blocca il piano: vale la stima
  const deMinimis = overrideOk ? String(Number(dmOverride)) : String(dmEstimate ? (dmEstimate.basis === 'RNA' ? dmEstimate.residual_eur : (dmEstimate.safe_residual_eur ?? dmEstimate.residual_eur)) : 270000)  // il valore che usa il piano: se non è verificato sul registro, la stima ridotta del margine di sicurezza; salvo correzione dell'utente

  // Il piano si ricalcola da solo a ogni scelta (bandi inclusi, obiettivo, de minimis): il calcolo è sul server.
  const run = useCallback(async () => {
    if (!match || pickedRows.length === 0) { setPlan(null); setPlanHigh(null); setPlanError(null); return }
    const mine = ++seq.current
    setLoading(true); setPlanError(null)
    const sent = (b) => ({ ...b, ...(confirmRef.current ? { confirm_tokens: true } : {}) })
    try {
      const applied = Object.fromEntries(match.forecast.categories.map((c) => [c.category, c.growth_applied]))                // le stesse percentuali della tabella: il piano parte dalla stessa stima
      // Due contributi a fondo perduto non si sommano sulla stessa spesa (doppio finanziamento, criterio 47): per prudenza ogni voce ne riceve uno solo, il migliore.
      const grants = pickedRows.filter((r) => r.estimate?.kind === 'FONDO_PERDUTO').map((r) => r.fund.fund_id)
      const line = (r, high) => {
        const f = high && r.estimate?.rate_high_pct > r.estimate?.rate_pct
          ? { ...r.fund, coverage_pct: r.estimate.rate_high_pct / 100, max_total_eur: r.estimate.cap_high_eur ?? r.fund.max_total_eur } : r.fund
        return grants.includes(f.fund_id) ? { ...f, excludes: [...new Set([...(f.excludes || []), ...grants.filter((id) => id !== f.fund_id)])] } : f
      }
      const projectLines = inProject ? project.lines.filter((l) => (l.nature === 'NUOVA' || (includeCurrent && l.nature === 'ORDINARIA')) && l.amount_eur > 0).map((l) => ({ item_id: l.item_id, category: l.category, amount_eur: l.amount_eur, expense_type: l.expense_type || undefined, label: l.label })) : null
      const base = projectLines ? { historical_expenses: projectLines } : { use_profile_forecast: true, growth_pct: applied }
      const body = (high) => ({ fiscal_year: match.forecast.fiscal_year, ...base, optimization_target: target,
        available_funding_lines: pickedRows.map((r) => line(r, high)), ...(needsDeMinimis ? { de_minimis_residual_eur: Number(deMinimis) } : {}) })
      const res = await api.optimizeAllocation(sent(body(false)))
      const hasRange = pickedRows.some((r) => r.estimate?.rate_high_pct > r.estimate?.rate_pct)
      const resHigh = hasRange ? await api.optimizeAllocation(sent(body(true))) : null
      if (mine === seq.current) { setConfirm(null); setPlan(res); setPlanHigh(resHigh); setPlanLines(body(false).available_funding_lines) }
    } catch (e) {
      if (mine === seq.current) {
        if (e.status === 409 && e.detail?.code === 'TOKENS_CONFIRM') { setConfirm(e.detail); setPlan(null); setPlanHigh(null) } else { setConfirm(null); setPlanError(e.message); setPlan(null); setPlanHigh(null) }
      }
    } finally { confirmRef.current = false; if (mine === seq.current) setLoading(false) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [match, picked, projectPicked, mode, target, deMinimis, project, includeCurrent])
  useEffect(() => { run() }, [run])
  const declareAid = () => window.dispatchEvent(new CustomEvent('quanto-assistant', { detail: { task: 'deminimis', year: Number(year) } }))
  // L'assistente chiede di ricalcolare (dopo aver salvato dati nel profilo) e aspetta il risultato: lo si comunica quando il piano è pronto.
  const estimateRef = useRef(null)
  estimateRef.current = estimate
  const recalc = useRef({ wanted: false, done: false })
  useEffect(() => {
    const on = (e) => {
      const d = e.detail || {}
      if (d.year) setYear(Number(d.year))
      if (d.allMode) allMode.current = true
      recalc.current = { wanted: true, done: false }
      api.profile().then(setOv).catch(() => {})
      estimateRef.current().finally(() => { recalc.current.done = true; setTick((t) => t + 1) })
    }
    window.addEventListener('quanto-recalc', on)
    return () => window.removeEventListener('quanto-recalc', on)
  }, [])
  const [tick, setTick] = useState(0)
  useEffect(() => {
    const r = recalc.current
    if (!r.wanted || !r.done || matching || loading || !match) return
    if (pickedRows.length > 0 && !plan && !planError && !confirm) return
    r.wanted = false
    window.dispatchEvent(new CustomEvent('quanto-allocation-result', { detail: {
      adatti: match.matching.summary.ADATTO, picked: pickedRows.length, usesDeMinimis: needsDeMinimis, needsTokens: confirm ? confirm.due : 0,
      covered: plan?.covered_by_public_funds_eur ?? 0, coveredHigh: planHigh?.covered_by_public_funds_eur ?? plan?.covered_by_public_funds_eur ?? 0,
      expense: plan?.total_gross_expense_eur ?? 0, net: plan?.net_cost_to_entity_eur ?? 0, coveragePct: plan?.overall_coverage_percentage ?? 0,
      deMinimis: dmEstimate ? { ...dmEstimate, residual_eur: Number(deMinimis), needed_eur: plan?.de_minimis_used_eur ?? 0 } : null } }))
  }, [tick, plan, planHigh, planError, confirm, loading, matching, match])         // eslint-disable-line react-hooks/exhaustive-deps

  const hasData = ov && ov.last_year != null
  const results = match?.matching.results || []
  const shown = results.filter((r) => r.fit === tab)
  useEffect(() => {
    if (!hasData) return undefined
    let live = true
    setIdeasLoading(true); setIdeasError(null)
    api.profileIdeas(year ? Number(year) : undefined, splitKey).then((d) => { if (live) setIdeas(d) }).catch((e) => { if (live) { setIdeasError(e.message); setIdeas(null) } }).finally(() => { if (live) setIdeasLoading(false) })
    return () => { live = false }
  }, [year, hasData, match === null, ideasTick, splitKey])        // eslint-disable-line react-hooks/exhaustive-deps
  const needs = ideas?.needs || null
  const setDept = (id, n) => {                                 // un tocco su − o +: parte dai reparti proposti e cambia solo quello
    const base = Object.keys(deptSplit).length ? { ...deptSplit } : Object.fromEntries((needs?.people?.departments || []).map((d) => [d.id, d.count]))
    const next = { ...base, [id]: Math.max(0, Math.min(50, n)) }
    setDeptSplit(Object.fromEntries(Object.entries(next).filter(([, v]) => v > 0)))
  }
  const growthIdea = (ideas?.ideas || []).find((i) => i.id === 'crescita') || null
  const needsSummary = needs ? (needs.needs.length ? `${needs.needs.map((n) => n.label).join(' e ')} · circa ${fmtEur(needs.total_eur)} l’anno` : (needs.missing.length ? 'Mancano dati per dirlo' : 'Nessun bisogno in più con la crescita prevista')) : (ideasLoading ? 'Calcolo…' : 'Da bilancio e previsione')
  const st = match?.matching.catalog?.stats || null
  useEffect(() => {
    if (!project || !ideas) return
    const fresh = ideas.ideas.find((i) => i.id === project.id)
    if (!fresh || fresh.bandi.length === project.bandi.length) return
    const known = new Set(project.bandi.map((b) => b.bando_id))
    setProject(fresh)
    const added = fresh.bandi.map((b) => b.bando_id).filter((id) => !known.has(id) && (match?.matching.results || []).some((r) => r.bando_id === id && r.fund && r.fit !== 'NON_ADATTO'))
    if (added.length) setProjectPicked((p) => [...new Set([...p, ...added])])
  }, [ideas])        // eslint-disable-line react-hooks/exhaustive-deps
  const ideasByBando = {}
  ;(ideas?.ideas || []).forEach((i) => i.bandi.forEach((b) => { (ideasByBando[b.bando_id] = ideasByBando[b.bando_id] || []).push(i) }))
  const projectBandi = results.filter((r) => r.fund && r.fit !== 'NON_ADATTO' && r.mode?.needs_project)
  const orphans = projectBandi.filter((r) => !(ideasByBando[r.bando_id] || []).length).map((r) => r.name)
  const isCandidate = (r) => (inProject ? (project?.bandi || []).some((b) => b.bando_id === r.bando_id) : !r.mode?.needs_project)
  const openStep = (id, on = true) => setOpenSteps((o) => ({ ...o, [id]: on }))
  const toggleStep = (id) => setOpenSteps((o) => ({ ...o, [id]: !o[id] }))
  const goStep = (id) => { openStep(id); setTimeout(() => flashTo(`al-${id}`), 120) }
  // «Usa questo progetto»: si passa allo scenario «Progetto» con i bandi che lo finanziano; il piano dell'anno e le sue scelte restano com'erano.
  const chooseProject = (idea) => {
    setProject(idea)
    const ids = new Set(idea.bandi.map((b) => b.bando_id))
    setProjectPicked((match?.matching.results || []).filter((r) => r.fund && r.fit !== 'NON_ADATTO' && ids.has(r.bando_id)).map((r) => r.bando_id))
    setMode('PROJECT')
    goStep('risultato')
  }
  const toggle = (id) => {
    if (inProject) setProjectPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]))
    else { allMode.current = false; setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id])) }
  }
  const pick = (ids, all) => { if (inProject) setProjectPicked(ids); else { allMode.current = !!all; setPicked(ids) } }
  const maxMonth = plan ? Math.max(...plan.monthly_plan.map((m) => m.gross_eur), 1) : 1

  const nPlanFunds = plan ? plan.fund_usage.filter((u) => u.used_eur > 0).length : 0
  const scenarioBar = (
    <div className="space-y-2.5">
      <div className="inline-flex rounded-full bg-tint-2 p-0.5" role="tablist" aria-label="Cosa pianificare">
        {[['ANNUAL', 'Spese dell’anno'], ['PROJECT', 'Un progetto']].map(([id, label]) => (
          <button key={id} role="tab" aria-selected={mode === id} onClick={() => { if (id === 'PROJECT' && !project) { goStep('progetti'); return } setMode(id) }}
            className={`px-4 py-1.5 rounded-full text-sm transition ${mode === id ? 'bg-white shadow-sm font-medium text-ink' : 'text-ink-2 hover:text-ink'}`}>{label}</button>
        ))}
      </div>
      <p className="text-sm text-ink-2 leading-snug">
        {inProject
          ? <>«{project.title}»: le sue spese nuove, con i bandi che finanziano progetti come questo. <button className="underline text-ink" onClick={() => goStep('progetti')}>Cambia progetto</button></>
          : mode === 'PROJECT' ? 'Scegli prima un progetto.'
            : <>Le spese previste per il {year}, con i bandi che non chiedono un progetto.{projectBandi.length > 0 && <> I {projectBandi.length} bandi che finanziano progetti sono a parte: <button className="underline text-ink" onClick={() => goStep('progetti')}>scegli un progetto</button>.</>}</>}
      </p>
    </div>
  )

  const stages = [
    { id: 'dati', go: 'dati', title: 'Azienda', done: !!hasData, line: ov ? `Profilo al ${ov.completeness_pct}%` : '…', cta: 'Carica il bilancio' },
    { id: 'stima', go: 'stima', title: 'Stima', done: !!match, off: !hasData, line: match ? `Spese ${year}: ${fmtEur(match.forecast.total_forecast_eur)}` : 'dal bilancio', cta: 'Vedi la stima' },
    { id: 'bisogni', go: 'bisogni', title: 'Bisogni', done: !!needs, off: !hasData, line: needs ? (needs.people?.total ? `${needs.people.total} ${needs.people.total === 1 ? 'persona' : 'persone'}${needs.needs.some((n) => n.kind === 'STRUMENTI') ? ' e strumenti' : ''}` : needs.needs.length ? 'strumenti' : 'nessuno in più') : 'persone e strumenti', cta: 'Vedi cosa serve per crescere' },
    { id: 'bandi', go: 'bandi', title: 'Bandi', done: !!match && (match.matching.summary.ADATTO > 0), off: !match, line: match ? `${match.matching.summary.ADATTO} adatti${st ? ` su ${st.open_total + st.studied} letti` : ''}` : 'tutti letti', cta: 'Guarda i bandi' },
    { id: 'progetti', go: 'progetti', title: 'Progetto', done: !!project || (!!match && projectBandi.length === 0), off: !match, line: project ? project.title : (projectBandi.length ? `${projectBandi.length} bandi a progetto` : 'non serve'), cta: 'Scegli il progetto' },
    { id: 'risultato', go: 'risultato', title: 'Piano', done: !!plan, off: !match, line: plan ? `${fmtEur(plan.covered_by_public_funds_eur)} coperti` : 'chi paga cosa', cta: 'Calcola il piano' },
    { id: 'budget', go: 'budget', title: 'Budget', done: false, off: !plan, line: plan ? `uno per ${nPlanFunds} ${nPlanFunds === 1 ? 'bando' : 'bandi'}` : 'uno per bando', cta: 'Crea i budget dei bandi' },
  ]

  return (
    <div className="space-y-4">
      <Guide page="allocation" />
      <HowItWorks kind="allocation" />
      <Journey stages={stages} onGo={goStep} />

      <Step id="al-dati" title="Azienda" done={!!hasData && ov?.missing.length === 0} open={!!openSteps.dati} onToggle={() => toggleStep('dati')}
        summary={ov ? `Profilo al ${ov.completeness_pct}%${ov.last_year != null ? ` · bilancio ${ov.last_year}` : ' · nessun bilancio'}` : null}
        info="Si parte dai bilanci e dai documenti del Profilo. Quello che manca si completa lì: QUANTO non inventa dati."
        chart={<ProfileChart ov={ov} />}>
        {!ov && !error && <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Carico…</p>}
        {ov && (
          <div className="flex flex-wrap items-center gap-x-8 gap-y-3">
            <div><span className="label">Dimensione</span><div className="text-sm font-semibold">{ov.size ? ov.size.label : 'da indicare'}</div></div>
            <div><span className="label">Documenti</span><div className="text-sm font-semibold">{ov.documents.total}{ov.documents.to_review ? ` · ${ov.documents.to_review} da verificare` : ''}</div></div>
            <div className="ml-auto flex flex-wrap gap-2">
              {(ov.missing.length > 0 || !hasData) && <button className="btn" onClick={() => window.dispatchEvent(new CustomEvent('quanto-assistant', { detail: { task: 'profilo' } }))}><Sparkles className="w-3.5 h-3.5" />Assistente</button>}
              <button className="btn-primary" onClick={() => { const n = nextStep(ov, Array.from({ length: ov.documents.total }, () => ({}))); onGoProfile(n && !n.done ? n.t : { to: 'azienda' }) }}>{ov.missing.length || ov.documents.to_review ? 'Completa il profilo' : 'Apri il profilo'}</button>
            </div>
          </div>
        )}
        {ov && ov.missing.length > 0 && <p className="text-xs text-amber-700">Manca: {ov.missing.map((m) => (m.year ? `${m.label} (${m.year})` : m.label)).join(' · ')}</p>}
        {ov && !hasData && <p className="text-xs text-ink-2">Senza un bilancio non si può stimare l’anno successivo.</p>}
      </Step>

      {hasData && (
        <Step id="al-stima" title={`Stima del ${year}`} done={!!match} open={!!openSteps.stima} onToggle={() => toggleStep('stima')}
          summary={match ? `Spese previste ${fmtEur(match.forecast.total_forecast_eur)} · nel ${match.forecast.base_year} ${fmtEur(match.forecast.total_baseline_eur)}` : (matching ? 'Calcolo…' : null)}
          info="Parte dall’ultimo bilancio: costi e ricavi variano di una percentuale annua. Se hai un modello di previsione uso quello; per le voci senza modello calcolo la variazione dai due ultimi bilanci, con la spiegazione."
          chart={<ForecastChart forecast={match?.forecast} />}>
          <TutorialVideo id="T06" />
          <ForecastStep forecast={match?.forecast} overrides={growth} setOverride={setOverride} year={year} setYear={setYear} matching={matching} onEstimate={estimate} onTemplateChanged={templateChanged} />
        </Step>
      )}
      {error && <div className="p-3 rounded-xl border border-red-500/30 text-red-700 text-xs">{error}</div>}

      {hasData && (
        <Step id="al-bisogni" title="Cosa serve per crescere" done={!!needs} open={!!openSteps.bisogni} onToggle={() => toggleStep('bisogni')} summary={needsSummary}
          info="Dal bilancio e dalla previsione dei ricavi: se l’azienda cresce come previsto, quante persone e quanti strumenti servono in più, a parità di produttività. È un’ipotesi da confermare con l’imprenditore, non una previsione: ogni numero mostra i dati da cui viene, e se un dato manca lo dice.">
          {ideasLoading && !needs && <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Calcolo…</p>}
          {needs && (
            <div className="space-y-5">
              <div className="rounded-2xl bg-tint p-4"><p className="text-[15px] text-ink leading-relaxed">{needs.summary}</p></div>

              {needs.people && (
                <div className="space-y-2">
                  <p className="text-sm font-medium text-ink">In quali reparti servono le persone?</p>
                  <p className="text-xs text-ink-2 leading-relaxed">{needs.people.ask_departments ? 'Indica i reparti: i ruoli già presenti non bastano a proporli.' : needs.people.departments_basis === 'MIX_ATTUALE' ? 'Proposta dalla composizione di oggi (i ruoli del registro del personale). Toccane uno per cambiarla.' : 'Scelti dallo studio.'}</p>
                  <div className="grid sm:grid-cols-3 gap-2">
                    {DEPT_ORDER.map(([id, label]) => {
                      const n = (Object.keys(deptSplit).length ? deptSplit : Object.fromEntries(needs.people.departments.map((d) => [d.id, d.count])))[id] || 0
                      return (
                        <div key={id} className={`rounded-2xl px-3 py-2 flex items-center gap-2 ${n ? 'bg-white border-2 border-ink' : 'bg-tint border border-transparent'}`}>
                          <span className="text-xs text-ink flex-1 min-w-0 leading-tight">{label}</span>
                          <button className="btn !px-2 !py-0.5" aria-label={`Meno ${label}`} disabled={n <= 0} onClick={() => setDept(id, n - 1)}>−</button>
                          <span className="w-5 text-center text-sm tabular-nums">{n}</span>
                          <button className="btn !px-2 !py-0.5" aria-label={`Più ${label}`} onClick={() => setDept(id, n + 1)}>+</button>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {needs.needs.map((n) => (
                <div key={n.kind} className="rounded-2xl bg-tint p-4 space-y-1.5">
                  <div className="flex flex-wrap items-baseline justify-between gap-2"><span className="text-sm font-semibold text-ink">{n.label}</span><span className="text-sm tabular-nums text-ink">{fmtEur(n.amount_eur)} l’anno</span></div>
                  <p className="text-xs text-ink-2 leading-relaxed">{n.basis}</p>
                </div>
              ))}
              {needs.people_message && <p className="text-xs text-ink-2 leading-relaxed">{needs.people_message}</p>}
              {needs.assets_message && <p className="text-xs text-ink-2 leading-relaxed">{needs.assets_message}</p>}
              {needs.missing.map((m) => <p key={m} className="text-xs text-amber-700">{m}</p>)}

              {needs.without_project?.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium text-ink">Senza scrivere nessun progetto</p>
                  <p className="text-xs text-ink-2 leading-relaxed">Esoneri INPS per chi assume. Non si sommano: per ogni assunzione conta il più ricco.</p>
                  <ul className="space-y-2">
                    {needs.without_project.slice(0, 3).map((m) => (
                      <li key={m.id} className="rounded-2xl bg-tint p-3 space-y-0.5">
                        <div className="flex flex-wrap items-baseline justify-between gap-2"><span className="text-sm font-medium text-ink">{m.name}</span><span className="text-sm tabular-nums text-emerald-700">fino a {fmtEur(m.total_max_eur)}</span></div>
                        <p className="text-xs text-ink-2">{m.value.text} a persona. Chi assumere: {m.who[0].replace(/\.$/, '').toLowerCase()}.{m.status === 'DA_VERIFICARE' && m.to_check[0] ? ` Da verificare: ${m.to_check[0].label}` : ''}</p>
                      </li>
                    ))}
                  </ul>
                  <button className="text-xs underline text-ink-2" onClick={() => goTab('agevolazioni')}>Tutte le agevolazioni: tirocini, apprendistato, incentivi regionali…</button>
                </div>
              )}

              {needs.with_project?.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium text-ink">Con un nuovo progetto</p>
                  <p className="text-xs text-ink-2 leading-relaxed">Un bando finanzia un progetto, non un’assunzione. Questi sono i tipi di progetto che puoi scrivere per far finanziare quelle persone:</p>
                  <ul className="space-y-1.5">{(needs.project_examples || []).map((e) => <li key={e.department} className="text-xs text-ink-2 leading-relaxed"><span className="font-medium text-ink">{e.department}.</span> {e.example}</li>)}</ul>
                  <p className="text-[11px] text-mute">Tipi: {needs.with_project.map((t) => t.label).join(' · ')}.</p>
                </div>
              )}

              {needs.needs.length > 0 && <p className="text-[11px] text-mute">{needs.assumption}</p>}
              {growthIdea && (
                <div className="flex flex-wrap items-center gap-3 pt-1">
                  <button className="btn-primary" onClick={() => chooseProject(growthIdea)}>Cerca i bandi che lo finanziano</button>
                  <span className="text-xs text-ink-2">Lo trasformo in un progetto e calcolo quanto coprono i bandi adatti. Il budget con le persone per reparto lo costruisce per ogni bando.</span>
                </div>
              )}
            </div>
          )}
        </Step>
      )}

      {match && (
        <Step id="al-bandi" title="Bandi" done={active.length > 0} open={!!openSteps.bandi} onToggle={() => toggleStep('bandi')}
          summary={`${match.matching.summary.ADATTO} adatti · ${match.matching.summary.DA_VERIFICARE} da verificare · ${active.length} inclusi ${inProject ? 'nel progetto' : 'nel piano'}`}
          info="Per ogni bando studiato: se puoi partecipare, quanto potrebbe coprire sulle tue spese e come rientrare nei tetti. La spunta «Includi» decide quali bandi entrano nello scenario che stai guardando (piano dell’anno o progetto)."
          chart={<BandiChart match={match} />}>
          <TutorialVideo id="T07" />
          <TutorialVideo id="T05" />
          {st && (
            <div className="rounded-2xl bg-tint p-4 space-y-1.5">
              <p className="text-sm text-ink-2 leading-relaxed"><span className="font-medium text-ink">Li uso tutti.</span> Ho letto in breve la scheda di {st.read} dei {st.open_total} bandi aperti del catalogo: {st.high} molto affini, {st.medium} affini. {st.studied} sono già studiati a fondo e fanno il piano con importi veri.{st.unread > 0 ? ` Altre ${st.unread} schede si leggono man mano.` : ''}</p>
              <Info label="Come lavora">Due letture. La prima è veloce e riguarda tutti i bandi: la scheda ufficiale dice chi può partecipare, che spese ammette e di quale regione è, e serve a scegliere quelli che somigliano all’azienda. La seconda è lo studio a fondo, solo per i bandi che servono: cerca e legge regole e requisiti, ed è ciò che permette di calcolare gli importi e di fare il budget.</Info>
            </div>
          )}
          <div className="flex flex-wrap items-center gap-2">
            {Object.entries(FIT).map(([k, [label, tone]]) => (
              <button key={k} onClick={() => setTab(k)} aria-pressed={tab === k} className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${tab === k ? tone : 'border-line text-ink-2 hover:border-line-strong'}`}>{label} · {match.matching.summary[k]}</button>
            ))}
            <button onClick={() => setTab('CATALOG')} aria-pressed={tab === 'CATALOG'} className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${tab === 'CATALOG' ? 'bg-brand/25 text-brand-ink border-brand/60' : 'border-line text-ink-2 hover:border-line-strong'}`}>Da studiare · {match.matching.catalog.total_candidates}</button>
          </div>
          {studied && (
            <div className="p-3 rounded-xl border border-emerald-500/30 bg-emerald-500/5 text-xs text-ink-2 space-y-1">
              <p className="font-medium text-emerald-700 inline-flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4" />Studiato: {studied.name}</p>
              <p>{studied.fit ? `Ora è in «${FIT[studied.fit][0]}»${studied.estimate ? `, contributo stimato ${fmtEur(studied.estimate.covered_eur)}` : ''}.` : 'Non risulta ancora valutabile.'}</p>
              <div className="flex flex-wrap items-center gap-3 pt-0.5">{studied.fit && studied.fit !== 'NON_ADATTO' && <button className="btn !py-1" onClick={() => onBudgetFrom(studied.id)}>Crea il budget di questo bando</button>}<button className="underline" onClick={() => setStudied(null)}>chiudi</button></div>
            </div>
          )}
          {tab === 'CATALOG' && <Info label="Cosa sono">Bandi del catalogo nazionale che QUANTO non ha ancora studiato, in ordine di affinità con la tua azienda. Premi «Studia questo bando»: a lettura finita compare l’importo.</Info>}
          {match.matching.missing_profile.length > 0 && <p className="text-xs text-amber-700">Per valutare meglio indica nel profilo: {match.matching.missing_profile.map((m) => MISSING_LABEL[m] || m).join(', ')}.</p>}
          {tab === 'CATALOG' ? (
            <div className="grid lg:grid-cols-2 gap-4">
              {match.matching.catalog.items.length === 0 && <p className="text-xs text-mute">Nessuna scheda letta ancora.</p>}
              {match.matching.catalog.items.map((it) => <CatalogCard key={it.bando_id} it={it} onStudied={afterStudy} />)}
            </div>
          ) : (
            <>
              {shown.length === 0 && <p className="text-xs text-mute">Nessun bando in questa categoria.</p>}
              <div className="grid lg:grid-cols-2 gap-4">{shown.map((r) => <BandoCard key={r.bando_id} r={r} picked={active.includes(r.bando_id)} includeLabel={inProject ? 'Includi nel progetto' : 'Includi nel piano'} scenario={inProject ? 'PROJECT' : 'ANNUAL'} linked={ideasByBando[r.bando_id] || []} onPickProject={chooseProject} onToggle={() => toggle(r.bando_id)} onBudget={onBudgetFrom} />)}</div>
            </>
          )}
        </Step>
      )}

      {match && (
        <Step id="al-progetti" title="Progetti" done={!!project} open={!!openSteps.progetti} onToggle={() => toggleStep('progetti')}
          summary={project ? `Scelto: «${project.title}»${inProject ? ' · in uso' : ''}` : (ideas ? `${ideas.ideas.length} idee dai tuoi documenti · per i ${projectBandi.length} bandi che finanziano progetti` : 'Per i bandi che finanziano progetti')}
          info="I bandi a progetto (ricerca, investimenti) finanziano le spese nuove di un progetto, non i costi correnti. Le idee qui sotto nascono dai documenti dell’azienda e ognuna elenca i bandi che finanziano quel tipo di progetto. Se un bando a progetto non ha un’idea collegata, i tuoi documenti non ne suggeriscono una adatta: non ne invento. Crediti d’imposta, garanzie, assunzioni e spese commerciali non chiedono un progetto.">
          <TutorialVideo id="T09" />
          <ProjectIdeas data={ideas} error={ideasError} loading={ideasLoading} orphans={orphans} active={project} onAllocate={chooseProject} onClear={() => { setProject(null); setMode('ANNUAL') }} includeCurrent={includeCurrent} setIncludeCurrent={setIncludeCurrent} />
        </Step>
      )}

      {match && (
        <Step id="al-risultato" title="Risultato" done={active.length > 0 && !!plan} open={!!openSteps.risultato} onToggle={() => toggleStep('risultato')} alert={planError}
          summary={confirm ? `Calcolare il piano costa ${fmtTok(confirm.due)} token: conferma per continuare` : plan ? `${fmtEur(plan.covered_by_public_funds_eur)}${planHigh && planHigh.covered_by_public_funds_eur > plan.covered_by_public_funds_eur + 0.5 ? ` – ${fmtEur(planHigh.covered_by_public_funds_eur)}` : ''} coperti su ${fmtEur(plan.total_gross_expense_eur)} · ${fmtNum(plan.overall_coverage_percentage, 1)}% · ${inProject ? `progetto «${project.title}»` : 'spese dell’anno'}` : (active.length === 0 ? (inProject ? 'Nessun bando adatto cita questo tipo di progetto: includi tu i bandi da usare' : 'Scegli i bandi da includere') : 'Calcolo…')}
          info={<><p><strong className="text-ink">Spese dell’anno</strong>: le spese che l’azienda sosterrà comunque nel {year} (personale, affitti, licenze…), coperte dai bandi che non chiedono un progetto: crediti d’imposta, spese commerciali, incentivi alle assunzioni.</p><p><strong className="text-ink">Un progetto</strong>: spese nuove e straordinarie (un investimento, una ricerca), coperte dai bandi che finanziano progetti. Un bando a progetto non paga le spese correnti: per questo non compare tra le spese dell’anno.</p><p>«Includi nel piano» e «Includi nel progetto» fanno la stessa cosa nello scenario che stai guardando: decidono quali bandi entrano nel calcolo. Le due scelte restano separate.</p><p>Le spese vengono dal budget dell’azienda e dal piano degli investimenti, se li hai caricati; altrimenti dalla stima dell’anno.</p><p>È un massimo teorico: non considera la probabilità di vincere né i tempi (vedi «Valore reale e incassi»).</p></>}
          >
          {confirm && <CostConfirm c={confirm} busy={loading} onConfirm={() => { confirmRef.current = true; run() }} />}
          <TutorialVideo id="T08" />
          {scenarioBar}
          {inProject && <ProjectCandidates items={(match.matching.catalog?.items || []).filter((it) => (it.cost_categories || []).some((c) => project.lines.some((l) => l.nature === 'NUOVA' && l.category === c))).slice(0, 6)} onStudied={afterStudy} />}
          <div className="max-w-xl"><PotentialChart plan={plan} nameOf={(id) => results.find((r) => r.fund?.fund_id === id)?.name || id} dm={{ estimate: dmEstimate }} /></div>
          <PotentialStep results={results} picked={active} onPick={pick} scenario={inProject ? 'PROJECT' : 'ANNUAL'} isCandidate={isCandidate} dm={{ estimate: dmEstimate, override: overrideOk ? dmOverride : '', invalid: dmOverride !== '' && !overrideOk, setOverride: (v) => setDmOverride(String(v).replace(/[^0-9.,]/g, '').replace(',', '.')), value: Number(deMinimis), onDeclare: declareAid, onVerify: () => onGoProfile({ to: 'aiuti' }) }} plan={plan} planHigh={planHigh} loading={loading} planError={planError} onStudyMore={studyMore} studyingMore={studyingMore} />
          {studyNote && <p className="text-[11px] text-ink-2 leading-relaxed">{studyNote}</p>}
        </Step>
      )}

      {match && active.length > 0 && plan && (
        <Step id="al-piano" title="Piano voce per voce" done open={!!openSteps.piano} onToggle={() => toggleStep('piano')} alert={planError}
          summary={`${plan.allocation_plan.length} voci · ${fmtEur(plan.covered_by_public_funds_eur)} coperti · ${fmtEur(plan.net_cost_to_entity_eur)} a tuo carico`}
          info="Con i bandi inclusi, il programma sceglie la combinazione migliore rispettando tetti dei fondi, limiti per categoria, fondi non cumulabili e de minimis."
          chart={<PlanChart plan={plan} />}>
          <div className="flex flex-wrap items-end gap-3">
            <label className="flex items-center gap-2 text-xs text-ink-2">Obiettivo <Hint id="alloc_obiettivo" />
              <select value={target} onChange={(e) => setTarget(e.target.value)} className="field !w-full md:!w-auto min-w-0">{TARGETS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>
          </div>
          <div className={`grid grid-cols-2 md:grid-cols-4 gap-4 transition ${loading ? 'opacity-50' : ''}`}>
            {[['Spesa totale', fmtEur(plan.total_gross_expense_eur), 'text-ink'],
              ['Coperta dai fondi', fmtEur(plan.covered_by_public_funds_eur), 'text-emerald-700'],
              ['A tuo carico', fmtEur(plan.net_cost_to_entity_eur), 'text-amber-700'],
              ['Quota coperta', `${fmtNum(plan.overall_coverage_percentage, 1)}%`, 'text-brand-ink']].map(([l, v, tone]) => (
              <div key={l} className="rounded-2xl border border-line bg-field p-4 min-w-0"><span className="label">{l}</span><div className={`text-lg font-semibold mt-1 whitespace-nowrap tabular-nums tracking-tight ${tone}`}>{v}</div></div>
            ))}
          </div>
          <div className="space-y-2"><span className="label inline-flex items-center gap-1.5">Da dove arrivano i soldi <Hint id="alloc_flusso" /></span><Sankey plan={plan} /></div>
          <div className="grid lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-2">
              {plan.allocation_plan.map((l) => (
                <div key={l.item_id} className="p-3 bg-field border border-line rounded-xl text-xs space-y-1.5">
                  <div className="flex justify-between gap-3"><span className="font-medium text-sm min-w-0 break-words">{l.label || CATEGORY_LABEL[l.category] || l.category}</span><span className="font-mono shrink-0">{fmtEur(l.gross_amount_eur)}</span></div>
                  {l.coverage.length ? l.coverage.map((c) => (
                    <div key={c.fund_id} className="flex justify-between gap-3 text-emerald-700 font-mono"><span className="min-w-0 break-words">{c.fund_id}</span><span className="shrink-0">{fmtEur(c.covered_amount_eur)} ({fmtNum(c.coverage_percentage, 1)}%)</span></div>
                  )) : <div className="text-mute">Nessun bando adatto: la paga l’azienda</div>}
                  <div className="flex justify-between text-amber-700 font-mono border-t border-line pt-1.5"><span>A tuo carico</span><span>{fmtEur(l.net_cost_to_entity_eur)}</span></div>
                </div>
              ))}
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <span className="label inline-flex items-center gap-1.5">Quanto si usa di ogni bando <Hint id="alloc_uso" /></span>
                {plan.fund_usage.map((u) => (
                  <div key={u.fund_id} className="text-xs font-mono space-y-0.5">
                    <div className="flex justify-between gap-3"><span className="text-ink-2 min-w-0 break-words">{u.fund_id}</span><span>{fmtEur(u.used_eur)}</span></div>
                    <div className="text-mute">{u.cap_eur != null ? `disponibili ${fmtEur(u.cap_eur)}` : 'nessun limite di importo'}</div>
                  </div>
                ))}
                {plan.de_minimis_residual_eur != null && <div className="text-xs font-mono pt-2 border-t border-line text-ink-2">De minimis usato {fmtEur(plan.de_minimis_used_eur)} · disponibile {fmtEur(plan.de_minimis_residual_eur)}</div>}
              </div>
              <div className="space-y-2">
                <span className="label inline-flex items-center gap-1.5">Mese per mese <Hint id="alloc_mesi" /></span>
                <div className="flex items-end gap-1 h-24">
                  {plan.monthly_plan.map((m) => (
                    <div key={m.month} className="flex-1 flex flex-col justify-end h-full" title={`Mese ${m.month}: totale ${fmtEur(m.gross_eur)}, coperto ${fmtEur(m.covered_eur)}`}>
                      <div className="bg-amber-400/70" style={{ height: `${(m.net_eur / maxMonth) * 100}%` }} />
                      <div className="bg-emerald-400/70" style={{ height: `${(m.covered_eur / maxMonth) * 100}%` }} />
                    </div>
                  ))}
                </div>
                <p className="text-[11px] text-mute"><span className="text-emerald-700">■</span> coperto <span className="text-amber-700 ml-2">■</span> a tuo carico</p>
              </div>
            </div>
          </div>
        </Step>
      )}

      {plan && onOpenBudgets && (
        <Step id="al-budget" title="Budget dei bandi" open={!!openSteps.budget} onToggle={() => toggleStep('budget')}
          summary={`Un budget per ognuno dei ${nPlanFunds} ${nPlanFunds === 1 ? 'bando usato' : 'bandi usati'}, già controllato con i suoi 60 criteri`}
          info="Ogni bando riceve solo le spese che finanzia. Il personale è diviso tra i progetti senza sovrapporsi, le spese pagate da due bandi dichiarano l’altro contributo, e i bandi non cumulabili non si toccano. Ogni budget si apre e si modifica nella pagina Budget.">
          <TutorialVideo id="T13" />
          <BudgetsFromPlan plan={plan} lines={planLines} onOpen={onOpenBudgets} />
        </Step>
      )}

      {plan && (
        <Step id="al-incassi" title="Valore reale e incassi" open={!!openSteps.incassi} onToggle={() => toggleStep('incassi')}
          summary="Quanto conti davvero di ottenere, e quando entrano i soldi"
          info="Un contributo non è un incasso: si vince o no, ottenerlo costa lavoro, e il rimborso arriva dopo che hai pagato. Scrivi per ogni bando probabilità di successo, costo di istruttoria e percentuale del consulente (anche zero): QUANTO non li inventa, senza mostra solo il nominale.">
          <TutorialVideo id="T10" />
          <RealityPanel plan={plan} lines={planLines} />
        </Step>
      )}
    </div>
  )
}
