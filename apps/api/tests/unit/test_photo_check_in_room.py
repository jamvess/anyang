"""A photo answer gets a real ocr_preview and verdict in the room (P1 + P2 in the chat).

Behavior from specs/features/check/photo-check-in-room.md §2, AC-1 to AC-19, AC-E4.

The gateway, the image store and the room state are FastAPI dependencies (spec §2.4), replaced
here with a fake provider, ``FakeImageStore`` and a fresh ``InMemoryRoomState`` per test.
SymPy is the real one (the checker pipeline runs it). Every session starts with the stub
problem ``p1``: factor x^2 - 49, reference (x-7)(x+7), ``factored`` (spec §3, §10 item 8).
Tests that need no image store leave ``get_image_store`` alone: its default means "no Storage
yet", so the stub streams stay (AC-10).
"""

import json
import logging
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.ai.gateway as gateway_module
import app.services.photo_check as photo_check
from app import stubs
from app.ai.gateway import Gateway, get_gateway
from app.ai.providers.base import Image
from app.ai.providers.fake import FakeProvider
from app.main import app
from app.models.room import EVENT_MODELS
from app.services.photo_check import get_image_store
from app.services.room_state import InMemoryRoomState, get_room_state
from app.settings import get_settings

SESSION_ID = "00000000-0000-4000-8000-000000000002"
OTHER_SESSION_ID = "00000000-0000-4000-8000-000000000003"
OTHER_TENANT = "00000000-0000-4000-8000-0000000000ff"
TENANT = stubs.tenant_of(None)  # tests run with AUTH_REQUIRED=false (tests/conftest.py)
PHOTO = f"{TENANT}/sessions/{SESSION_ID}/answer.jpeg"
IMAGE = Image(data=b"\xff\xd8 handwritten answer", mime_type="image/jpeg")
BYTES_PER_MB = 1_048_576  # api.md v1.7 "/uploads": 1 MB = 1,048,576 bytes

LOOKING = "ขอดูก่อนนะ"
CHECK_PLEASE = "เช็คให้หน่อยว่าอ่านถูกไหม"
UNREADABLE = "รูปนี้อ่านไม่ออก ลองถ่ายใหม่ให้ชัดขึ้นอีกนิดนะ"
DEGRADE = "ระบบช้า ลองส่งอีกทีนะ"

P1_TEXT = "แยกตัวประกอบ $x^2 - 49$"
P1_REFERENCE = "(x-7)(x+7)"
RIGHT = ["x^2 - 49", "= (x-7)(x+7)"]
WRONG = ["x^2 - 49", "= (x-7)(x-7)"]


def extract(*lines: tuple[str, float]) -> str:
    """An ``extract_answer`` reply (ExtractAnswerResult) with these (latex, confidence) lines."""
    return json.dumps(
        {"lines": [{"latex": latex, "confidence": c} for latex, c in lines], "notes": ""}
    )


def classify(error_type: str | None, verdict: str | None, line: int | None) -> str:
    """A ``check_answer`` classifier reply (CheckAnswerResult)."""
    return json.dumps(
        {
            "error_type": error_type,
            "evidence": "บรรทัด 2: +7 กลายเป็น -7" if line else "",
            "method": "doc",
            "verdict": verdict,
            "first_wrong_line": line,
            "confidence": 0.9,
        },
        ensure_ascii=False,
    )


CLASSIFY_RIGHT = classify(None, "correct", None)
CLASSIFY_SIGN = classify("sign", "incorrect", 2)
TWO_LINES = extract((RIGHT[0], 0.97), (RIGHT[1], 0.95))


class FakeImageStore:
    def __init__(self, files: dict[str, Image]) -> None:
        self.files = files
        self.reads: list[str] = []

    async def read(self, path: str) -> Image | None:
        self.reads.append(path)
        return self.files.get(path)


