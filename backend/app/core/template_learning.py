"""Template di budget: come le aziende di una nicchia compongono il budget per vincere un bando, e un algoritmo che impara da quei template.

Il commercialista salva un **template**: per un'azienda di una nicchia (codice ATECO) che ha scelto un bando, com'è ripartito il budget del progetto
(es. 13% consulenze, 16,1% ricerca e sviluppo, 45% beni strumentali…) e com'è andata (bozza, presentato, ammesso, non ammesso).

L'algoritmo non è un modello opaco: è statistica spiegabile e ripetibile (stessi template → stesso consiglio).
- **Chi somiglia a chi** — sei livelli, dal più preciso al più generale: stessa nicchia e stesso bando; stesso settore e stesso bando; stesso bando; stessa nicchia;
  stesso settore; tutti. Si usa il primo livello con almeno ``MIN_TEMPLATES`` template.
- **Chi conta di più** — ogni template pesa secondo l'esito: ammesso 3, presentato 1,5, bozza 1, non ammesso 0,25. Così i budget che hanno vinto trascinano il consiglio.
- **Il consiglio** — media pesata delle quote, con la dispersione (quanto sono diversi i template tra loro) e un livello di fiducia dichiarato.
- **Gli stili** — con almeno ``CLUSTER_MIN`` template si cercano gruppi di budget simili (k-means con seme fisso) e si dice quanti di ciascun gruppo hanno vinto.
- **Auto-miglioramento** — a ogni template nuovo o a ogni esito aggiornato il consiglio si ricalcola da solo: più dati → livello più preciso, dispersione più stretta,
  vincitori più pesanti. Si registra anche quanto ogni template si discostava dal consiglio che c'era al momento del salvataggio: con abbastanza esiti si vede se
  chi si avvicina al consiglio vince più spesso. Nessun testo viene generato: solo conti.

I template sono privati; chi vuole li condivide in forma anonima (niente ragione sociale né partita IVA) e allena l'algoritmo di tutti.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.core import events
from app.core.db import connect
from app.core.pattern_bank import kmeans, silhouette

SHARES = ("personnel_pct", "assets_pct", "consulting_pct", "research_pct", "overhead_pct", "training_pct", "communication_pct", "other_pct")
SHARE_LABEL = {"personnel_pct": "Personale", "assets_pct": "Beni strumentali", "consulting_pct": "Consulenze", "research_pct": "Ricerca e sviluppo",
               "overhead_pct": "Spese generali", "training_pct": "Formazione", "communication_pct": "Comunicazione", "other_pct": "Altro"}
OUTCOMES = ("BOZZA", "PRESENTATO", "AMMESSO", "NON_AMMESSO")
OUTCOME_LABEL = {"BOZZA": "Bozza", "PRESENTATO": "Presentato", "AMMESSO": "Ammesso", "NON_AMMESSO": "Non ammesso"}
OUTCOME_WEIGHT = {"AMMESSO": 3.0, "PRESENTATO": 1.5, "BOZZA": 1.0, "NON_AMMESSO": 0.25}
MIN_TEMPLATES = 3
HIGH_MIN = 8
CLUSTER_MIN = 6
MAX_K = 4
CLOSE_DISTANCE = 0.10        # un budget è «vicino al consiglio» se la distanza (metà della somma degli scarti, 0–1) è al massimo del 10%
MIN_FEEDBACK = 5             # esiti per lato necessari prima di dire se avvicinarsi al consiglio conviene

SECTION_NAME = {"A": "Agricoltura, silvicoltura e pesca", "B": "Estrazione di minerali", "C": "Attività manifatturiere", "D": "Energia elettrica, gas e vapore",
                "E": "Acqua, reti fognarie e rifiuti", "F": "Costruzioni", "G": "Commercio all'ingrosso e al dettaglio", "H": "Trasporto e magazzinaggio",
                "I": "Alloggio e ristorazione", "J": "Informazione e comunicazione", "K": "Attività finanziarie e assicurative", "L": "Attività immobiliari",
                "M": "Attività professionali, scientifiche e tecniche", "N": "Noleggio e servizi di supporto alle imprese", "O": "Amministrazione pubblica",
                "P": "Istruzione", "Q": "Sanità e assistenza sociale", "R": "Attività artistiche, sportive e di intrattenimento", "S": "Altre attività di servizi",
                "T": "Attività di famiglie e convivenze", "U": "Organizzazioni extraterritoriali"}
_SECTION_RANGES = [(1, 3, "A"), (5, 9, "B"), (10, 33, "C"), (35, 35, "D"), (36, 39, "E"), (41, 43, "F"), (45, 47, "G"), (49, 53, "H"), (55, 56, "I"), (58, 63, "J"),
                   (64, 66, "K"), (68, 68, "L"), (69, 75, "M"), (77, 82, "N"), (84, 84, "O"), (85, 85, "P"), (86, 88, "Q"), (90, 93, "R"), (94, 96, "S"), (97, 98, "T"), (99, 99, "U")]
TIERS = [("NICCHIA_E_BANDO", "stessa nicchia e stesso bando"), ("SETTORE_E_BANDO", "stesso settore e stesso bando"), ("BANDO", "stesso bando"),
         ("NICCHIA", "stessa nicchia"), ("SETTORE", "stesso settore"), ("TUTTI", "tutti i template")]


class TemplateError(ValueError):
    pass


def _n(x: float, digits: int = 1) -> str:
    """Numero all'italiana (virgola decimale)."""
    return f"{x:.{digits}f}".replace(".", ",")


