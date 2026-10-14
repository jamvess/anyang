# Worklog

One file per open branch: `docs/worklog/<branch-with-dashes>.md` (for example `feat/chat-page` → `feat-chat-page.md`).

- `/work-start` creates it from `_TEMPLATE.md`
- `/work-check` ticks steps and updates "Next step"
- `/work-pause` writes the handoff for the next session
- `/work-done` moves its content into the PR description and deletes it

Claude Code does not remember earlier sessions, so this file is how a new session (or a teammate) knows where the work stopped. Do not edit another person's worklog.
