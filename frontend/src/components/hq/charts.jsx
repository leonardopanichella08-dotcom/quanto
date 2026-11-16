import React from 'react'

/* Grafici minimi del Quartier Generale: solo CSS e SVG, nessuna libreria. Inchiostro per i dati, giallo del marchio per ciò che chiede attenzione. */
const INK = '#1d1d1f'
const YELLOW = '#F1E21B'
const TRACK = 'rgba(0,0,0,0.06)'

// Un numero grande con la sua etichetta; ``onClick`` lo rende un collegamento.
export function Big({ label, value, note, tone, onClick }) {
  const Tag = onClick ? 'button' : 'div'
  return (
    <Tag onClick={onClick} className={`text-left ${onClick ? 'hover:opacity-70 transition' : ''}`}>
      <span className="label block">{label}</span>
      <span className={`block text-[34px] leading-tight font-semibold tracking-tight font-mono ${tone || 'text-ink'}`}>{value}</span>
      {note && <span className="block text-xs text-mute mt-0.5">{note}</span>}
    </Tag>
  )
}

// Barre orizzontali ordinate: ogni riga è un dato; con ``onSelect`` si può scegliere.
export function BarList({ rows, selected, onSelect, unit = '', empty = 'Ancora nessun dato.', max }) {
  const top = max ?? Math.max(...rows.map((r) => r.value), 1)
  if (!rows.length) return <p className="text-xs text-mute italic">{empty}</p>
  return (
    <ul className="space-y-1.5">
      {rows.map((r) => {
        const pick = onSelect && r.id !== undefined
        const Row = pick ? 'button' : 'div'
        return (
          <li key={r.id ?? r.label}>
            <Row onClick={pick ? () => onSelect(r.id) : undefined} className={`w-full text-left group ${pick ? 'cursor-pointer' : ''}`}>
              <span className="flex items-baseline justify-between gap-3 text-xs">
                <span className={`truncate ${selected === r.id ? 'font-semibold text-ink' : 'text-ink-2'} ${pick ? 'group-hover:text-ink' : ''}`}>{r.label}</span>
                <span className="font-mono text-ink shrink-0">{r.display ?? r.value}{unit}</span>
              </span>
              <span className="block h-1.5 rounded-full mt-1" style={{ background: TRACK }}>
                <span className="block h-full rounded-full transition-all duration-700" style={{ width: `${Math.max(r.value > 0 ? 3 : 0, (r.value / top) * 100)}%`, background: r.alert ? YELLOW : INK, opacity: selected && selected !== r.id ? 0.35 : 1 }} />
              </span>
            </Row>
          </li>
        )
      })}
    </ul>
  )
}

// Colonne per giorno: l'ultimo giorno è giallo.
export function DayBars({ days, height = 84 }) {
  if (!days.length) return <p className="text-xs text-mute italic">Nessun evento.</p>
  const top = Math.max(...days.map((d) => d.n), 1)
  return (
    <div>
      <div className="flex items-end gap-1.5" style={{ height }}>
        {days.map((d, i) => (
          <div key={d.day} title={`${d.day}: ${d.n}`} className="flex-1 min-w-0 max-w-[34px] rounded-t-sm transition-all duration-700" style={{ height: `${Math.max(5, (d.n / top) * 100)}%`, background: i === days.length - 1 ? YELLOW : INK, opacity: i === days.length - 1 ? 1 : 0.8 }} />
        ))}
      </div>
      <div className="flex justify-between text-[10px] text-mute font-mono mt-1"><span>{days[0].day.slice(5)}</span><span>{days[days.length - 1].day.slice(5)}</span></div>
    </div>
  )
}

// Anello a due o più parti con la legenda a fianco.
export function Donut({ parts, size = 92, center }) {
  const total = parts.reduce((a, p) => a + p.value, 0)
  const R = 36
  const C = 2 * Math.PI * R
  let off = 0
  const shades = [INK, YELLOW, '#8e8e93', '#c7c7cc']
  return (
    <div className="flex items-center gap-4">
      <svg width={size} height={size} viewBox="0 0 100 100" role="img" aria-label={parts.map((p) => `${p.label}: ${p.value}`).join(', ')}>
        <circle cx="50" cy="50" r={R} fill="none" stroke={TRACK} strokeWidth="13" />
        {total > 0 && parts.map((p, i) => {
          const len = (p.value / total) * C
          const el = <circle key={p.label} cx="50" cy="50" r={R} fill="none" stroke={shades[i % shades.length]} strokeWidth="13" strokeDasharray={`${len} ${C - len}`} strokeDashoffset={-off} transform="rotate(-90 50 50)" />
          off += len
          return el
        })}
        {center !== undefined && <text x="50" y="55" textAnchor="middle" fontSize="20" fontWeight="600" fill={INK}>{center}</text>}
      </svg>
      <ul className="space-y-1 text-xs">
        {parts.map((p, i) => <li key={p.label} className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ background: shades[i % shades.length] }} /><span className="text-ink-2">{p.label}</span><span className="font-mono text-ink">{p.value}</span></li>)}
      </ul>
    </div>
  )
}

// Titoletto di un grafico.
export function ChartTitle({ children, right }) {
  return <div className="flex items-center justify-between gap-3 mb-3"><h3 className="text-[13px] font-semibold tracking-tight">{children}</h3>{right}</div>
}

// Pastiglie per scegliere una vista dentro una sezione.
export function Pills({ items, value, onChange }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map(([id, label]) => (
        <button key={id} onClick={() => onChange(id)} className={`px-3 py-1.5 rounded-full text-xs font-medium transition ${value === id ? 'bg-brand text-white' : 'bg-black/[0.05] text-ink-2 hover:bg-black/[0.09]'}`}>{label}</button>
      ))}
    </div>
  )
}
