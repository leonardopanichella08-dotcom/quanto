import React, { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { ArrowRight, ArrowUp, Loader2, Lock, ShieldCheck, X } from 'lucide-react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { api, session } from '../lib/api'
import { Wordmark } from './ui'
import { FAQ } from '../data/faq.js'
import { answer } from '../lib/faqSearch'
import './Landing.css'

gsap.registerPlugin(ScrollTrigger)
// su iPhone la barra degli indirizzi cambia l'altezza mentre si scorre: senza questo le animazioni si ricalcolano e la pagina salta
ScrollTrigger.config({ ignoreMobileResize: true })

const SECTIONS = [['metodo', 'Metodo'], ['agenti', 'Agenti'], ['prezzi', 'Prezzi'], ['domande', 'Domande']]

/* Homepage pubblica. Colori del marchio: bianco, nero, giallo #F1E21B. Nessun riquadro, nessuna griglia di schede:
   tipografia, linee, fotografia e movimento. Ogni animazione mostra il lavoro vero di QUANTO; le cifre sono di un esempio e lo dicono.
   Animazioni con GSAP (sempre fromTo con valori finali espliciti); con «riduci movimento» tutto è fermo e leggibile. */

// Visite al sito: una sessione casuale per scheda, la pagina, da dove arriva e i parametri utm. Nessun nome, nessun indirizzo, nessun IP.
function visit(kind, label = '') {
  try {
    let sid = sessionStorage.getItem('quanto_visit')
    if (!sid) { sid = (crypto.randomUUID?.() || String(Math.random()).slice(2) + Date.now()).replace(/[^A-Za-z0-9-]/g, ''); sessionStorage.setItem('quanto_visit', sid) }
    const u = new URLSearchParams(window.location.search)
    api.track({ kind, label, session: sid, path: window.location.pathname, referrer: document.referrer || '', utm_source: u.get('utm_source') || '', utm_medium: u.get('utm_medium') || '',
      utm_campaign: u.get('utm_campaign') || '', device: window.innerWidth < 720 ? 'telefono' : 'computer' })
  } catch { /* la misura non deve mai fermare la pagina */ }
}

const reduced = () => typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches

// ------------------------------------------------------------------------------------------------ accesso
function AuthModal({ mode, onClose, onSwitch, onDone }) {
  const isRegister = mode === 'register'
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [studio, setStudio] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [sent, setSent] = useState(null)                 // richiesta inviata: si aspetta l'approvazione
  // Esc chiude; la pagina sotto non scorre mentre il modulo è aperto (su iPhone scorreva dietro)
  useEffect(() => {
    const key = (e) => { if (e.key === 'Escape') onClose() }
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', key)
    return () => { document.body.style.overflow = prev; window.removeEventListener('keydown', key) }
  }, [onClose])
  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError(null)
    try {
      if (isRegister) { setSent(await api.requestAccess(email.trim(), name.trim(), password, studio.trim())); visit('form', 'richiesta di accesso inviata'); return }
      const res = await api.login(email.trim(), password)
      session.set(res.access_token, res.user)
      onDone(res.user)
    } catch (err) { setError(err.message) } finally { setBusy(false) }
  }
  if (sent) {
    return (
      <div className="qt-modal-backdrop" onClick={onClose}>
        <div className="qt-modal" onClick={(e) => e.stopPropagation()}>
          <button type="button" className="close" onClick={onClose} aria-label="Chiudi"><X className="w-4 h-4" /></button>
          <h3>Richiesta inviata</h3>
          <p className="sub">Controlliamo ogni richiesta a mano. Quando è approvata ti scriviamo a <b>{sent.email}</b>, e potrai entrare con la password che hai appena scelto.</p>
          <ol className="steps">
            <li><span>1</span>Ricevi la nostra richiesta di accesso <em>(fatto)</em></li>
            <li><span>2</span>La approviamo e scegliamo il tuo livello</li>
            <li><span>3</span>Ricevi un’e-mail e premi «Accedi»</li>
          </ol>
          <button type="button" className="submit" onClick={onClose}>Ho capito</button>
        </div>
      </div>
    )
  }
  return (
    <div className="qt-modal-backdrop" onClick={onClose}>
      <form className="qt-modal" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <button type="button" className="close" onClick={onClose} aria-label="Chiudi"><X className="w-4 h-4" /></button>
        <h3>{isRegister ? 'Richiedi accesso' : 'Accedi'}</h3>
        <p className="sub">{isRegister ? 'Compila i dati: la tua richiesta arriva a noi e ti rispondiamo via e-mail. In questa fase è gratuito e non serve la carta di credito.' : 'Usa le credenziali dello studio.'}</p>
        {isRegister && (<><label htmlFor="ln-name">Nome e cognome</label><input id="ln-name" required autoFocus value={name} onChange={(e) => setName(e.target.value)} /></>)}
        <label htmlFor="ln-email">E-mail</label>
        <input id="ln-email" type="email" required autoFocus={!isRegister} autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} />
        {isRegister && (<><label htmlFor="ln-studio">Studio o azienda <span className="opt">(facoltativo)</span></label><input id="ln-studio" value={studio} onChange={(e) => setStudio(e.target.value)} /></>)}
        <label htmlFor="ln-pw">{isRegister ? 'Scegli una password' : 'Password'}</label>
        <input id="ln-pw" type="password" required minLength={isRegister ? 12 : 1} autoComplete={isRegister ? 'new-password' : 'current-password'} value={password} onChange={(e) => setPassword(e.target.value)} />
        {isRegister && <p className="hint">Almeno 12 caratteri, lettere e almeno un numero o simbolo. La userai quando la richiesta sarà approvata.</p>}
        {error && <p className="error">{error}</p>}
        <button disabled={busy || !email || !password || (isRegister && !name)} className="submit">
          {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}{isRegister ? 'Invia la richiesta' : 'Entra'}
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
  { title: 'Il cliente', body: 'Legge i documenti e compila il profilo.', line: ['Profilo', 'Impresa di prova · ATECO 62.01 · profilo al 93%'] },
  { title: 'Le agevolazioni', body: 'Tiene solo ciò che l’impresa può ottenere.', line: ['Agevolazioni', '3 adatte · le escluse con il motivo scritto'] },
  { title: 'Lo studio del bando', body: 'Ogni regola legata al testo da cui viene.', line: ['Regole', '7 regole numeriche, ognuna con la sua fonte'] },
  { title: 'Il progetto e il budget', body: 'Controllato voce per voce con 60 criteri.', line: ['Budget', '60 controlli per voce · cosa passa, cosa va ridotto'] },
  { title: 'La domanda', body: 'Dossier, documenti e registro firmato.', line: ['Consegna', 'dossier · documenti di domanda · registro 7f3a…9b1d'] },
]

