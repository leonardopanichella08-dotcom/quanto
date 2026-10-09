import React from 'react'

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
