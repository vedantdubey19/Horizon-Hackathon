import io
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.errors import (
    ErrorCode,
    InvalidModelOutputError,
    LLMUnavailableError,
    UnreadableImageError,
)
from app.llm.client import LLMClient, set_llm_client
from app.main import app

client = TestClient(app)


class FailingLLMClient(LLMClient):
    """Mock client capable of simulating specific error modes."""

    def __init__(self, failure_mode: str):
        self.failure_mode = failure_mode

    async def generate_vision_json(self, *args, **kwargs):
        if self.failure_mode == "timeout":
            raise LLMUnavailableError(detail="AI model call timed out after 30.0s.")
        elif self.failure_mode == "unreadable":
            raise UnreadableImageError(detail="Handwriting completely illegible.")
        elif self.failure_mode == "invalid_json":
            raise InvalidModelOutputError(detail="Model returned truncated JSON.")
        return {"steps": []}

    async def generate_text_json(self, *args, **kwargs):
        if self.failure_mode == "timeout":
            raise LLMUnavailableError(detail="AI model call timed out after 30.0s.")
        elif self.failure_mode == "invalid_json":
            raise InvalidModelOutputError(detail="Invalid extraction JSON.")
        return {}


def test_unreadable_image_error_handling():
    set_llm_client(FailingLLMClient("unreadable"))
    orig_demo = settings.DEMO_MODE
    orig_key = settings.LLM_API_KEY
    try:
        settings.DEMO_MODE = False
        settings.LLM_API_KEY = "test_api_key_for_mock"

        res = client.post(
            "/api/transcribe",
            data={"problem_id": "phy-ohm-01"},
            files={"file": ("dark_photo.png", io.BytesIO(b"\x89PNG\r\n\x1a\nfake_unreadable"), "image/png")},
        )
        assert res.status_code == 422
        err = res.json()["error"]
        assert err["code"] == ErrorCode.UNREADABLE_IMAGE.value
        assert "clearer photo" in err["action"].lower()
    finally:
        settings.DEMO_MODE = orig_demo
        settings.LLM_API_KEY = orig_key
        set_llm_client(None)


def test_llm_timeout_unavailable_error():
    set_llm_client(FailingLLMClient("timeout"))
    orig_demo = settings.DEMO_MODE
    orig_key = settings.LLM_API_KEY
    try:
        settings.DEMO_MODE = False
        settings.LLM_API_KEY = "test_api_key_for_mock"

        res = client.post(
            "/api/transcribe",
            data={"problem_id": "phy-ohm-01"},
            files={"file": ("timeout.png", io.BytesIO(b"\x89PNG\r\n\x1a\nfake_timeout"), "image/png")},
        )
        assert res.status_code == 503
        err = res.json()["error"]
        assert err["code"] == ErrorCode.LLM_UNAVAILABLE.value
        assert "timed out" in err["message"].lower() or "unavailable" in err["message"].lower()
    finally:
        settings.DEMO_MODE = orig_demo
        settings.LLM_API_KEY = orig_key
        set_llm_client(None)


def test_invalid_model_output_error():
    set_llm_client(FailingLLMClient("invalid_json"))
    orig_demo = settings.DEMO_MODE
    orig_key = settings.LLM_API_KEY
    try:
        settings.DEMO_MODE = False
        settings.LLM_API_KEY = "test_api_key_for_mock"

        res = client.post(
            "/api/transcribe",
            data={"problem_id": "phy-ohm-01"},
            files={"file": ("bad_json.png", io.BytesIO(b"\x89PNG\r\n\x1a\nfake_bad_json"), "image/png")},
        )
        assert res.status_code == 502
        err = res.json()["error"]
        assert err["code"] == ErrorCode.INVALID_MODEL_OUTPUT.value
    finally:
        settings.DEMO_MODE = orig_demo
        settings.LLM_API_KEY = orig_key
        set_llm_client(None)


@pytest.mark.parametrize("bad_mime", ["application/pdf", "text/plain", "image/gif", "image/bmp"])
def test_unsupported_file_types_rejected(bad_mime):
    res = client.post(
        "/api/transcribe",
        data={"problem_id": "phy-ohm-01"},
        files={"file": ("bad_file", io.BytesIO(b"content"), bad_mime)},
    )
    assert res.status_code == 415
    err = res.json()["error"]
    assert err["code"] == ErrorCode.UNSUPPORTED_FILE.value
    assert "JPEG, PNG, or WebP" in err["action"]


def test_file_size_limit_enforced():
    oversized = b"x" * (settings.MAX_UPLOAD_SIZE_BYTES + 500)
    res = client.post(
        "/api/transcribe",
        data={"problem_id": "phy-ohm-01"},
        files={"file": ("huge.png", io.BytesIO(oversized), "image/png")},
    )
    assert res.status_code == 413
    err = res.json()["error"]
    assert err["code"] == ErrorCode.TOO_LARGE.value
    assert "exceeds" in err["message"].lower()


def test_low_confidence_step_marking():
    from app.services.vision import _load_sample_fixture

    # Test loading slip fixture with low confidence step
    steps = _load_sample_fixture("phy-ohm-01", filename="phy-ohm-01-slip.png")
    assert len(steps) == 3
    # Step 2 has confidence 0.70 < 0.75
    step_2 = next(s for s in steps if s.id == 2)
    assert step_2.confidence < 0.75
    assert step_2.needs_confirmation is True

    # Step 1 has confidence 0.98 >= 0.75
    step_1 = next(s for s in steps if s.id == 1)
    assert step_1.confidence >= 0.75
    assert step_1.needs_confirmation is False
