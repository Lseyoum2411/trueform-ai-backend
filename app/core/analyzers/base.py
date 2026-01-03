from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
import numpy as np
from app.models.analysis import AnalysisResult, MetricScore, FeedbackItem

logger = logging.getLogger(__name__)


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
    
    def finalize_score(self, component_scores: List[float], fallback: int = 70) -> float:
        """
        Ensures score is always valid and never 0 unless data is truly invalid.
        
        Args:
            component_scores: List of metric scores (0-100)
            fallback: Default score to use if component_scores is empty or invalid
            
        Returns:
            Final score from 40-100 (never 0 unless fallback is 0, which indicates invalid data)
        """
        if not component_scores:
            logger.warning(f"No component scores provided, using fallback: {fallback}")
            return float(fallback)
        
        try:
            score = float(np.mean(component_scores))
        except (ValueError, TypeError) as e:
            logger.warning(f"Error calculating score mean: {e}, using fallback: {fallback}")
            return float(fallback)
        
        # Absolute floor for valid analysis: never return 0 unless fallback is 0 (invalid data)
        # Minimum score for any valid analysis is 40
        if score <= 0:
            logger.warning(f"Score calculated as {score}, using fallback: {fallback}")
            return float(fallback)
        
        # Ensure score is within reasonable bounds (40-100)
        # Scores below 40 indicate catastrophic failure, but still valid analysis
        final_score = max(40.0, min(100.0, score))
        return round(final_score, 2)
    
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
            Overall score from 40-100 (never 0 unless data is invalid)
        """
        if not metric_scores:
            logger.warning("No metric scores provided to calculate_overall_score_penalty_based, using fallback")
            return self.finalize_score([], fallback=70)
        
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
        
        # Use finalize_score to ensure we never return 0 for valid analysis
        final_score = self.finalize_score([base_score], fallback=70)
        return final_score
    
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
    
    def deduplicate_feedback_by_metric(self, feedback_list: List[FeedbackItem]) -> List[FeedbackItem]:
        """
        Remove duplicate feedback items that have the same metric name or similar titles.
        Ensures only ONE feedback item per metric is returned.
        
        Deduplication strategy:
        1. Exact metric match → keep only first
        2. Similar titles (e.g., "Vertical Alignment" vs "Vertical alignment needs work") → keep only first
        3. Prioritize higher severity items if same metric
        
        Args:
            feedback_list: List of FeedbackItem objects
            
        Returns:
            Filtered list with at most one feedback item per metric
        """
        seen_metrics = set()
        seen_titles = set()
        unique_feedback = []
        
        # Sort by priority (critical > warning > info) so we keep the most important version
        priority_order = {"critical": 0, "warning": 1, "info": 2, "error": 0}
        sorted_feedback = sorted(
            feedback_list,
            key=lambda x: priority_order.get(getattr(x, 'level', 'warning'), 1)
        )
        
        for item in sorted_feedback:
            metric = getattr(item, 'metric', None)
            message = getattr(item, 'message', '') or ''
            
            # Skip items without a metric (keep them as they might be general feedback)
            if not metric:
                unique_feedback.append(item)
                continue
            
            # Check for exact metric match
            if metric in seen_metrics:
                logger.info(f"Removed duplicate feedback by metric: {metric}")
                continue
            
            # Normalize title from message for comparison
            # Extract title from structured message or use first part of message
            title = ""
            if '|' in message:
                # Structured message: extract first section
                parts = message.split('|')
                if len(parts) >= 2:
                    title = parts[1].strip()  # First content section
            else:
                # Simple message: use first sentence or first 50 chars
                title = message.split('.')[0].strip()[:50]
            
            # Normalize title for comparison (lowercase, remove punctuation)
            normalized_title = title.lower().strip().replace('_', ' ').replace('-', ' ')
            # Remove common suffixes like "needs work", "needs improvement", etc.
            normalized_title = normalized_title.replace(' needs work', '').replace(' needs improvement', '')
            normalized_title = normalized_title.replace(' can improve', '').replace(' requires attention', '')
            
            # Check for similar titles (one contains the other or they're very similar)
            is_duplicate_title = False
            for seen_title in seen_titles:
                # Check if titles are similar (one contains the other or vice versa)
                if normalized_title in seen_title or seen_title in normalized_title:
                    # Additional check: if both refer to same metric concept
                    if len(normalized_title) > 5 and len(seen_title) > 5:  # Avoid matching very short strings
                        is_duplicate_title = True
                        logger.info(f"Removed duplicate feedback by similar title: '{title}' (similar to existing)")
                        break
            
            if is_duplicate_title:
                continue
            
            # Not a duplicate - add it
            seen_metrics.add(metric)
            if normalized_title:
                seen_titles.add(normalized_title)
            unique_feedback.append(item)
        
        # Final validation: ensure no duplicates remain
        final_metrics = [getattr(item, 'metric', None) for item in unique_feedback if getattr(item, 'metric', None)]
        if len(final_metrics) != len(set(final_metrics)):
            logger.error("DUPLICATES STILL EXIST AFTER DEDUPLICATION! Applying aggressive deduplication.")
            # Keep only first occurrence of each metric
            seen = set()
            unique_feedback = [
                item for item in unique_feedback
                if (metric := getattr(item, 'metric', None)) and metric not in seen and not seen.add(metric)
            ]
        
        return unique_feedback
    
    def validate_feedback(self, feedback_list: List[FeedbackItem]) -> List[FeedbackItem]:
        """
        Remove invalid, vague, or contradictory feedback items.
        
        Filters out:
        - Vague "either/or" statements (e.g., "either A or B")
        - Contradictory statements
        - Placeholder/empty feedback
        - Feedback with low confidence indicators
        
        Args:
            feedback_list: List of FeedbackItem objects
            
        Returns:
            Filtered list with only valid, specific feedback
        """
        valid_feedback = []
        
        for item in feedback_list:
            message = getattr(item, 'message', '') or ''
            message_lower = message.lower()
            
            # Check for vague "either/or" patterns
            if 'either' in message_lower and 'or' in message_lower:
                # Check if it's a vague statement (not a valid "either X or Y" where both are specific)
                # Vague: "either too close or too far" (doesn't specify which)
                # Valid: "either forward lean or backward lean" (specific directions)
                vague_patterns = [
                    'either too',
                    'either not',
                    'either close or far',
                    'either forward or backward',
                    "couldn't determine",
                    "couldn't tell",
                    "unable to determine"
                ]
                if any(pattern in message_lower for pattern in vague_patterns):
                    logger.warning(f"Skipping vague feedback: {message[:100]}")
                    continue
            
            # Check for contradictory statements
            if "but it couldn't tell" in message_lower or "but couldn't determine" in message_lower:
                logger.warning(f"Skipping contradictory feedback: {message[:100]}")
                continue
            
            # Check for empty or placeholder feedback
            placeholder_patterns = [
                'todo', 'placeholder', 'tbd', 'coming soon', 'in development',
                'detailed analysis coming', 'analysis completed', 'not yet implemented'
            ]
            if not message or message.strip() in ['TODO', 'PLACEHOLDER', 'TBD']:
                logger.warning(f"Skipping placeholder feedback: {message[:100]}")
                continue
            if any(pattern in message_lower for pattern in placeholder_patterns):
                logger.warning(f"Skipping placeholder feedback: {message[:100]}")
                continue
            
            # All checks passed - keep this feedback
            valid_feedback.append(item)
        
        return valid_feedback

