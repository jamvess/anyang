# Feature: rate limit ของห้องติว + circuit breaker ของ gateway

| | |
|---|---|
| Area | platform |
| Requirements | TM-21 (ขีดจำกัดมาจาก `config/ai.yaml` → `guards`) · NFR-R1 (provider หลักล่ม ระบบยังตอบได้) · NFR-P2 (ต้นทุน AI ต่อ session) |
| Owner | Jam (item of Junior · ช่วง solo 2026-11-01) |
| Reviewer | Jam · Junior ดูย้อนหลัง (โครงสร้าง backend · §10) |
| Status | approved by Jam 2026-11-01 (OQ 1–6 ตามข้อเสนอ · Junior ดูข้อ 1–4 ย้อนหลังได้) |
| Related system spec | ai-orchestration.md §2.9 (Limits: 20 ข้อความ/นาที), §2.10 (Fallback chain, Circuit breaker) · api.md Conventions (Error), "ห้องติว", v1.7 "รูป เสียง และยืนยันลายมือ" · architecture.md v1.2 "สร้างแล้วหรือยัง" · `config/ai.yaml` → `guards.rate_limit_messages_per_minute`, `gateway.circuit_breaker.*` |

## 1. Context

`api-staging` เป็น URL สาธารณะ และยังเปิด `AI_PROVIDER=live` ไม่ได้ · architecture.md v1.2 บอกว่า gateway ยังไม่มี guards และ circuit breaker · feature นี้ทำ 2 อย่าง:

- **(ก) rate limit:** จำกัดจำนวนข้อความต่อ user ต่อนาทีบน endpoint ของห้องติวที่ทำให้เกิด AI call (§2.9) · กันคนส่งรัวๆ จนกิน credit (NFR-P2)
- **(ข) circuit breaker ใน gateway:** เมื่อ provider ล้มติดกันหลายครั้ง gateway หยุดเรียก provider นั้นชั่วคราว (§2.10) · ตอนนี้ไม่มี provider สำรอง จึงล้มทันทีแล้วให้ผู้เรียก degrade ตามเดิม (ข้อความ "ระบบช้า ลองส่งอีกทีนะ") · ผู้ใช้ไม่ต้องรอ timeout ทุกข้อความ และไม่ยิง request ใส่ provider ที่ล่มอยู่ (NFR-R1)

ทั้งสองอย่างอ่านค่าจาก `config/ai.yaml` ที่มีอยู่แล้ว ไม่ต้องเพิ่มค่าใหม่

## 2. Behavior

### 2.1 Rate limit (ก)

- **endpoint ที่นับ** (ข้อความที่ผู้ใช้ส่งในห้องติว · §2.9 "20 ข้อความ/นาที"):
  - `POST /sessions/{id}/messages` (text และรูป)
  - `POST /sessions/{id}/ocr/confirm`
  - `POST /exam-preps/{id}/scope/chat` (เพิ่ม 2026-11-04 · api.md v1.11 · เรียก AI ทุกข้อความเหมือนกัน)
  - `POST /personas/extract` (เพิ่ม 2026-11-04 · api.md v1.12 · เรียก AI ทุกครั้งเหมือนกัน)
  - ทุก endpoint ใช้ตัวนับเดียวกันของ user คนนั้น
- **ไม่นับ:** `GET` ทุกตัว, `/uploads`, `/transcribe`, `POST /exam-preps/{id}/sessions` (§10 ข้อ 2)
- **ค่า:** `limit = guards.rate_limit_messages_per_minute` (ตอนนี้ 20) · หน้าต่างเวลา 60 วินาทีเลื่อนไปเรื่อยๆ (sliding window) นับย้อนจากตอนนี้ · 60 วินาทีมาจากชื่อค่า "per minute" ไม่ใช่ threshold ใหม่
- **ทำไม่ถึง limit:** request ที่อยู่ใน 60 วินาทีที่ผ่านมามีไม่ถึง `limit` → ผ่าน และนับเพิ่ม 1
- **ถึง limit แล้ว:** มีครบ `limit` แล้ว → ตอบ `429` + body `{"error": {"code": "rate_limited", "message": …}}` + header `Retry-After` (จำนวนวินาทีเต็มที่ต้องรอจนแถวเก่าสุดหลุดหน้าต่าง ปัดขึ้น ≥ 1)
  - ตอบก่อนเริ่ม SSE · เป็น HTTP 429 ธรรมดา ไม่ใช่ event `error`
  - ไม่เรียก AI · request ที่ถูกปฏิเสธไม่นับเพิ่ม
