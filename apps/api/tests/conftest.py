import os

# Tests never call a real model unless marked @pytest.mark.live (apps/api/CLAUDE.md).
os.environ.setdefault("AI_PROVIDER", "fake")
os.environ.setdefault("APP_ENV", "test")
