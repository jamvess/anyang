"""PoC P6-lite: does a merge to main update api-staging by itself within 10 minutes?

    cd apps/api && uv run python ../../poc/P6-lite/deploy_latency.py

For every PR merged into main after the Cloud Build trigger was created:
  - should it deploy? Yes when one of its files matches the trigger's ``includedFiles``
    (infra/trigger-api-staging.yaml).
  - the build of its merge commit (``gcloud builds list``), its status, and minutes from the
    merge to the end of the build (the last step is ``gcloud run deploy``, so the new revision
    serves traffic by then).
  - the Cloud Run revision made from the image digest of that build, and when it was created.
Then: does api-staging serve the newest commit that should have deployed?

Needs ``gh`` (logged in) and ``gcloud`` (logged in, project anyang-513006). Read only.
Writes poc/P6-lite/results/deploy-latency.json.
"""

import json
import shutil
import statistics
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from fnmatch import fnmatchcase
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
TRIGGER_FILE = REPO / "infra" / "trigger-api-staging.yaml"
RESULTS = HERE / "results" / "deploy-latency.json"

REGION = "asia-southeast1"
SERVICE = "api-staging"
TARGET_MINUTES = 10.0  # pass criterion of P6-lite (specs/poc/README.md)


@dataclass(frozen=True)
class Merge:
    number: int
    title: str
    merged_at: str
    commit: str
    files: list[str]


@dataclass(frozen=True)
class Build:
    id: str
    commit: str
    status: str
    create_time: str
    finish_time: str | None
    digest: str | None


@dataclass(frozen=True)
class Row:
    pr: int
    title: str
    commit: str
    merged_at: str
    should_deploy: bool
    build_id: str | None
    build_status: str | None
    minutes_to_deployed: float | None
    revision: str | None
    revision_created_at: str | None
    within_target: bool | None


