"""Ogni bando a cui l'impresa può partecipare ha un valore in euro con la sua fonte: regole, modelli dichiarati dei bandi curati, tabelle del testo ufficiale."""
from app.core import benefit_extract, events, matching, valuation
from app.core.ingestion import Ingestion

# righe vere della tabella di intensità del bando SWIch 2026 (Regione Piemonte, par. 2.9), così come le restituisce l'estrazione del PDF
SWICH_TABLE = """2.9 Tipologia di agevolazione, regime e intensità di aiuto
L'agevolazione è concessa nella forma di contributo a fondo perduto, con intensità variabile in funzione della tipologia di beneficiario.
1 Intensità di agevolazione per attività a valere sull'art. 25 del Reg. (UE) 651/2014 - "Aiuti per progetti di ricerca e sviluppo"
TIPOLOGIA INTENSITA' MAGGIORAZIONE MAGGIORAZIONE
COLLABORAZIONE EFFETTIVA
BENEFICIARIO BASE DIMENSIONE ESL MAX
O DIFFUSIONE RISULTATI*
Micro-piccole imprese 25% 20% 15% o 5/15%*
60%
Medie imprese 25% 10% 15% o 5/15%*
50%
2 Intensità di agevolazione per attività a valere sull'art. 28 del Reg. (UE) 651/2014 - "Aiuti all'innovazione a favore delle PMI"
TIPOLOGIA BENEFICIARIO INTENSITA'
Micro-piccole imprese 50%
Medie imprese 50%
Il requisito della collaborazione risulta rispettato se le PMI sostengono almeno il 20% del totale dei costi sul progetto.
IMPORTO MASSIMO
CATEGORIA PROGETTUALE CONTRIBUTO*
1.a Small-mid challenges 1.000.000
1.b Big challenges 5.000.000
2.a P&M Challenges in partenariato 3.000.000
2.b P&M Challenges in forma singola 2.000.000
"""
PROFILE = {"size": {"code": "SMALL", "is_sme": True, "label": "Piccola impresa"}, "legal_form": "SOCIETA A RESPONSABILITA LIMITATA", "region": "Piemonte"}
BY_CAT = {"PERSONNEL": 890000.0, "CAPITAL_ASSETS": 112000.0, "CONSULTING": 172000.0, "OVERHEAD": 182000.0, "TRAINING": 18000.0}


def test_the_intensity_table_is_read_row_by_row_with_base_and_maximum():
    rows = benefit_extract.intensity_rows(SWICH_TABLE, "https://example.test/bando.pdf")
    sizes = {(r["size"], r["base"], r["max"]) for r in rows}
    assert ("MICRO_SMALL", 0.25, 0.6) in sizes and ("MEDIUM", 0.25, 0.5) in sizes and ("MICRO_SMALL", 0.5, 0.5) in sizes
    assert not any(r["max"] == 0.2 and r["size"] == "PMI" for r in rows)                   # «le PMI sostengono almeno il 20%» è una condizione, non un'intensità
    small = benefit_extract.range_for(rows, "SMALL")
    assert (small["low"], small["high"]) == (0.25, 0.6)
    medium = benefit_extract.range_for(rows, "MEDIUM")
    assert (medium["low"], medium["high"]) == (0.25, 0.5)
    assert benefit_extract.caps(SWICH_TABLE) == [1_000_000.0, 2_000_000.0, 3_000_000.0, 5_000_000.0]


def test_a_flat_sentence_is_read_without_a_size():
    rows = benefit_extract.intensity_rows("Il contributo è concesso nella misura del 40% delle spese ammissibili sostenute.")
    assert rows and rows[0]["size"] == "ALL" and rows[0]["base"] == 0.4
    assert benefit_extract.intensity_rows("L'anticipazione può arrivare fino al 30% del contributo concesso. I punti sono il 60% del totale.") == []


