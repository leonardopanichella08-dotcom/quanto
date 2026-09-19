import React, { useState } from 'react'
import { AlertTriangle, Download, FileText, Info, ShieldCheck } from 'lucide-react'
import { fmtEur, fmtNum, fmtPct, STATUS_STYLE } from '../lib/format'

function SummaryCard({ label, value, tone = 'text-neutral-100', note }) {
  return (
    <div className="card p-5">
      <span className="label">{label}</span>
      <div className={`text-2xl font-bold mt-2 font-mono ${tone}`}>{value}</div>
      <p className="text-xs text-neutral-500 mt-1">{note}</p>
    </div>
  )
}

function Row({ label, value, mono = true }) {
  return (
    <div className="flex justify-between gap-4 py-1 border-b border-neutral-800/60 last:border-0">
      <span className="text-neutral-500">{label}</span>
      <span className={`${mono ? 'font-mono' : ''} text-neutral-200 text-right break-all`}>{value}</span>
    </div>
  )
}

function Inspector({ item }) {
  if (!item) {
    return <p className="text-xs text-neutral-500 italic p-6 text-center">Clicca un importo nella tabella per ispezionare fonte contabile, tabella CCNL, norma e formula.</p>
  }
  const b = item.breakdown
  const isPersonnel = item.category === 'PERSONNEL'
  return (
    <div className="space-y-4 text-xs">
      <div className="p-3 bg-neutral-950 rounded-xl border border-neutral-800">
        <span className="text-neutral-500">Voce selezionata</span>
        <p className="font-bold text-sm text-neutral-200">{item.description}</p>
        <p className="font-mono text-neutral-400 text-[11px]">{item.item_id} · {item.category}</p>
      </div>

      <div className="p-3 bg-neutral-950 rounded-xl border border-neutral-800 space-y-1">
        <span className="text-neutral-500 font-semibold">Fonti dati utilizzate</span>
        <Row label="Fonte C (documento)" value={b.source_c_ref || '— mancante —'} />
        {b.ccnl_table_ref && <Row label="Fonte B (tabella)" value={b.ccnl_table_ref} />}
        <Row label="Fonte A (regola bando)" value={b.rule_version_hash} />
        {b.hourly_cap_eur != null && <Row label="Tetto orario di bando" value={`${fmtNum(b.hourly_cap_eur)} €/h`} />}
        {b.budget_cap_pct != null && <Row label="Massimale % di bando" value={fmtPct(b.budget_cap_pct)} />}
      </div>

      {isPersonnel && b.annual_cost_eur != null && (
        <div className="p-3 bg-neutral-950 rounded-xl border border-neutral-800 space-y-1">
          <span className="text-neutral-500 font-semibold">Formula (calcolata dal server)</span>
          <Row label="RAL" value={fmtEur(b.ral_eur)} />
          <Row label={`Oneri sociali (${fmtPct(b.social_charges_pct, 2)})`} value={fmtEur(b.social_charges_eur)} />
          <Row label={`TFR (${fmtPct(b.tfr_pct, 2)})`} value={fmtEur(b.tfr_eur)} />
          <Row label="Costo annuo lordo" value={fmtEur(b.annual_cost_eur)} />
          <Row label="Ore lavorabili (divisore)" value={b.working_hours} />
          <Row label="Costo orario" value={`${fmtNum(item.hourly_rate_computed)} €/h`} />
          <Row label="FTE × durata" value={`${b.fte_allocation} × ${b.duration_months} mesi`} />
          <Row label="Costo originario" value={fmtEur(item.original_cost_eur)} />
          <Row label="Importo ammesso" value={fmtEur(item.computed_cost_eur)} />
        </div>
      )}

      <div className="p-3 bg-neutral-950 rounded-xl border border-neutral-800 space-y-2">
        <span className="text-neutral-500 font-semibold">Criteri eseguiti</span>
        <div className="flex flex-wrap gap-1.5">
          {item.criteria_checked.map((c) => (
            <span key={c} className={`px-1.5 py-0.5 rounded font-mono text-[10px] border ${item.criteria_failed.includes(c) ? 'bg-amber-500/10 border-amber-500/30 text-amber-300' : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'}`}>#{c}</span>
          ))}
        </div>
        {item.criteria_not_evaluated?.length > 0 && (
          <div className="pt-1 space-y-1">
            <span className="text-neutral-500">Non valutati (dato o regola di bando mancante)</span>
            <div className="flex flex-wrap gap-1.5">
              {item.criteria_not_evaluated.map((c) => (
                <span key={c} title="Non eseguito: non conta come superato" className="px-1.5 py-0.5 rounded font-mono text-[10px] border border-neutral-700 text-neutral-500">#{c}</span>
              ))}
            </div>
          </div>
        )}
        <div className="space-y-1 pt-1">
          {item.applied_rules.map((r, i) => (
            <div key={i} className="p-1.5 bg-neutral-900 rounded font-mono text-[10px] text-neutral-300 break-all">{r}</div>
          ))}
        </div>
      </div>

      {item.rejection_reason && (
        <div className="p-3 bg-amber-500/10 border border-amber-500/20 text-amber-300 rounded-xl space-y-1">
          <span className="font-bold flex items-center gap-1"><AlertTriangle className="w-3.5 h-3.5" /> Note del motore deterministico</span>
          <p className="text-[11px] leading-relaxed">{item.rejection_reason}</p>
        </div>
      )}

      <div className="p-3 bg-neutral-950 rounded-xl border border-neutral-800 space-y-1">
        <span className="text-neutral-500">Hash SHA-256 della riga (foglia Merkle)</span>
        <p className="font-mono text-[10px] text-[#deffac] break-all p-2 bg-black rounded">{item.item_hash_sha256}</p>
      </div>
    </div>
  )
}