def parse_time(value: str) -> datetime:
    """RFC 3339 from gh and gcloud, with or without fractions (Python 3.12 reads both)."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def minutes_between(start: str, end: str) -> float:
    return round((parse_time(end) - parse_time(start)).total_seconds() / 60, 2)


def matches_trigger(files: list[str], globs: list[str]) -> bool:
    """Cloud Build ``includedFiles`` globs. Right for the ``<folder>/**`` globs the trigger uses;
    ``fnmatch`` lets ``*`` cross ``/``, so a single-level glob such as ``infra/*.yaml`` would match
    more than Cloud Build does."""
    return any(fnmatchcase(path, glob) for path in files for glob in globs)


def deploy_of_commit(builds: list[Build]) -> dict[str, Build]:
    """The build that counts for each commit: the first one that succeeded (that is when staging
    changed), otherwise the newest one (so a failed or running build shows up)."""
    chosen: dict[str, Build] = {}
    for build in sorted(builds, key=lambda b: parse_time(b.create_time)):
        current = chosen.get(build.commit)
        if current is None or current.status != "SUCCESS":
            chosen[build.commit] = build
    return chosen


def build_rows(
    merges: list[Merge],
    builds: list[Build],
    revisions: dict[str, tuple[str, str]],
    globs: list[str],
) -> list[Row]:
    """One row per merge. ``revisions`` maps an image digest to (revision name, created time)."""
    by_commit = deploy_of_commit(builds)
    rows = []
    for merge in sorted(merges, key=lambda m: m.merged_at):
        build = by_commit.get(merge.commit)
        minutes = None
        if build is not None and build.status == "SUCCESS" and build.finish_time:
            minutes = minutes_between(merge.merged_at, build.finish_time)
        revision = revisions.get(build.digest) if build and build.digest else None
        should_deploy = matches_trigger(merge.files, globs)
        rows.append(
            Row(
                pr=merge.number,
                title=merge.title,
                commit=merge.commit[:7],
                merged_at=merge.merged_at,
                should_deploy=should_deploy,
                build_id=build.id if build else None,
                build_status=build.status if build else None,
                minutes_to_deployed=minutes,
                revision=revision[0] if revision else None,
                revision_created_at=revision[1] if revision else None,
                within_target=(minutes is not None and minutes <= TARGET_MINUTES)
                if should_deploy
                else None,
            )
        )
    return rows


def summary(rows: list[Row], serving_digest: str | None, builds: list[Build]) -> dict:
    deploys = [r for r in rows if r.should_deploy]
    minutes = sorted(r.minutes_to_deployed for r in deploys if r.minutes_to_deployed is not None)
    newest = deploys[-1] if deploys else None
    newest_build = next((b for b in builds if newest and b.id == newest.build_id), None)
    return {
        "target_minutes": TARGET_MINUTES,
        "merges": len(rows),
        "merges_that_should_deploy": len(deploys),
        "deployed_by_trigger": len(minutes),
        "within_target": sum(1 for r in deploys if r.within_target),
        "missed_or_failed": [r.pr for r in deploys if r.minutes_to_deployed is None],
        "deployed_without_matching_files": [
            r.pr for r in rows if not r.should_deploy and r.build_id is not None
        ],
        "minutes_min": minutes[0] if minutes else None,
        "minutes_median": round(statistics.median(minutes), 2) if minutes else None,
        "minutes_max": minutes[-1] if minutes else None,
        "serving_newest_deploy": bool(
            newest_build and serving_digest and newest_build.digest == serving_digest
        ),
        "newest_deploy_pr": newest.pr if newest else None,
    }


# --- data from gh and gcloud ----------------------------------------------------------------


def _run_json(*args: str) -> object:
    exe = shutil.which(args[0])  # gcloud is gcloud.cmd on Windows
    if exe is None:
        sys.exit(f"{args[0]} not found on PATH")
    out = subprocess.run([exe, *args[1:]], check=True, capture_output=True, encoding="utf-8").stdout
    return json.loads(out)


def trigger() -> tuple[str, str, list[str]]:
    """(trigger id, create time, includedFiles) of the deployed trigger."""
    name = yaml.safe_load(TRIGGER_FILE.read_text(encoding="utf-8"))["name"]
    data = _run_json(
        "gcloud", "builds", "triggers", "describe", name, f"--region={REGION}", "--format=json"
    )
    return data["id"], data["createTime"], data.get("includedFiles", [])


def merges_since(since: str) -> list[Merge]:
    data = _run_json(
        "gh", "pr", "list", "--state", "merged", "--base", "main", "--limit", "200",
        "--json", "number,title,mergedAt,mergeCommit,files",
    )  # fmt: skip
    return [
        Merge(
            number=pr["number"],
            title=pr["title"],
            merged_at=pr["mergedAt"],
            commit=pr["mergeCommit"]["oid"],
            files=[f["path"] for f in pr["files"]],
        )
        for pr in data
        if parse_time(pr["mergedAt"]) >= parse_time(since)
    ]


def trigger_builds(trigger_id: str) -> list[Build]:
    data = _run_json(
        "gcloud", "builds", "list", f"--region={REGION}", "--limit=500", "--format=json",
        f"--filter=buildTriggerId={trigger_id}",
    )  # fmt: skip
    builds = []
    for b in data:
        images = (b.get("results") or {}).get("images") or []
        builds.append(
            Build(
                id=b["id"],
                commit=b.get("substitutions", {}).get("COMMIT_SHA", ""),
                status=b["status"],
                create_time=b["createTime"],
                finish_time=b.get("finishTime"),
                digest=images[0]["digest"] if images else None,
            )
        )
    return builds


def _digest(image: str) -> str | None:
    return image.split("@", 1)[1] if "@" in image else None


@dataclass(frozen=True)
class Revision:
    name: str
    digest: str | None
    created_at: str


def revisions() -> list[Revision]:
    """Revisions of api-staging, newest first (as gcloud lists them)."""
    data = _run_json(
        "gcloud", "run", "revisions", "list", f"--service={SERVICE}", f"--region={REGION}",
        "--format=json",
    )  # fmt: skip
    return [
        Revision(
            name=r["metadata"]["name"],
            digest=_digest(r["spec"]["containers"][0]["image"]),
            created_at=r["metadata"]["creationTimestamp"],
        )
        for r in data
    ]


def first_revision_of_digest(found: list[Revision]) -> dict[str, tuple[str, str]]:
    """Image digest -> (name, created time) of the first revision made from it, i.e. the deploy.
    Later revisions of the same image (for example ``services update --min-instances``) are
    settings changes, not deploys."""
    by_digest: dict[str, tuple[str, str]] = {}
    for revision in sorted(found, key=lambda r: parse_time(r.created_at)):
        if revision.digest and revision.digest not in by_digest:
            by_digest[revision.digest] = (revision.name, revision.created_at)
    return by_digest


def serving_digest(found: list[Revision]) -> str | None:
    """Image digest of the revision that takes traffic now."""
    data = _run_json(
        "gcloud", "run", "services", "describe", SERVICE, f"--region={REGION}", "--format=json"
    )
    serving = {t["revisionName"] for t in data["status"]["traffic"] if t.get("percent")}
    return next((r.digest for r in found if r.name in serving), None)


def main() -> None:
    trigger_id, created, globs = trigger()
    builds = trigger_builds(trigger_id)
    found = revisions()  # one snapshot for the rows and the summary
    rows = build_rows(merges_since(created), builds, first_revision_of_digest(found), globs)
    result = {
        "measured_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "trigger": {"id": trigger_id, "created": created, "included_files": globs},
        "summary": summary(rows, serving_digest(found), builds),
        "merges": [asdict(r) for r in rows],
    }
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, ensure_ascii=False))
    print(f"wrote {RESULTS.relative_to(REPO)}")


if __name__ == "__main__":
    main()
