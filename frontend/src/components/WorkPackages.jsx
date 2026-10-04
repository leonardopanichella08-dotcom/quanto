import React, { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, CheckCircle2, Download, Layers, Loader2, Plus, Trash2, XCircle } from 'lucide-react'
import { api, download } from '../lib/api'
import { fmtEur } from '../lib/format'
import { CATEGORY_LABEL, CATEGORY_ORDER } from '../lib/format'
import { Hint } from './Help'

const STORE = (bando) => `quanto_wp_${bando || 'nessuno'}`
const EXAMPLE = ['Coordinamento e gestione', 'Sviluppo', 'Sperimentazione e validazione', 'Diffusione e comunicazione']
const pctOrNull = (v) => (v === '' || v == null || Number.isNaN(Number(v)) ? null : Math.max(0, Math.min(1, Number(v) / 100)))
const CSV_SEP = ';'
const CRLF = String.fromCharCode(13, 10)

function load(bando) {
  try { const v = JSON.parse(localStorage.getItem(STORE(bando)) || 'null'); if (v && Array.isArray(v.wps)) return v } catch { /* niente archivio: si parte da zero */ }
  return { wps: [], split: false }
}

const blank = (n) => ({ wp_id: `WP${n}`, name: '', min: '', target: '', max: '', allowed: [], caps: {} })

