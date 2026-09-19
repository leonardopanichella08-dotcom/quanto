"""Catalogo dei bandi curati: regole e requisiti compilati da fonti ufficiali (consultate il 2026-09-19).

Principi:
- ogni regola ha la sua fonte e un livello di confidenza (PRIMARIA = testo ufficiale letto; SECONDARIA = fonte non
  ufficiale/di stampa, da verificare; INTERPRETAZIONE = traduzione in regola eseguibile di un testo qualitativo);
- ciò che le fonti NON dicono sta in ``not_specified``: non viene mai riempito con valori "plausibili";
- un riassunto automatico di una fonte non è una fonte: per Horizon Europe il tasso dei costi indiretti è stato
  verificato sul PDF ufficiale (25%) perché il riassunto della pagina riportava un valore errato (15%);
- queste schede NON sostituiscono la lettura del bando e del testo integrale: vanno riviste da un consulente prima
  di presentare una candidatura.
"""
from __future__ import annotations

from typing import Any, Dict, List

ACCESSED = "2026-09-19"


def R(topic: str, kind: str, text: str, criteria: List[int], source_ref: str, confidence: str = "PRIMARIA") -> Dict[str, Any]:
    return {"topic": topic, "kind": kind, "text": text, "criteria": criteria, "source_ref": source_ref, "confidence": confidence}


