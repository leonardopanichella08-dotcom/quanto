import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import BandiLibrary from './components/BandiLibrary'
import BudgetCanvas from './components/BudgetCanvas'
import AlgorithmLab from './components/AlgorithmLab'
import AllocationView from './components/AllocationView'
import PatternDemo from './components/PatternDemo'
import AuditorPortal from './components/AuditorPortal'
import RegistrationModal from './components/RegistrationModal'
import HQ from './components/hq/HQ'
import Guida from './components/Guida'
import Documents from './components/Documents'
import { ArrowLeft, FileScan, KeyRound, LogOut, BookOpen, Building2, Calculator, GitCompare, Library, ShieldCheck, Split } from 'lucide-react'
import { Mark, PageHead, Wordmark } from './components/ui'
import { NavContext } from './lib/nav'
import { api, download, fileToBase64, session } from './lib/api'
import { LoginScreen, PasswordModal } from './components/Login'

const TABS = [
  ['bandi', 'Bandi', Library], ['documents', 'Documenti', FileScan], ['canvas', 'Budget', Calculator], ['allocation', 'Allocazione', Split],
  ['pattern', 'Confronto', GitCompare], ['auditor', 'Verifica', ShieldCheck], ['guida', 'Guida', BookOpen], ['hq', 'Quartier Generale', Building2],
]
// Una riga per pagina: a cosa serve, in parole semplici.
const HEADS = {
  bandi: ['Bandi', 'Cerca un bando, leggi le sue regole e scegli quello per il tuo budget.'],
  documents: ['Documenti', 'Carica buste paga, bilanci e F24: ogni campo letto dice quanto è sicuro, e solo quello confermato entra nei calcoli.'],
  canvas: ['Budget', 'Inserisci le spese e controlla ogni regola del bando.'],
  allocation: ['Allocazione', 'Scopri quale fondo paga ogni spesa e quanto resta a carico tuo.'],
  pattern: ['Confronto', 'Guarda quanto il tuo budget somiglia a quelli dei progetti premiati.'],
  auditor: ['Verifica', 'Controlla che un budget certificato non sia stato modificato.'],
}

const params = new URLSearchParams(window.location.search)
const EMPTY_REQUEST = { project_id: 'PRJ-2026-001', grant_rules: null, cost_items: [], entity_liquidity_eur: null, baseline_totals: null }

