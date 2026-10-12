## What

<!-- One or two sentences. -->

## Spec and requirements

- Feature / PoC spec: `specs/...`
- Requirement IDs: <!-- e.g. TM-05, AM-04 -->

## How it was built

- [ ] Tests were written from the acceptance criteria first and reviewed by: @
- [ ] Implemented with Claude Code (yes/no) · rough % of code written by the agent: __%
- [ ] Number of red → green cycles: __

## Checklist

- [ ] CI green (lint, unit, integration, RLS isolation)
- [ ] No provider SDK outside `apps/api/app/ai/`
- [ ] No hard-coded learning thresholds (read from `config/learning.yaml`)
- [ ] New tables: `tenant_id` + RLS + isolation test
- [ ] Prompt changed → version bumped + evals pass
- [ ] Spec updated if behavior changed

## Screenshots / demo

<!-- UI changes: before/after. -->
