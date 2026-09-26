"""Estrazione dei riferimenti normativi da un testo (app.core.requirements_extractor.extract_legal_refs).

Prima di questi test l'estrattore riconosceva solo l'ordine «Legge n. 207 del 30/12/2024»: l'ordine di gran
lunga più comune nei testi ufficiali italiani, «Legge 30 dicembre 2024, n. 207» (data prima del numero), non
veniva trovato affatto — la causa concreta più probabile di bandi con «troppo poche leggi trovate»."""
from app.core.requirements_extractor import extract_legal_refs


def test_date_before_number_the_most_common_italian_form():
    text = "Ai sensi della Legge 30 dicembre 2024, n. 207, e del Decreto-Legge 17 marzo 2020, n. 18, convertito con modificazioni."
    refs = extract_legal_refs(text)
    assert "Legge n. 207 del 30 dicembre 2024" in refs
    assert "Decreto-Legge n. 18 del 17 marzo 2020" in refs


def test_number_before_date_still_recognized():
    text = "Vedi la Legge n. 207 del 30 dicembre 2024 e il Regolamento (UE) n. 2831/2023."
    refs = extract_legal_refs(text)
    assert "Legge n. 207 del 30 dicembre 2024" in refs
    assert "Regolamento (UE) n. 2831/2023" in refs


def test_bare_eu_regulation_without_parentheses():
    text = "Il regime rispetta il Regolamento UE n. 1407/2013 sugli aiuti de minimis."
    assert "Regolamento UE n. 1407/2013" in extract_legal_refs(text)


def test_new_kinds_dpr_deliberazione_direttiva():
    text = ("Il Decreto del Presidente della Repubblica 28 dicembre 2000, n. 445 disciplina le autocertificazioni. "
            "La Deliberazione 27 febbraio 2014, n. 12 individua le aree ammissibili. "
            "La Direttiva (UE) 12 dicembre 2018, n. 2002 regola l'efficienza energetica.")
    refs = extract_legal_refs(text)
    assert "Decreto del Presidente della Repubblica n. 445 del 28 dicembre 2000" in refs
    assert "Deliberazione n. 12 del 27 febbraio 2014" in refs
    assert "Direttiva (UE) n. 2002 del 12 dicembre 2018" in refs


def test_ambiguous_reference_without_date_or_year_is_discarded():
    assert extract_legal_refs("Come previsto dalla legge n. 27, si applica quanto segue.") == []


def test_most_cited_act_comes_first():
    text = "Legge 30 dicembre 2024, n. 207. " * 3 + "Decreto-Legge 17 marzo 2020, n. 18."
    refs = extract_legal_refs(text)
    assert refs[0] == "Legge n. 207 del 30 dicembre 2024"
