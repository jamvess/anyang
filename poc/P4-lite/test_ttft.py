"""Offline parts of the TTFT script (no network). spec: specs/poc/README.md P4-lite · NFR-P1."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from ttft import event_names, percentile

STUB_REPLY = Path(__file__).parents[2] / "apps" / "api" / "app" / "stubs" / "tutor_reply.sse"


def test_NFRP1_poc_event_names_of_the_stub_reply_end_with_done():
    names = list(event_names(STUB_REPLY.read_text(encoding="utf-8").splitlines()))

    assert names[0] == "token"
    assert names[-1] == "done"


def test_NFRP1_poc_event_names_handle_crlf_and_a_last_block_without_blank_line():
    lines = [
        "event: token\r\n",
        'data: {"text": "a"}\r\n',
        "\r\n",
        ": comment\n",
        "event: done\n",
        "data: {}\n",
    ]

    assert list(event_names(lines)) == ["token", "done"]


def test_NFRP1_poc_a_block_with_data_and_no_event_is_message():
    assert list(event_names(["data: x", ""])) == ["message"]


@pytest.mark.parametrize(
    ("p", "expected"),
    [(50, 5), (95, 10), (100, 10), (0, 1), (10, 1), (11, 2)],
)
def test_NFRP1_poc_nearest_rank_percentile(p: float, expected: float):
    assert percentile([float(v) for v in range(10, 0, -1)], p) == expected


def test_NFRP1_poc_percentile_of_nothing_is_an_error():
    with pytest.raises(ValueError):
        percentile([], 50)
