import React, { useMemo, useState } from 'react'
import { ArrowRight, Check, Loader2, Lock, Search, ShieldCheck, Sparkles, Target, X } from 'lucide-react'
import { api, session } from '../lib/api'
import { Mark, Wordmark } from './ui'
import './Landing.css'

const CELL_COLOR = { OK: '#10b981', ADJUSTED: '#f59e0b', REJECTED: '#ef4444', WAIT: '#38bdf8', NONE: '#F6F2E21f' }
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

// PRNG deterministico (nessuna libreria): un campo di nodi stabile, non casuale ad ogni render.
function mulberry32(seed) {
  let a = seed
  return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296 }
}

function NodeField() {
  const { dots, links, active } = useMemo(() => {
    const rnd = mulberry32(42)
    const pts = Array.from({ length: 70 }, (_, i) => ({ id: i, x: rnd() * 1200, y: rnd() * 460, r: 1.1 + rnd() * 1.1 }))
    const activeColors = ['#10b981', '#10b981', '#f59e0b', '#ef4444', '#10b981', '#38bdf8']
    const act = Array.from({ length: 6 }, (_, i) => ({ ...pts[i * 9], color: activeColors[i], delay: i * 0.5 }))
    const lk = []
    for (let i = 0; i < pts.length; i++) {
      for (let j = i + 1; j < pts.length; j++) {
        const dx = pts[i].x - pts[j].x, dy = pts[i].y - pts[j].y
        const d = Math.sqrt(dx * dx + dy * dy)
        if (d < 95 && rnd() > 0.55) lk.push([pts[i], pts[j]])
      }
    }
    return { dots: pts, links: lk, active: act }
  }, [])
  return (
    <svg className="node-field" viewBox="0 0 1200 460" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      {links.map(([a, b], i) => <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="#F6F2E2" strokeOpacity="0.06" strokeWidth="1" />)}
      {dots.map((p) => <circle key={p.id} cx={p.x} cy={p.y} r={p.r} fill="#F6F2E2" fillOpacity="0.22" />)}
      {active.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={2} fill={p.color} className="node-pulse" style={{ '--d': `${p.delay}s`, '--base-r': 2 }} />
      ))}
    </svg>
  )
}

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

function Gauge({ sharePct, limitPct, size = 128 }) {
  const r = 52, c = 2 * Math.PI * r
  const ok = sharePct <= limitPct
  const color = ok ? '#10b981' : '#ef4444'
  const ceiling = limitPct * 1.4 // il cerchio si riempie del tutto a 1,4 volte il tetto: dà margine visivo per mostrare quanto si è andati oltre
  const fraction = ceiling > 0 ? Math.min(1, sharePct / ceiling) : 0
  return (
    <svg width={size} height={size} viewBox="0 0 120 120">
      <circle cx="60" cy="60" r={r} fill="none" stroke="var(--l-line)" strokeWidth="10" />
      <circle cx="60" cy="60" r={r} fill="none" stroke={color} strokeWidth="10" strokeLinecap="round"
        strokeDasharray={c} strokeDashoffset={c * (1 - fraction)} transform="rotate(-90 60 60)" style={{ transition: 'stroke-dashoffset .3s ease, stroke .3s ease' }} />
      <text x="60" y="56" textAnchor="middle" fontSize="22" fontWeight="700" fill="var(--l-ink)" fontFamily="JetBrains Mono, monospace">{Math.round(sharePct)}%</text>
      <text x="60" y="74" textAnchor="middle" fontSize="9" fill="var(--l-mute)" fontFamily="Archivo, sans-serif">del totale</text>
    </svg>
  )
}

