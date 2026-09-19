import React from 'react'
import { Lightbulb } from 'lucide-react'

// Striscia introduttiva di ogni pagina: cosa fa, cosa si può fare, cosa aspettarsi.
export default function PageIntro({ title, children, tips = [] }) {
  return (
    <div className="rounded-2xl border border-[#deffac]/15 bg-[#deffac]/[0.04] px-5 py-3 flex gap-3">
      <Lightbulb className="w-4 h-4 text-[#deffac] shrink-0 mt-0.5" />
      <div className="text-xs text-neutral-300 leading-relaxed space-y-1 min-w-0">
        <p><span className="font-bold text-[#deffac]">{title}.</span> {children}</p>
        {tips.length > 0 && <ul className="list-disc pl-4 text-neutral-400 space-y-0.5">{tips.map((t) => <li key={t}>{t}</li>)}</ul>}
      </div>
    </div>
  )
}
