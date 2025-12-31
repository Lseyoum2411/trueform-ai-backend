from typing import List, Dict, Optional
from app.core.analyzers.base import BaseAnalyzer
from app.core.analyzers.weightlifting.squat import SquatAnalyzer
from app.core.analyzers.weightlifting.front_squat import FrontSquatAnalyzer
from app.core.analyzers.weightlifting.deadlift import DeadliftAnalyzer
from app.core.analyzers.weightlifting.rdl import RDLAnalyzer
from app.core.analyzers.weightlifting.bench_press import BenchPressAnalyzer
from app.core.analyzers.weightlifting.barbell_row import BarbellRowAnalyzer
from app.core.analyzers.weightlifting.dumbbell_row import DumbbellRowAnalyzer
# rear_delt_flies removed - not in movement registry requirements
from app.core.analyzers.weightlifting.lat_pulldown import LatPulldownAnalyzer
from app.models.analysis import AnalysisResult


class WeightliftingAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()
        self.lift_analyzers = {
            # Support both legacy and normalized IDs for backward compatibility
            "back_squat": SquatAnalyzer(),
            "barbell_squat": SquatAnalyzer(),  # Normalized ID maps to same analyzer
            "front_squat": FrontSquatAnalyzer(),
            "deadlift": DeadliftAnalyzer(),
            "rdl": RDLAnalyzer(),
            "romanian_deadlift": RDLAnalyzer(),  # Normalized ID maps to RDL analyzer
            "bench_press": BenchPressAnalyzer(),
            "barbell_row": BarbellRowAnalyzer(),
            "dumbbell_row": DumbbellRowAnalyzer(),
            "lat_pulldown": LatPulldownAnalyzer(),
            # Note: rear_delt_flies removed from registry - keeping file for backward compatibility
        }
    
    async def analyze(self, pose_data: List[Dict], lift_type: Optional[str] = None) -> AnalysisResult:
        if not lift_type:
            lift_type = "back_squat"
        
        if lift_type not in self.lift_analyzers:
            raise ValueError(f"Unsupported lift type: {lift_type}")
        
        analyzer = self.lift_analyzers[lift_type]
        result = await analyzer.analyze(pose_data)
        result.lift_type = lift_type
        return result






