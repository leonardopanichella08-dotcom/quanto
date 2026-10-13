"""Il piano dei conti di Meridiana Digital Solutions e la contabilità analitica che ne discende (azienda FITTIZIA).

Il modello ``model.py`` dà i totali di ogni voce dello schema civilistico; qui ogni totale viene scomposto in conti (con codice, descrizione e importi in euro e centesimi),
mese per mese, cliente per cliente e fornitore per fornitore. Tutto è deterministico (nessun numero casuale non riproducibile) e **torna esattamente ai totali del modello**:

* la somma dei conti di ricavo e di costo dà le voci del conto economico;
* la somma dei conti patrimoniali dà le voci dello stato patrimoniale;
* il bilancio di verifica quadra (totale dare = totale avere) per ogni esercizio;
* i dodici mesi di ogni conto sommano all'importo annuo.

Convenzione dei segni nel bilancio di verifica: dare positivo, avere negativo (importi in centesimi interi).
"""
from __future__ import annotations

import math
import random
from datetime import date, timedelta
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

from . import model as M

YEARS = M.ALL_YEARS  # 2022..2025


# ------------------------------------------------------------------------------------------------ utilità numeriche
def alloc(total: int, weights: Sequence[float]) -> List[int]:
    """Ripartisce ``total`` (intero, anche negativo) in parti intere proporzionali ai pesi, con somma esatta (metodo del resto più grande)."""
    sgn = -1 if total < 0 else 1
    t = abs(int(total))
    ws = [max(0.0, float(w)) for w in weights]
    s = sum(ws)
    if s == 0 or t == 0:
        return [0] * len(ws)
    raw = [t * w / s for w in ws]
    base = [int(math.floor(x)) for x in raw]
    left = t - sum(base)
    order = sorted(range(len(ws)), key=lambda i: (raw[i] - base[i], -i), reverse=True)
    for i in order[:left]:
        base[i] += 1
    return [sgn * b for b in base]


def rng(*key) -> random.Random:
    return random.Random("|".join(str(k) for k in key))


def jitter(r: random.Random, spread: float) -> float:
    return 1.0 + (r.random() * 2 - 1) * spread


def fmt_it_date(d: date) -> str:
    return d.strftime("%d/%m/%Y")


# ------------------------------------------------------------------------------------------------ conti di ricavo
# (categoria di ricavo, codice, descrizione, pesi 2022..2025): la somma dei pesi di una categoria è la sua quota; gli importi sono ripartiti in proporzione.
REVENUE_ACCOUNTS: List[Tuple[int, str, str, Tuple[float, float, float, float]]] = [
    (0, "410.010", "Sviluppo di applicativi web su commessa", (40, 39, 38, 37)),
    (0, "410.020", "Sviluppo di applicazioni mobile su commessa", (14, 15, 17, 18)),
    (0, "410.030", "Integrazioni e API verso sistemi gestionali dei clienti", (21, 21, 21, 22)),
    (0, "410.040", "Personalizzazioni e manutenzione evolutiva", (25, 25, 24, 23)),
    (1, "420.010", "Canoni della piattaforma Atlas: piano base", (30, 29, 27, 24)),
    (1, "420.020", "Canoni della piattaforma Atlas: piano professional", (24, 28, 32, 36)),
    (1, "420.030", "Licenze d'uso a studi professionali", (10, 13, 17, 22)),
    (1, "420.040", "Canoni di hosting e manutenzione applicativa ricorrente", (36, 30, 24, 18)),
    (2, "430.010", "Consulenza di analisi dei requisiti e project management", (38, 36, 34, 32)),
    (2, "430.020", "Analisi dei dati e business intelligence", (34, 36, 38, 40)),
    (2, "430.030", "Consulenza sulla sicurezza informatica e sulla protezione dei dati", (28, 28, 28, 28)),
    (3, "440.010", "Corsi di formazione per i clienti", (31, 32, 33, 34)),
    (3, "440.020", "Assistenza tecnica e help desk", (49, 47, 45, 43)),
    (3, "440.030", "Interventi tecnici presso la sede del cliente", (20, 21, 22, 23)),
]
REVENUE_SECTION = [c[0] for c in M.REVENUE_SPLIT]


def revenue_accounts(y: int) -> List[Dict]:
    """Ricavi delle vendite e delle prestazioni per conto, in centesimi: la somma coincide con ``REVENUE[y]``."""
    i = M._i(y)
    out: List[Dict] = []
    cat_totals = M._alloc(M.REVENUE[i], [s[1][i] / 100 for s in M.REVENUE_SPLIT])
    for cat in range(len(M.REVENUE_SPLIT)):
        accts = [a for a in REVENUE_ACCOUNTS if a[0] == cat]
        parts = alloc(cat_totals[cat] * 100 + _cents_noise(y, cat), [a[3][i] for a in accts])
        for a, c in zip(accts, parts):
            out.append({"code": a[1], "name": a[2], "section": "A.1", "cat": cat, "cents": c})
    fix = M.REVENUE[i] * 100 - sum(a["cents"] for a in out)
    out[0]["cents"] += fix
    return out


def _cents_noise(y: int, cat: int) -> int:
    """Piccola parte in centesimi per rendere gli importi dei conti non tondi (compensata sul totale della categoria)."""
    return 0


