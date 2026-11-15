import { FAQ } from '../data/faq.js'

/* «Chiedi a QUANTO»: trova tra le 200 risposte scritte quella più vicina alla domanda. Nessun modello linguistico: si confrontano le parole
   (senza accenti, senza parole vuote, con le radici di 5 lettere e pochi sinonimi), la domanda pesa più della risposta, e a parità vince la domanda
   più vicina per lunghezza a quella fatta. Se nulla somiglia abbastanza, lo dice. */
const STOP = new Set(('a ad al allo ai agli alla alle anche che chi ci come con cosa cosi da dal dallo dai dagli dalla dalle del dello dei degli della delle di e ed gli ha hanno ho i il in io la le lo ma mi mia mio ne nel nello nei negli nella nelle no non o per piu puo qual quale quali quando quanto quanta quella quello questa questo se si sia sono su sul sullo sui sugli sulla sulle te ti tra tu un una uno vi voi ' +
  'posso devo serve fare fa fanno essere stato viene sapere dire cos mio miei mie suo sua loro vostro vostra').split(' '))
const fold = (s) => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[’']/g, ' ')
const stem = (w) => (w.length > 5 ? w.slice(0, 5) : w)
// radici equivalenti: chi chiede «prezzo» deve trovare «costa», chi chiede «sicuri» deve trovare «cifrati»
const SYN = [['costa', 'costo', 'prezz', 'pagar', 'tarif', 'abbon'], ['sicur', 'cifra', 'prote', 'priva', 'gdpr'], ['bando', 'bandi', 'agevo', 'incen', 'misur'],
  ['impre', 'azien', 'clien', 'socie'], ['docum', 'file', 'caric'], ['dipen', 'perso', 'assun', 'lavor'], ['bilan', 'dichi'], ['grati', 'free', 'prova']]
const SYN_OF = new Map(SYN.flatMap((g) => g.map((w) => [w, g])))
const terms = (s) => fold(s).split(/[^a-z0-9]+/).filter((w) => w.length > 1 && !STOP.has(w)).map(stem)

const INDEX = FAQ.flatMap((g) => g.items.map((it) => { const q = terms(it[0]); return { it, q: new Set(q), qn: q.length || 1, a: new Set(terms(it[1])), c: new Set(terms(g.cat)) } }))

export function answer(question) {
  const t = [...new Set(terms(question))]
  if (!t.length) return { best: null, related: [] }
  const hit = (set, w) => (set.has(w) ? 1 : (SYN_OF.get(w) || []).some((s) => s !== w && set.has(s)) ? 0.7 : 0)
  const scored = INDEX.map((x) => {
    const inQ = t.reduce((n, w) => n + hit(x.q, w), 0)
    const s = (inQ * 3 + t.reduce((n, w) => n + hit(x.a, w) + hit(x.c, w) * 0.5, 0)) / Math.sqrt(t.length) + (2 * inQ) / x.qn
    return { x, s }
  }).filter((r) => r.s > 0).sort((a, b) => b.s - a.s)
  if (!scored.length || scored[0].s < 1.2) return { best: null, related: scored.slice(0, 2).map((r) => r.x.it) }
  return { best: scored[0].x.it, related: scored.slice(1, 3).filter((r) => r.s >= scored[0].s * 0.6).map((r) => r.x.it) }
}
