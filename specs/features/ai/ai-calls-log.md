# Feature: AI gateway เขียน `CallRecord` ลงตาราง `ai_calls`

| | |
|---|---|
| Area | platform |
| Requirements | AI-04, SA-06, NFR-P1 |
| Owner | Jam (item of Junior · solo time 31 ต.ค. 2569) |
| Reviewer | Jam · Junior (ข้อที่เป็นเรื่อง backend/DB ใน §10) |
| Status | approved (Jam 2026-10-31 · §10 ข้อ 2–4 ตามข้อเสนอ · ข้อ 1, 5 ใช้ข้อเสนอไปก่อน รอ Junior) |
| Related system spec | `ai-orchestration.md` §2.11 (`ai_calls`, Monitoring), §2.10 (cost) · `data-model.md` (Logs) · `0001_init.sql` `ai_calls` + policy `tenant_rows` (select อย่างเดียว) · `apps/api/CLAUDE.md` "Database" · `api.md` Conventions (`X-Request-Id`) |

## 1. Context

Gateway (`app/ai/gateway.py`) ส่ง `CallRecord` 1 ตัวต่อ `call` / `stream` / `embed` ให้ listener อยู่แล้ว (AI-04) แต่ยังไม่มี listener ตัวไหนเก็บผล · ตาราง `ai_calls` มีใน `0001_init.sql` แต่ยังไม่มีแถว · P4-lite ต้องดูต้นทุนต่อ session จาก log ของ gateway (`ai-orchestration.md` §3.6 แถว "TTFT และต้นทุน") · feature นี้เพิ่ม listener ที่ (1) เขียน log 1 บรรทัดแบบ structured JSON ทุก call และ (2) insert 1 แถวลง `ai_calls` เมื่อรู้ว่า call นี้เป็นของ tenant ไหน · ตอนนี้ API ยังไม่ตรวจ JWT (checklist ⚠️ 28 ต.ค.) จึงยังไม่มี request ไหนรู้ tenant · feature นี้เตรียมที่ให้ JWT ใส่ tenant ไว้ (§2 ข้อ 1) โดยไม่ต้องแก้ gateway อีก

## 2. Behavior

**1. Context ของ call** (module ใหม่ `app/ai/call_context.py`)

- contextvar `AICallContext(tenant_id: UUID, user_id: UUID | None, session_id: UUID | None)` · ค่าเริ่มต้นคือ `None` (ไม่รู้ tenant)
- ตั้งค่าด้วย `with ai_call_context(tenant_id=..., user_id=..., session_id=...):` · ออกจาก `with` แล้วกลับเป็นค่าเดิม · ซ้อนกันได้ (ตัวในทับตัวนอก)
- ผู้ตั้งค่า: dependency ที่ตรวจ JWT (Junior · ยังไม่มี · §10 ข้อ 1) ตั้ง `tenant_id`, `user_id` · service ที่รู้ session (เช่น `tutor_turn`) ตั้ง `session_id` · feature นี้**ไม่**ตั้งค่าใน request จริง
- `request_id` ไม่อยู่ใน context นี้ อ่านจาก `app.middleware.get_request_id()` ที่มีอยู่แล้ว

**2. แปลง `CallRecord` เป็นแถว** (ฟังก์ชัน pure `to_row(record, context, request_id) -> dict`)

| คอลัมน์ `ai_calls` | ค่า |
|---|---|
| `tenant_id`, `user_id`, `session_id` | จาก `AICallContext` |
| `request_id` | `get_request_id()` · `None` นอก request (เช่น eval, PoC) |
| `purpose`, `provider`, `model` | จาก `CallRecord` ตรงๆ |
| `prompt_version` | `CallRecord.prompt_version` · ยกเว้น `"none"` (ของ `embed` ที่ไม่มี prompt) → `null` (§10 ข้อ 4) |
| `tokens_in`, `tokens_out` | จาก `CallRecord` |
| `cached_tokens` | `null` (provider ยังไม่รายงาน · §9) |
| `latency_ms` | `round(CallRecord.latency_ms)` (คอลัมน์เป็น `integer`) |
| `cost_usd` | `null` (§10 ข้อ 2) |
| `status` | ตาราง map ด้านล่าง |
| `fallback_used` | `false` (gateway lite ยังไม่มี fallback · §9) |

