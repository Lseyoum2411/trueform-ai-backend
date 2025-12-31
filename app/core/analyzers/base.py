from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.models.analysis import AnalysisResult, MetricScore, FeedbackItem


class BaseAnalyzer(ABC):
    @abstractmethod
    async def analyze(self, pose_data: List[Dict]) -> AnalysisResult:
        pass
    
    def calculate_score(self, value: float, min_val: float, max_val: float, reverse: bool = False) -> float:
        """Legacy method for backward compatibility - returns metric score for tracking purposes."""
        if max_val == min_val:
            return 50.0
        
        normalized = (value - min_val) / (max_val - min_val)
        if reverse:
            normalized = 1 - normalized
        
        score = max(0, min(100, normalized * 100))
        return round(score, 2)
    
    def calculate_penalty_from_metric_score(self, metric_score: float, is_critical: bool = False) -> float:
        """
        Convert a metric score (0-100) to a penalty amount based on deviation from professional benchmark (90+).
        
        Professional benchmark = 90+ (elite level)
        - Score >= 90: No penalty (0)
        - Score 85-89: Minor penalty (-5 to -10)
        - Score 75-84: Moderate penalty (-15 to -25)
        - Score 60-74: Severe penalty (-30 to -40)
        - Score < 60: Critical penalty (-45 to -60)
        
        Critical metrics receive 1.5x penalty multiplier.
        
        Args:
            metric_score: Score from 0-100
            is_critical: If True, applies 1.5x penalty multiplier
            
        Returns:
            Penalty amount (negative value) to subtract from base score of 100
        """
        if metric_score >= 90:
            penalty = 0.0
        elif metric_score >= 85:
            # Minor deviation: -5 to -10
            penalty = -5.0 - ((90 - metric_score) / (90 - 85)) * 5.0
        elif metric_score >= 75:
            # Moderate deviation: -15 to -25
            penalty = -15.0 - ((85 - metric_score) / (85 - 75)) * 10.0
        elif metric_score >= 60:
            # Severe deviation: -30 to -40
            penalty = -30.0 - ((75 - metric_score) / (75 - 60)) * 10.0
        else:
            # Critical deviation: -45 to -60
            penalty = -45.0 - ((60 - metric_score) / 60) * 15.0
        
        # Apply critical multiplier
        if is_critical:
            penalty *= 1.5
        
        return round(penalty, 2)
    
    def calculate_overall_score_penalty_based(
        self,
        metric_scores: List[float],
        critical_metrics: List[int] = None,
        max_critical_failures: int = 2,
        max_moderate_failures: int = 3
    ) -> float:
        """
        Calculate overall score using penalty-based professional benchmark model.
        
        Starts at 100 and applies penalties for each metric deviation from professional standard.
        
        Args:
            metric_scores: List of metric scores (0-100)
            critical_metrics: List of indices in metric_scores that are critical metrics
            max_critical_failures: Hard cap threshold - if this many critical failures, cap score
            max_moderate_failures: Hard cap threshold - if this many moderate failures, cap score
            
        Returns:
            Overall score from 0-100
        """
        if not metric_scores:
            return 50.0
        
        if critical_metrics is None:
            critical_metrics = []
        
        # Start at 100 (professional benchmark)
        base_score = 100.0
        
        critical_failures = 0  # Count of metrics < 60
        moderate_failures = 0  # Count of metrics 60-74
        catastrophic_failures = 0  # Count of metrics < 50
        
        # Apply penalties for each metric
        for i, score in enumerate(metric_scores):
            is_critical = i in critical_metrics
            penalty = self.calculate_penalty_from_metric_score(score, is_critical=is_critical)
            base_score += penalty
            
            # Track failure counts for hard caps
            if score < 50:
                catastrophic_failures += 1
            elif score < 60:
                critical_failures += 1
            elif score < 75:
                moderate_failures += 1
        
        # Apply hard caps based on failure counts
        if catastrophic_failures >= 1:
            base_score = min(base_score, 50.0)  # Any catastrophic failure caps at 50
        elif critical_failures >= max_critical_failures:
            base_score = min(base_score, 60.0)  # 2+ critical failures cap at 60
        elif moderate_failures >= max_moderate_failures:
            base_score = min(base_score, 65.0)  # 3+ moderate failures cap at 65
        
        # Clamp to 0-100 range
        final_score = max(0.0, min(100.0, base_score))
        return round(final_score, 2)
    
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
    
    def create_positive_feedback(
        self,
        metric: str,
        what_youre_doing_well: str,
        reinforcement_cue: str,
    ) -> FeedbackItem:
        """Create positive/reinforcement feedback when form is acceptable (score >= 60)."""
        # Format positive feedback for parsing in service layer
        structured_message = f"POSITIVE|{what_youre_doing_well}|REINFORCEMENT|{reinforcement_cue}"
        return FeedbackItem(level="info", message=structured_message, metric=metric)
    
    def create_metric(
        self,
        name: str,
        score: float,
        value: Optional[Any] = None,
        unit: Optional[str] = None,
    ) -> MetricScore:
        return MetricScore(name=name, score=score, value=value, unit=unit)
    
    def create_beginner_feedback(
        self,
        level: str,
        metric: str,
        what_we_saw: str,
        how_to_fix: List[str],
        what_it_should_feel_like: str,
        common_mistake: str,
        self_check: str,
    ) -> FeedbackItem:
        """Create beginner-friendly feedback for weightlifting with simple, clear instructions."""
        # Combine into structured message format
        how_to_fix_str = "||".join(how_to_fix) if how_to_fix else ""
        structured_message = f"WHAT_WE_SAW|{what_we_saw}|HOW_TO_FIX|{how_to_fix_str}|WHAT_IT_SHOULD_FEEL_LIKE|{what_it_should_feel_like}|COMMON_MISTAKE|{common_mistake}|SELF_CHECK|{self_check}"
        return FeedbackItem(level=level, message=structured_message, metric=metric)
    
    def get_qualitative_strength_description(self, metric_name: str) -> str:
        """Convert metric name to qualitative strength description (no numeric values)."""
        # Map metric names to qualitative descriptions
        descriptions = {
            "base_stability": "Strong base stability",
            "vertical_alignment": "Excellent vertical alignment",
            "release_speed": "Quick release",
            "shot_rhythm": "Smooth shot rhythm",
            "elbow_alignment": "Proper elbow alignment",
            "knee_bend": "Good knee bend",
            "hip_alignment": "Solid hip alignment",
            "depth": "Excellent depth",
            "bar_path": "Straight bar path",
            "spine_alignment": "Proper spine alignment",
            "tempo": "Consistent tempo",
            "weight_transfer": "Strong weight transfer",
            "hip_rotation": "Excellent hip rotation",
            "balance": "Good balance",
            "follow_through": "Complete follow-through",
        }
        return descriptions.get(metric_name, f"Strong {metric_name.replace('_', ' ')}")
    
    def get_qualitative_weakness_description(self, metric_name: str) -> str:
        """Convert metric name to qualitative weakness description (no numeric values)."""
        descriptions = {
            "base_stability": "Base stability needs improvement",
            "vertical_alignment": "Vertical alignment needs work",
            "release_speed": "Release speed can improve",
            "shot_rhythm": "Shot rhythm needs refinement",
            "elbow_alignment": "Elbow alignment needs correction",
            "knee_bend": "Knee bend requires attention",
            "hip_alignment": "Hip alignment needs work",
            "depth": "Depth needs improvement",
            "bar_path": "Bar path needs correction",
            "spine_alignment": "Spine alignment requires attention",
            "tempo": "Tempo consistency needs work",
            "weight_transfer": "Weight transfer can improve",
            "hip_rotation": "Hip rotation needs development",
            "balance": "Balance requires attention",
            "follow_through": "Follow-through needs completion",
        }
        return descriptions.get(metric_name, f"{metric_name.replace('_', ' ').title()} needs improvement")
    
    def consolidate_weight_transfer_feedback(self, feedback_list: List[FeedbackItem]) -> List[FeedbackItem]:
        """
        Remove duplicate weight transfer feedback items.
        Ensures only ONE feedback item related to weight transfer exists in the list.
        
        Weight transfer concepts that should be consolidated:
        - weight_transfer, weight_shift, back-to-front loading
        - balance transition, pressure_shift, center_of_mass movement
        - hip_rotation (when combined with weight transfer concepts, especially in batting)
        
        Args:
            feedback_list: List of FeedbackItem objects
            
        Returns:
            Filtered list with at most one weight transfer feedback item
        """
        weight_transfer_metrics = {
            "weight_transfer", "weight_shift", "balance_transition",
            "pressure_shift", "center_of_mass", "back_to_front_loading"
        }
        
        # Track weight transfer related feedback
        weight_transfer_items = []
        other_items = []
        has_weight_transfer_metric = False
        
        for item in feedback_list:
            metric = getattr(item, 'metric', None) or ""
            metric_lower = metric.lower() if metric else ""
            
            # Check if this is weight transfer related
            is_weight_transfer = (
                metric in weight_transfer_metrics or
                (metric and "weight" in metric_lower and "transfer" in metric_lower)
            )
            
            if is_weight_transfer:
                weight_transfer_items.append(item)
                has_weight_transfer_metric = True
            # Also check hip_rotation if we already have weight transfer (they overlap in batting)
            elif metric == "hip_rotation" and has_weight_transfer_metric:
                # Skip hip_rotation if we already have weight_transfer feedback
                continue
            else:
                other_items.append(item)
        
        # Keep only the first/primary weight transfer item if multiple exist
        if weight_transfer_items:
            # Prefer items with "weight_transfer" metric over others
            primary_item = None
            for item in weight_transfer_items:
                metric = getattr(item, 'metric', None) or ""
                if metric == "weight_transfer":
                    primary_item = item
                    break
            
            if not primary_item:
                primary_item = weight_transfer_items[0]  # Use first one if no exact match
            
            return [primary_item] + other_items
        
        return feedback_list

