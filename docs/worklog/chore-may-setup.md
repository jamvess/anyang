# ตั้งเครื่อง May ตาม setup.md Part A

| | |
|---|---|
| Owner | May |
| Branch | `chore/may-setup` |
| Checklist item | ⭐ ตั้งเครื่องตัวเองตาม `setup.md` Part A (ได้คอมแล้ว 14 ต.ค.) |
| Status | in progress · 2026-10-15 |

## Plan

- [ ] 1. 🤖 เช็คเครื่องมือ A2 (git, Node 24, pnpm 10.34.7, uv, Python 3.12, Claude Code) และ git config A3 · เช็คว่า `.env` กับ `apps/web/.env.local` มีอยู่และไม่โผล่ใน `git status` (ไม่เปิดอ่านไฟล์)
- [ ] 2. 🤖 A6: รัน `uv run pytest` และ `pnpm test` · เปิด backend + frontend แล้วเช็ค `/docs` กับหน้าแรก · รัน `pnpm gen:api` แล้ว git ต้องไม่เห็นไฟล์เปลี่ยน
- [ ] 3. 🙋 May เปิด http://localhost:8000/docs และ http://localhost:3000 ใน browser ดูว่าขึ้นจริง
- [ ] 4. 🙋 A8: May สร้าง Claude chat Project `อ่านยัง?` อัปโหลดไฟล์ตามตาราง A8 และใส่ Custom instructions
- [ ] 5. 🤖 ติ๊ก checklist ใน `sprint-checklists.md`

## Definition of done

- เช็คลิสต์ A6 ครบ 5 ข้อ: `uv run pytest` ผ่าน (ไม่มี skipped), `pnpm test` ผ่าน, `/docs` เปิดได้, `localhost:3000` เปิดได้, `pnpm gen:api` แล้วไม่มีไฟล์เปลี่ยน
- มี Claude chat Project ของ May ตาม A8

## Decisions

- 2026-10-15 · ข้าม A0, A1, A4, A7 · ทำแล้ว (May clone repo, ใช้ Claude Code, deploy PR #5 ได้)

## Next step

ขั้น 1: เช็คเวอร์ชันเครื่องมือและ git config

## Waiting on

ไม่มี

## Notes for next time

- ห้ามให้ Claude Code เปิดอ่าน `.env` / `.env.local` เช็คได้แค่ว่าไฟล์มีอยู่
