"""Pydantic output models of the AI calls in flow 2.3 (A2, A4, A5, A6, A7) and extract_answer.

prompts/README.md rule 4: the JSON schema in each prompt must match its Pydantic model. The
models also check what the prompt rules promise (page ranges, ids, references), so a wrong
answer goes back to the model through the gateway's schema retry (AI-05).
"""

import json

import pytest
from pydantic import BaseModel, ValidationError

from app.models.scope_ai import (
    ExtractAnswerResult,
    ExtractTopicsLocalResult,
    MapQuestionsResult,
    MergeTopicsResult,
    SplitPastExamResult,
    VisionExtractResult,
)
from app.settings import get_settings

PROMPTS = get_settings().env.prompts_dir

MODELS: dict[str, type[BaseModel]] = {
    "vision_extract": VisionExtractResult,
    "split_past_exam": SplitPastExamResult,
    "extract_topics_local": ExtractTopicsLocalResult,
    "merge_topics": MergeTopicsResult,
    "map_questions": MapQuestionsResult,
    "extract_answer": ExtractAnswerResult,
}


def prompt_schema(purpose: str) -> dict:
    """The JSON example on the last line of prompts/<purpose>/v1.md."""
    text = (PROMPTS / purpose / "v1.md").read_text(encoding="utf-8")
    last_json_line = [line for line in text.splitlines() if line.startswith("{")][-1]
    return json.loads(last_json_line)


def keys_of(value) -> object:
    """Shape of a JSON value: nested keys only (first item of each list)."""
    if isinstance(value, dict):
        return {k: keys_of(v) for k, v in value.items()}
    if isinstance(value, list) and value:
        return [keys_of(value[0])]
    return None


def keys_of_model(model: type[BaseModel]) -> object:
    shape = {}
    for name, field in model.model_fields.items():
        annotation = field.annotation
        inner = getattr(annotation, "__args__", (None,))[0]
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            shape[name] = keys_of_model(annotation)
        elif isinstance(inner, type) and issubclass(inner, BaseModel):
            shape[name] = [keys_of_model(inner)]
        else:
            shape[name] = None
    return shape


def list_shape(value) -> object:
    """Treat lists of scalars like scalars, so ["string"] and list[str] compare equal."""
    if isinstance(value, dict):
        return {k: list_shape(v) for k, v in value.items()}
    if isinstance(value, list):
        return [list_shape(value[0])] if value and isinstance(value[0], dict) else None
    return value


@pytest.mark.parametrize("purpose", sorted(MODELS))
def test_AI05_prompt_schema_matches_pydantic_model(purpose: str):
    assert list_shape(keys_of(prompt_schema(purpose))) == list_shape(keys_of_model(MODELS[purpose]))


# --- A2 vision_extract -----------------------------------------------------------------------


def test_SM01_vision_extract_accepts_blank_page():
    result = VisionExtractResult.model_validate({"text": "", "latex_blocks": [], "notes": ""})
    assert result.text == ""


# --- A4 split_past_exam ----------------------------------------------------------------------


def test_SM01_split_past_exam_accepts_questions_with_and_without_points():
    result = SplitPastExamResult.model_validate(
        {
            "questions": [
                {"q_no": "ก1.1", "text": "จงหา $\\lim_{x \\to 0} x$", "page": 2, "points": 5},
                {"q_no": "ข3", "text": "จงหา $f'(x)$", "page": 4, "points": None},
            ],
            "notes": "",
        }
    )
    assert [q.q_no for q in result.questions] == ["ก1.1", "ข3"]


@pytest.mark.parametrize("q_no", ["", "ข้อ 1", "1.1.1.1"])
def test_SM01_split_past_exam_rejects_bad_question_numbers(q_no: str):
    with pytest.raises(ValidationError):
        SplitPastExamResult.model_validate(
            {"questions": [{"q_no": q_no, "text": "x", "page": 1, "points": None}], "notes": ""}
        )


def test_SM01_split_past_exam_rejects_duplicate_question_numbers():
    question = {"q_no": "ก1", "text": "x", "page": 1, "points": None}
    with pytest.raises(ValidationError, match="duplicate"):
        SplitPastExamResult.model_validate({"questions": [question, question], "notes": ""})


# --- A5 extract_topics_local -----------------------------------------------------------------


def local(pages: list[str], prereq_hint: list[str] | None = None) -> dict:
    topic = {"name": "ลิมิต (Limit)", "pages": pages, "prereq_hint": prereq_hint or []}
    return {"topics": [topic], "notes": ""}


def test_SM04_local_topic_pages_are_start_end_ranges():
    result = ExtractTopicsLocalResult.model_validate(local(["2-6", "9-9"]))
    assert result.topics[0].pages == ["2-6", "9-9"]


@pytest.mark.parametrize("pages", [[], ["7"], ["p.2-6"], ["6-2"]])
def test_SM04_local_topic_rejects_bad_page_ranges(pages: list[str]):
    with pytest.raises(ValidationError):
        ExtractTopicsLocalResult.model_validate(local(pages))


