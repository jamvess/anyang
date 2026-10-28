"""Tests for run_checker.py: run the checker over golden-set answers and write predictions.

    uv run --project apps/api pytest evals/test_run_checker.py

Spec: specs/features/check/check-answer-classifier.md §2.6 (AC-9, AC-21, AC-22). Uses the fake
provider (AI-03) and an in-process SymPy pool, so nothing touches the network.
"""

import json

import pytest
from app.ai.gateway import Gateway
from app.ai.providers.fake import FakeProvider
from app.settings import get_settings
from run_checker import run
from run_eval import score

# evals/ has no pytest config of its own (apps/api's asyncio_mode = "auto" does not apply here).
pytestmark = pytest.mark.asyncio

ROWS = [
    {
        "id": "ans_001",
        "problem": "\\text{แยกตัวประกอบ } x^{3}-x",
        "answer_format": "factored",
        "reference": "x(x-1)(x+1)",
        "lines": ["x^{3}-x", "=x(x^{2}-1)"],
        "verdict": "incomplete",
        "error_type": "concept",
        "first_wrong_line": None,
        "method": "doc",
    },
    {
        "id": "ans_003",
        "problem": "\\lim_{x \\to \\infty} \\frac{3x^{2}-x}{2x^{2}+5}",
        "answer_format": "expression",
        "reference": "\\frac{3}{2}",
        "lines": [
            "\\lim_{x \\to \\infty} \\frac{3x^{2}-x}{2x^{2}+5}",
            "=\\lim_{x \\to \\infty} \\frac{3-\\frac{1}{x}}{2+\\frac{5}{x^{2}}}",
            "=\\frac{3-0}{2+0}",
            "=\\frac{3}{2}",
        ],
        "verdict": "correct",
        "error_type": None,
        "first_wrong_line": None,
        "method": "doc",
    },
]

LLM_OK = json.dumps(
    {
        "error_type": "concept",
        "evidence": "",
        "method": "doc",
        "verdict": None,
        "first_wrong_line": None,
        "confidence": 0.9,
    }
)


class FakePool:
    async def run(self, fn, *args, timeout_s: float):
        return fn(*args)


def gateway(responses: list[str]) -> Gateway:
    settings = get_settings()
    return Gateway(
        settings.ai, settings.env.prompts_dir, FakeProvider({"check_answer": responses})
    )


async def test_AM06_writes_one_prediction_per_answer(tmp_path) -> None:
    # AC-21, AC-22 (fake provider: no network)
    out = tmp_path / "v1.jsonl"

    skipped = await run(
        ROWS, out_path=out, gateway=gateway([LLM_OK, LLM_OK]), pool=FakePool()
    )

    predictions = [
        json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()
    ]
    assert skipped == []
    assert [p["id"] for p in predictions] == ["ans_001", "ans_003"]
    for p in predictions:
        assert {
            "id",
            "verdict",
            "error_type",
            "first_wrong_line",
            "decided_by",
        } <= p.keys()
    assert predictions[0]["verdict"] == "incomplete"
    assert predictions[1]["verdict"] == "correct"
    assert score(ROWS, predictions)["verdict"]["matched"] == 2


async def test_AI05_answer_the_gateway_gives_up_on_is_skipped(tmp_path) -> None:
    # AC-9 (§10 decision 2): no prediction is written for it; its id is returned.
    out = tmp_path / "v1.jsonl"
    attempts = get_settings().ai.gateway.schema_retries + 1
    responses = ["not json"] * attempts + [LLM_OK]

    skipped = await run(ROWS, out_path=out, gateway=gateway(responses), pool=FakePool())

    predictions = [
        json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()
    ]
    assert skipped == ["ans_001"]
    assert [p["id"] for p in predictions] == ["ans_003"]
