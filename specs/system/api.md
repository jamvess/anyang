# API (v1.14)

Backend: FastAPI ที่ Cloud Run · เอกสาร OpenAPI สร้างอัตโนมัติที่ `/docs` · frontend generate types จาก `/openapi.json`

## Conventions

- **Auth:** ส่ง Supabase access token ใน `Authorization: Bearer <jwt>` ทุก request backend ส่ง token นี้ต่อให้ Supabase เพื่อให้ RLS ทำงาน · ไม่มี token หรือ token ผิด/หมดอายุ/ไม่มี `tenant_id` → `401` + `WWW-Authenticate: Bearer` code `missing_token` / `invalid_token` · ไม่ต้องมี token: `/health`, `/docs`, `/openapi.json` · Supabase Auth ติดต่อไม่ได้ → `503` code `auth_unavailable` (ไม่ใช่ 401 จะได้ไม่ไล่ทุกคนให้ login ใหม่) · ระหว่างที่หน้าเว็บยังไม่ส่ง token env `AUTH_REQUIRED=false` ให้ request ที่ไม่มี token ผ่านได้แต่ไม่มี tenant (token ที่ผิดยังได้ 401 · ยกเว้น API ที่ไม่มี `SUPABASE_URL`/`SUPABASE_ANON_KEY` เช่น api-staging ตอนนี้ จะไม่ตรวจ token เลย) · `specs/features/platform/api-auth.md` (v1.5)
- **Error:** `{"error": {"code": "scope_not_confirmed", "message": "..."}}` พร้อม HTTP status ที่ตรงความหมาย
- **Rate limit (v1.8):** ข้อความที่ผู้ใช้ส่งในห้องติว (`POST /sessions/{id}/messages` และ `POST /sessions/{id}/ocr/confirm` นับรวมกัน) ไม่เกิน `config/ai.yaml` → `guards.rate_limit_messages_per_minute` ใน 60 วินาทีล่าสุด ต่อ user (ไม่มี token นับต่อ IP) · เกินแล้ว `429` code `rate_limited` + header `Retry-After` (วินาที) ก่อนเริ่ม SSE · `specs/features/ai/gateway-guards.md`
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
| GET / PUT | `/me/tutor-profile` · `/me/buddy-profile` | อ่านและบันทึก persona |
| GET / PUT | `/me/profile` | ชื่อเล่น ระดับการศึกษา ภาษา |

**Persona และโปรไฟล์ (v1.12 · ข้อเสนอ รอ Junior ตัดสิน):** UC-01 (S04–S06, S30) · ai-orchestration §2.7 · UM-03, UM-04, UM-05, UM-07, UM-08, UM-09 · ยังไม่มี feature spec ของหน้าจอ · ทุก field ต้องมี และไม่มี field อื่น · ของผู้ใช้จาก token เสมอ ไม่รับ `user_id` · UM-06 เป็น `deferred` จึงไม่มี checklist ที่ mark อัตโนมัติ

**`TutorParams`** และ **`BuddyParams`** (§2.7 · เข้า prompt ผ่าน template เท่านั้น)

| Field | Type | ใช้กับ |
|---|---|---|
| `name`, `self_pronoun`, `call_user` | string · อักษรไทย อังกฤษ ตัวเลข ช่องว่าง · ตัดช่องว่างหัวท้าย · ไม่ว่าง · ยาวไม่เกิน `guards.max_persona_text_chars` | ทั้งคู่ |
| `formality`, `energy`, `strictness` | integer 1–3 (ไม่แปลงชนิด เช่น `"2"` ถูกปฏิเสธ · ใช้กับ `humor` และ boolean ทุกตัวในส่วนนี้) | ทั้งคู่ |
| `humor` | integer 0–2 | ทั้งคู่ |
| `emoji` | boolean | ทั้งคู่ |
| `voice_id` | string รูปแบบ `th-TH-` ตามด้วยตัวอักษรอังกฤษ ตัวเลข หรือ `-` (Google TTS) | ทั้งคู่ |
| `explain_style` | `"step_by_step"` \| `"example_first"` \| `"concise"` | tutor |
| `frequency` | `"low"` \| `"med"` \| `"high"` | buddy |
| `personality` | `"curious"` \| `"playful"` \| `"diligent"` | buddy |

- **`GET /personas/presets`** · `{tutors: PersonaPreset[], buddies: PersonaPreset[]}` · `PersonaPreset` = `{id: string, title: string, sample: string, params}` · `title` เช่น "ใจเย็น" · `sample` คือประโยคตัวอย่าง (UM-03) · tutor 3 แบบ, buddy 2 แบบ · "ไม่เอาเพื่อน" เป็นตัวเลือกของหน้าเว็บ ไม่ใช่ preset
- **`POST /personas/extract`** · body `{kind: "tutor" \| "buddy", description: string (ไม่ว่าง)}` · response `{params, refused: string[], sample: string}` (AI: `persona_extract`, `persona_preview` · UM-05, UM-07)
  - `params` ตาม `kind` · `refused` คือส่วนที่ทำให้ไม่ได้ พร้อมแสดงในกล่อง "ทำให้ไม่ได้: …" (UC-01 E4) · ไม่มีก็ `[]`
  - ไม่เก็บอะไร · กด "บันทึก" แล้วค่อย `PUT` · ปรับต่อก็ส่ง `description` ใหม่ทั้งก้อน
  - error: `422 validation_error` · `422 message_too_long` (เกิน `guards.max_message_chars`) · `429 rate_limited` + `Retry-After` (ตัวนับเดียวกับข้อความในห้องติว · `gateway-guards.md` §2.1) · `503 persona_unavailable` (AI ล่ม · UC-01 E5)
- **`GET /me/tutor-profile`** · `{params: TutorParams, description: string | null, version: integer ≥ 1}` · ยังไม่ตั้ง → `404 not_found` (UM-09)
- **`PUT /me/tutor-profile`** · body `{params: TutorParams, description: string | null}` · response เหมือน `GET` · `description` เก็บใน `description_raw` และ**ไม่เข้า prompt** (§2.7) · แก้แล้ว `version` เพิ่ม · มีผลตั้งแต่ turn ถัดไป · `description` เกิน `guards.max_message_chars` → `422 message_too_long` (ใช้กับ `PUT /me/buddy-profile` ด้วย)
- **`GET /me/buddy-profile`** · `{enabled: boolean, params: BuddyParams | null, description: string | null, version: integer ≥ 1}` · ยังไม่ตั้ง → `404 not_found`
- **`PUT /me/buddy-profile`** · body `{enabled: boolean, params: BuddyParams | null, description: string | null}` · `enabled = true` ต้องมี `params` (ไม่งั้น `422 validation_error`) · ปิดเพื่อนติว (UC-01 A2) ส่ง `enabled = false` · response เหมือน `GET`

