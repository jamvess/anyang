"""Tests for the check_answer scorer in run_eval.py (evals/README.md "การให้คะแนน",
specs/poc/README.md P2, ai-orchestration.md §2.4.8).

    uv run --project apps/api pytest evals/test_run_eval.py

The scorer only reads labels and predictions. It never calls a checker or an AI provider.
"""

import json
from pathlib import Path

import pytest
from run_eval import main, score


def label(id_, verdict, error_type, first_wrong_line):
    return {
        "id": id_,
        "verdict": verdict,
        "error_type": error_type,
        "first_wrong_line": first_wrong_line,
    }


def prediction(id_, verdict, error_type, first_wrong_line):
    return label(id_, verdict, error_type, first_wrong_line)


# The three examples of evals/README.md plus one correct answer.
LABELS = [
    label("ans_001", "incorrect", "sign", 1),
    label("ans_002", "incomplete", "concept", None),
    label("ans_003", "incorrect", "wrong_method", 1),
    label("ans_004", "correct", None, None),
]


def perfect():
    return [dict(row) for row in LABELS]


def write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


# --- verdict · AM-04 ----------------------------------------------------------------------


def test_AM04_eval_verdict_must_match_all_four_values_over_every_item():
    preds = perfect()
    preds[1] = prediction("ans_002", "incorrect", "concept", None)  # incomplete → incorrect

    result = score(LABELS, preds)

    assert result["verdict"]["matched"] == 3
    assert result["verdict"]["total"] == 4
    assert result["verdict"]["accuracy"] == pytest.approx(0.75)


def test_AM04_eval_binary_verdict_only_asks_counted_as_correct_or_wrong():
    preds = perfect()
    preds[1] = prediction("ans_002", "incorrect", "concept", None)  # both count as wrong
    preds[3] = prediction("ans_004", "correct_with_flaw", "sign", 1)  # correct → wrong

    result = score(LABELS, preds)

    assert result["verdict_binary"]["matched"] == 3
    assert result["verdict_binary"]["total"] == 4


def test_AM04_eval_binary_verdict_is_not_a_target():
    result = score(LABELS, perfect())

    assert "target" not in result["verdict_binary"]
    assert "passed" not in result["verdict_binary"]


# --- error_type · AM-06 -------------------------------------------------------------------


def test_AM06_eval_error_type_counts_only_items_whose_label_is_not_correct():
    preds = perfect()
    preds[3] = prediction("ans_004", "correct", "sign", None)  # label is correct: not counted

    result = score(LABELS, preds)

    assert result["error_type"]["total"] == 3
    assert result["error_type"]["matched"] == 3


def test_AM06_eval_missing_error_type_counts_as_mismatch():
    preds = perfect()
    preds[0] = prediction("ans_001", "incorrect", None, 1)

    result = score(LABELS, preds)

    assert result["error_type"]["matched"] == 2
    assert result["error_type"]["total"] == 3


def test_AM06_eval_wrong_error_type_counts_as_mismatch():
    preds = perfect()
    preds[0] = prediction("ans_001", "incorrect", "calculation", 1)

    result = score(LABELS, preds)

    assert result["error_type"]["matched"] == 2


# --- first_wrong_line · AM-05 -------------------------------------------------------------


def test_AM05_eval_first_wrong_line_counts_only_items_whose_label_has_a_line():
    preds = perfect()
    preds[0] = prediction("ans_001", "incorrect", "sign", 2)  # label says 1

    result = score(LABELS, preds)

    assert result["first_wrong_line"]["total"] == 2
    assert result["first_wrong_line"]["matched"] == 1


def test_AM05_eval_null_matching_null_is_not_counted():
    result = score(LABELS, perfect())

    # ans_002 and ans_004 are null in both label and prediction, and stay out of the total.
    assert result["first_wrong_line"]["total"] == 2


def test_AM05_eval_null_prediction_for_a_labeled_line_counts_as_mismatch():
    preds = perfect()
    preds[2] = prediction("ans_003", "incorrect", "wrong_method", None)

    result = score(LABELS, preds)

    assert result["first_wrong_line"]["matched"] == 1


# --- missing and bad predictions ----------------------------------------------------------


