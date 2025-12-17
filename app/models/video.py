from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class VideoStatusEnum(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class VideoUpload(BaseModel):
    video_id: str
    filename: str
    sport: str
    exercise_type: Optional[str] = None
    lift_type: Optional[str] = None
    uploaded_at: datetime
    file_size: int
    duration: Optional[float] = None


class VideoStatus(BaseModel):
    video_id: str
    status: str
    progress: Optional[float] = None
    analysis_id: Optional[str] = None
    error: Optional[str] = None


class VideoStatusResponse(BaseModel):
    video_id: str
    status: VideoStatusEnum
    progress: Optional[float] = None
    analysis_id: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

