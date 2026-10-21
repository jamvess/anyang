# API (v1.2)

Backend: FastAPI ที่ Cloud Run · เอกสาร OpenAPI สร้างอัตโนมัติที่ `/docs` · frontend generate types จาก `/openapi.json`

## Conventions

- **Auth:** ส่ง Supabase access token ใน `Authorization: Bearer <jwt>` ทุก request backend ส่ง token นี้ต่อให้ Supabase เพื่อให้ RLS ทำงาน
- **Error:** `{"error": {"code": "scope_not_confirmed", "message": "..."}}` พร้อม HTTP status ที่ตรงความหมาย
- **Long-running jobs:** ตอบ `202 Accepted` แล้วให้ client poll endpoint ความคืบหน้า
- **Streaming:** SSE ผ่าน `POST` (client ใช้ `fetch` + `ReadableStream`) ทุก stream จบด้วย event `done`
- **Request ID:** ทุก response มี header `X-Request-Id` ใช้ไล่ log ข้าม AI call และ DB

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

### ห้องติว (flow 2.2, 2.4, 2.5, 2.1)

| Method | Path | ทำอะไร |
|---|---|---|
| GET | `/exam-preps/{id}/sessions/active` | session ที่ยังเปิดอยู่ของการเตรียมสอบนี้ `{session_id}` · 404 `no_active_session` ถ้าไม่มี (TM-13 · ข้อเสนอ ดูด้านล่าง) |
| POST | `/exam-preps/{id}/sessions` | **SSE:** สร้าง session → `session` → `progress_card` → `token` (ข้อความเปิด) → `problem` → `done` |
| GET | `/sessions/{id}` | ข้อมูลห้อง `Room` (หัวห้อง + `limits` + ข้อความ) · ใช้ตอนเปิดห้องและกลับมาต่อ (TM-13) |
| POST | `/sessions/{id}/uploads` | signed URL สำหรับรูปหรือเสียง |
| POST | `/sessions/{id}/transcribe` | เสียง → text (ใส่ช่องพิมพ์ ไม่ส่งเอง) |
| POST | `/sessions/{id}/messages` | **SSE:** body `{text}` หรือ `{image_path}` (ข้อเสนอ `{text, image_path}` รอ Jam ตัดสิน ดูด้านล่าง) |
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

**`Message`:** `{id, role: "user" | "tutor" | "buddy" | "card" | "system", content: string | null, card: object | null, input_mode: "text" | "voice" | "image" | null, attachment_path: string | null, created_at}` · ไม่ส่ง `extracted_text` และ `intent` (ใช้ภายใน backend) · ตัวอย่างรูปร่าง: `apps/web/tests/fixtures/room/session-s15.json` (ยังไม่มี `session_id` และ `card`)

**ระบบช้า (degrade ของ tutor, ai-orchestration.md §2.10):** ส่งข้อความ template "ระบบช้า ลองส่งอีกทีนะ" เป็น `token` ที่ `speaker: "tutor"` แล้วตาม `done` และบันทึกเป็นข้อความ tutor ปกติใน `messages` · ส่ง `error` เฉพาะเมื่อไม่มีอะไรให้แสดงเลย

**รอตัดสิน (PR #35)**

1. **ส่งรูปพร้อมข้อความกำกับ** (รอ Jam): UI ส่ง `{text, image_path}` พร้อมกันได้ (`chat-room-ui.md` §11) · กระทบ flow รูป → `ocr_preview` → `ocr/confirm` → checker ต้องตัดสินว่าข้อความกำกับไปอยู่ตรงไหน (เช่น context ของ checker, ข้อความ user แยก, หรือไม่ใช้) · จนกว่าจะตัดสิน body ยังเป็นแบบเดิม
2. **หา session ที่เปิดอยู่ (TM-13):** หน้า room รู้แค่ prep id · ข้อเสนอ `GET /exam-preps/{id}/sessions/active` (ด้านบน) ทางเลือกคือให้ `POST /exam-preps/{id}/sessions` คืน session เดิมถ้ายังเปิดอยู่ · เลือก GET เพราะไม่มีผลข้างเคียง ไม่เรียก AI ไม่สร้างข้อความเปิดซ้ำ และ POST ยังมีความหมายเดียวคือเริ่ม session ใหม่ (stream เดียว ไม่ต้องมีสองรูปแบบ response) · "เปิดอยู่" = `ended_at is null` · ถ้ามีหลายอันใช้อันล่าสุด (กันสองแท็บสร้างซ้อนด้วย unique index ได้ภายหลัง ต้องแก้ migration)
3. **สมการใน `content` และ `token.text`** (รอ May): ตอนนี้ใช้ `$…$` (inline) และ `$$…$$` (block) ทั้งสองฝั่งหาด้วย regex ง่ายๆ · ยังไม่ตัดสินว่าใช้เป็น contract หรือเปลี่ยน · ต้องดู: `$` ที่ไม่ใช่สมการ (ราคา "$5"), `\$` ที่ escape ไว้, prompt `tutor_reply` ของ Jam ต้องใช้รูปแบบเดียวกัน · `problem.text_latex` เป็น LaTeX ล้วนไม่มีตัวคั่น ไม่อยู่ในข้อนี้
4. **รายการ `error.code` ของห้องติว** (Junior · ยังเปิด): ตอนนี้มีแค่รูปแบบ `{code, message}`
5. **id ของข้อความที่ stream มา** (Junior + May): event `token` และ `buddy` ไม่มี id จาก server UI จึงใช้ id ในเครื่อง แต่ `GET /messages/{id}/tts` ต้องใช้ id จริง · ทางเลือก: ส่ง id ของข้อความที่บันทึกแล้วมากับ `done` (เช่น `{message_ids: [...]}`) หรือให้ UI โหลด `GET /sessions/{id}/messages` ใหม่หลัง `done`
6. **ชื่อไฟล์ใน `attachment_path`** (Junior + May): UI แสดงชื่อไฟล์จากส่วนท้ายของ path ("วิธีทำ.jpg") ถ้า backend ตั้งชื่อไฟล์ใน Storage เป็น uuid ผู้ใช้จะเห็น uuid · ทางเลือก: เก็บชื่อเดิมไว้ท้าย path (`…/<uuid>/วิธีทำ.jpg`) หรือเพิ่ม field ชื่อไฟล์ (ต้องแก้ migration)

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
| `progress_card` | `{days_left, passed, total, readiness, topics: [{id, name, stars, level, review_due, origin}]}` | 2.2 |
| `problem` | `{problem_id, text_latex, difficulty, purpose}` (ไม่มีเฉลย) | 2.2 |
| `ocr_preview` | `{lines: [{latex, confidence}]}` | 2.2 |
| `verdict` | `{verdict, first_wrong_line, error_type}` | 2.4 |
| `buddy` | `{text}` (ใช้เมื่อ buddy ตอบนอกจังหวะ 2.1.7) | 2.1 |
| `session_end` | `{summary_lines: [..2]}` | 2.2 |
| `done` | `{}` | ทั้งหมด |
| `error` | `{code, message}` · ใช้เมื่อไม่มีข้อความให้แสดง (degrade ที่มีข้อความ template ส่งเป็น `token`) · รายการ code ยังเปิดอยู่ | ทั้งหมด |
