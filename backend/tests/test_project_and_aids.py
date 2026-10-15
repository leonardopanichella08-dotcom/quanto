"""Progetti e aiuti: che tipo di progetto finanzia un bando, idee di progetto dai documenti dell'azienda, spese ordinarie contro spese nuove, e la verifica del de minimis
sul registro nazionale degli aiuti con l'impresa unica."""
from datetime import date, timedelta

from app.core import aids_register, de_minimis, project_types
from tests.test_budget_dynamics import FUNDS, _plan, client, company  # noqa: F401  (company è una fixture)


# ------------------------------------------------------------------------------------------------ che progetti finanzia un bando
def test_project_types_come_from_the_sentences_of_the_bando_text_with_the_sentence_as_proof():
    texts = ["Sono finanziati progetti di digitalizzazione e di trasformazione digitale delle PMI.", "Il bando sostiene la ricerca industriale e lo sviluppo sperimentale.",
             "Le spese per l'acquisto di macchinari e attrezzature sono ammissibili.", "x" * 600 + " formazione del personale"]
    out = {t["code"]: t for t in project_types.for_texts(texts)}
    assert {"DIGITALIZZAZIONE", "RICERCA_SVILUPPO", "INVESTIMENTI_PRODUTTIVI"} <= set(out)
    assert "FORMAZIONE" not in out                                        # un impaginato rotto non dice di cosa si parla
    assert "digitalizzazione" in out["DIGITALIZZAZIONE"]["evidence"][0].lower()
    assert project_types.for_texts([]) == [] and project_types.for_texts(["Il bando è aperto fino al 30 giugno."]) == []        # senza testo non si indovina


def test_the_bando_detail_lists_the_project_types_it_finances(company):
    det = client.get("/api/v2/bandi/FVG-VALIDAZIONE-TRL-2026").json()
    assert isinstance(det["project_types"], list)
    sab = {t["code"] for t in client.get("/api/v2/bandi/NUOVA-SABATINI").json()["project_types"]}
    assert "INVESTIMENTI_PRODUTTIVI" in sab or "DIGITALIZZAZIONE" in sab        # la Sabatini finanzia beni strumentali e tecnologie digitali


# ------------------------------------------------------------------------------------------------ idee di progetto
def test_project_ideas_are_built_on_the_company_documents_and_never_invent_an_amount(company):
    out = client.get("/api/v2/profile/project-ideas?year=2026")
    assert out.status_code == 200, out.text
    data = out.json()
    ideas = {i["id"]: i for i in data["ideas"]}
    assert {"piano-ricerca_sviluppo", "piano-digitalizzazione", "rinnovo-beni", "assunzioni", "formazione"} <= set(ideas)
    # le spese già in programma sono nuove; quelle che l'azienda sostiene comunque sono ordinarie e restano separate
    rd = ideas["piano-ricerca_sviluppo"]
    assert rd["new_eur"] == 73500.0 and rd["ordinary_eur"] == 0 and rd["lines"][0]["sources"][0]["filename"]
    training = ideas["formazione"]
    assert training["new_eur"] == 0 and training["ordinary_eur"] > 0 and all(ln["nature"] == "ORDINARIA" for ln in training["lines"])
    # un importo che non viene da un documento non si inventa
    energy = ideas["energia"]
    assert all(ln["amount_eur"] is None and ln["nature"] == "DA_QUANTIFICARE" for ln in energy["lines"]) and energy["new_eur"] == 0 and energy["to_quantify"]
    hires = ideas["assunzioni"]
    assert any("RAL" in m for m in hires["missing"]) and hires["project_types"][0] == "OCCUPAZIONE"
    assert all(ln["item_id"].startswith("IDEA-") for i in data["ideas"] for ln in i["lines"])
    assert any("ipotesi" in n for n in data["notes"])
    # i bandi che finanziano quel tipo di progetto, con la frase come prova
    for i in data["ideas"]:
        for b in i["bandi"]:
            assert b["bando_id"] and b["types"]
    # le idee con spese nuove vengono per prime
    news = [i["new_eur"] for i in data["ideas"]]
    assert news == sorted(news, reverse=True)


