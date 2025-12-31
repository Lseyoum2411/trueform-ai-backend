from typing import Optional, Dict, Any
from datetime import datetime
from app.models.video import VideoStatusResponse, VideoStatusEnum
from app.models.analysis import AnalysisResult
import os
import json
from app.config import settings

video_statuses: Dict[str, Dict[str, Any]] = {}
analysis_results: Dict[str, AnalysisResult] = {}


def update_video_status(
    video_id: str,
    status: str,
    progress: Optional[float] = None,
    error: Optional[str] = None,
    analysis_id: Optional[str] = None,
):
    if progress is not None:
        progress = max(0.0, min(100.0, progress))
    
    if video_id not in video_statuses:
        video_statuses[video_id] = {
            "video_id": video_id,
            "status": status,
            "progress": progress or 0.0,
            "analysis_id": analysis_id,
            "error": error,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
    else:
        video_statuses[video_id].update({
            "status": status,
            "progress": progress if progress is not None else video_statuses[video_id].get("progress", 0.0),
            "analysis_id": analysis_id or video_statuses[video_id].get("analysis_id"),
            "error": error,
            "updated_at": datetime.now(),
        })


def get_video_status(video_id: str) -> Optional[VideoStatusResponse]:
    if video_id not in video_statuses:
        return None
    
    status_data = video_statuses[video_id]
    try:
        status_enum = VideoStatusEnum(status_data["status"])
    except ValueError:
        status_enum = VideoStatusEnum.QUEUED
    
    return VideoStatusResponse(
        video_id=video_id,
        status=status_enum,
        progress=status_data.get("progress"),
        analysis_id=status_data.get("analysis_id"),
        error=status_data.get("error"),
        created_at=status_data.get("created_at"),
        updated_at=status_data.get("updated_at"),
    )


def get_analysis_result(video_id: str) -> Optional[AnalysisResult]:
    if video_id in analysis_results:
        return analysis_results[video_id]
    
    result_path = os.path.join(settings.RESULTS_DIR, f"{video_id}.json")
    if os.path.exists(result_path):
        with open(result_path, "r") as f:
            data = json.load(f)
            return AnalysisResult(**data)
    
    return None