# ------------------------------------------------------------------------------------------------ nicchia da codice ATECO
def division_of(ateco_code: str) -> str:
    m = re.match(r"^\s*(\d{2})", str(ateco_code or "").replace(".", ""))
    if not m:
        raise TemplateError("Il codice ATECO ha il formato 62.01 (almeno le prime due cifre)")
    return m.group(1)


def section_of(division: str) -> str:
    d = int(division)
    for lo, hi, letter in _SECTION_RANGES:
        if lo <= d <= hi:
            return letter
    raise TemplateError(f"Divisione ATECO non riconosciuta: {division}")


def niche_label(ateco_code: str) -> Dict[str, str]:
    d = division_of(ateco_code)
    s = section_of(d)
    return {"division": d, "section": s, "section_name": SECTION_NAME[s], "label": f"{SECTION_NAME[s]} · ATECO {d}"}


# ------------------------------------------------------------------------------------------------ quote
def clean_shares(raw: Dict[str, Any]) -> Dict[str, float]:
    """Le quote vanno da 0 a 1 (o in percentuale) e devono sommare 100% (tolleranza del 2%): si normalizzano a 1 esatto."""
    vals = {}
    for k in SHARES:
        v = raw.get(k)
        try:
            vals[k] = float(str(v).replace(",", ".")) if v not in (None, "") else 0.0
        except ValueError:
            raise TemplateError(f"Quota non valida: {SHARE_LABEL[k]}") from None
    unknown = [k for k in raw if k not in SHARES]
    if unknown:
        raise TemplateError(f"Voce sconosciuta: {', '.join(sorted(unknown))}")
    if any(v < 0 for v in vals.values()):
        raise TemplateError("Le quote non possono essere negative")
    total = sum(vals.values())
    if total > 1.5:                                          # scritte in percentuale
        vals = {k: v / 100 for k, v in vals.items()}
        total = sum(vals.values())
    if total <= 0 or abs(total - 1) > 0.02:
        raise TemplateError(f"Le quote devono sommare 100% (sommano {_n(total * 100)}%)")
    return {k: round(v / total, 6) for k, v in vals.items()}


def _vec(shares: Dict[str, float]) -> np.ndarray:
    return np.array([float(shares.get(k, 0.0)) for k in SHARES])


def _distance(a: Dict[str, float], b: Dict[str, float]) -> float:
    return float(np.abs(_vec(a) - _vec(b)).sum() / 2)


# ------------------------------------------------------------------------------------------------ archivio
def _row(r) -> Dict[str, Any]:
    d = dict(r)
    d["shares"] = json.loads(d["shares"])
    d["recommended"] = json.loads(d["recommended"]) if d.get("recommended") else None
    for k in ("total_eur", "score", "distance"):
        d[k] = float(d[k]) if d.get(k) is not None else None
    d["niche"] = niche_label(d["ateco_code"])["label"]
    d["outcome_label"] = OUTCOME_LABEL[d["outcome"]]
    return d


def _pool(owner: str) -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM budget_templates WHERE owner=? OR shared=TRUE ORDER BY id", (owner,)).fetchall()
    return [_row(r) for r in rows]


