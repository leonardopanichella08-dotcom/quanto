import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { AlertTriangle, CheckCircle2, Loader2, Trash2 } from 'lucide-react'
import { api } from '../lib/api'
import { fmtEur, fmtNum } from '../lib/format'
import Guide from './Guide'

const COLORS = ['#38bdf8', '#34d399', '#a78bfa', '#f472b6', '#fbbf24', '#fb7185', '#94a3b8', '#d4d4d8']
const BY_CATEGORY = { PERSONNEL: 'personnel_pct', CAPITAL_ASSETS: 'assets_pct', CONSULTING: 'consulting_pct', OVERHEAD: 'overhead_pct', TRAINING: 'training_pct' }
const CONF = { ALTA: 'bg-emerald-500/15 text-emerald-700 border-emerald-500/30', MEDIA: 'bg-sky-500/15 text-sky-700 border-sky-500/30', BASSA: 'bg-amber-500/15 text-amber-700 border-amber-500/30' }
const pct = (v) => `${fmtNum((v || 0) * 100, 1)}%`

function ShareBar({ shares, meta, height = 'h-5' }) {
  return (
    <div className={`flex ${height} rounded overflow-hidden bg-tint-2`} role="img" aria-label={meta.map((m) => `${m.label} ${pct(shares[m.key])}`).join(', ')}>
      {meta.map((m, i) => shares[m.key] > 0 && <div key={m.key} title={`${m.label}: ${pct(shares[m.key])}`} style={{ width: `${shares[m.key] * 100}%`, background: COLORS[i % COLORS.length] }} />)}
    </div>
  )
}

function Legend({ meta }) {
  return <div className="flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-ink-2">{meta.map((m, i) => <span key={m.key} className="inline-flex items-center gap-1.5"><i className="w-2.5 h-2.5 rounded-sm" style={{ background: COLORS[i % COLORS.length] }} />{m.label}</span>)}</div>
}

/** Quote del budget che hai già controllato nel Budget, per categoria (importi ammessi dal server): servono come punto di partenza, non sono un calcolo nuovo. */
function sharesOfValidation(validation) {
  if (!validation?.items?.length) return null
  const tot = {}
  validation.items.forEach((i) => { const k = BY_CATEGORY[i.category]; if (k) tot[k] = (tot[k] || 0) + i.computed_cost_eur })
  const sum = Object.values(tot).reduce((a, b) => a + b, 0)
  return sum ? { shares: Object.fromEntries(Object.entries(tot).map(([k, v]) => [k, Math.round((v / sum) * 1000) / 10])), total: Math.round(sum) } : null
}

