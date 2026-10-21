# แก้ wireframe ตามที่ UC-01 ถึง UC-04 จดไว้ (D6)

| | |
|---|---|
| Owner | May |
| Branch | `docs/wireframe-uc-updates` |
| Checklist item | ไม่มีข้อตรงใน checklist · ทำตาม "ต้องเพิ่มใน spec หรือ wireframe (May · S4)" ของ UC-01 ถึง UC-04 ใน `docs/design/use-cases.md` (D6) |
| Status | in progress · 2026-10-21 |

## Plan

- [x] 1. 🤖 branch + worklog + draft PR · May เลือกขอบเขต: แก้หน้าเดิม + บทท้าย "ทางแยก"
- [ ] 2. 🤖 แก้หน้าเดิมใน `docs/design/wireframe.html`: S13 ปุ่ม "แก้เสร็จแล้ว" ใต้รายการหัวข้อ (UC-02) · S21 ยืนยันลายมือทุกครั้ง, กดแก้รายบรรทัด, ปุ่ม "ถ่ายใหม่", ไม่ไฮไลต์ตาม confidence, แก้เรื่องเล่า (UC-04)
- [ ] 3. 🙋 May เปิด wireframe ใน browser ดู S13, S21 แล้ว ok หรือบอกจุดแก้
- [ ] 4. 🤖 บทท้าย "ทางแยกและกรณีผิดพลาด" ประมาณ 8 หน้า: เช็คอีเมล + อีเมลซ้ำ (UC-01 A1, E2) · แปลง persona ไม่สำเร็จ (UC-01 E5) · ไฟล์อ่านไม่สำเร็จ (UC-02 E5) · การ์ด "กำลังอ่านไฟล์" ในหน้าหลัก (UC-02 E6) · กลับเข้าห้องกลางคัน (UC-03 E1) · ถูกปิดอัตโนมัติ (UC-03 E2) · รูปอ่านไม่ได้ (UC-04 E1)
- [ ] 5. 🙋 May review บทท้าย (หน้าตา + ข้อความ)
- [ ] 6. 🤖 อัปเดต "ต้องเพิ่มใน wireframe" ใน `use-cases.md` ว่าทำแล้ว

## Definition of done

- S13 และ S21 ตรงกับที่ตัดสินใน UC-02, UC-04 · บทท้ายครบทุกหน้าที่ UC จดไว้ (ยกเว้นที่ May ตัดออก)
- เปิด `wireframe.html` แล้วกดถัดไปได้ครบทุกหน้า ไม่มี error ใน console
- May approve

## Decisions

- 2026-10-21 · ขอบเขต: แก้ S13, S21 + บทท้าย "ทางแยก" (May เลือก) · หน้าเพิ่มไฟล์ทีหลัง (UC-02 A9) ทำถ้ามีเวลา

## Next step

ขั้น 2: แก้ S13 และ S21 ใน `docs/design/wireframe.html`

## Waiting on

ไม่มี

## Notes for next time

- wireframe เป็น storyboard: แต่ละหน้าคือ object ใน array `steps` (ch, clock, url, title, story, screen) · ชื่อหน้าใน `LABELS`
- ไฟล์ใหญ่ ~97 KB · แก้ด้วย Edit tool ทีละหน้า
