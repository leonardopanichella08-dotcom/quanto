import React, { useEffect, useRef, useState } from 'react'
import { ArrowRight, Loader2, Lock, ShieldCheck, X } from 'lucide-react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { api, session } from '../lib/api'
import { Mark, Wordmark } from './ui'
import './Landing.css'
import { LaunchVideo } from './TutorialVideo'

gsap.registerPlugin(ScrollTrigger)

/* Homepage pubblica. Fondo quasi nero, uniforme; nessun riquadro, nessuna griglia di schede: solo tipografia, linee e movimento.
   Ogni animazione racconta una cosa vera di QUANTO: il testo di un bando che diventa una regola e un calcolo, la pratica che si compone
   passo dopo passo, gli agenti che si passano il lavoro. Le cifre sono di un esempio e lo dicono. Con «riduci movimento» tutto è fermo e leggibile. */

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
        <h3>{isRegister ? 'Crea l’account dello studio' : 'Accedi'}</h3>
        <p className="sub">{isRegister ? 'Nessuna carta di credito. In questa fase tutto è gratuito.' : 'Usa le credenziali dello studio.'}</p>
        {isRegister && (<><label htmlFor="ln-name">Nome</label><input id="ln-name" required autoFocus value={name} onChange={(e) => setName(e.target.value)} /></>)}
        <label htmlFor="ln-email">E-mail</label>
        <input id="ln-email" type="email" required autoFocus={!isRegister} autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} />
        <label htmlFor="ln-pw">Password</label>
        <input id="ln-pw" type="password" required minLength={isRegister ? 12 : 1} autoComplete={isRegister ? 'new-password' : 'current-password'} value={password} onChange={(e) => setPassword(e.target.value)} />
        {isRegister && <p className="hint">Almeno 12 caratteri, lettere e almeno un numero o simbolo.</p>}
        {error && <p className="error">{error}</p>}
        <button disabled={busy || !email || !password || (isRegister && !name)} className="submit">
          {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}{isRegister ? 'Crea account' : 'Entra'}
        </button>
        <p className="switch">
          {isRegister ? <>Hai già un account? <button type="button" onClick={() => onSwitch('login')}>Accedi</button></> : <>Non hai un account? <button type="button" onClick={() => onSwitch('register')}>Crealo gratis</button></>}
        </p>
      </form>
    </div>
  )
}

// ------------------------------------------------------------------------------------------------ hero: il testo del bando diventa una regola, la regola un calcolo
const EXCERPTS = [
  { ref: 'Avviso · art. 6, comma 2', before: 'Le spese per consulenze specialistiche sono ammissibili ', mark: 'nel limite del 10% del totale', after: ' delle spese ammesse.',
    rule: ['Consulenze', '≤ 10% del totale'], calc: ['Richieste 40.000,00 €', 'ammesse 24.911,00 €'], verdict: 'ridotta', tone: 'warn' },
  { ref: 'Avviso · art. 8, comma 1', before: 'L’agevolazione è concessa ', mark: 'nella misura del 50%', after: ' delle spese ritenute ammissibili.',
    rule: ['Intensità', '50%'], calc: ['Spese ammesse 249.111,00 €', 'contributo 124.555,50 €'], verdict: 'calcolato', tone: 'ok' },
  { ref: 'Avviso · art. 5, comma 4', before: 'Non sono ammissibili le spese ', mark: 'sostenute prima della presentazione della domanda', after: '.',
    rule: ['Finestra di spesa', 'dopo la domanda'], calc: ['Fattura del 12/02', 'domanda del 03/03'], verdict: 'esclusa', tone: 'no' },
]

