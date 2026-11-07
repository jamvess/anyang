# ปิดช่อง `</message>` ใน prompt ของ `tutor_reply`

| | |
|---|---|
| Owner | Jam |
| Branch | `fix/tutor-reply-message-escape` |
| Checklist item | ไม่มีข้อตรง · พบตอน self-review ของ PR #109 |
| Status | in progress · 2026-11-07 |

## Plan

- [x] 1. 🤖 เพิ่ม AC ใน `specs/features/tutor/tutor-reply-stream.md` + test ให้แดงก่อน
- [x] 2. 🙋 Jam review AC และ test
- [ ] 3. 🤖 ย้าย `_as_data` ของ `services/checker.py` เป็น helper ใช้ร่วม แล้วใช้ใน `tutor_turn` · test เขียว · test เดิมของ checker ผ่าน

## Definition of done

- ข้อความผู้ใช้ที่มี `</message>` ไม่ปิด tag ก่อนเวลา ทุกรูปแบบที่ `<document>` กันอยู่แล้ว
- ข้อความปกติถึง model เหมือนเดิมทุกตัวอักษร
- ไม่แก้ `prompts/tutor_reply/v1.md` · test + ruff + CI เขียว

## Decisions

- 2026-11-07 · แก้ที่โค้ดไม่แก้ prompt · prompt ไม่เปลี่ยนจึงไม่ต้องขึ้น version และไม่ต้องรัน eval (`prompts/README.md` กฎ 1–2) · ยังไม่มี eval ของ `tutor_reply`

## Next step

ขั้น 2: Jam review AC-23, AC-24 และ `test_tutor_reply_message_tag.py`

## Waiting on

ไม่มี

## Notes for next time

- `services/checker.py` `_as_data` escape `</document` อยู่แล้ว (test: `test_check_answer_pipeline.py`) · `tutor_turn` ไม่ได้ใช้
