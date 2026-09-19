import React, { useMemo, useState } from 'react'
import { ChevronDown, ChevronRight, Copy, Trash2 } from 'lucide-react'
import { CATEGORY_LABEL } from '../lib/format'

const REQUIRED = new Set(['item_id', 'description', 'category', 'source_c_ref'])
const inputCls = 'field !px-2 !py-1.5 font-mono'

// Nomi leggibili per i valori tecnici dei menu (il valore inviato al server resta quello originale).
const OPTION_LABEL = {
  PERSONNEL: 'Personale', CAPITAL_ASSETS: 'Beni strumentali', CONSULTING: 'Consulenze', OVERHEAD: 'Spese generali', TRAINING: 'Formazione',
  TERZO_SETTORE: 'Terzo settore', METALMECCANICA: 'Metalmeccanica', COMMERCIO: 'Commercio', CREDITO: 'Credito',
  PERMANENT: 'Tempo indeterminato', FIXED_TERM: 'Tempo determinato', OCCASIONAL: 'Occasionale',
  PROJECT: 'Progetto', B2B: 'Verso altre imprese (B2B)', B2G: 'Verso la pubblica amministrazione (B2G)',
  HARDWARE: 'Hardware', SOFTWARE: 'Software', SERVICE: 'Servizio', IMMATERIAL: 'Bene immateriale', REAL_ESTATE: 'Immobile',
  COMMUNICATION: 'Comunicazione', GUARANTEE: 'Fideiussione/assicurazione', AUDIT: 'Revisione contabile', PENALTY: 'Sanzioni/penali', LEGAL_DISPUTE: 'Contenzioso legale',
  REPRESENTATION: 'Rappresentanza', RENT: 'Affitto', UTILITIES: 'Utenze', MAINTENANCE_ORDINARY: 'Manutenzione ordinaria', MAINTENANCE_EXTRAORDINARY: 'Manutenzione straordinaria',
  FINANCIAL_CHARGES: 'Oneri finanziari', BANK_TRANSFER: 'Bonifico', CARD: 'Carta', CASH: 'Contanti', CHECK: 'Assegno',
}

function Field({ field, value, onChange }) {
  const set = (v) => onChange(field.name, v)
  const label = (
    <span className="flex items-center gap-1.5 text-xs text-neutral-400 mb-1">
      {field.label}
      {field.criteria.map((c) => <span key={c} className="font-mono text-[10px] text-[#deffac]/80">#{c}</span>)}
    </span>
  )
  let control
  if (field.type === 'bool') {
    control = (
      <select value={value === undefined ? '' : String(value)} onChange={(e) => set(e.target.value === '' ? undefined : e.target.value === 'true')} className={inputCls}>
        <option value="">— non indicato</option><option value="true">Sì</option><option value="false">No</option>
      </select>
    )
  } else if (field.type === 'select') {
    control = (
      <select value={value ?? ''} onChange={(e) => set(e.target.value === '' ? undefined : e.target.value)} className={inputCls}>
        {!REQUIRED.has(field.name) && <option value="">— non indicato</option>}
        {field.options.map((o) => <option key={o} value={o}>{OPTION_LABEL[o] || o}</option>)}
      </select>
    )
  } else if (field.type === 'number') {
    control = <input type="number" step={field.step || 'any'} value={value ?? ''} onChange={(e) => set(e.target.value === '' ? undefined : Number(e.target.value))} className={inputCls} />
  } else if (field.type === 'date') {
    control = <input type="date" value={value ?? ''} onChange={(e) => set(e.target.value || undefined)} className={inputCls} />
  } else if (field.type === 'list') {
    control = (
      <input type="text" placeholder="nessuno" value={Array.isArray(value) ? value.join(', ') : ''}
        onChange={(e) => { const t = e.target.value; set(t.trim() === '' ? undefined : ['nessuno', '-'].includes(t.trim().toLowerCase()) ? [] : t.split(',').map((x) => x.trim()).filter(Boolean)) }}
        className={inputCls} />
    )
  } else {
    control = <input type="text" value={value ?? ''} onChange={(e) => set(REQUIRED.has(field.name) ? e.target.value : e.target.value === '' ? undefined : e.target.value)} className={inputCls} />
  }
  return <label className="block" title={field.help}>{label}{control}{field.help && <span className="block text-[11px] text-neutral-500 mt-0.5">{field.help}</span>}</label>
}

export default function LineEditor({ item, fields, onChange, onDelete, onDuplicate }) {
  const [open, setOpen] = useState({ Identificazione: true })
  const groups = useMemo(() => {
    const applicable = fields.filter((f) => f.categories === null || f.categories.includes(item.category))
    const by = {}
    applicable.forEach((f) => { (by[f.group] ||= []).push(f) })
    return Object.entries(by)
  }, [fields, item.category])

  const update = (name, value) => {
    const next = { ...item }
    if (value === undefined) delete next[name]
    else next[name] = value
    onChange(next)
  }
  const filled = (fs) => fs.filter((f) => item[f.name] !== undefined && item[f.name] !== '').length

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-neutral-400"><span className="font-mono text-neutral-200">{item.item_id}</span> · {CATEGORY_LABEL[item.category]}</p>
        <div className="flex gap-1.5">
          <button onClick={onDuplicate} title="Duplica" className="p-1.5 rounded-lg border border-neutral-700 text-neutral-300 hover:border-neutral-500"><Copy className="w-3.5 h-3.5" /></button>
          <button onClick={onDelete} title="Elimina" className="p-1.5 rounded-lg border border-red-500/40 text-red-300 hover:bg-red-500/10"><Trash2 className="w-3.5 h-3.5" /></button>
        </div>
      </div>
      <p className="text-[11px] text-neutral-500">I numeri #N sono i controlli che quel campo attiva. Un campo vuoto non viene valutato: non conta come superato.</p>
      {groups.map(([group, fs]) => (
        <div key={group} className="border border-neutral-800 rounded-xl overflow-hidden">
          <button onClick={() => setOpen({ ...open, [group]: !open[group] })} className="w-full flex items-center justify-between px-3 py-2 bg-neutral-950 text-xs font-bold text-neutral-200">
            <span className="flex items-center gap-1.5">{open[group] ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}{group}</span>
            <span className="font-mono text-[11px] text-neutral-500">{filled(fs)}/{fs.length}</span>
          </button>
          {open[group] && (
            <div className="p-3 grid grid-cols-1 sm:grid-cols-2 gap-3 bg-neutral-900/50">
              {fs.map((f) => <Field key={f.name} field={f} value={item[f.name]} onChange={update} />)}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
