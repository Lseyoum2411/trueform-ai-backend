from typing import Optional, List, Dict, Type
import os
import json
import logging
import time
from datetime import datetime
from app.models.analysis import AnalysisResult, Feedback, FeedbackItem, MetricScore
from app.config import settings
from app.core.movements_registry import normalize_movement_id

logger = logging.getLogger(__name__)

# Log that conditional MediaPipe feedback is active
logger.info("CONDITIONAL MEDIAPIPE FEEDBACK ACTIVE")
print("CONDITIONAL MEDIAPIPE FEEDBACK ACTIVE")


def _get_basketball_analyzer(exercise_type: Optional[str] = None):
    """Lazy-load BasketballAnalyzer only when needed."""
    from app.core.analyzers.basketball import BasketballAnalyzer
    return BasketballAnalyzer(exercise_type=exercise_type)


def _get_golf_analyzer(shot_type: str = "driver"):
    """Lazy-load GolfAnalyzer only when needed."""
    from app.core.analyzers.golf import GolfAnalyzer
    return GolfAnalyzer(shot_type=shot_type)


def _get_weightlifting_analyzer():
    """Lazy-load WeightliftingAnalyzer only when needed."""
    from app.core.analyzers.weightlifting import WeightliftingAnalyzer
    return WeightliftingAnalyzer()


def _get_baseball_analyzer(exercise_type: str = "pitching"):
    """Lazy-load BaseballAnalyzer only when needed."""
    from app.core.analyzers.baseball import BaseballAnalyzer
    return BaseballAnalyzer(exercise_type=exercise_type)


def _get_soccer_analyzer(movement_type: str = "shooting_technique"):
    """Lazy-load SoccerAnalyzer only when needed."""
    from app.core.analyzers.soccer import SoccerAnalyzer
    return SoccerAnalyzer(movement_type=movement_type)


def _get_track_field_analyzer(movement_type: str = "sprint_start"):
    """Lazy-load TrackFieldAnalyzer only when needed."""
    from app.core.analyzers.track_field import TrackFieldAnalyzer
    return TrackFieldAnalyzer(movement_type=movement_type)


def _get_volleyball_analyzer(movement_type: str = "spike_approach"):
    """Lazy-load VolleyballAnalyzer only when needed."""
    from app.core.analyzers.volleyball import VolleyballAnalyzer
    return VolleyballAnalyzer(movement_type=movement_type)


def _get_lacrosse_analyzer(movement_type: str = "shooting"):
    """Lazy-load LacrosseAnalyzer only when needed."""
    from app.core.analyzers.lacrosse import LacrosseAnalyzer
    return LacrosseAnalyzer(movement_type=movement_type)


# Universal metric normalization mapping for weightlifting
# Maps lift-specific metric names to universal scoring keys
WEIGHTLIFTING_METRIC_NORMALIZATION = {
    # Universal metrics (no mapping needed - already standard)
    "depth": "depth",
    "bar_path": "bar_path", 
    "spine_alignment": "spine_alignment",
    "tempo": "tempo",
    
    # Joint angle metrics normalize to descriptive names
    "left_hip": "hip_angle",
    "right_hip": "hip_angle",
    "left_knee": "knee_angle", 
    "right_knee": "knee_angle",
    "left_elbow": "elbow_angle",
    "right_elbow": "elbow_angle",
    "left_shoulder": "shoulder_angle",
    "right_shoulder": "shoulder_angle",
    
    # Lift-specific metrics that need normalization
    "back_angle": "spine_alignment",  # Alternative name for spine_alignment
    "hip_hinge": "hip_angle",  # Descriptive name for hip angle
    "knee_drive": "knee_angle",  # Descriptive name for knee angle
}


