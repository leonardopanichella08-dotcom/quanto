import React, { useEffect, useMemo, useRef, useState } from 'react'
import { ArrowRight, ChevronLeft, ChevronRight, Plus, X } from 'lucide-react'
import { api } from '../lib/api'
import { Term } from './Help'

const DEFAULT_ROWS = ['Stipendio Rossi — 26.282,70 €', 'Server GPU — 12.000,00 €', 'Consulenza audit — 17.500,00 €', 'Affitto sede — 4.800,00 €']
const MAX_ROWS = 12
const short = (h, n = 6) => (h ? h.slice(0, n) : '')

/** +1 all'ultima cifra della riga (o “1” in coda se non ci sono cifre): la più piccola modifica possibile. */
function bump(text) {
  const m = [...text.matchAll(/\d/g)].pop()
  if (!m) return `${text}1`
  const d = (Number(m[0]) + 1) % 10
  return text.slice(0, m.index) + d + text.slice(m.index + 1)
}

function Chip({ h, tone = 'neutral', title }) {
  const c = { neutral: 'text-ink-2 border-line-strong', lime: 'text-brand-ink border-brand/40', sky: 'text-sky-700 border-sky-500/40', red: 'text-red-700 border-red-500/50 bg-red-500/10', dim: 'text-mute border-line' }[tone]
  return <span title={title || h} className={`inline-block font-mono text-[11px] px-1.5 py-0.5 rounded border ${c}`}>{short(h)}…</span>
}

/** Albero: mostra solo i livelli già "costruiti" dal passo corrente; evidenzia coppie, percorso della prova o nodi cambiati. */
function Tree({ levels, upTo, mark }) {
  const n = levels[0].length
  const gap = 66, top = 18, lvH = 54, nodeW = 54, nodeH = 20
  const W = Math.max(320, n * gap + 20), H = top + levels.length * lvH + 26
  const xs = [levels[0].map((_, i) => 12 + nodeW / 2 + i * gap)]
  for (let k = 1; k < levels.length; k += 1) {
    xs.push(levels[k].map((_, j) => { const a = xs[k - 1][2 * j], b = xs[k - 1][2 * j + 1]; return b === undefined ? a : (a + b) / 2 }))
  }
  const y = (k) => H - 26 - nodeH - k * lvH
  const kindOf = (k, j) => mark?.(k, j) || 'neutral'
  const fill = { neutral: 'rgba(255,255,255,0.85)', lime: '#f1e21b', sky: '#e0f2fe', red: '#fee2e2', pair: 'rgba(21,21,15,0.08)' }
  const text = { neutral: '#45453d', lime: '#15150f', sky: '#075985', red: '#991b1b', pair: '#15150f' }
  return (
    <div className="overflow-x-auto">
      <svg width={W} height={H} role="img" aria-label="Albero di Merkle">
        {levels.map((lvl, k) => k > 0 && k <= upTo && lvl.map((_, j) => [2 * j, 2 * j + 1].map((c) => (
          xs[k - 1][c] !== undefined && <line key={`${k}-${j}-${c}`} x1={xs[k - 1][c]} y1={y(k - 1)} x2={xs[k][j]} y2={y(k) + nodeH} stroke="rgba(21,21,15,0.28)" />
        ))))}
        {levels.map((lvl, k) => k <= upTo && lvl.map((h, j) => {
          const kind = kindOf(k, j)
          return (
            <g key={`${k}-${j}`}>
              <rect x={xs[k][j] - nodeW / 2} y={y(k)} width={nodeW} height={nodeH} rx="4" fill={fill[kind]} stroke={kind === 'neutral' ? 'rgba(21,21,15,0.16)' : 'none'} />
              <text x={xs[k][j]} y={y(k) + 14} fontSize="10" fontFamily="monospace" textAnchor="middle" fill={text[kind]}>{short(h)}</text>
            </g>
          )
        }))}
        {upTo >= 0 && levels[0].map((_, j) => (
          <text key={j} x={xs[0][j]} y={y(0) + nodeH + 14} fontSize="10" textAnchor="middle" fill="#6c6c62">riga {j + 1}</text>
        ))}
      </svg>
    </div>
  )
}