IPERAMMORTAMENTO: Dict[str, Any] = {
    "bando_id": "IPERAMMORTAMENTO-2026",
    "name": "Nuovo Piano Transizione 5.0 — Iperammortamento",
    "issuer": "MIMIT / GSE",
    "status": "APERTO",
    "period": {"from": "2026-01-01", "to": "2028-09-30"},
    "legal_refs": [
        "Legge 30 dicembre 2025, n. 199 (bilancio 2026), art. 1, commi 427-436",
        "Decreto interministeriale 7 maggio 2026 (modalità attuative)",
        "Decreto direttoriale 10 giugno 2026 (termini e modelli di comunicazione)",
        "Decreto direttoriale 20 luglio 2026 (comunicazioni di conferma investimenti)",
        "Decreto-legge 27 marzo 2026, n. 38, convertito dalla legge 22 maggio 2026, n. 88",
    ],
    "benefit": {
        "type": "IPERAMMORTAMENTO",
        "summary": "Maggiorazione del costo di acquisizione deducibile (non è un contributo): riduce la base imponibile IRES/IRPEF lungo la vita utile del bene.",
        "tiers": [{"up_to_eur": 2_500_000, "rate_pct": 180}, {"up_to_eur": 10_000_000, "rate_pct": 100}, {"up_to_eur": 20_000_000, "rate_pct": 50}],
    },
    "sources": [
        {"title": "MIMIT — Nuovo Piano Transizione 5.0 - Iperammortamento", "url": "https://www.mimit.gov.it/it/incentivi/nuovo-piano-transizione-5-0-iperammortamento",
         "accessed": ACCESSED, "confidence": "PRIMARIA"},
        {"title": "reteagevolazioni.it — Iperammortamento 2026: guida (fonte non ufficiale)", "url": "https://www.reteagevolazioni.it/iperammortamento-2026/",
         "accessed": ACCESSED, "confidence": "SECONDARIA"},
        {"title": "pmi.it — Iperammortamento 2026: conferme al GSE (fonte non ufficiale)",
         "url": "https://www.pmi.it/impresa/contabilita-e-fisco/487218/iperammortamento-2026-requisiti-investimenti-imprese-novita.html",
         "accessed": ACCESSED, "confidence": "SECONDARIA"},
    ],
    "rules": {
        "eligible_categories": ["CAPITAL_ASSETS"], "requires_new_asset": True, "requires_iot": True, "appraisal_threshold_eur": 0,
        "requires_eu_origin": True, "eligibility_start": "2026-01-01", "eligibility_end": "2028-09-30",
    },
    "rule_notes": {
        "eligible_categories": {"source": "MIMIT: due categorie di beni (materiali/immateriali 4.0 negli Allegati IV e V; autoproduzione FER). Nessuna spesa di personale o consulenza.", "confidence": "PRIMARIA"},
        "requires_new_asset": {"source": "MIMIT: «beni materiali e immateriali strumentali nuovi».", "confidence": "PRIMARIA"},
        "requires_iot": {"source": "MIMIT: beni «interconnessi ai sistemi aziendali».", "confidence": "PRIMARIA"},
        "appraisal_threshold_eur": {"source": "MIMIT elenca la «perizia tecnica asseverata»; le fonti secondarie precisano che è obbligatoria per tutti gli investimenti (soglia 0 €).", "confidence": "INTERPRETAZIONE"},
        "requires_eu_origin": {"source": "Requisito di origine UE/SEE riportato solo da fonti non ufficiali (reteagevolazioni.it, pmi.it): NON presente nella pagina MIMIT. Da verificare sul decreto.", "confidence": "SECONDARIA"},
        "eligibility_start": {"source": "MIMIT: investimenti dal 1° gennaio 2026.", "confidence": "PRIMARIA"},
        "eligibility_end": {"source": "MIMIT: fino al 30 settembre 2028.", "confidence": "PRIMARIA"},
    },
    "requirements": [
        R("Beni ammissibili", "OBBLIGO", "Beni materiali e immateriali strumentali nuovi (Allegati IV e V della legge 199/2025) per la trasformazione digitale, interconnessi ai sistemi aziendali.", [16, 19, 20], "MIMIT — Beni ammissibili"),
        R("Autoproduzione da fonti rinnovabili", "LIMITE", "Beni materiali per l'autoproduzione di energia rinnovabile destinata all'autoconsumo (anche a distanza), con sistemi di stoccaggio; dimensionamento massimo 105% del fabbisogno energetico annuale.", [16], "MIMIT — Beni ammissibili"),
        R("Perizia tecnica asseverata", "OBBLIGO", "Perizia tecnica asseverata richiesta; per le fonti secondarie obbligatoria per tutti gli investimenti, senza più l'autocertificazione sotto 300.000 €.", [30], "MIMIT — Documentazione richiesta; fonti secondarie", "SECONDARIA"),
        R("Certificazione contabile", "OBBLIGO", "Certificazione contabile richiesta insieme alla perizia (verifica documentale esterna al motore).", [15], "MIMIT — Documentazione richiesta"),
        R("Periodo di ammissibilità", "LIMITE", "Investimenti completati dal 1° gennaio 2026 al 30 settembre 2028; gli scaglioni si applicano per anno e si azzerano a inizio esercizio.", [46], "MIMIT — Periodo; fonti secondarie per l'azzeramento annuale", "PRIMARIA"),
        R("Scaglioni di maggiorazione", "INFO", "Fino a 2,5 mln: 180%; oltre 2,5 e fino a 10 mln: 100%; oltre 10 e fino a 20 mln: 50%.", [], "MIMIT — Scaglioni"),
        R("Origine dei beni", "OBBLIGO", "Beni prodotti in Stati UE/SEE (non confermato dalla pagina MIMIT).", [16], "reteagevolazioni.it; pmi.it", "SECONDARIA"),
        R("Comunicazioni GSE", "OBBLIGO", "Prenotazione (dal 12 giugno 2026), conferma dell'investimento con acquisizione del 20% (dal 21 luglio 2026), avanzamento e completamento tramite piattaforma GSE.", [57], "MIMIT — Procedure e scadenze"),
    ],
    "not_specified": [
        "Requisiti di risparmio energetico (la pagina MIMIT non li riporta)",
        "Regole dettagliate su pagamenti e tracciabilità",
        "Limiti su leasing e IVA",
        "Cumulo con altre agevolazioni",
        "Obblighi di mantenimento/cessione dei beni",
    ],
}

