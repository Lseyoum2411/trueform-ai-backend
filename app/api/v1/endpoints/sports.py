from fastapi import APIRouter, HTTPException
from app.models.sport import Sport, ExerciseType
from app.config import SUPPORTED_SPORTS
from app.core.movements_registry import MOVEMENTS_REGISTRY, get_movements_for_sport

router = APIRouter()


@router.get("", response_model=list[Sport])
async def get_sports():
    """Get all supported sports with their movements from the registry."""
    sports_data = []
    
    # Sport descriptions
    sport_descriptions = {
        "basketball": "Analyze shooting form and mechanics",
        "golf": "Analyze golf swing mechanics and posture",
        "weightlifting": "Analyze form for various lifts",
        "baseball": "Analyze baseball form and mechanics",
        "soccer": "Analyze soccer technique and form",
        "track_field": "Analyze running form and sprint mechanics",
        "volleyball": "Analyze volleyball technique and form",
    }
    
    # Sport display names (for proper formatting)
    sport_display_names = {
        "basketball": "Basketball",
        "golf": "Golf",
        "weightlifting": "Weightlifting",
        "baseball": "Baseball",
        "soccer": "Soccer",
        "track_field": "Track and Field",
        "volleyball": "Volleyball",
    }
    
    # Build sports from registry
    for sport_id in SUPPORTED_SPORTS:
        movements = get_movements_for_sport(sport_id)
        
        # Convert MovementDefinition to ExerciseType
        exercise_types = [
            ExerciseType(
                id=movement.movement_id,
                name=movement.display_name,
                description=movement.description
            )
            for movement in movements
        ]
        
        # Basketball requires exercise_type but has default
        requires_exercise_type = sport_id != "basketball" or len(exercise_types) > 1
        
        sports_data.append(
            Sport(
                id=sport_id,
                name=sport_display_names.get(sport_id, sport_id.replace("_", " ").title()),
                description=sport_descriptions.get(sport_id, f"Analyze {sport_id.replace('_', ' ')} form"),
                requires_exercise_type=requires_exercise_type,
                exercise_types=exercise_types,
            )
        )
    
    return sports_data


@router.get("/{sport_id}", response_model=Sport)
async def get_sport(sport_id: str):
    if sport_id not in SUPPORTED_SPORTS:
        raise HTTPException(status_code=404, detail="Sport not found")
    
    movements = get_movements_for_sport(sport_id)
    
    # Convert MovementDefinition to ExerciseType
    exercise_types = [
        ExerciseType(
            id=movement.movement_id,
            name=movement.display_name,
            description=movement.description
        )
        for movement in movements
    ]
    
    sport_descriptions = {
        "basketball": "Analyze shooting form and mechanics",
        "golf": "Analyze golf swing mechanics and posture",
        "weightlifting": "Analyze form for various lifts",
        "baseball": "Analyze baseball form and mechanics",
        "soccer": "Analyze soccer technique and form",
        "track_field": "Analyze running form and sprint mechanics",
        "volleyball": "Analyze volleyball technique and form",
    }
    
    requires_exercise_type = sport_id != "basketball" or len(exercise_types) > 1
    
    return Sport(
        id=sport_id,
        name=sport_id.replace("_", " ").title(),
        description=sport_descriptions.get(sport_id, f"Analyze {sport_id.replace('_', ' ')} form"),
        requires_exercise_type=requires_exercise_type,
        exercise_types=exercise_types,
    )

