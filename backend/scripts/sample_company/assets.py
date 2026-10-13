"""Registro dei cespiti bene per bene (azienda FITTIZIA): ogni bene ha data di acquisto, fornitore, costo, aliquota, fondo e valore residuo.

I totali per classe e per anno **coincidono con i movimenti del modello** (``model.fixed_assets``): costo storico, fondo, acquisizioni, ammortamento e valore netto.
Le acquisizioni di ogni anno sono ripartite tra i beni acquistati in quell'anno; l'ammortamento tra i beni ancora da ammortizzare (la quota del primo anno è ridotta alla metà).
"""
from __future__ import annotations

from datetime import date
from functools import lru_cache
from typing import Dict, List, Tuple

from . import ledger as LG
from . import model as M

# classe → elenco di beni: (descrizione, anno di acquisto, peso nel costo di quell'anno, mese di acquisto, categoria di fornitore)
INTANG_ITEMS: List[List[Tuple[str, int, float, int, str]]] = [
    [("Piattaforma Atlas: motore di stima (versione 1)", 2018, 0.30, 12, "-"), ("Piattaforma Atlas: modulo di acquisizione dei documenti", 2019, 0.30, 12, "-"),
     ("Piattaforma Atlas: archivio delle regole dei bandi", 2020, 0.25, 12, "-"), ("Piattaforma Atlas: interfaccia web e reportistica", 2021, 0.15, 12, "-"),
     ("Piattaforma Atlas: miglioramento del motore di stima", 2022, 1.0, 12, "-"), ("Piattaforma Atlas: motore di calcolo deterministico", 2023, 1.0, 12, "-"),
     ("Piattaforma Atlas: API e integrazioni verso i gestionali", 2024, 1.0, 12, "-"), ("Piattaforma Atlas: assistente di inserimento dati e modulo di dossier", 2025, 1.0, 12, "-")],
    [("Licenza perpetua ambiente di modellazione UML e CAD", 2017, 0.35, 3, "Servizi cloud e licenze"), ("Software di gestione progetti e ticketing (licenza perpetua)", 2018, 0.4, 6, "Servizi cloud e licenze"),
     ("Software di business intelligence (licenza perpetua)", 2020, 0.25, 9, "Servizi cloud e licenze"), ("Software di contabilità e gestione paghe (licenza)", 2022, 1.0, 2, "Servizi cloud e licenze"),
     ("Software di gestione documentale e firma digitale (licenza)", 2023, 1.0, 5, "Servizi cloud e licenze"), ("Software di analisi statica del codice (licenza perpetua)", 2024, 1.0, 4, "Servizi cloud e licenze"),
     ("Software di monitoraggio e osservabilità (licenza perpetua)", 2025, 1.0, 7, "Servizi cloud e licenze")],
    [("Marchio denominativo ATLAS: registrazione presso l'UIBM", 2019, 0.5, 4, "Consulenze legali e fiscali"), ("Marchio figurativo Meridiana: registrazione e rinnovo", 2020, 0.5, 6, "Consulenze legali e fiscali"),
     ("Certificazione ISO 9001: costi di prima certificazione", 2022, 1.0, 10, "Consulenze informatiche"), ("Certificazione ISO/IEC 27001: costi di prima certificazione", 2023, 1.0, 9, "Consulenze informatiche"),
     ("Licenze d'uso di certificati e domini pluriennali", 2024, 1.0, 3, "Servizi cloud e licenze"), ("Rinnovo marchi e registrazione nome a dominio estero", 2025, 1.0, 5, "Consulenze legali e fiscali")],
    [("Migliorie su beni di terzi: sede legale di via Garibaldi (pareti e impianti)", 2016, 0.6, 3, "Fornitori di beni strumentali"), ("Migliorie su beni di terzi: sala server e cablaggio dedicato", 2019, 0.4, 7, "Fornitori di beni strumentali"),
     ("Migliorie su beni di terzi: unità locale di corso Francia (laboratorio dati)", 2021, 1.0, 9, "Fornitori di beni strumentali"), ("Migliorie su beni di terzi: ampliamento sala riunioni", 2022, 1.0, 6, "Fornitori di beni strumentali"),
     ("Migliorie su beni di terzi: cabina di proiezione e area formazione", 2023, 1.0, 4, "Fornitori di beni strumentali"),
     ("Migliorie su beni di terzi: illuminazione e insonorizzazione open space", 2024, 1.0, 8, "Fornitori di beni strumentali"),
     ("Migliorie su beni di terzi: rifacimento dei servizi e dell'area ristoro", 2025, 1.0, 6, "Fornitori di beni strumentali")],
]
TANG_ITEMS: List[List[Tuple[str, int, float, int, str]]] = [
    [("Cablaggio strutturato degli uffici di via Garibaldi", 2017, 0.35, 4, "Fornitori di beni strumentali"), ("Impianto di condizionamento della sede", 2018, 0.30, 6, "Fornitori di beni strumentali"),
     ("Impianto di videosorveglianza e controllo accessi", 2020, 0.20, 10, "Fornitori di beni strumentali"), ("Impianto elettrico di continuità (UPS) della sala server", 2021, 0.15, 3, "Fornitori di beni strumentali"),
     ("Impianto di rete wireless degli uffici", 2022, 1.0, 5, "Fornitori di beni strumentali"), ("Impianto di rilevazione presenze e domotica leggera", 2023, 1.0, 9, "Fornitori di beni strumentali"),
     ("Impianto di audio-videoconferenza della sala riunioni", 2024, 1.0, 7, "Fornitori di beni strumentali"), ("Impianto di ricarica elettrica per veicoli aziendali", 2025, 1.0, 11, "Fornitori di beni strumentali")],
    [("Server di produzione (cluster di tre nodi)", 2018, 0.30, 5, "Fornitori di beni strumentali"), ("Server di test e integrazione", 2019, 0.20, 9, "Fornitori di beni strumentali"),
     ("Apparati di rete e firewall di perimetro", 2020, 0.20, 2, "Fornitori di beni strumentali"), ("Sistema di storage e backup", 2021, 0.30, 11, "Fornitori di beni strumentali"),
     ("Parco dispositivi di test mobile (smartphone e tablet)", 2022, 1.0, 3, "Fornitori di beni strumentali"), ("Nodo aggiuntivo di calcolo per la piattaforma", 2023, 1.0, 6, "Fornitori di beni strumentali"),
     ("Apparati di laboratorio dati di corso Francia", 2024, 1.0, 10, "Fornitori di beni strumentali"), ("Rinnovo del sistema di storage e backup", 2025, 1.0, 4, "Fornitori di beni strumentali")],
    [("Workstation di sviluppo (primo lotto)", 2017, 0.2, 5, "Fornitori di beni strumentali"), ("Notebook di sviluppo (secondo lotto)", 2019, 0.3, 3, "Fornitori di beni strumentali"),
     ("Monitor 27 pollici (lotto)", 2020, 0.15, 9, "Fornitori di beni strumentali"), ("Stazione di lavoro grafica per la progettazione UX", 2021, 0.15, 6, "Fornitori di beni strumentali"),
     ("Notebook di sviluppo (terzo lotto)", 2021, 0.2, 10, "Fornitori di beni strumentali"), ("Workstation di sviluppo e notebook (lotto 2022)", 2022, 1.0, 4, "Fornitori di beni strumentali"),
     ("Notebook e dispositivi per i nuovi assunti (lotto 2023)", 2023, 1.0, 8, "Fornitori di beni strumentali"), ("Notebook, monitor e dock per i nuovi assunti (lotto 2024)", 2024, 1.0, 5, "Fornitori di beni strumentali"),
     ("Notebook e stazioni di lavoro per i nuovi assunti (lotto 2025)", 2025, 1.0, 9, "Fornitori di beni strumentali")],
    [("Scrivanie operative (lotto iniziale)", 2017, 0.35, 2, "Fornitori di beni strumentali"), ("Sedie ergonomiche (lotto iniziale)", 2017, 0.2, 2, "Fornitori di beni strumentali"),
     ("Armadi e arredi della sala riunioni", 2019, 0.25, 11, "Fornitori di beni strumentali"), ("Arredi del laboratorio dati di corso Francia", 2021, 0.2, 9, "Fornitori di beni strumentali"),
     ("Scrivanie e sedie per l'ampliamento dell'organico (2022)", 2022, 1.0, 5, "Fornitori di beni strumentali"), ("Arredi e scrivanie regolabili (2023)", 2023, 1.0, 7, "Fornitori di beni strumentali"),
     ("Arredi per la sala formazione (2024)", 2024, 1.0, 9, "Fornitori di beni strumentali"), ("Arredi e sedute per i nuovi postazioni di lavoro (2025)", 2025, 1.0, 10, "Fornitori di beni strumentali")],
    [("Autovettura aziendale ibrida di proprietà", 2019, 1.0, 5, "Fornitori di beni strumentali"), ("Dotazioni e allestimenti delle autovetture aziendali (2022)", 2022, 1.0, 6, "Fornitori di beni strumentali"),
     ("Dotazioni e allestimenti delle autovetture aziendali (2023)", 2023, 1.0, 6, "Fornitori di beni strumentali"), ("Dotazioni e allestimenti delle autovetture aziendali (2024)", 2024, 1.0, 6, "Fornitori di beni strumentali"),
     ("Dotazioni e allestimenti delle autovetture aziendali (2025)", 2025, 1.0, 6, "Fornitori di beni strumentali")],
]


