"""Pattern matching per similarità del coseno rispetto agli archetipi di budget vincenti (Modulo 6).

Nota metodologica: i vettori di quote sono non negativi, quindi il coseno è strutturalmente alto
(>0.7) anche per budget molto diversi. Lo score va letto insieme allo scostamento principale in
punti percentuali, che è il segnale operativo.
"""
from __future__ import annotations

import math
from typing import Dict

from app.models.schemas import MainDeviation, PatternMatchResponse

CATEGORIES = ("personnel_pct", "assets_pct", "consulting_pct", "overhead_pct")

# Fingerprint illustrativi (Fonte A/B): vanno sostituiti dal clustering su graduatorie reali (Modulo 5).
HISTORICAL_ARCHETYPES_DATABASE: Dict[str, Dict[str, float]] = {
    "TRAZIONE_OCCUPAZIONALE": {"personnel_pct": 0.61, "assets_pct": 0.15, "consulting_pct": 0.18, "overhead_pct": 0.06},
    "TRAZIONE_TECNOLOGICA": {"personnel_pct": 0.25, "assets_pct": 0.55, "consulting_pct": 0.15, "overhead_pct": 0.05},
    "TRAZIONE_CONSULENZIALE": {"personnel_pct": 0.30, "assets_pct": 0.10, "consulting_pct": 0.50, "overhead_pct": 0.10},
    "TRAZIONE_BILANCIATA": {"personnel_pct": 0.45, "assets_pct": 0.30, "consulting_pct": 0.18, "overhead_pct": 0.07},
}


class PatternMatchingEngine:
    @staticmethod
    def _cosine_similarity(v1: Dict[str, float], v2: Dict[str, float]) -> float:
        dot = sum(v1.get(c, 0.0) * v2.get(c, 0.0) for c in CATEGORIES)
        m1 = math.sqrt(sum(v1.get(c, 0.0) ** 2 for c in CATEGORIES))
        m2 = math.sqrt(sum(v2.get(c, 0.0) ** 2 for c in CATEGORIES))
        return 0.0 if m1 == 0.0 or m2 == 0.0 else dot / (m1 * m2)

    @classmethod
    def analyze_budget_pattern(cls, draft_budget: Dict[str, float]) -> PatternMatchResponse:
        total = sum(draft_budget.get(c, 0.0) for c in CATEGORIES)
        if total <= 0:
            raise ValueError("La somma delle quote del budget bozza deve essere positiva")
        draft = {c: draft_budget.get(c, 0.0) / total for c in CATEGORIES}

        # Parità di similarità: vince l'archetipo con nome minore, per determinismo.
        best_name, best_sim = min(
            ((name, cls._cosine_similarity(draft, vec)) for name, vec in HISTORICAL_ARCHETYPES_DATABASE.items()),
            key=lambda t: (-round(t[1], 12), t[0]),
        )
        best = HISTORICAL_ARCHETYPES_DATABASE[best_name]

        dev_cat = max(CATEGORIES, key=lambda c: (abs(draft[c] - best[c]), c))
        dev_pts = round((draft[dev_cat] - best[dev_cat]) * 100.0, 1)
        sign = "+" if dev_pts > 0 else ""
        recommendation = (
            f"Il budget proposto presenta una similarità del {round(best_sim * 100, 1)}% "
            f"rispetto all'archetipo storico '{best_name}'. "
            f"Principale scostamento rilevato nella categoria '{dev_cat}': {sign}{dev_pts} punti percentuali "
            f"rispetto alla media dei progetti vincenti."
        )
        return PatternMatchResponse(
            closest_archetype=best_name,
            similarity_score=round(best_sim, 2),
            archetype_averages=best,
            main_deviation=MainDeviation(category=dev_cat, deviation_points=dev_pts),
            recommendation=recommendation,
        )
