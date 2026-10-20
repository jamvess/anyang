# Use case UC-03 ติว และ UC-04 ส่งคำตอบ (D7)

| | |
|---|---|
| Owner | May |
| Branch | `docs/uc-tutor-answer` |
| Checklist item | Use case UC ติว และ UC ส่งคำตอบ ให้ครบ 4 UC (D7) |
| Status | in progress · 2026-10-20 |

## Plan

- [ ] 1. 🤖 อ่านที่มา: requirements (TM, AM, LM ฯลฯ), wireframe S15–S27, ai-orchestration (flow ห้องติว + ตรวจคำตอบ), learning-model, api.md, feature specs ของห้องแชท · จดรายการ requirement และหน้าจอของแต่ละ UC
- [ ] 2. 🤖 เขียน UC-03 ติวในห้องติว ตามรูปแบบเดียวกับ UC-01/02 (ตารางหัว, main flow, A, E, ต้องเพิ่มใน spec, คำถามเปิด)
- [ ] 3. 🙋 May ตัดสินเรื่องที่ spec ยังไม่กำหนดของ UC-03 (Claude ถามเป็นตัวเลือก) แล้วตรวจเนื้อหา
- [ ] 4. 🤖 เขียน UC-04 ส่งคำตอบและรับผลตรวจ
- [ ] 5. 🙋 May ตัดสินเรื่องที่ยังไม่กำหนดของ UC-04 แล้วตรวจเนื้อหา
- [ ] 6. 🤖 อัปเดตตารางสถานะใน `use-cases.md` และติ๊ก checklist ใน `sprint-checklists.md`

## Definition of done

- UC-03 และ UC-04 ครบ: ตารางหัว, main flow, alternative, exception · ทุกขั้นอ้างหน้าจอ `[S..]` และ requirement ID
- เรื่องที่ spec ไม่ได้กำหนด ไม่เดา แต่จดใน "คำถามเปิด" หรือ May ตัดสินแล้วจดใน "ตัดสินแล้ว"
- May approve ทั้งสอง UC · ตารางสถานะเป็น "May approve <วันที่>" · ครบ 4 UC

## Decisions

- 2026-10-20 · ทำใน S2 แทน S4 · ไม่ต้องรอใคร และงาน S3 ที่เหลือรอ endpoint `/messages` ของ Junior

## Next step

ขั้น 1: อ่านที่มาของ UC-03 และ UC-04

## Waiting on

ไม่มี

## Notes for next time

- ห้ามแก้ `requirements.md` / `api.md` (ไฟล์กลาง) ใน PR นี้ · จดเป็นข้อเสนอใน "ต้องเพิ่มใน spec" แทน เหมือน UC-01/02
