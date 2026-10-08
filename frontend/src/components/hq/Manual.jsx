import React, { useEffect, useMemo, useState } from 'react'
import { Download, Loader2 } from 'lucide-react'
import { api } from '../../lib/api'

// Inline: **grassetto**, *corsivo*, `codice`
function inline(text) {
  const out = []
  const re = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*\n]+\*)/g
  let last = 0
  let m
  let k = 0
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(text.slice(last, m.index))
    const t = m[0]
    if (t.startsWith('**')) out.push(<strong key={k++} className="text-ink">{t.slice(2, -2)}</strong>)
    else if (t.startsWith('`')) out.push(<code key={k++} className="px-1 rounded bg-tint-2 text-[11px]">{t.slice(1, -1)}</code>)
    else out.push(<em key={k++}>{t.slice(1, -1)}</em>)
    last = m.index + t.length
  }
  if (last < text.length) out.push(text.slice(last))
  return out
}

/** Il manuale in Markdown, mostrato a schermo: titoli, paragrafi, elenchi e tabelle. È lo stesso testo da cui si costruisce il PDF. */
function Render({ markdown }) {
  const blocks = useMemo(() => {
    const lines = markdown.split('\n')
    const out = []
    let i = 0
    while (i < lines.length) {
      const s = lines[i].trim()
      if (!s) { i += 1; continue }
      if (s.startsWith('# ')) { out.push({ t: 'h0', text: s.slice(2) }); i += 1; continue }
      if (s.startsWith('## ')) { out.push({ t: 'h1', text: s.slice(3) }); i += 1; continue }
      if (s.startsWith('### ')) { out.push({ t: 'h2', text: s.slice(4) }); i += 1; continue }
      if (s.startsWith('|')) {
        const rows = []
        while (i < lines.length && lines[i].trim().startsWith('|')) {
          const cells = lines[i].trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim())
          if (!cells.every((c) => /^:?-{2,}:?$/.test(c))) rows.push(cells)
          i += 1
        }
        out.push({ t: 'table', rows }); continue
      }
      if (/^(-|\d+\.)\s+/.test(s)) {
        const ordered = /^\d+\./.test(s)
        const items = []
        while (i < lines.length && /^\s*(-|\d+\.)\s+/.test(lines[i])) { items.push(lines[i].replace(/^\s*(-|\d+\.)\s+/, '')); i += 1 }
        out.push({ t: 'list', ordered, items }); continue
      }
      const para = []
      while (i < lines.length && lines[i].trim() && !/^(#|\||-\s|\d+\.\s)/.test(lines[i].trim())) { para.push(lines[i].trim()); i += 1 }
      out.push({ t: 'p', text: para.join(' ') })
    }
    return out
  }, [markdown])
  return (
    <div className="space-y-3 max-w-4xl">
      {blocks.map((b, n) => {
        if (b.t === 'h0') return <h1 key={n} className="text-2xl font-display font-bold tracking-tight">{b.text}</h1>
        if (b.t === 'h1') return <h2 key={n} className="text-lg font-display font-bold pt-5 border-b border-line pb-1">{b.text}</h2>
        if (b.t === 'h2') return <h3 key={n} className="text-sm font-semibold pt-2">{b.text}</h3>
        if (b.t === 'p') return <p key={n} className="text-xs text-ink-2 leading-relaxed">{inline(b.text)}</p>
        if (b.t === 'list') {
          const L = b.ordered ? 'ol' : 'ul'
          return <L key={n} className={`text-xs text-ink-2 leading-relaxed space-y-1 pl-5 ${b.ordered ? 'list-decimal' : 'list-disc'}`}>{b.items.map((it, j) => <li key={j}>{inline(it)}</li>)}</L>
        }
        return (
          <div key={n} className="overflow-x-auto"><table className="w-full text-[11px] border border-line">
            <thead><tr className="bg-brand/30 text-left">{b.rows[0].map((c, j) => <th key={j} className="p-2 font-semibold">{inline(c)}</th>)}</tr></thead>
            <tbody>{b.rows.slice(1).map((r, j) => <tr key={j} className="border-t border-line align-top">{r.map((c, k) => <td key={k} className="p-2 text-ink-2">{inline(c)}</td>)}</tr>)}</tbody>
          </table></div>
        )
      })}
    </div>
  )
}

export default function Manual() {
  const [doc, setDoc] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  useEffect(() => { api.hqManual().then(setDoc).catch((e) => setError(e.message)) }, [])
  const download = async () => {
    setBusy(true)
    try {
      const blob = await api.hqManualPdf()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = 'QUANTO_manuale_dei_processi.pdf'; a.click()
      setTimeout(() => URL.revokeObjectURL(url), 2000)
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }
  if (error) return <p className="text-xs text-red-700">{error}</p>
  if (!doc) return <p className="text-xs text-mute flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" />Carico il manuale…</p>
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <span className="text-xs text-ink-2">Versione {doc.version} · {doc.sections.length} capitoli · {doc.characters.toLocaleString('it-IT')} caratteri. Lo stesso testo si scarica in PDF.</span>
        <button className="btn-primary ml-auto" onClick={download} disabled={busy}>{busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}Scarica il PDF</button>
      </div>
      <div className="flex flex-wrap gap-1.5">{doc.sections.map((s) => <span key={s} className="px-2 py-0.5 rounded border border-line text-[11px] text-ink-2">{s}</span>)}</div>
      <div className="card p-6"><Render markdown={doc.markdown} /></div>
    </div>
  )
}
