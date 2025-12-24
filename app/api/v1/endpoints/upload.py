from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from app.models.video import VideoUpload, VideoStatus
from app.models.analysis import AnalysisResult
from app.services.analysis_service import AnalysisService
from app.config import settings, SUPPORTED_SPORTS, EXERCISE_TYPES, EXERCISE_ALIASES
from app.utils.status_helper import update_video_status, video_statuses, analysis_results
from app.core.pose_estimator import PoseEstimator
import os
import uuid
from datetime import datetime
import cv2
from typing import Optional
import json

router = APIRouter()


def get_video_duration(video_path: str) -> float:
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = frame_count / fps if fps > 0 else 0
    cap.release()
    return duration


async def process_video_analysis(video_id: str, video_path: str, sport: str, exercise_type: Optional[str]):
    try:
        update_video_status(video_id, "processing", progress=10.0)
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        update_video_status(video_id, "processing", progress=20.0)
        
        pose_estimator = PoseEstimator()
        update_video_status(video_id, "processing", progress=30.0)
        
        pose_data = pose_estimator.analyze_video(video_path)
        update_video_status(video_id, "processing", progress=60.0)
        
        if not pose_data:
            raise ValueError("No pose data extracted from video. Make sure the video contains a person and is a valid video file.")
        
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
        
    except Exception as e:
        error_msg = str(e)
        update_video_status(video_id, "error", progress=0.0, error=error_msg)
        print(f"Error processing video {video_id}: {error_msg}")


@router.post("", response_model=VideoUpload)
async def upload_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    sport: str = Form(...),
    exercise_type: Optional[str] = Form(None),
):
    # Debug logging: log received form fields (for troubleshooting multipart issues)
    logger.info(f"Upload received - sport: {sport}, exercise_type: {exercise_type}, filename: {video.filename if video else 'MISSING'}")
    
    if sport not in SUPPORTED_SPORTS:
        raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")
    
    if sport == "basketball":
        exercise_type = "jumpshot"
    elif sport in ["golf", "weightlifting"]:
        if not exercise_type:
            raise HTTPException(status_code=400, detail=f"exercise_type required for {sport}")
        
        if exercise_type in EXERCISE_ALIASES:
            exercise_type = EXERCISE_ALIASES[exercise_type]
        
        if exercise_type not in EXERCISE_TYPES.get(sport, []):
            raise HTTPException(status_code=400, detail=f"Unsupported exercise_type '{exercise_type}' for sport '{sport}'")
    
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
    
    video_upload = VideoUpload(
        video_id=video_id,
        filename=filename,
        sport=sport,
        exercise_type=exercise_type,
        lift_type=exercise_type if sport == "weightlifting" else None,
        uploaded_at=datetime.now(),
        file_size=file_size,
        duration=duration,
    )
    
    update_video_status(video_id, "queued", progress=0.0)
    
    background_tasks.add_task(process_video_analysis, video_id, file_path, sport, exercise_type)
    
    return video_upload


@router.get("/status/{video_id}", response_model=VideoStatus)
async def get_status(video_id: str):
    if video_id not in video_statuses:
        raise HTTPException(status_code=404, detail="Video not found")
    return video_statuses[video_id]


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

