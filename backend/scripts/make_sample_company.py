"""Genera i documenti di un'azienda di prova COMPLETAMENTE FITTIZIA, coerenti tra loro, da caricare nel profilo per provare QUANTO.

Azienda: Meridiana Digital Solutions S.r.l. (Torino, software e consulenza informatica). Ogni documento riporta in calce
«Documento di prova – dati fittizi»: nomi, codici fiscali, partita IVA e importi sono inventati, non appartengono a nessuna persona o impresa reale.

Uso:  python scripts/make_sample_company.py [cartella di destinazione]
"""
from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

COMPANY = {
    "name": "MERIDIANA DIGITAL SOLUTIONS S.R.L.", "vat": "09871230012", "legal_form": "Società a responsabilità limitata", "ateco": "62.01.00",
    "ateco_desc": "Produzione di software non connesso all'edizione", "street": "Via Giuseppe Garibaldi 28", "zip": "10122", "city": "TORINO", "prov": "TO",
    "founded": "14/03/2016", "rea": "TO-1187342", "pec": "meridianadigital@pec-prova.it", "capital": "50.000,00", "addetti": 17,
}
FOOTER = "Documento di prova - dati fittizi generati per provare QUANTO. Nessun valore corrisponde a persone o imprese reali."


# ------------------------------------------------------------------------------------------------ utilità
def eur(x) -> str:
    q = Decimal(str(x)).quantize(Decimal("0.01"))
    s = f"{abs(q):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if q < 0 else "") + s


def vat_check(first10: str) -> str:
    """Cifra di controllo della partita IVA italiana."""
    s = 0
    for i, ch in enumerate(first10):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        s += d
    return str((10 - s % 10) % 10)


def fiscal_code(surname: str, name: str, birth: date, male: bool, town_code: str) -> str:
    """Codice fiscale con carattere di controllo corretto (per i dati inventati dei dipendenti)."""
    vowels, consonants = "AEIOU", "BCDFGHJKLMNPQRSTVWXYZ"

    def cons(s: str) -> str:
        return "".join(c for c in s.upper() if c in consonants)

    def vow(s: str) -> str:
        return "".join(c for c in s.upper() if c in vowels)

    sur = (cons(surname) + vow(surname) + "XXX")[:3]
    nc = cons(name)
    nm = (nc[0] + nc[2] + nc[3]) if len(nc) >= 4 else (nc + vow(name) + "XXX")[:3]
    month = "ABCDEHLMPRST"[birth.month - 1]
    day = birth.day + (0 if male else 40)
    base = f"{sur}{nm}{birth.year % 100:02d}{month}{day:02d}{town_code}"
    odd = dict(zip("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", [1, 0, 5, 7, 9, 13, 15, 17, 19, 21, 1, 0, 5, 7, 9, 13, 15, 17, 19, 21, 2, 4, 18, 20, 11, 3, 6, 8, 12, 14, 16, 10, 22, 25, 24, 23]))
    even = dict(zip("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", list(range(10)) + list(range(26))))
    total = sum(odd[c] if i % 2 == 0 else even[c] for i, c in enumerate(base))
    return base + chr(ord("A") + total % 26)


COMPANY["vat"] = "0987123001" + vat_check("0987123001")


class Page:
    """Foglio A4 con testo posizionato: etichetta a sinistra, valore a destra sulla stessa riga (si legge come «ETICHETTA valore»)."""

    def __init__(self, path: Path, title: str, subtitle: str = "", footer: bool = True):
        self.path, self.title, self.subtitle, self.footer = path, title, subtitle, footer
        self.c = canvas.Canvas(str(path), pagesize=A4)
        self.c.setTitle(title)
        self.w, self.h = A4
        self.y = 0.0
        self.n = 0
        self._new_page()

    def _new_page(self) -> None:
        if self.n:
            self._foot()
            self.c.showPage()
        self.n += 1
        c = self.c
        c.setFillColor(colors.HexColor("#1f3a5f"))
        c.rect(0, self.h - 62, self.w, 62, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, self.h - 30, self.title)
        if self.subtitle:
            c.setFont("Helvetica", 9)
            c.drawString(40, self.h - 47, self.subtitle)
        c.setFillColor(colors.black)
        self.y = self.h - 90

    def _foot(self) -> None:
        if self.footer:
            self.c.setFont("Helvetica-Oblique", 6.5)
            self.c.setFillColor(colors.HexColor("#666666"))
            self.c.drawString(40, 24, FOOTER)
            self.c.drawRightString(self.w - 40, 24, f"pag. {self.n}")
            self.c.setFillColor(colors.black)

    def need(self, space: float = 30) -> None:
        if self.y < 50 + space:
            self._new_page()

    def heading(self, text: str, size: float = 10.5) -> None:
        self.need(40)
        self.y -= 8
        self.c.setFont("Helvetica-Bold", size)
        self.c.drawString(40, self.y, text)
        self.c.setStrokeColor(colors.HexColor("#c8d0da"))
        self.c.line(40, self.y - 3, self.w - 40, self.y - 3)
        self.y -= 15

    def text(self, text: str, size: float = 9, bold: bool = False, indent: float = 0, gap: float = 13) -> None:
        self.need()
        self.c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        self.c.drawString(40 + indent, self.y, text)
        self.y -= gap

    def field(self, label: str, value: str, x_value: float = 210) -> None:
        self.need()
        self.c.setFont("Helvetica-Bold", 8.5)
        self.c.drawString(40, self.y, label)
        self.c.setFont("Helvetica", 9)
        self.c.drawString(x_value, self.y, value)
        self.y -= 14

    def row(self, label: str, *amounts: str, indent: float = 0, bold: bool = False, cols: Tuple[float, ...] = (420, 505)) -> None:
        self.need()
        self.c.setFont("Helvetica-Bold" if bold else "Helvetica", 8.5)
        self.c.drawString(40 + indent, self.y, label)
        for x, a in zip(cols, amounts):
            if a != "":
                self.c.drawRightString(x, self.y, a)
        self.y -= 12.5

    def space(self, n: float = 8) -> None:
        self.y -= n

    def save(self) -> Path:
        self._foot()
        self.c.save()
        return self.path


