"""compute_importance: topic stars 0-3 and signal_r (specs/features/scope/compute-importance.md).

Thresholds come from config/learning.yaml -> stars through get_settings(); a test that needs
another value changes it with model_copy. Star levels (0-3) and exam weights in the inputs are
data, not thresholds (spec §4).
"""

import pytest

from app.domain.stars import ExamIn, TopicImportance, TopicIn, compute_importance
from app.settings import StarsConfig, get_settings

REASON_EXCLUDED = "ตัดออกตามที่แจ้ง"
REASON_NOT_SEEN = "ไม่พบในข้อสอบเก่า"
REASON_ONLY_ZERO_WEIGHT = "พบเฉพาะในข้อสอบที่ไม่ได้ใช้คิดดาว"
REASON_NO_PAST_EXAM = "ไม่มีข้อสอบเก่า จึงประเมินจากจำนวนหน้าในชีท"


def seen(n_in: int, n_total: int) -> str:
    return f"ออกในข้อสอบเก่า {n_in} จาก {n_total} ชุด"


def basis_of(name: str) -> str:
    return f'เป็นพื้นฐานของ "{name}"'


def topic(
    id: str,
    *,
    name: str | None = None,
    prereq_ids: list[str] | None = None,
    excluded: bool = False,
    importance_source: str = "computed",
    current_importance: int | None = None,
    current_reason: str | None = None,
    page_count: int = 0,
) -> TopicIn:
    # The name differs from the id so a reason that quotes the id instead of the name fails.
    return TopicIn(
        id=id,
        name=name if name is not None else f"หัวข้อ {id}",
        prereq_ids=prereq_ids or [],
        excluded=excluded,
        importance_source=importance_source,
        current_importance=current_importance,
        current_reason=current_reason,
        page_count=page_count,
    )


def by_id(result: list[TopicImportance]) -> dict[str, TopicImportance]:
    return {r.topic_id: r for r in result}


@pytest.fixture
def cfg() -> StarsConfig:
    return get_settings().learning.stars


@pytest.fixture
def two_same(cfg: StarsConfig) -> list[ExamIn]:
    """Two past exams from the same instructor (the setup of AC-1, AC-2, AC-5 to AC-13b)."""
    return [ExamIn("m1", cfg.weight_same_instructor), ExamIn("m2", cfg.weight_same_instructor)]


# --- with past exams -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("second_exam", "seen_in", "expected_stars", "expected_reason"),
    [
        pytest.param("same", {"m1", "m2"}, 3, seen(2, 2), id="AC-1 seen in both"),
        pytest.param("same", {"m1"}, 2, seen(1, 2), id="AC-2 seen in one"),
        pytest.param("other", {"m1"}, 3, seen(1, 2), id="AC-3 only the same-instructor exam"),
        pytest.param("other", {"m2"}, 2, seen(1, 2), id="AC-4 only the other-instructor exam"),
    ],
)
def test_SM03_signal_and_stars_from_past_exams(
    cfg: StarsConfig,
    second_exam: str,
    seen_in: set[str],
    expected_stars: int,
    expected_reason: str,
) -> None:
    # m1 is always from the same instructor; m2 from the same or another one.
    second_weight = getattr(cfg, f"weight_{second_exam}_instructor")
    exams = [ExamIn("m1", cfg.weight_same_instructor), ExamIn("m2", second_weight)]
    weight = {e.material_id: e.weight for e in exams}
    expected_r = sum(weight[m] for m in seen_in) / sum(weight.values())

    [result] = compute_importance([topic("t1")], exams, {("t1", m) for m in seen_in}, cfg)

    assert result.topic_id == "t1"
    assert result.signal_r == pytest.approx(expected_r)
    assert result.importance == expected_stars
    assert result.reason == expected_reason


def test_SM03_direct_prerequisite_of_three_star(cfg: StarsConfig, two_same: list[ExamIn]) -> None:
    # AC-5: B is a direct prerequisite of A (★★★) and never seen.
    # AC-6: C is a prerequisite of B only, so it is not lifted (one level, not transitive).
    topics = [
        topic("a", name="อนุพันธ์", prereq_ids=["b"]),
        topic("b", name="ลิมิต", prereq_ids=["c"]),
        topic("c", name="ฟังก์ชัน"),
    ]
    result = by_id(compute_importance(topics, two_same, {("a", "m1"), ("a", "m2")}, cfg))

    assert result["a"].importance == 3
    assert result["b"].importance == cfg.prerequisite_of_three_star_gets
    assert result["b"].reason == basis_of("อนุพันธ์")
    assert result["b"].signal_r == 0
    assert result["c"].importance == 1
    assert result["c"].reason == REASON_NOT_SEEN


