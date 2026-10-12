"""Genera i documenti di un'azienda di prova COMPLETAMENTE FITTIZIA, lunghi e dettagliati come quelli di un cliente vero, e coerenti tra loro.

Azienda: Meridiana Digital Solutions S.r.l. (Torino, software e consulenza informatica). I documenti sono:
- visura camerale ordinaria (sei sezioni: sede, capitale, attività, soci, amministratori, addetti, storia);
- tre bilanci d'esercizio (2023, 2024, 2025) in forma ordinaria: stato patrimoniale, conto economico, rendiconto finanziario, nota integrativa,
  relazione sulla gestione, verbale dell'assemblea e conto economico analitico per conti;
- due cedolini di agosto 2026 con tutte le voci del Libro Unico del Lavoro; due modelli F24 con sezioni erario, INPS e regioni;
- la bozza di candidatura del progetto Atlas, il DURC, la dichiarazione de minimis, il business plan 2026-2028;
- il registro degli aiuti, l'organico con il costo del lavoro e il libro dei cespiti in Excel.

Ogni numero viene dal modello contabile ``sample_company/model.py`` (attivo = passivo, il rendiconto riconcilia la cassa, i movimenti tornano ai saldi):
nomi, codici fiscali, partita IVA e importi sono inventati e non appartengono a nessuna persona o impresa reale.

Uso:  python scripts/make_sample_company.py [cartella di destinazione]
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sample_company import bilancio, docs, model  # noqa: E402
from sample_company.model import ALL_YEARS, COMPANY, YEARS  # noqa: E402,F401


def build(dest: Path) -> List[Tuple[str, Path]]:
    dest.mkdir(parents=True, exist_ok=True)
    files: List[Tuple[str, Path]] = []
    files.append(("COMPANY_REGISTRY", docs.make_registry(dest / "01_Visura_camerale_Meridiana_Digital_Solutions.pdf")))
    for n, y in enumerate(YEARS, 2):
        files.append(("BALANCE_SHEET", bilancio.make_balance(dest / f"0{n}_Bilancio_{y}.pdf", y)))
    files.append(("PAYSLIP", docs.make_payslip(dest / "05_Busta_paga_agosto_2026_Bertone_Andrea.pdf", "M003", 2980.77, "Impiegato - sviluppatore software senior")))
    files.append(("PAYSLIP", docs.make_payslip(dest / "06_Busta_paga_agosto_2026_Rinaldi_Sara.pdf", "M006", 2564.10, "Impiegata - analista dei dati")))
    files.append(("F24", docs.make_f24(dest / "07_F24_pagamento_16-09-2026.pdf", "16/09/2026", "agosto 2026", "08/2026",
                                       [("1001", "0008", "2026", 21486.30, 0), ("1040", "0008", "2026", 3120.00, 0), ("6008", "0008", "2026", 7845.20, 0), ("6938", "0000", "2025", 0, 3500.00)], 15284.55, 310.20, 118.40)))
    files.append(("F24", docs.make_f24(dest / "08_F24_pagamento_16-08-2026.pdf", "16/08/2026", "luglio 2026", "07/2026",
                                       [("1001", "0007", "2026", 21102.85, 0), ("1040", "0007", "2026", 2890.00, 0), ("6007", "0007", "2026", 7410.65, 0), ("6938", "0000", "2025", 0, 3500.00)], 14870.10, 306.85, 115.20)))
    files.append(("APPLICATION_DRAFT", docs.make_draft(dest / "09_Bozza_candidatura_Progetto_Atlas.pdf")))
    files.append(("OTHER", docs.make_durc(dest / "10_DURC_regolare_2026.pdf")))
    files.append(("OTHER", docs.make_de_minimis(dest / "11_Dichiarazione_de_minimis_2024-2026.pdf")))
    files.append(("OTHER", docs.make_business_plan(dest / "12_Business_plan_2026-2028.pdf")))
    files.append(("OTHER", docs.make_xlsx_aiuti(dest / "13_Registro_aiuti_ricevuti.xlsx")))
    files.append(("OTHER", docs.make_xlsx_organico(dest / "14_Organico_e_livelli_CCNL.xlsx")))
    files.append(("OTHER", docs.make_xlsx_cespiti(dest / "15_Libro_cespiti_2025.xlsx")))
    return files


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "documenti_di_prova" / "meridiana_digital_solutions"
    for kind, p in build(out):
        print(f"{kind:18} {p.name:60} {p.stat().st_size / 1024:8.1f} KB")
    for y in ALL_YEARS:
        p = model.pl(y)
        print(y, "ricavi", p["revenue"], "costi", p["b_total"], "utile", p["net"])