# ------------------------------------------------------------------------------------------------ bilanci
YEARS = (2023, 2024, 2025)
# (descrizione, voce CEE, importi 2022, 2023, 2024, 2025)  — 2022 serve solo per la colonna comparativa del bilancio 2023
COST_LINES: List[Tuple[str, str, Tuple[int, int, int, int]]] = [
    ("Cancelleria e materiale di consumo", "6", (6100, 7120, 8450, 9800)),
    ("Consulenze professionali informatiche e tecniche", "7", (27900, 38400, 61200, 86500)),
    ("Consulenze legali, fiscali e del lavoro", "7", (17100, 18200, 19600, 21800)),
    ("Compensi a professionisti e collaboratori esterni", "7", (33200, 41000, 52300, 64200)),
    ("Licenze software e servizi cloud", "7", (28800, 36500, 47900, 58600)),
    ("Energia elettrica e riscaldamento", "7", (13900, 14800, 13900, 14300)),
    ("Spese telefoniche e connettivita", "7", (8200, 8700, 9100, 9600)),
    ("Assicurazioni", "7", (9100, 9900, 10800, 11900)),
    ("Pubblicita e marketing", "7", (12300, 18600, 29400, 38700)),
    ("Corsi di formazione e aggiornamento professionale", "7", (6900, 9300, 14700, 18400)),
    ("Manutenzione e pulizia uffici", "7", (10600, 11200, 11900, 12800)),
    ("Spese di rappresentanza e trasferte", "7", (6400, 8900, 12300, 15600)),
    ("Affitto uffici e spese condominiali", "8", (42000, 48000, 54000, 54000)),
    ("Canoni di locazione operativa autovetture", "8", (4800, 7200, 10800, 13200)),
    ("Salari e stipendi", "9", (371000, 449000, 538000, 640000)),
    ("Oneri sociali", "9", (110400, 133600, 160100, 190400)),
    ("Trattamento di fine rapporto", "9", (26900, 32500, 38900, 46200)),
    ("Altri costi del personale (buoni pasto e welfare aziendale)", "9", (7100, 9400, 11700, 14100)),
    ("Ammortamento delle immobilizzazioni immateriali", "10", (11900, 15200, 19800, 22400)),
    ("Ammortamento delle immobilizzazioni materiali", "10", (17800, 21900, 27600, 31700)),
    ("Spese postali e di corriere", "14", (1500, 1700, 1900, 2100)),
]
HEADINGS = {"6": "6) per materie prime, sussidiarie, di consumo e di merci", "7": "7) per servizi", "8": "8) per godimento di beni di terzi",
            "9": "9) per il personale", "10": "10) ammortamenti e svalutazioni", "14": "14) oneri diversi di gestione"}
REVENUE = (900200, 1081400, 1327900, 1583200)
OTHER_INCOME_GRANTS = (6000, 12000, 31500, 42000)           # contributi in conto esercizio (credito d'imposta ricerca e sviluppo)
OTHER_INCOME_OTHER = (2100, 2900, 4200, 5800)
INT_INCOME = (210, 420, 980, 1450)
INT_EXPENSE = (11800, 11300, 10200, 8900)
EMPLOYEES = {2022: 9, 2023: 11, 2024: 13, 2025: 15}


def _idx(year: int) -> int:
    return year - 2022


