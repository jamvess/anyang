"""The hint ladder: what the tutor does after a check (specs/features/tutor/demo-room.md §2 K).

Code picks the directive and the LLM only says it (CLAUDE.md rule 1). Pure functions: no AI
call, no database. The number of hints before the solution is
``tutoring.max_hints_before_solution`` in config/learning.yaml.
"""

import re
from typing import Literal

from app.domain.checker import Verdict
from app.settings import TutoringConfig

Directive = Literal["continue", "hint_1", "hint_2", "reveal", "praise_and_show", "ask_working"]

# hint_2 is the last level the prompt knows; a longer ladder repeats it (§2 K item 1).
_HINT_LEVELS: tuple[Directive, ...] = ("hint_1", "hint_2")

# An operator SymPy evaluates by itself, so a line that still has one is a step, not the
# final answer (§2 K item 2): \frac{d}{dx}, \frac{d^2}{dx^2}, \lim, \int, \sum, d/dx.
_UNEVALUATED = re.compile(r"\\frac\{d(?:\^\{?\d+\}?)?\}\{d|\\lim|\\int|\\sum|\bd/d[a-z]")
_SPACES = re.compile(r"\s+")


def unfinished(verdict: Verdict, last_line: str) -> bool:
    """A right step that is not yet the final answer: an operator still to work out, or the
    right value not yet in the form the problem asks for (``incomplete``)."""
    if verdict == "incomplete":
        return True
    return verdict == "correct" and bool(_UNEVALUATED.search(_SPACES.sub("", last_line)))


def decide_directive(
    verdict: Verdict | None,
    *,
    give_up: bool,
    unfinished: bool,
    no_working: bool,
    wrong_before: int | None,
    cfg: TutoringConfig,
) -> Directive:
    """The table of §2 K item 1; the first row that matches wins.

    ``wrong_before`` is how many wrong answers this problem already had; None means the room
    has no ladder (not local), where every finished answer gets the solution as AM-07 says."""
    if give_up:
        return "reveal"
    ladder = wrong_before is not None
    if ladder and unfinished:
        return "continue"
    if no_working:
        return "ask_working"
    if verdict == "correct":
        return "praise_and_show"
    if ladder and verdict == "incorrect":
        wrong = wrong_before + 1
        if wrong <= cfg.max_hints_before_solution:
            return _HINT_LEVELS[min(wrong, len(_HINT_LEVELS)) - 1]
    return "reveal"


def attempt_outcome(
    directive: Directive, wrong_before: int, cfg: TutoringConfig
) -> tuple[bool, bool] | None:
    """``(is_correct, independent)`` of the one attempt a problem records when it ends
    (§2 K item 8), or None while it goes on. Right after the last hint is not independent."""
    if directive == "praise_and_show":
        return True, wrong_before < cfg.max_hints_before_solution
    if directive == "reveal":
        return False, True
    return None