def make_gateway(fake: FakeProvider) -> Gateway:
    """No retries, so one scripted failure is the final failure."""
    config = get_settings().ai
    config = config.model_copy(
        update={"gateway": config.gateway.model_copy(update={"retries": 0, "schema_retries": 0})}
    )
    return Gateway(config=config, prompts_dir=get_settings().env.prompts_dir, provider=fake)


@pytest.fixture(autouse=True)
def no_retry_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(gateway_module, "_sleep", fake_sleep)


@pytest.fixture(autouse=True)
def fresh_room_state() -> Iterator[InMemoryRoomState]:
    state = InMemoryRoomState()
    app.dependency_overrides[get_room_state] = lambda: state
    yield state
    app.dependency_overrides.pop(get_room_state, None)
    app.dependency_overrides.pop(get_gateway, None)
    app.dependency_overrides.pop(get_image_store, None)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def room() -> Callable[..., tuple[FakeProvider, FakeImageStore]]:
    """Install a fake provider scripted per purpose and an image store holding ``files``."""

    def install(
        script: dict[str, list[Any]], files: dict[str, Image] | None = None
    ) -> tuple[FakeProvider, FakeImageStore]:
        fake = FakeProvider(script)
        store = FakeImageStore({PHOTO: IMAGE} if files is None else files)
        app.dependency_overrides[get_gateway] = lambda: make_gateway(fake)
        app.dependency_overrides[get_image_store] = lambda: store
        return fake, store

    return install


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


def names(events: list[tuple[str, Any]]) -> list[str]:
    return [name for name, _ in events]


def tokens(events: list[tuple[str, Any]]) -> list[str]:
    return [data["text"] for name, data in events if name == "token"]


def requests_for(fake: FakeProvider, purpose: str) -> list[Any]:
    return [r for r in fake.requests if r.purpose == purpose]


def send_photo(client: TestClient, session_id: str = SESSION_ID, **body: Any) -> Any:
    return client.post(f"/sessions/{session_id}/messages", json={"image_path": PHOTO} | body)


def confirm(client: TestClient, lines: list[str], session_id: str = SESSION_ID) -> Any:
    return client.post(f"/sessions/{session_id}/ocr/confirm", json={"lines": lines})


def error_code(response: Any) -> str:
    return response.json()["error"]["code"]


# --- send a photo ---------------------------------------------------------------------


def test_TM06_photo_streams_real_ocr_preview(client, room):
    # AC-1, AC-4
    fake, store = room({"extract_answer": [TWO_LINES]})

    response = send_photo(client)

    assert response.status_code == 200
    assert "x-stub" not in response.headers
    events = parse_sse(response.text)
    assert events == [
        ("token", {"speaker": "tutor", "text": LOOKING}),
        (
            "ocr_preview",
            {
                "lines": [
                    {"latex": RIGHT[0], "confidence": 0.97},
                    {"latex": RIGHT[1], "confidence": 0.95},
                ]
            },
        ),
        ("token", {"speaker": "tutor", "text": CHECK_PLEASE}),
        ("done", {}),
    ]
    assert store.reads == [PHOTO]
    [request] = requests_for(fake, "extract_answer")
    assert request.images == [IMAGE]  # same bytes and mime type
    assert P1_TEXT in request.prompt  # problem_text is the pending problem


def test_AM02_photo_always_asks_to_confirm(client, room):
    # AC-2: even when the model is sure of every line, nothing is checked before confirming.
    fake, _ = room({"extract_answer": [extract((RIGHT[0], 1.0), (RIGHT[1], 1.0))]})

    events = parse_sse(send_photo(client).text)

    assert "ocr_preview" in names(events)
    assert "verdict" not in names(events)
    assert requests_for(fake, "check_answer") == []


def test_TM06_caption_does_not_reach_extract_answer(client, room):
    # AC-3
    fake, _ = room({"extract_answer": [TWO_LINES]})

    response = send_photo(client, text="ข้อ 2 ครับ")

    assert response.status_code == 200
    [request] = requests_for(fake, "extract_answer")
    assert "ข้อ 2 ครับ" not in request.prompt


