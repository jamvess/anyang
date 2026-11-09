"""The tutor room demo on a local machine (specs/features/tutor/demo-room.md, AC-1 to AC-11).

Local mode is the ``get_local_mode`` dependency (APP_ENV=local in a real run); the upload
folder is ``get_local_upload_dir``, pointed at tmp_path here. The demo room state is a fresh
``DemoRoomState`` per test. The gateway is a fake provider; SymPy is the real one, so answers
are written to be right or wrong for each problem's reference.
"""

import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.ai.gateway as gateway_module
from app import stubs
from app.ai.gateway import Gateway, get_gateway
from app.ai.providers.fake import FakeProvider
from app.domain.bkt import (
    ReadinessTopic,
    TopicProgress,
    level,
    mastery_eff,
    readiness,
    record_attempt,
    target_difficulty,
)
from app.main import app
from app.models.room import EVENT_MODELS
from app.services.demo_room import DEMO_PROBLEMS, DEMO_TOPICS, DemoRoomState
from app.services.dev_uploads import get_local_mode, get_local_upload_dir
from app.services.room_state import InMemoryRoomState, PendingProblem, get_room_state
from app.settings import get_settings

SESSION_ID = "00000000-0000-4000-8000-000000000002"
TENANT = stubs.tenant_of(None)  # tests run with AUTH_REQUIRED=false
JPEG = b"\xff\xd8 demo handwriting"
NEXT = "ข้อต่อไปนะ"
P1 = DEMO_PROBLEMS[0]


def classify(error_type: str | None, verdict: str | None, line: int | None) -> str:
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
P1_WRONG = ["x^2 - 49", "= (x-7)(x-7)"]


def extract(lines: list[str]) -> str:
    return json.dumps({"lines": [{"latex": x, "confidence": 0.9} for x in lines], "notes": ""})


def right_answer(problem: PendingProblem) -> list[str]:
    """One line equal to the reference: SymPy decides it is right for every demo problem."""
    return [problem.problem.reference_answer]


def make_gateway(fake: FakeProvider) -> Gateway:
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
def clean_overrides() -> Iterator[None]:
    yield
    for dependency in (get_gateway, get_room_state, get_local_mode, get_local_upload_dir):
        app.dependency_overrides.pop(dependency, None)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def local(tmp_path: Path) -> Callable[..., tuple[FakeProvider, DemoRoomState]]:
    """Local mode with the demo state, an upload folder in tmp_path and a scripted provider."""

    def install(script: dict[str, list[Any]]) -> tuple[FakeProvider, DemoRoomState]:
        fake = FakeProvider(script)
        state = DemoRoomState()
        app.dependency_overrides[get_gateway] = lambda: make_gateway(fake)
        app.dependency_overrides[get_room_state] = lambda: state
        app.dependency_overrides[get_local_mode] = lambda: True
        app.dependency_overrides[get_local_upload_dir] = lambda: tmp_path
        return fake, state

    return install


def parse_sse(body: str) -> list[tuple[str, Any]]:
    events = []
    for block in body.replace("\r\n", "\n").split("\n\n"):
        name, data = "message", []
        for line in block.split("\n"):
            if not line or line.startswith(":"):
                continue
            field, _, value = line.partition(":")
            if field == "event":
                name = value.strip()
            elif field == "data":
                data.append(value.removeprefix(" "))
        if data:
            events.append((name, json.loads("\n".join(data))))
    for name, data in events:
        if name in EVENT_MODELS:
            EVENT_MODELS[name].model_validate(data)
    return events


def names(events: list[tuple[str, Any]]) -> list[str]:
    return [n for n, _ in events]


def event(events: list[tuple[str, Any]], name: str) -> Any:
    return next(data for n, data in events if n == name)


def requests_for(fake: FakeProvider, purpose: str) -> list[Any]:
    return [r for r in fake.requests if r.purpose == purpose]


