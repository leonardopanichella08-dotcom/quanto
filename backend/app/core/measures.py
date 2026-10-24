"""Le agevolazioni che non sono bandi: sgravi e esoneri sul costo del lavoro, tirocini, apprendistato, incentivi regionali all'occupazione, misure per le nuove imprese.

Un commercialista che segue società di persone, ditte individuali e piccole srl non ha bisogno solo di bandi: per far crescere l'impresa assumere costa, e parte del costo si
recupera con strumenti che non passano da un bando (un esonero INPS) o passano da un bando della Regione (un tirocinio rimborsato). Qui stanno tutti, in un solo posto, con le stesse regole di sempre:

- **ogni numero ha la sua fonte e il suo grado di verifica**: ``verified`` dice se la regola è stata letta su una fonte secondaria ("SECONDARIA": circolari INPS riportate dalla stampa
  specializzata, da confermare sul sito INPS prima di presentare la domanda) o se è solo una famiglia di misure di cui i parametri cambiano per Regione ("DA_VERIFICARE");
- **nessun importo è inventato**: per le misure regionali non c'è un importo, c'è il modo di trovarle nel catalogo e le condizioni generali; i parametri stanno nel bando della Regione;
- **le regole sull'impresa si controllano da sole sui dati del profilo** (regione, dipendenti, DURC, tipo di impresa); quelle sul lavoratore si mostrano come «chi assumere»: è la scelta
  del datore, non un dato che l'impresa ha già;
- **le misure non cumulabili tra loro lo dicono**: l'app propone la migliore per il caso, non la somma.

Aggiornare le misure è un lavoro editoriale (le circolari cambiano ogni anno): ``VERIFIED_ON`` dice a che data è stato fatto l'ultimo controllo.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

VERIFIED_ON = "2026-10-24"
ZES_UNICA = {"Abruzzo", "Molise", "Campania", "Basilicata", "Sicilia", "Puglia", "Calabria", "Sardegna", "Marche", "Umbria"}

FAMILIES = [
    {"id": "ESONERI_INPS", "label": "Esoneri e sgravi INPS", "text": "Riducono i contributi che il datore versa all'INPS. Non servono bandi: si chiedono all'INPS e si usano in busta paga.", "no_project": True},
    {"id": "OCCUPAZIONE_REGIONALE", "label": "Incentivi regionali all'occupazione", "text": "Contributi della Regione (Fondo Sociale Europeo Plus) a chi assume. Importi e requisiti cambiano da una Regione all'altra.", "no_project": True},
    {"id": "TIROCINI", "label": "Tirocini", "text": "Il tirocinio non è un lavoro: è un percorso formativo. La Regione può coprire in tutto o in parte l'indennità mensile.", "no_project": True},
    {"id": "APPRENDISTATO", "label": "Apprendistato", "text": "Contratto a tempo indeterminato per formare un giovane: contributi ridotti e formazione esterna finanziata dalla Regione.", "no_project": True},
    {"id": "FISCALI", "label": "Vantaggi fiscali sulle assunzioni", "text": "Maggiorazioni del costo deducibile e crediti d'imposta legati alle nuove assunzioni.", "no_project": True},
    {"id": "NUOVE_IMPRESE", "label": "Nuove imprese e autoimpiego", "text": "Misure per chi sta per costituire un'impresa o l'ha costituita da poco: giovani, donne, disoccupati.", "no_project": False},
]

# Condizioni sull'impresa uguali per tutti gli esoneri 2026 (circolari INPS 55, 56 e 57 del 14 maggio 2026, riportate da stampa specializzata)
COMMON_COMPANY = [
    "Datore di lavoro privato (esclusa la pubblica amministrazione).",
    "DURC regolare e rispetto del contratto collettivo e delle norme su lavoro e sicurezza.",
    "Incremento occupazionale netto (in unità di lavoro annue) rispetto alla media dei dodici mesi prima.",
    "Nessun licenziamento per giustificato motivo oggettivo o collettivo nei 6 mesi prima e dopo l'assunzione (altrimenti l'esonero si recupera).",
    "Retribuzione non inferiore a quella dei contratti collettivi più rappresentativi.",
]
COMMON_AID = "È un aiuto di Stato (Reg. UE 651/2014): non supera il 50% del costo salariale, si registra nel Registro nazionale aiuti, sono escluse le imprese in difficoltà."
EXCLUSIVE = "Non cumulabile con gli altri esoneri sul costo del lavoro, con la Decontribuzione Sud, con l'incentivo per i disabili né con l'incentivo NASpI; compatibile con la maggiorazione del costo deducibile per nuove assunzioni (l. 207/2024, commi 399-400)."

MEASURES: List[Dict[str, Any]] = [
    {"id": "BONUS_GIOVANI_2026", "family": "ESONERI_INPS", "name": "Bonus Giovani 2026", "group": "ESONERI_2026",
     "tagline": "Esonero del 100% dei contributi del datore per assumere un under 35 a tempo indeterminato.",
     "worker": ["Meno di 35 anni alla data dell'assunzione (fino a 34 anni e 364 giorni).", "Senza impiego regolarmente retribuito da almeno 6, 12 o 24 mesi secondo la categoria di svantaggio (24 mesi: «molto svantaggiato»)."],
     "contract": "Tempo indeterminato, anche in somministrazione. Esclusi tempo determinato, apprendistato, intermittente, occasionale, domestico.",
     "period": "Assunzioni dal 1° gennaio al 31 dicembre 2026.", "valid_to": "2026-12-31",
     "cap_month_eur": 500, "cap_month_zes_eur": 650, "months": {"MOLTO_SVANTAGGIATO": 24, "SVANTAGGIATO": 12}, "worker_rule": {"age_max": 34},
     "company": COMMON_COMPANY, "aid": COMMON_AID, "cumulation": EXCLUSIVE,
     "how": "Domanda online sul Portale delle Agevolazioni INPS (ex DiResCo) prima dell'assunzione; poi la comunicazione obbligatoria entro 10 giorni dall'avviso dell'INPS.",
     "source": {"label": "Circolare INPS n. 55 del 14 maggio 2026 (d.l. 62/2026, art. 2)", "url": None}, "verified": "SECONDARIA"},
    {"id": "BONUS_DONNE_2026", "family": "ESONERI_INPS", "name": "Bonus Donne 2026", "group": "ESONERI_2026",
     "tagline": "Esonero del 100% dei contributi del datore per assumere una donna svantaggiata a tempo indeterminato, a ogni età.",
     "worker": ["Donna, senza limiti di età.", "Senza impiego regolarmente retribuito da almeno 6, 12 o 24 mesi secondo la categoria di svantaggio."],
     "contract": "Tempo indeterminato.", "period": "Assunzioni dal 1° gennaio al 31 dicembre 2026.", "valid_to": "2026-12-31",
     "cap_month_eur": 650, "cap_month_zes_eur": 800, "months": {"MOLTO_SVANTAGGIATO": 24, "SVANTAGGIATO": 12}, "worker_rule": {"gender": "F"},
     "company": COMMON_COMPANY, "aid": COMMON_AID, "cumulation": EXCLUSIVE,
     "how": "Domanda online sul Portale delle Agevolazioni INPS prima dell'assunzione (messaggi INPS sulle domande dall'11 giugno 2026).",
     "source": {"label": "Circolare INPS n. 57 del 14 maggio 2026", "url": None}, "verified": "SECONDARIA"},
    {"id": "BONUS_ZES_2026", "family": "ESONERI_INPS", "name": "Bonus ZES 2026 (Mezzogiorno)", "group": "ESONERI_2026",
     "tagline": "Esonero del 100% dei contributi per assumere un disoccupato di lunga durata (35 anni o più) in una sede della ZES unica.",
     "worker": ["35 anni o più, non dirigente.", "Disoccupato da almeno 24 mesi."],
     "contract": "Tempo indeterminato.", "period": "Assunzioni nel 2026.", "valid_to": "2026-12-31", "needs_zes": True, "max_employees": 10,
     "cap_month_eur": 650, "cap_month_zes_eur": 650, "months": {"ANY": 24}, "worker_rule": {"age_min": 35},
     "company": COMMON_COMPANY + ["Sede o unità produttiva nella ZES unica (Abruzzo, Molise, Campania, Basilicata, Sicilia, Puglia, Calabria, Sardegna, Marche, Umbria).", "Fino a 10 dipendenti nel mese dell'assunzione, al netto dei lavoratori agevolati."],
     "aid": COMMON_AID, "cumulation": EXCLUSIVE, "how": "Domanda online sul Portale delle Agevolazioni INPS.",
     "source": {"label": "Circolare INPS n. 56 del 14 maggio 2026", "url": None}, "verified": "SECONDARIA"},
    {"id": "BONUS_STABILIZZAZIONE_2026", "family": "ESONERI_INPS", "name": "Bonus Stabilizzazione 2026", "group": "ESONERI_2026",
     "tagline": "Esonero per trasformare in tempo indeterminato il contratto a termine di un giovane under 35.",
     "worker": ["Meno di 35 anni, mai assunto a tempo indeterminato.", "Contratto a termine di durata non superiore a 12 mesi, stipulato entro il 30 aprile 2026."],
     "contract": "Trasformazione in tempo indeterminato tra il 1° agosto e il 31 dicembre 2026.", "period": "Trasformazioni dal 1° agosto al 31 dicembre 2026.", "valid_to": "2026-12-31", "only_existing_contract": True,
     "cap_month_eur": 500, "cap_month_zes_eur": 500, "months": {"ANY": 24}, "worker_rule": {"age_max": 34},
     "company": COMMON_COMPANY, "aid": COMMON_AID, "cumulation": EXCLUSIVE, "how": "Domanda online sul Portale delle Agevolazioni INPS (procedura attivata a fine luglio 2026).",
     "source": {"label": "Circolare INPS n. 72 del 3 luglio 2026", "url": None}, "verified": "SECONDARIA"},
    {"id": "BONUS_MADRI_2026", "family": "ESONERI_INPS", "name": "Assunzione di madri con almeno tre figli", "group": "ESONERI_2026",
     "tagline": "Esonero dei contributi per assumere lavoratrici madri con tre o più figli.",
     "worker": ["Donna con almeno tre figli, nelle condizioni previste dalla circolare."], "contract": "Da verificare sulla circolare.", "period": "Da verificare sulla circolare.", "valid_to": None,
     "cap_year_eur": 8000, "worker_rule": {"gender": "F"}, "company": COMMON_COMPANY, "aid": COMMON_AID, "cumulation": EXCLUSIVE,
     "how": "Istruzioni nella circolare INPS n. 82 del 29 luglio 2026: leggerla prima di assumere.",
     "source": {"label": "Circolare INPS n. 82 del 29 luglio 2026", "url": None}, "verified": "DA_VERIFICARE", "note": "Importo massimo annuo riportato da una sola fonte secondaria: confermarlo sulla circolare."},
    # misure regionali e di famiglia: nessun importo qui, perché cambia per Regione e per bando
    {"id": "INCENTIVI_OCCUPAZIONE_FSE", "family": "OCCUPAZIONE_REGIONALE", "name": "Bonus occupazione e incentivi all'assunzione (Regione, FSE+)", "group": None,
     "tagline": "Contributi a fondo perduto alla Regione che assume: l'importo dipende dal tipo di contratto e dal lavoratore.",
     "worker": ["Donne, disoccupati di lungo periodo, giovani under 30-35, persone con disabilità: spesso con importi maggiorati."], "contract": "Dipende dal bando: di solito tempo indeterminato o apprendistato.",
     "period": "A bando, periodico.", "valid_to": None, "company": ["I requisiti si leggono nel bando della Regione dove ha sede l'impresa."], "aid": "Dipende dal bando (de minimis o regime di esenzione).", "cumulation": "Dipende dal bando.",
     "how": "Cerca nel catalogo «assunzioni» o «occupazione» e la tua Regione; leggi il bando e studialo a fondo: poi si usa come qualunque altro bando.", "search": ["assunzion", "occupazione", "incentivi all'occupazione"], "regional": True,
     "source": {"label": "Descrizione dello studio, da confrontare con il bando della Regione", "url": None}, "verified": "DA_VERIFICARE"},
    {"id": "VOUCHER_OCCUPAZIONALI", "family": "OCCUPAZIONE_REGIONALE", "name": "Voucher occupazionali", "group": None,
     "tagline": "Buoni che l'azienda riscatta per abbattere il costo di assunzione o coprire la formazione del nuovo dipendente.",
     "worker": ["Secondo il bando."], "contract": "Secondo il bando.", "period": "A bando.", "valid_to": None, "company": ["Secondo il bando."], "aid": "Dipende dal bando.", "cumulation": "Dipende dal bando.",
     "how": "Cerca nel catalogo «voucher» e la tua Regione.", "search": ["voucher"], "regional": True, "source": {"label": "Descrizione dello studio, da confrontare con il bando della Regione", "url": None}, "verified": "DA_VERIFICARE"},
    {"id": "TIROCINIO_GARANZIA_GIOVANI", "family": "TIROCINI", "name": "Tirocinio extracurricolare con indennità rimborsata (Garanzia Giovani / FSE+)", "group": None,
     "tagline": "La Regione copre in tutto o in gran parte l'indennità mensile del tirocinante NEET.",
     "worker": ["Giovane NEET (non studia e non lavora), di norma fino a 29 anni; alcune Regioni arrivano a 35."], "contract": "Tirocinio formativo (non è un contratto di lavoro): serve una convenzione con un ente promotore.",
     "period": "A bando regionale.", "valid_to": None, "company": ["Convenzione con l'ente promotore e rispetto dei limiti di tirocinanti per azienda stabiliti dalla Regione."], "aid": "Dipende dal programma.", "cumulation": "Dipende dal programma.",
     "how": "Cerca nel catalogo «tirocini» o «garanzia giovani» e la tua Regione.", "search": ["tirocini", "garanzia giovani", "tirocinio"], "regional": True,
     "source": {"label": "Descrizione dello studio, da confrontare con il programma della Regione", "url": None}, "verified": "DA_VERIFICARE"},
    {"id": "BONUS_TRASFORMAZIONE_TIROCINIO", "family": "TIROCINI", "name": "Bonus per trasformare il tirocinio in assunzione", "group": None,
     "tagline": "Contributo all'azienda se al termine del tirocinio assume il tirocinante (soprattutto a tempo indeterminato o in apprendistato).",
     "worker": ["Il tirocinante dell'azienda."], "contract": "Tempo indeterminato o apprendistato.", "period": "A bando regionale.", "valid_to": None, "company": ["Secondo il bando della Regione."], "aid": "Dipende dal bando.", "cumulation": "Dipende dal bando.",
     "how": "Cerca nel catalogo «trasformazione tirocinio» e la tua Regione.", "search": ["trasformazione", "tirocinio"], "regional": True,
     "source": {"label": "Descrizione dello studio, da confrontare con il bando della Regione", "url": None}, "verified": "DA_VERIFICARE"},
    {"id": "APPRENDISTATO", "family": "APPRENDISTATO", "name": "Apprendistato: sgravio contributivo e formazione esterna gratuita", "group": None,
     "tagline": "Contratto a tempo indeterminato per formare un giovane: contributi INPS ridotti per tutto il periodo formativo e formazione finanziata dalla Regione.",
     "worker": ["Giovane nell'età prevista dal contratto di apprendistato."], "contract": "Apprendistato (professionalizzante, di primo o terzo livello).", "period": "Misura strutturale; i cataloghi formativi sono regionali.", "valid_to": None,
     "company": ["Piano formativo e tutor aziendale; la formazione esterna è erogata dagli enti accreditati dalla Regione."], "aid": "Regime generale degli sgravi per apprendistato.", "cumulation": "Il Bonus Giovani 2026 non si applica all'apprendistato.",
     "how": "Parlane con il consulente del lavoro; cerca nel catalogo «apprendistato» e la tua Regione per i cataloghi formativi.", "search": ["apprendistato"], "regional": True,
     "source": {"label": "Descrizione dello studio; aliquote e durata da verificare sulla normativa INPS in vigore", "url": None}, "verified": "DA_VERIFICARE"},
    {"id": "DECONTRIBUZIONE_SUD", "family": "ESONERI_INPS", "name": "Decontribuzione Sud", "group": "ESONERI_2026",
     "tagline": "Riduzione percentuale dei contributi previdenziali per tutti i dipendenti delle sedi del Mezzogiorno (l. 207/2024, commi 406-422).",
     "worker": ["Tutti i dipendenti di sedi nelle regioni ammesse."], "contract": "Qualsiasi.", "period": "Da verificare sulla circolare in vigore.", "valid_to": None,
     "company": ["Sede in una regione ammessa del Mezzogiorno."], "aid": COMMON_AID, "cumulation": "Non cumulabile con i nuovi esoneri 2026 per la stessa assunzione.",
     "how": "Si applica in denuncia contributiva: chiedere al consulente del lavoro.", "source": {"label": "Legge 207/2024, commi 406-422 (citata nelle circolari INPS 2026)", "url": None}, "verified": "DA_VERIFICARE",
     "note": "Percentuale e durata non verificate: si legge la circolare in vigore."},
    {"id": "MAGGIORAZIONE_DEDUCIBILE", "family": "FISCALI", "name": "Maggiorazione del costo deducibile per nuove assunzioni", "group": None,
     "tagline": "Il costo delle nuove assunzioni si deduce con una maggiorazione (l. 207/2024, commi 399-400): è compatibile con i nuovi esoneri.",
     "worker": ["Secondo la norma."], "contract": "Tempo indeterminato.", "period": "Da verificare.", "valid_to": None, "company": ["Incremento occupazionale e condizioni della norma."], "aid": "Misura fiscale.", "cumulation": "Compatibile con Bonus Giovani, Donne, ZES.",
     "how": "Si usa in dichiarazione dei redditi: chiedere al consulente fiscale.", "source": {"label": "Legge 207/2024, commi 399-400 (citata nella circolare INPS n. 55/2026)", "url": None}, "verified": "DA_VERIFICARE", "note": "La misura è citata come compatibile; la maggiorazione e i limiti vanno letti nella norma."},
    {"id": "NUOVE_IMPRESE_BANDI", "family": "NUOVE_IMPRESE", "name": "Bandi per nuove imprese e autoimpiego", "group": None,
     "tagline": "Misure per chi vuole avviare un'attività: giovani, donne, disoccupati (esempi: Resto al Sud 2.0, Autoimpiego Centro-Nord, Smart&Start, ON Tasso Zero, microcredito).",
     "worker": ["Secondo il bando: spesso età, genere o stato di disoccupazione dei soci."], "contract": "Impresa da costituire o costituita da poco.", "period": "A bando.", "valid_to": None, "company": ["Impresa da costituire o neocostituita."], "aid": "Dipende dal bando.", "cumulation": "Dipende dal bando.",
     "how": "Il catalogo mostra i bandi per le imprese da costituire: scegli «Nuova impresa o da costituire» nel profilo.", "search": ["nuove imprese", "autoimpiego", "resto al sud", "smart"], "regional": False, "new_company": True,
     "source": {"label": "Catalogo nazionale dei bandi (schede ufficiali)", "url": None}, "verified": "DA_VERIFICARE"},
]
BY_ID = {m["id"]: m for m in MEASURES}


def _today(today: Optional[date]) -> date:
    return today or date.today()


def company_view(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Cosa dice il profilo che serve a queste misure, e cosa non dice (si chiede, mai si indovina)."""
    region = profile.get("region")
    return {"company_type": profile.get("company_type"), "company_status": profile.get("company_status") or "COSTITUITA", "region": region,
            "zes": (region in ZES_UNICA) if region else None, "employees": profile.get("employees"), "durc_regular": profile.get("durc_regular"),
            "founders_under35": profile.get("founders_under35"), "women_majority": profile.get("women_majority"), "founders_unemployed": profile.get("founders_unemployed")}


