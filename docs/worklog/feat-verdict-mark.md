# ผลตรวจ ✓/✗ ในห้องติว (S22)

| | |
|---|---|
| Owner | May |
| Branch | `feat/verdict-mark` |
| Checklist item | ไม่มีข้อตรงใน checklist · ต่อจาก `ocr-confirm-card.md` (#77) · UC-04 ขั้น 5, A4, A5, A7 · AM-05, AM-06, TM-20 |
| Status | in progress · 2026-10-28 |

## Plan

- [x] 1. 🤖 `/spec-feature` เขียน `specs/features/check/verdict-mark.md` จาก UC-04 ขั้น 5, A4, A5, A7, A8, ai-orchestration §2.4.5 ("ส่ง SSE `verdict` ก่อน tutor เริ่มพิมพ์"), `merge-rules.md` (ค่าของ `verdict` และ `error_type`) และ api.md (`verdict`) · ใส่คำถามเรื่องหน้าตา (wireframe ยังไม่มีเครื่องหมาย ✓/✗)
- [x] 2. 🙋 May review spec และตอบคำถามเรื่อง UI (ถามเป็นตัวเลือก): แสดงอะไรบ้าง, ข้อความของแต่ละ verdict, แสดงบรรทัดที่ผิดไหม
- [x] 3. 🤖 `/spec-to-tests` · ต้องแดงก่อน
- [x] 4. 🙋 May review test
- [ ] 5. 🤖 `/implement-feature` จน test เขียว
- [ ] 6. 🤖 แก้ wireframe S16 / S22 ให้มีเครื่องหมายผลตรวจตามที่ May เลือก (wireframe เป็นของ May)
- [ ] 7. 🙋 May ลองในเบราว์เซอร์บนหน้าทดลองชั่วคราว (ไม่ commit) แบบเดียวกับ #77

## Definition of done

- AC ทุกข้อใน `verdict-mark.md` มี test และผ่าน · lint, typecheck, test, build ผ่าน
- event `verdict` แสดงผลตรวจก่อนข้อความของติวเตอร์ ทั้งตอนตอบด้วยการพิมพ์และหลังยืนยันลายมือ
- wireframe ตรงกับที่ทำ

## Decisions

- 2026-10-28 · เลือกงานนี้เพราะทำให้ flow ส่งรูป → ยืนยัน → ผลตรวจ ครบฝั่งหน้าเว็บ และทำด้วย fake transport ได้
- 2026-10-28 · May ตัดสิน OQ 1–4 ตามข้อเสนอ: แถบเล็กเหนือคำพูดติวเตอร์ · บอกเลขบรรทัดในแถบ · ไม่แสดงประเภทความผิด · no_answer ไม่แสดงแถบ
- 2026-10-28 · May อนุมัติตัด `verdict` ออกจาก test เดิม 2 ตัว (chat-streaming AC-7, ocr-confirm-card AC-18 · AC-18 เปลี่ยนชื่อให้ตรงกับที่ตรวจ) · test ใหม่แดง 4 ตัว + ไฟล์ VerdictMark รันไม่ได้เพราะยังไม่มี component · ตัวที่เขียวอยู่แล้ว (no_answer, verdict ไม่รู้จัก) เป็นตัวกันไม่ให้แสดงแถบผิดเวลา

## Next step

ขั้น 5: `/implement-feature` สำหรับ `specs/features/check/verdict-mark.md`

## Waiting on

ไม่มี

## Notes for next time

- `verdict` = correct / correct_with_flaw / incomplete / incorrect · `error_type` 6 ค่า (AM-06) หรือ null · `first_wrong_line` นับจาก 1 หรือ null (`merge-rules.md`)
- ห้องตอนนี้ข้าม `verdict` (chat-streaming AC-7 มี test ที่ส่ง `verdict` คั่น token · ocr-confirm-card AC-18) → test สองตัวนี้อาจต้องปรับ ต้องขออนุมัติ May
