"""
Standard error response models for consistent error handling.
"""
from pydantic import BaseModel
from typing import Optional


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error_code: str
    message: str
    request_id: Optional[str] = None
    detail: Optional[str] = None  # Additional context if needed


