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
    
    def create_actionable_feedback(
        self,
        level: str,
        metric: str,
        observation: str,
        impact: str,
        how_to_fix: List[str],
        drill: str,
        coaching_cue: str,
    ) -> FeedbackItem:
        """Create structured feedback for basketball with actionable recommendations."""
        # Combine into message for backwards compatibility, but structure is in metadata
        message_parts = [observation]
        if impact:
            message_parts.append(f"Impact: {impact}")
        if how_to_fix:
            message_parts.append(f"How to fix: {', '.join(how_to_fix)}")
        if drill:
            message_parts.append(f"Drill: {drill}")
        if coaching_cue:
            message_parts.append(f"Cue: {coaching_cue}")
        
        # Store structured data in message with special markers (will be parsed in service layer)
        # Format: OBSERVATION|observation text|IMPACT|impact text|HOW_TO_FIX|item1||item2||item3|DRILL|drill text|CUE|cue text
        # Use double pipe (||) as delimiter for list items to avoid conflicts
        how_to_fix_str = "||".join(how_to_fix) if how_to_fix else ""
        structured_message = f"OBSERVATION|{observation}|IMPACT|{impact}|HOW_TO_FIX|{how_to_fix_str}|DRILL|{drill}|CUE|{coaching_cue}"
        return FeedbackItem(level=level, message=structured_message, metric=metric)
    
    def create_metric(
        self,
        name: str,
        score: float,
        value: Optional[Any] = None,
        unit: Optional[str] = None,
    ) -> MetricScore:
        return MetricScore(name=name, score=score, value=value, unit=unit)

