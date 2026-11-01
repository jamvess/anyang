"""NFR-P1: tutor_reply runs with Gemini 3 thinking level "minimal" (PoC P4-lite, PR #99).

specs/poc/reports/P4-lite.md §4: thinking "low" gave TTFT p95 3.87 s, "minimal" 1.20 s, so
config/ai.yaml 1.8 sets it. These tests keep the value accepted by the config schema and passed
unchanged to the Gemini SDK (self-review of #99).
"""

import pytest
from google.genai import types
from pydantic import ValidationError

from app.ai.providers.base import ProviderRequest
from app.ai.providers.gemini import _config
from app.settings import PurposeConfig, get_settings

PURPOSE = {"tier": "main", "temperature": 0.6, "max_tokens": 2000, "timeout_s": 30, "prompt": "v1"}


def test_NFRP1_config_accepts_minimal_and_rejects_unknown_levels():
    assert PurposeConfig.model_validate(PURPOSE | {"thinking": "minimal"}).thinking == "minimal"
    with pytest.raises(ValidationError):
        PurposeConfig.model_validate(PURPOSE | {"thinking": "none"})


def test_NFRP1_tutor_reply_uses_minimal_thinking():
    assert get_settings().ai.purposes["tutor_reply"].thinking == "minimal"


def test_NFRP1_gemini_request_carries_minimal_level():
    request = ProviderRequest(
        purpose="tutor_reply",
        model="gemini-3.5-flash",
        prompt="สวัสดี",
        temperature=0.6,
        max_tokens=2000,
        thinking="minimal",
    )

    config = _config(request, json_output=False)

    assert config.thinking_config.thinking_level == types.ThinkingLevel.MINIMAL
