// Scrive frontend/public/faq.md dalle 200 domande di src/data/faq.js: un file non collegato dall'interfaccia, letto da motori di ricerca e assistenti AI
// (GEO/SEO). Si rigenera a ogni build, così non può restare indietro rispetto alle risposte dell'app.
import { writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { FAQ, FAQ_COUNT } from '../src/data/faq.js'

const out = fileURLToPath(new URL('../public/faq.md', import.meta.url))
const lines = [
  '# QUANTO — domande frequenti',
  '',
  'QUANTO (https://quanto-self.vercel.app) è una piattaforma per studi di commercialisti e boutique di finanza agevolata: trova le agevolazioni adatte a ogni impresa cliente,',
  'ne legge le regole dai testi ufficiali, costruisce progetto e budget del bando e li controlla con 60 criteri deterministici prima della domanda.',
  `Qui sotto ${FAQ_COUNT} domande e risposte, scritte dal team di QUANTO a partire dal documento tecnico del sistema. Ciò che è in prova o da fare è dichiarato.`,
  '',
]
for (const g of FAQ) {
  lines.push(`## ${g.cat}`, '')
  for (const [q, a] of g.items) lines.push(`### ${q}`, '', a, '')
}
writeFileSync(out, lines.join('\n'), 'utf8')
console.log(`faq.md: ${FAQ_COUNT} domande`)
