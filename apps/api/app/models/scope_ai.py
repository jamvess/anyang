"""Structured outputs of the AI calls in flow 2.3 (ai-orchestration.md §2.3.7) and of
extract_answer (§2.4). Each model mirrors the JSON schema at the end of its prompt in
prompts/<purpose>/v1.md (prompts/README.md rule 4) and enforces the prompt's rules, so a
violation goes back to the model through the gateway's schema retry (AI-05).

The numeric limits here repeat what the prompts promise (for example "at most 3 prereq_hint");
they are output-format rules, not learning-model thresholds, so they do not live in
config/learning.yaml.
"""

import re
from typing import Annotated, Literal, Self

from pydantic import AfterValidator, BaseModel, Field, model_validator

from app.ai.latex import LatexStr, MathTextStr

# prompts/extract_topics_local/v1.md rule 8 · prompts/merge_topics/v1.md rule 6
MAX_PREREQS = 3

ErrorType = Literal["calculation", "sign", "wrong_method", "concept", "prerequisite"]

_PAGE_RANGE = re.compile(r"^(\d+)-(\d+)$")
_SOURCE = re.compile(r"^(.+):(\d+)-(\d+)$")
_Q_NO = re.compile(r"^[ก-ฮ]?\d+(\.\d+)?$")  # ก1.2, ข3, 3.2 (prompts/split_past_exam rule 2)
_TOPIC_ID = r"^t\d{2,}$"


def _check_range(start: str, end: str, value: str) -> None:
    if not 1 <= int(start) <= int(end):
        raise ValueError(f"page range {value!r} must be start-end with 1 <= start <= end")


def _page_range(value: str) -> str:
    match = _PAGE_RANGE.match(value)
    if not match:
        raise ValueError(f"page range {value!r} must look like '2-6' (a single page is '7-7')")
    _check_range(*match.groups(), value)
    return value


def _source(value: str) -> str:
    match = _SOURCE.match(value)
    if not match:
        raise ValueError(f"source {value!r} must look like 'sheet-01:2-6'")
    _check_range(match.group(2), match.group(3), value)
    return value


def _q_no(value: str) -> str:
    if not _Q_NO.match(value):
        raise ValueError(f"q_no {value!r} must look like 'ก1.2', 'ข3' or '3.2'")
    return value


PageRange = Annotated[str, AfterValidator(_page_range)]
Source = Annotated[str, AfterValidator(_source)]
QuestionNo = Annotated[str, AfterValidator(_q_no)]


# --- A2 vision_extract -------------------------------------------------------------------


class VisionExtractResult(BaseModel):
    text: MathTextStr
    latex_blocks: list[LatexStr]
    notes: str = ""


class PageText(BaseModel):
    page: int = Field(ge=1)
    text: MathTextStr


class VisionExtractPagesResult(BaseModel):
    """vision_extract_pages: every page of a scanned file in one call (PoC P3)."""

    pages: list[PageText]
    notes: str = ""

    @model_validator(mode="after")
    def _pages_numbered_1_to_n(self) -> Self:
        numbers = [p.page for p in self.pages]
        if numbers != list(range(1, len(numbers) + 1)):
            raise ValueError(f"pages must be numbered 1..n in order, got {numbers}")
        return self


# --- A4 split_past_exam ------------------------------------------------------------------


class PastExamQuestion(BaseModel):
    q_no: QuestionNo
    text: MathTextStr = Field(min_length=1)
    page: int = Field(ge=1)
    points: float | None


class SplitPastExamResult(BaseModel):
    questions: list[PastExamQuestion]
    notes: str = ""

    @model_validator(mode="after")
    def _unique_q_no(self) -> Self:
        numbers = [q.q_no for q in self.questions]
        if duplicates := sorted({n for n in numbers if numbers.count(n) > 1}):
            raise ValueError(f"duplicate q_no: {duplicates}")
        return self


# --- A5 extract_topics_local -------------------------------------------------------------


