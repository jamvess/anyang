# Feature: ห้องติวบันทึก session และข้อความลง DB แล้วกลับมาต่อได้

| | |
|---|---|
| Area | tutor (flow 2.2) |
| Requirements | TM-13, SA-06 |
| Owner | Junior |
| Reviewer | Junior · May (หน้าห้องรองรับ session ที่ไม่มี card และโจทย์ · ถ้อยคำใน `config/messages.yaml`) · Jam (follow-up: คำทักจาก AI ด้วย prompt `open_session` v2) |
| Status | approved (Junior 2026-11-11) |
| Related system spec | `api.md` v1.15 "บันทึกลง DB" · `data-model.md` (`tutor_sessions.scope_version_id` null ได้ · `0004`) · `0001_init.sql` `tutor_sessions`, `messages` (+`0002` `attachment_name`), policy `owner_rows` / `tenant_rows` · `api-auth.md` §2.5 (`get_user_db`) · `create-exam-prep.md` (3 กรณีของ token, `db_unavailable`) · `tutor-reply-stream.md` (stream, degrade) · `demo-room.md` §2 E (conversation) · `config/learning.yaml` `session.context_recent_turns` · `config/messages.yaml` (ใหม่ · `room_greeting`) |

## 1. Context

ห้องติวบน staging ตอนนี้เป็น stub: ทุกคนได้ session id เดียวกันจาก fixture และไม่มีอะไรบันทึก ปิดหน้าแล้วประวัติหาย · journey ของ advisor update วันจันทร์ต้อง "ส่งข้อความคุยกับ AI จริง → ปิด → เปิดใหม่แล้วเห็นประวัติ" (TM-13) · feature นี้ให้ 5 endpoint ของห้องติวอ่านและเขียน `tutor_sessions` + `messages` ด้วย JWT ของผู้ใช้ (RLS) เมื่อมี token · ทางของ stub และ demo ในเครื่องยังอยู่เมื่อไม่มี token

## 2. Behavior

**1. เลือกทางตาม token** (เหมือน `create-exam-prep.md` §2.1 · ใช้กับ 5 endpoint: `GET /exam-preps/{id}/sessions/active`, `POST /exam-preps/{id}/sessions`, `GET /sessions/{id}`, `GET /sessions/{id}/messages`, `POST /sessions/{id}/messages` ที่ไม่มี `image_path`)

| | มี token ที่ถูก | token ผิด | ไม่มี token |
|---|---|---|---|
| `AUTH_REQUIRED=true` | **DB จริง** · ไม่มี `X-Stub` | `401 invalid_token` | `401 missing_token` · ไม่มี stub |
| `AUTH_REQUIRED=false` | **DB จริง** · ไม่มี `X-Stub` | `401 invalid_token` | ทางเดิมทุกอย่าง (stub หรือ demo ในเครื่อง `APP_ENV=local`) · ไม่แตะ DB |

มี token บนเครื่อง dev (`APP_ENV=local`) ก็ใช้ DB ไม่ใช้ demo (§10 ข้อ 2) · ข้อความที่มี `image_path` ยังเป็นทางเดิมไม่ว่ามี token หรือไม่ (รอ Storage)

**2. ก่อนเริ่ม SSE** (ทุก endpoint ที่ใช้ DB): prep หรือ session ที่ไม่มี หรือ RLS มองไม่เห็น (tenant อื่น หรือ user อื่น) → `404 not_found` · DB ติดต่อไม่ได้ → `503 db_unavailable` (message คงที่เดียวกับ `create-exam-prep.md` §2.5 · log พร้อม `request_id`) · ไม่มีกรณีไหนเป็น `500`

**3. `GET /exam-preps/{id}/sessions/active`:** หา prep (ไม่เจอ → `404 not_found`) แล้วหา `tutor_sessions` ของ prep นี้ที่ `ended_at is null` เอาอันที่ `started_at` ล่าสุด · ไม่มี → `404 no_active_session` · เจอ → `200 {session_id}`

**4. `POST /exam-preps/{id}/sessions`:**

