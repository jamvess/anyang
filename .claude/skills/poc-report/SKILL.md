---
name: poc-report
description: Write the one-page report for a Proof of Concept from its spec and results. Use when a PoC run is finished.
argument-hint: [PoC id, e.g. P1]
---

Write `specs/poc/reports/$0.md` using `specs/poc/_REPORT_TEMPLATE.md`.

1. Read the PoC spec in `specs/poc/README.md` (section $0) and the results in `evals/` or the paths the user gives.
2. Report numbers exactly as measured, with sample size. Compare each metric to its pass criterion and mark PASS / FAIL.
3. State the decision (keep the plan, switch to the fallback, or change the design) and which spec files must be updated as a result. Propose the exact edits to `config/learning.yaml` or `specs/` but do not apply them without approval.
4. Keep it to one page.
