# Endpoint SSE ห้องติวที่ stream จาก gateway (P4-lite)

| | |
|---|---|
| Owner | Jam (item of Junior) |
| Branch | `feat/tutor-reply-stream` |
| Checklist item | Endpoint SSE `POST /sessions/{id}/messages` ที่ stream จาก gateway (P4-lite) |
| Status | in progress · 2026-10-31 |

## Plan

- [x] 1. 🤖 `/spec-feature`: ร่าง `specs/features/tutor/tutor-reply-stream.md` (AI-01, AI-02, AI-03, NFR-P1, TM-08) · ขอบเขต P4-lite ตาม `specs/poc/README.md`: ข้อความ user → `tutor_reply` (stream) → event `token` → `done` · ไม่มี stage machine, planner, buddy (เทอม 2) · มีส่วน "รอตัดสิน" แยกข้อที่เป็นของ Junior (auth, การบันทึก `messages`) ออกจากข้อที่เป็นของ Jam (prompt, gateway stream)
- [x] 2. 🙋 Jam review spec: อ่าน AC ทุกข้อ + ตัดสินข้อที่เป็นของ Jam · ข้อของ Junior ใช้ทางที่ไม่ล็อกโครงสร้าง backend แล้วจดใน Waiting on
- [x] 3. 🤖 `/spec-to-tests`: test ที่ fail ก่อน (fake provider, ไม่เรียก model จริง)
- [x] 4. 🙋 Jam review test (ชื่อ test ตรง AC · ไม่มี test ที่เรียก model จริงใน CI)
- [x] 5. 🤖 `/implement-feature`: gateway `stream()` + provider fake/gemini + prompt `tutor_reply/v1` + service + router (สัญญาเดิมของ `test_room_api_contract.py` ต้องผ่าน)
- [x] 6. 🙋 Jam smoke test ในเครื่องกับ Vertex: `cd apps/api` → `AI_PROVIDER=live uv run fastapi dev app/main.py` → ส่งข้อความจากหน้าแชท `pnpm dev` (http://localhost:3000) → ต้องเห็นตัวอักษรไหลออกมาและสมการ render · ใช้ ADC + `GOOGLE_CLOUD_PROJECT` ใน `.env` ของ Jam
- [ ] 7. 🙋 Jam บอกแชทกลุ่ม (solo time · `apps/api/` ของ Junior · `config/ai.yaml` ถ้าแตะ · `api.md` ถ้าต้องแก้)

## Definition of done

- `POST /sessions/{id}/messages` stream คำตอบจาก `ai.stream("tutor_reply")` ผ่าน gateway (AI-01) เป็น event `token` แล้วจบด้วย `done` ตาม `api.md` "SSE events"
- `AI_PROVIDER=fake` ผ่าน test ทั้งหมดโดยไม่แก้ code (AI-02, AI-03) · `test_room_api_contract.py` ยังผ่าน
- ขอบเขตการบันทึก `messages` และ JWT ตามที่ Junior ตัดสิน หรือจดไว้ใน Waiting on
- staging ยังเป็น `AI_PROVIDER=fake` จนกว่าจะเช็ค JWT ครบ (⚠️ ใน checklist 28 ต.ค.)
- `uv run ruff check .` + `uv run pytest` ผ่าน · CI เขียว
- ตรงกับ checklist: "Endpoint SSE `POST /sessions/{id}/messages` ที่ stream จาก gateway (P4-lite)"

## Decisions

- 2026-10-31 · Jam approve spec `tutor-reply-stream.md` และรับข้อเสนอทุกข้อใน §10
- §10 ข้อ 2 · `{image_path}` คง stub · flow รูปเป็น feature แยก
- §10 ข้อ 4 · fake ตอบด้วยข้อความ tutor ของ `app/stubs/tutor_reply.sse` ตัด buddy · tutor_reply ใน P4-lite ไม่มี buddy
- §10 ข้อ 5 · เอากรณี `{text}` ออกจาก `test_apimd_room_stubs_send_x_stub_header` · docstring ของ `test_room_stubs.py` บอกไว้แล้วว่าลบใน P4-lite
- §10 ข้อ 6 · ยังไม่มี timeout แยกของ token แรก · ดูผลวัด P4-lite ก่อน
- 2026-10-31 · Jam review test แล้ว (2 ไฟล์ใหม่ + `test_room_stubs.py` เปลี่ยนกรณี `{text}` เป็น `{image_path}`)

## Next step

ขั้น 7 (🙋): Jam ส่งข้อความแชทกลุ่ม (solo time + `config/ai.yaml` 1.5 + แก้ test ของ Junior + Waiting on 2 ข้อ) แล้วรัน `/work-done`

- 2026-10-31 · implement: `Gateway.stream` + `get_gateway` (FastAPI dependency) + `ai.stream` · provider protocol `stream(request, usage)` · fake แบ่งข้อความเป็นทีละคำ (เว้นวรรคติดไปกับคำ) และมี `defaults` ให้ตอบซ้ำได้ทุกข้อความใน fake mode · red → green 3 รอบ (gateway + fake · Gemini · endpoint)
- 2026-10-31 · เพิ่ม live smoke `test_AI01_vertex_streams_tutor_reply` ใน `tests/integration/test_vertex_live.py` (อยู่ใน test plan §8 แต่ตกไปตอน `/spec-to-tests`) · ต้องให้ Jam review

- 2026-10-31 · smoke บน Vertex (`test_AI01_vertex_streams_tutor_reply`, 1 ข้อความ, จากเครื่อง Jam): (1) default thinking + `max_tokens` 700 → TTFT 5,160 ms, ชนเพดาน 696/700 คำตอบถูกตัด (2) `thinking: low` + 700 → TTFT 4,350 ms ยังชนเพดาน (3) `thinking: low` + 2000 → TTFT 3,656 ms, tokens_out 666, คำตอบครบ 5 chunk · `config/ai.yaml` 1.5 (Jam ok)
- 2026-10-31 · TTFT ยังเกินเป้า 2 s (NFR-P1) · Jam: ไม่ block งานนี้ ให้ report P4-lite วัดบน staging แล้วตัดสิน
- 2026-10-31 · ข้ามส่วน ข (ลองในเบราว์เซอร์) · API ส่ง event รูปแบบเดิม และหน้าเว็บมี test ของ chunk ที่ตัดกลางสมการแล้ว (`chat-streaming.md` AC-9, AC-11)

## Waiting on

- Junior: §10 ข้อ 1 ของ spec · P4-lite ยังไม่ตรวจ JWT และไม่บันทึก `messages` (ใช้ข้อเสนอไปก่อน)
- Junior: §10 ข้อ 3 · `error.code` `message_too_long` (422) และ `ai_unavailable` (กลาง stream) · ยังไม่แก้ `api.md` จนกว่า Junior ตกลง

## Notes for next time

- gateway มีแค่ `call` (คืนก้อนเดียว + validate schema) · ยังไม่มี stream · provider protocol มีแค่ `generate`
- `app/db/` ว่าง · ยังไม่มี middleware ตรวจ JWT · stub ปัจจุบันอยู่ที่ `app/routers/room.py` + `app/stubs/tutor_reply.sse`
- ⚠️ ห้ามเปิด `AI_PROVIDER=live` บน api-staging จนกว่าจะเช็ค JWT ทุก endpoint (URL เป็น public)
