"""Typed settings: environment variables + config/learning.yaml + config/ai.yaml.

Every threshold of the learning model and every model-routing choice lives in the
YAML files (root CLAUDE.md rules 5 and 3). The models below mirror those files with
``extra="forbid"`` so a renamed or misspelled key fails at startup instead of being
silently ignored.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# apps/api/app/settings.py -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# --- config/learning.yaml (specs/system/learning-model.md) -------------------


class BktConfig(_Strict):
    p_init: float = Field(ge=0, le=1)
    p_transit: float = Field(ge=0, le=1)
    p_guess: float = Field(ge=0, le=1)
    p_slip: float = Field(ge=0, le=1)
    mastery_threshold: float = Field(ge=0, le=1)
    weak_below: float = Field(ge=0, le=1)
    count_only_independent: bool


class LevelsConfig(_Strict):
    show: list[str]


class DoneConfig(_Strict):
    require_exam_skills_covered: bool
    require_all_skills_if_no_past_exam: bool
    min_independent_correct_per_skill: int = Field(ge=1)
    three_star_final_difficulty: int
    tight_mode_two_star_difficulty: int


class ParkConfig(_Strict):
    max_problems_per_skill_per_day: int = Field(ge=1)
    max_fail_streak_per_skill: int = Field(ge=1)


class SpacingConfig(_Strict):
    first_gap_days: float = Field(gt=0)
    growth_factor: float = Field(gt=1)
    max_gap_ratio_of_days_left: float = Field(gt=0, le=1)
    min_gap_days: float = Field(gt=0)
    reset_on_wrong: bool
    review_slots_at_session_start: int = Field(ge=0)


class StarsConfig(_Strict):
    weight_same_instructor: float
    weight_other_instructor: float
    three_star_min_r: float
    prerequisite_of_three_star_gets: int
    no_past_exam_method: str


class ReadinessConfig(_Strict):
    weight: str
    exclude_zero_star: bool


class PlannerConfig(_Strict):
    problems_per_skill: str
    default_minutes_per_problem: float = Field(gt=0)
    default_daily_minutes: float = Field(gt=0)
    default_session_minutes: float = Field(gt=0)
    tight_ratio: float = Field(gt=0)
    triage_ratio: float = Field(gt=0)
    triage_days_left: int = Field(ge=0)
    final_mode_days_left: int = Field(ge=0)
    interleave_every_n_practice: int = Field(ge=1)


class OcrConfig(_Strict):
    confirm_below_confidence: float = Field(ge=0, le=1)


class CheckerConfig(_Strict):
    sympy_timeout_seconds: float = Field(gt=0)
    numeric_rel_tolerance: float = Field(ge=0)
    max_generate_retries: int = Field(ge=0)


class BuddyQuota(_Strict):
    low: int = Field(ge=0)
    med: int = Field(ge=0)
    high: int = Field(ge=0)


class BuddyConfig(_Strict):
    quota_per_topic: BuddyQuota
    min_user_turns_between: int = Field(ge=0)
    encourage_fail_streak: int = Field(ge=1)
    halve_quota_in_modes: list[str]


class SessionConfig(_Strict):
    idle_minutes_to_end: float = Field(gt=0)
    context_recent_turns: int = Field(ge=1)
    token_budget: int = Field(ge=1)
    grounding_chunks: int = Field(ge=0)


class LearningConfig(_Strict):
    version: float
    bkt: BktConfig
    levels: LevelsConfig
    done: DoneConfig
    park: ParkConfig
    spacing: SpacingConfig
    stars: StarsConfig
    readiness: ReadinessConfig
    planner: PlannerConfig
    ocr: OcrConfig
    checker: CheckerConfig
    buddy: BuddyConfig
    session: SessionConfig


# --- config/ai.yaml (specs/system/ai-orchestration.md §2.10) -----------------


class TierConfig(_Strict):
    primary: str
    fallback: str | None


class PurposeConfig(_Strict):
    tier: str
    temperature: float = Field(ge=0, le=2)
    max_tokens: int = Field(ge=1)
    timeout_s: float = Field(gt=0)
    prompt: str
    stream: bool = False


class CircuitBreakerConfig(_Strict):
    failure_rate_threshold: float = Field(gt=0, le=1)
    minimum_calls: int = Field(ge=1)
    sliding_window_calls: int = Field(ge=1)
    open_seconds: float = Field(gt=0)


class GatewayConfig(_Strict):
    retries: int = Field(ge=0)
    schema_retries: int = Field(ge=0)
    circuit_breaker: CircuitBreakerConfig


class GuardsConfig(_Strict):
    max_message_chars: int = Field(ge=1)
    rate_limit_messages_per_minute: int = Field(ge=1)
    max_image_mb: float = Field(gt=0)
    max_audio_seconds: float = Field(gt=0)
    answer_leak_check: bool


class TargetsConfig(_Strict):
    ttft_p95_seconds: float = Field(gt=0)
    cost_per_session_thb: float = Field(gt=0)


class RetentionConfig(_Strict):
    audio_days: int = Field(ge=0)
    full_prompt_days: int = Field(ge=0)


class AIConfig(_Strict):
    version: float
    tiers: dict[str, TierConfig]
    purposes: dict[str, PurposeConfig]
    gateway: GatewayConfig
    guards: GuardsConfig
    targets: TargetsConfig
    retention: RetentionConfig

    @model_validator(mode="after")
    def _purposes_use_known_tiers(self) -> "AIConfig":
        unknown = {name: p.tier for name, p in self.purposes.items() if p.tier not in self.tiers}
        if unknown:
            raise ValueError(f"purposes reference undefined tiers: {unknown}")
        return self


# --- environment ---------------------------------------------------------------


class EnvSettings(BaseSettings):
    """Backend variables from .env.example (local: repo-root .env; cloud: Secret Manager).

    Keep in sync with .env.example; NEXT_PUBLIC_* belong to apps/web and are ignored here.
    """

    model_config = SettingsConfigDict(
        env_file=_REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Paths to repo-root folders; the Docker image overrides them (commented out in .env.example).
    config_dir: Path = _REPO_ROOT / "config"
    prompts_dir: Path = _REPO_ROOT / "prompts"

    # --- App ---
    app_env: Literal["local", "test", "staging", "production"] = "local"

    # --- Supabase ---
    supabase_url: str = ""
    supabase_anon_key: SecretStr = SecretStr("")
    supabase_service_role_key: SecretStr = SecretStr("")
    database_url: SecretStr = SecretStr("")

    # --- AI providers ---
    ai_provider: Literal["fake", "live"] = "fake"
    ai_model_override: str = ""
    gemini_api_key: SecretStr = SecretStr("")
    google_cloud_project: str = ""
    google_cloud_location: str = ""
    google_application_credentials: str = ""
    anthropic_api_key: SecretStr = SecretStr("")
    mathpix_app_id: str = ""
    mathpix_app_key: SecretStr = SecretStr("")

    # --- Observability ---
    sentry_dsn: SecretStr = SecretStr("")
    log_level: Literal["debug", "info", "warning", "error", "critical"] = "info"


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    env: EnvSettings
    learning: LearningConfig
    ai: AIConfig


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def load_settings() -> Settings:
    env = EnvSettings()
    return Settings(
        env=env,
        learning=LearningConfig.model_validate(_load_yaml(env.config_dir / "learning.yaml")),
        ai=AIConfig.model_validate(_load_yaml(env.config_dir / "ai.yaml")),
    )


@lru_cache
def get_settings() -> Settings:
    return load_settings()
