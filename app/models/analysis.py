from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# Legacy models for backward compatibility with existing analyzers
class FeedbackItem(BaseModel):
    level: str
    message: str
    metric: Optional[str] = None


class MetricScore(BaseModel):
    name: str
    score: float
    value: Optional[Any] = None
    unit: Optional[str] = None


# New structured models
class PoseData(BaseModel):
    frame_number: int
    timestamp: float
    landmarks: Dict[str, Dict[str, float]]
    angles: Optional[Dict[str, float]] = None


class Feedback(BaseModel):
    category: str
    aspect: str
    message: str
    severity: str = "info"
    timestamp: Optional[float] = None
    # Optional structured fields for actionable recommendations (basketball-specific)
    observation: Optional[str] = None
    impact: Optional[str] = None
    how_to_fix: Optional[List[str]] = None
    drill: Optional[str] = None
    coaching_cue: Optional[str] = None
    recommendation: Optional[str] = None  # Legacy/fallback recommendation text


class AnalysisResult(BaseModel):
    video_id: str
    sport: str
    exercise_type: Optional[str] = None
    lift_type: Optional[str] = None  # Legacy field for backward compatibility

    # Absolute form quality
    overall_score: float = Field(..., ge=0, le=100)
    scores: Dict[str, float] = Field(default_factory=dict)

    # Improvement tracking (optional)
    previous_overall_score: Optional[float] = None
    overall_change: Optional[float] = None
    metric_changes: Optional[Dict[str, float]] = None
    previous_attempt_id: Optional[str] = None
    previous_attempt_date: Optional[datetime] = None

    # Legacy fields for backward compatibility (accept old analyzer outputs)
    analysis_id: Optional[str] = None
    metrics: List[MetricScore] = Field(default_factory=list)
    
    # New structured data
    pose_data: List[PoseData] = Field(default_factory=list)
    # Accept both old (FeedbackItem) and new (Feedback) formats - conversion handled in service
    feedback: Union[List[Feedback], List[FeedbackItem]] = Field(default_factory=list)
    
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)  # Legacy
    areas_for_improvement: List[str] = Field(default_factory=list)
    
    # Timestamps and metadata
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: Optional[datetime] = None  # Legacy
    processing_time: float = 0.0
    frames_analyzed: int = 0
    raw_data: Optional[Dict[str, Any]] = None

    @field_validator('overall_score')
    @classmethod
    def clamp_overall_score(cls, v: float) -> float:
        return max(0.0, min(100.0, float(v)))

    def model_post_init(self, __context):
        """Post-initialization: sync fields and populate scores dict from metrics."""
        # Sync weaknesses and areas_for_improvement
        if self.weaknesses and not self.areas_for_improvement:
            self.areas_for_improvement = self.weaknesses
        elif self.areas_for_improvement and not self.weaknesses:
            self.weaknesses = self.areas_for_improvement
        
        # Sync created_at and analyzed_at
        if not self.created_at:
            self.created_at = self.analyzed_at
        
        # Build scores dict from metrics if not provided (backward compatibility)
        if not self.scores and self.metrics:
            for metric in self.metrics:
                clamped_score = max(0.0, min(100.0, metric.score))
                self.scores[metric.name] = clamped_score
        
        # Generate analysis_id if not provided
        if not self.analysis_id:
            import uuid
            self.analysis_id = str(uuid.uuid4())
        
        # Calculate frames_analyzed from raw_data if available
        if self.frames_analyzed == 0 and self.raw_data and "frame_count" in self.raw_data:
            self.frames_analyzed = self.raw_data["frame_count"]
        
        # Note: Feedback conversion from FeedbackItem to Feedback is handled in AnalysisService
        # This keeps the model clean and handles conversion at the service layer
