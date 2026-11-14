"""Opening the room with a token when the prep has topics: progress card from the database, the
chosen topic and its reason, and a problem whose answer SymPy verified
(specs/features/tutor/room-problems-db.md · ai-orchestration §2.2.2, §2.4.6 · AM-11).

Code chooses the topic, the difficulty and whether the answer is right; the model writes the
problem and the greeting (CLAUDE.md rules 1, 4). Store calls run in the thread pool: the
Supabase client blocks.
"""

import logging
from collections.abc import AsyncIterator, Sequence
from contextlib import aclosing
from uuid import UUID

from starlette.concurrency import run_in_threadpool

from app.ai.call_context import AICallContext
from app.ai.gateway import Gateway
from app.auth import AuthContext
from app.db.errors import DbUnavailableError
from app.db.room import PrepRecord, RoomRepository, SessionRecord
from app.db.room_problems import ProblemRecord, ProblemRepository, ProgressFacts
from app.domain.bkt import (
    ReadinessTopic,
    TopicProgress,
    level,
    mastery_eff,
    readiness,
    target_difficulty,
)
from app.domain.room import (
    TopicFacts,
    choose_topic,
    focus_text,
    poses_a_problem,
    same_problem,
    text_latex_of,
)
from app.math.sympy_service import check_lines
from app.models.room import (
    DoneEvent,
    ProblemEvent,
    ProgressCardEvent,
    ProgressTopic,
    SessionEvent,
    TokenEvent,
)
from app.models.tutor_ai import GenerateProblemResult
from app.services.room_db import _save_tutor
from app.services.room_opening import greeting_events, topic_lines
from app.services.tutor_turn import Event, call_scope
from app.settings import LearningConfig, get_settings

log = logging.getLogger(__name__)

# No planner yet, so the mode never changes (bkt-mastery.md §10 item 2).
MODE = "normal"
# What the checker grades (spec §2.3 item 2).
ANSWER_FORMATS = "expression, factored, equation"
NONE = "none"  # the prompts' word for "nothing"


def usable_topics(topics: Sequence[TopicFacts]) -> list[TopicFacts]:
    """Spec §2.1: every topic that is not excluded, before or after the scope is confirmed.
    None of them has a star yet (stars not computed) → [] so the room opens as before (§2.2
    item 3 · self-review PR #131)."""
    usable = [t for t in topics if t.status != "excluded"]
    return usable if any((t.importance or 0) >= 1 for t in usable) else []


def progress_state(row: ProgressFacts | None, cfg: LearningConfig) -> TopicProgress:
    """A `topic_progress` row as BKT reads it; no row = not started at `bkt.p_init`."""
    if row is None:
        return TopicProgress(cfg.bkt.p_init, 0, 0)
    return TopicProgress(row.mastery, row.attempts_n, row.d_max)


def topic_level(state: TopicProgress, stars: int, cfg: LearningConfig) -> str:
    """The level of the card and of `topic_progress.level` (topic-progress-db.md §2.2 item 3):
    every skill counts as covered until skill coverage exists (§10 item 2)."""
    return level(state, target_difficulty(stars, MODE, cfg), True, cfg)


def _card(
    topics: list[TopicFacts], progress: list[ProgressFacts], days: int
) -> tuple[ProgressCardEvent, dict[UUID, str], dict[UUID, float]]:
    """The progress card from the database (spec §2.2 item 2), and each topic's level and mastery
    for choosing the topic."""
    cfg = get_settings().learning
    rows = {p.topic_id: p for p in progress}
    card_topics, weights, levels, mastery = [], [], {}, {}
    for topic in topics:
        stars = topic.importance or 0
        row = rows.get(topic.id)
        state = progress_state(row, cfg)
        d_target = target_difficulty(stars, MODE, cfg)
        this_level = topic_level(state, stars, cfg) if row else "not_started"
        levels[topic.id] = this_level
        if row:
            mastery[topic.id] = row.mastery
        card_topics.append(
            ProgressTopic(
                id=str(topic.id),
                name=topic.name,
                stars=stars,
                level=this_level,
                review_due=False,
                origin=topic.origin,
            )
        )
        eff = mastery_eff(state.mastery, state.d_max, d_target, cfg)
        weights.append(ReadinessTopic(stars, topic.signal_r, eff, state.attempts))
    card = ProgressCardEvent(
        days_left=days,
        passed=sum(1 for lv in levels.values() if lv == "passed"),
        total=len(topics),
        readiness=readiness(weights, cfg),
        topics=card_topics,
    )
    return card, levels, mastery


