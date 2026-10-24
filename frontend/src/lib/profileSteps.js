// Dati che nessun documento può dire: li chiede una domanda. Tutti gli altri dati mancanti si ricavano dai documenti giusti.
const ASKED = new Set(['is_innovative_startup', 'company_type'])

/** Il prossimo passo da fare per questo lavoro: uno solo, con il pulsante che porta esattamente lì. ``docs`` = elenco dei documenti (senza doc_type = tipo sconosciuto). */
export function nextStep(ov, docs) {
  if (!ov) return null
  const has = (t) => docs.some((d) => !d.doc_type || d.doc_type === t)
  if (!docs.length) return { text: 'Carica i documenti dell’azienda: bastano visura e ultimo bilancio per partire.', btn: 'Carica i documenti', t: { to: 'setup', step: 'all' } }
  const mp = ov.missing.filter((m) => m.scope === 'profile')
  const fromDocs = mp.filter((m) => !ASKED.has(m.key))
  if (fromDocs.length && !has('COMPANY_REGISTRY')) return { text: `Mancano i dati dell’impresa (${fromDocs.map((m) => m.label).slice(0, 3).join(', ')}): li ricavo dalla visura camerale.`, btn: 'Carica la visura', t: { to: 'setup', step: 'registry' } }
  if (fromDocs.length) return { text: `Nella visura non c’è: ${fromDocs.map((m) => m.label).slice(0, 3).join(', ')}. Scrivilo tu.`, btn: 'Scrivilo ora', t: { to: 'azienda', field: fromDocs[0].key } }
  const mf = ov.missing.filter((m) => m.scope === 'financial')
  if (mf.length && !has('BALANCE_SHEET')) return { text: 'Manca il bilancio: da lì ricavo ricavi, utile, dipendenti e i costi per categoria, base della stima dell’anno dopo.', btn: 'Carica il bilancio', t: { to: 'setup', step: 'balance' } }
  if (mf.length) return { text: `Nel bilancio manca: ${mf[0].label}${mf[0].year ? ` (esercizio ${mf[0].year})` : ''}${mf.length > 1 ? ` e altre ${mf.length - 1} voci` : ''}.`, btn: 'Completa i dati', t: mf[0].year ? { to: 'azienda', fin: { year: mf[0].year, key: mf[0].key } } : { to: 'setup', step: 'balance' } }
  if (mp.length) return { text: `Rispondi a ${mp.length === 1 ? 'una domanda' : `${mp.length} domande`} che nessun documento può dire: ${mp.map((m) => m.label).slice(0, 2).join(' · ')}.`, btn: 'Rispondi ora', t: { to: 'quick' } }
  if (ov.documents.to_review > 0) return { text: `${ov.documents.to_review} ${ov.documents.to_review === 1 ? 'lettura è' : 'letture sono'} poco sicure e non entrano nei calcoli finché non le verifichi.`, btn: 'Verifica ora', t: { to: 'documenti', doc: 'review' } }
  return { done: true, text: 'Il profilo è completo e le letture sono tutte verificate.', btn: 'Stima l’anno e cerca i bandi', t: null }
}
