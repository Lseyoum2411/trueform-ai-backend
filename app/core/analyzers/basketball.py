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
        
        overall_score = np.mean([
            base_stability_score, vertical_alignment_score, shot_rhythm_score,
            one_motion_flow_score, release_speed_score, knee_bend_score,
            hip_alignment_score, elbow_alignment_score, shooting_pocket_score,
            release_point_score, shot_arc_score, follow_through_score,
            wrist_snap_score,
        ])
        
        for metric in metrics:
            if metric.score >= 80:
                strengths.append(f"{metric.name}: {metric.score:.1f}/100")
            elif metric.score < 60:
                weaknesses.append(f"{metric.name}: {metric.score:.1f}/100")
        
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
            feedback.append(self.create_feedback("info", "Excellent base stability — solid foundation.", "base_stability"))
            strengths.append("Strong base stability")
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "base_stability",
                "Your feet are positioned too close together or too far apart.",
                "An improper stance width reduces balance and power transfer from your legs to your shot.",
                [
                    "Place your feet directly under your shoulders with toes pointing forward",
                    "Feel your weight evenly distributed on both feet before you shoot",
                    "Maintain this width throughout your entire shooting motion"
                ],
                "Stance-width form shooting from close range. Check foot position before each shot. Make multiple shots focusing only on base width.",
                "Shoulder width base"
            ))
        
        return score
    
    def _analyze_vertical_alignment(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        if not landmarks_list:
            return 50.0
        
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
        metrics.append(self.create_metric("vertical_alignment", score, value=round(score, 1)))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Perfect vertical alignment — body stacked correctly.", "vertical_alignment"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "vertical_alignment",
                "Your body is leaning forward or backward instead of staying straight.",
                "Leaning reduces balance and makes it harder to generate consistent power from your legs.",
                [
                    "Feel your head stacked directly over your shoulders",
                    "Keep your hips directly under your shoulders with no forward or backward lean",
                    "Drive straight up through your legs instead of leaning to create power"
                ],
                "Vertical alignment form shooting from close range. Use a mirror to check your posture. Hold the start position briefly before each shot. Make multiple shots.",
                "Stay stacked"
            ))
        
        return score
    
    def _analyze_shot_rhythm(self, pose_data: List[Dict], metrics: List, feedback: List, strengths: List) -> float:
        if len(pose_data) < 10:
            return 50.0
        
        frame_times = [i * 0.033 for i in range(len(pose_data))]
        motion_velocity = []
        
        for i in range(1, len(pose_data)):
            prev_landmarks = pose_data[i-1].get("landmarks", {})
            curr_landmarks = pose_data[i].get("landmarks", {})
            
            if "right_wrist" in prev_landmarks and "right_wrist" in curr_landmarks:
                velocity = np.sqrt(
                    (curr_landmarks["right_wrist"][0] - prev_landmarks["right_wrist"][0])**2 +
                    (curr_landmarks["right_wrist"][1] - prev_landmarks["right_wrist"][1])**2
                )
                motion_velocity.append(velocity)
        
        if not motion_velocity:
            return 50.0
        
        velocity_variance = np.var(motion_velocity)
        ideal_variance = 0.001
        rhythm_score = max(0, 100 - (abs(velocity_variance - ideal_variance) * 50000))
        
        score = round(rhythm_score, 2)
        metrics.append(self.create_metric("shot_rhythm", score, value=round(velocity_variance, 4), unit="variance"))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Perfect one-motion shot — Curry-level smoothness.", "shot_rhythm"))
            strengths.append("Elite shot rhythm")
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "shot_rhythm",
                "Your shooting motion has inconsistent timing between attempts.",
                "Varying rhythm makes it harder to develop muscle memory and repeat your shot under pressure.",
                [
                    "Start your upward motion with the ball already set near your shooting pocket",
                    "Eliminate any pause between knee bend and arm extension",
                    "Keep the ball moving continuously upward from start to release"
                ],
                "One-motion form shooting from close to mid-range. Make multiple shots without stopping the ball at any point during your motion.",
                "One smooth motion"
            ))
        
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
        for landmarks in landmarks_list:
            if all(k in landmarks for k in ["nose", "left_hip", "right_hip", "left_ankle", "right_ankle"]):
                hip_center_x = (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2
                ankle_center_x = (landmarks["left_ankle"][0] + landmarks["right_ankle"][0]) / 2
                nose_x = landmarks["nose"][0]
                
                vertical_deviation = abs(nose_x - hip_center_x) + abs(hip_center_x - ankle_center_x)
                alignment = max(0, 100 - (vertical_deviation * 300))
                alignment_scores.append(alignment)
        
        score = np.mean(alignment_scores) if alignment_scores else 50.0
        metrics.append(self.create_metric("vertical_alignment", score, value=round(score, 1)))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Perfect vertical alignment — body stacked correctly for balanced shot.", "vertical_alignment"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "vertical_alignment",
                "Your body is leaning, drifting, or twisting during shots off the dribble instead of staying balanced.",
                "Leaning reduces balance and makes it harder to generate consistent power. Body control and balance allow the same mechanics at game speed.",
                [
                    "Feel your head stacked directly over your shoulders throughout the shot",
                    "Keep your hips directly under your shoulders with no forward, backward, or side lean",
                    "Drive straight up through your legs instead of leaning to create power"
                ],
                "One-dribble pull-up with focus on body control. Check alignment in mirror before each shot. Make 20 shots emphasizing balance.",
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
    
    def _analyze_shooting_pocket(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        if not landmarks_list:
            return 50.0
        
        pocket_scores = []
        for landmarks in landmarks_list:
            if all(k in landmarks for k in ["right_elbow", "right_wrist", "right_shoulder"]):
                elbow_y = landmarks["right_elbow"][1]
                wrist_y = landmarks["right_wrist"][1]
                shoulder_y = landmarks["right_shoulder"][1]
                
                pocket_height = abs(elbow_y - shoulder_y)
                ideal_pocket = 0.15
                deviation = abs(pocket_height - ideal_pocket)
                pocket_score = max(0, 100 - (deviation * 400))
                pocket_scores.append(pocket_score)
        
        score = np.mean(pocket_scores) if pocket_scores else 50.0
        metrics.append(self.create_metric("shooting_pocket", score, value=round(score, 1)))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Good shooting pocket position.", "shooting_pocket"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "shooting_pocket",
                "Your shooting pocket is positioned too high or too low.",
                "An incorrect pocket position disrupts timing and makes it harder to generate consistent power and rhythm.",
                [
                    "Set the ball just outside your dominant shoulder with your elbow at 90 degrees",
                    "Keep the ball above your waist and below your chin",
                    "Feel your forearm stay vertical before you start your upward motion"
                ],
                "Stationary pocket check shooting from close range. Hold pocket position briefly, then shoot. Make multiple shots focusing on correct pocket height.",
                "Pocket clean"
            ))
        
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





