"""
Centralized Movement Registry for FormLab
Defines all supported sports and movements with their metadata
"""
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class MovementDefinition:
    """Definition of a single movement"""
    movement_id: str
    display_name: str
    description: str
    requires_equipment: bool = False
    key_phases: Optional[List[str]] = None


# Movement registry organized by sport
MOVEMENTS_REGISTRY: Dict[str, List[MovementDefinition]] = {
    "basketball": [
        MovementDefinition(
            movement_id="catch_and_shoot",
            display_name="Catch and Shoot",
            description="Shooting immediately after receiving a pass",
            requires_equipment=True,
            key_phases=["setup", "catch", "load", "release", "follow-through"]
        ),
        MovementDefinition(
            movement_id="shot_off_dribble",
            display_name="Shot Off the Dribble",
            description="Creating and shooting a jumpshot after dribbling",
            requires_equipment=True,
            key_phases=["setup", "dribble", "load", "execution", "release", "follow-through"]
        ),
        MovementDefinition(
            movement_id="free_throw",
            display_name="Free Throw",
            description="Shooting from the free throw line with no defenders",
            requires_equipment=True,
            key_phases=["setup", "preparation", "release", "follow-through"]
        ),
    ],
    "golf": [
        MovementDefinition(
            movement_id="driver_swing",
            display_name="Driver Swing",
            description="Full power drive from tee",
            requires_equipment=True,
            key_phases=["setup", "backswing", "downswing", "impact", "follow-through"]
        ),
        MovementDefinition(
            movement_id="iron_swing",
            display_name="Iron Swing",
            description="Iron shot swing with controlled trajectory",
            requires_equipment=True,
            key_phases=["setup", "backswing", "downswing", "impact", "follow-through"]
        ),
        MovementDefinition(
            movement_id="chip_shot",
            display_name="Chip Shot",
            description="Short approach shot near the green",
            requires_equipment=True,
            key_phases=["setup", "backswing", "impact", "follow-through"]
        ),
        MovementDefinition(
            movement_id="putting_stroke",
            display_name="Putting Stroke",
            description="Putting stroke on the green",
            requires_equipment=True,
            key_phases=["setup", "backstroke", "forward_stroke", "follow-through"]
        ),
    ],
    "weightlifting": [
        MovementDefinition(
            movement_id="barbell_squat",
            display_name="Barbell Squat",
            description="Squat with barbell on upper back",
            requires_equipment=True,
            key_phases=["setup", "descent", "bottom", "ascent"]
        ),
        MovementDefinition(
            movement_id="front_squat",
            display_name="Front Squat",
            description="Squat with barbell on front shoulders",
            requires_equipment=True,
            key_phases=["setup", "descent", "bottom", "ascent"]
        ),
        MovementDefinition(
            movement_id="deadlift",
            display_name="Deadlift",
            description="Lift bar from ground to standing position",
            requires_equipment=True,
            key_phases=["setup", "lift", "lockout", "lower"]
        ),
        MovementDefinition(
            movement_id="romanian_deadlift",
            display_name="Romanian Deadlift",
            description="Hip hinge movement with relatively straight legs",
            requires_equipment=True,
            key_phases=["setup", "descent", "stretch", "ascent"]
        ),
        MovementDefinition(
            movement_id="bench_press",
            display_name="Bench Press",
            description="Horizontal press on bench",
            requires_equipment=True,
            key_phases=["setup", "descent", "bottom", "ascent"]
        ),
        MovementDefinition(
            movement_id="barbell_row",
            display_name="Barbell Row",
            description="Bent-over rowing movement with barbell",
            requires_equipment=True,
            key_phases=["setup", "pull", "squeeze", "lower"]
        ),
        MovementDefinition(
            movement_id="dumbbell_row",
            display_name="Dumbbell Row",
            description="Single or two-arm dumbbell row",
            requires_equipment=True,
            key_phases=["setup", "pull", "squeeze", "lower"]
        ),
        MovementDefinition(
            movement_id="lat_pulldown",
            display_name="Lat Pulldown",
            description="Vertical pulling movement using cable machine",
            requires_equipment=True,
            key_phases=["setup", "pull", "squeeze", "return"]
        ),
    ],
    "baseball": [
        MovementDefinition(
            movement_id="pitching",
            display_name="Pitching",
            description="Pitching form and mechanics",
            requires_equipment=True,
            key_phases=["windup", "stride", "arm_cocking", "acceleration", "release", "follow-through"]
        ),
        MovementDefinition(
            movement_id="batting",
            display_name="Batting",
            description="Batting stance and swing mechanics",
            requires_equipment=True,
            key_phases=["stance", "load", "stride", "swing", "contact", "follow-through"]
        ),
        MovementDefinition(
            movement_id="catcher",
            display_name="Catcher",
            description="Catching form and positioning",
            requires_equipment=True,
            key_phases=["stance", "receiving", "blocking", "throwing"]
        ),
        MovementDefinition(
            movement_id="fielding",
            display_name="Fielding",
            description="Fielding stance and mechanics",
            requires_equipment=True,
            key_phases=["ready_position", "approach", "fielding", "throwing"]
        ),
    ],
    "soccer": [
        MovementDefinition(
            movement_id="shooting_technique",
            display_name="Shooting Technique",
            description="Shooting the ball at goal",
            requires_equipment=True,
            key_phases=["approach", "plant_foot", "strike", "follow-through"]
        ),
        MovementDefinition(
            movement_id="passing_technique",
            display_name="Passing Technique",
            description="Passing the ball to a teammate",
            requires_equipment=True,
            key_phases=["approach", "plant_foot", "contact", "follow-through"]
        ),
        MovementDefinition(
            movement_id="crossing_technique",
            display_name="Crossing Technique",
            description="Crossing the ball from wide areas",
            requires_equipment=True,
            key_phases=["approach", "plant_foot", "strike", "follow-through"]
        ),
        MovementDefinition(
            movement_id="dribbling",
            display_name="Dribbling",
            description="Controlling and moving the ball while running",
            requires_equipment=True,
            key_phases=["approach", "touch", "acceleration", "control"]
        ),
        MovementDefinition(
            movement_id="first_touch",
            display_name="First Touch",
            description="Controlling the ball when receiving a pass",
            requires_equipment=True,
            key_phases=["positioning", "first_touch", "control", "setup"]
        ),
    ],
    "track_field": [
        MovementDefinition(
            movement_id="sprint_start",
            display_name="Sprint Start",
            description="Starting technique from blocks",
            requires_equipment=True,
            key_phases=["set_position", "on_your_marks", "drive_phase", "transition"]
        ),
        MovementDefinition(
            movement_id="acceleration_phase",
            display_name="Acceleration Phase",
            description="Accelerating from start to top speed",
            requires_equipment=False,
            key_phases=["drive", "push", "extension", "recovery"]
        ),
        MovementDefinition(
            movement_id="max_velocity_sprint",
            display_name="Max Velocity Sprint",
            description="Maintaining maximum sprint speed",
            requires_equipment=False,
            key_phases=["upright_position", "ground_contact", "push_off", "recovery"]
        ),
        MovementDefinition(
            movement_id="shot_put",
            display_name="Shot Put",
            description="Analyze lower-body drive, hip rotation, and release mechanics",
            requires_equipment=True,
            key_phases=["setup", "glide", "rotation", "release", "follow-through"]
        ),
        MovementDefinition(
            movement_id="discus_throw",
            display_name="Discus Throw",
            description="Analyze rotational balance, sequencing, and release angle",
            requires_equipment=True,
            key_phases=["setup", "windup", "rotation", "release", "follow-through"]
        ),
        MovementDefinition(
            movement_id="javelin_throw",
            display_name="Javelin Throw",
            description="Analyze approach mechanics, torso separation, and throwing motion",
            requires_equipment=True,
            key_phases=["approach", "crossover", "plant", "release", "follow-through"]
        ),
        MovementDefinition(
            movement_id="hurdle_technique",
            display_name="Hurdle Technique",
            description="Analyze lead-leg mechanics, clearance efficiency, and rhythm",
            requires_equipment=True,
            key_phases=["approach", "takeoff", "clearance", "landing", "recovery"]
        ),
    ],
    "lacrosse": [
        MovementDefinition(
            movement_id="shooting",
            display_name="Shooting",
            description="Analyze lacrosse shooting mechanics, body alignment, rotational sequencing, and release mechanics",
            requires_equipment=True,
            key_phases=["setup", "windup", "rotation", "release", "follow-through"]
        ),
    ],
    "volleyball": [
        MovementDefinition(
            movement_id="spike_approach",
            display_name="Spike Approach",
            description="Approach and jumping for a spike attack",
            requires_equipment=True,
            key_phases=["approach", "plant", "jump", "arm_swing", "contact", "landing"]
        ),
        MovementDefinition(
            movement_id="jump_serve",
            display_name="Jump Serve",
            description="Serving with a jump and power",
            requires_equipment=True,
            key_phases=["toss", "approach", "jump", "contact", "follow-through", "landing"]
        ),
        MovementDefinition(
            movement_id="blocking_jump",
            display_name="Blocking Jump",
            description="Jumping to block opponent's attack",
            requires_equipment=True,
            key_phases=["ready_position", "approach", "jump", "reach", "landing"]
        ),
    ],
}


