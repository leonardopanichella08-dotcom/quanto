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
ACCESSED_2 = "2026-09-23"
ACCESSED_3 = "2026-09-26"
ACCESSED_4 = "2026-09-27"


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

SMART_START: Dict[str, Any] = {
    "bando_id": "SMART-START-ITALIA",
    "name": "Smart&Start Italia — finanziamento a tasso zero per start-up innovative",
    "issuer": "Invitalia S.p.A. / MIMIT",
    "status": "APERTO (sportello sempre aperto, senza graduatorie né click day)",
    "period": {"from": None, "to": None},
    "extraction_status": "PARTIAL",
    "legal_refs": [
        "Art. 25, decreto-legge 18 ottobre 2012, n. 179, conv. L. 17 dicembre 2012, n. 221 (definizione di start-up innovativa), come modificato dalla legge 16 dicembre 2024, n. 193",
        "Decreto MIMIT 24 settembre 2014 (istitutivo)", "Decreto MIMIT 30 agosto 2019 (revisione disciplina)",
        "Decreto MIMIT 13 luglio 2026 (ultimo aggiornamento)", "Decreto interministeriale 24 novembre 2021 (risorse PNRR)",
    ],
    "benefit": {
        "type": "FINANZIAMENTO_A_TASSO_ZERO",
        "summary": "Finanziamento senza interessi (fino a 10 anni) pari all'80-90% delle spese ammissibili, in parte convertibile in contributo a fondo perduto; fondo perduto pieno al 30% per i comuni colpiti dal sisma 2016-2017.",
        "tiers": [{"label": "Finanziamento base", "rate_pct": 80}, {"label": "Start-up a prevalenza femminile/giovanile o con ricercatore PhD", "rate_pct": 90},
                   {"label": "Fondo perduto — comuni sisma 2016-2017", "rate_pct": 30}],
    },
    "sources": [
        {"title": "MIMIT — Sostegno alle startup innovative (Smart & Start Italia)", "url": "https://www.mimit.gov.it/it/incentivi/sostegno-alle-startup-innovative-smart-start-italia",
         "accessed": ACCESSED_4, "confidence": "PRIMARIA"},
    ],
    "rules": {"eligible_categories": ["CAPITAL_ASSETS", "CONSULTING", "PERSONNEL"]},
    "rule_notes": {
        "eligible_categories": {"source": "MIMIT: immobilizzazioni materiali (impianti, macchinari, attrezzature tecnologiche nuovi), immobilizzazioni immateriali (brevetti, marchi, licenze, know-how), servizi funzionali (progettazione, consulenze specialistiche, marketing, collaborazioni di ricerca) e personale dipendente/collaboratori. È ammesso anche capitale circolante fino al 20% (materie prime, servizi, hosting), non rappresentabile con le categorie di costo del motore.", "confidence": "PRIMARIA"},
    },
    "requirements": [
        R("Beneficiari", "OBBLIGO", "Start-up innovative iscritte alla sezione speciale del registro imprese con i requisiti dell'art. 25 D.L. 179/2012 (come modificato dalla L. 193/2024); ammesse anche persone fisiche che costituiscono la start-up entro 30 giorni dall'ammissione e imprese estere con sede operativa in Italia.", [34], "MIMIT — Beneficiari"),
        R("Importo del piano", "LIMITE", "Piani di spesa tra 100.000 € e 1.500.000 €, da concludere entro 24 mesi dalla stipula del contratto di finanziamento.", [46], "MIMIT — Importi"),
        R("Intensità del finanziamento", "INFO", "Finanziamento a tasso zero (durata massima 10 anni) pari all'80% delle spese ammissibili; 90% se la start-up è composta interamente da donne e/o giovani under 35, o include un ricercatore con dottorato da non più di 6 anni; per le regioni del Mezzogiorno la restituzione richiesta è pari al 70% dell'importo finanziato.", [48], "MIMIT — Intensità dell'agevolazione"),
        R("Servizi di tutoraggio", "INFO", "10.000 € di servizi di tutoraggio tecnico-gestionale per le start-up costituite da non più di 36 mesi.", [], "MIMIT — Tutoraggio"),
        R("Conversione in fondo perduto", "INFO", "Fino al 50% delle somme investite da soggetti terzi o soci persone fisiche può essere convertito in contributo a fondo perduto, entro il 50% del totale delle agevolazioni concesse.", [48], "MIMIT — Conversione"),
        R("Fondo perduto zone sismiche", "INFO", "Contributo a fondo perduto pari al 30% delle spese per le imprese nei comuni colpiti dagli eventi sismici 2016-2017.", [48], "MIMIT — Sezione sisma"),
        R("Regime di aiuto", "OBBLIGO", "Regolamenti (UE) n. 1407/2013 (de minimis), n. 651/2014 (GBER) e n. 717/2014 (pesca).", [48, 49], "MIMIT — Regime di aiuto"),
        R("Gestione e domanda", "INFO", "Gestito da Invitalia S.p.A.; domanda esclusivamente tramite la piattaforma web dedicata; valutazione su competenze tecniche del team, carattere innovativo, sostenibilità economico-finanziaria e fattibilità tecnica; erogazione per stati di avanzamento, con rendicontazione a costi standard per il personale.", [57], "MIMIT — Modalità di presentazione e valutazione"),
        R("Regole non acquisite", "DA_REVISIONARE", "Non risultano dalla pagina: elenco ATECO ammessi/esclusi, dettaglio dei criteri di valutazione a punteggio, condizioni esatte per il capitale circolante (20%) e trattamento IVA.", [], "Assenti nella pagina MIMIT consultata"),
    ],
    "not_specified": [
        "Elenco ATECO ammessi/esclusi", "Dettaglio dei criteri di valutazione a punteggio",
        "Condizioni esatte per il capitale circolante (limite 20%)", "Trattamento IVA sulle spese ammissibili",
        "Testo integrale del Decreto 13 luglio 2026",
    ],
}

