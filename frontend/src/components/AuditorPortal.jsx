import React, { useEffect, useState } from 'react'
import { AlertOctagon, CheckCircle2, HelpCircle } from 'lucide-react'
import { api } from '../lib/api'
import { useNav } from '../lib/nav'
import Guide from './Guide'
import { Hint } from './Help'

function Verdict({ r }) {
  if (!r.registration_found) {
    return (
      <div className="p-4 border border-amber-500/30 rounded-xl flex items-center gap-3">
        <HelpCircle className="w-7 h-7 text-amber-400 shrink-0" />
        <div>
          <h4 className="font-semibold text-amber-300 text-sm">Nessuna registrazione trovata per questo progetto</h4>
          <p className="text-xs text-amber-200/80">Nel registro non c’è nessuna impronta per questo progetto: non posso confermare che il budget sia integro.</p>
        </div>
      </div>
    )
  }
  const ok = r.is_valid_and_unaltered
  const Icon = ok ? CheckCircle2 : AlertOctagon
  const t = ok
    ? { box: 'border-emerald-500/30', icon: 'text-emerald-400', title: 'text-emerald-300', text: 'text-emerald-200/80', pill: 'text-emerald-300 border-emerald-500/30' }
    : { box: 'border-red-500/30', icon: 'text-red-400', title: 'text-red-300', text: 'text-red-200/80', pill: 'text-red-300 border-red-500/30' }
  let why = 'L’impronta ricalcolata coincide con quella registrata; la firma e la catena del registro sono integre.'
  if (!ok) {
    if (!r.chain_intact) why = 'Il registro è stato alterato dopo la registrazione.'
    else if (!r.signature_valid) why = 'La firma non è valida oppure è di una chiave di cui non ci si fida.'
    else why = 'L’impronta è diversa da quella registrata: il budget è stato modificato dopo la registrazione, oppure è un altro budget.'
  }
  return (
    <div className={`p-4 border rounded-xl flex flex-wrap items-center justify-between gap-4 ${t.box}`}>
      <div className="flex items-center gap-3 min-w-0">
        <Icon className={`w-7 h-7 shrink-0 ${t.icon}`} />
        <div className="min-w-0">
          <h4 className={`font-semibold text-sm ${t.title}`}>{ok ? 'Budget certificato e non modificato' : 'ATTENZIONE: verifica non superata'}</h4>
          <p className={`text-xs ${t.text}`}>{why}</p>
        </div>
      </div>
      <span className={`text-xs font-mono px-3 py-1 rounded-full whitespace-nowrap border ${t.pill}`}>{r.verification_time_seconds}s</span>
    </div>
  )
}

function Chip({ ok, label }) {
  return (
    <span className={`px-2 py-1 rounded-lg text-xs font-medium border ${ok ? 'border-emerald-500/30 text-emerald-300' : 'border-red-500/30 text-red-300'}`}>
      {ok ? '✓' : '✗'} {label}
    </span>
  )
}

