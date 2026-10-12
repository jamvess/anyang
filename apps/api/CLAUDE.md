# apps/api — backend conventions

FastAPI on Python 3.12, managed with `uv`. Deployed to Google Cloud Run (Docker). Read the root `CLAUDE.md` first.

## Layout

```
apps/api/
├─ app/
│  ├─ main.py              # FastAPI app, routers, middleware (request_id, auth)
│  ├─ settings.py          # pydantic-settings, reads env + config/*.yaml
│  ├─ routers/             # HTTP + SSE endpoints only, no business logic
│  ├─ services/            # orchestration: ingestion, tutor turn, scope edit
│  ├─ domain/              # PURE logic, no I/O: bkt.py, stars.py, planner.py,
│  │                       #   stage_machine.py, buddy.py, readiness.py, spacing.py
│  ├─ ai/                  # gateway.py (ai.call), providers/{gemini,claude,fake}.py,
│  │                       #   guards.py, context_builder.py
│  ├─ math/                # sympy_service.py (parse, equivalence, timeout)
│  ├─ db/                  # Supabase/Postgres access, typed repositories
│  └─ models/              # Pydantic schemas (API + AI structured outputs)
├─ tests/
│  ├─ unit/                # domain/*, math/* — fast, no network
│  ├─ integration/         # API + local Supabase, RLS isolation
│  └─ conftest.py          # fake provider fixture, test tenants
└─ pyproject.toml
```

## Rules

- `domain/` modules are pure functions over dataclasses. They are the most tested code in the repo. They read thresholds from a `LearningConfig` object loaded from `config/learning.yaml`, never literals.
- Routers stay thin: validate input → call a service → return a Pydantic model or an SSE stream.
- SSE: use `sse-starlette` (`EventSourceResponse`). Event names are fixed in `specs/system/api.md` (`token`, `verdict`, `problem`, `progress_card`, `buddy`, `ocr_preview`, `scope_patch`, `session_end`, `done`).
- AI: call only `await ai.call(purpose="check_answer", input=..., schema=CheckResult)`. The gateway handles prompts, routing (`config/ai.yaml`), retries, fallback, guards and logging to `ai_calls`.
- Tests use the fake provider by default (`AI_PROVIDER=fake`). A test that needs a real model is marked `@pytest.mark.live` and is excluded from CI.
- SymPy runs in a subprocess with a timeout (value from config). Never call `simplify` in the request thread directly.
- Database: always pass the user JWT to Supabase so RLS applies. The service-role key is used only by background ingestion jobs and must still set `tenant_id` explicitly.
- Errors: return `{"error": {"code": "...", "message": "..."}}` with a proper HTTP status.
- Lint/format: `ruff`. Type hints everywhere.

## Testing patterns

- Name tests with the requirement ID: `test_PM02_mastery_reaches_threshold_after_three_correct`.
- Domain tests are table-driven (`pytest.mark.parametrize`) using the examples in the spec.
- Integration tests create two tenants and assert neither can read the other's rows (SA-06).
