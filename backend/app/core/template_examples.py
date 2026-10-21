"""Template di esempio nel motore collettivo: 48 budget costruiti sulle regole vere dei bandi in memoria e verificati con quelle stesse regole.

**Cosa sono.** Servono a far partire l'algoritmo dei template quando i budget reali dello studio sono pochi (partenza a freddo). Per ogni bando con regole pubblicate si
costruiscono, per nicchie ATECO plausibili, ripartizioni del budget in categorie (personale, beni, consulenze…) e si **verificano** con le regole di quota del bando:
- categorie ammesse (una quota in una categoria non ammessa → il budget **non è conforme**: nel motore la voce sarebbe respinta);
- tetto percentuale sulle consulenze (superato → **conforme con riduzioni**: il motore taglia l'eccedenza);
- spese generali a forfait (se non coincidono con il forfait → **conforme con riduzioni**);
- altrimenti **conforme**.
La verifica porta con sé la versione delle regole (hash): se il bando cambia, l'esempio si rifà da solo.

**Cosa NON sono.** Non sono budget di aziende reali e **non hanno un esito di bando**: «conforme» vuol dire che rispetta le regole di quota di quel bando, non che il bando è stato vinto.
Per questo sono marcati ``origin = 'ESEMPIO'`` ovunque, pesano la metà dei template reali, non contano come «ammessi» né nei confronti tra budget vicini e lontani dal consiglio, e **escono dal calcolo**
appena nel gruppo ci sono ``EXAMPLES_FADE`` template reali. Il personale non è verificato riga per riga (servirebbero le tabelle ufficiali dei contratti): è una quota dichiarata.
Si possono eliminare tutti dal Quartier Generale. Gli esempi sono deterministici: stesso bando, stesse regole → stessi esempi.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
from typing import Any, Dict, List, Optional, Tuple

from app.core import db, events
from app.core.db import connect

EXAMPLE_OWNER = "quanto:esempi"
CATEGORY_OF = {"personnel_pct": "PERSONNEL", "assets_pct": "CAPITAL_ASSETS", "consulting_pct": "CONSULTING", "research_pct": "CONSULTING", "overhead_pct": "OVERHEAD",
               "training_pct": "TRAINING", "communication_pct": "OVERHEAD", "other_pct": "OTHER"}
OUTCOME_FOR = {"CONFORME": "AMMESSO", "RIDUZIONI": "PRESENTATO", "NON_CONFORME": "NON_AMMESSO"}

# Per ogni bando curato: quante ripartizioni, per quali nicchie (divisioni ATECO e codici tipici), dimensione e regione, e come si distribuisce la spesa «normale» del progetto
# (intervalli per quota). Sono ipotesi di costruzione, dichiarate come tali: non descrivono aziende reali.
PROFILES: Dict[str, Dict[str, Any]] = {
    "HORIZON-EUROPE-MGA": {"count": 9, "sizes": ["piccola", "media"], "regions": [None], "total": (400_000, 2_500_000),
                           "niches": [("72.19", 3), ("62.01", 3), ("26.51", 3)],
                           "ranges": {"personnel_pct": (0.60, 0.74), "assets_pct": (0.03, 0.08), "consulting_pct": (0.04, 0.12), "research_pct": (0.04, 0.12), "training_pct": (0.0, 0.01)}},
    "FVG-VALIDAZIONE-TRL-2026": {"count": 9, "sizes": ["micro", "piccola"], "regions": ["Friuli-Venezia Giulia"], "total": (60_000, 400_000),
                                 "niches": [("62.01", 3), ("28.29", 3), ("26.51", 3)],
                                 "ranges": {"personnel_pct": (0.30, 0.45), "assets_pct": (0.10, 0.25), "consulting_pct": (0.25, 0.42)}},
    "SMART-START-ITALIA": {"count": 9, "sizes": ["micro", "piccola"], "regions": [None], "total": (150_000, 1_500_000),
                           "niches": [("62.01", 3), ("63.11", 3), ("26.20", 3)],
                           "ranges": {"assets_pct": (0.40, 0.58), "personnel_pct": (0.18, 0.30), "consulting_pct": (0.14, 0.26)}},
    "SIMEST-FONDO-394-PNRR": {"count": 9, "sizes": ["piccola", "media"], "regions": [None], "total": (100_000, 800_000),
                              "niches": [("10.39", 3), ("14.13", 3), ("28.29", 3)],
                              "ranges": {"assets_pct": (0.93, 0.99), "consulting_pct": (0.01, 0.045)}},
    "IPERAMMORTAMENTO-2026": {"count": 4, "sizes": ["piccola", "media"], "regions": [None], "total": (150_000, 1_800_000), "niches": [("25.62", 4)], "ranges": {"assets_pct": (1.0, 1.0)}},
    "NUOVA-SABATINI": {"count": 4, "sizes": ["micro", "piccola"], "regions": [None], "total": (40_000, 500_000), "niches": [("28.29", 4)], "ranges": {"assets_pct": (1.0, 1.0)}},
    "INVESTIMENTI-SOSTENIBILI-4.0-2026": {"count": 4, "sizes": ["piccola", "media"], "regions": [None], "total": (200_000, 2_000_000), "niches": [("22.29", 4)], "ranges": {"assets_pct": (1.0, 1.0)}},
}
# Non tutti gli esempi rispettano le regole: servono anche i casi che il motore taglierebbe o respingerebbe, altrimenti l'algoritmo non impara cosa evitare.
VARIANT_ODDS = (("ok", 0.62), ("tetto", 0.22), ("categoria", 0.16))


class ExampleError(ValueError):
    pass


def _rng(key: str) -> random.Random:
    return random.Random(int(hashlib.sha256(key.encode()).hexdigest()[:12], 16))


def verify_shares(rules: Dict[str, Any], shares: Dict[str, float]) -> Dict[str, Any]:
    """Verifica una ripartizione con le regole di quota del bando. Restituisce l'esito e ogni controllo con il suo motivo."""
    checks: List[Dict[str, Any]] = []
    eligible = rules.get("eligible_categories") or []
    flat = rules.get("overhead_flat_rate_pct")
    outcome = "CONFORME"

    def add(rule: str, ok: bool, detail: str, kind: str) -> None:
        nonlocal outcome
        checks.append({"rule": rule, "ok": ok, "detail": detail})
        if not ok:
            outcome = "NON_CONFORME" if kind == "CATEGORIA" else (outcome if outcome == "NON_CONFORME" else "RIDUZIONI")

    if eligible:
        bad = {k: v for k, v in shares.items() if v > 0.0005 and CATEGORY_OF[k] not in eligible and not (CATEGORY_OF[k] == "OVERHEAD" and flat)}
        add("categorie ammesse", not bad, ("tutte le quote sono in categorie ammesse" if not bad else "quote in categorie non ammesse: " + ", ".join(f"{k[:-4]} {v * 100:.1f}%" for k, v in bad.items())), "CATEGORIA")
    cap = rules.get("max_consulting_percentage")
    if cap is not None:
        consulting = sum(v for k, v in shares.items() if CATEGORY_OF[k] == "CONSULTING")
        add("tetto sulle consulenze", consulting <= float(cap) + 0.0005, f"consulenze {consulting * 100:.1f}% contro un tetto del {float(cap) * 100:.0f}%", "TETTO")
    if flat is not None:
        have = sum(v for k, v in shares.items() if CATEGORY_OF[k] == "OVERHEAD")
        if rules.get("overhead_flat_base") == "PERSONNEL":                         # forfait calcolato sul solo personale
            want, base = float(flat) * shares.get("personnel_pct", 0.0), "sul personale"
        else:                                                                      # forfait sui costi diretti: spese generali = forfait / (1 + forfait) del totale
            want, base = float(flat) / (1 + float(flat)), "sui costi diretti"
        add("spese generali a forfait", abs(have - want) <= 0.01, f"spese generali {have * 100:.1f}% contro il {want * 100:.1f}% che dà un forfait del {float(flat) * 100:.0f}% {base}", "TETTO")
    for key, label, share_key in (("max_overhead_percentage", "tetto sulle spese generali", "overhead_pct"), ("max_communication_pct", "tetto sulla comunicazione", "communication_pct")):
        v = rules.get(key)
        if v is not None:
            have = shares.get(share_key, 0.0)
            add(label, have <= float(v) + 0.0005, f"{have * 100:.1f}% contro un tetto del {float(v) * 100:.0f}%", "TETTO")
    if not checks:
        checks.append({"rule": "nessuna regola di quota", "ok": True, "detail": "il bando non dichiara tetti o categorie: nulla da verificare sulla struttura"})
    return {"outcome": outcome, "checks": checks}


