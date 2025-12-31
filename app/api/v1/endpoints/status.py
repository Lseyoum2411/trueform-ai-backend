from fastapi import APIRouter, HTTPException
from app.models.video import VideoStatusResponse, VideoStatusEnum
from app.models.analysis import AnalysisResult
from app.utils.status_helper import get_video_status, get_analysis_result
import os
import json
from app.config import settings

router = APIRouter()


@router.get("/{video_id}", response_model=VideoStatusResponse)
async def get_status(video_id: str):
    status = get_video_status(video_id)
    if not status:
        raise HTTPException(status_code=404, detail="Video not found")
    return status


@router.get("/results/{video_id}", response_model=AnalysisResult)
async def get_results(video_id: str):
    result = get_analysis_result(video_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis results not found")
    return result






<<<<<<< HEAD


=======
>>>>>>> 3cec07eb73eb7a9d41527c45e27aa974b9b882ec