def evaluate(measure: Dict[str, Any], profile: Dict[str, Any], today: Optional[date] = None) -> Dict[str, Any]:
    """Questa misura vale per questa impresa? Si controllano solo le condizioni sull'impresa; quelle sul lavoratore sono «chi assumere»."""
    today = _today(today)
    c = company_view(profile)
    why_not: List[str] = []
    to_check: List[Dict[str, str]] = []
    ok: List[str] = []
    status = "APPLICABILE"
    if measure["family"] in ("ESONERI_INPS", "FISCALI", "OCCUPAZIONE_REGIONALE", "TIROCINI", "APPRENDISTATO") and c["company_status"] == "DA_COSTITUIRE" and not measure.get("new_company"):
        return {"status": "DOPO_LA_COSTITUZIONE", "why": ["Vale per chi assume: si usa dopo aver costituito l'impresa e prima della prima assunzione."], "to_check": [], "ok": []}
    if measure.get("new_company") and c["company_status"] != "DA_COSTITUIRE":
        status = "DA_VERIFICARE"
        to_check.append({"key": "company_status", "label": "Per le imprese già costituite valgono i bandi per le nuove imprese solo entro pochi anni dalla costituzione: guarda anno di costituzione e scheda del bando."})
    if measure.get("valid_to") and today.isoformat() > measure["valid_to"]:
        return {"status": "SCADUTA", "why": [f"Valeva fino al {measure['valid_to'][8:10]}/{measure['valid_to'][5:7]}/{measure['valid_to'][:4]}."], "to_check": [], "ok": []}
    if measure["family"] == "ESONERI_INPS" and measure["id"] != "DECONTRIBUZIONE_SUD" and measure["verified"] == "SECONDARIA":
        if c["durc_regular"] is False:
            why_not.append("L'impresa non risulta regolare con DURC e contributi: l'esonero non spetta finché non si regolarizza.")
        elif c["durc_regular"] is None:
            to_check.append({"key": "durc_regular", "label": "L'impresa è regolare con DURC, contributi e imposte?"})
        else:
            ok.append("DURC regolare.")
    if measure.get("needs_zes"):
        if c["zes"] is None:
            to_check.append({"key": "region", "label": "In che regione ha sede l'impresa?"})
        elif not c["zes"]:
            why_not.append(f"La sede è in {c['region']}, che non è nella ZES unica (vale per Abruzzo, Molise, Campania, Basilicata, Sicilia, Puglia, Calabria, Sardegna, Marche, Umbria).")
        else:
            ok.append(f"Sede in {c['region']}: ZES unica.")
    if measure.get("max_employees") is not None:
        if c["employees"] is None:
            to_check.append({"key": "employees", "label": "Quanti dipendenti ha l'impresa?"})
        elif c["employees"] > measure["max_employees"]:
            why_not.append(f"L'impresa ha {c['employees']} dipendenti: il limite è {measure['max_employees']}.")
        else:
            ok.append(f"{c['employees']} dipendenti: entro il limite di {measure['max_employees']}.")
    if measure.get("only_existing_contract"):
        to_check.append({"key": "", "label": "Serve un lavoratore under 35 con contratto a termine (non oltre 12 mesi, stipulato entro il 30 aprile 2026) da trasformare."})
    if why_not:
        status = "NON_APPLICABILE"
    elif to_check and status == "APPLICABILE":
        status = "DA_VERIFICARE"
    if measure["verified"] == "DA_VERIFICARE" and status == "APPLICABILE":
        status = "DA_VERIFICARE"
        to_check.append({"key": "", "label": "I parametri vanno letti nel bando o nella circolare in vigore."})
    return {"status": status, "why": why_not, "to_check": to_check, "ok": ok}


