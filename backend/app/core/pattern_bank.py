"""Banca dati dei pattern vincenti e archetipi per clustering (Moduli 5 e 6).

Nessun archetipo è scritto nel codice: i budget storici (graduatorie pubbliche, dataset UE, dati del pilota con consenso) si
IMPORTANO da file, con la fonte; gli archetipi si CALCOLANO con k-means (k-means++ con seme fisso: stesso dataset, stessi archetipi).
Con pochi dati non si finge un clustering: sotto ``MIN_FOR_CLUSTERING`` budget per categoria c'è un solo archetipo (la media) dichiarato
come tale. Senza dati per la categoria il confronto non parte, e lo dice.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.core import events
from app.core.db import connect

SHARES = ("personnel_pct", "assets_pct", "consulting_pct", "overhead_pct", "training_pct", "communication_pct")
AMOUNTS = tuple(s.replace("_pct", "_eur") for s in SHARES)
MIN_FOR_CLUSTERING = 6
MAX_K = 6
LABEL = {"personnel_pct": "OCCUPAZIONALE", "assets_pct": "TECNOLOGICA", "consulting_pct": "CONSULENZIALE", "training_pct": "FORMATIVA",
         "communication_pct": "COMUNICATIVA", "overhead_pct": "GESTIONALE"}
SYN = {"categoria": "bando_category", "fonte": "source", "anno": "year", "totale": "total_eur", "punteggio": "score", "indirizzo": "source_url"}


class PatternError(ValueError):
    def __init__(self, message: str, errors: Optional[List[Dict[str, Any]]] = None):
        super().__init__(message)
        self.errors = errors or []


def _num(v: Any) -> Optional[float]:
    if v is None or str(v).strip() == "":
        return None
    t = str(v).strip().replace("%", "").replace("€", "").replace(" ", "")
    t = t.replace(".", "").replace(",", ".") if "," in t else t
    return float(t)


# ------------------------------------------------------------------------------------------------ importazione
def parse_budgets(filename: str, data: bytes) -> List[Dict[str, Any]]:
    """CSV (; o ,) con una riga per budget storico. Le quote si scrivono in % (58) o frazione (0,58); in alternativa gli importi (personnel_eur…)."""
    if not filename.lower().endswith((".csv", ".txt")):
        raise PatternError("Usa un file .csv")
    text = data.decode("utf-8-sig", errors="replace")
    first = text.splitlines()[0] if text.strip() else ""
    rows = list(csv.DictReader(io.StringIO(text), delimiter=";" if first.count(";") >= first.count(",") else ","))
    if not rows:
        raise PatternError("Il file non contiene righe")
    out, errors = [], []
    for i, raw in enumerate(rows, 2):
        r = {SYN.get(k.strip().lower(), k.strip().lower()): v for k, v in raw.items() if k}
        try:
            cat = (r.get("bando_category") or "").strip().upper()
            if not cat:
                raise ValueError("manca la categoria del bando (bando_category)")
            src = (r.get("source") or "").strip()
            if not src:
                raise ValueError("manca la fonte del dato (source): senza fonte un budget non entra nella banca dati")
            shares = {k: _num(r.get(k)) for k in SHARES}
            amounts = {k: _num(r.get(k)) for k in AMOUNTS}
            if any(v is not None for v in shares.values()):
                vals = {k: (v or 0.0) for k, v in shares.items()}
                if sum(vals.values()) > 1.5:                                       # scritte in percentuale
                    vals = {k: v / 100 for k, v in vals.items()}
            elif any(v is not None for v in amounts.values()):
                tot = sum(v or 0.0 for v in amounts.values())
                if tot <= 0:
                    raise ValueError("gli importi sommano zero")
                vals = {k.replace("_eur", "_pct"): (v or 0.0) / tot for k, v in amounts.items()}
            else:
                raise ValueError("mancano le quote di spesa (…_pct) o gli importi (…_eur)")
            if any(v < 0 for v in vals.values()) or abs(sum(vals.values()) - 1) > 0.02:
                raise ValueError(f"le quote devono sommare 100% (sommano {sum(vals.values()) * 100:.1f}%): record incompleto, scartato")
            total = _num(r.get("total_eur"))
            score = _num(r.get("score"))
            year = int(float(r["year"])) if r.get("year") not in (None, "") else None
            out.append({"bando_category": cat, "source": src, "source_url": (r.get("source_url") or None), "year": year, "total_eur": total, "score": score, **vals})
        except (ValueError, TypeError) as exc:
            errors.append({"line": i, "error": str(exc)})
    if errors:
        raise PatternError(f"{len(errors)} righe non valide: nulla è stato salvato", errors)
    return out


def import_budgets(rows: List[Dict[str, Any]], actor: str) -> Dict[str, Any]:
    cats = sorted({r["bando_category"] for r in rows})
    with connect() as conn:
        conn.executemany(
            "INSERT INTO pattern_budgets (bando_category, source, source_url, year, total_eur, score, personnel_pct, assets_pct, consulting_pct, overhead_pct, training_pct, "
            "communication_pct, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [(r["bando_category"], r["source"], r["source_url"], r["year"], r["total_eur"], r["score"], *[r[s] for s in SHARES], actor, events.now_iso()) for r in rows])
    result = {c: refresh_archetypes(c) for c in cats}
    events.record("pattern.import", f"Importati {len(rows)} budget storici in {len(cats)} categorie", actor=actor, details={"categories": cats})
    return {"imported": len(rows), "categories": result}


# ------------------------------------------------------------------------------------------------ clustering
def kmeans(x: np.ndarray, k: int, seed: int, iters: int = 100) -> Tuple[np.ndarray, np.ndarray]:
    """k-means con inizializzazione k-means++ e seme fisso (deterministico). Restituisce (etichette, centroidi)."""
    rng = np.random.default_rng(seed)
    n = len(x)
    centers = [x[rng.integers(n)]]
    for _ in range(1, k):
        d2 = np.min([np.sum((x - c) ** 2, axis=1) for c in centers], axis=0)
        p = d2 / d2.sum() if d2.sum() > 0 else np.full(n, 1 / n)
        centers.append(x[rng.choice(n, p=p)])
    c = np.array(centers)
    labels = np.zeros(n, dtype=int)
    for _ in range(iters):
        d = np.sum((x[:, None, :] - c[None, :, :]) ** 2, axis=2)
        new = d.argmin(axis=1)
        for j in range(k):
            members = x[new == j]
            if len(members):
                c[j] = members.mean(axis=0)
        if np.array_equal(new, labels) and _ > 0:
            break
        labels = new
    return labels, c


def silhouette(x: np.ndarray, labels: np.ndarray) -> float:
    n = len(x)
    if len(set(labels)) < 2:
        return -1.0
    d = np.sqrt(np.sum((x[:, None, :] - x[None, :, :]) ** 2, axis=2))
    s = []
    for i in range(n):
        same = labels == labels[i]
        a = d[i][same & (np.arange(n) != i)].mean() if same.sum() > 1 else 0.0
        b = min(d[i][labels == j].mean() for j in set(labels) if j != labels[i])
        s.append(0.0 if max(a, b) == 0 else (b - a) / max(a, b))
    return float(np.mean(s))


def _name(centroid: np.ndarray, used: set) -> str:
    dom = SHARES[int(np.argmax(centroid))]
    order = sorted(centroid, reverse=True)
    base = "TRAZIONE_BILANCIATA" if order[0] - order[1] < 0.08 else f"TRAZIONE_{LABEL[dom]}"
    name, i = base, 2
    while name in used:
        name, i = f"{base}_{i}", i + 1
    used.add(name)
    return name


def refresh_archetypes(category: str) -> Dict[str, Any]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM pattern_budgets WHERE bando_category=? ORDER BY id", (category,)).fetchall()
        conn.execute("DELETE FROM pattern_archetypes WHERE bando_category=?", (category,))
        if not rows:
            return {"budgets": 0, "archetypes": 0}
        x = np.array([[float(r[s]) for s in SHARES] for r in rows])
        scores = [float(r["score"]) if r["score"] is not None else None for r in rows]
        seed = int(hashlib.sha256((category + str(len(rows))).encode()).hexdigest()[:8], 16)
        if len(rows) >= MIN_FOR_CLUSTERING:
            best = None
            for k in range(2, min(MAX_K, len(rows) // 3) + 1):
                labels, cent = kmeans(x, k, seed)
                sil = silhouette(x, labels)
                if best is None or sil > best[0] + 1e-9:
                    best = (sil, k, labels, cent)
            sil, k, labels, cent = best if best else (None, 1, np.zeros(len(rows), dtype=int), x.mean(axis=0, keepdims=True))
            method = f"k-means k={k} (silhouette {sil:.2f})" if best else "media (dati insufficienti per separare gruppi)"
        else:
            k, labels, cent, sil = 1, np.zeros(len(rows), dtype=int), x.mean(axis=0, keepdims=True), None
            method = f"media di {len(rows)} budget: servono almeno {MIN_FOR_CLUSTERING} per fare il clustering"
        used: set = set()
        for j in range(len(cent)):
            idx = np.where(labels == j)[0]
            if len(idx) == 0:
                continue
            sc = [scores[i] for i in idx if scores[i] is not None]
            centroid = x[idx].mean(axis=0)
            conn.execute("INSERT INTO pattern_archetypes (bando_category, label, centroid, members, score_min, score_max, method, computed_at) VALUES (?,?,?,?,?,?,?,?)",
                         (category, _name(centroid, used), json.dumps(dict(zip(SHARES, [float(v) for v in centroid]))), len(idx), min(sc) if sc else None, max(sc) if sc else None, method, events.now_iso()))
    return {"budgets": len(rows), "archetypes": len(cent), "method": method}


# ------------------------------------------------------------------------------------------------ interrogazioni
def categories() -> List[Dict[str, Any]]:
    with connect() as conn:
        return [{"bando_category": r["bando_category"], "budgets": r["n"], "archetypes": r["a"]} for r in conn.execute(
            "SELECT b.bando_category, COUNT(*) n, (SELECT COUNT(*) FROM pattern_archetypes a WHERE a.bando_category=b.bando_category) a FROM pattern_budgets b GROUP BY b.bando_category ORDER BY 1").fetchall()]


def list_budgets(category: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM pattern_budgets " + ("WHERE bando_category=? " if category else "") + "ORDER BY id DESC LIMIT ?",
                            ((category, limit) if category else (limit,))).fetchall()
    return [{k: (float(v) if hasattr(v, "as_tuple") else v) for k, v in dict(r).items()} for r in rows]


def _cos(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return 0.0 if na == 0 or nb == 0 else float(a @ b / (na * nb))


def match(category: str, draft: Dict[str, float], nearest: int = 8, cap_notes: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """Confronto del budget bozza con gli archetipi e con i budget storici più simili (Modulo 6.3)."""
    category = category.strip().upper()
    vec = np.array([max(0.0, float(draft.get(s, 0.0))) for s in SHARES])
    if vec.sum() <= 0:
        raise PatternError("La somma delle quote del budget bozza deve essere positiva")
    vec = vec / vec.sum()
    with connect() as conn:
        arch = conn.execute("SELECT * FROM pattern_archetypes WHERE bando_category=? ORDER BY label", (category,)).fetchall()
        budgets = conn.execute("SELECT * FROM pattern_budgets WHERE bando_category=?", (category,)).fetchall()
    if not arch:
        known = [c["bando_category"] for c in categories()]
        raise PatternError(f"La banca dati non ha budget storici per la categoria «{category}». " +
                           (f"Categorie disponibili: {', '.join(known)}." if known else "La banca dati è vuota: importa le graduatorie (Quartier Generale)."))
    scored = []
    for a in arch:
        cen = json.loads(a["centroid"])
        scored.append((_cos(vec, np.array([cen[s] for s in SHARES])), a, cen))
    scored.sort(key=lambda t: (-round(t[0], 12), t[1]["label"]))          # a parità, il nome minore (determinismo)
    sim, best, cen = scored[0]
    dev = {s: float(vec[i] - cen[s]) for i, s in enumerate(SHARES)}
    main = max(SHARES, key=lambda s: (abs(dev[s]), s))
    note = None
    if cap_notes and main in cap_notes and vec[SHARES.index(main)] > cap_notes[main]:
        note = f"Sopra il tetto di bando del {round(cap_notes[main] * 100)}%"
    near = sorted(budgets, key=lambda r: -_cos(vec, np.array([float(r[s]) for s in SHARES])))[:max(5, min(10, nearest))]
    return {
        "closest_archetype": best["label"], "similarity_score": round(sim, 2), "archetype_averages": {s: round(cen[s], 4) for s in SHARES},
        "main_deviation": {"category": main, "deviation_points": round(dev[main], 4), "note": note},
        "deviations_pp": {s: round(dev[s] * 100, 1) for s in SHARES},
        "archetype": {"members": best["members"], "method": best["method"], "score_min": float(best["score_min"]) if best["score_min"] is not None else None,
                      "score_max": float(best["score_max"]) if best["score_max"] is not None else None},
        "nearest_budgets": [{"source": r["source"], "source_url": r["source_url"], "year": r["year"], "score": float(r["score"]) if r["score"] is not None else None,
                             "similarity": round(_cos(vec, np.array([float(r[s]) for s in SHARES])), 3), "shares": {s: round(float(r[s]), 4) for s in SHARES}} for r in near],
        "data_points": len(budgets),
        "recommendation": (f"Il budget proposto somiglia per {round(sim * 100, 1)}% all'archetipo «{best['label']}» ({best['members']} budget storici). "
                           f"Principale scostamento: {main} {'+' if dev[main] > 0 else ''}{round(dev[main] * 100, 1)} punti percentuali rispetto alla media dell'archetipo. "
                           "È un'indicazione statistica sulla struttura della spesa, non una previsione di esito."),
    }
