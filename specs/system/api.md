# API (v1.6)

Backend: FastAPI ที่ Cloud Run · เอกสาร OpenAPI สร้างอัตโนมัติที่ `/docs` · frontend generate types จาก `/openapi.json`

## Conventions

- **Auth:** ส่ง Supabase access token ใน `Authorization: Bearer <jwt>` ทุก request backend ส่ง token นี้ต่อให้ Supabase เพื่อให้ RLS ทำงาน · ไม่มี token หรือ token ผิด/หมดอายุ/ไม่มี `tenant_id` → `401` + `WWW-Authenticate: Bearer` code `missing_token` / `invalid_token` · ไม่ต้องมี token: `/health`, `/docs`, `/openapi.json` · Supabase Auth ติดต่อไม่ได้ → `503` code `auth_unavailable` (ไม่ใช่ 401 จะได้ไม่ไล่ทุกคนให้ login ใหม่) · ระหว่างที่หน้าเว็บยังไม่ส่ง token env `AUTH_REQUIRED=false` ให้ request ที่ไม่มี token ผ่านได้แต่ไม่มี tenant (token ที่ผิดยังได้ 401 · ยกเว้น API ที่ไม่มี `SUPABASE_URL`/`SUPABASE_ANON_KEY` เช่น api-staging ตอนนี้ จะไม่ตรวจ token เลย) · `specs/features/platform/api-auth.md` (v1.5)
- **Error:** `{"error": {"code": "scope_not_confirmed", "message": "..."}}` พร้อม HTTP status ที่ตรงความหมาย
- **Long-running jobs:** ตอบ `202 Accepted` แล้วให้ client poll endpoint ความคืบหน้า
- **Streaming:** SSE ผ่าน `POST` (client ใช้ `fetch` + `ReadableStream`) ทุก stream จบด้วย event `done`
- **Request ID:** ทุก response มี header `X-Request-Id` ใช้ไล่ log ข้าม AI call และ DB
- **สมการในข้อความ:** `messages.content` และ `token.text` เขียนสมการเป็น `$…$` (inline) และ `$$…$$` (block) · เครื่องหมาย $ ที่ไม่ใช่สมการเขียนเป็น `\$` · `$` ที่ไม่มีคู่แสดงเป็นตัวอักษร (`chat-streaming.md` AC-11b) · prompt ที่เขียนข้อความลงแชท (`tutor_reply` ฯลฯ) ต้องใช้รูปแบบนี้ · `problem.text_latex` เป็น LaTeX ล้วนไม่มีตัวคั่น ไม่อยู่ในข้อนี้ (v1.3 · May ตัดสิน 2026-10-21)

## Endpoints

### Persona (flow 2.7)

| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/personas/presets` | preset ของ tutor และ buddy |
| POST | `/personas/extract` | free text → params + รายการที่ทำไม่ได้ + ประโยคตัวอย่าง |
| PUT | `/me/tutor-profile` · `/me/buddy-profile` | บันทึก persona |
| GET / PUT | `/me/profile` | ชื่อเล่น ระดับการศึกษา ภาษา |

### Exam prep และ scope (flow 2.3)

| Method | Path | ทำอะไร |
|---|---|---|
| POST | `/exam-preps` | สร้างการเตรียมสอบ (ชื่อ วันสอบ นาทีต่อวัน) |
| GET | `/exam-preps` | รายการ + ความพร้อม % (หน้าหลัก) |
| POST | `/exam-preps/{id}/materials` | ได้ `material_id` + signed upload URL |
| PUT | `{signed_url}` | browser ส่งไฟล์เข้า Storage โดยตรง |
| POST | `/materials/{id}/uploaded` | body `{user_note}` · 202 เริ่ม classify |
| GET | `/exam-preps/{id}/materials` | ประเภทที่ AI เดา + สถานะ |
| POST | `/exam-preps/{id}/materials/confirm` | 202 เริ่ม ingest + สกัดหัวข้อ |
| GET | `/exam-preps/{id}/ingestion` | ความคืบหน้าทีละขั้น |
| GET | `/exam-preps/{id}/scope` | หัวข้อ draft + ดาว + เหตุผล |
| GET | `/topics/{id}/sources` | ข้อความต้นฉบับ + เลขหน้า |
| POST | `/exam-preps/{id}/scope/chat` | **SSE:** `token`, `scope_patch`, `done` |
| GET | `/exam-preps/{id}/scope/changes` | change log (S14) |
| POST | `/exam-preps/{id}/scope/confirm` | lock เป็น scope version |

**หน้าตรวจขอบเขต (v1.6 · ข้อเสนอ รอ Junior ตัดสิน):** รูปร่างตามข้อเสนอของ May ใน `specs/features/scope/scope-review.md` §3 (OQ 5–8) · ตัวอย่าง: `apps/web/tests/fixtures/scope/scope-s12.json`, `sources-t3.json` (id ในไฟล์ของเว็บเป็น `t3` ฯลฯ ของจริงเป็น uuid) · ทุก field ต้องมี และไม่มี field อื่น · prep หรือหัวข้อที่ไม่มี หรือเป็นของ tenant อื่น (RLS มองไม่เห็น) → `404` code `not_found`

**`Scope`** (response ของ `GET /exam-preps/{id}/scope`)

| Field | Type | ที่มา |
|---|---|---|
| `prep_name` | string | `exam_preps.title` |
| `days_left` | integer | เหมือน `Room.days_left` |
| `status` | `"draft"` \| `"confirmed"` | `"confirmed"` เมื่อ `exam_preps.active_scope_version_id` ไม่เป็น null **และ**ไม่มีแถว `scope_changes` ของ prep นี้ที่ `created_at` หลัง `confirmed_at` ของ version นั้น · ไม่งั้น `"draft"` (ยืนยันแล้วแก้ต่อ → กลับเป็น draft และยืนยันเป็น version ใหม่ได้) |
| `topics` | `ScopeTopic[]` | `topics` ของ prep นี้ เรียงตาม `order_index` · **รวมหัวข้อที่ `status = 'excluded'`** (หน้าเว็บแสดงท้ายรายการ · scope-review OQ 3) |
| `unmapped_questions` | `PastQuestion[]` | `past_exam_questions` ของไฟล์ใน prep นี้ที่ `topic_id is null` |

ยังสกัดหัวข้อหรือคำนวณดาวไม่เสร็จ (ขั้น 5d ของ ai-orchestration §2.3.4) → `409` code `scope_not_ready` (409 ตัวเดียวของ endpoint นี้ · `GET /topics/{id}/sources` ไม่มี 409) · หน้าเว็บอยู่ที่หน้าความคืบหน้า (S11) จนกว่า `GET /exam-preps/{id}/ingestion` จะบอกว่าเสร็จ

**`ScopeTopic`**

| Field | Type | ที่มา |
|---|---|---|
| `id` | string (uuid) | `topics.id` |
| `order` | integer ≥ 1 | `topics.order_index` (นับจาก 1) · หน้าเว็บแสดงเป็นเลขหน้าชื่อ |
| `name` | string | `topics.name` |
| `stars` | integer 0–3 · **ไม่เป็น null** (ถ้ายังมีหัวข้อที่ดาวเป็น null endpoint ตอบ `409 scope_not_ready` ไม่ตัดหัวข้อนั้นทิ้ง) | `topics.importance` · หัวข้อที่ `status = 'excluded'` เป็น `0` เสมอ · 0 ดาว = ตัดออก (ai-orchestration §2.3.5) |
| `reason` | string | `topics.importance_reason` (template ฝั่ง backend · ai-orchestration §2.3.5) |
| `source_label` | string | ข้อความพร้อมแสดงที่ backend สร้างจากช่วงหน้าใน `topic_sources` + `materials.file_name` (หน้าเว็บไม่ตัดหรือรวมเอง) |
| `origin` | `"doc"` \| `"user"` | `topics.origin` |

**`PastQuestion`:** `{id: string (uuid), label: string, text: string, map_note: string | null}`
- `label` ข้อความพร้อมแสดงจากชื่อไฟล์ + `past_exam_questions.q_no`
- `text` คือ `past_exam_questions.text` เขียนสมการเป็น `$…$` ตาม Conventions "สมการในข้อความ" (prompt `split_past_exam` รับและคืนสมการแบบนี้อยู่แล้ว)
- `map_note` คือ `past_exam_questions.map_note` (เหตุผลของ A7 ทุกข้อ ไม่ใช่เฉพาะข้อที่ map ไม่ได้ · data-model.md P3a ข้อ 3 · migration `0003` ใน PR #67)

**`TopicSources`** (response ของ `GET /topics/{id}/sources`)

| Field | Type | ที่มา |
|---|---|---|
| `excerpts` | `{material_name: string, page: integer ≥ 1, text: string}[]` | 1 รายการต่อ 1 หน้าในช่วงของ `topic_sources` · `materials.file_name`, `material_pages.page_no`, `material_pages.text` · เรียงตามไฟล์แล้วตามหน้า · หัวข้อ `origin = 'user'` ได้ `[]` |
| `questions` | `PastQuestion[]` | `past_exam_questions` ที่ `topic_id` = หัวข้อนี้ · เรียงตามไฟล์ (`materials.created_at`) แล้วตามลำดับในข้อสอบ · ไม่มีได้ `[]` |

**`ScopeConfirmed`** (response ของ `POST /exam-preps/{id}/scope/confirm` · ไม่มี body)
- ผลลัพธ์คือ `{scope_version_id: string (uuid), version: integer ≥ 1}`
- สิ่งที่ backend ทำ: สร้างแถว `scope_versions` (`status = 'confirmed'`, `snapshot` ของหัวข้อ) · ตั้ง `exam_preps.active_scope_version_id` · เปลี่ยนหัวข้อ `draft` เป็น `confirmed` · ai-orchestration §2.3.2 ขั้น 7
- หน้าเว็บใช้แค่ว่าได้ 2xx (`scope-review.md` AC-15) แล้วไปห้องติว
- error:
  - `409 scope_not_ready` · ยังสกัดหัวข้อไม่เสร็จ
  - `409 scope_already_confirmed` · `Scope.status` เป็น `"confirmed"` อยู่แล้ว
  - `409 scope_empty` · ไม่มีหัวข้อที่ไม่ได้ถูกตัดออก

**รอตัดสิน (v1.6 · Junior)** · ข้อเสนอเขียนโดย Jam ช่วง solo 2026-11-01 (PR #100) · stub ทำตามข้อเสนอนี้ไปก่อน ถ้าเปลี่ยนให้แก้ api.md + stub + test ใน PR ใหม่

1. **รูปร่างของ `Scope` และ `status`** (scope-review OQ 5): ใช้ข้อเสนอของ May ตามที่เขียนไว้ · `status` ดูจาก `active_scope_version_id` เพราะ scope ที่ยืนยันแล้วคือ version ที่ prep ชี้อยู่ และไม่มีการแก้หลังยืนยัน · ส่งหัวข้อที่ตัดออกเป็น `stars: 0` เพราะ OQ 3 ต้องแสดงหัวข้อที่ถูกตัด · backend ต้องเปลี่ยน `status = 'excluded'` กับ `importance = 0` ไปด้วยกันเสมอ เพราะ 0 ดาว = ตัดออก (§2.3.5) · หัวข้อที่เพิ่มด้วย `add_topic` ต้องได้ดาวตอนเพิ่ม (ยังไม่ได้เขียนใน §2.3.6) ไม่งั้น `GET /scope` จะตอบ `scope_not_ready`
2. **กฎของ `source_label` และ `label`** (OQ 6): ข้อเสนอคือ `{ชื่อไฟล์ไม่มีนามสกุล} น.{from}–{to}` (หน้าเดียวใช้ `น.{n}`) หลายช่วงคั่นด้วย `, ` · `label` = `{ชื่อไฟล์ไม่มีนามสกุล} ข้อ {q_no}` · ชื่อสั้นอย่าง "ch3" ใน fixture ของ May ต้องมีที่เก็บชื่อย่อ (ยังไม่มีใน schema) · หัวข้อ `origin = 'user'` ไม่มีช่วงหน้า ข้อเสนอคือส่ง `""` และหน้าเว็บไม่แสดงส่วนที่มา (ต้องถาม May ด้วย)
3. **ข้อความต้นฉบับ** (OQ 6): `excerpts.text` เป็นข้อความทั้งหน้าจาก `material_pages` · ถ้ายาวเกินไปค่อยตัดเฉพาะส่วนที่เกี่ยวข้องภายหลัง
4. **`text` ของข้อสอบใช้ `$…$`** (OQ 7): Jam ตกลง (เป็นเจ้าของ prompt) · `split_past_exam/v1` รับสมการเป็น LaTeX ใน `$` อยู่แล้ว
5. **error code ของ scope:** `scope_not_ready` (`GET /scope` และ confirm) · `scope_already_confirmed`, `scope_empty` (confirm อย่างเดียว) · 409 ทั้งหมด

### ห้องติว (flow 2.2, 2.4, 2.5, 2.1)

| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/exam-preps/{id}/sessions/active` | session ที่ยังเปิดอยู่ของการเตรียมสอบนี้ `{session_id}` · 404 `no_active_session` ถ้าไม่มี (TM-13 · ข้อเสนอ ดูด้านล่าง) |
| POST | `/exam-preps/{id}/sessions` | **SSE:** สร้าง session → `session` → `progress_card` → `token` (ข้อความเปิด) → `problem` → `done` |
| GET | `/sessions/{id}` | ข้อมูลห้อง `Room` (หัวห้อง + `limits` + ข้อความ) · ใช้ตอนเปิดห้องและกลับมาต่อ (TM-13) |
| POST | `/sessions/{id}/uploads` | signed URL สำหรับรูปหรือเสียง |
| POST | `/sessions/{id}/transcribe` | เสียง → text (ใส่ช่องพิมพ์ ไม่ส่งเอง) |
| POST | `/sessions/{id}/messages` | **SSE:** body `{text?, image_path?}` อย่างน้อยหนึ่งค่า · ถ้ามีทั้งคู่ `text` เป็นคำบรรยายของรูป (ดูด้านล่าง) |
| POST | `/sessions/{id}/ocr/confirm` | ยืนยันหรือแก้ข้อความที่อ่านจากรูป แล้ว stream ผลต่อ |
| POST | `/sessions/{id}/end` | จบ session → `session_end` |
| GET | `/sessions/{id}/messages` | รายการ `Message[]` อย่างเดียว เรียงตาม `created_at` เก่าไปใหม่ (แบ่งหน้าได้ภายหลัง) |
| GET | `/exam-preps/{id}/progress` | ข้อมูล progress card |
| GET | `/messages/{id}/tts` | URL ไฟล์เสียง (cache ตาม text + voice) |

