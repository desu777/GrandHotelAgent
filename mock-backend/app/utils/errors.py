"""
Error handling utilities for standardized error responses.
"""

from fastapi.responses import JSONResponse
from app.models import ErrorEnvelope


def error_response(code: str, message: str, status: int) -> JSONResponse:
    """
    Create standardized error response with ErrorEnvelope.

    Args:
        code: Error code constant (e.g. "ROOM_NOT_FOUND")
        message: Human-readable error message
        status: HTTP status code

    Returns:
        JSONResponse with ErrorEnvelope body
    """
    error = ErrorEnvelope(
        code=code,
        message=message,
        status=status
    )
    return JSONResponse(
        status_code=status,
        content=error.model_dump()
    )
