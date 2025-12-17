from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.router import api_router
import os

app = FastAPI(
    title="TrueForm AI API",
    description="Video-based sports form analysis using pose estimation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_PREFIX)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.RESULTS_DIR, exist_ok=True)


@app.get("/")
async def root():
    return {"message": "TrueForm AI API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