def test_AM01_unreadable_photo_asks_for_a_new_one(client, room):
    # AC-5 (UC-04 E1)
    room({"extract_answer": [extract()]})

    events = parse_sse(send_photo(client).text)

    assert events == [
        ("token", {"speaker": "tutor", "text": LOOKING}),
        ("token", {"speaker": "tutor", "text": UNREADABLE}),
        ("done", {}),
    ]


def test_AM02_new_photo_replaces_pending_preview(client, room):
    # AC-6
    three_lines = extract((RIGHT[0], 0.9), (RIGHT[1], 0.9), ("= (x+7)(x-7)", 0.9))
    room(
        {
            "extract_answer": [TWO_LINES, three_lines],
            "check_answer": [CLASSIFY_RIGHT],
            "explain_check": ["ถูกแล้ว"],
        }
    )
    send_photo(client)
    send_photo(client)

    mismatch = confirm(client, RIGHT)
    checked = confirm(client, [*RIGHT, "= (x+7)(x-7)"])

    assert mismatch.status_code == 422
    assert error_code(mismatch) == "ocr_lines_mismatch"
    assert checked.status_code == 200
    assert "verdict" in names(parse_sse(checked.text))


@pytest.mark.parametrize(
    "failure",
    [
        pytest.param(RuntimeError("down"), id="provider error"),
        pytest.param("not json", id="schema error"),
    ],
)
def test_AM01_extract_answer_failure_degrades(client, room, failure):
    # AC-7: the earlier preview, if any, can still be confirmed.
    room(
        {
            "extract_answer": [TWO_LINES, failure],
            "check_answer": [CLASSIFY_RIGHT],
            "explain_check": ["ถูกแล้ว"],
        }
    )
    send_photo(client)

    events = parse_sse(send_photo(client).text)
    still_pending = confirm(client, RIGHT)

    assert events == [
        ("token", {"speaker": "tutor", "text": LOOKING}),
        ("token", {"speaker": "tutor", "text": DEGRADE}),
        ("done", {}),
    ]
    assert still_pending.status_code == 200
    assert "verdict" in names(parse_sse(still_pending.text))


@pytest.mark.parametrize(
    "path",
    [
        pytest.param(f"{OTHER_TENANT}/sessions/{SESSION_ID}/answer.jpeg", id="other tenant"),
        pytest.param(f"{TENANT}/sessions/{OTHER_SESSION_ID}/answer.jpeg", id="other session"),
    ],
)
def test_SA06_image_path_of_another_session_is_not_found(client, room, path):
    # AC-8: refused before the SSE starts, without reading the file or calling a model.
    fake, store = room({}, files={path: IMAGE})

    response = client.post(f"/sessions/{SESSION_ID}/messages", json={"image_path": path})

    assert response.status_code == 404
    assert error_code(response) == "not_found"
    assert store.reads == []
    assert fake.requests == []


def test_TM06_missing_image_is_not_found(client, room):
    # AC-9
    fake, _ = room({}, files={})

    response = send_photo(client)

    assert response.status_code == 404
    assert error_code(response) == "not_found"
    assert fake.requests == []


@pytest.mark.parametrize(("extra", "accepted"), [(-1, True), (0, True), (1, False)])
def test_TM21_image_size_boundary(client, room, extra, accepted):
    # AC-boundary: the real file size is checked again, at the same limit as /uploads.
    limit = get_settings().ai.guards.max_image_mb * BYTES_PER_MB
    big = Image(data=b"\0" * (limit + extra), mime_type="image/jpeg")
    fake, _ = room({"extract_answer": [TWO_LINES]}, files={PHOTO: big})

    response = send_photo(client)

    if accepted:
        assert response.status_code == 200
        assert "ocr_preview" in names(parse_sse(response.text))
    else:
        assert response.status_code == 422
        assert error_code(response) == "file_too_large"
        assert fake.requests == []


