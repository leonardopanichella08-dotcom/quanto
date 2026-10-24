import React, { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, CheckCircle2, ChevronDown, Loader2, Search } from 'lucide-react'
import { api } from '../lib/api'
import { Info } from './ui'
import Guide from './Guide'
import { allocationGo, profileGo, useNav } from '../lib/nav'

const STATUS = {
  APPLICABILE: ['Per te sì', 'bg-emerald-500/15 text-emerald-700'],
  DA_VERIFICARE: ['Da verificare', 'bg-amber-500/15 text-amber-700'],
  NON_APPLICABILE: ['Non per te', 'bg-red-500/10 text-red-700'],
  SCADUTA: ['Scaduta', 'bg-ink/10 text-ink-2'],
  DOPO_LA_COSTITUZIONE: ['Dopo la costituzione', 'bg-sky-500/15 text-sky-700'],
}
const VERIFIED = { SECONDARIA: 'letta su fonti secondarie: conferma sul sito INPS', DA_VERIFICARE: 'parametri da leggere nel bando o nella circolare' }

/** Cerca nel catalogo nazionale le misure di una famiglia regionale nella Regione dell'impresa; ogni bando trovato porta dritto agli altri strumenti: budget e allocazione. */
function CatalogSearch({ item, region, onBudgetFrom }) {
  const nav = useNav()
  const [res, setRes] = useState(null)
  const [busy, setBusy] = useState(false)
  const [working, setWorking] = useState(null)        // bando in lavorazione: {id, what}
  const [studied, setStudied] = useState({})
  const [error, setError] = useState(null)
  const run = async () => {
    setBusy(true)
    try {
      const all = await Promise.all(item.search.slice(0, 3).map((t) => api.bandiSearch(`${t}${region ? ` ${region}` : ''}`).then((r) => r.matches || []).catch(() => [])))
      const seen = new Set()
      setRes(all.flat().filter((m) => (seen.has(m.bando_id) ? false : seen.add(m.bando_id))).slice(0, 6))
    } finally { setBusy(false) }
  }
  const isStudied = (m) => m.rules > 0 || studied[m.bando_id]
  // un bando letto in breve si studia a fondo prima di tutto il resto: senza regole non c'è né budget né importo
  const ensure = async (m) => { if (!isStudied(m)) { await api.researchRun({ bando_id: m.bando_id }); setStudied((x) => ({ ...x, [m.bando_id]: true })) } }
  const go = async (m, what) => {
    setWorking({ id: m.bando_id, what }); setError(null)
    try {
      await ensure(m)
      if (what === 'budget') await onBudgetFrom?.(m.bando_id)
      else { allocationGo('bandi'); nav.go('allocation') }
    } catch (e) { setError(e.message) } finally { setWorking(null) }
  }
  return (
    <div className="space-y-2">
      <button className="btn" disabled={busy} onClick={run}>{busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}Cerca nel catalogo{region ? ` · ${region}` : ''}</button>
      {res && res.length === 0 && <p className="text-xs text-mute">Nessun bando con questi nomi nel catalogo: prova dalla pagina Bandi.</p>}
      {error && <p className="text-xs text-red-700">{error}</p>}
      {res && res.length > 0 && (
        <ul className="space-y-2">
          {res.map((m) => {
            const busyHere = working?.id === m.bando_id
            return (
              <li key={m.bando_id} className="rounded-xl bg-white p-3 space-y-2">
                <div className="flex flex-wrap items-start gap-2"><p className="text-sm font-medium text-ink flex-1 min-w-0 break-words">{m.name}</p>
                  <span className={`px-2 py-0.5 rounded-full text-[11px] font-medium ${isStudied(m) ? 'bg-emerald-500/15 text-emerald-700' : 'bg-tint text-ink-2'}`}>{isStudied(m) ? 'Studiato a fondo' : 'Letto in breve'}</span></div>
                <p className="text-[11px] text-mute">{m.issuer || 'Ente non indicato'}{m.deadline && m.deadline !== 'non indicata' ? ` · scade il ${m.deadline.split('-').reverse().join('/')}` : ''}</p>
                {m.summary && <p className="text-xs text-ink-2 leading-relaxed line-clamp-3">{m.summary}</p>}
                <div className="flex flex-wrap items-center gap-2">
                  <button className="btn-primary !py-1" disabled={!!working} onClick={() => go(m, 'budget')}>{busyHere && working.what === 'budget' ? <Loader2 className="w-3 h-3 animate-spin" /> : null}{isStudied(m) ? 'Fai il budget per questo bando' : 'Studia e fai il budget'}</button>
                  <button className="btn !py-1" disabled={!!working} onClick={() => go(m, 'allocazione')}>{busyHere && working.what === 'allocazione' ? <Loader2 className="w-3 h-3 animate-spin" /> : null}{isStudied(m) ? 'Vedi nell’allocazione' : 'Studia e vedi nell’allocazione'}</button>
                  {busyHere && <span className="text-[11px] text-mute">Cerco e leggo le fonti ufficiali: può richiedere fino a un minuto.</span>}
                </div>
              </li>
            )
          })}
        </ul>
      )}
      {res && res.length > 0 && <Info label="Cosa fanno questi tasti">«Fai il budget» apre la pagina Budget con le regole di quel bando e una bozza dalle spese dell’impresa. «Vedi nell’allocazione» lo porta nel piano che decide quale bando paga cosa. Un bando letto solo in breve si studia a fondo prima: senza regole non ci sono importi né controlli.</Info>}
    </div>
  )
}

