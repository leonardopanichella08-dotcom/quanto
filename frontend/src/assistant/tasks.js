import { api } from '../lib/api'
import { fmtEur } from '../lib/format'

/** Le attività dell'assistente. Ogni passaggio è dichiarato in anticipo (così si vedono tutti a destra) e il programma li esegue uno alla volta:
 *  azioni sull'app (cambio pagina, salvataggi, calcoli) fatte dall'assistente, domande all'utente solo quando serve un dato che non c'è. */

const THIS_YEAR = new Date().getFullYear()
const evt = (name, detail) => window.dispatchEvent(new CustomEvent(name, { detail }))
const money = (n) => fmtEur(n)

// ---------------------------------------------------------------------------------------------- spiegazioni dei dati dell'azienda
const PROFILE_HELP = {
  legal_name: { what: 'Il nome ufficiale dell’azienda, com’è scritto in visura.', why: 'Serve a riconoscere l’azienda nei documenti e nelle domande.', where: 'Visura camerale, riga «Denominazione».', example: 'ALFA INNOVAZIONI S.R.L.', kind: 'text' },
  vat_number: { what: 'La partita IVA: 11 cifre.', why: 'Identifica l’impresa; molti bandi la chiedono nella domanda.', where: 'Visura camerale, oppure una fattura emessa dall’azienda.', example: '01234567890', kind: 'text' },
  legal_form: { what: 'Il tipo di società.', why: 'Cambia le imposte (l’aliquota IRES del 24% vale per le società di capitali), quindi il valore dei bonus fiscali; alcuni bandi sono per certe forme soltanto.', where: 'Visura camerale, riga «Forma giuridica».', example: 'Società a responsabilità limitata', kind: 'text' },
  ateco_code: { what: 'Il codice che classifica l’attività dell’azienda.', why: 'Molti bandi ammettono solo certi settori: con il codice controllo subito se l’azienda può partecipare.', where: 'Visura camerale (campo «Codice ATECO») o certificato di attribuzione della partita IVA.', example: '62.01.00', kind: 'text' },
  region: { what: 'La regione dove ha sede l’azienda.', why: 'Molti bandi sono regionali: valgono solo per le imprese con sede in quella regione.', where: 'Visura camerale, riga «Sede legale».', example: 'Piemonte', kind: 'select' },
  employees: { what: 'Quante persone lavorano in azienda (in media nell’anno).', why: 'Insieme al fatturato decide se l’azienda è micro, piccola, media o grande: ogni bando dà percentuali diverse.', where: 'Bilancio, nota integrativa («numero medio dei dipendenti»), oppure il libro unico del lavoro.', example: '14', kind: 'number' },
  is_innovative_startup: { what: 'Se l’azienda è iscritta al registro delle start-up innovative.', why: 'Alcuni bandi sono riservati alle start-up innovative; per gli altri non cambia nulla.', where: 'Visura camerale: compare la sezione speciale «Start-up innovativa».', example: 'No', kind: 'yesno' },
}

