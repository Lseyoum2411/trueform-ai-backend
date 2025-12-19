from typing import List, Dict
from datetime import datetime
import numpy as np
import uuid
from app.core.analyzers.weightlifting.base_lift import BaseLiftAnalyzer
from app.models.analysis import AnalysisResult


class LatPulldownAnalyzer(BaseLiftAnalyzer):
    async def analyze(self, pose_data: List[Dict]) -> AnalysisResult:
        if not pose_data:
            return self._create_empty_result()
        
        landmarks_list = [frame.get("landmarks", {}) for frame in pose_data]
        angles_list = [frame.get("angles", {}) for frame in pose_data]
        
        metrics = []
        feedback = []
        strengths = []
        weaknesses = []
        
        depth_score, depth_metric, depth_feedback = self.analyze_depth(landmarks_list, 0.5)
        metrics.append(depth_metric)
        feedback.extend(depth_feedback)
        
        path_score, path_metric, path_feedback = self.analyze_bar_path(landmarks_list)
        metrics.append(path_metric)
        feedback.extend(path_feedback)
        
        spine_score, spine_metric, spine_feedback = self.analyze_spine_alignment(landmarks_list)
        metrics.append(spine_metric)
        feedback.extend(spine_feedback)
        
        tempo_score, tempo_metric, tempo_feedback = self.analyze_tempo(pose_data)
        metrics.append(tempo_metric)
        feedback.extend(tempo_feedback)
        
        elbow_score, elbow_metric, elbow_feedback = self.analyze_joint_angles(angles_list, "left_elbow", 90.0, 20.0)
        metrics.append(elbow_metric)
        feedback.extend(elbow_feedback)
        
        shoulder_score, shoulder_metric, shoulder_feedback = self.analyze_joint_angles(angles_list, "left_hip", 30.0, 20.0)
        metrics.append(shoulder_metric)
        feedback.extend(shoulder_feedback)
        
        overall_score = np.mean([
            depth_score, path_score, spine_score, tempo_score, elbow_score, shoulder_score
        ])
        
        for metric in metrics:
            if metric.score >= 80:
                strengths.append(f"{metric.name}: {metric.score:.1f}/100")
            elif metric.score < 60:
                weaknesses.append(f"{metric.name}: {metric.score:.1f}/100")
        
        return AnalysisResult(
            analysis_id=str(uuid.uuid4()),
            video_id="",
            sport="weightlifting",
            lift_type="lat_pulldown",
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
            lift_type="lat_pulldown",
            overall_score=0.0,
            metrics=[],
            feedback=[],
            strengths=[],
            weaknesses=[],
            raw_data={},
            created_at=datetime.now(),
        )





