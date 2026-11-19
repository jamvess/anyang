# Feature: gateway รอแล้วลองใหม่เมื่อ provider ตอบ 429 · ห้องติวไม่สร้างโจทย์ซ้ำเมื่อโดน 429

| | |
|---|---|
| Area | platform (AI gateway) · tutor (สร้างโจทย์ตอนเปิดห้อง) |
| Requirements | NFR-R1 (provider หลักมีปัญหา ระบบยังตอบได้ · ai-orchestration §2.10) · AM-11 (โจทย์ในห้องจาก `generate_problem` ที่ SymPy ยืนยันแล้ว) |
| Owner | Junior |
| Reviewer | Jam (เจ้าของ gateway และ `room_problems` · ให้ Junior ตัดสิน 19 พ.ย.) |
| Status | implemented 2026-11-19 (PR #159 · Junior ok spec: §10 ข้อ 1 ตามข้อเสนอ · ข้อ 2 ปรับตาม Junior · ข้อ 3 ตามข้อเสนอ) |
| Related system spec | ai-orchestration.md §2.10 "Fallback chain" · `config/ai.yaml` `gateway.*` · `room-problems-db.md` §2 ข้อ 4, 7 · `gateway-guards.md` §2.2 (circuit breaker) · `gateway-truncation.md` (#146 · ไม่แตะส่วนเดียวกัน ดู §9) |

## 1. Context

journey บนเว็บ 17 พ.ย. (Junior · บัญชีทดสอบ): เปิดห้องครั้งแรกหลัง ingestion ได้ `generate_problem` 429 `RESOURCE_EXHAUSTED` 3 ครั้งใน 3 วินาที (08:57:42–45 UTC) แล้วห้องขึ้น "ตอนนี้เตรียมโจทย์ไม่ทัน" · สาเหตุ: gateway retry 429 แค่ `gateway.retries` (1) ครั้งหลังรอ `retry_backoff_seconds` (1 s) เพราะ Vertex ไม่ส่ง `retryDelay` · แล้ว `room_problems` ลองใหม่อีก `1 + checker.max_generate_retries` (3) รอบทันที รวม ~6 call ใน ~6 วินาที ซึ่งเร็วเกินกว่า quota แบบ shared ของ Vertex จะฟื้น · gateway ยังไม่มี fallback provider (`anthropic:TODO`) · เป็นความเสี่ยงอันดับ 1 ของวิดีโอ 23 พ.ย.

feature นี้: (A) 429 มีตารางรอของตัวเองที่ยาวขึ้นจาก `config/ai.yaml` แยก non-stream กับ stream · (B) `room_problems` ไม่ลองสร้างโจทย์ซ้ำเมื่อ gateway ยอมแพ้เพราะ 429 แล้ว (gateway รอไปแล้วเต็มตาราง) · ไม่รวม: ข้อความบอกผู้ใช้ระหว่างรอ (C) และ fallback model (D) · ทำหลังวิดีโอ

## 2. Behavior

### 2.1 Config (`config/ai.yaml` → `gateway`)

- `rate_limit_waits_seconds: [5, 15, 30]` · รอก่อนลองใหม่หลัง 429 ครั้งที่ 1, 2, 3 ของ call ที่ไม่ใช่ stream (`call`, `embed`) · จำนวนสมาชิก = จำนวนครั้งที่ลองใหม่หลัง 429 · `[]` = ไม่ลองใหม่หลัง 429
- `rate_limit_waits_stream_seconds: [5]` · เหมือนกันแต่สำหรับ `stream` ก่อน chunk แรก (ผู้ใช้กำลังรอข้อความ จึงสั้นกว่า)
- ทุกค่า ≥ 0 · key หายหรือค่าติดลบ → โหลด config ไม่ผ่าน (`AIConfig` แบบ strict เหมือน key อื่น)
- ทั้งสองค่าเป็น `[C]` · ที่มา: 429 ของ Vertex 17 พ.ย. ไม่หายใน 1–3 วินาที · calibrate หลัง Alpha จาก log ใน §2.2 ข้อ 6 (รอกี่วินาทีแล้วผ่าน)
- key เดิม (`retries`, `retry_backoff_seconds`, `max_retry_wait_seconds`) ไม่เปลี่ยนค่า และใช้กับ error ที่ไม่ใช่ 429 เท่านั้น · `max_retry_wait_seconds` ไม่ใช้กับ 429 แล้ว (เพดาน 10 s ต่ำกว่าตารางของเราเอง 30 s · Junior 19 พ.ย.)

### 2.2 `Gateway._with_retries` (ใช้กับ `call`, `embed` และ `stream` ก่อน chunk แรก)

1. error แบ่งเป็น 2 ชนิด แต่ละชนิดมีงบของตัวเองภายใน call เดียว:
   - **429** (`ProviderRateLimited`): งบ = `len(waits)` · `waits` = `rate_limit_waits_seconds` หรือ `rate_limit_waits_stream_seconds` ตาม caller
   - **อื่นๆ** (timeout, exception อื่นของ provider): งบ = `gateway.retries` รอ `retry_backoff_seconds` · เหมือนเดิมทุกอย่าง
2. 429 ครั้งที่ n (นับเฉพาะ 429 ของ call นี้ เริ่มที่ 1) ยังมีงบ (n ≤ `len(waits)`) → `step = waits[n − 1]` · ถ้า `retry_after > max(waits)` (ค่ามากสุดของตารางนั้น: 30 s non-stream, 5 s stream) → ยอมแพ้ทันทีไม่รอ (provider ขอรอนานกว่าที่ตารางเรายอม) · ไม่งั้นรอ `wait = max(step, retry_after)` (ไม่มี `retry_after` = `step`) แล้วลองใหม่ · `retry_after` เท่ากับ `max(waits)` พอดี → ยังรอ (Junior 19 พ.ย.)
3. งบของชนิดนั้นหมด → ยอมแพ้ ไม่รอ (เหมือนเดิม: ไม่รอหลังครั้งสุดท้าย)
4. ยอมแพ้โดย error สุดท้ายเป็น 429 → `AIRateLimitedError` (class ใหม่ ลูกของ `AIProviderError` · caller เดิมที่จับ `AIProviderError` ไม่ต้องแก้) · ยอมแพ้ด้วย error อื่น → `AIProviderError` เหมือนเดิม
5. ไม่เปลี่ยน: `timeout_s` ต่อครั้ง · `CallRecord` 1 แถวต่อ call (`provider_error` เมื่อยอมแพ้) · circuit breaker นับ 1 ผลต่อ call · stream retry เฉพาะก่อน chunk แรก · schema retry และ truncation (#146)
6. ทุกครั้งที่จะรอหลัง 429 → log WARNING บรรทัดเดียว: purpose, ครั้งที่ n, `wait`, `retry_after` (ไว้ calibrate §2.1)

ผลต่อเวลา: `call` ที่โดน 429 ทุกครั้งรอรวม 5 + 15 + 30 = 50 s แล้วล้ม (4 ครั้งที่เรียก provider) · `stream` รอรวม 5 s (2 ครั้ง) · ทั้งหมดอยู่ใต้ timeout ของ Cloud Run (300 s) และไม่มี timeout ฝั่ง `fetch` ของหน้าเว็บ

### 2.3 `room_problems` · สร้างโจทย์ (AM-11 · ต่อจาก `room-problems-db.md` §2 ข้อ 4)

1. ในรอบสร้างโจทย์ `1 + checker.max_generate_retries` · ถ้า `gateway.call("generate_problem", …)` ล้มด้วย `AIRateLimitedError` → หยุดรอบทันที ไม่สร้างใหม่ · ผลเหมือน "ไม่ได้โจทย์" (`room-problems-db.md` §2 ข้อ 7: ไม่มี `problem`, `room.no_problem` หลังคำทัก)
2. log WARNING ว่าหยุดเพราะ 429 (แยกจากบรรทัด "try n failed" เดิม)
3. error อื่น (schema, ซ้ำ, SymPy ไม่ยืนยัน, `AIProviderError` ที่ไม่ใช่ 429) → นับเป็นรอบและสร้างใหม่ตามเดิม

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Config | `gateway.rate_limit_waits_seconds: list[float ≥ 0]` · `gateway.rate_limit_waits_stream_seconds: list[float ≥ 0]` | `[5, 15, 30]` · `[5]` |
| Error ใหม่ | `AIRateLimitedError(AIProviderError)` ใน `app.ai.gateway` | `generate_problem: ProviderRateLimited: 429 RESOURCE_EXHAUSTED` |
| API / SSE | ไม่เปลี่ยน | |

## 4. Acceptance criteria

ทุกข้อใช้ fake provider (script ใส่ `ProviderRateLimited`) และ `_sleep` ที่จดเวลาแทนการรอจริง · ค่า waits อ่านจาก config ที่โหลด (ไม่ hard-code 5, 15, 30 ใน test ยกเว้น test ที่ส่ง config ของตัวเอง)

- **AC-1 (NFR-R1)** Given `call` ได้ 429 `len(W)` ครั้งแล้วได้คำตอบ (W = `rate_limit_waits_seconds`) Then ได้ผล · `sleeps == W` · provider ถูกเรียก `len(W) + 1` ครั้ง
- **AC-2 (NFR-R1 · boundary)** Given `call` ได้ 429 `len(W) + 1` ครั้ง Then `AIRateLimitedError` (เป็น `AIProviderError` ด้วย) · provider ถูกเรียก `len(W) + 1` ครั้ง · `sleeps == W` (ไม่รอหลังครั้งสุดท้าย)
- **AC-3 (NFR-R1)** Given `stream` ได้ 429 แล้วได้ chunk Then ได้ข้อความครบ · `sleeps == WS` (WS = `rate_limit_waits_stream_seconds`) · Given ได้ 429 `len(WS) + 1` ครั้ง Then `AIRateLimitedError` ก่อน chunk แรก · provider ถูกเรียก `len(WS) + 1` ครั้ง
- **AC-4 (NFR-R1)** Given `embed` ได้ 429 แล้วผ่าน Then `sleeps == W[:1]`
- **AC-5 (NFR-R1 · config)** Given config ที่ `rate_limit_waits_seconds = [1, 2]` Then 429 ทุกครั้ง → เรียก provider 3 ครั้ง `sleeps == [1, 2]` · Given `[]` Then 429 ครั้งแรก → `AIRateLimitedError` ไม่รอ · Given ค่าติดลบ Then โหลด config ไม่ผ่าน
- **AC-6 (NFR-R1 · retry_after)** Given `call` ที่ W = `[5, 15, 30]` และ `max_retry_wait_seconds` 10, 429 ครั้งแรก: `retry_after = 3` → รอ 5 · `= 8` → รอ 8 · `= 20` → รอ 20 (เกิน `max_retry_wait_seconds` ก็รอ) · `= 30` → รอ 30 (boundary) · `= 31` → ยอมแพ้ทันที `AIRateLimitedError`, `sleeps == []`, เรียก provider 1 ครั้ง · Given 429 ครั้งที่ 3 (step 30) และ `retry_after = 20` → รอ 30 · Given `stream` ที่ WS = `[5]`: `retry_after = 5` → รอ 5 · `= 6` → ยอมแพ้ทันที
- **AC-6b (NFR-R1 · error อื่นยังใช้เพดานเดิม)** Given `retry_backoff_seconds` > `max_retry_wait_seconds` และ error ที่ไม่ใช่ 429 Then ไม่ retry (เรียก provider 1 ครั้ง · พฤติกรรมเดิม)
- **AC-7 (NFR-R1 · error อื่นไม่เปลี่ยน)** Given timeout `retries + 1` ครั้ง Then `AIProviderError` ที่ไม่ใช่ `AIRateLimitedError` · `sleeps == [retry_backoff_seconds] × retries` · Given 429 → timeout → คำตอบ Then ได้ผล `sleeps == [W[0], retry_backoff_seconds]` (งบแยกกัน)
- **AC-8 (NFR-R1)** Given ยอมแพ้เพราะ 429 Then `CallRecord` 1 แถว `status = "provider_error"` · breaker บันทึกผลล้ม 1 ครั้ง
- **AC-9 (AM-11)** Given เปิดห้องที่ต้องสร้างโจทย์ และ `generate_problem` ล้มด้วย `AIRateLimitedError` ครั้งแรก Then gateway ถูกเรียก `generate_problem` 1 ครั้ง (ไม่ใช่ `1 + max_generate_retries`) · ไม่มีแถว `problems` · มี token `room.no_problem` หลังคำทัก
- **AC-10 (AM-11)** Given `generate_problem` ล้มด้วย `AIProviderError` ที่ไม่ใช่ 429 ทุกครั้ง Then ยังเรียก `1 + max_generate_retries` ครั้งเหมือนเดิม (`room-problems-db.md` AC-boundary)

## 5. Data changes

ไม่มี · ไม่มี migration · `ai_calls` เหมือนเดิม (1 แถวต่อ call)

## 9. ส่วนที่ซ้อนกับ #146 (gateway-truncation)

#146 แก้ `call` (schema retry), `stream` (`first_chunk`, ท้าย stream, `provider_failed`), `CallStatus` · ไม่แตะ `_with_retries` · feature นี้แก้ `_with_retries` (เพิ่มพารามิเตอร์ waits) และ 3 จุดที่เรียกมัน (`_generate`, `stream` ส่ง waits ของ stream, `embed`) เท่านั้น · ใน `stream` แก้บรรทัดเดียวที่เรียก `_with_retries` ไม่แตะ `first_chunk`

## 10. คำถามที่ต้องตัดสิน

1. **ai-orchestration.md §2.10 "Fallback chain" (ไฟล์ของ Jam):** แก้ประโยค "retry 1 ครั้ง (backoff …)" ให้บอกว่า 429 ใช้ `rate_limit_waits_*` ใน PR เดียวกัน · ข้อเสนอ: แก้ใน PR นี้แล้วบอก Jam ในคำอธิบาย PR
2. ~~`retry_after` เกิน step~~ · **ตัดสินแล้ว 19 พ.ย. (Junior):** รอ `max(step, retry_after)` · ยอมแพ้เมื่อ `retry_after > max(waits)` · `max_retry_wait_seconds` ใช้กับ error ที่ไม่ใช่ 429 เท่านั้น (§2.2 ข้อ 2)
3. **test เดิมของ §2.10 ที่ขัดกับข้อ 2 · ตัดสินแล้ว 19 พ.ย. (Junior): แก้ตามข้อเสนอ (boundary = ค่ามากสุดของตารางที่เกี่ยว) · บอก Jam ใน PR #159:**
   - `tests/unit/test_ai_gateway.py::test_ai_orchestration_2_10_no_retry_when_provider_asks_to_wait_too_long` · 429 ของ `call` ขอรอ `max_retry_wait_seconds + 1` = 11 s แล้วคาดว่ายอมแพ้ · กฎใหม่: 11 ≤ 30 → รอ 11 แล้วลองใหม่ · ข้อเสนอ: เปลี่ยน `retry_after` เป็น `max(rate_limit_waits_seconds) + 1` (ความหมายของ test เหมือนเดิม: ขอรอนานเกินเพดาน → ไม่ retry)
   - `tests/unit/test_ai_gateway_stream.py::test_AI01_stream_rate_limit_wait_boundary[0-True]` · stream ได้ 429 ขอรอ `max_retry_wait_seconds` = 10 s แล้วคาดว่ารอ 10 แล้วผ่าน · กฎใหม่: 10 > 5 (`max(rate_limit_waits_stream_seconds)`) → ยอมแพ้ · ข้อเสนอ: เปลี่ยนฐานของ boundary จาก `max_retry_wait_seconds` เป็น `max(rate_limit_waits_stream_seconds)` (กรณี `[1-False]` ผ่านอยู่แล้วแต่ควรเปลี่ยนฐานด้วยให้เป็น boundary จริง)
   - test เดิมอื่นที่มี 429 (`test_ai_orchestration_2_10_retry_waits_the_delay_the_provider_asked_for` · ขอ 5 s → รอ 5) ยังผ่าน
