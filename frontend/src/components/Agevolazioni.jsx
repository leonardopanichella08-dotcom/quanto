import React, { useEffect, useMemo, useRef, useState } from 'react'
import { AlertTriangle, CheckCircle2, ChevronDown, Loader2, Plus, X } from 'lucide-react'
import { api } from '../lib/api'
import { fmtEur } from '../lib/format'
import { Fold, Info } from './ui'
import Guide from './Guide'
import AgentBar from './AgentBar'
import { StudyResult } from './PipelineButton'
import { allocationGo, profileGo, useNav } from '../lib/nav'
import { loadChoice, saveChoice } from '../lib/measureChoice'

const STATUS = {
  APPLICABILE: ['Per te sì', 'bg-emerald-500/15 text-emerald-700'],
  DA_VERIFICARE: ['Da verificare', 'bg-amber-500/15 text-amber-700'],
  NON_APPLICABILE: ['Non per te', 'bg-red-500/10 text-red-700'],
  SCADUTA: ['Scaduta', 'bg-ink/10 text-ink-2'],
  DOPO_LA_COSTITUZIONE: ['Dopo la costituzione', 'bg-sky-500/15 text-sky-700'],
}
const VERIFIED = { SECONDARIA: 'letta su fonti secondarie: conferma sul sito INPS', DA_VERIFICARE: 'parametri da leggere nel bando o nella circolare' }
const itDate = (iso) => (iso && iso !== 'non indicata' ? iso.split('-').reverse().join('/') : null)
const GENDER = [['', 'Sesso'], ['F', 'Donna'], ['M', 'Uomo']]
const AGE = [['', 'Età'], ['UNDER35', 'Meno di 35 anni'], ['OVER35', '35 anni o più']]
const UNEMPLOYED = [['', 'Senza lavoro da'], ['LT6', 'meno di 6 mesi'], ['6_12', '6-12 mesi'], ['12_24', '12-24 mesi'], ['GE24', '24 mesi o più']]
const THIS_YEAR = new Date().getFullYear()
const YEARS = [['', 'Anno'], [String(THIS_YEAR), `Nel ${THIS_YEAR}`], [String(THIS_YEAR + 1), `Nel ${THIS_YEAR + 1}`]]
const BLANK = { gender: '', age: '', unemployed: '', year: '' }

/** Le opportunità aperte del catalogo per questa misura: le trova l'agente (solo se provate nella regione dell'impresa). Ognuna dice se è un bando (con un budget)
 * o un'agevolazione (senza budget) e ha un solo pulsante principale; lo studio, se serve, si fa qui, e l'esito si legge sotto la voce. */
