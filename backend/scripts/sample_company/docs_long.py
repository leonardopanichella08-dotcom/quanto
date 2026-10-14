"""Documenti ufficiali e contrattuali lunghi: dichiarazioni fiscali (REDDITI SC, IRAP, IVA), contratto di locazione, relazione tecnica sul credito d'imposta, estratto conto, libro soci, piano di ammortamento."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import List, Sequence, Tuple

from . import ledger as LG
from . import model as M
from . import people as P
from .bil_nota import E
from .pdfkit import Doc, cents, pct, units

CO = M.COMPANY
U = units


def _w(d: Doc) -> float:
    return d.width / 2.8346


def _rows(d: Doc, title: str, items: Sequence[Tuple[str, str, object]], font: float = 7.6) -> None:
    """Quadro di una dichiarazione: righe (rigo, descrizione, importo); un importo None o 0 è mostrato come «-»."""
    W = _w(d)
    d.H1(title)
    rows = [["Rigo", "Descrizione", "Importo (euro)"]]
    for rigo, desc, val in items:
        rows.append([rigo, desc, U(val) if isinstance(val, (int, float)) and val else (val if isinstance(val, str) else "-")])
    d.table(rows, [20, W - 56, 36], align_right_from=2, font=font, zebra=True)


def _frontespizio(d: Doc, kind: str, year: int, protocol: str) -> None:
    W = _w(d)
    d.table([["Dato", "Valore"], ["Contribuente", CO["name"]], ["Codice fiscale e partita IVA", CO["vat"]], ["Sede legale", f"{CO['street']}, {CO['zip']} {CO['city'].title()} ({CO['prov']})"], ["Codice attività", CO["ateco"]],
             ["Natura giuridica", "Società a responsabilità limitata (codice 1)"], ["Periodo d'imposta", f"01/01/{year} - 31/12/{year}"], ["Tipo di dichiarazione", "Ordinaria"], ["Rappresentante firmatario", f"Giulia Ferraris - {P.BY_ID['M001']['cf']}"],
             ["Intermediario incaricato", "Studio commercialista incaricato (dati di prova) - impegno alla presentazione del " + date(year + 1, 10, 28).strftime("%d/%m/%Y")], ["Protocollo telematico", protocol], ["Data di presentazione", date(year + 1, 10, 30).strftime("%d/%m/%Y")]],
            [66, W - 66], align_right_from=9, zebra=True, head=False)


# ================================================================================================ REDDITI SC
def redditi(path: Path, y: int = 2024) -> Path:
    p, b = M.pl(y), M.balance(y)
    t = p["tax"]
    d = Doc(path, f"Modello REDDITI SC {y + 1}", CO["name"], f"REDDITI SC {y + 1} - periodo d'imposta {y}")
    W = _w(d)
    d.title_block(f"MODELLO REDDITI SC {y + 1}", f"Società di capitali ed enti commerciali - periodo d'imposta {y}")
    _frontespizio(d, "SC", y, f"25103012345678-{y}")
    d.H1("Quadri compilati")
    d.table([["Quadro", "Contenuto", "Compilato"], ["RF", "Reddito d'impresa per i soggetti in contabilità ordinaria", "Sì"], ["RN", "Determinazione del reddito e dell'imposta", "Sì"], ["RS", "Prospetti comuni e dati di bilancio", "Sì"], ["RU", "Crediti d'imposta concessi alle imprese", "Sì"],
             ["RQ", "Imposte sostitutive e altre imposte", "No"], ["RX", "Compensazioni, rimborsi e crediti", "Sì"], ["RV", "Variazioni di realtà aziendale (consolidato)", "No"], ["RT", "Plusvalenze di natura finanziaria", "No"], ["RH", "Redditi di partecipazione", "No"]], [24, W - 54, 30], align_right_from=9, font=8, zebra=True)
    d.page_break()
    items = [("RF1", "Codice attività (ATECO)", "62.01.00"), ("RF2", "Soggetto in contabilità ordinaria (codice)", "1"), ("RF3", "Opzione per il regime di trasparenza fiscale", "No"), ("RF4", "Redazione del bilancio secondo i principi contabili nazionali", "Sì"),
             ("RF5", "Utile dell'esercizio risultante dal conto economico", p["net"]), ("RF6", "Perdita dell'esercizio risultante dal conto economico", "-"), ("RF7", "Imposte sul reddito dell'esercizio (IRES e IRAP)", p["taxes"])]
    k = 8
    for label, amount in t["up"].items():
        items.append((f"RF{k}", f"Variazione in aumento: {label}", amount))
        k += 1
    for label in ("Ammortamenti non deducibili", "Accantonamenti non deducibili", "Compensi agli amministratori non corrisposti", "Interessi passivi indeducibili (art. 96 TUIR)", "Minusvalenze patrimoniali", "Perdite su crediti non deducibili", "Sopravvenienze passive indeducibili", "Costi relativi a beni a uso promiscuo",
                  "IMU non deducibile", "Spese di ristorazione e ospitalità oltre i limiti", "Altre variazioni in aumento"):
        items.append((f"RF{k}", f"Variazione in aumento: {label}", "-"))
        k += 1
    k = 40
    for label, amount in t["down"].items():
        items.append((f"RF{k}", f"Variazione in diminuzione: {label}", amount))
        k += 1
    for label in ("Plusvalenze patrimoniali rateizzate", "Quota esente di dividendi", "Super ammortamenti e iper ammortamenti (maggiorazioni)", "Proventi non computabili", "Deduzione dell'IMU sugli immobili strumentali", "Deduzione di spese per beni di pronto impiego", "Altre variazioni in diminuzione"):
        items.append((f"RF{k}", f"Variazione in diminuzione: {label}", "-"))
        k += 1
    items += [("RF61", "Reddito (perdita) dell'esercizio", t["taxable"]), ("RF62", "Perdite pregresse utilizzate", "-"), ("RF63", "Deduzione per aiuto alla crescita economica (ACE)", round(p["pre_tax"] * 0.03)), ("RF64", "Reddito imponibile di periodo", t["taxable"])]
    _rows(d, "QUADRO RF - REDDITO D'IMPRESA", items)
    d.page_break()
    items = [("RN1", "Reddito complessivo", t["taxable"]), ("RN2", "Perdite di periodi precedenti", "-"), ("RN3", "Deduzione ACE", round(p["pre_tax"] * 0.03)), ("RN4", "Erogazioni liberali deducibili", "-"), ("RN5", "Reddito imponibile", t["taxable"]), ("RN6", "Imposta lorda (aliquota 24%)", t["ires"]),
             ("RN7", "Detrazione per oneri e spese", "-"), ("RN8", "Credito d'imposta per ricerca e sviluppo utilizzato in compensazione", "-"), ("RN9", "Altri crediti d'imposta", "-"), ("RN10", "Ritenute d'acconto subite", "-"), ("RN11", "Acconti versati", round(t["ires"] * 0.9)),
             ("RN12", "Eccedenza di versamenti da periodi precedenti", "-"), ("RN13", "Imposta dovuta (saldo)", t["ires"] - round(t["ires"] * 0.9)), ("RN14", "Primo acconto per il periodo successivo (40%)", round(t["ires"] * 0.4)), ("RN15", "Secondo acconto per il periodo successivo (60%)", round(t["ires"] * 0.6)),
             ("RN16", "Addizionale IRES per società di comodo", "-"), ("RN17", "Totale imposta sul reddito", t["ires"])]
    _rows(d, "QUADRO RN - DETERMINAZIONE DEL REDDITO E DELL'IMPOSTA", items)
    items = [("RS1", "Codice fiscale della società o ente dichiarante", CO["vat"]), ("RS5", "Ricavi delle vendite e delle prestazioni (A1)", p["revenue"]), ("RS6", "Variazione dei lavori in corso (A3)", p["wip_delta"]), ("RS7", "Incrementi di immobilizzazioni per lavori interni (A4)", p["capitalized"]),
             ("RS8", "Altri ricavi e proventi (A5)", p["grants"] + p["other_income"]), ("RS9", "Totale valore della produzione", p["a_total"]), ("RS10", "Costi per materie prime e merci (B6)", p["b6"]), ("RS11", "Costi per servizi (B7)", p["b7"]), ("RS12", "Costi per godimento di beni di terzi (B8)", p["b8"]),
             ("RS13", "Costi per il personale (B9)", p["b9a"] + p["b9b"] + p["b9c"] + p["b9e"]), ("RS14", "Ammortamenti (B10a e B10b)", p["b10a"] + p["b10b"]), ("RS15", "Svalutazioni (B10d)", p["b10d"]), ("RS16", "Oneri diversi di gestione (B14)", p["b14"]), ("RS17", "Totale costi della produzione", p["b_total"]),
             ("RS18", "Differenza tra valore e costi della produzione", p["ebit"]), ("RS19", "Proventi e oneri finanziari", p["fin"]), ("RS20", "Risultato prima delle imposte", p["pre_tax"]), ("RS21", "Imposte sul reddito dell'esercizio", p["taxes"]), ("RS22", "Utile dell'esercizio", p["net"]),
             ("RS30", "Totale attivo", b["assets"]), ("RS31", "Immobilizzazioni immateriali", b["intang"]), ("RS32", "Immobilizzazioni materiali", b["tang"]), ("RS33", "Rimanenze", b["wip"]), ("RS34", "Crediti verso clienti", b["trade"]), ("RS35", "Disponibilità liquide", b["cash"]),
             ("RS40", "Patrimonio netto", b["pn"]), ("RS41", "Trattamento di fine rapporto", b["tfr"]), ("RS42", "Debiti verso banche", b["loan"]), ("RS43", "Debiti verso fornitori", b["suppliers"]), ("RS44", "Debiti tributari", b["tax_debt"]), ("RS50", "Numero medio dei dipendenti", M.EMPLOYEES[y])]
    _rows(d, "QUADRO RS - PROSPETTI COMUNI E DATI DI BILANCIO", items)
    d.page_break()
    items = [("RS401", "Aiuti di Stato: credito d'imposta ricerca e sviluppo", M.GRANTS[2] if y == 2024 else M.GRANTS[1]), ("RS402", "Aiuti de minimis ricevuti nel periodo", 10000 if y == 2024 else 5200), ("RS403", "Codice COR dell'aiuto", "COR-0000001" if y == 2024 else "COR-0000003"),
             ("RS404", "Aiuti incompatibili con il mercato interno da restituire", "-"), ("RS405", "Impresa in difficoltà (art. 2, punto 18, Reg. UE 651/2014)", "No")]
    _rows(d, "RS - PROSPETTO DEGLI AIUTI DI STATO (RS401-RS405)", items)
    items = [("RU1", "Codice del credito d'imposta (L2 - ricerca e sviluppo)", "L2"), ("RU2", "Credito residuo dalla precedente dichiarazione", M.GRANTS[1] if y == 2024 else M.GRANTS[0]), ("RU3", "Credito maturato nel periodo", M.GRANTS[2] if y == 2024 else M.GRANTS[1]), ("RU4", "Credito utilizzato in compensazione nel periodo", round(M.GRANTS[1] / 3)),
             ("RU5", "Credito residuo da utilizzare", (M.GRANTS[1] if y == 2024 else M.GRANTS[0]) + (M.GRANTS[2] if y == 2024 else M.GRANTS[1]) - round(M.GRANTS[1] / 3)), ("RU6", "Costi ammissibili di riferimento", M.GRANTS[2] * 10 if y == 2024 else M.GRANTS[1] * 10), ("RU7", "Aliquota del credito", "10%"),
             ("RU8", "Certificazione della relazione tecnica", "Sì"), ("RU9", "Comunicazione al MIMIT presentata", "Sì")]
    _rows(d, "QUADRO RU - CREDITI D'IMPOSTA", items)
    items = [("RX1", "Credito IRES risultante dalla presente dichiarazione", "-"), ("RX2", "Debito IRES risultante dalla presente dichiarazione", t["ires"] - round(t["ires"] * 0.9)), ("RX3", "Credito IVA da riportare", "-"), ("RX4", "Credito utilizzato in compensazione nel modello F24", round(M.GRANTS[1] / 3)),
             ("RX5", "Eccedenza di credito da riportare al periodo successivo", "-"), ("RX6", "Credito di cui si chiede il rimborso", "-")]
    _rows(d, "QUADRO RX - COMPENSAZIONI E RIMBORSI", items)
    d.H1("DICHIARAZIONI E IMPEGNO ALLA PRESENTAZIONE")
    d.P(f"Il sottoscritto Giulia Ferraris, in qualità di rappresentante legale, dichiara che la presente dichiarazione è stata redatta sulla base delle scritture contabili regolarmente tenute e conformi al bilancio d'esercizio al 31/12/{y}. "
        "Il soggetto incaricato si impegna a trasmettere in via telematica la dichiarazione all'Agenzia delle Entrate e a conservarne copia con la documentazione di supporto per il termine di decadenza dell'accertamento.", left=True)
    d.H1("RICEVUTA DI PRESENTAZIONE TELEMATICA")
    d.table([["Dato", "Valore"], ["Esito", "Dichiarazione ricevuta e accettata"], ["Protocollo telematico", f"25103012345678-{y}"], ["Data e ora di ricezione", f"30/10/{y + 1} 10:42:18"], ["Controlli formali", "Nessuna anomalia"], ["Presentazione di dichiarazione integrativa", "No"]], [58, W - 58], align_right_from=9, font=8, zebra=True, head=False)
    d.small("Estratto di prova: i valori derivano dal bilancio di prova dell'esercizio; protocolli e date sono fittizi.")
    return d.save()


# ================================================================================================ IRAP
def irap(path: Path, y: int = 2024) -> Path:
    p = M.pl(y)
    d = Doc(path, f"Dichiarazione IRAP {y + 1}", CO["name"], f"IRAP {y + 1} - periodo d'imposta {y}")
    W = _w(d)
    d.title_block(f"DICHIARAZIONE IRAP {y + 1}", f"Imposta regionale sulle attività produttive - periodo d'imposta {y}")
    _frontespizio(d, "IRAP", y, f"25103012345999-{y}")
    d.page_break()
    items = [("IC1", "Regime ordinario per le società di capitali", "Sì"), ("IC2", "Ricavi delle vendite e delle prestazioni (A1)", p["revenue"]), ("IC3", "Variazione dei lavori in corso su ordinazione (A3)", p["wip_delta"]), ("IC4", "Incrementi di immobilizzazioni per lavori interni (A4)", p["capitalized"]),
             ("IC5", "Contributi in conto esercizio (A5)", p["grants"]), ("IC6", "Altri ricavi e proventi (A5)", p["other_income"]), ("IC7", "Totale valore della produzione (A)", p["a_total"]), ("IC8", "Costi per materie prime, sussidiarie e di consumo (B6)", p["b6"]), ("IC9", "Costi per servizi (B7)", p["b7"]),
             ("IC10", "Costi per godimento di beni di terzi (B8)", p["b8"]), ("IC11", "Ammortamenti delle immobilizzazioni (B10a e B10b)", p["b10a"] + p["b10b"]), ("IC12", "Svalutazioni dei crediti (B10d)", p["b10d"]), ("IC13", "Oneri diversi di gestione (B14)", p["b14"]),
             ("IC14", "Costi per il personale (B9) - non deducibili in questo schema", p["b9a"] + p["b9b"] + p["b9c"] + p["b9e"]), ("IC20", "Differenza tra valore e costi della produzione (A - B)", p["ebit"]), ("IC21", "Variazioni in aumento: costi per lavoro autonomo occasionale e collaborazioni", "-"),
             ("IC22", "Variazioni in aumento: perdite su crediti e svalutazioni eccedenti", "-"), ("IC23", "Variazioni in diminuzione: ricavi non imponibili e contributi", p["grants"]), ("IC24", "Valore della produzione lorda", p["ebit"] + p["grants"] * 0)]
    _rows(d, "QUADRO IC - DETERMINAZIONE DEL VALORE DELLA PRODUZIONE NETTA (SOCIETA' DI CAPITALI)", items)
    items = [("IS1", "Valore della produzione netta", p["tax"]["irap_base"]), ("IS2", "Deduzione del costo residuo del personale dipendente a tempo indeterminato (art. 11, c. 4-octies)", p["b9a"] + p["b9b"] + p["b9c"] + p["b9e"]), ("IS3", "Deduzione dei contributi previdenziali e assistenziali (art. 11, c. 1, lett. a)", p["b9b"]),
             ("IS4", "Deduzione per apprendisti, disabili e personale in ricerca e sviluppo", "-"), ("IS5", "Valore della produzione netta dopo le deduzioni", p["tax"]["irap_base"]), ("IS6", "Aliquota ordinaria regionale (Piemonte)", "3,90%"), ("IS7", "Imposta lorda", p["irap"]),
             ("IS8", "Crediti d'imposta utilizzati", "-"), ("IS9", "Acconti versati", round(p["irap"] * 0.92)), ("IS10", "Saldo a debito", p["irap"] - round(p["irap"] * 0.92)), ("IS11", "Primo acconto per il periodo successivo", round(p["irap"] * 0.4)), ("IS12", "Secondo acconto per il periodo successivo", round(p["irap"] * 0.6))]
    _rows(d, "QUADRO IS - DETERMINAZIONE DELL'IMPOSTA", items)
    d.page_break()
    items = [("IR1", "Regione di prevalente imputazione del valore della produzione", "Piemonte"), ("IR2", "Quota di valore della produzione imputata al Piemonte", "100%"), ("IR3", "Valore della produzione imputato alla Regione", p["tax"]["irap_base"]), ("IR4", "Aliquota applicata", "3,90%"), ("IR5", "Imposta dovuta alla Regione", p["irap"]),
             ("IR6", "Eventuali maggiorazioni regionali", "-"), ("IR7", "Imposta a debito dopo gli acconti", p["irap"] - round(p["irap"] * 0.92))]
    _rows(d, "QUADRO IR - RIPARTIZIONE REGIONALE DELL'IMPOSTA", items)
    d.H1("PROSPETTO DEL PERSONALE E DELLE DEDUZIONI")
    q, imp, app = M.HEADCOUNT_SPLIT[y]
    d.table([["Categoria", "Numero medio", "Costo (euro)", "Deducibile"], ["Quadri", str(q), U(round((p["b9a"] + p["b9b"] + p["b9c"] + p["b9e"]) * 0.17)), "Sì"], ["Impiegati", str(imp), U(round((p["b9a"] + p["b9b"] + p["b9c"] + p["b9e"]) * 0.7)), "Sì"], ["Apprendisti", str(app), U(round((p["b9a"] + p["b9b"] + p["b9c"] + p["b9e"]) * 0.13)), "Sì"],
             ["Totale", str(M.EMPLOYEES[y]), U(p["b9a"] + p["b9b"] + p["b9c"] + p["b9e"]), ""]], [50, 28, 40, W - 118], bold_rows=[4], align_right_from=1, font=8)
    d.H1("RICEVUTA DI PRESENTAZIONE")
    d.table([["Dato", "Valore"], ["Esito", "Dichiarazione ricevuta e accettata"], ["Protocollo telematico", f"25103012345999-{y}"], ["Data e ora", f"30/10/{y + 1} 10:51:07"], ["Anomalie", "Nessuna"]], [58, W - 58], head=False, align_right_from=9, font=8, zebra=True)
    d.small("Documento di prova: i valori derivano dal bilancio di prova dell'esercizio.")
    return d.save()


# ================================================================================================ IVA annuale
def iva(path: Path, y: int = 2025) -> Path:
    d = Doc(path, f"Dichiarazione annuale IVA {y + 1}", CO["name"], f"IVA {y + 1} - anno d'imposta {y}")
    W = _w(d)
    d.title_block(f"DICHIARAZIONE ANNUALE IVA {y + 1}", f"Anno d'imposta {y}")
    _frontespizio(d, "IVA", y, f"26043000112233-{y}")
    inv = LG.invoices_issued(y)
    rec = LG.invoices_received(y)
    imp_e = sum(i["taxable"] for i in inv if i["vat"])
    non_imp = sum(i["taxable"] for i in inv if not i["vat"])
    vat_e = sum(i["vat"] for i in inv)
    imp_r = sum(i["taxable"] for i in rec)
    vat_r = sum(i["vat"] for i in rec)
    d.page_break()
    items = [("VE1", "Operazioni attive: regime ordinario", "Sì"), ("VE20", "Operazioni imponibili con aliquota del 22%", E(imp_e)), ("VE21", "Imposta su operazioni con aliquota del 22%", E(vat_e)), ("VE23", "Operazioni imponibili con altre aliquote", "-"),
             ("VE30", "Operazioni non imponibili (art. 7-ter, clienti esteri)", E(non_imp)), ("VE31", "Operazioni esenti (art. 10)", "-"), ("VE32", "Operazioni con applicazione del reverse charge (come cedente)", "-"), ("VE33", "Operazioni con scissione dei pagamenti (art. 17-ter)", E(sum(i["taxable"] for i in inv if i["customer"]["kind"] == "PA"))),
             ("VE38", "Totale delle operazioni attive", E(imp_e + non_imp)), ("VE39", "Totale imposta sulle operazioni attive", E(vat_e)), ("VE40", "Variazioni e arrotondamenti dell'imposta", "-")]
    d.H1("QUADRO VE - OPERAZIONI ATTIVE")
    d.table([["Rigo", "Descrizione", "Importo (euro)"]] + [list(map(str, i)) for i in items], [20, W - 56, 36], align_right_from=2, font=7.8, zebra=True)
    items = [("VF1", "Acquisti e importazioni: regime ordinario", "Sì"), ("VF13", "Acquisti interni imponibili con aliquota del 22% (imponibile)", E(imp_r)), ("VF14", "Imposta sugli acquisti interni con aliquota del 22%", E(vat_r)), ("VF15", "Acquisti intracomunitari di beni e servizi", "-"),
             ("VF16", "Acquisti con reverse charge (come cessionario)", "-"), ("VF17", "Importazioni", "-"), ("VF25", "Totale acquisti e importazioni imponibili", E(imp_r)), ("VF26", "Totale imposta sugli acquisti", E(vat_r)), ("VF27", "IVA non detraibile", "-"), ("VF28", "Variazioni e arrotondamenti", "-"),
             ("VF29", "Imposta detraibile", E(vat_r))]
    d.H1("QUADRO VF - OPERAZIONI PASSIVE")
    d.table([["Rigo", "Descrizione", "Importo (euro)"]] + [list(map(str, i)) for i in items], [20, W - 56, 36], align_right_from=2, font=7.8, zebra=True)
    d.page_break()
    d.H1("QUADRO VJ - OPERAZIONI PARTICOLARI")
    d.table([["Rigo", "Descrizione", "Importo (euro)"], ["VJ1", "Acquisti di beni e servizi da non residenti", "-"], ["VJ2", "Acquisti di oro e argento", "-"], ["VJ3", "Acquisti di rottami", "-"], ["VJ4", "Operazioni con San Marino", "-"], ["VJ5", "Operazioni triangolari", "-"]], [20, W - 56, 36], align_right_from=2, font=7.8, zebra=True)
    d.H1("QUADRO VL - LIQUIDAZIONI PERIODICHE E SALDO ANNUALE")
    rows = [["Mese", "Rigo", "Operazioni attive (euro)", "IVA a debito (euro)", "Operazioni passive (euro)", "IVA a credito (euro)", "Saldo del mese (euro)"]]
    for m in range(1, 13):
        e = [i for i in inv if i["date"].month == m]
        r_ = [i for i in rec if i["date"].month == m]
        dv, cr = sum(i["vat"] for i in e), sum(i["vat"] for i in r_)
        rows.append([["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"][m - 1], f"VL{m}", E(sum(i["taxable"] for i in e)), E(dv), E(sum(i["taxable"] for i in r_)), E(cr), E(dv - cr)])
    rows.append(["Totale", "VL13", E(imp_e + non_imp), E(vat_e), E(imp_r), E(vat_r), E(vat_e - vat_r)])
    d.table(rows, [24, 14, 32, 28, 32, 28, W - 158], bold_rows=[13], align_right_from=2, font=7.6, zebra=True)
    d.table([["Rigo", "Descrizione", "Importo (euro)"], ["VL30", "Totale imposta dovuta", E(vat_e)], ["VL31", "Totale imposta detraibile", E(vat_r)], ["VL32", "IVA dovuta", E(vat_e - vat_r)], ["VL33", "IVA a credito", "-"], ["VL38", "Versamenti periodici effettuati (con interessi del 1% per i trimestrali: non applicabile)", E(vat_e - vat_r)],
             ["VL39", "Acconto IVA di dicembre", E(round((vat_e - vat_r) / 12 * 0.88))], ["VL40", "IVA da versare o a credito dopo acconto", "-"]], [20, W - 56, 36], align_right_from=2, font=7.8, zebra=True)
    d.page_break()
    d.H1("COMUNICAZIONI DEI DATI DELLE LIQUIDAZIONI PERIODICHE (LIPE)")
    rows = [["Trimestre", "Data di invio", "Operazioni attive (euro)", "Operazioni passive (euro)", "IVA esigibile (euro)", "IVA detratta (euro)", "Saldo (euro)", "Protocollo"]]
    for q in range(4):
        e = [i for i in inv if (i["date"].month - 1) // 3 == q]
        r_ = [i for i in rec if (i["date"].month - 1) // 3 == q]
        dv, cr = sum(i["vat"] for i in e), sum(i["vat"] for i in r_)
        sent = [date(y, 5, 31), date(y, 9, 16), date(y, 11, 30), date(y + 1, 2, 28)][q]
        rows.append([f"{q + 1}° trimestre {y}", sent.strftime("%d/%m/%Y"), E(sum(i["taxable"] for i in e)), E(sum(i["taxable"] for i in r_)), E(dv), E(cr), E(dv - cr), f"LIPE-{y}-{q + 1}0{q + 3}77"])
    d.table(rows, [24, 20, 28, 28, 26, 24, 22, W - 172], align_right_from=2, font=7, zebra=True)
    d.H1("QUADRO VX - DETERMINAZIONE DELL'IVA DOVUTA O A CREDITO")
    d.table([["Rigo", "Descrizione", "Importo (euro)"], ["VX1", "IVA dovuta", E(vat_e - vat_r)], ["VX2", "IVA a credito", "-"], ["VX3", "Credito IVA precedente utilizzato", "-"], ["VX4", "Versamenti eseguiti nell'anno", E(vat_e - vat_r)], ["VX5", "Importo da versare / a credito", "-"], ["VX6", "Credito IVA da riportare all'anno successivo", "-"], ["VX7", "Credito IVA chiesto a rimborso", "-"]],
            [20, W - 56, 36], align_right_from=2, font=7.8, zebra=True)
    d.H1("VOLUME D'AFFARI E DATI DI SINTESI")
    d.table([["Dato", "Valore"], ["Volume d'affari dell'anno", E(imp_e + non_imp)], ["Percentuale di operazioni verso clienti esteri", f"{non_imp / (imp_e + non_imp) * 100:.1f}%".replace(".", ",")], ["Percentuale di operazioni con pubbliche amministrazioni (scissione dei pagamenti)", f"{sum(i['taxable'] for i in inv if i['customer']['kind'] == 'PA') / (imp_e + non_imp) * 100:.1f}%".replace(".", ",")],
             ["Numero di fatture emesse", str(len(inv))], ["Numero di fatture ricevute", str(len(rec))], ["Plafond e dichiarazioni d'intento ricevute", "Nessuno"]], [W - 50, 50], align_right_from=1, font=8, zebra=True)
    d.small("Documento di prova: gli importi derivano dai registri IVA di prova.")
    return d.save()


# ================================================================================================ piano di ammortamento
def ammortamento(path: Path) -> Path:
    d = Doc(path, "Piano di ammortamento del finanziamento", CO["name"], "Finanziamento chirografario - piano di ammortamento")
    W = _w(d)
    d.title_block("PIANO DI AMMORTAMENTO DEL FINANZIAMENTO CHIROGRAFARIO", "Importo originario euro 300.000,00 - erogato il 30/09/2020 - 28 rate trimestrali di capitale costanti - tasso variabile Euribor a tre mesi + 2,10 punti")
    d.H1("Condizioni contrattuali")
    d.table([["Condizione", "Dettaglio"], ["Banca finanziatrice", "Istituto di credito di prova (ABI 03069)"], ["Numero del contratto", "FIN-2020-0098713"], ["Natura del finanziamento", "Chirografario a medio termine, per sostenere investimenti e capitale circolante"],
             ["Garanzia", "Fondo centrale di garanzia per le PMI, 80% dell'importo finanziato (commissione una tantum già versata)"], ["Rimborso", "28 rate trimestrali posticipate di capitale (10.714,29 euro) più interessi, 31/03, 30/06, 30/09 e 31/12"], ["Preammortamento", "Nessuno"],
             ["Tasso", "Euribor a tre mesi (media del mese precedente) più 2,10 punti; floor a zero"], ["Spese di istruttoria", "0,50% (1.500,00 euro) trattenute all'erogazione"], ["Rimborso anticipato", "Consentito senza penali con preavviso di 15 giorni"], ["Covenant", "Nessuno"],
             ["Imposta sostitutiva", "0,25% (750,00 euro) assolta all'erogazione"]], [50, W - 50], align_right_from=9, font=8, zebra=True)
    d.page_break()
    d.H1("Piano di rimborso")
    rows = [["N.", "Data", "Debito iniziale", "Quota capitale", "Interessi", "Rata totale", "Debito residuo", "Tasso"]]
    left = 300000.0
    cap = 300000 / 28
    totc = toti = 0.0
    for k in range(1, 29):
        y = 2020 + (9 + 3 * k - 1) // 12
        m = (9 + 3 * k - 1) % 12 + 1
        day = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
        rate = 0.0210 + (-0.0 if y <= 2021 else (0.012 if y == 2022 else (0.036 if y == 2023 else (0.033 if y == 2024 else 0.022))))
        interest = round(left * rate / 4, 2)
        q = round(cap, 2) if k < 28 else round(left, 2)
        rows.append([str(k), f"{day:02d}/{m:02d}/{y}", cents(left), cents(q), cents(interest), cents(q + interest), cents(left - q), f"{rate * 100:.2f}%".replace(".", ",")])
        left = round(left - q, 2)
        totc += q
        toti += interest
    rows.append(["", "Totale", "", cents(totc), cents(toti), cents(totc + toti), "", ""])
    d.table(rows, [8, 22, 28, 26, 22, 26, 28, W - 160], bold_rows=[len(rows) - 1], align_right_from=2, font=7.4, zebra=True)
    d.page_break()
    d.H1("Riepilogo annuale")
    d.table([["Anno", "Capitale rimborsato (euro)", "Debito residuo al 31/12 (euro)", "Interessi stimati (euro)"], ["2020", cents(10714.29), cents(289285.71), cents(1990)], ["2021", cents(42857.16), cents(246428.55), cents(5700)], ["2022", cents(42857.16), cents(203571.39), cents(7450)], ["2023", cents(42857.16), cents(160714.23), cents(9100)],
             ["2024", cents(42857.16), cents(117857.07), cents(6200)], ["2025", cents(42857.16), cents(75000.0), cents(4300)], ["2026", cents(45000.0), cents(30000.0), cents(2600)], ["2027", cents(30000.0), cents(0.0), cents(1100)]], [24, 50, 54, W - 128], align_right_from=1, font=8, zebra=True)
    d.P("Il piano riportato nei bilanci d'esercizio considera dal 2023 rate di 11.250 euro: dopo la rinegoziazione del 30/06/2022 l'importo delle rate residue è stato rideterminato su 24 rate trimestrali con ultima scadenza il 30/09/2027, mantenendo invariata la garanzia del Fondo centrale.", left=True)
    d.small("Documento di prova: i tassi storici sono indicativi.")
    return d.save()


# ================================================================================================ estratto conto
def estratto_conto(path: Path) -> Path:
    d = Doc(path, "Estratto conto bancario - agosto 2026", CO["name"], "Estratto conto - agosto 2026")
    W = _w(d)
    d.title_block("ESTRATTO CONTO BANCARIO - AGOSTO 2026", "Conto corrente ordinario n. 000123456789 - Banca prima (istituto di prova) - IBAN " + P.iban("0001234567"))
    r = LG.rng("ec-2026-08")
    bal0 = 311842.17
    bal = bal0
    ops: List[tuple] = []
    cust = list(LG.customers())
    for k in range(52):
        c = r.choice(cust[:44])
        ops.append((r.randint(1, 31), f"Bonifico ricevuto {c['name'][:38]} - pag. fattura {2026}/{r.randint(40, 330):04d}", 0, round(r.uniform(900, 23800), 2)))
    for k in range(60):
        s = r.choice(list(LG.suppliers()))
        ops.append((r.randint(1, 31), f"Bonifico a {s['name'][:38]} - fattura {r.randint(1000, 9999)}/26", round(r.uniform(180, 9400), 2), 0))
    ops += [(1, "Addebito canone di locazione sede di via Garibaldi", 4500.0, 0), (1, "Addebito canone di locazione unità locale di corso Francia", 1450.0, 0), (5, "Addebito SDD canone leasing autovetture", 1100.0, 0), (10, "Commissioni e spese di tenuta conto", 48.2, 0),
            (16, "Pagamento F24 - ritenute, IVA e contributi di luglio", 52432.0, 0), (21, "Accredito POS e incassi carte", 0, 2430.5), (26, "Bonifico stipendi di agosto (cumulativo, 17 dipendenti)", 41230.6, 0), (28, "Addebito carta di credito aziendale", 3120.4, 0), (31, "Competenze di liquidazione interessi", 0, 31.7),
            (12, "Addebito rata finanziamento chirografario (quota trimestrale)", 0, 0), (7, "Imposta di bollo su conto corrente", 34.2, 0), (14, "Commissioni su bonifici SEPA", 22.5, 0), (18, "Addebito assicurazione responsabilità civile professionale", 2860.0, 0)]
    ops = [o for o in ops if o[2] or o[3]]
    ops.sort(key=lambda o: (o[0], o[1]))
    rows = [["Data", "Valuta", "Descrizione", "Dare", "Avere", "Saldo"]]
    dare_tot = avere_tot = 0.0
    for day, desc, dare, avere in ops:
        bal = round(bal - dare + avere, 2)
        dare_tot += dare
        avere_tot += avere
        rows.append([f"{day:02d}/08/2026", f"{min(31, day + 1):02d}/08/2026", desc, cents(dare) if dare else "", cents(avere) if avere else "", cents(bal)])
    d.table(rows, [18, 18, W - 112, 24, 24, 28], align_right_from=3, font=6.9, zebra=True)
    d.table([["Riepilogo", "Importo (euro)"], ["Saldo iniziale al 01/08/2026", cents(bal0)], ["Totale movimenti in dare", cents(round(dare_tot, 2))], ["Totale movimenti in avere", cents(round(avere_tot, 2))], ["Saldo finale al 31/08/2026", cents(bal)], ["Numero di movimenti", str(len(ops))],
             ["Fido accordato (affidamento di conto)", cents(100000)], ["Fido utilizzato", cents(0)]], [W - 40, 40], bold_rows=[4], font=8, align_right_from=1)
    d.small("Estratto di prova: soggetti e importi sono fittizi.")
    return d.save()


# ================================================================================================ contratto di locazione
CLAUSES = [
    ("Premesse", "Il locatore è proprietario dell'immobile descritto all'articolo 2 e dichiara di averne la piena disponibilità, libero da pesi, vincoli, ipoteche e diritti di terzi che ne impediscano l'uso convenuto. Il conduttore dichiara di aver visitato l'immobile, di averne verificato lo stato e di ritenerlo idoneo all'uso pattuito. Le premesse costituiscono parte integrante del contratto."),
    ("Oggetto della locazione", "Il locatore concede in locazione al conduttore l'unità immobiliare sita in Torino, via Giuseppe Garibaldi 28, ai piani secondo e terzo, composta da uffici, sala riunioni, locale server, area ristoro e servizi igienici, per una superficie calpestabile complessiva di 420 metri quadrati, oltre a otto posti auto nell'autorimessa interrata. L'immobile è identificato al catasto fabbricati con i dati indicati nell'allegato A."),
    ("Destinazione d'uso", "L'immobile è destinato esclusivamente a uffici, studi professionali e attività di sviluppo e consulenza informatica. È vietato mutare la destinazione d'uso, subaffittare o cedere il contratto a terzi senza il preventivo consenso scritto del locatore, salvo quanto previsto dall'articolo 36 della legge 392/1978 in caso di cessione dell'azienda."),
    ("Durata e rinnovo", "La locazione ha durata di sei anni dal 1° gennaio 2023 al 31 dicembre 2028 e si rinnova tacitamente per ulteriori sei anni se nessuna delle parti comunica disdetta con lettera raccomandata o posta elettronica certificata almeno dodici mesi prima della scadenza. Il locatore può negare il rinnovo alla prima scadenza solo per i motivi indicati dall'articolo 29 della legge 392/1978."),
    ("Canone", "Il canone annuo è convenuto in 54.000,00 euro, da pagare in dodici rate mensili anticipate di 4.500,00 euro entro il giorno cinque di ogni mese, mediante bonifico bancario sul conto indicato dal locatore. Il canone non può essere compensato con crediti vantati dal conduttore, né il pagamento può essere sospeso per qualsiasi motivo."),
    ("Aggiornamento del canone", "Dal secondo anno il canone è aggiornato annualmente nella misura del 75% della variazione dell'indice ISTAT dei prezzi al consumo per le famiglie di operai e impiegati. L'aggiornamento opera automaticamente senza necessità di richiesta del locatore, a decorrere dal mese di gennaio di ogni anno, fino a un massimo del 4% annuo."),
    ("Oneri accessori", "Sono a carico del conduttore le spese di riscaldamento e raffrescamento, di pulizia e illuminazione delle parti comuni, di portierato, di manutenzione ordinaria dell'ascensore e le altre spese condominiali di cui all'articolo 9 della legge 392/1978, in base alla tabella millesimale allegata. Il conduttore versa acconti trimestrali di 1.800,00 euro, con conguaglio a consuntivo entro sessanta giorni dall'approvazione del rendiconto condominiale."),
    ("Deposito cauzionale", "A garanzia dell'esatto adempimento delle obbligazioni il conduttore ha versato un deposito cauzionale infruttifero di 5.850,00 euro, che il locatore restituirà entro sessanta giorni dalla riconsegna dell'immobile, previa verifica dello stato dei luoghi e del pagamento di tutte le somme dovute."),
    ("Fidejussione bancaria", "Il conduttore ha consegnato una fidejussione bancaria a prima richiesta di 27.000,00 euro, pari a sei mensilità, con scadenza al 30 giugno 2029, a garanzia degli obblighi di pagamento. La fidejussione è rinnovata a ogni scadenza finché non siano cessate tutte le obbligazioni del conduttore."),
    ("Consegna e stato dell'immobile", "L'immobile è consegnato nello stato di fatto e di diritto in cui si trova, come risulta dal verbale di consegna allegato, con gli impianti elettrico, idraulico, di climatizzazione e di rete dati funzionanti. Il conduttore si obbliga a riconsegnarlo, alla scadenza, nello stato in cui lo ha ricevuto, salvo il normale deperimento d'uso."),
    ("Manutenzione ordinaria e straordinaria", "Sono a carico del conduttore le riparazioni di piccola manutenzione e quelle derivanti da uso improprio; sono a carico del locatore le riparazioni straordinarie, quelle relative alla struttura, alla copertura e agli impianti centralizzati. Il conduttore comunica tempestivamente ogni guasto o danno e consente l'accesso al locatore per le verifiche e i lavori necessari."),
    ("Migliorie e addizioni", "Il conduttore può eseguire migliorie o modifiche non strutturali solo con il consenso scritto del locatore. Le migliorie eseguite restano acquisite all'immobile alla scadenza senza diritto a indennità o rimborsi, ferma la facoltà del locatore di pretendere il ripristino dello stato originario dei luoghi a spese del conduttore."),
    ("Impianti e dotazioni informatiche", "Il conduttore è autorizzato a installare cablaggi strutturati, apparati di rete, un locale server con impianto di continuità e sistema di condizionamento dedicato, e a eseguire le opere necessarie nel rispetto della normativa antincendio e di sicurezza. L'impianto di videosorveglianza è installato dal conduttore nel rispetto della disciplina sul controllo a distanza dei lavoratori."),
    ("Assicurazioni e responsabilità", "Il conduttore stipula e mantiene per tutta la durata una polizza di responsabilità civile verso terzi con massimale di almeno 2.000.000 di euro e una polizza incendio e furto sui propri beni. Il conduttore è responsabile dei danni causati all'immobile da fatto proprio, dei dipendenti e dei visitatori, e tiene indenne il locatore da pretese di terzi."),
    ("Sicurezza e conformità", "Il conduttore garantisce il rispetto della normativa in materia di salute e sicurezza sul lavoro, prevenzione incendi e tutela ambientale per le attività svolte. Il locatore consegna il certificato di prestazione energetica (classe energetica C) e la documentazione di conformità degli impianti, riportati nell'allegato D."),
    ("Subentro e cessione", "In caso di cessione, affitto o conferimento dell'azienda o di fusione o scissione del conduttore, il contratto prosegue con il nuovo titolare, con obbligo di comunicazione al locatore entro trenta giorni. Il locatore può opporsi per gravi motivi, tra cui la mancanza di adeguate garanzie di solvibilità del subentrante."),
    ("Recesso del conduttore", "Il conduttore può recedere in qualsiasi momento con preavviso di sei mesi da comunicarsi con raccomandata o posta elettronica certificata, ove ricorrano gravi motivi. Il recesso senza gravi motivi è ammesso dal secondo anno con preavviso di dodici mesi e il pagamento, a titolo di corrispettivo, di tre mensilità di canone."),
    ("Risoluzione per inadempimento", "Il mancato pagamento anche di una sola rata del canone o degli oneri accessori decorsi venti giorni dalla scadenza, la violazione della destinazione d'uso o del divieto di sublocazione, e le altre ipotesi previste dall'articolo 5 della legge 392/1978, danno diritto al locatore di chiedere la risoluzione del contratto, salvo il risarcimento del danno."),
    ("Prelazione e diritto di preferenza", "Al conduttore spetta il diritto di prelazione in caso di vendita dell'immobile locato ai sensi degli articoli 38 e 39 della legge 392/1978. Il locatore comunica al conduttore, con raccomandata, il corrispettivo, le condizioni e le modalità di pagamento della vendita progettata."),
    ("Indennità di avviamento", "Alla cessazione del rapporto per cause diverse dall'inadempimento, dalla disdetta del conduttore e dal recesso, il conduttore ha diritto a un'indennità pari a diciotto mensilità dell'ultimo canone corrisposto, ai sensi dell'articolo 34 della legge 392/1978, nei limiti e alle condizioni ivi previsti."),
    ("Registrazione e imposte", "Il contratto è registrato in via telematica entro trenta giorni dalla stipula. L'imposta di registro è ripartita in parti uguali tra le parti; le relative spese sono anticipate dal locatore, che ne chiede il rimborso del cinquanta per cento al conduttore. L'imposta di bollo è a carico del conduttore."),
    ("Trattamento dei dati personali", "Le parti si danno reciprocamente atto che i dati personali contenuti nel presente contratto sono trattati per le sole finalità connesse alla sua esecuzione, nel rispetto del regolamento (UE) 2016/679, e dichiarano di aver ricevuto l'informativa prevista dalla normativa."),
    ("Comunicazioni", "Tutte le comunicazioni tra le parti sono validamente effettuate a mezzo posta elettronica certificata agli indirizzi indicati in epigrafe o con lettera raccomandata con ricevuta di ritorno. Ogni variazione dell'indirizzo è comunicata per iscritto."),
    ("Legge applicabile e foro competente", "Il contratto è regolato dalla legge italiana e, per quanto non previsto, dalla legge 27 luglio 1978, n. 392 e dal codice civile. Per ogni controversia è competente in via esclusiva il Foro di Torino, salvo il tentativo preliminare di mediazione previsto dalla normativa."),
]


def contratto(path: Path) -> Path:
    d = Doc(path, "Contratto di locazione ad uso non abitativo", CO["name"], "Contratto di locazione - sede legale di via Garibaldi 28")
    W = _w(d)
    d.title_block("CONTRATTO DI LOCAZIONE DI IMMOBILE AD USO DIVERSO DA QUELLO ABITATIVO", "Sede legale di via Giuseppe Garibaldi 28, Torino - ai sensi della legge 27 luglio 1978, n. 392")
    d.P(f"Tra la società Immobiliare Garibaldi 28 S.r.l. (di seguito «locatore»), con sede in Torino, in persona del legale rappresentante pro tempore, e la società {CO['name']}, con sede in Torino, {CO['street']}, codice fiscale e partita IVA {CO['vat']}, "
        "in persona dell'amministratore unico Giulia Ferraris (di seguito «conduttore»), si conviene e si stipula quanto segue. (Soggetti e dati catastali sono di prova.)", left=True)
    for k, (t, tx) in enumerate(CLAUSES, 1):
        d.H2(f"Articolo {k} - {t}")
        d.P(tx)
        if k in (5, 7):
            d.table([["Voce economica", "Importo annuo (euro)", "Importo mensile (euro)"], ["Canone base", cents(54000), cents(4500)], ["Acconto spese condominiali e riscaldamento", cents(7200), cents(600)], ["Totale esborso periodico", cents(61200), cents(5100)]], [W - 80, 40, 40], bold_rows=[3], align_right_from=1, font=8)
    d.P("Letto, confermato e sottoscritto in Torino, il 12 dicembre 2022. Il locatore: Immobiliare Garibaldi 28 S.r.l. Il conduttore: Giulia Ferraris, amministratore unico. Ai sensi degli articoli 1341 e 1342 c.c. le parti approvano specificamente gli articoli 3, 4, 5, 6, 8, 10, 15, 17 e 21.", left=True)
    d.page_break()
    d.title_block("ALLEGATO A - DATI CATASTALI E DESCRIZIONE")
    d.table([["Dato", "Valore"], ["Comune", "Torino"], ["Indirizzo", "Via Giuseppe Garibaldi 28"], ["Foglio / particella / subalterno", "1180 / 245 / 31 e 32"], ["Categoria catastale", "A/10 - uffici e studi privati"], ["Classe e consistenza", "3 - 11 vani"], ["Rendita catastale", "euro 4.820,00"],
             ["Piano", "Secondo e terzo"], ["Superficie calpestabile", "420 mq"], ["Posti auto", "Otto, nell'autorimessa interrata (box 12-19)"], ["Certificato di prestazione energetica", "Classe C - EPgl,nren 98 kWh/mq anno - valido fino al 2032"], ["Dichiarazioni di conformità degli impianti", "Elettrico, idrico e termico del 2019; impianto antincendio del 2022"]], [66, W - 66], align_right_from=9, font=8, zebra=True)
    d.H1("ALLEGATO B - TABELLA MILLESIMALE (ESTRATTO)")
    d.table([["Tipo di spesa", "Millesimi", "Spesa annua stimata (euro)"], ["Spese generali", "62,40", cents(3120)], ["Riscaldamento e raffrescamento", "71,80", cents(3590)], ["Ascensore", "58,30", cents(580)], ["Portierato e pulizia scale", "62,40", cents(1490)], ["Autorimessa", "41,10", cents(420)], ["Totale spese accessorie stimate", "", cents(9200)]],
            [W - 80, 30, 50], bold_rows=[6], align_right_from=1, font=8)
    d.H1("ALLEGATO C - VERBALE DI CONSEGNA E INVENTARIO DEGLI IMPIANTI")
    d.table([["Impianto o dotazione", "Stato alla consegna", "Note"], ["Impianto elettrico", "Funzionante", "Quadri a norma, punti rete in tutti gli uffici"], ["Impianto di climatizzazione", "Funzionante", "Quattro unità canalizzate"], ["Impianto idrico e servizi igienici", "Funzionante", "Tre servizi, uno per disabili"],
             ["Ascensore", "Funzionante", "Verifica biennale ASL in regola"], ["Impianto antincendio", "Funzionante", "Estintori e illuminazione di emergenza"], ["Pavimenti e pareti", "Buono", "Tinteggiatura recente"], ["Serramenti", "Buono", "Doppio vetro"]], [60, 44, W - 104], align_right_from=9, font=8, zebra=True)
    d.H1("ALLEGATO D - REGOLAMENTO DEL CONDOMINIO (ESTRATTO)")
    for n, tx in enumerate(["Le parti comuni non possono essere ingombrate da arredi o materiali.", "Gli orari di apertura dello stabile sono dalle 7:30 alle 20:30 nei giorni feriali; l'accesso fuori orario è consentito con badge.", "Le unità destinate ad uffici non possono essere usate per attività rumorose o moleste.",
                            "I rifiuti sono depositati negli appositi contenitori differenziati.", "I lavori di manutenzione che interessano le parti comuni sono preventivamente comunicati all'amministratore.", "La sosta nell'autorimessa è consentita solo nel box assegnato."], 1):
        d.P(f"Art. {n}. {tx}")
    d.small("Contratto di prova: soggetti, dati catastali e importi sono fittizi.")
    return d.save()


# ================================================================================================ libro soci
def libro_soci(path: Path) -> Path:
    d = Doc(path, "Libro dei soci", CO["name"], "Libro dei soci - estratto al 31/12/2025")
    W = _w(d)
    d.title_block("LIBRO DEI SOCI", f"{CO['name']} - estratto vidimato, aggiornato al 31/12/2025")
    d.H1("Elenco dei soci")
    d.table([["Socio", "Codice fiscale", "Quota", "Valore nominale (euro)", "Data iscrizione", "Titolo"], ["FERRARIS GIULIA", P.BY_ID["M001"]["cf"], "60%", "30.000,00", "14/03/2016", "Sottoscrizione all'atto costitutivo e aumento di capitale"],
             ["BERTOLOTTI MARCO", P.fiscal_code("Bertolotti", "Marco", date(1979, 3, 14), True, "L219"), "40%", "20.000,00", "14/03/2016", "Sottoscrizione all'atto costitutivo e aumento di capitale"]], [34, 40, 14, 30, 24, W - 142], align_right_from=9, font=8)
    d.H1("Movimenti del capitale sociale")
    d.table([["Data", "Operazione", "Capitale prima", "Capitale dopo", "Delibera"], ["14/03/2016", "Costituzione", "-", "10.000,00", "Atto costitutivo, notaio in Torino (dati di prova)"], ["29/04/2021", "Aumento di capitale a pagamento e con riserve", "10.000,00", "50.000,00", "Assemblea straordinaria, verbale notarile"]], [24, 66, 30, 30, W - 150], align_right_from=2, font=8)
    d.P("L'aumento di capitale del 2021 è stato sottoscritto per 25.000 euro mediante utilizzo di riserve di utili e per 15.000 euro con nuovi conferimenti in denaro dei due soci in proporzione alle quote. Non esistono vincoli, pegni, usufrutti o patti parasociali sulle quote; lo statuto non prevede clausole di prelazione diverse da quelle di legge né di gradimento oltre quanto previsto per le quote di S.r.l.", left=True)
    d.H1("Assemblee dei soci")
    rows = [["Data", "Tipo", "Ordine del giorno", "Presenti", "Esito"]]
    for y in (2022, 2023, 2024, 2025):
        rows.append([f"28/04/{y + 1}", "Ordinaria", f"Approvazione del bilancio {y} e destinazione dell'utile", "100% del capitale", "Approvato all'unanimità"])
    rows += [["29/04/2022", "Ordinaria", "Rinnovo della carica dell'amministratore unico", "100% del capitale", "Approvato all'unanimità"], ["29/04/2021", "Straordinaria", "Aumento del capitale sociale a 50.000 euro", "100% del capitale", "Approvato all'unanimità"]]
    d.table(rows, [24, 28, W - 130, 38, 40], align_right_from=9, font=8, zebra=True)
    d.H1("Dividendi distribuiti")
    rows = [["Esercizio", "Delibera", "Dividendo totale (euro)", "A G. Ferraris (60%)", "A M. Bertolotti (40%)", "Data di pagamento"]]
    for y, div in ((2022, 40000), (2023, 60000), (2024, 80000), (2025, 90000)):
        rows.append([str(y), f"Assemblea del 28/04/{y + 1}", cents(div), cents(div * 0.6), cents(div * 0.4), f"15/06/{y + 1}"])
    d.table(rows, [20, 38, 34, 32, 34, W - 158], align_right_from=2, font=8, zebra=True)
    d.H1("Decisioni dei soci e dell'organo amministrativo")
    d.table([["Data", "Organo", "Oggetto"], ["30/09/2020", "Amministratore unico", "Approvazione del finanziamento di 300.000 euro con garanzia del Fondo centrale"], ["01/09/2021", "Amministratore unico", "Apertura dell'unità locale di corso Francia 114"], ["15/03/2023", "Amministratore unico", "Conferimento di procura a Matteo Gallo"],
             ["20/11/2023", "Amministratore unico", "Conferimento di procura a Paola Fontana"], ["12/12/2022", "Amministratore unico", "Stipula del contratto di locazione della sede di via Garibaldi 28 (6+6)"]], [26, 44, W - 70], align_right_from=9, font=8, zebra=True)
    d.small("Estratto di prova.")
    return d.save()


# ================================================================================================ relazione tecnica R&S
def relazione_rs(path: Path) -> Path:
    y = 2025
    d = Doc(path, "Relazione tecnica sul credito d'imposta ricerca e sviluppo", CO["name"], f"Relazione tecnica R&S {y}")
    W = _w(d)
    base = M.GRANTS[3] * 10
    d.title_block(f"RELAZIONE TECNICA - CREDITO D'IMPOSTA RICERCA E SVILUPPO {y}", "Art. 1, commi 198-206, legge 160/2019 - progetto «Atlas: motore di calcolo deterministico per la previsione dei costi e il recupero delle agevolazioni»")
    d.table([["Dato", "Valore"], ["Impresa", CO["name"]], ["Periodo di riferimento", f"01/01/{y} - 31/12/{y}"], ["Responsabile del progetto", "Matteo Gallo, responsabile sviluppo"], ["Redattore", "Giulia Ferraris, amministratore unico"], ["Data della relazione", f"20/03/{y + 1}"], ["Certificatore della relazione", "Revisore legale esterno (dati di prova)"],
             ["Costi ammissibili", cents(base)], ["Credito maturato (10%)", cents(M.GRANTS[3])]], [58, W - 58], align_right_from=9, font=8, zebra=True, head=False)
    d.H1("1. Descrizione del progetto")
    d.P("Il progetto ha l'obiettivo di sviluppare un motore di calcolo che stimi, a partire dal bilancio di un'impresa, i costi dell'anno successivo e il recupero ottenibile da bandi e agevolazioni, rispettando tetti, cumulo e limiti di aiuto, con un risultato riproducibile e verificabile. "
        "La novità rispetto allo stato dell'arte è la rappresentazione formale delle regole dei bandi come dati strutturati e la loro applicazione con aritmetica decimale e ottimizzazione lineare mista intera.")
    d.P("Le soluzioni disponibili si dividono in portali che elencano i bandi, privi di collegamento con i conti dell'impresa, e software di pianificazione finanziaria, che non conoscono le regole dei bandi. Nessuna delle soluzioni analizzate (venti prodotti, cfr. paragrafo 3) calcola l'importo recuperabile in modo riproducibile e con indicazione della fonte di ogni regola.")
    d.H1("2. Incertezza tecnico-scientifica")
    d.B(["<b>Rappresentazione delle regole.</b> Non era noto se regole eterogenee (percentuali, tetti per categoria, soglie, cumulo, finestre temporali) potessero essere descritte con un modello uniforme senza perdere informazioni rilevanti per il calcolo.",
         "<b>Riproducibilità e aritmetica.</b> Era incerta la possibilità di ottenere un risultato esatto, senza errori di arrotondamento, in un problema di ripartizione tra più fondi con vincoli di cumulo e doppio finanziamento.",
         "<b>Lettura dei documenti.</b> Era incerta l'affidabilità dell'estrazione automatica delle voci contabili da documenti reali eterogenei (testo e scansioni) e la possibilità di quantificarne l'incertezza.",
         "<b>Validità statistica.</b> Era incerto se la stima del recupero fosse sufficientemente vicina agli importi effettivamente ammessi (scostamento obiettivo inferiore al 10%)."])
    d.H1("3. Stato dell'arte e analisi comparativa")
    d.table([["Categoria di soluzione", "Prodotti esaminati", "Calcola il recupero?", "Riproducibile?", "Fonte per ogni regola?"], ["Portali di segnalazione dei bandi", "7", "No", "-", "No"], ["Software di budgeting per PMI", "6", "No", "Sì", "No"], ["Strumenti di consulenza assistita", "4", "In parte, manualmente", "No", "No"],
             ["Motori di regole generici", "3", "Sì, senza regole di bandi", "Sì", "No"]], [58, 34, 36, 24, W - 152], align_right_from=9, font=8, zebra=True)
    d.H1("4. Attività svolte nell'esercizio")
    acts = [("A1", "Modello formale delle regole dei bandi", "Ricerca industriale", "Gen-Giu", "Schema con 18 tipi di regola e verifica su 40 bandi"), ("A2", "Motore di ripartizione ottimale", "Sviluppo sperimentale", "Mar-Set", "Algoritmo con risultato deterministico e traccia dei passaggi"),
            ("A3", "Lettura dei documenti contabili", "Sviluppo sperimentale", "Apr-Nov", "Riconoscimento di bilanci, F24 e cedolini con indicazione dell'affidabilità"), ("A4", "Archivio delle regole con versionamento", "Sviluppo sperimentale", "Mag-Ott", "Versioni e fonti per ogni regola"),
            ("A5", "Validazione su casi reali", "Sviluppo sperimentale", "Set-Dic", "Scostamento medio del 7,8% su 15 imprese"), ("A6", "Registro firmato delle esecuzioni", "Sviluppo sperimentale", "Ott-Dic", "Catena di impronte verificabile")]
    d.table([["Att.", "Descrizione", "Natura", "Periodo", "Risultato"]] + [list(a) for a in acts], [12, 54, 34, 20, W - 120], align_right_from=9, font=7.8, zebra=True)
    for a, desc, nat, per, res in acts:
        d.H2(f"{a} - {desc}")
        d.P(f"<b>Obiettivo.</b> {desc}, nell'ambito del progetto Atlas, per ridurre l'incertezza tecnico-scientifica sopra indicata. <b>Metodo.</b> Le attività sono state condotte in cicli di sperimentazione di due settimane, con ipotesi, prototipo, misura e revisione; i risultati sono documentati nei verbali tecnici e nel repository del codice. "
            f"<b>Risultato.</b> {res}. <b>Natura dell'attività.</b> {nat}. <b>Periodo.</b> {per} {y}.")
    d.H1("5. Personale impiegato")
    rows = [["Matricola", "Ruolo", "Ore dedicate", "Costo orario (euro)", "Costo imputato (euro)"]]
    team = [("M002", "Responsabile sviluppo", 560), ("M003", "Sviluppatore senior", 820), ("M004", "Sviluppatore senior", 780), ("M014", "Data scientist", 940), ("M005", "Sviluppatore", 720), ("M007", "Sviluppatore", 640), ("M008", "Project manager", 380), ("M012", "UX designer", 420)]
    tot = 0
    for eid, role, hours in team:
        e = P.BY_ID[eid]
        rate = round(e["cost"] / 1720, 2)
        rows.append([eid, role, str(hours), cents(rate), cents(round(rate * hours, 2))])
        tot += round(rate * hours, 2)
    rows.append(["Totale", "", str(sum(h for _, _, h in team)), "", cents(tot)])
    d.table(rows, [20, W - 130, 26, 40, 44], bold_rows=[len(rows) - 1], align_right_from=2, font=8, zebra=True)
    d.H2("Ore dedicate per mese")
    rr = LG.rng("rs-ore")
    rows = [["Matricola"] + ["G", "F", "M", "A", "M", "G", "L", "A", "S", "O", "N", "D"] + ["Totale"]]
    for eid, role, hours in team:
        parts = LG.alloc(hours, [rr.uniform(0.6, 1.4) * (0.2 if k == 7 else 1) for k in range(12)])
        rows.append([eid] + [str(x) for x in parts] + [str(hours)])
    d.table(rows, [22] + [(W - 22 - 18) / 12] * 12 + [18], align_right_from=1, font=7.2, zebra=True)
    d.H1("6. Ricerca contrattuale e consulenze")
    cp = LG.alloc(base, [70, 18, 7, 5])
    rows = [["Fornitore", "Oggetto", "Fattura", "Data", "Importo (euro)"]]
    sup = [s for s in LG.suppliers() if s["category"] == "Consulenze informatiche"]
    parts = LG.alloc(cp[1], [40, 25, 20, 15])
    for k, (s, obj) in enumerate(zip(sup, ("Consulenza di data science e validazione statistica", "Revisione dell'architettura di sicurezza", "Test di penetrazione della piattaforma", "Supporto alla definizione del modello delle regole"))):
        rows.append([s["name"], obj, f"{y}/{210 + k * 37}", f"{15 + k * 6:02d}/{3 + k * 2:02d}/{y}", cents(parts[k])])
    rows.append(["Totale ricerca contrattuale e consulenze", "", "", "", cents(cp[1])])
    d.table(rows, [48, W - 134, 20, 20, 46], bold_rows=[len(rows) - 1], align_right_from=4, font=7.6, zebra=True)
    d.H1("7. Attrezzature e materiali")
    d.table([["Bene", "Quota di ammortamento imputata (euro)", "Quota di utilizzo nel progetto"], ["Server di calcolo e storage dedicato", cents(round(cp[2] * 0.55, 2)), "50%"], ["Dispositivi di test mobile", cents(round(cp[2] * 0.30, 2)), "100%"], ["Apparati di rete del laboratorio", cents(cp[2] - round(cp[2] * 0.55, 2) - round(cp[2] * 0.30, 2)), "50%"],
             ["Materiali e forniture per i prototipi", cents(cp[3]), "100%"]], [W - 90, 50, 40], align_right_from=1, font=8)
    d.H1("8. Costi ammissibili e credito maturato")
    d.table([["Voce di costo", "Importo (euro)"], ["Personale impiegato in attività di ricerca e sviluppo", cents(cp[0])], ["Ricerca contrattuale e consulenze tecniche", cents(cp[1])], ["Quote di ammortamento di attrezzature di laboratorio", cents(cp[2])], ["Materiali e forniture per i prototipi", cents(cp[3])],
             ["Totale costi ammissibili", cents(base)], ["Credito d'imposta (aliquota del 10%)", cents(M.GRANTS[3])]], [W - 40, 40], bold_rows=[5, 6], align_right_from=1, font=8)
    d.H1("9. Risultati e documentazione conservata")
    d.B(["Verbali tecnici dei cicli di sperimentazione (24 verbali).", "Repository del codice con cronologia delle modifiche e delle revisioni.", "Rapporto di validazione su 15 imprese (scostamento medio del 7,8%).", "Fogli di presenza mensili del personale firmati.", "Fatture e contratti delle consulenze e dei fornitori.",
         "Certificazione della relazione tecnica e comunicazione al MIMIT."])
    d.H1("10. Conclusioni")
    d.P("Le attività descritte rispettano i criteri di novità, creatività, incertezza, sistematicità e riproducibilità previsti dal Manuale di Frascati e dalla normativa. La relazione è predisposta dal responsabile di progetto e sottoscritta dal legale rappresentante; la certificazione contabile è affidata a un revisore esterno.")
    d.P("Torino, 20/03/2026. Il legale rappresentante: Giulia Ferraris. Il responsabile del progetto: Matteo Gallo.", left=True)
    return d.save()