SABATINI: Dict[str, Any] = {
    "bando_id": "NUOVA-SABATINI",
    "name": "Beni strumentali — Nuova Sabatini",
    "issuer": "MIMIT",
    "status": "APERTO",
    "period": None,
    "legal_refs": [
        "Decreto interministeriale 19 gennaio 2024, n. 43", "Circolare n. 410823 del 6 dicembre 2022 (punto 7.4: spese non ammissibili)",
        "Decreto ministeriale 18 giugno 2025", "Legge di bilancio 2026 (rifinanziamento)", "D.L. 69/2013, art. 2, comma 4", "D.L. 34/2019, art. 21; L. 160/2019 (investimenti green)",
    ],
    "benefit": {
        "type": "CONTRIBUTO_IN_CONTO_INTERESSI",
        "summary": "Finanziamento bancario 20.000–4.000.000 € (max 5 anni) con contributo sugli interessi: 2,75% ordinari; 3,575% investimenti 4.0 e green; capitalizzazione 5% (micro/piccole) o 3,575% (medie). Garanzia fino all'80% del Fondo PMI.",
        "tiers": [{"label": "Ordinari", "rate_pct": 2.75}, {"label": "4.0 e green", "rate_pct": 3.575}],
    },
    "sources": [
        {"title": "MIMIT — Nuova Sabatini (scheda)", "url": "https://www.mimit.gov.it/it/incentivi/agevolazioni-per-gli-investimenti-delle-pmi-in-beni-strumentali-nuova-sabatini", "accessed": ACCESSED, "confidence": "PRIMARIA"},
        {"title": "MIMIT — Nuova Sabatini: FAQ", "url": "https://www.mimit.gov.it/it/assistenza/domande-frequenti/beni-strumentali-nuova-sabatini-domande-frequenti-faq", "accessed": ACCESSED, "confidence": "PRIMARIA"},
    ],
    "rules": {"eligible_categories": ["CAPITAL_ASSETS"], "requires_new_asset": True, "excluded_asset_natures": ["REAL_ESTATE"], "requires_cup": True, "vat_never_eligible": True},
    "rule_notes": {
        "eligible_categories": {"source": "La misura finanzia solo l'acquisto (anche in leasing) di beni strumentali, hardware, software e tecnologie digitali.", "confidence": "PRIMARIA"},
        "requires_new_asset": {"source": "MIMIT scheda e FAQ 6.8: solo beni «nuovi di fabbrica»; esclusi usati e rigenerati.", "confidence": "PRIMARIA"},
        "excluded_asset_natures": {"source": "MIMIT scheda: non ammissibili «terreni e fabbricati».", "confidence": "PRIMARIA"},
        "requires_cup": {"source": "FAQ 10.7: le fatture devono riportare il CUP e la dicitura «art. 2, c. 4, D.L. n. 69/2013».", "confidence": "PRIMARIA"},
        "vat_never_eligible": {"source": "FAQ 6.10: il contributo è calcolato sul programma di investimento al netto dell'IVA.", "confidence": "PRIMARIA"},
    },
    "requirements": [
        R("Beni nuovi di fabbrica", "OBBLIGO", "Ammessi solo beni strumentali nuovi di fabbrica; richiesta la dichiarazione liberatoria del fornitore (Allegato 4). Veicoli: solo nuovi non ancora immatricolati.", [19, 16], "FAQ 6.8, 6.9, 6.14"),
        R("Spese escluse", "DIVIETO", "Non sono ammissibili terreni e fabbricati, beni usati o rigenerati, immobilizzazioni in corso e acconti; impianti infissi al suolo esclusi.", [16], "MIMIT scheda; FAQ 6.2"),
        R("Mera sostituzione", "DIVIETO", "La mera sostituzione di beni esistenti non è ammissibile (es. sostituzione di un mezzo obsoleto con euro 6).", [16], "FAQ 6.3"),
        R("Costi accessori", "LIMITE", "Ammissibili i costi accessori (trasporto, montaggio…) purché capitalizzati sul costo del bene, esclusi dazi, altre tasse, costi e onorari di perizie e notarili.", [23], "FAQ 6.5"),
        R("IVA", "DIVIETO", "Il contributo è calcolato sull'investimento al netto dell'IVA.", [53, 54], "FAQ 6.10"),
        R("Leasing", "DIVIETO", "Il lease-back non è ammesso (variazione del sistema di acquisizione); il riscatto anticipato non comporta la perdita del contributo; ammesso l'acconto al fornitore incluso nel contratto di leasing.", [24], "FAQ 6.12, 2.12, 2.8"),
        R("Software", "INFO", "Ammessi software di base e applicativi; contributo maggiorato (3,575%) solo se rientra negli Allegati 6/B (investimenti 4.0).", [26], "FAQ 6.4"),
        R("Documenti di spesa", "OBBLIGO", "Fatture con CUP e dicitura di legge; per i fornitori esteri apposizione con scrittura indelebile o timbro.", [50], "FAQ 10.7"),
        R("Cumulo", "LIMITE", "Cumulabile con altri aiuti di Stato (anche de minimis) sugli stessi costi purché non si superi l'intensità massima; con PNRR nel rispetto del divieto di doppio finanziamento; ammesso il credito d'imposta 5.0 alle stesse condizioni.", [47, 48], "FAQ 9.2, 9.9, 9.10"),
        R("Tempi", "LIMITE", "Investimento da ultimare entro 12 mesi dalla stipula del finanziamento (18 per contratti dal 1/1/2022 al 31/12/2023); richiesta di erogazione entro 120 giorni; data di ultimazione = ultimo titolo di spesa o ultimo verbale di consegna (leasing).", [46, 57], "FAQ 10.1"),
        R("Elenco integrale delle spese non ammissibili", "DA_REVISIONARE", "Le FAQ rimandano al punto 7.4 della circolare 410823 senza riprodurlo: l'elenco integrale non è stato acquisito.", [16], "FAQ 6.11"),
    ],
    "not_specified": [
        "Regole su tracciabilità e modalità di pagamento (le FAQ non le riportano)",
        "Vincoli di mantenimento del bene dopo l'ultimazione (salvo subentro entro 3 anni)",
        "Limitazioni per fornitori collegati/parti correlate",
        "Intensità di aiuto massima per dimensione d'impresa (10% medie, 20% piccole per il settore «altro»: non codificata come regola unica)",
    ],
}

