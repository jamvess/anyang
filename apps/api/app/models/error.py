"""Error envelope of every non-2xx response (specs/system/api.md Conventions)."""

from typing import Any

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


def error_docs(
    invalid: str = "Invalid path", conflict: str | None = None
) -> dict[int | str, dict[str, Any]]:
    """OpenAPI `responses` of a route with an id in its path, so generated types match the
    envelope. `invalid` names the 422 causes and `conflict` the 409 codes; no 409 without it."""
    errors: dict[int | str, dict[str, Any]] = {
        404: {"model": ErrorResponse, "description": "Not found"},
        422: {"model": ErrorResponse, "description": invalid},
    }
    if conflict:
        errors[409] = {"model": ErrorResponse, "description": conflict}
    return errors


def unavailable_docs(code: str) -> dict[int | str, dict[str, Any]]:
    """A route's own 503 replaces the 503 of AUTH_ERRORS, so it names both causes."""
    description = f"{code}, or auth_unavailable (Supabase Auth unreachable)"
    return {503: {"model": ErrorResponse, "description": description}}
