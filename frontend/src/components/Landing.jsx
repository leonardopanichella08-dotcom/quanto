import React, { useEffect, useRef, useState } from 'react'
import { ArrowRight, Loader2, Lock, ShieldCheck, X } from 'lucide-react'
import { api, session } from '../lib/api'
import { Mark, Wordmark } from './ui'
import './Landing.css'
import { LaunchVideo } from './TutorialVideo'

/* Homepage pubblica. Fondo quasi nero, uniforme. Una sola tinta di marca (il giallo), usata poco. Niente illustrazioni:
   solo testo, linee sottili e riquadri che riproducono il prodotto. Le cifre dei riquadri vengono da un'impresa di prova e lo dicono. */

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
        <h3>{isRegister ? 'Crea l’account dello studio' : 'Accedi'}</h3>
        <p className="sub">{isRegister ? 'Nessuna carta di credito. In questa fase tutto è gratuito.' : 'Usa le credenziali dello studio.'}</p>
        {isRegister && (<><label htmlFor="ln-name">Nome</label><input id="ln-name" required autoFocus value={name} onChange={(e) => setName(e.target.value)} /></>)}
        <label htmlFor="ln-email">E-mail</label>
        <input id="ln-email" type="email" required autoFocus={!isRegister} autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} />
        <label htmlFor="ln-pw">Password</label>
        <input id="ln-pw" type="password" required minLength={isRegister ? 12 : 1} autoComplete={isRegister ? 'new-password' : 'current-password'} value={password} onChange={(e) => setPassword(e.target.value)} />
        {isRegister && <p className="hint">Almeno 12 caratteri, lettere e almeno un numero o simbolo.</p>}
        {error && <p className="error">{error}</p>}
        <button disabled={busy || !email || !password || (isRegister && !name)} className="btn-solid submit">
          {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}{isRegister ? 'Crea account' : 'Entra'}
        </button>
        <p className="switch">
          {isRegister ? <>Hai già un account? <button type="button" onClick={() => onSwitch('login')}>Accedi</button></> : <>Non hai un account? <button type="button" onClick={() => onSwitch('register')}>Crealo gratis</button></>}
        </p>
      </form>
    </div>
  )
}

/** Gli elementi con .rv compaiono con una dissolvenza breve quando entrano in vista (una volta). Con «riduci movimento» sono già visibili. */
function useReveal(root) {
  useEffect(() => {
    const els = root.current ? [...root.current.querySelectorAll('.rv')] : []
    if (reducedMotion() || typeof IntersectionObserver === 'undefined') { els.forEach((e) => e.classList.add('in')); return undefined }
    const io = new IntersectionObserver((entries) => entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target) } }), { threshold: 0.15 })
    els.forEach((e) => io.observe(e))
    return () => io.disconnect()
  }, [root])
}

// ------------------------------------------------------------------------------------------------ riquadri del prodotto (cifre di un'impresa di prova)
const Frame = ({ title, note, children }) => (
  <div className="frame">
    <div className="frame-head"><span>{title}</span>{note && <span className="frame-note">{note}</span>}</div>
    <div className="frame-body">{children}</div>
  </div>
)

function HeroConsole() {
  const agents = [
    ['01', 'Agevolazioni', 'Misure per le assunzioni assegnate persona per persona', 'fatto'],
    ['02', 'Allocazione', 'Catalogo letto, bandi giudicati per territorio, settore e requisiti', 'fatto'],
    ['03', 'Budget', 'Bozza del budget di progetto, 60 controlli per voce', 'in corso'],
    ['04', 'Confronto', 'Scenari a confronto, documenti di domanda', 'in attesa'],
  ]
  return (
    <Frame title="Impresa di prova · ATECO 62.01" note="esempio">
      <ol className="console-steps">
        {agents.map(([n, t, d, s]) => (
          <li key={n} className={`st-${s.replace(' ', '-')}`}>
            <span className="cs-n">{n}</span>
            <div className="cs-txt"><b>{t}</b><span>{d}</span></div>
            <span className="cs-state">{s}</span>
          </li>
        ))}
      </ol>
      <div className="console-foot">
        <div><span className="lbl">Bandi adatti</span><span className="val">3</span></div>
        <div><span className="lbl">Da verificare</span><span className="val">0</span></div>
        <div><span className="lbl">Totale agevolato (massimo)</span><span className="val accent">163.949,41 €</span></div>
      </div>
    </Frame>
  )
}