def test_TM06_photo_stays_stub_without_storage(client):
    # AC-10: no image store override, so "no Storage yet" (the default) keeps the stubs.
    fake = FakeProvider({})
    app.dependency_overrides[get_gateway] = lambda: make_gateway(fake)

    photo = send_photo(client)
    confirmed = confirm(client, ["x^2 - 5x + 6", "= (x - 2)(x + 3)", "= x^2 + x - 6"])

    assert photo.headers.get("x-stub") == "true"
    assert parse_sse(photo.text) == stubs.events("image_reply")
    assert parse_sse(confirmed.text) == stubs.events("ocr_confirm")
    assert fake.requests == []


# --- confirm --------------------------------------------------------------------------


def test_AM04_confirmed_answer_gets_verdict_before_tutor(client, room):
    # AC-11
    room(
        {
            "extract_answer": [TWO_LINES],
            "check_answer": [CLASSIFY_RIGHT],
            "explain_check": [["ถูก", "แล้ว"]],
        }
    )
    send_photo(client)

    response = confirm(client, RIGHT)

    assert response.status_code == 200
    events = parse_sse(response.text)
    assert names(events) == ["verdict", "token", "token", "done"]
    assert events[0] == (
        "verdict",
        {"verdict": "correct", "first_wrong_line": None, "error_type": None},
    )
    assert tokens(events) == ["ถูก", "แล้ว"]


def test_AM05_wrong_line_and_error_type_in_verdict(client, room):
    # AC-12: the wrong line comes from SymPy, the error type from the classifier.
    room(
        {
            "extract_answer": [TWO_LINES],
            "check_answer": [CLASSIFY_SIGN],
            "explain_check": ["บรรทัด 2"],
        }
    )
    send_photo(client)

    events = parse_sse(confirm(client, WRONG).text)

    assert events[0] == (
        "verdict",
        {"verdict": "incorrect", "first_wrong_line": 2, "error_type": "sign"},
    )


def test_AM04_checker_uses_confirmed_lines(client, room):
    # AC-13: the preview misread line 2; the user fixed it, and the fixed line is checked.
    misread = extract((WRONG[0], 0.9), (WRONG[1], 0.9))
    fake, _ = room(
        {"extract_answer": [misread], "check_answer": [CLASSIFY_RIGHT], "explain_check": ["ถูกแล้ว"]}
    )
    send_photo(client)

    events = parse_sse(confirm(client, RIGHT).text)

    assert events[0][1]["verdict"] == "correct"
    [request] = requests_for(fake, "check_answer")
    assert f"2. {RIGHT[1]}" in request.prompt
    assert f"2. {WRONG[1]}" not in request.prompt


@pytest.mark.parametrize(
    ("sent", "edited"),
    [
        pytest.param(["x^2 - 49", "= (x-7)(x+7)", "= (x+7)(x-7)"], [2], id="line 2 edited"),
        pytest.param(["x^2 - 49", "= (x+7)(x-7)", "= (x+7)(x-7)"], [], id="nothing edited"),
    ],
)
def test_AM03_confirm_logs_edited_lines(client, room, caplog, sent, edited):
    # AC-14: one JSON line per confirm that gets a verdict; no answer text in it.
    caplog.set_level(logging.INFO, logger="app.ocr.confirm")
    preview = extract(("x^2 - 49", 0.9), ("= (x+7)(x-7)", 0.9), ("= (x+7)(x-7)", 0.9))
    room(
        {"extract_answer": [preview], "check_answer": [CLASSIFY_RIGHT], "explain_check": ["ถูกแล้ว"]}
    )
    send_photo(client)

    confirm(client, sent)

    lines = [r for r in caplog.records if r.name == "app.ocr.confirm"]
    assert len(lines) == 1
    message = lines[0].getMessage()
    assert json.loads(message) == {
        "session_id": SESSION_ID,
        "line_count": 3,
        "edited_lines": edited,
    }
    assert "49" not in message


