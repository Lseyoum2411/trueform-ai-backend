from typing import List, Dict
from datetime import datetime
import numpy as np
import uuid
from app.core.analyzers.base import BaseAnalyzer
from app.models.analysis import AnalysisResult, MetricScore, FeedbackItem


class SoccerAnalyzer(BaseAnalyzer):
    def __init__(self, movement_type: str = "shooting_technique"):
        super().__init__()
        self.movement_type = movement_type.lower()
        if self.movement_type not in ["shooting_technique", "passing_technique", "crossing_technique", "dribbling", "first_touch"]:
            self.movement_type = "shooting_technique"

    async def analyze(self, pose_data: List[Dict]) -> AnalysisResult:
        if not pose_data:
            return self._create_empty_result()

        landmarks_list = [frame.get("landmarks", {}) for frame in pose_data]
        angles_list = [frame.get("angles", {}) for frame in pose_data]

        metrics = []
        feedback = []
        strengths = []
        weaknesses = []

        # Exercise-specific analysis with different priorities
        if self.movement_type == "shooting_technique":
            # Shooting: Focus on Lean Forward & Laces (High Priority)
            lean_forward_score = self._analyze_lean_forward_shooting(landmarks_list, metrics, feedback)
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            follow_through_score = self._analyze_follow_through_shooting(landmarks_list, angles_list, metrics, feedback)
            metric_scores = [m.score for m in metrics]
            critical_metric_names = ["lean_forward"]
            critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=critical_indices, max_critical_failures=2, max_moderate_failures=3)
        elif self.movement_type == "passing_technique":
            # Passing: Focus on Lock Ankle & Follow Through (High Priority)
            ankle_stability_score = self._analyze_ankle_stability_passing(angles_list, metrics, feedback)
            follow_through_score = self._analyze_follow_through_passing(landmarks_list, angles_list, metrics, feedback)
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            metric_scores = [m.score for m in metrics]
            critical_metric_names = ["ankle_stability"]
            critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=critical_indices, max_critical_failures=2, max_moderate_failures=3)
        elif self.movement_type == "crossing_technique":
            # Crossing: Focus on Body Angle & Wrap the Foot (High Priority)
            body_angle_score = self._analyze_body_angle_crossing(landmarks_list, metrics, feedback)
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            follow_through_score = self._analyze_follow_through_crossing(landmarks_list, angles_list, metrics, feedback)
            metric_scores = [m.score for m in metrics]
            critical_metric_names = ["body_angle"]
            critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=critical_indices, max_critical_failures=2, max_moderate_failures=3)
        elif self.movement_type == "dribbling":
            # Dribbling: Focus on Close Control (High Priority)
            close_control_score = self._analyze_close_control_dribbling(pose_data, metrics, feedback)
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            metric_scores = [m.score for m in metrics]
            critical_metric_names = ["close_control"]
            critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=critical_indices, max_critical_failures=2, max_moderate_failures=3)
        elif self.movement_type == "first_touch":
            # First Touch: Focus on Soft Cushioning (High Priority)
            soft_touch_score = self._analyze_soft_touch_first_touch(pose_data, metrics, feedback)
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            metric_scores = [m.score for m in metrics]
            critical_metric_names = ["soft_touch"]
            critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=critical_indices, max_critical_failures=2, max_moderate_failures=3)
        else:
            # Default fallback (should not occur due to validation in __init__)
            # If we somehow get here, default to shooting analysis
            lean_forward_score = self._analyze_lean_forward_shooting(landmarks_list, metrics, feedback)
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            metric_scores = [m.score for m in metrics] if metrics else [lean_forward_score, balance_score]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=[], max_critical_failures=2, max_moderate_failures=3) if metrics else np.mean([lean_forward_score, balance_score])

        for metric in metrics:
            if metric.score >= 80:
                strengths.append(self.get_qualitative_strength_description(metric.name))
            elif metric.score < 60:
                weaknesses.append(self.get_qualitative_weakness_description(metric.name))

        # Consolidate duplicate weight transfer feedback (remove duplicate weight transfer items)
        feedback = self.consolidate_weight_transfer_feedback(feedback)
        
        # Remove any remaining duplicate feedback items by metric name
        feedback = self.deduplicate_feedback_by_metric(feedback)

        return AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            video_id="",
            sport="soccer",
            exercise_type=self.movement_type,
            overall_score=round(overall_score, 2),
            metrics=metrics,
            feedback=feedback,
            strengths=strengths,
            weaknesses=weaknesses,
            raw_data={"frame_count": len(pose_data), "movement_type": self.movement_type},
            created_at=datetime.now(),
        )

    def _analyze_lean_forward_shooting(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Shooting specific: Analyze lean forward - chest over ball."""
        if not landmarks_list or len(landmarks_list) < 5:
            return 50.0
        
        # Analyze torso angle during kick - should be forward (chest over ball)
        impact_frames = landmarks_list[len(landmarks_list) // 2:]
        lean_scores = []
        
        for landmarks in impact_frames:
            if all(k in landmarks for k in ["left_shoulder", "right_shoulder", "left_hip", "right_hip"]):
                shoulder_center_y = (landmarks["left_shoulder"][1] + landmarks["right_shoulder"][1]) / 2
                hip_center_y = (landmarks["left_hip"][1] + landmarks["right_hip"][1]) / 2
                
                # For forward lean, shoulders should be ahead of hips (lower Y value)
                # Positive value = forward lean (good for shooting)
                forward_lean = hip_center_y - shoulder_center_y
                
                # Ideal: shoulders slightly ahead of hips (0.02 to 0.05)
                if forward_lean >= 0.02:
                    lean_score = 100.0
                elif forward_lean >= 0.0:
                    lean_score = 70.0 + (forward_lean / 0.02) * 30.0
                else:
                    lean_score = max(0, (forward_lean + 0.05) / 0.05 * 70.0)
                
                lean_scores.append(lean_score)
        
        if not lean_scores:
            return 50.0
        
        score = np.mean(lean_scores)
        metric = self.create_metric("lean_forward", score, value=round(score, 1))
        metrics.append(metric)
        
        if score >= 85:
            # Positive feedback when form is excellent (score >= 85)
            feedback.append(self.create_feedback(
                "info",
                "Excellent forward lean — chest over ball and clean contact. Keep reinforcing this under pressure.",
                "lean_forward"
            ))
        elif score < 60:
            # Critical corrective feedback when fault is clearly detected (score < 60)
            feedback.append(self.create_actionable_feedback(
                "critical",
                "lean_forward",
                "You often lean back and strike the ball with your toe, causing shots to fly high or lose power and accuracy.",
                "Leaning forward keeps shots low and controlled. Striking with the laces (instep) provides a larger surface for power and accuracy. Leaning back sends the ball high, and toe-poking reduces control.",
                [
                    "Plant non-kicking foot even with or slightly ahead of the ball",
                    "Keep chest and shoulders over the ball",
                    "Lock ankle (toes down) and strike with laces",
                    "Follow through toward target and step forward"
                ],
                "Laces shooting drill — 3 sets of 10 shots emphasizing \"chest over, lock ankle.\" Alternate feet if possible.",
                "Chest over ball."
            ))
        else:
            # Warning corrective feedback for minor improvements (60 <= score < 85)
            feedback.append(self.create_actionable_feedback(
                "warning",
                "lean_forward",
                "Forward lean can be improved for better shooting technique.",
                "Leaning forward keeps the shot low and controlled, while striking with your laces gives power and accuracy.",
                [
                    "Plant non-kicking foot even with or slightly ahead of the ball",
                    "Keep chest and shoulders over the ball",
                    "Lock ankle and strike with laces (instep)"
                ],
                "Laces shooting drill emphasizing chest over ball and locked ankle",
                "Chest over ball"
            ))
        
        return score
    
    def _analyze_follow_through_shooting(self, landmarks_list: List[Dict], angles_list: List[Dict], metrics: List, feedback: List) -> float:
        """Shooting specific: Analyze follow-through toward target."""
        if not landmarks_list or len(landmarks_list) < 5:
            return 50.0
        
        # Analyze follow-through phase - leg should continue forward after impact
        follow_through_frames = landmarks_list[len(landmarks_list) * 3 // 4:]
        if not follow_through_frames:
            return 50.0
        
        # Check if kicking leg continues forward motion
        leg_motion_scores = []
        for i in range(1, len(follow_through_frames)):
            prev = follow_through_frames[i-1]
            curr = follow_through_frames[i]
            
            if "left_ankle" in prev and "left_ankle" in curr:
                # Ankle should continue moving forward (positive X direction for right-footed kicker)
                motion = curr["left_ankle"][0] - prev["left_ankle"][0]
                if motion > 0:  # Forward motion (good)
                    leg_motion_scores.append(100.0)
                else:
                    leg_motion_scores.append(max(0, 100 + motion * 500))
        
        if not leg_motion_scores:
            return 50.0
        
        score = np.mean(leg_motion_scores)
        metric = self.create_metric("follow_through", score, value=round(score, 1))
        metrics.append(metric)
        
        if score < 60:
            # Corrective feedback ONLY when fault is clearly detected (score < 60)
            feedback.append(self.create_actionable_feedback(
                "warning",
                "follow_through",
                "Follow-through toward target can be improved.",
                "Following through transfers power to the ball and improves accuracy.",
                [
                    "After contact, continue your kicking leg toward the target",
                    "Take an extra step forward after the kick"
                ],
                "Shooting drill with focus on follow-through",
                "Follow through"
            ))
        # No feedback when form is acceptable (score >= 60) for secondary metrics
        
        return score
    
    def _analyze_ankle_stability_passing(self, angles_list: List[Dict], metrics: List, feedback: List) -> float:
        """Passing specific: Analyze ankle lock - ankle should be firm at impact."""
        if not angles_list:
            return 50.0
        
        # Look at ankle angle consistency during impact phase
        impact_frames = angles_list[len(angles_list) // 2:len(angles_list) * 3 // 4]
        if len(impact_frames) < 2:
            return 50.0
        
        ankle_angles = []
        for angles in impact_frames:
            # Use knee angle as proxy for ankle position (locked ankle = stable knee-ankle relationship)
            if "left_knee" in angles:
                ankle_angles.append(angles["left_knee"])
        
        if len(ankle_angles) < 2:
            return 50.0
        
        # Low variance = stable/locked ankle (good)
        ankle_variance = np.var(ankle_angles)
        if ankle_variance <= 5:
            score = 100.0
        elif ankle_variance <= 10:
            score = 85.0
        elif ankle_variance <= 20:
            score = 70.0
        else:
            score = max(0, 100 - (ankle_variance - 20) * 2)
        
        score = min(100, max(0, score))
        metric = self.create_metric("ankle_stability", score, value=round(ankle_variance, 2))
        metrics.append(metric)
        
        if score >= 85:
            # Positive feedback when form is excellent (score >= 85)
            feedback.append(self.create_feedback(
                "info",
                "Excellent ankle lock — firm foot at impact. Keep reinforcing this solid contact.",
                "ankle_stability"
            ))
        elif score < 60:
            # Critical corrective feedback when fault is clearly detected (score < 60)
            feedback.append(self.create_actionable_feedback(
                "critical",
                "ankle_stability",
                "Passes lack power or accuracy due to a loose ankle and stopped follow-through.",
                "A locked ankle and full follow-through ensure clean energy transfer, accurate direction, and sufficient pace.",
                [
                    "Lock ankle by pulling toes up toward shin",
                    "Use inside of foot for short/medium passes",
                    "Swing through the ball naturally",
                    "Rotate hips toward target and step through pass"
                ],
                "Wall passing drill — 3 rounds of 20 passes (10 per foot), focusing on firm, accurate passes.",
                "Lock and follow."
            ))
        else:
            # Warning corrective feedback for minor improvements (60 <= score < 85)
            feedback.append(self.create_actionable_feedback(
                "warning",
                "ankle_stability",
                "Ankle stability can be improved for more accurate and powerful passes.",
                "A locked ankle creates a firm foot surface for accurate and well-paced passes.",
                [
                    "Lock ankle by pulling toes up toward shin",
                    "Use inside of foot for passing",
                    "Swing through the ball smoothly"
                ],
                "Wall passing drill focusing on firm contact",
                "Lock and follow"
            ))
        
        return score
    
    def _analyze_follow_through_passing(self, landmarks_list: List[Dict], angles_list: List[Dict], metrics: List, feedback: List) -> float:
        """Passing specific: Analyze follow-through toward target."""
        if not landmarks_list or len(landmarks_list) < 5:
            return 50.0
        
        # Analyze follow-through phase - leg should continue toward target
        follow_through_frames = landmarks_list[len(landmarks_list) * 3 // 4:]
        if not follow_through_frames:
            return 50.0
        
        # Check for smooth continuation of motion
        motion_scores = []
        for i in range(1, len(follow_through_frames)):
            prev = follow_through_frames[i-1]
            curr = follow_through_frames[i]
            
            if "left_ankle" in prev and "left_ankle" in curr:
                motion = np.sqrt(
                    (curr["left_ankle"][0] - prev["left_ankle"][0])**2 +
                    (curr["left_ankle"][1] - prev["left_ankle"][1])**2
                )
                # Good follow-through has smooth, controlled motion
                motion_scores.append(min(100, motion * 500))
        
        if not motion_scores:
            return 50.0
        
        score = np.mean(motion_scores)
        metric = self.create_metric("follow_through", score, value=round(score, 1))
        metrics.append(metric)
        
        if score < 60:
            # Corrective feedback ONLY when fault is clearly detected (score < 60)
            feedback.append(self.create_actionable_feedback(
                "warning",
                "follow_through",
                "Follow-through toward target can be improved.",
                "Following through transfers power to the ball and improves accuracy.",
                [
                    "After contacting the ball, let your kicking leg continue its motion naturally",
                    "Follow through toward your target",
                    "Step through with your plant foot"
                ],
                "Wall passing drill with focus on follow-through",
                "Follow through"
            ))
        # No feedback when form is acceptable (score >= 60) for secondary metrics
        
        return score
    
    def _analyze_body_angle_crossing(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Crossing specific: Analyze body angle - should approach at angle, not straight on."""
        if not landmarks_list or len(landmarks_list) < 5:
            return 50.0
        
        # Analyze approach angle - hips should be open (angled approach)
        approach_frames = landmarks_list[:len(landmarks_list) // 2]
        angle_scores = []
        
        for landmarks in approach_frames:
            if all(k in landmarks for k in ["left_hip", "right_hip", "left_shoulder", "right_shoulder"]):
                hip_center_x = (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2
                shoulder_center_x = (landmarks["left_shoulder"][0] + landmarks["right_shoulder"][0]) / 2
                
                # For angled approach, hips and shoulders should be rotated (different X positions)
                # This indicates open hips for crossing
                rotation = abs(hip_center_x - shoulder_center_x)
                # Some rotation is good (0.02 to 0.05 ideal)
                if 0.02 <= rotation <= 0.05:
                    angle_scores.append(100.0)
                elif rotation < 0.02:
                    angle_scores.append(rotation / 0.02 * 70.0)
                else:
                    angle_scores.append(max(70, 100 - (rotation - 0.05) * 1000))
        
        if not angle_scores:
            return 50.0
        
        score = np.mean(angle_scores)
        metric = self.create_metric("body_angle", score, value=round(score, 1))
        metrics.append(metric)
        
        if score >= 85:
            # Positive feedback when form is excellent (score >= 85)
            feedback.append(self.create_feedback(
                "info",
                "Excellent body angle — proper angled approach for crossing. Keep reinforcing this mechanics.",
                "body_angle"
            ))
        elif score < 60:
            # Critical corrective feedback when fault is clearly detected (score < 60)
            feedback.append(self.create_actionable_feedback(
                "critical",
                "body_angle",
                "Crosses lack bend or height due to straight-on approach and direct contact.",
                "An angled run-up and wrapped foot create curl and loft, making crosses more dangerous and playable for teammates.",
                [
                    "Approach ball at a 30–45° angle",
                    "Plant foot slightly behind and beside the ball",
                    "Strike slightly off-center with instep/inside",
                    "Wrap foot across body during follow-through"
                ],
                "Crossing to target drill — 10 crosses from each wing, aiming for penalty spot or far post.",
                "Around the ball."
            ))
        else:
            # Warning corrective feedback for minor improvements (60 <= score < 85)
            feedback.append(self.create_actionable_feedback(
                "warning",
                "body_angle",
                "Body angle can be improved for better crossing technique.",
                "Approaching at an angle allows your leg to swing across your body and wrap around the ball for a curling cross.",
                [
                    "Approach ball at a 30–45° angle",
                    "Open hips to allow your leg to swing across your body",
                    "Strike the ball with instep/inside of your foot, slightly off-center"
                ],
                "Crossing to target drill from wide areas",
                "Around the ball"
            ))
        
        return score
    
    def _analyze_follow_through_crossing(self, landmarks_list: List[Dict], angles_list: List[Dict], metrics: List, feedback: List) -> float:
        """Crossing specific: Analyze wrap-around follow-through."""
        if not landmarks_list or len(landmarks_list) < 5:
            return 50.0
        
        # Analyze follow-through across body (wrapping motion)
        follow_through_frames = landmarks_list[len(landmarks_list) * 3 // 4:]
        if not follow_through_frames:
            return 50.0
        
        # Check for cross-body motion (wrapping)
        cross_body_scores = []
        for i in range(1, len(follow_through_frames)):
            prev = follow_through_frames[i-1]
            curr = follow_through_frames[i]
            
            if "left_ankle" in prev and "left_ankle" in curr and "right_ankle" in prev and "right_ankle" in curr:
                # For right-footer, left ankle (kicking leg) should move across body (toward right ankle)
                ankle_separation_prev = abs(prev["left_ankle"][0] - prev["right_ankle"][0])
                ankle_separation_curr = abs(curr["left_ankle"][0] - curr["right_ankle"][0])
                
                # Separation decreasing = wrapping motion (good)
                if ankle_separation_curr < ankle_separation_prev:
                    cross_body_scores.append(100.0)
                else:
                    cross_body_scores.append(50.0)
        
        if not cross_body_scores:
            return 50.0
        
        score = np.mean(cross_body_scores)
        metric = self.create_metric("follow_through", score, value=round(score, 1))
        metrics.append(metric)
        
        if score < 60:
            # Corrective feedback ONLY when fault is clearly detected (score < 60)
            feedback.append(self.create_actionable_feedback(
                "warning",
                "follow_through",
                "Follow-through across body can be improved.",
                "Following through across your body helps create the wrapping motion that generates curve on the cross.",
                [
                    "Follow through across your body",
                    "Your kicking foot should wrap around the ball and continue in the direction of the cross"
                ],
                "Crossing drill with focus on wrap-around follow-through",
                "Wrap around"
            ))
        # No feedback when form is acceptable (score >= 60) for secondary metrics
        
        return score
    
    def _analyze_close_control_dribbling(self, pose_data: List[Dict], metrics: List, feedback: List) -> float:
        """Dribbling specific: Analyze close control - small touches, ball close to feet."""
        if len(pose_data) < 10:
            return 50.0
        
        # Analyze ball proximity to feet (based on ankle position consistency)
        # Small, controlled touches = consistent ankle position with small variations
        ankle_positions = []
        for frame in pose_data:
            landmarks = frame.get("landmarks", {})
            if "left_ankle" in landmarks:
                ankle_positions.append((landmarks["left_ankle"][0], landmarks["left_ankle"][1]))
        
        if len(ankle_positions) < 10:
            return 50.0
        
        # Calculate step-to-step distances (should be small for close control)
        step_distances = []
        for i in range(1, len(ankle_positions)):
            distance = np.sqrt(
                (ankle_positions[i][0] - ankle_positions[i-1][0])**2 +
                (ankle_positions[i][1] - ankle_positions[i-1][1])**2
            )
            step_distances.append(distance)
        
        if not step_distances:
            return 50.0
        
        avg_step_distance = np.mean(step_distances)
        # Small steps (0.02 to 0.05) = close control (good)
        # Large steps (>0.1) = ball getting away (bad)
        if avg_step_distance <= 0.05:
            score = 100.0
        elif avg_step_distance <= 0.08:
            score = 85.0
        elif avg_step_distance <= 0.12:
            score = 70.0
        else:
            score = max(0, 100 - (avg_step_distance - 0.12) * 500)
        
        score = min(100, max(0, score))
        metric = self.create_metric("close_control", score, value=round(avg_step_distance, 3))
        metrics.append(metric)
        
        if score >= 85:
            # Positive feedback when form is excellent (score >= 85)
            feedback.append(self.create_feedback(
                "info",
                "Excellent close control — ball staying close to feet. Keep reinforcing this under pressure.",
                "close_control"
            ))
        elif score < 60:
            # Critical corrective feedback when fault is clearly detected (score < 60)
            feedback.append(self.create_actionable_feedback(
                "critical",
                "close_control",
                "Touches are too large and overly reliant on the dominant foot.",
                "Close control improves reaction time, unpredictability, and ability to beat defenders.",
                [
                    "Take smaller touches (1–2 feet ahead)",
                    "Use both feet and multiple foot surfaces",
                    "Stay low, knees bent, on toes",
                    "Keep head up while maintaining close control"
                ],
                "Cone weave drill — 6–8 cones, 3 rounds per variation (right foot, left foot, alternating).",
                "Small touches."
            ))
        else:
            # Warning corrective feedback for minor improvements (60 <= score < 85)
            feedback.append(self.create_actionable_feedback(
                "warning",
                "close_control",
                "Close control can be improved for better dribbling.",
                "Close control keeps the ball within reach so you can react to defenders and change direction quickly.",
                [
                    "Take smaller touches — tap the ball gently so it stays close in front of you",
                    "Use both feet and different parts of your foot",
                    "Keep your knees bent and stay on your toes"
                ],
                "Cone weave drill with alternating feet and small touches",
                "Small touches"
            ))
        
        return score
    
    def _analyze_soft_touch_first_touch(self, pose_data: List[Dict], metrics: List, feedback: List) -> float:
        """First Touch specific: Analyze soft cushioning - controlled first touch."""
        if len(pose_data) < 5:
            return 50.0
        
        # Analyze deceleration/control on first touch
        # Soft touch = smooth deceleration after ball contact
        ankle_positions = []
        for frame in pose_data:
            landmarks = frame.get("landmarks", {})
            if "left_ankle" in landmarks:
                ankle_positions.append((landmarks["left_ankle"][0], landmarks["left_ankle"][1]))
        
        if len(ankle_positions) < 5:
            return 50.0
        
        # Calculate velocities - should decrease smoothly (cushioning)
        velocities = []
        for i in range(1, len(ankle_positions)):
            velocity = np.sqrt(
                (ankle_positions[i][0] - ankle_positions[i-1][0])**2 +
                (ankle_positions[i][1] - ankle_positions[i-1][1])**2
            )
            velocities.append(velocity)
        
        if len(velocities) < 3:
            return 50.0
        
        # Check for smooth deceleration pattern (soft touch)
        early_velocity = np.mean(velocities[:len(velocities)//3])
        late_velocity = np.mean(velocities[len(velocities)*2//3:])
        
        # Deceleration indicates soft cushioning (good)
        if late_velocity < early_velocity * 0.7:
            score = 100.0
        elif late_velocity < early_velocity * 0.85:
            score = 85.0
        elif late_velocity < early_velocity:
            score = 70.0
        else:
            score = max(0, 100 - (late_velocity - early_velocity) * 1000)
        
        score = min(100, max(0, score))
        metric = self.create_metric("soft_touch", score, value=round(score, 1))
        metrics.append(metric)
        
        if score >= 85:
            # Positive feedback when form is excellent (score >= 85)
            feedback.append(self.create_feedback(
                "info",
                "Excellent soft touch — controlled first touch. Keep reinforcing this.",
                "soft_touch"
            ))
        elif score < 60:
            # Critical corrective feedback when fault is clearly detected (score < 60)
            feedback.append(self.create_actionable_feedback(
                "critical",
                "soft_touch",
                "First touch is heavy, allowing the ball to bounce or roll away.",
                "A soft first touch preserves possession and sets up the next action efficiently.",
                [
                    "Relax receiving surface and \"give\" with the ball",
                    "Angle touch into space or away from defenders",
                    "Stay on toes and anticipate ball speed",
                    "Watch ball into contact"
                ],
                "Wall control drill — 3 sets of 10 receptions per foot, alternating dead stops and directional touches.",
                "Soft touch."
            ))
        else:
            # Warning corrective feedback for minor improvements (60 <= score < 85)
            feedback.append(self.create_actionable_feedback(
                "warning",
                "soft_touch",
                "First touch can be improved for better ball control.",
                "A soft, controlled first touch allows you to keep possession and choose your next move.",
                [
                    "Relax the part of your body receiving the ball — slightly withdraw to \"give\" with the ball's momentum",
                    "Decide your direction on the first touch",
                    "Be on your toes and watch the ball in — anticipate its speed and trajectory"
                ],
                "Wall control drill focusing on cushioning",
                "Soft touch"
            ))
        
        return score
    
    def _analyze_balance(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """General balance analysis for soccer movements."""
        if not landmarks_list:
            return 50.0
        
        balance_scores = []
        for landmarks in landmarks_list:
            if all(k in landmarks for k in ["left_ankle", "right_ankle", "left_hip", "right_hip"]):
                ankle_center_x = (landmarks["left_ankle"][0] + landmarks["right_ankle"][0]) / 2
                hip_center_x = (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2
                
                # Good balance = body center over base
                deviation = abs(hip_center_x - ankle_center_x)
                balance = max(0, 100 - (deviation * 400))
                balance_scores.append(balance)
        
        if not balance_scores:
            return 50.0
        
        score = np.mean(balance_scores)
        metric = self.create_metric("balance", score, value=round(score, 1))
        metrics.append(metric)
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent balance maintained.", "balance"))
        else:
            feedback.append(self.create_feedback("warning", "Balance can be improved for better control and stability.", "balance"))
        
        return score

    def _create_empty_result(self) -> AnalysisResult:
        return AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            video_id="",
            sport="soccer",
            exercise_type=self.movement_type,
            overall_score=0.0,
            metrics=[],
            feedback=[],
            strengths=[],
            weaknesses=[],
            raw_data={},
            created_at=datetime.now(),
        )

