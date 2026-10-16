// Controllo grafico da incollare nella console del browser (o da lanciare con javascript_tool): apre tutte le sezioni di ogni pagina e cerca testi schiacciati
// in colonne più strette di 90 px (il difetto «titolo spezzato lettera per lettera») e scorrimenti orizzontali. Va rifatto a 1440, 1024, 768 e 375 px di larghezza.
(async () => {
  const bad = []
  const scan = (page) => {
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT)
    let n
    while ((n = w.nextNode())) {
      const t = n.textContent.trim(); const p = n.parentElement
      if (t.length < 14 || !p || !p.offsetParent) continue
      const r = p.getBoundingClientRect(); const lh = parseFloat(getComputedStyle(p).lineHeight) || 16
      if (r.width > 0 && r.width < 90 && r.height > lh * 4) bad.push(`${page}: ${Math.round(r.width)}x${Math.round(r.height)} ${t.slice(0, 40)}`)
    }
    if (document.documentElement.scrollWidth > innerWidth) bad.push(`${page}: scorrimento orizzontale`)
  }
  for (const label of ['Guida', 'Bandi', 'Budget', 'Confronto', 'Profilo', 'Allocazione', 'Verifica']) {
    const b = [...document.querySelectorAll('aside button')].find((x) => x.textContent.trim().startsWith(label))
    if (!b) continue
    b.click(); await new Promise((r) => setTimeout(r, 1800))
    document.querySelectorAll('main button[aria-expanded=false]').forEach((x) => x.click()); await new Promise((r) => setTimeout(r, 900))
    scan(label)
  }
  console.log(bad.length ? bad.join('\n') : 'Nessun difetto di layout trovato')
})()
