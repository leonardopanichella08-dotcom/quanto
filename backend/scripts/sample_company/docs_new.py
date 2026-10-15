"""Documenti che un'azienda vera porta allo studio e che QUANTO ora legge: visura aiuti del registro nazionale, preventivi dei fornitori, fatture elettroniche XML, bilancio XBRL,
bilancio di verifica esportato dal gestionale. Dati fittizi, coerenti con il resto dell'azienda di prova.

Il tracciato della visura aiuti e del bilancio XBRL è un tracciato di prova: riproduce le informazioni che contengono, non il formato ufficiale (da confrontare con un file vero)."""
from __future__ import annotations

import csv
import io
import zipfile
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List
from xml.sax.saxutils import escape

from . import ledger as LG
from . import model as M
from .pdfkit import Doc, cents

CO = M.COMPANY


def _w(d: Doc) -> float:
    return d.width / 2.8346


# ================================================================================================ visura aiuti dell'RNA
def aid_rows() -> List[Dict]:
    """Le concessioni dell'azienda (le stesse del registro degli aiuti in Excel): ente, misura, data, regime, importo, codice COR."""
    return [
        {"granted": date(2024, 4, 12), "entity": "Camera di Commercio di Torino", "measure": "Voucher digitalizzazione PMI", "regime": "de minimis", "amount": 10000, "cor": "COR-0000001"},
        {"granted": date(2025, 10, 3), "entity": "Regione Piemonte", "measure": "Contributo partecipazione fiere", "regime": "de minimis", "amount": 6500, "cor": "COR-0000002"},
        {"granted": date(2023, 6, 30), "entity": "Agenzia delle Entrate", "measure": "Credito d'imposta ricerca e sviluppo 2022", "regime": "credito d'imposta", "amount": M.GRANTS[0], "cor": "COR-0000011"},
        {"granted": date(2024, 6, 30), "entity": "Agenzia delle Entrate", "measure": "Credito d'imposta ricerca e sviluppo 2023", "regime": "credito d'imposta", "amount": M.GRANTS[1], "cor": "COR-0000012"},
        {"granted": date(2025, 6, 30), "entity": "Agenzia delle Entrate", "measure": "Credito d'imposta ricerca e sviluppo 2024", "regime": "credito d'imposta", "amount": M.GRANTS[2], "cor": "COR-0000013"},
        {"granted": date(2021, 5, 20), "entity": "MIMIT", "measure": "Nuova Sabatini: contributo in conto impianti", "regime": "esenzione", "amount": 4900, "cor": "COR-0000014"},
        {"granted": date(2022, 2, 1), "entity": "Ministero del Lavoro", "measure": "Esonero contributivo under 36", "regime": "esenzione", "amount": 3200, "cor": "COR-0000015"},
        {"granted": date(2023, 9, 14), "entity": "Fondimpresa", "measure": "Conto formazione: finanziamento corsi", "regime": "de minimis", "amount": 5200, "cor": "COR-0000003"},
        {"granted": date(2025, 3, 31), "entity": "INAIL", "measure": "Riduzione del premio OT23", "regime": "riduzione del premio", "amount": 1850, "cor": "COR-0000016"},
    ]


def visura_aiuti(path: Path) -> Path:
    d = Doc(path, "Registro Nazionale degli Aiuti - Visura aiuti", CO["name"], "RNA - Visura aiuti (formato di prova)")
    W = _w(d)
    d.title_block("REGISTRO NAZIONALE DEGLI AIUTI DI STATO", "VISURA AIUTI - aiuti individuali concessi all'impresa (documento di prova: non riproduce il tracciato ufficiale)")
    d.H1("Soggetto")
    d.table([["Dato", "Valore"], ["Codice fiscale", CO["vat"]], ["Denominazione", CO["name"]], ["Data della visura", "14/10/2026"], ["Richiesta da", "Legale rappresentante dell'impresa, accesso con identità digitale"],
             ["Periodo considerato", "Tutte le concessioni registrate (de minimis e altri regimi)"]], [46, W - 46], head=False, align_right_from=9, font=8.4, zebra=True)
    d.H1("Concessioni registrate")
    rows = [["Data concessione", "Ente e misura", "Regime", "Importo (euro)", "Codice COR"]]
    for a in sorted(aid_rows(), key=lambda x: x["granted"]):
        rows.append([a["granted"].strftime("%d/%m/%Y"), f"{a['entity']} - {a['measure']}", a["regime"], cents(a["amount"]), a["cor"]])
    d.table(rows, [24, W - 108, 26, 26, 32], align_right_from=3, font=7.6, zebra=True)
    dm = [a for a in aid_rows() if a["regime"] == "de minimis" and a["granted"] > date(2023, 10, 14)]
    d.H1("Riepilogo de minimis")
    d.table([["Voce", "Importo (euro)"], ["Aiuti de minimis nei tre anni precedenti la visura", cents(sum(a["amount"] for a in dm))], ["Massimale per impresa unica (Reg. UE 2023/2831)", cents(300000)],
             ["Margine residuo", cents(300000 - sum(a["amount"] for a in dm))]], [W - 40, 40], bold_rows=[3], align_right_from=1, font=8.4)
    d.small("La visura riporta le concessioni dell'impresa interrogata. Per le imprese collegate (impresa unica) serve una visura per ciascuna.")
    return d.save()