def test_AM04_eval_missing_prediction_counts_as_mismatch_in_every_metric_it_belongs_to():
    preds = [row for row in perfect() if row["id"] != "ans_003"]

    result = score(LABELS, preds)

    assert result["missing"] == ["ans_003"]
    assert (result["verdict"]["matched"], result["verdict"]["total"]) == (3, 4)
    assert (result["error_type"]["matched"], result["error_type"]["total"]) == (2, 3)
    assert (result["first_wrong_line"]["matched"], result["first_wrong_line"]["total"]) == (1, 2)


def test_AM04_eval_prediction_with_unknown_id_is_an_error():
    preds = [*perfect(), prediction("ans_999", "correct", None, None)]

    with pytest.raises(ValueError, match="ans_999"):
        score(LABELS, preds)


def test_AM04_eval_duplicate_prediction_id_is_an_error():
    preds = [*perfect(), prediction("ans_001", "correct", None, None)]

    with pytest.raises(ValueError, match="ans_001"):
        score(LABELS, preds)


def test_AM04_eval_extra_prediction_fields_are_ignored():
    preds = perfect()
    for row in preds:
        row.update({"evidence": "…", "method": "doc", "decided_by": "sympy", "confidence": 0.9})

    result = score(LABELS, preds)

    assert result["verdict"]["matched"] == 4


# --- targets (specs/poc/README.md P2) -----------------------------------------------------


def test_AM04_eval_targets_come_from_the_p2_spec():
    result = score(LABELS, perfect())

    assert result["verdict"]["target"] == pytest.approx(0.95)
    assert result["error_type"]["target"] == pytest.approx(0.80)
    assert result["first_wrong_line"]["target"] == pytest.approx(0.85)


def test_AM04_eval_accuracy_exactly_at_target_passes():
    labels = [label(f"ans_{i:03}", "incorrect", "sign", 1) for i in range(20)]
    preds = [dict(row) for row in labels]
    preds[0] = prediction("ans_000", "correct", None, None)  # 19/20 = 95% verdict
    preds[1]["error_type"] = "calculation"
    preds[2]["error_type"] = "calculation"
    preds[3]["error_type"] = "calculation"  # 16/20 = 80% error_type
    preds[4]["first_wrong_line"] = 2
    preds[5]["first_wrong_line"] = 2  # 17/20 = 85% first_wrong_line

    result = score(labels, preds)

    assert result["verdict"]["passed"]
    assert result["error_type"]["passed"]
    assert result["first_wrong_line"]["passed"]
    assert result["passed"]


def test_AM04_eval_one_metric_below_target_fails_the_run():
    labels = [label(f"ans_{i:03}", "incorrect", "sign", 1) for i in range(20)]
    preds = [dict(row) for row in labels]
    preds[0] = prediction("ans_000", "correct", None, None)
    preds[1] = prediction("ans_001", "correct", None, None)  # 18/20 = 90% verdict

    result = score(labels, preds)

    assert not result["verdict"]["passed"]
    assert result["error_type"]["passed"]
    assert not result["passed"]


# --- command line (ai-orchestration.md §2.11: CI runs evals when a prompt changes) --------


def run_main(tmp_path: Path, preds: list[dict]) -> int:
    labels = write_jsonl(tmp_path / "labels.jsonl", LABELS)
    predictions = write_jsonl(tmp_path / "predictions.jsonl", preds)
    return main(
        [
            "--purpose",
            "check_answer",
            "--prompt",
            "v1",
            "--labels",
            str(labels),
            "--predictions",
            str(predictions),
            "--out",
            str(tmp_path / "results"),
        ]
    )


def test_ai_orchestration_2_11_eval_exit_code_is_0_when_every_target_passes(tmp_path):
    assert run_main(tmp_path, perfect()) == 0


def test_ai_orchestration_2_11_eval_exit_code_is_1_when_a_target_fails(tmp_path):
    preds = perfect()
    preds[0] = prediction("ans_001", "correct", None, None)

    assert run_main(tmp_path, preds) == 1


def test_ai_orchestration_2_11_eval_writes_the_score_to_results_named_by_prompt(tmp_path):
    run_main(tmp_path, perfect())

    written = json.loads((tmp_path / "results" / "v1.json").read_text(encoding="utf-8"))
    assert written["purpose"] == "check_answer"
    assert written["prompt"] == "v1"
    assert written["verdict"]["matched"] == 4
    assert written["passed"] is True


def test_ai_orchestration_2_11_eval_only_check_answer_is_supported(tmp_path):
    with pytest.raises(SystemExit):
        main(["--purpose", "extract_answer", "--prompt", "v1", "--predictions", "x.jsonl"])
