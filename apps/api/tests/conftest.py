import os

# Tests never call a real model unless marked @pytest.mark.live (apps/api/CLAUDE.md).
os.environ.setdefault("AI_PROVIDER", "fake")
os.environ.setdefault("APP_ENV", "test")
# Room tests written before the JWT check call the API without a token; auth tests turn it on
# through the get_auth_required dependency (specs/features/platform/api-auth.md §8).
os.environ.setdefault("AUTH_REQUIRED", "false")


import pytest


@pytest.fixture(autouse=True)
def _fresh_rate_limiter():
    """Each test starts with no room messages counted: the counts live in memory for the
    process (specs/features/ai/gateway-guards.md §2.1), and many tests post to the room."""
    from app.rate_limit import get_rate_limiter

    get_rate_limiter.cache_clear()
    yield
