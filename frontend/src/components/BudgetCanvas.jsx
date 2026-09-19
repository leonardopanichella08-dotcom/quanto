import React, { useMemo, useRef, useState } from 'react'
import { AlertTriangle, Download, FileSpreadsheet, FlaskConical, Info, Layers, Loader2, Play, Plus, ShieldCheck, Sparkles, Upload, X } from 'lucide-react'
import LineEditor from './LineEditor'
import PageIntro from './PageIntro'
import { api } from '../lib/api'
import { BANDO_STATUS_STYLE, CATEGORY_LABEL, CATEGORY_ORDER, STATUS_LABEL, STATUS_STYLE, fmtEur, fmtNum, fmtPct } from '../lib/format'

const NEW_ITEM = {
  PERSONNEL: { ccnl_code: 'TERZO_SETTORE', employee_level: '3', ral_eur: 30000, fte_allocation: 0.5, duration_months: 12 },
  CAPITAL_ASSETS: { amount_eur: 10000, asset_nature: 'HARDWARE' },
  CONSULTING: { amount_eur: 10000 },
  OVERHEAD: { amount_eur: 5000 },
  TRAINING: { amount_eur: 5000 },
}
const OUTCOME_STYLE = {
  PASS: 'text-emerald-300', ADJUSTED: 'text-amber-300', REJECTED: 'text-red-300', SUSPENDED: 'text-sky-300',
}

function SummaryCard({ label, value, tone = 'text-neutral-100', note }) {
  return (
    <div className="card p-4 min-w-0">
      <span className="label">{label}</span>
      <div className={`text-base sm:text-xl md:text-2xl font-bold mt-1.5 font-mono break-all ${tone}`}>{value}</div>
      <p className="text-[11px] text-neutral-500 mt-1">{note}</p>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between gap-4 py-1 border-b border-neutral-800/60 last:border-0 text-xs">
      <span className="text-neutral-500">{label}</span>
      <span className="font-mono text-neutral-200 text-right break-all">{value}</span>
    </div>
  )
}

function Inspector({ item, steps }) {
  if (!item) return <p className="text-xs text-neutral-500 italic p-6 text-center">Seleziona una voce per vedere l’origine del calcolo e ogni criterio applicato, passo per passo.</p>
  const b = item.breakdown
  return (
    <div className="space-y-4 text-xs">
      <div className="p-3 bg-neutral-950 rounded-xl border border-neutral-800">
        <p className="font-bold text-sm text-neutral-200">{item.description}</p>
        <p className="font-mono text-neutral-400 text-[11px]">{item.item_id} · {CATEGORY_LABEL[item.category]}</p>
        <p className="mt-2 flex flex-wrap gap-x-4 gap-y-1 font-mono text-[11px]">
          <span>originale <span className="text-neutral-200">{fmtEur(item.original_cost_eur)}</span></span>
          <span>ammesso <span className="text-emerald-300">{fmtEur(item.computed_cost_eur)}</span></span>
        </p>
      </div>

      {item.rejection_reason && (
        <div className="p-3 bg-amber-500/10 border border-amber-500/20 text-amber-300 rounded-xl space-y-1">
          <span className="font-bold flex items-center gap-1"><AlertTriangle className="w-3.5 h-3.5" /> Perché</span>
          <p className="text-[11px] leading-relaxed">{item.rejection_reason}</p>
        </div>
      )}

      <div className="p-3 bg-neutral-950 rounded-xl border border-neutral-800 space-y-1">
        <span className="text-neutral-500 font-semibold">Fonti dati</span>
        <Row label="Fonte C (documento)" value={b.source_c_ref || '— mancante —'} />
        {b.ccnl_table_ref && <Row label="Fonte B (tabella)" value={b.ccnl_table_ref} />}
        <Row label="Fonte A (regole bando)" value={b.rule_version_hash} />
        {b.hourly_cap_eur != null && <Row label="Tetto orario di bando" value={`${fmtNum(b.hourly_cap_eur)} €/h`} />}
        {b.budget_cap_pct != null && <Row label="Massimale % di bando" value={fmtPct(b.budget_cap_pct)} />}
      </div>

      {item.category === 'PERSONNEL' && b.annual_cost_eur != null && (
        <div className="p-3 bg-neutral-950 rounded-xl border border-neutral-800 space-y-1">
          <span className="text-neutral-500 font-semibold">Formula del costo del personale</span>
          <Row label="RAL" value={fmtEur(b.ral_eur)} />
          <Row label={`Oneri sociali (${fmtPct(b.social_charges_pct, 2)})`} value={fmtEur(b.social_charges_eur)} />
          <Row label={`TFR (${fmtPct(b.tfr_pct, 2)})`} value={fmtEur(b.tfr_eur)} />
          <Row label="Costo annuo lordo" value={fmtEur(b.annual_cost_eur)} />
          <Row label="Costo orario" value={`${fmtNum(item.hourly_rate_computed)} €/h (÷ ${b.working_hours} ore)`} />
          <Row label="FTE × durata" value={`${b.fte_allocation} × ${b.duration_months} mesi`} />
        </div>
      )}

      <div className="p-3 bg-neutral-950 rounded-xl border border-neutral-800 space-y-2">
        <span className="text-neutral-500 font-semibold">Cosa è successo, passo per passo</span>
        {steps.map((s) => (
          <div key={s.seq} className="flex gap-2 text-[11px] border-b border-neutral-900 pb-1.5 last:border-0">
            <span className="font-mono text-[#deffac] shrink-0 w-8">#{s.criterion}</span>
            <div className="min-w-0">
              <span className={`font-bold ${OUTCOME_STYLE[s.outcome]}`}>{s.outcome === 'PASS' ? 'ok' : s.outcome.toLowerCase()}</span>
              {s.delta_eur !== 0 && <span className="font-mono text-neutral-300"> {fmtEur(s.delta_eur)}</span>}
              <p className="text-neutral-500 leading-snug">{s.note}</p>
            </div>
          </div>
        ))}
        {item.criteria_not_evaluated.length > 0 && (
          <p className="text-[10px] text-neutral-500">Non valutati (dato o regola mancante): {item.criteria_not_evaluated.map((c) => `#${c}`).join(' ')}</p>
        )}
      </div>

      <div className="p-3 bg-neutral-950 rounded-xl border border-neutral-800 space-y-1">
        <span className="text-neutral-500">Hash SHA-256 della riga (foglia Merkle)</span>
        <p className="font-mono text-[10px] text-[#deffac] break-all p-2 bg-black rounded">{item.item_hash_sha256}</p>
      </div>
    </div>
  )
}

