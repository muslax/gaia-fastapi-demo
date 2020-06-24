from fastapi import APIRouter

from app.api.api_v1.endpoints.login import router as login_router
from app.api.api_v1.endpoints.user import router as user_router
# from app.api.api_v1.endpoints.persona import router as persona_router
from app.api.api_v1.endpoints.company import router as company_router
from app.api.api_v1.endpoints.project import router as project_router
# from app.api.api_v1.endpoints.gpq import router as gpq_router
from app.api.api_v1.endpoints.item import router as item_router


router = APIRouter()

router.include_router(item_router, tags=["Item"])
router.include_router(login_router, tags=["Login"])
router.include_router(user_router, tags=["Users"])
router.include_router(company_router, tags=["Companies"])
router.include_router(project_router, prefix="/projects", tags=["Projects"])
# router.include_router(persona_router, tags=["Personas"])
# router.include_router(gpq_router, tags=["GPQ"])


# router.include_router(login_router, tags=["login"])
# router.include_router(bacth_router, tags=["Batches"])
