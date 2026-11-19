"""Rate limit of the tutor room's user messages (specs/features/ai/gateway-guards.md §2.1, AC-1 to
AC-11, AC-tenant).

``L`` is ``guards.rate_limit_messages_per_minute`` from config/ai.yaml, never a literal. Time is a
fake clock the test moves, so no test sleeps. The endpoint tests replace ``get_rate_limiter``
with a limiter on that clock and ``get_auth`` with the user the test names.
"""

import math
from collections.abc import Callable, Iterator
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.ai.gateway import get_gateway
from app.ai.providers.fake import FakeProvider
from app.auth import AuthContext, get_auth
from app.db.room import get_room_repository
from app.main import app
from app.rate_limit import RateLimiter, get_rate_limiter
from app.settings import get_settings
from tests.unit.test_room_sessions_api import PREP_ID, FakeRoomRepo, prep_record
from tests.unit.test_tutor_reply_stream_api import make_gateway

L = get_settings().ai.guards.rate_limit_messages_per_minute
WINDOW = 60.0  # "per minute" in the config key's name (spec §2.1)
EPS = 0.001

SESSION_ID = "00000000-0000-4000-8000-000000000002"
MESSAGES = f"/sessions/{SESSION_ID}/messages"
OCR_CONFIRM = f"/sessions/{SESSION_ID}/ocr/confirm"
IMAGE = {"image_path": f"t/sessions/{SESSION_ID}/x.jpg"}  # stub reply, no AI call
OCR_LINES = {"lines": ["x^2 - 5x + 6", "= (x - 2)(x + 3)", "= x^2 + x - 6"]}

TENANT_A = UUID("00000000-0000-4000-8000-0000000000a1")
TENANT_B = UUID("00000000-0000-4000-8000-0000000000b1")
U1 = UUID("00000000-0000-4000-8000-000000000101")
U2 = UUID("00000000-0000-4000-8000-000000000102")
U3 = UUID("00000000-0000-4000-8000-000000000103")


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def limiter(clock: FakeClock) -> Iterator[RateLimiter]:
    made = RateLimiter(limit=L, clock=clock)
    app.dependency_overrides[get_rate_limiter] = lambda: made
    yield made
    app.dependency_overrides.pop(get_rate_limiter, None)


@pytest.fixture
def as_user() -> Iterator[Callable[[UUID | None, UUID], None]]:
    """``as_user(user_id, tenant_id)`` makes the next requests come from that user; ``None``
    makes them anonymous (AUTH_REQUIRED=false)."""
    current: dict[str, AuthContext | None] = {"auth": None}

    def set_user(user_id: UUID | None, tenant_id: UUID = TENANT_A) -> None:
        current["auth"] = (
            None
            if user_id is None
            else AuthContext(tenant_id=tenant_id, user_id=user_id, token="t")
        )

    app.dependency_overrides[get_auth] = lambda: current["auth"]
    yield set_user
    app.dependency_overrides.pop(get_auth, None)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


def open_session_repo() -> FakeRoomRepo:
    """SESSION_ID as an open session the signed-in user can see (room-sessions-db.md)."""
    repo = FakeRoomRepo(preps={PREP_ID: prep_record()})
    repo.add_session(id=UUID(SESSION_ID))
    return repo


def send(
    client: TestClient, n: int, url: str = MESSAGES, body: Any = IMAGE, **kw: Any
) -> list[int]:
    return [client.post(url, json=body, **kw).status_code for _ in range(n)]


def assert_rate_limited(response: Any) -> int:
    assert response.status_code == 429
    assert set(response.json()) == {"error"}
    assert response.json()["error"]["code"] == "rate_limited"
    retry_after = response.headers["retry-after"]
    assert retry_after.isdigit() and int(retry_after) >= 1
    return int(retry_after)


# --- the counter -----------------------------------------------------------------------------


