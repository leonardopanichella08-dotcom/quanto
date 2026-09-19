from fastapi import APIRouter, Depends

from app.api.deps import require_auth
from app.api.endpoints import allocation, auth, budget, ingestion, pattern, registry

api_router = APIRouter(prefix="/api/v2")
protected = [Depends(require_auth)]

api_router.include_router(auth.router, prefix="/auth", tags=["Autenticazione ERP (OAuth 2.0 / HMAC)"])
api_router.include_router(budget.router, prefix="/budget", tags=["Missione Uno - Budget Validation"], dependencies=protected)
api_router.include_router(pattern.router, prefix="/pattern", tags=["Demo - Pattern Matching"], dependencies=protected)
api_router.include_router(allocation.router, prefix="/allocation", tags=["Missione Due - Annual Allocation"], dependencies=protected)
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["Ingestion Fonte A"], dependencies=protected)
# registro: register protetto per singolo endpoint; le verifiche dell'Auditor Portal restano pubbliche
api_router.include_router(registry.router, prefix="/registry", tags=["Registro di asseverazione / Auditor Portal"])
