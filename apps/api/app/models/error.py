"""Error envelope of every non-2xx response (specs/system/api.md Conventions)."""

from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict


class ErrorBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str


class ErrorResponse(BaseModel):
    """{"error": {"code": "scope_not_confirmed", "message": "..."}}"""

    model_config = ConfigDict(extra="forbid")

    error: ErrorBody


def error_response(status: int, code: str, message: str) -> JSONResponse:
    """The envelope as a response, for handlers and routers that answer with an error."""
    body = ErrorResponse(error=ErrorBody(code=code, message=message))
    return JSONResponse(body.model_dump(), status_code=status)
