import React, { useCallback, useEffect, useState } from 'react'
import { CheckCircle2, Loader2 } from 'lucide-react'
import { api } from '../lib/api'

const TYPE_DOC = { CAPITALI: 'Servono bilancio e visura', PERSONE: 'Serve la dichiarazione dei redditi', DITTA: 'Serve la dichiarazione dei redditi' }

/** Sì / No / Non so: «Non so» lascia la risposta vuota (si chiede, non si indovina). */
function Tri({ label, hint, value, onSet, id }) {
  const opts = [[false, 'No'], [true, 'Sì']]
  return (
    <div id={id} className="flex flex-wrap items-center gap-x-4 gap-y-1.5 py-2">
      <div className="min-w-0 flex-1"><p className="text-sm text-ink leading-snug">{label}</p>{hint && <p className="text-[11px] text-mute leading-snug">{hint}</p>}</div>
      <div className="inline-flex rounded-full bg-tint p-0.5" role="group" aria-label={label}>
        {opts.map(([v, l]) => (
          <button key={l} type="button" aria-pressed={value === v} onClick={() => onSet(value === v ? '' : v)}
            className={`px-4 py-1 rounded-full text-xs transition ${value === v ? 'bg-white shadow-sm font-medium text-ink' : 'text-ink-2 hover:text-ink'}`}>{l}</button>
        ))}
      </div>
    </div>
  )
}

function Choice({ options, value, onSet, describe }) {
  return (
    <div className="grid sm:grid-cols-3 gap-2" role="radiogroup">
      {options.map((o) => (
        <button key={o.value} type="button" role="radio" aria-checked={value === o.value} onClick={() => onSet(o.value)}
          className={`text-left rounded-2xl p-3 transition ${value === o.value ? 'bg-white border-2 border-ink shadow-sm' : 'bg-tint hover:bg-tint-2 border border-transparent'}`}>
          <span className="block text-sm font-medium text-ink leading-snug">{o.label}</span>
          {describe && <span className="block text-[11px] text-mute mt-1">{describe(o.value)}</span>}
        </button>
      ))}
    </div>
  )
}

