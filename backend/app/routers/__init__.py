from app.routers.auth import router as auth_router
from app.routers.campaigns import router as campaigns_router
from app.routers.leads import router as leads_router
from app.routers.ai import router as ai_router
from app.routers.company import router as company_router

__all__ = [
    "auth_router",
    "campaigns_router",
    "leads_router",
    "ai_router",
    "company_router",
]
