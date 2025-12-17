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

SUPPORTED_SPORTS = ["basketball", "golf", "weightlifting"]

EXERCISE_TYPES = {
    "basketball": ["jumpshot"],
    "golf": ["driver", "fairway", "chip", "putt"],
    "weightlifting": [
        "back_squat", "front_squat", "deadlift", "rdl",
        "bench_press", "barbell_row", "lat_pulldown"
    ],
}

EXERCISE_ALIASES = {
    "squat": "back_squat",
    "bench": "bench_press",
    "row": "barbell_row",
    "pulldown": "lat_pulldown",
}

LIFT_TYPE_MAPPING = {
    "back_squat": "back_squat",
    "front_squat": "front_squat",
    "deadlift": "deadlift",
    "rdl": "rdl",
    "bench_press": "bench_press",
    "barbell_row": "barbell_row",
    "lat_pulldown": "lat_pulldown",
}