def get_movements_for_sport(sport_id: str) -> List[MovementDefinition]:
    """Get all movements for a given sport"""
    return MOVEMENTS_REGISTRY.get(sport_id, [])


def get_movement(sport_id: str, movement_id: str) -> Optional[MovementDefinition]:
    """Get a specific movement by sport and movement ID"""
    movements = get_movements_for_sport(sport_id)
    for movement in movements:
        if movement.movement_id == movement_id:
            return movement
    return None


def get_all_sports() -> List[str]:
    """Get list of all supported sport IDs"""
    return list(MOVEMENTS_REGISTRY.keys())


# Legacy ID mappings for backward compatibility
LEGACY_MOVEMENT_MAPPINGS: Dict[str, Dict[str, str]] = {
    "basketball": {
        "jumpshot": "shot_off_dribble",  # Map old jumpshot to shot off dribble
    },
    "golf": {
        "driver": "driver_swing",
        "fairway": "iron_swing",  # Map fairway to iron swing
        "chip": "chip_shot",
        "putt": "putting_stroke",
    },
    "weightlifting": {
        "back_squat": "barbell_squat",
        "front_squat": "front_squat",
        "deadlift": "deadlift",
        "rdl": "romanian_deadlift",
        "bench_press": "bench_press",
        "barbell_row": "barbell_row",
        "dumbbell_row": "dumbbell_row",
        "lat_pulldown": "lat_pulldown",
    },
}


def normalize_movement_id(sport_id: str, movement_id: str) -> str:
    """Normalize legacy movement IDs to new standardized IDs"""
    if sport_id in LEGACY_MOVEMENT_MAPPINGS:
        return LEGACY_MOVEMENT_MAPPINGS[sport_id].get(movement_id, movement_id)
    return movement_id

