// Solo presentazione: nessun calcolo monetario.
const eur = new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' })
export const fmtEur = (n) => (n == null ? '—' : eur.format(n))
export const fmtNum = (n, digits = 2) => (n == null ? '—' : Number(n).toLocaleString('it-IT', { minimumFractionDigits: digits, maximumFractionDigits: digits }))
export const fmtPct = (n, digits = 1) => (n == null ? '—' : `${(n * 100).toLocaleString('it-IT', { maximumFractionDigits: digits })}%`)

export const STATUS_STYLE = {
  APPROVED: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  CAP_EXCEEDED_ADJUSTED: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  REJECTED: 'bg-red-500/20 text-red-400 border-red-500/30',
  MISSING_DOCUMENTS: 'bg-red-500/20 text-red-400 border-red-500/30',
}
