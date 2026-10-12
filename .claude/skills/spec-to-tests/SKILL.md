---
name: spec-to-tests
description: Generate failing tests from the acceptance criteria of a feature spec. Use after the spec is approved and before implementation.
argument-hint: [path to feature spec]
---

Generate tests for the feature spec `$ARGUMENTS`.

1. Read the spec. Every acceptance criterion becomes at least one test; boundary cases become parametrized rows.
2. Backend tests go in `apps/api/tests/unit/` (pure domain logic) or `apps/api/tests/integration/` (API + DB). Frontend tests go next to the component as `*.test.tsx`.
3. Name each test with the requirement ID first, e.g. `test_SM03_three_stars_when_r_at_least_threshold`.
4. Use the fake AI provider and fixtures; tests must not call real models or the network.
5. Read thresholds from the test `LearningConfig` fixture, never hard-code them; assert behavior at the boundary using values from the config.
6. Run the tests and confirm they FAIL for the right reason (missing implementation, not syntax errors).
7. Stop. Print a table: criterion → test name → file. Wait for the human to review the tests before any implementation.
