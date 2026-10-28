# การ์ดยืนยันคำตอบลายมือในห้องติว (S21)

| | |
|---|---|
| Owner | May |
| Branch | `feat/ocr-confirm-card` |
| Checklist item | ไม่มีข้อตรงใน checklist · ต่อจาก "หน้าแชท P4-lite: … ส่งรูป" (S3) · UC-04 ขั้น 2–3 · AM-01, AM-02, AM-03, AM-05, TM-08 |
| Status | in progress · 2026-10-28 |

## Plan

- [x] 1. 🤖 `/spec-feature` เขียน `specs/features/check/ocr-confirm-card.md` จาก UC-04 ขั้น 2–5, A1, E1, wireframe S21, S22, S35 และ api.md (`ocr_preview`, `POST /sessions/{id}/ocr/confirm`, `verdict`) · ใส่คำถามเปิดเรื่อง body ของ `ocr/confirm` และทาง "ถ่ายใหม่" ที่ api.md ยังไม่กำหนด
- [x] 2. 🙋 May review spec: อ่าน AC ทีละข้อเทียบกับ wireframe S21 (`docs/design/wireframe.html` ข้อ 21) · ตอบคำถามเปิดที่เป็นเรื่อง UI (ถามเป็นตัวเลือก)
- [x] 3. 🤖 ถาม Junior เรื่อง api.md (ไฟล์ร่วม): body ของ `ocr/confirm` (บรรทัดที่แก้) และทางยกเลิก preview ตอน "ถ่ายใหม่" · comment ใน PR นี้ · ไม่แก้ api.md เอง
- [ ] 4. 🤖 `/spec-to-tests` · test ตั้งชื่อตาม requirement ID · ต้องแดงก่อน
- [ ] 5. 🙋 May review test: อ่านชื่อ test เทียบกับ AC ใน spec
- [ ] 6. 🤖 `/implement-feature` จน test เขียว · ใช้ fake transport ส่ง `ocr_preview` และ `verdict` ได้ · HTTP transport เรียก `ocr/confirm` ตาม api.md
- [ ] 7. 🙋 May ลองในเบราว์เซอร์: ส่งรูปแล้วเห็นการ์ด แก้บรรทัด กดยืนยัน (ขั้นละเอียดให้ตอนถึงข้อนี้)

## Definition of done

- AC ทุกข้อใน `ocr-confirm-card.md` มี test และผ่าน · lint, typecheck, test, build ผ่าน
- การ์ดแสดงทุกครั้งที่ได้ `ocr_preview` · แก้บรรทัดได้พร้อม preview สมการ · "ถูกแล้ว ตรวจเลย" และ "ถ่ายใหม่" ทำงานตาม spec
- คำถามที่ต้องแก้ api.md ส่งถึง Junior แล้ว (ไม่แก้ไฟล์ร่วมเอง)

## Decisions

- 2026-10-28 · เลือกงานนี้เพราะเป็น Must ต่อจากห้องติวโดยตรง และทำด้วย fake transport ได้โดยไม่ต้องรอ `/uploads` ของ Junior
- 2026-10-28 · May ตัดสิน OQ 1–4, 7 ตามข้อเสนอทุกข้อ: การ์ดล็อกหลังยืนยัน · แก้ทีละบรรทัด · แก้ได้อย่างเดียว ลบ/เพิ่มบรรทัดไม่ได้ · ถ่ายใหม่เปิดหน้าต่างเลือกรูปทันที · พิมพ์ในแชทได้ระหว่างการ์ดค้าง

## Next step

ขั้น 4: รัน `/spec-to-tests` สำหรับ `specs/features/check/ocr-confirm-card.md`

## Waiting on

- Junior ตอบ OQ 5, 6, 8 ใน PR #77 (body ของ `ocr/confirm`, ทางถ่ายใหม่, รูปแบบ latex, การ์ดในประวัติ) · ไม่บล็อก test และ fake transport

## Notes for next time

- ยืนยันทุกครั้ง ไม่ไฮไลต์ตาม confidence (P1 report · UC-04 ตัดสินแล้ว 2026-10-21)
- รูปอ่านไม่ออก (E1) มาเป็น `token` ของติวเตอร์ ไม่ใช่ `ocr_preview` → ไม่มีการ์ด
