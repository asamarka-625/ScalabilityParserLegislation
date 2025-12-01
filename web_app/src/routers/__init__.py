# Внешние зависимости
from fastapi import APIRouter
# Внутренние модули
from web_app.src.routers.api_router import router as api_router


router = APIRouter()
router.include_router(api_router)