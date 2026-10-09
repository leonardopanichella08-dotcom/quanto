"""Template di budget per nicchia e bando: salvataggio, consiglio pesato dall'esito, livelli di somiglianza, riallenamento a ogni dato nuovo, privacy."""
import pytest
from fastapi.testclient import TestClient

from app.core import template_learning as tl
from app.core.ingestion import Ingestion
from main import app

client = TestClient(app)

BANDO = "BANDO-AGRI"
OTHER = "BANDO-ALTRO"


def shares(**kw):
    base = {"personnel_pct": 0.10, "assets_pct": 0.45, "consulting_pct": 0.13, "research_pct": 0.161, "overhead_pct": 0.08, "training_pct": 0.04, "communication_pct": 0.039, "other_pct": 0.0}
    base.update(kw)
    return base


def seed_bandi():
    Ingestion.catalog(BANDO, "Bando per le imprese agricole", "Regione", None, None)
    Ingestion.catalog(OTHER, "Altro bando", "Ente", None, None)


def post(ateco="01.11", bando=BANDO, outcome="BOZZA", sh=None, **extra):
    return client.post("/api/v2/templates", json={"ateco_code": ateco, "bando_id": bando, "shares": sh or shares(), "outcome": outcome, **extra})


def test_ateco_gives_the_niche_and_the_section():
    n = tl.niche_label("01.11.10")
    assert n["division"] == "01" and n["section"] == "A" and "Agricoltura" in n["label"]
    assert tl.niche_label("62.01")["section"] == "J" and tl.niche_label("25.1")["section"] == "C" and tl.niche_label("70")["section"] == "M"
    with pytest.raises(tl.TemplateError):
        tl.niche_label("abc")


def test_shares_must_sum_to_one_and_percentages_are_accepted():
    ok = tl.clean_shares({"consulting_pct": 13, "research_pct": 16.1, "assets_pct": 45, "personnel_pct": 25.9})
    assert abs(sum(ok.values()) - 1) < 1e-9 and ok["research_pct"] == 0.161
    with pytest.raises(tl.TemplateError, match="100%"):
        tl.clean_shares({"consulting_pct": 0.3, "assets_pct": 0.3})
    with pytest.raises(tl.TemplateError, match="sconosciuta"):
        tl.clean_shares({"banane_pct": 1.0})


def test_a_template_is_saved_with_niche_bando_and_outcome_and_validated():
    seed_bandi()
    r = post(outcome="AMMESSO", total_eur=150000, score=82.5, region="Puglia", company_size="SMALL")
    assert r.status_code == 201, r.text
    t = r.json()
    assert t["ateco_division"] == "01" and t["bando_name"].startswith("Bando per le imprese agricole") and t["outcome"] == "AMMESSO" and t["shares"]["research_pct"] > 0.16
    assert post(bando="NON-ESISTE").status_code == 422
    assert post(sh={"consulting_pct": 0.2}).status_code == 422
    assert post(ateco="x").status_code == 422
    assert post(outcome="VINTO").status_code == 422
    assert len(client.get("/api/v2/templates").json()) == 1


def test_no_advice_without_enough_templates_and_the_message_says_how_many_are_needed():
    seed_bandi()
    post(); post()
    rec = client.post("/api/v2/templates/recommend", json={"ateco_code": "01.11", "bando_id": BANDO}).json()
    assert rec["status"] == "NO_DATA" and "almeno 3" in rec["message"] and rec["pool_size"] == 2


def test_the_recommendation_is_a_weighted_mean_where_winners_count_more():
    seed_bandi()
    winner = shares(consulting_pct=0.20, assets_pct=0.38)
    loser = shares(consulting_pct=0.05, assets_pct=0.53)
    post(outcome="AMMESSO", sh=winner); post(outcome="NON_AMMESSO", sh=loser); post(outcome="BOZZA", sh=shares())
    rec = client.post("/api/v2/templates/recommend", json={"ateco_code": "01.11", "bando_id": BANDO}).json()
    assert rec["status"] == "OK" and rec["basis"] == "NICCHIA_E_BANDO" and rec["templates_used"] == 3 and rec["wins"] == 1 and rec["confidence"] == "MEDIA"
    w = {"AMMESSO": 3.0, "NON_AMMESSO": 0.25, "BOZZA": 1.0}
    expected = (3.0 * 0.20 + 0.25 * 0.05 + 1.0 * 0.13) / sum(w.values())
    assert rec["recommended"]["consulting_pct"] == round(expected, 4)
    assert abs(sum(rec["recommended"].values()) - 1) < 0.001
    assert rec["range"]["consulting_pct"]["low"] <= rec["recommended"]["consulting_pct"] <= rec["range"]["consulting_pct"]["high"]
    assert any("ammessi" in line for line in rec["explanation"])


def test_the_advice_retrains_itself_when_an_outcome_is_updated():
    seed_bandi()
    ids = [post(outcome="BOZZA", sh=shares(consulting_pct=c, assets_pct=0.58 - c)).json()["id"] for c in (0.05, 0.10, 0.20)]
    before = client.post("/api/v2/templates/recommend", json={"ateco_code": "01.11", "bando_id": BANDO}).json()
    assert client.patch(f"/api/v2/templates/{ids[2]}", json={"outcome": "AMMESSO"}).status_code == 200
    after = client.post("/api/v2/templates/recommend", json={"ateco_code": "01.11", "bando_id": BANDO}).json()
    assert after["recommended"]["consulting_pct"] > before["recommended"]["consulting_pct"]               # il budget che ha vinto trascina il consiglio
    assert after["pool_hash"] != before["pool_hash"] and after["wins"] == 1
    again = client.post("/api/v2/templates/recommend", json={"ateco_code": "01.11", "bando_id": BANDO}).json()
    assert again["recommended"] == after["recommended"] and again["pool_hash"] == after["pool_hash"]    # stessi template, stesso consiglio


