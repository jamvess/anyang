# Exam prep API จริง: `POST`/`GET /exam-preps` บันทึกลง DB (CM-01, CM-02)

| | |
|---|---|
| Owner | Junior |
| Branch | `feat/exam-prep-api` |
| Checklist item | เตรียม staging สำหรับ demo รวม (ลำดับ 2 ของ journey วันจันทร์: exam prep API) |
| Status | in progress · 2026-11-11 |

## Plan

- [x] 1. 🤖 api.md v1.14 ปิด "รอตัดสิน" v1.10 ส่วน `/exam-preps` (ข้อ 3, 4, `exam_date_past`) · `guards.max_exam_prep_title_chars` ใน `config/ai.yaml` 1.16 · Junior ok 11 พ.ย.
- [ ] 2. 🙋 Junior บอก May (ข้อความใน PR) + บอกกลุ่มว่าแก้ไฟล์กลาง `api.md`, `config/ai.yaml`
- [x] 3. 🤖 `/spec-feature` → `specs/features/exam-prep/create-exam-prep.md` (CM-01, CM-02)
- [ ] 4. 🙋 Junior review spec
- [x] 5. 🤖 `/spec-to-tests`: unit (validation, grapheme, `days_left`, `stage`) + integration กับ Supabase ในเครื่อง (บันทึกผ่าน JWT ของ user, RLS, isolation SA-06)
- [ ] 6. 🙋 Junior review test
- [x] 7. 🤖 `/implement-feature`: repository ใน `app/db/` ที่ใช้ `get_user_db` · router เลิกใช้ stub ของ 2 endpoint นี้ · `pnpm gen:api`
- [ ] 8. 🤖 `/work-done` → ถาม Junior ก่อน merge

## Definition of done

- `POST /exam-preps` บันทึกแถว `exam_preps` จริงด้วย JWT ของผู้ใช้ · `GET /exam-preps` คืนแถวของผู้ใช้คนนั้นเท่านั้น · ไม่มี `X-Stub`
- validation ตาม api.md v1.14 (title นับ grapheme ≤ `guards.max_exam_prep_title_chars`, `exam_date_past`, `daily_minutes` 1–1440)
- integration test: isolation ระหว่าง 2 tenant (SA-06) · test ผ่านใน CI

## Decisions

- 2026-11-11 · `title` ≤ 100 อยู่ใน `config/ai.yaml` `guards.max_exam_prep_title_chars` ไม่ hard-code · นับ grapheme cluster · `daily_minutes` ≤ 1440 hard-code ได้ (นาทีในหนึ่งวัน)
- 2026-11-11 · ไม่มี field `subject` ใน API (เทอม 1 คณิตอย่างเดียว) · `readiness`/`topics_not_passed` เป็น null จนกว่าจะคำนวณ PM-03/04 จริง
- 2026-11-11 · ส่วน materials ของ v1.10 (ข้อ 1, 2, 5) ยังเปิด · ตัดสินตอนทำลำดับ 4 (upload + Storage)
- 2026-11-11 · ไม่มี token + `AUTH_REQUIRED=false` → stub เดิม (`X-Stub: true`) · ไม่มี token + `true` → 401 ไม่มี stub · มี token → DB จริง ไม่มี `X-Stub` · เพื่อให้ test ที่ review แล้วของ #105, #107 ผ่านโดยไม่แก้ และ May รันในเครื่องได้โดยไม่ login

## Next step

ข้อ 8: `/work-done` (code-review) แล้วถาม Junior ก่อน merge #121 · ร่าง PR อยู่ใน scratchpad pr-121.md จะใส่ตอน work-done · ค้าง: comment ใน issue #40 เพิ่ม `db_unavailable` (503) ในรายการ `error.code` (gh ติด rate limit 11 พ.ย.)

## Waiting on

ไม่มี

## Notes for next time

- ลำดับของ Junior สำหรับวันจันทร์: 1) login + #120 2) exam prep API (branch นี้) 3) บันทึก messages + resume 4) upload + Storage 5) ingestion (Jam)
