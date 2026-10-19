# แก้ wireframe S05, S08, S15 ตาม design ใหม่

| | |
|---|---|
| Owner | May |
| Branch | `docs/wireframe-s05-s08-s15` |
| Checklist item | แก้ wireframe S05 (คำแนะนำการเขียน persona), S08 (ช่องนาทีต่อวัน), S15 (progress card) (D6) |
| Status | in progress · 2026-10-19 |

## Plan

- [x] 1. 🙋 May บอกว่า wireframe อยู่ที่ไหน → `Downloads/end-to-end.html` (ไม่มี Figma)
- [x] 2. 🤖 copy เข้า repo เป็น `docs/design/wireframe.html` (ยังไม่แก้) + เขียน brief `docs/design/wireframe-s1-changes.md`
- [x] 3. 🤖 แก้ S05 ใน HTML → 🙋 May เปิดดูแล้ว ok
- [x] 4. 🤖 แก้ S08 (commit `39defa6`) → 🙋 May เปิดดูแล้ว ok (2026-10-19)
- [ ] 5. 🤖 แก้ S15 (แก้แล้ว 2026-10-19) → 🙋 May เปิดดูแล้ว ok (ยังไม่ได้ตอบ)
- [ ] 6. 🙋 May ส่งข้อเสนอ `skill_level` ของ buddy ให้ Jam ในแชทกลุ่ม
- [ ] 7. 🤖 ติ๊ก checklist

## Definition of done

- wireframe 3 หน้า (S05, S08, S15) แก้เสร็จตาม `ai-orchestration.md` §3.5 และ 2.7
- ทีมเปิดดูได้จากลิงก์ใน repo

## Decisions

- 2026-10-15 · เก็บ wireframe ใน repo ที่ `docs/design/wireframe.html` และให้ Claude แก้ HTML · ไม่มี Figma, ทีมเปิดดูจาก repo ได้
- 2026-10-15 · S08 นาทีต่อวัน: 30 / 45 / 60 / 90 นาที ไม่เลือกไว้ก่อน + "ไม่บังคับ" · ตรงกับ `daily_minutes` nullable ค่าเริ่มต้น 45
- 2026-10-15 · S05 เก็บ "ระดับความรู้ของเพื่อนติว" ไว้ และเสนอ Jam เพิ่ม param `skill_level` ใน `ai-orchestration.md` §2.7 · May เห็นว่ามีผลต่อการเรียนจริง

## Done today (2026-10-15)

- หา wireframe เจอที่ `Downloads/end-to-end.html` (27 หน้า, ไม่มี Figma) · copy เข้า repo เป็น `docs/design/wireframe.html`
- เขียน brief `docs/design/wireframe-s1-changes.md`: สิ่งที่แก้ทีละหน้า + ข้อเสนอ `skill_level` ของ buddy ให้ Jam + จุดที่ขัด spec ใน S04, S24 (ไว้ทำใน S2)
- S05: คำแนะนำเป็นแบบคงที่ (ไม่ติ๊กอัตโนมัติ, UM-06 deferred), ตัดปุ่มฟังเสียง (UM-07), เพิ่มกล่อง "ทำให้ไม่ได้" (§2.7 ข้อ 3) · May ok แล้ว
- S08: ตัวเลือก 30 / 45 / 60 / 90 นาที + "ไม่บังคับ" + คำอธิบาย · ในภาพเลือก 60 นาทีไว้เพราะเป็นสถานะหลังปาลกรอก (story เขียนไว้) · **May ยังไม่ได้ ok**

## Next step

1. ถาม May ว่า S08 ผ่านไหม (เปิด `docs/design/wireframe.html` ใน browser ไปหน้า S08) · ถ้า ok ติ๊กขั้น 4
2. ขั้น 5: แก้ S15 (หา `title:"เข้าห้องติวเลย ไม่มีหน้าคั่น"`) ให้เปิดห้องด้วย progress card ก่อน → พี่ตาลสรุป 2–3 ประโยค + เหตุผลที่เลือกผลต่างกำลังสอง → โจทย์ `x² − 49` · การ์ดแสดง สอบใน 5 วัน, ผ่าน 0/7 หัวข้อ, ความพร้อม 0%, รายหัวข้อพร้อมดาวและระดับ "ยังไม่เริ่ม" · แก้ story ที่เขียนว่า "ไม่มีการ์ด" ด้วย

## Waiting on

May: ตอบว่า S08 ผ่านไหม

## Notes for next time

- `progress_card` field: `days_left, passed, total, readiness, topics[{id, name, stars, level, review_due, origin}]` (`api.md`)
- ระดับ 4 ขั้น: ยังไม่เริ่ม / อ่อน / กำลังดี / ผ่าน (`ai-orchestration.md` 2.2.2)
- แก้ wireframe ด้วย Python `str.replace` ที่ assert ว่าเจอข้อความครั้งเดียว · `sed` จับบรรทัดที่มี emoji ในไฟล์ worklog ไม่ได้ ใช้ Edit tool แทน
- May ชอบคำตอบสั้นๆ บอกตรงๆ ว่าต้องทำอะไร
