# Feature: Ingestion · ไฟล์ของผู้ใช้ → หัวข้อ + ดาว

| | |
|---|---|
| Area | scope |
| Requirements | SM-01, SM-03, SM-04, CM-06, CM-07, AI-08, SA-06 |
| Owner | Jam |
| Reviewer | Jam · Junior ดูส่วน DB และตัวรัน job (§10) |
| Status | approved 2026-11-13 (Jam · §10 ข้อ 1–5 ตามข้อเสนอ · ข้อ 1–3 เป็นของ Junior ใช้ข้อเสนอไปก่อนเพื่อให้ทัน demo · Junior ดูย้อนหลัง) |
| Related system spec | ai-orchestration.md §2.3.2–2.3.9 · api.md v1.11 `Ingestion` · data-model.md รูป 2 · `compute-importance.md` · PoC `specs/poc/reports/P3.md` · `docs/team/sprint-checklists.md` ⭐ demo ขั้น 4 |

## 1. Context

demo end to end (23 พ.ย.) ต้องให้ไฟล์ที่ผู้ใช้อัปโหลดกลายเป็นหัวข้อพร้อมดาวจริงในหน้า scope · pipeline พิสูจน์แล้วใน PoC P3 (`poc/P3/` · ★★★ ตรง 10/12 = 83% · ≤ 3 นาทีต่อไฟล์) แต่เป็นสคริปต์ที่อ่าน/เขียนไฟล์ในเครื่อง · feature นี้ย้าย pipeline เข้า `apps/api` เป็นงานเบื้องหลังที่อ่านไฟล์จาก Storage และเขียนผลลง DB ของ tenant นั้น · endpoint ของไฟล์ (`/materials…`) เป็นของ Junior (demo ขั้น 3) และเรียกเข้ามาผ่าน 2 ฟังก์ชันใน §2.1 · หน้า S11 อ่านความคืบหน้าจาก `GET /exam-preps/{id}/ingestion` (§2.6)

## 2. Behavior

### 2.1 ทางเข้า (ผู้เรียกคือ endpoint ของ Junior)

1. `classify_material(material_id)` · เรียกหลัง `POST /materials/{id}/uploaded` (ai-orchestration §2.3.8 ข้อ 3) · ทำขั้น A1 (§2.2) แล้วจบ
2. `start_ingestion(exam_prep_id)` · เรียกหลัง `POST /exam-preps/{id}/materials/confirm` (ข้อ 5) · ไฟล์ทุกไฟล์ของ prep ที่ `kind_confirmed = true` และ `status = 'confirmed'` เข้าคิว · คืนทันที (job รันเบื้องหลัง · §2.7) · endpoint ตอบ `202` เอง
3. `retry_material(material_id)` · สำหรับ `POST /materials/{id}/retry` (api.md) · ล้มตอน classify → ทำ §2.2 ใหม่ · ล้มตอน ingest → ทำ §2.3 ของไฟล์นั้นใหม่ แล้วทำ §2.4 ถ้าทุกไฟล์พร้อม
4. ทุกทางเข้าทำงานด้วย service role และใส่ `tenant_id` ของ prep เองทุกแถว (apps/api/CLAUDE.md "Database" · ไม่มี JWT ของผู้ใช้ในงานเบื้องหลัง)

### 2.2 ขั้น A1 · classify (CM-06)

1. input: ชื่อไฟล์ที่ทำความสะอาดแล้ว (§2.5 ข้อ 1) · ข้อความ text layer ของ `ingestion.classify_pages` หน้าแรกในรูป `[p.N]` (ไม่เรียก vision ตอน classify เพื่อให้เร็วและถูก · ไฟล์สแกนจึงพึ่งชื่อไฟล์และ note เป็นหลัก · แก้ 13 พ.ย. ตอนเขียน test) · `user_note` (ไม่มี → `ไม่มี`)
2. `classify_material/v1` คืน `{kind, confidence, other_instructor, reason}` · `kind` ∈ `sheet | slides | past_exam | notes | other` · `other_instructor` = note หรือเนื้อหาบอกว่าข้อสอบชุดนี้เป็นของอาจารย์คนละคน
3. code เขียน `materials.kind`, `kind_confidence = confidence`, `relevance_weight` = `stars.weight_other_instructor` ถ้า `kind = past_exam` และ `other_instructor` ไม่งั้น `stars.weight_same_instructor` (AI ไม่ให้ตัวเลขน้ำหนักเอง · CLAUDE.md ข้อ 1) · `status = 'classified'` · ผู้ใช้ยืนยัน/แก้ใน S10 (ของ Junior + May)
4. AI ล้มหลัง retry ของ gateway → `status = 'failed'`, `error` = ข้อความสั้นสำหรับผู้ใช้ (§2.6 `error`)

