import pytest
from app.schemas import ExtractedStep, StepResult
from app.services.problems_repo import get_problem_by_id
from app.services.scorer import grade_steps


def test_correct_answer_full_marks():
    prob = get_problem_by_id("phy-ohm-01")
    steps = [
        ExtractedStep(
            step_id=1,
            formula="V = I * R",
            substitutions={},
            result=None,
            raw="V = I * R",
        ),
        ExtractedStep(
            step_id=2,
            formula=None,
            substitutions={"I": 0.5, "R": 20.0},
            result=None,
            raw="V = 0.5 * 20",
        ),
        ExtractedStep(
            step_id=3,
            formula=None,
            substitutions={},
            result=StepResult(value=10.0, unit="V"),
            raw="V = 10 V",
        ),
    ]

    res = grade_steps(prob, steps)
    assert res.total == 4
    assert res.max_total == 4
    assert all(r.awarded == 1 for r in res.results)


def test_rearranged_formula():
    prob = get_problem_by_id("phy-ohm-01")
    steps = [
        ExtractedStep(
            step_id=1,
            formula="I = V / R",
            substitutions={},
            result=None,
            raw="I = V / R",
        ),
        ExtractedStep(
            step_id=2,
            formula=None,
            substitutions={"I": 0.5, "R": 20.0},
            result=None,
            raw="0.5 = V / 20",
        ),
        ExtractedStep(
            step_id=3,
            formula=None,
            substitutions={},
            result=StepResult(value=10.0, unit="V"),
            raw="V = 10 V",
        ),
    ]

    res = grade_steps(prob, steps)
    formula_item = next(r for r in res.results if r.rule_id == "formula")
    assert formula_item.awarded == 1
    assert any(k in formula_item.reason.lower() for k in ["rearrangement", "matches", "equivalent"])


def test_wrong_substitution_with_follow_through():
    prob = get_problem_by_id("phy-ohm-01")
    # Student substitutes R = 2.0 instead of 20.0
    # Then correctly computes 0.5 * 2.0 = 1.0 V
    steps = [
        ExtractedStep(
            step_id=1,
            formula="V = I * R",
            substitutions={},
            result=None,
            raw="V = I * R",
        ),
        ExtractedStep(
            step_id=2,
            formula=None,
            substitutions={"I": 0.5, "R": 2.0},
            result=None,
            raw="V = 0.5 * 2",
        ),
        ExtractedStep(
            step_id=3,
            formula=None,
            substitutions={},
            result=StepResult(value=1.0, unit="V"),
            raw="V = 1 V",
        ),
    ]

    res = grade_steps(prob, steps)
    sub_res = next(r for r in res.results if r.rule_id == "substitution")
    calc_res = next(r for r in res.results if r.rule_id == "calculation")

    # Substitution loses mark
    assert sub_res.awarded == 0
    assert "Substitution: expected R = 20.0, found R = 2.0" in sub_res.reason

    # Calculation gains mark through follow-through
    assert calc_res.awarded == 1
    assert "Follow-through applied" in calc_res.reason
    assert res.total == 3  # 1 formula + 0 sub + 1 calc + 1 unit


def test_missing_unit():
    prob = get_problem_by_id("phy-ohm-01")
    steps = [
        ExtractedStep(
            step_id=1,
            formula="V = I * R",
            substitutions={},
            result=None,
            raw="V = I * R",
        ),
        ExtractedStep(
            step_id=2,
            formula=None,
            substitutions={"I": 0.5, "R": 20.0},
            result=None,
            raw="V = 0.5 * 20",
        ),
        ExtractedStep(
            step_id=3,
            formula=None,
            substitutions={},
            result=StepResult(value=10.0, unit=None),
            raw="V = 10",
        ),
    ]

    res = grade_steps(prob, steps)
    unit_res = next(r for r in res.results if r.rule_id == "unit")
    calc_res = next(r for r in res.results if r.rule_id == "calculation")

    assert calc_res.awarded == 1
    assert unit_res.awarded == 0
    assert "Unit: missing in final answer" in unit_res.reason
    assert res.total == 3


def test_right_answer_wrong_unit():
    prob = get_problem_by_id("phy-ohm-01")
    steps = [
        ExtractedStep(
            step_id=1,
            formula="V = I * R",
            substitutions={},
            result=None,
            raw="V = I * R",
        ),
        ExtractedStep(
            step_id=2,
            formula=None,
            substitutions={"I": 0.5, "R": 20.0},
            result=None,
            raw="V = 0.5 * 20",
        ),
        ExtractedStep(
            step_id=3,
            formula=None,
            substitutions={},
            result=StepResult(value=10.0, unit="A"),
            raw="V = 10 A",
        ),
    ]

    res = grade_steps(prob, steps)
    calc_res = next(r for r in res.results if r.rule_id == "calculation")
    unit_res = next(r for r in res.results if r.rule_id == "unit")

    # Calculation mark is independent of unit mark
    assert calc_res.awarded == 1
    assert unit_res.awarded == 0
    assert "Unit: Unit mismatch: expected V, found 'A'" in unit_res.reason


