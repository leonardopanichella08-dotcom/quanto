"""Cosa serve all'azienda per crescere: persone e strumenti dai ricavi previsti, a parità di produttività e di intensità di capitale. Mai numeri inventati: senza dati lo dice."""
from app.core import company_facts, company_profile as cp, growth_needs
from tests.test_budget_dynamics import client, company  # noqa: F401  (company è una fixture)


def _fake(monkeypatch, revenue=(3_000_000.0, 3_600_000.0), employees=20, personnel=1_000_000.0, assets=(600_000.0,), hires=1, capex=30_000.0):
    fin = {2025: ({"revenue_eur": revenue[0], "employees_avg": employees, "personnel_eur": personnel, "capital_assets_eur": 10.0, "consulting_eur": 1.0, "overhead_eur": 1.0, "training_eur": 1.0}, {})}
    monkeypatch.setattr(cp, "_load_financials", lambda owner: fin)
    monkeypatch.setattr(cp, "forecast", lambda owner, year, growth=None: {"base_year": 2025, "fiscal_year": year, "revenue": {"baseline_eur": revenue[0], "forecast_eur": revenue[1], "explanation": ["dal bilancio"]}})
    monkeypatch.setattr(company_facts, "facts", lambda owner: {"asset_line": [{"cost_eur": a, "net_eur": a / 2} for a in assets], "capex_plan": [{"year": 2026, "amount_eur": capex}] if capex else []})
    monkeypatch.setattr(company_facts, "staff", lambda owner: {"people": [], "hiring_plan": [{"start": "2026-03-01"}] * hires, "missing": []})


def test_growth_needs_people_and_tools_from_forecast_revenue(monkeypatch):
    _fake(monkeypatch)
    out = growth_needs.growth_needs("x", 2026)
    kinds = {n["kind"]: n for n in out["needs"]}
    assert out["growth_pct"] == 20.0
    # 3.000.000 € con 20 persone = 150.000 € a persona; 3.600.000 € → 24 persone; 1 già in programma → ne mancano 3, a 50.000 € l'una (1.000.000 € ÷ 20)
    assert kinds["PERSONE"]["quantity"] == 3 and kinds["PERSONE"]["unit_cost_eur"] == 50_000.0 and kinds["PERSONE"]["amount_eur"] == 150_000.0
    assert "150.000 € a persona" in kinds["PERSONE"]["basis"] and "già nel piano delle assunzioni" in kinds["PERSONE"]["basis"]
    # beni 600.000 € su 3.000.000 € di ricavi = 20%; a 3.600.000 € servono 720.000 €; ce ne sono 600.000 e 30.000 sono già nel piano → 90.000 €
    assert kinds["STRUMENTI"]["amount_eur"] == 90_000.0 and kinds["STRUMENTI"]["category"] == "CAPITAL_ASSETS"
    assert out["total_eur"] == 240_000.0 and "ipotesi" in out["assumption"]


def test_no_growth_means_no_needs_and_missing_data_is_said_not_guessed(monkeypatch):
    _fake(monkeypatch, revenue=(3_000_000.0, 3_000_000.0))
    out = growth_needs.growth_needs("x", 2026)
    assert out["needs"] == [] and "non vede crescita" in out["message"]
    _fake(monkeypatch, employees=None, assets=())
    out = growth_needs.growth_needs("x", 2026)
    assert out["needs"] == [] and any("organico" in m for m in out["missing"]) and any("libro cespiti" in m for m in out["missing"])
    _fake(monkeypatch, revenue=(3_000_000.0, 3_030_000.0), hires=0)                              # +1%: mezza persona o meno non è un'assunzione
    out = growth_needs.growth_needs("x", 2026)
    assert not [n for n in out["needs"] if n["kind"] == "PERSONE"]


def test_the_growth_project_comes_first_in_the_ideas_and_is_made_of_new_expenses(company, monkeypatch):
    needs = {"year": 2026, "base_year": 2025, "growth_pct": 20.0, "message": "Per sostenere la crescita prevista servono: 3 persone in più; Strumenti e attrezzature per circa 90.000 €.", "assumption": "A parità di produttività: ipotesi.",
             "needs": [{"kind": "PERSONE", "label": "3 persone in più", "quantity": 3, "unit_cost_eur": 50000.0, "amount_eur": 150000.0, "category": "PERSONNEL", "basis": "calcolo"},
                       {"kind": "STRUMENTI", "label": "Strumenti per circa 90.000 €", "quantity": None, "amount_eur": 90000.0, "category": "CAPITAL_ASSETS", "basis": "calcolo"}], "missing": [], "total_eur": 240000.0}
    monkeypatch.setattr(growth_needs, "growth_needs", lambda owner, year=None: needs)
    data = client.get("/api/v2/profile/project-ideas?year=2026").json()
    first = data["ideas"][0]
    assert first["id"] == "crescita" and first["project_types"] == ["OCCUPAZIONE", "INVESTIMENTI_PRODUTTIVI"] and first["new_eur"] == 240_000.0
    assert {ln["category"] for ln in first["lines"]} == {"PERSONNEL", "CAPITAL_ASSETS"} and all(ln["nature"] == "NUOVA" for ln in first["lines"])
    assert any("RAL" in m for m in first["missing"]) and first["cautions"] and data["needs"]["total_eur"] == 240_000.0


def test_the_allocation_reads_the_whole_catalog_and_says_how_many_it_read_and_how_many_it_studied(company):
    out = client.post("/api/v2/profile/match", json={"year": 2026})
    assert out.status_code == 200, out.text
    stats = out.json()["matching"]["catalog"]["stats"]
    assert {"open_total", "read", "unread", "studied", "studied_fit", "candidates", "high", "medium", "excluded"} <= set(stats)
    assert stats["studied"] >= 5 and stats["studied_fit"] <= stats["studied"]                  # i bandi studiati a fondo fanno il piano con importi veri
    for it in out.json()["matching"]["catalog"]["items"]:
        assert "cost_categories" in it                                                         # la scheda dice quali spese ammette: serve a trovare chi finanzia un progetto