def upload(client: TestClient, data: bytes = JPEG, content_type: str = "image/jpeg") -> str:
    """POST /uploads, then PUT the file to the returned URL; returns the path."""
    ticket = client.post(
        f"/sessions/{SESSION_ID}/uploads",
        json={
            "kind": "image",
            "content_type": content_type,
            "file_name": "a.jpg",
            "size_bytes": len(data),
        },
    ).json()
    put = client.put(ticket["upload_url"], content=data, headers={"Content-Type": content_type})
    assert put.status_code == 200
    return ticket["path"]


def send_photo(client: TestClient) -> list[tuple[str, Any]]:
    path = upload(client)
    return parse_sse(
        client.post(f"/sessions/{SESSION_ID}/messages", json={"image_path": path}).text
    )


def confirm(client: TestClient, lines: list[str]) -> list[tuple[str, Any]]:
    return parse_sse(client.post(f"/sessions/{SESSION_ID}/ocr/confirm", json={"lines": lines}).text)


def expected_card_readiness(progress: dict[str, TopicProgress]) -> float:
    cfg = get_settings().learning
    topics = []
    for topic in DEMO_TOPICS:
        p = progress.get(topic.topic_id, TopicProgress(cfg.bkt.p_init, 0, 0))
        d_target = target_difficulty(topic.stars, "normal", cfg)
        topics.append(
            ReadinessTopic(
                topic.stars,
                topic.signal_r,
                mastery_eff(p.mastery, p.d_max, d_target, cfg),
                p.attempts,
            )
        )
    return readiness(topics, cfg)


# --- A · local uploads ----------------------------------------------------------------


@pytest.mark.parametrize("is_local", [True, False], ids=["local", "not local"])
def test_TM06_upload_ticket_points_at_the_api_only_locally(client, tmp_path, is_local):
    # AC-1
    app.dependency_overrides[get_local_mode] = lambda: is_local
    app.dependency_overrides[get_local_upload_dir] = lambda: tmp_path

    response = client.post(
        f"/sessions/{SESSION_ID}/uploads",
        json={
            "kind": "image",
            "content_type": "image/jpeg",
            "file_name": "a.jpg",
            "size_bytes": 10,
        },
    )

    ticket = response.json()
    if is_local:
        assert "x-stub" not in response.headers
        assert ticket["upload_url"] == f"http://testserver/dev/uploads/{ticket['path']}"
    else:
        assert response.headers.get("x-stub") == "true"
        assert ticket["upload_url"].startswith(stubs.STORAGE_URL)


def test_TM06_uploaded_photo_reaches_extract_answer(client, local, tmp_path):
    # AC-2: the bytes PUT to the upload URL are the bytes the model reads.
    fake, _ = local({"extract_answer": [extract(right_answer(P1))]})

    events = send_photo(client)

    assert "ocr_preview" in names(events)
    [request] = requests_for(fake, "extract_answer")
    assert request.images[0].data == JPEG
    assert request.images[0].mime_type == "image/jpeg"
    assert len(list(tmp_path.rglob("*.jpeg"))) == 1


@pytest.mark.parametrize(
    ("path", "content_type", "size", "status", "code"),
    [
        pytest.param(
            f"{TENANT}/sessions/{SESSION_ID}/sub/a.jpeg",
            "image/jpeg",
            10,
            404,
            "not_found",
            id="extra folder",
        ),
        pytest.param(
            f"{TENANT}/sessions/{SESSION_ID}/..a.jpeg",
            "image/jpeg",
            10,
            404,
            "not_found",
            id="dot name",
        ),
        pytest.param(
            f"{TENANT}/other/{SESSION_ID}/a.jpeg",
            "image/jpeg",
            10,
            404,
            "not_found",
            id="not a session path",
        ),
        pytest.param(
            f"{TENANT}/sessions/{SESSION_ID}/a.txt",
            "text/plain",
            10,
            422,
            "unsupported_type",
            id="not an image",
        ),
        pytest.param(
            f"{TENANT}/sessions/{SESSION_ID}/a.jpeg",
            "image/jpeg",
            None,
            422,
            "file_too_large",
            id="over the limit",
        ),
    ],
)
def test_SA06_dev_upload_refuses_bad_paths_types_and_sizes(
    client, local, path, content_type, size, status, code
):
    # AC-3
    local({})
    limit = get_settings().ai.guards.max_image_mb * 1_048_576
    body = b"\0" * (limit + 1 if size is None else size)

    response = client.put(
        f"/dev/uploads/{path}", content=body, headers={"Content-Type": content_type}
    )

    assert response.status_code == status
    assert response.json()["error"]["code"] == code