### 2.3 ขั้นรายไฟล์ · อ่าน → ตัดรายข้อ → chunk → embed (SM-01, AI-08)

ลำดับต่อไฟล์ (เขียนแถว `ingestion_jobs` ของ stage นั้นเป็น `running` ก่อนเริ่ม และ `done` เมื่อจบ · `materials.status = 'ingesting'` ตั้งแต่ขั้นแรกจนจบ):

1. **extract** · PDF: อ่าน text layer ทีละหน้าด้วย PyMuPDF · คำนวณสัดส่วนตัวอักษรไทย = ไทย ÷ (ไทย + ละติน) ของทั้งไฟล์ (P3 `thai_share`) · ≥ `ingestion.min_thai_share` → ใช้ text layer (`extract_method = 'text_layer'`) · น้อยกว่า → render ทุกหน้าที่ `ingestion.render_dpi` แล้วเรียก `vision_extract_pages` ครั้งเดียวทั้งไฟล์ (A2b · `extract_method = 'vision'`) · จำนวนหน้าที่คืนต้องเท่าที่ส่ง ไม่งั้นไฟล์ล้ม · ไฟล์รูปเดี่ยว: `vision_extract` (A2) เป็นหน้า 1 · เขียน `material_pages` ทุกหน้า (`page_no` เริ่ม 1 ตามหน้า PDF)
2. **split_exam** (เฉพาะ `kind = past_exam`) · `split_past_exam` (A4) กับข้อความทุกหน้าในรูป `[p.N]` · เขียน `past_exam_questions` (`q_no`, `page_no`, `text`) ยังไม่มี `topic_id`
3. **chunk** (ไฟล์ที่ไม่ใช่ข้อสอบเก่า) · ตัดตามกฎของ P3 (`poc/P3/chunking.py`): ต่อหน้าตามลำดับจนถึง `ingestion.chunk_min_tokens` ไม่เกิน `ingestion.chunk_max_tokens` และไม่คร่อมเกิน `ingestion.chunk_max_pages` หน้า · หน้าที่ยาวเกินตัดที่บรรทัด · นับ token ภาษาไทยที่ `ingestion.thai_chars_per_token` ตัวต่อ token (ai-orchestration §2.3.3) · `content_hash` = sha256 ของ `text`
4. **embed** · `gateway.embed` ทีละ `embedding.batch_size` · เขียน `chunks` (`page_from`, `page_to`, `text`, `content_hash`, `embedding`) **text อยู่คู่ vector ทุกแถว (AI-08)** · ขนาด vector ผิด → gateway error → ไฟล์ล้ม
5. จบครบ → `materials.status = 'ready'` · ขั้นใดล้ม (AI ล้มหลัง retry, schema ผิดหลัง retry, PDF เปิดไม่ได้, Storage อ่านไม่ได้) → แถวของ stage นั้น `failed` + `error` · `materials.status = 'failed'`, `materials.error` = ข้อความสั้นตามชนิด (§2.6) · **ไฟล์อื่นของ prep ทำต่อ**
6. **รันซ้ำได้ (ai-orchestration §2.3.9 ข้อ 6):** ก่อนเริ่มขั้นรายไฟล์ ลบ `material_pages`, `chunks`, `past_exam_questions` เดิมของไฟล์นั้น

### 2.4 ขั้นรวมของ prep · หัวข้อ → map ข้อสอบ → ดาว (SM-01, SM-03, SM-04)

เริ่มเมื่อทุกไฟล์ที่ยืนยันแล้วของ prep เป็น `ready` (ไฟล์ `failed` ที่ผู้ใช้ยังไม่ตัดสิน → **ยังไม่เริ่ม** · api.md รอตัดสิน ข้อ 2 · ผู้ใช้ลองใหม่หรือลบไฟล์แล้วจึงเริ่ม) และต้องมีชีทอย่างน้อย 1 ไฟล์ (ไม่มี → ขั้นรวมล้ม · `error` "ยังไม่มีชีทหรือสไลด์ให้หาหัวข้อ")