Map `status` (check ของตาราง: `ok`, `schema_retry`, `fallback`, `degraded`, `error`):

| `CallRecord.status` | `schema_retries` | `ai_calls.status` |
|---|---|---|
| `ok` | 0 | `ok` |
| `ok` | ≥ 1 | `schema_retry` (ได้ผลแต่ต้อง retry schema) |
| `schema_error` | ใดๆ | `error` |
| `provider_error` | ใดๆ | `error` |

`fallback` และ `degraded` ยังไม่มีใครส่ง (gateway lite ไม่มี fallback · template "ระบบช้า" เป็นของ `tutor_turn` ไม่ใช่ gateway) · §10 ข้อ 3

**3. Listener `AICallLog`** (`app/db/ai_calls.py` · ผูกกับ gateway ด้วย `add_listener`)

1. ทุก record: เขียน log 1 บรรทัดที่ logger `app.ai.calls` ระดับ INFO · message เป็น JSON ของแถวจากข้อ 2 (UUID เป็น string) บวก `schema_retries` · ไม่มีข้อความ prompt หรือคำตอบ · Cloud Run ส่ง stdout เข้า Cloud Logging (§2.11 Monitoring)
2. ถ้า context มี `tenant_id` **และ** listener มี writer: insert แถวลง `ai_calls` · ถ้าไม่มี tenant: ไม่ insert (มีแค่ log ข้อ 1)
3. การ insert **ไม่ทำให้ AI call รอ**: listener ส่งงานไปทำเบื้องหลังแล้วคืนทันที (NFR-P1 · ไม่เพิ่ม TTFT) · gateway คืนผลหรือส่ง chunk ต่อได้โดยไม่ขึ้นกับ DB
4. Insert ล้ม (DB ล่ม, network, constraint): log ระดับ WARNING พร้อม `request_id` และ purpose แล้วจบ · ไม่ retry · ไม่ raise กลับไปที่ call (gateway จับ exception ของ listener อยู่แล้ว แต่งานเบื้องหลังต้องจับเองด้วย)
5. Writer ใช้ supabase-py กับ **service role key** และใส่ `tenant_id` เองเสมอ (`apps/api/CLAUDE.md` "Database" · policy ของ `ai_calls` ให้ user แค่ select จึงใช้ JWT ของ user insert ไม่ได้) · §10 ข้อ 1

**4. ต่อเข้ากับ gateway** (`build_default_gateway()`)

- ทุก mode (fake และ live) ใส่ `AICallLog` เสมอ
- มี writer เมื่อ `SUPABASE_URL` และ `SUPABASE_SERVICE_ROLE_KEY` มีค่าทั้งคู่ · ไม่ครบ → listener ทำแค่ข้อ 3.1 (dev ในเครื่องที่ไม่เปิด Supabase, CI unit test)
- Gateway ที่สร้างเองใน test, eval (`evals/run_checker.py`) และ PoC ไม่ได้ผ่าน `build_default_gateway()` จึงไม่เปลี่ยนพฤติกรรม

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | `CallRecord` (เดิม) + `AICallContext \| None` + `request_id: str \| None` | `CallRecord(purpose="tutor_reply", provider="vertex", model="gemini-3.5-flash", prompt_version="v1", status="ok", tokens_in=812, tokens_out=164, latency_ms=3712.4, schema_retries=0)` · context tenant `T1`, user `U1`, session `S1` |
| Output (DB) | 1 แถว `ai_calls` | `{tenant_id: T1, user_id: U1, session_id: S1, request_id: "6f1c…", purpose: "tutor_reply", provider: "vertex", model: "gemini-3.5-flash", prompt_version: "v1", tokens_in: 812, tokens_out: 164, cached_tokens: null, latency_ms: 3712, cost_usd: null, status: "ok", fallback_used: false}` |
| Output (log) | 1 บรรทัด JSON ที่ logger `app.ai.calls` | `{"purpose": "tutor_reply", …, "tenant_id": null, "schema_retries": 0}` |

