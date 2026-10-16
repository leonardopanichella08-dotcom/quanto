import React, { useState } from 'react'

// Il logotipo è una maschera: il colore lo decide il testo attorno (bianco su scuro, inchiostro su chiaro).
export function Wordmark({ height = 22, className = '' }) {
  const mask = { WebkitMaskImage: 'url(/brand/quanto-wordmark.png)', maskImage: 'url(/brand/quanto-wordmark.png)', WebkitMaskSize: 'contain', maskSize: 'contain', WebkitMaskRepeat: 'no-repeat', maskRepeat: 'no-repeat', WebkitMaskPosition: 'left center', maskPosition: 'left center' }
  return <span role="img" aria-label="Quanto" className={`block bg-current ${className}`} style={{ ...mask, height, width: Math.round(height * 2.936) }} />
}

// La Q del marchio: quadrato giallo con la Q bianca.
export function Mark({ size = 36, className = '' }) {
  return <img src="/brand/quanto-mark.png" alt="" width={size} height={size} className={`rounded-[22%] shrink-0 ${className}`} />
}

// Titolo di pagina: titolo e una riga che dice a cosa serve la pagina; a destra, lo stato (registro, bando in uso).
export function PageHead({ title, sub, children }) {
  return (
    <div className="flex flex-wrap items-end gap-x-6 gap-y-3 pb-5 border-b border-line">
      <div className="min-w-[16rem] flex-1">
        <h2 className="text-[22px] font-semibold tracking-tight leading-tight">{title}</h2>
        {sub && <p className="text-[13px] text-ink-2 mt-1 max-w-2xl">{sub}</p>}
      </div>
      {children}
    </div>
  )
}

// Titolo di sezione dentro una pagina o un riquadro: icona piccola + testo.
export function SectionTitle({ icon: Icon, children, className = '' }) {
  return (
    <h3 className={`flex items-center gap-2 font-semibold tracking-tight text-[15px] ${className}`}>
      {Icon && <Icon className="w-4 h-4 text-mute" />}
      {children}
    </h3>
  )
}

// Riquadro principale di una pagina: bordo sottile e, se serve, una piccola intestazione con il nome della sezione.
export function ChromeCard({ label, className = '', bodyClassName = 'p-6', children }) {
  return (
    <div className={`card overflow-hidden ${className}`}>
      <div className={bodyClassName}>{children}</div>
    </div>
  )
}

// Sezione che si apre e si chiude, con un riassunto sempre visibile nell'intestazione: chi la lascia chiusa vede comunque a che punto è.
// Il contenuto resta montato anche da chiuso, così le cose scritte e le caricamenti in corso non si perdono.
export function Fold({ id, icon: Icon, title, summary, badge, tone = 'neutral', open, onToggle, children, action }) {
  const tones = { neutral: 'border-line text-ink-2', warn: 'border-amber-500/40 text-amber-700 bg-amber-500/5', ok: 'border-emerald-500/30 text-emerald-700 bg-emerald-500/5' }
  return (
    <section id={id} className="card overflow-hidden scroll-mt-20" data-open={open ? 'true' : 'false'}>
      <div className="flex items-center gap-3 px-5 py-3.5">
        <button type="button" onClick={onToggle} aria-expanded={!!open} aria-controls={`${id}-body`} className="flex items-center gap-3 min-w-0 flex-1 text-left">
          <span className={`inline-block transition-transform ${open ? 'rotate-90' : ''} text-mute`} aria-hidden="true">▸</span>
          {Icon && <Icon className="w-4 h-4 text-mute shrink-0" />}
          <span className="min-w-0"><span className="block text-[15px] font-semibold tracking-tight text-ink">{title}</span>
            {summary && <span className="block text-xs text-ink-2 mt-0.5 truncate">{summary}</span>}</span>
        </button>
        {badge && <span className={`px-2 py-0.5 rounded-full border text-[11px] font-medium whitespace-nowrap ${tones[tone]}`}>{badge}</span>}
        {action}
      </div>
      <div id={`${id}-body`} className={open ? 'px-5 pb-5 pt-1 space-y-4 border-t border-line' : 'hidden'}>{children}</div>
    </section>
  )
}

// Una piccola «i»: la spiegazione sta nascosta finché non serve. Serve a tenere le pagine pulite senza togliere il perché delle cose.
export function Info({ children, label = 'Come funziona' }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="text-xs text-ink-2">
      <button type="button" onClick={() => setOpen(!open)} aria-expanded={open} className="inline-flex items-center gap-1.5 text-mute hover:text-ink">
        <span className="w-4 h-4 rounded-full border border-line-strong inline-flex items-center justify-center text-[10px] font-semibold leading-none" aria-hidden="true">i</span>{label}
      </button>
      {open && <div className="mt-2 leading-relaxed max-w-2xl space-y-1.5">{children}</div>}
    </div>
  )
}
