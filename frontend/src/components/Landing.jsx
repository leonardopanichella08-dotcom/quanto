import React, { useEffect, useMemo, useRef, useState } from 'react'
import { ArrowRight, ArrowUpRight, Loader2, Lock, Pause, Play, Search, ShieldCheck, Volume2, VolumeX, X } from 'lucide-react'
import { api, session } from '../lib/api'
import { Mark, Wordmark } from './ui'
import { FAQ, FAQ_COUNT } from '../data/faq'
import './Landing.css'

/* Homepage pubblica. Stile editoriale e istituzionale: fondo bianco, sezioni off-white, una sola grande fotografia nell'apertura,
   griglie a linee sottili al posto delle schede, giallo del marchio (#F1E21B) solo per i dettagli attivi.
   Movimento: solo comparse brevi con la curva cubic-bezier(0.16, 1, 0.3, 1); con «riduci movimento» tutto è fermo. */

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

/** Gli elementi .rv compaiono una volta, quando entrano in vista. */
function useReveal(root) {
  useEffect(() => {
    const els = root.current ? [...root.current.querySelectorAll('.rv')] : []
    if (reduced() || typeof IntersectionObserver === 'undefined') { els.forEach((e) => e.classList.add('in')); return undefined }
    const io = new IntersectionObserver((entries) => entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target) } }), { threshold: 0.12, rootMargin: '0px 0px -40px 0px' })
    els.forEach((e) => io.observe(e))
    return () => io.disconnect()
  }, [root])
}

// ------------------------------------------------------------------------------------------------ esempio: la frase del bando diventa una regola, la regola un calcolo
const EXCERPTS = [
  { ref: 'Avviso · art. 6, comma 2', before: 'Le spese per consulenze specialistiche sono ammissibili ', mark: 'nel limite del 10% del totale', after: ' delle spese ammesse.',
    rule: ['Consulenze', '≤ 10% del totale'], calc: ['Richieste', '40.000,00 €'], out: ['Ammesse', '24.911,00 €'], verdict: 'ridotta' },
  { ref: 'Avviso · art. 8, comma 1', before: 'L’agevolazione è concessa ', mark: 'nella misura del 50%', after: ' delle spese ritenute ammissibili.',
    rule: ['Intensità', '50%'], calc: ['Spese ammesse', '249.111,00 €'], out: ['Contributo', '124.555,50 €'], verdict: 'calcolato' },
  { ref: 'Avviso · art. 5, comma 4', before: 'Non sono ammissibili le spese ', mark: 'sostenute prima della presentazione della domanda', after: '.',
    rule: ['Finestra', 'dopo la domanda'], calc: ['Fattura', '12/02/2027'], out: ['Domanda', '03/03/2027'], verdict: 'esclusa' },
]

function RuleExample() {
  const [i, setI] = useState(0)
  const [step, setStep] = useState(reduced() ? 4 : 0)
  useEffect(() => {
    if (reduced()) return undefined
    const t = [setTimeout(() => setStep(1), 500), setTimeout(() => setStep(2), 1500), setTimeout(() => setStep(3), 2300), setTimeout(() => setStep(4), 3100),
      setTimeout(() => setStep(5), 6800), setTimeout(() => { setI((n) => (n + 1) % EXCERPTS.length); setStep(0) }, 7400)]
    return () => t.forEach(clearTimeout)
  }, [i])
  const x = EXCERPTS[i]
  return (
    <figure className={`rx s${step}`} aria-label="Esempio: una frase del bando diventa una regola e un calcolo">
      <figcaption className="rx-ref mono">{x.ref}<span>Esempio</span></figcaption>
      <blockquote className="rx-text">«{x.before}<mark>{x.mark}</mark>{x.after}»</blockquote>
      <div className="rx-grid">
        <div className="rx-cell c1"><span className="k">Regola</span><span className="v">{x.rule[0]}</span><span className="n mono">{x.rule[1]}</span></div>
        <div className="rx-cell c2"><span className="k">Sul budget</span><span className="v">{x.calc[0]}</span><span className="n mono">{x.calc[1]}</span></div>
        <div className="rx-cell c3"><span className="k">Esito</span><span className="v">{x.out[0]}</span><span className="n mono">{x.out[1]}</span><span className={`rx-verdict ${x.verdict}`}>{x.verdict}</span></div>
      </div>
    </figure>
  )
}

