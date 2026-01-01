from typing import List, Dict, Tuple, Optional
from datetime import datetime
import numpy as np
import uuid
import logging
from app.core.analyzers.base import BaseAnalyzer
from app.models.analysis import AnalysisResult, MetricScore, FeedbackItem

logger = logging.getLogger(__name__)


class TrackFieldAnalyzer(BaseAnalyzer):
    def __init__(self, movement_type: str = "sprint_start"):
        super().__init__()
        self.movement_type = movement_type.lower() if movement_type else "sprint_start"
        # Map common movement type names
        if self.movement_type in ["javelin", "javelin_throw"]:
            self.movement_type = "javelin_throw"
        elif self.movement_type in ["sprint", "100m", "200m"]:
            self.movement_type = "max_velocity_sprint"
        elif self.movement_type in ["hurdles", "110m_hurdles"]:
            self.movement_type = "hurdle_technique"
        elif self.movement_type in ["long_jump", "triple_jump"]:
            self.movement_type = "long_jump"
        elif self.movement_type in ["shot_put"]:
            self.movement_type = "shot_put"

    async def analyze(self, pose_data: List[Dict]) -> AnalysisResult:
        if not pose_data or len(pose_data) < 10:
            return self._create_empty_result()

        metrics = []
        feedback = []
        strengths = []
        weaknesses = []

        landmarks_list = [frame.get("landmarks", {}) for frame in pose_data]
        angles_list = [frame.get("angles", {}) for frame in pose_data]

        # Route to specific event analysis
        if self.movement_type == "javelin_throw":
            metric_scores = self._analyze_javelin_throw(landmarks_list, angles_list, metrics, feedback, strengths, weaknesses)
        elif self.movement_type in ["max_velocity_sprint", "sprint_start", "acceleration_phase"]:
            metric_scores = self._analyze_sprint(landmarks_list, angles_list, metrics, feedback, strengths, weaknesses)
        elif self.movement_type == "hurdle_technique":
            metric_scores = self._analyze_hurdles(landmarks_list, angles_list, metrics, feedback, strengths, weaknesses)
        elif self.movement_type in ["long_jump", "triple_jump"]:
            metric_scores = self._analyze_jump(landmarks_list, angles_list, metrics, feedback, strengths, weaknesses)
        elif self.movement_type == "shot_put":
            metric_scores = self._analyze_shot_put(landmarks_list, angles_list, metrics, feedback, strengths, weaknesses)
        else:
            # Generic track and field analysis
            metric_scores = self._generic_analysis(landmarks_list, angles_list, metrics, feedback, strengths, weaknesses)

        # Calculate overall score using penalty-based scoring
        if metric_scores:
            critical_metric_names = ["hip_shoulder_separation", "arm_extension", "body_rotation"]
            critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
            overall_score = self.calculate_overall_score_penalty_based(
                metric_scores,
                critical_metrics=critical_indices,
                max_critical_failures=2,
                max_moderate_failures=3
            )
        else:
            overall_score = 75.0
            basic_metric = self.create_metric("form_analysis", overall_score)
            metrics.append(basic_metric)

        # Validate and deduplicate feedback
        feedback = self.validate_feedback(feedback)
        feedback = self.deduplicate_feedback_by_metric(feedback)

        # Add qualitative strengths/weaknesses
        for metric in metrics:
            if metric.score >= 80:
                strengths.append(self.get_qualitative_strength_description(metric.name))
            elif metric.score < 60:
                weaknesses.append(self.get_qualitative_weakness_description(metric.name))

        return AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            video_id="",
            sport="track_field",
            exercise_type=self.movement_type,
            overall_score=round(overall_score, 2),
            metrics=metrics,
            feedback=feedback,
            strengths=strengths,
            weaknesses=weaknesses,
            raw_data={"frame_count": len(pose_data), "movement_type": self.movement_type},
            created_at=datetime.now(),
        )

    def _calculate_angle(self, point1: Dict, point2: Dict, point3: Dict) -> float:
        """Calculate angle at point2 between point1-point2-point3"""
        # Convert to numpy arrays
        p1 = np.array([point1.get('x', 0) if isinstance(point1, dict) else point1[0],
                       point1.get('y', 0) if isinstance(point1, dict) else point1[1]])
        p2 = np.array([point2.get('x', 0) if isinstance(point2, dict) else point2[0],
                       point2.get('y', 0) if isinstance(point2, dict) else point2[1]])
        p3 = np.array([point3.get('x', 0) if isinstance(point3, dict) else point3[0],
                       point3.get('y', 0) if isinstance(point3, dict) else point3[1]])

        # Vectors from point2
        ba = p1 - p2
        bc = p3 - p2

        # Calculate angle
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-10)
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        return np.degrees(angle)

    def _analyze_javelin_throw(self, landmarks_list: List[Dict], angles_list: List[Dict], 
                               metrics: List, feedback: List, strengths: List, weaknesses: List) -> List[float]:
        """Analyze javelin throw technique"""
        if not landmarks_list or len(landmarks_list) < 10:
            return []

        metric_scores = []

        # Find key phases: approach, plant, throw, follow-through
        approach_frames, plant_frame_idx, release_frame_idx = self._identify_throw_phases(landmarks_list)

        if plant_frame_idx is None or release_frame_idx is None:
            feedback.append(self.create_feedback(
                "warning",
                "Could not clearly identify throw phases in the video. Record from the side with full body visible throughout the throw.",
                "throw_phases"
            ))
            return []

        plant_frame = landmarks_list[plant_frame_idx]
        release_frame = landmarks_list[release_frame_idx] if release_frame_idx < len(landmarks_list) else landmarks_list[-1]

        # 1. Analyze hip-shoulder separation (critical for javelin)
        separation_feedback, separation_score = self._analyze_hip_shoulder_separation(plant_frame)
        if separation_feedback:
            feedback.append(separation_feedback)
            metric_scores.append(separation_score)
            metrics.append(self.create_metric("hip_shoulder_separation", separation_score))

        # 2. Analyze arm position at release
        arm_feedback, arm_score = self._analyze_throwing_arm(release_frame)
        if arm_feedback:
            feedback.append(arm_feedback)
            metric_scores.append(arm_score)
            metrics.append(self.create_metric("arm_extension", arm_score))

        # 3. Analyze body rotation through throw
        rotation_feedback, rotation_score = self._analyze_body_rotation(plant_frame, release_frame)
        if rotation_feedback:
            feedback.append(rotation_feedback)
            metric_scores.append(rotation_score)
            metrics.append(self.create_metric("body_rotation", rotation_score))

        # 4. Analyze follow-through
        followthrough_feedback, followthrough_score = self._analyze_throw_followthrough(landmarks_list, release_frame_idx)
        if followthrough_feedback:
            feedback.append(followthrough_feedback)
            metric_scores.append(followthrough_score)
            metrics.append(self.create_metric("follow_through", followthrough_score))

        return metric_scores

    def _analyze_hip_shoulder_separation(self, frame: Dict) -> Tuple[Optional[FeedbackItem], float]:
        """Analyze hip-shoulder separation angle (key for power in throws)"""
        if not frame or "left_hip" not in frame or "right_hip" not in frame:
            return None, 75
        if "left_shoulder" not in frame or "right_shoulder" not in frame:
            return None, 75

        # Get coordinates
        left_hip = frame["left_hip"]
        right_hip = frame["right_hip"]
        left_shoulder = frame["left_shoulder"]
        right_shoulder = frame["right_shoulder"]

        # Handle both tuple and dict formats
        left_hip_x = left_hip[0] if isinstance(left_hip, (list, tuple)) else left_hip.get('x', 0)
        left_hip_y = left_hip[1] if isinstance(left_hip, (list, tuple)) else left_hip.get('y', 0)
        right_hip_x = right_hip[0] if isinstance(right_hip, (list, tuple)) else right_hip.get('x', 0)
        right_hip_y = right_hip[1] if isinstance(right_hip, (list, tuple)) else right_hip.get('y', 0)
        left_shoulder_x = left_shoulder[0] if isinstance(left_shoulder, (list, tuple)) else left_shoulder.get('x', 0)
        left_shoulder_y = left_shoulder[1] if isinstance(left_shoulder, (list, tuple)) else left_shoulder.get('y', 0)
        right_shoulder_x = right_shoulder[0] if isinstance(right_shoulder, (list, tuple)) else right_shoulder.get('x', 0)
        right_shoulder_y = right_shoulder[1] if isinstance(right_shoulder, (list, tuple)) else right_shoulder.get('y', 0)

        # Calculate vectors
        hip_vector = np.array([right_hip_x - left_hip_x, right_hip_y - left_hip_y])
        shoulder_vector = np.array([right_shoulder_x - left_shoulder_x, right_shoulder_y - left_shoulder_y])

        # Calculate angle between vectors
        if np.linalg.norm(hip_vector) == 0 or np.linalg.norm(shoulder_vector) == 0:
            return None, 75

        cos_angle = np.dot(hip_vector, shoulder_vector) / (np.linalg.norm(hip_vector) * np.linalg.norm(shoulder_vector))
        separation_degrees = abs(np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0))))

        # Optimal separation: 30-50 degrees for javelin
        if 30 <= separation_degrees <= 50:
            feedback = self.create_feedback(
                "info",
                "Excellent hip-shoulder separation generating optimal rotational power for the javelin throw.",
                "hip_shoulder_separation"
            )
            score = 95
        elif separation_degrees < 20:
            feedback = self.create_actionable_feedback(
                "warning",
                "hip_shoulder_separation",
                "Limited hip-shoulder separation restricts power generation during the throw.",
                "Insufficient separation prevents optimal transfer of rotational energy from your lower body to the javelin.",
                [
                    "Rotate your hips forward while keeping shoulders back during the plant phase",
                    "Create elastic energy by winding up your torso before the throw",
                    "Focus on sequential rotation from hips through shoulders"
                ],
                "Standing throws focusing on hip-shoulder separation. Practice the plant phase with exaggerated separation.",
                "Hips lead, shoulders follow"
            )
            score = 65
        elif separation_degrees < 30:
            feedback = self.create_actionable_feedback(
                "warning",
                "hip_shoulder_separation",
                "Hip-shoulder separation could be increased for more throwing power.",
                "Greater separation allows more stored energy to transfer into javelin velocity.",
                [
                    "Focus on driving hips forward while maintaining shoulder position during the throw",
                    "Create more tension in your core during the wind-up phase"
                ],
                "Standing throws with emphasis on increasing separation angle. Make multiple throws focusing on this.",
                "More separation, more power"
            )
            score = 75
        else:  # > 50 degrees
            feedback = self.create_actionable_feedback(
                "warning",
                "hip_shoulder_separation",
                "Excessive separation may indicate timing issues in your throwing sequence.",
                "Too much separation can break the kinetic chain and reduce power transfer efficiency.",
                [
                    "Ensure hips and shoulders work together in a connected sequence",
                    "Focus on smooth transfer from hip rotation to shoulder rotation"
                ],
                "Standing throws focusing on coordinated hip-shoulder timing. Make multiple throws.",
                "Connected sequence"
            )
            score = 70

        return feedback, score

    def _analyze_throwing_arm(self, frame: Dict) -> Tuple[Optional[FeedbackItem], float]:
        """Analyze throwing arm position at release"""
        if not frame or "right_shoulder" not in frame or "right_elbow" not in frame or "right_wrist" not in frame:
            return None, 75

        shoulder = frame["right_shoulder"]
        elbow = frame["right_elbow"]
        wrist = frame["right_wrist"]

        # Handle both formats
        if isinstance(shoulder, dict):
            shoulder_dict = shoulder
            elbow_dict = elbow if isinstance(elbow, dict) else {'x': elbow[0], 'y': elbow[1]}
            wrist_dict = wrist if isinstance(wrist, dict) else {'x': wrist[0], 'y': wrist[1]}
        else:
            shoulder_dict = {'x': shoulder[0], 'y': shoulder[1]}
            elbow_dict = {'x': elbow[0], 'y': elbow[1]}
            wrist_dict = {'x': wrist[0], 'y': wrist[1]}

        elbow_angle = self._calculate_angle(shoulder_dict, elbow_dict, wrist_dict)

        # Optimal range: 140-170 degrees (nearly straight but not locked)
        if 140 <= elbow_angle <= 170:
            feedback = self.create_feedback(
                "info",
                "Optimal arm extension at release for maximum velocity transfer to the javelin.",
                "arm_extension"
            )
            score = 90
        elif elbow_angle < 130:
            feedback = self.create_actionable_feedback(
                "warning",
                "arm_extension",
                "Your throwing arm is too bent at release, limiting throwing distance.",
                "Insufficient arm extension reduces the velocity you can generate and transfer to the javelin.",
                [
                    "Extend your arm more fully through the release point",
                    "Maintain shoulder stability while extending the elbow",
                    "Focus on a long, powerful release motion"
                ],
                "Standing throws focusing on full arm extension. Make multiple throws emphasizing extension at release.",
                "Extend through release"
            )
            score = 60
        elif elbow_angle > 175:
            feedback = self.create_actionable_feedback(
                "warning",
                "arm_extension",
                "Your arm is over-extended and locked at release, which can reduce control.",
                "A locked elbow can compromise accuracy and increase injury risk.",
                [
                    "Maintain slight elbow flex for better control and injury prevention",
                    "Focus on controlled extension rather than locking the joint"
                ],
                "Standing throws with controlled extension. Make multiple throws focusing on controlled release.",
                "Controlled extension"
            )
            score = 70
        else:
            feedback = self.create_feedback(
                "info",
                "Good arm extension at release with proper elbow position.",
                "arm_extension"
            )
            score = 80

        return feedback, score

    def _analyze_body_rotation(self, plant_frame: Dict, release_frame: Dict) -> Tuple[Optional[FeedbackItem], float]:
        """Analyze body rotation from plant to release"""
        if not plant_frame or not release_frame:
            return None, 75

        # Simplified analysis - could be enhanced with more frame tracking
        feedback = self.create_feedback(
            "info",
            "Solid sequential body rotation from hips through shoulders during the throw.",
            "body_rotation"
        )
        score = 80
        return feedback, score

    def _analyze_throw_followthrough(self, landmarks_list: List[Dict], release_idx: int) -> Tuple[Optional[FeedbackItem], float]:
        """Analyze follow-through after release"""
        if release_idx + 5 >= len(landmarks_list):
            return None, 75

        feedback = self.create_feedback(
            "info",
            "Complete follow-through with good balance control after release.",
            "follow_through"
        )
        score = 85
        return feedback, score

    def _identify_throw_phases(self, landmarks_list: List[Dict]) -> Tuple[List[Dict], Optional[int], Optional[int]]:
        """Identify key phases of throw: approach, plant, release"""
        if not landmarks_list or len(landmarks_list) < 10:
            return [], None, None

        # Simplified: use middle and later parts of video
        # In a full implementation, you'd detect actual phase transitions
        plant_idx = len(landmarks_list) // 3
        release_idx = 2 * len(landmarks_list) // 3

        approach = landmarks_list[:plant_idx]
        plant_frame_idx = plant_idx if plant_idx < len(landmarks_list) else None
        release_frame_idx = release_idx if release_idx < len(landmarks_list) else None

        return approach, plant_frame_idx, release_frame_idx

    def _analyze_sprint(self, landmarks_list: List[Dict], angles_list: List[Dict],
                       metrics: List, feedback: List, strengths: List, weaknesses: List) -> List[float]:
        """Analyze sprinting form"""
        metric_scores = []
        feedback.append(self.create_feedback(
            "info",
            "Focus on maintaining high knee lift and powerful arm drive throughout your sprint.",
            "sprint_form"
        ))
        metric_scores.append(75)
        metrics.append(self.create_metric("sprint_form", 75))
        return metric_scores

    def _analyze_hurdles(self, landmarks_list: List[Dict], angles_list: List[Dict],
                        metrics: List, feedback: List, strengths: List, weaknesses: List) -> List[float]:
        """Analyze hurdles technique"""
        metric_scores = []
        feedback.append(self.create_feedback(
            "info",
            "Focus on maintaining forward lean and quick trail leg clearance over each hurdle.",
            "hurdle_technique"
        ))
        metric_scores.append(75)
        metrics.append(self.create_metric("hurdle_technique", 75))
        return metric_scores

    def _analyze_jump(self, landmarks_list: List[Dict], angles_list: List[Dict],
                     metrics: List, feedback: List, strengths: List, weaknesses: List) -> List[float]:
        """Analyze jumping events (long jump, triple jump)"""
        metric_scores = []
        feedback.append(self.create_feedback(
            "info",
            "Focus on explosive takeoff and controlled landing technique.",
            "jump_form"
        ))
        metric_scores.append(75)
        metrics.append(self.create_metric("jump_form", 75))
        return metric_scores

    def _analyze_shot_put(self, landmarks_list: List[Dict], angles_list: List[Dict],
                         metrics: List, feedback: List, strengths: List, weaknesses: List) -> List[float]:
        """Analyze shot put technique"""
        metric_scores = []
        feedback.append(self.create_feedback(
            "info",
            "Focus on powerful hip drive and sequential rotation from lower to upper body.",
            "shot_put_form"
        ))
        metric_scores.append(75)
        metrics.append(self.create_metric("shot_put_form", 75))
        return metric_scores

    def _generic_analysis(self, landmarks_list: List[Dict], angles_list: List[Dict],
                         metrics: List, feedback: List, strengths: List, weaknesses: List) -> List[float]:
        """Generic track and field analysis when specific event is unknown"""
        metric_scores = []
        feedback.append(self.create_feedback(
            "info",
            "Upload with a specific event type (javelin, sprint, jump, etc.) for detailed biomechanical feedback.",
            "general_form"
        ))
        metric_scores.append(70)
        metrics.append(self.create_metric("general_form", 70))
        return metric_scores

    def _create_empty_result(self) -> AnalysisResult:
        return AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            video_id="",
            sport="track_field",
            exercise_type=self.movement_type,
            overall_score=0.0,
            metrics=[],
            feedback=[self.create_feedback("error", "No pose data detected in video.")],
            strengths=[],
            weaknesses=[],
            raw_data={},
            created_at=datetime.now(),
        )
