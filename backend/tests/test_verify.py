import pytest
from app.services.verify import (
    normalize_unit,
    verify_unit,
    verify_formula,
    verify_expression,
    verify_substitution,
    verify_numeric,
    safe_parse_expression,
)


def test_formula_exact_and_rearranged():
    accepted = ["V = I * R", "V = IR", "V = R * I"]
    # Exact match
    matched, reason = verify_formula("V = I * R", accepted)
    assert matched is True
    assert "matches" in reason.lower()

    # Rearranged form: I = V / R
    matched, reason = verify_formula("I = V / R", accepted)
    assert matched is True
    assert "rearrangement" in reason.lower() or "equivalent" in reason.lower()

    # Rearranged form: R = V / I
    matched, reason = verify_formula("R = V / I", accepted)
    assert matched is True

    # Implicit multiplication without space
    matched, reason = verify_formula("V = IR", accepted)
    assert matched is True


def test_formula_kinematics():
    accepted = ["v = u + a * t", "v - u = a * t", "a = (v - u) / t"]
    # Kinematics rearrangement
    matched, reason = verify_formula("a = (v - u) / t", accepted)
    assert matched is True

    # Kinematics second equation with caret power
    accepted_s = ["s = u * t + 0.5 * a * t**2"]
    matched, reason = verify_formula("s = u * t + 0.5 * a * t^2", accepted_s)
    assert matched is True


def test_formula_invalid_and_unparseable():
    accepted = ["V = I * R"]
    # Invalid formula relation
    matched, reason = verify_formula("V = I / R", accepted)
    assert matched is False

    # Unparseable syntax must not crash
    matched, reason = verify_formula("V = == /// &&%", accepted)
    assert matched is False
    assert "could not parse" in reason.lower()

    # Empty formula
    matched, reason = verify_formula("", accepted)
    assert matched is False


def test_numeric_checks():
    # Exact match
    matched, reason = verify_numeric(10.0, 10.0, 0.01)
    assert matched is True

    # Within tolerance
    matched, reason = verify_numeric(10.005, 10.0, 0.01)
    assert matched is True

    # Arithmetic slip outside tolerance
    matched, reason = verify_numeric(9.5, 10.0, 0.01)
    assert matched is False
    assert "expected 10.0, found 9.5" in reason

    # Multi-value targets (e.g. quadratic roots [3.0, 0.5])
    matched, _ = verify_numeric(3.0, [3.0, 0.5], 0.01)
    assert matched is True
    matched, _ = verify_numeric(0.5, [3.0, 0.5], 0.01)
    assert matched is True
    matched, reason = verify_numeric(2.0, [3.0, 0.5], 0.01)
    assert matched is False

    # Non-numeric input
    matched, reason = verify_numeric("abc", 10.0, 0.01)
    assert matched is False


def test_unit_normalization_and_verification():
    # Canonical Ohm
    assert normalize_unit("Ω") == "ohm"
    assert normalize_unit("Ohms") == "ohm"
    assert normalize_unit("ohm") == "ohm"

    # Canonical speed
    assert normalize_unit("m s^-1") == "m/s"
    assert normalize_unit("m/sec") == "m/s"
    assert normalize_unit("meters per second") == "m/s"

    # Canonical pressure
    assert normalize_unit("N/m^2") == "Pa"
    assert normalize_unit("pascal") == "Pa"

    # Unit verification against accepted list
    accepted_v = ["V", "volt", "volts"]
    matched, reason = verify_unit("volts", accepted_v)
    assert matched is True

    # Missing unit
    matched, reason = verify_unit(None, accepted_v)
    assert matched is False
    assert "missing" in reason.lower()

    # Wrong unit
    matched, reason = verify_unit("A", accepted_v)
    assert matched is False
    assert "mismatch" in reason.lower()


def test_substitution_verification():
    expected = {"I": 0.5, "R": 20.0}

    # Correct substitution
    matched, reason = verify_substitution({"I": 0.5, "R": 20.0}, expected)
    assert matched is True

    # Case insensitivity
    matched, reason = verify_substitution({"i": 0.5, "r": 20.0}, expected)
    assert matched is True

    # Missing variable
    matched, reason = verify_substitution({"I": 0.5}, expected)
    assert matched is False
    assert "missing value for R" in reason

    # Wrong value
    matched, reason = verify_substitution({"I": 0.5, "R": 2.0}, expected)
    assert matched is False
    assert "expected R = 20.0, found R = 2.0" in reason


def test_expression_verification():
    target = "9*x**2 - 10*x + 4"

    # Equivalent with different term order
    matched, _ = verify_expression("-10*x + 4 + 9*x**2", target)
    assert matched is True

    # Equivalent with caret
    matched, _ = verify_expression("9*x^2 - 10*x + 4", target)
    assert matched is True

    # Wrong expression
    matched, _ = verify_expression("9*x**2 - 5*x + 4", target)
    assert matched is False