export default function MerkleLab() {
  const [rows, setRows] = useState(DEFAULT_ROWS)
  const [data, setData] = useState(null)
  const [tamper, setTamper] = useState(null)
  const [step, setStep] = useState(0)
  const [proofIdx, setProofIdx] = useState(0)
  const [error, setError] = useState(null)
  const seq = useRef(0)

  const valid = rows.length >= 1 && rows.every((r) => r.trim() && r.length <= 200)
  const tampered = useMemo(() => rows.map((r, i) => (i === 0 ? bump(r) : r)), [rows])
  const pIdx = Math.min(proofIdx, rows.length - 1)

  useEffect(() => {
    if (!valid) return undefined
    const mine = ++seq.current
    const t = setTimeout(async () => {
      try {
        const [a, b] = await Promise.all([api.merkleLab(rows, pIdx), api.merkleLab(tampered)])
        if (mine === seq.current) { setData(a); setTamper(b); setError(null) }
      } catch (e) { if (mine === seq.current) setError(e.message) }
    }, 250)
    return () => clearTimeout(t)
  }, [rows, tampered, pIdx, valid])

  const rounds = data?.rounds || []
  const steps = useMemo(() => [
    { id: 'rows', title: 'Le righe' },
    { id: 'hash', title: 'Un’impronta per riga' },
    { id: 'leaf', title: 'Le foglie' },
    ...rounds.map((r, k) => ({ id: `round${k}`, k, title: k === rounds.length - 1 ? 'Ultima unione' : `Si uniscono a coppie${rounds.length > 2 ? ` (${k + 1}ª volta)` : ''}` })),
    { id: 'root', title: 'La radice' },
    { id: 'proof', title: 'Prova di una riga' },
    { id: 'tamper', title: 'E se cambio 1 €?' },
  ], [rounds])
  const cur = steps[Math.min(step, steps.length - 1)]
  const go = (d) => setStep((s) => Math.max(0, Math.min(steps.length - 1, s + d)))

  const changedLevels = useMemo(() => (data && tamper ? data.levels.map((lvl, k) => new Set(lvl.map((h, j) => (tamper.levels[k]?.[j] !== h ? j : -1)).filter((j) => j >= 0))) : []), [data, tamper])

  // quanto dell'albero è visibile in questo passo
  const upTo = !data ? -1 : cur.id === 'rows' || cur.id === 'hash' ? -1 : cur.id === 'leaf' ? 0 : cur.id.startsWith('round') ? cur.k + 1 : data.levels.length - 1
  // percorso della prova: antenati della riga scelta (lime) e loro vicini (azzurro)
  const proofNodes = useMemo(() => {
    if (!data?.proof) return null
    const m = new Map()
    let idx = data.proof.index
    data.levels.forEach((lvl, k) => {
      m.set(`${k}:${idx}`, 'lime')
      const sib = idx % 2 === 0 ? idx + 1 : idx - 1
      if (k < data.levels.length - 1 && sib < lvl.length) m.set(`${k}:${sib}`, 'sky')
      idx = Math.floor(idx / 2)
    })
    return m
  }, [data])
  const mark = (k, j) => {
    if (!data) return 'neutral'
    if (cur.id.startsWith('round') && k === cur.k + 1) return 'pair'
    if (cur.id === 'root' && k === data.levels.length - 1) return 'lime'
    if (cur.id === 'proof') return proofNodes?.get(`${k}:${j}`) || 'neutral'
    if (cur.id === 'tamper' && changedLevels[k]?.has(j)) return 'red'
    return 'neutral'
  }

  const setRow = (i, v) => setRows((r) => r.map((x, k) => (k === i ? v : x)))

  return (
    <div className="space-y-5">
      {/* barra dei passi */}
      <div className="flex flex-wrap items-center gap-2">
        <button type="button" onClick={() => go(-1)} disabled={step === 0} aria-label="Passo precedente" className="btn !px-2"><ChevronLeft className="w-4 h-4" /></button>
        <div className="flex flex-wrap items-center gap-1.5 flex-1 min-w-0">
          {steps.map((s, i) => (
            <button key={s.id} type="button" onClick={() => setStep(i)} aria-label={`Passo ${i + 1}: ${s.title}`} title={s.title}
              className={`h-2.5 rounded-full transition-all ${i === step ? 'w-8 bg-liquid' : i < step ? 'w-2.5 bg-ink/40' : 'w-2.5 bg-tint-2 hover:bg-ink/15'}`} />
          ))}
        </div>
        <button type="button" onClick={() => go(1)} disabled={step >= steps.length - 1} aria-label="Passo successivo" className="btn !px-2"><ChevronRight className="w-4 h-4" /></button>
      </div>
      <p className="text-xs text-mute">Passo {Math.min(step, steps.length - 1) + 1} di {steps.length} · <span className="text-ink-2">{cur.title}</span></p>

      {error && <p className="text-xs text-red-700">{error}</p>}

      {data && upTo >= 0 && (
        <div className="card !bg-field p-3">
          <Tree levels={data.levels} upTo={upTo} mark={mark} />
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-6">
        {/* spiegazione a parole */}
        <div className="space-y-3 text-sm text-ink-2 leading-relaxed">
          {cur.id === 'rows' && (<>
            <p>Immagina di dover dimostrare che un elenco di spese <strong className="text-ink">non è stato toccato</strong>, senza dover rimandare l’elenco intero ogni volta.</p>
            <p>L’idea della <Term id="merkle">Merkle Root</Term>: ridurre tutto a <strong className="text-ink">un’unica impronta</strong> da 64 caratteri. Se cambia una sola cifra di una sola riga, l’impronta cambia.</p>
            <p className="text-xs text-ink-2">A destra ci sono quattro righe d’esempio: <strong>scrivici sopra</strong> o aggiungine (fino a {MAX_ROWS}) e guarda tutto ricalcolarsi. I calcoli li fa il vero motore di QUANTO.</p>
          </>)}
          {cur.id === 'hash' && (<>
            <p>Ogni riga passa in una funzione (SHA-256) che produce una <Term id="hash">impronta</Term> di 64 caratteri.</p>
            <ul className="list-disc pl-5 space-y-1 text-xs text-ink-2">
              <li>Stesso testo → sempre la stessa impronta.</li>
              <li>Una lettera o una cifra diversa → impronta <strong className="text-ink">totalmente</strong> diversa.</li>
              <li>Dall’impronta <strong className="text-ink">non</strong> si ricostruisce il testo.</li>
            </ul>
            <p className="text-xs text-ink-2">Prova: torna al passo 1, cambia “26.282,70” in “26.282,71” e guarda come cambia questa colonna.</p>
          </>)}
          {cur.id === 'leaf' && (<>
            <p>Ogni impronta di riga diventa una <strong className="text-ink">foglia</strong> dell’albero. Prima di unirle, ne rifacciamo l’impronta con davanti l’etichetta <code className="text-brand-ink">00</code> (“sono una foglia”).</p>
            <p className="text-xs text-ink-2">Perché? Le unioni useranno l’etichetta <code>01</code>. Così un punto intermedio dell’albero non può essere spacciato per una riga vera: è una difesa standard (RFC 6962).</p>
          </>)}
          {cur.id.startsWith('round') && (<>
            <p>Si prendono i valori <strong className="text-ink">a coppie</strong>: il 1° con il 2°, il 3° con il 4°… Per ogni coppia si rifà l’impronta dei due insieme (con etichetta <code className="text-brand-ink">01</code>). Ogni coppia dà <strong className="text-ink">un</strong> valore nuovo, quindi ne restano la metà.</p>
            <p className="text-xs text-ink-2">I due valori si mettono in ordine prima di unirli: chi sta a sinistra o a destra non cambia il risultato.</p>
            {rounds[cur.k]?.pairs.some((p) => p.kind === 'promote') && <p className="text-xs text-amber-700">Uno resta senza compagno: <strong>sale così com’è</strong> al livello dopo. Non lo duplichiamo: duplicarlo permetterebbe di aggiungere righe finte senza cambiare la radice.</p>}
          </>)}
          {cur.id === 'root' && (<>
            <p>Quando ne resta <strong className="text-ink">uno solo</strong>, quella è la Merkle Root: l’impronta di tutto il budget. Sempre 64 caratteri, che le righe siano 4 o 4.000.</p>
            <p className="text-xs text-ink-2">È l’unica cosa che QUANTO scrive nel <Term id="registro">registro</Term>: nessuna cifra, nessun nome. Chi ha il budget può ricalcolarla e confrontarla.</p>
          </>)}
          {cur.id === 'proof' && (<>
            <p>Come dimostrare che <strong className="text-ink">una riga</strong> è nel budget senza mostrare le altre? Basta dare a chi controlla i “vicini” lungo la strada verso la cima (in azzurro).</p>
            <p className="text-xs text-ink-2">Chi controlla rifà le unioni una per una: se arriva alla stessa radice, la riga c’era. Servono solo <strong className="text-ink">{data?.proof?.steps.length ?? '…'}</strong> impronte invece di tutte le {rows.length} righe.</p>
            <label className="text-xs text-ink-2 flex items-center gap-2">Riga da dimostrare
              <select value={pIdx} onChange={(e) => setProofIdx(Number(e.target.value))} className="field !w-auto max-w-full">
                {rows.map((r, i) => <option key={i} value={i}>{i + 1}. {r.slice(0, 32)}</option>)}
              </select>
            </label>
          </>)}
          {cur.id === 'tamper' && (<>
            <p>Ora cambiamo <strong className="text-ink">la più piccola cosa possibile</strong>: l’ultima cifra della riga 1 (+1). Ecco cosa succede lungo la strada verso la radice (in rosso):</p>
            <p className="text-xs text-ink-2">Le altre righe restano uguali, ma la radice è <strong className="text-red-700">completamente diversa</strong>. Chi controlla se ne accorge subito: è ciò che fa la pagina <em>Verifica</em>.</p>
          </>)}
          <div className="flex gap-2 pt-1">
            <button type="button" onClick={() => go(-1)} disabled={step === 0} className="btn"><ChevronLeft className="w-3.5 h-3.5" />Indietro</button>
            <button type="button" onClick={() => go(1)} disabled={step >= steps.length - 1} className="btn-primary inline-flex items-center gap-1.5">Avanti<ArrowRight className="w-3.5 h-3.5" /></button>
          </div>
        </div>

        {/* i numeri veri del passo */}
        <div className="space-y-2 min-w-0">
          {cur.id === 'rows' && (
            <div className="space-y-2">
              {rows.map((r, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="text-xs text-mute w-12 shrink-0">riga {i + 1}</span>
                  <input value={r} maxLength={200} onChange={(e) => setRow(i, e.target.value)} className="field min-w-0" aria-label={`Riga ${i + 1}`} />
                  <button type="button" onClick={() => setRows(rows.filter((_, k) => k !== i))} disabled={rows.length <= 1} aria-label={`Rimuovi riga ${i + 1}`} className="text-mute hover:text-red-700 disabled:opacity-30"><X className="w-4 h-4" /></button>
                </div>
              ))}
              <button type="button" onClick={() => setRows([...rows, `Nuova spesa ${rows.length + 1} — 1.000,00 €`])} disabled={rows.length >= MAX_ROWS} className="btn"><Plus className="w-3.5 h-3.5" />Aggiungi riga</button>
              {!valid && <p className="text-xs text-amber-700">Ogni riga deve contenere del testo.</p>}
            </div>
          )}
          {data && cur.id === 'hash' && (
            <div className="space-y-1.5">
              {rows.map((r, i) => (
                <div key={i} className="text-xs flex items-center gap-2 min-w-0">
                  <span className="text-ink-2 truncate w-2/5 shrink-0" title={r}>{r}</span><ArrowRight className="w-3 h-3 text-mute shrink-0" />
                  <span className="font-mono text-brand-ink truncate" title={data.row_hashes[i]}>{data.row_hashes[i]}</span>
                </div>
              ))}
            </div>
          )}
          {data && cur.id === 'leaf' && (
            <div className="space-y-1.5">
              {rows.map((_, i) => (
                <div key={i} className="text-xs flex flex-wrap items-center gap-2">
                  <span className="text-mute w-12">riga {i + 1}</span><Chip h={data.row_hashes[i]} tone="dim" /><span className="text-mute">00 +</span>
                  <ArrowRight className="w-3 h-3 text-mute" /><Chip h={data.leaves[i]} title={data.leaves[i]} tone="neutral" />
                </div>
              ))}
              <p className="text-[11px] text-mute pt-1">Ogni casella mostra i primi 6 caratteri; passa il mouse per vederla intera.</p>
            </div>
          )}
          {data && cur.id.startsWith('round') && (
            <div className="space-y-2">
              {rounds[cur.k].pairs.map((p, i) => (
                <div key={i} className="text-xs flex flex-wrap items-center gap-1.5">
                  {p.kind === 'combine' ? (<>
                    <Chip h={p.left} /><span className="text-mute">+</span><Chip h={p.right} /><span className="text-mute">01 →</span><Chip h={p.result} tone="lime" />
                    {p.swapped && <span className="text-[11px] text-mute">(messi in ordine)</span>}
                  </>) : (<>
                    <Chip h={p.left} /><span className="text-mute">senza compagno → sale invariato</span><Chip h={p.result} tone="lime" />
                  </>)}
                </div>
              ))}
              <p className="text-[11px] text-mute">{data.levels[cur.k].length} valori → {rounds[cur.k].size_after}</p>
            </div>
          )}
          {data && cur.id === 'root' && (
            <div className="space-y-2">
              <p className="text-xs text-ink-2">Merkle Root ({data.root.length} caratteri)</p>
              <p className="font-code text-xs text-brand-ink break-all p-3 bg-field border border-line rounded-lg">{data.root}</p>
              <p className="text-[11px] text-mute">In QUANTO viene mostrata con il prefisso <span className="font-mono">0x</span> e il codice CEP è formato dalle sue prime 16 lettere.</p>
            </div>
          )}
          {data?.proof && cur.id === 'proof' && (
            <div className="space-y-2 text-xs">
              <div className="flex flex-wrap items-center gap-1.5"><span className="text-ink-2">Parti dalla foglia</span><Chip h={data.leaves[data.proof.index]} tone="lime" /></div>
              {data.proof.steps.map((s, i) => (
                <div key={i} className="flex flex-wrap items-center gap-1.5">
                  <span className="text-mute">+ vicino {s.position === 'left' ? 'a sinistra' : 'a destra'}</span><Chip h={s.sibling} tone="sky" /><ArrowRight className="w-3 h-3 text-mute" /><Chip h={s.result} tone={i === data.proof.steps.length - 1 ? 'lime' : 'neutral'} />
                </div>
              ))}
              <p className={data.proof.verified ? 'text-emerald-700' : 'text-red-700'}>{data.proof.verified ? '✓ Arrivi alla radice: la riga c’era.' : '✗ Non arrivi alla radice.'}</p>
            </div>
          )}
          {data && tamper && cur.id === 'tamper' && (
            <div className="space-y-2 text-xs">
              <div><p className="text-mute">Riga 1 prima → dopo</p><p className="text-ink-2 break-words">{rows[0]} → <span className="text-red-700">{tampered[0]}</span></p></div>
              <div><p className="text-mute">Radice prima</p><p className="font-code text-brand-ink break-all">{data.root}</p></div>
              <div><p className="text-mute">Radice dopo</p><p className="font-code text-red-700 break-all">{tamper.root}</p></div>
              <p className="text-ink-2">Nodi cambiati: <strong className="text-red-700">{changedLevels.reduce((s, x) => s + x.size, 0)}</strong> su {data.levels.reduce((s, l) => s + l.length, 0)} — solo la strada dalla riga 1 alla radice.</p>
            </div>
          )}
        </div>
      </div>

      <p className="text-[11px] text-mute leading-relaxed border-t border-line pt-3">
        Nota di onestà: qui l’impronta di ogni riga è calcolata sul testo che scrivi. Nel budget vero è calcolata sulla riga già controllata (importi, documenti, regola usata, risultato); tutto il resto — etichette 00/01, ordine, nodo dispari che sale, radice — è identico.
      </p>
    </div>
  )
}
