import os
import logging
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response as StarletteResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [request_id=%(request_id)s] - %(message)s",
)

# Store original factory BEFORE overriding it to prevent recursion
_original_log_record_factory = logging.getLogRecordFactory()

def default_record_factory(*args, **kwargs):
    """Custom LogRecord factory that adds request_id field."""
    record = _original_log_record_factory(*args, **kwargs)
    if not hasattr(record, 'request_id'):
        record.request_id = 'startup'
    return record

logging.setLogRecordFactory(default_record_factory)
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", 8000))
logger.info(f"TrueForm AI initializing on port {PORT}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """PostHog startup diagnostics and application lifecycle management."""
    # Startup: PostHog diagnostics
    posthog_key = os.getenv("POSTHOG_API_KEY", "")
    key_present = bool(posthog_key)
    key_prefix = posthog_key[:8] if posthog_key else "N/A"
    
    logger.info(f"PostHog API Key present: {key_present}")
    if key_present:
        logger.info(f"PostHog API Key prefix: {key_prefix}...")
    
    # Test PostHog connection on startup
    if posthog_key:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://us.i.posthog.com/capture/",
                    json={
                        "api_key": posthog_key,
                        "event": "backend_startup_test",
                        "properties": {
                            "distinct_id": "backend_startup",
                        },
                    },
                )
                logger.info(f"PostHog connection test - Status: {response.status_code}, Response: {response.text}")
                if response.status_code == 200:
                    logger.info("PostHog connection successful")
                else:
                    logger.warning(f"PostHog connection test returned non-200 status: {response.status_code}")
        except Exception as e:
            logger.warning(f"PostHog connection test failed: {e}")
    
    logger.info("Application startup complete")
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("TrueForm AI shutting down")


app = FastAPI(
    title="TrueForm AI",
    version="1.0.0",
    description="AI-powered sports form analysis",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ----------------------------------------------------
# DEBUG MIDDLEWARE (TEMPORARY)
# Logs request/response and fails open
# ----------------------------------------------------

# Request ID middleware (must be first)
from app.utils.request_id import RequestIDMiddleware
app.add_middleware(RequestIDMiddleware)

@app.middleware("http")
async def debug_middleware(request: Request, call_next):
    from app.utils.request_id import get_request_id
    request_id = get_request_id(request)
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

# Serve uploaded videos (for frontend video playback)
try:
    from fastapi.staticfiles import StaticFiles
    from app.config import settings
    import os
    
    # Ensure uploads directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Mount static files for video serving
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
    logger.info(f"✓ Video uploads directory mounted at /uploads")
except Exception as e:
    logger.warning(f"Could not mount uploads directory: {e}", exc_info=True)

# ----------------------------------------------------
# Error handlers (consistent error responses)
# ----------------------------------------------------

from fastapi.exceptions import RequestValidationError
from app.models.error import ErrorResponse

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPException with consistent error format."""
    from app.utils.request_id import get_request_id
    request_id = get_request_id(request)
    
    # Map status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        413: "PAYLOAD_TOO_LARGE",
        422: "VALIDATION_ERROR",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
    }
    error_code = error_code_map.get(exc.status_code, f"HTTP_{exc.status_code}")
    
    error_response = ErrorResponse(
        error_code=error_code,
        message=exc.detail,
        request_id=request_id,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(exclude_none=True),
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with consistent format."""
    from app.utils.request_id import get_request_id
    request_id = get_request_id(request)
    
    # Extract first error message
    errors = exc.errors()
    message = errors[0].get("msg", "Validation error") if errors else "Validation error"
    
    error_response = ErrorResponse(
        error_code="VALIDATION_ERROR",
        message=message,
        request_id=request_id,
        detail=str(errors) if len(errors) > 1 else None,
    )
    return JSONResponse(
        status_code=422,
        content=error_response.model_dump(exclude_none=True),
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions safely."""
    from app.utils.request_id import get_request_id
    request_id = get_request_id(request)
    
    logger.error(f"Unhandled exception: {exc}", exc_info=True, extra={"request_id": request_id})
    
    error_response = ErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        request_id=request_id,
    )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(exclude_none=True),
    )

# ----------------------------------------------------
# Startup/Shutdown handled by lifespan context manager above
# 
# IMPORTANT: No heavy work allowed at import or startup.
# - ML models (MediaPipe, OpenCV, analyzers) must be lazy-loaded
# - Heavy imports must be deferred to request handlers or background tasks
# - Startup diagnostics should only log and test connections
# ----------------------------------------------------

# ----------------------------------------------------
# Local run
# ----------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=True)
