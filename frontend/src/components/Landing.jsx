import React, { useEffect, useRef, useState } from 'react'
import { ArrowRight, ArrowUp, Loader2, Lock, ShieldCheck, X } from 'lucide-react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { api, session } from '../lib/api'
import { Wordmark } from './ui'
import { FAQ } from '../data/faq.js'
import { answer } from '../lib/faqSearch'
import './Landing.css'
import PortalPreview from './PortalPreview'
import './PortalPreview.css'

gsap.registerPlugin(ScrollTrigger)

/* Homepage pubblica. Colori del marchio: bianco, nero, giallo #F1E21B. Nessun riquadro, nessuna griglia di schede:
   tipografia, linee, fotografia e movimento. Ogni animazione mostra il lavoro vero di QUANTO; le cifre sono di un esempio e lo dicono.
   Animazioni con GSAP (sempre fromTo con valori finali espliciti); con «riduci movimento» tutto è fermo e leggibile. */

const reduced = () => typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches

// ------------------------------------------------------------------------------------------------ accesso
function AuthModal({ mode, onClose, onSwitch, onDone }) {
  const isRegister = mode === 'register'
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError(null)
    try {
      const res = isRegister ? await api.register(email.trim(), name.trim(), password) : await api.login(email.trim(), password)
      session.set(res.access_token, res.user)
      onDone(res.user)
    } catch (err) { setError(err.message) } finally { setBusy(false) }
  }
  return (
    <div className="qt-modal-backdrop" onClick={onClose}>
      <form className="qt-modal" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <button type="button" className="close" onClick={onClose} aria-label="Chiudi"><X className="w-4 h-4" /></button>
        <h3>{isRegister ? 'Richiedi accesso' : 'Accedi'}</h3>
        <p className="sub">{isRegister ? 'Crea l’account dello studio. In questa fase è gratuito e non serve la carta di credito.' : 'Usa le credenziali dello studio.'}</p>
        {isRegister && (<><label htmlFor="ln-name">Nome</label><input id="ln-name" required autoFocus value={name} onChange={(e) => setName(e.target.value)} /></>)}
        <label htmlFor="ln-email">E-mail</label>
        <input id="ln-email" type="email" required autoFocus={!isRegister} autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} />
        <label htmlFor="ln-pw">Password</label>
        <input id="ln-pw" type="password" required minLength={isRegister ? 12 : 1} autoComplete={isRegister ? 'new-password' : 'current-password'} value={password} onChange={(e) => setPassword(e.target.value)} />
        {isRegister && <p className="hint">Almeno 12 caratteri, lettere e almeno un numero o simbolo.</p>}
        {error && <p className="error">{error}</p>}
        <button disabled={busy || !email || !password || (isRegister && !name)} className="submit">
          {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}{isRegister ? 'Crea l’account' : 'Entra'}
        </button>
        <p className="switch">
          {isRegister ? <>Hai già un account? <button type="button" onClick={() => onSwitch('login')}>Accedi</button></> : <>Non hai un account? <button type="button" onClick={() => onSwitch('register')}>Richiedi accesso</button></>}
        </p>
      </form>
    </div>
  )
}