def _draw_shares(profile: Dict[str, Any], rules: Dict[str, Any], variant: str, rng: random.Random) -> Dict[str, float]:
    raw = {k: rng.uniform(lo, hi) for k, (lo, hi) in profile["ranges"].items()}
    flat = rules.get("overhead_flat_rate_pct")
    if flat is not None:                                          # il forfait sulle spese generali fa parte della regola: le spese generali sono la sua quota del totale
        base = raw.get("personnel_pct", 0.0) if rules.get("overhead_flat_base") == "PERSONNEL" else sum(raw.values())
        raw["overhead_pct"] = base * float(flat)
        if variant == "tetto":                                    # lo sbaglio tipico: spese generali scritte a stima, non a forfait
            raw["overhead_pct"] *= rng.uniform(1.4, 1.9) if rng.random() < 0.6 else rng.uniform(0.3, 0.6)
    cap = rules.get("max_consulting_percentage")
    if variant == "tetto" and cap is not None:
        raw["consulting_pct"] = max(raw.get("consulting_pct", 0.0), 0.0) + rng.uniform(0.05, 0.15) * (1 if float(cap) < 0.2 else 0.5)
    if variant == "categoria":
        eligible = rules.get("eligible_categories") or []
        banned = [k for k, c in CATEGORY_OF.items() if eligible and c not in eligible and c != "OVERHEAD"]
        if banned:
            raw[rng.choice(banned)] = rng.uniform(0.05, 0.14)
    total = sum(raw.values()) or 1.0
    return {k: round(v / total, 6) for k, v in raw.items()}