**`Room`** (response ของ `GET /sessions/{id}`)

| Field | Type | ที่มา |
|---|---|---|
| `session_id` | string (uuid) | `tutor_sessions.id` |
| `prep_name` | string | `exam_preps.title` |
| `days_left` | integer | `exam_preps.exam_date` − วันนี้ (Asia/Bangkok) · คำนวณที่ backend |
| `user_name` | string | `profiles.nickname` |
| `tutor_name` | string | `tutor_profiles.params.name` (version ล่าสุด) |
| `buddy_name` | string \| null | `buddy_profiles.params.name` · `null` เมื่อไม่มี buddy หรือ `enabled = false` |
| `limits` | `{max_message_chars: integer, max_image_mb: integer}` | `config/ai.yaml` → `guards` · 1 MB = 1,048,576 bytes ตรงกับที่ backend ตรวจ |
| `messages` | `Message[]` | เหมือน `GET /sessions/{id}/messages` |

**`Message`:** `{id, role: "user" | "tutor" | "buddy" | "card" | "system", content: string | null, card: object | null, input_mode: "text" | "voice" | "image" | null, attachment_path: string | null, attachment_name: string | null, created_at}` · `attachment_path` เป็น path ใน Storage ที่ตั้งชื่อด้วย uuid ส่วน `attachment_name` คือชื่อไฟล์เดิมที่ผู้ใช้เห็น เช่น "วิธีทำ.jpg" (v1.3 · ต้องเพิ่ม column ใน `messages`) · ไม่ส่ง `extracted_text` และ `intent` (ใช้ภายใน backend) · ตัวอย่างรูปร่าง: `apps/web/tests/fixtures/room/session-s15.json` (ยังไม่มี `session_id` และ `card`)