export default function AuditorPortal({ request, defaultProject, defaultRoot }) {
  const nav = useNav()
  const [projectId, setProjectId] = useState(defaultProject || '')
  const [root, setRoot] = useState(defaultRoot || '')
  const [tamper, setTamper] = useState(false)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => { if (defaultProject) setProjectId(defaultProject) }, [defaultProject])
  useEffect(() => { if (defaultRoot) setRoot(defaultRoot) }, [defaultRoot])

  const run = async (fn) => {
    setLoading(true); setError(null)
    try { setResult(await fn()) } catch (e) { setError(e.message); setResult(null) } finally { setLoading(false) }
  }

  const verifyRoot = () => run(() => api.verifyRoot(projectId, root))
  const recompute = () => run(() => {
    const items = request.cost_items.map((i) => ({ ...i }))
    if (tamper) {
      const first = items.find((i) => i.ral_eur != null) ?? items[0]
      if (first.ral_eur != null) first.ral_eur += 1
      else first.amount_eur += 1
    }
    return api.verifyRecompute({ project_id: projectId, grant_rules: request.grant_rules, cost_items: items })
  })

  return (
    <div className="space-y-6">
      <Guide page="auditor" />
      <div className="card p-6 space-y-5">
        <div className="pb-3 border-b border-neutral-800">
          <h3 className="font-semibold text-lg">Il budget è stato cambiato dopo la certificazione?</h3>
          <p className="text-xs text-neutral-400 mt-0.5 leading-relaxed">Confronta l’impronta che hai in mano (o quella ricalcolata dai dati originali) con quella scritta nel registro, e controlla la firma e l’integrità del registro.</p>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <label className="space-y-1"><span className="label">Progetto</span>
            <input value={projectId} onChange={(e) => setProjectId(e.target.value)} className="field font-mono" /></label>
          <label className="space-y-1"><span className="label">Impronta presentata (Merkle Root)</span>
            <input value={root} onChange={(e) => setRoot(e.target.value)} placeholder="0x…" className="field font-mono" /></label>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button onClick={verifyRoot} disabled={loading || !projectId || !root} className="btn-primary">Verifica impronta</button>
          <Hint id="auditor_verifica" />
          <button onClick={recompute} disabled={loading || !projectId || !request.grant_rules || !request.cost_items.length} className="btn !border-[#deffac]/40 !text-[#deffac]">Ricalcola dai dati originali</button>
          <Hint id="auditor_ricalcola" />
          <label className="text-xs text-neutral-400 flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={tamper} onChange={(e) => setTamper(e.target.checked)} />
            Simula una manomissione (+1 € sulla prima riga)
            <Hint id="auditor_manomissione" />
          </label>
        </div>

        {error && <div className="p-3 rounded-xl border border-red-500/30 text-red-300 text-xs">{error}</div>}

        {result ? (
          <div className="space-y-4">
            <Verdict r={result} />
            {result.registration_found && (
              <div className="flex flex-wrap gap-2">
                <Chip ok={result.registered_merkle_root === result.provided_merkle_root} label="Impronta coincidente" />
                <Chip ok={result.signature_valid} label="Firma digitale valida" />
                <Chip ok={result.chain_intact} label={`Registro integro (${result.chain_entries} registrazioni)`} />
              </div>
            )}
            <div className="grid md:grid-cols-2 gap-4 text-xs font-mono">
              <div className="p-4 bg-neutral-950 border border-neutral-800 rounded-xl space-y-1 min-w-0">
                <span className="text-neutral-500 font-sans">{result.recomputed_from_data ? 'Impronta ricalcolata dai dati' : 'Impronta presentata'}</span>
                <p className="text-[#deffac] break-all p-2 bg-neutral-900 rounded">{result.provided_merkle_root}</p>
              </div>
              <div className="p-4 bg-neutral-950 border border-neutral-800 rounded-xl space-y-1 min-w-0">
                <span className="text-neutral-500 font-sans">Impronta registrata</span>
                <p className="text-emerald-400 break-all p-2 bg-neutral-900 rounded">{result.registered_merkle_root || '—'}</p>
              </div>
            </div>
            {result.registration_found && (
              <p className="text-[11px] text-neutral-500 font-mono break-all">Registrazione n. {result.seq} del {result.registered_at} · chiave {result.key_id} · impronta della registrazione {result.entry_hash}</p>
            )}
          </div>
        ) : (
          <div className="p-10 text-center text-neutral-500 text-sm bg-neutral-950 rounded-xl border border-neutral-800">
            Registra prima un budget dalla pagina Budget, poi verificalo qui — anche simulando una manomissione.
          </div>
        )}

        <button type="button" onClick={() => nav.go('guida', 'merkle')} className="text-xs text-[#deffac] hover:underline">Come si costruisce l’impronta? Guarda la spiegazione passo passo →</button>
      </div>
    </div>
  )
}