def test_SA06_dev_upload_does_not_exist_outside_local(client, tmp_path):
    # AC-3
    app.dependency_overrides[get_local_mode] = lambda: False
    app.dependency_overrides[get_local_upload_dir] = lambda: tmp_path

    response = client.put(
        f"/dev/uploads/{TENANT}/sessions/{SESSION_ID}/a.jpeg",
        content=JPEG,
        headers={"Content-Type": "image/jpeg"},
    )

    assert response.status_code == 404
    assert list(tmp_path.iterdir()) == []


# --- B, D · demo problems and progress card -------------------------------------------


def test_TM04_confirm_ends_with_card_then_next_problem(client, local):
    # AC-4, AC-9 (order): verdict → explanation → progress_card → "next" → problem → done.
    second = DEMO_PROBLEMS[1]
    fake, _ = local(
        {
            "extract_answer": [extract(right_answer(P1)), extract(right_answer(second))],
            "check_answer": [CLASSIFY_RIGHT],
            "explain_check": [["ถูก", "แล้ว"]],
        }
    )
    send_photo(client)

    events = confirm(client, right_answer(P1))
    send_photo(client)

    assert names(events) == [
        "verdict",
        "token",
        "token",
        "progress_card",
        "token",
        "problem",
        "done",
    ]
    assert events[4] == ("token", {"speaker": "tutor", "text": NEXT})
    assert event(events, "problem") == {
        "problem_id": second.problem_id,
        "text_latex": second.text_latex,
        "difficulty": second.difficulty,
        "purpose": "practice",
    }
    assert second.problem.text in requests_for(fake, "extract_answer")[1].prompt


def test_TM04_after_the_last_problem_comes_the_first(client, local):
    # AC-5
    count = len(DEMO_PROBLEMS)
    local(
        {
            "extract_answer": [extract(right_answer(p)) for p in DEMO_PROBLEMS],
            "check_answer": [CLASSIFY_RIGHT] * count,
            "explain_check": ["ถูกแล้ว"] * count,
        }
    )

    shown = []
    for problem in DEMO_PROBLEMS:
        send_photo(client)
        shown.append(event(confirm(client, right_answer(problem)), "problem")["problem_id"])

    assert shown == [p.problem_id for p in DEMO_PROBLEMS[1:]] + [P1.problem_id]


def test_TM04_tutor_failure_keeps_the_same_problem(client, local):
    # AC-6
    fake, _ = local(
        {
            "extract_answer": [extract(right_answer(P1)), extract(right_answer(P1))],
            "check_answer": [CLASSIFY_RIGHT],
            "explain_check": [RuntimeError("down")],
        }
    )
    send_photo(client)

    events = confirm(client, right_answer(P1))
    send_photo(client)

    assert "problem" not in names(events)
    assert P1.problem.text in requests_for(fake, "extract_answer")[1].prompt


def test_TM04_no_next_problem_outside_local(client, tmp_path):
    # AC-7: with no demo state (the default room state) the confirm stream is unchanged.
    fake = FakeProvider(
        {
            "extract_answer": [extract(right_answer(P1))],
            "check_answer": [CLASSIFY_RIGHT],
            "explain_check": ["ถูกแล้ว"],
        }
    )
    state = InMemoryRoomState()
    app.dependency_overrides[get_gateway] = lambda: make_gateway(fake)
    app.dependency_overrides[get_room_state] = lambda: state
    app.dependency_overrides[get_local_mode] = lambda: True  # uploads still work
    app.dependency_overrides[get_local_upload_dir] = lambda: tmp_path
    send_photo(client)

    events = confirm(client, right_answer(P1))

    assert names(events)[0] == "verdict"
    assert "problem" not in names(events)
    assert "progress_card" not in names(events)
    assert names(events)[-1] == "done"


