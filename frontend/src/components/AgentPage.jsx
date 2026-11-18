import React, { useEffect, useRef, useState } from 'react'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { Wordmark } from './ui'
import './AgentPage.css'

/* La pagina di un agente: come lavora davvero, passo per passo. I contenuti vengono dal documento degli agenti (docs/agenti/I_tre_agenti.md)
   e dal codice (measures.py, allocation_engine.py, deterministic_engine.py, templates): gli esempi sono «numeri di scuola» dichiarati come tali.
   I video sono quelli del portale (tutorial), in loop e senza controlli. */
export const AGENT_PAGES = {
  fiuto: {
    name: 'Fiuto', role: 'Agevolazioni', n: 1, img: '/landing/mascotte-fiuto.webp',
    line: 'Trova le agevolazioni che spettano all’impresa: esoneri sulle assunzioni, crediti d’imposta, incentivi.',
    video: 'tutorial-t02', videoNote: 'Il profilo: i documenti dell’impresa diventano dati, ognuno con la sua fonte.',
    steps: [
      ['Legge l’impresa', 'Tipo di impresa, regione, dipendenti, DURC: dai documenti già caricati. Se un dato manca lo chiede, non lo indovina.'],
      ['Controlla le misure', '13 misure in 6 famiglie, ognuna con la fonte e il grado di verifica. Ogni misura esce applicabile, da verificare, non applicabile o scaduta.'],
      ['Calcola quanto vale', 'Tetto mensile per mesi, per una assunzione, al massimo. È un massimo, non un incasso: non supera i contributi davvero dovuti.'],
      ['Non somma ciò che si esclude', 'Gli esoneri dello stesso gruppo sono alternativi: per ogni assunzione conta solo il più ricco.'],
      ['Collega la crescita', 'Dai ricavi previsti ricava quante persone servono e a ognuna assegna la misura migliore.'],
    ],
    example: { title: 'Un esempio, con numeri di scuola', rows: [['Impresa', 'srl in Puglia, 8 dipendenti, DURC regolare'], ['Crescita prevista', '+20% di ricavi → 2 assunzioni'], ['Misura', 'Bonus Giovani in zona ZES'], ['Valore', '650 € × 24 mesi = 15.600 € per persona']], end: 'Fino a 31.200 € per le due assunzioni, al massimo.' },
    rules: ['Le misure «da verificare» non entrano mai nei totali.', 'Nessun importo senza una fonte scritta.', 'Le misure regionali si cercano nel catalogo, filtrate per la regione dell’impresa.'],
  },
  riparto: {
    name: 'Riparto', role: 'Allocazione', n: 2, img: '/landing/mascotte-riparto.webp',
    line: 'Decide quale agevolazione paga quale spesa, senza mai contare due volte la stessa voce.',
    video: 'tutorial-t08', videoNote: 'Allocazione: chi paga cosa. La stima dell’anno e il piano, nel portale.',
    steps: [
      ['Compone le spese dell’anno', 'Dal budget dell’azienda, dal piano degli investimenti o dalla previsione sul bilancio. Ogni riga dice da dove viene.'],
      ['Giudica ogni bando', 'Apertura, spese ammesse, settore, territorio, dimensione. Un solo «no» e il bando è non adatto, con il motivo scritto.'],
      ['Studia i bandi affini', 'Quelli del catalogo con più affinità si studiano a fondo, uno dopo l’altro: solo i bandi studiati entrano nel piano.'],
      ['Ottimizza la combinazione', 'Un modello matematico esatto rispetta tetti, intensità, non cumulabilità, massimali e de minimis. Stessi dati, stesso piano.'],
      ['Scrive un budget per bando', 'Il personale si divide tra i bandi senza superare il 100% del tempo. Sei controlli incrociati prima di consegnare.'],
    ],
    example: { title: 'Un esempio verificato con il motore vero', rows: [['Spese', 'macchinario 100.000 € · consulenza 30.000 €'], ['Fondo A', '40% su beni e consulenze, tetto 30.000 €'], ['Fondo B', '50% sui soli beni, de minimis residuo 20.000 €'], ['Piano', 'B sul macchinario 20.000 € · A sulla consulenza 12.000 €']], end: '32.000 €: più dei 30.000 € della soluzione «ovvia».' },
    rules: ['Solo i bandi adatti entrano nella somma.', 'Una spesa non si copre oltre il 100%.', 'Il valore atteso si calcola solo con probabilità e costi indicati da una persona.'],
  },
  spunta: {
    name: 'Spunta', role: 'Budget', n: 3, img: '/landing/mascotte-spunta.webp',
    line: 'Scrive la bozza del budget dai documenti e la controlla con 60 criteri, prima che lo faccia l’ente.',
    video: 'tutorial-t12', videoNote: 'Il budget e i 60 criteri: la bozza nata dall’azienda e il controllo voce per voce.',
    steps: [
      ['Parte dall’azienda', 'Personale persona per persona (RAL, livello, contratto, quota di tempo) e le altre spese con importo, fonte e documento.'],
      ['Toglie ciò che il bando esclude', 'Le voci non ammesse dal bando non entrano nella bozza: non si gonfia un budget.'],
      ['Controlla ogni voce', '60 criteri deterministici: ammessa, ridotta, respinta o in attesa di un documento, con la regola che lo dice.'],
      ['Verifica tutto insieme', 'Tetti per categoria, cumulo con gli altri aiuti, persone mai oltre il 100% del tempo.'],
      ['Firma il risultato', 'Ogni budget controllato lascia un’impronta firmata nel registro: chiunque può verificare che nulla sia cambiato.'],
    ],
    example: { title: 'Cosa ti dice, in cima alla pagina', rows: [['Ho fatto', 'ho preparato 5 budget dal piano'], ['Ho trovato', '12 voci ammesse su 14, 2 ridotte'], ['Verificati insieme', 'nessun conflitto'], ['Mi serve da te', '1 voce aspetta il CUP']], end: 'Un solo pulsante, che cambia con il passo successivo.' },
    rules: ['I costi ordinari non diventano costi di progetto.', 'Un’ora di lavoro non si rendiconta a due bandi.', 'Ogni esito cita la regola del bando da cui viene.'],
  },
  duo: {
    name: 'Duo', role: 'Confronto', n: 4, img: '/landing/mascotte-duo.webp',
    line: 'Confronta il tuo budget con quelli di chi ha già partecipato: una statistica spiegabile, non un’opinione.',
    video: 'tutorial-t15', videoNote: 'Il Confronto: il consiglio che impara dai budget salvati.',
    steps: [
      ['Cerca chi somiglia', 'Sei livelli, dal più preciso (stessa nicchia e stesso bando) al più generale. Si usa il primo con almeno 3 budget.'],
      ['Pesa gli esiti', 'Ammesso pesa 3, presentato 1,5, bozza 1, non ammesso 0,25: i budget che hanno vinto guidano il consiglio.'],
      ['Calcola il consiglio', 'Per ogni voce la media pesata e l’intervallo «di solito tra».'],
      ['Misura la distanza', 'Quanto il tuo budget si scosta dal consiglio, e su quale voce. Entro il 10% è «vicino».'],
      ['Protegge i clienti', 'Dei budget altrui si usa un gruppo solo se ha almeno 3 budget: nessuno può risalire a un cliente.'],
    ],
    example: { title: 'Un esempio, con numeri di scuola', rows: [['Ammesso (peso 3)', 'personale 60 · beni 30 · consulenze 10'], ['Bozza (peso 1)', '50 · 30 · 20'], ['Non ammesso (peso 0,25)', '20 · 70 · 10'], ['Consiglio', '55,3% · 32,4% · 12,4%']], end: 'Un budget 50 · 35 · 15 dista il 5,3%: vicino.' },
    rules: ['La fiducia è alta solo con almeno 8 budget reali dello stesso bando e nicchia.', 'Con meno di 3 budget reali la fiducia è sempre bassa, e lo dice.', 'Gli esempi di avvio pesano la metà e spariscono quando arrivano i dati veri.'],
  },
}
const ORDER = ['fiuto', 'riparto', 'spunta', 'duo']

