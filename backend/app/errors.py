"""Typed exceptions and HTTP error handlers for MarkLoss."""

from enum import Enum
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ErrorCode(str, Enum):
    UNREADABLE_IMAGE = "UNREADABLE_IMAGE"
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    INVALID_MODEL_OUTPUT = "INVALID_MODEL_OUTPUT"
    UNSUPPORTED_FILE = "UNSUPPORTED_FILE"
    TOO_LARGE = "TOO_LARGE"
    PROBLEM_NOT_FOUND = "PROBLEM_NOT_FOUND"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"


class MarkLossError(Exception):
    """Base application exception with typed error code and actionable guidance."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        action: str,
        status_code: int = 400,
        detail: Optional[str] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.action = action
        self.status_code = status_code
        self.detail = detail


class UnreadableImageError(MarkLossError):
    def __init__(self, detail: Optional[str] = None):
        super().__init__(
            code=ErrorCode.UNREADABLE_IMAGE,
            message="Could not transcribe handwriting from the provided image.",
            action="Please take a clearer photo with better lighting or type the steps directly.",
            status_code=422,
            detail=detail,
        )


class LLMUnavailableError(MarkLossError):
    def __init__(self, detail: Optional[str] = None):
        super().__init__(
            code=ErrorCode.LLM_UNAVAILABLE,
            message="The AI vision/language service timed out or is temporarily unavailable.",
            action="Please try again in a few seconds or switch to sample demo mode.",
            status_code=503,
            detail=detail,
        )


class InvalidModelOutputError(MarkLossError):
    def __init__(self, detail: Optional[str] = None):
        super().__init__(
            code=ErrorCode.INVALID_MODEL_OUTPUT,
            message="The AI model response could not be parsed into a valid structure.",
            action="Please retry the operation.",
            status_code=502,
            detail=detail,
        )


class UnsupportedFileError(MarkLossError):
    def __init__(self, mime_type: str):
        super().__init__(
            code=ErrorCode.UNSUPPORTED_FILE,
            message=f"Unsupported image file type: {mime_type}.",
            action="Please upload a JPEG, PNG, or WebP image.",
            status_code=415,
            detail=f"Received MIME type: {mime_type}",
        )


class FileTooLargeError(MarkLossError):
    def __init__(self, size_bytes: int, max_bytes: int):
        super().__init__(
            code=ErrorCode.TOO_LARGE,
            message=f"Image file size ({size_bytes // 1024} KB) exceeds the limit of {max_bytes // (1024 * 1024)} MB.",
            action="Please upload a smaller or compressed photo.",
            status_code=413,
            detail=f"Size: {size_bytes} bytes",
        )


class ProblemNotFoundError(MarkLossError):
    def __init__(self, problem_id: str):
        super().__init__(
            code=ErrorCode.PROBLEM_NOT_FOUND,
            message=f"Problem '{problem_id}' was not found in the problem bank.",
            action="Please select a valid problem from the table of contents.",
            status_code=404,
            detail=f"Problem ID: {problem_id}",
        )


class ExtractionFailedError(MarkLossError):
    def __init__(self, detail: Optional[str] = None):
        super().__init__(
            code=ErrorCode.EXTRACTION_FAILED,
            message="Failed to parse mathematical steps after multiple validation attempts.",
            action="Please review your step text and formatting.",
            status_code=422,
            detail=detail,
        )


def register_error_handlers(app: FastAPI) -> None:
    """Register custom exception handlers with FastAPI application."""

    @app.exception_handler(MarkLossError)
    async def markloss_error_handler(request: Request, exc: MarkLossError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code.value,
                    "message": exc.message,
                    "action": exc.action,
                    "detail": exc.detail,
                }
            },
        )
