---
name: implement-feature
description: Implement a feature until its reviewed tests pass, following CLAUDE.md architecture rules. Use only after /spec-to-tests and human review of the tests.
argument-hint: [path to feature spec]
---

Implement the feature in `$ARGUMENTS`.

1. Re-read the spec, the root `CLAUDE.md` and the app-level `CLAUDE.md`.
2. Do not modify the reviewed tests. If a test seems wrong, stop and explain why instead of changing it.
3. Implement in small steps; run the relevant tests after each step (red → green). Count the red → green cycles.
4. Respect the architecture rules: pure logic in `app/domain/`, AI only through `ai.call`, thresholds from config, `tenant_id` + RLS on new tables, SSE event names from `specs/system/api.md`.
5. When all tests pass, refactor for clarity, run lint and the full test suite.
6. Write the PR description using `.github/pull_request_template.md`, including the requirement IDs, the number of red → green cycles, and anything in the spec that turned out to be ambiguous.
