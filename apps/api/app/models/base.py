"""Base of every API model: unknown fields are rejected, so responses match api.md exactly."""

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
