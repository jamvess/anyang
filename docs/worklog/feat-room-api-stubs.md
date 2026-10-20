# Stub router ห้องติว 4 endpoint ตาม api.md v1.2 (D5)

| | |
|---|---|
| Owner | Junior |
| Branch | `feat/room-api-stubs` |
| Checklist item | เขียน router หัวฟังก์ชันของทุก API ใน `specs/system/api.md` ให้หน้า `/docs` ครบ (D5) |
| Status | in progress · 2026-10-20 · ต่อจาก `docs/api-tutor-room` (PR #35) · May รอใช้ทำ HTTP transport |

## Plan

- [ ] 1. 🤖 เขียน test ที่ยัง fail จาก api.md v1.2 (`apps/api/tests/unit/test_room_api_contract.py`): 4 path อยู่ใน OpenAPI, field ของ `Room` / `Message` / `limits` ตรง spec, body ของ `POST /sessions/{id}/messages` แบบเดิม (`{text}` หรือ `{image_path}` อย่างใดอย่างหนึ่ง), ทุก stub ตอบ 501 ในรูป `{"error": {code, message}}`, 422 ก็ใช้รูปเดียวกัน
- [ ] 2. 🙋 Junior review test (อ่านไฟล์ test ที่ Claude สรุปให้ ตอบ ok หรือบอกข้อที่อยากแก้) · หลัง ok ห้ามแก้ test
- [ ] 3. 🤖 `app/models/room.py` (Pydantic) + `app/routers/room.py` (stub 501) + error handler กลางใน `app/main.py` · `uv run pytest` เขียว + `ruff check` / `ruff format --check` ผ่าน
- [ ] 4. 🙋 Junior เปิด `/docs` ดูด้วยตา: รัน `! cd apps/api && uv run fastapi dev app/main.py` → เปิด http://localhost:8000/docs → ต้องเห็นกลุ่ม **room** มี 4 endpoint → กด `GET /sessions/{id}` → Schemas ด้านล่างต้องมี `Room`, `Message`, `Limits` → Ctrl+C ปิด server
- [ ] 5. 🤖 อัปเดต checklist (sub-bullet ใต้ข้อ D5: ห้องติว 4 endpoint เสร็จ) · PR ready · ขอ review จาก May (รูปร่างที่ `pnpm gen:api` จะได้)

## Definition of done

- `/docs` แสดง 4 endpoint ของห้องติว (`GET /exam-preps/{id}/sessions/active`, `POST /exam-preps/{id}/sessions`, `GET /sessions/{id}`, `POST /sessions/{id}/messages`) พร้อม schema ตาม api.md v1.2
- test ที่ review แล้วผ่าน · CI (`api`, `api-integration`, `web`) เขียว
- ไม่มี business logic, ไม่แตะ DB, ไม่เรียก AI · body ของ `POST /messages` ยังเป็นแบบเดิมจนกว่า Jam ตัดสิน "รอตัดสิน" ข้อ 1

## Decisions

- 2026-10-20 · stub ตอบ 501 `not_implemented` แทนข้อมูลปลอม · ของจริงคือ P4-lite (S3) ซึ่งต้องผ่าน spec flow ของมันเอง · May ใช้ schema จาก `/openapi.json` ได้เลย ส่วนข้อมูลยังใช้ fixture
- 2026-10-20 · body ของ `POST /messages` ใช้แบบเดิม `{text}` หรือ `{image_path}` · "รอตัดสิน" ข้อ 1 ยังไม่มีคนตอบ (PR #35 merge โดยไม่ได้ตอบ)

## Next step

เริ่มขั้น 1: เขียน `apps/api/tests/unit/test_room_api_contract.py` จาก api.md v1.2 หัวข้อ "ห้องติว" และ "SSE events"

## Waiting on

- 🙋 May: review api.md v1.2 ย้อนหลัง (PR #35 merge ก่อนที่ May จะ review) · "รอตัดสิน" ข้อ 3, 5, 6
- 🙋 Jam: "รอตัดสิน" ข้อ 1

## Notes for next time

- `GuardsConfig.max_image_mb` ใน `app/settings.py` เป็น `float` แต่ api.md เขียน `limits.max_image_mb` เป็น integer · ต้องเลือกก่อนขั้น 1 (ดูคำถามในแชท 20 ต.ค.)
- `pnpm gen:api` เขียนลง `apps/web/lib/api-schema.ts` ซึ่งเป็นของ May · อย่า commit ไฟล์นั้นจาก branch นี้
