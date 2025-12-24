from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class VideoStatusEnum(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class VideoUploadResponse(BaseModel):
    """Response model for video upload endpoint."""
    video_id: str
    filename: str
    sport: str
    exercise_type: Optional[str] = None
    lift_type: Optional[str] = None
    uploaded_at: datetime
    file_size: int
    duration: Optional[float] = None
    status: str = "queued"  # Always "queued" on upload
    next_poll_url: Optional[str] = None  # URL to poll for status


# Backward compatibility alias
VideoUpload = VideoUploadResponse


class VideoStatusResponse(BaseModel):
    """Response model for video status endpoint."""
    video_id: str
    status: VideoStatusEnum  # queued | processing | completed | error
    progress: Optional[float] = Field(None, ge=0, le=100, description="Progress percentage (0-100)")
    analysis_id: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# Legacy alias for backward compatibility
VideoStatus = VideoStatusResponse

