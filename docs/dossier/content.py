"""Testo del dossier QUANTO v4.5. Ogni affermazione di stato è verificata sul codice (12 ottobre 2026); i dati online che richiedono l'accesso sono quelli dell'ultima lettura con accesso (4 ottobre 2026) e sono datati."""
from __future__ import annotations

import json
from pathlib import Path

FACTS = json.loads((Path(__file__).parent / "facts.json").read_text(encoding="utf-8"))


def build(m):  # noqa: C901 - un documento lungo è una sola funzione di testo
    H1, H2, H3, P, B, T, NOTE, CODE, SP, story = m.H1, m.H2, m.H3, m.P, m.B, m.T, m.NOTE, m.CODE, m.SP, m.story
    from reportlab.platypus import PageBreak, Paragraph

    # ------------------------------------------------------------------------------------------------ copertina
    story.append(Paragraph("QUANTO v4.5 — Documento Completo", m.S["title"]))
    story.append(Paragraph("Il motore di calcolo per studi di commercialisti e boutique di finanza agevolata", m.S["sub"]))
    story.append(Paragraph("Versione 4.5: riscrittura integrale della v3.0, aggiornata allo stato reale del sistema al 15 ottobre 2026 e con la visione ridefinita, con conteggi e schema API ricontrollati uno per uno sul codice. Nessuna sintesi: ogni processo è spiegato nel dettaglio e ogni funzione porta il suo stato.", m.S["p"]))
    SP(6)
    H1("Nota di apertura — cosa contiene questo documento e cosa è cambiato")
    P("Questo documento riprende, modulo per modulo, la struttura del documento «FKOS v2.1 — Documento Completo» (22 moduli, executive summary, schema tecnico API) e la porta al presente, partendo dalla v3.0 del 4 ottobre. "
      "Il prodotto si chiama **QUANTO** (FKOS era il nome di lavoro) ed è in produzione su https://quanto-self.vercel.app. Per ogni funzione si dice se è **realizzata e verificata**, **parziale**, oppure **ancora da fare**, e cosa manca per il 100%.")
    P("**Il cambio di posizionamento.** Dalla v3 QUANTO è pensato per chi lo usa di mestiere: **studi di commercialisti e boutique di finanza agevolata**. L'account è dello studio; ogni azienda cliente è un «lavoro» con il suo profilo, i suoi bilanci e i suoi risultati; "
      "il testo dell'interfaccia parla al professionista e non rimanda mai a «consulta il tuo commercialista». Le quattro decisioni strategiche della v2.1 restano il perno e sono tutte rispettate dal codice:")
    B(["**QUANTO non scrive progetti.** Nessun testo persuasivo, nessuna relazione illustrativa: solo la componente numerica (budget, ammissibilità, allocazione, stima dell'anno successivo).",
       "**Multi-verticale fin dal disegno.** Catalogo nazionale di oltre 5.900 misure letto dalle fonti istituzionali; le regole si estraggono solo su richiesta, con cache.",
       "**Metriche oneste e separate.** Nessun tasso di errore dichiarato prima di avere pratiche reali (Modulo 14).",
       "**Strumenti gratuiti.** Gli strumenti di QUANTO sono gratuiti per gli studi (Modulo 21): il pricing ibrido della v2.1 non è la strategia attuale; il contatore a crediti è solo un limite d'uso senza pagamenti."])
    P("A queste si aggiungono le decisioni prese dopo la v2.1, riportate con la data nel Modulo 29 e nella cronologia: eliminazione della blockchain (19/09/2026), regola **«mai dati inventati»** (ogni numero risale a una fonte reale o dichiara la propria lacuna), "
      "un solo processo standard per studiare ogni bando (01/10/2026, oggi RICERCA-v2), nessuna migrazione di Tailwind finché non serve (03/10/2026), caricamento manuale dei bandi riservato al Quartier Generale e scenario demo tolto dall'applicazione (tra il 5 e l'8 ottobre), **visione ridefinita il 12 ottobre 2026**: niente consulenza esterna (le regole le cura un team interno), niente partnership assicurative, e a lungo termine l'acquisizione di studi di commercialisti resi dipendenti da QUANTO (Modulo 18).")
    H2("Cosa è successo dal 4 al 15 ottobre, in sintesi")
    B(["**Studio e lavori** (Modulo 25): l'account è dello studio; ogni cliente è un lavoro con dati, documenti e risultati propri; cambiando pagina o chiudendo l'app ogni scelta si ritrova.",
       "**Ogni bando ha un valore in euro** (Modulo 24): regola pubblicata, modello curato con le sue ipotesi, oppure tabella di intensità letta dal testo ufficiale; il processo di ricerca ora segue i link fino a tre giri e cerca apposta la percentuale (RICERCA-v2).",
       "**Potenziale massimo con tutti i bandi insieme**, bilancio ricostruito con il grafico di ogni bando, piano **sempre uguale a parità di dati e sempre massimo**, legenda sempre visibile di ogni numero e **de minimis** spiegato, riconosciuto dalle fonti e stimato dai dati dichiarati (Modulo 24).",
       "**Confronto riscritto sui template di budget** (Modulo 25): due motori (collettivo e interno), consiglio che si auto-migliora a ogni dato, mappa nicchie-bandi, solo bandi affini al lavoro attivo.",
       "**Interfaccia professionale e minimale**: menu di gestione a sinistra, profilo completo dello studio (dati, sicurezza, piano e dati), nessun effetto vetro o «cartone animato».",
       "**Assistente guidato** (Modulo 26): dove l'utente dovrebbe inserire dati o muoversi nell'app, l'assistente lo fa al suo posto, passo per passo, e chiede i valori spiegando in parole semplici cosa sono e dove si trovano.",
       "**Manuale dei processi** (testo in Quartier Generale e PDF) e «I 60 criteri spiegati» (Modulo 15 e docs).",
       "**Documenti dell'azienda di prova ricostruiti come quelli veri** (Modulo 4 e 9.3): bilanci di 58-63 pagine con nota integrativa e relazione, visura di 9 pagine, domanda di contributo di 16 pagine, business plan di 46 pagine con modello mensile a 36 mesi, dichiarazioni fiscali, registri delle fatture e otto fogli Excel di centinaia di righe (57 documenti in tutto con le aggiunte del Modulo 31); il test ha trovato e fatto correggere sette difetti di lettura.",
       "**Assistente a chat** (Modulo 26): una scena a tutto schermo con l'app in una scheda ridotta e la chat a destra, con suggerimenti e barra di scrittura.",
       "**Visione ridefinita** (Modulo 18) e nuovo documento breve, il **Riassunto** (7 pagine, `docs/riassunto/`): cosa fa QUANTO, come lavora, gli strumenti e il valore per gli studi.",
       "**Voci di spesa, tutti i documenti, budget dall'azienda e dall'allocazione** (Modulo 31): oltre 50 voci sotto le cinque categorie, lettura degli Excel e di alcuni PDF, personale persona per persona, spese dal budget dell'azienda, un budget per ogni bando ricavato dall'allocazione. Esempio: la riga «Affitto della sede» diventa la voce «Affitti e locazioni».",
       "**Come si accede a un bando e de minimis verificato** (Modulo 31): non tutti i bandi chiedono un progetto (garanzie, crediti automatici, assunzioni, spese commerciali, ristori); idee di progetto dai documenti; impresa unica e visura aiuti dell'RNA con residuo prudente finché la verifica non è completa.",
       "**Più documenti letti, incrociati e usati** (Modulo 31, 31.7–31.12): fatture elettroniche XML, bilancio XBRL, bilancio di verifica in CSV, visura aiuti dell'RNA, libro soci, dichiarazioni fiscali, estratto conto e preventivi dei fornitori; controlli di coerenza tra i documenti (per esempio IVA e ricavi); i preventivi sostituiscono gli importi del piano degli investimenti. Esempio: il preventivo da 48.600 € del cloud prende il posto dei 45.000 € previsti, e lo dice.",
       "**Dall'allocazione alla realtà** (Modulo 31, 31.10): per ogni bando valore atteso (probabilità, consulente, istruttoria), tempi di incasso mese per mese e altri aiuti da sommare. Esempio: 60.000 € al 50% con consulente al 10% e 3.000 € di istruttoria valgono 24.000 €, non 60.000.",
       "**Livelli di contratto mancanti** (Modulo 31, 31.11): bozza di completamento di Fonte B, sempre da attestare da un manager; **voci escluse lette dal testo** ora in revisione; **azienda di prova che si aggiorna da sola** all'apertura dei documenti."])
    P("**Come è stato verificato (15 ottobre 2026).** **Codice:** **549 test automatici** verdi; operazioni API, migrazioni, tabelle e bandi curati ricontati dal codice; lo schema API di questo documento è confrontato con le rotte reali (OpenAPI). **Online:** il sito pubblicato serve esattamente l'ultima versione del frontend (stessi file generati dal build) e il registro firmato è integro, con la stessa chiave e una registrazione. **Non verificato online:** tutto ciò che richiede l'accesso (catalogo, bandi, regole, database) resta quello dell'ultima lettura con accesso, del **4 ottobre 2026**, e porta la data, perché durante questa riscrittura non era disponibile una sessione di accesso. Le funzioni aggiunte dopo il 4 ottobre (assistente, de minimis, legenda, Confronto) sono provate in locale su un database temporaneo con l'azienda di prova: **la verifica online con i dati reali resta da fare**.")
    H2("Legenda degli stati")
    T([["Etichetta", "Significato"],
       ["[[FATTO]]", "Realizzato, coperto da test automatici e, dove ha senso, provato online con dati reali."],
       ["[[PARZIALE]]", "Esiste e funziona, ma con un limite dichiarato (copertura, dato mancante, componente non collegata)."],
       ["[[DA FARE]]", "Previsto nella v2.1 e non ancora realizzato."],
       ["[[VISIONE]]", "Direzione a lungo termine, volutamente non anticipata (Modulo 18)."],
       ["[[DECISIONE]]", "Scelta presa dopo la v2.1 che cambia il disegno originale."]], [45, 125])

    # ------------------------------------------------------------------------------------------------ stato in una pagina
    H1("Lo stato in una pagina")
    T([["Modulo (v2.1)", "Stato", "In una riga"],
       ["1-3 Visione, missioni, posizionamento", "[[FATTO]]", "Le due missioni sono in produzione; il posizionamento è ora quello di strumento per studi e boutique di finanza agevolata (account dello studio, aziende clienti come «lavori»)."],
       ["4-6 Prova su dati realistici, Confronto e pattern", "[[PARZIALE]]", "Demo tolta dall'app; azienda di prova fittizia. Il Confronto è riscritto sui template di budget dello studio (due motori, consiglio che si auto-migliora): funziona, ma senza template reali dichiara «ancora pochi dati»."],
       ["7 Disaccoppiamento / Strict Grounding", "[[PARZIALE]]", "Motore e validatore numerico completi; il modello linguistico non è collegato in produzione (nessuna chiave), il testo è il template fisso."],
       ["8 Console", "[[FATTO]]", "Menu laterale con 7 pagine (Bandi, Budget, Allocazione, Confronto, Verifica, Guida, Profilo) + Algoritmo + Quartier Generale (12 sezioni) + assistente guidato. Il frontend non calcola mai importi."],
       ["9.1 Fonte A (normativa)", "[[PARZIALE]]", "Catalogo, schede, processo standard RICERCA-v2 (fino a 3 giri di link, ricerca mirata della percentuale), valutazione in euro, cache e coda di revisione: fatti. Stadio 3 con più passaggi AI: pronto ma spento. Audit di calibrazione: da fare."],
       ["9.2 Fonte B (tabelle)", "[[PARZIALE]]", "Versionata per data nel database, nessun valore nel codice; 3 CCNL, 2 parametri, 5 aliquote (ultima lettura online); zero benchmark di prezzo/tariffa."],
       ["9.3 Fonte C (dati del cliente)", "[[FATTO]]", "6 tipi di documento, cifratura AES-256-GCM, confidenza per campo, revisione, token per i dati personali. OCR su scansioni solo dove gira Tesseract (non su Vercel)."],
       ["9.4 Profilo dell'azienda e dello studio", "[[FATTO]]", "Un profilo per ogni lavoro (dati, bilanci con provenienza, modello di previsione) e un profilo dello studio a quattro sezioni (lavori, studio e dati, sicurezza, piano e dati)."],
       ["10-11 Motore e 60 criteri", "[[FATTO]]", "Tutti i 60 criteri implementati con Decimal; un criterio senza dato o regola è «non valutato», mai «superato»."],
       ["12 Allocazione e potenziale massimo", "[[FATTO]]", "MILP esatto (HiGHS), verifica in centesimi, piano deterministico e sempre massimo; pagina a 5 passi dal bilancio al piano; potenziale massimo con tutti i bandi adatti."],
       ["24 Valore in euro dei bandi e de minimis", "[[PARZIALE]]", "Ogni bando adatto ha un valore con intervallo e le sue ipotesi; il de minimis è riconosciuto dalle fonti e stimato dai dati dichiarati. Limite: un bando senza percentuale nei testi letti resta senza importo (e lo dice)."],
       ["25 Studio, lavori e Confronto a template", "[[FATTO]]", "Multi-lavoro con salvataggio per lavoro; template con esito, sei livelli di somiglianza, fiducia dichiarata, stili, due motori e privacy per gruppi minimi."],
       ["26 Assistente guidato", "[[FATTO]]", "Quattro attività con pannello a destra e passi visibili; provato in locale, da verificare online dopo il rilascio."],
       ["13 Dove interviene l'AI", "[[PARZIALE]]", "Confini rispettati; unica AI in produzione: la ricerca Brave per trovare i documenti, non per interpretarli. L'assistente non usa modelli linguistici."],
       ["14 Metriche", "[[FATTO]]", f"{FACTS['tests']} test automatici passano; nessuna metrica su pratiche reali (non esistono)."],
       ["15 Stack", "[[FATTO]]", "FastAPI + PostgreSQL + React/Vite su Vercel; CI con test, build e audit delle dipendenze."],
       ["16 Sicurezza e GDPR", "[[FATTO]]", "Cifratura a riposo, pseudonimizzazione, scrypt, blocco account, RLS su tutte le tabelle, intestazioni di sicurezza e CSP; esportazione ed eliminazione dei dati dello studio. DPA e valutazione d'impatto: da fare."],
       ["17 Registro crittografico", "[[DECISIONE]]", "Anticipato dalla Fase 2 e realizzato SENZA blockchain: catena di hash firmata Ed25519, Merkle, attestazioni offline, Auditor Portal."],
       ["18 Visione a lungo termine", "[[VISIONE]]", "Dal mercato degli studi, all'estero, all'acquisizione di studi resi dipendenti da QUANTO. Nessuna consulenza esterna e nessuna partnership assicurativa (decisione del 12/10/2026)."],
       ["19 Team interno e revisione delle regole", "[[PARZIALE]]", "Le regole e le tabelle le cura un team interno di QUANTO dal Quartier Generale (coda di revisione, scheda di revisione per bando); il team è da costituire."],
       ["20-22 Go-to-market", "[[DA FARE]]", "Nessuna attività commerciale avviata; registrazione libera e crediti simulati pronti."]], [52, 22, 96])
    H2("Numeri del sistema")
    P("Il codice è stato contato il 12 ottobre 2026; i dati online che richiedono l'accesso (catalogo, bandi, regole, database) sono quelli dell'ultima lettura con accesso, il **4 ottobre 2026**.")
    T([["Dato", "Valore"],
       ["Test automatici backend (12/10)", f"{FACTS['tests']} (tutti verdi; CI su ogni push: test su PostgreSQL 16, build, audit dipendenze)"],
       ["Endpoint REST (12/10)", f"{FACTS['endpoints']} operazioni sotto /api/v2 (più la radice /)"],
       ["Migrazioni del database (12/10)", f"{FACTS['migrations']} (init, fonte_b, fonte_c, funding_lines, users, pattern, draft_doc_type, enable_rls, requirement_figures, company_profile, catalog_meta, forecast_template, retire_demo, budget_templates, clients, user_profile)"],
       ["Tabelle (12/10)", f"{FACTS['tables']} più la tabella delle migrazioni, tutte con Row Level Security attiva"],
       ["Criteri del motore", "60 su 60 implementati"],
       ["Bandi curati a mano (12/10)", "8: Transizione 5.0 (iperammortamento), Nuova Sabatini, Horizon Europe, Smart&Start Italia, Investimenti Sostenibili 4.0, Fondo di Garanzia PMI, SIMEST 394/81, FVG Validazione TRL"],
       ["Catalogo nazionale (online, 4/10)", f"{FACTS['catalog_total']} voci aperte o senza data (da 5.975 prima della pulizia); {FACTS['catalog_open']} con scadenza futura certa, {FACTS['catalog_undated']} senza data; tutte con la scheda letta"],
       ["Bandi in memoria (online, 4/10)", f"{FACTS['bandi']} voci totali (comprendono il bando di prova poi eliminato); {FACTS['studied']} del catalogo già studiati con il processo standard"],
       ["Regole / requisiti letti (online, 4/10)", f"{FACTS['rules']} regole pubblicate o in revisione, {FACTS['requirements']} requisiti, {FACTS['sources']} documenti di fonte con {FACTS['files']} file originali conservati"],
       ["Fonte B pubblicata (online, 4/10)", "3 CCNL (Commercio, Metalmeccanica, Terzo settore), 2 parametri nazionali, 5 aliquote d'ammortamento, 0 benchmark"],
       ["Banca dei pattern", "5 budget da bilanci di società quotate, ciascuno con pagina e nota della fonte"],
       ["Database (online, 4/10)", f"PostgreSQL, {FACTS['db_mb']} MB, {FACTS['events']} eventi registrati, {FACTS['runs']} esecuzioni salvate"],
       ["Registro firmato (online, verificato 12/10)", "1 registrazione (prova della demo), catena integra, chiave di firma 4e5773cd74cfe97d (non di sviluppo), testa della catena 0ac85d96…"]], [48, 122])

    H2("Cosa è cambiato rispetto alla v2.1 — in dettaglio")
    T([["Area", "v2.1 (progetto)", "Oggi (sistema)"],
       ["Nome e destinatario", "FKOS, enti e PMI", "QUANTO, per studi di commercialisti e boutique di finanza agevolata: l'utente è il professionista, il cliente è un «lavoro»."],
       ["Registro (Mod. 17)", "Fase 2: albero di Merkle + hash dei documenti, ancoraggio non specificato", "Realizzato: catena di hash append-only firmata Ed25519, Merkle con separazione di dominio (RFC 6962), attestazione verificabile offline, Auditor Portal con QR. Blockchain eliminata per decisione del 19/09/2026."],
       ["Database", "PostgreSQL + vettoriale", f"PostgreSQL con {FACTS['migrations']} migrazioni e {FACTS['tables']} tabelle, trigger che rendono il registro append-only, RLS. Nessun database vettoriale: la lettura delle fonti è lessicale e strutturata (vedi 9.1)."],
       ["Fonte B", "Connettori che scaricano le tabelle", "Caricamento da file con bozza → attestazione → pubblicazione da un manager, versioni per data di validità, provenienza obbligatoria. I connettori automatici non esistono."],
       ["Fonte C", "Buste paga, F24, registri IVA, bilanci, piano dei conti, organigrammi", "Buste paga, bilanci (schema civilistico), F24, bozze di candidatura, visure camerali, altri documenti (archiviati e non letti). Registri IVA e piano dei conti: non letti."],
       ["Profilo e lavori", "Non previsto", "Nuovo: un profilo per ogni azienda cliente (lavoro), con provenienza di ogni valore, modello di previsione, stima, bandi adatti e bozza di budget; profilo dello studio con sicurezza, esportazione ed eliminazione dei dati."],
       ["Catalogo (Stadio 1)", "Metadati: nome, ente, scadenza, link", "Più la descrizione ufficiale e le caratteristiche della scheda, la scadenza, lo stato aperto/chiuso e l'ordinamento per affinità con l'azienda. Le voci chiuse vengono eliminate ogni notte."],
       ["Studio di un bando", "Stadio 2 e 3 sparsi", "Un solo processo standard, RICERCA-v2: cerca → scarica → segui i link (fino a 3 giri) → leggi → cerca la percentuale → valuta, con rapporto COMPLETA / PARZIALE / INSUFFICIENTE e motivo di ogni lacuna."],
       ["Valore dei bandi", "Non previsto", "Ogni bando adatto ha un valore in euro con intervallo prudente-massimo: regola pubblicata, modello curato (interessi, risparmio fiscale, fondo perduto, garanzia) o tabella di intensità del testo ufficiale."],
       ["Allocazione", "Dal bilancio all'anno successivo, fondi dal codice o a mano", "Pagina a 5 passi: dati → stima (modello di previsione o variazione dai bilanci, con la spiegazione) → bandi adatti → potenziale massimo con tutti i bandi insieme → piano voce per voce. Risultato deterministico e sempre massimo; de minimis gestito."],
       ["Criteri", "Fino a 60, costruiti progressivamente", "60 su 60. Un criterio senza dato o regola risulta «non valutato», mai «superato»."],
       ["Confronto (pattern)", "Banca da graduatorie pubbliche", "Template di budget dello studio con esito, consiglio per nicchia e bando con sei livelli di somiglianza, due motori (collettivo e interno), mappa nicchie-bandi. La banca dei 5 bilanci quotati resta nel Quartier Generale."],
       ["Utenti", "Non descritti", "Account dello studio con ruoli USER e MANAGER, accesso riservato al titolare per il Quartier Generale, registrazione libera, crediti simulati per studio."],
       ["LLM", "Renderer + Stadio 3", "Modulo completo e testato, spento in produzione (nessuna chiave): vale il template fisso."],
       ["Interfaccia", "4 viste + pannello interno", "Menu laterale: Allocazione, Confronto, Bandi, Budget, Verifica, Guida, Profilo + Algoritmo (dal Budget) + Quartier Generale (12 sezioni) + assistente guidato a destra."],
       ["Webhook", "8 eventi", "7 eventi emessi; rule.audit_flagged non è attivo (dipende dall'audit di calibrazione); consultation.requested è stato eliminato con la visione di consulenza."],
       ["Qualità", "Regression test sui 60 criteri", f"{FACTS['tests']} test su PostgreSQL reale, CI con azioni fissate per impronta, Dependabot, audit delle dipendenze."]], [28, 50, 92])
    story.append(PageBreak())

    # ------------------------------------------------------------------------------------------------ indice
    H1("Indice")
    for line in ["PARTE I — Visione e missione: Moduli 1-3", "PARTE II — Prova su dati realistici, Confronto e pattern: Moduli 4-6",
                 "PARTE III — Architettura tecnica e algoritmica: Moduli 7-16 (con il 9.4 Profilo e studio)",
                 "PARTE IV — La visione a lungo termine: Moduli 17-19", "PARTE V — Go-to-market: Moduli 20-22",
                 "PARTE VI — Il sistema com'è oggi: Moduli 23-31 — Quartier Generale, valore dei bandi e de minimis, studio e Confronto, assistente guidato, dati e database, cosa fa l'app a ogni azione, esito del test demo, cosa manca per il 100%",
                 "Executive summary", "Schema tecnico API (reale)", "Appendici A-B — variabili d'ambiente, cronologia del lavoro"]:
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
    P("Rispettato. Il motore ospita le regole di qualsiasi bando come istanze dello stesso insieme di criteri. Oggi il sistema contiene 8 bandi curati a mano (Transizione 5.0 – iperammortamento, Nuova Sabatini, Horizon Europe, Smart&Start Italia, Investimenti Sostenibili 4.0, Fondo di Garanzia PMI, SIMEST 394/81, FVG Validazione TRL) "
      "e un catalogo nazionale di oltre 800 misure aperte, delle quali una quota si studia su richiesta. L'ampiezza di copertura resta funzione di quanti bandi sono stati studiati, non un interruttore: **all'ultima lettura online (4 ottobre) 13 bandi reali avevano regole o requisiti letti**, gli altri sono descritti ma non valutabili in euro.")

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
    P("Lo studio apre un lavoro per l'azienda cliente e carica visura e bilanci (anche più anni) nel Profilo; l'Allocazione stima le spese dell'anno successivo, valuta i bandi studiati e il catalogo con un valore in euro per ciascuno, "
      "mostra quanto ogni bando coprirebbe e quali voci vanno ridotte per rispettare i tetti, calcola il **potenziale massimo** con tutti i bandi insieme e il piano ottimo: quale fonte copre quale spesa, quanto resta a carico, come si distribuisce mese per mese (Moduli 12 e 24).")
    H3("2.3 Il filo conduttore")
    P("Le due missioni condividono motore, fonti A/B/C e console. L'effetto di lock-in descritto nella v2.1 è ora concreto: il **profilo aziendale** è il ponte. Un'azienda che ha caricato i suoi documenti per la pianificazione arriva al bando con la bozza di budget già costruita sui propri bilanci.")

    H2("MODULO 3 — Il posizionamento competitivo")
    P("Invariato nel contenuto: QUANTO non è uno strumento di scrittura, non è un FP&A generalista privo di conoscenza normativa, non è IA generica. È il motore di calcolo che le tre categorie possono usare. "
      "Un elemento nuovo rafforza la differenza: il catalogo con le schede ufficiali e l'ordinamento per affinità trasforma «quale bando fa per me?» da ricerca manuale a lista ordinata e motivata (regione, dimensione, ATECO, settore, spese ammesse), senza promettere un esito.")

    # ================================================================================================ PARTE II
    H1("PARTE II — PROVA SU DATI REALISTICI, CONFRONTO E PATTERN")
    H2("MODULO 4 — La prova su dati realistici  [[PARZIALE]]")
    P("Lo scenario «demo» e il bando di prova a 60 criteri sono stati **tolti dall'applicazione** e le loro tracce dal database (migrazione 13): ciò che compare è sempre un dato dell'utente o un dato reale. Per provare il sistema esiste un'azienda interamente fittizia, "
      "Meridiana Digital Solutions S.r.l. (50 documenti lunghi e coerenti tra loro: visura camerale di 9 pagine; tre bilanci 2023-2025 in forma ordinaria di 58, 59 e 63 pagine ciascuno, con stato patrimoniale, conto economico, rendiconto finanziario, nota integrativa voce per voce, relazione sulla gestione, verbale di assemblea, libro cespiti e conto economico analitico con 110 voci di costo e la tabella degli aiuti de minimis; diciassette cedolini (uno per persona dell'organico, con la RAL che coincide con il registro del personale) e nove F24 (da gennaio a settembre 2026); domanda di contributo di 16 pagine; DURC e dichiarazione de minimis di 4 pagine ciascuno; business plan 2026-2028 di 46 pagine con previsione mese su mese; dichiarazioni REDDITI SC, IRAP e IVA, piano di ammortamento del finanziamento, estratto conto, contratto di locazione, libro soci e relazione tecnica sul credito di ricerca e sviluppo; otto fogli Excel: aiuti ricevuti, organico e livelli CCNL, libro cespiti, bilancio di verifica con conto economico mensile, registro delle fatture emesse (2023-2025) e ricevute (2024-2025), controllo commesse e budget 2026 e modello finanziario del business plan), generata da `backend/scripts/make_sample_company.py` e conservata in `documenti_di_prova/`. "
      "Si carica come si farebbe con un cliente vero: nessuna scorciatoia nel codice. Tutti i numeri nascono da un modello contabile (`backend/scripts/sample_company/model.py`) in cui attivo e passivo tornano, il rendiconto riconcilia la cassa e i movimenti delle immobilizzazioni portano ai saldi. Gli importi dei prospetti sono in unità di euro, come in un bilancio vero; l'allegato analitico è in euro e centesimi.")
    P("Il percorso di prova è quello di tutti: aprire un lavoro → caricare i documenti nel Profilo → profilo (92% con un solo gesto, 100% dopo la risposta sulla start-up) → stima dell'anno → bandi adatti → potenziale massimo → bozza di budget → controllo dei 60 criteri → esportazione → registrazione dell'impronta → verifica → Confronto.")
    B(["**Selezione del bando:** dal catalogo o ricerca per nome (ricerca interna, poi web con Brave Search). [[FATTO]]",
       "**Budget:** a mano, Excel, PDF di candidatura, busta paga, bilancio dell'azienda o **con l'assistente** (Modulo 26). [[FATTO]]",
       "**Confronto con i template:** consiglio per nicchia e bando (Modulo 25). [[PARZIALE]]",
       "**Conformity Score** in parallelo, con motivazione per ogni voce respinta o sospesa. [[FATTO]]"])
    H3("4.3 Un risultato letto sul database di prova")
    P("Eseguito il 12 ottobre 2026 su un database locale temporaneo (catalogo ridotto, non quello online) con i nuovi documenti dell'azienda di prova: profilo al 100% con le risposte lette dai 15 file (nessuna riga da verificare tranne la RAL stimata dei cedolini), spesa prevista 2027 di 1.991.026,11 € (ricavi 1.583.200 € nel 2025, +19,2% sul 2024); 6 bandi adatti, 3 senza progetto e 3 a progetto; nello scenario «Spese dell'anno» i bandi che non chiedono un progetto coprono 148.349,41 € (7,1%), fino a 177.414,75 € con tutte le maggiorazioni, su 2.100.185,69 € di spese (dal budget dell'azienda e dal piano degli investimenti), e lasciano il resto a carico (rilettura del 16 ottobre 2026: le cifre precedenti, 62,9%, includevano per errore i bandi a progetto sui costi correnti). Il risultato dipende dai bandi studiati: sul sistema online, con un catalogo più ricco, è diverso.")
    NOTE("I numeri sono quelli del database di prova e servono a mostrare il percorso, non a promettere un esito.")

    H2("MODULO 5 — La banca dei pattern e i template  [[PARZIALE]]")
    P("La **banca dei pattern** (5 bilanci reali di società quotate, ciascuno con pagina e criterio di calcolo nella nota) resta nel Quartier Generale («Banca pattern») e si importa da CSV con fonte obbligatoria su ogni riga. È un proxy della struttura di costo, non un insieme di budget vincenti.")
    T([["Categoria", "Budget", "Fonti (bilanci pubblicati)"],
       ["DIGITALE_ICT", "3", "Websolute S.p.A. (consolidato 2024), Alkemy S.p.A. (consolidato 2023, anno scelto per escludere un impairment one-off), Doxee S.p.A. (bilancio d'esercizio 2024)"],
       ["MANIFATTURIERO_INDUSTRIA40", "2", "Vimi Fasteners Group (consolidato 2024), Fervi S.p.A. (consolidato 2024)"]], [48, 14, 108])
    P("Il **vero** insieme di budget vincenti nasce ora dai **template dello studio** (Modulo 25): ogni commercialista salva i budget dei suoi clienti con l'esito e l'algoritmo impara da quelli. Finché i template non sono abbastanza il Confronto lo dice («ancora pochi dati») e non inventa nulla. Le graduatorie pubbliche dei bandi non sono state importate (il piano finanziario di sintesi è raro e disomogeneo). **[[DA FARE]]** per il dataset iniziale.")
    H2("MODULO 6 — Gli algoritmi del Confronto  [[FATTO]]")
    B(["**Banca dei pattern:** k-means++ con seme fisso e similarità del coseno tra le quote di spesa; sotto 6 budget per categoria c'è un solo archetipo, la media, dichiarata come tale.",
       "**Template:** media pesata per esito (ammesso 3, presentato 1,5, bozza 1, non ammesso 0,25) sul primo livello di somiglianza con almeno 3 template; con almeno 6 template un k-means a seme fisso trova gli «stili» di budget e dice quanti hanno vinto; la fiducia (alta, media, bassa) è dichiarata. Dettagli nel Modulo 25.",
       "**Natura statistica dichiarata:** non c'è alcun modello linguistico; l'etichetta dice sempre «indicazione statistica, non previsione di esito»."])
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
    P("Il menu di gestione sta a sinistra (sul telefono si apre dal pulsante in alto): in alto il **lavoro attivo** (l'azienda cliente su cui si lavora), poi il pulsante **Assistente**, poi le pagine in tre gruppi, in basso Guida, Profilo, Quartier Generale (solo titolare), crediti dello studio e utente.")
    T([["Pagina", "Cosa fa", "Corrispondenza con la v2.1"],
       ["Allocazione", "Cinque passi: dati dell'azienda, stima dell'anno, bandi adatti (adatti / da verificare / non adatti / da studiare), tutti i bandi insieme (potenziale massimo, bilancio ricostruito, de minimis, legenda dei numeri), piano voce per voce con Sankey, uso dei fondi e mesi.", "Vista 2 Allocazione annuale"],
       ["Confronto", "Template di budget dello studio, consiglio per nicchia e bando, due motori, stili, mappa nicchie-bandi; solo bandi affini al lavoro attivo.", "Vista 3 Demo Pattern (riscritta)"],
       ["Bandi", "Libreria dei bandi studiati e curati; sfoglia tutto il catalogo con le descrizioni; cerca sul web; pulsante «Studia il bando». Non si caricano più bandi da testo libero (solo il Quartier Generale).", "Vista «Bandi attivi»"],
       ["Budget", "Voci per categoria, controllo dei 60 criteri, Ispettore, modifica voce, bozza dal profilo azienda, ripartizione tra i pacchetti di lavoro (WP), import Excel/PDF, export XLSX/PDF, registrazione dell'impronta.", "Vista 1 Budget Canvas + Vista 4 Report"],
       ["Verifica", "Auditor Portal: verifica impronta, ricalcolo dai dati, manomissione simulata.", "Modulo 17 (anticipato)"],
       ["Guida", "Percorso rapido, Merkle passo passo, ogni funzione con un esempio, glossario.", "—"],
       ["Profilo", "Quattro sezioni: Lavori (le aziende clienti), Studio e dati, Sicurezza, Piano e dati; dentro ogni lavoro il profilo dell'azienda con procedura guidata, bilanci, documenti (anteprima, download singolo, ZIP).", "Nuova (Modulo 9.4)"],
       ["Algoritmo", "Il «film» del calcolo: 7 fasi, mappa voci × 60 controlli, cascata degli importi, albero di Merkle. Si apre dal Budget.", "—"],
       ["Quartier Generale", "Solo titolare: 12 sezioni (Modulo 23).", "Pannello di Ingestion (Mod. 8.4), esteso"]], [28, 100, 42])
    H3("8.3 Stack di presentazione e disegno")
    P("React 18.3 con Vite 7.3 e Tailwind 3.4, icone Lucide, un solo carattere (Inter) più JetBrains Mono per il codice. Disegno **minimale e professionale**: superfici piatte bianche con bordo sottile, nessun effetto vetro, nessuna sfocatura, spigoli piccoli, palette neutra in cui il giallo del marchio compare solo nel logo e in piccoli accenti. "
      "Gli spazi seguono una scala fissa; le pagine già visitate restano montate, quindi cambiando pagina si ritrova tutto com'era. La homepage mantiene la grafica d'apertura con la «catena di blocchi». "
      "Due fatti di processo: il frontend non ha router (si naviga con uno stato interno), e la migrazione a Tailwind 4 è stata rimandata per decisione del 03/10/2026 perché non è necessaria.")
    H3("8.4 Il Pannello di Ingestion")
    P("Esiste, ed è la sezione «Bandi» e «Catalogo» del Quartier Generale: per ogni bando, documenti (testo estratto e file originale), regole (anche quelle in disaccordo), requisiti, scheda di revisione, linea di finanziamento per l'allocazione, utilizzi, esportazione ZIP; per il catalogo, descrizioni e caratteristiche. Non è visibile agli utenti.")
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
    P("**Il processo standard di studio  [[FATTO]]** (`pipeline.py`, standard **RICERCA-v2**, uguale per ogni bando e ripetibile; dura da pochi secondi a circa mezzo minuto, entro il limite di 60 secondi della funzione):")
    B(["**Cerca:** parte dal nome e dall'indirizzo della scheda ufficiale; scoperta senza motori di ricerca dai cataloghi, dagli elenchi di Invitalia e MIMIT e dai portali di famiglia (Erasmus+, coesione/FSE/FESR/PNRR, PSR, energia, export); con la chiave Brave attiva si usa anche la ricerca web. Ogni risultato è classificato **UFFICIALE** (Gazzetta Ufficiale, Normattiva, EUR-Lex, ministeri, Invitalia, SIMEST, Mediocredito Centrale, Regioni, Camere di commercio, comuni…) o **SECONDARIA**: solo dal testo ufficiale si leggono regole e percentuali.",
       "**Scarica, primo giro:** fino a 8 documenti, 6 alla volta in parallelo; pagine web, PDF (fino a 12 MB e 400 pagine), Word, Excel; ogni documento è salvato intero (testo e file originale) con la sua impronta SHA-256 e **si accetta solo se parla davvero di quel bando** (nome o parole distintive), così il bando di un'altra Regione con un nome simile non inquina le regole. Protezioni: guardia contro richieste verso indirizzi interni (SSRF), limite di dimensione e di tempo, 400 richieste ogni 10 minuti.",
       "**Segui i link, fino a tre giri:** dalle pagine scaricate si scelgono fino a 4 documenti per giro (prima i PDF; punteggio in più per «bando», «avviso», «decreto», «regolamento», «allegato 1»; in meno per «privacy», «graduatoria», «report», «CUP»…), solo se sono passati meno di 26 secondi. È questo che porta dalla scheda del catalogo alla pagina dell'ente e agli allegati veri.",
       "**Leggi (`analysis.py`):** nessun documento può risultare «vuoto» senza dire perché. Un foglio elettronico è dato di riferimento (conservato, non letto); tra le edizioni dello stesso documento conta solo l'ultima; un documento che cita spesso il bando si legge intero, gli altri solo nei passaggi che lo nominano, e le regole numeriche ricavate da questi ultimi si pubblicano solo se confermate da due fonti.",
       "**Cerca la percentuale, apposta:** se dopo la lettura non c'è né una regola «contributo pari al N%» né una tabella di intensità, e sono passati meno di 30 secondi, parte un ultimo giro con fino a 4 documenti in più cercati con parole come «intensità contributo percentuale spese ammissibili beneficiari»; poi si rilegge tutto.",
       "**Valuta:** rapporto con soglie fisse. **COMPLETA** = almeno 20.000 caratteri di testo ufficiale, 40 requisiti e metà dei requisiti riconosciuti; **PARZIALE** = almeno un documento ufficiale e 10 requisiti; **INSUFFICIENTE** = il resto. Il rapporto elenca una per una le lacune (per esempio «nessuna percentuale di agevolazione trovata»): nessun bando resta a metà senza che si sappia perché.",
       "**Dopo la lettura:** requisiti con tema, tipo (obbligo, divieto, limite, informazione, da rivedere), controlli collegati, sezione di provenienza e **cifre strutturate** (percentuali, importi, durate). Cinque regole numeriche si ricavano da cifre con frase-guida e un solo valore corrispondente (tetto d'installazione, intensità d'aiuto, anticipo, variazione tra capitoli, ritardo di rimborso in mesi); i conflitti vanno in revisione con i candidati."])
    P("Esito reale su un bando regionale (SWIch 2026, Regione Piemonte): prima il sistema si fermava alla scheda del catalogo (8.754 caratteri); con la ricerca a più giri ha raggiunto la pagina della Regione (22.281 caratteri) e gli allegati (il bando completo da 177.687 caratteri, le definizioni, la normativa, le regole di compilazione): **6 documenti ufficiali, 293.206 caratteri, 158 requisiti**, e dalla tabella del bando «micro-piccole imprese: base 25%, massimo 60%» con i massimali per progetto da 1.000.000 a 5.000.000 euro.")
    P("**Limiti dichiarati della ricerca.** Le pagine costruite interamente con JavaScript danno poco testo; i PDF scansionati non si leggono senza riconoscimento ottico; i motori di ricerca gratuiti possono bloccare un server cloud (per questo la scheda del catalogo e i suoi link sono il percorso principale).")
    P("**Ciclo di vita  [[FATTO]].** Dalle schede si leggono «Data apertura» e «Data chiusura». Ogni notte si eliminano le voci mai toccate e certamente chiuse (con scadenza passata, oppure senza data e il cui nome cita solo anni passati). Un bando già studiato o richiesto da un cliente non si cancella mai in automatico. Nella libreria i bandi del catalogo mostrano ora «APERTO (fino al …)» o «CHIUSO (scaduto il …)» dalla scadenza ufficiale.")
    P("**Stadio 2 — estrazione deterministica  [[FATTO]].** Pattern e tassonomia collegata ai 60 criteri, nessun modello: ogni frase che tocca un tema noto diventa un requisito; ogni frase con obbligo o divieto fuori tassonomia finisce in «DA_REVISIONARE». Le regole numeriche estratte sono solo quelle riconosciute senza ambiguità (circa 24 chiavi note). Una regola pubblicata non viene mai sovrascritta da un'estrazione successiva: solo la revisione umana la corregge.")
    P("**Stadio 3 — più passaggi AI  [[PARZIALE]].** Implementato e testato: N estrazioni indipendenti (numero configurabile), ogni valore accettato solo se accompagnato dalla frase del documento da cui deriva e solo se quella frase compare davvero nel testo; il codice confronta i passaggi, concordanza → pubblicata, disaccordo → coda di revisione. **Non attivo in produzione** perché manca la chiave del provider.")
    P("**Coda di verifica umana  [[FATTO]].** `/ingestion/review-queue` e `/ingestion/review` (il team interno di QUANTO risolve un disaccordo e la regola viene pubblicata); il Quartier Generale permette di impostare, correggere o eliminare ogni regola e requisito, rileggere i documenti, esportare uno ZIP o eliminare il bando.")
    P("**Audit di calibrazione continua e canale reattivo  [[DA FARE]].** Il campionamento casuale di regole già pubblicate e l'evento `rule.audit_flagged` non esistono ancora; l'audit lo farà il team interno.")
    P("**Embedding e indicizzazione vettoriale  [[DA FARE]].** La v2.1 prevedeva chunking e vettori per la consultazione libera. Oggi la lettura è lessicale e strutturata: la rilevanza di un documento si decide da parole distintive del nome e dall'ente (con un elenco di parole generiche escluse), il che spiega un limite noto: un bando «fratello» dello stesso ente può contaminare lo studio di un altro (vedi Modulo 30).")

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

    H3("9.3.1 Leggere documenti fatti come quelli veri  [[FATTO]]")
    P("Quando i documenti dell'azienda di prova sono stati rifatti come quelli di un cliente vero (bilanci di 58-63 pagine, visura completa, F24 con più sezioni, domanda di contributo con più tabelle di costo) la lettura ha mostrato difetti che le versioni di una pagina nascondevano. Ora sono corretti e coperti da test dedicati:")
    T([["Difetto trovato", "Cosa succedeva", "Come si legge ora"],
       ["Importi senza centesimi", "Un bilancio redatto in unità di euro («1.583.200») non produceva nessuna riga: servivano i centesimi.", "Si legge come importo il primo numero intero che chiude la riga; un anno («2025 2024») non è un importo."],
       ["Costi esposti due volte", "Lo schema civilistico (voci 6, 7, 8, 9…) e l'allegato analitico (conto per conto) sommati contavano ogni costo due volte; lo stesso nella domanda di contributo (per voce, per pacchetto di lavoro, per persona).", "Ogni tabella è un blocco con il suo totale: si usa un solo blocco, quello che torna con il totale dichiarato e ha più righe già riconosciute."],
       ["Piè di pagina come costo", "«Pagina 13 di 14» diventava una riga di costo da 14 euro.", "Le intestazioni e i piè di pagina ripetuti sono ignorati."],
       ["Sottovoce «c)» come fine dei costi", "«c) trattamento di fine rapporto» (lettera minuscola normalizzata in «C)») chiudeva la sezione dei costi.", "Solo «C) Proventi e oneri finanziari» chiude i costi."],
       ["Etichetta ripetuta", "Lo stesso dato compariva più volte (ATECO prevalente e secondarie, addetti e dipendenti, totale e progressivi) e finiva «ambiguo».", "Conta l'etichetta più specifica e quella che apre la riga; tra occorrenze uguali vince il valore ripetuto, solo senza vincitore decide una persona."],
       ["Sezione INPS e crediti dell'F24", "Una riga INPS («DM10 … 08/2026») diventava un tributo; un credito compensato (6938) risultava un debito.", "Si leggono le sole sezioni con codice tributo; l'importo nella colonna «a credito compensati» è un credito, riconosciuto dalla posizione sulla pagina."],
       ["Costi che nessuna agevolazione copre", "Imposte indirette, quote associative, liberalità, svalutazioni, carburanti restavano «da assegnare» e il profilo non era mai completo.", "Nuova categoria «Altro (non agevolabile)»: riconosciuta da parole chiave sicure, entra nel totale dei costi ma non nelle cinque categorie di spesa."]], [40, 70, 60])
    H3("9.4 Il profilo dell'azienda e dello studio  [[FATTO]]")
    P("Il profilo è il ponte tra le due missioni: i dati veri dell'impresa, raccolti una sola volta, usati ovunque. Due tabelle (`company_profiles`, una riga per lavoro; `company_financials`, una per lavoro ed esercizio), entrambe con la **provenienza di ogni valore**.")
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
    P("**Stima dell'anno successivo.** Parte dall'ultimo esercizio ≤ anno−1: spesa = base × (1 + variazione)^(anni di proiezione), per le cinque categorie e per i ricavi. **La percentuale di ogni voce viene, in ordine,** da: quella scritta dall'utente in quel calcolo; il **modello di previsione** del lavoro (percentuali indicate dal cliente, dal suo CFO o stimate dallo studio, salvate con etichetta e nota); "
      "la variazione che risulta dai due ultimi bilanci, **già inserita** senza che l'utente la riscriva. Ogni riga ha la sua **spiegazione con i numeri dei documenti** («Nel bilancio 2024 il personale era 748.700 €, nel 2025 890.700 €: +19,0%; i ricavi sono passati da 1.327.900 a 1.583.200 € (+19,2%): la voce pesa il 56,4% e poi il 56,3% dei ricavi, in linea; gli addetti medi sono passati da 13 a 15»), "
      "con i nomi dei file da cui vengono i dati e un punto di attenzione sopra il 25% annuo. Variazioni non plausibili (sotto −95% o sopra +500%) e categorie sconosciute sono errori. Se l'ultimo bilancio è di due anni prima, la stima avvisa che proietta più anni.")
    P("**Abbinamento ai bandi (`/profile/match`).** Per ogni bando con regole o requisiti letti: controlli con esito OK / NON OK / DA VERIFICARE (apertura, categorie ammesse, ATECO, territorio, start-up, chi può presentare domanda), **valore in euro con intervallo prudente-massimo** (Modulo 24) e le riduzioni imposte dai tetti. "
      "Risultato: **Adatto** (nessun NO, nessun controllo decisivo da verificare, c'è un valore), **Da verificare** (manca un dato decisivo o il valore), **Non adatto** (almeno un NO). "
      "Esempio con le cifre dell'azienda di prova: per «Investimenti Sostenibili 4.0» (aliquota 75%, solo beni strumentali) i 112.700 € di beni strumentali del 2025 danno 84.525 €. "
      "Formula dei tetti: se una categoria supera la sua quota massima c del totale ammissibile, l'importo ammissibile è c × (altre spese ammesse) / (1 − c); con consulenze 40.000 €, altre spese 224.200 € e tetto del 10%, ne sono ammissibili 24.911 €.")
    P("**Quando manca la percentuale.** Il bando non riceve un importo inventato: resta nell'elenco «Bandi senza una percentuale nei documenti letti» con il motivo, e si può rilanciare lo studio, che ora cerca apposta la percentuale. Le garanzie pubbliche non sono un guadagno e non si sommano: si calcola solo l'importo garantibile.")
    P("**Bozza di budget per un bando (`/profile/template`).** Si costruisce sui dati dell'azienda e sulle regole del bando, non copiando l'ultimo bilancio. "
      "**Il personale è persona per persona**: dall'organico letto nei documenti (registro del personale in Excel e buste paga, unite dal token della persona) ogni dipendente diventa una voce con livello, contratto collettivo, RAL, "
      "quota di tempo sul progetto e, se c'è la busta paga, la RAL del cedolino per il confronto del criterio 15; la quota di tempo è quella del proprio orario (la RAL di chi è part-time è già ridotta). "
      "**Le altre spese sono voci di spesa** (affitti, energia, licenze software, trasferte…) e non categorie, ognuna con la sua fonte: il **budget dell'azienda** per l'anno del progetto se è stato caricato (conto per conto), il **piano degli investimenti** per gli acquisti di beni, "
      "altrimenti la **previsione dal bilancio** ripartita come nell'ultimo esercizio. **L'ammortamento non entra**: è il costo di beni già acquistati, non una spesa futura (un bando che ammette solo l'ammortamento si applica sul libro cespiti). "
      "Dove il budget dell'azienda e la stima dal bilancio differiscono di oltre il 5% lo si scrive con i numeri. Le voci che il bando esclude per nome non entrano, quelle sopra i tetti si riducono, "
      "e ciò che manca (investimenti previsti, tabella del contratto in Fonte B per un livello) è nell'elenco «cosa manca», mai inventato. Se il bando richiede il CUP (criterio 50) o le milestone (criterio 57) lo si dice. Le voci TPL-* si sostituiscono a ogni rigenerazione, il resto del budget non si tocca.")
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
      "Obiettivi: minimizzare la spesa netta (default), massimizzare le voci coperte, minimizzare i fondi coinvolti.")
    H3("12.2 Sempre lo stesso risultato, sempre il massimo")
    P("**Perché è stato corretto.** Con gli stessi dati dello stesso cliente il piano poteva cambiare ripartizione da un calcolo all'altro: quando due fondi valgono uguale su una spesa, il risolutore sceglieva in base all'ordine in cui i fondi arrivavano (il totale era lo stesso, la divisione no). "
      "**Come funziona ora.** I fondi sono messi in un ordine canonico (prima chi non è in de minimis, poi il tetto più alto, poi il nome) e dopo aver trovato il massimo un ultimo stadio, lessicografico, sceglie tra i piani equivalenti sempre lo stesso: stesso valore più alto, a parità il fondo senza de minimis, poi il tetto più alto, poi il nome. "
      "Verificato con cinque fondi equivalenti in tutti gli ordini possibili (9 esiti diversi prima, 1 dopo) e da due test dedicati. Il piano considera di default **tutti i bandi adatti** e include da solo quelli che entrano nel catalogo: cambia solo se cambiano i dati dell'azienda o il catalogo (per esempio Invitalia pubblica un bando nuovo). Se l'utente toglie dei bandi a mano, il piano è un sottoinsieme e lo dice.")
    H3("12.3 Da dove vengono spese e fondi")
    B(["**Spese:** una sola origine per richiesta — un bilancio caricato (righe sicure o confermate; se ci sono righe da verificare la richiesta fallisce con l'elenco), spese fornite dal chiamante, oppure **il profilo del lavoro** (`use_profile_forecast`: spese per categoria dell'ultimo esercizio, proiettate con le percentuali della stima, voci «STIMA-<CATEGORIA>»).",
       "**Fondi:** non sono nel codice. Una linea si ricava dalle regole **pubblicate** di un bando o dal suo modello di valore (categorie ammesse, intensità, finestra di ammissibilità, fondi non cumulabili, tetti di consulenze e spese generali); ciò che il bando non dice (dotazione massima) non si inventa. "
       "**Regola di prudenza:** due contributi a fondo perduto non si sommano sulla stessa spesa, quindi nella pagina ogni voce riceve un solo fondo perduto, il migliore; garanzie, interessi e risparmi fiscali invece possono convivere."])
    H3("12.4 Flusso operativo (pagina Allocazione)")
    T([["Passo", "Cosa succede", "Chiamata"],
       ["1", "Riepilogo del profilo del lavoro: completezza, ultimo bilancio, dimensione, documenti, cosa manca; rimando al Profilo o all'assistente.", "GET /profile"],
       ["2", "Anno da pianificare (default anno corrente + 1); tabella con base, variazione già compilata (modello o bilanci) con la spiegazione di ogni riga, stima; avvisi sulla proiezione. Il modello di previsione si salva o si elimina da qui.", "POST /profile/match"],
       ["3", "Quattro schede: Adatto, Da verificare, Non adatto, Da studiare. Ogni bando mostra valore con intervallo, percentuale, quota sul totale, riduzioni per i tetti, controlli, note (CUP, DNSH, beni nuovi) e l'etichetta «In de minimis» con la frase di prova. «Bozza di budget per questo bando» apre il Budget.", "POST /profile/match"],
       ["4", "**Il potenziale massimo:** «Combina tutti i bandi adatti» (con scenario ottimistico opzionale per i da verificare); «Coperto dai bandi» con l'intervallo prudente-massimo, spesa, quota coperta, resto a carico; tabella «Da solo» / «Nel piano insieme»; **bilancio ricostruito** con una barra per categoria e il contributo di ogni bando (12 colori; i bandi che non servono sono in legenda come «non usato»); riquadro de minimis; legenda dei numeri.", "POST /allocation/optimize (due volte: prudente e massimo)"],
       ["5", "Obiettivo e piano voce per voce: costi, copertura, Sankey spesa → fondo, uso dei fondi con margine di sicurezza, mese per mese. Si ricalcola a ogni scelta (risposte fuori ordine scartate); le scelte restano salvate per il lavoro.", "POST /allocation/optimize"]], [14, 126, 30])
    P("Dopo «Studia questo bando» su una voce del catalogo, la pagina ricalcola, porta l'utente alla scheda dove il bando è finito e mostra com'è andata la lettura (completa/parziale, documenti, requisiti, cifre, regole). Il pulsante «Studia i 5 bandi del catalogo più affini» li studia uno dopo l'altro e rifà la stima.")
    H2("MODULO 13 — Dove interviene l'AI e dove il dato proprietario")
    T([["Funzione", "Motore proprietario (codice)", "Modello linguistico", "Stato"],
       ["Estrazione dati da buste paga, bilanci, visure", "Sì — parser e lettore (testo del PDF o OCR)", "Mai", "[[FATTO]]"],
       ["Costo orario, ammortamenti, oneri, i 60 criteri", "Sì — formule e regole codificate", "Mai", "[[FATTO]]"],
       ["Allocazione multi-fonte", "Sì — MILP con verifica esatta", "Mai", "[[FATTO]]"],
       ["Stima dell'anno, abbinamento ai bandi, bozza di budget", "Sì — aritmetica e regole", "Mai", "[[FATTO]]"],
       ["Pattern matching (banca dei 5 bilanci)", "Sì — k-means e coseno", "Mai", "[[FATTO]]"],
       ["Valore in euro dei bandi e de minimis", "Sì — regole, modelli dichiarati, tabelle del testo ufficiale", "Mai", "[[FATTO]]"],
       ["Template e consiglio del Confronto", "Sì — media pesata e k-means a seme fisso", "Mai", "[[FATTO]]"],
       ["Assistente guidato", "Sì — procedure dichiarate, nessun testo generato", "Mai", "[[FATTO]]"],
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
       ["14.2 Fiducia del consiglio del Confronto", "Alta, media o bassa secondo quanti template lo sostengono; con pochi template il Confronto lo dice invece di dare un consiglio. Per i 5 bilanci della banca dei pattern il valore resta indicativo.", "[[PARZIALE]]"],
       ["14.3 Successo e clawback reali", "Richiede pratiche presentate e controlli ex post. Non compare in alcun materiale commerciale.", "non misurabile oggi"],
       ["Nuova: completezza della lettura", "Per ogni bando studiato: COMPLETA / PARZIALE / INSUFFICIENTE, con motivi. È una misura di copertura della lettura, non di correttezza delle regole.", "[[FATTO]]"],
       ["Nuova: confidenza dei campi", "Ogni campo di un documento del cliente porta la sua confidenza; sotto 0,90 non entra nei calcoli.", "[[FATTO]]"]], [40, 100, 30])

    H2("MODULO 15 — Stack tecnologico e infrastruttura  [[FATTO]]")
    T([["Livello", "Scelta reale"],
       ["Backend", "Python 3.12 (produzione e CI), FastAPI, Pydantic v2, uvicorn; calcolo in decimal.Decimal; risolutore HiGHS via SciPy; NumPy; pdfplumber e pypdf per i PDF; reportlab per i PDF generati; openpyxl per Excel; qrcode; cryptography (AES-GCM, Ed25519); httpx"],
       ["Database", "PostgreSQL gestito (Supabase) con psycopg e un pool di connessioni; 17 migrazioni versionate; trigger che rendono append-only il registro; Row Level Security attiva su tutte le tabelle; in test un PostgreSQL vero incorporato"],
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
       ["Account dello studio", "Esportazione di tutti i dati in un file, eliminazione dell'account con password ed e-mail di conferma, uscita da tutti i dispositivi, ultimi accessi visibili; i dati di ogni lavoro sono separati dagli altri dalla chiave «studio + lavoro»"],
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
    P("Stato online verificato il 12 ottobre 2026: una registrazione di prova (n. 1, del 4 ottobre), catena integra, chiave 4e5773cd74cfe97d (non di sviluppo).")
    H2("MODULO 18 — La visione: dagli strumenti all'acquisizione degli studi  [[VISIONE]]")
    P("**Decisione del 12 ottobre 2026.** La visione precedente (una componente assicurativa con partnership per la responsabilità, un reparto di consulenza con consulenti partner) è **eliminata**. Non ci saranno consulenti esterni a sistemare le regole dei bandi: le cura un team interno di QUANTO. Non ci saranno partnership assicurative.")
    P("La direzione è una sola, in quattro tappe. Ogni tappa ha senso solo se la precedente è compiuta, e nessuna è anticipata nel codice di oggi.")
    T([["Tappa", "Cosa succede", "Perché"],
       ["1. Mercato italiano degli studi", "Prendere tutta la fetta di mercato degli studi di commercialisti e delle boutique di finanza agevolata. Gli strumenti di QUANTO sono **gratuiti**: previsione di bilanci, bandi, budget, allocazione, confronto.", "Zero costo d'ingresso: lo studio li adotta e li usa per tutti i clienti."],
       ["2. Mercati esteri", "Portare gli stessi strumenti in altri mercati, con le regole dei bandi e le tabelle locali curate dal team interno.", "Lo stesso motore deterministico vale ovunque ci siano regole scritte da applicare."],
       ["3. Dipendenza", "Estendere gli strumenti fino a coprire circa il **90% delle funzioni** che uno studio svolge. Non solo previsione di bilanci, bandi e budget: quello è il punto di partenza, il resto viene molto più avanti.", "Uno studio che lavora dentro QUANTO per quasi tutto ciò che fa non può più farne a meno."],
       ["4. Acquisizione", "Acquisire studi di commercialisti già dipendenti da QUANTO.", "Il ricarico che lo studio applica alle PMI clienti diventa tutto guadagno; i costi si abbassano perché tutti gli strumenti sono già di QUANTO e gratuiti."]], [36, 84, 50])
    P("**Cosa implica per il prodotto oggi.** Strumenti gratuiti e sempre più larghi; dati dello studio separati per cliente (i «lavori»); template e Confronto che migliorano con l'uso dello studio; un assistente che esegue i passaggi al posto dell'utente. "
      "Tutto questo esiste per le due missioni (budget e allocazione); le tappe 2-4 non sono iniziate. Stato: [[VISIONE]].")
    NOTE("Condizione da verificare prima della tappa 4: l'ordinamento delle professioni regolamentate pone limiti alla proprietà degli studi da parte di soggetti che non sono professionisti (per esempio per le società tra professionisti). Non è una decisione presa: è un vincolo noto da chiarire.")
    H2("MODULO 19 — Il team interno e la revisione delle regole  [[PARZIALE]]")
    P("Le regole dei bandi, le tabelle ufficiali della Fonte B e ogni revisione le cura **un team interno di QUANTO**, dal Quartier Generale: coda di revisione dei disaccordi, regole e requisiti modificabili, rilettura dei documenti, tabelle con attestazione della fonte e, per ogni bando, la **scheda di revisione** "
      "(cosa dicono i documenti, cosa non dicono, quali parole cercare, dove compaiono, come verificare, quale controllo resta spento). Non esiste, e non è previsto, un canale verso consulenti esterni.")
    P("Stato: gli strumenti ci sono e funzionano; il team interno è da costituire (oggi opera il titolare) e l'audit di calibrazione delle regole già pubblicate è da fare.")
    # ================================================================================================ PARTE V
    H1("PARTE V — GO-TO-MARKET")
    H2("MODULO 20 — Target e segmentazione  [[DA FARE]]")
    P("Il bersaglio è **esplicito: studi di commercialisti e boutique di finanza agevolata**, che usano QUANTO per più clienti (un lavoro per cliente) e ne traggono il vantaggio del consiglio basato sui propri template. CFO di PMI e associazioni restano un canale per la Missione Due; i bandifici un canale secondario. "
      "La procedura guidata, il profilo per lavoro e l'assistente rendono credibile anche l'uso diretto da parte di un'impresa senza intermediari. Nessuna attività commerciale è stata avviata.")
    H2("MODULO 21 — Canali e modello economico  [[DA FARE]]")
    P("Vendita guidata dalla prova: il percorso (Modulo 4) può essere mostrato su dati del prospect caricati dal vivo. **Gli strumenti di QUANTO sono gratuiti per gli studi**: l'obiettivo non è l'abbonamento ma la dipendenza (Modulo 18). Il pricing a tre livelli della v2.1 (abbonamento, crediti, success fee) non è la strategia attuale. "
      "Esiste solo un contatore a crediti (100 per ciclo, un credito per controllo del budget, rinnovo dopo 364 giorni) come anteprima e limite d'uso dello studio: i pagamenti sono simulati e nessun conto è addebitato. "
      "La registrazione è libera (account gratuito, nessuna e-mail di conferma): va chiusa o protetta prima di un lancio.")
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
       ["Bandi", "Ogni bando in memoria: documenti con testo e file originale, regole (anche in disaccordo, modificabili), requisiti (riclassificabili), scheda di revisione, linea di finanziamento, utilizzi; rilettura, esportazione ZIP, eliminazione (con lapide per i curati e ripristino dei predefiniti); qui, e solo qui, si carica a mano il testo o il PDF di un bando."],
       ["Catalogo (nuova)", "Tutte le voci del catalogo con descrizione e caratteristiche, ricerca e filtro (con scheda letta / da leggere), contatori (voci, schede lette, da leggere, con scadenza futura, già studiate) e pulsante che legge in sequenza tutte le schede mancanti."],
       ["Manuale (nuova)", "Il manuale dei processi di QUANTO (versione 4.0, standard RICERCA-v2): testo a schermo e **PDF scaricabile**, costruito dallo stesso testo."],
       ["Tabelle ufficiali", "Fonte B: caricamento da file, bozze, pubblicazione con attestazione della fonte, versioni; modelli di file per tipo."],
       ["Banca pattern", "Importazione CSV con fonte obbligatoria, budget in banca e archetipi."],
       ["Utenti", "Creazione utenti, cambio ruolo, attivazione, reimpostazione password, sblocco."],
       ["Fascicoli", "Cartella di ogni progetto: validazioni, documenti, cronologia, registrazione."],
       ["Documenti", "Bandi caricati, importazioni, esportazioni (con impronta e dimensione)."],
       ["Database", "Tutte le tabelle in sola lettura, righe paginate, esportazione CSV, eliminazione di righe o svuotamento con conferma digitata (il registro firmato è escluso). Comprende anche i profili e i bilanci delle aziende."]], [30, 140])

    H2("MODULO 24 — Quanto vale un bando in euro, il potenziale massimo e il de minimis  [[PARZIALE]]")
    P("Domanda da cui è nato il modulo: «perché per la maggior parte dei bandi non c'è un importo? I dati ci sono, altrimenti il bando non esisterebbe». Risposta: **ogni bando adatto deve essere calcolabile**, con un solo criterio: ogni numero viene da una fonte ufficiale o da una formula dichiarata, e le ipotesi si scrivono accanto al numero.")
    H3("24.1 Da dove viene la percentuale (in quest'ordine)")
    T([["Livello", "Cosa è", "Esempio"],
       ["1. Regola pubblicata", "Il bando dichiara «contributo pari al N% delle spese»: valore unico.", "Investimenti Sostenibili 4.0: 75% sui beni strumentali"],
       ["2. Modello del bando (bandi curati)", "Formula con fonti e ipotesi, per i casi in cui l'aiuto non è una semplice percentuale.", "Tabella sotto"],
       ["3. Tabella del testo ufficiale", "Intensità per dimensione d'impresa: la prima percentuale è la **base**, la più alta il **massimo** con tutte le maggiorazioni; si usano le sole righe che riguardano la dimensione dell'azienda, ognuna con la frase e il documento da cui viene.", "«Micro-piccole imprese 25% 20% 15% 60%» → base 25%, massimo 60%: su 1.965.919 € di spesa, da 491.480 € a 1.179.552 €"]], [36, 76, 58])
    T([["Bando curato", "Natura del valore", "Come si calcola", "Ipotesi dichiarata"],
       ["Nuova Sabatini", "Contributo sugli interessi", "Interessi convenzionali di un finanziamento a 5 anni al 2,75% (3,575% per 4.0 e green), rate semestrali costanti: 7,66% (10,0%) dell'investimento", "Si finanzia l'intero investimento; il metodo ufficiale è nella circolare MIMIT"],
       ["Transizione 5.0 (iperammortamento)", "Risparmio fiscale", "Maggiorazione (180% fino a 2,5 milioni) × aliquota IRES del 24% = 43,2% dei beni", "Serve reddito imponibile capiente e beni 4.0"],
       ["Fondo 394/81 (SIMEST)", "Fondo perduto, in de minimis", "10% (con almeno un requisito) o 20% (imprese energivore)", "Il finanziamento copre le spese; il fondo perduto rientra nel de minimis"],
       ["Horizon Europe", "Fondo perduto", "Dal 70% (innovazione, imprese a scopo di lucro) al 100% (ricerca)", "Massimo teorico: solo la parte di spesa che entra in un progetto è finanziata"],
       ["Fondo di Garanzia PMI", "Garanzia (non è un guadagno)", "50% (liquidità) o 80% (investimenti) del finanziamento bancario", "L'investimento è finanziato per intero con un prestito"]], [34, 30, 66, 40])
    P("Il valore si calcola sulla spesa prevista dell'anno nelle categorie ammesse e non supera il tetto per progetto, se il bando ne ha uno. La **garanzia** non si somma ai contributi: si calcola solo l'importo garantibile (per esempio 78.861-126.178 € su un finanziamento di 157.722 €). "
      "Se nessuna fonte dà una percentuale il bando resta senza importo e lo dice: questo è il limite per cui il modulo è [[PARZIALE]].")
    H3("24.2 Il potenziale massimo e il bilancio ricostruito")
    P("Il potenziale massimo combina **tutti i bandi adatti** nel piano (Modulo 12) e risponde a: «se l'azienda ottenesse tutti i bandi a cui può accedere, quanto coprirebbe in un anno?». Si calcola due volte, con le percentuali prudenti e con quelle massime, e si mostra l'intervallo. "
      "Esempio dell'azienda di prova: da 1.307.746 € a 1.863.062 € coperti (66,5% e oltre) con 8 bandi, mentre sommando i bandi uno per uno si arriverebbe a 2.394.221 €: la differenza è la stessa spesa che non si può far pagare due volte. "
      "Il **bilancio ricostruito** è un grafico: per ogni categoria di spesa, quanto copre ciascun bando e quanto resta a carico. È un massimo teorico, e il riquadro lo ricorda con una nota da riportare al cliente.")
    H3("24.3 Come leggere i numeri")
    P("Sotto i risultati c'è sempre il riquadro «Come leggere questi numeri»: **Coperto dai bandi** (quanto delle spese pagano i bandi; due cifre = prudente e massimo), **Su una spesa di** (la spesa prevista), **Quota coperta** (il rapporto), **Resta a tuo carico** (il resto), **Da solo** (cosa darebbe il bando se fosse l'unico), "
      "**Nel piano insieme** (quanto serve davvero quando lavorano insieme), **non serve** (le sue spese sono già coperte da un bando più conveniente o il bando ha raggiunto il suo tetto: non è scartato e rientra se i dati cambiano). Gli scarti di pochi centesimi tra due cifre sono arrotondamenti: il piano lavora in centesimi interi, sempre per difetto. "
      "Tutti i bandi del piano compaiono in legenda e in tabella, ognuno con il suo colore (12 colori), anche quelli che non portano euro.")
    H3("24.4 Il de minimis")
    P("**Cos'è.** Un aiuto pubblico è normalmente vietato dalle regole europee sulla concorrenza; il de minimis (Reg. UE 2023/2831) è l'eccezione per gli aiuti piccoli: un'impresa unica, cioè l'azienda più le società collegate, può riceverne al massimo **300.000 € in tre anni mobili**. Conta solo per i bandi che lo dichiarano; gli altri non lo toccano.")
    B(["**Quali bandi sono in de minimis.** Lo dice solo una fonte: la scheda curata del bando oppure il testo ufficiale letto, che cita il regime o i suoi regolamenti (2023/2831, 1407/2013). Se il testo lo cita ma lo nega esplicitamente («non rientra nel regime de minimis») il bando non conta e la frase si mostra. Le fonti secondarie non servono a questo. Ogni bando riconosciuto porta l'etichetta «In de minimis» con la frase da cui viene. Un bando di cui nessuna fonte parla non è segnato.",
       "**Quanto ne resta all'azienda.** QUANTO non legge il Registro Nazionale degli Aiuti, quindi non inserisce un numero inventato: lo calcola da ciò che l'azienda ha dichiarato nel profilo (voce «Contributi pubblici ricevuti nell'esercizio» dei tre esercizi che precedono l'anno del piano). Per prudenza ogni contributo dichiarato conta come de minimis. Residuo = 300.000 € − somma, mai sotto zero.",
       "**La base della stima è sempre scritta:** **dato dichiarato** (tutti e tre gli anni compilati), **dato parziale** (alcuni anni; per gli altri non si sottrae nulla) o **ipotesi** (nessun anno compilato: si assume che non ci siano aiuti; non è un dato verificato).",
       "**Quanto ne usa il piano.** Il riquadro mostra anche il de minimis che il piano usa davvero: se ne usa 17.000 €, resta valido anche se l'azienda ne ha già ricevuti fino a 283.000 €. Il campo si può correggere a mano; l'assistente raccoglie i dati e spiega dove trovarli (visura aiuti RNA, provvedimenti di concessione, dichiarazioni firmate; per un gruppo si sommano le società collegate).",
       "**Il piano non si blocca mai** in attesa di questo dato. [[PARZIALE]]: senza il dato del cliente il residuo è un'ipotesi dichiarata; un collegamento automatico al registro non esiste."])

    H2("MODULO 25 — Lo studio, i lavori e il Confronto a template  [[FATTO]]")
    H3("25.1 Lo studio e i lavori")
    P("L'account è **dello studio**: nome, password e crediti valgono per tutto lo studio. Ogni azienda cliente è un **lavoro**: sotto il Profilo si aprono tanti lavori quanti sono i clienti, e ognuno ha il suo profilo, i suoi bilanci, i suoi documenti, il suo modello di previsione e i suoi risultati salvati. "
      "Il lavoro attivo si sceglie dal selettore in cima al menu e **tutte le pagine mostrano i dati di quell'azienda e di nessun'altra**: ogni dato vive con la chiave «studio + lavoro» (intestazione `X-Client-Id` su ogni chiamata). I dati già presenti prima di questa funzione sono stati convertiti nel primo lavoro (migrazione 15). "
      "Eliminare un lavoro cancella i suoi dati (si riscrive il nome per confermare), ma i template di budget restano allo studio.")
    P("**Cosa si salva da solo, per lavoro** (tabella `client_state`): anno e percentuali dell'Allocazione, bandi inclusi nel piano, obiettivo e de minimis; il budget con il bando scelto e il risultato del controllo; motore, bando e dati del Confronto. Cambiando pagina si ritrova tutto com'era (le pagine già visitate restano montate) e anche chiudendo e riaprendo l'app.")
    H3("25.2 Il profilo dello studio")
    T([["Sezione", "Contenuto"],
       ["Lavori", "Le aziende clienti, il lavoro attivo, apertura, rinomina ed eliminazione di un lavoro."],
       ["Studio e dati", "Nome, ruolo, ragione sociale e partita IVA dello studio, telefono. L'e-mail è l'identificativo di accesso e non si cambia da qui."],
       ["Sicurezza", "Cambio password con le regole in vista, uscita da tutti i dispositivi, ultimi accessi."],
       ["Piano e dati", "Crediti dello studio, operazioni recenti, esportazione di tutti i dati dello studio in un file, eliminazione dell'account con password ed e-mail di conferma."]], [30, 140])
    H3("25.3 Il Confronto: i template e come l'algoritmo impara")
    P("Il Confronto risponde a una domanda da commercialista: «per un'azienda di questa nicchia che sceglie questo bando, com'è fatto di solito il budget che vince?». Un **template** è una scheda con la **nicchia** (codice ATECO: le prime due cifre e il settore), il **bando**, la **ripartizione in otto voci** (personale, beni strumentali, consulenze, ricerca e sviluppo, spese generali, formazione, comunicazione, altro; somma 100%), l'**esito** (bozza, presentato, ammesso, non ammesso, con punteggio facoltativo), dimensione, Regione, importo e una nota.")
    T([["Passaggio", "Regola"],
       ["Chi somiglia a chi", "Sei livelli, dal più preciso: stessa nicchia e bando; stesso settore e bando; stesso bando; stessa nicchia; stesso settore; tutti. Si usa il primo livello con almeno **3 template**; se nessuno li ha, dice «ancora pochi dati»."],
       ["Chi conta di più", "Media pesata per esito: ammesso 3, presentato 1,5, bozza 1, non ammesso 0,25. Esempio: quote consulenze 20% (ammesso), 5% (non ammesso), 13% (bozza) → (3×20 + 0,25×5 + 1×13) / 4,25 = 17,5%; senza pesi 12,7%."],
       ["Fiducia", "ALTA se si usa il primo livello con almeno 8 template; MEDIA se il livello è 1, 2 o 3 (c'è un bando preciso); BASSA se solo livelli generici."],
       ["Intervallo tipico", "Per ogni voce, media ± la dispersione dei template: dove c'è più libertà e dove no."],
       ["Stili di budget", "Con almeno 6 template, k-means a seme fisso (ripetibile): gruppi di budget simili e quanti di ciascuno hanno vinto; se i gruppi non sono ben separati non si inventano stili."],
       ["Auto-miglioramento", "Non c'è addestramento notturno né scatola nera: il consiglio si ricalcola ogni volta da tutti i template, quindi migliora a ogni dato nuovo (più template → livello più preciso; un esito «ammesso» fa salire il peso da 1,5 a 3 e sposta il consiglio)."],
       ["Misura onesta", "Salvando un template si registra la distanza dal consiglio di quel momento (metà della somma degli scarti, 0-100%). Con almeno 5 esiti noti tra i budget vicini (scarto fino al 10%) e almeno 5 tra gli altri si mostra se i vicini vincono più spesso; prima lo dice."],
       ["Riproducibile", "Ogni consiglio porta l'impronta dei template usati: stessi template, stesso consiglio."]], [34, 136])
    H3("25.4 Due motori e privacy")
    B(["**Motore collettivo:** lavora su tutti i template della piattaforma. Ogni template salvato entra **sempre** nel collettivo, in forma anonima: così l'algoritmo si auto-migliora con i dati di tutti.",
       "**Motore interno:** lavora solo sui template dello studio, per vedere come lavora il proprio studio senza influenze esterne. Lo studio sceglie con quale motore confrontarsi.",
       "**Elenco sempre visibile:** i template dello studio, con il cliente da cui vengono; lì si aggiorna l'esito.",
       "**Cosa contiene un template:** solo nicchia, bando, Regione, dimensione, quote ed esito; ragione sociale e partita IVA non vengono salvate. La nota libera resta dello studio e l'algoritmo non la usa. Dei template degli altri studi si usano solo gruppi di **almeno 3**: sotto, nessuno può risalire a un singolo cliente.",
       "**Mappa nicchie-bandi:** per ogni nicchia, quali bandi hanno scelto i clienti, con ripartizione media, presentati e ammessi. Nel Confronto compaiono solo i bandi affini al lavoro attivo (stesso criterio dell'Allocazione); chi ha partecipato a un bando diverso lo cerca per nome."])
    P("**Stato [[PARZIALE]]:** il meccanismo è completo e testato; la qualità del consiglio dipende dai template reali che gli studi salvano. Con pochi dati il Confronto lo dice invece di inventare. Il consiglio è una statistica sulla struttura della spesa, non una previsione di esito: non sostituisce la verifica dei requisiti formali.")

    H2("MODULO 26 — L'assistente guidato  [[FATTO]]")
    P("Dove l'utente dovrebbe inserire dati o muoversi nell'app, può **affidare il lavoro all'assistente**. L'assistente non è un chatbot e non usa modelli linguistici: è un esecutore di procedure dichiarate, che compie le stesse azioni che farebbe l'utente e si ferma solo quando gli serve un dato che non c'è.")
    H3("26.1 Come si presenta")
    B(["Si avvia dal pulsante **Assistente** nel menu, da un suggerimento o scrivendo cosa si vuole fare nella chat. L'assistente capisce la richiesta con parole chiave («budget», «potenziale massimo», «aiuti ricevuti», «dati dell'azienda»): non è un modello linguistico e se non capisce lo dice, proponendo le attività possibili.",
       "È una **scena a tutto schermo**: a sinistra l'app, ridotta in una scheda con gli angoli arrotondati; sotto la scheda due pillole (il passo in corso con il suo avanzamento e il pulsante «Interrompi»); a destra una colonna di vetro con la **chat**, i suggerimenti e la barra di scrittura in basso. Lo sfondo è un gradiente giallo, quello del marchio, con superfici di vetro.",
       "Nella chat compare l'**elenco di tutti i passaggi**, che si spuntano man mano (in corso, in attesa di un dato, fatto, saltato, non riuscito) con il risultato di ciascuno; le risposte dell'utente restano come messaggi.",
       "Mentre l'assistente lavora l'app a sinistra si muove da sola (cambia pagina, salva, calcola) e non si può toccare; quando serve un valore compare nella chat un riquadro con la domanda, e per ogni campo spiega in parole semplici **cos'è, cosa scrivere, perché serve, dove si trova e un esempio**. Si può rispondere, saltare, scrivere «annulla» o premere «Interrompi» in qualsiasi momento."])
    H3("26.2 Le attività")
    T([["Attività", "Passaggi"],
       ["Calcolare il potenziale massimo", "Controlla i dati dell'azienda (chiede solo quelli che mancano: dati della visura, costi dell'ultimo bilancio) → apre l'Allocazione → stima l'anno e cerca i bandi adatti → verifica il de minimis (chiede gli aiuti ricevuti se serve) → mostra il risultato con le cifre."],
       ["Preparare la bozza di budget", "Controlla i dati → sceglie il bando (solo bandi con regole lette) → chiede la quota di progetto → crea la bozza dall'azienda (organico persona per persona, spese per voce con la loro fonte) → chiede solo ciò che manca davvero (se nei documenti non ci sono persone le chiede **una per una**: ruolo, CCNL, livello, RAL, quota di tempo, mesi, documento) → controlla il budget con i 60 criteri e riferisce voci ammesse, ridotte, respinte, in attesa."],
       ["Dichiarare gli aiuti già ricevuti", "Apre il profilo → chiede i contributi pubblici degli ultimi tre anni (con «Nessuno» come risposta rapida) → li salva → ricalcola l'Allocazione e riferisce il nuovo residuo."],
       ["Completare i dati dell'azienda", "Apre il profilo → chiede i dati che mancano con la spiegazione di ognuno (partita IVA, forma giuridica, ATECO, regione, dipendenti, start-up, bilancio) → li salva."]], [42, 128])
    H3("26.3 Cosa non fa")
    B(["**Non inventa dati:** usa solo ciò che l'utente scrive o che è già nel profilo. Un valore lasciato vuoto resta vuoto.",
       "**Non sceglie al posto dell'utente quando una tabella non esiste:** se nel sistema non ci sono contratti collettivi (CCNL) pubblicati lo dice e salta il passaggio del personale, senza assumerne uno.",
       "**Non fa nulla di irreversibile da solo:** non elimina dati e non registra impronte; compie azioni di inserimento, salvataggio e calcolo."])
    H3("26.4 Come è costruito")
    P("Il pannello e la macchina dei passaggi stanno in `frontend/src/assistant/AssistantContext.jsx`; le procedure in `tasks.js` (ogni attività dichiara in anticipo i suoi passaggi e li esegue uno alla volta). L'app espone all'assistente un ponte con le sole azioni dell'utente (cambiare pagina, scegliere il bando, mettere voci nel budget, controllarlo), "
      "e le pagine comunicano con eventi (`quanto-assistant`, `quanto-recalc`, `quanto-allocation-result`, `quanto-profile-changed`). I calcoli restano sul server: l'assistente non calcola importi.")
    P("**Stato:** provato in locale su un database temporaneo con l'azienda di prova (potenziale massimo, bozza di budget con una persona e controllo, dichiarazione degli aiuti); la **verifica online dopo il rilascio resta da fare**. Il passaggio del personale dipende dalle tabelle CCNL pubblicate in Fonte B.")

    H2("MODULO 27 — Dati e database  [[FATTO]]")
    T([["Tabella", "Contenuto"],
       ["bandi", "Una riga per bando o voce del catalogo: identificativo, nome ufficiale, ente, scadenza, indirizzo della scheda, stato del catalogo, stato dell'estrazione, richieste dei clienti, descrizione, caratteristiche (JSON) e data di lettura della scheda"],
       ["bando_meta · rules · requirements", "Descrizione curata dei bandi predefiniti; regole numeriche con origine e stato (pubblicata, in revisione); requisiti con tema, tipo, controlli collegati, cifre strutturate"],
       ["bando_sources · bando_files · bando_tombstones", "Testo e metadati di ogni documento di fonte; file originali; lapidi dei bandi eliminati"],
       ["fonte_b_datasets · _ccnl · _params · _amort · _benchmarks", "Fonte B versionata per data, con provenienza"],
       ["client_documents · client_document_fields", "Documenti dei clienti cifrati e relativi campi con confidenza, stato, token, riga di prova"],
       ["company_profiles · company_financials", "Profilo e bilanci per esercizio di ogni lavoro, con provenienza di ogni valore; compresi i contributi pubblici dichiarati (de minimis)"],
       ["forecast_templates · budget_templates", "Modello di previsione dei costi e dei ricavi di un lavoro; template di budget dello studio con nicchia, bando, quote ed esito"],
       ["clients · client_state", "I lavori (aziende clienti) dello studio e le scelte salvate per ciascuno (Allocazione, Budget, Confronto)"],
       ["funding_lines", "Linee di finanziamento per l'allocazione, ricavate dai bandi o indicate da una persona"],
       ["pattern_budgets · pattern_archetypes", "Banca dei pattern e archetipi calcolati"],
       ["users", "Account con hash scrypt, ruolo, tentativi falliti, versione del token"],
       ["events · runs · documents", "Timeline, esecuzioni salvate con richiesta e risposta complete, documenti lavorati"],
       ["anchors", "Registro firmato append-only"]], [60, 110])
    P(f"Contenuto online il 4 ottobre 2026: {FACTS['bandi']} bandi, {FACTS['rules']} regole, {FACTS['requirements']} requisiti, {FACTS['sources']} fonti, {FACTS['files']} file originali, {FACTS['events']} eventi, {FACTS['runs']} esecuzioni, {FACTS['documents']} documenti lavorati, 1 utente (il titolare), 1 profilo con 3 esercizi, 14 documenti del cliente di prova, 1 registrazione. "
      "Alla v2.1 di partenza il database era in memoria volatile; oggi i dati sopravvivono al riavvio del server.")

    H2("MODULO 28 — Cosa fa l'app a ogni azione dell'utente  [[FATTO]]")
    T([["Azione", "Cosa succede, in ordine"],
       ["Registrarsi / accedere", "Crea l'account USER (scrypt) o verifica la password con tempo costante; emette un token di 8 ore con versione; nella timeline compare l'accesso."],
       ["Caricare un documento", "Controlli (tipo noto, non vuoto, massimo 15 MB, nome ripulito, PDF per i tipi letti) → cifratura AES-256-GCM → lettura del testo (o OCR se disponibile) → parser del tipo → ogni campo con confidenza e stato → dati personali in token → salvataggio → sincronizzazione del profilo."],
       ["Confermare o correggere un campo", "Il campo diventa confermato o corretto, entra nei calcoli, il profilo si ricalcola. Se una busta paga ha la RAL stimata, la conferma abilita la voce di personale."],
       ["Rispondere alla domanda sulla start-up", "Scrive un valore MANUAL nel profilo; la completezza sale; l'abbinamento ai bandi usa subito la risposta."],
       ["Calcolare la stima e cercare i bandi", "Legge il profilo, proietta le cinque categorie con le variazioni dell'utente, valuta uno per uno i bandi con regole o requisiti, ordina il catalogo non studiato per affinità; registra l'evento con i conteggi."],
       ["Studiare un bando", "Processo standard (Modulo 9.1); al termine ricalcola l'abbinamento e porta alla scheda del bando con il rapporto di lettura."],
       ["Creare la bozza di budget", "Legge organico, budget, piano degli investimenti e bilancio; tiene le categorie e le voci ammesse, scala per la quota, riduce ai tetti; il personale entra persona per persona; le voci TPL-* sostituiscono la bozza precedente."],
       ["Controllare il budget", "Le sole voci complete (il personale senza RAL è escluso e segnalato) vanno al motore: criteri per voce → criteri sul budget intero → hash → Merkle → riepilogo. Si salvano l'esecuzione, l'evento e un credito. Esito: punteggio, ammesso, escluso o ridotto, motivi."],
       ["Ripartire in WP", "Le voci ammesse (importi approvati) e i WP con i loro vincoli vanno al risolutore; controlli di fattibilità → MILP → centesimi → verifica esatta → report per WP, controlli e CSV. Spostando una voce a mano il calcolo riparte."],
       ["Aprire o scaricare un documento", "Il file viene decifrato dal server solo per il proprietario; PDF, immagini e testo si guardano in una finestra della pagina, gli altri si scaricano. «Scarica tutti» ripete l'operazione per ogni file e compone lo ZIP nel browser."],
       ["Esportare", "Excel o PDF con CEP-ID e QR verso la verifica."],
       ["Registrare l'impronta", "Aggiunge una voce firmata Ed25519 alla catena; il trigger impedisce di cambiarla."],
       ["Verificare", "Confronta l'impronta, controlla la firma e la catena; «ricalcola dai dati» rifà tutto da zero; la manomissione simulata deve dare «impronta diversa»."],
       ["Calcolare il piano", "Una richiesta con le spese stimate e le linee dei bandi inclusi (due volte: percentuali prudenti e massime); un solo fondo perduto per spesa; fondi in ordine canonico; MILP; verifica esatta in centesimi; riepilogo con cifre controllate; evento e webhook."],
       ["Chiedere all'assistente", "Si apre il pannello a destra e l'app si riduce; l'assistente esegue i passaggi dichiarati dell'attività scelta (cambia pagina, salva, calcola) e si ferma a chiedere solo i dati che mancano; ogni salvataggio passa dalle stesse chiamate dell'utente."],
       ["Cambiare lavoro", "Il lavoro attivo cambia: ogni chiamata successiva porta la sua chiave, le pagine si ricaricano con i dati di quell'azienda e si ritrova il budget e le scelte salvate per quel lavoro."],
       ["Cambiare password", "Aggiorna l'hash e la versione del token: tutte le sessioni aperte decadono."]], [40, 130])

    H2("MODULO 29 — Esito del test demo del 4 ottobre 2026 e decisioni prese")
    NOTE("Il test è stato eseguito sul sistema online il 4 ottobre. Da allora la demo è stata tolta dall'applicazione e l'interfaccia è cambiata (menu laterale, lavori, assistente): i difetti sotto elencati restano corretti, la cronologia è nell'Appendice B.")
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
       "La bozza di budget contiene voci che il motore mette «in attesa» (CUP e milestone mancanti, tabella del contratto in Fonte B per un livello non pubblicato): è corretto, e la bozza lo dice nell'elenco «cosa manca»; un budget non diventa ammissibile finché non si aggiungono quei dati.",
       "Lo studio di un bando dal catalogo con nome generico può includere documenti di bandi «fratelli» dello stesso ente (rilevanza lessicale). Il titolo ufficiale riduce il problema, non lo elimina.",
       "Sul sito di produzione resta una registrazione di prova nel registro (n. 1), che per costruzione non si può cancellare; il progetto «DEMO-SHAPE» e le altre tracce della demo sono state eliminate dalla migrazione 13."])

    H2("MODULO 30 — Cosa manca per far funzionare QUANTO al 100%")
    H3("Dati e decisioni che servono dal titolare")
    T([["Cosa", "Perché serve", "Chi"],
       ["Chiave del provider del modello linguistico (e conferma del provider)", "Accende lo Stadio 3 (più passaggi) e il riepilogo scritto dal modello; oggi tutto è template.", "Titolare"],
       ["Dataset dei pattern vincenti (graduatorie pubbliche, dati del pilota con consenso)", "Oggi 5 bilanci di società quotate come proxy; servono almeno 6 budget per categoria per avere archetipi veri.", "Titolare / pilota"],
       ["Tabelle ufficiali: CCNL mancanti, benchmark di prezzo e di tariffa, aliquote d'ammortamento da fonte primaria", "Criteri 22 e 33 spenti; aliquote da fonte secondaria.", "Titolare con il team interno"],
       ["Motore OCR per le scansioni (adattatore cloud)", "Tesseract non gira su Vercel: oggi le scansioni vengono rifiutate.", "Decisione di provider"],
       ["Regione del database e documenti legali (DPA, informativa, valutazione d'impatto)", "Condizione per clienti reali.", "Titolare / legale"],
       ["Decisione sulla registrazione libera e sul pagamento reale", "Oggi chiunque può iscriversi gratis; i crediti sono simulati.", "Titolare"]], [60, 80, 30])
    H3("Lavoro di sviluppo ancora aperto")
    B(["**Regole numeriche dai bandi:** oggi circa 24 chiavi note producono regole; gli altri tetti vivono come cifre nei requisiti di tipo LIMITE. Prossimo passo: mapparli su nuove chiavi del motore, con revisione.",
       "**Rilevanza dei documenti:** da lessicale a vettoriale o con controllo sull'ente, per evitare la contaminazione tra bandi dello stesso ente (Modulo 9.1).",
       "**Audit di calibrazione** e relativo evento `rule.audit_flagged`; **Report di Asseverazione** in PDF; pubblicazione periodica di `head_hash` del registro.",
       "**WP: vincoli letti dal bando.** La ripartizione c'è (Modulo 2.1) ma i limiti dei WP li scrive l'utente; leggerli dal testo del bando è possibile solo dove il bando li dichiara.",
       "**Bozza di budget per persona:** chiusa il 14/10/2026: l'organico si legge dal registro del personale e dalle buste paga; l'assistente chiede le persone una per una solo se nei documenti non ci sono.",
       "**Connettori automatici** per la Fonte B; **registri IVA e piano dei conti** come tipi di documento.",
       "**Integrazioni ERP** (Zucchetti, TeamSystem): l'API è pronta (OAuth 2.0 + HMAC), le integrazioni non esistono.",
       "**Test dei processi sul campo:** nessuna pratica reale è stata presentata; per questo non esiste alcuna metrica di successo o di clawback.",
       "**Verifica online dell'ultimo rilascio:** il 12 ottobre si è potuto controllare solo ciò che non richiede l'accesso (versione del sito, registro firmato). Restano da provare online con i dati reali dello studio assistente, de minimis, legenda dei numeri e Confronto, e da rileggere i contatori del Quartier Generale.",
       "**Collegamento al Registro Nazionale degli Aiuti** per il de minimis: oggi il residuo si stima dagli aiuti dichiarati e dice su cosa si regge.",
       "**Tabelle CCNL online:** il passaggio del personale dell'assistente dipende dai contratti pubblicati in Fonte B (3 all'ultima lettura).",
       "**Bandi senza percentuale nei testi letti:** restano senza importo finché una fonte ufficiale non la dichiara; si possono far studiare di nuovo."])
    H3("Fasi della roadmap")
    T([["Fase", "Contenuto", "Stato"],
       ["1", "Motore, console, fonti A/B/C, allocazione, demo, profilo", "[[FATTO]] in gran parte; chiusura con i dati del titolare (sopra)"],
       ["2", "Registro crittografico e Auditor Portal", "[[FATTO]] (senza blockchain)"],
       ["3", "Mercato italiano degli studi: tutta la fetta di commercialisti e boutique di finanza agevolata, con strumenti gratuiti", "[[VISIONE]]"],
       ["4", "Mercati esteri: gli stessi strumenti con regole e tabelle locali curate dal team interno", "[[VISIONE]]"],
       ["5", "Dipendenza: strumenti per circa il 90% delle funzioni di uno studio", "[[VISIONE]]"],
       ["6", "Acquisizione di studi già dipendenti da QUANTO", "[[VISIONE]]"]], [14, 120, 36])
    story.append(PageBreak())

    # ================================================================================================ EXECUTIVE SUMMARY
    H2("MODULO 31 — Voci di spesa, tutti i documenti, budget dall'azienda e dall'allocazione (14 ottobre 2026)  [[FATTO]]")
    P("Quattro cambiamenti strutturali, fatti insieme perché si reggono a vicenda. Il cliente di prova ha tutti i dati; i clienti con documenti incompleti si proveranno dopo: oggi la bozza lo dice (elenco «cosa manca») e non inventa.")
    P("**31.1 Le voci di spesa, oltre le cinque categorie.** Personale, beni strumentali, consulenze, spese generali e formazione restano le categorie generali, ma sotto ci sono **voci di spesa** (oltre 50, con codice stabile): affitti, spese condominiali, energia, telefonia, assicurazioni, "
      "manutenzioni, trasferte, rappresentanza, pubblicità, licenze software, servizi cloud, consulenze legali/fiscali/tecniche, brevetti e marchi, certificazioni, corsi, seminari, imposte e tasse e così via. "
      "Ogni riga dei bilanci e dei fogli Excel ha la sua voce (con le stesse parole con cui compare nel documento); se nessuna parola corrisponde si usa la voce generica della categoria, mai una voce inventata. "
      "Un **bando** può escludere per nome una voce anche dentro una categoria ammessa: il testo ufficiale è letto frase per frase, una voce è esclusa solo se la frase dice che non è ammissibile (frasi ambigue, o dette nei due sensi, non contano); "
      "la regola `excluded_expense_types` ha la frase come prova, si vede nella scheda del bando (scheda «Voci di spesa»), il controllo 16 respinge la voce, la stima del contributo la toglie dalla base e l'allocazione non la copre mai con quel fondo.")
    P("*Esempio semplice.* La riga di bilancio «Affitto della sede di via Garibaldi» diventa la voce «Affitti e locazioni» (categoria spese generali). Se un bando dice «non sono ammissibili le spese di locazione», quella voce non entra nel budget né nel contributo stimato, e la scheda del bando mostra la frase.")
    P("**31.2 Tutti i documenti.** I fogli Excel dell'azienda non sono più solo archiviati: si riconoscono dalle intestazioni delle colonne e si leggono. Registro del personale (persona per persona: livello, contratto, ore, RAL; nome e codice fiscale non entrano mai, resta il token), libro cespiti con il piano di ammortamento, "
      "registro delle fatture ricevute (spese per voce e anno), registro degli aiuti, budget dell'azienda per conto, piano degli investimenti e piano delle assunzioni. Un foglio che non si riconosce resta archiviato. Ogni dato letto dice da quale foglio e riga viene; nel Profilo c'è «Cosa ho letto dai documenti» "
      "(spese per voce, organico, beni) e nella pagina dei documenti il dettaglio di ogni foglio.")
    P("*Esempio semplice.* Dal foglio Excel dell'organico QUANTO legge «sviluppatore senior, livello 3, RAL 41.300 €, 40 ore»; dal libro cespiti legge che sei computer sono ammortizzati al 100%; dalle fatture ricevute somma 65.663 € di affitti. Nome e codice fiscale non compaiono mai: resta un codice anonimo.")
    P("**31.3 Il budget dalla previsione.** Vedi la bozza di budget (Modulo 9): budget dell'azienda → piano degli investimenti → previsione dal bilancio, nessun ammortamento passato come spesa futura, confronto tra budget e previsione quando differiscono.")
    P("*Esempio semplice.* Il bilancio 2025 dice 190.000 € di spese generali; il budget 2026 che l'azienda ha caricato dice 210.000 €; QUANTO usa 210.000 € e scrive che sono +7,7% rispetto alla stima dal bilancio. L'ammortamento di 54.100 € non entra: sono beni già comprati.")
    P("**31.4 Dall'allocazione ai budget dei bandi (`POST /allocation/budgets`).** Dopo l'allocazione su uno o più bandi si ricava il **budget di ogni bando**: per ogni spesa, il costo su cui il bando calcola il suo contributo è «contributo coperto / intensità»; il personale si divide tra i progetti senza sovrapporsi "
      "(la somma delle quote di tempo di ogni persona su tutti i budget non supera il 100%); le spese finanziate da due bandi compaiono in entrambi dichiarando l'altro contributo (`funding_ids`, `other_aid_eur`), che è ciò che verificano i controlli 47 e 48. "
      "L'allocazione stessa rispetta ora anche le voci escluse per nome e l'aiuto cumulato massimo sulla stessa spesa. Ogni budget è controllato con i 60 criteri del suo bando e il gruppo con sei verifiche incrociate: nessuna spesa coperta oltre il suo importo, nessuna persona oltre il 100% del tempo, nessun cumulo vietato, "
      "aiuto cumulato entro il massimo, de minimis entro il plafond, ogni budget ottiene il contributo previsto (altrimenti si scrive perché il motore ne ammette meno). Il commercialista apre i budget uno alla volta nella pagina Budget (barra dei budget dell'allocazione) e li modifica; il gruppo si salva con il lavoro.")
    P("*Esempio semplice.* Due bandi coprono entrambi le licenze software: uno al 50%, l'altro al 75%. Ognuno riceve il proprio budget con quella spesa, e ciascuno dichiara l'altro contributo, così i controlli 47 e 48 verificano che il totale non superi il consentito. Una persona che lavora al 60% sul progetto A può stare al massimo al 40% sul progetto B.")

    P("**31.5 Come si accede a un bando: non tutti chiedono un progetto (15 ottobre 2026).** Un errore da evitare: pensare che ogni bando finanzi un «progetto nuovo». Non è così. "
      "Ogni bando ha una **modalità di accesso**, letta dal tipo di aiuto e dalle frasi del suo testo (la frase è la prova, mostrata nella scheda del bando): "
      "**progetto o investimento** (ricerca e sviluppo, Smart&Start, bandi regionali per l'innovazione: si finanziano le spese nuove del progetto); "
      "**credito d'imposta automatico** (iperammortamento, Transizione 5.0: contano gli acquisti qualificati dell'anno, senza domanda né graduatoria); "
      "**garanzia e liquidità** (Fondo di garanzia PMI: la base è il finanziamento bancario, non un elenco di spese); "
      "**occupazione** (incentivi alle assunzioni: contano le persone assunte e i loro requisiti, più il DURC); "
      "**spese commerciali e internazionalizzazione** (SIMEST: fiere, e-commerce, consulenze per l'export, anche spese ricorrenti); "
      "**ristoro** (contributi per crisi o caro energia, calcolati sui dati storici). Senza testo né tipo di aiuto, la modalità non si indovina.")
    P("*Esempio semplice.* Un'azienda spende ogni anno 20.000 € di fiere. Con un bando SIMEST quelle spese sono una base valida (si rimborsa una parte, se sostenute per il programma e dopo la domanda). "
      "Con un bando di ricerca la stessa spesa non conta: il bando vuole un progetto nuovo. Con il Fondo di garanzia non conta nessuna delle due: serve sapere di quanto fido ha bisogno.")
    P("**Cosa cambia in QUANTO.** (a) La scheda del bando dice come si accede, con esempio e frase di prova, e che tipo di progetto finanzia (digitalizzazione, ricerca e sviluppo, efficienza energetica, export, occupazione, formazione, macchinari…); "
      "(b) la bozza di budget e le sue etichette dipendono dalla modalità: per un bando a progetto dice che parte dalle spese correnti e non è ancora un progetto, per un bando sulle spese correnti le dice «base valida»; "
      "(c) il piano annuale di allocazione resta com'era (parte dalle spese dell'azienda: per molte misure è la base giusta) e un **progetto** si sceglie solo se serve; "
      "(d) le **idee di progetto** (`GET /profile/project-ideas`) propongono, dai documenti dell'azienda (piano degli investimenti, libro cespiti, piano delle assunzioni, formazione, promozione, energia), progetti con le spese che li compongono, "
      "ciascuna **nuova** (un acquisto o un'assunzione che il progetto causa), **corrente** (l'azienda la sostiene già: valida o no a seconda del bando) o **da quantificare** (serve un preventivo), cosa manca e i bandi che li finanziano; "
      "separano poi le **misure senza progetto** con la loro base. Sono ipotesi da validare con l'imprenditore; un importo che non viene da un documento non si inventa; "
      "(e) la data di avvio del progetto, se indicata, è controllata su ogni voce dal controllo 46 (finestra del bando).")
    P("*Esempio semplice.* Il piano delle assunzioni dell'azienda prevede un data engineer a settembre. L'idea «Nuove assunzioni» mostra la spesa come nuova, dice che mancano RAL e livello, e propone i bandi per l'occupazione: "
      "per quelli non serve scrivere un progetto, serve il contratto e il DURC.")
    P("**Il confine che QUANTO non supera.** Il costo del personale si rendiconta sulle ore realmente dedicate e alla retribuzione vera: il controllo 15 confronta la RAL dichiarata con la busta paga e il 7 il costo orario con le tabelle del contratto. "
      "Non esiste né è prevista una funzione che faccia passare costi ordinari, o stipendi pagati più del dovuto, come costi di progetto: sarebbe un costo non reale dichiarato a un ente pubblico.")
    P("**31.6 De minimis, impresa unica e registro nazionale (15 ottobre 2026).** QUANTO non può leggere il Registro Nazionale degli Aiuti (RNA): organizza la verifica perché sia fatta e documentata (`/profile/aids`). "
      "Nel Profilo: le cinque domande sull'impresa unica (Reg. UE 2023/2831, art. 2 par. 2) e l'elenco delle imprese collegate con codice fiscale; per ogni impresa la visura aiuti ufficiale con la data in cui è stata consultata e le concessioni (data, ente, misura, regime, importo, COR); "
      "il confronto con ciò che l'azienda ha dichiarato nei documenti (ogni differenza è scritta); il residuo del triennio calcolato sulla data di concessione e sommando tutte le imprese del gruppo; la conferma di chi ha fatto la verifica (resta nel registro delle operazioni). "
      "Gli stati sono VERIFICATO, NON VERIFICATO, SCADUTO (visura di oltre 30 giorni) e DISCORDANZA. Finché la verifica non è completa e recente il piano usa un residuo ridotto di un margine di sicurezza del 10% del tetto e non è definitivo. "
      "La visura aiuti caricata come documento viene ora letta da sola (31.7); le concessioni si possono anche riportare a mano. Il tracciato letto è quello del file di prova: sul primo file reale potrebbe servire un adattamento. Non sostituisce la dichiarazione firmata dal legale rappresentante.")
    P("*Esempio semplice.* L'azienda risulta aver ricevuto 16.500 € di de minimis. La visura dell'RNA ne mostra anche 40.000 € ricevuti da una società controllata: l'impresa unica ha già usato 56.500 € dei 300.000 €. Finché la visura non è caricata e recente (30 giorni), il piano usa 270.000 € al posto di 283.500 €.")

    P("**31.7 Più tipi di file, letti per intero (15 ottobre 2026).** Oltre a quelli del punto 31.2, QUANTO riconosce ora per contenuto (non per nome) questi file e ne ricava dati con la riga o la pagina di provenienza: "
      "**fatture elettroniche XML** (anche molte in un archivio ZIP: spese per voce e per anno; le tag pericolose di XML sono rifiutate); **bilancio XBRL** (ricavi, costi, personale, utile per esercizio); "
      "**bilancio di verifica del gestionale** in Excel o CSV (costi conto per conto, senza interessi e imposte sul reddito); **visura aiuti dell'RNA** (concessioni con data, misura, regime, importo e codice COR); "
      "**dichiarazione sostitutiva de minimis**; **libro soci** (le persone restano un codice anonimo, le società socie si nominano perché servono all'impresa unica); **dichiarazioni IVA, IRAP e REDDITI**; **estratto conto** (saldo alla data); **preventivi dei fornitori**. "
      "Un anno senza bilancio in PDF si compila dal bilancio di verifica o dall'XBRL; un anno con il PDF resta quello del PDF (ha le righe e la nota integrativa). Un file che non si riconosce resta archiviato.")
    P("*Esempio semplice.* L'azienda carica un archivio ZIP con 26 fatture elettroniche passive del 2025: QUANTO le legge una per una, somma per voce (affitti, licenze, consulenze) e per anno, e le spese compaiono nel budget con la dicitura «dalle fatture». Se carica anche il bilancio di verifica 2025 in CSV, i costi conto per conto servono per l'anno che non ha un PDF.")
    P("**31.8 Coerenza tra i documenti (`GET /profile/consistency`).** Documenti che parlano della stessa cosa si confrontano: volume d'affari IVA contro ricavi del bilancio (differenza oltre il 5%: da spiegare), ricavi XBRL contro bilancio PDF, quote dei soci che sommano 100%, società socie (per l'impresa unica), scadenza del DURC (segnalata a 30 giorni), età della visura aiuti (oltre 30 giorni: da rifare), preventivi scaduti, saldo del conto. "
      "Nel Profilo, «Cosa ho letto dai documenti», scheda «Coerenza tra i documenti».")
    P("*Esempio semplice.* La dichiarazione IVA 2025 dice 1.579.064 € di volume d'affari e il bilancio 1.583.200 € di ricavi: differenza 0,3%, «torna». Se la dichiarazione dicesse 1.300.000 €, QUANTO scriverebbe «da vedere: differenza 17,9%, va spiegata (anno d'imposta, operazioni fuori campo, reverse charge)» senza decidere quale dei due sia giusto.")
    P("**31.9 I preventivi nelle idee di progetto.** Un acquisto del piano degli investimenti ha un importo, non un fornitore. Se l'azienda ha caricato il preventivo di un fornitore per quel tipo di spesa e non è scaduto, l'idea di progetto usa l'importo del preventivo (il più basso se sono più d'uno), scrive fornitore, numero e validità e ricorda l'importo del piano. "
      "Se non c'è un preventivo, l'idea dice «manca un preventivo per…».")
    P("*Esempio semplice.* Il piano prevede 45.000 € di infrastruttura cloud. Il preventivo di Nuvola Datacenter è di 48.600 € valido fino al 31 dicembre: l'idea mostra 48.600 € con la dicitura del preventivo e «nel piano 45.000 €».")
    P("**31.10 Dall'allocazione alla realtà (`POST /allocation/reality`, passo 8 dell'Allocazione).** L'allocazione dice «questo bando copre 60.000 €». Non dice quanto ci si può contare, quanto costa ottenerlo e quando entrano i soldi. Per ogni bando del piano la persona indica "
      "**probabilità di successo, costo di istruttoria, percentuale del consulente** (anche zero): QUANTO non li inventa, e dove mancano mostra solo il nominale e dice cosa manca. Con le ipotesi calcola valore atteso = contributo × probabilità; consulente = % sul valore atteso; netto = valore atteso − consulente − istruttoria; "
      "la probabilità minima sopra la quale conviene. **Tempi**: anticipo e mesi di rimborso si leggono dalle regole pubblicate del bando (e si possono correggere; l'origine di ogni numero è scritta); le spese si pagano nel mese previsto, l'anticipo entra nel primo mese di spesa coperta, il resto dopo i mesi di rimborso; "
      "il risultato è la posizione di cassa mese per mese e il fabbisogno massimo da anticipare (calcolato come se tutti i contributi fossero concessi). **Altri aiuti**: credito d'imposta ricerca e sviluppo e aiuti non de minimis del registro degli ultimi due anni sono elencati come aiuti da sommare, con l'indicazione di inserirli come «altri aiuti» (controllo 48).")
    P("*Esempio semplice.* Bando A: contributo 60.000 €, probabilità 50%, consulente 10%, istruttoria 3.000 €: valore atteso 30.000 €, consulente 3.000 €, netto 24.000 € (conviene). Bando B: 30.000 € al 20% con istruttoria 8.000 €: valore atteso 6.000 €, netto −2.000 €; conviene solo se la probabilità supera il 26,7%. "
      "Se le spese di 120.000 € sono a gennaio e il contributo arriva dopo 3 mesi, l'azienda deve anticiparle tutte e 120.000 € fino ad aprile.")
    P("**31.11 Livelli di contratto mancanti (Fonte B).** Se una persona ha un livello che non è in tabella, il controllo del costo orario resta in attesa e il budget lo scrive. Nell'area riservata (Fonte B, «Livelli mancanti di un contratto») il manager può preparare una **bozza** che aggiunge i livelli mancanti (`GET /fonte-b/ccnl/{codice}/completion`, `POST /fonte-b/ccnl/{codice}/complete-levels`), "
      "ma solo se **tutti** i livelli già pubblicati di quel contratto hanno gli stessi parametri (ore, oneri sociali, TFR): in quel caso la bozza copia quei valori. Se i parametri sono diversi tra livelli non si deduce nulla. La bozza non entra nei calcoli: serve la verifica sul testo del contratto e la pubblicazione con attestazione di un manager, come per ogni altra tabella. "
      "Nel codice di produzione non c'è nessuna tabella contrattuale preimpostata.")
    P("*Esempio semplice.* COMMERCIO ha pubblicati i livelli 3 e 4: 1.680 ore, oneri 29,5%, TFR 8,33% per entrambi. Manca il 5. Il manager prepara la bozza «livelli 5 e Quadro»: stesse tre cifre. Controlla sul contratto che valgano anche per quei livelli e pubblica. Con TERZO_SETTORE, dove il livello 1 ha oneri 31% e il 2 il 30%, la bozza non è possibile: la tabella va caricata dal contratto.")
    P("**31.12 Voci escluse in revisione e azienda di prova che si aggiorna da sola.** Le voci di spesa che un bando esclude, lette dalle frasi del testo, non diventano più un controllo attivo da sole: restano **in revisione** nel Quartier Generale finché una persona le conferma, perché una voce letta male toglierebbe soldi ammessi. "
      "L'azienda di prova (57 documenti) si aggiorna da sola per chi l'ha già caricata: aprendo la pagina dei documenti, i file nuovi o cambiati (confronto per impronta SHA-256) si caricano e quelli tolti dal set si eliminano; a chi non l'ha mai caricata non viene caricato nulla.")
    P("**31.13 Un Profilo che guida (16 ottobre 2026).** La pagina Profilo di un lavoro è ora fatta di sezioni apribili con riassunto in testa (configurazione guidata, profilo dell'azienda, documenti, cosa è stato letto, aiuti): quelle già a posto restano chiuse. In cima c'è un solo «prossimo passo» calcolato dai dati (nessun documento → carica; mancano dati dell'impresa → carica la visura; manca il bilancio → caricalo; restano domande → rispondi; letture incerte → verifica), con il pulsante che porta al punto esatto: ogni pulsante di altre pagine (Allocazione, Budget) apre il Profilo sulla sezione giusta e la evidenzia. "
      "La verifica delle letture incerte è una tabella unica per tutti i documenti (valore, sicurezza, frase di origine) con conferma multipla; il dettaglio di un documento si apre sotto la sua riga, con «Sono tutte giuste» e «Vai al prossimo». Sono provati in un'app locale con l'utente di prova; il flusso completo con dati reali di produzione resta da vedere.")
    P("*Esempio semplice.* Aprendo il Profilo di un cliente con 57 documenti caricati: «Prossimo passo: 17 letture sono poco sicure. [Verifica ora]». Un clic apre la tabella con le 17 RAL stimate dalle buste paga, ciascuna con la frase da cui è stata ricavata; tolto il segno a quella che non torna, «Confermo le 16 selezionate» le dà per buone e il prossimo passo diventa «Stima l'anno e cerca i bandi».")
    P("**31.14 Allocazione chiara e grafica minimale (16 ottobre 2026).** Correzione di un errore logico: il piano dell'anno includeva anche i bandi che finanziano progetti (per esempio Horizon Europe), applicati ai costi correnti dell'azienda, e gonfiava il totale (1,36 milioni invece di circa 148.000 €). Ora i bandi sono di due famiglie e non si mescolano. "
      "La pagina ha un solo **Risultato** con un interruttore **Spese dell'anno / Un progetto**: nel primo contano solo i bandi che non chiedono un progetto (`mode.needs_project = false`) sulle spese previste; nel secondo le sole spese nuove del progetto scelto con i bandi che lo finanziano. "
      "La spunta «Includi nel piano / nel progetto» è la stessa: decide i bandi dello scenario visto; le due scelte sono separate (`picked`, `projectPicked`). Un bando a progetto, nel piano dell'anno, non ha importo né spunta: dice «finanzia le spese nuove di un progetto» e mostra i progetti possibili, ricavati dalle idee (`GET /profile/project-ideas`, un'idea elenca i bandi che la finanziano); se i documenti non suggeriscono un progetto adatto lo scrive e non lo inventa. "
      "**Grafica:** nuovo sistema in stile minimale (colori chiari, raggi ampi, pulsanti a pillola, campi senza bordo, carattere di sistema, molto spazio) applicato a tutta l'app con i token di `tailwind.config.js` e `index.css`; le spiegazioni lunghe stanno dietro una «i» (`Info`); in testa alle pagine restano solo gli avvisi che servono. "
      "Corretto il titolo che si spezzava lettera per lettera (regola CSS globale) e la griglia a cinque colonne della Guida; `frontend/scripts/layout_scan.js` apre ogni sezione di ogni pagina e cerca colonne schiacciate e scorrimenti orizzontali, a 1440, 1024, 768 e 375 px.")
    P("*Esempio semplice.* Spese dell'anno: «Nuovo Piano Transizione 5.0» e il fondo 394/81 coprono insieme circa 148.000 € delle spese previste. «Beni strumentali — Nuova Sabatini» compare con «finanzia le spese nuove di un progetto, fino all'8%» e il pulsante «Rinnovo dei beni a fine vita»: un clic passa allo scenario Progetto, con le spese di quel rinnovo, e «Spese dell'anno» riporta al calcolo di prima.")
    P("**Limiti dichiarati di questo modulo.** I tracciati della visura RNA, dell'XBRL e delle fatture XML che QUANTO legge oggi sono quelli dei file di prova (l'XML segue la struttura della fattura elettronica, l'RNA e l'XBRL no): il primo file reale potrebbe richiedere un adattamento, e per questo le righe lette portano sempre il testo di provenienza. "
      "Probabilità di successo e costi di istruttoria sono ipotesi della persona, non statistiche di QUANTO (non ci sono pratiche reali da cui ricavarle). Le funzioni dell'interfaccia di questo modulo sono state provate con test automatici e con la compilazione del frontend, non con una sessione di accesso reale.")

    H1("EXECUTIVE SUMMARY")
    P("QUANTO è un motore di calcolo, allocazione e — in prospettiva — consulenza finanziaria per studi di commercialisti e boutique di finanza agevolata, con due missioni permanenti: validare il budget di una candidatura a un bando pubblico e pianificare l'allocazione delle risorse dell'anno successivo tra spesa ordinaria e finanziamenti pubblici. "
      "Non scrive testo progettuale: produce solo la componente numerica, validata da un motore deterministico a 60 criteri, completamente disaccoppiato da qualunque modello linguistico.")
    P("**Il sistema esiste ed è in produzione.** Lo studio apre un lavoro per ogni azienda cliente e carica visura e bilanci in una procedura guidata; QUANTO ne ricava il profilo con la provenienza di ogni dato, stima le spese dell'anno successivo (con il modello di previsione del cliente o con la variazione dei suoi bilanci, spiegata riga per riga), trova tra i bandi studiati quelli adatti con un **valore in euro per ciascuno** "
      "e tra gli oltre 800 del catalogo quelli più affini da studiare, calcola il **potenziale massimo** con tutti i bandi insieme (sempre lo stesso a parità di dati, con il de minimis riconosciuto e stimato), costruisce la bozza di budget per il bando scelto, che il motore controlla, esporta e registra con un'impronta firmata verificabile da chiunque. "
      "Il Confronto impara dai template di budget dello studio e dice quanto è sicuro del proprio consiglio. Un **assistente guidato** esegue al posto dell'utente i passaggi in cui servono dati, spiegandoli in parole semplici.")
    P("La proposta si dimostra con casi su dati realistici; l'accuratezza con un Conformity Score su casi di test noti (549 test automatici) — non con un tasso di errore su pratiche reali, che non esistono. La copertura normativa non è vincolata a un solo bando: il catalogo individua tutto ciò che è aperto, e l'estrazione parte solo su conferma con riuso in cache. "
      "Il Registro crittografico è stato anticipato e realizzato senza blockchain; la visione a lungo termine (mercato degli studi, estero, acquisizione di studi dipendenti da QUANTO) è nel Modulo 18. Per arrivare al 100% servono dati e decisioni del titolare (chiave del modello, dataset dei pattern, tabelle ufficiali, OCR, documenti legali, verifica online dell'ultimo rilascio) e alcuni sviluppi dichiarati nel Modulo 30.")
    # ================================================================================================ SCHEMA API
    H1("SCHEMA TECNICO API (reale)")
    P("L'integrazione con ERP e gestionali avviene via REST protetta da OAuth 2.0 (client-credentials) o da firma HMAC; gli utenti dell'app usano un token a 8 ore. Non esiste alcun endpoint di generazione testuale progettuale. Tutto vive sotto `/api/v2`. Documentazione interattiva su `/docs`. Sono 158 operazioni sotto `/api/v2` (più la radice `/`); di seguito i gruppi con i principali.")
    T([["Gruppo", "Endpoint principali"],
       ["Salute", "GET /health, GET /health/ready"],
       ["Autenticazione", "POST /auth/register, /auth/login, /auth/token, /auth/change-password; GET /auth/me, /auth/me/activity, /auth/me/credits"],
       ["Bandi", "GET /bandi, /bandi/{id}, /bandi/catalog (q, issuer, only_new, described, with_meta, page), /bandi/catalog/issuers, /bandi/catalog/stats, /bandi/search, /bandi/references, /bandi/{id}/sources/{sha256}; POST /bandi/{id}/select, /bandi/upload (solo Quartier Generale); ricerca e studio: POST /bandi/research/search, /fetch, /analyze, /confirm, /run"],
       ["Ingestion", "GET /ingestion/catalog, /status/{id}, /review-queue, /grant-rules/{id}; POST /ingestion/catalog, /confirm/{id}, /extract, /review"],
       ["Budget", "POST /budget/validate, /budget/wp-plan (nuovo), /budget/import, /budget/export/pdf, /budget/export/xlsx; GET /budget/criteria, /budget/fields, /budget/template.xlsx"],
       ["Allocazione", "POST /allocation/optimize, /allocation/budgets (budget di ogni bando dall'allocazione, verificati insieme), /allocation/reality (valore atteso, tempi di incasso, altri aiuti); GET e POST /allocation/funds, POST /allocation/funds/from-bando, DELETE /allocation/funds/{id}"],
       ["Profilo e lavori", "GET /profile; PUT /profile; PUT /profile/financials/{anno}; POST /profile/sync, /profile/forecast, /profile/match, /profile/template (con year e project_start); GET /profile/expenses, /staff, /assets, /facts, /consistency, /quotes, /shareholders, /expense-types, /project-ideas, /project-types; GET/PUT/DELETE /profile/forecast-template (modello di previsione); GET/POST /clients, PATCH/DELETE /clients/{id}, GET/PUT /clients/current/state/{chiave}"],
       ["Aiuti e impresa unica", "GET /profile/aids (stato, residuo, differenze); PUT /profile/aids/group (domande e imprese collegate), /profile/aids/entries (visura aiuti dell'RNA o inserimento a mano); POST /profile/aids/confirm"],
       ["Template e Confronto", "GET /templates, /templates/meta, /templates/niches, /templates/learning; POST /templates, /templates/recommend; PATCH/DELETE /templates/{id}"],
       ["Account dello studio", "PATCH /auth/me; GET /auth/me/profile, /auth/me/export, /auth/me/activity, /auth/me/credits; POST /auth/me/sign-out-everywhere, /auth/change-password; DELETE /auth/me"],
       ["Documenti del cliente", "GET e POST /fonte-c/documents; GET e DELETE /fonte-c/documents/{id}; /file, /cost-line, /draft-items, /expenses; POST /fields/{id}/review"],
       ["Fonte B", "GET /fonte-b/summary, /kinds, /datasets, /datasets/{id}, /datasets/{id}/file, /template/{tipo}.csv; POST /datasets (bozza), /datasets/{id}/publish; DELETE bozza; GET /ccnl/{codice}/completion, POST /ccnl/{codice}/complete-levels (bozza dei livelli mancanti)"],
       ["Pattern", "GET /pattern/categories, /pattern/budgets; POST /pattern/match, /pattern/import"],
       ["Registro", "POST /registry/register, /verify/recompute, /verify/attestation, /merkle-lab; GET /registry/status, /public-key, /verify/{progetto}, /attestation/{progetto}"],
       ["Quartier Generale", "GET /hq/overview, /manual, /manual.pdf, /timeline, /operations, /projects, /projects/{id}, /runs/{id}, /documents, /bandi/{id}, /users (POST per creare, PATCH /users/{id}); archivio: GET /hq/archive, /archive/{id}, PATCH e DELETE /archive/{id}, POST /archive/restore-defaults, /archive/{id}/reanalyze, /requirements, PATCH e DELETE /requirements/{seq}, PUT e DELETE /rules/{chiave}, GET /consultant, /export.zip, /sources/{sha}/text e /file, DELETE /sources/{sha}; database: GET /hq/db/tables, /db/table/{tabella}, /export.csv, DELETE di una riga o della tabella"],
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
    P("La risposta di `/profile/match` contiene anche `de_minimis` (plafond, contributi dichiarati, residuo, base DICHIARATI / PARZIALE / IPOTESI, anni mancanti) e, per ogni bando, `de_minimis: {applies, basis, mentioned, evidence[]}` con la frase da cui viene.")
    CODE('POST /api/v2/profile/match      { "year": 2027, "growth": { "PERSONNEL": 0.04 } }\n  → { "forecast": { "base_year", "categories": [ { "category", "baseline_eur", "suggested_growth", "growth_applied", "forecast_eur" } ], "warnings", … },\n      "matching": { "results": [ { "bando_id", "fit": "ADATTO|DA_VERIFICARE|NON_ADATTO", "checks": [ { "id", "result": "OK|FAIL|UNKNOWN", "detail" } ],\n                      "estimate": { "rate_pct", "covered_eur", "by_category", "adjustments" } | null, "fund": { … }, "notes" } ],\n                    "catalog": { "items": [ { "bando_id", "summary", "score", "affinity", "reasons", "to_check" } ], "total_candidates", "excluded" },\n                    "summary", "missing_profile" } }\n\nPOST /api/v2/profile/template  { "bando_id": "…", "scale_pct": 25, "fit": true }\n  → { "cost_items": [ { "item_id": "TPL-01", … } ], "needs_personnel": { "amount_eur", "message" } | null, "adjustments", "excluded_categories", "notes", "total_eur" }')
    CODE('POST /api/v2/budget/wp-plan\n{ "project_id": "PRJ-2026-001", "allow_split": true,\n  "items": [ { "item_id": "A-01", "category": "PERSONNEL", "amount_eur": 60000, "pinned_wp": null } ],     // importi AMMESSI\n  "work_packages": [ { "wp_id": "WP1", "name": "Gestione", "min_share_pct": 0.1, "target_share_pct": 0.5, "max_share_pct": 0.6,\n                       "allowed_categories": ["PERSONNEL", "OVERHEAD"], "category_max_share": { "OVERHEAD": 0.2 } } ] }\n→ { "status": "OPTIMAL | BEST_FOUND | INFEASIBLE", "message", "assignments": [ { "item_id", "parts": [ { "wp_id", "amount_eur", "share" } ] } ],\n    "work_packages": [ { "wp_id", "total_eur", "share_pct", "by_category", "deviation_pp" } ], "checks": [ { "wp_id", "rule", "ok", "detail" } ],\n    "reasons": [], "unplaced": [], "notes": [] }')
    H3("4. Stato dell'ingestion")
    CODE('GET /api/v2/ingestion/status/FONDO-GARANZIA-PMI\n→ { "catalog_status": "CURATED", "extraction_status": "COMPLETED", "cache_hit": true, "rules_extracted_total": 2,\n    "rules_from_structured_parsing": 1, "rules_from_multi_pass_ai": 0, "rules_with_pass_agreement": 0,\n    "rules_pending_human_review": 1, "rules_human_reviewed": 0, "rules_from_curated_source": 0, "requested_by_clients_count": 11 }')
    H3("5. Notifiche webhook")
    P("Gli indirizzi e il segreto vengono solo dall'ambiente; il corpo è firmato HMAC-SHA256 (intestazione `X-Quanto-Signature`); i contenuti sono identificativi opachi e totali, mai dati personali o contabili di dettaglio.")
    T([["Evento", "Stato"],
       ["event.budget.validated", "[[FATTO]]"], ["event.budget.registered (nuovo)", "[[FATTO]]"], ["event.allocation.optimized", "[[FATTO]]"], ["event.criteria.failed", "[[FATTO]]"], ["event.pattern.matched", "[[FATTO]]"],
       ["event.bando.coverage_activated", "[[FATTO]]"], ["event.rule.disagreement_detected", "[[FATTO]] (attivo solo con lo Stadio 3)"],
       ["event.rule.audit_flagged", "[[DA FARE]]"]], [90, 80])

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
       ["Ricerca e archivio", "20/09/2026", "Ricerca web reale con scarico e lettura dei documenti, scoperta senza motori, archivio dei bandi con file originali e scheda di revisione."],
       ["Identità visiva", "21/09/2026", "Restyle con colore bianco e giallo, caratteri, icone."],
       ["Dati veri", "21/09/2026", "PostgreSQL, Fonte B in database, Fonte C cifrata con confidenza e revisione, utenti e ruoli, banca dei pattern con k-means, modulo del modello linguistico, cron del catalogo."],
       ["Demo e pulizia", "26/09-01/10/2026", "Demo con bandi reali, banca dei pattern con bilanci di società quotate, rifacimento della homepage e delle pagine con lo stile «finestra», pulizia del catalogo, processo standard di studio, figure strutturate."],
       ["Sicurezza e profilo", "03/10/2026", "Sicurezza e CI (azioni fissate, audit, intestazioni, CSP), profilo aziendale, stima dell'anno, abbinamento ai bandi, bozza di budget, allocazione a passi."],
       ["Catalogo, procedura guidata e test", "04/10/2026", "Schede del catalogo (descrizioni e caratteristiche), procedura guidata a passi, documenti dell'azienda di prova, test completo su dati reali con 18 correzioni, ripartizione delle voci tra i WP, anteprima e scarico di tutti i file dell'azienda, questo documento."],
       ["Valore dei bandi, studio e lavori", "05-08/10/2026", "Valore in euro di ogni bando (regola, modello, tabella di intensità), RICERCA-v2, modello di previsione con la spiegazione di ogni percentuale, potenziale massimo e bilancio ricostruito, demo tolta, caricamento manuale riservato al Quartier Generale, testi per gli studi."],
       ["Confronto e interfaccia", "05-08/10/2026", "Confronto a template con due motori, lavori dello studio con salvataggio per lavoro, profilo dello studio completo, interfaccia minimale con menu laterale, manuale dei processi (PDF e Quartier Generale) e «I 60 criteri spiegati»."],
       ["Allocazione deterministica", "09/10/2026", "Piano uguale a parità di dati e sempre massimo, tutti i bandi adatti di default, 12 colori e bandi «non serve» in legenda, ipotesi de minimis dichiarata."],
       ["Legenda, de minimis e assistente", "10/10/2026", "Legenda dei numeri, de minimis riconosciuto dalle fonti e stimato dai dati dichiarati, assistente guidato con pannello a destra, download dei PDF affidabile, 523 test."],
       ["Rilettura del dossier (v4.1)", "12/10/2026", "Conteggi e schema API ricontrollati sul codice (144 operazioni, 28 tabelle più quella delle migrazioni, 16 migrazioni), verifica del rilascio online (versione del frontend, registro firmato), stato della verifica dichiarato."],
       ["Visione, documenti di prova, assistente e riassunto (v4.2)", "12/10/2026", "Tolte la visione di consulenza e le assicurazioni, nuova visione (Modulo 18); documenti dell'azienda di prova rifatti come quelli veri e sette difetti di lettura corretti (9.3.1); assistente a chat a tutto schermo; nuovo documento breve «Riassunto» di 7 pagine; 523 test; questo documento."],
       ["Voci di spesa, tutti i documenti, budget dall'azienda e dall'allocazione (v4.3)", "14/10/2026", "Oltre 50 voci di spesa sotto le cinque categorie, voci escluse per nome dai bandi con la frase come prova; lettura dei fogli Excel (organico, cespiti, fatture, budget, investimenti, assunzioni, aiuti); bozza di budget con il personale persona per persona e le spese dal budget dell'azienda e dal piano degli investimenti, senza ammortamento; budget dei bandi ricavati dall'allocazione e verificati insieme (Modulo 31); azienda di prova con 50 documenti e pulsante «Carica l'azienda di prova»."],
       ["Progetti, idee di progetto e verifica de minimis (v4.4)", "15/10/2026", "Tipologie di progetto lette dai bandi, idee di progetto dai documenti con spese nuove e ordinarie separate, piano sul progetto scelto, tetto teorico di ammissibilità al posto del potenziale massimo, impresa unica e visura aiuti dell'RNA con confronto, residuo prudente e conferma (Modulo 31)."],
       ["Più documenti, realtà dell'allocazione, livelli CCNL e Profilo guidato (v4.5)", "15-16/10/2026", "Profilo con sezioni apribili, prossimo passo e verifica rapida (31.13); Allocazione con scenari Piano dell'anno / Progetto e testi ridotti (31.14); fatture XML, XBRL, CSV, visura RNA, libro soci, dichiarazioni, preventivi letti e incrociati; coerenza tra documenti; passo 8 «quanto vale davvero e quando incassi»; bozza dei livelli CCNL mancanti; voci escluse in revisione; azienda di prova di 57 documenti che si aggiorna da sola; 549 test (Modulo 31, 31.7–31.12)."]], [34, 28, 108])

    NOTE("Fine del documento. Ogni numero riportato è stato letto dal sistema o dal codice alla data indicata; dove un dato non esiste (pratiche reali, metriche di successo, benchmark) il documento lo dichiara.")
