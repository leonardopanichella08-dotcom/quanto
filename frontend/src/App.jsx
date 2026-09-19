import React, { useCallback, useEffect, useRef, useState } from 'react'
import { BarChart3, CalendarRange, Database, FileText, ShieldCheck } from 'lucide-react'
import BudgetCanvas from './components/BudgetCanvas'
import AllocationView from './components/AllocationView'
import PatternDemo from './components/PatternDemo'
import AuditorPortal from './components/AuditorPortal'
import IngestionPanel from './components/IngestionPanel'
import RegistrationModal from './components/RegistrationModal'
import { api, download } from './lib/api'
import { SEED_REQUEST } from './data/mockSeed'

const TABS = [
  ['canvas', 'Budget Canvas', FileText],
  ['allocation', 'Allocazione', CalendarRange],
  ['pattern', 'Demo Pattern', BarChart3],
  ['auditor', 'Auditor Portal', ShieldCheck],
  ['ingestion', 'Ingestion', Database],
]

const params = new URLSearchParams(window.location.search)

export default function App() {
  const [activeTab, setActiveTab] = useState(TABS.some(([id]) => id === params.get('tab')) ? params.get('tab') : 'canvas')
  const [request, setRequest] = useState(SEED_REQUEST)
  const [validation, setValidation] = useState(null)
  const [attestation, setAttestation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [registry, setRegistry] = useState(null)
  const seq = useRef(0)

  const loadRegistry = useCallback(() => api.registryStatus().then(setRegistry).catch(() => setRegistry({ offline: true })), [])
  useEffect(() => { loadRegistry() }, [loadRegistry])

  // Ogni validazione è una chiamata al server; le risposte fuori ordine vengono scartate.
  const validate = useCallback(async (req) => {
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

  const editFte = (itemId, fte) => {
    if (!(fte > 0 && fte <= 1)) return
    const next = { ...request, cost_items: request.cost_items.map((i) => (i.item_id === itemId ? { ...i, fte_allocation: fte } : i)) }
    setRequest(next)
    setAttestation(null) // un budget modificato ha una nuova radice: la registrazione precedente non lo riguarda
    validate(next)
  }

  const exportAs = (kind) => async () => {
    try {
      const blob = await (kind === 'pdf' ? api.exportPdf(request) : api.exportXlsx(request))
      download(blob, `${validation?.cep_id || 'budget'}.${kind}`)
    } catch (e) { setError(e.message) }
  }

  const banner = registry?.offline
    ? { dot: 'bg-neutral-600', text: 'Backend non raggiungibile', tone: 'text-neutral-400' }
    : !registry
      ? { dot: 'bg-neutral-600', text: 'Connessione al registro…', tone: 'text-neutral-400' }
      : !registry.intact
        ? { dot: 'bg-red-500', text: `Registro di asseverazione: CATENA NON INTEGRA (voce ${registry.broken_at_seq})`, tone: 'text-red-400' }
        : registry.is_dev_key
          ? { dot: 'bg-amber-500', text: `Registro attivo (${registry.entries} voci) — chiave di firma di SVILUPPO`, tone: 'text-amber-400' }
          : { dot: 'bg-emerald-500', text: `Registro di asseverazione integro (${registry.entries} voci) · chiave ${registry.key_id}`, tone: 'text-emerald-400' }

  return (
    <div className="min-h-screen bg-[#0e0e0e] text-neutral-100">
      <header className="border-b border-neutral-800 bg-neutral-900/60 backdrop-blur-xl sticky top-0 z-40 px-4 md:px-8 py-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 bg-[#deffac] text-black font-black rounded-xl flex items-center justify-center text-xl shadow-[0_0_20px_rgba(222,255,172,0.2)]">Q</div>
          <div>
            <h1 className="text-lg font-extrabold tracking-tight text-[#deffac]">QUANTO</h1>
            <p className="text-[10px] text-neutral-400 uppercase tracking-widest font-mono">Financial Knowledge Operating System</p>
          </div>
        </div>
        <nav className="flex items-center gap-1 bg-neutral-950 border border-neutral-800 p-1 rounded-xl overflow-x-auto max-w-full">
          {TABS.map(([id, label, Icon]) => (
            <button key={id} onClick={() => setActiveTab(id)}
              className={`px-4 py-2 text-xs font-bold rounded-lg transition flex items-center gap-2 whitespace-nowrap ${activeTab === id ? 'bg-[#deffac] text-black' : 'text-neutral-400 hover:text-white'}`}>
              <Icon className="w-3.5 h-3.5" />{label}
            </button>
          ))}
        </nav>
      </header>

      <main className="p-4 md:p-8 max-w-7xl mx-auto space-y-6">
        <div className="card p-4 px-6 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-3">
            <div className={`h-2.5 w-2.5 rounded-full ${banner.dot}`} />
            <span className={`text-xs font-mono ${banner.tone}`}>{banner.text}</span>
          </div>
          <span className="text-[11px] text-neutral-500 font-mono">Pseudonimizzazione lato server · nel registro solo la Merkle Root</span>
        </div>

        {activeTab === 'canvas' && (
          <BudgetCanvas request={request} validation={validation} loading={loading} error={error}
            onValidate={() => validate(request)} onEditFte={editFte} onExport={exportAs('xlsx')} onExportPdf={exportAs('pdf')} onRegister={() => setModalOpen(true)} />
        )}
        {activeTab === 'allocation' && <AllocationView />}
        {activeTab === 'pattern' && <PatternDemo />}
        {activeTab === 'auditor' && (
          <AuditorPortal request={request} defaultProject={params.get('project') || validation?.project_id || request.project_id}
            defaultRoot={params.get('root') || validation?.merkle_root} />
        )}
        {activeTab === 'ingestion' && <IngestionPanel />}
      </main>

      {validation && (
        <RegistrationModal isOpen={modalOpen} onClose={() => setModalOpen(false)} merkleRoot={validation.merkle_root} projectId={validation.project_id}
          cepId={validation.cep_id} registry={registry} attestation={attestation} onRegistered={(a) => { setAttestation(a); loadRegistry() }} />
      )}
    </div>
  )
}
