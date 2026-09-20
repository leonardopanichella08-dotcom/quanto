"""Scheda di controllo per il consulente (schema FKOS: coda di verifica / Pannello di Ingestion, uso interno).

Per ogni bando spiega, in parole semplici:
- **cosa dicono** i documenti letti (regole con la fonte),
- **cosa non dicono** (regole non trovate) e perché conta: quale controllo resta spento,
- **cosa cercare e come verificare** per ciascuna regola mancante o in disaccordo: parole chiave, dove compare di solito, come controllare,
- e i punti che richiedono una persona (requisiti da rivedere, documenti illeggibili, downloads falliti).

Non è visibile agli utenti finali: solo al Quartier Generale.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from app.core import bandi, events, research
from app.core.bandi import RULE_CRITERIA
from app.core.criteria_catalog import CRITERIA_TITLES

# chiave -> (etichetta, cosa significa, parole da cercare, dove compare di solito, come verificare)
RULE_INFO: Dict[str, Dict[str, Any]] = {
    "max_hourly_rate_personnel": {
        "label": "Tetto al costo orario del personale", "meaning": "Il massimo €/ora che il bando riconosce per le persone che lavorano al progetto: sopra questo valore il costo viene ridotto.",
        "search": ["costo orario", "tariffa oraria", "€/ora", "euro/ora", "hourly rate", "unit cost"], "where": "Articolo sulle spese ammissibili di personale o allegato dei costi standard.",
        "verify": "Controlla che il tetto valga per tutte le figure (non solo alcune fasce) e se è al lordo o al netto degli oneri. Se il bando usa tabelle per livello, segnalalo: la regola oggi è un solo numero."},
    "max_consulting_percentage": {
        "label": "Limite alle consulenze esterne (% del totale)", "meaning": "Quota massima del budget che può andare a consulenze esterne.",
        "search": ["consulenz", "prestazioni professionali", "servizi esterni", "external expertise", "consultancy"], "where": "Articolo sulle spese ammissibili o sui massimali per voce.",
        "verify": "Verifica su quale base è calcolata la percentuale (totale progetto, costi diretti, contributo?) e se include o no l'IVA."},
    "max_overhead_percentage": {
        "label": "Limite alle spese generali (% del totale)", "meaning": "Massimo riconosciuto per le spese generali/indirette.",
        "search": ["spese generali", "costi indiretti", "overhead", "indirect costs"], "where": "Sezione costi ammissibili o modalità di rendicontazione.",
        "verify": "Distingui se è un tetto sulle spese reali o un forfait (in quel caso la regola giusta è il tasso forfettario, con la sua base di calcolo)."},
    "overhead_flat_rate_pct": {
        "label": "Tasso forfettario per le spese generali", "meaning": "Le spese generali si riconoscono con una % fissa, senza giustificativi.",
        "search": ["forfett", "tasso forfettario", "flat rate", "flat-rate"], "where": "Sezione costi indiretti.",
        "verify": "Annota la base a cui si applica (costi di personale? costi diretti esclusi subappalti?): senza la base il forfait non si calcola."},
    "overhead_flat_base": {
        "label": "Base di calcolo del forfait", "meaning": "Su cosa si applica la % forfettaria (solo personale o tutti i costi diretti).",
        "search": ["costi diretti", "costi del personale", "direct costs", "staff costs"], "where": "Stesso paragrafo del forfait.", "verify": "Leggi la frase intera: spesso esclude subappalti o attrezzature."},
    "eligible_categories": {
        "label": "Categorie di spesa ammesse", "meaning": "Quali tipi di spesa il bando finanzia (personale, beni, consulenze, spese generali, formazione).",
        "search": ["spese ammissibili", "sono ammissibili", "esclusivamente", "eligible costs", "eligible expenses"], "where": "Articolo «Spese ammissibili» e, subito dopo, «Spese non ammissibili».",
        "verify": "Leggi entrambi gli elenchi: se il bando elenca solo alcune categorie le altre sono escluse. Attenzione alle voci ammesse solo a condizioni."},
    "excluded_asset_natures": {
        "label": "Beni esclusi (es. immobili)", "meaning": "Tipi di bene che non si finanziano (terreni, fabbricati, software, servizi…).",
        "search": ["terreni", "fabbricati", "immobili", "non ammissibil", "land", "buildings"], "where": "Elenco delle spese non ammissibili.", "verify": "Controlla eccezioni (es. opere murarie strettamente funzionali)."},
    "requires_eu_origin": {
        "label": "Beni prodotti in UE/SEE", "meaning": "I beni devono essere di produzione europea.",
        "search": ["prodotti in ue", "unione europea", "spazio economico europeo", "made in eu", "origine"], "where": "Requisiti dei beni (tipico dei crediti d'imposta 4.0/5.0).", "verify": "Verifica se serve una dichiarazione del fornitore o una certificazione."},
    "equipment_depreciation_only": {
        "label": "Attrezzature: solo ammortamento", "meaning": "Le attrezzature si riconoscono solo per la quota di ammortamento del periodo del progetto.",
        "search": ["ammortament", "quota di ammortamento", "depreciation"], "where": "Spese per attrezzature.", "verify": "Controlla le aliquote da usare (tabelle fiscali o del bando)."},
    "requires_new_asset": {
        "label": "Bene nuovo di fabbrica", "meaning": "Sono ammessi solo beni nuovi (non usati né rigenerati).",
        "search": ["nuovi di fabbrica", "beni nuovi", "usati", "rigenerati", "new equipment"], "where": "Requisiti dei beni.", "verify": "Cerca eccezioni per beni usati."},
    "requires_iot": {
        "label": "Interconnessione (Industria 4.0/5.0)", "meaning": "I beni devono essere interconnessi al sistema aziendale.",
        "search": ["interconness", "industria 4.0", "allegato a", "allegato b", "iot"], "where": "Allegati tecnici ai beni.", "verify": "Controlla gli elenchi di beni ammessi (allegati A/B): la regola da sola non basta."},
    "min_energy_saving_pct": {
        "label": "Risparmio energetico minimo", "meaning": "Riduzione dei consumi da dimostrare (spesso con perizia).",
        "search": ["risparmio energetico", "riduzione dei consumi", "energy saving", "almeno"], "where": "Requisiti tecnici dell'investimento.", "verify": "Annota la base di confronto (consumi prima/dopo? struttura produttiva o processo?)."},
    "max_price_deviation_pct": {
        "label": "Scostamento massimo dal prezzo di mercato", "meaning": "Quanto un prezzo può superare il benchmark senza essere ridotto.",
        "search": ["congruità", "prezzo di mercato", "preventivi", "benchmark", "tre preventivi"], "where": "Regole sulla congruità della spesa.", "verify": "Spesso il bando chiede solo N preventivi e non fissa una %: in quel caso la regola non esiste."},
    "max_installation_pct": {
        "label": "Limite ai costi di installazione", "meaning": "Quota massima di installazione/trasporto/collaudo rispetto al bene.",
        "search": ["installazione", "montaggio", "collaudo", "trasporto", "installation"], "where": "Spese per beni strumentali.", "verify": "Verifica la base di calcolo (valore del bene?)."},
    "vat_never_eligible": {
        "label": "IVA mai ammissibile", "meaning": "L'IVA non è un costo finanziabile.",
        "search": ["iva", "al netto dell'iva", "imposta sul valore aggiunto", "vat"], "where": "Spese ammissibili.", "verify": "Controlla se l'IVA indetraibile è ammessa: molti bandi la riconoscono se non recuperabile."},
    "max_immaterial_pct": {
        "label": "Limite ai beni immateriali", "meaning": "Quota massima di software/licenze/brevetti.",
        "search": ["immateriali", "software", "licenze", "brevetti", "intangible"], "where": "Spese per beni strumentali.", "verify": "Verifica la base della percentuale."},
    "requires_dnsh": {
        "label": "Principio DNSH (non arrecare danno all'ambiente)", "meaning": "Le spese non devono danneggiare l'ambiente in modo significativo.",
        "search": ["dnsh", "danno significativo", "do no significant harm"], "where": "Bandi PNRR / fondi UE.", "verify": "Cerca la checklist DNSH (schede tecniche): la sola presenza del requisito non dice quali verifiche fare."},
    "appraisal_threshold_eur": {
        "label": "Soglia oltre la quale serve una perizia", "meaning": "Importo sopra il quale serve una perizia tecnica asseverata.",
        "search": ["perizia", "asseverata", "giurata", "certificazione"], "where": "Requisiti dei beni / documenti a corredo.", "verify": "Annota la soglia esatta in €."},
    "min_durability_months": {
        "label": "Vincolo di destinazione (mesi)", "meaning": "Per quanto tempo il bene o l'attività va mantenuto dopo la chiusura.",
        "search": ["vincolo di destinazione", "mantenimento", "stabilità delle operazioni", "durabilità", "cinque anni", "tre anni"], "where": "Obblighi del beneficiario.", "verify": "Converti gli anni in mesi e controlla da quando parte il conteggio."},
    "require_independent_supplier": {
        "label": "Fornitori indipendenti (no parti correlate)", "meaning": "Non si possono acquistare beni/servizi da soggetti collegati al beneficiario.",
        "search": ["parti correlate", "conflitto di interess", "imprese collegate", "related part"], "where": "Regole sui fornitori.", "verify": "Leggi la definizione di «collegata» usata dal bando."},
    "allowed_ateco_prefixes": {
        "label": "Codici ATECO ammessi", "meaning": "Settori di attività dei fornitori o dei beneficiari ammessi.",
        "search": ["ateco", "codice ateco", "settori ammessi", "settori esclusi"], "where": "Requisiti soggettivi.", "verify": "Controlla sia l'elenco dei codici ammessi sia quello degli esclusi."},
    "subcontracting_allowed": {
        "label": "Subappalto ammesso o no", "meaning": "Se parte del progetto può essere affidata a terzi.",
        "search": ["subappalt", "subcontract", "affidamento a terzi"], "where": "Regole di esecuzione.", "verify": "Cerca i limiti (% massima, autorizzazione preventiva)."},
    "max_communication_pct": {
        "label": "Limite alle spese di comunicazione", "meaning": "Quota massima per comunicazione/promozione.",
        "search": ["comunicazione", "promozione", "pubblicità", "publicity"], "where": "Costi ammissibili.", "verify": "Verifica la base del calcolo."},
    "guarantee_costs_eligible": {
        "label": "Costi di fideiussione/assicurazione ammissibili", "meaning": "Se le garanzie richieste dal bando sono un costo finanziabile.",
        "search": ["fideiussione", "polizza", "garanzia", "assicurazione"], "where": "Spese ammissibili / erogazione anticipata.", "verify": "Cerca se il costo è ammesso solo per fideiussioni obbligatorie."},
    "max_audit_cost_eur": {
        "label": "Massimo per la revisione contabile", "meaning": "Importo massimo riconosciuto per certificare la spesa.",
        "search": ["revisione contabile", "revisore", "certificazione della spesa", "audit"], "where": "Rendicontazione.", "verify": "Annota l'importo in € e se è per progetto o per stato di avanzamento."},
    "eligibility_start": {
        "label": "Inizio del periodo di ammissibilità della spesa", "meaning": "Da quando le spese sono finanziabili: prima di questa data vengono escluse.",
        "search": ["a partire dal", "ammissibili dal", "data di avvio", "data di inizio", "eligible from", "start date"], "where": "Articolo sui termini di avvio del progetto.", "verify": "Controlla se conta la data della fattura, del pagamento o dell'ordine."},
    "eligibility_end": {
        "label": "Fine del periodo di ammissibilità", "meaning": "Entro quando vanno sostenute le spese.",
        "search": ["entro il", "termine di conclusione", "termine ultimo", "end date", "completion"], "where": "Termini del progetto.", "verify": "Verifica le proroghe."},
    "non_cumulable_funding_ids": {
        "label": "Contributi non cumulabili", "meaning": "Altri aiuti che non si possono avere per le stesse spese.",
        "search": ["cumulo", "cumulabil", "doppio finanziamento", "double funding"], "where": "Articolo su cumulo degli aiuti.", "verify": "Elenca i nomi delle misure incompatibili."},
    "max_aid_intensity_pct": {
        "label": "Intensità massima di aiuto", "meaning": "Quota massima di spesa coperta da aiuti pubblici (tetto europeo GBER).",
        "search": ["intensità di aiuto", "intensità massima", "gber", "aid intensity"], "where": "Regime di aiuti di Stato.", "verify": "Cambia per dimensione d'impresa e zona: annota la regola valida per il beneficiario tipo."},
    "contribution_rate_pct": {
        "label": "Percentuale di contributo", "meaning": "Quota della spesa ammessa che il bando rimborsa.",
        "search": ["fondo perduto", "contributo pari", "% delle spese", "percentuale di contribuzione", "funding rate"], "where": "Articolo sull'agevolazione.", "verify": "Molti bandi hanno più aliquote (per importo, area, tipo di beneficiario): scegli quella per il caso da validare."},
    "de_minimis_residual_eur": {
        "label": "Aiuti de minimis", "meaning": "Se il contributo è in de minimis, conta il plafond residuo dell'impresa.",
        "search": ["de minimis"], "where": "Regime di aiuto.", "verify": "Controlla il regolamento richiamato e la soglia nel triennio."},
    "requires_cup": {
        "label": "CUP obbligatorio", "meaning": "Il Codice Unico di Progetto va riportato su documenti di spesa.",
        "search": ["cup", "codice unico di progetto"], "where": "Obblighi di rendicontazione.", "verify": "Verifica dove va riportato (fatture, bonifici, contratti)."},
    "blocked_payment_methods": {
        "label": "Pagamenti non ammessi", "meaning": "Metodi di pagamento non tracciabili (contanti, assegni…).",
        "search": ["contant", "tracciabil", "bonifico", "assegn", "cash"], "where": "Rendicontazione della spesa.", "verify": "Controlla eccezioni per piccoli importi."},
    "requires_milestones": {
        "label": "Rendicontazione per stati di avanzamento (SAL)", "meaning": "Le spese si rendicontano a tappe.",
        "search": ["stato di avanzamento", "sal", "rendicontazione intermedia", "milestone"], "where": "Erogazione del contributo.", "verify": "Leggi quante tappe e con quali percentuali."},
    "max_inter_chapter_variation_pct": {
        "label": "Variazione tollerata tra capitoli di spesa", "meaning": "Quanto si può spostare un importo tra voci senza autorizzazione.",
        "search": ["variazioni", "rimodulazione", "scostamento tra le voci", "budget transfers"], "where": "Variazioni di progetto.", "verify": "Annota la % e la base."},
    "reimbursement_lag_months": {
        "label": "Tempo tra spesa e rimborso (mesi)", "meaning": "Quanto l'ente deve anticipare prima di essere rimborsato: incide sulla liquidità.",
        "search": ["erogazione", "saldo", "entro giorni", "entro mesi", "payment within"], "where": "Modalità di erogazione.", "verify": "Stima i mesi tra l'ultima spesa e il saldo."},
    "advance_pct": {
        "label": "Anticipo", "meaning": "Quota di contributo erogabile in anticipo.",
        "search": ["anticipo", "anticipazione", "pre-financing", "prefinanziamento"], "where": "Modalità di erogazione.", "verify": "Controlla se serve una fideiussione."},
    "overtime_allowed": {
        "label": "Straordinari ammessi", "meaning": "Se le ore di straordinario sono un costo finanziabile.",
        "search": ["straordinar", "overtime"], "where": "Costi del personale.", "verify": "Cerca se sono ammessi solo se previsti dal contratto."},
    "payroll_tolerance_pct": {
        "label": "Tolleranza tra busta paga e costo dichiarato", "meaning": "Scostamento accettato tra il costo dichiarato e quello reale dalla busta paga.",
        "search": ["busta paga", "libro unico", "scostamento", "payslip"], "where": "Rendicontazione del personale.", "verify": "Di solito non è scritta: se manca resta il controllo esatto."},
}


def _snippets(texts: List[str], keywords: List[str], limit: int = 2, width: int = 170) -> Dict[str, Any]:
    rx = re.compile("|".join(re.escape(k) for k in keywords), re.I)
    count, snips = 0, []
    for t in texts:
        for m in rx.finditer(t):
            count += 1
            if len(snips) < limit:
                a = max(0, m.start() - width // 2)
                snips.append("…" + re.sub(r"\s+", " ", t[a:m.end() + width // 2]).strip() + "…")
            if count > 400:
                break
    return {"count": count, "snippets": snips}


def consultant_sheet(bando_id: str) -> Optional[Dict[str, Any]]:
    d = bandi.get_bando_detail(bando_id)
    if d is None:
        return None
    sources = events.list_bando_sources(bando_id)
    texts = [research.focus_text(s["text"], d["name"]) for s in sources]

    rules = {r["key"]: r for r in d["rules"]}
    says, conflicts, silent = [], [], []
    for key, r in rules.items():
        info = RULE_INFO.get(key, {})
        base = {"key": key, "label": info.get("label", key), "criteria": RULE_CRITERIA.get(key, [])}
        if r["status"] == "PUBLISHED":
            says.append({**base, "value": r["value"], "source": r["source_ref"], "confidence": r["confidence"], "origin": r["origin"],
                         "check": "Confronta il valore con la frase originale nel documento indicato." if r["origin"] == "STRUCTURED_PARSING" else "Valore deciso da una persona."})
        else:
            conflicts.append({**base, "values": r["passes"], "source": r["source_ref"],
                              "what_to_do": "Documenti (o frasi) diversi danno numeri diversi. Apri le fonti, capisci quale valore vale per il beneficiario tipo e impostalo dalla scheda del bando."})
    for key, info in RULE_INFO.items():
        if key in rules:
            continue
        found = _snippets(texts, info["search"])
        crit = RULE_CRITERIA.get(key, [])
        silent.append({
            "key": key, "label": info["label"], "meaning": info["meaning"], "criteria": [{"n": n, "title": CRITERIA_TITLES.get(n, "")} for n in crit],
            "search": info["search"], "where": info["where"], "verify": info["verify"], "mentions": found["count"], "snippets": found["snippets"],
            "state": ("Le parole compaiono nei documenti ma non ho ricavato un valore univoco: leggi i passaggi e decidi." if found["count"]
                      else "Non compare nei documenti letti: probabilmente il bando non lo prevede. Conferma sul testo ufficiale, poi lascia spento il controllo."),
        })
    silent.sort(key=lambda x: (x["mentions"] == 0, -len(x["criteria"])))   # prima quelle di cui i documenti parlano

    review = [r for r in d["requirements"] if r["kind"] == "DA_REVISIONARE"][:60]
    docs = []
    problems = 0
    for s in sources:
        ana = json.loads(s["analysis"]) if s.get("analysis") else {}
        warns = json.loads(s["warnings"]) if s.get("warnings") else []
        issue = warns[:] + ([ana["note"]] if ana.get("note") else [])
        problems += 1 if issue else 0
        docs.append({"sha256": s["sha256"], "name": s["name"], "url": s.get("url"), "tier": s.get("tier"), "origin": s.get("origin"), "chars": len(s["text"]),
                     "pages": s.get("pages"), "has_file": bool(s.get("file_sha256")), "requirements": ana.get("requirements"), "lang": ana.get("lang"),
                     "used_chars": ana.get("used_chars"), "issues": issue})
    steps = [
        "Apri «Documenti in memoria» e controlla che siano davvero quelli del bando giusto (nome, ente, anno) e che ci sia tutto: avviso/bando, decreto attuativo, allegati, FAQ, circolari.",
        f"Decidi le {len(conflicts)} regole in disaccordo (sezione «Da decidere»)." if conflicts else "Nessuna regola in disaccordo.",
        f"Per le {len(silent)} regole non trovate: cerca le parole indicate nei documenti; se il bando ne parla imposta il valore, altrimenti conferma che il controllo resti spento.",
        f"Leggi i {len(review)} requisiti «da rivedere»: sono obblighi o divieti che non ho saputo collegare a un controllo." if review else "Nessun requisito da rivedere.",
        f"Risolvi i {problems} documenti con problemi (PDF scansionato, troncato, non leggibile): aggiungili a mano o scaricali altrove." if problems else "Tutti i documenti sono stati letti senza problemi evidenti.",
        "Controlla lo stato del bando (aperto/chiuso, scadenze, proroghe) sulla pagina ufficiale.",
        "Al termine premi «Rileggi tutto» e prova il bando nel Budget con una prova completa.",
    ]
    return {
        "bando_id": bando_id, "name": d["name"], "coverage": d["coverage_summary"], "extraction_status": d["extraction_status"],
        "curated_gaps": d.get("not_specified", []), "says": says, "conflicts": conflicts, "silent": silent, "review": review, "documents": docs, "checklist": steps,
        "summary": {"rules_published": len(says), "conflicts": len(conflicts), "silent": len(silent), "review": len(review), "documents": len(docs), "document_issues": problems},
    }
