"""PoC P4-lite: cost per tutor message from the gateway's call log (AI-04, ai-calls-log.md).

    cd apps/api
    AI_PROVIDER=live AUTH_REQUIRED=false uv run fastapi run app/main.py 2> api.log   # terminal 1
    uv run python ../../poc/P4-lite/ttft.py --base http://127.0.0.1:8000 --n 50 --label <label>
    uv run python ../../poc/P4-lite/cost.py api.log --label <label>

Reads the JSON lines of the ``app.ai.calls`` logger (one per AI call, app/db/ai_calls.py), keeps
``tutor_reply`` and prices them. ``tokens_out`` already counts thinking tokens, which Google bills
as output (app/ai/providers/gemini.py). Writes poc/P4-lite/results/<label>-cost.json.

Prices are list prices, so the result is an estimate; check it against Cloud Billing (SKU).
The session figure counts ``tutor_reply`` only; the full turn design has 2-4 AI calls per turn
(ai-orchestration.md §2.2), so it is a lower bound of the NFR-P2 session cost.
"""

import argparse
import json
import os
import statistics
from dataclasses import dataclass
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
# Calls that reached the user as a reply; other statuses are billed too, reported apart.
REPLY_STATUSES = {"ok", "schema_retry"}

# Vertex AI list price of gemini-3.5-flash, global endpoint, USD per 1M tokens, seen 2026-11-01:
# input from the Vertex pricing table (docs.cloud.google.com/vertex-ai/generative-ai/pricing);
# output (thinking included) from the CodeMender / AlphaEvolve tables on the same page, not yet
# confirmed in the main table. Override with --input-usd / --output-usd.
INPUT_USD_PER_M = 1.50
OUTPUT_USD_PER_M = 9.00
THB_PER_USD = 33.0  # rounded from 32.65-33.78 (Jul-Aug 2026); no reliable rate for 1 Nov
# Pass criterion of the session budget: config/ai.yaml targets.cost_per_session_thb.
MESSAGES_PER_SESSION = 45  # assumption: one tutor message a minute in a 45-minute session


@dataclass(frozen=True)
class Call:
    purpose: str
    model: str
    status: str
    tokens_in: int
    tokens_out: int
    latency_ms: int


def parse_log(lines: list[str]) -> list[Call]:
    """``app.ai.calls`` entries of a JSON-lines log; other lines (uvicorn, warnings) are skipped."""
    calls = []
    for line in lines:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, dict) or entry.get("logger") != "app.ai.calls":
            continue
        try:
            row = json.loads(entry["message"])
        except (json.JSONDecodeError, TypeError):
            continue  # same logger, plain text: "ai_calls insert failed (...)" warnings
        if not isinstance(row, dict) or "purpose" not in row:
            continue
        calls.append(
            Call(
                purpose=row["purpose"],
                model=row["model"],
                status=row["status"],
                tokens_in=row["tokens_in"] or 0,
                tokens_out=row["tokens_out"] or 0,
                latency_ms=row["latency_ms"] or 0,
            )
        )
    return calls


def usd(call: Call, input_usd_per_m: float, output_usd_per_m: float) -> float:
    return (call.tokens_in * input_usd_per_m + call.tokens_out * output_usd_per_m) / 1_000_000


def summary(
    calls: list[Call],
    input_usd_per_m: float = INPUT_USD_PER_M,
    output_usd_per_m: float = OUTPUT_USD_PER_M,
    thb_per_usd: float = THB_PER_USD,
    messages_per_session: int = MESSAGES_PER_SESSION,
    target_thb: float | None = None,
) -> dict:
    tutor = [c for c in calls if c.purpose == "tutor_reply"]
    replies = [c for c in tutor if c.status in REPLY_STATUSES]
    failed = [c for c in tutor if c.status not in REPLY_STATUSES]
    if not replies:
        raise ValueError("no successful tutor_reply calls in the log")
    costs = [usd(c, input_usd_per_m, output_usd_per_m) for c in replies]
    mean_usd = statistics.mean(costs)
    session_thb = mean_usd * messages_per_session * thb_per_usd
    return {
        "messages": len(replies),
        "models": sorted({c.model for c in replies}),
        "tokens_in": {"mean": statistics.mean(c.tokens_in for c in replies)},
        "tokens_out": {
            "mean": statistics.mean(c.tokens_out for c in replies),
            "median": statistics.median(c.tokens_out for c in replies),
            "max": max(c.tokens_out for c in replies),
        },
        "usd_per_message": {"mean": round(mean_usd, 6), "max": round(max(costs), 6)},
        "thb_per_message": round(mean_usd * thb_per_usd, 4),
        # Failed or stopped streams still use (and bill) tokens; not in the per-message mean.
        "failed_calls": {
            "count": len(failed),
            "usd": round(sum(usd(c, input_usd_per_m, output_usd_per_m) for c in failed), 6),
        },
        "session": {
            "counts": "tutor_reply only (lower bound: the full turn has 2-4 AI calls)",
            "messages_per_session": messages_per_session,
            "thb": round(session_thb, 2),
            "target_thb": target_thb,
            "within_target": None if target_thb is None else session_thb <= target_thb,
        },
        "prices": {
            "input_usd_per_m": input_usd_per_m,
            "output_usd_per_m": output_usd_per_m,
            "thb_per_usd": thb_per_usd,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("log", type=Path, help="stderr of the API run (JSON lines)")
    parser.add_argument("--label", required=True)
    parser.add_argument("--input-usd", type=float, default=INPUT_USD_PER_M)
    parser.add_argument("--output-usd", type=float, default=OUTPUT_USD_PER_M)
    parser.add_argument("--thb-per-usd", type=float, default=THB_PER_USD)
    parser.add_argument("--messages-per-session", type=int, default=MESSAGES_PER_SESSION)
    args = parser.parse_args()

    # The same config folder as the API run (CONFIG_DIR), read directly: no env validation needed.
    config_dir = Path(os.environ.get("CONFIG_DIR") or REPO / "config")
    ai = yaml.safe_load((config_dir / "ai.yaml").read_text(encoding="utf-8"))
    target = ai["targets"]["cost_per_session_thb"]
    calls = parse_log(args.log.read_text(encoding="utf-8").splitlines())
    result = summary(
        calls, args.input_usd, args.output_usd, args.thb_per_usd, args.messages_per_session, target
    )
    out = HERE / "results" / f"{args.label}-cost.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"wrote {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
