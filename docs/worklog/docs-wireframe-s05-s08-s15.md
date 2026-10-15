# แก้ wireframe S05, S08, S15 ตาม design ใหม่

| | |
|---|---|
| Owner | May |
| Branch | `docs/wireframe-s05-s08-s15` |
| Checklist item | แก้ wireframe S05 (คำแนะนำการเขียน persona), S08 (ช่องนาทีต่อวัน), S15 (progress card) (D6) |
| Status | in progress · 2026-10-15 |

## Plan

- [x] 1. 🙋 May บอกว่า wireframe อยู่ที่ไหน → `Downloads/end-to-end.html` (ไม่มี Figma)
- [x] 2. 🤖 copy เข้า repo เป็น `docs/design/wireframe.html` (ยังไม่แก้) + เขียน brief `docs/design/wireframe-s1-changes.md`
- [x] 3. 🤖 แก้ S05 ใน HTML → 🙋 May เปิดดูแล้ว ok
- [ ] 4. 🤖 แก้ S08 → 🙋 May เปิดดูแล้ว ok
- [ ] 5. 🤖 แก้ S15 → 🙋 May เปิดดูแล้ว ok
- [ ] 6. 🙋 May ส่งข้อเสนอ `skill_level` ของ buddy ให้ Jam ในแชทกลุ่ม
- [ ] 7. 🤖 ติ๊ก checklist

## Definition of done

- wireframe 3 หน้า (S05, S08, S15) แก้เสร็จตาม `ai-orchestration.md` §3.5 และ 2.7
- ทีมเปิดดูได้จากลิงก์ใน repo

## Decisions

- 2026-10-15 · เก็บ wireframe ใน repo ที่ `docs/design/wireframe.html` และให้ Claude แก้ HTML · ไม่มี Figma, ทีมเปิดดูจาก repo ได้
- 2026-10-15 · S08 นาทีต่อวัน: 30 / 45 / 60 / 90 นาที ไม่เลือกไว้ก่อน + "ไม่บังคับ" · ตรงกับ `daily_minutes` nullable ค่าเริ่มต้น 45
- 2026-10-15 · S05 เก็บ "ระดับความรู้ของเพื่อนติว" ไว้ และเสนอ Jam เพิ่ม param `skill_level` ใน `ai-orchestration.md` §2.7 · May เห็นว่ามีผลต่อการเรียนจริง

## Next step

ขั้น 4: แก้ S08 ใน `docs/design/wireframe.html` ตาม brief

## Waiting on

May: เปิดดู S05 แล้ว ok

## Notes for next time

- `progress_card` field: `days_left, passed, total, readiness, topics[{id, name, stars, level, review_due, origin}]` (`api.md`)
- ระดับ 4 ขั้น: ยังไม่เริ่ม / อ่อน / กำลังดี / ผ่าน (`ai-orchestration.md` 2.2.2)
