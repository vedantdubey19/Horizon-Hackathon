from fastapi import APIRouter
from app.errors import MarkLossError, ErrorCode, ProblemNotFoundError
from app.schemas import HintRequest, HintResponse
from app.services.hints import generate_hint
from app.services.problems_repo import get_problem_by_id

router = APIRouter(prefix="/api/hint", tags=["hint"])


@router.post("", response_model=HintResponse)
async def request_hint(request: HintRequest):
    """Generate a pedagogical leak-guarded hint for a failed rubric check."""
    prob = get_problem_by_id(request.problem_id)
    if not prob:
        raise ProblemNotFoundError(problem_id=request.problem_id)

    rubric_item = next((r for r in prob.rubric if r.id == request.rule_id), None)
    if not rubric_item:
        raise MarkLossError(
            code=ErrorCode.INVALID_MODEL_OUTPUT,
            message=f"Rubric rule '{request.rule_id}' not found in problem '{request.problem_id}'.",
            action="Please select a valid rubric check.",
            status_code=404,
        )

    response = await generate_hint(
        problem=prob,
        item=rubric_item,
        step_text=request.step_text,
        level=request.level,
    )

    return response
