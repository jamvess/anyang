"""The room does not make a problem again after the gateway gave up on a 429
(specs/features/ai/gateway-rate-limit-backoff.md §2.3 · AC-9, AC-10).

Same fakes as test_room_problems_api.py. The gateway of the room is the real one with the fake
provider, so a scripted ``ProviderRateLimited`` goes through the gateway's 429 table first;
``no_retry_sleep`` makes its waits instant.
"""

from typing import Any

import pytest

from app.ai.providers.base import ProviderRateLimited
from app.settings import get_settings
from tests.unit import test_room_problems_api as room_problems_api
from tests.unit.test_room_problems_api import (
    NO_PROBLEM,
    OPEN,
    block,
    generated,
    names,
    requests,
    script,
)
from tests.unit.test_tutor_reply_stream_api import parse_sse, tokens

# Fixtures of test_room_problems_api.py / test_room_sessions_api.py.
client = room_problems_api.client
fake = room_problems_api.fake
no_retry_sleep = room_problems_api.no_retry_sleep
problems = room_problems_api.problems
repo = room_problems_api.repo
signed_in = room_problems_api.signed_in

SETTINGS = get_settings()


def rate_limited() -> ProviderRateLimited:
    return ProviderRateLimited("429 RESOURCE_EXHAUSTED")


@pytest.mark.usefixtures("no_retry_sleep")
def test_AM11_a_429_after_the_gateway_table_stops_making_problems(signed_in, problems, fake):
    # AC-9: one gateway call of generate_problem, so the provider sees the table + 1 tries only.
    # A good problem is scripted after them: if the room tried again, it would get it.
    gateway_tries = len(SETTINGS.ai.gateway.rate_limit_waits_seconds) + 1
    script(
        fake,
        generate_problem=[rate_limited()] * gateway_tries + [generated()],
        open_session=["สวัสดี"],
    )

    events = parse_sse(signed_in.post(OPEN).text)

    assert len(requests(fake, "generate_problem")) == gateway_tries
    assert "problem" not in names(events)
    assert problems.problems == []
    assert tokens(events)[-1] == NO_PROBLEM
    assert block(requests(fake, "open_session")[0], "problem") == "none"
    assert names(events)[-1] == "done"


@pytest.mark.usefixtures("no_retry_sleep")
def test_AM11_other_provider_errors_still_count_as_a_try(signed_in, problems, fake):
    # AC-10: not a 429, so the room makes the problem again (room-problems-db.md AC-6)
    tries = 1 + SETTINGS.learning.checker.max_generate_retries
    failures: list[Any] = [RuntimeError("503")] * (tries - 1)
    script(fake, generate_problem=[*failures, generated()], open_session=["สวัสดี"])

    events = parse_sse(signed_in.post(OPEN).text)

    assert len(requests(fake, "generate_problem")) == tries
    assert "problem" in names(events)
    assert len(problems.problems) == 1
