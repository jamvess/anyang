# X-Request-Id middleware + error envelope ของ 500 (issue #50)

| | |
|---|---|
| Owner | Junior |
| Branch | `fix/api-request-id-errors` |
| Checklist item | ไม่มีใน checklist · issue #50 |
| Status | in progress · 2026-10-21 |

## Plan

- [x] 1. 🤖 เขียน test จาก api.md Conventions (Request ID, Error) + issue #50 → `tests/unit/test_request_id_and_500.py` · red: ไม่มี `app.middleware`
- [x] 2. 🙋 Junior review test แล้ว (2026-10-21) · แก้ 1 test: SSE ที่พังหลังส่ง header ต้องส่ง `error` แล้ว `done` (api.md) · commit `2bb5c90`
- [x] 3. 🤖 implement `app/middleware.py` (pure ASGI) + `install_middleware()` ใน `main.py` · green รอบแรก (1 รอบ red → green) · ลองสลับลำดับให้ตัวดักอยู่นอก CORS แล้ว 500 ไม่มี `Access-Control-Allow-Origin` จริง (test มีความหมาย)
- [ ] 4. 🤖 ruff + pytest ทั้งหมดผ่านในเครื่อง (177 passed) · เหลือ push → CI
- [x] 5. 🤖 comment ใน #50 แล้ว: สิ่งที่ทำ · `ai_calls.request_id` ยังไม่ทำ · 2 บรรทัดที่จะใส่ใน api.md PR รอบหน้า · PR body เปลี่ยนเป็น "part of #50"

## Definition of done

- ทุก response มี `X-Request-Id` (JSON, SSE, 404/405/422, 500, CORS preflight)
- 500 ที่ไม่ได้ดักตอบ `{"error": {"code": "internal_error", "message": ...}}` ไม่มีข้อความของ exception · ยังมี `Access-Control-Allow-Origin` และ `X-Request-Id`
- exception ถูก log พร้อม traceback และ request id
- test ผ่าน · CI เขียว

## Decisions

- 2026-10-21 · `X-Request-Id` จาก client รับเฉพาะ UUID ถ้าไม่ใช่สร้างใหม่ · กันข้อความแปลกๆ เข้า log และไม่ต้องตั้งความยาวสูงสุด (Junior)
- 2026-10-21 · ขอบเขต (ก): PR นี้มีแค่ `get_request_id()` + log ของ 500 · `CallRecord.request_id` / `ai_calls` รอ gateway S3 · #50 ยังเปิดไว้ (Junior)
- 2026-10-21 · message ของ 500 เป็นภาษาอังกฤษ `"Internal server error"` เหมือน envelope อื่น · หน้าเว็บแสดงข้อความไทยเอง (room-http AC-3c, AC-7)
- 2026-10-21 · SSE ที่พังหลังส่ง header: ส่ง `error {code: "internal_error"}` แล้ว `done {}` (api.md SSE events + Conventions) · `done` ยังเป็น `{}` เพราะ `{message_ids}` ของห้องติวรอ May เลือก A/B (#36)
- 2026-10-21 · api.md ไม่แก้ใน PR นี้ · 2 บรรทัด (`internal_error`, กติกา UUID) จดใน #50 ไว้ใส่ใน api.md PR รอบหน้า
- 2026-10-21 · ตัวดักไม่ re-raise exception เพื่อไม่ให้ server log ซ้ำ · ผลคือ Sentry มองไม่เห็นโดย default · ตอนเพิ่ม Sentry ใช้ `LoggingIntegration` หรือ `capture_exception()` ในตัวดัก (จดใน #50)
- 2026-10-21 · log ของ 500 ส่ง exception ตัวเดิมเป็น `exc_info` (ถ้าเป็น ExceptionGroup จะเห็น traceback ทุกตัว) · `_root_cause` ใช้แค่บรรทัดสรุป (Junior)

## Next step

ดู CI ของ PR #58 · ถ้าเขียว ให้ Junior พิมพ์ `/work-done`

## Waiting on

ไม่มี

## Notes for next time

- `@app.exception_handler(Exception)` ของ Starlette ไปอยู่ที่ `ServerErrorMiddleware` ซึ่งอยู่นอกสุด (นอก CORS) จึงไม่ช่วยเรื่อง CORS header · ต้องดักใน middleware ที่อยู่ใน CORS แทน