const COST_HELP = {
  revenue_eur: { label: 'Ricavi dell’anno', what: 'Quanto ha fatturato l’azienda nell’esercizio: ricavi delle vendite e delle prestazioni.', why: 'Serve a stimare la dimensione dell’azienda e come crescono i costi rispetto al fatturato.', where: 'Conto economico del bilancio, voce A.1 «Ricavi delle vendite e delle prestazioni».', example: '900000' },
  personnel_eur: { label: 'Costo del personale', what: 'Stipendi, contributi e TFR di tutti i dipendenti nell’anno.', why: 'È la voce di spesa più grande per molti bandi (ricerca, innovazione): decide quanto contributo si può chiedere.', where: 'Conto economico, voce B.9 «Per il personale» (somma delle sue righe).', example: '195000' },
  capital_assets_eur: { label: 'Beni strumentali (macchinari, computer, software)', what: 'Quanto l’azienda spende in un anno per beni che durano più anni.', why: 'I bandi per l’innovazione e gli sgravi fiscali (Transizione 5.0) si calcolano su questa voce.', where: 'Bilancio: acquisti dell’anno nelle immobilizzazioni (stato patrimoniale, nota integrativa) oppure gli ammortamenti, se non hai altro.', example: '60000' },
  consulting_eur: { label: 'Consulenze', what: 'Compensi a professionisti e consulenti esterni nell’anno.', why: 'Molti bandi rimborsano le consulenze, ma con un tetto: devo sapere quanto spendi per rispettarlo.', where: 'Conto economico, voce B.7 «Per servizi»: la riga delle consulenze professionali.', example: '40000' },
  overhead_eur: { label: 'Spese generali', what: 'Affitto, utenze, telefono, cancelleria: le spese che servono a far funzionare l’azienda.', why: 'Alcuni bandi le coprono con una percentuale fissa sulle altre spese.', where: 'Conto economico, voce B.7 «Per servizi» e B.8 «Per godimento di beni di terzi».', example: '25000' },
  training_eur: { label: 'Formazione', what: 'Corsi e formazione del personale.', why: 'Alcuni bandi (e il Fondo nuove competenze) coprono la formazione.', where: 'Conto economico, riga dei corsi di formazione dentro B.7 (o dal tuo gestionale).', example: '6000' },
}
const COST_KEYS = ['revenue_eur', 'personnel_eur', 'capital_assets_eur', 'consulting_eur', 'overhead_eur', 'training_eur']

/** Controlla il profilo dell'azienda; se mancano dati li chiede (uno per uno spiegati) e li salva. Restituisce il profilo aggiornato. */
async function ensureProfile(a, stepId) {
  a.begin(stepId, 'Leggo il profilo del lavoro…')
  await a.pause(500)
  let ov = await api.profile()
  const missingProfile = ov.missing.filter((m) => m.scope === 'profile')
  const needsBalance = ov.last_year == null
  if (!missingProfile.length && !needsBalance) {
    a.done(stepId, `Profilo completo: bilancio ${ov.last_year}, nessun dato mancante.`)
    return ov
  }
  if (missingProfile.length) {
    const fields = missingProfile.map((m) => {
      const h = PROFILE_HELP[m.key] || {}
      const f = { key: m.key, label: m.label, kind: h.kind || 'text', what: h.what, why: h.why, where: h.where, example: h.example }
      if (f.kind === 'select') f.options = (ov.regions || []).map((r) => ({ value: r, label: r }))
      if (m.key === 'employees') f.min = 0
      return f
    })
    const vals = await a.ask(stepId, { title: 'Mi servono alcuni dati dell’azienda', intro: 'Sono dati che di solito trovi nella visura camerale. Se non ce l’hai ora puoi saltare: i bandi che dipendono da questi dati resteranno «da verificare».', fields, submitLabel: 'Salva questi dati', skipLabel: 'Salta per ora' })
    if (vals) {
      const clean = Object.fromEntries(Object.entries(vals).map(([k, v]) => [k, typeof v === 'boolean' ? v : v]))
      ov = await api.saveProfile(clean)
      evt('quanto-profile-changed')
    }
  }
  if (ov.last_year == null) {
    const years = [THIS_YEAR - 1, THIS_YEAR - 2, THIS_YEAR - 3].map((y) => ({ value: String(y), label: String(y) }))
    const fields = [
      { key: 'year', label: 'Anno del bilancio', kind: 'select', options: years, default: String(THIS_YEAR - 1), what: 'L’esercizio a cui si riferiscono i numeri che scrivi sotto.', why: 'La stima dell’anno prossimo parte dall’ultimo anno chiuso.', where: 'Intestazione del bilancio.', example: String(THIS_YEAR - 1) },
      ...COST_KEYS.map((k) => ({ key: k, kind: 'money', optional: true, zeroLabel: 'Zero', min: 0, ...COST_HELP[k] })),
    ]
    for (;;) {
      const vals = await a.ask(stepId, {
        title: 'Mancano i dati di bilancio', intro: 'Non c’è ancora nessun bilancio. Scrivi i totali dell’ultimo anno chiuso (puoi caricare il PDF del bilancio nel Profilo, ma così sei più veloce). Lascia vuoto ciò che non sai: non lo invento.',
        fields, submitLabel: 'Salva il bilancio', skipLabel: 'Lo faccio dopo',
        validate: (v) => (COST_KEYS.slice(1).every((k) => v[k] == null) ? 'Scrivi almeno una voce di costo (anche zero se l’azienda non la sostiene).' : null),
      })
      if (!vals) { a.skip(stepId, 'Bilancio non inserito: senza non posso stimare l’anno prossimo.'); return null }
      const { year, ...numbers } = vals
      ov = await api.saveFinancials(Number(year), numbers)
      evt('quanto-profile-changed')
      break
    }
  }
  a.done(stepId, `Dati salvati nel profilo (bilancio ${ov.last_year}).`)
  return ov
}