INVESTIMENTI_SOSTENIBILI_40: Dict[str, Any] = {
    "bando_id": "INVESTIMENTI-SOSTENIBILI-4.0-2026",
    "name": "Investimenti Sostenibili 4.0 — Bando 2026 (PN RIC 2021-2027)",
    "issuer": "Invitalia S.p.A. / MIMIT",
    "status": "APERTO (invio domande dal 6 ottobre 2026)",
    "period": {"from": "2026-10-06", "to": None},
    "legal_refs": [
        "Programma Nazionale «Ricerca, Innovazione e Competitività per la transizione verde e digitale» FESR 2021-2027",
        "Art. 1, comma 101, legge 30 dicembre 2023, n. 213 (obbligo di copertura assicurativa contro le calamità naturali)",
    ],
    "benefit": {
        "type": "CONTRIBUTO_E_FINANZIAMENTO_MISTO",
        "summary": "Contributo in conto impianti e finanziamento agevolato che coprono complessivamente fino al 75% delle spese ammissibili.",
        "tiers": [{"label": "Copertura complessiva (contributo + finanziamento agevolato)", "rate_pct": 75}],
    },
    "sources": [
        {"title": "Invitalia — Investimenti sostenibili 4.0 – Bando 2026", "url": "https://www.invitalia.it/incentivi-e-strumenti/investimenti-sostenibili-40-bando-2026",
         "accessed": ACCESSED_4, "confidence": "PRIMARIA"},
    ],
    "rules": {"eligible_categories": ["CAPITAL_ASSETS"], "contribution_rate_pct": 0.75},
    "rule_notes": {
        "eligible_categories": {"source": "Invitalia: agevolazione erogata come «contributo in conto impianti», tipico degli investimenti in beni strumentali; la pagina non riporta un elenco analitico delle voci di spesa ammissibili.", "confidence": "INTERPRETAZIONE"},
        "contribution_rate_pct": {"source": "Invitalia: «contributo in conto impianti e finanziamento agevolato, che coprono fino al 75% delle spese ammissibili» — qui il motore codifica la copertura complessiva, senza distinguere la quota a fondo perduto da quella di finanziamento.", "confidence": "PRIMARIA"},
    },
    "requirements": [
        R("Beneficiari e territorio", "OBBLIGO", "Imprese di micro, piccola e media dimensione con sede in Molise, Basilicata, Calabria, Campania, Puglia, Sicilia e Sardegna.", [34], "Invitalia — Destinatari"),
        R("Intensità dell'agevolazione", "LIMITE", "Contributo in conto impianti e finanziamento agevolato che coprono complessivamente fino al 75% delle spese ammissibili.", [48], "Invitalia — Agevolazioni"),
        R("Calendario", "INFO", "Precompilazione della domanda dalle ore 12:00 del 10 settembre 2026; presentazione formale dalle ore 10:00 del 6 ottobre 2026, esclusivamente per via telematica tramite l'area riservata Invitalia (SPID o CIE).", [46], "Invitalia — Tempistiche"),
        R("Dotazione finanziaria", "INFO", "447,6 milioni di euro disponibili, al lordo degli oneri di gestione dell'Agenzia.", [], "Invitalia — Risorse"),
        R("Requisito assicurativo 2026", "OBBLIGO", "Le imprese devono essere in regola con l'obbligo di copertura assicurativa contro le calamità naturali (art. 1, comma 101, L. 213/2023).", [34], "Invitalia — Nuovo requisito 2026"),
        R("Classificazione ATECO", "INFO", "Le attività economiche sono classificate secondo ATECO 2025.", [34], "Invitalia — Classificazione"),
        R("Regole non acquisite", "DA_REVISIONARE", "La pagina non riporta: importo minimo/massimo di progetto, elenco analitico delle spese ammissibili, ripartizione esatta tra fondo perduto e finanziamento agevolato nel 75%, regime di aiuto, data di chiusura dello sportello. Serve il testo integrale del bando.", [], "Assenti nella pagina Invitalia consultata"),
    ],
    "not_specified": [
        "Importo minimo e massimo di progetto", "Elenco analitico delle spese ammissibili",
        "Ripartizione tra fondo perduto e finanziamento agevolato nel 75%", "Regime di aiuto (de minimis / GBER)",
        "Data di chiusura dello sportello",
    ],
}