HORIZON: Dict[str, Any] = {
    "bando_id": "HORIZON-EUROPE-MGA",
    "name": "Horizon Europe — Model Grant Agreement (azioni a costi reali)",
    "issuer": "Commissione europea",
    "status": "PERMANENTE (le condizioni della singola call possono variare)",
    "period": None,
    "legal_refs": ["EU Grants: HE MGA — Multi & Mono, V1.2 del 01.06.2026 (Art. 6, 6.2, 6.3, 20; Data Sheet punto 3)"],
    "benefit": {"type": "SOVVENZIONE", "summary": "Sovvenzione a costi reali con tasso forfettario del 25% sui costi diretti ammissibili (esclusi subappalti). I tassi di finanziamento dipendono dalla call.", "tiers": []},
    "sources": [
        {"title": "HE MGA V1.2 (01.06.2026) — testo ufficiale, PDF letto direttamente", "url": "https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/common/agr-contr/general-mga_horizon-euratom_en.pdf",
         "accessed": ACCESSED, "confidence": "PRIMARIA"},
        {"title": "AGA — Annotated Grant Agreement V2.0 (01.04.2025)", "url": "https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/common/guidance/aga_en.pdf",
         "accessed": ACCESSED, "confidence": "PRIMARIA"},
    ],
    "rules": {"overhead_flat_rate_pct": 0.25, "overhead_flat_base": "DIRECT_EXCL_SUBCONTRACTING", "equipment_depreciation_only": True,
              "require_independent_supplier": True, "subcontracting_allowed": True},
    "rule_notes": {
        "overhead_flat_rate_pct": {"source": "MGA Data Sheet: «Indirect cost flat-rate: 25% of the eligible direct costs (categories A-D, except volunteers costs, subcontracting costs, financial support to third parties…)». Verificato sul PDF: un riassunto automatico riportava erroneamente 15%.", "confidence": "PRIMARIA"},
        "overhead_flat_base": {"source": "Stessa clausola: base = costi diretti ammissibili esclusi subappalti.", "confidence": "PRIMARIA"},
        "equipment_depreciation_only": {"source": "MGA Data Sheet: «Equipment: OPTION 1 by default: depreciation only». Altre opzioni possono essere scelte dalla call.", "confidence": "PRIMARIA"},
        "require_independent_supplier": {"source": "MGA Art. 6.2 B/C: acquisti con le pratiche abituali, best value for money e assenza di conflitto di interessi (Art. 12).", "confidence": "PRIMARIA"},
        "subcontracting_allowed": {"source": "MGA Art. 6.2 B: i costi di subappalto sono ammissibili se a costi effettivi e assegnati con le pratiche abituali.", "confidence": "PRIMARIA"},
    },
    "requirements": [
        R("Costi di personale", "LIMITE", "Costo giornaliero = costo annuo del personale / 215; le giornate dichiarate in tutte le sovvenzioni UE per persona e anno non possono superare 215 (meno l'eventuale congedo parentale). Devono essere identificabili e verificabili.", [3, 8], "MGA Art. 6.2 A.1"),
        R("Subappalto", "OBBLIGO", "Ammissibile a costi effettivi (incluse imposte come IVA non deducibile/non rimborsabile), assegnato con le pratiche di acquisto abituali che garantiscano best value for money e assenza di conflitto di interessi.", [32, 35, 54], "MGA Art. 6.2 B"),
        R("Costi di acquisto e attrezzature", "OBBLIGO", "Costi di acquisto ammissibili (incluse imposte come IVA non deducibile/non rimborsabile) con le stesse regole di acquisto; per le attrezzature, per default solo l'ammortamento (le call possono scegliere altre opzioni).", [17, 18, 32, 53, 54], "MGA Art. 6.2 C; Data Sheet"),
        R("Costi indiretti", "LIMITE", "Tasso forfettario del 25% dei costi diretti ammissibili (categorie A-D), esclusi volontari, subappalti, sostegno finanziario a terzi.", [36], "MGA Data Sheet punto 3"),
        R("Costi non ammissibili", "DIVIETO", "Rendimento del capitale e dividendi; debito e oneri del debito; accantonamenti per perdite future; interessi; perdite di cambio; spese bancarie sui trasferimenti; spese eccessive o sconsiderate; IVA deducibile o rimborsabile; costi durante la sospensione.", [16, 54, 59], "MGA Art. 6.3(a)"),
        R("Doppio finanziamento", "DIVIETO", "Non ammissibili costi dichiarati in altre sovvenzioni UE (o di Stati membri/paesi terzi/altri enti che attuano il bilancio UE), salvo le eccezioni previste.", [47], "MGA Art. 6.3(b)"),
        R("Personale della pubblica amministrazione", "DIVIETO", "Non ammissibili i costi del personale di una pubblica amministrazione per attività che rientrano nelle sue normali attività.", [16], "MGA Art. 6.3(c)"),
        R("Periodo dei costi", "LIMITE", "I costi devono riferirsi al periodo di attuazione dell'azione (Art. 4) e i costi forfettari si applicano solo a costi ammissibili.", [46], "MGA Art. 6.1"),
        R("Documentazione", "OBBLIGO", "Le unità di costo devono essere identificabili e verificabili, supportate da registri e documentazione.", [15, 16], "MGA Art. 6.1 e Art. 20"),
    ],
    "not_specified": [
        "Finestra temporale e importi: dipendono dalla singola call e dall'accordo di sovvenzione",
        "Tetto orario o giornaliero: il MGA usa il costo effettivo /215, non un massimale",
        "Massimali percentuali per consulenze: non previsti dal MGA",
    ],
}

