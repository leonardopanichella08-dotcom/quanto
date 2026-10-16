import React, { useEffect, useState } from 'react'
import { AlertTriangle, ChevronDown, ChevronRight, Lightbulb, Loader2 } from 'lucide-react'
import { api } from '../lib/api'
import { CATEGORY_LABEL, fmtEur } from '../lib/format'

const NATURE = {
  NUOVA: ['nuova', 'border-emerald-500/30 text-emerald-700', 'Una spesa che il progetto causa (un acquisto, un’assunzione): è ciò che un bando finanzia.'],
  ORDINARIA: ['corrente', 'border-amber-500/30 text-amber-700', 'L’azienda la sostiene comunque. Per i bandi a progetto non è una spesa di progetto (entrano solo spese generali a forfait o personale realmente dedicato con timesheet); per i bandi sulle spese correnti (spese commerciali, liquidità, ristori) è una base valida.'],
  DA_QUANTIFICARE: ['da quantificare', 'border-line-strong text-ink-2', 'Non si ricava dai documenti: serve un preventivo.'],
}

function Idea({ idea, active, onAllocate }) {
  const [open, setOpen] = useState(false)
  return (
    <div className={`rounded-2xl border p-4 space-y-2.5 text-xs ${active ? 'border-brand/60 bg-brand/5' : 'border-line bg-field'}`}>
      <div className="flex flex-wrap items-start gap-2">
        <div className="min-w-0 flex-1"><p className="text-sm font-semibold text-ink break-words">{idea.title}</p>
          <p className="text-[11px] text-mute">{idea.project_type_labels.join(' · ')}</p></div>
        <div className="text-right"><span className="label">Spese nuove</span><div className="text-base font-semibold text-emerald-700 tabular-nums">{fmtEur(idea.new_eur)}</div>
          {idea.ordinary_eur > 0 && <div className="text-[11px] text-amber-700 tabular-nums">+ {fmtEur(idea.ordinary_eur)} correnti</div>}</div>
      </div>
      {idea.why.map((w) => <p key={w} className="text-ink-2 leading-relaxed">{w}</p>)}
      {idea.cautions.map((c) => <p key={c} className="text-amber-700 flex gap-1.5"><AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />{c}</p>)}
      <button className="text-ink-2 underline" onClick={() => setOpen(!open)}>{open ? 'Nascondi' : 'Spese, cosa manca e bandi'}</button>
      {open && (
        <div className="space-y-3 pt-2 border-t border-line">
          <div className="overflow-x-auto"><table className="w-full"><thead><tr className="text-left text-mute"><th className="font-medium py-1">Spesa</th><th className="font-medium">Natura</th><th className="font-medium text-right">Importo</th></tr></thead>
            <tbody>{idea.lines.map((l) => { const [nl, tone, hint] = NATURE[l.nature]; return (
              <tr key={l.item_id} className="border-t border-line align-top"><td className="py-1 text-ink-2">{l.label}<span className="block text-[10px] text-mute">{CATEGORY_LABEL[l.category]} · {l.detail}</span>
                {l.quotes?.length > 0 && <span className="block text-[10px] text-emerald-700">{l.quotes.length === 1 ? 'Preventivo' : 'Preventivi'}: {l.quotes.map((q) => `${q.supplier} ${fmtEur(q.net_eur)}${q.valid_until ? ` (valido fino al ${q.valid_until})` : ''}`).join(' · ')}{l.plan_amount_eur ? ` — nel piano ${fmtEur(l.plan_amount_eur)}` : ''}</span>}</td>
                <td><span title={hint} className={`px-1.5 py-0.5 rounded border text-[10px] ${tone}`}>{nl}</span></td><td className="text-right tabular-nums">{l.amount_eur == null ? '—' : fmtEur(l.amount_eur)}</td></tr>) })}</tbody></table></div>
          {idea.missing.length > 0 && <div><p className="font-medium text-ink">Cosa manca per farne un budget presentabile</p>{idea.missing.map((m) => <p key={m} className="text-ink-2">• {m}</p>)}</div>}
          <div><p className="font-medium text-ink">Bandi che finanziano questo tipo di progetto · {idea.bandi.length}</p>
            {idea.bandi.length === 0 && <p className="text-mute">Nessuno dei bandi studiati nomina questo tipo di progetto: studiane altri dalla pagina Bandi.</p>}
            {idea.bandi.map((b) => <div key={b.bando_id} className="mt-1"><p className="text-ink-2">{b.name} <span className="text-mute">· {b.types.join(', ')}{b.mode ? ` · ${b.needs_project ? 'a progetto' : b.mode.toLowerCase()}` : ''}{b.ordinary_costs_ok ? ' · ammette le spese correnti come base' : ''}</span></p>{b.evidence && <p className="text-[11px] text-mute">«{b.evidence}»</p>}</div>)}</div>
        </div>
      )}
      <div className="flex flex-wrap items-center gap-2 pt-1">
        <button className="btn-primary !py-1" disabled={idea.new_eur + idea.ordinary_eur <= 0} onClick={() => onAllocate(idea)}>{active ? 'Progetto in uso' : 'Calcola questo progetto'}</button>
        {idea.new_eur <= 0 && idea.ordinary_eur > 0 && <span className="text-mute">Senza spese nuove conta solo se includi le spese correnti (comando in alto).</span>}
        {idea.new_eur + idea.ordinary_eur <= 0 && <span className="text-mute">Senza spese quantificate non c’è ancora nulla da pianificare.</span>}
      </div>
    </div>
  )
}