1. หา prep (ไม่เจอ → `404 not_found` ก่อน SSE)
2. insert `tutor_sessions`: `tenant_id`, `user_id` จาก token · `exam_prep_id` · `scope_version_id` = `exam_preps.active_scope_version_id` (null ได้ · data-model.md) · คอลัมน์อื่นใช้ default · session เปิดเก่าไม่ถูกปิด
3. SSE: `session {session_id}` (id ของแถวใหม่) → `token` 1 ตัว (คำทักทั้งก้อน §2.8) → `done {message_ids: [id ของคำทัก]}` · ไม่เรียก AI
4. **ไม่ส่ง `progress_card`** เมื่อ `scope_version_id` เป็น null (api.md v1.15) · prep ที่มี scope แล้ว: ยังไม่ส่งเหมือนกันใน feature นี้ เพราะ card จาก mastery จริงยังไม่มี (§9) · **ไม่ส่ง `problem`**
5. หลังส่งคำทัก insert ข้อความ `role: "tutor"`, `content` = คำทักทั้งก้อน, `input_mode: null` แล้วส่ง id ใน `done` · insert ไม่สำเร็จ → `done {message_ids: []}` + log (session ยังใช้ได้)

**5. `GET /sessions/{id}`:** `Room`

| Field | ค่า |
|---|---|
| `session_id` | id ของ session |
| `prep_name` | `exam_preps.title` |
| `days_left` | `exam_date − วันนี้ (Asia/Bangkok)` เหมือน `create-exam-prep.md` §2.3 |
| `user_name` | `profiles.nickname` ตัดช่องว่างหัวท้ายแล้วไม่ว่าง · ไม่งั้น "คุณ" |
| `tutor_name` | `tutor_profiles.params.name` ของแถวที่ `version` สูงสุด (เท่ากันเอา `created_at` ล่าสุด) · ไม่มีแถว หรือ `name` ไม่ใช่ string ที่ไม่ว่าง → ชื่อ preset tutor ตัวแรกของ `GET /personas/presets` |
| `buddy_name` | `buddy_profiles` แถวล่าสุดแบบเดียวกัน ที่ `enabled = true` และมี `params.name` → ชื่อนั้น · ไม่งั้น `null` |
| `limits` | จาก `config/ai.yaml` `guards` เหมือนเดิม |
| `messages` | เหมือน §2.6 |

session ที่จบแล้ว (`ended_at` ไม่เป็น null) ยังได้ `200`

**6. `GET /sessions/{id}/messages`:** แถว `messages` ของ session เรียงตาม `created_at` เก่าไปใหม่ · แต่ละแถวเป็น `Message` (`id` เป็น uuid ของแถว · `card` เป็น jsonb ตามที่เก็บ · ไม่ส่ง `extracted_text`, `intent`) · ไม่แบ่งหน้า · ไม่มี → `[]`

**7. `POST /sessions/{id}/messages` (text):**

1. ตรวจ body และ `message_too_long` ตามเดิม · rate limit ตามเดิม (นับก่อนทุกอย่าง)
2. หา session (ไม่เจอ → `404 not_found`) · `ended_at` ไม่เป็น null → `409 session_already_ended` · ทั้งคู่ก่อน SSE
3. อ่าน conversation ก่อนหน้า: ข้อความ `user` และ `tutor` ล่าสุดของ session เป็น turn (turn = ข้อความ user 1 ข้อความ + ข้อความ tutor ที่ตามมา) เอา `config/learning.yaml` → `session.context_recent_turns` turn ล่าสุด เข้า `conversation_text` แบบเดียวกับ demo-room §2 E (escape `<`)
4. insert ข้อความ `user` (`content` = text, `input_mode: "text"`) **ก่อน**เรียก AI · insert ไม่สำเร็จ → `503 db_unavailable` ก่อน SSE (ไม่เรียก AI)
5. stream `tutor_reply` ด้วย `problem = "none"` (ยังไม่มีโจทย์ใน DB) และ conversation จากข้อ 3
6. tutor จบปกติ → insert ข้อความ `tutor` ทั้งก้อน → `done {message_ids: [id]}` · degrade ("ระบบช้า ลองส่งอีกทีนะ" เพราะล้มก่อน token แรก) → insert ข้อความ degrade เป็น `tutor` เหมือนกัน → `done {message_ids: [id]}` · ล้มหลังมี token แล้ว (event `error`) → ไม่ insert ข้อความ tutor · insert ข้อความ tutor ไม่สำเร็จ → `done {message_ids: []}` + log พร้อม `request_id`
7. `ai_calls` ได้ `session_id` ของ session จริง (เดิมไม่มีเพราะ session เป็น stub · `api-auth.md` §2.5)