# ================================================================================================ preventivi dei fornitori
QUOTES = [
    ("P-2026-114", "Nuvola Datacenter S.r.l.", "Infrastruttura cloud: hosting e macchine virtuali, ambienti di test e backup", date(2026, 10, 2),
     [("Servizio di hosting e macchine virtuali, 12 mesi", 21600), ("Archiviazione e backup cifrati, 12 mesi", 9800), ("Apparati di test e collaudo ambienti", 17200)]),
    ("SW-7731", "Licenze Tecniche Italia S.r.l.", "Licenze software perpetue per sviluppo e test", date(2026, 10, 5),
     [("Licenze strumenti di sviluppo, 12 postazioni", 11200), ("Licenze strumenti di test automatico, 6 postazioni", 6200)]),
    ("A-2026-58", "Ufficio Moderno S.p.A.", "Macchine d'ufficio e arredi per la nuova area di sviluppo", date(2026, 10, 7),
     [("Postazioni di lavoro complete, 10 pezzi", 14800), ("Stampanti multifunzione, 2 pezzi", 3400), ("Arredi e sedute ergonomiche", 5000)]),
]


def preventivo(path: Path, k: int) -> Path:
    number, supplier, subject, when, lines = QUOTES[k]
    d = Doc(path, f"Preventivo {number}", supplier, f"Preventivo n. {number}")
    W = _w(d)
    net = sum(a for _, a in lines)
    d.title_block("PREVENTIVO", f"Preventivo n. {number}")
    d.table([["Dato", "Valore"], ["Preventivo n.", number], ["Data", when.strftime("%d/%m/%Y")], ["Valido fino al", (when + timedelta(days=60)).strftime("%d/%m/%Y")], ["Fornitore", supplier],
             ["Cliente", CO["name"]], ["Oggetto", subject]], [40, W - 40], head=False, align_right_from=9, font=8.6, zebra=True)
    rows = [["Descrizione", "Importo (euro)"]] + [[t, cents(a)] for t, a in lines]
    d.table(rows, [W - 40, 40], align_right_from=1, font=8.6, zebra=True)
    d.table([["Totale imponibile", cents(net)], ["IVA 22%", cents(round(net * 0.22, 2))], ["Totale", cents(round(net * 1.22, 2))]], [W - 40, 40], head=False, bold_rows=[0], font=8.6)
    d.small("Condizioni: pagamento a 30 giorni data fattura; consegna entro 45 giorni dall'ordine. Preventivo di prova.")
    return d.save()


