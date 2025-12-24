"""
Request ID middleware for correlation tracking.

Generates a unique request_id (UUID) for each request and attaches it to:
- Request state (accessible in handlers)
- Response headers
- Log messages
"""
import uuid
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to generate and attach request_id to all requests."""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Attach to request state for use in handlers
        request.state.request_id = request_id
        
        # Update logger context for this request
        old_factory = logging.getLogRecordFactory()
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.request_id = request_id
            return record
        logging.setLogRecordFactory(record_factory)
        
        try:
            response = await call_next(request)
            # Add request_id to response headers
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            # Restore original factory
            logging.setLogRecordFactory(old_factory)


def get_request_id(request: Request) -> str:
    """Get request_id from request state."""
    return getattr(request.state, "request_id", "unknown")

