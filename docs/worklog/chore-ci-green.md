# CI เขียวครบบน main + ปิด S1 ข้อที่เสร็จแล้ว

| | |
|---|---|
| Owner | Junior |
| Branch | `chore/ci-green` |
| Checklist item | GitHub Actions รันครบ (Prompt 4) |
| Status | in progress · 2026-10-14 |

## Plan

- [ ] 1. 🤖 เทียบ `.github/workflows/ci.yml` กับ app ที่ scaffold แล้ว และรันทุกคำสั่งของ job `api`, `api-integration`, `web` บนเครื่อง แก้คำสั่งที่พัง
- [ ] 2. 🙋 ดูผล CI บน GitHub: เปิด https://github.com/jamvess/anyang/actions → workflow `ci` → run ล่าสุดของ `main` ต้องเขียวทั้ง 3 job (`api`, `api-integration`, `web`) ถ้ามี job แดง copy log ส่วนที่แดงมาให้ Claude
- [ ] 3. 🙋 ตั้ง/เช็ก branch protection: https://github.com/jamvess/anyang/settings/branches → Add rule (หรือ Edit ของ `main`) → Branch name pattern `main` → ติ๊ก "Require a pull request before merging" + "Require approvals: 1" → ติ๊ก "Require status checks to pass" แล้วค้นหาเพิ่ม `api`, `api-integration`, `web` → Save
- [ ] 4. 🤖 ติ๊ก checklist S1 ใน `docs/team/sprint-checklists.md`: ⭐ 3 ข้อที่ merge แล้ว + ข้อ GitHub Actions
- [ ] 5. 🤖 ปิดงาน: อัปเดต worklog, ให้พร้อม `/work-done`

## Definition of done

- CI เขียวบน `main` ทั้ง 3 job (เงื่อนไข "Done เมื่อ" ของ S1)
- `main` มี branch protection: ต้องผ่าน PR, review 1 คน, CI ผ่าน (`setup.md` §4.1)
- checklist S1 ของ Junior ติ๊กตรงกับความจริง

## Decisions

- 2026-10-14 · ไม่ทำ PR "chore: scaffold apps" ตาม Prompt 4 แยก · scaffold merge ไปแล้วใน PR #1–#3

## Next step

ทำข้อ 1: รัน ruff + pytest unit ใน `apps/api`, `supabase start` + pytest integration, และ `pnpm lint/typecheck/test/build` ใน `apps/web`

## Waiting on

ไม่มี

## Notes for next time

- เครื่อง Junior ยังไม่มี `gh` CLI