# ================================================================================================ fatture elettroniche (FatturaPA)
def _invoice_xml(inv: Dict) -> str:
    s = inv["supplier"]
    vat_digits = "".join(ch for ch in s["vat"] if ch.isdigit())[-11:].rjust(11, "0")
    iso = inv["date"].isoformat()
    taxable = f"{inv['taxable'] / 100:.2f}"                                          # il registro tiene i centesimi
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<p:FatturaElettronica versione="FPR12" xmlns:p="http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2">'
            f'<FatturaElettronicaHeader><CedentePrestatore><DatiAnagrafici><IdFiscaleIVA><IdPaese>IT</IdPaese><IdCodice>{vat_digits}</IdCodice></IdFiscaleIVA>'
            f'<Anagrafica><Denominazione>{escape(s["name"])}</Denominazione></Anagrafica></DatiAnagrafici></CedentePrestatore>'
            f'<CessionarioCommittente><DatiAnagrafici><IdFiscaleIVA><IdPaese>IT</IdPaese><IdCodice>{CO["vat"]}</IdCodice></IdFiscaleIVA><Anagrafica><Denominazione>{escape(CO["name"])}</Denominazione></Anagrafica></DatiAnagrafici></CessionarioCommittente>'
            f'</FatturaElettronicaHeader><FatturaElettronicaBody><DatiGenerali><DatiGeneraliDocumento><TipoDocumento>TD01</TipoDocumento><Divisa>EUR</Divisa><Data>{iso}</Data><Numero>{escape(inv["protocol"])}</Numero></DatiGeneraliDocumento></DatiGenerali>'
            f'<DatiBeniServizi><DettaglioLinee><NumeroLinea>1</NumeroLinea><Descrizione>{escape(inv["desc"])}</Descrizione><Quantita>1.00</Quantita><PrezzoUnitario>{taxable}</PrezzoUnitario><PrezzoTotale>{taxable}</PrezzoTotale><AliquotaIVA>22.00</AliquotaIVA></DettaglioLinee>'
            f'<DatiRiepilogo><AliquotaIVA>22.00</AliquotaIVA><ImponibileImporto>{taxable}</ImponibileImporto><Imposta>{inv["vat"] / 100:.2f}</Imposta></DatiRiepilogo></DatiBeniServizi></FatturaElettronicaBody></p:FatturaElettronica>')


def fatture_xml_zip(path: Path, year: int = 2025) -> Path:
    """Tutte le fatture ricevute dell'anno, un file XML per fattura, in un archivio ZIP come lo scarica il gestionale."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for inv in LG.invoices_received(year):
            z.writestr(f"IT{CO['vat']}_{inv['protocol'].replace('/', '_')}.xml", _invoice_xml(inv))
    return path


# ================================================================================================ bilancio XBRL
def bilancio_xbrl(path: Path) -> Path:
    """Il conto economico 2024 e 2025 in un'istanza XBRL con i nomi degli elementi della tassonomia italiana (tracciato di prova)."""
    ctx, facts = [], []
    for y in (2025, 2024):
        p = M.pl(y)
        c = f"c{y}"
        ctx.append(f'<xbrli:context id="{c}"><xbrli:entity><xbrli:identifier scheme="http://www.agenziaentrate.gov.it">{CO["vat"]}</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:startDate>{y}-01-01</xbrli:startDate><xbrli:endDate>{y}-12-31</xbrli:endDate></xbrli:period></xbrli:context>')
        personnel = p["b9a"] + p["b9b"] + p["b9c"] + p["b9e"]
        for name, v in (("RicaviDelleVenditeEDelleprestazioni", p["revenue"]), ("TotaleValoreDellaProduzione", p["a_total"]), ("CostiDellaProduzionePerMateriePrimeSussidiarieDiConsumoEDiMerci", p["b6"]),
                        ("CostiDellaProduzionePerServizi", p["b7"]), ("CostiDellaProduzionePerGodimentoDiBeniDiTerzi", p["b8"]), ("TotaleCostiDellaProduzionePerIlPersonale", personnel),
                        ("TotaleCostiDellaProduzione", p["b_total"]), ("UtilePerditaDellEsercizio", p["net"])):
            facts.append(f'<itcc-ci:{name} contextRef="{c}" unitRef="EUR" decimals="0">{v}</itcc-ci:{name}>')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:itcc-ci="http://www.infocamere.it/itnn/fr/itcc/ci/2018-11-04" xmlns:link="http://www.xbrl.org/2003/linkbase">'
           + "".join(ctx) + '<xbrli:unit id="EUR"><xbrli:measure>iso4217:EUR</xbrli:measure></xbrli:unit>' + "".join(facts) + "</xbrli:xbrl>")
    path.write_text(xml, encoding="utf-8")
    return path


# ================================================================================================ bilancio di verifica esportato dal gestionale (CSV)
def bilancio_verifica_csv(path: Path, year: int = 2025) -> Path:
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";", lineterminator="\r\n")
    w.writerow(["Codice", "Conto", "Saldo iniziale", "Movimenti dare", "Movimenti avere", "Saldo finale"])
    fmt = lambda c: f"{c / 100:.2f}".replace(".", ",")
    for r in LG.trial_balance(year):
        w.writerow([r["code"], r["name"], fmt(r["opening"]), fmt(r["dare"]), fmt(r["avere"]), fmt(r["closing"])])
    path.write_bytes(buf.getvalue().encode("cp1252", errors="replace"))
    return path