/** Idee di progetto dai documenti dell'azienda: un bando finanzia progetti, non costi. Ogni idea dice cosa la compone, cosa manca e quali bandi la finanziano. */
export default function ProjectIdeas({ year, active, onAllocate, onClear, includeCurrent, setIncludeCurrent }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  useEffect(() => {
    let live = true
    setLoading(true); setError(null)
    api.profileIdeas(year ? Number(year) : undefined).then((d) => { if (live) setData(d) }).catch((e) => { if (live) { setError(e.message); setData(null) } }).finally(() => { if (live) setLoading(false) })
    return () => { live = false }
  }, [year])
  return (
    <div className="space-y-4">
      <p className="text-xs text-ink-2 leading-snug">Progetti ricavati dai documenti dell’azienda. Sono ipotesi da validare: un importo che non viene da un documento non lo invento.</p>
      {loading && <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Costruisco le idee…</p>}
      {error && <p className="text-xs text-red-700">{error}</p>}
      {active && <div className="flex flex-wrap items-center gap-2 text-xs p-2.5 rounded-lg border border-brand/40 bg-brand/5"><Lightbulb className="w-3.5 h-3.5" />Progetto in uso: «{active.title}»<button className="btn !py-1 ml-auto" onClick={onClear}>Rimuovi il progetto</button></div>}
      <label className="inline-flex items-center gap-2 text-xs text-ink-2"><input type="checkbox" checked={!!includeCurrent} onChange={(e) => setIncludeCurrent?.(e.target.checked)} />Conta anche le spese correnti (per i bandi che le ammettono)</label>
      {data && data.ideas.length === 0 && <p className="text-xs text-mute">Nei documenti non ci sono ancora elementi per proporre progetti: carica il piano degli investimenti, il libro cespiti o il piano delle assunzioni.</p>}
      <div className="grid lg:grid-cols-2 gap-4">{(data?.ideas || []).map((i) => <Idea key={i.id} idea={i} active={active?.id === i.id} onAllocate={onAllocate} />)}</div>
      {data?.no_project?.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-line">
          <p className="text-sm font-medium text-ink">Misure che non chiedono un progetto · {data.no_project.length}</p>
          <p className="text-xs text-ink-2 leading-relaxed">Si accede per requisiti, per acquisti qualificati, per un finanziamento o per spese commerciali: il budget è un’altra cosa, e per molte di queste le spese e i dati dell’azienda sono la base giusta.</p>
          <div className="grid lg:grid-cols-2 gap-3">{data.no_project.map((m) => (
            <div key={m.bando_id} className="rounded-xl border border-line bg-field p-3 text-xs space-y-1"><p className="font-medium text-ink">{m.name}</p><p className="text-[11px] text-mute">{m.mode}</p>
              <p className="text-ink-2">Si calcola su {m.base}.</p><p className="text-mute">Esempio: {m.example}</p></div>))}</div>
        </div>
      )}
      {data?.notes.map((n) => <p key={n} className="text-[11px] text-mute">• {n}</p>)}
    </div>
  )
}
