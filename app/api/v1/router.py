from fastapi import APIRouter
from app.api.v1.endpoints import upload, sports, status, demo

api_router = APIRouter()

api_router.include_router(demo.router, prefix="/demo", tags=["demo"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(sports.router, prefix="/sports", tags=["sports"])
api_router.include_router(status.router, prefix="/status", tags=["status"])

