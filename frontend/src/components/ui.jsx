import React from 'react'

// Il logotipo è una maschera: il colore lo decide il testo attorno (bianco su scuro, inchiostro su chiaro).
export function Wordmark({ height = 22, className = '' }) {
  const mask = { WebkitMaskImage: 'url(/brand/quanto-wordmark.png)', maskImage: 'url(/brand/quanto-wordmark.png)', WebkitMaskSize: 'contain', maskSize: 'contain', WebkitMaskRepeat: 'no-repeat', maskRepeat: 'no-repeat', WebkitMaskPosition: 'left center', maskPosition: 'left center' }
  return <span role="img" aria-label="Quanto" className={`block bg-current ${className}`} style={{ ...mask, height, width: Math.round(height * 2.936) }} />
}

// La Q del marchio: quadrato giallo con la Q bianca.
export function Mark({ size = 36, className = '' }) {
  return <img src="/brand/quanto-mark.png" alt="" width={size} height={size} className={`rounded-[28%] shrink-0 shadow-[0_6px_16px_-6px_rgba(200,185,0,0.9)] ${className}`} />
}

// Titolo di pagina: icona in un riquadro giallo liquido, titolo e una riga che dice a cosa serve la pagina.
export function PageHead({ icon: Icon, title, sub, children }) {
  return (
    <div className="flex flex-wrap items-center gap-3.5">
      <span className="icon-tile w-11 h-11 rounded-2xl"><Icon className="w-5 h-5" /></span>
      <div className="min-w-[15rem] flex-1">
        <h2 className="text-2xl font-display font-bold tracking-tight leading-tight">{title}</h2>
        {sub && <p className="text-sm text-ink-2 mt-0.5">{sub}</p>}
      </div>
      {children}
    </div>
  )
}

// Titolo di sezione dentro una pagina o un riquadro: icona piccola + testo.
export function SectionTitle({ icon: Icon, children, className = '' }) {
  return (
    <h3 className={`flex items-center gap-2 font-display font-bold tracking-tight text-base ${className}`}>
      {Icon && <span className="icon-tile w-7 h-7 rounded-lg"><Icon className="w-3.5 h-3.5" /></span>}
      {children}
    </h3>
  )
}

// Finestra in stile "mockup" (tre pallini, come le anteprime della homepage): per il riquadro principale di una pagina,
// non per ogni scheda — resta un accento, non una regola applicata ovunque.
export function ChromeCard({ label, className = '', bodyClassName = 'p-6', children }) {
  return (
    <div className={`card overflow-hidden ${className}`}>
      <div className="flex items-center gap-1.5 px-4 py-2.5 border-b border-line bg-tint">
        <i className="w-2 h-2 rounded-full bg-red-400/70" /><i className="w-2 h-2 rounded-full bg-amber-400/70" /><i className="w-2 h-2 rounded-full bg-emerald-400/70" />
        {label && <span className="ml-2.5 text-[11px] font-code text-mute truncate">{label}</span>}
      </div>
      <div className={bodyClassName}>{children}</div>
    </div>
  )
}
