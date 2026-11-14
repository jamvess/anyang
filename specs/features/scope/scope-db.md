# Feature: หน้าตรวจขอบเขตบน DB · อ่านหัวข้อ + ดาว · ดูที่มา · ยืนยัน scope (demo ขั้น 5)

| | |
|---|---|
| Area | scope |
| Requirements | SM-02, SM-03, SM-04, SM-09, SA-06 |
| Owner | Jam (งานของ Junior · Junior ให้ตัดสินใจไปก่อน 14 พ.ย.) |
| Reviewer | Jam · Junior ดูย้อนหลัง (การเขียน `scope_versions`, `exam_preps`, `topics` · api.md v1.6 รอตัดสินข้อ 1–5) |
| Status | draft 2026-11-14 (PR #137) |
| Related system spec | api.md v1.6 "หน้าตรวจขอบเขต" + รอตัดสิน (v1.6) · `scope-review.md` (หน้าเว็บของ May · S12) · `ingestion.md` (#130 · ที่มาของหัวข้อ ดาว ช่วงหน้า ข้อสอบ) · ai-orchestration §2.3.2 ขั้น 7 (ยืนยัน), §2.3.5 (ดาว) · data-model.md รูป 2 · `docs/team/sprint-checklists.md` ⭐ demo ขั้น 5 |

## 1. Context

หลังอัปโหลดไฟล์ ingestion (#130) เขียนหัวข้อ ดาว เหตุผล ช่วงหน้า และข้อสอบเก่าลง DB แล้ว แต่ 3 endpoint ของหน้าตรวจขอบเขต (S12) ยังเป็น stub · ผู้ใช้จึงไม่เห็นหัวข้อของวิชาตัวเอง และกดยืนยันแล้วไม่มีอะไรถูกบันทึก (`exam_preps.active_scope_version_id` ว่างตลอด) · feature นี้ทำทั้ง 3 endpoint ในทางที่มี token ตามรูปร่างและข้อเสนอของ api.md v1.6 · ไม่มี AI call

## 2. Behavior

ทุกข้อใช้ JWT ของผู้ใช้ (RLS) · prep หรือหัวข้อที่ไม่มีหรือเป็นของคนอื่น → `404 not_found` · DB ล่ม → `503 db_unavailable` · ไม่มี token (`AUTH_REQUIRED=false`) → stub เดิมพร้อม `X-Stub` (api.md v1.14)

### 2.1 `GET /exam-preps/{id}/scope` → `Scope`

1. **ยังไม่พร้อม → `409 scope_not_ready`:** prep ยังไม่มีหัวข้อ หรือมีหัวข้อที่ `importance` เป็น null (ดาวยังคำนวณไม่เสร็จ · ไม่ตัดหัวข้อนั้นทิ้ง · api.md v1.6)
2. `prep_name` = `exam_preps.title` · `days_left` ตามกฎ v1.14 (Asia/Bangkok)
3. `status` = `"confirmed"` เมื่อ `active_scope_version_id` ไม่ว่าง **และ** ไม่มีแถว `scope_changes` ของ prep ที่ `created_at` หลัง `confirmed_at` ของ version นั้น · ไม่งั้น `"draft"` (api.md รอตัดสินข้อ 1)
4. `topics` = ทุกหัวข้อของ prep เรียง `order_index` **รวมที่ตัดออก** · `id` · `order` = `order_index` (นับจาก 1 · ingestion เขียนจาก 1) · `name` · `stars` = `importance` (หัวข้อ `status = 'excluded'` เป็น 0 เสมอ) · `reason` = `importance_reason` (ว่าง → `""`) · `origin`
5. `source_label` (api.md รอตัดสินข้อ 2): ช่วงหน้าใน `topic_sources` ของหัวข้อ เรียงตามไฟล์ (`materials.created_at`) แล้ว `page_from` · แต่ละช่วงเป็น `{ชื่อไฟล์ไม่มีนามสกุล} น.{from}–{to}` (หน้าเดียว `น.{n}`) · หลายช่วงคั่นด้วย `, ` · ไม่มีช่วง (หัวข้อ `origin = 'user'`) → `""`
6. `unmapped_questions` = `past_exam_questions` ของไฟล์ใน prep ที่ `topic_id is null` · เรียงตามไฟล์ (`materials.created_at`) แล้ว `page_no` แล้ว `q_no` (ตัวเลขเรียงแบบตัวเลข) · `label` = `{ชื่อไฟล์ไม่มีนามสกุล} ข้อ {q_no}` · `text` · `map_note` (null ได้)

### 2.2 `GET /topics/{id}/sources` → `TopicSources` (SM-04)

1. `excerpts` = 1 รายการต่อ 1 หน้าในทุกช่วงของ `topic_sources` ของหัวข้อ · `material_name` = `materials.file_name` · `page` = `page_no` · `text` = `material_pages.text` ทั้งหน้า (api.md รอตัดสินข้อ 3) · เรียงตามไฟล์แล้วหน้า · หน้าที่ช่วงทับกันมาครั้งเดียว · หน้าที่ไม่มีแถว `material_pages` ข้ามไป · หัวข้อ `origin = 'user'` → `[]`
2. `questions` = `past_exam_questions` ที่ `topic_id` = หัวข้อนี้ · เรียงเหมือน §2.1 ข้อ 6 · ไม่มี → `[]`

### 2.3 `POST /exam-preps/{id}/scope/confirm` → `ScopeConfirmed` (SM-09)

1. ตรวจตามลำดับ (ก่อนเขียนอะไร): ยังไม่พร้อมตาม §2.1 ข้อ 1 → `409 scope_not_ready` · `status` ตาม §2.1 ข้อ 3 เป็น `"confirmed"` → `409 scope_already_confirmed` · ไม่มีหัวข้อที่เหลือ (ทุกหัวข้อ `status = 'excluded'` หรือ `importance = 0`) → `409 scope_empty`
2. **version** = version สูงสุดของ prep + 1 (ยังไม่มี → 1)
3. เขียนตามลำดับ (ai-orchestration §2.3.2 ขั้น 7):
   1. insert `scope_versions`: `tenant_id` จาก token · `exam_prep_id` · `version` · `status = 'confirmed'` · `confirmed_at = now` · `snapshot` = รายการหัวข้อ `{topic_id, name, order, stars, status, origin}` หลังยืนยัน (หัวข้อ `draft` เป็น `confirmed`) เรียง `order_index`
   2. ตั้ง `exam_preps.active_scope_version_id` = แถวใหม่
   3. หัวข้อ `status = 'draft'` ของ prep → `'confirmed'` (หัวข้อ `excluded` คงเดิม)
4. **ยืนยันพร้อมกัน:** insert ข้อ 3.1 ชน `unique (exam_prep_id, version)` → `409 scope_already_confirmed` (อีก request ยืนยันไปก่อนแล้ว · ไม่เขียนข้อ 3.2–3.3)
5. เขียนข้อ 3.2 หรือ 3.3 ไม่ได้ (DB ล่มกลางทาง) → `503` · ยืนยันใหม่ได้ (ได้ version ถัดไป · version ที่ไม่ได้ใช้ค้างเป็นแถวที่ไม่มีใครชี้)
6. ผล `{scope_version_id, version}` · หน้าเว็บใช้แค่ว่าได้ 2xx แล้วไปห้องติว (scope-review AC-15)
7. session ที่เปิดหลังยืนยันผูก `scope_version_id` นี้ (#123 · `create_session` อ่าน `active_scope_version_id` อยู่แล้ว) · session ที่เปิดก่อนยืนยันคงเป็น null (0004)

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | prep ที่ ingestion เขียนแล้ว: `topics`, `topic_sources`, `materials`, `material_pages`, `past_exam_questions` | MTH10101: 34 หัวข้อ · ข้อสอบ 43 ข้อ |
| Output | `Scope` · `TopicSources` · `ScopeConfirmed` (api.md v1.6 · รูปร่างเดิมของ stub) | `source_label: "sheet-01 น.2–26, sheet-03 น.1"` · `{scope_version_id, version: 1}` |
| Output (DB) | `scope_versions` 1 แถว · `exam_preps.active_scope_version_id` · `topics.status` | |

## 4. Acceptance criteria

fake repository (แถวที่ JWT ของผู้ใช้เห็น) · "DB" = integration บน Supabase ในเครื่อง

- **AC-1 (SM-02, SM-03)** prep มี 3 หัวข้อ (★★★, ★★, ตัดออก) → `GET /scope` `200` · `topics` เรียง `order_index` ครบ 3 · หัวข้อที่ตัดออก `stars` 0 · `reason`, `origin` จาก DB · `status` `"draft"` · `prep_name`, `days_left` ของ prep · ไม่มี `X-Stub`
- **AC-2 (SM-04)** `source_label`: 2 ช่วงในไฟล์เดียว + 1 ช่วงอีกไฟล์ → `"sheet-01 น.2–26, sheet-01 น.30, sheet-03 น.1–2"` (ตามลำดับไฟล์แล้วหน้า · หน้าเดียวไม่มีขีด · ตัดนามสกุลไฟล์) · หัวข้อ `origin = 'user'` → `""`
- **AC-3** `unmapped_questions` = ข้อสอบที่ `topic_id` null เท่านั้น · `label` `"final-2566 ข้อ 2"` · เรียงข้อ 2 ก่อนข้อ 10 · `map_note` null ได้
- **AC-4** ยังไม่มีหัวข้อ หรือมีหัวข้อที่ `importance` null → `409 scope_not_ready` ทั้ง `GET /scope` และ confirm
- **AC-5 (SM-04)** `GET /topics/{id}/sources`: ช่วง 2–3 + 3–4 ของไฟล์เดียว → `excerpts` หน้า 2, 3, 4 (หน้า 3 ครั้งเดียว) พร้อม `material_name` และ `text` ของหน้า · `questions` ของหัวข้อนี้ · หัวข้อ `origin = 'user'` → `excerpts` `[]` · หัวข้อที่ไม่มี → `404`
- **AC-6 (SM-09)** confirm → `200 {scope_version_id, version: 1}` · แถว `scope_versions` มี `status = 'confirmed'`, `confirmed_at`, `snapshot` ของ 3 หัวข้อ · `active_scope_version_id` = แถวใหม่ · หัวข้อ `draft` เป็น `confirmed` · หัวข้อที่ตัดออกยัง `excluded` · หลังจากนั้น `GET /scope` `status` `"confirmed"`
- **AC-7** ยืนยันแล้ว → confirm อีกครั้ง → `409 scope_already_confirmed` · ไม่มีแถวใหม่
- **AC-8** มี `scope_changes` หลัง `confirmed_at` → `status` `"draft"` · confirm ได้ version 2
- **AC-9** ทุกหัวข้อตัดออก → `409 scope_empty`
- **AC-10** insert `scope_versions` ชน unique (ยืนยันพร้อมกัน) → `409 scope_already_confirmed` · `active_scope_version_id` ไม่เปลี่ยน
- **AC-11** prep ที่ไม่มี → `404` (ทั้ง 3 endpoint) · DB ล่ม → `503`
- **AC-12** ไม่มี token → stub เดิม (`X-Stub`) · test เดิมของ stub และ contract ผ่านโดยไม่แก้
- **AC-tenant (SA-06 · DB)** B อ่าน scope ของ A → `404` · B ยืนยัน scope ของ A → `404` และไม่มีแถว · A ยืนยัน → แถว `scope_versions` มี `tenant_id` ของ A · A เปิดห้องหลังยืนยัน → `tutor_sessions.scope_version_id` = version นั้น

## 5. Data changes

ไม่มี migration · เขียน `scope_versions` (insert), `exam_preps.active_scope_version_id`, `topics.status` (update) · อ่าน `topics`, `topic_sources`, `materials`, `material_pages`, `past_exam_questions`, `scope_changes` · RLS เดิม (`tenant_rows` / `owner_rows`)

## 6. API / SSE changes

ไม่มี endpoint หรือ field ใหม่ · ทั้ง 3 endpoint ในทางที่มี token ทำตาม api.md v1.6 · OpenAPI เพิ่ม `503 db_unavailable` · api.md (ไฟล์กลาง) เขียนว่าทางที่มี token ทำงานจริงแล้ว และใช้ข้อเสนอรอตัดสินข้อ 1–3, 5 (Junior ดูย้อนหลัง · §10)

## 7. AI calls

ไม่มี

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/unit/test_scope_db.py` (ไฟล์ใหม่ · fake repository ของ scope) | unit | AC-1 ถึง AC-11 |
| `tests/unit/test_scope_domain.py` (`source_label`, `label`, ลำดับข้อสอบ · table-driven) | unit (pure) | AC-2, AC-3 |
| test เดิม (`test_scope_api_contract.py`, `test_scope_stubs.py`) | unit | AC-12 |
| `tests/integration/test_scope_db.py` | integration | AC-tenant, AC-6 บนแถวจริง |
| รันกับข้อมูลจริงของ MTH10101 (ขั้น 4 ของ worklog) | มือ | ingestion → scope → ยืนยัน → เปิดห้อง |

## 9. Out of scope

- แก้ scope ผ่านแชท (`scope/chat`), change log (`scope/changes`), การเขียน `scope_changes` (SM-06–08 · S5) · endpoint เหล่านี้ยังเป็น stub
- ชื่อย่อของไฟล์ (เช่น "ch3" ใน fixture ของ May · ยังไม่มีที่เก็บ · api.md รอตัดสินข้อ 2) · ใช้ชื่อไฟล์ไม่มีนามสกุลไปก่อน
- ตัดข้อความต้นฉบับเฉพาะส่วนที่เกี่ยวข้อง (ส่งทั้งหน้า · api.md รอตัดสินข้อ 3)
- หน้าเว็บ S12 ต่อ API จริง (May · demo ขั้น 5 ฝั่งเว็บ)

## 10. Open questions

1. **(Junior) api.md รอตัดสิน v1.6 ข้อ 1–3, 5:** feature นี้ทำตามข้อเสนอทั้งหมด (`status` จาก `active_scope_version_id` · กฎ `source_label` / `label` · ข้อความทั้งหน้า · error code 409 ทั้ง 3 แบบ) · ถ้า Junior ตัดสินต่าง แก้ใน PR ใหม่
2. **(Junior) เขียน 3 ขั้นไม่ใช่ transaction เดียว:** PostgREST ทำทีละคำสั่ง · ทางอื่น: SQL function (RPC) ที่ทำทั้ง 3 ขั้นใน transaction · ข้อเสนอ: ทีละคำสั่งไปก่อน (unique ของ version กันยืนยันซ้ำ · ล่มกลางทางยืนยันใหม่ได้) · RPC หลัง demo ถ้าต้องการ

## 11. Spec changes needed

| ไฟล์ | แก้อะไร | ใคร |
|---|---|---|
| `specs/system/api.md` (ไฟล์กลาง) | หน้าตรวจขอบเขต: ทางที่มี token ทำงานจริง (v1.20) · รอตัดสินข้อ 1–3, 5 ใช้ข้อเสนอแล้ว (รอ Junior ยืนยัน) · `503 db_unavailable` | Jam · PR นี้ · ถามก่อน |