const HEAT = 'OOOAOOOROOOOWOOOONOOOAOONOOOOOOAOOONOROOOOONOOOOWOOONOOAOOOO'.split('')
const HEAT_CLASS = { O: 'ok', A: 'adj', R: 'rej', W: 'wait', N: 'none' }
function PanelChecks() {
  return (
    <Frame title="Budget · 60 controlli per voce" note="esempio">
      <div className="heat">{HEAT.map((c, i) => <i key={i} className={HEAT_CLASS[c]} />)}</div>
      <div className="legend"><span><i className="ok" />superato</span><span><i className="adj" />ridotto</span><span><i className="rej" />respinto</span><span><i className="wait" />da documentare</span><span><i className="none" />non valutato</span></div>
    </Frame>
  )
}

const PANELS = {
  docs: () => (
    <Frame title="Documenti del cliente">
      {[['Bilancio 2025', 'letto'], ['Visura camerale', 'letto'], ['Registro del personale', 'letto'], ['F24', 'letto']].map(([a, b]) => <div key={a} className="row"><span>{a}</span><span className="ok">{b}</span></div>)}
      <p className="foot">Ogni dato del profilo porta il documento e la pagina da cui viene.</p>
    </Frame>
  ),
  search: () => (
    <Frame title="Ricerca su tutto il catalogo" note="esempio">
      {[['Nuovo Piano Transizione 5.0', 'adatto'], ['Fondo 394/81 · SIMEST', 'adatto'], ['Investimenti Sostenibili 4.0', 'a progetto'], ['Comune di altra regione', 'escluso']].map(([a, b]) => <div key={a} className="row"><span>{a}</span><span className={b === 'escluso' ? 'no' : b === 'a progetto' ? 'mid' : 'ok'}>{b}</span></div>)}
      <p className="foot">Ogni esclusione ha il suo motivo scritto: territorio, settore, requisiti dell’impresa.</p>
    </Frame>
  ),
  rules: () => (
    <Frame title="Regole lette dal bando" note="esempio">
      <div className="row"><span>Consulenze</span><span className="mono">max 20% del totale</span></div>
      <div className="row"><span>Intensità di aiuto</span><span className="mono">50%</span></div>
      <div className="row"><span>Finestra di spesa</span><span className="mono">dopo la domanda</span></div>
      <p className="foot">Fonte: avviso, art. 6, comma 2 · lettura dal testo ufficiale. Ciò che il bando non scrive resta dichiarato come lacuna.</p>
    </Frame>
  ),
  budget: () => <PanelChecks />,
  deliver: () => (
    <Frame title="Consegna">
      <div className="row"><span>Dossier PDF</span><span className="dim">ogni numero con la fonte</span></div>
      <div className="row"><span>Budget per bando</span><span className="dim">pronto da presentare</span></div>
      <div className="row"><span>Documenti di domanda</span><span className="dim">raccolti dal sito ufficiale</span></div>
      <div className="row"><span>Registro firmato</span><span className="mono dim">7f3a9c1e…6c0e9b1d</span></div>
    </Frame>
  ),
}

const STEPS = [
  { n: '01', k: 'docs', title: 'Il cliente', body: 'Bilanci o dichiarazione dei redditi, visura, buste paga, F24. QUANTO li legge e compila il profilo dell’impresa; quello che manca lo chiede, non lo stima.' },
  { n: '02', k: 'search', title: 'Le agevolazioni', body: 'Cerca in tutto il catalogo: bandi nazionali, regionali e camerali, crediti d’imposta, incentivi alle assunzioni. Tiene solo ciò che l’impresa può davvero ottenere, e scrive perché il resto è escluso.' },
  { n: '03', k: 'rules', title: 'Lo studio del bando', body: 'Legge avvisi, decreti e allegati e ne ricava le regole numeriche: intensità, tetti, spese ammesse, finestre. Ogni regola resta legata al testo da cui viene.' },
  { n: '04', k: 'budget', title: 'Il progetto e il budget', body: 'Dai bisogni dell’impresa al progetto, dal progetto al budget del bando, controllato voce per voce con 60 criteri. Il piano dice quale agevolazione copre quale spesa, senza contare due volte la stessa.' },
  { n: '05', k: 'deliver', title: 'La domanda', body: 'Confronto tra scenari, documenti di domanda, dossier per il cliente e un registro firmato che prova che i numeri non sono stati toccati.' },
]

