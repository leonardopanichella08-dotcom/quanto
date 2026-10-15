"""I documenti aggiunti all'azienda di prova (visura aiuti, preventivi, fatture XML, XBRL, bilancio di verifica CSV): QUANTO li legge e li incrocia con il resto."""
from fastapi.testclient import TestClient

from main import app
from tests.test_sample_company import upload_all

client = TestClient(app)


def test_new_sample_documents_are_read_and_cross_checked(tmp_path):
    docs = upload_all(tmp_path)
    keys = lambda name: {f["field_key"] for f in docs[name]["fields"]}
    assert keys("51_Visura_aiuti_RNA_14-10-2026.pdf") == {"rna_visura", "rna_aid"} and len(docs["51_Visura_aiuti_RNA_14-10-2026.pdf"]["fields"]) == 10
    assert keys("55_Fatture_passive_2025_XML.zip") == {"supplier_spend"} and keys("56_Bilancio_2024-2025_XBRL.xbrl") == {"xbrl_balance"}
    assert keys("57_Bilancio_di_verifica_2025_gestionale.csv") == {"trial_balance_line"}
    assert keys("29_Libro_soci.pdf") == {"shareholder"} and keys("27_Estratto_conto_agosto_2026.pdf") == {"bank_balance"}
    assert keys("11_Dichiarazione_de_minimis_2024-2026.pdf") == {"de_minimis_declared"}
    client.post("/api/v2/profile/sync")

    # coerenza tra i documenti: nessun segnale di allarme sull'azienda di prova
    checks = {c["key"]: c for c in client.get("/api/v2/profile/consistency").json()["checks"]}
    assert checks["iva_vs_ricavi"]["status"] == "OK" and checks["soci"]["status"] == "OK" and checks["durc"]["status"] == "OK" and checks["visura_rna"]["status"] == "OK"
    assert checks["liquidita"]["status"] == "INFO" and "600.358" in checks["liquidita"]["detail"]

    # i preventivi
    quotes = client.get("/api/v2/profile/quotes").json()["quotes"]
    assert sorted((q["net_eur"], q["expense_type"]) for q in quotes) == [(17400.0, "CAP_SOFTWARE"), (23200.0, "CAP_ARREDI"), (48600.0, "CAP_CLOUD")] and not any(q["expired"] for q in quotes)
    assert len(client.get("/api/v2/profile/shareholders").json()["shareholders"]) == 2

    # il piano degli investimenti usa gli importi dei preventivi e lo dice
    ideas = {i["id"]: i for i in client.get("/api/v2/profile/project-ideas?year=2027").json()["ideas"]}
    dig = ideas["piano-digitalizzazione"]
    assert {l["amount_eur"] for l in dig["lines"]} == {48600.0, 17400.0} and all(l["quotes"] for l in dig["lines"]) and dig["new_eur"] == 66000.0
    assert not any(m.startswith("Un preventivo") for m in dig["missing"])
    assert any(m.startswith("Un preventivo per") for m in ideas["piano-ricerca_sviluppo"]["missing"])               # per lo sviluppo della piattaforma non c'è un preventivo

    # aiuti: la visura combacia con la dichiarazione e il registro; resta da rispondere sull'impresa unica
    a = client.get("/api/v2/profile/aids").json()
    assert a["differences"] == [] and a["received_eur"] == 16500.0 and a["residual_eur"] == 283500.0 and "SELF" in a["checks"]
    assert a["status"] == "NON_VERIFICATO" and a["suggested_answers"] and set(a["suggested_answers"].values()) == {"no"}
    saved = client.put("/api/v2/profile/aids/group", json={"answers": a["suggested_answers"], "companies": []})
    assert saved.status_code == 200
    b = client.get("/api/v2/profile/aids").json()
    assert b["status"] == "VERIFICATO" and b["usable_residual_eur"] == 283500.0 and b["suggested_answers"] is None