// ------------------------------------------------------------------------------------------------ riquadri con immagini sotto il titolo: schermate vere, mascotte, numeri
const TILES = [
  { k: 'team', img: '/landing/quattro-agenti.png', t: 'Quattro agenti.', s: 'Una squadra per ogni pratica.' },
  { k: 'shot', img: '/landing/app-bando-regole.webp', t: 'Le regole, dal testo ufficiale.' },
  { k: 'num', n: 60, t: 'controlli per voce' },
  { k: 'mas', img: '/landing/mascotte-fiuto.webp', t: 'Trova.' },
  { k: 'sig', t: 'Registro firmato.' },
  { k: 'shot2', img: '/landing/app-bando-fonti.webp', t: 'Ogni fonte dichiarata.' },
  { k: 'mas2', img: '/landing/mascotte-spunta.webp', t: 'Controlla.' },
]
function Bento() {
  return (
    <div className="bento" aria-label="QUANTO in sette riquadri">
      {TILES.map((x) => (
        <figure key={x.k} className={`tile tile-${x.k}`}>
          {x.img && <div className="tile-img"><img src={x.img} alt="" loading="eager" decoding="async" /></div>}
          {x.k === 'num' && <span className="tile-n" data-n={x.n}>{x.n}</span>}
          {x.k === 'sig' && <span className="tile-hash" aria-hidden="true">7f3a·e91c·04b2·9b1d</span>}
          <figcaption><b>{x.t}</b>{x.s && <span>{x.s}</span>}</figcaption>
        </figure>
      ))}
    </div>
  )
}


// ------------------------------------------------------------------------------------------------ immagine di sfondo (24/11: sostituisce il video); il telefono scarica la versione piccola
function BgImage({ className, eager = false }) {
  return <img className={className} src="/landing/apertura.webp" srcSet="/landing/apertura-1080.webp 1080w, /landing/apertura.webp 1920w" sizes="100vw"
    alt="" aria-hidden="true" loading={eager ? 'eager' : 'lazy'} fetchPriority={eager ? 'high' : 'auto'} decoding="async" />
}

