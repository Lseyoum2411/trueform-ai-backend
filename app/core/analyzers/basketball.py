from typing import List, Dict, Any
from datetime import datetime
import numpy as np
from app.core.analyzers.base import BaseAnalyzer
from app.models.analysis import AnalysisResult, MetricScore, FeedbackItem
import uuid


class BasketballAnalyzer(BaseAnalyzer):
    def __init__(self, exercise_type: str = None):
        super().__init__()
        self.exercise_type = exercise_type.lower() if exercise_type else None
    
    async def analyze(self, pose_data: List[Dict]) -> AnalysisResult:
        if not pose_data:
            return self._create_empty_result()
        
        metrics = []
        feedback = []
        strengths = []
        weaknesses = []
        
        landmarks_list = [frame.get("landmarks", {}) for frame in pose_data]
        angles_list = [frame.get("angles", {}) for frame in pose_data]
        
        # Exercise-specific analysis with different priorities
        if self.exercise_type == "catch_and_shoot":
            # Catch & Shoot: Focus on Release Speed (High Priority)
            base_stability_score = self._analyze_base_stability(landmarks_list, metrics, feedback, strengths)
            vertical_alignment_score = self._analyze_vertical_alignment(landmarks_list, metrics, feedback)
            release_speed_score = self._analyze_release_speed_catch_and_shoot(pose_data, metrics, feedback, strengths)
            shot_rhythm_score = self._analyze_shot_rhythm(pose_data, metrics, feedback, strengths)
            one_motion_flow_score = self._analyze_one_motion_flow(angles_list, metrics, feedback)
            knee_bend_score = self._analyze_knee_bend(angles_list, metrics, feedback)
            hip_alignment_score = self._analyze_hip_alignment(landmarks_list, metrics, feedback)
            elbow_alignment_score = self._analyze_elbow_alignment(landmarks_list, angles_list, metrics, feedback, strengths)
            shooting_pocket_score = self._analyze_shooting_pocket(landmarks_list, metrics, feedback)
            release_point_score = self._analyze_release_point(landmarks_list, metrics, feedback)
            shot_arc_score = self._analyze_shot_arc(landmarks_list, metrics, feedback)
            follow_through_score = self._analyze_follow_through(angles_list, metrics, feedback)
            wrist_snap_score = self._analyze_wrist_snap(angles_list, metrics, feedback)
        elif self.exercise_type == "shot_off_dribble":
            # Shot Off Dribble: Focus on Balance & Footwork (High Priority)
            base_stability_score = self._analyze_base_stability_shot_off_dribble(landmarks_list, metrics, feedback, strengths)
            vertical_alignment_score = self._analyze_vertical_alignment_shot_off_dribble(landmarks_list, metrics, feedback)
            shot_rhythm_score = self._analyze_shot_rhythm(pose_data, metrics, feedback, strengths)
            one_motion_flow_score = self._analyze_one_motion_flow(angles_list, metrics, feedback)
            release_speed_score = self._analyze_release_speed(pose_data, metrics, feedback, strengths)
            knee_bend_score = self._analyze_knee_bend(angles_list, metrics, feedback)
            hip_alignment_score = self._analyze_hip_alignment(landmarks_list, metrics, feedback)
            elbow_alignment_score = self._analyze_elbow_alignment(landmarks_list, angles_list, metrics, feedback, strengths)
            shooting_pocket_score = self._analyze_shooting_pocket(landmarks_list, metrics, feedback)
            release_point_score = self._analyze_release_point(landmarks_list, metrics, feedback)
            shot_arc_score = self._analyze_shot_arc(landmarks_list, metrics, feedback)
            follow_through_score = self._analyze_follow_through(angles_list, metrics, feedback)
            wrist_snap_score = self._analyze_wrist_snap(angles_list, metrics, feedback)
        elif self.exercise_type == "free_throw":
            # Free Throw: Focus on Follow-Through Consistency (High Priority)
            base_stability_score = self._analyze_base_stability(landmarks_list, metrics, feedback, strengths)
            vertical_alignment_score = self._analyze_vertical_alignment(landmarks_list, metrics, feedback)
            shot_rhythm_score = self._analyze_shot_rhythm(pose_data, metrics, feedback, strengths)
            one_motion_flow_score = self._analyze_one_motion_flow(angles_list, metrics, feedback)
            release_speed_score = self._analyze_release_speed(pose_data, metrics, feedback, strengths)
            knee_bend_score = self._analyze_knee_bend(angles_list, metrics, feedback)
            hip_alignment_score = self._analyze_hip_alignment(landmarks_list, metrics, feedback)
            elbow_alignment_score = self._analyze_elbow_alignment(landmarks_list, angles_list, metrics, feedback, strengths)
            shooting_pocket_score = self._analyze_shooting_pocket(landmarks_list, metrics, feedback)
            release_point_score = self._analyze_release_point(landmarks_list, metrics, feedback)
            shot_arc_score = self._analyze_shot_arc(landmarks_list, metrics, feedback)
            follow_through_score = self._analyze_follow_through_free_throw(angles_list, metrics, feedback)
            wrist_snap_score = self._analyze_wrist_snap(angles_list, metrics, feedback)
        else:
            # Default: General basketball analysis
            base_stability_score = self._analyze_base_stability(landmarks_list, metrics, feedback, strengths)
            vertical_alignment_score = self._analyze_vertical_alignment(landmarks_list, metrics, feedback)
            shot_rhythm_score = self._analyze_shot_rhythm(pose_data, metrics, feedback, strengths)
            one_motion_flow_score = self._analyze_one_motion_flow(angles_list, metrics, feedback)
            release_speed_score = self._analyze_release_speed(pose_data, metrics, feedback, strengths)
            knee_bend_score = self._analyze_knee_bend(angles_list, metrics, feedback)
            hip_alignment_score = self._analyze_hip_alignment(landmarks_list, metrics, feedback)
            elbow_alignment_score = self._analyze_elbow_alignment(landmarks_list, angles_list, metrics, feedback, strengths)
            shooting_pocket_score = self._analyze_shooting_pocket(landmarks_list, metrics, feedback)
            release_point_score = self._analyze_release_point(landmarks_list, metrics, feedback)
            shot_arc_score = self._analyze_shot_arc(landmarks_list, metrics, feedback)
            follow_through_score = self._analyze_follow_through(angles_list, metrics, feedback)
            wrist_snap_score = self._analyze_wrist_snap(angles_list, metrics, feedback)
        
        # Use penalty-based professional benchmark scoring
        # Critical metrics: base_stability, vertical_alignment, shot_rhythm, release_speed, elbow_alignment
        metric_scores = [m.score for m in metrics]
        critical_metric_names = ["base_stability", "vertical_alignment", "shot_rhythm", "release_speed", "elbow_alignment"]
        critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
        overall_score = self.calculate_overall_score_penalty_based(
            metric_scores,
            critical_metrics=critical_indices,
            max_critical_failures=2,
            max_moderate_failures=3
        )
        
        # Add qualitative strengths/weaknesses (NO numeric values)
        for metric in metrics:
            if metric.score >= 80:
                strengths.append(self.get_qualitative_strength_description(metric.name))
            elif metric.score < 60:
                weaknesses.append(self.get_qualitative_weakness_description(metric.name))
        
        # Validate and deduplicate feedback
        feedback = self.validate_feedback(feedback)
        feedback = self.deduplicate_feedback_by_metric(feedback)
        
        return AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            video_id="",
            sport="basketball",
            lift_type=None,
            overall_score=round(overall_score, 2),
            metrics=metrics,
            feedback=feedback,
            strengths=strengths,
            weaknesses=weaknesses,
            raw_data={"frame_count": len(pose_data)},
            created_at=datetime.now(),
        )
    
    def _analyze_base_stability(self, landmarks_list: List[Dict], metrics: List, feedback: List, strengths: List) -> float:
        if not landmarks_list:
            return 50.0
        
        stability_scores = []
        spacing_ratios = []
        
        for landmarks in landmarks_list:
            # Check if we have all required landmarks with sufficient visibility
            required_landmarks = ["left_ankle", "right_ankle", "left_shoulder", "right_shoulder"]
            if not all(k in landmarks for k in required_landmarks):
                continue
            
            # Check visibility (if available)
            left_ankle_vis = landmarks.get("left_ankle", {}).get("visibility", 1.0) if isinstance(landmarks.get("left_ankle"), dict) else 1.0
            right_ankle_vis = landmarks.get("right_ankle", {}).get("visibility", 1.0) if isinstance(landmarks.get("right_ankle"), dict) else 1.0
            left_shoulder_vis = landmarks.get("left_shoulder", {}).get("visibility", 1.0) if isinstance(landmarks.get("left_shoulder"), dict) else 1.0
            right_shoulder_vis = landmarks.get("right_shoulder", {}).get("visibility", 1.0) if isinstance(landmarks.get("right_shoulder"), dict) else 1.0
            
            # Skip if visibility is too low (not confident in measurements)
            if min(left_ankle_vis, right_ankle_vis, left_shoulder_vis, right_shoulder_vis) < 0.7:
                continue
            
            # Extract coordinates (handle both tuple/list and dict formats)
            left_ankle = landmarks["left_ankle"]
            right_ankle = landmarks["right_ankle"]
            left_shoulder = landmarks["left_shoulder"]
            right_shoulder = landmarks["right_shoulder"]
            
            # Get x coordinates (normalized 0-1)
            left_ankle_x = left_ankle[0] if isinstance(left_ankle, (list, tuple)) else left_ankle.get("x", 0)
            right_ankle_x = right_ankle[0] if isinstance(right_ankle, (list, tuple)) else right_ankle.get("x", 0)
            left_shoulder_x = left_shoulder[0] if isinstance(left_shoulder, (list, tuple)) else left_shoulder.get("x", 0)
            right_shoulder_x = right_shoulder[0] if isinstance(right_shoulder, (list, tuple)) else right_shoulder.get("x", 0)
            
            # Calculate distances
            foot_width = abs(right_ankle_x - left_ankle_x)
            shoulder_width = abs(right_shoulder_x - left_shoulder_x)
            
            # Calculate ratio of foot spacing to shoulder width
            if shoulder_width > 0.01:  # Avoid division by zero
                spacing_ratio = foot_width / shoulder_width
                spacing_ratios.append(spacing_ratio)
                
                # Optimal range: 1.0-1.3x shoulder width for basketball shooting
                if 1.0 <= spacing_ratio <= 1.3:
                    stability = 95
                elif spacing_ratio < 0.8:
                    # Too narrow
                    stability = max(0, 100 - (0.8 - spacing_ratio) * 200)
                elif spacing_ratio < 1.0:
                    # Slightly narrow
                    stability = max(0, 100 - (1.0 - spacing_ratio) * 100)
                elif spacing_ratio <= 1.5:
                    # Slightly wide
                    stability = max(0, 100 - (spacing_ratio - 1.3) * 100)
                else:
                    # Too wide
                    stability = max(0, 100 - (spacing_ratio - 1.5) * 200)
                
                stability_scores.append(stability)
        
        if not stability_scores:
            return 50.0
        
        score = np.mean(stability_scores)
        avg_spacing_ratio = np.mean(spacing_ratios) if spacing_ratios else 0
        metrics.append(self.create_metric("base_stability", score, value=round(avg_spacing_ratio, 2), unit="shoulder-width ratio"))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent base stability — solid foundation with optimal stance width.", "base_stability"))
            strengths.append("Strong base stability")
        elif score < 60:
            # Determine specific issue based on average spacing ratio
            if avg_spacing_ratio < 1.0:
                feedback.append(self.create_actionable_feedback(
                    "warning",
                    "base_stability",
                    "Your stance is too narrow, limiting stability and power generation.",
                    "A narrow base reduces balance and makes it harder to generate consistent power from your legs to your shot.",
                    [
                        "Widen your base to shoulder-width or slightly wider for better balance",
                        "Place your feet directly under your shoulders with toes pointing forward",
                        "Feel your weight evenly distributed on both feet before you shoot"
                    ],
                    "Stance-width form shooting from close range. Check foot position before each shot. Make multiple shots focusing only on base width.",
                    "Wider base"
                ))
            else:  # avg_spacing_ratio > 1.3
                feedback.append(self.create_actionable_feedback(
                    "warning",
                    "base_stability",
                    "Your stance is too wide, restricting upward power transfer.",
                    "An overly wide base limits vertical force generation and can reduce shooting consistency.",
                    [
                        "Bring your feet slightly closer to shoulder-width to optimize vertical force generation",
                        "Aim for feet positioned directly under your shoulders or slightly wider",
                        "Maintain this width throughout your entire shooting motion"
                    ],
                    "Stance-width form shooting from close range. Check foot position before each shot. Make multiple shots focusing only on base width.",
                    "Optimal width"
                ))
        else:
            # Score 60-84: acceptable but could improve
            if avg_spacing_ratio < 1.0:
                feedback.append(self.create_actionable_feedback(
                    "warning",
                    "base_stability",
                    "Your stance could be slightly wider for optimal balance.",
                    "A slightly wider base improves stability and power transfer.",
                    [
                        "Widen your base to match shoulder-width for better balance",
                        "Feel your weight evenly distributed on both feet"
                    ],
                    "Stance-width form shooting from close range. Make multiple shots focusing on base width.",
                    "Wider base"
                ))
            else:
                feedback.append(self.create_actionable_feedback(
                    "warning",
                    "base_stability",
                    "Your stance could be slightly narrower for optimal power transfer.",
                    "A slightly narrower base can improve vertical force generation.",
                    [
                        "Bring your feet slightly closer to shoulder-width",
                        "Maintain optimal width throughout your shooting motion"
                    ],
                    "Stance-width form shooting from close range. Make multiple shots focusing on base width.",
                    "Optimal width"
                ))
        
        return score
    
    def _analyze_vertical_alignment(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        if not landmarks_list:
            return 50.0
        
        alignment_scores = []
        lean_offsets = []  # Track lean direction and magnitude
        
        for landmarks in landmarks_list:
            if not all(k in landmarks for k in ["nose", "left_hip", "right_hip"]):
                continue
            
            # Check visibility if available
            nose_vis = landmarks.get("nose", {}).get("visibility", 1.0) if isinstance(landmarks.get("nose"), dict) else 1.0
            left_hip_vis = landmarks.get("left_hip", {}).get("visibility", 1.0) if isinstance(landmarks.get("left_hip"), dict) else 1.0
            right_hip_vis = landmarks.get("right_hip", {}).get("visibility", 1.0) if isinstance(landmarks.get("right_hip"), dict) else 1.0
            
            # Skip if visibility is too low
            if min(nose_vis, left_hip_vis, right_hip_vis) < 0.7:
                continue
            
            # Extract coordinates
            nose = landmarks["nose"]
            left_hip = landmarks["left_hip"]
            right_hip = landmarks["right_hip"]
            
            # Get coordinates (handle both tuple/list and dict formats)
            nose_x = nose[0] if isinstance(nose, (list, tuple)) else nose.get("x", 0)
            nose_y = nose[1] if isinstance(nose, (list, tuple)) else nose.get("y", 0)
            left_hip_x = left_hip[0] if isinstance(left_hip, (list, tuple)) else left_hip.get("x", 0)
            left_hip_y = left_hip[1] if isinstance(left_hip, (list, tuple)) else left_hip.get("y", 0)
            right_hip_x = right_hip[0] if isinstance(right_hip, (list, tuple)) else right_hip.get("x", 0)
            right_hip_y = right_hip[1] if isinstance(right_hip, (list, tuple)) else right_hip.get("y", 0)
            
            # Calculate hip center
            hip_center_x = (left_hip_x + right_hip_x) / 2
            hip_center_y = (left_hip_y + right_hip_y) / 2
            
            # Calculate lean (horizontal offset from hip to nose)
            lean_offset = nose_x - hip_center_x
            
            # Normalize by body height (approximate - distance from hip to nose)
            body_height = abs(hip_center_y - nose_y)
            if body_height > 0.01:  # Avoid division by zero
                lean_ratio = abs(lean_offset) / body_height
                lean_offsets.append(lean_offset)  # Store signed offset to determine direction
                
                # Calculate alignment score based on lean ratio
                if lean_ratio < 0.05:  # Less than 5% lean is excellent
                    alignment = 95
                elif lean_ratio < 0.10:  # 5-10% is acceptable
                    alignment = 85
                elif lean_ratio < 0.15:  # 10-15% is moderate
                    alignment = 70
                else:  # >15% is problematic
                    alignment = max(0, 100 - (lean_ratio - 0.15) * 400)
                
                alignment_scores.append(alignment)
        
        if not alignment_scores:
            return 50.0
        
        score = np.mean(alignment_scores)
        avg_lean_offset = np.mean(lean_offsets) if lean_offsets else 0
        avg_lean_ratio = abs(avg_lean_offset) / 0.2 if lean_offsets else 0  # Approximate body height
        
        metrics.append(self.create_metric("vertical_alignment", score, value=round(avg_lean_ratio * 100, 1), unit="% lean"))
        
        if score >= 85:
            if avg_lean_ratio < 0.05:
                feedback.append(self.create_feedback("info", "Perfect vertical alignment — body stacked correctly with excellent balance.", "vertical_alignment"))
            else:
                direction = "forward" if avg_lean_offset > 0 else "backward"
                feedback.append(self.create_feedback("info", f"Good balance with slight {direction} lean that doesn't affect shot consistency.", "vertical_alignment"))
        elif score < 60:
            # Determine specific direction and magnitude
            direction = "forward" if avg_lean_offset > 0 else "backward"
            magnitude = "significantly" if avg_lean_ratio > 0.15 else "noticeably"
            
            feedback.append(self.create_actionable_feedback(
                "warning",
                "vertical_alignment",
                f"Your torso leans {magnitude} {direction} during the shot.",
                "Leaning reduces balance and makes it harder to generate consistent power from your legs.",
                [
                    "Focus on maintaining a more upright position to improve consistency and accuracy",
                    "Feel your head stacked directly over your shoulders",
                    "Keep your hips directly under your shoulders with no forward or backward lean",
                    "Drive straight up through your legs instead of leaning to create power"
                ],
                "Vertical alignment form shooting from close range. Use a mirror to check your posture. Hold the start position briefly before each shot. Make multiple shots.",
                "Stay stacked"
            ))
        else:
            # Score 60-84: moderate issue
            direction = "forward" if avg_lean_offset > 0 else "backward"
            feedback.append(self.create_actionable_feedback(
                "warning",
                "vertical_alignment",
                f"Your body has a noticeable {direction} lean that could be improved.",
                "Reducing lean improves balance and power transfer from your legs.",
                [
                    "Feel your head stacked directly over your shoulders",
                    "Keep your hips directly under your shoulders",
                    "Drive straight up through your legs"
                ],
                "Vertical alignment form shooting from close range. Use a mirror to check your posture. Make multiple shots.",
                "Stay stacked"
            ))
        
        return score
    
    def _detect_shot_attempts(self, pose_data: List[Dict]) -> List[Dict]:
        """
        Detect individual shot attempts in the video by finding release points.
        Returns list of shot attempt segments (start_frame, end_frame, release_frame).
        """
        if len(pose_data) < 10:
            return []
        
        shot_attempts = []
        wrist_positions = []
        
        # Track wrist vertical position to find release points (wrist moving upward then downward)
        for i, frame in enumerate(pose_data):
            landmarks = frame.get("landmarks", {})
            if "right_wrist" in landmarks:
                wrist = landmarks["right_wrist"]
                wrist_y = wrist[1] if isinstance(wrist, (list, tuple)) else wrist.get("y", 0)
                wrist_positions.append((i, wrist_y))
        
        if len(wrist_positions) < 10:
            return []
        
        # Find local minima (release points - wrist at highest point)
        for i in range(5, len(wrist_positions) - 5):
            current_y = wrist_positions[i][1]
            # Check if this is a local maximum (wrist at highest point before release)
            is_peak = all(wrist_positions[j][1] <= current_y for j in range(max(0, i-5), i)) and \
                     all(wrist_positions[j][1] <= current_y for j in range(i+1, min(len(wrist_positions), i+5)))
            
            if is_peak:
                # Found a potential release point - estimate shot attempt boundaries
                start_frame = max(0, i - 15)  # ~0.5 seconds before release
                end_frame = min(len(pose_data) - 1, i + 10)  # ~0.3 seconds after release
                shot_attempts.append({
                    "start": start_frame,
                    "end": end_frame,
                    "release": i
                })
        
        # If no clear shots detected, assume single shot for entire video
        if not shot_attempts:
            shot_attempts.append({
                "start": 0,
                "end": len(pose_data) - 1,
                "release": len(pose_data) // 2
            })
        
        return shot_attempts
    
    def _calculate_shot_timing(self, pose_data: List[Dict], shot_attempt: Dict) -> float:
        """Calculate timing from gather to release for a single shot."""
        start_idx = shot_attempt["start"]
        release_idx = shot_attempt["release"]
        
        # Estimate timing based on frame indices (assuming ~30fps)
        frame_count = release_idx - start_idx
        timing = frame_count * 0.033  # seconds
        
        return timing
    
    def _analyze_single_shot_timing(self, pose_data: List[Dict], shot_attempt: Dict, metrics: List, feedback: List, strengths: List) -> float:
        """Analyze timing of a single shot attempt."""
        timing = self._calculate_shot_timing(pose_data, shot_attempt)
        
        # Optimal range: 0.3-0.5 seconds from gather to release
        if 0.3 <= timing <= 0.5:
            score = 90
            feedback.append(self.create_feedback("info", "Your release timing is in the optimal range for quick, effective shooting.", "shot_rhythm"))
            strengths.append("Optimal release timing")
        elif timing > 0.5:
            score = max(0, 100 - (timing - 0.5) * 100)
            feedback.append(self.create_actionable_feedback(
                "warning",
                "shot_rhythm",
                "Your release is slower than optimal.",
                "A slower release gives defenders more time to contest and reduces shooting efficiency.",
                [
                    "Work on a quicker motion from gather to release",
                    "Start your upward motion with the ball already set near your shooting pocket",
                    "Eliminate any pause between knee bend and arm extension",
                    "Keep the ball moving continuously upward from start to release"
                ],
                "One-motion form shooting from close to mid-range. Make multiple shots focusing on speed.",
                "One smooth motion"
            ))
        else:  # timing < 0.3
            score = max(0, 100 - (0.3 - timing) * 100)
            feedback.append(self.create_actionable_feedback(
                "warning",
                "shot_rhythm",
                "Your release may be too rushed.",
                "A rushed release can reduce accuracy and consistency.",
                [
                    "Ensure you have full control before releasing",
                    "Maintain smooth, controlled motion throughout",
                    "Balance speed with control"
                ],
                "Controlled-release form shooting from close range. Focus on smooth motion. Make multiple shots.",
                "Control and speed"
            ))
        
        score = round(score, 2)
        metrics.append(self.create_metric("shot_rhythm", score, value=round(timing, 3), unit="seconds"))
        return score
    
    def _analyze_shot_rhythm(self, pose_data: List[Dict], metrics: List, feedback: List, strengths: List) -> float:
        if len(pose_data) < 10:
            return 50.0
        
        # Detect number of shot attempts in video
        shot_attempts = self._detect_shot_attempts(pose_data)
        
        if len(shot_attempts) < 2:
            # Only one shot detected - analyze single shot timing instead of rhythm consistency
            return self._analyze_single_shot_timing(pose_data, shot_attempts[0] if shot_attempts else {"start": 0, "end": len(pose_data)-1, "release": len(pose_data)//2}, metrics, feedback, strengths)
        
        # Multiple shots detected - analyze rhythm consistency
        rhythm_timings = []
        for attempt in shot_attempts:
            timing = self._calculate_shot_timing(pose_data, attempt)
            rhythm_timings.append(timing)
        
        if not rhythm_timings:
            return 50.0
        
        # Calculate consistency (standard deviation of timings)
        if len(rhythm_timings) > 1:
            std_dev = np.std(rhythm_timings)
            mean_timing = np.mean(rhythm_timings)
        else:
            std_dev = 0
            mean_timing = rhythm_timings[0]
        
        # Score based on consistency (lower std_dev = more consistent = higher score)
        if std_dev < 0.05:
            score = 95
            feedback.append(self.create_feedback("info", "Excellent consistency in timing across multiple shots.", "shot_rhythm"))
            strengths.append("Elite shot rhythm consistency")
        elif std_dev < 0.10:
            score = 85
            feedback.append(self.create_feedback("info", "Good consistency in shot timing across attempts.", "shot_rhythm"))
        elif std_dev < 0.15:
            score = 70
            feedback.append(self.create_actionable_feedback(
                "warning",
                "shot_rhythm",
                "Your shot timing varies moderately between attempts.",
                "Varying rhythm makes it harder to develop muscle memory and repeat your shot under pressure.",
                [
                    "Focus on developing a consistent, repeatable rhythm",
                    "Start your upward motion with the ball already set near your shooting pocket",
                    "Eliminate any pause between knee bend and arm extension",
                    "Keep the ball moving continuously upward from start to release"
                ],
                "One-motion form shooting from close to mid-range. Make multiple shots focusing on consistent timing.",
                "One smooth motion"
            ))
        else:
            score = max(0, 100 - (std_dev - 0.15) * 200)
            feedback.append(self.create_actionable_feedback(
                "warning",
                "shot_rhythm",
                "Your shot timing varies significantly between attempts.",
                "Inconsistent rhythm makes it harder to develop muscle memory and repeat your shot under pressure.",
                [
                    "Focus on developing a consistent, repeatable rhythm",
                    "Practice the same timing on every shot",
                    "Start your upward motion with the ball already set near your shooting pocket",
                    "Eliminate any pause between knee bend and arm extension"
                ],
                "One-motion form shooting from close to mid-range. Make multiple shots focusing on consistent timing.",
                "One smooth motion"
            ))
        
        score = round(score, 2)
        metrics.append(self.create_metric("shot_rhythm", score, value=round(std_dev, 3), unit="std dev (seconds)"))
        return score
    
    def _analyze_one_motion_flow(self, angles_list: List[Dict], metrics: List, feedback: List) -> float:
        if not angles_list:
            return 50.0
        
        elbow_angles = [angles.get("right_elbow", 180) for angles in angles_list if "right_elbow" in angles]
        
        if not elbow_angles:
            return 50.0
        
        min_elbow = min(elbow_angles)
        max_elbow = max(elbow_angles)
        range_elbow = max_elbow - min_elbow
        
        ideal_range = 120
        flow_score = max(0, 100 - abs(range_elbow - ideal_range) * 0.5)
        
        score = round(flow_score, 2)
        metrics.append(self.create_metric("one_motion_flow", score, value=round(range_elbow, 1), unit="degrees"))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Smooth one-motion flow — no hitches.", "one_motion_flow"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "one_motion_flow",
                "Your shooting motion has hitches or pauses that interrupt the flow.",
                "Hitches break timing and reduce power transfer from your legs to the release.",
                [
                    "Feel your legs and arms move up together without any stops",
                    "Do not let the ball pause at your shooting pocket or set point",
                    "Keep everything moving in one continuous motion from start to finish"
                ],
                "Flow-through form shooting from close range. Each shot must be one continuous motion. Make multiple shots focusing on eliminating all hitches.",
                "No stops, keep flowing"
            ))
        
        return score
    
    def _analyze_release_speed(self, pose_data: List[Dict], metrics: List, feedback: List, strengths: List) -> float:
        if len(pose_data) < 5:
            return 50.0
        
        release_frames = pose_data[-5:]
        wrist_velocities = []
        
        for i in range(1, len(release_frames)):
            prev = release_frames[i-1].get("landmarks", {})
            curr = release_frames[i].get("landmarks", {})
            
            if "right_wrist" in prev and "right_wrist" in curr:
                velocity = np.sqrt(
                    (curr["right_wrist"][0] - prev["right_wrist"][0])**2 +
                    (curr["right_wrist"][1] - prev["right_wrist"][1])**2
                ) / 0.033
                wrist_velocities.append(velocity)
        
        if not wrist_velocities:
            return 50.0
        
        avg_velocity = np.mean(wrist_velocities)
        ideal_velocity = 0.4
        speed_score = max(0, 100 - abs(avg_velocity - ideal_velocity) * 200)
        
        score = round(speed_score, 2)
        metrics.append(self.create_metric("release_speed", score, value=round(avg_velocity, 2), unit="m/s"))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", f"Release speed fast ({avg_velocity:.2f}m/s) — elite range.", "release_speed"))
            strengths.append("Fast release speed")
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "release_speed",
                "Your release is slower than optimal for game situations.",
                "A slow release gives defenders time to contest and reduces your shooting percentage under pressure.",
                [
                    "Begin extending your legs before your shooting arm reaches full extension",
                    "Release the ball earlier in your jump instead of waiting until the peak",
                    "Feel your arm and legs work together to create speed"
                ],
                "Quick-release catch-and-shoot from mid-range. Catch and release immediately. Complete several sets with focus on speed.",
                "Up fast"
            ))
        
        return score
    
    def _analyze_release_speed_catch_and_shoot(self, pose_data: List[Dict], metrics: List, feedback: List, strengths: List) -> float:
        """Catch and Shoot specific analysis: Focus on catch-to-release timing and release speed."""
        if len(pose_data) < 10:
            return 50.0
        
        # Analyze catch-to-release timing (look for pause after catch)
        wrist_positions = []
        for frame in pose_data:
            landmarks = frame.get("landmarks", {})
            if "right_wrist" in landmarks:
                wrist_positions.append(landmarks["right_wrist"][1])
        
        if not wrist_positions or len(wrist_positions) < 10:
            return 50.0
        
        # Find when motion begins - wrist should start moving immediately
        velocities = []
        for i in range(1, len(wrist_positions)):
            velocity = abs(wrist_positions[i] - wrist_positions[i-1]) / 0.033
            velocities.append(velocity)
        
        if not velocities:
            return 50.0
        
        # Check if there's a pause (low velocity) after initial motion starts
        max_velocity_idx = np.argmax(velocities)
        early_velocities = velocities[:max_velocity_idx] if max_velocity_idx > 3 else velocities[:len(velocities)//3]
        
        if early_velocities:
            avg_early_velocity = np.mean(early_velocities)
            hesitation_score = min(100, avg_early_velocity * 1000)  # Higher early velocity = less hesitation
        else:
            hesitation_score = 50.0
        
        # Analyze release speed
        release_frames = pose_data[-5:]
        wrist_velocities = []
        
        for i in range(1, len(release_frames)):
            prev = release_frames[i-1].get("landmarks", {})
            curr = release_frames[i].get("landmarks", {})
            
            if "right_wrist" in prev and "right_wrist" in curr:
                velocity = np.sqrt(
                    (curr["right_wrist"][0] - prev["right_wrist"][0])**2 +
                    (curr["right_wrist"][1] - prev["right_wrist"][1])**2
                ) / 0.033
                wrist_velocities.append(velocity)
        
        if not wrist_velocities:
            return 50.0
        
        avg_velocity = np.mean(wrist_velocities)
        ideal_velocity = 0.45  # Slightly higher for catch and shoot
        speed_score = max(0, 100 - abs(avg_velocity - ideal_velocity) * 200)
        
        # Combine hesitation and speed scores (weighted toward speed)
        score = round((hesitation_score * 0.3 + speed_score * 0.7), 2)
        metrics.append(self.create_metric("release_speed", score, value=round(avg_velocity, 2), unit="m/s"))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Fast catch-to-release timing — efficient in game situations.", "release_speed"))
            strengths.append("Quick catch and shoot release")
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "critical",
                "release_speed",
                "Your catch-to-release timing is slow. You're waiting too long before initiating the shot, or releasing at the peak of your jump instead of on the way up.",
                "Slower releases reduce defensive contest time but also decrease shooting percentage under pressure. Quicker shots that combine lower-body and upper-body motion create more efficient shooting.",
                [
                    "Begin extending your legs before your shooting arm reaches full extension",
                    "Release the ball earlier in your jump instead of waiting until the peak",
                    "Eliminate any pause after catching the ball — catch, load, jump, and release should feel like one continuous motion"
                ],
                "Quick-release catch-and-shoot from mid-range. Catch and release immediately without hesitation. 5 sets of 5 shots focusing on eliminating pause after catch.",
                "Up fast"
            ))
        else:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "release_speed",
                "Your release speed can be improved for better game performance.",
                "Faster releases reduce defensive contest time and increase shooting percentage under pressure.",
                [
                    "Lower body should begin extending BEFORE the shooting arm reaches full extension",
                    "Shot should be released on the way up, not at the apex",
                    "Catch, load, jump, and release should feel like one continuous motion"
                ],
                "Quick-release catch-and-shoot drill from mid-range. Focus on timing between leg extension and arm extension. 5 sets of 5 shots.",
                "Up fast"
            ))
        
        return score
    
    def _analyze_base_stability_shot_off_dribble(self, landmarks_list: List[Dict], metrics: List, feedback: List, strengths: List) -> float:
        """Shot Off Dribble specific analysis: Focus on balance and footwork."""
        if not landmarks_list:
            return 50.0
        
        stability_scores = []
        for landmarks in landmarks_list:
            if "left_ankle" in landmarks and "right_ankle" in landmarks:
                ankle_distance = abs(landmarks["left_ankle"][0] - landmarks["right_ankle"][0])
                ideal_width = 0.15
                deviation = abs(ankle_distance - ideal_width)
                stability = max(0, 100 - (deviation * 500))
                stability_scores.append(stability)
        
        score = np.mean(stability_scores) if stability_scores else 50.0
        metrics.append(self.create_metric("base_stability", score, value=round(score, 1)))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent base stability — solid foundation for shot off dribble.", "base_stability"))
            strengths.append("Strong base stability")
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "critical",
                "base_stability",
                "Your feet are not properly set before rising. You're taking shots while leaning, drifting, or without a stable base after the dribble.",
                "An unstable base leads to inconsistent shooting form and reduces accuracy and power. Proper footwork improves accuracy and allows the same mechanics at game speed.",
                [
                    "Plant your feet firmly before rising — use a jump stop or one-two step after the dribble",
                    "Feel your shoulders remain level and stacked over your toes",
                    "Briefly gather your body, then explode upward in rhythm — controlled deceleration before explosion"
                ],
                "One-dribble pull-up drill with jump stop. Focus on balanced landings before shooting. Make multiple shots emphasizing feet set before rise.",
                "Feet first"
            ))
        else:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "base_stability",
                "Your base stability can be improved for better balance during shots off the dribble.",
                "A stable base leads to repeatable shooting form and improves accuracy at game speed.",
                [
                    "Shooter should plant feet firmly before rising (jump stop or one-two step)",
                    "Shoulders should remain level and stacked over toes",
                    "Body should gather briefly, then explode upward in rhythm"
                ],
                "One-dribble pull-up drill with jump stop. Emphasis on balanced landings before shooting. Make 20 shots focusing on footwork.",
                "Feet first"
            ))
        
        return score
    
    def _analyze_vertical_alignment_shot_off_dribble(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Shot Off Dribble specific: Focus on balance and body control."""
        if not landmarks_list:
            return 50.0
        
        alignment_scores = []
        lean_offsets = []  # Track lean direction and magnitude
        
        for landmarks in landmarks_list:
            if not all(k in landmarks for k in ["nose", "left_hip", "right_hip"]):
                continue
            
            # Check visibility if available
            nose_vis = landmarks.get("nose", {}).get("visibility", 1.0) if isinstance(landmarks.get("nose"), dict) else 1.0
            left_hip_vis = landmarks.get("left_hip", {}).get("visibility", 1.0) if isinstance(landmarks.get("left_hip"), dict) else 1.0
            right_hip_vis = landmarks.get("right_hip", {}).get("visibility", 1.0) if isinstance(landmarks.get("right_hip"), dict) else 1.0
            
            # Skip if visibility is too low
            if min(nose_vis, left_hip_vis, right_hip_vis) < 0.7:
                continue
            
            # Extract coordinates
            nose = landmarks["nose"]
            left_hip = landmarks["left_hip"]
            right_hip = landmarks["right_hip"]
            
            # Get coordinates (handle both tuple/list and dict formats)
            nose_x = nose[0] if isinstance(nose, (list, tuple)) else nose.get("x", 0)
            nose_y = nose[1] if isinstance(nose, (list, tuple)) else nose.get("y", 0)
            left_hip_x = left_hip[0] if isinstance(left_hip, (list, tuple)) else left_hip.get("x", 0)
            left_hip_y = left_hip[1] if isinstance(left_hip, (list, tuple)) else left_hip.get("y", 0)
            right_hip_x = right_hip[0] if isinstance(right_hip, (list, tuple)) else right_hip.get("x", 0)
            right_hip_y = right_hip[1] if isinstance(right_hip, (list, tuple)) else right_hip.get("y", 0)
            
            # Calculate hip center
            hip_center_x = (left_hip_x + right_hip_x) / 2
            hip_center_y = (left_hip_y + right_hip_y) / 2
            
            # Calculate lean (horizontal offset from hip to nose)
            lean_offset = nose_x - hip_center_x
            
            # Normalize by body height
            body_height = abs(hip_center_y - nose_y)
            if body_height > 0.01:
                lean_ratio = abs(lean_offset) / body_height
                lean_offsets.append(lean_offset)
                
                # Calculate alignment score
                if lean_ratio < 0.05:
                    alignment = 95
                elif lean_ratio < 0.10:
                    alignment = 85
                elif lean_ratio < 0.15:
                    alignment = 70
                else:
                    alignment = max(0, 100 - (lean_ratio - 0.15) * 400)
                
                alignment_scores.append(alignment)
        
        if not alignment_scores:
            return 50.0
        
        score = np.mean(alignment_scores)
        avg_lean_offset = np.mean(lean_offsets) if lean_offsets else 0
        avg_lean_ratio = abs(avg_lean_offset) / 0.2 if lean_offsets else 0
        
        metrics.append(self.create_metric("vertical_alignment", score, value=round(avg_lean_ratio * 100, 1), unit="% lean"))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Perfect vertical alignment — body stacked correctly for balanced shot.", "vertical_alignment"))
        elif score < 60:
            # Determine specific direction and magnitude
            direction = "forward" if avg_lean_offset > 0 else "backward"
            magnitude = "significantly" if avg_lean_ratio > 0.15 else "noticeably"
            
            feedback.append(self.create_actionable_feedback(
                "warning",
                "vertical_alignment",
                f"Your body leans {magnitude} {direction} during shots off the dribble instead of staying balanced.",
                "Leaning reduces balance and makes it harder to generate consistent power. Body control and balance allow the same mechanics at game speed.",
                [
                    f"Focus on maintaining a more upright position to reduce {direction} lean",
                    "Feel your head stacked directly over your shoulders throughout the shot",
                    "Keep your hips directly under your shoulders with no forward, backward, or side lean",
                    "Drive straight up through your legs instead of leaning to create power"
                ],
                "One-dribble pull-up with focus on body control. Check alignment in mirror before each shot. Make 20 shots emphasizing balance.",
                "Stay stacked"
            ))
        else:
            # Score 60-84: moderate issue
            direction = "forward" if avg_lean_offset > 0 else "backward"
            feedback.append(self.create_actionable_feedback(
                "warning",
                "vertical_alignment",
                f"Your body has a noticeable {direction} lean during shots off the dribble that could be improved.",
                "Reducing lean improves balance and power transfer from your legs.",
                [
                    "Feel your head stacked directly over your shoulders",
                    "Keep your hips directly under your shoulders",
                    "Drive straight up through your legs"
                ],
                "One-dribble pull-up with focus on body control. Check alignment in mirror. Make 20 shots emphasizing balance.",
                "Stay stacked"
            ))
        
        return score
    
    def _analyze_follow_through_free_throw(self, angles_list: List[Dict], metrics: List, feedback: List) -> float:
        """Free Throw specific analysis: Focus on follow-through consistency."""
        if not angles_list:
            return 50.0
        
        # Analyze consistency across multiple frames
        final_frames = angles_list[-5:] if len(angles_list) >= 5 else angles_list
        follow_through_angles = []
        
        for angles in final_frames:
            if "right_elbow" in angles:
                follow_through_angles.append(angles["right_elbow"])
        
        if not follow_through_angles:
            return 50.0
        
        avg_follow_through = np.mean(follow_through_angles)
        ideal_follow_through = 160
        
        # Check consistency (variance) - for free throws, consistency matters more than absolute value
        if len(follow_through_angles) > 1:
            consistency_variance = np.var(follow_through_angles)
            consistency_score = max(0, 100 - (consistency_variance * 100))  # Lower variance = higher consistency
        else:
            consistency_score = 50.0
        
        extension_score = max(0, 100 - abs(avg_follow_through - ideal_follow_through) * 1.5)
        
        # Weight consistency more heavily for free throws
        score = round((extension_score * 0.4 + consistency_score * 0.6), 2)
        metrics.append(self.create_metric("follow_through", score, value=round(avg_follow_through, 1), unit="degrees"))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Consistent follow-through extension — repeatable free throw form.", "follow_through"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "critical",
                "follow_through",
                "Your follow-through is inconsistent. You're pulling back your shooting arm early or not holding the finish consistently.",
                "Inconsistent follow-through creates inconsistent arc and backspin. Variation in finish leads to inconsistent results under pressure. Consistent follow-through builds muscle memory.",
                [
                    "Shooting arm should fully extend on every attempt",
                    "Wrist should snap downward with fingers pointing toward the rim",
                    "Follow-through should be held until the ball reaches the basket",
                    "Legs should supply power, not the upper body alone — synchronize leg drive and arm motion"
                ],
                "Repetitive routine-based free throw practice. Focus on identical routine and held finish. Make 30 free throws with emphasis on holding follow-through until ball reaches basket.",
                "Hold the pose"
            ))
        else:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "follow_through",
                "Your follow-through consistency can be improved for better free throw accuracy.",
                "Consistent follow-through creates repeatable arc and backspin, and holding the finish builds muscle memory.",
                [
                    "Shooting arm should fully extend on every attempt",
                    "Wrist should snap downward with fingers pointing toward the rim",
                    "Follow-through should be held until the ball reaches the basket",
                    "Synchronize leg drive and arm motion"
                ],
                "Routine-based free throw practice. Focus on identical routine and held finish. Make multiple free throws emphasizing consistency.",
                "Hold the pose"
            ))
        
        return score
    
    def _analyze_knee_bend(self, angles_list: List[Dict], metrics: List, feedback: List) -> float:
        if not angles_list:
            return 50.0
        
        knee_angles = []
        for angles in angles_list:
            if "right_knee" in angles:
                knee_angles.append(angles["right_knee"])
            elif "left_knee" in angles:
                knee_angles.append(angles["left_knee"])
        
        if not knee_angles:
            return 50.0
        
        avg_knee_angle = np.mean(knee_angles)
        ideal_knee = 120
        knee_score = max(0, 100 - abs(avg_knee_angle - ideal_knee) * 0.8)
        
        score = round(knee_score, 2)
        metrics.append(self.create_metric("knee_bend", score, value=round(avg_knee_angle, 1), unit="degrees"))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Good knee bend — proper loading.", "knee_bend"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "knee_bend",
                "You are not bending your knees enough to generate power from your legs.",
                "Insufficient leg loading forces you to use only arm strength, reducing shot power and range.",
                [
                    "Bend your knees until your thighs are nearly parallel to the ground",
                    "Feel your quads and glutes activate as you lower into your shooting position",
                    "Explode up through your legs as you extend your shooting arm"
                ],
                "Deep-bend form shooting from 10 feet. Focus on feeling your legs load before each shot. Make 20 shots emphasizing leg power.",
                "Deep bend, explode up"
            ))
        
        return score
    
    def _analyze_hip_alignment(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        if not landmarks_list:
            return 50.0
        
        alignment_scores = []
        for landmarks in landmarks_list:
            if "left_hip" in landmarks and "right_hip" in landmarks:
                hip_level = abs(landmarks["left_hip"][1] - landmarks["right_hip"][1])
                alignment = max(0, 100 - (hip_level * 500))
                alignment_scores.append(alignment)
        
        score = np.mean(alignment_scores) if alignment_scores else 50.0
        metrics.append(self.create_metric("hip_alignment", score, value=round(score, 1)))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Hips level and aligned.", "hip_alignment"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "hip_alignment",
                "Your hips are tilted or uneven during your shooting motion.",
                "Hip misalignment throws off your balance and reduces consistent power transfer from your lower body.",
                [
                    "Feel both hip bones at the same height before and during your shot",
                    "Keep your weight centered between both feet without shifting to one side",
                    "Maintain level hips from the start of your motion through release"
                ],
                "Level-hips form shooting from close range. Check hip position in mirror before each shot. Make multiple shots focusing on keeping hips level.",
                "Hips level"
            ))
        
        return score
    
    def _analyze_elbow_alignment(self, landmarks_list: List[Dict], angles_list: List[Dict], metrics: List, feedback: List, strengths: List) -> float:
        if not landmarks_list or not angles_list:
            return 50.0
        
        elbow_flares = []
        for i, landmarks in enumerate(landmarks_list):
            if "right_shoulder" in landmarks and "right_elbow" in landmarks and "right_wrist" in landmarks:
                shoulder_x = landmarks["right_shoulder"][0]
                elbow_x = landmarks["right_elbow"][0]
                wrist_x = landmarks["right_wrist"][0]
                
                elbow_flare = abs(elbow_x - (shoulder_x + wrist_x) / 2)
                elbow_flares.append(elbow_flare)
        
        if not elbow_flares:
            return 50.0
        
        avg_flare = np.mean(elbow_flares)
        flare_degrees = avg_flare * 180
        
        if flare_degrees < 5:
            score = 100
        elif flare_degrees < 10:
            score = 85
        elif flare_degrees < 15:
            score = 70
        else:
            score = max(0, 100 - (flare_degrees - 15) * 3)
        
        score = round(score, 2)
        metrics.append(self.create_metric("elbow_alignment", score, value=round(flare_degrees, 1), unit="degrees"))
        
        if score >= 90:
            feedback.append(self.create_feedback("info", "Perfect elbow alignment — straight like Lethal Shooter teaches.", "elbow_alignment"))
            strengths.append("Perfect elbow alignment")
        elif score < 70:
            feedback.append(self.create_actionable_feedback(
                "critical",
                "elbow_alignment",
                f"Your elbow is flaring out {flare_degrees:.1f} degrees instead of staying straight.",
                "Elbow flare causes the ball to travel off-center and creates inconsistent rotation, reducing accuracy significantly.",
                [
                    "Position your elbow directly under the ball with your forearm pointing straight up",
                    "Feel your elbow stay in line with your shoulder throughout your shot",
                    "Keep your shooting arm in a straight vertical line from shoulder to release point"
                ],
                "Elbow-alignment form shooting from close range. Check elbow position before each shot. Make multiple shots focusing only on keeping elbow straight under ball.",
                "Elbow straight"
            ))
        else:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "elbow_alignment",
                f"Your elbow has a slight flare of {flare_degrees:.1f} degrees.",
                "Even minor elbow deviations can cause the ball to miss left or right and reduce shooting consistency.",
                [
                    "Feel your elbow directly under the ball before you start your upward motion",
                    "Keep your shooting arm in a straight line from your shoulder through your release",
                    "Maintain elbow alignment throughout your entire shooting motion"
                ],
                "Straight-elbow form shooting from close range. Check alignment in mirror. Make multiple shots with extra focus on elbow position.",
                "Keep it straight"
            ))
        
        return score
    
    def _find_pocket_position_frame(self, landmarks_list: List[Dict]) -> Dict:
        """
        Find the frame where ball is in shooting pocket (before upward motion starts).
        This is typically the frame where shooting hand is at its lowest point (highest y value) before release.
        """
        if len(landmarks_list) < 5:
            return None
        
        pocket_frame = None
        max_hand_y = -1  # Track highest y value (lowest hand position)
        
        # Look through early frames (excluding last few which are release/follow-through)
        search_frames = landmarks_list[:max(1, len(landmarks_list) - 3)]
        
        for frame in search_frames:
            landmarks = frame.get("landmarks", {})
            if not all(k in landmarks for k in ["right_wrist", "right_elbow"]):
                continue
            
            # Check visibility
            wrist_vis = landmarks.get("right_wrist", {}).get("visibility", 1.0) if isinstance(landmarks.get("right_wrist"), dict) else 1.0
            if wrist_vis < 0.7:
                continue
            
            # Get wrist position (shooting hand)
            wrist = landmarks["right_wrist"]
            wrist_y = wrist[1] if isinstance(wrist, (list, tuple)) else wrist.get("y", 0)
            
            # Find frame with lowest hand position (highest y value) - this is the pocket position
            if wrist_y > max_hand_y:
                max_hand_y = wrist_y
                pocket_frame = frame
        
        return pocket_frame if pocket_frame else (landmarks_list[len(landmarks_list) // 3] if landmarks_list else None)
    
    def _analyze_shooting_pocket(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """
        Analyze shooting pocket position - must be specific about too high vs too low.
        Optimal pocket: Ball held between waist and chin, at upper chest level (60-80% between hip and chin).
        """
        if not landmarks_list:
            return 50.0
        
        # Find the frame where ball is in shooting pocket
        pocket_frame = self._find_pocket_position_frame(landmarks_list)
        if not pocket_frame:
            return 50.0
        
        landmarks = pocket_frame.get("landmarks", {})
        if not all(k in landmarks for k in ["nose", "right_shoulder", "left_shoulder", "right_hip", "left_hip", "right_wrist"]):
            return 50.0
        
        # Check visibility
        required_keys = ["nose", "right_shoulder", "left_shoulder", "right_hip", "left_hip", "right_wrist"]
        visibilities = []
        for key in required_keys:
            landmark = landmarks[key]
            vis = landmark.get("visibility", 1.0) if isinstance(landmark, dict) else 1.0
            visibilities.append(vis)
        
        if min(visibilities) < 0.7:
            return 50.0
        
        # Extract coordinates
        nose = landmarks["nose"]
        right_shoulder = landmarks["right_shoulder"]
        left_shoulder = landmarks["left_shoulder"]
        right_hip = landmarks["right_hip"]
        left_hip = landmarks["left_hip"]
        right_wrist = landmarks["right_wrist"]
        
        # Get y coordinates (handle both tuple/list and dict formats)
        nose_y = nose[1] if isinstance(nose, (list, tuple)) else nose.get("y", 0)
        shoulder_y = ((right_shoulder[1] if isinstance(right_shoulder, (list, tuple)) else right_shoulder.get("y", 0)) +
                     (left_shoulder[1] if isinstance(left_shoulder, (list, tuple)) else left_shoulder.get("y", 0))) / 2
        hip_y = ((right_hip[1] if isinstance(right_hip, (list, tuple)) else right_hip.get("y", 0)) +
                (left_hip[1] if isinstance(left_hip, (list, tuple)) else left_hip.get("y", 0))) / 2
        wrist_y = right_wrist[1] if isinstance(right_wrist, (list, tuple)) else right_wrist.get("y", 0)
        
        # Approximate chin position (slightly below nose)
        chin_y = nose_y + 0.02
        
        # Calculate pocket height as percentage between hip and chin
        body_height = abs(hip_y - chin_y)
        if body_height <= 0.01:  # Avoid division by zero
            return 50.0
        
        # Calculate pocket position ratio (0.0 = at hip, 1.0 = at chin)
        # Lower y value = higher position on screen
        pocket_position_ratio = (hip_y - wrist_y) / body_height
        
        # Optimal range: 0.6-0.8 (60-80% between hip and chin, favoring upper chest level)
        if 0.6 <= pocket_position_ratio <= 0.8:
            score = 95
            feedback.append(self.create_feedback("info", "Your shooting pocket is positioned optimally at upper chest level for quick, powerful release.", "shooting_pocket"))
        elif pocket_position_ratio < 0.4:
            # TOO LOW - ball below chest, near waist
            score = 60
            feedback.append(self.create_actionable_feedback(
                "warning",
                "shooting_pocket",
                "Your shooting pocket is positioned too low, below optimal chest level.",
                "A low starting position disrupts timing and makes it harder to generate consistent power and rhythm from your legs to your shot.",
                [
                    "Raise your starting position to upper chest level",
                    "Set the ball just outside your dominant shoulder with your elbow at 90 degrees",
                    "Keep the ball above your waist and below your chin",
                    "Feel your forearm stay vertical before you start your upward motion"
                ],
                "Stationary pocket check shooting from close range. Hold pocket position briefly at upper chest level, then shoot. Make multiple shots focusing on correct pocket height.",
                "Upper chest pocket"
            ))
        elif pocket_position_ratio > 0.85:
            # TOO HIGH - ball above chest, near face
            score = 65
            feedback.append(self.create_actionable_feedback(
                "warning",
                "shooting_pocket",
                "Your shooting pocket is positioned too high, above optimal chest level.",
                "A starting position too high disrupts timing and makes it harder to generate power from your legs to your shot.",
                [
                    "Lower your starting position to upper chest level",
                    "The ball should be at shoulder height, not near your face",
                    "Set the ball just outside your dominant shoulder with your elbow at 90 degrees",
                    "Feel your forearm stay vertical before you start your upward motion"
                ],
                "Stationary pocket check shooting from close range. Hold pocket position briefly at upper chest level, then shoot. Make multiple shots focusing on correct pocket height.",
                "Upper chest pocket"
            ))
        elif pocket_position_ratio < 0.6:
            # SLIGHTLY LOW
            score = 75
            feedback.append(self.create_actionable_feedback(
                "warning",
                "shooting_pocket",
                "Your shooting pocket is positioned slightly low.",
                "Raising the starting position slightly will optimize power transfer and timing.",
                [
                    "Raise your starting position slightly to upper chest level",
                    "Aim for the ball at shoulder height, just outside your dominant shoulder",
                    "Keep your elbow at 90 degrees before starting the upward motion"
                ],
                "Stationary pocket check shooting from close range. Make multiple shots focusing on slightly higher starting position.",
                "Slightly higher"
            ))
        else:  # pocket_position_ratio > 0.8 and <= 0.85
            # SLIGHTLY HIGH
            score = 78
            feedback.append(self.create_actionable_feedback(
                "warning",
                "shooting_pocket",
                "Your shooting pocket is positioned slightly high.",
                "Lowering the starting position slightly will improve consistency and power transfer.",
                [
                    "Lower your starting position slightly to upper chest level",
                    "Keep the ball between chest and chin level, not too close to your face",
                    "Maintain elbow at 90 degrees before starting the upward motion"
                ],
                "Stationary pocket check shooting from close range. Make multiple shots focusing on slightly lower starting position.",
                "Slightly lower"
            ))
        
        score = round(score, 2)
        metrics.append(self.create_metric("shooting_pocket", score, value=round(pocket_position_ratio * 100, 1), unit="% from hip to chin"))
        
        return score
    
    def _analyze_release_point(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        if not landmarks_list:
            return 50.0
        
        release_points = []
        for landmarks in landmarks_list:
            if "right_wrist" in landmarks:
                release_y = landmarks["right_wrist"][1]
                release_points.append(release_y)
        
        if not release_points:
            return 50.0
        
        avg_release = np.mean(release_points)
        ideal_release = 0.25
        release_score = max(0, 100 - abs(avg_release - ideal_release) * 300)
        
        score = round(release_score, 2)
        metrics.append(self.create_metric("release_point", score, value=round(avg_release, 3)))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Optimal release point height.", "release_point"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "release_point",
                "You are releasing the ball lower than optimal.",
                "A low release point reduces shot arc and makes it easier for defenders to block your shot.",
                [
                    "Fully straighten your elbow before releasing the ball",
                    "Finish with your fingers pointing toward the rim",
                    "Hold your follow-through high until the ball hits the rim"
                ],
                "High-release form shooting with exaggerated follow-through from close range. Make multiple shots focusing on full arm extension at release.",
                "Reach and hold"
            ))
        
        return score
    
    def _analyze_shot_arc(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        if len(landmarks_list) < 3:
            return 50.0
        
        wrist_trajectory = []
        for landmarks in landmarks_list:
            if "right_wrist" in landmarks:
                wrist_trajectory.append(landmarks["right_wrist"][1])
        
        if len(wrist_trajectory) < 3:
            return 50.0
        
        trajectory_variance = np.var(wrist_trajectory)
        ideal_variance = 0.01
        arc_score = max(0, 100 - abs(trajectory_variance - ideal_variance) * 5000)
        
        score = round(arc_score, 2)
        metrics.append(self.create_metric("shot_arc", score, value=round(trajectory_variance, 4), unit="variance"))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Good shot arc — proper trajectory.", "shot_arc"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "shot_arc",
                "Your shot trajectory is too flat with insufficient arc.",
                "A flat shot reduces the effective rim size and increases the chance of hitting the front of the rim or having shots blocked.",
                [
                    "Feel your shooting hand finish higher above your head after release",
                    "Aim the ball to peak at least 2 feet above the rim",
                    "Use more upward force from your legs to create additional lift"
                ],
                "High-arc form shooting from 12 feet. Visualize the ball going high above the rim. Make 30 shots focusing on creating maximum arc.",
                "High arc"
            ))
        
        return score
    
    def _analyze_follow_through(self, angles_list: List[Dict], metrics: List, feedback: List) -> float:
        if not angles_list:
            return 50.0
        
        final_frames = angles_list[-5:] if len(angles_list) >= 5 else angles_list
        follow_through_angles = []
        
        for angles in final_frames:
            if "right_elbow" in angles:
                follow_through_angles.append(angles["right_elbow"])
        
        if not follow_through_angles:
            return 50.0
        
        avg_follow_through = np.mean(follow_through_angles)
        ideal_follow_through = 160
        follow_score = max(0, 100 - abs(avg_follow_through - ideal_follow_through) * 1.5)
        
        score = round(follow_score, 2)
        metrics.append(self.create_metric("follow_through", score, value=round(avg_follow_through, 1), unit="degrees"))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Good follow-through extension.", "follow_through"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "follow_through",
                "You are not holding your follow-through long enough.",
                "A short follow-through reduces ball rotation and makes it harder to maintain consistent shot accuracy.",
                [
                    "Keep your shooting arm fully extended until the ball reaches the rim",
                    "Hold your wrist snapped forward with fingers pointing down toward the floor",
                    "Do not drop your arm until after the ball hits the rim"
                ],
                "Hold-through form shooting from close range. Hold follow-through for a full moment after each shot. Make multiple shots.",
                "Hold it"
            ))
        
        return score
    
    def _analyze_wrist_snap(self, angles_list: List[Dict], metrics: List, feedback: List) -> float:
        if len(angles_list) < 3:
            return 50.0
        
        wrist_motions = []
        for i in range(1, len(angles_list)):
            prev_elbow = angles_list[i-1].get("right_elbow", 180)
            curr_elbow = angles_list[i].get("right_elbow", 180)
            
            if prev_elbow != 180 and curr_elbow != 180:
                motion = abs(curr_elbow - prev_elbow)
                wrist_motions.append(motion)
        
        if not wrist_motions:
            return 50.0
        
        snap_intensity = np.max(wrist_motions) if wrist_motions else 0
        ideal_snap = 15
        snap_score = max(0, 100 - abs(snap_intensity - ideal_snap) * 3)
        
        score = round(snap_score, 2)
        metrics.append(self.create_metric("wrist_snap", score, value=round(snap_intensity, 1), unit="degrees"))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Good wrist snap — proper release motion.", "wrist_snap"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "wrist_snap",
                "Your wrist snap is either too weak or too aggressive at release.",
                "An improper wrist snap affects ball rotation and backspin, leading to inconsistent shot results and poor ball control.",
                [
                    "Feel your wrist snap forward naturally as the ball leaves your fingers",
                    "Let your fingers point down toward the floor at the end of your follow-through",
                    "Feel consistent backspin on the ball when it leaves your hand"
                ],
                "Wrist-snap form shooting from close range. Focus on feeling the snap at release. Make multiple shots concentrating on wrist action.",
                "Snap it"
            ))
        
        return score
    
    def _create_empty_result(self) -> AnalysisResult:
        return AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            video_id="",
            sport="basketball",
            lift_type=None,
            overall_score=0.0,
            metrics=[],
            feedback=[self.create_feedback("error", "No pose data detected in video.")],
            strengths=[],
            weaknesses=[],
            raw_data={},
            created_at=datetime.now(),
        )





