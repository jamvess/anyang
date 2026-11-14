"""Pure rules of the tutor room on the database (specs/features/tutor/room-sessions-db.md).

No I/O: the room header names (§2.5), the greeting from config/messages.yaml (§2.8) and which
saved messages reach tutor_reply as the conversation (§2.7 item 3).
"""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.settings import RoomGreetingConfig

# user_name when the user has no nickname (api.md v1.15). User-facing, so Thai.
FALLBACK_USER_NAME = "คุณ"

# A saved chat line: ("user" | "tutor", text).
ChatLine = tuple[str, str]


@dataclass(frozen=True)
class BuddyFacts:
    enabled: bool
    params: Mapping[str, Any] | None


@dataclass(frozen=True)
class RoomNames:
    user_name: str
    tutor_name: str
    buddy_name: str | None
    has_nickname: bool = False  # the greeting needs this, not a compare with FALLBACK_USER_NAME


def _name(params: Any) -> str | None:
    # params is any non-null jsonb (data-model.md): only an object can carry a name; anything
    # else falls back like a missing name instead of a 500 (spec §2.2).
    if not isinstance(params, Mapping):
        return None
    value = params.get("name")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def room_names(
    *,
    nickname: str | None,
    tutor_params: Mapping[str, Any] | None,
    buddy: BuddyFacts | None,
    preset_tutor_name: str,
) -> RoomNames:
    """§2.5: nickname or "คุณ"; the latest tutor profile's name or the first preset's; the
    buddy's name only while it is enabled."""
    has_nickname = bool(nickname and nickname.strip())
    user_name = nickname.strip() if nickname and has_nickname else FALLBACK_USER_NAME
    buddy_name = _name(buddy.params) if buddy and buddy.enabled else None
    return RoomNames(
        user_name=user_name,
        tutor_name=_name(tutor_params) or preset_tutor_name,
        buddy_name=buddy_name,
        has_nickname=has_nickname,
    )


def greeting_text(
    templates: RoomGreetingConfig, *, user_name: str | None, prep_name: str, days_left: int
) -> str:
    """§2.8: hello + exam line + invite. ``user_name`` None means no nickname. Values are
    inserted as text: only the templates (ours, checked at load) are format strings."""
    if user_name is None:
        hello = templates.hello_anonymous.format()
    else:
        hello = templates.hello_named.format(user_name=user_name)
    if days_left >= 1:
        exam = templates.days_left_many.format(days_left=days_left, prep_name=prep_name)
    elif days_left == 0:
        exam = templates.exam_today.format(prep_name=prep_name)
    else:
        exam = templates.exam_passed.format(prep_name=prep_name)
    return f"{hello} {exam} {templates.invite.format()}"


def recent_turns(lines: Sequence[ChatLine], turns: int) -> list[ChatLine]:
    """The lines of the last ``turns`` turns, oldest first. A turn starts at each user line;
    tutor lines before the first user line (the greeting) are a turn of their own
    (demo-room.md §2 E)."""
    grouped: list[list[ChatLine]] = []
    for role, text in lines:
        if role == "user" or not grouped:
            grouped.append([])
        grouped[-1].append((role, text))
    return [line for turn in grouped[-turns:] for line in turn] if turns > 0 else []


# --- the topic of the session and its problem (specs/features/tutor/room-problems-db.md) ------

# Level names as the progress card and the greeting say them (demo-room.md §2 F).
LEVEL_NAMES = {
    "not_started": "ยังไม่เริ่ม",
    "weak": "อ่อน",
    "developing": "กำลังดี",
    "passed": "ผ่าน",
}

_MATH = re.compile(r"\$\$(.+?)\$\$|\$([^$]+)\$", re.DOTALL)
# Characters that mean something in LaTeX text mode, as KaTeX writes them inside \text{}.
_TEXT_ESCAPES = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "%": r"\%",
    "#": r"\#",
    "&": r"\&",
    "_": r"\_",
    "^": r"\textasciicircum{}",
    "~": r"\textasciitilde{}",
    "$": r"\$",
}


