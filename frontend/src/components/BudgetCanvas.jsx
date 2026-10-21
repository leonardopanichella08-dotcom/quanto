import React, { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { api } from '../lib/api'
import { AlertTriangle, ArrowLeft, ChevronDown, ChevronLeft, ChevronRight, Download, Loader2, Play, Plus, ShieldCheck, Upload, X } from 'lucide-react'
import LineEditor from './LineEditor'
import ItemTemplatePicker from './ItemTemplatePicker'
import CriteriaHeatmap, { heatmapData } from './CriteriaHeatmap'
import Documents from './Documents'
import TemplateFromProfile from './TemplateFromProfile'
import WorkPackages from './WorkPackages'
import Guide from './Guide'
import HowItWorks from './HowItWorks'
import TutorialVideo from './TutorialVideo'
import { Hint } from './Help'
import { ChromeCard, Fold, Info } from './ui'
import { publishGo, scrollTop, useNav } from '../lib/nav'
import { fmtTok } from './Tokens'
import { BANDO_STATUS_STYLE, CATEGORY_LABEL, CATEGORY_ORDER, STATUS_LABEL, STATUS_STYLE, fmtEur, fmtNum, fmtPct } from '../lib/format'

const ITEM_STATUS_DOT = { APPROVED: '#10b981', CAP_EXCEEDED_ADJUSTED: '#f59e0b', REJECTED: '#ef4444', MISSING_DOCUMENTS: '#38bdf8' }

const NEW_ITEM = {
  PERSONNEL: { ccnl_code: 'COMMERCIO', employee_level: '3', ral_eur: 30000, fte_allocation: 0.5, duration_months: 12 },
  CAPITAL_ASSETS: { amount_eur: 10000, asset_nature: 'HARDWARE' },
  CONSULTING: { amount_eur: 10000 },
  OVERHEAD: { amount_eur: 5000 },
  TRAINING: { amount_eur: 5000 },
}
const OUTCOME_STYLE = { PASS: 'text-emerald-700', ADJUSTED: 'text-amber-700', REJECTED: 'text-red-700', SUSPENDED: 'text-sky-700' }
const OUTCOME_LABEL = { PASS: 'superato', ADJUSTED: 'ridotto', REJECTED: 'respinto', SUSPENDED: 'in attesa di documento' }

function SummaryCard({ label, value, tone = 'text-ink', note }) {
  return (
    <div className="card p-4 min-w-0">
      <span className="label">{label}</span>
      <div className={`text-xl xl:text-2xl font-semibold mt-1.5 whitespace-nowrap tabular-nums tracking-tight ${tone}`}>{value}</div>
      <p className="text-xs text-mute mt-1">{note}</p>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between gap-4 py-1 border-b border-line last:border-0 text-xs">
      <span className="text-mute">{label}</span>
      <span className="text-ink text-right tabular-nums">{value}</span>
    </div>
  )
}

function Block({ title, hint, children }) {
  return (
    <div className="p-4 bg-tint rounded-2xl space-y-2">
      <span className="text-ink text-[13px] font-medium inline-flex items-center gap-1.5">{title}{hint && <Hint id={hint} />}</span>
      {children}
    </div>
  )
}

function Inspector({ item, steps }) {
  const b = item.breakdown
  return (
    <div className="space-y-4">
      {item.rejection_reason && (
        <div className="p-4 rounded-2xl bg-amber-500/10 text-amber-900 flex gap-2.5">
          <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
          <div><p className="text-sm font-medium">Perché</p><p className="text-[13px] leading-relaxed mt-0.5">{item.rejection_reason}</p></div>
        </div>
      )}
      <div className="grid lg:grid-cols-2 gap-4 items-start">
        <div className="space-y-4 min-w-0">
          <Block title="Da dove vengono i dati" hint="fontea">
            <Row label="Documento (Fonte C)" value={b.source_c_ref || '— mancante —'} />
            {b.ccnl_table_ref && <Row label="Tabella ufficiale (Fonte B)" value={b.ccnl_table_ref} />}
            <Row label="Regole del bando (Fonte A), versione" value={b.rule_version_hash} />
            {b.hourly_cap_eur != null && <Row label="Tetto orario del bando" value={`${fmtNum(b.hourly_cap_eur)} €/h`} />}
            {b.budget_cap_pct != null && <Row label="Limite del bando (% del totale)" value={fmtPct(b.budget_cap_pct)} />}
          </Block>
          {item.category === 'PERSONNEL' && b.annual_cost_eur != null && (
            <Block title="Come si calcola il costo del personale">
              <Row label="RAL (stipendio annuo lordo)" value={fmtEur(b.ral_eur)} />
              <Row label={`Oneri sociali (${fmtPct(b.social_charges_pct, 2)})`} value={fmtEur(b.social_charges_eur)} />
              <Row label={`TFR (${fmtPct(b.tfr_pct, 2)})`} value={fmtEur(b.tfr_eur)} />
              <Row label="Costo annuo per l’azienda" value={fmtEur(b.annual_cost_eur)} />
              <Row label="Costo orario" value={`${fmtNum(item.hourly_rate_computed)} €/h (÷ ${b.working_hours} ore)`} />
              <Row label="Tempo dedicato × durata" value={`${b.fte_allocation} × ${b.duration_months} mesi`} />
            </Block>
          )}
        </div>
        <Block title="Controllo per controllo">
          <div className="space-y-2">
            {steps.map((s) => (
              <div key={s.seq} className="flex gap-3 text-xs border-b border-line pb-2 last:border-0 last:pb-0">
                <span className="font-mono text-mute shrink-0 w-8">#{s.criterion}</span>
                <div className="min-w-0">
                  <span className={`font-medium ${OUTCOME_STYLE[s.outcome]}`}>{OUTCOME_LABEL[s.outcome]}</span>
                  {s.delta_eur !== 0 && <span className="font-mono text-ink-2"> {fmtEur(s.delta_eur)}</span>}
                  <p className="text-ink-2 leading-snug mt-0.5">{s.note}</p>
                </div>
              </div>
            ))}
          </div>
          {item.criteria_not_evaluated.length > 0 && (
            <p className="text-xs text-mute pt-1">Non valutati (manca un dato o una regola): {item.criteria_not_evaluated.map((c) => `#${c}`).join(' ')}</p>
          )}
        </Block>
      </div>
      <details className="text-xs text-ink-2">
        <summary className="cursor-pointer text-mute hover:text-ink">Impronta della voce</summary>
        <p className="font-code text-[11px] text-brand-ink break-all p-3 mt-2 bg-tint rounded-xl">{item.item_hash_sha256}</p>
        <p className="mt-1.5 text-mute">È una foglia dell’albero di Merkle: la vedi con «Vedi l’animazione passo-passo».</p>
      </details>
    </div>
  )
}

export default function BudgetCanvas({
  bandi, bando, request, fields, validation, loading, error, busy, importInfo, criteriaTitles,
  onSelectBando, onProjectId, onItemsChange, onImport, onValidate, onRegister, onExport, onOpenLab, onDismissImport, onGoBandi,
  onUsePayslip, onUseBalance, onUseDraft, onUseTemplate, onGoProfile, templateOpen, incompleteItems = [], notice, onDismissNotice, budgetSet, onSwitchBudget, onCloseBudgetSet,
}) {
  const nav = useNav()
  const [selectedId, setSelectedId] = useState(null)
  const [delivery, setDelivery] = useState(null)             // quanto costa consegnare questo budget (esportare o registrare): 1 token, oppure già incluso
  const [panel, setPanel] = useState('inspect')
  const [view, setView] = useState('list')                  // 'list' = il budget; 'detail' = la scheda di una voce, in una vista a parte
  const [open, setOpen] = useState({})                       // riquadri richiudibili: chiusi finché non servono
  const toggleFold = (k) => setOpen((o) => ({ ...o, [k]: !o[k] }))
  const back = useRef(null)                                // dove eri nella pagina quando hai aperto la scheda
  const [addOpen, setAddOpen] = useState(false)
  const [docsOpen, setDocsOpen] = useState(false)
  const docsRef = useRef(null)
  const fileRef = useRef(null)
  const items = request.cost_items
  const byId = useMemo(() => Object.fromEntries((validation?.items || []).map((i) => [i.item_id, i])), [validation])
  const selectedInput = items.find((i) => i.item_id === selectedId) || null
  const selectedResult = selectedId ? byId[selectedId] : null
  const steps = useMemo(() => (validation?.trace?.steps || []).filter((s) => s.item_id === selectedId), [validation, selectedId])
  const heat = useMemo(() => heatmapData(validation, criteriaTitles), [validation, criteriaTitles])
  // Il criterio #1 (tabella CCNL) è la porta d'ingresso di tutte le voci di personale: se manca la tabella in
  // Fonte B la voce è respinta subito, e con lei tutti i controlli 2-15 che ne dipendono restano "non valutati" —
  // non un difetto della singola voce, ma l'assenza di un dato che serve a *ogni* voce di personale.
  const missingFonteB = validation?.items?.filter((i) => i.criteria_failed?.includes(1)) || []

  const groups = CATEGORY_ORDER.map((c) => [c, items.filter((i) => i.category === c)]).filter(([, l]) => l.length)
  const nextId = () => { let n = items.length + 1; while (items.some((i) => i.item_id === `NEW-${String(n).padStart(3, '0')}`)) n += 1; return `NEW-${String(n).padStart(3, '0')}` }

  const addFromTemplate = (t) => {
    const item = { item_id: nextId(), description: t.label, category: t.category, source_c_ref: '', ...NEW_ITEM[t.category], ...t.defaults }
    onItemsChange([...items, item]); setAddOpen(false); openItem(item.item_id, 'edit')
  }
  const update = (item) => { onItemsChange(items.map((i) => (i.item_id === selectedId ? item : i))); setSelectedId(item.item_id) }
  const remove = () => { onItemsChange(items.filter((i) => i.item_id !== selectedId)); setSelectedId(null); closeItem() }
  const duplicate = () => { const c = { ...selectedInput, item_id: nextId() }; onItemsChange([...items, c]); setSelectedId(c.item_id) }
  const ordered = useMemo(() => groups.flatMap(([, l]) => l), [items])      // eslint-disable-line react-hooks/exhaustive-deps
  const here = () => ({ w: window.scrollY, a: document.getElementById('app-scroll')?.scrollTop || 0 })
  const openItem = (id, tab) => {
    if (view !== 'detail') back.current = here()
    setSelectedId(id); setPanel(tab || (byId[id] ? 'inspect' : 'edit')); setView('detail'); scrollTop()
  }
  const closeItem = () => setView('list')
  useLayoutEffect(() => {                                                    // tornando al budget si ritrova lo stesso punto, non l'inizio della pagina
    if (view !== 'list' || !back.current) return
    const p = back.current; back.current = null
    window.scrollTo({ top: p.w }); document.getElementById('app-scroll')?.scrollTo({ top: p.a })
  }, [view])

  useEffect(() => {                                                         // il costo della consegna, letto prima di premere: si aggiorna dopo ogni esportazione o registrazione
    let live = true
    const load = () => { if (validation && request?.project_id) api.tokenQuote({ op: 'deliver', project_id: request.project_id, bando_id: bando?.bando_id || '', items: String(request.cost_items.length) }).then((q) => { if (live) setDelivery(q) }).catch(() => {}) }
    load()
    window.addEventListener('quanto-tokens-changed', load)
    return () => { live = false; window.removeEventListener('quanto-tokens-changed', load) }
  }, [validation?.merkle_root, request?.project_id, bando?.bando_id, request?.cost_items?.length])      // eslint-disable-line react-hooks/exhaustive-deps

  if (view === 'detail' && selectedInput) {
    const idx = ordered.findIndex((i) => i.item_id === selectedInput.item_id)
    const r = selectedResult
    const step = (d) => { const n = ordered[idx + d]; if (n) { setSelectedId(n.item_id); setPanel(byId[n.item_id] ? panel : 'edit'); scrollTop() } }
    return (
      <div className="space-y-5">
        <div className="flex flex-wrap items-center gap-3">
          <button onClick={closeItem} className="btn"><ArrowLeft className="w-3.5 h-3.5" />Torna al budget</button>
          <div className="ml-auto flex items-center gap-1.5">
            <button className="btn !px-2" disabled={idx <= 0} onClick={() => step(-1)} aria-label="Voce precedente"><ChevronLeft className="w-4 h-4" /></button>
            <span className="text-xs text-mute tabular-nums w-12 text-center">{idx + 1} / {ordered.length}</span>
            <button className="btn !px-2" disabled={idx >= ordered.length - 1} onClick={() => step(1)} aria-label="Voce successiva"><ChevronRight className="w-4 h-4" /></button>
          </div>
        </div>
        <div className="card p-6 space-y-5">
          <div className="flex flex-wrap items-start gap-3">
            <div className="min-w-0 flex-1">
              <h3 className="text-xl font-semibold tracking-tight break-words">{selectedInput.description || selectedInput.item_id}</h3>
              <p className="text-xs text-mute mt-1">{CATEGORY_LABEL[selectedInput.category]} · <span className="font-mono">{selectedInput.item_id}</span></p>
            </div>
            {r && <span className={`px-2.5 py-1 text-xs font-medium rounded-full border shrink-0 ${STATUS_STYLE[r.status]}`}>{STATUS_LABEL[r.status]}</span>}
          </div>
          {r && (
            <div className="flex flex-wrap gap-x-10 gap-y-2">
              <div><span className="label">Richiesto</span><div className="text-lg font-semibold tabular-nums">{fmtEur(r.original_cost_eur)}</div></div>
              <div><span className="label">Ammesso</span><div className="text-lg font-semibold tabular-nums text-emerald-700">{fmtEur(r.computed_cost_eur)}</div></div>
            </div>
          )}
          <div className="inline-flex p-1 rounded-full bg-tint text-xs font-medium" role="tablist">
            {[['inspect', 'Controlli', !r], ['edit', 'Modifica', false]].map(([k, l, off]) => (
              <button key={k} role="tab" aria-selected={panel === k} disabled={off} onClick={() => setPanel(k)}
                className={`px-4 py-1.5 rounded-full transition disabled:opacity-40 ${panel === k ? 'bg-white shadow-sm text-ink' : 'text-ink-2 hover:text-ink'}`}>{l}</button>
            ))}
          </div>
          {panel === 'inspect' && r ? <Inspector item={r} steps={steps} />
            : panel === 'inspect' ? <p className="text-sm text-mute">Premi «Controlla il budget» per vedere l’analisi di questa voce.</p>
              : fields ? <LineEditor item={selectedInput} fields={fields} onChange={update} onDelete={remove} onDuplicate={duplicate} /> : null}
        </div>
      </div>
    )
  }

  const statusCount = validation ? validation.items.reduce((a, i) => ({ ...a, [i.status]: (a[i.status] || 0) + 1 }), {}) : {}

  return (
    <div className="space-y-6">
      <Guide page="budget" />
      <HowItWorks kind="budget" />
      <TutorialVideo id="T12" />
      {budgetSet && <TutorialVideo id="T13" />}

      {budgetSet && (
        <div className="card p-4 space-y-2.5">
          <div className="flex flex-wrap items-center gap-2">
            <span className="label shrink-0">Budget dell’allocazione {budgetSet.fiscal_year}</span>
            {budgetSet.budgets.map((b) => (
              <button key={b.fund_id} onClick={() => onSwitchBudget(b.fund_id)} disabled={busy} aria-pressed={budgetSet.active === b.fund_id}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${budgetSet.active === b.fund_id ? 'bg-brand/25 text-brand-ink border-brand/60' : 'border-line text-ink-2 hover:border-line-strong'}`}>{b.name}</button>
            ))}
            <button className="btn !py-1 ml-auto" title="Torni a lavorare su un solo budget: quello che hai aperto resta, gli altri escono da questa barra" onClick={() => { if (window.confirm('Esci dal gruppo?' + String.fromCharCode(10, 10) + 'Non si crea un budget unico: ogni bando ha le sue regole e si presenta a parte. Resti sul budget che hai aperto; gli altri escono da questa barra e le modifiche non salvate si perdono. Li riottieni da Allocazione → «Budget dei bandi».')) onCloseBudgetSet() }}>Esci dal gruppo</button>
          </div>
          <Info label={budgetSet.ok ? 'Verificati insieme: nessun conflitto' : 'Ci sono incompatibilità'}>Un budget per ogni bando del piano: si presentano a parte, non si uniscono. {budgetSet.ok ? 'Questi budget sono stati verificati insieme: nessuna spesa coperta due volte oltre il consentito, nessuna persona oltre il 100% del tempo, nessun cumulo vietato.' : 'Tra questi budget ci sono incompatibilità: vedi l’elenco nella pagina Allocazione.'} Ogni budget è controllato con i 60 criteri del suo bando; se cambi le voci ricorda che gli altri budget dipendono da quelle spese.</Info>
        </div>
      )}

      {/* barra del bando */}
      <ChromeCard label={`quanto.app/budget${bando ? `/${bando.bando_id}` : ''}`} bodyClassName="p-4 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="label shrink-0">Bando</span>
          <select value={bando?.bando_id || ''} onChange={(e) => onSelectBando(e.target.value)} disabled={busy} className="field !w-auto max-w-[260px] md:max-w-sm">
            <option value="" disabled>Scegli un bando…</option>
            {bandi.map((b) => <option key={b.bando_id} value={b.bando_id} disabled={!b.rules_count}>{b.name}{b.rules_count ? '' : ' — regole non ancora lette'}</option>)}
          </select>
        </div>
        {bando && (
          <>
            <span className={`px-2 py-0.5 text-[11px] font-medium rounded border ${BANDO_STATUS_STYLE(bando.status || '')}`}>{(bando.status || '').split(' (')[0]}</span>
            <span className="text-xs text-ink-2">{bando.rules.length} regole · il bando attiva {bando.coverage_summary.REGOLA_DEL_BANDO} dei 60 controlli</span>
          </>
        )}
        <label className="flex items-center gap-2 md:ml-auto text-xs text-ink-2 w-full md:w-auto min-w-0">Nome del progetto
          <input value={request.project_id} onChange={(e) => onProjectId(e.target.value)} className="field !w-full md:!w-56 min-w-0 font-mono" />
        </label>
      </ChromeCard>
      {bando && bando.rules.length === 0 && (
        <div className="p-3 rounded-xl border border-amber-500/30 bg-amber-500/5 text-xs text-amber-800 flex flex-wrap items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>Per questo bando non ho ancora nessuna regola numerica: la ricerca sul web non è stata completata (serve scegliere le pagine ufficiali e confermare lo scaricamento).</span>
          <button onClick={onGoBandi} className="btn !py-1 ml-auto shrink-0">Completa la ricerca</button>
        </div>
      )}
      {!bando && (
        <div className="card p-8 text-center space-y-3">
          <p className="text-sm text-ink-2">Per iniziare scegli il bando su cui vuoi lavorare.</p>
          <button onClick={onGoBandi} className="btn-primary">Vai ai bandi</button>
        </div>
      )}

      {bando && <TemplateFromProfile key={`${bando.bando_id}-${templateOpen ? 'o' : 'c'}`} bando={bando} onApply={onUseTemplate} onGoProfile={onGoProfile} startOpen={!!templateOpen} />}

      {/* documenti a supporto: buste paga, bilanci, F24, bozze di candidatura — funzione secondaria, non serve un bando */}
      <div ref={docsRef} className="card">
        <button onClick={() => setDocsOpen(!docsOpen)} className="w-full flex items-center gap-2 px-4 py-3 text-left text-sm font-medium">
          {docsOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          Documenti a supporto (buste paga, bilanci, F24, bozze di candidatura)
        </button>
        {docsOpen && (
          <div className="px-4 pb-4">
            <Documents onUsePayslip={onUsePayslip} onUseBalance={onUseBalance} onUseDraft={onUseDraft} />
          </div>
        )}
      </div>

      {bando && (
        <>
          {/* strumenti: solo ciò che serve davvero */}
          <div className="flex flex-wrap items-center gap-2">
            <button onClick={() => fileRef.current?.click()} disabled={busy} className="btn"><Upload className="w-3.5 h-3.5" />Importa Excel</button>
            <input ref={fileRef} type="file" accept=".xlsx,.csv" className="hidden" onChange={(e) => { if (e.target.files?.[0]) onImport(e.target.files[0]); e.target.value = '' }} />
            <div className="relative">
              <button onClick={() => setAddOpen(!addOpen)} className="btn"><Plus className="w-3.5 h-3.5" />Aggiungi voce</button>
              {addOpen && (
                <>
                  <button aria-label="Chiudi" className="fixed inset-0 z-10 cursor-default" onClick={() => setAddOpen(false)} />
                  <ItemTemplatePicker onPick={addFromTemplate} />
                </>
              )}
            </div>
            <button onClick={onValidate} disabled={loading || !items.length} className="btn-primary ml-auto flex items-center gap-1.5">
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}{loading ? 'Controllo in corso…' : 'Controlla il budget'}
            </button>
          </div>

          {notice && notice.length > 0 && (
            <div className="p-3 rounded-xl border border-amber-500/30 bg-amber-500/5 text-xs text-amber-800 space-y-1">
              <div className="flex justify-between gap-3"><span className="font-semibold">Da sapere</span><button onClick={onDismissNotice} className="underline">chiudi</button></div>
              {notice.map((n) => <p key={n} className="leading-relaxed">{n}</p>)}
            </div>
          )}
          {incompleteItems.length > 0 && (
            <div className="p-3 rounded-xl border border-amber-500/30 bg-amber-500/5 text-xs text-amber-800 leading-relaxed">
              <span className="font-semibold">{incompleteItems.length} {incompleteItems.length === 1 ? 'voce di personale non è' : 'voci di personale non sono'} nel controllo</span>: mancano RAL, quota di tempo e durata ({incompleteItems.map((i) => i.description || i.item_id).join('; ')}). Aprile e completale: il resto del budget si controlla intanto.
            </div>
          )}
          {importInfo && (
            <div className={`p-3 rounded-xl border text-xs space-y-1 ${importInfo.errors.length ? 'border-amber-500/30 text-amber-800' : 'border-emerald-500/30 text-emerald-800'}`}>
              <div className="flex justify-between"><span className="font-semibold">Import: {importInfo.items.length} voci valide su {importInfo.rows_read} righe{importInfo.errors.length ? `, ${importInfo.errors.length} con errori` : ''}</span>
                <button onClick={onDismissImport} aria-label="Chiudi"><X className="w-3.5 h-3.5" /></button></div>
              {importInfo.errors.slice(0, 8).map((e) => <p key={e.row} className="font-mono text-xs">riga {e.row}: {e.message}</p>)}
              {importInfo.ignored_columns.length > 0 && <p className="text-xs">Colonne ignorate: {importInfo.ignored_columns.join(', ')}</p>}
            </div>
          )}
          {error && <div className="p-3 rounded-xl border border-red-500/30 text-red-700 text-xs">{error}</div>}

          {missingFonteB.length > 0 && (
            <div className="p-3 rounded-xl border border-amber-500/30 bg-amber-500/5 text-amber-900 text-xs leading-relaxed flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              <p>
                <strong>{missingFonteB.length} {missingFonteB.length === 1 ? 'voce di personale respinta' : 'voci di personale respinte'}</strong> ({missingFonteB.map((i) => i.item_id).join(', ')}):
                manca la tabella CCNL in Fonte B. Succede con <em>qualunque</em> bando finché non ne carichi una — Quartier Generale → Tabelle ufficiali.
              </p>
            </div>
          )}

          {/* riepilogo */}
          <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
            <SummaryCard label="Punteggio" value={validation ? `${validation.conformity_score}/100` : '—'} tone="text-brand-ink" note="controlli superati" />
            <SummaryCard label="Richiesto" value={fmtEur(validation?.total_requested_eur)} note={`${items.length} ${items.length === 1 ? 'voce' : 'voci'}`} />
            <SummaryCard label="Ammesso" value={fmtEur(validation?.total_approved_eur)} tone="text-emerald-700" note={validation ? `${statusCount.APPROVED || 0} ok · ${statusCount.CAP_EXCEEDED_ADJUSTED || 0} ridotte` : 'Premi «Controlla il budget»'} />
            <SummaryCard label="Escluso o ridotto" value={fmtEur(validation?.total_rejected_eur)} tone="text-amber-700" note={validation ? `${statusCount.REJECTED || 0} respinte · ${statusCount.MISSING_DOCUMENTS || 0} in attesa` : '—'} />
          </div>

          {/* le voci: un tocco apre la scheda della voce */}
          <div className="card p-5 space-y-5">
            <div className="flex items-center justify-between gap-3"><span className="text-[15px] font-semibold tracking-tight">Le voci del budget</span>{validation && <span className="text-xs text-mute">tocca una voce per vedere i controlli o modificarla</span>}</div>
            {items.length === 0 && <p className="text-sm text-mute text-center py-8">Nessuna voce. Parti dalla bozza del tuo profilo, importa un Excel o aggiungi una voce.</p>}
            {groups.map(([cat, list]) => (
              <div key={cat} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs text-mute font-medium px-1">
                  <span>{CATEGORY_LABEL[cat]} · {list.length}</span>
                  {validation && <span className="tabular-nums">{fmtEur(list.reduce((s, i) => s + (byId[i.item_id]?.computed_cost_eur || 0), 0))}</span>}
                </div>
                {list.map((it) => {
                  const r = byId[it.item_id]
                  return (
                    <button key={it.item_id} onClick={() => openItem(it.item_id)}
                      className="w-full text-left px-4 py-3 bg-tint hover:bg-tint-2 rounded-2xl flex items-center gap-3 transition">
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-ink truncate">{it.description}</p>
                        <p className="text-[11px] text-mute font-mono truncate">{it.item_id}{r && r.criteria_failed.length ? ` · non superati: ${r.criteria_failed.map((c) => `#${c}`).join(' ')}` : ''}</p>
                      </div>
                      {r && <span className={`px-2 py-0.5 text-[11px] font-medium rounded-full border shrink-0 ${STATUS_STYLE[r.status]}`}>{STATUS_LABEL[r.status]}</span>}
                      <div className="text-right shrink-0 w-24">
                        <div className="text-sm font-medium tabular-nums text-ink">{r ? fmtEur(r.computed_cost_eur) : fmtEur(it.ral_eur ?? it.amount_eur)}</div>
                        {r && r.original_cost_eur !== r.computed_cost_eur && <div className="text-[11px] tabular-nums text-amber-700 line-through">{fmtEur(r.original_cost_eur)}</div>}
                      </div>
                      <ChevronRight className="w-4 h-4 text-mute shrink-0" />
                    </button>
                  )
                })}
              </div>
            ))}
          </div>

          {validation && (
            <div className="space-y-3">
              <Fold id="fold-heat" title="Controllo per controllo" summary={`${validation.items.length} ${validation.items.length === 1 ? 'voce' : 'voci'} × 60 controlli: ${heat.passed} ${heat.passed === 1 ? 'superato' : 'superati'}, ${heat.adjusted + heat.rejected} da guardare`} open={open.heat} onToggle={() => toggleFold('heat')}>
                <div className="flex flex-wrap items-center justify-between gap-2 pt-3">
                  <Info label="Come si legge">Ogni riga è una voce e ogni quadratino uno dei 60 controlli. Verde: superato. Ambra: ridotto. Rosso: respinto. Azzurro: in attesa di un documento. Tratteggiato: non valutato perché manca un dato o una regola del bando. Grigio chiaro: non riguarda questa voce. Tocca una riga per aprire la voce.</Info>
                  <button onClick={onOpenLab} className="btn">Vedi l’animazione passo-passo</button>
                </div>
                <CriteriaHeatmap items={validation.items} byKey={heat.byKey} notEval={heat.notEval} budgetChecks={validation.budget_checks || []}
                  selected={selectedId} onSelect={openItem} titles={heat.titles} statusDot={ITEM_STATUS_DOT} />
              </Fold>

              {validation.budget_checks?.length > 0 && (
                <Fold id="fold-checks" title="Controlli sull’intero budget" summary={['PASS', 'FAIL', 'NOT_EVALUATED'].map((k) => { const n = validation.budget_checks.filter((c) => c.status === k).length; return `${n} ${{ PASS: n === 1 ? 'superato' : 'superati', FAIL: n === 1 ? 'non superato' : 'non superati', NOT_EVALUATED: n === 1 ? 'non valutato' : 'non valutati' }[k]}` }).join(' · ')}
                  open={open.checks} onToggle={() => toggleFold('checks')}>
                  <div className="space-y-2 pt-3">
                    {validation.budget_checks.map((c) => {
                      const tone = c.status === 'PASS' ? 'text-emerald-700' : c.status === 'FAIL' ? 'text-red-700' : 'text-mute'
                      const word = c.status === 'PASS' ? 'ok' : c.status === 'FAIL' ? 'non superato' : 'non valutato'
                      return <div key={c.criterion} className="text-xs flex gap-3"><span className={`shrink-0 w-28 ${tone}`}>#{c.criterion} {word}</span><span className="text-ink-2">{c.title}: {c.message}</span></div>
                    })}
                  </div>
                </Fold>
              )}

              <Fold id="fold-summary" title="Riassunto" summary={validation.llm_explanation_summary} open={open.summary} onToggle={() => toggleFold('summary')}>
                <p className="text-sm text-ink-2 leading-relaxed pt-3">{validation.llm_explanation_summary}</p>
                <p className="text-[11px] text-mute">{validation.explanation_source === 'LLM' ? 'Scritto da un modello linguistico, cifre verificate.' : 'Scritto dal programma.'} <span className="font-code break-all">{validation.cep_id} · impronta {validation.merkle_root.slice(0, 18)}…</span></p>
              </Fold>

              <button onClick={() => { publishGo(); nav.go('pattern') }} className="w-full flex items-center gap-3 rounded-2xl border border-emerald-500/40 bg-emerald-500/[0.04] hover:bg-emerald-500/10 px-5 py-3.5 text-left transition">
                <span className="min-w-0 flex-1"><span className="block text-sm font-semibold text-ink">Pubblica questo budget per tutti</span>
                  <span className="block text-xs text-ink-2 mt-0.5">Allena il motore di QUANTO e il consiglio per tutti, anche per il tuo studio. Anonimo.</span></span>
                <span className="px-2.5 py-1 rounded-full bg-emerald-600 text-white text-xs font-semibold whitespace-nowrap">+0,5 token</span>
                <ChevronRight className="w-4 h-4 text-mute shrink-0" />
              </button>

              <div className="card px-5 py-4 flex flex-wrap items-center gap-3">
                <span className="text-sm font-medium">Consegna</span>
                {delivery && <span className={`text-xs ${delivery.covered ? 'text-emerald-700' : 'text-ink-2'}`} title={delivery.reason}>{delivery.covered ? 'già inclusa' : `${fmtTok(delivery.cost)} token`}</span>}
                <div className="ml-auto flex flex-wrap items-center gap-2">
                  <button onClick={() => onExport('xlsx')} className="btn"><Download className="w-3.5 h-3.5" />Excel</button>
                  <button onClick={() => onExport('pdf')} className="btn"><Download className="w-3.5 h-3.5" />PDF</button>
                  <button onClick={onRegister} className="btn-primary flex items-center gap-1.5"><ShieldCheck className="w-3.5 h-3.5" />Registra l’impronta</button>
                </div>
              </div>
            </div>
          )}

          {validation && <WorkPackages bando={bando} projectId={request.project_id} validation={validation} request={request} />}
        </>
      )}
    </div>
  )
}
