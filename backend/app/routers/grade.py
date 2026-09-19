from fastapi import APIRouter
from app.errors import ProblemNotFoundError
from app.schemas import GradeRequest, GradeResponse
from app.services.extract import extract_step_fields
from app.services.problems_repo import get_problem_by_id
from app.services.scorer import grade_steps

router = APIRouter(prefix="/api/grade", tags=["grade"])


@router.post("", response_model=GradeResponse)
async def grade_submission(request: GradeRequest):
    """Grade transcribed and confirmed student steps deterministically."""
    prob = get_problem_by_id(request.problem_id)
    if not prob:
        raise ProblemNotFoundError(problem_id=request.problem_id)

    # 1. Extract structured fields from student step texts
    extracted_steps = await extract_step_fields(request.steps)

    # 2. Grade deterministically using verify and scorer
    response = grade_steps(
        problem=prob,
        steps=extracted_steps,
        previous_results=request.previous_results,
    )

    return response