**8. คำทักเปิดห้อง** (Junior 2026-11-11 · §10 ข้อ 1): code เติม template จาก `config/messages.yaml` → `room_greeting` (ที่เดียวที่ May/Jam แก้ถ้อยคำได้โดยไม่แก้ code · โหลดและตรวจตอน start เหมือน config อื่น: key ขาดหรือ placeholder ที่ไม่รู้จัก → แอป start ไม่ได้)

| ส่วน | key | ใช้เมื่อ | placeholder ที่ใช้ได้ |
|---|---|---|---|
| คำทัก | `hello_named` | `user_name` ไม่ใช่ fallback "คุณ" | `{user_name}` |
| | `hello_anonymous` | ไม่มี nickname | ไม่มี |
| วันสอบ | `days_left_many` | `days_left ≥ 1` | `{days_left}`, `{prep_name}` |
| | `exam_today` | `days_left = 0` | `{prep_name}` |
| | `exam_passed` | `days_left < 0` | `{prep_name}` |
| ชวนเริ่ม | `invite` | เสมอ | ไม่มี |

คำทัก = `hello` + ช่องว่าง + ส่วนวันสอบ + ช่องว่าง + `invite` · ค่าที่เติม (`user_name`, `prep_name`) มาจากผู้ใช้ แต่ไม่เข้า LLM และ template เป็นของเรา (ไม่ใช้ค่าของผู้ใช้เป็น format string) · ค่าเริ่มต้น (May ปรับได้): `hello_named` "สวัสดี {user_name}!" · `hello_anonymous` "สวัสดี!" · `days_left_many` "เหลืออีก {days_left} วันก่อนสอบ{prep_name}" · `exam_today` "วันนี้สอบ{prep_name}แล้ว ทบทวนจุดสำคัญกันอีกรอบนะ" · `exam_passed` "สอบ{prep_name}ผ่านไปแล้ว ทบทวนต่อได้เสมอ" · `invite` "พิมพ์คำถามหรือโจทย์ที่อยากให้ช่วยมาได้เลยนะ"

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | header `Authorization: Bearer <jwt>` · path `{id}` uuid · `POST /sessions/{id}/messages` body `{text}` | `{"text": "อธิบายผลต่างกำลังสองหน่อย"}` |
| Output `active` | `200 {session_id}` | `{"session_id": "…uuid…"}` |
| Output `POST …/sessions` | SSE `session` → `token`… → `done` | `event: session` `data: {"session_id": "…"}` … `event: done` `data: {"message_ids": ["…"]}` |
| Output `GET /sessions/{id}` | `200 Room` | `{"session_id": "…", "prep_name": "แคลคูลัส 1 กลางภาค", "days_left": 27, "user_name": "คุณ", "tutor_name": "พี่กร", "buddy_name": null, "limits": {…}, "messages": [ … ]}` |
| Output messages | `200 Message[]` | `[{"id": "…", "role": "user", "content": "…", "card": null, "input_mode": "text", "attachment_path": null, "attachment_name": null, "created_at": "…"}]` |
| Error | `ErrorResponse` | `401 missing_token` / `invalid_token` · `404 not_found` · `404 no_active_session` · `409 session_already_ended` · `422 validation_error` / `message_too_long` · `429 rate_limited` · `503 db_unavailable` |

## 4. Acceptance criteria

ทุกข้อใช้ fake provider · "ผู้ใช้ A" มี token ที่ถูก · ค่า `context_recent_turns` อ่านจาก config ที่ test โหลด

**ทางของ token**

- **AC-auth-required (SA-06)** `AUTH_REQUIRED=true` ไม่มี token → ทั้ง 5 endpoint `401 missing_token` · ไม่มี `X-Stub` · ไม่เรียก repository และ AI
- **AC-auth-stub (SA-06)** `AUTH_REQUIRED=false` ไม่มี token → พฤติกรรมเดิม (test ที่ review แล้วของห้องติวผ่านโดยไม่แก้) · ไม่เรียก repository
- **AC-auth-real (TM-13)** มี token (`AUTH_REQUIRED` true หรือ false, `APP_ENV` local หรือ staging) → ใช้ repository · ไม่มี `X-Stub`
- **AC-auth-bad (SA-06)** token ผิด → `401 invalid_token` ทั้งสองค่าของ `AUTH_REQUIRED`

