import React, { useEffect, useState } from 'react'
import { ArrowRight, CheckCircle2, Linkedin, Mail, PenLine, UserPlus } from 'lucide-react'
import { api } from '../../lib/api'
import Ask from './Ask'
import { Big, ChartTitle, LineChart } from './charts'

/* «Oggi»: la prima cosa che vede il titolare. Le cose da fare (solo quelle vere), quattro numeri, un grafico, e il chatbot per tutto il resto. */
export default function Today({ data, goto }) {
  const [mk, setMk] = useState(null)
  const [accounts, setAccounts] = useState([])
  useEffect(() => { api.mkOverview(30).then(setMk).catch(() => setMk(null)); api.mkAccounts().then(setAccounts).catch(() => setAccounts([])) }, [])
  const acc = data.access || {}
  const toApprove = mk?.posts?.DA_APPROVARE || 0
  const unlinked = accounts.filter((a) => a.status !== 'collegato').length
  const todo = [
    acc.PENDING > 0 && { icon: UserPlus, n: acc.PENDING, text: `richiest${acc.PENDING === 1 ? 'a' : 'e'} di accesso da decidere`, go: () => goto('access') },
    acc.mail_to_send > 0 && { icon: Mail, n: acc.mail_to_send, text: 'e-mail di conferma da inviare', go: () => goto('access') },
    toApprove > 0 && { icon: PenLine, n: toApprove, text: `post LinkedIn da approvare`, go: () => goto('marketing', 'posts') },
    unlinked > 0 && { icon: Linkedin, n: unlinked, text: `account LinkedIn da collegare`, go: () => goto('marketing', 'accounts') },
  ].filter(Boolean)
  const visits = mk?.visits_by_day || []
  const byDay = Object.fromEntries((data.events_by_day || []).map((d) => [d.day, d.n]))
  const days = [...new Set([...visits.map((v) => v.day), ...Object.keys(byDay)])].sort().slice(-30)
  const vmap = Object.fromEntries(visits.map((v) => [v.day, v.visitors]))

  return (
    <div className="space-y-8">
      <section>
        <ChartTitle>Da fare</ChartTitle>
        {todo.length === 0
          ? <p className="text-sm text-ink-2 flex items-center gap-2"><CheckCircle2 className="w-4 h-4" />Niente in sospeso. Le richieste nuove, i post da approvare e le e-mail da inviare compaiono qui.</p>
          : (
            <ul className="space-y-2">
              {todo.map((t) => (
                <li key={t.text}>
                  <button onClick={t.go} className="w-full text-left flex items-center gap-4 rounded-2xl px-4 py-3 hover:opacity-90 transition" style={{ background: '#F1E21B' }}>
                    <t.icon className="w-4 h-4 shrink-0" /><span className="text-xl font-semibold font-mono w-8">{t.n}</span><span className="flex-1 text-sm font-medium">{t.text}</span><ArrowRight className="w-4 h-4" />
                  </button>
                </li>
              ))}
            </ul>
          )}
      </section>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        <Big label="Visitatori del sito" value={mk ? mk.visitors : '—'} note="ultimi 30 giorni" onClick={() => goto('marketing')} />
        <Big label="Richieste di accesso" value={mk ? mk.signups : '—'} note={mk?.conversion_pct != null ? `${mk.conversion_pct}% dei visitatori` : 'ultimi 30 giorni'} onClick={() => goto('access')} />
        <Big label="Utenti attivi" value={data.auth.users} note={`${data.auth.managers} manager`} onClick={() => goto('access')} />
        <Big label="Budget controllati" value={data.validations} note="dagli studi, da sempre" onClick={() => goto('data')} />
      </div>

      <section className="card p-5">
        <ChartTitle right={<button onClick={() => goto('marketing')} className="text-xs text-ink-2 hover:text-ink">Marketing →</button>}>Visitatori del sito e operazioni nell’app</ChartTitle>
        <LineChart points={days.map((d) => ({ x: d, a: vmap[d] || 0, b: byDay[d] || 0 }))} labels={['visitatori', 'operazioni']} />
      </section>

      <Ask />
    </div>
  )
}
