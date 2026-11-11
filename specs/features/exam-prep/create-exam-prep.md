# Feature: สร้างและดูรายการ exam prep บน DB จริง

| | |
|---|---|
| Area | scope (flow 2.3 ขั้นสร้างการเตรียมสอบ) |
| Requirements | CM-01, CM-02, SA-06 |
| Owner | Junior |
| Reviewer | Junior · May (รูปร่าง API ที่ฟอร์ม S08 และหน้าหลัก S27 ใช้) |
| Status | approved (Junior 2026-11-11) |
| Related system spec | `api.md` v1.14 "สร้างการเตรียมสอบและใส่ไฟล์" (`ExamPrep`, `POST`/`GET /exam-preps`) · `data-model.md` (RLS ของตารางส่วนตัว) · `0001_init.sql` `exam_preps`, policy `owner_rows` · `api-auth.md` §2.5 (`get_user_db`) · `config/ai.yaml` `guards.max_exam_prep_title_chars` · `config/learning.yaml` `planner.default_daily_minutes` |

## 1. Context

`POST /exam-preps` และ `GET /exam-preps` ตอนนี้เป็น stub ที่คืน fixture (`X-Stub: true`) ไม่บันทึกอะไร · journey ของ advisor update วันจันทร์ 16 พ.ย. ต้องสร้าง exam prep ได้จริงแล้วเห็นในรายการหลัง login ใหม่ · feature นี้เปลี่ยนสอง endpoint ให้อ่านและเขียนตาราง `exam_preps` ด้วย JWT ของผู้ใช้ (RLS) ตามสัญญาใน api.md v1.14 · หน้า S08 (ฟอร์ม) และ S27 (หน้าหลัก) ของ May เรียกใช้ · endpoint อื่นของ flow 2.3 ยังเป็น stub

## 2. Behavior

**1. `POST /exam-preps`** (CM-01)