/** La scheda in un minuto: poche risposte, quasi tutte un tocco. Se c'è la visura, molte arrivano da sole. */
export default function QuickProfile({ version = 0, onChanged }) {
  const [ov, setOv] = useState(null)
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)
  const [text, setText] = useState({})
  const load = useCallback(() => api.profile().then((o) => { setOv(o); setError(null) }).catch((e) => setError(e.message)), [])
  useEffect(() => { load() }, [load, version])
  useEffect(() => {
    window.addEventListener('quanto-profile-changed', load)
    return () => window.removeEventListener('quanto-profile-changed', load)
  }, [load])
  if (!ov) return <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Carico…</p>
  const q = Object.fromEntries(ov.quick.fields.map((f) => [f.key, f]))
  const val = (k) => (k in text ? text[k] : q[k]?.value ?? '')
  const save = async (key, value) => {
    setBusy(key); setError(null)
    try { setOv(await api.saveProfile({ [key]: value === '' ? null : value })); setText((t) => { const n = { ...t }; delete n[key]; return n }); onChanged?.() } catch (e) { setError(e.message) } finally { setBusy(null) }
  }
  const type = ov.company_type
  const capitali = type === 'CAPITALI' || !type
  const origin = (k) => (q[k]?.source?.origin === 'DOCUMENT' ? 'dalla visura' : q[k]?.source?.origin === 'DERIVED' ? 'dedotto' : null)
  const field = (k, label, props = {}) => (
    <label className="space-y-1 block"><span className="label">{label}{origin(k) && <span className="normal-case font-normal text-emerald-700"> · {origin(k)}</span>}</span>
      <input className="field" value={val(k)} {...props} onChange={(e) => setText((t) => ({ ...t, [k]: e.target.value }))} onBlur={() => { if (k in text && String(text[k]) !== String(q[k]?.value ?? '')) save(k, text[k]) }} /></label>
  )
  return (
    <div className="space-y-6 pt-3">
      <div className="flex flex-wrap items-center gap-3">
        <p className="text-sm text-ink-2 flex-1 min-w-[16rem]">Rispondi con un tocco. Se hai caricato la visura, molte risposte ci sono già; il resto serve a trovare le agevolazioni giuste.</p>
        <span className="text-xs text-mute tabular-nums">{ov.quick.answered} di {ov.quick.total} risposte{busy && <Loader2 className="inline w-3 h-3 ml-1.5 animate-spin" />}</span>
      </div>
      {error && <p className="text-xs text-red-700">{error}</p>}

      <section className="space-y-2">
        <h4 className="text-[13px] font-semibold text-ink">Che tipo di impresa è?</h4>
        <Choice options={ov.company_types} value={type || ''} onSet={(v) => save('company_type', v)} describe={(v) => TYPE_DOC[v]} />
        {q.company_type?.source?.origin === 'DERIVED' && <p className="text-[11px] text-emerald-700">Dedotto dalla forma giuridica della visura: toccane un altro per cambiare.</p>}
        <div className="pt-1"><Choice options={ov.company_statuses.map((s) => ({ value: s.value, label: s.value === 'COSTITUITA' ? 'Già costituita' : 'Nuova o da costituire' }))} value={val('company_status') || 'COSTITUITA'} onSet={(v) => save('company_status', v)} /></div>
      </section>

      <section className="space-y-3">
        <h4 className="text-[13px] font-semibold text-ink">Dove e di cosa si occupa</h4>
        <div className="grid sm:grid-cols-4 gap-3">
          <label className="space-y-1 block sm:col-span-2"><span className="label">Regione della sede{origin('region') && <span className="normal-case font-normal text-emerald-700"> · {origin('region')}</span>}</span>
            <select className="field" value={val('region')} onChange={(e) => save('region', e.target.value)}><option value="">— scegli —</option>{ov.regions.map((r) => <option key={r}>{r}</option>)}</select></label>
          {field('province', 'Provincia', { maxLength: 2, placeholder: 'es. BA' })}
          {field('employees', 'Dipendenti', { type: 'number', min: 0 })}
          <div className="sm:col-span-2">{field('ateco_code', 'Codice ATECO principale', { placeholder: 'es. 62.01' })}</div>
          <div className="sm:col-span-2">{field('ateco_secondary', 'Altri ATECO (facoltativo)', { placeholder: 'es. 47.91, 73.11' })}</div>
          {val('company_status') !== 'DA_COSTITUIRE' && field('founded_year', 'Anno di costituzione', { type: 'number', min: 1900 })}
        </div>
      </section>

      <section className="space-y-1">
        <h4 className="text-[13px] font-semibold text-ink">Soci e regolarità</h4>
        <div className="divide-y divide-line">
          <Tri id="pf-founders_under35" label="Almeno un socio o il titolare ha meno di 35 anni" hint="Per gli incentivi ai giovani" value={val('founders_under35')} onSet={(v) => save('founders_under35', v)} />
          <Tri id="pf-women_majority" label="L’impresa è a prevalenza femminile" hint="Soci o titolare in maggioranza donne" value={val('women_majority')} onSet={(v) => save('women_majority', v)} />
          <Tri id="pf-founders_unemployed" label="Un socio o promotore è disoccupato o inoccupato" hint="Serve per l’autoimpiego e le nuove imprese" value={val('founders_unemployed')} onSet={(v) => save('founders_unemployed', v)} />
          <Tri id="pf-durc_regular" label="L’impresa è regolare con DURC, contributi e imposte" hint="Quasi ogni agevolazione lo richiede" value={val('durc_regular')} onSet={(v) => save('durc_regular', v)} />
          {capitali && <Tri id="pf-is_innovative_startup" label="È una start-up innovativa iscritta al registro" value={val('is_innovative_startup')} onSet={(v) => save('is_innovative_startup', v)} />}
        </div>
        <p className="text-[11px] text-mute pt-1">Non so: lascia vuoto. Le agevolazioni che dipendono da quella risposta restano «da verificare», non vengono scartate.</p>
      </section>
      {ov.quick.answered === ov.quick.total && <p className="text-xs text-emerald-700 inline-flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5" />Scheda completa.</p>}
    </div>
  )
}