def balance_figures(year: int) -> Dict[str, object]:
    i = _idx(year)
    cost_total = sum(v[i] for _, _, v in COST_LINES)
    a_total = REVENUE[i] + OTHER_INCOME_GRANTS[i] + OTHER_INCOME_OTHER[i]
    ebit = a_total - cost_total
    pre_tax = ebit + INT_INCOME[i] - INT_EXPENSE[i]
    ires = round(pre_tax * 0.24)
    irap = round((ebit + 0.0) * 0.039)
    net = pre_tax - ires - irap
    return {"costs": cost_total, "a_total": a_total, "ebit": ebit, "pre_tax": pre_tax, "ires": ires, "irap": irap, "net": net}


def make_balance(path: Path, year: int) -> Path:
    f_cur, f_prev = balance_figures(year), balance_figures(year - 1) if year > 2022 else None
    i, p = _idx(year), _idx(year) - 1
    cols = (440, 515)
    pg = Page(path, f"BILANCIO DI ESERCIZIO AL 31/12/{year}", f"{COMPANY['name']} - P.IVA {COMPANY['vat']} - Sede in {COMPANY['city'].title()} ({COMPANY['prov']}) {COMPANY['street']}")
    pg.text(f"Redatto in forma abbreviata ai sensi dell'art. 2435-bis del codice civile. Importi in euro. Esercizio chiuso al 31/12/{year}.", 8.5)
    pg.space(2)

    # --- stato patrimoniale (valori coerenti: attivo = passivo)
    eq = 118000
    equity_open: Dict[int, int] = {2022: eq}
    for y in (2022, 2023, 2024, 2025):
        equity_open[y] = eq
        eq += int(balance_figures(y)["net"])
    cap, legal = 50000, 10000
    def sp_values(y: int) -> Dict[str, int]:
        net = int(balance_figures(y)["net"])
        retained = equity_open[y] - cap - legal
        pn = cap + legal + retained + net
        tfr = int(sum(v[_idx(y)] for d, c, v in COST_LINES if d == "Trattamento di fine rapporto") * 3.4)
        debt_bank = max(0, 210000 - (y - 2022) * 45000)
        suppliers = int(sum(v[_idx(y)] for d, c, v in COST_LINES if c == "7") * 0.16)
        tax_debt = int(abs(int(balance_figures(y)["ires"])) + int(balance_figures(y)["irap"]) * 1.0) + 31000
        social = int(sum(v[_idx(y)] for d, c, v in COST_LINES if d == "Oneri sociali") / 6)
        other_debt = int(sum(v[_idx(y)] for d, c, v in COST_LINES if d == "Salari e stipendi") / 14)
        intang = 64000 + (y - 2022) * 14000
        tang = 92000 + (y - 2022) * 9000
        fin_assets = 8500
        receivables = int(REVENUE[_idx(y)] * 0.27)
        tax_credit = 24000 + (y - 2022) * 6000
        passive = pn + tfr + debt_bank + suppliers + tax_debt + social + other_debt + 4200
        cash = passive - (intang + tang + fin_assets + receivables + tax_credit + 6800)
        return {"intang": intang, "tang": tang, "fin": fin_assets, "recv": receivables, "taxcr": tax_credit, "cash": cash, "prepaid": 6800,
                "cap": cap, "legal": legal, "ret": retained, "net": net, "pn": pn, "tfr": tfr, "bank": debt_bank, "supp": suppliers, "taxd": tax_debt,
                "soc": social, "oth": other_debt, "accr": 4200, "assets": passive}
    cur, prev = sp_values(year), (sp_values(year - 1) if year > 2022 else None)

    def pair(key: str):
        return (eur(cur[key]), eur(prev[key]) if prev else "")

    pg.heading("STATO PATRIMONIALE - ATTIVO")
    pg.row("", f"31/12/{year}", f"31/12/{year - 1}", bold=True, cols=cols)
    pg.row("B) Immobilizzazioni", bold=True, cols=cols)
    pg.row("I - Immobilizzazioni immateriali", *pair("intang"), indent=10, cols=cols)
    pg.row("II - Immobilizzazioni materiali", *pair("tang"), indent=10, cols=cols)
    pg.row("III - Immobilizzazioni finanziarie", *pair("fin"), indent=10, cols=cols)
    pg.row("C) Attivo circolante", bold=True, cols=cols)
    pg.row("II - Crediti verso clienti", *pair("recv"), indent=10, cols=cols)
    pg.row("II - Crediti tributari", *pair("taxcr"), indent=10, cols=cols)
    pg.row("IV - Disponibilita liquide", *pair("cash"), indent=10, cols=cols)
    pg.row("D) Ratei e risconti attivi", *pair("prepaid"), cols=cols)
    pg.row("TOTALE ATTIVO", *pair("assets"), bold=True, cols=cols)

    pg.heading("STATO PATRIMONIALE - PASSIVO")
    pg.row("A) Patrimonio netto", *pair("pn"), bold=True, cols=cols)
    pg.row("I - Capitale", *pair("cap"), indent=10, cols=cols)
    pg.row("IV - Riserva legale", *pair("legal"), indent=10, cols=cols)
    pg.row("VI - Altre riserve", *pair("ret"), indent=10, cols=cols)
    pg.row("IX - Risultato di esercizio (a nuovo e utile)", *pair("net"), indent=10, cols=cols)
    pg.row("C) Trattamento di fine rapporto di lavoro subordinato", *pair("tfr"), bold=True, cols=cols)
    pg.row("D) Debiti", bold=True, cols=cols)
    pg.row("4 - Debiti verso banche", *pair("bank"), indent=10, cols=cols)
    pg.row("7 - Debiti verso fornitori", *pair("supp"), indent=10, cols=cols)
    pg.row("12 - Debiti tributari", *pair("taxd"), indent=10, cols=cols)
    pg.row("13 - Debiti verso istituti di previdenza", *pair("soc"), indent=10, cols=cols)
    pg.row("14 - Altri debiti", *pair("oth"), indent=10, cols=cols)
    pg.row("E) Ratei e risconti passivi", *pair("accr"), cols=cols)
    pg.row("TOTALE PASSIVO E PATRIMONIO NETTO", *pair("assets"), bold=True, cols=cols)

    # --- conto economico (schema art. 2425 c.c., con il dettaglio delle voci di costo)
    pg.heading("CONTO ECONOMICO")
    pg.row("", f"{year}", f"{year - 1}", bold=True, cols=cols)
    pg.row("A) VALORE DELLA PRODUZIONE", bold=True, cols=cols)
    pg.row("1) Ricavi delle vendite e delle prestazioni", eur(REVENUE[i]), eur(REVENUE[p]), indent=10, cols=cols)
    pg.row("5) altri ricavi e proventi:", indent=10, cols=cols)
    pg.row("contributi in conto esercizio", eur(OTHER_INCOME_GRANTS[i]), eur(OTHER_INCOME_GRANTS[p]), indent=22, cols=cols)
    pg.row("altri", eur(OTHER_INCOME_OTHER[i]), eur(OTHER_INCOME_OTHER[p]), indent=22, cols=cols)
    pg.row("Totale valore della produzione", eur(f_cur["a_total"]), eur(f_prev["a_total"]) if f_prev else "", bold=True, cols=cols)

    pg.row("B) COSTI DELLA PRODUZIONE", bold=True, cols=cols)
    for code in ("6", "7", "8", "9", "10", "14"):
        lines = [(d, v) for d, c, v in COST_LINES if c == code]
        pg.row(HEADINGS[code], eur(sum(v[i] for _, v in lines)), eur(sum(v[p] for _, v in lines)), indent=10, cols=cols)
        for d, v in lines:
            pg.row(d, eur(v[i]), eur(v[p]), indent=26, cols=cols)
    pg.row("Totale costi della produzione", eur(f_cur["costs"]), eur(f_prev["costs"]) if f_prev else "", bold=True, cols=cols)
    pg.row("Differenza tra valore e costi della produzione (A - B)", eur(f_cur["ebit"]), eur(f_prev["ebit"]) if f_prev else "", bold=True, cols=cols)

    pg.row("C) PROVENTI E ONERI FINANZIARI", bold=True, cols=cols)
    pg.row("16) altri proventi finanziari - interessi attivi", eur(INT_INCOME[i]), eur(INT_INCOME[p]), indent=10, cols=cols)
    pg.row("17) interessi e altri oneri finanziari", eur(-INT_EXPENSE[i]), eur(-INT_EXPENSE[p]), indent=10, cols=cols)
    pg.row("Risultato prima delle imposte", eur(f_cur["pre_tax"]), eur(f_prev["pre_tax"]) if f_prev else "", bold=True, cols=cols)
    pg.row("20) Imposte sul reddito dell'esercizio (IRES e IRAP)", eur(-(f_cur["ires"] + f_cur["irap"])), eur(-(f_prev["ires"] + f_prev["irap"])) if f_prev else "", indent=10, cols=cols)
    pg.row("21) UTILE (PERDITA) DELL'ESERCIZIO", eur(f_cur["net"]), eur(f_prev["net"]) if f_prev else "", bold=True, cols=cols)

    pg.heading("NOTA INTEGRATIVA (estratto)")
    pg.text("Criteri di valutazione: i criteri applicati sono quelli dell'art. 2426 c.c., invariati rispetto all'esercizio precedente.", 8.5)
    pg.text("Le immobilizzazioni immateriali (software sviluppato internamente) sono ammortizzate in 5 anni; le materiali in base alla vita utile stimata.", 8.5)
    pg.text("I contributi in conto esercizio si riferiscono al credito d'imposta per attivita di ricerca e sviluppo.", 8.5)
    pg.space(3)
    pg.text("Dati sull'occupazione", 9, bold=True)
    n = EMPLOYEES[year]
    managers = 1
    clerks = n - managers - 2
    pg.row("Quadri", str(managers), indent=10, cols=(300,))
    pg.row("Impiegati", str(clerks), indent=10, cols=(300,))
    pg.row("Apprendisti", "2", indent=10, cols=(300,))
    pg.row(f"Numero medio dei dipendenti {n}", indent=0, bold=True)
    pg.space(4)
    pg.text(f"L'organo amministrativo propone di destinare l'utile dell'esercizio, pari a euro {eur(f_cur['net'])}, a riserva straordinaria.", 8.5)
    return pg.save()