TRANSIZIONE_50: Dict[str, Any] = {
    "bando_id": "TRANSIZIONE-5.0-2024-2025",
    "name": "Piano Transizione 5.0 — credito d'imposta 2024-2025",
    "issuer": "MIMIT / GSE",
    "status": "CHIUSO",
    "period": {"from": "2024-01-01", "to": "2025-12-31"},
    "legal_refs": [
        "Art. 38 D.L. 2 marzo 2024, n. 19 (conv. L. 29 aprile 2024, n. 56)", "Decreto interministeriale 24 luglio 2024",
        "Decreti direttoriali 6 agosto 2024, 11 settembre 2024, 6 novembre 2025", "Circolare operativa 16 agosto 2024, n. 25877",
        "Legge 30 dicembre 2024, n. 207, commi 427-429",
    ],
    "benefit": {
        "type": "CREDITO_D_IMPOSTA",
        "summary": "Credito d'imposta sulla quota di investimento, in funzione della riduzione dei consumi energetici (struttura 3-6/6-10/≥10%; processo 5-10/10-15/≥15%). Fino a 10 mln: 35%/40%/45%; oltre 10 mln (fino a 50): 5%/10%/15%. Limite 50 mln per impresa e anno.",
        "tiers": [{"up_to_eur": 10_000_000, "rate_pct": [35, 40, 45]}, {"up_to_eur": 50_000_000, "rate_pct": [5, 10, 15]}],
    },
    "sources": [
        {"title": "MIMIT — Piano Transizione 5.0", "url": "https://www.mimit.gov.it/it/incentivi/piano-transizione-5-0", "accessed": ACCESSED, "confidence": "PRIMARIA"},
        {"title": "GSE — Credito d'imposta Transizione 5.0: calcolo", "url": "https://www.gse.it/servizi-per-te/attuazione-misure-pnrr/transizione-5-0/il-calcolo-del-credito-d-imposta", "accessed": ACCESSED, "confidence": "PRIMARIA"},
    ],
    "rules": {"eligible_categories": ["CAPITAL_ASSETS", "TRAINING"], "min_energy_saving_pct": 0.03, "appraisal_threshold_eur": 0,
              "eligibility_start": "2024-01-01", "eligibility_end": "2025-12-31", "non_cumulable_funding_ids": ["TRANSIZIONE-4.0"]},
    "rule_notes": {
        "eligible_categories": {"source": "MIMIT: beni 4.0 (Allegati A e B L. 232/2016), software di monitoraggio energetico, autoproduzione FER e formazione del personale.", "confidence": "PRIMARIA"},
        "min_energy_saving_pct": {"source": "MIMIT: riduzione dei consumi di almeno il 3% per la struttura produttiva o del 5% per il processo (il motore codifica la soglia più bassa: 3%).", "confidence": "PRIMARIA"},
        "appraisal_threshold_eur": {"source": "MIMIT: certificazioni ex ante ed ex post rilasciate da valutatori indipendenti (EGE, ESCo, ingegneri, periti industriali).", "confidence": "INTERPRETAZIONE"},
        "eligibility_start": {"source": "MIMIT: investimenti nel biennio 2024-2025.", "confidence": "PRIMARIA"},
        "eligibility_end": {"source": "MIMIT: fino al 31 dicembre 2025.", "confidence": "PRIMARIA"},
        "non_cumulable_funding_ids": {"source": "MIMIT: i crediti 5.0 e 4.0 non sono cumulabili per i medesimi beni.", "confidence": "PRIMARIA"},
    },
    "requirements": [
        R("Stato della misura", "INFO", "CHIUSA: risorse esaurite (decreto 6 novembre 2025); sostituita dal Nuovo Piano Transizione 5.0 - Iperammortamento dal 12 giugno 2026. Utile per progetti già in corso o per confronto.", [], "MIMIT — Stato attuale"),
        R("Riduzione dei consumi", "LIMITE", "Almeno 3% sulla struttura produttiva o 5% sul processo interessato dall'investimento; semplificazioni dalla legge di bilancio 2025 (macchinari ammortizzati da oltre 24 mesi; contratti EPC con ESCo).", [21], "MIMIT — Requisiti"),
        R("Certificazioni ex ante ed ex post", "OBBLIGO", "Certificazione ex ante della riduzione dei consumi e certificazione ex post della realizzazione, da valutatori indipendenti abilitati.", [30], "MIMIT — Documenti"),
        R("Acconto", "OBBLIGO", "Pagamento di un acconto di almeno il 20% del costo totale degli investimenti (inclusi i costi accessori) e degli impianti di autoproduzione.", [52], "MIMIT — Tracciabilità/acconto"),
        R("Formazione", "LIMITE", "Formazione del personale ammessa fino al 10% degli investimenti e comunque max 300.000 € (limite non codificato come regola).", [16], "MIMIT — Spese ammissibili"),
        R("Cumulo", "LIMITE", "Cumulabile con altre agevolazioni (anche UE) purché non coprano le medesime quote di costo; non cumulabile con il credito Transizione 4.0 per i medesimi beni.", [47], "MIMIT — Cumulo; L. 207/2024"),
        R("Utilizzo del credito", "INFO", "Utilizzabile solo in compensazione (F24) dopo 10 giorni dalla comunicazione all'Agenzia delle entrate.", [], "MIMIT"),
    ],
    "not_specified": [
        "Elenco delle spese non ammissibili (la pagina non lo riporta)",
        "Trattamento di IVA e leasing (le FAQ n. 4.25 citano il riscatto di beni in leasing senza dettagli)",
        "Vincoli di mantenimento e destinazione d'uso post-investimento",
        "DNSH: una fonte di ricerca lo indica come condizione imprescindibile, la pagina MIMIT non lo cita — NON codificato",
    ],
}