// ------------------------------------------------------------------------------------------------ il processo: la pratica si compone mentre si scorre
const STEPS = [
  { title: 'Il cliente', body: 'Bilanci o dichiarazione dei redditi, visura, buste paga, F24: QUANTO li legge e compila il profilo dell’impresa. Quello che manca lo chiede, non lo stima.', line: ['Profilo', 'Impresa di prova · ATECO 62.01 · profilo al 93%'] },
  { title: 'Le agevolazioni', body: 'Cerca in tutto il catalogo: bandi nazionali, regionali e camerali, crediti d’imposta, incentivi alle assunzioni. Tiene solo ciò che l’impresa può ottenere e scrive perché il resto è escluso.', line: ['Agevolazioni', '3 adatte · le escluse con il motivo scritto'] },
  { title: 'Lo studio del bando', body: 'Legge avvisi, decreti e allegati e ne ricava le regole numeriche, ognuna legata al testo da cui viene. Ciò che il bando non scrive resta dichiarato come lacuna.', line: ['Regole', '7 regole numeriche, ognuna con la sua fonte'] },
  { title: 'Il progetto e il budget', body: 'Dai bisogni dell’impresa al progetto, dal progetto al budget del bando, controllato voce per voce con 60 criteri. Il piano dice quale agevolazione copre quale spesa, senza contarla due volte.', line: ['Budget', '60 controlli per voce · cosa passa, cosa va ridotto'] },
  { title: 'La domanda', body: 'Confronto tra scenari, documenti di domanda raccolti dal sito ufficiale, dossier per il cliente e un registro firmato che prova che i numeri non sono stati toccati.', line: ['Consegna', 'dossier · documenti di domanda · registro 7f3a…9b1d'] },
]


// ------------------------------------------------------------------------------------------------ video di sfondo: parte da solo, senza audio, in loop; con «riduci movimento» resta la foto
function BgVideo({ className }) {
  const ref = useRef(null)
  useEffect(() => {
    const v = ref.current
    if (!v) return undefined
    if (reduced()) { v.pause(); return undefined }
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) v.play().catch(() => {}); else v.pause() }, { threshold: 0.05 })
    io.observe(v)
    return () => io.disconnect()
  }, [])
  return <video ref={ref} className={className} src="/landing/sfondo.mp4" poster="/landing/skyline-alba.jpg" muted loop playsInline autoPlay preload="auto" aria-hidden="true" tabIndex={-1} disablePictureInPicture />
}

// ------------------------------------------------------------------------------------------------ video che scorre come un'animazione
function LoopVideo({ src, poster, label }) {
  const ref = useRef(null)
  useEffect(() => {
    const v = ref.current
    if (!v) return undefined
    if (reduced()) { v.pause(); return undefined }
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) v.play().catch(() => {}); else v.pause() }, { threshold: 0.25 })
    io.observe(v)
    return () => io.disconnect()
  }, [])
  return <video ref={ref} className="loop-video" src={src} poster={poster} muted loop playsInline autoPlay preload="metadata" aria-label={label} disablePictureInPicture controlsList="nodownload nofullscreen noremoteplayback" />
}

// ------------------------------------------------------------------------------------------------ domande: 8 in vista, le altre si chiedono
const SHOWN = [
  ['Che cos’è QUANTO', 0], ['Che cos’è QUANTO', 1], ['Che cos’è QUANTO', 6], ['La ricerca delle agevolazioni', 1],
  ['Quali bandi sono davvero per il cliente', 2], ['Il budget e i 60 criteri', 8], ['Sicurezza e privacy', 1], ['Prezzi e token', 0],
].map(([c, k]) => FAQ.find((g) => g.cat === c).items[k])

function FaqShort() {
  const [open, setOpen] = useState(null)
  return (
    <dl className="faq">
      {SHOWN.map(([q, a], k) => (
        <div key={q} className={`faq-item${open === k ? ' open' : ''}`}>
          <dt><button type="button" aria-expanded={open === k} onClick={() => setOpen(open === k ? null : k)}><span>{q}</span><i aria-hidden="true" /></button></dt>
          <dd><div><p>{a}</p></div></dd>
        </div>
      ))}
    </dl>
  )
}

