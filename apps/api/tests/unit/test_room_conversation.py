"""Which saved messages reach tutor_reply as the conversation
(specs/features/tutor/room-sessions-db.md §2.7 item 3 · AC-boundary-turns).

`app.domain.room.recent_turns` groups saved (role, text) lines into turns: a turn starts at each
user message, and tutor lines before the first user message (the greeting) are a turn of their
own, as in demo-room.md §2 E. N comes from config/learning.yaml → session.context_recent_turns.
"""

import pytest

from app.domain.room import recent_turns
from app.settings import get_settings

N = get_settings().learning.session.context_recent_turns


def history(turns: int) -> list[tuple[str, str]]:
    """A greeting, then `turns - 1` exchanges: `turns` turns in all."""
    lines = [("tutor", "greeting")]
    for i in range(1, turns):
        lines += [("user", f"q{i}"), ("tutor", f"a{i}")]
    return lines


@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_TM13_keeps_the_last_n_turns(delta: int) -> None:
    lines = history(N + delta)

    kept = recent_turns(lines, N)

    if delta <= 0:
        assert kept == lines  # N - 1 or N turns: all of them
    else:
        assert kept == lines[1:]  # N + 1 turns: the oldest (the greeting) drops
        assert kept[0] == ("user", "q1")


def test_TM13_several_tutor_lines_stay_in_one_turn() -> None:
    lines = [("user", "q1"), ("tutor", "a1"), ("tutor", "a1b"), ("user", "q2"), ("tutor", "a2")]

    assert recent_turns(lines, 1) == [("user", "q2"), ("tutor", "a2")]
    assert recent_turns(lines, 2) == lines


def test_TM13_no_messages_is_no_conversation() -> None:
    assert recent_turns([], N) == []


def test_TM13_a_user_message_without_a_reply_is_a_turn() -> None:
    """A message whose reply failed (AC-17) still counts as a turn."""
    lines = [("user", "q1"), ("user", "q2"), ("tutor", "a2")]

    assert recent_turns(lines, 1) == [("user", "q2"), ("tutor", "a2")]
    assert recent_turns(lines, 2) == lines
