"""Error envelope of every non-2xx response (specs/system/api.md Conventions)."""

from pydantic import BaseModel, ConfigDict


class ErrorBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str


class ErrorResponse(BaseModel):
    """{"error": {"code": "scope_not_confirmed", "message": "..."}}"""

    model_config = ConfigDict(extra="forbid")

    error: ErrorBody
