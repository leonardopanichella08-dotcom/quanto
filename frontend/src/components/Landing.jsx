import React, { useEffect, useMemo, useRef, useState } from 'react'
import { ArrowRight, Check, FileText, Link2, Loader2, Lock, ShieldCheck, Table2, X } from 'lucide-react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { api, session } from '../lib/api'
import { Mark, Wordmark } from './ui'
import { REVIEWS } from './landingReviews'
import './Landing.css'
import { LaunchVideo } from './TutorialVideo'

gsap.registerPlugin(ScrollTrigger)

const eur = (n) => n.toLocaleString('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const reducedMotion = () => typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches

const CELL_COLOR = { OK: '#10b981', ADJUSTED: '#f59e0b', REJECTED: '#ef4444', WAIT: '#38bdf8', NONE: '#F6F2E21f' }
// esempio fisso (non è un bando reale): illustra la distribuzione tipica di un controllo a 60 criteri
const DEMO_OUTCOMES = [
  'OK', 'OK', 'OK', 'ADJUSTED', 'OK', 'OK', 'OK', 'REJECTED', 'OK', 'OK', 'OK', 'OK', 'WAIT', 'OK', 'OK',
  'OK', 'OK', 'NONE', 'OK', 'OK', 'OK', 'ADJUSTED', 'OK', 'OK', 'NONE', 'OK', 'OK', 'OK', 'OK', 'OK',
  'OK', 'ADJUSTED', 'OK', 'OK', 'OK', 'NONE', 'OK', 'REJECTED', 'OK', 'OK', 'OK', 'OK', 'OK', 'NONE', 'OK',
  'OK', 'OK', 'OK', 'WAIT', 'OK', 'OK', 'OK', 'NONE', 'OK', 'OK', 'ADJUSTED', 'OK', 'OK', 'OK', 'OK',
]
const MINI_HEAT = ['OK', 'OK', 'ADJUSTED', 'OK', 'OK', 'OK', 'OK', 'REJECTED', 'OK', 'OK', 'OK', 'OK', 'OK', 'OK', 'WAIT', 'OK', 'OK', 'OK']

// ------------------------------------------------------------------------------------------------ catena di blocchi (decorazione delle sezioni scure)
function mulberry32(seed) {
  let a = seed
  return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296 }
}
const HEX = '0123456789abcdef'
const hexStr = (rnd, n) => Array.from({ length: n }, () => HEX[Math.floor(rnd() * 16)]).join('')