def list_templates(owner: str) -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM budget_templates WHERE owner=? ORDER BY id DESC", (owner,)).fetchall()
    out = []
    for r in rows:
        d = _row(r)
        d.pop("owner", None)
        out.append(d)
    return out


def _pool_hash(pool: List[Dict[str, Any]]) -> str:
    return hashlib.sha256("|".join(f"{t['id']}:{t['updated_at']}:{t['outcome']}" for t in pool).encode()).hexdigest()[:12]


# ------------------------------------------------------------------------------------------------ il consiglio
def _matches(t: Dict[str, Any], tier: str, division: Optional[str], section: Optional[str], bando_id: Optional[str]) -> bool:
    same_bando = bool(bando_id) and t["bando_id"] == bando_id
    return {"NICCHIA_E_BANDO": same_bando and division is not None and t["ateco_division"] == division,
            "SETTORE_E_BANDO": same_bando and section is not None and t["ateco_section"] == section,
            "BANDO": same_bando, "NICCHIA": division is not None and t["ateco_division"] == division,
            "SETTORE": section is not None and t["ateco_section"] == section, "TUTTI": True}[tier]


def recommend(owner: str, ateco_code: Optional[str], bando_id: Optional[str], draft: Optional[Dict[str, Any]] = None, exclude_id: Optional[int] = None) -> Dict[str, Any]:
    """Il budget consigliato per questa nicchia e questo bando, con i numeri da cui viene. Confronta anche un budget bozza, se c'è."""
    division = section = None
    if ateco_code:
        division = division_of(ateco_code)
        section = section_of(division)
    pool = [t for t in _pool(owner) if t["id"] != exclude_id]
    counts = {tier: sum(1 for t in pool if _matches(t, tier, division, section, bando_id)) for tier, _ in TIERS}
    chosen = next((tier for tier, _ in TIERS if counts[tier] >= MIN_TEMPLATES), None)
    out: Dict[str, Any] = {"tier_counts": [{"tier": t, "label": lbl, "templates": counts[t]} for t, lbl in TIERS], "pool_size": len(pool), "pool_hash": _pool_hash(pool),
                           "min_templates": MIN_TEMPLATES}
    if chosen is None:
        out.update({"status": "NO_DATA", "message": f"Servono almeno {MIN_TEMPLATES} template simili per dare un consiglio: oggi ce ne sono {len(pool)} in tutto. "
                                                     "Salva i budget dei tuoi clienti (con l'esito) e il consiglio nasce da solo."})
        return out
    sel = [t for t in pool if _matches(t, chosen, division, section, bando_id)]
    w = np.array([OUTCOME_WEIGHT[t["outcome"]] for t in sel])
    x = np.array([_vec(t["shares"]) for t in sel])
    mean = (x * w[:, None]).sum(axis=0) / w.sum()
    std = np.sqrt((w[:, None] * (x - mean) ** 2).sum(axis=0) / w.sum())
    wins = sum(1 for t in sel if t["outcome"] == "AMMESSO")
    confidence = "ALTA" if chosen == "NICCHIA_E_BANDO" and len(sel) >= HIGH_MIN else "MEDIA" if chosen in ("NICCHIA_E_BANDO", "SETTORE_E_BANDO", "BANDO") else "BASSA"
    label = dict(TIERS)[chosen]
    rec = {k: round(float(mean[i]), 4) for i, k in enumerate(SHARES)}
    rng = {k: {"low": round(max(0.0, float(mean[i] - std[i])), 4), "high": round(min(1.0, float(mean[i] + std[i])), 4)} for i, k in enumerate(SHARES)}
    explanation = [f"Ho usato {len(sel)} template con {label}" + (f", di cui {wins} ammessi" if wins else "") + ". I budget ammessi pesano 3 volte una bozza, i non ammessi un quarto."]
    top = sorted(SHARES, key=lambda k: -rec[k])[:3]
    explanation.append("Le voci più pesanti: " + ", ".join(f"{SHARE_LABEL[k].lower()} {_n(rec[k] * 100)}%" for k in top) + ".")
    spread = sorted(SHARES, key=lambda k: -std[SHARES.index(k)])[0]
    explanation.append(f"La voce su cui i template sono più diversi è {SHARE_LABEL[spread].lower()} (±{_n(std[SHARES.index(spread)] * 100)} punti): lì c'è più libertà.")
    if confidence != "ALTA":
        need = (HIGH_MIN - counts["NICCHIA_E_BANDO"]) if counts["NICCHIA_E_BANDO"] < HIGH_MIN else 0
        explanation.append(f"Fiducia {confidence.lower()}: il consiglio diventa preciso con {need or 'più'} template della stessa nicchia e dello stesso bando (oggi {counts['NICCHIA_E_BANDO']}).")
    styles = _styles(sel, w, x) if len(sel) >= CLUSTER_MIN else []
    out.update({"status": "OK", "basis": chosen, "basis_label": label, "templates_used": len(sel), "wins": wins, "confidence": confidence, "recommended": rec, "range": rng,
                "average_total_eur": _avg_total(sel), "score_range": _score_range(sel), "styles": styles, "explanation": explanation,
                "outcomes": {o: sum(1 for t in sel if t["outcome"] == o) for o in OUTCOMES}})
    if draft:
        d = clean_shares(draft)
        dev = {k: round((d[k] - rec[k]) * 100, 1) for k in SHARES}
        main = max(SHARES, key=lambda k: abs(dev[k]))
        cos = float(_vec(d) @ mean / (np.linalg.norm(_vec(d)) * np.linalg.norm(mean))) if np.linalg.norm(mean) else 0.0
        out["comparison"] = {"draft": d, "deviations_pp": dev, "main": {"key": main, "label": SHARE_LABEL[main], "pp": dev[main]}, "distance": round(_distance(d, rec), 4),
                             "similarity": round(cos, 3),
                             "message": (f"Il tuo budget dista il {_n(_distance(d, rec) * 100)}% dal consiglio. Lo scostamento maggiore è su {SHARE_LABEL[main].lower()}: "
                                         f"{'+' if dev[main] > 0 else ''}{_n(dev[main])} punti rispetto alla media pesata. Nota professionale: è un'indicazione statistica sulla struttura della spesa, non una previsione di esito.")}
    return out


