"""Vision transcription service for MarkLoss."""

import json
import logging
from pathlib import Path
from typing import List, Tuple
from app.config import settings
from app.errors import (
    FileTooLargeError,
    InvalidModelOutputError,
    LLMUnavailableError,
    UnsupportedFileError,
    UnreadableImageError,
)
from app.llm.client import get_llm_client
from app.llm.prompts import TRANSCRIPTION_SYSTEM_PROMPT
from app.schemas import TranscribedStep
from app.services.cache import (
    cache_transcription,
    compute_image_hash,
    get_cached_transcription,
)

logger = logging.getLogger("markloss.vision")

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "samples" / "fixtures"


def _load_sample_fixture(problem_id: str, filename: str = "") -> List[TranscribedStep]:
    """Load pre-recorded sample fixture for DEMO_MODE or offline safety."""
    target_file = None

    # 1. Problem-specific error/slip fixture
    if "slip" in filename or "wrong" in filename:
        cand = FIXTURES_DIR / f"{problem_id}-slip.json"
        if cand.exists():
            target_file = cand
        elif problem_id == "phy-ohm-01":
            target_file = FIXTURES_DIR / "phy-ohm-01-slip.json"

    # 2. Standard problem fixture
    if not target_file or not target_file.exists():
        cand = FIXTURES_DIR / f"{problem_id}.json"
        if cand.exists():
            target_file = cand

    # 3. Fallback to phy-ohm-01
    if not target_file or not target_file.exists():
        target_file = FIXTURES_DIR / "phy-ohm-01.json"

    if target_file and target_file.exists():
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [TranscribedStep.model_validate(s) for s in data.get("steps", [])]
        except Exception as e:
            logger.warning("Failed to load fixture %s: %s", target_file, e)

    # Minimal fallback steps if fixture load fails
    return [
        TranscribedStep(id=1, text="V = I * R", confidence=0.98, needs_confirmation=False),
        TranscribedStep(id=2, text="V = 0.5 * 20", confidence=0.95, needs_confirmation=False),
        TranscribedStep(id=3, text="V = 10 V", confidence=0.96, needs_confirmation=False),
    ]


async def transcribe_image(
    problem_id: str,
    image_bytes: bytes,
    mime_type: str,
    filename: str = "",
) -> Tuple[List[TranscribedStep], bool]:
    """Transcribe handwriting from image into numbered steps.

    Args:
        problem_id: The ID of the problem being answered.
        image_bytes: Raw bytes of the uploaded image.
        mime_type: File content MIME type.

    Returns:
        (steps, was_cached) tuple.
    """
    # 1. Validate file format
    if mime_type.lower() not in ALLOWED_MIME_TYPES:
        raise UnsupportedFileError(mime_type=mime_type)

    # 2. Validate file size
    size_bytes = len(image_bytes)
    if size_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
        raise FileTooLargeError(
            size_bytes=size_bytes,
            max_bytes=settings.MAX_UPLOAD_SIZE_BYTES,
        )

    # 3. Check in-memory hash cache
    img_hash = compute_image_hash(image_bytes)
    cached_steps = get_cached_transcription(img_hash)
    if cached_steps is not None:
        logger.info("Returning cached transcription for image hash: %s...", img_hash[:8])
        return cached_steps, True

    # 4. Check DEMO_MODE
    if settings.is_demo_mode:
        logger.info("DEMO_MODE active: loading fixture for problem %s (filename=%s)", problem_id, filename)
        fixture_steps = _load_sample_fixture(problem_id, filename)
        cache_transcription(img_hash, fixture_steps)
        return fixture_steps, False

    # 5. Live Vision LLM transcription
    client = get_llm_client()
    prompt = f"Transcribe this student's handwritten answer sheet for problem '{problem_id}'. Return numbered steps with confidence scores."

    try:
        data = await client.generate_vision_json(
            image_bytes=image_bytes,
            mime_type=mime_type,
            prompt=prompt,
            system_instruction=TRANSCRIPTION_SYSTEM_PROMPT,
            temperature=0.0,
        )
    except (LLMUnavailableError, InvalidModelOutputError, UnreadableImageError):
        raise
    except Exception as e:
        logger.error("Vision transcription error: %s", str(e))
        raise UnreadableImageError(detail=str(e))

    raw_steps = data.get("steps", [])
    if not raw_steps:
        raise UnreadableImageError(detail="Model returned no readable steps.")

    transcribed_steps: List[TranscribedStep] = []
    for s in raw_steps:
        conf = float(s.get("confidence", 0.9))
        step = TranscribedStep(
            id=int(s.get("id", len(transcribed_steps) + 1)),
            text=str(s.get("text", "")).strip(),
            confidence=conf,
            needs_confirmation=(conf < 0.75),
        )
        transcribed_steps.append(step)

    # Store in cache
    cache_transcription(img_hash, transcribed_steps)
    return transcribed_steps, False