export default function BudgetCanvas({
  bandi, bando, request, fields, validation, loading, error, busy, importInfo,
  onSelectBando, onProjectId, onItemsChange, onDemo, onImport, onValidate, onRegister, onExport, onOpenLab, onDismissImport, onGoBandi,
}) {
  const [selectedId, setSelectedId] = useState(null)
  const [panel, setPanel] = useState('inspect')
  const [addOpen, setAddOpen] = useState(false)
  const fileRef = useRef(null)
  const items = request.cost_items
  const byId = useMemo(() => Object.fromEntries((validation?.items || []).map((i) => [i.item_id, i])), [validation])
  const selectedInput = items.find((i) => i.item_id === selectedId) || null
  const selectedResult = selectedId ? byId[selectedId] : null
  const steps = useMemo(() => (validation?.trace?.steps || []).filter((s) => s.item_id === selectedId), [validation, selectedId])

  const groups = CATEGORY_ORDER.map((c) => [c, items.filter((i) => i.category === c)]).filter(([, l]) => l.length)
  const nextId = () => { let n = items.length + 1; while (items.some((i) => i.item_id === `NEW-${String(n).padStart(3, '0')}`)) n += 1; return `NEW-${String(n).padStart(3, '0')}` }

  const add = (cat) => {
    const item = { item_id: nextId(), description: `Nuova voce — ${CATEGORY_LABEL[cat]}`, category: cat, source_c_ref: '', ...NEW_ITEM[cat] }
    onItemsChange([...items, item]); setSelectedId(item.item_id); setPanel('edit'); setAddOpen(false)
  }
  const update = (item) => { onItemsChange(items.map((i) => (i.item_id === selectedId ? item : i))); setSelectedId(item.item_id) }
  const remove = () => { onItemsChange(items.filter((i) => i.item_id !== selectedId)); setSelectedId(null) }
  const duplicate = () => { const c = { ...selectedInput, item_id: nextId() }; onItemsChange([...items, c]); setSelectedId(c.item_id) }
  const pick = (id) => { setSelectedId(id); if (panel !== 'edit') setPanel('inspect') }

  const statusCount = validation ? validation.items.reduce((a, i) => ({ ...a, [i.status]: (a[i.status] || 0) + 1 }), {}) : {}

  return (
    <div className="space-y-6">
      <PageIntro title="Budget canvas (Missione Uno)" tips={['Scegli il bando, poi carica uno scenario demo, importa un Excel o aggiungi voci a mano (tutte le categorie).', 'Clicca una voce per vedere ogni criterio applicato o modificarne i campi: il ricalcolo è sul server.', 'Registra la Merkle Root o esporta in XLSX/PDF con CEP-ID e QR.']}>
        Qui il budget di una candidatura viene validato voce per voce con i 60 criteri, alle regole del bando scelto.
      </PageIntro>

      {/* barra del bando */}
      <div className="card p-4 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="label shrink-0">Bando</span>
          <select value={bando?.bando_id || ''} onChange={(e) => onSelectBando(e.target.value)} disabled={busy} className="bg-neutral-950 border border-neutral-700 rounded-xl px-3 py-2 text-xs max-w-[260px] md:max-w-sm">
            <option value="" disabled>Scegli un bando…</option>
            {bandi.map((b) => <option key={b.bando_id} value={b.bando_id}>{b.name}</option>)}
          </select>
        </div>
        {bando && (
          <>
            <span className={`px-2 py-0.5 text-[10px] font-bold rounded border ${BANDO_STATUS_STYLE(bando.status || '')}`}>{(bando.status || '').split(' (')[0]}</span>
            <span className="text-[11px] text-neutral-400 font-mono">{bando.rules.length} regole · {bando.coverage_summary.REGOLA_DEL_BANDO}/60 criteri attivati dal bando</span>
            {bando.not_specified?.length > 0 && <button onClick={onGoBandi} className="text-[11px] text-amber-300 hover:underline flex items-center gap-1"><AlertTriangle className="w-3 h-3" />{bando.not_specified.length} lacune del bando</button>}
          </>
        )}
        <label className="flex items-center gap-2 md:ml-auto text-[11px] text-neutral-400 w-full md:w-auto min-w-0">Progetto
          <input value={request.project_id} onChange={(e) => onProjectId(e.target.value)} className="bg-neutral-950 border border-neutral-800 rounded-lg px-2 py-1.5 font-mono text-xs w-full md:w-56 min-w-0" />
        </label>
      </div>
      {!bando && (
        <div className="card p-8 text-center space-y-3">
          <Layers className="w-8 h-8 text-neutral-600 mx-auto" />
          <p className="text-sm text-neutral-300">Per iniziare scegli il bando su cui vuoi lavorare.</p>
          <button onClick={onGoBandi} className="btn-primary">Apri la biblioteca dei bandi</button>
        </div>
      )}

      {bando && (
        <>
          {/* barra strumenti */}
          <div className="flex flex-wrap items-center gap-2">
            <button onClick={() => onDemo('stress')} disabled={busy} className="px-3 py-2 rounded-xl border border-violet-500/40 text-violet-200 hover:bg-violet-500/10 text-xs font-bold flex items-center gap-1.5 disabled:opacity-50"><FlaskConical className="w-3.5 h-3.5" />Stress-test 46 voci (tutti i 60 criteri)</button>
            <button onClick={() => onDemo('realistic')} disabled={busy} className="px-3 py-2 rounded-xl border border-neutral-700 text-neutral-200 hover:border-neutral-500 text-xs font-bold flex items-center gap-1.5 disabled:opacity-50"><Sparkles className="w-3.5 h-3.5" />Progetto realistico</button>
            <button onClick={() => fileRef.current?.click()} disabled={busy} className="px-3 py-2 rounded-xl border border-neutral-700 text-neutral-200 hover:border-neutral-500 text-xs font-bold flex items-center gap-1.5 disabled:opacity-50"><Upload className="w-3.5 h-3.5" />Importa Excel/CSV</button>
            <input ref={fileRef} type="file" accept=".xlsx,.csv" className="hidden" onChange={(e) => { if (e.target.files?.[0]) onImport(e.target.files[0]); e.target.value = '' }} />
            <a href={api.templateUrl} className="px-3 py-2 rounded-xl border border-neutral-800 text-neutral-400 hover:text-white text-xs font-bold flex items-center gap-1.5"><FileSpreadsheet className="w-3.5 h-3.5" />Template Excel</a>
            <div className="relative">
              <button onClick={() => setAddOpen(!addOpen)} className="px-3 py-2 rounded-xl border border-neutral-700 text-neutral-200 hover:border-neutral-500 text-xs font-bold flex items-center gap-1.5"><Plus className="w-3.5 h-3.5" />Aggiungi voce</button>
              {addOpen && (
                <div className="absolute z-20 mt-1 w-48 card p-1 shadow-xl">
                  {CATEGORY_ORDER.map((c) => <button key={c} onClick={() => add(c)} className="w-full text-left px-3 py-2 text-xs rounded-lg hover:bg-neutral-800">{CATEGORY_LABEL[c]}</button>)}
                </div>
              )}
            </div>
            <button onClick={onValidate} disabled={loading || !items.length} className="btn-primary ml-auto flex items-center gap-1.5">
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}{loading ? 'Esecuzione…' : 'Esegui validazione'}
            </button>
          </div>

          {importInfo && (
            <div className={`p-3 rounded-xl border text-xs space-y-1 ${importInfo.errors.length ? 'border-amber-500/30 bg-amber-500/10 text-amber-200' : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200'}`}>
              <div className="flex justify-between"><span className="font-bold">Import: {importInfo.items.length} voci valide su {importInfo.rows_read} righe{importInfo.errors.length ? `, ${importInfo.errors.length} con errori` : ''}</span>
                <button onClick={onDismissImport}><X className="w-3.5 h-3.5" /></button></div>
              {importInfo.errors.slice(0, 8).map((e) => <p key={e.row} className="font-mono text-[11px]">riga {e.row}: {e.message}</p>)}
              {importInfo.ignored_columns.length > 0 && <p className="text-[11px]">Colonne ignorate: {importInfo.ignored_columns.join(', ')}</p>}
            </div>
          )}
          {error && <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-xs">{error}</div>}

          {/* riepilogo */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <SummaryCard label="Conformity score" value={validation ? `${validation.conformity_score}/100` : '—'} tone="text-[#deffac]" note="% controlli superati su quelli eseguiti" />
            <SummaryCard label="Richiesto" value={fmtEur(validation?.total_requested_eur)} note={`${items.length} voci in ${groups.length} categorie`} />
            <SummaryCard label="Ammesso" value={fmtEur(validation?.total_approved_eur)} tone="text-emerald-400" note={validation ? `${statusCount.APPROVED || 0} ok · ${statusCount.CAP_EXCEEDED_ADJUSTED || 0} decurtate` : 'Esegui la validazione'} />
            <SummaryCard label="Escluso o decurtato" value={fmtEur(validation?.total_rejected_eur)} tone="text-amber-400" note={validation ? `${statusCount.REJECTED || 0} respinte · ${statusCount.MISSING_DOCUMENTS || 0} sospese` : '—'} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 items-start">
            <div className="lg:col-span-3 card p-4 space-y-4">
              {items.length === 0 && <p className="text-sm text-neutral-500 italic text-center p-8">Nessuna voce. Carica uno scenario demo, importa un Excel o aggiungi una voce.</p>}
              {groups.map(([cat, list]) => (
                <div key={cat} className="space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] text-neutral-500 uppercase tracking-wider font-semibold px-1">
                    <span>{CATEGORY_LABEL[cat]} ({list.length})</span>
                    {validation && <span className="font-mono normal-case">{fmtEur(list.reduce((s, i) => s + (byId[i.item_id]?.computed_cost_eur || 0), 0))}</span>}
                  </div>
                  {list.map((it) => {
                    const r = byId[it.item_id]
                    return (
                      <button key={it.item_id} onClick={() => pick(it.item_id)}
                        className={`w-full text-left p-3 bg-neutral-950 border rounded-xl flex items-center gap-3 transition hover:border-neutral-600 ${selectedId === it.item_id ? 'border-[#deffac]' : 'border-neutral-800'}`}>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-semibold text-neutral-200 truncate">{it.description}</p>
                          <p className="text-[10px] text-neutral-500 font-mono">{it.item_id}{r && r.criteria_failed.length ? ` · falliti: ${r.criteria_failed.map((c) => `#${c}`).join(' ')}` : ''}</p>
                        </div>
                        {r && <span className={`px-2 py-0.5 text-[10px] font-bold rounded border shrink-0 ${STATUS_STYLE[r.status]}`}>{STATUS_LABEL[r.status]}</span>}
                        <div className="text-right shrink-0 w-28">
                          <div className="font-mono text-xs font-bold text-neutral-100">{r ? fmtEur(r.computed_cost_eur) : fmtEur(it.ral_eur ?? it.amount_eur)}</div>
                          {r && r.original_cost_eur !== r.computed_cost_eur && <div className="font-mono text-[10px] text-amber-400/80 line-through">{fmtEur(r.original_cost_eur)}</div>}
                        </div>
                      </button>
                    )
                  })}
                </div>
              ))}

              {validation && (
                <div className="space-y-3 pt-2">
                  <div className="p-3 bg-neutral-950 border border-neutral-800 rounded-xl text-xs text-neutral-300 leading-relaxed">
                    <span className="label block mb-1">Sintesi ({validation.explanation_source === 'LLM' ? 'LLM, numeri validati' : 'template deterministico'})</span>
                    {validation.llm_explanation_summary}
                  </div>
                  {validation.budget_checks?.length > 0 && (
                    <div className="p-3 bg-neutral-950 border border-neutral-800 rounded-xl space-y-1.5">
                      <span className="label block">Controlli sull’intero budget</span>
                      {validation.budget_checks.map((c) => {
                        const tone = c.status === 'PASS' ? 'text-emerald-400' : c.status === 'FAIL' ? 'text-red-400' : 'text-neutral-500'
                        return <div key={c.criterion} className="text-[11px] flex gap-2"><span className={`font-mono shrink-0 ${tone}`}>#{c.criterion} {c.status === 'NOT_EVALUATED' ? '—' : c.status}</span><span className="text-neutral-400">{c.title}: {c.message}</span></div>
                      })}
                    </div>
                  )}
                  <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-neutral-800">
                    <span className="font-mono text-[11px] text-neutral-500">{validation.cep_id} · root {validation.merkle_root.slice(0, 18)}…</span>
                    <div className="flex flex-wrap gap-2">
                      <button onClick={onOpenLab} className="px-3 py-2 rounded-xl border border-[#deffac]/40 text-[#deffac] hover:bg-[#deffac]/10 text-xs font-bold flex items-center gap-1.5"><Play className="w-3.5 h-3.5" />Guarda l’algoritmo in azione</button>
                      <button onClick={() => onExport('xlsx')} className="px-3 py-2 border border-neutral-700 hover:border-neutral-500 text-neutral-200 font-bold text-xs rounded-xl flex items-center gap-1.5"><Download className="w-3.5 h-3.5" />XLSX</button>
                      <button onClick={() => onExport('pdf')} className="px-3 py-2 border border-neutral-700 hover:border-neutral-500 text-neutral-200 font-bold text-xs rounded-xl flex items-center gap-1.5"><Download className="w-3.5 h-3.5" />PDF</button>
                      <button onClick={onRegister} className="btn-primary flex items-center gap-1.5"><ShieldCheck className="w-3.5 h-3.5" />Registra Merkle Root</button>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="lg:col-span-2 card p-4 space-y-3 self-start lg:sticky lg:top-24 max-h-[80vh] overflow-y-auto">
              <div className="flex gap-1 bg-neutral-950 border border-neutral-800 p-1 rounded-xl w-fit">
                <button onClick={() => setPanel('inspect')} className={`px-3 py-1.5 text-xs font-bold rounded-lg flex items-center gap-1.5 ${panel === 'inspect' ? 'bg-[#deffac] text-black' : 'text-neutral-400'}`}><Info className="w-3.5 h-3.5" />Ispettore</button>
                <button onClick={() => setPanel('edit')} disabled={!selectedInput} className={`px-3 py-1.5 text-xs font-bold rounded-lg disabled:opacity-40 ${panel === 'edit' ? 'bg-[#deffac] text-black' : 'text-neutral-400'}`}>Modifica voce</button>
              </div>
              {panel === 'inspect' ? (
                selectedResult ? <Inspector item={selectedResult} steps={steps} />
                  : <p className="text-xs text-neutral-500 italic p-6 text-center">{selectedInput ? 'Esegui la validazione per vedere l’analisi di questa voce, oppure passa a “Modifica voce”.' : 'Seleziona una voce dall’elenco.'}</p>
              ) : selectedInput && fields ? (
                <LineEditor item={selectedInput} fields={fields} onChange={update} onDelete={remove} onDuplicate={duplicate} />
              ) : <p className="text-xs text-neutral-500 italic p-6 text-center">Seleziona una voce da modificare.</p>}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
