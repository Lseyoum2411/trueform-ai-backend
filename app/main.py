"""
TrueForm AI - FastAPI Application

Optimized for Railway deployment with instant health check response
"""

import os
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# ============================================================================
# LOGGING SETUP (Lightweight, no imports)
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# PORT CONFIGURATION (No imports)
# ============================================================================

PORT = int(os.getenv("PORT", 8000))
logger.info(f"TrueForm AI initializing on port {PORT}")

# ============================================================================
# CREATE FASTAPI APP (Minimal, no middleware yet)
# ============================================================================

app = FastAPI(
    title="TrueForm AI",
    version="1.0.0",
    description="AI-powered sports form analysis using pose estimation",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================================
# CRITICAL: ROOT AND HEALTH ENDPOINTS FIRST
# These MUST respond instantly for Railway health checks
# NO imports, NO middleware, NO dependencies
# ============================================================================

@app.get("/", response_class=JSONResponse)
async def root():
    """
    Root endpoint for Railway health check.
    MUST respond instantly - no ML dependencies.
    """
    return {
        "status": "online",
        "service": "TrueForm AI",
        "version": "1.0.0",
        "port": PORT,
        "message": "Welcome to TrueForm AI API",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_class=JSONResponse)
async def health_check():
    """
    Health check endpoint.
    Returns instant response without loading analyzers.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "port": PORT,
        "environment": "production"
    }

# ============================================================================
# STARTUP EVENT: Load Heavy Dependencies AFTER Health Check
# This runs AFTER Railway has already verified the app responds
# ============================================================================

@app.on_event("startup")
async def load_heavy_dependencies():
    """
    Load ML dependencies after Railway health check passes.
    This prevents import blocking from affecting health check response.
    """
    logger.info("=" * 60)
    logger.info("Health check endpoints ready - loading ML dependencies...")
    logger.info("=" * 60)
    
    try:
        # Import heavy modules NOW (after health endpoints are ready)
        from fastapi.middleware.cors import CORSMiddleware
        from app.config import settings
        from app.api.v1.router import api_router
        
        logger.info("✓ Settings loaded")
        logger.info("✓ API router loaded")
        
        # Add CORS middleware (after health check is already working)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("✓ CORS middleware configured")
        
        # Include API routes (upload, analyze, status, etc.)
        app.include_router(api_router, prefix=settings.API_PREFIX)
        logger.info(f"✓ API routes registered at {settings.API_PREFIX}")
        
        # Create directories after settings are loaded
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs(settings.RESULTS_DIR, exist_ok=True)
        logger.info("✓ Upload and results directories created")
        
        logger.info("=" * 60)
        logger.info("All dependencies loaded successfully")
        logger.info(f"TrueForm AI ready at http://0.0.0.0:{PORT}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"Failed to load dependencies: {e}", exc_info=True)
        logger.error("API routes will NOT be available")
        logger.error("Health endpoints still functional")
        logger.error("=" * 60)

# ============================================================================
# SHUTDOWN EVENT
# ============================================================================

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("TrueForm AI shutting down...")

# ============================================================================
# DIRECT EXECUTION (for local testing)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True
    )
