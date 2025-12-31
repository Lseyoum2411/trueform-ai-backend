from typing import List, Dict
from datetime import datetime
import numpy as np
import uuid
from app.core.analyzers.base import BaseAnalyzer
from app.models.analysis import AnalysisResult, MetricScore, FeedbackItem


class LacrosseAnalyzer(BaseAnalyzer):
    def __init__(self, movement_type: str = "shooting"):
        super().__init__()
        self.movement_type = movement_type.lower()
        if self.movement_type not in ["shooting"]:
            self.movement_type = "shooting"

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
        if self.movement_type == "shooting":
            # Shooting: Focus on Weight Transfer and Rotation (High Priority)
            weight_transfer_score = self._analyze_weight_transfer_shooting(landmarks_list, metrics, feedback)
            rotation_score = self._analyze_rotation_shooting(landmarks_list, angles_list, metrics, feedback)
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            metric_scores = [m.score for m in metrics]
            critical_metric_names = ["weight_transfer", "rotation"]
            critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=critical_indices, max_critical_failures=2, max_moderate_failures=3)
        else:
            # Default: General lacrosse analysis
            balance_score = self._analyze_balance(landmarks_list, metrics, feedback)
            metric_scores = [m.score for m in metrics] if metrics else [balance_score]
            overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=[], max_critical_failures=2, max_moderate_failures=3) if metrics else balance_score

        for metric in metrics:
            if metric.score >= 80:
                strengths.append(self.get_qualitative_strength_description(metric.name))
            elif metric.score < 60:
                weaknesses.append(self.get_qualitative_weakness_description(metric.name))

        return AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            video_id="",
            sport="lacrosse",
            exercise_type=self.movement_type,
            overall_score=round(overall_score, 2),
            metrics=metrics,
            feedback=feedback,
            strengths=strengths,
            weaknesses=weaknesses,
            raw_data={"frame_count": len(pose_data), "movement_type": self.movement_type},
            created_at=datetime.now(),
        )

    def _analyze_weight_transfer_shooting(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """Lacrosse shooting specific: Analyze weight transfer - back foot to front foot."""
        if not landmarks_list or len(landmarks_list) < 5:
            return 50.0
        
        # Analyze weight transfer during shot - weight should shift from back to front foot
        impact_frames = landmarks_list[len(landmarks_list) // 2:]
        weight_transfers = []
        
        for landmarks in impact_frames:
            if all(k in landmarks for k in ["left_ankle", "right_ankle", "left_hip", "right_hip"]):
                left_ankle_x = landmarks["left_ankle"][0]
                right_ankle_x = landmarks["right_ankle"][0]
                hip_center_x = (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2
                
                ankle_center = (left_ankle_x + right_ankle_x) / 2
                # For right-handed shooter, left foot is typically front foot
                # Weight should shift forward
                if left_ankle_x < right_ankle_x:  # Left is front
                    transfer = max(0, min(1, (ankle_center - hip_center_x) / (ankle_center - left_ankle_x + 0.01)))
                else:
                    transfer = max(0, min(1, (hip_center_x - ankle_center) / (right_ankle_x - ankle_center + 0.01)))
                
                weight_transfers.append(transfer)
        
        if not weight_transfers:
            return 50.0
        
        avg_transfer = np.mean(weight_transfers)
        # Good weight transfer: 0.55+ (weight shifted to front foot)
        ideal_transfer = 0.60
        deviation = abs(avg_transfer - ideal_transfer)
        
        if deviation <= 0.15:
            score = 100.0
        else:
            score = max(0, 100 - (deviation / 0.15) * 30)
        
        score = min(100, max(0, score))
        metric = self.create_metric("weight_transfer", score, value=round(avg_transfer, 3), unit="ratio")
        metrics.append(metric)
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent weight transfer — weight shifted to front foot.", "weight_transfer"))
        elif score < 60:
            feedback.append(self.create_actionable_feedback(
                "critical",
                "weight_transfer",
                "Your lacrosse shot is relying too much on your arms; you often keep your weight on your back foot and don't rotate your torso fully. This results in shots that lack power and sometimes miss the mark.",
                "A powerful, accurate lacrosse shot uses the whole body. Transferring your weight from your back foot to front foot and rotating your hips and shoulders into the shot generates far more force than arms alone. It's similar to a baseball throw or a golf swing — the legs and core generate power, and the arms follow through. Without weight transfer, you're essentially shooting with half your potential power and can also sail the ball because your body isn't aligned toward the target. Incorporating your legs and core will give you a faster shot and better accuracy.",
                [
                    "Step into your shot. If your right hand is the top hand on the stick, your left foot should step forward toward the goal as you shoot (and vice versa for lefties)",
                    "Start with your weight on your back foot and push off it, shifting your weight onto the front foot as you release the ball",
                    "Rotate your hips and shoulders. As you step, turn your hips toward the goal and follow with your shoulders",
                    "Follow through with your stick pointing toward where you aimed. A good indicator of proper rotation is that after the shot, your stick and body continue in the direction of the shot"
                ],
                "Step-down shooting drill: Stand a comfortable distance from the goal. Start with your feet staggered (if you're a righty shooter, right foot back, left foot forward). Take a cradle and then step forward hard with your back foot, rotate your body, and shoot. Repeat this multiple times focusing on really feeling the push off the back foot and the torso turn. The ball should zip out faster. Then practice shooting on the run, using that same weight transfer on the plant foot and rotation.",
                "Legs into shot"
            ))
        else:
            feedback.append(self.create_actionable_feedback(
                "warning",
                "weight_transfer",
                "Your weight transfer can be improved for more powerful shots.",
                "Transferring weight from back foot to front foot generates far more force than arms alone.",
                [
                    "Step into your shot — step forward toward the goal",
                    "Start with weight on your back foot and push off it, shifting to front foot as you release",
                    "Rotate your hips and shoulders toward the goal"
                ],
                "Step-down shooting drill: Stand a comfortable distance from goal. Start with feet staggered, step forward hard with back foot, rotate your body, and shoot. Repeat multiple times focusing on weight transfer.",
                "Legs into shot"
            ))
        
        return score
    
    def _analyze_rotation_shooting(self, landmarks_list: List[Dict], angles_list: List[Dict], metrics: List, feedback: List) -> float:
        """Lacrosse shooting specific: Analyze torso rotation - hips and shoulders should rotate toward goal."""
        if not landmarks_list or len(landmarks_list) < 5:
            return 50.0
        
        # Analyze hip/shoulder rotation - should rotate toward goal during shot
        approach_frames = landmarks_list[:len(landmarks_list) // 2]
        impact_frames = landmarks_list[len(landmarks_list) // 2:]
        
        if not approach_frames or not impact_frames:
            return 50.0
        
        # Calculate average shoulder/hip positions in approach vs impact
        approach_shoulder_x = []
        impact_shoulder_x = []
        
        for landmarks in approach_frames:
            if "left_shoulder" in landmarks and "right_shoulder" in landmarks:
                shoulder_center = (landmarks["left_shoulder"][0] + landmarks["right_shoulder"][0]) / 2
                approach_shoulder_x.append(shoulder_center)
        
        for landmarks in impact_frames:
            if "left_shoulder" in landmarks and "right_shoulder" in landmarks:
                shoulder_center = (landmarks["left_shoulder"][0] + landmarks["right_shoulder"][0]) / 2
                impact_shoulder_x.append(shoulder_center)
        
        if not approach_shoulder_x or not impact_shoulder_x:
            return 50.0
        
        # Rotation = change in shoulder position (for right-handed, should move left/forward)
        avg_approach = np.mean(approach_shoulder_x)
        avg_impact = np.mean(impact_shoulder_x)
        rotation = abs(avg_impact - avg_approach)
        
        # Some rotation is good (0.02 to 0.05 ideal)
        if 0.02 <= rotation <= 0.05:
            score = 100.0
        elif rotation < 0.02:
            score = (rotation / 0.02) * 70.0
        elif rotation <= 0.08:
            score = 70.0 + ((0.08 - rotation) / 0.03) * 30.0
        else:
            score = max(50, 100 - (rotation - 0.08) * 500)
        
        score = min(100, max(0, score))
        metric = self.create_metric("rotation", score, value=round(rotation, 3))
        metrics.append(metric)
        
        if score >= 85:
            feedback.append(self.create_feedback("info", "Excellent rotation — hips and shoulders rotating toward goal.", "rotation"))
        else:
            feedback.append(self.create_feedback(
                "warning",
                "Lacrosse shooting: Rotate your hips and shoulders. As you step, turn your hips toward the goal and follow with your shoulders. Your torso should unwind powerfully toward the target.",
                "rotation"
            ))
        
        return score
    
    def _analyze_balance(self, landmarks_list: List[Dict], metrics: List, feedback: List) -> float:
        """General balance analysis for lacrosse movements."""
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
            sport="lacrosse",
            exercise_type=self.movement_type,
            overall_score=0.0,
            metrics=[],
            feedback=[],
            strengths=[],
            weaknesses=[],
            raw_data={},
            created_at=datetime.now(),
        )

