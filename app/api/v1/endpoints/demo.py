"""
Demo endpoint - Returns static example responses for frontend development and demos.

This endpoint does NOT:
- Trigger ML model loading
- Access files
- Perform any processing
- Risk backend stability

Returns realistic sample data matching actual API responses.
"""
from fastapi import APIRouter
from datetime import datetime
from app.models.video import VideoUploadResponse, VideoStatusResponse, VideoStatusEnum
from app.models.analysis import AnalysisResult

router = APIRouter()


@router.get("", response_model=dict)
async def get_demo():
    """
    Get demo examples of upload, status, and results responses.
    
    Returns static JSON examples that match the actual API responses.
    Useful for frontend development, UI mocking, and demos.
    """
    # Sample upload response (what you get after POST /api/v1/upload)
    sample_upload_response = VideoUploadResponse(
        video_id="demo-550e8400-e29b-41d4-a716-446655440000",
        filename="demo-550e8400-e29b-41d4-a716-446655440000.mp4",
        sport="basketball",
        exercise_type="jumpshot",
        lift_type=None,
        uploaded_at=datetime(2025, 1, 23, 12, 0, 0),
        file_size=5242880,
        duration=5.5,
        status="queued",
        next_poll_url="/api/v1/upload/status/demo-550e8400-e29b-41d4-a716-446655440000",
    )
    
    # Sample status response - processing (what you get from GET /api/v1/upload/status/{video_id})
    sample_status_processing = VideoStatusResponse(
        video_id="demo-550e8400-e29b-41d4-a716-446655440000",
        status=VideoStatusEnum.PROCESSING,
        progress=60.0,
        analysis_id=None,
        error=None,
        created_at=datetime(2025, 1, 23, 12, 0, 0),
        updated_at=datetime(2025, 1, 23, 12, 0, 5),
    )
    
    # Sample status response - completed
    sample_status_completed = VideoStatusResponse(
        video_id="demo-550e8400-e29b-41d4-a716-446655440000",
        status=VideoStatusEnum.COMPLETED,
        progress=100.0,
        analysis_id="demo-abc123-def456-ghi789",
        error=None,
        created_at=datetime(2025, 1, 23, 12, 0, 0),
        updated_at=datetime(2025, 1, 23, 12, 5, 30),
    )
    
    # Sample results response (what you get from GET /api/v1/upload/results/{video_id})
    sample_results_response = AnalysisResult(
        video_id="demo-550e8400-e29b-41d4-a716-446655440000",
        analysis_id="demo-abc123-def456-ghi789",
        sport="basketball",
        exercise_type="jumpshot",
        lift_type=None,
        overall_score=85.5,
        scores={
            "stability": 90.0,
            "alignment": 85.0,
            "rhythm": 82.0,
            "release": 88.0,
        },
        feedback=[
            {
                "category": "form_analysis",
                "aspect": "stability",
                "message": "Good base stability throughout the shot",
                "severity": "info",
                "timestamp": None,
            },
            {
                "category": "form_analysis",
                "aspect": "alignment",
                "message": "Excellent follow-through position",
                "severity": "positive",
                "timestamp": None,
            },
            {
                "category": "form_analysis",
                "aspect": "rhythm",
                "message": "Slight forward lean during release",
                "severity": "warning",
                "timestamp": None,
            },
        ],
        strengths=["Excellent follow-through", "Good balance", "Consistent release"],
        weaknesses=["Slight forward lean"],
        areas_for_improvement=["Slight forward lean", "Timing could improve"],
        frames_analyzed=150,
        processing_time=12.5,
        analyzed_at=datetime(2025, 1, 23, 12, 5, 30),
    )
    
    return {
        "upload_response": sample_upload_response.model_dump(mode='json'),
        "status_response_processing": sample_status_processing.model_dump(mode='json'),
        "status_response_completed": sample_status_completed.model_dump(mode='json'),
        "results_response": sample_results_response.model_dump(mode='json'),
        "note": "These are static examples. Use actual endpoints for real data.",
        "endpoints": {
            "upload": "POST /api/v1/upload",
            "status": "GET /api/v1/upload/status/{video_id}",
            "results": "GET /api/v1/upload/results/{video_id}",
            "sports": "GET /api/v1/sports",
        },
    }