def test_SM02_local_topic_has_at_most_three_prereq_hints():
    with pytest.raises(ValidationError):
        ExtractTopicsLocalResult.model_validate(local(["1-2"], ["a", "b", "c", "d"]))


def test_SM01_local_topics_may_be_empty_with_a_note():
    result = ExtractTopicsLocalResult.model_validate({"topics": [], "notes": "scanned junk"})
    assert result.notes == "scanned junk"


# --- A6 merge_topics -------------------------------------------------------------------------


def merged(topic_id: str, order: int, prereqs: list[str], skill_id: str | None = None) -> dict:
    return {
        "id": topic_id,
        "name": f"หัวข้อ {topic_id}",
        "order": order,
        "sources": ["sheet-01:2-6"],
        "prereqs": prereqs,
        "excluded_by_note": False,
        "skills": [
            {
                "id": skill_id or f"{topic_id}.s1",
                "name": "หาลิมิตโดยแทนค่า",
                "common_mistakes": [{"text": "ลืมเช็คตัวส่วน", "error_type": "concept"}],
            }
        ],
    }


def test_SM02_merge_topics_accepts_prerequisites_in_order():
    result = MergeTopicsResult.model_validate(
        {"topics": [merged("t01", 1, []), merged("t02", 2, ["t01"])], "notes": ""}
    )
    assert result.topics[1].prereqs == ["t01"]


def test_SM02_merge_topics_rejects_unknown_prerequisite():
    with pytest.raises(ValidationError, match="t09"):
        MergeTopicsResult.model_validate({"topics": [merged("t01", 1, ["t09"])], "notes": ""})


def test_SM02_merge_topics_rejects_prerequisite_cycle():
    with pytest.raises(ValidationError, match="cycle"):
        MergeTopicsResult.model_validate(
            {"topics": [merged("t01", 1, ["t02"]), merged("t02", 2, ["t01"])], "notes": ""}
        )


def test_SM02_merge_topics_rejects_prerequisite_ordered_after_its_topic():
    with pytest.raises(ValidationError, match="order"):
        MergeTopicsResult.model_validate(
            {"topics": [merged("t01", 1, ["t02"]), merged("t02", 2, [])], "notes": ""}
        )


def test_SM02_merge_topics_rejects_duplicate_ids():
    with pytest.raises(ValidationError, match="duplicate"):
        MergeTopicsResult.model_validate(
            {"topics": [merged("t01", 1, []), merged("t01", 2, [])], "notes": ""}
        )


def test_SM01_merge_topics_skill_id_belongs_to_its_topic():
    with pytest.raises(ValidationError, match=r"t02.s1"):
        MergeTopicsResult.model_validate(
            {"topics": [merged("t01", 1, [], skill_id="t02.s1")], "notes": ""}
        )


@pytest.mark.parametrize("source", ["sheet-01", "sheet-01:2", "2-6"])
def test_SM04_merge_topics_sources_name_file_and_page_range(source: str):
    topic = merged("t01", 1, []) | {"sources": [source]}
    with pytest.raises(ValidationError):
        MergeTopicsResult.model_validate({"topics": [topic], "notes": ""})


def test_SM01_merge_topics_rejects_unknown_error_type():
    topic = merged("t01", 1, [])
    topic["skills"][0]["common_mistakes"][0]["error_type"] = "no_answer"
    with pytest.raises(ValidationError):
        MergeTopicsResult.model_validate({"topics": [topic], "notes": ""})


# --- A7 map_questions ------------------------------------------------------------------------


def mapping(topic_id: str | None, skill_id: str | None) -> dict:
    return {
        "mappings": [
            {
                "q_id": "midterm-2559-1:ก1.1",
                "topic_id": topic_id,
                "skill_id": skill_id,
                "trap": None,
                "note": "",
            }
        ]
    }


def test_SM03_map_questions_accepts_topic_and_skill():
    result = MapQuestionsResult.model_validate(mapping("t03", "t03.s1"))
    assert result.mappings[0].skill_id == "t03.s1"


def test_SM03_map_questions_accepts_unmapped_question():
    result = MapQuestionsResult.model_validate(mapping(None, None))
    assert result.mappings[0].topic_id is None


@pytest.mark.parametrize(
    ("topic_id", "skill_id"), [("t03", None), (None, "t03.s1"), ("t03", "t04.s1")]
)
def test_SM03_map_questions_skill_must_belong_to_topic(topic_id, skill_id):
    with pytest.raises(ValidationError):
        MapQuestionsResult.model_validate(mapping(topic_id, skill_id))


# --- extract_answer (P1) ---------------------------------------------------------------------


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_AM01_extract_answer_confidence_is_between_0_and_1(confidence: float):
    with pytest.raises(ValidationError):
        ExtractAnswerResult.model_validate(
            {"lines": [{"latex": "x^{2}", "confidence": confidence}], "notes": ""}
        )


def test_AM01_extract_answer_accepts_empty_photo():
    assert ExtractAnswerResult.model_validate({"lines": [], "notes": "blank"}).lines == []
