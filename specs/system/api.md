# API (v1.1)

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
| POST | `/exam-preps/{id}/sessions` | **SSE:** สร้าง session → `progress_card` → `token` (ข้อความเปิด) → `problem` → `done` |
| POST | `/sessions/{id}/uploads` | signed URL สำหรับรูปหรือเสียง |
| POST | `/sessions/{id}/transcribe` | เสียง → text (ใส่ช่องพิมพ์ ไม่ส่งเอง) |
| POST | `/sessions/{id}/messages` | **SSE:** body `{text}` หรือ `{image_path}` |
| POST | `/sessions/{id}/ocr/confirm` | ยืนยันหรือแก้ข้อความที่อ่านจากรูป แล้ว stream ผลต่อ |
| POST | `/sessions/{id}/end` | จบ session → `session_end` |
| GET | `/sessions/{id}/messages` | ประวัติแชท (สำหรับกลับมาต่อ TM-13) |
| GET | `/exam-preps/{id}/progress` | ข้อมูล progress card |
| GET | `/messages/{id}/tts` | URL ไฟล์เสียง (cache ตาม text + voice) |

### บัญชี

| Method | Path | ทำอะไร |
|---|---|---|
| DELETE | `/me` | ลบบัญชีและข้อมูลทั้งหมด (UM-10) |
| DELETE | `/exam-preps/{id}` · `/materials/{id}` | ลบรายการหรือไฟล์ (CM-10) |

## SSE events

| Event | Payload | Flow |
|---|---|---|
| `token` | `{speaker: "tutor" \| "buddy", text}` | 2.2, 2.3 |
| `scope_patch` | `{topic_id, changes}` | 2.3 |
| `progress_card` | `{days_left, passed, total, readiness, topics: [{id, name, stars, level, review_due, origin}]}` | 2.2 |
| `problem` | `{problem_id, text_latex, difficulty, purpose}` (ไม่มีเฉลย) | 2.2 |
| `ocr_preview` | `{lines: [{latex, confidence}]}` | 2.2 |
| `verdict` | `{verdict, first_wrong_line, error_type}` | 2.4 |
| `buddy` | `{text}` (ใช้เมื่อ buddy ตอบนอกจังหวะ 2.1.7) | 2.1 |
| `session_end` | `{summary_lines: [..2]}` | 2.2 |
| `done` | `{}` | ทั้งหมด |
| `error` | `{code, message}` | ทั้งหมด |