# ------------------------------------------------------------------------------------------------ visura
def make_registry(path: Path) -> Path:
    co = COMPANY
    pg = Page(path, "VISURA ORDINARIA DI SOCIETA' DI CAPITALI", "Estratto del Registro delle Imprese - Camera di Commercio di Torino (documento di prova)")
    pg.text(f"Data della visura: {date(2026, 10, 2).strftime('%d/%m/%Y')}", 8.5)
    pg.heading("INFORMAZIONI SULLA SOCIETA'")
    pg.field("DENOMINAZIONE:", co["name"])
    pg.field("FORMA GIURIDICA:", co["legal_form"])
    pg.field("PARTITA IVA:", co["vat"])
    pg.field("CODICE FISCALE:", co["vat"])
    pg.field("NUMERO REA:", co["rea"])
    pg.field("PEC:", co["pec"])
    pg.field("SEDE LEGALE:", f"{co['street']}, {co['zip']} {co['city']} ({co['prov']})")
    pg.field("DATA DI COSTITUZIONE:", co["founded"])
    pg.field("CAPITALE SOCIALE:", f"euro {co['capital']} interamente versato")
    pg.field("STATO ATTIVITA:", "Attiva - nessuna procedura concorsuale in corso")
    pg.heading("ATTIVITA'")
    pg.field("CODICE ATECO:", f"{co['ateco']}  {co['ateco_desc']}")
    pg.text("Attivita secondaria esercitata: consulenza informatica e gestione di strutture informatizzate.", 9)
    pg.text("Oggetto sociale: sviluppo, produzione e manutenzione di software, piattaforme di analisi dei dati e servizi di consulenza", 9)
    pg.text("informatica e organizzativa per imprese ed enti pubblici; formazione sui temi della trasformazione digitale.", 9)
    pg.heading("ADDETTI")
    pg.field("NUMERO ADDETTI:", f"{co['addetti']}  (soci lavoratori e dipendenti, al 30/06/2026)")
    pg.heading("AMMINISTRAZIONE E SOCI")
    pg.text("Amministratore unico: FERRARIS GIULIA - rappresentante dell'impresa - in carica fino a revoca", 9)
    pg.text("Soci: FERRARIS GIULIA quota 60% - BERTOLOTTI MARCO quota 40%", 9)
    pg.heading("ALBI E REGISTRI")
    pg.text("Iscritta alla sezione ordinaria del Registro delle Imprese. Non risulta iscritta alla sezione speciale delle start-up innovative.", 9)
    pg.text("Dimensione dichiarata: piccola impresa ai sensi della raccomandazione 2003/361/CE.", 9)
    return pg.save()


