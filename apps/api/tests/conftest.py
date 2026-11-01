import os

# Tests never call a real model unless marked @pytest.mark.live (apps/api/CLAUDE.md).
os.environ.setdefault("AI_PROVIDER", "fake")
os.environ.setdefault("APP_ENV", "test")
# Room tests written before the JWT check call the API without a token; auth tests turn it on
# through the get_auth_required dependency (specs/features/platform/api-auth.md §8).
os.environ.setdefault("AUTH_REQUIRED", "false")
