from typing import List, Dict
from datetime import datetime
import numpy as np
import uuid
from app.core.analyzers.weightlifting.base_lift import BaseLiftAnalyzer
from app.models.analysis import AnalysisResult


class RDLAnalyzer(BaseLiftAnalyzer):
    async def analyze(self, pose_data: List[Dict]) -> AnalysisResult:
        if not pose_data:
            return self._create_empty_result()
        
        landmarks_list = [frame.get("landmarks", {}) for frame in pose_data]
        angles_list = [frame.get("angles", {}) for frame in pose_data]
        
        metrics = []
        feedback = []
        strengths = []
        weaknesses = []
        
        # High Priority: Proper Hip Hinge
        hip_hinge_score, hip_hinge_metric, hip_hinge_feedback = self.analyze_hip_hinge_rdl(landmarks_list, angles_list)
        metrics.append(hip_hinge_metric)
        feedback.extend(hip_hinge_feedback)
        
        depth_score, depth_metric, depth_feedback = self.analyze_depth(landmarks_list, 0.65, "rdl")
        metrics.append(depth_metric)
        feedback.extend(depth_feedback)
        
        path_score, path_metric, path_feedback = self.analyze_bar_path(landmarks_list, "rdl")
        metrics.append(path_metric)
        feedback.extend(path_feedback)
        
        spine_score, spine_metric, spine_feedback = self.analyze_spine_alignment(landmarks_list, "rdl")
        metrics.append(spine_metric)
        feedback.extend(spine_feedback)
        
        tempo_score, tempo_metric, tempo_feedback = self.analyze_tempo(pose_data, "rdl")
        metrics.append(tempo_metric)
        feedback.extend(tempo_feedback)
        
        hip_score, hip_metric, hip_feedback = self.analyze_joint_angles(angles_list, "left_hip", 130.0, 25.0, "rdl")
        metrics.append(hip_metric)
        feedback.extend(hip_feedback)
        
        # Use penalty-based professional benchmark scoring
        # Critical metrics: hip_hinge, spine_alignment
        metric_scores = [m.score for m in metrics]
        critical_metric_names = ["hip_hinge", "spine_alignment"]
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
            lift_type="rdl",
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
            lift_type="rdl",
            overall_score=0.0,
            metrics=[],
            feedback=[],
            strengths=[],
            weaknesses=[],
            raw_data={},
            created_at=datetime.now(),
        )






