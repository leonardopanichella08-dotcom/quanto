"""Persone e identificativi fittizi (codici fiscali con carattere di controllo corretto, ma nomi e dati inventati)."""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Tuple


def fiscal_code(surname: str, name: str, birth: date, male: bool, town_code: str) -> str:
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


def iban(seed: str) -> str:
    """IBAN italiano fittizio con cifre di controllo corrette (ABI/CAB inventati)."""
    bban = "X" + seed.rjust(22, "0")[-22:].replace(" ", "0")
    digits = "".join(str(int(c, 36)) for c in bban + "IT00")
    check = 98 - int(digits) % 97
    return f"IT{check:02d}{bban}"


# nome, cognome, sesso, nascita, comune (codice catastale), residenza
EMPLOYEES: List[Dict] = [
    {"id": "M001", "surname": "Ferraris", "name": "Giulia", "male": False, "birth": date(1981, 2, 18), "town": "L219", "role": "Amministratore e direttore tecnico", "level": "Quadro", "contract": "Indeterminato", "hired": "2016-03-14", "hours": 40, "cost": 78000},
    {"id": "M002", "surname": "Gallo", "name": "Matteo", "male": True, "birth": date(1984, 7, 2), "town": "L219", "role": "Responsabile sviluppo", "level": "1", "contract": "Indeterminato", "hired": "2016-09-01", "hours": 40, "cost": 69000},
    {"id": "M003", "surname": "Bertone", "name": "Andrea", "male": True, "birth": date(1991, 6, 12), "town": "L219", "role": "Sviluppatore senior", "level": "3", "contract": "Indeterminato", "hired": "2018-02-01", "hours": 40, "cost": 57000},
    {"id": "M004", "surname": "Marchetti", "name": "Elena", "male": False, "birth": date(1990, 1, 25), "town": "L219", "role": "Sviluppatore senior", "level": "3", "contract": "Indeterminato", "hired": "2019-05-13", "hours": 40, "cost": 56500},
    {"id": "M005", "surname": "Costa", "name": "Luca", "male": True, "birth": date(1993, 9, 9), "town": "L219", "role": "Sviluppatore", "level": "4", "contract": "Indeterminato", "hired": "2020-09-01", "hours": 40, "cost": 49500},
    {"id": "M006", "surname": "Ricci", "name": "Chiara", "male": False, "birth": date(1994, 4, 30), "town": "L219", "role": "Data analyst", "level": "4", "contract": "Indeterminato", "hired": "2021-03-01", "hours": 40, "cost": 48800},
    {"id": "M007", "surname": "Moretti", "name": "Davide", "male": True, "birth": date(1995, 12, 3), "town": "L219", "role": "Sviluppatore", "level": "4", "contract": "Indeterminato", "hired": "2022-01-10", "hours": 40, "cost": 48000},
    {"id": "M008", "surname": "Conti", "name": "Federica", "male": False, "birth": date(1988, 8, 16), "town": "L219", "role": "Project manager", "level": "2", "contract": "Indeterminato", "hired": "2022-06-01", "hours": 40, "cost": 61000},
    {"id": "M009", "surname": "De Luca", "name": "Simone", "male": True, "birth": date(1996, 3, 21), "town": "L219", "role": "Sviluppatore", "level": "4", "contract": "Indeterminato", "hired": "2023-02-01", "hours": 40, "cost": 47500},
    {"id": "M010", "surname": "Barbieri", "name": "Laura", "male": False, "birth": date(1997, 10, 11), "town": "L219", "role": "Sviluppatore", "level": "4", "contract": "Indeterminato", "hired": "2023-09-18", "hours": 40, "cost": 47000},
    {"id": "M011", "surname": "Fontana", "name": "Paola", "male": False, "birth": date(1985, 5, 5), "town": "L219", "role": "Amministrazione e personale", "level": "4", "contract": "Indeterminato", "hired": "2023-11-06", "hours": 30, "cost": 33500},
    {"id": "M012", "surname": "Esposito", "name": "Marco", "male": True, "birth": date(1992, 11, 27), "town": "L219", "role": "UX designer", "level": "4", "contract": "Indeterminato", "hired": "2024-04-02", "hours": 40, "cost": 46500},
    {"id": "M013", "surname": "Villa", "name": "Giorgia", "male": False, "birth": date(2000, 6, 14), "town": "L219", "role": "Sviluppatore", "level": "5", "contract": "Apprendistato", "hired": "2024-09-02", "hours": 40, "cost": 36800},
    {"id": "M014", "surname": "Greco", "name": "Fabio", "male": True, "birth": date(1990, 2, 8), "town": "L219", "role": "Data scientist", "level": "3", "contract": "Indeterminato", "hired": "2025-01-13", "hours": 40, "cost": 55500},
    {"id": "M015", "surname": "Rossetti", "name": "Valentina", "male": False, "birth": date(1989, 7, 19), "town": "L219", "role": "Commerciale", "level": "3", "contract": "Indeterminato", "hired": "2025-03-03", "hours": 40, "cost": 54000},
    {"id": "M016", "surname": "Mancini", "name": "Nicolò", "male": True, "birth": date(2001, 1, 22), "town": "L219", "role": "Sviluppatore", "level": "5", "contract": "Apprendistato", "hired": "2025-10-01", "hours": 40, "cost": 36000},
    {"id": "M017", "surname": "Ferrero", "name": "Anna", "male": False, "birth": date(2002, 4, 17), "town": "L219", "role": "Sviluppatore", "level": "5", "contract": "Apprendistato", "hired": "2026-02-02", "hours": 40, "cost": 35500},
]
for e in EMPLOYEES:
    e["cf"] = fiscal_code(e["surname"], e["name"], e["birth"], e["male"], e["town"])
BY_ID = {e["id"]: e for e in EMPLOYEES}


def ral(e: Dict) -> int:
    """RAL (retribuzione annua lorda) di una persona: la stessa nel registro del personale, nei cedolini e nel business plan."""
    return int(round(e["cost"] / 1.38 / 100) * 100)


def gross_monthly(e: Dict) -> float:
    """Competenze lorde mensili su 14 mensilità: RAL / 14, così la RAL stimata dal cedolino coincide con quella dichiarata."""
    return round(ral(e) / 14, 2)
SHAREHOLDERS = [("FERRARIS GIULIA", "FRRGLI81B58L219X", 60, 30000), ("BERTOLOTTI MARCO", "BRTMRC79C14L219P", 40, 20000)]
