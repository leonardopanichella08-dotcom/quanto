import React, { useState } from 'react'
import { ChevronDown } from 'lucide-react'

const FLOWS = {
  budget: {
    title: 'Come nasce il budget',
    lead: 'Prima si legge il bando, poi si prepara la bozza, poi si controlla: i 60 criteri guardano il budget, non il bando, e lo fanno a ogni modifica.',
    steps: [
      ['Leggo il bando', 'Dai testi ufficiali ricavo le regole: percentuali, tetti, voci escluse, date. Dove il bando tace, quel controllo non si applica.'],
      ['Preparo la bozza', 'Dai documenti dell’azienda: ogni persona con livello e RAL, le spese una per una. Lascio fuori ciò che il bando non ammette e riduco ciò che supera i tetti.'],
      ['Controllo con i 60 criteri', 'Ogni voce risulta ammessa, ridotta, respinta o in attesa di un documento, con il motivo. Si ricontrolla da solo a ogni modifica.'],
      ['Correggi e registra', 'Sistemi le voci segnalate. Il budget ammesso si esporta e si registra con un’impronta firmata.'],
    ],
    notes: [
      ['E se non ci sono template?', 'I template (pagina Confronto) suggeriscono come ripartire il budget guardando aziende simili con il loro esito. Se non ce ne sono, la bozza parte solo dai dati dell’azienda: QUANTO lo dice e non inventa un consiglio.'],
      ['È un budget «vincente»?', 'QUANTO lo rende ammissibile e coerente con le regole del bando. Se vincerai dipende dal progetto e dagli altri candidati: la graduatoria non la prevede nessuno, e QUANTO non finge di farlo.'],
    ],
  },
  allocation: {
    title: 'Come lavora l’allocazione',
    lead: 'L’allocazione decide quale bando paga cosa. Non è ancora un budget: i budget si ricavano dopo, uno per bando.',
    steps: [
      ['Stimo le spese', 'Le spese previste dell’anno: budget dell’azienda, piano degli investimenti, oppure la variazione dei bilanci.'],
      ['Trovo i bandi adatti', 'Per ogni bando studiato: puoi partecipare? Quanto copre sulle tue spese?'],
      ['Assegno ogni spesa a un bando', 'Senza doppioni: la stessa spesa non si fa pagare due volte, e i tetti dei bandi e il de minimis sono rispettati.'],
      ['Ricavo un budget per bando', 'Ogni bando ha le sue regole e si presenta a parte: per questo non esiste un budget unico. Poi si controllano con i 60 criteri nella pagina Budget.'],
    ],
    notes: [
      ['Spese dell’anno o progetto?', 'I bandi che non chiedono un progetto (crediti d’imposta, spese commerciali…) coprono le spese dell’anno. I bandi che finanziano progetti coprono le spese nuove di un progetto: si calcolano a parte.'],
    ],
  },
}

/** Il percorso in quattro passi, in parole semplici: chiuso per difetto, si apre a richiesta. */
export default function HowItWorks({ kind }) {
  const f = FLOWS[kind]
  const [open, setOpen] = useState(false)
  if (!f) return null
  return (
    <section className="card overflow-hidden">
      <button type="button" onClick={() => setOpen(!open)} aria-expanded={open} className="w-full flex items-center gap-3 px-6 py-4 text-left">
        <span className="min-w-0 flex-1">
          <span className="block text-[15px] font-semibold tracking-tight text-ink">{f.title}</span>
          <span className="block text-sm text-ink-2 mt-0.5 leading-snug">{f.lead}</span>
        </span>
        <ChevronDown className={`w-4 h-4 text-mute shrink-0 transition ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="px-6 pb-6 pt-4 space-y-5 border-t border-line">
          <ol className="grid sm:grid-cols-2 xl:grid-cols-4 gap-3">
            {f.steps.map(([t, d], i) => (
              <li key={t} className="rounded-2xl bg-tint p-4 space-y-1.5">
                <span className="w-6 h-6 rounded-full bg-ink text-white text-xs font-semibold flex items-center justify-center">{i + 1}</span>
                <p className="text-sm font-semibold text-ink leading-snug">{t}</p>
                <p className="text-xs text-ink-2 leading-relaxed">{d}</p>
              </li>
            ))}
          </ol>
          <dl className="space-y-3">
            {f.notes.map(([q, a]) => (
              <div key={q}><dt className="text-sm font-medium text-ink">{q}</dt><dd className="text-xs text-ink-2 leading-relaxed mt-0.5 max-w-2xl">{a}</dd></div>
            ))}
          </dl>
        </div>
      )}
    </section>
  )
}