def value_per_hire(measure: Dict[str, Any], profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Quanto può valere per una assunzione, al massimo: tetto mensile × mesi. Non è un incasso: l'esonero non supera i contributi davvero dovuti."""
    if measure.get("cap_month_eur") is None:
        if measure.get("cap_year_eur"):
            return {"max_eur": measure["cap_year_eur"], "text": f"fino a {measure['cap_year_eur']:,.0f} € l'anno".replace(",", ".")}
        return None
    zes = company_view(profile)["zes"]
    cap = measure["cap_month_zes_eur"] if zes and measure.get("cap_month_zes_eur") else measure["cap_month_eur"]
    months = sorted(set(measure["months"].values()))
    lo, hi = cap * months[0], cap * months[-1]
    text = (f"fino a {cap} € al mese per {months[0]} mesi: {lo:,.0f} €".replace(",", ".") if lo == hi else
            f"fino a {cap} € al mese per {months[0]}-{months[-1]} mesi: {lo:,.0f}-{hi:,.0f} €".replace(",", "."))
    return {"cap_month_eur": cap, "months": months, "min_eur": lo, "max_eur": hi, "text": text, "zes": bool(zes)}


def for_company(profile: Dict[str, Any], today: Optional[date] = None) -> Dict[str, Any]:
    """Tutte le misure, per famiglia, con lo stato per questa impresa."""
    today = _today(today)
    fams = []
    for fam in FAMILIES:
        items = []
        for m in MEASURES:
            if m["family"] != fam["id"]:
                continue
            ev = evaluate(m, profile, today)
            items.append({"id": m["id"], "name": m["name"], "tagline": m["tagline"], "status": ev["status"], "ok": ev["ok"], "why_not": ev["why"], "to_check": ev["to_check"], "worker": m["worker"], "contract": m["contract"],
                          "period": m["period"], "company": m["company"], "aid": m["aid"], "cumulation": m["cumulation"], "how": m["how"], "source": m["source"], "verified": m["verified"], "note": m.get("note"),
                          "value": value_per_hire(m, profile), "group": m["group"], "search": m.get("search"), "regional": bool(m.get("regional"))})
        fams.append({**fam, "items": items})
    counts: Dict[str, int] = {}
    for f in fams:
        for it in f["items"]:
            counts[it["status"]] = counts.get(it["status"], 0) + 1
    return {"verified_on": VERIFIED_ON, "company": company_view(profile), "families": fams, "counts": counts,
            "warning": "Le circolari INPS cambiano ogni anno: i dati qui sono riportati da fonti secondarie e vanno confermati sul sito INPS prima di presentare la domanda."}


def best_for_hires(profile: Dict[str, Any], hires: int, today: Optional[date] = None) -> List[Dict[str, Any]]:
    """Per ``hires`` assunzioni: le misure senza progetto che valgono per questa impresa, dalla più ricca, con chi assumere per usarle. Gli esoneri 2026 non si sommano: si sceglie il migliore per ogni persona."""
    today = _today(today)
    out = []
    for m in MEASURES:
        if m["verified"] != "SECONDARIA" or m.get("only_existing_contract"):         # la stabilizzazione trasforma un contratto che c'è già: non vale per una persona nuova
            continue
        ev = evaluate(m, profile, today)
        if ev["status"] in ("NON_APPLICABILE", "SCADUTA", "DOPO_LA_COSTITUZIONE"):
            continue
        v = value_per_hire(m, profile)
        if not v:
            continue
        out.append({"id": m["id"], "name": m["name"], "status": ev["status"], "who": m["worker"], "contract": m["contract"], "value": v, "total_max_eur": v["max_eur"] * hires,
                    "to_check": ev["to_check"], "source": m["source"], "cumulation": m["cumulation"]})
    return sorted(out, key=lambda x: -x["value"]["max_eur"])
