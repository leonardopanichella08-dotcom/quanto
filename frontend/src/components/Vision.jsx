import React, { useEffect, useRef, useState } from 'react'
import { ArrowLeft, ArrowRight, Fingerprint, ShieldCheck, Target } from 'lucide-react'
import './Vision.css'

function Reveal({ children, className = '' }) {
  const ref = useRef(null)
  const [inView, setInView] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setInView(true); io.disconnect() } }, { threshold: 0.2 })
    io.observe(el)
    return () => io.disconnect()
  }, [])
  return <div ref={ref} className={`fade-up ${inView ? 'in' : ''} ${className}`}>{children}</div>
}

const SECTIONS = ['apertura', 'idea', 'principi', 'architettura', 'visione', 'chiusura']

export default function Vision({ onGoHome, onStart }) {
  const [active, setActive] = useState(0)
  useEffect(() => {
    const els = SECTIONS.map((id) => document.getElementById(id)).filter(Boolean)
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) setActive(SECTIONS.indexOf(e.target.id)) })
    }, { threshold: 0.5 })
    els.forEach((el) => io.observe(el))
    return () => io.disconnect()
  }, [])
  const scrollTo = (id) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })

  return (
    <div className="qt-vision">
      <div className="glow" style={{ width: 600, height: 600, top: '10%', left: '50%', transform: 'translateX(-50%)' }} />
      <svg className="grain" width="100%" height="100%"><filter id="ng"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" stitchTiles="stitch" /></filter><rect width="100%" height="100%" filter="url(#ng)" /></svg>

      <div className="scroll-index">
        {SECTIONS.map((id, i) => <button key={id} className={i === active ? 'on' : ''} onClick={() => scrollTo(id)} aria-label={id} />)}
      </div>

      <nav className="v-nav"><div className="row">
        <button onClick={onGoHome}><ArrowLeft className="w-3.5 h-3.5" />QUANTO</button>
        <button className="brand-btn" onClick={onStart}>Inizia gratis</button>
      </div></nav>

      <section className="reel" id="apertura"><div className="wrap">
        <div className="eyebrow-v"><span className="n mono">01</span>Il punto di partenza</div>
        <Reveal><h1 className="open">Ogni anno, migliaia di progetti chiedono un contributo pubblico. <span className="accent">Una parte viene respinta</span> per un dettaglio nel budget che nessuno aveva controllato prima.</h1></Reveal>
        <Reveal><p className="lede">Non per il progetto. Non per il merito. Per un tetto di spesa, una percentuale, una regola scritta in un decreto che nessuno ha letto fino in fondo prima di premere "invia".</p></Reveal>
      </div></section>

      <section className="reel" id="idea"><div className="wrap">
        <div className="eyebrow-v"><span className="n mono">02</span>L'idea</div>
        <Reveal><h2 className="statement">Le regole esistono già. Sono scritte, pubbliche, ufficiali.<br />Nessuno le aveva mai rese <span className="accent">calcolabili</span>.</h2></Reveal>
        <Reveal><p className="body-v">Un bando pubblico è un contratto: dice cosa è ammesso, quanto, entro quando, con quale documentazione. È tutto lì, nero su bianco — decreti, circolari, allegati tecnici. Ma è scritto per essere letto da una persona, non da una macchina. Così ogni consulente lo rilegge da capo, ogni volta, e ogni lettura può differire dalla precedente.</p></Reveal>
        <Reveal><div className="quote-block"><p>Non serve indovinare se un budget verrà accettato. Basta calcolarlo — una volta sola, nello stesso modo, per tutti.</p></div></Reveal>
      </div></section>

      <section className="reel" id="principi"><div className="wrap">
        <div className="eyebrow-v"><span className="n mono">03</span>I principi</div>
        <Reveal><h2 className="statement">QUANTO non genera risposte. Le calcola.</h2></Reveal>
        <Reveal><p className="body-v">È la differenza tra chiedere a un modello linguistico "questo budget andrà bene?" e costruire un motore che applica la regola vera, con la fonte accanto, sempre nello stesso modo.</p></Reveal>
        <div className="principle-list">
          <Reveal><div className="principle"><div className="ic"><Target className="w-6 h-6" /></div><div><h3>Deterministico</h3><p>Stesso budget, stesso risultato — oggi, tra un anno, su qualunque server. Nessuna generazione: solo calcolo, tracciabile fino all'ultima riga.</p></div></div></Reveal>
          <Reveal><div className="principle"><div className="ic"><Fingerprint className="w-6 h-6" /></div><div><h3>Fonti dichiarate</h3><p>Ogni regola cita da dove viene — un decreto, una circolare, una pagina ufficiale — e con quale affidabilità è stata letta. Quello che le fonti non dicono resta scritto come lacuna, mai inventato.</p></div></div></Reveal>
          <Reveal><div className="principle"><div className="ic"><ShieldCheck className="w-6 h-6" /></div><div><h3>Verificabile</h3><p>Ogni budget controllato lascia un'impronta firmata, composta in un registro a catena: chiunque — un revisore, un ente, un socio — può controllare che nulla sia stato cambiato dopo la certificazione.</p></div></div></Reveal>
        </div>
      </div></section>

      <section className="reel" id="architettura"><div className="wrap">
        <div className="eyebrow-v"><span className="n mono">04</span>Come è fatto</div>
        <Reveal><h2 className="statement">Tre fonti. Un motore. Un registro.</h2></Reveal>
        <Reveal><p className="body-v">L'architettura non è un dettaglio tecnico: è la scelta di non fidarsi di nessuna fonte singola, e di non lasciare mai una cifra senza sapere da dove viene.</p></Reveal>
        <Reveal><div className="arch-grid">
          <div className="arch-card"><div className="tag mono">Fonte A</div><h4>Il bando</h4><p>Ricerca autonoma di decreti, avvisi, circolari; ogni regola resta legata al testo da cui è stata letta.</p></div>
          <div className="arch-card"><div className="tag mono">Fonte B</div><h4>Le tabelle ufficiali</h4><p>CCNL, ammortamenti, parametri di legge — versionati, datati, mai impliciti: se manca una tabella, il controllo lo dichiara invece di stimare.</p></div>
          <div className="arch-card"><div className="tag mono">Fonte C</div><h4>I documenti del cliente</h4><p>Buste paga, bilanci, candidature: letti con una soglia di sicurezza per campo, cifrati a riposo, dati personali sempre come token opachi.</p></div>
        </div></Reveal>
        <Reveal><p className="body-v" style={{ marginTop: 36 }}>Sopra le tre fonti, un motore applica fino a 60 criteri deterministici a ogni voce di spesa. Ogni voce controllata lascia un'impronta digitale; le impronte si compongono in un albero di Merkle, e la cima dell'albero — una sola impronta, firmata — è la prova che quel budget, in quel momento, era esattamente così.</p></Reveal>
      </div></section>

      <section className="reel short" id="visione"><div className="wrap">
        <div className="eyebrow-v"><span className="n mono">05</span>La visione</div>
        <Reveal><h2 className="statement">Non vogliamo essere un altro strumento di conformità.</h2></Reveal>
        <Reveal><p className="lede">Vogliamo diventare l'infrastruttura di fiducia tra chi chiede un fondo pubblico e chi lo eroga — il punto in cui entrambe le parti guardano lo stesso calcolo, fatto con le stesse regole, verificabile da chiunque.</p></Reveal>
        <Reveal><p className="body-v">Oggi QUANTO controlla un budget. Domani, la stessa disciplina — regole dichiarate, calcolo deterministico, registro verificabile — può estendersi a ogni fase della vita di un fondo pubblico: dalla candidatura alla rendicontazione, fino all'audit finale. Non un'altra promessa dell'intelligenza artificiale: una macchina che non indovina mai, e per questo si può controllare.</p></Reveal>
      </div></section>

      <section className="reel short closing" id="chiusura"><div className="wrap">
        <Reveal><h2 className="statement">Vuoi saperne di più?</h2></Reveal>
        <Reveal><p className="lede" style={{ marginInline: 'auto' }}>Prova QUANTO con un bando vero, o torna alla presentazione del prodotto.</p></Reveal>
        <div className="closing-ctas">
          <button className="btn-v-solid" onClick={onStart}>Inizia gratis<ArrowRight className="w-3.5 h-3.5" /></button>
          <button className="btn-v-line" onClick={onGoHome}>Torna al prodotto</button>
        </div>
      </div></section>

      <footer className="v-foot">© 2026 QUANTO — una macchina che non indovina mai.</footer>
    </div>
  )
}
