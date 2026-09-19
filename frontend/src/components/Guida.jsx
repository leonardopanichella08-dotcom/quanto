import React, { useEffect, useMemo, useState } from 'react'
import { FUNCTIONS, GLOSSARY, QUICKSTART } from '../data/help'
import { useNav } from '../lib/nav'
import MerkleLab from './MerkleLab'

const SECTIONS = [['percorso', 'Percorso rapido'], ['merkle', 'Merkle Root passo passo'], ['funzioni', 'Ogni funzione, con un esempio'], ['glossario', 'Glossario']]

function Quickstart() {
  const nav = useNav()
  const go = ['bandi', 'canvas', 'canvas', 'lab', 'auditor']
  return (
    <div className="space-y-4">
      <p className="text-sm text-neutral-300 leading-relaxed max-w-2xl">QUANTO controlla il budget di una domanda di finanziamento: prende le regole del bando, verifica ogni spesa e ti dice cosa è finanziabile, cosa va ridotto e perché. Il percorso è sempre lo stesso, in cinque mosse.</p>
      <ol className="grid md:grid-cols-5 gap-3">
        {QUICKSTART.map((s, i) => (
          <li key={s.t}>
            <button type="button" onClick={() => nav.go(go[i])} className="card p-4 h-full w-full text-left space-y-2 hover:border-neutral-600 transition">
              <span className="w-6 h-6 rounded-full bg-[#deffac] text-black text-xs font-bold flex items-center justify-center">{i + 1}</span>
              <p className="text-sm font-semibold">{s.t}</p>
              <p className="text-xs text-neutral-400 leading-relaxed">{s.d}</p>
            </button>
          </li>
        ))}
      </ol>
      <div className="card p-4 space-y-2 max-w-2xl">
        <p className="text-sm font-semibold">Tre cose da tenere a mente</p>
        <ul className="list-disc pl-5 space-y-1.5 text-xs text-neutral-300 leading-relaxed">
          <li><strong className="text-white">I numeri non sono “stimati”.</strong> Il motore fa solo calcoli esatti e ripetibili: stessi dati, stesso risultato.</li>
          <li><strong className="text-white">Se manca un dato, il controllo non parte</strong> e lo vedi come “non valutato”. Non viene mai contato come superato.</li>
          <li><strong className="text-white">Le regole dei bandi vanno verificate sul testo ufficiale</strong> prima di presentare una domanda: ogni regola mostra la sua fonte e quanto è affidabile.</li>
        </ul>
      </div>
    </div>
  )
}

function Functions() {
  return (
    <div className="space-y-3">
      <p className="text-xs text-neutral-400">Per ogni pagina, ogni funzione: cosa fa e un esempio. Gli importi sono inventati per spiegare.</p>
      {FUNCTIONS.map((g, gi) => (
        <details key={g.page} open={gi === 0} className="card group">
          <summary className="cursor-pointer list-none px-4 py-3 flex items-center justify-between">
            <span className="text-sm font-semibold">{g.page}</span>
            <span className="text-xs text-neutral-500">{g.items.length} funzioni</span>
          </summary>
          <div className="px-4 pb-4 grid md:grid-cols-2 gap-x-8 gap-y-4 border-t border-neutral-800 pt-4">
            {g.items.map((it) => (
              <div key={it.name} className="space-y-1">
                <p className="text-sm font-medium text-neutral-100">{it.name}</p>
                <p className="text-xs text-neutral-300 leading-relaxed">{it.what}</p>
                <p className="text-xs text-neutral-400 leading-relaxed border-l-2 border-[#deffac]/40 pl-3"><span className="text-neutral-500">Esempio · </span>{it.example}</p>
              </div>
            ))}
          </div>
        </details>
      ))}
    </div>
  )
}

function Glossary() {
  const [q, setQ] = useState('')
  const list = useMemo(() => {
    const n = q.trim().toLowerCase()
    return Object.entries(GLOSSARY).map(([id, g]) => ({ id, ...g }))
      .filter((g) => !n || `${g.term} ${g.text} ${g.example}`.toLowerCase().includes(n))
      .sort((a, b) => a.term.localeCompare(b.term, 'it'))
  }, [q])
  return (
    <div className="space-y-4">
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cerca una parola (es. TFR, cumulo, impronta…)" aria-label="Cerca nel glossario" className="field max-w-md" />
      <div className="grid md:grid-cols-2 gap-3">
        {list.map((g) => (
          <div key={g.id} className="card p-4 space-y-1">
            <p className="text-sm font-semibold">{g.term}</p>
            <p className="text-xs text-neutral-300 leading-relaxed">{g.text}</p>
            <p className="text-xs text-neutral-400 leading-relaxed"><span className="text-neutral-500">Esempio · </span>{g.example}</p>
          </div>
        ))}
        {list.length === 0 && <p className="text-xs text-neutral-500 italic">Nessuna parola trovata.</p>}
      </div>
    </div>
  )
}

export default function Guida({ anchor }) {
  const [section, setSection] = useState(SECTIONS.some(([id]) => id === anchor) ? anchor : 'percorso')
  useEffect(() => { if (SECTIONS.some(([id]) => id === anchor)) setSection(anchor) }, [anchor])
  return (
    <div className="space-y-6">
      <section className="border-l-2 border-[#deffac]/40 pl-4 space-y-1">
        <h2 className="text-lg font-semibold">Guida</h2>
        <p className="text-sm text-neutral-300 leading-relaxed">Tutto quello che serve per capire QUANTO, con parole semplici ed esempi. Nelle altre pagine trovi anche le icone <span className="inline-flex w-4 h-4 rounded-full border border-neutral-600 text-[10px] items-center justify-center align-middle">?</span> e le parole sottolineate a puntini: cliccale per una spiegazione al volo.</p>
      </section>
      <div className="flex flex-wrap gap-x-6 gap-y-2 border-b border-neutral-800">
        {SECTIONS.map(([id, label]) => (
          <button key={id} type="button" onClick={() => setSection(id)}
            className={`pb-2.5 text-sm -mb-px border-b-2 transition ${section === id ? 'border-[#deffac] text-white' : 'border-transparent text-neutral-400 hover:text-white'}`}>{label}</button>
        ))}
      </div>
      {section === 'percorso' && <Quickstart />}
      {section === 'merkle' && <MerkleLab />}
      {section === 'funzioni' && <Functions />}
      {section === 'glossario' && <Glossary />}
    </div>
  )
}