/** Una catena di blocchi firmati, come il registro vero di QUANTO: ogni blocco porta un'impronta e si lega al precedente. */
function ChainField({ rows = 3, perRow = 7, seed = 7, variant = '' }) {
  const { blocks, links, active } = useMemo(() => {
    const rnd = mulberry32(seed)
    const w = 1200, h = 460
    const bx = Array.from({ length: rows }, (_, r) => {
      const y = (h / (rows + 1)) * (r + 1) + (rnd() - 0.5) * 30
      const offset = (rnd() - 0.5) * 60
      return Array.from({ length: perRow }, (_, i) => ({ id: `${r}-${i}`, x: offset + (w / (perRow - 0.4)) * (i + 0.4) + (rnd() - 0.5) * 24, y: y + (rnd() - 0.5) * 18, hex: hexStr(rnd, 4) }))
    })
    const flat = bx.flat()
    const lk = bx.flatMap((row) => row.slice(1).map((p, i) => [row[i], p]))
    const act = [flat[4], flat[Math.floor(flat.length / 2)], flat[flat.length - 5]].filter(Boolean).map((p, i) => ({ ...p, color: ['#F1E21B', '#10b981', '#38bdf8'][i], delay: i * 0.7 }))
    return { blocks: flat, links: lk, active: act }
  }, [rows, perRow, seed])
  return (
    <svg className={`chain-field ${variant}`} viewBox="0 0 1200 460" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      {links.map(([a, b], i) => <line key={i} x1={a.x + 18} y1={a.y} x2={b.x - 18} y2={b.y} stroke="#F6F2E2" strokeOpacity="0.1" strokeWidth="1" strokeDasharray="2 3" />)}
      {blocks.map((p) => (
        <g key={p.id} transform={`translate(${p.x}, ${p.y})`} opacity="0.55">
          <rect x="-17" y="-10" width="34" height="20" rx="4" fill="none" stroke="#F6F2E2" strokeOpacity="0.3" />
          <text x="0" y="4" textAnchor="middle" fontSize="6.5" fontFamily="JetBrains Mono, monospace" fill="#F6F2E2" fillOpacity="0.45">{p.hex}</text>
        </g>
      ))}
      {active.map((p, i) => (
        <g key={i} transform={`translate(${p.x}, ${p.y})`}>
          <rect x="-17" y="-10" width="34" height="20" rx="4" fill="none" stroke={p.color} strokeWidth="1.3" className="block-pulse" style={{ '--d': `${p.delay}s` }} />
          <text x="0" y="4" textAnchor="middle" fontSize="6.5" fontFamily="JetBrains Mono, monospace" fill={p.color}>{p.hex}</text>
        </g>
      ))}
    </svg>
  )
}

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
        <h3>{isRegister ? 'Inizia gratis' : 'Accedi'}</h3>
        <p className="sub">{isRegister ? 'Un account, nessuna carta di credito. Puoi cominciare subito.' : 'Bentornato: usa le tue credenziali.'}</p>
        {isRegister && (<><label htmlFor="ln-name">Nome</label><input id="ln-name" required autoFocus value={name} onChange={(e) => setName(e.target.value)} /></>)}
        <label htmlFor="ln-email">E-mail</label>
        <input id="ln-email" type="email" required autoFocus={!isRegister} autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} />
        <label htmlFor="ln-pw">Password</label>
        <input id="ln-pw" type="password" required minLength={isRegister ? 12 : 1} autoComplete={isRegister ? 'new-password' : 'current-password'} value={password} onChange={(e) => setPassword(e.target.value)} />
        {isRegister && <p className="hint">Almeno 12 caratteri, lettere e almeno un numero o simbolo.</p>}
        {error && <p className="error">{error}</p>}
        <button disabled={busy || !email || !password || (isRegister && !name)} className="btn-solid submit">
          {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ArrowRight className="w-3.5 h-3.5" />}{isRegister ? 'Crea account' : 'Entra'}
        </button>
        <p className="switch">
          {isRegister ? <>Hai già un account? <button type="button" onClick={() => onSwitch('login')}>Accedi</button></> : <>Non hai un account? <button type="button" onClick={() => onSwitch('register')}>Iscriviti gratis</button></>}
        </p>
      </form>
    </div>
  )
}

// ------------------------------------------------------------------------------------------------ animazioni: si accendono quando la grafica entra in vista
/** Vero appena l'elemento entra in vista (una volta sola). Con «riduci movimento» è subito vero. */
function useInView(ref, threshold = 0.35) {
  const [seen, setSeen] = useState(false)
  useEffect(() => {
    if (reducedMotion() || typeof IntersectionObserver === 'undefined') { setSeen(true); return undefined }
    const el = ref.current
    if (!el) return undefined
    const io = new IntersectionObserver(([en]) => { if (en.isIntersecting) { setSeen(true); io.disconnect() } }, { threshold })
    io.observe(el)
    return () => io.disconnect()
  }, [ref, threshold])
  return seen
}

