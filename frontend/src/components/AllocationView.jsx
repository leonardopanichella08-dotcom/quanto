import React, { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import { fmtEur, fmtNum, CATEGORY_LABEL } from '../lib/format'
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronRight, CircleHelp, ExternalLink, Loader2, Sparkles, XCircle } from 'lucide-react'
import { ChromeCard, SectionTitle } from './ui'
import Guide from './Guide'
import PipelineButton from './PipelineButton'
import { Hint } from './Help'
import ForecastStep from './ForecastStep'
import PotentialStep from './PotentialStep'

const PALETTE = ['#38bdf8', '#a78bfa', '#f472b6', '#34d399', '#fbbf24', '#fb7185', '#2dd4bf', '#818cf8', '#f97316', '#84cc16', '#e879f9', '#94a3b8']

/** Flusso delle spese verso i fondi: lo spessore è proporzionale all'importo coperto (dati del solver, nessun calcolo qui). */
function Sankey({ plan }) {
  const items = plan.allocation_plan
  const allFunds = plan.fund_usage.map((f) => f.fund_id)
  const funds = plan.fund_usage.filter((f) => f.used_eur > 0)
  const gross = items.reduce((s, i) => s + i.gross_amount_eur, 0) || 1
  const W = 700, H = Math.max(240, items.length * 46), gap = 10, X0 = 150, X1 = W - 170
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
        <PipelineButton bandoId={it.bando_id} label="Studia questo bando" onDone={(r) => onStudied(it, r)} />
        {it.source_url && <a href={it.source_url} target="_blank" rel="noreferrer" className="text-xs text-sky-700 hover:underline inline-flex items-center gap-1 pt-2"><ExternalLink className="w-3 h-3" />Scheda ufficiale</a>}
      </div>
    </div>
  )
}

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
        <div className="flex flex-wrap gap-1.5 justify-end">
          {r.de_minimis?.applies && <span title={r.de_minimis.evidence[0]?.text} className="px-2 py-0.5 text-[11px] font-medium rounded border border-violet-500/30 bg-violet-500/10 text-violet-700">In de minimis</span>}
          <span className={`px-2 py-0.5 text-[11px] font-medium rounded border ${tone}`}>{fit}</span>
        </div>
      </div>

      {e ? (
        <div className="flex flex-wrap items-end gap-x-6 gap-y-2">
          <div><span className="label">{e.kind_label || 'Contributo stimato'}</span><div className="text-lg font-display font-semibold text-emerald-700 tabular-nums">{fmtEur(e.covered_eur)}{e.covered_high_eur > e.covered_eur + 0.5 && <span className="text-sm text-emerald-700/80"> – {fmtEur(e.covered_high_eur)}</span>}</div></div>
          <div><span className="label">Percentuale</span><div className="text-sm font-semibold tabular-nums">{fmtNum(e.rate_pct, 1)}%{e.rate_high_pct > e.rate_pct + 0.05 && ` – ${fmtNum(e.rate_high_pct, 1)}%`}</div></div>
          <div><span className="label">Sul totale delle tue spese</span><div className="text-sm font-semibold tabular-nums">{fmtNum(e.covered_pct_of_total, 1)}%</div></div>
        </div>
      ) : r.guarantee ? (
        <div className="space-y-1">
          <div className="flex flex-wrap items-end gap-x-6 gap-y-2">
            <div><span className="label">Importo garantibile</span><div className="text-lg font-display font-semibold text-sky-700 tabular-nums">{fmtEur(r.guarantee.guaranteed_low_eur)} – {fmtEur(r.guarantee.guaranteed_high_eur)}</div></div>
            <div><span className="label">Su un finanziamento di</span><div className="text-sm font-semibold tabular-nums">{fmtEur(r.guarantee.financed_eur)}</div></div>
          </div>
          <p className="text-[11px] text-mute">{r.guarantee_info?.kind_label}</p>
        </div>
      ) : <p className="text-xs text-amber-700">{r.notes.find((n) => n.startsWith('Il bando non dichiara')) || 'Nei documenti ufficiali letti non compare una percentuale: puoi farlo studiare di nuovo per cercarla.'}</p>}
      {e && (e.assumptions?.length > 0 || e.evidence?.length > 0) && (
        <div className="text-[11px] text-ink-2 space-y-1 leading-relaxed">
          {e.assumptions.map((a, i) => <p key={i}>• {a}</p>)}
          {e.evidence.slice(0, 2).map((x, i) => <p key={`ev${i}`} className="text-mute">Dal testo ufficiale: «{x.text}»{x.url && <> · <a href={x.url} target="_blank" rel="noreferrer" className="underline">fonte</a></>}</p>)}
        </div>
      )}
      {!e && r.guarantee && r.guarantee_info && (
        <div className="text-[11px] text-ink-2 space-y-1 leading-relaxed">
          {r.guarantee_info.assumptions.map((a, i) => <p key={i}>• {a}</p>)}
        </div>
      )}

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
          {r.de_minimis?.applies && <p className="text-ink-2"><span className="font-medium text-ink">De minimis:</span> questo aiuto conta contro il tetto di 300.000 € in tre anni. {r.de_minimis.basis === 'MODELLO' ? 'Lo dichiara la scheda curata del bando.' : 'Lo dice il testo ufficiale letto:'} {r.de_minimis.basis === 'TESTO' && <>«{r.de_minimis.evidence[0]?.text}»{r.de_minimis.evidence[0]?.url && <> · <a href={r.de_minimis.evidence[0].url} target="_blank" rel="noreferrer" className="underline">fonte</a></>}</>}</p>}
          {!r.de_minimis?.applies && r.de_minimis?.mentioned && <p className="text-mute">Il testo ufficiale cita il de minimis ma dice che questo aiuto non rientra: «{r.de_minimis.evidence[0]?.text}»</p>}
          {r.notes.filter((n) => !n.startsWith('Il bando non dichiara')).map((n) => <p key={n} className="text-mute">• {n}</p>)}
          {r.missing_profile.length > 0 && <p className="text-amber-700">Per decidere servono ancora: {r.missing_profile.map((m) => MISSING_LABEL[m] || m).join(', ')}.</p>}
          <p className="text-[11px] text-mute">{r.rules_count} regole e {r.requirements_count} requisiti letti dal bando. Punto di attenzione per la tua diagnosi consulenziale: stima basata solo su ciò che il bando dichiara; l’esito dipende dall’istruttoria.</p>
        </div>
      )}
    </div>
  )
}

