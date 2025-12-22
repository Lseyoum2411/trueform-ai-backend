"""
TrueForm AI - FastAPI Application

Correct lifecycle structure for Railway deployment
"""

import os
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# ------------------------------------------------------------------
# Logging (lightweight)
# ------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Port
# ------------------------------------------------------------------

PORT = int(os.getenv("PORT", 8000))
logger.info(f"TrueForm AI initializing on port {PORT}")

# ------------------------------------------------------------------
# Create FastAPI app
# ------------------------------------------------------------------

app = FastAPI(
    title="TrueForm AI",
    version="1.0.0",
    description="AI-powered sports form analysis",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ------------------------------------------------------------------
# Root + Health (MUST be instant for Railway)
# ------------------------------------------------------------------

@app.get("/", response_class=JSONResponse)
async def root():
    return {
        "status": "online",
        "service": "TrueForm AI",
        "version": "1.0.0",
        "port": PORT,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_class=JSONResponse)
async def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "port": PORT,
    }

# ------------------------------------------------------------------
# Load config + register middleware + routers (BEFORE startup)
# ------------------------------------------------------------------

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
    logger.info("✓ CORS middleware registered")

    app.include_router(api_router, prefix=settings.API_PREFIX)
    logger.info(f"✓ API routes registered at {settings.API_PREFIX}")

    # Create directories after settings are loaded
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.RESULTS_DIR, exist_ok=True)
    logger.info("✓ Upload and results directories created")

except Exception as e:
    logger.error("Failed to load configuration", exc_info=True)

# ------------------------------------------------------------------
# Startup event — PRE-WARM ONLY (NO registration)
# ------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    logger.info("Pre-warming ML dependencies (optional)...")
    try:
        from app.core.pose_estimator import PoseEstimator
        _ = PoseEstimator()
        logger.info("✓ PoseEstimator loaded")
    except Exception as e:
        logger.warning("ML pre-warm failed, will load on first request")

# ------------------------------------------------------------------
# Shutdown
# ------------------------------------------------------------------

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("TrueForm AI shutting down")

# ------------------------------------------------------------------
# Local run
# ------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=True)
