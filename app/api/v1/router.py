from fastapi import APIRouter
from app.api.v1.endpoints import upload, sports, status, demo, ready, waitlist

api_router = APIRouter()

api_router.include_router(demo.router, prefix="/demo", tags=["demo"])
api_router.include_router(ready.router, prefix="/ready", tags=["ready"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(sports.router, prefix="/sports", tags=["sports"])
api_router.include_router(status.router, prefix="/status", tags=["status"])
api_router.include_router(waitlist.router, tags=["waitlist"])