1. **A5** `extract_topics_local/v2` ทีละไฟล์ที่ไม่ใช่ข้อสอบเก่า · `file_name` = ชื่อที่ทำความสะอาดแล้ว · `material_kind` = `materials.kind` · `pages_text` = ทุกหน้าในรูป `[p.N]`
2. **A6** `merge_topics/v2` ครั้งเดียว · `files_topics` = ผล A5 ทุกไฟล์ โดย `file` ของแต่ละไฟล์เป็น **key สั้น `f1`, `f2`, …** ตามลำดับเวลาสร้างไฟล์ และ `pages` เป็น `<key>:<start>-<end>` (แบบ P3) · `user_notes` = `user_note` ของทุกไฟล์ที่ไม่ว่าง บรรทัดละไฟล์ `<key>: <note>` · ไม่มีเลย → `ไม่มี`
3. **A7** `map_questions/v1` ทีละข้อสอบเก่า · `topics` = id, ชื่อ, skills ของผล A6 · `questions` = `{q_id: "<key>:<q_no>", text}` · q_id ที่ส่งไปแต่ไม่กลับมา → ข้อนั้นไม่มี `topic_id` และ `map_note` เป็น null (log ไว้)
4. **เขียนผล (code):** เขียนเมื่อผล AI ของ A5, A6, A7 ครบแล้วเท่านั้น (AI ล้ม → ไม่แตะ DB) · Supabase REST ไม่มี transaction จึงเขียนหัวข้อชุดใหม่ก่อน แล้วค่อยลบชุดเดิม · เขียนล้มกลางทาง → ลบแถวใหม่ที่เขียนไปแล้ว ชุดเดิมยังอยู่ (แก้ 13 พ.ย. ตอนออกแบบ test):
   - `topics`: 1 แถวต่อหัวข้อของ A6 · `name` · `order_index` = `order` · `prereq_ids` = id ใหม่ของหัวข้อใน `prereqs` · `origin = 'doc'` · `status = 'excluded'` ถ้า `excluded_by_note` ไม่งั้น `'draft'`
   - `topic_skills`: 1 แถวต่อ skill · `common_mistakes` = ของ A6 · `exam_freq` = จำนวนข้อสอบที่ A7 map มาที่ skill นั้น
   - `topic_sources`: 1 แถวต่อช่วงใน `sources` · key → `material_id` · source ที่ key ไม่รู้จัก หรือ `page_from` > จำนวนหน้าของไฟล์ → **ไม่เขียนแถวนั้น** (log) · `page_to` เกินจำนวนหน้า → ตัดเหลือหน้าสุดท้าย
   - `past_exam_questions`: `topic_id`, `skill_id`, `trap`, `map_note` = `note` ของ A7 (ทุกข้อ · `0003`)
   - สุดท้าย ลบหัวข้อชุดเดิมของ prep ที่ `origin = 'doc'` และ `status` เป็น `draft` หรือ `excluded` (รันซ้ำก่อนยืนยัน · §2.4 ข้อ 6)
5. **ดาว** · `compute_importance` (`domain/stars.py`) ด้วย input ตาม `compute-importance.md` §2 "ผู้เรียก": `excluded` = `status = 'excluded'` · `page_count` = จำนวนหน้าที่ไม่ซ้ำของ `topic_sources` ของหัวข้อ · `exams` = ข้อสอบเก่ากับ `relevance_weight` · `appearances` = `(topic_id, material_id)` จาก `past_exam_questions` · เขียน `importance`, `signal_r`, `importance_reason`, `importance_source = 'computed'`
6. รันซ้ำ (เช่น retry หลังไฟล์ล้ม) ก่อนยืนยัน scope ได้หัวข้อชุดใหม่แทนชุดเดิม ไม่ซ้ำ · หลังยืนยันแล้ว (เพิ่มไฟล์ทีหลัง CM-05) ไม่อยู่ใน feature นี้ (§9)
7. ล้ม (A5/A6/A7 ล้มหลัง retry หรือเขียน DB ไม่ได้) → ขั้นรวม `failed` + `error` · ไม่มีหัวข้อครึ่งชุด (ข้อ 4)

### 2.5 ข้อความจากผู้ใช้และจากไฟล์

1. **ชื่อไฟล์** (ai-orchestration §2.3.3 · Jam 2026-11-07): ก่อนเข้า prompt ใดๆ แทนตัวขึ้นบรรทัดและตัวควบคุม (Unicode category `Cc`, `Cf`, `Zl`, `Zp`) ด้วยช่องว่าง แล้วยุบช่องว่างซ้ำ · ยาวเกิน `guards.max_attachment_name_chars` (นับ grapheme) → ตัดแบบเก็บนามสกุลเหมือน `messages.attachment_name` (data-model กฎทั่วไป)
2. ข้อความจากไฟล์และ `user_note` เข้า prompt ใน data block เสมอ (ทุก prompt ของ flow นี้ทำอยู่แล้ว · CLAUDE.md ข้อ 8)