/** Chiede gli aiuti pubblici ricevuti negli ultimi tre anni e li salva nel profilo (servono al tetto de minimis). */
async function askAid(a, stepId, saveId, year) {
  const years = [year - 3, year - 2, year - 1]
  const ov = await api.profile()
  const known = Object.fromEntries((ov.financials || []).map((f) => [f.fiscal_year, f.values?.public_aid_eur]))
  const fields = years.map((y) => ({
    key: `y${y}`, label: `Contributi pubblici ricevuti nel ${y}`, kind: 'money', optional: true, zeroLabel: 'Nessuno', min: 0, default: known[y] ?? '',
    what: y === years[0] ? 'La somma dei contributi, sovvenzioni o aiuti pubblici che l’azienda ha ricevuto in quell’anno, di qualunque ente (Stato, Regione, Camera di commercio, UE).' : undefined,
    why: y === years[0] ? 'Ogni azienda può ricevere al massimo 300.000 € di aiuti «de minimis» in tre anni. Quello che ha già ricevuto si toglie dal tetto, e il piano rispetta quello che resta.' : undefined,
    where: y === years[0] ? 'Visura aiuti sul Registro Nazionale degli Aiuti (RNA), oppure i provvedimenti di concessione e le dichiarazioni de minimis firmate per le domande precedenti. Se l’azienda fa parte di un gruppo, sommare quelle delle società collegate.' : undefined,
    example: y === years[0] ? '40000 se ha ricevuto un voucher da 40.000 €; «Nessuno» se non ha ricevuto nulla' : undefined,
  }))
  const vals = await a.ask(stepId, {
    title: 'Aiuti pubblici già ricevuti', intro: 'Per rispettare il tetto de minimis devo sapere cosa ha già ricevuto l’azienda negli ultimi tre anni. Se non lo sai, lascia vuoto: userò la stima prudente e ti dirò su cosa si regge.',
    fields, submitLabel: 'Salva e ricalcola', skipLabel: 'Non lo so, uso la stima',
  })
  if (!vals) return null
  a.begin(saveId, 'Scrivo i dati nel profilo…')
  let n = 0
  for (const y of years) {
    const v = vals[`y${y}`]
    if (v === undefined) continue
    await api.saveFinancials(y, { public_aid_eur: v }); n += 1
  }
  evt('quanto-profile-changed')
  a.done(saveId, n ? `${n} ${n === 1 ? 'anno salvato' : 'anni salvati'} nel profilo.` : 'Nessun dato nuovo da salvare.')
  return vals
}

const eurShort = (n) => money(n)

