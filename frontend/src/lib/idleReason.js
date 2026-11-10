import { fmtEur } from './format'

/** Perché un bando incluso nel piano «non serve» (il programma non gli assegna nessuna spesa) e quando servirebbe.
 *  r: il bando non usato; rows: i bandi del piano; used: { fund_id: euro usati nel piano }. Solo dati del piano, niente supposizioni. */
export function idleReason(r, rows, used) {
  const usedOf = (x) => used[x.fund?.fund_id] ?? 0
  const others = rows.filter((x) => x.bando_id !== r.bando_id && usedOf(x) > 0)
  const cats = r.fund?.allowed_categories || []
  const shares = (x) => cats.some((c) => (x.fund?.allowed_categories || []).includes(c))
  const isGrant = r.estimate?.kind === 'FONDO_PERDUTO'
  const excl = (x) => (r.fund?.excludes || []).includes(x.fund?.fund_id) || (x.fund?.excludes || []).includes(r.fund?.fund_id)
  const grantRival = others.filter((x) => isGrant && x.estimate?.kind === 'FONDO_PERDUTO' && shares(x)).sort((a, b) => usedOf(b) - usedOf(a))[0]
  const exclRival = others.filter(excl).sort((a, b) => usedOf(b) - usedOf(a))[0]
  const sameCats = others.filter(shares).sort((a, b) => usedOf(b) - usedOf(a))[0]
  const alone = r.estimate?.covered_eur
  const best = grantRival || exclRival || sameCats
  if (!best) return { why: 'Le spese che ammette non ci sono tra quelle del piano, o sono già al tetto: insieme agli altri bandi non aggiunge nulla.', when: null, rival: null }
  const why = grantRival
    ? `Paga le stesse spese di «${best.name}», che ne copre di più (${fmtEur(usedOf(best))}${alone ? ` contro ${fmtEur(alone)}` : ''}). Due contributi a fondo perduto non si pagano sulla stessa spesa: il programma tiene il più conveniente.`
    : exclRival
      ? `Non è cumulabile con «${best.name}», che copre di più (${fmtEur(usedOf(best))}): insieme si usa solo quello.`
      : `Le spese che ammette sono già coperte da «${best.name}» fino al massimo consentito: la stessa spesa non si paga due volte.`
  const when = `Servirebbe se «${best.name}» non entra nel piano (per esempio se non viene concesso o lo togli)${alone ? `: da solo coprirebbe ${fmtEur(alone)}` : ''}.`
  return { why, when, rival: best }
}
