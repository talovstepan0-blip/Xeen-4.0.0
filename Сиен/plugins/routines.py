# Файл: plugins/routines.py
"""
Плагин тренировок - список упражнений
"""

DEFAULT_EXERCISES = [
    {"name": "Push-ups", "sets": 3, "reps": 15},
    {"name": "Squats", "sets": 3, "reps": 20},
    {"name": "Plank", "sets": 3, "duration": "60s"},
    {"name": "Lunges", "sets": 3, "reps": 12}
]


def execute(params: dict) -> dict:
    """Управление тренировками"""
    action = params.get("action", "list")
    
    if action == "list":
        return {"status": "success", "exercises": DEFAULT_EXERCISES}
    elif action == "add":
        return add_exercise(params)
    else:
        return {"status": "error", "message": "Unknown action"}


def add_exercise(params: dict) -> dict:
    exercise = {
        "name": params.get("name", ""),
        "sets": params.get("sets", 3),
        "reps": params.get("reps", 10)
    }
    DEFAULT_EXERCISES.append(exercise)
    return {"status": "success", "exercise": exercise}
