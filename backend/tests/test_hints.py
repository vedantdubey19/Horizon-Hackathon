import pytest
from app.schemas import CheckType
from app.services.hints import (
    detect_leak,
    get_safe_fallback_hint,
    _extract_leak_targets,
)
from app.services.problems_repo import get_problem_by_id


def test_leak_guard_detects_numeric_targets():
    prob = get_problem_by_id("phy-ohm-01")
    calc_item = next(r for r in prob.rubric if r.id == "calculation")
    targets = _extract_leak_targets(prob, calc_item)

    assert "10" in targets or "10.0" in targets
    assert "20" in targets or "20.0" in targets

    # Positive leak test: hint says the target number
    leaking_hint_1 = "You need to multiply 0.5 by 20 to get 10."
    assert detect_leak(leaking_hint_1, targets) is True

    leaking_hint_2 = "The potential difference should be 10V."
    assert detect_leak(leaking_hint_2, targets) is True

    # Negative test: safe pedagogical hint without the answer
    safe_hint = "Make sure you multiply the current by the resistance carefully."
    assert detect_leak(safe_hint, targets) is False


def test_leak_guard_unit_trap():
    prob = get_problem_by_id("phy-trap-07")
    calc_item = next(r for r in prob.rubric if r.id == "calculation")
    targets = _extract_leak_targets(prob, calc_item)

    assert "20000" in targets or "20000.0" in targets

    leaking_hint = "After dividing 50 by 0.0025 you will get 20000 Pa."
    assert detect_leak(leaking_hint, targets) is True

    safe_hint = "Remember that area in cm² needs to be converted to standard m² before dividing."
    assert detect_leak(safe_hint, targets) is False


def test_safe_fallback_templates_coverage():
    # Verify every check type has valid non-empty templates for levels 1, 2, 3
    prob = get_problem_by_id("phy-ohm-01")
    targets = _extract_leak_targets(prob)

    for ct in CheckType:
        for lvl in [1, 2, 3]:
            hint = get_safe_fallback_hint(ct, lvl)
            assert isinstance(hint, str)
            assert len(hint) > 10
            # Ensure no target numbers leak in fallback templates
            assert detect_leak(hint, targets) is False


@pytest.mark.asyncio
async def test_generate_hint_demo_mode():
    from app.services.hints import generate_hint

    prob = get_problem_by_id("phy-ohm-01")
    sub_item = next(r for r in prob.rubric if r.id == "substitution")

    # Level 1 hint
    h1 = await generate_hint(prob, sub_item, "V = 0.5 * 2", 1)
    assert h1.level == 1
    assert h1.max_level_reached is False
    assert len(h1.hint) > 0

    # Level 3 hint (max level reached)
    h3 = await generate_hint(prob, sub_item, "V = 0.5 * 2", 3)
    assert h3.level == 3
    assert h3.max_level_reached is True
