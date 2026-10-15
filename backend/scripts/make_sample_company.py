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
import unicodedata
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sample_company import bilancio, docs, docs_long, docs_more, docs_new, model, xlsx_pack  # noqa: E402
from sample_company.model import ALL_YEARS, COMPANY, YEARS  # noqa: E402,F401


def payslips(dest: Path) -> List[Tuple[str, Path]]:
    """Il cedolino di agosto 2026 di ogni persona dell'organico (17): competenze lorde = RAL / 14, così il cedolino e il registro del personale dicono la stessa cosa."""
    from sample_company import people as P
    out = []
    others = [x["id"] for x in P.EMPLOYEES if x["id"] not in ("M003", "M006")]
    for e in P.EMPLOYEES:
        n = {"M003": "05", "M006": "06"}.get(e["id"]) or str(36 + others.index(e["id"]))
        role = e["role"][:1].upper() + e["role"][1:]
        qualifica = f"{'Quadro' if e['level'] == 'Quadro' else 'Impiegato/a'} - {role.lower()}" + (" (apprendista)" if e["contract"] == "Apprendistato" else "")
        fname = unicodedata.normalize("NFKD", f"{e['surname']}_{e['name']}").encode("ascii", "ignore").decode().replace(" ", "_")
        out.append(("PAYSLIP", docs.make_payslip(dest / f"{n}_Busta_paga_agosto_2026_{fname}.pdf", e["id"], P.gross_monthly(e), qualifica)))
    return out


def build(dest: Path) -> List[Tuple[str, Path]]:
    dest.mkdir(parents=True, exist_ok=True)
    files: List[Tuple[str, Path]] = []
    files.append(("COMPANY_REGISTRY", docs.make_registry(dest / "01_Visura_camerale_Meridiana_Digital_Solutions.pdf")))
    for n, y in enumerate(YEARS, 2):
        files.append(("BALANCE_SHEET", bilancio.make_balance(dest / f"0{n}_Bilancio_{y}.pdf", y)))
    for kind, path in payslips(dest):
        files.append((kind, path))
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
    # F24 dei mesi precedenti del 2026 (i versamenti del 16 di ogni mese)
    import random
    r = random.Random("f24-2026")
    for k, pay_mm in enumerate((7, 6, 5, 4, 3, 2, 1), 16):
        ref_m = pay_mm - 1 or 12
        ref_y = 2026 if pay_mm > 1 else 2025
        names = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
        rows = [("1001", f"{ref_m:04d}", str(ref_y), round(20200 + r.uniform(-600, 700), 2), 0), ("1040", f"{ref_m:04d}", str(ref_y), round(2800 + r.uniform(-150, 260), 2), 0),
                (f"60{ref_m:02d}", f"{ref_m:04d}", str(ref_y), round(7100 + r.uniform(-500, 500), 2), 0)]
        if pay_mm == 7:
            rows.append(("6938", "0000", "2025", 0, 3500.00))
        files.append(("F24", docs.make_f24(dest / f"{k}_F24_pagamento_16-{pay_mm:02d}-2026.pdf", f"16/{pay_mm:02d}/2026", f"{names[ref_m - 1]} {ref_y}", f"{ref_m:02d}/{ref_y}", rows,
                                           round(14400 + r.uniform(-400, 500), 2), round(300 + r.uniform(-8, 12), 2), round(112 + r.uniform(-4, 6), 2))))
    files.append(("OTHER", docs_long.redditi(dest / "23_Dichiarazione_Redditi_SC_2025.pdf")))
    files.append(("OTHER", docs_long.irap(dest / "24_Dichiarazione_IRAP_2025.pdf")))
    files.append(("OTHER", docs_long.iva(dest / "25_Dichiarazione_IVA_2026.pdf")))
    files.append(("OTHER", docs_long.ammortamento(dest / "26_Piano_ammortamento_finanziamento.pdf")))
    files.append(("OTHER", docs_long.estratto_conto(dest / "27_Estratto_conto_agosto_2026.pdf")))
    files.append(("OTHER", docs_long.contratto(dest / "28_Contratto_locazione_sede.pdf")))
    files.append(("OTHER", docs_long.libro_soci(dest / "29_Libro_soci.pdf")))
    files.append(("OTHER", docs_long.relazione_rs(dest / "30_Relazione_tecnica_credito_RS_2025.pdf")))
    files.append(("OTHER", xlsx_pack.verifica(dest / "31_Bilancio_di_verifica_e_CE_mensile.xlsx")))
    files.append(("OTHER", xlsx_pack.fatture_emesse(dest / "32_Registro_fatture_emesse_2023-2025.xlsx")))
    files.append(("OTHER", xlsx_pack.fatture_ricevute(dest / "33_Registro_fatture_ricevute_2024-2025.xlsx")))
    files.append(("OTHER", xlsx_pack.commesse(dest / "34_Controllo_commesse_e_budget_2026.xlsx")))
    files.append(("OTHER", xlsx_pack.modello_bp(dest / "35_Business_plan_modello_finanziario.xlsx")))
    files.append(("OTHER", docs_new.visura_aiuti(dest / "51_Visura_aiuti_RNA_14-10-2026.pdf")))
    for k, name in enumerate(("52_Preventivo_infrastruttura_cloud.pdf", "53_Preventivo_licenze_software.pdf", "54_Preventivo_macchine_e_arredi.pdf")):
        files.append(("OTHER", docs_new.preventivo(dest / name, k)))
    files.append(("OTHER", docs_new.fatture_xml_zip(dest / "55_Fatture_passive_2025_XML.zip")))
    files.append(("OTHER", docs_new.bilancio_xbrl(dest / "56_Bilancio_2024-2025_XBRL.xbrl")))
    files.append(("OTHER", docs_new.bilancio_verifica_csv(dest / "57_Bilancio_di_verifica_2025_gestionale.csv")))
    return files


def publish(files: List[Tuple[str, Path]], public: Path) -> Path:
    """Copia i documenti anche in ``frontend/public/azienda_di_prova`` con un elenco (manifest.json): è la copia che l'app offre con «Carica l'azienda di prova».
    Ogni rigenerazione la riallinea, così l'app e la cartella ``documenti_di_prova`` non possono più divergere."""
    import hashlib
    import json
    import shutil
    if public.exists():
        shutil.rmtree(public)
    public.mkdir(parents=True)
    manifest = []
    for kind, path in files:
        shutil.copy2(path, public / path.name)
        manifest.append({"file": path.name, "doc_type": kind, "size": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    (public / "manifest.json").write_text(json.dumps({"company": COMPANY["name"], "files": manifest}, ensure_ascii=False, indent=1), encoding="utf-8")
    return public


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "documenti_di_prova" / "meridiana_digital_solutions"
    built = build(out)
    for kind, p in built:
        print(f"{kind:18} {p.name:60} {p.stat().st_size / 1024:8.1f} KB")
    if len(sys.argv) <= 1:                                      # destinazione standard: si aggiorna anche la copia offerta dall'app
        print("copia per l'app:", publish(built, Path(__file__).resolve().parents[2] / "frontend" / "public" / "azienda_di_prova"))
    for y in ALL_YEARS:
        p = model.pl(y)
        print(y, "ricavi", p["revenue"], "costi", p["b_total"], "utile", p["net"])