def test_AM02_confirm_twice_has_no_pending_ocr(client, room):
    # AC-15
    room(
        {
            "extract_answer": [TWO_LINES],
            "check_answer": [CLASSIFY_RIGHT],
            "explain_check": ["ถูกแล้ว"],
        }
    )
    send_photo(client)
    confirm(client, RIGHT)

    again = confirm(client, RIGHT)

    assert again.status_code == 409
    assert error_code(again) == "no_pending_ocr"


def test_AM02_confirm_without_preview_has_no_pending_ocr(client, room):
    # AC-16: never sent a photo, or the preview belongs to another session.
    room({"extract_answer": [TWO_LINES]})

    never = confirm(client, RIGHT)
    send_photo(client)
    other = confirm(client, RIGHT, session_id=OTHER_SESSION_ID)

    assert never.status_code == 409
    assert error_code(never) == "no_pending_ocr"
    assert other.status_code == 409
    assert error_code(other) == "no_pending_ocr"


def test_AM04_checker_bug_keeps_preview(client, room, monkeypatch):
    # AC-17: a non-AI error in the checker (photo_check calls check_answer of
    # app/services/checker.py, spec §2.2 item 4) ends with internal_error and no verdict.
    room(
        {
            "extract_answer": [TWO_LINES],
            "check_answer": [CLASSIFY_RIGHT],
            "explain_check": ["ถูกแล้ว"],
        }
    )
    send_photo(client)
    real_check = photo_check.check_answer

    async def broken(*args: Any, **kwargs: Any) -> Any:
        raise KeyError("bug")

    monkeypatch.setattr(photo_check, "check_answer", broken)
    failed = parse_sse(confirm(client, RIGHT).text)
    monkeypatch.setattr(photo_check, "check_answer", real_check)
    retried = parse_sse(confirm(client, RIGHT).text)

    assert names(failed) == ["error"]
    assert failed[0][1]["code"] == "internal_error"
    assert retried[0][0] == "verdict"


@pytest.mark.parametrize(
    ("lines", "classifier", "expected"),
    [
        pytest.param(
            WRONG,
            CLASSIFY_SIGN,
            [
                "verdict: incorrect",
                "first_wrong_line: 2",
                "error_type: sign",
                "evidence: บรรทัด 2: +7 กลายเป็น -7",
                "method: doc",
            ],
            id="AC-18 incorrect",
        ),
        pytest.param(
            RIGHT,
            CLASSIFY_RIGHT,
            ["verdict: correct", "first_wrong_line: none", "error_type: none", "method: doc"],
            id="AC-18b correct",
        ),
    ],
)
def test_AM07_explain_check_gets_check_result(client, room, lines, classifier, expected):
    # AC-18, AC-18b: the tutor explains from the check result, the reference and the sheet.
    fake, _ = room(
        {
            "extract_answer": [TWO_LINES],
            "check_answer": [classifier],
            "explain_check": [["อธิบาย", "ต่อ"]],
        }
    )
    send_photo(client)

    events = parse_sse(confirm(client, lines).text)

    assert names(events) == ["verdict", "token", "token", "done"]
    assert tokens(events) == ["อธิบาย", "ต่อ"]
    assert all(data["speaker"] == "tutor" for name, data in events if name == "token")
    [request] = requests_for(fake, "explain_check")
    for fact in expected:
        assert fact in request.prompt
    assert P1_TEXT in request.prompt
    assert P1_REFERENCE in request.prompt  # sent on purpose (spec §2.2 item 6)
    assert f"1. {lines[0]}" in request.prompt
    assert f"2. {lines[1]}" in request.prompt


