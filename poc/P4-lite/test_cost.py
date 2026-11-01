"""Tests for cost.py, the part that decides the cost numbers in the P4-lite report.

cd apps/api && uv run pytest ../../poc/P4-lite -q
"""

import json

import pytest
from cost import Call, parse_log, summary, usd


def log_line(**row) -> str:
    values = {
        "purpose": "tutor_reply",
        "model": "gemini-3.5-flash",
        "status": "ok",
        "tokens_in": 300,
        "tokens_out": 500,
        "latency_ms": 2000,
    } | row
    return json.dumps({"severity": "INFO", "logger": "app.ai.calls", "message": json.dumps(values)})


def test_NFRP2_parse_keeps_only_ai_call_lines():
    lines = [
        "INFO:     Started server process [1]",
        log_line(),
        json.dumps({"severity": "WARNING", "logger": "app.auth", "message": "x"}),
        "",
        log_line(tokens_out=None),  # a provider that reports no usage
    ]

    calls = parse_log(lines)

    assert [c.tokens_out for c in calls] == [500, 0]


def test_NFRP2_usd_prices_input_and_output_per_million():
    call = Call("tutor_reply", "m", "ok", tokens_in=1_000_000, tokens_out=2_000_000, latency_ms=0)

    assert usd(call, input_usd_per_m=1.5, output_usd_per_m=9.0) == pytest.approx(19.5)


def test_NFRP2_summary_prices_only_successful_tutor_replies_and_the_session():
    calls = parse_log(
        [
            log_line(tokens_in=1000, tokens_out=1000),
            log_line(tokens_in=1000, tokens_out=3000),
            log_line(status="error", tokens_out=9999),  # failed: not a reply the user saw
            log_line(purpose="embed", tokens_in=9999, tokens_out=0),
        ]
    )

    result = summary(
        calls, input_usd_per_m=1.0, output_usd_per_m=10.0, thb_per_usd=30.0,
        messages_per_session=10, target_thb=5.0,
    )  # fmt: skip

    # mean = (1000*1 + 2000*10) / 1e6 = 0.021 USD per message
    assert result["messages"] == 2
    assert result["usd_per_message"]["mean"] == pytest.approx(0.021)
    assert result["thb_per_message"] == pytest.approx(0.63)
    assert result["session"]["thb"] == pytest.approx(6.3)
    assert result["session"]["within_target"] is False


def test_NFRP2_summary_needs_at_least_one_reply():
    with pytest.raises(ValueError):
        summary(parse_log([log_line(status="error")]))
