import React, { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { ArrowRight, Check, FileText, Link2, Loader2, Lock, ShieldCheck, Sparkles, Table2, X } from 'lucide-react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { api, session } from '../lib/api'
import { Mark, Wordmark } from './ui'
import './Landing.css'

gsap.registerPlugin(ScrollTrigger)
const LiquidHero = lazy(() => import('./LiquidHero'))

const eur = (n) => n.toLocaleString('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const reducedMotion = () => typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches

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

// ------------------------------------------------------------------------------------------------ pannelli illustrativi (dati d'esempio dell'azienda di prova)
const Glass = ({ children, className = '' }) => <div className={`glass ${className}`}>{children}</div>

function PanelDocs() {
  const rows = ['Conto economico', 'Stato patrimoniale', 'F24 · versamenti e crediti', 'Visura · ATECO e sede']
  return (
    <Glass className="panel">
      <div className="p-label">LETTURA AUTOMATICA</div>
      <div className="p-bar"><i style={{ width: '100%' }} /></div>
      {rows.map((r) => <div key={r} className="p-row"><span>{r}</span><span className="ok"><Check size={13} />letto</span></div>)}
    </Glass>
  )
}
function PanelForecast() {
  const rows = [['Personale', 1.0, 0.99], ['Consulenze', 0.24, 0.23], ['Spese generali', 0.2, 0.19], ['Beni strumentali', 0.13, 0.13], ['Formazione', 0.03, 0.02]]
  return (
    <Glass className="panel">
      <div className="p-label">SPESE PER CATEGORIA · BILANCIO CONTRO STIMA</div>
      {rows.map(([l, a, b]) => (
        <div key={l} className="p-pair"><span>{l}</span><div><i className="a" style={{ width: `${b * 100}%` }} /><i className="b" style={{ width: `${a * 100}%` }} /></div></div>
      ))}
      <div className="p-legend"><span><i className="a" />bilancio 2025</span><span><i className="b" />stima 2027</span></div>
    </Glass>
  )
}
function PanelBandi() {
  const rows = [['Horizon Europe', 'Adatto'], ['Investimenti Sostenibili 4.0', 'Adatto'], ['Transizione 5.0', 'Adatto'], ['Nuova Sabatini', 'Adatto'], ['Bando regionale', 'Da verificare']]
  return (
    <Glass className="panel">
      <div className="p-label">BANDI ADATTI ALL'AZIENDA</div>
      {rows.map(([n, f]) => <div key={n} className="p-row"><span>{n}</span><span className={`pill ${f === 'Adatto' ? 'g' : 'a'}`}>{f}</span></div>)}
    </Glass>
  )
}
function PanelAlloc() {
  const rows = [['Personale', 0.7], ['Consulenze', 0.7], ['Spese generali', 0], ['Beni strumentali', 1], ['Formazione', 0.14]]
  return (
    <Glass className="panel">
      <div className="p-label">POTENZIALE MASSIMO · TUTTI I BANDI INSIEME</div>
      <div className="p-big">{eur(1252698.85)} €</div>
      <div className="p-sub">su 1.991.026,11 € di spese · quota coperta 62,9%</div>
      {rows.map(([l, v]) => <div key={l} className="p-cov"><span>{l}</span><div><i style={{ width: `${v * 100}%` }} /></div></div>)}
      <span className="pill v">De minimis · stimato dai bilanci</span>
    </Glass>
  )
}
function PanelDossier() {
  return (
    <Glass className="panel">
      <div className="p-label">CONSEGNA</div>
      <div className="p-out"><FileText size={20} /><div><b>Dossier</b><span>PDF con ogni numero e la sua fonte</span></div></div>
      <div className="p-out"><Table2 size={20} /><div><b>Budget</b><span>Template per bando, pronto da compilare</span></div></div>
      <div className="p-out"><Link2 size={20} /><div><b>Registro firmato</b><span>Catena di impronte verificabile</span></div></div>
      <div className="p-hash">0x7f3a9c1e5b8d2f4a…6c0e9b1d3a7f5c2e</div>
    </Glass>
  )
}

const STEPS = [
  { n: '01', title: 'Carichi i documenti del cliente', body: 'Bilanci, F24, visura, buste paga. QUANTO li legge voce per voce e compila il profilo dell’azienda: dove non è sicuro, te lo chiede.', Panel: PanelDocs },
  { n: '02', title: 'Stima l’anno successivo', body: 'Parte dall’ultimo bilancio e applica la variazione che risulta dai tuoi dati, oppure il modello che indichi tu. Ogni percentuale ha la sua spiegazione.', Panel: PanelForecast },
  { n: '03', title: 'Trova i bandi adatti', body: 'Confronta l’azienda con la biblioteca dei bandi: regione, dimensione, ATECO, spese ammesse. Quello che il bando non dice resta dichiarato, mai inventato.', Panel: PanelBandi },
  { n: '04', title: 'Calcola il massimo recuperabile', body: 'Tutti i bandi insieme, senza pagare due volte la stessa spesa e rispettando tetti, cumulo e de minimis, che QUANTO stima da solo dai bilanci.', Panel: PanelAlloc },
  { n: '05', title: 'Consegna dossier e registro', body: 'Un dossier PDF, il budget per bando e un registro firmato che prova che i numeri non sono stati toccati.', Panel: PanelDossier },
]

const PILLARS = [
  ['Legge i documenti', 'Bilanci, F24, visure e buste paga diventano dati, con la pagina e la riga da cui vengono.'],
  ['Stima l’anno', 'Previsione di bilancio per categoria di spesa, con la spiegazione di ogni percentuale.'],
  ['Trova i bandi', 'Una biblioteca di bandi studiati dalle fonti ufficiali, confrontati con l’azienda.'],
  ['Calcola il massimo', 'Un solo risultato: quanto può recuperare l’azienda, calcolato al centesimo.'],
]

const TOOLS = [
  ['Profilo azienda', 'Dati e bilanci in un posto solo, ognuno con il documento da cui arriva.'],
  ['Previsione di bilancio', 'Spese e ricavi dell’anno successivo, con modello tuo o variazione dai bilanci.'],
  ['Biblioteca dei bandi', 'Bandi studiati dalle fonti ufficiali, con regole, tetti e scadenze.'],
  ['Allocazione ottimale', 'Quale bando paga quale spesa: il piano migliore, sempre lo stesso a parità di dati.'],
  ['De minimis automatico', 'Il tetto residuo stimato dagli aiuti dichiarati nei bilanci, con la sua base dichiarata.'],
  ['Budget per bando', 'Il template di budget del bando, costruito dalle spese dell’azienda.'],
  ['Dossier PDF', 'Il documento da consegnare al cliente, con ogni cifra e la sua fonte.'],
  ['Registro firmato', 'Ogni calcolo lascia un’impronta in una catena firmata e verificabile.'],
  ['Assistente interno', 'Ti accompagna passo per passo e ti chiede solo i valori che mancano, spiegandoli.'],
]

const STATEMENT = 'Nessuna stima aleatoria. Nessun testo inventato. Solo regole ufficiali, applicate in modo deterministico e verificabile.'
const MARQUEE = ['Bilanci', 'F24', 'Visure', 'Bandi', 'De minimis', 'Budget', 'Dossier', 'Registro firmato']

export default function Landing({ onLogin, onAuditor, onVision }) {
  const root = useRef(null)
  const cardNum = useRef(null)
  const [modal, setModal] = useState(null)
  const [active, setActive] = useState(0)
  const reduce = reducedMotion()

  useEffect(() => {
    let off = () => {}
    const ctx = gsap.context(() => {
      const nav = root.current.querySelector('.qt-nav')
      ScrollTrigger.create({ start: 24, end: 99999, onUpdate: (s) => nav.classList.toggle('solid', s.scroll() > 24) })

      // il numero della scheda del hero conta fino al valore d'esempio
      const counter = { v: 0 }
      const setNum = () => { if (cardNum.current) cardNum.current.textContent = `${eur(counter.v)} €` }
      if (reduce) { counter.v = 1252698.85; setNum(); return }

      const tl = gsap.timeline({ defaults: { ease: 'power4.out' } })
      tl.from('.hero .eyebrow', { y: 18, opacity: 0, duration: 0.8 })
        .from('.hero h1 .w > span', { yPercent: 115, duration: 1.1, stagger: 0.05 }, '-=0.5')
        .from('.hero .sub', { y: 22, opacity: 0, duration: 0.9 }, '-=0.7')
        .from('.hero .ctas > *', { y: 18, opacity: 0, duration: 0.8, stagger: 0.1 }, '-=0.6')
        .from('.hero .hero-card', { y: 60, opacity: 0, rotateX: 12, duration: 1.3 }, '-=1.0')
        .to(counter, { v: 1252698.85, duration: 2.2, ease: 'power3.out', onUpdate: setNum }, '-=0.8')
        .from('.hero .hero-card .bar i', { scaleX: 0, transformOrigin: 'left', duration: 1.2, stagger: 0.08 }, '-=1.6')

      // la scheda del hero si muove piano con lo scroll e segue il mouse
      gsap.to('.hero .hero-card-wrap', { yPercent: -12, ease: 'none', scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true } })
      const wrap = root.current.querySelector('.hero-card-wrap')
      const onMove = (e) => {
        const r = wrap.getBoundingClientRect()
        const x = (e.clientX - (r.left + r.width / 2)) / window.innerWidth, y = (e.clientY - (r.top + r.height / 2)) / window.innerHeight
        gsap.to('.hero .hero-card', { rotateY: x * 10, rotateX: -y * 8, duration: 0.8, ease: 'power3.out' })
      }
      window.addEventListener('pointermove', onMove, { passive: true })
      off = () => window.removeEventListener('pointermove', onMove)

      // i titoli di sezione e le schede entrano scorrendo
      gsap.utils.toArray('.reveal').forEach((el) => gsap.from(el, { y: 44, opacity: 0, filter: 'blur(10px)', duration: 1, ease: 'power3.out', scrollTrigger: { trigger: el, start: 'top 86%' } }))
      ScrollTrigger.batch('.reveal-card', { start: 'top 88%', onEnter: (els) => gsap.from(els, { y: 50, opacity: 0, filter: 'blur(8px)', duration: 0.9, stagger: 0.09, ease: 'power3.out', overwrite: true }) })

      // la frase che si accende parola per parola
      gsap.fromTo('.statement .sw', { opacity: 0.14 }, { opacity: 1, stagger: 0.12, ease: 'none', scrollTrigger: { trigger: '.statement', start: 'top 70%', end: 'bottom 55%', scrub: true } })

      // «come funziona»: la sezione resta ferma e i cinque passi scorrono
      const mm = gsap.matchMedia()
      mm.add('(min-width: 900px)', () => {
        ScrollTrigger.create({
          trigger: '.how', start: 'top top', end: () => `+=${window.innerHeight * 0.65 * STEPS.length}`, pin: '.how-pin', scrub: true,
          onUpdate: (s) => setActive(Math.min(STEPS.length - 1, Math.floor(s.progress * STEPS.length))),
        })
      })

      // numeri della sezione strumenti
      gsap.utils.toArray('.count').forEach((el) => {
        const to = Number(el.dataset.to); const o = { v: 0 }
        gsap.to(o, { v: to, duration: 1.6, ease: 'power2.out', onUpdate: () => { el.textContent = Math.round(o.v) }, scrollTrigger: { trigger: el, start: 'top 90%', once: true } })
      })

    }, root)
    return () => { off(); ctx.revert() }
  }, [reduce])

  const split = (text) => text.split(' ').map((w, i) => <span key={i} className="w"><span>{w}</span></span>)

  return (
    <div className="qt-land" ref={root}>
      <nav className="qt-nav"><div className="wrap row">
        <div className="brand"><Mark size={30} /><Wordmark height={17} className="wordmark-mask" /></div>
        <div className="links">
          <a href="#cosa-fa">Cosa fa</a>
          <a href="#come-funziona">Come funziona</a>
          <a href="#strumenti">Strumenti</a>
          <a href="#prezzi">Prezzi</a>
          <button onClick={onVision}><Sparkles size={14} />La visione</button>
        </div>
        <div className="actions">
          <button className="btn-ghost" onClick={() => setModal('login')}>Accedi</button>
          <button className="btn-solid" onClick={() => setModal('register')}>Inizia gratis</button>
        </div>
      </div></nav>

      <header className="hero">
        <Suspense fallback={null}><LiquidHero reduce={reduce} /></Suspense>
        <div className="wrap hero-grid">
          <div className="hero-copy">
            <span className="eyebrow"><i />Per studi di commercialisti e boutique di finanza agevolata</span>
            <h1>{split('Il motore di calcolo per la finanza agevolata.')}</h1>
            <p className="sub">Carichi i bilanci del cliente. QUANTO stima l’anno successivo, trova i bandi, applica le regole ufficiali e calcola il massimo recuperabile: al centesimo, con la fonte di ogni numero.</p>
            <div className="ctas">
              <button className="btn-solid big" onClick={() => setModal('register')}>Inizia gratis<ArrowRight size={16} /></button>
              <a className="btn-line big" href="#come-funziona">Come funziona</a>
            </div>
            <p className="fineprint">Gratuito oggi. Nessuna carta di credito richiesta.</p>
          </div>
          <div className="hero-card-wrap">
            <Glass className="hero-card">
              <div className="hc-top"><span>ALLOCAZIONE · ESERCIZIO 2027</span><span>azienda di prova</span></div>
              <div className="hc-label">POTENZIALE MASSIMO · TUTTI I BANDI INSIEME</div>
              <div className="hc-num" ref={cardNum}>{eur(0)} €</div>
              <div className="hc-sub">fino a <b>1.718.015,07 €</b> con tutte le maggiorazioni</div>
              {[['Personale', 70], ['Consulenze', 70], ['Beni strumentali', 100], ['Formazione', 14]].map(([l, v]) => (
                <div key={l} className="bar"><span>{l}</span><div><i style={{ width: `${v}%` }} /></div></div>
              ))}
              <div className="hc-foot"><span className="pill g"><Check size={12} />Regole ufficiali verificate</span><span className="pill v">De minimis stimato</span></div>
            </Glass>
            <p className="caption">Illustrazione: i valori sono quelli dell’azienda di prova.</p>
          </div>
        </div>
        <div className="scroll-hint" aria-hidden="true"><i /></div>
      </header>

      <div className="marquee" aria-hidden="true">
        <div className="track">{[...MARQUEE, ...MARQUEE, ...MARQUEE, ...MARQUEE].map((w, i) => <span key={i}>{w}<em>◆</em></span>)}</div>
      </div>

      <section className="sect" id="cosa-fa"><div className="wrap">
        <div className="sect-head reveal"><span className="kicker">Cosa fa</span><h2>Dal bilancio al massimo recuperabile, in un solo posto</h2></div>
        <div className="pillars">
          {PILLARS.map(([t, b], i) => (
            <Glass key={t} className="pillar reveal-card"><span className="num">0{i + 1}</span><h3>{t}</h3><p>{b}</p></Glass>
          ))}
        </div>
      </div></section>

      <section className="statement"><div className="wrap">
        <p>{STATEMENT.split(' ').map((w, i) => <span key={i} className="sw">{w} </span>)}</p>
      </div></section>

      <section className="how" id="come-funziona">
        <div className="how-pin"><div className="wrap how-grid">
          <div className="how-left">
            <span className="kicker">Come funziona</span>
            <h2>Cinque passi, nessun foglio Excel in mezzo</h2>
            <ol className="how-steps">
              {STEPS.map((s, i) => (
                <li key={s.n} className={i === active ? 'on' : ''}>
                  <span className="n">{s.n}</span>
                  <div><h3>{s.title}</h3><p>{s.body}</p><div className="inline-panel"><s.Panel /></div></div>
                </li>
              ))}
            </ol>
          </div>
          <div className="how-right">
            <div className="how-stage">{STEPS.map((s, i) => <div key={s.n} className={`how-panel ${i === active ? 'on' : ''}`}><s.Panel /></div>)}</div>
            <p className="caption">Illustrazioni con i dati dell’azienda di prova.</p>
          </div>
        </div></div>
      </section>

      <section className="sect light" id="strumenti"><div className="wrap">
        <div className="sect-head reveal"><span className="kicker">Gli strumenti</span><h2>Tutto quello che serve per un cliente, già collegato</h2>
          <p>Un account per lo studio, un flusso dedicato per ogni azienda cliente. <b className="count" data-to="60">60</b> controlli per bando, ognuno con la fonte da cui viene la regola.</p></div>
        <div className="bento">
          {TOOLS.map(([t, b], i) => (
            <div key={t} className={`tool reveal-card t${i}`}><span className="idx">{String(i + 1).padStart(2, '0')}</span><h3>{t}</h3><p>{b}</p></div>
          ))}
        </div>
      </div></section>

      <section className="sect dark"><div className="wrap">
        <div className="sect-head center reveal"><span className="kicker">Perché fidarsi</span><h2>Tre principi, non uno slogan</h2></div>
        <div className="trio">
          <Glass className="trio-item reveal-card"><ShieldCheck size={26} /><h3>Deterministico</h3><p>Stesso dato, stesso risultato. I calcoli non usano modelli generativi: solo regole tracciabili, riga per riga.</p></Glass>
          <Glass className="trio-item reveal-card"><FileText size={26} /><h3>Fonti dichiarate</h3><p>Ogni regola cita da dove viene, un decreto o una circolare, e quanto ci si può fidare di quella lettura.</p></Glass>
          <Glass className="trio-item reveal-card"><Link2 size={26} /><h3>Verificabile</h3><p>Un registro firmato a prova di manomissione: chiunque può controllare che un dossier non sia stato toccato.</p></Glass>
        </div>
      </div></section>

      <section className="sect light" id="per-chi"><div className="wrap">
        <div className="sect-head reveal"><span className="kicker">Per chi è</span><h2>Per chi segue molti clienti e non può sbagliare un numero</h2></div>
        <div className="who">
          <div className="who-item reveal-card"><h3>Studi di commercialisti</h3><p>Decine di imprese clienti, un account solo. Per ognuna, il potenziale dei bandi pronto da mostrare con la fonte di ogni regola.</p></div>
          <div className="who-item reveal-card"><h3>Boutique di finanza agevolata</h3><p>Dal bilancio al budget del bando, sapendo subito cosa verrebbe ridotto o respinto prima di presentare la domanda.</p></div>
          <div className="who-item reveal-card"><h3>Più clienti, stesso tempo</h3><p>Le ore che andavano nella ricerca manuale e nei fogli di calcolo tornano al lavoro che solo lo studio può fare.</p></div>
        </div>
      </div></section>

      <section className="sect dark" id="prezzi"><div className="wrap">
        <div className="sect-head center reveal"><span className="kicker">Prezzi</span><h2>Gratuito oggi. Onesto sempre.</h2>
          <p>QUANTO è gratuito in questa fase. Più avanti arriveranno piani a pagamento per studi e team: chi si iscrive ora userà il prodotto gratuitamente più a lungo.</p></div>
        <div className="pricing">
          <Glass className="price-card reveal-card hot">
            <div className="tier">Oggi</div><div className="amount">Gratis</div>
            <ul><li>Profilo azienda e lettura dei documenti</li><li>Previsione di bilancio e biblioteca dei bandi</li><li>Allocazione, de minimis e dossier</li><li>Registro firmato e verifica</li></ul>
            <button className="btn-solid big" onClick={() => setModal('register')}>Inizia gratis</button>
          </Glass>
          <Glass className="price-card reveal-card dim">
            <div className="tier">Presto</div><div className="amount">In arrivo</div>
            <ul><li>Piani a consumo per studi e team</li><li>Prezzi non ancora definiti</li></ul>
          </Glass>
        </div>
      </div></section>

      <section className="cta-final">
        <div className="orb" aria-hidden="true" />
        <div className="wrap reveal">
          <h2>Prima di consegnare il prossimo piano al tuo cliente, calcolalo con QUANTO.</h2>
          <p>Gratis in questa fase, senza carta di credito, pronto in un minuto.</p>
          <button className="btn-solid big" onClick={() => setModal('register')}>Inizia gratis<ArrowRight size={16} /></button>
        </div>
      </section>

      <footer className="qt-foot"><div className="wrap row">
        <span className="copy">© 2026 QUANTO</span>
        <button onClick={onVision}><Sparkles size={14} />La visione</button>
        <button onClick={onAuditor}><ShieldCheck size={14} />Sei un revisore?</button>
        <span className="sp" />
        <button onClick={() => setModal('login')}><Lock size={13} />Accedi</button>
      </div></footer>

      {modal && <AuthModal mode={modal} onClose={() => setModal(null)} onSwitch={setModal} onDone={onLogin} />}
    </div>
  )
}