FNC3: Dict[str, Any] = {
    "bando_id": "FNC3-2024",
    "name": "Fondo Nuove Competenze 3 — Competenze per le innovazioni",
    "issuer": "Ministero del Lavoro / ANPAL",
    "status": "CHIUSO (finestra 10/02-10/04/2025; dotazione incrementata con D.D. 9/2026)",
    "period": {"from": "2025-02-10", "to": "2025-04-10"},
    "legal_refs": ["Decreto direttoriale n. 439 del 5 dicembre 2024 (Avviso)", "Decreto direttoriale n. 9 del 9 gennaio 2026 (+125.952.000 €)", "Art. 88 D.L. 34/2020"],
    "benefit": {"type": "RIMBORSO_COSTO_DEL_LAVORO", "summary": "Rimborso del costo del lavoro delle ore di lavoro destinate alla formazione, in base ad accordi collettivi di rimodulazione dell'orario.", "tiers": []},
    "sources": [
        {"title": "Ministero del Lavoro — FNC3: pubblicato l'Avviso", "url": "https://lavoro.gov.it/notizie/pagine/fondo-nuove-competenze-3-competenze-per-le-innovazioni-pubblicato-avviso", "accessed": ACCESSED, "confidence": "PRIMARIA"},
        {"title": "Ministero del Lavoro — Fondo nuove competenze", "url": "https://www.lavoro.gov.it/temi-e-priorita/orientamento-e-formazione/focus/fondi-alle-imprese-la-formazione-continua/pagine-0", "accessed": ACCESSED, "confidence": "PRIMARIA"},
    ],
    "rules": {"eligible_categories": ["PERSONNEL"]},
    "rule_notes": {"eligible_categories": {"source": "Le pagine consultate indicano il rimborso del costo del lavoro; i costi di docenza non sono dettagliati.", "confidence": "INTERPRETAZIONE"}},
    "requirements": [
        R("Beneficiari", "OBBLIGO", "Datori di lavoro privati (anche a partecipazione pubblica) che abbiano sottoscritto accordi collettivi di rimodulazione dell'orario di lavoro finalizzati a percorsi formativi.", [15], "Ministero del Lavoro — Beneficiari"),
        R("Costo del lavoro", "INFO", "Il contributo è commisurato al costo del lavoro del personale per le ore dedicate alla formazione.", [2, 3], "Ministero del Lavoro"),
        R("Regole numeriche non acquisite", "DA_REVISIONARE", "Ore massime di formazione, calcolo della retribuzione oraria, oneri contributivi inclusi, tetti, regime di aiuto e requisiti dell'accordo non sono riportati nelle pagine consultate: serve il testo integrale dell'Avviso (D.D. 439/2024) e le FAQ.", [], "Assenti nelle fonti consultate"),
    ],
    "not_specified": [
        "Numero massimo di ore di formazione per lavoratore",
        "Modalità di calcolo della retribuzione oraria e inclusione degli oneri contributivi",
        "Percentuale di finanziamento e tetti per beneficiario",
        "Regime di aiuto (de minimis / GBER)",
        "Requisiti specifici dell'accordo collettivo",
    ],
}