// ------------------------------------------------------------------------------------------------ video con controlli essenziali
const fmtTime = (s) => (Number.isFinite(s) ? `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}` : '0:00')
function EditorialVideo({ src, poster, label, title, note }) {
  const ref = useRef(null)
  const [playing, setPlaying] = useState(false)
  const [muted, setMuted] = useState(true)
  const [t, setT] = useState(0)
  const [d, setD] = useState(0)
  const toggle = () => { const v = ref.current; if (!v) return; if (v.paused) { v.play().catch(() => {}) } else v.pause() }
  const seek = (e) => { const v = ref.current; if (!v || !d) return; const r = e.currentTarget.getBoundingClientRect(); v.currentTime = ((e.clientX - r.left) / r.width) * d }
  return (
    <figure className="ev">
      <div className="ev-frame">
        <video ref={ref} src={src} poster={poster} muted={muted} playsInline preload="metadata" aria-label={title}
          onPlay={() => setPlaying(true)} onPause={() => setPlaying(false)} onEnded={() => setPlaying(false)}
          onTimeUpdate={(e) => setT(e.currentTarget.currentTime)} onLoadedMetadata={(e) => setD(e.currentTarget.duration)} onClick={toggle} />
        {!playing && <button type="button" className="ev-big" onClick={toggle} aria-label={`Riproduci: ${title}`}><Play size={22} /></button>}
        <div className="ev-bar">
          <button type="button" onClick={toggle} aria-label={playing ? 'Pausa' : 'Riproduci'}>{playing ? <Pause size={15} /> : <Play size={15} />}</button>
          <div className="ev-track" onClick={seek} role="slider" aria-label="Posizione nel video" aria-valuemin={0} aria-valuemax={Math.round(d)} aria-valuenow={Math.round(t)} tabIndex={0}
            onKeyDown={(e) => { const v = ref.current; if (!v) return; if (e.key === 'ArrowRight') v.currentTime = Math.min(d, t + 5); if (e.key === 'ArrowLeft') v.currentTime = Math.max(0, t - 5) }}>
            <i style={{ width: d ? `${(t / d) * 100}%` : '0%' }} />
          </div>
          <span className="mono">{fmtTime(t)} / {fmtTime(d)}</span>
          <button type="button" onClick={() => setMuted((m) => !m)} aria-label={muted ? 'Attiva l’audio' : 'Disattiva l’audio'}>{muted ? <VolumeX size={15} /> : <Volume2 size={15} />}</button>
        </div>
      </div>
      <figcaption className="ev-cap"><span className="mono">{label}</span><b>{title}</b>{note && <em>{note}</em>}</figcaption>
    </figure>
  )
}