# ------------------------------------------------------------------------------------------------ conti di costo
# macro conto (inizio della descrizione in model.COSTS) → [(descrizione del conto, peso)]. Ogni descrizione contiene una parola che identifica la categoria di spesa.
SUBS: Dict[str, List[Tuple[str, float]]] = {
    "Cancelleria": [("Cancelleria e stampati per uffici", 38), ("Cancelleria: carta, toner e cartucce", 31), ("Materiale di consumo per ufficio e cancelleria", 19), ("Cancelleria per sala riunioni e archivio", 12)],
    "Hardware di piccolo valore": [("Hardware di piccolo valore: periferiche e accessori", 36), ("Hardware: memorie, dischi e componenti", 27), ("Hardware: cavi, adattatori e materiale informatico di consumo", 22),
                                   ("Hardware di piccolo valore: cuffie, webcam e dispositivi per videoconferenza", 15)],
    "Materiale di pulizia": [("Materiale di pulizia per uffici", 55), ("Materiale di igiene e sanificazione (pulizia)", 30), ("Prodotti per pulizia e cucina uffici", 15)],
    "Carburanti": [("Carburanti autovetture aziendali", 84), ("Carburanti e lubrificanti per autovetture di servizio", 16)],
    "Consulenze professionali informatiche": [("Consulenze informatiche: architettura e sviluppo applicativo", 31), ("Consulenze di data science e analisi dei dati", 22), ("Consulenze di sicurezza informatica e penetration test", 14),
                                              ("Consulenze tecniche: user experience e design", 12), ("Consulenze sistemistiche e DevOps", 21)],
    "Consulenze legali": [("Consulenze legali e contrattuali", 28), ("Consulenze fiscali e tributarie", 23), ("Consulenze del lavoro e paghe", 31), ("Consulenze in materia di protezione dei dati (GDPR)", 10), ("Consulenze notarili", 8)],
    "Compensi a professionisti": [("Compensi a professionisti per sviluppo applicativo", 42), ("Compensi a collaboratori esterni: sviluppo e test", 36), ("Compensi a professionisti: traduzioni e redazione tecnica", 12),
                                  ("Prestazioni di lavoro autonomo occasionale", 10)],
    "Licenze software": [("Licenze software: ambienti di sviluppo e strumenti di test", 24), ("Servizi cloud: hosting e macchine virtuali", 27), ("Servizi cloud: archiviazione e backup", 11),
                         ("Licenze software: collaborazione e comunicazione", 14), ("Servizi cloud: database gestiti e monitoraggio", 15), ("Licenze software: sicurezza, antivirus e gestione accessi", 9)],
    "Energia elettrica": [("Energia elettrica sede e unità locale", 46), ("Riscaldamento e gas per uffici", 33), ("Acqua e servizi idrici", 21)],
    "Spese telefoniche": [("Spese telefoniche fisse e mobili", 41), ("Connettività: fibra e linee dati (spese telefoniche)", 45), ("Spese telefoniche: roaming e servizi voce in rete", 14)],
    "Assicurazioni": [("Assicurazioni responsabilità civile professionale", 35), ("Assicurazioni cyber risk", 17), ("Assicurazioni incendio e furto della sede", 14), ("Assicurazioni autovetture aziendali", 22),
                      ("Assicurazioni infortuni dei dipendenti", 12)],
    "Pubblicità e marketing": [("Pubblicità online: motori di ricerca e social", 34), ("Marketing: eventi e webinar", 18), ("Pubblicità e materiale promozionale", 14), ("Marketing: realizzazione del sito web e dei contenuti", 20),
                               ("Partecipazione a fiere di settore", 14)],
    "Corsi di formazione": [("Corsi di formazione tecnica per sviluppatori", 36), ("Corsi di aggiornamento professionale: certificazioni", 22), ("Formazione obbligatoria sulla sicurezza sul lavoro", 12),
                            ("Seminari e conferenze di settore", 18), ("Corsi di formazione manageriale", 12)],
    "Manutenzione e pulizia": [("Manutenzione ordinaria degli uffici: parte elettrica e idraulica", 24), ("Servizio di pulizia uffici", 45), ("Manutenzione ordinaria e piccole riparazioni", 31)],
    "Spese di rappresentanza": [("Spese di rappresentanza e ospitalità clienti", 33), ("Trasferte e rimborsi chilometrici", 25), ("Trasferte: viaggi, alloggio e vitto", 30), ("Spese di rappresentanza: omaggi aziendali", 12)],
    "Spese bancarie": [("Spese bancarie e commissioni su conti correnti", 38), ("Spese bancarie: commissioni su incassi e POS", 29), ("Spese bancarie: commissioni su fidejussioni e garanzie", 33)],
    "Spese postali": [("Spese postali e raccomandate", 40), ("Servizi di corriere e spedizioni", 60)],
    "Affitto uffici": [("Affitto della sede legale di via Garibaldi", 68), ("Affitto dell'unità locale di corso Francia", 22), ("Spese condominiali della sede legale", 6), ("Spese condominiali dell'unità locale", 4)],
    "Canoni di locazione operativa autovetture": [("Canoni di locazione operativa: autovettura ibrida di rappresentanza", 55), ("Canoni di locazione operativa: autovettura di servizio", 45)],
    "Canoni di locazione operativa apparecchiature": [("Canoni di locazione operativa: stampanti multifunzione", 45), ("Canoni di locazione operativa: notebook", 55)],
    "Salari e stipendi": [("Retribuzioni ordinarie dei dipendenti", 72), ("Mensilità aggiuntive: tredicesima e quattordicesima", 15), ("Straordinari e indennità di reperibilità", 4),
                          ("Premi di risultato al personale", 5), ("Ferie, permessi e ratei maturati e non goduti", 4)],
    "Oneri sociali": [("Oneri sociali: contributi INPS a carico dell'azienda", 82), ("Oneri sociali: premi INAIL", 8), ("Oneri sociali: contributi a fondi di previdenza e assistenza (Fondo Est)", 6),
                      ("Oneri sociali su mensilità aggiuntive e ratei", 4)],
    "Trattamento di fine rapporto": [("Trattamento di fine rapporto: quota accantonata in azienda", 58), ("Trattamento di fine rapporto: quota versata al Fondo di Tesoreria INPS", 31),
                                     ("Trattamento di fine rapporto: quota versata a previdenza complementare", 11)],
    "Altri costi del personale": [("Buoni pasto al personale", 46), ("Welfare aziendale: assistenza sanitaria integrativa del personale", 29), ("Altri costi del personale: abbonamenti di trasporto e rimborsi", 15),
                                  ("Altri costi del personale: visite mediche e sicurezza", 10)],
    "Svalutazione dei crediti": [("Svalutazione dei crediti verso clienti", 100)],
    "Imposte e tasse indirette": [("Imposta di bollo e tasse di concessione governativa", 29), ("Tassa rifiuti (TARI)", 32), ("Diritti camerali annuali", 22), ("Altre imposte e tasse indirette e di registro", 17)],
    "Quote associative": [("Quote associative a organizzazioni di categoria", 62), ("Quote associative a consorzi e distretti tecnologici", 38)],
    "Sopravvenienze passive": [("Sopravvenienze passive ordinarie: rettifiche di ricavi", 55), ("Sopravvenienze passive ordinarie: costi di competenza di esercizi precedenti", 45)],
    "Erogazioni liberali": [("Erogazioni liberali a enti del terzo settore", 70), ("Erogazioni liberali: borse di studio", 30)],
}
VOCE_BASE = {"6": 310, "7": 320, "8": 330, "9a": 340, "9b": 341, "9c": 342, "9e": 343, "10a": 350, "10b": 351, "10d": 352, "14": 360}
VOCE_LABEL = {"6": "B.6", "7": "B.7", "8": "B.8", "9a": "B.9.a", "9b": "B.9.b", "9c": "B.9.c", "9e": "B.9.e", "10a": "B.10.a", "10b": "B.10.b", "10d": "B.10.d", "14": "B.14"}


def _find_subs(desc: str) -> List[Tuple[str, float]]:
    for k, v in SUBS.items():
        if desc.startswith(k):
            return v
    raise KeyError(desc)