@pytest.mark.parametrize(("sent_before", "limited"), [(L - 2, False), (L - 1, False), (L, True)])
def test_TM21_limit_boundary(clock: FakeClock, sent_before: int, limited: bool) -> None:
    """AC-2: the (L - 1)th and Lth messages pass, the (L + 1)th does not."""
    limiter = RateLimiter(limit=L, clock=clock)
    for _ in range(sent_before):
        assert limiter.hit("u1") is None

    retry_after = limiter.hit("u1")

    assert (retry_after is not None) is limited
    if limited:
        assert isinstance(retry_after, int) and retry_after >= 1


@pytest.mark.parametrize(("later", "limited"), [(WINDOW - EPS, True), (WINDOW + EPS, False)])
def test_TM21_window_boundary(clock: FakeClock, later: float, limited: bool) -> None:
    """AC-3: L messages at t0 still count at t0 + 60 - ε and are gone at t0 + 60 + ε."""
    limiter = RateLimiter(limit=L, clock=clock)
    for _ in range(L):
        limiter.hit("u1")

    clock.advance(later)

    assert (limiter.hit("u1") is not None) is limited


def test_TM21_rejected_messages_do_not_count(clock: FakeClock) -> None:
    """AC-4: retrying after a 429 does not push the wait further out."""
    limiter = RateLimiter(limit=L, clock=clock)
    for _ in range(L):
        limiter.hit("u1")
    first = limiter.hit("u1")

    waits = [limiter.hit("u1") for _ in range(5)]

    assert first is not None and all(w is not None and w <= first for w in waits)
    clock.advance(WINDOW + EPS)
    assert limiter.hit("u1") is None  # only the L accepted messages were in the window


def test_TM21_retry_after_counts_to_the_oldest_message(clock: FakeClock) -> None:
    limiter = RateLimiter(limit=L, clock=clock)
    limiter.hit("u1")
    clock.advance(10.5)
    for _ in range(L - 1):
        limiter.hit("u1")

    retry_after = limiter.hit("u1")

    assert retry_after == math.ceil(WINDOW - 10.5)


def test_TM21_keys_are_counted_separately(clock: FakeClock) -> None:
    """AC-7 at the counter level."""
    limiter = RateLimiter(limit=L, clock=clock)
    for _ in range(L):
        limiter.hit("u1")

    assert limiter.hit("u1") is not None
    assert limiter.hit("u2") is None


def test_TM21_limit_comes_from_config() -> None:
    """AC-10: the app's limiter uses guards.rate_limit_messages_per_minute."""
    get_rate_limiter.cache_clear()

    assert get_rate_limiter().limit == L


def test_TM21_a_smaller_configured_limit_applies(clock: FakeClock) -> None:
    """AC-10: with a limit of 3 the 4th message is refused."""
    limiter = RateLimiter(limit=3, clock=clock)

    results = [limiter.hit("u1") for _ in range(4)]

    assert results[:3] == [None, None, None] and results[3] is not None


# --- the endpoints -----------------------------------------------------------------------------


def test_TM21_l_messages_in_a_minute_pass(client, limiter, as_user) -> None:
    """AC-1"""
    as_user(U1)

    assert send(client, L) == [200] * L


def test_TM21_message_over_the_limit_is_429_without_an_ai_call(client, limiter, as_user) -> None:
    """AC-2: the (L + 1)th text message gets 429 and tutor_reply is not called for it."""
    fake = FakeProvider({"tutor_reply": ["ตอบ"] * (L + 1)})
    app.dependency_overrides[get_gateway] = lambda: make_gateway(fake)
    # A signed-in text message goes to the DB (room-sessions-db.md AC-auth-real): SESSION_ID is
    # an open session in a fake repository (Jam ยังไม่ ok · 2026-11-12 · PR #123).
    app.dependency_overrides[get_room_repository] = open_session_repo
    try:
        as_user(U1)
        assert send(client, L, body={"text": "ข้อ 1"}) == [200] * L

        response = client.post(MESSAGES, json={"text": "ข้อ 1"})

        assert_rate_limited(response)
        assert len(fake.requests) == L
    finally:
        app.dependency_overrides.pop(get_gateway, None)
        app.dependency_overrides.pop(get_room_repository, None)