# ------------------------------------------------------------------------------------------------ buste paga
def irpef_month(gross: float, months: int = 14) -> Tuple[float, float, float]:
    inps = round(gross * 0.0919, 2)
    taxable = (gross - inps) * months
    tax = min(taxable, 28000) * 0.23 + max(0.0, min(taxable, 50000) - 28000) * 0.35 + max(0.0, taxable - 50000) * 0.43
    if taxable <= 15000:
        detr = 1955.0
    elif taxable <= 28000:
        detr = 1910 + 1190 * (28000 - taxable) / 13000
    elif taxable <= 50000:
        detr = 1910 * (50000 - taxable) / 22000
    else:
        detr = 0.0
    irpef = max(0.0, tax - detr) / months
    addizionali = taxable * 0.0201 / 12
    return inps, round(irpef, 2), round(addizionali, 2)


def make_payslip(path: Path, surname: str, name: str, level: str, gross: float, birth: date, male: bool, town: str, hired: str) -> Path:
    co = COMPANY
    cf = fiscal_code(surname, name, birth, male, town)
    inps, irpef, add = irpef_month(gross)
    net = round(gross - inps - irpef - add, 2)
    tfr = round(gross / 13.5, 2)
    pg = Page(path, "CEDOLINO PAGA - LIBRO UNICO DEL LAVORO", f"{co['name']} - P.IVA {co['vat']} - {co['street']}, {co['zip']} {co['city'].title()}")
    pg.heading("DATI ANAGRAFICI E CONTRATTUALI")
    pg.field("COGNOME E NOME:", f"{surname.upper()} {name.upper()}")
    pg.field("CODICE FISCALE:", cf)
    pg.field("DATA ASSUNZIONE:", hired)
    pg.field("CCNL:", "Commercio, Terziario Distribuzione e Servizi")
    pg.field("LIVELLO:", level)
    pg.field("MANSIONE:", "Impiegato - sviluppatore software" if level != "1" else "Quadro")
    pg.field("MENSILITA:", "14")
    pg.field("PERIODO DI RETRIBUZIONE:", "08/2026")
    pg.heading("COMPETENZE")
    pg.row("Retribuzione base (paga base + contingenza)", eur(round(gross * 0.86, 2)), cols=(505,))
    pg.row("Scatti di anzianita", eur(round(gross * 0.04, 2)), cols=(505,))
    pg.row("Superminimo individuale", eur(round(gross - round(gross * 0.86, 2) - round(gross * 0.04, 2), 2)), cols=(505,))
    pg.row(f"TOTALE COMPETENZE {eur(gross)}", bold=True)
    pg.heading("TRATTENUTE")
    pg.row("Contributi previdenziali INPS a carico del lavoratore (9,19%)", eur(inps), cols=(505,))
    pg.row("IRPEF lorda del mese al netto delle detrazioni", eur(irpef), cols=(505,))
    pg.row("Addizionale regionale e comunale", eur(add), cols=(505,))
    pg.row(f"TOTALE TRATTENUTE {eur(round(inps + irpef + add, 2))}", bold=True)
    pg.space(4)
    pg.row(f"NETTO IN BUSTA {eur(net)}", bold=True)
    pg.heading("RATEI E TFR")
    pg.row(f"QUOTA TFR {eur(tfr)}", indent=0)
    pg.row("Ferie e permessi residui al 31/08/2026: 11,5 giorni", indent=0)
    return pg.save()