def test_SM03_never_seen_gets_one_star(cfg: StarsConfig, two_same: list[ExamIn]) -> None:
    # AC-7
    topics = [topic("a"), topic("x")]
    result = by_id(compute_importance(topics, two_same, {("a", "m1"), ("a", "m2")}, cfg))

    assert result["x"].importance == 1
    assert result["x"].reason == REASON_NOT_SEEN
    assert result["x"].signal_r == 0


def test_SM03_seen_prerequisite_keeps_exam_reason(cfg: StarsConfig, two_same: list[ExamIn]) -> None:
    # AC-8: B is a prerequisite of A (★★★) but was itself seen in 1 of 2 exams.
    topics = [topic("a", prereq_ids=["b"]), topic("b")]
    appearances = {("a", "m1"), ("a", "m2"), ("b", "m1")}
    result = by_id(compute_importance(topics, two_same, appearances, cfg))

    assert result["b"].importance == 2
    assert result["b"].reason == seen(1, 2)


def test_SM03_prerequisite_reason_names_first_three_star_topic(
    cfg: StarsConfig, two_same: list[ExamIn]
) -> None:
    # AC-9: A1 comes before A2 in the input; their ids sort the other way round, so the
    # test fails if the code picks by id instead of input order.
    topics = [
        topic("b", name="ลิมิต"),
        topic("t9", name="A1", prereq_ids=["b"]),
        topic("t1", name="A2", prereq_ids=["b"]),
    ]
    appearances = {("t9", "m1"), ("t9", "m2"), ("t1", "m1"), ("t1", "m2")}
    result = by_id(compute_importance(topics, two_same, appearances, cfg))

    assert result["t9"].importance == 3
    assert result["t1"].importance == 3
    assert result["b"].reason == basis_of("A1")


# --- excluded and user-set stars -----------------------------------------------------


def test_SM03_excluded_gets_zero_but_keeps_signal(cfg: StarsConfig, two_same: list[ExamIn]) -> None:
    # AC-10
    [result] = compute_importance(
        [topic("a", excluded=True)], two_same, {("a", "m1"), ("a", "m2")}, cfg
    )

    assert result.importance == 0
    assert result.reason == REASON_EXCLUDED
    assert result.signal_r == pytest.approx(1.0)


def test_SM03_excluded_topic_does_not_lift_its_prerequisites(
    cfg: StarsConfig, two_same: list[ExamIn]
) -> None:
    # AC-11
    topics = [topic("a", excluded=True, prereq_ids=["b"]), topic("b")]
    result = by_id(compute_importance(topics, two_same, {("a", "m1"), ("a", "m2")}, cfg))

    assert result["b"].importance == 1
    assert result["b"].reason == REASON_NOT_SEEN


def test_SM09_user_stars_and_reason_are_kept(cfg: StarsConfig, two_same: list[ExamIn]) -> None:
    # AC-12: stars and reason stay, signal_r is computed again (readiness % uses it).
    [result] = compute_importance(
        [
            topic(
                "a",
                importance_source="user",
                current_importance=1,
                current_reason="user: อาจารย์ไม่เน้น",
            )
        ],
        two_same,
        {("a", "m1"), ("a", "m2")},
        cfg,
    )

    assert result.importance == 1
    assert result.reason == "user: อาจารย์ไม่เน้น"
    assert result.signal_r == pytest.approx(1.0)


def test_SM09_user_three_star_lifts_its_prerequisites(
    cfg: StarsConfig, two_same: list[ExamIn]
) -> None:
    # AC-13: A was never seen but the user set ★★★, so B (prerequisite, never seen) is lifted.
    # Another topic is seen so the exams count and the past-exam rules apply.
    topics = [
        topic(
            "a",
            name="อินทิกรัล",
            prereq_ids=["b"],
            importance_source="user",
            current_importance=3,
            current_reason="user: อาจารย์บอกว่าออกแน่",
        ),
        topic("b"),
        topic("z"),
    ]
    result = by_id(compute_importance(topics, two_same, {("z", "m1")}, cfg))

    assert result["a"].importance == 3
    assert result["a"].reason == "user: อาจารย์บอกว่าออกแน่"
    assert result["b"].importance == cfg.prerequisite_of_three_star_gets
    assert result["b"].reason == basis_of("อินทิกรัล")


