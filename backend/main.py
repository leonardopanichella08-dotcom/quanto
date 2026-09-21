import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import psycopg

from app.core import db
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router

app = FastAPI(
    title="QUANTO - Financial Knowledge Operating System",
    version="2.1.0",
    description="Motore di budgeting deterministico, allocazione annuale e asseverazione crittografica (Merkle + registro firmato)",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Origini esplicite (mai "*" con credenziali). Configurabili via QUANTO_CORS_ORIGINS (separate da virgola).
_origins = [o.strip() for o in os.getenv("QUANTO_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware, allow_origins=_origins, allow_credentials=False,
    allow_methods=["GET", "POST"], allow_headers=["Content-Type", "Authorization", "X-Quanto-Timestamp", "X-Quanto-Signature", "X-HQ-Token"],
)

app.include_router(api_router)


@app.exception_handler(db.DatabaseNotConfigured)
async def _db_missing(_: Request, exc: db.DatabaseNotConfigured):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(psycopg.OperationalError)
async def _db_down(_: Request, exc: psycopg.OperationalError):
    return JSONResponse(status_code=503, content={"detail": "Il database non risponde: riprova tra poco"})


@app.get("/api/v2/health/ready", tags=["Health Check"])
def readiness():
    """Pronto solo se il database risponde e lo schema è aggiornato."""
    with db.connect() as conn:
        conn.execute("SELECT 1")
    return {"status": "READY", "database": "PostgreSQL"}


@app.get("/api/v2/health", tags=["Health Check"])
@app.get("/", tags=["Health Check"])
def system_health_check():
    return {
        "system": "QUANTO Engine",
        "status": "OPERATIONAL",
        "version": "2.1.0",
        "registry": "Catena di hash append-only firmata Ed25519",
        "privacy": "Pseudonimizzazione lato server; nel registro solo la Merkle Root",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