def build_examples(rules_by_bando: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Gli esempi, in modo deterministico (stesse regole → stessi esempi). ``rules_by_bando``: id → {name, rules (dict del GrantRuleSet), hash}."""
    out: List[Dict[str, Any]] = []
    for bando_id, profile in PROFILES.items():
        info = rules_by_bando.get(bando_id)
        if not info:
            continue
        rules = info["rules"]
        k = 0
        for ateco, n in profile["niches"]:
            for i in range(n):
                key = f"{bando_id}|{ateco}|{i}"
                rng = _rng(key)
                roll, variant, acc = rng.random(), "ok", 0.0
                for name, p in VARIANT_ODDS:
                    acc += p
                    if roll <= acc:
                        variant = name
                        break
                if k == 2:                                                      # ogni bando ha almeno un caso che il motore taglierebbe e uno che respingerebbe, dove le regole lo permettono
                    variant = "tetto" if (rules.get("max_consulting_percentage") is not None or rules.get("overhead_flat_rate_pct") is not None) else "categoria"
                elif k == 5 and rules.get("eligible_categories"):
                    variant = "categoria"
                shares = _draw_shares(profile, rules, variant, rng)
                ver = verify_shares(rules, shares)
                lo, hi = profile["total"]
                total = round(math.exp(rng.uniform(math.log(lo), math.log(hi))) / 1000) * 1000
                out.append({"example_key": key, "bando_id": bando_id, "bando_name": info["name"], "ateco_code": ateco, "shares": shares, "total_eur": float(total),
                            "company_size": rng.choice(profile["sizes"]), "region": rng.choice(profile["regions"]), "outcome": OUTCOME_FOR[ver["outcome"]],
                            "verification": {"method": "quote_vs_regole_del_bando", "rule_version_hash": info["hash"], "result": ver["outcome"], "checks": ver["checks"],
                                             "personnel": "quota dichiarata, non verificata riga per riga (servono le tabelle ufficiali dei contratti)"},
                            "note": "Esempio costruito sulle regole del bando e verificato con esse: non è un budget reale e non ha un esito di bando."})
                k += 1
    return out


def _rules_by_bando() -> Dict[str, Dict[str, Any]]:
    from app.core import bandi
    from app.core.ingestion import Ingestion
    bandi.ensure_seeded()
    out: Dict[str, Dict[str, Any]] = {}
    for bando_id in PROFILES:
        bando = Ingestion.get_bando(bando_id)
        rule_set, _missing = Ingestion.build_rule_set(bando_id)
        if bando is None or rule_set is None:
            continue
        d = rule_set.model_dump(mode="json")
        out[bando_id] = {"name": bando["name"], "rules": d, "hash": d.get("rule_version_hash") or ""}
    return out


def seed(actor: str = "sistema") -> Dict[str, int]:
    """Inserisce gli esempi mancanti e rifà quelli le cui regole sono cambiate. Idempotente."""
    from app.core import template_learning as tl
    ex = build_examples(_rules_by_bando())
    created = refreshed = 0
    now = events.now_iso()
    with connect() as conn:
        conn.lock(7_419_104)
        have = {r["example_key"]: r["verification"] for r in conn.execute("SELECT example_key, verification FROM budget_templates WHERE origin='ESEMPIO'").fetchall()}
        for e in ex:
            old = json.loads(have[e["example_key"]]).get("rule_version_hash") if e["example_key"] in have and have[e["example_key"]] else None
            if e["example_key"] in have:
                if old == e["verification"]["rule_version_hash"]:
                    continue
                conn.execute("DELETE FROM budget_templates WHERE example_key=?", (e["example_key"],))
                refreshed += 1
            else:
                created += 1
            niche = tl.niche_label(e["ateco_code"])
            conn.execute(
                "INSERT INTO budget_templates (owner, shared, ateco_code, ateco_division, ateco_section, company_size, region, bando_id, bando_name, total_eur, shares, outcome, score, note, "
                "created_at, updated_at, origin, verification, example_key) VALUES (?,TRUE,?,?,?,?,?,?,?,?,?,?,NULL,?,?,?,'ESEMPIO',?,?)",
                (EXAMPLE_OWNER, e["ateco_code"], niche["division"], niche["section"], e["company_size"], e["region"], e["bando_id"], e["bando_name"], e["total_eur"], json.dumps(e["shares"]),
                 e["outcome"], e["note"], now, now, json.dumps(e["verification"]), e["example_key"]))
    if created or refreshed:
        events.record("template.examples", f"Esempi del motore collettivo: {created} nuovi, {refreshed} rifatti per regole cambiate", actor=actor, details={"created": created, "refreshed": refreshed})
    return {"created": created, "refreshed": refreshed, "total": len(ex)}


def remove_all(actor: str = "sistema") -> int:
    with connect() as conn:
        n = conn.execute("DELETE FROM budget_templates WHERE origin='ESEMPIO'").rowcount
    events.record("template.examples_off", f"Esempi del motore collettivo eliminati: {n}", actor=actor)
    return n


_DONE: Dict[str, Optional[int]] = {"generation": None}


def enabled() -> bool:
    return os.getenv("QUANTO_SEED_TEMPLATES", "1").strip().lower() not in ("0", "false", "no", "")


def ensure() -> None:
    """Prima volta che il motore collettivo lavora su questo database: gli esempi ci sono (a meno che il titolare li abbia disattivati). Una volta sola per database."""
    if not enabled() or _DONE["generation"] == db.GENERATION:
        return
    try:
        with connect() as conn:
            last = conn.execute("SELECT op FROM events WHERE op IN ('template.examples', 'template.examples_off') ORDER BY id DESC LIMIT 1").fetchone()
            if last is not None and last["op"] == "template.examples_off":
                _DONE["generation"] = db.GENERATION                      # il titolare li ha tolti apposta: non si rimettono da soli
                return
        seed("sistema")
        _DONE["generation"] = db.GENERATION
    except Exception:                                                    # gli esempi sono un aiuto: se qualcosa va storto il motore lavora comunque sui template reali
        _DONE["generation"] = db.GENERATION
