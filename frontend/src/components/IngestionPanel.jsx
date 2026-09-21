import React, { useCallback, useEffect, useState } from 'react'
import { api } from '../lib/api'
import { SEED_BANDO_TEXT } from '../data/mockSeed'
import { Hint } from './Help'

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
    <div className="p-3 bg-field border border-line rounded-xl"><span className="label block">{label}</span><span className="font-mono text-sm">{String(value)}</span></div>
  )

  return (
    <div className="space-y-6">
      <div className="card p-6 space-y-4">
        <div className="pb-3 border-b border-line">
          <h3 className="font-semibold text-lg flex items-center gap-2">Caricamento bandi (uso interno) <Hint id="hq_caricamento" /></h3>
          <p className="text-xs text-ink-2 mt-0.5">Estrae le regole dal testo di un bando con un programma (Stadio 2) e confronta più letture indipendenti (Stadio 3): solo quando non concordano decide una persona.</p>
        </div>
        <div className="grid md:grid-cols-2 gap-3">
          <label className="space-y-1"><span className="label">Codice del bando</span>
            <input value={bandoId} onChange={(e) => setBandoId(e.target.value)} className="w-full field font-mono" /></label>
          <label className="space-y-1"><span className="label">Nome del bando</span>
            <input value={name} onChange={(e) => setName(e.target.value)} className="w-full bg-field border border-line rounded-xl px-3 py-2 text-xs" /></label>
        </div>
        <label className="space-y-1 block"><span className="label">Testo del bando</span>
          <textarea value={text} onChange={(e) => setText(e.target.value)} rows={7} className="w-full field font-mono" /></label>
        <div className="flex flex-wrap gap-3">
          <button onClick={runExtract} disabled={busy || !bandoId} className="btn-primary">Estrai le regole</button>
          <button onClick={runDisagreement} disabled={busy} className="px-4 py-2 border border-line-strong hover:border-line-strong text-ink font-bold text-xs rounded-xl transition disabled:opacity-50">Demo: due letture che non concordano</button>
        </div>
        {error && <div className="p-3 rounded-xl border border-red-500/30 bg-red-500/10 text-red-700 text-xs">{error}</div>}
        {last && (
          <div className="p-3 bg-field border border-line rounded-xl text-xs font-mono space-y-1">
            <div>già in memoria: {last.cache_hit ? 'sì' : 'no'} · controlli attivati: {last.coverage_activated ? 'sì' : 'no'}</div>
            <div className="text-emerald-700">pubblicate: {Object.entries(last.published).map(([k, v]) => `${k}=${v}`).join(', ') || '—'}</div>
            <div className="text-amber-700">da verificare a mano: {last.pending_human_review.join(', ') || '—'}</div>
          </div>
        )}
      </div>

      {status && (
        <div className="card p-6 space-y-3">
          <span className="label">Stato · {status.bando_id}</span>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {stat('Estrazione', status.extraction_status)}
            {stat('Già in memoria', status.cache_hit)}
            {stat('Regole trovate', status.rules_extracted_total)}
            {stat('Lette dal testo', status.rules_from_structured_parsing)}
            {stat('Letture concordi', status.rules_with_pass_agreement)}
            {stat('Da verificare', status.rules_pending_human_review)}
            {stat('Verificate da una persona', status.rules_human_reviewed)}
            {stat('Richieste ricevute', status.requested_by_clients_count)}
          </div>
        </div>
      )}

      <div className="card p-6 space-y-3">
        <span className="label">Da verificare a mano ({queue.length})</span>
        {queue.length === 0 && <p className="text-xs text-mute">Niente da verificare: le letture concordano.</p>}
        {queue.map((item) => {
          const key = `${item.bando_id}/${item.rule_key}`
          return (
            <div key={key} className="p-4 bg-field border border-line rounded-xl text-xs space-y-2">
              <div className="font-mono">{item.bando_id} · <span className="text-amber-700">{item.rule_key}</span></div>
              <div className="font-mono text-ink-2">letture: {item.passes.map((p) => p ?? 'n/d').join(' ≠ ')}</div>
              <div className="flex gap-2">
                <input placeholder="valore corretto" value={decisions[key] ?? ''} onChange={(e) => setDecisions({ ...decisions, [key]: e.target.value })}
                  className="bg-tint border border-line-strong rounded-lg px-2 py-1 font-mono text-xs" />
                <button onClick={() => resolve(item)} disabled={busy || !decisions[key]} className="btn-primary">Pubblica</button>
              </div>
            </div>
          )
        })}
      </div>

      {rules && (
        <div className="card p-6 space-y-2">
          <span className="label">Regole pubblicate (l’insieme che usa il motore)</span>
          <p className="text-xs text-mute font-mono">versione delle regole: {rules.rule_version_hash} (cambia se cambia una regola)</p>
          <pre className="text-xs font-mono bg-field border border-line rounded-xl p-3 overflow-x-auto">{JSON.stringify(Object.fromEntries(Object.entries(rules).filter(([, v]) => v !== null && (!Array.isArray(v) || v.length))), null, 2)}</pre>
        </div>
      )}
    </div>
  )
}