class AnalysisService:
    def __init__(self):
        # No analyzers pre-loaded - all analyzers are lazy-loaded per request
        self._ensure_results_directory()
    
    def _ensure_results_directory(self):
        """Ensure results directory exists for saving analysis history."""
        try:
            os.makedirs(settings.RESULTS_DIR, exist_ok=True)
            logger.debug(f"Results directory verified: {settings.RESULTS_DIR}")
        except OSError as e:
            logger.warning(f"Could not create results directory {settings.RESULTS_DIR}: {e}")
    
    def _normalize_weightlifting_metrics(self, metrics: List[MetricScore]) -> Dict[str, float]:
        """
        Normalize lift-specific metric names to universal scoring keys.
        Only applies to weightlifting analyzers.
        """
        normalized_scores = {}
        
        for metric in metrics:
            original_name = metric.name
            normalized_name = WEIGHTLIFTING_METRIC_NORMALIZATION.get(
                original_name, 
                original_name  # Keep original if no mapping exists
            )
            
            # Clamp score to 0-100 range
            clamped_score = max(0.0, min(100.0, metric.score))
            
            # If multiple metrics map to same normalized name, take average
            if normalized_name in normalized_scores:
                normalized_scores[normalized_name] = (
                    normalized_scores[normalized_name] + clamped_score
                ) / 2.0
            else:
                normalized_scores[normalized_name] = clamped_score
            
            # Log unmapped metrics at debug level
            if normalized_name == original_name and original_name not in WEIGHTLIFTING_METRIC_NORMALIZATION.values():
                logger.debug(f"Unmapped weightlifting metric: {original_name} (kept as-is)")
        
        return normalized_scores
    
    def _convert_feedback_items(self, feedback_items: List[FeedbackItem]) -> List[Feedback]:
        """Convert legacy FeedbackItem list to new Feedback list."""
        feedback_list = []
        for item in feedback_items:
            # Parse structured message if it contains action data markers
            observation = None
            impact = None
            how_to_fix = None
            drill = None
            coaching_cue = None
            what_we_saw = None
            what_it_should_feel_like = None
            common_mistake = None
            self_check = None
            
            # Parse basketball-style feedback (OBSERVATION|IMPACT|HOW_TO_FIX|DRILL|CUE)
            if "OBSERVATION|" in item.message:
                parts = item.message.split("|")
                try:
                    obs_idx = parts.index("OBSERVATION")
                    impact_idx = parts.index("IMPACT")
                    how_idx = parts.index("HOW_TO_FIX")
                    drill_idx = parts.index("DRILL")
                    cue_idx = parts.index("CUE")
                    
                    observation = parts[obs_idx + 1] if obs_idx + 1 < len(parts) else None
                    impact = parts[impact_idx + 1] if impact_idx + 1 < len(parts) else None
                    # Extract how_to_fix items (everything between HOW_TO_FIX and DRILL markers)
                    if how_idx + 1 < drill_idx:
                        how_to_fix_parts = parts[how_idx + 1:drill_idx]
                        how_to_fix_str = "|".join(how_to_fix_parts)  # Rejoin with single pipe
                        how_to_fix = how_to_fix_str.split("||") if how_to_fix_str else None  # Split on double pipe delimiter
                        how_to_fix = [item.strip() for item in how_to_fix] if how_to_fix else None  # Clean up whitespace
                    else:
                        how_to_fix = None
                    drill = parts[drill_idx + 1] if drill_idx + 1 < len(parts) else None
                    coaching_cue = parts[cue_idx + 1] if cue_idx + 1 < len(parts) else None
                except (ValueError, IndexError):
                    pass  # Fall back to regular message parsing
            
            # Parse weightlifting beginner-friendly feedback (WHAT_WE_SAW|HOW_TO_FIX|WHAT_IT_SHOULD_FEEL_LIKE|COMMON_MISTAKE|SELF_CHECK)
            if "WHAT_WE_SAW|" in item.message:
                parts = item.message.split("|")
                try:
                    saw_idx = parts.index("WHAT_WE_SAW")
                    how_idx = parts.index("HOW_TO_FIX")
                    feel_idx = parts.index("WHAT_IT_SHOULD_FEEL_LIKE")
                    mistake_idx = parts.index("COMMON_MISTAKE")
                    check_idx = parts.index("SELF_CHECK")
                    
                    what_we_saw = parts[saw_idx + 1] if saw_idx + 1 < len(parts) else None
                    # Extract how_to_fix items (everything between HOW_TO_FIX and WHAT_IT_SHOULD_FEEL_LIKE markers)
                    if how_idx + 1 < feel_idx:
                        how_to_fix_parts = parts[how_idx + 1:feel_idx]
                        how_to_fix_str = "|".join(how_to_fix_parts)
                        how_to_fix = how_to_fix_str.split("||") if how_to_fix_str else None
                        how_to_fix = [item.strip() for item in how_to_fix] if how_to_fix else None
                    else:
                        how_to_fix = None
                    what_it_should_feel_like = parts[feel_idx + 1] if feel_idx + 1 < len(parts) else None
                    common_mistake = parts[mistake_idx + 1] if mistake_idx + 1 < len(parts) else None
                    self_check = parts[check_idx + 1] if check_idx + 1 < len(parts) else None
                except (ValueError, IndexError):
                    pass  # Fall back to regular message parsing
            
            feedback_list.append(Feedback(
                category="form_analysis",
                aspect=item.metric or "general",
                message=item.message,
                severity=item.level,  # Map level -> severity
                timestamp=None,
                observation=observation,
                impact=impact,
                how_to_fix=how_to_fix,
                drill=drill,
                coaching_cue=coaching_cue,
                what_we_saw=what_we_saw,
                what_it_should_feel_like=what_it_should_feel_like,
                common_mistake=common_mistake,
                self_check=self_check
            ))
        return feedback_list
    
    def _clamp_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Ensure all metric scores are within 0-100 range."""
        return {name: max(0.0, min(100.0, score)) for name, score in scores.items()}
    
    def _get_previous_attempt(
        self, 
        video_id: str, 
        sport: str, 
        exercise_type: Optional[str]
    ) -> Optional[AnalysisResult]:
        """
        Retrieve previous analysis result for improvement tracking.
        Currently uses file-based lookup (can be extended to database).
        """
        try:
            # Look for previous results in results directory
            # Pattern: search for results with same sport/exercise_type
            # For now, use a simple file-based approach
            # In production, this would query a database
            
            if not os.path.exists(settings.RESULTS_DIR):
                return None
            
            # Search for previous results (simplified - would use DB in production)
            # For now, return None (first-time user scenario)
            # This method is extensible for future database integration
            logger.debug(f"Previous attempt lookup for {video_id}/{sport}/{exercise_type} - not implemented (first-time user)")
            return None
            
        except Exception as e:
            logger.warning(f"Error retrieving previous attempt: {e}")
            return None
    
    def _save_for_history(self, result: AnalysisResult):
        """Save analysis result to history for future improvement tracking."""
        try:
            if not os.path.exists(settings.RESULTS_DIR):
                self._ensure_results_directory()
            
            result_path = os.path.join(settings.RESULTS_DIR, f"{result.video_id}.json")
            with open(result_path, "w") as f:
                json.dump(result.model_dump(mode='json'), f, default=str)
            
            logger.debug(f"Analysis result saved to history: {result_path}")
            
        except Exception as e:
            logger.warning(f"Error saving analysis result to history: {e}")
    
    def _calculate_improvement_tracking(
        self, 
        current_result: AnalysisResult,
        previous_result: Optional[AnalysisResult]
    ) -> AnalysisResult:
        """Calculate improvement deltas if previous attempt exists."""
        if not previous_result:
            # First-time user - no improvement tracking
            return current_result
        
        # Calculate overall change
        current_result.previous_overall_score = previous_result.overall_score
        current_result.overall_change = current_result.overall_score - previous_result.overall_score
        current_result.previous_attempt_id = previous_result.analysis_id or previous_result.video_id
        current_result.previous_attempt_date = previous_result.analyzed_at
        
        # Calculate metric-level changes
        metric_changes = {}
        for metric_name, current_score in current_result.scores.items():
            if metric_name in previous_result.scores:
                previous_score = previous_result.scores[metric_name]
                metric_changes[metric_name] = current_score - previous_score
            else:
                # New metric - no comparison available
                metric_changes[metric_name] = 0.0
        
        current_result.metric_changes = metric_changes
        
        logger.info(
            f"Improvement tracking: overall_change={current_result.overall_change:.2f}, "
            f"previous_score={previous_result.overall_score:.2f}"
        )
        
        return current_result
    
    async def analyze_video(
        self,
        video_path: str,
        sport: str,
        exercise_type: Optional[str] = None,
        pose_data: Optional[List[Dict]] = None,
    ) -> AnalysisResult:
        """
        Analyze video and return normalized, clamped AnalysisResult with improvement tracking.
        """
        start_time = time.time()
        
        # Handle empty pose_data gracefully
        if not pose_data:
            logger.warning("Empty pose_data provided - returning error result")
            error_result = AnalysisResult(
                video_id="",
                sport=sport,
                exercise_type=exercise_type,
                overall_score=0.0,
                scores={},
                feedback=[
                    Feedback(
                        category="error",
                        aspect="pose_detection",
                        message="No pose data detected. Ensure person is visible in video.",
                        severity="critical",
                        timestamp=None
                    )
                ],
                areas_for_improvement=["Pose detection failed - check video quality"],
                frames_analyzed=0,
                processing_time=time.time() - start_time
            )
            return error_result
        
        try:
            # Normalize movement/exercise type ID using registry
            normalized_exercise_type = None
            if exercise_type:
                normalized_exercise_type = normalize_movement_id(sport, exercise_type)
            
            # Route to appropriate analyzer (using lazy-load functions)
            if sport == "basketball":
                # Basketball analyzer now accepts exercise_type
                exercise_type_for_analyzer = normalized_exercise_type or None
                basketball_analyzer = _get_basketball_analyzer(exercise_type=exercise_type_for_analyzer)
                raw_result = await basketball_analyzer.analyze(pose_data)
                # Update exercise_type in result to normalized value
                if normalized_exercise_type:
                    raw_result.exercise_type = normalized_exercise_type
            elif sport == "golf":
                # Normalize golf shot types (driver -> driver_swing, etc.)
                shot_type = normalized_exercise_type or "driver_swing"
                # Map back to analyzer's expected format
                if shot_type == "driver_swing":
                    shot_type = "driver"
                elif shot_type == "iron_swing":
                    shot_type = "iron"
                elif shot_type == "chip_shot":
                    shot_type = "chip"
                elif shot_type == "putting_stroke":
                    shot_type = "putt"
                golf_analyzer = _get_golf_analyzer(shot_type=shot_type)
                raw_result = await golf_analyzer.analyze(pose_data)
            elif sport == "weightlifting":
                lift_type = normalized_exercise_type or "barbell_squat"
                # Map normalized ID to analyzer's expected format
                from app.config import LIFT_TYPE_MAPPING
                analyzer_lift_type = LIFT_TYPE_MAPPING.get(lift_type, lift_type)
                weightlifting_analyzer = _get_weightlifting_analyzer()
                raw_result = await weightlifting_analyzer.analyze(pose_data, lift_type=analyzer_lift_type)
                # Store normalized exercise_type
                raw_result.exercise_type = lift_type
            elif sport == "baseball":
                exercise_type_for_analyzer = normalized_exercise_type or "pitching"
                baseball_analyzer = _get_baseball_analyzer(exercise_type=exercise_type_for_analyzer)
                raw_result = await baseball_analyzer.analyze(pose_data)
            elif sport == "soccer":
                movement_type = normalized_exercise_type or "shooting_technique"
                soccer_analyzer = _get_soccer_analyzer(movement_type=movement_type)
                raw_result = await soccer_analyzer.analyze(pose_data)
            elif sport == "track_field":
                movement_type = normalized_exercise_type or "sprint_start"
                track_analyzer = _get_track_field_analyzer(movement_type=movement_type)
                raw_result = await track_analyzer.analyze(pose_data)
            elif sport == "volleyball":
                movement_type = normalized_exercise_type or "spike_approach"
                volleyball_analyzer = _get_volleyball_analyzer(movement_type=movement_type)
                raw_result = await volleyball_analyzer.analyze(pose_data)
            elif sport == "lacrosse":
                movement_type = normalized_exercise_type or "shooting"
                lacrosse_analyzer = _get_lacrosse_analyzer(movement_type=movement_type)
                raw_result = await lacrosse_analyzer.analyze(pose_data)
            else:
                raise ValueError(f"Unsupported sport: {sport}")
            
            # Convert legacy feedback format to new format
            new_feedback = []
            if hasattr(raw_result, 'feedback') and raw_result.feedback:
                # If analyzer provided feedback, convert it
                if raw_result.feedback and len(raw_result.feedback) > 0 and isinstance(raw_result.feedback[0], FeedbackItem):
                    new_feedback = self._convert_feedback_items(raw_result.feedback)
                elif raw_result.feedback:
                    # Already in new format (Feedback objects) or empty list
                    new_feedback = [f for f in raw_result.feedback if isinstance(f, Feedback)]
            
            # Build scores dictionary from metrics
            if raw_result.metrics:
                scores = {metric.name: metric.score for metric in raw_result.metrics}
            else:
                scores = {}
            
            # Normalize weightlifting metrics
            if sport == "weightlifting" and raw_result.metrics:
                scores = self._normalize_weightlifting_metrics(raw_result.metrics)
            
            # Clamp all scores to 0-100
            scores = self._clamp_scores(scores)
            
            # Clamp overall_score
            clamped_overall = max(0.0, min(100.0, raw_result.overall_score))
            
            # Convert pose_data to PoseData format for frontend overlay
            from app.models.analysis import PoseData
            pose_data_list = []
            if pose_data:
                for i, frame_data in enumerate(pose_data):
                    landmarks_dict = frame_data.get("landmarks", {})
                    # Convert landmarks from Tuple format to Dict format for JSON serialization
                    landmarks_formatted = {}
                    for key, value in landmarks_dict.items():
                        if isinstance(value, tuple) and len(value) == 3:
                            landmarks_formatted[key] = {"x": value[0], "y": value[1], "z": value[2]}
                        elif isinstance(value, dict):
                            landmarks_formatted[key] = value
                    
                    pose_data_list.append(
                        PoseData(
                            frame_number=i,
                            timestamp=i * (1.0 / 30.0),  # Estimate: 30 FPS
                            landmarks=landmarks_formatted,
                            angles=frame_data.get("angles", {})
                        )
                    )
            
            # Build normalized result
            normalized_result = AnalysisResult(
                video_id=raw_result.video_id,
                sport=raw_result.sport,
                exercise_type=exercise_type or getattr(raw_result, 'exercise_type', None) or raw_result.lift_type,
                lift_type=raw_result.lift_type if sport == "weightlifting" else None,
                overall_score=clamped_overall,
                scores=scores,
                metrics=raw_result.metrics,  # Keep for backward compatibility
                feedback=new_feedback,
                strengths=raw_result.strengths,
                weaknesses=raw_result.weaknesses,
                areas_for_improvement=raw_result.weaknesses,  # Sync with weaknesses
                analyzed_at=datetime.utcnow(),
                created_at=getattr(raw_result, 'created_at', None) or datetime.utcnow(),
                processing_time=time.time() - start_time,
                frames_analyzed=raw_result.raw_data.get('frame_count', len(pose_data)) if raw_result.raw_data else len(pose_data) if pose_data else 0,
                raw_data=raw_result.raw_data,
                analysis_id=getattr(raw_result, 'analysis_id', None),
                pose_data=pose_data_list  # Include pose data for frontend overlay
            )
            
            # Get previous attempt for improvement tracking
            previous_result = self._get_previous_attempt(
                normalized_result.video_id,
                normalized_result.sport,
                normalized_result.exercise_type
            )
            
            # Calculate improvement tracking (only if previous attempt exists)
            if previous_result:
                normalized_result = self._calculate_improvement_tracking(
                    normalized_result,
                    previous_result
                )
            
            # Save result for future improvement tracking
            self._save_for_history(normalized_result)
            
            return normalized_result
            
        except Exception as e:
            logger.error(f"Error during video analysis: {e}", exc_info=True)
            # Return clean error result
            error_result = AnalysisResult(
                video_id="",
                sport=sport,
                exercise_type=exercise_type,
                overall_score=0.0,
                scores={},
                feedback=[
                    Feedback(
                        category="error",
                        aspect="analysis",
                        message=f"Analysis failed: {str(e)}",
                        severity="critical",
                        timestamp=None
                    )
                ],
                areas_for_improvement=[f"Analysis error: {str(e)}"],
                frames_analyzed=len(pose_data) if pose_data else 0,
                processing_time=time.time() - start_time
            )
            return error_result
