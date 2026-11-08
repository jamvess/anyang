# P8-lite · `compute_importance` (ดาวความสำคัญของหัวข้อ)

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/compute-importance` |
| Checklist item | P8-lite ร่วมกับทีม (เป็นเจ้าของ spec `compute_importance`) |
| Status | in progress · 2026-11-08 |

Spec: `specs/features/scope/compute-importance.md` (approved 31 ต.ค.) · SM-03, SM-09 · metrics: `poc/P8-lite/metrics.md`

## Plan

- [x] 1. 🤖 `/spec-to-tests`: `apps/api/tests/unit/test_stars.py` (19 test ตาม §8) + AC-19 ใน `test_settings.py` · รันให้แดงเพราะยังไม่มี `app/domain/stars.py` · จดเวลาลง metrics §4
- [x] 2. 🙋 Jam review test (ตาราง AC → test) · จดเวลาเริ่ม–จบลง metrics §4 · test ผิดจดลง metrics §3 · spec ไม่ชัดจดลง §5
- [ ] 3. 🤖 `/implement-feature`: `app/domain/stars.py` + `StarsConfig.no_past_exam_method` เป็น `Literal["page_terciles"]` · จดทุกรอบ red → green ลง metrics §2
- [ ] 4. 🤖 รัน `pytest`, `ruff` ทั้งหมด · กรอก metrics §1 ด้วย `agent_lines.sh`
- [ ] 5. 🙋 `/work-done`: `/code-review` (จดบั๊กลง metrics §3) · ข้อความกลุ่มให้ Junior + May review test ย้อนหลัง

## Definition of done

- test ทุกข้อใน spec §8 เขียวใน CI (job `api` ไม่มี Supabase = AC-pure)
- `StarsConfig.no_past_exam_method` ค่าผิดล้มตอนโหลด config (AC-19)
- `poc/P8-lite/metrics.md` กรอกครบ §1–§5 (ยกเว้นเวลาของ Junior และ May ถ้ายังไม่ได้ review)
- ติ๊กขั้น `/spec-to-tests` → `/implement-feature` → merge ของข้อ P8-lite (ข้อ checklist ติ๊กเมื่อเก็บ metrics ครบ)

## Decisions

- 2026-11-08 · Jam ok test ทั้งหมด (review 13:52–13:56) รวม test ที่เพิ่มจาก §2 ขั้นที่ 3 และ `signal_r` ของ AC-17 หารด้วยหน้าของทุกหัวข้อรวมที่ตัดออก · จดใน metrics §5
- 2026-11-08 · solo time: Jam review test เองแล้ว implement ต่อ · Junior + May review ย้อนหลังหลัง merge (ทีมตกลง 31 ต.ค. · ไม่ต้องรอ approve) · `apps/api/` เป็นของ Junior จึงบอกกลุ่ม

## Next step

รัน `/implement-feature specs/features/scope/compute-importance.md` (ขั้น 3) · จดทุกรอบ red → green ลง `poc/P8-lite/metrics.md` §2

## Waiting on

ไม่มี (Junior + May review test ย้อนหลังได้ ไม่ขวาง)

## Notes for next time

- เริ่มงาน 13:46 (8 พ.ย.) · `/spec-to-tests` 13:47–13:50 (รอ Claude)
- test ที่ไม่มี AC ตรง (มาจาก §2): `test_SM03_no_past_exam_keeps_user_stars_and_counts_their_rank` (§2 ขั้นที่ 3 ข้อ 1–3) และแถว "ranked by pages, not by input order" ใน `test_SM03_no_past_exam_page_terciles` · ถ้า Jam ok ให้จดลง metrics §5 ว่า spec ไม่มี AC ของกรณีผู้ใช้แก้ดาวในโหมดไม่มีข้อสอบเก่า
- integration test ในเครื่องแดงเพราะ local Supabase ยังไม่มี `topic_sources` (ต้อง `npx supabase db reset`) · ไม่เกี่ยวกับงานนี้ · CI รัน migration เอง