function RuleMachine() {
  const root = useRef(null)
  const [i, setI] = useState(0)
  useEffect(() => {
    if (reduced()) return undefined
    const el = root.current
    const q = (sel) => el.querySelectorAll(sel)
    const ctx = gsap.context(() => {                       // fromTo con valori finali espliciti: in sviluppo l'effetto parte due volte e un «from» resterebbe a zero
      gsap.timeline({ onComplete: () => setI((n) => (n + 1) % EXCERPTS.length) })
        .fromTo(q('.rm-text'), { opacity: 0, y: 8 }, { opacity: 1, y: 0, duration: 0.6, ease: 'power2.out' })
        .fromTo(q('.rm-mark'), { backgroundSize: '0% 100%' }, { backgroundSize: '100% 100%', duration: 0.9, ease: 'power2.inOut' }, '+=0.3')
        .fromTo(q('.rm-wire'), { scaleX: 0 }, { scaleX: 1, duration: 0.5, ease: 'power2.inOut' })
        .fromTo(q('.rm-rule > *'), { opacity: 0, x: -8 }, { opacity: 1, x: 0, duration: 0.45, stagger: 0.08, ease: 'power2.out' })
        .fromTo(q('.rm-wire2'), { scaleX: 0 }, { scaleX: 1, duration: 0.5, ease: 'power2.inOut' }, '+=0.2')
        .fromTo(q('.rm-calc > *'), { opacity: 0, x: -8 }, { opacity: 1, x: 0, duration: 0.45, stagger: 0.1, ease: 'power2.out' })
        .fromTo(q('.rm-verdict'), { opacity: 0, scale: 0.9 }, { opacity: 1, scale: 1, duration: 0.4, ease: 'back.out(2)' })
        .to(q('.rm-stage'), { opacity: 0, duration: 0.5, ease: 'power1.in' }, '+=2.6')
    }, el)
    return () => ctx.revert()
  }, [i])
  const x = EXCERPTS[i]
  return (
    <div className="rm" ref={root} aria-label="Esempio: una frase del bando diventa una regola e un calcolo">
      <div className="rm-stage" key={i}>
        <p className="rm-ref">{x.ref} <span className="rm-ex">esempio</span></p>
        <p className="rm-text">«{x.before}<span className="rm-mark">{x.mark}</span>{x.after}»</p>
        <div className="rm-flow">
          <i className="rm-wire" />
          <div className="rm-rule"><span className="k">Regola</span><span className="v">{x.rule[0]}</span><span className="v strong">{x.rule[1]}</span></div>
          <i className="rm-wire2" />
          <div className="rm-calc"><span className="k">Sul budget</span><span className="v">{x.calc[0]}</span><span className="v strong">{x.calc[1]}</span></div>
          <span className={`rm-verdict ${x.tone}`}>{x.verdict}</span>
        </div>
      </div>
      <div className="rm-dots" aria-hidden="true">{EXCERPTS.map((_, k) => <i key={k} className={k === i ? 'on' : ''} />)}</div>
    </div>
  )
}

// ------------------------------------------------------------------------------------------------ il processo: la pratica si compone mentre si scorre
const STEPS = [
  { title: 'Il cliente', body: 'Bilanci o dichiarazione dei redditi, visura, buste paga, F24: QUANTO li legge e compila il profilo dell’impresa. Quello che manca lo chiede, non lo stima.',
    line: ['Profilo', 'Impresa di prova · ATECO 62.01 · profilo al 93%'] },
  { title: 'Le agevolazioni', body: 'Cerca in tutto il catalogo: bandi nazionali, regionali e camerali, crediti d’imposta, incentivi alle assunzioni. Tiene solo ciò che l’impresa può ottenere e scrive perché il resto è escluso.',
    line: ['Agevolazioni', '3 adatte · le escluse con il motivo scritto'] },
  { title: 'Lo studio del bando', body: 'Legge avvisi, decreti e allegati e ne ricava le regole numeriche, ognuna legata al testo da cui viene. Ciò che il bando non scrive resta dichiarato come lacuna.',
    line: ['Regole', '7 regole numeriche, ognuna con la sua fonte'] },
  { title: 'Il progetto e il budget', body: 'Dai bisogni dell’impresa al progetto, dal progetto al budget del bando, controllato voce per voce con 60 criteri. Il piano dice quale agevolazione copre quale spesa, senza contarla due volte.',
    line: ['Budget', '60 controlli per voce · cosa passa, cosa va ridotto'] },
  { title: 'La domanda', body: 'Confronto tra scenari, documenti di domanda raccolti dal sito ufficiale, dossier per il cliente e un registro firmato che prova che i numeri non sono stati toccati.',
    line: ['Consegna', 'dossier · documenti di domanda · registro 7f3a…9b1d'] },
]

// ------------------------------------------------------------------------------------------------ gli agenti si passano il lavoro
const AGENTS = [
  { name: 'Agevolazioni', what: 'Le misure che non chiedono un progetto: esoneri e incentivi alle assunzioni, crediti d’imposta. A ogni persona da assumere assegna la misura più ricca che le spetta.',
    did: 'Ho letto le assunzioni previste', found: 'Bonus Giovani per una persona, 15.600 € al massimo', need: 'Il mese di assunzione della seconda persona' },
  { name: 'Allocazione', what: 'Legge il catalogo, giudica ogni bando per l’impresa e compone il piano: quale agevolazione paga quale spesa, con tetti, cumulo e de minimis.',
    did: 'Ho cercato tra tutti i bandi aperti e ne ho studiati 8', found: '3 bandi adatti alle spese dell’anno, 3 a progetto', need: 'Nulla: puoi preparare i budget' },
  { name: 'Budget', what: 'Scrive la bozza del budget di progetto dai documenti dell’impresa e la controlla con le regole del bando, prima della domanda.',
    did: 'Ho scritto la bozza voce per voce', found: '2 voci da ridurre per rientrare nei tetti', need: 'Il registro del personale, per le persone sul progetto' },
  { name: 'Confronto', what: 'Mette a confronto bandi e scenari sullo stesso progetto, con lo stesso metodo, per decidere con il cliente.',
    did: 'Ho confrontato due bandi sullo stesso budget', found: 'Quale dei due copre di più, voce per voce', need: 'La scelta del cliente' },
]