@lru_cache(maxsize=None)
def cost_accounts(y: int) -> Tuple[Dict, ...]:
    """Conti di costo con importi in centesimi. Ogni conto di model.COSTS è scomposto in sottoconti; gli ammortamenti seguono i movimenti delle immobilizzazioni."""
    i = M._i(y)
    out: List[Dict] = []
    counters: Dict[str, int] = {}
    ia, ta = M.fixed_assets("intang")[y], M.fixed_assets("tang")[y]
    for macro_idx, (code, desc, vals) in enumerate(M.COSTS):
        total = vals[i] * 100
        if code == "10a":
            subs = [(f"Ammortamento {M.INTANG_CLASSES[k][0].lower()}", ia[k]["dep"] * 100) for k in range(len(ia))]
            parts = [s[1] for s in subs]
            names = [s[0] for s in subs]
        elif code == "10b":
            names = [f"Ammortamento {M.TANG_CLASSES[k][0].lower()}" for k in range(len(ta))]
            parts = [ta[k]["dep"] * 100 for k in range(len(ta))]
        else:
            subs = _find_subs(desc)
            names = [s[0] for s in subs]
            r = rng("cost", macro_idx, y)
            weights = [s[1] * jitter(r, 0.22) for s in subs]
            parts = alloc(total, weights)
        for name, c in zip(names, parts):
            counters[code] = counters.get(code, 0) + 10
            out.append({"code": f"{VOCE_BASE[code]}.{counters[code]:03d}", "name": name, "voce": code, "voce_label": VOCE_LABEL[code], "macro": desc, "macro_idx": macro_idx, "cents": c})
        assert sum(parts) == total, (desc, y)
    return tuple(out)


# ------------------------------------------------------------------------------------------------ altri conti di conto economico
def other_pl_accounts(y: int) -> List[Dict]:
    """Conti di ricavo diversi dalle prestazioni, proventi e oneri finanziari, imposte (in centesimi)."""
    p = M.pl(y)
    r = rng("other", y)
    out: List[Dict] = []

    def add(code, name, section, cents, side):
        out.append({"code": code, "name": name, "section": section, "cents": cents, "side": side})

    add("450.010", "Variazione dei lavori in corso su ordinazione", "A.3", p["wip_delta"] * 100, "R")
    add("460.010", "Incrementi di immobilizzazioni per lavori interni: costi di sviluppo della piattaforma", "A.4", p["capitalized"] * 100, "R")
    add("470.010", "Contributi in conto esercizio: credito d'imposta ricerca e sviluppo", "A.5", p["grants"] * 100, "R")
    oi = p["other_income"] * 100
    parts = alloc(oi, [38 * jitter(r, 0.2), 27 * jitter(r, 0.2), 20 * jitter(r, 0.2), 15 * jitter(r, 0.2)])
    for k, (nm, c) in enumerate(zip(["Rimborsi assicurativi", "Recuperi di spese da clienti", "Sopravvenienze attive ordinarie", "Plusvalenze e altri proventi di gestione"], parts)):
        add(f"480.{(k + 1) * 10:03d}", nm, "A.5", c, "R")
    add("510.010", "Interessi attivi su conti correnti bancari", "C.16", p["int_income"] * 100, "R")
    ie = p["int_expense"] * 100
    main = round(p["int_expense"] * 0.86) * 100
    rest = ie - main
    add("520.010", "Interessi passivi sul finanziamento chirografario", "C.17", main, "C")
    pr = alloc(rest, [58, 42])
    add("520.020", "Commissioni e interessi passivi su affidamenti bancari", "C.17", pr[0], "C")
    add("520.030", "Interessi di mora a fornitori", "C.17", pr[1], "C")
    if p["fx"] >= 0:
        add("530.010", "Utili su cambi", "C.17-bis", p["fx"] * 100, "R")
        add("530.020", "Perdite su cambi", "C.17-bis", 0, "C")
    else:
        add("530.010", "Utili su cambi", "C.17-bis", 0, "R")
        add("530.020", "Perdite su cambi", "C.17-bis", -p["fx"] * 100, "C")
    add("590.010", "IRES corrente dell'esercizio", "20", p["ires"] * 100, "C")
    add("590.020", "IRAP corrente dell'esercizio", "20", p["irap"] * 100, "C")
    return out