**ระบบช้า (degrade ของ tutor, ai-orchestration.md §2.10):** ส่งข้อความ template "ระบบช้า ลองส่งอีกทีนะ" เป็น `token` ที่ `speaker: "tutor"` แล้วตาม `done` และบันทึกเป็นข้อความ tutor ปกติใน `messages` · ส่ง `error` เฉพาะเมื่อไม่มีอะไรให้แสดงเลย

**รอตัดสิน (PR #35)**

1. ~~**ส่งรูปพร้อมข้อความกำกับ** (รอ Jam)~~ **ตัดสินแล้ว** (Jam 2026-10-21 · PR #45): ข้อความกำกับเป็นคำบรรยายของรูป · เก็บเป็น `content` ของข้อความ user ที่มี `attachment_path` (ข้อความเดียว `input_mode: "image"`) · tutor เห็นใน conversation (เช่น "ข้อ 2 ครับ") · **ไม่ส่งเข้า `extract_answer` และ checker** ผลตรวจใช้แค่บรรทัดที่ user ยืนยันใน `ocr/confirm` เพื่อให้ผลขึ้นกับคำตอบอย่างเดียว และกันข้อความอย่าง "ข้อนี้ถูกแล้ว" ไปชี้นำ LLM classifier · flow รูปยืนยันทุกครั้ง (AM-02)
2. **หา session ที่เปิดอยู่ (TM-13):** หน้า room รู้แค่ prep id · ข้อเสนอ `GET /exam-preps/{id}/sessions/active` (ด้านบน) ทางเลือกคือให้ `POST /exam-preps/{id}/sessions` คืน session เดิมถ้ายังเปิดอยู่ · เลือก GET เพราะไม่มีผลข้างเคียง ไม่เรียก AI ไม่สร้างข้อความเปิดซ้ำ และ POST ยังมีความหมายเดียวคือเริ่ม session ใหม่ (stream เดียว ไม่ต้องมีสองรูปแบบ response) · "เปิดอยู่" = `ended_at is null` · ถ้ามีหลายอันใช้อันล่าสุด (กันสองแท็บสร้างซ้อนด้วย unique index ได้ภายหลัง ต้องแก้ migration)
3. **รายการ `error.code` ของห้องติว** (Junior · ยังเปิด): ตอนนี้มีแค่รูปแบบ `{code, message}`
4. **หัวข้อ 0 ดาวใน progress card** (รอ May · ถามใน PR #63): ไม่แสดง → `stars` 1–3 · แสดง → `stars` 0–3 · `topics.importance` ใน DB รับ 0–3 และ readiness ไม่นับ 0 ดาวอยู่แล้ว (`learning.yaml` → `readiness.exclude_zero_star`)

ตัดสินแล้วใน v1.3 (May 2026-10-21 · ข้อ 5, 6 รอ Junior ยืนยันใน PR): สมการในข้อความ → Conventions · id ของข้อความที่ stream → `done.message_ids` · ชื่อไฟล์ → `Message.attachment_name`

### บัญชี

| Method | Path | ทำอะไร |
|---|---|---|
| DELETE | `/me` | ลบบัญชีและข้อมูลทั้งหมด (UM-10) |
| DELETE | `/exam-preps/{id}` · `/materials/{id}` | ลบรายการหรือไฟล์ (CM-10) |

## SSE events

| Event | Payload | Flow |
|---|---|---|
| `session` | `{session_id}` · event แรกของ `POST /exam-preps/{id}/sessions` | 2.2 |
| `token` | `{speaker: "tutor" \| "buddy", text}` | 2.2, 2.3 |
| `scope_patch` | `{topic_id, changes}` | 2.3 |
| `progress_card` | `{days_left, passed, total, readiness, topics: [{id, name, stars, level, review_due, origin}]}` · type ของ `topics[]` ดูด้านล่าง | 2.2 |
| `problem` | `{problem_id, text_latex, difficulty, purpose}` (ไม่มีเฉลย) | 2.2 |
| `ocr_preview` | `{lines: [{latex, confidence}]}` | 2.2 |
| `verdict` | `{verdict, first_wrong_line, error_type}` | 2.4 |
| `buddy` | `{text}` (ใช้เมื่อ buddy ตอบนอกจังหวะ 2.1.7) | 2.1 |
| `session_end` | `{summary_lines: [..2]}` | 2.2 |
| `done` | `{}` · ห้องติว: `{message_ids: [...]}` id ของข้อความ tutor และ buddy ที่ stream นี้บันทึกลง `messages` เรียงตามลำดับที่ stream (ใช้แทน id ในเครื่องของ UI เช่น เรียก `GET /messages/{id}/tts`) · v1.3 | ทั้งหมด |
| `error` | `{code, message}` · ใช้เมื่อไม่มีข้อความให้แสดง (degrade ที่มีข้อความ template ส่งเป็น `token`) · รายการ code ยังเปิดอยู่ | ทั้งหมด |

**`progress_card.topics[]`** (v1.4 · #40)

| Field | Type |
|---|---|
| `id` | string |
| `name` | string |
| `stars` | integer 1–3 หรือ 0–3 (รอตัดสินข้อ 4) · **ไม่เป็น null** |
| `level` | `"not_started"` \| `"weak"` \| `"developing"` \| `"passed"` · ตรงกับ `config/learning.yaml` → `levels.show` และ check ของ `topic_progress.level` |
| `review_due` | boolean |
| `origin` | `"doc"` \| `"user"` · ตรงกับ check ของ `topics.origin` |

`stars` มาจาก `topics.importance` ซึ่งใน DB เป็น null ได้ · backend **ไม่ส่งหัวข้อที่ `importance` ยังไม่ได้คำนวณ** เพราะดาวคำนวณในขั้น 5d (ai-orchestration §2.3.4) ก่อนยืนยัน scope และการ์ดแสดงหลังยืนยัน · type ที่ generate จึงเป็น `number` ไม่ใช่ `number | null` · ทุก field ต้องมี และไม่มี field อื่น
