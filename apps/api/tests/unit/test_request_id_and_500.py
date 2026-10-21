"""api.md Conventions: X-Request-Id on every response, and the error envelope for unhandled 500s.

Issue #50. Middleware order (outer → inner): request id → CORS → unhandled-error catcher.
The catcher sits inside CORS so a 500 still carries Access-Control-Allow-Origin; without it
the browser reports a CORS error instead of the 500 (#49). It sits inside the request id
middleware so the 500 also carries X-Request-Id.
"""

import logging
from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sse_starlette import EventSourceResponse
from starlette.middleware.cors import CORSMiddleware

from app.main import app
from app.middleware import (
    RequestIdMiddleware,
    UnhandledErrorMiddleware,
    get_request_id,
    install_middleware,
)
from app.settings import EnvSettings
from tests.unit.test_room_api_contract import parse_sse

LOCAL = "http://localhost:3000"
ROOM = "/sessions/00000000-0000-4000-8000-000000000002"
SECRET = "db password is hunter2"  # must never reach the client


def _is_uuid(value: str | None) -> bool:
    try:
        UUID(value or "")
    except ValueError:
        return False
    return True


def _test_app() -> FastAPI:
    api = FastAPI()
    install_middleware(api, EnvSettings(_env_file=None))

    @api.get("/boom")
    async def boom() -> None:
        raise RuntimeError(SECRET)

    @api.get("/echo-request-id")
    async def echo() -> dict[str, str | None]:
        return {"request_id": get_request_id()}

    @api.get("/stream-then-boom")
    async def stream_then_boom() -> EventSourceResponse:
        async def events() -> AsyncIterator[dict[str, str]]:
            yield {"event": "token", "data": '{"text": "ok"}'}
            raise RuntimeError(SECRET)

        return EventSourceResponse(events())

    return api


@pytest.fixture
def main_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def client() -> TestClient:
    # raise_server_exceptions=False: see the response the browser gets, not the traceback.
    return TestClient(_test_app(), raise_server_exceptions=False)


# --- wiring -------------------------------------------------------------------


def test_apimd_conventions_main_app_middleware_order() -> None:
    # user_middleware[0] is the outermost.
    assert [m.cls for m in app.user_middleware] == [
        RequestIdMiddleware,
        CORSMiddleware,
        UnhandledErrorMiddleware,
    ]


# --- X-Request-Id ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "path", "kwargs"),
    [
        ("get", "/health", {}),
        ("get", ROOM, {}),  # 200 JSON
        ("post", f"{ROOM}/messages", {"json": {"text": "hi"}}),  # 200 SSE
        ("get", "/no-such-path", {}),  # 404 envelope
        ("get", "/sessions/not-a-uuid", {}),  # 422 envelope
        ("delete", "/health", {}),  # 405 envelope
    ],
)
def test_apimd_conventions_every_response_has_request_id(
    main_client: TestClient, method: str, path: str, kwargs: dict
) -> None:
    response = getattr(main_client, method)(path, **kwargs)

    assert _is_uuid(response.headers.get("x-request-id"))


def test_apimd_conventions_cors_preflight_has_request_id(main_client: TestClient) -> None:
    response = main_client.options(
        f"{ROOM}/messages",
        headers={"Origin": LOCAL, "Access-Control-Request-Method": "POST"},
    )

    assert response.status_code == 200
    assert _is_uuid(response.headers.get("x-request-id"))


def test_apimd_conventions_request_ids_differ_per_request(main_client: TestClient) -> None:
    ids = {main_client.get("/health").headers["x-request-id"] for _ in range(3)}

    assert len(ids) == 3


def test_apimd_conventions_client_uuid_request_id_is_kept(main_client: TestClient) -> None:
    sent = str(uuid4())

    assert (
        main_client.get("/health", headers={"X-Request-Id": sent}).headers["x-request-id"] == sent
    )


@pytest.mark.parametrize("sent", ["abc", "", "1" * 1000, "00000000-0000-4000-8000-00000000000g"])
def test_apimd_conventions_non_uuid_request_id_is_replaced(
    main_client: TestClient, sent: str
) -> None:
    # Only a UUID is trusted, so a client cannot put arbitrary text into our logs.
    received = main_client.get("/health", headers={"X-Request-Id": sent}).headers["x-request-id"]

    assert received != sent
    assert _is_uuid(received)


def test_apimd_conventions_handler_sees_same_request_id(client: TestClient) -> None:
    # get_request_id() is how the gateway (ai_calls.request_id) and logs pick up the id.
    response = client.get("/echo-request-id")

    assert response.json()["request_id"] == response.headers["x-request-id"]


def test_apimd_conventions_request_id_is_none_outside_a_request() -> None:
    assert get_request_id() is None


# --- unhandled 500 --------------------------------------------------------------


def test_apimd_conventions_unhandled_error_returns_500_envelope(client: TestClient) -> None:
    response = client.get("/boom")

    assert response.status_code == 500
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Internal server error"}
    }


def test_apimd_conventions_500_does_not_leak_exception_text(client: TestClient) -> None:
    assert SECRET not in client.get("/boom").text


def test_apimd_conventions_500_keeps_cors_and_request_id(client: TestClient) -> None:
    response = client.get("/boom", headers={"Origin": LOCAL})

    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == LOCAL
    assert _is_uuid(response.headers.get("x-request-id"))


def test_apimd_conventions_500_is_logged_with_request_id(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.ERROR):
        response = client.get("/boom")

    [record] = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert record.exc_info is not None
    assert SECRET in str(record.exc_info[1])  # the log keeps the detail the client never sees
    assert record.request_id == response.headers["x-request-id"]


def test_apimd_sse_error_after_stream_started_sends_error_then_done(client: TestClient) -> None:
    # Once SSE headers are sent the status cannot change to 500, so the failure becomes the
    # `error` event (api.md SSE events) and the stream still ends with `done` (Conventions).
    response = client.get("/stream-then-boom")

    assert response.status_code == 200
    assert parse_sse(response.text) == [
        ("token", {"text": "ok"}),
        ("error", {"code": "internal_error", "message": "Internal server error"}),
        ("done", {}),
    ]
    assert SECRET not in response.text