const AGENTS = [
  ['Agevolazioni', 'Le misure che non chiedono un progetto: esoneri e incentivi alle assunzioni, crediti d’imposta. Assegna a ogni persona da assumere la misura più ricca che le spetta.'],
  ['Allocazione', 'Legge il catalogo, giudica ogni bando per l’impresa e compone il piano: quale agevolazione paga quale spesa, con tetti, cumulo e de minimis.'],
  ['Budget', 'Scrive la bozza del budget di progetto dai documenti dell’impresa e la controlla con le regole del bando, prima della domanda.'],
  ['Confronto', 'Mette a confronto bandi e scenari sullo stesso progetto, con lo stesso metodo, per decidere con il cliente.'],
]

const PRINCIPLES = [
  ['Deterministico', 'Stessi dati, stesso risultato. Gli agenti organizzano il lavoro; i numeri li calcolano regole tracciabili, mai un modello che indovina.'],
  ['Fonti dichiarate', 'Ogni regola cita il testo ufficiale da cui è letta e quanto è affidabile la lettura. Quello che le fonti non dicono resta scritto come lacuna.'],
  ['Verificabile', 'Ogni budget controllato lascia un’impronta firmata in un registro a catena: un revisore o un ente può controllare che nulla sia cambiato.'],
]

const AUDIENCE = [
  ['Studi di commercialisti', 'Offrire la finanza agevolata ai clienti dello studio senza costruire un reparto dedicato: QUANTO fa la ricerca, lo studio e il budget, lo studio decide e firma.'],
  ['Boutique di finanza agevolata', 'Più pratiche nello stesso tempo, con la certezza di cosa verrebbe ridotto o respinto prima di presentare la domanda.'],
  ['Studi con molti clienti', 'Un account, un lavoro per ogni impresa: documenti, profilo, agevolazioni e budget restano separati e sempre aggiornati.'],
]

const CHANGES = [
  ['Ogni numero ha una fonte', 'Il commercialista mostra al cliente da dove viene ogni cifra: il documento dell’impresa o l’articolo del bando.'],
  ['Il calcolo si rifà, uguale', 'Rifatto davanti al cliente, tra un mese o da un revisore, il risultato è lo stesso.'],
  ['Niente fogli di calcolo in mezzo', 'Dai documenti del cliente al budget del bando, nello stesso posto.'],
]