FONDO_GARANZIA: Dict[str, Any] = {
    "bando_id": "FONDO-GARANZIA-PMI",
    "name": "Fondo di Garanzia per le PMI",
    "issuer": "Mediocredito Centrale (gestore) / MIMIT",
    "status": "APERTO (modalità prorogate per tutto il 2026)",
    "period": {"from": None, "to": "2026-12-31"},
    "legal_refs": [
        "Decreto-legge 31 dicembre 2025, n. 200, art. 14, comma 1 (proroga 2026)",
        "Circolare Mediocredito Centrale n. 1/2026 (gestore del Fondo)",
        "Art. 15-bis del D.L. 145/2023 (\"Decreto Anticipi\")",
        "Legge 30 dicembre 2024, n. 207",
    ],
    "benefit": {
        "type": "GARANZIA_PUBBLICA",
        "summary": "Garanzia pubblica su finanziamenti bancari a PMI e professionisti: non è un contributo diretto sulle spese di progetto, riduce il rischio di credito per la banca (spesso condizione per ottenere il finanziamento).",
        "tiers": [{"label": "Liquidità", "rate_pct": 50}, {"label": "Investimento", "rate_pct": 80}, {"label": "Nuova Sabatini / importo ridotto / microcredito", "rate_pct": 80},
                   {"label": "PMI innovative, start-up innovative, incubatori certificati", "rate_pct": 80}],
    },
    "sources": [
        {"title": "Mediocredito Centrale — Prorogate per il 2026 le modalità di funzionamento del Fondo di garanzia",
         "url": "https://www.mcc.it/primopiano/notizie/prorogate-per-il-2026-le-modalita-di-funzionamento-del-fondo-di-garanzia/", "accessed": ACCESSED_2, "confidence": "PRIMARIA"},
        {"title": "fondidigaranzia.it — Home (dati operativi, beneficiari, sezioni speciali)", "url": "https://www.fondidigaranzia.it/", "accessed": ACCESSED_2, "confidence": "PRIMARIA"},
        {"title": "MIMIT — Disposizioni Operative del Fondo di Garanzia PMI (testo integrale, 202 pagine: definizioni e struttura generale; le date dei decreti citati arrivano al 2017, i tassi e i plafond attuali sono nella Circolare MCC 1/2026)",
         "url": "https://www.mimit.gov.it/images/stories/normativa/disposizioni_fondo_di_garanzia.pdf", "accessed": ACCESSED_3, "confidence": "PRIMARIA"},
        {"title": "pmi.it — Fondo di Garanzia PMI 2026: regole confermate (importo massimo e plafond, fonte non ufficiale)",
         "url": "https://www.pmi.it/finanza/investimenti-pmi/483436/fondo-garanzia-pmi-regole-2026.html", "accessed": ACCESSED_2, "confidence": "SECONDARIA"},
    ],
    "rules": {},
    "rule_notes": {},
    "requirements": [
        R("Percentuali di copertura", "INFO", "50% per finanziamenti a fronte di liquidità; 80% per finanziamenti a fronte di investimento, operazioni Nuova Sabatini a importo ridotto, microcredito, e per PMI innovative/start-up innovative/incubatori certificati.", [], "MCC — comunicazione proroga 2026"),
        R("Natura dello strumento", "INFO", "È una garanzia pubblica su un finanziamento bancario, non un contributo a fondo perduto: riduce il rischio per la banca ma non copre direttamente le spese del progetto. Per questo non attiva regole di voce di costo del motore (non ha una «intensità di aiuto» sulle spese, ma una percentuale di copertura sul prestito).", [], "Valutazione redazionale, in base alla natura dello strumento", "INTERPRETAZIONE"),
        R("Forme della garanzia", "INFO", "Tre forme: Garanzia Diretta (il Fondo garantisce direttamente il soggetto finanziatore), Controgaranzia (il Fondo garantisce un Confidi o un altro fondo di garanzia che a sua volta garantisce il finanziamento) e Cogaranzia (il Fondo garantisce insieme a un Confidi, un altro fondo o il FEI).", [], "MIMIT — Disposizioni Operative, Parte I, Definizioni"),
        R("Beneficiari finali", "OBBLIGO", "PMI (micro, piccole, medie secondo le soglie UE: medie <250 occupati e ≤50 mln di fatturato o ≤43 mln di bilancio; piccole <50 occupati e ≤10 mln; micro <10 occupati e ≤2 mln), Consorzi tra PMI e Professionisti iscritti a un ordine o associazione professionale riconosciuta, valutati economicamente sani secondo il Modello di valutazione (rating) del Gestore.", [34], "MIMIT — Disposizioni Operative, Parte I, lett. kkk, ss"),
        R("Sezioni speciali", "INFO", "Sezioni dedicate esistono per: imprese femminili e donne professioniste (Dipartimento Pari Opportunità), microcredito, autotrasporto merci conto terzi, imprese dell'indotto di aziende in amministrazione straordinaria, oltre a quelle regionali e tematiche più recenti (Sicilia, Emilia-Romagna, Piemonte, Veneto, Trento, Marche, Just Transition Fund, ricerca e innovazione).", [], "MIMIT — Disposizioni Operative, Parte I, lett. z, aa, eee, fff, ggg; fondidigaranzia.it — Home"),
        R("Regime di aiuto", "DA_REVISIONARE", "Le Disposizioni Operative (testo del 2017) citano i regolamenti de minimis UE 1407/2013, 1408/2013 (agricolo) e 717/2014 (pesca): questi sono stati superati dal Regolamento (UE) 2023/2831, già in uso per gli altri bandi di questo catalogo. Non confermato se le operazioni più recenti del Fondo si appoggino anche al Regolamento (UE) n. 651/2014 (GBER) in alternativa al de minimis.", [48, 49], "MIMIT — Disposizioni Operative, Parte I, lett. p; incrocio con REFERENCES di questo catalogo"),
        R("Importo massimo e plafond", "DA_REVISIONARE", "Fonti non ufficiali indicano un importo massimo garantito di 5 milioni di euro per impresa e un plafond 2026 di 140 miliardi di euro complessivi; non confermati su una pagina ufficiale MCC letta direttamente (rimandano alla Circolare 1/2026, non ancora acquisita in testo integrale).", [], "pmi.it", "SECONDARIA"),
    ],
    "not_specified": [
        "Importo massimo garantito per impresa e plafond complessivo (solo da fonti non ufficiali)",
        "Costo della garanzia (commissioni) per fascia di rating (il Modello di valutazione è alla Parte VI delle Disposizioni Operative, non ancora letta per intero: 202 pagine)",
        "Elenco completo dei settori/finanziamenti esclusi",
        "Conferma se il regime di aiuto corrente sia ancora de minimis puro o preveda anche il GBER",
        "Testo integrale della Circolare MCC n. 1/2026 con le tabelle aggiornate (non acquisito)",
    ],
}