/** Numero che cresce fino al valore quando la grafica è «accesa»; si azzera quando si spegne, così riparte da capo. */
function CountUp({ to, live, decimals = 2, suffix = '', duration = 1.7 }) {
  const [v, setV] = useState(reducedMotion() ? to : 0)
  useEffect(() => {
    if (reducedMotion()) { setV(to); return undefined }
    if (!live) { setV(0); return undefined }
    const o = { v: 0 }
    const tw = gsap.to(o, { v: to, duration, delay: 0.25, ease: 'power3.out', onUpdate: () => setV(o.v) })
    return () => tw.kill()
  }, [live, to, duration])
  return <>{v.toLocaleString('it-IT', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}{suffix}</>
}

// ------------------------------------------------------------------------------------------------ mini-finestre desktop (stile precedente)
const Chrome = ({ url }) => <div className="chrome"><i /><i /><i />{url && <span className="url">{url}</span>}</div>

/** Mini-finestra: le sue righe e barre si animano quando entra in vista. */
function MW({ tilt = '-1deg', compact, url, children }) {
  const ref = useRef(null)
  const live = useInView(ref)
  return <div ref={ref} className={`mini-window${compact ? ' compact' : ''}${live ? ' live' : ''}`} style={{ '--tilt': tilt }}><Chrome url={url} />{children}</div>
}
const ix = (i) => ({ '--i': i })

function DeterministicMockup() {
  return (
    <MW compact tilt="0.8deg">
      <div className="mw-body">
        <div className="mw-run" style={ix(0)}><span>Esecuzione di lunedì</span><span className="mono">a7f3…9c1e</span></div>
        <div className="mw-run" style={ix(1)}><span>Esecuzione di venerdì</span><span className="mono">a7f3…9c1e</span></div>
        <span className="ok-badge" style={ix(2)}><Check className="w-3.5 h-3.5" />Impronta identica</span>
      </div>
    </MW>
  )
}
function SourceMockup() {
  return (
    <MW compact tilt="-0.6deg">
      <div className="mw-body">
        <div className="mw-rule-line" style={ix(0)}><span className="rule-k">Consulenze</span><span className="rule-v mono">max 20%</span></div>
        <p className="mw-src" style={ix(1)}>Fonte: Art. 25, D.L. 18 ottobre 2012, n. 179, conv. L. 17 dicembre 2012, n. 221</p>
      </div>
    </MW>
  )
}
function HashMockup() {
  return (
    <MW compact tilt="1.2deg">
      <div className="mw-body">
        <div className="mw-hash" style={ix(0)}>0x7f3a9c1e5b8d2f4a…<br />6c0e9b1d3a7f5c2e</div>
        <span className="mw-badge" style={ix(2)}><ShieldCheck className="w-3.5 h-3.5" />Firmato e verificabile</span>
      </div>
    </MW>
  )
}
function ClientsMockup() {
  const rows = [['Meridiana Digital Solutions', 'ATECO 62.01'], ['Officine Valtellina', 'ATECO 25.62'], ['Agritech Lomellina', 'ATECO 01.13'], ['Ferro & Figli Carpenterie', 'ATECO 25.11']]
  return (
    <MW tilt="-1.2deg" url="quanto.app/clienti">
      <div className="mw-body" style={{ minHeight: 'auto' }}>
        {rows.map(([n, a], i) => <div key={n} className="mw-line" style={ix(i)}><span className="dot" style={{ background: '#F1E21B' }} />{n}<span className="amt">{a}</span></div>)}
      </div>
    </MW>
  )
}
function HeatMockup() {
  return (
    <MW tilt="1deg" url="quanto.app/budget">
      <div className="mw-body" style={{ minHeight: 'auto' }}><div className="mw-heat">{MINI_HEAT.map((o, i) => <i key={i} style={{ background: CELL_COLOR[o], '--i': i }} />)}</div></div>
    </MW>
  )
}
function AllocationMockup() {
  return (
    <MW tilt="-1deg" url="quanto.app/allocazione">
      <div className="mw-body" style={{ minHeight: 'auto' }}>
        <div className="mw-bar"><span style={{ width: '62%', background: '#F1E21B', '--i': 0 }}>Bandi · 62%</span><span style={{ width: '38%', background: 'var(--d-line)', color: 'var(--d-ink)', '--i': 1 }}>Ente · 38%</span></div>
        <div className="mw-bar-labels"><span>€ 0</span><span>€ 1.991.026</span></div>
      </div>
    </MW>
  )
}

// ------------------------------------------------------------------------------------------------ pannelli di «come funziona» (qui sì, vetro: sono le funzioni di QUANTO)
// Ogni pannello riceve `live`: quando diventa vero le barre si riempiono, le righe compaiono una dopo l'altra e i numeri crescono.
function PanelDocs({ live }) {
  const rows = ['Conto economico', 'Stato patrimoniale', 'F24 · versamenti e crediti', 'Visura · ATECO e sede']
  return (
    <div className={`panel${live ? ' live' : ''}`}>
      <div className="p-label">LETTURA AUTOMATICA</div>
      <div className="p-bar"><i style={ix(0)} /></div>
      {rows.map((r, i) => <div key={r} className="p-row" style={ix(i + 1)}><span>{r}</span><span className="ok"><Check size={13} />letto</span></div>)}
    </div>
  )
}
function PanelForecast({ live }) {
  const rows = [['Personale', 1.0, 0.99], ['Consulenze', 0.24, 0.23], ['Spese generali', 0.2, 0.19], ['Beni strumentali', 0.13, 0.13], ['Formazione', 0.03, 0.02]]
  return (
    <div className={`panel${live ? ' live' : ''}`}>
      <div className="p-label">SPESE PER CATEGORIA · BILANCIO CONTRO STIMA</div>
      {rows.map(([l, a, b], i) => <div key={l} className="p-pair" style={ix(i)}><span>{l}</span><div><i className="a" style={{ width: `${b * 100}%` }} /><i className="b" style={{ width: `${a * 100}%` }} /></div></div>)}
      <div className="p-legend p-late"><span><i className="a" />bilancio 2025</span><span><i className="b" />stima 2027</span></div>
    </div>
  )
}
function PanelBandi({ live }) {
  const rows = [['Horizon Europe', 'Adatto'], ['Investimenti Sostenibili 4.0', 'Adatto'], ['Transizione 5.0', 'Adatto'], ['Nuova Sabatini', 'Adatto'], ['Bando regionale', 'Da verificare']]
  return (
    <div className={`panel${live ? ' live' : ''}`}>
      <div className="p-label">BANDI ADATTI ALL'AZIENDA</div>
      {rows.map(([n, f], i) => <div key={n} className="p-row" style={ix(i)}><span>{n}</span><span className={`pill ${f === 'Adatto' ? 'g' : 'a'}`}>{f}</span></div>)}
    </div>
  )
}
function PanelAlloc({ live }) {
  const rows = [['Personale', 0.05], ['Consulenze', 0.12], ['Spese generali', 0], ['Beni strumentali', 0.2], ['Formazione', 0.1]]
  return (
    <div className={`panel${live ? ' live' : ''}`}>
      <div className="p-label">SPESE DELL’ANNO · BANDI SENZA PROGETTO · ESEMPIO</div>
      <div className="p-big"><CountUp to={148349.41} live={live} suffix=" €" /></div>
      <div className="p-sub">su 2.100.185,69 € di spese · quota coperta <CountUp to={7.1} live={live} decimals={1} suffix="%" /></div>
      {rows.map(([l, v], i) => <div key={l} className="p-cov" style={ix(i + 1)}><span>{l}</span><div><i style={{ width: `${v * 100}%` }} /></div></div>)}
      <span className="pill v p-late">De minimis · stimato dai bilanci</span>
    </div>
  )
}
function PanelDossier({ live }) {
  return (
    <div className={`panel${live ? ' live' : ''}`}>
      <div className="p-label">CONSEGNA</div>
      <div className="p-out" style={ix(0)}><FileText size={20} /><div><b>Dossier</b><span>PDF con ogni numero e la sua fonte</span></div></div>
      <div className="p-out" style={ix(1)}><Table2 size={20} /><div><b>Budget</b><span>Template per bando, pronto da compilare</span></div></div>
      <div className="p-out" style={ix(2)}><Link2 size={20} /><div><b>Registro firmato</b><span>Catena di impronte verificabile</span></div></div>
      <div className="p-hash p-late">0x7f3a9c1e5b8d2f4a…6c0e9b1d3a7f5c2e</div>
    </div>
  )
}

/** Pannello nella versione per schermi stretti: si accende quando scorrendo entra in vista. */
function InlinePanel({ Panel }) {
  const ref = useRef(null)
  const live = useInView(ref, 0.4)
  return <div ref={ref}><Panel live={live} /></div>
}

const STEPS = [
  { n: '01', title: 'Carichi i documenti', body: 'Bilanci, F24, visura, buste paga: QUANTO li legge voce per voce e compila il profilo dell’azienda.', Panel: PanelDocs, url: 'quanto.app/documenti' },
  { n: '02', title: 'Stima l’anno successivo', body: 'Parte dall’ultimo bilancio e applica la variazione che risulta dai tuoi dati, con la spiegazione di ogni percentuale.', Panel: PanelForecast, url: 'quanto.app/allocazione/2' },
  { n: '03', title: 'Trova i bandi adatti', body: 'Confronta l’azienda con la biblioteca dei bandi. Quello che il bando non dice resta dichiarato, mai inventato.', Panel: PanelBandi, url: 'quanto.app/bandi' },
  { n: '04', title: 'Assegna le spese ai bandi', body: 'Per le spese dell’anno o per un progetto, senza pagare due volte la stessa spesa, con tetti, cumulo e de minimis.', Panel: PanelAlloc, url: 'quanto.app/allocazione/4' },
  { n: '05', title: 'Consegna dossier e registro', body: 'Un dossier PDF, il budget per bando e un registro firmato che prova che i numeri non sono stati toccati.', Panel: PanelDossier, url: 'quanto.app/dossier' },
]

const PILLARS = [
  ['Legge i documenti', 'Bilanci, F24, visure e buste paga diventano dati, con la pagina da cui vengono.'],
  ['Stima l’anno', 'Previsione di bilancio per categoria di spesa, spiegata voce per voce.'],
  ['Trova i bandi', 'Una biblioteca di bandi studiati dalle fonti ufficiali.'],
  ['Assegna le spese ai bandi', 'Quale bando paga cosa, per le spese dell’anno o per un progetto, senza contare due volte la stessa spesa.'],
]

const FUNCS = ['Lettura dei documenti', 'Profilo azienda', 'Previsione di bilancio', 'Biblioteca dei bandi', 'Allocazione ottimale', 'De minimis automatico', 'Budget per bando', 'Dossier PDF', 'Registro firmato', 'Assistente interno']

const STATEMENT = [['Nessuna', 0], ['stima', 0], ['aleatoria.', 0], ['Nessun', 0], ['testo', 0], ['inventato.', 0], ['Solo', 0], ['regole', 1], ['ufficiali,', 1], ['applicate', 0], ['in', 0], ['modo', 0], ['deterministico.', 0]]

export default function Landing({ onLogin, onAuditor, onVision }) {
  const root = useRef(null)
  const [modal, setModal] = useState(null)
  const [active, setActive] = useState(0)
  const reduce = reducedMotion()

  useEffect(() => {
    let off = () => {}
    const ctx = gsap.context(() => {
      const nav = root.current.querySelector('.qt-nav')
      ScrollTrigger.create({ start: 24, end: 99999, onUpdate: (s) => nav.classList.toggle('solid', s.scroll() > 24) })
      if (reduce) return

      const tl = gsap.timeline({ defaults: { ease: 'power4.out' } })
      tl.from('.hero h1 .w > span', { yPercent: 115, duration: 1.1, stagger: 0.06 })
        .from('.hero .sub', { y: 22, opacity: 0, duration: 0.9 }, '-=0.7')
        .from('.hero .ctas > *', { y: 18, opacity: 0, duration: 0.8, stagger: 0.1 }, '-=0.6')
        .from('.hero .window', { y: 90, opacity: 0, duration: 1.4 }, '-=0.9')
        .from('.hero .heat-cell', { scale: 0, opacity: 0, duration: 0.5, ease: 'back.out(2)', stagger: { each: 0.012, from: 'start' } }, '-=0.9')
        .from('.hero .float', { y: 50, opacity: 0, duration: 1, stagger: 0.15 }, '-=1.2')
        .add(() => { const o = { v: 0 }; const el = root.current.querySelector('.n46'); gsap.to(o, { v: 46, duration: 1.8, ease: 'power3.out', onUpdate: () => { if (el) el.textContent = Math.round(o.v) } }) }, '-=1.4')

      // la finestra del hero oscilla piano nello spazio e segue il mouse; le finestrelle laterali scorrono a profondità diverse
      gsap.set('.hero .window-tilt', { rotateX: 6, rotateY: -6 })
      gsap.to('.hero .window-tilt', { rotateY: 6, rotateX: 3, duration: 6, ease: 'sine.inOut', yoyo: true, repeat: -1 })
      gsap.to('.hero .float.l', { yPercent: -28, ease: 'none', scrollTrigger: { trigger: '.window-wrap', start: 'top bottom', end: 'bottom top', scrub: 1 } })
      gsap.to('.hero .float.r', { yPercent: 22, ease: 'none', scrollTrigger: { trigger: '.window-wrap', start: 'top bottom', end: 'bottom top', scrub: 1 } })
      const win = root.current.querySelector('.window-wrap')
      const onMove = (e) => {
        const r = win.getBoundingClientRect()
        const x = (e.clientX - (r.left + r.width / 2)) / window.innerWidth, y = (e.clientY - (r.top + r.height / 2)) / window.innerHeight
        gsap.to('.hero .window-mouse', { rotateY: x * 14, rotateX: -y * 8, duration: 0.9, ease: 'power3.out' })
      }
      window.addEventListener('pointermove', onMove, { passive: true })
      off = () => window.removeEventListener('pointermove', onMove)

      // striscia delle funzioni: scorre piano e accelera un poco con lo scroll
      const track = gsap.to('.ticker-track', { xPercent: -50, duration: 70, ease: 'none', repeat: -1 })
      ScrollTrigger.create({ start: 0, end: 'max', onUpdate: (s) => {
        const boost = Math.min(5, 1 + Math.abs(s.getVelocity()) / 700)
        gsap.to(track, { timeScale: boost, duration: 0.25, overwrite: true, onComplete: () => gsap.to(track, { timeScale: 1, duration: 1.4 }) })
      } })

      gsap.utils.toArray('.reveal').forEach((el) => gsap.from(el, { y: 40, opacity: 0, duration: 0.9, ease: 'power3.out', scrollTrigger: { trigger: el, start: 'top 88%' } }))
      ScrollTrigger.batch('.reveal-card', { start: 'top 90%', onEnter: (els) => { els.forEach((e) => e.classList.add('in')); gsap.from(els, { y: 44, opacity: 0, duration: 0.85, stagger: 0.09, ease: 'power3.out', overwrite: true }) } })

      // la frase si «accende» parola per parola
      gsap.fromTo('.statement .sw', { opacity: 0.16 }, { opacity: 1, stagger: 0.1, ease: 'none', scrollTrigger: { trigger: '.statement', start: 'top 72%', end: 'bottom 55%', scrub: true } })
      gsap.fromTo('.statement .hl', { backgroundSize: '0% 0.62em' }, { backgroundSize: '100% 0.62em', ease: 'none', scrollTrigger: { trigger: '.statement', start: 'top 45%', end: 'bottom 50%', scrub: true } })

      // «come funziona»: la sezione resta ferma e i cinque passi scorrono
      const mm = gsap.matchMedia()
      mm.add('(min-width: 900px)', () => {
        ScrollTrigger.create({
          trigger: '.how', start: 'top top', end: () => `+=${window.innerHeight * 0.65 * STEPS.length}`, pin: '.how-pin', scrub: true,
          onUpdate: (s) => setActive(Math.min(STEPS.length - 1, Math.floor(s.progress * STEPS.length))),
        })
      })

      gsap.utils.toArray('.count').forEach((el) => {
        const to = Number(el.dataset.to); const o = { v: 0 }
        gsap.to(o, { v: to, duration: 1.6, ease: 'power2.out', onUpdate: () => { el.textContent = Math.round(o.v) }, scrollTrigger: { trigger: el, start: 'top 92%', once: true } })
      })
    }, root)
    return () => { off(); ctx.revert() }
  }, [reduce])

  const split = (nodes) => nodes.map((w, i) => <span key={i} className="w"><span>{w}</span></span>)

  return (
    <div className="qt-land" ref={root}>
      <nav className="qt-nav"><div className="wrap row">
        <div className="brand"><Mark size={30} /><Wordmark height={17} className="wordmark-mask" /></div>
        <div className="links">
          <a href="#cosa-fa">Cosa fa</a>
          <a href="#come-funziona">Come funziona</a>
          <a href="#strumenti">Strumenti</a>
          <a href="#prezzi">Prezzi</a>
          <button onClick={onVision}>La visione</button>
        </div>
        <div className="actions">
          <button className="btn-ghost" onClick={() => setModal('login')}>Accedi</button>
          <button className="btn-solid" onClick={() => setModal('register')}>Inizia gratis</button>
        </div>
      </div></nav>

      <header className="hero">
        <div className="hero-bg" aria-hidden="true"><i className="grid" /></div>
        <div className="wrap hero-inner">
          <h1>{split(['Il', 'motore', 'di', 'calcolo', 'per', 'la', <mark key="m">finanza agevolata.</mark>])}</h1>
          <p className="sub">Dai bilanci dei tuoi clienti ai bandi giusti, con ogni numero spiegato.</p>
          <div className="ctas">
            <button className="btn-solid big" onClick={() => setModal('register')}>Inizia gratis<ArrowRight size={16} /></button>
            <a className="btn-line big" href="#come-funziona">Come funziona</a>
          </div>

          <div className="window-wrap">
            <div className="float l"><AllocationMockup /></div>
            <div className="float r"><DeterministicMockup /></div>
            <div className="window-mouse"><div className="window-tilt">
              <div className="depth" />
              <div className="window">
                <Chrome url="quanto.app/budget" />
                <div className="body">
                  <div className="top"><span className="name">Beni strumentali — Nuova Sabatini</span><span className="score mono"><b className="n46">46</b>/60 superati</span></div>
                  <div className="heat-grid">{DEMO_OUTCOMES.map((o, i) => <div key={i} className="heat-cell" style={{ background: CELL_COLOR[o], '--d': `${((Math.floor(i / 15) + (i % 15)) * 0.11).toFixed(2)}s` }} title={`#${i + 1}`} />)}</div>
                  <div className="heat-legend">
                    <span><i style={{ background: CELL_COLOR.OK }} />superato</span>
                    <span><i style={{ background: CELL_COLOR.ADJUSTED }} />ridotto</span>
                    <span><i style={{ background: CELL_COLOR.REJECTED }} />respinto</span>
                    <span><i style={{ background: CELL_COLOR.WAIT }} />da documentare</span>
                    <span><i style={{ background: CELL_COLOR.NONE }} />non valutato</span>
                  </div>
                </div>
              </div>
            </div></div>
          </div>
        </div>
      <div className="ticker" aria-label="Le funzioni di QUANTO">
        <div className="ticker-track">{[0, 1].map((k) => <div key={k} className="ticker-set" aria-hidden={k === 1}>{FUNCS.map((f) => <span key={f} className="ticker-item">{f}</span>)}</div>)}</div>
      </div>
      </header>

      <section className="sect" id="video"><div className="wrap">
        <div className="sect-head center reveal"><span className="kicker">In 40 secondi</span><h2>Guarda QUANTO al lavoro</h2></div>
        <LaunchVideo />
      </div></section>

      <section className="sect" id="cosa-fa"><div className="wrap">
        <div className="sect-head reveal"><span className="kicker">Cosa fa</span><h2>Dal bilancio ai bandi giusti, in un solo posto</h2></div>
        <div className="pillars">
          {PILLARS.map(([t, b], i) => (
            <div key={t} className="pillar reveal-card"><span className="step-n">{i + 1}</span><h3>{t}</h3><p>{b}</p></div>
          ))}
        </div>
      </div></section>

      <section className="statement"><div className="wrap">
        <p>{STATEMENT.map(([w, hl], i) => <span key={i} className={`sw${hl ? ' hl' : ''}`}>{w} </span>)}</p>
      </div></section>

      <section className="how dark" id="come-funziona">
        <div className="how-pin"><div className="wrap how-grid">
          <div className="how-left">
            <span className="kicker">Come funziona</span>
            <h2>Cinque passi, nessun foglio Excel in mezzo</h2>
            <ol className="how-steps">
              {STEPS.map((s, i) => (
                <li key={s.n} className={i === active ? 'on' : ''}>
                  <span className="n">{s.n}</span>
                  <div><h3>{s.title}</h3><p>{s.body}</p><div className="inline-panel"><div className="glass win-glass"><InlinePanel Panel={s.Panel} /></div></div></div>
                </li>
              ))}
            </ol>
          </div>
          <div className="how-right">
            <div className="how-stage">{STEPS.map((s, i) => (
              <div key={s.n} className={`how-panel ${i === active ? 'on' : ''}`}>
                <div className="how-window"><div className="depth" /><Chrome url={s.url} /><div className="glass win-glass"><s.Panel live={i === active} /></div></div>
              </div>
            ))}</div>
          </div>
        </div></div>
      </section>

      <section className="sect" id="strumenti"><div className="wrap">
        <div className="sect-head reveal"><span className="kicker">Gli strumenti</span><h2>Tutto quello che serve per un cliente, già collegato</h2>
          <p>Un account per lo studio, un flusso dedicato per ogni azienda cliente. <b className="count" data-to="60">60</b> controlli su ogni voce del budget, con le regole del bando e la fonte da cui vengono.</p></div>
        <div className="funziona-rows last">
          <div className="funziona-row"><div className="fr-text"><span className="step-n">A</span><h3>Un account, tutti i clienti</h3><p>Ogni azienda ha il suo flusso: documenti, profilo, bandi e piano restano separati e sempre aggiornati.</p></div><div className="fr-visual"><ClientsMockup /></div></div>
          <div className="funziona-row rev"><div className="fr-text"><span className="step-n">B</span><h3>60 controlli sul budget</h3><p>Ogni voce è controllata con le regole del bando: vedi subito cosa passa, cosa viene ridotto e cosa va documentato, prima di presentare la domanda.</p></div><div className="fr-visual"><HeatMockup /></div></div>
        </div>
      </div></section>

      <section className="sect dark">
        <ChainField rows={2} perRow={9} seed={41} variant="faint" />
        <div className="wrap">
          <div className="sect-head center reveal"><span className="kicker">Perché fidarsi</span><h2>Tre principi, non uno slogan</h2></div>
          <div className="trio">
            <div className="trio-item reveal-card"><DeterministicMockup /><h3>Deterministico</h3><p>Stesso dato, stesso risultato. I calcoli non usano modelli generativi: solo regole tracciabili.</p></div>
            <div className="trio-item reveal-card"><SourceMockup /><h3>Fonti dichiarate</h3><p>Ogni regola cita da dove viene e quanto ci si può fidare di quella lettura.</p></div>
            <div className="trio-item reveal-card"><HashMockup /><h3>Verificabile</h3><p>Un registro firmato a prova di manomissione: chi vuole può controllarlo.</p></div>
          </div>
        </div>
      </section>

      <section className="sect" id="per-chi"><div className="wrap">
        <div className="sect-head reveal"><span className="kicker">Per chi è</span><h2>Per chi segue molti clienti e non può sbagliare un numero</h2></div>
        <div className="trio">
          <div className="trio-item reveal-card"><ClientsMockup /><h3>Studi di commercialisti</h3><p>Decine di imprese clienti, un account solo, la fonte di ogni regola pronta da mostrare.</p></div>
          <div className="trio-item reveal-card"><HeatMockup /><h3>Boutique di finanza agevolata</h3><p>Dal bilancio al budget del bando, sapendo subito cosa verrebbe ridotto o respinto.</p></div>
          <div className="trio-item reveal-card"><AllocationMockup /><h3>Più clienti, stesso tempo</h3><p>Le ore della ricerca manuale tornano al lavoro che solo lo studio può fare.</p></div>
        </div>
      </div></section>

      <section className="sect reviews" id="recensioni"><div className="wrap">
        <div className="rev-grid">
          {REVIEWS.map((r) => (
            <figure key={r.id} className="review reveal-card">
              <blockquote>{r.text}</blockquote>
              <figcaption>{r.role}</figcaption>
            </figure>
          ))}
        </div>
      </div></section>

      <section className="sect tint" id="prezzi"><div className="wrap">
        <div className="sect-head center reveal"><span className="kicker">Prezzi</span><h2>Gratuito oggi. Onesto sempre.</h2>
          <p>QUANTO è gratuito in questa fase. Più avanti arriveranno piani a pagamento per studi e team: chi si iscrive ora userà il prodotto gratuitamente più a lungo.</p></div>
        <div className="pricing">
          <div className="price-card reveal-card hot">
            <div className="tier">Oggi</div><div className="amount">Gratis</div>
            <ul><li>Profilo azienda e lettura dei documenti</li><li>Previsione di bilancio e biblioteca dei bandi</li><li>Allocazione, de minimis e dossier</li><li>Registro firmato e verifica</li></ul>
            <button className="btn-solid big" onClick={() => setModal('register')}>Inizia gratis</button>
          </div>
          <div className="price-card reveal-card dim">
            <div className="tier">Presto</div><div className="amount">In arrivo</div>
            <ul><li>Piani a consumo per studi e team</li><li>Prezzi non ancora definiti</li></ul>
          </div>
        </div>
      </div></section>

      <section className="cta-final dark">
        <div className="wrap reveal">
          <h2>Prima di consegnare il prossimo piano al tuo cliente, calcolalo con QUANTO.</h2>
          <p>Gratis in questa fase, senza carta di credito, pronto in un minuto.</p>
          <button className="btn-solid big" onClick={() => setModal('register')}>Inizia gratis<ArrowRight size={16} /></button>
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
