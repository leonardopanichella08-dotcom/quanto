import React, { useState } from 'react'
import { Briefcase, ChevronDown, Loader2, Pencil, Plus, Trash2 } from 'lucide-react'
import { api } from '../lib/api'
import { fmtNum } from '../lib/format'

/** Selettore del lavoro attivo (l'azienda cliente su cui si sta lavorando), sempre visibile nella barra. */
export function ClientSwitcher({ clients, clientId, onChange, onNew }) {
  if (!clients) return null
  if (clients.length === 0) return <button className="btn !py-1.5 text-xs" onClick={onNew}><Plus className="w-3.5 h-3.5" />Apri il primo lavoro</button>
  return (
    <label className="relative inline-flex items-center gap-1.5 text-xs text-ink-2" title="Il lavoro attivo: tutte le pagine mostrano i dati di questa azienda">
      <Briefcase className="w-3.5 h-3.5 text-mute shrink-0" />
      <select aria-label="Lavoro attivo" value={clientId || ''} onChange={(e) => (e.target.value === '__new' ? onNew() : onChange(Number(e.target.value)))}
        className="field !py-1.5 !pr-7 !w-auto max-w-[15rem] truncate appearance-none text-xs font-medium">
        {clients.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        <option value="__new">+ Nuovo lavoro…</option>
      </select>
      <ChevronDown className="w-3 h-3 absolute right-2 pointer-events-none text-mute" />
    </label>
  )
}

/** Quando serve un lavoro attivo e non c'è. */
export function NeedClient({ onGo }) {
  return (
    <div className="card p-8 text-center space-y-3 max-w-xl mx-auto">
      <Briefcase className="w-8 h-8 text-mute mx-auto" />
      <h3 className="font-semibold text-base">Prima apri un lavoro</h3>
      <p className="text-xs text-ink-2 leading-relaxed">Ogni azienda cliente ha il suo profilo, i suoi bilanci e i suoi risultati. Apri il lavoro dell’azienda dal Profilo dello studio e poi torna qui.</p>
      <button className="btn-primary" onClick={onGo}>Vai al Profilo</button>
    </div>
  )
}

/** I lavori dello studio: una scheda per azienda cliente, con a che punto è. */
export function ClientsPanel({ clients, clientId, onSelect, onChanged }) {
  const [name, setName] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [renaming, setRenaming] = useState(null)

  const create = async (e) => {
    e.preventDefault()
    setBusy(true); setError(null)
    try { const c = await api.createClient(name); setName(''); await onChanged(c.id) } catch (err) { setError(err.message) } finally { setBusy(false) }
  }
  const rename = async (c) => {
    const n = window.prompt('Nuovo nome del lavoro', c.name)
    if (n == null || !n.trim() || n.trim() === c.name) return
    try { await api.patchClient(c.id, { name: n.trim() }); await onChanged(clientId) } catch (err) { setError(err.message) }
  }
  const remove = async (c) => {
    const typed = window.prompt(`Eliminare «${c.name}» con profilo, bilanci, documenti e risultati salvati? I template di budget restano.\n\nPer confermare riscrivi il nome del lavoro:`)
    if (typed == null) return
    try { await api.deleteClient(c.id, typed); await onChanged(c.id === clientId ? null : clientId) } catch (err) { setError(err.message) }
  }

  return (
    <div className="space-y-4" id="lavori">
      <div className="flex flex-wrap items-end gap-3">
        <div className="min-w-0 flex-1"><h3 className="font-semibold text-base">I lavori dello studio</h3>
          <p className="text-xs text-ink-2 mt-0.5 max-w-2xl leading-relaxed">Ogni azienda con cui lavori su QUANTO è un lavoro: ha il suo profilo, i suoi bilanci, i suoi documenti e i risultati salvati. I crediti sono dello studio.</p></div>
        <form onSubmit={create} className="flex items-center gap-2">
          <input className="field !w-56" value={name} onChange={(e) => setName(e.target.value)} placeholder="Nome dell'azienda (nuovo lavoro)" aria-label="Nome del nuovo lavoro" />
          <button className="btn-primary" disabled={busy || name.trim().length < 2}>{busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}Apri lavoro</button>
        </form>
      </div>
      {error && <p className="text-xs text-red-700">{error}</p>}
      {clients && clients.length === 0 && <div className="p-4 rounded-2xl border border-dashed border-line-strong text-xs text-ink-2">Nessun lavoro ancora. Scrivi il nome della prima azienda e premi «Apri lavoro»: poi carichi visura e bilanci.</div>}
      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-3">
        {(clients || []).map((c) => {
          const on = c.id === clientId
          return (
            <div key={c.id} className={`rounded-2xl border p-4 space-y-2 ${on ? 'border-brand/60 bg-brand/5' : 'border-line bg-field'}`}>
              <div className="flex items-start gap-2">
                <div className="min-w-0 flex-1"><p className="text-sm font-semibold text-ink break-words">{c.name}</p>
                  <p className="text-[11px] text-mute">{[c.ateco_code && `ATECO ${c.ateco_code}`, c.region, c.size].filter(Boolean).join(' · ') || 'Profilo da completare'}</p></div>
                {on && <span className="px-2 py-0.5 text-[11px] font-medium rounded border border-brand/60 text-brand-ink">Attivo</span>}
              </div>
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-ink-2">
                <span>Profilo {fmtNum(c.completeness_pct, 0)}%</span>
                <span>{c.last_year ? `Ultimo bilancio ${c.last_year}` : 'Nessun bilancio'}</span>
                <span>{c.documents} {c.documents === 1 ? 'documento' : 'documenti'}</span>
                {c.saved.length > 0 && <span>Salvati: {c.saved.map((s) => ({ allocation: 'allocazione', budget: 'budget', confronto: 'confronto' }[s.key] || s.key)).join(', ')}</span>}
              </div>
              <div className="flex flex-wrap gap-2 pt-1">
                <button className="btn !py-1" onClick={() => onSelect(c.id)} disabled={on}>{on ? 'In uso' : 'Apri'}</button>
                <button className="btn !py-1" onClick={() => rename(c)} aria-label={`Rinomina ${c.name}`}><Pencil className="w-3 h-3" /></button>
                <button className="btn !py-1 ml-auto text-red-700" onClick={() => remove(c)} aria-label={`Elimina ${c.name}`}><Trash2 className="w-3 h-3" /></button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
