// Solo presentazione: nessun calcolo monetario.
const eur = new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' })
export const fmtEur = (n) => (n == null ? '—' : eur.format(n))
export const fmtNum = (n, digits = 2) => (n == null ? '—' : Number(n).toLocaleString('it-IT', { minimumFractionDigits: digits, maximumFractionDigits: digits }))
export const fmtPct = (n, digits = 1) => (n == null ? '—' : `${(n * 100).toLocaleString('it-IT', { maximumFractionDigits: digits })}%`)
export const fmtTs = (ts) => (ts ? new Date(ts).toLocaleString('it-IT', { dateStyle: 'short', timeStyle: 'medium' }) : '—')
export const fmtBytes = (n) => (n == null ? '—' : n < 1024 ? `${n} B` : n < 1048576 ? `${(n / 1024).toFixed(1)} KB` : `${(n / 1048576).toFixed(1)} MB`)

export const STATUS_STYLE = {
  APPROVED: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  CAP_EXCEEDED_ADJUSTED: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  REJECTED: 'bg-red-500/20 text-red-400 border-red-500/30',
  MISSING_DOCUMENTS: 'bg-sky-500/20 text-sky-300 border-sky-500/30',
}
export const STATUS_LABEL = { APPROVED: 'Approvata', CAP_EXCEEDED_ADJUSTED: 'Decurtata', REJECTED: 'Respinta', MISSING_DOCUMENTS: 'Sospesa' }

export const CATEGORY_LABEL = {
  PERSONNEL: 'Personale', CAPITAL_ASSETS: 'Beni strumentali', CONSULTING: 'Consulenze', OVERHEAD: 'Spese generali', TRAINING: 'Formazione',
}
export const CATEGORY_ORDER = ['PERSONNEL', 'CAPITAL_ASSETS', 'CONSULTING', 'OVERHEAD', 'TRAINING']

export const BANDO_STATUS_STYLE = (s = '') =>
  s.startsWith('APERTO') ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
    : s.startsWith('CHIUSO') ? 'bg-neutral-500/15 text-neutral-300 border-neutral-500/30'
      : s.startsWith('SANDBOX') ? 'bg-violet-500/15 text-violet-300 border-violet-500/30'
        : 'bg-amber-500/15 text-amber-300 border-amber-500/30'

export const KIND_STYLE = {
  OBBLIGO: 'bg-sky-500/15 text-sky-300 border-sky-500/30', DIVIETO: 'bg-red-500/15 text-red-300 border-red-500/30',
  LIMITE: 'bg-amber-500/15 text-amber-300 border-amber-500/30', INFO: 'bg-neutral-500/15 text-neutral-300 border-neutral-500/30',
  DA_REVISIONARE: 'bg-fuchsia-500/15 text-fuchsia-300 border-fuchsia-500/30',
}

// blocchi dei 60 criteri (Modulo 11)
export const CRITERIA_BLOCKS = [
  { from: 1, to: 15, label: 'Personale' }, { from: 16, to: 30, label: 'Beni strumentali' },
  { from: 31, to: 45, label: 'Consulenze e spese generali' }, { from: 46, to: 60, label: 'Tempo, cumulo, tracciabilità' },
]