@pytest.mark.parametrize(
    ("correct", "expected_level"), [(True, "developing"), (False, "weak")], ids=["right", "wrong"]
)
def test_PM02_progress_card_comes_from_bkt(client, local, correct, expected_level):
    # AC-9
    cfg = get_settings().learning
    lines = right_answer(P1) if correct else P1_WRONG
    local(
        {
            "extract_answer": [extract(lines)],
            "check_answer": [CLASSIFY_RIGHT if correct else CLASSIFY_SIGN],
            "explain_check": ["อธิบาย"],
        }
    )
    send_photo(client)

    card = event(confirm(client, lines), "progress_card")

    topic = P1.topic_id
    after = record_attempt(TopicProgress(cfg.bkt.p_init, 0, 0), correct, P1.difficulty, True, cfg)
    stars = {t.topic_id: t.stars for t in DEMO_TOPICS}[topic]
    assert level(after, target_difficulty(stars, "normal", cfg), True, cfg) == expected_level
    levels = {row["id"]: row["level"] for row in card["topics"]}
    assert levels[topic] == expected_level
    assert all(lv == "not_started" for tid, lv in levels.items() if tid != topic)
    assert card["total"] == len(DEMO_TOPICS)
    assert card["passed"] == 0
    assert card["readiness"] == pytest.approx(expected_card_readiness({topic: after}))


def test_TM15_opening_card_shows_the_demo_topics_not_started(client, local):
    # AC-10: the rest of the opening stream is the fixture's.
    local({})

    events = parse_sse(
        client.post("/exam-preps/00000000-0000-4000-8000-000000000001/sessions").text
    )

    card = event(events, "progress_card")
    assert [row["id"] for row in card["topics"]] == [t.topic_id for t in DEMO_TOPICS]
    assert all(row["level"] == "not_started" for row in card["topics"])
    assert card["readiness"] == 0
    assert names(events) == [name for name, _ in stubs.events("session_start")]


def test_PM02_failed_check_records_no_attempt(client, local):
    # AC-11: the classifier fails first; only the second, successful confirm counts.
    cfg = get_settings().learning
    local(
        {
            "extract_answer": [extract(right_answer(P1))],
            "check_answer": [RuntimeError("down"), CLASSIFY_RIGHT],
            "explain_check": ["ถูกแล้ว"],
        }
    )
    send_photo(client)
    confirm(client, right_answer(P1))

    card = event(confirm(client, right_answer(P1)), "progress_card")

    once = record_attempt(TopicProgress(cfg.bkt.p_init, 0, 0), True, P1.difficulty, True, cfg)
    assert card["readiness"] == pytest.approx(expected_card_readiness({P1.topic_id: once}))


# --- C · the tutor knows the pending problem -------------------------------------------


def test_AM13_tutor_reply_gets_the_problem_without_its_reference(client):
    # AC-8: everywhere, with the default room state (problem p1).
    fake = FakeProvider({"tutor_reply": ["เริ่มจากดูว่าเป็นผลต่างกำลังสองไหม"]})
    app.dependency_overrides[get_gateway] = lambda: make_gateway(fake)
    app.dependency_overrides[get_room_state] = lambda: InMemoryRoomState()

    response = client.post(f"/sessions/{SESSION_ID}/messages", json={"text": "ข้อนี้เริ่มยังไง"})

    assert response.status_code == 200
    [request] = requests_for(fake, "tutor_reply")
    assert P1.problem.text in request.prompt
    assert P1.problem.reference_answer not in request.prompt
    assert "ข้อนี้เริ่มยังไง" in request.prompt
    assert get_settings().ai.purposes["tutor_reply"].prompt == "v2"
