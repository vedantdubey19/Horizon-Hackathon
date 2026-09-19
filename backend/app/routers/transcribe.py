from fastapi import APIRouter, File, Form, UploadFile
from app.errors import ProblemNotFoundError
from app.schemas import TranscribeResponse
from app.services.problems_repo import get_problem_by_id
from app.services.vision import transcribe_image

router = APIRouter(prefix="/api/transcribe", tags=["transcribe"])


@router.post("", response_model=TranscribeResponse)
async def transcribe(
    problem_id: str = Form(...),
    file: UploadFile = File(...),
):
    """Transcribe handwriting from uploaded answer sheet image."""
    prob = get_problem_by_id(problem_id)
    if not prob:
        raise ProblemNotFoundError(problem_id=problem_id)

    content = await file.read()
    mime_type = file.content_type or "image/jpeg"

    steps, was_cached = await transcribe_image(
        problem_id=problem_id,
        image_bytes=content,
        mime_type=mime_type,
        filename=file.filename or "",
    )

    return TranscribeResponse(
        problem_id=problem_id,
        steps=steps,
        cached=was_cached,
    )
