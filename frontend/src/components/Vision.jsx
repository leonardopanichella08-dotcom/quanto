import React, { useEffect, useRef, useState } from 'react'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { Wordmark } from './ui'
import './Vision.css'

/* «La visione»: stesso linguaggio della homepage (bianco, nero, giallo #F1E21B, tipografia grande, nessun riquadro).
   Ogni blocco compare quando entra in vista; con «riduci movimento» è già fermo. */
function Reveal({ children, className = '', as: Tag = 'div' }) {
  const ref = useRef(null)
  const [inView, setInView] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el) return undefined
    if (typeof IntersectionObserver === 'undefined' || window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) { setInView(true); return undefined }
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setInView(true); io.disconnect() } }, { threshold: 0.18 })
    io.observe(el)
    return () => io.disconnect()
  }, [])
  return <Tag ref={ref} className={`v-rv ${inView ? 'in' : ''} ${className}`}>{children}</Tag>
}

const SECTIONS = [['apertura', 'Il punto di partenza'], ['idea', 'L’idea'], ['principi', 'I principi'], ['architettura', 'Come è fatto'], ['visione', 'La visione'], ['chiusura', 'Inizia']]

export default function Vision({ onGoHome, onStart }) {
  const [active, setActive] = useState(0)
  const [glass, setGlass] = useState(false)
  useEffect(() => {
    const els = SECTIONS.map(([id]) => document.getElementById(id)).filter(Boolean)
    const io = new IntersectionObserver((entries) => entries.forEach((e) => { if (e.isIntersecting) setActive(SECTIONS.findIndex(([id]) => id === e.target.id)) }), { threshold: 0.45 })
    els.forEach((el) => io.observe(el))
    const on = () => setGlass(window.scrollY > 24)
    on()
    window.addEventListener('scroll', on, { passive: true })
    return () => { io.disconnect(); window.removeEventListener('scroll', on) }
  }, [])
  const go = (id) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })

  return (
    <div className="qt-vision">
      <nav className={`v-nav${glass ? ' glass' : ''}`}><div className="v-pill">
        <button className="v-back" onClick={onGoHome}><ArrowLeft size={14} /><Wordmark height={14} className="v-wordmark" /></button>
        <button className="v-cta" onClick={onStart}>Richiedi accesso</button>
      </div></nav>

      <ol className="v-index" aria-label="Sezioni">
        {SECTIONS.map(([id, label], i) => <li key={id}><button className={i === active ? 'on' : ''} onClick={() => go(id)} aria-label={label}><span>{label}</span></button></li>)}
      </ol>

      <section className="v-sect first" id="apertura"><div className="v-wrap">
        <Reveal as="h1">Ogni anno migliaia di progetti chiedono un contributo pubblico. <mark>Una parte viene respinta</mark> per un dettaglio nel budget che nessuno aveva controllato prima.</Reveal>
        <Reveal as="p" className="v-lede">Non per il progetto. Non per il merito. Per un tetto di spesa, una percentuale, una regola scritta in un decreto che nessuno ha letto fino in fondo prima di premere «invia».</Reveal>
      </div></section>

      <section className="v-sect" id="idea"><div className="v-wrap">
        <Reveal as="h2">Le regole esistono già. Sono scritte, pubbliche, ufficiali. Nessuno le aveva mai rese <mark>calcolabili</mark>.</Reveal>
        <Reveal as="p" className="v-body">Un bando pubblico è un contratto: dice cosa è ammesso, quanto, entro quando, con quale documentazione. È tutto lì, nero su bianco, in decreti, circolari e allegati tecnici. Ma è scritto per essere letto da una persona, non da una macchina. Così ogni consulente lo rilegge da capo, ogni volta, e ogni lettura può differire dalla precedente.</Reveal>
        <Reveal as="blockquote" className="v-quote">Non serve indovinare se un budget verrà accettato. Basta calcolarlo: una volta sola, nello stesso modo, per tutti.</Reveal>
      </div></section>

      <section className="v-sect" id="principi"><div className="v-wrap">
        <Reveal as="h2">QUANTO non genera risposte. Le calcola.</Reveal>
        <Reveal as="p" className="v-body">È la differenza tra chiedere a un modello linguistico «questo budget andrà bene?» e costruire un motore che applica la regola vera, con la fonte accanto, sempre nello stesso modo.</Reveal>
        <div className="v-principles">
          {[['Deterministico', 'Stesso budget, stesso risultato: oggi, tra un anno, su qualunque server. Nessuna generazione: solo calcolo, tracciabile fino all’ultima riga.'],
            ['Fonti dichiarate', 'Ogni regola cita da dove viene (un decreto, una circolare, una pagina ufficiale) e con quale affidabilità è stata letta. Quello che le fonti non dicono resta scritto come lacuna, mai inventato.'],
            ['Verificabile', 'Ogni budget controllato lascia un’impronta firmata, composta in un registro a catena: chiunque, un revisore, un ente, un socio, può controllare che nulla sia cambiato dopo la verifica.']].map(([t, b], k) => (
            <Reveal key={t} className="v-principle"><span className="v-n">0{k + 1}</span><h3>{t}</h3><p>{b}</p></Reveal>
          ))}
        </div>
      </div></section>

      <section className="v-sect" id="architettura"><div className="v-wrap">
        <Reveal as="h2">Tre fonti. Un motore. Un registro.</Reveal>
        <Reveal as="p" className="v-body">L’architettura non è un dettaglio tecnico: è la scelta di non fidarsi di nessuna fonte singola, e di non lasciare mai una cifra senza sapere da dove viene.</Reveal>
        <div className="v-sources">
          {[['A', 'Il bando', 'Ricerca autonoma di decreti, avvisi e circolari; ogni regola resta legata al testo da cui è stata letta.'],
            ['B', 'Le tabelle ufficiali', 'Contratti collettivi, ammortamenti, parametri di legge: versionati, datati, mai impliciti. Se manca una tabella, il controllo lo dichiara invece di stimare.'],
            ['C', 'I documenti del cliente', 'Buste paga, bilanci, candidature: letti con una soglia di sicurezza per campo, cifrati a riposo, dati personali sempre come codici anonimi.']].map(([l, t, b]) => (
            <Reveal key={l} className="v-source"><span className="v-letter">{l}</span><div><h3>{t}</h3><p>{b}</p></div></Reveal>
          ))}
        </div>
        <Reveal as="p" className="v-body">Sopra le tre fonti, un motore applica fino a 60 criteri deterministici a ogni voce di spesa. Ogni voce controllata lascia un’impronta digitale; le impronte si compongono in un albero di Merkle, e la cima dell’albero, una sola impronta firmata, è la prova che quel budget, in quel momento, era esattamente così.</Reveal>
      </div></section>

      <section className="v-sect" id="visione"><div className="v-wrap">
        <Reveal as="h2">Oggi la finanza agevolata. Domani il sistema operativo dello studio.</Reveal>
        <Reveal as="p" className="v-lede">Vogliamo diventare l’infrastruttura di fiducia tra chi chiede un fondo pubblico e chi lo eroga: il punto in cui entrambe le parti guardano lo stesso calcolo, fatto con le stesse regole, verificabile da chiunque.</Reveal>
        <Reveal as="p" className="v-body">Oggi QUANTO svolge le pratiche di finanza agevolata con quattro agenti. Domani la stessa disciplina (regole dichiarate, calcolo deterministico, registro verificabile) si estende a ogni fase della vita di un fondo pubblico, dalla candidatura alla rendicontazione, e alle altre attività dello studio, una alla volta. Non un’altra promessa dell’intelligenza artificiale: una macchina che non indovina mai, e per questo si può controllare.</Reveal>
      </div></section>

      <section className="v-sect last" id="chiusura"><div className="v-wrap">
        <Reveal as="h2">Prova QUANTO con un cliente vero.</Reveal>
        <Reveal className="v-ctas">
          <button className="v-cta big" onClick={onStart}>Richiedi accesso<ArrowRight size={15} /></button>
          <button className="v-link" onClick={onGoHome}>Torna al prodotto</button>
        </Reveal>
      </div></section>

      <footer className="v-foot"><div className="v-wrap">© 2026 QUANTO · una macchina che non indovina mai.</div></footer>
    </div>
  )
}