// ------------------------------------------------------------------------------------------------ i quattro verbi in una riga: una capsula gialla scivola da uno all'altro, la frase cambia sotto
function Verbs() {
  const [i, setI] = useState(0)
  const [pill, setPill] = useState(null)
  const hold = useRef(0)
  const ref = useRef(null)
  const seen = useRef(false)
  const btns = useRef([])
  useEffect(() => {
    if (reduced()) return undefined
    const io = new IntersectionObserver(([e]) => { seen.current = e.isIntersecting }, { threshold: 0.3 })
    if (ref.current) io.observe(ref.current)
    const t = setInterval(() => { if (seen.current && Date.now() - hold.current > 8000) setI((n) => (n + 1) % VERBS.length) }, 3200)
    return () => { clearInterval(t); io.disconnect() }
  }, [])
  // la capsula si misura sulla parola accesa (anche dopo il caricamento dei caratteri e quando la finestra cambia)
  useLayoutEffect(() => {
    const place = () => { const b = btns.current[i]; if (b) setPill({ x: b.offsetLeft, y: b.offsetTop, w: b.offsetWidth, h: b.offsetHeight }) }
    place()
    document.fonts?.ready?.then(place)
    window.addEventListener('resize', place)
    return () => window.removeEventListener('resize', place)
  }, [i])
  return (
    <div className="vs2 fade-in" ref={ref}>
      <div className="vs2-row" role="tablist" aria-label="Cosa fa QUANTO">
        {pill && <i className="vs2-pill" aria-hidden="true" style={{ transform: `translate(${pill.x}px, ${pill.y}px)`, width: pill.w, height: pill.h }} />}
        {VERBS.map(([v], k) => (
          <button key={v} ref={(el) => { btns.current[k] = el }} type="button" role="tab" aria-selected={k === i} className={k === i ? 'on' : ''}
            onClick={() => { hold.current = Date.now(); setI(k) }}>{v}</button>
        ))}
      </div>
      <p className="vs2-text" key={i} aria-live="polite">{VERBS[i][1]}</p>
      <div className="vs2-bar" aria-hidden="true"><i key={`b${i}`} /></div>
    </div>
  )
}

// ------------------------------------------------------------------------------------------------ la pratica: una carta in 3D che segue il mouse e si compone mentre si scorre
function PracticeCard({ step }) {
  const card = useRef(null)
  const move = (e) => {
    if (reduced() || e.pointerType !== 'mouse' || !card.current) return
    const r = e.currentTarget.getBoundingClientRect()
    const x = (e.clientX - r.left) / r.width - 0.5
    const y = (e.clientY - r.top) / r.height - 0.5
    const s = card.current.style
    s.setProperty('--ry', `${(x * 16).toFixed(2)}deg`); s.setProperty('--rx', `${(-y * 12).toFixed(2)}deg`)
    s.setProperty('--mx', `${((x + 0.5) * 100).toFixed(1)}%`); s.setProperty('--my', `${((y + 0.5) * 100).toFixed(1)}%`)
  }
  const leave = () => { const s = card.current?.style; if (s) { s.setProperty('--rx', '0deg'); s.setProperty('--ry', '0deg') } }
  return (
    <div className="pc-stage" onPointerMove={move} onPointerLeave={leave}>
      <div className="pc-card" ref={card} aria-label="La pratica che si compone">
        <p className="pc-head"><span>Pratica · impresa di prova</span><i className="pr-dot" /></p>
        <p className="pc-step" key={step}><b>{String(step + 1).padStart(2, '0')}</b>{STEPS[step].title}</p>
        <div className="pc-rows">
          {STEPS.map((s, k) => (
            <div key={s.title} className={`pl${k <= step ? ' in' : ''}${k === step ? ' now' : ''}`}>
              <span className="pl-k">{s.line[0]}</span><span className="pl-v">{s.line[1]}</span>
            </div>
          ))}
        </div>
        <p className={`pc-end${step === STEPS.length - 1 ? ' in' : ''}`}>Pronta per la domanda.</p>
        <i className="proc-progress" aria-hidden="true" />
      </div>
    </div>
  )
}

