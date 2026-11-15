"""Avvia il backend in locale leggendo un file di ambiente, senza installare nulla.

    python scripts/run_local.py                         # sviluppo: legge backend/.env e usa un PostgreSQL INCORPORATO (dati in backend/.localdb)
    python scripts/run_local.py --env-file .env.prod --prod --port 8001   # SOLO su richiesta esplicita: database di produzione

Regole di sicurezza:
- senza ``--prod`` ogni indirizzo di database scritto nel file viene IGNORATO: in sviluppo si usa sempre il database incorporato;
- con ``--prod`` serve un indirizzo di database nel file, e lo script lo dice a voce alta prima di partire;
- nessuna variabile viene stampata (né valori né chiavi).
Il primo manager si crea da solo se nel file ci sono QUANTO_BOOTSTRAP_ADMIN_EMAIL e QUANTO_BOOTSTRAP_ADMIN_PASSWORD e non esiste ancora nessun utente.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB_VARS = ("QUANTO_DATABASE_URL", "DATABASE_URL", "POSTGRES_URL")


def read_env(path: pathlib.Path) -> dict:
    """KEY=valore per riga; righe vuote e commenti ignorati; virgolette esterne tolte."""
    out = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.split(" #", 1)[0].strip().strip('"').strip("'")
        if value:
            out[key.strip()] = value
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env-file", default=".env", help="file di ambiente, relativo a backend/ (default .env)")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--prod", action="store_true", help="usa il database scritto nel file (produzione): solo su richiesta esplicita")
    args = ap.parse_args()

    env_path = (ROOT / args.env_file).resolve()
    values = read_env(env_path) if env_path.exists() else {}
    if not env_path.exists():
        print(f"Nessun file {args.env_file}: parto con i valori di sviluppo minimi.")
    for k in DB_VARS:                                  # mai un database ereditato dalla shell
        os.environ.pop(k, None)
    for k, v in values.items():
        if k in DB_VARS and not args.prod:
            continue
        os.environ[k] = v

    if args.prod:
        if not any(os.environ.get(k) for k in DB_VARS):
            sys.exit("--prod senza un indirizzo di database nel file: mi fermo.")
        print("ATTENZIONE: database di PRODUZIONE. Solo lettura, salvo ok esplicito del titolare.")
    else:
        import pixeltable_pgserver as pgserver          # in requirements-dev.txt
        data = ROOT / ".localdb"
        data.mkdir(exist_ok=True)
        server = pgserver.get_server(str(data), cleanup_mode="stop")
        os.environ["QUANTO_DATABASE_URL"] = server.get_uri()
        os.environ.setdefault("QUANTO_PII_KEY", "solo-sviluppo-locale")
        os.environ.setdefault("QUANTO_FILE_KEY", "11" * 32)
        os.environ.setdefault("QUANTO_JWT_SECRET", "solo-sviluppo-locale")
        print(f"Database locale incorporato in {data} (resta tra un avvio e l'altro).")

    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)
    import uvicorn
    from main import app
    print(f"Backend su http://127.0.0.1:{args.port}  (documentazione delle API: /docs)")
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
