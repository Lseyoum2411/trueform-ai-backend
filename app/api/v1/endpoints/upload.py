from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from app.models.video import VideoUpload, VideoStatusResponse
from app.models.analysis import AnalysisResult
from app.services.analysis_service import AnalysisService
from app.config import settings, SUPPORTED_SPORTS, EXERCISE_TYPES, EXERCISE_ALIASES
from app.utils.status_helper import update_video_status, video_statuses, analysis_results
from app.utils.rate_limiter import can_start_analysis, start_analysis, finish_analysis
from app.core.pose_estimator import PoseEstimator
import os
import uuid
from datetime import datetime
import cv2
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_video_duration(video_path: str) -> float:
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = frame_count / fps if fps > 0 else 0
    cap.release()
    return duration


async def process_video_analysis(video_id: str, video_path: str, sport: str, exercise_type: Optional[str]):
    """
    Background task to process video analysis.
    Runs asynchronously via BackgroundTasks to avoid blocking upload response.
    """
    # Check rate limit before starting
    if not can_start_analysis(video_id):
        error_msg = "Analysis queue is full. Please try again later."
        update_video_status(video_id, "error", progress=0.0, error=error_msg)
        logger.warning(f"Analysis rejected due to rate limit for {video_id}")
        return
    
    start_analysis(video_id)
    logger.info(f"Background analysis started for video_id: {video_id}, sport: {sport}, exercise_type: {exercise_type}")
    
    try:
        update_video_status(video_id, "processing", progress=10.0)
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        update_video_status(video_id, "processing", progress=20.0)
        logger.info(f"Video file found, initializing pose estimation for {video_id}")
        
        pose_estimator = PoseEstimator()
        update_video_status(video_id, "processing", progress=30.0)
        
        pose_data = pose_estimator.analyze_video(video_path)
        update_video_status(video_id, "processing", progress=60.0)
        
        if not pose_data:
            raise ValueError("No pose data extracted from video. Ensure person is visible and video is valid.")
        
        logger.info(f"Pose data extracted ({len(pose_data)} frames), running analysis for {video_id}")
        service = AnalysisService()
        update_video_status(video_id, "processing", progress=70.0)
        
        result = await service.analyze_video(video_path, sport, exercise_type, pose_data)
        update_video_status(video_id, "processing", progress=90.0)
        
        result.analysis_id = str(uuid.uuid4())
        result.video_id = video_id
        
        analysis_results[video_id] = result
        
        # Ensure results directory exists before saving
        os.makedirs(settings.RESULTS_DIR, exist_ok=True)
        result_path = os.path.join(settings.RESULTS_DIR, f"{video_id}.json")
        with open(result_path, "w") as f:
            json.dump(result.model_dump(mode='json'), f, default=str)
        
        update_video_status(video_id, "completed", progress=100.0, analysis_id=result.analysis_id)
        logger.info(f"Analysis completed successfully for video_id: {video_id}, analysis_id: {result.analysis_id}")
        finish_analysis(video_id)
        
    except Exception as e:
        # Sanitize error message (no stack traces, no internal paths)
        error_msg = str(e)
        # Remove file paths from error messages
        if "\\" in error_msg or "/" in error_msg:
            # Keep only the error type and descriptive message
            error_type = type(e).__name__
            error_msg = f"{error_type}: {error_msg.split(':', 1)[-1].strip()}" if ":" in error_msg else f"{error_type}: {error_msg}"
        
        update_video_status(video_id, "error", progress=0.0, error=error_msg)
        logger.error(f"Analysis failed for video_id: {video_id}, error: {error_msg}", exc_info=True)
        finish_analysis(video_id)