def test_a_bando_with_only_a_table_gets_a_range_with_source_and_project_cap():
    Ingestion.catalog("CAT-TABELLA", "Bando regionale di ricerca", "Regione", None, "https://example.test/bando")
    events.save_bando_source("CAT-TABELLA", "bando.pdf", SWICH_TABLE, url="https://example.test/bando.pdf", tier="UFFICIALE")
    out = matching.evaluate("CAT-TABELLA", PROFILE, BY_CAT, 2027)
    est = out["estimate"]
    assert est is not None and est["origin"] == "TESTO" and est["kind"] == "FONDO_PERDUTO"
    assert est["rate_pct"] == 25.0 and est["rate_high_pct"] == 60.0
    assert est["cap_eur"] == 1_000_000.0 and est["covered_eur"] == round(0.25 * sum(BY_CAT.values()), 2)       # sotto il tetto
    assert est["covered_high_eur"] == 1_000_000.0 or est["covered_high_eur"] <= 5_000_000.0                  # il massimo è limitato dal tetto più alto
    assert est["evidence"] and "Micro-piccole" in est["evidence"][0]["text"]
    assert out["fund"]["coverage_pct"] == 0.25 and out["fund"]["max_total_eur"] == 1_000_000.0


def test_only_the_official_text_is_used_not_secondary_summaries():
    Ingestion.catalog("CAT-SECONDARIA", "Bando letto da un riassunto", "Ente", None, "https://example.test/x")
    events.save_bando_source("CAT-SECONDARIA", "blog", SWICH_TABLE, url="https://blog.test/x", tier="SECONDARIA")
    assert matching.evaluate("CAT-SECONDARIA", PROFILE, BY_CAT, 2027)["estimate"] is None


def test_curated_bandi_each_have_a_value_with_assumptions_and_the_guarantee_is_not_summed():
    from app.core import bandi
    bandi.ensure_seeded()
    ev = {b: matching.evaluate(b, PROFILE, BY_CAT, 2027) for b in ("NUOVA-SABATINI", "IPERAMMORTAMENTO-2026", "SIMEST-FONDO-394-PNRR", "HORIZON-EUROPE-MGA", "FONDO-GARANZIA-PMI")}

    sab = ev["NUOVA-SABATINI"]["estimate"]
    assert sab["kind"] == "CONTO_INTERESSI" and sab["summable"] is True
    share = valuation.conventional_interest_share(0.0275)
    assert 0.07 < share < 0.08 and sab["covered_eur"] == round(BY_CAT["CAPITAL_ASSETS"] * share, 2)                # ≈ 7,6% dell'investimento finanziato
    assert sab["covered_high_eur"] > sab["covered_eur"] and sab["assumptions"]

    iper = ev["IPERAMMORTAMENTO-2026"]["estimate"]
    assert iper["kind"] == "RISPARMIO_FISCALE" and iper["covered_eur"] == round(BY_CAT["CAPITAL_ASSETS"] * 1.8 * 0.24, 2)

    sim = ev["SIMEST-FONDO-394-PNRR"]["estimate"]
    base = BY_CAT["CAPITAL_ASSETS"] + min(BY_CAT["CONSULTING"], 0.05 * 1e9)
    assert sim["rate_pct"] == 10.0 and sim["rate_high_pct"] == 20.0 and ev["SIMEST-FONDO-394-PNRR"]["fund"]["de_minimis"] is True
    assert abs(sim["covered_high_eur"] - 2 * sim["covered_eur"]) <= 0.02 and base > 0

    hor = ev["HORIZON-EUROPE-MGA"]["estimate"]
    assert hor["rate_pct"] == 70.0 and hor["rate_high_pct"] == 100.0 and hor["kind"] == "FONDO_PERDUTO"

    gar = ev["FONDO-GARANZIA-PMI"]
    assert gar["estimate"] is None and gar["fund"] is None                                                       # nessun importo da sommare né linea nel piano
    assert gar["guarantee"]["guaranteed_low_eur"] == round(BY_CAT["CAPITAL_ASSETS"] * 0.5, 2) and gar["guarantee"]["guaranteed_high_eur"] == round(BY_CAT["CAPITAL_ASSETS"] * 0.8, 2)
    assert gar["fit"] != "NON_ADATTO"


def test_the_published_rate_still_wins_over_models_and_texts():
    Ingestion.catalog("BANDO-REGOLA", "Contributi alle imprese", "Ente", None, None)
    Ingestion.extract("BANDO-REGOLA", source_text="Il contributo a fondo perduto è pari al 50% delle spese ammissibili.", source_ref="testo")
    events.save_bando_source("BANDO-REGOLA", "bando.pdf", SWICH_TABLE, url="https://example.test/b.pdf", tier="UFFICIALE")
    est = matching.evaluate("BANDO-REGOLA", PROFILE, BY_CAT, 2027)["estimate"]
    assert est["origin"] == "REGOLA" and est["rate_pct"] == 50.0 and est["rate_high_pct"] == 50.0
