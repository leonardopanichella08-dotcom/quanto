import React, { useEffect, useState } from 'react'
import { ChevronDown, ChevronRight, Loader2 } from 'lucide-react'
import { api } from '../lib/api'
import { CATEGORY_LABEL, fmtEur } from '../lib/format'

/** Cosa QUANTO ha capito dai documenti oltre ai totali: le spese per voce (affitti, energia, licenze…), l'organico persona per persona e i beni. Serve a far vedere che nulla è stato ignorato. */
export default function DocumentFacts({ version = 0 }) {
  const [open, setOpen] = useState(false)
  const [tab, setTab] = useState('spese')
  const [data, setData] = useState({})
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  useEffect(() => {
    if (!open) return
    setLoading(true); setError(null)
    Promise.allSettled([api.profileExpenses(), api.profileStaff(), api.profileAssets(), api.profileFacts()]).then(([e, s, a, f]) => {
      setData({ expenses: e.value, staff: s.value, assets: a.value, facts: f.value })
      if (e.status === 'rejected' && !s.value && !a.value) setError(e.reason?.message || 'Non ci sono ancora dati letti')
    }).finally(() => setLoading(false))
  }, [open, version])
  const { expenses, staff, assets, facts } = data
  const tabs = [['spese', `Spese per voce${expenses ? ` · ${expenses.types.length}` : ''}`], ['organico', `Organico${staff?.people?.length ? ` · ${staff.people.length}` : ''}`], ['beni', `Beni${assets?.assets?.length ? ` · ${assets.assets.length}` : ''}`]]
  return (
    <div className="card">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center gap-2 px-4 py-3 text-left text-sm font-medium">
        {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}Cosa ho letto dai documenti
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3">
          <p className="text-xs text-ink-2 leading-relaxed">Oltre ai totali per categoria, QUANTO legge ogni riga dei bilanci e dei fogli Excel: le spese una per una, le persone con livello e RAL, i beni con il loro ammortamento. Con questi dati costruisce il budget voce per voce.</p>
          {facts && Object.keys(facts.counts || {}).length > 0 && <p className="text-[11px] text-mute">Dai documenti: {Object.entries(facts.counts).map(([k, n]) => `${n} ${{ staff_member: 'persone', asset_line: 'beni', dep_plan_line: 'righe di ammortamento', supplier_spend: 'voci di spesa dalle fatture', aid_received: 'aiuti', capex_plan: 'investimenti', hiring_plan: 'assunzioni', budget_line: 'conti di budget', durc: 'DURC', lease: 'contratto di locazione', rd_credit: 'credito di ricerca e sviluppo', loan: 'finanziamento' }[k] || k}`).join(' · ')}.</p>}
          <div className="flex flex-wrap gap-2">{tabs.map(([k, l]) => <button key={k} onClick={() => setTab(k)} aria-pressed={tab === k} className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${tab === k ? 'bg-brand/25 text-brand-ink border-brand/60' : 'border-line text-ink-2 hover:border-line-strong'}`}>{l}</button>)}</div>
          {loading && <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Carico…</p>}
          {error && <p className="text-xs text-amber-700">{error}</p>}
          {tab === 'spese' && expenses && (
            <div className="overflow-x-auto"><table className="w-full text-xs"><thead><tr className="text-left text-mute"><th className="py-1 font-medium">Voce di spesa nel bilancio {expenses.year}</th><th className="font-medium">Categoria</th><th className="font-medium text-right">Righe</th><th className="font-medium text-right">Importo</th></tr></thead>
              <tbody>{expenses.types.map((t) => <tr key={t.code} className="border-t border-line"><td className="py-1 text-ink-2">{t.label}</td><td className="text-mute">{CATEGORY_LABEL[t.category] || t.category}</td><td className="text-right tabular-nums">{t.lines}</td><td className="text-right tabular-nums">{fmtEur(t.amount_eur)}</td></tr>)}</tbody></table>
              {expenses.pending_lines > 0 && <p className="text-[11px] text-amber-700 mt-1">{expenses.pending_lines} righe sono ancora da verificare e non sono incluse.</p>}</div>
          )}
          {tab === 'organico' && staff && (
            staff.people.length === 0 ? <p className="text-xs text-mute">Nessuna persona letta: carica il registro del personale (Excel) o le buste paga.</p> : (
              <div className="overflow-x-auto"><table className="w-full text-xs"><thead><tr className="text-left text-mute"><th className="py-1 font-medium">Persona</th><th className="font-medium">Livello</th><th className="font-medium">Contratto</th><th className="font-medium">CCNL</th><th className="font-medium text-right">Ore/sett.</th><th className="font-medium text-right">RAL</th></tr></thead>
                <tbody>{staff.people.map((p) => <tr key={p.token} className="border-t border-line"><td className="py-1 text-ink-2">{p.role || 'Persona'} <span className="text-mute">{p.ref}</span></td><td>{p.level || '—'}</td><td className="text-mute">{p.contract || '—'}</td><td>{p.ccnl_code ? p.ccnl_code.toLowerCase() : <span className="text-amber-700">da indicare</span>}</td><td className="text-right tabular-nums">{p.hours_week ?? '—'}</td><td className="text-right tabular-nums">{fmtEur(p.ral_eur ?? p.payslip_ral_eur)}</td></tr>)}</tbody></table>
                {staff.missing.map((m) => <p key={m} className="text-[11px] text-amber-700 mt-1">{m}</p>)}</div>
            )
          )}
          {tab === 'beni' && assets && (
            assets.assets.length === 0 ? <p className="text-xs text-mute">Nessun libro cespiti letto.</p> : (
              <div className="overflow-x-auto"><table className="w-full text-xs"><thead><tr className="text-left text-mute"><th className="py-1 font-medium">Classe di beni</th><th className="font-medium text-right">Beni</th><th className="font-medium text-right">Costo storico</th><th className="font-medium text-right">Valore residuo</th></tr></thead>
                <tbody>{Object.entries(assets.by_class).map(([c, v]) => <tr key={c} className="border-t border-line"><td className="py-1 text-ink-2">{c}</td><td className="text-right tabular-nums">{v.assets}</td><td className="text-right tabular-nums">{fmtEur(v.cost_eur)}</td><td className="text-right tabular-nums">{fmtEur(v.net_eur)}</td></tr>)}</tbody></table>
                {Object.keys(assets.depreciation_by_year).length > 0 && <p className="text-[11px] text-mute mt-1">Ammortamento previsto: {Object.entries(assets.depreciation_by_year).map(([y, v]) => `${y}: ${fmtEur(v)}`).join(' · ')}.</p>}</div>
            )
          )}
        </div>
      )}
    </div>
  )
}
