# ตรวจ wireframe ทั้ง 27 หน้าให้ตรงกับ design ใหม่ (D6)

| | |
|---|---|
| Owner | May |
| Branch | `docs/wireframe-review-27` |
| Checklist item | ตรวจ wireframe ทั้ง 27 หน้าว่าไม่มีส่วนที่ขัดกับ design ใหม่ (D6) |
| Status | in progress · 2026-10-19 |

## Plan

"design ใหม่" = `specs/system/ai-orchestration.md` (โดยเฉพาะ §3.5), `specs/requirements/requirements.md` (สถานะ changed / deferred), `specs/system/api.md`, `specs/system/learning-model.md`

- [ ] 1. 🤖 อ่าน spec แล้วทำรายการ "สิ่งที่ design ใหม่กำหนด" ที่กระทบหน้าจอ + ทำรายการ 27 หน้าจาก `docs/design/wireframe.html`
- [ ] 2. 🤖 ไล่ตรวจทีละหน้า (S01–S27) เขียนผลลง `docs/design/wireframe-s2-review.md`: หน้า · สิ่งที่ขัด · อ้างอิง spec · ข้อเสนอ (แก้ wireframe / แก้ spec / ปล่อยไว้) · รวม 3 เรื่องที่จดไว้จาก S1 (S04, S13–S14, S24) และข้อเสนอ `skill_level` ของ S05
- [ ] 3. 🙋 May ตัดสินทีละข้อในไฟล์ review (พิมพ์ในช่อง "ตัดสิน": `แก้ wf` / `แก้ spec` / `ปล่อย` + เหตุผลสั้นๆ)
- [ ] 4. 🤖 แก้ `wireframe.html` ตามที่ตัดสิน `แก้ wf` · ทีละหน้า · ไม่แตะหน้าอื่น
- [ ] 5. 🙋 May เปิด `docs/design/wireframe.html` ใน browser (ดับเบิลคลิกไฟล์ใน File Explorer หรือคลิกขวาในแถบ Explorer ของ VS Code → Reveal in File Explorer แล้วดับเบิลคลิก) ใช้ลูกศรซ้ายขวาไปหน้าที่แก้ ดูว่าถูกต้อง
- [ ] 6. 🤖 ข้อที่ตัดสิน `แก้ spec` → รวมเป็นข้อเสนอใน PR description + ข้อความแชทกลุ่มถึงเจ้าของ spec (spec เป็นไฟล์ร่วม ไม่แก้เองโดยไม่ถาม)

## Definition of done

- ทุกหน้า S01–S27 มีผลตรวจใน `wireframe-s2-review.md` (ผ่าน หรือ มีรายการที่ขัด)
- ทุกรายการที่ขัดมีคำตัดสินของ May · ข้อ `แก้ wf` แก้แล้วใน `wireframe.html` · ข้อ `แก้ spec` อยู่ใน PR description และแจ้งเจ้าของแล้ว
- Junior review PR

## Decisions

- 2026-10-19 · ใช้ type `docs` · แก้แค่ wireframe และเอกสาร design

## Next step

Claude ทำขั้น 1: อ่าน spec + ทำรายการ 27 หน้า

## Waiting on

ไม่มี

## Notes for next time

- ข้อเสนอ `skill_level` ของ buddy (S05) ยังรอ Jam ตอบ (`docs/design/wireframe-s1-changes.md`)