// ------------------------------------------------------------------------------------------------ video che scorre come un'animazione
function LoopVideo({ src, poster, label }) {
  const ref = useRef(null)
  useEffect(() => {
    const v = ref.current
    if (!v) return undefined
    v.muted = true; v.defaultMuted = true
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
  const box = useRef(null)
  const ask = (text) => {
    const t = (text ?? q).trim()
    if (!t) return
    setLog((l) => [...l, { q: t, r: answer(t) }])
    setQ('')
  }
  // scorre solo dentro la chat e solo dopo una domanda: prima usava scrollIntoView, che all'apertura portava tutta la pagina giù alle domande
  useEffect(() => {
    const el = box.current
    if (!el || log.length === 0) return
    el.scrollTo({ top: el.scrollHeight, behavior: reduced() ? 'auto' : 'smooth' })
  }, [log])
  return (
    <div className="ask">
      <div className="ask-log" aria-live="polite" ref={box}>
        {log.length === 0 && (
          <div className="ask-start">
            <p className="ask-hint">Chiedi qualcosa su QUANTO.</p>
            <div className="ask-rel">{['Quanto costa?', 'I documenti sono cifrati?', 'Scrive il progetto al posto mio?'].map((s) => <button key={s} type="button" onClick={() => ask(s)}>{s}</button>)}</div>
          </div>
        )}
        {log.map((m, k) => (
          <div key={k} className="ask-turn">
            <p className="ask-q">{m.q}</p>
            {m.r.best ? <p className="ask-a">{m.r.best[1]}</p> : <p className="ask-a muted">Non ho una risposta scritta per questa domanda. Prova con altre parole, per esempio «budget», «de minimis» o «token».</p>}
            {m.r.related.length > 0 && <div className="ask-rel">{m.r.related.map(([rq]) => <button key={rq} type="button" onClick={() => ask(rq)}>{rq}</button>)}</div>}
          </div>
        ))}
      </div>
      <form className="ask-bar" onSubmit={(e) => { e.preventDefault(); ask() }}>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Chiedi a QUANTO…" aria-label="Fai una domanda su QUANTO" enterKeyHint="send" autoComplete="off" />
        <button type="submit" disabled={!q.trim()} aria-label="Invia la domanda"><ArrowUp size={16} /></button>
      </form>
    </div>
  )
}

// I quattro agenti, ognuno con la sua mascotte: l'antenna fiuta le agevolazioni, il cubo divide le spese, la spunta controlla, il doppio confronta.
const AGENTS = [
  { id: 'fiuto', short: 'Trova le misure che spettano all’impresa.', img: '/landing/mascotte-fiuto.webp', name: 'Fiuto', role: 'Agevolazioni', job: 'Ha l’antenna sempre accesa: legge assunzioni e spese dell’impresa e trova le misure che le spettano davvero, crediti d’imposta e incentivi compresi.',
    say: ['Ho letto', 'le 2 assunzioni previste'], found: 'Bonus Giovani: fino a 15.600 €' },
  { id: 'riparto', short: 'Decide quale agevolazione paga quale spesa.', img: '/landing/mascotte-riparto.webp', name: 'Riparto', role: 'Allocazione', job: 'Mette ogni spesa sotto l’agevolazione giusta, rispettando tetti, cumulo e de minimis, senza mai contare due volte la stessa voce.',
    say: ['Ho studiato', '8 bandi aperti'], found: '3 adatti alle spese dell’anno' },
  { id: 'spunta', short: 'Scrive il budget e lo passa ai 60 controlli.', img: '/landing/mascotte-spunta.webp', name: 'Spunta', role: 'Budget', job: 'Scrive la bozza del budget dai documenti e la passa ai 60 controlli prima della domanda: cosa passa, cosa va ridotto, cosa va documentato.',
    say: ['Ho controllato', '60 criteri per voce'], found: '2 voci da ridurre' },
  { id: 'duo', short: 'Confronta bandi e scenari sullo stesso progetto.', img: '/landing/mascotte-duo.webp', name: 'Duo', role: 'Confronto', job: 'Ha due facce perché guarda due strade insieme: confronta bandi e scenari sullo stesso progetto, con lo stesso metodo.',
    say: ['Ho confrontato', '2 bandi sullo stesso budget'], found: 'il primo copre di più' },
]

// Il gestionale vero: due schermate reali della scheda di un bando, che si alternano da sole.
const SHOTS = [
  { src: '/landing/app-bando-regole.webp', tab: 'Le regole', text: 'Ogni bando ha la sua scheda: tipo di aiuto, regole numeriche e controlli che attivano, ognuna con la frase del testo ufficiale da cui è letta.' },
  { src: '/landing/app-bando-fonti.webp', tab: 'Le fonti', text: 'Sotto ogni scheda le fonti consultate: atti citati, documenti ufficiali e data di lettura. Ciò che manca resta scritto come lacuna.' },
]
function RealApp() {
  const [i, setI] = useState(0)
  const hold = useRef(0)
  useEffect(() => {
    if (reduced()) return undefined
    const t = setInterval(() => { if (Date.now() - hold.current > 9000) setI((n) => (n + 1) % SHOTS.length) }, 5500)
    return () => clearInterval(t)
  }, [])
  return (
    <div className="real">
      <div className="real-tabs" role="tablist">
        {SHOTS.map((x, k) => <button key={x.tab} role="tab" aria-selected={k === i} className={k === i ? 'on' : ''} onClick={() => { hold.current = Date.now(); setI(k) }}>{x.tab}<i style={{ animationPlayState: k === i ? 'running' : 'paused' }} key={`${k}-${i}`} /></button>)}
      </div>
      <div className="real-frame">
        <div className="real-bar"><i /><i /><i /><span>quanto · archivio dei bandi</span></div>
        <div className="real-view">{SHOTS.map((x, k) => <img key={x.src} src={x.src} alt={`Schermata reale di QUANTO: ${x.tab.toLowerCase()} di un bando`} className={k === i ? 'on' : ''} loading="lazy" />)}</div>
      </div>
    </div>
  )
}

const VERBS = [
  ['Trova', 'Le agevolazioni che spettano davvero all’impresa.'],
  ['Studia', 'Le regole del bando, dai testi ufficiali.'],
  ['Costruisce', 'Progetto e budget, voce per voce.'],
  ['Controlla', '60 criteri, prima che lo faccia l’ente.'],
]

export default function Landing({ onLogin, onAuditor, onVision, onAgent }) {
  const root = useRef(null)
  const [modal, setModalRaw] = useState(null)
  const setModal = (m) => { if (m === 'register') visit('cta', 'Richiedi accesso'); setModalRaw(m) }
  useEffect(() => {
    visit('view')
    // la pagina si apre sempre in alto, sul titolo: il browser non deve riportarla dove era rimasta l'ultima volta
    if ('scrollRestoration' in history) history.scrollRestoration = 'manual'
    // anche con un indirizzo rimasto come …/#domande (dal menu, poi ricaricato) si riparte dal titolo
    if (window.location.hash === '#richiedi') setModalRaw('register')
    if (window.location.hash) history.replaceState(null, '', window.location.pathname + window.location.search)
    window.scrollTo({ top: 0, behavior: 'instant' })
  }, [])
  const [nav, setNav] = useState({ glass: false, hide: false })
  const [menu, setMenu] = useState(false)
  const [here, setHere] = useState('')
  const [step, setStep] = useState(0)

  // la voce della barra si accende sulla sezione che si sta leggendo
  useEffect(() => {
    const els = SECTIONS.map(([id]) => document.getElementById(id)).filter(Boolean)
    const io = new IntersectionObserver((es) => { es.forEach((e) => { if (e.isIntersecting) setHere(e.target.id) }) }, { rootMargin: '-45% 0px -50% 0px' })
    els.forEach((el) => io.observe(el))
    return () => io.disconnect()
  }, [])
  useEffect(() => {
    if (!menu) return undefined
    const key = (e) => { if (e.key === 'Escape') setMenu(false) }
    window.addEventListener('keydown', key)
    return () => window.removeEventListener('keydown', key)
  }, [menu])

  // navigazione: del tutto trasparente sopra l'apertura animata (solo le scritte), vetro solo dopo l'apertura;
  // sparisce appena si comincia a scendere, così il video resta libero, e torna appena si risale
  useEffect(() => {
    let last = window.scrollY
    const on = () => {
      const y = window.scrollY
      const dir = y > last + 4 ? 'down' : y < last - 4 ? 'up' : null      // la direzione si decide qui, prima che «last» cambi
      last = y
      setNav((n) => {
        const hide = y < 60 ? false : dir === 'down' ? true : dir === 'up' ? false : n.hide
        const glass = y > 40                                          // apertura bianca: il vetro arriva appena si scende
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
      // riquadri: salgono uno dopo l'altro, le immagini scorrono piano dentro la cornice, il 60 conta, la firma si scrive
      gsap.fromTo('.bento .tile', { opacity: 0, y: 48, scale: 0.96 }, { opacity: 1, y: 0, scale: 1, duration: 1.1, ease: 'power4.out', stagger: 0.07, delay: 0.55 })
      gsap.utils.toArray('.bento .tile-img img').forEach((el) => gsap.fromTo(el, { yPercent: -4 }, { yPercent: 4, ease: 'none', scrollTrigger: { trigger: el.closest('.tile'), start: 'top bottom', end: 'bottom top', scrub: true } }))
      const n = document.querySelector('.bento .tile-n')
      if (n) { const o = { v: 0 }; gsap.fromTo(o, { v: 0 }, { v: Number(n.dataset.n), duration: 1.8, delay: 0.9, ease: 'power2.out', onUpdate: () => { n.textContent = Math.round(o.v) } }) }

      gsap.utils.toArray('.mask-in').forEach((el) => gsap.fromTo(el.querySelectorAll('.ln > span'), { yPercent: 110 }, { yPercent: 0, duration: 1.1, ease: 'power4.out', stagger: 0.08, scrollTrigger: { trigger: el, start: 'top 85%' } }))
      gsap.utils.toArray('.fade-in').forEach((el) => gsap.fromTo(el, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 1, ease: 'power3.out', scrollTrigger: { trigger: el, start: 'top 88%' } }))


      const mm = gsap.matchMedia()
      mm.add('(min-width: 961px)', () => {
        ScrollTrigger.create({
          trigger: '.proc', start: 'top top', end: () => `+=${window.innerHeight * 0.42 * STEPS.length}`, pin: '.proc-pin', scrub: true,
          onUpdate: (s) => { setStep(Math.min(STEPS.length - 1, Math.floor(s.progress * STEPS.length))); gsap.set('.proc-progress', { scaleX: s.progress }) },
        })
      })
      mm.add('(max-width: 960px)', () => { setStep(STEPS.length - 1) })

      // la carta della pratica entra inclinata e si raddrizza mentre arriva al centro dello schermo
      gsap.fromTo('.pc-stage', { rotateX: 22, y: 60, opacity: 0.4 }, { rotateX: 0, y: 0, opacity: 1, ease: 'none', scrollTrigger: { trigger: '.proc', start: 'top 85%', end: 'top 15%', scrub: true } })

      gsap.utils.toArray('.pr-col').forEach((el, i) => {
        gsap.fromTo(el.querySelector('.pr-rule'), { scaleX: 0 }, { scaleX: 1, duration: 1.1, delay: i * 0.12, ease: 'power3.inOut', scrollTrigger: { trigger: el, start: 'top 88%' } })
        gsap.fromTo(el.querySelectorAll('h3, p'), { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.9, delay: 0.2 + i * 0.12, stagger: 0.08, ease: 'power3.out', scrollTrigger: { trigger: el, start: 'top 88%' } })
      })

      gsap.fromTo('.agent', { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.9, stagger: 0.12, ease: 'power3.out', scrollTrigger: { trigger: '.agent-row', start: 'top 85%' } })

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
      <nav className={`qt-nav${nav.glass || menu ? ' is-glass' : ''}${navHidden && !menu ? ' hide' : ''}${menu ? ' menu-open' : ''}`}><div className="nav-pill">
        <a href="#top" className="brand" aria-label="QUANTO, torna all’inizio" onClick={() => setMenu(false)}><Wordmark height={14} className="wordmark" /></a>
        <div className="links">
          {SECTIONS.map(([id, t]) => <a key={id} href={`#${id}`} className={here === id ? 'on' : ''} aria-current={here === id ? 'true' : undefined}>{t}</a>)}
        </div>
        <div className="actions">
          <button className="nav-login" onClick={() => setModal('login')}>Accedi</button>
          <button className="nav-cta" onClick={() => setModal('register')}>Richiedi accesso</button>
          <button className="nav-burger" aria-label={menu ? 'Chiudi il menu' : 'Apri il menu'} aria-expanded={menu} aria-controls="qt-menu" onClick={() => setMenu((m) => !m)}><i /><i /></button>
        </div>
      </div>
      <div id="qt-menu" className={`nav-sheet${menu ? ' open' : ''}`} aria-hidden={!menu}>
        {SECTIONS.map(([id, t], k) => <a key={id} href={`#${id}`} tabIndex={menu ? 0 : -1} style={{ transitionDelay: menu ? `${0.04 * k + 0.05}s` : '0s' }} onClick={() => setMenu(false)}>{t}<ArrowRight size={18} /></a>)}
        <button type="button" tabIndex={menu ? 0 : -1} className="sheet-login" onClick={() => { setMenu(false); setModal('login') }}><Lock size={14} />Accedi</button>
      </div></nav>
      {menu && <div className="nav-scrim" onClick={() => setMenu(false)} aria-hidden="true" />}

      <header className="hero" id="top">
        <div className="wrap hero-inner">
          <h1>{lines(['La finanza agevolata,', 'dall’inizio alla fine.'])}</h1>
          <p className="hero-sub after">Quattro agenti. Ogni numero con la sua fonte.</p>
          <div className="hero-ctas after">
            <button className="btn-cta big" onClick={() => setModal('register')}>Richiedi accesso<ArrowRight size={15} /></button>
            <a className="hero-link" href="#agenti">Conosci gli agenti<ArrowRight size={14} /></a>
          </div>
        </div>
        <div className="wrap"><Bento /></div>
      </header>

      <section className="sect" id="metodo"><div className="wrap">
        <h2 className="mask-in">{lines(['Tutto il lavoro di una pratica', 'di finanza agevolata.'])}</h2>
        <Verbs />
      </div></section>

      <section className="sect real-sect" id="gestionale"><div className="wrap split real-split">
        <div>
          <h2 className="mask-in">{lines(['Il gestionale,', 'com’è davvero.'])}</h2>
        </div>
        <div className="fade-in"><RealApp /></div>
      </div></section>

      <section className="proc" id="processo">
        <div className="proc-pin"><div className="wrap proc-grid">
          <h2 className="proc-title">Dal primo documento del cliente alla domanda.</h2>
          <PracticeCard step={step} />
        </div></div>
      </section>

      <section className="sect agents" id="agenti"><div className="wrap">
        <div className="team">
          <h2 className="mask-in">{lines(['Quattro agenti.', 'Una squadra per ogni pratica.'])}</h2>
        </div>
        <ol className="agent-row">
          {AGENTS.map((g, k) => (
            <li key={g.name} className="agent">
              <div className="agent-pic"><img src={g.img} alt={`${g.name}, l’agente ${g.role}`} loading="lazy" style={{ animationDelay: `${k * 0.4}s` }} /></div>
              <p className="agent-n"><span>{k + 1}</span>{g.role}</p>
              <h3>{g.name}</h3>
              <p className="agent-job">{g.short}</p>
              <button className="agent-more" onClick={() => onAgent?.(g.id)} aria-label={`Come lavora ${g.name}`}>Come lavora<ArrowRight size={13} /></button>
            </li>
          ))}
        </ol>
        <div className="agents-video">
          <div className="fade-in"><LoopVideo src="/video/quanto-quattro-agenti.mp4" poster="/landing/quattro-agenti.png" label="I quattro agenti di QUANTO al lavoro" /></div>
          <div className="fade-in">
            <h3>Guardali lavorare.</h3>
          </div>
        </div>
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
        <p className="price-note fade-in"><i />Gratis durante la prova. Nessuna carta.</p>
        <div className="prices">
          <div className="price">
            <span className="tier">Piano Studio</span>
            <div className="amount-wrap"><div className="amount">209 €<small> al mese</small></div></div>
            <span className="alt">oppure 1.999 € all’anno · 15 token al mese inclusi</span>
            <ul>
              <li>Lavoro quotidiano sempre libero</li>
              <li>Piano di allocazione · 2–4,8 token</li>
              <li>Consegna di un budget · 1–2 token</li>
              <li>Studio di un bando nuovo · 3 token</li>
              <li>10 token di benvenuto</li>
            </ul>
            <button className="btn-cta" onClick={() => setModal('register')}>Inizia gratis<ArrowRight size={14} /></button>
          </div>
          <div className="price price-alt">
            <span className="tier">Token in più</span>
            <div className="amount-wrap"><div className="amount">25 €<small> ogni 10 token</small></div></div>
            <span className="alt">2,50 € a token</span>
            <ul>
              <li>Quando finiscono quelli del mese</li>
              <li>Vedi il costo prima di spendere</li>
              <li>Se un calcolo fallisce, tornano</li>
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
        <BgImage className="hero-img still" />
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