def test_AM07_explain_check_prompt_and_route():
    # AC-18c: a streamed purpose on the main tier, routed like tutor_reply, with a v1 prompt.
    purposes = get_settings().ai.purposes
    explain, tutor = purposes["explain_check"], purposes["tutor_reply"]
    assert explain.stream is True
    assert (get_settings().env.prompts_dir / "explain_check" / f"{explain.prompt}.md").exists()
    same = ("tier", "temperature", "max_tokens", "timeout_s", "thinking")
    assert {k: getattr(explain, k) for k in same} == {k: getattr(tutor, k) for k in same}

    prompt = Path(get_settings().env.prompts_dir / "explain_check" / "v1.md").read_text("utf-8")
    front = prompt.split("---")[1]
    assert "purpose: explain_check" in front
    assert "version: 1" in front
    for name in ("problem", "reference_answer", "solution_steps", "answer_lines", "check_result"):
        assert name in front


def test_AM07_tutor_failure_after_verdict(client, room):
    # AC-19: the verdict already sent stays; the tutor part degrades like tutor_reply.
    room(
        {
            "extract_answer": [TWO_LINES, TWO_LINES],
            "check_answer": [CLASSIFY_RIGHT, CLASSIFY_RIGHT],
            "explain_check": [RuntimeError("down"), ["ถูก", RuntimeError("cut")]],
        }
    )
    send_photo(client)
    before_first = parse_sse(confirm(client, RIGHT).text)
    send_photo(client)
    after_first = parse_sse(confirm(client, RIGHT).text)

    assert before_first == [
        ("verdict", {"verdict": "correct", "first_wrong_line": None, "error_type": None}),
        ("token", {"speaker": "tutor", "text": DEGRADE}),
        ("done", {}),
    ]
    assert names(after_first) == ["verdict", "token", "error"]
    assert after_first[-1][1]["code"] == "ai_unavailable"


def test_AM06_classifier_failure_keeps_preview(client, room, caplog):
    # AC-E4 (temporary, spec §10 item 2): no verdict, no explanation, no log; confirm again.
    caplog.set_level(logging.INFO, logger="app.ocr.confirm")
    fake, _ = room(
        {
            "extract_answer": [TWO_LINES],
            "check_answer": [RuntimeError("down"), CLASSIFY_SIGN],
            "explain_check": ["บรรทัด 2"],
        }
    )
    send_photo(client)

    failed = parse_sse(confirm(client, WRONG).text)
    no_log = [r for r in caplog.records if r.name == "app.ocr.confirm"]
    retried = parse_sse(confirm(client, WRONG).text)

    assert failed == [("token", {"speaker": "tutor", "text": DEGRADE}), ("done", {})]
    assert no_log == []
    assert len(requests_for(fake, "explain_check")) == 1  # only for the retry
    assert retried[0] == (
        "verdict",
        {"verdict": "incorrect", "first_wrong_line": 2, "error_type": "sign"},
    )


# --- from §10 item 4 (proposal used for now) -------------------------------------------


def test_AM02_problem_stays_pending_after_check(client, room):
    # §10 item 4: with no planner yet, p1 stays the pending problem after it is checked,
    # so the demo can send another photo for it.
    fake, _ = room(
        {
            "extract_answer": [TWO_LINES, TWO_LINES],
            "check_answer": [CLASSIFY_RIGHT],
            "explain_check": ["ถูกแล้ว"],
        }
    )
    send_photo(client)
    confirm(client, RIGHT)

    events = parse_sse(send_photo(client).text)

    assert "ocr_preview" in names(events)
    assert P1_TEXT in requests_for(fake, "extract_answer")[1].prompt


# --- added after /code-review (8 Nov) · not in spec §8 -----------------------------------