def test_arithmetic_slip():
    prob = get_problem_by_id("phy-ohm-01")
    steps = [
        ExtractedStep(
            step_id=1,
            formula="V = I * R",
            substitutions={},
            result=None,
            raw="V = I * R",
        ),
        ExtractedStep(
            step_id=2,
            formula=None,
            substitutions={"I": 0.5, "R": 20.0},
            result=None,
            raw="V = 0.5 * 20",
        ),
        ExtractedStep(
            step_id=3,
            formula=None,
            substitutions={},
            result=StepResult(value=9.5, unit="V"),
            raw="V = 9.5 V",
        ),
    ]

    res = grade_steps(prob, steps)
    calc_res = next(r for r in res.results if r.rule_id == "calculation")
    assert calc_res.awarded == 0
    assert "Calculation: expected 10.0, found 9.5" in calc_res.reason
    assert res.total == 3


def test_unparseable_line():
    prob = get_problem_by_id("phy-ohm-01")
    steps = [
        ExtractedStep(
            step_id=1,
            formula="??? @@@ %%%",
            substitutions={},
            result=None,
            raw="??? @@@ %%%",
        ),
        ExtractedStep(
            step_id=2,
            formula=None,
            substitutions={},
            result=None,
            raw="...",
        ),
    ]

    res = grade_steps(prob, steps)
    assert res.total == 0
    assert res.max_total == 4
    # No crashes, every item has an honest reason
    assert all(r.awarded == 0 for r in res.results)


def test_recovered_mark_detection():
    prob = get_problem_by_id("phy-ohm-01")
    # First attempt: arithmetic slip on calculation
    slip_steps = [
        ExtractedStep(
            step_id=1,
            formula="V = I * R",
            substitutions={},
            result=None,
            raw="V = I * R",
        ),
        ExtractedStep(
            step_id=2,
            formula=None,
            substitutions={"I": 0.5, "R": 20.0},
            result=None,
            raw="V = 0.5 * 20",
        ),
        ExtractedStep(
            step_id=3,
            formula=None,
            substitutions={},
            result=StepResult(value=9.0, unit="V"),
            raw="V = 9 V",
        ),
    ]
    res_1 = grade_steps(prob, slip_steps)
    calc_1 = next(r for r in res_1.results if r.rule_id == "calculation")
    assert calc_1.awarded == 0
    assert calc_1.is_recovered is False

    # Second attempt: student corrects arithmetic to 10
    corrected_steps = [
        ExtractedStep(
            step_id=1,
            formula="V = I * R",
            substitutions={},
            result=None,
            raw="V = I * R",
        ),
        ExtractedStep(
            step_id=2,
            formula=None,
            substitutions={"I": 0.5, "R": 20.0},
            result=None,
            raw="V = 0.5 * 20",
        ),
        ExtractedStep(
            step_id=3,
            formula=None,
            substitutions={},
            result=StepResult(value=10.0, unit="V"),
            raw="V = 10 V",
        ),
    ]
    res_2 = grade_steps(prob, corrected_steps, previous_results=res_1.results)
    calc_2 = next(r for r in res_2.results if r.rule_id == "calculation")
    assert calc_2.awarded == 1
    assert calc_2.is_recovered is True
    # Formula and unit were already awarded in res_1, so is_recovered should be False for them
    formula_2 = next(r for r in res_2.results if r.rule_id == "formula")
    assert formula_2.is_recovered is False


def test_unit_trap_follow_through():
    prob = get_problem_by_id("phy-trap-07")
    # Student misses conversion: uses 25 cm^2 directly
    # P = 50 / 25 = 2 Pa
    steps = [
        ExtractedStep(
            step_id=1,
            formula=None,
            substitutions={},
            result=StepResult(value=25.0, unit="cm^2"),
            raw="A = 25 cm^2",
        ),
        ExtractedStep(
            step_id=2,
            formula="P = F / A",
            substitutions={},
            result=None,
            raw="P = F / A",
        ),
        ExtractedStep(
            step_id=3,
            formula=None,
            substitutions={"F": 50.0, "A": 25.0},
            result=None,
            raw="P = 50 / 25",
        ),
        ExtractedStep(
            step_id=4,
            formula=None,
            substitutions={},
            result=StepResult(value=2.0, unit="Pa"),
            raw="P = 2 Pa",
        ),
    ]

    res = grade_steps(prob, steps)
    conv_res = next(r for r in res.results if r.rule_id == "conversion")
    calc_res = next(r for r in res.results if r.rule_id == "calculation")

    # Conversion is lost
    assert conv_res.awarded == 0
    assert "Conversion: expected 0.0025, found 25.0" in conv_res.reason

    # Calculation is awarded via follow-through
    assert calc_res.awarded == 1
    assert "Follow-through applied" in calc_res.reason
