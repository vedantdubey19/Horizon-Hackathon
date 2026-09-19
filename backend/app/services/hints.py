"""Pedagogical 3-level hint engine with answer leak guard."""

import logging
import re
from typing import List, Optional
from app.config import settings
from app.llm.client import get_llm_client
from app.llm.prompts import HINT_SYSTEM_PROMPT
from app.schemas import CheckType, HintResponse, Problem, RubricItem

logger = logging.getLogger("markloss.hints")

# Guaranteed-safe fallback templates that NEVER contain numbers or answers
_SAFE_TEMPLATES = {
    CheckType.FORMULA: {
        1: "Look closely at the formula written in your initial step.",
        2: "Recall the fundamental equation relating the given quantities.",
        3: "Check whether the formula is correctly rearranged for the unknown variable.",
    },
    CheckType.SUBSTITUTION: {
        1: "Check the values you substituted into the equation.",
        2: "Ensure that each number from the problem statement corresponds to the correct variable.",
        3: "Carefully verify the Cartesian sign convention or numerical values substituted.",
    },
    CheckType.CONVERSION: {
        1: "Take a closer look at the units of the given values in step 1.",
        2: "Recall the standard SI units required before substituting into the formula.",
        3: "Remember to convert area from square centimetres into square metres before dividing.",
    },
    CheckType.NUMERIC: {
        1: "Review the arithmetic in your calculation step.",
        2: "Double check the algebraic operations (multiplication, division, powers) carried out.",
        3: "Re-calculate the arithmetic step carefully to catch any arithmetic slip.",
    },
    CheckType.UNIT: {
        1: "Take a look at the physical unit written in your final answer.",
        2: "Recall the standard SI unit used to measure this physical quantity.",
        3: "Ensure your unit matches standard notation and includes proper dimensions.",
    },
    CheckType.EXPRESSION: {
        1: "Look closely at the algebraic expression derived in this step.",
        2: "Recall the standard rules of differentiation, integration, or algebraic rearrangement.",
        3: "Verify that all powers, coefficients, and signs were carried through accurately.",
    },
}


def _extract_leak_targets(problem: Problem, item: Optional[RubricItem] = None) -> List[str]:
    """Identify numeric targets and expressions that must NEVER appear in a hint."""
    targets: List[str] = []

    # Problem expected value
    exp = problem.expected.value
    if isinstance(exp, list):
        for e in exp:
            targets.append(str(e))
            if isinstance(e, float) and e.is_integer():
                targets.append(str(int(e)))
    elif exp is not None:
        targets.append(str(exp))
        if isinstance(exp, float) and exp.is_integer():
            targets.append(str(int(exp)))

    # Rubric item targets across all items in problem
    items_to_check = [item] if item else problem.rubric
    for r in problem.rubric:
        if r.target is not None:
            if isinstance(r.target, list):
                for t in r.target:
                    targets.append(str(t))
                    if isinstance(t, float) and t.is_integer():
                        targets.append(str(int(t)))
            else:
                t = r.target
                targets.append(str(t))
                if isinstance(t, float) and t.is_integer():
                    targets.append(str(int(t)))

        # Expected substitutions
        if r.expect:
            for val in r.expect.values():
                targets.append(str(val))
                if isinstance(val, float) and val.is_integer():
                    targets.append(str(int(val)))

    # Remove empty or trivially short single chars like '0' or '1' that might appear in normal English
    cleaned: List[str] = []
    for t in targets:
        s = t.strip()
        if s and s not in {"0", "1", "-1"}:
            cleaned.append(s)

    return list(set(cleaned))


def detect_leak(hint_text: str, leak_targets: List[str]) -> bool:
    """Scan hint text to verify no target answer or calculation result was leaked.

    Args:
        hint_text: The candidate hint string.
        leak_targets: List of banned numeric strings or expressions.

    Returns:
        True if an answer leak was detected, False if safe.
    """
    if not hint_text:
        return False

    for target in leak_targets:
        # Check numeric match not part of another number or decimal
        escaped = re.escape(target)
        pattern = rf"(?<!\d)(?<!\d\.){escaped}(?!\d)(?!\.\d)"
        if re.search(pattern, hint_text, re.IGNORECASE):
            logger.warning("Leak guard detected target '%s' in hint: '%s'", target, hint_text)
            return True

    return False


def get_safe_fallback_hint(check_type: CheckType, level: int) -> str:
    """Return an educator-crafted guaranteed-safe hint that never leaks."""
    clamped_level = max(1, min(level, 3))
    templates = _SAFE_TEMPLATES.get(check_type, _SAFE_TEMPLATES[CheckType.NUMERIC])
    return templates.get(clamped_level, templates[1])


async def generate_hint(
    problem: Problem,
    item: RubricItem,
    step_text: str,
    level: int,
) -> HintResponse:
    """Generate a leak-guarded pedagogical hint for a failed rubric check.

    Args:
        problem: The problem definition (for leak target scanning).
        item: The specific rubric item the student failed.
        step_text: The student's written step text.
        level: Requested hint level (1, 2, or 3).

    Returns:
        HintResponse with the safe hint text.
    """
    clamped_level = max(1, min(level, 3))
    max_reached = (clamped_level == 3)
    leak_targets = _extract_leak_targets(problem, item)

    # In DEMO_MODE or if no API key, use educator-crafted safe templates directly
    if settings.is_demo_mode:
        safe_text = get_safe_fallback_hint(item.check, clamped_level)
        return HintResponse(
            rule_id=item.id,
            level=clamped_level,
            hint=safe_text,
            max_level_reached=max_reached,
        )

    # Live LLM generation with prompt isolation (NEVER sends expected or full solution)
    prompt = (
        f"Generate a Level {clamped_level} hint for the following error:\n"
        f"- Rubric check: {item.label}\n"
        f"- Check type: {item.check.value}\n"
        f"- Student's step: \"{step_text}\"\n\n"
        f"Remember: DO NOT include the numerical answer or calculated numbers in your hint."
    )

    client = get_llm_client()

    for attempt in range(2):  # Max 2 retries on leak detection
        try:
            data = await client.generate_text_json(
                prompt=prompt,
                system_instruction=HINT_SYSTEM_PROMPT,
                temperature=0.2,
            )
            raw_hint = str(data.get("hint", "")).strip()

            # Run through Leak Guard
            if not detect_leak(raw_hint, leak_targets):
                return HintResponse(
                    rule_id=item.id,
                    level=clamped_level,
                    hint=raw_hint,
                    max_level_reached=max_reached,
                )
            else:
                logger.warning("Hint attempt %d leaked target value, retrying...", attempt + 1)
        except Exception as e:
            logger.warning("LLM hint generation attempt %d failed: %s", attempt + 1, e)

    # Fall back to safe template if LLM attempts leak or fail
    logger.info("Falling back to guaranteed-safe template hint for rule %s", item.id)
    fallback = get_safe_fallback_hint(item.check, clamped_level)
    return HintResponse(
        rule_id=item.id,
        level=clamped_level,
        hint=fallback,
        max_level_reached=max_reached,
    )
