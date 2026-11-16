"""Richieste di accesso: chi si registra aspetta, il titolare approva dal Quartier Generale con il livello, l'e-mail resta pronta."""
import pytest
from fastapi.testclient import TestClient

from app.core import access, users
from main import app
from tests.conftest import manager_token

client = TestClient(app)
PW = "Una-Password-Robusta-42"


@pytest.fixture
def secured(monkeypatch):
    monkeypatch.setenv("QUANTO_AUTH_REQUIRED", "1")
    return monkeypatch


def hq():
    return {"Authorization": f"Bearer {manager_token()}"}


def ask(email="laura@studio.test", name="Laura Bianchi", studio="Studio Bianchi"):
    return client.post("/api/v2/auth/register", json={"email": email, "name": name, "password": PW, "studio_name": studio})


def login(email="laura@studio.test", pw=PW):
    return client.post("/api/v2/auth/login", json={"email": email, "password": pw})


def first_request():
    return client.get("/api/v2/hq/access-requests", headers=hq()).json()["requests"][0]["id"]


def test_chi_si_registra_non_entra_subito_e_la_richiesta_arriva_al_quartier_generale(secured):
    r = ask()
    assert r.status_code == 200 and r.json()["pending"] is True and "access_token" not in r.json()
    lista = client.get("/api/v2/hq/access-requests", headers=hq()).json()
    assert lista["counts"]["PENDING"] == 1
    req = lista["requests"][0]
    assert req["email"] == "laura@studio.test" and req["status"] == "PENDING" and req["studio_name"] == "Studio Bianchi"
    assert [lv["id"] for lv in lista["levels"]] == ["USER", "MANAGER"]
    assert client.get("/api/v2/hq/overview", headers=hq()).json()["access"]["PENDING"] == 1


def test_in_attesa_la_password_giusta_da_un_messaggio_chiaro_e_quella_sbagliata_resta_credenziali_errate(secured):
    ask()
    attesa = login()
    assert attesa.status_code == 403 and "in attesa di approvazione" in attesa.json()["detail"]
    sbagliata = login(pw="sbagliata-sbagliata-1")
    assert sbagliata.status_code == 401 and "non corrette" in sbagliata.json()["detail"]


def test_approvando_con_il_livello_l_account_si_attiva_e_l_email_e_gia_pronta(secured):
    ask()
    rid = first_request()
    ok = client.post(f"/api/v2/hq/access-requests/{rid}/approve", json={"level": "USER"}, headers=hq())
    assert ok.status_code == 200 and ok.json()["status"] == "APPROVED" and ok.json()["level_label"] == "Utente"
    mail = ok.json()
    assert "approvata" in mail["mail_subject"] and "Ciao Laura" in mail["mail_body"] and "«Utente»" in mail["mail_body"]
    assert "quanto-self.vercel.app" in mail["mail_body"] and "Quartier Generale" not in mail["mail_body"]
    entra = login()
    assert entra.status_code == 200 and entra.json()["user"]["role"] == "USER"
    assert client.get("/api/v2/hq/overview", headers={"Authorization": f"Bearer {entra.json()['access_token']}"}).status_code in (401, 403)   # un Utente non entra nel Quartier Generale
    assert client.get("/api/v2/hq/access-requests", headers=hq()).json()["counts"]["mail_to_send"] == 1
    inviata = client.post(f"/api/v2/hq/access-requests/{rid}/mail-sent", headers=hq())
    assert inviata.status_code == 200 and inviata.json()["mail_sent_at"]
    assert client.get("/api/v2/hq/access-requests", headers=hq()).json()["counts"]["mail_to_send"] == 0


def test_il_livello_manager_si_assegna_e_l_email_dice_solo_cio_che_e_vero(secured):
    ask(email="capo@studio.test", name="Marco Capo")
    ok = client.post(f"/api/v2/hq/access-requests/{first_request()}/approve", json={"level": "MANAGER"}, headers=hq()).json()
    assert "«Manager»" in ok["mail_body"] and "aggiornamenti automatici" in ok["mail_body"]
    assert "Quartier Generale" not in ok["mail_body"]                        # il Quartier Generale è del titolare: nessun livello lo promette
    entra = login(email="capo@studio.test")
    assert entra.status_code == 200 and entra.json()["user"]["role"] == "MANAGER"