def test_TM21_retry_after_a_429_stays_429(client, limiter, as_user) -> None:
    """AC-4 through the endpoint."""
    as_user(U1)
    send(client, L)
    first = assert_rate_limited(client.post(MESSAGES, json=IMAGE))

    for _ in range(5):
        assert assert_rate_limited(client.post(MESSAGES, json=IMAGE)) <= first


def test_TM21_messages_and_ocr_confirm_share_one_counter(client, limiter, as_user) -> None:
    """AC-5"""
    as_user(U1)
    send(client, L - 1)

    assert client.post(OCR_CONFIRM, json=OCR_LINES).status_code == 200
    assert_rate_limited(client.post(MESSAGES, json=IMAGE))
    assert_rate_limited(client.post(OCR_CONFIRM, json=OCR_LINES))


def test_TM21_other_room_endpoints_are_not_limited(client, limiter, as_user) -> None:
    """AC-6"""
    as_user(U1)
    send(client, L)
    upload = {"kind": "image", "content_type": "image/jpeg", "file_name": "a.jpg", "size_bytes": 9}
    # A signed-in GET /sessions/{id} reads the DB (room-sessions-db.md AC-auth-real): SESSION_ID
    # is an open session in a fake repository (Jam ยังไม่ ok · 2026-11-12 · PR #123).
    app.dependency_overrides[get_room_repository] = open_session_repo
    try:
        assert client.get(f"/sessions/{SESSION_ID}").status_code == 200
    finally:
        app.dependency_overrides.pop(get_room_repository, None)
    assert client.post(f"/sessions/{SESSION_ID}/uploads", json=upload).status_code == 200
    assert (
        client.post(
            f"/sessions/{SESSION_ID}/transcribe", json={"audio_path": "t/a.webm"}
        ).status_code
        == 200
    )


def test_TM21_each_user_has_their_own_limit(client, limiter, as_user) -> None:
    """AC-7"""
    as_user(U1)
    send(client, L)
    assert_rate_limited(client.post(MESSAGES, json=IMAGE))

    as_user(U2)

    assert client.post(MESSAGES, json=IMAGE).status_code == 200


def test_SA06_rate_limit_does_not_cross_tenants_or_leak_ids(client, limiter, as_user) -> None:
    """AC-tenant"""
    as_user(U1, TENANT_A)
    send(client, L)
    refused = client.post(MESSAGES, json=IMAGE)
    assert_rate_limited(refused)

    as_user(U3, TENANT_B)
    assert client.post(MESSAGES, json=IMAGE).status_code == 200

    body = refused.text
    for secret in (str(U1), str(U3), str(TENANT_A), str(TENANT_B)):
        assert secret not in body


def test_TM21_anonymous_requests_are_counted_per_client_ip(client, limiter, as_user) -> None:
    """AC-8: without a token the first X-Forwarded-For address is the key."""
    as_user(None)
    first_ip = {"X-Forwarded-For": "203.0.113.7, 10.0.0.1"}
    send(client, L, headers=first_ip)

    assert_rate_limited(client.post(MESSAGES, json=IMAGE, headers=first_ip))
    other = client.post(MESSAGES, json=IMAGE, headers={"X-Forwarded-For": "198.51.100.2"})
    assert other.status_code == 200


def test_TM21_invalid_bodies_count_too(client, limiter, as_user) -> None:
    """AC-9"""
    as_user(U1)
    assert send(client, L, body={}) == [422] * L

    assert_rate_limited(client.post(MESSAGES, json=IMAGE))


@pytest.mark.parametrize("path", ["/sessions/{id}/messages", "/sessions/{id}/ocr/confirm"])
def test_TM21_openapi_documents_429(client, path: str) -> None:
    """AC-11"""
    responses = client.get("/openapi.json").json()["paths"][path]["post"]["responses"]

    schema = responses["429"]["content"]["application/json"]["schema"]
    assert schema["$ref"] == "#/components/schemas/ErrorResponse"