def test_a_project_idea_can_be_allocated_and_becomes_budgets_for_the_funds(company):
    ideas = client.get("/api/v2/profile/project-ideas?year=2026").json()["ideas"]
    idea = next(i for i in ideas if i["id"] == "piano-digitalizzazione")
    lines = [{"item_id": ln["item_id"], "category": ln["category"], "amount_eur": ln["amount_eur"], "expense_type": ln["expense_type"], "label": ln["label"]} for ln in idea["lines"] if ln["nature"] == "NUOVA"]
    r = client.post("/api/v2/allocation/optimize", json={"fiscal_year": 2026, "historical_expenses": lines, "available_funding_lines": list(FUNDS)})
    assert r.status_code == 200, r.text
    plan = r.json()
    assert plan["total_gross_expense_eur"] == round(sum(ln["amount_eur"] for ln in lines), 2)           # solo le spese nuove del progetto, non i costi annuali
    out = client.post("/api/v2/allocation/budgets", json={"allocation": plan, "fiscal_year": 2026, "funding_lines": list(FUNDS)})
    assert out.status_code == 200, out.text
    assert out.json()["ok"] and out.json()["budgets"]


# ------------------------------------------------------------------------------------------------ spese ordinarie contro spese nuove
def test_the_template_says_it_is_not_yet_a_project_and_separates_new_from_ordinary_costs(company):
    r = client.post("/api/v2/profile/template", json={"bando_id": "FVG-VALIDAZIONE-TRL-2026", "scale_pct": 40, "fit": True, "project_start": "2026-03-01"})
    assert r.status_code == 200, r.text
    t = r.json()
    assert t["notes"][0].startswith("Questa bozza parte dalle spese che l'azienda sostiene già") and "non è ancora un progetto" in t["notes"][0]
    natures = {b["basis"]: b["nature"] for b in t["basis"]}
    assert natures["PIANO_INVESTIMENTI"] == "NUOVA" and natures["BUDGET"] == "ORDINARIA"
    assert t["reality"]["new_eur"] > 0 and t["reality"]["ordinary_eur"] > t["reality"]["new_eur"]
    assert any("timesheet" in n for n in t["notes"])                          # la quota di tempo va dimostrata sulle ore vere
    assert all(i["expense_date"] == "2026-03-01" for i in t["cost_items"])    # il controllo 46 verifica la finestra del bando su ogni voce
    bad = client.post("/api/v2/profile/template", json={"bando_id": "FVG-VALIDAZIONE-TRL-2026", "scale_pct": 40, "project_start": "domani"})
    assert bad.status_code == 422


# ------------------------------------------------------------------------------------------------ de minimis, impresa unica e registro nazionale
def _rows(*amounts, when="2025-06-10"):
    return [{"granted": when, "entity": "Ente di prova", "measure": f"Misura {i}", "regime": "de minimis", "amount_eur": a, "cor": f"COR-{1000 + i}"} for i, a in enumerate(amounts, 1)]


def test_without_a_verification_the_de_minimis_is_not_verified_and_the_plan_uses_a_safety_margin():
    st = aids_register.status("t-aids")
    assert st["status"] == "NON_VERIFICATO" and st["usable_residual_eur"] == 270000.0 and st["safety_margin_eur"] == 30000.0
    est = de_minimis.estimate("t-aids", 2027)
    assert est["basis"] == "IPOTESI" and est["verification"]["status"] == "NON_VERIFICATO" and est["safe_residual_eur"] == 270000.0     # 300.000 − 10% del tetto


