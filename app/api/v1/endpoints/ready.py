"""
Readiness endpoint - Verifies app is ready to handle requests.

Checks:
- API routers are loaded
- Upload directory is writable

Does NOT:
- Load ML models
- Perform heavy checks
- Block startup
"""
from fastapi import APIRouter, HTTPException
import os
from app.config import settings

router = APIRouter()


@router.get("")
async def readiness_check():
    """
    Check if the application is ready to handle requests.
    
    Returns 200 if ready, 503 if not ready.
    """
    checks = {
        "routers_loaded": False,
        "upload_dir_writable": False,
    }
    
    # Check if routers are loaded (if we can import api_router, they're loaded)
    try:
        from app.api.v1.router import api_router
        checks["routers_loaded"] = True
    except Exception:
        checks["routers_loaded"] = False
    
    # Check if upload directory is writable
    try:
        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        # Try to write a test file
        test_file = os.path.join(upload_dir, ".ready_check")
        with open(test_file, "w") as f:
            f.write("ready")
        os.remove(test_file)
        checks["upload_dir_writable"] = True
    except Exception:
        checks["upload_dir_writable"] = False
    
    if all(checks.values()):
        return {
            "status": "ready",
            "checks": checks,
        }
    else:
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready. Checks: {checks}"
        )
