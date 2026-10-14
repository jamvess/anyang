---
name: work-pause
description: Stop for today when the task is not finished. Save and push everything, write the handoff in the worklog so the next session can continue, and draft the team-chat message.
disable-model-invocation: true
---

The person wants to stop. Make sure nothing is lost and the next session (which will not remember this one) can continue from the worklog alone. Talk in Thai.

1. Run `git status`. Show the list of changed files. Commit them with `wip: <short description>`. Never commit `.env*`. If a file looks like it should not be committed, ask first.
2. Update the worklog in `docs/worklog/` for this branch:
   - **Status:** paused · today's date
   - **Done today:** bullets
   - **Next step:** the very next concrete action, written so that a fresh session can do it without asking
   - **Waiting on:** a person or a 🙋 action, or "ไม่มี"
   - **Notes for next time:** anything learned today that is not obvious from the code (commands that failed, decisions, links)
3. Commit `chore(worklog): pause <branch>` and `git push`.
4. Print in Thai:
   - **สรุปวันนี้** in 3 lines
   - **ข้อความสำหรับแชทกลุ่ม** ready to copy, for example "วันนี้ทำ ___ ไปถึง ___ · พรุ่งนี้ต่อ ___ · รอ ___"
   - **ครั้งหน้า:** "พิมพ์ `/work-start <ชื่อ>` แล้วเลือกทำต่องานนี้"
   - **ก่อนปิดเครื่อง:** "กด Ctrl+C ทุกหน้าต่างที่เปิด dev server แล้วพิมพ์ /exit"
