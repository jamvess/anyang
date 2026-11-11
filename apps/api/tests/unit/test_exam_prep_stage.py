"""Pure rules of an exam prep: today in Bangkok, days_left and stage
(specs/features/exam-prep/create-exam-prep.md §2.3, §2.4 · api.md v1.14 `ExamPrep`).

`app.domain.exam_prep` has no I/O: the repository collects the facts (active scope, topic
importances, materials) and these functions decide.
"""

from datetime import UTC, date, datetime

import pytest

from app.domain.exam_prep import MaterialFacts, bangkok_today, days_left, prep_stage

CONFIRMED = MaterialFacts(kind_confirmed=True, status="confirmed")
INGESTING = MaterialFacts(kind_confirmed=True, status="ingesting")
FAILED = MaterialFacts(kind_confirmed=True, status="failed")
READY = MaterialFacts(kind_confirmed=True, status="ready")
CLASSIFIED = MaterialFacts(kind_confirmed=False, status="classified")
UPLOADED = MaterialFacts(kind_confirmed=False, status="uploaded")


@pytest.mark.parametrize(
    ("now", "today"),
    [
        (datetime(2026, 11, 11, 5, 0, tzinfo=UTC), date(2026, 11, 11)),
        (datetime(2026, 11, 11, 16, 59, 59, tzinfo=UTC), date(2026, 11, 11)),  # 23:59:59 BKK
        (datetime(2026, 11, 11, 17, 0, tzinfo=UTC), date(2026, 11, 12)),  # 00:00 BKK
        (datetime(2026, 11, 11, 17, 30, tzinfo=UTC), date(2026, 11, 12)),  # AC-boundary-date-tz
    ],
)
def test_CM02_today_is_the_date_in_bangkok(now: datetime, today: date) -> None:
    assert bangkok_today(now) == today


@pytest.mark.parametrize(
    ("exam_date", "expected"),
    [
        (date(2026, 11, 10), -1),  # AC-14: a past exam stays in the list with a negative count
        (date(2026, 11, 11), 0),
        (date(2026, 11, 12), 1),
        (date(2026, 12, 8), 27),
    ],
)
def test_CM02_days_left(exam_date: date, expected: int) -> None:
    assert days_left(exam_date, today=date(2026, 11, 11)) == expected


@pytest.mark.parametrize(
    ("active_scope", "importances", "materials", "stage"),
    [
        # materials: no file, or no confirmed file
        (False, [], [], "materials"),
        (False, [], [UPLOADED, CLASSIFIED], "materials"),
        # processing: a file with kind_confirmed = true
        (False, [], [CONFIRMED], "processing"),
        (False, [], [CLASSIFIED, READY], "processing"),
        # scope: topics all with importance, no confirmed file still confirmed/ingesting/failed
        (False, [3, 1, 0], [READY], "scope"),
        (False, [2], [READY, CLASSIFIED], "scope"),
        # not scope: a topic without importance yet
        (False, [3, None], [READY], "processing"),
        # not scope: topics complete but a confirmed file is still being read (CM-05)
        (False, [3, 2], [READY, INGESTING], "processing"),
        (False, [3, 2], [READY, CONFIRMED], "processing"),
        (False, [3, 2], [READY, FAILED], "processing"),
        # no topics at all is not ready (Junior 2026-11-11 · Jam revisits at ingestion)
        (False, [], [READY], "processing"),
        # tutoring wins over everything
        (True, [], [], "tutoring"),
        (True, [3, None], [INGESTING], "tutoring"),
    ],
)
def test_CM01_stage(
    active_scope: bool,
    importances: list[int | None],
    materials: list[MaterialFacts],
    stage: str,
) -> None:
    assert (
        prep_stage(
            has_active_scope=active_scope, topic_importances=importances, materials=materials
        )
        == stage
    )