function AgentRelay() {
  const root = useRef(null)
  const [on, setOn] = useState(0)
  useEffect(() => {
    if (reduced()) return undefined
    const el = root.current
    const st = ScrollTrigger.create({ trigger: el, start: 'top 80%', end: 'bottom 20%' })
    let n = 0
    const tick = () => { if (st.isActive) { n = (n + 1) % AGENTS.length; setOn(n) } }
    const t = setInterval(tick, 4200)
    return () => { clearInterval(t); st.kill() }
  }, [])
  useEffect(() => {
    if (reduced()) return
    const el = root.current
    gsap.fromTo(el.querySelector('.ar-pulse'), { left: `${(Math.max(on - 1, 0) / (AGENTS.length - 1)) * 100}%` }, { left: `${(on / (AGENTS.length - 1)) * 100}%`, duration: 0.9, ease: 'power3.inOut' })
    gsap.fromTo(el.querySelectorAll('.ar-detail > *'), { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.6, stagger: 0.07, ease: 'power2.out' })
  }, [on])
  const a = AGENTS[on]
  return (
    <div className="ar" ref={root}>
      <div className="ar-track">
        <i className="ar-line" /><i className="ar-fill" style={{ width: `${(on / (AGENTS.length - 1)) * 100}%` }} /><i className="ar-pulse" />
        {AGENTS.map((x, k) => (
          <button key={x.name} type="button" className={`ar-node${k === on ? ' on' : ''}${k < on ? ' done' : ''}`} style={{ left: `${(k / (AGENTS.length - 1)) * 100}%` }} onClick={() => setOn(k)}>
            <i /><span>{x.name}</span>
          </button>
        ))}
      </div>
      <div className="ar-detail" aria-live="polite">
        <p className="ar-what">{a.what}</p>
        <div className="ar-say">
          <p><span>Ho fatto</span>{a.did}</p>
          <p><span>Ho trovato</span>{a.found}</p>
          <p><span>Mi serve da te</span>{a.need}</p>
        </div>
        <p className="ar-ex">esempio</p>
      </div>
    </div>
  )
}