function MicroTool() {
  const [total, setTotal] = useState(150000)
  const [consulenze, setConsulenze] = useState(40000)
  const limitPct = 0.20
  const limit = total * limitPct
  const pct = total > 0 ? (consulenze / total) * 100 : 0
  const over = Math.max(0, consulenze - limit)
  const ok = consulenze <= limit
  return (
    <div className="tool-window">
      <div className="chrome"><i /><i /><i /><span className="url mono">quanto.app — controllo in tempo reale</span></div>
      <div className="tool-body">
        <div>
          <div className="tool-field">
            <label htmlFor="mt-total">Totale del progetto</label>
            <div className="row"><span>€</span><input id="mt-total" type="number" min={1000} step={1000} value={total} onChange={(e) => setTotal(Math.max(1000, Number(e.target.value) || 0))} /></div>
          </div>
          <div className="tool-field">
            <label htmlFor="mt-cons">Di cui consulenze</label>
            <div className="row"><span>€</span><input id="mt-cons" type="number" min={0} step={1000} value={consulenze} onChange={(e) => setConsulenze(Math.max(0, Number(e.target.value) || 0))} /></div>
            <input type="range" min={0} max={total} step={1000} value={Math.min(consulenze, total)} onChange={(e) => setConsulenze(Number(e.target.value))} />
          </div>
          <p className="tool-rule">Regola d'esempio, come tante nei bandi reali: <b>le consulenze non possono superare il 20% del totale ammissibile</b>.</p>
        </div>
        <div className="gauge-wrap">
          <Gauge sharePct={pct} limitPct={limitPct * 100} />
          <div className={`gauge-verdict ${ok ? 'ok' : 'fail'}`}>{ok ? 'Ammesso' : 'Ridotto'}</div>
          <p className="gauge-detail">
            {ok ? `${consulenze.toLocaleString('it-IT')} € rientrano nel tetto di ${limit.toLocaleString('it-IT')} €.`
              : `Superano il tetto di ${over.toLocaleString('it-IT')} €: ne verrebbero ammessi solo ${limit.toLocaleString('it-IT')} €.`}
          </p>
        </div>
      </div>
      <p className="tool-note">Esempio illustrativo, non collegato a un bando reale. Nel prodotto ogni regola come questa ha una fonte ufficiale dichiarata, e i controlli sono fino a 60.</p>
    </div>
  )
}

const CAT_COLOR = { p: '#38bdf8', b: '#f59e0b', c: '#10b981' }
const MINI_HEAT = ['OK', 'OK', 'ADJUSTED', 'OK', 'OK', 'OK', 'OK', 'REJECTED', 'OK', 'OK', 'OK', 'OK', 'OK', 'OK', 'WAIT', 'OK', 'OK', 'OK']

function SearchMockup() {
  return (
    <div className="mini-window" style={{ '--tilt': '-1.4deg' }}>
      <div className="chrome"><i /><i /><i /></div>
      <div className="mw-body">
        <div className="mw-search"><Search className="w-3.5 h-3.5" style={{ opacity: 0.6 }} />Resto al Sud</div>
        <div className="mw-result">✓ Trovato — Invitalia, decreto ufficiale</div>
        <div className="mw-result muted">Scarico 3 PDF ufficiali…</div>
      </div>
    </div>
  )
}
function BudgetMockup() {
  const rows = [['Project manager', 'p', '42.000 €'], ['Macchinario CNC', 'b', '68.500 €'], ['Consulenza audit', 'c', '12.000 €']]
  return (
    <div className="mini-window" style={{ '--tilt': '1.2deg' }}>
      <div className="chrome"><i /><i /><i /></div>
      <div className="mw-body" style={{ minHeight: 'auto', padding: '18px 20px' }}>
        {rows.map(([label, cat, amt]) => <div key={label} className="mw-line"><span className="dot" style={{ background: CAT_COLOR[cat] }} />{label}<span className="amt">{amt}</span></div>)}
      </div>
    </div>
  )
}
function HeatMockup() {
  return (
    <div className="mini-window" style={{ '--tilt': '-1deg' }}>
      <div className="chrome"><i /><i /><i /></div>
      <div className="mw-body" style={{ minHeight: 'auto' }}>
        <div className="mw-heat">{MINI_HEAT.map((o, i) => <i key={i} style={{ background: CELL_COLOR[o] }} />)}</div>
      </div>
    </div>
  )
}
function HashMockup() {
  return (
    <div className="mini-window" style={{ '--tilt': '1.6deg' }}>
      <div className="chrome"><i /><i /><i /></div>
      <div className="mw-body">
        <div className="mw-hash">0x7f3a9c1e5b8d2f4a…<br />6c0e9b1d3a7f5c2e</div>
        <span className="mw-badge"><ShieldCheck className="w-3.5 h-3.5" />Firmato e verificabile</span>
      </div>
    </div>
  )
}
function AllocationMockup() {
  return (
    <div className="mini-window" style={{ '--tilt': '-1.3deg' }}>
      <div className="chrome"><i /><i /><i /></div>
      <div className="mw-body" style={{ minHeight: 'auto' }}>
        <div className="mw-bar"><span style={{ width: '62%', background: '#10b981' }}>Fondo · 62%</span><span style={{ width: '38%', background: 'var(--d-line)', color: 'var(--d-ink)' }}>Ente · 38%</span></div>
        <div className="mw-bar-labels"><span>€ 0</span><span>€ 100.000</span></div>
      </div>
    </div>
  )
}

