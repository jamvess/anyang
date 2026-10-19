# Review requirements.md ฝั่ง UI/UX (D1)

| | |
|---|---|
| Owner | May |
| Branch | `docs/requirements-review-may` |
| Checklist item | ร่วม review `specs/requirements/requirements.md` (D1) |
| Status | in progress · 2026-10-19 |

## Plan

`requirements.md` เป็น**ไฟล์ร่วม** · แก้ใน PR นี้ได้ แต่ต้องให้ Junior และ Jam review ทั้งคู่ก่อน merge และแจ้งแชทกลุ่ม

- [x] 1. 🤖 เทียบ `requirements.md` v1.1 กับ wireframe ที่แก้แล้ว (PR #14), feature spec หน้าแชท (PR #16), `ai-orchestration.md`, `api.md` · ดูคอลัมน์ Screen, Status, หมายเหตุ, ข้อที่ขัดกันเอง, และ requirement ที่ UI ต้องมีแต่ยังไม่มี ID
- [x] 2. 🙋 May ตัดสินทีละเรื่อง (Claude ถามเป็นตัวเลือก): แก้ใน requirements.md / ส่งเป็นคำถามให้เพื่อน / ปล่อย · 2026-10-19 ตัดสินครบ 6 เรื่อง
- [x] 3. 🤖 แก้ `requirements.md` ตามที่ May ตัดสิน (เปลี่ยนเลขเวอร์ชันเป็น v1.2 + บรรทัดสรุปการเปลี่ยนแปลง) · ข้อที่ต้องถามเพื่อนไปอยู่ใน PR description · 2026-10-19 แก้แล้ว
- [x] 4. 🙋 May ส่งข้อความแชทกลุ่มให้ Junior + Jam review (Claude ร่างให้) · 2026-10-19 ส่งแล้ว

## Definition of done

- ทุกเรื่องที่เจอมีคำตัดสินของ May
- `requirements.md` แก้ตามคำตัดสิน และ PR ได้ review จาก Junior **และ** Jam (ไฟล์ร่วม)

## Decisions

- 2026-10-19 · ใช้ type `docs` · แก้แค่เอกสาร requirement
- 2026-10-19 · ถาม May เป็นตัวเลือก ไม่ให้แก้ตารางเอง (May ถนัดแบบนี้)
- 2026-10-19 · แก้ได้ทันที (ไม่ต้องตัดสิน): CM-01 เวลาต่อวันไม่บังคับ (ตรง ai-orchestration 2.5.2) · Screen: TM-03 +S19, TM-07 +S13, TM-05 +S26, PM-03 +S15/S24
- 2026-10-19 · May ตัดสิน: (1) ข้อ changed เขียน Requirement ใหม่เป็นความหมายปัจจุบัน หมายเหตุบอกของเดิม (UM-07, TM-05, TM-07, TM-11, AM-02, PM-01, PM-03, SA-02) · (2) เพิ่ม TM-20 bubble (Must) · (3) เพิ่ม TM-21 ขีดจำกัด input จาก config (Should) · (4) UM-09, UM-10, CM-10 Screen = "ยังไม่มีหน้าจอ" + งาน wireframe S4 · (5) เพิ่ม NFR-A1 accessibility · (6) ชื่อ test หน้าแชทเปลี่ยนเป็น TM20/TM21 ตอนทำ P4-lite (จดใน spec)

## Next step

ทุกขั้นเสร็จแล้ว · May พิมพ์ `/work-done` (reviewer: Junior + Jam เพราะไฟล์ร่วม)

## Waiting on

ไม่มี

## Notes for next time

- D1 เป็นงานร่วมทั้งทีม · PR นี้ครอบคลุมมุม UI/UX ของ May เท่านั้น
