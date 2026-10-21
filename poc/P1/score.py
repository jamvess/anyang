"""PoC P1 step 2 · score the transcriptions against May's labels (evals/handwriting).

    cd apps/api
    uv run --with "antlr4-python3-runtime==4.11.*" python ../../poc/P1/score.py \
        --model gemini:gemini-3.5-flash --model gemini:gemini-3.5-flash-lite

Targets from specs/poc/README.md P1: line accuracy >= 80% for a model, and a confidence
threshold that flags >= 95% of misread lines. The chosen threshold is the lowest one that
reaches the target, so users confirm as few lines as possible (AM-02). Only labeled rows
(`labeled_by` set) are scored. Writes results/<model>/score.json (no image content).
"""

import argparse
import csv
import json
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from lines import align

HERE = Path(__file__).parent
REPO = HERE.parents[1]
LABELS = REPO / "evals" / "handwriting" / "labels.jsonl"
PHOTOS = REPO / "evals" / "handwriting" / "photos.csv"
OUT = HERE / "out"
RESULTS = HERE / "results"

TARGET_LINE_ACCURACY = 0.8  # specs/poc/README.md P1
TARGET_RECALL_WRONG = 0.95  # specs/poc/README.md P1
THRESHOLDS = [round(0.5 + 0.05 * k, 2) for k in range(10)]  # 0.50 .. 0.95


@dataclass(frozen=True)
class ConfidencePoint:
    confidence: float
    wrong: bool


@dataclass(frozen=True)
class ImageScore:
    correct: int
    label_lines: int
    points: list[ConfidencePoint]


def score_image(predicted: list[dict], label: list[str], unclear: list[int]) -> ImageScore:
    """unclear holds 1-based label line numbers that are not scored (evals/README.md rule 7)."""
    truth = [text for n, text in enumerate(label, start=1) if n not in set(unclear)]
    result = align([p["latex"] for p in predicted], truth)
    wrong = set(result.predicted_wrong)
    points = [ConfidencePoint(p["confidence"], i in wrong) for i, p in enumerate(predicted)]
    return ImageScore(correct=result.correct, label_lines=len(truth), points=points)


def pr_at(points: list[ConfidencePoint], threshold: float) -> dict:
    """Flag lines with confidence < threshold; how many misread lines does that catch?"""
    flagged = [p for p in points if p.confidence < threshold]
    wrong = [p for p in points if p.wrong]
    caught = [p for p in flagged if p.wrong]
    return {
        "threshold": threshold,
        "recall_wrong": round(len(caught) / len(wrong), 3) if wrong else None,
        "precision_wrong": round(len(caught) / len(flagged), 3) if flagged else None,
        "flag_rate": round(len(flagged) / len(points), 3) if points else None,
    }


def choose_threshold(
    points: list[ConfidencePoint], thresholds: list[float], target: float
) -> float | None:
    for threshold in sorted(thresholds):
        recall = pr_at(points, threshold)["recall_wrong"]
        if recall is not None and recall >= target:
            return threshold
    return None


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def score_model(model: str) -> dict:
    name = model.partition(":")[2]
    photos = {row["id"]: row for row in csv.DictReader(PHOTOS.open(encoding="utf-8"))}
    labeled = [e for e in load_jsonl(LABELS) if e.get("labeled_by") and e["lines"]]
    per_group: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    points: list[ConfidencePoint] = []
    latency, tokens_in, tokens_out, missing, images = [], [], [], [], []
    for entry in labeled:
        path = OUT / name / f"{entry['id']}.json"
        if not path.exists():
            missing.append(entry["id"])
            continue
        answer = json.loads(path.read_text(encoding="utf-8"))
        score = score_image(answer["lines"], entry["lines"], entry.get("unclear_lines", []))
        points += score.points
        latency.append(answer["latency_ms"])
        tokens_in.append(answer["tokens_in"])
        tokens_out.append(answer["tokens_out"])
        photo = photos.get(entry["id"], {})
        for group in (
            "all",
            f"medium:{photo.get('medium') or 'paper'}",
            f"writer:{entry['writer']}",
        ):
            per_group[group][0] += score.correct
            per_group[group][1] += score.label_lines
        images.append({"id": entry["id"], "correct": score.correct, "lines": score.label_lines})

    def ratio(pair: list[int]) -> float | None:
        return round(pair[0] / pair[1], 3) if pair[1] else None

    accuracy = ratio(per_group["all"])
    chosen = choose_threshold(points, THRESHOLDS, TARGET_RECALL_WRONG)
    return {
        "model": model,
        "images_scored": len(images),
        "images_missing": missing,
        "label_lines": per_group["all"][1],
        "line_accuracy": accuracy,
        "line_accuracy_pass": accuracy is not None and accuracy >= TARGET_LINE_ACCURACY,
        "by_group": {g: ratio(v) for g, v in sorted(per_group.items()) if g != "all"},
        "predicted_lines": len(points),
        "misread_lines": sum(p.wrong for p in points),
        "pr_curve": [pr_at(points, t) for t in THRESHOLDS],
        "chosen_threshold": chosen,
        "threshold_pass": chosen is not None,
        "latency_ms": {
            "mean": round(statistics.mean(latency)) if latency else None,
            "p95": round(sorted(latency)[int(0.95 * (len(latency) - 1))]) if latency else None,
        },
        "tokens_per_image": {
            "in": round(statistics.mean(tokens_in)) if tokens_in else None,
            "out": round(statistics.mean(tokens_out)) if tokens_out else None,
        },
        "images": images,
    }


def main(models: list[str]) -> None:
    for model in models:
        result = score_model(model)
        folder = RESULTS / model.partition(":")[2]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "score.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        summary = {k: v for k, v in result.items() if k not in ("images", "pr_curve")}
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", action="append", required=True)
    main(parser.parse_args().model)
