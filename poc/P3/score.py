"""PoC P3 step 3 · compare the pipeline output with May's labels (evals/topics/mth10101).

    cd apps/api && uv run python ../../poc/P3/score.py [--model gemini-3.5-flash]

Targets from specs/poc/README.md P3: topics match >= 80%, three-star match >= 80%,
<= 3 minutes per file. Topics are paired by overlapping PDF pages (Jam's choice): the IoU of
the (file, page) sets, one-to-one, best pair first. Writes results/<model>/score.json and
score.md; unmatched topics are listed for Junior to check by eye.
"""

import argparse
import json
import re
from collections import defaultdict

from common import LABELS, OUT, RESULTS, read_json, write_json
from stars import Topic, stars

from app.settings import get_settings

MIN_IOU = 0.5  # Jam's choice; the report also shows the sensitivity below
IOU_SENSITIVITY = (0.3, 0.5, 0.7)
TARGET = 0.8  # specs/poc/README.md P3
TARGET_MINUTES_PER_FILE = 3

_RANGE = re.compile(r"^(.+):(\d+)-(\d+)$")


def page_set(ranges: list[str]) -> set[tuple[str, int]]:
    pages: set[tuple[str, int]] = set()
    for value in ranges:
        file, start, end = _RANGE.match(value).groups()  # type: ignore[union-attr]
        pages.update((file, p) for p in range(int(start), int(end) + 1))
    return pages