**`Profile`** (response ของ `GET` และ `PUT /me/profile` · UM-08)

| Field | Type | ที่มา |
|---|---|---|
| `nickname` | string \| null | `profiles.nickname` · trigger ใส่จากชื่อใน Google |
| `education_level` | `"lower_secondary"` \| `"upper_secondary"` \| `"university"` \| `"other"` \| null | `profiles.education_level` · null จนกว่าจะตั้ง |
| `explain_language` | `"th_en"` \| `"th"` \| `"en"` | `profiles.explain_language` (ไทย + ศัพท์อังกฤษ / ไทยล้วน / English) |
| `auto_read` | boolean | อ่านออกเสียงอัตโนมัติ (TM-09 · ค่าเริ่มต้นปิด) · ยังไม่มีคอลัมน์ (รอตัดสินข้อ 1) |
| `setup_step` | `"crew"` \| `"profile"` \| `"done"` | คำนวณที่ backend ตามลำดับ: `crew` เมื่อยังไม่มี tutor หรือ buddy profile · `profile` เมื่อ `education_level` เป็น null · ไม่งั้น `done` · หน้าเว็บใช้พากลับหน้าที่ค้าง (UC-01 E6) |

- **`PUT /me/profile`** · body ทุก field ยกเว้น `setup_step` · `nickname` ใช้กฎเดียวกับ `name` ของ persona เพราะเข้า prompt ทุก turn (§2.2) · `education_level` ไม่เป็น null · error `422 validation_error`