**เปิด session**

- **AC-1 (TM-13)** Given A มี prep When `POST /exam-preps/{id}/sessions` Then SSE เรียงเป็น `session` → `token` อย่างน้อย 1 → `done` · ไม่มี `progress_card` และ `problem` · `session.session_id` เป็นแถวใหม่ใน `tutor_sessions` ที่ `tenant_id`, `user_id` ตรง token, `exam_prep_id` ตรง, `scope_version_id` null, `ended_at` null · `done.message_ids` มี 1 id ซึ่งเป็นข้อความ `tutor` ที่ `content` = token ทั้งหมดต่อกัน
- **AC-2 (TM-13)** Given prep มี `active_scope_version_id` When เปิด session Then แถวใหม่มี `scope_version_id` ตรงกัน · ยังไม่มี `progress_card`
- **AC-3 (SA-06)** Given prep ของ B (tenant อื่น) หรือ id ที่ไม่มี When A เปิด session Then `404 not_found` ก่อน SSE · ไม่มีแถวใหม่
- **AC-4 (TM-13)** คำทักมาจาก `config/messages.yaml` (test ใช้ config ของ test ที่มีข้อความต่างจากของจริง แล้วยืนยันว่าได้ข้อความนั้น) · ไม่มี AI call (fake provider ไม่ถูกเรียก)
- **AC-boundary-greeting (TM-13)** `days_left` = 2 → `days_left_many` · = 1 → `days_left_many` · = 0 → `exam_today` · = −1 → `exam_passed` · มี nickname → `hello_named` เติมชื่อ · ไม่มี → `hello_anonymous` · ชื่อหรือ title ที่มี `{` `}` เช่น "{x}" ถูกใส่ตามตัวอักษร ไม่ถูกตีความ
- **AC-config (TM-13)** `config/messages.yaml` ขาด key หรือมี placeholder ที่ไม่อยู่ในตาราง §2.8 → โหลด settings ไม่ผ่าน
- **AC-5 (TM-13)** Given insert คำทักล้ม When เปิด session Then `done {message_ids: []}` · session ยังอยู่

**หา session ที่เปิดอยู่**

- **AC-6 (TM-13)** Given A มี 2 session เปิดของ prep เดียว When `GET …/sessions/active` Then ได้อันที่ `started_at` ล่าสุด
- **AC-7 (TM-13)** Given session ทั้งหมดของ prep `ended_at` ไม่เป็น null หรือไม่มีเลย Then `404 no_active_session`
- **AC-8 (SA-06)** prep ของ tenant อื่น หรือ id ที่ไม่มี → `404 not_found` (ไม่ใช่ `no_active_session`)
- **AC-9 (TM-13)** session ของ prep อื่นของ A ไม่ถูกนับ

**ห้องและประวัติ**

- **AC-10 (TM-13)** Given A เปิด session, ส่ง 2 ข้อความ When `GET /sessions/{id}` ด้วย token ใหม่ของ A (login ใหม่) Then `messages` มีคำทัก + user + tutor + user + tutor เรียงตามเวลา · `id` เป็น uuid · `input_mode` ของ user เป็น `"text"` ของ tutor เป็น null · `GET /sessions/{id}/messages` ได้รายการเดียวกัน
- **AC-11 (TM-13)** หัวห้อง: `prep_name` = title · `days_left` ตามวันกรุงเทพ · ไม่มี profile → `user_name = "คุณ"`, `tutor_name` = ชื่อ preset tutor ตัวแรก, `buddy_name = null` · `nickname = "  "` → "คุณ" · มี tutor profile 2 version → ชื่อของ version สูงสุด · buddy `enabled = false` → null · buddy `enabled = true` → ชื่อ
- **AC-12 (TM-13)** session ที่จบแล้ว → `GET /sessions/{id}` ยัง `200` พร้อมประวัติ
- **AC-13 (SA-06)** session ของ tenant อื่น หรือ id ที่ไม่มี → `GET /sessions/{id}` และ `GET …/messages` `404 not_found`
- **AC-14 (TM-13)** session ไม่มีข้อความ → `messages: []`

