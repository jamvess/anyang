# ห้องติว · แสดงชื่อและเวลาใหม่เมื่อข้อความคนเดิมห่างกันนาน (TM-20)

| | |
|---|---|
| Owner | May |
| Branch | `feat/message-time-gap` |
| Checklist item | ไม่มีใน checklist · เจอตอนลองหน้าห้องติวจริง (PR #42): ข้อความที่ส่งใหม่ไปรวมใต้ "ปาล 20:47" ของข้อความเก่า เวลาไม่ตรง |
| Status | in progress · 2026-10-21 |

## Plan

- [x] 1. 🤖 `/spec-feature`: แก้ `specs/features/tutor/chat-room-ui.md` (เพิ่ม AC-3b) หรือ spec ใหม่ · กติกา: ข้อความติดกันของคนเดิมรวมใต้ชื่อเดียว (AC-3 เดิม) ยกเว้นห่างจากข้อความก่อนหน้าเกินค่าที่กำหนด → แสดงชื่อ + เวลาใหม่ · 🙋 May เลือกค่า
- [x] 2. 🙋 May review spec
- [ ] 3. 🤖 `/spec-to-tests` · test ใหม่ใน `MessageList.test.tsx` (ไม่แก้ test เดิม)
- [ ] 4. 🙋 May review test
- [ ] 5. 🤖 `/implement-feature` ใน `MessageList.tsx` + lint, typecheck, test, build

## Definition of done

- ข้อความคนเดิมที่ห่างกันเกินค่าที่ตั้ง แสดงชื่อและเวลาของตัวเอง · ที่ติดกันในเวลาสั้นยังรวมตาม AC-3 · test เดิมผ่านโดยไม่แก้
- lint, typecheck, test, build ผ่าน

## Decisions

- 2026-10-21 · ช่วงห่าง `MESSAGE_GROUP_GAP_MIN` = 5 นาที (May เลือก) · ตั้งแต่ 5 นาทีขึ้นไป (รวม 5 นาทีพอดี) แสดงชื่อและเวลาใหม่ · เพิ่มเป็น AC-3b ใน chat-room-ui.md

## Next step

ขั้น 3: `/spec-to-tests` สำหรับ AC-3b ใน MessageList.test.tsx

## Waiting on

ไม่มี

## Notes for next time

- กฎรวมอยู่ใน `MessageList.tsx` (`continued = role เดียวกับข้อความก่อนหน้า`) · ค่าช่วงห่างเป็นค่าของ UI ไม่ใช่ learning model (แบบ `NEAR_BOTTOM_PX`) จึงเป็น constant ในโค้ดได้
