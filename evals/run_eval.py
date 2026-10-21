"""Score the answer checker against the golden set (evals/answers).

    uv run --project apps/api python evals/run_eval.py --purpose check_answer --prompt v1 \
        --predictions evals/answers/predictions/v1.jsonl

Metrics, denominators and the prediction format are defined in evals/README.md
("การให้คะแนน"). Targets from specs/poc/README.md P2 (ai-orchestration.md §2.4.8). The checker
itself is not called here yet: it needs the SymPy service (apps/api/app/math, P2), so this
script scores a predictions file. Writes evals/answers/results/<prompt>.json and exits 1 when a
target is missed, so CI can gate prompt and model changes (§2.11).
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
LABELS = HERE / "answers" / "labels.jsonl"
RESULTS = HERE / "answers" / "results"

TARGETS = {
    "verdict": 0.95,  # specs/poc/README.md P2
    "error_type": 0.80,  # specs/poc/README.md P2
    "first_wrong_line": 0.85,  # specs/poc/README.md P2
}
COUNTED_AS_CORRECT = "correct"  # evals/README.md verdict table: every other verdict is wrong


def load_jsonl(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def index_predictions(labels: list[dict], predictions: list[dict]) -> dict[str, dict]:
    known = {row["id"] for row in labels}
    by_id: dict[str, dict] = {}
    for row in predictions:
        id_ = row["id"]
        if id_ not in known:
            raise ValueError(f"prediction {id_} has no label")
        if id_ in by_id:
            raise ValueError(f"prediction {id_} appears more than once")
        by_id[id_] = row
    return by_id


def tally(matches: list[bool]) -> dict:
    total = len(matches)
    matched = sum(matches)
    return {"matched": matched, "total": total, "accuracy": matched / total if total else None}


def against_target(metric: str, matches: list[bool]) -> dict:
    counts = tally(matches)
    target = TARGETS[metric]
    passed = counts["accuracy"] is not None and counts["accuracy"] >= target
    return {**counts, "target": target, "passed": passed}


def score(labels: list[dict], predictions: list[dict]) -> dict:
    by_id = index_predictions(labels, predictions)
    verdict, verdict_binary, error_type, first_wrong_line = [], [], [], []

    for label in labels:
        pred = by_id.get(label["id"])
        found = pred is not None

        verdict.append(found and pred["verdict"] == label["verdict"])
        verdict_binary.append(
            found
            and (pred["verdict"] == COUNTED_AS_CORRECT) == (label["verdict"] == COUNTED_AS_CORRECT)
        )
        if label["verdict"] != COUNTED_AS_CORRECT:
            predicted = pred.get("error_type") if found else None
            error_type.append(predicted is not None and predicted == label["error_type"])
        if label["first_wrong_line"] is not None:
            predicted = pred.get("first_wrong_line") if found else None
            first_wrong_line.append(predicted == label["first_wrong_line"])

    result = {
        "n": len(labels),
        "missing": [label["id"] for label in labels if label["id"] not in by_id],
        "verdict": against_target("verdict", verdict),
        "verdict_binary": tally(verdict_binary),
        "error_type": against_target("error_type", error_type),
        "first_wrong_line": against_target("first_wrong_line", first_wrong_line),
    }
    result["passed"] = all(result[metric]["passed"] for metric in TARGETS)
    return result


def describe(name: str, metric: dict) -> str:
    accuracy = "n/a" if metric["accuracy"] is None else f"{metric['accuracy']:.1%}"
    line = f"{name:<17} {metric['matched']}/{metric['total']} = {accuracy}"
    if "target" in metric:
        line += f"  target >= {metric['target']:.0%}  {'PASS' if metric['passed'] else 'FAIL'}"
    return line


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--purpose", required=True, choices=["check_answer"])
    parser.add_argument("--prompt", required=True, help="prompt version, e.g. v1")
    parser.add_argument("--predictions", required=True, type=Path, help="checker output JSONL")
    parser.add_argument("--labels", type=Path, default=LABELS)
    parser.add_argument("--out", type=Path, default=RESULTS)
    args = parser.parse_args(argv)

    result = score(load_jsonl(args.labels), load_jsonl(args.predictions))

    args.out.mkdir(parents=True, exist_ok=True)
    written = {"purpose": args.purpose, "prompt": args.prompt, **result}
    (args.out / f"{args.prompt}.json").write_text(
        json.dumps(written, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"{args.purpose} {args.prompt} - {result['n']} answers")
    for metric in ["verdict", "verdict_binary", "error_type", "first_wrong_line"]:
        print(describe(metric, result[metric]))
    if result["missing"]:
        print(f"missing predictions: {', '.join(result['missing'])}")
    print("PASS" if result["passed"] else "FAIL")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
