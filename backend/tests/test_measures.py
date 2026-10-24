"""Le agevolazioni che non sono bandi: esoneri INPS, tirocini, apprendistato, incentivi regionali; il tipo di impresa e i dati minimi."""
from datetime import date

import pytest

from app.core import company_profile as cp, measures

PROFILE = {"company_type": "CAPITALI", "company_status": "COSTITUITA", "region": "Puglia", "employees": 8, "durc_regular": True}
D = date(2026, 10, 24)


def ev(mid, profile=None, today=D, **over):
    return measures.evaluate(measures.BY_ID[mid], {**PROFILE, **(profile or {}), **over}, today)


def test_company_conditions_are_checked_on_the_profile_and_worker_conditions_are_who_to_hire():
    assert ev("BONUS_ZES_2026")["status"] == "APPLICABILE"                                              # sede in ZES unica, 8 dipendenti, DURC regolare
    assert ev("BONUS_ZES_2026", employees=12)["status"] == "NON_APPLICABILE" and "12 dipendenti" in ev("BONUS_ZES_2026", employees=12)["why"][0]
    assert ev("BONUS_ZES_2026", region="Lombardia")["status"] == "NON_APPLICABILE" and "non è nella ZES" in ev("BONUS_ZES_2026", region="Lombardia")["why"][0]
    assert ev("BONUS_GIOVANI_2026", durc_regular=False)["status"] == "NON_APPLICABILE"
    unknown = ev("BONUS_GIOVANI_2026", durc_regular=None)                                                # un dato che manca si chiede, non si indovina
    assert unknown["status"] == "DA_VERIFICARE" and unknown["to_check"][0]["key"] == "durc_regular"
    assert ev("BONUS_GIOVANI_2026")["status"] == "APPLICABILE"


def test_expired_new_companies_and_regional_families():
    assert ev("BONUS_GIOVANI_2026", today=date(2027, 1, 10))["status"] == "SCADUTA"
    assert ev("BONUS_GIOVANI_2026", company_status="DA_COSTITUIRE")["status"] == "DOPO_LA_COSTITUZIONE"
    assert ev("NUOVE_IMPRESE_BANDI", company_status="DA_COSTITUIRE")["status"] in ("APPLICABILE", "DA_VERIFICARE")
    reg = ev("TIROCINIO_GARANZIA_GIOVANI")                                                              # famiglia regionale: nessun importo inventato, i parametri si leggono nel bando
    assert reg["status"] == "DA_VERIFICARE" and measures.value_per_hire(measures.BY_ID["TIROCINIO_GARANZIA_GIOVANI"], PROFILE) is None


def test_value_per_hire_is_cap_times_months_and_zes_raises_the_cap():
    zes = measures.value_per_hire(measures.BY_ID["BONUS_GIOVANI_2026"], PROFILE)
    assert zes["cap_month_eur"] == 650 and zes["min_eur"] == 7800 and zes["max_eur"] == 15600 and "650 € al mese" in zes["text"]
    north = measures.value_per_hire(measures.BY_ID["BONUS_GIOVANI_2026"], {**PROFILE, "region": "Lombardia"})
    assert north["cap_month_eur"] == 500 and north["max_eur"] == 12000
    women = measures.value_per_hire(measures.BY_ID["BONUS_DONNE_2026"], PROFILE)
    assert women["cap_month_eur"] == 800 and women["max_eur"] == 19200


def test_the_best_exoneration_is_chosen_not_summed():
    best = measures.best_for_hires(PROFILE, 2, D)
    assert best[0]["id"] == "BONUS_DONNE_2026" and best[0]["total_max_eur"] == 2 * 19200
    assert all("Non cumulabile" in b["cumulation"] for b in best)
    assert {m["group"] for m in measures.MEASURES if m["id"] in ("BONUS_GIOVANI_2026", "BONUS_DONNE_2026", "BONUS_ZES_2026")} == {"ESONERI_2026"}


def test_every_measure_has_a_source_and_a_verification_level():
    for m in measures.MEASURES:
        assert m["source"]["label"] and m["verified"] in ("SECONDARIA", "DA_VERIFICARE")
        if m["verified"] == "DA_VERIFICARE":
            assert m.get("cap_month_eur") is None                                                       # niente importi mensili inventati dove non c'è una fonte letta
    out = measures.for_company(PROFILE, D)
    assert [f["id"] for f in out["families"]][:3] == ["ESONERI_INPS", "OCCUPAZIONE_REGIONALE", "TIROCINI"] and out["verified_on"] and "confermati sul sito INPS" in out["warning"]


