import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from starlette.responses import Response as StarletteResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", 8000))
logger.info(f"Starting app on port {PORT}")

app = FastAPI()

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
# ULTRA-MINIMAL HEALTH ENDPOINTS
# ----------------------------------------------------

@app.get("/", response_class=PlainTextResponse)
async def root():
    return "OK"


@app.get("/health", response_class=PlainTextResponse)
async def health():
    return "OK"
