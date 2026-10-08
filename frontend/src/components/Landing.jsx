import React, { useMemo, useState } from 'react'
import { ArrowRight, Check, Loader2, Lock, Search, ShieldCheck, Sparkles, X } from 'lucide-react'
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

const HEX = '0123456789abcdef'
function hexStr(rnd, n) { let s = ''; for (let i = 0; i < n; i++) s += HEX[Math.floor(rnd() * 16)]; return s }

/** Non punti a caso: una catena di blocchi firmati, come il registro vero di QUANTO — ogni blocco porta un'impronta
 * e si lega al precedente. Disposta in righe larghe così resta leggibile come "catena" anche a distanza. */
function ChainField({ rows = 3, perRow = 7, seed = 7, variant = '' }) {
  const { blocks, links, active } = useMemo(() => {
    const rnd = mulberry32(seed)
    const w = 1200, h = 460
    const bx = Array.from({ length: rows }, (_, r) => {
      const y = (h / (rows + 1)) * (r + 1) + (rnd() - 0.5) * 30
      const offset = (rnd() - 0.5) * 60
      return Array.from({ length: perRow }, (_, i) => ({
        id: `${r}-${i}`, x: offset + (w / (perRow - 0.4)) * (i + 0.4) + (rnd() - 0.5) * 24, y: y + (rnd() - 0.5) * 18, hex: hexStr(rnd, 4),
      }))
    })
    const flat = bx.flat()
    const lk = bx.flatMap((row) => row.slice(1).map((p, i) => [row[i], p]))
    const activeColors = ['#10b981', '#f59e0b', '#38bdf8']
    const act = [flat[4], flat[Math.floor(flat.length / 2)], flat[flat.length - 5]].filter(Boolean).map((p, i) => ({ ...p, color: activeColors[i], delay: i * 0.7 }))
    return { blocks: flat, links: lk, active: act }
  }, [rows, perRow, seed])
  return (
    <svg className={`chain-field ${variant}`} viewBox="0 0 1200 460" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      {links.map(([a, b], i) => <line key={i} x1={a.x + 18} y1={a.y} x2={b.x - 18} y2={b.y} stroke="#F6F2E2" strokeOpacity="0.08" strokeWidth="1" strokeDasharray="2 3" />)}
      {blocks.map((p) => (
        <g key={p.id} transform={`translate(${p.x}, ${p.y})`} opacity="0.5">
          <rect x="-17" y="-10" width="34" height="20" rx="4" fill="none" stroke="#F6F2E2" strokeOpacity="0.28" />
          <text x="0" y="4" textAnchor="middle" fontSize="6.5" fontFamily="JetBrains Mono, monospace" fill="#F6F2E2" fillOpacity="0.4">{p.hex}</text>
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

function DeterministicMockup() {
  return (
    <div className="mini-window compact" style={{ '--tilt': '0.8deg' }}>
      <div className="chrome"><i /><i /><i /></div>
      <div className="mw-body">
        <div className="mw-run"><span>Esecuzione di lunedì</span><span className="mono">a7f3…9c1e</span></div>
        <div className="mw-run"><span>Esecuzione di venerdì</span><span className="mono">a7f3…9c1e</span></div>
        <span className="ok-badge"><Check className="w-3.5 h-3.5" />Impronta identica</span>
      </div>
    </div>
  )
}
function SourceMockup() {
  return (
    <div className="mini-window compact" style={{ '--tilt': '-0.6deg' }}>
      <div className="chrome"><i /><i /><i /></div>
      <div className="mw-body">
        <div className="mw-rule-line"><span className="rule-k">Consulenze</span><span className="rule-v mono">max 20%</span></div>
        <p className="mw-src">Fonte: Art. 25, D.L. 18 ottobre 2012, n. 179, conv. L. 17 dicembre 2012, n. 221</p>
      </div>
    </div>
  )
}
function ApprovalMockup() {
  return (
    <div className="mini-window compact" style={{ '--tilt': '1deg' }}>
      <div className="chrome"><i /><i /><i /></div>
      <div className="mw-body">
        {['Personale', 'Beni strumentali', 'Consulenze', 'Documenti'].map((t) => <div key={t} className="mw-check"><Check className="w-3 h-3" />{t}</div>)}
        <span className="ok-badge"><ShieldCheck className="w-3.5 h-3.5" />Pronto da firmare</span>
      </div>
    </div>
  )
}

const STEPS = [
  { n: '01', title: 'Scegli il bando', body: "Cercalo per nome: QUANTO naviga le pagine ufficiali e scarica i documenti da solo.", Visual: SearchMockup },
  { n: '02', title: 'Costruisci il budget', body: 'Il budget del progetto del cliente: voci a mano, dalla bozza dei suoi bilanci o importate da Excel.', Visual: BudgetMockup },
  { n: '03', title: 'QUANTO controlla', body: 'Fino a 60 criteri, ognuno con la fonte da cui viene la regola.', Visual: HeatMockup },
  { n: '04', title: "Registra l'impronta", body: "Un'impronta digitale firmata, a prova di manomissione.", Visual: HashMockup },
  { n: '05', title: 'Alloca ai fondi', body: 'Decide quale fondo paga quale spesa nell\'anno, così mostri al cliente quanto resta a suo carico.', Visual: AllocationMockup },
]

export default function Landing({ onLogin, onAuditor, onVision }) {
  const [modal, setModal] = useState(null) // null | 'login' | 'register'
  return (
    <div className="qt-land">
      <div className="dark-zone">
        <div className="glow-yellow" style={{ width: 520, height: 520, top: -160, left: '50%', transform: 'translateX(-50%)' }} />
        <ChainField variant="clear-center" />
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
          <span className="eyebrow"><span className="dot" />Per studi commercialistici e consulenti</span>
          <h1 style={{ fontSize: 'clamp(28px, 4.3vw, 52px)', maxWidth: '24ch', lineHeight: 1.08 }}>La piattaforma di Finanza Agevolata ed Allocazione di Bilancio per <mark>Studi Commercialistici e Consulenti d’Impresa</mark></h1>
          <p className="sub">Potenzia il tuo studio con il motore deterministico che trasforma i dati di bilancio dei tuoi clienti in piani d’allocazione finanziaria e contributi pubblici. Elimina le ore di ricerca manuale e genera nuovi ricavi ad alto margine.</p>
          <div className="ctas">
            <button className="btn-solid" onClick={() => setModal('register')}>Inizia gratis<ArrowRight className="w-3.5 h-3.5" /></button>
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
          <p className="fineprint" style={{ marginTop: 14 }}>Illustrazione dell’interfaccia: i valori sono d’esempio.</p>
        </div></header>

        <svg className="curve-divider" viewBox="0 0 1200 64" preserveAspectRatio="none"><path d="M0,64 C300,0 900,0 1200,64 L1200,64 L0,64 Z" fill="var(--l-bg)" /></svg>
      </div>

      <section className="sect tight" id="vantaggi"><div className="wrap">
        <div className="sect-head">
          <span className="kicker">Vantaggi per lo studio</span>
          <h2>Più clienti seguiti, senza un analista in più</h2>
        </div>
        <div className="blocks" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))' }}>
          <div className="block-card"><div className="range mono">01</div><h4>Zero ore analista</h4><p style={{ fontSize: 13.5, lineHeight: 1.6, color: 'var(--l-ink-2)' }}>Analisi immediata dei bilanci civilistici del cliente e abbinamento deterministico ai bandi del catalogo nazionale: giorni di ricerca manuale ridotti a pochi minuti.</p></div>
          <div className="block-card"><div className="range mono">02</div><h4>Modello a consumo</h4><p style={{ fontSize: 13.5, lineHeight: 1.6, color: 'var(--l-ink-2)' }}>Ogni diagnosi di allocazione è un report che puoi riaddebitare direttamente al cliente o re-impacchettare come servizio di consulenza continuativa.</p></div>
          <div className="block-card"><div className="range mono">03</div><h4>Precisione deterministica a 60 criteri</h4><p style={{ fontSize: 13.5, lineHeight: 1.6, color: 'var(--l-ink-2)' }}>Nessuna IA generica e nessun testo inventato: calcoli esatti al centesimo, ogni regola con la sua fonte ufficiale dichiarata.</p></div>
        </div>
      </div></section>

      <section className="sect" id="come-funziona"><div className="wrap">
        <div className="sect-head">
          <span className="kicker">Come funziona</span>
          <h2>Dal bando al budget certificato</h2>
        </div>
        <p className="tool-note" style={{ marginBottom: 20 }}>Le immagini sono illustrazioni dell’interfaccia: i valori che vi compaiono non sono dati reali.</p>
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

      <section className="sect dark-sect">
        <ChainField rows={2} perRow={9} seed={23} variant="faint" />
        <div className="wrap">
          <div className="sect-head center">
            <span className="kicker">Perché fidarsi</span>
            <h2>Tre principi, non uno slogan</h2>
          </div>
          <div className="trio">
            <div className="trio-item"><DeterministicMockup /><h3>Deterministico</h3><p>Stesso budget, stesso risultato. Nessuna generazione: solo calcolo e regole tracciabili, riga per riga.</p></div>
            <div className="trio-item"><SourceMockup /><h3>Fonti dichiarate</h3><p>Ogni regola cita da dove viene — un decreto, una circolare — e quanto ci si può fidare di quella lettura.</p></div>
            <div className="trio-item"><HashMockup /><h3>Verificabile</h3><p>Registro firmato, a prova di manomissione: chiunque può controllare che un budget certificato non sia stato toccato.</p></div>
          </div>
        </div>
      </section>

      <section className="sect dark-sect">
        <div className="glow-warm" style={{ width: 700, height: 500, top: '10%', left: '50%', transform: 'translateX(-50%)' }} aria-hidden="true" />
        <div className="wrap">
          <div className="sect-head">
            <span className="kicker">Per chi è</span>
            <h2>Pensato per chi segue molti clienti</h2>
          </div>
          <div className="trio">
            <div className="trio-item"><ApprovalMockup /><h3>Studi commercialistici strutturati</h3><p>Con reparto consulenza o finanza straordinaria: uno studio segue decine di imprese clienti, con la fonte di ogni regola pronta da mostrare.</p></div>
            <div className="trio-item"><HeatMockup /><h3>Boutique di finanza agevolata</h3><p>Costruiscono il budget del progetto e sanno subito cosa verrebbe respinto, prima di presentare la candidatura per il cliente.</p></div>
            <div className="trio-item"><AllocationMockup /><h3>Fractional CFO e consulenti di direzione</h3><p>Pianificano più fondi insieme per l'impresa che seguono e sanno chi paga cosa lungo tutto l'anno.</p></div>
          </div>
        </div>
      </section>

      <section className="sect dark-sect" id="prezzi">
        <ChainField rows={2} perRow={8} seed={41} variant="low" />
        <div className="wrap">
          <div className="sect-head">
            <span className="kicker">Prezzi</span>
            <h2>Gratuito oggi. Onesto sempre.</h2>
            <p>QUANTO è gratuito in questa fase. Più avanti arriveranno piani a pagamento per team ed enti — chi si iscrive ora userà il prodotto gratuitamente più a lungo.</p>
          </div>
          <div className="pricing">
            <div className="price-card dark-card">
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
            <div className="price-card dark-card dim">
              <div className="tier">Presto</div>
              <div className="amount">In arrivo</div>
              <ul>
                <li>Piani a consumo per studi e team di consulenza</li>
                <li>Prezzi non ancora definiti</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <div className="dark-zone">
        <div className="glow-yellow" style={{ width: 460, height: 460, bottom: -200, left: '50%', transform: 'translateX(-50%)' }} />
        <div className="cta-final"><div className="wrap">
          <h2>Prima di inviare il prossimo budget del tuo cliente, controllalo.</h2>
          <p>Gratis in questa fase, senza carta di credito, pronto in un minuto.</p>
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