def test_tiers_fall_back_from_niche_and_bando_to_the_sector_and_say_so():
    seed_bandi()
    for div in ("01.11", "01.21", "03.11"):                         # tutte nella sezione A, bando diverso da quello cercato
        post(ateco=div, bando=OTHER)
    rec = client.post("/api/v2/templates/recommend", json={"ateco_code": "01.50", "bando_id": BANDO}).json()
    assert rec["status"] == "OK" and rec["basis"] == "SETTORE" and rec["confidence"] == "BASSA"
    assert next(t for t in rec["tier_counts"] if t["tier"] == "NICCHIA_E_BANDO")["templates"] == 0
    for _ in range(3):
        post(ateco="01.50", bando=BANDO)
    assert client.post("/api/v2/templates/recommend", json={"ateco_code": "01.50", "bando_id": BANDO}).json()["basis"] == "NICCHIA_E_BANDO"


def test_a_draft_budget_is_compared_with_the_recommendation():
    seed_bandi()
    for _ in range(3):
        post()
    draft = shares(consulting_pct=0.33, assets_pct=0.25)
    rec = client.post("/api/v2/templates/recommend", json={"ateco_code": "01.11", "bando_id": BANDO, "draft": draft}).json()
    cmp = rec["comparison"]
    assert cmp["main"]["key"] == "assets_pct" and cmp["main"]["pp"] == -20.0 and 0 < cmp["distance"] < 0.5 and "Nota professionale" in cmp["message"]


def test_private_templates_stay_private_and_shared_ones_train_everybody_anonymously():
    seed_bandi()
    for _ in range(3):
        post(shared=True)
    post(sh=shares(consulting_pct=0.5, assets_pct=0.0))                      # privato di chi scrive
    # un altro professionista vede il consiglio costruito dai soli template condivisi, non quello privato
    other = tl.recommend("altro-utente", "01.11", BANDO)
    assert other["status"] == "OK" and other["templates_used"] == 3 and other["pool_size"] == 3
    assert tl.list_templates("altro-utente") == []
    assert all("owner" not in t for t in tl.list_templates("anonymous"))                              # chi legge i propri template non vede mai il proprietario


def test_only_the_owner_can_change_or_delete_a_template():
    seed_bandi()
    tid = post().json()["id"]
    with pytest.raises(KeyError):
        tl.update_template("altro-utente", tid, {"outcome": "AMMESSO"})
    assert tl.delete_template("altro-utente", tid) is False
    assert client.delete(f"/api/v2/templates/{tid}").status_code == 200 and client.delete(f"/api/v2/templates/{tid}").status_code == 404


def test_niche_map_and_learning_feedback():
    seed_bandi()
    for i in range(6):
        post(outcome="AMMESSO" if i < 3 else "NON_AMMESSO", sh=shares(consulting_pct=0.13 if i < 3 else 0.40, assets_pct=0.45 if i < 3 else 0.18))
    post(ateco="62.01", bando=OTHER, outcome="AMMESSO")
    nm = client.get("/api/v2/templates/niches").json()
    agri = next(n for n in nm if n["division"] == "01")
    assert agri["templates"] == 6 and agri["wins"] == 3 and agri["bandi"][0]["bando_id"] == BANDO and agri["bandi"][0]["submitted"] == 6
    assert {n["division"] for n in nm} == {"01", "62"}
    st = client.get("/api/v2/templates/learning").json()
    assert st["templates_mine"] == 7 and st["outcomes"]["AMMESSO"] == 4 and st["niches"] == 2
    assert "Servono almeno 5 esiti" in st["feedback"]["message"] or st["feedback"]["enough"]


def test_styles_appear_only_with_enough_clearly_separated_templates():
    seed_bandi()
    for i in range(4):
        post(sh=shares(consulting_pct=0.30 + i * 0.005, assets_pct=0.28 - i * 0.005), outcome="NON_AMMESSO")
    for i in range(4):
        post(sh=shares(consulting_pct=0.05 + i * 0.005, assets_pct=0.53 - i * 0.005), outcome="AMMESSO")
    rec = client.post("/api/v2/templates/recommend", json={"ateco_code": "01.11", "bando_id": BANDO}).json()
    assert len(rec["styles"]) == 2 and rec["styles"][0]["wins"] == 4 and rec["styles"][1]["wins"] == 0


def test_other_peoples_shared_templates_are_used_only_in_groups_of_three_or_more():
    seed_bandi()
    post(shared=True); post(shared=True)                                    # solo due condivisi: un secondo professionista non deve poterli distinguere
    assert tl.recommend("altro-utente", "01.11", BANDO)["status"] == "NO_DATA"
    assert tl.niche_map("altro-utente") == []
    post(shared=True)                                                       # con il terzo il gruppo è anonimo abbastanza
    assert tl.recommend("altro-utente", "01.11", BANDO)["status"] == "OK"
    assert tl.niche_map("altro-utente")[0]["templates"] == 3
    assert len(tl.niche_map("anonymous")[0]["bandi"]) == 1                  # chi li ha scritti li vede sempre tutti
