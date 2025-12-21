import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Logging first (lightweight)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", 8000))
logger.info(f"Initializing FastAPI on port {PORT}")

# Create app immediately
app = FastAPI(
    title="TrueForm AI API",
    description="Video-based sports form analysis using pose estimation",
    version="1.0.0",
)

# 🚨 ROOT ENDPOINT — MUST BE FIRST (Railway health check)
@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "trueform-ai-backend",
        "port": PORT,
        "docs": "/docs"
    }

# Lightweight health check
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "port": PORT
    }

# Load heavy dependencies AFTER root endpoints
logger.info("Loading heavy dependencies...")

try:
    from app.config import settings
    from app.api.v1.router import api_router

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.API_PREFIX)

    # Create directories after settings are loaded
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.RESULTS_DIR, exist_ok=True)

    logger.info("API routes registered")

except Exception as e:
    logger.error("Failed to load heavy dependencies", exc_info=True)

@app.on_event("startup")
async def startup():
    logger.info("Application startup complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=PORT,
    )
