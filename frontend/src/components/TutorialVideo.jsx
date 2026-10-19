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

/** Il video di presentazione, per la pagina iniziale: grande, con locandina e avvio al clic (ha la musica, non parte da solo). */
export function LaunchVideo() {
  const [play, setPlay] = useState(false)
  return (
    <div className="lp-video">
      {play
        ? <video src={LAUNCH.src} poster={LAUNCH.poster} controls autoPlay playsInline preload="auto" aria-label={LAUNCH.title} />
        : (
          <button type="button" onClick={() => setPlay(true)} className="lp-video-poster" aria-label={`Guarda il video: ${LAUNCH.title}`}>
            <img src={LAUNCH.poster} alt="" loading="lazy" />
            <span className="lp-video-play"><Play size={26} /></span>
            <span className="lp-video-cap">Guarda · {LAUNCH.seconds} s</span>
          </button>
        )}
    </div>
  )
}
