import React, { useEffect, useState } from 'react'
import { AlertOctagon, CheckCircle2, HelpCircle, ShieldCheck } from 'lucide-react'
import { api } from '../lib/api'

function Verdict({ r }) {
  if (!r.registration_found) {
    return (
      <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-center gap-3">
        <HelpCircle className="w-8 h-8 text-amber-400 shrink-0" />
        <div>
          <h4 className="font-bold text-amber-400 text-sm">Nessuna registrazione trovata per questo progetto</h4>
          <p className="text-xs text-amber-300/80">Il registro non contiene alcuna Merkle Root: l’integrità non può essere attestata.</p>
        </div>
      </div>
    )
  }
  const ok = r.is_valid_and_unaltered
  const Icon = ok ? CheckCircle2 : AlertOctagon
  const t = ok
    ? { box: 'bg-emerald-500/10 border-emerald-500/30', icon: 'text-emerald-400', title: 'text-emerald-400', text: 'text-emerald-300/80', pill: 'text-emerald-400 bg-emerald-500/20' }
    : { box: 'bg-red-500/10 border-red-500/30', icon: 'text-red-400', title: 'text-red-400', text: 'text-red-300/80', pill: 'text-red-400 bg-red-500/20' }
  let why = 'La Merkle Root ricalcolata coincide al 100% con quella registrata; firma e catena del registro sono integre.'
  if (!ok) {
    if (!r.chain_intact) why = 'La catena del registro NON è integra: il registro è stato alterato dopo la registrazione.'
    else if (!r.signature_valid) why = 'La firma della voce non è valida o proviene da una chiave non di fiducia.'
    else why = 'La Merkle Root presentata è diversa da quella registrata: il budget è stato modificato dopo la registrazione o è un altro documento.'
  }
  return (
    <div className={`p-4 border rounded-xl flex items-center justify-between gap-4 ${t.box}`}>
      <div className="flex items-center gap-3">
        <Icon className={`w-8 h-8 shrink-0 ${t.icon}`} />
        <div>
          <h4 className={`font-bold text-sm ${t.title}`}>{ok ? 'Budget asseverato e inalterato' : 'ATTENZIONE: verifica fallita'}</h4>
          <p className={`text-xs ${t.text}`}>{why}</p>
        </div>
      </div>
      <span className={`text-xs font-mono px-3 py-1 rounded-full whitespace-nowrap ${t.pill}`}>{r.verification_time_seconds}s</span>
    </div>
  )
}

function Chip({ ok, label }) {
  return (
    <span className={`px-2 py-1 rounded-lg text-[11px] font-semibold border ${ok ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' : 'bg-red-500/10 border-red-500/30 text-red-300'}`}>
      {ok ? '✓' : '✗'} {label}
    </span>
  )
}

export default function AuditorPortal({ request, defaultProject, defaultRoot }) {
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
    <div className="card p-6 space-y-5">
      <div className="pb-3 border-b border-neutral-800">
        <h3 className="font-bold text-lg flex items-center gap-2"><ShieldCheck className="w-5 h-5 text-emerald-400" />Auditor Portal — asseverazione crittografica</h3>
        <p className="text-xs text-neutral-400 mt-0.5">Confronto tra la Merkle Root presentata (o ricalcolata dai dati originali) e quella nel registro firmato; verifica di firma e integrità della catena.</p>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <label className="space-y-1"><span className="label">ID progetto</span>
          <input value={projectId} onChange={(e) => setProjectId(e.target.value)} className="w-full bg-neutral-950 border border-neutral-800 rounded-xl px-3 py-2 font-mono text-xs" /></label>
        <label className="space-y-1"><span className="label">Merkle Root presentata</span>
          <input value={root} onChange={(e) => setRoot(e.target.value)} placeholder="0x…" className="w-full bg-neutral-950 border border-neutral-800 rounded-xl px-3 py-2 font-mono text-xs" /></label>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button onClick={verifyRoot} disabled={loading || !projectId || !root} className="px-5 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-black font-bold text-xs rounded-xl transition disabled:opacity-50">Verifica radice</button>
        <button onClick={recompute} disabled={loading || !projectId} className="px-5 py-2.5 border border-emerald-500/50 text-emerald-300 hover:bg-emerald-500/10 font-bold text-xs rounded-xl transition disabled:opacity-50">Ricalcola dai dati originali</button>
        <label className="text-xs text-neutral-400 flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={tamper} onChange={(e) => setTamper(e.target.checked)} />
          Simula manomissione (+1 € sulla prima riga)
        </label>
      </div>

      {error && <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-xs">{error}</div>}

      {result ? (
        <div className="space-y-4">
          <Verdict r={result} />
          {result.registration_found && (
            <div className="flex flex-wrap gap-2">
              <Chip ok={result.registered_merkle_root === result.provided_merkle_root} label="Merkle Root coincidente" />
              <Chip ok={result.signature_valid} label="Firma Ed25519 valida" />
              <Chip ok={result.chain_intact} label={`Catena integra (${result.chain_entries} voci)`} />
            </div>
          )}
          <div className="grid md:grid-cols-2 gap-4 text-xs font-mono">
            <div className="p-4 bg-neutral-950 border border-neutral-800 rounded-xl space-y-1">
              <span className="text-neutral-500">{result.recomputed_from_data ? 'Radice ricalcolata dai dati' : 'Radice presentata'}</span>
              <p className="text-[#deffac] break-all p-2 bg-neutral-900 rounded">{result.provided_merkle_root}</p>
            </div>
            <div className="p-4 bg-neutral-950 border border-neutral-800 rounded-xl space-y-1">
              <span className="text-neutral-500">Radice registrata</span>
              <p className="text-emerald-400 break-all p-2 bg-neutral-900 rounded">{result.registered_merkle_root || '—'}</p>
            </div>
          </div>
          {result.registration_found && (
            <p className="text-[11px] text-neutral-500 font-mono break-all">Voce n. {result.seq} del {result.registered_at} · chiave {result.key_id} · hash {result.entry_hash}</p>
          )}
        </div>
      ) : (
        <div className="p-10 text-center text-neutral-500 text-sm italic bg-neutral-950 rounded-xl border border-neutral-800">
          Registra prima un budget dalla vista Budget Canvas, poi verificalo qui — anche con la manomissione simulata.
        </div>
      )}
    </div>
  )
}
