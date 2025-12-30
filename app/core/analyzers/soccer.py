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
            overall_score = np.mean([lean_forward_score, balance_score, follow_through_score])
        elif self.movement_type == "passing_technique":
            # Passing: Focus on Lock Ankle & Follow Through (High Priority)
            ankle_stability_score = self._analyze_ankle_stability_passing(angles_list, metrics, feedback)
            follow_through_score = self._analyze_follow_through_passing(landmarks_list, angles_list, metrics, feedback)
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            overall_score = np.mean([ankle_stability_score, follow_through_score, balance_score])
        elif self.movement_type == "crossing_technique":
            # Crossing: Focus on Body Angle & Wrap the Foot (High Priority)
            body_angle_score = self._analyze_body_angle_crossing(landmarks_list, metrics, feedback)
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            follow_through_score = self._analyze_follow_through_crossing(landmarks_list, angles_list, metrics, feedback)
            overall_score = np.mean([body_angle_score, balance_score, follow_through_score])
        elif self.movement_type == "dribbling":
            # Dribbling: Focus on Close Control (High Priority)
            close_control_score = self._analyze_close_control_dribbling(pose_data, metrics, feedback)
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            overall_score = np.mean([close_control_score, balance_score])
        elif self.movement_type == "first_touch":
            # First Touch: Focus on Soft Cushioning (High Priority)
            soft_touch_score = self._analyze_soft_touch_first_touch(pose_data, metrics, feedback)
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            overall_score = np.mean([soft_touch_score, balance_score])
        else:
            # Default: General soccer analysis
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            overall_score = balance_score

        for metric in metrics:
            if metric.score >= 80:
                strengths.append(f"{metric.name}: {metric.score:.1f}/100")
            elif metric.score < 60:
                weaknesses.append(f"{metric.name}: {metric.score:.1f}/100")

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
            feedback.append(self.create_feedback("info", "Excellent forward lean — chest over ball.", "lean_forward"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "critical",
                "lean_forward",
                "When shooting, you often lean back and strike the ball with your toe, causing your shots to sail high or lack power and accuracy.",
                "Proper shooting technique uses your body weight and the right part of your foot. Leaning forward (chest over the ball) keeps the shot low and controlled, and striking with your laces (the instep) gives a large, solid surface for power and accuracy. If you lean back, the ball will typically fly high. If you toe-poke, you lose control over direction and power. Fixing these fundamentals will result in harder, more reliable shots on target.",
                [
                    "Plant your non-kicking foot about even with or slightly ahead of the ball, a few inches to the side. This position naturally forces your chest and shoulders over the ball",
                    "Keep your head down, eyes on the ball through the kick",
                    "Lock your ankle on your kicking foot (toes pointed downward) and strike the center of the ball with the laces (the top of your foot)",
                    "Follow through with your kicking leg. After contact, your foot should continue toward the target and you can take an extra step or two forward"
                ],
                "Laces shooting drill: Set up a ball and take multiple shots from the top of the penalty box or a comfortable distance. For each shot, say out loud \"chest over, lock ankle\" as you shoot (it sounds silly, but it reinforces technique). Emphasize leaning into the shot and hitting with shoelaces. Aim low. Complete several sets, alternating feet if you can, to build good habits.",
                "Chest over ball"
            ))
        else:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "lean_forward",
                "Your forward lean can be improved for better shooting technique.",
                "Leaning forward keeps the shot low and controlled, while striking with your laces gives power and accuracy.",
                [
                    "Plant your non-kicking foot even with or slightly ahead of the ball",
                    "Keep your chest and shoulders over the ball",
                    "Lock your ankle and strike with your laces, not your toe"
                ],
                "Laces shooting drill: Take multiple shots saying \"chest over, lock ankle\" as you shoot. Focus on leaning into the shot. Complete several sets.",
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
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent follow-through toward target.", "follow_through"))
        else:
            feedback.append(self.create_feedback(
                "warning",
                "Shooting: Follow through with your kicking leg. After contact, your foot should continue toward the target.",
                "follow_through"
            ))
        
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
            feedback.append(self.create_feedback("info", "Excellent ankle lock — firm foot at impact.", "ankle_stability"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "critical",
                "ankle_stability",
                "Some of your passes lack power or accuracy because your foot is not firm at impact (ankle is loose) and you sometimes stop your leg instead of following through toward the target.",
                "For a pass to be accurate and well-paced, you need a stable foot (locked ankle) and a full follow-through. A floppy foot will absorb energy and send the ball unpredictably. Stopping your kick too soon means you're not transferring all your energy to the ball, making passes weak and easier to intercept. Proper technique will give your passes a straight trajectory and enough speed to reach your teammate.",
                [
                    "Lock your ankle by pointing your toe up and pulling it toward your shin for an inside-of-foot pass (this makes your foot firm). Use the inside of your foot for short to medium passes",
                    "Swing through the ball. Don't stab at it. After contacting the ball, let your kicking leg continue its motion naturally in the direction of your target",
                    "Keep your eyes on the ball at the moment of impact and your body balanced. Lean your body slightly over the ball and step through the pass with your plant foot following the direction of the ball"
                ],
                "Wall passing drill: Stand a comfortable distance from a wall. Pass the ball against the wall with your right foot and trap the rebound with your left, then vice versa. Focus on each pass being firm (you should hear a nice pop from the wall) and accurate. Key points: locked ankle, and a smooth follow-through each time. Complete multiple passes with each foot for several rounds.",
                "Lock and follow"
            ))
        else:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "ankle_stability",
                "Your ankle stability can be improved for more accurate and powerful passes.",
                "A locked ankle creates a firm foot surface for accurate and well-paced passes.",
                [
                    "Lock your ankle by pointing your toe up and pulling it toward your shin",
                    "Use the inside of your foot for passing",
                    "Swing through the ball, don't stab at it"
                ],
                "Wall passing drill: Stand a comfortable distance from a wall. Pass and trap, alternating feet. Focus on locked ankle and smooth follow-through. Complete multiple passes with each foot for several rounds.",
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
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent follow-through — smooth motion toward target.", "follow_through"))
        else:
            feedback.append(self.create_feedback(
                "warning",
                "Passing: Follow through toward your target. After contacting the ball, let your kicking leg continue its motion naturally.",
                "follow_through"
            ))
        
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
            feedback.append(self.create_feedback("info", "Excellent body angle — proper angled approach for crossing.", "body_angle"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "critical",
                "body_angle",
                "Your crosses often lack curve or height — they tend to go flat or off-target because you approach the ball straight on and hit it too directly, rather than wrapping your foot around the ball.",
                "A good cross usually has a bit of bend and appropriate loft to drop into the dangerous area. Approaching at an angle and using the instep/inside to wrap around the ball creates that curling trajectory. If you run straight at the ball and kick it like a shot, it'll either go straight (often right to the goalkeeper or out) or not get over the defenders. Proper crossing technique increases the chances your teammates can get to the ball.",
                [
                    "Approach the ball at an angle (roughly 30-45 degrees to your target line). This positioning opens up your hips, allowing your leg to swing across your body",
                    "Plant your non-kicking foot slightly behind and to the side of the ball. As you swing your kicking leg, strike the ball with the instep/inside of your foot, slightly off-center (the side of the ball farthest from the goal)",
                    "Follow through across your body. Your kicking foot should wrap around the ball and continue in the direction of the cross (like you're swinging from outside to inside)"
                ],
                "Crossing to target drill: Set up a flag or cone in the penalty area as a target (for example, around the penalty spot or far post area). From the right wing, practice hitting crosses aiming to curl the ball toward that target (for a right-footer, it should bend leftward in the air). Focus on your angled run-up and wrapping your foot. Do 10 crosses from the right, then 10 from the left wing (where a left foot or different angle is needed). Quality over power.",
                "Around the ball"
            ))
        else:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "body_angle",
                "Your body angle can be improved for better crossing technique.",
                "Approaching at an angle allows your leg to swing across your body and wrap around the ball for a curling cross.",
                [
                    "Approach the ball at an angle (roughly 30-45 degrees to your target line)",
                    "Open up your hips to allow your leg to swing across your body",
                    "Strike the ball with the instep/inside of your foot, slightly off-center"
                ],
                "Crossing to target drill: Set up a target in the penalty area. Practice hitting crosses from the wing, focusing on angled run-up and wrapping your foot. Do 10 crosses from each wing.",
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
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent wrap-around follow-through.", "follow_through"))
        else:
            feedback.append(self.create_feedback(
                "warning",
                "Crossing: Follow through across your body. Your kicking foot should wrap around the ball and continue in the direction of the cross.",
                "follow_through"
            ))
        
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
            feedback.append(self.create_feedback("info", "Excellent close control — ball staying close to feet.", "close_control"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "critical",
                "close_control",
                "When dribbling at speed, the ball sometimes gets too far away from you, and you favor using only your dominant foot. This makes it easier for defenders to dispossess you because they can predict your moves or poke the ball away during a heavy touch.",
                "Close control keeps the ball within reach so you can react to defenders and change direction quickly. Using both feet and all parts of your feet (inside, outside, sole) makes you less predictable and more versatile on the ball. If you only use one foot or take big touches, opponents will have an easier time stealing the ball or forcing you into a mistake. Improving close control will make you a more confident and elusive dribbler.",
                [
                    "Take smaller touches. Instead of kicking the ball far ahead on each stride, tap it gently so it stays close in front of you",
                    "Use both feet. Practice dribbling patterns where you alternate touches between your left and right foot. Also use different parts of your foot: the instep for pushing forward, the outside of the foot for lateral moves, and the sole to pull the ball back or stop quickly",
                    "Keep your knees bent and stay on your toes. This athletic position lets you change direction quickly. And keep your head up as much as you can"
                ],
                "Cone weave: Set up several cones or markers spaced apart in a zigzag or straight line. Dribble through them, weaving around each cone. Focus on using many small touches (at least one touch per step). Do this drill with your right foot only, then left foot only, then alternating both feet. Repeat each variation multiple times. As you improve, try to go faster without losing control or hitting the cones.",
                "Small touches"
            ))
        else:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "close_control",
                "Your close control can be improved for better dribbling.",
                "Close control keeps the ball within reach so you can react to defenders and change direction quickly.",
                [
                    "Take smaller touches — tap the ball gently so it stays close in front of you",
                    "Use both feet and different parts of your foot",
                    "Keep your knees bent and stay on your toes"
                ],
                "Cone weave: Set up several cones and dribble through them with many small touches. Do this with your right foot only, then left foot only, then alternating both feet. Repeat each variation multiple times.",
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
            feedback.append(self.create_feedback("info", "Excellent soft touch — controlled first touch.", "soft_touch"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "critical",
                "soft_touch",
                "Your first touch on the ball is sometimes heavy — the ball tends to bounce or roll too far away from you, making it hard to control or giving opponents a chance to intervene.",
                "A soft, controlled first touch is critical in soccer. It allows you to keep possession and choose your next move (pass, shot, dribble) without scrambling. If the ball ricochets off your foot or body, you lose that advantage. Cushioning the ball (like catching an egg) will set you up for smoother play. It also helps in tight spaces, as a good first touch can evade a pressing defender.",
                [
                    "Relax the part of your body receiving the ball. If it's your foot, keep your ankle firm but not rigid, and as the ball hits, slightly withdraw your foot in the same direction the ball is coming from (this \"gives\" with the ball's momentum)",
                    "Decide your direction on the first touch. Rather than stopping the ball dead every time, often you want to direct it into space or away from a defender",
                    "Be on your toes and watch the ball in. Anticipate the ball's speed and trajectory as it comes to you. Move your feet early so you meet the ball in a good position"
                ],
                "Wall control drill: Stand a comfortable distance from a wall. Pass the ball against the wall and practice controlling the rebound with one touch. Alternate between trapping it dead at your feet, or taking a prep touch to the side as if preparing to shoot or pass. Use both feet (and thighs/chest for higher bounces if you want). Complete several sets with multiple receptions per foot. Focus on softening the impact and keeping the ball close.",
                "Soft touch"
            ))
        else:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "soft_touch",
                "Your first touch can be improved for better ball control.",
                "A soft, controlled first touch allows you to keep possession and choose your next move.",
                [
                    "Relax the part of your body receiving the ball — slightly withdraw to \"give\" with the ball's momentum",
                    "Decide your direction on the first touch",
                    "Be on your toes and watch the ball in — anticipate its speed and trajectory"
                ],
                "Wall control drill: Stand a comfortable distance from a wall. Pass against the wall and practice controlling the rebound with one touch. Complete several sets with multiple receptions per foot, focusing on softening the impact.",
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