export default function BudgetCanvas({ request, validation, loading, error, onValidate, onEditFte, onRegister, onExport, onExportPdf }) {
  const [selectedId, setSelectedId] = useState(null)
  const selected = validation?.items.find((i) => i.item_id === selectedId) ?? null
  const inputById = Object.fromEntries(request.cost_items.map((i) => [i.item_id, i]))

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <SummaryCard label="Conformity Score" value={validation ? `${validation.conformity_score}/100` : '—'} tone="text-[#deffac]" note="% controlli superati sui criteri eseguiti" />
        <SummaryCard label="Totale richiesto" value={fmtEur(validation?.total_requested_eur)} note="Costo pieno prima dei massimali" />
        <SummaryCard label="Totale ammesso" value={fmtEur(validation?.total_approved_eur)} tone="text-emerald-400" note="Importo valido per la candidatura" />
        <SummaryCard label="Totale decurtato" value={fmtEur(validation?.total_rejected_eur)} tone="text-amber-400" note="Rettifiche a tetti e massimali" />
      </div>

      {error && <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-xs">{error}</div>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-neutral-800">
            <h3 className="font-bold text-lg flex items-center gap-2"><FileText className="w-5 h-5 text-[#deffac]" />Budget validato (Missione Uno)</h3>
            <button onClick={onValidate} disabled={loading} className="btn-primary">{loading ? 'Esecuzione engine…' : 'Esegui validazione'}</button>
          </div>

          {validation ? (
            <div className="space-y-3">
              {validation.items.map((item) => {
                const input = inputById[item.item_id]
                return (
                  <div key={item.item_id} className={`p-4 bg-neutral-950 border rounded-xl transition hover:border-neutral-600 ${selectedId === item.item_id ? 'border-[#deffac]' : 'border-neutral-800'}`}>
                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-semibold text-sm">{item.description}</span>
                          <span className={`px-2 py-0.5 text-[10px] font-bold rounded border ${STATUS_STYLE[item.status]}`}>{item.status}</span>
                        </div>
                        <p className="text-xs text-neutral-500 font-mono">
                          {item.item_id}
                          {item.hourly_rate_computed > 0 && (
                            <> · <button className="num-btn" onClick={() => setSelectedId(item.item_id)}>{fmtNum(item.hourly_rate_computed)} €/h</button> (tetto {fmtNum(item.hourly_rate_cap)})</>
                          )}
                        </p>
                        {input?.category === 'PERSONNEL' && (
                          <label className="text-xs text-neutral-400 flex items-center gap-2 pt-1">
                            FTE
                            <input type="number" min="0.05" max="1" step="0.05" value={input.fte_allocation}
                              onChange={(e) => onEditFte(item.item_id, Number(e.target.value))}
                              className="w-20 bg-neutral-900 border border-neutral-700 rounded-lg px-2 py-1 font-mono text-xs" />
                            <span className="text-neutral-600">ricalcolo lato server</span>
                          </label>
                        )}
                      </div>
                      <div className="text-right shrink-0">
                        <button className="num-btn text-sm font-bold text-neutral-100" onClick={() => setSelectedId(item.item_id)}>{fmtEur(item.computed_cost_eur)}</button>
                        {item.original_cost_eur !== item.computed_cost_eur && (
                          <div className="text-[11px] text-amber-400/80 font-mono line-through decoration-amber-400/40">{fmtEur(item.original_cost_eur)}</div>
                        )}
                        <span className="text-[10px] text-neutral-500 flex items-center gap-1 justify-end mt-1"><Info className="w-3 h-3" />Ispettore</span>
                      </div>
                    </div>
                  </div>
                )
              })}

              <div className="p-3 bg-neutral-950 border border-neutral-800 rounded-xl text-xs text-neutral-300 leading-relaxed">
                <span className="label block mb-1">Sintesi ({validation.explanation_source === 'LLM' ? 'LLM, numeri validati' : 'template deterministico'})</span>
                {validation.llm_explanation_summary}
              </div>

              {validation.budget_checks?.length > 0 && (
                <div className="p-3 bg-neutral-950 border border-neutral-800 rounded-xl space-y-1.5">
                  <span className="label block">Controlli sull’intero budget</span>
                  {validation.budget_checks.map((c) => {
                    const tone = c.status === 'PASS' ? 'text-emerald-400' : c.status === 'FAIL' ? 'text-red-400' : 'text-neutral-500'
                    return (
                      <div key={c.criterion} className="text-[11px] flex gap-2">
                        <span className={`font-mono shrink-0 ${tone}`}>#{c.criterion} {c.status === 'NOT_EVALUATED' ? '—' : c.status}</span>
                        <span className="text-neutral-400">{c.title}: {c.message}</span>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          ) : (
            <div className="p-12 text-center text-neutral-500 text-sm italic bg-neutral-950 rounded-xl border border-neutral-800">
              Clicca “Esegui validazione” per calcolare il budget con il Deterministic Engine.
            </div>
          )}

          {validation && (
            <div className="pt-4 border-t border-neutral-800 flex flex-wrap justify-between gap-3 items-center">
              <div className="font-mono text-[11px] text-neutral-500">
                <span className="text-neutral-400">{validation.cep_id}</span> · root {validation.merkle_root.slice(0, 18)}…
              </div>
              <div className="flex flex-wrap gap-2">
                <button onClick={onExport} className="px-3 py-2.5 border border-neutral-700 hover:border-neutral-500 text-neutral-200 font-bold text-xs rounded-xl flex items-center gap-2 transition">
                  <Download className="w-4 h-4" />XLSX
                </button>
                <button onClick={onExportPdf} className="px-3 py-2.5 border border-neutral-700 hover:border-neutral-500 text-neutral-200 font-bold text-xs rounded-xl flex items-center gap-2 transition">
                  <Download className="w-4 h-4" />PDF
                </button>
                <button onClick={onRegister} className="px-5 py-2.5 bg-[#deffac] hover:bg-[#a8fd00] text-black font-bold text-xs rounded-xl flex items-center gap-2 transition">
                  <ShieldCheck className="w-4 h-4" />Registra Merkle Root
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="card p-6 space-y-4 self-start">
          <h3 className="label flex items-center gap-2"><Info className="w-4 h-4 text-[#deffac]" />Ispettore di riga</h3>
          <Inspector item={selected} />
        </div>
      </div>
    </div>
  )
}
