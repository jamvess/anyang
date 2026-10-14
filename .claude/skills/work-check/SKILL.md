---
name: work-check
description: Check the step just finished. Run the relevant checks, explain the change in plain Thai, list exactly what the human must verify, update the worklog, and commit after the human says ok. Use after every step of a task.
disable-model-invocation: true
---

Check the work done since the last commit. The person will only read your report and answer, so make it short, concrete and in Thai (technical terms in English).

## 1 · Collect

Run `git status` and `git diff HEAD --stat`. Read the current worklog in `docs/worklog/` for this branch.

## 2 · Run checks for the areas that changed

| Changed | Run |
|---|---|
| `apps/api/` or `config/` | `cd apps/api && uv run ruff check . && uv run pytest` |
| `apps/web/` | `cd apps/web && pnpm lint && pnpm typecheck && pnpm test` |
| `supabase/migrations/` | `uv run pytest tests/integration` from `apps/api` (only after Junior confirms the migration is pushed to anyang-dev) |
| `prompts/` or `evals/` | the eval script for that prompt, if one exists |
| only `.md` files | nothing |

If a check fails, fix it (at most 2 attempts) and run it again. Never change a test that a human already reviewed. If it still fails, stop and explain the problem in plain Thai.

## 3 · Report (in Thai, this exact structure)

**ทำอะไรไป** · at most 5 bullets in plain words. Explain any term a first-year student would not know.

**ผลตรวจ** · one line per check, ✅ or ❌.

**🔍 คุณช่วยเช็ค** · 2 to 5 items. Each one must be doable in under a minute and must say exactly where to look and what should be there, for example:
- "เปิด http://localhost:3000/chat ต้องเห็นกล่องพิมพ์ข้อความด้านล่าง"
- "เปิดไฟล์ `.github/CODEOWNERS` บรรทัด 2 ต้องเป็น @may-real-name"
- "อ่านชื่อ test 4 ตัวในตาราง ต้องตรงกับ AC-1 ถึง AC-4 ใน spec"

Never write "review all the code".

**⚠️ ความเสี่ยง** · anything that touched a shared file, another person's folder, a migration, env variables, CI, or that differs from the spec. Write "ไม่มี" if there is none.

**📋 ก๊อปไปถาม Claude chat** · only when there is a design decision or something you are unsure about. Write a self-contained block: the task, what was done, the exact question.

## 4 · Update the worklog

Tick the finished step, add any decision made (with the reason), and rewrite "Next step" as one concrete action.

## 5 · Wait for the answer

End with: "ผ่านไหม? (ok = commit แล้วไปขั้นต่อไป / บอกสิ่งที่ต้องแก้)".

- On **ok**: `git add` only the files of this step (never `.env*`), commit with a conventional message that describes the step, `git push`, then continue with the next step of the plan.
- On a correction: fix it and run this check again.
- If this was the last step: say "ครบทุกขั้นแล้ว พิมพ์ /work-done เพื่อปิดงาน".