export default function Confronto({ validation }) {
  const [meta, setMeta] = useState(null)
  const [bandi, setBandi] = useState([])
  const [mine, setMine] = useState([])
  const [niches, setNiches] = useState([])
  const [learning, setLearning] = useState(null)
  const [ateco, setAteco] = useState('')
  const [bandoId, setBandoId] = useState('')
  const [size, setSize] = useState('')
  const [region, setRegion] = useState('')
  const [rec, setRec] = useState(null)
  const [recError, setRecError] = useState(null)
  const [form, setForm] = useState({ shares: {}, total: '', outcome: 'BOZZA', score: '', note: '', shared: false })
  const [saving, setSaving] = useState(false)
  const [showMine, setShowMine] = useState(false)
  const [msg, setMsg] = useState(null)
  const [error, setError] = useState(null)
  const seq = useRef(0)
  const fromBudget = useMemo(() => sharesOfValidation(validation), [validation])

  const refresh = useCallback(async () => {
    const [m, n, l] = await Promise.all([api.templatesMine(), api.templateNiches(), api.templateLearning()])
    setMine(m); setNiches(n); setLearning(l)
  }, [])

  useEffect(() => {
    (async () => {
      try {
        const [mt, bl, ov] = await Promise.all([api.templateMeta(), api.bandi(), api.profile().catch(() => null)])
        setMeta(mt); setBandi(bl.filter((b) => b.curated || b.rules_count || b.requirements_count).sort((a, b) => a.name.localeCompare(b.name)))
        const f = ov?.fields || []
        const get = (k) => f.find((x) => x.key === k)?.value
        if (get('ateco_code')) setAteco(String(get('ateco_code')))
        if (get('region')) setRegion(String(get('region')))
        if (ov?.size?.code) setSize(ov.size.code)
        const [m, n, l] = await Promise.all([api.templatesMine(), api.templateNiches(), api.templateLearning()])
        setMine(m); setNiches(n); setLearning(l)
      } catch (e) { setError(e.message) }
    })()
  }, [])

  const ask = useCallback(async (draft) => {
    if (!ateco && !bandoId) { setRec(null); return }
    const id = ++seq.current
    setRecError(null)
    try {
      const r = await api.templateRecommend({ ateco_code: ateco || undefined, bando_id: bandoId || undefined, ...(draft ? { draft } : {}) })
      if (id === seq.current) setRec(r)
    } catch (e) { if (id === seq.current) { setRec(null); setRecError(e.message) } }
  }, [ateco, bandoId])
  useEffect(() => { const t = setTimeout(() => ask(), 350); return () => clearTimeout(t) }, [ask, mine.length])

  const draftPct = useMemo(() => Object.fromEntries(Object.entries(form.shares).filter(([, v]) => v !== '' && !Number.isNaN(Number(v))).map(([k, v]) => [k, Number(v) / 100])), [form.shares])
  const sum = Object.values(draftPct).reduce((a, b) => a + b, 0)
  const setShare = (k, v) => setForm((f) => ({ ...f, shares: { ...f.shares, [k]: v } }))

  const save = async () => {
    setSaving(true); setError(null); setMsg(null)
    try {
      const body = { ateco_code: ateco, bando_id: bandoId, shares: draftPct, outcome: form.outcome, shared: form.shared, note: form.note,
        ...(form.total ? { total_eur: Number(form.total) } : {}), ...(form.score !== '' ? { score: Number(form.score) } : {}), ...(size ? { company_size: size } : {}), ...(region ? { region } : {}) }
      const t = await api.createTemplate(body)
      setMsg(`Template salvato (${t.niche}). Il consiglio si è aggiornato${t.distance != null ? `: questo budget distava il ${fmtNum(t.distance * 100, 1)}% dal consiglio di prima` : ''}.`)
      await refresh(); await ask()
    } catch (e) { setError(e.message) } finally { setSaving(false) }
  }
  const setOutcome = async (t, outcome) => { try { await api.patchTemplate(t.id, { outcome }); await refresh(); await ask() } catch (e) { setError(e.message) } }
  const toggleShared = async (t) => { try { await api.patchTemplate(t.id, { shared: !t.shared }); await refresh(); await ask() } catch (e) { setError(e.message) } }
  const remove = async (t) => { if (!window.confirm('Eliminare questo template?')) return; try { await api.deleteTemplate(t.id); await refresh(); await ask() } catch (e) { setError(e.message) } }

  if (!meta) return <div className="space-y-6"><Guide page="pattern" />{error ? <p className="text-xs text-red-700">{error}</p> : <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Carico…</p>}</div>
  const shareMeta = meta.shares
  const bandoName = (id) => bandi.find((b) => b.bando_id === id)?.name || id

  return (
    <div className="space-y-6">
      <Guide page="pattern" />
      {error && <div className="p-3 rounded-xl border border-red-500/30 text-red-700 text-xs">{error}</div>}

      {learning && (
        <div className="card p-5 space-y-2">
          <span className="label">Come sta imparando l’algoritmo</span>
          <div className="flex flex-wrap gap-x-8 gap-y-2">
            {[['Template tuoi', learning.templates_mine], ['Nel campione', learning.templates_pool], ['Nicchie', learning.niches], ['Bandi', learning.bandi], ['Ammessi', learning.outcomes.AMMESSO]].map(([l, v]) => (
              <div key={l}><span className="label">{l}</span><div className="text-xl font-display font-semibold tabular-nums">{v}</div></div>
            ))}
          </div>
          <p className="text-[11px] text-ink-2 leading-relaxed">{learning.feedback.message} Più template e più esiti inserisci, più il consiglio diventa preciso: si ricalcola da solo a ogni salvataggio.</p>
        </div>
      )}

      <div className="card p-6 space-y-4">
        <div><h3 className="font-semibold text-base">Il budget consigliato</h3>
          <p className="text-xs text-ink-2 mt-0.5 max-w-2xl leading-relaxed">Scegli la nicchia (codice ATECO) e il bando: ti mostro come hanno ripartito il budget le aziende simili che hanno scelto quel bando, contando di più quelle ammesse.</p></div>
        <div className="grid sm:grid-cols-4 gap-3">
          <label className="space-y-1"><span className="label">Codice ATECO</span><input className="field" value={ateco} onChange={(e) => setAteco(e.target.value)} placeholder="es. 01.11 o 62.01" /></label>
          <label className="space-y-1 sm:col-span-2"><span className="label">Bando scelto</span>
            <select className="field" value={bandoId} onChange={(e) => setBandoId(e.target.value)}><option value="">— tutti i bandi —</option>{bandi.map((b) => <option key={b.bando_id} value={b.bando_id}>{b.name}</option>)}</select></label>
          <label className="space-y-1"><span className="label">Dimensione</span>
            <select className="field" value={size} onChange={(e) => setSize(e.target.value)}><option value="">—</option><option value="MICRO">Microimpresa</option><option value="SMALL">Piccola</option><option value="MEDIUM">Media</option><option value="LARGE">Grande</option></select></label>
        </div>
        {recError && <p className="text-xs text-red-700">{recError}</p>}
        {rec && rec.status === 'NO_DATA' && (
          <div className="p-3 rounded-xl border border-amber-500/30 bg-amber-500/5 text-xs text-ink-2 leading-relaxed"><p className="font-medium text-amber-700 inline-flex items-center gap-1.5"><AlertTriangle className="w-3.5 h-3.5" />Ancora pochi dati</p><p className="mt-1">{rec.message}</p></div>
        )}
        {rec && rec.status === 'OK' && (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`px-2 py-0.5 text-[11px] font-medium rounded border ${CONF[rec.confidence]}`}>Fiducia {rec.confidence.toLowerCase()}</span>
              <span className="text-xs text-ink-2">{rec.templates_used} template · {rec.basis_label}{rec.wins ? ` · ${rec.wins} ammessi` : ''}{rec.average_total_eur ? ` · budget medio ${fmtEur(rec.average_total_eur)}` : ''}</span>
            </div>
            <ShareBar shares={rec.recommended} meta={shareMeta} height="h-7" />
            <Legend meta={shareMeta} />
            <table className="w-full text-xs"><thead><tr className="text-left text-mute"><th className="py-1 font-medium">Voce</th><th className="font-medium text-right">Consigliata</th><th className="font-medium text-right">Di solito tra</th></tr></thead>
              <tbody>{shareMeta.map((m) => <tr key={m.key} className="border-t border-line"><td className="py-1.5 text-ink-2">{m.label}</td><td className="text-right font-semibold tabular-nums">{pct(rec.recommended[m.key])}</td><td className="text-right text-mute tabular-nums">{pct(rec.range[m.key].low)} – {pct(rec.range[m.key].high)}</td></tr>)}</tbody></table>
            <ul className="text-xs text-ink-2 space-y-1">{rec.explanation.map((t, i) => <li key={i} className="flex gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 mt-0.5 text-emerald-600 shrink-0" />{t}</li>)}</ul>
            {rec.styles?.length > 0 && (
              <div className="space-y-2"><span className="label">Stili di budget trovati</span>
                {rec.styles.map((s) => (
                  <div key={s.name} className="p-3 rounded-xl border border-line bg-field space-y-1.5"><div className="flex justify-between text-xs"><span className="font-medium text-ink">{s.name}</span><span className="text-mute">{s.templates} template · {s.wins} ammessi</span></div><ShareBar shares={s.shares} meta={shareMeta} height="h-3" /></div>
                ))}
              </div>
            )}
            <p className="text-[11px] text-mute">Livelli cercati: {rec.tier_counts.map((t) => `${t.label} ${t.templates}`).join(' · ')}. Il consiglio è una statistica sui template, non una previsione di esito: stessi template, stesso consiglio (impronta {rec.pool_hash}).</p>
          </div>
        )}
      </div>

      <div className="card p-6 space-y-4">
        <div><h3 className="font-semibold text-base">Salva un budget come template</h3>
          <p className="text-xs text-ink-2 mt-0.5 max-w-2xl leading-relaxed">Per un cliente di questa nicchia che ha scelto questo bando: scrivi come hai ripartito il budget del progetto e com’è andata. Il template allena il consiglio qui sopra.</p></div>
        <div className="flex flex-wrap gap-2">
          {fromBudget && <button className="btn" onClick={() => setForm((f) => ({ ...f, shares: fromBudget.shares, total: String(fromBudget.total) }))}>Parti dal budget che hai controllato</button>}
          {rec?.status === 'OK' && <button className="btn" onClick={() => setForm((f) => ({ ...f, shares: Object.fromEntries(Object.entries(rec.recommended).map(([k, v]) => [k, Math.round(v * 1000) / 10])) }))}>Parti dal consiglio</button>}
          {sum > 0 && Math.abs(sum - 1) > 0.0005 && <button className="btn" onClick={() => setForm((f) => ({ ...f, shares: Object.fromEntries(Object.entries(draftPct).map(([k, v]) => [k, Math.round((v / sum) * 1000) / 10])) }))}>Porta a 100%</button>}
        </div>
        <div className="grid sm:grid-cols-4 gap-3">
          {shareMeta.map((m) => <label key={m.key} className="space-y-1"><span className="label">{m.label} %</span><input type="number" step="0.1" min="0" className="field" value={form.shares[m.key] ?? ''} onChange={(e) => setShare(m.key, e.target.value)} /></label>)}
        </div>
        {sum > 0 && <div className="space-y-1.5"><ShareBar shares={draftPct} meta={shareMeta} /><p className={`text-[11px] ${Math.abs(sum - 1) <= 0.0205 ? 'text-ink-2' : 'text-amber-700'}`}>Totale {pct(sum)}{Math.abs(sum - 1) > 0.0205 ? ' — deve fare 100%' : ''}</p></div>}
        {rec?.status === 'OK' && sum > 0 && Math.abs(sum - 1) <= 0.0205 && (
          <button className="text-xs underline text-ink-2 text-left" onClick={() => ask(draftPct)}>Confronta con il consiglio</button>
        )}
        {rec?.comparison && <p className="text-xs text-ink-2 leading-relaxed p-3 rounded-xl bg-field border border-line">{rec.comparison.message}</p>}
        <div className="grid sm:grid-cols-4 gap-3">
          <label className="space-y-1"><span className="label">Esito</span><select className="field" value={form.outcome} onChange={(e) => setForm({ ...form, outcome: e.target.value })}>{meta.outcomes.map((o) => <option key={o.key} value={o.key}>{o.label}</option>)}</select></label>
          <label className="space-y-1"><span className="label">Importo del budget (€)</span><input type="number" className="field" value={form.total} onChange={(e) => setForm({ ...form, total: e.target.value })} /></label>
          <label className="space-y-1"><span className="label">Punteggio (facoltativo)</span><input type="number" className="field" value={form.score} onChange={(e) => setForm({ ...form, score: e.target.value })} /></label>
          <label className="space-y-1"><span className="label">Regione</span><input className="field" value={region} onChange={(e) => setRegion(e.target.value)} /></label>
        </div>
        <label className="space-y-1 block"><span className="label">Nota (facoltativa)</span><input className="field" maxLength={500} value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} placeholder="Per esempio: progetto di meccanizzazione, cofinanziamento 40%" /></label>
        <label className="inline-flex items-center gap-2 text-xs text-ink-2 cursor-pointer"><input type="checkbox" checked={form.shared} onChange={(e) => setForm({ ...form, shared: e.target.checked })} />Condividi in forma anonima (niente ragione sociale né partita IVA) per allenare l’algoritmo di tutti</label>
        <div className="flex items-center gap-3">
          <button className="btn-primary" disabled={saving || !ateco || !bandoId || Math.abs(sum - 1) > 0.0205} onClick={save}>{saving && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Salva template</button>
          {(!ateco || !bandoId) && <span className="text-xs text-mute">Indica il codice ATECO e il bando.</span>}
        </div>
        {msg && <p className="text-xs text-emerald-700">{msg}</p>}
      </div>

      <div className="card p-6 space-y-3">
        <div><h3 className="font-semibold text-base">Mappa: quali nicchie partecipano a quali bandi</h3>
          <p className="text-xs text-ink-2 mt-0.5">Per ogni nicchia, i bandi scelti con la ripartizione media del budget e quanti sono stati ammessi. Clicca un bando per vedere il consiglio.</p></div>
        {niches.length === 0 && <p className="text-xs text-mute">Nessun template ancora: salvane uno qui sopra e la mappa si costruisce.</p>}
        {niches.map((n) => (
          <div key={n.division} className="rounded-2xl border border-line bg-field p-4 space-y-2">
            <div className="flex flex-wrap justify-between gap-2 text-sm"><span className="font-semibold text-ink">{n.niche}</span><span className="text-xs text-mute">{n.templates} template · {n.wins} ammessi</span></div>
            {n.bandi.map((b) => (
              <button key={b.bando_id} className="w-full text-left space-y-1 hover:bg-white/60 rounded-lg p-1.5" onClick={() => { setAteco(n.division); setBandoId(b.bando_id); window.scrollTo({ top: 0, behavior: 'smooth' }) }}>
                <div className="flex flex-wrap justify-between gap-2 text-xs"><span className="text-ink-2 min-w-0 break-words">{b.bando_name}</span><span className="text-mute">{b.templates} template · {b.submitted} presentati · {b.wins} ammessi{b.regions.length ? ` · ${b.regions.join(', ')}` : ''}</span></div>
                <ShareBar shares={b.shares} meta={shareMeta} height="h-3" />
              </button>
            ))}
            <Legend meta={shareMeta} />
          </div>
        ))}
      </div>

      <div className="card p-6 space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="min-w-0 flex-1"><h3 className="font-semibold text-base">I miei dati di apprendimento</h3>
            <p className="text-xs text-ink-2 mt-0.5">I template che hai salvato servono solo all’algoritmo e restano chiusi: aprili per aggiornare un esito (quando il bando risponde) o per eliminarne uno. Nessun altro li vede.</p></div>
          <button className="btn" onClick={() => setShowMine(!showMine)}>{showMine ? 'Nascondi' : `Apri i miei template (${mine.length})`}</button>
        </div>
        {showMine && mine.length === 0 && <p className="text-xs text-mute">Nessun template salvato.</p>}
        {showMine && mine.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-xs"><thead><tr className="text-left text-mute"><th className="py-1.5 font-medium">Nicchia</th><th className="font-medium">Bando</th><th className="font-medium w-48">Ripartizione</th><th className="font-medium">Esito</th><th className="font-medium">Condiviso</th><th /></tr></thead>
              <tbody>{mine.map((t) => (
                <tr key={t.id} className="border-t border-line align-top">
                  <td className="py-2 pr-2 text-ink-2">{t.niche}{t.total_eur ? <span className="block text-[10px] text-mute">{fmtEur(t.total_eur)}</span> : null}</td>
                  <td className="pr-2 text-ink-2 max-w-[14rem] break-words">{bandoName(t.bando_id)}</td>
                  <td className="pr-2"><ShareBar shares={t.shares} meta={shareMeta} height="h-3" /></td>
                  <td><select className="field !py-1 !w-auto" value={t.outcome} onChange={(e) => setOutcome(t, e.target.value)}>{meta.outcomes.map((o) => <option key={o.key} value={o.key}>{o.label}</option>)}</select></td>
                  <td><input type="checkbox" checked={t.shared} onChange={() => toggleShared(t)} aria-label="Condiviso in forma anonima" /></td>
                  <td className="text-right"><button className="text-mute hover:text-red-700" onClick={() => remove(t)} aria-label="Elimina"><Trash2 className="w-3.5 h-3.5" /></button></td>
                </tr>
              ))}</tbody></table>
          </div>
        )}
      </div>
    </div>
  )
}
