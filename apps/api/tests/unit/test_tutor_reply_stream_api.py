"""POST /sessions/{id}/messages streams tutor_reply from the gateway (PoC P4-lite).

Behavior from specs/features/tutor/tutor-reply-stream.md §2 "Endpoint", AC-11 to AC-18.
The gateway is replaced through the ``get_gateway`` dependency with a fake provider.

Starlette's TestClient returns the body only after the app finishes, so the tests about
timing (AC-11) and disconnects (AC-18) drive the ASGI app directly with ``run_asgi``.
"""

import asyncio
import json
from collections.abc import Awaitable, Callable, Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.ai.gateway as gateway_module
from app.ai.gateway import CallRecord, Gateway, get_gateway
from app.ai.providers.fake import FakeProvider
from app.main import app
from app.models.room import DoneEvent, ErrorEvent, TokenEvent
from app.settings import get_settings

SESSION_ID = "00000000-0000-4000-8000-000000000002"
URL = f"/sessions/{SESSION_ID}/messages"
DEGRADE_TEXT = "ระบบช้า ลองส่งอีกทีนะ"  # api.md "ระบบช้า"
EVENT_MODELS = {"token": TokenEvent, "done": DoneEvent, "error": ErrorEvent}


def make_gateway(fake: FakeProvider, retries: int | None = None) -> Gateway:
    config = get_settings().ai
    if retries is not None:
        config = config.model_copy(
            update={"gateway": config.gateway.model_copy(update={"retries": retries})}
        )
    return Gateway(config=config, prompts_dir=get_settings().env.prompts_dir, provider=fake)


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


def parse_sse(body: str) -> list[tuple[str, Any]]:
    events = []
    for block in body.replace("\r\n", "\n").split("\n\n"):
        name, data = "message", []
        for line in block.split("\n"):
            if not line or line.startswith(":"):
                continue
            field, _, value = line.partition(":")
            value = value.removeprefix(" ")
            if field == "event":
                name = value
            elif field == "data":
                data.append(value)
        if data:
            events.append((name, json.loads("\n".join(data))))
    for name, data in events:
        if name in EVENT_MODELS:
            EVENT_MODELS[name].model_validate(data)
    return events


def tokens(events: list[tuple[str, Any]]) -> list[str]:
    return [data["text"] for name, data in events if name == "token"]


