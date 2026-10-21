# รองรับ `\$` ในข้อความแชท (TM-08 · api.md v1.3)

| | |
|---|---|
| Owner | May |
| Branch | `feat/escaped-dollar` |
| Checklist item | ไม่มีใน checklist · ทำตาม api.md v1.3 Conventions "สมการในข้อความ" (May ตัดสิน 2026-10-21 ใน PR #36) ระหว่างรอ CORS ของ PR #42 |
| Status | ready for work-done · 2026-10-21 |

## Plan

- [x] 1. 🤖 `/spec-feature`: `specs/features/tutor/math-escape.md` (TM-08) · `\$` นอกสมการ = เครื่องหมาย $ ไม่เปิด/ปิดสมการ · ในสมการส่งต่อให้ KaTeX · ระหว่าง stream ไม่ถือเป็น `$` ที่ยังไม่ปิด
- [x] 2. 🙋 May review spec
- [x] 3. 🤖 `/spec-to-tests` · test ใหม่ใน `tests/chat/MessageText.test.tsx` (ไม่แก้ test เดิม)
- [x] 4. 🙋 May review test
- [x] 5. 🤖 `/implement-feature` ใน `components/chat/MessageText.tsx` + lint, typecheck, test, build

## Definition of done

- `\$` แสดงเป็น "$" ทั้งตอน stream และหลัง stream · สมการ `$…$` / `$$…$$` เดิมยังทำงาน · test เดิมผ่านโดยไม่แก้
- lint, typecheck, test, build ผ่าน

## Decisions

- 2026-10-21 · `\\$` (backslash สองตัว): นับ backslash ที่ติดกัน เลขคี่ = เครื่องหมาย $ · เลขคู่ = `$` จริง (May ตัดสิน)
- 2026-10-21 · implement: เปลี่ยน regex `MATH` เป็นตัวแยกทีละตัวอักษรใน `MessageText.tsx` เพราะต้องนับ backslash ก่อน `$` · red → green 1 รอบ (78/78) · lint, typecheck, build ผ่าน

## Next step

รัน /work-done

## Waiting on

ไม่มี

## Notes for next time

- กฎเดิมอยู่ที่ `MessageText.tsx` (regex `MATH` + `withoutUnclosedMath`) · spec เดิม: chat-room-ui.md AC-7..10, chat-streaming.md AC-9..11b
