---
name: work-start
description: Start a work session. Sync with main, show what teammates finished, pick a new task or resume an unfinished one, create the branch, the worklog and a step plan. Use at the beginning of every work session.
argument-hint: [your name - Junior | May | Jam | ALL (solo time, pick from the whole team)]
disable-model-invocation: true
---

You are guiding **$ARGUMENTS** through the start of a work session. The person should only have to read and confirm. Talk to them in Thai (keep technical terms in English), use short sentences, and number every choice so they can answer with a number or "ok".

If no name was given, ask "คุณคือใคร: 1 Junior · 2 May · 3 Jam · 4 ALL (ทำคนเดียวช่วง solo หยิบงานของใครก็ได้)" and stop.

If the argument is `ALL` (any case), this is **solo time**: one person works while the others are offline (different time zones), and may take any teammate's task. Follow the steps below with the changes in **Mode ALL** at the end of this file. With a name, everything stays as written (overlap time: each person on their own tasks in parallel).

## 1 · Sync (do not ask, just do it)

1. Run `git status`. If there are uncommitted changes, stop and list the files. Offer: (1) commit them on a new branch, (2) they belong to an unfinished branch, switch there. Never discard changes.
2. Run `git fetch origin --prune`.
3. Find this person's unfinished work: local branches other than `main` from `git branch -vv`.
   - Branch whose upstream shows `: gone` → its PR was merged. Offer to delete it with `git branch -d`.
   - Otherwise read its worklog from the remote copy, `git show origin/<branch>:docs/worklog/<slug>.md` (slug = branch name with `/` replaced by `-`), because a teammate may have pushed to it in solo time. Note its "Owner", "Status" and "Next step".
4. `git switch main` then `git pull`.
5. Run `uv sync` in `apps/api` and `pnpm install` in `apps/web` (fast when nothing changed).

## 2 · Team status

Read `docs/team/sprint-checklists.md`, `docs/team/roles.md` and `git log --oneline -15`. If the `gh` command exists, also run `gh pr list --state open` to see what teammates are working on.

Report in Thai, at most 12 lines:

