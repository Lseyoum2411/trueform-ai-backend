from fastapi import APIRouter, HTTPException
from app.models.sport import Sport, ExerciseType
from app.config import SUPPORTED_SPORTS, EXERCISE_TYPES

router = APIRouter()


@router.get("", response_model=list[Sport])
async def get_sports():
    golf_exercises = [
        ExerciseType(id="driver", name="Driver", description="Full power drive from tee"),
        ExerciseType(id="fairway", name="Fairway Wood", description="Long distance fairway shot"),
        ExerciseType(id="chip", name="Chip Shot", description="Short approach shot near green"),
        ExerciseType(id="putt", name="Putt", description="Putting stroke on green"),
    ]
    
    weightlifting_exercises = [
        ExerciseType(id="back_squat", name="Back Squat", description="Barbell on upper back, full depth squat"),
        ExerciseType(id="front_squat", name="Front Squat", description="Barbell on front shoulders, squat"),
        ExerciseType(id="deadlift", name="Deadlift", description="Lift bar from ground to standing"),
        ExerciseType(id="rdl", name="Romanian Deadlift", description="Hip hinge movement with straight legs"),
        ExerciseType(id="bench_press", name="Bench Press", description="Horizontal press on bench"),
        ExerciseType(id="barbell_row", name="Barbell Row", description="Bent-over rowing movement"),
        ExerciseType(id="dumbbell_row", name="Dumbbell Row", description="Single or two-arm dumbbell row"),
        ExerciseType(id="rear_delt_flies", name="Rear Delt Flies", description="Rear deltoid isolation exercise"),
        ExerciseType(id="lat_pulldown", name="Lat Pulldown", description="Vertical pulling movement"),
    ]
    
    baseball_exercises = [
        ExerciseType(id="pitching", name="Pitching", description="Analyze pitching form and mechanics"),
        ExerciseType(id="batting", name="Batting", description="Analyze batting stance and swing"),
        ExerciseType(id="catcher", name="Catcher", description="Analyze catching form and positioning"),
        ExerciseType(id="fielding", name="Fielding", description="Analyze fielding stance and mechanics"),
    ]
    
    sports_data = [
        Sport(
            id="basketball",
            name="Basketball",
            description="Analyze jump shot form using Steph Curry and Lethal Shooter biomechanics",
            requires_exercise_type=False,
            exercise_types=[
                ExerciseType(id="jumpshot", name="Jump Shot", description="Standard jump shot form analysis")
            ],
        ),
        Sport(
            id="golf",
            name="Golf",
            description="Analyze golf swing mechanics and posture",
            requires_exercise_type=True,
            exercise_types=golf_exercises,
        ),
        Sport(
            id="weightlifting",
            name="Weightlifting",
            description="Analyze form for various lifts",
            requires_exercise_type=True,
            exercise_types=weightlifting_exercises,
        ),
        Sport(
            id="baseball",
            name="Baseball",
            description="Analyze baseball form and mechanics",
            requires_exercise_type=True,
            exercise_types=baseball_exercises,
        ),
    ]
    return sports_data


@router.get("/{sport_id}", response_model=Sport)
async def get_sport(sport_id: str):
    if sport_id not in SUPPORTED_SPORTS:
        raise HTTPException(status_code=404, detail="Sport not found")
    
    golf_exercises = [
        ExerciseType(id="driver", name="Driver", description="Full power drive from tee"),
        ExerciseType(id="fairway", name="Fairway Wood", description="Long distance fairway shot"),
        ExerciseType(id="chip", name="Chip Shot", description="Short approach shot near green"),
        ExerciseType(id="putt", name="Putt", description="Putting stroke on green"),
    ]
    
    weightlifting_exercises = [
        ExerciseType(id="back_squat", name="Back Squat", description="Barbell on upper back, full depth squat"),
        ExerciseType(id="front_squat", name="Front Squat", description="Barbell on front shoulders, squat"),
        ExerciseType(id="deadlift", name="Deadlift", description="Lift bar from ground to standing"),
        ExerciseType(id="rdl", name="Romanian Deadlift", description="Hip hinge movement with straight legs"),
        ExerciseType(id="bench_press", name="Bench Press", description="Horizontal press on bench"),
        ExerciseType(id="barbell_row", name="Barbell Row", description="Bent-over rowing movement"),
        ExerciseType(id="dumbbell_row", name="Dumbbell Row", description="Single or two-arm dumbbell row"),
        ExerciseType(id="rear_delt_flies", name="Rear Delt Flies", description="Rear deltoid isolation exercise"),
        ExerciseType(id="lat_pulldown", name="Lat Pulldown", description="Vertical pulling movement"),
    ]
    
    baseball_exercises = [
        ExerciseType(id="pitching", name="Pitching", description="Analyze pitching form and mechanics"),
        ExerciseType(id="batting", name="Batting", description="Analyze batting stance and swing"),
        ExerciseType(id="catcher", name="Catcher", description="Analyze catching form and positioning"),
        ExerciseType(id="fielding", name="Fielding", description="Analyze fielding stance and mechanics"),
    ]
    
    if sport_id == "basketball":
        return Sport(
            id="basketball",
            name="Basketball",
            description="Analyze jump shot form using Steph Curry and Lethal Shooter biomechanics",
            requires_exercise_type=False,
            exercise_types=[
                ExerciseType(id="jumpshot", name="Jump Shot", description="Standard jump shot form analysis")
            ],
        )
    elif sport_id == "golf":
        return Sport(
            id="golf",
            name="Golf",
            description="Analyze golf swing mechanics and posture",
            requires_exercise_type=True,
            exercise_types=golf_exercises,
        )
    elif sport_id == "weightlifting":
        return Sport(
            id="weightlifting",
            name="Weightlifting",
            description="Analyze form for various lifts",
            requires_exercise_type=True,
            exercise_types=weightlifting_exercises,
        )
    elif sport_id == "baseball":
        return Sport(
            id="baseball",
            name="Baseball",
            description="Analyze baseball form and mechanics",
            requires_exercise_type=True,
            exercise_types=baseball_exercises,
        )
    
    raise HTTPException(status_code=404, detail="Sport not found")

