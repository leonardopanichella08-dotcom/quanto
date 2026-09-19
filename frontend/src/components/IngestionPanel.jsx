import React, { useCallback, useEffect, useState } from 'react'
import { Database } from 'lucide-react'
import { api } from '../lib/api'
import { SEED_BANDO_TEXT } from '../data/mockSeed'

export default function IngestionPanel() {
  const [bandoId, setBandoId] = useState('TRANSIZIONE-5.0-2026')
  const [name, setName] = useState('Piano Transizione 5.0')
  const [text, setText] = useState(SEED_BANDO_TEXT)
  const [status, setStatus] = useState(null)
  const [queue, setQueue] = useState([])
  const [rules, setRules] = useState(null)
  const [last, setLast] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [decisions, setDecisions] = useState({})

  const refresh = useCallback(async () => {
    try {
      setQueue(await api.ingestionQueue())
      try { setStatus(await api.ingestionStatus(bandoId)) } catch { setStatus(null) }
      try { setRules(await api.ingestionRules(bandoId)) } catch { setRules(null) }
    } catch (e) { setError(e.message) }
  }, [bandoId])

  useEffect(() => { refresh() }, [refresh])

  const act = async (fn) => {
    setBusy(true); setError(null)
    try { await fn(); await refresh() } catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  const runExtract = () => act(async () => {
    await api.ingestionAddBando({ bando_id: bandoId, name })
    await api.ingestionConfirm(bandoId)
    setLast(await api.ingestionExtract({ bando_id: bandoId, source_text: text }))
  })

  // dimostra lo Stadio 3: due passaggi indipendenti che DISACCORDANO sulla quota consulenze
  const runDisagreement = () => act(async () => {
    const id = `${bandoId}-DEMO-PASSI`
    await api.ingestionAddBando({ bando_id: id, name: `${name} (demo passaggi multipli)` })
    setLast(await api.ingestionExtract({ bando_id: id, ai_passes: [
      { max_hourly_rate_personnel: '35', max_consulting_percentage: '20%', max_overhead_percentage: 0.07 },
      { max_hourly_rate_personnel: 35, max_consulting_percentage: 0.25, max_overhead_percentage: '0,07' },
    ] }))
  })

  const resolve = (item) => act(async () => {
    await api.ingestionReview({ bando_id: item.bando_id, rule_key: item.rule_key, value: decisions[`${item.bando_id}/${item.rule_key}`] })
  })

  const stat = (label, value) => (
    <div className="p-3 bg-neutral-950 border border-neutral-800 rounded-xl"><span className="label block">{label}</span><span className="font-mono text-sm">{String(value)}</span></div>
  )

  return (
    <div className="space-y-6">
      <div className="card p-6 space-y-4">
        <div className="pb-3 border-b border-neutral-800">
          <h3 className="font-bold text-lg flex items-center gap-2"><Database className="w-5 h-5 text-[#deffac]" />Pannello di Ingestion — Fonte A (uso interno)</h3>
          <p className="text-xs text-neutral-400 mt-0.5">Stadio 2: estrazione deterministica dal testo del bando. Stadio 3: confronto dei passaggi indipendenti fatto dal codice; solo i disaccordi vanno a verifica umana.</p>
        </div>
        <div className="grid md:grid-cols-2 gap-3">
          <label className="space-y-1"><span className="label">ID bando</span>
            <input value={bandoId} onChange={(e) => setBandoId(e.target.value)} className="w-full bg-neutral-950 border border-neutral-800 rounded-xl px-3 py-2 font-mono text-xs" /></label>
          <label className="space-y-1"><span className="label">Denominazione</span>
            <input value={name} onChange={(e) => setName(e.target.value)} className="w-full bg-neutral-950 border border-neutral-800 rounded-xl px-3 py-2 text-xs" /></label>
        </div>
        <label className="space-y-1 block"><span className="label">Testo del bando</span>
          <textarea value={text} onChange={(e) => setText(e.target.value)} rows={7} className="w-full bg-neutral-950 border border-neutral-800 rounded-xl px-3 py-2 font-mono text-xs" /></label>
        <div className="flex flex-wrap gap-3">
          <button onClick={runExtract} disabled={busy || !bandoId} className="btn-primary">Conferma bando ed estrai regole</button>
          <button onClick={runDisagreement} disabled={busy} className="px-4 py-2 border border-neutral-700 hover:border-neutral-500 text-neutral-200 font-bold text-xs rounded-xl transition disabled:opacity-50">Demo: due passaggi in disaccordo</button>
        </div>
        {error && <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-xs">{error}</div>}
        {last && (
          <div className="p-3 bg-neutral-950 border border-neutral-800 rounded-xl text-xs font-mono space-y-1">
            <div>cache_hit: {String(last.cache_hit)} · copertura attivata: {String(last.coverage_activated)}</div>
            <div className="text-emerald-300">pubblicate: {Object.entries(last.published).map(([k, v]) => `${k}=${v}`).join(', ') || '—'}</div>
            <div className="text-amber-300">in verifica umana: {last.pending_human_review.join(', ') || '—'}</div>
          </div>
        )}
      </div>

      {status && (
        <div className="card p-6 space-y-3">
          <span className="label">Stato pipeline · {status.bando_id}</span>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {stat('Estrazione', status.extraction_status)}
            {stat('Cache hit', status.cache_hit)}
            {stat('Regole totali', status.rules_extracted_total)}
            {stat('Parsing deterministico', status.rules_from_structured_parsing)}
            {stat('Concordanza passaggi', status.rules_with_pass_agreement)}
            {stat('In verifica umana', status.rules_pending_human_review)}
            {stat('Riviste da umano', status.rules_human_reviewed)}
            {stat('Richieste clienti', status.requested_by_clients_count)}
          </div>
        </div>
      )}

      <div className="card p-6 space-y-3">
        <span className="label">Coda di verifica umana ({queue.length})</span>
        {queue.length === 0 && <p className="text-xs text-neutral-500 italic">Nessun disaccordo da risolvere.</p>}
        {queue.map((item) => {
          const key = `${item.bando_id}/${item.rule_key}`
          return (
            <div key={key} className="p-4 bg-neutral-950 border border-neutral-800 rounded-xl text-xs space-y-2">
              <div className="font-mono">{item.bando_id} · <span className="text-amber-300">{item.rule_key}</span></div>
              <div className="font-mono text-neutral-400">passaggi: {item.passes.map((p) => p ?? 'n/d').join(' ≠ ')}</div>
              <div className="flex gap-2">
                <input placeholder="valore corretto" value={decisions[key] ?? ''} onChange={(e) => setDecisions({ ...decisions, [key]: e.target.value })}
                  className="bg-neutral-900 border border-neutral-700 rounded-lg px-2 py-1 font-mono text-xs" />
                <button onClick={() => resolve(item)} disabled={busy || !decisions[key]} className="btn-primary">Pubblica</button>
              </div>
            </div>
          )
        })}
      </div>

      {rules && (
        <div className="card p-6 space-y-2">
          <span className="label">GrantRuleSet composto dalle regole pubblicate</span>
          <p className="text-[11px] text-neutral-500 font-mono">rule_version_hash: {rules.rule_version_hash} (cambia se cambia una regola)</p>
          <pre className="text-[11px] font-mono bg-neutral-950 border border-neutral-800 rounded-xl p-3 overflow-x-auto">{JSON.stringify(Object.fromEntries(Object.entries(rules).filter(([, v]) => v !== null && (!Array.isArray(v) || v.length))), null, 2)}</pre>
        </div>
      )}
    </div>
  )
}
