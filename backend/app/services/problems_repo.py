import json
from pathlib import Path
from typing import Dict, List, Optional
from app.schemas import Problem, ProblemSummary

_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "problems"
_PROBLEMS_CACHE: Optional[Dict[str, Problem]] = None


def load_problems() -> Dict[str, Problem]:
    global _PROBLEMS_CACHE
    if _PROBLEMS_CACHE is not None:
        return _PROBLEMS_CACHE

    problems: Dict[str, Problem] = {}
    for filename in ["physics.json", "math.json"]:
        file_path = _DATA_DIR / filename
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    prob = Problem.model_validate(item)
                    problems[prob.id] = prob
    _PROBLEMS_CACHE = problems
    return _PROBLEMS_CACHE


def get_all_problems() -> List[Problem]:
    return list(load_problems().values())


def get_problem_by_id(problem_id: str) -> Optional[Problem]:
    return load_problems().get(problem_id)


def get_problem_summaries() -> List[ProblemSummary]:
    summaries: List[ProblemSummary] = []
    for prob in load_problems().values():
        total_marks = sum(item.marks for item in prob.rubric)
        summaries.append(
            ProblemSummary(
                id=prob.id,
                subject=prob.subject,
                grade=prob.grade,
                statement=prob.statement,
                total_marks=total_marks,
            )
        )
    return summaries