const STEPS = [
  { n: '01', title: 'Scegli il bando', body: "Cercalo per nome: QUANTO naviga le pagine ufficiali e scarica i documenti da solo.", Visual: SearchMockup },
  { n: '02', title: 'Costruisci il budget', body: 'Voci di spesa a mano, da un esempio o importate da Excel.', Visual: BudgetMockup },
  { n: '03', title: 'QUANTO controlla', body: 'Fino a 60 criteri, ognuno con la fonte da cui viene la regola.', Visual: HeatMockup },
  { n: '04', title: "Registra l'impronta", body: "Un'impronta digitale firmata, a prova di manomissione.", Visual: HashMockup },
  { n: '05', title: 'Alloca ai fondi', body: 'Decide chi paga cosa nell\'anno, riducendo quanto resta a tuo carico.', Visual: AllocationMockup },
]

export default function Landing({ onLogin, onAuditor, onVision }) {
  const [modal, setModal] = useState(null) // null | 'login' | 'register'
  return (
    <div className="qt-land">
      <div className="dark-zone">
        <div className="glow-yellow" style={{ width: 520, height: 520, top: -160, left: '50%', transform: 'translateX(-50%)' }} />
        <NodeField />
        <svg className="grain" width="100%" height="100%"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" stitchTiles="stitch" /></filter><rect width="100%" height="100%" filter="url(#n)" /></svg>

        <nav className="qt-nav"><div className="wrap row">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}><Mark size={30} /><Wordmark height={17} className="wordmark-mask" /></div>
          <div className="links">
            <a href="#come-funziona">Come funziona</a>
            <a href="#controlli">I 60 controlli</a>
            <a href="#prezzi">Prezzi</a>
            <button onClick={onVision}><Sparkles className="w-3.5 h-3.5" style={{ marginRight: 5 }} />La visione</button>
          </div>
          <div className="actions">
            <button className="btn-ghost" onClick={() => setModal('login')}>Accedi</button>
            <button className="btn-solid" onClick={() => setModal('register')}>Inizia gratis</button>
          </div>
        </div></nav>

        <header className="hero"><div className="wrap hero-inner">
          <span className="eyebrow"><span className="dot" />Controllo budget per bandi pubblici</span>
          <h1>Sai se il budget verrà <mark>respinto</mark>. Prima di inviarlo.</h1>
          <p className="sub">QUANTO controlla ogni voce di spesa contro le regole ufficiali del bando scelto — fino a 60 criteri, ciascuno con la sua fonte dichiarata. Non un'intelligenza artificiale che indovina: un motore che calcola, sempre allo stesso modo.</p>
          <div className="ctas">
            <button className="btn-solid" onClick={() => setModal('register')}>Inizia gratis<ArrowRight className="w-3.5 h-3.5" /></button>
            <a href="#prova" className="btn-line">Prova un controllo</a>
          </div>
          <p className="fineprint">Gratuito oggi. Nessuna carta di credito richiesta.</p>

          <div className="window-wrap"><div className="window">
            <div className="chrome"><i /><i /><i /><span className="url">quanto.app/budget</span></div>
            <div className="body">
              <div className="top"><span className="name">Beni strumentali — Nuova Sabatini</span><span className="score mono">46/60 superati</span></div>
              <div className="heat-grid">{DEMO_OUTCOMES.map((o, i) => <div key={i} className="heat-cell" style={{ background: CELL_COLOR[o] }} title={`#${i + 1}`} />)}</div>
              <div className="heat-legend">
                <span><i style={{ background: CELL_COLOR.OK }} />superato</span>
                <span><i style={{ background: CELL_COLOR.ADJUSTED }} />ridotto</span>
                <span><i style={{ background: CELL_COLOR.REJECTED }} />respinto</span>
                <span><i style={{ background: CELL_COLOR.WAIT }} />da documentare</span>
                <span><i style={{ background: CELL_COLOR.NONE }} />non valutato</span>
              </div>
            </div>
          </div></div>
        </div></header>

        <svg className="curve-divider" viewBox="0 0 1200 64" preserveAspectRatio="none"><path d="M0,64 C300,0 900,0 1200,64 L1200,64 L0,64 Z" fill="var(--l-bg)" /></svg>
      </div>

      <section className="sect tight" id="prova"><div className="wrap">
        <div className="sect-head center">
          <span className="kicker">Provalo subito</span>
          <h2>Un assaggio di una delle 60 regole</h2>
          <p>Cambia i numeri e guarda il risultato aggiornarsi. Nel prodotto vero, questo succede per ogni voce del tuo budget, con la fonte della regola sempre visibile.</p>
        </div>
        <MicroTool />
      </div></section>

      <section className="sect" id="come-funziona"><div className="wrap">
        <div className="sect-head">
          <span className="kicker">Come funziona</span>
          <h2>Dal bando al budget certificato</h2>
        </div>
        <div className="funziona-rows">
          {STEPS.map((s, i) => (
            <div key={s.n} className={`funziona-row ${i % 2 ? 'rev' : ''}`}>
              <div className="fr-text"><span className="step-n">{s.n}</span><h3>{s.title}</h3><p>{s.body}</p></div>
              <div className="fr-visual"><s.Visual /></div>
            </div>
          ))}
        </div>
      </div></section>

      <section className="sect" id="controlli">
        <div className="pattern-grid" aria-hidden="true" />
        <div className="wrap">
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
        </div>
      </section>

      <section className="sect">
        <div className="glow-warm" style={{ width: 700, height: 500, top: '10%', left: '50%', transform: 'translateX(-50%)' }} aria-hidden="true" />
        <div className="wrap">
          <div className="sect-head center">
            <span className="kicker">Perché fidarsi</span>
            <h2>Tre principi, non uno slogan</h2>
          </div>
          <div className="pillars">
            <div className="pillar"><div className="icon"><Target className="w-5 h-5" /></div><h3>Deterministico</h3><p>Stesso budget, stesso risultato. Nessuna generazione: solo calcolo e regole tracciabili, riga per riga.</p></div>
            <div className="pillar"><div className="icon"><Check className="w-5 h-5" /></div><h3>Fonti dichiarate</h3><p>Ogni regola cita da dove viene — un decreto, una circolare — e quanto ci si può fidare di quella lettura.</p></div>
            <div className="pillar"><div className="icon"><ShieldCheck className="w-5 h-5" /></div><h3>Verificabile</h3><p>Registro firmato, a prova di manomissione: chiunque può controllare che un budget certificato non sia stato toccato.</p></div>
          </div>
        </div>
      </section>

      <section className="sect band-alt">
        <div className="pattern-dots" aria-hidden="true" />
        <div className="wrap">
          <div className="sect-head">
            <span className="kicker">Per chi è</span>
            <h2>Chi lo usa già così</h2>
          </div>
          <div className="audience">
            <div className="aud-card"><h4>Consulenti e commercialisti</h4><p>Controllano il budget di un cliente prima di firmarlo, con la fonte di ogni regola pronta da mostrare.</p></div>
            <div className="aud-card"><h4>PMI e startup</h4><p>Costruiscono il budget del progetto e sanno subito cosa verrebbe respinto, prima di candidarsi.</p></div>
            <div className="aud-card"><h4>Enti ed associazioni</h4><p>Pianificano più fondi insieme e sanno chi paga cosa lungo tutto l'anno.</p></div>
          </div>
        </div>
      </section>

      <section className="sect" id="prezzi">
        <div className="pattern-dots" aria-hidden="true" />
        <div className="wrap">
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
              <button className="btn-line" style={{ width: '100%', justifyContent: 'center' }} onClick={() => setModal('register')}>Inizia gratis</button>
            </div>
            <div className="price-card dim">
              <div className="tier">Presto</div>
              <div className="amount">In arrivo</div>
              <ul>
                <li>Piani annuali a consumo per team ed enti</li>
                <li>Prezzi non ancora definiti</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <div className="dark-zone">
        <div className="glow-yellow" style={{ width: 460, height: 460, bottom: -200, left: '50%', transform: 'translateX(-50%)' }} />
        <div className="cta-final"><div className="wrap">
          <h2>Prima di inviare il prossimo budget, controllalo.</h2>
          <p>Gratis, senza carta di credito, pronto in un minuto.</p>
          <button className="btn-solid" onClick={() => setModal('register')}>Inizia gratis<ArrowRight className="w-3.5 h-3.5" /></button>
        </div></div>

        <footer className="qt-foot"><div className="wrap" style={{ display: 'flex', alignItems: 'center', gap: 14, width: '100%', flexWrap: 'wrap' }}>
          <span className="copy">© 2026 QUANTO</span>
          <button onClick={onVision}><Sparkles className="w-3.5 h-3.5" style={{ marginRight: 4 }} />La visione</button>
          <button onClick={onAuditor}><ShieldCheck className="w-3.5 h-3.5" style={{ marginRight: 4 }} />Sei un revisore?</button>
          <span className="sp" />
          <button onClick={() => setModal('login')}><Lock className="w-3 h-3" style={{ marginRight: 4 }} />Accedi</button>
        </div></footer>
      </div>

      {modal && <AuthModal mode={modal} onClose={() => setModal(null)} onSwitch={setModal} onDone={onLogin} />}
    </div>
  )
}
