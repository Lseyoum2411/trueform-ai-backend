from typing import List, Dict
from datetime import datetime
import numpy as np
import uuid
from app.core.analyzers.base import BaseAnalyzer
from app.models.analysis import AnalysisResult, MetricScore, FeedbackItem


class VolleyballAnalyzer(BaseAnalyzer):
    def __init__(self, movement_type: str = "spike_approach"):
        super().__init__()
        self.movement_type = movement_type.lower()
        if self.movement_type not in ["spike_approach", "jump_serve", "blocking_jump"]:
            self.movement_type = "spike_approach"

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
        if self.movement_type == "spike_approach":
            # Spike Approach: Focus on Timing and Arm Swing (High Priority)
            jump_timing_score = self._analyze_jump_timing_spike(landmarks_list, metrics, feedback)
            arm_swing_score = self._analyze_arm_swing_spike(landmarks_list, angles_list, metrics, feedback)
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            metric_scores = [m.score for m in metrics]
            critical_metric_names = ["jump_timing", "arm_swing"]
            critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=critical_indices, max_critical_failures=2, max_moderate_failures=3)
        elif self.movement_type == "jump_serve":
            # Jump Serve: Focus on Consistent Toss (High Priority)
            toss_consistency_score = self._analyze_toss_consistency_serve(landmarks_list, metrics, feedback)
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            metric_scores = [m.score for m in metrics]
            critical_metric_names = ["toss_consistency"]
            critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=critical_indices, max_critical_failures=2, max_moderate_failures=3)
        elif self.movement_type == "blocking_jump":
            # Blocking Jump: Focus on Timing and Penetration (High Priority)
            block_timing_score = self._analyze_block_timing(landmarks_list, metrics, feedback)
            penetration_score = self._analyze_penetration_block(landmarks_list, metrics, feedback)
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            metric_scores = [m.score for m in metrics]
            critical_metric_names = ["block_timing", "penetration"]
            critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=critical_indices, max_critical_failures=2, max_moderate_failures=3)
        else:
            # Default: General volleyball analysis
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            metric_scores = [m.score for m in metrics] if metrics else [balance_score]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=[], max_critical_failures=2, max_moderate_failures=3) if metrics else balance_score

        for metric in metrics:
            if metric.score >= 80:
                strengths.append(self.get_qualitative_strength_description(metric.name))
            elif metric.score < 60:
                weaknesses.append(self.get_qualitative_weakness_description(metric.name))

        # Consolidate duplicate weight transfer feedback (remove duplicate weight transfer items)
        feedback = self.consolidate_weight_transfer_feedback(feedback)

        return AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            video_id="",
            sport="volleyball",
            exercise_type=self.movement_type,
            overall_score=round(overall_score, 2),
            metrics=metrics,
            feedback=feedback,
            strengths=strengths,
            weaknesses=weaknesses,
            raw_data={"frame_count": len(pose_data), "movement_type": self.movement_type},
            created_at=datetime.now(),
        )

    def _analyze_jump_timing_spike(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Spike approach specific: Analyze jump timing - should contact at peak of reach."""
        if not landmarks_list or len(landmarks_list) < 10:
            return 50.0
        
        # Analyze jump height pattern - peak should occur around contact point
        # For good timing, we want peak jump to align with contact (later in sequence)
        wrist_heights = []
        for landmarks in landmarks_list:
            if "right_wrist" in landmarks:
                wrist_heights.append(landmarks["right_wrist"][1])  # Lower Y = higher
        
        if len(wrist_heights) < 10:
            return 50.0
        
        # Find peak jump position (lowest Y value = highest point)
        peak_idx = np.argmin(wrist_heights)
        total_frames = len(wrist_heights)
        
        # Ideal: peak occurs in last 40% of movement (contact at peak)
        ideal_peak_position = 0.6  # 60% through movement
        actual_peak_position = peak_idx / total_frames
        
        # Score based on how close peak is to ideal position
        timing_deviation = abs(actual_peak_position - ideal_peak_position)
        if timing_deviation <= 0.1:
            score = 100.0
        elif timing_deviation <= 0.2:
            score = 85.0
        elif timing_deviation <= 0.3:
            score = 70.0
        else:
            score = max(0, 100 - (timing_deviation - 0.3) * 100)
        
        score = min(100, max(0, score))
        metric = self.create_metric("jump_timing", score, value=round(actual_peak_position, 2))
        metrics.append(metric)
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent jump timing — contacting ball at peak reach.", "jump_timing"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "critical",
                "jump_timing",
                "Your spiking approach is often mistimed — sometimes you jump too early or too late relative to the set — and you're not using a full arm swing. As a result, you're hitting the ball on the way down or without much power.",
                "Timing your jump to contact the ball at the peak of your reach is critical for a powerful spike. If you're on the way down, you've lost height and hitting power. Additionally, a full arm swing (drawing your arm back and swinging through fast with a wrist snap) generates speed on the ball. Mistiming plus a half-hearted arm swing leads to easy, less forceful hits that opponents can dig or block. Improving these will make your spikes more explosive and effective.",
                [
                    "Watch the set carefully and adjust your approach speed. If the ball is set high, you may need to wait a split second longer before you start your approach. If it's low or quick, you go faster",
                    "Use a consistent approach with multiple steps (commonly for right-handers: left, right-left). The last two steps should be quick and explosive — think \"big last step, then jump\"",
                    "As you plant those last two steps, swing your arms back, then swing them up explosively to help your lift",
                    "Draw your hitting arm back during your jump (elbow high and behind, like pulling a bow and arrow). Then swing through fast and snap your wrist on contact"
                ],
                "Self-toss spike practice: Toss a ball to yourself (or have a partner toss) and practice your approach and jump timing. Focus on jumping so that you contact the ball at your highest point. Repeat this multiple times: toss, approach, jump, spike. Each time, adjust if you were early or late. Additionally, practice with a partner setting: have them set the ball multiple times, and you concentrate on matching your jump to the set. Over time, you'll internalize the right timing.",
                "Jump on time, reach high"
            ))
        else:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "jump_timing",
                "Your jump timing can be improved for more powerful spikes.",
                "Timing your jump to contact the ball at the peak of your reach is critical for power.",
                [
                    "Watch the set carefully and adjust your approach speed",
                    "Use a consistent approach with quick, explosive last two steps",
                    "Swing your arms up explosively to help your lift"
                ],
                "Self-toss spike practice: Toss a ball to yourself and practice your approach and jump timing. Focus on contacting the ball at your highest point. Repeat multiple times, adjusting if you were early or late.",
                "Jump on time, reach high"
            ))
        
        return score
    
    def _analyze_arm_swing_spike(self, landmarks_list: List[Dict], angles_list: List[Dict], metrics: List, feedback: List) -> float:
        """Spike approach specific: Analyze full arm swing - arm should draw back then swing through."""
        if not landmarks_list or not angles_list:
            return 50.0
        
        # Analyze arm extension range - should show full swing motion
        elbow_angles = []
        for angles in angles_list:
            if "right_elbow" in angles:
                elbow_angles.append(angles["right_elbow"])
        
        if len(elbow_angles) < 5:
            return 50.0
        
        # Check for full range of motion (arm draws back then extends)
        min_elbow = min(elbow_angles)  # Most bent (drawn back)
        max_elbow = max(elbow_angles)  # Most extended (swing through)
        range_of_motion = max_elbow - min_elbow
        
        # Ideal: large range (80+ degrees) indicates full swing
        if range_of_motion >= 80:
            score = 100.0
        elif range_of_motion >= 60:
            score = 85.0
        elif range_of_motion >= 40:
            score = 70.0
        else:
            score = max(0, (range_of_motion / 40) * 70.0)
        
        score = min(100, max(0, score))
        metric = self.create_metric("arm_swing", score, value=round(range_of_motion, 1), unit="degrees")
        metrics.append(metric)
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent arm swing — full range of motion.", "arm_swing"))
        else:
            feedback.append(self.create_feedback(
                "warning",
                "Spike: Draw your hitting arm back during your jump (elbow high and behind) then swing through fast and snap your wrist on contact. Make sure you reach high — fully extend your arm when you hit.",
                "arm_swing"
            ))
        
        return score
    
    def _analyze_toss_consistency_serve(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Jump serve specific: Analyze toss consistency - should be in same position."""
        if not landmarks_list or len(landmarks_list) < 5:
            return 50.0
        
        # For jump serve, we analyze consistency by looking at hand/wrist positions during toss phase
        # Early frames should show toss motion (hand moving upward)
        toss_frames = landmarks_list[:len(landmarks_list) // 2]
        
        wrist_positions = []
        for landmarks in toss_frames:
            if "right_wrist" in landmarks:
                wrist_positions.append((landmarks["right_wrist"][0], landmarks["right_wrist"][1]))
        
        if len(wrist_positions) < 3:
            return 50.0
        
        # Analyze upward motion (should be consistent for good toss)
        # Look at vertical motion consistency
        vertical_velocities = []
        for i in range(1, len(wrist_positions)):
            vertical_velocity = wrist_positions[i-1][1] - wrist_positions[i][1]  # Negative = upward
            if vertical_velocity > 0:  # Only count upward motion
                vertical_velocities.append(vertical_velocity)
        
        if not vertical_velocities:
            return 50.0
        
        # Low variance in toss motion = consistent (good)
        velocity_variance = np.var(vertical_velocities)
        if velocity_variance <= 0.0001:
            score = 100.0
        elif velocity_variance <= 0.0005:
            score = 85.0
        elif velocity_variance <= 0.001:
            score = 70.0
        else:
            score = max(0, 100 - (velocity_variance - 0.001) * 50000)
        
        score = min(100, max(0, score))
        metric = self.create_metric("toss_consistency", score, value=round(velocity_variance, 6))
        metrics.append(metric)
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent toss consistency — consistent toss position.", "toss_consistency"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "critical",
                "toss_consistency",
                "Your jump serve's biggest issue is an inconsistent toss. Sometimes the ball is too far in front, other times too far behind or off to the side, making it hard for you to jump and hit it solidly. This leads to missed or weak serves.",
                "The toss is the foundation of a good jump serve. A consistent toss (same spot, same height every time) allows you to approach and contact the ball in the optimal hitting zone. If your toss is erratic, even a great approach and swing can't save the serve. Getting the toss right will dramatically improve your serve accuracy and power, because you can hit the ball at full extension and in front of you rather than reaching or adjusting awkwardly.",
                [
                    "Practice the toss separately. Stand and toss the ball with your hitting hand (if you're right-handed, toss with right hand) high and slightly forward",
                    "Aim for a toss that will peak a few feet above your extended hitting reach and about a step or two in front of you. It should also be in line with your hitting shoulder",
                    "Use a consistent motion: Don't toss with a big throw; it's more of a controlled lift. Keep your tossing arm relatively straight and lift the ball up with your palm/fingers guiding it",
                    "Approach after the toss: As soon as the ball leaves your hand, take your approach (usually a 3-step: for right-handers, left-right-left). The goal is to jump and meet the ball at full arm extension"
                ],
                "Toss-and-catch drill: Stand at your serving position and toss the ball as if you're going to jump serve, but instead of hitting it, just jump and catch it at what would be your contact point. If you can catch it comfortably with your arm fully extended, your toss was good. If you have to reach forward or it's off to the side, adjust and try again. Repeat multiple tosses (and jumps) aiming for perfect placement. Once you have a feel for that, do a series of actual jump serves focusing on replicating that same toss every time.",
                "High and forward"
            ))
        else:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "toss_consistency",
                "Your toss consistency can be improved for better jump serves.",
                "A consistent toss allows you to approach and contact the ball in the optimal hitting zone.",
                [
                    "Practice the toss separately — toss high and slightly forward",
                    "Use a controlled lift motion, not a big throw",
                    "Aim for the same spot every time — a few feet above your extended reach and a step or two in front"
                ],
                "Toss-and-catch drill: Toss the ball and jump to catch it at your contact point. If you can catch it comfortably with your arm fully extended, your toss was good. Repeat multiple tosses aiming for perfect placement.",
                "High and forward"
            ))
        
        return score
    
    def _analyze_block_timing(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Blocking jump specific: Analyze timing - should jump when hitter jumps."""
        if not landmarks_list or len(landmarks_list) < 10:
            return 50.0
        
        # Analyze jump timing pattern - similar to spike, but focus on explosive upward motion
        wrist_heights = []
        for landmarks in landmarks_list:
            if "left_wrist" in landmarks:
                wrist_heights.append(landmarks["left_wrist"][1])
            elif "right_wrist" in landmarks:
                wrist_heights.append(landmarks["right_wrist"][1])
        
        if len(wrist_heights) < 10:
            return 50.0
        
        # Find peak jump (should occur at right time relative to "hitter's" motion)
        # For blocking, we want quick, explosive jump
        peak_idx = np.argmin(wrist_heights)
        total_frames = len(wrist_heights)
        
        # Block jump should peak relatively early (around 40-50% through) for timing with hitter
        ideal_peak_position = 0.45
        actual_peak_position = peak_idx / total_frames
        
        timing_deviation = abs(actual_peak_position - ideal_peak_position)
        if timing_deviation <= 0.1:
            score = 100.0
        elif timing_deviation <= 0.2:
            score = 85.0
        elif timing_deviation <= 0.3:
            score = 70.0
        else:
            score = max(0, 100 - (timing_deviation - 0.3) * 100)
        
        score = min(100, max(0, score))
        metric = self.create_metric("block_timing", score, value=round(actual_peak_position, 2))
        metrics.append(metric)
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent block timing — jumping at right moment.", "block_timing"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "critical",
                "block_timing",
                "When blocking at the net, you're often either early or late on your jump, and you sometimes jump straight up with your hands not reaching over the net. This results in missed blocks or the ball tooling off your hands out of bounds.",
                "A successful block requires jumping at the right moment (so your hands meet the ball as the hitter spikes) and penetrating over the net (reaching your hands across to seal off the space). If you mistime, you're basically blocking air or coming down as the ball comes over. If you don't penetrate, the hitter can hit off your hands and the ball will fall on your side or out off your block. Correct timing plus getting over the net will significantly increase your block touches and stuffs.",
                [
                    "Watch the hitter's approach and arm swing closely. The best cue to jump is when the hitter is about to jump or is just taking off",
                    "As a general rule, you jump when they jump (for quick sets, you may need to go up slightly before). This way, your hands are up as they swing",
                    "As you jump, reach your arms straight up and then over the net. Don't swat at the ball, just form a solid wall",
                    "Penetrating means your hands are on the opponent's side of the net (without touching the net) at peak jump. This cuts off the angle"
                ],
                "Shadow blocking: With no ball, have a partner stand as a \"hitter\" on the other side of the net. They should do a mock spike motion. Practice timing your jump with their arm swing — they swing, you jump to block. Focus on penetrating your arms over the net on each rep. Repeat multiple times. Then move to live hitting: have a partner or coach hit balls while you attempt to block. Start with easier, high sets to get the timing, then progress to game-like sets. Each time, concentrate on the point of contact — your goal is to meet the ball squarely with firm hands over the net.",
                "Jump with hitter"
            ))
        else:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "block_timing",
                "Your block timing can be improved for more effective blocks.",
                "Jumping at the right moment ensures your hands meet the ball as the hitter spikes.",
                [
                    "Watch the hitter's approach and arm swing closely",
                    "Jump when they jump (for quick sets, go up slightly before)",
                    "Reach your arms straight up and then over the net"
                ],
                "Shadow blocking: Have a partner do a mock spike motion. Practice timing your jump with their arm swing. Focus on penetrating your arms over the net. Repeat multiple times.",
                "Jump with hitter"
            ))
        
        return score
    
    def _analyze_penetration_block(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Blocking jump specific: Analyze penetration - hands should reach over net."""
        if not landmarks_list:
            return 50.0
        
        # Analyze arm extension - wrists should be high (hands reaching over net)
        peak_frames = landmarks_list[len(landmarks_list) // 2:]
        wrist_heights = []
        
        for landmarks in peak_frames:
            if "left_wrist" in landmarks:
                wrist_heights.append(landmarks["left_wrist"][1])
            elif "right_wrist" in landmarks:
                wrist_heights.append(landmarks["right_wrist"][1])
        
        if not wrist_heights:
            return 50.0
        
        # Check if wrists are high (low Y values) relative to shoulders
        avg_wrist_height = np.mean(wrist_heights)
        
        # For penetration, we want wrists significantly above shoulders
        # Use reference height (shoulders) - wrists should be much lower (higher up)
        shoulder_heights = []
        for landmarks in peak_frames:
            if "left_shoulder" in landmarks:
                shoulder_heights.append(landmarks["left_shoulder"][1])
        
        if shoulder_heights:
            avg_shoulder_height = np.mean(shoulder_heights)
            extension = avg_shoulder_height - avg_wrist_height  # Positive = wrists above shoulders
            
            # Ideal: wrists well above shoulders (0.15+)
            if extension >= 0.15:
                score = 100.0
            elif extension >= 0.10:
                score = 85.0
            elif extension >= 0.05:
                score = 70.0
            else:
                score = max(0, (extension / 0.05) * 70.0)
        else:
            score = 50.0
        
        score = min(100, max(0, score))
        metric = self.create_metric("penetration", score, value=round(score, 1))
        metrics.append(metric)
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent penetration — hands reaching over net.", "penetration"))
        else:
            feedback.append(self.create_feedback(
                "warning",
                "Blocking: Penetrate over the net. Reach your arms straight up and then over the net — your hands should be on the opponent's side at peak jump. Spread your fingers wide and keep your hands strong to create a big blocking surface.",
                "penetration"
            ))
        
        return score
    
    def _analyze_balance(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """General balance analysis for volleyball movements."""
        if not landmarks_list:
            return 50.0
        
        balance_scores = []
        for landmarks in landmarks_list:
            if all(k in landmarks for k in ["left_ankle", "right_ankle", "left_hip", "right_hip"]):
                ankle_center_x = (landmarks["left_ankle"][0] + landmarks["right_ankle"][0]) / 2
                hip_center_x = (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2
                
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
            sport="volleyball",
            exercise_type=self.movement_type,
            overall_score=0.0,
            metrics=[],
            feedback=[],
            strengths=[],
            weaknesses=[],
            raw_data={},
            created_at=datetime.now(),
        )