// ------------------------------------------------------------------------------------------------ newsletter
function Newsletter() {
  const [email, setEmail] = useState('')
  const [consent, setConsent] = useState(false)
  const [state, setState] = useState(null)        // null · 'busy' · 'ok' · 'already' · { error }
  const send = async (e) => {
    e.preventDefault()
    setState('busy')
    try { const r = await api.newsletterSubscribe(email.trim(), consent); setState(r.already ? 'already' : 'ok') } catch (err) { setState({ error: err.message }) }
  }
  if (state === 'ok' || state === 'already') return <p className="nl-done">{state === 'ok' ? 'Iscrizione registrata. Riceverai solo aggiornamenti di finanza agevolata.' : 'Questo indirizzo era già iscritto: non serve altro.'}</p>
  return (
    <form className="nl" onSubmit={send}>
      <label htmlFor="nl-email" className="nl-label">E-mail dello studio</label>
      <div className="nl-row">
        <input id="nl-email" type="email" required placeholder="nome@studio.it" value={email} onChange={(e) => setEmail(e.target.value)} />
        <button type="submit" disabled={!email || !consent || state === 'busy'}>{state === 'busy' ? 'Invio…' : 'Iscriviti'}<ArrowRight size={14} /></button>
      </div>
      <label className="nl-consent"><input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
        <span>Acconsento a ricevere la newsletter di QUANTO sulla finanza agevolata. L’indirizzo serve solo a questo invio, non viene ceduto a terzi e posso cancellarmi in qualunque momento.</span></label>
      {state?.error && <p className="nl-error">{state.error}</p>}
    </form>
  )
}

// ------------------------------------------------------------------------------------------------ FAQ
function FaqBlock() {
  const [q, setQ] = useState('')
  const [cat, setCat] = useState(FAQ[0].cat)
  const [open, setOpen] = useState(null)
  const norm = (s) => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
  const results = useMemo(() => {
    const k = norm(q.trim())
    if (!k) return null
    return FAQ.flatMap((g) => g.items.filter(([a, b]) => norm(a).includes(k) || norm(b).includes(k)).map((it) => ({ cat: g.cat, it })))
  }, [q])
  const list = results ?? (FAQ.find((g) => g.cat === cat)?.items || []).map((it) => ({ cat, it }))
  return (
    <div className="faq">
      <div className="faq-side">
        <div className="faq-search"><Search size={15} /><input type="search" placeholder={`Cerca tra ${FAQ_COUNT} domande`} value={q} onChange={(e) => { setQ(e.target.value); setOpen(null) }} aria-label="Cerca nelle domande frequenti" /></div>
        <ul className="faq-cats" aria-label="Argomenti">
          {FAQ.map((g) => (
            <li key={g.cat}><button type="button" className={!results && g.cat === cat ? 'on' : ''} onClick={() => { setQ(''); setCat(g.cat); setOpen(null) }}>
              <span>{g.cat}</span><span className="mono">{String(g.items.length).padStart(2, '0')}</span></button></li>
          ))}
        </ul>
      </div>
      <div className="faq-list">
        {results && <p className="faq-count mono">{results.length} {results.length === 1 ? 'risposta' : 'risposte'} per «{q.trim()}»</p>}
        {list.length === 0 && <p className="faq-empty">Nessuna domanda contiene queste parole. Prova con un termine più semplice, per esempio «budget», «de minimis» o «token».</p>}
        <dl>
          {list.map(({ cat: c, it: [a, b] }, k) => {
            const id = `${c}-${k}`
            const isOpen = open === id
            return (
              <div key={id} className={`faq-item${isOpen ? ' open' : ''}`}>
                <dt><button type="button" aria-expanded={isOpen} onClick={() => setOpen(isOpen ? null : id)}>
                  <span className="mono faq-n">{String(k + 1).padStart(2, '0')}</span><span className="faq-q">{a}</span><span className="faq-plus" aria-hidden="true" /></button></dt>
                <dd><div className="faq-a">{results && <span className="faq-cat mono">{c}</span>}<p>{b}</p></div></dd>
              </div>
            )
          })}
        </dl>
      </div>
    </div>
  )
}

