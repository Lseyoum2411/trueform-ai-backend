from typing import List, Dict
from datetime import datetime
import numpy as np
import uuid
from app.core.analyzers.weightlifting.base_lift import BaseLiftAnalyzer
from app.models.analysis import AnalysisResult


class RearDeltFliesAnalyzer(BaseLiftAnalyzer):
    async def analyze(self, pose_data: List[Dict]) -> AnalysisResult:
        if not pose_data:
            return self._create_empty_result()
        
        landmarks_list = [frame.get("landmarks", {}) for frame in pose_data]
        angles_list = [frame.get("angles", {}) for frame in pose_data]
        
        metrics = []
        feedback = []
        strengths = []
        weaknesses = []
        
        # Analyze key aspects of rear delt flies
        spine_score, spine_metric, spine_feedback = self.analyze_spine_alignment(landmarks_list, "rear_delt_flies")
        metrics.append(spine_metric)
        feedback.extend(spine_feedback)
        
        tempo_score, tempo_metric, tempo_feedback = self.analyze_tempo(pose_data, "rear_delt_flies")
        metrics.append(tempo_metric)
        feedback.extend(tempo_feedback)
        
        shoulder_score, shoulder_metric, shoulder_feedback = self.analyze_joint_angles(angles_list, "left_shoulder", 90.0, 25.0, "rear_delt_flies")
        metrics.append(shoulder_metric)
        feedback.extend(shoulder_feedback)
        
        elbow_score, elbow_metric, elbow_feedback = self.analyze_joint_angles(angles_list, "left_elbow", 170.0, 20.0, "rear_delt_flies")
        metrics.append(elbow_metric)
        feedback.extend(elbow_feedback)
        
        # Use penalty-based professional benchmark scoring
        # Critical metrics: spine_alignment
        metric_scores = [m.score for m in metrics]
        critical_metric_names = ["spine_alignment"]
        critical_indices = [i for i, m in enumerate(metrics) if m.name in critical_metric_names]
        overall_score = self.calculate_overall_score_penalty_based(metric_scores, critical_metrics=critical_indices, max_critical_failures=2, max_moderate_failures=3)
        
        for metric in metrics:
            if metric.score >= 80:
                strengths.append(self.get_qualitative_strength_description(metric.name))
            elif metric.score < 60:
                weaknesses.append(self.get_qualitative_weakness_description(metric.name))
        
        return AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            video_id="",
            sport="weightlifting",
            lift_type="rear_delt_flies",
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
            lift_type="rear_delt_flies",
            overall_score=0.0,
            metrics=[],
            feedback=[],
            strengths=[],
            weaknesses=[],
            raw_data={},
            created_at=datetime.now(),
        )
