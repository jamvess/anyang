# แก้ wireframe S05, S08, S15 ตาม design ใหม่

| | |
|---|---|
| Owner | May |
| Branch | `docs/wireframe-s05-s08-s15` |
| Checklist item | แก้ wireframe S05 (คำแนะนำการเขียน persona), S08 (ช่องนาทีต่อวัน), S15 (progress card) (D6) |
| Status | in progress · 2026-10-15 |

## Plan

- [ ] 1. 🙋 May บอกว่า wireframe อยู่ที่ไหน (ลิงก์ Figma หรือไฟล์) และส่งรูปหน้าจอปัจจุบันของ S05, S08, S15
- [ ] 2. 🤖 เขียน brief การแก้ทีละหน้าใน `docs/design/wireframe-s1-changes.md`: ต้องเพิ่ม/เปลี่ยนอะไร, ข้อความภาษาไทยที่ใช้, อ้างอิง spec (UM-05, UM-07, CM-01, TM-11, TM-15, `ai-orchestration.md` 2.2.2, 2.5.2, 2.7, `api.md` `progress_card`)
- [ ] 3. 🙋 May review brief (เลือกข้อความ, ตัดสินใจเรื่อง layout)
- [ ] 4. 🙋 May แก้ S05 ใน Figma: เพิ่มคำแนะนำวิธีเขียน persona ใต้ช่อง free text
- [ ] 5. 🙋 May แก้ S08 ใน Figma: เพิ่มช่อง optional "วันละประมาณกี่นาที"
- [ ] 6. 🙋 May แก้ S15 ใน Figma: ข้อความเปิดห้องเป็น progress card + สรุป 2–3 ประโยค + โจทย์ข้อแรก
- [ ] 7. 🤖 ใส่ลิงก์ Figma + รูป 3 หน้าที่แก้แล้วใน brief และติ๊ก checklist

## Definition of done

- wireframe 3 หน้า (S05, S08, S15) แก้เสร็จตาม `ai-orchestration.md` §3.5 และ 2.7
- ทีมเปิดดูได้จากลิงก์ใน repo

## Decisions

## Next step

ขั้น 1: ถาม May ว่า wireframe อยู่ที่ไหน

## Waiting on

May: ลิงก์ wireframe + รูป 3 หน้า

## Notes for next time

- `progress_card` field: `days_left, passed, total, readiness, topics[{id, name, stars, level, review_due, origin}]` (`api.md`)
- ระดับ 4 ขั้น: ยังไม่เริ่ม / อ่อน / กำลังดี / ผ่าน (`ai-orchestration.md` 2.2.2)
