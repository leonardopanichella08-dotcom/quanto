import React from 'react'
import { AlertTriangle, CheckCircle2 } from 'lucide-react'
import { fmtBytes } from '../../lib/format'
import Activity from './Activity'
import Manual from './Manual'
import { Pills } from './charts'

/* Sistema: cosa è successo (attività), se tutto è a posto (salute) e come funziona (manuale). */
function Health({ data }) {
  const rows = [
    [data.registry.intact, 'Registro firmato', data.registry.intact ? `integro · ${data.registry.entries} registrazioni` : 'ALTERATO: una registrazione non torna'],
    [!data.registry.is_dev_key, 'Chiave di firma', data.registry.is_dev_key ? `di prova (${data.registry.key_id}): va sostituita in produzione` : data.registry.key_id],
    [data.auth.required, 'Accesso all’app', data.auth.required ? `protetto · ${data.auth.users} utenti` : 'NON protetto'],
    [!data.storage.volatile, 'Database', `${data.storage.engine} · ${fmtBytes(data.storage.size_bytes)}`],
  ]
  return (
    <ul className="card divide-y divide-line">
      {rows.map(([ok, label, text]) => (
        <li key={label} className="flex items-center gap-3 px-5 py-3.5 text-sm">
          {ok ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600" />}
          <span className="w-44 shrink-0 font-medium">{label}</span><span className={ok ? 'text-ink-2' : 'text-amber-800'}>{text}</span>
        </li>
      ))}
    </ul>
  )
}

export default function System({ view, setView, data, ops, opsById, onReplay }) {
  return (
    <div className="space-y-6">
      <Pills items={[['activity', 'Attività'], ['health', 'Salute'], ['manual', 'Manuale']]} value={view} onChange={setView} />
      {view === 'activity' && <Activity ops={ops} opsById={opsById} onReplay={onReplay} />}
      {view === 'health' && <Health data={data} />}
      {view === 'manual' && <Manual />}
    </div>
  )
}
