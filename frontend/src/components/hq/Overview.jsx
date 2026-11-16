import React, { useMemo } from 'react'
import { AlertTriangle, ArrowRight, CheckCircle2 } from 'lucide-react'
import { fmtBytes, fmtTs } from '../../lib/format'
import { BarList, Big, ChartTitle, DayBars } from './charts'

/* Panoramica: poche cifre, tre grafici e una riga di stato. Le cose da fare compaiono in cima solo quando ci sono. */
export default function Overview({ data, ops, opsById, goto }) {
  const c = data.counts
  const acc = data.access || { PENDING: 0, mail_to_send: 0 }
  const docsTotal = Object.values(data.documents_by_kind).reduce((a, b) => a + b, 0)
  const alerts = [
    !data.registry.intact && 'Il registro firmato risulta alterato.',
    !data.auth.required && 'L’accesso non è protetto: chiunque può entrare.',
    data.registry.is_dev_key && 'La firma del registro usa una chiave di prova.',
    data.storage.volatile && data.storage.note,
  ].filter(Boolean)
  const byArea = useMemo(() => {
    const m = {}
    ops.forEach((o) => { m[o.area] = (m[o.area] || 0) + o.stats.count })
    return Object.entries(m).filter(([, n]) => n > 0).sort((a, b) => b[1] - a[1]).slice(0, 6).map(([area, n]) => ({ label: area, value: n }))
  }, [ops])
  const store = [
    { id: 'bandi', label: 'Bandi', value: c.bandi }, { id: 'rules', label: 'Regole', value: c.rules }, { id: 'requirements', label: 'Requisiti', value: c.requirements },
    { id: 'documents', label: 'Documenti lavorati', value: docsTotal }, { id: 'runs', label: 'Esecuzioni salvate', value: c.runs },
  ]
  const todo = acc.PENDING > 0 || acc.mail_to_send > 0

  return (
    <div className="space-y-8">
      {todo && (
        <button onClick={() => goto('access')} className="w-full text-left rounded-2xl p-5 flex flex-wrap items-center gap-x-8 gap-y-2 hover:opacity-90 transition" style={{ background: '#F1E21B' }}>
          <span className="text-[34px] leading-none font-semibold font-mono text-ink">{acc.PENDING + acc.mail_to_send}</span>
          <span className="flex-1 min-w-[14rem]">
            <span className="block font-semibold text-sm text-ink">Da fare negli accessi</span>
            <span className="block text-xs text-ink/70">{[acc.PENDING > 0 && `${acc.PENDING} richiest${acc.PENDING === 1 ? 'a' : 'e'} da decidere`, acc.mail_to_send > 0 && `${acc.mail_to_send} e-mail da inviare`].filter(Boolean).join(' · ')}</span>
          </span>
          <span className="text-sm font-medium text-ink inline-flex items-center gap-1.5">Apri<ArrowRight className="w-4 h-4" /></span>
        </button>
      )}

      {alerts.length > 0 && (
        <div className="rounded-2xl border border-amber-500/40 bg-amber-500/10 p-4 space-y-1">
          {alerts.map((a) => <p key={a} className="text-xs text-amber-800 flex items-center gap-2"><AlertTriangle className="w-3.5 h-3.5 shrink-0" />{a}</p>)}
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        <Big label="Budget controllati" value={data.validations} note={data.last_validation_ts ? `ultimo ${fmtTs(data.last_validation_ts)}` : 'nessuno ancora'} onClick={() => goto('activity')} />
        <Big label="Progetti" value={data.projects} note="con almeno un’operazione" onClick={() => goto('activity')} />
        <Big label="Bandi in memoria" value={c.bandi} note={`${c.rules} regole · ${c.requirements} requisiti`} onClick={() => goto('data', 'bandi')} />
        <Big label="Utenti" value={data.auth.users} note={`${data.auth.managers} manager`} onClick={() => goto('access')} />
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        <div className="card p-5"><ChartTitle right={<span className="text-xs text-mute">{c.events} eventi in tutto</span>}>Attività, ultimi giorni</ChartTitle><DayBars days={data.events_by_day} /></div>
        <div className="card p-5"><ChartTitle>Dove si lavora</ChartTitle><BarList rows={byArea} empty="Ancora nessuna operazione." /></div>
        <div className="card p-5"><ChartTitle right={<button onClick={() => goto('data', 'database')} className="text-xs text-ink-2 hover:text-ink">Database →</button>}>Cosa c’è in memoria</ChartTitle><BarList rows={store} /></div>
      </div>

      <div className="card p-5">
        <ChartTitle right={<button onClick={() => goto('activity')} className="text-xs text-ink-2 hover:text-ink">Tutta l’attività →</button>}>Ultimi eventi</ChartTitle>
        {data.recent_events.slice(0, 6).map((e) => (
          <div key={e.id} className="flex flex-wrap items-center gap-x-3 text-xs border-b border-line py-1.5 last:border-0">
            <span className="font-mono text-[11px] text-mute w-32 shrink-0">{fmtTs(e.ts)}</span>
            <span className="font-semibold shrink-0">{opsById[e.op]?.title || e.op}</span>
            <span className="text-ink-2 truncate">{e.summary}</span>
          </div>
        ))}
        {data.recent_events.length === 0 && <p className="text-xs text-mute">Ancora nessuna operazione registrata.</p>}
      </div>

      <p className="text-xs text-mute flex flex-wrap items-center gap-x-5 gap-y-1">
        <span className="inline-flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5" />{data.storage.engine} · {fmtBytes(data.storage.size_bytes)}</span>
        <span>Registro firmato: {data.registry.entries} registrazioni, {data.registry.intact ? 'integro' : 'ALTERATO'} (chiave {data.registry.key_id})</span>
        <span>Accesso {data.auth.required ? 'protetto' : 'NON protetto'}</span>
      </p>
    </div>
  )
}
