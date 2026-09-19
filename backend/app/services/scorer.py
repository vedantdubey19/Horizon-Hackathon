"""Deterministic scoring and follow-through engine for MarkLoss.

Awards marks strictly according to rubric definitions and deterministic checks.
Applies follow-through marking when earlier errors are carried forward consistently.
"""

from typing import Dict, List, Optional, Tuple, Union
import sympy as sp

from app.schemas import (
    CheckType,
    ExtractedStep,
    GradeResponse,
    GradeResultItem,
    Problem,
    RubricItem,
)
from app.services.verify import (
    safe_parse_expression,
    verify_expression,
    verify_formula,
    verify_numeric,
    verify_substitution,
    verify_unit,
    _LOCAL_DICT,
)


def _evaluate_formula_with_subs(
    formula_str: str,
    target_var: str,
    subs: Dict[str, float],
) -> Optional[float]:
    """Solve formula for target_var and substitute student values.

    Args:
        formula_str: Equation string, e.g. "V = I * R" or "s = u*t + 0.5*a*t**2"
        target_var: The symbol to solve for, e.g. "V", "s", "v", "P"
        subs: Mapping of variable names to student's substituted numbers

    Returns:
        Re-computed float value or None if evaluation fails.
    """
    if "=" not in formula_str:
        return None

    parts = formula_str.split("=", 1)
    lhs = safe_parse_expression(parts[0])
    rhs = safe_parse_expression(parts[1])
    if lhs is None or rhs is None:
        return None

    eq = sp.simplify(lhs - rhs)
    target_sym = _LOCAL_DICT.get(target_var, sp.Symbol(target_var))

    try:
        sols = sp.solve(eq, target_sym)
        if not sols:
            return None

        # Build substitution dictionary with safe symbols
        sub_map = {}
        for k, v in subs.items():
            sym = _LOCAL_DICT.get(k, sp.Symbol(k))
            sub_map[sym] = float(v)

        for sol in sols:
            val = sol.subs(sub_map)
            try:
                f_val = float(val)
                return f_val
            except Exception:
                continue
    except Exception:
        pass

    return None


def _check_follow_through(
    problem: Problem,
    item: RubricItem,
    student_val: float,
    student_subs: Dict[str, Dict[str, float]],
    student_convs: Dict[str, float],
    prior_calcs: Dict[str, float],
) -> Tuple[bool, str]:
    """Check if student's calculation is mathematically consistent with prior steps.

    Args:
        problem: Current problem definition.
        item: The current numeric rubric item being graded.
        student_val: The student's computed numeric result.
        student_subs: Recorded student substitutions per rubric id.
        student_convs: Recorded student conversions per rubric id.
        prior_calcs: Recorded student earlier calculation values.

    Returns:
        (matched, reason) tuple.
    """
    dep_id = item.depends_on
    if not dep_id:
        return False, ""

    # Case 1: Dependency on a substitution (e.g. phy-ohm-01, phy-kin-04, phy-kin-05, phy-work-06)
    if dep_id in student_subs:
        subs = student_subs[dep_id]
        # Find the formula rubric item for this problem
        formula_item = next(
            (r for r in problem.rubric if r.check == CheckType.FORMULA), None
        )
        if formula_item and formula_item.accept:
            formula_str = formula_item.accept[0]
            # Identify target variable (e.g. from expected result or formula LHS)
            target_var = formula_str.split("=")[0].strip()
            recomputed = _evaluate_formula_with_subs(formula_str, target_var, subs)
            if recomputed is not None:
                tol = item.tolerance or 0.01
                allowed = max(tol * abs(recomputed), tol)
                if abs(student_val - recomputed) <= allowed:
                    return (
                        True,
                        f"calculation matches your substituted values ({student_val:.2f})",
                    )

        # Problem-specific math substitution follow-through:
        # e.g. math-diff-03 (f'(2) evaluated with student derivative)
        # e.g. math-geom-07 (d = sqrt(dx^2 + dy^2))
        if problem.id == "math-geom-07":
            dx = subs.get("dx", 0.0)
            dy = subs.get("dy", 0.0)
            recomputed = (dx**2 + dy**2) ** 0.5
            if abs(student_val - recomputed) <= 0.05:
                return True, f"distance matches your differences ({student_val:.2f})"

    # Case 2: Dependency on unit conversion (e.g. phy-trap-07)
    if dep_id in student_convs:
        # Student might have used unconverted area (25 instead of 0.0025)
        # Or an alternate conversion value
        unconverted_or_wrong_val = student_convs[dep_id]
        if unconverted_or_wrong_val > 0:
            # P = F / A, with F = 50
            recomputed = 50.0 / unconverted_or_wrong_val
            tol = item.tolerance or 1.0
            allowed = max(tol * abs(recomputed), tol)
            if abs(student_val - recomputed) <= allowed:
                return (
                    True,
                    f"calculation matches your area value ({student_val:.2f})",
                )

    # Case 3: Dependency on an earlier calculated value (e.g. phy-res-02, phy-power-08, math-ap-02, math-sys-05)
    if dep_id in prior_calcs:
        prior_val = prior_calcs[dep_id]

        if problem.id == "phy-res-02":
            # I = 12 / R_p
            if prior_val > 0:
                recomputed = 12.0 / prior_val
                if abs(student_val - recomputed) <= 0.05:
                    return (
                        True,
                        f"current matches your equivalent resistance R_p = {prior_val:.2f}",
                    )

        elif problem.id == "phy-power-08":
            # P_op = 110^2 / R
            if prior_val > 0:
                recomputed = (110.0**2) / prior_val
                if abs(student_val - recomputed) <= 0.5:
                    return (
                        True,
                        f"operating power matches your resistance R = {prior_val:.1f}",
                    )

        elif problem.id == "math-ap-02":
            # S_20 = (20 / 2) * (3 + a_20)
            recomputed = 10.0 * (3.0 + prior_val)
            if abs(student_val - recomputed) <= 0.5:
                return (
                    True,
                    f"sum matches your calculated 20th term = {prior_val}",
                )

        elif problem.id == "math-sys-05":
            # y = 2*x - 4
            recomputed = 2.0 * prior_val - 4.0
            if abs(student_val - recomputed) <= 0.05:
                return (
                    True,
                    f"y matches your calculated x = {prior_val}",
                )

    return False, ""