/** Ripartizione delle voci AMMESSE tra i pacchetti di lavoro del bando: i vincoli li scrive chi conosce il bando, il calcolo (risolutore esatto) è sul server. */
export default function WorkPackages({ bando, projectId, validation, request }) {
  const initial = useMemo(() => load(bando?.bando_id), [bando?.bando_id])
  const [wps, setWps] = useState(initial.wps)
  const [split, setSplit] = useState(initial.split)
  const [pins, setPins] = useState({})
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [res, setRes] = useState(null)
  const [error, setError] = useState(null)
  useEffect(() => { setWps(initial.wps); setSplit(initial.split); setRes(null); setPins({}) }, [initial])
  useEffect(() => { try { localStorage.setItem(STORE(bando?.bando_id), JSON.stringify({ wps, split })) } catch { /* l'archivio può non esserci */ } }, [wps, split, bando?.bando_id])

  const admitted = useMemo(() => {
    const desc = Object.fromEntries((request?.cost_items || []).map((i) => [i.item_id, i.description]))
    return (validation?.items || []).filter((i) => i.computed_cost_eur > 0).map((i) => ({ item_id: i.item_id, category: i.category, amount_eur: i.computed_cost_eur, description: desc[i.item_id] || i.description || '' }))
  }, [validation, request])
  const total = admitted.reduce((s, i) => s + i.amount_eur, 0)

  const set = (k, patch) => setWps((cur) => cur.map((w, i) => (i === k ? { ...w, ...patch } : w)))
  const toggle = (k, cat) => set(k, { allowed: wps[k].allowed.includes(cat) ? wps[k].allowed.filter((c) => c !== cat) : [...wps[k].allowed, cat] })

  const run = async (nextPins = pins) => {
    setBusy(true); setError(null)
    try {
      const body = {
        project_id: projectId, allow_split: split,
        items: admitted.map((i) => ({ ...i, description: i.description.slice(0, 200), ...(nextPins[i.item_id] ? { pinned_wp: nextPins[i.item_id] } : {}) })),
        work_packages: wps.map((w) => ({
          wp_id: w.wp_id.trim(), name: w.name.trim(), min_share_pct: pctOrNull(w.min), target_share_pct: pctOrNull(w.target), max_share_pct: pctOrNull(w.max),
          allowed_categories: w.allowed.length ? w.allowed : null,
          category_max_share: Object.fromEntries(Object.entries(w.caps).filter(([, v]) => v !== '' && pctOrNull(v) !== null).map(([k, v]) => [k, pctOrNull(v)])),
        })),
      }
      setRes(await api.wpPlan(body))
    } catch (e) { setError(e.message); setRes(null) } finally { setBusy(false) }
  }
  const pin = (itemId, wp) => { const next = { ...pins, [itemId]: wp || undefined }; if (!wp) delete next[itemId]; setPins(next); run(next) }

  const csv = () => {
    const rows = [['voce', 'descrizione', 'categoria', 'importo ammesso (EUR)', 'WP', 'importo nel WP (EUR)']]
    res.assignments.forEach((a) => a.parts.forEach((p) => rows.push([a.item_id, a.description, CATEGORY_LABEL[a.category] || a.category, a.amount_eur, p.wp_id, p.amount_eur])))
    const cell = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`
    download(new Blob([String.fromCharCode(0xfeff) + rows.map((r) => r.map(cell).join(CSV_SEP)).join(CRLF)], { type: 'text/csv;charset=utf-8' }), `ripartizione-wp-${projectId || 'budget'}.csv`)
  }

  const ready = res && (res.status === 'OPTIMAL' || res.status === 'BEST_FOUND')
  return (
    <div className="card overflow-hidden">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center gap-2 px-4 py-3 text-left text-sm font-medium" aria-expanded={open}>
        <Layers className="w-4 h-4 text-brand-ink" />Pacchetti di lavoro (WP) — dividi il budget ammesso
        <span className="ml-auto text-xs text-mute font-normal">{wps.length ? `${wps.length} WP` : 'facoltativo'}</span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-4">
          <p className="text-xs text-ink-2 leading-relaxed">Molti bandi chiedono di dividere il progetto in pacchetti di lavoro. Indica quelli del tuo bando e i limiti che prevede (quota minima o massima del totale, categorie di spesa ammesse, tetto di una categoria dentro il WP):
            QUANTO assegna le voci <strong>ammesse</strong> ({admitted.length} voci, {fmtEur(total)}) in modo da rispettarli e, se indichi una quota desiderata, da avvicinarsi il più possibile. Se non esiste una ripartizione te lo dice e spiega perché. <Hint id="budget_wp" /></p>

          <div className="space-y-2">
            {wps.map((w, k) => (
              <div key={k} className="p-3 rounded-xl border border-line bg-field space-y-2 text-xs">
                <div className="flex flex-wrap items-end gap-2">
                  <label className="space-y-0.5"><span className="label">Sigla</span><input className="field !w-24 !py-1 font-mono" value={w.wp_id} onChange={(e) => set(k, { wp_id: e.target.value })} aria-label="Sigla del WP" /></label>
                  <label className="space-y-0.5 flex-1 min-w-[10rem]"><span className="label">Nome</span><input className="field !py-1" value={w.name} placeholder="es. Sviluppo" onChange={(e) => set(k, { name: e.target.value })} aria-label="Nome del WP" /></label>
                  {[['min', 'Minima %'], ['target', 'Desiderata %'], ['max', 'Massima %']].map(([key, label]) => (
                    <label key={key} className="space-y-0.5"><span className="label">{label}</span><input type="number" min="0" max="100" step="0.5" className="field !w-24 !py-1" value={w[key]} onChange={(e) => set(k, { [key]: e.target.value })} aria-label={`${label} del ${w.wp_id}`} /></label>
                  ))}
                  <button className="btn !py-1" onClick={() => setWps((cur) => cur.filter((_, i) => i !== k))} aria-label={`Elimina ${w.wp_id}`}><Trash2 className="w-3 h-3" /></button>
                </div>
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="text-mute">Categorie ammesse{w.allowed.length === 0 ? ' (tutte)' : ''}:</span>
                  {CATEGORY_ORDER.map((c) => <button key={c} onClick={() => toggle(k, c)} aria-pressed={w.allowed.includes(c)}
                    className={`px-2 py-0.5 rounded-full border ${w.allowed.includes(c) ? 'border-brand bg-brand/20 text-ink' : 'border-line text-ink-2 hover:border-line-strong'}`}>{CATEGORY_LABEL[c]}</button>)}
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-mute">Tetto dentro il WP (% del WP):</span>
                  {CATEGORY_ORDER.map((c) => (
                    <label key={c} className="flex items-center gap-1">{CATEGORY_LABEL[c]}
                      <input type="number" min="0" max="100" className="field !w-16 !py-0.5" value={w.caps[c] ?? ''} onChange={(e) => set(k, { caps: { ...w.caps, [c]: e.target.value } })} aria-label={`Tetto ${CATEGORY_LABEL[c]} nel ${w.wp_id}`} /></label>
                  ))}
                </div>
              </div>
            ))}
            <div className="flex flex-wrap items-center gap-2">
              <button className="btn" onClick={() => setWps((cur) => [...cur, blank(cur.length + 1)])}><Plus className="w-3.5 h-3.5" />Aggiungi un WP</button>
              {wps.length === 0 && <button className="btn" onClick={() => setWps(EXAMPLE.map((n, i) => ({ ...blank(i + 1), name: n })))}>Parti da una struttura d’esempio (4 WP, da modificare)</button>}
              <label className="inline-flex items-center gap-2 text-xs text-ink-2 ml-auto"><input type="checkbox" checked={split} onChange={(e) => setSplit(e.target.checked)} />Una voce può essere divisa tra più WP</label>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button className="btn-primary" disabled={busy || wps.length === 0 || admitted.length === 0} onClick={() => run()}>{busy && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Ripartisci le voci</button>
            {admitted.length === 0 && <span className="text-xs text-amber-700">Non ci sono voci ammesse da dividere: controlla prima il budget.</span>}
            {error && <span className="text-xs text-red-700">{error}</span>}
          </div>

          {res && (
            <div className="space-y-3">
              <div className={`p-3 rounded-xl border text-xs flex gap-2 ${ready ? (res.all_checks_ok ? 'border-emerald-500/30 bg-emerald-500/5 text-emerald-800' : 'border-amber-500/30 bg-amber-500/5 text-amber-800') : 'border-red-500/30 bg-red-500/5 text-red-700'}`}>
                {ready && res.all_checks_ok ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertTriangle className="w-4 h-4 shrink-0" />}
                <div className="space-y-1"><p className="font-medium">{res.message}</p>
                  {(res.notes || []).map((n) => <p key={n}>{n}</p>)}
                  {(res.reasons || []).map((r) => <p key={r}>• {r}</p>)}
                  {(res.unplaced || []).length > 0 && <p>Restano fuori: {res.unplaced.map((u) => `${u.description || u.item_id} (${fmtEur(u.unplaced_eur)})`).join('; ')}.</p>}</div>
              </div>
              {ready && (
                <>
                  <div className="grid md:grid-cols-2 gap-3">
                    {res.work_packages.map((w) => (
                      <div key={w.wp_id} className="p-3 rounded-xl border border-line bg-field text-xs space-y-1.5">
                        <div className="flex items-baseline gap-2"><span className="font-semibold text-ink">{w.wp_id}</span><span className="text-ink-2 truncate">{w.name}</span><span className="ml-auto font-mono font-semibold">{fmtEur(w.total_eur)}</span></div>
                        <div className="relative h-2 rounded-full bg-tint-2 overflow-hidden"><div className="h-full bg-brand" style={{ width: `${Math.min(100, w.share_pct)}%` }} />
                          {w.target_share_pct != null && <i className="absolute top-0 bottom-0 w-0.5 bg-ink" style={{ left: `${w.target_share_pct * 100}%` }} title="quota desiderata" />}</div>
                        <p className="text-mute">{w.share_pct.toLocaleString('it-IT')}% del budget ammesso · {w.items} {w.items === 1 ? 'voce' : 'voci'}{w.deviation_pp != null ? ` · desiderata ${(w.target_share_pct * 100).toLocaleString('it-IT')}% (${w.deviation_pp > 0 ? '+' : ''}${w.deviation_pp.toLocaleString('it-IT')} punti)` : ''}</p>
                        <p className="text-mute">{Object.entries(w.by_category).map(([c, v]) => `${CATEGORY_LABEL[c] || c} ${v.pct_of_wp.toLocaleString('it-IT')}%`).join(' · ') || 'vuoto'}</p>
                      </div>
                    ))}
                  </div>
                  <div className="p-3 rounded-xl border border-line space-y-1 text-xs">
                    <span className="label">Controlli sui vincoli</span>
                    {res.checks.map((c, i) => <p key={i} className="flex gap-1.5 items-start">{c.ok ? <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 text-emerald-600 shrink-0" /> : <XCircle className="w-3.5 h-3.5 mt-0.5 text-red-600 shrink-0" />}
                      <span><span className="font-medium">{c.wp_id || 'Budget'} · {c.rule}:</span> <span className="text-ink-2">{c.detail}</span></span></p>)}
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead><tr className="text-left text-mute"><th className="py-1 font-medium">Voce</th><th className="font-medium">Categoria</th><th className="font-medium text-right">Ammesso</th><th className="font-medium pl-3">WP</th><th className="font-medium pl-3">Sposta in</th></tr></thead>
                      <tbody>{res.assignments.map((a) => (
                        <tr key={a.item_id} className="border-t border-line">
                          <td className="py-1.5 pr-2"><span className="font-mono text-mute">{a.item_id}</span> {a.description}</td><td>{CATEGORY_LABEL[a.category] || a.category}</td><td className="text-right tabular-nums">{fmtEur(a.amount_eur)}</td>
                          <td className="pl-3">{a.parts.map((p) => `${p.wp_id}${a.parts.length > 1 ? ` ${fmtEur(p.amount_eur)}` : ''}`).join(' + ')}{a.pinned ? ' (scelto da te)' : ''}</td>
                          <td className="pl-3"><select className="field !py-0.5 !w-auto text-xs" value={pins[a.item_id] || ''} onChange={(e) => pin(a.item_id, e.target.value)} aria-label={`Sposta ${a.item_id}`}>
                            <option value="">automatico</option>{wps.map((w) => <option key={w.wp_id} value={w.wp_id.trim()}>{w.wp_id}</option>)}</select></td>
                        </tr>))}</tbody>
                    </table>
                  </div>
                  <button className="btn" onClick={csv}><Download className="w-3.5 h-3.5" />Scarica la ripartizione (CSV)</button>
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
