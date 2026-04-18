from fastapi import APIRouter

from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.transfers import router as transfers_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(transfers_router)
