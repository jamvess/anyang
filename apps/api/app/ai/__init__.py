"""AI gateway package. Callers use ``from app import ai`` then ``await ai.call(...)`` or
``async for chunk in ai.stream(...)`` (AI-01)."""

from app.ai.gateway import call, stream

__all__ = ["call", "stream"]
