from typing import List, Dict
from datetime import datetime
import numpy as np
import uuid
from app.core.analyzers.weightlifting.base_lift import BaseLiftAnalyzer
from app.models.analysis import AnalysisResult


class FrontSquatAnalyzer(BaseLiftAnalyzer):
    async def analyze(self, pose_data: List[Dict]) -> AnalysisResult:
        if not pose_data:
            return self._create_empty_result()
        
        landmarks_list = [frame.get("landmarks", {}) for frame in pose_data]
        angles_list = [frame.get("angles", {}) for frame in pose_data]
        
        metrics = []
        feedback = []
        strengths = []
        weaknesses = []
        
        # High Priority: Elbows Up and Chest Up
        elbow_position_score, elbow_position_metric, elbow_position_feedback = self.analyze_elbow_position_front_squat(landmarks_list, angles_list)
        metrics.append(elbow_position_metric)
        feedback.extend(elbow_position_feedback)
        
        depth_score, depth_metric, depth_feedback = self.analyze_depth(landmarks_list, 0.75, "front_squat")
        metrics.append(depth_metric)
        feedback.extend(depth_feedback)
        
        path_score, path_metric, path_feedback = self.analyze_bar_path(landmarks_list, "front_squat")
        metrics.append(path_metric)
        feedback.extend(path_feedback)
        
        spine_score, spine_metric, spine_feedback = self.analyze_spine_alignment(landmarks_list, "front_squat")
        metrics.append(spine_metric)
        feedback.extend(spine_feedback)
        
        tempo_score, tempo_metric, tempo_feedback = self.analyze_tempo(pose_data, "front_squat")
        metrics.append(tempo_metric)
        feedback.extend(tempo_feedback)
        
        knee_score, knee_metric, knee_feedback = self.analyze_joint_angles(angles_list, "left_knee", 95.0, 15.0, "front_squat")
        metrics.append(knee_metric)
        feedback.extend(knee_feedback)
        
        # Use penalty-based professional benchmark scoring
        # Critical metrics: depth, spine_alignment, bar_path
        metric_scores = [m.score for m in metrics]
        critical_metric_names = ["depth", "spine_alignment", "bar_path"]
        critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
        overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=critical_indices, max_critical_failures=2, max_moderate_failures=3)
        
        for metric in metrics:
            if metric.score >= 80:
                strengths.append(self.get_qualitative_strength_description(metric.name))
            elif metric.score < 60:
                weaknesses.append(self.get_qualitative_weakness_description(metric.name))
        
        # Remove any duplicate feedback items by metric name
        feedback = self.deduplicate_feedback_by_metric(feedback)
        
        return AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            video_id="",
            sport="weightlifting",
            lift_type="front_squat",
            overall_score=round(overall_score, 2),
            metrics=metrics,
            feedback=feedback,
            strengths=strengths,
            weaknesses=weaknesses,
            raw_data={"frame_count": len(pose_data)},
            created_at=datetime.now(),
        )
    
    def _create_empty_result(self) -> AnalysisResult:
        return AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            video_id="",
            sport="weightlifting",
            lift_type="front_squat",
            overall_score=0.0,
            metrics=[],
            feedback=[],
            strengths=[],
            weaknesses=[],
            raw_data={},
            created_at=datetime.now(),
        )