@dataclass(frozen=True)
class TopicFacts:
    """A topic of the prep as the room needs it (`topics` row)."""

    id: UUID
    name: str
    order_index: int
    importance: int | None
    status: str  # draft | confirmed | excluded
    origin: str
    signal_r: float = 0.0


def choose_topic(
    topics: Sequence[TopicFacts],
    mastery: Mapping[UUID, float],
    levels: Mapping[UUID, str],
    p_init: float,
) -> TopicFacts | None:
    """§2.2 item 3 (TM-01, simple rule): among topics with a star that are not passed, most
    stars, then lowest mastery (not started = `p_init`), then `order_index`. All passed → the
    lowest mastery. No topic with a star → None."""
    eligible = [t for t in topics if t.status != "excluded" and (t.importance or 0) >= 1]
    if not eligible:
        return None
    open_ones = [t for t in eligible if levels.get(t.id, "not_started") != "passed"]
    if open_ones:
        return min(
            open_ones,
            key=lambda t: (-(t.importance or 0), mastery.get(t.id, p_init), t.order_index),
        )
    return min(eligible, key=lambda t: (mastery.get(t.id, p_init), t.order_index))


def focus_text(topic: TopicFacts, level: str) -> str:
    """The short reason of the choice for the greeting (§2.2 item 4 · TM-02)."""
    return f"{topic.name} · {topic.importance or 0} ดาว · {LEVEL_NAMES[level]}"


def text_latex_of(text: str) -> str:
    """One line of LaTeX for the problem card from text with `$…$` math: the words go in
    `\\text{}` (§10 item 4 · `problems` has no text_latex column)."""
    out: list[str] = []
    end = 0
    for match in _MATH.finditer(text):
        _add_text(out, text[end : match.start()])
        out.append((match.group(1) or match.group(2)).strip())
        end = match.end()
    _add_text(out, text[end:])
    return " ".join(out)


def _add_text(out: list[str], words: str) -> None:
    if words.strip():
        escaped = "".join(_TEXT_ESCAPES.get(char, char) for char in words)
        out.append(rf"\text{{{escaped}}}")


_LATEX_COMMAND = re.compile(r"\\[A-Za-z]+")
_LETTER = re.compile(r"[A-Za-z]")
_SPACE = re.compile(r"\s+")
# A variable on the left, no letter on the right once LaTeX commands are gone (`x = -\frac{2}{3}`).
_SOLVED = re.compile(r"^\s*[A-Za-z]\s*=\s*(?:[^A-Za-z\\]|\\[A-Za-z]+)*$")


def poses_a_problem(expression: str, reference_answer: str) -> bool:
    """§2.3 item 4 (found in the live run, 13 Nov): `expression` must be the problem, not its
    answer worked out by the model, or SymPy would only check arithmetic (`5 + 1` = `6`). So it
    keeps a variable once the LaTeX commands are taken out, and is not the answer itself."""
    if _SPACE.sub("", expression) == _SPACE.sub("", reference_answer):
        return False
    if all(_SOLVED.match(part) for part in expression.split(",")):
        return False  # `x=3, x=2`: solutions, not an equation to solve
    return bool(_LETTER.search(_LATEX_COMMAND.sub("", expression)))


def _math_of(text: str) -> str:
    return "".join(_SPACE.sub("", m.group(1) or m.group(2)) for m in _MATH.finditer(text))


def same_problem(text: str, other: str) -> bool:
    """§2.3 item 4 (v2 · PR #133): two problem texts ask the same thing when, with every space
    taken out, all their `$…$` math is the same (other words around it do not make a new
    problem) or, when neither has math, their whole text is the same."""
    math, other_math = _math_of(text), _math_of(other)
    if math or other_math:
        return math == other_math
    return _SPACE.sub("", text) == _SPACE.sub("", other)
