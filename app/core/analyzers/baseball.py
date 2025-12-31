from typing import List, Dict
from datetime import datetime
import numpy as np
import uuid
from app.core.analyzers.base import BaseAnalyzer
from app.models.analysis import AnalysisResult, MetricScore, FeedbackItem


class BaseballAnalyzer(BaseAnalyzer):
    def __init__(self, exercise_type: str = "pitching"):
        super().__init__()
        self.exercise_type = exercise_type.lower()
        if self.exercise_type not in ["pitching", "batting", "catcher", "fielding"]:
            self.exercise_type = "pitching"
    
    async def analyze(self, pose_data: List[Dict]) -> AnalysisResult:
        if not pose_data:
            return self._create_empty_result()
        
        metrics = []
        feedback = []
        strengths = []
        weaknesses = []
        
        landmarks_list = [frame.get("landmarks", {}) for frame in pose_data]
        angles_list = [frame.get("angles", {}) for frame in pose_data]
        
        # Movement-specific analysis with different priorities
        if self.exercise_type == "pitching":
            # Pitching: Focus on Lower Body Engagement (High Priority)
            lower_body_score = self._analyze_pitching_lower_body_engagement(landmarks_list, angles_list, metrics, feedback, strengths)
            hip_rotation_score = self._analyze_hip_rotation(landmarks_list, angles_list, metrics, feedback)
            stride_score = self._analyze_stride_athletic_posture(landmarks_list, metrics, feedback)
            # Pitching critical: lower_body_engagement
            metric_scores = [m.score for m in metrics]
            critical_metric_names = ["lower_body_engagement"]
            critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=critical_indices, max_critical_failures=2, max_moderate_failures=3)
            
        elif self.exercise_type == "batting":
            # Batting: Focus on Weight Transfer (High Priority)
            weight_transfer_score = self._analyze_batting_weight_transfer(landmarks_list, angles_list, metrics, feedback, strengths)
            hip_rotation_score = self._analyze_batting_hip_rotation(landmarks_list, angles_list, metrics, feedback)
            stride_score = self._analyze_batting_stride(landmarks_list, metrics, feedback)
            metric_scores = [m.score for m in metrics]
            critical_metric_names = ["weight_transfer"]
            critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=critical_indices, max_critical_failures=2, max_moderate_failures=3)
            
        elif self.exercise_type == "catcher":
            # Catcher: Focus on Quick Throwing Release (High Priority)
            quick_release_score = self._analyze_catcher_quick_release(pose_data, landmarks_list, metrics, feedback, strengths)
            footwork_score = self._analyze_catcher_footwork(landmarks_list, metrics, feedback)
            arm_path_score = self._analyze_catcher_arm_path(landmarks_list, angles_list, metrics, feedback)
            metric_scores = [m.score for m in metrics]
            critical_metric_names = ["quick_release"]
            critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=critical_indices, max_critical_failures=2, max_moderate_failures=3)
            
        elif self.exercise_type == "fielding":
            # Fielding: Focus on Stay Low and Centered (High Priority)
            stay_low_score = self._analyze_fielding_stay_low(landmarks_list, angles_list, metrics, feedback, strengths)
            centered_approach_score = self._analyze_fielding_centered(landmarks_list, metrics, feedback)
            two_hands_score = self._analyze_fielding_two_hands(landmarks_list, metrics, feedback)
            metric_scores = [m.score for m in metrics]
            critical_metric_names = ["stay_low"]
            critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=critical_indices, max_critical_failures=2, max_moderate_failures=3)
            
        else:
            # Default fallback (should not occur due to validation in __init__)
            # If we somehow get here, default to pitching analysis
            lower_body_score = self._analyze_pitching_lower_body_engagement(landmarks_list, angles_list, metrics, feedback, strengths)
            metric_scores = [m.score for m in metrics] if metrics else [lower_body_score]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=[], max_critical_failures=2, max_moderate_failures=3) if metrics else lower_body_score
        
        # Populate strengths and weaknesses from metrics (NO numeric values)
        for metric in metrics:
            if metric.score >= 80:
                strengths.append(self.get_qualitative_strength_description(metric.name))
            elif metric.score < 60:
                weaknesses.append(self.get_qualitative_weakness_description(metric.name))
        
        # Consolidate duplicate weight transfer feedback (remove hip_rotation feedback if weight_transfer exists)
        feedback = self.consolidate_weight_transfer_feedback(feedback)
        
        # Remove any remaining duplicate feedback items by metric name
        feedback = self.deduplicate_feedback_by_metric(feedback)
        
        return AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            video_id="",
            sport="baseball",
            exercise_type=self.exercise_type,
            overall_score=round(overall_score, 2),
            metrics=metrics,
            feedback=feedback,
            strengths=strengths,
            weaknesses=weaknesses,
            raw_data={"frame_count": len(pose_data), "exercise_type": self.exercise_type},
            created_at=datetime.now(),
        )
    
    # ==================== PITCHING ANALYSIS ====================
    
    def _analyze_pitching_lower_body_engagement(self, landmarks_list: List[Dict], angles_list: List[Dict], metrics: List, feedback: List, strengths: List) -> float:
        """High Priority: Analyze lower body engagement and leg drive for pitching."""
        if not landmarks_list or not angles_list:
            return 50.0
        
        # Analyze knee bend depth (deeper = more leg engagement)
        knee_angles = []
        for angles in angles_list:
            if "right_knee" in angles:
                knee_angles.append(angles["right_knee"])
            elif "left_knee" in angles:
                knee_angles.append(angles["left_knee"])
        
        if not knee_angles:
            return 50.0
        
        avg_knee_angle = np.mean(knee_angles)
        min_knee_angle = min(knee_angles)  # Most bent position
        
        # Ideal knee bend for pitching drive phase: ~90-110 degrees
        # Lower angle (more bent) = better leg engagement
        ideal_knee_min = 90.0
        knee_engagement_score = max(0, 100 - abs(min_knee_angle - ideal_knee_min) * 0.8)
        
        # Analyze hip angle (hip extension indicates drive)
        hip_angles = []
        for angles in angles_list:
            if "right_hip" in angles:
                hip_angles.append(angles["right_hip"])
            elif "left_hip" in angles:
                hip_angles.append(angles["left_hip"])
        
        if hip_angles:
            avg_hip_angle = np.mean(hip_angles)
            # Higher hip angle indicates better extension/drive
            ideal_hip = 140.0
            hip_drive_score = max(0, 100 - abs(avg_hip_angle - ideal_hip) * 0.6)
            combined_score = (knee_engagement_score * 0.6 + hip_drive_score * 0.4)
        else:
            combined_score = knee_engagement_score
        
        score = round(combined_score, 2)
        metrics.append(self.create_metric("lower_body_engagement", score, value=round(min_knee_angle, 1), unit="degrees"))
        
        if score >= 85:
            # Positive feedback when form is excellent (score >= 85)
            feedback.append(self.create_feedback(
                "info",
                "Excellent lower body engagement — strong leg drive and hip rotation generating power effectively. Keep reinforcing this mechanics.",
                "lower_body_engagement"
            ))
            strengths.append("Strong leg and hip drive")
        elif score < 60:
            # Critical corrective feedback when fault is clearly detected (score < 60)
            feedback.append(self.create_actionable_feedback(
                "critical",
                "lower_body_engagement",
                "You're not fully using your legs and hips when pitching, instead relying mostly on your arm for power.",
                "Power in pitching comes from the ground up. Failing to engage the lower body reduces velocity and increases arm strain. Proper leg drive and hip rotation increase speed and protect the arm.",
                [
                    "Push forcefully off the rubber with your back leg as you stride",
                    "Stay in a slight squat/athletic posture down the mound",
                    "Rotate hips before the arm comes through (legs → hips → arm)",
                    "Keep the core tight to transfer energy efficiently"
                ],
                "Towel snap drill — Hold a towel and snap it at a target using full leg drive and hip rotation. Do 5–8 reps.",
                "Use your legs."
            ))
        else:
            # Warning corrective feedback for minor improvements (60 <= score < 85)
            feedback.append(self.create_actionable_feedback(
                "warning",
                "lower_body_engagement",
                "Lower body engagement can be improved for better power and safety.",
                "Increasing leg and hip drive will improve velocity while reducing stress on your throwing arm.",
                [
                    "Focus on driving harder off your back leg",
                    "Feel your hips rotate before your arm accelerates",
                    "Think about transferring power from the ground up"
                ],
                "Towel snap drill emphasizing leg drive and hip rotation",
                "Drive from the ground"
            ))
        
        return score
    
    def _analyze_hip_rotation(self, landmarks_list: List[Dict], angles_list: List[Dict], metrics: List, feedback: List) -> float:
        """Analyze hip rotation timing and range for pitching."""
        if not landmarks_list or len(landmarks_list) < 5:
            return 50.0
        
        # Analyze hip separation (difference between shoulder and hip rotation)
        rotation_scores = []
        for i in range(1, len(landmarks_list)):
            landmarks = landmarks_list[i]
            if "left_shoulder" in landmarks and "right_shoulder" in landmarks and "left_hip" in landmarks and "right_hip" in landmarks:
                shoulder_center_x = (landmarks["left_shoulder"][0] + landmarks["right_shoulder"][0]) / 2
                hip_center_x = (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2
                separation = abs(shoulder_center_x - hip_center_x)
                rotation_scores.append(separation)
        
        if not rotation_scores:
            return 50.0
        
        max_separation = max(rotation_scores)
        # Good hip-shoulder separation indicates proper rotation
        ideal_separation = 0.12
        rotation_score = max(0, 100 - abs(max_separation - ideal_separation) * 500)
        
        score = round(rotation_score, 2)
        metrics.append(self.create_metric("hip_rotation", score, value=round(max_separation, 3)))
        
        if score < 60:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "hip_rotation",
                "Your hips are rotating too early or too late relative to your shoulders.",
                "Proper hip-shoulder separation creates torque and generates power while reducing arm stress.",
                [
                    "Let your hips lead the rotation",
                    "Create separation between hips and shoulders before arm acceleration",
                    "Feel your core engage during rotation"
                ],
                "Hip rotation drill with focus on timing",
                "Hips first"
            ))
        
        return score
    
    def _analyze_stride_athletic_posture(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Analyze athletic posture during stride phase."""
        if not landmarks_list:
            return 50.0
        
        # Analyze vertical alignment during stride
        alignment_scores = []
        for landmarks in landmarks_list:
            if all(k in landmarks for k in ["nose", "left_hip", "right_hip", "left_ankle", "right_ankle"]):
                hip_center_x = (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2
                ankle_center_x = (landmarks["left_ankle"][0] + landmarks["right_ankle"][0]) / 2
                nose_x = landmarks["nose"][0]
                
                vertical_deviation = abs(nose_x - hip_center_x) + abs(hip_center_x - ankle_center_x)
                alignment = max(0, 100 - (vertical_deviation * 300))
                alignment_scores.append(alignment)
        
        score = np.mean(alignment_scores) if alignment_scores else 50.0
        metrics.append(self.create_metric("athletic_posture", score, value=round(score, 1)))
        
        if score < 60:
            feedback.append(self.create_feedback(
                "warning",
                "Maintain athletic posture during stride — avoid leaning too far forward or backward.",
                "athletic_posture"
            ))
        
        return score
    
    # ==================== BATTING ANALYSIS ====================
    
    def _analyze_batting_weight_transfer(self, landmarks_list: List[Dict], angles_list: List[Dict], metrics: List, feedback: List, strengths: List) -> float:
        """High Priority: Analyze weight transfer from back foot to front foot for batting."""
        if not landmarks_list or len(landmarks_list) < 5:
            return 50.0
        
        # Analyze center of mass shift (using hip position)
        hip_center_positions = []
        for landmarks in landmarks_list:
            if "left_hip" in landmarks and "right_hip" in landmarks:
                hip_center = (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2
                hip_center_positions.append(hip_center)
        
        if len(hip_center_positions) < 5:
            return 50.0
        
        # Calculate weight shift (difference between start and contact point)
        start_position = np.mean(hip_center_positions[:len(hip_center_positions)//3])
        contact_position = np.mean(hip_center_positions[-len(hip_center_positions)//3:])
        weight_shift = abs(contact_position - start_position)
        
        # Good weight transfer shows significant forward shift
        ideal_shift = 0.15
        transfer_score = max(0, 100 - abs(weight_shift - ideal_shift) * 400)
        
        score = round(transfer_score, 2)
        metrics.append(self.create_metric("weight_transfer", score, value=round(weight_shift, 3)))
        
        if score >= 85:
            # Positive feedback when form is excellent (score >= 85)
            feedback.append(self.create_feedback(
                "info",
                "Excellent weight transfer — strong back-to-front shift generating power from your lower body. Maintain this timing.",
                "weight_transfer"
            ))
            strengths.append("Strong weight transfer")
        elif score < 60:
            # Critical corrective feedback when fault is clearly detected (score < 60)
            feedback.append(self.create_actionable_feedback(
                "critical",
                "weight_transfer",
                "You're not shifting your weight from your back foot to your front foot, causing weaker, arm-dominant swings.",
                "Bat speed and power come from proper weight transfer and hip rotation. Without it, contact is weak and inconsistent.",
                [
                    "Start with weight slightly on the back leg",
                    "Take a small stride and shift weight forward",
                    "Rotate hips fully toward the ball",
                    "Let the back foot pivot (\"squish the bug\")"
                ],
                "Batting tee drill — 3 sets of 5 swings focusing on shifting from 70% back foot to 70% front foot.",
                "Back to front."
            ))
        else:
            # Warning corrective feedback for minor improvements (60 <= score < 85)
            feedback.append(self.create_actionable_feedback(
                "warning",
                "weight_transfer",
                "Weight transfer can be improved for more power.",
                "Better weight transfer generates more bat speed and power from your lower body.",
                [
                    "Feel your weight start on your back foot",
                    "Shift forward as you stride",
                    "Rotate your hips into the swing"
                ],
                "Batting tee drill focusing on weight shift",
                "Shift and rotate"
            ))
        
        return score
    
    def _analyze_batting_hip_rotation(self, landmarks_list: List[Dict], angles_list: List[Dict], metrics: List, feedback: List) -> float:
        """
        Analyze hip rotation toward pitcher for batting.
        NOTE: For batting, hip rotation is part of weight transfer, so feedback is suppressed
        to avoid duplicate weight transfer feedback. The metric is still tracked for scoring.
        """
        if not landmarks_list or len(landmarks_list) < 5:
            return 50.0
        
        # Similar to pitching but for batting rotation
        rotation_scores = []
        for landmarks in landmarks_list:
            if "left_shoulder" in landmarks and "right_shoulder" in landmarks and "left_hip" in landmarks and "right_hip" in landmarks:
                shoulder_center_x = (landmarks["left_shoulder"][0] + landmarks["right_shoulder"][0]) / 2
                hip_center_x = (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2
                separation = abs(shoulder_center_x - hip_center_x)
                rotation_scores.append(separation)
        
        if not rotation_scores:
            return 50.0
        
        max_separation = max(rotation_scores)
        ideal_separation = 0.10
        rotation_score = max(0, 100 - abs(max_separation - ideal_separation) * 500)
        
        score = round(rotation_score, 2)
        metrics.append(self.create_metric("hip_rotation", score, value=round(max_separation, 3)))
        
        # DO NOT generate feedback for hip_rotation in batting - weight_transfer feedback already covers this
        # Hip rotation is part of the weight transfer mechanism, so including it would create duplicate feedback
        
        return score
    
    def _analyze_batting_stride(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Analyze stride length and timing for batting."""
        if not landmarks_list or len(landmarks_list) < 5:
            return 50.0
        
        # Analyze stride by looking at foot positions
        stride_scores = []
        for landmarks in landmarks_list:
            if "left_ankle" in landmarks and "right_ankle" in landmarks:
                stride_width = abs(landmarks["left_ankle"][0] - landmarks["right_ankle"][0])
                stride_scores.append(stride_width)
        
        if not stride_scores:
            return 50.0
        
        avg_stride = np.mean(stride_scores)
        max_stride = max(stride_scores)
        ideal_stride = 0.25
        stride_score = max(0, 100 - abs(max_stride - ideal_stride) * 300)
        
        score = round(stride_score, 2)
        metrics.append(self.create_metric("stride", score, value=round(max_stride, 3)))
        
        return score
    
    # ==================== CATCHER ANALYSIS ====================
    
    def _analyze_catcher_quick_release(self, pose_data: List[Dict], landmarks_list: List[Dict], metrics: List, feedback: List, strengths: List) -> float:
        """High Priority: Analyze quick throwing release for catcher."""
        if not pose_data or len(pose_data) < 5:
            return 50.0
        
        # Analyze transfer speed (how quickly hand moves from glove position to throwing position)
        # Look at wrist velocity during early frames (transfer phase)
        transfer_velocities = []
        for i in range(1, min(10, len(pose_data))):
            prev_landmarks = pose_data[i-1].get("landmarks", {})
            curr_landmarks = pose_data[i].get("landmarks", {})
            
            if "right_wrist" in prev_landmarks and "right_wrist" in curr_landmarks:
                velocity = np.sqrt(
                    (curr_landmarks["right_wrist"][0] - prev_landmarks["right_wrist"][0])**2 +
                    (curr_landmarks["right_wrist"][1] - prev_landmarks["right_wrist"][1])**2
                ) / 0.033
                transfer_velocities.append(velocity)
        
        if not transfer_velocities:
            return 50.0
        
        avg_transfer_velocity = np.mean(transfer_velocities)
        # Higher velocity indicates quicker transfer
        ideal_velocity = 0.35
        release_score = max(0, 100 - abs(avg_transfer_velocity - ideal_velocity) * 200)
        
        score = round(release_score, 2)
        metrics.append(self.create_metric("quick_release", score, value=round(avg_transfer_velocity, 3), unit="m/s"))
        
        if score >= 85:
            # Positive feedback when form is excellent (score >= 85)
            feedback.append(self.create_feedback(
                "info",
                "Fast glove-to-hand transfer — efficient release and footwork. Keep reinforcing this quick, compact motion.",
                "quick_release"
            ))
            strengths.append("Quick transfer")
        elif score < 60:
            # Critical corrective feedback when fault is clearly detected (score < 60)
            feedback.append(self.create_actionable_feedback(
                "critical",
                "quick_release",
                "Throws are slow due to extra glove-to-hand motion and inefficient footwork.",
                "A catcher's pop time determines stolen bases. Faster transfers and compact movements improve throw speed and accuracy.",
                [
                    "Bring glove straight to chest for transfer",
                    "Shorten arm path (glove → ear → throw)",
                    "Use quick right-left footwork toward second base",
                    "Begin throwing motion as feet land"
                ],
                "Pop-up throw drill — 10 reps simulating different pitch locations.",
                "Quick transfer."
            ))
        else:
            # Warning corrective feedback for minor improvements (60 <= score < 85)
            feedback.append(self.create_actionable_feedback(
                "warning",
                "quick_release",
                "Release speed can be improved for better game control.",
                "Faster transfers improve throw accuracy and help catch runners.",
                [
                    "Focus on immediate ball transfer to chest",
                    "Keep arm path compact",
                    "Coordinate footwork with transfer"
                ],
                "Pop-up throw drill emphasizing speed",
                "Transfer fast"
            ))
        
        return score
    
    def _analyze_catcher_footwork(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Analyze footwork efficiency for catcher throwing."""
        if not landmarks_list or len(landmarks_list) < 5:
            return 50.0
        
        # Analyze foot movement direction (should move toward target)
        foot_movements = []
        for i in range(1, len(landmarks_list)):
            prev_landmarks = landmarks_list[i-1]
            curr_landmarks = landmarks_list[i]
            
            if "right_ankle" in prev_landmarks and "right_ankle" in curr_landmarks:
                movement = abs(curr_landmarks["right_ankle"][0] - prev_landmarks["right_ankle"][0])
                foot_movements.append(movement)
        
        if not foot_movements:
            return 50.0
        
        avg_movement = np.mean(foot_movements)
        # Good footwork shows purposeful movement
        ideal_movement = 0.08
        footwork_score = max(0, 100 - abs(avg_movement - ideal_movement) * 800)
        
        score = round(footwork_score, 2)
        metrics.append(self.create_metric("footwork", score, value=round(avg_movement, 3)))
        
        if score < 60:
            feedback.append(self.create_feedback(
                "warning",
                "Use right-left footwork toward target for better throwing accuracy.",
                "footwork"
            ))
        
        return score
    
    def _analyze_catcher_arm_path(self, landmarks_list: List[Dict], angles_list: List[Dict], metrics: List, feedback: List) -> float:
        """Analyze compact arm path (glove to ear) for catcher."""
        if not landmarks_list or not angles_list:
            return 50.0
        
        # Analyze elbow angle (compact path = shorter arm path)
        elbow_angles = []
        for angles in angles_list:
            if "right_elbow" in angles:
                elbow_angles.append(angles["right_elbow"])
        
        if not elbow_angles:
            return 50.0
        
        avg_elbow_angle = np.mean(elbow_angles)
        min_elbow_angle = min(elbow_angles)
        # Compact path = smaller elbow angle during cocking phase
        ideal_elbow_min = 75.0
        arm_path_score = max(0, 100 - abs(min_elbow_angle - ideal_elbow_min) * 1.0)
        
        score = round(arm_path_score, 2)
        metrics.append(self.create_metric("arm_path", score, value=round(min_elbow_angle, 1), unit="degrees"))
        
        if score < 60:
            feedback.append(self.create_feedback(
                "warning",
                "Use a more compact arm path — glove directly to ear position.",
                "arm_path"
            ))
        
        return score
    
    # ==================== FIELDING ANALYSIS ====================
    
    def _analyze_fielding_stay_low(self, landmarks_list: List[Dict], angles_list: List[Dict], metrics: List, feedback: List, strengths: List) -> float:
        """High Priority: Analyze staying low and centered for fielding."""
        if not landmarks_list or not angles_list:
            return 50.0
        
        # Analyze knee bend (staying low = deeper knee bend)
        knee_angles = []
        for angles in angles_list:
            if "left_knee" in angles:
                knee_angles.append(angles["left_knee"])
            elif "right_knee" in angles:
                knee_angles.append(angles["right_knee"])
        
        if not knee_angles:
            return 50.0
        
        avg_knee_angle = np.mean(knee_angles)
        min_knee_angle = min(knee_angles)
        
        # Good fielding position: low (knee angle ~100-120 degrees)
        ideal_knee_min = 110.0
        stay_low_score = max(0, 100 - abs(min_knee_angle - ideal_knee_min) * 0.8)
        
        score = round(stay_low_score, 2)
        metrics.append(self.create_metric("stay_low", score, value=round(min_knee_angle, 1), unit="degrees"))
        
        if score >= 85:
            # Positive feedback when form is excellent (score >= 85)
            feedback.append(self.create_feedback(
                "info",
                "Excellent low fielding position — athletic and ready. Continue reinforcing this centered approach.",
                "stay_low"
            ))
            strengths.append("Good low position")
        elif score < 60:
            # Critical corrective feedback when fault is clearly detected (score < 60)
            feedback.append(self.create_actionable_feedback(
                "critical",
                "stay_low",
                "You field too upright and reach from the side instead of getting behind the ball.",
                "Staying low and centered improves clean fielding and recovery on bad hops while setting up quicker throws.",
                [
                    "Bend knees and lower glove early",
                    "Move feet to align body behind the ball",
                    "Field with two hands (glove + bare hand)",
                    "Square chest to the ball's path"
                ],
                "Soft hands & smother drill — 2 sets of 10 ground balls focusing on staying low and centered.",
                "Stay low."
            ))
        else:
            # Warning corrective feedback for minor improvements (60 <= score < 85)
            feedback.append(self.create_actionable_feedback(
                "warning",
                "stay_low",
                "Fielding position can be improved by staying lower.",
                "A lower position improves reaction time and allows better foot movement.",
                [
                    "Bend your knees more in ready position",
                    "Keep your center of gravity low",
                    "Avoid reaching — move your feet"
                ],
                "Low position fielding drill",
                "Get down"
            ))
        
        return score
    
    def _analyze_fielding_centered(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Analyze centered approach (moving feet vs reaching) for fielding."""
        if not landmarks_list or len(landmarks_list) < 5:
            return 50.0
        
        # Analyze body alignment (centered = nose/hip/ankle aligned)
        alignment_scores = []
        for landmarks in landmarks_list:
            if all(k in landmarks for k in ["nose", "left_hip", "right_hip", "left_ankle", "right_ankle"]):
                hip_center_x = (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2
                ankle_center_x = (landmarks["left_ankle"][0] + landmarks["right_ankle"][0]) / 2
                nose_x = landmarks["nose"][0]
                
                # Check if body is centered (small deviation)
                deviation = abs(nose_x - hip_center_x) + abs(hip_center_x - ankle_center_x)
                alignment = max(0, 100 - (deviation * 400))
                alignment_scores.append(alignment)
        
        score = np.mean(alignment_scores) if alignment_scores else 50.0
        metrics.append(self.create_metric("centered_approach", score, value=round(score, 1)))
        
        if score < 60:
            feedback.append(self.create_feedback(
                "warning",
                "Move your feet to center the ball instead of reaching laterally.",
                "centered_approach"
            ))
        
        return score
    
    def _analyze_fielding_two_hands(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Analyze two-hand fielding position."""
        if not landmarks_list:
            return 50.0
        
        # Analyze hand proximity (two hands = hands close together)
        hand_distances = []
        for landmarks in landmarks_list:
            if "left_wrist" in landmarks and "right_wrist" in landmarks:
                distance = np.sqrt(
                    (landmarks["left_wrist"][0] - landmarks["right_wrist"][0])**2 +
                    (landmarks["left_wrist"][1] - landmarks["right_wrist"][1])**2
                )
                hand_distances.append(distance)
        
        if not hand_distances:
            return 50.0
        
        avg_distance = np.mean(hand_distances)
        ideal_distance = 0.15  # Hands close together
        two_hands_score = max(0, 100 - abs(avg_distance - ideal_distance) * 400)
        
        score = round(two_hands_score, 2)
        metrics.append(self.create_metric("two_hand_fielding", score, value=round(avg_distance, 3)))
        
        if score < 60:
            feedback.append(self.create_feedback(
                "warning",
                "Field the ball with two hands for better control and quicker transfer.",
                "two_hand_fielding"
            ))
        
        return score
    
    def _create_empty_result(self) -> AnalysisResult:
        return AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            video_id="",
            sport="baseball",
            exercise_type=self.exercise_type,
            overall_score=0.0,
            metrics=[],
            feedback=[self.create_feedback("error", "No pose data detected in video.")],
            strengths=[],
            weaknesses=[],
            raw_data={},
            created_at=datetime.now(),
        )
