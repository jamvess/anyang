---
name: work-done
description: Finish a task. Merge the latest main, run all checks, update every doc the change affects and the sprint checklist, turn the worklog into the PR description, mark the PR ready and draft the team messages.
disable-model-invocation: true
---

Close the current task so that teammates and their Claude sessions see it as done. Talk in Thai and only ask the person to confirm.

## 1 · Is it really done?

Read the worklog in `docs/worklog/` for this branch. If a plan step is not ticked or the Definition of done is not met, list what is missing and stop.

## 2 · Bring in the latest main

`git fetch origin` then `git merge origin/main`. On conflicts, stop. Explain each conflict in plain Thai, propose a resolution, and wait for "ok".

## 3 · Full checks

For every app touched by `git diff origin/main...HEAD --stat`:
- `apps/api`: `uv run ruff check .` and `uv run pytest`
- `apps/web`: `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`

Fix failures. Never change tests a human already reviewed.

## 4 · Update the docs

Compare `git diff origin/main...HEAD` with this table. Update every row that applies, then show the table with ✅ (updated) or — (not needed) and a few words why.

| If the change… | Update |
|---|---|
| adds or renames an env variable | `.env.example`, the settings class, and `docs/team/setup.md` A5 |
| needs a new tool to be installed | `docs/team/setup.md` A2 |
| adds or changes an endpoint or SSE event | `specs/system/api.md`; run `pnpm gen:api` with the API running and commit `apps/web/lib/api-schema.ts` |
| adds or changes a table or column | a new file in `supabase/migrations/` (never edit an old one) and `specs/system/data-model.md`; remind Junior to `db push` after merge |
| changes a threshold or constant | `config/learning.yaml` with a source tag [A]/[B]/[calc]/[C] and `specs/system/learning-model.md` |
| changes a prompt | a new version file in `prompts/`, never overwrite the old one |
| behaves differently from a spec | that feature spec or `specs/system/*.md`; ask first because specs are shared |
| finishes or changes a requirement | the status column of `specs/requirements/requirements.md` |
| finishes a PoC | `/poc-report <ID>` |
| revealed a mistake Claude kept repeating | a rule in the relevant `CLAUDE.md` |
| changes how the team works | `docs/team/daily-workflow.md` or `setup.md` |

## 5 · Tick the checklist

In `docs/team/sprint-checklists.md`, change the exact item named in the worklog from `[ ]` to `[x]`. If the task completed only part of the item, leave it unticked and add a short sub-bullet saying what is done.

## 6 · PR description, then remove the worklog

Write the PR description with `.github/pull_request_template.md`, using the worklog: what was done, decisions and why, requirement IDs, a rough % of code written by the agent, the number of red → green cycles. Save it to a temporary file outside the repo. Then delete `docs/worklog/<slug>.md`, because its content now lives in the PR.

## 7 · Commit and push

Commit `docs: update docs and checklist for <task>` (never `.env*`) and push.

## 8 · Open the PR for review

Reviewer for each owner:

| Work of | Reviewer |
|---|---|
| Junior | Jam (Python code) or May (parts used by the web app) |
| May | Junior |
| Jam | Junior |
| Shared files | both other people |

- If `gh` exists: `gh pr edit --body-file <file>`, `gh pr ready`, `gh pr edit --add-reviewer <github username from .github/CODEOWNERS>`.
- Otherwise print the description in a code block and tell them: paste it into the PR, click **Ready for review**, and choose the reviewer.

## 9 · Final report (Thai)

- **🔍 เช็คก่อนส่ง** (3 items): the PR description is correct, the right checklist item is ticked, the docs table makes sense
- **ข้อความแชทกลุ่ม** ready to copy: "ขอ review PR ___ หน่อย · ทำเรื่อง ___"
- **📤 ไฟล์ที่ต้องอัปโหลดใหม่เข้า Claude chat Project:** every changed file under `specs/`, `docs/team/` or `CLAUDE.md`, or "ไม่มี"
- **ขั้นถัดไป:** "เมื่อเพื่อน Approve และ CI เขียว ให้กด Merge แล้ว Delete branch จากนั้นพิมพ์ `/work-start <ชื่อ>` เพื่อเริ่มงานต่อไป"
