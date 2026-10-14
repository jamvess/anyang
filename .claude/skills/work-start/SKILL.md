---
name: work-start
description: Start a work session. Sync with main, show what teammates finished, pick a new task or resume an unfinished one, create the branch, the worklog and a step plan. Use at the beginning of every work session.
argument-hint: [your name - Junior | May | Jam]
disable-model-invocation: true
---

You are guiding **$ARGUMENTS** through the start of a work session. The person should only have to read and confirm. Talk to them in Thai (keep technical terms in English), use short sentences, and number every choice so they can answer with a number or "ok".

If no name was given, ask "คุณคือใคร: 1 Junior · 2 May · 3 Jam" and stop.

## 1 · Sync (do not ask, just do it)

1. Run `git status`. If there are uncommitted changes, stop and list the files. Offer: (1) commit them on a new branch, (2) they belong to an unfinished branch, switch there. Never discard changes.
2. Run `git fetch origin --prune`.
3. Find this person's unfinished work: local branches other than `main` from `git branch -vv`.
   - Branch whose upstream shows `: gone` → its PR was merged. Offer to delete it with `git branch -d`.
   - Otherwise read its worklog with `git show <branch>:docs/worklog/<slug>.md` (slug = branch name with `/` replaced by `-`) and note its "Next step".
4. `git switch main` then `git pull`.
5. Run `uv sync` in `apps/api` and `pnpm install` in `apps/web` (fast when nothing changed).

## 2 · Team status

Read `docs/team/sprint-checklists.md`, `docs/team/roles.md` and `git log --oneline -15`. If the `gh` command exists, also run `gh pr list --state open` to see drafts and review requests.

Report in Thai, at most 12 lines:

- **เพื่อนทำอะไรเสร็จล่าสุด** (from the git log and the checklist)
- **PR ที่รอให้คุณ review** (only if gh exists). If there are any, recommend doing the review first (`docs/team/daily-workflow.md` section D).
- **งานที่คุณค้างอยู่** (unfinished branches + their "Next step")
- **Sprint ตอนนี้** (match today's date to the sprint table) and how many of their items are left

## 3 · Choose a task

Show numbered options:

- One option per unfinished branch: "ทำต่อ: <branch> · ขั้นถัดไป: …"
- Up to 3 new tasks: unchecked items of this person in the current sprint. Order: ⭐ items first, then items a teammate is waiting on, then the rest. Skip items already covered by someone's open PR. For each, write one line on why it is next, a size (S under 1 hr / M half a day / L more than a day), and whether it has 🙋 human-only parts.

Wait for the choice.

## 4a · Resume an unfinished branch

1. `git switch <branch>` then `git merge origin/main`. On conflicts, stop. Explain each conflict in plain Thai, propose a resolution, and wait for "ok".
2. Read the worklog and `git diff origin/main...HEAD --stat`.
3. Summarize in 3–5 lines what is done and what the next step is. Ask "เริ่มขั้นถัดไปเลยไหม".

## 4b · Start a new task

1. **Branch:** `<type>/<short-kebab-name>`, where type is one of `feat` `fix` `chore` `docs` `poc`. Create it from the updated `main`.
2. **Kind of work:**
   - Feature with requirement IDs → follow the spec flow: `/spec-feature` → human reviews spec → `/spec-to-tests` → human reviews tests → `/implement-feature`.
   - PoC → code in `poc/<ID>/`, finish with `/poc-report <ID>`.
   - chore / docs / setup → do it directly.
3. **Plan:** read the relevant `CLAUDE.md` files and specs. Write 3–8 small steps. Mark each step 🤖 (Claude does it) or 🙋 (the person must do it, e.g. click in a dashboard, enter a secret, take photos, make a design decision, label data). For 🙋 steps, write exact click-by-click instructions. End the plan with a **Definition of done** taken from the checklist item or spec.
4. **Worklog:** copy `docs/worklog/_TEMPLATE.md` to `docs/worklog/<slug>.md` and fill in Task, Owner, Checklist item (exact text), Plan and Definition of done.
5. **Publish:** commit `chore(worklog): start <branch>` and `git push -u origin <branch>`. If `gh` exists, run `gh pr create --draft --title "<type>: <task>" --body "Work in progress · see docs/worklog/<slug>.md"`. Otherwise build the URL `https://github.com/<owner>/<repo>/compare/<branch>?expand=1` from `git remote get-url origin` and tell them to click **Create draft pull request**.
6. Show the plan and ask "แผนนี้โอเคไหม (ok / บอกข้อที่อยากแก้)". Wait.

## 5 · The loop (after the plan is approved)

Do one step at a time. After each step, follow `.claude/skills/work-check/SKILL.md` exactly: run the checks, explain, list what the person must verify, update the worklog, then wait for "ok". On "ok", commit and push, then start the next step. For 🙋 steps, give the instructions and wait until they say it is done.

When every step is done, tell them to type `/work-done`. If they want to stop for today, tell them to type `/work-pause`.

## Rules

- Never read `.env` or `.env.*` files. Anything that needs a secret is a 🙋 step.
- Only Junior may run `npx supabase db push` or `npx supabase link`, and only after explicit confirmation.
- Before editing a file owned by someone else (see `docs/team/roles.md` and `.github/CODEOWNERS`) or a shared file (`CLAUDE.md`, `specs/requirements/requirements.md`, `specs/system/api.md`, `config/ai.yaml`), say so and ask first. Also remind them to tell the group chat.
- Never change tests that a human already reviewed.
