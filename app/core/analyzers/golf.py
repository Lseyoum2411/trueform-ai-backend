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
        if self.shot_type not in ["driver", "iron", "chip", "putt"]:
            logger.warning(f"Unknown shot_type '{shot_type}', defaulting to 'driver'")
            self.shot_type = "driver"
        
        # Shot-specific biomechanical parameters
        if self.shot_type == "driver":
            # Initialize driver-specific parameters but won't use them in new implementation
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
        
        # Exercise-specific analysis with different priorities
        if self.shot_type == "driver":
            # Driver: Focus on Inside-Out Swing Path (High Priority)
            swing_path_score = self._analyze_swing_path_driver(landmarks_list, angles_list, metrics, feedback)
            weight_transfer_score = self._analyze_weight_transfer_driver(landmarks_list, metrics, feedback)
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            tempo_score = self._analyze_tempo(pose_data, metrics, feedback)
            follow_through_score = self._analyze_follow_through(landmarks_list, angles_list, metrics, feedback)
            stance_width_score = self._analyze_stance_width(landmarks_list, metrics, feedback)
            spine_tilt_score = self._analyze_spine_tilt(landmarks_list, metrics, feedback)
            metric_scores = [m.score for m in metrics]
            if not metric_scores:
                logger.warning(f"Golf/{self.shot_type}: No component scores calculated, using fallback")
            critical_metric_names = ["swing_path"]
            critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=critical_indices, max_critical_failures=2, max_moderate_failures=3)
        elif self.shot_type == "iron":
            # Iron: Focus on Ball-First Contact (High Priority)
            ball_contact_score = self._analyze_ball_contact_iron(landmarks_list, angles_list, metrics, feedback)
            weight_transfer_score = self._analyze_weight_transfer_iron(landmarks_list, metrics, feedback)
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            tempo_score = self._analyze_tempo(pose_data, metrics, feedback)
            follow_through_score = self._analyze_follow_through(landmarks_list, angles_list, metrics, feedback)
            stance_width_score = self._analyze_stance_width(landmarks_list, metrics, feedback)
            spine_tilt_score = self._analyze_spine_tilt(landmarks_list, metrics, feedback)
            metric_scores = [m.score for m in metrics]
            if not metric_scores:
                logger.warning(f"Golf/{self.shot_type}: No component scores calculated, using fallback")
            critical_metric_names = ["ball_contact"]
            critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=critical_indices, max_critical_failures=2, max_moderate_failures=3)
        elif self.shot_type == "chip":
            # Chip: Focus on Weight Forward, No Flip (High Priority)
            weight_forward_score = self._analyze_weight_forward_chip(landmarks_list, metrics, feedback)
            wrist_stability_score = self._analyze_wrist_stability_chip(angles_list, metrics, feedback)
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            tempo_score = self._analyze_tempo(pose_data, metrics, feedback)
            metric_scores = [m.score for m in metrics]
            if not metric_scores:
                logger.warning(f"Golf/{self.shot_type}: No component scores calculated, using fallback")
            critical_metric_names = ["weight_forward"]
            critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=critical_indices, max_critical_failures=2, max_moderate_failures=3)
        elif self.shot_type == "putt":
            # Putt: Focus on Steady Shoulders (High Priority)
            shoulder_stability_score = self._analyze_shoulder_stability_putt(landmarks_list, angles_list, metrics, feedback)
            wrist_stability_score = self._analyze_wrist_stability_putt(angles_list, metrics, feedback)
            head_stability_score = self._analyze_head_stability_putt(landmarks_list, metrics, feedback)
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            metric_scores = [m.score for m in metrics]
            if not metric_scores:
                logger.warning(f"Golf/{self.shot_type}: No component scores calculated, using fallback")
            critical_metric_names = ["shoulder_stability"]
            critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=critical_indices, max_critical_failures=2, max_moderate_failures=3)
        else:
            # Default: General golf analysis
            stance_width_score = self._analyze_stance_width(landmarks_list, metrics, feedback)
            spine_tilt_score = self._analyze_spine_tilt(landmarks_list, metrics, feedback)
            backswing_rotation_score = self._analyze_backswing_rotation(angles_list, landmarks_list, metrics, feedback)
            weight_transfer_score = self._analyze_weight_transfer(landmarks_list, metrics, feedback)
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            tempo_score = self._analyze_tempo(pose_data, metrics, feedback)
            follow_through_score = self._analyze_follow_through(landmarks_list, angles_list, metrics, feedback)
            metric_scores = [m.score for m in metrics]
            if not metric_scores:
                logger.warning(f"Golf/{self.shot_type}: No component scores calculated, using fallback")
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=[], max_critical_failures=2, max_moderate_failures=3)
        
        # Categorize strengths and weaknesses (NO numeric values)
        for metric in metrics:
            if metric.score >= 80:
                strengths.append(self.get_qualitative_strength_description(metric.name))
            elif metric.score < 60:
                weaknesses.append(self.get_qualitative_weakness_description(metric.name))
        
        # Consolidate duplicate weight transfer feedback (remove duplicate weight transfer items)
        feedback = self.consolidate_weight_transfer_feedback(feedback)
        
        # Remove any remaining duplicate feedback items by metric name
        feedback = self.deduplicate_feedback_by_metric(feedback)
        
        # Ensure overall_score is never 0 for valid analysis
        if overall_score <= 0:
            logger.warning(f"Golf/{self.shot_type}: Overall score is {overall_score}, using fallback")
            overall_score = self.finalize_score([], fallback=70)
        
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
    
    def _analyze_swing_path_driver(self, landmarks_list: List[Dict], angles_list: List[Dict], metrics: List, feedback: List) -> float:
        """Driver specific: Analyze inside-out swing path to prevent over-the-top motion."""
        if not landmarks_list or len(landmarks_list) < 10:
            return 50.0
        
        # Analyze downswing path by looking at elbow position relative to body
        # For inside-out path, trail elbow (right for right-handers) should tuck in
        downswing_frames = landmarks_list[len(landmarks_list) // 2:]
        elbow_positions = []
        
        for landmarks in downswing_frames:
            if all(k in landmarks for k in ["right_elbow", "right_hip", "right_shoulder"]):
                elbow_x = landmarks["right_elbow"][0]
                hip_x = landmarks["right_hip"][0]
                shoulder_x = landmarks["right_shoulder"][0]
                
                # Inside-out path: elbow should be closer to body (tucked)
                body_center = (shoulder_x + hip_x) / 2
                elbow_offset = abs(elbow_x - body_center)
                elbow_positions.append(elbow_offset)
        
        if not elbow_positions:
            return 50.0
        
        avg_elbow_offset = np.mean(elbow_positions)
        ideal_offset = 0.08  # Elbow should be close to body center
        deviation = abs(avg_elbow_offset - ideal_offset)
        
        if deviation <= 0.03:
            score = 100.0
        else:
            score = max(0, 100 - (deviation / 0.03) * 40)
        
        score = min(100, max(0, score))
        metrics.append(self.create_metric("swing_path", score, value=round(avg_elbow_offset, 3)))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent inside-out swing path — club approaching from inside.", "swing_path"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "critical",
                "swing_path",
                "Your driver swing is coming \"over the top\" with an outside-to-inside path. This often results in a slice (ball curving right for a right-handed golfer) and a loss of distance.",
                "An outside-in swing path puts side-spin on the ball, causing it to curve and not travel as far. It also means you're likely not hitting the ball with the clubface square. A more inside-out swing path helps you make solid, centered contact with less side-spin, leading to straighter, longer drives. Basically, correcting your swing path will tame that slice and add yards.",
                [
                    "Start your downswing by dropping your hands toward your trail hip (right hip for right-handers) instead of casting them out away from your body",
                    "Feel like your back elbow is tucking into your side to shallow the club's path",
                    "Feel like you are swinging out toward right field (for a right-hander) or \"down the line\" through the ball",
                    "Ensure you're shifting your weight onto your front foot as you swing. Begin the downswing by moving your left hip (for right-handers) toward the target and turning"
                ],
                "Headcover drill: Place a headcover or a small object just outside the target line a few inches behind the ball (toward where an outside-in path would come from). Practice swinging and hitting the ball without contacting the headcover. Start slowly to get the feel, then build to full swings. Do 10 practice swings and then 10 drives with a ball, all focusing on that inside-out motion.",
                "Inside swing"
            ))
        else:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "swing_path",
                "Your swing path can be improved to prevent coming over the top.",
                "An inside-out swing path helps you make solid, centered contact with less side-spin, leading to straighter, longer drives.",
                [
                    "Start your downswing by dropping your hands toward your trail hip instead of casting them out",
                    "Feel like your back elbow is tucking into your side to shallow the club's path",
                    "Shift your weight onto your front foot as you swing"
                ],
                "Headcover drill: Place a headcover just outside the target line behind the ball. Practice swinging without contacting the headcover. Do 10 practice swings focusing on inside-out motion.",
                "Inside swing"
            ))
        
        return score
    
    def _analyze_weight_transfer_driver(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Driver specific: Weight shift to front foot for inside-out path."""
        if not landmarks_list or len(landmarks_list) < 5:
            return 50.0
        
        impact_frames = landmarks_list[len(landmarks_list) // 2:]
        weight_transfers = []
        
        for landmarks in impact_frames:
            if all(k in landmarks for k in ["left_ankle", "right_ankle", "left_hip", "right_hip"]):
                left_ankle_x = landmarks["left_ankle"][0]
                right_ankle_x = landmarks["right_ankle"][0]
                hip_center_x = (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2
                
                ankle_center = (left_ankle_x + right_ankle_x) / 2
                if left_ankle_x < right_ankle_x:  # Left is front foot
                    transfer = max(0, min(1, (ankle_center - hip_center_x) / (ankle_center - left_ankle_x + 0.01)))
                else:
                    transfer = max(0, min(1, (hip_center_x - ankle_center) / (right_ankle_x - ankle_center + 0.01)))
                
                weight_transfers.append(transfer)
        
        if not weight_transfers:
            return 50.0
        
        avg_transfer = np.mean(weight_transfers)
        ideal_transfer = 0.65
        deviation = abs(avg_transfer - ideal_transfer)
        
        if deviation <= 0.15:
            score = 100.0
        else:
            score = max(0, 100 - (deviation / 0.15) * 30)
        
        score = min(100, max(0, score))
        metrics.append(self.create_metric("weight_transfer", score, value=round(avg_transfer, 3), unit="ratio"))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent weight transfer to front foot.", "weight_transfer"))
        elif score < 60:
            feedback.append(self.create_feedback(
                "warning",
                "Driver swing: Increase weight transfer to front foot during downswing. Begin by moving your left hip toward the target.",
                "weight_transfer"
            ))
        
        return score
    
    def _analyze_ball_contact_iron(self, landmarks_list: List[Dict], angles_list: List[Dict], metrics: List, feedback: List) -> float:
        """Iron specific: Analyze ball-first contact - hands ahead of ball, descending blow."""
        if not landmarks_list or len(landmarks_list) < 10:
            return 50.0
        
        impact_frames = landmarks_list[len(landmarks_list) // 2:len(landmarks_list) * 3 // 4]
        forward_lean_scores = []
        
        for landmarks in impact_frames:
            if all(k in landmarks for k in ["left_wrist", "left_elbow", "left_shoulder"]):
                wrist_x = landmarks["left_wrist"][0]
                elbow_x = landmarks["left_elbow"][0]
                shoulder_x = landmarks["left_shoulder"][0]
                
                arm_line = (elbow_x + shoulder_x) / 2
                forward_lean = arm_line - wrist_x
                forward_lean_scores.append(forward_lean)
        
        if not forward_lean_scores:
            return 50.0
        
        avg_forward_lean = np.mean(forward_lean_scores)
        ideal_lean = 0.03
        if avg_forward_lean >= ideal_lean:
            score = 100.0
        elif avg_forward_lean >= 0.01:
            score = 70.0 + (avg_forward_lean / ideal_lean) * 30.0
        else:
            score = max(0, (avg_forward_lean / 0.01) * 70.0)
        
        score = min(100, max(0, score))
        metrics.append(self.create_metric("ball_contact", score, value=round(avg_forward_lean, 3)))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent ball-first contact with hands leading.", "ball_contact"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "critical",
                "ball_contact",
                "You tend to scoop or flip your wrists at impact with your irons, which causes you to hit behind the ball (fat shots) or catch it thin. Your weight stays on your back foot and the clubhead passes your hands too early.",
                "Solid iron shots come from striking the ball first, then the turf with a descending blow. That means your hands lead the clubhead at impact and your weight is on your front foot. If you hang back and flip, you lose compression and distance, and your shots become inconsistent. Correcting this will give you crisper, more accurate iron shots with proper trajectory.",
                [
                    "Shift your weight to your front foot during the downswing. By the time you strike the ball, the majority of your weight should be over your lead leg",
                    "Keep your hands ahead of the ball at impact. Think of your hands passing over the spot where the ball lies a split second before the clubhead does",
                    "Hit down on the ball. A good iron shot feels like you're hitting the ball then taking a divot out in front of where the ball was. Trust the loft of the club to get the ball up; your job is to deliver the club with your hands forward and a descending blow"
                ],
                "Line drill: Draw a chalk line or put a piece of tape on the grass/mat representing where the ball would be. Without a ball, take swings trying to brush the ground in front of the line (on the target side of it). When you can consistently do that, hit balls placed just behind the line, and see that your divot starts at or just past the line. Complete several sets with multiple swings focusing on this contact point.",
                "Hands forward"
            ))
        else:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "ball_contact",
                "Your ball contact can be improved for better iron shots.",
                "Striking the ball first with hands leading creates crisper, more accurate iron shots with proper trajectory.",
                [
                    "Shift your weight to your front foot during the downswing",
                    "Keep your hands ahead of the ball at impact",
                    "Hit down on the ball — feel like you're hitting the ball then taking a divot in front"
                ],
                "Line drill: Put tape on the ground where the ball would be. Practice brushing the ground in front of the line. Complete several sets with multiple swings focusing on contact point.",
                "Hands forward"
            ))
        
        return score
    
    def _analyze_weight_transfer_iron(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Iron specific: Weight forward for ball-first contact."""
        if not landmarks_list or len(landmarks_list) < 5:
            return 50.0
        
        impact_frames = landmarks_list[len(landmarks_list) // 2:]
        weight_transfers = []
        
        for landmarks in impact_frames:
            if all(k in landmarks for k in ["left_ankle", "right_ankle", "left_hip", "right_hip"]):
                left_ankle_x = landmarks["left_ankle"][0]
                right_ankle_x = landmarks["right_ankle"][0]
                hip_center_x = (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2
                
                ankle_center = (left_ankle_x + right_ankle_x) / 2
                if left_ankle_x < right_ankle_x:  # Left is front foot
                    transfer = max(0, min(1, (ankle_center - hip_center_x) / (ankle_center - left_ankle_x + 0.01)))
                else:
                    transfer = max(0, min(1, (hip_center_x - ankle_center) / (right_ankle_x - ankle_center + 0.01)))
                
                weight_transfers.append(transfer)
        
        if not weight_transfers:
            return 50.0
        
        avg_transfer = np.mean(weight_transfers)
        ideal_transfer = 0.55
        deviation = abs(avg_transfer - ideal_transfer)
        
        if deviation <= 0.12:
            score = 100.0
        else:
            score = max(0, 100 - (deviation / 0.12) * 30)
        
        score = min(100, max(0, score))
        metrics.append(self.create_metric("weight_transfer", score, value=round(avg_transfer, 3), unit="ratio"))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent weight transfer to front foot for ball-first contact.", "weight_transfer"))
        elif score < 60:
            feedback.append(self.create_feedback(
                "warning",
                "Iron swing: Shift weight to your front foot during the downswing. By impact, majority of weight should be over your lead leg.",
                "weight_transfer"
            ))
        
        return score
    
    def _analyze_weight_forward_chip(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Chip specific: Analyze weight forward (70% on lead foot)."""
        if not landmarks_list:
            return 50.0
        
        weight_distributions = []
        for landmarks in landmarks_list:
            if all(k in landmarks for k in ["left_ankle", "right_ankle", "left_hip", "right_hip"]):
                left_ankle_x = landmarks["left_ankle"][0]
                right_ankle_x = landmarks["right_ankle"][0]
                hip_center_x = (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2
                
                ankle_center = (left_ankle_x + right_ankle_x) / 2
                if left_ankle_x < right_ankle_x:  # Left is front foot
                    weight_front = max(0, min(1, (ankle_center - hip_center_x) / (ankle_center - left_ankle_x + 0.01)))
                else:
                    weight_front = max(0, min(1, (hip_center_x - ankle_center) / (right_ankle_x - ankle_center + 0.01)))
                
                weight_distributions.append(weight_front)
        
        if not weight_distributions:
            return 50.0
        
        avg_weight_front = np.mean(weight_distributions)
        ideal_weight_front = 0.70  # 70% on front foot
        deviation = abs(avg_weight_front - ideal_weight_front)
        
        if deviation <= 0.10:
            score = 100.0
        else:
            score = max(0, 100 - (deviation / 0.10) * 40)
        
        score = min(100, max(0, score))
        metrics.append(self.create_metric("weight_forward", score, value=round(avg_weight_front, 3), unit="ratio"))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent weight forward positioning for chip shots.", "weight_forward"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "critical",
                "weight_forward",
                "When chipping, you sometimes lean back and try to lift the ball into the air with your wrists. This often results in chunked shots (hitting the turf behind the ball) or skulled shots (hitting the ball too high on the face and sending it flying).",
                "Effective chipping is about consistent contact and letting the club's loft do the work. Keeping your weight forward and wrists firm (no flipping) ensures the club strikes the ball then grass, giving you a controlled trajectory. If you fall back or flip your wrists, the low point of your swing moves and you lose touch, causing those mis-hits. By staying steady over the ball, you improve accuracy and distance control around the greens.",
                [
                    "Set up with most of your weight on your lead foot (left foot for right-handers) and keep it there through the entire chip",
                    "Keep your wrists firm. As you swing the club back and through, think of your arms and shoulders forming a triangle and rocking like a pendulum",
                    "Make sure your hands lead the clubhead slightly at impact. Your hands should be just ahead of the ball when you contact it"
                ],
                "One-foot drill: Try hitting some chip shots while standing with your back foot barely touching the ground (or even slightly lifted onto the toe). This forces your weight onto your front foot. Hit 10 short chips like this—if you lean back, you'll lose balance, so it teaches you to stay forward. Then go back to normal stance and hit another 10 chips, maintaining that weight-forward feeling.",
                "Weight forward"
            ))
        else:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "weight_forward",
                "Your weight positioning can be improved for better chip shots.",
                "Keeping weight forward ensures consistent contact and controlled trajectory.",
                [
                    "Set up with most of your weight on your lead foot and keep it there",
                    "Keep your wrists firm — think of your arms and shoulders rocking like a pendulum",
                    "Make sure your hands lead the clubhead slightly at impact"
                ],
                "One-foot drill: Hit chip shots with your back foot barely touching the ground. Hit 10 chips like this, then 10 with normal stance maintaining weight-forward feeling.",
                "Weight forward"
            ))
        
        return score
    
    def _analyze_wrist_stability_chip(self, angles_list: List[Dict], metrics: List, feedback: List) -> float:
        """Chip specific: Analyze wrist stability (no flipping)."""
        if not angles_list:
            return 50.0
        
        impact_frames = angles_list[len(angles_list) // 2:]
        wrist_changes = []
        
        for i in range(1, len(impact_frames)):
            prev_angles = impact_frames[i-1]
            curr_angles = impact_frames[i]
            
            if "right_elbow" in prev_angles and "right_elbow" in curr_angles:
                angle_change = abs(curr_angles["right_elbow"] - prev_angles["right_elbow"])
                wrist_changes.append(angle_change)
        
        if not wrist_changes:
            return 50.0
        
        avg_wrist_change = np.mean(wrist_changes)
        if avg_wrist_change <= 5:
            score = 100.0
        elif avg_wrist_change <= 10:
            score = 85.0
        elif avg_wrist_change <= 15:
            score = 70.0
        else:
            score = max(0, 100 - (avg_wrist_change - 15) * 3)
        
        score = min(100, max(0, score))
        metrics.append(self.create_metric("wrist_stability", score, value=round(avg_wrist_change, 1), unit="degrees"))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent wrist stability — no flipping during chip.", "wrist_stability"))
        elif score < 60:
            feedback.append(self.create_feedback(
                "warning",
                "Chip shot: Keep your wrists firm throughout the chip. Don't try to scoop the ball — let the club's loft do the work.",
                "wrist_stability"
            ))
        
        return score
    
    def _analyze_shoulder_stability_putt(self, landmarks_list: List[Dict], angles_list: List[Dict], metrics: List, feedback: List) -> float:
        """Putt specific: Analyze steady shoulders (rocking motion, not wristy)."""
        if not landmarks_list or len(landmarks_list) < 5:
            return 50.0
        
        shoulder_heights = []
        for landmarks in landmarks_list:
            if "left_shoulder" in landmarks and "right_shoulder" in landmarks:
                shoulder_y = (landmarks["left_shoulder"][1] + landmarks["right_shoulder"][1]) / 2
                shoulder_heights.append(shoulder_y)
        
        if len(shoulder_heights) < 5:
            return 50.0
        
        velocities = []
        for i in range(1, len(shoulder_heights)):
            velocity = abs(shoulder_heights[i] - shoulder_heights[i-1])
            velocities.append(velocity)
        
        if not velocities:
            return 50.0
        
        velocity_variance = np.var(velocities)
        if velocity_variance <= 0.0001:
            score = 100.0
        elif velocity_variance <= 0.0005:
            score = 85.0
        elif velocity_variance <= 0.001:
            score = 70.0
        else:
            score = max(0, 100 - (velocity_variance - 0.001) * 50000)
        
        score = min(100, max(0, score))
        metrics.append(self.create_metric("shoulder_stability", score, value=round(velocity_variance, 6)))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent steady shoulder motion — smooth rocking putt.", "shoulder_stability"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "critical",
                "shoulder_stability",
                "Your putting stroke can get a bit wristy and you sometimes peek up too early to see the putt. This leads to the putter face twisting or hitting the ball inconsistently, affecting your line and distance.",
                "A great putt is all about keeping the stroke smooth and the face square. That means using your shoulders to rock the putter (like a pendulum) and keeping your wrists quiet. If your wrists break or you lift your head mid-stroke, the putter face opens or closes and you mis-hit the ball. Staying steady—head down, shoulders doing the work—improves accuracy and distance control on the greens.",
                [
                    "Rock your shoulders to move the putter, as if they are hinges. Your arms and hands should move as one unit with your shoulders; there shouldn't be independent flicking of the wrists",
                    "Keep your eyes down. Try to listen for the ball to drop in the cup instead of watching it immediately",
                    "Maintain a light, even grip pressure and steady lower body. Your legs and hips shouldn't move at all during a putt"
                ],
                "Gate drill: Place two tees or small objects just outside the width of your putter head, creating a \"gate\" near the ball. Practice putting through this gate. If your stroke is steady and straight (driven by shoulders, not wrists), the putter will go through without hitting the tees. Do 15 putts from a short distance focusing on form, not whether the putt sinks.",
                "Rock and lock"
            ))
        else:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "shoulder_stability",
                "Your putting stroke can be improved for better consistency.",
                "Using your shoulders to rock the putter keeps the stroke smooth and the face square.",
                [
                    "Rock your shoulders to move the putter — your arms and hands should move as one unit",
                    "Keep your eyes down — listen for the ball to drop instead of watching immediately",
                    "Maintain steady lower body — legs and hips shouldn't move during the putt"
                ],
                "Gate drill: Place two tees just outside your putter width creating a gate. Practice putting through without hitting the tees. Do 15 putts focusing on shoulder-driven motion.",
                "Rock and lock"
            ))
        
        return score
    
    def _analyze_wrist_stability_putt(self, angles_list: List[Dict], metrics: List, feedback: List) -> float:
        """Putt specific: Analyze wrist stability (quiet wrists)."""
        if not angles_list:
            return 50.0
        
        angle_changes = []
        for i in range(1, len(angles_list)):
            prev_angles = angles_list[i-1]
            curr_angles = angles_list[i]
            
            if "right_elbow" in prev_angles and "right_elbow" in curr_angles:
                change = abs(curr_angles["right_elbow"] - prev_angles["right_elbow"])
                angle_changes.append(change)
        
        if not angle_changes:
            return 50.0
        
        avg_change = np.mean(angle_changes)
        if avg_change <= 2:
            score = 100.0
        elif avg_change <= 5:
            score = 85.0
        elif avg_change <= 8:
            score = 70.0
        else:
            score = max(0, 100 - (avg_change - 8) * 5)
        
        score = min(100, max(0, score))
        metrics.append(self.create_metric("wrist_stability", score, value=round(avg_change, 1), unit="degrees"))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent quiet wrists — steady putting stroke.", "wrist_stability"))
        elif score < 60:
            feedback.append(self.create_feedback(
                "warning",
                "Putt: Keep your wrists quiet. Your arms and hands should move as one unit with your shoulders.",
                "wrist_stability"
            ))
        
        return score
    
    def _analyze_head_stability_putt(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Putt specific: Analyze head stability (no peeking)."""
        if not landmarks_list:
            return 50.0
        
        head_positions = []
        for landmarks in landmarks_list:
            if "nose" in landmarks:
                head_positions.append(landmarks["nose"][1])  # Y position (vertical)
        
        if len(head_positions) < 5:
            return 50.0
        
        head_variance = np.var(head_positions)
        if head_variance <= 0.0001:
            score = 100.0
        elif head_variance <= 0.0005:
            score = 85.0
        elif head_variance <= 0.001:
            score = 70.0
        else:
            score = max(0, 100 - (head_variance - 0.001) * 50000)
        
        score = min(100, max(0, score))
        metrics.append(self.create_metric("head_stability", score, value=round(head_variance, 6)))
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent head stability — staying down through the putt.", "head_stability"))
        elif score < 60:
            feedback.append(self.create_feedback(
                "warning",
                "Putt: Keep your head still and eyes down. Listen for the ball to drop instead of peeking up early.",
                "head_stability"
            ))
        
        return score
    
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
        
        # Only provide feedback if stance width is suboptimal (score < 60)
        # Make it binary: too narrow, too wide, or optimal (no feedback if optimal)
        if score < 60:
            is_too_narrow = avg_stance_width < self.stance_width_ideal
            
            if is_too_narrow:
                # Stance is too narrow - needs to widen
                feedback.append(self.create_actionable_feedback(
                    "warning",
                    "stance_width",
                    "Your stance is too narrow, reducing stability and limiting power generation.",
                    "A narrow stance makes it harder to maintain balance during rotation and reduces your ability to generate power. Widening your stance creates a more stable base that supports your swing mechanics.",
                    [
                        "Set your feet slightly wider than shoulder-width",
                        "Feel pressure evenly through both feet, especially the inside of your trail foot",
                        "You should feel stable enough to rotate without swaying or stepping"
                    ],
                    "",
                    "Wide and stable"
                ))
            else:
                # Stance is too wide - needs to narrow
                feedback.append(self.create_actionable_feedback(
                    "warning",
                    "stance_width",
                    "Your stance is too wide, restricting hip rotation and weight transfer.",
                    "An overly wide stance limits your ability to rotate your hips effectively and can restrict weight transfer. A more athletic, shoulder-width stance allows for better mobility and rotation.",
                    [
                        "Bring your feet closer to shoulder-width",
                        "Feel athletic and mobile, not stretched or locked"
                    ],
                    "",
                    "Athletic base"
                ))
        # If score >= 60, no stance width feedback is shown (optimal or acceptable)
        
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