## 4. Acceptance criteria

ทุกข้อใช้ fake provider และ writer ปลอม ยกเว้นข้อที่บอกว่าเป็น integration (Supabase ในเครื่อง)

**แปลงแถว (`to_row`)**

- **AC-1 (AI-04)** Given record `ok`, `schema_retries=0` และ context ครบ (tenant, user, session) และ request id When `to_row` Then ได้ทุกคอลัมน์ตามตาราง §2 ข้อ 2 · `status="ok"` · `fallback_used=false` · `cached_tokens` และ `cost_usd` เป็น `null`
- **AC-2 (AI-04)** Given record `ok` ที่ `schema_retries=1` When `to_row` Then `status="schema_retry"` · และ `schema_retries=0` ได้ `"ok"` (ขอบของตาราง map)
- **AC-3 (AI-04)** Given record `schema_error` หรือ `provider_error` (parametrize ทั้งสอง) When `to_row` Then `status="error"`
- **AC-4 (AI-04)** Given record ของ `embed` (`prompt_version="none"`) When `to_row` Then `prompt_version` เป็น `null`
- **AC-5 (AI-04)** Given `latency_ms=3712.6` When `to_row` Then `latency_ms=3713` (int)
- **AC-6 (AI-04)** Given context ที่มีแต่ tenant (`user_id`, `session_id` เป็น `None`) และไม่มี request id When `to_row` Then `user_id`, `session_id`, `request_id` เป็น `null`

**Context**

- **AC-7 (AI-04)** Given ไม่ได้ตั้ง context When อ่าน context Then ได้ `None` · Given `with ai_call_context(tenant_id=T1)` ซ้อนด้วย `with ai_call_context(tenant_id=T1, session_id=S1)` When อ่านในชั้นใน Then ได้ `session_id=S1` · ออกจากชั้นในแล้วได้ `session_id=None` · ออกจากชั้นนอกแล้วได้ `None`

**Listener กับ gateway (end to end ด้วย fake)**

- **AC-8 (AI-04)** Given gateway ที่มี `AICallLog` กับ writer ปลอม และ context มี tenant When `await gateway.call(...)` สำเร็จ 1 ครั้ง Then writer ได้ 1 แถว · `tokens_in`, `tokens_out` ตรงกับ record
- **AC-9 (AI-04)** Given เหมือน AC-8 When `gateway.stream(...)` อ่านจนจบ Then writer ได้ 1 แถวของ purpose นั้น `status="ok"` · และเมื่อ `gateway.embed(...)` 1 ครั้ง Then ได้ 1 แถว `purpose="embed"`
- **AC-10 (AI-04)** Given gateway ที่ provider ล้มทุกครั้ง และ context มี tenant When `call` (raise `AIProviderError`) Then writer ยังได้ 1 แถว `status="error"` และ error เดิมยังถึงผู้เรียก
- **AC-11 (AI-04)** Given ไม่มี context (ไม่รู้ tenant) When `call` สำเร็จ Then writer ไม่ได้แถวเลย · มี log 1 บรรทัดที่ logger `app.ai.calls` ระดับ INFO ที่ parse เป็น JSON ได้ และ `tenant_id` เป็น `null`
- **AC-12 (AI-04)** Given context มี tenant When `call` สำเร็จ Then มี log 1 บรรทัดเหมือน AC-11 (แต่ `tenant_id` เป็น string ของ T1) **และ** writer ได้ 1 แถว · log ไม่มีข้อความ prompt หรือคำตอบของ model
- **AC-13 (AI-04, NFR-P1)** Given writer ปลอมที่หน่วงไว้จนกว่า test จะปล่อย When `await gateway.call(...)` Then `call` คืนผลก่อน writer ทำเสร็จ (gateway ไม่รอ DB)
- **AC-14 (AI-04)** Given writer ปลอมที่ raise ตอน insert When `call` Then `call` คืนผลปกติ · มี log ระดับ WARNING 1 บรรทัดที่มี purpose · ไม่มี exception หลุดออกมาจากงานเบื้องหลัง

