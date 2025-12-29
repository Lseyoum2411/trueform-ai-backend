from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]
    MAX_UPLOAD_SIZE_MB: int = 100
    MAX_VIDEO_DURATION_SEC: int = 60
    UPLOAD_DIR: str = "uploads"
    RESULTS_DIR: str = "results"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# SUPPORTED_SPORTS defined here
SUPPORTED_SPORTS = ["basketball", "golf", "weightlifting", "baseball", "soccer", "track_field", "volleyball", "lacrosse"]

# Build EXERCISE_TYPES from movement registry (no circular dependency since registry doesn't import config)
from app.core.movements_registry import MOVEMENTS_REGISTRY

EXERCISE_TYPES = {}
for sport_id, movements in MOVEMENTS_REGISTRY.items():
    EXERCISE_TYPES[sport_id] = [movement.movement_id for movement in movements]

EXERCISE_ALIASES = {
    "squat": "barbell_squat",
    "back_squat": "barbell_squat",
    "bench": "bench_press",
    "row": "barbell_row",
    "db_row": "dumbbell_row",
    "dumbbell_row": "dumbbell_row",
    "pulldown": "lat_pulldown",
    "rdl": "romanian_deadlift",
    # Golf legacy mappings
    "driver": "driver_swing",
    "fairway": "iron_swing",
    "chip": "chip_shot",
    "putt": "putting_stroke",
    # Basketball legacy mappings
    "jumpshot": "shot_off_dribble",
}

# Weightlifting movement to analyzer mapping (normalized IDs)
LIFT_TYPE_MAPPING = {
    "barbell_squat": "back_squat",  # Maps to existing analyzer
    "back_squat": "back_squat",  # Legacy support
    "front_squat": "front_squat",
    "deadlift": "deadlift",
    "romanian_deadlift": "rdl",  # Maps to existing RDL analyzer
    "rdl": "rdl",  # Legacy support
    "bench_press": "bench_press",
    "barbell_row": "barbell_row",
    "dumbbell_row": "dumbbell_row",
    "lat_pulldown": "lat_pulldown",
}
