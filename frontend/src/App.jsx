import React, { useCallback, useEffect, useRef, useState } from 'react'
import { Activity, BarChart3, BookOpen, CalendarRange, FileText, Lock, ShieldCheck } from 'lucide-react'
import BandiLibrary from './components/BandiLibrary'
import BudgetCanvas from './components/BudgetCanvas'
import AlgorithmLab from './components/AlgorithmLab'
import AllocationView from './components/AllocationView'
import PatternDemo from './components/PatternDemo'
import AuditorPortal from './components/AuditorPortal'
import RegistrationModal from './components/RegistrationModal'
import HQ from './components/hq/HQ'
import { api, download, fileToBase64 } from './lib/api'

const TABS = [
  ['bandi', 'Bandi', BookOpen], ['canvas', 'Budget', FileText], ['lab', 'Algoritmo', Activity], ['allocation', 'Allocazione', CalendarRange],
  ['pattern', 'Pattern', BarChart3], ['auditor', 'Auditor', ShieldCheck], ['hq', 'Quartier Generale', Lock],
]

const params = new URLSearchParams(window.location.search)
const EMPTY_REQUEST = { project_id: 'PRJ-2026-001', grant_rules: null, cost_items: [], entity_liquidity_eur: null, baseline_totals: null }

export default function App() {
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
  const seq = useRef(0)
  const debounce = useRef(null)

  const loadBandi = useCallback(async () => { setBandi(await api.bandi()) }, [])
  const loadRegistry = useCallback(() => api.registryStatus().then(setRegistry).catch(() => setRegistry({ offline: true })), [])
  useEffect(() => {
    loadBandi().catch((e) => setError(e.message))
    loadRegistry()
    api.fields().then((f) => setFields(f.fields)).catch(() => {})
    api.criteria().then((c) => setCriteriaTitles(Object.fromEntries(c.criteria.map((x) => [x.number, x.title])))).catch(() => {})
  }, [loadBandi, loadRegistry])

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
  const changeProject = (project_id) => { setRequest((r) => ({ ...r, project_id })); setAttestation(null) }

  const exportAs = async (kind) => {
    try {
      const blob = await (kind === 'pdf' ? api.exportPdf(request) : api.exportXlsx(request))
      download(blob, `${validation?.cep_id || 'budget'}.${kind}`)
    } catch (e) { setError(e.message) }
  }

  const openReplay = (response) => { setReplay(response); setTab('lab') }

  const banner = registry?.offline ? { dot: 'bg-neutral-600', text: 'Backend non raggiungibile', tone: 'text-neutral-400' }
    : !registry ? { dot: 'bg-neutral-600', text: 'Connessione al registro…', tone: 'text-neutral-400' }
      : !registry.intact ? { dot: 'bg-red-500', text: `Registro di asseverazione: CATENA NON INTEGRA (voce ${registry.broken_at_seq})`, tone: 'text-red-400' }
        : registry.is_dev_key ? { dot: 'bg-amber-500', text: `Registro attivo (${registry.entries} voci) — chiave di firma di SVILUPPO`, tone: 'text-amber-400' }
          : { dot: 'bg-emerald-500', text: `Registro di asseverazione integro (${registry.entries} voci) · chiave ${registry.key_id}`, tone: 'text-emerald-400' }

  const labData = replay || validation

  return (
    <div className="min-h-screen bg-[#0e0e0e] text-neutral-100">
      <header className="border-b border-neutral-800 bg-neutral-900/60 backdrop-blur-xl sticky top-0 z-40 px-4 md:px-8 py-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 bg-[#deffac] text-black font-black rounded-xl flex items-center justify-center text-xl shadow-[0_0_20px_rgba(222,255,172,0.2)]">Q</div>
          <div>
            <h1 className="text-lg font-extrabold tracking-tight text-[#deffac] leading-none">QUANTO</h1>
            <p className="text-[10px] text-neutral-400 uppercase tracking-widest font-mono">Financial Knowledge OS</p>
          </div>
        </div>
        <nav className="flex items-center gap-1 bg-neutral-950 border border-neutral-800 p-1 rounded-xl overflow-x-auto max-w-full">
          {TABS.map(([id, label, Icon]) => (
            <button key={id} onClick={() => setTab(id)}
              className={`px-3 py-2 text-xs font-bold rounded-lg transition flex items-center gap-1.5 whitespace-nowrap ${tab === id ? 'bg-[#deffac] text-black' : 'text-neutral-400 hover:text-white'}`}>
              <Icon className="w-3.5 h-3.5" />{label}
            </button>
          ))}
        </nav>
      </header>

      <main className="p-4 md:p-8 max-w-7xl mx-auto space-y-6">
        <div className="card p-3 px-5 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-3">
            <div className={`h-2.5 w-2.5 rounded-full ${banner.dot}`} />
            <span className={`text-xs font-mono ${banner.tone}`}>{banner.text}</span>
          </div>
          <span className="text-[11px] text-neutral-500 font-mono">{bando ? `Bando attivo: ${bando.name}` : 'Nessun bando selezionato'}</span>
        </div>

        {tab === 'bandi' && <BandiLibrary bandi={bandi} selectedId={bando?.bando_id} onSelect={selectBando} onReload={loadBandi} />}
        {tab === 'canvas' && (
          <BudgetCanvas bandi={bandi} bando={bando} request={request} fields={fields} validation={validation} loading={loading} error={error} busy={busy} importInfo={importInfo}
            onSelectBando={(id) => selectBando(id).catch(() => {})} onProjectId={changeProject} onItemsChange={changeItems} onDemo={loadDemo} onImport={importFile}
            onValidate={() => validate(request)} onRegister={() => setModalOpen(true)} onExport={exportAs}
            onOpenLab={() => { setReplay(null); setTab('lab') }} onDismissImport={() => setImportInfo(null)} onGoBandi={() => setTab('bandi')} />
        )}
        {tab === 'lab' && (
          <div className="space-y-4">
            {replay && <div className="p-3 rounded-xl border border-fuchsia-500/30 bg-fuchsia-500/10 text-fuchsia-200 text-xs flex items-center justify-between gap-3">
              <span>Stai rivedendo un’esecuzione salvata nella memoria ({replay.project_id} · {replay.bando_id}).</span>
              <button onClick={() => setReplay(null)} className="font-bold underline">Torna alla validazione corrente</button></div>}
            <AlgorithmLab validation={labData} title={labData?.project_id} criteriaTitles={criteriaTitles} />
          </div>
        )}
        {tab === 'allocation' && <AllocationView />}
        {tab === 'pattern' && <PatternDemo />}
        {tab === 'auditor' && (
          <AuditorPortal request={request} defaultProject={params.get('project') || validation?.project_id || request.project_id}
            defaultRoot={params.get('root') || validation?.merkle_root} />
        )}
        {tab === 'hq' && <HQ bandi={bandi} onReplay={openReplay} />}
      </main>

      {validation && (
        <RegistrationModal isOpen={modalOpen} onClose={() => setModalOpen(false)} merkleRoot={validation.merkle_root} projectId={validation.project_id}
          cepId={validation.cep_id} registry={registry} attestation={attestation} onRegistered={(a) => { setAttestation(a); loadRegistry() }} />
      )}
    </div>
  )
}