def test_SA06_another_tenant_cannot_use_or_replace_a_preview(client, room):
    # The room state is keyed by tenant and session: a session id alone does not say who owns
    # it until tutor_sessions exists.
    from uuid import UUID

    from app.auth import AuthContext, get_auth

    tenant_a, tenant_b = UUID(int=0xA), UUID(int=0xB)
    photo_a = f"{tenant_a}/sessions/{SESSION_ID}/a.jpeg"
    photo_b = f"{tenant_b}/sessions/{SESSION_ID}/b.jpeg"
    three = extract(("x^2 - 49", 0.9), ("= (x-7)(x+7)", 0.9), ("= (x+7)(x-7)", 0.9))
    room(
        {
            "extract_answer": [TWO_LINES, three],
            "check_answer": [CLASSIFY_RIGHT],
            "explain_check": ["ถูกแล้ว"],
        },
        files={photo_a: IMAGE, photo_b: IMAGE},
    )
    current: dict[str, AuthContext] = {}
    app.dependency_overrides[get_auth] = lambda: current["auth"]
    try:
        url = f"/sessions/{SESSION_ID}"
        current["auth"] = AuthContext(tenant_id=tenant_a, user_id=UUID(int=1), token="a")
        client.post(f"{url}/messages", json={"image_path": photo_a})

        current["auth"] = AuthContext(tenant_id=tenant_b, user_id=UUID(int=2), token="b")
        b_confirms_a = confirm(client, RIGHT)
        client.post(f"{url}/messages", json={"image_path": photo_b})

        current["auth"] = AuthContext(tenant_id=tenant_a, user_id=UUID(int=1), token="a")
        a_confirms = confirm(client, RIGHT)
    finally:
        app.dependency_overrides.pop(get_auth, None)

    assert b_confirms_a.status_code == 409
    assert error_code(b_confirms_a) == "no_pending_ocr"
    assert a_confirms.status_code == 200  # B's photo did not replace A's 2-line preview
    assert names(parse_sse(a_confirms.text))[0] == "verdict"


def test_AM02_blank_lines_are_left_out_of_the_preview(client, room, caplog):
    # A blank line cannot be confirmed (the confirm body refuses it), and whitespace alone is
    # not an edit (AM-03).
    caplog.set_level(logging.INFO, logger="app.ocr.confirm")
    spaced = extract((RIGHT[0], 0.9), ("  ", 0.5), (RIGHT[1] + " ", 0.9))
    room(
        {
            "extract_answer": [spaced, extract(("", 0.5))],
            "check_answer": [CLASSIFY_RIGHT],
            "explain_check": ["ถูกแล้ว"],
        }
    )

    first = parse_sse(send_photo(client).text)
    confirmed = confirm(client, RIGHT)
    only_blank = parse_sse(send_photo(client).text)

    assert dict(first)["ocr_preview"]["lines"] == [
        {"latex": RIGHT[0], "confidence": 0.9},
        {"latex": RIGHT[1], "confidence": 0.9},
    ]
    assert confirmed.status_code == 200
    [line] = [r for r in caplog.records if r.name == "app.ocr.confirm"]
    assert json.loads(line.getMessage())["edited_lines"] == []
    assert tokens(only_blank) == [LOOKING, UNREADABLE]


async def test_AM02_a_preview_is_taken_once_and_a_newer_one_wins():
    # One confirm per preview even when two arrive together; a preview put back after a failed
    # check never replaces a newer photo.
    from app.services.room_state import STUB_PROBLEM, PendingPreview

    state = InMemoryRoomState()
    old = PendingPreview(pending=STUB_PROBLEM, lines=("a",))
    new = PendingPreview(pending=STUB_PROBLEM, lines=("b",))
    await state.set_preview("t/s", old)

    assert await state.take_preview("t/s") == old
    assert await state.take_preview("t/s") is None
    await state.set_preview("t/s", new)
    await state.restore_preview("t/s", old)
    assert await state.take_preview("t/s") == new
    await state.restore_preview("t/s", old)
    assert await state.take_preview("t/s") == old