class LocalTopic(BaseModel):
    name: str = Field(min_length=1)
    pages: list[PageRange] = Field(min_length=1)
    prereq_hint: list[str] = Field(max_length=MAX_PREREQS)


class ExtractTopicsLocalResult(BaseModel):
    topics: list[LocalTopic]
    notes: str = ""


# --- A6 merge_topics ---------------------------------------------------------------------


class CommonMistake(BaseModel):
    text: str = Field(min_length=1)
    error_type: ErrorType


class MergedSkill(BaseModel):
    id: str = Field(pattern=r"^t\d{2,}\.s\d+$")
    name: str = Field(min_length=1)
    common_mistakes: list[CommonMistake]


class MergedTopic(BaseModel):
    id: str = Field(pattern=_TOPIC_ID)
    name: str = Field(min_length=1)
    order: int = Field(ge=1)
    sources: list[Source] = Field(min_length=1)
    prereqs: list[str]
    excluded_by_note: bool = False
    skills: list[MergedSkill] = Field(min_length=1)

    @model_validator(mode="after")
    def _skills_belong_to_topic(self) -> Self:
        foreign = [s.id for s in self.skills if not s.id.startswith(f"{self.id}.")]
        if foreign:
            raise ValueError(f"topic {self.id} has skills of another topic: {foreign}")
        return self


class MergeTopicsResult(BaseModel):
    topics: list[MergedTopic]
    notes: str = ""

    @model_validator(mode="after")
    def _valid_prerequisite_graph(self) -> Self:
        ids = [t.id for t in self.topics]
        if duplicates := sorted({i for i in ids if ids.count(i) > 1}):
            raise ValueError(f"duplicate topic ids: {duplicates}")
        by_id = {t.id: t for t in self.topics}
        for topic in self.topics:
            if unknown := [p for p in topic.prereqs if p not in by_id]:
                raise ValueError(f"topic {topic.id} has unknown prereqs: {unknown}")
        if cycle := _find_cycle({t.id: t.prereqs for t in self.topics}):
            raise ValueError(f"prerequisite cycle: {' -> '.join(cycle)}")
        for topic in self.topics:
            if late := [p for p in topic.prereqs if by_id[p].order >= topic.order]:
                raise ValueError(f"topic {topic.id} must come after its prereqs in order: {late}")
        return self


def _find_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    visiting: list[str] = []
    done: set[str] = set()

    def visit(node: str) -> list[str] | None:
        if node in visiting:
            return [*visiting[visiting.index(node) :], node]
        if node in done:
            return None
        visiting.append(node)
        for nxt in graph[node]:
            if found := visit(nxt):
                return found
        visiting.pop()
        done.add(node)
        return None

    for start in graph:
        if found := visit(start):
            return found
    return None


# --- A7 map_questions --------------------------------------------------------------------


class QuestionMapping(BaseModel):
    q_id: str = Field(min_length=1)
    topic_id: str | None = Field(pattern=_TOPIC_ID)
    skill_id: str | None
    trap: str | None
    note: str = ""

    @model_validator(mode="after")
    def _skill_of_topic(self) -> Self:
        if (self.topic_id is None) != (self.skill_id is None):
            raise ValueError(f"{self.q_id}: topic_id and skill_id must both be set or both null")
        if self.topic_id and not self.skill_id.startswith(f"{self.topic_id}."):  # type: ignore[union-attr]
            raise ValueError(
                f"{self.q_id}: skill {self.skill_id} is not a skill of topic {self.topic_id}"
            )
        return self


class MapQuestionsResult(BaseModel):
    mappings: list[QuestionMapping]


# --- extract_answer (§2.4, P1) -----------------------------------------------------------


class AnswerLine(BaseModel):
    latex: LatexStr
    confidence: float = Field(ge=0, le=1)


class ExtractAnswerResult(BaseModel):
    lines: list[AnswerLine]
    notes: str = ""
