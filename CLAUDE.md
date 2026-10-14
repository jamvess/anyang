# CLAUDE.md — อ่านยัง? (AI study room for exam prep)

Read this file before every task. It is the contract between the team and any AI coding agent working in this repo.

## What we are building

A web app where a student uploads course material (sheets, slides, past exams), confirms an AI-extracted exam scope (topics + importance stars), then studies in a single chat room with an AI Tutor (and an optional AI Buddy). The tutor picks topics, gives problems, checks handwritten answers, teaches immediately on mistakes, and tracks mastery.

Senior project, KMUTT Computer Engineering. Team: Junior (backend + DevOps), May (frontend + UX), Jam (AI + evaluation).

## Repo map

| Path | What lives there |
|---|---|
| `apps/web/` | Next.js (App Router) + TypeScript + Tailwind + KaTeX. Deployed on Vercel. Has its own `CLAUDE.md`. |
| `apps/api/` | FastAPI (Python 3.12, uv). Deployed on Google Cloud Run. Has its own `CLAUDE.md`. |
| `supabase/migrations/` | SQL migrations. `0001_init.sql` is the data model. Applied with the Supabase CLI. |
| `specs/` | **Source of truth.** Requirements, system design, AI flows, learning model, API, feature specs, PoC specs. |
| `config/` | `learning.yaml` (every threshold of the learning model) and `ai.yaml` (model routing). |
| `prompts/` | Versioned prompts, one folder per AI purpose. |
| `evals/` | Golden sets and eval scripts for AI components. |
| `infra/` | Cloud Build, deploy scripts. |
| `docs/team/` | Roles, setup guide, sprint checklists (for humans). |

## How we work: Spec-Driven + Test-Driven

1. **Spec first.** Every feature has a spec in `specs/features/<area>/<feature>.md` (template: `specs/features/_TEMPLATE.md`). Behavior that is not in a spec does not get built.
2. **Tests from the spec.** Write tests from the acceptance criteria before the implementation. A human reviews the tests before you implement.
3. **Implement until green**, then refactor.
4. **CI must pass** (lint, unit, integration, RLS isolation, evals when prompts change).
5. **PR reviewed by a teammate** before merge.

If a spec is unclear, contradictory or missing a case: **stop and say so**. Propose the spec change in the PR description. Never guess behavior and never edit a spec silently.

Use the project skills: `/spec-feature`, `/spec-to-tests`, `/implement-feature`, `/poc-report`.

## Work sessions

- Start every session with `/work-start <name>` (Junior, May or Jam).
- Run `/work-check` after every step.
- End with `/work-pause` (unfinished) or `/work-done` (ready for PR).
- Progress lives in `docs/worklog/<branch>.md` (branch name with `/` replaced by `-`), so anyone can pick up where the last session stopped. See `docs/team/daily-workflow.md`.

## Traceability

- Requirement IDs come from `specs/requirements/requirements.md` (e.g. `TM-05`, `AM-04`).
- Test names start with the requirement ID: `test_TM05_buddy_silent_when_problem_pending`, `it('TM08 renders inline LaTeX')`.
- Tests for infrastructure with no requirement ID start with the system spec and section instead, e.g. `it('api.md SSE: parses events split across chunks')`. Feature behavior must always use a requirement ID.
- PR titles reference the feature spec and requirement IDs.

## Architecture rules (do not break)

1. **Code decides, the LLM speaks.** Stage transitions, topic selection, stars, mastery, buddy decisions are deterministic Python in `apps/api/app/domain/`. The LLM only turns a directive into words. See `specs/system/ai-orchestration.md` §1.3.
2. **The AI never writes to the database.** It returns structured output or whitelisted actions; code validates, then applies.
3. **Every AI call goes through the gateway** `ai.call(purpose, input, schema)` in `apps/api/app/ai/`. Never import a provider SDK anywhere else (AI-01).
4. **Math correctness is decided by SymPy** whenever the answer parses. The LLM classifies the error type only.
5. **No magic numbers.** Every threshold of the learning model is read from `config/learning.yaml`, and each value there cites its source or calibration plan (`specs/system/learning-model.md`). Do not hard-code 0.95, 0.2, 10, etc. in code.
6. **Multi-tenant from day one.** Every table has `tenant_id`, RLS is on for every table, and tests prove isolation (SA-06).
7. **SSE, not WebSocket**, for streaming to the browser.
8. **Prompts live in `prompts/`**, versioned (`v1.md`, `v2.md`), never inline strings in code. Uploaded document text is always wrapped in `<document>` tags and treated as data.
9. **No LangChain / LlamaIndex.** Retrieval and orchestration are our own small, testable modules.
10. **Secrets** only via environment variables (local `.env`, Secret Manager in cloud). Never commit keys.

## Commands

```bash
# database (local)
npx supabase start                  # local Postgres + Auth + Storage (Docker)
npx supabase db reset               # re-apply migrations

# backend
cd apps/api
uv sync
uv run fastapi dev app/main.py      # http://localhost:8000/docs
uv run pytest                       # tests (fake AI provider by default)
uv run ruff check . && uv run ruff format --check .

# frontend
cd apps/web
pnpm install
pnpm dev                            # http://localhost:3000
pnpm test                           # Vitest
pnpm lint && pnpm typecheck
```

## Definition of Done for a PR

- [ ] Linked feature spec (or PoC spec) and requirement IDs
- [ ] Tests written from acceptance criteria, reviewed, passing
- [ ] No provider SDK outside the gateway, no hard-coded thresholds
- [ ] New tables have `tenant_id` + RLS + an isolation test
- [ ] Prompt changes bump the prompt version and pass evals
- [ ] Spec updated in the same PR if behavior changed (with reviewer approval)

## Language

Code, identifiers, commit messages: English. Specs and team docs: Thai with English technical terms. User-facing text: Thai.
