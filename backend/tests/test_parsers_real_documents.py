"""Cosa succede quando un documento è fatto come quelli veri: importi senza centesimi, costi esposti più volte, etichette ripetute, piè di pagina, F24 con la sezione INPS."""
import json

from app.core.fonte_c import parsers


def L(*rows, page=1):
    return [{"text": t, "page": page, "conf_min": 1.0, "conf_mean": 1.0, "top": i * 12, "words": []} for i, t in enumerate(rows)]


def test_amounts_in_units_are_read_as_the_first_number_at_the_end_of_the_line():
    a = parsers.amount_units
    assert str(a("1) ricavi delle vendite e delle prestazioni 1.583.200 1.327.900")) == "1583200.00"
    assert str(a("a) salari e stipendi 640.000 538.000")) == "640000.00"
    assert str(a("14) oneri diversi di gestione 9.800")) == "9800.00"
    assert str(a("Totale 1.414.350,00 1.184.950,00")) == "1414350.00"             # con i centesimi vale come prima
    assert a("Numero medio dei dipendenti per categoria 2025 2024") is None        # gli anni non sono importi
    assert a("Documento n. T 481726395") is None and a("Data 16/09/2026") is None


def test_a_balance_without_cents_is_read_and_a_second_cost_table_is_not_counted_twice():
    lines = L("Bilancio d'esercizio al 31/12/2025",
              "B) COSTI DELLA PRODUZIONE",
              "6) per materie prime, sussidiarie, di consumo e di merci 24.050 20.350",
              "7) per servizi 360.100 289.900",
              "9) per il personale 890.700 748.700",
              "a) salari e stipendi 640.000 538.000", "b) oneri sociali 190.400 160.100", "c) trattamento di fine rapporto 46.200 38.900", "e) altri costi 14.100 11.700",
              "Totale costi della produzione 1.275.0 1.058.0".replace("1.275.0", "1.274.850").replace("1.058.0", "1.058.650"),
              "Pagina 4 di 14",
              "ALLEGATO A - CONTO ECONOMICO ANALITICO",
              "B) COSTI DELLA PRODUZIONE",
              "Cancelleria e materiale di consumo 9.800,00", "Consulenze professionali informatiche e tecniche 86.500,00", "Salari e stipendi 640.000,00", "Oneri sociali 190.400,00",
              "Altri servizi non classificati 348.150,00", "Totale costi della produzione 1.274.850,00")
    out = parsers.parse_balance(lines)
    expense = [json.loads(f.value) for f in out if f.key == "expense_line"]
    # il blocco analitico (più dettagliato) e quello civilistico tornano entrambi con il totale: se ne usa uno solo
    assert sum(float(e["amount_eur"]) for e in expense) == 1274850.0
    descs = [e["description"].lower() for e in expense]
    assert len(descs) == len(set(descs)) and not any("pagina" in x for x in descs)         # nessun costo due volte, il piè di pagina non è un costo
    by = {f.key: f for f in out if f.key != "expense_line"}
    assert by["total_costs_eur"].value == "1274850.00" and by["total_costs_eur"].status == "AUTO"


def test_the_most_specific_label_wins_and_the_repeated_value_beats_the_detail_lines():
    lines = L("Ricavi delle vendite e delle prestazioni per categoria", "Sviluppo software 680.000 590.000", "Totale ricavi delle vendite e delle prestazioni 1.583.200 1.327.900",
              "A) VALORE DELLA PRODUZIONE", "1) ricavi delle vendite e delle prestazioni 1.583.200 1.327.900", "Ricavi delle vendite e delle prestazioni: canoni 475.000")
    by = {f.key: f for f in parsers.parse_balance(lines)}
    assert by["revenue_eur"].value == "1583200.00" and by["revenue_eur"].status == "AUTO"
    emp = parsers.parse_registry(L("INFORMAZIONI", "Addetti (dipendenti e indipendenti) 17 INPS", "di cui dipendenti 15", "Numero medio annuo di addetti 16,5"))
    assert {f.key: f.value for f in emp}["employees"] == "17"
    ateco = parsers.parse_registry(L("Codice ATECO attività prevalente 62.01.00", "Codice ATECO attività secondaria 62.02.00", "Altra attività secondaria 63.11.19"))
    assert {f.key: f.value for f in ateco}["ateco_code"] == "62.01.00"
    pay = parsers.parse_payslip(L("Totale competenze 2.980,77", "Totale competenze progressive 23.846,16", "Netto in busta 1.990,68"))
    assert {f.key: f.value for f in pay}["gross_monthly_eur"] == "2980.77"


def test_costs_that_no_grant_covers_are_classified_as_other_and_not_left_to_review():
    for d in ("Imposte e tasse indirette", "Quote associative e contributi a organismi di categoria", "Sopravvenienze passive ordinarie", "Erogazioni liberali", "Carburanti e lubrificanti",
              "Svalutazione dei crediti compresi nell'attivo circolante"):
        assert parsers.classify_cost(d)[0] == "OTHER", d
    assert parsers.classify_cost("Consulenze legali e fiscali")[0] == "CONSULTING"
    assert parsers.classify_cost("Svalutazione delle immobilizzazioni materiali")[0] is None          # due categorie in conflitto: decide una persona


def test_f24_reads_only_tax_sections_and_separates_compensated_credits():
    lines = L("MODELLO F24", "Data di pagamento 16/09/2026", "SEZIONE ERARIO", "Codice tributo Rateazione Anno Importi a debito Importi a credito",
              "1001 0008 2026 21.486,30", "SEZIONE INPS", "0100 DM10 0123456789 08/2026 - 08/2026 15.284,55", "SEZIONE REGIONI ED ENTI LOCALI", "3802 01 2026 310,20", "SALDO FINALE 21.796,50")
    rows = [json.loads(f.value) for f in parsers.parse_f24(lines)]
    assert [(r["codice_tributo"], r["importo_debito_eur"]) for r in rows] == [("1001", "21486.30"), ("3802", "310.20")]
