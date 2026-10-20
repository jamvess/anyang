# เปิด branch protection ของ main

| | |
|---|---|
| Owner | Jam |
| Branch | `chore/enable-branch-protection` |
| Checklist item | ⭐ สร้าง repo, วาง starter files · branch protection ยังไม่ได้ตั้ง (ruleset 25137368 หายไป ตรวจ 19 ต.ค. · ruleset ใหม่ main id 25374094 ยังปิดอยู่ ตามที่ Jam ขอเลื่อน) · Jam จะตั้งใหม่ · repo เป็น public |
| Status | in progress · 2026-10-20 |

## Plan

- [x] 1. 🤖 ตรวจ ruleset 25374094 และ CI · ตั้งค่าครบแล้วแต่ `enforcement: disabled`: ห้ามลบ branch, ห้าม force push, ต้องผ่าน PR และ approve 1 คน, ต้องผ่าน check `api`, `api-integration`, `web` · ไม่มี bypass · `ci.yml` รันทุก PR ไม่มี path filter และ 6 รอบล่าสุดผ่านหมด
- [x] 2. 🙋 Jam บอกทีมในกลุ่มก่อนเปิด (ข้อความร่างใน worklog ขั้นนี้)
- [x] 3. 🙋 Jam เปิด ruleset ใน GitHub (Settings → Rules → Rulesets → main → Enforcement status = Active → Save changes) หรือสั่งให้ Claude รัน `gh api`
- [x] 4. 🤖 ตรวจว่าเปิดจริง: `enforcement: active` และ PR ที่ยังไม่มี approve ขึ้นว่า merge ไม่ได้
- [x] 5. 🤖 อัปเดตบรรทัด branch protection ใน `docs/team/sprint-checklists.md` แล้ว `/work-done`

## Definition of done

- ruleset `main` เป็น Active · merge เข้า `main` ต้องมี approve 1 คนและ CI ผ่าน 3 check
- ทีมรู้ก่อนเปิด
- checklist อัปเดตแล้ว

## Decisions

- 2026-10-20 · เริ่มงานนี้เพราะ PR #31 และ #33 ถูก merge โดยไม่มี review ทั้งที่ขั้นตอนของทีมต้องรอ Approve
- 2026-10-20 · ใช้ ruleset 25374094 ที่ตั้งไว้แล้ว ไม่สร้างใหม่ · branch protection เป็นหน้าที่ของ Junior ตาม `roles.md` แต่ Jam เป็นเจ้าของ repo จึงเป็นคนเปิด
- 2026-10-20 · Jam เปิด ruleset เองผ่านหน้าเว็บ (ทาง ก) 11:33 น. · ตรวจแล้ว: `enforcement: active`, rules ของ main = deletion, non_fast_forward, pull_request, required_status_checks · PR #15 ขึ้น `BLOCKED`

## Next step

`/work-done` · reviewer Junior · PR นี้ต้องรอ approve ก่อน merge

## Waiting on

ไม่มี

## Notes for next time

- `poc/` ขึ้นเป็น untracked บน branch นี้ (คือ `out/` และ `results/` ของ P1) · ห้าม commit
- Junior review PR #15 (20 ต.ค. 11:24): ต้องแก้ 2 จุดบน `poc/P3` ก่อน merge: (1) retry ไม่มี backoff (2) `repair_unescaped_latex` แก้ทุก string รวมข้อความไทย/อังกฤษ เช่น newline ก่อน `mid-term` · Junior เสนอซ่อมเฉพาะ field LaTeX (`AnswerLine.latex`, `latex_blocks`) · ไม่ block: license PyMuPDF (AGPL) ให้ทีมคุย