SANDBOX: Dict[str, Any] = {
    "bando_id": "QUANTO-SANDBOX-60",
    "name": "QUANTO Sandbox — bando di prova a 60 criteri",
    "issuer": "QUANTO (fittizio)",
    "status": "SANDBOX",
    "period": {"from": "2026-01-01", "to": "2027-12-31"},
    "legal_refs": ["Bando fittizio: definisce tutte le regole per esercitare ogni criterio. Non è un bando reale."],
    "benefit": {"type": "SANDBOX", "summary": "Nessun beneficio reale. Serve a provare il motore su tutti i 60 criteri.", "tiers": []},
    "sources": [],
    "rules": {},  # riempito da demo.SANDBOX_RULES in bandi.py
    "rule_notes": {},
    "requirements": [
        R("Scopo", "INFO", "Il bando di prova attiva tutte le regole: usalo con lo scenario «Stress-test 46 voci» per vedere ogni criterio all'opera.", [], "QUANTO"),
    ],
    "not_specified": [],
}

BANDI: List[Dict[str, Any]] = [IPERAMMORTAMENTO, SABATINI, HORIZON, TRANSIZIONE_50, FNC3, SANDBOX]

REFERENCES: List[Dict[str, Any]] = [
    {
        "id": "DE-MINIMIS-2023-2831", "title": "Regolamento (UE) 2023/2831 — aiuti «de minimis»",
        "summary": "Massimale di 300.000 € per impresa unica su tre anni mobili (prima 200.000 €); in vigore dal 1° gennaio 2024 al 31 dicembre 2030. Per ogni nuova concessione si considera l'importo complessivo già concesso (o richiesto e non ancora concesso) nei tre anni precedenti.",
        "criteria": [49], "url": "https://eur-lex.europa.eu/legal-content/IT/TXT/PDF/?uri=OJ:L_202302831", "accessed": ACCESSED, "confidence": "SECONDARIA",
        "note": "Massimale letto da sintesi di enti/associazioni (Fon.Ter, Finanza & Fisco, incentivimpresa.it); testo EUR-Lex non letto integralmente.",
    },
]
