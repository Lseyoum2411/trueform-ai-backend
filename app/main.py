import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response as StarletteResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", 8000))
logger.info(f"TrueForm AI initializing on port {PORT}")

app = FastAPI(
    title="TrueForm AI",
    version="1.0.0",
    description="AI-powered sports form analysis",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ----------------------------------------------------
# DEBUG MIDDLEWARE (TEMPORARY)
# Logs request/response and fails open
# ----------------------------------------------------

@app.middleware("http")
async def debug_middleware(request: Request, call_next):
    logger.info(f"→ Request: {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        logger.info(f"← Response: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"✗ Middleware error: {e}", exc_info=True)
        return StarletteResponse(content=b"ERROR", status_code=500)

# ----------------------------------------------------
# Health endpoints (MUST be instant for Railway)
# ----------------------------------------------------

@app.get("/", response_class=JSONResponse)
async def root():
    return {"status": "ok"}


@app.get("/health", response_class=JSONResponse)
async def health():
    return {"status": "ok"}

# ----------------------------------------------------
# CORS middleware (at module level, before startup)
# ----------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("✓ CORS middleware registered")

# ----------------------------------------------------
# API router (at module level, before startup)
# ----------------------------------------------------

try:
    from app.api.v1.router import api_router
    app.include_router(api_router, prefix="/api/v1")
    logger.info("✓ API routes registered at /api/v1")
except Exception as e:
    logger.error(f"Failed to load API router: {e}", exc_info=True)

# ----------------------------------------------------
# Startup event — Optional pre-warm (NO registration)
# ----------------------------------------------------

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup complete")

# ----------------------------------------------------
# Shutdown
# ----------------------------------------------------

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("TrueForm AI shutting down")

# ----------------------------------------------------
# Local run
# ----------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=True)