- **เพื่อนทำอะไรเสร็จล่าสุด** (from the git log and the checklist)
- **PR ที่เพื่อนเปิดอยู่** (only if gh exists): one line each, so the person does not start the same work. No approval is needed from anyone (root `CLAUDE.md`, "How we work" 5), so do not suggest reviewing first.
- **งานที่คุณค้างอยู่** (unfinished branches + their "Next step")
- **Sprint ตอนนี้** (match today's date to the sprint table) and how many of their items are left

## 3 · Choose a task

Show numbered options:

- One option per unfinished branch: "ทำต่อ: <branch> · ขั้นถัดไป: …"
- Up to 3 new tasks: unchecked items of this person in the current sprint. Order: ⭐ items first, then items a teammate is waiting on, then the rest. Skip items already covered by someone's open PR. For each, write one line on why it is next, a size (S under 1 hr / M half a day / L more than a day), and whether it has 🙋 human-only parts.

Wait for the choice.

## 4a · Resume an unfinished branch

1. **Check the lock.** If the worklog Status is `in progress` and the Owner line says someone else continues it (`ทำต่อโดย <name>`), that person may be working on it now. Stop and ask: "<name> ทำ branch นี้ต่ออยู่ ถามในกลุ่มก่อนไหม (1 ถามก่อน · 2 เขาทำเสร็จแล้ว ทำต่อได้)".
2. `git switch <branch>`, then `git pull --ff-only` (brings in commits a teammate pushed in solo time), then `git merge origin/main`. On conflicts, stop. Explain each conflict in plain Thai, propose a resolution, and wait for "ok".
3. **Take the lock.** Set the worklog Status to `in progress · <today>` (if it says `paused`), commit `chore(worklog): resume <branch>` and push right away, so a `/work-start ALL` session elsewhere does not pick the same branch.
4. Read the worklog and `git diff origin/main...HEAD --stat`.
5. Summarize in 3–5 lines what is done and what the next step is. If someone else worked on it (`ทำต่อโดย`), say what they did. Ask "เริ่มขั้นถัดไปเลยไหม".

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
- Before editing a file owned by someone else (see `docs/team/roles.md` and `.github/CODEOWNERS`) or a shared file (`CLAUDE.md`, `specs/requirements/requirements.md`, `specs/system/api.md`, `config/*.yaml`), say so and ask first. Also remind them to tell the group chat.
- Never change tests that a human already reviewed.

## Mode ALL (solo time)

The team agreed (2026-10-31) that during solo time anyone may take anyone's task, so work keeps moving while the owner is offline. Overlap time still uses names.

**Who is at the keyboard.** Run `gh api user --jq .login` and map the login with the GitHub row of `docs/team/roles.md` (the table writes handles as `` `@login` ``; strip the backticks, the `@` and any note in brackets before comparing). If `gh` is missing or the login is not in the table, ask "คุณคือใคร: 1 Junior · 2 May · 3 Jam". Call this person the **operator**. The operator owns the session: worklog Owner, 🙋 steps, secrets in their own `.env`.

**Section 1 · Sync.** Same, plus list the teammates' unfinished work from the remote branches, not from PRs (a branch may have no PR, and `gh` may be missing): every `origin/<branch>` except `main` (`git for-each-ref --format='%(refname:short)' refs/remotes/origin`) that has `docs/worklog/<slug>.md` (`git show origin/<branch>:docs/worklog/<slug>.md`). If `gh` exists, add the PR number from `gh pr list --state open --json number,headRefName`.

**Section 2 · Team status.** Same report, but "งานค้าง" covers everyone: one line per open branch with its owner, worklog Status and Next step.

**Section 3 · Choose a task.** Show two numbered groups, so tasks nobody has started are always on the list:

**ก · ทำต่อ** (all of them)

1. The operator's own unfinished branches.
2. Teammates' branches whose worklog Status is **paused** (written by `/work-pause`). Never offer a branch whose Status is `in progress`, or one with no worklog: its owner may be in the middle of it.

**ข · เริ่มใหม่** (at least 3, even when group ก is long) · unchecked items that no open branch covers (match each branch's worklog Checklist item), from every section of `docs/team/sprint-checklists.md`:

1. Current sprint: ⭐ first, then items someone is waiting on (unblocks another person's next step), then the rest.
2. If fewer than 3 are left, fill from the next sprint, then from items still unchecked in earlier sprints.

End with one more option: **"ดูงานที่ยังไม่เริ่มทั้งหมด"**. If chosen, list every unchecked, unstarted item of every person and every sprint (grouped by sprint, owner shown, sizes and 🙋 parts as below) and let the operator pick any of them.

For each option show: owner (whose item it is), why it is next, size (S/M/L), and its 🙋 parts. **Skip, or mark "ทำได้บางส่วน",** an option whose 🙋 steps need a specific other person:

- access the operator does not have (Supabase dashboard, `npx supabase db push` or `link` which only Junior may run, Vercel, a secret in someone else's `.env`, a device or account),
- a decision that `roles.md` ("ตัดสินใจเรื่อง") gives to that person (backend/DB/deploy → Junior, screens and flow → May, prompt/model/threshold/eval → Jam).

For "ทำได้บางส่วน", plan only the parts the operator can do and put the rest under **Waiting on** in the worklog, naming the person.

**Section 4a · Resume a teammate's branch.** Follow 4a, but in step 3 (take the lock) also set Owner to `<owner> · ทำต่อโดย <operator> (<date>)` and commit `chore(worklog): <operator> continues <branch>`. Push before any other work, so the owner sees it when they come back and their own `/work-start` stops at the lock check. Do not rewrite the plan or the decisions already made; continue from Next step.

**Section 4b · Start a teammate's item.** Worklog Owner `<operator> (item of <owner>)`. The Checklist item is the exact text from the owner's section.

**Ownership rule.** For a file owned by the teammate whose task this is, the team agreement replaces asking that teammate, but the operator still tells the group chat what they took (draft message in Thai: "solo time: <operator> ทำ <task> ของ <owner> · PR #__ · ถ้ามีอะไรทักได้ ไว้ดูตอนตื่น"). **Shared files** (`CLAUDE.md`, `specs/requirements/requirements.md`, `specs/system/api.md`, `config/*.yaml`) keep the base rule: say so and ask the operator before editing, and post the group chat message before merge, as in `/work-done`. Never change tests a human already reviewed, whoever reviewed them.

**Ending.** `/work-pause` and `/work-done` read the worklog Owner line: when it says `ทำต่อโดย` or `(item of …)`, they add the solo notes themselves (see those skills).