export default function Landing({ onLogin, onAuditor, onVision }) {
  const root = useRef(null)
  const [modal, setModal] = useState(null)
  const [solid, setSolid] = useState(false)
  const [step, setStep] = useState(0)

  useEffect(() => {
    const on = () => setSolid(window.scrollY > 16)
    on()
    window.addEventListener('scroll', on, { passive: true })
    return () => window.removeEventListener('scroll', on)
  }, [])

  useEffect(() => {
    if (reduced()) { setStep(STEPS.length - 1); return undefined }
    const ctx = gsap.context(() => {
      // titolo: le righe salgono da una maschera
      gsap.fromTo('.hero .ln > span', { yPercent: 110 }, { yPercent: 0, duration: 1.1, ease: 'power4.out', stagger: 0.09, delay: 0.1 })
      gsap.fromTo('.hero .after', { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.9, ease: 'power3.out', stagger: 0.08, delay: 0.55 })

      // titoli di sezione: maschera dal basso
      gsap.utils.toArray('.mask-in').forEach((el) => gsap.fromTo(el.querySelectorAll('.ln > span'), { yPercent: 110 }, { yPercent: 0, duration: 1, ease: 'power4.out', stagger: 0.08, scrollTrigger: { trigger: el, start: 'top 85%' } }))
      gsap.utils.toArray('.fade-in').forEach((el) => gsap.fromTo(el, { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.9, ease: 'power3.out', scrollTrigger: { trigger: el, start: 'top 88%' } }))

      // la frase si accende parola per parola mentre si scorre
      gsap.fromTo('.manifesto .w', { opacity: 0.14 }, { opacity: 1, stagger: 0.1, ease: 'none', scrollTrigger: { trigger: '.manifesto', start: 'top 75%', end: 'bottom 45%', scrub: true } })

      // il processo: la linea si disegna, il passo attivo si accende, la pratica si compone
      const mm = gsap.matchMedia()
      mm.add('(min-width: 961px)', () => {
        ScrollTrigger.create({
          trigger: '.proc', start: 'top top', end: () => `+=${window.innerHeight * 0.7 * STEPS.length}`, pin: '.proc-pin', scrub: true,
          onUpdate: (s) => {
            setStep(Math.min(STEPS.length - 1, Math.floor(s.progress * STEPS.length)))
            gsap.set('.proc-progress', { scaleY: s.progress })
          },
        })
      })
      mm.add('(max-width: 960px)', () => { setStep(STEPS.length - 1) })

      // principi: ogni parola chiave si scopre con una riga che la attraversa
      gsap.utils.toArray('.pr-row').forEach((el) => {
        gsap.fromTo(el.querySelector('.pr-rule'), { scaleX: 0 }, { scaleX: 1, duration: 1.1, ease: 'power3.inOut', scrollTrigger: { trigger: el, start: 'top 85%' } })
        gsap.fromTo(el.querySelectorAll('.ln > span'), { yPercent: 110 }, { yPercent: 0, duration: 1, ease: 'power4.out', delay: 0.2, scrollTrigger: { trigger: el, start: 'top 85%' } })
        gsap.fromTo(el.querySelector('p'), { opacity: 0 }, { opacity: 1, duration: 0.9, delay: 0.45, scrollTrigger: { trigger: el, start: 'top 85%' } })
      })
    }, root)
    return () => ctx.revert()
  }, [])

  const lines = (arr) => arr.map((t, i) => <span key={i} className="ln"><span>{t}</span></span>)

  return (
    <div className="qt-land" ref={root}>
      <nav className={`qt-nav${solid ? ' solid' : ''}`}><div className="wrap row">
        <div className="brand"><Mark size={26} /><Wordmark height={15} className="wordmark" /></div>
        <div className="links">
          <a href="#processo">Il processo</a>
          <a href="#agenti">Gli agenti</a>
          <a href="#principi">Principi</a>
          <a href="#prezzi">Prezzi</a>
          <button onClick={onVision}>La visione</button>
        </div>
        <div className="actions">
          <button className="btn-ghost" onClick={() => setModal('login')}>Accedi</button>
          <button className="btn-solid" onClick={() => setModal('register')}>Inizia gratis</button>
        </div>
      </div></nav>

      <header className="hero"><div className="wrap">
        <p className="eyebrow after">Finanza agevolata per studi di commercialisti</p>
        <h1>{lines(['La finanza agevolata', 'dello studio,', 'dall’inizio alla fine.'])}</h1>
        <div className="hero-row">
          <div>
            <p className="lead after">QUANTO trova le agevolazioni adatte a ogni cliente, ne studia le regole, costruisce il progetto e il budget e li controlla prima della domanda. Agenti che svolgono il lavoro, ogni numero legato alla sua fonte.</p>
            <div className="ctas after">
              <button className="btn-solid big" onClick={() => setModal('register')}>Inizia gratis<ArrowRight size={15} /></button>
              <a className="btn-text" href="#processo">Il processo<ArrowRight size={14} /></a>
            </div>
          </div>
          <div className="after"><RuleMachine /></div>
        </div>
      </div></header>

      <section className="manifesto"><div className="wrap">
        <p>{'Un bando è un testo scritto per essere letto da una persona. QUANTO lo rende calcolabile: legge la regola, la applica al budget del cliente e dice da quale articolo viene, sempre nello stesso modo.'.split(' ').map((w, i) => <span key={i} className="w">{w} </span>)}</p>
      </div></section>

      <section className="sect" id="video"><div className="wrap">
        <h2 className="mask-in">{lines(['QUANTO al lavoro,', 'in quaranta secondi.'])}</h2>
        <div className="video fade-in"><LaunchVideo /></div>
      </div></section>

      <section className="proc" id="processo">
        <div className="proc-pin"><div className="wrap proc-grid">
          <div className="proc-left">
            <p className="eyebrow">Il processo</p>
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
            <p className="pr-head">Pratica · Impresa di prova <span>esempio</span></p>
            {STEPS.map((s, k) => (
              <div key={s.title} className={`pl${k <= step ? ' in' : ''}${k === step ? ' now' : ''}`}>
                <span className="pl-k">{s.line[0]}</span><span className="pl-v">{s.line[1]}</span>
              </div>
            ))}
            <p className={`pl-end${step === STEPS.length - 1 ? ' in' : ''}`}>Pronta per la domanda.</p>
          </div>
        </div></div>
      </section>

      <section className="sect" id="agenti"><div className="wrap">
        <p className="eyebrow fade-in">Gli agenti</p>
        <h2 className="mask-in">{lines(['Quattro agenti, in ordine.', 'Lo studio decide e firma.'])}</h2>
        <p className="para fade-in">Ognuno ha un compito preciso, dice sempre che cosa ha fatto, che cosa ha trovato e che cosa gli serve da te, e passa il lavoro al successivo.</p>
        <div className="fade-in"><AgentRelay /></div>
      </div></section>

      <section className="sect" id="principi"><div className="wrap">
        <p className="eyebrow fade-in">Perché fidarsi</p>
        {[['Deterministico.', 'Stessi dati, stesso risultato. Gli agenti organizzano il lavoro; i numeri li calcolano regole tracciabili, mai un modello che indovina.'],
          ['Fonti dichiarate.', 'Ogni regola cita il testo ufficiale da cui è letta e quanto è affidabile la lettura. Quello che le fonti non dicono resta scritto come lacuna.'],
          ['Verificabile.', 'Ogni budget controllato lascia un’impronta firmata in un registro a catena: un revisore o un ente può controllare che nulla sia cambiato.']].map(([t, b]) => (
          <div key={t} className="pr-row">
            <i className="pr-rule" />
            <h3 className="pr-title">{lines([t])}</h3>
            <p>{b}</p>
          </div>
        ))}
      </div></section>

      <section className="sect" id="per-chi"><div className="wrap">
        <p className="eyebrow fade-in">Per chi è</p>
        <h2 className="mask-in wide">{lines(['Per gli studi di commercialisti', 'e le boutique di finanza agevolata', 'che seguono molte imprese', 'e non possono sbagliare un numero.'])}</h2>
        <p className="para fade-in">Lo studio offre la finanza agevolata ai suoi clienti senza costruire un reparto dedicato: QUANTO fa la ricerca, lo studio delle regole e il budget; il commercialista mostra al cliente da dove viene ogni cifra, e il calcolo rifatto tra un mese dà lo stesso risultato.</p>
      </div></section>

      <section className="sect" id="visione-breve"><div className="wrap split">
        <h2 className="mask-in">{lines(['Oggi la finanza agevolata.', 'Domani il sistema', 'operativo dello studio.'])}</h2>
        <div className="fade-in">
          <p className="para">Si parte dal lavoro dove un errore costa di più e il tempo manca sempre: le pratiche di finanza agevolata, svolte da agenti che seguono regole dichiarate.</p>
          <p className="para">Lo stesso metodo (dati letti dai documenti, regole con la fonte, calcolo che si può rifare e verificare) si estende alle altre attività dello studio, una alla volta.</p>
          <button className="btn-text" onClick={onVision}>Leggi la visione<ArrowRight size={14} /></button>
        </div>
      </div></section>

      <section className="sect" id="prezzi"><div className="wrap">
        <p className="eyebrow fade-in">Prezzi</p>
        <h2 className="mask-in">{lines(['Gratuito oggi.', 'Chiaro sempre.'])}</h2>
        <p className="para fade-in">Il lavoro quotidiano è libero. I token si usano solo dove serve un calcolo grande o un consegnabile. In questa fase di prova nessun token viene scalato e non serve la carta.</p>
        <div className="prices fade-in">
          <div>
            <p className="pt">Piano Studio</p>
            <p className="pa">209 €<small> al mese · oppure 1.999 € all’anno · 15 token al mese</small></p>
            <p className="pd">Profilo, documenti, stima, allocazione e controllo del budget sempre liberi. Piano di allocazione da 2 a 4,8 token, consegna di un budget da 1 a 2 token (30 giorni per lo stesso lavoro), studio di un bando nuovo 3 token (1 torna se la lettura è completa). 10 token di benvenuto che non scadono, +0,5 per ogni budget pubblicato per tutti.</p>
          </div>
          <div>
            <p className="pt">Ricariche</p>
            <p className="pa">25 €<small> ogni 10 token</small></p>
            <p className="pd">Quando i token del mese finiscono. Il pagamento online arriverà: oggi le ricariche le elabora il titolare.</p>
          </div>
        </div>
      </div></section>

      <section className="cta-final"><div className="wrap">
        <h2 className="mask-in">{lines(['La prossima pratica,', 'preparala con QUANTO.'])}</h2>
        <div className="fade-in cta-row">
          <button className="btn-solid big" onClick={() => setModal('register')}>Crea l’account dello studio<ArrowRight size={15} /></button>
          <span>Gratuito in questa fase, senza carta di credito.</span>
        </div>
      </div></section>

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