SIMEST_394: Dict[str, Any] = {
    "bando_id": "SIMEST-FONDO-394-PNRR",
    "name": "Fondo 394/81 — Finanziamenti agevolati per Transizione Digitale ed Ecologica",
    "issuer": "SIMEST (Gruppo CDP) / MAECI",
    "status": "APERTO (sportello a fondo rotativo)",
    "period": {"from": "2024-10-28", "to": None},
    "legal_refs": [
        "Art. 2, comma 1, D.L. 28 maggio 1981, n. 251, conv. L. 29 luglio 1981, n. 394 (Fondo 394/81)",
        "Art. 6 D.L. 25 giugno 2008, n. 112, conv. L. 6 agosto 2008, n. 133",
        "Regolamento (UE) 2023/2831 della Commissione, 13 dicembre 2023 (aiuti «de minimis»)",
        "Art. 72, comma 1, lett. d), D.L. 17 marzo 2020, n. 18, conv. L. 24 aprile 2020, n. 27 (Cofinanziamento a fondo perduto)",
        "Decreto MAECI 1° giugno 2023 (disciplina degli strumenti finanziari a sostegno dell'internazionalizzazione)",
        "Art. 1, comma 469, L. 30 dicembre 2024, n. 207; art. 17, comma 5, D.L. 30 giugno 2025, n. 95, conv. L. 8 agosto 2025, n. 118; art. 1, comma 1, lett. b), D.L. 3 aprile 2026, n. 42",
    ],
    "benefit": {
        "type": "FINANZIAMENTO_AGEVOLATO_MISTO",
        "summary": "Finanziamento a tasso agevolato (aggiornato mensilmente, mai negativo) della durata di 6 anni (2 di preammortamento + 4 di rimborso), abbinabile a una quota di Cofinanziamento a fondo perduto (10% o 20% dell'importo, secondo i requisiti dell'impresa, entro tetti in euro ed entro il plafond de minimis).",
        "tiers": [{"label": "Cofinanziamento — imprese energivore/efficientamento energetico", "rate_pct": 20}, {"label": "Cofinanziamento — altri requisiti (Sud Italia, certificazioni, giovanile, femminile, export ≥20%, innovativa)", "rate_pct": 10}],
    },
    "sources": [
        {"title": "SIMEST — Circolare n. 4/394/2023 «Transizione Digitale o Ecologica» (aggiornamento del 30 luglio 2026) — testo integrale letto",
         "url": "https://www.simest.it/app/uploads/2026/08/Circolare-4-394-2023-DE-30.07.2026.pdf", "accessed": ACCESSED_3, "confidence": "PRIMARIA"},
        {"title": "SIMEST — Comunicato: dal Comitato Agevolazioni via libera al nuovo Fondo 394 finanziato dall'Unione europea",
         "url": "https://www.simest.it/media/comunicati-stampa/simest-nuovo-fondo-394/", "accessed": ACCESSED_2, "confidence": "PRIMARIA"},
    ],
    "rules": {"eligible_categories": ["CAPITAL_ASSETS", "CONSULTING"], "max_consulting_percentage": 0.05},
    "rule_notes": {
        "eligible_categories": {"source": "Circolare § 5.1: spese ammissibili per attrezzature tecnologiche, software, certificazioni, investimenti per sostenibilità ambientale, rafforzamento patrimoniale, consulenze (§ 5.1 punti 4-5). § 5.2 esclude esplicitamente le spese correnti relative al personale dell'impresa richiedente: PERSONNEL non è ammissibile.", "confidence": "PRIMARIA"},
        "max_consulting_percentage": {"source": "Circolare § 5.1 punto 5: spese per consulenze finalizzate alla presentazione e gestione della domanda «per un valore fino a un massimo del 5% dell'importo deliberato e comunque non superiore a € 100.000».", "confidence": "PRIMARIA"},
    },
    "requirements": [
        R("Importo dell'intervento", "LIMITE", "Minimo 10.000 €. Massimo il minore tra il 35% dei ricavi medi degli ultimi due bilanci e un tetto per dimensione d'impresa: 500.000 € (micro impresa), 2.500.000 € (PMI, PMI innovative, Start Up Innovative), 5.000.000 € (altre imprese).", [7, 48], "Circolare § 3.1"),
        R("Destinazione dell'importo", "LIMITE", "Almeno il 50% a investimenti digitali e/o ecologici; fino al 50% a «Ulteriori Investimenti» di rafforzamento patrimoniale (incremento capitale sociale/finanziamento soci a controllate, tetto 600.000 €). Quota elevabile all'80% (Balcani Occidentali, imprese con interessi USA) o al 90% (eventi meteorologici eccezionali, imprese energivore, misura «Energia per la Competitività Internazionale»).", [16], "Circolare § 2.1"),
        R("Cofinanziamento a fondo perduto — percorso A", "LIMITE", "Fino al 20% dell'importo (30% se PMI) e comunque max 200.000 €, entro il plafond de minimis, per imprese energivore o con percorso di efficientamento energetico, o rientranti nella misura «Energia per la Competitività Internazionale» (per domande presentate entro il 31/12/2026).", [48, 49], "Circolare § 3.2 lett. a"),
        R("Cofinanziamento a fondo perduto — percorso B", "LIMITE", "Fino al 10% dell'importo e comunque max 100.000 €, per PMI del Sud Italia (Abruzzo, Basilicata, Calabria, Campania, Molise, Puglia, Sardegna, Sicilia) costituite da almeno 6 mesi, oppure con certificazioni ambientali/di sostenibilità, oppure giovanile o femminile (≥60% quote), oppure con fatturato export medio ≥20%, oppure PMI innovativa/Start Up Innovativa.", [48, 49], "Circolare § 3.2 lett. b"),
        R("Durata e rimborso", "INFO", "Durata 6 anni dalla stipula (2 di preammortamento + 4 di rimborso, estendibile di 2 anni per energivore/USA/IA/eventi meteo). Rimborso in 8 rate semestrali posticipate a capitale costante (7 in caso di proroga del preammortamento; 12 o 11 con l'estensione biennale).", [55], "Circolare § 3.4, § 3.5"),
        R("Tasso e interessi di mora", "INFO", "Tasso agevolato aggiornato mensilmente (mai inferiore a zero). Interessi di mora: tasso di riferimento UE maggiorato del 4%.", [], "Circolare § 3.6, § 3.7"),
        R("Esenzione da garanzie", "INFO", "Esenti le imprese in classe di Scoring 1-2, le PMI innovative e le Start Up Innovative; su richiesta anche le imprese con interessi nei Balcani Occidentali e (per domande entro il 31/12/2026) le imprese energivore.", [], "Circolare § 3.6"),
        R("Spese ammissibili", "OBBLIGO", "Transizione digitale (attrezzature tecnologiche, software, consulenze digitali, disaster recovery, blockchain solo per notarizzazione, industria 4.0, certificazioni digitali, spese IA), transizione ecologica (investimenti di sostenibilità ambientale, certificazioni/diagnosi energetica), rafforzamento patrimoniale (nei limiti del § 2.1), consulenze di conformità normativa, consulenze per la domanda (max 5%, tetto 100.000 €).", [16, 31], "Circolare § 5.1"),
        R("Spese escluse", "DIVIETO", "Spese connesse all'esportazione (commissioni sul venduto, rete di distribuzione), spese commerciali dirette (assistenza post-vendita, trasporto, stoccaggio), spese correnti dell'impresa incluso il personale, consulenze continuative/ordinarie (fiscale, legale, pubblicità), spese nei settori esclusi, spese già coperte da altro aiuto non cumulabile.", [16, 35], "Circolare § 5.2"),
        R("Indipendenza dei consulenti", "OBBLIGO", "I consulenti devono essere terzi indipendenti, a condizioni di mercato, con dichiarazione di indipendenza; le prestazioni non devono essere continuative/periodiche né rientrare nei costi di esercizio ordinari.", [32], "Circolare § 5.1"),
        R("Requisiti di ammissibilità dell'impresa", "OBBLIGO", "Sede legale e operativa in Italia; iscritta al registro imprese e in stato di attività; almeno 2 bilanci depositati; conformità alla normativa ambientale; DURC regolare; nessuna procedura concorsuale in corso; Scoring fuori dalle classi 10-12; non «in difficoltà» ai sensi del Reg. UE 651/2014 art. 2.18; obbligo di Polizza Catastrofale assolto; almeno un requisito di vocazione estera (fatturato export ≥10%, o ≥3% per energivore, o ≥10% di fatturato verso clienti esportatori, o impegno al 100% delle risorse su spese IA).", [34, 45], "Circolare § 2.2"),
        R("Rendicontazione", "OBBLIGO", "Prima rendicontazione obbligatoria entro 12 mesi dalla stipula; rendicontazione finale entro 30 giorni dal termine del Periodo di Realizzazione (24 mesi dal CUP, prorogabile di 6 mesi); pagamenti tracciati su conto corrente dedicato con CUP in fattura, mai per compensazione.", [50, 52, 57], "Circolare § 5.3, definizioni"),
        R("Altre linee del Fondo 394/81", "DA_REVISIONARE", "Questa scheda copre solo la linea «Transizione Digitale o Ecologica» (Circolare 4/394/2023). Il Fondo ha altre linee attive con circolari separate non ancora lette per intero (es. Circolare 7/394/2023 partecipazione a fiere/mercati, Circolare 8/394/2023): non rappresentate qui.", [], "simest.it/app/uploads/ — elenco circolari, non ancora acquisite"),
    ],
    "not_specified": [
        "Le altre linee di intervento del Fondo 394/81 (fiere/missioni, e-commerce, patrimonializzazione pura): circolari separate non lette",
        "Tabella completa delle spese ammissibili all'ambito Intelligenza Artificiale (Allegato 2 alla Circolare, non acquisito)",
        "Dettaglio del modello di Scoring (classi di merito di credito Mediocredito Centrale)",
        "Elenco integrale delle cause di revoca e decadenza",
    ],
}

