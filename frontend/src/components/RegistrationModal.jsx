import React, { useState } from 'react'
import { CheckCircle2, KeyRound, ShieldCheck, X } from 'lucide-react'
import { api, ApiError } from '../lib/api'

function Field({ label, value }) {
  return (
    <div className="space-y-0.5">
      <span className="text-neutral-500">{label}</span>
      <p className="text-neutral-200 break-all">{value}</p>
    </div>
  )
}

export default function RegistrationModal({ isOpen, onClose, merkleRoot, projectId, cepId, registry, attestation, onRegistered }) {
  const [loading, setLoading] = useState(false)
  const [notice, setNotice] = useState(null)
  const [error, setError] = useState(null)
  if (!isOpen) return null

  const handleRegister = async () => {
    setLoading(true); setError(null); setNotice(null)
    try {
      onRegistered(await api.register({ project_id: projectId, merkle_root: merkleRoot }))
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        setNotice(e.detail?.same_root
          ? 'Questo budget è già registrato con la stessa Merkle Root: nessuna nuova registrazione necessaria. Passa all’Auditor Portal per verificarlo.'
          : 'Il progetto risulta già registrato con una Merkle Root DIVERSA: il registro è append-only e non consente sovrascritture. Usa un nuovo identificativo di progetto per una nuova versione.')
      } else {
        setError(e.message)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="card max-w-lg w-full p-6 space-y-5 relative max-h-[90vh] overflow-y-auto">
        <button onClick={onClose} aria-label="Chiudi" className="absolute top-4 right-4 text-neutral-400 hover:text-white"><X className="w-5 h-5" /></button>
        <div className="flex items-center gap-3">
          <div className="p-3 bg-[#deffac]/10 border border-[#deffac]/20 text-[#deffac] rounded-xl"><ShieldCheck className="w-6 h-6" /></div>
          <div>
            <h3 className="font-bold text-base">Registrazione nel registro di asseverazione</h3>
            <p className="text-xs text-neutral-400">Catena di hash append-only, voce firmata Ed25519</p>
          </div>
        </div>

        <div className="space-y-2 text-xs font-mono bg-neutral-950 p-3 rounded-xl border border-neutral-800">
          <span className="text-neutral-500">{cepId} · progetto (opaco): {projectId}</span>
          <p className="text-[#deffac] break-all">{merkleRoot}</p>
          <p className="text-neutral-600 font-sans">Nel registro viene scritta solo questa impronta: nessun dato contabile o personale.</p>
        </div>

        {registry?.is_dev_key && (
          <p className="text-[11px] text-amber-300 bg-amber-500/10 border border-amber-500/20 rounded-xl p-3 flex gap-2">
            <KeyRound className="w-4 h-4 shrink-0" />
            Il server usa la chiave di firma di SVILUPPO: le attestazioni non hanno valore probatorio. Imposta QUANTO_SIGNING_KEY.
          </p>
        )}
        {notice && <p className="text-xs text-sky-300 bg-sky-500/10 border border-sky-500/20 rounded-xl p-3">{notice}</p>}
        {error && <p className="text-xs text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl p-3">{error}</p>}

        {attestation ? (
          <div className="space-y-3 text-[11px] font-mono">
            <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold font-sans"><CheckCircle2 className="w-4 h-4" />Registrata: voce n. {attestation.seq}</div>
            <div className="p-3 bg-neutral-950 border border-neutral-800 rounded-xl space-y-2">
              <Field label="Registrata il" value={attestation.registered_at} />
              <Field label="Hash voce" value={attestation.entry_hash} />
              <Field label="Hash voce precedente" value={attestation.prev_hash} />
              <Field label={`Firma Ed25519 (chiave ${attestation.key_id})`} value={attestation.signature} />
            </div>
          </div>
        ) : (
          <button onClick={handleRegister} disabled={loading} className="w-full py-3 bg-[#deffac] hover:bg-[#a8fd00] text-black font-bold text-sm rounded-xl transition disabled:opacity-50">
            {loading ? 'Registrazione…' : 'Conferma e registra'}
          </button>
        )}
      </div>
    </div>
  )
}
