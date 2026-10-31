"""Self-review additions to tutor-reply-stream (2026-10-31), AC-19 to AC-22 of
specs/features/tutor/tutor-reply-stream.md. Fake provider only, no network.
"""

from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.ai.gateway as gateway_module
from app.ai.gateway import AIProviderError, Gateway, get_gateway
from app.ai.providers.base import ProviderRequest, StreamUsage
from app.ai.providers.fake import FakeProvider
from app.ai.providers.gemini import GeminiProvider
from app.main import app
from app.settings import get_settings
from tests.unit.test_tutor_reply_stream_api import DEGRADE_TEXT, URL, make_gateway, parse_sse

MESSAGE = {"message": "สวัสดี"}


@pytest.fixture(autouse=True)
def no_retry_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(gateway_module, "_sleep", fake_sleep)


@pytest.fixture
def use_gateway() -> Iterator[Callable[[Gateway], None]]:
    def install(gateway: Gateway) -> None:
        app.dependency_overrides[get_gateway] = lambda: gateway

    yield install
    app.dependency_overrides.pop(get_gateway, None)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


# --- AC-19 errors inside the stream never leak and always end the stream -------------


def test_AI01_send_message_config_error_ends_with_error_event(client, use_gateway):
    # A live gateway with no provider for the tier's model: AIConfigError after the 200.
    settings = get_settings()
    use_gateway(Gateway.live(settings.ai, settings.env.prompts_dir, providers={}))

    events = parse_sse(client.post(URL, json={"text": "x"}).text)

    assert [name for name, _ in events] == ["error"]
    assert events[0][1]["code"] == "internal_error"
    assert "provider" not in events[0][1]["message"]


def test_AI01_send_message_error_message_hides_provider_text(client, use_gateway):
    fake = FakeProvider({"tutor_reply": [["ถูก", RuntimeError("500 INTERNAL project-secret")]]})
    use_gateway(make_gateway(fake, retries=0))

    events = parse_sse(client.post(URL, json={"text": "x"}).text)

    assert events[-1][0] == "error"
    assert "project-secret" not in events[-1][1]["message"]


# --- AC-20 a reply with no text is a failure, not an empty turn -----------------------


async def test_AI01_stream_without_text_is_retried_then_fails():
    fake = FakeProvider({"tutor_reply": [[""], [""]]})
    gateway = make_gateway(fake, retries=1)

    with pytest.raises(AIProviderError, match="no text"):
        async for _ in gateway.stream("tutor_reply", MESSAGE):
            pass
    assert len(fake.requests) == 2


def test_AI01_send_message_degrades_when_reply_has_no_text(client, use_gateway):
    fake = FakeProvider({"tutor_reply": [[""], [""]]})
    use_gateway(make_gateway(fake, retries=1))

    events = parse_sse(client.post(URL, json={"text": "x"}).text)

    assert events == [("token", {"speaker": "tutor", "text": DEGRADE_TEXT}), ("done", {})]


# --- AC-21 blank text is no message ------------------------------------------------


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_AI01_send_message_rejects_blank_text(client, use_gateway, text: str):
    fake = FakeProvider({"tutor_reply": [["ไม่ควรถูกเรียก"]]})
    use_gateway(make_gateway(fake))

    response = client.post(URL, json={"text": text})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert fake.requests == []


# --- AC-22 long-lived fake and provider streams are closed ---------------------------


async def test_AI03_fake_without_record_keeps_no_history():
    fake = FakeProvider({}, defaults={"tutor_reply": ["ตอบ ซ้ำ"]}, record=False)
    gateway = make_gateway(fake)

    for _ in range(3):
        async for _chunk in gateway.stream("tutor_reply", MESSAGE):
            pass

    assert fake.requests == []
    assert fake.chunks_sent == []


async def test_AI01_gemini_stream_closes_the_sdk_stream_when_closed_early():
    closed: list[bool] = []

    class SdkStream:
        def __init__(self) -> None:
            self._texts = ["ถูก", "แล้ว", "ครับ"]

        def __aiter__(self) -> "SdkStream":
            return self

        async def __anext__(self) -> Any:
            if not self._texts:
                raise StopAsyncIteration
            return type("Chunk", (), {"text": self._texts.pop(0), "usage_metadata": None})()

        async def aclose(self) -> None:
            closed.append(True)

    class Models:
        async def generate_content_stream(self, **_kwargs: Any) -> SdkStream:
            return SdkStream()

    provider = GeminiProvider(api_key="test-key")
    provider._client = type("C", (), {"aio": type("A", (), {"models": Models()})()})()
    request = ProviderRequest(
        purpose="tutor_reply", model="gemini-test", prompt="x", temperature=0.0, max_tokens=10
    )

    chunks = provider.stream(request, StreamUsage())
    assert await anext(chunks) == "ถูก"
    await chunks.aclose()

    assert closed == [True]
