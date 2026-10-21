"""Gemini provider: a 429 becomes ProviderRateLimited with the wait Gemini asked for, so the
gateway can back off (ai-orchestration.md §2.10, review of PR #15). No network: the SDK client
is replaced by a stub that raises the SDK's own error."""

import pytest
from google.genai import errors

from app.ai.providers.base import ProviderRateLimited, ProviderRequest
from app.ai.providers.gemini import GeminiProvider, retry_after_seconds


def quota_error(retry_delay: str | None) -> dict:
    """The JSON body of a Gemini 429 (google.rpc.Status with RetryInfo)."""
    details: list[dict] = [{"@type": "type.googleapis.com/google.rpc.QuotaFailure"}]
    if retry_delay is not None:
        details.append(
            {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": retry_delay}
        )
    return {
        "error": {
            "code": 429,
            "message": "You exceeded your current quota.",
            "status": "RESOURCE_EXHAUSTED",
            "details": details,
        }
    }


def test_ai_orchestration_2_10_gemini_retry_delay_is_read_in_seconds():
    assert retry_after_seconds(quota_error("36s")) == 36
    assert retry_after_seconds(quota_error("1.5s")) == 1.5


def test_ai_orchestration_2_10_gemini_without_retry_delay_gives_none():
    assert retry_after_seconds(quota_error(None)) is None
    assert retry_after_seconds({}) is None


class RaisingModels:
    def __init__(self, error: Exception) -> None:
        self._error = error

    async def generate_content(self, **_kwargs):
        raise self._error


class StubClient:
    def __init__(self, error: Exception) -> None:
        self.aio = type("Aio", (), {"models": RaisingModels(error)})()


def provider_raising(error: Exception) -> GeminiProvider:
    provider = GeminiProvider(api_key="test-key")
    provider._client = StubClient(error)  # no network in unit tests
    return provider


REQUEST = ProviderRequest(
    purpose="extract_answer", model="gemini-test", prompt="x", temperature=0.0, max_tokens=10
)


async def test_ai_orchestration_2_10_gemini_429_becomes_rate_limited():
    provider = provider_raising(errors.ClientError(429, quota_error("36s")))

    with pytest.raises(ProviderRateLimited) as raised:
        await provider.generate(REQUEST)
    assert raised.value.retry_after == 36


async def test_ai_orchestration_2_10_gemini_other_client_errors_are_not_rate_limits():
    provider = provider_raising(errors.ClientError(400, {"error": {"code": 400}}))

    with pytest.raises(errors.ClientError):
        await provider.generate(REQUEST)