def test_SM09_user_source_without_stars_is_computed(
    cfg: StarsConfig, two_same: list[ExamIn]
) -> None:
    # AC-13b
    [result] = compute_importance(
        [topic("a", importance_source="user", current_importance=None)],
        two_same,
        {("a", "m1"), ("a", "m2")},
        cfg,
    )

    assert result.importance == 3
    assert result.reason == seen(2, 2)


# --- boundaries and config -----------------------------------------------------------

EPS = 0.001  # spec AC-boundary: r = 0.5 is exact in float


@pytest.mark.parametrize(
    ("min_r", "expected_stars"),
    [(0.5 + EPS, 2), (0.5, 3), (0.5 - EPS, 3)],
    ids=["above", "equal", "below"],
)
def test_SM03_three_star_boundary(
    cfg: StarsConfig, two_same: list[ExamIn], min_r: float, expected_stars: int
) -> None:
    # AC-boundary: two equal weights, seen in one, so r = 0.5.
    boundary_cfg = cfg.model_copy(update={"three_star_min_r": min_r})
    [result] = compute_importance([topic("a")], two_same, {("a", "m1")}, boundary_cfg)

    assert result.signal_r == 0.5
    assert result.importance == expected_stars


def test_SM03_prerequisite_stars_from_config(cfg: StarsConfig, two_same: list[ExamIn]) -> None:
    # AC-config: the setup of AC-5 with prerequisite_of_three_star_gets = 1.
    one_star_cfg = cfg.model_copy(update={"prerequisite_of_three_star_gets": 1})
    topics = [topic("a", name="อนุพันธ์", prereq_ids=["b"]), topic("b")]
    result = by_id(compute_importance(topics, two_same, {("a", "m1"), ("a", "m2")}, one_star_cfg))

    assert result["b"].importance == 1
    assert result["b"].reason == basis_of("อนุพันธ์")


def test_SM03_zero_total_weight_means_no_past_exam(cfg: StarsConfig) -> None:
    # AC-zero-weight: both exams weigh 0 → no-past-exam rules, signal_r = page share.
    exams = [ExamIn("m1", 0.0), ExamIn("m2", 0.0)]
    topics = [topic("a", page_count=6), topic("b", page_count=2)]
    result = by_id(compute_importance(topics, exams, {("a", "m1"), ("b", "m2")}, cfg))

    assert result["a"].signal_r == pytest.approx(6 / 8)
    assert result["b"].signal_r == pytest.approx(2 / 8)
    # n = 2: rank 0 < 2/3 → ★★★, rank 1 < 4/3 → ★★
    assert result["a"].importance == 3
    assert result["b"].importance == 2
    assert result["a"].reason == REASON_NO_PAST_EXAM
    assert result["b"].reason == REASON_NO_PAST_EXAM


def test_SM03_zero_weight_exam_is_not_counted(cfg: StarsConfig) -> None:
    # AC-weight-zero-one
    exams = [ExamIn("m1", 1.0), ExamIn("m2", 0.0)]
    topics = [topic("x"), topic("y")]
    appearances = {("x", "m2"), ("y", "m1"), ("y", "m2")}
    result = by_id(compute_importance(topics, exams, appearances, cfg))

    assert result["x"].signal_r == 0
    assert result["x"].importance == 1
    assert result["x"].reason == REASON_ONLY_ZERO_WEIGHT
    assert result["y"].signal_r == pytest.approx(1.0)
    assert result["y"].importance == 3
    assert result["y"].reason == seen(1, 1)


# --- no past exam --------------------------------------------------------------------


@pytest.mark.parametrize(
    ("pages", "expected_stars"),
    [
        pytest.param([12, 10, 8, 6, 4, 2], [3, 3, 2, 2, 1, 1], id="AC-14 six topics"),
        pytest.param([7, 6, 5, 4, 3, 2, 1], [3, 3, 3, 2, 2, 1, 1], id="AC-15 seven topics"),
        pytest.param([10, 8, 8, 8, 4, 2], [3, 3, 3, 3, 1, 1], id="AC-16 ties share a rank"),
        pytest.param([5, 5, 5], [2, 2, 2], id="AC-16b all equal"),
        pytest.param([0, 0, 0], [2, 2, 2], id="AC-16b all zero"),
        pytest.param([2, 12, 8], [1, 3, 2], id="ranked by pages, not by input order"),
    ],
)
def test_SM03_no_past_exam_page_terciles(
    cfg: StarsConfig, pages: list[int], expected_stars: list[int]
) -> None:
    topics = [topic(f"t{i}", page_count=p) for i, p in enumerate(pages)]
    result = compute_importance(topics, [], set(), cfg)

    total = sum(pages)
    assert [r.importance for r in result] == expected_stars
    assert [r.signal_r for r in result] == pytest.approx([p / total if total else 0 for p in pages])
    assert all(r.reason == REASON_NO_PAST_EXAM for r in result)