def test_the_single_enterprise_flow_is_not_complete_with_a_dont_know_and_needs_the_related_companies():
    assert aids_register.status("t-aids2")["status"] == "NON_VERIFICATO"
    r = client.put("/api/v2/profile/aids/group", json={"answers": {"a": "no", "b": "no", "c": "no", "d": "no", "e": "non_so"}, "companies": []})
    assert r.status_code == 200 and any("non so" in p for p in r.json()["problems"])
    bad = client.put("/api/v2/profile/aids/group", json={"answers": {"a": "si", "b": "no", "c": "no", "d": "no", "e": "no"}, "companies": []})
    assert bad.status_code == 422 and "elenca le imprese collegate" in bad.json()["detail"]
    assert client.put("/api/v2/profile/aids/group", json={"answers": {"z": "no"}, "companies": []}).status_code == 422
    assert client.put("/api/v2/profile/aids/group", json={"answers": {"a": "forse"}, "companies": []}).status_code == 422


def test_a_complete_and_recent_verification_makes_the_residual_official():
    ok = {"a": "no", "b": "no", "c": "no", "d": "no", "e": "no"}
    client.put("/api/v2/profile/aids/group", json={"answers": ok, "companies": []})
    st = client.put("/api/v2/profile/aids/entries", json={"company": "SELF", "source": "RNA", "checked_at": date.today().isoformat(), "entries": _rows(10000, 6500)}).json()
    assert st["status"] == "VERIFICATO" and st["received_eur"] == 16500.0 and st["residual_eur"] == 283500.0 and st["usable_residual_eur"] == 283500.0 and st["problems"] == []
    assert client.post("/api/v2/profile/aids/confirm", json={"note": "visura del giorno"}).json()["confirmations"][-1]["status"] == "VERIFICATO"


def test_an_old_visura_or_a_missing_related_company_blocks_the_verification():
    ok = {"a": "no", "b": "no", "c": "no", "d": "no", "e": "no"}
    client.put("/api/v2/profile/aids/group", json={"answers": ok, "companies": []})
    old = (date.today() - timedelta(days=45)).isoformat()
    st = client.put("/api/v2/profile/aids/entries", json={"company": "SELF", "source": "RNA", "checked_at": old, "entries": _rows(10000)}).json()
    assert st["status"] == "SCADUTO" and st["usable_residual_eur"] == 260000.0 and any("più di 30 giorni" in p for p in st["problems"])
    yes = {"a": "si", "b": "no", "c": "no", "d": "no", "e": "no"}
    st = client.put("/api/v2/profile/aids/group", json={"answers": yes, "companies": [{"cf": "01234567890", "name": "Controllata Srl", "relation": "controllata al 60%"}]}).json()
    assert st["status"] == "NON_VERIFICATO" and any("Controllata Srl" in p for p in st["problems"])
    st = client.put("/api/v2/profile/aids/entries", json={"company": "SELF", "source": "RNA", "checked_at": date.today().isoformat(), "entries": _rows(10000)}).json()
    assert st["status"] == "NON_VERIFICATO"                                  # la visura della collegata manca ancora
    st = client.put("/api/v2/profile/aids/entries", json={"company": "01234567890", "source": "RNA", "checked_at": date.today().isoformat(), "entries": _rows(40000, when="2025-02-01")}).json()
    assert st["status"] == "VERIFICATO" and st["received_eur"] == 50000.0 and st["residual_eur"] == 250000.0          # gli aiuti della collegata contano nel tetto dell'impresa unica