async def opening_events(
    gateway: Gateway,
    repo: RoomRepository,
    problems: ProblemRepository,
    auth: AuthContext,
    prep: PrepRecord,
    session: SessionRecord,
    topics: list[TopicFacts],
    days: int,
    fallback_greeting: str,
) -> AsyncIterator[Event]:
    """Spec §2.2: session → progress_card → greeting → problem → done."""
    yield "session", SessionEvent(session_id=session.id)
    try:
        progress = await run_in_threadpool(problems.list_progress, prep.id)
    except DbUnavailableError:
        progress = []
    card, levels, mastery = _card(topics, progress, days)
    yield "progress_card", card

    cfg = get_settings().learning
    call_context = AICallContext(auth.tenant_id, auth.user_id, session.id)
    chosen = choose_topic(topics, mastery, levels, cfg.bkt.p_init)
    problem: ProblemRecord | None = None
    card_latex = ""
    if chosen is not None:
        found = await _problem_for(
            gateway, problems, auth, prep.id, session.id, chosen, call_context
        )
        if found is not None:
            problem, card_latex = found

    facts = {
        "days_left": str(card.days_left),
        "readiness": f"{round(card.readiness * 100)}%",
        "topics": topic_lines(card),
        "problem": problem.text if problem else NONE,  # never the answer (AM-13)
        "focus": focus_text(chosen, levels[chosen.id]) if chosen else NONE,
    }
    said: list[str] = []
    # Closed with the stream: a client that leaves also closes the model's stream.
    async with aclosing(
        greeting_events(gateway, facts, fallback_greeting, said, call_context)
    ) as greeting:
        async for event in greeting:
            yield event
    ids = await _save_tutor(repo, auth, session, "".join(said))
    if problem is not None:
        yield (
            "problem",
            ProblemEvent(
                problem_id=str(problem.id),
                text_latex=card_latex,
                difficulty=problem.difficulty,
                purpose=problem.purpose,  # type: ignore[arg-type]  # problems.purpose check
            ),
        )
    elif chosen is not None:
        line = get_settings().messages.room.no_problem
        yield "token", TokenEvent(speaker="tutor", text=line)
        ids += await _save_tutor(repo, auth, session, line)  # what was sent is saved (§2.2)
    yield "done", DoneEvent(message_ids=ids)


