import React, { useCallback, useEffect, useState } from 'react'
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronRight, Loader2, Plus, ShieldCheck, Trash2 } from 'lucide-react'
import { api } from '../lib/api'
import TutorialVideo from './TutorialVideo'
import { fmtEur } from '../lib/format'

const STATE = {
  VERIFICATO: ['Verificato sul registro', 'border-emerald-500/30 text-emerald-700 bg-emerald-500/5'],
  NON_VERIFICATO: ['Non verificato', 'border-amber-500/30 text-amber-700 bg-amber-500/5'],
  SCADUTO: ['Visura scaduta', 'border-amber-500/30 text-amber-700 bg-amber-500/5'],
  DISCORDANZA: ['Differenze da spiegare', 'border-red-500/30 text-red-700 bg-red-500/5'],
}
const EMPTY = { granted: '', entity: '', measure: '', regime: 'de minimis', amount_eur: '', cor: '' }

/** Aiuti già ricevuti, impresa unica e visura aiuti del Registro Nazionale degli Aiuti: la verifica che il de minimis richiede, fatta e documentata. */
export default function AidsPanel() {
  const [open, setOpen] = useState(false)
  const [st, setSt] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(null)
  const [answers, setAnswers] = useState({})
  const [companies, setCompanies] = useState([])
  const [drafts, setDrafts] = useState({})                  // per impresa: { checked_at, rows }
  const [note, setNote] = useState('')

  const apply = useCallback((s) => {
    setSt(s)
    setAnswers(s.group.answers || {})
    setCompanies(s.group.companies || [])
    const d = {}
    s.companies.forEach((c) => { d[c.cf] = { checked_at: s.checks[c.cf]?.checked_at || '', rows: s.entries.filter((e) => e.company === c.cf && e.source === 'RNA').map((e) => ({ ...e, amount_eur: String(e.amount_eur) })) } })
    setDrafts(d)
  }, [])
  useEffect(() => { if (open && !st) api.profileAids().then(apply).catch((e) => setError(e.message)) }, [open, st, apply])

  const run = async (key, fn) => { setBusy(key); setError(null); try { apply(await fn()) } catch (e) { setError(e.message) } finally { setBusy(null) } }
  const setRow = (cf, i, k, v) => setDrafts((d) => ({ ...d, [cf]: { ...d[cf], rows: d[cf].rows.map((r, j) => (j === i ? { ...r, [k]: v } : r)) } }))
  const [label, tone] = st ? STATE[st.status] : []

  return (
    <div className="card">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center gap-2 px-4 py-3 text-left text-sm font-medium">
        {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}<ShieldCheck className="w-4 h-4 text-brand-ink" />Aiuti ricevuti, impresa unica e registro nazionale
        {st && <span className={`ml-auto px-2 py-0.5 rounded border text-[11px] font-medium ${tone}`}>{label}</span>}
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-4 text-xs">
          <TutorialVideo id="T11" />
          <p className="text-ink-2 leading-relaxed">Il de minimis (300.000 € in tre anni) vale per l’<strong className="text-ink">impresa unica</strong>: l’azienda più quelle che le sono collegate. QUANTO non può leggere il Registro Nazionale degli Aiuti (RNA) da solo: serve la <strong className="text-ink">visura aiuti</strong> ufficiale, scaricata dall’impresa o da un suo delegato. Qui si riportano le concessioni e si confrontano con i documenti; finché la verifica non è completa e recente (30 giorni) il piano usa un residuo ridotto di un margine di sicurezza.</p>
          {error && <p className="text-red-700">{error}</p>}
          {!st && !error && <p className="text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Carico…</p>}
          {st && (
            <>
              <div className={`p-3 rounded-xl border space-y-1 ${tone}`}>
                <div className="flex flex-wrap items-end gap-x-8 gap-y-1">
                  <div><span className="label">Aiuti de minimis nel triennio</span><div className="text-base font-semibold tabular-nums text-ink">{fmtEur(st.received_eur)}</div></div>
                  <div><span className="label">Residuo</span><div className="text-base font-semibold tabular-nums text-ink">{fmtEur(st.residual_eur)}</div></div>
                  <div><span className="label">Che il piano può usare</span><div className="text-base font-semibold tabular-nums text-ink">{fmtEur(st.usable_residual_eur)}</div></div>
                </div>
                <p className="text-ink-2 leading-relaxed">{st.message}</p>
                {st.problems.map((p) => <p key={p} className="text-ink-2 flex gap-1.5"><AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0 text-amber-600" />{p}</p>)}
              </div>

              <div className="space-y-2">
                <p className="font-medium text-ink">1. Impresa unica: l’azienda ha legami con altre imprese?</p>
                {st.suggested_answers && Object.keys(answers).length === 0 && (
                  <p className="p-2 rounded-lg border border-emerald-500/30 bg-emerald-500/5 text-ink-2 leading-relaxed">
                    Nella dichiarazione sostitutiva caricata l’impresa dichiara di non essere collegata ad altre. Puoi usarla come risposta di partenza: resta una tua verifica, non viene applicata da sola.{' '}
                    <button className="underline text-ink" onClick={() => setAnswers({ ...st.suggested_answers })}>Usa «No» a tutte le domande</button>
                  </p>
                )}
                {Object.entries(st.questions).map(([k, q]) => (
                  <div key={k} className="flex flex-wrap items-start gap-2">
                    <span className="flex-1 min-w-[16rem] text-ink-2 leading-relaxed">{k}) {q}</span>
                    <select className="field !w-auto !py-1" aria-label={`Domanda ${k}`} value={answers[k] || ''} onChange={(e) => setAnswers({ ...answers, [k]: e.target.value })}>
                      <option value="">— rispondi —</option><option value="no">No</option><option value="si">Sì</option><option value="non_so">Non so</option></select>
                  </div>
                ))}
                {Object.values(answers).includes('si') && (
                  <div className="space-y-1.5 pl-3 border-l-2 border-line">
                    <p className="text-ink-2">Imprese collegate (serve il codice fiscale o la partita IVA: anche per loro serve la visura aiuti):</p>
                    {companies.map((c, i) => (
                      <div key={i} className="flex flex-wrap gap-2">
                        <input className="field !py-1 !w-44" placeholder="Codice fiscale o P. IVA" value={c.cf} onChange={(e) => setCompanies(companies.map((x, j) => (j === i ? { ...x, cf: e.target.value } : x)))} />
                        <input className="field !py-1 !w-48" placeholder="Nome" value={c.name} onChange={(e) => setCompanies(companies.map((x, j) => (j === i ? { ...x, name: e.target.value } : x)))} />
                        <input className="field !py-1 flex-1 min-w-[10rem]" placeholder="Che legame (es. controllata al 60%)" value={c.relation} onChange={(e) => setCompanies(companies.map((x, j) => (j === i ? { ...x, relation: e.target.value } : x)))} />
                        <button className="btn !py-1" onClick={() => setCompanies(companies.filter((_, j) => j !== i))} aria-label="Togli l’impresa"><Trash2 className="w-3 h-3" /></button>
                      </div>
                    ))}
                    <button className="btn !py-1" onClick={() => setCompanies([...companies, { cf: '', name: '', relation: '' }])}><Plus className="w-3 h-3" />Aggiungi un’impresa</button>
                  </div>
                )}
                <button className="btn-primary" disabled={busy === 'group'} onClick={() => run('group', () => api.saveAidsGroup(answers, companies.filter((c) => c.cf)))}>{busy === 'group' && <Loader2 className="w-3.5 h-3.5 animate-spin" />}Salva l’impresa unica</button>
              </div>

              <div className="space-y-3">
                <p className="font-medium text-ink">2. Visura aiuti dell’RNA, impresa per impresa</p>
                {st.companies.map((c) => {
                  const d = drafts[c.cf] || { checked_at: '', rows: [] }
                  return (
                    <div key={c.cf} className="p-3 rounded-xl border border-line bg-field space-y-2">
                      <div className="flex flex-wrap items-center gap-3">
                        <span className="font-medium text-ink">{c.cf === 'SELF' ? 'La tua azienda' : `${c.name || c.cf} (${c.cf})`}</span>
                        <label className="flex items-center gap-2 text-ink-2 ml-auto">Visura consultata il<input type="date" className="field !py-1 !w-40" value={d.checked_at} onChange={(e) => setDrafts({ ...drafts, [c.cf]: { ...d, checked_at: e.target.value } })} /></label>
                      </div>
                      {d.rows.length > 0 && (
                        <div className="overflow-x-auto"><table className="w-full"><thead><tr className="text-left text-mute"><th className="font-medium py-1">Concessione</th><th className="font-medium">Ente</th><th className="font-medium">Misura</th><th className="font-medium">Regime</th><th className="font-medium text-right">Importo</th><th className="font-medium pl-2">COR</th><th /></tr></thead>
                          <tbody>{d.rows.map((r, i) => (
                            <tr key={i} className="border-t border-line">
                              <td className="py-1"><input type="date" className="field !py-1 !w-36" value={r.granted} onChange={(e) => setRow(c.cf, i, 'granted', e.target.value)} /></td>
                              <td><input className="field !py-1 !w-36" value={r.entity} onChange={(e) => setRow(c.cf, i, 'entity', e.target.value)} /></td>
                              <td><input className="field !py-1 !w-44" value={r.measure} onChange={(e) => setRow(c.cf, i, 'measure', e.target.value)} /></td>
                              <td><select className="field !py-1 !w-28" value={r.regime} onChange={(e) => setRow(c.cf, i, 'regime', e.target.value)}><option>de minimis</option><option>altro</option></select></td>
                              <td><input type="number" min="0" step="0.01" className="field !py-1 !w-28 text-right" value={r.amount_eur} onChange={(e) => setRow(c.cf, i, 'amount_eur', e.target.value)} /></td>
                              <td className="pl-2"><input className="field !py-1 !w-32 font-mono" value={r.cor || ''} onChange={(e) => setRow(c.cf, i, 'cor', e.target.value)} /></td>
                              <td><button className="btn !py-1" onClick={() => setDrafts({ ...drafts, [c.cf]: { ...d, rows: d.rows.filter((_, j) => j !== i) } })} aria-label="Togli la riga"><Trash2 className="w-3 h-3" /></button></td></tr>))}</tbody></table></div>
                      )}
                      <div className="flex flex-wrap gap-2">
                        <button className="btn !py-1" onClick={() => setDrafts({ ...drafts, [c.cf]: { ...d, rows: [...d.rows, { ...EMPTY }] } })}><Plus className="w-3 h-3" />Aggiungi una concessione</button>
                        <button className="btn-primary !py-1" disabled={busy === c.cf || !d.checked_at} onClick={() => run(c.cf, () => api.saveAidsEntries(c.cf, 'RNA', d.rows.filter((r) => r.granted && r.amount_eur), d.checked_at))}>{busy === c.cf && <Loader2 className="w-3 h-3 animate-spin" />}Salva la visura</button>
                        {!d.rows.length && d.checked_at && <span className="text-mute self-center">Nessuna concessione: se la visura è vuota, salvala così.</span>}
                      </div>
                    </div>
                  )
                })}
              </div>

              <div className="space-y-1.5">
                <p className="font-medium text-ink">3. Confronto con i documenti</p>
                {st.declared_in_documents.length === 0 && <p className="text-mute">Nei documenti caricati non c’è un registro degli aiuti da confrontare.</p>}
                {st.declared_in_documents.length > 0 && <p className="text-ink-2">Dichiarati nei documenti: {st.declared_in_documents.map((d) => `${d.granted} · ${d.measure || d.entity} · ${fmtEur(d.amount_eur)}`).join('; ')}.</p>}
                {st.differences.map((d) => <p key={d} className="text-red-700 flex gap-1.5"><AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />{d}</p>)}
                {st.differences.length === 0 && st.checks.SELF && st.declared_in_documents.length > 0 && <p className="text-emerald-700 flex gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 mt-0.5 shrink-0" />La visura e i documenti dicono la stessa cosa.</p>}
              </div>

              <div className="space-y-1.5">
                <p className="font-medium text-ink">4. Conferma</p>
                <p className="text-ink-2 leading-relaxed">Chi ha fatto la verifica la attesta: resta nel registro delle operazioni, con la data. Non sostituisce la dichiarazione firmata dal legale rappresentante.</p>
                <div className="flex flex-wrap gap-2"><input className="field !py-1 flex-1 min-w-[14rem]" placeholder="Nota (facoltativa)" value={note} onChange={(e) => setNote(e.target.value)} />
                  <button className="btn" disabled={busy === 'confirm'} onClick={() => run('confirm', () => api.confirmAids(note))}>{busy === 'confirm' && <Loader2 className="w-3 h-3 animate-spin" />}Attesto la verifica</button></div>
                {st.confirmations.length > 0 && <p className="text-[11px] text-mute">Ultima conferma: {st.confirmations[st.confirmations.length - 1].at.slice(0, 10)} · {st.confirmations[st.confirmations.length - 1].by} · {STATE[st.confirmations[st.confirmations.length - 1].status]?.[0]}.</p>}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
