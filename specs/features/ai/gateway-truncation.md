# Feature: gateway ไม่ retry schema เมื่อคำตอบถูกตัดเพราะ MAX_TOKENS

| | |
|---|---|
| Area | platform (AI gateway) |
| Requirements | AI-01 (ทุก call ผ่าน provider layer · provider บอกเหตุที่หยุดผ่าน interface กลาง ไม่ให้ส่วนอื่นอ่าน SDK เอง) · AI-04 (log ทุก call · แยกสาเหตุ "ถูกตัด" ออกจาก schema error) |
| Owner | Jam |
| Reviewer | Jam · Junior ดูย้อนหลัง (บรรทัด log ของ `app.ai.calls` · ไม่แตะตาราง `ai_calls`) |
| Status | approved 2026-11-17 (Jam ok spec · §10 ข้อ 1 และ 3 ตามข้อเสนอ) |
| Related system spec | ai-orchestration.md §2.10 "Output" (schema retry 1 ครั้ง) · `config/ai.yaml` `gateway.schema_retries`, `purposes.*.max_tokens`, `thinking` · `ai-calls-log.md` §2.2 (map `status`), §2 ข้อ 1 (บรรทัด log) · `gateway-guards.md` §2.2 (circuit breaker: อะไรนับเป็นล้ม) · `gemini-vertex.md` · checklist ของ #140 "หลัง #140 · gateway ไม่ retry schema ด้วยงบเดิม…" (พบตอนลอง `classify_material` บน Vertex 17 พ.ย.) |

## 1. Context