# ------------------------------------------------------------------------------------------------ il tipo di impresa e i dati minimi
@pytest.mark.parametrize("text,expected", [("SOCIETA' A RESPONSABILITA' LIMITATA", "CAPITALI"), ("S.r.l.", "CAPITALI"), ("S.p.A.", "CAPITALI"), ("Società in accomandita per azioni", "CAPITALI"),
                                           ("S.N.C.", "PERSONE"), ("Società in accomandita semplice", "PERSONE"), ("Società semplice", "PERSONE"), ("Impresa individuale", "DITTA"),
                                           ("Libero professionista", "DITTA"), ("boh", None), ("", None), (None, None)])
def test_company_type_is_read_from_the_legal_form(text, expected):
    assert cp.infer_company_type(text) == expected


def test_persons_and_sole_traders_need_only_revenue_and_personnel_from_the_tax_return():
    need = cp.required_for("PERSONE")
    assert need["fin_required"] == ["revenue_eur", "personnel_eur"] and need["document"] == "DICHIARAZIONE_REDDITI" and "is_innovative_startup" in need["skip_profile"]
    assert cp.required_for("CAPITALI")["document"] == "BILANCIO" and len(cp.required_for("CAPITALI")["fin_required"]) == 6


def test_profile_overview_adapts_to_the_company_type_and_lists_the_quick_questions():
    owner = "tipo-impresa-test"
    cp.update_profile(owner, {"legal_name": "Rossi e C.", "vat_number": "12345678903", "legal_form": "S.N.C.", "ateco_code": "47.11", "region": "Puglia", "employees": 3})
    cp.update_financials(owner, 2025, {"revenue_eur": 400000, "personnel_eur": 90000})
    ov = cp.overview(owner)
    assert ov["company_type"] == "PERSONE" and ov["document"]["kind"] == "DICHIARAZIONE_REDDITI"
    assert not [m for m in ov["missing"] if m["scope"] == "financial"] and not [m for m in ov["missing"] if m["key"] == "is_innovative_startup"]
    assert ov["completeness_pct"] == 100
    q = {x["key"]: x for x in ov["quick"]["fields"]}
    assert q["company_type"]["answered"] is True and q["company_type"]["source"]["origin"] == "DERIVED" and q["durc_regular"]["answered"] is False and "is_innovative_startup" not in q
    assert cp.profile_values(owner)["is_innovative_startup"] is False
    with pytest.raises(cp.ProfileError):
        cp.update_profile(owner, {"company_type": "SPA"})
    cp.update_profile(owner, {"founders_age": "U35", "company_status": "DA_COSTITUIRE", "durc_regular": "no"})
    vals = cp.profile_values(owner)
    assert vals["founders_under35"] is True and vals["founders_under40"] is True                       # una sola domanda: meno di 35 anni implica meno di 40
    assert vals["company_status"] == "DA_COSTITUIRE" and vals["durc_regular"] is False
    cp.update_profile(owner, {"founders_age": "U40"})
    assert cp.profile_values(owner)["founders_under35"] is False and cp.profile_values(owner)["founders_under40"] is True
    cp.update_profile(owner, {"founders_age": "OVER40"})
    assert cp.profile_values(owner)["founders_under40"] is False
    with pytest.raises(cp.ProfileError):
        cp.update_profile(owner, {"founders_age": "boh"})
    assert "founders_under35" not in {f["key"] for f in cp.overview(owner)["fields"]} and "founders_under40" not in {f["key"] for f in cp.overview(owner)["fields"]}


def test_a_sole_trader_never_reads_the_word_balance_sheet():
    owner = "ditta-test"
    cp.update_profile(owner, {"legal_form": "Impresa individuale", "legal_name": "Bianchi Mario", "vat_number": "12345678903", "ateco_code": "47.11", "region": "Lazio", "employees": 0})
    assert cp.company_type_of(owner) == "DITTA"
    assert cp.say(owner, "Mancano i dati di bilancio: carica un bilancio nel profilo o inserisci i costi dell'ultimo esercizio") == "Mancano i dati della dichiarazione dei redditi: inserisci ricavi e spese di personale dell'ultimo periodo d'imposta"
    out = cp.localize(owner, {"forecast": {"categories": [{"explanation": ["Nel bilancio 2024 il personale era 1 €, dai due ultimi bilanci risulta"], "source": {"filename": "Bilancio_2025.pdf"}}]}})
    assert out["forecast"]["categories"][0]["explanation"][0] == "Nella dichiarazione dei redditi 2024 il personale era 1 €, dalle due ultime dichiarazioni dei redditi risulta"
    assert out["forecast"]["categories"][0]["source"]["filename"] == "Bilancio_2025.pdf"                # i nomi dei file non si toccano
    assert cp.say("capitali-test", "Nel bilancio 2024") == "Nel bilancio 2024"                           # le società di capitali leggono «bilancio»
    ov = cp.overview(owner)
    assert ov["document"]["kind"] == "DICHIARAZIONE_REDDITI" and all("bilanci" not in m["label"].lower() for m in ov["missing"])
