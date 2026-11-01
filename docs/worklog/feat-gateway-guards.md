# Rate limit ของห้องติว + circuit breaker ของ gateway

| | |
|---|---|
| Owner | Jam (item of Junior) |
| Branch | `feat/gateway-guards` |
| Checklist item | วัด TTFT และต้นทุนบน staging ร่วมกับ May (P4-lite) |
| Status | in progress · 2026-11-01 |

## Plan

ส่วนที่ทำได้ของ checklist item: กัน 2 อย่างที่ทำให้เปิด `AI_PROVIDER=live` บน `api-staging` ไม่ได้ (architecture.md v1.2 "สร้างแล้วหรือยัง") · ยังไม่ได้วัด TTFT บน staging ในงานนี้

- [x] 1. 🤖 `/spec-feature ai/gateway-guards TM-21 NFR-R1 NFR-P2`: (ก) จำกัด `guards.rate_limit_messages_per_minute` ต่อ user บน endpoint ที่เรียก AI ของห้องติว (ai-orchestration §2.9 Limits) (ข) circuit breaker ใน gateway (§2.10: error ≥ 50% จากอย่างน้อย 10 calls → พัก 60 วินาที) · ไม่มี provider สำรอง จึงล้มทันทีแล้ว degrade
- [x] 2. 🙋 Jam review spec + ตอบ open questions (threshold เป็นเรื่องของ Jam · โครงสร้าง backend เป็นของ Junior → เขียนเป็นข้อเสนอ)
- [x] 3. 🙋 ถ้าต้องเพิ่มค่าใน `config/ai.yaml` (ไฟล์ร่วม) บอกแชทกลุ่ม
- [x] 4. 🤖 `/spec-to-tests` · แดงก่อน
- [x] 5. 🙋 Jam review test
- [x] 6. 🤖 `/implement-feature` · test เขียว + ruff
- [x] 7. 🤖 อัปเดตแถว gateway ใน `architecture.md` + บรรทัดความคืบหน้าใน checklist

## Definition of done

- spec `specs/features/ai/gateway-guards.md` approved · AC ทุกข้อมี test ที่ผ่าน
- ค่าทุกตัวอ่านจาก `config/ai.yaml` พร้อมป้ายที่มา (ไม่มี magic number)
- CI เขียว · checklist item ยังไม่ติ๊ก (ยังไม่ได้วัดบน staging)

## Decisions

- 2026-11-01 · Jam approve spec: OQ 1–6 ตามข้อเสนอ (ไม่มี token นับต่อ IP ไว้ก่อน · ยังไม่นับ `POST /exam-preps/{id}/sessions` · body ผิดก็นับ · เก็บในหน่วยความจำต่อ instance · half-open ปล่อย 1 call · call ที่ breaker ปฏิเสธไม่ลง `ai_calls`)
- 2026-11-01 · ไม่ต้องแก้ `config/ai.yaml`: `gateway.circuit_breaker` (4 ค่า · [B] Resilience4j) และ `guards.rate_limit_messages_per_minute` มีอยู่แล้ว · ขั้น 3 จึงข้าม
- 2026-11-01 · ทำ rate limit + circuit breaker ก่อน answer-leak check (AM-13) เพราะ leak check ต้องมีโจทย์ที่ค้างอยู่ ซึ่งยังไม่มีใน flow จริง

## Next step

ทุกขั้นเสร็จแล้ว · `/work-done` (บอกแชทกลุ่มก่อน merge เพราะแก้ api.md)

## Done today

- 2026-11-01 · ขั้น 4: test 42 ตัว (`test_rate_limit.py`, `test_circuit_breaker.py`) + fixture ล้างตัวนับใน `tests/conftest.py` · แดงก่อน (`ModuleNotFoundError`)
- 2026-11-01 · ขั้น 6: `app/rate_limit.py` (dependency `chat_rate_limit` บน `/messages` และ `/ocr/confirm`), `app/ai/circuit_breaker.py`, `Gateway(clock=)` + `gateway.breaker()` · 4 รอบ red → green · unit 576 ผ่าน
- 2026-11-01 · test ที่ review แล้วล้ม 1 ตัว (`test_apimd_room_media_endpoints_and_errors_in_openapi` ของ `/ocr/confirm` ตรวจชุด error พอดี) · Jam อนุญาตให้เพิ่ม `429` · api.md v1.8 + architecture.md (Jam อนุญาตแก้ไฟล์ร่วม)

## Waiting on

- Junior: ยืนยันโครงสร้าง backend ของ rate limit (เก็บในหน่วยความจำต่อ instance หรือใน DB) · ตั้ง env ของ `api-staging` (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `AUTH_REQUIRED`) + runtime SA ก่อนเปิด live
- May: หน้าเว็บ login + ส่ง token (ไม่งั้น rate limit นับต่อ user ไม่ได้)

## Notes for next time

- 
