from typing import List, Dict, Optional
from datetime import datetime
import numpy as np
import uuid
import logging
from app.core.analyzers.base import BaseAnalyzer
from app.models.analysis import AnalysisResult, MetricScore, FeedbackItem

logger = logging.getLogger(__name__)


class GolfAnalyzer(BaseAnalyzer):
    def __init__(self, shot_type: str = "driver"):
        super().__init__()
        self.shot_type = shot_type.lower()
        if self.shot_type not in ["driver", "iron"]:
            logger.warning(f"Unknown shot_type '{shot_type}', defaulting to 'driver'")
            self.shot_type = "driver"
        
        # Shot-specific biomechanical parameters
        if self.shot_type == "driver":
            # Driver: Power-focused, upward launch
            self.stance_width_ideal = 0.20  # Wider stance for stability
            self.stance_width_tolerance = 0.05
            self.spine_tilt_ideal = -0.15  # Tilt away from target (negative = right tilt for right-handed)
            self.spine_tilt_tolerance = 0.08
            self.backswing_rotation_ideal = 95.0  # Degrees - larger rotation
            self.backswing_rotation_tolerance = 15.0
            self.weight_transfer_ideal = 0.65  # More weight transfer to front foot
            self.weight_transfer_tolerance = 0.15
            self.balance_emphasis = "power"  # Emphasis on power generation
            self.follow_through_height_ideal = 0.85  # Higher finish
            self.follow_through_tolerance = 0.10
        else:  # iron
            # Iron: Precision-focused, downward compression
            self.stance_width_ideal = 0.15  # Narrower stance for control
            self.stance_width_tolerance = 0.04
            self.spine_tilt_ideal = -0.05  # Minimal tilt, more neutral
            self.spine_tilt_tolerance = 0.05
            self.backswing_rotation_ideal = 85.0  # Degrees - controlled rotation
            self.backswing_rotation_tolerance = 12.0
            self.weight_transfer_ideal = 0.55  # Balanced weight transfer
            self.weight_transfer_tolerance = 0.12
            self.balance_emphasis = "stability"  # Emphasis on balance and compression
            self.follow_through_height_ideal = 0.70  # Controlled finish
            self.follow_through_tolerance = 0.10
        
        # Common parameters for both shot types
        self.tempo_ideal = 0.8  # Smooth, controlled tempo
        self.tempo_tolerance = 0.2
        
        logger.info(f"GolfAnalyzer initialized for shot_type: {self.shot_type}")
    
    async def analyze(self, pose_data: List[Dict], shot_type: Optional[str] = None) -> AnalysisResult:
        if shot_type:
            self.shot_type = shot_type.lower()
            logger.info(f"Shot type updated to: {self.shot_type}")
        
        if not pose_data:
            return self._create_empty_result()
        
        metrics = []
        feedback = []
        strengths = []
        weaknesses = []
        
        landmarks_list = [frame.get("landmarks", {}) for frame in pose_data]
        angles_list = [frame.get("angles", {}) for frame in pose_data]
        
        # Analyze key golf metrics with shot-specific thresholds
        stance_width_score = self._analyze_stance_width(landmarks_list, metrics, feedback)
        spine_tilt_score = self._analyze_spine_tilt(landmarks_list, metrics, feedback)
        backswing_rotation_score = self._analyze_backswing_rotation(angles_list, landmarks_list, metrics, feedback)
        weight_transfer_score = self._analyze_weight_transfer(landmarks_list, metrics, feedback)
        balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
        tempo_score = self._analyze_tempo(pose_data, metrics, feedback)
        follow_through_score = self._analyze_follow_through(landmarks_list, angles_list, metrics, feedback)
        
        # Calculate overall score
        overall_score = np.mean([
            stance_width_score,
            spine_tilt_score,
            backswing_rotation_score,
            weight_transfer_score,
            balance_score,
            tempo_score,
            follow_through_score,
        ])
        
        # Categorize strengths and weaknesses
        for metric in metrics:
            if metric.score >= 80:
                strengths.append(f"{metric.name}: {metric.score:.1f}/100")
            elif metric.score < 60:
                weaknesses.append(f"{metric.name}: {metric.score:.1f}/100")
        
        return AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            video_id="",
            sport="golf",
            lift_type=None,
            overall_score=round(overall_score, 2),
            metrics=metrics,
            feedback=feedback,
            strengths=strengths,
            weaknesses=weaknesses,
            raw_data={
                "frame_count": len(pose_data),
                "shot_type": self.shot_type,
            },
            created_at=datetime.now(),
        )
    
    def _create_empty_result(self) -> AnalysisResult:
        return AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            video_id="",
            sport="golf",
            lift_type=None,
            overall_score=0.0,
            metrics=[],
            feedback=[self.create_feedback("warning", f"{self.shot_type.capitalize()} swing: No pose data detected. Ensure person is visible in video.")],
            strengths=[],
            weaknesses=[],
            raw_data={"frame_count": 0, "shot_type": self.shot_type},
            created_at=datetime.now(),
        )
    
    def _analyze_stance_width(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Analyze stance width - wider for driver, narrower for iron."""
        if not landmarks_list:
            return 50.0
        
        stance_widths = []
        for landmarks in landmarks_list:
            if "left_ankle" in landmarks and "right_ankle" in landmarks:
                ankle_distance = abs(landmarks["left_ankle"][0] - landmarks["right_ankle"][0])
                stance_widths.append(ankle_distance)
        
        if not stance_widths:
            return 50.0
        
        avg_stance_width = np.mean(stance_widths)
        deviation = abs(avg_stance_width - self.stance_width_ideal)
        
        # Score based on how close to ideal
        if deviation <= self.stance_width_tolerance:
            score = 100.0
        else:
            score = max(0, 100 - (deviation / self.stance_width_tolerance) * 30)
        
        score = min(100, max(0, score))
        metrics.append(self.create_metric(
            "stance_width",
            round(score, 2),
            value=round(avg_stance_width, 3),
            unit="normalized"
        ))
        
        if score >= 85:
            feedback.append(self.create_feedback(
                "info",
                f"{self.shot_type.capitalize()} swing: Excellent stance width for {self.shot_type} shot.",
                "stance_width"
            ))
        elif score < 60:
            if self.shot_type == "driver":
                feedback.append(self.create_feedback(
                    "warning",
                    "Driver swing: Stance too narrow. Widen stance for better stability and power.",
                    "stance_width"
                ))
            else:
                feedback.append(self.create_feedback(
                    "warning",
                    "Iron swing: Stance too wide. Narrow stance slightly for better control and precision.",
                    "stance_width"
                ))
        
        return score
    
    def _analyze_spine_tilt(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Analyze spine tilt - more tilt for driver, neutral for iron."""
        if not landmarks_list:
            return 50.0
        
        spine_tilts = []
        for landmarks in landmarks_list:
            if all(k in landmarks for k in ["left_shoulder", "right_shoulder", "left_hip", "right_hip"]):
                shoulder_center_x = (landmarks["left_shoulder"][0] + landmarks["right_shoulder"][0]) / 2
                hip_center_x = (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2
                
                # Calculate tilt (positive = left tilt, negative = right tilt)
                # For right-handed golfer, we want right tilt (negative)
                tilt = hip_center_x - shoulder_center_x
                spine_tilts.append(tilt)
        
        if not spine_tilts:
            return 50.0
        
        avg_tilt = np.mean(spine_tilts)
        deviation = abs(avg_tilt - self.spine_tilt_ideal)
        
        if deviation <= self.spine_tilt_tolerance:
            score = 100.0
        else:
            score = max(0, 100 - (deviation / self.spine_tilt_tolerance) * 30)
        
        score = min(100, max(0, score))
        metrics.append(self.create_metric(
            "spine_tilt",
            round(score, 2),
            value=round(avg_tilt, 3),
            unit="normalized"
        ))
        
        if score >= 85:
            feedback.append(self.create_feedback(
                "info",
                f"{self.shot_type.capitalize()} swing: Optimal spine tilt for {self.shot_type} shot.",
                "spine_tilt"
            ))
        elif score < 60:
            if self.shot_type == "driver":
                feedback.append(self.create_feedback(
                    "warning",
                    "Driver swing: Increase spine tilt away from target to promote upward launch angle.",
                    "spine_tilt"
                ))
            else:
                feedback.append(self.create_feedback(
                    "warning",
                    "Iron swing: Reduce spine tilt. Maintain more neutral spine for better compression.",
                    "spine_tilt"
                ))
        
        return score
    
    def _analyze_backswing_rotation(self, angles_list: List[Dict], landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Analyze shoulder rotation in backswing - larger for driver, controlled for iron."""
        if not angles_list or not landmarks_list:
            return 50.0
        
        rotations = []
        for i, (angles, landmarks) in enumerate(zip(angles_list, landmarks_list)):
            # Look for maximum rotation (typically at top of backswing)
            if "left_shoulder_angle" in angles:
                # Use shoulder angle as proxy for rotation
                angle = angles["left_shoulder_angle"]
                if angle > 90:  # Likely in backswing
                    rotations.append(angle)
            elif "right_shoulder_angle" in angles:
                angle = angles["right_shoulder_angle"]
                if angle > 90:
                    rotations.append(angle)
        
        if not rotations:
            # Fallback: estimate from shoulder-hip relationship
            for landmarks in landmarks_list:
                if all(k in landmarks for k in ["left_shoulder", "right_shoulder", "left_hip", "right_hip"]):
                    shoulder_center = np.array([
                        (landmarks["left_shoulder"][0] + landmarks["right_shoulder"][0]) / 2,
                        (landmarks["left_shoulder"][1] + landmarks["right_shoulder"][1]) / 2
                    ])
                    hip_center = np.array([
                        (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2,
                        (landmarks["left_hip"][1] + landmarks["right_hip"][1]) / 2
                    ])
                    
                    # Calculate rotation angle
                    vector = shoulder_center - hip_center
                    angle = np.degrees(np.arctan2(vector[1], abs(vector[0])))
                    if angle > 45:  # Likely in backswing
                        rotations.append(angle + 45)  # Normalize
        
        if not rotations:
            return 50.0
        
        max_rotation = max(rotations)
        deviation = abs(max_rotation - self.backswing_rotation_ideal)
        
        if deviation <= self.backswing_rotation_tolerance:
            score = 100.0
        else:
            score = max(0, 100 - (deviation / self.backswing_rotation_tolerance) * 30)
        
        score = min(100, max(0, score))
        metrics.append(self.create_metric(
            "backswing_rotation",
            round(score, 2),
            value=round(max_rotation, 1),
            unit="degrees"
        ))
        
        if score >= 85:
            feedback.append(self.create_feedback(
                "info",
                f"{self.shot_type.capitalize()} swing: Excellent rotation for {self.shot_type} shot.",
                "backswing_rotation"
            ))
        elif score < 60:
            if self.shot_type == "driver":
                feedback.append(self.create_feedback(
                    "warning",
                    "Driver swing: Increase shoulder rotation in backswing for more power generation.",
                    "backswing_rotation"
                ))
            else:
                feedback.append(self.create_feedback(
                    "warning",
                    "Iron swing: Control rotation. Avoid over-rotating for better consistency.",
                    "backswing_rotation"
                ))
        
        return score
    
    def _analyze_weight_transfer(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Analyze weight transfer to front foot - more for driver, balanced for iron."""
        if not landmarks_list or len(landmarks_list) < 5:
            return 50.0
        
        # Find impact/follow-through phase (typically later frames)
        impact_frames = landmarks_list[len(landmarks_list) // 2:]
        
        weight_transfers = []
        for landmarks in impact_frames:
            if all(k in landmarks for k in ["left_ankle", "right_ankle", "left_hip", "right_hip"]):
                # Estimate weight distribution by hip position relative to ankles
                left_ankle_x = landmarks["left_ankle"][0]
                right_ankle_x = landmarks["right_ankle"][0]
                hip_center_x = (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2
                
                # For right-handed golfer, weight should shift to left (lower x value)
                ankle_center = (left_ankle_x + right_ankle_x) / 2
                if left_ankle_x < right_ankle_x:  # Left is front foot
                    # Weight transfer = how much hip moves toward front foot
                    transfer = max(0, min(1, (ankle_center - hip_center_x) / (ankle_center - left_ankle_x + 0.01)))
                else:
                    transfer = max(0, min(1, (hip_center_x - ankle_center) / (right_ankle_x - ankle_center + 0.01)))
                
                weight_transfers.append(transfer)
        
        if not weight_transfers:
            return 50.0
        
        avg_transfer = np.mean(weight_transfers)
        deviation = abs(avg_transfer - self.weight_transfer_ideal)
        
        if deviation <= self.weight_transfer_tolerance:
            score = 100.0
        else:
            score = max(0, 100 - (deviation / self.weight_transfer_tolerance) * 30)
        
        score = min(100, max(0, score))
        metrics.append(self.create_metric(
            "weight_transfer",
            round(score, 2),
            value=round(avg_transfer, 3),
            unit="ratio"
        ))
        
        if score >= 85:
            feedback.append(self.create_feedback(
                "info",
                f"{self.shot_type.capitalize()} swing: Excellent weight transfer for {self.shot_type} shot.",
                "weight_transfer"
            ))
        elif score < 60:
            if self.shot_type == "driver":
                feedback.append(self.create_feedback(
                    "warning",
                    "Driver swing: Increase weight transfer to front foot for more power and upward launch.",
                    "weight_transfer"
                ))
            else:
                feedback.append(self.create_feedback(
                    "warning",
                    "Iron swing: Maintain balanced weight transfer. Focus on compression over power.",
                    "weight_transfer"
                ))
        
        return score
    
    def _analyze_balance(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Analyze balance throughout swing - critical for both shot types."""
        if not landmarks_list:
            return 50.0
        
        balance_scores = []
        for landmarks in landmarks_list:
            if all(k in landmarks for k in ["left_ankle", "right_ankle", "left_hip", "right_hip", "left_shoulder", "right_shoulder"]):
                # Calculate center of mass stability
                ankle_center_x = (landmarks["left_ankle"][0] + landmarks["right_ankle"][0]) / 2
                hip_center_x = (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2
                shoulder_center_x = (landmarks["left_shoulder"][0] + landmarks["right_shoulder"][0]) / 2
                
                # Stability = how aligned the body segments are
                vertical_alignment = abs(hip_center_x - ankle_center_x) + abs(shoulder_center_x - hip_center_x)
                balance = max(0, 100 - (vertical_alignment * 400))
                balance_scores.append(balance)
        
        if not balance_scores:
            return 50.0
        
        score = np.mean(balance_scores)
        score = min(100, max(0, score))
        metrics.append(self.create_metric(
            "balance",
            round(score, 2),
            value=round(score, 1),
            unit="score"
        ))
        
        if score >= 85:
            feedback.append(self.create_feedback(
                "info",
                f"{self.shot_type.capitalize()} swing: Excellent balance maintained throughout swing.",
                "balance"
            ))
        elif score < 60:
            if self.balance_emphasis == "power":
                feedback.append(self.create_feedback(
                    "critical",
                    "Driver swing: Balance compromised. Maintain stability for consistent power generation.",
                    "balance"
                ))
            else:
                feedback.append(self.create_feedback(
                    "critical",
                    "Iron swing: Balance is critical for compression. Focus on maintaining stable base.",
                    "balance"
                ))
        
        return score
    
    def _analyze_tempo(self, pose_data: List[Dict], metrics: List, feedback: List) -> float:
        """Analyze swing tempo - smooth and controlled for both shot types."""
        if len(pose_data) < 5:
            return 50.0
        
        # Calculate motion velocity throughout swing
        velocities = []
        for i in range(1, len(pose_data)):
            prev_landmarks = pose_data[i-1].get("landmarks", {})
            curr_landmarks = pose_data[i].get("landmarks", {})
            
            if "right_wrist" in prev_landmarks and "right_wrist" in curr_landmarks:
                velocity = np.sqrt(
                    (curr_landmarks["right_wrist"][0] - prev_landmarks["right_wrist"][0])**2 +
                    (curr_landmarks["right_wrist"][1] - prev_landmarks["right_wrist"][1])**2
                )
                velocities.append(velocity)
        
        if not velocities:
            return 50.0
        
        # Tempo = consistency of velocity (low variance = smooth tempo)
        velocity_variance = np.var(velocities)
        avg_velocity = np.mean(velocities)
        
        # Ideal: smooth acceleration, not jerky
        tempo_consistency = max(0, 100 - (velocity_variance * 1000))
        
        # Check if overall tempo is reasonable (not too fast, not too slow)
        if self.tempo_ideal - self.tempo_tolerance <= avg_velocity <= self.tempo_ideal + self.tempo_tolerance:
            tempo_speed_score = 100.0
        else:
            deviation = min(
                abs(avg_velocity - (self.tempo_ideal - self.tempo_tolerance)),
                abs(avg_velocity - (self.tempo_ideal + self.tempo_tolerance))
            )
            tempo_speed_score = max(0, 100 - (deviation / self.tempo_tolerance) * 30)
        
        score = (tempo_consistency * 0.6 + tempo_speed_score * 0.4)
        score = min(100, max(0, score))
        
        metrics.append(self.create_metric(
            "tempo",
            round(score, 2),
            value=round(avg_velocity, 3),
            unit="normalized"
        ))
        
        if score >= 85:
            feedback.append(self.create_feedback(
                "info",
                f"{self.shot_type.capitalize()} swing: Excellent tempo — smooth and controlled.",
                "tempo"
            ))
        elif score < 60:
            feedback.append(self.create_feedback(
                "warning",
                f"{self.shot_type.capitalize()} swing: Tempo inconsistent. Smooth out the swing motion.",
                "tempo"
            ))
        
        return score
    
    def _analyze_follow_through(self, landmarks_list: List[Dict], angles_list: List[Dict], metrics: List, feedback: List) -> float:
        """Analyze follow-through height - higher for driver, controlled for iron."""
        if not landmarks_list or len(landmarks_list) < 3:
            return 50.0
        
        # Analyze follow-through phase (last third of frames)
        follow_through_frames = landmarks_list[2 * len(landmarks_list) // 3:]
        
        follow_through_heights = []
        for landmarks in follow_through_frames:
            if "right_wrist" in landmarks and "right_hip" in landmarks:
                # Height = how high wrist is relative to hip
                wrist_height = landmarks["right_wrist"][1]
                hip_height = landmarks["right_hip"][1]
                
                # Normalized height (0 = at hip, 1 = fully extended above head)
                height_ratio = max(0, min(1, (hip_height - wrist_height) / 0.5))
                follow_through_heights.append(height_ratio)
        
        if not follow_through_heights:
            return 50.0
        
        avg_height = np.mean(follow_through_heights)
        deviation = abs(avg_height - self.follow_through_height_ideal)
        
        if deviation <= self.follow_through_tolerance:
            score = 100.0
        else:
            score = max(0, 100 - (deviation / self.follow_through_tolerance) * 30)
        
        score = min(100, max(0, score))
        metrics.append(self.create_metric(
            "follow_through",
            round(score, 2),
            value=round(avg_height, 3),
            unit="normalized"
        ))
        
        if score >= 85:
            feedback.append(self.create_feedback(
                "info",
                f"{self.shot_type.capitalize()} swing: Excellent follow-through for {self.shot_type} shot.",
                "follow_through"
            ))
        elif score < 60:
            if self.shot_type == "driver":
                feedback.append(self.create_feedback(
                    "warning",
                    "Driver swing: Increase follow-through height. Finish high for maximum power transfer.",
                    "follow_through"
                ))
            else:
                feedback.append(self.create_feedback(
                    "warning",
                    "Iron swing: Control follow-through. Maintain balanced finish for consistency.",
                    "follow_through"
                ))
        
        return score
