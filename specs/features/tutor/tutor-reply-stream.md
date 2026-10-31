# Feature: ห้องติว stream คำตอบ tutor จาก gateway (P4-lite)

| | |
|---|---|
| Area | tutor / platform |
| Requirements | AI-01, AI-02, AI-03, NFR-P1, TM-08 |
| Owner | Jam (item of Junior · solo time 31 ต.ค. 2569) |
| Reviewer | Jam · Junior (ข้อ "รอตัดสิน" ของ backend ใน §10) |
| Status | approved (Jam 2026-10-31 · §10 ข้อ 1, 3 ใช้ข้อเสนอไปก่อน รอ Junior) |
| Related system spec | `specs/poc/README.md` P4-lite · `api.md` "ห้องติว", "SSE events", Conventions · `ai-orchestration.md` §2.2.3, §2.2.7, §2.9, §2.10 · `config/ai.yaml` → `purposes.tutor_reply`, `guards`, `targets` |

## 1. Context

ตอนนี้ `POST /sessions/{id}/messages` เป็น stub (PR #38) ที่ส่ง `app/stubs/tutor_reply.sse` ทั้งก้อน · May ต่อหน้าแชทกับ stub แล้ว (`room-http.md`) และวัด overhead ของ infra ได้ TTFT p95 0.15 วินาที (`poc/P4-lite/README.md` บน branch `poc/P4-lite-ttft`) · feature นี้เปลี่ยนเฉพาะข้อความที่เป็น **text** ให้ไปเรียก `tutor_reply` ผ่าน gateway แบบ stream แล้วส่งเป็น event `token` ทีละชิ้น เพื่อให้ P4-lite วัด TTFT กับ model จริงได้ และสลับ fake ↔ live ได้ด้วย config · ตาม P4-lite: ไม่มี stage machine, planner และ buddy (ย้ายไปเทอม 2)

## 2. Behavior

**Gateway: `ai.stream(purpose, input)`** (เพิ่มคู่กับ `ai.call` ใน `app/ai/gateway.py` · AI-01)

1. อ่าน `purposes.<purpose>` จาก `config/ai.yaml` · ถ้าไม่มี purpose หรือ `stream` ไม่ใช่ `true` → `AIConfigError` (ไม่เรียก provider)
2. โหลด prompt `prompts/<purpose>/v<n>.md` และเติม placeholder แบบเดียวกับ `call` · route ตาม tier (รวม `AI_MODEL_OVERRIDE`) แบบเดียวกับ `call`
3. เรียก provider แบบ stream ด้วย `temperature`, `max_tokens`, `thinking` ของ purpose · คืน async iterator ของข้อความทีละชิ้น **ตามที่ provider ส่งมา** ไม่รวมก้อน ไม่แก้ตัวอักษร (ไม่ซ่อม backslash แบบ `app/ai/latex.py` เพราะไม่ใช่ JSON) · ชิ้นที่เป็น string ว่างไม่ส่งต่อ
4. **Retry เฉพาะก่อนได้ชิ้นแรก:** ถ้า provider ล้มหรือ rate limit ก่อนส่งชิ้นแรก ใช้กติกาเดียวกับ `call` (`gateway.retries`, `retry_backoff_seconds`, `max_retry_wait_seconds`) · หลังได้ชิ้นแรกแล้วไม่ retry (ส่งให้ user ไปแล้ว ดึงคืนไม่ได้) และส่ง error ต่อให้ผู้เรียก
5. Timeout ของทั้ง stream = `timeout_s` ของ purpose · เกินแล้วถือเป็น provider error ตามข้อ 4
6. ไม่มี schema validation (ผลเป็นข้อความอิสระ)
7. ส่ง `CallRecord` 1 ครั้งเมื่อ stream จบ (สำเร็จ, ล้ม หรือผู้เรียกหยุดกลางทาง) · `status` = `ok` เมื่อจบครบ ไม่เช่นนั้น `provider_error` · `latency_ms` = เวลาทั้ง stream · token นับจาก usage ที่ provider รายงาน (fake ใช้ค่าประมาณแบบเดียวกับ `generate`)

**Provider** (`app/ai/providers/`): protocol เพิ่ม `stream(request)` คืน async iterator ของชิ้นข้อความ และ usage ตอนจบ

- **Fake (AI-03):** script เดิม (`purpose → [str | Exception]`) · stream แบ่งข้อความที่ script ไว้เป็นชิ้นตามกติกาคงที่ (ผลเหมือนเดิมทุกครั้ง) · `Exception` ใน script → raise ก่อนชิ้นแรก · ให้ test สั่ง "ล้มหลังชิ้นที่ k" และหน่วงระหว่างชิ้นได้
- **Gemini / Vertex:** ใช้ streaming API ของ SDK ใน `app/ai/providers/gemini.py` เท่านั้น (AI-01) · ไม่ตั้ง `response_mime_type` เป็น JSON

**Endpoint `POST /sessions/{id}/messages`**

1. Body ตาม `SendMessageRequest` เดิม (ส่ง `text` หรือ `image_path` อย่างใดอย่างหนึ่ง)
2. `text` ยาวเกิน `guards.max_message_chars` (นับตัวอักษร) → ตอบ `422` แบบ `ErrorResponse` ก่อนเรียก AI · code ดู §10 ข้อ 3
3. `text` → service `tutor_turn` เรียก `ai.stream("tutor_reply", {"message": text})` แล้วส่งแต่ละชิ้นเป็น `token {speaker: "tutor", text: <ชิ้น>}` ตามลำดับ · จบด้วย `done {}` · response **ไม่มี** header `X-Stub`
4. Provider ล้ม**ก่อน**ส่ง token แรก (หลัง retry แล้ว): ส่ง `token {speaker: "tutor", text: "ระบบช้า ลองส่งอีกทีนะ"}` แล้ว `done {}` (api.md "ระบบช้า")
5. Provider ล้ม**หลัง**ส่ง token ไปแล้ว: ส่ง `error {code, message}` แล้วจบ stream (ไม่มี `done`) · หน้าเว็บแสดง "ส่งไม่สำเร็จ ลองส่งอีกทีนะ" และเก็บ bubble ที่ได้แล้วไว้ (`chat-streaming.md` AC-13) · code ดู §10 ข้อ 3
6. `image_path` → ยังเป็น stub เดิม (flow รูป, `ocr_preview`, `ocr/confirm` เป็น feature แยก) · ดู §10 ข้อ 2
7. ทุก event ผ่าน model ใน `app/models/room.py` (`TokenEvent`, `DoneEvent`, `ErrorEvent`) จึงผ่าน `test_room_api_contract.py` เดิม
8. ถ้า client ตัดการเชื่อมต่อกลาง stream: หยุดอ่านจาก provider (ไม่อ่านต่อจนจบ)

**Prompt `prompts/tutor_reply/v1.md`** (Jam · frontmatter ตาม `prompts/README.md`)

- layer ที่ P4-lite มี: 1 System (บทบาท tutor ภาษาไทย, รูปแบบสมการตาม api.md Conventions: `$…$`, `$$…$$`, `\$` สำหรับเครื่องหมายเงิน) และ 10 Input (ข้อความ user ใน placeholder `{{message}}`) · layer 2–9 ของ §2.2.3 ต้องใช้ DB และ planner จึงยังไม่มี
- ไม่มีข้อมูลส่วนตัวของ user ใน prompt (§2.9 Data)

**Fake ตอน `AI_PROVIDER=fake` (staging, dev):** gateway แบบ default ต้องตอบ `tutor_reply` ได้ (ตอนนี้ `FakeProvider({})` ไม่มี script จึงจะล้มทุกข้อความ) · ข้อความที่ script ไว้ดู §10 ข้อ 4

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | `POST /sessions/{id}/messages` body `SendMessageRequest` `{text}` | `{"text": "แยกตัวประกอบ $x^2-49$ ยังไง"}` |
| Output (สำเร็จ) | SSE: `token {speaker:"tutor", text}` × n → `done {}` | `event: token` / `data: {"speaker":"tutor","text":"ใช้ผลต่างกำลังสอง "}` … `event: done` / `data: {}` |
| Output (ล้มก่อน token แรก) | `token` ข้อความ template → `done {}` | `data: {"speaker":"tutor","text":"ระบบช้า ลองส่งอีกทีนะ"}` |
| Output (ล้มกลาง stream) | `token` × k → `error {code, message}` | `event: error` / `data: {"code":"ai_unavailable","message":"..."}` |
| Output (ข้อความยาวเกิน) | `422` `ErrorResponse` | `{"error":{"code":"…","message":"…"}}` |
| Gateway | `ai.stream(purpose: str, input: dict) -> AsyncIterator[str]` | `async for chunk in ai.stream("tutor_reply", {"message": text})` |

## 4. Acceptance criteria

ทุกข้อใช้ fake provider (`AI_PROVIDER=fake` หรือ inject `FakeProvider`) · ไม่เรียก model จริง

**Gateway**

- **AC-1 (AI-01)** Given `tutor_reply` ใน config มี `stream: true` และ prompt v1 When `ai.stream("tutor_reply", {"message": "สวัสดี"})` Then provider ได้ request ที่ `purpose = "tutor_reply"`, model ตาม tier `main`, `temperature`/`max_tokens`/`thinking` ตาม config และ prompt ที่มี "สวัสดี" แทน `{{message}}`
- **AC-2 (AI-01)** Given purpose ที่ไม่มีใน config หรือ purpose ที่ `stream` ไม่ใช่ `true` (เช่น `check_answer`) When `ai.stream(...)` Then `AIConfigError` และ provider ไม่ถูกเรียก
- **AC-3 (AI-03)** Given fake script `tutor_reply: ["ถูกแล้ว $x^2$"]` When stream 2 รอบด้วย script เดียวกัน Then ได้ลำดับชิ้นเหมือนกันทั้ง 2 รอบ และต่อกันได้ "ถูกแล้ว $x^2$" พอดี
- **AC-4 (TM-08)** Given fake stream ชิ้น `"$\\frac{1}{2}"`, `"\\neq \\theta$"` When stream Then ได้ชิ้นตรงตามนั้นทุกตัวอักษร (backslash ไม่หาย ไม่ถูกซ่อม ไม่ถูกรวมชิ้น)
- **AC-5 (AI-01)** Given fake stream ชิ้น `"ก"`, `""`, `"ข"` When stream Then ได้ `"ก"`, `"ข"` (ชิ้นว่างไม่ส่งต่อ)
- **AC-6 (AI-01)** Given script `tutor_reply: [RuntimeError, "ตอบได้"]` และ `gateway.retries = 1` When stream Then provider ถูกเรียก 2 ครั้ง และได้ "ตอบได้"
- **AC-6b (AI-01)** Given script `tutor_reply: [ProviderRateLimited(retry_after = max_retry_wait_seconds + 1), "ตอบได้"]` When stream Then ไม่ retry และ error ส่งถึงผู้เรียก · Given `retry_after = max_retry_wait_seconds` Then retry 1 ครั้งและได้ "ตอบได้" (ค่าอ่านจาก `config/ai.yaml` → `gateway`)
- **AC-7 (AI-01)** Given fake ที่ส่งชิ้นแรกแล้วล้ม When stream Then ได้ชิ้นแรก แล้ว error ส่งถึงผู้เรียก และ provider ถูกเรียกแค่ 1 ครั้ง (ไม่ retry หลังได้ชิ้นแรก)
- **AC-8 (AI-01)** Given fake หน่วงจนเกิน `timeout_s` ของ `tutor_reply` ก่อนชิ้นแรก When stream Then ถือเป็น provider error ตาม AC-6 (retry แล้วจึงส่ง error) · ค่า timeout อ่านจาก config ที่ test ตั้งให้สั้น
- **AC-9 (AI-01)** Given stream สำเร็จ / ล้มกลางทาง / ผู้เรียกหยุดอ่านหลังชิ้นแรก When จบ Then listener ได้ `CallRecord` **1** ครั้งต่อ stream ที่ `purpose = "tutor_reply"`, `prompt_version = "v1"` และ `status` = `ok` / `provider_error` / `provider_error` ตามลำดับ
- **AC-10 (AI-02)** Given `AI_PROVIDER=fake` When `build_default_gateway()` แล้ว `stream("tutor_reply", ...)` Then ได้ข้อความตาม §10 ข้อ 4 โดยไม่ต้องตั้งค่าอื่น · และ `app/routers/`, `app/services/` ไม่ import `app.ai.providers` หรือ SDK ของ provider

**Endpoint**

- **AC-11 (NFR-P1)** Given fake ส่ง `"ถูก"` แล้วรอสัญญาณจาก test ก่อนส่ง `"แล้ว"` When ส่ง `{text: "x"}` Then client ได้ `token {speaker:"tutor", text:"ถูก"}` **ก่อน** test ปล่อยชิ้นที่ 2 (ไม่ buffer ทั้งก้อน) · หลังปล่อยได้ `token "แล้ว"` แล้ว `done {}`
- **AC-12 (AI-01)** Given fake ส่ง 3 ชิ้น When ส่ง `{text: "x"}` Then ได้ `token` 3 อันตามลำดับ ทุกอัน `speaker = "tutor"` แล้ว `done {}` เป็น event สุดท้าย · response ไม่มี header `X-Stub` · ทุก event ผ่าน model ใน `app/models/room.py`
- **AC-13 (AI-01)** Given fake ล้มทุกครั้ง (เกิน retry) ก่อนชิ้นแรก When ส่ง `{text: "x"}` Then ได้ `token {speaker:"tutor", text:"ระบบช้า ลองส่งอีกทีนะ"}` แล้ว `done {}` และไม่มี `error`
- **AC-14 (AI-01)** Given fake ส่ง `"ถูก"` แล้วล้ม When ส่ง `{text: "x"}` Then ได้ `token "ถูก"` แล้ว `error` ที่มี `code` และ `message` เป็น event สุดท้าย และไม่มี `done`
- **AC-15 (AI-01)** Given ข้อความ `text` ยาว `guards.max_message_chars` ตัวอักษร When ส่ง Then ได้ stream ปกติ · Given ยาว `max_message_chars + 1` Then `422` แบบ `ErrorResponse` และ provider ไม่ถูกเรียก · Given ยาว `max_message_chars − 1` Then stream ปกติ (นับเป็นตัวอักษร: test ใช้อักษรไทยด้วย)
- **AC-16 (AI-01)** Given body `{image_path: "a/b.jpg"}` When ส่ง Then พฤติกรรมเดิมของ stub (ตาม §10 ข้อ 2) และ provider ไม่ถูกเรียก
- **AC-17 (TM-08)** Given fake ส่ง `"$$a^2 - b^2"`, `" = (a-b)(a+b)$$"` When ส่ง Then `token.text` ใน SSE เป็น 2 ชิ้นนั้นตรงตัวอักษร (JSON ของ `data` decode แล้วได้ backslash และ `$` ครบ)
- **AC-18 (AI-01)** Given client ปิดการเชื่อมต่อหลังได้ token แรก When fake ยังมีชิ้นเหลือ Then fake ไม่ถูกอ่านจนจบ (ชิ้นที่ยังไม่ได้ส่งไม่ถูกขอ) และมี `CallRecord` 1 อัน
- **AC-contract** `test_room_api_contract.py` ผ่านโดยไม่แก้

**Tenant (SA-06):** feature นี้ไม่อ่านและไม่เขียน DB (§10 ข้อ 1) จึงยังไม่มี AC-tenant · เมื่อ Junior ตัดสินให้บันทึก `messages` ต้องเพิ่ม AC ว่า user ของ tenant อื่นส่งข้อความเข้า session นี้ไม่ได้

## 5. Data changes

ไม่มี (ไม่แตะ DB · ดู §10 ข้อ 1)

## 6. API / SSE changes

| Endpoint / event | Request | Response |
|---|---|---|
| `POST /sessions/{id}/messages` (มีใน api.md แล้ว) | `{text}` | SSE จาก gateway แทน stub · ไม่มี `X-Stub` · event ที่ใช้: `token`, `done`, `error` (มีใน api.md แล้ว) |
| `POST /sessions/{id}/messages` | `{image_path}` | ไม่เปลี่ยน (stub) |
| ข้อความยาวเกิน | `{text}` ยาวเกิน `guards.max_message_chars` | `422` `ErrorResponse` · code ใหม่ (§10 ข้อ 3) |

ไม่มี endpoint หรือ event ใหม่ · ไม่ต้องรัน `pnpm gen:api` (schema ไม่เปลี่ยน)

## 7. AI calls

| Purpose | Tier | Output schema | Prompt file |
|---|---|---|---|
| `tutor_reply` | main (`config/ai.yaml` · `stream: true`) | ข้อความอิสระ (stream) · ไม่มี schema | `prompts/tutor_reply/v1.md` (ใหม่) |

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `test_AI01_stream_sends_purpose_settings_and_rendered_prompt` | unit | AC-1 |
| `test_AI01_stream_rejects_unknown_or_non_stream_purpose` | unit | AC-2 |
| `test_AI03_fake_stream_is_deterministic_and_joins_to_script` | unit | AC-3 |
| `test_TM08_stream_keeps_latex_chunks_verbatim` | unit | AC-4 |
| `test_AI01_stream_skips_empty_chunks` | unit | AC-5 |
| `test_AI01_stream_retries_before_first_chunk` | unit | AC-6 |
| `test_AI01_stream_rate_limit_wait_boundary` (parametrize: = และ +1) | unit | AC-6b |
| `test_AI01_stream_no_retry_after_first_chunk` | unit | AC-7 |
| `test_AI01_stream_timeout_counts_as_provider_error` | unit | AC-8 |
| `test_AI01_stream_emits_one_call_record` (parametrize 3 กรณี) | unit | AC-9 |
| `test_AI02_default_fake_gateway_streams_tutor_reply` | unit | AC-10 |
| `test_AI01_room_code_does_not_import_providers` | unit | AC-10 |
| `test_NFR_P1_first_token_sent_before_stream_ends` | unit (TestClient + fake) | AC-11 |
| `test_AI01_send_message_streams_tokens_then_done` | unit | AC-12 |
| `test_AI01_send_message_degrades_when_provider_fails_first` | unit | AC-13 |
| `test_AI01_send_message_error_after_partial_reply` | unit | AC-14 |
| `test_AI01_send_message_length_boundary` (parametrize −1, =, +1 · ไทย) | unit | AC-15 |
| `test_AI01_send_message_image_keeps_stub` | unit | AC-16 |
| `test_TM08_send_message_sse_keeps_latex` | unit | AC-17 |
| `test_AI01_send_message_stops_provider_on_disconnect` | unit | AC-18 |
| `test_room_api_contract.py` (เดิม) | unit | AC-contract |
| live smoke: `@pytest.mark.live` stream `tutor_reply` บน Vertex 1 ข้อความ | integration (ไม่อยู่ใน CI) | §2 Gemini/Vertex |

## 9. Out of scope

- บันทึกข้อความลง `messages`, `done.message_ids` (api.md v1.3), ตรวจ JWT และ 404 ของ session ที่ไม่มี (§10 ข้อ 1)
- layer 2–9 ของ context (persona, scope, performance, directive, grounding, checker, conversation) · stage machine, planner, buddy scene (เทอม 2 ตาม P4-lite)
- เขียน `ai_calls` ลงตาราง (checklist ข้อแยกของ Junior · feature นี้แค่ส่ง `CallRecord` ให้ listener) · ต้นทุนต่อข้อความ
- flow รูป (`extract_answer`, `ocr_preview`, `ocr/confirm`), answer-leak check, rate limit 20 ข้อความ/นาที, intent router, distress template (§2.9)
- fallback ไป Claude, circuit breaker (เทอม 2 ตาม P4-lite)
- เปิด `AI_PROVIDER=live` บน api-staging (รอ Junior เช็ค JWT · checklist 28 ต.ค.)

## 10. Open questions

1. **(Junior · backend/DB · ใช้ข้อเสนอไปก่อน รอ Junior)** P4-lite ยังไม่ตรวจ JWT และยังไม่บันทึก `messages` ใช่ไหม · เหตุผล: `POST /exam-preps/{id}/sessions` ยังเป็น stub จึงยังไม่มีแถว `tutor_sessions` จริงให้ผูก และ `app/db/` ยังไม่มี · ผลคือ endpoint นี้รับ session id อะไรก็ได้ และ tutor ไม่เห็นข้อความก่อนหน้า · **ข้อเสนอ:** ใช่ ทำใน feature ถัดไปที่เปลี่ยน session เป็นของจริง · ระหว่างนี้ staging ต้องเป็น fake
2. **ตัดสินแล้ว (Jam 2026-10-31): คง stub** · `{image_path}` ควรทำอะไรใน P4-lite · **ข้อเสนอ:** คง stub เดิม (`X-Stub: true`) จนกว่าจะทำ flow รูป · ทางเลือกคือตอบ error ทันที
3. **(Junior · api.md "รอตัดสิน" ข้อ 3 · ใช้ข้อเสนอไปก่อน รอ Junior)** `error.code` ของ (ก) ข้อความยาวเกิน (`422`) และ (ข) AI ล้มกลาง stream · **ข้อเสนอ:** (ก) `message_too_long` (ข) `ai_unavailable` (ตรงกับตัวอย่างใน `chat-streaming.md` AC-13)
4. **ตัดสินแล้ว (Jam 2026-10-31): ใช้ข้อความ tutor ของ stub ตัด buddy** · ข้อความของ fake เมื่อ `AI_PROVIDER=fake` (staging และ dev) · **ข้อเสนอ:** ใช้ข้อความ tutor ของ `app/stubs/tutor_reply.sse` (มีทั้ง inline และ block math) โดยตัด token buddy ออก เพราะ tutor_reply ใน P4-lite ไม่มี buddy · ผลคือ demo บน staging จะไม่เห็น bubble buddy ใน**คำตอบ**อีกแล้ว
5. **ตัดสินแล้ว (Jam 2026-10-31): เอากรณี `{text}` ออก** · `test_room_stubs.py` (ของ Junior) ระบุว่า "Delete this file in P4-lite" และ `test_apimd_room_stubs_send_x_stub_header` ครอบ `POST /sessions/{id}/messages` ด้วย · feature นี้ทำให้ test นั้น fail สำหรับข้อความ text · **ข้อเสนอ:** เอาเฉพาะกรณี `{text}` ออกจาก test นั้น (ตามที่ docstring ของไฟล์บอกไว้ล่วงหน้า) ส่วน endpoint อื่นที่ยังเป็น stub คงไว้ · ต้องให้คนอนุมัติเพราะเป็น test ที่ review แล้ว
6. **ตัดสินแล้ว (Jam 2026-10-31): ยังไม่เพิ่ม** · ควรมี timeout แยกสำหรับ token แรก (เพื่อ NFR-P1) นอกจาก `timeout_s` ของทั้ง stream ไหม · **ข้อเสนอ:** ยังไม่ต้อง ใช้ `timeout_s` ไปก่อน แล้วดูจากผลวัด P4-lite · ถ้าเพิ่มต้องเป็นค่าใน `config/ai.yaml` พร้อมที่มา

## 11. Spec changes needed

- `specs/system/api.md` (ไฟล์กลาง · ต้องบอกกลุ่ม): เพิ่ม error code ตาม §10 ข้อ 3 เมื่อ Junior ตกลง · ไม่แก้ใน PR นี้ถ้ายังไม่ตกลง (implement ตามข้อเสนอ แล้วจดไว้)
- `config/ai.yaml`: ไม่ต้องแก้ (`tutor_reply` มี `stream: true` อยู่แล้ว) · ยกเว้นถ้าตัดสิน §10 ข้อ 6 ให้เพิ่ม key
- `prompts/tutor_reply/v1.md`: ไฟล์ใหม่ (Jam เป็นเจ้าของ `prompts/`) · ยังไม่มี eval ของ tutor behavior (§2.11) จึงใช้ live smoke แทนใน P4-lite
