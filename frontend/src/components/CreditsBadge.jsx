import React, { useEffect, useState } from 'react'
import { api } from '../lib/api'

const R = 9
const C = 2 * Math.PI * R
const tone = (pct) => (pct > 50 ? '#10b981' : pct > 20 ? '#f59e0b' : '#ef4444')

/** Anello di avanzamento dei crediti (ipotesi di piano annuale a consumo). */
export function CreditsRing({ pct, size = 22 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className="shrink-0">
      <circle cx="12" cy="12" r={R} fill="none" stroke="currentColor" strokeOpacity="0.15" strokeWidth="3" />
      <circle cx="12" cy="12" r={R} fill="none" stroke={tone(pct)} strokeWidth="3" strokeLinecap="round"
        strokeDasharray={C} strokeDashoffset={C * (1 - pct / 100)} transform="rotate(-90 12 12)" />
    </svg>
  )
}

/** Pillola sempre visibile accanto al profilo, nell'header: quanto resta del piano (ora gratuito, in anteprima di un abbonamento annuale). */
export default function CreditsBadge({ onClick }) {
  const [credits, setCredits] = useState(null)
  useEffect(() => { api.meCredits().then(setCredits).catch(() => {}) }, [])
  if (!credits) return null
  return (
    <button onClick={onClick} className="btn !px-2.5 !py-1.5 !gap-1.5" title={`${credits.remaining} crediti su ${credits.limit} · si rinnovano tra ${credits.days_until_renewal} giorni`}>
      <CreditsRing pct={credits.pct_remaining} />
      <span className="tabular-nums">{credits.pct_remaining}%</span>
    </button>
  )
}
