"""Offline parts of the P9-lite load script (fake provider, no network).
spec: specs/poc/README.md P9-lite · run: uv run --project apps/api pytest poc/P9-lite"""

import json
from types import SimpleNamespace

import load
import make_sheet
import pytest

from app.ai.providers.base import ProviderRateLimited
from app.ai.providers.fake import FakeProvider
from app.settings import get_settings

DAILY = (
    "429 RESOURCE_EXHAUSTED. {'error': {'details': [{'violations': [{'quotaId': "
    "'GenerateRequestsPerDayPerProjectPerModel-FreeTier'}]}]}}"
)
MINUTE = '429 RESOURCE_EXHAUSTED. quotaId: "GenerateRequestsPerMinutePerProjectPerModel-FreeTier"'

PROBLEM = json.dumps(
    {
        "text": r"หาค่า $\lim_{x \to 2} \frac{x^2-4}{x-2}$",
        "text_latex": r"\text{หาค่า } \lim_{x \to 2} \frac{x^{2}-4}{x-2}",
        "expression": r"\lim_{x \to 2}\frac{x^{2}-4}{x-2}",
        "answer_format": "expression",
        "reference_answer": "4",
        "solution_steps": ["= x+2", "= 4"],
        "skill": None,
    },
    ensure_ascii=False,
)
CHECK = json.dumps(
    {
        "error_type": None,
        "evidence": "ok",
        "method": "doc",
        "verdict": "correct",
        "first_wrong_line": None,
        "confidence": 0.9,
    }
)


def _defaults() -> dict:
    return {
        "generate_problem": PROBLEM,
        "typed_answer": json.dumps({"is_answer": True, "lines": ["4"], "give_up": False}),
        "check_answer": CHECK,
        "explain_check": "เก่งมาก",
        "open_session": "สวัสดี",
        "tutor_reply": "ได้เลย",
        "session_summary": json.dumps({"lines": ["วันนี้ตอบถูกหมด"]}, ensure_ascii=False),
        "classify_material": json.dumps(
            {"kind": "sheet", "confidence": 0.9, "other_instructor": False, "reason": "ชีท"},
            ensure_ascii=False,
        ),
    }


@pytest.fixture(scope="module")
def sheet():
    font = make_sheet.DEFAULT_FONT
    if not font.exists():
        pytest.skip(f"no Thai font at {font}")
    out = make_sheet.build(font)
    return out


def _args(**overrides):
    base = dict(
        model="gemini-test",
        sessions=1,
        concurrency=1,
        problems=2,
        chat=1,
        classify=True,
        think=0.0,
        label="t",
    )
    return SimpleNamespace(**{**base, **overrides})


def test_poc_P9lite_data_file_refuses_a_path_outside_data():
    assert load.data_file("student_turns.json").parent == load.DATA
    with pytest.raises(ValueError):
        load.data_file("../../../evals/topics/mth10101/raw/sheet.pdf")


@pytest.mark.parametrize(
    ("message", "quota", "daily"),
    [
        (DAILY, "GenerateRequestsPerDayPerProjectPerModel-FreeTier", True),
        (MINUTE, "GenerateRequestsPerMinutePerProjectPerModel-FreeTier", False),
        ("503 UNAVAILABLE. The model is overloaded.", None, False),
    ],
)
def test_poc_P9lite_quota_id_tells_daily_from_per_minute(message, quota, daily):
    assert load.quota_id(message) == quota
    assert load.is_daily(load.quota_id(message)) is daily


@pytest.mark.asyncio
async def test_poc_P9lite_a_session_runs_the_room_flow_and_counts_every_attempt(sheet):
    fake = FakeProvider({}, defaults=_defaults())

    result = await load.run(_args(), get_settings(), fake)

    summary = result["summary"]
    assert summary["sessions_completed"] == 1
    purposes = [a["purpose"] for a in result["attempts"]]
    assert purposes[0] == "classify_material"
    assert purposes[1:3] == ["generate_problem", "open_session"]
    # problem 2 is answered wrong then right: two typed answers, checks and explanations
    assert purposes.count("typed_answer") == 3
    assert purposes.count("explain_check") == 3
    assert purposes[-2:] == ["tutor_reply", "session_summary"]
    assert summary["requests_per_completed_session"] == len(purposes) - 1  # classify has no session
    assert summary["generate_problem_verified_share"] == 1.0
    assert all(a["status"] == "ok" for a in result["attempts"])


@pytest.mark.asyncio
async def test_poc_P9lite_after_a_daily_429_nothing_more_is_sent(sheet):
    fake = FakeProvider(
        {"generate_problem": [ProviderRateLimited(DAILY, retry_after=40.0)]}, defaults=_defaults()
    )

    result = await load.run(_args(sessions=5, classify=False), get_settings(), fake)

    summary = result["summary"]
    assert summary["daily_quota_id"] == "GenerateRequestsPerDayPerProjectPerModel-FreeTier"
    assert summary["sessions_started"] == 1  # no new session once the quota is gone
    assert summary["sessions_completed"] == 0
    assert len(fake.requests) == 1  # the provider saw only the first request
    statuses = [a["status"] for a in result["attempts"]]
    assert statuses[0] == "429"
    assert set(statuses[1:]) <= {"skipped_daily"}


@pytest.mark.asyncio
async def test_poc_P9lite_a_503_is_recorded_and_the_gateway_retry_is_counted_too(sheet):
    class Overloaded(Exception):
        code = 503

    fake = FakeProvider(
        {"classify_material": [Overloaded("503 UNAVAILABLE")]}, defaults=_defaults()
    )

    result = await load.run(_args(sessions=0), get_settings(), fake)

    classify = [a for a in result["attempts"] if a["purpose"] == "classify_material"]
    assert [a["status"] for a in classify] == ["503", "ok"]
    assert result["summary"]["rate_503"] == 0.5


def test_poc_P9lite_percentile_of_nothing_is_none():
    assert load.percentile([], 0.95) is None
    assert load.percentile([1.0, 2.0, 3.0], 0.5) == 2.0


@pytest.mark.asyncio
async def test_poc_P9lite_think_time_comes_before_each_student_message(sheet):
    fake = FakeProvider({}, defaults=_defaults())
    gateway, _ = load.build_gateway(get_settings(), "gemini-test", fake)
    waits: list[float] = []

    async def sleep(seconds: float) -> None:
        waits.append(seconds)

    outcome = await load.run_session(
        gateway, get_settings(), 0, load.sheet_pages(), load.load_turns(), 2, 1, 30.0, sleep
    )

    assert outcome.completed
    assert waits == [30.0] * 4  # 1 answer, 2 answers (wrong then right), 1 chat line