// ------------------------------------------------------------------------------------------------ contenuti
const METHOD = [
  ['01', 'Il cliente', 'Bilanci o dichiarazione dei redditi, visura, buste paga, F24, fatture: QUANTO li legge e compila il profilo, con la fonte di ogni dato.'],
  ['02', 'Le agevolazioni', 'Ricerca su tutto il catalogo, nazionale, regionale e camerale. Restano solo le misure che l’impresa può ottenere; le altre hanno il motivo scritto.'],
  ['03', 'Le regole', 'Avvisi, decreti e allegati letti alla fonte: intensità, tetti, spese ammesse e finestre, ognuna legata al suo articolo.'],
  ['04', 'Progetto e budget', 'Dai bisogni dell’impresa al progetto, dal progetto al budget del bando, controllato voce per voce con 60 criteri.'],
  ['05', 'La domanda', 'Scenari a confronto, documenti di domanda raccolti, dossier per il cliente e registro firmato dei numeri.'],
]
const AGENTS = [
  ['Agevolazioni', 'Le misure che non chiedono un progetto: esoneri e incentivi alle assunzioni, crediti d’imposta. A ogni persona da assumere la misura più ricca che le spetta.'],
  ['Allocazione', 'Giudica ogni bando per l’impresa e compone il piano: quale agevolazione paga quale spesa, con tetti, cumulo e de minimis.'],
  ['Budget', 'Scrive la bozza del budget dai documenti dell’impresa e la controlla con le regole del bando, prima della domanda.'],
  ['Confronto', 'Mette a confronto bandi e scenari sullo stesso progetto, con lo stesso metodo, per decidere con il cliente.'],
]
const PRINCIPLES = [
  ['Deterministico', 'Stessi dati, stesso risultato. Gli agenti organizzano il lavoro; le cifre le calcolano regole tracciabili, mai un modello che indovina.'],
  ['Fonti dichiarate', 'Ogni regola cita il testo ufficiale da cui è letta. Ciò che le fonti non dicono resta scritto come lacuna, mai riempito.'],
  ['Verificabile', 'Ogni budget controllato lascia un’impronta firmata in un registro a catena: un revisore o un ente può verificare che nulla sia cambiato.'],
]
const FOR_STUDIOS = [
  ['Un account, tutti i clienti', 'Ogni impresa è un lavoro separato, con documenti, profilo, piano e budget sempre aggiornati.'],
  ['Senza un reparto dedicato', 'QUANTO fa ricerca, studio delle regole e prima stesura del budget. Lo studio decide con il cliente e firma.'],
  ['Ogni cifra si mostra', 'Al cliente si mostra da dove viene ogni numero: il suo documento o l’articolo del bando.'],
  ['Il calcolo si rifà', 'Rifatto davanti al cliente, tra un mese o da un revisore, il risultato è lo stesso.'],
  ['Società, persone, ditte', 'Per chi non ha il bilancio bastano la dichiarazione dei redditi e due numeri. Nessuna domanda superflua.'],
  ['Nessun costo ordinario travestito', 'Il personale si rendiconta sulle ore e sulla retribuzione vera: QUANTO non aiuta a far passare costi ordinari come costi di progetto.'],
]
const TOPICS = [['Normativa', 'Circolari, decreti e novità che cambiano le agevolazioni'], ['Bandi', 'Analisi tecniche delle misure aperte: cosa ammettono, cosa no'], ['Studio', 'Metodi per organizzare le pratiche e parlare con il cliente']]