export default function AllocationView({ onGoProfile, onBudgetFrom }) {
  const [ov, setOv] = useState(null)
  const [year, setYear] = useState(new Date().getFullYear() + 1)
  const [growth, setGrowth] = useState({})                 // percentuali che l'utente ha scritto a mano in questa schermata (le altre arrivano dal modello o dai bilanci)
  const [match, setMatch] = useState(null)                 // {forecast, matching}
  const [matching, setMatching] = useState(false)
  const [tab, setTab] = useState('ADATTO')
  const [picked, setPicked] = useState([])
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
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [planError, setPlanError] = useState(null)
  const seq = useRef(0)

  useEffect(() => { api.profile().then(setOv).catch((e) => setError(e.message)) }, [])
  // scelte salvate per questo lavoro: anno, percentuali scritte a mano, bandi inclusi, obiettivo, de minimis
  useEffect(() => {
    api.clientState('allocation').then((st) => {
      const v = st.value
      if (v) { if (v.year) setYear(v.year); setGrowth(v.growth || {}); if (v.target) setTarget(v.target); setDmOverride(v.dmOverride || ''); allMode.current = v.allMode ?? false; pending.current = v.allMode ? null : (v.picked || []) }
    }).catch(() => {}).finally(() => setRestored(true))
  }, [])
  useEffect(() => {
    if (!restored) return undefined
    const t = setTimeout(() => { api.saveClientState('allocation', { year, growth, picked, target, dmOverride, allMode: allMode.current }).catch(() => {}) }, 800)
    return () => clearTimeout(t)
  }, [restored, year, growth, picked, target, dmOverride])

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
      const sure = res.matching.results.filter((r) => r.fit === 'ADATTO' && r.fund).map((r) => r.bando_id)
      const keep = allMode.current ? sure : (pending.current ?? picked)   // piano «tutti i bandi adatti»: segue i bandi nuovi; altrimenti le scelte restano (se ancora valide)
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
      const found = res.matching.results.find((x) => x.bando_id === it.bando_id)
      setStudied({ name: found?.name || it.name, report: r?.report, fit: found?.fit, estimate: found?.estimate })
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
      setStudyNote(`Ho studiato ${done.length} bandi: ${done.join('; ')}. Stima e bandi aggiornati.`)
    } catch (e) { setError(e.message) } finally { setStudyingMore(false) }
  }

  const pickedRows = (match?.matching.results || []).filter((r) => picked.includes(r.bando_id) && r.fund)
  const needsDeMinimis = pickedRows.some((r) => r.fund.de_minimis)
  const dmEstimate = match?.de_minimis || null
  const deMinimis = dmOverride !== '' ? dmOverride : String(dmEstimate ? dmEstimate.residual_eur : 300000)      // il valore che usa il piano: la stima, salvo correzione dell'utente

  // Il piano si ricalcola da solo a ogni scelta (bandi inclusi, obiettivo, de minimis): il calcolo è sul server.
  const run = useCallback(async () => {
    if (!match || pickedRows.length === 0) { setPlan(null); setPlanHigh(null); setPlanError(null); return }
    const mine = ++seq.current
    setLoading(true); setPlanError(null)
    try {
      const applied = Object.fromEntries(match.forecast.categories.map((c) => [c.category, c.growth_applied]))                // le stesse percentuali della tabella: il piano parte dalla stessa stima
      // Due contributi a fondo perduto non si sommano sulla stessa spesa (doppio finanziamento, criterio 47): per prudenza ogni voce ne riceve uno solo, il migliore.
      const grants = pickedRows.filter((r) => r.estimate?.kind === 'FONDO_PERDUTO').map((r) => r.fund.fund_id)
      const line = (r, high) => {
        const f = high && r.estimate?.rate_high_pct > r.estimate?.rate_pct
          ? { ...r.fund, coverage_pct: r.estimate.rate_high_pct / 100, max_total_eur: r.estimate.cap_high_eur ?? r.fund.max_total_eur } : r.fund
        return grants.includes(f.fund_id) ? { ...f, excludes: [...new Set([...(f.excludes || []), ...grants.filter((id) => id !== f.fund_id)])] } : f
      }
      const body = (high) => ({ fiscal_year: match.forecast.fiscal_year, use_profile_forecast: true, growth_pct: applied, optimization_target: target,
        available_funding_lines: pickedRows.map((r) => line(r, high)), ...(needsDeMinimis ? { de_minimis_residual_eur: Number(deMinimis) } : {}) })
      const res = await api.optimizeAllocation(body(false))
      const hasRange = pickedRows.some((r) => r.estimate?.rate_high_pct > r.estimate?.rate_pct)
      const resHigh = hasRange ? await api.optimizeAllocation(body(true)) : null
      if (mine === seq.current) { setPlan(res); setPlanHigh(resHigh) }
    } catch (e) { if (mine === seq.current) { setPlanError(e.message); setPlan(null); setPlanHigh(null) } } finally { if (mine === seq.current) setLoading(false) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [match, picked, target, deMinimis])
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
    if (pickedRows.length > 0 && !plan && !planError) return
    r.wanted = false
    window.dispatchEvent(new CustomEvent('quanto-allocation-result', { detail: {
      adatti: match.matching.summary.ADATTO, picked: pickedRows.length, usesDeMinimis: needsDeMinimis,
      covered: plan?.covered_by_public_funds_eur ?? 0, coveredHigh: planHigh?.covered_by_public_funds_eur ?? plan?.covered_by_public_funds_eur ?? 0,
      expense: plan?.total_gross_expense_eur ?? 0, net: plan?.net_cost_to_entity_eur ?? 0, coveragePct: plan?.overall_coverage_percentage ?? 0,
      deMinimis: dmEstimate ? { ...dmEstimate, residual_eur: Number(deMinimis), needed_eur: plan?.de_minimis_used_eur ?? 0 } : null } }))
  }, [tick, plan, planHigh, planError, loading, matching, match])         // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = (id) => { allMode.current = false; setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id])) }
  const pick = (ids, all) => { allMode.current = !!all; setPicked(ids) }
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
            <div className="ml-auto flex flex-wrap gap-2">
              {(ov.missing.length > 0 || !hasData) && <button className="btn" onClick={() => window.dispatchEvent(new CustomEvent('quanto-assistant', { detail: { task: 'profilo' } }))}><Sparkles className="w-3.5 h-3.5" />Falli inserire all’assistente</button>}
              <button className="btn-primary" onClick={onGoProfile}>{ov.missing.length ? 'Completa il profilo' : 'Apri il profilo'}</button>
            </div>
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
          sub="Parte dall’ultimo bilancio: costi e ricavi aumentati o diminuiti di una percentuale annua. Se hai un modello di previsione (indicato dal cliente, dal suo CFO o stimato dal tuo studio) uso quello; per le voci senza modello calcolo io la variazione dai tuoi due ultimi bilanci e la inserisco già, con la spiegazione.">
          <ForecastStep forecast={match?.forecast} overrides={growth} setOverride={setOverride} year={year} setYear={setYear} matching={matching} onEstimate={estimate} onTemplateChanged={templateChanged} />
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
            <button onClick={() => setTab('CATALOG')} aria-pressed={tab === 'CATALOG'} className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${tab === 'CATALOG' ? 'bg-brand/25 text-brand-ink border-brand/60' : 'border-line text-ink-2 hover:border-line-strong'}`}>Da studiare · {match.matching.catalog.total_candidates}</button>
          </div>
          {studied && (
            <div className="p-3 rounded-xl border border-emerald-500/30 bg-emerald-500/5 text-xs text-ink-2 space-y-1">
              <p className="font-medium text-emerald-700 inline-flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4" />Studiato: {studied.name}</p>
              {studied.report && <p>Lettura {studied.report.status === 'COMPLETA' ? 'completa' : studied.report.status === 'PARZIALE' ? 'parziale' : 'insufficiente'}: {studied.report.documents_official} documenti ufficiali, {studied.report.requirements} requisiti, {studied.report.figures} cifre, {studied.report.rules_published} regole numeriche.</p>}
              <p>{studied.fit ? `Ora lo trovi in «${FIT[studied.fit][0]}»${studied.estimate ? `, con un contributo stimato di ${fmtEur(studied.estimate.covered_eur)}` : ''}. ${studied.fit === 'NON_ADATTO' ? 'Apri «Dettagli» sulla scheda per vedere quale controllo non è superato.' : studied.estimate ? '' : 'Il bando non dichiara un’aliquota di contributo, quindi non c’è una stima in euro.'}` : 'Il bando non risulta ancora valutabile: apri la pagina Bandi per vedere cosa è stato letto.'}</p>
              <button className="underline" onClick={() => setStudied(null)}>chiudi</button>
            </div>
          )}
          {tab === 'CATALOG' && (
            <p className="text-[11px] text-mute leading-relaxed">Bandi del catalogo nazionale che QUANTO non ha ancora studiato, messi in ordine di affinità con la tua azienda usando la descrizione della scheda ufficiale (spese ammesse, regione, dimensione, ATECO). Non c’è ancora nessun importo: premi «Studia questo bando» e, a lettura finita, ricalcola la stima per vederne il contributo.
              {match.matching.catalog.excluded > 0 && ` Esclusi perché non adatti a te: ${match.matching.catalog.excluded}.`}
              {match.matching.catalog.without_description > 0 && ` Schede ancora da leggere: ${match.matching.catalog.without_description}.`}</p>
          )}
          {match.matching.missing_profile.length > 0 && <p className="text-xs text-amber-700">Per valutare meglio alcuni bandi indica nel profilo: {match.matching.missing_profile.map((m) => MISSING_LABEL[m] || m).join(', ')}.</p>}
          {tab === 'CATALOG' ? (
            <div className="grid lg:grid-cols-2 gap-4">
              {match.matching.catalog.items.length === 0 && <p className="text-xs text-mute">Nessuna scheda del catalogo letta ancora: il lavoro notturno le legge a gruppi.</p>}
              {match.matching.catalog.items.map((it) => <CatalogCard key={it.bando_id} it={it} onStudied={afterStudy} />)}
            </div>
          ) : (
            <>
              {shown.length === 0 && <p className="text-xs text-mute">Nessun bando in questa categoria.</p>}
              <div className="grid lg:grid-cols-2 gap-4">{shown.map((r) => <BandoCard key={r.bando_id} r={r} picked={picked.includes(r.bando_id)} onToggle={() => toggle(r.bando_id)} onBudget={onBudgetFrom} />)}</div>
            </>
          )}
        </Step>
      )}

      {match && (
        <Step n={4} title="Tutti i bandi insieme: il potenziale massimo" done={picked.length > 0 && !!plan}
          sub="Se l’azienda partecipasse e vincesse tutti i bandi a cui può accedere, quanto riuscirebbe a coprire in un anno? Li applico insieme rispettando cumulo, tetti e de minimis, senza pagare due volte la stessa spesa.">
          <PotentialStep results={results} picked={picked} onPick={pick} dm={{ estimate: dmEstimate, override: dmOverride, setOverride: setDmOverride, value: Number(deMinimis), onDeclare: declareAid }} plan={plan} planHigh={planHigh} loading={loading} planError={planError} onStudyMore={studyMore} studyingMore={studyingMore} />
          {studyNote && <p className="text-[11px] text-ink-2 leading-relaxed">{studyNote}</p>}
        </Step>
      )}

      {match && picked.length > 0 && (
        <Step n={5} title="Il piano dell’anno, voce per voce" done={!!plan}
          sub="Con i bandi che hai incluso, il programma prova le combinazioni possibili e sceglie la migliore, rispettando i tetti dei fondi, i limiti per categoria, i fondi non cumulabili e il de minimis.">
          <div className="flex flex-wrap items-end gap-3">
            <label className="flex items-center gap-2 text-xs text-ink-2">Obiettivo <Hint id="alloc_obiettivo" />
              <select value={target} onChange={(e) => setTarget(e.target.value)} className="field !w-full md:!w-auto min-w-0">{TARGETS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></label>
            <span className="text-xs text-mute">{pickedRows.length} {pickedRows.length === 1 ? 'bando incluso' : 'bandi inclusi'}</span>
          </div>
          {needsDeMinimis && <p className="text-[11px] text-ink-2 leading-relaxed max-w-3xl">Alcuni bandi scelti sono in de minimis: il tetto residuo che il piano rispetta (<strong className="text-ink">{fmtEur(Number(deMinimis))}</strong>) e come è stato stimato sono spiegati nel punto 4.</p>}
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
        </>
      )}
    </div>
  )
}
