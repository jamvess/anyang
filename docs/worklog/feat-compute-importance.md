# P8-lite · `compute_importance` (ดาวความสำคัญของหัวข้อ)

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/compute-importance` |
| Checklist item | P8-lite ร่วมกับทีม (เป็นเจ้าของ spec `compute_importance`) |
| Status | in progress · 2026-11-08 |

Spec: `specs/features/scope/compute-importance.md` (approved 31 ต.ค.) · SM-03, SM-09 · metrics: `poc/P8-lite/metrics.md`

## Plan

- [ ] 1. 🤖 `/spec-to-tests`: `apps/api/tests/unit/test_stars.py` (19 test ตาม §8) + AC-19 ใน `test_settings.py` · รันให้แดงเพราะยังไม่มี `app/domain/stars.py` · จดเวลาลง metrics §4
- [ ] 2. 🙋 Jam review test (ตาราง AC → test) · จดเวลาเริ่ม–จบลง metrics §4 · test ผิดจดลง metrics §3 · spec ไม่ชัดจดลง §5
- [ ] 3. 🤖 `/implement-feature`: `app/domain/stars.py` + `StarsConfig.no_past_exam_method` เป็น `Literal["page_terciles"]` · จดทุกรอบ red → green ลง metrics §2
- [ ] 4. 🤖 รัน `pytest`, `ruff` ทั้งหมด · กรอก metrics §1 ด้วย `agent_lines.sh`
- [ ] 5. 🙋 `/work-done`: `/code-review` (จดบั๊กลง metrics §3) · ข้อความกลุ่มให้ Junior + May review test ย้อนหลัง

## Definition of done

- test ทุกข้อใน spec §8 เขียวใน CI (job `api` ไม่มี Supabase = AC-pure)
- `StarsConfig.no_past_exam_method` ค่าผิดล้มตอนโหลด config (AC-19)
- `poc/P8-lite/metrics.md` กรอกครบ §1–§5 (ยกเว้นเวลาของ Junior และ May ถ้ายังไม่ได้ review)
- ติ๊กขั้น `/spec-to-tests` → `/implement-feature` → merge ของข้อ P8-lite (ข้อ checklist ติ๊กเมื่อเก็บ metrics ครบ)

## Decisions

- 2026-11-08 · solo time: Jam review test เองแล้ว implement ต่อ · Junior + May review ย้อนหลังหลัง merge (ทีมตกลง 31 ต.ค. · ไม่ต้องรอ approve) · `apps/api/` เป็นของ Junior จึงบอกกลุ่ม

## Next step

รัน `/spec-to-tests specs/features/scope/compute-importance.md`

## Waiting on

ไม่มี (Junior + May review test ย้อนหลังได้ ไม่ขวาง)

## Notes for next time

- เริ่มงาน 13:46 (8 พ.ย.)