- **นับก่อนตรวจ body:** request ที่ body ผิด (422) ก็นับ · กันคนยิง body เสียรัวๆ (§10 ข้อ 3) · ยกเว้น body ที่ไม่ใช่ JSON เลย: FastAPI ปฏิเสธก่อนถึงตัวนับ จึงไม่นับ (ไม่ถึง AI อยู่แล้ว · self-review #103)
- **นับต่อใคร:**
  - มี token (`get_auth` ได้ `AuthContext`): นับต่อ `user_id` · user คนละคน (tenant เดียวกันหรือคนละ tenant) ไม่กระทบกัน
  - ไม่มี token (`AUTH_REQUIRED=false`): นับต่อ IP ของ client (ค่าแรกของ `X-Forwarded-For` ที่ Cloud Run ใส่ · ไม่มีก็ใช้ IP ของ connection) (§10 ข้อ 1)
- **ที่เก็บ:** ในหน่วยความจำของ process (แต่ละ instance ของ Cloud Run นับแยกกัน) · restart แล้วเริ่มนับใหม่ (§10 ข้อ 4) · ทุก 60 วินาทีลบ key ที่ไม่มีข้อความในหน้าต่าง กันหน่วยความจำโตจาก IP ใหม่ทุก request
- **header:** `Retry-After` อยู่ใน `Access-Control-Expose-Headers` ให้หน้าเว็บอ่านได้

### 2.2 Circuit breaker (ข)

ค่าทั้งหมดจาก `gateway.circuit_breaker` ใน `config/ai.yaml` (ป้าย [B] Resilience4j defaults):

| ค่า | ตอนนี้ | ใช้ทำอะไร |
|---|---|---|
| `failure_rate_threshold` | 0.5 | สัดส่วน call ที่ล้มในหน้าต่าง ที่ทำให้เปิด breaker |
| `minimum_calls` | 10 | ต้องมี call ในหน้าต่างอย่างน้อยเท่านี้ก่อนจะคิดสัดส่วน |
| `sliding_window_calls` | 100 | หน้าต่างคือ call ล่าสุดไม่เกินจำนวนนี้ |
| `open_seconds` | 60 | breaker เปิดนานเท่านี้แล้วลองใหม่ |

- **breaker แยกต่อ provider** (`vertex`, `gemini`, `fake`) · ทุก purpose และทุก tier ที่ใช้ provider เดียวกันใช้ breaker ตัวเดียวกัน
- **นับอะไร:** 1 call ของ `ai.call` / `ai.stream` / `embed` ที่จบแล้ว = 1 ผล:
  - ล้ม = จบด้วย `AIProviderError` หลัง retry ครบแล้ว (timeout, error ของ provider, rate limit ของ provider, stream ที่ไม่มีข้อความ, stream ที่ขาดกลางทาง)
  - สำเร็จ = provider ตอบแล้ว รวม `AISchemaError` (model ตอบแต่ผิด schema ไม่ใช่ provider ล่ม) และ stream ที่ผู้เรียกหยุดอ่านเองก่อนจบ
  - ไม่นับ: `AIConfigError`, `AIInputError` (เกิดก่อนเรียก provider) · call ที่ผู้เรียก cancel ก่อน provider ตอบ (ไม่ได้บอกอะไรเกี่ยวกับ provider · ถ้าเป็น call ทดลองตอน half-open ก็ปล่อยช่องให้ call ถัดไปทดลองแทน)
- **สถานะ:**
  - **closed** (เริ่มต้น): เรียก provider ตามปกติ · หลังแต่ละ call ถ้ามี ≥ `minimum_calls` ผลในหน้าต่าง และสัดส่วนที่ล้ม ≥ `failure_rate_threshold` → **open**
  - **open:** ทุก call ที่ route ไป provider นี้ล้มทันทีด้วย `AIProviderError` ("circuit open") ไม่เรียก provider ไม่ retry · เมื่อเปิดครบ `open_seconds` → **half-open**
  - **half-open:** ปล่อย call ถัดไป 1 call ไปที่ provider (call อื่นที่มาพร้อมกันล้มทันทีเหมือน open) · สำเร็จ → **closed** และล้างหน้าต่าง · ล้ม → **open** อีก `open_seconds` (§10 ข้อ 5)
- **ผลของ call ที่เริ่มก่อนเปลี่ยนสถานะไม่นับ:** ทุกครั้งที่เปลี่ยนสถานะเริ่มรุ่นใหม่ (generation) · call ช้าที่เริ่มตอน closed แล้วจบหลัง breaker เปิด จะไม่ถูกนับเป็นผลของ call ทดลอง
- **call ทดลองที่ไม่รายงานผล** (เช่น stream ที่ถูกทิ้งโดยไม่ปิด) หมดอายุหลัง `open_seconds` แล้ว call ถัดไปเป็นตัวทดลองแทน · ผลที่มาช้าของตัวเก่าไม่นับ
- **config:** `minimum_calls` ต้องไม่เกิน `sliding_window_calls` (ไม่งั้นไม่มีทางเปิด) · โหลด config ไม่ผ่านถ้าเกิน
- **ผู้เรียกไม่ต้องรู้จัก breaker:** เห็นแค่ `AIProviderError` แบบเดิม · `tutor_turn` จึง degrade เป็น `token` "ระบบช้า ลองส่งอีกทีนะ" → `done` ตามเดิม (tutor-reply-stream.md)
- **log:** call ที่ล้มเพราะ breaker เปิด ไม่ได้เรียก AI จึงไม่ส่ง `CallRecord` (ไม่มี token, ไม่มีแถวใน `ai_calls`) · เขียน log `warning` 1 บรรทัดต่อการเปลี่ยนสถานะ (closed→open, open→half-open, half-open→closed/open) พร้อมชื่อ provider (§10 ข้อ 6)
- **ที่เก็บ:** ใน `Gateway` ตัวที่ process ใช้ (`get_gateway()` สร้างครั้งเดียว) · แต่ละ instance ของ Cloud Run มี breaker ของตัวเอง

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input (ก) | request ที่ `POST /sessions/{id}/messages` หรือ `/ocr/confirm` + ตัวตน (`user_id` หรือ IP) + เวลาปัจจุบัน | user `u1` ส่งข้อความที่ 21 ภายใน 60 วินาที |
| Output (ก) | ผ่านตามปกติ หรือ `429` `{"error": {"code": "rate_limited", "message": "…"}}` + `Retry-After: <int>` | `429` `Retry-After: 12` |
| Input (ข) | ผลของแต่ละ call ต่อ provider + เวลาปัจจุบัน | 10 call ล่าสุดของ `vertex` ล้ม 5 |
| Output (ข) | สถานะ closed / open / half-open · ตอน open ทุก call ได้ `AIProviderError` ทันที | `tutor_reply` ได้ "ระบบช้า ลองส่งอีกทีนะ" โดยไม่เรียก Vertex |

## 4. Acceptance criteria

เวลาในทุกข้อเป็นนาฬิกาที่ test ควบคุมได้ (ไม่ `sleep` จริง) · provider เป็น `FakeProvider` ที่สั่งให้ล้มหรือสำเร็จได้ · `L` = `guards.rate_limit_messages_per_minute` และค่า breaker อ่านจาก config ใน test ไม่ hard-code

**Rate limit (ก)**

- **AC-1 (TM-21)** Given user `u1` ยังไม่เคยส่ง When ส่ง `POST /sessions/{id}/messages` `L` ครั้งภายใน 60 วินาที Then ผ่านทั้ง `L` ครั้ง (200 + SSE ตามเดิม)
- **AC-2 (TM-21 · boundary)** Given `u1` ส่งไปแล้ว `L` ครั้งภายใน 60 วินาที When ส่งครั้งที่ `L + 1` Then `429` code `rate_limited` มี header `Retry-After` เป็นจำนวนเต็ม ≥ 1 · body เป็น error envelope · ไม่มีการเรียก `tutor_reply` · ทดสอบที่ `L − 1` (ผ่าน), `L` (ผ่าน), `L + 1` (429)
- **AC-3 (TM-21 · boundary ของหน้าต่าง)** Given `u1` ส่งครบ `L` ครั้งที่เวลา t0 When ส่งอีกที่ t0 + 60 − ε Then `429` · When ส่งที่ t0 + 60 + ε Then ผ่าน
- **AC-4 (TM-21)** Given `u1` ได้ `429` แล้ว When ส่งซ้ำอีก 5 ครั้งทันที Then ได้ `429` ทุกครั้ง และ `Retry-After` ไม่เพิ่มขึ้น (request ที่ถูกปฏิเสธไม่นับ)
- **AC-5 (TM-21)** Given `u1` ส่ง `/messages` `L − 1` ครั้ง When ส่ง `/ocr/confirm` 1 ครั้งแล้วส่ง `/messages` อีก Then `/ocr/confirm` ผ่าน และ `/messages` ครั้งถัดไปได้ `429` (ใช้ตัวนับเดียวกัน)
- **AC-6 (TM-21)** Given `u1` ส่งครบ `L` แล้ว When ส่ง `GET /sessions/{id}`, `POST /sessions/{id}/uploads`, `/transcribe` Then ไม่มีอันไหนได้ `429`
- **AC-7 (TM-21)** Given `u1` ส่งครบ `L` แล้ว When `u2` ส่ง Then `u2` ผ่าน (นับแยกต่อ `user_id`)
- **AC-tenant (SA-06)** Given `u1` ของ tenant A ส่งครบ `L` When `u3` ของ tenant B ส่ง Then ผ่าน · ข้อความ error ของ `u1` ไม่มี `user_id`, tenant หรือจำนวนของคนอื่น
- **AC-8 (TM-21)** Given ไม่มี token (`AUTH_REQUIRED=false`) และ `X-Forwarded-For: 203.0.113.7, 10.0.0.1` When ส่ง `L + 1` ครั้ง Then ครั้งที่ `L + 1` ได้ `429` · Given IP อื่น `198.51.100.2` Then ผ่าน
- **AC-9 (TM-21)** Given body ผิด (`{}`) When ส่ง `L` ครั้ง (ได้ 422 ทุกครั้ง) แล้วส่ง body ที่ถูก Then ได้ `429`
- **AC-10 (TM-21)** ค่า `L` อ่านจาก `config/ai.yaml` → `guards.rate_limit_messages_per_minute`: Given config ที่ตั้งเป็น 3 When ส่ง 4 ครั้ง Then ครั้งที่ 4 ได้ `429`
- **AC-11 (TM-21)** OpenAPI ของ `/messages`, `/ocr/confirm`, `scope/chat` และ `/personas/extract` มี response `429` ที่ชี้ไป `ErrorResponse`
- **AC-26 (TM-21)** Given `u1` ส่ง `/messages` `L − 1` ครั้ง When ส่ง `scope/chat` 1 ครั้งแล้วส่ง `/messages` อีก Then `scope/chat` ผ่าน และ `/messages` ตอบ `429` (ตัวนับเดียวกัน)
- **AC-27 (TM-21)** Given `u1` ส่ง `/messages` `L − 1` ครั้ง When ส่ง `/personas/extract` 1 ครั้งแล้วส่ง `/messages` อีก Then `/personas/extract` ผ่าน และ `/messages` ตอบ `429` (ตัวนับเดียวกัน)

**Circuit breaker (ข)**

- **AC-12 (NFR-R1)** Given breaker ของ `fake` เป็น closed และหน้าต่างมี 9 ผล (ล้ม 9) When call ที่ 10 ล้ม Then breaker เป็น open (ครบ `minimum_calls` และสัดส่วน 10/10 ≥ threshold) · Given หน้าต่างมี 9 ผลที่ล้มทั้งหมด Then ยังเป็น closed (ยังไม่ครบ `minimum_calls`)
- **AC-13 (NFR-R1 · boundary ของสัดส่วน)** Given `minimum_calls` call ล่าสุด สัดส่วนที่ล้มต่ำกว่า threshold 1 call (เช่น 4/10) Then closed · เท่ากับ threshold (5/10) Then open · คำนวณจำนวนจาก config ใน test
- **AC-14 (NFR-R1 · หน้าต่าง)** Given `sliding_window_calls` call ที่สำเร็จ แล้วตามด้วย call ที่ล้ม Then สัดส่วนคิดจาก `sliding_window_calls` call ล่าสุดเท่านั้น (call ที่เก่ากว่าหลุดหน้าต่าง)
- **AC-15 (NFR-R1)** Given breaker open When `ai.call` และ `ai.stream` Then ทั้งคู่ล้มด้วย `AIProviderError` ทันที · `FakeProvider` ไม่ถูกเรียก (ไม่มี request ใหม่) · ไม่มีการรอ backoff · ไม่ส่ง `CallRecord`
- **AC-16 (NFR-R1 · boundary ของเวลา)** Given open ที่เวลา t0 When call ที่ t0 + `open_seconds` − ε Then ล้มทันที · When call ที่ t0 + `open_seconds` + ε Then call นั้นไปถึง provider (half-open)
- **AC-17 (NFR-R1)** Given half-open When call ที่ถูกปล่อยไปสำเร็จ Then closed และหน้าต่างว่าง (ล้มอีก 1 ครั้งยังไม่เปิด breaker)
- **AC-18 (NFR-R1)** Given half-open When call ที่ถูกปล่อยไปล้ม Then open อีก `open_seconds` นับจากตอนนั้น
- **AC-19 (NFR-R1)** Given half-open และ call แรกยังไม่จบ When มี call ที่สองพร้อมกัน Then call ที่สองล้มทันทีโดยไม่เรียก provider
- **AC-20 (NFR-R1)** Given `AISchemaError` ครบ `minimum_calls` ครั้ง Then breaker ยัง closed (model ตอบได้ แค่ผิด schema) · Given `AIConfigError` หรือ `AIInputError` Then ไม่ถูกนับในหน้าต่าง
- **AC-21 (NFR-R1)** Given stream ที่ผู้เรียกหยุดอ่านก่อนจบ (`aclosing`) Then นับเป็นสำเร็จ · Given stream ที่ provider ตัดกลางทาง Then นับเป็นล้ม
- **AC-22 (NFR-R1)** Given breaker ของ `vertex` open When call ที่ route ไป `gemini` Then เรียก `gemini` ตามปกติ (breaker แยกต่อ provider · ใช้ `Gateway.live` ที่มี fake 2 ตัว)
- **AC-23 (NFR-R1 · ผู้ใช้เห็น)** Given breaker open When `POST /sessions/{id}/messages` `{text}` Then SSE เป็น `token` "ระบบช้า ลองส่งอีกทีนะ" → `done` (degrade แบบเดิม · tutor-reply-stream.md) ภายในเวลาที่ไม่ขึ้นกับ `timeout_s`
- **AC-24 (NFR-R1)** การเปลี่ยนสถานะแต่ละครั้งเขียน log `warning` 1 บรรทัดที่มีชื่อ provider และสถานะใหม่ · ไม่มี prompt หรือข้อความของผู้ใช้ใน log
- **AC-25 (NFR-R1)** ค่าทั้ง 4 อ่านจาก `config/ai.yaml` → `gateway.circuit_breaker`: Given config ที่ตั้ง `minimum_calls: 2`, `failure_rate_threshold: 1.0` When ล้ม 2 ครั้ง Then open

**AC-boundary:** rate limit ที่ `L − 1`, `L`, `L + 1` (AC-2) และหน้าต่าง 60 ± ε (AC-3) · breaker ที่ `minimum_calls − 1` / `minimum_calls` (AC-12), threshold − 1 call / = threshold (AC-13), `open_seconds` ± ε (AC-16)

## 5. Data changes

ไม่มี · ตัวนับ rate limit และสถานะ breaker อยู่ในหน่วยความจำ (§10 ข้อ 4) · ไม่มีแถวใหม่ใน `ai_calls`

## 6. API / SSE changes

| Endpoint / event | Request | Response |
|---|---|---|
| `POST /sessions/{id}/messages` | เหมือนเดิม | เพิ่ม `429` `rate_limited` + `Retry-After` |
| `POST /sessions/{id}/ocr/confirm` | เหมือนเดิม | เพิ่ม `429` `rate_limited` + `Retry-After` |

ไม่มี SSE event ใหม่ · ต้องแก้ api.md (§11)

## 7. AI calls

ไม่มี call ใหม่ · breaker ครอบทุก call ที่ผ่าน gateway (`call`, `stream`, `embed`)

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/unit/test_rate_limit.py` (ใหม่): ตัวนับกับนาฬิกาที่ควบคุมได้ + endpoint ผ่าน `TestClient` | unit | AC-1 ถึง AC-11, AC-tenant |
| `tests/unit/test_circuit_breaker.py` (ใหม่): breaker กับนาฬิกาที่ควบคุมได้ + `Gateway` กับ `FakeProvider` | unit | AC-12 ถึง AC-22, AC-24, AC-25 |
| `tests/unit/test_circuit_breaker.py`: `POST /messages` ตอน breaker open | unit | AC-23 |
| `tests/unit/test_gateway_guards_review.py` (self-review #103): ผลจากรุ่นเก่า, cancel, call ทดลองหมดอายุ, config, ล้าง key, CORS | unit | §2.1, §2.2 ส่วนที่เพิ่มหลัง review |

## 9. Out of scope

- provider สำรอง (Claude, Mathpix) และการ route ไป fallback ตอน breaker open (§2.10 Fallback chain) · ตอนนี้ไม่มี provider ที่สอง
- answer-leak check (AM-13) · ต้องมีโจทย์ที่ค้างอยู่ใน flow จริงก่อน
- quota token ต่อ user/วัน และต่อ tenant ตาม plan (§2.10 ควบคุมต้นทุน, SA-04)
- rate limit ที่นับรวมทุก instance (Redis หรือตารางใน DB)
- ข้อความภาษาไทยเมื่อได้ `429` ในหน้าเว็บ (TM-21 "ระบบต้องบอก user" ฝั่ง UI · งานของ May)
- เปิด `AI_PROVIDER=live` บน `api-staging` (ยังต้องตั้ง auth env + runtime SA · Junior)

## 10. Open questions

**ตัดสินแล้ว (Jam 2026-11-01): ตามข้อเสนอทั้ง 6 ข้อ** (§2 เขียนตามนั้นแล้ว) · ข้อ 1–4 เป็นโครงสร้าง backend จึงเป็นข้อเสนอที่ Junior เปลี่ยนได้ทีหลังใน PR ใหม่ · ข้อ 1 ทำแบบนับต่อ IP ไว้ก่อน และถือว่าห้ามเปิด `AI_PROVIDER=live` บน staging ขณะที่ `AUTH_REQUIRED=false`

1. **ไม่มี token นับต่อ IP:** ข้อเสนอคือใช้ค่าแรกของ `X-Forwarded-For` · ค่านี้ client ปลอมได้ถ้ายิงตรงไม่ผ่าน load balancer · บน Cloud Run ค่าแรกมาจาก client จึงปลอมได้เช่นกัน · ทางเลือก: (ก) ใช้ค่าสุดท้ายที่ Google ใส่ (ข) ไม่นับคนที่ไม่มี token เลย แล้วบังคับว่าห้ามเปิด live ถ้า `AUTH_REQUIRED=false` · Claude เอนไปทาง (ข) + ข้อเสนอนี้เป็นทางกันชั่วคราว
2. **`POST /exam-preps/{id}/sessions` ควรนับไหม:** endpoint นี้เรียก AI ทำข้อความเปิด (ตอนนี้ยังเป็น stub) · §2.9 พูดแค่ "ข้อความ" · ข้อเสนอคือยังไม่นับ
3. **request ที่ body ผิดนับไหม:** ข้อเสนอคือนับ (กันยิง body เสียรัวๆ) · ถ้าไม่นับ ต้องตรวจ body ก่อนนับ
4. **ตัวนับและ breaker อยู่ในหน่วยความจำต่อ instance:** `api-staging` มีได้ถึง `--max-instances=2` · ผู้ใช้คนหนึ่งจึงส่งได้สูงสุดราว `2 × L` ต่อนาทีในกรณีแย่สุด · ข้อเสนอคือพอสำหรับ staging และ Alpha · ย้ายไปเก็บร่วมกันตอนทำ quota ต่อ plan
5. **half-open ปล่อยกี่ call:** Resilience4j ปล่อย 10 call (`permittedNumberOfCallsInHalfOpenState`) แต่ `ai.yaml` ไม่มีค่านี้ · ข้อเสนอคือปล่อย 1 call (ไม่ต้องเพิ่มค่าใน config ซึ่งเป็นไฟล์ร่วม) · ถ้าจะใช้ 10 ต้องเพิ่ม `half_open_calls` ใน `ai.yaml` พร้อมป้าย [B]
6. **call ที่ breaker ปฏิเสธต้องลง `ai_calls` ไหม:** ข้อเสนอคือไม่ลง (ไม่ได้เรียก AI · AI-04 log token ของ call ที่เกิดขึ้นจริง) · log `warning` ตอนเปลี่ยนสถานะพอใช้ดูใน Cloud Logging · ถ้าอยากนับว่าผู้ใช้เจอ degrade กี่ครั้ง ใช้ status `degraded` ที่ check constraint ของ `ai_calls` มีอยู่แล้วได้

## 11. Spec changes needed

- **api.md** (ไฟล์ร่วม · Junior): เพิ่ม `429` `rate_limited` + `Retry-After` ใน Conventions (Error) และใน `POST /sessions/{id}/messages`, `POST /sessions/{id}/ocr/confirm`
- **architecture.md** "สร้างแล้วหรือยัง": แถว AI gateway เปลี่ยนเป็นมี circuit breaker + rate limit (ยังไม่มี fallback และ answer-leak check) · ทำใน PR เดียวกับโค้ด
- **ai-orchestration.md** §2.10: Circuit breaker เขียนว่า "error ≥ 50% จากอย่างน้อย 10 calls" · ไม่ได้บอกขนาดหน้าต่าง (`ai.yaml` ใช้ 100) และไม่ได้บอกพฤติกรรม half-open · เสนอให้เพิ่มประโยคอ้างถึง spec นี้ (Jam เป็นเจ้าของ ai-orchestration)
- ไม่ต้องแก้ `config/ai.yaml` (ค่าทั้งหมดมีอยู่แล้ว)