export default function Landing({ onLogin, onAuditor, onVision }) {
  const root = useRef(null)
  const [modal, setModal] = useState(null)
  const [solid, setSolid] = useState(false)
  useReveal(root)
  useEffect(() => {
    const on = () => setSolid(window.scrollY > 16)
    on()
    window.addEventListener('scroll', on, { passive: true })
    return () => window.removeEventListener('scroll', on)
  }, [])

  return (
    <div className="qt-land" ref={root}>
      <nav className={`qt-nav${solid ? ' solid' : ''}`}><div className="wrap row">
        <div className="brand"><Mark size={26} /><Wordmark height={15} className="wordmark" /></div>
        <div className="links">
          <a href="#cosa-fa">Cosa fa</a>
          <a href="#come-funziona">Il processo</a>
          <a href="#agenti">Gli agenti</a>
          <a href="#prezzi">Prezzi</a>
          <button onClick={onVision}>La visione</button>
        </div>
        <div className="actions">
          <button className="btn-ghost" onClick={() => setModal('login')}>Accedi</button>
          <button className="btn-solid" onClick={() => setModal('register')}>Inizia gratis</button>
        </div>
      </div></nav>

      <header className="hero"><div className="wrap hero-grid">
        <div className="hero-text">
          <span className="eyebrow rv">Finanza agevolata per studi professionali</span>
          <h1 className="rv">La finanza agevolata dello studio, dall’inizio alla fine.</h1>
          <p className="lead rv">QUANTO trova le agevolazioni adatte a ogni cliente, ne studia le regole, costruisce il progetto e il budget e li controlla prima della domanda. Con agenti che svolgono il lavoro e ogni numero legato alla sua fonte.</p>
          <div className="ctas rv">
            <button className="btn-solid big" onClick={() => setModal('register')}>Inizia gratis<ArrowRight size={15} /></button>
            <a className="btn-line big" href="#come-funziona">Il processo</a>
          </div>
          <p className="fine rv">Gratuito in questa fase. Nessuna carta di credito.</p>
        </div>
        <div className="hero-visual rv"><HeroConsole /></div>
      </div></header>

      <section className="band"><div className="wrap stats">
        <div className="rv"><span className="num">60</span><span className="cap">controlli su ogni voce del budget</span></div>
        <div className="rv"><span className="num">4</span><span className="cap">agenti, un percorso: dalle agevolazioni alla domanda</span></div>
        <div className="rv"><span className="num">1</span><span className="cap">fonte dichiarata per ogni numero</span></div>
        <div className="rv"><span className="num">0</span><span className="cap">cifre stimate a caso o inventate</span></div>
      </div></section>

      <section className="sect" id="video"><div className="wrap">
        <div className="head rv"><span className="eyebrow">In 40 secondi</span><h2>QUANTO al lavoro</h2></div>
        <div className="video rv"><LaunchVideo /></div>
      </div></section>

      <section className="sect" id="cosa-fa"><div className="wrap">
        <div className="head rv"><span className="eyebrow">Cosa fa</span><h2>Tutto il lavoro di una pratica di finanza agevolata, in un solo posto.</h2>
          <p>Il cuore è la pratica: capire a quali agevolazioni ha diritto l’impresa, scrivere il progetto, presentare un budget che regge. L’allocazione delle spese ne è la conseguenza: il budget dice quale agevolazione paga cosa.</p></div>
        <div className="cols4">
          {[['Trova', 'Le agevolazioni per cui l’impresa ha i requisiti, su tutto il catalogo, con il motivo di ogni esclusione.'],
            ['Studia', 'Le regole del bando lette dai testi ufficiali: intensità, tetti, spese ammesse, cumulo, de minimis.'],
            ['Costruisce', 'Il progetto dai bisogni dell’impresa e il budget del bando dai suoi documenti.'],
            ['Controlla', 'Ogni voce con 60 criteri, prima che lo faccia l’ente: cosa passa, cosa va ridotto, cosa va documentato.']].map(([t, b], i) => (
            <div key={t} className="cell rv"><span className="idx">{String(i + 1).padStart(2, '0')}</span><h3>{t}</h3><p>{b}</p></div>
          ))}
        </div>
      </div></section>

      <section className="statement"><div className="wrap">
        <p className="rv">Nessuna stima aleatoria. Nessun testo inventato. <span>Solo regole ufficiali, applicate sempre nello stesso modo.</span></p>
      </div></section>

      <section className="sect" id="come-funziona"><div className="wrap">
        <div className="head rv"><span className="eyebrow">Il processo</span><h2>Dal primo documento del cliente alla domanda.</h2></div>
        <div className="steps">
          {STEPS.map((s) => {
            const P = PANELS[s.k]
            return (
              <div key={s.n} className="step rv">
                <div className="step-text"><span className="idx">{s.n}</span><h3>{s.title}</h3><p>{s.body}</p></div>
                <div className="step-panel"><P /></div>
              </div>
            )
          })}
        </div>
      </div></section>

      <section className="sect" id="agenti"><div className="wrap">
        <div className="head rv"><span className="eyebrow">Gli agenti</span><h2>Quattro agenti, in ordine. Lo studio resta al comando.</h2>
          <p>Ogni agente ha un compito preciso e dice sempre tre cose: che cosa ha fatto, che cosa ha trovato, che cosa gli serve da te. Con un pulsante passa il lavoro al successivo.</p></div>
        <div className="agents">
          {AGENTS.map(([t, b], i) => (
            <div key={t} className="agent rv">
              <div className="agent-top"><span className="idx">{i + 1}</span><h3>{t}</h3></div>
              <p>{b}</p>
            </div>
          ))}
        </div>
        <div className="agentbar rv">
          <div><span className="lbl">Ho fatto</span><span>Ho cercato tra tutti i bandi aperti, ne ho studiati 8 e ho giudicato quali sono per l’impresa.</span></div>
          <div><span className="lbl">Ho trovato</span><span>3 bandi adatti alle spese dell’anno, 3 a progetto.</span></div>
          <div><span className="lbl">Mi serve da te</span><span>Il registro del personale, per il budget persona per persona.</span></div>
          <span className="agentbar-note">esempio</span>
        </div>
      </div></section>

      <section className="sect" id="principi"><div className="wrap">
        <div className="head rv"><span className="eyebrow">Perché fidarsi</span><h2>Tre principi, verificabili.</h2></div>
        <div className="cols3">
          {PRINCIPLES.map(([t, b]) => <div key={t} className="cell rv"><h3>{t}</h3><p>{b}</p></div>)}
        </div>
      </div></section>

      <section className="sect" id="per-chi"><div className="wrap">
        <div className="head rv"><span className="eyebrow">Per chi è</span><h2>Per lo studio che segue molte imprese e non può sbagliare un numero.</h2></div>
        <div className="cols3">
          {AUDIENCE.map(([t, b]) => <div key={t} className="cell rv"><h3>{t}</h3><p>{b}</p></div>)}
        </div>
      </div></section>

      <section className="sect" id="nello-studio"><div className="wrap">
        <div className="head rv"><span className="eyebrow">Nello studio</span><h2>Che cosa cambia nel lavoro di ogni giorno.</h2></div>
        <div className="cols3">
          {CHANGES.map(([t, b]) => <div key={t} className="cell rv"><h3>{t}</h3><p>{b}</p></div>)}
        </div>
      </div></section>

      <section className="sect" id="visione-breve"><div className="wrap split">
        <div className="head rv"><span className="eyebrow">Oggi e domani</span><h2>Oggi la finanza agevolata. Domani il sistema operativo dello studio.</h2></div>
        <div className="rv">
          <p className="para">Si parte dal lavoro dove un errore costa di più e il tempo manca sempre: le pratiche di finanza agevolata, svolte da agenti che seguono regole dichiarate.</p>
          <p className="para">Lo stesso metodo (dati letti dai documenti, regole con la fonte, calcolo che si può rifare e verificare) si estende alle altre attività dello studio, una alla volta, finché QUANTO diventa il posto in cui lo studio lavora.</p>
          <button className="text-link" onClick={onVision}>Leggi la visione<ArrowRight size={14} /></button>
        </div>
      </div></section>

      <section className="sect" id="prezzi"><div className="wrap">
        <div className="head rv"><span className="eyebrow">Prezzi</span><h2>Gratuito oggi. Chiaro sempre.</h2>
          <p>Il lavoro quotidiano è libero. I token si usano solo dove serve un calcolo grande o un consegnabile: il piano di allocazione, la consegna di un budget, lo studio di un bando nuovo. In questa fase di prova nessun token viene scalato e non serve la carta.</p></div>
        <div className="pricing">
          <div className="price rv">
            <span className="tier">Piano Studio</span>
            <div className="amount">209 € <small>al mese</small></div>
            <span className="alt">oppure 1.999 € all’anno · 15 token al mese</span>
            <ul>
              <li>Profilo, documenti, stima, allocazione e controllo del budget: sempre liberi</li>
              <li>Piano di allocazione: da 2 a 4,8 token secondo i dati analizzati (30 giorni per lo stesso lavoro)</li>
              <li>Consegna di un budget: da 1 a 2 token (30 giorni per lo stesso)</li>
              <li>Studio di un bando nuovo: 3 token, 1 torna se la lettura è completa</li>
              <li>+0,5 token per ogni budget pubblicato per tutti · 10 token di benvenuto che non scadono</li>
            </ul>
            <button className="btn-solid big" onClick={() => setModal('register')}>Inizia gratis</button>
          </div>
          <div className="price rv">
            <span className="tier">Ricariche</span>
            <div className="amount">25 € <small>ogni 10 token</small></div>
            <ul>
              <li>Quando i token del mese finiscono</li>
              <li>Il pagamento online arriverà: oggi le ricariche le elabora il titolare</li>
            </ul>
          </div>
        </div>
      </div></section>

      <section className="cta-final"><div className="wrap rv">
        <h2>La prossima pratica di finanza agevolata, preparala con QUANTO.</h2>
        <p>Gratuito in questa fase, senza carta di credito. Si comincia caricando i documenti di un cliente.</p>
        <button className="btn-solid big" onClick={() => setModal('register')}>Crea l’account dello studio<ArrowRight size={15} /></button>
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