# ------------------------------------------------------------------------------------------------ F24
def make_f24(path: Path, pay_date: str, month_ref: str, rows: List[Tuple[str, str, str, float]]) -> Path:
    co = COMPANY
    pg = Page(path, "MODELLO DI PAGAMENTO UNIFICATO F24 - SEZIONE ERARIO", f"Contribuente: {co['name']} - codice fiscale {co['vat']}")
    pg.text(f"Data di versamento: {pay_date}   -   Delega presentata tramite home banking (ricevuta di pagamento)", 8.5)
    pg.heading("SEZIONE ERARIO")
    pg.text("codice tributo   rateazione / mese di riferimento   anno di riferimento   importi a debito versati", 7.5, bold=True)
    total = 0.0
    for code, period, year, amount in rows:
        pg.text(f"{code}    {period}    {year}    {eur(amount)}", 9, indent=6)
        total += amount
    pg.space(4)
    pg.text(f"TOTALE A DEBITO VERSATO {eur(total)}", 9, bold=True)
    pg.heading("SEZIONE INPS")
    pg.text("DM10 - contributi previdenziali e assistenziali del mese di riferimento: versati con la stessa delega", 8.5)
    pg.text(f"Periodo di riferimento: {month_ref}", 8.5)
    return pg.save()


# ------------------------------------------------------------------------------------------------ bozza di candidatura
def make_draft(path: Path) -> Path:
    pg = Page(path, "PROGETTO ATLAS - DOMANDA DI CONTRIBUTO", "Piattaforma di analisi predittiva dei costi per le PMI - bozza interna di candidatura")
    pg.heading("1. DESCRIZIONE DEL PROGETTO")
    pg.text("Atlas e una piattaforma web che aiuta le piccole imprese a prevedere i propri costi e a individuare gli incentivi pubblici piu adatti.", 9)
    pg.text("Il progetto dura 12 mesi, coinvolge 6 persone del team e prevede un prototipo, una fase di test con 15 imprese e il rilascio commerciale.", 9)
    pg.heading("2. PIANO DEI COSTI")
    lines = [("Personale di progetto (6 persone, quota di tempo media 45%)", 168000), ("Consulenze specialistiche di data science", 36000),
             ("Licenze software e servizi cloud per lo sviluppo", 24000), ("Attrezzature informatiche e macchinari per il laboratorio dati", 28500),
             ("Spese di formazione del personale sui nuovi strumenti", 9000), ("Spese generali di progetto (affitto e utenze quota progetto)", 22400)]
    for d, v in lines:
        pg.row(d, eur(v), cols=(505,))
    pg.row(f"TOTALE COSTI PROGETTO {eur(sum(v for _, v in lines))}", bold=True)
    pg.heading("3. CRONOPROGRAMMA")
    pg.text("Mesi 1-3: analisi e progettazione. Mesi 4-8: sviluppo del prototipo. Mesi 9-11: test con le imprese pilota. Mese 12: rilascio.", 9)
    pg.heading("4. RISULTATI ATTESI")
    pg.text("Almeno 15 imprese pilota coinvolte e una riduzione stimata del 20% del tempo dedicato alla ricerca di incentivi.", 9)
    return pg.save()