### 2.6 `GET /exam-preps/{id}/ingestion` จริง (CM-07)

มี token → อ่าน DB ด้วย JWT ของผู้ใช้ (RLS) แล้วตอบตาม `Ingestion` ของ api.md · ไม่มี token (`AUTH_REQUIRED=false`) → stub เดิม (`X-Stub`)

1. prep ไม่มีหรือเป็นของ tenant อื่น → `404 not_found` · DB ล่ม → `503 db_unavailable` (แบบ #121, #123)
2. `files` ตาม api.md · `status` ของไฟล์ = รวมจากแถว `ingestion_jobs` ของไฟล์: มี `failed` → `failed` · มี `running` → `running` · ครบทุก stage `done` → `done` · ไม่งั้น `queued`
3. `detail`: `running` → ข้อความของ stage ("กำลังอ่าน", "กำลังแยกรายข้อ", "กำลังเตรียมเนื้อหา") · `done` → "{n} หน้า" (+ " · {m} ข้อ" สำหรับข้อสอบเก่า) · อื่นๆ → null
4. `error` (เมื่อ `failed`): ข้อความสั้นที่ไม่มีรายละเอียดภายใน · PDF เปิดไม่ได้ → "เปิดไฟล์นี้ไม่ได้" · AI หรือ Storage ล้ม → "อ่านไฟล์นี้ไม่สำเร็จ ลองใหม่ได้" · ข้อความจริงอยู่ใน log
5. `steps` ตาม label ของ api.md: "อ่านสิ่งที่คุณเขียนกำกับไว้" (`done` เมื่อทุกไฟล์ `done`) · "หาหัวข้อและลำดับการเรียน" (สถานะของ stage `topics` ของ prep) · "เทียบกับข้อสอบเก่า {n} ชุด" (stage `stars` · ไม่มีข้อสอบเก่าก็ไม่มีขั้นนี้)
6. `scope_ready` = ขั้นรวมทุกขั้น `done` และไม่มีไฟล์ที่ยืนยันแล้วซึ่ง `confirmed`, `ingesting` หรือ `failed`

### 2.7 ตัวรัน job (สำหรับ demo ในเครื่อง)

1. `start_ingestion` สร้าง `asyncio` task ใน process ของ API (เก็บ reference ไว้ไม่ให้ถูกเก็บขยะ) · 1 task ต่อ prep · ไฟล์ทำทีละไฟล์ตามลำดับเวลาสร้าง (เวลาต่อไฟล์คาดเดาได้ และไม่ชน quota ของ Vertex)
2. เรียก `start_ingestion` ซ้ำขณะ task ของ prep เดิมยังรัน → ไม่สร้าง task ใหม่ (ไฟล์ใหม่ที่ยืนยันทีหลังเข้าคิวของ task เดิมหลังไฟล์ที่ค้าง)
3. API ปิดกลางทาง → แถวที่ค้าง `running` ไม่มีใครทำต่อ · ไม่อยู่ใน feature นี้ (§10 ข้อ 2 · ตัวรันจริงบน Cloud Run เป็นของ Junior ใน S5)

### 2.8 สิ่งที่ code ตัดสิน · สิ่งที่ AI ทำ

AI (A1, A2/A2b, A4, A5, A6, A7) ให้แค่ข้อความ หัวข้อ และการจับคู่ในรูป schema ที่ตรวจแล้ว (AI-05) · code ตัดสิน: วิธีอ่าน, chunk, น้ำหนักข้อสอบ, การแปลง key/id, การตัด source ที่ผิด, ดาว, สถานะ · AI ไม่เขียน DB (CLAUDE.md ข้อ 2)

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | `materials` ของ prep (`kind_confirmed`, `kind`, `storage_path`, `file_name`, `user_note`, `relevance_weight`) + ไฟล์ใน Storage | ชีท 4 ไฟล์ + ข้อสอบ 2 ไฟล์ของ MTH10101 (`evals/topics/mth10101/raw/`) |
| Output (DB) | `material_pages`, `chunks`, `past_exam_questions`, `ingestion_jobs`, `topics`, `topic_skills`, `topic_sources` · `materials.status` | หัวข้อ "ลิมิต" ★★★ `signal_r` 1.0 · source `sheet-02.pdf` หน้า 3–9 |
| Output (API) | `Ingestion` ของ api.md | `{"scope_ready": false, "files": [{"material_id": "…", "file_name": "sheet-01.pdf", "status": "done", "detail": "14 หน้า", "error": null}], "steps": [{"label": "หาหัวข้อและลำดับการเรียน", "status": "running"}]}` |

## 4. Acceptance criteria

ทุกข้อใช้ fake provider (embed ปลอมคืน vector ยาว `embedding.dimensions`) · unit ใช้ repository ในหน่วยความจำ · ข้อที่บอก "DB" เป็น integration บน Supabase ในเครื่อง · ค่าตัวเลขอ่านจาก config ของ test

**ขั้นรายไฟล์**

- **AC-1 (SM-01, AI-08)** Given ชีท PDF ที่มี text layer ภาษาไทย 3 หน้า When ingest Then `material_pages` 3 แถว `text_layer` · `chunks` ทุกแถวมี `text`, `content_hash` = sha256(text) และ vector ยาว `embedding.dimensions` · ไม่เรียก `vision_extract_pages` · `materials.status = 'ready'`
- **AC-2 (SM-01)** Given PDF ที่ text layer เป็นภาษาอังกฤษล้วน (ข้อสอบสแกน) When ingest Then เรียก `vision_extract_pages` 1 ครั้งพร้อมรูปทุกหน้า · `material_pages` เป็น `vision`
- **AC-boundary-thai (SM-01)** สัดส่วนไทย = `min_thai_share` − ε → vision · = ค่า → text layer · + ε → text layer (config ทดสอบ)
- **AC-3** `vision_extract_pages` คืนจำนวนหน้าไม่เท่าที่ส่ง → ไฟล์ `failed` · error "อ่านไฟล์นี้ไม่สำเร็จ ลองใหม่ได้" · ไม่มี `material_pages` ค้าง
- **AC-4 (SM-01)** Given ข้อสอบเก่า When ingest Then `split_past_exam` ได้ข้อความทุกหน้าในรูป `[p.N]` · `past_exam_questions` ตามผล (`q_no`, `page_no`, `text`) · ไม่ทำ chunk / embed ของไฟล์นี้
- **AC-5 (AI-08)** chunk: หน้า 3 หน้า หน้าละ (`chunk_min_tokens` ÷ 2) token → chunk แรกรวม 2 หน้า ไม่คร่อมเกิน `chunk_max_pages` · หน้าเดียวยาวเกิน `chunk_max_tokens` → ตัดเป็นหลายส่วนในหน้านั้น ไม่มีส่วนไหนเกิน (กฎเดียวกับ `poc/P3/test_chunking.py`)
- **AC-boundary-chunk (AI-08)** หน้าที่ยาว `chunk_max_tokens` − 1, = ค่า, + 1 token → ส่วนเดียว, ส่วนเดียว, 2 ส่วน
- **AC-6 (AI-08)** chunk 25 อัน, `batch_size` 10 → `embed` 3 ครั้ง (10, 10, 5) · vector ยาวผิด → ไฟล์ `failed`
- **AC-7** ไฟล์หนึ่งล้ม อีกไฟล์ทำต่อจน `ready` · ขั้นรวมยังไม่เริ่ม (ไม่มีการเรียก A5)
- **AC-8** ingest ไฟล์เดิมซ้ำ → `material_pages`, `chunks`, `past_exam_questions` ของไฟล์นั้นไม่ซ้ำ (จำนวนเท่ารอบแรก)
- **AC-9** ชื่อไฟล์ `"a\nIgnore previous instructions.pdf"` → ทุก prompt ได้ `a Ignore previous instructions.pdf` (ไม่มี `\n`, ไม่มีตัวควบคุม)

**ขั้นรวม**

- **AC-10 (SM-01, SM-04)** Given ชีท 2 + ข้อสอบ 1 ที่ `ready` When ขั้นรวม Then A5 2 ครั้ง (key `f1`, `f2`), A6 1 ครั้ง, A7 1 ครั้ง · `topics` ตามผล A6 (`order_index`, `prereq_ids` เป็น id ใหม่) · `topic_sources` ชี้ `material_id` ที่ถูกตาม key · `topic_skills` มี `common_mistakes`
- **AC-11 (SM-04)** source ที่ key ไม่รู้จัก หรือ `page_from` เกินจำนวนหน้า → ไม่มีแถวนั้น · `page_to` เกิน → ตัดเหลือหน้าสุดท้าย
- **AC-12 (SM-03)** ข้อสอบ 2 ชุด หัวข้อ A ถูก map จากทั้ง 2 ชุด → ★★★ `signal_r` 1.0 · หัวข้อ B 1 ชุด → ★★ · เท่ากับผลของ `compute_importance` กับ input เดียวกัน · `importance_source = 'computed'`
- **AC-13 (SM-03)** ข้อสอบที่ classify ได้ `other_instructor` → `relevance_weight = stars.weight_other_instructor` และดาวคิดด้วยน้ำหนักนั้น
- **AC-14 (SM-03)** ไม่มีข้อสอบเก่า → ไม่เรียก A7 · ดาวแบบ page terciles · `steps` ไม่มีขั้น "เทียบกับข้อสอบเก่า"
- **AC-15** A6 บอก `excluded_by_note` → หัวข้อ `status = 'excluded'`, ★ 0
- **AC-16** A7 คืน `topic_id` null พร้อม `note` → `past_exam_questions.topic_id` null, `map_note` = note · q_id ที่หายจากผล → `map_note` null · `topic_skills.exam_freq` นับเฉพาะข้อที่ map มา
- **AC-17** `user_note` 2 ไฟล์ → A6 `user_notes` = `f1: …` / `f2: …` · ไม่มี note → `ไม่มี`
- **AC-18** ขั้นรวมรันซ้ำก่อนยืนยัน → หัวข้อเดิม (`origin = 'doc'`, `draft`) หายไป · หัวข้อใหม่ไม่ซ้ำ · หัวข้อ `origin = 'user'` ยังอยู่
- **AC-19** A6 ล้มหลัง retry → ไม่มีหัวข้อใหม่ในตาราง (หัวข้อเดิมยังอยู่) · step "หาหัวข้อ…" `failed` · `scope_ready = false` · เขียน `topic_sources` ล้มกลางทาง → หัวข้อใหม่ที่เขียนไปแล้วถูกลบ หัวข้อเดิมยังอยู่
- **AC-20** ไม่มีชีทเลย (ข้อสอบเก่าอย่างเดียว) → ขั้นรวม `failed` · ไม่เรียก A5/A6

**classify**

- **AC-21 (CM-06)** A1 คืน `{kind: "past_exam", confidence: 0.82, other_instructor: false}` → `materials.kind = past_exam`, `kind_confidence = 0.82`, `relevance_weight = weight_same_instructor`, `status = 'classified'` · input มีชื่อไฟล์ที่ทำความสะอาดแล้ว, ข้อความ `classify_pages` หน้าแรก และ note
- **AC-22 (CM-06)** A1 ล้ม → `status = 'failed'` + error

**API**

- **AC-23 (CM-07)** มี token · ไฟล์ 3 ไฟล์ (done, running, failed) → `files` เรียงตามเวลาสร้าง สถานะตามแถวของ `ingestion_jobs` · `detail` "14 หน้า" / "กำลังแยกรายข้อ" / null · `error` ของไฟล์ที่ล้มเป็นข้อความสั้น ไม่มี stack · `scope_ready = false`
- **AC-24 (CM-07)** ทุกไฟล์ `done` + ขั้นรวม `done` → `scope_ready = true` · `steps` ทุกตัว `done`
- **AC-25 (CM-07)** ไม่มีไฟล์ที่ยืนยัน → `200` · `files: []`
- **AC-26** ไม่มี token → stub เดิม (`X-Stub: true`) · DB ล่ม → `503 db_unavailable`
- **AC-tenant (SA-06 · DB)** prep ของ tenant A ingest จนจบ → ทุกแถวที่เขียนมี `tenant_id` = A · user ของ tenant B: `GET /exam-preps/{A-prep}/ingestion` → `404` · query `topics`, `chunks`, `past_exam_questions` ด้วย JWT ของ B ได้ 0 แถว

**ตัวรัน**

- **AC-27** `start_ingestion` คืนก่อน job จบ · เรียกซ้ำระหว่างรัน → task เดิม (ไม่ ingest ซ้ำ)

## 5. Data changes

| Table | Column / index / policy | เพิ่ม / แก้ |
|---|---|---|
| `ingestion_jobs` | `material_id` null ได้ + `exam_prep_id uuid not null references exam_preps(id) on delete cascade` · แถวของขั้นรวม (`topics`, `stars`) มี `material_id` null · RLS เดิม | **แก้ · migration `0005` · รอ Junior** (api.md รอตัดสิน ข้อ 1 เสนอไว้แล้ว · §10 ข้อ 1) |
| `materials` | ไม่เปลี่ยน · ใช้ `status`, `error`, `kind`, `kind_confidence`, `relevance_weight` ที่มี | — |
| `material_pages`, `chunks`, `past_exam_questions`, `topics`, `topic_skills`, `topic_sources` | ไม่เปลี่ยน · เขียนครั้งแรก | — |

## 6. API / SSE changes

| Endpoint / event | Request | Response |
|---|---|---|
| `GET /exam-preps/{id}/ingestion` | ไม่เปลี่ยน | ไม่เปลี่ยนรูปแบบ (api.md `Ingestion`) · มี token → ข้อมูลจริง · เพิ่ม `404`, `503 db_unavailable` (แบบ endpoint อื่นของ #121, #123) |
| `/materials…` (Junior) | — | เรียก `classify_material`, `start_ingestion`, `retry_material` (§2.1) |

## 7. AI calls

ทุก call ผ่าน gateway · config เดิมใน `config/ai.yaml` (วัดแล้วใน P3 บน Vertex)

| Purpose | Tier | Output schema | Prompt file |
|---|---|---|---|
| `classify_material` (A1 · **ใหม่**) | small | `ClassifyMaterialResult {kind, confidence, other_instructor, reason}` (**แก้จาก** `relevance_weight` ใน ai-orchestration §2.3.7) | `prompts/classify_material/v1.md` (ใหม่ · input `file_name`, `pages_text`, `user_note`) |
| `vision_extract_pages` (A2b) | vision | `VisionExtractPagesResult` | `vision_extract_pages/v1` |
| `vision_extract` (A2) | vision | `VisionExtractResult` | `vision_extract/v1` |
| `split_past_exam` (A4) | small | `SplitPastExamResult` | `split_past_exam/v1` |
| `extract_topics_local` (A5) | mid | `ExtractTopicsLocalResult` | `extract_topics_local/v2` |
| `merge_topics` (A6) | main | `MergeTopicsResult` | `merge_topics/v2` |
| `map_questions` (A7) | small | `MapQuestionsResult` | `map_questions/v1` |
| `embed` (A3) | embed | vector | — |

## 8. Test plan

อ่าน PDF ผ่าน interface `Documents` (`pages_text`, `page_images`) · unit test ใช้ตัวปลอมที่คืนข้อความรายหน้า เพราะ PDF ภาษาไทยต้องมี font ไทยซึ่งเครื่อง CI ไม่มี · ตัวจริง (`PyMuPdfDocuments`) มี test ของตัวเองกับ PDF ภาษาอังกฤษ · ภาษาไทยจริงทดสอบในขั้น 4 ของ worklog (MTH10101)

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/unit/test_ingestion_domain.py` (สัดส่วนไทย, chunk, ชื่อไฟล์, key → material, source ที่ผิด, สถานะรวมของไฟล์และ step) | unit (pure) | AC-boundary-thai, AC-5, AC-boundary-chunk, AC-9, AC-11, AC-23–25 (ส่วนคิดสถานะ) |
| `tests/unit/test_ingestion_pipeline.py` (fake provider + repository ในหน่วยความจำ + PDF เล็กที่สร้างใน test ด้วย PyMuPDF) | unit | AC-1–4, AC-6–8, AC-10, AC-12–22, AC-27 |
| `tests/unit/test_ingestion_api.py` (dependency override) | unit | AC-23–26 |
| `tests/integration/test_ingestion_db.py` (Supabase ในเครื่อง · 2 tenants) | integration | AC-tenant, AC-18 |
| รันจริงบน Vertex กับ MTH10101 เทียบ P3 (`poc/P3/score.py` อ่านผลจาก DB) | eval (มือ · ขั้น 4 ของ worklog) | เป้า: ★★★ ≥ 10/12 · ≤ 3 นาทีต่อไฟล์ |

## 9. Out of scope

- endpoint ของไฟล์ (`/materials…`), signed upload URL, bucket + policy (Junior · demo ขั้น 3) · feature นี้อ่านไฟล์ผ่าน interface `MaterialFiles.read(storage_path)` ที่มีตัวจริงอ่าน Supabase Storage ด้วย service role และตัวในเครื่องอ่านโฟลเดอร์
- `topic_chunks` (เลือก chunk ของหัวข้อด้วย vector similarity · ai-orchestration §2.3.4 ขั้น 5d) · ใช้ตอน grounding ในห้องติว (SM-11 · S6) · chunk + vector พร้อมแล้วจาก feature นี้
- PPTX, DOCX (ai-orchestration §2.3.3) · demo ใช้ PDF และรูป
- เพิ่มไฟล์หลังยืนยัน scope (CM-05), ลบไฟล์ที่ ready แล้ว (CM-10 · api.md รอตัดสิน ข้อ 3), แก้ scope ผ่านแชท (SM-06)
- ลองใหม่ของขั้นรวม (api.md รอตัดสิน ข้อ 8) · ตัวรัน job ที่ทนต่อ API ปิด / หลาย instance (Cloud Run · S5)

## 10. Open questions

**ตัดสิน 13 พ.ย. (Jam):** ข้อ 1–5 ตามข้อเสนอ · ข้อ 1–3 เป็นการตัดสินของ Junior (DB, deploy · roles.md) ใช้ข้อเสนอไปก่อนเพื่อให้ทัน demo 23 พ.ย. แล้ว Junior ดูย้อนหลัง · migration `0005` ขึ้นแค่ Supabase ในเครื่องด้วย `db reset` · ขึ้น dev/staging เมื่อ Junior ok

1. **(Junior) migration `0005`:** `ingestion_jobs.material_id` null ได้ + `exam_prep_id` สำหรับแถวของขั้นรวม · ข้อเสนอเดิมของ api.md รอตัดสิน ข้อ 1 · Junior ok แล้ว Jam เขียน migration ใน PR นี้ได้ (demo ในเครื่องใช้ `db reset` · ขึ้น dev/staging เป็นของ Junior) · ทางสำรองถ้าไม่ ok: เก็บสถานะขั้นรวมไว้ในแถว stage `topics` / `stars` ของทุกไฟล์
2. **(Junior) ตัวรัน job:** demo ใช้ `asyncio` task ใน process ของ API (§2.7) · บน Cloud Run ต้องเปิด CPU ตลอดเวลา หรือแยกเป็น Cloud Run Job / Cloud Tasks · ตัดสินใน S5 ตอนทำ journey บน staging
3. **(Junior) `MaterialFiles` บน Storage:** ใครเขียนตัวที่อ่าน Supabase Storage · ข้อเสนอ: Jam เขียนใน PR นี้ (service role อ่าน bucket ของ demo ขั้น 3) แล้ว Junior ดูย้อนหลัง · ชื่อ bucket ตามที่ Junior ตั้ง
4. **(Jam · prompt) A1 คืน `other_instructor` แทน `relevance_weight`:** ให้ code เลือกน้ำหนักจาก config (CLAUDE.md ข้อ 1, 5) · แก้ตาราง ai-orchestration §2.3.7 (§11)
5. **(Jam) `material_kind` ของ A5 = `materials.kind`** (`sheet`, `slides`, `notes`, `other`) · P3 ส่ง `lecture` / `exercise` ตามที่รู้จากชื่อไฟล์ · kind ใน DB ไม่มี "แบบฝึกหัด" · ข้อเสนอ: ส่ง `materials.kind` ตรงๆ แล้วดูผลในขั้น 4 ของ worklog (เทียบ P3) · ถ้าแย่ลงค่อยเพิ่มค่า `exercise` (migration) หรือให้ A1 บอกว่าเป็นแบบฝึกหัด
6. **ไฟล์ `failed` บล็อกขั้นรวม** จนผู้ใช้ลองใหม่หรือลบ (api.md รอตัดสิน ข้อ 2 · ข้อเสนอเดิม) · ใน demo ไม่ควรเกิด · ถ้าเกิดตอนอัดใช้ retry

## 11. Spec changes needed

| ไฟล์ | แก้อะไร | ใคร |
|---|---|---|
| `config/ai.yaml` (ไฟล์กลาง · ถามก่อน) | section ใหม่ `ingestion:` · `min_thai_share: 0.3` [C] (P3: ข้อสอบสแกน 0.0, ชีท > 0.5) · `render_dpi: 150` [C] (P3) · `classify_pages: 3` [C] (ai-orchestration §2.3.2 ขั้น 2) · `chunk_min_tokens: 400`, `chunk_max_tokens: 800`, `chunk_max_pages: 2` (ai-orchestration §2.3.3 · P3b) · `thai_chars_per_token: 1.7` [C] (P3b วัด 1.47–1.82) | Jam · PR นี้ |
| `specs/system/ai-orchestration.md` §2.3.7 | A1 output `{kind, confidence, other_instructor, reason}` · ตัวเลขใน §2.3.3 ชี้ไป `config/ai.yaml` → `ingestion` | Jam · PR นี้ |
| `specs/system/api.md` (ไฟล์กลาง · ถามก่อน) | `GET /exam-preps/{id}/ingestion`: มี token อ่าน DB · `404`, `503 db_unavailable` · ข้อความของ `detail` / `error` (§2.6) · รอตัดสิน ข้อ 1 ตามผล §10 ข้อ 1 | Jam · PR นี้ · Junior ดูย้อนหลัง |
| `specs/system/data-model.md` | `0005` (ถ้า Junior ok) | Jam · PR นี้ |
| `prompts/classify_material/v1.md` | prompt ใหม่ | Jam · PR นี้ |