1. เลือกทางตาม token (Junior ตัดสิน 2026-11-11 · ใช้กับ `GET` ด้วย):

   | | มี token ที่ถูก | token ผิด | ไม่มี token |
   |---|---|---|---|
   | `AUTH_REQUIRED=true` (staging, production) | **DB จริง** · ไม่มี `X-Stub` | `401 invalid_token` | `401 missing_token` · **ไม่มี stub เด็ดขาด** |
   | `AUTH_REQUIRED=false` (เครื่อง dev, test เดิม) | **DB จริง** · ไม่มี `X-Stub` | `401 invalid_token` | **stub เดิม** ที่คืน fixture พร้อม `X-Stub: true` · ไม่แตะ DB |

   ทางของ stub คงไว้ให้ May รันเว็บในเครื่องได้โดยไม่ login และให้ test ที่ review แล้ว (`test_exam_prep_api_contract.py`, `test_exam_prep_stubs.py`, `test_persona_stubs.py` ของ PR #105, #107) ผ่านโดยไม่ต้องแก้ · ทาง DB ใช้ `get_user_db` (`api-auth.md` §2.5) · การตรวจ body ข้อ 2–3 ใช้กับทั้งสองทาง
2. ตรวจ body (field เกิน, ขาด หรือผิดชนิด → `422 validation_error`):
   - `title`: string · มีอักขระควบคุม (Unicode category `Cc`: `\n`, `\r`, `\t`, `\x00`, `\x7f` ฯลฯ) ตรงไหนก็ตาม รวมหัวท้าย → `422 validation_error` · ตรวจข้อนี้**ก่อน**ตัดช่องว่าง (`"แคลคูลัส\n"` ถูกปฏิเสธ ไม่ถูกตัดทิ้ง) · อักขระจัดรูปแบบ (category `Cf` เช่น zero-width joiner U+200D) ได้ · แล้วตัดช่องว่างหัวท้าย · หลังตัดต้องไม่ว่าง · จำนวน **grapheme cluster** ต้อง ≤ `config/ai.yaml` → `guards.max_exam_prep_title_chars` (สระบน-ล่างและวรรณยุกต์ไทยรวมกับพยัญชนะเป็น 1 · ไม่นับตาม code point) · เกิน → `422 validation_error` (ไม่ตัดให้สั้น ต่างจาก `attachment_name`) · ชื่อซ้ำกับ prep เดิมได้ (api.md ไม่ห้าม · DB ไม่มี unique)
   - `exam_date`: string รูปแบบ `YYYY-MM-DD` เท่านั้น
   - `daily_minutes`: ไม่ส่ง หรือ `null`, หรือ JSON integer 1–1440 · string (`"30"`), boolean, ทศนิยม (`30.5`) → `422 validation_error` (ไม่แปลงชนิด · กฎเดียวกับ persona ใน api.md v1.12)
3. `exam_date` ก่อน "วันนี้" ตามเวลา Asia/Bangkok → `422 exam_date_past` · วันนี้ได้ · ตรวจหลังข้อ 2
4. insert 1 แถวลง `exam_preps` ผ่าน client ของผู้ใช้: `tenant_id` = `AuthContext.tenant_id`, `user_id` = `AuthContext.user_id` (จาก token เสมอ ไม่รับจาก body), `title` (หลังตัดช่องว่าง), `exam_date`, `daily_minutes` (null ถ้าไม่ส่ง), `subject` = null · `status` และ `created_at` ใช้ default ของ DB · policy `owner_rows` ตรวจซ้ำว่า tenant และ user ตรงกับ token
5. ตอบ `201` + `ExamPrep` ของแถวที่สร้าง: `stage = "materials"`, `readiness = null`, `topics_not_passed = null` · `days_left` ตาม §2.3 · ไม่มี header `X-Stub`

**2. `GET /exam-preps`** (CM-01, CM-02)

1. ต้องมีผู้ใช้เหมือน §2.1 ข้อ 1
2. อ่าน `exam_preps` ผ่าน client ของผู้ใช้ (RLS ทำให้เห็นแค่แถวของตัวเอง) ที่ `status = 'active'` (ไม่รวม `archived`)
3. เรียงตาม `exam_date` ใกล้ก่อน แล้วตาม `created_at` เก่าก่อน · ไม่มีแถว → `200 []`
4. แต่ละแถวเป็น `ExamPrep` · `days_left` ตาม §2.3 · `stage` ตาม §2.4 · `readiness` และ `topics_not_passed` เป็น null เสมอใน feature นี้ (api.md v1.14: null จนกว่า backend จะคำนวณ PM-03, PM-04) · ไม่มี header `X-Stub`

**3. `days_left`** (CM-02) = `exam_date − วันนี้` เป็นจำนวนวัน · "วันนี้" คือวันที่ตามเวลา Asia/Bangkok (UTC+7 ไม่มี DST) ตอนที่ request เข้ามา · เหมือน `Room.days_left` · ใน `GET` ค่าติดลบได้ถ้าวันสอบผ่านไปแล้ว (prep เก่ายังแสดงในรายการ · ดู §10 ข้อ 2)

**4. `stage`** (api.md v1.14 · ตามลำดับ ตัวแรกที่ตรง):

1. `tutoring` เมื่อ `active_scope_version_id` ไม่เป็น null
2. `scope` เมื่อ scope พร้อม: มีหัวข้อ (`topics`) ของ prep อย่างน้อย 1 หัวข้อ, ทุกหัวข้อมี `importance` ไม่เป็น null และไม่มีไฟล์ที่ `kind_confirmed = true` ซึ่ง `status` เป็น `confirmed`, `ingesting` หรือ `failed` (แปลงจาก `Ingestion.scope_ready` เป็นเงื่อนไขบน DB · ไม่มีหัวข้อเลย = ยังไม่พร้อม · Junior ตัดสิน 2026-11-11) · ⚠️ **Jam: ทบทวนเงื่อนไขนี้ตอนทำ ingestion** (เช่นใช้สถานะของ `ingestion_jobs` ขั้นรวมแทน) แล้วแก้ทั้ง spec นี้และ api.md `Ingestion.scope_ready` ให้ตรงกัน
3. `processing` เมื่อมีไฟล์ (`materials`) ของ prep ที่ `kind_confirmed = true`
4. `materials` นอกนั้น (รวม prep ที่ยังไม่มีไฟล์)

ระหว่างที่ upload และ ingestion ยังเป็น stub แถวที่สร้างจริงจะเป็น `materials` จนกว่า feature เหล่านั้นจะเขียน `materials`, `topics` จริง · อ่าน `materials` และ `topics` ผ่าน client ของผู้ใช้เหมือนกัน (RLS ของสองตารางนี้กรองตาม tenant)

**5. DB ล่ม** (Supabase ตอบ error, timeout หรือ network ล้ม) → `503` code `db_unavailable` (api.md v1.14) · `message` คงที่ "ระบบบันทึกข้อมูลไม่ได้ชั่วคราว ลองใหม่อีกครั้ง" ไม่มีรายละเอียดจาก exception · log รายละเอียดพร้อม `request_id` (ไม่ log token) · ไม่ปล่อยเป็น `500`

**6. นับ grapheme** ด้วย helper เดียวใน `app/` ที่ใช้ dependency `regex` pattern `\X` (Unicode UAX #29) · guard ของ `attachment_name` (`max_attachment_name_chars`) ใช้ helper นี้ซ้ำเมื่อทำจริง

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input `POST` | header `Authorization: Bearer <jwt>` · body `{title: string, exam_date: "YYYY-MM-DD", daily_minutes?: integer \| null}` | `{"title": "แคลคูลัส 1 กลางภาค", "exam_date": "2026-12-08"}` |
| Output `POST` | `201` + `ExamPrep` | `{"id": "…uuid…", "title": "แคลคูลัส 1 กลางภาค", "exam_date": "2026-12-08", "days_left": 27, "daily_minutes": null, "stage": "materials", "readiness": null, "topics_not_passed": null}` (เมื่อวันนี้คือ 2026-11-11) |
| Input `GET` | header `Authorization: Bearer <jwt>` | |
| Output `GET` | `200` + `ExamPrep[]` | `[]` หรือรายการตามตัวอย่างข้างบน |
| Error | `ErrorResponse` | `401 missing_token` · `401 invalid_token` · `422 validation_error` · `422 exam_date_past` · `503 db_unavailable` |

## 4. Acceptance criteria

ทุกข้อ "วันนี้" = วันที่ Asia/Bangkok ที่ test ตรึงไว้ (ไม่ใช้นาฬิกาจริง) · `guards.max_exam_prep_title_chars` อ่านจาก config ที่ test โหลด (ไม่เขียน 100 ลงใน test)

**สร้าง (CM-01)**

- **AC-1 (CM-01)** Given ผู้ใช้ A login แล้ว When `POST /exam-preps` `{title: "แคลคูลัส 1 กลางภาค", exam_date: วันนี้ + 27}` Then `201` · body ตรง `ExamPrep` ทุก field (`days_left = 27`, `daily_minutes = null`, `stage = "materials"`, `readiness = null`, `topics_not_passed = null`) · ไม่มี `X-Stub` · ตาราง `exam_preps` มีแถวใหม่ 1 แถวที่ `tenant_id`, `user_id` ตรงกับ token ของ A, `subject` เป็น null, `status = 'active'`
- **AC-2 (CM-01)** Given ผู้ใช้ A When `POST` พร้อม `daily_minutes: 45` Then `201` · `daily_minutes = 45` ใน response และในแถว
- **AC-3 (CM-01)** Given ผู้ใช้ A When `POST` พร้อม `daily_minutes: null` Then `201` · `daily_minutes = null`
- **AC-4 (CM-01)** Given title `"  แคลคูลัส 1  "` When `POST` Then `201` · `title = "แคลคูลัส 1"` ทั้งใน response และในแถว
- **AC-5 (CM-01)** Given title `""` หรือ `"   "` When `POST` Then `422 validation_error` · ไม่มีแถวใหม่
- **AC-6 (CM-01)** Given body ไม่มี `title` หรือไม่มี `exam_date`, หรือมี field เกิน (เช่น `subject`, `user_id`, `tenant_id`) When `POST` Then `422 validation_error` · ไม่มีแถวใหม่
- **AC-7 (CM-01)** Given `exam_date` เป็น `"2026-1-5"`, `"05/01/2026"`, `"2026-11-11T00:00:00"` หรือ `"2026-02-30"` When `POST` Then `422 validation_error`
- **AC-8 (CM-01)** Given `daily_minutes` เป็น `"30"`, `true` หรือ `30.5` When `POST` Then `422 validation_error`
- **AC-9 (CM-01)** Given ผู้ใช้ A มี prep ชื่อ "แคลคูลัส 1" แล้ว When `POST` ชื่อเดียวกันอีกครั้ง Then `201` · มี 2 แถว

**Boundary**

- **AC-boundary-date (CM-01, CM-02)** `exam_date` = วันนี้ − 1 → `422 exam_date_past` · = วันนี้ → `201` `days_left = 0` · = วันนี้ + 1 → `201` `days_left = 1`
- **AC-boundary-date-tz (CM-02)** Given นาฬิกา UTC เป็น 2026-11-11T17:30Z (= 2026-11-12 00:30 ที่กรุงเทพ) When `POST` `exam_date: "2026-11-11"` Then `422 exam_date_past` · และ `exam_date: "2026-11-12"` → `201` `days_left = 0`
- **AC-boundary-title (CM-01)** ให้ N = `guards.max_exam_prep_title_chars` · title ยาว N − 1 grapheme → `201` · N → `201` · N + 1 → `422 validation_error`
- **AC-boundary-title-thai (CM-01)** title ภาษาไทยที่มี N grapheme แต่มี code point มากกว่า N (เช่นคำที่มีสระบนและวรรณยุกต์ "กี่" ซ้ำจนครบ N grapheme) → `201` · ช่องว่างหัวท้ายไม่นับ (title N grapheme + ช่องว่างหน้าหลัง → `201`)
- **AC-title-control (CM-01)** title ที่มีอักขระควบคุม → `422 validation_error` · ไม่มีแถวใหม่: `"แคลคูลัส\n1"` (กลาง) · `"แคลคูลัส\t1"` · `"แคลคูลัส\x001"` · `"แคลคูลัส\r\n1"` · `"แคลคูลัส\x7f"` · `"แคลคูลัส 1\n"` (ท้าย · ไม่ถูกตัดทิ้ง) · `"\tแคลคูลัส 1"` (หน้า)
- **AC-title-format-ok (CM-01)** title ที่มีอักขระจัดรูปแบบ (`Cf`) ไม่ใช่อักขระควบคุม → `201` และเก็บตามที่ส่ง: zero-width joiner กลางคำไทย `"แคล‍คูลัส"` · zero-width non-joiner `"แคล‌คูลัส"` · ช่องว่างธรรมดากลางคำ `"แคลคูลัส 1 กลางภาค"`
- **AC-boundary-minutes (CM-01)** `daily_minutes` = 0 → `422` · 1 → `201` · 1440 → `201` · 1441 → `422`

**รายการ (CM-01, CM-02)**

- **AC-10 (CM-01)** Given ผู้ใช้ A ยังไม่มี prep When `GET /exam-preps` Then `200 []` · ไม่มี `X-Stub`
- **AC-11 (CM-02)** Given ผู้ใช้ A สร้าง prep สอบวันนี้ + 10 และวันนี้ + 3 When `GET` Then ได้ 2 รายการ เรียง +3 ก่อน · `days_left` = 3 และ 10
- **AC-12 (CM-01)** Given A มี 2 prep วันสอบเดียวกัน สร้างเวลาต่างกัน When `GET` Then อันที่สร้างก่อนมาก่อน
- **AC-13 (CM-01)** Given A มี prep ที่ `status = 'archived'` (ตั้งด้วย service role ใน test) When `GET` Then ไม่มีแถวนั้น
- **AC-14 (CM-02)** Given prep ของ A ที่ `exam_date` เป็นเมื่อวาน (ใส่ด้วย service role) When `GET` Then อยู่ในรายการ `days_left = -1`
- **AC-15 (CM-01)** `stage`: prep ที่ไม่มีไฟล์ → `materials` · มีไฟล์ `kind_confirmed = false` เท่านั้น → `materials` · มีไฟล์ `kind_confirmed = true` → `processing` · มีหัวข้อที่ `importance` ครบทุกหัวข้อและไม่มีไฟล์ยืนยันแล้วที่ `confirmed`/`ingesting`/`failed` → `scope` · มีหัวข้อแต่ `importance` เป็น null อย่างน้อย 1 → ไม่ใช่ `scope` · มีหัวข้อครบแต่มีไฟล์ยืนยันแล้วที่ `ingesting` → `processing` · มี `active_scope_version_id` → `tutoring` (`readiness`, `topics_not_passed` ยังเป็น null) · ข้อมูลไฟล์และหัวข้อใส่ด้วย service role ใน test
- **AC-16 (CM-01)** Given request เดียวกับ AC-1 When สร้างแล้ว `GET` ด้วย token ใหม่ของ A (login ใหม่) Then เห็น prep ที่สร้าง (บันทึกจริง ไม่อยู่ใน memory)

**Auth และ tenant**

- **AC-auth-required (SA-06)** Given `AUTH_REQUIRED=true` When `POST` หรือ `GET` ไม่มี token Then `401 missing_token` · ไม่มี `X-Stub` · ไม่เรียก repository (ไม่มีแถวใหม่ · ไม่ได้ fixture)
- **AC-auth-stub (SA-06)** Given `AUTH_REQUIRED=false` When `POST` (body ถูก) หรือ `GET` ไม่มี token Then ได้ stub: `201` / `200` พร้อม `X-Stub: true` · `GET` ได้ fixture (มี prep ครบทั้ง 4 stage) · ไม่เรียก repository · `POST` ที่ body ผิดยังได้ `422` ตามกฎเดียวกัน
- **AC-auth-real (CM-01)** Given มี token ที่ถูก When `POST` หรือ `GET` ทั้งเมื่อ `AUTH_REQUIRED=true` และ `false` Then ใช้ repository (DB จริง) · ไม่มี header `X-Stub`
- **AC-auth-bad (SA-06)** token ผิด → `401 invalid_token` ทั้งเมื่อ `AUTH_REQUIRED=true` และ `false` · ไม่มีแถวใหม่
- **AC-tenant (SA-06)** Given ผู้ใช้ A และ B อยู่คนละ tenant และ A มี prep 2 รายการ When B `GET /exam-preps` Then `[]` · และเมื่อ B `POST` แล้ว A `GET` ก็ไม่เห็นของ B
- **AC-tenant-body (SA-06)** Given B ส่ง `tenant_id` หรือ `user_id` ของ A ใน body When `POST` Then `422 validation_error` (field เกิน) · ไม่มีแถวใหม่ใน tenant ของ A

**DB ล่ม**

- **AC-db (CM-01)** Given client ของ DB โยน error (จำลองใน unit test) When `POST` หรือ `GET` Then `503` `{"error": {"code": "db_unavailable", "message": "ระบบบันทึกข้อมูลไม่ได้ชั่วคราว ลองใหม่อีกครั้ง"}}` (ไม่ใช่ 500) · message ไม่มีข้อความจาก exception · มี `X-Request-Id`

## 5. Data changes

ไม่มี · ใช้ `exam_preps` (`0001_init.sql`) ตามที่เป็น · policy `owner_rows` (`tenant_id = current_tenant_id() and user_id = auth.uid()`) มีอยู่แล้วทั้ง using และ with check · index `(tenant_id, user_id)` มีอยู่แล้ว

## 6. API / SSE changes

| Endpoint / event | Request | Response |
|---|---|---|
| `POST /exam-preps` | เปลี่ยนจาก stub เป็นของจริง · body ตาม api.md v1.14 | `201` `ExamPrep` · ไม่มี `X-Stub` · error ตาม §3 |
| `GET /exam-preps` | เปลี่ยนจาก stub เป็นของจริง | `200` `ExamPrep[]` · ไม่มี `X-Stub` |

OpenAPI: `daily_minutes` มี `minimum: 1`, `maximum: 1440` · `title` ไม่ใส่ `maxLength` (OpenAPI นับเป็นตัวอักษร ไม่ใช่ grapheme) · response `401`, `422`, `503` เป็น `ErrorResponse` · หลัง merge May รัน `pnpm gen:api`

## 7. AI calls

ไม่มี

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/unit/test_exam_prep_api.py` · router + validation กับ fake repository (ไม่ต่อ DB) · นาฬิกาตรึง · config จริงที่โหลด | unit | AC-4 ถึง AC-8, AC-boundary-*, AC-title-control, AC-title-format-ok, AC-db, AC-auth-required, AC-auth-stub, AC-auth-real (fake auth + fake repository) |
| `tests/unit/test_graphemes.py` · helper นับ grapheme (ไทยมีสระบนและวรรณยุกต์, emoji ที่มี ZWJ, ASCII) | unit | AC-boundary-title, AC-boundary-title-thai |
| `tests/unit/test_exam_prep_stage.py` · ฟังก์ชันคำนวณ `stage` และ `days_left` (pure) แบบ table-driven | unit | AC-15, AC-boundary-date-tz, AC-14 (ค่าติดลบ) |
| `tests/integration/test_exam_prep_db.py` · Supabase ในเครื่องหรือ CI · user จริง 2 คนคนละ tenant (สร้างด้วย admin API แล้วลบ เหมือน `test_api_auth_db.py`) | integration | AC-1 ถึง AC-3, AC-9 ถึง AC-13, AC-16, AC-tenant, AC-tenant-body, AC-auth-real, AC-auth-bad (token จริง) |

ชื่อ test ขึ้นต้นด้วย requirement ID เช่น `test_CM01_title_over_max_graphemes_rejected`, `test_SA06_other_tenant_sees_no_exam_preps`

## 9. Out of scope

- materials, upload, Storage, ingestion, scope (ยังเป็น stub · ลำดับ 4–5 ของงานวันจันทร์)
- คำนวณ `readiness` (PM-03) และ `topics_not_passed` (PM-04) จริง
- `GET /exam-preps/{id}`, แก้ไข prep, archive, `DELETE /exam-preps/{id}`
- หน้าเว็บ S08, S27 (May)
- เพดานวันสอบไกลสุด

## 10. Open questions

ตัดสินครบแล้ว (Junior 2026-11-11):

1. ~~DB ล่มตอบอะไร~~ → `503 db_unavailable` (§2.5 · api.md v1.14 · เพิ่มในรายการ `error.code` ของ issue #40)
2. ~~prep ที่วันสอบผ่านไปแล้ว~~ → แสดงใน `GET` พร้อม `days_left` ติดลบ ไม่ archive อัตโนมัติ · **May** ตัดสินว่าการ์ดแสดงอย่างไร
3. ~~`scope` เมื่อยังไม่มีหัวข้อ~~ → ยังไม่พร้อม · Jam ทบทวนตอนทำ ingestion (§2.4 ข้อ 2)
4. ~~นับ grapheme ด้วยอะไร~~ → `regex` `\X` helper เดียว (§2.6)
5. ~~title ที่มีอักขระควบคุม~~ → ปฏิเสธ `422 validation_error` (§2.1 · AC-title-control) เพราะ title คือ `prep_name` ของห้องและน่าจะเข้า prompt ของ tutor ทีหลัง · เก็บ DB ให้สะอาดตั้งแต่ตอนนี้ดีกว่าตามล้างแถวเก่า

## 11. Spec changes needed

- `specs/system/api.md` v1.14 (ไฟล์กลาง · ทำแล้วใน PR นี้): `503 db_unavailable` และกฎอักขระควบคุมของ `title`
- issue #40 รายการ `error.code`: เพิ่ม `db_unavailable` (503)
- `apps/api/pyproject.toml`: dependency `regex`