def grade_steps(
    problem: Problem,
    steps: List[ExtractedStep],
    previous_results: Optional[List[GradeResultItem]] = None,
) -> GradeResponse:
    """Grade extracted student steps deterministically against the problem rubric.

    Args:
        problem: Problem with complete rubric definitions.
        steps: Extracted steps from student submission.
        previous_results: Prior results for detecting recovered marks upon retry.

    Returns:
        GradeResponse with line-by-line awarded marks and reasons.
    """
    results: List[GradeResultItem] = []
    student_subs: Dict[str, Dict[str, float]] = {}
    student_convs: Dict[str, float] = {}
    prior_calcs: Dict[str, float] = {}

    prev_awarded_map: Dict[str, int] = {}
    if previous_results:
        prev_awarded_map = {r.rule_id: r.awarded for r in previous_results}

    used_step_ids = set()

    for item in problem.rubric:
        awarded = 0
        reason = ""
        matched_step_id: Optional[int] = None

        if item.check == CheckType.FORMULA:
            # Search steps for formula
            formula_step = next(
                (s for s in steps if s.formula and s.formula.strip()), None
            )
            if formula_step and item.accept:
                matched_step_id = formula_step.step_id
                matched, v_reason = verify_formula(formula_step.formula, item.accept)
                if matched:
                    awarded = item.marks
                    reason = f"Formula: {v_reason}"
                else:
                    reason = f"Formula: '{formula_step.formula}' is incorrect."
            else:
                reason = "Formula: missing or unstated."

        elif item.check == CheckType.SUBSTITUTION:
            # Search steps for substitutions
            sub_step = next((s for s in steps if s.substitutions), None)
            if sub_step and item.expect:
                matched_step_id = sub_step.step_id
                student_subs[item.id] = sub_step.substitutions
                matched, v_reason = verify_substitution(
                    sub_step.substitutions, item.expect, item.tolerance or 0.01
                )
                if matched:
                    awarded = item.marks
                    reason = "Substitution: correct values substituted."
                else:
                    reason = v_reason
            else:
                reason = "Substitution: no substituted values found."

        elif item.check == CheckType.CONVERSION:
            # Look for conversion step result
            conv_step = next(
                (s for s in steps if s.result and s.result.value is not None), None
            )
            if conv_step and item.target is not None:
                matched_step_id = conv_step.step_id
                used_step_ids.add(conv_step.step_id)
                try:
                    val = float(conv_step.result.value)
                    student_convs[item.id] = val
                    matched, _ = verify_numeric(val, item.target, item.tolerance or 0.01)
                    if matched:
                        awarded = item.marks
                        reason = f"Conversion: correct unit conversion ({val})."
                    else:
                        reason = f"Conversion: expected {item.target}, found {val}."
                except (ValueError, TypeError):
                    reason = f"Conversion: invalid value '{conv_step.result.value}'."
            else:
                reason = "Conversion: required unit conversion step is missing."

        elif item.check == CheckType.NUMERIC:
            # Look for calculation result across steps (excluding steps used for conversion)
            calc_steps = [
                s for s in steps if s.result and s.result.value is not None and s.step_id not in used_step_ids
            ]
            # Match step corresponding to this numeric check
            target_step = None
            if len(calc_steps) == 1:
                target_step = calc_steps[0]
            elif len(calc_steps) > 1:
                # If problem has multiple numeric items (e.g. req_calc vs current_calc)
                numeric_items = [r for r in problem.rubric if r.check == CheckType.NUMERIC]
                idx = numeric_items.index(item) if item in numeric_items else 0
                if idx < len(calc_steps):
                    target_step = calc_steps[idx]
                else:
                    target_step = calc_steps[-1]

            if target_step and item.target is not None:
                matched_step_id = target_step.step_id
                try:
                    s_val = float(target_step.result.value)
                    prior_calcs[item.id] = s_val
                    matched, _ = verify_numeric(s_val, item.target, item.tolerance or 0.01)
                    if matched:
                        awarded = item.marks
                        reason = f"Calculation: {s_val} is correct."
                    else:
                        # Check Follow-Through marking
                        ft_matched, ft_reason = _check_follow_through(
                            problem,
                            item,
                            s_val,
                            student_subs,
                            student_convs,
                            prior_calcs,
                        )
                        if ft_matched:
                            awarded = item.marks
                            reason = f"Follow-through applied: {ft_reason}."
                        else:
                            reason = f"Calculation: expected {item.target}, found {s_val}."
                except (ValueError, TypeError):
                    reason = f"Calculation: non-numeric result '{target_step.result.value}'."
            else:
                reason = "Calculation: result missing."

        elif item.check == CheckType.UNIT:
            # Look for unit in final step or steps with units
            unit_step = next(
                (s for s in reversed(steps) if s.result and s.result.unit), None
            )
            if unit_step and item.accept:
                matched_step_id = unit_step.step_id
                u_str = unit_step.result.unit
                matched, v_reason = verify_unit(u_str, item.accept)
                if matched:
                    awarded = item.marks
                    reason = f"Unit: {v_reason}"
                else:
                    reason = f"Unit: {v_reason}"
            else:
                reason = "Unit: missing in final answer."

        elif item.check == CheckType.EXPRESSION:
            # Look for matching algebraic expression
            expr_step = next(
                (s for s in steps if s.formula or (s.result and s.result.value)), None
            )
            if expr_step and item.target:
                matched_step_id = expr_step.step_id
                test_str = expr_step.formula or str(expr_step.result.value)
                matched, _ = verify_expression(test_str, str(item.target))
                if matched:
                    awarded = item.marks
                    reason = "Expression: correct algebraic expression."
                else:
                    reason = f"Expression: '{test_str}' does not match expected form."
            else:
                reason = "Expression: required step missing."

        # Detect recovered mark
        prev_awarded = prev_awarded_map.get(item.id, 0)
        is_recovered = (prev_awarded < item.marks) and (awarded == item.marks)

        results.append(
            GradeResultItem(
                rule_id=item.id,
                label=item.label,
                awarded=awarded,
                max=item.marks,
                reason=reason,
                step_id=matched_step_id,
                is_recovered=is_recovered,
            )
        )

    total = sum(r.awarded for r in results)
    max_total = sum(r.max for r in results)

    return GradeResponse(
        problem_id=problem.id,
        results=results,
        total=total,
        max_total=max_total,
    )