# ------------------------------------------------------------------------------------------------ altri documenti (non letti, solo archiviati)
def make_durc(path: Path) -> Path:
    co = COMPANY
    pg = Page(path, "DOCUMENTO UNICO DI REGOLARITA' CONTRIBUTIVA (DURC)", "INPS - INAIL - Casse Edili (documento di prova)")
    pg.field("Numero protocollo:", "INAIL_48217763")
    pg.field("Data richiesta:", "01/09/2026")
    pg.field("Scadenza validita:", "29/12/2026")
    pg.field("Denominazione:", co["name"])
    pg.field("Codice fiscale:", co["vat"])
    pg.field("Sede legale:", f"{co['street']}, {co['zip']} {co['city'].title()}")
    pg.field("CCNL applicato:", "Commercio, Terziario Distribuzione e Servizi")
    pg.field("Dimensione aziendale:", "Da 6 a 15 addetti")
    pg.heading("ESITO")
    pg.text("Il documento risulta REGOLARE nei confronti di INPS e INAIL alla data della verifica.", 10, bold=True)
    pg.text("Il presente documento ha validita di 120 giorni dalla data di emissione.", 9)
    return pg.save()


def make_de_minimis(path: Path) -> Path:
    co = COMPANY
    pg = Page(path, "DICHIARAZIONE SOSTITUTIVA DI ATTO DI NOTORIETA' - AIUTI 'DE MINIMIS'", "Regolamento (UE) n. 2831/2024 - triennio 2024-2026 (documento di prova)")
    pg.text(f"Il sottoscritto Giulia FERRARIS, legale rappresentante di {co['name']}, P.IVA {co['vat']},", 9)
    pg.text("consapevole delle responsabilita penali previste in caso di dichiarazioni mendaci, dichiara che nel triennio in esame", 9)
    pg.text("l'impresa ha ricevuto i seguenti aiuti in regime de minimis:", 9)
    pg.heading("AIUTI RICEVUTI")
    pg.row("Voucher per la digitalizzazione delle PMI - Camera di Commercio - concesso il 12/04/2024", eur(10000), cols=(505,))
    pg.row("Contributo regionale per la partecipazione a fiere - concesso il 03/10/2025", eur(6500), cols=(505,))
    pg.row(f"TOTALE AIUTI NEL TRIENNIO {eur(16500)}", bold=True)
    pg.text("Massimale applicabile: euro 300.000,00 nell'arco di tre esercizi finanziari. Margine residuo dichiarato: euro 283.500,00.", 9)
    pg.text("L'impresa non e collegata ad altre imprese ai sensi dell'art. 2 del regolamento.", 9)
    return pg.save()


def make_business_plan(path: Path) -> Path:
    pg = Page(path, "BUSINESS PLAN 2026-2028", f"{COMPANY['name']} - sintesi per finanziatori e bandi (documento di prova)")
    pg.heading("1. L'AZIENDA")
    pg.text("Meridiana Digital Solutions sviluppa software e piattaforme di analisi dei dati per le PMI. Fondata nel 2016 a Torino, oggi conta 17 persone.", 9)
    pg.heading("2. OBIETTIVI DEL TRIENNIO")
    pg.row("", "2026", "2027", "2028", bold=True, cols=(350, 430, 510))
    pg.row("Ricavi previsti", eur(1860000), eur(2150000), eur(2480000), cols=(350, 430, 510))
    pg.row("Dipendenti previsti a fine anno", "19", "22", "25", cols=(350, 430, 510))
    pg.row("Investimenti in ricerca e sviluppo", eur(210000), eur(260000), eur(300000), cols=(350, 430, 510))
    pg.heading("3. INVESTIMENTI PREVISTI")
    pg.text("Piattaforma Atlas (analisi predittiva dei costi), potenziamento dell'infrastruttura cloud e formazione specialistica del team.", 9)
    pg.text("Fonti di copertura: autofinanziamento, contributi pubblici a fondo perduto e, per la quota residua, finanziamento bancario.", 9)
    return pg.save()


def make_xlsx_aiuti(path: Path) -> Path:
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Registro aiuti"
    ws.append(["Ente concedente", "Misura", "Base normativa", "Data concessione", "Importo (EUR)", "Regime", "Codice COR (prova)"])
    ws.append(["Camera di Commercio di Torino", "Voucher digitalizzazione PMI", "Reg. UE 2831/2024", "2024-04-12", 10000, "de minimis", "COR-0000001"])
    ws.append(["Regione Piemonte", "Contributo partecipazione fiere", "Reg. UE 2831/2024", "2025-10-03", 6500, "de minimis", "COR-0000002"])
    ws.append(["Agenzia delle Entrate", "Credito d'imposta ricerca e sviluppo 2025", "Art. 1 c. 198 L. 160/2019", "2026-06-30", 42000, "credito d'imposta", "-"])
    wb.save(path)
    return path


