"""The current instant as a FastAPI dependency, so tests can fix the clock."""

from datetime import UTC, datetime


def get_now() -> datetime:
    return datetime.now(UTC)
