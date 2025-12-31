from pydantic import BaseModel
from typing import List, Optional


class ExerciseType(BaseModel):
    id: str
    name: str
    description: str


class Sport(BaseModel):
    id: str
    name: str
    description: str
    requires_exercise_type: bool = False
    exercise_types: Optional[List[ExerciseType]] = None
    lift_types: Optional[List[str]] = None


class SportListResponse(BaseModel):
    sports: List[Sport]

