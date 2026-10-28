"""AI gateway package. Callers use ``from app import ai`` then ``await ai.call(...)`` (AI-01)."""

from app.ai.gateway import call

__all__ = ["call"]
