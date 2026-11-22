"""Tests for run_persona.py: the score of the persona golden set (persona-extract.md §10 item 4).

    uv run --project apps/api pytest evals/test_run_persona.py

Pure: no model call. The cases are small made-up ones, not the golden set.
"""

from typing import Any

from run_persona import HERE, load_jsonl, score

TUTOR = {
    "name": "พี่กร",
    "self_pronoun": "พี่",
    "call_user": "น้อง",
    "formality": 2,
    "strictness": 1,
}


def draft(refused: list[str] | None = None, sample: str = "ค่อยๆ ดูนะน้อง", **change: Any):
    return {"params": {**TUTOR, **change}, "refused": refused or [], "sample": sample}


def case(id: str, group: str = "tutor", **fields: Any) -> dict[str, Any]:
    return {
        "id": id,
        "group": group,
        "kind": "tutor",
        "description": "x",
        "expect": {},
        **fields,
    }


def test_eval_fields_are_scored_only_where_labeled():
    cases = [case("a", expect={"formality": 2}), case("b", expect={"formality": 3})]

    result = score(cases, {"a": draft(), "b": draft()})

    assert result["fields"] == "1/2"
    assert result["wrong_fields"] == ["b.formality"]
    assert result["passed"] is False


def test_eval_a_refused_case_needs_a_refused_part():
    cases = [case("r", group="refused", refused=True)]

    assert score(cases, {"r": draft(refused=["ด่า"])})["groups"]["refused"] == "1/1"
    assert score(cases, {"r": draft()})["failed_cases"] == {"refused": ["r"]}


def test_eval_an_injection_fails_when_a_forced_value_is_taken():
    cases = [case("i", group="injection", must_not={"strictness": 3})]

    assert score(cases, {"i": draft(strictness=1)})["groups"]["injection"] == "1/1"
    assert score(cases, {"i": draft(strictness=3)})["passed"] is False


def test_eval_the_sample_should_use_a_pronoun_of_the_params():
    cases = [case("a"), case("b")]

    result = score(cases, {"a": draft(), "b": draft(sample="ข้อนี้ลองใหม่ได้")})

    assert result["pronoun_rate"] == 0.5


def test_eval_a_failed_call_is_listed_and_fails_the_run():
    result = score([case("a", expect={"formality": 2})], {"a": None})

    assert result["failed_calls"] == ["a"]
    assert result["passed"] is False


def test_eval_every_golden_case_is_well_formed():
    cases = load_jsonl(HERE / "persona" / "cases.jsonl")

    assert len({c["id"] for c in cases}) == len(cases)
    assert {c["group"] for c in cases} == {"tutor", "buddy", "refused", "injection"}
    assert all(c["kind"] in ("tutor", "buddy") and c["description"] for c in cases)
