# Stub router ห้องติว 4 endpoint ตาม api.md v1.2 (D5)

| | |
|---|---|
| Owner | Junior |
| Branch | `feat/room-api-stubs` |
| Checklist item | เขียน router หัวฟังก์ชันของทุก API ใน `specs/system/api.md` ให้หน้า `/docs` ครบ (D5) |
| Status | in progress · 2026-10-20 · ต่อจาก `docs/api-tutor-room` (PR #35) · May รอใช้ทำ HTTP transport |

## Plan

- [x] 1. 🤖 เขียน test ที่ยัง fail จาก api.md v1.2 (`apps/api/tests/unit/test_room_api_contract.py`): 4 path อยู่ใน OpenAPI, field ของ `Room` / `Message` / `Limits` ตรง spec, response และ SSE event ผ่าน model, `X-Stub: true`, body ของ `POST /sessions/{id}/messages` แบบเดิม (`{text}` หรือ `{image_path}` อย่างใดอย่างหนึ่ง), 422 / 404 อยู่ในรูป `{"error": {code, message}}`
- [x] 2. 🙋 Junior review test (อ่านไฟล์ test ที่ Claude สรุปให้ ตอบ ok หรือบอกข้อที่อยากแก้) · หลัง ok ห้ามแก้ test
- [x] 3. 🤖 `app/models/room.py` (Pydantic) + `app/routers/room.py` (stub จาก fixture ใน `app/stubs/`) + error handler กลางใน `app/main.py` · `uv run pytest` เขียว + `ruff check` / `ruff format --check` ผ่าน
- [ ] 4. 🙋 Junior เปิด `/docs` ดูด้วยตา: รัน `! cd apps/api && uv run fastapi dev app/main.py` → เปิด http://localhost:8000/docs → ต้องเห็นกลุ่ม **room** มี 4 endpoint → กด `GET /sessions/{id}` → Schemas ด้านล่างต้องมี `Room`, `Message`, `Limits` → Ctrl+C ปิด server
- [ ] 5. 🤖 อัปเดต checklist (sub-bullet ใต้ข้อ D5: ห้องติว 4 endpoint เสร็จ) · PR ready · ขอ review จาก May (รูปร่างที่ `pnpm gen:api` จะได้)

## Definition of done

- `/docs` แสดง 4 endpoint ของห้องติว (`GET /exam-preps/{id}/sessions/active`, `POST /exam-preps/{id}/sessions`, `GET /sessions/{id}`, `POST /sessions/{id}/messages`) พร้อม schema ตาม api.md v1.2
- test ที่ review แล้วผ่าน · CI (`api`, `api-integration`, `web`) เขียว
- ไม่มี business logic, ไม่แตะ DB, ไม่เรียก AI · body ของ `POST /messages` ยังเป็นแบบเดิมจนกว่า Jam ตัดสิน "รอตัดสิน" ข้อ 1

## Decisions

- 2026-10-20 · แก้ schema 422/404 ใน PR นี้ (Junior) · ใช้ `ErrorResponse` แทน `HTTPValidationError` เพื่อให้ `pnpm gen:api` ได้ type ที่ถูก · test ใหม่อยู่ใน `test_openapi_error_schema.py` (ไม่แตะ test ที่ล็อกแล้ว)
- 2026-10-20 · fixture ของ stub: โจทย์เปลี่ยนเป็น `x^2 - 49` · `progress_card.topics` มี 4 หัวข้อ ใช้ชุดเดียวกับ card ใน `room.json`
- 2026-10-20 · Junior review test แล้ว (ok) · test 2 ไฟล์ล็อกแล้ว ห้ามแก้

- 2026-10-20 · stub คืนข้อมูลจาก fixture ไม่ใช่ 501 (Junior เลือก) · 501 ไม่ช่วย May ต่อ HTTP transport เกินกว่า type ที่มีใน spec อยู่แล้ว · ของจริงคือ P4-lite (S3) ผ่าน spec flow ของมันเอง
  - `GET /exam-preps/{id}/sessions/active` → `{session_id}` จาก fixture · `GET /sessions/{id}` → `Room` จาก `session-s15.json` ของ May (+ `session_id`, `card`)
  - `POST /exam-preps/{id}/sessions` และ `POST /sessions/{id}/messages` → stream fixture SSE ของ May เป็น `text/event-stream` จริง · stream ของ POST sessions เริ่มด้วย event `session` · ทุก stream จบด้วย `done`
  - ทั้ง 4 endpoint มี header `X-Stub: true` และ docstring "stub — replaced in P4-lite"
  - test ตรวจว่า response ผ่าน model ของ api.md v1.2 ไม่ตรวจค่าใน fixture ตรงๆ · test 422 และรูป error ยังอยู่ตามแผน
- 2026-10-20 · fixture ของ stub copy ไว้ที่ `apps/api/app/stubs/` · Docker copy แค่ `apps/api/app/` จึงอ่าน `apps/web/tests/` ตอน deploy ไม่ได้ และ `apps/web/` เป็นของ May
- 2026-10-20 · `limits` ใน `Room` อ่านจาก `config/ai.yaml` → `guards` ไม่ใช้ค่าใน fixture (กฎ no magic numbers)
- 2026-10-20 · `limits.max_image_mb` เป็น integer ตาม api.md · เปลี่ยน `GuardsConfig.max_image_mb` เป็น `int` (B1)
- 2026-10-20 · body ของ `POST /messages` ใช้แบบเดิม `{text}` หรือ `{image_path}` · "รอตัดสิน" ข้อ 1 ยังไม่มีคนตอบ (PR #35 merge โดยไม่ได้ตอบ)

## Next step

ขั้น 4 (🙋): Junior รัน `! cd apps/api && uv run fastapi dev app/main.py` แล้วเปิด http://localhost:8000/docs ดูกลุ่ม room 4 endpoint + schema `Room`, `Message`, `Limits` และ event models · ตอบ ok แล้วไปขั้น 5

หลัง PR นี้ merge: เปิด PR เล็กแยก (`docs/api-progress-card-topics`) แก้ api.md (ไฟล์ร่วม · บอกแชทกลุ่ม) กำหนด type ของ `progress_card.topics[]`: `stars` int 1–3, `level` จาก `config/learning.yaml` → `levels.show`, `review_due` bool, `origin` `"doc" | "user"` · ตอนนี้แค่เดาไว้ใน `app/stubs/` · ต้องถามด้วยว่าหัวข้อ 0 ดาวแสดงใน card ไหม (`topics.importance` ใน DB เป็น 0–3 และ `readiness.exclude_zero_star`)

## Waiting on

- 🙋 May: review api.md v1.2 ย้อนหลัง (PR #35 merge ก่อนที่ May จะ review) · "รอตัดสิน" ข้อ 3, 5, 6
- 🙋 Jam: "รอตัดสิน" ข้อ 1

## Notes for next time

- `pnpm gen:api` เขียนลง `apps/web/lib/api-schema.ts` ซึ่งเป็นของ May · อย่า commit ไฟล์นั้นจาก branch นี้
- fixture SSE ของ May (`session_start.txt`) ใช้ `problem.purpose = "check"` ซึ่งไม่อยู่ใน check ของ DB (`probe` / `verify` / `practice` / `review`) · copy ฝั่ง backend ใช้ `probe` · ต้องบอก May
- api.md ไม่ได้กำหนด type ของ field ใน `progress_card.topics[]` (`stars`, `level`, `review_due`, `origin`) · test ตรวจแค่ระดับบนของ `progress_card`
- test แยก 2 ไฟล์: `test_room_api_contract.py` = ที่ endpoint จริงต้องผ่านด้วย · `test_room_stubs.py` = เฉพาะ stub (`X-Stub`) **ลบทิ้งใน P4-lite**
- event model ทุกตัวต้องอยู่ใน `components.schemas` ไม่งั้น `pnpm gen:api` ไม่สร้าง type ให้ May · FastAPI ไม่ใส่ model ที่ไม่มี endpoint อ้างถึง ต้องอ้างผ่าน `responses` ของ endpoint SSE
- path parameter ใน router ใช้ `{id}` ตาม api.md ผ่าน `Path(alias="id")` (test อ้าง path แบบ `/sessions/{id}`)
- 500 ที่ไม่ได้ดัก (exception ที่หลุดออกมา) ยังไม่ตอบในรูป `{"error": {code, message}}` · ทำใน P4-lite
- type ของ field ใน `progress_card.topics[]` ใน `app/stubs/` (`stars` int, `level` จาก `learning.yaml` → `levels.show`, `review_due` bool, `origin` doc/user) เป็นค่าที่เดาไว้สำหรับ stub · api.md ยังไม่ได้กำหนด