function Linked({ item, onBudgetFrom }) {
  const nav = useNav()
  const [working, setWorking] = useState(null)        // voce in lavorazione: {id, what}
  const [outcome, setOutcome] = useState({})          // esito dello studio, per voce: si mostra dove si è cliccato
  const [error, setError] = useState(null)
  const list = item.linked || []
  const isStudied = (m) => m.studied || outcome[m.bando_id]?.studied
  const toBudget = async (m) => {
    setWorking({ id: m.bando_id, what: 'budget' }); setError(null)
    try {
      const r = await onBudgetFrom?.(m.bando_id)
      if (r && !r.ok) setOutcome((x) => ({ ...x, [m.bando_id]: r.study }))              // niente Budget: il motivo resta qui
    } catch (e) { setError(e.message) } finally { setWorking(null) }
  }
  const toAllocation = async (m) => {
    setWorking({ id: m.bando_id, what: 'allocazione' }); setError(null)
    try {
      if (!isStudied(m)) { const r = await api.researchRun({ bando_id: m.bando_id }); setOutcome((x) => ({ ...x, [m.bando_id]: r.study })) }
      allocationGo({ step: 'bandi', bando: m.bando_id }); nav.go('allocation')
    } catch (e) { setError(e.message) } finally { setWorking(null) }
  }
  if (item.linked_note) return <p className="text-xs text-amber-700">{item.linked_note}</p>
  if (!list.length) return <p className="text-xs text-mute">Nulla di aperto nel catalogo{item.linked_region ? ` per la regione ${item.linked_region}` : ''}: il catalogo si aggiorna ogni notte e lo ricontrollo da solo.</p>
  return (
    <div className="space-y-2">
      <p className="label">Aperti ora nel catalogo{item.linked_region ? ` · ${item.linked_region}` : ''}</p>
      {error && <p className="text-xs text-red-700">{error}</p>}
      <ul className="space-y-2">
        {list.map((m) => {
          const busyHere = working?.id === m.bando_id
          const noBudget = m.budget === false || outcome[m.bando_id]?.budget === false
          const st = outcome[m.bando_id]
          return (
            <li key={m.bando_id} className="rounded-xl bg-white p-3 space-y-2">
              <div className="flex flex-wrap items-start gap-2"><p className="text-sm font-medium text-ink flex-1 min-w-0 break-words">{m.name}</p>
                <span className={`px-2 py-0.5 rounded-full text-[11px] font-medium ${noBudget ? 'bg-sky-500/15 text-sky-700' : 'bg-tint text-ink-2'}`}>{noBudget ? 'Agevolazione · niente budget' : 'Bando'}</span></div>
              <p className="text-[11px] text-mute">{m.issuer || 'Ente non indicato'}{m.form ? ` · ${m.form}` : ''}{itDate(m.deadline) ? ` · scade il ${itDate(m.deadline)}` : ''}{isStudied(m) ? ' · studiato' : ''}</p>
              {st && !st.budget_ready && <StudyResult study={st} />}
              {st?.retry && (
                <button className="btn !py-1" disabled={!!working} onClick={async () => { setWorking({ id: m.bando_id, what: 'retry' }); try { const r = await api.researchRun({ bando_id: m.bando_id }); setOutcome((x) => ({ ...x, [m.bando_id]: r.study })) } catch (e) { setError(e.message) } finally { setWorking(null) } }}>
                  {busyHere && working.what === 'retry' ? <Loader2 className="w-3 h-3 animate-spin" /> : null}Riprova la lettura</button>)}
              <div className="flex flex-wrap items-center gap-2">
                {!noBudget && !(st && !st.budget_ready) && (
                  <button className="btn-primary !py-1" disabled={!!working} onClick={() => toBudget(m)}>{busyHere && working.what === 'budget' ? <Loader2 className="w-3 h-3 animate-spin" /> : null}{isStudied(m) ? 'Fai il budget' : 'Studia e fai il budget'}</button>)}
                <button className={`${noBudget || (st && !st.budget_ready) ? 'btn-primary' : 'btn'} !py-1`} disabled={!!working} onClick={() => toAllocation(m)}>{busyHere && working.what === 'allocazione' ? <Loader2 className="w-3 h-3 animate-spin" /> : null}{isStudied(m) ? 'Vedi nell’Allocazione' : 'Studia e vedi nell’Allocazione'}</button>
                {busyHere && <span className="text-[11px] text-mute">Leggo le fonti ufficiali: può richiedere fino a un minuto.</span>}
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

function Item({ it, onAnswer, onBudgetFrom, assignedTo }) {
  const [open, setOpen] = useState(false)
  const [label, tone] = STATUS[it.status] || STATUS.DA_VERIFICARE
  return (
    <li className="rounded-2xl bg-tint">
      <button type="button" onClick={() => setOpen(!open)} aria-expanded={open} className="w-full text-left px-4 py-3 flex items-start gap-3">
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-2"><span className="text-sm font-semibold text-ink">{it.name}</span><span className={`px-2 py-0.5 rounded-full text-[11px] font-medium ${tone}`}>{label}</span>
            {assignedTo > 0 && <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-ink text-white">Scelta per {assignedTo === 1 ? '1 persona' : `${assignedTo} persone`}</span>}
            {it.linked?.length > 0 && <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-sky-500/15 text-sky-700">{it.linked.length} {it.linked.length === 1 ? 'aperto' : 'aperti'} nel catalogo{it.linked_region ? ` · ${it.linked_region}` : ''}</span>}</span>
          <span className="block text-xs text-ink-2 mt-1 leading-snug">{it.tagline}</span>
          {it.value && <span className="block text-xs font-medium text-emerald-700 mt-1">{it.value.text} per ogni assunzione, al massimo</span>}
        </span>
        <ChevronDown className={`w-4 h-4 text-mute shrink-0 mt-1 transition ${open ? 'rotate-180' : ''}`} />
      </button>
      {it.existing_contract && <p className="px-4 pb-3 -mt-1 text-[11px] text-ink-2">Si usa su un contratto a termine già in corso, non su una nuova assunzione: per questo non entra nel totale dell’Allocazione.</p>}
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
          {it.search && <Linked item={it} onBudgetFrom={onBudgetFrom} />}
        </div>
      )}
    </li>
  )
}

const Select = ({ label, value, onChange, options }) => (
  <select aria-label={label} className={`field !py-1.5 text-xs min-w-0 ${value ? 'text-ink' : 'text-mute'}`} value={value} onChange={(e) => onChange(e.target.value)}>
    {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
  </select>
)

/** Chi assume l'impresa: per ogni persona l'agente sceglie la sola agevolazione più ricca che vale per l'impresa e per lei. Le persone arrivano dal bisogno di crescita; i dati che mancano si chiedono. */
function Hires({ positions, setPositions, assign, busy }) {
  const set = (i, k, v) => setPositions(positions.map((p, j) => (j === i ? { ...p, [k]: v } : p)))
  const res = assign?.positions || []
  return (
    <section className="card p-5 space-y-4" aria-label="Chi assume l’impresa">
      <div className="flex flex-wrap items-start gap-3">
        <div className="min-w-0 flex-1">
          <h3 className="text-base font-semibold tracking-tight text-ink">Chi assume l’impresa</h3>
          <p className="text-sm text-ink-2 mt-0.5">Indica ogni persona: per ognuna scelgo lo sgravio che vale di più e lo metto nel piano.</p>
        </div>
        {assign?.counted > 0 && <div className="text-right"><span className="label">Nel piano</span><div className="text-xl font-display font-semibold text-emerald-700 tabular-nums">{fmtEur(assign.total_eur)}</div></div>}
      </div>
      {positions.length === 0 && <p className="text-sm text-ink-2">Nessuna assunzione indicata. Aggiungi una persona per vedere cosa si recupera.</p>}
      <ul className="space-y-2.5">
        {positions.map((p, i) => {
          const r = res[i]
          const b = r?.best
          return (
            <li key={i} className="rounded-2xl bg-tint p-3 space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-ink">Persona {i + 1}</span>
                <button type="button" className="ml-auto text-mute hover:text-red-700" aria-label={`Togli la persona ${i + 1}`} onClick={() => setPositions(positions.filter((_, j) => j !== i))}><X className="w-4 h-4" /></button>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <Select label={`Sesso della persona ${i + 1}`} value={p.gender} onChange={(v) => set(i, 'gender', v)} options={GENDER} />
                <Select label={`Età della persona ${i + 1}`} value={p.age} onChange={(v) => set(i, 'age', v)} options={AGE} />
                <Select label={`Da quanto la persona ${i + 1} è senza lavoro`} value={p.unemployed} onChange={(v) => set(i, 'unemployed', v)} options={UNEMPLOYED} />
                <Select label={`In che anno si assume la persona ${i + 1}`} value={String(p.year ?? '')} onChange={(v) => set(i, 'year', v)} options={YEARS} />
              </div>
              {r && (b ? (
                <p className="text-xs leading-snug">
                  <span className="font-medium text-ink">{b.name}</span>
                  <span className="text-ink-2"> · {b.value_text}</span>
                  {b.sure && b.exact ? <span className="text-emerald-700"> · nel piano</span> : <span className="text-amber-700"> · non nel piano: manca {b.to_check.join(', ') || 'un dato'}</span>}
                  {r.better_if && <span className="block text-ink-2">Potrebbe valere di più: {r.better_if.name}, {fmtEur(r.better_if.value_eur)}, se indichi {r.better_if.missing.join(', ')}.</span>}
                </p>
              ) : (
                <p className="text-xs text-amber-700 leading-snug">{r.message}
                  {!r.late && r.rejected?.length > 0 && <span className="block text-ink-2">{r.rejected.slice(0, 3).map((x) => `${x.name}: ${x.why.charAt(0).toLowerCase()}${x.why.slice(1)}`).join(' · ')}</span>}
                </p>
              ))}
            </li>
          )
        })}
      </ul>
      <div className="flex flex-wrap items-center gap-3">
        <button type="button" className="btn" disabled={positions.length >= 50} onClick={() => setPositions([...positions, { ...BLANK }])}><Plus className="w-3.5 h-3.5" />Aggiungi una persona</button>
        {busy && <span className="text-xs text-mute flex items-center gap-1.5"><Loader2 className="w-3 h-3 animate-spin" />Calcolo…</span>}
      </div>
      <Info label="Come scelgo e perché non si sommano">
        <p>Ogni persona usa <strong className="text-ink">una sola</strong> agevolazione: gli esoneri 2026 non si sommano tra loro per la stessa assunzione. Persone diverse possono usarne di diverse, e allora si sommano.</p>
        <p>Il valore è il tetto mensile per i mesi della fascia: per esempio 650 € al mese per 24 mesi = 15.600 €. È un <strong className="text-ink">massimo</strong>: l’esonero non supera i contributi che il datore deve davvero.</p>
        <p>Gli esoneri 2026 valgono solo per chi è assunto <strong className="text-ink">entro il 31/12/2026</strong>: per un’assunzione dell’anno dopo serve una nuova norma, e finché non c’è non conto nulla.</p>
        <p>Una persona senza tutti i dati non entra nel totale: te lo dico e dico quale dato manca. Se per lei un’agevolazione è certa e un’altra più ricca dipende da un dato mancante, conto la certa e ti mostro l’altra. Le assunzioni indicate sono anche quelle del piano dell’Allocazione.</p>
      </Info>
    </section>
  )
}

/** Tutte le agevolazioni, non solo i bandi: esoneri INPS, tirocini, apprendistato, incentivi regionali, nuove imprese. Una famiglia alla volta, nessuna sovrapposizione. */
export default function Agevolazioni({ clientId, onBudgetFrom }) {
  const nav = useNav()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [fam, setFam] = useState('ESONERI_INPS')
  const [all, setAll] = useState(false)
  const load = () => api.measures().then((d) => { setData(d); setError(null) }).catch((e) => setError(e.message))
  useEffect(() => { load() }, [clientId])
  useEffect(() => { window.addEventListener('quanto-profile-changed', load); return () => window.removeEventListener('quanto-profile-changed', load) }, [])

  // chi si assume: dalle persone salvate per questo lavoro; se non ce ne sono, tante quante ne servono alla crescita prevista (dati da completare)
  const [positions, setPositions] = useState(null)
  const [assign, setAssign] = useState(null)
  const [busy, setBusy] = useState(false)
  const touched = useRef(false)
  const edit = (next) => { touched.current = true; setPositions(next) }
  useEffect(() => {
    let live = true
    api.clientState('measure_positions').then((st) => st?.value?.positions).catch(() => null).then(async (saved) => {
      if (!live) return
      if (Array.isArray(saved)) { touched.current = true; setPositions(saved); return }          // persone indicate dallo studio: il piano si riallinea sempre a loro (anche dopo un cambio di regole)
      let n = 0
      try { n = (await api.needs())?.people?.total || 0 } catch { n = 0 }
      if (live) setPositions(Array.from({ length: Math.min(n, 10) }, () => ({ ...BLANK })))
    })
    return () => { live = false }
  }, [clientId])
  useEffect(() => {
    if (positions === null) return undefined
    let live = true
    const t = setTimeout(async () => {
      setBusy(true)
      try {
        const r = await api.measuresAssign(positions)
        if (!live) return
        setAssign(r)
        if (touched.current) {                                            // solo dopo una modifica: le scelte fatte in passato non si cancellano per un'anteprima
          api.saveClientState('measure_positions', { positions }).catch(() => {})
          saveChoice(r.items.map((i) => ({ id: i.id, hires: i.hires, assigned: true, months: i.months })))
        }
      } catch { if (live) setAssign(null) } finally { if (live) setBusy(false) }
    }, 400)
    return () => { live = false; clearTimeout(t) }
  }, [positions, data?.company?.durc_regular, data?.company?.region])        // eslint-disable-line react-hooks/exhaustive-deps
  const [legacy, setLegacy] = useState([])
  useEffect(() => { loadChoice().then(setLegacy) }, [clientId, assign])
  const assignedCount = useMemo(() => Object.fromEntries((assign?.items || []).map((i) => [i.id, i.hires])), [assign])

  const current = useMemo(() => data?.families.find((f) => f.id === fam), [data, fam])
  const answer = (key) => { profileGo({ to: 'quick', field: key }); nav.go('profilo') }
  if (error) return <div className="space-y-6"><Guide page="agevolazioni" /><p className="text-xs text-red-700">{error}</p></div>
  if (!data || positions === null) return <div className="space-y-6"><Guide page="agevolazioni" /><p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Carico…</p></div>
  const c = data.company
  const total = data.families.reduce((a, f) => a + f.items.length, 0)
  const sure = data.counts.APPLICABILE || 0
  const open = (assign?.positions || []).filter((p) => p.best && !(p.best.sure && p.best.exact))
  const incomplete = open.length
  const missingWhat = [...new Set(open.flatMap((p) => p.best.to_check).filter((x) => !x.endsWith('?') && x.length < 40))].slice(0, 4).join(', ')      // solo i dati della persona: quelli dell'impresa hanno la loro riga
  const missingCompany = c.durc_regular == null || !c.region || c.employees == null
  const need = [
    missingCompany && <span key="co" className="inline-flex flex-wrap items-center gap-2">Mancano dati dell’impresa (DURC, regione o dipendenti).<button className="btn !py-0.5 !text-[11px]" onClick={() => answer('durc_regular')}>Rispondi in un minuto</button></span>,
    incomplete > 0 && <span key="pp">Per {incomplete === 1 ? '1 persona manca' : `${incomplete} persone mancano`} {missingWhat || 'dei dati'}: finché non {incomplete === 1 ? 'li indichi non entra' : 'li indichi non entrano'} nel totale.</span>,
    data.stale && <span key="st">Le regole sono state controllate il {itDate(data.verified_on)} ({data.verified_age_days} giorni fa): conferma sul sito INPS.</span>,
  ].filter(Boolean)
  const place = `${c.region ? `${c.region}${c.zes ? ' (ZES unica)' : ''}` : 'regione non indicata'}, ${c.employees != null ? `${c.employees} dipendenti` : 'dipendenti non indicati'}`
  return (
    <div className="space-y-6">
      <AgentBar current="agevolazioni"
        did={`Ho controllato ${total} agevolazioni per l’impresa: ${place}.`}
        found={`${sure === 1 ? '1 vale' : `${sure} valgono`} per questa impresa.${assign?.counted ? ` Per ${assign.counted === 1 ? '1 persona' : `${assign.counted} persone`} recuperi fino a ${fmtEur(assign.total_eur)}: ${assign.counted === 1 ? 'è già' : 'sono già'} nel totale dell’Allocazione.` : ''}${assign?.uncertain_max_eur > 0 ? ` Altri ${fmtEur(assign.uncertain_max_eur)} al massimo, se i dati mancanti lo confermano.` : ''}`}
        need={need.length ? <span className="space-y-1 block">{need.map((n, i) => <span key={i} className="block">{n}</span>)}</span> : null}
        next={{ label: 'Vai all’Allocazione', onClick: () => { allocationGo('misure'); nav.go('allocation') } }} />
      <Guide page="agevolazioni" />

      <Hires positions={positions} setPositions={edit} assign={assign} busy={busy} />
      {legacy.some((x) => !x.assigned) && !touched.current && <p className="text-[11px] text-ink-2">Hai anche agevolazioni scelte in precedenza: restano nell’Allocazione finché non indichi le persone qui sopra, poi le sostituisce la scelta per persona.</p>}

      <Fold id="fold-agevolazioni" title="Tutte le agevolazioni" summary={`${total} misure in ${data.families.length} famiglie · ${sure} per te sì · ${data.counts.DA_VERIFICARE || 0} da verificare`} open={all} onToggle={() => setAll(!all)}>
        <div className="space-y-3 pt-3">
          <div className="flex flex-wrap gap-2" role="tablist" aria-label="Famiglie di agevolazioni">
            {data.families.map((f) => {
              const n = f.items.filter((i) => i.status === 'APPLICABILE').length
              return (
                <button key={f.id} role="tab" aria-selected={fam === f.id} onClick={() => setFam(f.id)}
                  className={`px-3.5 py-2 rounded-full text-xs font-medium transition ${fam === f.id ? 'bg-ink text-white' : 'bg-tint text-ink-2 hover:text-ink'}`}>{f.label}{n > 0 && <span className="ml-1.5 opacity-80">· {n}</span>}</button>
              )
            })}
          </div>
          {current && (
            <div className="space-y-3">
              <p className="text-sm text-ink-2 leading-relaxed">{current.text}</p>
              <ul className="space-y-2.5">{current.items.map((it) => <Item key={it.id} it={{ ...it, family: fam }} onAnswer={answer} onBudgetFrom={onBudgetFrom} assignedTo={assignedCount[it.id] || 0} />)}</ul>
            </div>
          )}
          <button className="text-xs underline text-ink-2" onClick={() => nav.go('bandi')}>Cerca tra tutti i bandi</button>
        </div>
      </Fold>
      <p className="text-[11px] text-mute leading-relaxed">Regole controllate il {itDate(data.verified_on)} ({data.verified_age_days === 0 ? 'oggi' : `${data.verified_age_days} giorni fa`}). {data.warning}</p>
    </div>
  )
}