def test_SM03_no_past_exam_skips_excluded(cfg: StarsConfig) -> None:
    # AC-17: the excluded topic has the most pages; it gets 0 and is left out of n (n = 3).
    topics = [
        topic("ex", excluded=True, page_count=9),
        topic("a", page_count=6),
        topic("b", page_count=4),
        topic("c", page_count=2),
    ]
    result = by_id(compute_importance(topics, [], set(), cfg))

    assert result["ex"].importance == 0
    assert result["ex"].reason == REASON_EXCLUDED
    assert [result[t].importance for t in ("a", "b", "c")] == [3, 2, 1]
    # signal_r is the page share over every topic, the excluded one included (spec §2 step 1).
    assert result["ex"].signal_r == pytest.approx(9 / 21)
    assert result["a"].signal_r == pytest.approx(6 / 21)


def test_SM03_no_past_exam_keeps_user_stars_and_counts_their_rank(cfg: StarsConfig) -> None:
    # Spec §2 step 3 items 1-3: a user-set topic keeps its stars and reason but still takes a
    # rank. With the user topic counted, n = 3 and "b" (rank 1) gets ★★; without it, n = 2
    # and "b" (rank 0) would get ★★★.
    topics = [
        topic(
            "u",
            importance_source="user",
            current_importance=1,
            current_reason="user: ไม่ออก",
            page_count=10,
        ),
        topic("b", page_count=6),
        topic("c", page_count=2),
    ]
    result = by_id(compute_importance(topics, [], set(), cfg))

    assert result["u"].importance == 1
    assert result["u"].reason == "user: ไม่ออก"
    assert result["b"].importance == 2
    assert result["c"].importance == 1


def test_SM03_no_past_exam_ignores_prerequisites(cfg: StarsConfig) -> None:
    # AC-18: "b" is a prerequisite of "a" (★★★ by pages); it keeps the stars of its own rank.
    topics = [
        topic("a", prereq_ids=["b"], page_count=10),
        topic("c", page_count=6),
        topic("b", page_count=2),
    ]
    result = by_id(compute_importance(topics, [], set(), cfg))

    assert result["a"].importance == 3
    assert result["b"].importance == 1
    assert result["b"].reason == REASON_NO_PAST_EXAM


# --- general -------------------------------------------------------------------------


def test_SM03_output_keeps_input_order(cfg: StarsConfig, two_same: list[ExamIn]) -> None:
    # AC-order: every topic comes back once, in input order, whatever its stars.
    topics = [topic("z"), topic("a", prereq_ids=["z"]), topic("m", excluded=True), topic("b")]
    appearances = {("a", "m1"), ("a", "m2"), ("b", "m1")}
    result = compute_importance(topics, two_same, appearances, cfg)

    assert [r.topic_id for r in result] == ["z", "a", "m", "b"]
    assert compute_importance([], two_same, set(), cfg) == []
    assert compute_importance([], [], set(), cfg) == []


# --- added after /code-review (8 Nov) · not in spec §8 ------------------------------


def test_SM03_signal_r_does_not_depend_on_exam_order(cfg: StarsConfig) -> None:
    # Spec §1 (reproducible): weights like 0.1, 0.2, 0.3 are not exact in binary. Adding them
    # one by one (+=) gives 0.6000000000000001 in this order and 0.6 in the other, so r would
    # depend on the exam order. (Python 3.12 sum() is already compensated; the code uses
    # math.fsum, which is exactly rounded.)
    exams = [ExamIn("m1", 0.1), ExamIn("m2", 0.2), ExamIn("m3", 0.3), ExamIn("m4", 0.4)]
    appearances = {("a", "m1"), ("a", "m2"), ("a", "m3")}

    results = [
        compute_importance([topic("a")], order, appearances, cfg)[0].signal_r
        for order in (exams, exams[::-1])
    ]
    assert results[0] == results[1] == 0.6