def test_con_il_titolare_configurato_anche_un_manager_resta_fuori_dal_quartier_generale(secured, monkeypatch):
    monkeypatch.setenv("QUANTO_OWNER_EMAIL", "titolare@studio.test")
    users.create_user("titolare@studio.test", "Titolare", PW, "MANAGER", actor="test")
    users.create_user("capo@studio.test", "Marco Capo", PW, "MANAGER", actor="test")
    capo = login(email="capo@studio.test").json()["access_token"]
    titolare = login(email="titolare@studio.test").json()["access_token"]
    assert client.get("/api/v2/hq/access-requests", headers={"Authorization": f"Bearer {capo}"}).status_code == 403
    assert client.get("/api/v2/hq/access-requests", headers={"Authorization": f"Bearer {titolare}"}).status_code == 200


def test_rifiutando_l_account_resta_chiuso_e_la_risposta_cortese_e_pronta(secured):
    ask()
    no = client.post(f"/api/v2/hq/access-requests/{first_request()}/reject", json={"reason": "Per ora apriamo solo agli studi di commercialisti."}, headers=hq()).json()
    assert no["status"] == "REJECTED" and "studi di commercialisti" in no["mail_body"]
    chiuso = login()
    assert chiuso.status_code == 403 and "non è stata accettata" in chiuso.json()["detail"]


def test_una_richiesta_si_decide_una_volta_sola_e_il_livello_deve_essere_valido(secured):
    ask()
    rid = first_request()
    assert client.post(f"/api/v2/hq/access-requests/{rid}/approve", json={"level": "SUPER"}, headers=hq()).status_code == 422
    assert client.post(f"/api/v2/hq/access-requests/{rid}/mail-sent", headers=hq()).status_code == 422            # prima si decide
    assert client.post(f"/api/v2/hq/access-requests/{rid}/approve", json={"level": "USER"}, headers=hq()).status_code == 200
    assert client.post(f"/api/v2/hq/access-requests/{rid}/reject", json={}, headers=hq()).status_code == 422
    assert client.post("/api/v2/hq/access-requests/9999/approve", json={"level": "USER"}, headers=hq()).status_code == 404


def test_senza_il_titolare_nessuno_vede_o_decide_le_richieste(secured):
    ask()
    assert client.get("/api/v2/hq/access-requests").status_code == 401
    assert client.post("/api/v2/hq/access-requests/1/approve", json={"level": "USER"}).status_code == 401


def test_la_vecchia_attivazione_a_mano_non_aggira_la_richiesta(secured):
    ask()
    uid = [u for u in users.list_users() if u["email"] == "laura@studio.test"][0]["id"]
    r = client.patch(f"/api/v2/hq/users/{uid}", json={"active": True}, headers=hq())
    assert r.status_code == 422 and "sezione Accessi" in r.json()["detail"]
    assert login().status_code == 403


def test_il_modulo_pubblico_ha_un_tetto_alle_richieste_in_attesa(secured, monkeypatch):
    monkeypatch.setattr(access, "MAX_PENDING", 2)
    assert ask(email="a@studio.test").status_code == 200 and ask(email="b@studio.test").status_code == 200
    pieno = ask(email="c@studio.test")
    assert pieno.status_code == 422 and "troppe richieste" in pieno.json()["detail"]


def test_gli_utenti_gia_attivi_non_sono_toccati_dalla_novita(secured):
    users.create_user("storico@studio.test", "Utente Storico", PW, "USER", actor="test")
    assert login(email="storico@studio.test").status_code == 200
    assert client.get("/api/v2/hq/access-requests", headers=hq()).json()["counts"]["PENDING"] == 0
