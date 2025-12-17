from typing import List, Dict, Optional
from app.core.analyzers.base import BaseAnalyzer
from app.core.analyzers.weightlifting.squat import SquatAnalyzer
from app.core.analyzers.weightlifting.front_squat import FrontSquatAnalyzer
from app.core.analyzers.weightlifting.deadlift import DeadliftAnalyzer
from app.core.analyzers.weightlifting.rdl import RDLAnalyzer
from app.core.analyzers.weightlifting.bench_press import BenchPressAnalyzer
from app.core.analyzers.weightlifting.barbell_row import BarbellRowAnalyzer
from app.core.analyzers.weightlifting.lat_pulldown import LatPulldownAnalyzer
from app.models.analysis import AnalysisResult


class WeightliftingAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()
        self.lift_analyzers = {
            "back_squat": SquatAnalyzer(),
            "front_squat": FrontSquatAnalyzer(),
            "deadlift": DeadliftAnalyzer(),
            "rdl": RDLAnalyzer(),
            "bench_press": BenchPressAnalyzer(),
            "barbell_row": BarbellRowAnalyzer(),
            "lat_pulldown": LatPulldownAnalyzer(),
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




