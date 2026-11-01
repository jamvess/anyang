# Worklog

One file per open branch: `docs/worklog/<branch-with-dashes>.md` (for example `feat/chat-page` → `feat-chat-page.md`).

- `/work-start` creates it from `_TEMPLATE.md`
- `/work-check` ticks steps and updates "Next step"
- `/work-pause` writes the handoff for the next session
- `/work-done` moves its content into the PR description and deletes it

Claude Code does not remember earlier sessions, so this file is how a new session (or a teammate) knows where the work stopped. Do not edit another person's worklog, **except** in solo time: `/work-start ALL` may continue a teammate's branch whose Status is `paused`, and then updates its Owner (`ทำต่อโดย …`), Status and the steps it does (team decision 2026-10-31).

**Status is a lock.** `in progress` means someone is working on the branch now; `/work-pause` sets `paused`. `/work-start` sets `in progress` again and pushes before resuming, so two people never work on one branch at once.