def iou(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


def match_topics(
    ai: dict[str, list[str]], label: dict[str, list[str]], min_iou: float
) -> dict[str, str]:
    """Label topic id -> AI topic id, each used at most once, highest IoU first."""
    ai_pages = {k: page_set(v) for k, v in ai.items()}
    label_pages = {k: page_set(v) for k, v in label.items()}
    candidates = sorted(
        (
            (iou(lp, ap), lid, aid)
            for lid, lp in label_pages.items()
            for aid, ap in ai_pages.items()
        ),
        key=lambda c: (-c[0], c[1], c[2]),
    )
    pairs: dict[str, str] = {}
    used: set[str] = set()
    for score, lid, aid in candidates:
        if score < min_iou:
            break
        if lid not in pairs and aid not in used:
            pairs[lid] = aid
            used.add(aid)
    return pairs


def three_star_match(human: dict[str, int], computed: dict[str, int | None]) -> dict:
    """Share of the label's three-star topics that also got three stars."""
    label3 = {t for t, s in human.items() if s == 3}
    hit = {t for t in label3 if computed.get(t) == 3}
    computed3 = {t for t, s in computed.items() if s == 3}
    return {
        "label_three_star": len(label3),
        "matched": len(hit),
        "recall": round(len(hit) / len(label3), 3) if label3 else None,
        "computed_three_star": len(computed3),
        "precision": round(len(hit) / len(computed3), 3) if computed3 else None,
        "exact_stars_agreement": round(
            sum(1 for t, s in human.items() if computed.get(t) == s) / len(human), 3
        ),
    }


def label_stars(labels: dict, cfg) -> dict[str, int]:
    """(a) The formula on May's own exam map: does the formula agree with people?"""
    exams = sorted({q.split(":")[0] for q in labels["question_map"]})
    weights = {e: cfg.weight_same_instructor for e in exams}
    appearances = {(m["topic"], q.split(":")[0]) for q, m in labels["question_map"].items()}
    topics = [Topic(t["id"], t["prereqs"], False, t["name"]) for t in labels["topics"]]
    return {tid: r.importance for tid, r in stars(topics, weights, appearances, cfg).items()}


def main(model: str) -> None:
    cfg = get_settings().learning.stars
    labels = read_json(LABELS)
    folder = RESULTS / model
    topics = read_json(folder / "topics.json")
    mapping = read_json(folder / "mapping.json")
    run = read_json(folder / "run.json")

    label_pages = {t["id"]: t["pages"] for t in labels["topics"]}
    ai_pages = {t["id"]: t["sources"] for t in topics}
    human = {t["id"]: t["stars_human"] for t in labels["topics"]}
    names = {t["id"]: t["name"] for t in labels["topics"]}
    ai_names = {t["id"]: t["name"] for t in topics}
    ai_stars = {t["id"]: t["stars"] for t in topics}

    sensitivity = {}
    for threshold in IOU_SENSITIVITY:
        pairs = match_topics(ai_pages, label_pages, threshold)
        sensitivity[str(threshold)] = {
            "recall": round(len(pairs) / len(label_pages), 3),
            "precision": round(len(pairs) / len(ai_pages), 3) if ai_pages else None,
        }
    pairs = match_topics(ai_pages, label_pages, MIN_IOU)
    to_label = {aid: lid for lid, aid in pairs.items()}

    pipeline = {lid: ai_stars.get(pairs[lid]) if lid in pairs else None for lid in human}
    formula_only = label_stars(labels, cfg)

    correct = wrong = missing = 0
    question_rows = []
    for q, truth in labels["question_map"].items():
        got = mapping.get(q)
        mapped = to_label.get(got["topic_id"]) if got and got["topic_id"] else None
        ok = mapped == truth["topic"]
        if got is None:
            missing += 1
        elif ok:
            correct += 1
        else:
            wrong += 1
        question_rows.append(
            {"q": q, "label": truth["topic"], "ai": got["topic_id"] if got else None, "ok": ok}
        )

    per_file = defaultdict(float)
    for row in run["calls"]:
        if row["file"]:
            per_file[row["file"]] += row["latency_ms"] / 1000
    shared = sum(r["latency_ms"] for r in run["calls"] if not r["file"]) / 1000
    files = sorted(per_file)
    # Shared calls (A6 merge, A7 per exam is per file) are spread evenly over the files.
    minutes = {f: round((per_file[f] + shared / len(files)) / 60, 2) for f in files}

    score = {
        "model": run["model"],
        "min_iou": MIN_IOU,
        "topics": {
            "label": len(label_pages),
            "ai": len(ai_pages),
            "matched": len(pairs),
            "recall": round(len(pairs) / len(label_pages), 3),
            "precision": round(len(pairs) / len(ai_pages), 3) if ai_pages else None,
            "iou_sensitivity": sensitivity,
            "pass": len(pairs) / len(label_pages) >= TARGET,
        },
        "three_star_formula_on_label_map": three_star_match(human, formula_only),
        "three_star_pipeline": three_star_match(human, pipeline),
        "questions": {
            "label": len(labels["question_map"]),
            "correct_topic": correct,
            "wrong_topic": wrong,
            "missing": missing,
            "accuracy": round(correct / len(labels["question_map"]), 3),
        },
        "minutes_per_file": minutes,
        "max_minutes_per_file": max(minutes.values()) if minutes else None,
        "tokens": {"in": run["tokens_in"], "out": run["tokens_out"]},
        "schema_retries": sum(r["schema_retries"] for r in run["calls"]),
        "unmatched_label_topics": [
            {"id": t, "name": names[t], "pages": label_pages[t]} for t in human if t not in pairs
        ],
        "unmatched_ai_topics": [
            {"id": a, "name": ai_names[a], "sources": ai_pages[a]}
            for a in ai_pages
            if a not in to_label
        ],
        "pairs": [
            {"label": lid, "label_name": names[lid], "ai": aid, "ai_name": ai_names[aid]}
            for lid, aid in pairs.items()
        ],
        "questions_detail": question_rows,
    }
    score["three_star_pipeline"]["pass"] = (score["three_star_pipeline"]["recall"] or 0) >= TARGET
    write_json(folder / "score.json", score)
    print(
        json.dumps(
            {k: v for k, v in score.items() if not k.endswith(("detail", "pairs"))},
            ensure_ascii=False,
            indent=2,
        )
    )
    print(f"wrote {folder / 'score.json'} (inputs from {OUT})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="", help="results folder; default: AI_MODEL_OVERRIDE")
    args = parser.parse_args()
    model = args.model or get_settings().env.ai_model_override.partition(":")[2]
    main(model)
