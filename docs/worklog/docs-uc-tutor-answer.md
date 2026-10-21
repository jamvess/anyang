# Use case UC-03 ติว และ UC-04 ส่งคำตอบ (D7)

| | |
|---|---|
| Owner | May |
| Branch | `docs/uc-tutor-answer` |
| Checklist item | Use case UC ติว และ UC ส่งคำตอบ ให้ครบ 4 UC (D7) |
| Status | in progress · 2026-10-21 |

## Plan

- [x] 1. 🤖 อ่านที่มา: requirements (TM, AM, LM ฯลฯ), wireframe S15–S27, ai-orchestration (flow ห้องติว + ตรวจคำตอบ), learning-model, api.md, feature specs ของห้องแชท · จดรายการ requirement และหน้าจอของแต่ละ UC
- [x] 2. 🤖 เขียน UC-03 ติวในห้องติว ตามรูปแบบเดียวกับ UC-01/02 (ตารางหัว, main flow, A, E, ต้องเพิ่มใน spec, คำถามเปิด)
- [x] 3. 🙋 May ตัดสินเรื่องที่ spec ยังไม่กำหนดของ UC-03 (Claude ถามเป็นตัวเลือก) แล้วตรวจเนื้อหา
- [ ] 4. 🤖 เขียน UC-04 ส่งคำตอบและรับผลตรวจ
- [ ] 5. 🙋 May ตัดสินเรื่องที่ยังไม่กำหนดของ UC-04 แล้วตรวจเนื้อหา
- [ ] 6. 🤖 อัปเดตตารางสถานะใน `use-cases.md` และติ๊ก checklist ใน `sprint-checklists.md`

## Definition of done

- UC-03 และ UC-04 ครบ: ตารางหัว, main flow, alternative, exception · ทุกขั้นอ้างหน้าจอ `[S..]` และ requirement ID
- เรื่องที่ spec ไม่ได้กำหนด ไม่เดา แต่จดใน "คำถามเปิด" หรือ May ตัดสินแล้วจดใน "ตัดสินแล้ว"
- May approve ทั้งสอง UC · ตารางสถานะเป็น "May approve <วันที่>" · ครบ 4 UC

## Decisions

- 2026-10-20 · ทำใน S2 แทน S4 · ไม่ต้องรอใคร และงาน S3 ที่เหลือรอ endpoint `/messages` ของ Junior
- 2026-10-21 · UC-03: May ตัดสิน 4 เรื่อง (กลับเข้าห้อง, ปิดอัตโนมัติ, เพิ่มหัวข้อนอกชีท, เรียกเพื่อนติวกลับ) · ดู "ตัดสินแล้ว" ใน use-cases.md
- 2026-10-21 · api.md "รอตัดสิน" (May ตอบ ยังไม่ได้แก้ api.md เพราะเป็นไฟล์กลาง): ข้อ 3 ใช้ `$…$` / `$$…$$` เป็น contract และ `\$` = เครื่องหมาย $ จริง (web ยังไม่รองรับ `\$` ต้องเพิ่มตอนทำ feature) · ข้อ 5 `done` ส่ง `{message_ids: [...]}` เรียงตาม bubble ที่ stream · ข้อ 6 เพิ่ม field ชื่อไฟล์ใน `messages` (Junior แก้ migration) path ใน Storage เป็น uuid

## Next step

ขั้น 4: เขียน UC-04 ส่งคำตอบและรับผลตรวจ (ที่มาอ่านแล้ว: ai-orchestration §2.2.5, §2.4, requirements AM-01..13, wireframe review R16, R17, R21, R24)

## Waiting on

ไม่มี

## Notes for next time

- ห้ามแก้ `requirements.md` / `api.md` (ไฟล์กลาง) ใน PR นี้ · จดเป็นข้อเสนอใน "ต้องเพิ่มใน spec" แทน เหมือน UC-01/02
