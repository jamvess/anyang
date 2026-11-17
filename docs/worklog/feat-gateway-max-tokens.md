# gateway ไม่ retry schema เมื่อคำตอบถูกตัดเพราะ MAX_TOKENS

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/gateway-max-tokens` |
| Checklist item | หลัง #140 · gateway ไม่ retry schema ด้วยงบเดิมเมื่อ provider ตัดคำตอบเพราะ `MAX_TOKENS` (retry แบบนี้ไม่มีทางผ่าน · จดไว้ใน review #15) · log สาเหตุแยกจาก schema error · ต้องเปิด `finish_reason` จาก provider (AI-01, AI-04 · พบตอนลอง `classify_material` บน Vertex 17 พ.ย. · ส่วนของ gateway: ตกลงกับ Jam) |
| Status | in progress · 2026-11-17 |

## Plan

ตอนนี้: `Gateway.call` ได้ JSON ที่ขาดเพราะ Gemini หยุดที่ `max_output_tokens` (thinking นับรวม) → `ValidationError` → retry schema 1 ครั้งด้วย `max_tokens` เท่าเดิม + prompt ยาวขึ้น (แนบคำตอบเดิม) → ขาดอีก → `AISchemaError` · เสีย 2 call และ log เป็น `schema_error` เหมือน model ตอบผิดรูป · `ProviderResponse` ไม่มี `finish_reason` · ข้อ checklist นี้อยู่ใน `docs/team/sprint-checklists.md` ของ #140 (ยังไม่ merge)

- [x] 1. 🤖 `/spec-feature` → `specs/features/ai/gateway-truncation.md` (AI-01, AI-04):
  - provider ส่ง `truncated` (Gemini: `finish_reason == MAX_TOKENS`) ใน `ProviderResponse` · fake provider ตั้งได้
  - `call`: คำตอบถูกตัดและ parse ไม่ผ่าน → ไม่ retry schema · raise error ใหม่ที่เป็นลูกของ `AISchemaError` (caller เดิมไม่ต้องแก้) · ถูกตัดแต่ parse ผ่าน → ใช้ได้ตามเดิม
  - `CallRecord.status` ค่าใหม่ `truncated` → `ai_calls.status = 'error'` (ไม่ต้องมี migration) · บรรทัด log ของ `app.ai.calls` บอก `truncated` แยกจาก schema error
  - stream (`tutor_reply` ฯลฯ): ถูกตัดกลางคำตอบ → log อย่างเดียว (ข้อความที่ส่งไปแล้วเอาคืนไม่ได้) · ตัดสินตอน review
  - เสนอ 1 บรรทัดใน `specs/system/ai-orchestration.md` §2.10 "Output" (spec ระบบ · ถามก่อน)
  - → 🙋 Jam review spec
- [x] 2. 🤖 `/spec-to-tests` (unit · fake provider · Gemini response จำลอง) → 🙋 Jam review test
- [ ] 3. 🤖 `/implement-feature` จน green · ruff · pytest ทั้งชุด
- [ ] 4. 🤖 + 🙋 test แบบ `@pytest.mark.live` (ไม่เข้า CI): เรียก Gemini บน Vertex ด้วย `max_tokens` เล็กมาก → ได้ error ใหม่หลัง provider call 1 ครั้ง · Jam รันด้วย ADC ของตัวเอง (`gcloud auth application-default login` ทำไว้แล้ว)
- [ ] 5. 🤖 จดผลลง spec

## Definition of done

- คำตอบที่ถูกตัดเพราะ `MAX_TOKENS` ไม่ถูก retry schema · เรียก provider 1 ครั้ง · caller ได้ error ที่ยังจับด้วย `AISchemaError` ได้
- log และ `CallRecord` แยกได้ว่าเป็น "ถูกตัด" ไม่ใช่ schema error · ตาราง `ai_calls` ไม่ต้องแก้
- test จาก AC ผ่าน · test เดิมผ่านโดยไม่แก้ · ruff, pytest, CI เขียว · live test ผ่านบน Vertex

## Decisions

- 2026-11-17 · ทำก่อน #140 merge ได้ เพราะไม่แตะไฟล์ของ #140 (gateway, providers, `ai_calls.py`)
- 2026-11-17 · ไม่เพิ่มคอลัมน์ใน `ai_calls` (ต้องมี migration และ `db push` ของ Junior) · ใช้ `status = 'error'` เดิม + บรรทัด log · ถ้าอยากเก็บสาเหตุใน DB ให้ Junior ตัดสินทีหลัง

## Next step

ข้อ 2 รอ Jam review test (19 test ใหม่ · 14 แดง 5 ผ่านอยู่แล้ว · live 1 ตัว) · ok แล้วทำข้อ 3 `/implement-feature`

## Waiting on

ไม่มี

## Notes for next time

- integration test ของ API ในเครื่องรันไม่ได้ (`anyang-dev` ตอบ "Unregistered API key") · ใช้ unit test + CI