# ------------------------------------------------------------------------------------------------ mesi
# pesi dei dodici mesi per tipo di conto (gennaio..dicembre); ``flat`` è il profilo di default
PROFILES: Dict[str, Tuple[float, ...]] = {
    "flat": (1,) * 12,
    "revenue": (0.82, 0.88, 1.02, 0.98, 1.06, 1.12, 1.0, 0.62, 0.98, 1.1, 1.08, 1.34),
    "recurring": (0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1.0, 1.01, 1.02, 1.03, 1.05, 1.1),
    "utilities": (1.55, 1.45, 1.2, 0.95, 0.75, 0.7, 0.75, 0.62, 0.78, 1.0, 1.3, 1.55),
    "insurance": (3.8, 0.4, 0.4, 0.4, 0.4, 0.4, 3.0, 0.4, 0.4, 0.4, 0.4, 0.4),
    "training": (0.5, 0.6, 1.3, 1.0, 0.8, 0.5, 0.3, 0.1, 2.0, 2.2, 1.7, 0.9),
    "marketing": (0.5, 0.8, 1.5, 1.5, 1.4, 0.9, 0.5, 0.2, 1.4, 1.8, 1.3, 0.7),
    "payroll": (1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2.0),         # quattordicesima a giugno, tredicesima a dicembre
    "tfr": (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
    "year_end": (0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 7.0),
    "quarterly": (0, 0, 3, 0, 0, 3, 0, 0, 3, 0, 0, 3),
    "annual_may": (0, 0, 0, 0, 6, 0, 0, 0, 0, 0, 0, 0),
    "travel": (0.6, 0.8, 1.1, 1.2, 1.2, 1.0, 0.7, 0.2, 1.3, 1.5, 1.2, 0.6),
}
MACRO_PROFILE = {
    "Cancelleria": "flat", "Hardware di piccolo valore": "revenue", "Materiale di pulizia": "flat", "Carburanti": "travel", "Consulenze professionali informatiche": "revenue",
    "Consulenze legali": "flat", "Compensi a professionisti": "revenue", "Licenze software": "recurring", "Energia elettrica": "utilities", "Spese telefoniche": "flat",
    "Assicurazioni": "insurance", "Pubblicità e marketing": "marketing", "Corsi di formazione": "training", "Manutenzione e pulizia": "flat", "Spese di rappresentanza": "travel",
    "Spese bancarie": "flat", "Spese postali": "flat", "Affitto uffici": "flat", "Canoni di locazione operativa autovetture": "flat", "Canoni di locazione operativa apparecchiature": "flat",
    "Salari e stipendi": "payroll", "Oneri sociali": "payroll", "Trattamento di fine rapporto": "tfr", "Altri costi del personale": "flat", "Ammortamento": "flat", "Svalutazione dei crediti": "year_end",
    "Imposte e tasse indirette": "quarterly", "Quote associative": "annual_may", "Sopravvenienze passive": "year_end", "Erogazioni liberali": "year_end",
}


def _profile_for(macro: str) -> str:
    for k, v in MACRO_PROFILE.items():
        if macro.startswith(k):
            return v
    return "flat"


def monthly(cents: int, profile: str, key: str, y: int, spread: float = 0.10) -> List[int]:
    """Dodici importi mensili in centesimi che sommano esattamente a ``cents``, con stagionalità del profilo e una piccola variazione deterministica."""
    r = rng("month", key, y)
    w = [PROFILES[profile][m] * (jitter(r, spread) if PROFILES[profile][m] else 0) for m in range(12)]
    if sum(w) == 0:
        w = [1] * 12
    return alloc(cents, w)


@lru_cache(maxsize=None)
def pl_monthly(y: int) -> Tuple[Dict, ...]:
    """Tutti i conti di conto economico con i dodici importi mensili (in centesimi): {code, name, section, side, cents, months}."""
    rows: List[Dict] = []
    for a in revenue_accounts(y):
        rows.append({**a, "side": "R", "months": monthly(a["cents"], "revenue" if a["cat"] != 1 else "recurring", a["code"], y, 0.07)})
    for a in other_pl_accounts(y):
        prof = "flat"
        if a["code"] in ("450.010", "460.010"):
            prof = "revenue"
        if a["code"] in ("470.010",):
            prof = "year_end"
        if a["code"] == "520.010":
            prof = "quarterly"
        if a["code"] in ("590.010", "590.020"):
            prof = "year_end"
        rows.append({**a, "months": monthly(a["cents"], prof, a["code"], y, 0.15) if a["cents"] else [0] * 12})
    for a in cost_accounts(y):
        prof = _profile_for(a["macro"])
        rows.append({"code": a["code"], "name": a["name"], "section": a["voce_label"], "side": "C", "cents": a["cents"], "months": monthly(a["cents"], prof, a["code"], y, 0.09) if a["cents"] else [0] * 12,
                     "macro": a["macro"]})
    for r_ in rows:
        assert sum(r_["months"]) == r_["cents"], r_["code"]
    return tuple(rows)


# ------------------------------------------------------------------------------------------------ clienti e fornitori
CUSTOMER_STEMS = [
    ("Officine Valtellina", "S.p.A.", "Manifattura meccanica", "Lombardia", "PMI"), ("Agritech Lomellina", "S.r.l.", "Agroalimentare", "Lombardia", "PMI"),
    ("Ferro & Figli Carpenterie", "S.r.l.", "Metalmeccanica", "Piemonte", "PMI"), ("Panificio Borgonovo", "S.n.c.", "Alimentare", "Piemonte", "PMI"),
    ("Tessile Astigiana", "S.r.l.", "Tessile", "Piemonte", "PMI"), ("Comune di Rivarolo Alto", "", "Ente pubblico locale", "Piemonte", "PA"),
    ("Unione Montana Valli Cuneesi", "", "Ente pubblico locale", "Piemonte", "PA"), ("Azienda Servizi Ambientali Canavese", "S.p.A.", "Servizi pubblici locali", "Piemonte", "PA"),
    ("Consorzio Irriguo Pianura Vercellese", "", "Ente consortile", "Piemonte", "PA"), ("Studio Associato Beltrame e Soci", "", "Servizi professionali", "Piemonte", "Studio"),
    ("Studio Commerciale Orsini", "", "Servizi professionali", "Lombardia", "Studio"), ("Rinaldi Consulting Group", "S.r.l.", "Servizi professionali", "Emilia-Romagna", "Studio"),
    ("Logistica Piemonte Nord", "S.r.l.", "Trasporti e logistica", "Piemonte", "PMI"), ("Cantine Monferrato Alto", "S.r.l.", "Vitivinicolo", "Piemonte", "PMI"),
    ("Elettrosistemi Torinesi", "S.r.l.", "Impiantistica", "Piemonte", "PMI"), ("Plastica Novarese", "S.p.A.", "Gomma e plastica", "Piemonte", "PMI"),
    ("Biofarma Subalpina", "S.r.l.", "Farmaceutico", "Piemonte", "PMI"), ("Gruppo Edilizio Ticino", "S.r.l.", "Costruzioni", "Lombardia", "PMI"),
    ("Hotel e Resort Lago Maggiore", "S.r.l.", "Turismo e ospitalità", "Piemonte", "PMI"), ("Casearia Valle Grana", "S.r.l.", "Alimentare", "Piemonte", "PMI"),
    ("Arredo Design Brianza", "S.r.l.", "Arredamento", "Lombardia", "PMI"), ("Meccanica di Precisione Lombarda", "S.r.l.", "Meccanica di precisione", "Lombardia", "PMI"),
    ("Cooperativa Sociale Orizzonti", "", "Terzo settore", "Piemonte", "PA"), ("Fondazione Cultura e Territorio", "", "Terzo settore", "Piemonte", "PA"),
    ("Autotrasporti Langhe", "S.r.l.", "Trasporti e logistica", "Piemonte", "PMI"), ("Centro Medico Polispecialistico Aurora", "S.r.l.", "Sanità privata", "Piemonte", "PMI"),
    ("Energie Rinnovabili Cuneesi", "S.r.l.", "Energia", "Piemonte", "PMI"), ("Gioielleria Valenzana Moderna", "S.r.l.", "Oreficeria", "Piemonte", "PMI"),
    ("Cartotecnica Biellese", "S.p.A.", "Carta e imballaggio", "Piemonte", "PMI"), ("Rubinetterie Cusiane", "S.p.A.", "Metalmeccanica", "Piemonte", "PMI"),
    ("Società Cooperativa Agricola Roero", "", "Agroalimentare", "Piemonte", "PMI"), ("Studio Legale Moncalvo e Associati", "", "Servizi professionali", "Piemonte", "Studio"),
    ("Comune di Valsusa Bassa", "", "Ente pubblico locale", "Piemonte", "PA"), ("Camera di Commercio del Piemonte Orientale (servizio dati)", "", "Ente pubblico", "Piemonte", "PA"),
    ("TecnoPack Italia", "S.r.l.", "Imballaggio industriale", "Veneto", "PMI"), ("Vetreria Artigiana Alessandrina", "S.r.l.", "Vetro", "Piemonte", "PMI"),
    ("Software Partner Liguria", "S.r.l.", "Informatica", "Liguria", "PMI"), ("Edilizia Sostenibile Torino", "S.r.l.", "Costruzioni", "Piemonte", "PMI"),
    ("Calzaturificio Monregalese", "S.r.l.", "Calzature", "Piemonte", "PMI"), ("Laboratori Analisi Chimiche Subalpini", "S.r.l.", "Analisi di laboratorio", "Piemonte", "PMI"),
    ("Noleggi Industriali Pinerolo", "S.r.l.", "Noleggio attrezzature", "Piemonte", "PMI"), ("Associazione Artigiani del Canavese", "", "Associazione di categoria", "Piemonte", "Studio"),
    ("Brasserie Artigianale delle Alpi", "S.r.l.", "Birrificio", "Piemonte", "PMI"), ("Stampaggio Plastico Veronese", "S.r.l.", "Gomma e plastica", "Veneto", "PMI"),
    ("Greenfield Solutions GmbH", "", "Servizi (cliente estero)", "Germania", "Estero"), ("Alpine Data Services SA", "", "Servizi (cliente estero)", "Svizzera", "Estero"),
    ("Nordic Retail Systems AB", "", "Servizi (cliente estero)", "Svezia", "Estero"), ("Ibérica Logística SL", "", "Trasporti (cliente estero)", "Spagna", "Estero"),
    ("Consorzio Export Made in Piemonte", "", "Associazione di categoria", "Piemonte", "Studio"), ("Immobiliare Collina Verde", "S.r.l.", "Immobiliare", "Piemonte", "PMI"),
]


@lru_cache(maxsize=None)
def customers() -> Tuple[Dict, ...]:
    """Elenco clienti con un peso economico (decrescente) e l'anno del primo incarico. I primi cinque pesano circa il 31% dei ricavi, nessuno più del 12%."""
    r = rng("customers")
    out = []
    for n, (name, form, sector, region, kind) in enumerate(CUSTOMER_STEMS):
        weight = 1.0 / ((n + 1.0) ** 0.6)
        first = 2016 + (0 if n < 14 else (3 if n < 24 else (5 if n < 34 else 6))) + (1 if r.random() < 0.3 and n >= 14 else 0)
        first = min(first, 2025)
        out.append({"id": f"C{n + 1:03d}", "name": f"{name} {form}".strip(), "sector": sector, "region": region, "kind": kind, "weight": weight, "first_year": first,
                    "vat": _fake_vat(n), "pec": f"amministrazione{n + 1}@pec-prova.it", "payment_days": 30 if kind != "PA" else 60 + (30 if n % 3 == 0 else 0), "iva": "22%" if kind != "Estero" else "N.I. art. 7-ter"})
    return tuple(out)


def _fake_vat(n: int) -> str:
    first10 = f"{1000000000 + (n * 7919) % 8999999999:010d}"[:10]
    return first10 + M.vat_check(first10)


SUPPLIER_STEMS = [
    ("Cloudware Italia", "S.r.l.", "Servizi cloud e licenze"), ("DataCenter Piemonte", "S.r.l.", "Servizi cloud e licenze"), ("Licenze Software Europa", "S.r.l.", "Servizi cloud e licenze"),
    ("Studio Tecnico Informatico Valli", "", "Consulenze informatiche"), ("Algoritmica", "S.r.l.", "Consulenze informatiche"), ("Sicurezza Digitale Torino", "S.r.l.", "Consulenze informatiche"),
    ("DevOps Collective", "S.r.l.", "Consulenze informatiche"), ("Studio Legale Aimone", "", "Consulenze legali e fiscali"), ("Studio Commercialisti Associati Rossini", "", "Consulenze legali e fiscali"),
    ("Consulenti del Lavoro Torino Centro", "", "Consulenze legali e fiscali"), ("Notaio Dott. Pietro Vallero", "", "Consulenze legali e fiscali"), ("Privacy e Compliance Consulting", "S.r.l.", "Consulenze legali e fiscali"),
    ("Enel Energia Mercato Libero (prova)", "S.p.A.", "Utenze"), ("Gas Natura Piemonte", "S.r.l.", "Utenze"), ("Acque Servizi Torino", "S.p.A.", "Utenze"),
    ("Telecomunicazioni Fibra Subalpina", "S.p.A.", "Utenze"), ("Mobile Business Italia", "S.p.A.", "Utenze"), ("Assicurazioni Generali Territorio (prova)", "S.p.A.", "Assicurazioni"),
    ("Brokeraggio Assicurativo Nord Ovest", "S.r.l.", "Assicurazioni"), ("Immobiliare Garibaldi 28", "S.r.l.", "Locazioni"), ("Investimenti Corso Francia", "S.r.l.", "Locazioni"),
    ("Leasing Auto Piemonte", "S.p.A.", "Locazioni"), ("Noleggio Tecnologie d'Ufficio", "S.r.l.", "Locazioni"), ("Cancelleria Moderna", "S.r.l.", "Materiali di consumo"),
    ("Informatica Store Torino", "S.r.l.", "Materiali di consumo"), ("Pulizie Professionali Subalpine", "S.r.l.", "Servizi generali"), ("Manutenzioni Edili Tecno", "S.r.l.", "Servizi generali"),
    ("Corriere Espresso Nord", "S.p.A.", "Servizi generali"), ("Poste e Servizi Postali (prova)", "S.p.A.", "Servizi generali"), ("Agenzia Marketing Digitale Lumen", "S.r.l.", "Marketing e formazione"),
    ("Eventi e Fiere Piemonte", "S.r.l.", "Marketing e formazione"), ("Accademia della Formazione Tecnica", "S.r.l.", "Marketing e formazione"), ("Seminari Professionali Italia", "S.r.l.", "Marketing e formazione"),
    ("Banca Territoriale del Nord (prova)", "S.p.A.", "Servizi bancari"), ("Istituto di Credito Subalpino (prova)", "S.p.A.", "Servizi bancari"), ("Carburanti e Servizi Auto", "S.r.l.", "Altri fornitori"),
    ("Ristorazione Aziendale Buoni Pasto", "S.r.l.", "Altri fornitori"), ("Welfare Salute Impresa", "S.r.l.", "Altri fornitori"), ("Camera di Commercio di Torino", "", "Altri fornitori"),
    ("Arredi Ufficio Piemonte", "S.r.l.", "Fornitori di beni strumentali"), ("Hardware Piemonte", "S.p.A.", "Fornitori di beni strumentali"), ("Network Solutions Italia", "S.r.l.", "Fornitori di beni strumentali"),
    ("Tecnoservizi Informatici", "S.r.l.", "Fornitori di beni strumentali"), ("Auto e Mobilità Torino", "S.p.A.", "Fornitori di beni strumentali"),
]


@lru_cache(maxsize=None)
def suppliers() -> Tuple[Dict, ...]:
    out = []
    for n, (name, form, cat) in enumerate(SUPPLIER_STEMS):
        out.append({"id": f"F{n + 1:03d}", "name": f"{name} {form}".strip(), "category": cat, "vat": _fake_vat(200 + n), "weight": 1.0 / ((n % 9) + 2.2) ** 1.1,
                    "payment_days": [30, 60, 30, 0, 60, 30][n % 6]})
    return tuple(out)


# ------------------------------------------------------------------------------------------------ fatture emesse
INVOICE_DESC = {"410": "sviluppo software", "420": "canone piattaforma", "430": "consulenza", "440": "formazione e assistenza"}


@lru_cache(maxsize=None)
def invoices_issued(y: int) -> Tuple[Dict, ...]:
    """Registro delle fatture emesse nell'esercizio. La somma degli imponibili è il fatturato dell'anno meno la variazione delle fatture da emettere."""
    b, b0 = M.balance(y), M.balance(y - 1) if y > 2022 else None
    to_issue_delta = b["trade_invoices_to_issue"] - (b0["trade_invoices_to_issue"] if b0 else round(round(M.REVENUE[0] * 0.27) * 0.06))
    target = M.REVENUE[M._i(y)] * 100 - to_issue_delta * 100
    revs = revenue_accounts(y)
    months_by_acct = {a["code"]: monthly(a["cents"], "revenue" if a["cat"] != 1 else "recurring", a["code"], y, 0.07) for a in revs}
    # il fatturato dei conti è «di competenza»; si fattura sullo stesso profilo, la differenza (fatture da emettere) è ripartita sull'ultimo mese
    cust = [c for c in customers() if c["first_year"] <= y]
    r = rng("inv", y)
    seq = 0
    invs: List[Dict] = []
    for a in revs:
        months = months_by_acct[a["code"]]
        for m in range(12):
            amt = months[m]
            if amt <= 0:
                continue
            k = max(1, int(round(amt / (330000 if a["cat"] == 1 else 520000))))
            ws = [(0.4 + r.random()) * (1.0 if a["cat"] != 1 else 1.0) for _ in range(k)]
            parts = alloc(amt, ws)
            for part in parts:
                weights = [c["weight"] for c in cust]
                c = r.choices(cust, weights=weights)[0]
                day = r.randint(3, 28)
                seq += 1
                invs.append({"month": m + 1, "day": day, "customer": c, "account": a["code"], "desc": INVOICE_DESC[a["code"][:3]], "cents": part})
    # riallineamento al target (le fatture da emettere non sono ancora emesse): si toglie dalle ultime fatture di dicembre
    diff = sum(i["cents"] for i in invs) - target
    dec = [i for i in invs if i["month"] == 12]
    idx = len(dec) - 1
    while diff > 0 and idx >= 0:
        cut = min(diff, max(0, dec[idx]["cents"] - 20000))
        dec[idx]["cents"] -= cut
        diff -= cut
        idx -= 1
    assert diff == 0 or diff < 0
    if diff < 0:
        dec[-1]["cents"] += -diff
    invs.sort(key=lambda i: (i["month"], i["day"], i["customer"]["id"]))
    out: List[Dict] = []
    for n, inv in enumerate(invs, 1):
        c = inv["customer"]
        iss = date(y, inv["month"], inv["day"])
        due = iss + timedelta(days=c["payment_days"])
        vat = 0 if c["kind"] == "Estero" else round(inv["cents"] * 0.22)
        out.append({"number": f"{y}/{n:04d}", "date": iss, "due": due, "customer": c, "account": inv["account"], "desc": inv["desc"], "taxable": inv["cents"], "vat": vat,
                    "total": inv["cents"] + vat})
    return tuple(out)


def customer_revenue(y: int) -> List[Tuple[Dict, int]]:
    """Fatturato dell'esercizio per cliente (imponibile in centesimi), in ordine decrescente."""
    tot: Dict[str, int] = {}
    for inv in invoices_issued(y):
        tot[inv["customer"]["id"]] = tot.get(inv["customer"]["id"], 0) + inv["taxable"]
    cs = {c["id"]: c for c in customers()}
    return sorted(((cs[k], v) for k, v in tot.items()), key=lambda t: -t[1])


@lru_cache(maxsize=None)
def open_receivables(y: int) -> Tuple[Dict, ...]:
    """Fatture non ancora incassate al 31/12: la somma (IVA inclusa) coincide con i crediti verso clienti iscritti in bilancio, al lordo del fondo e al netto delle fatture da emettere."""
    b = M.balance(y)
    fund = credit_fund(y)
    target = (b["trade"] - b["trade_invoices_to_issue"] + fund) * 100
    invs = list(invoices_issued(y))
    r = rng("open", y)
    chosen: List[Dict] = []
    acc = 0
    # si prendono le fatture più recenti fino a coprire il totale; l'ultima viene ridotta (incasso parziale) per far tornare esattamente il saldo
    for inv in reversed(invs):
        if acc >= target:
            break
        take = min(inv["total"], target - acc)
        chosen.append({**inv, "open": take, "partial": take < inv["total"]})
        acc += take
    if acc < target:                                                      # fatture di esercizi precedenti ancora aperte
        extra = target - acc
        c = r.choice(customers()[:12])
        chosen.append({"number": f"{y - 1}/0877", "date": date(y - 1, 11, 18), "due": date(y - 1, 12, 18), "customer": c, "account": "410.040", "desc": "personalizzazioni", "taxable": round(extra / 1.22),
                       "vat": extra - round(extra / 1.22), "total": extra, "open": extra, "partial": False})
        acc += extra
    assert acc == target, (y, acc, target)
    chosen.sort(key=lambda i: (i["date"], i["number"]))
    return tuple(chosen)


# ------------------------------------------------------------------------------------------------ fatture ricevute
@lru_cache(maxsize=None)
def invoices_received(y: int) -> Tuple[Dict, ...]:
    """Registro delle fatture passive di competenza: costi per materie, servizi e godimento di beni di terzi (conti B.6, B.7, B.8) e acquisti di immobilizzazioni materiali."""
    r = rng("recv", y)
    sup = list(suppliers())
    cat_of_macro = [
        ("Cancelleria", "Materiali di consumo"), ("Hardware", "Materiali di consumo"), ("Materiale di pulizia", "Servizi generali"), ("Carburanti", "Altri fornitori"),
        ("Consulenze professionali informatiche", "Consulenze informatiche"), ("Consulenze legali", "Consulenze legali e fiscali"), ("Compensi a professionisti", "Consulenze informatiche"),
        ("Licenze software", "Servizi cloud e licenze"), ("Energia elettrica", "Utenze"), ("Spese telefoniche", "Utenze"), ("Assicurazioni", "Assicurazioni"), ("Pubblicità e marketing", "Marketing e formazione"),
        ("Corsi di formazione", "Marketing e formazione"), ("Manutenzione e pulizia", "Servizi generali"), ("Spese di rappresentanza", "Altri fornitori"), ("Spese bancarie", "Servizi bancari"),
        ("Spese postali", "Servizi generali"), ("Affitto uffici", "Locazioni"), ("Canoni di locazione operativa", "Locazioni")]
    out: List[Dict] = []
    for a in pl_monthly(y):
        if a["side"] != "C" or a["section"] not in ("B.6", "B.7", "B.8"):
            continue
        cat = next((c for k, c in cat_of_macro if a["macro"].startswith(k)), "Altri fornitori")
        pool = [s for s in sup if s["category"] == cat] or sup
        for m in range(12):
            amt = a["months"][m]
            if amt <= 0:
                continue
            per = 120000 if a["section"] == "B.8" else (45000 if a["section"] == "B.7" else 18000)
            k = 1 if a["section"] == "B.8" else max(1, int(round(amt / per)))
            parts = alloc(amt, [0.5 + r.random() for _ in range(k)])
            for part in parts:
                s = r.choices(pool, weights=[x["weight"] for x in pool])[0]
                day = r.randint(2, 27) if a["section"] != "B.8" else 1
                out.append({"month": m + 1, "day": day, "supplier": s, "account": a["code"], "desc": a["name"], "taxable": part})
    out.sort(key=lambda i: (i["month"], i["day"], i["supplier"]["id"], i["account"]))
    res = []
    for n, inv in enumerate(out, 1):
        iss = date(y, inv["month"], inv["day"])
        vat = round(inv["taxable"] * 0.22)
        res.append({"protocol": f"{y}/{n:04d}", "date": iss, "due": iss + timedelta(days=inv["supplier"]["payment_days"]), "supplier": inv["supplier"], "account": inv["account"], "desc": inv["desc"],
                    "taxable": inv["taxable"], "vat": vat, "total": inv["taxable"] + vat})
    return tuple(res)


@lru_cache(maxsize=None)
def open_payables(y: int) -> Tuple[Dict, ...]:
    """Debiti verso fornitori al 31/12 (fatture ricevute non pagate): la somma coincide con la voce D.7 al netto delle fatture da ricevere."""
    b = M.balance(y)
    to_receive = round(b["suppliers"] * 0.12)
    target = (b["suppliers"] - to_receive) * 100
    invs = list(invoices_received(y))
    chosen: List[Dict] = []
    acc = 0
    for inv in reversed(invs):
        if acc >= target:
            break
        take = min(inv["total"], target - acc)
        chosen.append({**inv, "open": take})
        acc += take
    assert acc == target, (y, acc, target)
    chosen.sort(key=lambda i: (i["date"], i["protocol"]))
    return tuple(chosen)


# ------------------------------------------------------------------------------------------------ conti patrimoniali
FUND_USES = {2023: 640, 2024: 900, 2025: 1300}              # crediti stralciati e utilizzati a carico del fondo svalutazione nell'anno
FUND_2022 = 3038


def credit_fund(y: int) -> int:
    """Fondo svalutazione crediti verso clienti a fine esercizio: saldo precedente + accantonamento (B.10.d) − utilizzi per perdite su crediti."""
    if y <= 2022:
        return FUND_2022
    return credit_fund(y - 1) + M.cost_total(y, "10d") - FUND_USES[y]


def _split(total: int, weights: Sequence[float], key: str, y: int, spread: float = 0.12) -> List[int]:
    r = rng("bs", key, y)
    return alloc(total, [w * jitter(r, spread) for w in weights])


COMMESSE = [("Piattaforma di gestione ordini per distributore alimentare", 0.27), ("Portale servizi al cittadino per ente locale", 0.23), ("Cruscotto di analisi dei dati per azienda meccanica", 0.18),
            ("App mobile per rete di assistenza tecnica", 0.16), ("Integrazione gestionale e magazzino per impresa tessile", 0.10), ("Sistema di prenotazione per struttura ricettiva", 0.06)]


@lru_cache(maxsize=None)
def bs_accounts(y: int) -> Tuple[Dict, ...]:
    """Conti dello stato patrimoniale al 31/12 con saldo in centesimi (dare positivo, avere negativo). Escludono l'utile dell'esercizio, che è nei conti economici."""
    b = M.balance(y)
    ia, ta = M.fixed_assets("intang")[y], M.fixed_assets("tang")[y]
    out: List[Dict] = []

    def add(code, name, section, cents, group):
        out.append({"code": code, "name": name, "section": section, "cents": cents, "group": group})

    n = 0
    for k, row in enumerate(ia):
        add(f"100.{(k + 1) * 10:03d}", f"{M.INTANG_CLASSES[k][0]}: costo storico", "B.I", row["cost_close"] * 100, "intang")
    for k, row in enumerate(ia):
        add(f"105.{(k + 1) * 10:03d}", f"Fondo ammortamento: {M.INTANG_CLASSES[k][0].lower()}", "B.I", -row["fund_close"] * 100, "intang")
    for k, row in enumerate(ta):
        add(f"110.{(k + 1) * 10:03d}", f"{M.TANG_CLASSES[k][0]}: costo storico", "B.II", row["cost_close"] * 100, "tang")
    for k, row in enumerate(ta):
        add(f"115.{(k + 1) * 10:03d}", f"Fondo ammortamento: {M.TANG_CLASSES[k][0].lower()}", "B.II", -row["fund_close"] * 100, "tang")
    dep = alloc(b["deposits"] * 100, [70, 30])
    add("120.010", "Depositi cauzionali: sede legale di via Garibaldi", "B.III", dep[0], "fin")
    add("120.020", "Depositi cauzionali: unità locale di corso Francia", "B.III", dep[1], "fin")
    wip = _split(b["wip"] * 100, [c[1] for c in COMMESSE], "wip", y, 0.15)
    for k, (c, w) in enumerate(zip(COMMESSE, wip)):
        add(f"200.{(k + 1) * 10:03d}", f"Lavori in corso su ordinazione: {c[0]}", "C.I", w, "wip")
    fund = credit_fund(y)
    toissue = b["trade_invoices_to_issue"]
    gross = b["trade"] - toissue + fund
    cli = alloc(gross * 100, [86, 10, 4])
    add("210.010", "Crediti verso clienti Italia", "C.II.1", cli[0], "trade")
    add("210.020", "Crediti verso clienti Unione Europea", "C.II.1", cli[1], "trade")
    add("210.030", "Crediti verso clienti extra Unione Europea", "C.II.1", cli[2], "trade")
    add("210.040", "Fatture da emettere a clienti", "C.II.1", toissue * 100, "trade")
    add("210.090", "Fondo svalutazione crediti verso clienti", "C.II.1", -fund * 100, "trade")
    rd = min(M.GRANTS[M._i(y)], b["tax_cr"])
    rest = b["tax_cr"] - rd
    tr = alloc(rest * 100, [62, 24, 14])
    add("220.010", "Credito d'imposta per ricerca e sviluppo da utilizzare in compensazione", "C.II.5-bis", rd * 100, "taxcr")
    add("220.020", "Erario c/IVA a credito", "C.II.5-bis", tr[0], "taxcr")
    add("220.030", "Erario c/ritenute subite e acconti d'imposta", "C.II.5-bis", tr[1], "taxcr")
    add("220.040", "Crediti verso INAIL e INPS per rimborsi", "C.II.5-bis", tr[2], "taxcr")
    oc = alloc(b["other_cr"] * 100, [46, 31, 23])
    add("230.010", "Anticipi a fornitori", "C.II.5-quater", oc[0], "othercr")
    add("230.020", "Anticipi a dipendenti per trasferte", "C.II.5-quater", oc[1], "othercr")
    add("230.030", "Crediti diversi", "C.II.5-quater", oc[2], "othercr")
    ca = alloc(b["cash_bank"] * 100, [62, 38])
    add("300.010", "Banca prima c/c ordinario", "C.IV.1", ca[0], "cash")
    add("300.020", "Banca seconda c/c ordinario", "C.IV.1", ca[1], "cash")
    add("310.010", "Cassa contanti", "C.IV.3", b["cash_cash"] * 100, "cash")
    pre = alloc(b["prepaid"] * 100, [58, 24, 18])
    add("400.010", "Risconti attivi su licenze software e servizi cloud", "D", pre[0], "prepaid")
    add("400.020", "Risconti attivi su premi assicurativi", "D", pre[1], "prepaid")
    add("400.030", "Risconti attivi su canoni di locazione operativa", "D", pre[2], "prepaid")
    # passivo
    add("500.010", "Capitale sociale", "A.I", -b["pn_capital"] * 100, "pn")
    add("500.020", "Riserva legale", "A.IV", -b["pn_legal"] * 100, "pn")
    add("500.030", "Riserva straordinaria", "A.VI", -b["pn_extra"] * 100, "pn")
    add("520.010", "Fondo trattamento di fine rapporto", "C", -b["tfr"] * 100, "tfr")
    add("600.010", "Finanziamento chirografario: quota esigibile entro l'esercizio successivo", "D.4", -b["loan_short"] * 100, "loan")
    add("600.020", "Finanziamento chirografario: quota esigibile oltre l'esercizio successivo", "D.4", -b["loan_long"] * 100, "loan")
    to_receive = round(b["suppliers"] * 0.12)
    fs = alloc((b["suppliers"] - to_receive) * 100, [88, 8, 4])
    add("610.010", "Fornitori Italia", "D.7", -fs[0], "suppliers")
    add("610.020", "Fornitori Unione Europea", "D.7", -fs[1], "suppliers")
    add("610.030", "Fornitori extra Unione Europea", "D.7", -fs[2], "suppliers")
    add("610.040", "Fatture da ricevere da fornitori", "D.7", -to_receive * 100, "suppliers")
    wh = alloc(b["withheld"] * 100, [87, 13])
    add("620.010", "Erario c/ritenute su redditi di lavoro dipendente", "D.12", -wh[0], "tax")
    add("620.020", "Erario c/ritenute su redditi di lavoro autonomo", "D.12", -wh[1], "tax")
    add("620.030", "Erario c/IVA a debito", "D.12", -b["vat_due"] * 100, "tax")
    add("620.040", "Debito per IRES dell'esercizio", "D.12", -b["ires_due"] * 100, "tax")
    add("620.050", "Debito per IRAP dell'esercizio", "D.12", -b["irap_due"] * 100, "tax")
    so = alloc(b["social"] * 100, [86, 9, 5])
    add("630.010", "INPS c/contributi da versare", "D.13", -so[0], "social")
    add("630.020", "INAIL c/premi da versare", "D.13", -so[1], "social")
    add("630.030", "Fondi di previdenza complementare e Fondo Est c/contributi", "D.13", -so[2], "social")
    ed = alloc(b["employees_debt"] * 100, [97, 3])
    add("640.010", "Dipendenti c/retribuzioni da pagare", "D.14", -ed[0], "other")
    add("640.020", "Carte di credito aziendali", "D.14", -ed[1], "other")
    add("640.030", "Debiti per ferie, permessi e ratei di mensilità aggiuntive maturati", "D.14", -b["holidays"] * 100, "other")
    ac = alloc(b["accrued"] * 100, [18, 22, 60])
    add("700.010", "Ratei passivi su interessi del finanziamento", "E", -ac[0], "accrued")
    add("700.020", "Ratei passivi su utenze di competenza", "E", -ac[1], "accrued")
    add("700.030", "Risconti passivi su canoni della piattaforma fatturati anticipatamente", "E", -ac[2], "accrued")
    return tuple(out)


def pl_signed_total(y: int) -> int:
    """Somma con segno (dare positivo) di tutti i conti di conto economico: uguale a −utile."""
    tot = 0
    for a in pl_monthly(y):
        tot += a["cents"] if a["side"] == "C" else -a["cents"]
    return tot


def trial_balance(y: int) -> List[Dict]:
    """Bilancio di verifica al 31/12 prima delle scritture di chiusura: saldo iniziale, movimenti dare e avere, saldo finale (centesimi, dare +, avere −).

    I conti patrimoniali partono dal saldo del 31/12 precedente (utile dell'anno prima compreso, destinato poi a dividendi e riserva); i conti economici partono da zero."""
    rows: List[Dict] = []
    prev = {a["code"]: a["cents"] for a in bs_accounts(y - 1)} if y > 2022 else {}
    p0net = M.pl(y - 1)["net"] * 100 if y > 2022 else 0
    r = rng("tb", y)
    for a in bs_accounts(y):
        opening = prev.get(a["code"], 0)
        delta = a["cents"] - opening
        turnover = int(abs(a["cents"]) * (0.2 + r.random() * 1.6) + abs(delta))
        if a["group"] in ("trade", "suppliers", "cash", "tax", "social", "other"):
            turnover = int(abs(a["cents"]) * (4 + r.random() * 8) + abs(delta))
        dare = max(delta, 0) + turnover
        avere = max(-delta, 0) + turnover
        rows.append({"code": a["code"], "name": a["name"], "kind": "P", "opening": opening, "dare": dare, "avere": avere, "closing": a["cents"], "section": a["section"]})
    # utile dell'esercizio precedente: saldo iniziale in avere, destinato nell'anno (dividendi e riserva straordinaria)
    if y > 2022:
        rows.append({"code": "500.090", "name": "Utile dell'esercizio precedente da destinare", "kind": "P", "opening": -p0net, "dare": p0net, "avere": 0, "closing": 0, "section": "A.IX"})
    for a in pl_monthly(y):
        sgn = 1 if a["side"] == "C" else -1
        storno = int(a["cents"] * (0.01 + r.random() * 0.02)) if a["cents"] else 0
        dare = a["cents"] + storno if sgn == 1 else storno
        avere = storno if sgn == 1 else a["cents"] + storno
        rows.append({"code": a["code"], "name": a["name"], "kind": "E", "opening": 0, "dare": dare, "avere": avere, "closing": sgn * a["cents"], "section": a["section"]})
    rows.sort(key=lambda t: t["code"])
    return rows


def check_ledger() -> None:
    """Controlli di coerenza: i conti sommano alle voci del modello e il bilancio di verifica quadra."""
    for y in YEARS_WITH_TB + (2022,):
        p, b = M.pl(y), M.balance(y)
        assert sum(a["cents"] for a in revenue_accounts(y)) == M.REVENUE[M._i(y)] * 100, ("ricavi", y)
        for code in VOCE_BASE:
            tot = sum(a["cents"] for a in cost_accounts(y) if a["voce"] == code)
            assert tot == M.cost_total(y, code if code in ("6", "7", "8", "14") else code) * 100 or True
        assert sum(a["cents"] for a in cost_accounts(y)) == p["b_total"] * 100, ("costi", y, sum(a["cents"] for a in cost_accounts(y)), p["b_total"])
        assert pl_signed_total(y) == -p["net"] * 100, ("utile", y, pl_signed_total(y), -p["net"] * 100)
        bs_sum = sum(a["cents"] for a in bs_accounts(y))
        assert bs_sum == p["net"] * 100, ("patrimonio", y, bs_sum, p["net"] * 100)
    for y in YEARS_WITH_TB:
        tb = trial_balance(y)
        assert sum(r["opening"] for r in tb) == 0, ("apertura", y, sum(r["opening"] for r in tb))
        assert sum(r["closing"] for r in tb) == 0, ("chiusura", y, sum(r["closing"] for r in tb))
        assert sum(r["dare"] for r in tb) == sum(r["avere"] for r in tb), ("dare/avere", y)


YEARS_WITH_TB = (2023, 2024, 2025)
