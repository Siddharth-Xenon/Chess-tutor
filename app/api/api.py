from fastapi import APIRouter

from app.api.routers import app

api_router = APIRouter()

api_router.include_router(app.router, prefix="/app", tags=["app"])
