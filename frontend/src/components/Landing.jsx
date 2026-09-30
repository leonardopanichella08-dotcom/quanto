import React, { useMemo, useState } from 'react'
import { ArrowRight, Check, Loader2, Lock, ShieldCheck, X } from 'lucide-react'
import { api, session } from '../lib/api'
import { Mark, Wordmark } from './ui'
import './Landing.css'

const CELL_COLOR = { OK: '#10b981', ADJUSTED: '#f59e0b', REJECTED: '#ef4444', WAIT: '#38bdf8', NONE: '#0E0E0A1f' }
// esempio fisso (non è un bando reale): illustra la distribuzione tipica di un controllo a 60 criteri
const DEMO_OUTCOMES = [
  'OK', 'OK', 'OK', 'ADJUSTED', 'OK', 'OK', 'OK', 'REJECTED', 'OK', 'OK', 'OK', 'OK', 'WAIT', 'OK', 'OK',
  'OK', 'OK', 'NONE', 'OK', 'OK', 'OK', 'ADJUSTED', 'OK', 'OK', 'NONE', 'OK', 'OK', 'OK', 'OK', 'OK',
  'OK', 'ADJUSTED', 'OK', 'OK', 'OK', 'NONE', 'OK', 'REJECTED', 'OK', 'OK', 'OK', 'OK', 'OK', 'NONE', 'OK',
  'OK', 'OK', 'OK', 'WAIT', 'OK', 'OK', 'OK', 'NONE', 'OK', 'OK', 'ADJUSTED', 'OK', 'OK', 'OK', 'OK',
]
const BLOCKS = [
  { from: 1, to: 15, label: 'Personale' }, { from: 16, to: 30, label: 'Beni strumentali' },
  { from: 31, to: 45, label: 'Consulenze e spese generali' }, { from: 46, to: 60, label: 'Date, cumulo, tracciabilità' },
]

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
        {isRegister && (
          <><label htmlFor="ln-name">Nome</label><input id="ln-name" required autoFocus value={name} onChange={(e) => setName(e.target.value)} /></>
        )}
        <label htmlFor="ln-email">E-mail</label>
        <input id="ln-email" type="email" required autoFocus={!isRegister} autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} />
        <label htmlFor="ln-pw">Password</label>
        <input id="ln-pw" type="password" required minLength={isRegister ? 12 : 1} autoComplete={isRegister ? 'new-password' : 'current-password'} value={password} onChange={(e) => setPassword(e.target.value)} />
        {isRegister && <p style={{ fontSize: 11.5, color: 'var(--l-mute)', marginTop: 6 }}>Almeno 12 caratteri, lettere e almeno un numero o simbolo.</p>}
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

function MicroTool() {
  const [total, setTotal] = useState(150000)
  const [consulenze, setConsulenze] = useState(40000)
  const limitPct = 0.20
  const limit = total * limitPct
  const pct = total > 0 ? consulenze / total : 0
  const over = Math.max(0, consulenze - limit)
  const ok = consulenze <= limit
  return (
    <div className="tool-card">
      <div>
        <div className="tool-field">
          <label htmlFor="mt-total">Totale del progetto</label>
          <div className="row"><span>€</span><input id="mt-total" type="number" min={1000} step={1000} value={total} onChange={(e) => setTotal(Math.max(1000, Number(e.target.value) || 0))} /></div>
        </div>
        <div className="tool-field">
          <label htmlFor="mt-cons">Di cui consulenze</label>
          <div className="row"><span>€</span><input id="mt-cons" type="number" min={0} step={1000} value={consulenze} onChange={(e) => setConsulenze(Math.max(0, Number(e.target.value) || 0))} /></div>
          <input type="range" min={0} max={total} step={1000} value={Math.min(consulenze, total)} onChange={(e) => setConsulenze(Number(e.target.value))} style={{ marginTop: 10 }} />
        </div>
        <p className="tool-rule">Regola d'esempio, come tante nei bandi reali: <b>le consulenze non possono superare il 20% del totale ammissibile</b>.</p>
      </div>
      <div>
        <div className={`tool-result ${ok ? 'ok' : 'fail'}`}>
          <div className="verdict">{ok ? 'Ammesso' : 'Ridotto'}</div>
          <div className="bar-track"><div className="bar-fill" style={{ width: `${Math.min(100, pct * 100)}%`, background: ok ? 'var(--l-green)' : 'var(--l-red)' }} /></div>
          <div className="detail mono">{Math.round(pct * 100)}% del totale · tetto {Math.round(limitPct * 100)}% ({limit.toLocaleString('it-IT')} €)</div>
          <p className="detail" style={{ marginTop: 10 }}>
            {ok
              ? `Le consulenze richieste rientrano nel tetto: ${consulenze.toLocaleString('it-IT')} € ammessi.`
              : `Superano il tetto di ${over.toLocaleString('it-IT')} €: verrebbero ammessi solo ${limit.toLocaleString('it-IT')} €, il resto respinto — con la regola citata, non a caso.`}
          </p>
        </div>
        <p className="tool-note">Esempio illustrativo, non collegato a un bando reale. Nel prodotto ogni regola come questa ha una fonte ufficiale dichiarata, e i controlli sono fino a 60.</p>
      </div>
    </div>
  )
}

