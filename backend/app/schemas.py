from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class Subject(str, Enum):
    PHYSICS = "physics"
    MATH = "math"


class CheckType(str, Enum):
    FORMULA = "formula"
    SUBSTITUTION = "substitution"
    NUMERIC = "numeric"
    UNIT = "unit"
    CONVERSION = "conversion"
    EXPRESSION = "expression"


class RubricItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    label: str
    marks: int = 1
    check: CheckType
    accept: Optional[List[str]] = None
    expect: Optional[Dict[str, float]] = None
    target: Optional[Union[float, str, List[float]]] = None
    tolerance: Optional[float] = 0.01
    depends_on: Optional[str] = None


class ExpectedResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value: Union[float, str, List[Union[float, str]]]
    unit: Optional[str] = None


class Problem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    subject: Subject
    grade: int = Field(..., alias="class")
    statement: str
    expected: ExpectedResult
    rubric: List[RubricItem]


class ProblemSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    subject: Subject
    grade: int = Field(..., alias="class")
    statement: str
    total_marks: int


# Transcription schemas
class TranscribedStep(BaseModel):
    id: int
    text: str
    confidence: float
    needs_confirmation: bool = False


class TranscribeResponse(BaseModel):
    problem_id: str
    steps: List[TranscribedStep]
    cached: bool = False


# Step inputs for grading
class StepInput(BaseModel):
    id: int
    text: str


class StepResult(BaseModel):
    value: Optional[Union[float, str]] = None
    unit: Optional[str] = None


class ExtractedStep(BaseModel):
    step_id: int
    formula: Optional[str] = None
    substitutions: Dict[str, float] = Field(default_factory=dict)
    result: Optional[StepResult] = None
    raw: str


# Grade schemas
class GradeResultItem(BaseModel):
    rule_id: str
    label: str
    awarded: int
    max: int
    reason: str
    step_id: Optional[int] = None
    is_recovered: bool = False


class GradeRequest(BaseModel):
    problem_id: str
    steps: List[StepInput]
    previous_results: Optional[List[GradeResultItem]] = None


class GradeResponse(BaseModel):
    problem_id: str
    results: List[GradeResultItem]
    total: int
    max_total: int


# Hint schemas
class HintRequest(BaseModel):
    problem_id: str
    rule_id: str
    step_text: str
    level: int = Field(..., ge=1, le=3)


class HintResponse(BaseModel):
    rule_id: str
    level: int
    hint: str
    max_level_reached: bool = False
