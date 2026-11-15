import React, { useEffect, useRef, useState } from 'react'

/* Ricostruzione minimale del portale dopo l'accesso, per la homepage: le quattro pagine degli agenti con le cifre dell'impresa di prova
   (Meridiana, interamente inventata, la stessa dei documenti di prova). Passa da una pagina all'altra da sola; si può anche scegliere.
   Non è uno screenshot: è disegnata nei colori del marchio, e lo dice. */
const reduced = () => typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches
const PAGES = ['Agevolazioni', 'Allocazione', 'Budget', 'Confronto']
const SAY = [
  ['Ho letto le assunzioni previste per il 2026.', 'Bonus Giovani per una persona: fino a 15.600 €.', 'Il mese di assunzione della seconda persona.'],
  ['Ho cercato tra tutti i bandi aperti e ne ho studiati 8.', '3 bandi adatti alle spese dell’anno, 3 a progetto.', 'Nulla: puoi preparare i budget.'],
  ['Ho scritto la bozza voce per voce e l’ho controllata.', '46 controlli superati, 2 voci da ridurre.', 'Il CUP del progetto, per due voci in attesa.'],
  ['Ho confrontato due bandi sullo stesso budget.', 'Il primo copre di più su beni e consulenze.', 'La scelta del cliente.'],
]

function Bar({ label, value, pct, tone = 'ink', on }) {
  return (
    <div className="pp-bar">
      <div className="pp-bar-top"><span>{label}</span><b>{value}</b></div>
      <div className="pp-bar-track"><i className={tone} style={{ width: on ? `${pct}%` : '0%' }} /></div>
    </div>
  )
}

const HEAT = 'OOOAOOOROOOOWOOOONOOOAOONOOOOOOAOOONOROOOOONOOOOWOOONOOAOOOO'.split('')

function Screen({ k, on }) {
  if (k === 0) return (
    <div className="pp-screen">
      <p className="pp-h">Chi assume l’impresa</p>
      {[['Persona 1', 'Under 35 · senza lavoro da 24 mesi · 2026', 'Bonus Giovani 2026', '650 € × 24 mesi', '15.600 €', true], ['Persona 2', 'Donna · over 35 · senza lavoro da 12 mesi', 'Bonus Donne 2026', 'manca il mese di assunzione', 'da verificare', false]].map(([p, d, m, how, v, ok], i) => (
        <div key={p} className="pp-row" style={{ transitionDelay: `${0.15 + i * 0.12}s` }}>
          <div><b>{p}</b><span>{d}</span></div>
          <div className="pp-arrow" />
          <div><b>{m}</b><span>{how}</span></div>
          <span className={`pp-val${ok ? '' : ' muted'}`}>{v}</span>
        </div>
      ))}
      <p className="pp-note">Una sola misura per persona, la più ricca tra quelle certe. Chi ha un dato mancante non si somma.</p>
    </div>
  )
  if (k === 1) return (
    <div className="pp-screen">
      <div className="pp-steps">{['L’azienda', 'Bandi adatti', 'Tutti insieme', 'Progetti'].map((s, i) => <span key={s} className={i === 1 ? 'on' : i === 0 ? 'done' : ''}>{s}</span>)}</div>
      <Bar label="Nuovo Piano Transizione 5.0 — Iperammortamento" value="119.284 €" pct={92} on={on} />
      <Bar label="Fondo 394/81 — SIMEST" value="29.065 €" pct={24} on={on} />
      <Bar label="Beni strumentali — Nuova Sabatini · a progetto" value="21.162 €" pct={18} tone="yellow" on={on} />
      <div className="pp-total"><span>Totale agevolato, spese dell’anno</span><b>163.949,41 €</b></div>
      <p className="pp-note">I bandi a progetto non si sommano alle spese dell’anno: si calcolano nella sezione Progetti.</p>
    </div>
  )
  if (k === 2) return (
    <div className="pp-screen">
      <p className="pp-h">Fondo 394/81 · 60 controlli per voce</p>
      <div className="pp-heat">{HEAT.map((c, i) => <i key={i} className={`h-${c}`} style={{ transitionDelay: `${i * 0.012}s` }} />)}</div>
      {[['Fiera internazionale, stand e trasferte', '18.400 €', 'ammessa'], ['Consulenza per l’export', '12.000 €', 'ridotta a 5.000 €'], ['Piattaforma e-commerce', '22.000 €', 'in attesa del CUP']].map(([v, a, e], i) => (
        <div key={v} className="pp-item" style={{ transitionDelay: `${0.3 + i * 0.1}s` }}><span>{v}</span><b>{a}</b><em className={i === 0 ? 'ok' : i === 1 ? 'warn' : 'wait'}>{e}</em></div>
      ))}
    </div>
  )
  return (
    <div className="pp-screen">
      <p className="pp-h">Stesso budget, due bandi</p>
      <div className="pp-compare">
        {[['Bando A', [['Beni', 78], ['Consulenze', 46], ['Personale', 30]], '64.210 €'], ['Bando B', [['Beni', 52], ['Consulenze', 18], ['Personale', 44]], '48.900 €']].map(([t, rows, tot], j) => (
          <div key={t}>
            <b className="pp-ct">{t}</b>
            {rows.map(([l, p]) => <Bar key={l} label={l} value="" pct={p} tone={j === 0 ? 'ink' : 'gray'} on={on} />)}
            <div className="pp-total small"><span>Copre</span><b>{tot}</b></div>
          </div>
        ))}
      </div>
      <p className="pp-note">Esempio illustrativo: il confronto usa lo stesso metodo e le stesse spese per entrambi i bandi.</p>
    </div>
  )
}

export default function PortalPreview() {
  const [k, setK] = useState(0)
  const [on, setOn] = useState(false)
  const hold = useRef(0)
  const root = useRef(null)
  useEffect(() => {
    if (reduced()) { setOn(true); return undefined }
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) setOn(true) }, { threshold: 0.3 })
    if (root.current) io.observe(root.current)
    const t = setInterval(() => { if (Date.now() - hold.current > 10000) setK((n) => (n + 1) % PAGES.length) }, 5200)
    return () => { io.disconnect(); clearInterval(t) }
  }, [])
  const [did, found, need] = SAY[k]
  return (
    <div className={`pp${on ? ' on' : ''}`} ref={root}>
      <div className="pp-window" aria-label="Ricostruzione del portale QUANTO">
        <div className="pp-top"><i /><i /><i /><span>quanto · impresa di prova</span></div>
        <div className="pp-body">
          <aside className="pp-side">
            <span className="pp-brand">quanto</span>
            <span className="pp-work">Meridiana · ATECO 62.01</span>
            {PAGES.map((p, i) => <button key={p} type="button" className={i === k ? 'on' : ''} onClick={() => { hold.current = Date.now(); setK(i) }}><span>{i + 1}</span>{p}</button>)}
          </aside>
          <main className="pp-main">
            <div className="pp-agent" key={`a${k}`}>
              <p><span>Ho fatto</span>{did}</p>
              <p><span>Ho trovato</span>{found}</p>
              <p><span>Mi serve da te</span>{need}</p>
            </div>
            <div className="pp-stage" key={k}><Screen k={k} on={on} /></div>
          </main>
        </div>
      </div>
      <p className="pp-caption">Ricostruzione del portale: impresa di prova inventata, cifre illustrative.</p>
    </div>
  )
}
