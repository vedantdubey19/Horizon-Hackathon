"""Structured field extraction service for student steps."""

import json
import logging
import re
from typing import Any, Dict, List, Optional
from app.config import settings
from app.errors import ExtractionFailedError
from app.llm.client import get_llm_client
from app.llm.prompts import EXTRACTION_SYSTEM_PROMPT
from app.schemas import ExtractedStep, StepInput, StepResult

logger = logging.getLogger("markloss.extract")


def rule_based_extract_step(step: StepInput) -> ExtractedStep:
    """Deterministic fallback parser for common step patterns without LLM dependency."""
    text = step.text.strip()
    formula: Optional[str] = None
    substitutions: Dict[str, float] = {}
    result: Optional[StepResult] = None

    # Check for explicit variable assignments like I = 0.5, R = 20
    explicit_assignments = re.findall(
        r"([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(-?\d+(?:\.\d+)?)(?![*+/^a-zA-Z0-9_])", text
    )
    if len(explicit_assignments) >= 2 or (len(explicit_assignments) == 1 and "," in text):
        for var, val in explicit_assignments:
            substitutions[var] = float(val)

    # Check if line has arithmetic operators on RHS
    has_operator = (
        any(op in text.split("=")[-1] for op in ["*", "/", "+", "-"])
        if "=" in text
        else False
    )
    all_nums = [float(n) for n in re.findall(r"[-+]?\d*\.?\d+", text)]

    if "=" in text:
        lhs, rhs = text.split("=", 1)
        lhs_has_letter = bool(re.search(r"[a-zA-Z]", lhs))
        rhs_has_letter = bool(re.search(r"[a-zA-Z]", rhs))
        if lhs_has_letter and rhs_has_letter and not all_nums:
            formula = text
        elif has_operator and all_nums:
            # Substitution line: e.g. V = 0.5 * 20 or P = 50 / 25
            if not substitutions:
                substitutions = {f"val_{i+1}": n for i, n in enumerate(all_nums)}
        elif not has_operator and all_nums:
            # Final result line: e.g. V = 10 V or V = 9 V or V = 10
            unit_match = re.search(
                r"[-+]?\d*\.?\d+\s*([a-zA-ZΩμ]+(?:/[a-zA-ZΩμ0-9\^]+)?)", text
            )
            unit_str = unit_match.group(1).strip() if unit_match else None
            # Validate unit
            if unit_str and unit_str.lower() in [
                "v", "a", "m", "j", "pa", "w", "ohm", "cm", "m/s", "n"
            ]:
                result = StepResult(value=all_nums[-1], unit=unit_str)
            else:
                result = StepResult(value=all_nums[-1], unit=None)
    elif all_nums:
        unit_match = re.search(
            r"[-+]?\d*\.?\d+\s*([a-zA-ZΩμ]+(?:/[a-zA-ZΩμ0-9\^]+)?)", text
        )
        unit_str = unit_match.group(1).strip() if unit_match else None
        result = StepResult(value=all_nums[-1], unit=unit_str)

    return ExtractedStep(
        step_id=step.id,
        formula=formula,
        substitutions=substitutions,
        result=result,
        raw=text,
    )


async def extract_step_fields(steps: List[StepInput]) -> List[ExtractedStep]:
    """Extract structured fields from student step texts.

    Uses LLM with fallback to deterministic rule-based extractor.

    Args:
        steps: List of raw numbered steps.

    Returns:
        List of structured ExtractedStep objects.
    """
    if not steps:
        return []

    if settings.is_demo_mode:
        # In demo mode, apply rule-based parser immediately for instantaneous, reliable results
        return [rule_based_extract_step(s) for s in steps]

    # Live LLM extraction
    client = get_llm_client()
    formatted_steps = json.dumps([{"id": s.id, "text": s.text} for s in steps], indent=2)
    prompt = f"Extract structured mathematical fields from these steps:\n\n{formatted_steps}"

    for attempt in range(2):
        try:
            data = await client.generate_text_json(
                prompt=prompt,
                system_instruction=EXTRACTION_SYSTEM_PROMPT,
                temperature=0.0,
            )
            raw_extracted = data.get("steps", [])
            extracted_steps: List[ExtractedStep] = []
            for item in raw_extracted:
                step_id = int(item.get("step_id", 0))
                original_step = next((s for s in steps if s.id == step_id), None)
                raw_text = original_step.text if original_step else ""

                res_dict = item.get("result")
                res_obj = None
                if res_dict and isinstance(res_dict, dict) and res_dict.get("value") is not None:
                    res_obj = StepResult(
                        value=res_dict.get("value"),
                        unit=res_dict.get("unit"),
                    )

                extracted_steps.append(
                    ExtractedStep(
                        step_id=step_id,
                        formula=item.get("formula"),
                        substitutions=item.get("substitutions", {}),
                        result=res_obj,
                        raw=raw_text,
                    )
                )
            return extracted_steps

        except Exception as e:
            logger.warning("LLM extraction attempt %d failed: %s", attempt + 1, e)
            if attempt == 1:
                logger.info("Falling back to deterministic rule-based extractor.")
                return [rule_based_extract_step(s) for s in steps]

    return [rule_based_extract_step(s) for s in steps]