**ส่งข้อความ**

- **AC-15 (TM-13)** Given session เปิด When ส่ง `{text}` Then ข้อความ `user` ถูก insert ก่อนเรียก AI (fake provider เห็นแถวนั้นอยู่แล้วตอนถูกเรียก) · หลัง stream มีข้อความ `tutor` = token ทั้งหมดต่อกัน · `done.message_ids` = [id ของ tutor]
- **AC-16 (TM-13)** degrade (ล้มก่อน token แรก) → ข้อความ `tutor` = ข้อความ degrade ถูกบันทึก · id อยู่ใน `done`
- **AC-17 (TM-13)** ล้มหลังมี token (event `error`) → มีแค่ข้อความ `user` · ไม่มีข้อความ `tutor`
- **AC-18 (TM-13)** insert tutor ล้ม → `done {message_ids: []}` · log มี `request_id`
- **AC-19 (TM-13)** insert user ล้ม → `503 db_unavailable` ก่อน SSE · AI ไม่ถูกเรียก
- **AC-20 (TM-13)** session จบแล้ว → `409 session_already_ended` · ไม่มีแถวใหม่ · AI ไม่ถูกเรียก
- **AC-21 (SA-06)** session ของ tenant อื่น → `404 not_found` · ไม่มีแถวใหม่ใน tenant ไหนเลย
- **AC-22 (TM-13)** `tutor_reply` ได้ `problem = "none"` และ `conversation` จาก DB
- **AC-boundary-turns (TM-13)** ให้ N = `session.context_recent_turns` · session มี N − 1, N, N + 1 turn ก่อนข้อความนี้ → conversation มีครบ N − 1 / N turn / N turn ล่าสุด (turn เก่าสุดหลุด) · ข้อความที่กำลังส่งไม่อยู่ใน conversation · `<` ใน content ถูก escape
- **AC-23 (TM-13)** `ai_calls` ของ call นี้มี `session_id` ของ session จริง

**DB ล่ม**

- **AC-db (TM-13)** repository โยน `DbUnavailableError` ตอนหา prep หรือ session → `503 db_unavailable` ทุก endpoint · ก่อน SSE · ไม่มีข้อความจาก exception

## 5. Data changes

| Table | Column / index / policy | เพิ่ม / แก้ |
|---|---|---|
| `tutor_sessions` | `scope_version_id` drop not null (`0004_tutor_sessions_scope_nullable.sql`) | แก้ |

policy เดิมพอ: `tutor_sessions` `owner_rows` (tenant + user) · `messages` `tenant_rows` (tenant) + FK ไป session ของ user เอง · ไม่มีตารางใหม่ · Junior `db push` ขึ้น anyang-dev และ anyang-staging

## 6. API / SSE changes

| Endpoint / event | Request | Response |
|---|---|---|
| `GET /exam-preps/{id}/sessions/active` | จาก stub เป็นของจริง | `200 {session_id}` · `404 not_found` / `no_active_session` · `503` |
| `POST /exam-preps/{id}/sessions` | จาก stub เป็นของจริง | SSE `session` → `token` → `done` (ไม่มี `progress_card`, `problem`) · `404` · `503` |
| `GET /sessions/{id}` | จาก stub เป็นของจริง | `Room` · `404` · `503` |
| `GET /sessions/{id}/messages` | จาก stub เป็นของจริง | `Message[]` · `404` · `503` |
| `POST /sessions/{id}/messages` (text) | เพิ่มการบันทึก | `404`, `409 session_already_ended`, `503` ก่อน SSE · `done.message_ids` id จริง |

ทั้งหมดตาม api.md v1.15 · OpenAPI เพิ่ม `404`/`409`/`503` ที่ยังไม่มี · `pnpm gen:api`

## 7. AI calls

