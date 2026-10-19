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
- [x] 5. 🤖 แก้ S15 → 🙋 May เปิดดูแล้ว ok (2026-10-19)
- [ ] 6. 🙋 May ส่งข้อเสนอ `skill_level` ของ buddy ให้ Jam ในแชทกลุ่ม
- [ ] 7. 🤖 ติ๊ก checklist

## Definition of done

- wireframe 3 หน้า (S05, S08, S15) แก้เสร็จตาม `ai-orchestration.md` §3.5 และ 2.7
- ทีมเปิดดูได้จากลิงก์ใน repo

## Decisions

- 2026-10-15 · เก็บ wireframe ใน repo ที่ `docs/design/wireframe.html` และให้ Claude แก้ HTML · ไม่มี Figma, ทีมเปิดดูจาก repo ได้
- 2026-10-15 · S08 นาทีต่อวัน: 30 / 45 / 60 / 90 นาที ไม่เลือกไว้ก่อน + "ไม่บังคับ" · ตรงกับ `daily_minutes` nullable ค่าเริ่มต้น 45
- 2026-10-15 · S05 เก็บ "ระดับความรู้ของเพื่อนติว" ไว้ และเสนอ Jam เพิ่ม param `skill_level` ใน `ai-orchestration.md` §2.7 · May เห็นว่ามีผลต่อการเรียนจริง
- 2026-10-19 · S15 นับ 8 หัวข้อ (ไม่ใช่ 7) · ตรงกับ S14 "ขอบเขตสุดท้าย · 8 หัวข้อ" (กำลังสามถูกตัดไปแล้ว)
- 2026-10-19 · S15 ตัดข้อความมีน "เอาดิ เราก็ยังไม่ค่อยได้" ออก · TM-15 ให้ส่งโจทย์ต่อจากสรุปทันที และ buddy ห้ามพูดระหว่างรอคำตอบ (TM-05) มีนยังพูดใน S17

## Done today (2026-10-15)

- หา wireframe เจอที่ `Downloads/end-to-end.html` (27 หน้า, ไม่มี Figma) · copy เข้า repo เป็น `docs/design/wireframe.html`
- เขียน brief `docs/design/wireframe-s1-changes.md`: สิ่งที่แก้ทีละหน้า + ข้อเสนอ `skill_level` ของ buddy ให้ Jam + จุดที่ขัด spec ใน S04, S24 (ไว้ทำใน S2)
- S05: คำแนะนำเป็นแบบคงที่ (ไม่ติ๊กอัตโนมัติ, UM-06 deferred), ตัดปุ่มฟังเสียง (UM-07), เพิ่มกล่อง "ทำให้ไม่ได้" (§2.7 ข้อ 3) · May ok แล้ว
- S08: ตัวเลือก 30 / 45 / 60 / 90 นาที + "ไม่บังคับ" + คำอธิบาย · ในภาพเลือก 60 นาทีไว้เพราะเป็นสถานะหลังปาลกรอก (story เขียนไว้) · **May ยังไม่ได้ ok**

## Done 2026-10-19

- May ok S08 แล้ว
- S15: เพิ่ม progress card ก่อนข้อความแรก (สอบใน 5 วัน, ผ่าน 0 / 8 หัวข้อ, ความพร้อม 0% + คำอธิบายว่าไม่ใช่คะแนนสอบ, รายหัวข้อเรียงตามดาว ระดับ "ยังไม่เริ่ม" ทั้งหมด) → พี่ตาลสรุป 2 ประโยค + เหตุผล → โจทย์ `x² − 49` · แก้ story ให้ตรง · May ok แล้ว

## Next step

ขั้น 6: May ส่งข้อเสนอ `skill_level` ให้ Jam ในแชทกลุ่ม (ข้อความอยู่ใน `docs/design/wireframe-s1-changes.md` หัวข้อ "ข้อเสนอแก้ spec")

## Waiting on

May: ส่งข้อความหา Jam แล้วบอกว่าส่งแล้ว

## Notes for next time

- `progress_card` field: `days_left, passed, total, readiness, topics[{id, name, stars, level, review_due, origin}]` (`api.md`)
- ระดับ 4 ขั้น: ยังไม่เริ่ม / อ่อน / กำลังดี / ผ่าน (`ai-orchestration.md` 2.2.2)
- แก้ wireframe ด้วย Python `str.replace` ที่ assert ว่าเจอข้อความครั้งเดียว · `sed` จับบรรทัดที่มี emoji ในไฟล์ worklog ไม่ได้ ใช้ Edit tool แทน
- May ชอบคำตอบสั้นๆ บอกตรงๆ ว่าต้องทำอะไร