**ต่อเข้ากับ `build_default_gateway()`**

- **AC-15 (AI-04)** Given `AI_PROVIDER=fake` และไม่มี `SUPABASE_URL` When `build_default_gateway()` Then gateway มี `AICallLog` ที่ไม่มี writer (call ได้ log, ไม่พยายามต่อ DB)
- **AC-16 (AI-04)** Given `AI_PROVIDER=fake`, `SUPABASE_URL` และ `SUPABASE_SERVICE_ROLE_KEY` มีค่า When `build_default_gateway()` Then `AICallLog` มี writer ของ Supabase (ตรวจโดยไม่ต่อ network จริง)

**DB (integration · Supabase ในเครื่อง)**

- **AC-17 (AI-04)** Given writer ของ Supabase ด้วย service role When insert แถวจาก `to_row` ของ tenant A Then อ่านด้วย service role เจอ 1 แถว ค่าตรงกัน · check constraint ของ `status` รับทุกค่าที่ map ได้ (`ok`, `schema_retry`, `error`)
- **AC-tenant (SA-06)** Given แถว `ai_calls` ของ tenant A และ tenant B (seed ด้วย service role) When user A select `ai_calls` ด้วย JWT ของตัวเอง Then เห็นเฉพาะแถวของ A · And user A insert `ai_calls` ด้วย JWT ของตัวเอง Then ถูกปฏิเสธ (policy เป็น select อย่างเดียว) · เพิ่มใน `tests/integration/test_rls_isolation.py`

**ไม่มี** AC-boundary ของ threshold: feature นี้ไม่ใช้ค่าใน `config/learning.yaml` · ขอบเดียวคือ `schema_retries` 0 / 1 ใน AC-2

## 5. Data changes

ไม่มี · ใช้ `ai_calls` ใน `0001_init.sql` ตามเดิมทุกคอลัมน์ · ไม่แก้ policy

## 6. API / SSE changes

ไม่มี

## 7. AI calls

ไม่มี (feature นี้บันทึก call ของ purpose อื่น ไม่เรียก AI เอง)

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `test_AI04_row_has_every_column_of_the_record` | unit | AC-1 |
| `test_AI04_status_schema_retry_from_one_retry` (parametrize 0 / 1) | unit | AC-2 |
| `test_AI04_failed_record_maps_to_error` (parametrize 2 status) | unit | AC-3 |
| `test_AI04_embed_has_null_prompt_version` | unit | AC-4 |
| `test_AI04_latency_rounded_to_int` | unit | AC-5 |
| `test_AI04_missing_context_fields_are_null` | unit | AC-6 |
| `test_AI04_call_context_nests_and_resets` | unit | AC-7 |
| `test_AI04_call_writes_one_row_with_tenant` | unit | AC-8 |
| `test_AI04_stream_and_embed_write_one_row_each` | unit | AC-9 |
| `test_AI04_failed_call_still_writes_error_row` | unit | AC-10 |
| `test_AI04_no_tenant_logs_but_does_not_write` | unit | AC-11 |
| `test_AI04_log_line_is_json_without_prompt_text` | unit | AC-12 |
| `test_AI04_call_does_not_wait_for_the_writer` | unit | AC-13 |
| `test_AI04_writer_failure_only_warns` | unit | AC-14 |
| `test_AI04_default_gateway_logs_without_supabase` | unit | AC-15 |
| `test_AI04_default_gateway_writes_with_supabase_env` | unit | AC-16 |
| `test_AI04_service_role_inserts_ai_calls_row` | integration | AC-17 |
| `test_SA06_ai_calls_isolated_and_not_insertable_by_users` | integration | AC-tenant |