def _avg_total(sel: List[Dict[str, Any]]) -> Optional[float]:
    v = [t["total_eur"] for t in sel if t["total_eur"]]
    return round(sum(v) / len(v), 2) if v else None


def _score_range(sel: List[Dict[str, Any]]) -> Optional[Dict[str, float]]:
    v = [t["score"] for t in sel if t["score"] is not None]
    return {"min": min(v), "max": max(v), "n": len(v)} if v else None


def _styles(sel: List[Dict[str, Any]], w: np.ndarray, x: np.ndarray) -> List[Dict[str, Any]]:
    """Gruppi di budget simili (k-means, seme fisso). Per ognuno: quanti template, quanti ammessi, la ripartizione media."""
    seed = int(hashlib.sha256(("|".join(str(t["id"]) for t in sel)).encode()).hexdigest()[:8], 16)
    best = None
    for k in range(2, min(MAX_K, len(sel) // 3) + 1):
        labels, cent = kmeans(x, k, seed)
        s = silhouette(x, labels)
        if best is None or s > best[0] + 1e-9:
            best = (s, labels)
    if best is None or best[0] < 0.2:                        # gruppi poco separati: non si inventano stili
        return []
    labels = best[1]
    out = []
    for j in sorted(set(labels)):
        idx = [i for i, lb in enumerate(labels) if lb == j]
        cent = (x[idx] * w[idx][:, None]).sum(axis=0) / w[idx].sum()
        dom = SHARES[int(np.argmax(cent))]
        out.append({"name": f"Stile «{SHARE_LABEL[dom].lower()}»", "templates": len(idx), "wins": sum(1 for i in idx if sel[i]["outcome"] == "AMMESSO"),
                    "shares": {k: round(float(cent[i]), 4) for i, k in enumerate(SHARES)}})
    return sorted(out, key=lambda s: (-s["wins"], -s["templates"], s["name"]))


# ------------------------------------------------------------------------------------------------ scrittura
def _validate_common(data: Dict[str, Any]) -> Dict[str, Any]:
    ateco = str(data.get("ateco_code") or "").strip().replace(",", ".")
    if not re.fullmatch(r"\d{2}(\.\d{1,2}){0,2}", ateco):
        raise TemplateError("Il codice ATECO ha il formato 62.01 (o 62.01.00)")
    niche = niche_label(ateco)
    outcome = str(data.get("outcome") or "BOZZA").upper()
    if outcome not in OUTCOMES:
        raise TemplateError("Esito non valido: bozza, presentato, ammesso o non ammesso")
    score = data.get("score")
    if score not in (None, ""):
        try:
            score = float(score)
        except (TypeError, ValueError):
            raise TemplateError("Punteggio non valido") from None
        if not 0 <= score <= 1000:
            raise TemplateError("Punteggio non valido")
    else:
        score = None
    total = data.get("total_eur")
    total = float(total) if total not in (None, "") else None
    if total is not None and not 0 < total < 1e10:
        raise TemplateError("Importo totale non valido")
    return {"ateco_code": ateco, "ateco_division": niche["division"], "ateco_section": niche["section"], "outcome": outcome, "score": score, "total_eur": total,
            "company_size": (str(data.get("company_size") or "")[:20] or None), "region": (str(data.get("region") or "")[:40] or None),
            "note": str(data.get("note") or "")[:500], "shared": bool(data.get("shared"))}


def save_template(owner: str, data: Dict[str, Any], actor: Optional[str] = None) -> Dict[str, Any]:
    from app.core import bandi
    from app.core.ingestion import Ingestion
    bandi.ensure_seeded()                                   # i bandi curati entrano in archivio alla prima richiesta
    common = _validate_common(data)
    bando_id = str(data.get("bando_id") or "").strip()
    bando = Ingestion.get_bando(bando_id) if bando_id else None
    if bando is None:
        raise TemplateError("Scegli il bando a cui si riferisce il template (deve essere tra quelli in memoria)")
    shares = clean_shares(data.get("shares") or {})
    rec = recommend(owner, common["ateco_code"], bando_id)          # il consiglio che c'era prima di questo template: serve a misurare se l'algoritmo ci prende
    recommended = rec.get("recommended")
    distance = round(_distance(shares, recommended), 4) if recommended else None
    now = events.now_iso()
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO budget_templates (owner, shared, ateco_code, ateco_division, ateco_section, company_size, region, bando_id, bando_name, total_eur, shares, outcome, score, "
            "note, recommended, distance, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) RETURNING id",
            (owner, common["shared"], common["ateco_code"], common["ateco_division"], common["ateco_section"], common["company_size"], common["region"], bando_id, bando["name"],
             common["total_eur"], json.dumps(shares), common["outcome"], common["score"], common["note"], json.dumps(recommended) if recommended else None, distance, now, now))
        new_id = cur.fetchone()["id"]
    events.record("template.save", f"Template salvato: {niche_label(common['ateco_code'])['label']} · {bando['name'][:50]} · {OUTCOME_LABEL[common['outcome']]}", actor=actor or owner, bando_id=bando_id,
                  details={"template_id": new_id, "shared": common["shared"], "distance_from_recommendation": distance})
    with connect() as conn:
        row = conn.execute("SELECT * FROM budget_templates WHERE id=?", (new_id,)).fetchone()
    return _row(row)


def update_template(owner: str, template_id: int, data: Dict[str, Any], actor: Optional[str] = None) -> Dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM budget_templates WHERE id=? AND owner=?", (template_id, owner)).fetchone()
    if row is None:
        raise KeyError(template_id)
    cur = _row(row)
    merged = {"ateco_code": cur["ateco_code"], "outcome": cur["outcome"], "score": cur["score"], "total_eur": cur["total_eur"], "company_size": cur["company_size"],
              "region": cur["region"], "note": cur["note"], "shared": cur["shared"], **{k: v for k, v in data.items() if k in ("outcome", "score", "note", "shared", "total_eur")}}
    common = _validate_common(merged)
    shares = clean_shares(data["shares"]) if data.get("shares") else cur["shares"]
    with connect() as conn:
        conn.execute("UPDATE budget_templates SET outcome=?, score=?, note=?, shared=?, total_eur=?, shares=?, updated_at=? WHERE id=?",
                     (common["outcome"], common["score"], common["note"], common["shared"], common["total_eur"], json.dumps(shares), events.now_iso(), template_id))
        row = conn.execute("SELECT * FROM budget_templates WHERE id=?", (template_id,)).fetchone()
    events.record("template.update", f"Template {template_id} aggiornato: {OUTCOME_LABEL[common['outcome']]}", actor=actor or owner, bando_id=cur["bando_id"], details={"template_id": template_id})
    return _row(row)


def delete_template(owner: str, template_id: int, actor: Optional[str] = None) -> bool:
    with connect() as conn:
        cur = conn.execute("DELETE FROM budget_templates WHERE id=? AND owner=?", (template_id, owner))
        n = cur.rowcount
    if n:
        events.record("template.delete", f"Template {template_id} eliminato", actor=actor or owner, details={"template_id": template_id})
    return n > 0


# ------------------------------------------------------------------------------------------------ mappa delle nicchie e stato dell'apprendimento
def niche_map(owner: str) -> List[Dict[str, Any]]:
    """Per ogni nicchia (ATECO a 2 cifre): quanti template, quali bandi hanno scelto, con quale ripartizione media e quanti ammessi."""
    pool = _pool(owner)
    by: Dict[str, List[Dict[str, Any]]] = {}
    for t in pool:
        by.setdefault(t["ateco_division"], []).append(t)
    out = []
    for div, items in sorted(by.items()):
        bandi: Dict[str, List[Dict[str, Any]]] = {}
        for t in items:
            bandi.setdefault(t["bando_id"], []).append(t)
        rows = []
        for bid, ts in bandi.items():
            w = np.array([OUTCOME_WEIGHT[t["outcome"]] for t in ts])
            x = np.array([_vec(t["shares"]) for t in ts])
            mean = (x * w[:, None]).sum(axis=0) / w.sum()
            rows.append({"bando_id": bid, "bando_name": ts[0]["bando_name"], "templates": len(ts), "wins": sum(1 for t in ts if t["outcome"] == "AMMESSO"),
                         "submitted": sum(1 for t in ts if t["outcome"] in ("PRESENTATO", "AMMESSO", "NON_AMMESSO")),
                         "shares": {k: round(float(mean[i]), 4) for i, k in enumerate(SHARES)}, "regions": sorted({t["region"] for t in ts if t["region"]}),
                         "sizes": sorted({t["company_size"] for t in ts if t["company_size"]})})
        rows.sort(key=lambda r: (-r["wins"], -r["templates"], r["bando_name"]))
        out.append({"division": div, "section": items[0]["ateco_section"], "niche": niche_label(items[0]["ateco_code"])["label"], "templates": len(items),
                    "wins": sum(1 for t in items if t["outcome"] == "AMMESSO"), "bandi": rows})
    out.sort(key=lambda n: (-n["templates"], n["division"]))
    return out


def learning_status(owner: str) -> Dict[str, Any]:
    """Come sta imparando l'algoritmo: quanti template, con che esiti, e se i budget vicini al consiglio vincono più spesso."""
    pool = _pool(owner)
    mine = [t for t in pool if t["owner"] == owner]
    outcomes = {o: sum(1 for t in pool if t["outcome"] == o) for o in OUTCOMES}
    judged = [t for t in pool if t["outcome"] in ("AMMESSO", "NON_AMMESSO") and t["distance"] is not None]
    close = [t for t in judged if t["distance"] <= CLOSE_DISTANCE]
    far = [t for t in judged if t["distance"] > CLOSE_DISTANCE]
    feedback: Dict[str, Any] = {"judged": len(judged), "close": len(close), "far": len(far), "enough": len(close) >= MIN_FEEDBACK and len(far) >= MIN_FEEDBACK}
    if feedback["enough"]:
        rate = lambda xs: round(100 * sum(1 for t in xs if t["outcome"] == "AMMESSO") / len(xs), 1)  # noqa: E731
        feedback.update({"close_win_rate_pct": rate(close), "far_win_rate_pct": rate(far)})
        feedback["message"] = (f"I budget vicini al consiglio (scarto fino al {CLOSE_DISTANCE * 100:.0f}%) sono stati ammessi nel {_n(feedback['close_win_rate_pct'])}% dei casi, "
                               f"gli altri nel {_n(feedback['far_win_rate_pct'])}%.")
    else:
        feedback["message"] = (f"Servono almeno {MIN_FEEDBACK} esiti noti sia tra i budget vicini al consiglio sia tra gli altri per dire se seguire il consiglio conviene: "
                               f"oggi {len(close)} vicini e {len(far)} lontani.")
    return {"templates_mine": len(mine), "templates_pool": len(pool), "templates_shared_by_others": sum(1 for t in pool if t["owner"] != owner), "outcomes": outcomes,
            "pool_hash": _pool_hash(pool), "feedback": feedback, "niches": len({t["ateco_division"] for t in pool}), "bandi": len({t["bando_id"] for t in pool})}
