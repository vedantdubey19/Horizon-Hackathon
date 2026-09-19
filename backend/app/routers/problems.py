from typing import List
from fastapi import APIRouter
from app.errors import ProblemNotFoundError
from app.schemas import ProblemSummary
from app.services.problems_repo import get_problem_by_id, get_problem_summaries

router = APIRouter(prefix="/api/problems", tags=["problems"])


@router.get("", response_model=List[ProblemSummary])
async def list_problems():
    """Retrieve problem summaries (rubric and expected results are NEVER sent to the client)."""
    return get_problem_summaries()


@router.get("/{problem_id}", response_model=ProblemSummary)
async def get_problem(problem_id: str):
    """Retrieve single problem summary by ID."""
    prob = get_problem_by_id(problem_id)
    if not prob:
        raise ProblemNotFoundError(problem_id=problem_id)

    total_marks = sum(item.marks for item in prob.rubric)
    return ProblemSummary(
        id=prob.id,
        subject=prob.subject,
        grade=prob.grade,
        statement=prob.statement,
        total_marks=total_marks,
    )
