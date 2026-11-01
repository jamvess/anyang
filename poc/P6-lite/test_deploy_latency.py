"""Tests for the parts of deploy_latency.py that decide the numbers in the P6-lite report.

cd apps/api && uv run pytest ../../poc/P6-lite -q
"""

from deploy_latency import (
    TARGET_MINUTES,
    Build,
    Merge,
    Revision,
    build_rows,
    first_revision_of_digest,
    matches_trigger,
    minutes_between,
    summary,
)

GLOBS = ["apps/api/**", "config/**", "prompts/**", "infra/**"]


def merge(number: int, at: str, commit: str, files: list[str]) -> Merge:
    return Merge(number=number, title=f"PR {number}", merged_at=at, commit=commit, files=files)


def build(commit: str, finish: str | None, status: str = "SUCCESS", digest: str = "") -> Build:
    return Build(
        id=f"b-{commit}",
        commit=commit,
        status=status,
        create_time="2026-10-31T16:00:00Z",
        finish_time=finish,
        digest=digest or f"sha256:{commit}",
    )


def test_P6_trigger_globs_match_any_depth_and_only_listed_folders():
    assert matches_trigger(["apps/api/app/db/ai_calls.py"], GLOBS)
    assert matches_trigger(["docs/x.md", "config/ai.yaml"], GLOBS)
    assert not matches_trigger(["apps/web/app/page.tsx", "docs/team/roles.md"], GLOBS)
    assert not matches_trigger([], GLOBS)


def test_P6_minutes_between_reads_gh_and_gcloud_times():
    # gh: no fraction · gcloud: nanoseconds trimmed by Python to microseconds
    assert (
        minutes_between("2026-10-31T16:47:43Z", "2026-10-31T16:51:34.926626Z") == 3.87
    )  # 3 min 51.9 s


def test_P6_rows_pair_merge_with_build_of_its_commit():
    merges = [
        merge(1, "2026-10-31T16:00:00Z", "aaa", ["apps/api/x.py"]),
        merge(2, "2026-10-31T17:00:00Z", "bbb", ["apps/web/y.tsx"]),
    ]
    builds = [build("aaa", "2026-10-31T16:04:00Z")]
    revisions = {"sha256:aaa": ("api-staging-00001", "2026-10-31T16:03:50Z")}

    rows = build_rows(merges, builds, revisions, GLOBS)

    assert [(r.pr, r.should_deploy, r.minutes_to_deployed) for r in rows] == [
        (1, True, 4.0),
        (2, False, None),
    ]
    assert rows[0].revision == "api-staging-00001"
    assert rows[0].within_target is True
    assert rows[1].within_target is None  # no deploy expected, so not judged


def test_P6_failed_or_slow_build_is_not_within_target():
    merges = [
        merge(1, "2026-10-31T16:00:00Z", "aaa", ["infra/a"]),
        merge(2, "2026-10-31T17:00:00Z", "bbb", ["infra/b"]),
        merge(3, "2026-10-31T18:00:00Z", "ccc", ["infra/c"]),
    ]
    slow = f"2026-10-31T17:{int(TARGET_MINUTES) + 1:02d}:00Z"
    builds = [build("aaa", None, status="FAILURE"), build("bbb", slow)]

    rows = build_rows(merges, builds, {}, GLOBS)

    assert [r.within_target for r in rows] == [False, False, False]
    assert rows[2].build_id is None  # no build at all: the trigger missed it


def test_P6_rerun_of_a_commit_uses_the_newest_build():
    merges = [merge(1, "2026-10-31T16:00:00Z", "aaa", ["infra/a"])]
    old = Build("old", "aaa", "FAILURE", "2026-10-31T16:00:05Z", None, None)
    new = Build("new", "aaa", "SUCCESS", "2026-10-31T16:20:00Z", "2026-10-31T16:24:00Z", None)

    rows = build_rows(merges, [new, old], {}, GLOBS)

    assert rows[0].build_id == "new"


def test_P6_summary_counts_and_checks_serving_revision():
    merges = [
        merge(1, "2026-10-31T16:00:00Z", "aaa", ["apps/api/x.py"]),
        merge(2, "2026-10-31T17:00:00Z", "bbb", ["apps/api/y.py"]),
        merge(3, "2026-10-31T18:00:00Z", "ccc", ["docs/z.md"]),
    ]
    builds = [build("aaa", "2026-10-31T16:03:00Z"), build("bbb", "2026-10-31T17:05:00Z")]
    rows = build_rows(merges, builds, {}, GLOBS)

    result = summary(rows, "sha256:bbb", builds)

    assert result["merges"] == 3
    assert result["merges_that_should_deploy"] == 2
    assert result["within_target"] == 2
    assert result["missed_or_failed"] == []
    assert (result["minutes_min"], result["minutes_max"]) == (3.0, 5.0)
    assert result["serving_newest_deploy"] is True
    assert summary(rows, "sha256:aaa", builds)["serving_newest_deploy"] is False


# --- self-review of PR #96 ---------------------------------------------------------------------


def test_P6_first_successful_build_counts_even_if_a_later_rerun_is_running():
    merges = [merge(1, "2026-10-31T16:00:00Z", "aaa", ["infra/a"])]
    done = Build("done", "aaa", "SUCCESS", "2026-10-31T16:00:05Z", "2026-10-31T16:04:00Z", None)
    rerun = Build("rerun", "aaa", "WORKING", "2026-10-31T16:30:00.5Z", None, None)

    rows = build_rows(merges, [rerun, done], {}, GLOBS)

    assert (rows[0].build_id, rows[0].minutes_to_deployed) == ("done", 4.0)


def test_P6_revision_of_a_digest_is_the_first_one_made_from_it():
    found = [  # newest first, as gcloud lists them
        Revision("api-staging-00003", "sha256:bbb", "2026-10-31T18:00:00Z"),  # min-instances
        Revision("api-staging-00002", "sha256:bbb", "2026-10-31T17:04:00Z"),  # the deploy
        Revision("api-staging-00001", "sha256:aaa", "2026-10-31T16:03:00Z"),
    ]

    by_digest = first_revision_of_digest(found)

    assert by_digest["sha256:bbb"] == ("api-staging-00002", "2026-10-31T17:04:00Z")
    assert by_digest["sha256:aaa"][0] == "api-staging-00001"


def test_P6_median_of_an_even_count_is_the_mean_of_the_middle_two():
    merges = [merge(i, f"2026-10-31T1{i}:00:00Z", c, ["infra/x"]) for i, c in enumerate("abcd")]
    finishes = ["10:03:00", "11:04:00", "12:05:00", "13:09:00"]
    builds = [build(c, f"2026-10-31T{t}Z") for c, t in zip("abcd", finishes, strict=True)]

    result = summary(build_rows(merges, builds, {}, GLOBS), None, builds)

    assert result["minutes_median"] == 4.5  # (4 + 5) / 2, not the upper middle 5