**รอตัดสิน (v1.12 · Junior)** · ข้อเสนอเขียนโดย Jam ช่วง solo 2026-11-04 (PR #107) · stub ทำตามข้อเสนอนี้ไปก่อน ถ้าเปลี่ยนให้แก้ api.md + stub + test ใน PR ใหม่

1. **`auto_read`:** ยังไม่มีคอลัมน์ · ข้อเสนอคือ migration `profiles.auto_read boolean not null default false` · สวิตช์อยู่ใน S05 แต่บันทึกกับ `PUT /me/profile` ใน S06 ถ้าปิดเว็บก่อนค่าจะหาย
2. **ค่าเริ่มต้นของภาษา** (UC-01 คำถามเปิด 2): DB เป็น `'th'` แต่หน้าจอเลือก "ไทย + ศัพท์อังกฤษ" ไว้ให้ · ข้อเสนอคือ migration เปลี่ยนเป็น `'th_en'` + เพิ่ม check
3. **`buddy_profiles.params` ห้าม null:** ปิดเพื่อนติวแล้วเก็บเป็น `{}` ไหม · API ส่ง `params: null`
4. **แถวของ persona:** `tutor_profiles` และ `buddy_profiles` ไม่มี unique ต่อ user · แก้แล้วเพิ่มแถวเป็น version ใหม่ หรือทับแถวเดิม
5. **`voice_id` และ preset:** รายการเสียงที่อนุญาตและ params ของ preset เก็บที่ไหน (config หรือตาราง) · stub ใช้ค่าชั่วคราวและตรวจแค่ `th-TH-`
6. **การลบ:** `DELETE /me` ต้องลบ `auth.users` ด้วย service role และลบไฟล์ใน Storage · ทำให้จบใน request หรือเป็น job · `DELETE /exam-preps/{id}` ลบได้แม้มี session เปิดอยู่ไหม
7. **error code ใหม่:** `persona_unavailable` · ใช้ซ้ำ: `message_too_long`, `rate_limited`
8. **`nickname` ที่ trigger คัดลอกจาก Google:** `handle_new_user` ใส่ชื่อดิบ (อาจมี `-`, `'` หรือยาวเกินเพดาน) ซึ่งไม่ผ่านกฎของ `PUT` · ข้อเสนอคือ S06 ให้แก้ก่อนส่ง และ backend กรองค่าก่อนเข้า prompt ถ้าผู้ใช้ยังไม่ผ่าน S06

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
| POST | `/materials/{id}/retry` | อ่านไฟล์ที่ล้มใหม่ (UC-02 E5) |
| GET | `/exam-preps/{id}/scope` | หัวข้อ draft + ดาว + เหตุผล |
| GET | `/topics/{id}/sources` | ข้อความต้นฉบับ + เลขหน้า |
| POST | `/exam-preps/{id}/scope/chat` | **SSE:** `token`, `scope_patch`, `done` |
| GET | `/exam-preps/{id}/scope/changes` | change log (S14) |
| POST | `/exam-preps/{id}/scope/confirm` | lock เป็น scope version |

**สร้างการเตรียมสอบและใส่ไฟล์ (v1.10 · `POST`/`GET /exam-preps` ตัดสินแล้ว v1.14 · Junior 2026-11-11 · ส่วน materials ยังเป็นข้อเสนอ รอ Junior ตัดสิน):** UC-02 ขั้น 1–5 (S07–S10) · ai-orchestration §2.3.2 ขั้น 1–3 · ยังไม่มี feature spec ของหน้าจอ · ทุก field ต้องมี และไม่มี field อื่น · prep หรือไฟล์ที่ไม่มีหรือเป็นของ tenant อื่น → `404 not_found`

**`ExamPrep`** (response ของ `POST /exam-preps` และแต่ละแถวของ `GET /exam-preps`)

| Field | Type | ที่มา |
|---|---|---|
| `id` | string (uuid) | `exam_preps.id` |
| `title` | string | `exam_preps.title` |
| `exam_date` | string (date · `YYYY-MM-DD`) | `exam_preps.exam_date` |
| `days_left` | integer | เหมือน `Room.days_left` (CM-02) |
| `daily_minutes` | integer \| null | `exam_preps.daily_minutes` · null = ใช้ค่าจาก `config/learning.yaml` → `planner.default_daily_minutes` (UC-02 A1) |
| `stage` | `"materials"` \| `"processing"` \| `"scope"` \| `"tutoring"` | คำนวณที่ backend ตามลำดับ: `tutoring` เมื่อมี `active_scope_version_id` · ไม่งั้น `scope` เมื่อ `Ingestion.scope_ready` (v1.11) · ไม่งั้น `processing` เมื่อมีไฟล์ที่ `kind_confirmed = true` · ไม่งั้น `materials` (รวม prep ที่ยังไม่มีไฟล์) · แก้ใน v1.11 เพราะกฎเดิมให้ `scope` ทั้งที่ยังสกัดหัวข้อไม่เสร็จ · หน้าเว็บใช้เลือกว่าการ์ดพาไปหน้าไหน |
| `readiness` | number 0–1 \| null | PM-03 · null เมื่อยังคำนวณไม่ได้: ก่อน `stage = "tutoring"` หรือ backend ยังไม่ได้คำนวณ PM-03 (v1.14) · หน้าเว็บแสดง "—" ไม่ใช่ 0% |
| `topics_not_passed` | integer \| null | จำนวนหัวข้อที่ `level ≠ passed` (PM-04) · null ตามกฎเดียวกับ `readiness` (v1.14) |

- **`POST /exam-preps`** · body `{title: string, exam_date: string (date), daily_minutes?: integer}` (CM-01) · `201` + `ExamPrep` (`stage = "materials"`, `readiness` และ `topics_not_passed` เป็น null) · บันทึกลง `exam_preps` ด้วย JWT ของผู้ใช้ (RLS) · `tenant_id` และ `user_id` มาจาก token เสมอ ไม่รับจาก body (v1.14)
  - `title`: ชื่อวิชาหรือการสอบที่ผู้ใช้พิมพ์ เช่น "แคลคูลัส 1 กลางภาค" · ตัดช่องว่างหัวท้าย · ไม่ว่าง · ยาวไม่เกิน `config/ai.yaml` → `guards.max_exam_prep_title_chars` นับเป็น grapheme cluster (สระและวรรณยุกต์ไทยไม่นับแยก · แบบเดียวกับ `max_attachment_name_chars`) · ห้ามมีอักขระควบคุม (Unicode category `Cc` เช่น `\n`, `\t`, `\x00`) ตรงไหนก็ตาม รวมหัวท้าย (ตรวจก่อนตัดช่องว่าง `"แคลคูลัส\n"` จึงถูกปฏิเสธ ไม่ใช่ถูกตัดทิ้ง) · อักขระจัดรูปแบบอย่าง zero-width joiner ยังได้ (v1.14 · title คือ `prep_name` ของห้องและอาจเข้า prompt ของ tutor ทีหลัง) · ไม่มี field `subject` แยก (เทอม 1 เป็นคณิตอย่างเดียว · `exam_preps.subject` เป็น null)
  - `exam_date`: `YYYY-MM-DD` · วันนี้ได้ · ก่อนวันนี้ (Asia/Bangkok) → `422 exam_date_past`
  - `daily_minutes`: ไม่บังคับ (หน้าเว็บไม่ต้องส่ง) · ถ้าส่ง ต้องเป็น integer 1–1440 · ไม่ส่งหรือ `null` = ใช้ค่าจาก `planner.default_daily_minutes` (UC-02 A1)
  - field เกิน, ผิดชนิด หรือผิดกฎข้างบน → `422 validation_error`
  - DB ติดต่อไม่ได้ (error, timeout, network) → `503 db_unavailable` · message คงที่ ไม่มีรายละเอียดจาก exception (ใช้กับ `GET` ด้วย · v1.14)
- **`GET /exam-preps`** · `ExamPrep[]` ของผู้ใช้ (RLS) เรียงตาม `exam_date` ใกล้ก่อน แล้วตาม `created_at` · ไม่รวม `status = 'archived'` · ยังไม่มี → `[]` (v1.14)
- ทั้งสอง endpoint อ่านและเขียน DB จริง **ไม่มี `X-Stub` เมื่อมี token** (v1.14 · เดิมเป็น stub ที่คืน fixture) · ไม่มี token: `AUTH_REQUIRED=true` → `401 missing_token` (ไม่มี stub) · `AUTH_REQUIRED=false` (เครื่อง dev) → stub เดิมพร้อม `X-Stub: true` ไม่แตะ DB (`specs/features/exam-prep/create-exam-prep.md` §2.1)

**`Material`** (แต่ละแถวของ `GET /exam-preps/{id}/materials` และ response ของ `/uploaded`)

| Field | Type | ที่มา |
|---|---|---|
| `id` | string (uuid) | `materials.id` |
| `file_name` | string | `materials.file_name` (แสดงผลอย่างเดียว ไม่ใช้ประกอบ path) |
| `kind` | `"sheet"` \| `"slides"` \| `"past_exam"` \| `"notes"` \| `"other"` \| null | `materials.kind` · null จนกว่า classify เสร็จ |
| `kind_confidence` | number 0–1 \| null | `materials.kind_confidence` (CM-06) |
| `kind_confirmed` | boolean | `materials.kind_confirmed` |
| `user_note` | string \| null | `materials.user_note` (CM-04) |
| `status` | `"uploaded"` \| `"classified"` \| `"confirmed"` \| `"ingesting"` \| `"ready"` \| `"failed"` | `materials.status` (CM-07) |
| `error` | string \| null | `materials.error` · ข้อความสั้นที่แสดงให้ผู้ใช้ได้ เมื่อ `status = "failed"` (UC-02 E5) |

- **`POST /exam-preps/{id}/materials`** · body `{file_name: string (ไม่ว่าง), content_type: string, size_bytes: integer ≥ 1}` (CM-03) · response `{material_id, upload_url, path}` · `path` = `{tenant_id}/{exam_prep_id}/{material_id}` (data-model.md · §2.3.2 ขั้น 1) · สร้างแถว `materials` ที่ `status = "uploaded"` · เกิน `guards.max_material_mb` หรือ `guards.max_image_mb` ถ้าเป็นรูป (1 MB = 1,048,576 bytes · v1.13) → `422 file_too_large` เหมือน `/sessions/{id}/uploads` · ชนิดไฟล์เช็คก่อนขนาด
  - `content_type` ที่รับ (ไม่สนตัวพิมพ์ ตัด parameter หลัง `;` แบบเดียวกับ `/sessions/{id}/uploads`): `application/pdf`, `image/jpeg`, `image/png`, `image/webp`, `image/heic`, PPTX `application/vnd.openxmlformats-officedocument.presentationml.presentation`, DOCX `application/vnd.openxmlformats-officedocument.wordprocessingml.document` · นอกนั้น `422 unsupported_type`
- **`POST /materials/{id}/uploaded`** · body `{user_note?: string}` · `202` + `Material` · เริ่ม classify (§2.3.2 ขั้น 2) · ไฟล์นี้แจ้งไปแล้ว → `409 already_uploaded`
- **`GET /exam-preps/{id}/materials`** · `Material[]` เรียงตามเวลาที่สร้าง · หน้า S10 poll จนทุกไฟล์มี `kind`
- **`POST /exam-preps/{id}/materials/confirm`** · body `{materials: [{id, kind}]}` (ไฟล์ที่จะยืนยัน อย่างน้อย 1 ไฟล์ · `id` ไม่ซ้ำ · ไฟล์ `failed` ไม่ต้องส่ง · `kind` ตาม enum ของ `Material`) · `202` + `{queued: integer}` (จำนวนไฟล์ที่เริ่ม ingest · ขั้น 3) · ตั้ง `kind_confirmed = true` · ไฟล์ใน body ที่ `status` ไม่ใช่ `classified` (ยัง classify ไม่เสร็จ หรือยืนยันไปแล้ว) → `409 not_classified` · ไฟล์ที่ไม่ได้ส่งมาไม่ถูกเช็ค จึงเพิ่มไฟล์ทีหลังได้ (CM-05) · `id` ซ้ำ → `422 validation_error` · `id` ที่ไม่ใช่ไฟล์ของ prep นี้ → `422 unknown_material`

**รอตัดสิน (v1.10 · Junior)** · ข้อเสนอเขียนโดย Jam ช่วง solo 2026-11-02 (PR #105) · stub ทำตามข้อเสนอนี้ไปก่อน ถ้าเปลี่ยนให้แก้ api.md + stub + test ใน PR ใหม่

1. **ชนิดไฟล์ที่รับ** (UC-02 คำถามเปิด 1): PDF, รูป, PPTX, DOCX ตาม ai-orchestration §2.3.3 · ไฟล์ที่ไม่รับปฏิเสธตอนขอที่อัปโหลด (ก่อน browser ส่งไฟล์)
2. ~~**ขนาดไฟล์สูงสุด** (UC-02 คำถามเปิด 1)~~ **ตัดสินแล้ว** (Jam 2026-11-07 · PR #109): `guards.max_material_mb: 50` ตามเพดานของ Supabase Free · รูปใช้ `guards.max_image_mb` เดิม เพราะเข้า `vision_extract` ทั้งก้อนเหมือนรูปในห้องแชท · ข้อที่ยังเปิด:
   - **ไฟล์สแกนล้มก่อนถึงเพดานนี้มาก (Jam):** A2b มี `max_tokens: 16000` และ P3 วัดได้ 3,199–7,943 token จาก 12–14 หน้า · ประมาณจาก 2 ไฟล์ได้ว่าไฟล์สแกนเกินราว 28–70 หน้าจะได้ JSON ขาด แล้ว `failed` หลังอัปโหลดสำเร็จ · ต้องมีเพดานจำนวนหน้าหรือแบ่งไฟล์ก่อนเปิด ingest จริง
   - **`size_bytes` คือค่าที่ client แจ้ง (Junior):** เรียก API ตรงด้วย `size_bytes: 1` แล้วส่งไฟล์ใหญ่ได้ · ของจริงต้องตั้ง `file_size_limit` ของ bucket ให้ตรงค่านี้ หรือตรวจขนาดจริงตอน `/uploaded` · `/sessions/{id}/uploads` ก็เหมือนกัน
   - **หน้าเว็บจะรู้ค่านี้จากไหน:** ยังไม่กำหนด (May · ตอนเขียน spec ของ S09)
3. ~~**วันสอบ** (UC-02 คำถามเปิด 2)~~ **ตัดสินแล้ว** (Junior 2026-11-11 · v1.14): วันนี้ได้ · ก่อนวันนี้ได้ `422 exam_date_past`
4. ~~**`stage`, `readiness`, `topics_not_passed` ใน `ExamPrep`**~~ **ตัดสินแล้ว** (Junior 2026-11-11 · v1.14): ใช้ตามข้อเสนอ · `readiness` และ `topics_not_passed` เป็น null ได้จนกว่า backend จะคำนวณ PM-03, PM-04 จริง
5. **ประเภทไฟล์:** UC-02 ขั้น 4 พูดถึง "แบบฝึกหัด" แต่ check ของ `materials.kind` ไม่มีค่านี้ · ข้อเสนอคือใช้ enum ของ schema (`sheet`, `slides`, `past_exam`, `notes`, `other`) และนับแบบฝึกหัดเป็น `sheet`
6. **error code ใหม่:** ~~`exam_date_past`~~ (ตัดสินแล้ว v1.14), `unsupported_type` และ `file_too_large` (เหมือนห้องติว), `already_uploaded`, `not_classified`, `unknown_material`

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

**ความคืบหน้า แชทแก้ขอบเขต และ change log (v1.11 · ข้อเสนอ รอ Junior ตัดสิน):** UC-02 ขั้น 6–12 (S11, S13, S14) · ai-orchestration §2.3.2 ขั้น 4–6, §2.3.4, §2.3.6 · ยังไม่มี feature spec ของหน้าจอ · ทุก field ต้องมี และไม่มี field อื่น · prep หรือไฟล์ที่ไม่มีหรือเป็นของ tenant อื่น → `404 not_found`

**`Ingestion`** (response ของ `GET /exam-preps/{id}/ingestion` · CM-07) · หน้า S11 poll จน `scope_ready = true` แล้วไป S12 เอง · ยังไม่มีไฟล์ที่ยืนยัน ก็ตอบ `200` และ `files` เป็น `[]`

| Field | Type | ที่มา |
|---|---|---|
| `scope_ready` | boolean | `true` เมื่อ `GET /exam-preps/{id}/scope` ไม่ตอบ `409 scope_not_ready` **และ**ไม่มีไฟล์ที่ยืนยันแล้วซึ่งยัง `confirmed`, `ingesting` หรือ `failed` · หัวข้อเดิมครบแล้วแต่กำลังอ่านไฟล์ใหม่ (CM-05) ยังเป็น `false` |
| `files` | `IngestionFile[]` | ไฟล์ที่ `kind_confirmed = true` เรียงตามเวลาที่สร้าง · ถ้ามี scope version แล้ว เอาเฉพาะไฟล์ที่มีแถว `ingestion_jobs` ซึ่ง `updated_at` หลัง `confirmed_at` ของ version นั้น (UC-02 A9) ไม่ใช้เวลาที่สร้างไฟล์ เพราะไฟล์ที่อัปโหลดก่อนยืนยันอาจเริ่มอ่านทีหลังได้ |
| `steps` | `{label: string, status: "pending" \| "running" \| "done" \| "failed"}[]` | ขั้นรวมของทั้ง prep เรียงตามลำดับที่แสดง · `label` เป็นข้อความพร้อมแสดงจาก backend: "อ่านสิ่งที่คุณเขียนกำกับไว้", "หาหัวข้อและลำดับการเรียน", "เทียบกับข้อสอบเก่า {n} ชุด" · ไม่มีข้อสอบเก่าก็ไม่มีขั้นสุดท้าย (UC-02 E1) |

**`IngestionFile`**

| Field | Type | ที่มา |
|---|---|---|
| `material_id` | string (uuid) | `materials.id` |
| `file_name` | string | `materials.file_name` |
| `status` | `"queued"` \| `"running"` \| `"done"` \| `"failed"` | ค่าเดียวกับ `ingestion_jobs.status` · รวมจากทุกแถวของไฟล์นั้น |
| `detail` | string \| null | ข้อความพร้อมแสดงจาก backend เช่น "14 หน้า", "12 ข้อ", "กำลังแยกรายข้อ" |
| `error` | string \| null | ข้อความสั้นที่แสดงให้ผู้ใช้ได้ เมื่อ `status = "failed"` (UC-02 E5) |

- **`POST /materials/{id}/retry`** · ปุ่ม "ลองใหม่" ของ UC-02 E5 · ไม่มี body · `202` + `Material` · อ่านไฟล์ใหม่ตั้งแต่ขั้นที่ล้ม · ล้มตอน classify (เห็นใน S10) → `status = "uploaded"` · ล้มตอน ingest (เห็นใน S11) → `status = "confirmed"` · `error` เป็น null · ไฟล์ที่ `status` ไม่ใช่ `failed` → `409 not_failed`
- **`DELETE /materials/{id}`** · ปุ่ม "ไปต่อโดยไม่มีไฟล์นี้" ของ UC-02 E5 และการลบไฟล์ของ CM-10 · `204` ไม่มี body · ไฟล์ที่ `status` เป็น `confirmed` หรือ `ingesting` → `409 material_busy`

**`POST /exam-preps/{id}/scope/chat`** (S13 · SM-06, SM-07 · A8 `scope_edit`) · body `{text: string (ไม่ว่าง)}` · ตอบเป็น SSE: `scope_patch` 0 ตัวขึ้นไป → `token` (`speaker = "tutor"`) → `done` (`{}`)

- code ตรวจ action ของ AI ก่อน (§2.3.6) แล้วจึงส่ง `scope_patch` และคำตอบ เพราะ A8 คืน JSON ก้อนเดียว · action ไม่ผ่านการตรวจ → ไม่มี `scope_patch` มีแค่ `token` ที่ถามผู้ใช้ใหม่ (UC-02 E2)
- แก้หลังยืนยันแล้วได้ · `Scope.status` กลับเป็น `"draft"` ตามกฎของ v1.6
- error: `409 scope_not_ready` · `422 validation_error` · `422 message_too_long` (เกิน `guards.max_message_chars`) · `429 rate_limited` + `Retry-After` (ตัวนับเดียวกับข้อความในห้องติว · `gateway-guards.md` §2.1) · AI ล่มกลาง stream → event `error` (`ai_unavailable`)

**`scope_patch.changes`** มีเฉพาะ field ของ `ScopeTopic` ที่เปลี่ยน (อย่างน้อย 1 field · ไม่มี `id` · ไม่มีค่า null · `name` ไม่ว่าง) · หน้าเว็บเอาไปทับการ์ดของ `topic_id` · ไม่รู้จัก `topic_id` และ `changes` มีครบทุก field = การ์ดใหม่ · ไม่รู้จักแต่ไม่ครบ (รายการในหน้าเว็บเก่า) → โหลด `GET /scope` ใหม่ ไม่สร้างการ์ด

| op ของ AI | event ที่ส่ง |
|---|---|
| `set_importance`, `exclude`, `include` | `{stars, reason}` · ตัดออก = `stars: 0` |
| `rename` | `{name}` |
| `reorder` | 1 event ต่อหัวข้อที่ `order` เปลี่ยน · `{order}` |
| `add_topic` | ทุก field ของ `ScopeTopic` ยกเว้น `id` · `topic_id` คือ id ใหม่ · `origin = "user"` |
| `exclude_skill`, `include_skill` | ไม่ส่ง เพราะ skill ไม่อยู่บนการ์ด (SM-12) · ยังมีแถวใน change log |

**`ScopeChange`** (แต่ละแถวของ `GET /exam-preps/{id}/scope/changes` · S14 · SM-08) · เรียงตาม `created_at` เก่าไปใหม่ · แก้หัวข้อเดิมหลายครั้งได้หลายแถว · เฉพาะแถวที่ `created_at` หลัง `confirmed_at` ของ scope version ปัจจุบัน ทั้งหมดถ้ายังไม่เคยยืนยัน (กฎเดียวกับ `Scope.status`) · error: `409 scope_not_ready`

| Field | Type | ที่มา |
|---|---|---|
| `id` | string (uuid) | `scope_changes.id` |
| `topic_id` | string (uuid) | `scope_changes.topic_id` · แถวที่ `topic_id` เป็น null ไม่ส่ง |
| `topic_name` | string | `topics.name` ปัจจุบัน |
| `op` | `"set_importance"` \| `"exclude"` \| `"include"` \| `"rename"` \| `"reorder"` \| `"add_topic"` \| `"exclude_skill"` \| `"include_skill"` | `scope_changes.op` |
| `before` | object \| null | `scope_changes.before` · `{stars}` (`set_importance`, `exclude`, `include`) · `{name}` (`rename`) · `{order}` (`reorder`) · `{skill_name}` (`exclude_skill`, `include_skill`) · `add_topic` เป็น null |
| `after` | object \| null | `scope_changes.after` · รูปแบบเดียวกับ `before` · `add_topic` เป็น `{name, stars}` |
| `reason` | string \| null | `scope_changes.reason` |
| `actor` | `"user"` \| `"ai"` \| `"system"` | `scope_changes.actor` |
| `created_at` | string (ISO 8601) | `scope_changes.created_at` |

**รอตัดสิน (v1.11 · Junior)** · ข้อเสนอเขียนโดย Jam ช่วง solo 2026-11-04 (PR #106) · stub ทำตามข้อเสนอนี้ไปก่อน ถ้าเปลี่ยนให้แก้ api.md + stub + test ใน PR ใหม่

1. **`ingestion_jobs` ของขั้นรวม:** `material_id` ห้าม null แต่หัวข้อกับดาวทำต่อ prep ไม่ใช่ต่อไฟล์ และไม่มี stage ของ "อ่านสิ่งที่เขียนกำกับ" · ข้อเสนอคือ migration ให้ `material_id` เป็น null ได้ + เพิ่ม `exam_prep_id`
2. **ไฟล์ `failed` ที่ผู้ใช้ยังไม่ตัดสิน:** ข้อเสนอคือขั้นรวมหัวข้อ (A6) รอจนทุกไฟล์เสร็จหรือถูกลบ เพื่อไม่ต้องเรียก main tier ซ้ำ
3. **ลบไฟล์ที่ `ready` แล้ว:** หัวข้อที่สร้างจากไฟล์นั้นต้องเป็นอย่างไร (CM-10) · ยังไม่มีคำตอบ
4. **ประวัติแชท S13:** ฝั่ง prompt ตัดสินแล้ว (Jam 2026-11-07 · PR #109): A8 ได้ `session.context_recent_turns` ข้อความล่าสุดจาก server (ai-orchestration §2.3.6) · **ที่เก็บยังรอ Junior:** `messages.session_id` ห้าม null · body `{text}` ใช้ได้ทุกทาง · ยังไม่มี endpoint อ่านประวัติ รีเฟรชแล้วเริ่มคุยใหม่
5. **พูดใน S13 (SM-06):** `/sessions/{id}/uploads` และ `/transcribe` ผูกกับ session แต่ S13 ไม่มี session · **stub รอบนี้รับแค่ข้อความพิมพ์ ฝั่งเสียงของ SM-06 ยังไม่ครบ**
6. **ข้อความพร้อมแสดง:** `steps.label` และ `files.detail` สร้างที่ backend แบบเดียวกับ `source_label` · May อาจอยากคุมข้อความเอง
7. **error code ใหม่:** `not_failed`, `material_busy` · ใช้ซ้ำ: `scope_not_ready`, `message_too_long`, `rate_limited`
8. **ขั้นรวมล้ม (`steps[].status = "failed"`):** เช่น A6 ล้มหลัง retry ครบ · `scope_ready` เป็น `false` และ S11 ต้องหยุด poll · ยังไม่มีทางออกให้ผู้ใช้: endpoint ลองใหม่ของขั้นรวม (Junior) และหน้าตาของสถานะนี้ใน S11 (May · UC-02 E5 พูดถึงเฉพาะรายไฟล์)

### ห้องติว (flow 2.2, 2.4, 2.5, 2.1)

| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/exam-preps/{id}/sessions/active` | session ที่ยังเปิดอยู่ของการเตรียมสอบนี้ `{session_id}` · 404 `no_active_session` ถ้าไม่มี (TM-13 · ข้อเสนอ ดูด้านล่าง) |
| POST | `/exam-preps/{id}/sessions` | **SSE:** สร้าง session → `session` → `progress_card` → `token` (ข้อความเปิด) → `problem` → `done` |
| GET | `/sessions/{id}` | ข้อมูลห้อง `Room` (หัวห้อง + `limits` + ข้อความ) · ใช้ตอนเปิดห้องและกลับมาต่อ (TM-13) |
| POST | `/sessions/{id}/uploads` | signed URL สำหรับรูปหรือเสียง |
| POST | `/sessions/{id}/transcribe` | เสียง → text (ใส่ช่องพิมพ์ ไม่ส่งเอง) |
| POST | `/sessions/{id}/messages` | **SSE:** body `{text?, image_path?}` อย่างน้อยหนึ่งค่า · ถ้ามีทั้งคู่ `text` เป็นคำบรรยายของรูป (ดูด้านล่าง) · `429 rate_limited` (Conventions · v1.8) |
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

**รูป เสียง และยืนยันลายมือ (v1.7 · ข้อเสนอ รอ Junior ตัดสิน):** ตอบ `voice-input.md` OQ 6 และ `ocr-confirm-card.md` OQ 5–6 ของ May · ทุก field ต้องมี และไม่มี field อื่น · session ที่ไม่มีหรือเป็นของ tenant อื่น → `404 not_found`

**`POST /sessions/{id}/uploads`** · ขอที่อัปโหลดไฟล์ 1 ไฟล์ แล้ว browser `PUT` ไฟล์เข้า Storage เอง (แบบเดียวกับ `materials` · flow 2.3.8 ข้อ 2)

| | Field | Type | หมายเหตุ |
|---|---|---|---|
| Request | `kind` | `"image"` \| `"audio"` | รูปวิธีทำ (TM-06) หรือเสียงพูด (TM-07) |
| | `content_type` | string | image: `image/jpeg`, `image/png`, `image/webp`, `image/heic` · audio: `audio/webm`, `audio/ogg`, `audio/mp4` · ไม่สนตัวพิมพ์ และตัด parameter หลัง `;` ก่อนเทียบ (`audio/webm;codecs=opus` ของ Chrome ใช้ได้) · นอกนั้น `422 unsupported_type` |
| | `file_name` | string | ชื่อไฟล์เดิม · backend เก็บเป็น `messages.attachment_name` ตอนส่งข้อความ (ตัดตาม `guards.max_attachment_name_chars` · data-model.md) · ไม่ใช้ประกอบ path |
| | `size_bytes` | integer ≥ 1 | image เกิน `guards.max_image_mb` (1 MB = 1,048,576 bytes) → `422 file_too_large` |
| Response | `upload_url` | string | signed upload URL ของ Supabase Storage · ใช้ได้ครั้งเดียวและหมดอายุ |
| | `path` | string | `{tenant_id}/sessions/{session_id}/{uuid}.{ext}` · ส่งต่อเป็น `image_path` ของ `POST /sessions/{id}/messages` หรือ `audio_path` ของ `/transcribe` |

**`POST /sessions/{id}/transcribe`** · เสียง → ข้อความ ใส่ช่องพิมพ์ **ไม่ส่งเอง** (ai-orchestration §2.2.5)

- Request `{audio_path: string}` (path จาก `/uploads` ของ session นี้ · path ของ session อื่น → `404 not_found`) · Response `{text: string}` · ไม่ได้ยินเสียงได้ `{text: ""}` (หน้าเว็บแสดงข้อความเอง · voice-input AC-12)
- error: `422 audio_too_long` (ยาวเกิน `guards.max_audio_seconds`) · `503 stt_unavailable` (STT ล่มหลัง retry · §2.10)

**`POST /sessions/{id}/ocr/confirm`** · ยืนยันหรือแก้บรรทัดที่อ่านจากรูป แล้ว stream ผลตรวจ

- Request `{lines: string[]}` · ทุกบรรทัดตามลำดับ แต่ละบรรทัดไม่ว่าง (ช่องว่างล้วนบนการ์ดคือยกเลิกการแก้ · ocr-confirm-card OQ 2) จำนวนเท่ากับ `ocr_preview.lines` ใบล่าสุด (หน้าเว็บแก้ได้แต่เพิ่มหรือลบบรรทัดไม่ได้ · ocr-confirm-card OQ 3) · backend เทียบกับ preview เองเพื่อ log บรรทัดที่แก้ (AM-03)
- Response: SSE แบบเดียวกับ `POST /sessions/{id}/messages`: `verdict` → `token`… → `done` (verdict มาก่อน tutor เริ่มพิมพ์ · §2.4.5)
- error: `409 no_pending_ocr` (ไม่มี preview ที่รอยืนยัน) · `422 ocr_lines_mismatch` (จำนวนบรรทัดไม่เท่า) · `429 rate_limited` (Conventions · v1.8)

**preview ที่ค้าง (ocr-confirm-card OQ 5, 7):** ไม่มี endpoint ยกเลิก · ส่งรูปใหม่ → preview ใหม่แทนใบเดิม · พิมพ์ข้อความระหว่างที่ preview ค้าง → เป็นข้อความปกติ (ตอบคำถามได้) และ preview ยังรอยืนยัน

**รอตัดสิน (v1.7 · Junior)** · ข้อเสนอเขียนโดย Jam ช่วง solo 2026-11-01 (PR #102) · stub ทำตามข้อเสนอนี้ไปก่อน ถ้าเปลี่ยนให้แก้ api.md + stub + test ใน PR ใหม่

1. **body และ response ของ `/uploads`** (voice-input OQ 6): เพิ่ม `file_name` และ `size_bytes` จากข้อเสนอของ May (`{kind, content_type}`) เพื่อเก็บ `attachment_name` และปฏิเสธไฟล์ใหญ่ก่อนอัปโหลด · ขนาดจริงต้องตรวจซ้ำตอนใช้ไฟล์ เพราะ browser ส่งค่านี้เอง · เสียงไม่มีเพดานขนาด ตรวจความยาวตอน `/transcribe` แทน
2. **path ใน Storage:** `{tenant_id}/sessions/{session_id}/{uuid}.{ext}` ตามกฎ prefix ของ tenant (data-model.md) · ต้องสร้าง bucket + storage policy
3. **ทาง "ถ่ายใหม่" และข้อความระหว่าง preview ค้าง** (ocr-confirm-card OQ 5): เลือกทาง (ข) ไม่มี endpoint · ข้อความที่พิมพ์เป็นข้อความปกติ
4. **`ocr_preview.lines[].latex` เป็น LaTeX ล้วนไม่มี `$`** (ocr-confirm-card OQ 6) เหมือน `problem.text_latex` · Jam ตกลง (เจ้าของ prompt `extract_answer`)
5. **error code ใหม่:** `unsupported_type`, `file_too_large`, `audio_too_long`, `stt_unavailable`, `no_pending_ocr`, `ocr_lines_mismatch`

**จบ session ประวัติแชท progress card และเสียงอ่าน (v1.9 · ข้อเสนอ รอ Junior ตัดสิน):** ทุก field ต้องมี และไม่มี field อื่น · session, prep หรือข้อความที่ไม่มีหรือเป็นของ tenant อื่น → `404 not_found`

**`POST /sessions/{id}/end`** · ผู้ใช้กดจบ session (PM-05 · ai-orchestration §2.2.9) · ไม่มี body

- Response: SSE `session_end` `{summary_lines: string[]}` (1–2 บรรทัดที่ไม่ว่าง · ai-orchestration §2.2.9 เขียนว่า 2 บรรทัด ดูรอตัดสินข้อ 6 · `session_summary` ทำจาก running summary · บันทึกที่ `tutor_sessions.summary` และเป็นข้อความในแชทด้วย ดูรอตัดสินข้อ 7) → `done`
- สิ่งที่ backend ทำ: ตั้ง `tutor_sessions.ended_at = now()` และ `end_reason = 'user'` **ก่อน**เรียก AI ด้วยคำสั่งเดียวที่มีเงื่อนไข `ended_at is null` (request ที่มาพร้อมกันได้ 409 แทนการเรียก `session_summary` ซ้ำ) · คำนวณการเปลี่ยนแปลงของ mastery ตาม §2.2.9 (ยังไม่มีใน stub)
- error: `409 session_already_ended` (`ended_at` ไม่เป็น null) · ตอบก่อนเริ่ม SSE
- จบแบบอื่น (`time_budget`, `plan_done`, `idle`) เป็นของ backend เอง ไม่ผ่าน endpoint นี้

**`GET /sessions/{id}/messages`** · ประวัติแชท (TM-13)

- Response: `Message[]` เป็น array ตรงๆ เรียงตาม `created_at` เก่าไปใหม่ · รูปร่างเดียวกับ `Room.messages`
- ยังไม่แบ่งหน้า

**`GET /exam-preps/{id}/progress`** · progress card ตอนผู้ใช้ขอดู (TM-11) · หน้าแรกก่อนเข้าห้อง (TM-15)

- Response: schema `ProgressCardEvent` ตัวเดียวกับ payload ของ event `progress_card` (หน้าเว็บใช้ type เดียว) (`{days_left, passed, total, readiness, topics}` · `topics[]` ตาม "`progress_card.topics[]`" ด้านล่าง)
- error: `409 scope_not_confirmed` (prep ยังไม่มี `active_scope_version_id` · progress นับจาก scope ที่ยืนยันแล้ว)

**`GET /messages/{id}/tts`** · เสียงอ่านข้อความของ tutor (TM-09 · เทอม 2 · ตอนนี้มีแค่ stub)

- Response: `{audio_url: string}` · signed URL ของไฟล์เสียงใน Storage ที่ cache ตาม hash(text + voice) (§2.8)
- error: `409 tts_unavailable` (ไม่ใช่ข้อความของ tutor ตาม TM-09 · หรือข้อความว่าง) · `503 tts_unavailable` เมื่อ TTS ล่ม

**รอตัดสิน (v1.9 · Junior)** · ข้อเสนอเขียนโดย Jam ช่วง solo 2026-11-02 (PR #104) · stub ทำตามข้อเสนอนี้ไปก่อน ถ้าเปลี่ยนให้แก้ api.md + stub + test ใน PR ใหม่

1. **`/end` ตอบเป็น SSE:** เพราะ `session_end` เป็น event และสรุปมาจาก AI call · ทางเลือกคือตอบ JSON `{summary_lines}` ธรรมดา
2. **`/end` ไม่นับใน rate limit** (`gateway-guards.md` §2.1 นับเฉพาะข้อความที่ผู้ใช้ส่ง) · ถึงจะเรียก AI แต่จบ session ได้ครั้งเดียว (ครั้งที่สองได้ 409)
3. **`GET /sessions/{id}/messages` ยังไม่แบ่งหน้า** · ต้องมีก่อน Beta ถ้า session ยาว
4. **`GET /exam-preps/{id}/progress` ใช้รูปร่างเดียวกับ event** · หน้าเว็บใช้ component เดียวกันทั้งสองที่
5. **error code ใหม่:** `session_already_ended`, `scope_not_confirmed` (มีในตัวอย่างของ Conventions อยู่แล้ว), `tts_unavailable`
6. **จำนวนบรรทัดของสรุป** (self-review #104): ai-orchestration §2.2.9 และ §3.3 เขียนว่า "สรุป 2 บรรทัด" · ตาราง SSE เดิมเขียน `[..2]` · ข้อเสนอคือรับ 1–2 บรรทัด (session สั้นอาจมีเรื่องเดียว) · ถ้าต้อง 2 บรรทัดพอดี ให้แก้ `SessionEndEvent`
7. **เก็บสรุปเป็นข้อความในแชทด้วย** (self-review #104): PM-05 ให้สรุป "ในรูปแบบ chat message" · ถ้าเก็บแค่ `tutor_sessions.summary` สรุปจะหายจาก `GET /sessions/{id}/messages` หลังโหลดหน้าใหม่ และไม่มี id ให้ `/tts` · ข้อเสนอคือเพิ่มแถวใน `messages` (role `tutor`) และส่ง id ใน `done.message_ids`
8. **TTS อ่านข้อความของ buddy ด้วยไหม:** TM-09 พูดถึงข้อความของ tutor เท่านั้น · ข้อเสนอคือตาม TM-09 (เพิ่ม buddy ต้องแก้ requirement)
9. **id ของข้อความและหัวข้อใน fixture ของห้องติวไม่ใช่ uuid** (`m0`, `t1` · ของเดิมตั้งแต่ PR #38): `/messages/{id}/tts` และ `/topics/{id}/sources` รับ uuid · ของจริงเป็น uuid ทั้งหมด (`messages.id`, `topics.id`) · ข้อเสนอคือเปลี่ยน `Message.id` และ `ProgressTopic.id` เป็น uuid พร้อม fixture ใน PR ที่ต่อห้องติวกับ DB

### บัญชี

| Method | Path | ทำอะไร |
|---|---|---|
| DELETE | `/me` | ลบบัญชีและข้อมูลทั้งหมด (UM-10) · `204` |
| DELETE | `/exam-preps/{id}` · `/materials/{id}` | ลบรายการหรือไฟล์ (CM-10) · `204` · `/materials/{id}` ดู v1.11 · ไม่พบ → `404 not_found` |

## SSE events

| Event | Payload | Flow |
|---|---|---|
| `session` | `{session_id}` · event แรกของ `POST /exam-preps/{id}/sessions` | 2.2 |
| `token` | `{speaker: "tutor" \| "buddy", text}` | 2.2, 2.3 |
| `scope_patch` | `{topic_id, changes}` · `changes` มีเฉพาะ field ของ `ScopeTopic` ที่เปลี่ยน (ดู v1.11) | 2.3 |
| `progress_card` | `{days_left, passed, total, readiness, topics: [{id, name, stars, level, review_due, origin}]}` · type ของ `topics[]` ดูด้านล่าง | 2.2 |
| `problem` | `{problem_id, text_latex, difficulty, purpose}` (ไม่มีเฉลย) | 2.2 |
| `ocr_preview` | `{lines: [{latex, confidence}]}` · `latex` เป็น LaTeX ล้วนไม่มี `$` · `confidence` 0–1 (หน้าเว็บไม่แสดง · ยืนยันทุกครั้ง AM-02) · `lines` ไม่ว่าง (รูปที่อ่านไม่ได้ส่งเป็น `token` แทน) · v1.7 | 2.2 |
| `verdict` | `{verdict, first_wrong_line, error_type}` · `verdict`: `correct` \| `correct_with_flaw` \| `incomplete` \| `incorrect` · `first_wrong_line`: integer ≥ 1 หรือ null · `error_type`: `calculation` \| `sign` \| `wrong_method` \| `concept` \| `prerequisite` \| `no_answer` หรือ null · ชุดค่าตาม `merge-rules.md` §2: `correct` → ทั้งสองเป็น null · `incomplete` → `concept` + line null · `no_answer` → `incorrect` + line null · นอกนั้นมีทั้ง line และ error_type · v1.7 | 2.4 |
| `buddy` | `{text}` (ใช้เมื่อ buddy ตอบนอกจังหวะ 2.1.7) | 2.1 |
| `session_end` | `{summary_lines: [..2]}` · 1–2 บรรทัด · มาจาก `POST /sessions/{id}/end` (v1.9) | 2.2 |
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
