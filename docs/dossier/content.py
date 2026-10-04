"""Testo del dossier QUANTO v3.0. Ogni affermazione di stato è stata verificata sul codice o sul sistema online il 4 ottobre 2026."""
from __future__ import annotations

import json
from pathlib import Path

FACTS = json.loads((Path(__file__).parent / "facts.json").read_text(encoding="utf-8"))


def build(m):  # noqa: C901 - un documento lungo è una sola funzione di testo
    H1, H2, H3, P, B, T, NOTE, CODE, SP, story = m.H1, m.H2, m.H3, m.P, m.B, m.T, m.NOTE, m.CODE, m.SP, m.story
    from reportlab.platypus import PageBreak, Paragraph

    # ------------------------------------------------------------------------------------------------ copertina
    story.append(Paragraph("QUANTO v3.0 — Documento Completo", m.S["title"]))
    story.append(Paragraph("Motore di budgeting, allocazione annuale e profilo aziendale per la finanza agevolata", m.S["sub"]))
    story.append(Paragraph("Riscrittura integrale del documento FKOS v2.1, aggiornata allo stato reale del sistema al 4 ottobre 2026. Nessuna sintesi: ogni processo è spiegato nel dettaglio e ogni funzione porta il suo stato.", m.S["p"]))
    SP(6)
    H1("Nota di apertura — cosa contiene questo documento e cosa è cambiato")
    P("Questo documento riprende, modulo per modulo, la struttura del documento «FKOS v2.1 — Documento Completo» (22 moduli, executive summary, schema tecnico API) e la porta al presente. "
      "Il prodotto oggi si chiama **QUANTO** (FKOS era il nome di lavoro) ed è in produzione su https://quanto-self.vercel.app. A differenza della v2.1, che descriveva un progetto da costruire, "
      "questa versione descrive un sistema che esiste: per ogni funzione si dice se è **realizzata e verificata**, **parziale**, oppure **ancora da fare**, e cosa manca per il 100%.")
    P("Le quattro decisioni strategiche della v2.1 restano il perno e sono tutte rispettate dal codice:")
    B(["**QUANTO non scrive progetti.** Nessun testo persuasivo, nessuna relazione illustrativa: solo la componente numerica (budget, ammissibilità, allocazione, stima dell'anno successivo).",
       "**Multi-verticale fin dal disegno.** Catalogo nazionale di oltre 5.900 misure letto dalle fonti istituzionali; le regole si estraggono solo su richiesta, con cache.",
       "**Metriche oneste e separate.** Nessun tasso di errore dichiarato prima di avere pratiche reali (Modulo 14).",
       "**Pricing ibrido.** Oggi l'app è gratuita e mostra un'anteprima a crediti (Modulo 21): il pagamento reale non esiste ancora."])
    P("A queste si aggiungono decisioni prese dopo la v2.1, riportate con la data nel Modulo 26: eliminazione della blockchain (19/09/2026), regola «mai dati inventati» (ogni numero risale a una fonte reale o dichiara la propria lacuna), "
      "un solo processo standard per studiare ogni bando (01/10/2026), nessuna migrazione di Tailwind finché non serve (03/10/2026).")

    H2("Legenda degli stati")
    T([["Etichetta", "Significato"],
       ["[[FATTO]]", "Realizzato, coperto da test automatici e, dove ha senso, provato online con dati reali."],
       ["[[PARZIALE]]", "Esiste e funziona, ma con un limite dichiarato (copertura, dato mancante, componente non collegata)."],
       ["[[DA FARE]]", "Previsto nella v2.1 e non ancora realizzato."],
       ["[[FASE 3]] [[FASE 4]]", "Visione a lungo termine, volutamente non anticipata."],
       ["[[DECISIONE]]", "Scelta presa dopo la v2.1 che cambia il disegno originale."]], [45, 125])

    # ------------------------------------------------------------------------------------------------ stato in una pagina
    H1("Lo stato in una pagina")
    T([["Modulo (v2.1)", "Stato", "In una riga"],
       ["1-3 Visione, missioni, posizionamento", "[[FATTO]]", "Le due missioni sono entrambe in produzione; la seconda (allocazione) è stata ricostruita attorno al profilo aziendale."],
       ["4-6 Demo e pattern vincenti", "[[PARZIALE]]", "Pagina Confronto, 5 budget reali di società quotate, k-means; con meno di 6 budget per categoria c'è un solo archetipo (la media), dichiarato."],
       ["7 Disaccoppiamento / Strict Grounding", "[[PARZIALE]]", "Motore e validatore numerico completi; il modello linguistico non è collegato in produzione (nessuna chiave), il testo è il template fisso."],
       ["8 Console", "[[FATTO]]", "7 pagine cliente + Algoritmo + Quartier Generale (11 sezioni). Il frontend non calcola mai nulla."],
       ["9.1 Fonte A (normativa)", "[[PARZIALE]]", "Catalogo, trigger, cache, pipeline standard, Stadio 2 deterministico, coda di revisione: fatti. Stadio 3 con più passaggi AI: pronto ma spento. Audit di calibrazione: da fare."],
       ["9.2 Fonte B (tabelle)", "[[PARZIALE]]", "Versionata per data nel database, nessun valore nel codice; 3 CCNL, 2 parametri, 5 aliquote; zero benchmark di prezzo/tariffa."],
       ["9.3 Fonte C (dati del cliente)", "[[FATTO]]", "6 tipi di documento, cifratura AES-256-GCM, confidenza per campo, revisione, token per i dati personali. OCR su scansioni solo dove gira Tesseract (non su Vercel)."],
       ["9.4 Profilo aziendale (nuovo)", "[[FATTO]]", "Dati dell'impresa e bilanci per esercizio con provenienza, procedura guidata, stima, abbinamento ai bandi, bozza di budget."],
       ["10-11 Motore e 60 criteri", "[[FATTO]]", "Tutti i 60 criteri implementati con Decimal; un criterio senza dato o regola è «non valutato», mai «superato»."],
       ["12 Allocazione annuale", "[[FATTO]]", "MILP esatto (HiGHS), verifica in centesimi; nuova pagina a 4 passi dal bilancio al piano."],
       ["13 Dove interviene l'AI", "[[PARZIALE]]", "Confini rispettati; unica AI in produzione: la ricerca Brave per trovare i documenti, non per interpretarli."],
       ["14 Metriche", "[[FATTO]]", f"{FACTS['tests']} test automatici passano; nessuna metrica su pratiche reali (non esistono)."],
       ["15 Stack", "[[FATTO]]", "FastAPI + PostgreSQL + React/Vite su Vercel; CI con test, build e audit delle dipendenze."],
       ["16 Sicurezza e GDPR", "[[FATTO]]", "Cifratura a riposo, pseudonimizzazione, scrypt, blocco account, RLS su tutte le tabelle, intestazioni di sicurezza e CSP. DPA e valutazione d'impatto: da fare."],
       ["17 Registro crittografico", "[[DECISIONE]]", "Anticipato dalla Fase 2 e realizzato SENZA blockchain: catena di hash firmata Ed25519, Merkle, attestazioni offline, Auditor Portal."],
       ["18 Componente assicurativa", "[[FASE 3]]", "Non toccata, per scelta."],
       ["19 Reparto di consulenza", "[[FASE 4]]", "Non toccato; esiste solo la «scheda per il consulente» nel Quartier Generale."],
       ["20-22 Go-to-market", "[[DA FARE]]", "Nessuna attività commerciale avviata; registrazione libera e crediti simulati pronti."]], [52, 22, 96])

    H2("Numeri del sistema (verificati il 4 ottobre 2026)")
    T([["Dato", "Valore"],
       ["Test automatici backend", f"{FACTS['tests']} (tutti verdi; CI su ogni push: test su PostgreSQL 16, build, audit dipendenze)"],
       ["Endpoint REST", "121 sotto /api/v2 (più la radice di salute)"],
       ["Migrazioni del database", "11 (init, fonte_b, fonte_c, funding_lines, users, pattern, draft_doc_type, enable_rls, requirement_figures, company_profile, catalog_meta)"],
       ["Tabelle", "24, tutte con Row Level Security attiva"],
       ["Criteri del motore", "60 su 60 implementati"],
       ["Catalogo nazionale", f"{FACTS['catalog_total']} voci aperte o senza data (da 5.975 prima della pulizia); {FACTS['catalog_open']} con scadenza futura certa, {FACTS['catalog_undated']} senza data; tutte con la scheda letta"],
       ["Bandi in memoria", f"{FACTS['bandi']} voci totali; 9 curati a mano; {FACTS['studied']} del catalogo già studiati con il processo standard"],
       ["Regole / requisiti letti", f"{FACTS['rules']} regole pubblicate o in revisione, {FACTS['requirements']} requisiti, {FACTS['sources']} documenti di fonte con {FACTS['files']} file originali conservati"],
       ["Fonte B pubblicata", "3 CCNL (Commercio, Metalmeccanica, Terzo settore), 2 parametri nazionali, 5 aliquote d'ammortamento, 0 benchmark"],
       ["Banca dei pattern", "5 budget da bilanci di società quotate, ciascuno con pagina e nota della fonte"],
       ["Database", f"PostgreSQL, {FACTS['db_mb']} MB, {FACTS['events']} eventi registrati, {FACTS['runs']} esecuzioni salvate"],
       ["Registro firmato", "1 registrazione (prova della demo), catena integra, chiave di firma 4e5773cd74cfe97d"]], [48, 122])

    H2("Cosa è cambiato rispetto alla v2.1 — in dettaglio")
    T([["Area", "v2.1 (progetto)", "Oggi (sistema)"],
       ["Nome", "FKOS", "QUANTO"],
       ["Registro (Mod. 17)", "Fase 2: albero di Merkle + hash dei documenti, ancoraggio non specificato", "Realizzato: catena di hash append-only firmata Ed25519, Merkle con separazione di dominio (RFC 6962), attestazione verificabile offline, Auditor Portal con QR. Blockchain eliminata per decisione del 19/09/2026."],
       ["Database", "PostgreSQL + vettoriale", "PostgreSQL con 11 migrazioni, trigger che rendono il registro append-only, RLS. Nessun database vettoriale: la lettura delle fonti è lessicale e strutturata (vedi 9.1)."],
       ["Fonte B", "Connettori che scaricano le tabelle", "Caricamento da file con bozza → attestazione → pubblicazione da un manager, versioni per data di validità, provenienza obbligatoria. I connettori automatici non esistono."],
       ["Fonte C", "Buste paga, F24, registri IVA, bilanci, piano dei conti, organigrammi", "Buste paga, bilanci (schema civilistico), F24, bozze di candidatura, visure camerali, altri documenti (archiviati e non letti). Registri IVA e piano dei conti: non letti."],
       ["Profilo aziendale", "Non previsto", "Nuovo: dati dell'impresa, bilanci per esercizio, provenienza di ogni valore, procedura guidata, stima dell'anno successivo, bandi adatti, bozza di budget."],
       ["Catalogo (Stadio 1)", "Metadati: nome, ente, scadenza, link", "Più la descrizione ufficiale e le caratteristiche della scheda (forma di agevolazione, costi ammessi, dimensione, regioni, ATECO), la scadenza, lo stato aperto/chiuso e l'ordinamento per affinità con l'azienda. Le voci chiuse vengono eliminate ogni notte."],
       ["Studio di un bando", "Stadio 2 e 3 sparsi", "Un solo processo standard: cerca → scarica → leggi → valuta, con rapporto di completezza (COMPLETA / PARZIALE / INSUFFICIENTE) e motivo di ogni lacuna."],
       ["Allocazione", "Dal bilancio all'anno successivo, fondi dal codice o a mano", "Pagina a 4 passi: dati → stima (variazione scelta dall'utente) → bandi adatti con tetti e riduzioni → piano MILP con i bandi spuntati. I fondi si ricavano dalle regole pubblicate dei bandi."],
       ["Criteri", "Fino a 60, costruiti progressivamente", "60 su 60. Un criterio senza dato o regola risulta «non valutato», mai «superato»."],
       ["Pattern", "Banca da graduatorie pubbliche", "Bilanci reali di società quotate (cinque), k-means con soglia dichiarata; sotto soglia una sola media."],
       ["Utenti", "Non descritti", "Account con ruoli USER e MANAGER, accesso riservato al titolare per il Quartier Generale, registrazione libera, crediti simulati."],
       ["LLM", "Renderer + Stadio 3", "Modulo completo e testato, spento in produzione (nessuna chiave): vale il template fisso."],
       ["Interfaccia", "4 viste + pannello interno", "Bandi, Budget, Allocazione, Confronto, Verifica, Guida, Profilo + Algoritmo (dal Budget) + Quartier Generale (11 sezioni)."],
       ["Webhook", "8 eventi", "7 eventi emessi; consultation.requested e rule.audit_flagged non attivi (dipendono da Fase 4 e dall'audit)."],
       ["Qualità", "Regression test sui 60 criteri", f"{FACTS['tests']} test su PostgreSQL reale, CI con azioni fissate per impronta, Dependabot, audit delle dipendenze."]], [28, 50, 92])
    story.append(PageBreak())

    # ------------------------------------------------------------------------------------------------ indice
    H1("Indice")
    for line in ["PARTE I — Visione e missione: Moduli 1-3", "PARTE II — La demo e la validazione dei pattern vincenti: Moduli 4-6",
                 "PARTE III — Architettura tecnica e algoritmica: Moduli 7-16 (con il nuovo 9.4 Profilo aziendale)",
                 "PARTE IV — La visione a lungo termine: Moduli 17-19", "PARTE V — Go-to-market: Moduli 20-22",
                 "PARTE VI — Il sistema com'è oggi (nuova): Moduli 23-27 — Quartier Generale, dati e database, cosa fa l'app a ogni azione, esito del test demo, cosa manca per il 100%",
                 "Executive summary", "Schema tecnico API (reale)", "Appendici A-D — variabili d'ambiente, tabelle, test, cronologia delle fasi"]:
        P(line)

    # ================================================================================================ PARTE I
    H1("PARTE I — VISIONE E MISSIONE")
    H2("MODULO 1 — La missione: motore di budgeting, non copilota di scrittura")
    H3("1.1 Cosa NON è QUANTO")
    P("QUANTO non genera testo progettuale, non scrive obiettivi, non redige la narrativa che convince la commissione. Il limite è strutturale: non esiste un solo endpoint di generazione testuale progettuale. "
      "Il testo che l'app produce è solo la frase di riepilogo di un calcolo già fatto, oggi un template fisso con le cifre iniettate dal motore (campo `explanation_source: TEMPLATE` nella risposta di validazione).")
    H3("1.2 La genesi del problema")
    P("Invariata: il consulente tradizionale lavora a compartimenti stagni e produce budget generici; l'IA generica stima invece di calcolare e sbaglia sistematicamente sui numeri (costi orari fuori scala, lordo e netto confusi, categorie di beni non ammesse). "
      "QUANTO occupa lo spazio in mezzo: calcola, non stima e non scrive. Il caso che l'ha reso concreto è stato il nostro: un'azienda con bilanci e buste paga vuole sapere a quali bandi può accedere, quali spese rientrano, di quanto vanno ridotte e quanto vale il contributo.")
    H3("1.3 Perché non restringersi a un solo bando")
    P("Rispettato. Il motore ospita le regole di qualsiasi bando come istanze dello stesso insieme di criteri. Oggi il sistema contiene 9 bandi curati a mano (Transizione 5.0 – iperammortamento, Nuova Sabatini, Horizon Europe, Smart&Start Italia, Investimenti Sostenibili 4.0, Fondo di Garanzia PMI, SIMEST 394/81, FVG Validazione TRL, più il bando di prova a 60 criteri) "
      "e un catalogo nazionale di oltre 800 misure aperte, delle quali una quota si studia su richiesta. L'ampiezza di copertura resta funzione di quanti bandi sono stati studiati, non un interruttore: **oggi 13 bandi reali (più il bando di prova) hanno regole o requisiti letti**, gli altri sono descritti ma non valutabili in euro.")

    H2("MODULO 2 — Il prodotto reale: le due missioni")
    H3("2.1 Missione Uno — in fase di candidatura  [[FATTO]]")
    P("L'utente sceglie un bando, inserisce o importa le voci (a mano, da Excel/CSV, da una candidatura già scritta in PDF, da una busta paga, **dalla bozza costruita sul proprio bilancio**) e preme «Controlla il budget». "
      "Per ogni voce il motore dice se è ammissibile, a quale importo, con quali criteri e perché; il budget intero riceve un punteggio di conformità, una Merkle Root e un CEP-ID. Si esporta in Excel e PDF con QR verso la verifica.")
    P("**Ripartizione delle voci tra i pacchetti di lavoro (WP)  [[FATTO]]** (realizzata il 4 ottobre 2026). Dopo il controllo, la scheda «Pacchetti di lavoro (WP)» della pagina Budget divide il budget **ammesso** (importi approvati dal motore, non quelli richiesti) tra i WP del bando. "
      "Nessun vincolo è inventato: li scrive chi conosce il bando, e per ogni WP sono tutti facoltativi.")
    T([["Vincolo per WP", "Significato"],
       ["Quota minima / massima", "Percentuale del totale ammesso che il WP deve almeno raggiungere o non superare."],
       ["Quota desiderata", "Il piano si avvicina il più possibile (somma degli scostamenti assoluti minima)."],
       ["Categorie ammesse", "Quali categorie di spesa il WP può contenere (di default tutte)."],
       ["Tetto per categoria nel WP", "Es. consulenze al massimo il 30% del WP: Σ importi consulenze ≤ 30% · totale del WP."],
       ["Voce assegnata a mano", "L'utente può fissare una voce a un WP (menu «Sposta in»): il calcolo riparte rispettandola."],
       ["Dividere le voci", "Se consentito, una voce può stare in più WP; si divide solo quando serve (ogni divisione costa poco nell'obiettivo)."]], [48, 122])
    P("**Come funziona.** Programma lineare misto-intero risolto con HiGHS, come l'allocazione annuale: variabile x_iw (voce i nel WP w; binaria se non si dividono le voci), Σ_w x_iw = 1, bound a zero per le categorie non ammesse, quote del WP tra minimo e massimo, tetti per categoria dentro il WP, "
      "obiettivo = scostamento dalle quote desiderate; a parità i WP si riempiono nell'ordine indicato. Gli importi finali sono in centesimi (una voce non divisa resta intera; una divisa si distribuisce per resti maggiori, la somma è esatta) e tutto è **ri-verificato in aritmetica esatta**. "
      "Se non esiste una ripartizione il sistema non forza nulla: spiega perché (nessun WP ammette una categoria, tetti che sommano a meno del 100%, quote minime oltre il 100%) e, quando i vincoli si scontrano, indica quali voci restano fuori e di quanto.")
    P("**Esempio verificato da test.** Quattro voci ammesse da 60.000, 20.000, 15.000 e 5.000 € e tre WP con quote desiderate 50%, 30% e 20% (il primo con massimo 60%): senza dividere voci lo scostamento totale minimo è di 20 punti; consentendo di dividerne una (la voce da 60.000 € tra i primi due WP) le quote tornano esattamente 50/30/20. "
      "L'operazione compare in timeline e nella mappa delle operazioni; il risultato si scarica in CSV. Non è un controllo dei 60 criteri: le regole del bando sui tetti per categoria restano affidate al motore, i vincoli per WP sono quelli dichiarati dall'utente.")
    H3("2.2 Missione Due — pianificazione ordinaria  [[FATTO]]")
    P("L'ente carica visura e bilanci (anche più anni) nel Profilo; l'Allocazione stima le spese dell'anno successivo partendo dall'ultimo bilancio con le variazioni scelte dall'utente, valuta i bandi studiati e il catalogo, "
      "mostra quanto ogni bando coprirebbe e quali voci vanno ridotte per rispettare i tetti, e calcola il piano ottimo con i bandi scelti: quale fonte copre quale spesa, quanto resta a carico, come si distribuisce mese per mese.")
    H3("2.3 Il filo conduttore")
    P("Le due missioni condividono motore, fonti A/B/C e console. L'effetto di lock-in descritto nella v2.1 è ora concreto: il **profilo aziendale** è il ponte. Un'azienda che ha caricato i suoi documenti per la pianificazione arriva al bando con la bozza di budget già costruita sui propri bilanci.")

    H2("MODULO 3 — Il posizionamento competitivo")
    P("Invariato nel contenuto: QUANTO non è uno strumento di scrittura, non è un FP&A generalista privo di conoscenza normativa, non è IA generica. È il motore di calcolo che le tre categorie possono usare. "
      "Un elemento nuovo rafforza la differenza: il catalogo con le schede ufficiali e l'ordinamento per affinità trasforma «quale bando fa per me?» da ricerca manuale a lista ordinata e motivata (regione, dimensione, ATECO, settore, spese ammesse), senza promettere un esito.")

    # ================================================================================================ PARTE II
    H1("PARTE II — LA DEMO E LA VALIDAZIONE DEI PATTERN VINCENTI")
    H2("MODULO 4 — La demo reale  [[PARZIALE]]")
    P("La demo si esegue oggi con dati reali. Sull'account di prova (Meridiana Digital Solutions S.r.l., azienda interamente fittizia con 14 documenti coerenti tra loro) il percorso è: procedura guidata nel Profilo (profilo dallo 0% al 92% con un solo gesto di caricamento, 100% dopo una risposta), "
      "stima 2027 dall'ultimo bilancio, confronto con 12 bandi studiati e 136 voci del catalogo, bozza di budget per il bando scelto, controllo dei 60 criteri, esportazione, registrazione dell'impronta, verifica (anche con manomissione simulata), confronto con i budget premiati.")
    B(["**Selezione del bando:** da catalogo o ricerca per nome (ricerca interna, poi web con Brave Search). [[FATTO]]",
       "**Budget bozza:** a mano, Excel, PDF di candidatura, busta paga o bilancio dell'azienda. [[FATTO]]",
       "**Pattern comparabili:** i budget storici della categoria scelta; con i dati attuali (3 e 2 budget) si ottiene un solo archetipo per categoria, dichiarato come media. [[PARZIALE]]",
       "**Pattern Similarity Score** con scostamento principale, e pulsanti «Usa il budget che ho controllato» e «Usa i costi del mio profilo». [[FATTO]]",
       "**Simulazione di correzione in tempo reale:** ogni modifica rilancia il confronto sul server dopo 450 ms. [[FATTO]]",
       "**Conformity Score** in parallelo, con motivazione per ogni voce respinta o sospesa. [[FATTO]]"])
    H3("4.3 Perché la demo è onesta")
    P("Ogni elemento è verificabile nello stesso momento: i budget storici sono bilanci pubblicati con la pagina da cui derivano (visibile in «Banca pattern» del Quartier Generale), il calcolo è deterministico, la correzione ha il riferimento esatto. "
      "Esempio reale della demo del 4 ottobre: ripartizione dell'azienda di prova (64,8% personale, 8,2% beni, 12,5% consulenze, 13,2% spese generali, 1,3% formazione) → archetipo «TRAZIONE_BILANCIATA», somiglianza 0,87, scostamento principale −24,8 punti sulle spese generali; i tre budget più simili sono Websolute (93,3%), Alkemy (82,5%) e Doxee (79,9%).")
    NOTE("Il valore dello scostamento dipende dal dataset corrente (5 budget).")

    H2("MODULO 5 — La banca dati dei pattern vincenti  [[PARZIALE]]")
    P("Struttura del dato: per ogni budget la ripartizione percentuale tra sei categorie (personale, beni, consulenze, spese generali, formazione, comunicazione) più metadati (categoria di bando, fonte obbligatoria, anno, punteggio opzionale). "
      "L'importazione avviene da CSV nel Quartier Generale (sezione «Banca pattern») e **blocca le righe incomplete**; la fonte è obbligatoria su ogni riga.")
    T([["Categoria", "Budget", "Fonti (tutte bilanci pubblicati, con pagina e criterio di calcolo nella nota)"],
       ["DIGITALE_ICT", "3", "Websolute S.p.A. (consolidato 2024), Alkemy S.p.A. (consolidato 2023, anno scelto per escludere un impairment one-off), Doxee S.p.A. (bilancio d'esercizio 2024)"],
       ["MANIFATTURIERO_INDUSTRIA40", "2", "Vimi Fasteners Group (consolidato 2024), Fervi S.p.A. (consolidato 2024)"]], [48, 14, 108])
    P("Differenza dalla v2.1: le graduatorie pubbliche dei bandi non sono ancora state importate (il piano finanziario di sintesi è raro e disomogeneo); la banca parte da bilanci di società quotate, che sono dati veri e verificabili ma sono proxy di struttura di costo, non budget di progetto vincenti. "
      "Il vero set di pattern vincenti (graduatorie e dati del pilota con consenso) resta **[[DA FARE]]** ed è la prima voce dei dati da fornire (Modulo 27).")
    H2("MODULO 6 — L'algoritmo di pattern matching  [[FATTO]]")
    B(["**Fase uno — archetipi:** k-means++ con seme fisso (stesso dataset, stessi archetipi). Sotto **6 budget per categoria** non si finge un clustering: c'è un solo archetipo, la media, dichiarata come tale («media di 3 budget: servono almeno 6 per fare il clustering»).",
       "**Fase due — similarità:** similarità del coseno tra il vettore delle sei quote e ogni archetipo; si restituiscono archetipo più vicino, scostamento voce per voce in punti percentuali, i tre budget storici più simili con fonte, e il Conformity Score del budget controllato.",
       "**Natura statistica dichiarata:** è l'unico calcolo non univoco; non c'è alcun modello linguistico. L'etichetta dice sempre «indicazione statistica, non previsione»."])

    # ================================================================================================ PARTE III
    H1("PARTE III — ARCHITETTURA TECNICA E ALGORITMICA")
    H2("MODULO 7 — Architettura generale: il principio di disaccoppiamento  [[PARZIALE]]")
    P("Il motore proprietario (codice puro) è separato dal renderer linguistico da un contratto JSON. Il modello linguistico non riceve mai documenti grezzi né interroga le fonti; riceve solo il risultato calcolato e bloccato. "
      "Il **validatore numerico** confronta ogni numero del testo prodotto con quelli del JSON in aritmetica Decimal, senza tolleranza; un solo numero diverso fa scartare il testo e subentra il template fisso.")
    T([["Componente", "Stato", "Dettaglio"],
       ["Motore deterministico", "[[FATTO]]", "decimal.Decimal per ogni operazione monetaria; float solo ai bordi; ogni riga ha traccia dei criteri eseguiti, falliti e non valutati."],
       ["Validatore numerico", "[[FATTO]]", "Gli identificativi (LINE-001, 0x7f83…) non sono «numeri» e devono comparire testualmente nel JSON."],
       ["Renderer", "[[FATTO]]", "Flusso: JSON bloccato → (LLM opzionale) → validatore → template di ripiego."],
       ["Collegamento al modello linguistico", "[[PARZIALE]]", "Modulo llm.py completo (provider anthropic, modello e numero di passaggi da variabili d'ambiente), 12 test; in produzione nessuna chiave: il testo è sempre il template. È il motivo per cui le risposte riportano explanation_source = TEMPLATE."]], [42, 24, 104])
    H3("7.4 Il chiarimento sull'AI nell'ingestion")
    P("Resta valido: l'AI dell'ingestion opera a monte, nella costruzione della Fonte A; il disaccoppiamento riguarda ciò che accade a valle. Oggi la differenza è netta: **in produzione l'ingestion usa solo codice**; l'unico servizio esterno è il motore di ricerca (Brave) che trova gli indirizzi, mai che interpreta un numero.")

    H2("MODULO 8 — Il livello grafico: la Console  [[FATTO]]")
    H3("8.1 Filosofia di interfaccia")
    P("Ogni numero mostrato è verificabile: l'Ispettore di una voce mostra fonti, formula e ogni controllo con il motivo; le cifre della procedura guidata e dell'allocazione dicono da quale documento o regola arrivano. Il frontend non esegue mai un calcolo economico: ogni interazione genera una chiamata e un risultato lato server.")
    H3("8.2 Le pagine (oggi)")
    T([["Pagina", "Cosa fa", "Corrispondenza con la v2.1"],
       ["Bandi", "Libreria dei bandi studiati e curati; sfoglia tutto il catalogo con le descrizioni; cerca sul web; aggiungi un documento a mano; pulsante «Studia il bando».", "Vista «Bandi attivi»"],
       ["Budget", "Voci per categoria, controllo dei 60 criteri, Ispettore, modifica voce, bozza dal profilo azienda, ripartizione tra i pacchetti di lavoro (WP), import Excel/PDF, export XLSX/PDF, registrazione dell'impronta.", "Vista 1 Budget Canvas + Vista 4 Report"],
       ["Allocazione", "Quattro passi: dati dell'azienda, stima dell'anno, bandi adatti (adatti / da verificare / non adatti / da studiare), piano con Sankey, uso dei fondi e mesi.", "Vista 2 Allocazione annuale"],
       ["Confronto", "Pattern matching con archetipi e budget storici più simili.", "Vista 3 Demo Pattern"],
       ["Verifica", "Auditor Portal: verifica impronta, ricalcolo dai dati, manomissione simulata.", "Modulo 17 (anticipato)"],
       ["Guida", "Percorso rapido, Merkle passo passo, ogni funzione con un esempio, glossario.", "—"],
       ["Profilo", "Procedura guidata a passi, dati e bilanci dell'azienda, crediti, operazioni recenti, documenti con anteprima, download singolo e scarico di tutti i file in un archivio ZIP.", "Nuova (Modulo 9.4)"],
       ["Algoritmo", "Il «film» del calcolo: 7 fasi, mappa voci × 60 controlli, cascata degli importi, albero di Merkle. Si apre dal Budget.", "—"],
       ["Quartier Generale", "Solo titolare: 11 sezioni (Modulo 23).", "Pannello di Ingestion (Mod. 8.4), esteso"]], [28, 100, 42])
    H3("8.3 Stack di presentazione")
    P("React 18.3 con Vite 7.3 e Tailwind 3.4, icone Lucide, font Archivo, Outfit e JetBrains Mono. Stile: riquadri in forma di finestra («chrome») sulle pagine principali, tipografia marcata, e nella homepage lo sfondo «catena di blocchi» al posto della precedente animazione a costellazioni. "
      "Due fatti di processo: il frontend non ha router (si naviga con uno stato interno), e la migrazione a Tailwind 4 è stata rimandata per decisione del 03/10/2026 perché non è necessaria (gli avvisi «high» restanti riguardano solo la catena di build di Tailwind 3, non il codice in produzione).")
    H3("8.4 Il Pannello di Ingestion")
    P("Esiste, ed è la sezione «Bandi» e «Catalogo» del Quartier Generale: per ogni bando, documenti (testo estratto e file originale), regole (anche quelle in disaccordo), requisiti, scheda per il consulente, linea di finanziamento per l'allocazione, utilizzi, esportazione ZIP; per il catalogo, descrizioni e caratteristiche. Non è visibile agli utenti.")
    story.append(PageBreak())

    H2("MODULO 9 — Il triplo motore di retrieval proprietario (Fonti A, B, C)")
    H3("9.1 Fonte A — normativa e prassi  [[PARZIALE]]")
    P("**Stadio 1 — ricerca e catalogazione  [[FATTO]].** Due lavori notturni di Vercel Cron: `catalog-refresh` (03:00) aggiorna il catalogo dalle mappe del sito di incentivi.gov.it (circa 5.900 misure: nazionali, regionali, comunali, camere di commercio, GAL) e di Invitalia, legge le date e cancella le voci chiuse; "
      "`catalog-describe` (03:30) legge la scheda ufficiale di ogni voce. Le informazioni che si salvano sono **lette dalla pagina**, mai scritte da un modello:")
    B(["titolo ufficiale (og:title; il nome ricavato dall'indirizzo è accorciato e generico);", "descrizione breve (la «description» dichiarata dalla scheda, oppure il primo paragrafo di «Cos'è», tagliato a fine frase evitando abbreviazioni come «n.» o «art.»);",
       "forma di agevolazione, costi ammessi, spesa ammessa e agevolazione concedibile (minimo-massimo), tipologia di soggetto, dimensione, settori, ATECO, regioni, comuni, aree speciali, soggetto gestore, date di apertura e chiusura e stato (aperto, in arrivo, chiuso, senza data)."])
    P("Stato al 4 ottobre: 5.409 schede lette in un'unica passata di circa 4 minuti (400 per chiamata, 24 richieste in parallelo), 4.685 voci già chiuse eliminate, 801 voci restanti, tutte con descrizione. Una voce si rilegge se la versione di lettura salvata è più vecchia (`read_v`).")
    P("**Ordinamento per affinità.** Per le voci non ancora studiate, l'Allocazione calcola un punteggio spiegato, senza alcun importo: 0,75 × la quota delle spese previste dell'azienda coperta dai «costi ammessi» della scheda; +0,10 se la misura è locale (al massimo 3 regioni) e include la regione dell'azienda; "
      "+0,15 se tra i settori elencati (massimo 10) c'è il suo (la divisione ATECO si traduce nelle parole delle schede: 62 → ICT, 25 e 28 → meccanica, 56 → ristorazione, ecc.), −0,30 se sono elencati settori che non includono il suo; +0,05 per le start-up innovative; −0,40 se la misura è per «start-up» e l'impresa ha almeno cinque anni. "
      "Sono esclusi i bandi scaduti, riservati a un'altra regione o dimensione d'impresa, con ATECO incompatibili, o per start-up innovative quando l'azienda dichiara di non esserlo. A pari punteggio vince chi scade prima. Ogni risultato elenca i motivi e ciò che resta da verificare.")
    P("**Trigger e cache  [[FATTO]].** L'estrazione delle regole parte quando un cliente conferma il bando («Sì, è questo» o «Studia questo bando»). Se le regole di quel bando sono già in memoria vengono riusate (`cache_hit`) e il contatore `requested_by_clients_count` cresce; altrimenti parte il processo standard.")
    P("**Il processo standard di studio  [[FATTO]]** (`pipeline.py`, uguale per ogni bando e ripetibile):")
    B(["**Cerca:** otto interrogazioni sul nome; scoperta senza motori di ricerca dai cataloghi, dagli elenchi di Invitalia e MIMIT e dai portali di famiglia (Erasmus+, coesione/FSE/FESR/PNRR, PSR, energia, export); con la chiave Brave attiva si usa anche la ricerca web. Ogni risultato è classificato UFFICIALE (Gazzetta Ufficiale, Normattiva, EUR-Lex, ministeri, Invitalia, regioni…) o SECONDARIA.",
       "**Scarica:** in parallelo, con un secondo giro sui PDF ufficiali collegati dalle pagine scaricate; ogni documento è salvato intero (testo e file originale) con la sua impronta SHA-256. Protezioni: guardia contro richieste verso indirizzi interni (SSRF), limite di dimensione e di tempo, limite di frequenza (400 richieste ogni 10 minuti).",
       "**Leggi (`analysis.py`):** nessun documento può risultare «vuoto» senza dire perché (lingua, testo usato, motivo). Tre decisioni uguali per tutti: un foglio elettronico è dato di riferimento (conservato, non letto); tra le edizioni dello stesso documento conta solo l'ultima; un documento «severo» (che si intitola come il bando o lo cita spesso) si legge intero, gli altri solo nei passaggi che nominano il bando, e le regole numeriche ricavate da questi ultimi si pubblicano solo se confermate da due fonti.",
       "**Valuta:** rapporto con soglie fisse: COMPLETA, PARZIALE o INSUFFICIENTE, e l'elenco dei motivi di ogni lacuna.",
       "**Dopo la lettura:** requisiti con tema, tipo (obbligo, divieto, limite, informazione, da rivedere), controlli collegati, sezione di provenienza e **cifre strutturate** (percentuali, importi, durate con qualificatore massimo/minimo/riferimento). Cinque regole numeriche si ricavano da cifre con frase-guida e un solo valore corrispondente (tetto d'installazione, intensità d'aiuto, anticipo, variazione tra capitoli, ritardo di rimborso in mesi); i conflitti vanno in revisione con i candidati."])
    P("Esito reale sul bando CNR «progetti di ricerca industriale e sviluppo sperimentale» (studiato dall'Allocazione online il 4 ottobre): lettura completa, 8 documenti ufficiali, 165 requisiti, 90 cifre, 2 regole numeriche.")
    P("**Ciclo di vita  [[FATTO]].** Dalle schede si leggono «Data apertura» e «Data chiusura». Ogni notte si eliminano le voci mai toccate e certamente chiuse (con scadenza passata, oppure senza data e il cui nome cita solo anni passati). Un bando già studiato o richiesto da un cliente non si cancella mai in automatico. Nella libreria i bandi del catalogo mostrano ora «APERTO (fino al …)» o «CHIUSO (scaduto il …)» dalla scadenza ufficiale.")
    P("**Stadio 2 — estrazione deterministica  [[FATTO]].** Pattern e tassonomia collegata ai 60 criteri, nessun modello: ogni frase che tocca un tema noto diventa un requisito; ogni frase con obbligo o divieto fuori tassonomia finisce in «DA_REVISIONARE». Le regole numeriche estratte sono solo quelle riconosciute senza ambiguità (circa 24 chiavi note). Una regola pubblicata non viene mai sovrascritta da un'estrazione successiva: solo la revisione umana la corregge.")
    P("**Stadio 3 — più passaggi AI  [[PARZIALE]].** Implementato e testato: N estrazioni indipendenti (numero configurabile), ogni valore accettato solo se accompagnato dalla frase del documento da cui deriva e solo se quella frase compare davvero nel testo; il codice confronta i passaggi, concordanza → pubblicata, disaccordo → coda di revisione. **Non attivo in produzione** perché manca la chiave del provider.")
    P("**Coda di verifica umana  [[FATTO]].** `/ingestion/review-queue` e `/ingestion/review` (il consulente risolve un disaccordo e la regola viene pubblicata); il Quartier Generale permette di impostare, correggere o eliminare ogni regola e requisito, rileggere i documenti, esportare uno ZIP o eliminare il bando.")
    P("**Audit di calibrazione continua e canale reattivo  [[DA FARE]].** Il campionamento casuale di regole già pubblicate e l'evento `rule.audit_flagged` non esistono ancora; il canale verso il Reparto di Consulenza è Fase 4.")
    P("**Embedding e indicizzazione vettoriale  [[DA FARE]].** La v2.1 prevedeva chunking e vettori per la consultazione libera. Oggi la lettura è lessicale e strutturata: la rilevanza di un documento si decide da parole distintive del nome e dall'ente (con un elenco di parole generiche escluse), il che spiega un limite noto: un bando «fratello» dello stesso ente può contaminare lo studio di un altro (vedi Modulo 27).")

    H3("9.2 Fonte B — tabelle di mercato e benchmark ufficiali  [[PARZIALE]]")
    P("**Nessun valore è scritto nel codice.** Le tabelle stanno nel database (`fonte_b_datasets`, `fonte_b_ccnl`, `fonte_b_params`, `fonte_b_amort`, `fonte_b_benchmarks`), arrivano da un file con la loro provenienza (documento, indirizzo, impronta del file, riferimento), nascono come **bozza** e un manager le **pubblica** attestando la fonte; "
      "ogni insieme ha un periodo di validità e una versione nuova non sovrascrive la precedente. Il motore lavora su una fotografia presa una sola volta, con una «data di riferimento» esplicita: lo stesso budget ricalcolato con la stessa data dà sempre la stessa impronta. Quando una tabella manca il motore lo dice e la riga non viene calcolata: non esistono valori «standard».")
    T([["Tabella", "Pubblicata oggi", "Fonte dichiarata"],
       ["CCNL COMMERCIO", "8 livelli (1-7 e Quadro)", "Art. 211 del CCNL Terziario Confcommercio: quota oraria con divisore 168 per 40 ore/settimana"],
       ["CCNL METALMECCANICA", "9 livelli (A1-D2)", "Art. 5 (divisore orario 173) e Art. 1 (classificazione 2021) del CCNL Metalmeccanici"],
       ["CCNL TERZO_SETTORE", "13 livelli (A1-F2)", "Art. 51 (orario 38 ore, divisore 165) e Art. 47 (inquadramento) del CCNL di riferimento"],
       ["PARAMS NAZIONALE", "2 parametri", "L. 92/2012 art. 2 c. 28 (1,4% sui contratti non a tempo indeterminato, +0,5 punti per ogni rinnovo); limite di reddito dei collaboratori occasionali"],
       ["AMORTIZATION", "5 categorie", "D.M. 31/12/1988: **fonte secondaria** (compilazione da un sito di agevolazioni, PDF ufficiale non leggibile come testo); solo le 5 categorie generiche"],
       ["BENCHMARK", "0", "Nessun benchmark di prezzo o di tariffa giornaliera: i criteri 22 e 33 restano «non valutati»"]], [36, 36, 98])
    P("Non esistono i connettori automatici (Ministero del Lavoro, ISTAT, portali di categoria) previsti dalla v2.1: l'aggiornamento è un caricamento manuale di file. [[DA FARE]]. Il CCNL del credito e altri contratti non sono presenti.")

    H3("9.3 Fonte C — dati contabili del cliente  [[FATTO]]")
    T([["Tipo documento", "Lettura", "Campi letti"],
       ["Busta paga", "Testo del PDF o OCR", "Nome e codice fiscale (subito sostituiti da token), CCNL, livello, periodo, totale competenze, netto, quota TFR, mensilità; **RAL stimata** = competenze × mensilità, sempre in revisione (la RAL non è sul cedolino)."],
       ["Bilancio", "Testo del PDF o OCR", "Esercizio (anche «al 31/12/2025»), ricavi, utile o perdita, totale costi della produzione, dipendenti medi; **ogni riga di costo** del conto economico con categoria assegnata da parole chiave. Le sottovoci che sommano il sottototale non si contano due volte; l'attivo e il passivo si ignorano se esiste la sezione dei costi."],
       ["Modello F24", "Testo del PDF o OCR", "Righe di codice tributo, periodo (rateazione o mese), anno e importo a debito."],
       ["Bozza di candidatura", "Testo del PDF o OCR", "Righe del «piano dei costi» / «quadro economico» e simili, nella sezione riconosciuta; il personale non diventa una voce unica (vedi 9.4)."],
       ["Visura camerale", "Testo del PDF o OCR", "Denominazione, partita IVA, forma giuridica, codice ATECO, provincia della sede, anno di costituzione, numero di addetti."],
       ["Altro documento", "Non letto", "Archiviato cifrato in qualunque formato (PDF, Excel…): DURC, dichiarazione de minimis, business plan, contratti."]], [30, 28, 112])
    B(["**Confidenza per campo.** Il testo di un PDF vale 1,0; per l'OCR vale la confidenza del motore; la confidenza della riga si propaga al campo. Soglia di accettazione: 0,90 (variabile `QUANTO_FIELD_CONFIDENCE_MIN`). Sotto soglia il campo è «da verificare» e **non entra nei calcoli** finché una persona non lo conferma («È giusto») o lo corregge.",
       "**Principio fail-safe:** un campo ambiguo (stessa etichetta con valori diversi nel documento) scende a 0,55; una riga senza categoria riconoscibile (nessuna o più categorie in conflitto) resta «da assegnare» a una persona.",
       "**Cifratura a riposo:** AES-256-GCM con chiave `QUANTO_FILE_KEY`; senza la chiave nessun file si carica. Nome del file e impronta SHA-256 restano in chiaro, il contenuto no.",
       "**Pseudonimizzazione:** nomi, codici fiscali e IBAN diventano token (HMAC-SHA256 con chiave segreta, non un hash semplice: gli spazi di ricerca di codici fiscali e IBAN sono enumerabili). Anche la riga d'origine mostrata come prova è ripulita.",
       "**OCR:** interfaccia unica `OcrEngine`; il motore open source Tesseract serve sul server e **non gira su Vercel**: in produzione le scansioni vengono rifiutate con un messaggio chiaro, non si inventa mai un testo. Un adattatore cloud è da fare. [[PARZIALE]]",
       "**Proprietà:** ogni documento appartiene all'utente che lo ha caricato; nessun altro lo vede. Il nome del file viene ripulito da percorsi e caratteri di controllo; i file vuoti si rifiutano.",
       "**Aprire e scaricare tutto ciò che l'azienda ha allegato  [[FATTO]]:** nell'elenco «I tuoi documenti» ogni file ha «Apri» (anteprima nella pagina per PDF, immagini e testo semplice; i fogli Excel e simili si scaricano), «Scarica» (file originale, decifrato solo per il proprietario, con il nome originale anche se contiene accenti) ed «Elimina» (con conferma). "
       "«Scarica tutti i file (ZIP)» crea nel browser un archivio con tutti i file divisi per tipo (Visura camerale, Bilancio, Busta paga…) e un `elenco_documenti.csv` con tipo, stato, data, dimensione e impronta SHA-256 di ciascuno. L'archivio si compone nel browser perché Vercel limita a 4,5 MB la risposta di una singola chiamata; i file tornano identici agli originali (verificato byte per byte)."])

    H3("9.4 Il profilo aziendale  [[FATTO]]  (nuovo)")
    P("Il profilo è il ponte tra le due missioni: i dati veri dell'impresa, raccolti una sola volta, usati ovunque. Due tabelle (`company_profiles`, una riga per utente; `company_financials`, una per utente ed esercizio), entrambe con la **provenienza di ogni valore**.")
    T([["Origine", "Significato", "Regola"],
       ["DOCUMENT", "Letto da un documento (con il suo numero)", "Entra solo se letto con sicurezza o confermato. Se il documento viene eliminato, il valore decade alla successiva sincronizzazione."],
       ["MANUAL", "Scritto dall'utente", "**Non viene mai sovrascritto** da una nuova lettura dei documenti."],
       ["DERIVED", "Ricavato (es. regione dalla provincia della sede)", "Si ricalcola se la sorgente cambia; non scavalca un valore manuale."]], [26, 56, 88])
    B(["**Dati dell'impresa:** ragione sociale, partita IVA (11 cifre), forma giuridica, codice ATECO (62.01 o 62.01.00), regione e provincia della sede, anno di costituzione, dipendenti, e se l'impresa è una start-up innovativa iscritta al registro (l'unica risposta che nessun documento può dare).",
       "**Dati per esercizio:** ricavi, utile (perdita), totale costi della produzione, dipendenti medi e i costi nelle cinque categorie (personale, beni strumentali, consulenze, spese generali, formazione). Se alcune righe del bilancio sono ancora da verificare, l'esercizio è segnalato come parziale.",
       "**Completezza (0-100%):** quota dei campi richiesti dell'impresa più gli importi obbligatori dell'ultimo esercizio. Richiesti: ragione sociale, partita IVA, forma giuridica, ATECO, regione, dipendenti, risposta sulla start-up; ricavi e le cinque categorie di costo.",
       "**Classe dimensionale UE** (raccomandazione 2003/361/CE, indicativa): microimpresa sotto 10 addetti e 2 M€; piccola sotto 50 e 10 M€; media sotto 250 e 50 M€; altrimenti grande; «provvisoria» se manca il fatturato; senza il totale di bilancio né le imprese collegate.",
       "**Procedura guidata (nel Profilo):** barra di avanzamento a segmenti e un passo alla volta: 1) carica tutti i documenti insieme (il tipo si propone dal nome del file e si può correggere; ogni file mostra «letto · N campi» o «archiviato»), 2) visura, 3) bilancio dell'ultimo esercizio, 4) bilanci precedenti (facoltativo), 5) due domande (la start-up e gli eventuali dati mancanti), 6) controllo delle righe incerte, 7) altri documenti (facoltativo), 8) profilo completo con il pulsante verso l'Allocazione. Parte dal primo passo obbligatorio non ancora fatto.",
       "**Sincronizzazione:** ogni caricamento, conferma o eliminazione di un documento rilancia `POST /profile/sync`."])
    P("**Stima dell'anno successivo.** Parte dall'ultimo esercizio ≤ anno−1: spesa = base × (1 + variazione)^(anni di proiezione). **La variazione non ha un valore predefinito**: la sceglie l'utente; dalle sue due ultime annate si ricava solo un suggerimento («+19,0%», «+29,6%») che l'utente applica con un clic. Variazioni non plausibili (sotto −95% o sopra +500%) e categorie sconosciute sono errori. Se l'ultimo bilancio è di due anni prima, la stima avvisa che proietta più anni.")
    P("**Abbinamento ai bandi (`/profile/match`).** Per ogni bando con regole o requisiti letti: controlli con esito OK / NON OK / DA VERIFICARE (apertura, categorie ammesse, ATECO, territorio, start-up, tipologia di soggetto), contributo stimato **solo se il bando dichiara un'aliquota**, e le riduzioni imposte dai tetti. "
      "Esempio con le cifre vere dell'azienda di prova: per «Investimenti Sostenibili 4.0» (aliquota 75%, solo beni strumentali) i 112.700 € di beni strumentali del 2025 danno un contributo stimato di 84.525 € (6,1% delle spese totali). "
      "Formula dei tetti: se una categoria supera la sua quota massima c del totale ammissibile, l'importo ammissibile è c × (altre spese ammesse) / (1 − c); con consulenze 40.000 €, altre spese 224.200 € e tetto del 10%, ne sono ammissibili 24.911 €.")
    P("**Quando non c'è un'aliquota.** Garanzia pubblica, finanziamento a tasso zero, contributo in conto interessi, iperammortamento (beneficio fiscale): il beneficio non è una percentuale delle spese del bilancio, dipende da altri dati (prestito richiesto, durata, imposte pagate). La scheda lo dice con la spiegazione specifica del tipo e **non scrive alcun importo**.")
    P("**Bozza di budget per un bando (`/profile/template`).** Parte dalle righe dell'ultimo bilancio, tiene le categorie che il bando ammette, applica la quota di progetto scelta dall'utente (da 1 a 100%), riduce le voci sopra i tetti. Punti di onestà: il **personale non diventa una voce** (il motore pretende persona per persona livello, CCNL, RAL e quota di tempo) ma viene indicato come importo da completare; le voci di ammortamento sono segnalate come costo di beni già acquistati; "
      "se il bando richiede il CUP (criterio 50) o le milestone (criterio 57) lo si dice, perché finché mancano la voce resta «in attesa». Le voci TPL-* si sostituiscono a ogni rigenerazione, il resto del budget non si tocca.")

    H2("MODULO 10 — L'algoritmo deterministico: dal dato grezzo alla riga validata  [[FATTO]]")
    P("Walkthrough illustrativo (cifre dell'esempio della v2.1; non è un caso reale): un Project Manager Junior al 50% su un progetto, livello 3 del CCNL Terzo settore, RAL dichiarata 38.000 €.")
    T([["Passo", "Cosa fa il motore", "Dove prende il dato"],
       ["1", "Riceve ruolo, livello, quota FTE (0,5), durata (12 mesi) e RAL dichiarata.", "Utente / busta paga (Fonte C)"],
       ["2", "Confronta la RAL dichiarata con quella della busta paga (tolleranza `payroll_tolerance_pct`, default 1%): se diverge, la voce è sospesa.", "Fonte C"],
       ["3", "Cerca ore lavorabili annue, oneri e TFR del livello nella tabella del contratto.", "Fonte B (CCNL pubblicato alla data di riferimento); se manca la voce non si calcola"],
       ["4", "Costo orario = (RAL + oneri + TFR) / ore lavorabili effettive, in Decimal.", "Motore"],
       ["5", "Confronta con il tetto orario del bando; sopra, decurta fino al tetto.", "Fonte A (`max_hourly_rate_personnel`)"],
       ["6", "Applica quota FTE e durata; verifica che la somma su più progetti non superi il 100%.", "Motore"],
       ["7", "Controlli incrociati dei criteri 1-15 (inquadramento, superminimi, straordinari, tempo determinato, occasionali…).", "Fonti A, B, C"],
       ["8", "Esito: validata, decurtata, respinta o in attesa; hash SHA-256 canonico della riga = foglia dell'albero di Merkle.", "Motore"],
       ["9", "Solo ora un testo spiega il risultato; le cifre del testo sono iniettate dal motore e ricontrollate.", "Renderer"]], [12, 100, 58])
    NOTE("Tutte le grandezze monetarie usano decimal.Decimal; le rettifiche riducono l'importo ammesso senza mai aumentarlo (0 ≤ approvato ≤ originale).")

    H2("MODULO 11 — I 60 criteri del Deterministic Engine  [[FATTO]]")
    P("Implementati tutti e 60, ciascuno come funzione autonoma e testabile isolatamente (55 test dedicati nel file dei criteri, più i test del motore). Regola di fondo: un criterio si esegue solo se esiste il dato sulla riga e, dove serve, la regola nel bando; altrimenti è **«non valutato» e non conta come superato**. "
      "Sulla pagina Bandi ogni bando mostra quanti criteri attiva davvero («5/60 attivati dal bando»): gli altri girano solo sui dati inseriti o restano spenti.")
    P("Tre stati di copertura per bando: REGOLA_DEL_BANDO (attivato da una regola pubblicata), SOLO_DATI (eseguibile sui soli dati della riga) e NON_ATTIVO (serve una regola che il bando non dice). Cinque criteri valgono sull'intero budget e non sulla singola riga: 48, 49, 55, 56, 60. "
      "Il criterio 60 verifica la coerenza globale: nessun importo ammesso supera l'originale e ammesso + rettifiche = richiesto.")
    blocks = [("Criteri 1-15 — Costo del personale e tetto lavoratori (CCNL)", range(1, 16)), ("Criteri 16-30 — Beni strumentali, ammortamenti e requisiti 4.0/5.0", range(16, 31)),
              ("Criteri 31-45 — Consulenze esterne, subappalti e spese generali", range(31, 46)), ("Criteri 46-60 — Coerenza temporale, congruenza dei prezzi e cumulabilità", range(46, 61))]
    for title, rng in blocks:
        H3(title)
        T([["N.", "Criterio"]] + [[str(n), m.CRITERIA_TITLES[n]] for n in rng], [12, 158])

    H2("MODULO 12 — L'algoritmo di allocazione annuale  [[FATTO]]")
    H3("12.1 Obiettivo e formulazione")
    P("«Quale combinazione di fonti minimizza la spesa a carico dell'ente rispettando cumulabilità, tetti e scadenze?» È un programma lineare misto-intero risolto con HiGHS (`scipy.optimize.milp`). Variabili: x_pj ∈ [0, copertura massima] quota della (sotto)voce p coperta dal fondo j; z_pj binaria di utilizzo. Vincoli:")
    B(["Σ_j x_pj ≤ 1 — una voce non è coperta oltre il 100%;", "Σ_p a_p·x_pj ≤ dotazione_j — tetto del fondo;", "Σ_(p∈c) a_p·x_pj ≤ quota_cj · Σ_p a_p·x_pj — massimali per categoria (criteri 31 e 36);",
       "z_pj + z_pk ≤ 1 per i fondi non cumulabili (criterio 47, double funding);", "Σ_(p, j∈de minimis) a_p·x_pj ≤ plafond residuo (criterio 49); l'importo è obbligatorio se uno dei fondi scelti è in de minimis;", "finestre di attività mensili dei fondi (criterio 46)."])
    P("Il solver lavora in euro (float) solo per trovare la struttura ottima; gli importi finali sono interi in centesimi, arrotondati per difetto e **ri-verificati in aritmetica esatta** contro tutti i vincoli, con riparazione deterministica dei residui. Le spese senza mese sono espanse in 12 mensilità solo se un fondo ha una finestra ridotta. "
      "Obiettivi: minimizzare la spesa netta (default), massimizzare le voci coperte, minimizzare i fondi coinvolti (con un parametro di risparmio minimo).")
    H3("12.2 Da dove vengono spese e fondi (cambiato rispetto alla v2.1)")
    B(["**Spese:** una sola origine per richiesta — un bilancio caricato (righe sicure o confermate; se ci sono righe da verificare la richiesta fallisce con l'elenco), spese fornite dal chiamante, oppure **il profilo aziendale** (`use_profile_forecast`: spese per categoria dell'ultimo esercizio, proiettate con le variazioni `growth_pct` scelte dall'utente, voci «STIMA-<CATEGORIA>»).",
       "**Fondi:** non sono nel codice. Una linea si ricava dalle regole **pubblicate** di un bando (categorie ammesse, intensità del contributo, finestra di ammissibilità, fondi non cumulabili, tetti di consulenze e spese generali); ciò che il bando non dice (dotazione massima, regime de minimis) non si inventa: lo indica una persona o resta vuoto. Nella pagina, spuntando i bandi nel passo 3 la linea di ciascuno viene passata al solver."])
    H3("12.3 Flusso operativo (pagina Allocazione)")
    T([["Passo", "Cosa succede", "Chiamata"],
       ["1", "Riepilogo del profilo: completezza, ultimo bilancio, dimensione, documenti, cosa manca; rimando al Profilo.", "GET /profile"],
       ["2", "Anno da pianificare (default anno corrente + 1); tabella con base, variazione suggerita, variazione scelta, stima; avvisi sulla proiezione e sulle categorie senza dato.", "POST /profile/match"],
       ["3", "Quattro schede: Adatto, Da verificare, Non adatto, Da studiare. Ogni bando mostra contributo, aliquota, quota sul totale, riduzioni per i tetti, controlli e note (CUP, DNSH, beni nuovi, vincolo di destinazione). «Bozza di budget per questo bando» apre il Budget con la bozza.", "POST /profile/match"],
       ["4", "Obiettivo, de minimis residuo (se serve) e piano: costi, copertura, quota coperta, Sankey spesa → fondo, piano voce per voce, uso dei fondi con margine di sicurezza, mese per mese. Si ricalcola a ogni scelta (risposte fuori ordine scartate).", "POST /allocation/optimize"]], [14, 126, 30])
    P("Dopo «Studia questo bando» su una voce del catalogo, la pagina ricalcola, porta l'utente alla scheda dove il bando è finito (adatto, da verificare o non adatto) e mostra com'è andata la lettura (completa/parziale, documenti, requisiti, cifre, regole) e se c'è una stima in euro.")

    H2("MODULO 13 — Dove interviene l'AI e dove il dato proprietario")
    T([["Funzione", "Motore proprietario (codice)", "Modello linguistico", "Stato"],
       ["Estrazione dati da buste paga, bilanci, visure", "Sì — parser e lettore (testo del PDF o OCR)", "Mai", "[[FATTO]]"],
       ["Costo orario, ammortamenti, oneri, i 60 criteri", "Sì — formule e regole codificate", "Mai", "[[FATTO]]"],
       ["Allocazione multi-fonte", "Sì — MILP con verifica esatta", "Mai", "[[FATTO]]"],
       ["Stima dell'anno, abbinamento ai bandi, bozza di budget", "Sì — aritmetica e regole", "Mai", "[[FATTO]]"],
       ["Pattern matching", "Sì — k-means e coseno", "Mai", "[[FATTO]]"],
       ["Ricerca e catalogazione dei bandi (Stadio 1)", "Sì — mappe dei siti, schede ufficiali, estrazione di campi dalla pagina", "No: oggi non serve un modello", "[[FATTO]]"],
       ["Ricerca del documento giusto di un bando", "Orchestrazione e filtri", "Nessuno: motore di ricerca Brave (indirizzi, non interpretazione)", "[[FATTO]]"],
       ["Conferma del bando e cache", "Sì", "Cliente conferma", "[[FATTO]]"],
       ["Regole da tabelle e prosa standard (Stadio 2)", "Sì — pattern deterministici", "Mai", "[[FATTO]]"],
       ["Regole dal residuo in prosa libera (Stadio 3)", "Sì — confronto dei passaggi", "N estrazioni indipendenti con frase di prova", "[[PARZIALE]] spento"],
       ["Audit di calibrazione", "Selezione del campione", "No — revisore umano", "[[DA FARE]]"],
       ["Frase di riepilogo del calcolo", "Template fisso con cifre iniettate + validatore", "Opzionale, vincolato ai numeri forniti", "[[PARZIALE]] solo template"],
       ["Scrittura della candidatura", "No", "No — fuori scopo", "—"]], [54, 52, 44, 20])
    P("L'unica eccezione dichiarata al principio resta lo Stadio 3, perché interpreta testo normativo; porta con sé il confronto dei passaggi, la frase di prova obbligatoria e la coda di revisione.")

    H2("MODULO 14 — Le metriche di accuratezza")
    T([["Metrica", "Cosa misura", "Stato"],
       ["14.1 Conformity Score", f"Percentuale di criteri rispettati da un budget; il motore è provato da {FACTS['tests']} test automatici (inclusi 55 sui singoli criteri e 14 sul motore) su casi con esito noto. Claim ammesso: «il motore applica correttamente il 100% delle regole testate sul set di validazione attuale».", "[[FATTO]]"],
       ["14.2 Pattern Similarity Score", "Distanza dagli archetipi dei budget storici; con i dati attuali ha valore indicativo (5 budget).", "[[PARZIALE]]"],
       ["14.3 Successo e clawback reali", "Richiede pratiche presentate e controlli ex post. Non compare in alcun materiale commerciale.", "non misurabile oggi"],
       ["Nuova: completezza della lettura", "Per ogni bando studiato: COMPLETA / PARZIALE / INSUFFICIENTE, con motivi. È una misura di copertura della lettura, non di correttezza delle regole.", "[[FATTO]]"],
       ["Nuova: confidenza dei campi", "Ogni campo di un documento del cliente porta la sua confidenza; sotto 0,90 non entra nei calcoli.", "[[FATTO]]"]], [40, 100, 30])

    H2("MODULO 15 — Stack tecnologico e infrastruttura  [[FATTO]]")
    T([["Livello", "Scelta reale"],
       ["Backend", "Python 3.12 (produzione e CI), FastAPI, Pydantic v2, uvicorn; calcolo in decimal.Decimal; risolutore HiGHS via SciPy; NumPy; pdfplumber e pypdf per i PDF; reportlab per i PDF generati; openpyxl per Excel; qrcode; cryptography (AES-GCM, Ed25519); httpx"],
       ["Database", "PostgreSQL gestito (Supabase) con psycopg e un pool di connessioni; 11 migrazioni versionate; trigger che rendono append-only il registro; Row Level Security attiva su tutte le tabelle; in test un PostgreSQL vero incorporato"],
       ["Frontend", "React 18.3, Vite 7.3, Tailwind 3.4, Lucide; nessuna libreria di grafici (Sankey e istogrammi sono SVG propri)"],
       ["Hosting", "Vercel: funzione Python (durata massima 60 secondi) nella regione di Francoforte, sito statico, due cron giornalieri (03:00 e 03:30); il database e i file cifrati stanno nel database"],
       ["CI/CD", "GitHub Actions con azioni fissate per impronta del commit, permessi minimi, ubuntu-24.04: test backend su PostgreSQL 16, build del frontend, controllo delle dipendenze che finiscono in produzione (pip-audit, npm audit senza dipendenze di sviluppo); Dependabot per le dipendenze, ignorando gli aggiornamenti di versione maggiore del frontend; ogni push su main ridistribuisce"],
       ["Dati regionali", "Funzioni a Francoforte. La regione del database Supabase va confermata nel pannello del fornitore prima di dichiarare la residenza UE ai clienti. [[DA FARE]]"]], [26, 144])
    H3("15.4 Manutenzione delle Fonti A")
    B(["Catalogazione: due cron notturni, costo trascurabile, nessun rischio sui numeri.", "Estrazione: su richiesta; il costo di un bando richiesto da dieci clienti si paga una volta.", "Parser: uno per ogni formato riconosciuto; i formati nuovi arricchiscono la libreria.",
       "Verifica umana residua: solo per disaccordi (Stadio 3, spento) e per le regole numeriche lasciate in revisione dal filtro delle fonti (esempi: misure locali di camere di commercio).", "Audit di calibrazione: da realizzare."])

    H2("MODULO 16 — Sicurezza, privacy e conformità GDPR")
    H3("16.1 Misure realizzate  [[FATTO]]")
    T([["Area", "Misura"],
       ["Dati dei clienti", "AES-256-GCM a riposo (chiave a 32 byte); token HMAC per nomi, codici fiscali e IBAN; ricomposizione solo per l'utente proprietario; ogni documento è visibile solo a chi lo ha caricato"],
       ["Password e accessi", "scrypt con sale casuale; 5 errori di fila bloccano l'account per 15 minuti (il blocco sta nel database, vale su tutte le istanze); un utente inesistente costa lo stesso tempo e dà lo stesso messaggio; token JWT HS256 di 8 ore con versione: cambiare password o disattivare l'utente lo invalida subito"],
       ["Ruoli", "USER e MANAGER; il Quartier Generale è riservato al titolare (`QUANTO_OWNER_EMAIL`), non a ogni manager"],
       ["Integrazione ERP", "OAuth 2.0 client-credentials (token di 1 ora) e firma HMAC-SHA256 della richiesta con timestamp (tolleranza 5 minuti) contro il replay"],
       ["Rete", "Intestazioni nosniff, X-Frame-Options DENY, Referrer-Policy, Permissions-Policy e Content-Security-Policy restrittiva (solo risorse dello stesso sito, fonti Google solo per i caratteri; cornici e oggetti solo se creati dall'app stessa come blob, per l'anteprima dei documenti); guardia SSRF nel recupero dei documenti; limite di frequenza; i webhook usano solo indirizzi dall'ambiente e corpo firmato"],
       ["Dati nel database", "Row Level Security attiva su tutte le tabelle; il registro firmato è protetto da trigger e non è cancellabile dal Quartier Generale"],
       ["Rilascio", "Nessuna chiave nel repository; azioni fissate per impronta; audit delle dipendenze in CI"]], [32, 138])
    H3("16.2 Pseudonimizzazione lato server")
    P("Come nella v2.1: la minimizzazione e la pseudonimizzazione sono lato server, in infrastruttura isolata. **Mancano** ancora l'accordo di trattamento dei dati (DPA), l'informativa e la valutazione d'impatto da formalizzare prima di clienti reali, e va dichiarata la residenza del database. [[DA FARE]]")

    # ================================================================================================ PARTE IV
    H1("PARTE IV — LA VISIONE A LUNGO TERMINE")
    H2("MODULO 17 — Il registro crittografico (CEP)  [[DECISIONE]]  [[FATTO]]")
    P("La v2.1 lo collocava in Fase 2. È stato anticipato perché senza di esso la verifica era solo dichiarata; è stato realizzato in forma diversa dalla prima ipotesi: **nessuna blockchain** (decisione del titolare del 19/09/2026, mai da reintrodurre salvo richiesta).")
    B(["**Albero di Merkle** con le due difese standard (RFC 6962 / CVE-2012-2459): foglie = SHA-256(0x00 ‖ hash riga), nodi = SHA-256(0x01 ‖ min ‖ max), nodo dispari promosso invariato (non duplicato), così [a,b,c] e [a,b,c,c] danno radici diverse.",
       "**Hash per riga** canonico SHA-256; la Merkle Root del budget e il CEP-ID (es. CEP-523933E0C00D062F) derivano dalle righe e dalla versione delle regole (`rule_version_hash`, hash del contenuto delle regole pubblicate).",
       "**Registro:** catena di hash append-only, ogni voce lega (progetto opaco, Merkle Root, istante) all'hash della precedente ed è firmata Ed25519; il trigger del database vieta modifiche e cancellazioni. La chiave **pubblica** (`/registry/public-key`) è la radice di fiducia e va fissata dall'auditor fuori banda; un'attestazione firmata si verifica offline con la sola chiave pubblica.",
       "**Dual-Layer Output:** Layer 1 = PDF/XLSX con CEP-ID e QR; Layer 2 = Auditor Portal (pagina Verifica): verifica dell'impronta presentata, ricalcolo dai dati originali, simulazione di manomissione (+1 € sulla prima riga → «impronta diversa»).",
       "**Limite dichiarato:** il registro è gestito da QUANTO, non da un testimone terzo. Per rafforzarlo si può pubblicare periodicamente `head_hash` (PEC, repository pubblico, marca temporale qualificata). [[DA FARE]]",
       "**Non realizzato:** il «Report di Asseverazione Crittografica» in PDF come documento a sé. Esiste l'attestazione firmata in JSON e la pagina di verifica. [[DA FARE]]"])
    P("Stato online: una registrazione di prova (n. 1, 4 ottobre 2026), catena integra, chiave 4e5773cd74cfe97d.")
    H2("MODULO 18 — La componente assicurativa  [[FASE 3]]")
    P("Invariato: richiede storico di pratiche reali, struttura regolamentare adeguata (licenza IVASS o partner MGA) e validazione attuariale indipendente; esclusioni esplicite; rischio sistemico da mitigare con limiti di esposizione per regola. Nessuna riga di codice, per scelta.")
    H2("MODULO 19 — Il reparto di consulenza  [[FASE 4]]")
    P("Invariato: rete di consulenti partner, segnalazione dei casi limite, canale reattivo sulle regole. Precursore reale già presente: la **scheda per il consulente** nel Quartier Generale (per ogni bando: cosa dicono i documenti, cosa non dicono, quali parole cercare, dove compaiono, come verificare, quale controllo resta spento).")

    # ================================================================================================ PARTE V
    H1("PARTE V — GO-TO-MARKET")
    H2("MODULO 20 — Target e segmentazione  [[DA FARE]]")
    P("Invariato: commercialisti e studi strutturati come canale moltiplicatore, CFO di PMI e associazioni per la Missione Due, bandifici come canale secondario. Una novità di prodotto cambia il racconto commerciale: la procedura guidata e il profilo rendono credibile anche l'uso diretto da parte di un'impresa senza intermediari.")
    H2("MODULO 21 — Canali e pricing  [[DA FARE]]")
    P("Vendita guidata dalla demo: la demo reale ora esiste (Modulo 4) e può essere mostrata su dati del prospect caricati dal vivo. Pricing a tre livelli (abbonamento, crediti, success fee) più la commissione di Fase 4: **non implementato**. Esiste solo l'anteprima: ogni utente ha un «piano gratuito — anteprima di un piano annuale» con 100 crediti per ciclo e un credito per controllo del budget, con rinnovo dopo 364 giorni; i pagamenti sono simulati, nessun conto è addebitato. "
      "La registrazione è libera (account USER gratuito, nessuna e-mail di conferma): va chiusa o protetta prima di un lancio.")
    H2("MODULO 22 — Competizione e barriere all'entrata")
    P("Invariato nelle conclusioni. Barriere che il codice ha già iniziato a costruire: la libreria di parser e di tassonomia dei requisiti, i bandi studiati con tutte le fonti originali conservate, il profilo e i documenti dei clienti, il registro firmato. La strategia di partnership con gli ERP resta un'opzione da valutare con dati di mercato.")
    story.append(PageBreak())

    # ================================================================================================ PARTE VI
    H1("PARTE VI — IL SISTEMA COM'È OGGI")
    H2("MODULO 23 — Il Quartier Generale  [[FATTO]]")
    P("Area riservata al titolare dell'account (si apre dal Profilo; nessun altro utente la vede). È «la memoria del sistema»: ogni dato della piattaforma ha una vista, tranne i contenuti riservati dei clienti, di cui si vedono solo i contatori.")
    T([["Sezione", "Cosa mostra e cosa permette"],
       ["Panoramica", "Budget controllati, progetti, bandi, documenti, eventi, registrazioni; stato della memoria (PostgreSQL, dimensione) e della sicurezza (utenti, manager, chiave di firma); attività recente; ultimi eventi."],
       ["Timeline", "Ogni operazione in ordine di tempo, filtrabile per operazione, progetto, bando, esito; dal dettaglio si rivede nell'Algoritmo l'esecuzione salvata."],
       ["Mappa operazioni", "Tutte le operazioni fattibili con le fasi interne e le statistiche (numero, durata)."],
       ["Bandi", "Ogni bando in memoria: documenti con testo e file originale, regole (anche in disaccordo, modificabili), requisiti (riclassificabili), scheda per il consulente, linea di finanziamento, utilizzi; rilettura, esportazione ZIP, eliminazione (con lapide per i curati e ripristino dei predefiniti)."],
       ["Catalogo (nuova)", "Tutte le voci del catalogo con descrizione e caratteristiche, ricerca e filtro (con scheda letta / da leggere), contatori (voci, schede lette, da leggere, con scadenza futura, già studiate) e pulsante che legge in sequenza tutte le schede mancanti."],
       ["Tabelle ufficiali", "Fonte B: caricamento da file, bozze, pubblicazione con attestazione della fonte, versioni; modelli di file per tipo."],
       ["Banca pattern", "Importazione CSV con fonte obbligatoria, budget in banca e archetipi."],
       ["Utenti", "Creazione utenti, cambio ruolo, attivazione, reimpostazione password, sblocco."],
       ["Fascicoli", "Cartella di ogni progetto: validazioni, documenti, cronologia, registrazione."],
       ["Documenti", "Bandi caricati, importazioni, esportazioni (con impronta e dimensione)."],
       ["Database", "Tutte le tabelle in sola lettura, righe paginate, esportazione CSV, eliminazione di righe o svuotamento con conferma digitata (il registro firmato è escluso). Comprende anche i profili e i bilanci delle aziende."]], [30, 140])

    H2("MODULO 24 — Dati e database  [[FATTO]]")
    T([["Tabella", "Contenuto"],
       ["bandi", "Una riga per bando o voce del catalogo: identificativo, nome ufficiale, ente, scadenza, indirizzo della scheda, stato del catalogo, stato dell'estrazione, richieste dei clienti, descrizione, caratteristiche (JSON) e data di lettura della scheda"],
       ["bando_meta · rules · requirements", "Descrizione curata dei bandi predefiniti; regole numeriche con origine e stato (pubblicata, in revisione); requisiti con tema, tipo, controlli collegati, cifre strutturate"],
       ["bando_sources · bando_files · bando_tombstones", "Testo e metadati di ogni documento di fonte; file originali; lapidi dei bandi eliminati"],
       ["fonte_b_datasets · _ccnl · _params · _amort · _benchmarks", "Fonte B versionata per data, con provenienza"],
       ["client_documents · client_document_fields", "Documenti dei clienti cifrati e relativi campi con confidenza, stato, token, riga di prova"],
       ["company_profiles · company_financials", "Profilo e bilanci per esercizio, con provenienza di ogni valore"],
       ["funding_lines", "Linee di finanziamento per l'allocazione, ricavate dai bandi o indicate da una persona"],
       ["pattern_budgets · pattern_archetypes", "Banca dei pattern e archetipi calcolati"],
       ["users", "Account con hash scrypt, ruolo, tentativi falliti, versione del token"],
       ["events · runs · documents", "Timeline, esecuzioni salvate con richiesta e risposta complete, documenti lavorati"],
       ["anchors", "Registro firmato append-only"]], [60, 110])
    P(f"Contenuto online il 4 ottobre 2026: {FACTS['bandi']} bandi, {FACTS['rules']} regole, {FACTS['requirements']} requisiti, {FACTS['sources']} fonti, {FACTS['files']} file originali, {FACTS['events']} eventi, {FACTS['runs']} esecuzioni, {FACTS['documents']} documenti lavorati, 1 utente (il titolare), 1 profilo con 3 esercizi, 14 documenti del cliente di prova, 1 registrazione. "
      "Alla v2.1 di partenza il database era in memoria volatile; oggi i dati sopravvivono al riavvio del server.")

    H2("MODULO 25 — Cosa fa l'app a ogni azione dell'utente  [[FATTO]]")
    T([["Azione", "Cosa succede, in ordine"],
       ["Registrarsi / accedere", "Crea l'account USER (scrypt) o verifica la password con tempo costante; emette un token di 8 ore con versione; nella timeline compare l'accesso."],
       ["Caricare un documento", "Controlli (tipo noto, non vuoto, massimo 15 MB, nome ripulito, PDF per i tipi letti) → cifratura AES-256-GCM → lettura del testo (o OCR se disponibile) → parser del tipo → ogni campo con confidenza e stato → dati personali in token → salvataggio → sincronizzazione del profilo."],
       ["Confermare o correggere un campo", "Il campo diventa confermato o corretto, entra nei calcoli, il profilo si ricalcola. Se una busta paga ha la RAL stimata, la conferma abilita la voce di personale."],
       ["Rispondere alla domanda sulla start-up", "Scrive un valore MANUAL nel profilo; la completezza sale; l'abbinamento ai bandi usa subito la risposta."],
       ["Calcolare la stima e cercare i bandi", "Legge il profilo, proietta le cinque categorie con le variazioni dell'utente, valuta uno per uno i bandi con regole o requisiti, ordina il catalogo non studiato per affinità; registra l'evento con i conteggi."],
       ["Studiare un bando", "Processo standard (Modulo 9.1); al termine ricalcola l'abbinamento e porta alla scheda del bando con il rapporto di lettura."],
       ["Creare la bozza di budget", "Legge l'ultimo esercizio, filtra per categorie ammesse, scala per la quota, riduce ai tetti; il personale resta fuori con l'importo indicato; le voci TPL-* sostituiscono la bozza precedente."],
       ["Controllare il budget", "Le sole voci complete (il personale senza RAL è escluso e segnalato) vanno al motore: criteri per voce → criteri sul budget intero → hash → Merkle → riepilogo. Si salvano l'esecuzione, l'evento e un credito. Esito: punteggio, ammesso, escluso o ridotto, motivi."],
       ["Ripartire in WP", "Le voci ammesse (importi approvati) e i WP con i loro vincoli vanno al risolutore; controlli di fattibilità → MILP → centesimi → verifica esatta → report per WP, controlli e CSV. Spostando una voce a mano il calcolo riparte."],
       ["Aprire o scaricare un documento", "Il file viene decifrato dal server solo per il proprietario; PDF, immagini e testo si guardano in una finestra della pagina, gli altri si scaricano. «Scarica tutti» ripete l'operazione per ogni file e compone lo ZIP nel browser."],
       ["Esportare", "Excel o PDF con CEP-ID e QR verso la verifica."],
       ["Registrare l'impronta", "Aggiunge una voce firmata Ed25519 alla catena; il trigger impedisce di cambiarla."],
       ["Verificare", "Confronta l'impronta, controlla la firma e la catena; «ricalcola dai dati» rifà tutto da zero; la manomissione simulata deve dare «impronta diversa»."],
       ["Calcolare il piano", "Una richiesta con le spese stimate e le linee dei bandi spuntati; MILP; verifica esatta in centesimi; riepilogo con cifre controllate; evento e webhook."],
       ["Cambiare password", "Aggiorna l'hash e la versione del token: tutte le sessioni aperte decadono."]], [40, 130])

    H2("MODULO 26 — Esito del test demo del 4 ottobre 2026 e decisioni prese")
    P("Il sistema è stato provato come lo userebbe un'azienda vera, in produzione, con i 14 documenti dell'azienda fittizia Meridiana Digital Solutions S.r.l. (software, Torino, 17 addetti, ricavi 2025 di 1.583.200 €, tre bilanci 2023-2025 con schema civilistico, due buste paga, due F24, una bozza di candidatura, DURC, de minimis, business plan, due Excel). Funzioni provate: "
      "registrazione e accesso, procedura guidata, lettura di tutti i tipi di documento, verifica delle letture incerte, stima dell'anno, abbinamento ai bandi, studio di un bando del catalogo (con ricerca web reale), bozza di budget, controllo dei 60 criteri, esportazione Excel e PDF, algoritmo, registrazione, verifica e manomissione, confronto, guida, ricerca di un bando, tutte le 11 sezioni del Quartier Generale e una serie di richieste volutamente sbagliate.")
    H3("Cosa ha funzionato al primo colpo")
    B(["Lettura di tutti i 14 file: 92% di profilo con un solo gesto, 100% dopo la risposta alla domanda sulla start-up; costi per categoria che sommano il totale dei costi della produzione in tutti e tre gli anni.",
       "Stima 2027 (890.700 € di personale, 112.700 di beni, 172.500 di consulenze, 182.000 di spese generali, 18.400 di formazione), abbinamento con 12 bandi studiati e catalogo, studio in tempo reale di un bando dal catalogo.",
       "Esportazione Excel (8,5 KB) e PDF (21,8 KB), registrazione n. 1 firmata, verifica coincidente, manomissione rilevata, confronto con i budget storici.",
       "Tutte le richieste errate rifiutate con messaggio chiaro (partita IVA a 3 cifre, regione inesistente, campo sconosciuto, esercizio 1850, importo non numerico, variazione implausibile, scala 0 o 150, PDF finto, tipo sconosciuto, due origini di spesa insieme, copertura 150%)."])
    H3("Difetti trovati e corretti (con la causa)")
    T([["N.", "Difetto", "Causa", "Correzione"],
       ["1", "Dopo il caricamento dalla procedura guidata, l'elenco «I tuoi documenti» sotto restava a zero fino al ricaricamento della pagina.", "La procedura e l'elenco erano due componenti che non si parlavano.", "L'elenco si aggiorna quando la procedura cambia qualcosa (chiave di aggiornamento condivisa)."],
       ["2", "Nel browser dei bandi e nella ricerca per nome non comparivano le descrizioni appena create.", "Il campo era nei dati ma non nell'interfaccia.", "Descrizione mostrata in «Sfoglia tutti i bandi» e nei risultati della ricerca interna."],
       ["3", "I bandi del catalogo già studiati ma scaduti (es. 2023, marzo 2026) erano etichettati «IN LAVORAZIONE».", "Lo stato veniva solo dal campo generico.", "Stato dalla scadenza ufficiale: «CHIUSO (scaduto il …)» o «APERTO (fino al …)»."],
       ["4", "Nel Budget si potevano scegliere bandi senza regole (errore al clic).", "L'elenco mostrava tutti.", "Voci senza regole disattivate con l'indicazione «regole non ancora lette»."],
       ["5", "La bozza di budget metteva il personale come voce unica senza RAL: il controllo dava errore 422 e bloccava l'intero budget.", "Il motore vuole persona per persona livello, CCNL, RAL, quota di tempo.", "Il personale esce dalla bozza e dall'importazione di una candidatura con l'importo indicato e il motivo; nei tetti percentuali continua a contare."],
       ["6", "Messaggio d'errore illeggibile («cost_items.3: Value error, ral_eur obbligatoria…») e risultato vecchio accanto a voci cambiate.", "Messaggio tecnico mostrato così com'è; il risultato precedente non veniva cancellato.", "Messaggio in italiano con il nome della voce; una voce di personale senza RAL è esclusa dal controllo e segnalata con un avviso, il resto si controlla; il risultato obsoleto sparisce."],
       ["7", "Le voci di «ammortamento» del bilancio entravano nella bozza come se fossero acquisti.", "Sono il costo di beni già acquistati.", "Avviso nella bozza: sostituiscile con gli acquisti previsti. Aggiunti avvisi su CUP e milestone se il bando le richiede."],
       ["8", "Dopo «Studia questo bando» la pagina tornava alla scheda iniziale e il rapporto di lettura spariva.", "L'intero calcolo veniva rilanciato resettando la scelta.", "La pagina porta alla scheda dove il bando è finito e mostra il rapporto (completa/parziale, documenti, requisiti, cifre, regole, e se c'è una stima in euro)."],
       ["9", "Nomi dei bandi del catalogo generici (dall'indirizzo) e quindi studi con documenti poco pertinenti.", "Il nome era la versione accorciata dell'indirizzo.", "Si usa il titolo ufficiale della scheda (og:title); le voci già lette si rileggono (versione di lettura 2) e il nome si aggiorna."],
       ["10", "Classifica del catalogo piatta (molti 100%) e priva del settore.", "Il punteggio saturava a 1 e ignorava il settore.", "Punteggio rescalato (0,75 sulle spese + bonus), settore ricavato dall'ATECO, penalità per misure da «start-up» a imprese mature, a pari punteggio prima chi scade prima."],
       ["11", "Un file vuoto con nome `../../x.exe` veniva accettato come «altro documento».", "Mancavano due controlli.", "File vuoti rifiutati; nome ripulito da percorsi e caratteri di controllo. Il file di prova creato è stato eliminato."],
       ["12", "Una variazione per una categoria inesistente (es. BANANE) veniva ignorata in silenzio.", "La richiesta accettava qualsiasi chiave.", "Errore «Categoria sconosciuta»."],
       ["13", "La Guida non menzionava profilo, procedura guidata, catalogo, stima né bandi da studiare.", "Non era stata aggiornata.", "Percorso rapido con il nuovo primo passo, sezioni Allocazione, Profilo e Catalogo riscritte con esempi verificati."],
       ["14", "Il Confronto partiva con tutte le quote a 0 se il budget controllato era tutto «in attesa».", "Le quote derivano dagli importi ammessi, tutti zero.", "Nuovo pulsante «Usa i costi del mio profilo» che calcola le quote sull'ultimo bilancio."],
       ["15", "Il lavoro notturno avrebbe impiegato oltre un mese per leggere il catalogo.", "Lotti troppo piccoli.", "Lotti da 400 con 24 richieste in parallelo e un pulsante che li ripete fino a esaurimento: 5.409 schede in circa 4 minuti."],
       ["16", "Una frase di presentazione veniva tagliata dopo «n.» di «n. 59».", "Il taglio si faceva sul primo punto.", "Il taglio ignora le abbreviazioni (n., art., lett., D.M.…) e finisce a fine frase."],
       ["17", "Una misura «per gli enti del terzo settore» (IRAP, Regione Piemonte) veniva proposta come affine a una S.r.l.", "La classifica non guardava la tipologia di soggetto della scheda.", "Escluse le misure riservate a enti, persone fisiche, amministrazioni o imprese ancora da costituire. Scoperto dallo studio reale del bando durante il test, corretto subito."],
       ["18", "Dopo lo studio il messaggio diceva «non dichiara un'aliquota» anche per un bando risultato non adatto per altri motivi.", "Messaggio unico per due casi diversi.", "Messaggio distinto: per «Non adatto» rimanda ai Dettagli, per gli altri dice se c'è o no una stima in euro."]], [8, 56, 46, 60])
    H3("Limiti residui dichiarati (non sono errori nascosti)")
    B(["L'importo di «ammortamento» e «licenze software e servizi cloud» finisce tra i beni strumentali perché così lo classificano le parole chiave del bilancio; la persona lo vede e può riassegnarlo.",
       "La bozza di budget contiene voci che il motore mette «in attesa» (CUP e milestone mancanti): è corretto, ma significa che un budget costruito dal bilancio non diventa ammissibile finché non si aggiungono quei dati.",
       "Lo studio di un bando dal catalogo con nome generico può includere documenti di bandi «fratelli» dello stesso ente (rilevanza lessicale). Il titolo ufficiale riduce il problema, non lo elimina.",
       "Sul sito di produzione resta una registrazione di prova nel registro (n. 1) e un progetto «DEMO-SHAPE» nella timeline: sono tracce del test."])

    H2("MODULO 27 — Cosa manca per far funzionare QUANTO al 100%")
    H3("Dati e decisioni che servono dal titolare")
    T([["Cosa", "Perché serve", "Chi"],
       ["Chiave del provider del modello linguistico (e conferma del provider)", "Accende lo Stadio 3 (più passaggi) e il riepilogo scritto dal modello; oggi tutto è template.", "Titolare"],
       ["Dataset dei pattern vincenti (graduatorie pubbliche, dati del pilota con consenso)", "Oggi 5 bilanci di società quotate come proxy; servono almeno 6 budget per categoria per avere archetipi veri.", "Titolare / pilota"],
       ["Tabelle ufficiali: CCNL mancanti, benchmark di prezzo e di tariffa, aliquote d'ammortamento da fonte primaria", "Criteri 22 e 33 spenti; aliquote da fonte secondaria.", "Titolare con consulente"],
       ["Motore OCR per le scansioni (adattatore cloud)", "Tesseract non gira su Vercel: oggi le scansioni vengono rifiutate.", "Decisione di provider"],
       ["Regione del database e documenti legali (DPA, informativa, valutazione d'impatto)", "Condizione per clienti reali.", "Titolare / legale"],
       ["Decisione sulla registrazione libera e sul pagamento reale", "Oggi chiunque può iscriversi gratis; i crediti sono simulati.", "Titolare"]], [60, 80, 30])
    H3("Lavoro di sviluppo ancora aperto")
    B(["**Regole numeriche dai bandi:** oggi circa 24 chiavi note producono regole; gli altri tetti vivono come cifre nei requisiti di tipo LIMITE. Prossimo passo: mapparli su nuove chiavi del motore, con revisione.",
       "**Rilevanza dei documenti:** da lessicale a vettoriale o con controllo sull'ente, per evitare la contaminazione tra bandi dello stesso ente (Modulo 9.1).",
       "**Audit di calibrazione** e relativo evento `rule.audit_flagged`; **Report di Asseverazione** in PDF; pubblicazione periodica di `head_hash` del registro.",
       "**WP: vincoli letti dal bando.** La ripartizione c'è (Modulo 2.1) ma i limiti dei WP li scrive l'utente; leggerli dal testo del bando è possibile solo dove il bando li dichiara.",
       "**Bozza di budget per persona:** estrarre dall'organico (Excel) le persone con livello e quota di tempo per costruire le voci di personale.",
       "**Connettori automatici** per la Fonte B; **registri IVA e piano dei conti** come tipi di documento.",
       "**Integrazioni ERP** (Zucchetti, TeamSystem): l'API è pronta (OAuth 2.0 + HMAC), le integrazioni non esistono.",
       "**Test dei processi sul campo:** nessuna pratica reale è stata presentata; per questo non esiste alcuna metrica di successo o di clawback."])
    H3("Fasi della roadmap")
    T([["Fase", "Contenuto", "Stato"],
       ["1", "Motore, console, fonti A/B/C, allocazione, demo, profilo", "[[FATTO]] in gran parte; chiusura con i dati del titolare (sopra)"],
       ["2", "Registro crittografico e Auditor Portal", "[[FATTO]] (senza blockchain)"],
       ["3", "Componente assicurativa", "[[FASE 3]]"],
       ["4", "Reparto di consulenza", "[[FASE 4]]"]], [14, 100, 56])
    story.append(PageBreak())

    # ================================================================================================ EXECUTIVE SUMMARY
    H1("EXECUTIVE SUMMARY")
    P("QUANTO è un motore di calcolo, allocazione e — in prospettiva — consulenza finanziaria per enti, PMI e associazioni, con due missioni permanenti: validare il budget di una candidatura a un bando pubblico e pianificare l'allocazione delle risorse dell'anno successivo tra spesa ordinaria e finanziamenti pubblici. "
      "Non scrive testo progettuale: produce solo la componente numerica, validata da un motore deterministico a 60 criteri, completamente disaccoppiato da qualunque modello linguistico.")
    P("**Il sistema esiste ed è in produzione.** Un'azienda carica visura e bilanci in una procedura guidata; QUANTO ne ricava il profilo con la provenienza di ogni dato, stima le spese dell'anno successivo con le variazioni scelte dall'utente, trova tra i bandi studiati quelli adatti (indicando quanto coprirebbero e di quanto vanno ridotte le voci per rispettare i tetti) "
      "e tra gli oltre 800 del catalogo quelli più affini da studiare, calcola il piano ottimo di copertura e costruisce la bozza di budget per il bando scelto, poi controllata dal motore, esportata e registrata con una impronta firmata verificabile da chiunque.")
    P("La proposta si dimostra con una demo comparativa su dati reali; l'accuratezza con un Conformity Score su casi di test noti — non con un tasso di errore su pratiche reali, che non esistono. La copertura normativa non è vincolata a un solo bando: il catalogo individua tutto ciò che è aperto, e l'estrazione parte solo su conferma con riuso in cache. "
      "Il Registro crittografico è stato anticipato e realizzato senza blockchain; la componente assicurativa e il reparto di consulenza restano visione a lungo termine. Per arrivare al 100% servono dati e decisioni del titolare (chiave del modello, dataset dei pattern, tabelle ufficiali, OCR, documenti legali) e alcuni sviluppi dichiarati nel Modulo 27.")

    # ================================================================================================ SCHEMA API
    H1("SCHEMA TECNICO API (reale)")
    P("L'integrazione con ERP e gestionali avviene via REST protetta da OAuth 2.0 (client-credentials) o da firma HMAC; gli utenti dell'app usano un token a 8 ore. Non esiste alcun endpoint di generazione testuale progettuale. Tutto vive sotto `/api/v2`. Documentazione interattiva su `/docs`. Sono 121 endpoint; di seguito i gruppi con i principali.")
    T([["Gruppo", "Endpoint principali"],
       ["Salute", "GET /health, GET /health/ready"],
       ["Autenticazione", "POST /auth/register, /auth/login, /auth/token, /auth/change-password; GET /auth/me, /auth/me/activity, /auth/me/credits"],
       ["Bandi", "GET /bandi, /bandi/{id}, /bandi/catalog (q, issuer, only_new, described, with_meta, page), /bandi/catalog/issuers, /bandi/catalog/stats, /bandi/search, /bandi/references; POST /bandi/{id}/select, /bandi/upload; ricerca e studio: POST /bandi/research/search, /fetch, /analyze, /confirm, /run"],
       ["Ingestion", "GET /ingestion/catalog, /status/{id}, /review-queue, /grant-rules/{id}; POST /ingestion/catalog, /confirm/{id}, /extract, /review"],
       ["Budget", "POST /budget/validate, /budget/wp-plan (nuovo), /budget/import, /budget/export/pdf, /budget/export/xlsx; GET /budget/criteria, /budget/fields, /budget/demo, /budget/template.xlsx"],
       ["Allocazione", "POST /allocation/optimize; GET e POST /allocation/funds, POST /allocation/funds/from-bando, DELETE /allocation/funds/{id}"],
       ["Profilo (nuovo)", "GET /profile; PUT /profile; PUT /profile/financials/{anno}; POST /profile/sync, /profile/forecast, /profile/match, /profile/template"],
       ["Documenti del cliente", "GET e POST /fonte-c/documents; GET e DELETE /fonte-c/documents/{id}; /file, /cost-line, /draft-items, /expenses; POST /fields/{id}/review"],
       ["Fonte B", "GET /fonte-b/summary, /kinds, /datasets, /template/{tipo}.csv; POST /datasets (bozza), /datasets/{id}/publish; DELETE bozza"],
       ["Pattern", "GET /pattern/categories, /pattern/budgets; POST /pattern/match, /pattern/import"],
       ["Registro", "POST /registry/register, /verify/recompute, /verify/attestation, /merkle-lab; GET /registry/status, /public-key, /verify/{progetto}, /attestation/{progetto}"],
       ["Quartier Generale", "GET /hq/overview, /timeline, /operations, /projects, /documents, /users, /archive e /archive/{id} (con regole, requisiti, fonti, scheda consulente, ZIP), /db/tables"],
       ["Lavori periodici", "GET/POST /cron/catalog-refresh, /cron/catalog-lifecycle, /cron/catalog-describe (segreto del cron o manager)"]], [32, 138])
    H3("1. Validazione del budget di progetto")
    P("Differenza dalla v2.1: le regole del bando viaggiano nel campo `grant_rules` (l'insieme completo delle regole pubblicate, con `rule_version_hash`), non in un `grant_context`; i valori della voce sono campi diretti della voce, non in `raw_values`. La rinomina verso lo schema originale non è stata fatta. [[PARZIALE]]")
    CODE('POST /api/v2/budget/validate\n{\n  "project_id": "PRJ-2026-001",\n  "grant_rules": { "bando_id": "NUOVA-SABATINI", "bando_name": "…", "rule_version_hash": "…", "contribution_rate_pct": 0.0275, … },\n  "cost_items": [ { "item_id": "A-01", "category": "CAPITAL_ASSETS", "amount_eur": 219600.0, "source_c_ref": "DOC-FC-12", … } ],\n  "entity_liquidity_eur": 90000, "baseline_totals": { … }\n}')
    P("Risposta (campi reali): `project_id`, `bando_id`, `status` (VALIDATED), `conformity_score` (es. 91), `total_requested_eur`, `total_approved_eur`, `total_rejected_eur`, `items[]` con `status` (APPROVED, CAP_EXCEEDED_ADJUSTED, REJECTED, MISSING_DOCUMENTS), `original_cost_eur`, `computed_cost_eur`, `rejection_reason`, `applied_rules`, `criteria_checked`, `criteria_failed`, `criteria_not_evaluated`, `item_hash_sha256`; "
      "`budget_checks[]` per i criteri 48, 49, 55, 56, 60; `trace` (fasi, passi, tetti %, albero di Merkle); `run_id`, `reference_date`, `merkle_root`, `cep_id`, `llm_explanation_summary`, `explanation_source` (TEMPLATE o LLM).")
    H3("2. Allocazione annuale")
    CODE('POST /api/v2/allocation/optimize\n{\n  "fiscal_year": 2027,\n  "use_profile_forecast": true,                 // oppure historical_balance_ref, oppure historical_expenses (una sola origine)\n  "growth_pct": { "CONSULTING": 0.10 },          // variazione annua scelta dall\'utente\n  "available_funding_lines": [ { "fund_id": "…", "allowed_categories": ["CAPITAL_ASSETS"], "coverage_pct": 0.75, "de_minimis": false, … } ],\n  "optimization_target": "MINIMIZE_NET_COST",    // MAXIMIZE_COVERED_ITEMS | MINIMIZE_FUNDS_INVOLVED\n  "excluded_funds": [], "de_minimis_residual_eur": null\n}')
    P("Risposta: `status`, `total_gross_expense_eur`, `covered_by_public_funds_eur`, `net_cost_to_entity_eur`, `overall_coverage_percentage`, `allocation_plan[]` (voce, importo, copertura per fondo, a carico), `fund_usage[]` (usato, dotazione, margine di sicurezza), `monthly_plan[]`, `summary`, `solver`.")
    H3("3. Profilo, stima, abbinamento e bozza")
    CODE('POST /api/v2/profile/match      { "year": 2027, "growth": { "PERSONNEL": 0.04 } }\n  → { "forecast": { "base_year", "categories": [ { "category", "baseline_eur", "suggested_growth", "growth_applied", "forecast_eur" } ], "warnings", … },\n      "matching": { "results": [ { "bando_id", "fit": "ADATTO|DA_VERIFICARE|NON_ADATTO", "checks": [ { "id", "result": "OK|FAIL|UNKNOWN", "detail" } ],\n                      "estimate": { "rate_pct", "covered_eur", "by_category", "adjustments" } | null, "fund": { … }, "notes" } ],\n                    "catalog": { "items": [ { "bando_id", "summary", "score", "affinity", "reasons", "to_check" } ], "total_candidates", "excluded" },\n                    "summary", "missing_profile" } }\n\nPOST /api/v2/profile/template  { "bando_id": "…", "scale_pct": 25, "fit": true }\n  → { "cost_items": [ { "item_id": "TPL-01", … } ], "needs_personnel": { "amount_eur", "message" } | null, "adjustments", "excluded_categories", "notes", "total_eur" }')
    CODE('POST /api/v2/budget/wp-plan\n{ "project_id": "PRJ-2026-001", "allow_split": true,\n  "items": [ { "item_id": "A-01", "category": "PERSONNEL", "amount_eur": 60000, "pinned_wp": null } ],     // importi AMMESSI\n  "work_packages": [ { "wp_id": "WP1", "name": "Gestione", "min_share_pct": 0.1, "target_share_pct": 0.5, "max_share_pct": 0.6,\n                       "allowed_categories": ["PERSONNEL", "OVERHEAD"], "category_max_share": { "OVERHEAD": 0.2 } } ] }\n→ { "status": "OPTIMAL | BEST_FOUND | INFEASIBLE", "message", "assignments": [ { "item_id", "parts": [ { "wp_id", "amount_eur", "share" } ] } ],\n    "work_packages": [ { "wp_id", "total_eur", "share_pct", "by_category", "deviation_pp" } ], "checks": [ { "wp_id", "rule", "ok", "detail" } ],\n    "reasons": [], "unplaced": [], "notes": [] }')
    H3("4. Stato dell'ingestion")
    CODE('GET /api/v2/ingestion/status/FONDO-GARANZIA-PMI\n→ { "catalog_status": "CURATED", "extraction_status": "COMPLETED", "cache_hit": true, "rules_extracted_total": 2,\n    "rules_from_structured_parsing": 1, "rules_from_multi_pass_ai": 0, "rules_with_pass_agreement": 0,\n    "rules_pending_human_review": 1, "rules_human_reviewed": 0, "rules_from_curated_source": 0, "requested_by_clients_count": 11 }')
    H3("5. Notifiche webhook")
    P("Gli indirizzi e il segreto vengono solo dall'ambiente; il corpo è firmato HMAC-SHA256 (intestazione `X-Quanto-Signature`); i contenuti sono identificativi opachi e totali, mai dati personali o contabili di dettaglio.")
    T([["Evento", "Stato"],
       ["event.budget.validated", "[[FATTO]]"], ["event.budget.registered (nuovo)", "[[FATTO]]"], ["event.allocation.optimized", "[[FATTO]]"], ["event.criteria.failed", "[[FATTO]]"], ["event.pattern.matched", "[[FATTO]]"],
       ["event.bando.coverage_activated", "[[FATTO]]"], ["event.rule.disagreement_detected", "[[FATTO]] (attivo solo con lo Stadio 3)"],
       ["event.consultation.requested", "[[FASE 4]]"], ["event.rule.audit_flagged", "[[DA FARE]]"]], [90, 80])

    # ================================================================================================ APPENDICI
    H1("APPENDICE A — Variabili d'ambiente")
    T([["Variabile", "A cosa serve"],
       ["QUANTO_DATABASE_URL (o DATABASE_URL / POSTGRES_URL)", "Connessione a PostgreSQL; QUANTO_DB_POOL_MAX per la dimensione del pool"],
       ["QUANTO_AUTH_REQUIRED", "Autenticazione (di default attiva; spenta solo in sviluppo)"],
       ["QUANTO_JWT_SECRET · QUANTO_HMAC_SECRET · QUANTO_OAUTH_CLIENTS", "Token degli utenti, firma HMAC delle richieste, client OAuth per gli ERP"],
       ["QUANTO_OWNER_EMAIL", "L'unico indirizzo che entra nel Quartier Generale"],
       ["QUANTO_BOOTSTRAP_ADMIN_EMAIL · QUANTO_BOOTSTRAP_ADMIN_PASSWORD", "Creazione del primo manager (da usare una volta)"],
       ["QUANTO_FILE_KEY", "Chiave AES-256 dei file dei clienti (senza non si carica nulla)"],
       ["QUANTO_PII_KEY", "Chiave dei token per nomi, codici fiscali e IBAN"],
       ["QUANTO_FIELD_CONFIDENCE_MIN", "Soglia di confidenza dei campi letti (default 0,90)"],
       ["QUANTO_SIGNING_KEY · QUANTO_TRUSTED_PUBLIC_KEYS", "Chiave privata Ed25519 del registro; chiavi pubbliche considerate di fiducia"],
       ["QUANTO_OCR_ENGINE · QUANTO_TESSERACT_CMD", "Motore OCR (non disponibile su Vercel)"],
       ["QUANTO_LLM_PROVIDER · QUANTO_LLM_MODEL · QUANTO_LLM_PASSES · ANTHROPIC_API_KEY · QUANTO_LLM_API_KEY", "Modello linguistico (spento senza chiave)"],
       ["QUANTO_BRAVE_API_KEY (e analoghe per altri motori)", "Ricerca web dei documenti di un bando (attiva in produzione)"],
       ["CRON_SECRET", "Accesso dei cron di Vercel agli endpoint /cron"],
       ["QUANTO_WEBHOOK_URLS · QUANTO_WEBHOOK_SECRET", "Destinazioni e segreto dei webhook"],
       ["QUANTO_CORS_ORIGINS · QUANTO_PUBLIC_URL", "Origini consentite e indirizzo pubblico (per i QR)"],
       ["QUANTO_ALLOW_UNOFFICIAL_TABLES", "Solo sviluppo: consente tabelle di Fonte B senza fonte ufficiale"]], [76, 94])

    H1("APPENDICE B — Cronologia del lavoro")
    T([["Blocco", "Data", "Contenuto"],
       ["Fondazione", "19/09/2026", "Costruzione del monorepo (backend FastAPI, frontend React, test), 60 criteri, registro firmato, ingestion, OAuth/HMAC, export, allocazione MILP. Blockchain eliminata per decisione del titolare."],
       ["Quartier Generale e Algoritmo", "19/09/2026", "Quartier Generale, memoria degli eventi, Algoritmo grafico, libreria dei bandi con fonti, demo a 46 voci, import Excel."],
       ["Linguaggio e Guida", "20/09/2026", "Restyle minimale, linguaggio semplificato, Guida con Merkle interattiva, aiuti in ogni pagina."],
       ["Ricerca e archivio", "20/09/2026", "Ricerca web reale con scarico e lettura dei documenti, scoperta senza motori, archivio dei bandi con file originali e scheda per il consulente."],
       ["Identità visiva", "21/09/2026", "Restyle con colore bianco e giallo, caratteri, icone."],
       ["Dati veri", "21/09/2026", "PostgreSQL, Fonte B in database, Fonte C cifrata con confidenza e revisione, utenti e ruoli, banca dei pattern con k-means, modulo del modello linguistico, cron del catalogo."],
       ["Demo e pulizia", "26/09-01/10/2026", "Demo con bandi reali, banca dei pattern con bilanci di società quotate, rifacimento della homepage e delle pagine con lo stile «finestra», pulizia del catalogo, processo standard di studio, figure strutturate."],
       ["Sicurezza e profilo", "03/10/2026", "Sicurezza e CI (azioni fissate, audit, intestazioni, CSP), profilo aziendale, stima dell'anno, abbinamento ai bandi, bozza di budget, allocazione a passi."],
       ["Catalogo, procedura guidata e test", "04/10/2026", "Schede del catalogo (descrizioni e caratteristiche), procedura guidata a passi, documenti dell'azienda di prova, test completo su dati reali con 18 correzioni, ripartizione delle voci tra i WP, anteprima e scarico di tutti i file dell'azienda, questo documento."]], [34, 28, 108])
    NOTE("Fine del documento. Ogni numero riportato è stato letto dal sistema o dal codice alla data indicata; dove un dato non esiste (pratiche reali, metriche di successo, benchmark) il documento lo dichiara.")
