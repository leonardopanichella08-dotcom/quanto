import React, { useMemo, useRef, useState } from 'react'
import { Search } from 'lucide-react'
import { searchTemplates } from '../data/itemTemplates'
import { CATEGORY_LABEL, CATEGORY_ORDER } from '../lib/format'

/** Cerca tra le voci tipiche di un budget di progetto (una per una scelte con criterio, non generate a caso) e
 * ne sceglie una come punto di partenza: categoria e campi tipici già compilati, tutto modificabile dopo. */
export default function ItemTemplatePicker({ onPick }) {
  const [q, setQ] = useState('')
  const inputRef = useRef(null)
  const results = useMemo(() => searchTemplates(q), [q])
  const groups = CATEGORY_ORDER.map((c) => [c, results.filter((t) => t.category === c)]).filter(([, l]) => l.length)

  return (
    <div className="absolute z-20 mt-1 w-[26rem] max-w-[92vw] card p-3 shadow-xl space-y-2">
      <div className="relative">
        <Search className="w-3.5 h-3.5 text-mute absolute left-2.5 top-1/2 -translate-y-1/2" />
        <input ref={inputRef} autoFocus value={q} onChange={(e) => setQ(e.target.value)}
          placeholder="Cerca una voce (es. consulenza legale, formatore, licenza software…)" aria-label="Cerca una voce tipica"
          className="field !pl-8 !py-1.5 text-xs" />
      </div>
      <div className="max-h-80 overflow-y-auto space-y-3 pr-1">
        {groups.map(([cat, list]) => (
          <div key={cat}>
            <p className="text-[10px] uppercase tracking-wide text-mute font-semibold px-1 mb-1">{CATEGORY_LABEL[cat]}</p>
            <div className="space-y-0.5">
              {list.map((t) => (
                <button key={t.id} onClick={() => onPick(t)} className="w-full text-left px-2.5 py-1.5 rounded-lg hover:bg-tint-2 transition">
                  <span className="block text-xs font-medium text-ink">{t.label}</span>
                  <span className="block text-[11px] text-mute leading-snug">{t.hint}</span>
                </button>
              ))}
            </div>
          </div>
        ))}
        {results.length === 0 && <p className="text-xs text-mute text-center py-4">Nessuna voce tipica trovata con questa ricerca.</p>}
      </div>
      <div className="border-t border-line pt-2 space-y-1.5">
        <span className="text-[11px] text-mute px-1">…oppure parti da una categoria vuota:</span>
        <div className="flex flex-wrap gap-1.5 px-1">
          {CATEGORY_ORDER.map((c) => (
            <button key={c} onClick={() => onPick({ category: c, label: `Nuova voce — ${CATEGORY_LABEL[c]}`, defaults: {} })}
              className="px-2 py-1 rounded-lg border border-line-strong text-[11px] text-ink-2 hover:text-ink hover:border-line-strong transition">
              {CATEGORY_LABEL[c]}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
