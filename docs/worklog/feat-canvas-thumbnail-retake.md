# ภาพย่อใน bubble ที่ส่งรูป + "ถ่ายใหม่" พาไปที่ canvas

| | |
|---|---|
| Owner | May |
| Branch | `feat/canvas-thumbnail-retake` |
| Checklist item | ไม่มีใน checklist · มาจาก `answer-canvas.md` §10 ข้อ 3–4 ส่วน "เพิ่ม" (May ตัดสิน 2026-11-12 · PR #122) |
| Status | in progress · 2026-11-12 |

## Plan

ขอบเขต: ฝั่งเว็บ (`apps/web`) เท่านั้น · ภาพย่อของรูปที่**ส่งใน session นี้** ใช้ไฟล์ในเครื่อง (object URL) · ภาพย่อของแชทเก่าหลังโหลดใหม่ต้องให้ API ส่งลิงก์อ่านรูป (api.md · Junior · ชนกับ #123) จึงอยู่นอกขอบเขต แสดงชื่อไฟล์เหมือนเดิม

- [ ] 1. 🤖 เขียนส่วนใหม่ใน `specs/features/tutor/answer-canvas.md` (§2 D ภาพย่อ, §2 E ถ่ายใหม่ → canvas) + AC + boundary · แจ้ง `ocr-confirm-card.md` §2 (ปุ่มถ่ายใหม่) ว่าเปลี่ยนเมื่อส่งจาก canvas
- [ ] 2. 🙋 May review spec (Claude สรุปเป็นข้อๆ + ถามเป็นตัวเลือก)
- [ ] 3. 🤖 `/spec-to-tests` (Vitest)
- [ ] 4. 🙋 May review test (Claude สรุปชื่อ test เป็นภาษาไทย)
- [ ] 5. 🤖 `/implement-feature` จน test ผ่าน + lint, typecheck, test, build
- [ ] 6. 🙋 May ลองในห้องเดโม่ (AI จำลอง): ส่งรูปจาก 📷 และจาก canvas เห็นภาพย่อ · กด "ถ่ายใหม่" ของคำตอบจาก canvas แล้วจอเลื่อนไปที่ canvas

## Definition of done

- spec ที่ May approve · test ที่ May review ผ่านทั้งหมด · CI เขียว
- ภาพย่อขึ้นใน bubble ของรูปที่ส่งใน session นี้ · "ถ่ายใหม่" ของคำตอบจาก canvas พาไปที่ canvas · จาก 📷 ยังเปิดหน้าต่างเลือกไฟล์

## Decisions

- 2026-11-12 · ใช้ type `feat` · เปลี่ยน behavior ของหน้าจอ
- 2026-11-12 · แก้ spec เดิม `answer-canvas.md` (ไฟล์ของ Jam · หน้าจอเป็นของ May) แทนการสร้าง spec ใหม่ · เป็นการต่อยอดจาก §10

## Next step

Claude ทำขั้น 1: ร่าง §2 D, §2 E และ AC

## Waiting on

- Junior (ทีหลัง): ลิงก์อ่านรูปใน `GET /sessions/{id}` ถ้าอยากให้ภาพย่อขึ้นในแชทเก่าด้วย (api.md · ไฟล์ร่วม)

## Notes for next time

- PR #123 (ห้องติวบันทึกลงฐานข้อมูล) แก้ห้องติวอยู่ · ระวัง conflict ใน `ChatRoom.tsx`
