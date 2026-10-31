# Endpoint SSE ห้องติวที่ stream จาก gateway (P4-lite)

| | |
|---|---|
| Owner | Jam (item of Junior) |
| Branch | `feat/tutor-reply-stream` |
| Checklist item | Endpoint SSE `POST /sessions/{id}/messages` ที่ stream จาก gateway (P4-lite) |
| Status | in progress · 2026-10-31 |

## Plan

- [ ] 1. 🤖 `/spec-feature`: ร่าง `specs/features/tutor/tutor-reply-stream.md` (AI-01, AI-02, AI-03, NFR-P1, TM-08) · ขอบเขต P4-lite ตาม `specs/poc/README.md`: ข้อความ user → `tutor_reply` (stream) → event `token` → `done` · ไม่มี stage machine, planner, buddy (เทอม 2) · มีส่วน "รอตัดสิน" แยกข้อที่เป็นของ Junior (auth, การบันทึก `messages`) ออกจากข้อที่เป็นของ Jam (prompt, gateway stream)
- [ ] 2. 🙋 Jam review spec: อ่าน AC ทุกข้อ + ตัดสินข้อที่เป็นของ Jam · ข้อของ Junior ใช้ทางที่ไม่ล็อกโครงสร้าง backend แล้วจดใน Waiting on
- [ ] 3. 🤖 `/spec-to-tests`: test ที่ fail ก่อน (fake provider, ไม่เรียก model จริง)
- [ ] 4. 🙋 Jam review test (ชื่อ test ตรง AC · ไม่มี test ที่เรียก model จริงใน CI)
- [ ] 5. 🤖 `/implement-feature`: gateway `stream()` + provider fake/gemini + prompt `tutor_reply/v1` + service + router (สัญญาเดิมของ `test_room_api_contract.py` ต้องผ่าน)
- [ ] 6. 🙋 Jam smoke test ในเครื่องกับ Vertex: `cd apps/api` → `AI_PROVIDER=live uv run fastapi dev app/main.py` → ส่งข้อความจากหน้าแชท `pnpm dev` (http://localhost:3000) → ต้องเห็นตัวอักษรไหลออกมาและสมการ render · ใช้ ADC + `GOOGLE_CLOUD_PROJECT` ใน `.env` ของ Jam
- [ ] 7. 🙋 Jam บอกแชทกลุ่ม (solo time · `apps/api/` ของ Junior · `config/ai.yaml` ถ้าแตะ · `api.md` ถ้าต้องแก้)

## Definition of done

- `POST /sessions/{id}/messages` stream คำตอบจาก `ai.stream("tutor_reply")` ผ่าน gateway (AI-01) เป็น event `token` แล้วจบด้วย `done` ตาม `api.md` "SSE events"
- `AI_PROVIDER=fake` ผ่าน test ทั้งหมดโดยไม่แก้ code (AI-02, AI-03) · `test_room_api_contract.py` ยังผ่าน
- ขอบเขตการบันทึก `messages` และ JWT ตามที่ Junior ตัดสิน หรือจดไว้ใน Waiting on
- staging ยังเป็น `AI_PROVIDER=fake` จนกว่าจะเช็ค JWT ครบ (⚠️ ใน checklist 28 ต.ค.)
- `uv run ruff check .` + `uv run pytest` ผ่าน · CI เขียว
- ตรงกับ checklist: "Endpoint SSE `POST /sessions/{id}/messages` ที่ stream จาก gateway (P4-lite)"

## Decisions

## Next step

ขั้น 1 (🤖): รัน `/spec-feature` สำหรับ `specs/features/tutor/tutor-reply-stream.md`

## Waiting on

- Junior: ตรวจ JWT ของ Supabase และการบันทึก `messages` (โครงสร้าง backend + DB เป็นของ Junior ตาม `roles.md`) · ข้อเสนอจะอยู่ในส่วน "รอตัดสิน" ของ spec

## Notes for next time

- gateway มีแค่ `call` (คืนก้อนเดียว + validate schema) · ยังไม่มี stream · provider protocol มีแค่ `generate`
- `app/db/` ว่าง · ยังไม่มี middleware ตรวจ JWT · stub ปัจจุบันอยู่ที่ `app/routers/room.py` + `app/stubs/tutor_reply.sse`
- ⚠️ ห้ามเปิด `AI_PROVIDER=live` บน api-staging จนกว่าจะเช็ค JWT ทุก endpoint (URL เป็น public)
