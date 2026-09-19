"""Deterministic verification engine for MarkLoss.

Pure functions for verifying formulas, substitutions, numeric values,
expressions, and units without LLM involvement.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import re
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)

# Restricted transformations: safe algebraic parsing without code execution
_TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)

# Common unit aliases mapping to canonical forms
_UNIT_ALIASES: Dict[str, str] = {
    # Resistance
    "ohm": "ohm",
    "ohms": "ohm",
    "ω": "ohm",
    "kohm": "kohm",
    # Voltage
    "v": "V",
    "volt": "V",
    "volts": "V",
    "mv": "mV",
    "kv": "kV",
    # Current
    "a": "A",
    "amp": "A",
    "amps": "A",
    "ampere": "A",
    "amperes": "A",
    "ma": "mA",
    # Length / distance
    "m": "m",
    "meter": "m",
    "meters": "m",
    "metre": "m",
    "metres": "m",
    "cm": "cm",
    "centimeter": "cm",
    "centimeters": "cm",
    "centimetre": "cm",
    "centimetres": "cm",
    "mm": "mm",
    "km": "km",
    # Speed
    "m/s": "m/s",
    "m s^-1": "m/s",
    "m s-1": "m/s",
    "m*s^-1": "m/s",
    "m/sec": "m/s",
    "meter/second": "m/s",
    "meters per second": "m/s",
    "metres per second": "m/s",
    # Acceleration
    "m/s^2": "m/s^2",
    "m/s2": "m/s^2",
    "m/s**2": "m/s^2",
    "m s^-2": "m/s^2",
    "m s-2": "m/s^2",
    "m*s^-2": "m/s^2",
    # Energy / Work
    "j": "J",
    "joule": "J",
    "joules": "J",
    "n m": "J",
    "n*m": "J",
    "nm": "J",
    # Force
    "n": "N",
    "newton": "N",
    "newtons": "N",
    # Pressure
    "pa": "Pa",
    "pascal": "Pa",
    "pascals": "Pa",
    "n/m^2": "Pa",
    "n/m2": "Pa",
    "n m^-2": "Pa",
    "n*m^-2": "Pa",
    # Power
    "w": "W",
    "watt": "W",
    "watts": "W",
    "j/s": "W",
    "kw": "kW",
    # Area
    "m^2": "m^2",
    "m2": "m^2",
    "m**2": "m^2",
    "cm^2": "cm^2",
    "cm2": "cm^2",
    "cm**2": "cm^2",
    # Time
    "s": "s",
    "sec": "s",
    "second": "s",
    "seconds": "s",
}


def normalize_unit(unit_str: Optional[str]) -> str:
    """Normalize a unit string to canonical representation.

    Args:
        unit_str: Raw unit string, e.g. "m s^-1", "volts", "Ω".

    Returns:
        Canonical unit string, e.g. "m/s", "V", "ohm".
    """
    if not unit_str:
        return ""

    raw = unit_str.strip().lower()
    raw = raw.replace("ω", "ohm").replace("μ", "u")
    raw = re.sub(r"\s+", " ", raw)

    # Direct alias match
    if raw in _UNIT_ALIASES:
        return _UNIT_ALIASES[raw]

    # Normalize exponents: e.g. s^-1 -> /s, m^2
    cleaned = raw.replace("**", "^").replace(" ", "")
    if cleaned in _UNIT_ALIASES:
        return _UNIT_ALIASES[cleaned]

    return unit_str.strip()


def verify_unit(
    student_unit: Optional[str], accepted_units: List[str]
) -> Tuple[bool, str]:
    """Check if student unit matches any accepted unit canonical forms.

    Args:
        student_unit: Student unit extracted from answer.
        accepted_units: List of acceptable unit representations.

    Returns:
        (matched, reason) tuple.
    """
    if not student_unit:
        return False, "Unit missing in final answer."

    norm_student = normalize_unit(student_unit)
    norm_accepted = [normalize_unit(u) for u in accepted_units]

    if norm_student in norm_accepted:
        return True, f"Unit '{student_unit}' is correct."

    return False, f"Unit mismatch: expected {norm_accepted[0]}, found '{student_unit}'."


_LOCAL_DICT = {
    "I": sp.Symbol("I"),
    "E": sp.Symbol("E"),
    "S": sp.Symbol("S"),
    "N": sp.Symbol("N"),
    "O": sp.Symbol("O"),
    "C": sp.Symbol("C"),
}


def safe_parse_expression(expr_str: str) -> Optional[sp.Expr]:
    """Parse a mathematical expression safely using SymPy without eval/exec.

    Args:
        expr_str: Expression string to parse.

    Returns:
        SymPy Expr object or None if unparseable.
    """
    if not expr_str or not expr_str.strip():
        return None

    # Pre-clean string
    cleaned = expr_str.strip().replace("^", "**")
    # Replace unicode division/multiplication
    cleaned = cleaned.replace("×", "*").replace("÷", "/")
    # Remove leading/trailing periods or commas
    cleaned = cleaned.strip(" .,;")

    try:
        return parse_expr(
            cleaned,
            transformations=_TRANSFORMATIONS,
            local_dict=_LOCAL_DICT,
            evaluate=False,
        )
    except Exception:
        return None


def verify_formula(
    student_formula: str, accepted_formulas: List[str]
) -> Tuple[bool, str]:
    """Verify formula equivalence algebraically using SymPy.

    Allows valid rearrangements, e.g. I = V/R when V = I*R is expected.

    Args:
        student_formula: Student's formula text, e.g. "I = V / R".
        accepted_formulas: List of accepted formula strings.

    Returns:
        (matched, reason) tuple.
    """
    if not student_formula or not student_formula.strip():
        return False, "Formula is missing."

    s_clean = student_formula.strip()

    # Exact string match (case-insensitive, space-insensitive)
    def normalize_str(s: str) -> str:
        return re.sub(r"\s+", "", s.lower())

    norm_s = normalize_str(s_clean)
    for acc in accepted_formulas:
        if norm_s == normalize_str(acc):
            return True, f"Formula matches accepted form: {s_clean}"

    # Equation algebraic equivalence via SymPy
    if "=" in s_clean:
        parts = s_clean.split("=", 1)
        lhs_s = safe_parse_expression(parts[0])
        rhs_s = safe_parse_expression(parts[1])
        if lhs_s is None or rhs_s is None:
            return False, f"Could not parse formula: {s_clean}"

        student_diff = sp.simplify(lhs_s - rhs_s)

        for acc in accepted_formulas:
            if "=" in acc:
                acc_parts = acc.split("=", 1)
                lhs_a = safe_parse_expression(acc_parts[0])
                rhs_a = safe_parse_expression(acc_parts[1])
                if lhs_a is None or rhs_a is None:
                    continue

                acc_diff = sp.simplify(lhs_a - rhs_a)

                # Direct difference check (lhs - rhs == 0 or rhs - lhs == 0)
                diff_between = sp.simplify(student_diff - acc_diff)
                sum_between = sp.simplify(student_diff + acc_diff)
                if diff_between == 0 or sum_between == 0:
                    return True, f"Formula is algebraically equivalent to {acc}"

                # Rearrangement check: solve acc_diff for any symbol and substitute
                symbols = list(acc_diff.free_symbols)
                for sym in symbols:
                    try:
                        sols = sp.solve(sp.Eq(acc_diff, 0), sym)
                        for sol in sols:
                            substituted = sp.simplify(student_diff.subs(sym, sol))
                            if substituted == 0:
                                return True, f"Formula is a valid rearrangement of {acc}"
                    except Exception:
                        continue
            else:
                # Expression check without '='
                acc_expr = safe_parse_expression(acc)
                if acc_expr is not None and sp.simplify(student_diff - acc_expr) == 0:
                    return True, f"Formula matches expression {acc}"

    return False, f"Formula '{s_clean}' does not match expected standard forms."


def verify_expression(student_expr_str: str, target_expr_str: str) -> Tuple[bool, str]:
    """Check algebraic equivalence of two expressions using SymPy.

    Args:
        student_expr_str: Student mathematical expression.
        target_expr_str: Target mathematical expression.

    Returns:
        (matched, reason) tuple.
    """
    s_expr = safe_parse_expression(student_expr_str)
    if s_expr is None:
        return False, f"Could not parse expression: '{student_expr_str}'."

    t_expr = safe_parse_expression(target_expr_str)
    if t_expr is None:
        return False, f"Invalid target expression: '{target_expr_str}'."

    diff = sp.simplify(s_expr - t_expr)
    if diff == 0:
        return True, "Expression is algebraically correct."

    return False, f"Expression '{student_expr_str}' does not match expected form."


def verify_substitution(
    student_subs: Dict[str, float],
    expected_subs: Dict[str, float],
    tolerance: float = 0.01,
) -> Tuple[bool, str]:
    """Verify that student substitution values match expected values.

    Args:
        student_subs: Dictionary of student extracted variable values.
        expected_subs: Dictionary of expected variable values.
        tolerance: Relative tolerance for numeric comparison.

    Returns:
        (matched, reason) tuple.
    """
    if not student_subs:
        return False, "Substitution missing: no substituted values found."

    # Case-insensitive / normalized lookup map
    norm_student = {k.strip().lower(): v for k, v in student_subs.items()}

    named_match = True
    mismatch_reason = ""
    for var, exp_val in expected_subs.items():
        v_key = var.strip().lower()
        if v_key not in norm_student:
            named_match = False
            mismatch_reason = f"Substitution: missing value for {var} (expected {exp_val})."
            break

        found_val = norm_student[v_key]
        allowed_diff = max(tolerance * abs(exp_val), tolerance)
        if abs(found_val - exp_val) > allowed_diff:
            named_match = False
            mismatch_reason = f"Substitution: expected {var} = {exp_val}, found {var} = {found_val}."
            break

    if named_match:
        return True, "All substituted values are correct."

    # If named matching failed, check if values match the expected set (e.g. from inline substitutions)
    stud_vals = sorted(student_subs.values())
    exp_vals = sorted(expected_subs.values())
    if len(stud_vals) == len(exp_vals):
        all_match = True
        for s_v, e_v in zip(stud_vals, exp_vals):
            allowed = max(tolerance * abs(e_v), tolerance)
            if abs(s_v - e_v) > allowed:
                all_match = False
                break
        if all_match:
            return True, "All substituted values are correct."

    return False, mismatch_reason or "Substitution mismatch."


def verify_numeric(
    student_val: Union[float, int],
    target_val: Union[float, int, List[Union[float, int]]],
    tolerance: float = 0.01,
) -> Tuple[bool, str]:
    """Verify student numeric calculation within given tolerance.

    Supports single target value or multiple accepted roots/solutions.

    Args:
        student_val: Extracted numerical result from student.
        target_val: Expected target float or list of floats.
        tolerance: Absolute/relative tolerance.

    Returns:
        (matched, reason) tuple.
    """
    if student_val is None:
        return False, "Calculation result missing."

    try:
        s_val = float(student_val)
    except (ValueError, TypeError):
        return False, f"Calculation result '{student_val}' is not a valid number."

    if isinstance(target_val, list):
        # Target has multiple acceptable values (e.g. quadratic roots or vector components)
        for t in target_val:
            t_f = float(t)
            allowed = max(tolerance * abs(t_f), tolerance) if tolerance < 0.5 else tolerance
            if abs(s_val - t_f) <= allowed:
                return True, f"Calculation {s_val} matches target root {t_f}."
        return False, f"Calculation: expected one of {target_val}, found {s_val}."
    else:
        t_f = float(target_val)
        allowed = max(tolerance * abs(t_f), tolerance) if tolerance < 0.5 else tolerance
        if abs(s_val - t_f) <= allowed:
            return True, f"Calculation matches expected target {t_f} within tolerance."
        return False, f"Calculation: expected {t_f}, found {s_val}."
