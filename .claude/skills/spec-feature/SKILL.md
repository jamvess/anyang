---
name: spec-feature
description: Draft a feature spec from requirement IDs and the system specs, using specs/features/_TEMPLATE.md. Use before any new feature is implemented.
argument-hint: [area/feature-name] [requirement IDs...]
---

Draft the feature spec `specs/features/$0.md` for requirements: $ARGUMENTS

1. Read `specs/features/_TEMPLATE.md`, `specs/requirements/requirements.md` (the listed IDs), and the relevant parts of `specs/system/` (ai-orchestration.md, learning-model.md, api.md, data-model.md). Read `config/learning.yaml` if the feature uses thresholds.
2. Fill every section of the template. Acceptance criteria are Given/When/Then, each tagged with a requirement ID, each testable without a real AI model.
3. Include at least: one happy path, every branch in the relevant flow, boundary values for every threshold used (value − ε, value, value + ε), and the tenant-isolation case if data is read or written.
4. List data changes (tables/columns) and API changes (endpoints, SSE events) exactly; if they are not in `specs/system/`, flag them under "Spec changes needed".
5. Do NOT write code. Do NOT invent behavior: anything not supported by the system specs goes under "Open questions".
6. End by printing the open questions for the human reviewer.
