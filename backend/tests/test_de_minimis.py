"""De minimis: quali bandi lo sono (solo se lo dice una fonte) e quanto del tetto di 300.000 € resta all'azienda (stima dichiarata, mai inventata)."""
from app.core import benefit_extract, de_minimis, valuation
from app.core import company_profile as cp
from app.core.db import connect


def test_the_text_that_says_the_aid_is_de_minimis_is_found_with_its_words():
    hits = benefit_extract.de_minimis_mentions("Il contributo è concesso ai sensi del Regolamento (UE) 2023/2831 relativo agli aiuti «de minimis» alle imprese.")
    assert len(hits) == 1 and not hits[0]["negated"] and "2023/2831" in hits[0]["text"]


def test_an_explicit_denial_is_not_counted_and_no_mention_means_not_de_minimis():
    hits = benefit_extract.de_minimis_mentions("Il presente aiuto non rientra nel regime de minimis ma è un aiuto in esenzione.")
    assert len(hits) == 1 and hits[0]["negated"]
    assert benefit_extract.de_minimis_mentions("Contributo pari al 50% delle spese ammissibili.") == []


def test_a_curated_model_flag_makes_the_bando_de_minimis_with_the_reason():
    info = valuation.de_minimis_info("QUALSIASI-ID-SENZA-FONTI", {"kind": "FONDO_PERDUTO", "de_minimis": True, "evidence": []})
    assert info["applies"] and info["basis"] == "MODELLO" and "300.000" in info["evidence"][0]["text"]
    none = valuation.de_minimis_info("QUALSIASI-ID-SENZA-FONTI", None)
    assert not none["applies"] and none["basis"] is None and none["evidence"] == []


def _source(bando_id: str, text: str, tier: str) -> None:
    with connect() as conn:
        conn.execute("INSERT INTO bando_sources (bando_id, ts, name, sha256, text, url, tier) VALUES (?,?,?,?,?,?,?) ON CONFLICT (bando_id, sha256) DO UPDATE SET text=excluded.text",
                     (bando_id, "2026-10-09T10:00:00", "avviso.pdf", f"sha-{bando_id}", text, "https://ente.example/avviso.pdf", tier))


def test_a_bando_whose_official_text_cites_the_regime_counts_against_the_ceiling():
    _source("T-DM-SI", "Art. 9. Gli aiuti sono concessi ai sensi del Regolamento (UE) 2023/2831 relativo all'applicazione degli aiuti de minimis.", "UFFICIALE")
    info = valuation.de_minimis_info("T-DM-SI", None)
    assert info["applies"] and info["basis"] == "TESTO" and info["evidence"][0]["url"] == "https://ente.example/avviso.pdf"
    assert "2023/2831" in info["evidence"][0]["text"]


def test_a_denial_in_the_official_text_is_reported_but_does_not_count_and_a_secondary_source_is_ignored():
    _source("T-DM-NO", "Il contributo non rientra nel regime de minimis: è un aiuto in esenzione.", "UFFICIALE")
    info = valuation.de_minimis_info("T-DM-NO", None)
    assert not info["applies"] and info["mentioned"] and info["basis"] == "TESTO"
    _source("T-DM-SEC", "Secondo il blog il bando è in regime de minimis.", "SECONDARIA")
    assert not valuation.de_minimis_info("T-DM-SEC", None)["mentioned"]


def test_estimate_without_any_declared_aid_is_the_declared_hypothesis():
    est = de_minimis.estimate("nessuno-" + "x", 2027)
    assert est["basis"] == "IPOTESI" and est["residual_eur"] == 300000.0 and est["received_eur"] == 0.0
    assert "non è un dato verificato" in est["note"].lower() and est["years_missing"] == [2024, 2025, 2026]


def test_declared_public_aid_in_the_last_three_years_reduces_the_residual():
    owner = "studio-dm-test"
    cp.update_financials(owner, 2025, {"public_aid_eur": 120000}, owner)
    est = de_minimis.estimate(owner, 2027)
    assert est["basis"] == "PARZIALE" and est["received_eur"] == 120000.0 and est["residual_eur"] == 180000.0
    assert est["years_declared"] == [2025] and est["years_missing"] == [2024, 2026]
    cp.update_financials(owner, 2024, {"public_aid_eur": 0}, owner)
    cp.update_financials(owner, 2026, {"public_aid_eur": 40000}, owner)
    est = de_minimis.estimate(owner, 2027, used_by_plan_eur=17305.24)
    assert est["basis"] == "DICHIARATI" and est["residual_eur"] == 140000.0
    assert est["needed_eur"] == 17305.24 and est["margin_eur"] == 122694.76


def test_the_residual_never_goes_below_zero():
    owner = "studio-dm-test-2"
    cp.update_financials(owner, 2026, {"public_aid_eur": 500000}, owner)
    assert de_minimis.estimate(owner, 2027)["residual_eur"] == 0.0


def test_a_year_with_only_declared_aid_is_not_the_last_balance_sheet():
    owner = "studio-dm-test-3"
    cp.update_financials(owner, 2026, {"public_aid_eur": 10000}, owner)
    ov = cp.overview(owner)
    assert ov["last_year"] is None and ov["financials"][0]["fiscal_year"] == 2026         # niente «ultimo bilancio»: servono ricavi o costi
    cp.update_financials(owner, 2025, {"revenue_eur": 100000, "personnel_eur": 20000}, owner)
    assert cp.overview(owner)["last_year"] == 2025


def test_the_match_returns_the_estimate_and_marks_every_bando():
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    r = client.put("/api/v2/profile/financials/2025", json={"values": {"revenue_eur": 900000, "personnel_eur": 200000, "capital_assets_eur": 60000, "consulting_eur": 40000, "overhead_eur": 25000, "training_eur": 6000}})
    assert r.status_code == 200, r.text
    out = client.post("/api/v2/profile/match", json={"year": 2027, "growth": {}})
    assert out.status_code == 200, out.text
    body = out.json()
    assert body["de_minimis"]["plafond_eur"] == 300000.0 and body["de_minimis"]["basis"] in ("IPOTESI", "PARZIALE", "DICHIARATI")
    assert body["matching"]["results"] and all("applies" in x["de_minimis"] for x in body["matching"]["results"])
    simest = [x for x in body["matching"]["results"] if "394" in x["name"] and x.get("fund")]
    assert simest and all(x["fund"]["de_minimis"] and x["de_minimis"]["applies"] for x in simest)       # SIMEST: lo dice la scheda curata