export default function Landing({ onLogin, onAuditor, onVision }) {
  const root = useRef(null)
  const [modal, setModal] = useState(null)
  const [solid, setSolid] = useState(false)
  useReveal(root)
  useEffect(() => {
    const on = () => setSolid(window.scrollY > 24)
    on()
    window.addEventListener('scroll', on, { passive: true })
    return () => window.removeEventListener('scroll', on)
  }, [])

  return (
    <div className="qt-land" ref={root}>
      <nav className={`qt-nav${solid ? ' solid' : ''}`}><div className="wrap row">
        <a href="#top" className="brand" aria-label="QUANTO, torna all’inizio"><Mark size={24} /><Wordmark height={14} className="wordmark" /></a>
        <div className="links">
          <a href="#metodo">Il Metodo</a>
          <a href="#agenti">I 4 Agenti</a>
          <a href="#commercialisti">Per i Commercialisti</a>
          <a href="#insights">Insights &amp; Newsletter</a>
          <a href="#faq">FAQ</a>
        </div>
        <div className="actions">
          <button className="btn-ghost" onClick={() => setModal('login')}>Accedi</button>
          <button className="btn-cta" onClick={() => setModal('register')}>Richiedi accesso</button>
        </div>
      </div></nav>

      <header className="hero" id="top">
        <img className="hero-img" src="/landing/skyline-alba.jpg" alt="" />
        <div className="hero-shade" aria-hidden="true" />
        <div className="wrap hero-inner">
          <p className="hero-eyebrow mono rv">Finanza agevolata · per studi di commercialisti</p>
          <h1 className="rv">Il metodo deterministico per la finanza agevolata dello studio.</h1>
          <p className="hero-sub rv">QUANTO trova le agevolazioni adatte a ogni cliente, ne legge le regole alla fonte, costruisce progetto e budget e li controlla prima della domanda. Ogni numero porta con sé il documento da cui viene.</p>
          <div className="hero-ctas rv">
            <button className="btn-cta big" onClick={() => setModal('register')}>Richiedi accesso<ArrowRight size={15} /></button>
            <a className="hero-link" href="#metodo">Il metodo<ArrowRight size={14} /></a>
          </div>
        </div>
        <div className="wrap hero-foot">
          <span className="mono">01 / Dal documento del cliente alla domanda</span>
          <span className="mono">60 controlli per voce · 4 agenti · 0 cifre inventate</span>
        </div>
      </header>

      <section className="sect" id="metodo"><div className="wrap">
        <div className="sect-head rv"><span className="idx mono">02 / Il Metodo</span><h2>Una pratica di finanza agevolata, dall’inizio alla fine, in un solo posto.</h2>
          <p>Il cuore è la pratica: capire a quali agevolazioni ha diritto l’impresa, scrivere il progetto, presentare un budget che regge. L’allocazione delle spese ne è la conseguenza: il budget dice quale agevolazione paga cosa.</p></div>
        <ol className="hair-grid g5 rv">
          {METHOD.map(([n, t, b]) => <li key={n}><span className="mono n">{n}</span><h3>{t}</h3><p>{b}</p></li>)}
        </ol>
      </div></section>

      <section className="sect off"><div className="wrap split">
        <div className="sect-head rv"><span className="idx mono">03 / Il calcolo</span><h2>Un bando è scritto per una persona. QUANTO lo rende calcolabile.</h2>
          <p>Legge la frase, ne ricava la regola, la applica al budget del cliente e dice da quale articolo viene. Sempre nello stesso modo.</p></div>
        <div className="rv"><RuleExample /></div>
      </div></section>

      <section className="sect dark" id="agenti"><div className="wrap">
        <div className="sect-head rv"><span className="idx mono">04 / I 4 Agenti</span><h2>Quattro agenti, in ordine. Lo studio decide e firma.</h2>
          <p>Ognuno ha un compito, dice sempre che cosa ha fatto, che cosa ha trovato e che cosa gli serve, e passa il lavoro al successivo. Nessuno decide cifre: le calcolano le regole.</p></div>
        <div className="rv"><EditorialVideo src="/video/quanto-quattro-agenti.mp4" poster="/landing/quattro-agenti.png" label="01 / Architettura multi-agente" title="I quattro agenti di QUANTO" note="Agevolazioni · Allocazione · Budget · Confronto" /></div>
        <ol className="hair-grid g4 on-dark rv">
          {AGENTS.map(([t, b], k) => <li key={t}><span className="mono n">{String(k + 1).padStart(2, '0')}</span><h3>{t}</h3><p>{b}</p></li>)}
        </ol>
        <div className="video-pair rv">
          <EditorialVideo src="/video/quanto-lancio.mp4" poster="/video/quanto-lancio.jpg" label="02 / La piattaforma" title="QUANTO in quaranta secondi" />
          <div className="video-aside">
            <p className="mono">Ogni agente, in cima alla sua pagina</p>
            <dl>
              <div><dt>Ho fatto</dt><dd>Ho cercato tra tutti i bandi aperti e ne ho studiati 8.</dd></div>
              <div><dt>Ho trovato</dt><dd>3 bandi adatti alle spese dell’anno, 3 a progetto.</dd></div>
              <div><dt>Mi serve da te</dt><dd>Il registro del personale, per il budget persona per persona.</dd></div>
            </dl>
            <p className="aside-note mono">Esempio su un’impresa di prova</p>
          </div>
        </div>
      </div></section>

      <section className="sect" id="commercialisti"><div className="wrap">
        <div className="sect-head rv"><span className="idx mono">05 / Per i Commercialisti</span><h2>Per lo studio che segue molte imprese e non può sbagliare un numero.</h2></div>
        <ul className="hair-grid g3 rv">
          {FOR_STUDIOS.map(([t, b]) => <li key={t}><h3>{t}</h3><p>{b}</p></li>)}
        </ul>
        <div className="principles rv">
          {PRINCIPLES.map(([t, b], k) => <div key={t}><span className="mono n">{`0${k + 1}`}</span><h3>{t}</h3><p>{b}</p></div>)}
        </div>
        <div className="terms rv">
          <div><span className="mono">Oggi</span><p>Gratuito in fase di prova. Nessun addebito, nessuna carta.</p></div>
          <div><span className="mono">Piano Studio</span><p>209 € al mese oppure 1.999 € all’anno, 15 token al mese inclusi. Il lavoro quotidiano resta libero.</p></div>
          <div><span className="mono">Token</span><p>Solo per piano di allocazione, consegna di un budget e studio di un bando nuovo. Ricariche: 25 € ogni 10 token.</p></div>
        </div>
      </div></section>

      <section className="sect off" id="insights"><div className="wrap split">
        <div className="rv">
          <div className="sect-head"><span className="idx mono">06 / Insights</span><h2>Approfondimenti per chi segue la finanza agevolata.</h2>
            <p>Analisi normative, letture tecniche dei bandi, metodi di studio. Gli articoli sono in preparazione: nessun contenuto di riempimento.</p></div>
          <ul className="articles">
            {TOPICS.map(([t, b]) => (
              <li key={t}><span className="tag mono">{t}</span><div><p className="a-title">{b}</p><p className="a-meta mono">In arrivo</p></div></li>
            ))}
          </ul>
        </div>
        <div className="rv newsletter">
          <span className="idx mono">Newsletter</span>
          <h3>Aggiornamenti di finanza agevolata, a zero rumore.</h3>
          <p>Le novità che cambiano le agevolazioni per i clienti dello studio: circolari, nuove misure, scadenze. Niente promozioni.</p>
          <Newsletter />
        </div>
      </div></section>

      <section className="sect" id="faq"><div className="wrap">
        <div className="sect-head rv"><span className="idx mono">07 / Domande frequenti</span><h2>{FAQ_COUNT} risposte, dalla prima pratica al registro firmato.</h2>
          <p>Scritte per il commercialista che valuta QUANTO, partendo dal documento tecnico del sistema. Ciò che è in prova o da fare è detto.</p></div>
        <div className="rv"><FaqBlock /></div>
      </div></section>

      <section className="cta-final">
        <img className="hero-img" src="/landing/skyline-alba.jpg" alt="" />
        <div className="hero-shade strong" aria-hidden="true" />
        <div className="wrap rv">
          <span className="idx mono">08 / Accesso</span>
          <h2>La prossima pratica, preparala con QUANTO.</h2>
          <div className="hero-ctas">
            <button className="btn-cta big" onClick={() => setModal('register')}>Richiedi accesso<ArrowRight size={15} /></button>
            <button className="hero-link" onClick={onVision}>Leggi la visione<ArrowUpRight size={14} /></button>
          </div>
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