function Loop({ name }) {
  const ref = useRef(null)
  useEffect(() => {
    const v = ref.current
    if (!v || window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return undefined
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) v.play().catch(() => {}); else v.pause() }, { threshold: 0.3 })
    io.observe(v)
    return () => io.disconnect()
  }, [name])
  return <video ref={ref} key={name} className="ag-video" src={`/video/${name}.mp4`} poster={`/video/${name}.jpg`} muted loop playsInline autoPlay preload="metadata" aria-hidden="true" disablePictureInPicture />
}

function Reveal({ children, className = '', as: Tag = 'div' }) {
  const ref = useRef(null)
  const [inView, setInView] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el || typeof IntersectionObserver === 'undefined') { setInView(true); return undefined }
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setInView(true); io.disconnect() } }, { threshold: 0.15 })
    io.observe(el)
    return () => io.disconnect()
  }, [])
  return <Tag ref={ref} className={`ag-rv ${inView ? 'in' : ''} ${className}`}>{children}</Tag>
}

export default function AgentPage({ id, onHome, onAgent, onStart }) {
  const a = AGENT_PAGES[id] || AGENT_PAGES.fiuto
  const next = ORDER[(ORDER.indexOf(id) + 1) % ORDER.length]
  const nx = AGENT_PAGES[next]
  useEffect(() => { window.scrollTo({ top: 0 }) }, [id])
  return (
    <div className="qt-agent">
      <nav className="ag-nav"><div className="ag-pill">
        <button className="ag-back" onClick={onHome}><ArrowLeft size={14} /><Wordmark height={14} className="ag-wordmark" /></button>
        <div className="ag-others">{ORDER.map((k) => <button key={k} className={k === id ? 'on' : ''} onClick={() => onAgent(k)}><img src={AGENT_PAGES[k].img} alt="" />{AGENT_PAGES[k].name}</button>)}</div>
        <button className="ag-cta" onClick={onStart}>Richiedi accesso</button>
      </div></nav>

      <header className="ag-hero" key={id}>
        <img src={a.img} alt={`${a.name}, l’agente ${a.role}`} className="ag-mascot" />
        <div>
          <p className="ag-kicker"><span>{a.n}</span>{a.role}</p>
          <h1>{a.name}</h1>
          <p className="ag-line">{a.line}</p>
        </div>
      </header>

      <section className="ag-sect"><div className="ag-wrap ag-media">
        <Reveal className="ag-frame"><Loop name={a.video} /></Reveal>
        <Reveal as="p" className="ag-note">{a.videoNote}</Reveal>
      </div></section>

      <section className="ag-sect"><div className="ag-wrap">
        <Reveal as="h2">Come lavora</Reveal>
        <ol className="ag-steps">
          {a.steps.map(([t, b], k) => (
            <Reveal as="li" key={t}><span className="ag-num">{String(k + 1).padStart(2, '0')}</span><div><h3>{t}</h3><p>{b}</p></div></Reveal>
          ))}
        </ol>
      </div></section>

      <section className="ag-sect"><div className="ag-wrap ag-two">
        <Reveal className="ag-card">
          <p className="ag-card-head">{a.example.title}</p>
          {a.example.rows.map(([k, v]) => <div key={k} className="ag-row"><span>{k}</span><span>{v}</span></div>)}
          <p className="ag-card-end">{a.example.end}</p>
        </Reveal>
        <Reveal className="ag-rules">
          <p className="ag-card-head">Regole che non cambia mai</p>
          <ul>{a.rules.map((r) => <li key={r}>{r}</li>)}</ul>
        </Reveal>
      </div></section>

      <section className="ag-sect ag-last"><div className="ag-wrap ag-next">
        <button className="ag-nextcard" onClick={() => onAgent(next)}>
          <img src={nx.img} alt="" />
          <span><small>Poi il lavoro passa a</small><b>{nx.name} · {nx.role}</b></span>
          <ArrowRight size={18} />
        </button>
        <button className="ag-cta big" onClick={onStart}>Richiedi accesso<ArrowRight size={15} /></button>
      </div></section>

      <footer className="ag-foot"><div className="ag-wrap">© 2026 QUANTO · gli esempi usano numeri di scuola; i video sono del portale.</div></footer>
    </div>
  )
}
