import io
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.llm.client import LLMClient, set_llm_client
from app.main import app

client = TestClient(app)


class MockLLMClient(LLMClient):
    """Mock LLM client returning controlled responses for testing."""

    async def generate_vision_json(self, *args, **kwargs):
        return {
            "steps": [
                {"id": 1, "text": "V = I * R", "confidence": 0.98},
                {"id": 2, "text": "V = 0.5 * 20", "confidence": 0.95},
                {"id": 3, "text": "V = 10 V", "confidence": 0.97},
            ]
        }

    async def generate_text_json(self, prompt, system_instruction, *args, **kwargs):
        if "extract" in system_instruction.lower():
            return {
                "steps": [
                    {"step_id": 1, "formula": "V = I * R", "substitutions": {}, "result": None},
                    {"step_id": 2, "formula": None, "substitutions": {"I": 0.5, "R": 20.0}, "result": None},
                    {"step_id": 3, "formula": None, "substitutions": {}, "result": {"value": 10.0, "unit": "V"}},
                ]
            }
        # Hint generation
        return {"hint": "Check the multiplication of current and resistance."}


@pytest.fixture(autouse=True)
def setup_mock_llm():
    set_llm_client(MockLLMClient())
    yield
    set_llm_client(None)


def test_health_check():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"


def test_list_problems_shields_rubrics():
    res = client.get("/api/problems")
    assert res.status_code == 200
    problems = res.json()
    assert len(problems) == 15

    for p in problems:
        # Strict security rule: rubric and expected answers must NEVER be sent to client
        assert "rubric" not in p
        assert "expected" not in p
        assert "statement" in p
        assert "total_marks" in p


def test_get_single_problem_and_not_found():
    res = client.get("/api/problems/phy-ohm-01")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "phy-ohm-01"
    assert "rubric" not in data
    assert "expected" not in data

    # Negative test: nonexistent problem
    res_404 = client.get("/api/problems/non-existent-problem")
    assert res_404.status_code == 404
    err = res_404.json()["error"]
    assert err["code"] == "PROBLEM_NOT_FOUND"


def test_transcribe_endpoint_valid_image():
    # Read sample png
    with open("samples/images/ohm_correct.png", "rb") as f:
        img_bytes = f.read()

    res = client.post(
        "/api/transcribe",
        data={"problem_id": "phy-ohm-01"},
        files={"file": ("ohm_correct.png", io.BytesIO(img_bytes), "image/png")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["problem_id"] == "phy-ohm-01"
    assert len(data["steps"]) >= 3
    assert data["steps"][0]["text"] == "V = I * R"


def test_transcribe_unsupported_file_type():
    res = client.post(
        "/api/transcribe",
        data={"problem_id": "phy-ohm-01"},
        files={"file": ("notes.txt", io.BytesIO(b"random text"), "text/plain")},
    )
    assert res.status_code == 415
    err = res.json()["error"]
    assert err["code"] == "UNSUPPORTED_FILE"


def test_transcribe_file_too_large():
    # Simulate oversized file (> 5MB)
    fake_large_bytes = b"0" * (settings.MAX_UPLOAD_SIZE_BYTES + 1024)
    res = client.post(
        "/api/transcribe",
        data={"problem_id": "phy-ohm-01"},
        files={"file": ("large.png", io.BytesIO(fake_large_bytes), "image/png")},
    )
    assert res.status_code == 413
    err = res.json()["error"]
    assert err["code"] == "TOO_LARGE"


def test_grade_endpoint_correct_flow():
    payload = {
        "problem_id": "phy-ohm-01",
        "steps": [
            {"id": 1, "text": "V = I * R"},
            {"id": 2, "text": "V = 0.5 * 20"},
            {"id": 3, "text": "V = 10 V"},
        ],
    }
    res = client.post("/api/grade", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 4
    assert data["max_total"] == 4
    assert len(data["results"]) == 4
    assert all(r["awarded"] == 1 for r in data["results"])


def test_grade_endpoint_with_recovery_diff():
    # Initial attempt with arithmetic slip
    initial_payload = {
        "problem_id": "phy-ohm-01",
        "steps": [
            {"id": 1, "text": "V = I * R"},
            {"id": 2, "text": "V = 0.5 * 20"},
            {"id": 3, "text": "V = 9 V"},
        ],
    }
    res1 = client.post("/api/grade", json=initial_payload)
    data1 = res1.json()
    assert data1["total"] == 3

    # Retry submission with corrected step and previous_results included
    retry_payload = {
        "problem_id": "phy-ohm-01",
        "steps": [
            {"id": 1, "text": "V = I * R"},
            {"id": 2, "text": "V = 0.5 * 20"},
            {"id": 3, "text": "V = 10 V"},
        ],
        "previous_results": data1["results"],
    }
    res2 = client.post("/api/grade", json=retry_payload)
    data2 = res2.json()
    assert data2["total"] == 4
    calc_res = next(r for r in data2["results"] if r["rule_id"] == "calculation")
    assert calc_res["awarded"] == 1
    assert calc_res["is_recovered"] is True


def test_hint_endpoint():
    payload = {
        "problem_id": "phy-ohm-01",
        "rule_id": "substitution",
        "step_text": "V = 0.5 * 2",
        "level": 2,
    }
    res = client.post("/api/hint", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["rule_id"] == "substitution"
    assert data["level"] == 2
    assert "hint" in data
    assert len(data["hint"]) > 0