Gemini 3 นับ thinking รวมใน `max_output_tokens` · ถ้า purpose ตั้ง `max_tokens` น้อยไปหรือไม่ได้ตั้ง `thinking` คำตอบ JSON จะขาดกลางทาง (`finish_reason = MAX_TOKENS`) · ตอนนี้ `Gateway.call` เห็นแค่ `ValidationError` จึง retry schema ด้วย `max_tokens` เท่าเดิมและ prompt ที่ยาวขึ้น (แนบคำตอบเดิม) ซึ่งไม่มีทางผ่าน · เสีย call ที่ 2 ทั้งเวลาและเงิน และ log บอกเป็น schema error เหมือน model ตอบผิดรูป (เจอกับ `classify_material` 17 พ.ย. · Junior #140) · feature นี้ให้ provider บอกว่าคำตอบถูกตัด แล้ว gateway หยุดทันทีและบันทึกสาเหตุแยก

## 2. Behavior

### 2.1 provider บอกว่าคำตอบถูกตัด (AI-01)

1. `ProviderResponse` มี field ใหม่ `truncated: bool` (ค่าเริ่มต้น `False`) · `StreamUsage` มี `truncated: bool` (ค่าเริ่มต้น `False`) ที่ provider ตั้งระหว่าง stream
2. Gemini (`gemini.py` · ทั้ง Gemini API และ Vertex): `truncated = True` เมื่อ candidate แรกมี `finish_reason == FinishReason.MAX_TOKENS` · ไม่มี candidate หรือ `finish_reason` อื่น (`STOP`, `SAFETY`, …) → `False` · stream: ดูทุก chunk ที่มี `finish_reason`
3. Fake provider (AI-03): script ใส่ `Truncated("<text>")` ได้ · `generate` ส่ง text นั้นพร้อม `truncated=True` · `stream` ส่ง text นั้นทีละคำตามเดิม แล้วตั้ง `usage.truncated = True` ตอนจบ
4. โค้ดนอก `app/ai/providers/` ไม่อ่าน `finish_reason` ของ SDK เอง (AI-01)

### 2.2 `Gateway.call` (structured)

แต่ละรอบของ schema retry หลังได้ response:

1. parse ผ่าน → ใช้ได้ตามเดิม แม้ `truncated = True` (JSON ครบก่อนถึงเพดานพอดี) · `status = "ok"`
2. parse ไม่ผ่าน และ `truncated = False` → retry schema ตามเดิม (`gateway.schema_retries`)
3. parse ไม่ผ่าน และ `truncated = True` → **ไม่ retry** · raise `AITruncatedError` (ลูกของ `AISchemaError` · caller เดิมที่จับ `AISchemaError` 9 จุดใน `app/` ไม่ต้องแก้) · ข้อความบอก purpose, `max_tokens` และ `tokens_out` · `status = "truncated"`
   - เกิดในรอบ retry (รอบแรก parse ไม่ผ่านแบบไม่ถูกตัด รอบสองถูกตัด) → หยุดเหมือนกัน · `schema_retries` ใน record = จำนวน retry ที่ทำไปแล้ว
4. token ของทุกรอบรวมกันใน record เหมือนเดิม

### 2.3 `Gateway.stream` (free text)

1. stream ที่ถูกตัดกลางคำตอบ: chunk ที่ส่งแล้วส่งต่อตามเดิม ไม่ raise (ผู้ใช้ได้ข้อความไปแล้ว · retry ไม่ได้หลัง chunk แรก · `gateway-guards.md`) · record `status = "truncated"` · log ระดับ WARNING 1 บรรทัดที่ logger `app.ai.gateway` บอก purpose และ `max_tokens`
2. stream ที่ไม่มี text เลย (thinking ใช้หมด) ยังเป็น `AIProviderError` "the model returned no text" ตามเดิม (retry ได้ก่อน chunk แรก)

### 2.4 การบันทึก (AI-04)

1. `CallRecord.status` มีค่าใหม่ `"truncated"`
2. `ai_calls.status` (check ของตาราง: `ok`, `schema_retry`, `fallback`, `degraded`, `error`) → `"truncated"` map เป็น `"error"` เหมือน `schema_error` · **ไม่มี migration**
3. บรรทัด log ของ `app.ai.calls` (`ai-calls-log.md` §2 ข้อ 1) เพิ่ม field `call_status` = `CallRecord.status` (`ok`, `schema_error`, `provider_error`, `truncated`) ต่อจาก `schema_retries` · ใน log จึงแยก "ถูกตัด" ออกจาก schema error ได้ · แถวใน DB ไม่เปลี่ยน
4. circuit breaker (`gateway-guards.md` §2.2): `truncated` นับเป็น "model ตอบแล้ว" ไม่ใช่ provider ล้ม (แบบ `schema_error`) · ไม่เปิด breaker เพราะ config ของ purpose ผิด

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input (provider → gateway) | `ProviderResponse(text, tokens_in, tokens_out, truncated)` | `ProviderResponse(text='{"kind": "sh', tokens_in=820, tokens_out=300, truncated=True)` |
| Output (caller) | ผลตาม schema หรือ `AITruncatedError` (`isinstance(e, AISchemaError)`) | `AITruncatedError("classify_material: answer cut at max_tokens=300 (tokens_out=300)")` |
| Output (log) | บรรทัด JSON ของ `app.ai.calls` + `call_status` | `{…, "status": "error", "schema_retries": 0, "call_status": "truncated"}` |

## 4. Acceptance criteria

fake provider ทั้งหมด (AI-03) · Gemini ทดสอบด้วย response จำลองของ SDK (ไม่เรียก network) ยกเว้น AC-14 (live)

**provider (AI-01)**

- **AC-1 (AI01)** Given response จำลองของ Gemini ที่ candidate แรก `finish_reason = MAX_TOKENS` When `generate` Then `ProviderResponse.truncated is True` · Given `STOP`, `SAFETY` หรือไม่มี candidate (parametrize) Then `False`
- **AC-2 (AI01)** Given stream จำลองของ Gemini ที่ chunk สุดท้าย `finish_reason = MAX_TOKENS` When อ่าน `stream` จนจบ Then text ครบตาม chunk และ `usage.truncated is True` · `STOP` → `False`
- **AC-3 (AI03)** Given fake script `[Truncated('{"kind": "sh')]` When `generate` Then text เดิม `truncated=True` · Given `str` ธรรมดา Then `truncated=False`

**`call` (AI-01, AI-04)**

- **AC-4 (AI01)** Given `classify_material` ได้ `Truncated('{"kind": "sh')` When `call` Then raise `AITruncatedError` ที่ `isinstance(…, AISchemaError)` · provider ถูกเรียก **1 ครั้ง** (ไม่ retry schema) · ข้อความมี `classify_material` และ `max_tokens`
- **AC-5 (AI01)** Given `Truncated('<JSON ที่ครบและผ่าน schema>')` When `call` Then ได้ผลตาม schema · `CallRecord.status = "ok"`
- **AC-6 (AI01)** Given คำตอบผิดรูปที่ไม่ถูกตัด แล้วตามด้วย JSON ที่ถูก (script 2 รายการ) When `call` Then ได้ผล · provider ถูกเรียก 2 ครั้ง (schema retry เดิมยังทำงาน)
- **AC-7 (AI01)** Given คำตอบผิดรูปที่ไม่ถูกตัด แล้วตามด้วย `Truncated(...)` ที่ parse ไม่ผ่าน When `call` Then `AITruncatedError` หลัง provider 2 ครั้ง · record `schema_retries = 1`, `status = "truncated"`
- **AC-8 (AI04)** Given AC-4 Then listener ได้ `CallRecord` 1 รายการ `status = "truncated"` · `tokens_out` = ของคำตอบที่ถูกตัด
- **AC-9 (AI04)** Given 9 caller เดิมที่จับ `AISchemaError` · ไม่มี test ใหม่ต่อ caller: AC-4 พิสูจน์ว่า `AITruncatedError` เป็นลูกของ `AISchemaError` (test เดิมของ caller ผ่านโดยไม่แก้)

**stream (AI-04)**

- **AC-10 (AI04)** Given `tutor_reply` ได้ `Truncated("ลองแยกตัวประกอบดู")` When อ่าน `gateway.stream` จนจบ Then ได้ chunk ทุกคำ ไม่ raise · record `status = "truncated"` · มี log WARNING ที่ `app.ai.gateway` บอก `tutor_reply`

**การบันทึก (AI-04)**

- **AC-11 (AI04)** Given record `status = "truncated"` When `to_row` Then `status = "error"` (เพิ่มแถวใน table-driven test เดิมของ `ai-calls-log.md` AC-3 เป็น test ใหม่ ไม่แก้ test เดิม)
- **AC-12 (AI04)** Given call ที่ถูกตัดใน context ที่มี tenant When log Then บรรทัด JSON ของ `app.ai.calls` มี `"call_status": "truncated"` และ `"status": "error"` · call ที่ผ่านมี `"call_status": "ok"`

**circuit breaker**

- **AC-13** Given breaker ที่ `minimum_calls` call ล้วนเป็น `truncated` When เรียกต่อ Then breaker ยังปิด (ค่า `minimum_calls` และ `failure_rate_threshold` อ่านจาก config ใน test · ไม่ hard-code)

**live (ไม่เข้า CI)**

- **AC-14 (AI01 · `@pytest.mark.live`)** Given gateway จริงบน Vertex ที่ purpose `classify_material` ใช้ `max_tokens` 16 (config ใน test เท่านั้น ไม่แก้ `config/ai.yaml`) When `call` กับไฟล์ตัวอย่าง Then `AITruncatedError` และ provider ถูกเรียก 1 ครั้ง (นับจาก listener: record เดียว `schema_retries = 0`)

**AC-boundary:** ไม่มี threshold ของ learning model · ขอบของ `gateway.schema_retries` (อ่านจาก config): ถูกตัดในรอบแรก (AC-4) และในรอบสุดท้าย (AC-7) · ขอบของ `truncated`: ถูกตัดแต่ parse ผ่าน (AC-5)

**AC-tenant:** ไม่อ่านหรือเขียนข้อมูลใหม่ · แถว `ai_calls` ใช้ context เดิม (`ai-calls-log.md` AC-tenant)

## 5. Data changes

ไม่มี · `ai_calls.status` ใช้ค่า `error` เดิม (§2.4 ข้อ 2) · ถ้าอยากเก็บสาเหตุใน DB ต้องมี migration (§10 ข้อ 2)

## 6. API / SSE changes

ไม่มี

## 7. AI calls

ไม่เพิ่ม purpose · เปลี่ยนพฤติกรรมของ gateway กับทุก purpose ที่ใช้ `call` และ `stream`

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/unit/test_gemini_truncation.py` (ใหม่ · response จำลองของ SDK) | unit | AC-1, AC-2 |
| `tests/unit/test_gateway_truncation.py` (ใหม่ · fake provider) | unit | AC-3 ถึง AC-10, AC-13 |
| `tests/unit/test_ai_calls_log_truncation.py` (ใหม่ · ไม่แก้ `test_ai_calls_log.py`) | unit | AC-11, AC-12 |
| `tests/integration/test_gateway_truncation_live.py` (`@pytest.mark.live` · แบบ `test_vertex_live.py`) | live | AC-14 |

## 9. Out of scope

- เพิ่ม `max_tokens` อัตโนมัติแล้วลองใหม่ (ต้นทุนไม่แน่นอน · ค่า `max_tokens` เป็นของ config ที่ Jam ตัดสินต่อ purpose)
- คอลัมน์สาเหตุใน `ai_calls` (§10 ข้อ 2)
- `finish_reason` อื่น (`SAFETY`, `RECITATION`) · ถ้าต้องจัดการแยก ทำเป็น feature ใหม่
- provider อื่น (Claude · AI-02 ยังเป็น `TODO` ใน `config/ai.yaml`) · ตอนเพิ่ม provider ต้องตั้ง `truncated` ตาม `stop_reason == "max_tokens"`

## 10. Open questions

1. **ตัดสินแล้ว (Jam 17 พ.ย.): ตามข้อเสนอ** · **(Jam) stream ที่ถูกตัด:** ข้อเสนอ: ไม่ raise + log WARNING (§2.3) · ทางเลือก: ส่งข้อความต่อท้าย เช่น "(ข้อความยาวเกิน ถูกตัด)" ให้ผู้ใช้รู้ · ข้อเสนอไม่ส่ง เพราะ `max_tokens` ของ stream (2000) เผื่อไว้มาก และข้อความ template ต้องผ่าน `messages.yaml` (ไฟล์กลาง)
2. **(Junior · ดูย้อนหลัง) เก็บสาเหตุใน DB:** ตอนนี้แยกได้จาก log (`call_status`) เท่านั้น · ถ้าอยาก query ใน `ai_calls` ต้องเพิ่มค่าใน check ของ `status` หรือคอลัมน์ใหม่ (migration + `db push`)
3. **ตัดสินแล้ว (Jam 17 พ.ย.): เพิ่มแล้ว** · **(Jam) บรรทัดใน `ai-orchestration.md` §2.10 "Output"** (spec ระบบ): เพิ่มต่อจาก "Schema validation … retry 1 ครั้ง": "ยกเว้นคำตอบที่ provider ตัดเพราะ `max_tokens` (`truncated`): ไม่ retry เพราะงบเท่าเดิมไม่มีทางผ่าน · ล้มด้วย `AITruncatedError` และ log แยก (`gateway-truncation.md`)"

## 11. Spec changes needed

- `ai-orchestration.md` §2.10 "Output": 1 บรรทัดตาม §10 ข้อ 3 (แก้แล้วใน PR #146)
- `ai-calls-log.md` §2.2: แถวใหม่ในตาราง map (`truncated` → `error`) · §2 ข้อ 3.1: บรรทัด log มี `call_status` (แก้แล้วใน PR #146)