def make_xlsx_organico(path: Path) -> Path:
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Organico"
    ws.append(["Matricola", "Ruolo", "Livello CCNL", "Tipo contratto", "Data assunzione", "Ore settimanali", "Costo azienda annuo stimato (EUR)"])
    rows = [("M001", "Amministratore e direttore tecnico", "Quadro", "Indeterminato", "2016-03-14", 40, 78000), ("M002", "Responsabile sviluppo", "1", "Indeterminato", "2016-09-01", 40, 69000),
            ("M003", "Sviluppatore senior", "3", "Indeterminato", "2018-02-01", 40, 57000), ("M004", "Sviluppatore senior", "3", "Indeterminato", "2019-05-13", 40, 56500),
            ("M005", "Sviluppatore", "4", "Indeterminato", "2020-09-01", 40, 49500), ("M006", "Data analyst", "4", "Indeterminato", "2021-03-01", 40, 48800),
            ("M007", "Sviluppatore", "4", "Indeterminato", "2022-01-10", 40, 48000), ("M008", "Project manager", "2", "Indeterminato", "2022-06-01", 40, 61000),
            ("M009", "Sviluppatore", "4", "Indeterminato", "2023-02-01", 40, 47500), ("M010", "Sviluppatore", "4", "Indeterminato", "2023-09-18", 40, 47000),
            ("M011", "Amministrazione e personale", "4", "Indeterminato", "2023-11-06", 30, 33500), ("M012", "UX designer", "4", "Indeterminato", "2024-04-02", 40, 46500),
            ("M013", "Sviluppatore", "5", "Apprendistato", "2024-09-02", 40, 36800), ("M014", "Data scientist", "3", "Indeterminato", "2025-01-13", 40, 55500),
            ("M015", "Commerciale", "3", "Indeterminato", "2025-03-03", 40, 54000), ("M016", "Sviluppatore", "5", "Apprendistato", "2025-10-01", 40, 36000),
            ("M017", "Sviluppatore", "5", "Apprendistato", "2026-02-02", 40, 35500)]
    for r in rows:
        ws.append(list(r))
    wb.save(path)
    return path


# ------------------------------------------------------------------------------------------------ pacchetto completo
def build(dest: Path) -> List[Tuple[str, Path]]:
    dest.mkdir(parents=True, exist_ok=True)
    files: List[Tuple[str, Path]] = []
    files.append(("COMPANY_REGISTRY", make_registry(dest / "01_Visura_camerale_Meridiana_Digital_Solutions.pdf")))
    for n, y in enumerate(YEARS, 2):
        files.append(("BALANCE_SHEET", make_balance(dest / f"0{n}_Bilancio_{y}.pdf", y)))
    files.append(("PAYSLIP", make_payslip(dest / "05_Busta_paga_agosto_2026_Bertone_Andrea.pdf", "Bertone", "Andrea", "3", 2980.77, date(1991, 6, 12), True, "L219", "18/02/2018")))
    files.append(("PAYSLIP", make_payslip(dest / "06_Busta_paga_agosto_2026_Rinaldi_Sara.pdf", "Rinaldi", "Sara", "4", 2564.10, date(1996, 11, 3), False, "F205", "10/01/2022")))
    files.append(("F24", make_f24(dest / "07_F24_pagamento_16-09-2026.pdf", "16/09/2026", "agosto 2026", [("1001", "0008", "2026", 21486.30), ("1040", "0008", "2026", 3120.00), ("6008", "0008", "2026", 15284.55)])))
    files.append(("F24", make_f24(dest / "08_F24_pagamento_16-08-2026.pdf", "16/08/2026", "luglio 2026", [("1001", "0007", "2026", 21102.85), ("1040", "0007", "2026", 2890.00), ("6007", "0007", "2026", 14870.10)])))
    files.append(("APPLICATION_DRAFT", make_draft(dest / "09_Bozza_candidatura_Progetto_Atlas.pdf")))
    files.append(("OTHER", make_durc(dest / "10_DURC_regolare_2026.pdf")))
    files.append(("OTHER", make_de_minimis(dest / "11_Dichiarazione_de_minimis_2024-2026.pdf")))
    files.append(("OTHER", make_business_plan(dest / "12_Business_plan_2026-2028.pdf")))
    files.append(("OTHER", make_xlsx_aiuti(dest / "13_Registro_aiuti_ricevuti.xlsx")))
    files.append(("OTHER", make_xlsx_organico(dest / "14_Organico_e_livelli_CCNL.xlsx")))
    return files


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "documenti_di_prova" / "meridiana_digital_solutions"
    for kind, p in build(out):
        print(f"{kind:18} {p.name}")
    for y in YEARS:
        b = balance_figures(y)
        print(y, "ricavi", REVENUE[_idx(y)], "costi", b["costs"], "utile", b["net"])