def _rates(kind: str) -> List[float]:
    classes = M.INTANG_CLASSES if kind == "intang" else M.TANG_CLASSES
    return [int(c[5].rstrip("%")) / 100 for c in classes]


def _suppliers_for(cat: str):
    pool = [s for s in LG.suppliers() if s["category"] == cat]
    return pool or list(LG.suppliers())


def _alloc_capped(total: int, caps: List[int], weights: List[float]) -> List[int]:
    """Ripartisce ``total`` secondo i pesi senza superare i limiti ``caps``: l'eccedenza si redistribuisce sui beni ancora capienti."""
    out = [0] * len(caps)
    rem = total
    active = [k for k in range(len(caps)) if caps[k] > 0 and weights[k] > 0]
    for _ in range(12):
        if rem <= 0 or not active:
            break
        parts = LG.alloc(rem, [weights[k] for k in active])
        rem = 0
        nxt = []
        for k, p in zip(active, parts):
            room = caps[k] - out[k]
            if p >= room:
                out[k] += room
                rem += p - room
            else:
                out[k] += p
                nxt.append(k)
        active = nxt
    return out


@lru_cache(maxsize=None)
def register(kind: str) -> Dict[int, List[Dict]]:
    """Per ogni esercizio 2022-2025, l'elenco dei beni con i loro movimenti. Le chiavi: class, item, supplier, date, rate, cost_open, capex, cost_close, fund_open, dep, fund_close, net_close."""
    classes = M.INTANG_CLASSES if kind == "intang" else M.TANG_CLASSES
    templates = INTANG_ITEMS if kind == "intang" else TANG_ITEMS
    movements = M.fixed_assets(kind)
    rates = _rates(kind)
    items: List[Dict] = []
    for k, tpl in enumerate(templates):
        pre = [t for t in tpl if t[1] < 2022]
        cost0 = movements[2022][k]["cost_open"]
        pre_costs = LG.alloc(cost0, [t[2] for t in pre])
        for t, c in zip(pre, pre_costs):
            items.append({"class": k, "item": t[0], "year": t[1], "month": t[3], "cost": {2022: c}, "supplier_cat": t[4]})
        for y in M.ALL_YEARS:
            cur = [t for t in tpl if t[1] == y]
            if not cur:
                continue
            parts = LG.alloc(movements[y][k]["capex"], [t[2] for t in cur])
            for t, c in zip(cur, parts):
                items.append({"class": k, "item": t[0], "year": y, "month": t[3], "cost": {y: c}, "supplier_cat": t[4], "bought_in_window": True})
    sup_r = LG.rng("assets", kind)
    for it in items:
        pool = _suppliers_for(it["supplier_cat"]) if it["supplier_cat"] != "-" else []
        it["supplier"] = sup_r.choice(pool)["name"] if pool else "Realizzazione interna (personale e consulenti)"
        it["rate"] = rates[it["class"]]
        it["date"] = date(it["year"], it["month"], min(28, 4 + (it["month"] * 7) % 22))
    # simulazione anno per anno
    state = {id(it): {"cost": 0, "fund": 0} for it in items}
    result: Dict[int, List[Dict]] = {}
    for y in M.ALL_YEARS:
        rows: List[Dict] = []
        for k in range(len(classes)):
            cls_items = [it for it in items if it["class"] == k]
            row = movements[y][k]
            if y == 2022:
                # costo e fondo di apertura: ripartiti sui beni acquistati prima del 2022
                pre = [it for it in cls_items if it["year"] < 2022]
                for it in pre:
                    state[id(it)]["cost"] = it["cost"][2022]
                weights = [it["cost"][2022] * min(1.0, (2022 - it["year"]) * it["rate"] * 0.95) for it in pre]
                fund0 = _alloc_capped(row["fund_open"], [int(it["cost"][2022] * 0.97) for it in pre], weights)
                for it, f in zip(pre, fund0):
                    state[id(it)]["fund"] = f
            snap_open = {id(it): dict(state[id(it)]) for it in cls_items}
            for it in cls_items:
                capex = it["cost"].get(y, 0) if it["year"] == y or (it["year"] < 2022 and False) else 0
                if it["year"] == y:
                    capex = it["cost"][y]
                    state[id(it)]["cost"] += capex
                    snap_open[id(it)]["cost"] = 0
            # ammortamento dell'anno
            caps = [state[id(it)]["cost"] - state[id(it)]["fund"] for it in cls_items]
            w = [state[id(it)]["cost"] * it["rate"] * (0.5 if it["year"] == y else 1.0) for it in cls_items]
            dep = _alloc_capped(row["dep"], caps, w)
            for it, dp in zip(cls_items, dep):
                st = state[id(it)]
                st["fund"] += dp
                rows.append({"class": k, "class_name": classes[k][0], "item": it["item"], "supplier": it["supplier"], "date": it["date"], "rate": it["rate"], "year": it["year"],
                             "cost_open": snap_open[id(it)]["cost"], "capex": it["cost"].get(y, 0) if it["year"] == y else 0, "cost_close": st["cost"],
                             "fund_open": snap_open[id(it)]["fund"], "dep": dp, "fund_close": st["fund"], "net_close": st["cost"] - st["fund"]})
            tot = [r for r in rows if r["class"] == k]
            assert sum(r["cost_close"] for r in tot) == row["cost_close"], (kind, y, k, "costo")
            assert sum(r["fund_close"] for r in tot) == row["fund_close"], (kind, y, k, "fondo", sum(r["fund_close"] for r in tot), row["fund_close"])
            assert sum(r["net_close"] for r in tot) == row["net_close"], (kind, y, k, "netto")
            assert sum(r["dep"] for r in tot) == row["dep"], (kind, y, k, "ammortamento")
        result[y] = rows
    return result


def projected_depreciation(kind: str, years: Tuple[int, ...] = (2026, 2027, 2028, 2029, 2030)) -> List[Dict]:
    """Piano di ammortamento dei beni esistenti al 31/12/2025 (aliquota sul costo, nei limiti del residuo)."""
    out = []
    for r in register(kind)[2025]:
        left = r["net_close"]
        plan = {}
        for yy in years:
            q = min(left, round(r["cost_close"] * r["rate"]))
            plan[yy] = q
            left -= q
        out.append({**r, "plan": plan, "after": left})
    return out