export default function Landing({ onLogin, onAuditor }) {
  const [modal, setModal] = useState(null) // null | 'login' | 'register'
  return (
    <div className="qt-land">
      <nav className="qt-nav"><div className="wrap row">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}><Mark size={30} /><Wordmark height={17} /></div>
        <div className="links">
          <a href="#come-funziona">Come funziona</a>
          <a href="#controlli">I 60 controlli</a>
          <a href="#prezzi">Prezzi</a>
        </div>
        <div className="actions">
          <button className="btn-ghost" onClick={() => setModal('login')}>Accedi</button>
          <button className="btn-solid" onClick={() => setModal('register')}>Inizia gratis</button>
        </div>
      </div></nav>

      <header className="hero"><div className="wrap hero-grid">
        <div>
          <span className="eyebrow"><span className="dot" />Controllo budget per bandi pubblici</span>
          <h1>Sai se il budget verrà <mark>respinto</mark>. Prima di inviarlo.</h1>
          <p className="sub">QUANTO controlla ogni voce di spesa contro le regole ufficiali del bando scelto — fino a 60 criteri, ciascuno con la sua fonte dichiarata. Non un'intelligenza artificiale che indovina: un motore che calcola, sempre allo stesso modo.</p>
          <div className="ctas">
            <button className="btn-solid" onClick={() => setModal('register')}>Inizia gratis<ArrowRight className="w-3.5 h-3.5" /></button>
            <a href="#prova" className="btn-line">Prova un controllo</a>
          </div>
          <p className="fineprint">Gratuito oggi. Nessuna carta di credito richiesta.</p>
        </div>
        <div className="heat-card">
          <div className="top"><span className="name">Beni strumentali — Nuova Sabatini</span><span className="score mono">46/60</span></div>
          <div className="heat-grid">{DEMO_OUTCOMES.map((o, i) => <div key={i} className="heat-cell" style={{ background: CELL_COLOR[o] }} title={`#${i + 1}`} />)}</div>
          <div className="heat-legend">
            <span><i style={{ background: CELL_COLOR.OK }} />superato</span>
            <span><i style={{ background: CELL_COLOR.ADJUSTED }} />ridotto</span>
            <span><i style={{ background: CELL_COLOR.REJECTED }} />respinto</span>
            <span><i style={{ background: CELL_COLOR.WAIT }} />da documentare</span>
            <span><i style={{ background: CELL_COLOR.NONE }} />non valutato</span>
          </div>
        </div>
      </div></header>

      <section className="sect" id="prova"><div className="wrap">
        <div className="sect-head">
          <span className="kicker">Provalo subito</span>
          <h2>Un assaggio di una delle 60 regole</h2>
          <p>Cambia i numeri e guarda il risultato aggiornarsi. Nel prodotto vero, questo succede per ogni voce del tuo budget, con la fonte della regola sempre visibile.</p>
        </div>
        <MicroTool />
      </div></section>

      <section className="sect" id="come-funziona"><div className="wrap">
        <div className="sect-head">
          <span className="kicker">Come funziona</span>
          <h2>Dal bando al budget certificato, cinque passaggi</h2>
        </div>
        <div className="steps">
          <div className="step"><div className="n mono">01</div><h3>Scegli il bando</h3><p>Cercalo per nome: QUANTO naviga le pagine ufficiali e scarica i documenti da solo.</p></div>
          <div className="step"><div className="n mono">02</div><h3>Costruisci il budget</h3><p>Voci di spesa a mano, da un esempio o importate da Excel.</p></div>
          <div className="step"><div className="n mono">03</div><h3>QUANTO controlla</h3><p>Fino a 60 criteri, ognuno con la fonte da cui viene la regola.</p></div>
          <div className="step"><div className="n mono">04</div><h3>Registra l'impronta</h3><p>Un'impronta digitale firmata, a prova di manomissione.</p></div>
          <div className="step"><div className="n mono">05</div><h3>Alloca ai fondi</h3><p>Decide chi paga cosa nell'anno, riducendo quanto resta a tuo carico.</p></div>
        </div>
      </div></section>

      <section className="sect" id="controlli"><div className="wrap">
        <div className="sect-head">
          <span className="kicker">Il motore</span>
          <h2>60 criteri, in quattro gruppi</h2>
          <p>Ogni criterio è attivo solo se il bando dice qualcosa in merito: quello che i documenti non dicono resta dichiarato, mai inventato.</p>
        </div>
        <div className="blocks">
          {BLOCKS.map((b) => (
            <div key={b.label} className="block-card">
              <div className="range mono">#{b.from}–{b.to}</div>
              <h4>{b.label}</h4>
              <div className="block-mini">{Array.from({ length: 15 }).map((_, i) => <i key={i} />)}</div>
            </div>
          ))}
        </div>
      </div></section>

      <section className="sect"><div className="wrap">
        <div className="sect-head">
          <span className="kicker">Perché fidarsi</span>
          <h2>Tre principi, non uno slogan</h2>
        </div>
        <div className="pillars">
          <div className="pillar"><div className="num mono">01</div><h3>Deterministico</h3><p>Stesso budget, stesso risultato. Nessuna generazione: solo calcolo e regole tracciabili, riga per riga.</p></div>
          <div className="pillar"><div className="num mono">02</div><h3>Fonti dichiarate</h3><p>Ogni regola cita da dove viene — un decreto, una circolare — e quanto ci si può fidare di quella lettura.</p></div>
          <div className="pillar"><div className="num mono">03</div><h3>Verificabile</h3><p>Registro firmato, a prova di manomissione: chiunque può controllare che un budget certificato non sia stato toccato.</p></div>
        </div>
      </div></section>

      <section className="sect"><div className="wrap">
        <div className="sect-head">
          <span className="kicker">Per chi è</span>
          <h2>Chi lo usa già così</h2>
        </div>
        <div className="audience">
          <div className="aud-card"><h4>Consulenti e commercialisti</h4><p>Controllano il budget di un cliente prima di firmarlo, con la fonte di ogni regola pronta da mostrare.</p></div>
          <div className="aud-card"><h4>PMI e startup</h4><p>Costruiscono il budget del progetto e sanno subito cosa verrebbe respinto, prima di candidarsi.</p></div>
          <div className="aud-card"><h4>Enti ed associazioni</h4><p>Pianificano più fondi insieme e sanno chi paga cosa lungo tutto l'anno.</p></div>
        </div>
      </div></section>

      <section className="sect" id="prezzi" style={{ borderBottom: 'none' }}><div className="wrap">
        <div className="sect-head">
          <span className="kicker">Prezzi</span>
          <h2>Gratuito oggi. Onesto sempre.</h2>
          <p>QUANTO è gratuito in questa fase. Più avanti arriveranno piani a pagamento per team ed enti — chi si iscrive ora userà il prodotto gratuitamente più a lungo.</p>
        </div>
        <div className="pricing">
          <div className="price-card">
            <div className="tier">Oggi</div>
            <div className="amount">Gratis</div>
            <ul>
              <li>Bandi, ricerca e controllo del budget</li>
              <li>Fino a 60 criteri per bando</li>
              <li>Registro firmato e verifica</li>
              <li>Documenti privati e allocazione dei fondi</li>
            </ul>
            <button className="btn-solid" style={{ width: '100%', justifyContent: 'center' }} onClick={() => setModal('register')}>Inizia gratis</button>
          </div>
          <div className="price-card dim">
            <div className="tier">Presto</div>
            <div className="amount">In arrivo</div>
            <ul>
              <li>Piani per team ed enti</li>
              <li>Prezzi non ancora definiti</li>
            </ul>
          </div>
        </div>
      </div></section>

      <div className="cta-final"><div className="wrap">
        <h2>Prima di inviare il prossimo budget, controllalo.</h2>
        <p>Gratis, senza carta di credito, pronto in un minuto.</p>
        <button className="btn-yellow btn-solid" onClick={() => setModal('register')}>Inizia gratis<ArrowRight className="w-3.5 h-3.5" /></button>
      </div></div>

      <footer className="qt-foot"><div className="wrap" style={{ display: 'flex', alignItems: 'center', gap: 14, width: '100%' }}>
        <span className="copy">© 2026 QUANTO</span>
        <button className="btn-ghost" style={{ padding: '4px 0' }} onClick={onAuditor}><ShieldCheck className="w-3.5 h-3.5" style={{ marginRight: 4 }} />Sei un revisore? Verifica un budget certificato</button>
        <span className="sp" />
        <button className="btn-ghost" style={{ padding: '4px 0' }} onClick={() => setModal('login')}><Lock className="w-3 h-3" style={{ marginRight: 4 }} />Accedi</button>
      </div></footer>

      {modal && <AuthModal mode={modal} onClose={() => setModal(null)} onSwitch={setModal} onDone={onLogin} />}
    </div>
  )
}
