from dotenv import dotenv_values

from app.settings import _REPO_ROOT, EnvSettings

ENV_EXAMPLE = _REPO_ROOT / ".env.example"
COMMENTED_IN_ENV_EXAMPLE = {"config_dir", "prompts_dir"}


def test_env_settings_match_env_example() -> None:
    example_keys = {
        key.lower() for key in dotenv_values(ENV_EXAMPLE) if not key.startswith("NEXT_PUBLIC_")
    }
    commented_keys = {
        line.removeprefix("#").strip().split("=", 1)[0].lower()
        for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines()
        if line.startswith("# ") and "=" in line
    }

    assert set(EnvSettings.model_fields) - COMMENTED_IN_ENV_EXAMPLE == example_keys
    assert commented_keys >= COMMENTED_IN_ENV_EXAMPLE


def test_env_example_parses() -> None:
    # Inline comments ("AI_PROVIDER=fake   # fake | live") must not leak into values.
    settings = EnvSettings(_env_file=ENV_EXAMPLE)

    assert settings.ai_provider == "fake"
    assert settings.log_level == "info"