function Item({ it, region, onAnswer, onBudgetFrom }) {
  const nav = useNav()
  const [open, setOpen] = useState(false)
  const [label, tone] = STATUS[it.status] || STATUS.DA_VERIFICARE
  return (
    <li className="rounded-2xl bg-tint">
      <button type="button" onClick={() => setOpen(!open)} aria-expanded={open} className="w-full text-left px-4 py-3 flex items-start gap-3">
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-2"><span className="text-sm font-semibold text-ink">{it.name}</span><span className={`px-2 py-0.5 rounded-full text-[11px] font-medium ${tone}`}>{label}</span></span>
          <span className="block text-xs text-ink-2 mt-1 leading-snug">{it.tagline}</span>
          {it.value && <span className="block text-xs font-medium text-emerald-700 mt-1">{it.value.text} per ogni assunzione, al massimo</span>}
        </span>
        <ChevronDown className={`w-4 h-4 text-mute shrink-0 mt-1 transition ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3 text-xs text-ink-2 border-t border-line pt-3">
          {it.why_not.map((w) => <p key={w} className="text-red-700 flex gap-1.5"><AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />{w}</p>)}
          {it.ok.map((w) => <p key={w} className="text-emerald-700 flex gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 mt-0.5 shrink-0" />{w}</p>)}
          {it.to_check.map((c) => (
            <p key={c.label} className="text-amber-700 flex flex-wrap items-center gap-2">{c.label}{c.key && <button className="btn !py-0.5 !text-[11px]" onClick={() => onAnswer(c.key)}>Rispondi</button>}</p>
          ))}
          <div><p className="label">Chi assumere</p><ul className="list-disc pl-4 space-y-0.5">{it.worker.map((w) => <li key={w}>{w}</li>)}</ul></div>
          <div><p className="label">Contratto</p><p>{it.contract}</p></div>
          <div><p className="label">Periodo</p><p>{it.period}</p></div>
          <div><p className="label">Condizioni sull’impresa</p><ul className="list-disc pl-4 space-y-0.5">{it.company.map((w) => <li key={w}>{w}</li>)}</ul></div>
          <div><p className="label">Cumulo e aiuti di Stato</p><p>{it.cumulation} {it.aid}</p></div>
          <div><p className="label">Come si ottiene</p><p>{it.how}</p></div>
          {it.note && <p className="text-amber-700">{it.note}</p>}
          <p className="text-[11px] text-mute">Fonte: {it.source.label} · {VERIFIED[it.verified]}</p>
          {it.search && <CatalogSearch item={it} region={it.regional ? region : null} onBudgetFrom={onBudgetFrom} />}
          {it.family === 'ESONERI_INPS' && it.value && (
            <div className="rounded-xl bg-white p-3 space-y-2">
              <p>Per gli sgravi non c’è un budget da compilare: il vantaggio si applica in busta paga. Si collega ai <span className="font-medium text-ink">bisogni di crescita</span>: quante assunzioni servono, in quale reparto e quanto valgono al massimo.</p>
              <button className="btn" onClick={() => { allocationGo('bisogni'); nav.go('allocation') }}>Usa nelle assunzioni dell’Allocazione</button>
            </div>
          )}
        </div>
      )}
    </li>
  )
}

/** Tutte le agevolazioni, non solo i bandi: esoneri INPS, tirocini, apprendistato, incentivi regionali, nuove imprese. Una famiglia alla volta, nessuna sovrapposizione. */
export default function Agevolazioni({ clientId, onBudgetFrom }) {
  const nav = useNav()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [fam, setFam] = useState('ESONERI_INPS')
  const load = () => api.measures().then((d) => { setData(d); setError(null) }).catch((e) => setError(e.message))
  useEffect(() => { load() }, [clientId])
  useEffect(() => { window.addEventListener('quanto-profile-changed', load); return () => window.removeEventListener('quanto-profile-changed', load) }, [])
  const current = useMemo(() => data?.families.find((f) => f.id === fam), [data, fam])
  const answer = (key) => { profileGo({ to: 'quick', field: key }); nav.go('profilo') }
  if (error) return <div className="space-y-6"><Guide page="agevolazioni" /><p className="text-xs text-red-700">{error}</p></div>
  if (!data) return <div className="space-y-6"><Guide page="agevolazioni" /><p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Carico…</p></div>
  const c = data.company
  return (
    <div className="space-y-6">
      <Guide page="agevolazioni" />
      <div className="card p-5 space-y-3">
        <div className="flex flex-wrap items-center gap-x-8 gap-y-2">
          <div><span className="label">Per te sì</span><div className="text-2xl font-semibold tabular-nums text-emerald-700">{data.counts.APPLICABILE || 0}</div></div>
          <div><span className="label">Da verificare</span><div className="text-2xl font-semibold tabular-nums text-amber-700">{data.counts.DA_VERIFICARE || 0}</div></div>
          <div><span className="label">Non per te</span><div className="text-2xl font-semibold tabular-nums">{(data.counts.NON_APPLICABILE || 0) + (data.counts.SCADUTA || 0)}</div></div>
          <p className="text-xs text-ink-2 flex-1 min-w-[14rem]">{c.region ? `Sede in ${c.region}${c.zes ? ' (ZES unica)' : ''}` : 'Regione non indicata'} · {c.employees != null ? `${c.employees} dipendenti` : 'dipendenti non indicati'} · {c.company_status === 'DA_COSTITUIRE' ? 'impresa da costituire' : 'già costituita'}</p>
        </div>
        {(c.durc_regular == null || !c.region || c.employees == null) && (
          <p className="text-xs text-amber-700 flex flex-wrap items-center gap-2">Mancano risposte che cambiano il risultato.<button className="btn !py-0.5 !text-[11px]" onClick={() => answer('durc_regular')}>Apri la scheda in un minuto</button></p>
        )}
        <Info label="Perché ci sono anche le misure che non sono bandi">Per far crescere un’impresa assumere costa, e parte del costo si recupera con strumenti che non passano da un bando: un esonero INPS, un tirocinio rimborsato dalla Regione, l’apprendistato. Qui trovi tutto in un posto, famiglia per famiglia. I bandi veri e propri sono nell’Allocazione e nella pagina Bandi.</Info>
      </div>

      <div className="flex flex-wrap gap-2" role="tablist" aria-label="Famiglie di agevolazioni">
        {data.families.map((f) => {
          const n = f.items.filter((i) => i.status === 'APPLICABILE').length
          return (
            <button key={f.id} role="tab" aria-selected={fam === f.id} onClick={() => setFam(f.id)}
              className={`px-3.5 py-2 rounded-full text-xs font-medium transition ${fam === f.id ? 'bg-ink text-white' : 'bg-tint text-ink-2 hover:text-ink'}`}>{f.label}{n > 0 && <span className="ml-1.5 opacity-80">· {n}</span>}</button>
          )
        })}
        <button className="px-3.5 py-2 rounded-full text-xs font-medium bg-tint text-ink-2 hover:text-ink" onClick={() => nav.go('allocation')}>Bandi e finanziamenti →</button>
      </div>

      {current && (
        <div className="space-y-3">
          <p className="text-sm text-ink-2 leading-relaxed">{current.text}</p>
          <ul className="space-y-2.5">{current.items.map((it) => <Item key={it.id} it={{ ...it, family: fam }} region={c.region} onAnswer={answer} onBudgetFrom={onBudgetFrom} />)}</ul>
        </div>
      )}
      <p className="text-[11px] text-mute leading-relaxed">Ultimo controllo delle regole: {data.verified_on.split('-').reverse().join('/')}. {data.warning}</p>
    </div>
  )
}