Test unit อยู่ใน `apps/api/tests/unit/test_ai_calls_log.py` · integration อยู่ใน `tests/integration/`

## 9. Out of scope

- ตรวจ JWT และตั้ง `tenant_id` / `user_id` ให้ทุก request (Junior · checklist ⚠️ 28 ต.ค.) · ตั้ง `session_id` ใน `tutor_turn` (ทำพร้อมการบันทึก `messages` · `tutor-reply-stream.md` §9)
- `cached_tokens`: provider ยังไม่ส่ง `cached_content_token_count` ออกมาใน `ProviderResponse` / `StreamUsage`
- `fallback_used` และ `status` `fallback` / `degraded`: มาพร้อม fallback provider และ circuit breaker (เทอม 2 ตาม P4-lite)
- เก็บ prompt/response เต็ม 30 วัน (§2.11 Retention) · dashboard TTFT p95, error rate, cost/วัน/tenant · quota token ต่อ user/วัน (§2.10)
- รอ insert ที่ค้างอยู่ให้เสร็จตอน Cloud Run ปิด instance (§10 ข้อ 5)

## 10. Open questions

1. **(Junior · backend)** `app/db/` ใช้ supabase-py + service role key (มีใน dependency และ `test_rls_isolation.py` ใช้อยู่แล้ว) หรือ psycopg ผ่าน `DATABASE_URL`? · ข้อเสนอ: supabase-py ไปก่อน · writer เป็น interface เล็กๆ (`insert(row)`) Junior เปลี่ยนทีหลังได้โดยไม่แก้ listener · และ JWT dependency จะตั้ง `ai_call_context` ตามข้อ §2.1 ไหม
2. **(Jam · cost)** `cost_usd` ปล่อย `null` ใน feature นี้ (ข้อเสนอ) หรือเพิ่มตารางราคาต่อ model ใน `config/ai.yaml` (ไฟล์กลาง · ต้องมีที่มาของราคา) แล้วคำนวณจาก token? · ถ้า `null` P4-lite คิดต้นทุนเองจาก `tokens_in` / `tokens_out` ใน log
3. **(Jam)** ตาราง map `status` ใน §2 ข้อ 2 โอเคไหม · โดยเฉพาะ `schema_error` → `error` (ตารางไม่มีค่า `schema_error`) และ stream ที่ผู้เรียกหยุดกลางทาง (gateway ส่ง `provider_error`) → `error`
4. **(Jam)** `prompt_version` ของ `embed` เป็น `null` แทน `"none"` โอเคไหม
5. **(Junior · deploy)** insert ที่ยังค้างตอน instance ปิดจะหาย (ไม่กี่แถว · log ข้อ 3.1 ยังอยู่) · รับได้ใน P4-lite ไหม หรือให้ lifespan ของ FastAPI รอก่อนปิด (ต้องมีค่า timeout ใหม่ใน config)

## 11. Spec changes needed

- `ai-orchestration.md` §2.11 เขียนว่า "`ai_calls` เก็บทุก call" แต่ `tenant_id` เป็น `not null` · call ที่ไม่รู้ tenant (eval, PoC, request ที่ยังไม่ตรวจ JWT) จึงลงตารางไม่ได้ · เสนอเพิ่มประโยค: "call ที่ไม่มี tenant (eval, PoC) เขียนเฉพาะ log ใน Cloud Logging" (ไฟล์ของ Jam)
- ถ้าเลือกตารางราคาใน §10 ข้อ 2: เพิ่ม `pricing` ใน `config/ai.yaml` (ไฟล์กลาง · บอกกลุ่ม) และอ้างถึงใน §2.10
