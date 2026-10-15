"""Lettura dei PDF «altri documenti» dell'azienda che dicono qualcosa di preciso: DURC, contratto di locazione, relazione sul credito d'imposta ricerca e sviluppo, finanziamento,
visura aiuti del Registro Nazionale degli Aiuti, libro dei soci, dichiarazione de minimis, dichiarazioni fiscali (IVA, IRAP, REDDITI), estratto conto, preventivi dei fornitori.

Un documento si riconosce dal titolo e dalle espressioni che lo definiscono; i dati si leggono solo se compaiono con la loro etichetta («Scadenza validità», «Il canone annuo è convenuto in…»).
Se un dato non c'è o non è chiaro non si legge: il documento resta archiviato. Nessun valore è dedotto.
"""
from __future__ import annotations

import json
import re
from datetime import date
from typing import Any, Dict, List, Optional

from app.core.anonymizer import PrivacyAnonymizer
from app.core.fonte_c import parsers

Field = parsers.Field
CONF = 0.92                                                  # testo di un PDF nativo con etichetta esplicita: letto bene, ma meno di una cella di foglio
_MONTHS = {"GENNAIO": 1, "FEBBRAIO": 2, "MARZO": 3, "APRILE": 4, "MAGGIO": 5, "GIUGNO": 6, "LUGLIO": 7, "AGOSTO": 8, "SETTEMBRE": 9, "OTTOBRE": 10, "NOVEMBRE": 11, "DICEMBRE": 12}
_EUR = r"(\d{1,3}(?:\.\d{3})*,\d{2})"


def _money(s: str) -> float:
    return float(s.replace(".", "").replace(",", "."))


def _dmy(s: str) -> Optional[str]:
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    return date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat() if m else None


def _long_date(day: str, month: str, year: str) -> Optional[str]:
    mth = _MONTHS.get(parsers.norm(month))
    return date(int(year), mth, int(day)).isoformat() if mth else None


def _fact(key: str, payload: Dict[str, Any], page: int, snippet: str) -> Field:
    return Field(key, json.dumps(payload, ensure_ascii=False, sort_keys=True), CONF, page, snippet[:200], False)


def read(text: str) -> List[Field]:
    out: List[Field] = []
    n = parsers.norm(text)
    flat = re.sub(r"\s+", " ", text)
    if "DURC" in n and "REGOLARITA CONTRIBUTIVA" in n:
        outcome = "regolare" if "ESITO REGOLARE" in n else ("irregolare" if "ESITO IRREGOLARE" in n else None)
        issued = re.search(r"Data emissione\s+(\d{2}/\d{2}/\d{4})", text)
        expires = re.search(r"Scadenza validit\S*\s+(\d{2}/\d{2}/\d{4})", text)
        proto = re.search(r"Numero protocollo\s+(\S+)", text)
        if outcome and expires:
            out.append(_fact("durc", {"outcome": outcome, "issued": _dmy(issued.group(1)) if issued else None, "expires": _dmy(expires.group(1)), "protocol": proto.group(1) if proto else None}, 1,
                             f"DURC {outcome}, scade il {expires.group(1)}"))
    if "CONTRATTO DI LOCAZIONE" in n:
        rent = re.search(r"canone annuo\D{0,60}?" + _EUR + r"\s*euro", flat, re.I)
        span = re.search(r"dal\s+(\d{1,2})\S*\s+([a-zà-ù]+)\s+(\d{4})\s+al\s+(\d{1,2})\S*\s+([a-zà-ù]+)\s+(\d{4})", flat, re.I)
        if rent:
            out.append(_fact("lease", {"annual_rent_eur": _money(rent.group(1)), "from": _long_date(*span.groups()[:3]) if span else None, "to": _long_date(*span.groups()[3:]) if span else None},
                             1, f"canone annuo {rent.group(1)} euro"))
    if "CREDITO DIMPOSTA RICERCA" in n:                      # norm() toglie gli apostrofi
        base = re.search(r"Totale costi ammissibili\s*" + _EUR, flat, re.I)
        credit = re.search(r"Credito d.imposta \(aliquota del (\d+)%\)\s*" + _EUR, flat, re.I)
        year = re.search(r"01/01/(20\d{2})", n)
        if base and credit:
            out.append(_fact("rd_credit", {"year": int(year.group(1)) if year else None, "eligible_costs_eur": _money(base.group(1)), "rate_pct": int(credit.group(1)), "credit_eur": _money(credit.group(2))}, 1,
                             f"costi ammissibili {base.group(1)}, credito {credit.group(2)}"))
    if "PIANO DI AMMORTAMENTO DEL FINANZIAMENTO" in n:
        loan = re.search(r"Importo originario euro\s+" + _EUR + r"\s*-\s*erogato il\s+(\d{2}/\d{2}/\d{4})\s*-\s*(\d+)\s+rate", flat, re.I)
        if loan:
            out.append(_fact("loan", {"original_eur": _money(loan.group(1)), "disbursed": _dmy(loan.group(2)), "installments": int(loan.group(3))}, 1, f"finanziamento di {loan.group(1)} euro"))
    _more(text, n, flat, out)
    return out