export default function App() {
  const [user, setUser] = useState(session.user())
  const [pwOpen, setPwOpen] = useState(false)
  const [balanceRef, setBalanceRef] = useState(null)   // bilancio scelto per l'allocazione
  const [tab, setTab] = useState(TABS.some(([id]) => id === params.get('tab')) ? params.get('tab') : 'bandi')
  const [bandi, setBandi] = useState([])
  const [bando, setBando] = useState(null)
  const [request, setRequest] = useState(EMPTY_REQUEST)
  const [fields, setFields] = useState(null)
  const [criteriaTitles, setCriteriaTitles] = useState({})
  const [validation, setValidation] = useState(null)
  const [replay, setReplay] = useState(null)
  const [attestation, setAttestation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [importInfo, setImportInfo] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [registry, setRegistry] = useState(null)
  const [guideAnchor, setGuideAnchor] = useState(null)
  const [labFrom, setLabFrom] = useState('canvas')   // da dove si è arrivati alla vista dell'algoritmo
  const seq = useRef(0)
  const debounce = useRef(null)

  const loadBandi = useCallback(async () => { setBandi(await api.bandi()) }, [])
  const loadRegistry = useCallback(() => api.registryStatus().then(setRegistry).catch(() => setRegistry({ offline: true })), [])
  useEffect(() => {
    const out = () => setUser(null)
    window.addEventListener('quanto-logout', out)
    return () => window.removeEventListener('quanto-logout', out)
  }, [])
  const logout = () => { session.clear(); setUser(null); setBando(null); setValidation(null); setAttestation(null) }
  useEffect(() => {
    if (!user) return
    loadBandi().catch((e) => setError(e.message))
    loadRegistry()
    api.fields().then((f) => setFields(f.fields)).catch(() => {})
    api.criteria().then((c) => setCriteriaTitles(Object.fromEntries(c.criteria.map((x) => [x.number, x.title])))).catch(() => {})
  }, [user, loadBandi, loadRegistry])

  // Ogni validazione è una chiamata al server; le risposte fuori ordine vengono scartate.
  const validate = useCallback(async (req) => {
    if (!req.grant_rules || !req.cost_items.length) return
    const mine = ++seq.current
    setLoading(true); setError(null)
    try {
      const res = await api.validateBudget(req)
      if (mine === seq.current) setValidation(res)
    } catch (e) {
      if (mine === seq.current) setError(e.message)
    } finally {
      if (mine === seq.current) setLoading(false)
    }
  }, [])

  const selectBando = async (id) => {
    setBusy(true); setError(null)
    try {
      const detail = await api.bandoDetail(id)
      if (!detail.grant_rules) throw new Error('Questo bando non ha ancora regole pubblicate')
      await api.bandoSelect(id) // registra la scelta nella timeline
      setBando(detail)
      setRequest((r) => ({ ...r, grant_rules: detail.grant_rules }))
      setValidation(null); setAttestation(null); setImportInfo(null)
      setTab('canvas')
    } catch (e) { setError(e.message); throw e } finally { setBusy(false) }
  }

  const loadDemo = async (mode) => {
    if (!bando) return
    setBusy(true); setError(null)
    try {
      const scenario = await api.demo(bando.bando_id, mode)
      const next = { ...scenario, project_id: `${scenario.project_id}-${bando.bando_id.split('-')[0]}` }
      setRequest(next); setAttestation(null); setImportInfo(null)
      await validate(next)
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  const importFile = async (file) => {
    setBusy(true); setError(null)
    try {
      const res = await api.importItems({ filename: file.name, content_base64: await fileToBase64(file) })
      setImportInfo(res)
      if (res.items.length) {
        const next = { ...request, cost_items: res.items }
        setRequest(next); setAttestation(null)
        await validate(next)
      }
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  // Modifiche alle voci: se il budget era già stato validato si ricalcola sul server dopo una breve pausa.
  const changeItems = (items) => {
    const next = { ...request, cost_items: items }
    setRequest(next); setAttestation(null)
    if (validation) {
      clearTimeout(debounce.current)
      debounce.current = setTimeout(() => validate(next), 700)
    }
  }
  // voce di personale precompilata da una busta paga: solo campi sicuri o confermati; RAL dichiarata, FTE e durata li scrive l'utente
  const addPayslipItem = (res) => {
    const it = res.cost_item
    const item = { item_id: `P-DOC${res.document_id}`, ...it }
    changeItems([...request.cost_items.filter((x) => x.item_id !== item.item_id), item])
    setTab('canvas'); window.scrollTo({ top: 0 })
  }
  const changeProject = (project_id) => { setRequest((r) => ({ ...r, project_id })); setAttestation(null) }

  const exportAs = async (kind) => {
    try {
      const blob = await (kind === 'pdf' ? api.exportPdf(request) : api.exportXlsx(request))
      download(blob, `${validation?.cep_id || 'budget'}.${kind}`)
    } catch (e) { setError(e.message) }
  }

  const openReplay = (response) => { setReplay(response); setLabFrom('hq'); setTab('lab') }
  const nav = useMemo(() => ({ go: (t, anchor) => { setGuideAnchor(anchor || null); setTab(t); window.scrollTo({ top: 0 }) } }), [])

  const banner = registry?.offline ? { dot: 'bg-ink/30', text: 'Il server non risponde', tone: 'text-ink-2' }
    : !registry ? { dot: 'bg-ink/30', text: 'Mi collego al registro…', tone: 'text-ink-2' }
      : !registry.intact ? { dot: 'bg-red-500', text: `Attenzione: il registro delle certificazioni è stato alterato (voce ${registry.broken_at_seq})`, tone: 'text-red-700' }
        : registry.is_dev_key ? { dot: 'bg-amber-500', text: `Registro attivo (${registry.entries} ${registry.entries === 1 ? 'registrazione' : 'registrazioni'}) · chiave di prova: le certificazioni non valgono come prova`, tone: 'text-amber-700' }
          : { dot: 'bg-emerald-500', text: `Registro integro · ${registry.entries} ${registry.entries === 1 ? 'registrazione' : 'registrazioni'}`, tone: 'text-ink-2' }

  const labData = replay || validation
  const isManager = user?.role === 'MANAGER'
  const tabs = TABS.filter(([id]) => id !== 'hq' || isManager)

  if (!user && tab !== 'auditor') return <LoginScreen onLogin={setUser} onAuditor={() => setTab('auditor')} />

  return (
    <NavContext.Provider value={nav}>
    <div className="min-h-screen text-ink">
      <div className="liquid-bg" aria-hidden="true"><span /><span /><span /></div>
      <header className="md:sticky top-0 z-40 px-3 md:px-6 pt-3">
        <div className="glass-strong rounded-3xl max-w-7xl mx-auto px-3 md:px-4 py-2.5 flex flex-wrap items-center gap-x-4 gap-y-2">
          <button onClick={() => nav.go('bandi')} className="flex items-center gap-2.5 rounded-2xl" aria-label="Quanto, torna ai bandi">
            <Mark size={34} />
            <Wordmark height={20} className="text-ink" />
          </button>
          <nav className="flex items-center gap-1 overflow-x-auto max-w-full md:ml-auto order-3 md:order-none w-full md:w-auto -mx-1 px-1 pb-0.5" aria-label="Pagine">
            {tabs.map(([id, label, Icon]) => {
              const on = tab === id || (tab === 'lab' && id === 'canvas')
              return (
                <button key={id} onClick={() => nav.go(id)} aria-current={on ? 'page' : undefined}
                  className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-full text-[13px] whitespace-nowrap transition duration-200 ${on ? 'bg-liquid text-ink font-medium shadow-[0_6px_16px_-8px_rgba(200,185,0,0.9),0_0_0_1px_rgba(150,135,0,0.16)]' : 'text-ink-2 hover:text-ink hover:bg-white/70'}`}>
                  <Icon className="w-4 h-4" />{label}
                </button>
              )
            })}
          </nav>
          {user && (
            <div className="flex items-center gap-1 text-xs text-ink-2 order-2 md:order-none">
              <span className="hidden 2xl:inline max-w-[160px] truncate" title={user.email}>{user.name}</span>
              <button onClick={() => setPwOpen(true)} className="btn !px-2.5 !py-1.5" title="Cambia password" aria-label="Cambia password"><KeyRound className="w-3.5 h-3.5" /></button>
              <button onClick={logout} className="btn !px-2.5 !py-1.5" title="Esci" aria-label="Esci"><LogOut className="w-3.5 h-3.5" /></button>
            </div>
          )}
        </div>
      </header>

      <main className="px-4 md:px-8 pt-6 pb-16 max-w-7xl mx-auto space-y-6">
        {HEADS[tab] && <PageHead icon={TABS.find(([id]) => id === tab)[2]} title={HEADS[tab][0]} sub={HEADS[tab][1]}>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="chip"><span className={`h-1.5 w-1.5 rounded-full ${banner.dot}`} /><span className={banner.tone}>{banner.text}</span></span>
            <span className="chip">{bando ? `In uso: ${bando.name}` : 'Nessun bando scelto'}</span>
          </div>
        </PageHead>}

        {tab === 'bandi' && <BandiLibrary bandi={bandi} selectedId={bando?.bando_id} onSelect={selectBando} onReload={loadBandi} />}
        {tab === 'canvas' && (
          <BudgetCanvas bandi={bandi} bando={bando} request={request} fields={fields} validation={validation} loading={loading} error={error} busy={busy} importInfo={importInfo}
            onSelectBando={(id) => selectBando(id).catch(() => {})} onProjectId={changeProject} onItemsChange={changeItems} onDemo={loadDemo} onImport={importFile}
            onValidate={() => validate(request)} onRegister={() => setModalOpen(true)} onExport={exportAs}
            onOpenLab={() => { setReplay(null); setLabFrom('canvas'); setTab('lab') }} onDismissImport={() => setImportInfo(null)} onGoBandi={() => setTab('bandi')} />
        )}
        {tab === 'lab' && (
          <div className="space-y-4">
            <button onClick={() => nav.go(labFrom)} className="btn"><ArrowLeft className="w-3.5 h-3.5" />{labFrom === 'hq' ? 'Torna al Quartier Generale' : 'Torna al Budget'}</button>
            {replay && <div className="p-3 rounded-lg border border-brand/30 bg-brand/5 text-ink text-xs flex flex-wrap items-center justify-between gap-3">
              <span>Stai rivedendo un’esecuzione salvata ({replay.project_id} · {replay.bando_id}).</span>
              <button onClick={() => setReplay(null)} className="font-semibold text-brand-ink underline">Torna al controllo corrente</button></div>}
            <AlgorithmLab validation={labData} title={labData?.project_id} criteriaTitles={criteriaTitles} />
          </div>
        )}
        {tab === 'allocation' && <AllocationView balanceRef={balanceRef} onPickBalance={setBalanceRef} onGoDocuments={() => nav.go('documents')} />}
        {tab === 'documents' && <Documents onUseBalance={(id) => { setBalanceRef(id); nav.go('allocation') }} onUsePayslip={addPayslipItem} />}
        {tab === 'pattern' && <PatternDemo bando={bando} validation={validation} />}
        {tab === 'auditor' && (
          <AuditorPortal request={request} defaultProject={params.get('project') || validation?.project_id || request.project_id}
            defaultRoot={params.get('root') || validation?.merkle_root} />
        )}
        {tab === 'guida' && <Guida anchor={guideAnchor} />}
        {tab === 'hq' && isManager && <HQ bandi={bandi} onReplay={openReplay} user={user} />}
      </main>

      {pwOpen && <PasswordModal onClose={() => setPwOpen(false)} />}
      {validation && (
        <RegistrationModal isOpen={modalOpen} onClose={() => setModalOpen(false)} merkleRoot={validation.merkle_root} projectId={validation.project_id}
          cepId={validation.cep_id} registry={registry} attestation={attestation} onRegistered={(a) => { setAttestation(a); loadRegistry() }} />
      )}
    </div>
    </NavContext.Provider>
  )
}