| Purpose | Tier | Output schema | Prompt file |
|---|---|---|---|
| `tutor_reply` | main (เดิม) | free text, stream | `prompts/tutor_reply/v2.md` (ไม่แก้) |
| คำทักเปิดห้อง | ไม่มี AI call · template จาก `config/messages.yaml` (§2.8) · follow-up ของ Jam: prompt `open_session` v2 | | |

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/unit/test_room_sessions_api.py` · router กับ fake repository + fake gateway · `get_auth` override · นาฬิกาตรึง | unit | AC-auth-required, AC-auth-stub, AC-auth-real, AC-1, AC-3–9, AC-11–22, AC-db |
| `tests/unit/test_room_conversation.py` · ฟังก์ชันตัด turn จากรายการข้อความ (pure) | unit | AC-boundary-turns |
| `tests/unit/test_room_greeting.py` · ฟังก์ชันประกอบคำทัก (pure) + การโหลด `config/messages.yaml` | unit | AC-4, AC-boundary-greeting, AC-config |
| `tests/integration/test_room_sessions_db.py` · anyang-dev · user จริง 2 คน | integration | AC-1, AC-2, AC-6, AC-10, AC-11 (profile จริง), AC-13, AC-21, AC-23, AC-auth-bad |

## 9. Out of scope

- `progress_card` จาก mastery จริง (TM-15) และ `problem` จาก planner
- `POST /sessions/{id}/end` (PM-05 · ยังเป็น stub) · ปิด session อัตโนมัติ (`idle`)
- รูป, `ocr_preview`, `verdict`, `/ocr/confirm`, ข้อความ buddy (รอ Storage)
- แบ่งหน้าประวัติ · unique index กันสองแท็บเปิด session ซ้อน
- หน้าเว็บ (May)

## 10. Open questions

1. ~~**คำทักเปิดห้องเมื่อไม่มี card และโจทย์**~~ **ตัดสินแล้ว (ก)** Junior 2026-11-11 → §2.8 · template อยู่ใน `config/messages.yaml` ไม่อยู่ใน router · คำทักจาก AI (prompt `open_session` v2) เป็น follow-up ของ Jam · ข้อเดิม: prompt `open_session` v1 บอก AI ว่า "progress card อยู่บนจอแล้ว" และ "ชวนลองทำโจทย์ด้านล่าง" ซึ่งไม่จริงใน session นี้ · ถ้าใช้ต่อ AI จะพูดถึงสิ่งที่ไม่มีบนจอ · ทางเลือก:
   - **(ก) ข้อเสนอ:** ไม่เรียก AI · คำทักเป็น template ที่ code เติม (code decides, LLM speaks ไม่จำเป็นตรงนี้): "สวัสดี{user_name ถ้าไม่ใช่ "คุณ" เติม " " + ชื่อ}! เหลืออีก {days_left} วันก่อนสอบ{prep_name} พิมพ์คำถามหรือโจทย์ที่อยากให้ช่วยมาได้เลยนะ" · ข้อความผู้ใช้เห็นต้องให้ May ดูถ้อยคำ · ห้องเปิดเร็ว ไม่มี AI call
   - (ข) prompt `open_session` v2 ที่รู้ว่าไม่มี card/โจทย์ · เป็นงานของ Jam (prompt + eval) ไม่ทันวันจันทร์
2. ~~**มี token บนเครื่อง dev**~~ **ตัดสินแล้ว** (Junior 2026-11-11): ใช้ DB · ข้อเดิม:ใช้ DB เหมือน staging (demo room ในเครื่องยังใช้ได้เมื่อไม่ส่ง token) · ผลคือ demo room ที่มีโจทย์ 5 ข้อหายไปเมื่อ May รันเว็บพร้อม login
3. ~~**`messages` RLS เป็น `tenant_rows`**~~ **ตัดสินแล้ว** (Junior 2026-11-11): พอสำหรับตอนนี้ · จดใน data-model.md · ข้อเดิม: · tenant ส่วนตัวมี user เดียวจึงพอ · tenant แบบกลุ่ม (ทีหลัง) ต้องกรองผ่าน session ของ user เอง: feature นี้อ่านข้อความผ่าน session ที่ RLS ของ `tutor_sessions` เห็นแล้วเท่านั้น

## 11. Spec changes needed

- `specs/system/api.md` v1.15 (commit แล้ว)
- `specs/system/data-model.md` (commit แล้ว)
- api.md v1.15: คำทักเป็น template จาก `config/messages.yaml` (แก้ใน PR นี้)
- `config/messages.yaml` ไฟล์ใหม่ (ไฟล์กลาง `config/*.yaml` · Junior ok · บอกกลุ่ม)
- data-model.md: RLS ของ `messages` กรองแค่ tenant (แก้ใน PR นี้)