# ------------------------------------------------------------------------------------------------ gli altri documenti
_AMOUNT = r"(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)"
_ROW_AID = re.compile(r"^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(de minimis|esenzione[^0-9]*|credito d.imposta[^0-9]*|riduzione del premio|altro)\s+" + _EUR + r"\s+(COR-\d+|-)\s*$", re.I)
_ROW_DECL = re.compile(r"^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+De minimis\s+" + _EUR + r"(?:\s+(.*))?$", re.I)
_ROW_SHARE = re.compile(r"^([A-Z][A-Z' .]+?)\s+([A-Z0-9]{16}|\d{11})\s+(\d{1,3})%\s+" + _EUR + r"\s+(\d{2}/\d{2}/\d{4})")


def _amount(s: str) -> float:
    return float(s.replace(".", "").replace(",", ".")) if "," in s else float(s.replace(".", ""))


def _after(label: str, text: str) -> Optional[str]:
    m = re.search(label + r"\s+" + _AMOUNT, text, re.I)
    return m.group(1) if m else None


def _more(text: str, n: str, flat: str, out: List[Field]) -> None:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # --- visura aiuti del Registro Nazionale degli Aiuti
    if "VISURA AIUTI" in n and "REGISTRO NAZIONALE" in n:
        cf = re.search(r"Codice fiscale\s+(\d{11}|[A-Z0-9]{16})", text)
        when = re.search(r"Data della visura\s+(\d{2}/\d{2}/\d{4})", text)
        den = re.search(r"Denominazione\s+(.+)", text)
        if cf and when:
            out.append(_fact("rna_visura", {"cf": cf.group(1), "denomination": (den.group(1).strip()[:120] if den else None), "checked_at": _dmy(when.group(1))}, 1, f"visura aiuti del {when.group(1)}"))
            for k, ln in enumerate(lines):
                m = _ROW_AID.match(ln)
                if m:
                    regime = "de minimis" if m.group(3).lower().startswith("de minimis") else "altro"
                    measure = m.group(2).strip()
                    nxt = lines[k + 1] if k + 1 < len(lines) else ""
                    if nxt and len(nxt) < 70 and not re.match(r"\d{2}/\d{2}/\d{4}", nxt) and "COR-" not in nxt and not re.match(r"(Riepilogo|Voce|Aiuti|Massimale|Margine|La visura|Documento)", nxt):
                        measure += " " + nxt                              # la misura può andare a capo nella tabella
                    out.append(_fact("rna_aid", {"granted": _dmy(m.group(1)), "measure": measure[:200], "regime": regime, "amount_eur": _money(m.group(4)), "cor": None if m.group(5) == "-" else m.group(5)},
                                     1, ln))
    # --- libro dei soci: i soci persone fisiche restano un codice anonimo, le società socie si nominano (servono all'impresa unica)
    if "LIBRO DEI SOCI" in n:
        for ln in lines:
            m = _ROW_SHARE.match(ln)
            if not m:
                continue
            ident = m.group(2)
            person = len(ident) == 16
            payload = {"kind": "persona" if person else "impresa", "percent": int(m.group(3)), "nominal_eur": _money(m.group(4)), "since": _dmy(m.group(5))}
            if person:
                payload["token"] = PrivacyAnonymizer.generate_opaque_token(ident)
            else:
                payload.update({"cf": ident, "name": m.group(1).strip()[:120]})
            out.append(_fact("shareholder", payload, 1, "libro soci: " + ("socio persona fisica" if person else "socio società")))
    # --- dichiarazione sostitutiva «de minimis»
    if "AIUTI" in n and "DE MINIMIS" in n and "DICHIARAZIONE SOSTITUTIVA" in n:
        aids, seen = [], set()
        for ln in lines:
            m = _ROW_DECL.match(ln)
            if m and (m.group(1), m.group(3)) not in seen:
                seen.add((m.group(1), m.group(3)))
                cor = re.search(r"COR-\d+", m.group(4) or "")
                aids.append({"granted": _dmy(m.group(1)), "measure": m.group(2).strip()[:200], "amount_eur": _money(m.group(3)), "cor": cor.group(0) if cor else None})
        total = _after(r"TOTALE AIUTI NEL TRIENNIO", flat) or _after(r"TOTALE AIUTI NEL", flat)
        signed = re.search(r"Luogo e data:\s*[A-Za-z' ]+,\s*(\d{2}/\d{2}/\d{4})", text)
        alone = "NON E COLLEGATA" in n
        if aids or total:
            out.append(_fact("de_minimis_declared", {"signed": _dmy(signed.group(1)) if signed else None, "aids": aids, "total_eur": _money(total) if total else None, "unique_enterprise_alone": alone}, 1,
                             f"dichiarazione de minimis: {len(aids)} aiuti"))
    # --- dichiarazioni fiscali: le cifre che servono a controllare la coerenza con il bilancio
    if "DICHIARAZIONE ANNUALE IVA" in n:
        vol = _after(r"Volume d.affari dell.anno", flat)
        year = re.search(r"Anno d.imposta\s+(20\d{2})", text, re.I)
        if vol:
            out.append(_fact("tax_return", {"kind": "IVA", "tax_year": int(year.group(1)) if year else None, "turnover_eur": _amount(vol)}, 1, "dichiarazione IVA: volume d'affari"))
    if "DICHIARAZIONE IRAP" in n:
        base = _after(r"IS1 Valore della produzione netta", flat)
        tax = _after(r"IS7 Imposta lorda", flat)
        year = re.search(r"periodo d.imposta\s+(20\d{2})", text, re.I)
        if base:
            out.append(_fact("tax_return", {"kind": "IRAP", "tax_year": int(year.group(1)) if year else None, "net_production_value_eur": _amount(base), "tax_eur": _amount(tax) if tax else None}, 1, "dichiarazione IRAP"))
    if "MODELLO REDDITI SC" in n:
        taxable = _after(r"RF64 Reddito imponibile di periodo", flat)
        gross = _after(r"RN6 Imposta lorda \(aliquota 24%\)", flat)
        year = re.search(r"periodo d.imposta\s+(20\d{2})", text, re.I)
        if taxable:
            out.append(_fact("tax_return", {"kind": "REDDITI", "tax_year": int(year.group(1)) if year else None, "taxable_income_eur": _amount(taxable), "gross_tax_eur": _amount(gross) if gross else None}, 1, "dichiarazione REDDITI SC"))
    # --- estratto conto bancario
    if "ESTRATTO CONTO BANCARIO" in n:
        bal = re.search(r"Saldo finale al\s+(\d{2}/\d{2}/\d{4})\s+" + _EUR, flat)
        if bal:
            out.append(_fact("bank_balance", {"on": _dmy(bal.group(1)), "balance_eur": _money(bal.group(2))}, 1, f"saldo del conto al {bal.group(1)}"))
    # --- preventivo di un fornitore
    if "PREVENTIVO" in n and "TOTALE IMPONIBILE" in n:
        number = re.search(r"Preventivo n\.?\s*([A-Za-z0-9/\-]+)", text, re.I)
        when = re.search(r"Data\s+(\d{2}/\d{2}/\d{4})", text)
        valid = re.search(r"Valido fino al\s+(\d{2}/\d{2}/\d{4})", text, re.I)
        supplier = re.search(r"Fornitore\s+(.+)", text)
        subject = re.search(r"Oggetto\s+(.+)", text)
        net = _after(r"Totale imponibile", flat)
        if net and supplier:
            from app.core import expense_types
            subj = subject.group(1).strip()[:200] if subject else ""
            out.append(_fact("quote", {"number": number.group(1) if number else None, "date": _dmy(when.group(1)) if when else None, "valid_until": _dmy(valid.group(1)) if valid else None,
                                       "supplier": supplier.group(1).strip()[:120], "subject": subj, "net_eur": _money(net), "expense_type": expense_types.classify_type(subj) or None}, 1, f"preventivo {number.group(1) if number else ''}"))