// ---------------------------------------------------------------------------------------------- attività
export const TASKS = {
  deminimis: {
    title: 'Dichiarare gli aiuti già ricevuti',
    blurb: 'Il de minimis è il tetto di 300.000 € in tre anni agli aiuti «piccoli». Ti chiedo cosa ha già ricevuto l’azienda e ricalcolo il piano.',
    steps: [
      { id: 'profilo', title: 'Apro il profilo dell’azienda' },
      { id: 'domande', title: 'Ti chiedo gli aiuti ricevuti' },
      { id: 'salvo', title: 'Salvo i dati nel profilo' },
      { id: 'ricalcolo', title: 'Ricalcolo l’Allocazione' },
    ],
    async run(a, p) {
      const b = a.bridge()
      const year = Number(p.year) || THIS_YEAR + 1
      a.begin('profilo'); b.go('profilo'); await a.pause(800); a.done('profilo', 'Sezione dei bilanci aperta.')
      a.begin('domande', 'Preparo le domande…')
      const vals = await askAid(a, 'domande', 'salvo', year)
      if (!vals) { a.skip('domande', 'Usiamo la stima prudente.'); a.skip('salvo'); a.skip('ricalcolo', 'Il piano resta com’è.'); a.finish('Nessun dato salvato: il piano continua a usare la stima prudente.'); return }
      a.done('domande', 'Ho le risposte.')
      a.begin('ricalcolo'); b.go('allocation'); await a.pause(600)
      evt('quanto-recalc', { year })
      const res = await a.waitFor('quanto-allocation-result', 90000)
      a.done('ricalcolo', res ? `Piano aggiornato: ${money(res.covered)} coperti.` : 'Ho avviato il ricalcolo: il risultato compare nella pagina.')
      a.finish(res?.deMinimis ? `Il tetto de minimis residuo è ora ${money(res.deMinimis.residual_eur)} (${res.deMinimis.basis === 'DICHIARATI' ? 'dato dichiarato' : res.deMinimis.basis === 'PARZIALE' ? 'dato parziale' : 'ipotesi'}); il piano ne usa ${money(res.deMinimis.needed_eur ?? 0)}.` : 'Aiuti salvati e piano aggiornato.')
    },
  },

  allocazione: {
    title: 'Calcolare il potenziale massimo dei bandi',
    blurb: 'Controllo i dati dell’azienda (ti chiedo solo quelli che mancano), stimo l’anno prossimo, cerco i bandi adatti e li combino nel piano migliore.',
    steps: [
      { id: 'dati', title: 'Controllo i dati dell’azienda' },
      { id: 'vai', title: 'Apro l’Allocazione' },
      { id: 'stima', title: 'Stimo l’anno e cerco i bandi adatti' },
      { id: 'aiuti', title: 'Verifico il tetto de minimis' },
      { id: 'esito', title: 'Ti mostro il risultato' },
    ],
    async run(a, p) {
      const b = a.bridge()
      const year = Number(p.year) || THIS_YEAR + 1
      b.go('profilo'); await a.pause(300)
      const ov = await ensureProfile(a, 'dati')
      if (!ov || ov.last_year == null) { for (const s of ['vai', 'stima', 'aiuti', 'esito']) a.skip(s); a.finish('Mi manca il bilancio: appena lo inserisci (anche a mano) riparto da qui.'); return }
      a.begin('vai'); b.go('allocation'); await a.pause(700); a.done('vai', 'Pagina Allocazione aperta.')
      a.begin('stima', 'Calcolo… può volerci qualche secondo.')
      evt('quanto-recalc', { year, allMode: true })
      let res = await a.waitFor('quanto-allocation-result', 120000)
      a.done('stima', res ? `${res.adatti} bandi adatti, ${res.picked} inclusi nel piano.` : 'Calcolo avviato: il risultato compare nella pagina.')
      if (res?.deMinimis && res.usesDeMinimis) {
        a.begin('aiuti')
        if (res.deMinimis.basis === 'DICHIARATI') a.done('aiuti', `Aiuti ricevuti già dichiarati: residuo ${money(res.deMinimis.residual_eur)}.`)
        else {
          const vals = await askAid(a, 'aiuti', 'aiuti', year)
          if (vals) {
            evt('quanto-recalc', { year, allMode: true }); a.begin('stima', 'Ricalcolo con i dati dichiarati…')
            res = (await a.waitFor('quanto-allocation-result', 90000)) || res
            a.done('stima', 'Piano ricalcolato.'); a.done('aiuti', 'Aiuti dichiarati e piano aggiornato.')
          } else a.skip('aiuti', 'Uso la stima prudente (300.000 € nell’ipotesi di nessun aiuto ricevuto).')
        }
      } else a.skip('aiuti', 'Nessuno dei bandi nel piano è in de minimis: non serve.')
      a.begin('esito'); await a.pause(500)
      if (res) {
        a.done('esito', `Coperto ${money(res.covered)} su ${money(res.expense)} (${res.coveragePct.toLocaleString('it-IT', { maximumFractionDigits: 1 })}%).`)
        a.finish(`Con ${res.picked} bandi insieme il piano copre ${money(res.covered)}${res.coveredHigh > res.covered + 0.5 ? ` (fino a ${money(res.coveredHigh)} con tutte le maggiorazioni)` : ''} su una spesa di ${money(res.expense)}. Restano a carico dell’azienda ${money(res.net)}.${res.deMinimis && res.usesDeMinimis ? (res.deMinimis.needed_eur > 0 ? `\nDe minimis: il piano ne usa ${money(res.deMinimis.needed_eur)} su ${money(res.deMinimis.residual_eur)} disponibili.` : '\nDe minimis: nessun aiuto in de minimis serve a questo piano, il tetto non viene toccato.') : ''}\nTutti i numeri sono spiegati nella pagina, sotto il grafico.`)
      } else { a.done('esito', 'Guarda i risultati nella pagina.'); a.finish('Il calcolo è in corso o non ha prodotto un piano: guarda la pagina Allocazione.') }
    },
  },

  budget: {
    title: 'Preparare la bozza di budget',
    blurb: 'Scelgo il bando, creo la bozza dalle spese del bilancio, ti chiedo i dati delle persone del progetto e controllo il budget.',
    steps: [
      { id: 'dati', title: 'Controllo i dati dell’azienda' },
      { id: 'bando', title: 'Scelgo il bando' },
      { id: 'quota', title: 'Decido quanta spesa va nel progetto' },
      { id: 'bozza', title: 'Creo la bozza dal bilancio' },
      { id: 'personale', title: 'Aggiungo le persone del progetto' },
      { id: 'controllo', title: 'Controllo il budget con i 60 criteri' },
    ],
    async run(a, p) {
      const b = a.bridge()
      const ov = await ensureProfile(a, 'dati')
      if (!ov || ov.last_year == null) { for (const s of ['bando', 'quota', 'bozza', 'personale', 'controllo']) a.skip(s); a.finish('Senza i costi del bilancio non posso creare la bozza: appena li inserisci riparto da qui.'); return }

      // 1. il bando
      a.begin('bando')
      const list = (b.bandi() || []).filter((x) => x.rules_count > 0)
      let bandoId = p.bandoId || null
      let detail = null
      while (!detail) {
        if (!bandoId) {
          const vals = await a.ask('bando', {
            title: 'Per quale bando è il budget?', intro: 'Il budget si controlla con le regole di un bando preciso. Vedi solo i bandi di cui ho già letto le regole.',
            fields: [{ key: 'bando', label: 'Bando', kind: 'select', default: b.currentBando() || '', options: list.map((x) => ({ value: x.bando_id, label: x.name })),
              what: 'Il bando a cui vuoi partecipare.', why: 'Ogni bando ha tetti e voci ammesse diversi: la bozza e i controlli seguono le sue regole.', where: 'Se non lo vedi, cercalo nella pagina Bandi e fallo studiare.' }],
            submitLabel: 'Scelgo questo bando', skipLabel: 'Annulla',
          })
          if (!vals) { for (const s of ['bando', 'quota', 'bozza', 'personale', 'controllo']) a.skip(s); a.finish('Annullato: nessuna modifica al budget.'); return }
          bandoId = vals.bando
        }
        a.begin('bando', 'Carico le regole del bando…')
        try { detail = await b.selectBando(bandoId) } catch (e) { a.fail('bando', e.message); bandoId = null; await a.pause(900) }
      }
      a.done('bando', detail.name)
      b.go('canvas'); await a.pause(500)

      // 2. la quota di progetto
      let scale = Number(p.scale) || null
      if (!scale) {
        const vals = await a.ask('quota', {
          title: 'Quanta della spesa annua va nel progetto?', intro: 'La bozza prende le spese dell’ultimo bilancio e le moltiplica per la quota che indichi.',
          fields: [{ key: 'scale', label: 'Quota del progetto sui costi annui', kind: 'percent', default: 100, min: 1, max: 100,
            what: 'La parte delle spese dell’azienda che serve al progetto finanziato.', why: 'Un progetto raramente assorbe tutta l’attività: se il progetto vale metà delle spese di un anno, scrivi 50.', example: '100 se il progetto è tutta l’attività; 50 se è metà' }],
          submitLabel: 'Usa questa quota',
        })
        scale = vals?.scale || 100
      }
      a.done('quota', `${scale}% delle spese annue.`)

      // 3. la bozza
      a.begin('bozza', 'Leggo il bilancio e applico i tetti del bando…')
      let res
      for (;;) {
        try { res = await api.profileTemplate(bandoId, scale, true); break } catch (e) {
          a.fail('bozza', e.message)
          const ov2 = await ensureProfile(a, 'dati')
          if (!ov2 || ov2.last_year == null) { a.skip('personale'); a.skip('controllo'); a.finish('Non ho i costi del bilancio: la bozza non è stata creata.'); return }
          a.begin('bozza', 'Riprovo…')
        }
      }
      await b.applyTemplate(res)
      a.done('bozza', `${res.cost_items.length} voci per ${money(res.total_eur)} (bilancio ${res.base_year}).${res.adjustments.length ? ` Ridotte ${res.adjustments.length} categorie per i tetti del bando.` : ''}`)

      // 4. il personale
      if (res.needs_personnel) {
        a.begin('personale', `Nel bilancio il personale costa ${money(res.needs_personnel.amount_eur)}: il controllo vuole ogni persona a parte.`)
        const fl = await api.fields()
        const ccnl = fl.ccnl_levels || {}
        const codes = Object.keys(ccnl)
        const items = []
        for (let n = 1; codes.length; n += 1) {
          const who = await a.ask('personale', {
            title: `Persona ${n} del progetto: ruolo e contratto`, intro: 'Scrivi il ruolo, non il nome: i dati personali non servono. Poi il contratto collettivo (CCNL) con cui è assunta.',
            fields: [
              { key: 'description', label: 'Ruolo nel progetto', kind: 'text', what: 'Cosa fa questa persona nel progetto.', why: 'Compare nel budget e nel controllo.', example: 'Sviluppatore software senior' },
              { key: 'ccnl', label: 'Contratto collettivo (CCNL)', kind: 'select', options: codes.map((c) => ({ value: c, label: c.replace(/_/g, ' ').toLowerCase().replace(/^./, (m) => m.toUpperCase()) })),
                what: 'Il contratto nazionale di lavoro applicato in azienda: fissa le tabelle di costo orario con cui controllo la voce.', why: 'Senza CCNL non posso calcolare il costo ammissibile della persona.', where: 'Sul contratto di assunzione o sulla busta paga (riga «CCNL applicato»).' },
              { key: 'doc', label: 'Documento che lo giustifica', kind: 'text', optional: true, what: 'Un riferimento al documento da cui viene il costo.', why: 'Il controllo #1 chiede che ogni costo abbia un documento: se manca la voce resta «in attesa».', where: 'Nome o numero della busta paga o del contratto.', example: 'Busta paga marzo 2026' },
            ],
            submitLabel: 'Avanti', skipLabel: items.length ? 'Ho finito: nessun’altra persona' : 'Salto il personale',
          })
          if (!who) break
          const levels = ccnl[who.ccnl] || []
          const pay = await a.ask('personale', {
            title: `Persona ${n}: livello, stipendio e impegno`, intro: `«${who.description}» · ${who.ccnl.replace(/_/g, ' ').toLowerCase()}.`,
            fields: [
              { key: 'level', label: 'Livello di inquadramento', kind: 'select', options: levels.map((l) => ({ value: l, label: `Livello ${l}` })), what: 'Il livello scritto sul contratto o sulla busta paga.', why: 'Ogni livello ha un costo orario di riferimento nelle tabelle del CCNL.', where: 'Busta paga, campo «Livello» o «Qualifica».' },
              { key: 'ral', label: 'RAL (stipendio annuo lordo)', kind: 'money', min: 1, what: 'Quanto guadagna la persona in un anno, lordo, prima delle tasse.', why: 'Il costo del progetto si calcola sulla RAL, confrontata con le tabelle del contratto.', where: 'Contratto di assunzione, oppure la busta paga: retribuzione lorda mensile × 13 o 14 mensilità.', example: '34000' },
              { key: 'fte', label: 'Quanto tempo dedica al progetto', kind: 'percent', default: 100, min: 1, max: 100, what: 'La percentuale del suo tempo di lavoro che passa sul progetto.', why: 'Si rimborsa solo la parte di tempo dedicata al progetto.', example: '50 se lavora metà tempo sul progetto' },
              { key: 'months', label: 'Per quanti mesi', kind: 'number', default: 12, min: 1, max: 36, step: 1, suffix: 'mesi', what: 'La durata in cui la persona lavora al progetto.', why: 'Il costo si calcola sui mesi effettivi.', example: '12' },
            ],
            submitLabel: 'Aggiungi questa persona',
          })
          if (pay) items.push({ item_id: `P-ASS-${String(n).padStart(2, '0')}`, description: who.description, category: 'PERSONNEL', source_c_ref: who.doc || '', ccnl_code: who.ccnl, employee_level: pay.level, ral_eur: pay.ral, fte_allocation: pay.fte / 100, duration_months: Math.round(pay.months) })
          const more = await a.ask('personale', { title: items.length ? (items.length === 1 ? 'Aggiunta 1 persona' : `Aggiunte ${items.length} persone`) : 'Nessuna persona aggiunta', intro: 'Vuoi aggiungerne un’altra?', fields: [], submitLabel: 'Sì, aggiungine un’altra', skipLabel: 'No, ho finito' })
          if (!more) break
        }
        if (!codes.length) a.skip('personale', 'Nel sistema non ci sono ancora le tabelle dei contratti collettivi (CCNL): senza non posso controllare il costo di una persona e non ne scelgo uno al posto tuo. Le pubblica il Quartier Generale; appena ci sono, rifai questo passaggio.')
        else if (items.length) { await b.addItems(items); a.done('personale', `${items.length} ${items.length === 1 ? 'persona aggiunta' : 'persone aggiunte'} al budget.`) } else a.skip('personale', 'Nessuna persona aggiunta: la voce personale resta da inserire.')
      } else a.skip('personale', 'Il bilancio non ha costi di personale da dettagliare.')

      // 5. il controllo
      a.begin('controllo', 'Applico i 60 criteri a ogni voce…')
      const v = await b.validate()
      if (v) {
        const by = (s) => v.items.filter((i) => i.status === s).length
        a.done('controllo', `${by('APPROVED')} voci ammesse, ${by('CAP_EXCEEDED_ADJUSTED')} ridotte, ${by('REJECTED')} respinte, ${by('MISSING_DOCUMENTS')} in attesa di documento.`)
        a.finish(`Budget controllato per «${detail.name}»: ${money(v.items.reduce((s, i) => s + (i.computed_cost_eur || 0), 0))} ammessi su ${money(v.items.reduce((s, i) => s + (i.original_cost_eur || 0), 0))} richiesti.\nGli importi della bozza vengono dal bilancio e sono una base: sostituisci le voci di ammortamento con gli acquisti che prevedi, e allega i documenti alle voci in attesa.`)
      } else { a.done('controllo', 'Non ho potuto avviare il controllo: guarda i messaggi nella pagina Budget.'); a.finish('Bozza creata. Il controllo non è partito: apri «Controlla il budget» nella pagina.') }
    },
  },

  profilo: {
    title: 'Completare i dati dell’azienda',
    blurb: 'Ti chiedo i dati che mancano nel profilo (visura e bilancio), spiegandoti dove trovarli, e li salvo io.',
    steps: [{ id: 'profilo', title: 'Apro il profilo dell’azienda' }, { id: 'dati', title: 'Controllo cosa manca e te lo chiedo' }],
    async run(a) {
      const b = a.bridge()
      a.begin('profilo'); b.go('profilo'); await a.pause(700); a.done('profilo', 'Profilo aperto.')
      const ov = await ensureProfile(a, 'dati')
      a.finish(ov ? 'I dati sono nel profilo: tutte le pagine li usano da subito.' : 'Nessun dato salvato.')
    },
  },
}
export const TASK_ORDER = ['allocazione', 'budget', 'deminimis', 'profilo']