function AskQuanto() {
  const [q, setQ] = useState('')
  const [log, setLog] = useState([])
  const end = useRef(null)
  const ask = (text) => {
    const t = (text ?? q).trim()
    if (!t) return
    setLog((l) => [...l, { q: t, r: answer(t) }])
    setQ('')
  }
  useEffect(() => { end.current?.scrollIntoView?.({ block: 'nearest', behavior: reduced() ? 'auto' : 'smooth' }) }, [log])
  return (
    <div className="ask">
      <div className="ask-log" aria-live="polite">
        {log.length === 0 && <p className="ask-hint">Scrivi una domanda su QUANTO. Rispondo con le risposte scritte dal team, non con un modello che inventa.</p>}
        {log.map((m, k) => (
          <div key={k} className="ask-turn">
            <p className="ask-q">{m.q}</p>
            {m.r.best ? <p className="ask-a">{m.r.best[1]}</p> : <p className="ask-a muted">Non ho una risposta scritta per questa domanda. Prova con altre parole, per esempio «budget», «de minimis» o «token».</p>}
            {m.r.related.length > 0 && <div className="ask-rel">{m.r.related.map(([rq]) => <button key={rq} type="button" onClick={() => ask(rq)}>{rq}</button>)}</div>}
          </div>
        ))}
        <span ref={end} />
      </div>
      <form className="ask-bar" onSubmit={(e) => { e.preventDefault(); ask() }}>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Chiedi a QUANTO…" aria-label="Fai una domanda su QUANTO" />
        <button type="submit" disabled={!q.trim()} aria-label="Invia la domanda"><ArrowUp size={16} /></button>
      </form>
    </div>
  )
}

const VERBS = [
  ['Trova', 'Le agevolazioni per cui l’impresa ha i requisiti, su tutto il catalogo: bandi nazionali, regionali e camerali, crediti d’imposta, incentivi alle assunzioni. Ogni esclusione ha il suo motivo.'],
  ['Studia', 'Le regole del bando lette dai testi ufficiali: intensità, tetti, spese ammesse, cumulo, de minimis. Ogni regola resta legata all’articolo da cui viene.'],
  ['Costruisce', 'Il progetto dai bisogni dell’impresa e il budget del bando dai suoi documenti, persona per persona e voce per voce.'],
  ['Controlla', 'Ogni voce con 60 criteri, prima che lo faccia l’ente: cosa passa, cosa va ridotto, cosa va documentato.'],
]

