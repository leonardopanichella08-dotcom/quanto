import React, { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { Play, X } from 'lucide-react'
import { LAUNCH, TUTORIALS } from '../data/tutorials'

function Player({ v, autoPlay = true }) {
  return <video className="w-full aspect-video rounded-2xl bg-black" src={v.src} poster={v.poster} controls autoPlay={autoPlay} playsInline preload="metadata" aria-label={v.title} />
}

/** Un video tutorial: una scheda piccola con la locandina; al clic si apre il lettore nello stesso punto. `variant="link"` è una pillola che apre il video in una finestra. */
export default function TutorialVideo({ id, variant = 'card' }) {
  const v = TUTORIALS[id]
  const [open, setOpen] = useState(false)
  useEffect(() => {
    if (variant !== 'link' || !open) return undefined
    const on = (e) => { if (e.key === 'Escape') setOpen(false) }
    window.addEventListener('keydown', on)
    return () => window.removeEventListener('keydown', on)
  }, [variant, open])
  if (!v || v.hidden) return null

  if (variant === 'link') {
    return (
      <>
        <button type="button" className="asst-chip inline-flex items-center gap-1.5" onClick={() => setOpen(true)}><Play className="w-3 h-3" />Guarda come funziona · {v.seconds} s</button>
        {open && createPortal(
          <div className="fixed inset-0 z-[80] bg-black/60 flex items-center justify-center p-4 md:p-10" role="dialog" aria-modal="true" aria-label={v.title} onClick={() => setOpen(false)}>
            <div className="w-full max-w-4xl space-y-3" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center gap-3 text-white"><span className="text-sm font-medium">{v.title}</span><button className="ml-auto rounded-full bg-white/15 hover:bg-white/25 p-1.5" onClick={() => setOpen(false)} aria-label="Chiudi il video"><X className="w-4 h-4" /></button></div>
              <Player v={v} />
            </div>
          </div>, document.body)}
      </>
    )
  }

  return (
    <div className="rounded-2xl bg-tint p-3">
      {open ? (
        <div className="space-y-2">
          <Player v={v} />
          <div className="flex items-center gap-3 px-1 text-xs text-ink-2"><span className="font-medium text-ink">{v.title}</span><span className="text-mute">Esempio con dati fittizi.</span><button className="ml-auto underline" onClick={() => setOpen(false)}>Chiudi</button></div>
        </div>
      ) : (
        <button type="button" onClick={() => setOpen(true)} className="w-full flex items-center gap-4 text-left group" aria-label={`Guarda il video: ${v.title}`}>
          <span className="relative shrink-0 w-36 sm:w-44 aspect-video rounded-xl overflow-hidden bg-black">
            <img src={v.poster} alt="" loading="lazy" className="w-full h-full object-cover" />
            <span className="absolute inset-0 flex items-center justify-center bg-black/25 group-hover:bg-black/10 transition"><span className="w-9 h-9 rounded-full bg-white/95 flex items-center justify-center shadow"><Play className="w-4 h-4 text-ink ml-0.5" /></span></span>
          </span>
          <span className="min-w-0">
            <span className="block text-[11px] text-mute">Video · {v.seconds} s</span>
            <span className="block text-sm font-semibold text-ink leading-snug">{v.title}</span>
            <span className="block text-xs text-ink-2 mt-0.5 leading-snug">{v.about}</span>
          </span>
        </button>
      )}
    </div>
  )
}

/** Il video di presentazione, per la pagina iniziale: parte da solo (senza audio, come impongono i browser) quando ci si passa sopra e si ferma quando si scorre oltre.
 *  Con i controlli del lettore si attiva l'audio (ha la musica), si mette in pausa o si porta avanti. Chi preferisce meno movimento deve premere play. */
export function LaunchVideo() {
  const ref = React.useRef(null)
  const wrap = React.useRef(null)
  const [started, setStarted] = useState(false)
  useEffect(() => {
    const v = ref.current
    const box = wrap.current
    if (!v || !box) return undefined
    const calm = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    let userPaused = false           // chi mette in pausa da sé non viene disturbato dallo scorrimento
    let byScroll = false
    const play = () => { if (!calm && !userPaused) v.play().then(() => setStarted(true)).catch(() => {}) }
    const stop = () => { if (!v.paused) { byScroll = true; v.pause() } }
    v.addEventListener('pause', () => { if (!byScroll) userPaused = true; byScroll = false })
    v.addEventListener('play', () => { userPaused = false })
    // visibile per metà o più → parte; altrimenti si ferma (si controlla a ogni scorrimento)
    const check = () => {
      const r = box.getBoundingClientRect()
      const seen = Math.min(r.bottom, window.innerHeight) - Math.max(r.top, 0)
      if (r.height > 0 && seen / r.height >= 0.5) play(); else stop()
    }
    window.addEventListener('scroll', check, { passive: true })
    window.addEventListener('resize', check)
    const onEnter = () => play()
    box.addEventListener('pointerenter', onEnter)
    check()
    return () => { window.removeEventListener('scroll', check); window.removeEventListener('resize', check); box.removeEventListener('pointerenter', onEnter); v.pause() }
  }, [])
  return (
    <div className="lp-video" ref={wrap}>
      <video ref={ref} src={LAUNCH.src} poster={LAUNCH.poster} muted loop={false} controls playsInline preload="metadata" aria-label={LAUNCH.title} />
      {!started && <span className="lp-video-cap">Scorri qui per guardarlo · {LAUNCH.seconds} s</span>}
    </div>
  )
}