async def run_asgi(
    body: dict[str, Any],
    on_text: Callable[[str], Awaitable[None]] | None = None,
    disconnect: asyncio.Event | None = None,
) -> tuple[int, dict[str, str], str]:
    """POST ``body`` to the app and return (status, headers, body text). ``on_text`` gets the
    body received so far after every chunk; setting ``disconnect`` makes the client leave."""
    request = json.dumps(body).encode()
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": URL,
        "raw_path": URL.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [(b"content-type", b"application/json"), (b"host", b"test")],
        "client": ("test", 1),
        "server": ("test", 80),
    }
    sent_request = False
    leave = disconnect or asyncio.Event()
    status = 0
    headers: dict[str, str] = {}
    received = ""

    async def receive() -> dict[str, Any]:
        nonlocal sent_request
        if not sent_request:
            sent_request = True
            return {"type": "http.request", "body": request, "more_body": False}
        await leave.wait()
        return {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        nonlocal status, received
        if message["type"] == "http.response.start":
            status = message["status"]
            headers.update({k.decode().lower(): v.decode() for k, v in message["headers"]})
        elif message["type"] == "http.response.body":
            received += message.get("body", b"").decode()
            if on_text is not None:
                await on_text(received)

    await asyncio.wait_for(app(scope, receive, send), timeout=5)
    return status, headers, received


# --- AC-11 TTFT: the first token is not held back ---------------------------------------


async def test_NFR_P1_first_token_sent_before_stream_ends(use_gateway):
    release = asyncio.Event()
    first_seen = asyncio.Event()
    second_before_release: list[bool] = []

    async def hold() -> None:
        await release.wait()

    fake = FakeProvider({"tutor_reply": [["ถูก", hold, "แล้ว"]]})
    use_gateway(make_gateway(fake))

    async def on_text(text: str) -> None:
        if '"ถูก"' in text and not first_seen.is_set():
            second_before_release.append('"แล้ว"' in text)
            first_seen.set()

    task = asyncio.create_task(run_asgi({"text": "x"}, on_text=on_text))
    await asyncio.wait_for(first_seen.wait(), timeout=2)  # arrives while the provider waits
    assert second_before_release == [False]
    release.set()
    status, _, body = await task

    assert status == 200
    events = parse_sse(body)
    assert tokens(events) == ["ถูก", "แล้ว"]
    assert events[-1] == ("done", {})


# --- AC-12 to AC-17 -------------------------------------------------------------------


def test_AI01_send_message_streams_tokens_then_done(client, use_gateway):
    fake = FakeProvider({"tutor_reply": [["ก", "ข", "ค"]]})
    use_gateway(make_gateway(fake))

    response = client.post(URL, json={"text": "x"})

    assert response.status_code == 200
    assert "x-stub" not in response.headers
    events = parse_sse(response.text)
    assert [name for name, _ in events] == ["token", "token", "token", "done"]
    assert all(data["speaker"] == "tutor" for name, data in events if name == "token")
    assert tokens(events) == ["ก", "ข", "ค"]
    assert len(fake.requests) == 1


def test_AI01_send_message_degrades_when_provider_fails_first(client, use_gateway):
    fake = FakeProvider({"tutor_reply": [RuntimeError("down"), RuntimeError("still down")]})
    use_gateway(make_gateway(fake, retries=1))

    events = parse_sse(client.post(URL, json={"text": "x"}).text)

    assert events == [("token", {"speaker": "tutor", "text": DEGRADE_TEXT}), ("done", {})]


def test_AI01_send_message_error_after_partial_reply(client, use_gateway):
    fake = FakeProvider({"tutor_reply": [["ถูก", RuntimeError("cut")]]})
    use_gateway(make_gateway(fake, retries=1))

    events = parse_sse(client.post(URL, json={"text": "x"}).text)

    names = [name for name, _ in events]
    assert names == ["token", "error"]
    assert tokens(events) == ["ถูก"]
    # spec §10 item 3: proposed code, pending Junior (api.md "รอตัดสิน" item 3)
    assert events[-1][1]["code"] == "ai_unavailable"
    assert events[-1][1]["message"]
    assert "done" not in names


@pytest.mark.parametrize("extra", [-1, 0, 1])
def test_AI01_send_message_length_boundary(client, use_gateway, extra: int):
    limit = get_settings().ai.guards.max_message_chars
    text = "ก" * (limit + extra)  # Thai: counted in characters, not bytes
    fake = FakeProvider({"tutor_reply": [["ตอบ"]]})
    use_gateway(make_gateway(fake))

    response = client.post(URL, json={"text": text})

    if extra <= 0:
        assert response.status_code == 200
        assert tokens(parse_sse(response.text)) == ["ตอบ"]
    else:
        assert response.status_code == 422
        # spec §10 item 3: proposed code, pending Junior
        assert response.json()["error"]["code"] == "message_too_long"
        assert fake.requests == []


def test_AI01_send_message_image_keeps_stub(client, use_gateway):
    fake = FakeProvider({"tutor_reply": [["ไม่ควรถูกเรียก"]]})
    use_gateway(make_gateway(fake))

    response = client.post(URL, json={"image_path": "sessions/s1/วิธีทำ.jpg"})

    assert response.status_code == 200
    assert response.headers.get("x-stub") == "true"
    assert parse_sse(response.text)[-1][0] == "done"
    assert fake.requests == []


def test_TM08_send_message_sse_keeps_latex(client, use_gateway):
    chunks = ["$$a^2 - b^2", " = (a-b)(a+b)$$", " และ $\\frac{1}{2}$"]
    fake = FakeProvider({"tutor_reply": [chunks]})
    use_gateway(make_gateway(fake))

    events = parse_sse(client.post(URL, json={"text": "x"}).text)

    assert tokens(events) == chunks


# --- AC-18 the client leaves ----------------------------------------------------------


async def test_AI01_send_message_stops_provider_on_disconnect(use_gateway):
    never = asyncio.Event()  # never set: only a cancelled stream gets past hold()
    first_seen = asyncio.Event()
    leave = asyncio.Event()

    async def hold() -> None:
        await never.wait()

    fake = FakeProvider({"tutor_reply": [["ถูก", hold, "แล้ว", "ครับ"]]})
    gateway = make_gateway(fake)
    records: list[CallRecord] = []
    gateway.add_listener(records.append)
    use_gateway(gateway)

    async def on_text(text: str) -> None:
        if '"ถูก"' in text:
            first_seen.set()

    task = asyncio.create_task(run_asgi({"text": "x"}, on_text=on_text, disconnect=leave))
    await asyncio.wait_for(first_seen.wait(), timeout=2)
    leave.set()
    await asyncio.wait_for(task, timeout=2)  # finishes only if the stream stops reading

    assert fake.chunks_sent == ["ถูก"]
    assert len(records) == 1