export default function Landing({ onLogin, onAuditor, onVision }) {
  const root = useRef(null)
  const [modal, setModal] = useState(null)
  const [nav, setNav] = useState({ glass: false, hide: false })
  const [step, setStep] = useState(0)

  // navigazione: trasparente sull'apertura, vetro allo scorrimento; sparisce scendendo e torna appena si risale
  useEffect(() => {
    let last = window.scrollY
    const on = () => {
      const y = window.scrollY
      const dir = y > last + 4 ? 'down' : y < last - 4 ? 'up' : null      // la direzione si decide qui, prima che «last» cambi
      last = y
      setNav((n) => {
        const hide = y < 160 ? false : dir === 'down' ? true : dir === 'up' ? false : n.hide
        const glass = y > 24
        return hide === n.hide && glass === n.glass ? n : { glass, hide }
      })
    }
    window.addEventListener('scroll', on, { passive: true })
    return () => window.removeEventListener('scroll', on)
  }, [])
  const navHidden = nav.hide

  useEffect(() => {
    if (reduced()) { setStep(STEPS.length - 1); return undefined }
    const ctx = gsap.context(() => {
      gsap.fromTo('.hero .ln > span', { yPercent: 110 }, { yPercent: 0, duration: 1.2, ease: 'power4.out', stagger: 0.09, delay: 0.15 })
      gsap.fromTo('.hero .after', { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 1, ease: 'power3.out', stagger: 0.1, delay: 0.6 })
      gsap.fromTo('.hero .hero-img', { scale: 1.08 }, { scale: 1, duration: 2.4, ease: 'power2.out' })
      gsap.fromTo('.hero .hero-img', { yPercent: 0 }, { yPercent: 12, ease: 'none', scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true } })

      gsap.utils.toArray('.mask-in').forEach((el) => gsap.fromTo(el.querySelectorAll('.ln > span'), { yPercent: 110 }, { yPercent: 0, duration: 1.1, ease: 'power4.out', stagger: 0.08, scrollTrigger: { trigger: el, start: 'top 85%' } }))
      gsap.utils.toArray('.fade-in').forEach((el) => gsap.fromTo(el, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 1, ease: 'power3.out', scrollTrigger: { trigger: el, start: 'top 88%' } }))


      // i quattro verbi: il contorno si riempie di nero mentre la parola attraversa la pagina, la sottolineatura gialla corre
      gsap.utils.toArray('.verb').forEach((el) => {
        gsap.fromTo(el.querySelector('.verb-fill'), { clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0% 0 0)', ease: 'none', scrollTrigger: { trigger: el, start: 'top 80%', end: 'top 35%', scrub: true } })
        gsap.fromTo(el.querySelector('.verb-line'), { scaleX: 0 }, { scaleX: 1, ease: 'none', scrollTrigger: { trigger: el, start: 'top 70%', end: 'top 35%', scrub: true } })
        gsap.fromTo(el.querySelector('p'), { opacity: 0, x: 24 }, { opacity: 1, x: 0, duration: 1, ease: 'power3.out', scrollTrigger: { trigger: el, start: 'top 60%' } })
      })

      const mm = gsap.matchMedia()
      mm.add('(min-width: 961px)', () => {
        ScrollTrigger.create({
          trigger: '.proc', start: 'top top', end: () => `+=${window.innerHeight * 0.42 * STEPS.length}`, pin: '.proc-pin', scrub: true,
          onUpdate: (s) => { setStep(Math.min(STEPS.length - 1, Math.floor(s.progress * STEPS.length))); gsap.set('.proc-progress', { scaleY: s.progress }) },
        })
      })
      mm.add('(max-width: 960px)', () => { setStep(STEPS.length - 1) })

      gsap.utils.toArray('.pr-col').forEach((el, i) => {
        gsap.fromTo(el.querySelector('.pr-rule'), { scaleX: 0 }, { scaleX: 1, duration: 1.1, delay: i * 0.12, ease: 'power3.inOut', scrollTrigger: { trigger: el, start: 'top 88%' } })
        gsap.fromTo(el.querySelectorAll('h3, p'), { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.9, delay: 0.2 + i * 0.12, stagger: 0.08, ease: 'power3.out', scrollTrigger: { trigger: el, start: 'top 88%' } })
      })

      // prezzi: le cifre salgono, le righe dell'elenco si disegnano una dopo l'altra
      gsap.utils.toArray('.price').forEach((el) => {
        gsap.fromTo(el.querySelector('.amount'), { yPercent: 60, opacity: 0 }, { yPercent: 0, opacity: 1, duration: 1.1, ease: 'power4.out', scrollTrigger: { trigger: el, start: 'top 80%' } })
        gsap.fromTo(el.querySelectorAll('li'), { opacity: 0, x: -12 }, { opacity: 1, x: 0, duration: 0.7, stagger: 0.08, ease: 'power3.out', scrollTrigger: { trigger: el, start: 'top 75%' } })
      })
    }, root)
    return () => ctx.revert()
  }, [])

  const lines = (arr) => arr.map((t, i) => <span key={i} className="ln"><span>{t}</span></span>)

  return (
    <div className="qt-land" ref={root}>
      <nav className={`qt-nav${nav.glass ? ' is-glass' : ''}${navHidden ? ' hide' : ''}`}><div className="nav-pill">
        <a href="#top" className="brand" aria-label="QUANTO, torna all’inizio"><Wordmark height={14} className="wordmark" /></a>
        <div className="links">
          <a href="#metodo">Metodo</a>
          <a href="#portale">Portale</a>
          <a href="#prezzi">Prezzi</a>
          <a href="#domande">Domande</a>
        </div>
        <div className="actions">
          <button className="nav-login" onClick={() => setModal('login')}>Accedi</button>
          <button className="nav-cta" onClick={() => setModal('register')}>Richiedi accesso</button>
        </div>
      </div></nav>

      <header className="hero" id="top">
        <BgVideo className="hero-img" />
        <div className="hero-shade" aria-hidden="true" />
        <div className="wrap hero-inner">
          <h1>{lines(['La finanza agevolata', 'dello studio,', 'dall’inizio alla fine.'])}</h1>
          <p className="hero-sub after">QUANTO trova le agevolazioni adatte a ogni cliente, ne studia le regole, costruisce il progetto e il budget e li controlla prima della domanda. Agenti che svolgono il lavoro, ogni numero legato alla sua fonte.</p>
          <div className="hero-ctas after">
            <button className="btn-cta big" onClick={() => setModal('register')}>Richiedi accesso<ArrowRight size={15} /></button>
            <a className="hero-link" href="#portale">Guarda il portale<ArrowRight size={14} /></a>
          </div>
        </div>
      </header>

      <section className="sect" id="metodo"><div className="wrap">
        <h2 className="mask-in">{lines(['Tutto il lavoro di una pratica', 'di finanza agevolata.'])}</h2>
        <p className="para fade-in">Il cuore è la pratica: capire a quali agevolazioni ha diritto l’impresa, scrivere il progetto, presentare un budget che regge. L’allocazione delle spese ne è la conseguenza: il budget dice quale agevolazione paga cosa.</p>
        <div className="verbs">
          {VERBS.map(([v, d]) => (
            <div key={v} className="verb">
              <h3 className="verb-word" aria-label={v}><span className="verb-out" aria-hidden="true">{v}</span><span className="verb-fill" aria-hidden="true">{v}</span><i className="verb-line" /></h3>
              <p>{d}</p>
            </div>
          ))}
        </div>
      </div></section>

      <section className="proc" id="processo">
        <div className="proc-pin"><div className="wrap proc-grid">
          <div className="proc-left">
            <h2>Dal primo documento del cliente alla domanda.</h2>
            <ol className="proc-steps">
              <i className="proc-rail" /><i className="proc-progress" />
              {STEPS.map((s, k) => (
                <li key={s.title} className={k === step ? 'on' : k < step ? 'done' : ''}>
                  <span className="pn">{String(k + 1).padStart(2, '0')}</span>
                  <div><h3>{s.title}</h3><p>{s.body}</p></div>
                </li>
              ))}
            </ol>
          </div>
          <div className="proc-right" aria-label="La pratica che si compone">
            <p className="pr-head">Pratica · impresa di prova</p>
            {STEPS.map((s, k) => (
              <div key={s.title} className={`pl${k <= step ? ' in' : ''}${k === step ? ' now' : ''}`}>
                <span className="pl-k">{s.line[0]}</span><span className="pl-v">{s.line[1]}</span>
              </div>
            ))}
            <p className={`pl-end${step === STEPS.length - 1 ? ' in' : ''}`}>Pronta per la domanda.</p>
          </div>
        </div></div>
      </section>

      <section className="sect portal" id="portale"><div className="wrap">
        <div className="agents-intro">
          <div>
            <h2 className="mask-in">{lines(['Quattro agenti.', 'Lo studio decide e firma.'])}</h2>
            <p className="para fade-in">Agevolazioni, Allocazione, Budget e Confronto, in ordine. Ognuno dice cosa ha fatto, cosa ha trovato e cosa gli serve; i numeri li calcolano le regole.</p>
          </div>
          <div className="fade-in"><LoopVideo src="/video/quanto-quattro-agenti.mp4" poster="/landing/quattro-agenti.png" label="I quattro agenti di QUANTO" /></div>
        </div>
        <PortalPreview />
      </div></section>

      <section className="sect tight" id="principi"><div className="wrap principles">
        {[['Deterministico', 'Stessi dati, stesso risultato. Mai un modello che indovina una cifra.'],
          ['Fonti dichiarate', 'Ogni regola cita il testo ufficiale da cui è letta. Ciò che manca resta scritto come lacuna.'],
          ['Verificabile', 'Ogni budget lascia un’impronta firmata: chiunque può controllare che nulla sia cambiato.']].map(([t, b2]) => (
          <div key={t} className="pr-col"><i className="pr-rule" /><h3>{t}</h3><p>{b2}</p></div>
        ))}
      </div></section>

      <section className="sect" id="prezzi"><div className="wrap">
        <h2 className="mask-in">{lines(['Gratuito oggi.', 'Chiaro sempre.'])}</h2>
        <p className="para fade-in">Il lavoro quotidiano è libero. I token si usano solo dove serve un calcolo grande o un consegnabile: il piano di allocazione, la consegna di un budget, lo studio di un bando nuovo. In questa fase di prova nessun token viene scalato e non serve la carta.</p>
        <div className="prices">
          <div className="price">
            <span className="tier">Piano Studio</span>
            <div className="amount-wrap"><div className="amount">209 €<small> al mese</small></div></div>
            <span className="alt">oppure 1.999 € all’anno · 15 token al mese inclusi</span>
            <ul>
              <li>Profilo, documenti, stima, allocazione e controllo del budget: sempre liberi</li>
              <li>Piano di allocazione: da 2 a 4,8 token secondo i dati analizzati (30 giorni per lo stesso lavoro)</li>
              <li>Consegna di un budget: da 1 a 2 token (30 giorni per lo stesso)</li>
              <li>Studio di un bando nuovo: 3 token, 1 torna se la lettura è completa</li>
              <li>+0,5 token per ogni budget pubblicato per tutti</li>
              <li>10 token di benvenuto che non scadono</li>
            </ul>
            <button className="btn-cta big" onClick={() => setModal('register')}>Inizia gratis<ArrowRight size={15} /></button>
          </div>
          <div className="price">
            <span className="tier">Token in più</span>
            <div className="amount-wrap"><div className="amount">25 €<small> ogni 10 token</small></div></div>
            <span className="alt">2,50 € a token</span>
            <ul>
              <li>Quando i token del mese finiscono</li>
              <li>Il lavoro non si ferma: senza token si fermano solo piano, consegne e studi nuovi</li>
              <li>Prima di spendere vedi il costo e il perché; se un calcolo fallisce i token tornano</li>
              <li>Il pagamento online arriverà: oggi le ricariche le elabora il titolare</li>
            </ul>
          </div>
        </div>
      </div></section>

      <section className="sect" id="domande"><div className="wrap split faq-split">
        <div>
          <h2 className="mask-in">{lines(['Domande.'])}</h2>
          <div className="fade-in"><FaqShort /></div>
        </div>
        <div className="fade-in"><AskQuanto /></div>
      </div></section>

      <section className="cta-final">
        <BgVideo className="hero-img still" />
        <div className="hero-shade strong" aria-hidden="true" />
        <div className="wrap">
          <h2 className="mask-in">{lines(['La prossima pratica,', 'preparala con QUANTO.'])}</h2>
          <div className="hero-ctas fade-in"><button className="btn-cta big" onClick={() => setModal('register')}>Richiedi accesso<ArrowRight size={15} /></button></div>
        </div>
      </section>

      <footer className="qt-foot"><div className="wrap row">
        <span className="copy">© 2026 QUANTO</span>
        <button onClick={onVision}>La visione</button>
        <button onClick={onAuditor}><ShieldCheck size={14} />Sei un revisore?</button>
        <span className="sp" />
        <button onClick={() => setModal('login')}><Lock size={13} />Accedi</button>
      </div></footer>

      {modal && <AuthModal mode={modal} onClose={() => setModal(null)} onSwitch={setModal} onDone={onLogin} />}
    </div>
  )
}
