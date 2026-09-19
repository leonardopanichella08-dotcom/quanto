import pytest

from app.core.budget_service import validate_budget
from app.core.numeric_validator import validate_text_against_payload
from app.core.pattern_engine import PatternMatchingEngine
from app.core.renderer import budget_context, eur, render_with_grounding, static_budget_summary
from app.models.schemas import BudgetValidationRequest

PAYLOAD = {"approved": 26282.70, "requested": 65113.12, "bando": "TRANSIZIONE-5.0-2026", "root": "0x7ae2ce9406b9b0f70000"}


def test_validator_accepts_italian_and_plain_formats():
    assert validate_text_against_payload("Ammessi 26.282,70 € su 65113.12 € per TRANSIZIONE-5.0-2026", PAYLOAD).ok


@pytest.mark.parametrize("text", [
    "Ammessi 26.283,00 €",             # arrotondamento diverso
    "Ammessi 27.000 €",                # cifra inventata
    "Risparmio del 12% sul totale",    # percentuale non tracciabile
    "Bando TRANSIZIONE-5.0-2027",      # identificativo alterato
])
def test_validator_rejects_untraceable_numbers(text):
    assert not validate_text_against_payload(text, PAYLOAD).ok


def test_validator_allows_hash_prefix_of_known_root():
    assert validate_text_against_payload("Root 0x7ae2ce9406b9…", PAYLOAD).ok


class FakeLLM:
    def __init__(self, text=None, boom=False):
        self.text, self.boom, self.seen = text, boom, None

    def complete(self, system, context_json):
        self.seen = context_json
        if self.boom:
            raise TimeoutError("provider down")
        return self.text


def _ctx(seed_items, rules):
    resp = validate_budget(BudgetValidationRequest(project_id="P", grant_rules=rules, cost_items=seed_items))
    ctx = budget_context({**resp.model_dump(), "bando_name": rules.bando_name, "items": [i.model_dump(mode="json") for i in resp.items]})
    return resp, ctx


def test_llm_text_used_only_when_numbers_match(seed_items, rules):
    _, ctx = _ctx(seed_items, rules)
    good = FakeLLM(f"Ammessi {eur(ctx['total_approved_eur'])} € su {eur(ctx['total_requested_eur'])} € richiesti.")
    text, source = render_with_grounding(ctx, static_budget_summary(ctx), good)
    assert source == "LLM" and text == good.text


def test_hallucinated_number_falls_back_to_static_template(seed_items, rules):
    _, ctx = _ctx(seed_items, rules)
    static = static_budget_summary(ctx)
    text, source = render_with_grounding(ctx, static, FakeLLM("Ammessi 99.999,99 € complessivi."))
    assert (text, source) == (static, "TEMPLATE")


def test_llm_failure_falls_back_and_llm_only_sees_locked_json(seed_items, rules):
    _, ctx = _ctx(seed_items, rules)
    static = static_budget_summary(ctx)
    assert render_with_grounding(ctx, static, FakeLLM(boom=True)) == (static, "TEMPLATE")
    spy = FakeLLM("Ammessi 1 €")
    render_with_grounding(ctx, static, spy)
    assert "description" not in spy.seen and "source_c_ref" not in spy.seen  # nessun dato grezzo alla LLM


def test_static_summary_passes_its_own_validator(seed_items, rules):
    resp, ctx = _ctx(seed_items, rules)
    assert validate_text_against_payload(resp.llm_explanation_summary, ctx, (100,)).ok


# ---------------------------------------------------------------- pattern
def test_pattern_match_seed_budget():
    r = PatternMatchingEngine.analyze_budget_pattern({"personnel_pct": 0.58, "assets_pct": 0.12, "consulting_pct": 0.25, "overhead_pct": 0.05})
    assert r.closest_archetype == "TRAZIONE_OCCUPAZIONALE" and r.similarity_score == 0.99
    assert r.main_deviation.category == "consulting_pct" and r.main_deviation.deviation_points == 7.0


def test_pattern_normalizes_and_identifies_pure_archetypes():
    r = PatternMatchingEngine.analyze_budget_pattern({"personnel_pct": 25, "assets_pct": 55, "consulting_pct": 15, "overhead_pct": 5})
    assert r.closest_archetype == "TRAZIONE_TECNOLOGICA" and r.similarity_score == 1.0
    assert r.main_deviation.deviation_points == 0.0


def test_pattern_rejects_empty_budget():
    with pytest.raises(ValueError):
        PatternMatchingEngine.analyze_budget_pattern({"personnel_pct": 0})
