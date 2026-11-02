# Contract + stub ของ endpoint ที่เหลือของห้องติว (D5 · ส่วนที่ 3)

| | |
|---|---|
| Owner | Jam (item of Junior) |
| Branch | `feat/room-rest-stubs` |
| Checklist item | เขียน router หัวฟังก์ชันของทุก API ใน `specs/system/api.md` ให้หน้า `/docs` ครบ (D5) |
| Status | in progress · 2026-11-02 |

## Plan

4 endpoint สุดท้ายของห้องติวใน api.md: `POST /sessions/{id}/end`, `GET /sessions/{id}/messages`, `GET /exam-preps/{id}/progress`, `GET /messages/{id}/tts`

- [x] 1. 🤖 ร่าง contract (ข้อเสนอรอ Junior) จาก api.md (`Message`, `progress_card`, `session_end`), ai-orchestration §2.2.9 และ `tutor_sessions` ใน `0001_init.sql`
- [x] 2. 🙋 Jam อ่านร่าง ตอบ ok · บอกแชทกลุ่มว่าจะแก้ `api.md` (ไฟล์ร่วม)
- [x] 3. 🤖 ใส่ร่างลง `api.md` v1.9 + "รอตัดสิน (v1.9 · Junior)"
- [x] 4. 🤖 test contract + stub · แดงก่อน
- [ ] 5. 🙋 Jam review test
- [ ] 6. 🤖 models + stub (`X-Stub: true`) · test เขียว + ruff
- [ ] 7. 🤖 `api-schema.ts` generate ใหม่ + บรรทัดความคืบหน้าใน checklist

## Definition of done

- `api.md` มี request/response/error ของ 4 endpoint · ข้อที่ยังไม่ตัดสินอยู่ใน "รอตัดสิน (v1.9 · Junior)"
- `/docs` แสดงครบ · stub ส่ง `X-Stub: true` · test + ruff + CI เขียว
- ข้อ D5 ยังไม่ติ๊ก (ยังเหลือกลุ่ม exam prep + materials, persona, บัญชี)

## Decisions

- 2026-11-02 · ทำกลุ่มห้องติวให้ครบก่อน เพราะรูปร่างส่วนใหญ่มีใน api.md อยู่แล้ว จึงเดาน้อยกว่ากลุ่ม exam prep

## Next step

ขั้น 5: Jam review `tests/unit/test_room_rest_api_contract.py` + `test_room_rest_stubs.py` · แล้วขั้น 6 models + stub

## Waiting on

- Junior: ตัดสิน contract (รอตัดสิน v1.9)
- May: `pnpm gen:api` แล้วใช้ type ใหม่ (ประวัติแชท, progress card, จบ session)

## Notes for next time

- แบบของ stub: `app/routers/room.py` (PR #38, #102), `app/routers/scope.py` (PR #100)