@router.post("", response_model=VideoUpload)
async def upload_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    sport: str = Form(...),
    exercise_type: Optional[str] = Form(None),
):
    # Debug logging: log received form fields (for troubleshooting multipart issues)
    logger.info(f"Upload received - sport: {sport}, exercise_type: {exercise_type}, filename: {video.filename if video else 'MISSING'}")
    
    # Validate sport
    if sport not in SUPPORTED_SPORTS:
        valid_sports = ", ".join(SUPPORTED_SPORTS)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sport '{sport}'. Supported sports: {valid_sports}"
        )
    
    # Validate exercise_type based on sport requirements
    if sport == "basketball":
        exercise_type = "jumpshot"
    elif sport in ["golf", "weightlifting"]:
        if not exercise_type:
            raise HTTPException(
                status_code=400,
                detail=f"exercise_type is required for {sport}. Valid options: {', '.join(EXERCISE_TYPES.get(sport, []))}"
            )
        
        # Handle aliases
        if exercise_type in EXERCISE_ALIASES:
            exercise_type = EXERCISE_ALIASES[exercise_type]
        
        # Validate exercise_type against sport
        valid_exercises = EXERCISE_TYPES.get(sport, [])
        if exercise_type not in valid_exercises:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid exercise_type '{exercise_type}' for sport '{sport}'. Valid options: {', '.join(valid_exercises)}"
            )
    
    video_id = str(uuid.uuid4())
    file_extension = os.path.splitext(video.filename)[1]
    filename = f"{video_id}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    file_size = 0
    with open(file_path, "wb") as f:
        while chunk := await video.read(1024 * 1024):
            file_size += len(chunk)
            f.write(chunk)
            if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                os.remove(file_path)
                raise HTTPException(
                    status_code=413,
                    detail=f"File size exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit"
                )
    
    duration = get_video_duration(file_path)
    if duration > settings.MAX_VIDEO_DURATION_SEC:
        os.remove(file_path)
        raise HTTPException(
            status_code=400,
            detail=f"Video duration exceeds {settings.MAX_VIDEO_DURATION_SEC} seconds"
        )
    
    # Check rate limit before queuing analysis
    if not can_start_analysis(video_id):
        os.remove(file_path)  # Clean up uploaded file
        raise HTTPException(
            status_code=429,
            detail="Analysis queue is full. Please try again later."
        )
    
    update_video_status(video_id, "queued", progress=0.0)
    logger.info(f"Video uploaded successfully, video_id: {video_id}, queued for background processing")
    
    # Build status polling URL for frontend
    next_poll_url = f"{settings.API_PREFIX}/upload/status/{video_id}"
    
    video_upload = VideoUpload(
        video_id=video_id,
        filename=filename,
        sport=sport,
        exercise_type=exercise_type,
        lift_type=exercise_type if sport == "weightlifting" else None,
        uploaded_at=datetime.now(),
        file_size=file_size,
        duration=duration,
        status="queued",
        next_poll_url=next_poll_url,
        next_steps=f"Video uploaded successfully. Poll {next_poll_url} to track analysis progress. Status will change from 'queued' to 'processing' to 'completed'.",
    )
    
    # Process analysis in background (non-blocking)
    background_tasks.add_task(process_video_analysis, video_id, file_path, sport, exercise_type)
    
    return video_upload


@router.get("/status/{video_id}", response_model=VideoStatusResponse)
async def get_status(video_id: str):
    """
    Get video processing status.
    
    Returns current status (queued | processing | completed | error) and progress.
    """
    if video_id not in video_statuses:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Convert status dict to VideoStatusResponse model
    status_data = video_statuses[video_id]
    from app.models.video import VideoStatusEnum
    
    try:
        status_enum = VideoStatusEnum(status_data.get("status", "queued"))
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


@router.get("/results/{video_id}", response_model=AnalysisResult)
async def get_results(video_id: str):
    if video_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis results not found")
    return analysis_results[video_id]


@router.delete("/video/{video_id}")
async def delete_video(video_id: str):
    if video_id not in video_statuses:
        raise HTTPException(status_code=404, detail="Video not found")
    
    video_status = video_statuses[video_id]
    filename = None
    for status in video_statuses.values():
        if status.video_id == video_id:
            filename = f"{video_id}.mp4"
            break
    
    if filename:
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    result_path = os.path.join(settings.RESULTS_DIR, f"{video_id}.json")
    if os.path.exists(result_path):
        os.remove(result_path)
    
    video_statuses.pop(video_id, None)
    analysis_results.pop(video_id, None)
    
    return {"message": "Video and analysis deleted successfully"}

