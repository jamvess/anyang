import shutil
from pathlib import Path

import pytest
import yaml
from dotenv import dotenv_values
from pydantic import ValidationError

from app.settings import _REPO_ROOT, EnvSettings, load_settings

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


def test_SM03_unknown_no_past_exam_method_fails_at_config_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # compute-importance.md AC-19: a typo in learning.yaml fails when the app loads its
    # settings (startup), not later when an ingestion job calls compute_importance.
    config_dir = _REPO_ROOT / "config"
    learning = yaml.safe_load((config_dir / "learning.yaml").read_text(encoding="utf-8"))
    learning["stars"]["no_past_exam_method"] = "page_tercile"
    (tmp_path / "learning.yaml").write_text(
        yaml.safe_dump(learning, allow_unicode=True), encoding="utf-8"
    )
    shutil.copy(config_dir / "ai.yaml", tmp_path / "ai.yaml")
    monkeypatch.setenv("CONFIG_DIR", str(tmp_path))

    with pytest.raises(ValidationError, match="no_past_exam_method"):
        load_settings()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("prerequisite_of_three_star_gets", 0),
        ("prerequisite_of_three_star_gets", 4),
        ("three_star_min_r", 0),
        ("three_star_min_r", 1.1),
        ("weight_same_instructor", -0.1),
        ("weight_other_instructor", -0.1),
    ],
)
def test_SM03_stars_config_out_of_range_fails_at_load(field: str, value: float) -> None:
    # Added after /code-review (8 Nov): a value that would break topics.importance (0-3) or
    # give ★★★ to topics never seen fails when config loads, like AC-19.
    from app.settings import StarsConfig, get_settings

    stars = get_settings().learning.stars.model_dump() | {field: value}

    with pytest.raises(ValidationError, match=field):
        StarsConfig.model_validate(stars)
