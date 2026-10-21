# X-Request-Id middleware + error envelope ของ 500 (issue #50)

| | |
|---|---|
| Owner | Junior |
| Branch | `fix/api-request-id-errors` |
| Checklist item | ไม่มีใน checklist · issue #50 |
| Status | in progress · 2026-10-21 |

## Plan

- [ ] 1. 🤖 เขียน test จาก api.md Conventions (Request ID, Error) + issue #50 → `tests/unit/test_request_id_and_500.py` (ตอนนี้ red: ไม่มี `app.middleware`)
- [ ] 2. 🙋 Junior review test + ตอบคำถาม spec (incoming id รับเฉพาะ UUID · ขอบเขตการส่ง id ต่อไป log/`ai_calls` · ข้อความของ 500)
- [ ] 3. 🤖 implement `app/middleware.py` (pure ASGI · ไม่ใช้ `BaseHTTPMiddleware` เพราะ SSE) + `install_middleware()` ใน `main.py` · ลำดับ outer → inner: request id → CORS → ตัวดัก 500
- [ ] 4. 🤖 ruff + pytest ทั้งหมด (รวม `test_cors.py` เดิม) → push → CI
- [ ] 5. 🤖 docs: api.md Conventions (ถ้า Junior ตกลงเพิ่ม `internal_error` / กติกา incoming id · ไฟล์ shared ต้องถามก่อน) · comment ใน #50

## Definition of done

- ทุก response มี `X-Request-Id` (JSON, SSE, 404/405/422, 500, CORS preflight)
- 500 ที่ไม่ได้ดักตอบ `{"error": {"code": "internal_error", "message": ...}}` ไม่มีข้อความของ exception · ยังมี `Access-Control-Allow-Origin` และ `X-Request-Id`
- exception ถูก log พร้อม traceback และ request id
- test ผ่าน · CI เขียว

## Decisions

## Next step

รอ Junior review test ในขั้น 1 และตอบคำถามขั้น 2

## Waiting on

ไม่มี

## Notes for next time

- `@app.exception_handler(Exception)` ของ Starlette ไปอยู่ที่ `ServerErrorMiddleware` ซึ่งอยู่นอกสุด (นอก CORS) จึงไม่ช่วยเรื่อง CORS header · ต้องดักใน middleware ที่อยู่ใน CORS แทน