FVG_VALIDAZIONE: Dict[str, Any] = {
    "bando_id": "FVG-VALIDAZIONE-TRL-2026",
    "name": "Validazione di idee e tecnologie innovative (TRL 6-8) — PR FESR FVG 2021-2027, Bando 2026",
    "issuer": "Regione Autonoma Friuli Venezia Giulia",
    "status": "A SPORTELLO RICORRENTE (finestra 27/07-21/09/2026 chiusa; riapre 1° febbraio-31 marzo e 1° giugno-31 agosto, ogni anno)",
    "period": {"from": "2026-07-27", "to": None},
    "legal_refs": [
        "Deliberazione della Giunta regionale n. 916 del 26 giugno 2026",
        "Legge regionale 12 dicembre 2022, n. 22, art. 7, commi 56, 57 e 60",
        "Legge regionale 20 marzo 2000, n. 7", "Decreto del Presidente della Regione n. 61/2026",
        "Regolamento (UE) n. 651/2014 (GBER)",
    ],
    "benefit": {
        "type": "CONTRIBUTO_IN_CONTO_CAPITALE",
        "summary": "Contributo a fondo perduto differenziato per TRL (livello di maturità tecnologica) e dimensione d'impresa: dal 25% (grande impresa, TRL 7-8) all'80% (università/organismi di ricerca).",
        "tiers": [
            {"label": "TRL 6 — micro/piccola impresa", "rate_pct": 55}, {"label": "TRL 6 — micro/piccola impresa innovativa/PMI innovativa", "rate_pct": 70},
            {"label": "TRL 6 — media impresa", "rate_pct": 40}, {"label": "TRL 6 — media impresa innovativa", "rate_pct": 50}, {"label": "TRL 6 — grande impresa", "rate_pct": 30},
            {"label": "TRL 7-8 — micro/piccola impresa", "rate_pct": 45}, {"label": "TRL 7-8 — media impresa", "rate_pct": 35}, {"label": "TRL 7-8 — grande impresa", "rate_pct": 25},
            {"label": "Università/organismi di ricerca (ogni TRL)", "rate_pct": 80},
        ],
    },
    "sources": [
        {"title": "Regione FVG — Bando 2026 per contributi a fondo perduto a progetti di validazione di idee e tecnologie innovative TRL 6-7-8",
         "url": "https://www.regione.fvg.it/rafvg/cms/RAFVG/ricerca/fare-ricerca/FOGLIA21/articolo.html", "accessed": ACCESSED_4, "confidence": "PRIMARIA"},
    ],
    "rules": {"eligible_categories": ["PERSONNEL", "CAPITAL_ASSETS", "CONSULTING"], "max_consulting_percentage": 0.45,
              "overhead_flat_rate_pct": 0.10, "overhead_flat_base": "PERSONNEL"},
    "rule_notes": {
        "eligible_categories": {"source": "Regione FVG: personale (costi standard), strumenti e attrezzature, servizi di consulenza qualificata, prestazioni e servizi, beni immateriali, realizzazione di prototipi, materiali di consumo, spese generali forfettarie. Beni immateriali/materiali di consumo/prototipi non hanno una categoria distinta nel motore: qui accorpati a CAPITAL_ASSETS/CONSULTING per approssimazione.", "confidence": "INTERPRETAZIONE"},
        "max_consulting_percentage": {"source": "Regione FVG: «la somma delle spese per i servizi di consulenza qualificata, le prestazioni e servizi e la realizzazione di prototipi è ammissibile nel limite massimo del 45% della spesa presentata» — il tetto ufficiale copre tre voci insieme (consulenza+prestazioni+prototipi), qui codificato solo sulla voce consulenze del motore: una sovra-approssimazione se le tre voci sono usate insieme.", "confidence": "INTERPRETAZIONE"},
        "overhead_flat_rate_pct": {"source": "Regione FVG: spese generali forfettarie al 10% dei costi di personale.", "confidence": "PRIMARIA"},
        "overhead_flat_base": {"source": "Regione FVG: base di calcolo del forfait sono i costi di personale.", "confidence": "PRIMARIA"},
    },
    "requirements": [
        R("Beneficiari", "OBBLIGO", "Imprese del territorio regionale di ogni dimensione (comprese start-up innovative e spin-off), università insediate in regione, organismi di ricerca pubblici o di diritto pubblico/privato insediati in regione.", [34], "Regione FVG — Beneficiari"),
        R("Intensità di aiuto per TRL 6 (ricerca industriale)", "INFO", "Micro/piccola impresa 55% (70% se start-up/PMI innovativa); media impresa 40% (50% se innovativa); grande impresa 30%; università/organismi di ricerca 80%.", [48], "Regione FVG — Intensità TRL 6"),
        R("Intensità di aiuto per TRL 7-8 (sviluppo sperimentale)", "INFO", "Micro/piccola impresa 45%; media impresa 35%; grande impresa 25%; università/organismi di ricerca 80%.", [48], "Regione FVG — Intensità TRL 7-8"),
        R("Limite alle consulenze, prestazioni e prototipi", "LIMITE", "La somma di consulenza qualificata, prestazioni/servizi e realizzazione di prototipi non può superare il 45% della spesa presentata.", [31], "Regione FVG — Vincolo di spesa"),
        R("Spese generali", "INFO", "Forfettario del 10% dei costi di personale.", [36], "Regione FVG — Spese generali"),
        R("Contributo massimo e durata per TRL", "LIMITE", "TRL 6: max 150.000 €, durata 6-12 mesi. TRL 7: max 250.000 €, durata 6-18 mesi. TRL 8: max 500.000 €, durata 6-24 mesi.", [46], "Regione FVG — Importi e durata"),
        R("Calendario a sportello", "INFO", "Prima finestra 2026: dalle ore 10:00 del 27 luglio alle ore 16:00 del 21 settembre 2026 (chiusa). Finestre successive ricorrenti: 1° febbraio-31 marzo e 1° giugno-31 agosto, ogni anno.", [46], "Regione FVG — Calendario sportello"),
        R("Dotazione finanziaria", "INFO", "2.217.871 €, integrabile con ulteriori risorse se disponibili.", [], "Regione FVG — Dotazione"),
        R("Limiti di partecipazione", "LIMITE", "Massimo una domanda per sportello per impresa; massimo due domande per dipartimento universitario.", [], "Regione FVG — Limiti"),
        R("Regime di aiuto", "OBBLIGO", "Regolamento (UE) n. 651/2014 (GBER); il regime de minimis è escluso per le imprese, salvo per le garanzie.", [48, 49], "Regione FVG — Regime di aiuto"),
        R("Regole di dettaglio non acquisite", "DA_REVISIONARE", "Tabelle standard di costo del personale (UCS), procedura di valutazione a punteggio, elenco analitico delle spese escluse e cause di esclusione non risultano dalla pagina di sintesi: serve il testo integrale della DGR 916/2026 e dell'allegato.", [], "Assenti nella pagina di sintesi consultata"),
    ],
    "not_specified": [
        "Tabelle standard di costo del personale (UCS)", "Procedura di valutazione a punteggio",
        "Elenco analitico delle spese escluse", "Cause di esclusione ed eventuali revoche",
        "Testo integrale della DGR 916/2026 (non ancora letto per intero)",
    ],
}

BANDI: List[Dict[str, Any]] = [IPERAMMORTAMENTO, SABATINI, HORIZON, SMART_START, INVESTIMENTI_SOSTENIBILI_40, FONDO_GARANZIA, SIMEST_394, FVG_VALIDAZIONE]

REFERENCES: List[Dict[str, Any]] = [
    {
        "id": "DE-MINIMIS-2023-2831", "title": "Regolamento (UE) 2023/2831 — aiuti «de minimis»",
        "summary": "Massimale di 300.000 € per impresa unica su tre anni mobili (prima 200.000 €); in vigore dal 1° gennaio 2024 al 31 dicembre 2030. Per ogni nuova concessione si considera l'importo complessivo già concesso (o richiesto e non ancora concesso) nei tre anni precedenti.",
        "criteria": [49], "url": "https://eur-lex.europa.eu/legal-content/IT/TXT/PDF/?uri=OJ:L_202302831", "accessed": ACCESSED, "confidence": "SECONDARIA",
        "note": "Massimale letto da sintesi di enti/associazioni (Fon.Ter, Finanza & Fisco, incentivimpresa.it); testo EUR-Lex non letto integralmente.",
    },
]