def test_the_visura_is_compared_with_what_the_company_declared_in_its_documents(company, tmp_path):
    import base64
    from tests.test_budget_dynamics import sample
    path = next(p for k, p in sample.build(tmp_path) if p.name.startswith("13_Registro_aiuti"))
    assert client.post("/api/v2/fonte-c/documents", json={"doc_type": "OTHER", "filename": path.name, "content_base64": base64.b64encode(path.read_bytes()).decode()}).status_code == 201
    ok = {"a": "no", "b": "no", "c": "no", "d": "no", "e": "no"}
    client.put("/api/v2/profile/aids/group", json={"answers": ok, "companies": []})
    st = client.get("/api/v2/profile/aids?on=2026-10-02").json()
    assert st["declared_in_documents"]                                       # il registro degli aiuti caricato è letto
    # la visura riporta solo uno dei due aiuti dichiarati: la differenza va spiegata
    first = st["declared_in_documents"][0]
    st = client.put("/api/v2/profile/aids/entries", json={"company": "SELF", "source": "RNA", "checked_at": date.today().isoformat(),
                                                          "entries": [{"granted": first["granted"], "entity": first["entity"], "measure": first["measure"], "regime": "de minimis", "amount_eur": first["amount_eur"], "cor": first["cor"]}]}).json()
    if len(st["declared_in_documents"]) > 1:
        assert st["status"] == "DISCORDANZA" and any("Dichiarato nei documenti ma non nella visura" in d for d in st["differences"])
    # i valori non validi si rifiutano con un messaggio chiaro
    assert client.put("/api/v2/profile/aids/entries", json={"company": "SELF", "source": "RNA", "entries": []}).status_code == 422
    assert client.put("/api/v2/profile/aids/entries", json={"company": "SELF", "source": "RNA", "checked_at": "2099-01-01", "entries": []}).status_code == 422
    assert client.put("/api/v2/profile/aids/entries", json={"company": "SELF", "source": "MANUALE", "entries": [{"granted": "2025-01-01", "amount_eur": -5}]}).status_code == 422


def test_a_verified_residual_replaces_the_estimate_in_the_plan_and_an_unverified_one_stays_prudent():
    ok = {"a": "no", "b": "no", "c": "no", "d": "no", "e": "no"}
    aids_register.save_group("t-aids3", ok, [], "test")
    est = de_minimis.estimate("t-aids3", 2027)
    assert est["basis"] == "IPOTESI" and est["safe_residual_eur"] == 270000.0 and est["verification"]["status"] == "NON_VERIFICATO"
    aids_register.save_entries("t-aids3", "SELF", "RNA", _rows(20000, 15000), date.today().isoformat(), "test")
    est = de_minimis.estimate("t-aids3", 2027)
    assert est["basis"] == "RNA" and est["received_eur"] == 35000.0 and est["residual_eur"] == 265000.0 and est["safe_residual_eur"] == 265000.0
    assert "Registro Nazionale degli Aiuti" in est["note"] and est["verification"]["status"] == "VERIFICATO"
    # una verifica incompleta che trova più aiuti di quelli dei bilanci vale come la più prudente
    aids_register.save_group("t-aids4", {"a": "no", "b": "no", "c": "no", "d": "no", "e": "non_so"}, [], "test")
    aids_register.save_entries("t-aids4", "SELF", "MANUALE", _rows(100000), None, "test")
    est = de_minimis.estimate("t-aids4", 2027)
    assert est["verification"]["status"] == "NON_VERIFICATO" and est["safe_residual_eur"] == 170000.0           # 300.000 − 100.000 − 30.000 di margine


