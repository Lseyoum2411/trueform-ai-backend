from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.models.analysis import AnalysisResult, MetricScore, FeedbackItem


class BaseAnalyzer(ABC):
    @abstractmethod
    async def analyze(self, pose_data: List[Dict]) -> AnalysisResult:
        pass
    
    def calculate_score(self, value: float, min_val: float, max_val: float, reverse: bool = False) -> float:
        if max_val == min_val:
            return 50.0
        
        normalized = (value - min_val) / (max_val - min_val)
        if reverse:
            normalized = 1 - normalized
        
        score = max(0, min(100, normalized * 100))
        return round(score, 2)
    
    def create_feedback(
        self,
        level: str,
        message: str,
        metric: Optional[str] = None,
    ) -> FeedbackItem:
        return FeedbackItem(level=level, message=message, metric=metric)
    
    def create_metric(
        self,
        name: str,
        score: float,
        value: Optional[Any] = None,
        unit: Optional[str] = None,
    ) -> MetricScore:
        return MetricScore(name=name, score=score, value=value, unit=unit)