async def _problem_for(
    gateway: Gateway,
    problems: ProblemRepository,
    auth: AuthContext,
    prep_id: UUID,
    session_id: UUID,
    topic: TopicFacts,
    call_context: AICallContext,
) -> tuple[ProblemRecord, str] | None:
    """The open problem of the topic, or a new verified one (spec §2.3); None when there is
    none. The second value is the card's LaTeX."""
    cfg = get_settings().learning
    difficulty = target_difficulty(topic.importance or 0, MODE, cfg)
    try:
        reused = await run_in_threadpool(problems.open_problem, prep_id, topic.id)
        if reused is not None:
            return reused, text_latex_of(reused.text)
        if difficulty is None:  # a skipped topic is never chosen (importance >= 1 · §2.2 item 3)
            return None
        skills = await run_in_threadpool(problems.list_skills, topic.id)
        limit = cfg.session.grounding_chunks
        chunks = await run_in_threadpool(problems.source_chunks, topic.id, limit)
        avoid = cfg.session.avoid_recent_problems
        previous = await run_in_threadpool(problems.recent_problems, prep_id, topic.id, avoid)
        # The latest problems already say whether the topic has one (self-review PR #133).
        practised = bool(previous) or (
            avoid == 0 and await run_in_threadpool(problems.topic_has_problems, prep_id, topic.id)
        )
    except DbUnavailableError:
        return None

    keys = {f"s{n}": skill.id for n, skill in enumerate(skills, start=1)}
    values = {
        "topic": topic.name,
        "skills": "\n".join(f"{key}: {skill.name}" for key, skill in zip(keys, skills, strict=True))
        or NONE,
        "source_text": "\n\n".join(chunks) or NONE,
        "difficulty": str(difficulty),
        "answer_formats": ANSWER_FORMATS,
        # v2: the latest problems of the topic, so the next one differs (§2.3 item 2).
        # One line each, as the prompt reads them: a text with a line break stays one problem.
        "previous_problems": "\n".join(f"- {' '.join(p.text.split())}" for p in previous) or NONE,
    }
    for attempt in range(1 + cfg.checker.max_generate_retries):
        try:
            with call_scope(call_context):
                result = await gateway.call("generate_problem", values, GenerateProblemResult)
        except Exception as error:  # the model or the schema: counts as a try (spec AC-6)
            log.warning("generate_problem try %d failed: %s", attempt + 1, error)
            continue
        if repeated := next((p for p in previous if same_problem(result.text, p.text)), None):
            # Both texts, to calibrate session.avoid_recent_problems (learning.yaml).
            log.warning(
                "generate_problem try %d: %r is the same as problem %s %r",
                attempt + 1,
                result.text,
                repeated.id,
                repeated.text,
            )
            continue
        if not await verified(result):
            log.warning(
                "generate_problem try %d: SymPy does not confirm %r = %r (%s)",
                attempt + 1,
                result.expression,
                result.reference_answer,
                result.answer_format,
            )
            continue
        try:
            saved = await run_in_threadpool(
                lambda result=result: problems.add_problem(
                    tenant_id=auth.tenant_id,
                    session_id=session_id,
                    topic_id=topic.id,
                    skill_id=keys.get(result.skill or ""),
                    source="generated",
                    text=result.text,
                    reference_answer=result.reference_answer,
                    solution_steps=result.solution_steps,
                    answer_format=result.answer_format,
                    verified=True,
                    difficulty=difficulty,
                    purpose="practice" if practised else "probe",
                )
            )
        except DbUnavailableError:
            return None
        return saved, result.text_latex
    return None


async def next_problem(
    gateway: Gateway,
    problems: ProblemRepository,
    auth: AuthContext,
    prep_id: UUID,
    session_id: UUID,
    call_context: AICallContext,
) -> tuple[ProblemRecord, str] | None:
    """The problem after one has ended (room-answers-db.md §2.2 item 5): the topic and the
    problem by the rules of the opening (§2.2 item 3, §2.3), in the current session."""
    try:
        topics = usable_topics(await run_in_threadpool(problems.list_topics, prep_id))
        progress = await run_in_threadpool(problems.list_progress, prep_id)
    except DbUnavailableError:
        return None
    _, levels, mastery = _card(topics, progress, days=0)  # the card itself comes at opening
    chosen = choose_topic(topics, mastery, levels, get_settings().learning.bkt.p_init)
    if chosen is None:  # also no topics (usable_topics gave [])
        return None
    return await _problem_for(gateway, problems, auth, prep_id, session_id, chosen, call_context)


async def verified(result: GenerateProblemResult) -> bool:
    """AM-11 · ai-orchestration §2.4.6: SymPy evaluates `expression` to `reference_answer`; a
    `factored` answer must also be fully factored. An `expression` that is only the answer
    worked out does not count (`poses_a_problem`)."""
    if not poses_a_problem(result.expression, result.reference_answer):
        return False
    check = await check_lines(
        answer_format=result.answer_format,
        reference_answer=result.reference_answer,
        lines=[result.expression],
    )
    if not check.parsed or check.timed_out or check.final_equal is not True:
        return False
    if result.answer_format == "factored":
        form = await check_lines(
            answer_format="factored",
            reference_answer=result.reference_answer,
            lines=[result.reference_answer],
        )
        # The problem must still need factoring: `(x-1)(x+1)x` for `x(x-1)(x+1)` is the answer.
        return form.final_in_form is True and check.final_in_form is False
    return True