# ------------------------------------------------------------------------------------------------ non tutti i bandi chiedono un progetto
def test_each_bando_says_how_it_is_accessed_and_not_all_of_them_ask_for_a_project(company):
    mode = {}
    for bid in ("FONDO-GARANZIA-PMI", "IPERAMMORTAMENTO-2026", "SIMEST-FONDO-394-PNRR", "FVG-VALIDAZIONE-TRL-2026", "HORIZON-EUROPE-MGA", "NUOVA-SABATINI", "SMART-START-ITALIA"):
        mode[bid] = client.get(f"/api/v2/bandi/{bid}").json()["funding_modes"]
    assert mode["FONDO-GARANZIA-PMI"]["primary"] == "GARANZIA_LIQUIDITA" and mode["IPERAMMORTAMENTO-2026"]["primary"] == "CREDITO_AUTOMATICO"
    assert mode["SIMEST-FONDO-394-PNRR"]["primary"] == "SPESE_CORRENTI"
    assert all(mode[b]["primary"] == "PROGETTO_INVESTIMENTO" for b in ("FVG-VALIDAZIONE-TRL-2026", "HORIZON-EUROPE-MGA", "NUOVA-SABATINI", "SMART-START-ITALIA"))
    first = {b: m["modes"][0] for b, m in mode.items()}
    assert first["FONDO-GARANZIA-PMI"]["needs_project"] is False and first["FONDO-GARANZIA-PMI"]["ordinary_costs_ok"] is True       # per la liquidità serve il fabbisogno, non un progetto
    assert first["IPERAMMORTAMENTO-2026"]["needs_project"] is False and first["IPERAMMORTAMENTO-2026"]["ordinary_costs_ok"] is False  # contano gli acquisti qualificati
    assert first["SIMEST-FONDO-394-PNRR"]["ordinary_costs_ok"] is True and first["FVG-VALIDAZIONE-TRL-2026"]["needs_project"] is True
    assert all(m["base"] and m["example"] for m in first.values())
    assert first["FONDO-GARANZIA-PMI"]["by_benefit_type"] is True and first["FONDO-GARANZIA-PMI"]["mentions"] >= 1             # tipo di aiuto e frasi del testo
    assert client.get("/api/v2/bandi/QUANTO-SANDBOX-60").json()["funding_modes"] == {"primary": None, "modes": []}              # senza testo né tipo di aiuto non si indovina


def test_the_template_depends_on_how_the_bando_is_accessed(company):
    simest = client.post("/api/v2/profile/template", json={"bando_id": "SIMEST-FONDO-394-PNRR", "scale_pct": 20, "fit": True})
    assert simest.status_code == 200, simest.text
    t = simest.json()
    assert t["notes"][0].startswith("Questo bando non chiede un progetto nuovo") and "base valida" in t["notes"][0]
    assert {b["nature"] for b in t["basis"]} <= {"NUOVA", "CORRENTE"} and any(b["nature"] == "CORRENTE" for b in t["basis"])          # le spese correnti, qui, non sono sospette
    assert t["reality"]["mode"]["ordinary_costs_ok"] is True
    fvg = client.post("/api/v2/profile/template", json={"bando_id": "FVG-VALIDAZIONE-TRL-2026", "scale_pct": 40}).json()
    assert fvg["notes"][0].startswith("Questa bozza parte dalle spese che l'azienda sostiene già") and any(b["nature"] == "ORDINARIA" for b in fvg["basis"])


def test_ideas_list_the_measures_that_need_no_project_with_their_own_base(company):
    data = client.get("/api/v2/profile/project-ideas?year=2026").json()
    ids = {m["bando_id"]: m for m in data["no_project"]}
    assert {"FONDO-GARANZIA-PMI", "IPERAMMORTAMENTO-2026", "SIMEST-FONDO-394-PNRR"} <= set(ids)
    assert "FVG-VALIDAZIONE-TRL-2026" not in ids
    assert all(m["base"] and m["example"] for m in ids.values()) and ids["SIMEST-FONDO-394-PNRR"]["ordinary_costs_ok"] is True
    for idea in data["ideas"]:
        for b in idea["bandi"]:
            assert "mode" in b and "needs_project" in b and "ordinary_costs_ok" in b


def test_the_matching_shows_the_mode_of_every_bando(company):
    r = client.post("/api/v2/profile/match", json={"year": 2027})
    assert r.status_code == 200, r.text
    results = {x["bando_id"]: x for x in r.json()["matching"]["results"]}
    assert results["FONDO-GARANZIA-PMI"]["mode"]["code"] == "GARANZIA_LIQUIDITA" and results["FVG-VALIDAZIONE-TRL-2026"]["mode"]["needs_project"] is True
