"""Pure rules of the tutor room on the database (specs/features/tutor/room-sessions-db.md).

No I/O: the room header names (§2.5), the greeting from config/messages.yaml (§2.8) and which
saved messages reach tutor_reply as the conversation (§2.7 item 3).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

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


def _name(params: Mapping[str, Any] | None) -> str | None:
    value = (params or {}).get("name")
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
    user_name = nickname.strip() if nickname and nickname.strip() else FALLBACK_USER_NAME
    buddy_name = _name(buddy.params) if buddy and buddy.enabled else None
    return RoomNames(
        user_name=user_name,
        tutor_name=_name(tutor_params) or preset_tutor_name,
        buddy_name=buddy_name,
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
