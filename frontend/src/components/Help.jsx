import React, { useEffect, useRef, useState } from 'react'
import { X } from 'lucide-react'
import { lookup } from '../data/help'

/** Riquadro con titolo, spiegazione ed esempio. Posizione `fixed` calcolata dal pulsante: non viene tagliato dai pannelli con scorrimento. */
function Popover({ id, pos, onClose }) {
  const h = lookup(id)
  if (!h) return null
  // solo <span>: il riquadro può stare dentro un <p> (parole cliccabili nei testi) senza HTML non valido
  return (
    <span role="dialog" aria-label={h.title} style={pos}
      className="fixed z-50 block card !bg-tint p-4 shadow-2xl space-y-2 text-left font-sans font-normal normal-case max-h-[70vh] overflow-y-auto">
      <span className="flex items-start justify-between gap-3">
        <span className="block text-sm font-semibold text-ink">{h.title}</span>
        <button type="button" onClick={onClose} aria-label="Chiudi" className="text-mute hover:text-ink shrink-0"><X className="w-4 h-4" /></button>
      </span>
      <span className="block text-xs text-ink-2 leading-relaxed">{h.text}</span>
      {h.example && <span className="block text-xs text-ink-2 leading-relaxed border-l-2 border-brand/40 pl-3"><span className="text-mute">Esempio · </span>{h.example}</span>}
    </span>
  )
}

function usePop() {
  const [pos, setPos] = useState(null)
  const ref = useRef(null)
  const close = () => setPos(null)
  useEffect(() => {
    if (!pos) return undefined
    const onDown = (e) => { if (ref.current && !ref.current.contains(e.target) && !e.target.closest?.('[role="dialog"]')) close() }
    const onKey = (e) => { if (e.key === 'Escape') close() }
    const onScroll = (e) => { if (!e.target.closest?.('[role="dialog"]')) close() }
    document.addEventListener('mousedown', onDown); document.addEventListener('keydown', onKey)
    window.addEventListener('scroll', onScroll, true); window.addEventListener('resize', close)
    return () => {
      document.removeEventListener('mousedown', onDown); document.removeEventListener('keydown', onKey)
      window.removeEventListener('scroll', onScroll, true); window.removeEventListener('resize', close)
    }
  }, [pos])
  const toggle = () => {
    if (pos) { close(); return }
    const r = ref.current.getBoundingClientRect()
    const width = Math.min(340, window.innerWidth - 16)
    const left = Math.max(8, Math.min(r.left, window.innerWidth - width - 8))
    // sotto il pulsante se c'è posto, altrimenti sopra
    const below = window.innerHeight - r.bottom > 220 || r.top < 220
    setPos(below ? { left, width, top: r.bottom + 8 } : { left, width, bottom: window.innerHeight - r.top + 8 })
  }
  return { pos, close, toggle, ref }
}

/** Piccola icona “?” accanto a una funzione: clic per leggere cosa fa e un esempio. */
export function Hint({ id, className = '' }) {
  const { pos, close, toggle, ref } = usePop()
  const h = lookup(id)
  if (!h) return null
  return (
    <span ref={ref} className={`inline-flex align-middle ${className}`}>
      <button type="button" onClick={toggle} aria-expanded={Boolean(pos)} aria-label={`Spiegazione: ${h.title}`}
        className="w-4 h-4 rounded-full border border-line-strong text-[10px] leading-none text-ink-2 hover:text-ink hover:border-line-strong inline-flex items-center justify-center transition">?</button>
      {pos && <Popover id={id} pos={pos} onClose={close} />}
    </span>
  )
}

/** Parola difficile: sottolineata a puntini, il clic mostra la spiegazione semplice. */
export function Term({ id, children }) {
  const { pos, close, toggle, ref } = usePop()
  const h = lookup(id)
  return (
    <span ref={ref} className="inline">
      <button type="button" onClick={toggle} aria-expanded={Boolean(pos)}
        className="underline decoration-dotted decoration-mute underline-offset-4 hover:text-ink hover:decoration-ink-2 cursor-help">{children ?? h?.title}</button>
      {pos && <Popover id={id} pos={pos} onClose={close} />}
    </span>
  )
}
