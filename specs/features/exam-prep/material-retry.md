# Feature: ปุ่ม "ลองใหม่" ของไฟล์ที่ล้ม · `POST /materials/{id}/retry` ทางจริง

| | |
|---|---|
| Area | scope (flow 2.3 · S10–S11) |
| Requirements | CM-07, SA-06, AI-04 |
| Owner | Junior |
| Reviewer | Junior · Jam (ใช้ `IngestionRunner` ของ ingestion · ไม่แก้ไฟล์ของ Jam) · May (ปุ่มในแถว S10/S11 · `upload-page.md`) |
| Status | draft |
| Related system spec | `api.md` `POST /materials/{id}/retry` (UC-02 E5 · `Material`) · `materials-db.md` §2.1 (ทางมี/ไม่มี token), §2.4 ข้อ 6 (เริ่มงานเบื้องหลังใต้ `ai_call_context`), §9 · `ingestion.md` §2.1 ข้อ 3, §2.2 ข้อ 5, §2.3 ข้อ 5–6, §2.4 · `ai-calls-log.md` §2.1 · `0001_init.sql` `materials`, policy `tenant_rows` · `0009` trigger ของ `materials` |

## 1. Context

ไฟล์ที่ AI อ่านไม่สำเร็จจบที่ `failed` + "อ่านไฟล์นี้ไม่สำเร็จ ลองใหม่ได้" ตามที่ `ingestion.md` §2.2 ข้อ 5 รับประกัน แต่ `POST /materials/{id}/retry` ยังเป็น stub (`materials-db.md` §2.1 · §9) จึงไม่มีทางลองใหม่จริงนอกจากรัน script · เกิดแล้ว 3 ครั้งในการซ้อม journey ครั้งล่าสุดคือ 19 พ.ย. (`midterm-2559-1.pdf` ถูกตัดที่ `max_tokens` 300 · #170) · feature นี้ทำ endpoint ให้ใช้ DB จริงด้วย JWT ของผู้ใช้ แล้วสั่ง `IngestionRunner` ที่มีอยู่ให้ทำขั้นที่ล้มใหม่ · ปุ่มในแถวของ S10/S11 เป็นงานของ May (§9)

## 2. Behavior

### 2.1 เลือกทางตาม token

ตารางเดียวกับ `materials-db.md` §2.1: มี token ที่ถูก → **ทางจริง** (§2.2) ไม่มี `X-Stub` · token ผิด → `401 invalid_token` · ไม่มี token + `AUTH_REQUIRED=true` → `401 missing_token` · ไม่มี token + `AUTH_REQUIRED=false` → **stub เดิม** + `X-Stub: true` ไม่แตะ DB และไม่เริ่มงาน

### 2.2 ทางจริง

1. path `id` ไม่ใช่ uuid → `422 validation_error` (ตามเดิม · ตรวจก่อนแตะ DB)
2. หาแถว `materials` ผ่าน client ของผู้ใช้ (RLS) · ไม่มี หรือเป็นของ tenant อื่น → `404 not_found`
3. `status` ไม่ใช่ `failed` → `409 not_failed`
4. เลือกขั้นที่จะทำใหม่จาก `kind_confirmed` (กติกาเดียวกับ `IngestionRunner.retry` · `ingestion.md` §2.1 ข้อ 3):
   - `kind_confirmed = false` → ล้มตอน classify (S10) · สถานะใหม่ `uploaded`
   - `kind_confirmed = true` → ล้มตอน ingest (S11) · สถานะใหม่ `confirmed`
5. **update แบบมีเงื่อนไข** ผ่าน client ของผู้ใช้: `status` = สถานะใหม่, `error = null` **where `id` = id และ `status = 'failed'`** · ไม่มีแถวที่ถูก update (อีก request ชิงไปก่อน เช่นกดสองครั้ง) → `409 not_failed` และ**ไม่เริ่มงาน** · column อื่นไม่แตะ (`kind`, `kind_confidence`, `uploaded_at`, `user_note` คงเดิม) · trigger ของ `0009` อนุญาตอยู่แล้วเพราะไม่แก้ `storage_path`, `tenant_id`, `exam_prep_id`
6. หลัง update สำเร็จ เริ่มงานเบื้องหลัง**ภายใต้ `ai_call_context(tenant_id, user_id)` ของ token** (แบบ `materials-db.md` §2.4 ข้อ 6 · แถว `ai_calls` มี tenant และ user · AI-04) และ**ไม่รอ** ให้จบ · request ที่ถูกยกเลิกไม่ยกเลิกงาน:
   - สถานะใหม่ `uploaded` → `runner.classify(material_id)` (ทางเดียวกับ `/uploaded`)
   - สถานะใหม่ `confirmed` → `runner.start(exam_prep_id)` · runner หยิบไฟล์ที่ `confirmed` ทุกไฟล์ของ prep (`ingestion.md` §2.1 ข้อ 2) · ทำขั้นรายไฟล์ใหม่ตั้งแต่ต้น (§2.3 ข้อ 6 ลบผลเก่าก่อน) แล้วทำขั้นรวมเมื่อทุกไฟล์ `ready` · ถ้า runner ของ prep นั้นยังทำงานอยู่ รอบถัดไปของมันหยิบไฟล์นี้ (`ingestion.md` §2.7 · self-review #130)
   - ไม่เรียก `IngestionRunner.retry` เพราะมันรอ classify จนจบใน request และอ่านแถวซ้ำด้วย service role · ไม่แก้ `app/services/ingestion.py`
7. ตอบ `202` + `Material` ของแถวหลัง update (`status` ใหม่ · `error: null`)
8. DB ล่ม (ข้อ 2 หรือ 5) → `503 db_unavailable` และไม่เริ่มงาน
9. **ผลของงาน:** ไม่ใช่ความรับผิดชอบของ endpoint · classify จบที่ `classified` หรือ `failed` อีกครั้ง (`ingestion.md` §2.2 ข้อ 5 · ลองใหม่ได้อีกไม่จำกัดครั้ง) · ingest จบที่ `ready` หรือ `failed` · S10/S11 เห็นผลจาก poll เดิม

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | `POST /materials/{id}/retry` · ไม่มี body · `Authorization: Bearer <JWT>` | `POST /materials/6f1c…/retry` |
| Output | `202` + `Material` | `{"id": "6f1c…", "file_name": "midterm-2559-1.pdf", "status": "uploaded", "kind": null, "kind_confirmed": false, "error": null, …}` |
| Error | `{"error": {"code", "message"}}` | `404 not_found` · `409 not_failed` · `422 validation_error` · `503 db_unavailable` · `401` |

## 4. Acceptance criteria

ทุกข้อใช้ fake repo + runner ปลอมที่จดว่าถูกสั่งอะไร (แบบ `test_materials_db_api.py`) · ไม่มี AI model จริง

- **AC-1 (CM-07)** Given ไฟล์ของผู้ใช้ `failed` `kind_confirmed = false` `error` "อ่านไฟล์นี้ไม่สำเร็จ ลองใหม่ได้" When `POST /retry` ด้วย token Then `202` · body `status = "uploaded"` `error = null` · แถวใน repo เป็น `uploaded` `error` null · runner ได้ `classify(id)` 1 ครั้ง ไม่มี `start` · ไม่มี `X-Stub`
- **AC-2 (CM-07)** Given ไฟล์ `failed` `kind_confirmed = true` `kind = "past_exam"` When `POST /retry` Then `202` · `status = "confirmed"` `error = null` · `kind` คง `past_exam` · runner ได้ `start(exam_prep_id)` 1 ครั้ง ไม่มี `classify`
- **AC-3 (CM-07)** Given ไฟล์ที่ `status` เป็น `uploaded`, `classified`, `confirmed`, `ingesting`, `ready` (parametrize) When `POST /retry` Then `409 not_failed` · แถวไม่เปลี่ยน · runner ไม่ถูกสั่ง
- **AC-4 (CM-07)** Given ไฟล์ `failed` แต่ update แบบมีเงื่อนไขไม่ได้แถว (repo จำลองว่ามี request อื่นเปลี่ยนสถานะไปก่อน) When `POST /retry` Then `409 not_failed` · runner ไม่ถูกสั่ง
- **AC-5 (CM-07)** Given ไฟล์ `failed` When `POST /retry` สองครั้งติดกัน Then ครั้งแรก `202` · ครั้งที่สอง `409 not_failed` · runner ถูกสั่ง 1 ครั้งรวม
- **AC-6 (SA-06)** Given ไฟล์ของ tenant อื่น (repo ของผู้ใช้มองไม่เห็น) หรือ id ที่ไม่มี When `POST /retry` Then `404 not_found` · ไม่มีการ update · runner ไม่ถูกสั่ง
- **AC-7 (AI-04)** Given ไฟล์ `failed` ทั้งสองแบบ (parametrize classify / ingest) When `POST /retry` ด้วย token ของ user U tenant T Then ตอนสั่ง runner `ai_call_context` ปัจจุบันคือ (T, U)
- **AC-8 (CM-07)** Given DB ล่มตอนอ่านแถว หรือตอน update (parametrize) When `POST /retry` Then `503 db_unavailable` · runner ไม่ถูกสั่ง
- **AC-9 (CM-07)** Given ไม่มี token และ `AUTH_REQUIRED=false` When `POST /retry` Then ตอบแบบ stub เดิม (`202` · `X-Stub: true` · `status = "uploaded"`) · repo และ runner ไม่ถูกแตะ
- **AC-10 (CM-07)** Given `AUTH_REQUIRED=true` ไม่มี token Then `401 missing_token` · token ผิด (ทั้งสองค่าของ `AUTH_REQUIRED`) Then `401 invalid_token` · runner ไม่ถูกสั่ง
- **AC-11 (CM-07)** Given path `id` ไม่ใช่ uuid When `POST /retry` Then `422 validation_error` · repo ไม่ถูกแตะ
- **AC-12 (SA-06 · integration · Supabase local)** Given ไฟล์ `failed` ของ tenant A When user ของ tenant B เรียก `POST /retry` ผ่าน client ของตัวเอง Then `404` และแถวของ A ยัง `failed` · When user ของ A เรียก Then แถวเป็น `uploaded` (update ผ่าน RLS + trigger `0009` ได้จริง)

ไม่มี threshold ใน feature นี้ จึงไม่มี AC แบบ boundary

## 5. Data changes

ไม่มี · ใช้ `materials.status`, `error`, `kind_confirmed` ที่มีอยู่ · RLS `tenant_rows` และ trigger `0009` เดิมพอ

| Table | Column / index / policy | เพิ่ม / แก้ |
|---|---|---|
| — | — | — |

## 6. API / SSE changes

| Endpoint / event | Request | Response |
|---|---|---|
| `POST /materials/{id}/retry` | ไม่มี body (เดิม) | `202` + `Material` (เดิม) · **ทางจริงเมื่อมี token** · เพิ่ม `503 db_unavailable` ใน OpenAPI ของ endpoint นี้ (เหมือน `/uploaded`) |

รูปร่างเดิมตาม `api.md` ไม่เปลี่ยน · `pnpm gen:api` อาจเปลี่ยนแค่ response 503 ใน `api-schema.ts`

## 7. AI calls

ไม่มีใหม่ · งานที่สั่งเรียก `classify_material` (A1) หรือ purpose ของขั้นรายไฟล์และขั้นรวมตาม `ingestion.md` เดิม

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `test_CM07_retry_after_classify_failed_classifies_again` | unit | AC-1 |
| `test_CM07_retry_after_ingest_failed_queues_the_prep_again` | unit | AC-2 |
| `test_CM07_retry_of_a_file_not_failed_is_409` (parametrize 5 สถานะ) | unit | AC-3 |
| `test_CM07_retry_lost_to_another_request_is_409` | unit | AC-4 |
| `test_CM07_retry_twice_starts_the_job_once` | unit | AC-5 |
| `test_SA06_retry_of_another_tenants_file_is_404` | unit | AC-6 |
| `test_AI04_retry_starts_the_job_with_the_users_ai_context` (parametrize) | unit | AC-7 |
| `test_CM07_retry_db_down_is_503` (parametrize) | unit | AC-8 |
| `test_CM07_retry_without_token_keeps_the_stub` | unit | AC-9 |
| `test_CM07_retry_auth_errors` | unit | AC-10 |
| `test_CM07_retry_bad_id_is_422` | unit | AC-11 |
| `test_SA06_retry_of_another_tenants_file_is_404_on_supabase` | integration | AC-12 |

ไฟล์ใหม่ `tests/unit/test_material_retry_api.py` ใช้ fixture ของ `test_materials_db_api.py` · test เดิมที่ review แล้วไม่แก้

## 9. Out of scope

- ปุ่ม "ลองใหม่" ในแถวไฟล์ของ S10 (`UploadPage`) และ S11 (`ProgressPage`) และการแก้ `upload-page.md` §2 ข้อ 8 + AC-19 ("ไม่มีปุ่มลองใหม่ในแถว") · **งานของ May** (§10 ข้อ 1)
- `DELETE /materials/{id}` ("ไปต่อโดยไม่มีไฟล์นี้" · CM-10) · ยัง stub · หลังวิดีโอ
- จำกัดจำนวนครั้งที่ลองใหม่ หรือ rate limit ของ endpoint นี้
- แก้ `IngestionRunner.retry` ของ Jam (ยังใช้ไม่ได้จาก request เพราะรอ classify จนจบ · §10 ข้อ 3)

## 10. Open questions

1. **(May) ปุ่มในแถว:** `upload-page.md` §2 ข้อ 8 และ AC-19 เขียนว่า "ไม่มีปุ่มลองใหม่ในแถว" · ต้องแก้ spec และ test ที่ May review แล้ว · Junior ถาม May แล้ว (19 พ.ย.) · ถ้า May ทำไม่ทัน 20 พ.ย. Claude ทำแบบ solo หลัง May อนุมัติ
2. **(Junior) S11 เห็น `failed` ค้างชั่วครู่หลังกดลองใหม่ของไฟล์ที่ล้มตอน ingest:** สถานะรายไฟล์ใน `GET /ingestion` คำนวณจากแถว `ingestion_jobs` ไม่ใช่ `materials.status` (`file_status(f.jobs, …)`) · แถว job ที่ `failed` อยู่จนกว่า runner จะเริ่ม stage แรกของไฟล์นั้นใหม่ · ปกติ runner ว่าง (ขั้นรวมไม่เริ่มเมื่อมีไฟล์ล้ม · `ingestion.md` §2.4) จึงเริ่มทันทีในไม่กี่ ms · ถ้า runner ของ prep กำลังทำไฟล์อื่น S11 จะเห็น `failed` (ไม่มีข้อความ error เพราะ `error` เป็น null แล้ว) จนรอบถัดไป · **ข้อเสนอ:** ยอมรับในวิดีโอ · หลังวิดีโอให้ Jam ตั้งแถว job ของไฟล์เป็น `queued` ตอน retry (ingestion_jobs เขียนด้วย service role เท่านั้น)
3. **(Jam) `IngestionRunner.retry`:** ไม่มีใครเรียกหลัง feature นี้ · เก็บไว้ หรือเปลี่ยนให้ไม่รอ classify แล้วให้ router เรียกแทน (หลังวิดีโอ · ไม่ขวาง)
4. **(Junior) prep ที่ `archived`:** `/uploaded` ไม่ตรวจสถานะของ prep · feature นี้ทำตามนั้น (ลองใหม่ได้แม้ prep ถูก archive) · ข้อเสนอ: ไม่ตรวจ เหมือน `/uploaded`

## 11. Spec changes needed

- `api.md` v1.21 ย่อหน้า "ทางที่มี token ทำงานจริง": "`/retry` และ `DELETE` ยังเป็น stub" → "`DELETE` ยังเป็น stub · `/retry` ทางจริงตาม `material-retry.md`" · **ไฟล์กลาง: แจ้งกลุ่มก่อน merge**
- `materials-db.md` §2.1 และ §9: เปลี่ยนคำว่า `/retry` ยังเป็น stub ให้ชี้มาที่ spec นี้
- `ingestion.md` §2.1 ข้อ 3: เพิ่มว่า endpoint ใช้ `runner.classify` / `runner.start` แทน `retry_material` (§2.2 ข้อ 6) · ไฟล์ของ Jam · บอก Jam ใน PR
